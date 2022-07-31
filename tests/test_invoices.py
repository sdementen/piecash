import pytest
import piecash

#import datetime
from decimal import Decimal
    
@pytest.fixture 
def book():
    #creates a basic book for test purposes
    #create an empty in-memory book
    book = piecash.create_book()

    #get the default currency
    default_currency = book.currencies[0]

    #add a 2nd currency
    NOK = piecash.factories.create_currency_from_ISO("NOK")
    book.add(NOK)

    #create some accounts
    invoice_income_account = piecash.Account(name="invoice_income_account", type="INCOME", parent=book.root_account, commodity=default_currency, placeholder=False,)
    bill_expense_account = piecash.Account(name="bill_expense_account", type="EXPENSE", parent=book.root_account, commodity=default_currency, placeholder=False,)
    expense_voucher_account = piecash.Account(name="expense_voucher_account", type="EXPENSE", parent=book.root_account, commodity=default_currency, placeholder=False,)
    creditcard_account = piecash.Account(name="creditcard_account", type="CREDIT", parent=book.root_account, commodity=default_currency, placeholder=False,)

    #create some people
    customer = piecash.Customer('Good customer', book.currencies[0])
    book.add(customer)
    vendor = piecash.Vendor('Good vendor', default_currency, book=book)
    employee = piecash.Employee('Better employee', default_currency, book=book)
    employee.creditcard_account = creditcard_account

    #create a taxtable (leave as empty for now)
    taxtable = piecash.business.tax.Taxtable('mytaxtable')
    book.add(taxtable)

    #create job
    book.save()     #need a save for the Job.customer to take
    job1 = piecash.Job('a good customer job name', customer)
    job2 = piecash.Job('a good vendor job name', vendor)
    book.save()
    
    return book

@pytest.fixture
def book_with_billterms(book):
    #create some terms
    term_day = piecash.business.invoice.Billterm("term_day", book=book)
    term_proximo = piecash.business.invoice.Billterm("term_proximo", term_type=piecash.business.invoice.Termtype.proximo)
    term_proximo.duedays=1
    term_proximo.discountdays=1
    term_proximo.discount=10
    term_proximo.cutoff=5
    book.add(term_proximo)

    book.save()
    return book

@pytest.fixture
def book_with_updated_job_properties(book_with_billterms):
    book = book_with_billterms
    job = book.jobs[0]
    job.name = 'a better customer job name'
    job.rate = 1045.
    job.active = False
    job.reference = 'some awesome reference'
    book.save()
    return book

@pytest.fixture
def book_with_invoices(book_with_updated_job_properties):
    book = book_with_updated_job_properties
    
    #create some invoices / bills / expense vouchers
    invoice1 = piecash.Invoice(book.customers[0], book.currencies[0])
    invoice2 = piecash.Invoice(book.jobs[0], book.currencies[0])
    bill1 = piecash.Bill(book.vendors[0], book.currencies[0])
    bill2 = piecash.Bill(book.jobs[1], book.currencies[0])
    expensevoucher = piecash.Expensevoucher(book.employees[0], book.currencies[0])

    #set some invoice/bill/expensevoucher properties
    invoice1.notes = 'some super notes for customer invoice'
    invoice1.billing_id = 'setting invoice billing id'
    invoice1.active = False
    invoice1.is_credit_note = True
    invoice1.currency = book.currencies[1]
    invoice1.term = book.billterms[1]

    invoice2.notes = 'customer job notes'
    invoice2.billing_id = 'customer job billing id'
    invoice2.active = True
    invoice2.is_credit_note = False
    invoice2.currency = book.currencies[1]
    invoice2.term = book.billterms[0]

    bill1.notes = 'notes vendor bill'
    bill1.billing_id = 'billing id vendor bill'
    bill1.active = False
    bill1.is_credit_note = True
    bill1.currency = book.currencies[1]
    bill1.term = book.billterms[1]

    bill2.notes = 'vendor job notes'
    bill2.billing_id = 'billing id vendor job bill'
    bill2.active = True
    bill2.is_credit_note = False
    bill2.currency = book.currencies[1]
    bill2.term = book.billterms[0]

    expensevoucher.notes = 'expensevoucher notes'
    expensevoucher.billing_id = 'billing id expensevoucher'
    expensevoucher.active = True
    expensevoucher.is_credit_note = False
    expensevoucher.currency = book.currencies[0]
    expensevoucher.term = book.billterms[0]

    book.save()
    return book

