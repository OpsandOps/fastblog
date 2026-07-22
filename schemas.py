from pydantic import BaseModel, ConfigDict, Field

class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=50)
    created_at: str = Field(min_lenth=1)
    updated_at: str = Field(min_length=0)


class PostCreate(PostBase):
    ...

class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int 