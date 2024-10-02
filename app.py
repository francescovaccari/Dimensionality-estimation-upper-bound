import streamlit as st
import pandas as pd
import sqlite3
from sqlite3 import Connection
import plotly.graph_objects as go
from plotly.subplots import make_subplots

#### Set Up

# Specify csv column names representing parameters to filter data --------------> substitute with (first,second, etc)_data_filter_colname
generative_process_colname = 'Generative_process'
noise_distribution_colname = 'Noise_distribution'
normalization_method_colname = 'Final_normalization'
ts_length_colname = 'Time_Series_Length'
synth_neurons_colname = 'Syntethic_Neurons'
variance_decay_colname = 'Tau'

# Specify condition/method-specific prefixes (if any) 
# for csv column names representing variables to exhibit as results
conditions_prefix_colname = ['PA', 'CV', 'K1', 'PR', '80%', '90%']

# Specify csv column names representing variables to exhibit as results (mean and std)
first_result_colname = 'Identifiable_Dimensions'
second_result_colname = 'Real_data_in_denoised_matrix'
third_result_colname = 'Estimated_noise_err'

# Specify csv column names to plot
y_variable_plot_colnames = [first_result_colname, second_result_colname, third_result_colname]
x_variable_plot_colname = variance_decay_colname
colorcode_variable_plot_colname = 'Noise'

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
    df.to_sql('data', conn, if_exists='replace', index=False)
    return conn

# Load data into SQLite
dataset = 'data/Final_table.xlsx'
conn = load_data_to_sqlite(dataset)


#### Input selection for data filtering

st.subheader("Filter the data" ,divider=True)

# Function to get unique values from a column
def get_unique_values(column: str) -> list:
    query = f"SELECT DISTINCT {column} FROM data"
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
SELECT * FROM data 
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

    # Choose methods ---------------------------------> find more general term
    selected_condition = st.selectbox('Choose a method/condition:', conditions_prefix_colname)

    ### Report results' mean and std 
    st.subheader(f'{first_result_colname.replace('_',' ')}, {second_result_colname.replace('_',' ')} and {third_result_colname.replace('_',' ')}', divider=True)

    # Sum up selected parameters
    st.subheader("Simulation Parameters")
    st.table({
        "Parameter": [f"{generative_process_colname.replace('_',' ')}",
                    f"{noise_distribution_colname.replace('_',' ')}",
                    f"{normalization_method_colname.replace('_',' ')}",
                    f"{ts_length_colname.replace('_',' ')}",
                    f"{synth_neurons_colname.replace('_',' ')}",
                    f"{variance_decay_colname.replace('_',' ')}",
                    ],
        "Value": [(selected_process),
                  (selected_distribution),
                  (selected_normalization),
                  (selected_length_min, selected_length_max), 
                  (selected_units_min, selected_units_max), 
                  (selected_decay_min, selected_decay_max),
                  ]
    })

    # Report results
    st.subheader("Statistics")
    st.table({
        "Metric": [f"{first_result_colname.replace('_',' ')} mean", f"{first_result_colname.replace('_',' ')} st.dev", 
                   f"{second_result_colname.replace('_',' ')} mean", f"{second_result_colname.replace('_',' ')} st.dev",
                   f"{third_result_colname.replace('_',' ')} mean", f"{third_result_colname.replace('_',' ')} st.dev"],
        "Value": [
            f"{filtered_data[selected_condition+'_'+first_result_colname].mean():.2f}",
            f"{filtered_data[selected_condition+'_'+first_result_colname].std():.2f}",
            f"{filtered_data[selected_condition+'_'+second_result_colname].mean():.2f}",
            f"{filtered_data[selected_condition+'_'+second_result_colname].std():.2f}",
            f"{filtered_data[selected_condition+'_'+third_result_colname].mean():.2f}",
            f"{filtered_data[selected_condition+'_'+third_result_colname].std():.2f}"
        ]
    })

    ### Plot results
    st.subheader('Plot', divider=True)

    # Create subplots
    fig = make_subplots(rows=3, cols=1, subplot_titles=y_variable_plot_colnames)

    for i, y_variable in enumerate(y_variable_plot_colnames, start=1):

        scatter = go.Scatter(
            x=filtered_data[x_variable_plot_colname],
            y=filtered_data[selected_condition+'_'+y_variable],
            mode='markers',
            name=y_variable,
            marker=dict(
                color=filtered_data[colorcode_variable_plot_colname],
                colorscale='Viridis',
                showscale=True if i == 3 else False,  # Show colorbar only for the last plot
                colorbar=dict(
                    title=colorcode_variable_plot_colname,
                    len=0.5,  # Length of the colorbar (0-1)
                    thickness=15,  # Width of the colorbar in pixels
                    x=1.02,  # Position
                    y=0.5,  # Position
                    yanchor='middle'
                ) if i == 3 else None
            )
        )
        
        fig.add_trace(scatter, row=i, col=1)
        
        fig.update_xaxes(title_text=x_variable_plot_colname, row=i, col=1)
        fig.update_yaxes(title_text=y_variable, row=i, col=1)

    fig.update_layout(height=900, width=1200)

    st.plotly_chart(fig)

else:
    st.warning("No data available for the selected filters.")
