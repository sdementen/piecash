piecash and the official python bindings
========================================

piecash is an alternative to the python bindings that may be bundled with gnucash
(http://wiki.gnucash.org/wiki/Python_Bindings).

This page aims to give some elements of comparison between both python interfaces to better understand their relevancy
to your needs.
Information on the official python bindings may be incomplete (information gathered from mailing lists and wiki).

Gnucash 3.0.x series
--------------------

+------------------+----------------------------------+------------------------------------------+
|                  | piecash (>=1.0.0)                | official python bindings (gnucash 3.0.n) |
+------------------+----------------------------------+------------------------------------------+
| book format      | gnucash 3.0.n                    | gnucash 3.0.n                            |
+------------------+----------------------------------+------------------------------------------+
| environment      | Python 3.6/3.7/3.8/3.9           | Python 3                                 |
+------------------+----------------------------------+------------------------------------------+
| installation     | pure python package              | compilation (difficult on windows)       |
|                  | 'pip install piecash'            | binaries (available on Linux)            |
+------------------+----------------------------------+------------------------------------------+
| requires GnuCash | no                               | yes                                      |
+------------------+----------------------------------+------------------------------------------+
| runs on Android  | yes                              | no                                       |
+------------------+----------------------------------+------------------------------------------+
| gnucash files    | SQL backend only                 | SQL backend and XML                      |
+------------------+----------------------------------+------------------------------------------+
| documentation    | yes (read the docs)              | partial                                  |
|                  | actively developed               |                                          |
+------------------+----------------------------------+------------------------------------------+
| functionalities  | creation of new books            | all functionalities provided             |
|                  | read/browse objects              | by the GnuCash C/C++ engine              |
|                  | create objects (basic)           |                                          |
|                  | update online prices             |                                          |
+------------------+----------------------------------+------------------------------------------+

Gnucash 2.6.x series
--------------------

+------------------+----------------------------------+------------------------------------------+
|                  | piecash (<=0.18.0)               | official python bindings (gnucash 2.6.n) |
+------------------+----------------------------------+------------------------------------------+
| book format      | gnucash 2.6.n                    | gnucash 2.6.n                            |
+------------------+----------------------------------+------------------------------------------+
| environment      | Python 2.7 & 3.3/3.4/3.5/3.6     | Python 2.7                               |
+------------------+----------------------------------+------------------------------------------+
| installation     | pure python package              | compilation (difficult on windows)       |
|                  | 'pip install piecash'            | binaries (available on Linux)            |
+------------------+----------------------------------+------------------------------------------+
| requires GnuCash | no                               | yes                                      |
+------------------+----------------------------------+------------------------------------------+
| runs on Android  | yes                              | no                                       |
+------------------+----------------------------------+------------------------------------------+
| gnucash files    | SQL backend only                 | SQL backend and XML                      |
+------------------+----------------------------------+------------------------------------------+
| documentation    | yes (read the docs)              | partial                                  |
|                  | actively developed               |                                          |
+------------------+----------------------------------+------------------------------------------+
| functionalities  | creation of new books            | all functionalities provided             |
|                  | read/browse objects              | by the GnuCash C/C++ engine              |
|                  | create objects (basic)           |                                          |
|                  | update online prices             |                                          |
+------------------+----------------------------------+------------------------------------------+