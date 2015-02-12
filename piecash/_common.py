from decimal import Decimal

from sqlalchemy import Column, VARCHAR, INTEGER, cast, Float, DECIMAL
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.hybrid import hybrid_property

from .sa_extra import DeclarativeBase, _Date, long


class GnucashException(Exception):
    pass


class GncNoActiveSession(GnucashException):
    pass


class GncValidationError(GnucashException):
    pass


class Recurrence(DeclarativeBase):
    __tablename__ = 'recurrences'

    __table_args__ = {'sqlite_autoincrement': True}

    # column definitions
    id = Column('id', INTEGER(), primary_key=True, nullable=False)
    obj_guid = Column('obj_guid', VARCHAR(length=32),nullable=False)
    recurrence_mult = Column('recurrence_mult', INTEGER(), nullable=False)
    recurrence_period_type = Column('recurrence_period_type', VARCHAR(length=2048), nullable=False)
    recurrence_period_start = Column('recurrence_period_start', _Date(), nullable=False)
    recurrence_weekend_adjust = Column('recurrence_weekend_adjust', VARCHAR(length=2048), nullable=False)

    # relation definitions
    # added from the DeclarativeBaseGUID object (as linked from different objects like the slots)
    def __repr__(self):
        return "{}*{} from {} [{}]".format(self.recurrence_period_type,self.recurrence_mult,
                                           self.recurrence_period_start, self.recurrence_weekend_adjust)



class Address(object):
    _address_fields = "addr1 addr2 addr3 addr4 email fax name phone".split()

    def __init__(self, *args):
        for fld, val in zip(Address._address_fields, args):
            setattr(self, fld, val)

    def __composite_values__(self):
        return tuple(self)

    def __eq__(self, other):
        return isinstance(other, Address) and all(getattr(other, fld) == getattr(self, fld) for fld in Address._address_fields)

    def __ne__(self, other):
        return not self.__eq__(other)


def hybrid_property_gncnumeric(num_col, denom_col):
    """Return an hybrid_property handling a Decimal represented by a numerator and a denominator column.
    It assumes the python field related to the sqlcolumn is named as _sqlcolumn.

    :type num_col: sqlalchemy.sql.schema.Column
    :type denom_col: sqlalchemy.sql.schema.Column
    :return: sqlalchemy.ext.hybrid.hybrid_property
    """
    num_name, denom_name = "_{}".format(num_col.name), "_{}".format(denom_col.name)
    name = num_col.name.split("_")[0]
    def fset(self, d):
        if d is None:
            num, denom = None, None
        else:
            if isinstance(d, tuple):
                d = Decimal(d[0]) / d[1]
            elif isinstance(d, (float, int, long, str)):
                d = Decimal(d)
            assert isinstance(d, Decimal)

            sign, digits, exp = d.as_tuple()
            denom = 10 ** max(-exp, 0)

            # print num_name, denom,
            denom_basis = getattr(self, "{}_basis".format(denom_name), None)
            if denom_basis is not None:
                # print "got a basis for ", self, denom_basis
                denom = denom_basis
            # print denom
            num = int(d * denom)

        setattr(self, num_name, num)
        setattr(self, denom_name, denom)


    def fget(self):
        num, denom = getattr(self, num_name), getattr(self, denom_name)
        if num is None:
            return
        else:
            return Decimal(num) / denom

    def expr(cls):
        # todo: cast into Decimal for postgres and for sqlite (for the latter, use sqlite3.register_converter ?)
        return (cast(num_col, Float) / denom_col).label(name)

    return hybrid_property(
        fget=fget,
        fset=fset,
        expr=expr,
    )


class CallableList(list):
    """
    A simple class (inherited from list) allowing to retrieve a given list element with a filter on an attribute.

    It can be used as the collection_class of a sqlalchemy relationship or to wrap any list (see examples
    in :class:`piecash.core.session.GncSession`)
    """
    def __call__(self, **kwargs):
        """
        Return the first element of the list that has attributes matching the kwargs dict. The `get` method is
        an alias for this method.

        To be used as::

            l(mnemonic="EUR", namespace="CURRENCY")
        """
        for obj in self:
            for k, v in kwargs.items():
                if getattr(obj, k) != v:
                    break
            else:
                return obj
        else:
            raise KeyError("Could not find object with {} in {}".format(kwargs, self))

    get = __call__


class GncImbalanceError(GncValidationError):
    pass