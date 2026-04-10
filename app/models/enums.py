from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    BANNED = "banned"
    SHADOW_BANNED = "shadow_banned"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

    # Support short notation
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value_upper = value.upper()
            if value_upper == "M":
                return cls.MALE
            elif value_upper == "F":
                return cls.FEMALE
            elif value_upper == "O":
                return cls.OTHER
        return super()._missing_(value)


class SearchCityMode(StrEnum):
    LOCAL = "local"
    GLOBAL = "global"


class SwipeAction(StrEnum):
    LIKE = "like"
    SKIP = "skip"
