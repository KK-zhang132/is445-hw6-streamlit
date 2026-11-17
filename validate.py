from pathlib import Path
import pandas as pd
from streamlit.testing.v1 import AppTest
from analysis import load_inventory, agency_summary, decade_summary, filter_inventory

root = Path(__file__).parent
df = load_inventory()
raw = pd.read_csv(root / 'data/building_inventory.csv')
assert len(df) == len(raw) == 8862
summary = agency_summary(df)
assert summary.records.sum() == len(raw)
assert summary.area.sum() == raw['Square Footage'].clip(lower=0).sum()
assert int(df.year.isna().sum()) == 289
uses = df.usage.value_counts().head(8).index.tolist()
heat = decade_summary(df, uses)
assert heat.records.sum() == len(df[df.year.notna() & df.usage.isin(uses)])
assert (heat.groupby('usage').share.sum().round(10) == 1).all()
assert heat.decade.min() > 0 and heat.records.min() == 0
at = AppTest.from_file(str(root / 'streamlit_app.py'), default_timeout=30).run()
assert not at.exception, at.exception
assert len(at.get('vega_lite_chart')) == 2
initial = at.metric[0].value
at.radio(key='metric').set_value('Number of records').run()
assert not at.exception
at.radio(key='heat_mode').set_value('Number of records').run()
assert not at.exception
at.multiselect(key='counties').set_value(['Cook']).run()
assert not at.exception and at.metric[0].value != initial
at.selectbox(key='status').set_value('In Use').run()
assert not at.exception
assert int(at.metric[0].value.replace(',', '')) == len(raw[(raw.County == 'Cook') & (raw['Bldg Status'] == 'In Use')])
at.slider(key='top_n').set_value(20).run()
assert not at.exception
empty = next((c,s) for c in df.county.unique() for s in df.status.unique() if filter_inventory(df,[c],s).empty)
at.multiselect(key='counties').set_value([empty[0]])
at.selectbox(key='status').set_value(empty[1]).run()
assert not at.exception and at.metric[0].value == '0'
assert len(at.info) == 2
print('PASS: raw totals, date cleaning, heatmap denominators, both charts, both metric toggles, county/status/top-N filters, empty selection.')
print(summary.sort_values('area', ascending=False).head(3).to_string(index=False))
