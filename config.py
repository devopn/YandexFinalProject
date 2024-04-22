from dataclasses import dataclass

@dataclass
class Config:
    tg_api: str
    db_url: str
    yandex_api_key: str
    yandex_cloud_catalog: str

config = Config(
    tg_api="XXX",
    db_url="XXX",
    yandex_api_key="XXX",
    yandex_cloud_catalog="XXX")
