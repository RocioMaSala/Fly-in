from dataclasses import dataclass, field
from map_creator import Connection, Zone, DroneMap, ZoneTypes
from map_parsing import map_creation
import heapq

class NoPathError(Exception):
    def __init__(
            self, message: str = "Invalid Path"
            ) -> None:
        super().__init__(f"{message}")


@dataclass
class DroneSituation:
    drone_id: int
    actual_position: str
    transit_destination: str | None = None
    reached_final_zone: bool = False


@dataclass
class Simulation:
    static_map: DroneMap
    drone_list: list[DroneSituation] = field(default_factory=list)
    actual_zone_occupation: dict[str, list[int]] = field(default_factory=dict)
    actual_conex_occupation: dict[frozenset[str], list[int]] = field(default_factory=dict)
    turn_count: int = 0
    movement_log: list[str] = field(default_factory=list)


    def initialize_drones(self) -> None:
        start_name = ""
        for zone in self.static_map.zone_map.values():
            if zone.start_zone:
                start_name = zone.name
                break
        total_drone_nb = self.static_map.drone_number
        drone_id = 1
        while drone_id <= total_drone_nb:
            drone = DroneSituation(drone_id=drone_id, actual_position=start_name)
            self.drone_list.append(drone)
            if drone.actual_position not in self.actual_zone_occupation:
                self.actual_zone_occupation[drone.actual_position] = []
            self.actual_zone_occupation[drone.actual_position].append(drone.drone_id)
            drone_id += 1

    
    def dijkstra(self, start_name: str, ocupacion_temporal: dict[str, list[int]] = None) -> tuple[float, list[str]]:
        if ocupacion_temporal is None:
            ocupacion_temporal = self.actual_zone_occupation
        end_name = ""
        for zone in self.static_map.zone_map.values():
            if zone.finish_zone:
                end_name = zone.name
                break
        if start_name == end_name:
            return (0.0, [start_name])
        dist = {}
        for k in self.static_map.zone_map.keys():
            dist[k] = float("inf")
        dist[start_name] = 0
        predecessor = {}
        connection_matrix = self.static_map.adjacency()

        heap: list[tuple[float, str]] = []
        heapq.heappush(heap, (0, start_name))
        
        visited = set()

        while heap:
            current_dist, current_zone = heapq.heappop(heap)
            if current_zone in visited:
                continue
            visited.add(current_zone)
        
            for dest_zone in connection_matrix.get(current_zone,[]):
                if self.static_map.zone_map[dest_zone].zone_type == ZoneTypes.BLOCKED:
                    continue
                if dest_zone != end_name and current_zone == start_name:
                    drones_actuales = len(ocupacion_temporal.get(dest_zone, []))
                    if drones_actuales >= self.static_map.zone_map[dest_zone].max_drones:
                        continue
                if self.static_map.zone_map[dest_zone].zone_type == ZoneTypes.NORMAL:
                    cost = 1
                elif self.static_map.zone_map[dest_zone].zone_type == ZoneTypes.PRIORITY:
                    cost = 1
                elif self.static_map.zone_map[dest_zone].zone_type == ZoneTypes.RESTRICTED:
                    cost = 2
                else:
                    cost = 1
                
                new_distance = current_dist + cost
                if new_distance < dist[dest_zone]:
                    dist[dest_zone] = new_distance
                    predecessor[dest_zone] = current_zone
                    heapq.heappush(heap, (new_distance, dest_zone))
        
        if dist[end_name] == float("inf"):
            raise NoPathError
        
        path = []
        current = end_name
        while current != start_name:
            path.append(current)
            current = predecessor[current]
        path.append(start_name)
        path.reverse()
        total_dist = dist[end_name]
        return (total_dist, path)
    

    def process_turn(self) -> None:
        self.turn_count += 1
        turn_movements = []

        movement_planification = {}

        ocupacion_proyectada = {zona: lista.copy() for zona, lista in self.actual_zone_occupation.items()}
        
        drones_in_transit = [d for d in self.drone_list if d.transit_destination and not d.reached_final_zone]
        
        for drone in drones_in_transit:
            movement_planification[drone.drone_id] = ("TRANSIT_END", drone.transit_destination)
            if drone.transit_destination not in ocupacion_proyectada:
                ocupacion_proyectada[drone.transit_destination] = []
            ocupacion_proyectada[drone.transit_destination].append(drone.drone_id)

        free_drones = [d for d in self.drone_list if not d.transit_destination and not d.reached_final_zone]
        mapa_vacio = {}
        def order_criteria(drone):
            try:
                distance = self.dijkstra(drone.actual_position, mapa_vacio)[0]
            except NoPathError:
                distance = float('inf')
            return(distance, drone.drone_id)
        
        free_drones.sort(key=order_criteria)

        for drone in free_drones:
            orig = drone.actual_position
            if drone.drone_id in ocupacion_proyectada.get(orig, []):
                ocupacion_proyectada[orig].remove(drone.drone_id)
            try:
                total_distance, path = self.dijkstra(drone.actual_position, ocupacion_proyectada)
                next_position = path[1]

                print(f"[Turno {self.turn_count}] Dron {drone.drone_id} planifica ir a {next_position}")


                if self.static_map.zone_map[next_position].zone_type == ZoneTypes.RESTRICTED:
                    movement_planification[drone.drone_id] = ("RESTRICTED_START", next_position)
                else:
                    movement_planification[drone.drone_id] = ("NORMAL_MOVE", next_position)
                    if next_position not in ocupacion_proyectada:
                        ocupacion_proyectada[next_position] = []
                    ocupacion_proyectada[next_position].append(drone.drone_id)
            except (NoPathError, IndexError):
                if drone.drone_id not in ocupacion_proyectada.get(orig, []):
                    ocupacion_proyectada[orig].append(drone.drone_id)
                continue
        
        for drone in self.drone_list:
            if drone.drone_id not in movement_planification:
                continue

            mov_type, destination = movement_planification[drone.drone_id]
            previous_position = drone.actual_position
        
            if mov_type == "TRANSIT_END":
                drone.actual_position = destination
                drone.transit_destination = None
                if drone.actual_position not in self.actual_zone_occupation:
                    self.actual_zone_occupation[drone.actual_position] = []
                self.actual_zone_occupation[drone.actual_position].append(drone.drone_id)
                self.actual_conex_occupation[frozenset({previous_position, drone.actual_position})].remove(drone.drone_id)

            elif mov_type == "RESTRICTED_START":
                drone.transit_destination = destination
                if frozenset({previous_position, drone.transit_destination}) not in self.actual_conex_occupation:
                    self.actual_conex_occupation[frozenset({previous_position, drone.transit_destination})] = []
                self.actual_conex_occupation[frozenset({previous_position, drone.transit_destination})].append(drone.drone_id)
                self.actual_zone_occupation[previous_position].remove(drone.drone_id)

            elif mov_type == "NORMAL_MOVE":
                drone.actual_position = destination
                if drone.actual_position not in self.actual_zone_occupation:
                    self.actual_zone_occupation[drone.actual_position] = []
                self.actual_zone_occupation[drone.actual_position].append(drone.drone_id)
                self.actual_zone_occupation[previous_position].remove(drone.drone_id)
            
            # Comprobación de meta
            if drone.actual_position and self.static_map.zone_map[drone.actual_position].finish_zone:
                drone.reached_final_zone = True
            
            turn_movements.append(f"D{drone.drone_id}-{destination}")
    
        self.movement_log.append(" ".join(turn_movements))
    
    def run_simulation(self) -> None:
        self.initialize_drones()
        while not all (drone.reached_final_zone for drone in self.drone_list):
            self.process_turn()


if __name__ == "__main__":
    my_map = map_creation()
    simu = Simulation(static_map=my_map)
    simu.run_simulation()

    print(f"Simulation Finished")
    for logro in simu.movement_log:
        print(logro)
    
    