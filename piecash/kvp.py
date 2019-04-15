import datetime
import decimal
import sys
import uuid
from enum import Enum
from importlib import import_module

from sqlalchemy import Column, VARCHAR, INTEGER, REAL, BIGINT, types, event, Index
from sqlalchemy.orm import relation, foreign, object_session, backref

from ._common import CallableList
from ._common import hybrid_property_gncnumeric
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
    list: KVP_Type.KVP_TYPE_GLIST,
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
    KVP_Type.KVP_TYPE_GLIST: 'guid',
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
        for sl in self.slots:
            if sl.name == key:
                return True
        else:
            return False

    def __getitem__(self, key):
        assert not isinstance(key, int), \
            "You are accessing slots with an integer (={}) while a string is expected".format(key)
        keys = key.split("/", 1)
        key = keys[0]
        for sl in self.slots:
            if sl.name == key:
                break
        else:
            raise KeyError("No slot exists with name '{}'".format(key))
        if len(keys) > 1:
            return sl[keys[1]]
        else:
            return sl  # .value

    def __setitem__(self, key, value):
        keys = key.split("/", 1)
        key = keys[0]
        for sl in self.slots:
            if sl.name == key:
                break
        else:
            # new key
            if len(keys) > 1:
                if isinstance(self, SlotFrame):
                    sf = SlotFrame(name=self._name + "/" + key,
                                   obj_guid=self.guid_val)
                else:
                    sf = SlotFrame(name=key,
                                   obj_guid=self.guid)
                sf[keys[1]] = value
                self.slots.append(sf)
            else:
                self.slots.append(slot(parent=self, name=key, value=value))

            return

        if len(keys) > 1:
            sl[keys[1]] = value
            return
        # assign if type is correct
        if isinstance(value, sl._python_type):
            sl.value = value
        else:
            raise TypeError("Type of '{}' is not one of {}".format(value, sl._python_type))

    def __delitem__(self, key):
        if isinstance(key, slice):
            # delete all
            del self.slots[key]
            return
        keys = key.split("/", 1)
        for i, sl in enumerate(self.slots):
            if sl.name == keys[0]:
                break
        else:
            raise KeyError("No slot exists with name '{}'".format(key))
        if len(keys) > 1:
            del sl[keys[1]]
        else:
            del self.slots[i]

    def iteritems(self):
        for sl in self.slots:
            yield sl.name, sl

    def get(self, key, default=None):
        try:
            return self[key].value
        except KeyError:
            return default


