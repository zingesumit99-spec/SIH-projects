import networkx as nx
import osmnx as ox
import random
import matplotlib.pyplot as plt

def generate_dummy_traffic(graph_path, num_cars=50):
    # 1. Load the map we saved in Phase 1
    print("Loading road network...")
    try:
        G = ox.load_graphml(graph_path)
    except FileNotFoundError:
        print(f"Error: Could not find {graph_path}. Did you run Phase 1?")
        return

    # 2. Get a list of all possible intersections (nodes)
    nodes = list(G.nodes())
    
    routes = []
    print(f"Generating {num_cars} random trips...")
    
    # 3. Create random Origin-Destination pairs
    for i in range(num_cars):
        origin = random.choice(nodes)
        destination = random.choice(nodes)
        
        # Make sure origin and destination aren't the same
        while origin == destination:
            destination = random.choice(nodes)
            
        try:
            # 4. Calculate the shortest path (Standard Routing)
            # We use 'length' as the weight to find the shortest physical distance
            route = nx.shortest_path(G, origin, destination, weight='length')
            routes.append(route)
        except nx.NetworkXNoPath:
            # Sometimes a random node is disconnected (like a dead end or gated area)
            # We just skip it if there's no path
            pass 

    print(f"Successfully generated {len(routes)} valid routes.")
    
    # 5. Plot the routes on the map (Still using matplotlib for debugging)
    fig, ax = ox.plot_graph_routes(
        G, 
        routes, 
        route_colors='cyan', 
        route_linewidth=2, 
        node_size=0, 
        edge_color='#333333', 
        bgcolor='black'
    )
    
    return routes

if __name__ == "__main__":
    filepath = "campus_road_network.graphml"
    generated_routes = generate_dummy_traffic(filepath, num_cars=50)