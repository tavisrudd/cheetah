#!/usr/bin/env python
# $Id: Parser.py,v 1.18 2001/09/16 00:05:57 tavis_rudd Exp $
"""Parser base-class for Cheetah's TagProcessor class and for the Template class

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@calrudd.com>
License: This software is released for unlimited distribution under the
         terms of the Python license.
Version: $Revision: 1.18 $
Start Date: 2001/08/01
Last Revision Date: $Date: 2001/09/16 00:05:57 $
"""
__author__ = "Tavis Rudd <tavis@calrudd.com>"
__version__ = "$Revision: 1.18 $"[11:-2]

##################################################
## DEPENDENCIES ##

import re
from re import DOTALL, MULTILINE
from types import StringType
from tokenize import tokenprog

# intra-package imports ...
from Utilities import lineNumFromPos
from NameMapper import valueFromSearchList, valueForName
##################################################
## CONSTANTS & GLOBALS ##

True = (1==1)
False = (0==1)

##################################################
## FUNCTIONS ##

def escapeRegexChars(string):
    return re.sub(r'([\$\^\*\+\.\?\{\}\[\]\(\)\|\\])', r'\\\1' , string)

def matchTokenOrfail(text, pos):
    match = tokenprog.match(text, pos)
    if match is None:
        raise SyntaxError(text, pos)
    return match, match.end()

def separateTagsFromText(initialText, startTagRE, endTagRE):
    """breaks a string up into a textVsTagsList where the odd items are plain
    text and the even items are the contents of the tags."""

    chunks = startTagRE.split(initialText)
    textVsTagsList = []
    for chunk in chunks:
        textVsTagsList.extend(endTagRE.split(chunk))
    return textVsTagsList

def processTextVsTagsList(textVsTagsList, tagProcessorFunction):
    """loops through textVsTagsList - the output from separateTagsFromText() -
    and filters all the tag items with the tagProcessorFunction"""
    
    ## odd items are plain text, even ones are tags
    processedList = textVsTagsList[:]
    for i in range(1, len(processedList), 2):
        processedList[i] = tagProcessorFunction(processedList[i])
    return processedList

# re tools
def group(*choices): return '(' + '|'.join(choices) + ')'
def nongroup(*choices): return '(?:' + '|'.join(choices) + ')'
def namedGroup(name, *choices): return '(P:<' + name +'>' + '|'.join(choices) + ')'
def any(*choices): return apply(group, choices) + '*'
def maybe(*choices): return apply(group, choices) + '?'

##################################################
## Regex chunks for the parser ##


#generic
namechars = "abcdefghijklmnopqrstuvwxyz" \
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_";


WS = r'[ \f\t]*'                        # Whitespace
EOL = r'\r\n|\n|\r'
EOLZ = EOL + r'|\Z'
escCharLookBehind = nongroup(r'(?<=\A)',r'(?<!\\)')
name = r'[a-zA-Z_]\w*'
nameCharLookAhead = r'(?=[A-Za-z_])'

#placeholder-specific
validSecondCharsLookAhead = r'(?=[A-Za-z_\*\{])'



##################################################
## CLASSES ##

class SyntaxError(ValueError):
    def __init__(self, text, pos):
        self.text = text
        self.pos = pos
    def __str__(self):
        lineNum = lineNumFromPos(self.text, self.pos)
        return "unfinished expression on line %d (char %d) in: \n%s " % (
            lineNum, self.pos, self.text)
        # @@ augment this to give the line number and show a normal version of the txt

class Error(Exception):
    pass

