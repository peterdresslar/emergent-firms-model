import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import SymLogNorm

def visualize_network(gml_path):
    """
    Visualizes the Emergent Firm Model network from a GML file.
    
    - The main connected subgraph is shown in a large subplot.
    - Singletons (with no edges) are displayed in a row above, sorted by net worth.
    - We use a SymLogNorm to handle very large outliers positively or negatively.
      That way, near-zero values appear near yellow, negative extremes approach red, and positive extremes approach green.
    - Node size in the main subnetwork indicates the number of employees (in_degree).
    """
    # 1) Load the network as directed
    G = nx.read_gml(gml_path, destringizer=float)
    G = nx.DiGraph(G)
    
    # 2) Remove self-loops & identify singletons
    G.remove_edges_from(nx.selfloop_edges(G))
    singletons = [n for n in G.nodes() if G.degree(n) == 0]
    connected = [n for n in G.nodes() if n not in singletons]
    
    # 3) Set up the figure with two subplot areas
    fig = plt.figure(figsize=(20, 24))  # noqa: F841 (this was in the original code)
    network_ax = plt.subplot2grid((5, 1), (1, 0), rowspan=4)  # Main network
    singleton_ax = plt.subplot2grid((5, 1), (0, 0), rowspan=1)  # Singleton row
    
    # 4) Compute net worth and set up a SymLogNorm (0-centered)
    net_worth = {}
    for n in G.nodes():
        savings = float(G.nodes[n].get('savings', 0))
        loan = float(G.nodes[n].get('loan', 0))
        net_worth[n] = savings - loan
    
    nw_values = np.array(list(net_worth.values()))
    low, high = nw_values.min(), nw_values.max()
    abs_max = max(abs(low), abs(high))
    # Use a symmetrical log norm around zero, with a linear threshold near zero
    # so we don't blow up the region around net_worth ≈ 0.
    # You can tweak linthresh to control how "wide" the linear region is.
    norm = SymLogNorm(
        linthresh=1,
        linscale=1.0,
        vmin=-abs_max,
        vmax=abs_max,
        base=10
    )
    
    # Colormap to use
    cmap = plt.cm.RdYlGn
    
    # 5) Main network subgraph
    H = G.subgraph(connected)
    pos_main = nx.kamada_kawai_layout(H)
    
    # Node sizes based on in_degree
    in_degs = H.in_degree()
    node_sizes_main = [100 + (in_degs[n] * 200) for n in H.nodes()]
    
    # Colors for the main network nodes
    node_colors_main = [cmap(norm(net_worth[n])) for n in H.nodes()]
    
    # Draw main network
    nx.draw_networkx_nodes(
        H, pos_main,
        nodelist=list(H.nodes()),
        node_size=node_sizes_main,
        node_color=node_colors_main,
        alpha=0.7,
        ax=network_ax
    )
    nx.draw_networkx_edges(
        H, pos_main,
        edge_color='gray',
        alpha=0.2,
        arrows=True,
        arrowsize=10,
        width=0.5,
        ax=network_ax
    )
    
    # 6) Singletons in a row, sorted by net worth
    if singletons:
        sorted_singletons = sorted(singletons, key=lambda x: net_worth[x])
        num_singletons = len(sorted_singletons)
        
        # X-coordinates for singletons
        if num_singletons > 1:
            x_coords = np.linspace(0, 1, num_singletons)
        else:
            x_coords = [0.5]
        
        pos_singletons = {n: (x, 0.5) for n, x in zip(sorted_singletons, x_coords)}
        
        # Colors for singletons using the SAME shared norm
        singleton_colors = [cmap(norm(net_worth[n])) for n in sorted_singletons]
        
        nx.draw_networkx_nodes(
            G, pos_singletons,
            nodelist=sorted_singletons,
            node_size=50,  # smaller nodes
            node_color=singleton_colors,
            alpha=0.7,
            ax=singleton_ax
        )
        
    # 7) Shared colorbar
    # We'll base this on the same norm so that singletons and connected subgraph use the same scale
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])  # no data needed, we just want the color scale
    cbar = plt.colorbar(sm, ax=network_ax)
    cbar.set_label("Net Worth (Savings - Loans) [SymLogNorm]")
    
    # 8) Titles
    network_ax.set_title(
        "Connected Firms and Workers\n"
        "Node size: # of employees (in_degree)\n"
        "Color: SymLogNorm of net worth (Red=debt, Green=savings, 0=yellow)\n"
        "Edges: worker → employer (directed)"
    )
    singleton_ax.set_title("Self-employed Agents (arranged by net worth from left to right)")
    
    # 9) Hide axis lines
    network_ax.axis("off")
    singleton_ax.axis("off")
    singleton_ax.margins(0.05, 0.00)
    
    # 10) Save
    outpath = gml_path.replace(".gml", "_viz.png")
    plt.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    gml_path = "../data/N600t500r20lendingrate3.gml"
    visualize_network(gml_path)