class Slot(DeclarativeBase):
    __tablename__ = 'slots'

    __table_args__ = (
        Index('slots_guid_index', 'obj_guid'),
        {'sqlite_autoincrement': True, }
    )

    # column definitions
    id = Column('id', INTEGER(), primary_key=True, nullable=False, autoincrement=True)
    obj_guid = Column('obj_guid', VARCHAR(length=32), nullable=False)
    _name = Column('name', VARCHAR(length=4096), nullable=False)

    @property
    def name(self):
        if self._name:
            return self._name.split("/")[-1]
        else:
            return self._name

    @name.setter
    def name(self, value):
        self._name = value

    slot_type = Column('slot_type', SlotType(), nullable=False)

    __mapper_args__ = {
        'polymorphic_on': slot_type,
    }

    def __init__(self, name, value=None, obj_guid=None):
        self.name = name
        if value is not None:
            self.value = value
        if obj_guid is not None:
            self.obj_guid = obj_guid

    def __str__(self):
        return "<{} {}={!r}>".format(self.__class__.__name__, self.name, self.value)


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

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.name == other.name
                and self.value == other.value
                )


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
SlotString = define_simpleslot(postfix="String",
                               pytype=(str,),
                               KVPtype=KVP_Type.KVP_TYPE_STRING,
                               field="string_val",
                               col_type=VARCHAR(length=4096),
                               col_default=None,
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


class SlotFrame(DictWrapper, Slot):
    __mapper_args__ = {
        'polymorphic_identity': KVP_Type.KVP_TYPE_FRAME
    }
    _python_type = (dict,)

    guid_val = Column('guid_val', VARCHAR(length=32))

    slots = relation('Slot',
                     primaryjoin=foreign(Slot.obj_guid) == guid_val,
                     cascade='all, delete-orphan',
                     collection_class=CallableList,
                     single_parent=True,
                     backref=backref("parent", remote_side=guid_val),

                     )

    @property
    def value(self):
        # convert to dict
        return {sl.name: sl.value for sl in self.slots}

    @value.setter
    def value(self, value):
        self.slots = [slot(parent=self, name=k, value=v) for k, v in value.items()]

    def __init__(self, **kwargs):
        self.guid_val = uuid.uuid4().hex
        super(SlotFrame, self).__init__(**kwargs)


class SlotList(SlotFrame):
    __mapper_args__ = {
        'polymorphic_identity': KVP_Type.KVP_TYPE_GLIST
    }
    _python_type = (list,)

    @property
    def value(self):
        # convert to dict
        return [sl.value for sl in self.slots]

    @value.setter
    def value(self, value):
        self.slots = [slot(parent=self, name=str(i), value=v) for i, v in enumerate(value)]

    def __init__(self, **kwargs):
        self.guid_val = uuid.uuid4().hex
        super(SlotFrame, self).__init__(**kwargs)


@event.listens_for(SlotFrame.slots, 'remove')
def remove_slot(target, value, initiator):
    s = object_session(value)
    if value in s.new:
        s.expunge(value)
    else:
        s.delete(value)


class SlotGUID(SlotFrame):
    __mapper_args__ = {
        'polymorphic_identity': KVP_Type.KVP_TYPE_GUID
    }
    _python_type = (DeclarativeBase,)

    # add
    _mapping_name_class = {
        'from-sched-xaction': 'piecash.core.transaction.ScheduledTransaction',
        'account': 'piecash.core.account.Account',
        'invoice-guid': 'piecash.business.invoice.Invoice',
        'peer_guid': 'piecash.core.transaction.Split',
        'gains-split': 'piecash.core.transaction.Split',
        'gains-source': 'piecash.core.transaction.Split',
        'default-currency': 'piecash.core.commodity.Commodity',
    }

    @property
    def Class(self):
        name, guid = self.name, self.guid_val
        if name.startswith('CURRENCY::'):
            # handle capital gain account
            class_to_retrieve = 'piecash.core.account.Account'
        else:
            class_to_retrieve = self._mapping_name_class.get(name, None)
            if class_to_retrieve is None:
                raise ValueError(
                    "Smart retrieval of GUID slot with name '{}' is not yet supported. "
                    "Need to retrieve proper object type in kvp module "
                    "(add in SlotGUID._mapping_name_class)".format(name))
        class_module, class_name = class_to_retrieve.rsplit('.', 1)
        mod = import_module(class_module)
        Class = getattr(mod, class_name)
        return Class

    @property
    def value(self):
        return object_session(self).query(self.Class).filter_by(guid=self.guid_val).one()

    @value.setter
    def value(self, value):
        assert isinstance(value, self.Class)
        self.guid_val = value.guid


def get_all_subclasses(cls):
    all_subclasses = []

    direct_subclasses = cls.__subclasses__()

    all_subclasses.extend(direct_subclasses)

    for subclass in direct_subclasses:
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def slot(parent, name, value):
    if isinstance(parent, SlotFrame):
        name = parent._name + "/" + name
        guid_parent = parent.guid_val
    else:
        guid_parent = parent.guid

    # handle datetime before others (as otherwise can be mixed with date)
    if isinstance(value, datetime.datetime):
        return SlotTime(name=name, value=value, obj_guid=guid_parent)

    for cls in get_all_subclasses(Slot):
        if isinstance(value, cls._python_type) and cls != SlotFrame and cls != SlotList:
            return cls(name=name, value=value, obj_guid=guid_parent)

    if isinstance(value, dict):
        # transform a dict to Frame/Slots
        sf = SlotFrame(name=name, obj_guid=guid_parent)
        for k, v in value.items():
            sl = slot(parent=sf, name=k, value=v)
            sl.parent = sf
        return sf

    if isinstance(value, list):
        # transform a list to List/Slots
        sf = SlotList(name=name)
        for i, v in enumerate(value):
            sl = slot(parent=sf, name=str(i), value=v)
            sl.parent = sf
        return sf

    raise ValueError("Cannot handle type of '{}'".format(value))


class SlotNumeric(Slot):
    __mapper_args__ = {
        'polymorphic_identity': KVP_Type.KVP_TYPE_NUMERIC
    }
    _python_type = (tuple, decimal.Decimal)

    _numeric_val_num = Column('numeric_val_num', BIGINT(), nullable=True, default=0)
    _numeric_val_denom = Column('numeric_val_denom', BIGINT(), nullable=True, default=1)
    value = hybrid_property_gncnumeric(_numeric_val_num, _numeric_val_denom)


SlotDate = define_simpleslot(postfix="Date",
                             pytype=(datetime.date,),
                             KVPtype=KVP_Type.KVP_TYPE_GDATE,
                             field="gdate_val",
                             col_type=_Date(),
                             col_default=None,
                             )