@pytest.fixture
def book_with_invoice_entries(book_with_invoices):
    book = book_with_invoices

    #get accounts
    invoice_income_account = book.accounts[0]
    bill_expense_account = book.accounts[1]
    expense_voucher_account = book.accounts[2]
    creditcard_account = book.accounts[3]
    
    #get invoices / bills / expense vouchers
    invoice1 = book.invoices[0]
    invoice2 = book.invoices[1]
    bill1 = book.bills[0]
    bill2 = book.bills[1]
    expensevoucher = book.expensevouchers[0]
    
    #Add some entries to invoices/bills/expense vouchers
    anEntry = piecash.business.invoice.Entry(invoice=invoice1) 
    anEntry.description = 'invoice1 description'
    anEntry.action = 'invoice1 action1'
    anEntry.notes = 'invoice1 notes'
    anEntry.quantity = 10
    anEntry.acct = invoice_income_account
    anEntry.price = 100.01
    
    anEntry = piecash.business.invoice.Entry(invoice=invoice2) 
    anEntry.description = 'invoice2 description'
    anEntry.action = 'invoice2 action1'
    anEntry.notes = 'invoice2 notes'
    anEntry.quantity = 11
    anEntry.acct = invoice_income_account
    anEntry.price = 101.01

    anEntry = piecash.business.invoice.Entry(invoice=bill1) 
    anEntry.description = 'bill1 description'
    anEntry.action = 'bill1 action1'
    anEntry.notes = 'bill1 notes'
    anEntry.quantity = 20
    anEntry.acct = bill_expense_account
    anEntry.price = 200.01
    
    anEntry = piecash.business.invoice.Entry(invoice=bill2) 
    anEntry.description = 'bill2 description'
    anEntry.action = 'bill2 action1'
    anEntry.notes = 'bill2 notes'
    anEntry.quantity = 21
    anEntry.acct = bill_expense_account
    anEntry.price = 201.01

    anEntry = piecash.business.invoice.Entry(invoice=expensevoucher) 
    anEntry.description = 'expensevoucher description'
    anEntry.action = 'expensevoucher action1'
    anEntry.notes = 'expensevoucher notes'
    anEntry.quantity = 31
    anEntry.acct = expense_voucher_account
    anEntry.price = 301.01
    anEntry.billable = True
    anEntry.b_paytype = piecash.business.invoice.Paytype.credit

    anEntry = piecash.business.invoice.Entry(invoice=expensevoucher) 
    anEntry.description = 'expensevoucher description2'
    anEntry.action = 'expensevoucher action2'
    anEntry.notes = 'expensevoucher notes2'
    anEntry.quantity = 32
    anEntry.acct = expense_voucher_account
    anEntry.price = 302.01
    anEntry.billable = False
    anEntry.b_paytype = piecash.business.invoice.Paytype.cash

    book.save()
    return book
     
def test_add_terms(book_with_billterms):
    book = book_with_billterms
    assert len(book.billterms) == 2
    
    # check term_day
    assert book.billterms[0].name == 'term_day'
    assert book.billterms[0].type == piecash.business.invoice.Termtype.days.value
    assert book.billterms[0].duedays == 30
    assert book.billterms[0].discountdays == 0
    assert book.billterms[0].discount == 0
    assert book.billterms[0].cutoff == 0
    
    # check term_proximo
    assert book.billterms[1].name == 'term_proximo'
    assert book.billterms[1].type == piecash.business.invoice.Termtype.proximo.value
    assert book.billterms[1].duedays == 1
    assert book.billterms[1].discountdays == 1
    assert book.billterms[1].discount == 10
    assert book.billterms[1].cutoff == 5

def test_add_terms2(book):
    #try adding a billterm with non-existing type
    with pytest.raises(TypeError):
        aterm = piecash.business.invoice.Billterm("termday", term_type='no existing type')

    #add two terms with same name
    aterm1 = piecash.business.invoice.Billterm("termday", book=book)
    aterm2 = piecash.business.invoice.Billterm("termday", book=book)

    book.save()
    
    assert len(book.billterms) == 2

def test_job_properties(book_with_updated_job_properties):
    book = book_with_updated_job_properties

    job = book.jobs[0]
    assert job.name == 'a better customer job name'
    assert job.rate == 1045.
    assert not job.active
    assert job.reference == 'some awesome reference'
    assert job.owner == book.customers[0]

    job.rate = 50
    assert book.jobs[0].rate == 50

def test_invoices(book_with_invoices):
    book = book_with_invoices

    assert len(book.invoices) == 2
    assert len(book.bills) == 2
    assert len(book.expensevouchers) == 1
    
    # get invoices / bills / expensevouchers
    invoice1 = book.invoices[0]
    invoice2 = book.invoices[1]
    bill1 = book.bills[0]
    bill2 = book.bills[1]
    expensevoucher = book.expensevouchers[0]

    #set some invoice/bill/expensevoucher properties
    assert invoice1.notes == 'some super notes for customer invoice'
    assert invoice1.billing_id == 'setting invoice billing id'
    assert not invoice1.active
    assert invoice1.is_credit_note
    assert invoice1.currency == book.currencies[1]
    assert invoice1.term == book.billterms[1]

    assert invoice2.notes == 'customer job notes'
    assert invoice2.billing_id == 'customer job billing id'
    assert invoice2.active
    assert not invoice2.is_credit_note
    assert invoice2.currency == book.currencies[1]
    assert invoice2.term == book.billterms[0]

    assert bill1.notes == 'notes vendor bill'
    assert bill1.billing_id == 'billing id vendor bill'
    assert not bill1.active
    assert bill1.is_credit_note
    assert bill1.currency == book.currencies[1]
    assert bill1.term == book.billterms[1]

    assert bill2.notes == 'vendor job notes'
    assert bill2.billing_id == 'billing id vendor job bill'
    assert bill2.active
    assert not bill2.is_credit_note
    assert bill2.currency == book.currencies[1]
    assert bill2.term == book.billterms[0]

    assert expensevoucher.notes == 'expensevoucher notes'
    assert expensevoucher.billing_id == 'billing id expensevoucher'
    assert expensevoucher.active
    assert not expensevoucher.is_credit_note
    assert expensevoucher.currency == book.currencies[0]
    assert expensevoucher.term == book.billterms[0]

