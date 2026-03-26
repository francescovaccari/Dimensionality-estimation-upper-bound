import pandas as pd
import streamlit as st
from pathlib import Path
from ._utils.helpers import (
    load_data_to_sqlite,
    extract_metadata_from_data,
    create_simulation_filter_widgets,
    filter_data_by_parameters,
    create_method_selector,
    create_independent_variable_selector,
    create_color_variable_selector,
    create_metrics_plots,
    display_simulation_summary,
    display_results_summary,
)

# Set page config
st.set_page_config(
    page_title="Dimensionality Estimation Analysis",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dimensionality Estimation Analysis")
st.write("Filter simulations and visualize metrics by method and independent variable")

# ============================================================================
# INITIALIZE SESSION STATE
# ============================================================================
if 'filter_clicked' not in st.session_state:
    st.session_state.filter_clicked = False

# ============================================================================
# LOAD DATA
# ============================================================================
st.subheader("Load Data", divider=True)

# Try to load from local file
data_file_path = Path("data/Data_table.csv")
if data_file_path.exists():
    df = pd.read_csv(data_file_path)
    st.success(f"✅ Loaded data from {data_file_path}")
    st.write(f"Data shape: {df.shape[0]} simulations × {df.shape[1]} columns")
else:
    st.error(f"❌ Data file not found at {data_file_path}")
    st.stop()

# ============================================================================
# EXTRACT METADATA
# ============================================================================
header_sim_params, header_methods, header_metrics, all_columns = extract_metadata_from_data(df)

st.write("**Metadata extracted:**")
col1, col2, col3 = st.columns(3)
with col1:
    st.write(f"📍 **Simulation Parameters:** {len(header_sim_params)}")
    with st.expander("View list"):
        st.write(header_sim_params)
with col2:
    st.write(f"🔬 **Methods:** {len(header_methods)}")
    with st.expander("View list"):
        st.write(header_methods)
with col3:
    st.write(f"📈 **Metrics:** {len(header_metrics)}")
    with st.expander("View list"):
        st.write(header_metrics)

# ============================================================================
# FILTERING SECTION
# ============================================================================
st.subheader("Step 1: Filter Simulations", divider=True)

# Create filter widgets in a form
with st.form("filter_form", border=True):
    selected_filters = create_simulation_filter_widgets(df, header_sim_params)
    if st.form_submit_button(
        "🔄 Update Simulation Filtering",
        use_container_width=True,
        type="primary"
    ):
        st.session_state.filter_clicked = True

# Only proceed with analysis if the button was clicked
if not st.session_state.filter_clicked:
    st.info("👈 Adjust the filters above and click the button to proceed with the analysis.")
    st.stop()

# Apply filters
filtered_data = filter_data_by_parameters(df, selected_filters)

st.write(f"**Filtered result:** {filtered_data.shape[0]} / {df.shape[0]} simulations")

if filtered_data.empty:
    st.warning("⚠️ No data matches the current filters. Please adjust the filters.")
    st.stop()

# Display summary
display_simulation_summary(filtered_data, header_sim_params)

# ============================================================================
# METHOD SELECTION
# ============================================================================
st.subheader("Step 2: Select Analysis Method", divider=True)
selected_method = create_method_selector(header_methods)

# ============================================================================
# INDEPENDENT VARIABLE SELECTION
# ============================================================================
st.subheader("Step 3: Select Independent Variable", divider=True)
selected_x_var = create_independent_variable_selector(header_sim_params, filtered_data)

if filtered_data[selected_x_var].nunique() <= 1:
    st.warning(
        f"⚠️ Selected variable '{selected_x_var}' has no variation in the filtered data. "
        "Please adjust filters to have variation in the independent variable."
    )
    st.stop()

# ============================================================================
# COLOR VARIABLE SELECTION
# ============================================================================
st.subheader("Step 4: Select Color Variable (Optional)", divider=True)
selected_color_var = create_color_variable_selector(header_sim_params, filtered_data)

st.info(
    f"**Plotting all metrics** (x-axis: **{selected_x_var}**, method: **{selected_method}**"
    f"{f', color: **{selected_color_var}**' if selected_color_var else ''})"
)

# ============================================================================
# RESULTS SUMMARY
# ============================================================================
st.subheader("Step 5: Results Summary Statistics", divider=True)
display_results_summary(filtered_data, selected_method, header_metrics)

# ============================================================================
# VISUALIZATIONS
# ============================================================================
st.subheader("Step 6: Results Visualization", divider=True)

# Create plots
fig = create_metrics_plots(
    filtered_data=filtered_data,
    method=selected_method,
    x_variable=selected_x_var,
    header_metrics=header_metrics,
    color_variable=selected_color_var
)

if fig is not None:
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# DATA SUMMARY
# ============================================================================
st.subheader("Filtered Data Summary", divider=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Number of Simulations", filtered_data.shape[0])
with col2:
    st.metric(
        f"Unique {selected_x_var} values",
        filtered_data[selected_x_var].nunique()
    )
with col3:
    st.metric(
        "Data Completeness",
        f"{(filtered_data.notna().sum().sum() / (filtered_data.shape[0] * filtered_data.shape[1]) * 100):.1f}%"
    )

# Show first few rows of filtered data
with st.expander("📋 View filtered data (first 10 rows)"):
    st.dataframe(filtered_data.head(10), use_container_width=True)
