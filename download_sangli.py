import osmnx as ox

def download_sangli():
    # Center of Sangli covering Vishrambag and core arteries
    sangli_center = (16.8524, 74.5815)
    radius_meters = 5000  # 5km radius

    print("Downloading full Sangli road network... please wait 15-30 seconds.")
    G = ox.graph_from_point(sangli_center, dist=radius_meters, network_type='drive')
    
    filepath = "sangli_city_network.graphml"
    ox.save_graphml(G, filepath)
    print(f"✅ Success! Saved {len(G.nodes)} intersections and {len(G.edges)} roads to {filepath}")

if __name__ == "__main__":
    download_sangli()