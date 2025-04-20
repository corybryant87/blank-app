import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import numpy_financial as npf

# ------------- Helper Functions -------------------
def fmt_dollar(x):
    """Format a number as a dollar string with commas and no decimals."""
    try:
        return '$' + format(int(round(x)), ',d')
    except Exception:
        return '$0'


def compute_amortization(debt, rate, payment):
    """Compute amortization schedule."""
    records = []
    bal = debt
    total_interest = 0
    months = 0
    while bal > 0 and months < 600:  # 50 year maximum
        interest = bal * (rate/12/100)
        total_interest += interest
        bal = bal + interest - payment
        if bal < 0:
            bal = 0
        records.append({
            'Month': months,
            'Remaining Balance': bal,
            'Interest This Month': interest
        })
        months += 1
    return pd.DataFrame(records), months, total_interest

# ------------- Sidebar Inputs -------------------
st.sidebar.title('Budget & Debt Planning')

annual_income = st.sidebar.number_input(
    'Annual Gross Income', min_value=0, value=60000, step=1000, format="%d"
)
monthly_income = annual_income / 12

total_debt = st.sidebar.number_input(
    'Total Debt Balance', min_value=0, value=20000, step=100, format="%d"
)
debt_interest_rate = st.sidebar.number_input(
    'Debt Interest Rate (%)', min_value=0.0, value=5.0, step=0.1
)
min_monthly_payment = st.sidebar.number_input(
    'Monthly Debt Payment', min_value=0, value=300, step=50, format="%d"
)
monthly_retirement_savings = st.sidebar.number_input(
    'Monthly Retirement Savings', min_value=0, value=1000, step=100, format="%d"
)
retirement_increase = st.sidebar.number_input(
    'Annual Retirement Contribution Increase (%)',
    min_value=0.0, max_value=20.0, value=3.0, step=0.5,
    help="Your monthly contribution will increase by this percentage each year"
)
annual_return = st.sidebar.number_input(
    'Expected Annual Return (%)', min_value=0.0, value=7.0, step=0.1
)
current_age = st.sidebar.number_input(
    'Current Age', min_value=0, value=30, step=1
)
desired_retirement_age = st.sidebar.number_input(
    'Desired Retirement Age', min_value=current_age, value=65, step=1
)

# ------------- Budget Allocation -------------------
st.header('Budget Allocations')

st.subheader('Adjust Allocation Percentages')
housing_pct = st.slider(
    'Housing (% of income)', min_value=0, max_value=50, value=30, step=1
)
essentials_pct = st.slider(
    'Other Essentials (% of income)', min_value=0, max_value=50, value=40, step=1
)
st.caption('Recommended: Housing 30%, Other Essentials 40%')

housing_allocation = housing_pct / 100 * monthly_income
essentials_allocation = essentials_pct / 100 * monthly_income
savings = monthly_retirement_savings
discretionary = monthly_income - (
    housing_allocation + essentials_allocation + savings + min_monthly_payment
)

budget_df = pd.DataFrame({
    'Category': [
        f'Housing ({housing_pct}%)',
        f'Other Essentials ({essentials_pct}%)',
        'Retirement Savings',
        'Debt Payment',
        'Discretionary'
    ],
    'Amount': [
        housing_allocation,
        essentials_allocation,
        savings,
        min_monthly_payment,
        discretionary
    ]
})
st.table(budget_df.style.format({'Amount': lambda x: fmt_dollar(x)}))

fig_budget = go.Figure(data=[go.Pie(
    labels=budget_df['Category'],
    values=budget_df['Amount'],
    text=[fmt_dollar(v) for v in budget_df['Amount']],
    textinfo='label+text'
)])
fig_budget.update_layout(title='Monthly Budget Allocation')
st.plotly_chart(fig_budget)

# ------------- Debt Payoff -------------------
st.header('Debt Payoff Analysis')
payment_scenarios = {
    'Current Payment': min_monthly_payment,
    '+50% Payment': min_monthly_payment * 1.5,
    '+100% Payment': min_monthly_payment * 2,
    '+200% Payment': min_monthly_payment * 3
}
debt_plans, amort_dfs = [], []
for name, pay in payment_scenarios.items():
    amort_df, months, total_int = compute_amortization(
        total_debt, debt_interest_rate, pay
    )
    amort_df['Plan'] = name
    amort_dfs.append(amort_df)
    debt_plans.append({
        'Plan': name,
        'Monthly Payment': pay,
        'Months to Payoff': months,
        'Total Interest Paid': total_int
    })
