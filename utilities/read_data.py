import h5py
import pandas as pd
import streamlit as st
import numpy as np

@st.cache_data
def load_nodes_from_h5_results(path):
    """
    Loads all nodes contained in a results file as a list
    """
    with h5py.File(path) as hdf_file:
        nodes = extract_data_from_h5_dataset(hdf_file["topology/nodes"])

    return nodes


@st.cache_data
def load_carriers_from_h5_results(path):
    """
    Loads all carriers contained in a results file as a list
    """
    with h5py.File(path) as hdf_file:
        carriers = extract_data_from_h5_dataset(hdf_file["topology/carriers"])

    return carriers


def extract_datasets_from_h5_group(group, prefix=()):
    """
    Gets all datasets from a group of an h5 file and writes it to a multi-index dataframe

    :param group: group of h5 file
    :return: dataframe containing all datasets in group
    """
    data = {}
    for key, value in group.items():
        if isinstance(value, h5py.Group):
            data.update(extract_datasets_from_h5_group(value, prefix + (key,)))
        elif isinstance(value, h5py.Dataset):
            if value.shape == ():
                data[prefix + (key,)] = [value[()]]
            else:
                data[prefix + (key,)] = value[:]

    df = pd.DataFrame(data)

    return df


def extract_data_from_h5_dataset(dataset):
    """
    Gets dataset from an h5 file

    :param group: group of h5 file
    :return: dataframe containing all datasets in group
    """
    data = [item.decode('utf-8') for item in dataset]

    return data

def export_csv(df, label, filename):
    """
    Makes a button on the side bar that allows for csv export
    :param df: dataframe to export
    :param label: label of button
    :param filename: filename to export
    :return:
    """
    excel_buffer = df.to_csv(index=False, sep=';')
    st.sidebar.download_button(
        label=label,
        data=excel_buffer,
        file_name=filename,
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


def add_time_steps_to_df(df):
    """
    Adds time index to a df
    """
    hour = df.index.to_list()
    num_rows = len(hour)
    day = np.repeat(np.arange(1, num_rows + 1), 24)[0:num_rows]
    week = np.repeat(np.arange(1, num_rows + 1), 24 * 7)[0:num_rows]
    month = pd.date_range(start='2008-01-01 00:00', end='2008-12-31 00:00', freq='1h').month[0:num_rows].to_list()
    year = np.ones(num_rows)

    df.index = pd.MultiIndex.from_arrays([hour, day, week, month, year],
                                             names=['Hour', 'Day', 'Week', 'Month', 'Year'])
    
    return df

def read_results_from_h5(path_h5):
    """
    Reads the energybalance, technology operation, design and network operation, design into a dict
    """
    res = {}

    loading_data_bar = st.progress(0, text="Loading energy balance")
    res['energybalance'] = read_energy_balance(path_h5)
    loading_data_bar.progress(20, text="Loading technology operation")
    res['technology_operation'] = read_technology_operation(path_h5)
    loading_data_bar.progress(60, text="Loading technology design")
    res['technology_design'] = read_technology_design(path_h5)
    loading_data_bar.progress(80, text="Loading network operation and design")
    res['network_design'], res['network_operation'] = read_networks(path_h5)
    loading_data_bar.progress(100, text="Done")

    return res
    


def read_energy_balance(path_h5):
    """
    Reads energybalance
    """
    with h5py.File(path_h5, 'r') as hdf_file:
        df_bal = extract_datasets_from_h5_group(hdf_file["operation/energy_balance"])

    df_bal = df_bal['period1']
    df_bal = df_bal.rename_axis(columns=['Node', 'Carrier', 'Variable'])
    df_bal = add_time_steps_to_df(df_bal)

    return df_bal

def read_technology_operation(path_h5):
    """
    Reads technology operation
    """
    with h5py.File(path_h5, 'r') as hdf_file:
        df_ope = extract_datasets_from_h5_group(hdf_file["operation/technology_operation"])

    df_ope = df_ope['period1']
    df_ope = df_ope.rename_axis(columns=['Node', 'Technology', 'Variable'])
    df_ope = add_time_steps_to_df(df_ope)

    return df_ope

def read_technology_design(path_h5):
    """
    Reads technology design
    """
    with h5py.File(path_h5, 'r') as hdf_file:
        technology_design = extract_datasets_from_h5_group(hdf_file["design/nodes"])
        technology_design = technology_design['period1']
        technology_design = pd.melt(technology_design)
        technology_design.columns = ['Node', 'Technology', 'Variable', 'Value']

    return technology_design

def read_networks(path_h5):
    with h5py.File(path_h5, 'r') as hdf_file:
        network_design = extract_datasets_from_h5_group(hdf_file["design/networks"])
    network_design = network_design['period1']
    network_design = network_design.melt()
    network_design.columns = ['Network', 'Arc_ID', 'Variable', 'Value']
    network_design = network_design.pivot(columns='Variable', index=['Arc_ID', 'Network'], values='Value')
    network_design['FromNode'] = network_design['fromNode'].apply(
        lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
    network_design['ToNode'] = network_design['toNode'].apply(
        lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
    network_design.drop(columns=['fromNode', 'toNode', 'network'], inplace=True)
    network_design = network_design.reset_index()
    numeric_cols = [c for c in network_design.columns if c not in ['Arc_ID', 'Network', 'FromNode', 'ToNode']]
    network_design[numeric_cols] = network_design[numeric_cols].apply(pd.to_numeric, errors='coerce')
    arc_ids = network_design[['Arc_ID', 'FromNode', 'ToNode']]

    with h5py.File(path_h5, 'r') as hdf_file:
        network_operation = extract_datasets_from_h5_group(hdf_file["operation/networks"])

    network_operation = network_operation['period1']
    network_operation.columns.names = ['Network', 'Arc_ID', 'Variable']

    network_operation = network_operation.T.reset_index()
    network_operation = pd.merge(network_operation, arc_ids.drop_duplicates(subset=['Arc_ID']), how='inner', left_on='Arc_ID', right_on='Arc_ID')
    network_operation = network_operation.set_index(['Network', 'Arc_ID', 'Variable', 'FromNode', 'ToNode']).T

    network_operation = add_time_steps_to_df(network_operation)

    return network_design, network_operation
