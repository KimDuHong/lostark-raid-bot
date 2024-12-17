from pydantic import BaseModel

class DiscordUserSchema(BaseModel):
    discord_id: int
    discord_name: str
    discord_avatar: str | None = None
