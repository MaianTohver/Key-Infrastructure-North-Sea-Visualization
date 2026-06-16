import streamlit as st
import altair as alt
import pandas as pd
import folium
from folium.features import DivIcon
from branca.colormap import linear
from folium.plugins import PolyLineTextPath, PolyLineOffset
from streamlit_folium import st_folium

from .process_data import aggregate_time, export_csv

def plot_chart(df):
    """
    Plots an altair area chart
    """
    df = df.reset_index()
    df = pd.melt(df, value_vars=df.columns, id_vars=['Timeslice'])

    if len(df['Timeslice'].unique()) == 1:
        chart = alt.Chart(df).mark_bar().encode(
            x='Timeslice:Q',
            y='sum(value):Q',
            color="Variable:N").configure_legend(orient='bottom').interactive()
    else:
        chart = alt.Chart(df).mark_area().encode(
            x='Timeslice:Q',
            y='sum(value):Q',
            color="Variable:N").configure_legend(orient='bottom').interactive()

    return chart

def plot_nodes(map, node_data):
    for node_name, data in node_data.iterrows():
        folium.CircleMarker(
            location=[data['lat'], data['lon']],
            radius=5,  # Adjust the radius as needed
            color='black',  # Marker color
            fill=True,
            fill_color='black',  # Fill color
            fill_opacity=0.7,
        ).add_to(map)
        folium.map.Marker(
            [data['lat'], data['lon']],
            icon=DivIcon(icon_size=(150, 36),
                         icon_anchor=(-5, 20),
                         html='<div style="font-size: 9pt">' + node_name + '</div>')
        ).add_to(map)


def plot_technology_design():
    """
    Plots the technology design
    """
    data = st.session_state['Result']['technology_design']
    data = data[data['Variable']!= 'technology']

    with st.form('PlottingOptions'):
        all_vars = data['Variable'].unique()
        selected_var = st.selectbox('**Variable Selection**', all_vars)

        technologies = data['Technology'].unique()
        selected_technologies = st.multiselect('**Technology Selection**', technologies,
                                               default=technologies)

        submitted = st.form_submit_button('Plot')

    if submitted:
        data = data[data['Variable'] == selected_var]
        data = data[data['Technology'].isin(selected_technologies)]

        st.header(selected_var)

        chart = alt.Chart(data).mark_bar().encode(
            y='Node:N',
            x=alt.X('Value:Q', title=selected_var),
            color='Technology:N'
        ).interactive()
        st.altair_chart(chart, width='stretch')


def plot_energy_balance():
    """
    Plots the energy balance
    """
    data = st.session_state['Result']['energybalance']

    # with st.form('PlottingOptions'):
    carriers = data.columns.get_level_values('Carrier').unique()
    selected_carrier = st.selectbox('**Carrier Selection**', carriers)

    nodes = data.columns.get_level_values('Node').unique()
    selected_node = st.selectbox('**Node Selection**', nodes)

    time_agg_options = {'Annual Totals': 'Year',
                        'Monthly Totals': 'Month',
                        'Weekly Totals': 'Week',
                        'Daily Totals': 'Day',
                        'Hourly Totals': 'Hour'}
    time_agg = st.selectbox('**Time Aggregation**', time_agg_options.keys())

    # submitted = st.form_submit_button('Plot')

    # if submitted:
    data = data.loc[:, (selected_node, selected_carrier, slice(None), slice(None))]

    aggregated_data = aggregate_time(data, time_agg_options[time_agg])

    st.header("Supply")
    series_supply = ['generic_production',
                     'technology_outputs',
                     'network_inflow',
                     'import']
    selected_supply_series = st.multiselect('Select Series to Filter', series_supply,
                                            default=series_supply)

    plot_data = aggregated_data.loc[:,
                aggregated_data.columns.get_level_values('Variable').isin(selected_supply_series)]
    plot_data.columns = plot_data.columns.get_level_values('Variable')
    chart = plot_chart(plot_data)
    st.altair_chart(chart, theme="streamlit", width='stretch')

    st.header("Demand")
    # Multi-select box for filtering series
    series_demand = ['demand',
                     'technology_inputs',
                     'network_outflow',
                     'export']
    selected_demand_series = st.multiselect('Select Series to Filter', series_demand,
                                            default=series_demand)
    plot_data = aggregated_data.loc[:,
                aggregated_data.columns.get_level_values('Variable').isin(selected_demand_series)]
    plot_data.columns = plot_data.columns.get_level_values('Variable')
    chart = plot_chart(plot_data)
    st.altair_chart(chart, theme="streamlit", width='stretch')


