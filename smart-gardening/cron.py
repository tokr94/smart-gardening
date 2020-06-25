import logging
import os
import sys

from argparse import ArgumentParser
from crontab import CronTab
from settings import *


if __name__ == '__main__':
    logging.getLogger().setLevel(LOG_LEVEL)

    if os.name == "nt":
        logging.error("Script cannot be used on Windows machine")

    else:
        parser = ArgumentParser()
        parser.add_argument('--user', type=str, required=False, help="Set the user of \
                            the crontab. Load from current users's crontab by default.")
        parser.add_argument('--disabled', required=False, action="store_true",
                            help="Set if this cron job should be disabled or not.")

        args = parser.parse_args()

        user = args.user
        enabled = not args.disabled

        cmd = sys.executable + " -u"
        cmd = cmd + " " + os.path.join(os.getcwd(), "cronjob.py")

        if not user:
            user = True  # load from current user's crontab

        cron = CronTab(user=user)
        present = False

        for tmp in cron.find_command(cmd):
            if present:
                logging.warning("More than one job found: %s" % tmp)
                continue

            present = True
            job = tmp

        if not present:
            job = cron.new(command=cmd, comment="created automatically")
            logging.info("Created new job for command: '%s'" % cmd)

        logging.info("Set pattern for cronjob '%s'" % CRON_PATTERN)
        job.setall(CRON_PATTERN)

        logging.info("Set cronjob enabled: %s" % enabled)
        job.enable(enabled)

        cron.write()
