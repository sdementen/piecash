from __future__ import division
from xml.etree import ElementTree

from sqlalchemy import Column, VARCHAR, INTEGER, ForeignKey, BIGINT
from sqlalchemy.orm import relation

from ..model_common import DeclarativeBaseGuid
from ..sa_extra import _DateTime, hybrid_property_gncnumeric


class Commodity(DeclarativeBaseGuid):
    __tablename__ = 'commodities'

    __table_args__ = {}

    # column definitions
    cusip = Column('cusip', VARCHAR(length=2048))
    fraction = Column('fraction', INTEGER(), nullable=False, default=100)
    fullname = Column('fullname', VARCHAR(length=2048))
    mnemonic = Column('mnemonic', VARCHAR(length=2048), nullable=False)
    namespace = Column('namespace', VARCHAR(length=2048), nullable=False)
    quote_flag = Column('quote_flag', INTEGER(), nullable=False)
    quote_source = Column('quote_source', VARCHAR(length=2048))
    quote_tz = Column('quote_tz', VARCHAR(length=2048))

    # relation definitions

    def __repr__(self):
        return "Commodity<{}:{}>".format(self.namespace, self.mnemonic)

    @classmethod
    def create_from_ISO(cls, mnemonic, from_web=False):
        if not from_web:
            from .currency_ISO import ISO_currencies

            for cur in ISO_currencies:
                if cur.mnemonic == mnemonic:
                    # create the currency
                    return cls(mnemonic=cur.mnemonic,
                               fullname=cur.currency,
                               fraction=10 ** int(cur.fraction),
                               cusip=cur.cusip,
                               namespace="CURRENCY",
                               quote_flag=1,
                               quote_source="currency"
                    )
            else:
                raise ValueError("Could not find the mnemonic '{}' in the ISO table".format(mnemonic))

        else:
            # retrieve XML table with currency information
            import requests

            url = "http://www.currency-iso.org/dam/downloads/table_a1.xml"
            table = requests.get(url)

            # parse it with elementree
            root = ElementTree.fromstring(table.content)
            # and look for each currency item
            for i in root.findall(".//CcyNtry"):
                # if there is no mnemonic, skip it
                mnemonic_node = i.find("Ccy")
                if mnemonic_node is None:
                    continue
                # if the mnemonic is not the one expected, skip it
                if mnemonic_node.text != mnemonic:
                    continue
                # retreive currency info from xml
                cusip = i.find("CcyNbr").text
                fraction = 10 ** int(i.find("CcyMnrUnts").text)
                fullname = i.find("CcyNm").text
                break
            else:
                # raise error if mnemonic has not been found
                raise ValueError("Could not find the mnemonic '{}' in the table at {}".format(mnemonic, url))

            # create the currency
            return cls(mnemonic=mnemonic,
                       fullname=fullname,
                       fraction=fraction,
                       cusip=cusip,
                       namespace="CURRENCY",
                       quote_flag=1,
                       quote_source="currency"
            )


class Price(DeclarativeBaseGuid):
    __tablename__ = 'prices'

    __table_args__ = {}

    # column definitions
    commodity_guid = Column('commodity_guid', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    currency_guid = Column('currency_guid', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    date = Column('date', _DateTime, nullable=False)
    source = Column('source', VARCHAR(length=2048))
    type = Column('type', VARCHAR(length=2048))

    _value_denom = Column('value_denom', BIGINT(), nullable=False)
    _value_num = Column('value_num', BIGINT(), nullable=False)
    _value_denom_basis = None
    value = hybrid_property_gncnumeric(_value_num, _value_denom)

    # relation definitions

    commodity = relation('Commodity', foreign_keys=[commodity_guid])
    currency = relation('Commodity', foreign_keys=[currency_guid])