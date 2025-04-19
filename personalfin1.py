import streamlit as st  
import pandas as pd  
import numpy as np  
import plotly.express as px  
import numpy_financial as npf  
  
# ------------- Helper Functions -------------------  
def fmt_dollar(x):  
    """Format a number as a dollar string with commas and no decimals."""  
    return '$' + format(int(round(x)), ',d')  
  
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
  
# ------------- Budget Calculations -------------------  
st.title('Personal Budget & Debt Payoff Analysis')  
  
# Budget allocations  
housing = monthly_income * 0.30  
essentials = monthly_income * 0.40  
savings = monthly_income * 0.15  
  
# Determine debt payment based on plan  
if debt_aggressiveness == 'Conservative':  
    debt_payment = min_monthly_payment  
elif debt_aggressiveness == 'Moderate':  
    debt_payment = min_monthly_payment * 1.5  
else:  # Aggressive  
    debt_payment = min_monthly_payment * 2.0  
  
# Calculate discretionary  
discretionary = monthly_income - (housing + essentials + savings + debt_payment)  
  
# Display budget breakdown  
st.header('Monthly Budget Breakdown')  
budget_data = {  
    'Category': ['Housing', 'Essentials', 'Savings', 'Debt Payment', 'Discretionary'],  
    'Amount': [housing, essentials, savings, debt_payment, discretionary]  
}  
budget_df = pd.DataFrame(budget_data)  
budget_df['Amount'] = budget_df['Amount'].apply(fmt_dollar)  
st.table(budget_df)  
  
# Budget pie chart  
fig_budget = px.pie(budget_df, values=[housing, essentials, savings, debt_payment, discretionary],  
                    names=['Housing', 'Essentials', 'Savings', 'Debt Payment', 'Discretionary'],  
                    title='Monthly Budget Allocation')  
st.plotly_chart(fig_budget)  
  
# ------------- Debt Analysis -------------------  
st.header('Debt Payoff Analysis')  
  
# Display debt payment plans  
payment_plans = {  
    'Plan': ['Conservative', 'Moderate', 'Aggressive'],  
    'Minimum Payment': [min_monthly_payment] * 3,  
    'Recommended Payment': [  
        min_monthly_payment,  
        min_monthly_payment * 1.5,  
        min_monthly_payment * 2.0  
    ],  
    'Maximum Payment': [min_monthly_payment * 2.0] * 3  
}  
plans_df = pd.DataFrame(payment_plans)  
for col in ['Minimum Payment', 'Recommended Payment', 'Maximum Payment']:  
    plans_df[col] = plans_df[col].apply(fmt_dollar)  
st.table(plans_df)  
  
# Calculate and display amortization  
amort_df, months_to_payoff, total_interest = compute_amortization(  
    total_debt, debt_interest_rate, debt_payment  
)  
  
st.write(f'Months to pay off debt: {months_to_payoff}')  
st.write(f'Total interest paid: {fmt_dollar(total_interest)}')  
  
# Debt payoff chart  
fig_debt = px.line(amort_df, x='Month', y='Remaining Balance',  
                   title='Debt Payoff Schedule')  
fig_debt.update_layout(yaxis_tickprefix='$', yaxis_tickformat=',.0f')  
st.plotly_chart(fig_debt)  
  
# ------------- Retirement Analysis -------------------  
st.header('Retirement Analysis')  
  
# Calculate monthly return rate  
monthly_rate = (1 + annual_return/100)**(1/12) - 1  
months_to_retirement = (desired_retirement_age - current_age) * 12  
  
# Future Value calculation  
future_value = (retirement_savings * (1 + monthly_rate)**months_to_retirement +   
               savings * ((1 + monthly_rate)**months_to_retirement - 1) / monthly_rate)  
  
# Annual withdrawal (4% rule)  
annual_withdrawal = future_value * 0.04  
  
st.write(f'Projected Retirement Savings: {fmt_dollar(future_value)}')  
st.write(f'Estimated Annual Withdrawal (4% Rule): {fmt_dollar(annual_withdrawal)}')  
  
# Create retirement projection dataframe  
years = range(current_age, desired_retirement_age + 1)  
projection = []  
current_savings = retirement_savings  
for year in years:  
    projection.append({  
        'Age': year,  
        'Balance': current_savings  
    })  
    current_savings = current_savings * (1 + annual_return/100) + (savings * 12)  
  
projection_df = pd.DataFrame(projection)  
  
# Retirement projection chart  
fig_retirement = px.line(projection_df, x='Age', y='Balance',  
                        title='Retirement Savings Projection')  
fig_retirement.update_layout(yaxis_tickprefix='$', yaxis_tickformat=',.0f')  
st.plotly_chart(fig_retirement)  
  
# ------------- Resources -------------------  
st.header('Next Steps')  
st.markdown("""  
- Review and adjust your budget allocations  
- Consider increasing your debt payments if possible  
- Consult with a financial advisor about retirement planning  
- Visit [Investopedia](https://www.investopedia.com/) for more financial education  
""")  