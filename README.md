# Explore-our-data-app

Just a minimal csv explorer app, built and hosted on [Streamlit](https://docs.streamlit.io/). It allows custom filtering and plotting of tabular data, in the most common formats (csv, tsv, xlsl).
To specify which columns represent data filters, results and plots variables, a JSON file is provided in the repo (check the [template](config.json5)).

**What's the use of this app?**
If you're looking for a way to show your data in a free, simple and effective interface: that's the case. 

**A case use from open-research**
[Vaccari et al. 2024](PreprintLink) computed simulations of neural data based on multiple combinations of parameters (like the number of neurons, length of recordings, etc), then used different methods to estimate the least number of dimensions representing the signal.
Since the process can be computationally intensive and time-consuming, they released the simulated data for everyone to use (and save some energy :seedling:), and provided a [link](SimulationsDataExplorer) to their own version of this app, so that readers could filter the data and explore specific results.

## Install, customize and deploy

The process from installation to deployment is quite straightforward: fork this repo to your own github account and clone the forked repo to your local machine; then, create and activate a python (or conda) environment with all the required libraries

### Installation :gear:

**1.** Fork this repository directly on [Github](https://github.com/):

A fork is like your own copy of the project. 
In case you are not familiar with the process of forking:

1. *Click the "Fork" Button*: At the top right of this page, you’ll see a button that says Fork. Click it.

2. *Choose Your Account*: GitHub will ask where you want to fork the project. Select your GitHub account.
    
3. *Wait for the Fork to Complete*: After a few moments, you’ll have your own copy of this project under your GitHub account!


**2.** Clone the forked repository and navigate to root:

```bash
git clone https://github.com/[YourUsername]/[YourForkedRepo].git
cd YourForkedRepo
```

**3.** Create a virtual environment, activate it and install the requirements, with conda:
```bash
conda create -n streamlit-app python
conda activate streamlit-app
pip install -r requirements
```
or with python:
```bash
python -m path/to/venv 
source <path/to/venv>/bin/activate
pip install -r requirements
```

### Customization :pencil:

**1.** Put your own data in the `/data` folder, or just get the data from an external source. 
Specify the data source accordingly:

```json5
data_source: {
      path: "data/your_data.csv",
      url: "",
    }
```
Supported formats: csv, tsv, xlxs. File size is limited to 50 MB by Github, and to 200 MB by Streamlit.

**2.** Fill the [config file](config.json5), i.e. specify the names (and site labels) of the columns that should be used as filters, results and plot variables. For example:

```json5
// Data Filters Configuration
filters: {
// Single-valued filters (displayed as dropdown selectors)
single_valued: [
    {
    name: "column_name",
    label: "variable name",
    },

    // Add more filters
],

// Range filters with discrete values (displayed as two horizontal dropdown selectors)
range_discrete: [
    {
    name: "column_name",
    label: "variable name",
    },

    // Add more filters
],

// Range filters with continuous values (displayed as a slider)
range_continuous: [
    {
    name: "column_name",
    label: "variable name",
    },
],
}
```

**3.** Push the modifications to the forked repository.
```bash
cd forked-repo
git add .
git commit -m "Added data source; customized config file"
git push origin
```

### Deployment :rocket:

**1.** Create an account on [Streamlit Cloud](https://share.streamlit.io/).

**2.** Log in to your Streamlit Cloud account

**3.** Click "New app"

**4.** Select your GitHub account and the repository you created

**5.** Choose the main file (`app.py`)

**6.** Click "Deploy"


## Contributing

Any contribution, comment on features to add, critique on the current implementation, basically any feedback is very much appreciated :grin:

