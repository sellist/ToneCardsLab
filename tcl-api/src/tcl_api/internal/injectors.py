import logging
from typing import Type, TypeVar, Dict, Any, Optional, Callable
from sqlalchemy.orm import Session

from tcl_api.models.entities import User, Deck, Card, DeckViewer
from tcl_api.repository.db.base import BaseDAO
from tcl_api.repository.db.daos import UserDAO, DeckDAO, CardDAO, DeckViewerDAO

ModelType = TypeVar("ModelType")


class DAOFactory:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self._dao_cache: Dict[Type, Any] = {}

        # look in repository.db.daos for specialized DAOs, or import from wherever,
        # overrides the default GenericDAO for specific models
        self._specialized_daos = {
            User: UserDAO,
            Deck: DeckDAO,
            Card: CardDAO,
            DeckViewer: DeckViewerDAO,
        }

    def get_dao(self, model_class: Type[ModelType]) -> BaseDAO:
        if model_class in self._dao_cache:
            return self._dao_cache[model_class]

        if model_class in self._specialized_daos:
            dao_class = self._specialized_daos[model_class]
            dao_instance = dao_class(self.db_session)
        else:
            logging.warning(f"No specialized DAO for {model_class.__name__}, using GenericDAO.")
            dao_instance = GenericDAO(model_class, self.db_session)

        self._dao_cache[model_class] = dao_instance
        return dao_instance


class GenericDAO(BaseDAO):
    """Generic DAO implementation for models without specialized DAOs."""

    def __init__(self, model_class: Type[ModelType], db: Session):
        """Initialize generic DAO with model class and database session."""
        super().__init__(model_class, db)


_dao_factory: Optional[DAOFactory] = None


def initialize_dao_factory(db_session: Session) -> None:
    global _dao_factory
    _dao_factory = DAOFactory(db_session)


def get_dao(model_class: Type[ModelType]) -> Callable:
    def decorator(cls):
        if not hasattr(cls, '_pending_dao_injections'):
            cls._pending_dao_injections = []
        cls._pending_dao_injections.append(model_class)

        if not hasattr(cls, '_dao_init_wrapped'):
            original_init = cls.__init__

            def new_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)

                if _dao_factory is None:
                    raise RuntimeError("DAO factory not initialized. Call initialize_dao_factory() first.")

                for pending_model_class in cls._pending_dao_injections:
                    dao_var_name = f"{pending_model_class.__name__.lower()}_dao"
                    dao_instance = _dao_factory.get_dao(pending_model_class)
                    setattr(self, dao_var_name, dao_instance)
                    logging.info(f"Injected {dao_var_name} into {self.__class__.__name__} instance")

            cls.__init__ = new_init
            cls._dao_init_wrapped = True

        return cls

    return decorator


def get_dao_instance(model_class: Type[ModelType]) -> BaseDAO:
    if _dao_factory is None:
        raise RuntimeError("DAO factory not initialized. Call initialize_dao_factory() first.")
    return _dao_factory.get_dao(model_class)
