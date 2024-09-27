import streamlit as st
import pandas as pd
import sqlite3
from sqlite3 import Connection
import plotly.graph_objects as go
import numpy as np # -----> for dummy variance decay


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


#### Input selection

# Function to get unique values from a column
def get_unique_values(column: str) -> list:
    query = f"SELECT DISTINCT {column} FROM simulations_data"
    return [row[0] for row in conn.execute(query).fetchall()]

st.title("Explore simulated data from [paper title]")

st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit, \
         sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. \
         Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi \
         ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit \
          in voluptate velit esse cillum dolore eu fugiat nulla pariatur. \
          Excepteur sint occaecat cupidatat non proident, sunt in culpa \
          qui officia deserunt mollit anim id est laborum.")

st.subheader("Filter the pool of simulations" ,divider=True)

# Dropdown for Generative Process
generative_process_colname = 'generator'
generative_process = get_unique_values(generative_process_colname)
selected_process = st.selectbox('Generative process:', generative_process)

# Dropdown for Noise Distribution
noise_distribution_colname = 'equal_noise'
noise_distribution = get_unique_values(noise_distribution_colname)
selected_distribution = st.selectbox('Noise distribution:', noise_distribution)

# Dropdown for Final Normalization Method
normalization_method_colname = 'soft_norm'
normalization_method = get_unique_values(normalization_method_colname)
selected_normalization = st.selectbox('Noise distribution:', normalization_method)

# Slider for selecting a range of synthetic neurons
synth_neurons_colname = 'fake_units'
synth_neurons = get_unique_values(synth_neurons_colname)
selected_units = st.slider('Number of synthetic neurons:', 
                           min_value=min(synth_neurons), 
                           max_value=max(synth_neurons), 
                           value=(min(synth_neurons), max(synth_neurons)))

# Slider for selecting a range of timeseries length
ts_length_colname = 'length'
ts_length = get_unique_values(ts_length_colname)
selected_length = st.slider('Timeseries length:', 
                            min_value=min(ts_length), 
                            max_value=max(ts_length), 
                            value=(min(ts_length), max(ts_length)))

# Slider for selecting a range of latent variance decay
# variance_decay_colname = ''
# variance_decay = get_unique_values(variance_decay_colname)
dummy_decay_data = np.linspace(0,1.5,16)
variance_decay = dummy_decay_data
selected_decay = st.slider('Latent variance decay (\u03C4):', 
                            min_value=min(variance_decay), 
                            max_value=max(variance_decay), 
                            value=(min(variance_decay), max(variance_decay)))


#### Data filtering

# Query data based on selection
query = f"""
SELECT * FROM simulations_data 
WHERE {generative_process_colname} = ?
AND {noise_distribution_colname} = ? 
AND {normalization_method_colname} = ? 
AND {synth_neurons_colname} BETWEEN ? AND ? 
AND {ts_length_colname} BETWEEN ? AND ?
"""
# AND {variance_decay_colname} BETWEEN ? AND ? -------------> add once final data available
# """

# Execute the query with the parameters
selected_units_min, selected_units_max = selected_units
selected_length_min, selected_length_max = selected_length
query_params = (selected_process, selected_distribution, selected_normalization, 
          selected_units_min, selected_units_max, 
          selected_length_min, selected_length_max 
          # selected_decay[0], selected_decay[1] -------------> add once final data available
          )

# Filter the dataframe and display
filtered_data = pd.read_sql(query, conn, params=query_params)
st.write(filtered_data)


#### Elaborate filtered data

if not filtered_data.empty:

    ## Report mean and std

    st.subheader('Identified dimensions and noise error', divider=True)

    # Selected parameters
    st.subheader("Simulation Parameters")
    st.table({
        "Parameter": ["Number of synthetic neurons", "Length of the simulation", "Value of latent variance decay"],
        "Value": [selected_units, selected_length, selected_decay]
    })

    # Number of dimensions and noise error
    number_dimensions_colname = 'num_dim'
    noise_error_colname = 'noise.1'

    st.subheader("Statistics")
    st.table({
        "Metric": ["Identifiable dimensions mean", "Identifiable dimensions st.dev", "Noise error mean", "Noise error st.dev"],
        "Value": [
            f"{filtered_data[number_dimensions_colname].mean():.2f}",
            f"{filtered_data[number_dimensions_colname].std():.2f}",
            f"{filtered_data[noise_error_colname].mean():.2f}",
            f"{filtered_data[noise_error_colname].std():.2f}"
        ]
    })


    # variance_decay_colname = '' -------------> add once final data available
    # st.write(
    #     f'Identifiable dimensions: \
    #         mean {filtered_data[variance_decay_colname].mean()}, \
    #         st.dev {filtered_data[variance_decay_colname].std}'
    # )


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
