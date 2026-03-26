# Dimensionality Estimation Upper Bound -- Streamlit App

This repository hosts a Streamlit application designed to help estimate
the number of significant components in high-dimensional data or simply 
to explore the results of our simulation study.

The app allows users to explore a large set of simulations from:

> Vaccari et al., 2024 (bioRxiv)

by interactively filtering parameters and visualizing how different
conditions affect dimensionality estimation methods.

👉 **Launch the app:**\
https://dimensionality-estimation-upper-bound.streamlit.app

------------------------------------------------------------------------

## 📌 Citation

If you use this tool, please cite:

> FE Vaccari, S Diomedi, E Bettazzi, M Filippini, M De Vitis, K
> Hadjidimitrakis, P Fattori\
> More or less latent variables in the high-dimensional data space? That
> is the question\
> bioRxiv 2024.11.28.625854\
> https://doi.org/10.1101/2024.11.28.625854

------------------------------------------------------------------------

## 🧠 Rationale Behind the Analysis

Estimating the intrinsic dimensionality of high-dimensional datasets is
a fundamental problem in data analysis, especially in fields such as
neuroscience.

In complex systems: - data structure can contain an unkwon number of
 many latent variables - not all latent variables are directly observable - 
noise and structure interact in non-trivial ways

To address this, we designed simulations with: - controlled latent
structure - realistic noise models - varying complexity. 
PCa was applied on the generated matrices and different PCA-based criteria to
estimate the optimal number of components were benchmarked.

Importantly, given a matrix with a specific size and a decreasing variance profile
across principal components, there exists an upper bound on the number
of dimensions that can be reliably estimated and distinguished from noise.

------------------------------------------------------------------------

## 🚀 How the App Works

The app provides an interactive interface to:

1.  Filter simulations based on parameter values\
2.  Choose one of 10+ PCA-based dimensionality estimation criteria\
3.  Inspect summary statistics\
4.  Visualize results across conditions

------------------------------------------------------------------------

## ⚙️ Simulation Parameters

Synthetic datasets (i.e. data matrices) of size **\[T, M\]** are generated, where:

-   **times_series_length:** number of samples (time points, T)
-   **fake_units:** number of observed variables (M)


### Core parameters

-   **gen:** method used to generate the latent variables (using a *dynamical* system or
        a *random* process)
-   **num_latent:** (N, n° of latent variables) true underlying dimensionality
-   **decayFactor:** (DF or Decay Factor) controls variance decay across components
-   **tau:** a posteriori variance decay estimates
-   **nonLinAlfa:** (α) degree of non-linear transformation
-   **nonLinear_var:** a posteriori nonlinearities estimates (in terms of % variance)


### Noise parameters

-   **noiseDistr:** (Noise distribution) following a *gaussian* or *poisson* distr.
-   **noiseFactor:** (NF or Noise Factor) overall noise level
-   **equalNoise:** (noise variability across units)
    -   *0*: β drawn from a normal distr. leading to units with different noise levels
    -   *1*: β equal for all units (same noise level)
-   **noise_var:** a posteriori noise estimates (in terms of % variance)

### Preprocessing

-   **soft_norm:** (final normalization before applying PCA)
    -   *0*: z-scoring
    -   *1*: soft-normalization

------------------------------------------------------------------------

## 🧪 Recommended Settings for Neural Data simulations

-   **gen** Generative Process: *dynamical*
-   **noiseDistr** Noise Distribution: *poisson*
-   **equalNoise** (noise variability across units): *0*
-   **soft_norm** (final normalization): *1*

  #### Additional settings for finding upper bound dimensionality when analyzing neural data

  -   Set **times_series_length**, **fake_units** and a **tau** range that match your own data
  -   **num_latent**: *1000*

------------------------------------------------------------------------

## Available criteria for dimensionality estimation
-   **80:** 80% explained variance threshold
-   **90:** 90% explained variance threshold
-   **PR:** Participation Ratio;
-   **K1:** Kaiser rule (retain components with eigenvalues > 1)
-   **PA:** Parallel Analysis (compare eigenvalues with those from shuffled data)
-   **optimal_SVHT:** Optimal Singular Value Hard Thresholding (Gavish & Donoho, 2014)
-   **CV_rows:** cross-validated PCA applied across rows only
-   **CV_cols:** cross-validated PCA applied across columns only
-   **CV_bicross:** bi-cross validation (simultaneous row/column holdout)
-   **CV_rows&cols:** cross-validation over rows and columns with missing data imputation
-   **OPTIMAL_knowing_struct:** oracle estimator using ground-truth latent dimensionality (used as a reference benchmark)


## 📬 Support

francesco.vaccari6@unibo.it
