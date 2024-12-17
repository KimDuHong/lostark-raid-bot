from pydantic import BaseModel


class CharacterSchema(BaseModel):
    character_name: str
    character_class: str
    item_level: int
    server_name: str
    main_character: bool = False


class ExpeditionSchema(BaseModel):
    character_image: str
    server_name: str
    expedition_level: int
    characters: list[CharacterSchema]
