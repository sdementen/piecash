Developer Notes
===============

This is a community-maintained fork. See README for the original project link.

Development Setup
-----------------

- to prepare a virtualenv for dev purposes::

    pipenv install -e .[test,doc]

- to generate the sdist dist\piecash-XXX.tar.gz::

    python setup.py sdist

- to upload file on PyPI::

    python setup.py sdist upload

- to generate the modules `modules.rst` and `piecash.rst` in the docs\source\doc folder, go to the docs\source\doc folder and::

    sphinx-apidoc -o . ../../piecash

- to build the doc (do not forget to `pipenv install -e .[doc]` before)::

    cd docs
    make html

  The documentation will be available through docs/build/html/index.html.

- to test via tox and conda, create first the different environment with the relevant versions of python::

    conda create -n py35 python=3.5 virtualenv
    conda create -n py36 python=3.6 virtualenv
    ...

  adapt tox.ini to point to the proper conda envs and then run::

    tox

- to release a new version:
    1. update metadata.py
    2. update changelog
    3. `tag MM.mm.pp`
    4. twine upload dist/* --repository piecash

- to release a new version with gitflow:
    0. git flow release start 0.18.0
    1. update metadata.py
    2. update changelog
    3. git flow release finish
    4. checkout master branch in git
    5. python setup.py sdist upload

Maintenance (fork)
-----------------

- Run tests locally: ``pytest tests/ -v`` (exclude ``test_integration.py`` if no Postgres/MySQL)
- Check dependencies: ``pip install pip-audit && pip-audit``
- For PyPI release without original maintainer access, consider publishing as ``piecash-community``

Piecash2 Migration Checklist (future)
-------------------------------------

Reference: https://github.com/sdementen/piecash2

Piecash2 uses SQLAlchemy 2 and sqlacodegen_v2 for schema generation. Below is a
prioritized list for porting piecash features to piecash2:

**Phase 1 - Core (piecash2 has open_book only)**

- [ ] create_book
- [ ] High-level Book API (accounts, commodities, transactions as properties)
- [ ] Account.get_balance (with at_date, commodity conversion)
- [ ] Commodity.currency_conversion (with at_date for #209)

**Phase 2 - Scripts & Export**

- [ ] Ledger export (scripts/ledger.py) with #238 fix (no thousand separators)
- [ ] QIF export
- [ ] Price import/export (CSV)
- [ ] piecash CLI (scripts/export.py)

**Phase 3 - Advanced**

- [ ] Business (invoices, customers, vendors)
- [ ] KVP/slots
- [ ] Lot handling, scrub_account (FIFO from #237)
