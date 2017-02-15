# -*- coding: utf-8 -*-
from __future__ import print_function

import imp
import os
import subprocess
import sys

# # Python 2.6 subprocess.check_output compatibility. Thanks Greg Hewgill!
if 'check_output' not in dir(subprocess):
    def check_output(cmd_args, *args, **kwargs):
        proc = subprocess.Popen(
            cmd_args, *args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(args)
        return out


    subprocess.check_output = check_output

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


# from setuptools.command.test import test

class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        # self.test_args = []
        # self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


try:
    import colorama

    colorama.init()  # Initialize colorama on Windows
except ImportError:
    # Don't require colorama just for running paver tasks. This allows us to
    # run `paver install' without requiring the user to first have colorama
    # installed.
    pass

# Add the current directory to the module search path.
sys.path.append('.')

# # Constants
CODE_DIRECTORY = 'piecash'
DOCS_DIRECTORY = 'docs'
TESTS_DIRECTORY = 'tests'
DATA_DIRECTORY = 'gnucash_books'
PYTEST_FLAGS = ['--doctest-modules']

# Import metadata. Normally this would just be:
#
# from piecash import metadata
#
# However, when we do this, we also import `piecash/__init__.py'. If this
# imports names from some other modules and these modules have third-party
# dependencies that need installing (which happens after this file is run), the
# script will crash. What we do instead is to load the metadata module by path
# instead, effectively side-stepping the dependency problem. Please make sure
# metadata has no dependencies, otherwise they will need to be added to
# the setup_requires keyword.
metadata = imp.load_source(
    'metadata', os.path.join(CODE_DIRECTORY, 'metadata.py'))


# # Miscellaneous helper functions

def get_project_files():
    """Retrieve a list of project files, ignoring hidden files.

    :return: sorted list of project files
    :rtype: :class:`list`
    """
    if is_git_project():
        return get_git_project_files()

    project_files = []
    for top, subdirs, files in os.walk('.'):
        for subdir in subdirs:
            if subdir.startswith('.'):
                subdirs.remove(subdir)

        for f in files:
            if f.startswith('.'):
                continue
            project_files.append(os.path.join(top, f))

    return project_files


def is_git_project():
    return os.path.isdir('.git')


def get_git_project_files():
    """Retrieve a list of all non-ignored files, including untracked files,
    excluding deleted files.

    :return: sorted list of git project files
    :rtype: :class:`list`
    """
    cached_and_untracked_files = git_ls_files(
        '--cached',  # All files cached in the index
        '--others',  # Untracked files
        # Exclude untracked files that would be excluded by .gitignore, etc.
        '--exclude-standard')
    uncommitted_deleted_files = git_ls_files('--deleted')

    # Since sorting of files in a set is arbitrary, return a sorted list to
    # provide a well-defined order to tools like flake8, etc.
    return sorted(cached_and_untracked_files - uncommitted_deleted_files)


def git_ls_files(*cmd_args):
    """Run ``git ls-files`` in the top-level project directory. Arguments go
    directly to execution call.

    :return: set of file names
    :rtype: :class:`set`
    """
    cmd = ['git', 'ls-files']
    cmd.extend(cmd_args)
    return set(subprocess.check_output(cmd).splitlines())


def print_success_message(message):
    """Print a message indicating success in green color to STDOUT.

    :param message: the message to print
    :type message: :class:`str`
    """
    try:
        import colorama

        print(colorama.Fore.GREEN + message + colorama.Fore.RESET)
    except ImportError:
        print(message)


def print_failure_message(message):
    """Print a message indicating failure in red color to STDERR.

    :param message: the message to print
    :type message: :class:`str`
    """
    try:
        import colorama

        print(colorama.Fore.RED + message + colorama.Fore.RESET,
              file=sys.stderr)
    except ImportError:
        print(message, file=sys.stderr)


def read(filename):
    """Return the contents of a file.

    :param filename: file path
    :type filename: :class:`str`
    :return: the file's content
    :rtype: :class:`str`
    """
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()


def _lint():
    """Run lint and return an exit code."""
    # Flake8 doesn't have an easy way to run checks using a Python function, so
    # just fork off another process to do it.

    # Python 3 compat:
    # - The result of subprocess call outputs are byte strings, meaning we need
    # to pass a byte string to endswith.
    project_python_files = [filename for filename in get_project_files()
                            if filename.endswith(b'.py')]
    retcode = subprocess.call(
        ['flake8', '--ignore=E126,E121', '--max-line-length=99', '--max-complexity=10']
        + project_python_files)
    if retcode == 0:
        print_success_message('No style errors')
    return retcode


# define install_requires for specific Python versions
python_version_specific_requires = []

# as of Python >= 2.7 and >= 3.2, the argparse module is maintained within
# the Python standard library, otherwise we install it as a separate package
# if sys.version_info < (2, 7) or (3, 0) <= sys.version_info < (3, 3):
#     python_version_specific_requires.append('argparse')


# See here for more options:
# <http://pythonhosted.org/setuptools/setuptools.html>

setup_dict = dict(
    name=metadata.package,
    version=metadata.version,
    author=metadata.authors[0],
    author_email=metadata.emails[0],
    maintainer=metadata.authors[0],
    maintainer_email=metadata.emails[0],
    url=metadata.url,
    description=metadata.description,
    long_description=read('README.rst'),
    keywords=['GnuCash', 'python', 'binding', 'interface', 'sqlalchemy'],
    license='MIT',
    platforms='any',
    # Find a list of classifiers here:
    # <http://pypi.python.org/pypi?%3Aaction=list_classifiers>
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Office/Business',
        'Topic :: Office/Business :: Financial',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=find_packages(exclude=(TESTS_DIRECTORY, DATA_DIRECTORY)),
    install_requires=[
                         'SQLAlchemy>=1.0',
                         'SQLAlchemy-Utils>=0.31',
                         'pytz',
                         'enum-compat',
                         'tzlocal',
                         'yahoo-finance',
                     ] + python_version_specific_requires,
    # Allow tests to be run with `python setup.py test'.
    tests_require=[
        'pytest',
        'py',
    ],
    # console=['scripts/piecash_ledger.py','scripts/piecash_toqif.py'],
    scripts=['scripts/piecash_ledger.py', 'scripts/piecash_toqif.py', 'scripts/piecash_prices.py'],
    cmdclass={'test': PyTest},
    test_suite="tests",
    zip_safe=False,  # don't use eggs
)


def main():
    setup(**setup_dict)


if __name__ == '__main__':
    main()
