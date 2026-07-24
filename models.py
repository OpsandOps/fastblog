from __future__ import annotations #enables forward relationships between fields

from datetime import UTC, datetime
from database import Base
from sqlalchemy import DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    image_file: Mapped[ str | None] = mapped_column(String(120), nullable=True, default=None)
    image_path: Mapped[str | None] = mapped_column(String(255), default=None)

    posts: Mapped[list[Post]] = relationship(back_populates="author") 
    #used for backward relationships like user.posts,
    #"author" is the related name here just like in Django

    def __repr__(self) -> str:
        return f"<User id='{self.id}' username='{self.username}' email='{self.email}'>"


    @property
    def image_url(self):
        '''
        checks for image_file in the User object, and populates the Image folder with it
        else use the default picture from the static folder.
        '''
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "static/profile_pics/default.jpg"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )
    author: Mapped[User] = relationship(back_populates="posts")

    def __repr__(self):
        return f"<Post id: '{self.id} 'Post title: '{self.title}' Post content: '{self.conten}'>"
