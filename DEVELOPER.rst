
Some note for developers:

- to generate the sdist dist\piecash-XXX.tar.gz

python setup.py sdist


- to upload file on PyPI

twine upload dist\piecash-0.13.0.tar.gz

- to generate the modules `modules.rst' and `piecash.rst' in the \doc folder, go to the \doc folder and

`sphinx-apidoc -o . ../../piecash'
