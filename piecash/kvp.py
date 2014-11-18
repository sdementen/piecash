import decimal
from enum import Enum
from sqlalchemy import Column, VARCHAR, INTEGER, REAL, BIGINT, cast, Float
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relation, foreign
from .sa_extra import _Date, _DateTime, DeclarativeBase


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

KVP_info = {
    KVP_Type.KVP_TYPE_GINT64: 'int64_val',
    KVP_Type.KVP_TYPE_DOUBLE: 'double_val',
    KVP_Type.KVP_TYPE_STRING: 'string_val',
    KVP_Type.KVP_TYPE_GUID: 'guid_val',
    KVP_Type.KVP_TYPE_TIMESPEC: 'timespec_val',
    KVP_Type.KVP_TYPE_GDATE: 'gdate_val',
    KVP_Type.KVP_TYPE_NUMERIC: ('numeric_val_num', 'numeric_val_denom'),
}


class Slot(DeclarativeBase):
    __tablename__ = 'slots'

    __table_args__ = {}

    # column definitions
    name = Column('name', VARCHAR(length=4096), nullable=False)
    id = Column('id', INTEGER(), primary_key=True, nullable=False)
    obj_guid = Column('obj_guid', VARCHAR(length=32),nullable=False,index=True)
    slot_type = Column('slot_type', INTEGER(), nullable=False)

    double_val = Column('double_val', REAL())
    gdate_val = Column('gdate_val', _Date())
    guid_val = Column('guid_val', VARCHAR(length=32))
    int64_val = Column('int64_val', BIGINT())
    string_val = Column('string_val', VARCHAR(length=4096))
    timespec_val = Column('timespec_val', _DateTime())

    numeric_val_denom = Column('numeric_val_denom', BIGINT(), nullable=False)
    numeric_val_num = Column('numeric_val_num', BIGINT(), nullable=False)

    def __str__(self):
        return "<slot {}:{}>".format(self.name, self.string_val if self.slot_type == 4 else self.slot_type)

class KVPManager(object):
    """
    Implement logic to access KVP store

    TODO: handle frame and lists
    """
    # set the relation to the slots table (KVP)
    @classmethod
    def __declare_last__(cls):
        cls.slots = relation(Slot, primaryjoin=foreign(Slot.obj_guid)==cls.guid, cascade='all, delete-orphan')

    def get_kvp_type(self, key):
        fld_type = self._kvp_slots.get(key, None)
        if fld_type is None:
            raise ValueError, "key '{}' cannot be assigned to {}".format(key, self)
        return fld_type

    def get_kvp_slot(self, key):
        #TODO: use a query to get directly the slot instead of doing this in python (improve efficiency)
        for slot in self.slots:
            if slot.name==key:
                return slot
        else:
            # key not found
            raise KeyError, "no {} in kvp of {}".format(key, self)

    def iter_kvp(self):
        for slot in self.slots:
            yield slot.name, self.get_kvp(slot.name) #TODO: not effecient but avoid copy/paste of code

    _kvp_simple_slots = (
                KVP_Type.KVP_TYPE_DOUBLE,
                KVP_Type.KVP_TYPE_GDATE,
                KVP_Type.KVP_TYPE_GINT64,
                KVP_Type.KVP_TYPE_GUID,
                KVP_Type.KVP_TYPE_TIMESPEC,
                KVP_Type.KVP_TYPE_STRING,
        )
    def get_kvp(self, key):
        fld_type = self.get_kvp_type(key)
        slot = self.get_kvp_slot(key)

        if fld_type in self._kvp_simple_slots:
            return getattr(slot, KVP_info[fld_type])
        elif fld_type==KVP_Type.KVP_TYPE_NUMERIC:
            return getattr(slot, KVP_info[fld_type][0]), getattr(slot, KVP_info[fld_type][1])
        else:
            assert False, "type {} not yet supported".format(fld_type)

    def set_kvp(self, key, value):
        fld_type = self.get_kvp_type(key)

        try:
            # retrieve slot if it exist
            slot = self.get_kvp_slot(key)
        except KeyError:
            # or create new if it does not exist
            slot = Slot(name=key,
                        slot_type=fld_type.value)
            self.slots.append(slot)

        if fld_type in self._kvp_simple_slots:
            setattr(slot, KVP_info[fld_type], value)
        elif fld_type==KVP_Type.KVP_TYPE_NUMERIC:
            setattr(slot, KVP_info[fld_type][0], value[0])
            setattr(slot, KVP_info[fld_type][1], value[1])
        else:
            assert False, "type {} not yet supported".format(fld_type)

    def del_kvp(self, key):
        #TODO: use a query to get directly the slot instead of doing this in python (improve efficiency)
        for i, slot in enumerate(self.slots):
            if slot.name==key:
                break
        else:
            raise ValueError, "key '{}' does not exist in {}".format(key, self)
        del self.slots[i]
