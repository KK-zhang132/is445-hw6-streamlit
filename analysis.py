"""Data transformations shared by the Streamlit report and validation."""
from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).parent / "data" / "building_inventory.csv"
SOURCE_URL = "https://raw.githubusercontent.com/UIUC-iSchool-DataViz/is445_data/main/building_inventory.csv"


def load_inventory():
    df = pd.read_csv(DATA_PATH).rename(columns={
        "Agency Name": "agency", "County": "county", "Bldg Status": "status",
        "Usage Description": "usage", "Year Constructed": "year",
        "Square Footage": "sqft",
    })
    for col in ["agency", "county", "status", "usage"]:
        df[col] = df[col].fillna("Not provided").str.strip()
    df["sqft"] = pd.to_numeric(df["sqft"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    # Zero is an unknown year, not a construction year. Keep unknown dates in plot 1.
    df["year"] = df["year"].where(df["year"].between(1, 2026) & (df["year"] % 1 == 0))
    return df


def filter_inventory(df, counties, status):
    result = df
    if counties:
        result = result[result["county"].isin(counties)]
    if status != "All statuses":
        result = result[result["status"] == status]
    return result.copy()


def agency_summary(df):
    # Nonpositive or missing areas do not contribute to totals; records still count.
    return (df.assign(area=df["sqft"].where(df["sqft"] > 0, 0))
            .groupby("agency", as_index=False)
            .agg(records=("agency", "size"), area=("area", "sum"))
            .assign(million_sqft=lambda x: x["area"] / 1_000_000))


def decade_summary(df, usages):
    dated = df[df["year"].notna() & df["usage"].isin(usages)].copy()
    if dated.empty:
        return pd.DataFrame(columns=["usage", "decade", "records", "share"])
    dated["decade"] = (dated["year"] // 10 * 10).astype(int)
    decades = range(int(dated["decade"].min()), int(dated["decade"].max()) + 10, 10)
    grid = pd.MultiIndex.from_product([usages, decades], names=["usage", "decade"])
    counts = dated.groupby(["usage", "decade"]).size().reindex(grid, fill_value=0).rename("records").reset_index()
    totals = counts.groupby("usage")["records"].transform("sum")
    counts["share"] = counts["records"].div(totals.where(totals > 0)).fillna(0)
    return counts
