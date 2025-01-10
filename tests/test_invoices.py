import pytest
import piecash

import datetime
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
    expensevoucher1 = piecash.Expensevoucher(book.employees[0], book.currencies[0])
    expensevoucher2 = piecash.Expensevoucher(book.employees[0], book.currencies[0])

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
    bill1.billto = book.customers[0]

    bill2.notes = 'vendor job notes'
    bill2.billing_id = 'billing id vendor job bill'
    bill2.active = True
    bill2.is_credit_note = False
    bill2.currency = book.currencies[1]
    bill2.term = book.billterms[0]
    bill2.billto = book.jobs[0]

    expensevoucher1.notes = 'expensevoucher notes'
    expensevoucher1.billing_id = 'billing id expensevoucher'
    expensevoucher1.active = True
    expensevoucher1.is_credit_note = False
    expensevoucher1.currency = book.currencies[1]
    expensevoucher1.term = book.billterms[0]

    expensevoucher2.notes = 'expensevoucher notes'
    expensevoucher2.billing_id = 'billing id expensevoucher'
    expensevoucher2.active = True
    expensevoucher2.is_credit_note = True
    expensevoucher2.currency = book.currencies[1]
    expensevoucher2.term = book.billterms[0]

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
    expensevoucher1 = book.expensevouchers[0]
    expensevoucher2 = book.expensevouchers[1]
        
    #Add some entries to invoices/bills/expense vouchers
    anEntry = piecash.business.invoice.Entry(invoice=invoice1) 
    anEntry.description = 'invoice1 description'
    anEntry.action = 'invoice1 action1'
    anEntry.notes = 'invoice1 notes'
    anEntry.quantity = 10
    anEntry.account = invoice_income_account
    anEntry.price = Decimal(str(100.01))
    
    anEntry = piecash.business.invoice.Entry(invoice=invoice2) 
    anEntry.description = 'invoice2 description'
    anEntry.action = 'invoice2 action1'
    anEntry.notes = 'invoice2 notes'
    anEntry.quantity = 11
    anEntry.account = invoice_income_account
    anEntry.price = Decimal(str(101.01))

    anEntry = piecash.business.invoice.Entry(invoice=bill1) 
    anEntry.description = 'bill1 description'
    anEntry.action = 'bill1 action1'
    anEntry.notes = 'bill1 notes'
    anEntry.quantity = 20
    anEntry.account = bill_expense_account
    anEntry.price = Decimal(str(200.01))
    
    anEntry = piecash.business.invoice.Entry(invoice=bill2) 
    anEntry.description = 'bill2 description'
    anEntry.action = 'bill2 action1'
    anEntry.notes = 'bill2 notes'
    anEntry.quantity = 21
    anEntry.account = bill_expense_account
    anEntry.price = Decimal(str(201.01))

    anEntry = piecash.business.invoice.Entry(invoice=expensevoucher1) 
    anEntry.description = 'expensevoucher description'
    anEntry.action = 'expensevoucher action1'
    anEntry.notes = 'expensevoucher notes'
    anEntry.quantity = 31
    anEntry.account = expense_voucher_account
    anEntry.price = Decimal(str(301.01))
    anEntry.billable = True
    anEntry.b_paytype = piecash.business.invoice.Paytype.credit

    anEntry = piecash.business.invoice.Entry(invoice=expensevoucher1) 
    anEntry.description = 'expensevoucher description2'
    anEntry.action = 'expensevoucher action2'
    anEntry.notes = 'expensevoucher notes2'
    anEntry.quantity = 32
    anEntry.account = expense_voucher_account
    anEntry.price = Decimal(str(302.01))
    anEntry.billable = False
    anEntry.b_paytype = piecash.business.invoice.Paytype.cash

    anEntry = piecash.business.invoice.Entry(invoice=expensevoucher2) 
    anEntry.description = 'expensevoucher description'
    anEntry.action = 'expensevoucher action1'
    anEntry.notes = 'expensevoucher notes'
    anEntry.quantity = 33
    anEntry.account = expense_voucher_account
    anEntry.price = Decimal(str(401.01))
    anEntry.billable = True
    anEntry.b_paytype = piecash.business.invoice.Paytype.credit

    anEntry = piecash.business.invoice.Entry(invoice=expensevoucher2) 
    anEntry.description = 'expensevoucher description2'
    anEntry.action = 'expensevoucher action2'
    anEntry.notes = 'expensevoucher notes2'
    anEntry.quantity = 34
    anEntry.account = expense_voucher_account
    anEntry.price = Decimal(str(402.01))
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
    assert len(book.expensevouchers) == 2
        
    # get invoices / bills / expensevouchers
    invoice1 = book.invoices[0]
    invoice2 = book.invoices[1]
    bill1 = book.bills[0]
    bill2 = book.bills[1]
    expensevoucher1 = book.expensevouchers[0]
    expensevoucher2 = book.expensevouchers[1]

    #set some invoice/bill/expensevoucher properties
    assert invoice1.id == '000001'
    assert invoice1.notes == 'some super notes for customer invoice'
    assert invoice1.billing_id == 'setting invoice billing id'
    assert not invoice1.active
    assert invoice1.is_credit_note
    assert invoice1.currency == book.currencies[1]
    assert invoice1.term == book.billterms[1]
    assert invoice1.owner == book.customers[0]
    assert invoice1.end_owner == book.customers[0]
    assert invoice1.date_opened.date() == datetime.date.today()

    assert invoice2.id == '000002'
    assert invoice2.notes == 'customer job notes'
    assert invoice2.billing_id == 'customer job billing id'
    assert invoice2.active
    assert not invoice2.is_credit_note
    assert invoice2.currency == book.currencies[1]
    assert invoice2.term == book.billterms[0]
    assert invoice2.owner == book.jobs[0]    
    assert invoice2.end_owner == book.customers[0]
    assert invoice2.date_opened.date() == datetime.date.today()

    assert bill1.id == '000001'
    assert bill1.notes == 'notes vendor bill'
    assert bill1.billing_id == 'billing id vendor bill'
    assert not bill1.active
    assert bill1.is_credit_note
    assert bill1.currency == book.currencies[1]
    assert bill1.term == book.billterms[1]
    assert bill1.owner == book.vendors[0]
    assert bill1.end_owner == book.vendors[0]
    assert bill1.billto == book.customers[0]
    assert bill1.date_opened.date() == datetime.date.today()

    assert bill2.id == '000002'
    assert bill2.notes == 'vendor job notes'
    assert bill2.billing_id == 'billing id vendor job bill'
    assert bill2.active
    assert not bill2.is_credit_note
    assert bill2.currency == book.currencies[1]
    assert bill2.term == book.billterms[0]
    assert bill2.owner == book.jobs[1]
    assert bill2.end_owner == book.vendors[0]
    assert bill2.billto == book.jobs[0]
    assert bill2.date_opened.date() == datetime.date.today()

    assert expensevoucher1.id == '000001'
    assert expensevoucher1.notes == 'expensevoucher notes'
    assert expensevoucher1.billing_id == 'billing id expensevoucher'
    assert expensevoucher1.active
    assert not expensevoucher1.is_credit_note
    assert expensevoucher1.currency == book.currencies[1]
    assert expensevoucher1.term == book.billterms[0]
    assert expensevoucher1.owner == book.employees[0]
    assert expensevoucher1.end_owner == book.employees[0]
    assert expensevoucher1.date_opened.date() == datetime.date.today()

    assert expensevoucher2.id == '000002'
    assert expensevoucher2.notes == 'expensevoucher notes'
    assert expensevoucher2.billing_id == 'billing id expensevoucher'
    assert expensevoucher2.active
    assert expensevoucher2.is_credit_note
    assert expensevoucher2.currency == book.currencies[1]
    assert expensevoucher2.term == book.billterms[0]
    assert expensevoucher2.owner == book.employees[0]
    assert expensevoucher2.end_owner == book.employees[0]
    assert expensevoucher2.date_opened.date() == datetime.date.today()


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
    assert anEntry.account == invoice_income_account
    assert anEntry.price == Decimal(str(100.01))
    
    anEntry = invoice2.entries[0]
    assert anEntry.description == 'invoice2 description'
    assert anEntry.action == 'invoice2 action1'
    assert anEntry.notes == 'invoice2 notes'
    assert anEntry.quantity == 11
    assert anEntry.account == invoice_income_account
    assert anEntry.price == Decimal(str(101.01))

    anEntry = bill1.entries[0]
    assert anEntry.description == 'bill1 description'
    assert anEntry.action == 'bill1 action1'
    assert anEntry.notes == 'bill1 notes'
    assert anEntry.quantity == 20
    assert anEntry.account == bill_expense_account
    assert anEntry.price == Decimal(str(200.01))
    
    anEntry = bill2.entries[0]
    assert anEntry.description == 'bill2 description'
    assert anEntry.action == 'bill2 action1'
    assert anEntry.notes == 'bill2 notes'
    assert anEntry.quantity == 21
    assert anEntry.account == bill_expense_account
    assert anEntry.price == Decimal(str(201.01))

    anEntry = expensevoucher.entries[0]
    assert anEntry.description == 'expensevoucher description'
    assert anEntry.action == 'expensevoucher action1'
    assert anEntry.notes == 'expensevoucher notes'
    assert anEntry.quantity == 31
    assert anEntry.account == expense_voucher_account
    assert anEntry.price == Decimal(str(301.01))
    assert anEntry.billable
    assert anEntry.b_paytype == piecash.business.invoice.Paytype.credit

    anEntry = expensevoucher.entries[1]
    assert anEntry.description == 'expensevoucher description2'
    assert anEntry.action == 'expensevoucher action2'
    assert anEntry.notes == 'expensevoucher notes2'
    assert anEntry.quantity == 32
    assert anEntry.account == expense_voucher_account
    assert anEntry.price == Decimal(str(302.01))
    assert not anEntry.billable
    assert anEntry.b_paytype == piecash.business.invoice.Paytype.cash

