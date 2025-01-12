from EmergentFirmsModel import action

def run_EmergentFirmsModel(parameters=None, path='./data/', experiment='default'):
    # Default parameters if none provided
    default_parameters = [
        600,    # N
        0.01,   # churn
        1,      # cost
        2,      # multiplier
        0.03,   # savingrate
        0.01,   # sigma
        1,      # lending
        0.0025  # lendingrate
    ]
    
    # If parameters is None or partially specified, use defaults
    if parameters is None:
        parameters = default_parameters
    else:
        # Ensure parameters is the correct length by filling in with defaults
        parameters = [
            p if p is not None else d 
            for p, d in zip(parameters + [None] * len(default_parameters), default_parameters)
        ][:len(default_parameters)]
    
    # Run model with parameters and path
    F, agentHistory = action(parameters, path, experiment)
    
    return F, agentHistory

def run_model(model, parameters=None, path='./data/', experiment='default'):
    if model == "EmergentFirmsModel":
        return run_EmergentFirmsModel(parameters, path, experiment)
    else:
        raise ValueError(f"Model {model} not found")

if __name__ == "__main__":
    # Example usage if running directly
    run_EmergentFirmsModel()