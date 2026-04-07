from pydantic import BaseModel, Field

class UserRequest(BaseModel):
    content_type: str = Field(default="")
    content_tone: str = Field(default="")
    content_number: int = Field(default=1)
    content_topics: list[str] = Field(default=[])
    content_trends: list[str] = Field(default=[])
    content_audience: str = Field(default="")
    content_platform: str = Field(default="")
    content_extra_details: str = Field(default="")
  
  
