# Explore-our-data-app

Just a minimal csv explorer app, built and hosted on [Streamlit](https://docs.streamlit.io/). It allows custom filtering and plotting of tabular data, in the most common formats (csv, tsv, xlsl).
To specify which columns represent data filters, results and plots variables, a JSON file is provided in the repo (check the [template](config.json5)).

**What's the use of this app?**
If you're looking for a way to show your data in a free, simple and effective interface: that's the case. 

**A case use from open-research**
[Vaccari et al. 2024](Link) computed simulations of neural data based on multiple combinations of parameters (like the number of neurons, length of recordings, etc), then used different methods to estimate the least number of dimensions representing the signal.
Since the process can be computationally intensive and time-consuming, they released the simulations data for everyone to use (and save some energy (green symbol)), and provided a [link]() to this app to let readers filter them and check results statistics and plots.

## From installation to deployment

Installation is very easy, just get the repo, create and activate a python (or conda) environment

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

5. Add your forked repo to your own Streamlit account, and deploy from there.

## Features

## Contributing

#