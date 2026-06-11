from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ZoneTypes(Enum):
    NORMAL = "normal"
    RESTRICTED = "restricted"
    PRIORITY = "priority"
    BLOCKED = "blocked"


@dataclass
class Zone:
    name: str
    coord_x: int
    coord_y: int
    start_zone: bool = False
    finish_zone: bool = False
    zone_type: ZoneTypes = ZoneTypes.NORMAL
    color: Optional[str] = None


@dataclass
class Connection:
    zone_start: str
    zone_finish: str
    max_capacity: int = 1


@dataclass
class DroneMap:
    drone_number: int
    zone_map: dict[str, Zone] = field(default_factory=dict)
    connection_map: list[Connection] = field(default_factory=list)


def parse_zone(line: str) -> Zone:
    if "[" in line:
        name_coord = line.split("[")[0]
        metadata = line.split("[")[1]
        hub_type = name_coord.split(" ")[0]
        if hub_type is "start_hub":
            start_zone == True
        if hub_type is "end_hub":
            finish_zone == True
        name = name_coord.split(" ")[1]
        coord_x = int(name_coord.split(" ")[2])
        coord_y = int(name_coord.split(" ")[3])
    else:
        hub_type = line.split(" ")[0]
        if hub_type is "start_hub":
            start_zone == True
        if hub_type is "end_hub":
            finish_zone == True
        name = line.split(" ")[1]
        coord_x = int(line.split(" ")[2])
        coord_y = int(line.split(" ")[3])

    

