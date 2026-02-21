import streamlit as st
import data_loader

st.set_page_config(page_title="QA Platform", layout="wide")

# Load test_history data
df = data_loader.load_history()
unique_scenarios = df["scenario"].unique()

st.sidebar.markdown("### Filters")
st.sidebar.caption("Use the filter below to see specific scenarios.")
scenario_filter = st.sidebar.multiselect(
    "Filter by scenario:",
    options=unique_scenarios,
    default=unique_scenarios
)
df = df[df["scenario"].isin(scenario_filter)]

# Calculate KPIs from test data
overall_pass_rate = df["pass_rate"].mean()
total_rollbacks = int(df["rollback_triggered"].sum())
total_deployments = len(df)

# MTTR: average days between a rollback and the next clean pass_rate=1.0 day
rollback_days = df[df["rollback_triggered"]].index.tolist()
mttr_values = []
for idx in rollback_days:
    recovery = df[(df.index > idx) & (df["pass_rate"] == 1.0)]
    if not recovery.empty:
        mttr_values.append(recovery.index[0] - idx)
avg_mttr = f"{sum(mttr_values) / len(mttr_values):.0f} days" if mttr_values else "N/A"

st.title("QA Validation Platform — Release Health")
st.caption("Use the sidebar to filter by scenario.")

tab1, tab2 = st.tabs(["Release Health", "Device Event Log"])

with tab1:
    # Top row: 4 KPI cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Pass Rate", f"{overall_pass_rate:.1%}")
    col2.metric("Deployments", total_deployments)
    col3.metric("Rollbacks (30d)", total_rollbacks)
    col4.metric("Avg. MTTR", avg_mttr)

    # Pass rate trend line chart
    st.subheader("Pass Rate Trend")
    st.line_chart(df.set_index("date")["pass_rate"])

    # Rollout history table with rollback rows highlighted in red
    st.subheader("Rollout History")

    def highlight_rollbacks(row):
        return ["color: #ff4444; font-weight: bold" if row["rollback_triggered"] else "" for _ in row]

    st.dataframe(df.style.apply(highlight_rollbacks, axis=1), use_container_width=True)

with tab2:
    st.subheader("Device Event Log")
    st.info(
        "This is the raw per-device audit log written by the device simulator. "
        "Each row is one state transition on one device (IDLE → UPDATING → UPDATED or ROLLED_BACK). "
        "It is not used for KPI calculations, that is handled by the summarised rollout history in the other tab."
    )
    
    events_df = data_loader.load_events()
    if events_df.empty:
        st.warning("No event data found. Run device_simulator/seed_history.py first.")
    else:
        st.dataframe(events_df, use_container_width=True)