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
  
# New input for annual retirement savings increase  
retirement_increase = st.sidebar.number_input(  
    'Annual Retirement Contribution Increase (%)',  
    min_value=0.0,  
    max_value=20.0,  # Setting a reasonable maximum  
    value=3.0,  
    step=0.5,  
    help="Your monthly contribution will increase by this percentage each year"  
)  
# Calculate the monthly increase rate  
monthly_increase_rate = retirement_increase / 200  # Halved percentage for calculations  
  
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
discretionary = monthly_income - (housing_allocation + essentials_allocation + savings + min_monthly_payment)  
  
# Create budget dataframe  
budget_data = {  
    'Category': ['Housing (30%)', 'Essentials (40%)', 'Retirement Savings',   
                'Debt Payment', 'Discretionary'],  
    'Amount': [housing_allocation, essentials_allocation, savings,   
              min_monthly_payment, discretionary]  
}  
  
budget_df = pd.DataFrame(budget_data)  
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
  
# Calculate different payment scenarios  
payment_scenarios = {  
    'Current Payment': min_monthly_payment,  
    '+50% Payment': min_monthly_payment * 1.5,  
    '+100% Payment': min_monthly_payment * 2,  
    '+200% Payment': min_monthly_payment * 3  
}  
  
# Compute amortization for each scenario  
debt_plans = []  
for scenario, payment in payment_scenarios.items():  
    amort_df, months, total_interest = compute_amortization(total_debt, debt_interest_rate, payment)  
    debt_plans.append({  
        'Plan': scenario,  
        'Monthly Payment': payment,  
        'Months to Payoff': months,  
        'Total Interest Paid': total_interest  
    })  
  
debt_plans_df = pd.DataFrame(debt_plans)  
st.table(debt_plans_df.style.format({  
    'Monthly Payment': lambda x: fmt_dollar(x),  
    'Total Interest Paid': lambda x: fmt_dollar(x)  
}))  
  
# ------------- Retirement Analysis -------------------  
st.header('Retirement Analysis')  
  
# Calculate rates and periods  
monthly_rate = (1 + annual_return/100)**(1/12) - 1  
years_to_retirement = desired_retirement_age - current_age  
  
# Base scenario calculations with increasing contributions  
projection_base = []  
current_savings = 0  
current_monthly_savings = monthly_retirement_savings  
  
for year in range(years_to_retirement + 1):  
    projection_base.append({  
        'Age': current_age + year,  
        'Balance': current_savings,  
        'Monthly Contribution': current_monthly_savings,  
        'Scenario': 'Base'  
    })  
    # Update for next year  
    current_savings = current_savings * (1 + annual_return/100) + (current_monthly_savings * 12)  
    current_monthly_savings = current_monthly_savings * (1 + retirement_increase/100)  
  
# Calculate final values for display  
final_monthly_contribution = monthly_retirement_savings * (1 + retirement_increase/100)**years_to_retirement  
future_value_base = projection_base[-1]['Balance']  
  
st.write('**Base Scenario**')  
st.write('Initial Monthly Contribution: ' + fmt_dollar(monthly_retirement_savings))  
st.write('Final Monthly Contribution: ' + fmt_dollar(final_monthly_contribution))  
st.write('Projected Retirement Savings: ' + fmt_dollar(future_value_base))  
st.write('Estimated Annual Withdrawal (4% Rule): ' + fmt_dollar(future_value_base * 0.04))  
  
# +10% and +20% scenarios with same annual increase  
scenarios = {  
    '+10% Contribution': 1.1,  
    '+20% Contribution': 1.2  
}  
  
all_projections = projection_base.copy()  
  
for scenario_name, multiplier in scenarios.items():  
    current_savings = 0  
    current_monthly_savings = monthly_retirement_savings * multiplier  
      
    scenario_projections = []  
    for year in range(years_to_retirement + 1):  
        scenario_projections.append({  
            'Age': current_age + year,  
            'Balance': current_savings,  
            'Monthly Contribution': current_monthly_savings,  
            'Scenario': scenario_name  
        })  
        # Update for next year  
        current_savings = current_savings * (1 + annual_return/100) + (current_monthly_savings * 12)  
        current_monthly_savings = current_monthly_savings * (1 + retirement_increase/100)  
      
    final_value = scenario_projections[-1]['Balance']  
    final_monthly = scenario_projections[-1]['Monthly Contribution']  
      
    st.write(f'\n**{scenario_name} Scenario**')  
    st.write('Initial Monthly Contribution: ' + fmt_dollar(monthly_retirement_savings * multiplier))  
    st.write('Final Monthly Contribution: ' + fmt_dollar(final_monthly))  
    st.write('Projected Retirement Savings: ' + fmt_dollar(final_value))  
    st.write('Estimated Annual Withdrawal (4% Rule): ' + fmt_dollar(final_value * 0.04))  
      
    all_projections.extend(scenario_projections)  
  
# Create combined retirement projection plot  
projection_df = pd.DataFrame(all_projections)  
fig_retirement = px.line(projection_df,   
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