def test_subtotal_and_taxes_for_invoiceentries(book):
    default_currency = book.currencies[0]
    
    #create a customer invoice
    invoice = piecash.Invoice(book.customers[0], default_currency)

    #create some expense accounts to hold the various taxes
    tax_account_1 = piecash.Account(name='taxaccount_1', type='EXPENSE', parent=book.root_account, commodity=default_currency)
    tax_account_2 = piecash.Account(name='taxaccount_2', type='EXPENSE', parent=book.root_account, commodity=default_currency)
    tax_account_3 = piecash.Account(name='taxaccount_3', type='EXPENSE', parent=book.root_account, commodity=default_currency)
    tax_account_4 = piecash.Account(name='taxaccount_4', type='EXPENSE', parent=book.root_account, commodity=default_currency)
    
    #create an income account for the invoice
    income_account = piecash.Account(name='invoice income', type='INCOME', parent=book.root_account, commodity=default_currency)

    #create an account receivable for the invoice
    accounts_receivable = piecash.Account(name='accounts_receivable', type='RECEIVABLE', parent=book.root_account, commodity=default_currency)
    
    #create taxtable with multiple entries, using both value and percent
    taxtable = piecash.business.tax.Taxtable('mytaxtable')
    book.add(taxtable)
    piecash.business.tax.TaxtableEntry("value", 10, tax_account_1, taxtable=taxtable)
    piecash.business.tax.TaxtableEntry("value", 3, tax_account_2, taxtable=taxtable)
    piecash.business.tax.TaxtableEntry("percentage", 6, tax_account_3, taxtable=taxtable)
    piecash.business.tax.TaxtableEntry("percentage", 8, tax_account_4, taxtable=taxtable)
    
    #add entries    
    for discount_type in [piecash.business.tax.DiscountType.percent, piecash.business.tax.DiscountType.value]:
        piecash.business.invoice.Entry(
                                    invoice=invoice, 
                                    description=f'discount type: {discount_type}',
                                    action='some action',
                                    quantity = 2,
                                    price=Decimal(str(200)),
                                    account=income_account,
                                    i_discount=Decimal(str('6')),
                                    i_disc_type=discount_type,
                                    taxable = False
                                )                

    book.save()

    for discount_how in [piecash.business.tax.DiscountHow.sametime, piecash.business.tax.DiscountHow.pretax, piecash.business.tax.DiscountHow.posttax, ]:
        for discount_type in [piecash.business.tax.DiscountType.percent, piecash.business.tax.DiscountType.value]:
            for tax_included in [True, False]:
                piecash.business.invoice.Entry(
                                    invoice=invoice, 
                                    description=f'discount type: {discount_type} ; discount how: {discount_how} ; tax_included: {tax_included}',
                                    action='some action',
                                    quantity = 2,
                                    price=Decimal(str(200)),
                                    account=income_account,
                                    taxincluded=tax_included,
                                    taxtable=taxtable,
                                    i_discount=Decimal(str('6')),
                                    i_disc_type=discount_type,
                                    i_disc_how=discount_how,
                                    b_paytype=piecash.business.invoice.Paytype.cash,
                                    billable=False,
                                    taxable = True
                                )
    book.save()

    subtotals = [
        376, 394, 
        319.11, 376, 333.47, 394, 
        319.11, 376, 333.47, 394, 
        315.47, 371.86, 333.47, 394]
    taxes = [
        0, 0, 
        60.53, 69, 60.53, 69, 
        57.67, 65.64, 59.69, 68.16, 
        60.53, 69, 60.53, 69]
        
    assert len(book.invoices[0].entries) ==  14
        
    for entry, subtotal, tax in zip(book.invoices[0].entries, subtotals, taxes):
        entry_subtotal, entry_tax, entry_tax_per_taxaccount = entry.subtotal_and_tax
        assert round(entry_subtotal, 2) == round(Decimal(subtotal), 2)
        assert round(entry_tax, 2) == round(Decimal(tax), 2)
    
    tax_per_taxaccount = book.invoices[0].tax_per_taxaccount
    assert round(tax_per_taxaccount[tax_account_1], 2) == round(Decimal(120), 2)
    assert round(tax_per_taxaccount[tax_account_2], 2) == round(Decimal(36), 2)
    assert round(tax_per_taxaccount[tax_account_3], 2) == round(Decimal(262.83), 2)
    assert round(tax_per_taxaccount[tax_account_4], 2) == round(Decimal(350.44), 2)

