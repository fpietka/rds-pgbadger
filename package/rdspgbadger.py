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

__version__ = "1.2.3"


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
parser.add_argument('--assume-role', help="AWS STS AssumeRole")
parser.add_argument('--profile', help="AWS config profile")
parser.add_argument('-r', '--region', help="AWS region")
parser.add_argument('-o', '--output', help="Output folder for logs and report",
                    default='out')
parser.add_argument('-n', '--no-process', help="Only download logs",
                    action='store_true')
parser.add_argument('-X', '--pgbadger-args', help="pgbadger arguments",
                    default='')
parser.add_argument('-f', '--format', help="Format of the report",
                    choices=['text', 'html', 'bin', 'json', 'tsung'],
                    default='html')

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


def get_all_logs(dbinstance_id, output,
                 date=None, region=None, assume_role=None, profile=None):

    session_args = {
        'profile_name': profile,
        'region_name': region
    }
    session = boto3.Session(**session_args)

    rds_client = session.client("rds")
    if assume_role:
        sts_client = session.client('sts')
        assumed_role_object = sts_client.assume_role(
            RoleArn=assume_role,
            RoleSessionName="RDSPGBadgerSession1"
        )

        credentials = assumed_role_object['Credentials']
        boto_args = {
            'aws_access_key_id': credentials['AccessKeyId'],
            'aws_secret_access_key': credentials['SecretAccessKey'],
            'aws_session_token': credentials['SessionToken']
        }
        logger.info('STS Assumed role %s', assume_role)
        rds_client = boto3.client("rds", **boto_args)

    paginator = rds_client.get_paginator("describe_db_log_files")
    response_iterator = paginator.paginate(
        DBInstanceIdentifier=dbinstance_id,
        FilenameContains="postgresql.log"
    )

    for response in response_iterator:
        for log in (name for name in response.get("DescribeDBLogFiles")
                    if not date or date in name["LogFileName"]):
            filename = "{}/{}".format(output, log["LogFileName"])
            logger.info("Downloading file %s", filename)
            try:
                os.remove(filename)
            except OSError:
                pass
            write_log(rds_client, dbinstance_id, filename, log["LogFileName"])


def write_log(client, dbinstance_id, filename, logfilename):
    marker = "0"
    initial_max_number_of_lines = 10000
    max_number_of_lines = initial_max_number_of_lines
    truncated_string = " [Your log message was truncated]"
    slice_length = len(truncated_string) + 1

    response = client.download_db_log_file_portion(
        DBInstanceIdentifier=dbinstance_id,
        LogFileName=logfilename,
        Marker=marker,
        NumberOfLines=max_number_of_lines
    )

    while True:
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        with open(filename, "a") as logfile:
            if 'LogFileData' in response:
                if truncated_string in response["LogFileData"][-slice_length:]:
                    downloaded_lines = response["LogFileData"].count("\n")
                    if downloaded_lines == 0:
                        raise Exception(
                            "No line was downloaded in last portion!")
                    max_number_of_lines = max(int(downloaded_lines / 2), 1)
                    logger.info("Log truncated, retrying portion with "
                                "NumberOfLines = {0}".format(
                                    max_number_of_lines))
                else:
                    max_number_of_lines = initial_max_number_of_lines
                    marker = response["Marker"]
                    logfile.write(response["LogFileData"])

        if ('LogFileData' in response and
                not response["LogFileData"].rstrip("\n") and
                not response["AdditionalDataPending"]):
            break

        response = client.download_db_log_file_portion(
            DBInstanceIdentifier=dbinstance_id,
            LogFileName=logfilename,
            Marker=marker,
            NumberOfLines=max_number_of_lines
        )


def main():
    args = parser.parse_args()
    define_logger(args.verbose)

    if args.date:
        logger.info("Getting logs from %s", args.date)
    else:
        logger.info("Getting all logs")

    if args.profile:
        logger.info("Getting logs with AWS %s profile", args.profile)
    else:
        logger.info("No profile defined. Default configuration are used to get logs")

    if args.assume_role:
        logger.info("Getting logs with AWS %s role", args.assume_role)

    pgbadger = which("pgbadger")
    if not pgbadger:
        raise Exception("pgbadger not found")
    logger.debug("pgbadger found")

    try:
        get_all_logs(
                args.instance,
                args.output,
                date=args.date,
                region=args.region,
                assume_role=args.assume_role,
                profile=args.profile
            )
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
        command = ("{} -p \"%t:%r:%u@%d:[%p]:\" {} -o {}/report.{} "
                   "{}/error/*.log.* ".format(pgbadger,
                                              args.pgbadger_args,
                                              args.output,
                                              args.format,
                                              args.output))
        logger.debug("Command: %s", command)
        subprocess.call(command, shell=True)
        logger.info("Done")


if __name__ == '__main__':
    main()
