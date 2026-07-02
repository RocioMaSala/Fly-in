from dataclasses import dataclass, field
from map_creator import Connection, Zone, DroneMap, ZoneTypes
from map_parsing import map_creation
import heapq

class NoPathError(Exception):
    def __init__(
            self, message: str = "Invalid Path"
            ) -> None:
        super().__init__(f"{message}")

class SimulationTimeoutError(Exception):
    def __init__(self, message: str = "Simulation exceeded maximum turn limit") -> None:
        super().__init__(message)


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

    
    def dijkstra(self, start_name: str) -> tuple[float, list[str]]:
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

            for dest_zone in connection_matrix.get(current_zone, []):
                if self.static_map.zone_map[dest_zone].zone_type == ZoneTypes.BLOCKED:
                    continue
                if self.static_map.zone_map[dest_zone].zone_type == ZoneTypes.NORMAL:
                    cost = 1
                elif self.static_map.zone_map[dest_zone].zone_type == ZoneTypes.PRIORITY:
                    cost = 0.9
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
        active_drones = [drone for drone in self.drone_list if not drone.reached_final_zone]
        temp_dist_path = {}
        turn_movements = []
        link_capacity_map = self.static_map.link_capacity()
        for drone in active_drones:
            try:
                temp_dist_path[drone.drone_id] = self.dijkstra(drone.actual_position)
            except NoPathError:
                temp_dist_path[drone.drone_id] = (float('inf'), [])
        active_drones_sorted = sorted(
            active_drones,
            key=lambda drone: (temp_dist_path[drone.drone_id][0], drone.drone_id)
        )
        normal_connections_used: list[frozenset[str]] = []
        for drone in active_drones_sorted:
            if drone.transit_destination:
                previous_position = drone.actual_position
                drone.actual_position = drone.transit_destination
                drone.transit_destination = None
                if drone.actual_position not in self.actual_zone_occupation:
                    self.actual_zone_occupation[drone.actual_position] = []
                self.actual_zone_occupation[drone.actual_position].append(drone.drone_id)
                self.actual_conex_occupation[
                    frozenset({previous_position, drone.actual_position})
                ].remove(drone.drone_id)
                if self.static_map.zone_map[drone.actual_position].finish_zone:
                    drone.reached_final_zone = True
                turn_movements.append(f"D{drone.drone_id}-{drone.actual_position}")

            else:
                try:
                    total_distance, path = self.dijkstra(drone.actual_position)
                except NoPathError:
                    continue
                previous_position = drone.actual_position
                next_position = path[1]
                link_key = frozenset({previous_position, next_position})
                drones_en_conexion = len(
                    self.actual_conex_occupation.get(link_key, [])
                    )
                max_link = link_capacity_map.get(link_key, 1)
                if drones_en_conexion >= max_link:
                    continue

                next_zone = self.static_map.zone_map[next_position]
                next_zone = self.static_map.zone_map[next_position]
                if not next_zone.finish_zone:
                    next_zone_drones = len(
                        self.actual_zone_occupation.get(next_position, [])
                        )
                    if next_zone_drones >= next_zone.max_drones:
                        continue

                if self.static_map.zone_map[next_position].zone_type == ZoneTypes.RESTRICTED:
                    drone.transit_destination = next_position
                    key = frozenset({previous_position, drone.transit_destination})
                    if key not in self.actual_conex_occupation:
                        self.actual_conex_occupation[key] = []
                    self.actual_conex_occupation[key].append(drone.drone_id)
                    self.actual_zone_occupation[previous_position].remove(drone.drone_id)
                    turn_movements.append(f"D{drone.drone_id}-{drone.transit_destination}")
                else:
                    drone.actual_position = next_position

                    if link_key not in self.actual_conex_occupation:
                        self.actual_conex_occupation[link_key] = []
                    self.actual_conex_occupation[link_key].append(drone.drone_id)
                    normal_connections_used.append(link_key)

                    if drone.actual_position not in self.actual_zone_occupation:
                        self.actual_zone_occupation[drone.actual_position] = []
                    self.actual_zone_occupation[drone.actual_position].append(drone.drone_id)
                    self.actual_zone_occupation[previous_position].remove(drone.drone_id)

                    if self.static_map.zone_map[drone.actual_position].finish_zone:
                        drone.reached_final_zone = True
                    turn_movements.append(
                        f"D{drone.drone_id}-{drone.actual_position}"
                        )

        for link_key in normal_connections_used:
            self.actual_conex_occupation[link_key] = []

        self.movement_log.append(" ".join(turn_movements))

    def run_simulation(self) -> None:
        self.initialize_drones()
        max_turns = 1000
        while not all(drone.reached_final_zone for drone in self.drone_list):
            self.process_turn()
            if self.turn_count > max_turns:
                raise SimulationTimeoutError(
                    f"Simulation exceeded {max_turns} turns without completing"
                )


if __name__ == "__main__":
    from display import display_static_map

    COLORES_ANSI = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "red": "\033[91m",
        "reset": "\033[0m"
    }

    try:
        my_map = map_creation()
        display_static_map(my_map)
        simu = Simulation(static_map=my_map)
        simu.run_simulation()
        print(
            "Map Key:\n Zone Type Normal -> '■'\n "
            "Zone Type Blocked -> '✕'\n "
            "Zone Type Restricted -> '▲'\n "
            "Zone Type Priority -> '●'")
        print("\nSimulation Finished")
        for turn_number, logro in enumerate(simu.movement_log, start=1):
            if not logro.strip():
                print(f"Turn {turn_number}: No movements")
                continue

            movimientos_coloreados = []

            for mov in logro.split():
                if "-" in mov:
                    drone_part, zone_name = mov.split("-", 1)
                    zone_obj = my_map.zone_map.get(zone_name)

                    color_nombre = getattr(zone_obj, 'color', 'reset')
                    color_ansi = COLORES_ANSI.get(
                        color_nombre, COLORES_ANSI["reset"]
                        )

                    mov_color = (
                        f"{drone_part}-"
                        f"{color_ansi}{zone_name}{COLORES_ANSI['reset']}")
                    movimientos_coloreados.append(mov_color)
                else:
                    movimientos_coloreados.append(mov)

            print(f"Turn {turn_number}: {' '.join(movimientos_coloreados)}")

    except Exception as e:
        print(e)
