import re

ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-_]+$')

LISTING_ID_PATHS: list[list[str]] = [
    ['data', 'item', 'id'],
    ['item', 'id'],
    ['listing', 'id'],
    ['ad', 'id'],
    ['itemInfo', 'id'],
]

TITLE_PATHS: list[list[str]] = [
    ['data', 'item', 'title'],
    ['item', 'title'],
    ['seo', 'title'],
]

ADDRESS_PATHS: list[list[str]] = [
    ['data', 'item', 'fullAddress'],
    ['item', 'address'],
    ['item', 'locationName'],
]

PRICE_PATHS: list[list[str]] = [
    ['data', 'item', 'price', 'value'],
    ['item', 'price', 'value'],
    ['item', 'price'],
    ['seo', 'price'],
]

COORDS_PATHS: list[list[str]] = [
    ['data', 'item', 'coordinates'],
    ['item', 'coordinates'],
    ['location', 'coords'],
]
