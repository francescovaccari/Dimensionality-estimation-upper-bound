# Dimensionality Estimation Upper Bound Streamlit App

This repository hosts a Streamlit application designed to help estimate the number of significant components in high-dimensional data. 
The app filters simulations obtained from the paper (Vaccari et al., [paper here]) based on user-defined settings and visualizes the results, providing simple statistics to guide dimensionality estimation.

Upon usage, please cite:
> FE Vaccari, S Diomedi, E Bettazzi, M Filippini, M De Vitis, K Hadjidimitrakis, P Fattori<br>
> **More or fewer latent variables in the high-dimensional data space? That is the question**<br>
> *Journal yyyy*, [link here]<br>
> (arXiv link: [link here])

## Rationale Behind the Analysis

Properly estimating the number of dimensions (or components) in data is crucial for proper data interpretation and subsequent analysis. In contexts like neural data, where the underlying structure is complex and involves many latent variables, failing to determine the correct dimensionality can lead to misleading conclusions, such as mistaking noise for meaningful signal.

To address this challenge, we designed a subset of simulations with a complex underlying structure, including a large number of latent variables. These simulations explore scenarios where not all latent variables are detectable, allowing us to estimate upper bounds for identifiable dimensionality. The key insight behind this analysis is that, given a known decreasing curve in the explained variance of the principal components (PCs), and a data matrix with specific dimensions, one cannot reliably estimate an arbitrarily large number of significant components. This method helps define the upper limits of dimensionality estimation, especially in high-dimensional data depending on matrix properties and criterion used.

## How to Use the App

The app allows users to filter simulations based on specific criteria (e.g., matrix size, normalization procedure, criterion used for dimensionality estimation etc.) and visualize the results.
The application provides an interactive interface to help users understand and analyze dimensionality estimation in different settings.

**Note:**
- Some parameters allow the user to select a range (e.g. [50, 100] observed variables or neurons). Setting the minimum and maximum values to the same number will select only that specific value for that parameter.
- For neural data, the recommended settings are:
  - **Generative Process**: 'PCs'
  - **Noise Distribution**: 'Gaussian'
- The parameter tau can be estimated using the `fit_tau.m` function available in the MATLAB package provided at: [https://github.com/francescovaccari/Dimensionality-estimation](https://github.com/francescovaccari/Dimensionality-estimation)
- According to the results presented in our paper, **PA/CV** emerged as the most consistent methods. **CV** can sometimes yield highly variable results whereas **PA** can be too conservative in some cases.


## Support
Email francesco.vaccari6@unibo.it with any questions.
