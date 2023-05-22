"""Logging module"""
from __future__ import annotations

import logging
import os
from datetime import datetime as dt

from rich.logging import RichHandler

from rawtools import __version__


def configure(module_name=None, *args, **kwargs):
    """Set up log files and associated handlers"""
    verbose = kwargs.get('verbose', False)
    path = kwargs.get('path', ['.'])
    write_log_files = kwargs.get('write_log_files', True)

    # Configure logging, stderr and file logs
    logging_level = logging.INFO
    if verbose:
        logging_level = logging.DEBUG

    logFormatter = logging.Formatter(
        '%(asctime)s - [%(levelname)-4.8s] - %(filename)s %(lineno)d - %(message)s',
    )

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)

    consoleHandler = RichHandler()
    consoleHandler.setLevel(logging_level)
    rootLogger.addHandler(consoleHandler)

    if write_log_files:
        # Set project-level logging
        if module_name is not None:
            logfile_basename = (
                f"{dt.today().strftime('%Y-%m-%d_%H-%M-%S')}_{module_name}.log"
            )
        rpath = os.path.realpath(path[0])
        if os.path.isdir(rpath):
            dname = rpath
        else:
            dname = os.path.dirname(rpath)
        lfp = os.path.join(dname, logfile_basename)  # base log file path
        fileHandler = logging.FileHandler(lfp)
        fileHandler.setFormatter(logFormatter)
        # always show debug statements in log file
        fileHandler.setLevel(logging.DEBUG)
        rootLogger.addHandler(fileHandler)

        # TODO: determine if running as system/root or as regular user
        # If regular user, store logs in .local/cache
        sdfp = os.path.join(
            '/',
            'var',
            'log',
            'rawtools',
            module_name,
        )  # system directory file path
        if not os.path.exists(sdfp):
            os.makedirs(sdfp)
        slfp = os.path.join(sdfp, logfile_basename)  # system log file path
        syslogFileHandler = logging.FileHandler(slfp)
        syslogFileHandler.setFormatter(logFormatter)
        syslogFileHandler.setLevel(
            logging.DEBUG,
        )  # always show debug statements in log file
        rootLogger.addHandler(syslogFileHandler)

    logging.debug(f'Running {__package__}.{module_name} {__version__}')
    logging.debug(f'Runtime arguments: {kwargs}')
