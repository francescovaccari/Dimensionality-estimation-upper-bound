from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sqlite3 import connect, Connection
from typing import Dict, List, Tuple
import json5

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
        for filter_name, filter_details in filters.items():
            if filter_type == 'single_valued':
                options = get_unique_values(conn, filter_name)
                selected_values[filter_name] = st.selectbox(filter_details['label'], options)
            elif filter_type in ['range_discrete', 'range_continuous']:
                options = sorted(get_unique_values(conn, filter_name))
                if filter_type == 'range_discrete':
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_values[f"{filter_name}_min"] = st.selectbox(f"Min {filter_details['label']}", options)
                    with col2:
                        selected_values[f"{filter_name}_max"] = st.selectbox(f"Max {filter_details['label']}", options)
                else:
                    selected_values[f"{filter_name}_min"], selected_values[f"{filter_name}_max"] = st.select_slider(
                        filter_details['label'], options=options, value=(options[0], options[-1])
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
    
    for filter_type, filter_dict in filters.items():
        for column in filter_dict:
            if filter_type == 'single_valued':
                conditions.append(f"{column} = ?")
                params.append(selected_filters[column])
            elif filter_type in ['range_discrete', 'range_continuous']:
                conditions.append(f"{column} BETWEEN ? AND ?")
                params.extend([selected_filters[f"{column}_min"], selected_filters[f"{column}_max"]])
    
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
    for filter_type, filters in filter_config.items():
        for filter_name, _ in filters.items():
            if filter_type == 'single_valued':
                parameters.extend([
                    f"{filter_name}",
                ])
                values.extend({
                    f"{selected_filters[filter_name]}",
                })
            elif filter_type in ['range_discrete', 'range_continuous']:
                parameters.extend([
                    f"{filter_name}_min",
                    f"{filter_name}_max",
                ])
                values.extend({
                    selected_filters[f"{filter_name}_min"],
                    selected_filters[f"{filter_name}_max"],
                })

    st.table({"Parameter": parameters, 
               "Value": values})

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
                        subplot_titles=[y.replace('_', ' ') for y in plot_config['y_axes']])
    
    for i, y_variable in enumerate(plot_config['y_axes'], start=1):
        scatter = go.Scatter(
            x=data[plot_config['x_axis']],
            y=data[prefix+y_variable],
            mode='markers',
            name=y_variable,
            marker=dict(
                color=data[plot_config['color_variable']],
                colorscale='Bluered',
                showscale=True if i == len(plot_config['y_axes']) else False,
                colorbar=dict(
                    title=plot_config['color_variable'],
                    len=0.5,
                    thickness=15,
                    x=1.02,
                    y=0.5,
                    yanchor='middle'
                ) if i == len(plot_config['y_axes']) else None
            )
        )
        
        fig.add_trace(scatter, row=i, col=1)
        
        fig.update_xaxes(title_text=plot_config['x_axis'].replace('_', ' '), row=i, col=1)
        fig.update_yaxes(title_text=y_variable.replace('_', ' '), row=i, col=1)
    
    fig.update_layout(height=300 * len(plot_config['y_axes']), width=1500)
    return fig