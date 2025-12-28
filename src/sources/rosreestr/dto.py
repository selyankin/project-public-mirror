"""DTO для API Росреестра."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any


def _get_str(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    return str(value) if isinstance(value, str) and value else None


@dataclass(slots=True)
class RosreestrMainCharactersDto:
    description: str | None = None
    value: str | None = None
    unitDescription: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RosreestrMainCharactersDto:
        return cls(
            description=_get_str(data, 'description'),
            value=_get_str(data, 'value'),
            unitDescription=_get_str(data, 'unitDescription'),
        )


@dataclass(slots=True)
class RosreestrPermittedUseDto:
    classifier_code: str | None = None
    transcript: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RosreestrPermittedUseDto:
        return cls(
            classifier_code=_get_str(data, 'classifier_code'),
            transcript=_get_str(data, 'transcript'),
        )


@dataclass(slots=True)
class RosreestrEncumbranceDto:
    typeDesc: str | None = None
    rightNumber: str | None = None
    startDate: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RosreestrEncumbranceDto:
        return cls(
            typeDesc=_get_str(data, 'typeDesc'),
            rightNumber=_get_str(data, 'rightNumber'),
            startDate=_get_str(data, 'startDate'),
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
            rightTypeDesc=_get_str(data, 'rightTypeDesc'),
            rightNumber=_get_str(data, 'rightNumber'),
            rightRegDate=_get_str(data, 'rightRegDate'),
            rightType=_get_str(data, 'rightType'),
            part=_get_str(data, 'part'),
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
            price=_get_str(data, 'price'),
            balance=_get_str(data, 'balance'),
            credit=_get_str(data, 'credit'),
            speed=_get_str(data, 'speed'),
            attempts=_get_str(data, 'attempts'),
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
        kwargs = {field: _get_str(data, field) for field in cls.__annotations__}
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
    mainCharacters: list[RosreestrMainCharactersDto] | None = None
    inquiry: RosreestrInquiryDto | None = None
    objectType: str | None = None
    purpose: str | None = None
    status: str | None = None
    area: str | None = None
    level: str | None = None
    undergroundFloors: str | None = None
    wallMaterial: str | None = None
    commissioningYear: str | None = None
    yearBuild: str | None = None
    cadUnitDate: str | None = None
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
        main_characters = cls._parse_list(
            data.get('mainCharacters'),
            RosreestrMainCharactersDto,
        )
        inquiry_data = data.get('inquiry')
        return cls(
            address=(
                RosreestrAddressDto.from_dict(address)
                if isinstance(address, dict)
                else None
            ),
            infoUpdate=_get_str(data, 'infoUpdate'),
            cadNumber=_get_str(data, 'cadNumber'),
            cadCost=_get_str(data, 'cadCost'),
            rights=rights,
            encumbrances=encumbrances,
            permittedUse=permitted_use,
            mainCharacters=main_characters,
            inquiry=(
                RosreestrInquiryDto.from_dict(inquiry_data)
                if isinstance(inquiry_data, dict)
                else None
            ),
            objectType=_get_str(data, 'objectType'),
            purpose=_get_str(data, 'purpose'),
            status=_get_str(data, 'status'),
            area=_get_str(data, 'area'),
            level=_get_str(data, 'level'),
            undergroundFloors=_get_str(data, 'undergroundFloors'),
            wallMaterial=_get_str(data, 'wallMaterial'),
            commissioningYear=_get_str(data, 'commissioningYear'),
            yearBuild=_get_str(data, 'yearBuild'),
            cadUnitDate=_get_str(data, 'cadUnitDate'),
            regDate=_get_str(data, 'regDate'),
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
