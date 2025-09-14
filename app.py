import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# -------------------------
# Data Loading & Preparation
# -------------------------

def clean_columns(df):
    """Clean column names - remove spaces, lowercase, handle inconsistencies"""
    return df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"))

@st.cache_data
def load_data():
    """Load and combine all marketing data with business metrics"""
    
    # Load marketing data from all channels
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
    
    # Combine all marketing data
    all_marketing = pd.concat(dfs, ignore_index=True)
    
    # Calculate key marketing metrics
    # Had to handle division by zero carefully
    all_marketing["ctr"] = all_marketing["clicks"] / all_marketing["impression"].replace(0, np.nan)
    all_marketing["cpc"] = all_marketing["spend"] / all_marketing["clicks"].replace(0, np.nan)
    all_marketing["roas"] = all_marketing["attributed_revenue"] / all_marketing["spend"].replace(0, np.nan)
    
    # Load business data
    business = pd.read_csv("data/Business.csv")
    business = clean_columns(business)
    
    # Create daily marketing summary for joining with business data
    daily_marketing = all_marketing.groupby("date").agg({
        "impression": "sum",
        "clicks": "sum", 
        "spend": "sum",
        "attributed_revenue": "sum"
    }).reset_index()
    
    # Calculate daily metrics
    daily_marketing["daily_ctr"] = daily_marketing["clicks"] / daily_marketing["impression"].replace(0, np.nan)
    daily_marketing["daily_cpc"] = daily_marketing["spend"] / daily_marketing["clicks"].replace(0, np.nan) 
    daily_marketing["daily_roas"] = daily_marketing["attributed_revenue"] / daily_marketing["spend"].replace(0, np.nan)
    
    # Combine business and marketing data
    combined = pd.merge(business, daily_marketing, on="date", how="left")
    
    # Add business context metrics - learned these are important for stakeholders
    combined["marketing_revenue_share"] = combined["attributed_revenue"] / combined["total_revenue"].replace(0, np.nan)
    combined["marketing_spend_ratio"] = combined["spend"] / combined["total_revenue"].replace(0, np.nan)
    
    return all_marketing, business, combined, daily_marketing

# -------------------------
# Main App
# -------------------------

# Load data
all_marketing, business, combined, daily_marketing = load_data()

# Convert dates to datetime for filtering
combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
combined = combined.dropna(subset=["date"])

# Page configuration
st.set_page_config(page_title="Marketing Intelligence Dashboard", layout="wide")
st.title("📊 Marketing Intelligence Dashboard")
st.markdown("*AI-assisted analysis combining marketing performance with business outcomes*")

# -------------------------
# Sidebar Filters
# -------------------------

st.sidebar.header("📅 Filters")

# Date range selector
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(combined["date"].min().date(), combined["date"].max().date()),
    min_value=combined["date"].min().date(),
    max_value=combined["date"].max().date()
)

# Filter data
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered = combined[
        (combined["date"] >= pd.to_datetime(start_date)) & 
        (combined["date"] <= pd.to_datetime(end_date))
    ]
else:
    filtered = combined

# Channel filter for detailed analysis
selected_channels = st.sidebar.multiselect(
    "Select Channels",
    options=all_marketing["channel"].unique(),
    default=all_marketing["channel"].unique()
)

# -------------------------
# Key Performance Indicators
# -------------------------

