from collections import defaultdict
from decimal import Decimal

from sqlalchemy import Column, VARCHAR, ForeignKey, BIGINT, event
from sqlalchemy.orm import relation, backref, validates

from ..model_common import DeclarativeBaseGuid
from .book import Book
from ..sa_extra import _DateTime, CallableList, Session, hybrid_property_gncnumeric

"""
Examples of transaction and splits (with value and quantity) for several transactions,
some mono-currency (in default or foreign currency), some multi-currency

Commodity<CURRENCY:EUR>	salary
	[Commodity<CURRENCY:EUR>] -1000 / -1000 for Account<Income>
	[Commodity<CURRENCY:EUR>] 1000 / 1000 for Account<Assets:Current Assets:Checking Account>
Commodity<CURRENCY:EUR>	transfert to US account
	[Commodity<CURRENCY:EUR>] -400 / -400 for Account<Assets:Current Assets:Checking Account>
	[Commodity<CURRENCY:USD>] 400 / 448.15 for Account<Assets:Current Assets:CheckAcc USD>
	[Commodity<CURRENCY:USD>] -400 / -448.15 for Account<Trading:CURRENCY:USD>
	[Commodity<CURRENCY:EUR>] 400 / 400 for Account<Trading:CURRENCY:EUR>
Commodity<CURRENCY:EUR>	other transfer + expense
	[Commodity<CURRENCY:EUR>] -210 / -210 for Account<Assets:Current Assets:Checking Account>
	[Commodity<CURRENCY:USD>] 182.85 / 213.21 for Account<Assets:Current Assets:CheckAcc USD>
	[Commodity<CURRENCY:USD>] -182.85 / -213.21 for Account<Trading:CURRENCY:USD>
	[Commodity<CURRENCY:EUR>] 182.85 / 182.85 for Account<Trading:CURRENCY:EUR>
	[Commodity<CURRENCY:EUR>] 17.15 / 17.15 for Account<Expenses>
	[Commodity<CURRENCY:EUR>] 10 / 10 for Account<Imbalance-EUR>
Commodity<CURRENCY:USD>	bonus
	[Commodity<CURRENCY:USD>] -150 / -150 for Account<Income:income in usd>
	[Commodity<CURRENCY:USD>] 150 / 150 for Account<Assets:Current Assets:CheckAcc USD>
Commodity<CURRENCY:USD>	retransfer
	[Commodity<CURRENCY:USD>] -100 / -100 for Account<Assets:Current Assets:CheckAcc USD>
	[Commodity<CURRENCY:EUR>] 100 / 90 for Account<Assets:Current Assets:Checking Account>
	[Commodity<CURRENCY:EUR>] -100 / -90 for Account<Trading:CURRENCY:EUR>
	[Commodity<CURRENCY:USD>] 100 / 100 for Account<Trading:CURRENCY:USD>
Commodity<CURRENCY:CAD>	cross CAD to USD transfer
	[Commodity<CURRENCY:CAD>] 30 / 30 for Account<Assets:Current Assets:CheckAcc CAD>
	[Commodity<CURRENCY:USD>] -30 / -26.27 for Account<Assets:Current Assets:CheckAcc USD>
	[Commodity<CURRENCY:USD>] 30 / 26.27 for Account<Trading:CURRENCY:USD>
	[Commodity<CURRENCY:CAD>] -30 / -30 for Account<Trading:CURRENCY:CAD>
Commodity<CURRENCY:USD>	cross CAD to USD transfer (initiated from USD account)
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
    _quantity_num = Column('quantity_num', BIGINT(), nullable=False)
    quantity = hybrid_property_gncnumeric(_quantity_num, _quantity_denom)

    reconcile_date = Column('reconcile_date', _DateTime())
    reconcile_state = Column('reconcile_state', VARCHAR(length=1), nullable=False, default="n")
    tx_guid = Column('tx_guid', VARCHAR(length=32), ForeignKey('transactions.guid'), nullable=False, index=True)

    _value_denom = Column('value_denom', BIGINT(), nullable=False)
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
            return "<Split {} {} {}~{} {}>".format(self.account,
                                                   self.value, self.transaction.currency.mnemonic,
                                                   self.quantity, self.account.commodity.mnemonic)
        except AttributeError:
            return "<Split {}>".format(self.account)


    # @validates("_value_num", "_quantity_num")
    # def sync_value_amount(self, key, value):
    # """If value or quantity is changed and that
    # """
    # if key == "_value_num":
    # if self.transaction and self.account:
    # if self.transaction.currency == self.account.commodity:
    # if self.quantity != value:
    # print self.quantity, value
    # self.quantity = value
    #     if key == "_quantity_num":
    #         if self.transaction and self.account:
    #             if self.transaction.currency == self.account.commodity:
    #                 if self.value != value:
    #                     print self.value, value
    #                     self.value = value
    #     return value

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

    @property
    def post_date(self):
        return self._post_date

    @post_date.setter
    def post_date(self, value):
        if value:
            self["date-posted"] = value
        else:
            del self["date_posted"]
        self._post_date = value

    splits = relation(Split,
                      backref='transaction',
                      cascade='all, delete-orphan',
                      collection_class=CallableList,
    )


    # relation definitions
    currency = relation('Commodity', backref=backref('transactions',
                                                     cascade='all, delete-orphan',
                                                     collection_class=CallableList,
    ))


    def get_imbalances(self):

        if not (self.currency):
            raise ValueError, "Transaction has no currency yet"

        imbalance_cur = Decimal(0)
        imbalance_comm = defaultdict(lambda: Decimal(0))

        for sp in self.splits:
            if not (sp.account) or not (sp.account.commodity):
                raise ValueError, "Split has no commodity"

            imbalance_comm[sp.account.commodity] += sp.quantity
            imbalance_cur += sp.value

        imb_splits = []
        if imbalance_cur:
            imb_splits.append({"account_name": "Imbalance-{}".format(self.currency.mnemonic),
                               "commodity": self.currency,
                               "value": -imbalance_cur})
        imb_splits.extend([
            {"account_name": "Trading:{}:{}".format(k.namespace, k.mnemonic),
             "commodity": k,
             "value": -v}
            for k, v in imbalance_comm.iteritems()
            if v])
        return imb_splits

    def add_imbalance_splits(self):
        from .account import Account

        imb = self.get_imbalances()

        session = self.get_session()
        assert session
        book = session.query(Book).one()
        default_cur = book.root_account.commodity
        for sp in imb:
            account_name = sp["account_name"]
            acc = book.root_account
            if account_name.startswith("Imbalance"):
                try:
                    acc = acc.children.get(name=account_name)
                except KeyError:
                    acc = Account(parent=acc,
                                  placeholder=False,
                                  commodity=default_cur,
                                  name=account_name,
                                  account_type="BANK")
                    Split(transaction=self,
                          value=sp["value"],
                          quantity=0,
                          account=acc,
                    )

            else:
                trading, namespace, mnemonic = account_name.split(":")
                try:
                    acc = acc.children.get(name=trading)
                except KeyError:
                    acc = Account(parent=acc,
                                  placeholder=True,
                                  commodity=default_cur,
                                  name=trading,
                                  account_type="TRADING")
                try:
                    acc = acc.children.get(name=namespace)
                except KeyError:
                    acc = Account(parent=acc,
                                  placeholder=True,
                                  commodity=default_cur,
                                  name=namespace,
                                  account_type="TRADING")
                try:
                    acc = acc.children.get(name=mnemonic)
                except KeyError:
                    acc = Account(parent=acc,
                                  placeholder=False,
                                  commodity=sp["commodity"],
                                  name=mnemonic,
                                  account_type="TRADING")

                v = sp["value"]
                Split(transaction=self,
                      value=v,
                      quantity=v,
                      account=acc,
                )


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

    @classmethod
    def stock_transaction(cls,
                          post_date,
                          enter_date,
                          description,
                          order,
                          amount,
                          quantity,
                          unit_price,
                          currency,
                          broker_account,
                          stock_account,
                          commission_account):
        amount100 = int(amount * 100)
        quantity = int(quantity)
        commission100 = int((amount - quantity * unit_price) * 100)
        assert (order == "buy" and commission100 >= 0) or (
            order == "sell" and commission100 <= 0), "{} {} {} {}".format(order, commission100, amount,
                                                                          quantity * unit_price)

        # print broker_account, stock_account
        # print amount100, commission100,
        tx = Transaction(currency=currency,
                         post_date=post_date,
                         enter_date=enter_date,
                         description=description,
                         num="",
                         splits=[Split(account=broker_account,
                                       reconcile_state='n',
                                       value_num=-amount100 if order == "buy" else amount100 - commission100,
                                       value_denom=100,
                                       quantity_num=-amount100 if order == "buy" else amount100 - commission100,
                                       quantity_denom=100,
                                       memo="",
                                       action="",
                         ),
                                 Split(account=stock_account,
                                       reconcile_state='n',
                                       value_num=(+amount100 - commission100) if order == "buy" else -amount100,
                                       value_denom=100,
                                       quantity_num=quantity if order == "buy" else -quantity,
                                       quantity_denom=1,
                                       memo="",
                                       action="",
                                 )] + ([Split(account=commission_account,
                                              reconcile_state='n',
                                              value_num=(commission100),
                                              value_denom=100,
                                              quantity_num=(commission100),
                                              quantity_denom=1,
                                              memo="",
                                              action="",
                         )] if unit_price else []))
        return tx


@event.listens_for(Session, 'before_flush')
def set_imbalance_on_transaction(session, flush_context, instances):
    print "flushing"
    pass
