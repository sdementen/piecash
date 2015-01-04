import uuid

from sqlalchemy import Column, VARCHAR, event, inspect
from sqlalchemy.orm import relation, foreign, object_session

from .kvp import DictWrapper, Slot
from ._common import CallableList
from .sa_extra import DeclarativeBase


class DeclarativeBaseGuid(DictWrapper, DeclarativeBase):
    __abstract__ = True

    #: the unique identifier of the object
    guid = Column('guid', VARCHAR(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)

    # set the relation to the slots table (KVP)
    @classmethod
    def __declare_last__(cls):
        # do not do it on the DeclarativeBaseGuid as it is an abstract class
        if cls == DeclarativeBaseGuid:
            return

        cls.slots = relation('Slot',
                             primaryjoin=foreign(Slot.obj_guid) == cls.guid,
                             cascade='all, delete-orphan',
                             collection_class=CallableList,
        )

        # assign id of slot when associating to object
        @event.listens_for(cls.slots, "remove")
        def my_append_listener_slots(target, value, initiator):
            s = object_session(value)
            if s:
                if value in s.new:
                    s.expunge(value)
                else:
                    s.delete(value)

    def get_session(self):
        # return the sa session of the object
        return object_session(self)

