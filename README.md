# 

This is a simple app built and maintained on [Streamlit](link to docs). It allows a showcast, filtering and plotting of tabular data in the most common formats (csv, tsv, xlsl).
Data filtering and results report/plotting can be customized by filling a configuration JSON file.

To give an idea of how this app can be used for research purposes, [Vaccari et al. 2024]() uses it to show/plot simulations of neural data, give a look [here](https://simulations-plotter-app-epkw2t8vpkwmaj3pqvtwjp.streamlit.app/)

Main purpose of this app is to allow exploring and sharing of research data for the sake of open-science and replicability.
Since no security measures are allowed

## From installation to deployment

Installation is very easy, just get the repo, create and activate a python or conda environment

### Steps

1. Clone this repository and navigate to root:
```bash
git clone git@github.com:EdoardoBettazzi/explore-our-data-app.git
cd explore-our-data
```

2. Create a virtual environment, activate it and install the requirements, with conda:
```bash
conda create -n explore_our_data python
conda activate explore_our_data
pip install -r requirements
```
or with python:
```bash
python -m path/to/venv 
source <path/to/venv>/bin/activate
pip install -r requirements
```

3. 
```bash
git clone èèèèèèèèèèèèèèèèè
```

4. fff
```bash
git clone èèèèèèèèèèèèèèèèè
```


## Setup

1. Put your own data in the `/data` folder. Supported formats: csv, tsv, xlxs. File size is limited to 50 MB by Github, and to 200 MB by Streamlit.

2. Fill the [config file](config.json5), i.e. specify the names (and site labels) of the columns that should be used as filters, results, plot variables.

3. Push the your personal forked repository.
```bash
cd forked-repo
git add .
git commit -m "Initial commit"
git push origin
```

4. Create an account on [Streamlit cloud](link).

5. Add your forked repo to 

## Features

## Contributing

#