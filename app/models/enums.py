from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    BANNED = "banned"
    SHADOW_BANNED = "shadow_banned"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class SearchCityMode(StrEnum):
    LOCAL = "local"
    GLOBAL = "global"


class SwipeAction(StrEnum):
    LIKE = "like"
    SKIP = "skip"
