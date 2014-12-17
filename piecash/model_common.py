import uuid

from sqlalchemy import Column, VARCHAR, inspect, event, INTEGER
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import object_session, relation, foreign

from .kvp import DictWrapper, Slot
from piecash.sa_extra import _Date
from .sa_extra import DeclarativeBase, CallableList


class DeclarativeBaseGuid(DictWrapper, DeclarativeBase):
    __abstract__ = True


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

        try:
            # if there is an active session, add the object to it
            get_active_session().add(self)
        except GncNoActiveSession:
            pass

    @classmethod
    def lookup(cls, name):
        try:
            s = get_active_session()
        except GncNoActiveSession:
            raise GncNoActiveSession(
                "No active session is available to lookup a {} = '{}'. Please use a 'with book:' block to set an active session".format(
                    cls.__name__, name))

        return s.query(cls).filter(cls.lookup_key == name).one()

    def get_session(self):
        # return the sa session of the object
        return object_session(self)

    @property
    def slot_collection(self):
        return self.slots


        # @validates('readonly1', 'readonly2')
        # def _write_once(self, key, value):
        # existing = getattr(self, key)
        # if existing is not None:
        #         raise ValueError("Field '%s' is write-once" % key)
        #     return value


class GnucashException(Exception):
    pass


class GncNoActiveSession(GnucashException):
    pass


class GncValidationError(GnucashException):
    pass


# module variable to be used with the context manager "with book:"
# this variable can then be used in the code to retrieve the "active" session
_default_session = []


def is_active_session():
    return len(_default_session) != 0


def get_active_session():
    # return the active session enabled thanks to a 'with book' context manager
    # throw an exception if no active session
    try:
        return _default_session[-1]
    except IndexError:
        raise GncNoActiveSession(
            "No active session is available. Please use a 'with book:' block to set an active session")


class Recurrence(DeclarativeBase):
    __tablename__ = 'recurrences'

    __table_args__ = {}

    # column definitions
    id = Column('id', INTEGER(), primary_key=True, nullable=False)
    obj_guid = Column('obj_guid', VARCHAR(length=32), nullable=False)
    recurrence_mult = Column('recurrence_mult', INTEGER(), nullable=False)
    recurrence_period_start = Column('recurrence_period_start', _Date(), nullable=False)
    recurrence_period_type = Column('recurrence_period_type', VARCHAR(length=2048), nullable=False)
    recurrence_weekend_adjust = Column('recurrence_weekend_adjust', VARCHAR(length=2048), nullable=False)

    # relation definitions
    # added from the DeclarativeBaseGUID object (as linked from different objects like the slots
    def __repr__(self):
        return "{}/{} from {} [{}]".format(self.recurrence_mult, self.recurrence_period_type,
                                           self.recurrence_period_start, self.recurrence_weekend_adjust)