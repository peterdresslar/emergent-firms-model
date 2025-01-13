import asyncio
from EmergentFirmsModel import action
from model_def import MODEL_NAME, MODEL_VERSION, PARAMETERS #noqa
import os
from datetime import datetime

async def run_EmergentFirmsModel(parameters=None, tmax=100, path='../data/', experiment='default'):
    # If parameters is None, use all defaults
    if parameters is None:
        model_parameters = [p["default"] for p in PARAMETERS]
    else:
        # Convert parameters dict to list matching PARAMETERS order
        model_parameters = []
        param_dict = parameters if isinstance(parameters, dict) else {}
        
        for param_def in PARAMETERS:
            param_name = param_def["name"]
            # Use provided value if exists, otherwise use default
            param_value = param_dict.get(param_name, param_def["default"])
            model_parameters.append(param_value)
    
    # Run model with parameters and path
    F, agentHistory = await asyncio.to_thread(action, model_parameters, tmax, path, experiment)
    
    return F, agentHistory

async def run_model(expdef, path='../data/'):
    if not isinstance(expdef, dict):
        raise ValueError("expdef must be a dictionary")
    
    # Create base experiment directory with timestamp
    experiment_name = expdef.get("experiment_name")
    print(f"🚀 Commencing experiment {experiment_name} 🚀")
    experiment_path = os.path.join(path, experiment_name + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    os.makedirs(experiment_path, exist_ok=True)
        
    # Check if this is a multi-sim configuration
    if "sims" in expdef:
        tasks = []
        for sim in expdef["sims"]:
            # Check model name for each simulation
            if sim["model_name"] != "EmergentFirmsModel":
                raise ValueError(f"Model {sim['model_name']} not found")
                
            # Create tasks for each run of each simulation
            for run_num in range(sim["sim_runs"]):
                experiment_name = f"{sim['sim_name']}_run{run_num}"
                task = run_EmergentFirmsModel(
                    parameters=sim["sim_params"],
                    tmax=sim["sim_steps"],
                    path=experiment_path,
                    experiment=experiment_name
                )
                tasks.append(task)
        
        # Run all simulations concurrently and gather results
        results = await asyncio.gather(*tasks)
        return results
    else:
        # Single sim case
        if expdef.get("model_name") != "EmergentFirmsModel":
            raise ValueError(f"Model {expdef.get('model_name')} not found")
            
        return await run_EmergentFirmsModel(
            parameters=expdef.get("sim_params"),
            tmax=expdef["sim_steps"],
            path=experiment_path,
            experiment=expdef["experiment_name"]
        )

if __name__ == "__main__":
    # Example usage if running directly
    asyncio.run(run_EmergentFirmsModel())