def test_subtotal_and_taxes_for_billentries(book):
    default_currency = book.currencies[0]
    
    #create a vendor bill
    bill = piecash.Bill(book.vendors[0], default_currency)

    #create some expense accounts to hold the various taxes
    tax_account_1 = piecash.Account(name='taxaccount_1', type='EXPENSE', parent=book.root_account, commodity=default_currency)
    tax_account_2 = piecash.Account(name='taxaccount_2', type='EXPENSE', parent=book.root_account, commodity=default_currency)
    tax_account_3 = piecash.Account(name='taxaccount_3', type='EXPENSE', parent=book.root_account, commodity=default_currency)
    tax_account_4 = piecash.Account(name='taxaccount_4', type='EXPENSE', parent=book.root_account, commodity=default_currency)
    
    #create an expense account for the bill
    expense_account = piecash.Account(name='expense account', type='EXPENSE', parent=book.root_account, commodity=default_currency)

    #create an account payable for the invoice
    accounts_payable = piecash.Account(name='accounts_payable', type='PAYABLE', parent=book.root_account, commodity=default_currency)
    
    #create taxtable with multiple entries, using both value and percent
    taxtable = piecash.business.tax.Taxtable('mytaxtable')
    book.add(taxtable)
    piecash.business.tax.TaxtableEntry("value", 10, tax_account_1, taxtable=taxtable)
    piecash.business.tax.TaxtableEntry("value", 3, tax_account_2, taxtable=taxtable)
    piecash.business.tax.TaxtableEntry("percentage", 6, tax_account_3, taxtable=taxtable)
    piecash.business.tax.TaxtableEntry("percentage", 8, tax_account_4, taxtable=taxtable)
    
    #add entries    
    piecash.business.invoice.Entry(
                                    invoice=bill, 
                                    description=f'entry 1 - not taxable',
                                    action='some action',
                                    quantity = 2,
                                    price=Decimal(str(200)),
                                    account=expense_account,
                                    taxable = False
                                )                

    for tax_included in [True, False]:
        piecash.business.invoice.Entry(
                                    invoice=bill, 
                                    description=f'tax_included: {tax_included}',
                                    action='some action',
                                    quantity = 2,
                                    price=Decimal(str(200)),
                                    account=expense_account,
                                    taxincluded=tax_included,
                                    taxtable=taxtable,
                                    b_paytype=piecash.business.invoice.Paytype.cash,
                                    billable=False,
                                    taxable = True
                                )
    book.save()

    subtotals = [400, 339.47, 400]

    #the following values are not presented in the Gnucash GUI. However, total matches the taxes posted to the various accounts.
    taxes = [0, 60.53, 69]

    for entry, subtotal, tax in zip(book.bills[0].entries, subtotals, taxes):
        entry_subtotal, entry_tax, entry_tax_per_taxaccount = entry.subtotal_and_tax
        assert round(entry_subtotal, 2) == round(Decimal(subtotal), 2)
        assert round(entry_tax, 2) == round(Decimal(tax), 2)
    
    tax_per_taxaccount = book.bills[0].tax_per_taxaccount
    assert round(tax_per_taxaccount[tax_account_1], 2) == round(Decimal(20), 2)
    assert round(tax_per_taxaccount[tax_account_2], 2) == round(Decimal(6), 2)
    assert round(tax_per_taxaccount[tax_account_3], 2) == round(Decimal(44.37), 2)
    assert round(tax_per_taxaccount[tax_account_4], 2) == round(Decimal(59.16), 2)

