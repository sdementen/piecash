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


    def __init__(self, *args, **kwargs):
        """A simple constructor that allows initialization from kwargs.

        Sets attributes on the constructed instance using the names and
        values in ``kwargs``.

        Only keys that are present as
        attributes of the instance's class are allowed. These could be,
        for example, any mapped columns or relationships.
        """
        cls_ = type(self)
        key_rel = {rel.key: rel.mapper.class_ for rel in inspect(cls_).relationships}

        for k, v in kwargs.items():
            attr = getattr(cls_, k)
            # if the field is a relation and the value is a string, replace the string by the lookup
            if isinstance(v, str) and k in key_rel:
                v = key_rel[k].lookup(v)
            setattr(self, k, v)


    def get_session(self):
        # return the sa session of the object
        return object_session(self)

    @property
    def slot_collection(self):
        return self.slots