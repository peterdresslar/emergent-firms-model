# coding: utf-8

# comment from PDD:
# disable ruff E701 for this file, keeping style consistent with original code
# ruff: noqa: E701

######################################################################################################################
# Emergent Firm Model
# May 20, 2018
# J M Applegate
######################################################################################################################
# This code will run a single simulation of the Emergent Firm Model with the parameters specified.
# Firm data for each timestep is saved in a .csv file, and a network graph representing final economy structure
# is saved as a .gml file. The network also contains savings, wages and loan node attributes.
# Refer to ODD for 
######################################################################################################################

######################################################################################################################
# import required packages
######################################################################################################################

import numpy
import random
import networkx as nx
import pandas
from scipy.optimize import minimize_scalar
from scipy.stats import truncnorm
import json
import os
import numpy as np
from datetime import datetime
######################################################################################################################
# model parameter settings
# change these at will
######################################################################################################################

# csv file name
# PDD: new path variable -- the directory where the data will be saved
path = '../data/'

# experiment name controls file naming. set this to a value if you want to simply run from here.
experiment = 'N600t500lendingrate3'

# number of model time steps
tmax = 500

# mininmum and maximum degree of social network
# NOTE: right now these are somewhat hard-wired into the model--they do not get passed as parameters
mindegree = 2
maxdegree = 6

# number of agents
# (this can be set higher, but beware increasing storage requirements)
N = 600

# agent activation rate
churn = .01

# job change cost and multiplier for startup
cost = 1
multiplier = 2

# mean saving rate
# (if sigma = 0 all agent have same rate)
savingrate = .03
sigma = .01

# toggles lending on (1) or off (0)
lending = 1

### new parameters for v1.0.1
# lending rate (previous)
# lendingrate = .03

# loan guidelines:
# debt_awareness: whether agents consider loan repayability when making decisions.
# Set to False to simulate behavior from the original model.
debt_awareness = True 

# loan_repayment_lookahead: This lookahead behaves like a loan term. 
# Agent uses this to determine if they can repay a loan in the specified time.
# Higher values should essentially equate to higher risk tolerance, as an external change
# during repayment could cause the agent to be unable to repay.
loan_repayment_lookahead = 12

# lending rate (previous)
# lendingrate = .03
# We set the lending rate to a more likely "monthly" rate, as the default churn setting 
# seems analogous to a monthly churn rate.
lendingrate = .03  # Monthly compound interest rate (3% APR)

# loan_cap: Maximum total loan amount, set somewhat arbitrarily to tmax
# avoid runaway loans which could distort the population metrics
# a zero value will remove the cap
# loan_cap = tmax 



######################################################################################################################
# function definitions
######################################################################################################################
# instantiation functions
######################################################################################################################
def create_agents(N, savingrate, sigma, X):
    agents = {}
    for i in range(N):
        agents[i] = {'id': i, 'omega': 1.0, 'links': 0, 'component': 0, 
                     'theta': random.uniform(0, 1),
                     'a': random.uniform(0, 1/2), 'b': random.uniform(3/4, 5/4), 'beta': random.uniform(1, 3/2), 
                     'rate': savingrate if sigma == 0 else X.rvs(1)[0], 'U_self': 0.0, 'e_self': 0.0, 'e_star': 0.0, 
                     'firm': i, 'wage': 0.0, 'savings': 0.0, 'loan': 0.0, 'borrow': 0, 'startup': 0, 'move': 0, 
                     'thwart': 0, 'go': 0} 
        # 21 agent attributes
    return agents

def social_network(N, mindegree, maxdegree):
    while True:
        degrees = [random.randint(mindegree, maxdegree) for _ in range(N)] 
        if nx.is_graphical(degrees): break
    G = nx.random_degree_sequence_graph(degrees)

    components = list(nx.connected_components(G))
    return(G, components)

def singleton_utility(agent):
    e_star, U = 0, 0
    a, b, beta = agent['a'], agent['b'], agent['beta']
    e_star, U = optimize_e(agent['a'], agent['b'], agent['beta'], agent['omega'], agent['theta'], 0, 1)
    O = (a * e_star + b * e_star**beta) # noqa keep original code variable name
    return (e_star, U, O)