st.header("🎯 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

total_spend = filtered["spend"].sum()
total_business_revenue = filtered["total_revenue"].sum()
total_attributed_revenue = filtered["attributed_revenue"].sum()
avg_roas = filtered["daily_roas"].mean()

col1.metric("Total Marketing Spend", f"${total_spend:,.0f}")
col2.metric("Total Business Revenue", f"${total_business_revenue:,.0f}")
col3.metric("Marketing Attributed Revenue", f"${total_attributed_revenue:,.0f}")
col4.metric("Average ROAS", f"{avg_roas:.2f}" if not pd.isna(avg_roas) else "N/A")

# Marketing efficiency context
if total_business_revenue > 0:
    marketing_contribution = (total_attributed_revenue / total_business_revenue) * 100
    st.info(f"💡 Marketing contributes **{marketing_contribution:.1f}%** of total business revenue")

# -------------------------
# Performance Trends
# -------------------------

st.header("📈 Performance Over Time")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Spend vs Revenue Trends")
    # Using matplotlib for more control - learned this gives better customization
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(filtered["date"], filtered["spend"], label="Marketing Spend", color="#1f77b4", linewidth=2)
    ax.plot(filtered["date"], filtered["total_revenue"], label="Business Revenue", color="#ff7f0e", linewidth=2)
    ax.set_xlabel("Date")
    ax.set_ylabel("Amount ($)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.subheader("ROAS Trend")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(filtered["date"], filtered["daily_roas"], label="Daily ROAS", color="#2ca02c", linewidth=2)
    ax.axhline(y=1, color="red", linestyle="--", alpha=0.7, label="Break-even Line")
    ax.set_xlabel("Date")
    ax.set_ylabel("ROAS")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

# -------------------------
# Channel Performance Analysis
# -------------------------

st.header("📱 Channel Performance Breakdown")

# Filter marketing data by selected channels
filtered_marketing = all_marketing[all_marketing["channel"].isin(selected_channels)]

# Channel summary statistics
channel_stats = filtered_marketing.groupby("channel").agg({
    "impression": "sum",
    "clicks": "sum",
    "spend": "sum", 
    "attributed_revenue": "sum"
}).reset_index()

channel_stats["channel_ctr"] = channel_stats["clicks"] / channel_stats["impression"]
channel_stats["channel_cpc"] = channel_stats["spend"] / channel_stats["clicks"] 
channel_stats["channel_roas"] = channel_stats["attributed_revenue"] / channel_stats["spend"]

col1, col2 = st.columns(2)

with col1:
    st.subheader("Investment by Channel")
    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(channel_stats["channel"], channel_stats["spend"], color=["#1f77b4", "#ff7f0e", "#2ca02c"])
    ax.set_ylabel("Spend ($)")
    ax.set_title("Marketing Investment by Channel")
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'${height:,.0f}', ha='center', va='bottom')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.subheader("ROAS by Channel")
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#2ca02c" if roas > 1 else "#d62728" for roas in channel_stats["channel_roas"]]
    bars = ax.bar(channel_stats["channel"], channel_stats["channel_roas"], color=colors)
    ax.axhline(y=1, color="black", linestyle="--", alpha=0.7, label="Break-even")
    ax.set_ylabel("ROAS")
    ax.set_title("Return on Ad Spend by Channel")
    ax.legend()
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}', ha='center', va='bottom')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

# Channel performance table
st.subheader("Channel Performance Summary")
display_cols = ["channel", "spend", "attributed_revenue", "channel_roas", "channel_ctr", "channel_cpc"]
formatted_stats = channel_stats[display_cols].copy()
formatted_stats["spend"] = formatted_stats["spend"].apply(lambda x: f"${x:,.0f}")
formatted_stats["attributed_revenue"] = formatted_stats["attributed_revenue"].apply(lambda x: f"${x:,.0f}")
formatted_stats["channel_roas"] = formatted_stats["channel_roas"].apply(lambda x: f"{x:.2f}")
formatted_stats["channel_ctr"] = formatted_stats["channel_ctr"].apply(lambda x: f"{x:.2%}")
formatted_stats["channel_cpc"] = formatted_stats["channel_cpc"].apply(lambda x: f"${x:.2f}")

st.dataframe(formatted_stats, use_container_width=True)

# -------------------------
# Campaign Analysis
# -------------------------

st.header("🎯 Campaign Performance Analysis")

# Campaign-level aggregation
campaign_stats = filtered_marketing.groupby("campaign").agg({
    "spend": "sum",
    "attributed_revenue": "sum", 
    "clicks": "sum",
    "impression": "sum"
}).reset_index()

