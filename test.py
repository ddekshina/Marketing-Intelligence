import pandas as pd

# Load the CSV
df = pd.read_csv("data/Facebook.csv")

# Add metrics
df["CPC"] = df["spend"] / df["clicks"]
df["CTR"] = df["clicks"] / df["impression"]
df["ROAS"] = df["attributed revenue"] / df["spend"]

# Group by campaign
campaign_summary = (
    df.groupby("campaign", as_index=False)
      .agg({
          "impression": "sum",
          "clicks": "sum",
          "spend": "sum",
          "attributed revenue": "sum"
      })
)

# Recalculate metrics at campaign level
campaign_summary["CPC"] = campaign_summary["spend"] / campaign_summary["clicks"]
campaign_summary["CTR"] = campaign_summary["clicks"] / campaign_summary["impression"]
campaign_summary["ROAS"] = campaign_summary["attributed revenue"] / campaign_summary["spend"]

print(campaign_summary.head())

# ---- Daily aggregation (time series) ----
daily_summary = (
    df.groupby("date", as_index=False)
      .agg({
          "impression": "sum",
          "clicks": "sum",
          "spend": "sum",
          "attributed revenue": "sum"
      })
)

# Recalculate metrics at daily level
daily_summary["CPC"] = daily_summary["spend"] / daily_summary["clicks"]
daily_summary["CTR"] = daily_summary["clicks"] / daily_summary["impression"]
daily_summary["ROAS"] = daily_summary["attributed revenue"] / daily_summary["spend"]

print("\n=== Daily summary ===")
print(daily_summary.head())

# ---- Combine all channels ----
files = {
    "Facebook": "data/Facebook.csv",
    "Google": "data/Google.csv",
    "TikTok": "data/TikTok.csv"
}

dfs = []
for channel, filepath in files.items():
    temp = pd.read_csv(filepath)
    temp["channel"] = channel   # add a new column
    dfs.append(temp)

# Merge into one big dataset
all_data = pd.concat(dfs, ignore_index=True)

# Add metrics
all_data["CPC"] = all_data["spend"] / all_data["clicks"]
all_data["CTR"] = all_data["clicks"] / all_data["impression"]
all_data["ROAS"] = all_data["attributed revenue"] / all_data["spend"]

print("\n=== Combined data across channels ===")
print(all_data.head())

# ---- Channel-level aggregation ----
channel_summary = (
    all_data.groupby("channel", as_index=False)
      .agg({
          "impression": "sum",
          "clicks": "sum",
          "spend": "sum",
          "attributed revenue": "sum"
      })
)

# Recalculate metrics per channel
channel_summary["CPC"] = channel_summary["spend"] / channel_summary["clicks"]
channel_summary["CTR"] = channel_summary["clicks"] / channel_summary["impression"]
channel_summary["ROAS"] = channel_summary["attributed revenue"] / channel_summary["spend"]

print("\n=== Channel summary ===")
print(channel_summary)

# ---- Load Business data ----
business = pd.read_csv("data/Business.csv")

print("\n=== Business data ===")
print(business.head())

# ---- Merge with daily marketing summary ----
# First, aggregate all channels daily
marketing_daily = (
    all_data.groupby("date", as_index=False)
      .agg({
          "impression": "sum",
          "clicks": "sum",
          "spend": "sum",
          "attributed revenue": "sum"
      })
)

# Add marketing metrics
marketing_daily["CPC"] = marketing_daily["spend"] / marketing_daily["clicks"]
marketing_daily["CTR"] = marketing_daily["clicks"] / marketing_daily["impression"]
marketing_daily["ROAS"] = marketing_daily["attributed revenue"] / marketing_daily["spend"]

# Merge on 'date' to align marketing with business KPIs
combined = pd.merge(business, marketing_daily, on="date", how="left")

print("\n=== Business + Marketing combined ===")
print(combined.head())
