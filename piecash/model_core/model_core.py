from sqlalchemy import Column, INTEGER, VARCHAR, Table

from ..sa_extra import DeclarativeBase


gnclock = Table(u'gnclock', DeclarativeBase.metadata,
                Column('hostname', VARCHAR(length=255)),
                Column('pid', INTEGER()),
)


class Version(DeclarativeBase):
    __tablename__ = 'versions'

    __table_args__ = {}

    # column definitions
    table_name = Column('table_name', VARCHAR(length=50), primary_key=True, nullable=False)
    table_version = Column('table_version', INTEGER(), nullable=False)

    # relation definitions
    # none

    def __repr__(self):
        return "Version<{}={}>".format(self.table_name, self.table_version)













