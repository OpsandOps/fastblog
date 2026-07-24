from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException 

# ========schema imports =================
from schemas import PostCreate, PostResponse, UserCreate, UserResponse

# ===========db imports ================
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import Depends
from database import Base, engine, get_db, 

# ============model imports ===============
import models


# =======create database tables on app startup if not exist ======
# looks at all the models that inherits from base and create all the tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

#=======mount a media file for all user_uploaded files=========
app.mount("/media" StaticFiles(directory="media"), name="media")
#========set a template library and selected dir for template==========
templates = Jinja2Templates(directory="templates")
#=======mount a static file for all static files we create==============
app.mount("/static", StaticFiles(directory="static"), name="static") 

# post_list: list[dict] = [
#     {   
#         "id": 1,
#         "author": "Julien Nagelsman",
#         "title": "Home away from home",
#         "content": "This is a serial novel written by a very good author about a Home away from home this is to add some content to the blog",
#         "created_at": "15th July 2026",
#         "updated_at": "today"
#     },
#     {   
#         "id": 2,
#         "author": "Prospa  Ops",
#         "title": "God is Good",
#         "content": "A devotional written by the author for daily study and religious content built with fastapi",
#         "created_at": "20th July 2026",
#         "updated_at": "today"
#     },
#     {
#         "id": 3,
#         "author": "Damelson Vincent",
#         "title": "Power over Fear",
#         "content": "The chronicle of a developer who never writes but read and debugs, I dont even know what that means here",
#         "created_at": "22nd July 2026",
#         "updated_at": "today"
#     }

# ]

# ========HTTP EXCEPTION HANDLER===============================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": exc.status_code, "detail": exc.detail, "title": f"Error {exc.status_code}"},
        status_code=exc.status_code,
    )


#===========GENERIC HTTP EXCEPTION HANDLER==error 500===========
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": 500, "detail": None, "title": "Server Error"},
        status_code=500,
    )

#==========GENERAL HTTP EXCEPTION HANDLER FOR STARLETTE================
@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    # 1. handle starlette exception with and without a detail
    message = (
        exception.detail 
        if exception.detail
        else "An error occured. Please Check your request and try again."
    )

    # 2. check the route,to match else return JSON response

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )

    # 3. return our error.html for errored routes
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )

# ============VALIDATION EXCEPTION HANDLER FOR STARLETTE===========================
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={'detail': exception.errors()}
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again"
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


# ============GET ROUTE============ BROWSEABLE ROUTES (NOT IN SCHEMA)=============
@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request, db: Annotated[Session, Depend(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"})


# ========GET ROUTE====BROWSABLE ROUTES(NOT IN SCHEMA)================
@app.get("/posts/{post_id}", include_in_schema=False, name="post")
def get_post_pages(post_id: int, request: Request):
    for p in post_list:
        if p.get("id") == post_id:
            return templates.TemplateResponse(
                request, 
                "post.html", 
                {"post": p, "title": p["title"][:50]})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not Found")


# ================API ROUTES(NOT BROWSABLE)==================
@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_posts(post_id: int) -> dict:
    for post_item in post_list:
        if post_item.get("id") == post_id:
            return post_list['content']
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not Found")


# =================GET API ROUTE(NOT BROWSEABLE)===================
@app.get("/api/all_posts", response_model=list[PostResponse])
def get_all_posts() -> list:
    return post_list

# ================POST API ROUTES(NOT BROWSABLE)========CREATE POST============
@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,

)
def create_post(new_post: PostCreate):
    new_id = max(p["id"] for p in post_list) + 1 if post_list else 1 # teneray conditonal expression
    created_post = {
        "id": new_id,
        "author": new_post.author,
        "title": new_post.title,
        "content": new_post.content,
        "created_at": new_post.created_at,
        "updated_at": " "
    }
    post_list.append(created_post)
    return created_post 

# ===========API USER ROUTE======(post)===CREATE USER=====
# The standard SQLAlchemy ORM create pattern is
#  -- Check if the record exists 
#  -- Instantiate the model 
#  -- db.add()
#  -- db.commit() 
#  -- db.refresh()
# =====================================
@app.post(
    "/api/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)

def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    # 1. check the username if it exists
    result = db.execute(
        select(models.User).where(models.User.username == user.username)
    )
    if result.scalars().first(): # scalars() unpacks the tuple returned in result to a user object
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # 2. check for exisiting email and raise errors if they exist, if theyfont create the new user
     result = db.execute(
        select(models.User).where(models.User.email == user.email)
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # 3. create the actual ORM new_user object.
    new_user = models.User(
        username=user.username,
        email=user.email,
    )

    # 4. Standard ORM save pattern
    # === add the newly created user to the table
    db.add(new_user)
    #===persist the newuser to the db======
    db.commit()
    #===refresh the db to ensure newuser persist=====
    db.refresh(new_user)

    # 5. return the object
    return new_user

# ==================API ROUTE (GET) ======GET USER======================
# The standard SQLAlchemy ORM read pattern for a single record is
#  -- Query the database using a where clause
#  -- Extract the object using scalars().first()
#  -- Check if it exists (if not, raise 404)
#  -- Return the object
# =====================================================================

@app.get(
    "/api/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK
)

def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    #1. Query database for the user with user_id
    result = db.execute(
        select(models.User).where(models.User.id == user_id),
    )

    #2. Extract the user object, None if not exist
    user = result.scalars().first()

    #3. Validate: if the user does not exist raise exception
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )
    #4. return the found user
        return user  

# ==================API ROUTE {user_id}===post ==================
# The standard SQLAlchemy ORM read pattern for related records is
#  -- Verify the parent record (User) exists
#  -- Query the database for the child records (Posts) using a where clause
#  -- Extract all objects using scalars().all()
#  -- Return the list of objects
# ====================================================================
@app.get(
    "/api/users/{user_id}/posts",
    response_model=list[PostResponse],
    status_code=status.HTTP_200
)
def get_user_posts(user_id: int, db: Annotated[Session, Depends(get_db)]):
    # 1. query the database to verify if the user exists
    result = db.execute(
        select(models.User).where(models.User.id == user_id)
    )

    user = result.scalars().first()
    #2. if the user does not EXIST raise an exception
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    #3. Query the database for all the post belonging to the user
    post_result = db.execute(
        select(models.Post).where(models.Post.user_id == user_id)
    )

    #4 . Extract all the post into a list (returns an empty list if the user has no post)
    posts = posts_result.scalars().all()

    #5. return all posts
    return posts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)








