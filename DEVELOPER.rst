Some note for developers:
-------------------------

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
    4. python setup.py sdist upload

- to release a new version with gitflow:
    0. git flow release start 0.18.0
    1. update metadata.py
    2. update changelog
    3. git flow release finish
    4. checkout master branch in git
    5. python setup.py sdist upload
