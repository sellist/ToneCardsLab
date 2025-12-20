"""DAO injection utilities for creating data access objects dynamically."""
import logging
from typing import Type, TypeVar, Dict, Any, Optional, Callable
from sqlalchemy.orm import Session

from ..repository.db.base import BaseDAO
from ..repository.db.models import User, Deck, Card, DeckViewer
from ..repository.db.daos import UserDAO, DeckDAO, CardDAO, DeckViewerDAO

ModelType = TypeVar("ModelType")


class DAOFactory:
    """factory for creating DAO instances dynamically."""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self._dao_cache: Dict[Type, Any] = {}

        # Registry of specialized DAO classes
        self._specialized_daos = {
            User: UserDAO,
            Deck: DeckDAO,
            Card: CardDAO,
            DeckViewer: DeckViewerDAO,
        }

    def get_dao(self, model_class: Type[ModelType]) -> BaseDAO:
        """
            factory = DAOFactory(db_session)
            card_dao = factory.get_dao(Card)
            user_dao = factory.get_dao(User)
        """
        # check cache first
        if model_class in self._dao_cache:
            return self._dao_cache[model_class]

        if model_class in self._specialized_daos:
            dao_class = self._specialized_daos[model_class]
            dao_instance = dao_class(self.db_session)
        else:
            # Create generic DAO for models without specialized implementation
            logging.warning(f"No specialized DAO for {model_class.__name__}, using GenericDAO.")
            dao_instance = GenericDAO(model_class, self.db_session)

        self._dao_cache[model_class] = dao_instance
        return dao_instance


class GenericDAO(BaseDAO):
    """Generic DAO implementation for models without specialized DAOs."""

    def __init__(self, model_class: Type[ModelType], db: Session):
        """Initialize generic DAO with model class and database session."""
        super().__init__(model_class, db)


# Global factory instance (to be initialized with db session)
_dao_factory: Optional[DAOFactory] = None


def initialize_dao_factory(db_session: Session) -> None:
    global _dao_factory
    _dao_factory = DAOFactory(db_session)


def get_dao(model_class: Type[ModelType]) -> Callable:
    """
    Decorator that injects DAO instance as class variable.

    Usage:
        @get_dao(User)
        @get_dao(Card)
        class MyService:
            def some_method(self):
                users = self.user_dao.get_all()
                cards = self.card_dao.get_all()
    """

    def decorator(cls):
        # Store the model class for deferred injection
        if not hasattr(cls, '_pending_dao_injections'):
            cls._pending_dao_injections = []
        cls._pending_dao_injections.append(model_class)

        # Only wrap __init__ once, even if multiple @get_dao decorators are used
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


def inject_dao(model_class: Type[ModelType]) -> Callable:
    """
    Explicit decorator version of get_dao for cleaner decorator syntax.

    @inject_dao(User)
    @inject_dao(Card)
    class MyService:

        # gets UserDao and CardDao injected as class variables
        users = user_dao.get_all()
        cards = card_dao.get_all()
    """
    def decorator(cls):
        """Decorator that injects DAO as class variable."""
        # Store the model class for deferred injection
        if not hasattr(cls, '_pending_dao_injections'):
            cls._pending_dao_injections = []
        cls._pending_dao_injections.append(model_class)

        # Only wrap __init__ once, even if multiple decorators are used
        if not hasattr(cls, '_dao_init_wrapped'):
            original_init = cls.__init__

            def new_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)

                # Inject DAOs after initialization
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


