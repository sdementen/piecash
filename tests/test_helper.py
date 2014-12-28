import os.path
import sys

test_folder = os.path.dirname(os.path.realpath(__file__))
book_folder = os.path.join(test_folder, "..", "gnucash_books")
file_template = os.path.join(book_folder, "empty_book.gnucash")
file_for_test = os.path.join(test_folder, "empty_book_for_test.gnucash")
file_template_full = os.path.join(book_folder, "test_book.gnucash")
file_for_test_full = os.path.join(test_folder, "test_book_for_test.gnucash")

if sys.version_info.major==3:
    def run_file(fname):
        with open(fname) as f:
            code = compile(f.read(), fname, 'exec')
            exec(code, {})
else:
    def run_file(fname):
        return execfile(fname, {})
