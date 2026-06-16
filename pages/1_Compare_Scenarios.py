import pandas as pd
import streamlit as st
from pathlib import Path
import altair as alt

st.set_page_config(page_title="Compare Scenarios", layout="wide")

# Initialize back-end processing/caching
if 'load_cash' in globals():
    load_cash()

st.header("Compare Scenarios")
scenarios = {
    "Baseline": "RE_only",
    "Onshore DAC Only": "Onshore_DAC_only",
    "Offshore DAC Only": "Offshore_DAC_only"
}

case_keys = {}
case_keys["2030"] = {"costs": "min costs"}
case_keys["2040"] = {"costs": "min costs"}

with st.expander("Explanations"):
    st.subheader("Target year")
    st.markdown("The scenarios evaluate energy system deployment variants for 2030 and 2040.")
    st.subheader("Optimization")
    st.markdown("**Costs** optimizations minimize total system costs, composed of "
                "fixed and variable infrastructure expenses alongside negative emission asset implementations.")
    st.subheader("Scenarios")
    st.markdown("In the **Baseline** scenario, no negative emission tech is allowed. "
                "In the **Onshore DAC** scenario, carbon capture facilities are bound to terrestrial grid points. "
                "In the **Offshore DAC** scenario, capture facilities are integrated out at sea with marine generation hubs.")
year_selected = st.selectbox("Select target year", [2040])
case_selected = st.selectbox("Select optimization", list(case_keys[str(year_selected)].keys()))
cy_selected = st.selectbox("Select climate year", [2009])

scenarios_selected = st.multiselect("Select scenarios to compare", list(scenarios.keys()))
scenarios_selected_mapped = [scenarios[k] for k in scenarios_selected]

# Variable Setup
all_vars = st.session_state["HeaderKeys"].copy()

if case_selected == "net emissions":
    all_vars = all_vars[all_vars["Available for net_emissions"] == 1]

if year_selected == 2030:
    all_vars = all_vars[all_vars["Available 2030"] == 1]

all_vars = all_vars.dropna()

variables_available = all_vars.sort_values(by=["Key"]).set_index(["Key"])
units = all_vars.sort_values(by=["Key"]).set_index(["Key"])["Unit"].to_dict()
factors = all_vars.sort_values(by=["Key"]).set_index(["Key"])["Factor"].to_dict()
variables_selected = st.multiselect("Select variable to plot", list(variables_available.index))
unstack_cols = st.checkbox("Unstack Columns")
summary_df = st.session_state["Summary" + str(year_selected)]
plot_data = summary_df[summary_df[("global", "global", "objective")] == case_keys[str(year_selected)][case_selected]]
plot_data = plot_data[plot_data[("global", "global", "Case")].isin(scenarios_selected_mapped)]
cols = [("global", "global", "Case"), ("global", "global", "Subcase"), ("global", "global", "cy")]
cols.extend([(variables_available.loc[key]["level0"], variables_available.loc[key]["level1"], variables_available.loc[key]["level2"]) for key in variables_selected])
plot_data = plot_data[cols]

column_names = []
for col in plot_data.columns:
    column_names.append(st.session_state["HeaderKeys"][
        (st.session_state["HeaderKeys"]["level0"] == col[0]) &
        (st.session_state["HeaderKeys"]["level1"] == col[1]) &
        (st.session_state["HeaderKeys"]["level2"] == col[2])
    ]["Key"].values[0])
plot_data.columns = column_names

plot_data = plot_data.fillna(0)
plot_data["Case_Subcase"] = plot_data['Case'] + ' - ' + plot_data['Subcase']
plot_data = plot_data.drop(columns=['Case', 'Subcase'])
plot_data = plot_data.set_index(['Case_Subcase', "climate_year"])

for col in plot_data.columns:
    plot_data[col] = plot_data[col] * variables_available.loc[col]["Factor"]

plot_data = plot_data.reset_index().melt(id_vars=['Case_Subcase', "climate_year"])

plot_data_base_cy = plot_data[plot_data['climate_year'] == cy_selected]
plot_data_other_cy = plot_data[plot_data['climate_year'] != cy_selected]
if 'export_csv' in globals():
    export_csv(plot_data, "Download shown data", "ScenarioComparison.csv")

# Merge units
units_merge = st.session_state["HeaderKeys"].dropna().sort_values(by=["Key"]).set_index(["Key"])["Unit"]
plot_data_base_cy = plot_data_base_cy.merge(units_merge, right_index=True, left_on="variable")
plot_data_other_cy = plot_data_other_cy.merge(units_merge, right_index=True, left_on="variable")

unit_to_show = [units[key] for key in variables_selected]
unit_to_show = list(set(unit_to_show))
unit_to_show = " / ".join(unit_to_show)
if unstack_cols:
    base_year = (alt.Chart(plot_data_base_cy).encode(
        y=alt.Y('Case_Subcase:N', title=None, axis=alt.Axis(labelLimit=200)),
        x=alt.X('value:Q', title=unit_to_show),
        color=alt.Color('variable', legend=alt.Legend(title=None, orient="top", columns=1, labelLimit=500)),
        row=alt.Row('variable:N', title="", spacing=90),
        tooltip=[alt.Tooltip('Case_Subcase:N', title="Sub-scenario"),
                 alt.Tooltip('variable:N', title="Variable"),
                 alt.Tooltip('value:Q', title="Value"),
                 alt.Tooltip('Unit:N', title="Unit")]
    ))
    st.altair_chart(base_year.mark_bar(), theme="streamlit", width='stretch')

else:
    plot_data_other_cy_summed = plot_data_other_cy.groupby(["climate_year", "Case_Subcase"])[['value']].sum().reset_index()

    base_year = alt.Chart(plot_data_base_cy).encode(
        y=alt.Y('Case_Subcase:N', title=None, axis=alt.Axis(labelLimit=200)),
        x=alt.X('value:Q', title=unit_to_show),
        color=alt.Color('variable', legend=alt.Legend(title=None, orient="top", columns=1, labelLimit=500)),
        tooltip=[alt.Tooltip('Case_Subcase:N', title="Sub-scenario"),
                 alt.Tooltip('variable:N', title="Variable"),
                 alt.Tooltip('value:Q', title="Value"),
                 alt.Tooltip('Unit:N', title="Unit")]
    ).interactive()

    other_years = alt.Chart(plot_data_other_cy_summed).mark_point(size=100).encode(
        y=alt.Y('Case_Subcase:N', title=None, axis=alt.Axis(labelLimit=200)),
        x=alt.X('value:Q', title=unit_to_show),
        shape=alt.Shape('climate_year:N', legend=alt.Legend(title="Climate year", orient="top")),
        color=alt.value('black')
    ).interactive()
    st.altair_chart(base_year.mark_bar() + other_years.mark_point(), theme="streamlit", width='stretch')