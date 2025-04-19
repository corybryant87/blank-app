import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="Personal Finance Advisor")

# Utility function to format dollars
def format_dollar(amount):
    return "$" + format(int(round(amount)), ",")

# Debt amortization calculation
def calculate_amortization(total_debt, annual_income, plan_percentage, debt_interest_rate):
    monthly_income = annual_income / 12
    monthly_payment = monthly_income * plan_percentage
    r = debt_interest_rate / 100 / 12
    if r == 0:
        months = total_debt / monthly_payment
    else:
        try:
            months = -np.log(1 - (total_debt * r / monthly_payment)) / np.log(1 + r)
        except Exception as e:
            months = np.nan
    total_interest = monthly_payment * months - total_debt
    return monthly_payment, months, total_interest

# Generate amortization schedule
def generate_amortization_schedule(total_debt, monthly_payment, debt_interest_rate):
    r = debt_interest_rate / 100 / 12
    balance = total_debt
    schedule = []
    month = 1
    while balance > 0 and month < 600:
        interest = balance * r
        principal = monthly_payment - interest
        if balance - principal < 0:
            principal = balance
            monthly_payment = principal + interest
        balance -= principal
        schedule.append({
            'Month': month,
            'Payment': format_dollar(monthly_payment),
            'Principal': format_dollar(principal),
            'Interest': format_dollar(interest),
            'Remaining Balance': format_dollar(balance)
        })
        month += 1
    return pd.DataFrame(schedule)

# Generate budget breakdown dataframe
def generate_budget_breakdown(annual_income):
    items = ['Housing', 'Transportation', 'Food', 'Utilities', 'Insurance', 'Savings', 'Entertainment']
    percentages = [0.30, 0.15, 0.15, 0.10, 0.10, 0.15, 0.05]
    amounts = [annual_income * p for p in percentages]
    return pd.DataFrame({'Category': items, 'Amount': amounts})

