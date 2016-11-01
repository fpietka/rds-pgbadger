.. image:: https://landscape.io/github/fpietka/rds-pgbadger/master/landscape.svg?style=flat
   :target: https://landscape.io/github/fpietka/rds-pgbadger/master
   :alt: Code Health
.. image:: https://img.shields.io/pypi/v/rdspgbadger.svg
   :target: https://pypi.python.org/pypi/rdspgbadger
   :alt: Version
.. image:: https://img.shields.io/pypi/pyversions/rdspgbadger.svg
   :target: https://pypi.python.org/pypi/rdspgbadger
   :alt: Python versions supported
.. image:: https://img.shields.io/pypi/l/rdspgbadger.svg
   :target: https://pypi.python.org/pypi/rdspgbadger
   :alt: License

============
RDS-Pgbadger
============

Fetches RDS log files and analyzes them with pgbadger_.

Prerequisites
-------------

Make sure your credentials are set in the ``~/.aws/credentials`` file.
Also, you can set a region in the ``~/.aws/config`` file, so passing region option to the script is not needed.
Last but not least, make sure you have ``pgbadger`` installed and reacheable from your ``$PATH``.

Parameter group
---------------

You will have to configure your database parameter group.

First of all, ensure ``log_min_duration_statement`` is set to ``0`` or higher, else you won't have anything to be parsed.

Then you must enable some other parameters to get more information in the logs.

+-----------------------------+-------+
| Parameter                   | Value |
+=============================+=======+
| log_checkpoints             | 1     |
+-----------------------------+-------+
| log_connections             | 1     |
+-----------------------------+-------+
| log_disconnections          | 1     |
+-----------------------------+-------+
| log_lock_waits              | 1     |
+-----------------------------+-------+
| log_temp_files              | 0     |
+-----------------------------+-------+
| log_autovacuum_min_duration | 0     |
+-----------------------------+-------+

Also make sure ``lc_messages`` is either at engine default or set to ``C``.

For further details, please refer to Dalibo's pgbadger_ documentation.

Installation
------------

You can install it using ``pip``::

 $ pip install rdspgbadger

Usage
-----

To build a ``pgbadger`` report, just run the following (replacing ``instanceid`` by your instance ID)::

 $ rds-pgbadger instanceid

Options
-------

Only the Instance ID is mandatory, but there are also other options you can use:

* -d, --date : by default the script downloads all the available logs. By specifying a date in the format ``YYYY-MM-DD``, you can then download only that day's logs.
* -r, --region : by default the script use the region specified in your AWS config file. If none, or if you wish to change it, you can use this option to do so.
* -o, --output : by default the script outputs log files and reports to the ``out`` folder. This option allows you to change it.
* -n, --no-process : download log file(s), but do not process them with PG Badger.

Contribute
----------

For any request, feel free to make a pull request or fill an issue on Github_.

.. _pgbadger: http://dalibo.github.io/pgbadger/
.. _Github: https://github.com/fpietka/rds-pgbadger
