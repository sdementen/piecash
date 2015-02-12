from __future__ import print_function
from piecash import create_book

# create by default an in memory sqlite version
book = create_book(echo=False)

print("Book is saved:", book.is_saved, end=' ')
print(" ==> book description:", book.root_account.description)

print("changing description...")
book.root_account.description = "hello, book"
print("Book is saved:", book.is_saved, end=' ')
print(" ==> book description:", book.root_account.description)

print("saving...")
book.save()

print("Book is saved:", book.is_saved, end=' ')
print(" ==> book description:", book.root_account.description)

print("changing description...")
book.root_account.description = "nevermind, book"
print("Book is saved:", book.is_saved, end=' ')
print(" ==> book description:", book.root_account.description)

print("cancel...")
book.cancel()

print("Book is saved:", book.is_saved, end=' ')
print(" ==> book description:", book.root_account.description)