def test_subtotal_and_taxes_for_expensevoucherentries(book_with_invoice_entries):
    book = book_with_invoice_entries

    subtotals = [9331.31, 9664.32]
    taxes = [0, 0]

    for entry, subtotal, tax in zip(book.expensevouchers[0].entries, subtotals, taxes):
        entry_subtotal, entry_tax, entry_tax_per_taxaccount = entry.subtotal_and_tax
        assert round(entry_subtotal, 2) == round(Decimal(subtotal), 2)
        assert round(entry_tax, 2) == round(Decimal(tax), 2)
    
    tax_per_taxaccount = book.expensevouchers[0].tax_per_taxaccount
    assert len(tax_per_taxaccount) == 0

def test_billto(book):
    #create invoices with different billtos
    customer = book.customers[0]
    vendor = book.vendors[0]
    employee = book.employees[0]
    customer_job = book.jobs[0]
    vendor_job = book.jobs[1]
    currency = book.currencies[0]
    
    with pytest.raises(ValueError):
        invoice = piecash.Bill(vendor, currency, billto=employee)
        
    with pytest.raises(ValueError):
        invoice = piecash.Bill(vendor, currency, billto=vendor)

    with pytest.raises(ValueError):
        invoice = piecash.Bill(vendor, currency, billto=vendor_job)
        
    with pytest.raises(ValueError):
        invoice = piecash.Expensevoucher(employee, currency, billto=vendor)
        
    with pytest.raises(ValueError):
        invoice = piecash.Expensevoucher(employee, currency, billto=employee)

    with pytest.raises(ValueError):
        invoice = piecash.Expensevoucher(employee, currency, billto=vendor_job)

    with pytest.raises(ValueError):
        invoice = piecash.Expensevoucher(employee, currency, billto=employee)

    invoice1a = piecash.Bill(vendor, currency, billto=customer)
    invoice1b = piecash.Bill(vendor, currency, billto=customer_job)
    invoice2a = piecash.Expensevoucher(employee, currency, billto=customer)
    invoice2b = piecash.Expensevoucher(employee, currency, billto=customer_job)

    book.flush()

    assert book.bills[0].billto == customer
    assert book.bills[1].billto == customer_job
    assert book.expensevouchers[0].billto == customer
    assert book.expensevouchers[1].billto == customer_job