######################################################################################################################
# decision functions
######################################################################################################################
def decide(i, agents, F, S, move_cost, startup_cost, lending, lendingrate, debt_awareness, loan_repayment_lookahead):
    firm = agents[i]['firm']
    wage = agents[i]['wage']
    savings = agents[i]['savings']
    loan = agents[i]['loan']
    U_single = agents[i]['U_self']
    e_single = agents[i]['e_self']
    
    A = list(nx.node_connected_component(F, i))
    if i in A: A.remove(i) #other current firm members
    
    e_other, U_other, firm_other, other_log_entry = other_utility(i, agents, F, S, A, lendingrate, debt_awareness, loan_repayment_lookahead)
    
    log_entry = {
        "agent_id": i,
        "time": None,  # will be filled in action()
        "decision_type": None,
        "old_firm": firm,
        "old_wage": wage,
        "old_savings": savings,
        "old_loan": loan,
        "U_single": U_single,
        "e_single": e_single,
        "U_other": U_other,
        "e_other": e_other,
        "firm_other": firm_other,
        "new_firm": None,
        "new_e_star": None,
        "cost": None,
        "sampled_inputs": {},
        "narrative": "",
        "other_utility_log": other_log_entry,
        "optimize_e_verification": None
    }
    
    # Verify optimize_e
    verification_results = verify_optimize_e(agents, F, i)
    log_entry["optimize_e_verification"] = verification_results
    log_entry["narrative"] += verification_results["narrative"]
    
    if not A: #singleton firm
        log_entry["decision_type"] = "singleton_firm"
        cost = wage * move_cost
        log_entry["cost"] = cost
        log_entry["sampled_inputs"]["move_cost"] = move_cost
        if U_other > U_single:
            log_entry["narrative"] = f"Singleton agent {i} considers moving to firm {firm_other} because U_other ({U_other:.4f}) > U_single ({U_single:.4f})."
            if savings >= cost:
                e_star, firm = e_other, firm_other
                agents[i]['savings'] += -1 * cost
                agents[i]['move'] = 1
                log_entry["narrative"] += f" Agent {i} has sufficient savings ({savings:.4f}) to cover move cost ({cost:.4f})."
                log_entry["new_firm"] = firm
                log_entry["new_e_star"] = e_star
            elif lending and loan == 0:
                e_star, firm = e_other, firm_other
                agents[i]['loan'] = cost - savings
                agents[i]['savings'] = 0
                agents[i]['move'] = 1
                agents[i]['borrow'] = 1
                log_entry["narrative"] += f" Agent {i} borrows to cover move cost ({cost:.4f}) because savings ({savings:.4f}) are insufficient."
                log_entry["new_firm"] = firm
                log_entry["new_e_star"] = e_star
            else:
                e_star = e_single
                agents[i]['thwart'] = 1
                log_entry["narrative"] += f" Agent {i} cannot afford to move and has no loan, so move is thwarted."
                log_entry["new_firm"] = firm
                log_entry["new_e_star"] = e_star
        else:
            e_star = e_single
            log_entry["narrative"] = f"Singleton agent {i} remains in place because U_other ({U_other:.4f}) <= U_single ({U_single:.4f})."
            log_entry["new_firm"] = firm
            log_entry["new_e_star"] = e_star
                
    else:
        log_entry["decision_type"] = "non_singleton_firm"
        e_current, U_current = current_utility(i, agents, A)
        all_U = [U_current, U_other, U_single]
        log_entry["U_current"] = U_current
        log_entry["e_current"] = e_current
        log_entry["sampled_inputs"]["all_U"] = all_U
    
        if max(all_U) == U_single:
            log_entry["narrative"] = f"Agent {i} considers starting a new firm because U_single ({U_single:.4f}) is the highest utility."
            cost = startup_cost * wage
            log_entry["cost"] = cost
            log_entry["sampled_inputs"]["startup_cost"] = startup_cost
            if savings >= cost:
                e_star, firm = e_single, i
                agents[i]['savings'] += -1 * cost
                agents[i]['startup'] = 1
                log_entry["narrative"] += f" Agent {i} has sufficient savings ({savings:.4f}) to cover startup cost ({cost:.4f})."
                log_entry["new_firm"] = firm
                log_entry["new_e_star"] = e_star
            elif lending and loan == 0:
                e_star, firm = e_single, i
                agents[i]['loan'] = cost - savings
                agents[i]['savings'] = 0
                agents[i]['startup'] = 1
                agents[i]['borrow'] = 1
                log_entry["narrative"] += f" Agent {i} borrows to cover startup cost ({cost:.4f}) because savings ({savings:.4f}) are insufficient."
                log_entry["new_firm"] = firm
                log_entry["new_e_star"] = e_star
            else:
                e_star = e_current
                agents[i]['thwart'] = 1
                log_entry["narrative"] += f" Agent {i} cannot afford to start a firm and has no loan, so startup is thwarted."
                log_entry["new_firm"] = firm
                log_entry["new_e_star"] = e_star
        elif max(all_U) == U_other:
            log_entry["narrative"] = f"Agent {i} considers moving to firm {firm_other} because U_other ({U_other:.4f}) is the highest utility."
            cost = move_cost * wage
            log_entry["cost"] = cost
            log_entry["sampled_inputs"]["move_cost"] = move_cost
            if savings >= cost:
                e_star, firm = e_other, firm_other
                agents[i]['savings'] += -1 * cost
                agents[i]['move'] = 1
                log_entry["narrative"] += f" Agent {i} has sufficient savings ({savings:.4f}) to cover move cost ({cost:.4f})."
                log_entry["new_firm"] = firm
                log_entry["new_e_star"] = e_star
            elif lending and loan == 0:
                e_star, firm = e_other, firm_other
                agents[i]['loan'] = cost - savings
                agents[i]['savings'] = 0
                agents[i]['move'] = 1
                agents[i]['borrow'] = 1
                log_entry["narrative"] += f" Agent {i} borrows to cover move cost ({cost:.4f}) because savings ({savings:.4f}) are insufficient."
                log_entry["new_firm"] = firm
                log_entry["new_e_star"] = e_star
            else:
                e_star = e_current
                agents[i]['thwart'] = 1
                log_entry["narrative"] = f" Agent {i} cannot afford to move and has no loan, so move is thwarted."
                log_entry["new_firm"] = firm
                log_entry["new_e_star"] = e_star
        else:
            e_star = e_current
            log_entry["narrative"] = f"Agent {i} remains in place because U_current ({U_current:.4f}) is the highest utility."
            log_entry["new_firm"] = firm
            log_entry["new_e_star"] = e_star
    
    return(e_star, firm, log_entry)