def plot_technology_operation():
    """
    Plots technology operation
    """
    data = st.session_state['Result']['technology_operation']

    nodes = list(data.columns.get_level_values('Node').unique())
    nodes = ["Aggregate all nodes"] + nodes
    selected_node = st.selectbox('**Node Selection**', nodes)
    if selected_node == "Aggregate all nodes":
        data = data.T.groupby(level=[1 ,2]).sum().T
        data.columns = pd.MultiIndex.from_tuples(
            [('Aggregated_node',) + col for col in data.columns]
        )
        data.columns.names = ['Node', 'Technology', 'Variable']

    else:
        data = data.loc[:, (selected_node, slice(None), slice(None))]

    technologies = data.columns.get_level_values('Technology').unique()
    selected_technology = st.selectbox('**Technology Selection**', technologies)

    time_agg_options = {'Annual Totals': 'Year',
                        'Monthly Totals': 'Month',
                        'Weekly Totals': 'Week',
                        'Daily Totals': 'Day',
                        'Hourly Totals': 'Hour'}
    time_agg = st.selectbox('**Time Aggregation**', time_agg_options.keys())

    data = data.loc[:, (slice(None), selected_technology, slice(None))]
    aggregated_data = aggregate_time(data, time_agg_options[time_agg])


    with st.form('PlottingOptions'):

        submitted = st.form_submit_button('Plot')

        if submitted:

            st.header("Input")
            variables_in = [col for col in aggregated_data.columns.get_level_values('Variable') if col.endswith('input')]
            plot_data = aggregated_data.loc[:, (slice(None), slice(None), variables_in)]
            plot_data.columns = plot_data.columns.get_level_values('Variable')
            if not plot_data.empty:
                chart = plot_chart(plot_data)
                st.altair_chart(chart, theme="streamlit", width='stretch')
            else:
                st.markdown("Nothing to show")

            # Output
            st.header("Output")
            variables_out = [col for col in aggregated_data.columns.get_level_values('Variable') if col.endswith('output')]
            plot_data = aggregated_data.loc[:, (slice(None), slice(None), variables_out)]
            plot_data.columns = plot_data.columns.get_level_values('Variable')
            if not plot_data.empty:
                chart = plot_chart(plot_data)
                st.altair_chart(chart, theme="streamlit", width='stretch')
            else:
                st.markdown("Nothing to show")

            st.header("Other Variables")
            variables_other = [x for x in aggregated_data.columns.get_level_values('Variable') if
                               ((x not in variables_in) & (x not in variables_out))]
            plot_data = aggregated_data.loc[:, (slice(None), slice(None), variables_other)]
            plot_data.columns = plot_data.columns.get_level_values('Variable')
            if not plot_data.empty:
                chart = plot_chart(plot_data)
                st.altair_chart(chart, theme="streamlit", width='stretch')
            else:
                st.markdown("Nothing to show")

    export_csv(
        aggregated_data,
        "Download plotted data as csv",
        "time_series.csv",
    )

