from builtins import object
import decimal
import datetime
import uuid

from enum import Enum
from past.types import basestring
from sqlalchemy import Column, VARCHAR, INTEGER, REAL, BIGINT, types, event
from sqlalchemy.orm import relation, foreign, object_session, backref

from .model_common import hybrid_property_gncnumeric
from .model_common import CallableList
from .sa_extra import _DateTime, DeclarativeBase, _Date


class KVP_Type(Enum):
    KVP_TYPE_INVALID = -1
    KVP_TYPE_GINT64 = 1
    KVP_TYPE_DOUBLE = 2
    KVP_TYPE_NUMERIC = 3
    KVP_TYPE_STRING = 4
    KVP_TYPE_GUID = 5
    KVP_TYPE_TIMESPEC = 6
    KVP_TYPE_BINARY = 7
    KVP_TYPE_GLIST = 8
    KVP_TYPE_FRAME = 9
    KVP_TYPE_GDATE = 10


pytype_KVPtype = {
    int: KVP_Type.KVP_TYPE_GINT64,
    float: KVP_Type.KVP_TYPE_DOUBLE,
    decimal.Decimal: KVP_Type.KVP_TYPE_NUMERIC,
    dict: KVP_Type.KVP_TYPE_FRAME,
    # to fill
}

KVPtype_fields = {
    KVP_Type.KVP_TYPE_GINT64: 'int64_val',
    KVP_Type.KVP_TYPE_DOUBLE: 'double_val',
    KVP_Type.KVP_TYPE_STRING: 'string_val',
    KVP_Type.KVP_TYPE_GUID: 'guid_val',
    KVP_Type.KVP_TYPE_TIMESPEC: 'timespec_val',
    KVP_Type.KVP_TYPE_GDATE: 'gdate_val',
    KVP_Type.KVP_TYPE_NUMERIC: ('numeric_val_num', 'numeric_val_denom'),
    KVP_Type.KVP_TYPE_FRAME: 'guid',
}


class SlotType(types.TypeDecorator):
    """Used to customise the DateTime type for sqlite (ie without the separators as in gnucash
    """
    impl = INTEGER

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.value

    def process_result_value(self, value, dialect):
        if value is not None:
            return KVP_Type(value)


class DictWrapper(object):
    def __contains__(self, key):
        for sl in self.slot_collection:
            if sl.name == key:
                return True
        else:
            return False


    def __getitem__(self, key):
        for sl in self.slot_collection:
            if sl.name == key:
                break
        else:
            raise KeyError("No slot exists with name '{}'".format(key))
        return sl.value

    def __setitem__(self, key, value):
        for sl in self.slot_collection:
            if sl.name == key:
                break
        else:
            self.slot_collection.append(slot(name=key, value=value))
            return
        # assign if type is correct
        if isinstance(value, sl._python_type):
            sl.value = value
        else:
            raise TypeError("Type of '{}' is not one of {}".format(value, sl._python_type))

    def __delitem__(self, key):
        for i, sl in enumerate(self.slot_collection):
            if sl.name == key:
                break
        else:
            raise KeyError("No slot exists with name '{}'".format(key))
        del self.slot_collection[i]


    def iteritems(self):
        for sl in self.slot_collection:
            yield sl.name, sl.value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


class Slot(DeclarativeBase):
    __tablename__ = 'slots'

    # column definitions
    name = Column('name', VARCHAR(length=4096), nullable=False)
    id = Column('id', INTEGER(), primary_key=True, nullable=False)
    obj_guid = Column('obj_guid', VARCHAR(length=32), nullable=False, index=True)
    slot_type = Column('slot_type', SlotType(), nullable=False)

    __mapper_args__ = {
        'polymorphic_on': slot_type,
    }

    def __repr__(self):
        return "<{} {}={} as {}>".format(self.__class__.__name__, self.name, self.value, self._python_type)
        return "<slot {}={} ({}) -> {}>".format(self.name, self.value, self.slot_type, self.obj_guid)


class SlotSimple(Slot):
    __mapper_args__ = {
        'polymorphic_identity': -1,
    }

    _python_type = ()

    @property
    def value(self):
        return getattr(self, self._field)

    @value.setter
    def value(self, value):
        setattr(self, self._field, value)


