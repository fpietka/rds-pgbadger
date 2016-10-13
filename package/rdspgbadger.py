#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
Fetch logs from RDS postgres instance and use them with pgbadger to generate a
report.
"""

import os
import errno
import boto3
from botocore.exceptions import (ClientError,
                                 EndpointConnectionError,
                                 NoRegionError,
                                 NoCredentialsError,
                                 PartialCredentialsError)
import argparse
from datetime import datetime
try:
    from shutil import which
except ImportError:
    from which import which

import subprocess

import logging

__version__ = "1.0.0"


def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('instance', help="RDS instance identifier")
parser.add_argument('--version', action='version',
                    version='%(prog)s {version}'.format(version=__version__))

parser.add_argument('-v', '--verbose', help="increase output verbosity",
                    action='store_true')
parser.add_argument('-d', '--date', help="get logs for given YYYY-MM-DD date",
                    type=valid_date)
parser.add_argument('-r', '--region', help="AWS region")
parser.add_argument('-o', '--output', help="Output folder for logs and report",
                    default='out')
parser.add_argument('-n', '--no-process', help="Only download logs",
                    action='store_true')

logger = logging.getLogger("rds-pgbadger")


def define_logger(verbose=False):
    logger = logging.getLogger("rds-pgbadger")
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logFormatter = logging.Formatter("%(asctime)s :: %(levelname)s :: "
                                     "%(message)s")
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)


def get_all_logs(dbinstance_id, output, date=None, region=None):
    if region:
        client = boto3.client("rds", region_name=region)
    else:
        client = boto3.client("rds")
    paginator = client.get_paginator("describe_db_log_files")
    response_iterator = paginator.paginate(
        DBInstanceIdentifier=dbinstance_id,
        FilenameContains="postgresql.log"
    )

    for response in response_iterator:
        for log in (name for name in response.get("DescribeDBLogFiles")
                    if date in name["LogFileName"]):
            response = client.download_db_log_file_portion(
                DBInstanceIdentifier=dbinstance_id,
                LogFileName=log["LogFileName"]
            )
            filename = "{}/{}".format(output, log["LogFileName"])
            logger.info("Downloading file %s", filename)
            if not os.path.exists(os.path.dirname(filename)):
                try:
                    os.makedirs(os.path.dirname(filename))
                except OSError as exc:  # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise
            with open(filename, "w") as logfile:
                logfile.write(response["LogFileData"])


def main():
    args = parser.parse_args()
    define_logger(args.verbose)

    if args.date:
        logger.info("Getting logs from %s", args.date)
    else:
        logger.info("Getting all logs")

    pgbadger = which("pgbadger")
    if not pgbadger:
        raise Exception("pgbadger not found")
    logger.debug("pgbadger found")

    try:
        get_all_logs(args.instance, args.output, args.date, args.region)
    except (EndpointConnectionError, ClientError) as e:
        logger.error(e)
        exit(1)
    except NoRegionError:
        logger.error("No region provided")
        exit(1)
    except NoCredentialsError:
        logger.error("Missing credentials")
        exit(1)
    except PartialCredentialsError:
        logger.error("Partial credentials, please check your credentials file")
        exit(1)

    if args.no_process:
        logger.info("File(s) downloaded. Not processing with PG Badger.")
    else:
        logger.info("Generating PG Badger report.")
        command = ("{} -p \"%t:%r:%u@%d:[%p]:\" -o {}/report.html "
                   "{}/error/*.log.*".format(pgbadger, args.output,
                                             args.output))
        logger.debug("Command:")
        logger.debug(command)
        subprocess.call(command, shell=True)
        logger.info("Done")


if __name__ == '__main__':
    main()