def test_post(book_with_invoice_entries):
    book = book_with_invoice_entries
    
    NOK = book.commodities(mnemonic='NOK')
    EUR = book.commodities(mnemonic='EUR')
    
    COP = piecash.factories.create_currency_from_ISO("COP")
    book.add(COP)

    ar = piecash.Account(name="A/Receivable", 
              type="RECEIVABLE",
              parent=book.root_account,
              commodity=NOK,
              placeholder=False,)
    ap = piecash.Account(name="A/Payable", 
              type="PAYABLE",
              parent=book.root_account,
              commodity=NOK,
              placeholder=False,)

    arCOP = piecash.Account(name="A/R test", 
              type="RECEIVABLE",
              parent=book.root_account,
              commodity=COP,
              placeholder=False,)
    apCOP = piecash.Account(name="A/P test", 
              type="PAYABLE",
              parent=book.root_account,
              commodity=COP,
              placeholder=False,)

    date = datetime.date.today()
    book.add(piecash.Price(commodity=NOK, currency=EUR, date=date, value=Decimal('0.1')))

    book.flush()
    
    for objtype in [book.invoices, book.bills, book.expensevouchers]:
        postacc = ar
        wrong_postacc_currency = arCOP
        wrong_postacc_type = ap
        
        if objtype != book.invoices:
            postacc, wrong_postacc_type = wrong_postacc_type, postacc
            wrong_postacc_currency = apCOP
        
        for obj in objtype:
            with pytest.raises(ValueError):
                obj.post(wrong_postacc_type)

            with pytest.raises(ValueError):
                obj.post(wrong_postacc_currency)
            
            obj.post(postacc, prices=book.prices)
    book.flush()
    
