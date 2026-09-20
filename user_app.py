import streamlit as st
import networkx as nx
import osmnx as ox
import pandas as pd
import pydeck as pdk
import random
import time
import math
import base64
from datetime import datetime

st.set_page_config(layout="wide", page_title="Sangli Smart Traffic Navigation")

GRAPH_FILE = "sangli_city_network.graphml"
WCE_LAT = 16.8411
WCE_LON = 74.6015
WCE_RADIUS_KM = 3.0

def calculate_bearing(lon1, lat1, lon2, lat2):
    dLon = math.radians(lon2 - lon1)
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    y = math.sin(dLon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dLon)
    bearing_deg = math.degrees(math.atan2(y, x))
    return (90 - bearing_deg) % 360

def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return r * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

@st.cache_resource
def load_graph():
    try:
        G = ox.load_graphml(GRAPH_FILE)
        for node, data in G.nodes(data=True):
            data["x"], data["y"] = float(data["x"]), float(data["y"])
        return G
    except Exception as e:
        st.error(f"Unable to load {GRAPH_FILE}. Error: {e}")
        return None

# --- REPLACED OPENSTREETMAP SCRAPER WITH EXPLICIT CLEAN LANDMARKS ---
@st.cache_data(ttl=86400)
def load_places():
    data = [
        {"name": "Wanlesswadi", "lat": 16.8650, "lon": 74.6100, "type": "Area"},
        {"name": "College Corner", "lat": 16.8480, "lon": 74.5980, "type": "Junction"},
        {"name": "Pushpraj Chowk", "lat": 16.8522, "lon": 74.5928, "type": "Junction"},
        {"name": "Madhavnagar", "lat": 16.8720, "lon": 74.5940, "type": "Area"},
        {"name": "Ram Mandir Chowk", "lat": 16.8530, "lon": 74.5750, "type": "Junction"},
        {"name": "Walchand College", "lat": WCE_LAT, "lon": WCE_LON, "type": "College"},
        {"name": "Ganpati Mandir", "lat": 16.8490, "lon": 74.5680, "type": "Temple"},
        {"name": "Srushti Chowk", "lat": 16.8390, "lon": 74.6150, "type": "Junction"},
        {"name": "Bharati Vidyapeeth", "lat": 16.8320, "lon": 74.6180, "type": "University"},
        {"name": "Miraj", "lat": 16.8280, "lon": 74.6430, "type": "City"}
    ]
    df = pd.DataFrame(data)
    df["label_tier"] = 1
    return df

@st.cache_data(ttl=15)
def create_live_traffic(_G):
    G, live_time = _G, time.time()
    rng, road_data = random.Random(int(live_time / 15)), []
    for u, v, k, data in G.edges(keys=True, data=True):
        wave = math.sin(live_time / 18 + (u + v) / 1000)
        val = rng.random() + (wave * 0.20)
        if val < 0.58: color, mult, width = [0, 150, 255, 190], 1.0, 3
        elif val < 0.82: color, mult, width = [241, 196, 15, 210], 2.5, 4
        else: color, mult, width = [231, 76, 60, 235], 7.0, 5
        road_data.append({"path": [[float(G.nodes[u]["x"]), float(G.nodes[u]["y"])], [float(G.nodes[v]["x"]), float(G.nodes[v]["y"])]], "color": color, "width": width, "multiplier": mult})
    return road_data

def create_routing_graph(G):
    R = nx.DiGraph()
    random.seed(42)
    for u, v, k, data in G.edges(keys=True, data=True):
        length = float(data.get("length", 100))
        val = random.random()
        mult = 1.0 if val < 0.60 else (2.5 if val < 0.85 else 7.0)
        cost = length * mult
        if not R.has_edge(u, v) or cost < R[u][v]["cost"]:
            R.add_edge(u, v, length=length, cost=cost)
    return R