debt_plans_df = pd.DataFrame(debt_plans)
st.table(debt_plans_df.style.format({
    'Monthly Payment': lambda x: fmt_dollar(x),
    'Total Interest Paid': lambda x: fmt_dollar(x)
}))
combined_amort = pd.concat(amort_dfs, ignore_index=True)
fig_debt = px.line(
    combined_amort,
    x='Month',
    y='Remaining Balance',
    color='Plan',
    title='Debt Repayment Schedules'
)
fig_debt.update_layout(
    yaxis_tickprefix='$',
    yaxis_tickformat=',d',
    xaxis_title='Month',
    yaxis_title='Remaining Balance'
)
st.plotly_chart(fig_debt)

# ------------- Retirement Analysis -------------------
st.header('Retirement Analysis')
years = desired_retirement_age - current_age
scenarios = {'Base': 1, '+10% Contribution': 1.1, '+25% Contribution': 1.25, '+50% Contribution': 1.5}
retire_plans = []
for name, mult in scenarios.items():
    bal = 0
    monthly_sav = monthly_retirement_savings * mult
    for _ in range(years + 1):
        bal = bal * (1 + annual_return/100) + (monthly_sav * 12)
        monthly_sav *= (1 + retirement_increase/100)
    final_monthly = (
        monthly_retirement_savings * mult * (1 + retirement_increase/100) ** years
    )
    annual_withdraw = bal * 0.04
    retire_plans.append({
        'Scenario': name,
        'Initial Monthly': monthly_retirement_savings * mult,
        'Final Monthly': final_monthly,
        'Projected Savings': bal,
        '4% Withdrawal': annual_withdraw
    })
retire_df = pd.DataFrame(retire_plans)
st.table(retire_df.style.format({
    'Initial Monthly': lambda x: fmt_dollar(x),
    'Final Monthly': lambda x: fmt_dollar(x),
    'Projected Savings': lambda x: fmt_dollar(x),
    '4% Withdrawal': lambda x: fmt_dollar(x)
}))
projection_records = []
for name, mult in scenarios.items():
    bal = 0
    monthly_sav = monthly_retirement_savings * mult
    for year in range(years + 1):
        projection_records.append({'Age': current_age + year, 'Balance': bal, 'Scenario': name})
        bal = bal * (1 + annual_return/100) + (monthly_sav * 12)
        monthly_sav *= (1 + retirement_increase/100)
proj_df = pd.DataFrame(projection_records)
fig_ret = px.line(
    proj_df,
    x='Age',
    y='Balance',
    color='Scenario',
    title='Retirement Savings Projections - All Scenarios'
)
# Reverse legend order so +50% appears at top and Base at bottom
fig_ret.update_layout(
    yaxis_tickprefix='$',
    yaxis_tickformat=',d',
    xaxis_title='Age',
    yaxis_title='Balance',
    legend=dict(traceorder='reversed')
)
st.plotly_chart(fig_ret)

# ------------- Resources -------------------
st.header('Next Steps & Resources')
current_plan = debt_plans_df[debt_plans_df['Plan'] == 'Current Payment'].iloc[0]
months_current = int(current_plan['Months to Payoff'])
interest_current = current_plan['Total Interest Paid']
st.markdown(f"""
- **Debt Payoff**: At your current payment of {fmt_dollar(min_monthly_payment)}, you will pay off {fmt_dollar(total_debt)} in approximately {months_current} months, paying {fmt_dollar(interest_current)} in interest. Consider increasing payments to the +50% scenario to reduce time and interest.
- **Budget Rebalance**: You have {fmt_dollar(discretionary)} discretionary each month. Allocate 10–20% of that to an emergency fund in a high-yield savings account.
- **Retirement Automation**: Automate your monthly contributions and schedule an annual increase of {retirement_increase}% to stay on track automatically.
- **Refinancing Check**: If your debt interest rate ({debt_interest_rate}%) is above market, explore refinancing or consolidation to lower your rate.
- **Quarterly Review**: Set a calendar reminder to revisit your sliders and projections every quarter and adjust for changes.
- **Tools & Resources**: Use budgeting apps like Mint or YNAB for real-time tracking, and visit [Investopedia](https://www.investopedia.com/) for deeper dives.


App created by: Cory Bryant, Helena Qian, John Hurdt, Pasang Lhamo, Varun Garg, and William Ostdiek
""")

print("App execution complete.")

