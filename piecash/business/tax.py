import uuid
from sqlalchemy import Column, VARCHAR, BIGINT, INTEGER, ForeignKey
from sqlalchemy.orm import relation
from piecash._common import CallableList, hybrid_property_gncnumeric
from piecash._declbase import DeclarativeBaseGuid
from piecash.sa_extra import DeclarativeBase

__author__ = 'sdementen'


class Taxtable(DeclarativeBaseGuid):
    __tablename__ = 'taxtables'

    __table_args__ = {}

    # column definitions
    guid = Column('guid', VARCHAR(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)
    name = Column('name', VARCHAR(length=50), nullable=False)
    refcount = Column('refcount', BIGINT(), nullable=False)
    invisible = Column('invisible', INTEGER(), nullable=False)
    parent_guid = Column('parent', VARCHAR(length=32), ForeignKey('taxtables.guid'))

    # relation definitions
    entries = relation('TaxtableEntry',
                       back_populates='taxtable',
                       cascade='all, delete-orphan',
                       collection_class=CallableList,
    )
    children = relation('Taxtable',
                        back_populates='parent',
                        cascade='all, delete-orphan',
                        collection_class=CallableList,
    )
    parent = relation('Taxtable',
                      back_populates='children',
                      remote_side=guid,
    )


class TaxtableEntry(DeclarativeBase):
    __tablename__ = 'taxtable_entries'

    __table_args__ = {'sqlite_autoincrement': True}

    # column definitions
    id = Column('id', INTEGER(), primary_key=True, nullable=False)
    taxtable_guid = Column('taxtable', VARCHAR(length=32),
                           ForeignKey('taxtables.guid'), nullable=False)
    account_guid = Column('account', VARCHAR(length=32), ForeignKey('accounts.guid'), nullable=False)
    _amount_num = Column('amount_num', BIGINT(), nullable=False)
    _amount_denom = Column('amount_denom', BIGINT(), nullable=False)
    amount = hybrid_property_gncnumeric(_amount_num, _amount_denom)
    type = Column('type', INTEGER(), nullable=False)

    # relation definitions
    taxtable = relation('Taxtable', back_populates='entries')
    account = relation('Account')