#missing: check of transaction splits: combined value    
# post to wrong account currency
    
    assert book.invoices[0].is_posted
    assert book.invoices[0].date_posted.date() == datetime.date.today()
    assert book.invoices[0].post_account == ar
    assert book.invoices[0].post_txn == book.query(piecash.Transaction).filter(piecash.Transaction.description == book.invoices[0].owner.name, piecash.Transaction.num == book.invoices[0].id).all()[0]
    lot = book.query(piecash.Lot).filter(piecash.Lot.guid==book.invoices[0].post_lot.guid).all()[0]
    assert book.invoices[0].post_lot == lot
    assert book.invoices[0].post_account.guid == lot.account_guid
    assert book.invoices[1].is_posted
    assert book.invoices[1].date_posted.date() == datetime.date.today()
    assert book.invoices[1].post_account == ar
    assert book.invoices[1].post_txn == book.query(piecash.Transaction).filter(piecash.Transaction.description == book.invoices[1].owner.name, piecash.Transaction.num == book.invoices[1].id).all()[0]
    lot = book.query(piecash.Lot).filter(piecash.Lot.guid==book.invoices[1].post_lot.guid).all()[0]
    assert book.invoices[1].post_lot == lot
    assert book.invoices[1].post_account.guid == lot.account_guid
    assert book.bills[0].is_posted
    assert book.bills[0].date_posted.date() == datetime.date.today()
    assert book.bills[0].post_account == ap
    assert book.bills[0].post_txn == book.query(piecash.Transaction).filter(piecash.Transaction.description == book.bills[0].owner.name, piecash.Transaction.num == book.bills[0].id).all()[0]
    lot = book.query(piecash.Lot).filter(piecash.Lot.guid==book.bills[0].post_lot.guid).all()[0]
    assert book.bills[0].post_lot == lot
    assert book.bills[0].post_account.guid == lot.account_guid
    assert book.bills[1].is_posted
    assert book.bills[1].date_posted.date() == datetime.date.today()
    assert book.bills[1].post_account == ap
    assert book.bills[1].post_txn == book.query(piecash.Transaction).filter(piecash.Transaction.description == book.bills[1].owner.name, piecash.Transaction.num == book.bills[1].id).all()[0]
    lot = book.query(piecash.Lot).filter(piecash.Lot.guid==book.bills[1].post_lot.guid).all()[0]
    assert book.bills[1].post_lot == lot
    assert book.bills[1].post_account.guid == lot.account_guid
    assert book.expensevouchers[0].is_posted
    assert book.expensevouchers[0].date_posted.date() == datetime.date.today()
    assert book.expensevouchers[0].post_account == ap
    assert book.expensevouchers[0].post_txn == book.query(piecash.Transaction).filter(piecash.Transaction.description == book.expensevouchers[0].owner.name, piecash.Transaction.num == book.expensevouchers[0].id).all()[0]
    lot = book.query(piecash.Lot).filter(piecash.Lot.guid==book.expensevouchers[0].post_lot.guid).all()[0]
    assert book.expensevouchers[0].post_lot == lot
    assert book.expensevouchers[0].post_account.guid == lot.account_guid
    assert book.expensevouchers[1].is_posted
    assert book.expensevouchers[1].date_posted.date() == datetime.date.today()
    assert book.expensevouchers[1].post_account == ap
    assert book.expensevouchers[1].post_txn == book.query(piecash.Transaction).filter(piecash.Transaction.description == book.expensevouchers[1].owner.name, piecash.Transaction.num == book.expensevouchers[1].id).all()[0]
    lot = book.query(piecash.Lot).filter(piecash.Lot.guid==book.expensevouchers[1].post_lot.guid).all()[0]
    assert book.expensevouchers[1].post_lot == lot
    assert book.expensevouchers[1].post_account.guid == lot.account_guid

