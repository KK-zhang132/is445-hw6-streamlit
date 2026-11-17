from pathlib import Path
import altair as alt
import streamlit as st
from analysis import SOURCE_URL, load_inventory, filter_inventory, agency_summary, decade_summary

st.set_page_config(page_title="Illinois, Built | IS 445 HW6", page_icon="🏛️", layout="wide")
st.markdown("""<style>
.block-container {max-width:1180px; padding-top:3rem; padding-bottom:3rem;}
h1 {letter-spacing:-0.045em;}
h2 {letter-spacing:-0.025em;}
[data-testid="stMetricValue"] {color:#147D78;}
</style>""", unsafe_allow_html=True)

@st.cache_data
def get_data():
    return load_inventory()

df = get_data()
st.caption("IS 445 · HOMEWORK 6 · JIEHONG ZHANG")
st.title("Illinois, built.")
st.markdown("### Two ways to read the state's building inventory")
st.markdown("Explore **which agencies account for the inventory** and **when buildings with different uses were constructed**. These are records in the course dataset, not a live inventory of every building in Illinois.")

with st.sidebar:
    st.header("Explore the inventory")
    st.caption("These filters update both visualizations.")
    counties = st.multiselect("County", sorted(df["county"].unique()), placeholder="All counties", key="counties")
    status = st.selectbox("Building status", ["All statuses"] + sorted(df["status"].unique()), key="status")
    st.caption("No county selected means all counties. Status labels are preserved from the source.")
    st.divider()
    st.markdown(f"[Course dataset ↗]({SOURCE_URL})")
    st.markdown("[Source code ↗](https://github.com/KK-zhang132/is445-hw6-streamlit)")
    st.caption("A fixed copy of the CSV is included in the repository so the report stays reproducible.")

selected = filter_inventory(df, counties, status)
summary = agency_summary(selected)
a, b, c = st.columns(3)
a.metric("Inventory records", f"{len(selected):,}")
b.metric("Floor area (million sq ft)", f"{summary['area'].sum() / 1_000_000:,.2f}")
c.metric("Agencies represented", f"{selected['agency'].nunique():,}")
st.caption("Scope: " + (", ".join(counties) if counties else "All counties") + " · " + status + ". Each CSV row counts as one inventory record.")

st.divider()
st.subheader("01 / Who accounts for the inventory?")
st.markdown("A large number of records does not necessarily mean a large share of floor area. **Switch the ranking metric** to compare the two.")
left, right = st.columns([3, 2])
metric = left.radio("Rank agencies by", ["Total floor area", "Number of records"], horizontal=True, key="metric")
top_n = right.slider("Maximum agencies shown", 5, 20, 10, key="top_n")
field = "million_sqft" if metric == "Total floor area" else "records"
x_title = "Total reported floor area (million sq ft)" if field == "million_sqft" else "Inventory records"
ranked = summary.sort_values([field, "agency"], ascending=[False, True]).head(top_n)
if ranked.empty:
    st.info("No records match these filters. Choose another county or status.")
else:
    base = alt.Chart(ranked).encode(
        x=alt.X(f"{field}:Q", title=x_title, scale=alt.Scale(zero=True), axis=alt.Axis(format=".1f" if field == "million_sqft" else ",d")),
        y=alt.Y("agency:N", title=None, sort=ranked["agency"].tolist(), axis=alt.Axis(labelLimit=350)),
        tooltip=[alt.Tooltip("agency:N", title="Agency"), alt.Tooltip("records:Q", title="Records", format=","), alt.Tooltip("area:Q", title="Floor area (sq ft)", format=",")],
    )
    stems = base.mark_rule(color="#BAD4CF", strokeWidth=3).encode(x2=alt.datum(0))
    dots = base.mark_circle(color="#147D78", size=110, opacity=1)
    chart = (stems + dots).properties(height=max(220, len(ranked) * 32), title="Agency ranking within the selected inventory").configure_axis(labelFontSize=12, titleFontSize=13).configure_view(stroke=None)
    st.altair_chart(chart, width="stretch", theme=None)
    leader = ranked.iloc[0]
    denominator = summary[field].sum()
    if denominator > 0:
        st.caption(f"In this selection, {leader['agency']} ranks first and accounts for {leader[field] / denominator:.1%} of {'reported floor area' if field == 'million_sqft' else 'records'} across all selected agencies (including those outside the displayed top {top_n}).")

st.markdown("**Design reflection — visualization 1.** This lollipop chart highlights how agency rankings change when the inventory is measured by total floor area instead of the number of records. Horizontal position on a linear scale supports precise comparisons, and every stem starts at zero so the distances remain proportional. Agencies are sorted from largest to smallest for the selected metric; horizontal labels leave room for long agency names. A single dark teal color keeps attention on magnitude without suggesting an extra category, while lighter stems guide the eye to each dot. The metric switch, county filter, status filter, and top-agency slider recompute the plotted results, providing interaction beyond hover or zoom. Counts include all selected rows, while area totals use only positive reported square footage. With more time, I would add a paired-rank view so readers could track each agency's movement between the two metrics without remembering the previous ordering.")

