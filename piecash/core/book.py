from sqlalchemy import Column, VARCHAR, ForeignKey
from sqlalchemy.orm import relation

from .._declbase import DeclarativeBaseGuid


class Book(DeclarativeBaseGuid):
    """
    A Book represents an accounting book. A new GnuCash document contains only a single Book .

    Attributes:
        root_account (:class:`piecash.core.account.Account`): the root account of the book
        root_template (:class:`piecash.core.account.Account`): the root template of the book (usage not yet clear...)
        uri (str): connection string of the book (set by the GncSession when accessing the book)
    """
    __tablename__ = 'books'

    __table_args__ = {}

    # column definitions
    root_account_guid = Column('root_account_guid', VARCHAR(length=32),
                               ForeignKey('accounts.guid'), nullable=False)
    root_template_guid = Column('root_template_guid', VARCHAR(length=32),
                                ForeignKey('accounts.guid'), nullable=False)

    # relation definitions
    root_account = relation('Account',
                            back_populates='book',
                            foreign_keys=[root_account_guid],
    )
    root_template = relation('Account',
                             foreign_keys=[root_template_guid])

    def __init__(self, root_account, root_template):
        self.root_account = root_account
        self.root_template = root_template

    def __repr__(self):
        return "<Book {}>".format(self.uri)