from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sqlite3 import connect, Connection
from typing import Dict, List, Tuple, Set
import json5
import requests
from io import BytesIO
import os
import re

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
                min_key = filter_details['name'] + "_min"
                max_key = filter_details['name'] + "_max"
                values.extend([
                    f"{selected_filters[min_key]:.2f}",
                    f"{selected_filters[max_key]:.2f}"
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


# New functions for the updated workflow

def extract_metadata_from_data(df: pd.DataFrame) -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    Extract metadata (methods, metrics, and simulation parameters) from the data DataFrame.
    
    The DataFrame structure is: simulation_param_columns, then {method}_{metric} columns.
    Known simulation parameters come from the MATLAB script's headerSimulationParameters.
    
    :param df: Input DataFrame
    :return: Tuple of (headerSimulationParameters, headerMethods, headerMetrics, all_columns)
    """
    known_sim_params = [
        'fake_units', 'time_series_length', 'num_latent', 'noiseDistr', 'equalNoise',
        'soft_norm', 'gen', 'decayCap', 'decayFactor', 'noiseFactor', 'nonLinAlfa',
        'noise_var', 'nonLinear_var', 'tau'
    ]
    
    # Get simulation parameters that actually exist in the data
    header_sim_params = [col for col in known_sim_params if col in df.columns]
    
    # Extract methods and metrics from remaining columns
    methods_set = set()
    metrics_set = set()
    
    for col in df.columns:
        if col not in header_sim_params:
            # Pattern: {method}_{metric} or {method}_recon_accuracy
            parts = col.rsplit('_', 1)
            if len(parts) == 2:
                method_part, metric_part = parts
                # Handle special case: if metric_part is "recon_accuracy", the full metric is that
                if metric_part == 'accuracy':  # part of recon_accuracy
                    # Handle {method}_recon_accuracy
                    if method_part.endswith('_recon'):
                        actual_method = method_part.rsplit('_', 1)[0]
                        methods_set.add(actual_method)
                        metrics_set.add('recon_accuracy')
                    else:
                        methods_set.add(method_part)
                        metrics_set.add(metric_part)
                elif metric_part == 'accuracy_opt':  # part of recon_accuracy_opt
                    if method_part.endswith('_recon'):
                        actual_method = method_part.rsplit('_', 1)[0]
                        methods_set.add(actual_method)
                        metrics_set.add('recon_accuracy_opt')
                    else:
                        methods_set.add(method_part)
                        metrics_set.add(metric_part)
                else:
                    methods_set.add(method_part)
                    metrics_set.add(metric_part)
    
    # Better approach: use regex to parse {method}_{metric} pattern
    methods_set = set()
    metrics_set = set()
    
    known_metrics = {'k', 'dim_error', 'tot_expl_var', 'estimated_noise_var', 
                     'estimated_noise_err', 'recon_accuracy', 'dim_error_opt',
                     'estimated_noise_err_opt', 'recon_accuracy_opt'}
    
    for col in df.columns:
        if col not in header_sim_params:
            # Try to match {method}_{metric}
            match = re.match(r'^(.+)_(k|dim_error|tot_expl_var|estimated_noise_var|estimated_noise_err|recon_accuracy|dim_error_opt|estimated_noise_err_opt|recon_accuracy_opt)$', col)
            if match:
                method = match.group(1)
                metric = match.group(2)
                methods_set.add(method)
                metrics_set.add(metric)
    
    header_methods = sorted(list(methods_set))
    header_metrics = sorted(list(metrics_set))
    
    return header_sim_params, header_methods, header_metrics, df.columns.tolist()


def create_simulation_filter_widgets(df: pd.DataFrame, header_sim_params: List[str], 
                                     exclude_cols: List[str] = None) -> Dict:
    """
    Create interactive filter widgets for simulation parameters.
    
    :param df: Input DataFrame
    :param header_sim_params: List of simulation parameter column names
    :param exclude_cols: Columns to exclude from filtering
    :return: Dictionary of selected filter values
    """
    if exclude_cols is None:
        exclude_cols = []
    
    selected_filters = {}
    cols_per_row = 3
    
    filterable_params = [p for p in header_sim_params if p not in exclude_cols]
    
    st.subheader("Filter Simulations")
    
    # Create filter widgets in a grid
    for idx, param in enumerate(filterable_params):
        if idx % cols_per_row == 0:
            cols = st.columns(cols_per_row)
        
        col_idx = idx % cols_per_row
        
        with cols[col_idx]:
            unique_values = sorted(df[param].unique())
            param_type = df[param].dtype
            
            if len(unique_values) <= 10:
                # Use multiselect for few unique values
                selected_filters[param] = st.multiselect(
                    f"Select {param}",
                    unique_values,
                    default=unique_values
                )
            else:
                # Use slider for many unique values
                if param_type in ['float64', 'float32']:
                    min_val, max_val = float(df[param].min()), float(df[param].max())
                    selected_filters[f"{param}_range"] = st.slider(
                        f"Select {param} range",
                        min_val, max_val, (min_val, max_val)
                    )
                else:
                    min_val, max_val = int(df[param].min()), int(df[param].max())
                    selected_filters[f"{param}_range"] = st.slider(
                        f"Select {param} range",
                        min_val, max_val, (min_val, max_val)
                    )
    
    return selected_filters


def filter_data_by_parameters(df: pd.DataFrame, selected_filters: Dict) -> pd.DataFrame:
    """
    Filter the DataFrame based on selected simulation parameters.
    
    :param df: Input DataFrame
    :param selected_filters: Dictionary of selected filter values
    :return: Filtered DataFrame
    """
    filtered_df = df.copy()
    
    for key, value in selected_filters.items():
        if key.endswith('_range'):
            # Range filter
            param = key.replace('_range', '')
            min_val, max_val = value
            filtered_df = filtered_df[(filtered_df[param] >= min_val) & (filtered_df[param] <= max_val)]
        else:
            # Multiselect filter
            if isinstance(value, list) and len(value) > 0:
                filtered_df = filtered_df[filtered_df[key].isin(value)]
    
    return filtered_df


def create_method_selector(header_methods: List[str]) -> str:
    """
    Create a widget to select a method.
    
    :param header_methods: List of available methods
    :return: Selected method name
    """
    st.subheader("Select Analysis Method")
    selected_method = st.selectbox("Method", header_methods)
    return selected_method


def create_independent_variable_selector(header_sim_params: List[str], 
                                         filtered_data: pd.DataFrame) -> str:
    """
    Create a widget to select the independent variable for plots.
    
    :param header_sim_params: List of simulation parameter names
    :param filtered_data: Filtered DataFrame to determine available options
    :return: Selected independent variable name
    """
    st.subheader("Select Independent Variable for Plots")
    
    # Only show parameters that have variation in the filtered data
    available_params = []
    for param in header_sim_params:
        if filtered_data[param].nunique() > 1:
            available_params.append(param)
    
    if not available_params:
        st.warning("No parameters with variation in filtered data. Using first parameter.")
        return header_sim_params[0]
    
    selected_param = st.selectbox("Independent Variable", available_params)
    return selected_param


def create_color_variable_selector(header_sim_params: List[str], 
                                   filtered_data: pd.DataFrame) -> str:
    """
    Create a widget to select a parameter for coloring the plot points.
    
    :param header_sim_params: List of simulation parameter names
    :param filtered_data: Filtered DataFrame to determine available options
    :return: Selected color variable name
    """
    # Only show parameters that have variation in the filtered data
    available_params = []
    for param in header_sim_params:
        if filtered_data[param].nunique() > 1:
            available_params.append(param)
    
    if not available_params:
        st.info("No parameters with variation. Colors will be uniform.")
        return None
    
    selected_param = st.selectbox("Color by Parameter (optional)", [None] + available_params, format_func=lambda x: "None" if x is None else x)
    return selected_param


def create_metrics_plots(filtered_data: pd.DataFrame, method: str, x_variable: str,
                         header_metrics: List[str], 
                         color_variable: str = None) -> go.Figure:
    """
    Create subplots for all metrics as a function of the selected independent variable.
    Displays plots in a 3-column grid layout.
    
    :param filtered_data: Filtered DataFrame
    :param method: Selected method name
    :param x_variable: Independent variable name
    :param header_metrics: List of metric names
    :param color_variable: Optional variable to use for color coding
    :return: Plotly Figure object
    """
    import math
    
    # Remove metrics that don't have data for this method or have too many NaNs
    available_metrics = []
    for metric in header_metrics:
        col_name = f"{method}_{metric}"
        if col_name in filtered_data.columns:
            # Check if most values are not NaN
            if filtered_data[col_name].notna().sum() > len(filtered_data) * 0.1:
                available_metrics.append(metric)
    
    if not available_metrics:
        st.error(f"No data available for method '{method}'")
        return None
    
    # Calculate grid dimensions (3 columns)
    cols_per_row = 3
    num_rows = math.ceil(len(available_metrics) / cols_per_row)
    
    # Create subplots with 3 columns
    fig = make_subplots(
        rows=num_rows, 
        cols=cols_per_row,
        subplot_titles=[metric.replace('_', ' ').title() for metric in available_metrics],
        vertical_spacing=0.12,
        horizontal_spacing=0.10
    )
    
    # Add traces for each metric
    for idx, metric in enumerate(available_metrics):
        col_name = f"{method}_{metric}"
        
        # Get valid data (non-NaN)
        valid_mask = filtered_data[col_name].notna() & filtered_data[x_variable].notna()
        x_data = filtered_data[valid_mask][x_variable]
        y_data = filtered_data[valid_mask][col_name]
        
        # Prepare color data
        color_data = None
        if color_variable and color_variable in filtered_data.columns:
            color_data = filtered_data[valid_mask][color_variable]
        
        # Calculate position in grid
        row_pos = (idx // cols_per_row) + 1
        col_pos = (idx % cols_per_row) + 1
        
        # Show colorbar only on the last trace if we have color data
        show_colorbar = (idx == len(available_metrics) - 1) and (color_data is not None)
        
        scatter = go.Scatter(
            x=x_data,
            y=y_data,
            mode='markers',
            name=metric,
            showlegend=False,
            marker=dict(
                size=7,
                color=color_data if color_data is not None else 'rgba(99, 99, 99, 0.8)',
                colorscale='Greys' if color_data is not None else None,
                showscale=show_colorbar,
                reversescale=True if color_data is not None else False,
                line=dict(
                    color='royalblue',
                    width=0.5
                ),
                colorbar=dict(
                    title=color_variable if color_variable else None,
                    thickness=15,
                    len=0.7,
                    x=1.02
                ) if show_colorbar else None,
                opacity=0.75
            )
        )
        
        fig.add_trace(scatter, row=row_pos, col=col_pos)
        
        # Update axes labels
        fig.update_xaxes(
            title_text=x_variable.replace('_', ' ').title(), 
            row=row_pos, col=col_pos,
            showgrid=True,
            gridwidth=0.5,
            griddash='dash',
            gridcolor='rgba(200, 200, 200, 0.4)'
        )
        fig.update_yaxes(
            title_text=metric.replace('_', ' ').title(), 
            row=row_pos, col=col_pos,
            showgrid=True,
            gridwidth=0.5,
            griddash='dash',
            gridcolor='rgba(200, 200, 200, 0.4)'
        )
    
    # Update layout
    plot_height = 350 * num_rows  # Approx 3x the original (250 -> ~350 per plot)
    color_info = f" | Color: {color_variable}" if color_variable else ""
    
    fig.update_layout(
        height=plot_height,
        width=1400,
        showlegend=False,
        title_text=f"Method: {method} | X-axis: {x_variable}{color_info}",
        font=dict(size=10),
        margin=dict(r=150)  # Extra margin on right for colorbar
    )
    
    return fig


def display_simulation_summary(filtered_data: pd.DataFrame, header_sim_params: List[str]) -> None:
    """
    Display a summary of the filtered simulations.
    
    :param filtered_data: Filtered DataFrame
    :param header_sim_params: List of simulation parameter names
    """
    st.subheader("Filtered Simulation Summary")
    
    summary_data = {
        'Parameter': [],
        'Min': [],
        'Mean': [],
        'Max': [],
        'Unique Values': []
    }
    
    for param in header_sim_params:
        if param in filtered_data.columns:
            summary_data['Parameter'].append(param)
            
            # Check if column is numeric or categorical
            if pd.api.types.is_numeric_dtype(filtered_data[param]):
                summary_data['Min'].append(f"{filtered_data[param].min():.4g}")
                summary_data['Mean'].append(f"{filtered_data[param].mean():.4g}")
                summary_data['Max'].append(f"{filtered_data[param].max():.4g}")
            else:
                # For categorical/string columns, show unique values
                summary_data['Min'].append(str(filtered_data[param].min()))
                summary_data['Mean'].append("—")
                summary_data['Max'].append(str(filtered_data[param].max()))
            
            summary_data['Unique Values'].append(filtered_data[param].nunique())
    
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)


def display_results_summary(filtered_data: pd.DataFrame, method: str, 
                           header_metrics: List[str]) -> None:
    """
    Display comprehensive statistics for all metrics across filtered simulations.
    
    :param filtered_data: Filtered DataFrame
    :param method: Selected method name
    :param header_metrics: List of metric names
    """
    st.subheader("Results Summary Statistics")
    
    # Prepare statistics data
    stats_data = {
        'Metric': [],
        'Mean': [],
        'Std': [],
        '5th %ile': [],
        '25th %ile': [],
        'Median': [],
        '75th %ile': [],
        '95th %ile': []
    }
    
    for metric in header_metrics:
        col_name = f"{method}_{metric}"
        
        # Check if column exists and has valid data
        if col_name not in filtered_data.columns:
            continue
        
        # Get valid data (non-NaN)
        data = filtered_data[col_name].dropna()
        
        if len(data) == 0:
            continue
        
        # Compute statistics
        stats_data['Metric'].append(metric.replace('_', ' ').title())
        stats_data['Mean'].append(f"{data.mean():.4g}")
        stats_data['Std'].append(f"{data.std():.4g}")
        stats_data['5th %ile'].append(f"{data.quantile(0.05):.4g}")
        stats_data['25th %ile'].append(f"{data.quantile(0.25):.4g}")
        stats_data['Median'].append(f"{data.quantile(0.50):.4g}")
        stats_data['75th %ile'].append(f"{data.quantile(0.75):.4g}")
        stats_data['95th %ile'].append(f"{data.quantile(0.95):.4g}")
    
    # Display as dataframe
    if stats_data['Metric']:
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
    else:
        st.warning(f"No valid data available for method '{method}'")
