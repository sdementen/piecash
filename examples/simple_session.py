from __future__ import print_function
import os
import tempfile

from piecash import open_book, create_book, GnucashException


FILE_1 = os.path.join(tempfile.gettempdir(), "not_there.gnucash")
FILE_2 = os.path.join(tempfile.gettempdir(), "example_file.gnucash")

if os.path.exists(FILE_2):
    os.remove(FILE_2)

# open a file that isn't there, detect the error
try:
    book = open_book(FILE_1)
except GnucashException as backend_exception:
    print("OK", backend_exception)

# create a new file, this requires a file type specification
with create_book(FILE_2) as book:
    pass

# open the new file, try to open it a second time, detect the lock
# using the session as context manager automatically release the lock and close the session
with open_book(FILE_2) as book:
    try:
        with open_book(FILE_2) as book_2:
            pass
    except GnucashException as backend_exception:
        print("OK", backend_exception)

os.remove(FILE_2)