campaign_stats["campaign_roas"] = campaign_stats["attributed_revenue"] / campaign_stats["spend"]
campaign_stats["campaign_ctr"] = campaign_stats["clicks"] / campaign_stats["impression"]

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Top Campaigns by ROAS")
    # Filter campaigns with meaningful spend to avoid outliers
    significant_campaigns = campaign_stats[campaign_stats["spend"] >= 100]
    top_roas = significant_campaigns.nlargest(10, "campaign_roas")
    
    display_cols = ["campaign", "spend", "attributed_revenue", "campaign_roas"]
    top_roas_display = top_roas[display_cols].copy()
    top_roas_display["spend"] = top_roas_display["spend"].apply(lambda x: f"${x:,.0f}")
    top_roas_display["attributed_revenue"] = top_roas_display["attributed_revenue"].apply(lambda x: f"${x:,.0f}")
    top_roas_display["campaign_roas"] = top_roas_display["campaign_roas"].apply(lambda x: f"{x:.2f}")
    
    st.dataframe(top_roas_display, use_container_width=True)

with col2:
    st.subheader("💰 Top Campaigns by Investment")
    top_spend = campaign_stats.nlargest(10, "spend")
    
    top_spend_display = top_spend[display_cols].copy()
    top_spend_display["spend"] = top_spend_display["spend"].apply(lambda x: f"${x:,.0f}")
    top_spend_display["attributed_revenue"] = top_spend_display["attributed_revenue"].apply(lambda x: f"${x:,.0f}")
    top_spend_display["campaign_roas"] = top_spend_display["campaign_roas"].apply(lambda x: f"{x:.2f}")
    
    st.dataframe(top_spend_display, use_container_width=True)

# -------------------------
# Advanced Analytics & Insights
# -------------------------

st.header("🔍 Advanced Analytics & Insights")

# Performance insights using AI-assisted analysis techniques
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Performance Insights")
    
    # Best and worst performing channels
    best_channel = channel_stats.loc[channel_stats["channel_roas"].idxmax()]
    worst_channel = channel_stats.loc[channel_stats["channel_roas"].idxmin()]
    
    st.success(f"🏆 **Top Performer**: {best_channel['channel']} (ROAS: {best_channel['channel_roas']:.2f})")
    st.error(f"⚠️ **Needs Attention**: {worst_channel['channel']} (ROAS: {worst_channel['channel_roas']:.2f})")
    
    # Marketing efficiency analysis
    if avg_roas > 2:
        st.info("💡 **Strong Performance**: ROAS above 2.0 suggests efficient marketing spend")
    elif avg_roas > 1:
        st.warning("⚖️ **Moderate Performance**: ROAS positive but room for optimization")
    else:
        st.error("🚨 **Performance Alert**: ROAS below break-even requires immediate attention")

with col2:
    st.subheader("🎯 Optimization Opportunities")
    
    # Identify underperforming campaigns with significant spend
    # Used AI to help identify this optimization approach
    underperforming = campaign_stats[
        (campaign_stats["campaign_roas"] < 0.8) & 
        (campaign_stats["spend"] > 500)
    ].sort_values("spend", ascending=False)
    
    if len(underperforming) > 0:
        st.warning(f"Found {len(underperforming)} high-spend campaigns with ROAS < 0.8")
        
        # Show top 5 for review
        review_campaigns = underperforming.head(5)[["campaign", "spend", "campaign_roas"]]
        review_campaigns["spend"] = review_campaigns["spend"].apply(lambda x: f"${x:,.0f}")
        review_campaigns["campaign_roas"] = review_campaigns["campaign_roas"].apply(lambda x: f"{x:.2f}")
        
        st.dataframe(review_campaigns, use_container_width=True)
        
        potential_savings = underperforming["spend"].sum() * 0.5  # Estimate 50% could be reallocated
        st.info(f"💰 Potential optimization: ~${potential_savings:,.0f} in spend could be reallocated")
    else:
        st.success("✅ No major underperforming campaigns identified")

