import networkx as nx
import numpy as np

def generate_firms_report(agents, F, t):
    firms_data = []
    for g in nx.connected_components(F):
        h = list(g)
        n = len(h)
        # Skip singletons
        if n == 1:
            continue
            
        firm_id = agents[h[0]]['firm']
        a = agents[firm_id]['a']
        b = agents[firm_id]['b']
        beta = agents[firm_id]['beta']
        E = 0
        total_savings = 0
        total_loans = 0
        for j in g: 
            E += agents[j]['e_star']
            total_savings += agents[j]['savings']
            total_loans += agents[j]['loan']
        O_total = (a * E + b * E **beta)
        share = O_total / n
        
        firms_data.append({
            "time": t,
            "firm_id": firm_id,
            "num_employees": n,
            "total_effort": E,
            "total_output": O_total,
            "average_wage": share,
            "total_savings": total_savings,
            "total_loans": total_loans
        })
    return firms_data

def generate_economic_census(agents, t, F):
    # Initialize aggregates
    total_agents = len(agents)
    total_savings = 0
    total_loans = 0
    total_utility = 0
    total_effort = 0
    total_wages = 0
    
    # Initialize firm size distribution
    firm_sizes = {}
    singleton_count = 0
    
    # Calculate Gini coefficient helper function
    def gini(x):
        mad = np.abs(np.subtract.outer(x, x)).mean()
        rmad = mad/np.mean(x)
        return 0.5 * rmad
    
    # Collect data for distributions
    net_worths = []
    wages = []
    utilities = []
    
    for i, agent in agents.items():
        net_worth = agent['savings'] - agent['loan']
        net_worths.append(net_worth)
        wages.append(agent['wage'])
        utilities.append(agent['current_utility'] if i in F else agent['U_self'])
        
        total_savings += agent['savings']
        total_loans += agent['loan']
        total_utility += utilities[-1]
        total_effort += agent['e_star']
        total_wages += agent['wage']
        
        # Track firm sizes
        firm_id = agent['firm']
        if firm_id == i and len(list(nx.node_connected_component(F, i))) == 1:
            singleton_count += 1
        else:
            firm_sizes[firm_id] = firm_sizes.get(firm_id, 0) + 1
    
    # Calculate quintile boundaries (0, 20, 40, 60, 80, 100 percentiles)
    wealth_quintiles = np.percentile(net_worths, [0, 20, 40, 60, 80, 100])
    wage_quintiles = np.percentile(wages, [0, 20, 40, 60, 80, 100])
    utility_quintiles = np.percentile(utilities, [0, 20, 40, 60, 80, 100])
    
    # Calculate quintile means
    def quintile_means(data, boundaries):
        means = []
        for i in range(len(boundaries)-1):
            quintile_data = [x for x in data if boundaries[i] <= x < boundaries[i+1]]
            means.append(np.mean(quintile_data))
        return means
    
    wealth_quintile_means = quintile_means(net_worths, wealth_quintiles)
    wage_quintile_means = quintile_means(wages, wage_quintiles)
    utility_quintile_means = quintile_means(utilities, utility_quintiles)
    
    census_data = {
        "time": t,
        "num_firms": len(set(agent['firm'] for agent in agents.values())),
        "num_singleton_firms": singleton_count,
        "avg_firm_size": total_agents / (len(firm_sizes) + singleton_count) if (len(firm_sizes) + singleton_count) > 0 else 0,
        "largest_firm_size": max(firm_sizes.values()) if firm_sizes else 1,
        
        # Economic indicators
        "total_savings": total_savings,
        "total_loans": total_loans,
        "total_wages": total_wages,
        "total_effort": total_effort,
        "mean_utility": total_utility / total_agents,
        
        # Inequality measures
        "wage_gini": gini(wages),
        "wealth_gini": gini(net_worths),
        "utility_gini": gini(utilities),
        
        # Distribution statistics
        "wealth_std": np.std(net_worths),
        "wage_std": np.std(wages),
        "utility_std": np.std(utilities),
        
        # Quintile boundaries
        "wealth_q0": wealth_quintiles[0],
        "wealth_q20": wealth_quintiles[1],
        "wealth_q40": wealth_quintiles[2],
        "wealth_q60": wealth_quintiles[3],
        "wealth_q80": wealth_quintiles[4],
        "wealth_q100": wealth_quintiles[5],
        
        "wage_q0": wage_quintiles[0],
        "wage_q20": wage_quintiles[1],
        "wage_q40": wage_quintiles[2],
        "wage_q60": wage_quintiles[3],
        "wage_q80": wage_quintiles[4],
        "wage_q100": wage_quintiles[5],
        
        "utility_q0": utility_quintiles[0],
        "utility_q20": utility_quintiles[1],
        "utility_q40": utility_quintiles[2],
        "utility_q60": utility_quintiles[3],
        "utility_q80": utility_quintiles[4],
        "utility_q100": utility_quintiles[5],
        
        # Quintile means
        "wealth_q1_mean": wealth_quintile_means[0],
        "wealth_q2_mean": wealth_quintile_means[1],
        "wealth_q3_mean": wealth_quintile_means[2],
        "wealth_q4_mean": wealth_quintile_means[3],
        "wealth_q5_mean": wealth_quintile_means[4],
        
        "wage_q1_mean": wage_quintile_means[0],
        "wage_q2_mean": wage_quintile_means[1],
        "wage_q3_mean": wage_quintile_means[2],
        "wage_q4_mean": wage_quintile_means[3],
        "wage_q5_mean": wage_quintile_means[4],
        
        "utility_q1_mean": utility_quintile_means[0],
        "utility_q2_mean": utility_quintile_means[1],
        "utility_q3_mean": utility_quintile_means[2],
        "utility_q4_mean": utility_quintile_means[3],
        "utility_q5_mean": utility_quintile_means[4],
        
        # Additional ratios
        "debt_to_savings": total_loans / total_savings if total_savings > 0 else float('inf'),
        "employment_rate": (total_agents - singleton_count) / total_agents,
        
        # Quintile ratios
        "wealth_q5_to_q1": wealth_quintile_means[4] / wealth_quintile_means[0] if wealth_quintile_means[0] != 0 else float('inf'),
        "wage_q5_to_q1": wage_quintile_means[4] / wage_quintile_means[0] if wage_quintile_means[0] != 0 else float('inf'),
        "utility_q5_to_q1": utility_quintile_means[4] / utility_quintile_means[0] if utility_quintile_means[0] != 0 else float('inf')
    }
    
    return [census_data]