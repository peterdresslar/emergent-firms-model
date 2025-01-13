"""
model_config.py
---------------
This file defines the configuration parameters for the EmergentFirmsModel. Each parameter
has metadata about its name, type, default value, and a short description.

You can import and use these definitions in a “run_model.py” or other control-plane modules.
"""

PARAMETERS = [
    {
        "name": "N",
        "type": int,
        "default": 600,
        "description": "Number of agents in the simulation",
    },
    {
        "name": "churn",
        "type": float,
        "default": 0.01,
        "description": "Activation rate for agent decisions in each step",
    },
    {
        "name": "cost",
        "type": float,
        "default": 1.0,
        "description": "Base job-change cost for an agent to move or start a firm",
    },
    {
        "name": "multiplier",
        "type": float,
        "default": 2.0,
        "description": "Multiplier for startup costs when founding a new firm (as opposed to job-change costs)",
    },
    {
        "name": "savingrate",
        "type": float,
        "default": 0.03,
        "description": "Mean savings rate for agents; fraction of wage they put away each time step",
    },
    {
        "name": "sigma",
        "type": float,
        "default": 0.01,
        "description": "Standard deviation for truncated normal distribution of savingrates across agents",
    },
    {
        "name": "lending",
        "type": int,
        "default": 1,
        "description": "Toggle for loan functionality; 1 = on, 0 = off",
    },
    {
        "name": "lendingrate",
        "type": float,
        "default": 0.0025,  # ~3% APR if steps are monthly (example)
        "description": "Interest rate on loans applied each time step (compounded in pay_loans())",
    },
    {
        "name": "debt_awareness",
        "type": bool,
        "default": True,
        "description": "If True, agents consider whether they can repay loans before taking them",
    },
    {
        "name": "loan_repayment_lookahead",
        "type": int,
        "default": 12,
        "description": "Number of steps an agent looks ahead to ensure they can repay a new loan",
    },
]

if __name__ == "__main__":
    print(PARAMETERS)