# -------------------------
# Anomaly Detection
# -------------------------

st.header("🚨 Anomaly Detection")

# Statistical anomaly detection for spend spikes - AI helped implement this approach
spend_mean = daily_marketing["spend"].mean()
spend_std = daily_marketing["spend"].std()
upper_threshold = spend_mean + 2.5 * spend_std
lower_threshold = max(0, spend_mean - 2.5 * spend_std)

anomalies = daily_marketing[
    (daily_marketing["spend"] > upper_threshold) | 
    (daily_marketing["spend"] < lower_threshold)
].copy()

if len(anomalies) > 0:
    st.warning(f"🔍 Detected {len(anomalies)} spending anomalies using statistical thresholds")
    
    # Show recent anomalies
    recent_anomalies = anomalies.sort_values("date", ascending=False).head(5)
    anomaly_display = recent_anomalies[["date", "spend", "daily_roas"]].copy()
    anomaly_display["spend"] = anomaly_display["spend"].apply(lambda x: f"${x:,.0f}")
    anomaly_display["daily_roas"] = anomaly_display["daily_roas"].apply(lambda x: f"{x:.2f}" if not pd.isna(x) else "N/A")
    
    st.dataframe(anomaly_display, use_container_width=True)
else:
    st.success("✅ No significant spending anomalies detected")

# -------------------------
# Strategic Recommendations  
# -------------------------

st.header("💡 Strategic Recommendations")

recommendations = []

# Channel-based recommendations
best_roas_channel = channel_stats.loc[channel_stats["channel_roas"].idxmax()]
if best_roas_channel["channel_roas"] > 1.5:
    recommendations.append(f"🔥 **Scale Up**: Increase budget for {best_roas_channel['channel']} (ROAS: {best_roas_channel['channel_roas']:.2f})")

worst_roas_channel = channel_stats.loc[channel_stats["channel_roas"].idxmin()]  
if worst_roas_channel["channel_roas"] < 0.8:
    recommendations.append(f"⚠️ **Optimize**: Review {worst_roas_channel['channel']} strategy (ROAS: {worst_roas_channel['channel_roas']:.2f})")

# Overall performance recommendations
if avg_roas < 1.2:
    recommendations.append("🎯 **Focus**: Overall ROAS suggests need for campaign optimization and audience refinement")

# Budget reallocation suggestion
high_spend_low_roas = channel_stats[
    (channel_stats["spend"] > channel_stats["spend"].median()) & 
    (channel_stats["channel_roas"] < 1.0)
]

if len(high_spend_low_roas) > 0:
    total_inefficient_spend = high_spend_low_roas["spend"].sum()
    recommendations.append(f"💰 **Reallocation Opportunity**: ${total_inefficient_spend:,.0f} in spend from underperforming channels")

# Display recommendations
if recommendations:
    for i, rec in enumerate(recommendations, 1):
        st.write(f"{i}. {rec}")
else:
    st.success("✅ Current marketing performance appears well-optimized")

# -------------------------
# Footer
# -------------------------

st.markdown("---")
st.markdown("*Dashboard leveraging AI-assisted analysis for marketing intelligence • Built with Streamlit*")

# Technical notes for transparency
with st.expander("🔧 Technical Notes"):
    st.write("""
    **Data Processing:**
    - Combined data from Facebook, Google, and TikTok campaigns
    - Merged with business performance metrics
    - Applied statistical methods for anomaly detection
    
    **AI-Assisted Analysis:**
    - Used LLMs to identify key marketing analytics patterns
    - Implemented statistical anomaly detection techniques
    - Applied best practices for campaign performance evaluation
    
    **Key Metrics:**
    - ROAS: Return on Ad Spend (Revenue ÷ Spend)
    - CTR: Click-Through Rate (Clicks ÷ Impressions)
    - CPC: Cost Per Click (Spend ÷ Clicks)
    """)