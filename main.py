from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError, ResponseValidationError 
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException 

# ========schema imports =================
from schemas import PostCreate, PostResponse, UserCreate, UserResponse

# ===========db imports ================
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import Depends
from database import Base, engine, get_db

# ============model imports ===============
import models

# ============import logging to log cleanly ==========
import logging

# ===create a logger instance=====
logger = logging.getLogger(__name__)


# =======create database tables on app startup if not exist ======
# looks at all the models that inherits from base and create all the tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

#=======mount a media file for all user_uploaded files=========
app.mount("/media", StaticFiles(directory="media"), name="media")
#========set a template library and selected dir for template==========
templates = Jinja2Templates(directory="templates")
#=======mount a static file for all static files we create==============
app.mount("/static", StaticFiles(directory="static"), name="static") 

# ========HTTP EXCEPTION HANDLER===============================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"Unhandled Exception on {request.url.path}: {str(exc)}", exc_info=True)

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": exc.status_code, "detail": exc.detail, "title": f"Error {exc.status_code}"},
        status_code=exc.status_code,
    )


#===========GENERIC HTTP EXCEPTION HANDLER==error 500===========
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.url.path}: {str(exc)}", exc_info=True)

    if request.url.path.startswith("/api"):
        return JSONResponse (
            status_code=500,
            content={"detail": "not found"}
        )
        
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
# ==============request validation exception handler==================================
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exception: RequestValidationError):
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

# ==========response validation exception handler ===================================
@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
    logger.error(f"Response Validation Error on {request.url.path}: {str(exc.errors())}", exc_info=True)
    
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            # Don't leak internal schema errors to the user
            content={"detail": "Server error: Failed to format response data"} 
        )
        
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": 500, "detail": None, "title": "Server Error"},
        status_code=500,
    )

# =======POST ROUTES ====================
# ====GET=========== BROWSABLE ROUTES (NOT IN SCHEMA)=============
@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    post = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": post})


# ========GET ROUTE WITH POST ID====BROWSABLE ROUTES(NOT IN SCHEMA)================
@app.get("/posts/{post_id}", include_in_schema=False, name="post")
def get_post_pages(post_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    #1. Query the db for a post matching the post_id
    result = db.execute(
        select(models.Post).where(models.Post.id == post_id)
    )

    #2. extract the post from result
    post = result.scalars().first()

    #3. if the post exist, return the post using the template with a sliced title
    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {
                "post": post, "title": title
            }
        )
    #4. if the post does not exist, return a http 404 exception
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not Found")



# ======BROWSABLE ROUTE ========("user/{user_id}/posts")====
#to get all post for a user
#===============================================================

@app.get(
    "/users/{user_id}/posts",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
    name="users"
)
def get_all_user_posts(user_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    # 1. query the database to verify if the user exists
    result = db.execute(
        select(models.User).where(models.User.id == user_id)
    )

    user = result.scalars().all()
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
    posts = post_result.scalars().first()

    #5. return all posts if the post exist, return the post using the template with a sliced title
    if posts:
        title = posts.title[:50]
        return templates.TemplateResponse(
            request,
            "user_post.html",
            {
                "posts": posts, "title": title, "user": user
            }
        )
    #4. if the post does not exist, return a http 404 exception
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not Found")

# ================API ROUTES(NOT BROWSABLE)==================
# @app.get("/api/posts/{post_id}", response_model=PostResponse)
@app.get("/api/posts/{post_id}")
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    #1. Query the db for the post based on the post_id
    result = db.execute(
        select(models.Post).where(models.Post.id == post_id)
    )
    # 2. Extracts the post object return None if no id
    post = result.scalars().first()

    #3. return the post
    if post:
        return post.content 
        # to return a single post content, remove the response_model=PostResponse
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not Found")


# =================GET API ROUTE(NOT BROWSEABLE)===================
# fix validatio error here
@app.get("/api/all_posts", response_model=list[PostResponse])
def get_all_posts(db: Annotated[Session, Depends(get_db)]):
    #1. Query the db for all post
    result = db.execute(select(models.Post).options(selectinload(models.Post.author)))
    #2. serialise/extract post
    all_post = result.scalars().all()
    #3. return post
    return all_post


# ================POST API ROUTES(NOT BROWSABLE)========CREATE POST============
@app.post(
    "/api/create_posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,

)

def create_post(post_data: PostCreate, db: Annotated[Session, Depends(get_db)]):
    #1. Query for an existing user
    existing_user = db.execute(
        select(models.User).where(
            models.User.id == post_data.user_id
        )
    )

    #2. transform to a list
    existing_user_result = existing_user.scalars().first()

    if not existing_user_result: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Cannot create a post for a non-existent user."
        )


    #1. Query the db to check if there is an existing post with the same id for the user
    post_result = db.execute(
        select(models.Post).where(
            models.Post.title == post_data.title,
            models.Post.user_id == post_data.user_id
        )
    )
    #2. Extract the first post from the result
    post = post_result.scalars().first()

    #3. raise exception if the post exist
    if post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post with this title exist already"
        )

    #4. Create a new post object
    new_post = models.Post(
        title=post_data.title,
        content=post_data.content,
        user_id=post_data.user_id,
    )

    # 5. add the post to db 
    try:
        db.add(new_post)
        db.commit()
        # db.refresh(new_post, attribute_names=['author'])
        # 6 refetch the post to make sure the user is attached using the .options(selectinload(models.Post.author))
        result = db.execute(
            select(models.Post)
            .options(selectinload(models.Post.author))
            .where(models.Post.id == new_post.id)
            )

        new_post = result.scalars().all()

    except SQLAlchemyError as e:
        # rollback to previous db state
        db.rollback()
        # log the full error context for traceability
        logger.error(f"Database failed to create post: {str(e)}")
        # raise generic http error 
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to create post"
        )
        
    # 6. return post
    return new_post
    

# ===========API USER ROUTE======(post)===CREATE USER=====
# The standard SQLAlchemy ORM create pattern is
#  -- Check if the record exists 
#  -- Instantiate the model 
#  -- db.add()
#  -- db.commit() 
#  -- db.refresh()
# ======================================================
@app.post(
    "/api/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)

def create_user(new_user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    # 1. check the username if it exists
    result = db.execute(
        select(models.User).where(models.User.username == new_user.username)
    )
    if result.scalars().first(): # scalars() unpacks the tuple returned in result to a user object
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # 2. check for exisiting email and raise errors if they exist, if not dont create the new user
    result = db.execute(
        select(models.User).where(models.User.email == new_user.email)
    )

    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # 3. create the actual ORM new_user object.
    user = models.User(
        username=new_user.username,
        email=new_user.email,
    )

    # 4. Standard ORM save pattern
    # === add the newly created user to the table
    try:
        db.add(user)
        #===persist the newuser to the db======
        db.commit()
        #===refresh the db to ensure newuser persist=====
        db.refresh(user)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database failed to create {user.username}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Usern not created")

    # 5. return the object
    return user

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
            status_code=status.HTTP_404_NOT_FOUND,
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
    status_code=status.HTTP_200_OK
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
    posts = post_result.scalars().all()

    #5. return all posts
    return posts



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)








