import networkx as nx

G = nx.read_gml("../data/N600t500r20lendingrate3.gml")
G = nx.DiGraph(G)


max_employees = max(dict(G.in_degree()).values())
print(f"Maximum number of employees (in_degree): {max_employees}")

max_out_degree = max(dict(G.out_degree()).values())
print(f"Maximum number of employers (out_degree): {max_out_degree}")

max_savings = max(nx.get_node_attributes(G, 'savings').values())
print(f"Maximum savings: {max_savings}")

max_loan = max(nx.get_node_attributes(G, 'loan').values())
print(f"Maximum loan: {max_loan}")