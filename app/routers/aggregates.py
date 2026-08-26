import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Link, SpeedRecord
from app.schemas import (
    DAY_TO_ID,
    PERIOD_TO_ID,
    Day,
    LinkAggregate,
    LinkDetail,
    Period,
    SpatialFilterRequest,
)

router = APIRouter()


@router.get("/", response_model=list[LinkAggregate])
def get_aggregates(day: Day, period: Period, db: Session = Depends(get_db)):
    stmt = (
        select(
            Link.link_id,
            Link.road_name,
            Link.length,
            func.ST_AsGeoJSON(Link.geom).label("geometry"),
            func.avg(SpeedRecord.average_speed).label("average_speed"),
        )
        .join(SpeedRecord, SpeedRecord.link_id == Link.link_id)
        .where(
            SpeedRecord.day_of_week == DAY_TO_ID[day],
            SpeedRecord.period == PERIOD_TO_ID[period],
        )
        .group_by(Link.link_id, Link.road_name, Link.length, Link.geom)
    )
    rows = db.execute(stmt).all()
    return [
        LinkAggregate(
            link_id=r.link_id,
            road_name=r.road_name,
            length=r.length,
            average_speed=r.average_speed,
            geometry=json.loads(r.geometry),
        )
        for r in rows
    ]


@router.get("/{link_id}", response_model=LinkDetail)
def get_aggregate_for_link(
    link_id: int, day: Day, period: Period, db: Session = Depends(get_db)
):
    stmt = (
        select(
            Link.link_id,
            Link.road_name,
            Link.length,
            Link.funclass_id,
            Link.speedcat,
            Link.usdk_speed_category,
            func.ST_AsGeoJSON(Link.geom).label("geometry"),
            func.avg(SpeedRecord.average_speed).label("average_speed"),
        )
        .join(SpeedRecord, SpeedRecord.link_id == Link.link_id)
        .where(
            Link.link_id == link_id,
            SpeedRecord.day_of_week == DAY_TO_ID[day],
            SpeedRecord.period == PERIOD_TO_ID[period],
        )
        .group_by(
            Link.link_id,
            Link.road_name,
            Link.length,
            Link.funclass_id,
            Link.speedcat,
            Link.usdk_speed_category,
            Link.geom,
        )
    )
    row = db.execute(stmt).first()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No speed data for link_id={link_id} on {day.value} during {period.value}",
        )
    return LinkDetail(
        link_id=row.link_id,
        road_name=row.road_name,
        length=row.length,
        funclass_id=row.funclass_id,
        speedcat=row.speedcat,
        usdk_speed_category=row.usdk_speed_category,
        average_speed=row.average_speed,
        geometry=json.loads(row.geometry),
    )


@router.post("/spatial_filter/", response_model=list[LinkAggregate])
def spatial_filter(body: SpatialFilterRequest, db: Session = Depends(get_db)):
    min_lon, min_lat, max_lon, max_lat = body.bbox
    bbox_geom = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)

    stmt = (
        select(
            Link.link_id,
            Link.road_name,
            Link.length,
            func.ST_AsGeoJSON(Link.geom).label("geometry"),
            func.avg(SpeedRecord.average_speed).label("average_speed"),
        )
        .join(SpeedRecord, SpeedRecord.link_id == Link.link_id)
        .where(
            func.ST_Intersects(Link.geom, bbox_geom),
            SpeedRecord.day_of_week == DAY_TO_ID[body.day],
            SpeedRecord.period == PERIOD_TO_ID[body.period],
        )
        .group_by(Link.link_id, Link.road_name, Link.length, Link.geom)
    )
    rows = db.execute(stmt).all()
    return [
        LinkAggregate(
            link_id=r.link_id,
            road_name=r.road_name,
            length=r.length,
            average_speed=r.average_speed,
            geometry=json.loads(r.geometry),
        )
        for r in rows
    ]
