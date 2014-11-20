from sqlalchemy import Column, VARCHAR, ForeignKey, INTEGER
from sqlalchemy.orm import relation, backref, validates
from piecash.kvp import KVP_Type
from piecash.model_common import DeclarativeBaseGuid


class Account(DeclarativeBaseGuid):
    __tablename__ = 'accounts'

    __table_args__ = {}

    # column definitions
    account_type = Column('account_type', VARCHAR(length=2048), nullable=False)
    code = Column('code', VARCHAR(length=2048))
    commodity_guid = Column('commodity_guid', VARCHAR(length=32), ForeignKey('commodities.guid'))
    commodity_scu = Column('commodity_scu', INTEGER(), nullable=False, default=0)
    description = Column('description', VARCHAR(length=2048))
    guid = DeclarativeBaseGuid.guid
    hidden = Column('hidden', INTEGER(), default=0)
    name = Column('name', VARCHAR(length=2048), nullable=False)
    non_std_scu = Column('non_std_scu', INTEGER(), nullable=False, default=0)
    parent_guid = Column('parent_guid', VARCHAR(length=32), ForeignKey('accounts.guid'))
    placeholder = Column('placeholder', INTEGER(), default=0)

    # relation definitions
    commodity = relation('Commodity', backref=backref('accounts', cascade='all, delete-orphan'))
    children = relation('Account',
                        backref=backref('parent', remote_side=guid),
                        cascade='all, delete-orphan',
    )

    # definition of fields accessible through the kvp system
    _kvp_slots = {
        "notes": KVP_Type.KVP_TYPE_STRING,
        "placeholder": KVP_Type.KVP_TYPE_STRING,
    }

    @validates('placeholder')
    def validate_placeholder(self, key, placeholder):
        print "validating", key, placeholder
        if placeholder:
            self.set_kvp("placeholder", "true")
            return 1
        else:
            self.del_kvp("placeholder", exception_if_not_exist=False)
            return 0


    def fullname(self):
        acc = self
        l = []
        while acc:
            l.append(acc.name)
            acc = acc.parent
        return ":".join(l[-2::-1])

    def __init__(self, **kwargs):
        # set description field to name field for convenience (if not defined)
        # kwargs.setdefault('description', kwargs['name'])

        super(Account, self).__init__(**kwargs)


    def __repr__(self):
        return "Account<{}>".format(self.fullname())