Some note for developers:
-------------------------

- to generate the sdist dist\piecash-XXX.tar.gz::

    python setup.py sdist

- to upload file on PyPI::

    twine upload dist\piecash-0.13.0.tar.gz

- to generate the modules `modules.rst` and `piecash.rst` in the \doc folder, go to the \doc folder and::

    sphinx-apidoc -o . ../../piecash

- to build the doc (do not forget to `pip install -r requirements-dev.txt` before)::

    cd docs/source
    sphinx-build . build

  The documentation will be available through docs/source/build/index.html.

- to test via tox and conda, create first the different environment with the relevant versions of python::

    conda create -n py27 python=2.7 virtualenv
    conda create -n py35 python=3.5 virtualenv
    ...

  adapt tox.ini to point to the proper conda envs and then run::

    tox

- to release a new version:
    1. update metadata.py
    2. update changelog
    3. `tag MM.mm.pp`