def other_utility(i, agents, F, S, A, lendingrate, debt_awareness, loan_repayment_lookahead):
    B = list(S.neighbors(i)) # Network is created with at least two links per node.
    C = [a for a in B if a not in A]
    U, e_star, firm, e_trial, U_trial = 0, 0, 0, 0, 0
    
    log_entry = {
        "agent_id": i,
        "function": "other_utility",
        "evaluated_firms": [],
        "best_firm": None,
        "best_e_star": None,
        "best_U": None,
        "narrative": ""
    }
    
    for j in C:
        trial = agents[j]['firm']

        # before we start, we need to check if the agent can repay the loan with the expected wage
        # from the firm they are considering moving to. This way the agent can choose to move to
        # the firm that maximizes their utility out of the options they *can afford*.

        # Check the flag for debt_awareness first! If debt_awareness is True, the model skips the evaluation.
        # Note this flag is model-wide, not per-agent.
        if debt_awareness:
            if can_repay_loan(agents[i], agents[trial]['wage'], agents[i]['loan'], lendingrate, loan_repayment_lookahead):
                log_entry["narrative"] += f"Agent {i} can repay loan at rate {lendingrate} with expected wage from firm {trial}."
            else:
                log_entry["narrative"] += f"Agent {i} cannot repay loan at rate {lendingrate} with expected wage from firm {trial}."
                continue

        D = list(nx.node_connected_component(F, j))
        if j in D:
            D.remove(j)
        n = len(D)
        E_o = 0
        for k in D: E_o += agents[k]['e_star']
        e_trial, U_trial = optimize_e(agents[trial]['a'], agents[trial]['b'], agents[trial]['beta'], 
                                      agents[i]['omega'], 
                                      agents[i]['theta'], E_o, n + 1)
        log_entry["evaluated_firms"].append({
            "firm_id": trial,
            "e_trial": e_trial,
            "U_trial": U_trial
        })
        if U_trial > U: 
            e_star, U, firm = e_trial, U_trial, trial
            log_entry["best_firm"] = firm
            log_entry["best_e_star"] = e_star
            log_entry["best_U"] = U
            log_entry["narrative"] = f"Agent {i} found firm {firm} to have the highest utility ({U:.4f}) among neighbors."
    
    if not C:
        log_entry["narrative"] = f"Agent {i} has no neighbors to evaluate."
    
    return (e_star, U, firm, log_entry)

