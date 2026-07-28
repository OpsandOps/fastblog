from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr

# ===============================================
#              USER SCHEMA
# ===============================================
class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)

class UserCreate(UserBase):
    ...
    
class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    image_file: str | None = None
    image_path: str | None = None
    

# =============================================
#       POST SCHEMA
# =============================================
class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)

class PostCreate(PostBase):
    user_id: int # temporary - passed manually after auth we get this from the current user session

class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int 
    user_id: int
    author: UserResponse
    created_at: datetime
    updated_at: datetime | None = None