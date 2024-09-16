from sqlalchemy.orm import Session
from pydantic import BaseModel
from .models import Base as ModelBase


def add_to_db(db: Session, model: ModelBase, item_schema: BaseModel):
    db_item = model(**item_schema.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_by_id(db: Session, model: ModelBase, item_id: int):
    item = db.query(model).filter(id == item_id).first()
    return item