def define_simpleslot(postfix, pytype, KVPtype, field, col_type, col_default):
    cls = type(
        'Slot{}'.format(postfix),
        (SlotSimple,),
        {
            "__mapper_args__": {'polymorphic_identity': KVPtype},
            field: Column(field, col_type, default=col_default),
            "_field": field,
            "_python_type": pytype,
        }
    )
    return cls


SlotInt = define_simpleslot(postfix="Int",
                            pytype=(int,),
                            KVPtype=KVP_Type.KVP_TYPE_GINT64,
                            field="int64_val",
                            col_type=BIGINT(),
                            col_default=0,
)
SlotDouble = define_simpleslot(postfix="Double",
                               pytype=(float,),
                               KVPtype=KVP_Type.KVP_TYPE_DOUBLE,
                               field="double_val",
                               col_type=REAL(),
                               col_default=0,
)
SlotTime = define_simpleslot(postfix="Time",
                             pytype=(datetime.time,),
                             KVPtype=KVP_Type.KVP_TYPE_TIMESPEC,
                             field="timespec_val",
                             col_type=_DateTime(),
                             col_default=None,
)
SlotDate = define_simpleslot(postfix="Date",
                             pytype=(datetime.date,),
                             KVPtype=KVP_Type.KVP_TYPE_GDATE,
                             field="gdate_val",
                             col_type=_Date(),
                             col_default=None,
)
SlotString = define_simpleslot(postfix="String",
                               pytype=(basestring,),
                               KVPtype=KVP_Type.KVP_TYPE_STRING,
                               field="string_val",
                               col_type=VARCHAR(length=4096),
                               col_default=None,
)


class SlotNumeric(Slot):
    __mapper_args__ = {
        'polymorphic_identity': KVP_Type.KVP_TYPE_NUMERIC
    }
    _python_type = (tuple, decimal.Decimal)

    _numeric_val_denom = Column('numeric_val_denom', BIGINT(), nullable=False, default=1)
    _numeric_val_num = Column('numeric_val_num', BIGINT(), nullable=False, default=0)
    value = hybrid_property_gncnumeric(_numeric_val_num, _numeric_val_denom)


class SlotFrame(DictWrapper, Slot):
    __mapper_args__ = {
        'polymorphic_identity': KVP_Type.KVP_TYPE_FRAME
    }
    _python_type = (dict,)

    guid_val = Column('guid_val', VARCHAR(length=32))

    slot_collection = relation('Slot',
                               primaryjoin=foreign(Slot.obj_guid) == guid_val,
                               cascade='all, delete-orphan',
                               collection_class=CallableList,
                               backref=backref("parent", remote_side=guid_val, single_parent=True),
    )

    @property
    def value(self):
        # convert to dict
        return {sl.name: sl.value for sl in self.slot_collection}

    @value.setter
    def value(self, value):
        self.slot_collection = [slot(name=k, value=v) for k, v in value.items()]


    def __init__(self, **kwargs):
        self.guid_val = uuid.uuid4().hex
        super(SlotFrame, self).__init__(**kwargs)


@event.listens_for(SlotFrame.slot_collection, 'remove')
def remove_slot(target, value, initiator):
    s = object_session(value)
    if value in s.new:
        s.expunge(value)
    else:
        s.delete(value)


def get_all_subclasses(cls):
    all_subclasses = []

    direct_subclasses = cls.__subclasses__()

    all_subclasses.extend(direct_subclasses)

    for subclass in direct_subclasses:
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def slot(name, value):
    # handle datetime before others (as otherwise can be mixed with date)
    if isinstance(value, datetime.datetime):
        return SlotTime(name=name, value=value)

    for cls in get_all_subclasses(Slot):
        if isinstance(value, cls._python_type):
            return cls(name=name, value=value)

    if isinstance(value, dict):
        # transform a dict to Frame/Slots
        def dict2list_of_slots(dct):
            return [slot(name=k, value=v) for k, v in dct.items()]

        return slot(name=name, value=dict2list_of_slots(value))

    raise ValueError("Cannot handle type of '{}'".format(value))
