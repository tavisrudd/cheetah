#!/usr/bin/env python
# $Id: Delimiters.py,v 1.12 2001/08/11 16:57:50 tavis_rudd Exp $
"""A dictionary of delimeter regular expressions that are used in Cheetah

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.12 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2001/08/11 16:57:50 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.12 $"[11:-2]


##################################################
## DEPENDENCIES ##

import re

##################################################
### CONSTANTS & GLOBALS ###

escCharLookBehind = r'(?:(?<=\A)|(?<!\\))'
tagClosure = r'(?:/#|\r\n|\n|\r)'
lazyTagClosure = r'(?:\r\n|\n|\r)'

delimiters = {
    '[%,%]':re.compile(r"\[%(.+?)%\]",re.DOTALL),
    '{,}':re.compile(r"{(.+?)}",re.DOTALL),
    '<%,%>':re.compile(r"<%(.+?)%>",re.DOTALL),

    'extendDirective':re.compile(escCharLookBehind +
                                 r'#extend[\f\t ]+(?P<parent>.*?)' +
                                 r'[\f\t ]*' + tagClosure, re.DOTALL),
    }



