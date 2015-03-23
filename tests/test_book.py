import os

import pytest
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session

from piecash import create_book, Account, GnucashException, Book
from piecash.sa_extra import get_foreign_keys, DeclarativeBase

test_folder = os.path.dirname(os.path.realpath(__file__))
db = os.path.join(test_folder, "foo.sqlite")


@pytest.fixture(params=[None, db])
def s(request):
    name = request.param
    if name and os.path.exists(name):
        os.remove(name)
    return create_book(name)

class TestBook_create_book(object):
    def test_create_default(self, s):

        assert isinstance(s, Book)
        assert isinstance(s.session, Session)
        assert s.uri is None
        assert s.session.bind.name == "sqlite"

        EUR = s.commodities[0]
        assert EUR.mnemonic == "EUR"
        assert EUR.namespace == "CURRENCY"

        # no std account
        assert len(s.accounts) == 0
        # two root accounts
        root_accs = s.query(Account).all()
        assert all([acc.type == "ROOT" for acc in root_accs])
        assert len(root_accs) == 2

        # no slots
        assert len(s.slots) == 0

    def test_create_save_cancel_flush(self, s):

        EUR = s.commodities[0]
        EUR.mnemonic = "foo"
        assert EUR.mnemonic == "foo"
        s.cancel()
        assert EUR.mnemonic == "EUR"

        EUR.mnemonic = "foo"
        assert EUR.mnemonic == "foo"
        s.flush()
        assert EUR.mnemonic == "foo"
        s.cancel()
        assert EUR.mnemonic == "EUR"

        EUR.mnemonic = "foo"
        s.save()
        assert EUR.mnemonic == "foo"

    def test_create_specific_currency(self):
        s = create_book(currency="USD")
        CUR = s.commodities[0]
        assert CUR.mnemonic == "USD"
        assert CUR.namespace == "CURRENCY"

        s = create_book(currency="CHF")
        CUR = s.commodities[0]
        assert CUR.mnemonic == "CHF"
        assert CUR.namespace == "CURRENCY"

        with pytest.raises(ValueError):
            s = create_book(currency="ZIE")

    def test_create_named_book(self):
        # remove file if left from previous test
        if os.path.exists(db):
            os.remove(db)

        # assert creation of file
        s = create_book(db)
        assert os.path.exists(db)
        t = os.path.getctime(db)

        # ensure error if no overwrite
        with pytest.raises(GnucashException):
            s = create_book(db)
        with pytest.raises(GnucashException):
            s = create_book(uri_conn="sqlite:///{}".format(db))
        with pytest.raises(GnucashException):
            s = create_book(db, overwrite=False)

        assert os.path.getctime(db) == t

        # if overwrite, DB is recreated
        s = create_book(db, overwrite=True)
        assert os.path.getctime(db) > t

        # clean test
        os.remove(db)

    def test_create_FK(self):
        # create and keep FK
        s = create_book(keep_foreign_keys=True)
        fk = list(get_foreign_keys(metadata=DeclarativeBase.metadata,
                                   engine=s.session.bind))
        Inspector.from_engine(s.session.bind)
        assert len(fk) == 31

        # create and drop FK
        s = create_book("fk.text.sqlite", keep_foreign_keys=False, overwrite=True, echo=True)
        fk = list(get_foreign_keys(metadata=DeclarativeBase.metadata,
                                   engine=s.session.bind))
        assert len(fk) == 0
