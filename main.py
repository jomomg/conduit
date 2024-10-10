import jwt
from fastapi import FastAPI, APIRouter
from .routers import profiles, users, articles
from .database import engine
from .models import Base


Base.metadata.create_all(bind=engine)


api = APIRouter()
api.include_router(users.router, tags=["users", "authentication"])
api.include_router(articles.router)
api.include_router(profiles.router)

app = FastAPI()
app.include_router(api, prefix="/api")


@app.get("/")
async def root():
    return {"message": "welcome to conduit"}
