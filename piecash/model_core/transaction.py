from collections import defaultdict
from decimal import Decimal

from sqlalchemy import Column, VARCHAR, ForeignKey, BIGINT, event
from sqlalchemy.orm import relation, backref, validates
from sqlalchemy.orm.base import instance_state
from sqlalchemy.orm.exc import NoResultFound

from ..model_common import DeclarativeBaseGuid, GncValidationError
from .book import Book
from .account import Account
from ..sa_extra import _DateTime, CallableList, Session, hybrid_property_gncnumeric, mapped_to_slot_property

"""
Examples of transaction and splits (with value and quantity) for several transactions,
some mono-currency (in default or foreign currency), some multi-currency

Commodity<CURRENCY:EUR>    salary
    [Commodity<CURRENCY:EUR>] -1000 / -1000 for Account<Income>
    [Commodity<CURRENCY:EUR>] 1000 / 1000 for Account<Assets:Current Assets:Checking Account>
Commodity<CURRENCY:EUR>    transfert to US account
    [Commodity<CURRENCY:EUR>] -400 / -400 for Account<Assets:Current Assets:Checking Account>
    [Commodity<CURRENCY:USD>] 400 / 448.15 for Account<Assets:Current Assets:CheckAcc USD>
    [Commodity<CURRENCY:USD>] -400 / -448.15 for Account<Trading:CURRENCY:USD>
    [Commodity<CURRENCY:EUR>] 400 / 400 for Account<Trading:CURRENCY:EUR>
Commodity<CURRENCY:EUR>    other transfer + expense
    [Commodity<CURRENCY:EUR>] -210 / -210 for Account<Assets:Current Assets:Checking Account>
    [Commodity<CURRENCY:USD>] 182.85 / 213.21 for Account<Assets:Current Assets:CheckAcc USD>
    [Commodity<CURRENCY:USD>] -182.85 / -213.21 for Account<Trading:CURRENCY:USD>
    [Commodity<CURRENCY:EUR>] 182.85 / 182.85 for Account<Trading:CURRENCY:EUR>
    [Commodity<CURRENCY:EUR>] 17.15 / 17.15 for Account<Expenses>
    [Commodity<CURRENCY:EUR>] 10 / 10 for Account<Imbalance-EUR>
Commodity<CURRENCY:USD>    bonus
    [Commodity<CURRENCY:USD>] -150 / -150 for Account<Income:income in usd>
    [Commodity<CURRENCY:USD>] 150 / 150 for Account<Assets:Current Assets:CheckAcc USD>
Commodity<CURRENCY:USD>    retransfer
    [Commodity<CURRENCY:USD>] -100 / -100 for Account<Assets:Current Assets:CheckAcc USD>
    [Commodity<CURRENCY:EUR>] 100 / 90 for Account<Assets:Current Assets:Checking Account>
    [Commodity<CURRENCY:EUR>] -100 / -90 for Account<Trading:CURRENCY:EUR>
    [Commodity<CURRENCY:USD>] 100 / 100 for Account<Trading:CURRENCY:USD>
Commodity<CURRENCY:CAD>    cross CAD to USD transfer
    [Commodity<CURRENCY:CAD>] 30 / 30 for Account<Assets:Current Assets:CheckAcc CAD>
    [Commodity<CURRENCY:USD>] -30 / -26.27 for Account<Assets:Current Assets:CheckAcc USD>
    [Commodity<CURRENCY:USD>] 30 / 26.27 for Account<Trading:CURRENCY:USD>
    [Commodity<CURRENCY:CAD>] -30 / -30 for Account<Trading:CURRENCY:CAD>
Commodity<CURRENCY:USD>    cross CAD to USD transfer (initiated from USD account)
    [Commodity<CURRENCY:USD>] -26.27 / -26.27 for Account<Assets:Current Assets:CheckAcc USD>
    [Commodity<CURRENCY:CAD>] 26.27 / 30 for Account<Assets:Current Assets:CheckAcc CAD>
    [Commodity<CURRENCY:CAD>] -26.27 / -30 for Account<Trading:CURRENCY:CAD>
    [Commodity<CURRENCY:USD>] 26.27 / 26.27 for Account<Trading:CURRENCY:USD>
    """


