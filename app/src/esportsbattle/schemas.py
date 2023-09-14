from pydantic import BaseModel


# class SMatch(BaseModel):
#     data: dict[str, str]


# class STournament(BaseModel):
#     data: list[SMatch]


class SRawData(BaseModel):
    data: dict[str, dict[str, list[dict[str, str]]]]
