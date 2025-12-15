from enum import StrEnum


class QueryType(StrEnum):
    url = "url"
    address = "address"
    developer = "developer"
    house = "house"


class CheckStatus(StrEnum):
    queued = "queued"
    building = "building"
    ready = "ready"
    failed = "failed"
