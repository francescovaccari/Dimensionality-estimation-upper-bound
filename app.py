import streamlit as st
import pandas as pd
import sqlite3
from sqlite3 import Connection
import plotly.graph_objects as go
from datetime import datetime

# Function to load data into SQLite database
@st.cache_resource
def load_data_to_sqlite(csv_file: str) -> Connection:
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    df = pd.read_excel(csv_file)
    df.to_sql('simulations_data', conn, if_exists='replace', index=False)
    return conn

# Load data into SQLite
dataset = 'data/simulations.xlsx'
conn = load_data_to_sqlite(dataset)

# Function to get unique values from a column
def get_unique_values(column: str) -> list:
    query = f"SELECT DISTINCT {column} FROM simulations_data"
    return [row[0] for row in conn.execute(query).fetchall()]

st.title("Data Filter and Visualization")

# Dropdown for fake_units
fake_units = get_unique_values('fake_units')
selected_units = st.selectbox('Select a number of units:', fake_units)

# Dropdown for length
length = get_unique_values('length')
selected_length = st.selectbox('Choose the simulation length:', length)

# Dropdown for num_latent
num_latent = get_unique_values('num_latent')
selected_latent = st.selectbox('Select a number of latent dimensions:', num_latent)

# Custom range
# available_vals = get_unique_values('dt')
# start = st.selectbox('Select start:', available_vals)
# end = st.selectbox('Select end:', available_vals, index=len(available_vals)-1)

# Query data based on selection
query = """
SELECT * FROM simulations_data 
WHERE fake_units = ? AND length = ? AND num_latent = ?
"""
# In case of ranges add: AND [column name] BETWEEN ? AND ?

filtered_data = pd.read_sql(query, conn, params=(selected_units, selected_length, selected_latent))

# Display filtered data
st.write(filtered_data)

# Custom plotting
if not filtered_data.empty:
    st.subheader(f"Number of units: {selected_units}, \
                 simulation length: {selected_length}, \
                number of latent dimensions: {selected_latent}")
    
    # Select columns for plotting
    numeric_columns = filtered_data.select_dtypes(include=['float64', 'int64']).columns
    selected_columns = st.multiselect("Select columns to plot", numeric_columns)
    
    if selected_columns:
        fig = go.Figure()
        
        for column in selected_columns:
            # Calculate mean and standard deviation
            mean = filtered_data[column].mean()
            std = filtered_data[column].std()
            
            # Create x-axis values (simple index)
            x_values = list(range(len(filtered_data)))

            # Add trace for actual values
            fig.add_trace(go.Scatter(
                x=x_values,
                y=filtered_data[column],
                mode='lines',
                name=f'{column} Values',
                line=dict(dash='solid')
            ))
            
            # Add trace for mean
            fig.add_trace(go.Scatter(
                x=x_values,
                y=[mean] * len(filtered_data),
                mode='lines',
                name=f'{column} Mean',
                line=dict(dash='solid')
            ))
            
            # Add traces for standard deviation
            fig.add_trace(go.Scatter(
                x=x_values,
                y=[mean + std] * len(filtered_data),
                mode='lines',
                name=f'{column} +1 STD',
                line=dict(dash='dot')
            ))
            fig.add_trace(go.Scatter(
                x=x_values,
                y=[mean - std] * len(filtered_data),
                mode='lines',
                name=f'{column} -1 STD',
                line=dict(dash='dot')
            ))

        fig.update_layout(
            title=f'Mean and Standard Deviation of {', '.join(selected_columns)}',
            xaxis_title='Index',
            yaxis_title='Value',
            legend_title='Metrics'
        )
        
        st.plotly_chart(fig)
    else:
        st.warning("Please select at least one column to plot.")
else:
    st.warning("No data available for the selected filters.")
