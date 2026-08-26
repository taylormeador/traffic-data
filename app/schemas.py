from enum import Enum

from pydantic import BaseModel, Field


class Day(str, Enum):
    SUNDAY = "Sunday"
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"


# SQL DAYOFWEEK() convention: Sunday=1 ... Saturday=7
DAY_TO_ID: dict[Day, int] = {
    Day.SUNDAY: 1,
    Day.MONDAY: 2,
    Day.TUESDAY: 3,
    Day.WEDNESDAY: 4,
    Day.THURSDAY: 5,
    Day.FRIDAY: 6,
    Day.SATURDAY: 7,
}


class Period(str, Enum):
    OVERNIGHT = "Overnight"
    EARLY_MORNING = "Early Morning"
    AM_PEAK = "AM Peak"
    MIDDAY = "Midday"
    EARLY_AFTERNOON = "Early Afternoon"
    PM_PEAK = "PM Peak"
    EVENING = "Evening"


PERIOD_TO_ID: dict[Period, int] = {
    Period.OVERNIGHT: 1,
    Period.EARLY_MORNING: 2,
    Period.AM_PEAK: 3,
    Period.MIDDAY: 4,
    Period.EARLY_AFTERNOON: 5,
    Period.PM_PEAK: 6,
    Period.EVENING: 7,
}


class LinkAggregate(BaseModel):
    link_id: int
    road_name: str | None
    length: float
    average_speed: float
    geometry: dict


class LinkDetail(BaseModel):
    link_id: int
    road_name: str | None
    length: float
    funclass_id: int
    speedcat: int
    usdk_speed_category: int
    average_speed: float
    geometry: dict


class SlowLink(BaseModel):
    link_id: int
    road_name: str | None
    slow_day_count: int


class SpatialFilterRequest(BaseModel):
    day: Day
    period: Period
    bbox: tuple[float, float, float, float] = Field(
        description="Bounding box as [min_lon, min_lat, max_lon, max_lat]"
    )
