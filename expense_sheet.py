import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Personal Finance Dashboard 2025", layout="wide")

st.title("💰 Personal Finance Dashboard 2025")
st.caption("Realistic take-home pay with OBBBA overtime rules • Smart budgeting")

# --- STATE TAX AVERAGES ---
STATE_TAX_RATES = {
    "None / No State Tax": 0.00,
    "California": 0.093,
    "New York": 0.0685,
    "Texas": 0.00,
    "Florida": 0.00,
    "Pennsylvania": 0.0307,
    "Illinois": 0.0495,
    "Ohio": 0.035,
    "Georgia": 0.0549,
    "North Carolina": 0.0475,
    "Michigan": 0.0425,
}


def get_state_rate(state):
    return STATE_TAX_RATES.get(state, 0.05)


# --- SIDEBAR ---
with st.sidebar:
    st.header("📈 Income")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        filing_status = st.selectbox("Filing Status", ["Single", "Married Filing Jointly"], index=0)
    with col_g2:
        state = st.selectbox("State", sorted(STATE_TAX_RATES.keys()))

    gross_monthly_salary = st.number_input("Gross Monthly Base Salary ($)", min_value=0.0, value=8000.0, step=500.0)

    st.markdown("**Gross Monthly Overtime Pay**")
    st.caption("Total overtime earnings (e.g., time-and-a-half pay received)")
    gross_overtime_monthly = st.number_input("Gross Overtime Pay ($/mo)", min_value=0.0, value=0.0, step=100.0,
                                             help="Full overtime amount paid")

    other_net_income = st.number_input("Other Monthly Income (Net)", min_value=0.0, value=0.0, step=100.0)

    # --- TAX ESTIMATION ---
    gross_annual_salary = gross_monthly_salary * 12
    gross_overtime_annual = gross_overtime_monthly * 12
    gross_annual_total = gross_annual_salary + gross_overtime_annual

    # FICA
    ss_tax = min(gross_annual_total, 176100) * 0.062
    medicare_tax = gross_annual_total * 0.0145
    fica_annual = ss_tax + medicare_tax

    # Federal Income Tax
    std_ded = 31500 if filing_status == "Married Filing Jointly" else 15750
    taxable_base = max(0, gross_annual_total - std_ded)

    if filing_status == "Married Filing Jointly":
        brackets = [(0, 23850, 0.10), (23850, 96950, 0.12), (96950, 206700, 0.22),
                    (206700, 394600, 0.24), (394600, 501050, 0.32), (501050, 751600, 0.35),
                    (751600, taxable_base, 0.37)]
    else:
        brackets = [(0, 11925, 0.10), (11925, 48475, 0.12), (48475, 103350, 0.22),
                    (103350, 197300, 0.24), (197300, 250525, 0.32), (250525, 626350, 0.35),
                    (626350, taxable_base, 0.37)]

    fed_tax_full = 0
    prev = 0
    for low, high, rate in brackets:
        if taxable_base > prev:
            fed_tax_full += (min(taxable_base, high) - prev) * rate
        prev = high

    # OBBBA Overtime Premium Deduction (assume 1/3 of OT is premium)
    premium_annual = gross_overtime_annual / 3
    ot_cap = 25000 if filing_status == "Married Filing Jointly" else 12500
    phase_limit = 300000 if filing_status == "Married Filing Jointly" else 150000
    approx_magi = gross_annual_total

    if approx_magi < phase_limit:
        ot_deduction = min(premium_annual, ot_cap)
    else:
        ot_deduction = 0

    fed_tax_savings = ot_deduction * (fed_tax_full / max(taxable_base, 1) if taxable_base > 0 else 0.22)
    fed_tax_actual = fed_tax_full - fed_tax_savings

    # State Tax
    state_rate = get_state_rate(state)
    state_tax = gross_annual_total * state_rate

    total_tax_annual = fica_annual + fed_tax_actual + state_tax
    net_annual = gross_annual_total - total_tax_annual
    net_monthly = net_annual / 12

    total_take_home = net_monthly + other_net_income

    st.metric("Estimated Take-Home Pay", f"${total_take_home:,.2f}")
    if gross_overtime_monthly > 0:
        st.caption(f"Includes ~${fed_tax_savings / 12:,.0f}/mo federal tax savings from OBBBA")

    st.markdown("---")
    st.header("📊 Monthly Expenses (Excluding Savings)")

# --- LIFESTYLE EXPENSE CATEGORIES ---
default_expenses = {
    "Housing (Rent/Mortgage)": 2000,
    "Utilities": 250,
    "Groceries & Dining": 600,
    "Transportation": 400,
    "Insurance": 500,
    "Debt Payments": 300,
    "Entertainment & Subscriptions": 200,
    "Personal Care & Clothing": 150,
    "Miscellaneous": 300
}

