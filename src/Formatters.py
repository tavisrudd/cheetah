#!/usr/bin/env python
# $Id: Formatters.py,v 1.4 2001/08/16 22:15:17 tavis_rudd Exp $
"""Formatters Cheetah's $placeholders

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.4 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/08/16 22:15:17 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.4 $"[11:-2]

##################################################
## DEPENDENCIES ##

# intra-package imports ...

##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##

class Error(Exception):
    pass

class BaseClass:
    """A baseclass for the Cheetah Formatters."""
    
    def __init__(self, templateObj):
        """Setup a ref to the templateObj.  Subclasses should call this method."""
        self.setting = templateObj.setting
        self.settings = templateObj.settings

    def generateAutoArgs(self):
        
        """This hook allows the formatters to generate an arg-list that will be
        appended to the arg-list of a $placeholder tag when it is being
        translated into Python code during the template compilation process. See
        the 'Pager' formatter class for an example."""
        
        return ''
        
    def format(self, val, **kw):
        
        """Replace None with an empty string.  Reimplement this method if you
        want more advanced formatting."""
        
        if val == None:
            return ''
        return str(val)

    
## make an alias
ReplaceNone = BaseClass

class MaxLen(BaseClass):
    def format(self, val, **kw):
        """Replace None with '' and cut off at maxlen."""
        if val == None:
            return ''
        output = str(val)
        if kw.has_key('maxlen') and len(output) > kw['maxlen']:
            return output[:kw['maxlen']]
        return output


class Pager(BaseClass):
    def __init__(self, templateObj):
        BaseClass.__init__(self, templateObj)
        self._IDcounter = 0
        
    def buildQString(self,varsDict, updateDict):
        finalDict = varsDict.copy()
        finalDict.update(updateDict)
        qString = '?'
        for key, val in finalDict.items():
            qString += str(key) + '=' + str(val) + '&'
        return qString

    def generateAutoArgs(self):
        ID = str(self._IDcounter)
        self._IDcounter += 1
        return ', trans=trans, ID=' + ID
    
    def format(self, val, **kw):
        """Replace None with '' and cut off at maxlen."""
        if val == None:
            return ''
        output = str(val)
        if kw.has_key('trans') and kw['trans']:
            ID = kw['ID']
            marker = kw.get('marker', '<split>')
            req = kw['trans'].request()
            URI = req.environ()['SCRIPT_NAME'] + req.environ()['PATH_INFO']
            queryVar = 'pager' + str(ID) + '_page'
            fields = req.fields()
            page = int(fields.get( queryVar, 1))
            pages = output.split(marker)
            output = pages[page-1]
            output += '<BR>'
            if page > 1:
                output +='<A HREF="' + URI + self.buildQString(fields, {queryVar:max(page-1,1)}) + \
                          '">Previous Page</A>&nbsp;&nbsp;&nbsp;'
            if page < len(pages):
                output += '<A HREF="' + URI + self.buildQString(
                    fields,
                    {queryVar:
                     min(page+1,len(pages))}) + \
                     '">Next Page</A>' 

            return output
        return output

