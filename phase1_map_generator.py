import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

def generate_city_graph():
    # Coordinates for Walchand College of Engineering area
    latitude = 16.8441
    longitude = 74.6015
    center_point = (latitude, longitude)
    radius_meters = 2000  # 2km radius around campus

    print("Downloading street network... This might take a few seconds.")
    
    # Download the network strictly for driving (ignores walking paths)
    G = ox.graph_from_point(center_point, dist=radius_meters, network_type='drive')

    # Plot the graph to visually confirm it worked
    print("Generating visual map...")
    fig, ax = ox.plot_graph(
        G, 
        show=False, 
        close=False, 
        edge_color='#999999', 
        edge_linewidth=1, 
        node_size=5,
        node_color='red'
    )
    plt.title("Map Area (2km radius)", fontsize=15)
    plt.show()

    # Save the graph locally so we don't have to download it every time we test Phase 2
    filepath = "campus_road_network.graphml"
    ox.save_graphml(G, filepath)
    print(f"Graph successfully saved as {filepath}")
    
    return G

if __name__ == "__main__":
    # Run the function
    road_graph = generate_city_graph()
    
    # Print some basic stats for the judges
    print(f"Total Intersections (Nodes): {len(road_graph.nodes)}")
    print(f"Total Roads (Edges): {len(road_graph.edges)}")