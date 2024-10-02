import streamlit as st
import pandas as pd
import sqlite3
from sqlite3 import Connection
import plotly.graph_objects as go

#### Set Up

# Specify csv column names for filtering data
generative_process_colname = 'Generative_process'
noise_distribution_colname = 'Noise_distribution'
normalization_method_colname = 'Final_normalization'
ts_length_colname = 'Time_Series_Length'
synth_neurons_colname = 'Syntethic_Neurons'
variance_decay_colname = 'Tau'

# Specify csv column names to exhibit as results (mean and std)
first_result_colname = 'Identifiable_dimensions'
second_result_colname = 'Noise'

# Page layout
st.set_page_config(
    page_title="Check Our Data",
    page_icon=":brain:",  # :eyeglasses:
    layout="wide",
    )

# Title and small description
st.title("Explore simulated data from [paper title]")

st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit, \
         sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. \
         Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi \
         ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit \
          in voluptate velit esse cillum dolore eu fugiat nulla pariatur. \
          Excepteur sint occaecat cupidatat non proident, sunt in culpa \
          qui officia deserunt mollit anim id est laborum.")


#### Data Loading

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


#### Input selection for data filtering

st.subheader("Filter the data" ,divider=True)

# Function to get unique values from a column
def get_unique_values(column: str) -> list:
    query = f"SELECT DISTINCT {column} FROM simulations_data"
    return [row[0] for row in conn.execute(query).fetchall()]

## Dropdowns

# Generative Process
generative_process = get_unique_values(generative_process_colname)
selected_process = st.selectbox('Generative process:', generative_process)

# Noise Distribution
noise_distribution = get_unique_values(noise_distribution_colname)
selected_distribution = st.selectbox('Noise distribution:', noise_distribution)

# Final Normalization Method
normalization_method = get_unique_values(normalization_method_colname)
selected_normalization = st.selectbox('Normalization method:', normalization_method)

## Sliders 

# Synthetic neurons
synth_neurons = get_unique_values(synth_neurons_colname)
selected_units_min, selected_units_max = st.select_slider('Number of synthetic neurons:', 
                           options = synth_neurons, 
                           value=(synth_neurons[0], synth_neurons[-1]))

# Timeseries length
ts_length = get_unique_values(ts_length_colname)
selected_length_min, selected_length_max = st.select_slider('Timeseries length:', 
                            options = ts_length, 
                            value=(ts_length[0], ts_length[-1]))

# Latent variance decay: Tau
variance_decay = get_unique_values(variance_decay_colname)
selected_decay_min, selected_decay_max = st.select_slider('Latent variance decay (\u03C4):', 
                            options = variance_decay, 
                            value=(variance_decay[0], variance_decay[-1]))


#### Data filtering

# Query data based on selection
query = f"""
SELECT * FROM simulations_data 
WHERE {generative_process_colname} = ?
AND {noise_distribution_colname} = ? 
AND {normalization_method_colname} = ? 
AND {synth_neurons_colname} BETWEEN ? AND ? 
AND {ts_length_colname} BETWEEN ? AND ?
AND {variance_decay_colname} BETWEEN ? AND ?
"""

# Execute the query with the parameters
query_params = (selected_process, selected_distribution, selected_normalization, 
          selected_units_min, selected_units_max, 
          selected_length_min, selected_length_max,
          selected_decay_min, selected_decay_max
          )

# Filter the dataframe and display
filtered_data = pd.read_sql(query, conn, params=query_params)
st.write(filtered_data)


#### Elaborate filtered data

if not filtered_data.empty:

    ### Report results' mean and std 

    st.subheader('Identified dimensions and noise error', divider=True)

    # Sum up selected parameters
    st.subheader("Simulation Parameters")
    st.table({
        "Parameter": ["Number of synthetic neurons", "Length of the simulation", "Value of latent variance decay"],
        "Value": [(selected_units_min, selected_units_max), (selected_length_min, selected_length_max), (selected_decay_min, selected_decay_max)]
    })

    # Report first and second results
    st.subheader("Statistics")
    st.table({
        "Metric": [f"{first_result_colname.replace('_',' ')} mean", f"{first_result_colname.replace('_',' ')} st.dev", 
                   f"{second_result_colname.replace('_',' ')} mean", f"{second_result_colname.replace('_',' ')} st.dev"],
        "Value": [
            f"{filtered_data[first_result_colname].mean():.2f}",
            f"{filtered_data[first_result_colname].std():.2f}",
            f"{filtered_data[second_result_colname].mean():.2f}",
            f"{filtered_data[second_result_colname].std():.2f}"
        ]
    })

    ## Plot desired variables
    
    st.subheader('Plot', divider=True)

    # Select columns for plotting
    numeric_columns = filtered_data.select_dtypes(include=['float64', 'int64']).columns

    # Select x and y variables
    x_variable = st.selectbox("Select x variable", numeric_columns)
    y_variable = st.selectbox("Select y variable", numeric_columns)

    if x_variable and y_variable:
        fig = go.Figure()

        # Calculate mean and standard deviation for y variable
        mean = filtered_data[y_variable].mean()
        std = filtered_data[y_variable].std()

        # Add trace for actual values
        fig.add_trace(go.Scatter(
            x=filtered_data[x_variable],
            y=filtered_data[y_variable],
            mode='markers',
            name=f'{y_variable} Values',
            line=dict(dash='solid')
        ))

        # # Add trace for mean
        # fig.add_trace(go.Scatter(
        #     x=filtered_data[x_variable],
        #     y=[mean] * len(filtered_data),
        #     mode='lines',
        #     name=f'{y_variable} Mean',
        #     line=dict(dash='solid')
        # ))

        # # Add traces for standard deviation
        # fig.add_trace(go.Scatter(
        #     x=filtered_data[x_variable],
        #     y=[mean + std] * len(filtered_data),
        #     mode='lines',
        #     name=f'{y_variable} +1 STD',
        #     line=dict(dash='dot')
        # ))
        # fig.add_trace(go.Scatter(
        #     x=filtered_data[x_variable],
        #     y=[mean - std] * len(filtered_data),
        #     mode='lines',
        #     name=f'{y_variable} -1 STD',
        #     line=dict(dash='dot')
        # ))

        fig.update_layout(
            title=f'{y_variable} vs {x_variable}',
            xaxis_title=x_variable,
            yaxis_title=y_variable,
            legend_title='Metrics'
        )

        st.plotly_chart(fig)
    else:
        st.warning("Please select both x and y variables to plot.")
else:
    st.warning("No data available for the selected filters.")
