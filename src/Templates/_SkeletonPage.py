#!/usr/bin/env python
# $Id: _SkeletonPage.py,v 1.7 2002/02/26 02:20:52 tavis_rudd Exp $
"""A baseclass for the SkeletonPage template

Meta-Data
==========
Author: Tavis Rudd <tavis@calrudd.com>,
Version: $Revision: 1.7 $
Start Date: 2001/04/05
Last Revision Date: $Date: 2002/02/26 02:20:52 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__revision__ = "$Revision: 1.7 $"[11:-2]

##################################################
## DEPENDENCIES ##

import time, types, os, sys

# intra-package imports ...
from Cheetah.Template import Template


##################################################
## GLOBALS AND CONSTANTS ##

True = (1==1)
False = (0==1)

##################################################
## CLASSES ##
        
class _SkeletonPage(Template):
    """A baseclass for the SkeletonPage template"""
    
    def __init__(self, *args, **KWs):
        Template.__init__(self, *args, **KWs)
        self._initializeSettings()
        self.addToSearchList(self.settings())
        
    def _initializeSettings(self):
        ## Default values for the names embedded in the template ##
        docType = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" ' + \
                  '"http://www.w3.org/TR/html4/loose.dtd">'

        #docType = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' + \
        #'"http://www.w3.org/TR/xhtml1l/DTD/transitional.dtd">'
        
        title = ''
        siteDomainName = 'www.example.com'
        siteCredits = 'Designed & Implemented by Tavis Rudd'
        siteCopyrightName = "Tavis Rudd"
    
        metaTags = {}
        # metaTags = {'HTTP_EQUIV':{'test':1234}, 'NAME':{'test':1234,'test2':1234} }
        stylesheets = {}
        # stylesheets = {'.cssClassName':'stylesheetCode'}
        stylesheetsOrder = []
        # stylesheetsOrder = ['.cssClassName',]
        stylesheetLibs = {}
        # stylesheetLibs = {'libName':'libSrcPath'}
        javascriptLibs = {}
        javascriptTags = {}
        # javascriptLibs = {'libName':'libSrcPath'}
        bodyTagAttribs = {}
   
        defaults = locals().copy()
        del defaults['self']
        self.updateSettings(defaults)
   

    def metaTags(self):
        """Return a formatted vesion of the self._metaTags dictionary, using the
        formatMetaTags function from Cheetah.Macros.HTML"""
        
        return self.formatMetaTags(self.setting('metaTags'))
    
    def stylesheetTags(self):
        """Return a formatted version of the self._stylesheetLibs and
        self._stylesheets dictionaries.  The keys in self._stylesheets must
        be listed in the order that they should appear in the list
        self._stylesheetsOrder, to ensure that the style rules are defined in
        the correct order."""
        
        stylesheetTagsTxt = ''
        for title, src in self.setting('stylesheetLibs').items():
            stylesheetTagsTxt += '<link rel="stylesheet" type="text/css" href="' + str(src) + '" />\n'

        if not self.setting('stylesheetsOrder'):
            return stylesheetTagsTxt
        
        stylesheetTagsTxt += '<style type="text/css"><!--\n'
        for identifier in self.setting('stylesheetsOrder'):
            if not self.setting('stylesheets').has_key(identifier):
                warning = '# the identifier ' + identifier + \
                          'was in stylesheetsOrder, but not in stylesheets'
                print warning
                stylesheetTagsTxt += warning
                continue
                    
            attribsDict = self.setting('stylesheets')[identifier]
            cssCode = ''
            attribCode = ''
            for k, v in attribsDict.items():
                attribCode += str(k) + ': ' + str(v) + '; '
            attribCode = attribCode[:-2] # get rid of the last semicolon
                
            cssCode = '\n' + identifier + ' {' +  attribCode + '}'
            stylesheetTagsTxt += cssCode
            
        stylesheetTagsTxt += '\n//--></style>\n'

        return stylesheetTagsTxt

    def javascriptTags(self):
        """Return a formatted version of the javascriptTags and
        javascriptLibs dictionaries.  Each value in javascriptTags
        should be a either a code string to include, or a list containing the
        JavaScript version number and the code string. The keys can be anything.
        The same applies for javascriptLibs, but the string should be the
        SRC filename rather than a code string."""
        
        javascriptTagsTxt = []
        for key, details in self.setting('javascriptTags').items():
            if type(details) not in (types.ListType, types.TupleType):
                details = ['',details]

            javascriptTagsTxt += ['<script language="JavaScript', str(details[0]),
                                      '" ><!--\n', str(details[0]), '\n//--></script>\n']


        for key, details in self.setting('javascriptLibs').items():
            if type(details) not in (types.ListType, types.TupleType):
                details = ['',details]

            javascriptTagsTxt += ['<script language="JavaScript', str(details[0]),
                                      '" src="', str(details[1]), '" />\n']
        return ''.join(javascriptTagsTxt)
    
    def bodyTag(self):
        """Create a body tag from the entries in the dict bodyTagAttribs."""
        return self.formHTMLTag('body', self.setting('bodyTagAttribs'))


    def imgTag(self, src, alt='', width=None, height=None, border=0):
        
        """Dynamically generate an image tag.  Cheetah will try to convert the
        src argument to a WebKit serverSidePath relative to the servlet's
        location. If width and height aren't specified they are calculated using
        PIL or ImageMagick if available."""
        
        src = self.normalizePath(src)
        

        if not width or not height:
            try:                    # see if the dimensions can be calc'd with PIL
                import Image
                im = Image.open(src)
                calcWidth, calcHeight = im.size
                del im
                if not width: width = calcWidth
                if not height: height = calcHeight

            except:
                try:                # try imageMagick instead
                    calcWidth, calcHeight = os.popen(
                        'identify -format "%w,%h" ' + src).read().split(',')
                    if not width: width = calcWidth
                    if not height: height = calcHeight
        
                except:
                    pass
                
        if width and height:
            return ''.join(['<img src="', src, '" width="', str(width), '" height="', str(height),
                           '" alt="', alt, '" border="', str(border), '" />'])
        elif width:
            return ''.join(['<img src="', src, '" width="', str(width),
                           '" alt="', alt, '" border="', str(border), '" />'])
        elif height:
            return ''.join(['<img src="', src, '" height="', str(height),
                           '" alt="', alt, '" border="', str(border), '" />'])
        else:
            return ''.join(['<img src="', src, '" alt="', alt, '" border="', str(border),'" />'])


    def currentYr(self):
        """Return a string representing the current yr."""
        return time.strftime("%Y",time.localtime(time.time()))
    
    def currentDate(self, formatString="%b %d, %Y"):
        """Return a string representing the current localtime."""
        return time.strftime(formatString,time.localtime(time.time()))
    
    def spacer(self, width=1,height=1):
        return '<img src="spacer.gif" width="%s" height="%s" alt="" />'% (str(width), str(height))
    
    def formHTMLTag(self, tagName, attributes={}):
        """returns a string containing an HTML <tag> """
        tagTxt = ['<', tagName.lower()]
        for name, val in attributes.items():
            tagTxt += [' ', name.lower(), '="', str(val),'"']
        tagTxt.append('>')
        return ''.join(tagTxt)
    
    def formatMetaTags(self, metaTags):
        """format a dict of metaTag definitions into an HTML version"""
        metaTagsTxt = []
        if metaTags.has_key('HTTP_EQUIV'):
            for http_equiv, contents in metaTags['HTTP_EQUIV'].items():
                metaTagsTxt += ['<meta http_equiv="', str(http_equiv), '" contents="',
                                str(contents), '" />\n']
                
        if metaTags.has_key('NAME'):
            for name, contents in metaTags['NAME'].items():
                metaTagsTxt += ['<meta name="', str(name), '" contents="', str(contents),
                                '" />\n']
        return ''.join(metaTagsTxt)
    
