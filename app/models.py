from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Link(Base):
    __tablename__ = "link"

    link_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    length: Mapped[float] = mapped_column(Float)
    road_name: Mapped[str | None] = mapped_column(String, nullable=True)
    usdk_speed_category: Mapped[int] = mapped_column(Integer)
    funclass_id: Mapped[int] = mapped_column(Integer)
    speedcat: Mapped[int] = mapped_column(Integer)
    volume_value: Mapped[int] = mapped_column(Integer)
    volume_bin_id: Mapped[int] = mapped_column(Integer)
    volume_year: Mapped[int] = mapped_column(Integer)
    volumes_bin_description: Mapped[str] = mapped_column(String)
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=True)
    )


class SpeedRecord(Base):
    __tablename__ = "speed_record"
    __table_args__ = (
        # day_of_week currently contributes zero additional selectivity on top of
        # period/link_id alone since every loaded row has day_of_week=2, but it seems
        # obvious that the system would want to handle more than one day of data, eventually.
        Index("ix_speed_record_link_day_period", "link_id", "day_of_week", "period"),
        Index("ix_speed_record_period_day_link", "period", "day_of_week", "link_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    link_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("link.link_id"))
    date_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    freeflow: Mapped[float] = mapped_column(Float)
    sample_size: Mapped[int] = mapped_column(Integer)
    std_dev: Mapped[float] = mapped_column(Float)
    min_speed: Mapped[float] = mapped_column(Float)
    max_speed: Mapped[float] = mapped_column(Float)
    confidence: Mapped[int] = mapped_column(Integer)
    average_speed: Mapped[float] = mapped_column(Float)
    average_pct_85: Mapped[float] = mapped_column(Float)
    average_pct_95: Mapped[float] = mapped_column(Float)
    day_of_week: Mapped[int] = mapped_column(Integer)
    period: Mapped[int] = mapped_column(Integer)
