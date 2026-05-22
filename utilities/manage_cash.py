import streamlit as st
from pathlib import Path
import pandas as pd

from .read_data import read_results_from_h5

def show_sidebar():
    """
    Shows cash status and button in sidebar
    """
    show_cash_status()
    if st.session_state['Result']:
        clear_cash()

def show_cash_status():
    """
    Displays the cash status
    :return:
    """
    if st.session_state['Result']:
        st.sidebar.success("Results successfully loaded")
    else:
        st.sidebar.error("Results not loaded")

def clear_cash():
    """
    Clears cash
    :return:
    """
    if st.sidebar.button('Reset data'):
        st.session_state['Result'] = {}

def load_data_in_cash():
    """
    Loads results into cash
    :return:
    """
    st.markdown("**Load result file from Zenodo repository**")
    st.write("[Link to Zenodo repository](https://zenodo.org/records/14336316)")
    uploaded_h5 = st.file_uploader("")
    if uploaded_h5 is not None:
        st.session_state['Result'] = read_results_from_h5(uploaded_h5)
        st.session_state['ScenariosName'] = uploaded_h5.name.replace("_", " ").replace(
            ".h5",
                                                                              "")


def load_cash():
    if 'Result' not in st.session_state:
        st.session_state['Result'] = {}
    if 'NodeLocations' not in st.session_state:
        st.session_state['NodeLocations'] = pd.read_csv("./data/Node_Locations.csv",
                                                        sep=";", index_col=0, quoting=3)
    if 'Summary2030' not in st.session_state:
        st.session_state['Summary2030'] = pd.read_csv("./data/Summary_2030.csv", header=[0, 1, 2], index_col=0)
    if 'Summary2040' not in st.session_state:
        st.session_state['Summary2040'] = pd.read_csv("./data/Summary_2040.csv", header=[0, 1, 2], index_col=0)
    if 'HeaderKeys' not in st.session_state:
        st.session_state['HeaderKeys'] = pd.read_csv("./data/HeaderKeys.csv",
                                                     sep=";")

