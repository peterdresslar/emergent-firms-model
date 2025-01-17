# Emergent Firms Model - Extended Analysis

This repository contains analysis and extensions of the Emergent Firms Model originally developed by J M Applegate. The base model explores how firms emerge from individual agents' utility-maximizing behaviors, including effects of capital constraints and lending.

## What's New in Version 1.0.1

### Refactor for Standalone Runability

- **Enhanced Execution Options**: 
  - The experiment wrapper was replaced with the `__main__` entry point: `action(...)` now initializes all logic so that it can be imported and called by external scripts without using libs.
  - You can still set variables in the model file and call simulations directly via `python EmergentFirmsModel.py` 
- **Flexible File Handling**:
  - New directory/path inputs
  - Configurable output locations via `path` and `experiment` parameters
- **Model Integrity**:
  - Apart from the new Debt Awareness logic (described below), all model logic is preserved with some small Python 3.11 compatibility updates

### Debt Awareness Enhancements

- **debt_awareness** (default: `True`)
  - When `True`: Agents consider loan repayability within loan term
  - When `False`: Agents use original model's naive borrowing
- **loan_repayment_lookahead**
  - Specifies future timesteps agents consider for loan repayment
  - Acts as effective loan term
  - Higher values indicate higher risk tolerance
- **lendingrate**
  - Aligned with model's monthly churn rate
  - Churn default and lendingrate defaults were tweaked to be more in line with each other. Note that with the new Debt Awareness option they are related in a way they otherwise were not before.
- **loan_cap**
  - Optional limit on total loan amounts
  - Disabled by default
  - Prevents runaway debt scenarios

These enhancements make the model behave differently by implementing practical lending constraints and allowing experimentation with different debt awareness scenarios.

## Analysis Tools

This new version also includes the following analysis products:

- **`visualize_network_static.py`**: This script generates a static visualization of the network structure from a GML file. The visualization includes:
    - A main subplot showing the connected firms and workers, with node size representing the number of employees (in-degree) and node color representing the net worth (savings - loans) using a `SymLogNorm` colormap.
    - A row of singletons (self-employed agents) arranged by net worth.
    - Directed edges from worker to employer.
    - A colorbar indicating the net worth scale.
    - The script uses `matplotlib` to generate the visualization and saves it as a PNG file.
- **`check_gml_stats.py`**: This script calculates and prints basic statistics from a GML file, including:
    - The maximum number of employees (in-degree).
    - The maximum number of employers (out-degree).
    - The maximum savings.
    - The maximum loan.
    - The script uses `networkx` to load the GML file and `numpy` to calculate the statistics.
- **`interactive_population_charts.ipynb`**: This Jupyter Notebook provides interactive charts for exploring agent-level data from the CSV output. It allows you to:
    - Select an agent ID from a dropdown menu.
    - View time series charts of various agent attributes, including `wage`, `savings`, `loan`, `a`, `beta`, `links`, `component`, `rate`, `U_self`, `e_self`, and `e_star`.
    - View binary attributes such as `startup`, `thwart`, `borrow`, `move`, and `go` as time series.
    - The notebook uses `pandas` to load the CSV data, `matplotlib` for plotting, and `ipywidgets` for interactivity.
- **Event Logging:** The model now generates an event log by default that gives extensive detail on decisioning. However, the code for this is quite verbose and I would like to clean it up in a future iteration.

## Introducing Sim Control

The `sim_control.py` script provides a control plane for running simulations. It allows you to:

- Run single or multiple simulations defined as "experiments" in JSON files.
- Specify experiment and simulation parameters and configurations.
- Automate large-scale simulation tasks.

To use `sim_control.py`, you can either:

1.  Provide a single experiment definition file:
    ```bash
    python sim_control.py --sim_def <path_to_sim_def.json>
    ```
2.  Provide multiple experiment definition files:
    ```bash
    python sim_control.py --sim_defs <path_to_sim_def1.json> <path_to_sim_def2.json> ...
    ```
3.  Provide a single experiment definition file as a positional argument:
    ```bash
    python sim_control.py <path_to_sim_def.json>
    ```

An example experiment definition file is provided in the `sims/` directory.

Please note that sim control is a work in progress.

## Original Model

The original version of this model is preserved in the `original-v1.0.0` branch. This represents the initial implementation as uploaded to CoMSES/OpenABM and serves as a reference point for all subsequent development. 

The `main` branch contains subsequent modifications by the maintainer of this repo, @peterdresslar.

The original model was developed by J M Applegate and is available on [CoMSES](https://www.comses.net). The model explores how economies and firms emerge from individual agent behaviors, incorporating:
- Returns-to-scale benefits
- Coordination advantages
- Cash-in-advance constraints
- Universal credit-creating lending mechanisms

## Technical Updates
The codebase includes very minor updates for compatibility with Python environments >= v3.11:
- Updated NetworkX syntax for node attribute access
- Modified numpy type declarations
- Updated package requirements for Python 3.11+ compatibility

## Requirements
python
- numpy>=1.20.0
- networkx>=2.6.0
- pandas>=1.3.0
- scipy>=1.7.0
- matplotlib>=3.4.0
- ipywidgets>=7.6.0

## Usage
0. (From the code directory)
1. Create and activate a Python virtual environment
2. Install requirements: `pip install -r requirements.txt`
3. Run the model: `python EmergentFirmsModel.py`

The model will generate (by default in the working directory):
- A CSV file containing agent history
- A GML file representing the final network structure
- A JSON file containing the event log
- A CSV file containing the firm history
- A CSV file containing the economic census

## Attribution

   This project builds upon work licensed under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) from [CoMSES Network](https://www.comses.net).

   - **Original Work**: https://www.comses.net/codebases/9e802c7e-20e5-4448-bb24-12e1b019ea98/releases/1.0.0/
   - **Original Author**: J. M. Applegate

## Acknowledgments
This work builds upon the Emergent Firms Model developed by J M Applegate, which itself extends concepts from Rob Axtell's Endogenous Dynamics of Multi-Agent Firms model. Please see the original documentation and CoMSES-specific metadata in `/docs` for more information.
