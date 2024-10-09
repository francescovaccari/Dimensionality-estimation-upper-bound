from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sqlite3 import connect, Connection
from typing import Dict, List, Tuple
import json5
import requests
from io import BytesIO
import os

def load_config(config_path: str) -> dict:
    """
    Load and parse a JSON5 configuration file.
    
    :param config_path: Path to the configuration file
    :return: Dictionary containing the parsed configuration
    """
    with open(config_path, 'r') as f:
        return json5.load(f)

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

@st.cache_resource
def get_file_extension(url):
    return os.path.splitext(url)[1].lower()

@st.cache_resource
def load_data_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = BytesIO(response.content)
        
        file_extension = get_file_extension(url)
        
        if file_extension == '.csv':
            return pd.read_csv(content)
        elif file_extension == '.tsv':
            return pd.read_csv(content, sep='\t')
        elif file_extension in ['.xlsx', '.xls']:
            return pd.read_excel(content)
        else:
            st.error(f"Unsupported file format: {file_extension}")
            return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def get_unique_values(conn: Connection, column: str) -> List:
    """
    Get unique values from a column in the database.
    
    :param conn: SQLite database connection
    :param column: Name of the column
    :return: List of unique values
    """
    query = f"SELECT DISTINCT {column} FROM data"
    return [row[0] for row in conn.execute(query).fetchall()]


def create_filter_widgets(conn: Connection, filter_config: Dict) -> Dict:
    """
    Dynamically create filter widgets based on the filter configuration.
    
    :param conn: SQLite database connection
    :param filter_config: Dictionary of filter configurations
    :return: Dictionary of selected filter values
    """
    selected_values = {}
    for filter_type, filters in filter_config.items():
        for filter_details in filters:
            filter_name = filter_details['name']
            filter_label = filter_details['label']
            options = sorted(get_unique_values(conn, filter_name))
            
            if filter_type == 'single_valued':
                selected_values[filter_name] = st.selectbox(filter_label, options, format_func=lambda x: f"{x:.2f}" if isinstance(x, float) else x)
            elif filter_type == 'range_discrete':
                col1, col2 = st.columns(2)
                with col1:
                    selected_values[f"{filter_name}_min"] = st.selectbox(f"Min {filter_label}", options, format_func=lambda x: f"{x:.2f}" if isinstance(x, float) else x)
                with col2:
                    selected_values[f"{filter_name}_max"] = st.selectbox(f"Max {filter_label}", options, format_func=lambda x: f"{x:.2f}" if isinstance(x, float) else x)
            elif filter_type == 'range_continuous':
                selected_values[f"{filter_name}_min"], selected_values[f"{filter_name}_max"] = st.select_slider(
                    filter_label, options=options, value=(options[0], options[-1]), format_func=lambda x: f"{x:.2f}",
                    )
    
    return selected_values

def build_query(filters: Dict, selected_filters: Dict) -> Tuple[str, List]:
    """
    Dynamically build SQL query based on selected filters.
    
    :param filters: Dictionary of filter configurations
    :param selected_filters: Dictionary of selected filter values
    :return: Tuple of (query string, list of parameter values)
    """
    conditions = []
    params = []
    
    for filter_type, filter_list in filters.items():
        for filter_details in filter_list:
            column = filter_details['name']
            if filter_type == 'single_valued':
                if column in selected_filters:
                    conditions.append(f"{column} = ?")
                    params.append(selected_filters[column])
            elif filter_type in ['range_discrete', 'range_continuous']:
                min_value = selected_filters.get(f"{column}_min")
                max_value = selected_filters.get(f"{column}_max")
                if min_value is not None and max_value is not None:
                    if min_value == max_value:
                        conditions.append(f"{column} = ?")
                        params.append(min_value)
                    else:
                        conditions.append(f"{column} BETWEEN ? AND ?")
                        params.extend([min_value, max_value])
    
    query = f"SELECT * FROM data WHERE {' AND '.join(conditions)}"
    return query, params

def display_filters_summary(filter_config: Dict, selected_filters: Dict) -> None:
    """
    Display results statistics based on the configuration.
    
    :param filter_config: Dictionary of filters configurations
    :param selected_filters: Dictionary of user-selected values for filters
    """
    st.subheader("Filtering Parameters")
    
    parameters = []
    values = []
    for filter_type, filter_list in filter_config.items():
        for filter_details in filter_list:
            if filter_type == 'single_valued':
                parameters.extend([
                    f"{filter_details['label']}",
                ])
                value = selected_filters[filter_details['name']]
                if isinstance(value, float):
                    value = f"{selected_filters[filter_details['name']]:.2f}"
                values.extend({
                    value
                })
            elif filter_type in ['range_discrete', 'range_continuous']:
                parameters.extend([
                    f"{filter_details['label']} min",
                    f"{filter_details['label']} max",
                ])
                values.extend([
                    f"{selected_filters[filter_details['name'] + "_min"]:.2f}",
                    f"{selected_filters[filter_details['name'] + "_max"]:.2f}"
                ])

    st.table(pd.DataFrame.from_dict({
        "Parameters" : parameters,
        "Values" : values
    }))

def display_results(data: pd.DataFrame, results_config: Dict, condition_prefix: str) -> None:
    """
    Display results statistics based on the configuration.
    
    :param data: Filtered DataFrame
    :param config: Dictionary of result configurations
    """
    st.subheader("Statistics")
    
    results = []
    values = []
    for col in results_config['columns']:
        col_name = condition_prefix + col['name']
        results.extend([
            f"{col['label']}",
        ])
        values.extend({
            f"{data[col_name].mean():.2f} +/- {data[col_name].std():.2f}",
        })
    
    st.table({"Metric": results, 
               "Mean +/- std": values})

def create_subplots(data: pd.DataFrame, plot_config: Dict, prefix: str) -> go.Figure:
    """
    Create subplots based on the plot configuration.
    
    :param data: Filtered DataFrame
    :param plot_config: Dictionary of plot configurations
    :param prefix: str of the condition/method prefix
    :return: Plotly Figure object
    """
    fig = make_subplots(rows=len(plot_config['y_axes']), cols=1, 
                        subplot_titles=[y['label'] for y in plot_config['y_axes']])
    
    for i, y_variable in enumerate(plot_config['y_axes'], start=1):
        scatter = go.Scatter(
            x=data[plot_config['x_axis']['name']],
            y=data[prefix+y_variable['name']],
            mode='markers',
            name=y_variable['label'],
            showlegend=False,
            marker=dict(
                color=data[plot_config['color_variable']['name']],
                colorscale='Bluered',
                showscale=True if i == len(plot_config['y_axes']) else False,
                colorbar=dict(
                    title=plot_config['color_variable']['label'],
                    len=0.5,
                    thickness=15,
                    x=1.02,
                    y=0.5,
                    yanchor='middle'
                ) if i == len(plot_config['y_axes']) else None,
            )
        )
        
        fig.add_trace(scatter, row=i, col=1)
        
        fig.update_xaxes(title_text=plot_config['x_axis']['label'], row=i, col=1)
        fig.update_yaxes(title_text=y_variable['label'], row=i, col=1)
    
    fig.update_layout(height=300 * len(plot_config['y_axes']), width=1500)
    return fig
