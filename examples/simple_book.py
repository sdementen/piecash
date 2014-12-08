from __future__ import print_function
from piecash import create_book

# create by default an in memory sqlite version
ses = create_book(echo=False)
book = ses.book

print("Book is saved:", ses.is_saved, end=' ')
print(" ==> book description:", book.root_account.description)

print("changing description...")
book.root_account.description = "hello, book"
print("Book is saved:", ses.is_saved, end=' ')
print(" ==> book description:", book.root_account.description)

print("saving...")
ses.save()

print("Book is saved:", ses.is_saved, end=' ')
print(" ==> book description:", book.root_account.description)

print("changing description...")
book.root_account.description = "nevermind, book"
print("Book is saved:", ses.is_saved, end=' ')
print(" ==> book description:", book.root_account.description)

print("cancel...")
ses.cancel()

print("Book is saved:", ses.is_saved, end=' ')
print(" ==> book description:", book.root_account.description)
