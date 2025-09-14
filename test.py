import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# Helper: clean column names
# -------------------------
def clean_columns(df):
    return df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"))

# -------------------------
# Load Marketing Data (all channels)
# -------------------------
files = {
    "Facebook": "data/Facebook.csv",
    "Google": "data/Google.csv",
    "TikTok": "data/TikTok.csv"
}

dfs = []
for channel, filepath in files.items():
    temp = pd.read_csv(filepath)
    temp = clean_columns(temp)         # standardize columns
    temp["channel"] = channel          # add channel column
    dfs.append(temp)

# Merge all channels into one DataFrame
all_data = pd.concat(dfs, ignore_index=True)

# Add metrics
all_data["cpc"] = all_data["spend"] / all_data["clicks"]
all_data["ctr"] = all_data["clicks"] / all_data["impression"]
all_data["roas"] = all_data["attributed_revenue"] / all_data["spend"]

print("\n=== Combined Marketing Data ===")
print(all_data.head())

# -------------------------
# Campaign Summary
# -------------------------
campaign_summary = (
    all_data.groupby("campaign", as_index=False)
      .agg({
          "impression": "sum",
          "clicks": "sum",
          "spend": "sum",
          "attributed_revenue": "sum"
      })
)
campaign_summary["cpc"] = campaign_summary["spend"] / campaign_summary["clicks"]
campaign_summary["ctr"] = campaign_summary["clicks"] / campaign_summary["impression"]
campaign_summary["roas"] = campaign_summary["attributed_revenue"] / campaign_summary["spend"]

print("\n=== Campaign Summary ===")
print(campaign_summary.head())

# -------------------------
# Daily Summary
# -------------------------
daily_summary = (
    all_data.groupby("date", as_index=False)
      .agg({
          "impression": "sum",
          "clicks": "sum",
          "spend": "sum",
          "attributed_revenue": "sum"
      })
)
daily_summary["cpc"] = daily_summary["spend"] / daily_summary["clicks"]
daily_summary["ctr"] = daily_summary["clicks"] / daily_summary["impression"]
daily_summary["roas"] = daily_summary["attributed_revenue"] / daily_summary["spend"]

print("\n=== Daily Summary ===")
print(daily_summary.head())

# -------------------------
# Channel Summary
# -------------------------
channel_summary = (
    all_data.groupby("channel", as_index=False)
      .agg({
          "impression": "sum",
          "clicks": "sum",
          "spend": "sum",
          "attributed_revenue": "sum"
      })
)
channel_summary["cpc"] = channel_summary["spend"] / channel_summary["clicks"]
channel_summary["ctr"] = channel_summary["clicks"] / channel_summary["impression"]
channel_summary["roas"] = channel_summary["attributed_revenue"] / channel_summary["spend"]

print("\n=== Channel Summary ===")
print(channel_summary)

# -------------------------
# Business Integration
# -------------------------
business = pd.read_csv("data/Business.csv")
business = clean_columns(business)

print("\n=== Business Data ===")
print(business.head())

# Merge daily marketing with business data
combined = pd.merge(business, daily_summary, on="date", how="left")

# Add ratios
combined["marketing_revenue_pct"] = combined["attributed_revenue"] / combined["total_revenue"]
combined["marketing_spend_pct"] = combined["spend"] / combined["total_revenue"]
combined["gross_margin_pct"] = combined["gross_profit"] / combined["total_revenue"]

print("\n=== Business + Marketing Combined ===")
print(combined[["date", "total_revenue", "spend", "attributed_revenue",
                "marketing_revenue_pct", "marketing_spend_pct", "gross_margin_pct"]].head())


# ---- Plot 1: Spend vs Revenue over Time ----
plt.figure(figsize=(12,5))

plt.plot(combined["date"], combined["spend"], label="Marketing Spend", color="red")
plt.plot(combined["date"], combined["total_revenue"], label="Total Revenue", color="blue")

plt.xlabel("Date")
plt.ylabel("Amount ($)")
plt.title("Spend vs Revenue Over Time")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# ---- Plot 2: ROAS over Time ----
plt.figure(figsize=(12,5))

plt.plot(combined["date"], combined["roas"], label="ROAS", color="green")

plt.axhline(y=1, color="gray", linestyle="--", linewidth=1)  # breakeven line
plt.xlabel("Date")
plt.ylabel("ROAS (Revenue ÷ Spend)")
plt.title("ROAS (Return on Ad Spend) Over Time")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# -------------------------
# Channel Breakdown: Spend vs Revenue
# -------------------------
plt.figure(figsize=(10,6))

plt.bar(channel_summary["channel"], channel_summary["spend"], label="Spend", color="red", alpha=0.6)
plt.bar(channel_summary["channel"], channel_summary["attributed_revenue"], label="Revenue", color="blue", alpha=0.6)

plt.xlabel("Channel")
plt.ylabel("Amount ($)")
plt.title("Spend vs Revenue by Channel")
plt.legend()
plt.tight_layout()
plt.show()

# -------------------------
# Channel Breakdown: ROAS
# -------------------------
plt.figure(figsize=(10,6))

plt.bar(channel_summary["channel"], channel_summary["roas"], color="green")

plt.axhline(y=1, color="gray", linestyle="--", linewidth=1)  # breakeven line
plt.xlabel("Channel")
plt.ylabel("ROAS")
plt.title("ROAS by Channel")
plt.tight_layout()
plt.show()

# -------------------------
# Campaign Leaderboard (Top 10 by ROAS)
# -------------------------
top_campaigns = campaign_summary.sort_values("roas", ascending=False).head(10)

plt.figure(figsize=(12,6))
plt.barh(top_campaigns["campaign"], top_campaigns["roas"], color="green")
plt.axvline(x=1, color="gray", linestyle="--", linewidth=1)  # breakeven line
plt.xlabel("ROAS")
plt.title("Top 10 Campaigns by ROAS")
plt.gca().invert_yaxis()  # highest at the top
plt.tight_layout()
plt.show()

# -------------------------
# Campaign Leaderboard (Top 10 by Spend)
# -------------------------
biggest_campaigns = campaign_summary.sort_values("spend", ascending=False).head(10)

plt.figure(figsize=(12,6))
plt.barh(biggest_campaigns["campaign"], biggest_campaigns["spend"], color="red")
plt.xlabel("Spend ($)")
plt.title("Top 10 Campaigns by Spend")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()