def nearest_node(G, lat, lon):
    try:
        return ox.distance.nearest_nodes(G, X=lon, Y=lat)
    except ImportError:
        best_node, best_dist = None, None
        for node in G.nodes():
            dist = (float(G.nodes[node]["x"]) - lon) ** 2 + (float(G.nodes[node]["y"]) - lat) ** 2
            if best_dist is None or dist < best_dist:
                best_dist, best_node = dist, node
        return best_node if best_node is not None else (_ for _ in ()).throw(ValueError())

def route_to_coordinates(G, route):
    return [[float(G.nodes[node]["x"]), float(G.nodes[node]["y"])] for node in route]

G = load_graph()
if G is None: st.stop()

traffic_data = create_live_traffic(G)
routing_graph = create_routing_graph(G)
places = load_places()

st.title("📍 Sangli Smart Traffic Navigator")
st.caption("Clean landmark routing • Live traffic updates")

left, right = st.columns([1, 3])

with left:
    st.subheader("Trip Planner")
    st.markdown("🔵 **Blue** → Free Flow\n\n🟡 **Yellow** → Moderate Traffic\n\n🔴 **Red** → Heavy Congestion")
    st.divider()

    place_names = places["name"].tolist()
    default_index = place_names.index("Walchand College") if "Walchand College" in place_names else 0

    origin_name = st.selectbox("📍 Starting Point", place_names, index=default_index)
    destination_name = st.selectbox("🏁 Destination", place_names)

    if st.button("🚗 Find Smart Route", use_container_width=True, type="primary"):
        origin_row = places[places["name"] == origin_name].iloc[0]
        destination_row = places[places["name"] == destination_name].iloc[0]
        origin_node = nearest_node(G, float(origin_row["lat"]), float(origin_row["lon"]))
        destination_node = nearest_node(G, float(destination_row["lat"]), float(destination_row["lon"]))
        try:
            normal_route = nx.shortest_path(routing_graph, origin_node, destination_node, weight="length")
            smart_route = nx.shortest_path(routing_graph, origin_node, destination_node, weight="cost")
            normal_cost = sum(routing_graph[a][b]["cost"] for a, b in zip(normal_route[:-1], normal_route[1:]))
            smart_cost = sum(routing_graph[a][b]["cost"] for a, b in zip(smart_route[:-1], smart_route[1:]))
            st.session_state["normal_route"] = normal_route
            st.session_state["smart_route"] = smart_route
            st.session_state["normal_minutes"] = max(1, int(normal_cost / 50))
            st.session_state["smart_minutes"] = max(1, int(smart_cost / 50))
            st.session_state["origin_name"] = origin_name
            st.session_state["destination_name"] = destination_name
            st.session_state["navigating"] = False
        except nx.NetworkXNoPath:
            st.error("❌ No road connection found between these places.")

    if "smart_route" in st.session_state:
        st.error(f"⚠️ **Normal Route**\nEstimated time: **{st.session_state['normal_minutes']} minutes**")
        st.success(f"🚀 **Smart Traffic Route**\nEstimated time: **{st.session_state['smart_minutes']} minutes**")
        if st.button("▶️ START NAVIGATION", type="primary", use_container_width=True):
            st.session_state["navigating"] = True
            st.rerun()

