"""
Search for account.
Type in any part of the account name and the script will search through all the accounts
in the book and display all that contain the given string.

to-do:
- search for entered string
- allow multiple search terms separated by space
"""
# pylint: disable=invalid-name
import sys
import piecash
from piecash import Commodity

# Variables
filename = sys.argv[1]
#############################

searchTerm = input("Please enter the search term:")

def searchAccount(searchTerm, book):
    """Searches through account names"""
    print("Search results:\n")

    found = False

    # search
    for account in book.accounts:
        #print(account.fullname)
        # name
        if searchTerm.lower() in account.fullname.lower():
            print(account.fullname)
            found = True

    if not found:
        print("Search term not found in account names.")
    return

with piecash.open_book(filename, open_if_lock=True) as book:
    searchAccount(searchTerm, book)
