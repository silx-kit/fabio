# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2016-2017 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/
"""Bunch of useful decorators"""

from __future__ import absolute_import, print_function, division

__authors__ = ["Jerome Kieffer", "H. Payno", "P. Knobel"]
__license__ = "MIT"
__date__ = "28/03/2019"

import sys
import logging
import functools
import traceback
from fabio.third_party import six

from .. import _version

depreclog = logging.getLogger("fabio.DEPRECATION")

deprecache = set([])


_CACHE_VERSIONS = {}


def deprecated(func=None, reason=None, replacement=None, since_version=None,
               only_once=True, skip_backtrace_count=1,
               deprecated_since=None):
    """
    Decorator that deprecates the use of a function

    :param str reason: Reason for deprecating this function
        (e.g. "feature no longer provided",
    :param str replacement: Name of replacement function (if the reason for
        deprecating was to rename the function)
    :param str since_version: First *fabio* version for which the function was
        deprecated (e.g. "0.5.0").
    :param bool only_once: If true, the deprecation warning will only be
        generated one time. Default is true.
    :param int skip_backtrace_count: Amount of last backtrace to ignore when
        logging the backtrace
    :param Union[int,str] deprecated_since: If provided, log it as warning
        since a version of the library, else log it as debug
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = func.func_name if sys.version_info[0] < 3 else func.__name__

            deprecated_warning(type_='Function',
                               name=name,
                               reason=reason,
                               replacement=replacement,
                               since_version=since_version,
                               only_once=only_once,
                               skip_backtrace_count=skip_backtrace_count,
                               deprecated_since=deprecated_since)
            return func(*args, **kwargs)
        return wrapper
    if func is not None:
        return decorator(func)
    return decorator


def deprecated_warning(type_, name, reason=None, replacement=None,
                       since_version=None, only_once=True,
                       skip_backtrace_count=0,
                       deprecated_since=None):
    """
    Function to log a deprecation warning

    :param str type_: Nature of the object to be deprecated:
        "Module", "Function", "Class" ...
    :param name: Object name.
    :param str reason: Reason for deprecating this function
        (e.g. "feature no longer provided",
    :param str replacement: Name of replacement function (if the reason for
        deprecating was to rename the function)
    :param str since_version: First *fabio* version for which the function was
        deprecated (e.g. "0.5.0").
    :param bool only_once: If true, the deprecation warning will only be
        generated one time for each different call locations. Default is true.
    :param int skip_backtrace_count: Amount of last backtrace to ignore when
        logging the backtrace
    :param Union[int,str] deprecated_since: If provided, log the deprecation
        as warning since a version of the library, else log it as debug.
    """
    if not depreclog.isEnabledFor(logging.WARNING):
        # Avoid computation when it is not logged
        return

    msg = "%s %s is deprecated"
    if since_version is not None:
        msg += " since fabio version %s" % since_version
    msg += "."
    if reason is not None:
        msg += " Reason: %s." % reason
    if replacement is not None:
        msg += " Use '%s' instead." % replacement
    msg += "\n%s"
    limit = 2 + skip_backtrace_count
    backtrace = "".join(traceback.format_stack(limit=limit)[0])
    backtrace = backtrace.rstrip()
    if only_once:
        data = (msg, type_, name, backtrace)
        if data in deprecache:
            return
        else:
            deprecache.add(data)

    if deprecated_since is not None:
        if isinstance(deprecated_since, six.string_types):
            if deprecated_since not in _CACHE_VERSIONS:
                hexversion = _version.calc_hexversion(string=deprecated_since)
                _CACHE_VERSIONS[deprecated_since] = hexversion
                deprecated_since = hexversion
            else:
                deprecated_since = _CACHE_VERSIONS[deprecated_since]
        log_as_debug = _version.hexversion < deprecated_since
    else:
        log_as_debug = False

    if log_as_debug:
        depreclog.debug(msg, type_, name, backtrace)
    else:
        depreclog.warning(msg, type_, name, backtrace)
