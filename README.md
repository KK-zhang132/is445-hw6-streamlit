# Illinois, built — IS 445 HW6

A Streamlit report exploring the course's Illinois building inventory.

**Live app:** https://kk-zhang132-is445-hw6.streamlit.app/

**Repository:** https://github.com/KK-zhang132/is445-hw6-streamlit

## Visualizations

1. An agency lollipop ranking switches between reported floor area and record count, with an adjustable top-N limit.
2. A construction-decade × building-use heatmap switches between counts and within-use percentages.

County and status filters update both charts. Each chart has an original paragraph explaining its purpose, design, and possible improvements. No HW5 data, plots, or write-up text are reused: HW5 used BFRO reports, a stacked bar chart, and a map.

## Run

Python 3.12:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Deploy this public repository on Streamlit Community Cloud using branch `main` and entrypoint `streamlit_app.py`. No secrets are needed. Keep the app public.

## Data

[Original course CSV](https://raw.githubusercontent.com/UIUC-iSchool-DataViz/is445_data/main/building_inventory.csv)

A fixed copy is included in `data/building_inventory.csv`. Each row counts as an inventory record. No deduplication is performed because the source lacks a unique building identifier. Nonpositive or missing area does not contribute to area totals, but those rows remain in record counts. Unknown or invalid construction years are excluded from the heatmap, which shows the eight most frequent uses in the selected inventory. Percentages use dated records within each use as their denominator. Empty decade/use combinations are filled with zero. The dataset is a historical snapshot, not a live census of Illinois buildings.

## Validation

Run `python validate.py` for aggregation checks and Streamlit AppTest interaction tests.
