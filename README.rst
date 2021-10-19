.. image:: https://api.codacy.com/project/badge/Grade/902dd72b33df408b8d1274890cd805db
   :target: https://www.codacy.com/project/fpietka/rds-pgbadger/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=fpietka/rds-pgbadger&amp;utm_campaign=Badge_Grade_Dashboard
   :alt: Grade
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
RDS-pgBadger
============

Fetches RDS log files and analyzes them with pgBadger_.

Prerequisites
-------------

Make sure your credentials are set in the ``~/.aws/credentials`` file.
Also, you can set a region in the ``~/.aws/config`` file, so passing region option to the script is not needed.
Alternatively you can define a profile in ``~/.aws/conf`` and ``~/.aws/credentials`` files, and use it with ``--profile=profile_name`` option.
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

For further details, please refer to Dalibo's pgBadger_ documentation.

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
* -n, --no-process : download log file(s), but do not process them with pgBadger.
* -X, --pgbadger-args : command-line arguments to pass to pgBadger
* --profile : by specifying a profile name, you use your configuration in ``.config`` and ``.credentials`` files. If specified, this profile is used to assume role defined in ``--assume-role`` option.
* --assume-role : by specifying a role you can use STS to assume a role, which is useful for cross account access with out having to setup the `.config` file. Format ``arn:aws:iam::<account_id>:<role_name>``

Known issue
-----------

In spite of the great work of askainet_, AWS API seems to be too instable, and sometimes download of big log files can
fail. In such case retrying a few minutes later seems to work.

see `pull request 10`_

Contribute
----------

For any request, feel free to make a pull request or fill an issue on Github_.

.. _pgBadger: http://dalibo.github.io/pgbadger/
.. _Github: https://github.com/fpietka/rds-pgbadger
.. _askainet: https://github.com/askainet
.. _pull request 10: https://github.com/fpietka/rds-pgbadger/pull/10
