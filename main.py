from typing import Annotated
from fastapi import FastAPI, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import SessionMaker, engine
from .models import Base, User, Profile
from .schemas import UserRegistration, UserOut
from .crud import add_to_db

Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db_session = SessionMaker()
    try:
        yield db_session
    finally:
        db_session.close()


@app.get("/")
async def root():
    return {"message": "welcome to conduit"}


# register user
@app.post("/api/users", response_model=UserOut)
async def register_user(
    user: Annotated[UserRegistration, Body(embed=True)], db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    new_profile = Profile(user_id=new_user.id, username=user.username)
    db.add(new_profile)
    db.commit()
    return new_user
