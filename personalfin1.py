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
  
annual_income = st.sidebar.number_input(  
    'Annual Gross Income',  
    min_value=0,  
    value=60000,  
    step=1000,  
    format="%d"  
)  
monthly_income = annual_income / 12  
  
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
    'Monthly Debt Payment',  
    min_value=0,  
    value=300,  
    step=50,  
    format="%d"  
)  
  
monthly_retirement_savings = st.sidebar.number_input(  
    'Monthly Retirement Savings',  
    min_value=0,  
    value=1000,  
    step=100,  
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
  
# ------------- Budget Allocation -------------------  
st.header('Budget Allocations')  
  
# Allocate income  
housing_allocation = 0.30 * monthly_income  
essentials_allocation = 0.40 * monthly_income  
savings = monthly_retirement_savings  
debt_payment = min_monthly_payment  
discretionary = monthly_income - (housing_allocation + essentials_allocation + savings + debt_payment)  
  
# Create budget dataframe  
budget_data = {  
    'Category': ['Housing (30%)', 'Essentials (40%)', 'Savings',   
                'Debt Payment', 'Discretionary'],  
    'Amount': [housing_allocation, essentials_allocation, savings,   
              debt_payment, discretionary]  
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
  
# Calculate payments for each scenario  
current_payment = min_monthly_payment  
payment_50_more = current_payment * 1.5  
payment_100_more = current_payment * 2  
payment_200_more = current_payment * 3  
  
# Compute amortization for each scenario  
amort_current, months_current, total_int_current = compute_amortization(total_debt, debt_interest_rate, current_payment)  
amort_50, months_50, total_int_50 = compute_amortization(total_debt, debt_interest_rate, payment_50_more)  
amort_100, months_100, total_int_100 = compute_amortization(total_debt, debt_interest_rate, payment_100_more)  
amort_200, months_200, total_int_200 = compute_amortization(total_debt, debt_interest_rate, payment_200_more)  
  
# Create debt plans summary  
debt_plans = pd.DataFrame({  
    'Plan': ['Current Payment', '+50% Payment', '+100% Payment', '+200% Payment'],  
    'Monthly Payment': [current_payment, payment_50_more, payment_100_more, payment_200_more],  
    'Months to Payoff': [months_current, months_50, months_100, months_200],  
    'Total Interest Paid': [total_int_current, total_int_50, total_int_100, total_int_200]  
})  
  
st.table(debt_plans.style.format({  
    'Monthly Payment': lambda x: fmt_dollar(x),  
    'Total Interest Paid': lambda x: fmt_dollar(x)  
}))  
  
# Display amortization chart for all scenarios  
all_amort = pd.DataFrame()  
for scenario, df in [('Current Payment', amort_current),   
                    ('+50% Payment', amort_50),  
                    ('+100% Payment', amort_100),  
                    ('+200% Payment', amort_200)]:  
    df['Scenario'] = scenario  
    all_amort = pd.concat([all_amort, df])  
  
fig_debt = px.line(all_amort,   
                   x='Month',   
                   y='Remaining Balance',  
                   color='Scenario',  
                   title='Debt Payoff Schedule - All Scenarios')  
fig_debt.update_layout(yaxis_tickprefix='$', yaxis_tickformat=',d')  
st.plotly_chart(fig_debt)  
  
# ------------- Retirement Analysis -------------------  
st.header('Retirement Analysis')  
  
# Calculate rates and periods  
monthly_rate = (1 + annual_return/100)**(1/12) - 1  
months_to_retirement = (desired_retirement_age - current_age) * 12  
  
# Base scenario calculations  
future_value_base = monthly_retirement_savings * ((1 + monthly_rate)**months_to_retirement - 1) / monthly_rate  
annual_withdrawal_base = future_value_base * 0.04  
  
st.write('**Base Scenario**')  
st.write('Projected Retirement Savings: ' + fmt_dollar(future_value_base))  
st.write('Estimated Annual Withdrawal (4% Rule): ' + fmt_dollar(annual_withdrawal_base))  
  
# Create base projection  
years = range(current_age, desired_retirement_age + 1)  
projection_base = []  
current_savings_base = 0  # Start from 0  
for year in years:  
    projection_base.append({  
        'Age': year,  
        'Balance': current_savings_base,  
        'Scenario': 'Base'  
    })  
    current_savings_base = current_savings_base * (1 + annual_return/100) + (monthly_retirement_savings * 12)  
  
# +10% contribution scenario  
savings_10 = monthly_retirement_savings * 1.1  
projection_10 = []  
current_savings_10 = 0  # Start from 0  
future_value_10 = savings_10 * ((1 + monthly_rate)**months_to_retirement - 1) / monthly_rate  
  
for year in years:  
    projection_10.append({  
        'Age': year,  
        'Balance': current_savings_10,  
        'Scenario': '+10% Contribution'  
    })  
    current_savings_10 = current_savings_10 * (1 + annual_return/100) + (savings_10 * 12)  
  
st.write('\n**+10% Contribution Scenario**')  
st.write('Projected Retirement Savings: ' + fmt_dollar(future_value_10))  
st.write('Estimated Annual Withdrawal (4% Rule): ' + fmt_dollar(future_value_10 * 0.04))  
  
# +20% contribution scenario  
savings_20 = monthly_retirement_savings * 1.2  
projection_20 = []  
current_savings_20 = 0  # Start from 0  
future_value_20 = savings_20 * ((1 + monthly_rate)**months_to_retirement - 1) / monthly_rate  
  
for year in years:  
    projection_20.append({  
        'Age': year,  
        'Balance': current_savings_20,  
        'Scenario': '+20% Contribution'  
    })  
    current_savings_20 = current_savings_20 * (1 + annual_return/100) + (savings_20 * 12)  
  
st.write('\n**+20% Contribution Scenario**')  
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
st.markdown('''  
- Review and adjust your budget allocations.  
- Consider increasing your debt payments if possible.  
- Consult with a financial advisor about retirement planning.  
- Visit [Investopedia](https://www.investopedia.com/) for more financial education.  
''')  
  
print("App execution complete.")  