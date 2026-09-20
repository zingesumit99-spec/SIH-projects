import networkx as nx
import osmnx as ox
import random
import matplotlib.pyplot as plt
from itertools import islice

def k_shortest_paths(G, source, target, k, weight='length'):
    """Finds the top 'k' shortest paths."""
    try:
        return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))
    except nx.NetworkXNoPath:
        return []

def simulate_smart_routing(graph_path, num_cars=100):
    print("Loading road network for Smart Routing Simulation...")
    try:
        G = ox.load_graphml(graph_path)
    except FileNotFoundError:
        print(f"Error: Could not find {graph_path}.")
        return

    # Create a simplified version of the graph strictly for the math algorithm
    G_simple = nx.DiGraph(G)

    nodes = list(G.nodes())
    standard_routes = []
    smart_routes = []
    
    print(f"Routing {num_cars} cars with Smart Distribution...")
    
    for i in range(num_cars):
        origin = random.choice(nodes)
        destination = random.choice(nodes)
        
        while origin == destination:
            destination = random.choice(nodes)
            
        try:
            # Standard Route (Herding)
            # Use the original graph for standard routing
            standard_route = nx.shortest_path(G, origin, destination, weight='length')
            standard_routes.append(standard_route)
        except nx.NetworkXNoPath:
            continue
            
        # Calculate Smart Routes using the simplified graph (G_simple)
        # THIS IS THE LINE THAT FIXED THE ERROR
        alt_paths = k_shortest_paths(G_simple, origin, destination, k=3, weight='length')
        
        if alt_paths:
            # Probabilistic Distribution
            rand_val = random.random()
            
            if rand_val < 0.6 and len(alt_paths) >= 1:
                chosen_path = alt_paths[0]
            elif rand_val < 0.9 and len(alt_paths) >= 2:
                chosen_path = alt_paths[1]
            elif len(alt_paths) >= 3:
                chosen_path = alt_paths[2]
            else:
                chosen_path = alt_paths[0] 
                
            smart_routes.append(chosen_path)

    print("Generating visual comparison...")
    fig, axes = plt.subplots(1, 2, figsize=(15, 8))
    
    # Plot Standard (Herding)
    axes[0].set_title("Standard Routing (Herding Effect)", fontsize=14, color='white')
    axes[0].set_facecolor('black')
    ox.plot_graph_routes(
        G, standard_routes, route_colors='red', route_linewidth=2, 
        node_size=0, edge_color='#333333', ax=axes[0], show=False
    )
    
    # Plot Smart (Distributed)
    axes[1].set_title("Smart Probabilistic Routing (Your Solution)", fontsize=14, color='white')
    axes[1].set_facecolor('black')
    ox.plot_graph_routes(
        G, smart_routes, route_colors='cyan', route_linewidth=2, 
        node_size=0, edge_color='#333333', ax=axes[1], show=False
    )
    
    fig.patch.set_facecolor('black')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    filepath = "campus_road_network.graphml"
    simulate_smart_routing(filepath, num_cars=100)