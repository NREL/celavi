"""Shared utilities and simple objects"""

import logging

LOGGER = logging.getLogger(name=__name__)


def logger(name='FPEAM'):
    """
    Produce Logger.

    :param name: [string]
    :return: [Logger]
    """

    return logging.getLogger(name=name)


def filepath(fpath, max_length=None):
    """
    Validate filepath <fpath> by asserting it exists.

    :param fpath: [string]
    :return: [bool] True on success
    """

    if max_length:
        try:
            assert len(fpath) <= int(max_length)
        except AssertionError:
            print('path too long')

    from os.path import exists, abspath, expanduser
    from pathlib import Path
    from pkg_resources import resource_filename

    # get a full path
    if fpath.startswith('~'):
        _fpath = expanduser(fpath)
    elif fpath.startswith('.'):
        _fpath = abspath(fpath)
    else:
        _fpath = fpath

    LOGGER.debug('validating %s' % fpath)

    # check if exists as regular file
    _exists = exists(_fpath)

    try:
        assert _exists
    except AssertionError:
        print('filepath does not exist')
    else:
        return Path(_fpath)

    # check if resource exists
    _exists = exists(_fpath)

    try:
        assert _exists
    except AssertionError:
        print('error - filepath')
    else:
        return _fpath


