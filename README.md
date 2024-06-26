# CELAVI and Circularity Futures
A circular economy emphasizes the efficient use of all resources (e.g., materials, land, water). Despite anticipated overall benefits to society, the transition to a circular economy is likely to create regional differences in impacts. Current tools are unable to fully evaluate these potential externalities, which will be important for informing research prioritization and regional decision making. 

The Circular Economy Lifecycle Assessment and VIsualization (CELAVI) framework allows stakeholders to quantify and visualize potential regional and sectoral transfers of impacts that could result from transitioning to a circular economy, with particular focus on energy materials. The framework uses system dynamics to model material flows for multiple circular economy pathways and decisions are based on learning-by-doing and are implemented via cost and strategic value of different circular economy pathways. It uses network theory to track the spatial and sectoral flow of functional units across a graph and discrete event simulation to to step through time and evaluate lifecycle assessment data at each time step. The framework is designed to be flexible and scalable to accommodate multiple energy materials and multiple energy technologies. The primary goal of CELAVI is to help answer questions about how material flows and environmental and economic impacts of energy systems might change if the circularity of energy systems increases. 

## Branch Structure and Management

This repo contains code development for the CELAVI codebase (local cost minimization determines material flows) and the Circularity Futures codebase (material flows determine local and system costs). Our long-term goal is to merge these two decision-making functionalities into a single unified model, but for now please consider these two codebases as separate.

* For CELAVI development, see `master`, `develop`, and `doc-pages`, as well as any issue or bug fix branches off of these. Releases up through v1.3.2 correspond to CELAVI.
* For Circularity Futures develpment, see `dev-circfutures` and issue/bug fix branches off of this branch ONLY. DO NOT merge any Circularity Futures development, issue, or bug fix branches back into `master`, as this will overwrite the latest working version of CELAVI.

Please maintain good repo hygiene by creating one branch per Git issue, using consistent branch naming schemes, tagging issues in commit messages, and writing explanatory commit messages.

## macOS and Windows

On macOS, use Terminal to type the commands. On Windows, use the Anaconda Prompt. To start typing the commands, you will need to use the `cd` command (which does the same thing on macOS and Windows) to navigate to the root of the cloned repository. Most of the commands work the same on macOS or Windows. Where they differ, this documentation will call those difference out.

## Installation

This installation assumes you are using `conda` to create virtual environments. CELAVI requires packages from `pip` and `conda`, so there are two steps to the installation. These installation commands only need to be executed once before CELAAVI can be executed.

### Installation step 1: pip install
From the command prompt with the folder of your cloned repository, execute the following commands (these only need to be ran once at installation time):

```
conda create -n celavi python=3.8
conda activate celavi
pip install -e .
```

## Running the package

From the root of the repo, type a command similar to the following. This will execute the costgraph. Note that the paths to the files will need to be changed for your particular folder structure.

```
python -m celavi --data [your path to the CELAVI data folder] --config [your path to the config file(yaml) in the CELAVI data folder]
```

## Guide for development

### Code formatting and type checking

To ensure code consistency, we use MyPy for type checking and Black for code formatting. This table lists some information on these packages and how they are set up:

Package | What it does | Configuration File | URL for more information |
---|---|---|---
MyPy | Creates optional type checking for variables in the code to reduce errors that arise from type mismatches | `mypy.ini` | [http://mypy-lang.org/](http://mypy-lang.org/)
Black | Ensures code is consistently formatted | `pyproject.toml` | [https://black.readthedocs.io/en/stable/](https://black.readthedocs.io/en/stable/)

### Manually executing code formatting and type checking

From the root of the repo, run the following commands

```
mypy celavi
black celavi --exclude sd_model.py
```

(Note: The `--exclude` option will ignore the automatically generated SD model from PySD)

If all passes, you will get status messages that look similar to the following:

The message from MyPy:

```
Success: no issues found in 1 source file
```

The message from Black:

```
All done! ✨ 🍰 ✨
1 file left unchanged.
```

Black has the useful feature that, if it finds a non-compliant file, it will fail with an error but will also reformat the file for you.

The first time you run MyPy can be slow since it needs to parse the files and put them into a cache for faster type checking.

### Docstrings

To build the documentation from the docstrings in the code, type the following commands from the root of the repo:

On macOS, from the root of the repo, type the following command:

``` 
cd docs
make html
```

On Windows, from the root of the repo, type the following command:

``` 
cd docs
make.bat html
```

After these commands, these documentation can be found at `docs/_build/html/index.html`

### Testing

This project uses `pytest` as the testing framework. To run all the tests, execute the following command from the root of the repo.

``` 
pytest celavi/tests
```
