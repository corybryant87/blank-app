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
    except Exception as e:
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

monthly_income = st.sidebar.number_input(
    'Monthly Net Income',
    min_value=0,
    value=5000,
    step=100,
    format="%d"
)

total_debt = st.sidebar.number_input(
    'Total Debt Balance',
    min_value=0,
    value=20000,
    step=100,
    format="%d"
)

debt_interest_rate = st.sidebar.number_input(
    'Debt Interest Rate (%)',
    min_value=0.0,
    value=5.0,
    step=0.1
)

min_monthly_payment = st.sidebar.number_input(
    'Minimum Monthly Debt Payment',
    min_value=0,
    value=300,
    step=50,
    format="%d"
)

retirement_savings = st.sidebar.number_input(
    'Current Retirement Savings',
    min_value=0,
    value=10000,
    step=1000,
    format="%d"
)

annual_return = st.sidebar.number_input(
    'Expected Annual Return (%)',
    min_value=0.0,
    value=7.0,
    step=0.1
)

current_age = st.sidebar.number_input(
    'Current Age',
    min_value=0,
    value=30,
    step=1
)

desired_retirement_age = st.sidebar.number_input(
    'Desired Retirement Age',
    min_value=current_age,
    value=65,
    step=1
)

debt_aggressiveness = st.sidebar.selectbox(
    'Debt Payoff Plan', 
    ['Conservative', 'Moderate', 'Aggressive']
)

# ------------- Budget Allocation -------------------
st.header('Budget Allocations')

# Allocate income
housing_allocation = 0.30 * monthly_income
essentials_allocation = 0.40 * monthly_income
savings = 0.15 * monthly_income

if debt_aggressiveness == 'Conservative':
    chosen_debt_payment = min_monthly_payment
elif debt_aggressiveness == 'Moderate':
    chosen_debt_payment = 1.5 * min_monthly_payment
else:
    chosen_debt_payment = 2 * min_monthly_payment

discretionary = monthly_income - (housing_allocation + essentials_allocation + savings + chosen_debt_payment)

# Create budget dataframe
budget_data = {
    'Category': ['Housing (30%)', 'Essentials (40%)', 'Savings (15%)', 
                f'Debt Payment ({debt_aggressiveness})', 'Discretionary'],
    'Amount': [housing_allocation, essentials_allocation, savings, 
              chosen_debt_payment, discretionary]
}

budget_df = pd.DataFrame(budget_data)

# Display table
st.table(budget_df.style.format({'Amount': lambda x: fmt_dollar(x)}))

# Create pie chart with dollar values
fig_budget = go.Figure(data=[go.Pie(
    labels=budget_df['Category'],
    values=budget_df['Amount'],
    text=[fmt_dollar(val) for val in budget_df['Amount']],
    textinfo='label+text'
)])
fig_budget.update_layout(title='Monthly Budget Allocation')
st.plotly_chart(fig_budget)

# ------------- Debt Payoff -------------------
st.header('Debt Payoff Analysis')

# Prepare debt payoff calculations
min_payment = min_monthly_payment
rec_payment = 1.5 * min_monthly_payment
max_payment = 2 * min_monthly_payment

# Compute amortization for each plan
amort_min, months_min, total_int_min = compute_amortization(total_debt, debt_interest_rate, min_payment)
amort_rec, months_rec, total_int_rec = compute_amortization(total_debt, debt_interest_rate, rec_payment)
amort_max, months_max, total_int_max = compute_amortization(total_debt, debt_interest_rate, max_payment)

# Create debt plans summary
debt_plans = pd.DataFrame({
    'Plan': ['Minimum', 'Recommended', 'Aggressive'],
    'Monthly Payment': [min_payment, rec_payment, max_payment],
    'Months to Payoff': [months_min, months_rec, months_max],
    'Total Interest Paid': [total_int_min, total_int_rec, total_int_max]
})

st.table(debt_plans.style.format({
    'Monthly Payment': lambda x: fmt_dollar(x),
    'Total Interest Paid': lambda x: fmt_dollar(x)
}))

