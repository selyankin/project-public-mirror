"""DTO для API Росреестра."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any


def _to_str(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


@dataclass(slots=True)
class RosreestrMainCharactersDto:
    description: str | None = None
    value: str | None = None
    unitDescription: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RosreestrMainCharactersDto:
        return cls(
            description=_to_str(data.get('description')),
            value=_to_str(data.get('value')),
            unitDescription=_to_str(data.get('unitDescription')),
        )


@dataclass(slots=True)
class RosreestrPermittedUseDto:
    classifier_code: str | None = None
    transcript: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RosreestrPermittedUseDto:
        return cls(
            classifier_code=_to_str(data.get('classifier_code')),
            transcript=_to_str(data.get('transcript')),
        )


@dataclass(slots=True)
class RosreestrEncumbranceDto:
    typeDesc: str | None = None
    rightNumber: str | None = None
    startDate: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RosreestrEncumbranceDto:
        return cls(
            typeDesc=_to_str(data.get('typeDesc')),
            rightNumber=_to_str(data.get('rightNumber')),
            startDate=_to_str(data.get('startDate')),
        )


@dataclass(slots=True)
class RosreestrRightDto:
    rightTypeDesc: str | None = None
    rightNumber: str | None = None
    rightRegDate: str | None = None
    rightType: str | None = None
    part: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RosreestrRightDto:
        return cls(
            rightTypeDesc=_to_str(data.get('rightTypeDesc')),
            rightNumber=_to_str(data.get('rightNumber')),
            rightRegDate=_to_str(data.get('rightRegDate')),
            rightType=_to_str(data.get('rightType')),
            part=_to_str(data.get('part')),
        )


@dataclass(slots=True)
class RosreestrInquiryDto:
    price: str | None = None
    balance: str | None = None
    credit: str | None = None
    speed: str | None = None
    attempts: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RosreestrInquiryDto:
        return cls(
            price=_to_str(data.get('price')),
            balance=_to_str(data.get('balance')),
            credit=_to_str(data.get('credit')),
            speed=_to_str(data.get('speed')),
            attempts=_to_str(data.get('attempts')),
        )


@dataclass(slots=True)
class RosreestrAddressDto:
    region: str | None = None
    city: str | None = None
    cityType: str | None = None
    street: str | None = None
    streetType: str | None = None
    house: str | None = None
    houseType: str | None = None
    building: str | None = None
    buildingType: str | None = None
    structure: str | None = None
    structureType: str | None = None
    apartment: str | None = None
    apartmentType: str | None = None
    liter: str | None = None
    readableAddress: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RosreestrAddressDto:
        kwargs = {
            field: _to_str(data.get(field)) for field in cls.__annotations__
        }
        return cls(**kwargs)  # type: ignore[arg-type]


@dataclass(slots=True)
class RosreestrObjectDto:
    address: RosreestrAddressDto | None = None
    infoUpdate: str | None = None
    cadNumber: str | None = None
    cadCost: str | None = None
    rights: list[RosreestrRightDto] | None = None
    encumbrances: list[RosreestrEncumbranceDto] | None = None
    permittedUse: list[RosreestrPermittedUseDto] | None = None
    mainCharacters: RosreestrMainCharactersDto | None = None
    inquiry: RosreestrInquiryDto | None = None
    objectType: str | None = None
    ObjectType: str | None = None
    purpose: str | None = None
    status: str | None = None
    area: str | None = None
    level: str | None = None
    undergroundFloors: str | None = None
    undergroundFloor: str | None = None
    wallMaterial: str | None = None
    oksWallMaterial: str | None = None
    commissioningYear: str | None = None
    oksCommisioningYear: str | None = None
    yearBuild: str | None = None
    oksYearBuild: str | None = None
    cadUnitDate: str | None = None
    cadCostDate: str | None = None
    regDate: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RosreestrObjectDto:
        address = data.get('address')
        rights = cls._parse_list(data.get('rights'), RosreestrRightDto)
        encumbrances = cls._parse_list(
            data.get('encumbrances'),
            RosreestrEncumbranceDto,
        )
        permitted_use = cls._parse_list(
            data.get('permittedUse'),
            RosreestrPermittedUseDto,
        )
        main_characters = cls._parse_main_character(data.get('mainCharacters'))
        inquiry_data = data.get('inquiry')
        return cls(
            address=(
                RosreestrAddressDto.from_dict(address)
                if isinstance(address, dict)
                else None
            ),
            infoUpdate=_to_str(data.get('infoUpdate')),
            cadNumber=_to_str(data.get('cadNumber')),
            cadCost=_to_str(data.get('cadCost')),
            rights=rights,
            encumbrances=encumbrances,
            permittedUse=permitted_use,
            mainCharacters=main_characters,
            inquiry=(
                RosreestrInquiryDto.from_dict(inquiry_data)
                if isinstance(inquiry_data, dict)
                else None
            ),
            objectType=_to_str(data.get('objectType')),
            ObjectType=_to_str(
                data.get('ObjectType') or data.get('objectType')
            ),
            purpose=_to_str(data.get('purpose')),
            status=_to_str(data.get('status')),
            area=_to_str(data.get('area')),
            level=_to_str(data.get('level')),
            undergroundFloors=_to_str(data.get('undergroundFloors')),
            undergroundFloor=_to_str(
                data.get('undergroundFloor') or data.get('undergroundFloors')
            ),
            wallMaterial=_to_str(data.get('wallMaterial')),
            oksWallMaterial=_to_str(
                data.get('oksWallMaterial') or data.get('wallMaterial')
            ),
            commissioningYear=_to_str(data.get('commissioningYear')),
            oksCommisioningYear=_to_str(
                data.get('oksCommisioningYear') or data.get('commissioningYear')
            ),
            yearBuild=_to_str(data.get('yearBuild')),
            oksYearBuild=_to_str(
                data.get('oksYearBuild') or data.get('yearBuild')
            ),
            cadUnitDate=_to_str(data.get('cadUnitDate')),
            cadCostDate=_to_str(
                data.get('cadCostDate') or data.get('cadUnitDate')
            ),
            regDate=_to_str(data.get('regDate')),
        )

    @staticmethod
    def _parse_list(
        items: Any,
        dto_cls,
    ) -> list[Any] | None:
        if not isinstance(items, Iterable):
            return None
        parsed = [
            dto_cls.from_dict(item) for item in items if isinstance(item, dict)
        ]
        return parsed or None

    @staticmethod
    def _parse_main_character(
        data: Any,
    ) -> RosreestrMainCharactersDto | None:
        if isinstance(data, dict):
            return RosreestrMainCharactersDto.from_dict(data)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    return RosreestrMainCharactersDto.from_dict(item)
        return None


@dataclass(slots=True)
class RosreestrApiResponse:
    status: int | None = None
    found: bool = False
    object: RosreestrObjectDto | None = None

    @classmethod
    def from_dict(cls, data: Any) -> RosreestrApiResponse:
        if not isinstance(data, dict):
            return cls()
        status = data.get('status')
        found = bool(data.get('found'))
        object_data = data.get('object')
        obj = (
            RosreestrObjectDto.from_dict(object_data)
            if isinstance(object_data, dict)
            else None
        )
        return cls(
            status=int(status) if isinstance(status, (int, float)) else None,
            found=found,
            object=obj,
        )

    def to_dict(self) -> dict[str, object]:
        """Сериализовать ответ для кэша."""

        return {
            'status': self.status,
            'found': self.found,
            'object': asdict(self.object) if self.object else None,
        }