# Create monthly budget breakdown bar chart
def create_budget_bar_chart():
    import numpy as np
    categories = ['Housing', 'Discretionary', 'Essentials', 'Savings', 'Debt']
    # Example percentages for monthly income per category
    min_vals = [20, 5, 15, 10, 10]
    recommended_vals = [30, 10, 25, 15, 20]
    high_vals = [40, 15, 35, 20, 30]

    x = np.arange(len(categories))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))

    bars1 = ax.bar(x - width, min_vals, width, label='Min', color='lightsteelblue')
    bars2 = ax.bar(x, recommended_vals, width, label='Recommended', color='royalblue')
    bars3 = ax.bar(x + width, high_vals, width, label='High', color='darkblue')

    ax.set_ylabel('Percentage of Monthly Income (%)')
    ax.set_title('Monthly Budget Breakdown by Category')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()

    # Annotate bars
    def autolabel(bars):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(str(int(height)) + '%',
                        xy=(bar.get_x() + bar.get_width()/2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')

    autolabel(bars1)
    autolabel(bars2)
    autolabel(bars3)

    plt.tight_layout()
    return fig

# Streamlit App Layout
st.title('Personal Finance Advisor')

# Input Section
col1, col2 = st.columns(2)
with col1:
    name = st.text_input('Name')
    annual_income = st.number_input('Annual Income ($)', min_value=0, value=60000, step=1000, format='%d')
    total_debt = st.number_input('Total Debt ($)', min_value=0, value=10000, step=1000, format='%d')
with col2:
    debt_interest_rate = st.slider('Debt Interest Rate (%)', 0, 25, 5)
    years_until_retirement = st.number_input('Years Until Retirement', min_value=0, value=20, step=1)
    current_savings = st.number_input('Current Savings ($)', min_value=0, value=0, step=1000, format='%d')
    desired_retirement_income = st.number_input('Desired Annual Retirement Income ($)', min_value=0, value=48000, step=1000, format='%d')

st.markdown('---')

# Section: Budget Breakdown
st.header('Budget Breakdown')
budget_df = generate_budget_breakdown(annual_income)
st.dataframe(budget_df)

st.subheader('Monthly Budget Breakdown Bar Chart')
fig_budget = create_budget_bar_chart()
st.pyplot(fig_budget)

st.markdown('---')

# Section: Debt Repayment Analysis
st.header('Debt Repayment Analysis')
plan = st.selectbox('Debt Repayment Plan', ['Aggressive (15%)', 'Standard (10%)', 'Minimum (5%)'])
percentage = {'Aggressive (15%)': 0.15, 'Standard (10%)': 0.10, 'Minimum (5%)': 0.05}[plan]

monthly_payment, months, total_interest = calculate_amortization(total_debt, annual_income, percentage, debt_interest_rate)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric('Monthly Payment', format_dollar(monthly_payment))
with col2:
    st.metric('Months to Debt Freedom', str(int(round(months))))
with col3:
    st.metric('Total Interest', format_dollar(total_interest))

amort_df = generate_amortization_schedule(total_debt, monthly_payment, debt_interest_rate)
st.dataframe(amort_df.head(20))

st.markdown('---')

# Section: Savings Strategy
st.header('Savings Strategy')
monthly_essential = (annual_income / 12) * 0.5
target_emergency = monthly_essential * 3

col1, col2 = st.columns(2)
with col1:
    st.subheader('Emergency Fund')
    st.metric('Target Emergency Fund', format_dollar(target_emergency))
    if current_savings < target_emergency:
        remaining = target_emergency - current_savings
        monthly_contribution = remaining / 12
        st.metric('Additional Needed', format_dollar(remaining))
        st.metric('Monthly Contribution', format_dollar(monthly_contribution))
    else:
        st.success('Emergency fund target met!')
with col2:
    st.subheader('Retirement Planning')
    monthly_savings = (annual_income / 12) * 0.15
    r = 0.07 / 12
    n = years_until_retirement * 12
    fv_current = current_savings * ((1 + r) ** n)
    fv_contrib = monthly_savings * (((1 + r) ** n - 1) / r)
    projected_nest_egg = fv_current + fv_contrib
    projected_income = projected_nest_egg * 0.04
    st.metric('Projected Nest Egg', format_dollar(projected_nest_egg))
    st.metric('Annual Retirement Income', format_dollar(projected_income))
    if projected_income < desired_retirement_income:
        st.warning("Shortfall: " + format_dollar(desired_retirement_income - projected_income))
    else:
        st.success('Retirement funding on track!')

st.markdown('---')

# Analysis Download Section
if name:
    analysis_text = "Personal Financial Analysis for " + name + "\
\
"
    analysis_text += "Annual Income: " + format_dollar(annual_income) + "\
"
    analysis_text += "Desired Retirement Income: " + format_dollar(desired_retirement_income) + "\
\
"
    analysis_text += "Budget Breakdown:\
"
    for _, row in budget_df.iterrows():
        analysis_text += row['Category'] + ": " + format_dollar(row['Amount']) + "\
"
    analysis_text += "\
Debt Analysis:\
"
    analysis_text += "Total Debt: " + format_dollar(total_debt) + "\
"
    analysis_text += "Monthly Payment: " + format_dollar(monthly_payment) + "\
"
    analysis_text += "Months to Debt Freedom: " + str(int(round(months))) + "\
"
    analysis_text += "Total Interest: " + format_dollar(total_interest) + "\
\
"
    analysis_text += "Retirement Planning:\
"
    analysis_text += "Years Until Retirement: " + str(years_until_retirement) + "\
"
    analysis_text += "Projected Nest Egg: " + format_dollar(projected_nest_egg) + "\
"
    analysis_text += "Projected Annual Retirement Income: " + format_dollar(projected_income) + "\
\
"
    analysis_text += "Emergency Fund:\
"
    analysis_text += "Target Emergency Fund: " + format_dollar(target_emergency) + "\
"
    analysis_text += "Current Savings: " + format_dollar(current_savings) + "\
\
"
    st.download_button(
        label="Download Your Financial Analysis",
        data=analysis_text,
        file_name=name + "_Personal_Financial_Analysis.txt",
        mime="text/plain"
    )
