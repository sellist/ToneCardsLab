from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func
from datetime import datetime
from uuid import UUID

from .database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseDAO(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    abc dao with some common CRUD operations.
    """

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def create(self, obj_in: CreateSchemaType) -> ModelType:
        if isinstance(obj_in, dict):
            obj_data = obj_in
        elif hasattr(obj_in, 'model_dump'):
            obj_data = obj_in.model_dump()
        elif hasattr(obj_in, 'dict'):
            obj_data = obj_in.dict()
        else:
            obj_data = obj_in

        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_id(self, id: UUID) -> Optional[ModelType]:
        stmt = select(self.model).where(self._get_id_column() == id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        stmt = select(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    stmt = stmt.where(getattr(self.model, key) == value)

        if order_by:
            if order_by.startswith('-'):
                stmt = stmt.order_by(getattr(self.model, order_by[1:]).desc())
            else:
                stmt = stmt.order_by(getattr(self.model, order_by))

        stmt = stmt.offset(skip).limit(limit)
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_all(self) -> List[ModelType]:
        stmt = select(self.model)
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def update(
        self,
        id: UUID,
        obj_in: UpdateSchemaType
    ) -> Optional[ModelType]:
        db_obj = self.get_by_id(id)
        if not db_obj:
            return None

        if isinstance(obj_in, dict):
            obj_data = obj_in
        elif hasattr(obj_in, 'model_dump'):
            obj_data = obj_in.model_dump(exclude_unset=True)
        elif hasattr(obj_in, 'dict'):
            obj_data = obj_in.dict(exclude_unset=True)
        else:
            obj_data = obj_in

        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        if hasattr(db_obj, 'updated_at'):
            db_obj.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: UUID) -> bool:
        db_obj = self.get_by_id(id)
        if not db_obj:
            return False

        self.db.delete(db_obj)
        self.db.commit()
        return True

    def soft_delete(self, id: UUID) -> Optional[ModelType]:
        db_obj = self.get_by_id(id)
        if not db_obj:
            return None

        if not hasattr(db_obj, 'deleted_at'):
            raise AttributeError(f"{self.model.__name__} does not support soft deletes")

        db_obj.deleted_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        stmt = select(func.count()).select_from(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    stmt = stmt.where(getattr(self.model, key) == value)

        result = self.db.execute(stmt)
        return result.scalar_one()

    def exists(self, id: UUID) -> bool:

        stmt = select(func.count()).select_from(self.model).where(self._get_id_column() == id)
        result = self.db.execute(stmt)
        return result.scalar_one() > 0

    def bulk_create(self, objects: List[CreateSchemaType]) -> List[ModelType]:
        db_objects = []
        for obj_in in objects:
            if isinstance(obj_in, dict):
                obj_data = obj_in
            elif hasattr(obj_in, 'model_dump'):
                obj_data = obj_in.model_dump()
            elif hasattr(obj_in, 'dict'):
                obj_data = obj_in.dict()
            else:
                obj_data = obj_in

            db_obj = self.model(**obj_data)
            db_objects.append(db_obj)

        self.db.add_all(db_objects)
        self.db.commit()

        for db_obj in db_objects:
            self.db.refresh(db_obj)

        return db_objects

    def bulk_delete(self, ids: List[UUID]) -> int:
        stmt = delete(self.model).where(self._get_id_column().in_(ids))
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def _get_id_column(self):
        return list(self.model.__table__.primary_key.columns)[0]

    def refresh(self, obj: ModelType) -> ModelType:
        self.db.refresh(obj)
        return obj

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def flush(self) -> None:
        self.db.flush()

