from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException 
from datetime import datetime

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static") 

post: list[dict] = [
    {   
        "id": 1,
        "author": "Julien Nagelsman",
        "title": "Home away from home",
        "content": "This is a serial novel written by a very good author about a Home away from home this is to add some content to the blog",
        "created_at": datetime.now(),
        "updated_at": ""
    },
    {   
        "id": 2,
        "author": "Prospa  Ops",
        "title": "God is Good",
        "content": "A devotional written by the author for daily study and religious content built with fastapi",
        "created_at": datetime.now(),
        "updated_at": " "
    },
    {
        "id": 3,
        "author": "Damelson Vincent",
        "title": "Power over Fear",
        "content": "The chronicle of a developer who never writes but read and debugs, I dont even know what that means here",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

]


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": exc.status_code, "detail": exc.detail, "title": f"Error {exc.status_code}"},
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse(
        request,
        "error.html",
        {"status_code": 500, "detail": None, "title": "Server Error"},
        status_code=500,
    )


# catching exceptions with starlette
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

# Validation error handler 
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("api"):
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


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": post, "title": "Home"})



@app.get("/posts/{post_id}", include_in_schema=False, name="post")
def get_post_pages(post_id: int, request: Request):
    for p in post:
        if p.get("id") == post_id:
            return templates.TemplateResponse(
                request, 
                "post.html", 
                {"post": p, "title": p["title"][:50]})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not Found")



@app.get("/api/posts/{post_id}")
def get_posts(post_id: int) -> dict:
    for posts in post:
        if posts.get("id") == post_id:
            return posts
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not Found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)