def current_utility(i, agents, A): # A is other employees
    e_star, U, E_o = 0, 0, 0
    n = len(A)
    for j in A: E_o += agents[j]['e_star'] 
    e_star, U = optimize_e(agents[i]['a'], agents[i]['b'], agents[i]['beta'], agents[i]['omega'], 
                           agents[i]['theta'], E_o, n + 1)
    return (e_star, U)

def optimize_e(a, b, beta, w, theta, E_o, n):
    # original code:
    # f = lambda e_star: -1 * ((a * (e_star + E_o) + b * (e_star + E_o) ** beta)
    #                          / n) ** theta * (w - e_star) ** (1 - theta)
    # rewritten for my understanding:
    def f(e_star):
        return -1 * ((a * (e_star + E_o) + b * (e_star + E_o) ** beta) / n) ** theta * (w - e_star) ** (1 - theta)
    
    res = minimize_scalar(f, bounds=(0, 1), method='bounded')
    return(res.x, -res.fun) # returns estar and maximized utility

def verify_optimize_e(agents, F, i):
    # Get agent and firm data
    agent = agents[i]
    firm_id = agent['firm']
    A = list(nx.node_connected_component(F, i))
    if i in A: A.remove(i)
    n = len(A) + 1
    E_o = 0
    for k in A: E_o += agents[k]['e_star']
    a, b, beta = agents[firm_id]['a'], agents[firm_id]['b'], agents[firm_id]['beta']
    w, theta = agent['omega'], agent['theta']

    # Calculate expected utility for a range of e_star values
    e_stars = np.linspace(0, 1, 100)
    utilities = []
    for e_star in e_stars:
        output_share = (a * (e_star + E_o) + b * (e_star + E_o) ** beta) / n
        utility = output_share ** theta * (w - e_star) ** (1 - theta)
        utilities.append(utility)
    
    # Find the e_star that maximizes utility
    max_utility_index = np.argmax(utilities)
    expected_e_star = e_stars[max_utility_index]
    expected_max_utility = utilities[max_utility_index]

    # Run optimize_e
    optimized_e_star, optimized_max_utility = optimize_e(a, b, beta, w, theta, E_o, n)

    # Compare results
    narrative = f"Verification for agent {i}, firm {firm_id}: "
    if abs(expected_e_star - optimized_e_star) < 0.001:
        narrative += "optimize_e is working correctly. "
    else:
        narrative += "optimize_e is NOT working correctly. "
    narrative += f"Expected e_star: {expected_e_star:.4f}, Optimized e_star: {optimized_e_star:.4f}. "
    
    return {
        "expected_e_star": expected_e_star,
        "expected_max_utility": expected_max_utility,
        "optimized_e_star": optimized_e_star,
        "optimized_max_utility": optimized_max_utility,
        "narrative": narrative
    }

