from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Link, SpeedRecord
from app.schemas import PERIOD_TO_ID, Period, SlowLink

router = APIRouter()


@router.get("/slow_links/", response_model=list[SlowLink])
def get_slow_links(
    period: Period,
    threshold: float = Query(..., gt=0, description="Speed threshold in mph"),
    min_days: int = Query(..., ge=1, le=7, description="Minimum qualifying days in a week"),
    db: Session = Depends(get_db),
):
    daily_avg = (
        select(
            SpeedRecord.link_id,
            SpeedRecord.day_of_week,
            func.avg(SpeedRecord.average_speed).label("avg_speed"),
        )
        .where(SpeedRecord.period == PERIOD_TO_ID[period])
        .group_by(SpeedRecord.link_id, SpeedRecord.day_of_week)
        .subquery()
    )

    stmt = (
        select(
            daily_avg.c.link_id,
            Link.road_name,
            func.count().label("slow_day_count"),
        )
        .join(Link, Link.link_id == daily_avg.c.link_id)
        .where(daily_avg.c.avg_speed < threshold)
        .group_by(daily_avg.c.link_id, Link.road_name)
        .having(func.count() >= min_days)
    )
    rows = db.execute(stmt).all()
    return [
        SlowLink(link_id=r.link_id, road_name=r.road_name, slow_day_count=r.slow_day_count)
        for r in rows
    ]
