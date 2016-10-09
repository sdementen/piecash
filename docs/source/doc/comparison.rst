piecash and the official python bindings
========================================

piecash is an alternative to the python bindings that may be bundled with gnucash
(http://wiki.gnucash.org/wiki/Python_Bindings).

This page aims to give some elements of comparison between both python interfaces to better understand their relevancy
to your needs.
Information on the official python bindings may be incomplete (information gathered from mailing lists and wiki).


+---------------------------+----------------------------+---------------------------------------+
|                           |    piecash                 |      official python bindings         |
|                           |                            |                                       |
+===========================+============================+=======================================+
|  environment              |      Python 2.7            |      Python 2.7                       |
|                           |                            |                                       |
|                           |      Python 3.3/3.4/3.5    |                                       |
+---------------------------+----------------------------+---------------------------------------+
|  installation             |    pure python package     |    compilation (difficult on windows) |
|                           |                            |                                       |
|                           |    'pip install piecash'   |    binaries (available on Linux)      |
+---------------------------+----------------------------+---------------------------------------+
|  requires GnuCash         |      no                    |      yes                              |
+---------------------------+----------------------------+---------------------------------------+
|  gnucash files            |  SQL backend only          |     SQL backend and XML               |
+---------------------------+----------------------------+---------------------------------------+
|  documentation            |  yes (read the docs),      |     partial                           |
|                           |  actively developed        |                                       |
+---------------------------+----------------------------+---------------------------------------+
|  functionalities          |- creation of new books     |   all functionalities provided by     |
|                           |- read/browse objects       |                                       |
|                           |- create objects (basic)    |   the GnuCash C/C++ engine            |
|                           |- update online prices      |                                       |
+---------------------------+----------------------------+---------------------------------------+
| to be continued           |   ...                      |  ...                                  |
+---------------------------+----------------------------+---------------------------------------+
