from dataclasses import dataclass, field


@dataclass
class DroneSituation:
    drone_id: int
    actual_position: str
    transit_destination: Optional[str] = None
    reached_final_zone: bool = False
