import streamlit as st  
import pandas as pd  
import numpy as np  
import matplotlib.pyplot as plt  
import numpy_financial as npf  
  
# Try setting a seaborn style, if available  
try:  
    plt.style.use('seaborn-v0_8-whitegrid')  
except Exception as e:  
    print("Seaborn style not available, using default style.")  
  
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
  
# ------------- Budget Allocation -------------------  
housing = 0.30 * monthly_income  
essentials = 0.40 * monthly_income  
savings = 0.15 * monthly_income  
  
# Determine Debt Payment based on the aggressiveness option  
if debt_aggressiveness == 'Conservative':  
    debt_payment = min_monthly_payment  
elif debt_aggressiveness == 'Moderate':  
    debt_payment = 1.5 * min_monthly_payment  
elif debt_aggressiveness == 'Aggressive':  
    debt_payment = 2 * min_monthly_payment  
else:  
    debt_payment = min_monthly_payment  
  
allocated = housing + essentials + savings + debt_payment  
discretionary = monthly_income - allocated  
  
st.header('Monthly Budget Allocation')  
budget_data = {  
    'Category': ['Housing', 'Essentials', 'Savings', 'Debt', 'Discretionary'],  
    'Amount': [housing, essentials, savings, debt_payment, discretionary]  
}  
budget_df = pd.DataFrame(budget_data)  
budget_df['Amount'] = budget_df['Amount'].apply(fmt_dollar)  
st.table(budget_df)  
  
# Pie Chart for Budget Allocation  
fig1, ax1 = plt.subplots(figsize=(6, 6))  
ax1.pie([housing, essentials, savings, debt_payment, discretionary], labels=['Housing', 'Essentials', 'Savings', 'Debt', 'Discretionary'], autopct='%1.0f%%')  
ax1.set_title('Budget Allocation')  
st.pyplot(fig1)  
plt.close(fig1)  
  
# ------------- Debt Payoff -------------------  
st.header('Debt Payoff Analysis')  
  
# Create table for debt plans  
debt_plans = pd.DataFrame({  
    'Plan': ['Conservative', 'Moderate', 'Aggressive'],  
    'Minimum Payment': [fmt_dollar(min_monthly_payment)] * 3,  
    'Recommended Payment': [fmt_dollar(min_monthly_payment),  
                            fmt_dollar(1.5 * min_monthly_payment),  
                            fmt_dollar(2 * min_monthly_payment)],  
    'Maximum Payment': [fmt_dollar(2 * min_monthly_payment)] * 3  
})  
st.table(debt_plans)  
  
# Calculate amortization using the chosen debt payment  
amort_df, months_to_payoff, total_interest = compute_amortization(  
    total_debt, debt_interest_rate, debt_payment  
)  
  
st.write("Months to Payoff: " + str(months_to_payoff))  
st.write("Total Interest Paid: " + fmt_dollar(total_interest))  
  
# Debt payoff chart  
fig2, ax2 = plt.subplots(figsize=(10, 6))  
ax2.plot(amort_df['Month'], amort_df['Remaining Balance'])  
ax2.set_title('Debt Payoff Schedule')  
ax2.set_xlabel('Month')  
ax2.set_ylabel('Remaining Balance ($)')  
ax2.grid(True)  
st.pyplot(fig2)  
plt.close(fig2)  
  
# ------------- Retirement Analysis -------------------  
st.header('Retirement Analysis')  
  
# Calculate monthly return rate  
monthly_rate = (1 + annual_return/100)**(1/12) - 1  
months_to_retirement = (desired_retirement_age - current_age) * 12  
  
# Future Value calculation  
# Future Value = S0*(1+r)^n + c*((1+r)^n - 1)/r  
future_value = (retirement_savings * (1 + monthly_rate)**months_to_retirement +  
                savings * ((1 + monthly_rate)**months_to_retirement - 1) / monthly_rate)  
  
# Annual withdrawal (4% rule)  
annual_withdrawal = future_value * 0.04  
  
st.write('Projected Retirement Savings: ' + fmt_dollar(future_value))  
st.write('Estimated Annual Withdrawal (4% Rule): ' + fmt_dollar(annual_withdrawal))  
  
# Create retirement projection dataframe (annual)  
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
fig3, ax3 = plt.subplots(figsize=(10, 6))  
ax3.plot(projection_df['Age'], projection_df['Balance'])  
ax3.set_title('Retirement Savings Projection')  
ax3.set_xlabel('Age')  
ax3.set_ylabel('Balance ($)')  
ax3.grid(True)  
st.pyplot(fig3)  
plt.close(fig3)  
  
# ------------- Resources -------------------  
st.header('Next Steps & Resources')  
st.markdown("""  
- Review and adjust your budget allocations.  
- Consider increasing your debt payments if possible.  
- Consult with a financial advisor about retirement planning.  
- Visit [Investopedia](https://www.investopedia.com/) for more financial education.  
""")  