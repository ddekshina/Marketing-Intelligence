import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# Helper: clean column names
# -------------------------
def clean_columns(df):
    return df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"))

# -------------------------
# Load Data
# -------------------------
@st.cache_data
def load_data():
    files = {
        "Facebook": "data/Facebook.csv",
        "Google": "data/Google.csv",
        "TikTok": "data/TikTok.csv"
    }
    dfs = []
    for channel, filepath in files.items():
        temp = pd.read_csv(filepath)
        temp = clean_columns(temp)
        temp["channel"] = channel
        dfs.append(temp)

    all_data = pd.concat(dfs, ignore_index=True)

    # metrics
    all_data["cpc"] = all_data["spend"] / all_data["clicks"].replace(0, pd.NA)
    all_data["ctr"] = all_data["clicks"] / all_data["impression"].replace(0, pd.NA)
    all_data["roas"] = all_data["attributed_revenue"] / all_data["spend"].replace(0, pd.NA)

    business = pd.read_csv("data/Business.csv")
    business = clean_columns(business)

    daily_summary = (
        all_data.groupby("date", as_index=False)
        .agg({
            "impression": "sum",
            "clicks": "sum",
            "spend": "sum",
            "attributed_revenue": "sum"
        })
    )
    daily_summary["cpc"] = daily_summary["spend"] / daily_summary["clicks"].replace(0, pd.NA)
    daily_summary["ctr"] = daily_summary["clicks"] / daily_summary["impression"].replace(0, pd.NA)
    daily_summary["roas"] = daily_summary["attributed_revenue"] / daily_summary["spend"].replace(0, pd.NA)

    combined = pd.merge(business, daily_summary, on="date", how="left")
    return all_data, business, combined, daily_summary

# -------------------------
# Data Prep
# -------------------------
all_data, business, combined, daily_summary = load_data()

# Ensure datetime
combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
combined = combined.dropna(subset=["date"])

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Marketing Intelligence Dashboard", layout="wide")
st.title("📊 Marketing Intelligence Dashboard")

# Date filter
date_range = st.slider(
    "Select Date Range",
    min_value=combined["date"].min().to_pydatetime(),
    max_value=combined["date"].max().to_pydatetime(),
    value=(combined["date"].min().to_pydatetime(), combined["date"].max().to_pydatetime())
)

filtered = combined[(combined["date"] >= date_range[0]) & (combined["date"] <= date_range[1])]

# -------------------------
# KPIs
# -------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Total Spend", f"${filtered['spend'].sum():,.0f}")
col2.metric("Total Revenue", f"${filtered['total_revenue'].sum():,.0f}")
col3.metric("Avg ROAS", f"{filtered['roas'].mean():.2f}")

# -------------------------
# Spend vs Revenue Over Time
# -------------------------
st.subheader("Spend vs Revenue Over Time")
st.line_chart(filtered.set_index("date")[["spend", "total_revenue"]])

# -------------------------
# ROAS Over Time
# -------------------------
st.subheader("ROAS Over Time")
st.line_chart(filtered.set_index("date")[["roas"]])

# -------------------------
# Channel Breakdown
# -------------------------
st.subheader("Channel Breakdown")

channel_summary = (
    all_data.groupby("channel", as_index=False)
    .agg({
        "impression": "sum",
        "clicks": "sum",
        "spend": "sum",
        "attributed_revenue": "sum"
    })
)
channel_summary["roas"] = channel_summary["attributed_revenue"] / channel_summary["spend"].replace(0, pd.NA)

col1, col2 = st.columns(2)

with col1:
    st.bar_chart(channel_summary.set_index("channel")[["spend", "attributed_revenue"]])

with col2:
    st.bar_chart(channel_summary.set_index("channel")[["roas"]])

# -------------------------
# Campaign Leaderboards
# -------------------------
st.subheader("Campaign Leaderboards")

campaign_summary = (
    all_data.groupby("campaign", as_index=False)
    .agg({
        "impression": "sum",
        "clicks": "sum",
        "spend": "sum",
        "attributed_revenue": "sum"
    })
)
campaign_summary["roas"] = campaign_summary["attributed_revenue"] / campaign_summary["spend"].replace(0, pd.NA)

col1, col2 = st.columns(2)

with col1:
    top_roas = campaign_summary.sort_values("roas", ascending=False).head(10)
    st.write("### Top 10 Campaigns by ROAS")
    st.dataframe(top_roas[["campaign", "spend", "attributed_revenue", "roas"]])

with col2:
    top_spend = campaign_summary.sort_values("spend", ascending=False).head(10)
    st.write("### Top 10 Campaigns by Spend")
    st.dataframe(top_spend[["campaign", "spend", "attributed_revenue", "roas"]])

# -------------------------
# Anomaly Detection & Recommendations
# -------------------------
st.subheader("⚠️ Anomaly Detection & Recommendations")

# Low ROAS campaigns
low_roas = campaign_summary[campaign_summary["roas"] < 0.5]
if not low_roas.empty:
    st.write("### 🚨 Low ROAS Campaigns (ROAS < 0.5)")
    st.dataframe(low_roas[["campaign", "spend", "attributed_revenue", "roas"]])
    st.warning("Recommendation: Pause or optimize these campaigns — they are not cost-effective.")

# Spend spikes
spend_mean = daily_summary["spend"].mean()
spend_std = daily_summary["spend"].std()
spike_threshold = spend_mean + 3 * spend_std
spikes = daily_summary[daily_summary["spend"] > spike_threshold]

if not spikes.empty:
    st.write("### 🚨 Spend Spikes Detected")
    st.dataframe(spikes[["date", "spend", "attributed_revenue", "roas"]])
    st.warning("Recommendation: Investigate these dates for possible overspending or errors.")
