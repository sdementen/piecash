import os.path

test_folder = os.path.dirname(os.path.realpath(__file__))
book_folder = os.path.join(test_folder, "..", "gnucash_books")
file_template = os.path.join(book_folder, "empty_book.gnucash")
file_for_test = os.path.join(test_folder, "empty_book_for_test.gnucash")
file_template_full = os.path.join(book_folder, "test_book.gnucash")
file_for_test_full = os.path.join(test_folder, "test_book_for_test.gnucash")
