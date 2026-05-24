from enum import Enum


class StoreId(str, Enum):
    PLAZA_VEA = "plaza_vea"
    METRO = "metro"
    VIVANDA = "vivanda"
    TOTTUS = "tottus"


class QuantityUnit(str, Enum):
    G = "g"
    KG = "kg"
    ML = "ml"
    L = "l"
    UNIT = "unit"
    PACK = "pack"
    ROLL = "roll"
    BAG = "bag"
    BOX = "box"


class Availability(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
