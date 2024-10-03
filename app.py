import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlite3 import connect, Connection
import streamlit as st

#### Set Up -------------------------------------------------------------------------------------------------------------------------------------------------------------

# Data filtering parameters: 
# Specify csv column names representing parameters to filter data (1, 2, 3, etc. is the order of appearance on the webapp)

# Single-valued filters (low/high number of values)
singlevalued_filter1_colname = 'Generative_process'
singlevalued_filter2_colname = 'Noise_distribution'
singlevalued_filter3_colname = 'Final_normalization'

# Ranges (low number of values)
range_discrete_filter1_colname = 'Time_Series_Length'
range_discrete_filter2_colname = 'Syntethic_Neurons'

# Ranges (high number of values)
range_continuous_filter1_colname = 'Tau'

# Condition/method-specific prefixes: 
# If any, specify for prefixes csv column names representing variables to exhibit as results
conditions_prefix_list = ['PA', 'CV', 'K1', 'PR', '80%', '90%']

# Results variables:
# Specify csv column names representing variables to exhibit as results (mean and std)
result1_colname = 'Identifiable_Dimensions'
result2_colname = 'Real_data_in_denoised_matrix'
result3_colname = 'Estimated_noise_err'

# Scatterplots variables:
# Specify csv column names to plot
y_variable_plot_colnames = [result1_colname, result2_colname, result3_colname]
x_variable_plot_colname = range_continuous_filter1_colname
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


#### Data Loading -------------------------------------------------------------------------------------------------------------------------------------------------------------

# Function to load data into SQLite database
@st.cache_resource
def load_data_to_sqlite(file_path: str) -> Connection:
    conn = connect(':memory:', check_same_thread=False)
    file_extension = Path(file_path).suffix.lower()
    
    if file_extension == '.xlsx':
        df = pd.read_excel(file_path)
    elif file_extension in ('.csv', '.tsv'):
        separator = '\t' if file_extension == '.tsv' else ','
        df = pd.read_csv(file_path, sep=separator)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")
    
    df.to_sql('data', conn, if_exists='replace', index=False)
    return conn

# Load data into SQLite
dataset = 'data/Final_table.xlsx'
conn = load_data_to_sqlite(dataset)


#### Input selection for data filtering

# Section title
st.subheader("Filter the data" ,divider=True)

# Function to get unique values from a column
def get_unique_values(column: str) -> list:
    query = f"SELECT DISTINCT {column} FROM data"
    return [row[0] for row in conn.execute(query).fetchall()]

## Vertical dropdowns: Single-valued filters (low/high number of values)

# Filter 1
singlevalued_filter1 = get_unique_values(singlevalued_filter1_colname)
label = singlevalued_filter1_colname.replace('_', ' ')
selected_singlevalued_filter1 = st.selectbox(f'{label}:', singlevalued_filter1)

# Filter 2
singlevalued_filter2 = get_unique_values(singlevalued_filter2_colname)
label = singlevalued_filter2_colname.replace('_', ' ')
selected_singlevalued_filter2 = st.selectbox(f'{label}:', singlevalued_filter2)

# Filter 3
singlevalued_filter3 = get_unique_values(singlevalued_filter3_colname)
label = singlevalued_filter3_colname.replace('_', ' ')
selected_singlevalued_filter3 = st.selectbox(f'{label}:', singlevalued_filter3)

## Horizontal dropdowns: Ranges (low number of values)

# Filter 1
lowerbound_1, upperbound_1 = st.columns(2)
range_discrete_filter1 = sorted(get_unique_values(range_discrete_filter1_colname))
label = range_discrete_filter1_colname.replace('_', ' ')
with lowerbound_1:
    selected_range_discrete_filter1_min = st.selectbox(
        f'Min {label}:',
        range_discrete_filter1,
        key='min_filter1'
    )
with upperbound_1:
    selected_range_discrete_filter1_max = st.selectbox(
        f'Max {label}:',
        range_discrete_filter1,
        key='max_filter1'
    )
if selected_range_discrete_filter1_min > selected_range_discrete_filter1_max:
    st.error("Error: minimum value must be less than or equal to maximum value.")

# Filter 2
lowerbound_2, upperbound_2 = st.columns(2)
range_discrete_filter2 = sorted(get_unique_values(range_discrete_filter2_colname))
label = range_discrete_filter2_colname.replace('_', ' ')
with lowerbound_2:
    selected_range_discrete_filter2_min = st.selectbox(
        f'Min {label}:',
        range_discrete_filter2,
        key='min_filter2'
    )
with upperbound_2:
    selected_range_discrete_filter2_max = st.selectbox(
        f'Max {label}:',
        range_discrete_filter2,
        key='max_filter2'
    )
if selected_range_discrete_filter2_min > selected_range_discrete_filter2_max:
    st.error("Error: minimum value must be less than or equal to maximum value.")

## Sliders (ranges w/ high number of values)

