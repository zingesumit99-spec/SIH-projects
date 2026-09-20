import streamlit as st
import networkx as nx
import osmnx as ox
import random
import pandas as pd
import pydeck as pdk
from itertools import islice

st.set_page_config(layout="wide", page_title="Smart Traffic Router")

@st.cache_resource
def load_map():
    G = ox.load_graphml("campus_road_network.graphml")
    G_simple = nx.DiGraph(G)
    return G, G_simple

def k_shortest_paths(G, source, target, k, weight='length'):
    try:
        return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))
    except nx.NetworkXNoPath:
        return []

st.title("🚦 SIH Traffic Rerouting Dashboard")
col1, col2 = st.columns([1, 3])

with col1:
    st.header("Controls")
    num_cars = st.slider("Number of Vehicles", 10, 200, 100)
    routing_type = st.radio("Routing Algorithm", ["Standard (Herding)", "Smart (Probabilistic)"])
    run_btn = st.button("Run Simulation", type="primary")

with col2:
    if run_btn:
        with st.spinner("Calculating routes..."):
            G, G_simple = load_map()
            nodes = list(G.nodes())
            
            # We will store the full path (list of coordinates) for each car
            route_lines = []
            
            for _ in range(num_cars):
                origin = random.choice(nodes)
                dest = random.choice(nodes)
                while origin == dest:
                    dest = random.choice(nodes)
                    
                try:
                    if routing_type == "Standard (Herding)":
                        route = nx.shortest_path(G, origin, dest, weight='length')
                        color = [255, 0, 0, 100] # Red with opacity for overlapping
                    else:
                        alt_paths = k_shortest_paths(G_simple, origin, dest, 3, 'length')
                        if alt_paths:
                            rand_val = random.random()
                            if rand_val < 0.6: route = alt_paths[0]
                            elif rand_val < 0.9 and len(alt_paths) >= 2: route = alt_paths[1]
                            elif len(alt_paths) >= 3: route = alt_paths[2]
                            else: route = alt_paths[0]
                        else:
                            continue
                        color = [0, 255, 255, 100] # Cyan with opacity
                    
                    # Extract the continuous path of coordinates for PyDeck
                    path_coords = [[G.nodes[n]['x'], G.nodes[n]['y']] for n in route]
                    route_lines.append({"path": path_coords, "color": color})
                    
                except nx.NetworkXNoPath:
                    continue
            
            if route_lines:
                df = pd.DataFrame(route_lines)
                
                # Configure the PyDeck Map (Dark Mode, 3D Pitch)
                view_state = pdk.ViewState(
                    latitude=16.8441, 
                    longitude=74.6015, 
                    zoom=14, 
                    pitch=45 # Adds a cool 3D tilt to the map!
                )
                
                # Draw continuous paths (lines) instead of dots
                layer = pdk.Layer(
                    type="PathLayer",
                    data=df,
                    pickable=True,
                    get_color="color",
                    width_scale=20,
                    width_min_pixels=2,
                    get_path="path",
                    get_width=2
                )
                
                r = pdk.Deck(layers=[layer], initial_view_state=view_state, map_style="mapbox://styles/mapbox/dark-v9")
                st.pydeck_chart(r)
                
            else:
                st.error("No valid routes found.")
    else:
        st.info("👈 Adjust the controls and click 'Run Simulation'")