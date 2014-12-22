from sqlalchemy import Column, VARCHAR, ForeignKey
from sqlalchemy.orm import relation, backref

from ..model_declbase import DeclarativeBaseGuid


class Book(DeclarativeBaseGuid):
    __tablename__ = 'books'

    __table_args__ = {}

    # column definitions
    root_account_guid = Column('root_account_guid', VARCHAR(length=32),
                               ForeignKey('accounts.guid'), nullable=False)
    root_template_guid = Column('root_template_guid', VARCHAR(length=32),
                                ForeignKey('accounts.guid'), nullable=False)

    # relation definitions
    root_account = relation('Account', foreign_keys=[root_account_guid],
                            backref=backref('book', cascade='all, delete-orphan', uselist=False))
    root_template = relation('Account', foreign_keys=[root_template_guid])



