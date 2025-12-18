import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Personal Finance Dashboard 2025", layout="wide")

st.title("💰 Personal Finance Dashboard 2025")
st.caption("Track your income, expenses, and savings • Simple monthly budgeting tool")

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.header("📊 Your Monthly Income")
    monthly_salary = st.number_input("Net Monthly Salary ($)", min_value=0.0, value=5000.0, step=100.0)
    other_income = st.number_input("Other Monthly Income ($)", min_value=0.0, value=0.0, step=50.0)
    total_income = monthly_salary + other_income
    st.metric("Total Monthly Income", f"${total_income:,.2f}")

    st.markdown("---")
    st.header("📈 Expense Categories")
    st.info("Adjust amounts below – based on 2025 US averages for reference")

# Default categories with realistic 2025 averages (single person ~$6,000-6,500/month total spend)
default_expenses = {
    "Housing (Rent/Mortgage)": 2000,
    "Utilities (Electric, Water, Internet)": 250,
    "Groceries & Dining": 600,
    "Transportation (Gas, Car, Transit)": 400,
    "Insurance (Health, Auto, etc.)": 500,
    "Debt Payments (Loans, Credit Cards)": 300,
    "Entertainment & Subscriptions": 200,
    "Personal Care & Clothing": 150,
    "Savings & Investments": 800,
    "Miscellaneous/Other": 300
}

expenses = {}
total_expenses = 0
for category, default in default_expenses.items():
    amount = st.sidebar.number_input(category, min_value=0.0, value=float(default), step=50.0, key=category)
    expenses[category] = amount
    total_expenses += amount

st.sidebar.metric("Total Monthly Expenses", f"${total_expenses:,.2f}")

savings = total_income - total_expenses
st.sidebar.metric("Monthly Savings / (Deficit)", f"${savings:,.2f}", delta=None)

annual_income = total_income * 12
annual_expenses = total_expenses * 12
annual_savings = savings * 12

# --- MAIN DASHBOARD ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Monthly Income", f"${total_income:,.2f}")
col2.metric("Monthly Expenses", f"${total_expenses:,.2f}")
col3.metric("Monthly Savings", f"${savings:,.2f}")
col4.metric("Savings Rate", f"{(savings / total_income * 100):.1f}%" if total_income > 0 else "0%")

st.markdown("---")

# Pie chart for expenses
if total_expenses > 0:
    fig_pie = px.pie(
        values=list(expenses.values()),
        names=list(expenses.keys()),
        title="Monthly Expense Breakdown",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

# Bar chart comparison
df_summary = pd.DataFrame({
    "Category": ["Income", "Expenses", "Savings"],
    "Amount ($)": [total_income, total_expenses, max(savings, 0)]
})
fig_bar = px.bar(df_summary, x="Category", y="Amount ($)", title="Monthly Overview", text="Amount ($)",
                 color="Category", color_discrete_sequence=["green", "red", "blue"])
fig_bar.update_traces(texttemplate='$%{text:,.0f}')
st.plotly_chart(fig_bar, use_container_width=True)

# Annual projection
st.subheader("📅 Annual Projection")
col_a1, col_a2, col_a3 = st.columns(3)
col_a1.metric("Projected Annual Income", f"${annual_income:,.2f}")
col_a2.metric("Projected Annual Expenses", f"${annual_expenses:,.2f}")
col_a3.metric("Projected Annual Savings", f"${annual_savings:,.2f}")

if savings > 0:
    st.success(f"🎉 Great job! You're saving ${savings:,.2f} per month ({(savings / total_income * 100):.1f}% of income).")
elif savings == 0:
    st.info("💡 You're breaking even – consider finding small ways to boost savings.")
else:
    st.warning(f"⚠️ You're spending ${abs(savings):,.2f} more than you earn each month. Look for areas to cut back.")

# --- EXPORTS ---
st.markdown("---")
st.subheader("📥 Export Your Budget")

df_export = pd.DataFrame({
    "Category": list(expenses.keys()) + ["Total Income", "Total Expenses", "Monthly Savings"],
    "Monthly Amount ($)": list(expenses.values()) + [total_income, total_expenses, savings]
})

col_ex1, col_ex2 = st.columns(2)

with col_ex1:
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Download CSV",
        data=csv,
        file_name=f"Budget_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

with col_ex2:
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Monthly Budget')
    excel_buffer.seek(0)
    st.download_button(
        label="📈 Download Excel",
        data=excel_buffer.getvalue(),
        file_name=f"Budget_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.caption("Built with ❤️ using Streamlit • Estimates only • Adjust to your real numbers!")