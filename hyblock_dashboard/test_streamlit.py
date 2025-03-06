#!/usr/bin/env python3
"""
Simple test script for Streamlit
"""

import streamlit as st
import pandas as pd
import numpy as np

# Basic page config
st.set_page_config(page_title="Streamlit Test", page_icon="🧪")

# Title
st.title("Streamlit Test")
st.markdown("Testing Streamlit caching and basic functionality")

# Simple cached function without persist
@st.cache_data(ttl=60)
def get_data():
    """Get some test data"""
    return pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.randn(100)
    })

# Display data
st.subheader("Random Data")
data = get_data()
st.dataframe(data)

st.success("If you see this, Streamlit is working correctly!") 