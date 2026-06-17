import sys
from map_creator import DroneMap, parse_zone, parse_connection

class UsageError(Exception):
    def __init__(self, message: str = "Usage Error: python3 XXXXX "
                 "config.txt") -> None:
        super().__init__(message)

class MissingDroneNumber(Exception):
    def __init__(self, message: str = "Index Error: A drone number is needed") -> None:
        super().__init__(message)

class DroneNumberError(Exception):
    def __init__(self, message: str = "Value Error: A valid drone number is needed") -> None:
        super().__init__(message)

def map_creation() -> DroneMap:
    if len(sys.argv) != 2:
        raise UsageError 
    try:
        with open(sys.argv[1]) as file:
            line_num = 0
            drone_nbr = None
            start_hub_name = None
            end_hub_name = None
            for line in file:
                line_num += 1
                line_clean = line.strip() #elimino todos los espacios antes y después
                
                if not line_clean or line_clean.startswith("#"):
                    continue

                if not line_clean.startswith("nb_drones:"):
                    raise DroneNumberError(f"Value Error: Expected 'nb_drones:', line {line_num}")

                try:
                    value_part = line_clean.split(":", 1)[1].strip()
                    drone_nbr = int(value_part)
                except (IndexError, ValueError):
                    raise DroneNumberError(f"Value Error: A valid drone number is needed, line {line_num}")
                
                if drone_nbr <= 0:
                    raise DroneNumberError(f"Value Error: Drone number must be a positive integer, line {line_num}")
                break

            if drone_nbr is None:
                raise MissingDroneNumber("Index Error: A drone number is needed at the beginning of the file")

            map = DroneMap(drone_nbr)

            for line in file:
                line_num += 1
                line_clean = line.strip()
                if not line.clean() or line.clean.startswith("#"):
                    continue
                if line_clean.startswith(("start_hub", "end_hub", "hub")):
                    zone = parse_zone(line, line_num)
                    if line_clean.startswith("start_hub:"):
                        if start_hub_name is not None:
                            raise ValueError(f"Parsing Error: Multiple start_hubs detected, line {line_num}")
                        start_hub_name = zone.name
                    elif line_clean.startswith("end_hub:"):
                        if end_hub_name is not None:
                            raise ValueError(f"Parsing Error: Multiple end_hubs detected, line {line_num}")
                        end_hub_name = zone.name
                    map.zone_map[zone.name] = zone
                elif line.strip().startswith("connection"):
                    connection = parse_connection(line, line_num)

                    if connection.zone_start not in map.zone_map:
                        raise ValueError(f"Parsing Error: Zone '{connection.zone_start}' is not defined, line {line_num}")
                    if connection.zone_finish not in map.zone_map:
                        raise ValueError(f"Parsing Error: Zone '{connection.zone_finish}' is not defined, line {line_num}")
                    for existing_conn in map.connection_map:
                        match_direct = (existing_conn.zone_start == connection.zone_start and
                                        existing_conn.zone_finish == connection.zone_finish)
                        match_inverted = (existing_conn.zone_start == connection.zone_finish and
                                          existing_conn.zone_finish == connection.zone_start)

                        if match_direct or match_inverted:
                            raise ValueError(f"Parsing Error: Duplicate connection between '{connection.zone_start}' and '{connection.zone_finish}', line {line_num}")
                    map.connection_map.append(connection)

            if start_hub_name is None:
                raise ValueError("Parsing Error: Missing 'start_hub:' zone in the file")

            if end_hub_name is None:
                raise ValueError("Parsing Error: Missing 'end_hub:' zone in the file")

            if start_hub_name == end_hub_name:
                raise ValueError(f"Parsing Error: 'start_hub' and 'end_hub' cannot be the same ('{start_hub_name}')")

        return map
    except FileNotFoundError:
        raise FileNotFoundError("File not present")


if __name__ == "__main__":
    try:
        map = map_creation()

    except Exception as e:
        print(e)
