import io
import json
import logging

import pandas as pd
import requests
from geoalchemy2 import WKTElement
from shapely.geometry import shape
from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Link, SpeedRecord

logger = logging.getLogger(__name__)


def _fetch_parquet(url: str) -> pd.DataFrame:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return pd.read_parquet(io.BytesIO(response.content))


def _to_wkt_element(geo_json: str) -> WKTElement:
    geom = shape(json.loads(geo_json))
    if geom.geom_type == "MultiLineString":
        assert len(geom.geoms) == 1, (
            f"expected single-part MultiLineString, got {len(geom.geoms)} parts"
        )
        geom = geom.geoms[0]
    return WKTElement(geom.wkt, srid=4326)


def _load_links(session: Session) -> int:
    df = _fetch_parquet(settings.link_info_url).rename(columns={"_length": "length"})
    rows = [
        {
            "link_id": r.link_id,
            "length": r.length,
            "road_name": None if pd.isna(r.road_name) else r.road_name,
            "usdk_speed_category": r.usdk_speed_category,
            "funclass_id": r.funclass_id,
            "speedcat": r.speedcat,
            "volume_value": r.volume_value,
            "volume_bin_id": r.volume_bin_id,
            "volume_year": r.volume_year,
            "volumes_bin_description": r.volumes_bin_description,
            "geom": _to_wkt_element(r.geo_json),
        }
        for r in df.itertuples(index=False)
    ]
    session.execute(insert(Link), rows)
    return len(rows)


def _load_speed_records(session: Session) -> int:
    df = _fetch_parquet(settings.speed_data_url)
    df["date_time"] = pd.to_datetime(df["date_time"], utc=True)
    df = df.rename(
        columns={"min": "min_speed", "max": "max_speed", "count": "sample_size"}
    )
    rows = df.to_dict(orient="records")
    session.execute(insert(SpeedRecord), rows)
    return len(rows)


def ingest(session: Session) -> None:
    already_loaded = session.execute(
        select(func.count()).select_from(Link)
    ).scalar_one()
    if already_loaded:
        logger.info("Ingestion skipped: %s links already present", already_loaded)
        return

    logger.info("Starting ingestion")
    link_count = _load_links(session)
    logger.info("Loaded %s links", link_count)
    speed_count = _load_speed_records(session)
    logger.info("Loaded %s speed records", speed_count)
    session.commit()
    logger.info("Ingestion complete")