# Filter 1
range_continuous_filter1 = sorted(get_unique_values(range_continuous_filter1_colname))
label = range_continuous_filter1_colname.replace('_', ' ')
selected_range_continuous_filter1_min, selected_range_continuous_filter1_max = st.select_slider(f'{label}:',
                            options = range_continuous_filter1, 
                            value=(range_continuous_filter1[0], range_continuous_filter1[-1]))


#### Data filtering -------------------------------------------------------------------------------------------------------------------------------------------------------------

# Query data based on selection
query = f"""
SELECT * FROM data 
WHERE {singlevalued_filter1_colname} = ?
AND {singlevalued_filter2_colname} = ? 
AND {singlevalued_filter3_colname} = ?
AND {range_discrete_filter1_colname} BETWEEN ? AND ? 
AND {range_discrete_filter2_colname} BETWEEN ? AND ?
AND {range_continuous_filter1_colname} BETWEEN ? AND ?
"""

# Execute the query with the parameters
query_params = (
    selected_singlevalued_filter1, 
    selected_singlevalued_filter2, 
    selected_singlevalued_filter3, 
    selected_range_discrete_filter1_min, 
    selected_range_discrete_filter1_max, 
    selected_range_discrete_filter2_min, 
    selected_range_discrete_filter2_max,
    selected_range_continuous_filter1_min, 
    selected_range_continuous_filter1_max
    )

# Filter the dataframe and display
filtered_data = pd.read_sql(query, conn, params=query_params)
st.write(filtered_data)


#### Elaborate filtered data -------------------------------------------------------------------------------------------------------------------------------------------------------------

if not filtered_data.empty:

    # Prompt user to choose results columns prefix, if any
    if len(conditions_prefix_list) > 0:
        selected_prefix = st.selectbox('Select a method:', conditions_prefix_list) + '_'
    else:
        selected_prefix = ''

    ### Report results' mean and std 
    st.subheader(f'{result1_colname.replace('_',' ')}, {result2_colname.replace('_',' ')} and {result3_colname.replace('_',' ')}', divider=True)

    # Sum up selected parameters
    st.subheader("Filtering Parameters")
    st.table({
        "Parameter": [
            f"{singlevalued_filter1_colname.replace('_',' ')}",
            f"{singlevalued_filter2_colname.replace('_',' ')}",
            f"{singlevalued_filter3_colname.replace('_',' ')}",
            f"{range_discrete_filter1_colname.replace('_',' ')}",
            f"{range_discrete_filter2_colname.replace('_',' ')}",
            f"{range_continuous_filter1_colname.replace('_',' ')}",
        ],
        "Value": [
            (selected_singlevalued_filter1),
            (selected_singlevalued_filter2),
            (selected_singlevalued_filter3),
            (selected_range_discrete_filter1_min, selected_range_discrete_filter1_max), 
            (selected_range_discrete_filter2_min, selected_range_discrete_filter2_max), 
            (selected_range_continuous_filter1_min, selected_range_continuous_filter1_max),
                  ]
    })

    # Report results
    st.subheader("Results statistics")
    st.table({
        "Metric": [f"{result1_colname.replace('_',' ')} mean", f"{result1_colname.replace('_',' ')} st.dev", 
                   f"{result2_colname.replace('_',' ')} mean", f"{result2_colname.replace('_',' ')} st.dev",
                   f"{result3_colname.replace('_',' ')} mean", f"{result3_colname.replace('_',' ')} st.dev"],
        "Value": [
            f"{filtered_data[selected_prefix+result1_colname].mean():.2f}",
            f"{filtered_data[selected_prefix+result1_colname].std():.2f}",
            f"{filtered_data[selected_prefix+result2_colname].mean():.2f}",
            f"{filtered_data[selected_prefix+result2_colname].std():.2f}",
            f"{filtered_data[selected_prefix+result3_colname].mean():.2f}",
            f"{filtered_data[selected_prefix+result3_colname].std():.2f}"
        ]
    })

    ### Plot results
    st.subheader('Plots', divider=True)

    # Create subplots
    fig = make_subplots(rows=3, cols=1, subplot_titles=[s.replace('_',' ') for s in y_variable_plot_colnames])

    for i, y_variable in enumerate(y_variable_plot_colnames, start=1):

        scatter = go.Scatter(
            x=filtered_data[x_variable_plot_colname],
            y=filtered_data[selected_prefix+y_variable],
            mode='markers',
            name=y_variable,
            marker=dict(
                color=filtered_data[colorcode_variable_plot_colname],
                colorscale='Bluered',
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
        
        x_label = x_variable_plot_colname.replace('_', ' ')
        y_label = y_variable.replace('_', ' ')
        fig.update_xaxes(title_text=x_label, row=i, col=1)
        fig.update_yaxes(title_text=y_label, row=i, col=1)

    fig.update_layout(height=900, width=1200)

    st.plotly_chart(fig)

else:
    st.warning("No data available for the selected filters.")