# Display amortization chart for chosen plan
if debt_aggressiveness == 'Conservative':
    amort_df = amort_min
elif debt_aggressiveness == 'Moderate':
    amort_df = amort_rec
else:
    amort_df = amort_max

fig_debt = px.line(amort_df, x='Month', y='Remaining Balance', 
                   title='Debt Payoff Schedule')
fig_debt.update_layout(yaxis_tickprefix='$', yaxis_tickformat=',d')
st.plotly_chart(fig_debt)

# ------------- Retirement Analysis -------------------
st.header('Retirement Analysis')

# Calculate rates and periods
monthly_rate = (1 + annual_return/100)**(1/12) - 1
months_to_retirement = (desired_retirement_age - current_age) * 12

# Base scenario calculations
future_value_base = (retirement_savings * (1 + monthly_rate)**months_to_retirement + 
                    savings * ((1 + monthly_rate)**months_to_retirement - 1) / monthly_rate)
annual_withdrawal_base = future_value_base * 0.04

st.write('**Base Scenario**')
st.write('Projected Retirement Savings: ' + fmt_dollar(future_value_base))
st.write('Estimated Annual Withdrawal (4% Rule): ' + fmt_dollar(annual_withdrawal_base))

# Create base projection
years = range(current_age, desired_retirement_age + 1)
projection_base = []
current_savings_base = retirement_savings
for year in years:
    projection_base.append({
        'Age': year,
        'Balance': current_savings_base,
        'Scenario': 'Base'
    })
    current_savings_base = current_savings_base * (1 + annual_return/100) + (savings * 12)

# 10% increase scenario
savings_10 = savings * 1.1
projection_10 = []
current_savings_10 = retirement_savings
future_value_10 = (retirement_savings * (1 + monthly_rate)**months_to_retirement + 
                   savings_10 * ((1 + monthly_rate)**months_to_retirement - 1) / monthly_rate)

for year in years:
    projection_10.append({
        'Age': year,
        'Balance': current_savings_10,
        'Scenario': '+10% Contribution'
    })
    current_savings_10 = current_savings_10 * (1 + annual_return/100) + (savings_10 * 12)

st.write('\
**+10% Contribution Scenario**')
st.write('Projected Retirement Savings: ' + fmt_dollar(future_value_10))
st.write('Estimated Annual Withdrawal (4% Rule): ' + fmt_dollar(future_value_10 * 0.04))

# 20% increase scenario
savings_20 = savings * 1.2
projection_20 = []
current_savings_20 = retirement_savings
future_value_20 = (retirement_savings * (1 + monthly_rate)**months_to_retirement + 
                   savings_20 * ((1 + monthly_rate)**months_to_retirement - 1) / monthly_rate)

for year in years:
    projection_20.append({
        'Age': year,
        'Balance': current_savings_20,
        'Scenario': '+20% Contribution'
    })
    current_savings_20 = current_savings_20 * (1 + annual_return/100) + (savings_20 * 12)

st.write('\
**+20% Contribution Scenario**')
st.write('Projected Retirement Savings: ' + fmt_dollar(future_value_20))
st.write('Estimated Annual Withdrawal (4% Rule): ' + fmt_dollar(future_value_20 * 0.04))

# Combine all scenarios into one dataframe for plotting
all_projections = pd.DataFrame(projection_base + projection_10 + projection_20)

# Create combined retirement projection plot
fig_retirement = px.line(all_projections, 
                        x='Age', 
                        y='Balance',
                        color='Scenario',
                        title='Retirement Savings Projections - All Scenarios')
fig_retirement.update_layout(yaxis_tickprefix='$', 
                           yaxis_tickformat=',d',
                           xaxis_title='Age',
                           yaxis_title='Balance')
st.plotly_chart(fig_retirement)

# ------------- Resources -------------------
st.header('Next Steps & Resources')
st.markdown("""
- Review and adjust your budget allocations.
- Consider increasing your debt payments if possible.
- Consult with a financial advisor about retirement planning.
- Visit [Investopedia](https://www.investopedia.com/) for more financial education.
""")

print("App execution complete.")