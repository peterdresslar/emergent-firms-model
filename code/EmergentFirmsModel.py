# coding: utf-8

######################################################################################################################
# Emergent Firm Model
# May 20, 2018
#J M Applegate
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
import itertools 
import math
import pandas
from scipy.optimize import minimize_scalar
from scipy.stats import truncnorm

######################################################################################################################
# model parameter settings
# change these at will
######################################################################################################################

# csv file name
directory = './'
experiment = 'N600t500r20lendingrate3' # example experiment name

# number of model time steps
tmax = 500

# mininmum and maximum degree of social network
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

# lending rate
lendingrate = .03

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
    O = (a * e_star + b * e_star**beta)
    return (e_star, U, O)

######################################################################################################################
# decision functions
######################################################################################################################
def decide(i, agents, F, S, move, startup, lending):
    firm = agents[i]['firm']
    wage = agents[i]['wage']
    savings = agents[i]['savings']
    loan = agents[i]['loan']
    U_single = agents[i]['U_self']
    e_single = agents[i]['e_self']
    
    A = list(nx.node_connected_component(F, i))
    A.remove(i) #other current firm members
    
    e_other, U_other, firm_other = other_utility(i, agents, F, S, A)
    
    if not A: #singleton firm
        cost = wage * move
        if U_other > U_single:
            if savings >= cost: 
                e_star, firm = e_other, firm_other 
                agents[i]['savings'] += -1 * cost
                agents[i]['move'] = 1
            elif lending and loan == 0:
                e_star, firm = e_other, firm_other
                agents[i]['loan'] = cost - savings
                agents[i]['savings'] = 0
                agents[i]['move'] = 1
                agents[i]['borrow'] = 1
            else: 
                e_star = e_single
                agents[i]['thwart'] = 1
        else: 
            e_star = e_single
                
    else: 
        e_current, U_current = current_utility(i, agents, A)
        all_U = [U_current, U_other, U_single]
    
        if max(all_U) == U_single:
            cost = startup * wage
            if savings >= cost: 
                e_star, firm = e_single, i
                agents[i]['savings'] += -1 * cost
                agents[i]['startup'] = 1
            elif lending and loan == 0:
                e_star, firm = e_single, i
                agents[i]['loan'] = cost - savings
                agents[i]['savings'] = 0
                agents[i]['startup'] = 1
                agents[i]['borrow'] = 1
            else: 
                e_star = e_current
                agents[i]['thwart'] = 1
        elif max(all_U) == U_other: 
            cost = move * wage
            if savings >= cost: 
                e_star, firm = e_other, firm_other 
                agents[i]['savings'] += -1 * cost
                agents[i]['move'] = 1
            elif lending and loan == 0:
                e_star, firm = e_other, firm_other 
                agents[i]['loan'] = cost - savings
                agents[i]['savings'] = 0
                agents[i]['move'] = 1
                agents[i]['borrow'] = 1
            else: 
                e_star = e_current
                agents[i]['thwart'] = 1
        else: 
            e_star = e_current 
    
    return(e_star, firm)

def other_utility(i, agents, F, S, A):
    B = list(S.neighbors(i)) # Network is created with at least two links per node.
    C = [a for a in B if a not in A]
    U, e_star, firm, e_trial, U_trial = 0, 0, 0, 0, 0
    for j in C:
        trial = agents[j]['firm']
        D = list(nx.node_connected_component(F, j)) # should be at least one, self
        n = len(D)
        E_o = 0
        for k in D: E_o += agents[k]['e_star']
        e_trial, U_trial = optimize_e(agents[trial]['a'], agents[trial]['b'], agents[trial]['beta'], 
                                      agents[i]['omega'], 
                                      agents[i]['theta'], E_o, n + 1)
        if U_trial > U: e_star, U, firm = e_trial, U_trial, trial
    return (e_star, U, firm) 

def current_utility(i, agents, A): # A is other employees
    e_star, U, E_o = 0, 0, 0
    n = len(A)
    for j in A: E_o += agents[j]['e_star'] 
    e_star, U = optimize_e(agents[i]['a'], agents[i]['b'], agents[i]['beta'], agents[i]['omega'], 
                           agents[i]['theta'], E_o, n + 1)
    return (e_star, U)

def optimize_e(a, b, beta, w, theta, E_o, n):
    f = lambda e_star: -1 * ((a * (e_star + E_o) + b * (e_star + E_o) ** beta)
                             / n) ** theta * (w - e_star) ** (1 - theta)
    res = minimize_scalar(f, bounds=(0, 1), method='bounded')
    return(res.x, -res.fun) # returns estar and maximized utility

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
# function containing main body of code 
######################################################################################################################

def action(parameters, agentHistory):
    
    N, churn, cost, multiplier, savingrate, sigma, lending, lendingrate = parameters
    move = cost
    startup = multiplier * cost
    
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
    for t in range(tmax):
        for i in agents: agents[i].update({'go': 0, 'borrow': 0, 'startup': 0, 'move': 0, 'thwart': 0})
        sequence = random.sample(range(N), k=N)
        for i in random.sample(range(N), k=N):
            if random.random() > churn: continue
            agents[i]['go'] = 1
            firm = agents[i]['firm']
            agents[i]['e_star'], new_firm = decide(i, agents, F, S, move, startup, lending)
            if new_firm != firm: 
                A = nx.node_connected_component(F, i)
                if firm == i and len(A) > 1: F = change_ownership(F, i, A, agents)
                F.add_edge(i, new_firm)
                if F.has_edge(i, firm): F.remove_edge(i, firm)
                agents[i]['firm'] = new_firm
            F.nodes[i]['savings'] = numpy.float64(agents[i]['savings'])
            F.nodes[i]['wage'] = numpy.float64(agents[i]['wage'])
            F.nodes[i]['loan'] = numpy.float64(agents[i]['loan'])
        distribute_output(agents, F)
        if lending: pay_loans(N, agents, lendingrate)
        params = parameters + [t]
        agentHistory[loc:loc+N,0:9] = numpy.tile(params,(N, 1))
        agentHistory[loc:loc+N,9:] = numpy.array([list(v.values()) for v in agents.values()])
        loc += N
        
    return(F, agentHistory)

######################################################################################################################
# experiment wrapper, set up this way to facilitate multi-run modifications
######################################################################################################################

parameters = [N, churn, cost, multiplier, savingrate, sigma, lending, lendingrate]
param_names = ['N', 'churn', 'cost', 'multiplier', 'savingrate', 'sigma', 'lending', 'lendingrate', 't']
rows = N * tmax
agentHistory = numpy.empty((rows, 30)) # parameter string with time + 21 agent attributes

F, agentHistory = action(parameters, agentHistory)

column_names = param_names + ['id', 'omega', 'theta', 'links', 'component', 'a', 'b', 'beta', 'rate', 'U_self', 
                              'e_self', 'e_star',
                              'firm', 'wage', 'savings', 'loan', 'borrow', 'startup', 'move', 'thwart', 'go']
agentHistoryDF = pandas.DataFrame(agentHistory, columns = column_names)
agentHistoryDF.to_csv(directory + experiment + '.csv', index=False)
nx.write_gml(F, directory + experiment + '.gml')
