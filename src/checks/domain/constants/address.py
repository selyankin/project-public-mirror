import re
from typing import Final

WHITESPACE_RE: Final[re.Pattern[str]] = re.compile(r'\s+')
COMMA_RE: Final[re.Pattern[str]] = re.compile(r'\s*,\s*')

ADDRESS_KEYWORDS = {
    'ул',
    'улица',
    'пр-т',
    'проспект',
    'просп',
    'пер',
    'переулок',
    'ш',
    'шоссе',
    'наб',
    'набережная',
    'пл',
    'площадь',
    'д',
    'дом',
    'кв',
    'корп',
    'корпус',
    'стр',
    'строение',
    'лит',
    'бульвар',
    'б-р',
}
