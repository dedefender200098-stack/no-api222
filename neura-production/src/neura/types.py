from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Coordinates:
    x: int
    y: int
    _id: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Coordinates":
        return cls(
            x=data["x"],
            y=data["y"],
            _id=data["_id"],
        )


@dataclass
class PulseData:
    id: str
    is_collected: bool
    coordinates: Coordinates
    _id: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PulseData":
        return cls(
            id=data["id"],
            is_collected=data["isCollected"],
            coordinates=Coordinates.from_dict(data["coordinates"]),
            _id=data["_id"],
        )


@dataclass
class Pulses:
    first_collected_at: datetime
    last_collected_at: Optional[datetime]
    data: List[PulseData]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pulses":
        first_collected_at = datetime.fromisoformat(
            data["firstCollectedAt"].replace("Z", "+00:00")
        )
        last_collected_at = (
            datetime.fromisoformat(data["lastCollectedAt"].replace("Z", "+00:00"))
            if data["lastCollectedAt"]
            else None
        )
        pulses_data = [PulseData.from_dict(item) for item in data["data"]]
        return cls(
            first_collected_at=first_collected_at,
            last_collected_at=last_collected_at,
            data=pulses_data,
        )


@dataclass
class TradingVolume:
    month: float
    all_time: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradingVolume":
        return cls(
            month=data["month"],
            all_time=data["allTime"],
        )


@dataclass
class UserData:
    address: str
    neura_points: int
    trading_volume: TradingVolume
    pulses: Pulses
    social_accounts: List[Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserData":
        return cls(
            address=data["address"],
            neura_points=data["neuraPoints"],
            trading_volume=TradingVolume.from_dict(data["tradingVolume"]),
            pulses=Pulses.from_dict(data["pulses"]),
            social_accounts=data.get("socialAccounts", []),
        )
