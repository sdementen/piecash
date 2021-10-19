import uuid

from sqlalchemy import Column, VARCHAR, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relation, foreign, object_session

from ._common import CallableList
from .kvp import DictWrapper, Slot
from .sa_extra import DeclarativeBase


class DeclarativeBaseGuid(DictWrapper, DeclarativeBase):
    __abstract__ = True

    #: the unique identifier of the object
    guid = Column(
        "guid",
        VARCHAR(length=32),
        primary_key=True,
        nullable=False,
        default=lambda: uuid.uuid4().hex,
    )

    @declared_attr
    def slots(cls):
        rel = relation(
            "Slot",
            primaryjoin=foreign(Slot.obj_guid) == cls.guid,
            cascade="all, delete-orphan",
            collection_class=CallableList,
        )

        return rel
