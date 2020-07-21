# CELAVI
A circular economy emphasizes the efficient use of all resources (e.g., materials, land, water). Despite anticipated overall benefits to society, the transition to a circular economy is likely to create regional differences in impacts. Current tools are unable to fully evaluate these potential externalities, which will be important for informing research prioritization and regional decision making. 

The Circular Economy Lifecycle Assessment and VIsualization (CELAVI) framework allows stakeholders to quantify and visualize potential regional and sectoral transfers of impacts that could result from transitioning to a circular economy, with particular focus on energy materials. The framework uses system dynamics to model material flows for multiple circular economy pathways and decisions are based on learning-by-doing and are implemented via cost and strategic value of different circular economy pathways. It uses network theory to track the spatial and sectoral flow of functional units across a graph and discrete event simulation to to step through time and evaluate lifecycle assessment data at each time step. The framework is designed to be flexible and scalable to accommodate multiple energy materials and multiple energy technologies. The primary goal of CELAVI is to help answer questions about how material flows and environmental and economic impacts of energy systems might change if the circularity of energy systems increases. 

## Quickstart

From the folder into which this was repo was cloned
```
conda create -n tiny-lca python=3.7
pip install -e .
python suh_section_3.2.py
```

## Citations

This software may use [OpenMDAO](https://openmdao.org):

J. S. Gray, J. T. Hwang, J. R. R. A. Martins, K. T. Moore, and B. A. Naylor, “OpenMDAO: An Open-Source Framework for Multidisciplinary Design, Analysis, and Optimization,” Structural and Multidisciplinary Optimization, 2019.

It also implements sections of the following papers:

Suh, Sagnwon. "Functions, commodities and environmental impacts in an ecological–economic model." Ecological Economics 48 (2004) 451–467