def test_invoices2(book_with_invoices):
    book = book_with_invoices
    
    #create some invoices / bills / expense vouchers - mismatch owners
    with pytest.raises(ValueError):
        piecash.Invoice(book.vendors[0], book.currencies[0])
        piecash.Invoice(book.employees[0], book.currencies[0])
        piecash.Invoice(book.jobs[1], book.currencies[0])

        piecash.Bill(book.customers[0], book.currencies[0])
        piecash.Bill(book.employees[0], book.currencies[0])
        piecash.Bill(book.jobs[0], book.currencies[0])

        piecash.Expensevoucher(book.customers[0], book.currencies[0])
        piecash.Expensevoucher(book.vendors[0], book.currencies[0])
        piecash.Expensevoucher(book.jobs[0], book.currencies[0])
        piecash.Expensevoucher(book.jobs[1], book.currencies[0])

def test_entries(book_with_invoice_entries):
    book = book_with_invoice_entries
    
    #get accounts
    invoice_income_account = book.accounts[0]
    bill_expense_account = book.accounts[1]
    expense_voucher_account = book.accounts[2]
    creditcard_account = book.accounts[3]
    
    #get invoices / bills / expense vouchers
    invoice1 = book.invoices[0]
    invoice2 = book.invoices[1]
    bill1 = book.bills[0]
    bill2 = book.bills[1]
    expensevoucher = book.expensevouchers[0]
    
    #Add some entries to invoices/bills/expense vouchers
    assert len(invoice1.entries) == 1
    assert len(invoice2.entries) == 1
    assert len(bill1.entries) == 1
    assert len(bill2.entries) == 1
    assert len(expensevoucher.entries) == 2

    anEntry = invoice1.entries[0]
    assert anEntry.description == 'invoice1 description'
    assert anEntry.action == 'invoice1 action1'
    assert anEntry.notes == 'invoice1 notes'
    assert anEntry.quantity == 10
#    assert anEntry.acct == invoice_income_account
    assert anEntry.price == Decimal(str(100.01))
    
    anEntry = invoice2.entries[0]
    assert anEntry.description == 'invoice2 description'
    assert anEntry.action == 'invoice2 action1'
    assert anEntry.notes == 'invoice2 notes'
    assert anEntry.quantity == 11
#    assert anEntry.acct = invoice_income_account
    assert anEntry.price == Decimal(str(101.01))

    anEntry = bill1.entries[0]
    assert anEntry.description == 'bill1 description'
    assert anEntry.action == 'bill1 action1'
    assert anEntry.notes == 'bill1 notes'
    assert anEntry.quantity == 20
#    anEntry.acct = bill_expense_account
    assert anEntry.price == Decimal(str(200.01))
    
    anEntry = bill2.entries[0]
    assert anEntry.description == 'bill2 description'
    assert anEntry.action == 'bill2 action1'
    assert anEntry.notes == 'bill2 notes'
    assert anEntry.quantity == 21
#    anEntry.acct = bill_expense_account
    assert anEntry.price == Decimal(str(201.01))

    anEntry = expensevoucher.entries[0]
    assert anEntry.description == 'expensevoucher description'
    assert anEntry.action == 'expensevoucher action1'
    assert anEntry.notes == 'expensevoucher notes'
    assert anEntry.quantity == 31
#    assert anEntry.acct == expense_voucher_account
    assert anEntry.price == Decimal(str(301.01))
    assert anEntry.billable
    assert anEntry.b_paytype == piecash.business.invoice.Paytype.credit

    anEntry = expensevoucher.entries[1]
    assert anEntry.description == 'expensevoucher description2'
    assert anEntry.action == 'expensevoucher action2'
    assert anEntry.notes == 'expensevoucher notes2'
    assert anEntry.quantity == 32
#    assert anEntry.acct = expense_voucher_account
    assert anEntry.price == Decimal(str(302.01))
    assert not anEntry.billable
    assert anEntry.b_paytype == piecash.business.invoice.Paytype.cash



# things to check
# Decimal - must be a better way
# account: should get an account, not guid