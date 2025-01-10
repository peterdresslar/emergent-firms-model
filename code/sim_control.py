"""
sim_control.py
--------------
This module manages the execution of multiple simulation runs for the agent-based model
defined in EmergentFirmsModel.py. It serves as a “control plane,” allowing you to:

  • Specify parameter sets and experiment configurations
  • Launch batches of simulations with varying settings
  • Collect and organize run-level outputs for downstream analysis (e.g., metastatistics)
  • Maintain consistency and reproducibility across experiments

Use sim_control.py to coordinate and automate large-scale simulation tasks without
further bloating the core model’s source code in EmergentFirmsModel.py.

You can run a single sim using sim_control by calling the script with arguments:

    python sim_control.py --sim_name <sim_name> --sim_runs <num_runs>

This will run the model (at EmergentFirmsModel.py) with the *default* parameters and number of runs.
Or, along the same lines, you can run a single sim with overridden parameters:

    python sim_control.py --sim_name <sim_name> --sim_runs <num_runs> --debt_awareness <bool> --loan_term <int> --loan_cap <int>

See the model itself for the full list of settable parameters.

You can also run multiple sims (or just a single, well-defined sim) by calling the script with a the file path to a sim definition json file:
    python sim_control.py --sim_def <sim_def_file_path>

An example sim definition file is provided in the sims/ directory.
"""

import argparse
import json
import sys
from pathlib import Path
import importlib.util

def load_model():
    """Dynamically import EmergentFirmsModel.py"""
    model_path = Path(__file__).parent / "EmergentFirmsModel.py"
    spec = importlib.util.spec_from_file_location("EmergentFirmsModel", model_path)
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    return model

def run_single_sim(sim_name, sim_runs, **model_params):
    """Run a single simulation with specified parameters"""
    model = load_model()
    
    # Override default model parameters with any provided params
    for param, value in model_params.items():
        if hasattr(model, param):
            setattr(model, param, value)
        else:
            print(f"Warning: Parameter '{param}' not found in model")
    
    # TODO: Implement actual simulation runs
    print(f"Running simulation '{sim_name}' for {sim_runs} iterations")
    print("Model parameters:", model_params)

def run_multi_sim(sim_def_path):
    """Run simulations defined in a JSON file
    
    The JSON file can contain:
    - No sims: runs a single simulation with default parameters
    - One sim: runs that simulation with its specified parameters
    - Multiple sims: runs each simulation with its respective parameters
    """
    with open(sim_def_path) as f:
        sim_def = json.load(f)
    
    # If no sims defined, run with defaults
    if "sims" not in sim_def:
        print("No simulations defined in file, running with default parameters")
        run_single_sim(
            sim_name=sim_def.get("sim_name", "default_sim"),
            sim_runs=1
        )
        return
    
    # Run each defined simulation
    for sim in sim_def["sims"]:
        run_single_sim(
            sim_name=sim["sim_name"],
            sim_runs=sim.get("sim_runs", 1),  # Default to 1 run if not specified
            **sim.get("sim_params", {})
        )

def main():
    parser = argparse.ArgumentParser(description="Control plane for EmergentFirmsModel simulations")
    
    # Create mutually exclusive argument group
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sim_def", type=str, help="Path to simulation definition JSON file")
    group.add_argument("--sim_name", type=str, help="Name for a single simulation run")
    
    # Optional arguments for single sim mode
    parser.add_argument("--sim_runs", type=int, help="Number of simulation runs", default=1)
    parser.add_argument("--debt_awareness", type=bool, help="Whether agents consider loan repayability")
    parser.add_argument("--loan_term", type=int, help="Loan repayment lookahead period")
    parser.add_argument("--loan_cap", type=int, help="Maximum total loan amount")
    
    args = parser.parse_args()
    
    if args.sim_def:
        run_multi_sim(args.sim_def)
    else:
        # Extract model params from args, excluding None values
        model_params = {k: v for k, v in vars(args).items() 
                       if k not in ["sim_def", "sim_name", "sim_runs"] and v is not None}
        run_single_sim(args.sim_name, args.sim_runs, **model_params)

if __name__ == "__main__":
    main()