class Split(DeclarativeBaseGuid):
    __tablename__ = 'splits'

    __table_args__ = {}

    # column definitions
    account_guid = Column('account_guid', VARCHAR(length=32), ForeignKey('accounts.guid'), nullable=False, index=True)
    action = Column('action', VARCHAR(length=2048), nullable=False, default="")
    lot_guid = Column('lot_guid', VARCHAR(length=32), ForeignKey('lots.guid'))
    memo = Column('memo', VARCHAR(length=2048), nullable=False, default="")

    _quantity_denom = Column('quantity_denom', BIGINT(), nullable=False)
    _quantity_denom_basis = None
    _quantity_num = Column('quantity_num', BIGINT(), nullable=False)
    quantity = hybrid_property_gncnumeric(_quantity_num, _quantity_denom)

    reconcile_date = Column('reconcile_date', _DateTime())
    reconcile_state = Column('reconcile_state', VARCHAR(length=1), nullable=False, default="n")
    tx_guid = Column('tx_guid', VARCHAR(length=32), ForeignKey('transactions.guid'), nullable=False, index=True)

    _value_denom = Column('value_denom', BIGINT(), nullable=False)
    _value_denom_basis = None
    _value_num = Column('value_num', BIGINT(), nullable=False)
    value = hybrid_property_gncnumeric(_value_num, _value_denom)

    # relation definitions
    account = relation('Account', backref=backref('splits',
                                                  cascade='all, delete-orphan',
                                                  collection_class=CallableList,
    ))

    lot = relation('Lot', backref=backref('splits',
                                          cascade='all, delete-orphan',
                                          collection_class=CallableList,
    ))

    def __repr__(self):
        try:
            cur = self.transaction.currency.mnemonic
            acc = self.account
            com = acc.commodity.mnemonic
            if cur==com:
                return "<Split {} {} {}>".format(acc,
                                                   self.value, cur)
            else:
                return "<Split {} {} {} [{} {}]>".format(acc,
                                                   self.value, cur,
                                                   self.quantity, com)
        except AttributeError:
            return "<Split {}>".format(self.account)

    @validates("transaction", "account")
    def set_denom_basis(self, key, value):
        if value is None:
            return value
        if "transaction" == key:
            self._value_denom_basis = value.currency.fraction
            self.value = self.value
            trx = value
            acc = self.account
        if "account" == key:
            self._quantity_denom_basis = value.commodity_scu
            self.quantity = self.quantity
            trx = self.transaction
            acc = value

        if trx and acc:
            if trx.currency == acc.commodity:
                self.quantity = self.value
                # if the quantity has different rounding that value, then reassign the quantity to the value
                if self.quantity != self.value:
                    self.value = self.quantity

        return value


