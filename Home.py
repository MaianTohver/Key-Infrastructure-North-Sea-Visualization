import streamlit as st

from utilities import *
# from pathlib import Path
# import h5py
# import pandas as pd
# from utilities import *
# from networks import plot_nodes
# import folium
# from streamlit_folium import st_folium
# from branca.colormap import linear
# from folium.plugins import PolyLineTextPath, PolyLineOffset
# import sys

# Session States
load_cash()

# Page Setup
st.set_page_config(
    page_title="Home",
)

# Show cash status
# show_sidebar()

st.subheader("Welcome to the visualization platform of the paper ""Unlocking the green "
             "power of the North Sea: Identifying key energy infrastructure synergies "
             "for 2030 and 2040""! 👋")
st.write("The paper explores the role of electricity grids, energy storage and "
         "hydrogen infrastructure in the North Sea region towards 2030 and 2040. This "
         "website visualizes interactively the results of the optimizations as well "
         "as a more detailed scenario comparison.")

st.write("On the page 'Compare Scenarios' you can compare the results for the 2030 "
         "and 2040 scenarios for selected variables. On the page 'Download Data', "
         "you can download the aggregated results for the two years. In 'Visualize "
         "Single Results', you can upload an h5 file available on [Zenodo](https://zenodo.org/records/14336316) "
         "to visualize the design and operation of a single scenario.")

