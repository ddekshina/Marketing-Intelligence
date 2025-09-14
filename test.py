import pandas as pd

# Load the CSV
df = pd.read_csv("data/Facebook.csv")

# Calculate metrics
df["CPC"] = df["spend"] / df["clicks"]
df["CTR"] = df["clicks"] / df["impression"]
df["ROAS"] = df["attributed revenue"] / df["spend"]

# Show important columns
print(df[["date", "campaign", "spend", "attributed revenue", "CPC", "CTR", "ROAS"]].head())
