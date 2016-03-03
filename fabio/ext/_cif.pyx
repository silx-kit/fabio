# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/kif/fabio
#
#    Copyright (C) 2015 European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
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
__doc__ = "Cif parser helper functions" 
__author__ = "Jerome Kieffer"
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__copyright__ = "2014, European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "30/10/2015"

cimport numpy
import numpy
import cython


@cython.boundscheck(False)
def split_tokens(bytes_text):
    """
    Separate the text representing a CIF file into a list of tokens. 

    @param bytes_text: the content of the CIF - file
    @type bytes_text:  8-bit string (str in python2 or bytes in python3)
    @return: list of all the fields of the CIF
    @rtype: list
    """
    cdef:
        unsigned char[:] ary = bytearray(bytes_text)
        bint in_comment=False, in_single_quote=False, in_double_quote=False, multiline=False, go_on=True
        int i=-1, start=-1, end=-1, imax
        char prev, next, cur = b"\n"
        bytes EOL = b'\r\n'
        bytes BLANK = b" \t\r\n"
        unsigned char SINGLE_QUOTE = b"'"
        unsigned char DOUBLE_QUOTE = b'"'
        unsigned char SEMICOLUMN = b';'
        unsigned char HASH = b"#"
        unsigned char UNDERSCORE = b"_"
        unsigned char DASH = b"-"
        unsigned char QUESTIONMARK = b"?"
        bytes BINARY_MARKER = b"--CIF-BINARY-FORMAT-SECTION--"
        int lbms = len(BINARY_MARKER)
    next = ary[0]
    imax = len(bytes_text) - 1
    fields = []
    while go_on:
        i += 1
        prev = cur
        cur = next
        if i < imax:
            next = ary[i+1]
        else:
            next = b"\n"
            go_on = False
#         print(i,chr(prev),chr(cur),chr(next),in_comment,in_single_quote,in_double_quote,multiline, start, cur ==SINGLE_QUOTE)
        # Skip comments
        if in_comment: 
            if cur in EOL:
                in_comment = False
            continue
                    
        if prev in EOL:
            if cur == HASH:
                in_comment = True
                continue
            if cur == SEMICOLUMN:
                if multiline:
                    fields.append(bytes_text[start:i].strip())
                    start = -1
                    multiline = False
                else:
                    multiline = True
                    start = i + 1
                continue 

        if multiline: 
            # Handle CBF
            if cur == DASH:
                if bytes_text[i:i + lbms] == BINARY_MARKER:
                    end = bytes_text[i + lbms:].find(BINARY_MARKER)
                    i += end + 2 * lbms
                    cur = ary[i]
                    next = ary[i + 1]
            continue

        # Handle single quote
        if cur == SINGLE_QUOTE:
            if (not in_single_quote) and (not in_double_quote) and (start < 0) and (prev in BLANK):
                start = i + 1
                in_single_quote = True
                continue
            if (in_single_quote) and (not in_double_quote) and (start >= 0) and (next in BLANK):
                fields.append(bytes_text[start:i].strip())
                start = -1
                in_single_quote = False
                continue
        if in_single_quote:
            continue
               
        # Handle double quote
        if cur == DOUBLE_QUOTE:
            if (not in_single_quote) and (not in_double_quote) and (start < 0) and (prev in BLANK):
                start = i + 1
                in_double_quote = True
                continue
            if (not in_single_quote) and (in_double_quote) and (start >= 0) and (next in BLANK):
                fields.append(bytes_text[start:i].strip())
                start = -1
                in_double_quote = False
                continue
        if in_double_quote:
            continue
        
        # Normal fields
        if cur in BLANK:
            if start >= 0:
                fields.append(bytes_text[start:i].strip())
                start = -1
        else:
            if start < 0:
                start = i
    if start >= 0:
        fields.append(bytes_text[start:].strip())
    return fields
