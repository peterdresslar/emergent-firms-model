"""
sim_control.py

A WORK IN PROGRESS


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
import asyncio
from run_model import run_model

async def run_simulation(sim_def_path):
    """Run a single simulation definition file"""
    with open(sim_def_path) as f:
        simdef = json.load(f)
    
    print(f"Running simulation(s) defined in {sim_def_path}")
    results = await run_model(simdef)
    return results

async def run_simulations(sim_def_paths):
    """Run multiple simulation definition files"""
    tasks = []
    for sim_def_path in sim_def_paths:
        tasks.append(run_simulation(sim_def_path))
    
    results = await asyncio.gather(*tasks)
    return results

def main():
    parser = argparse.ArgumentParser(description="Control plane for EmergentFirmsModel simulations")
    
    # Add optional positional argument for sim_def file
    parser.add_argument("sim_def_file", nargs="?", type=str, 
                       help="Path to simulation definition JSON file")
    
    # Add named arguments group
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sim_def", type=str, help="Path to simulation definition JSON file")
    group.add_argument("--sim_defs", nargs="+", type=str, help="Multiple simulation definition files")
    
    args = parser.parse_args()

    # Collect all sim_def paths
    sim_def_paths = []
    if args.sim_def_file:
        sim_def_paths.append(args.sim_def_file)
    if args.sim_def:
        sim_def_paths.append(args.sim_def)
    if args.sim_defs:
        sim_def_paths.extend(args.sim_defs)

    if not sim_def_paths:
        print("No simulation definition provided.")
        parser.print_help()
        return

    # Run simulations
    asyncio.run(run_simulations(sim_def_paths))

if __name__ == "__main__":
    main()
