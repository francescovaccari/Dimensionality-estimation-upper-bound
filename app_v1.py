import pandas as pd
import streamlit as st
from _utils.helpers import load_config, load_data_from_url, load_data_to_sqlite, build_query, create_subplots, create_filter_widgets, display_filters_summary, display_results

# Load configuration
config = load_config('config.json5')

# Set up page
st.set_page_config(**config['page_config'])
st.title(config['title'])
st.write(config['description'])
    
# Section title
st.subheader("Filter the data" ,divider=True)

# Load data, either from url or from a path
if config['data_source']['url']:
    conn = load_data_from_url(config['data_source']['url'])
    st.write("Data from configured URL:")
    st.write(conn)
else:
    conn = load_data_to_sqlite(config['data_source']['path'])

# Create filter widgets
selected_filters = create_filter_widgets(conn, config['filters'])

# Build query and fetch data
query, params = build_query(config['filters'], selected_filters)
filtered_data = pd.read_sql(query, conn, params=params)

# Show filtered data
st.write(filtered_data)

# Display results
if not filtered_data.empty:

    # Section title
    st.subheader("Results" ,divider=True)

    # Filters summary
    display_filters_summary(config['filters'], selected_filters)

    # Select condition/method prefix, if any
    if config['results']['prefix_options']:
        selected_prefix = st.selectbox('Select a method:', config['results']['prefix_options']) + '_'
    else:
        selected_prefix = ''

    display_results(filtered_data, config['results'], selected_prefix)

    # Section title
    st.subheader("Plot" ,divider=True)
    
    # Create and display plots
    fig = create_subplots(filtered_data, config['plots'], selected_prefix)
    st.plotly_chart(fig)
else:
    st.warning("No data available for the selected filters.")