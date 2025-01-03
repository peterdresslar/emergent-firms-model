# Emergent Firms Model - Extended Analysis

This repository contains analysis and extensions of the Emergent Firms Model originally developed by J M Applegate. The base model explores how firms emerge from individual agents' utility-maximizing behaviors, including effects of capital constraints and lending.

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

### Version 1.0.1
- **Critical Model Change:** The model now uses a directed graph to represent the employer-employee relationship. This involved the following changes:
    - The graph is now initialized as a directed graph (`nx.DiGraph`).
    - The `nx.node_connected_component` function was replaced with `nx.descendants` to find reachable nodes in a directed graph.
    - The `nx.connected_components` function was replaced with `nx.strongly_connected_components` in the `distribute_output` function.
    - **Conceptual Change:** The `distribute_output` function now distributes output based on *strongly connected components* rather than *connected components*. This is a conceptual change that should be reviewed carefully, as it may affect the model's behavior.

    Note for this version of the model: we see that there may be a difference between the intended operation of the loans concept and the actual implementation. We will explore this in future versions.

## Analysis Tools

This repository includes the following analysis tools:

- **`visualize_network_static.py`**: This script generates a static visualization of the network structure from a GML file. The visualization includes:
    - A main subplot showing the connected firms and workers, with node size representing the number of employees (in-degree) and node color representing the net worth (savings - loans) using a `SymLogNorm` colormap.
    - A row of singletons (self-employed agents) arranged by net worth.
    - Directed edges from worker to employer.
    - A colorbar indicating the net worth scale.
- **`check_gml_stats.py`**: This script calculates and prints basic statistics from a GML file, including:
    - The maximum number of employees (in-degree).
    - The maximum number of employers (out-degree).
    - The maximum savings.
    - The maximum loan.

## Requirements
python
- numpy>=1.20.0
- networkx>=2.6.0
- pandas>=1.3.0
- scipy>=1.7.0

## Usage
0. (From the code directory)
1. Create and activate a Python virtual environment
2. Install requirements: `pip install -r requirements.txt`
3. Run the model: `python EmergentFirmsModel.py`

The model will generate (by default in the working directory):
- A CSV file containing agent history
- A GML file representing the final network structure

## License
This work is derived from code licensed under CC-BY-NC (Creative Commons Attribution-NonCommercial).

## Acknowledgments
This work builds upon the Emergent Firms Model developed by J M Applegate, which itself extends concepts from Rob Axtell's Endogenous Dynamics of Multi-Agent Firms model. Please see the original documentation and CoMSES-specific metadata in `/docs` for more information.