lifestyle_expenses = {}
total_lifestyle_expenses = 0
for category, default in default_expenses.items():
    amount = st.sidebar.number_input(category, min_value=0.0, value=float(default), step=50.0, key=f"exp_{category}")
    lifestyle_expenses[category] = amount
    total_lifestyle_expenses += amount

st.sidebar.metric("Total Lifestyle Expenses", f"${total_lifestyle_expenses:,.2f}")

st.sidebar.markdown("---")
st.sidebar.subheader("💰 Planned Savings & Investments")
planned_savings = st.sidebar.number_input("Monthly Savings & Investments ($)", min_value=0.0, value=800.0, step=100.0,
                                          help="401k, IRA, brokerage, emergency fund, etc.")

money_leftover = total_take_home - total_lifestyle_expenses - planned_savings

st.sidebar.metric("Money Leftover (After Planned Savings)", f"${money_leftover:,.2f}")

# --- MAIN DASHBOARD: 4 METRICS AT TOP ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Take-Home Income", f"${total_take_home:,.2f}")
col2.metric("Lifestyle Expenses", f"${total_lifestyle_expenses:,.2f}")
col3.metric("Savings & Investments", f"${planned_savings:,.2f}")
col4.metric("Money Leftover", f"${money_leftover:,.2f}")

st.markdown("---")

# --- PIE CHART: Now includes Savings & Investments ---
all_spending_categories = {**lifestyle_expenses, "Savings & Investments": planned_savings}
total_spending = total_lifestyle_expenses + planned_savings

if total_spending > 0:
    fig_pie = px.pie(
        values=list(all_spending_categories.values()),
        names=list(all_spending_categories.keys()),
        title="Full Monthly Spending Breakdown (incl. Savings)",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

# Bar Overview
df_summary = pd.DataFrame({
    "Category": ["Take-Home Income", "Lifestyle Expenses", "Savings & Investments", "Money Leftover"],
    "Amount": [total_take_home, total_lifestyle_expenses, planned_savings, max(money_leftover, 0)]
})
fig_bar = px.bar(
    df_summary,
    x="Category",
    y="Amount",
    title="Monthly Cash Flow Overview",
    text="Amount",
    color="Category",
    color_discrete_map={
        "Take-Home Income": "#00CC96",
        "Lifestyle Expenses": "#EF553B",
        "Savings & Investments": "#636EFA",
        "Money Leftover": "#FFA15A"
    }
)
fig_bar.update_traces(texttemplate='$%{text:,.0f}')
st.plotly_chart(fig_bar, use_container_width=True)

# Annual View
st.subheader("📅 Annual Projection")
col_a1, col_a2, col_a3, col_a4 = st.columns(4)
col_a1.metric("Annual Take-Home", f"${total_take_home * 12:,.0f}")
col_a2.metric("Annual Lifestyle Expenses", f"${total_lifestyle_expenses * 12:,.0f}")
col_a3.metric("Annual Planned Savings", f"${planned_savings * 12:,.0f}")
col_a4.metric("Annual Leftover", f"${money_leftover * 12:,.0f}")

# Feedback
if money_leftover > 500:
    st.success(f"🎉 You're in great shape — ${money_leftover:,.0f}/mo extra after planned savings!")
elif money_leftover > 0:
    st.info(f"👍 ${money_leftover:,.0f} leftover each month — room to boost savings or enjoy.")
elif money_leftover > -500:
    st.warning("⚠️ Slightly over budget — small tweaks could help.")
else:
    st.error(f"😬 Overspending by ${abs(money_leftover):,.0f}/mo — consider adjusting.")

# --- EXPORT ---
st.markdown("---")
st.subheader("📥 Export Your Budget")

df_export = pd.DataFrame({
    "Category": ["Gross Base Salary (Monthly)", "Gross Overtime (Monthly)", "Est. OBBBA Tax Savings (Monthly)",
                 "Take-Home Pay", "Other Income", "Planned Savings & Investments"] +
                list(lifestyle_expenses.keys()) + ["Total Lifestyle Expenses", "Money Leftover"],
    "Amount ($)": [gross_monthly_salary, gross_overtime_monthly, fed_tax_savings / 12,
                   net_monthly, other_net_income, planned_savings] +
                  list(lifestyle_expenses.values()) + [total_lifestyle_expenses, money_leftover]
})

col_ex1, col_ex2 = st.columns(2)
with col_ex1:
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.download_button("📄 Download CSV", data=csv, file_name=f"Budget_{datetime.now().strftime('%Y%m%d')}.csv",
                       mime="text/csv")

with col_ex2:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Budget')
    buffer.seek(0)
    st.download_button("📈 Download Excel", data=buffer.getvalue(),
                       file_name=f"Budget_{datetime.now().strftime('%Y%m%d')}.xlsx")

st.caption("2025 estimates • OBBBA overtime benefit included • Not financial advice")