def can_repay_loan(agent, expected_wage, cost, lendingrate, loan_repayment_lookahead):
    return agent['savings'] + expected_wage * loan_repayment_lookahead >= cost * (1 + lendingrate) ** loan_repayment_lookahead

######################################################################################################################
# utility functions
######################################################################################################################

def change_ownership(F, i, A, agents):
    A_list = list(A)
    A_list.remove(i)
    new_owner = random.sample(A_list, 1)[0]
    F.remove_edge(new_owner, i)
    agents[new_owner]['firm'] = new_owner
    A_list.remove(new_owner)
    if A_list: 
        for j in A_list:
            agents[j]['firm'] = new_owner
            F.add_edge(j, new_owner)
            F.remove_edge(j, i)
    return(F)

def distribute_output(agents, F):
    for g in nx.connected_components(F):
        h = list(g)
        n = len(h)
        firm = agents[h[0]]['firm']
        a = agents[firm]['a']
        b = agents[firm]['b']
        beta = agents[firm]['beta']
        E = 0
        for j in g: E += agents[j]['e_star']
        O_total = (a * E + b * E **beta)
        share = O_total / n
        for j in g: 
            agents[j]['wage'] = share
            agents[j]['savings'] += share * agents[j]['rate']

def pay_loans(N, agents, lendingrate):
    for i in range(N):
        loan = agents[i]['loan']
        if loan != 0: 
            loan = loan * (1 + lendingrate) - agents[i]['savings']
            if loan < 0: 
                agents[i]['savings'] = abs(loan)
                agents[i]['loan'] = 0
            else:
                agents[i]['savings'] = 0
                agents[i]['loan'] = loan

######################################################################################################################
# census functions
######################################################################################################################
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
        utilities.append(current_utility(i, agents, list(nx.node_connected_component(F, i)))[1] if i in F else agent['U_self'])
        
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

######################################################################################################################
# action is the main function that operates the model
# function containing main body of code 
######################################################################################################################