def plot_network_design():
    data = st.session_state['Result']['network_design']

    with st.form('PlottingOptions'):
        networks_available = list(data['Network'].unique())
        selected_netw = st.multiselect('Select a network:', networks_available)

        variables_available = list(data.columns)
        variables_available.remove("Arc_ID")
        variables_available.remove("Network")
        variables_available.remove("FromNode")
        variables_available.remove("ToNode")

        selected_variable = st.selectbox('Select a variable:', variables_available)
        submitted = st.form_submit_button('Plot')

        if submitted:
            data = data[data['Network'].isin(selected_netw)]

            if data.empty:
                st.warning("No data for the selected network(s). Please select at least one network.")
            else:
                arc_ids = data[['Arc_ID', 'FromNode', 'ToNode']]
                data = data.groupby('Arc_ID').sum(numeric_only=True).reset_index()
                data = data.merge(arc_ids.drop_duplicates('Arc_ID'), on='Arc_ID')

                # Init map
                node_data = st.session_state['NodeLocations']
                map_center = [node_data['lat'].mean(), node_data['lon'].mean()]
                map = folium.Map(location=map_center, zoom_start=5)

                # Plot nodes
                plot_nodes(map, node_data)

                # Plot edges
                if selected_variable in ['size', 'capex', 'total_flow']:
                    max_value = data[selected_variable].max()
                    if max_value > 0:
                        color_scale = linear.OrRd_09.scale(0, 1)

                        for _, edge_data in data.iterrows():
                            from_node_data = node_data.loc[edge_data.FromNode]
                            to_node_data = node_data.loc[edge_data.ToNode]

                            normalized_value = edge_data[selected_variable] / max_value
                            color = color_scale(normalized_value)
                            if normalized_value > 0.001:
                                line = folium.plugins.PolyLineOffset(
                                    [(from_node_data['lat'], from_node_data['lon']),
                                     (to_node_data['lat'], to_node_data['lon'])],
                                    color=color,
                                    weight=3.5,
                                    opacity=1,
                                    offset=3,
                                    tooltip=edge_data[selected_variable]
                                ).add_to(map)
                                attr = {"font-weight": "bold", "font-size": "13"}
                                folium.plugins.PolyLineTextPath(
                                    line, "      >", repeat=True, offset=5, attributes=attr
                                ).add_to(map)

                st_folium(map, width=725)


def plot_network_operation():
    data = st.session_state['Result']['network_operation']

    networks = data.columns.get_level_values('Network').unique()
    selected_network = st.multiselect('**Network Selection**', networks)

    time_agg_options = {'Annual Totals': 'Year',
                        'Monthly Totals': 'Month',
                        'Weekly Totals': 'Week',
                        'Daily Totals': 'Day',
                        'Hourly Totals': 'Hour'}
    time_agg = st.selectbox('**Time Aggregation**', time_agg_options.keys())
    data = data.loc[:, (selected_network, slice(None), 'flow')]
    aggregated_data = aggregate_time(data, time_agg_options[time_agg])

    if time_agg != 'Annual Totals':
        selected_timeslice = st.slider("Select a time slice: ", min_value=min(aggregated_data.index), max_value=max(aggregated_data.index))
        aggregated_data = aggregated_data[aggregated_data.index == selected_timeslice]

    data = aggregated_data.T

    data.columns = ['Flow']
    data = data.reset_index()
    submitted = st.button('Plot')

    if submitted:
        if not selected_network:
            st.warning("Please select at least one network.")
        elif data.empty:
            st.warning("No data for the selected network(s).")
        else:
            arc_ids = data[['Arc_ID', 'FromNode', 'ToNode']]
            data = data.groupby('Arc_ID').sum()
            data.drop(columns=['FromNode', 'ToNode', 'Network'], inplace=True)
            data = data.merge(arc_ids, on='Arc_ID')

            # Init map
            node_data = st.session_state['NodeLocations']
            map_center = [node_data['lat'].mean(), node_data['lon'].mean()]
            map = folium.Map(location=map_center, zoom_start=5)

            # Plot nodes
            plot_nodes(map, node_data)

            # Plot edges
            max_value = data['Flow'].max()
            color_scale = linear.OrRd_09.scale(0, 1)

            for _, edge_data in data.iterrows():
                from_node_data = node_data.loc[edge_data.FromNode]
                to_node_data = node_data.loc[edge_data.ToNode]

                flow_this_direction = edge_data['Flow']
                flow_other_direction = data[
                    (data['FromNode'] == to_node_data.name) &
                    (data['ToNode'] == from_node_data.name)]

                uni_flow = flow_this_direction - flow_other_direction.loc[:, 'Flow'].values[0]

                if uni_flow > 0.1:
                    normalized_value = uni_flow / max_value
                    color = color_scale(normalized_value)
                    folium.plugins.AntPath(
                        locations=[(from_node_data['lat'], from_node_data['lon']),
                                   (to_node_data['lat'], to_node_data['lon'])],
                        color=color, dash_array=[10, 20], weight=5,
                    ).add_to(map)

            st_folium(map, width=725)