st.divider()
st.subheader("02 / When were buildings with different uses constructed?")
st.markdown("Read each row across time. **Switch to within-use percentages** to compare the timing of construction for common and uncommon uses.")
mode = st.radio("Heatmap measure", ["Share within each use", "Number of records"], horizontal=True, key="heat_mode")
usages = selected["usage"].value_counts().head(8).index.tolist()
heat = decade_summary(selected, usages)
if heat.empty:
    st.info("No valid construction years are available for this selection.")
else:
    is_share = mode == "Share within each use"
    color = alt.Color("share:Q", title="Share within use", scale=alt.Scale(scheme="tealblues", domain=[0, 1]), legend=alt.Legend(format=".0%")) if is_share else alt.Color("records:Q", title="Records", scale=alt.Scale(scheme="tealblues", zero=True))
    chart = alt.Chart(heat).mark_rect(stroke="#FAFAF7", strokeWidth=1).encode(
        x=alt.X("decade:O", title="Construction decade (start year)", sort="ascending", axis=alt.Axis(labelAngle=-45, labelOverlap=True)),
        y=alt.Y("usage:N", title=None, sort=usages, axis=alt.Axis(labelLimit=200)),
        color=color,
        tooltip=[alt.Tooltip("usage:N", title="Building use"), alt.Tooltip("decade:O", title="Decade begins"), alt.Tooltip("records:Q", title="Records", format=","), alt.Tooltip("share:Q", title="Share of dated records within use", format=".1%")],
    ).properties(height=max(180, len(usages) * 42), title="Construction decades for the eight most frequent uses").configure_axis(labelFontSize=12, titleFontSize=13, grid=False).configure_view(stroke=None)
    st.altair_chart(chart, width="stretch", theme=None)
    dated_count = int(heat["records"].sum())
    st.caption(f"Showing {dated_count:,} dated records in the {len(usages)} most frequent uses (ranked by all selected records). {selected['year'].isna().sum():,} selected records have unknown/invalid construction years and are omitted from this chart. Percentages sum to 100% within each nonempty row; they are not shares of all buildings.")

st.markdown("**Design reflection — visualization 2.** The heatmap highlights concentrations of construction decades across the eight most frequent building uses in the current selection. Equal-width columns follow chronological decade order, rows identify use categories, and rectangular marks make the two-dimensional grouping compact. A light-to-dark sequential teal-blue palette represents increasing magnitude; color is appropriate here because the goal is to spot concentrations rather than read exact differences. The default measure divides each cell by the total number of dated records for that use, with a fixed 0–100% color scale, so a common category such as Storage does not dominate merely because it has more records. The count toggle reveals absolute volume instead, while tooltips provide both values. Empty decade/use combinations are filled with zero, and unknown construction years are excluded rather than treated as year zero. This is the age composition of buildings represented in the dataset, not a complete history of construction or demolition. With more time, I would add a selectable detail panel for one use and a separate missing-year comparison, making smaller patterns and uneven data coverage easier to examine.")

st.divider()
st.subheader("Data notes & relationship to HW5")
st.markdown("**No data, plots, or write-up text are reused from HW5.** HW5 explored BFRO Bigfoot reports with a seasonal stacked bar chart and a geographic point map. HW6 uses the Illinois building inventory, an agency lollipop ranking, and a construction-decade heatmap. Both the dataset and the visual questions are different; all explanatory text here is newly written.")
with st.expander("Source, cleaning, and interpretation", expanded=False):
    st.markdown(f"""- **Source:** [building_inventory.csv]({SOURCE_URL}), provided in the IS 445 course repository. The included snapshot contains **{len(df):,} records**.
- **Unit:** one row in the source CSV. Similar-looking rows are retained because the file has no unique building identifier that would justify automatic deduplication.
- **Area:** {int((df['sqft'].isna() | (df['sqft'] <= 0)).sum()):,} rows have missing or nonpositive square footage. They count as records but contribute no floor area.
- **Dates:** {int(df['year'].isna().sum()):,} rows have unknown or invalid construction years. The heatmap uses positive integer years through 2026 and bins them into calendar decades.
- **Categories:** original agency, status, and use labels are retained, including abbreviated labels such as “Detention & Correc.”
- **Scope:** totals describe the course data snapshot; no claim is made that it covers all Illinois buildings or their present-day status.
""")
    st.download_button("Download the source CSV", Path(__file__).with_name("data").joinpath("building_inventory.csv").read_bytes(), "building_inventory.csv", "text/csv")
st.caption("Built with Streamlit, pandas, and Altair · IS 445 / Fall 2026")
