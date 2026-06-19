from map_parsing import map_creation

drone_map = map_creation()
distance, path = drone_map.dijkstra()
print(f"Distance: {distance}")
print(f"Path: {path}")