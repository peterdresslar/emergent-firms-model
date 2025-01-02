
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