class Transaction(DeclarativeBaseGuid):
    __tablename__ = 'transactions'

    __table_args__ = {}

    # column definitions
    currency_guid = Column('currency_guid', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    description = Column('description', VARCHAR(length=2048))
    enter_date = Column('enter_date', _DateTime)
    num = Column('num', VARCHAR(length=2048), nullable=False, default="")
    _post_date = Column('post_date', _DateTime, index=True)
    post_date = mapped_to_slot_property(_post_date, slot_name="date-posted", slot_transform=lambda x:x.date() if x else None)

    splits = relation(Split,
                      backref=backref('transaction'),
                      single_parent=True,
                      cascade='all, delete-orphan',
                      collection_class=CallableList,
    )


    # relation definitions
    currency = relation('Commodity', backref=backref('transactions',
                                                     cascade='all, delete-orphan',
                                                     collection_class=CallableList,
    ))

    def validate(self, session):
        old = instance_state(self).committed_state

        # check same currency
        if "currency" in old and old["currency"] is not None:
            raise GncValidationError, "You cannot change the currency of a transaction once it has been set"

        # validate the splits
        if "splits" in old:
            imbalance = Decimal(0)
            c = self.currency
            for sp in self.splits:
                if sp.account.commodity != c:
                    raise GncValidationError, "Only single currency transactions are supported"

                sp.quantity = sp.value
                if sp.quantity != sp.value:
                    sp.value = sp.quantity

                imbalance += sp.value

            # if there is an imbalance, add an imbalance split to the transaction
            if imbalance:
                # retrieve imbalance account
                imb_acc_name = "Imbalance-{}".format(c.mnemonic)
                try:
                    acc = session.query(Account).filter_by(name=imb_acc_name).one()
                except NoResultFound:
                    book = session.query(Book).one()
                    acc = Account(name=imb_acc_name,
                                  parent=book.root_account,
                                  commodity=c,
                                  account_type="BANK")

                Split(value=-imbalance,
                      quantity=-imbalance,
                      account=acc,
                      transaction=self)


    # def get_imbalances(self):
    #
    #     if not (self.currency):
    #         raise ValueError, "Transaction has no currency yet"
    #
    #     imbalance_cur = Decimal(0)
    #     imbalance_comm = defaultdict(lambda: Decimal(0))
    #
    #     for sp in self.splits:
    #         if not (sp.account) or not (sp.account.commodity):
    #             raise ValueError, "Split has no commodity"
    #
    #         imbalance_comm[sp.account.commodity] += sp.quantity
    #         imbalance_cur += sp.value
    #
    #     imb_splits = []
    #     if imbalance_cur:
    #         imb_splits.append({"account_name": "Imbalance-{}".format(self.currency.mnemonic),
    #                            "commodity": self.currency,
    #                            "value": -imbalance_cur})
    #     imb_splits.extend([
    #         {"account_name": "Trading:{}:{}".format(k.namespace, k.mnemonic),
    #          "commodity": k,
    #          "value": -v}
    #         for k, v in imbalance_comm.iteritems()
    #         if v])
    #     return imb_splits
    #
    # def add_imbalance_splits(self):
    #     from .account import Account
    #
    #     imb = self.get_imbalances()
    #
    #     session = self.get_session()
    #     assert session
    #     book = session.query(Book).one()
    #     default_cur = book.root_account.commodity
    #     for sp in imb:
    #         account_name = sp["account_name"]
    #         acc = book.root_account
    #         if account_name.startswith("Imbalance"):
    #             try:
    #                 acc = acc.children.get(name=account_name)
    #             except KeyError:
    #                 acc = Account(parent=acc,
    #                               placeholder=False,
    #                               commodity=default_cur,
    #                               name=account_name,
    #                               account_type="BANK")
    #                 Split(transaction=self,
    #                       value=sp["value"],
    #                       quantity=0,
    #                       account=acc,
    #                 )
    #
    #         else:
    #             trading, namespace, mnemonic = account_name.split(":")
    #             try:
    #                 acc = acc.children.get(name=trading)
    #             except KeyError:
    #                 acc = Account(parent=acc,
    #                               placeholder=True,
    #                               commodity=default_cur,
    #                               name=trading,
    #                               account_type="TRADING")
    #             try:
    #                 acc = acc.children.get(name=namespace)
    #             except KeyError:
    #                 acc = Account(parent=acc,
    #                               placeholder=True,
    #                               commodity=default_cur,
    #                               name=namespace,
    #                               account_type="TRADING")
    #             try:
    #                 acc = acc.children.get(name=mnemonic)
    #             except KeyError:
    #                 acc = Account(parent=acc,
    #                               placeholder=False,
    #                               commodity=sp["commodity"],
    #                               name=mnemonic,
    #                               account_type="TRADING")
    #
    #             v = sp["value"]
    #             Split(transaction=self,
    #                   value=v,
    #                   quantity=v,
    #                   account=acc,
    #             )


    @classmethod
    def single_transaction(cls,
                           post_date,
                           enter_date,
                           description,
                           value,
                           from_account,
                           to_account):
        # currency is derived from "from_account" (as in GUI)
        currency = from_account.commodity
        # currency of other destination account should be identical (as only one value given)
        assert currency == to_account.commodity, "Commodities of accounts should be the same"
        tx = Transaction(
            currency=currency,
            post_date=post_date,
            enter_date=enter_date,
            description=description,
            splits=[
                Split(account=from_account, value=-value),
                Split(account=to_account, value=value),
            ])
        return tx

    # @classmethod
    # def stock_transaction(cls,
    #                       post_date,
    #                       enter_date,
    #                       description,
    #                       order,
    #                       amount,
    #                       quantity,
    #                       unit_price,
    #                       currency,
    #                       broker_account,
    #                       stock_account,
    #                       commission_account):
    #     amount100 = int(amount * 100)
    #     quantity = int(quantity)
    #     commission100 = int((amount - quantity * unit_price) * 100)
    #     assert (order == "buy" and commission100 >= 0) or (
    #         order == "sell" and commission100 <= 0), "{} {} {} {}".format(order, commission100, amount,
    #                                                                       quantity * unit_price)
    #
    #     tx = Transaction(currency=currency,
    #                      post_date=post_date,
    #                      enter_date=enter_date,
    #                      description=description,
    #                      num="",
    #                      splits=[Split(account=broker_account,
    #                                    reconcile_state='n',
    #                                    value_num=-amount100 if order == "buy" else amount100 - commission100,
    #                                    value_denom=100,
    #                                    quantity_num=-amount100 if order == "buy" else amount100 - commission100,
    #                                    quantity_denom=100,
    #                                    memo="",
    #                                    action="",
    #                      ),
    #                              Split(account=stock_account,
    #                                    reconcile_state='n',
    #                                    value_num=(+amount100 - commission100) if order == "buy" else -amount100,
    #                                    value_denom=100,
    #                                    quantity_num=quantity if order == "buy" else -quantity,
    #                                    quantity_denom=1,
    #                                    memo="",
    #                                    action="",
    #                              )] + ([Split(account=commission_account,
    #                                           reconcile_state='n',
    #                                           value_num=(commission100),
    #                                           value_denom=100,
    #                                           quantity_num=(commission100),
    #                                           quantity_denom=1,
    #                                           memo="",
    #                                           action="",
    #                      )] if unit_price else []))
    #     return tx


@event.listens_for(Session, 'before_flush')
def set_imbalance_on_transaction(session, flush_context, instances):
    # identify transactions to verify
    txs = set()
    for o in session.dirty:
        if isinstance(o, Transaction):
            txs.add(o)
        if isinstance(o, Split):
            txs.add(o.transaction)
    txs = txs.union(o for o in session.new if isinstance(o, Transaction))

    # for each transaction, validate the transaction
    for tx in txs:
        tx.validate(session)
