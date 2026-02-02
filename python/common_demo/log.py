"""Implement some simple interface for logging."""

import logging
import logging.handlers
import datetime
import os
import inspect
import time
import sys


DEFAULT_LOG_FILENAME = '/tmp/pscli.log'
print2console = False
my_logger = None


def init(log_file=None, _print2console=False):
    global my_logger
    global print2console
    print2console = _print2console
    if my_logger is None:
        if log_file is not None:
            my_logger = logging.getLogger('pscli_logger')
            my_logger.setLevel(logging.INFO)
            handler = logging.handlers.RotatingFileHandler(log_file,
                                                          maxBytes=1024*1024*50,
                                                          backupCount=1)
            my_logger.addHandler(handler)


def debug(msg):
    global my_logger
    if my_logger is None:
        return
    global print2console
    if print2console:
        print msg
    current_time = datetime.datetime.now()
    caller_frame = inspect.stack()[1]
    frame = caller_frame[0]
    info = inspect.getframeinfo(frame)
    filename, line_number, func_name = my_logger.findCaller()
    msg = 'L4[%d][%s][%d]%s:%d:%s() %s' % (
        int(time.time()*1000000),
        current_time.strftime('%y-%m-%d;%H:%M:%S'), 
        os.getpid(),
        info.filename,
        info.lineno,
        info.function,
        msg,
    )
    my_logger.debug(msg)

def info(msg):
    global my_logger
    if my_logger is None:
        return
    global print2console
    if print2console:
        print msg
    current_time = datetime.datetime.now()
    caller_frame = inspect.stack()[1]
    frame = caller_frame[0]
    info = inspect.getframeinfo(frame)
    filename, line_number, func_name = my_logger.findCaller()
    msg = 'L3[%d][%s][%d]%s:%d:%s() %s' % (
        int(time.time()*1000000),
        current_time.strftime('%y-%m-%d;%H:%M:%S'),
        os.getpid(),
        info.filename,
        info.lineno,
        info.function,
        msg,
    )
    my_logger.info(msg)


def error(msg):
    global my_logger
    if my_logger is None:
        return
    global print2console
    if print2console:
        sys.stderr.write(msg)
        sys.stderr.write("\n")
    current_time = datetime.datetime.now()
    caller_frame = inspect.stack()[1]
    frame = caller_frame[0]
    info = inspect.getframeinfo(frame)
    filename, line_number, func_name = my_logger.findCaller()
    msg = 'L1[%d][%s][%d]%s:%d:%s() %s' % (
        int(time.time()*1000000),
        current_time.strftime('%y-%m-%d;%H:%M:%S'),
        os.getpid(),
        info.filename,
        info.lineno,
        info.function,
        msg,
    )
    my_logger.error(msg)


def warn(msg):
    global my_logger
    if my_logger is None:
        return
    global print2console
    if print2console:
        print msg
    current_time = datetime.datetime.now()
    caller_frame = inspect.stack()[1]
    frame = caller_frame[0]
    info = inspect.getframeinfo(frame)
    filename, line_number, func_name = my_logger.findCaller()
    msg = 'L2[%d][%s][%d]%s:%d:%s() %s' % (
        int(time.time()*1000000),
        current_time.strftime('%y-%m-%d;%H:%M:%S'),
        os.getpid(),
        info.filename,
        info.lineno,
        info.function,
        msg,
    )
    my_logger.warn(msg)