class Parser:
    """This is an abstract base-class that is inherited by both the Template and
    TagProcessor classes.  It provides universal access to Cheetah's generic
    parsing tools, the $placeholder parsing tools, and a few tools for
    #directive parsing.

    When it is inherited by TagProcessor and all TagProcessor's subclasses a
    reference to the master templateObj must be supplied as the 'templateObj'
    argument.  This is done automatically when the Template class sets up its
    TagProcessors.  This approach allows the methods of 'Template' and the
    methods of this class to coexist seemlessly."""
    
    def __init__(self, templateObj=None):
        """This method sets up some internal references to the master
        templateObj if a reference is supplied. Otherwise, it will assume that it
        IS the master templateObj and will setup the regex's the parser
        uses. This method must be called by subclasses."""

        if templateObj:            
            ## setup some method mappings for convenience
            self.settings = templateObj.settings
            self.setting = templateObj.setting
            self.searchList = templateObj.searchList

            ## setup some attribute mappings
            self._placeholderREs = templateObj._placeholderREs
            self._directiveREbits = templateObj._directiveREbits

        else:                           # iAmATemplateObj
            self.makePlaceholderREs()       # inherited from the Parser class
            self.makeDirectiveREbits()

    ## regex setup ##

    def makePlaceholderREs(self):
        
        """Setup the regexs for placeholder parsing.  Do it here so all the
        TagProcessors don't have to create them for themselves.

        All $placeholders are translated into valid Python code by swapping
        'placeholderStartToken' ($) for 'marker'.  This marker is then used by
        the parser to find the start of each placeholder and allows $vars in
        function arg lists to be parsed correctly.  '$x()' becomes '
        placeholderTag.x()' when it's marked.

        The marker starts with a space to allow $var$var to be parsed correctly.
        $a$b is translated to --placeholderTag.a placeholderTag.b-- instead of
        --placeholderTag.aplaceholderTag.b--, which the parser would mistake for
        a single $placeholder The extra space is removed by the parser."""
        
        REs = self._placeholderREs = {}
        marker = self.setting('placeholderMarker')
        REs['nameMapperChunk'] = re.compile(
            marker +
            r'(?:CACHED\.|REFRESH_[0-9]+(?:_[0-9]+){0,1}\.){0,1}([A-Za-z_0-9\.]+)')

        markerEscaped = escapeRegexChars(marker)
        markerLookBehind= r'(?:(?<=' + markerEscaped + ')|(?<=' + markerEscaped + '\{))'
        
        REs['cachedTags'] = re.compile(
            markerLookBehind + r'\*' + nameCharLookAhead)
        REs['refreshTag'] = re.compile(markerLookBehind +
                                                    r'\s*\*([0-9\.]+?)\*' +
                                                    nameCharLookAhead)
        REs['startToken'] = re.compile(
            escCharLookBehind +
            escapeRegexChars(self.setting('placeholderStartToken')) +
            validSecondCharsLookAhead)

        
    def makeDirectiveREbits(self):
        """Construct the regex bits that are used in directive parsing."""
        startToken = self.setting('directiveStartToken')
        endToken = self.setting('directiveEndToken')
        startTokenEsc = escapeRegexChars(startToken)
        endTokenEsc = escapeRegexChars(endToken)
        endTokenEscGrp = nongroup(endTokenEsc)
        start = escCharLookBehind + startTokenEsc
        start_gobbleWS = '(?:\A|^)' + WS + startTokenEsc
        
        endGrp = nongroup(endTokenEsc, EOLZ)
        lazyEndGrp = nongroup(EOLZ)

        bits = self._directiveREbits = locals().copy()
        del bits['self']

    def simpleDirectiveReList(self, directiveReChunk):
        
        """Return a list of two regexs for a simple directive: one
        whitespace-gobbling and one plain.  A simple directive one that only has
        a start-tag, such as #cache, #stop, or #include."""
        
        bits = self._directiveREbits
        plainRE = re.compile(bits['start']  +
                             directiveReChunk +
                             bits['endGrp'])
        gobbleRE = re.compile(bits['start_gobbleWS']  +
                             directiveReChunk +
                             bits['lazyEndGrp'], MULTILINE)
        return [gobbleRE, plainRE]


    ## generic parsing methods ##
    
    def splitExprFromTxt(self, txt, MARKER):

        """Split a text string containing marked placeholders
        (e.g. self.mark(txt)) into a list of plain text VS placeholders.

        This is the core of the placeholder parsing!

        Modified from code written by Ka-Ping Yee for his itpl module.
        """
        
        chunks = []
        pos = 0

        MARKER_LENGTH = len(MARKER)

        while 1:
            markerPos = txt.find(MARKER, pos)
            if markerPos < 0:
                break
            nextchar = txt[markerPos + MARKER_LENGTH]

            if nextchar == "{":
                chunks.append((0, txt[pos:markerPos]))
                pos = markerPos + MARKER_LENGTH + 1
                level = 1
                while level:
                    match, pos = matchTokenOrfail(txt, pos)
                    tstart, tend = match.regs[3]
                    token = txt[tstart:tend]

                    if token == "{":
                        level = level+1
                    elif token == "}":
                        level = level-1
                chunks.append((1, txt[markerPos + MARKER_LENGTH + 1 : pos-1]))

            elif nextchar in namechars:
                chunks.append((0, txt[pos:markerPos]))
                match, pos = matchTokenOrfail(txt, markerPos + MARKER_LENGTH)

                while pos < len(txt):
                    if txt[pos] == "." and \
                        pos+1 < len(txt) and txt[pos+1] in namechars:

                        match, pos = matchTokenOrfail(txt, pos+1)
                    elif txt[pos] in "([":
                        pos, level = pos+1, 1
                        while level:
                            match, pos = matchTokenOrfail(txt, pos)
                            tstart, tend = match.regs[3]
                            token = txt[tstart:tend]
                            if token[0] in "([":
                                level = level+1
                            elif token[0] in ")]":
                                level = level-1
                    else:
                        break
                chunks.append((1, txt[markerPos + MARKER_LENGTH:pos]))

            else:
                raise SyntaxError(txt[pos:markerPos+MARKER_LENGTH], pos)
                ## @@ we shouldn't have gotten here

        if pos < len(txt):
            chunks.append((0, txt[pos:]))

        return chunks

    def wrapExpressionsInStr(self, txt, marker, before, after):
        
        """Wrap all marked expressions in a string with the strings 'before' and
        'after'."""
        
        result = []
        resAppend = result.append
        for live, chunk in self.splitExprFromTxt(txt, marker):
            if live:
                resAppend( before + chunk + after )
            else:
                resAppend(chunk)

        return ''.join(result)


    ## placeholder-specific parsing methods ##

    def markPlaceholders(self, txt):
        """Swap the $'s for a marker that can be parsed as valid python code.
        Default is 'placeholder.'

        Also mark whether the placeholder is to be statically cached or
        timed-refresh cached"""
        REs = self._placeholderREs
        
        txt = REs['startToken'].sub(
            self.setting('placeholderMarker'), txt)
        txt = REs['cachedTags'].sub('CACHED.', txt)
        def refreshSubber(match):
            return 'REFRESH_' + match.group(1).replace('.','_') + '.'
        txt = REs['refreshTag'].sub(refreshSubber, txt)
        return txt

    def unmarkPlaceholders(self, txt):
        MARKER = self.setting('placeholderMarker')
        token = self.setting('placeholderStartToken')
        txt = re.sub(MARKER + 'CACHED\.' , token + '*', txt)
        def refreshSubber(match, token=token):
            return token + '*' + match.group(1).replace('_','.') + '*'
        txt = re.sub(MARKER + r'REFRESH_(.*)\.', refreshSubber, txt)
        txt = re.sub(MARKER, token, txt)
        return txt
        
    def translateRawPlaceholderString(self, txt, autoCall=True):
        """Translate raw $placeholders in a string directly into valid Python code.

        This method is used for handling $placeholders in #directives
        """
        return self.translatePlaceholderString(self.markPlaceholders(txt),
                                               autoCall=autoCall)


    def translatePlaceholderString(self, txt, autoCall=True):
        """Translate a marked placeholder string into valid Python code."""

        searchList = self.searchList()
        
        def translateName(name, self=self,
                          autoCall=autoCall,
                          firstSpecialCharRE=re.compile(r'\(|\['),
                          ):
            
            ## get rid of the 'cache-type' tokens
            # - these are handled by the tag-processor instead
            nameChunks = name.split('.')
            if nameChunks[0] == 'CACHED':
                    del nameChunks[0]
            if nameChunks[0].startswith('REFRESH'):
                del nameChunks[0]
            name = '.'.join(nameChunks)

            ## split the name into a part that NameMapper can handle and the rest
            firstSpecialChar = firstSpecialCharRE.search(name)
            if firstSpecialChar:         # NameMapper can't handle [] or ()
                firstSpecialChar = firstSpecialChar.start()
                nameMapperPartOfName, remainderOfName = \
                                      name[0:firstSpecialChar], name[firstSpecialChar:]
                remainderOfName = remainderOfName
                nameChunks = nameMapperPartOfName.split('.')
            else:
                nameMapperPartOfName = name
                remainderOfName = ''

            ## only do autocalling on names that have no () in them
            # @@TR: finish this off so that it works with the type of calls Chuck uses
            if autoCall and name.find('(') == -1 \
               and self.setting('useAutocalling'):
                safeToAutoCall = True
            else:
                safeToAutoCall = False
            
            ## deal with local vars from #set and #for directives
            if nameMapperPartOfName in self._localVarsList:
                return nameMapperPartOfName + remainderOfName
            elif nameChunks[0] in self._localVarsList:
                translatedName = 'valueForName(' + nameChunks[0] + ',"""' + \
                           '.'.join(nameChunks[1:]) + '""", ' + \
                           str(safeToAutoCall) + ')' + remainderOfName
                return translatedName

            ## Translate the NameMapper part of the Name
            translatedName = 'valueFromSearchList(searchList, "' + \
                           nameMapperPartOfName + '", ' + \
                           str(safeToAutoCall) + ')' + remainderOfName
            return translatedName

        ##########################
        resultList = []
        for live, chunk in self.splitExprFromTxt(txt, self.setting('placeholderMarker')):
            if live:
                if self._placeholderREs['nameMapperChunk'].search(chunk):
                    chunk = self.translatePlaceholderString(chunk)
                resultList.append( translateName(chunk) ) # using the function from above
            else:
                resultList.append(chunk)

        return ''.join(resultList)
    

    def escapePlaceholders(self, theString):
        """Escape any escaped placeholders in the string."""

        token = self.setting('placeholderStartToken')
        return theString.replace(token, '\\' + token)

    def unescapePlaceholders(self, theString):
        """Unescape any escaped placeholders in the string.
        
        This method is called by the Template._codeGenerator() in stage 1, which
        is why the first arg is 'templateObj.  self.escapePlaceholders() isn't
        called by Template._codeGenerator() so it doesn't take a templateObj arg."""
        
        token = self.setting('placeholderStartToken')
        return theString.replace('\\' + token, token)

    def evalPlaceholderString(self, txt, globalsDict={}, localsDict={'trans':None}):
        #the trans in the localsDict is there for the formatters
        """Return the value of a placeholderstring. This doesn't work with localVars."""
        
        localsDict.update({'theFormatters':self._theFormatters,
                           'searchList':self.searchList(),
                           'valueFromSearchList':valueFromSearchList,
                           'valueForName':valueForName,
                           'True':1,
                           'False':0})
        return eval(txt, globalsDict, localsDict)
    
    def execPlaceholderString(self, code, globalsDict={}, localsDict={'trans':None}):
        """Exec a placeholderString and return a tuple of the globalsDict, and
        the localsDict. This doesn't work with localVars."""
        
        localsDict.update({'theFormatters':self._theFormatters,
                           'searchList':self.searchList(),
                           'valueFromSearchList':valueFromSearchList,
                           'valueForName':valueForName,
                           'True':1,
                           'False':0})
        exec code in globalsDict, localsDict
        return (globalsDict,localsDict)
    
