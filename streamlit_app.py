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
  
def compute_retirement_scenario(monthly_contribution, years, annual_return, annual_increase):  
    """Compute retirement projections for a given contribution amount"""  
    current_savings = 0  
    current_monthly = monthly_contribution  
      
    for _ in range(years):  
        annual_contrib = current_monthly * 12  
        current_savings = current_savings * (1 + annual_return/100) + annual_contrib  
        current_monthly *= (1 + annual_increase/100)  
      
    return current_savings  
  
# ------------- App Layout -------------------  
st.title('Personal Finance Calculator')  
  
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
  
monthly_debt_payment = st.sidebar.number_input(  
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
  
retirement_increase = st.sidebar.number_input(  
    'Annual Retirement Contribution Increase (%)',  
    min_value=0.0,  
    max_value=20.0,  
    value=3.0,  
    step=0.5  
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
  
# ------------- Budget Analysis -------------------  
st.header('Monthly Budget Analysis')  
  
# Calculate budget allocations  
budget_categories = {  
    'Housing (25-35%)': 0.30,  
    'Transportation (10-15%)': 0.15,  
    'Food (10-15%)': 0.12,  
    'Utilities (5-10%)': 0.08,  
    'Insurance (10-15%)': 0.12,  
    'Debt Payment': monthly_debt_payment / monthly_income,  
    'Retirement Savings': monthly_retirement_savings / monthly_income,  
    'Other': 0.0  # Will be calculated as remainder  
}  
  
# Calculate 'Other' as remainder  
allocated = sum(budget_categories.values())  
budget_categories['Other'] = max(0, 1 - allocated)  
  
# Create budget allocation table  
budget_table = pd.DataFrame({  
    'Category': budget_categories.keys(),  
    'Percentage': [f"{v*100:.1f}%" for v in budget_categories.values()],  
    'Monthly Amount': [fmt_dollar(v * monthly_income) for v in budget_categories.values()]  
})  
  
st.write("Monthly Budget Allocation")  
st.dataframe(budget_table)  
  
# Create pie chart with dollar values  
fig_budget = px.pie(  
    values=[v * monthly_income for v in budget_categories.values()],  
    names=budget_categories.keys(),  
    title='Monthly Budget Allocation'  
)  
  
# Update pie chart to show dollar values in labels  
fig_budget.update_traces(  
    textinfo='label+value',  
    texttemplate='%{label}<br>%{value:$,.0f}'  
)  
  
st.plotly_chart(fig_budget)  
  
# ------------- Debt Analysis -------------------  
st.header('Debt Payoff Analysis')  
  
# Calculate different payment scenarios  
payment_scenarios = {  
    'Current Payment': monthly_debt_payment,  
    '+50% Payment': monthly_debt_payment * 1.5,  
    '+100% Payment': monthly_debt_payment * 2.0,  
    '+200% Payment': monthly_debt_payment * 3.0  
}  
  
debt_analysis = []  
for scenario, payment in payment_scenarios.items():  
    schedule, months, total_interest = compute_amortization(total_debt, debt_interest_rate, payment)  
    debt_analysis.append({  
        'Plan': scenario,  
        'Monthly Payment': fmt_dollar(payment),  
        'Months to Payoff': f"{months:,d}",  
        'Total Interest': fmt_dollar(total_interest)  
    })  
  
debt_table = pd.DataFrame(debt_analysis)  
st.write("Debt Payoff Scenarios")  
st.dataframe(debt_table)  
  
# Create debt payoff visualization  
years_to_plot = 10  
months_to_plot = years_to_plot * 12  
  
fig_debt = go.Figure()  
for scenario, payment in payment_scenarios.items():  
    schedule, _, _ = compute_amortization(total_debt, debt_interest_rate, payment)  
    if len(schedule) > months_to_plot:  
        schedule = schedule.iloc[:months_to_plot]  
    fig_debt.add_trace(go.Scatter(  
        x=schedule['Month'],  
        y=schedule['Remaining Balance'],  
        name=scenario,  
        mode='lines'  
    ))  
  
fig_debt.update_layout(  
    title='Debt Payoff Projection (10 Year Window)',  
    xaxis_title='Months',  
    yaxis_title='Remaining Balance',  
    yaxis_tickprefix='$',  
    showlegend=True  
)  
st.plotly_chart(fig_debt)  
  
# ------------- Retirement Analysis -------------------  
st.header('Retirement Analysis')  
  
years_to_retirement = desired_retirement_age - current_age  
  
# Calculate different retirement scenarios  
retirement_scenarios = {  
    'Base Contribution': monthly_retirement_savings,  
    '+50% Contribution': monthly_retirement_savings * 1.5,  
    '+100% Contribution': monthly_retirement_savings * 2.0,  
    '+200% Contribution': monthly_retirement_savings * 3.0  
}  
  
retirement_analysis = []  
for scenario, contribution in retirement_scenarios.items():  
    future_value = compute_retirement_scenario(  
        contribution,   
        years_to_retirement,   
        annual_return,   
        retirement_increase  
    )  
    monthly_income = future_value * 0.04 / 12  # 4% rule, monthly  
      
    retirement_analysis.append({  
        'Plan': scenario,  
        'Monthly Contribution': fmt_dollar(contribution),  
        'Projected Balance': fmt_dollar(future_value),  
        'Monthly Income (4% Rule)': fmt_dollar(monthly_income)  
    })  
  
retirement_table = pd.DataFrame(retirement_analysis)  
st.write("Retirement Scenarios")  
st.dataframe(retirement_table)  
  
# Create retirement projection visualization  
def retirement_projection_over_time(monthly_contribution, years, annual_return, annual_increase):  
    values = []  
    current_monthly = monthly_contribution  
    savings = 0  
    year_range = list(range(years + 1))  
      
    for _ in year_range:  
        values.append(savings)  
        annual_contrib = current_monthly * 12  
        savings = savings * (1 + annual_return/100) + annual_contrib  
        current_monthly *= (1 + annual_increase/100)  
    return year_range, values  
  
fig_retirement = go.Figure()  
for scenario, contribution in retirement_scenarios.items():  
    years, values = retirement_projection_over_time(  
        contribution,   
        years_to_retirement,   
        annual_return,   
        retirement_increase  
    )  
    fig_retirement.add_trace(go.Scatter(  
        x=years,  
        y=values,  
        name=scenario,  
        mode='lines'  
    ))  
  
fig_retirement.update_layout(  
    title='Retirement Savings Projection',  
    xaxis_title='Years',  
    yaxis_title='Balance',  
    yaxis_tickprefix='$',  
    showlegend=True  
)  
st.plotly_chart(fig_retirement)  
  
# ------------- Resources -------------------  
st.header('Next Steps & Resources')  
st.markdown('''  
- Review and adjust your budget allocations.  
- Consider increasing your debt payments if possible.  
- Consult with a financial advisor about retirement planning.  
- Visit [Investopedia](https://www.investopedia.com/) for more financial education.  
''')  
