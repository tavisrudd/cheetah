#!/usr/bin/env python
# $Id: TemplateCmdLineIface.py,v 1.2 2001/12/07 04:59:11 tavis_rudd Exp $

"""Provides a command line interface to compiled Cheetah template modules.

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
Version: $Revision: 1.2 $
Start Date: 2001/12/06
Last Revision Date: $Date: 2001/12/07 04:59:11 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.2 $"[11:-2]

##################################################
## DEPENDENCIES

import sys
import os
import getopt
import os.path

try:
    from cPickle import load
except ImportError:
    from pickle import load


#intra-package imports ...
from Version import version

##################################################
## GLOBALS & CONTANTS

True = (1==1)
False = (1==0)

class Error(Exception):
    pass

class CmdLineIface:
    """A command line interface to compiled Cheetah template modules."""

    def __init__(self, templateObj,
                 scriptName=os.path.basename(sys.argv[0]),
                 cmdLineArgs=sys.argv[1:]):

        self._template = templateObj
        self._scriptName = scriptName
        self._cmdLineArgs = cmdLineArgs

    def run(self):
        """The main program controller."""
        
        self._processCmdLineArgs()
        print self._template
        
    def _processCmdLineArgs(self):
        try:
            self._opts, self._args = getopt.getopt(
                self._cmdLineArgs, 'hep:', ['help',
                                            'env',
                                            'pickle=',
                                            ])

        except getopt.GetoptError, v:
            # print help information and exit:
            print v
            self.usage()
            sys.exit(2)
        
        for o, a in self._opts:
            if o in ('-h','--help'):
                self.usage()
                sys.exit()
            if o in ('-e','--env'):
                self._template.prependToSearchList(os.environ)
            if o in ('-p','--pickle'):
                self._template.prependToSearchList( load(a) )

    def usage(self):
        print \
"""Cheetah %(version)s template module command-line interface

Usage
-----
  %(scriptName)s [OPTION]

Options
-------
  -h, --help                 Print this help information
  
  -e, --env                  Use shell ENVIRONMENT variables to fill the
                             $placeholders in the template.
                             
  -p <file>, --pickle <file> Use a variables from a dictionary stored in Python
                             pickle file to 

Description
-----------

This interface allows you to execute a Cheetah template from the command line
and collect the output.  It can prepend the shell ENVIRONMENT or a pickled
Python dictionary to the template's $placeholder searchList, overriding the
defaults for the $placeholders.

""" % {'scriptName':self._scriptName,
       'version':version,
       }


