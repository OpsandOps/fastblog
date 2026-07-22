from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException 
from datetime import datetime
from schemas import PostCreate, PostResponse

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static") 

post_list: list[dict] = [
    {   
        "id": 1,
        "author": "Julien Nagelsman",
        "title": "Home away from home",
        "content": "This is a serial novel written by a very good author about a Home away from home this is to add some content to the blog",
        "created_at": "15th July 2026",
        "updated_at": "today"
    },
    {   
        "id": 2,
        "author": "Prospa  Ops",
        "title": "God is Good",
        "content": "A devotional written by the author for daily study and religious content built with fastapi",
        "created_at": "20th July 2026",
        "updated_at": "today"
    },
    {
        "id": 3,
        "author": "Damelson Vincent",
        "title": "Power over Fear",
        "content": "The chronicle of a developer who never writes but read and debugs, I dont even know what that means here",
        "created_at": "22nd July 2026",
        "updated_at": "today"
    }

]

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


# ============GET ROUTE============BROWSEABLE ROUTES (NOT IN SCHEMA)=============
@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": post_list, "title": "Home"})


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

# ================POST API ROUTES(NOT BROWSABLE)====================
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







if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)








