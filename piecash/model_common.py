import uuid
import decimal

from sqlalchemy import Column, VARCHAR, BIGINT, cast, Float, inspect, event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session, relation, foreign

from .kvp import DictWrapper, Slot
from .sa_extra import DeclarativeBase, CallableList


class DeclarativeBaseGuid(DictWrapper, DeclarativeBase):
    __abstract__ = True

    # set the relation to the slots table (KVP)
    @classmethod
    def __declare_last__(cls):
        # do not do it on the DeclarativeBaseGuid as it is an abstract class
        if cls ==DeclarativeBaseGuid:
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
            if value in s.new:
                s.expunge(value)
            else:
                s.delete(value)


    guid = Column('guid', VARCHAR(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)

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

        for k, v in kwargs.iteritems():
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
            raise GncNoActiveSession, "No active session is available to lookup a {} = '{}'. Please use a 'with book:' block to set an active session".format(
                cls.__name__, name)

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
        #     if existing is not None:
        #         raise ValueError("Field '%s' is write-once" % key)
        #     return value




class GnucashException(Exception):
    pass


class GncNoActiveSession(GnucashException):
    pass


def dict_decimal(field):
    """Create a dictionnary that can be added to the locals() of a declarative base that models
    - two BIGINT() fields with name field_denom and field_num
    - a Decimal field linked to the two previous fields and that is the one to use in python

    :param field:
    :return:
    """

    def fset(self, d):
        _, _, exp = d.as_tuple()
        self.value_denom = denom = int(d.radix() ** (-exp))
        self.value_num = int(d * denom)

    dct = {
        field + '_denom': Column(field + '_denom', BIGINT(), nullable=False),
        field + '_num': Column(field + '_num', BIGINT(), nullable=False),
        field: hybrid_property(
            fget=lambda self: decimal.Decimal(self.value_num) / decimal.Decimal(self.value_denom),
            fset=fset,
            expr=lambda cls: cast(cls.value_num, Float) / cls.value_denom,
        )
    }

    print """


    {field}_denom = Column('{field}_denom', BIGINT(), nullable=False)
    {field}_num = Column('{field}_num', BIGINT(), nullable=False)
    def fset(self, d):
        _, _, exp = d.as_tuple()
        self.{field}_denom = denom = int(d.radix() ** (-exp))
        self.{field}_num = int(d * denom)
    {field} = hybrid_property(
        fget=lambda self: decimal.Decimal(self.{field}_num) / decimal.Decimal(self.{field}_denom),
        fset=fset,
        expr=lambda cls: cast(cls.{field}_num, Float) / cls.{field}_denom,
    )
    """.format(field=field)
    return dct


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
        raise GncNoActiveSession, "No active session is available. Please use a 'with book:' block to set an active session"