def action(parameters, tmax, path, experiment):
    print("Model called with parameters: ", parameters, "\n tmax: ", tmax, "\n path: ", path, "\n experiment: ", experiment)
    
    # Create experiment-specific directory with a date-time stamp (use an underscore between experiment and datetimestamp)
    experiment_path = os.path.join(path, experiment + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    os.makedirs(experiment_path, exist_ok=True)
    
    # set up column names
    param_names = ['N', 'churn', 'cost', 'multiplier', 'savingrate', 'sigma', 'lending', 'lendingrate', 'debt_awareness', 'loan_repayment_lookahead', 't']
    param_count = len(param_names)
    
    column_names = param_names + ['id', 'omega', 'theta', 'links', 'component', 'a', 'b', 'beta', 'rate', 'U_self', 
                              'e_self', 'e_star',
                              'firm', 'wage', 'savings', 'loan', 'borrow', 'startup', 'move', 'thwart', 'go']
    column_count = len(column_names)

    # unpack parameters
    N, churn, cost, multiplier, savingrate, sigma, lending, lendingrate, debt_awareness, loan_repayment_lookahead = parameters
    
    # initialize agentHistory
    rows = N * tmax  # total rows = one row per agent, per time step
    agentHistory = numpy.empty((rows, column_count)) # parameter string with time + 21 agent attributes.

    # model setup (original model code)
    move_rate = cost
    startup_rate = multiplier * cost
    X = 0 if sigma == 0 else truncnorm((0 - savingrate) / sigma, (1 - savingrate) / sigma, loc=savingrate, scale=sigma)
    
    agents = create_agents(N, savingrate, sigma, X)
    for i in agents:
        agents[i]['e_self'], agents[i]['U_self'], agents[i]['wage'] = singleton_utility(agents[i])
        agents[i]['e_star'] = agents[i]['e_self']
    S, components = social_network(N, mindegree, maxdegree)
    for i in agents:
        agents[i]['links'] = S.degree(i)
        agents[i]['component'] = [idx for idx, x in enumerate(components) if i in x][0]
    F = nx.empty_graph(N)

    loc = 0
    events_log = [] # Initialize the events log at the start of action
    firms_history = [] # Initialize the firms history log
    census_history = [] # Initialize the economic census log
    for t in range(tmax):
        for i in agents: agents[i].update({'go': 0, 'borrow': 0, 'startup': 0, 'move': 0, 'thwart': 0})
        for i in random.sample(range(N), k=N):
            if random.random() > churn: continue
            agents[i]['go'] = 1
            firm = agents[i]['firm']
            # Unpack all three return values from decide
            agents[i]['e_star'], new_firm, log_entry = decide(i, agents, F, S, move_rate, startup_rate, lending, lendingrate, debt_awareness, loan_repayment_lookahead)
            log_entry["time"] = t  # Add the time to the log entry
            if new_firm != firm: 
                A = nx.node_connected_component(F, i)
                if firm == i and len(A) > 1: F = change_ownership(F, i, A, agents)
                F.add_edge(i, new_firm)
                if F.has_edge(i, firm): F.remove_edge(i, firm)
                agents[i]['firm'] = new_firm
            F.nodes[i]['savings'] = numpy.float64(agents[i]['savings'])
            F.nodes[i]['wage'] = numpy.float64(agents[i]['wage'])
            F.nodes[i]['loan'] = numpy.float64(agents[i]['loan'])
            
            if log_entry["decision_type"] is not None:
                events_log.append(log_entry)
        distribute_output(agents, F)
        if lending: pay_loans(N, agents, lendingrate)
        params = parameters + [t]
        # use counts instead of indices to avoid errors
        agentHistory[loc:loc+N,0:param_count] = numpy.tile(params,(N, 1))
        agentHistory[loc:loc+N,param_count:] = numpy.array([list(v.values()) for v in agents.values()])
        loc += N
        
        # Generate and store the reports
        firms_history.append(generate_firms_report(agents, F, t))
        census_history.append(generate_economic_census(agents, t, F))
    
    # After the main loop finishes, serialize the events to JSON
    with open(os.path.join(experiment_path, "events.json"), "w") as f:
        json.dump(events_log, f, indent=2)
    
    # Convert the history logs to pandas DataFrames and save them to CSV
    firms_history_df = pandas.concat([pandas.DataFrame(x) for x in firms_history])
    firms_output_file = os.path.join(experiment_path, "firms.csv")
    #overwrite existing file if it exists
    if os.path.exists(firms_output_file):
        os.remove(firms_output_file)
    firms_history_df.to_csv(firms_output_file, index=False, float_format=lambda x: f'{x:.12f}'.rstrip('0').rstrip('.'))
    
    census_history_df = pandas.concat([pandas.DataFrame(x) for x in census_history])
    census_history_df.to_csv(os.path.join(experiment_path, "census.csv"), index=False, float_format=lambda x: f'{x:.12f}'.rstrip('0').rstrip('.'))

    # initialize agentHistoryDF and send it to csv
    agentHistoryDF = pandas.DataFrame(agentHistory, columns = column_names)
    agentHistoryDF.to_csv(os.path.join(experiment_path, 'agents.csv'), index=False, float_format=lambda x: f'{x:.12f}'.rstrip('0').rstrip('.'))

    # Format node attributes before writing GML
    for node in F.nodes():
        for attr in ['savings', 'wage', 'loan']:
            if attr in F.nodes[node]:
                F.nodes[node][attr] = f'{float(F.nodes[node][attr]):.12f}'.rstrip('0').rstrip('.')

    nx.write_gml(F, os.path.join(experiment_path, 'network.gml'))
    
    return(F, agentHistory)

######################################################################################################################
# experiment wrapper, set up this way to facilitate multi-run modifications
######################################################################################################################

if __name__ == "__main__":
    parameters = [
        N,                # 0
        churn,            # 1
        cost,             # 2
        multiplier,       # 3
        savingrate,       # 4
        sigma,            # 5
        lending,          # 6
        lendingrate,      # 7
        # new loan-related parameters
        debt_awareness,   # 8
        loan_repayment_lookahead, # 9
    ]
    F, agentHistory = action(parameters, tmax, path, experiment)