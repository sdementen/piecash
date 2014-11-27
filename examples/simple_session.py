import os
import shutil
from sqlalchemy import inspect
from piecash import open_book, create_book, GnucashException, Book

FILE_1 = "/tmp/not_there.xac"
FILE_2 = "/tmp/example_file.xac"

# open a file that isn't there, detect the error
try:
    session = open_book(FILE_1)
except GnucashException, backend_exception:
    print "OK", backend_exception

# create a new file, this requires a file type specification
with create_book(FILE_2) as session:
    pass

# open the new file, try to open it a second time, detect the lock
# using the session as context manager automatically release the lock and close the session
with open_book(FILE_2) as session:
    try:
        session_2 = open_book(FILE_2)
    except GnucashException, backend_exception:
        print "OK", backend_exception

os.remove(FILE_2)
