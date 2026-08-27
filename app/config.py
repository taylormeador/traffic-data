from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    link_info_url: str = (
        "https://cdn.urbansdk.com/data-engineering-interview/link_info.parquet.gz"
    )
    speed_data_url: str = (
        "https://cdn.urbansdk.com/data-engineering-interview/duval_jan1_2024.parquet.gz"
    )
    raw_data_dir: str = "/app/data/raw"


settings = Settings()