with right:
    map_placeholder = st.empty()
    traffic_layer = pdk.Layer("PathLayer", data=pd.DataFrame(traffic_data), get_path="path", get_color="color", get_width="width", width_min_pixels=1, pickable=False)
    
    # Clean, uncluttered text layer showing only the requested key landmarks
    label_layer = pdk.Layer(
        "TextLayer",
        data=places,
        get_position=["lon", "lat"],
        get_text="name",
        get_size=13,
        get_color=[255, 255, 255, 255],
        get_alignment_baseline="'center'",
        get_text_anchor="'middle'",
        background=True,
        get_background_color=[0, 0, 0, 180],
        pickable=True
    )
    
    layers = [traffic_layer, label_layer]

    if "smart_route" in st.session_state:
        smart_route = st.session_state["smart_route"]
        route_coordinates = route_to_coordinates(G, smart_route)
        route_layer = pdk.Layer("PathLayer", data=pd.DataFrame([{"path": route_coordinates}]), get_path="path", get_color=[0, 220, 255, 255], get_width=8, width_min_pixels=6, pickable=False)
        layers.append(route_layer)

        endpoint_data = pd.DataFrame([{"lon": route_coordinates[0][0], "lat": route_coordinates[0][1]}, {"lon": route_coordinates[-1][0], "lat": route_coordinates[-1][1]}])
        endpoint_layer = pdk.Layer("ScatterplotLayer", data=endpoint_data, get_position=["lon", "lat"], get_radius=18, radius_min_pixels=10, get_fill_color=[255, 255, 255, 255], get_line_color=[0, 0, 0, 255], get_line_width=3, pickable=False)
        layers.append(endpoint_layer)

        if st.session_state.get("navigating", False):
            arrow_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140" viewBox="0 0 140 140"><circle cx="70" cy="70" r="62" fill="#00D9FF" stroke="white" stroke-width="7"/><path d="M70 12 L120 92 L70 70 L20 92 Z" fill="white" stroke="#004F63" stroke-width="5"/><circle cx="70" cy="70" r="10" fill="#004F63"/></svg>'
            arrow_url = "data:image/svg+xml;base64," + base64.b64encode(arrow_svg.encode("utf-8")).decode("utf-8")

            skip_step = max(1, len(route_coordinates) // 15)
            for i in range(0, len(route_coordinates) - skip_step, skip_step):
                start, end = route_coordinates[i], route_coordinates[i + skip_step]
                direction = calculate_bearing(start[0], start[1], end[0], end[1])
                
                steps = 4
                for step in range(steps):
                    progress = step / steps
                    curr_lon = start[0] + (end[0] - start[0]) * progress
                    curr_lat = start[1] + (end[1] - start[1]) * progress
                    
                    glow_layer = pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{"lon": curr_lon, "lat": curr_lat}]), get_position=["lon", "lat"], get_radius=30, radius_min_pixels=22, get_fill_color=[0, 220, 255, 90], pickable=False)
                    tracker_layer = pdk.Layer("IconLayer", data=pd.DataFrame([{"lon": curr_lon, "lat": curr_lat, "angle": direction, "icon": {"url": arrow_url, "width": 140, "height": 140, "anchorY": 70}}]), get_position=["lon", "lat"], get_icon="icon", get_size=1, size_scale=1, size_min_pixels=70, size_max_pixels=120, get_angle="angle", billboard=False, pickable=False)
                    
                    camera = pdk.ViewState(latitude=curr_lat, longitude=curr_lon, zoom=17, pitch=50, bearing=0)
                    deck = pdk.Deck(layers=[traffic_layer, label_layer, route_layer, endpoint_layer, glow_layer, tracker_layer], initial_view_state=camera, map_style="mapbox://styles/mapbox/dark-v9")
                    map_placeholder.pydeck_chart(deck, use_container_width=True)
                    time.sleep(0.01)

            st.session_state["navigating"] = False
            st.success("🏁 You have reached " + st.session_state["destination_name"] + "!")
            st.balloons()
        else:
            first_point = route_coordinates[0]
            view = pdk.ViewState(latitude=first_point[1], longitude=first_point[0], zoom=15, pitch=40)
            deck = pdk.Deck(layers=layers, initial_view_state=view, map_style="mapbox://styles/mapbox/dark-v9")
            map_placeholder.pydeck_chart(deck, use_container_width=True)
    else:
        view = pdk.ViewState(latitude=WCE_LAT, longitude=WCE_LON, zoom=12, pitch=35)
        deck = pdk.Deck(layers=layers, initial_view_state=view, map_style="mapbox://styles/mapbox/dark-v9")
        map_placeholder.pydeck_chart(deck, use_container_width=True)