def test_post_multicurrency(book):
    #currencies
    NOK = book.commodities(mnemonic='NOK')
    EUR = book.commodities(mnemonic='EUR')
    COP = piecash.factories.create_currency_from_ISO("COP")
    HRK = piecash.factories.create_currency_from_ISO("HRK")
    BGN = piecash.factories.create_currency_from_ISO("BGN")
    book.add(COP)
    book.add(HRK)
    book.add(BGN)

    #accounts
    entry_income = piecash.Account(name="invoice_income_account_HRK", type="INCOME", parent=book.root_account, commodity=HRK, placeholder=False,)
    entry_income2 = piecash.Account(name="invoice_income_account_BGN", type="INCOME", parent=book.root_account, commodity=BGN, placeholder=False,)
    entry_income3 = piecash.Account(name="invoice_income_account_NOK", type="INCOME", parent=book.root_account, commodity=NOK, placeholder=False,)
    tax1 = piecash.Account(name="tax1", type="LIABILITY", parent=book.root_account, commodity=COP, placeholder=False,)
    tax2 = piecash.Account(name="tax2", type="LIABILITY", parent=book.root_account, commodity=EUR, placeholder=False,)
    ar = piecash.Account(name="A/Receivable", type="RECEIVABLE", parent=book.root_account, commodity=NOK, placeholder=False,)

    #taxtable
    taxtable = piecash.business.tax.Taxtable('multicurrencytt')
    book.add(taxtable)
    piecash.business.tax.TaxtableEntry("value", 10, tax1, taxtable=taxtable)
    piecash.business.tax.TaxtableEntry("percentage", 20, tax2, taxtable=taxtable)
    
    #invoice
    invoice = piecash.Invoice(book.customers[0], NOK)
    entry1 = piecash.business.invoice.Entry(invoice, quantity=5, price=1000, account=entry_income, taxtable=taxtable)
    entry2 = piecash.business.invoice.Entry(invoice, quantity=10, price=2000, account=entry_income2, taxtable=taxtable)
    entry3 = piecash.business.invoice.Entry(invoice, quantity=20, price=3000, account=entry_income3, taxtable=taxtable)

    #set some prices
    date = datetime.date.today()
    book.add(piecash.Price(commodity=NOK, currency=EUR, date=date, value=Decimal('0.1')))
    book.add(piecash.Price(commodity=NOK, currency=BGN, date=date, value=Decimal('0.2')))
    book.add(piecash.Price(commodity=NOK, currency=HRK, date=date, value=Decimal('0.75')))
    book.add(piecash.Price(commodity=NOK, currency=COP, date=date, value=Decimal('445')))
    book.flush()

    invoice.post(ar, prices=book.prices)

    txn = invoice.post_txn
