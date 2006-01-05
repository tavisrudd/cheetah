#!/usr/bin/env python
# $Id: Template.py,v 1.130 2006/01/05 06:46:42 tavis_rudd Exp $
"""Provides the core Template class for Cheetah
See the docstring in __init__.py and the User's Guide for more information

Meta-Data
================================================================================
Author: Tavis Rudd <tavis@damnsimple.com>
License: This software is released for unlimited distribution under the
         terms of the MIT license.  See the LICENSE file.
Version: $Revision: 1.130 $
Start Date: 2001/03/30
Last Revision Date: $Date: 2006/01/05 06:46:42 $
""" 
__author__ = "Tavis Rudd <tavis@damnsimple.com>"
__revision__ = "$Revision: 1.130 $"[11:-2]

import os                         # used to get environ vars, etc.
import os.path
import sys                        # used in the error handling code
import re                         # used to define the internal delims regex
import new                        # used to bind the compiled template code
from new import instancemethod
import types                      # used in the mergeNewTemplateData method
                                  # and in Template.__init__()
import string
try:
    from types import StringTypes
except ImportError:
    StringTypes = (types.StringType,types.UnicodeType)
from types import StringType, ClassType
import time                       # used in the cache refresh code
from time import time as currentTime # used in the cache refresh code
import os.path                    # used in Template.normalizePath()
from os.path import getmtime, exists
from random import randrange
from tempfile import gettempdir, mktemp
import imp
import traceback

import __builtin__ # sometimes used by dynamically compiled templates

# Base classes for Template
from Cheetah.SettingsManager import SettingsManager  
from Cheetah.Servlet import Servlet                 
from Cheetah.Utils.WebInputMixin import WebInputMixin
# More intra-package imports ...
from Cheetah.Compiler import Compiler
from Cheetah import ErrorCatchers              # for placeholder tags
from Cheetah import Filters                          # the output filters
from Cheetah.DummyTransaction import DummyTransaction
from threading import Lock
from Cheetah.convertTmplPathToModuleName import convertTmplPathToModuleName
# this is used in the generated code:
from Cheetah.NameMapper import NotFound, valueFromSearchList, valueForName 
from Cheetah.NameMapper import valueFromFrameOrSearchList # this is used in the generated code
from Cheetah.Utils import VerifyType             # Used in Template.__init__
from Cheetah.Utils.Misc import checkKeywords     # Used in Template.__init__
from Cheetah.Utils.Indenter import Indenter      # Used in Template.__init__ and for
                                                 # placeholders
from Cheetah.CacheRegion import CacheRegion

# function name aliase in used dynamically loaded templates
VFSL = valueFromSearchList
VFFSL = valueFromFrameOrSearchList
VFN = valueForName

try:
    from ds.sys.Unspecified import Unspecified
except ImportError:
    class Unspecified:
        pass

class Error(Exception):  pass
class PreprocessError(Error): pass

_cheetahModuleNames = []
_uniqueModuleNameLock = Lock() # used to prevent collisions in sys.modules
def _genUniqueModuleName(baseModuleName):
    _uniqueModuleNameLock.acquire()
    if baseModuleName not in sys.modules and baseModuleName not in _cheetahModuleNames:
        finalName = baseModuleName
    else:
        finalName = ('cheetah_'+baseModuleName
                     +'_'
                     +''.join(map(lambda x: '%02d' % x, time.localtime(time.time())[:6]))
                     + str(randrange(10000, 99999)))

    _cheetahModuleNames.append(finalName) # prevent collisions
    _uniqueModuleNameLock.release()
    return finalName
    
class Template(SettingsManager, Servlet, WebInputMixin):    
    """The core template engine.  It serves as a base class for Template
    servlets and also knows how to compile a template."""


    _defaultMainMethodName = None
    _compilerSettings = None
    _compilerClass = Compiler

    def _getCompilerClass(klass, source=None, file=None):
        return klass._compilerClass
    _getCompilerClass = classmethod(_getCompilerClass)

    def _getCompilerSettings(klass, source=None, file=None):
        return klass._compilerSettings
    _getCompilerSettings = classmethod(_getCompilerSettings)



    _keepGeneratedPythonModulesForTracebacks = False
    _cacheDirForGeneratedPythonModules = None # change to a dirname
    _compileLock = Lock() # used to prevent race conditions while writing file
    
    def compile(klass, source=None, file=None,
                returnAClass=True,
                compilerSettings=None,
                compilerClass=None,
                moduleName=None,
                className=None,
                mainMethodName=None,
                
                moduleGlobals=None,
                # a dict of vars that will be added to the global namespace of
                # the module the generated code is executed in.

                keepRefToGeneratedModuleCode=False,
                preprocessors=None,
                ):
        """Compiles cheetah source code and returns a python class.  You then
        create template instances using that class.

        If you want to get the generated python source code instead, pass the
        argument returnAClass=False.
        """

        S = types.StringType
        U = types.UnicodeType
        D = types.DictType
        F = types.FileType
        N = types.NoneType
        try:
            VerifyType.VerifyType(source, 'source', [N,S,U], 'string or None')
            VerifyType.VerifyType(file, 'file', [N,S,U,F], 'string, file open for reading, or None')
            if compilerSettings:
                VerifyType.VerifyType(compilerSettings, 'compilerSettings', [D], 'dictionary')
        except TypeError, reason:
            # Re-raise the exception here so that the traceback will end in
            # this function rather than in some utility function.
            raise TypeError(reason)

        if preprocessors:
            if not source: # @@TR: this needs improving
                if isinstance(file, (str, unicode)): # it's a filename.
                    f = open(file) # Raises IOError.
                    source = f.read()
                    f.close()
                elif hasattr(file, 'read'):
                    source = file.read()  # Can't set filename or mtime--they're not accessible.
                file = None
            origSrc = source
            source = klass._preprocessSource(source, preprocessors)
            

        __orig_file__ = None
        if not moduleName:
            if file and type(file) in StringTypes:
                moduleName = convertTmplPathToModuleName(file)
                __orig_file__ = file
            else:
                moduleName = 'DynamicallyCompiledCheetahTemplate'

        if not compilerSettings:
            compilerSettings = klass._getCompilerSettings(source, file) or {}
        if not compilerClass:
            compilerClass = klass._getCompilerClass(source, file)
            
        className = className or moduleName
        mainMethodName = mainMethodName or klass._defaultMainMethodName
        
        compiler = compilerClass(source, file,
                                 moduleName=moduleName,
                                 mainClassName=className,
                                 mainMethodName=mainMethodName,
                                 settings=(compilerSettings or {}),                                 
                                 )
        compiler.compile()
        #encoding = compiler.getModuleEncoding()
        generatedModuleCode = compiler.getModuleCode()
        
        if returnAClass:
            uniqueModuleName = _genUniqueModuleName(moduleName)
            __file__ = uniqueModuleName+'.py' # relative file path with no dir part

            if klass._keepGeneratedPythonModulesForTracebacks:
                if not os.path.exists(klass._cacheDirForGeneratedPythonModules):
                    raise Exception('%s does not exist'%
                                    klass._cacheDirForGeneratedPythonModules)

                __file__ = os.path.join(klass._cacheDirForGeneratedPythonModules,
                                        __file__)
                klass._compileLock.acquire()
                try:
                    # @@TR: might want to assert that it doesn't already exist
                    try:
                        open(__file__, 'w').write(generatedModuleCode)
                        # @@TR: should probably restrict the perms, etc.
                    except OSError:
                        # @@ TR: should this optionally raise?
                        traceback.print_exc(file=sys.stderr)
                finally:
                    klass._compileLock.release()
            try:
                co = compile(generatedModuleCode, __file__, 'exec')
            except:
                print generatedModuleCode
                raise
            mod = new.module(uniqueModuleName)
            mod.__file__ = __file__
            if __orig_file__ and os.path.exists(__orig_file__):
                # this is used in the WebKit filemonitoring code
                mod.__orig_file__ = __orig_file__

            if moduleGlobals:
                for k, v in moduleGlobals.items():
                    setattr(mod, k, v)
            exec co in mod.__dict__

            sys.modules[uniqueModuleName] = mod
            templateClass = getattr(mod, className)
            if keepRefToGeneratedModuleCode:
                templateClass._generatedModuleCode = generatedModuleCode
            return templateClass
        else:
            return generatedModuleCode
    compile = classmethod(compile)

    def _preprocessSource(klass, source, preprocessors):
        """Iterates through the .compile() classmethod's preprocessors argument
        and pipes the source code through each each preprocessors.
        """
        if not isinstance(preprocessors, (list, tuple)):
            preprocessors = [preprocessors]
        for preprocessor in preprocessors:
            preprocessor = klass._normalizePreprocessor(preprocessor)
            source = preprocessor.preprocess(source)
        return source
    _preprocessSource = classmethod(_preprocessSource)

    def _normalizePreprocessor(klass, input):
        """Used to convert the items in the .compile() classmethod's
        preprocessors argument into real source preprocessors.  This permits the
        use of several shortcut forms for defining preprocessors.
        """
        if hasattr(input, 'preprocess'):
            return input
        elif callable(input):
            class Preprocessor:
                def preprocess(self, src):
                    return input(src)
            return Preprocessor()

        ##
        class Options(object): pass
        options = Options()
        options.searchList = []
        options.keepRefToGeneratedModuleCode = True
        
        def normalizeSearchList(searchList):
            if not isinstance(searchList, (list, tuple)):
                searchList = [searchList]
            return searchList            
        
        if isinstance(input, str):
            options.prefix = input            
        elif isinstance(input, (list, tuple)):
            prefix, searchList = input
            options.prefix = prefix
            options.searchList = normalizeSearchList(searchList)
        elif isinstance(input, dict):
            options.prefix = input.get('prefix')
            options.searchList = normalizeSearchList(
                input.get('searchList',
                          input.get('namespaces', [])))            
            for k, v in input.items():
                setattr(options, k, v)
        else: #it's an options object
            options = input

        if not hasattr(options, 'outputTransformer'):            
            options.outputTransformer = str

        if not hasattr(options, 'compiler'):
            def createPreprocessCompiler(prefix, compilerSettings=None):
                class PreprocessorCompiler(klass):
                    _compilerSettings = dict(
                        cheetahVarStartToken='$'+prefix,
                        directiveStartToken='#'+prefix,
                        commentStartToken='##'+prefix,
                        multiLineCommentStartToken='#*'+prefix,
                        )
                    if compilerSettings:
                        _compilerSettings.update(compilerSettings)
                return PreprocessorCompiler

            compilerSettings = getattr(options, 'compilerSettings', None)
            if not compilerSettings and not options.prefix:
                raise TypeError(
                    'Preprocessor requires either a "prefix" or a "compilerSettings" arg.'
                    ' Neither was provided.')
            options.compiler = createPreprocessCompiler(
                prefix=options.prefix,
                compilerSettings=compilerSettings,
                )

        class Preprocessor:
            def preprocess(self, source):
                moduleGlobals = getattr(options, 'moduleGlobals', None)
                templClass = options.compiler.compile(
                    source,
                    keepRefToGeneratedModuleCode=options.keepRefToGeneratedModuleCode,
                    moduleGlobals=moduleGlobals,
                    )
                instance = templClass(searchList=options.searchList)
                source = options.outputTransformer(instance)
                return source
        return Preprocessor()
    _normalizePreprocessor = classmethod(_normalizePreprocessor)        



    def assignRequiredMethodsToClass(klass, otherClass):
        for methodname in ('_initCheetahAttributes',
                           'searchList',
                           'errorCatcher',
                           'refreshCache',
                           'getVar',
                           'varExists',
                           'getFileContents',
                           'runAsMainProgram',
                           '_includeCheetahSource',
                           '_genTmpFilename',
                           '_importAsDummyModule',
                           ):
            if not hasattr(otherClass, methodname):
                method = getattr(Template, methodname)
                newMethod = instancemethod(method.im_func, None, otherClass)
                #print methodname, method
                setattr(otherClass, methodname, newMethod)

        if not hasattr(otherClass, '__str__') or otherClass.__str__ is object.__str__:
            mainMethName = getattr(otherClass,
                                   '_mainCheetahMethod_for_'+otherClass.__name__, None)
            if mainMethName:
                def __str__(self): return getattr(self, mainMethName)()
                __str__ = instancemethod(__str__, None, otherClass)
                setattr(otherClass, '__str__', __str__)            
            
    assignRequiredMethodsToClass = classmethod(assignRequiredMethodsToClass)


    ## end classmethods ##

    def __init__(self, source=None, searchList=Unspecified, file=None,
                 filter='EncodeUnicode', # which filter from Cheetah.Filters
                 filtersLib=Filters,
                 errorCatcher=None,
                 
                 compilerSettings=Unspecified, # control the behaviour of the compiler
                 _globalSetVars=Unspecified, # used internally for #include'd templates
                 _preBuiltSearchList=Unspecified # used internally for #include'd templates
                 ):
        
        """Reads in the template definition, sets up the namespace searchList,
        processes settings, then compiles.

        Compiler configuration settings should be passed in as a dictionary via
        the 'compilerSettings' keyword.

        This method can also be called without arguments in cases where it is
        called as a baseclass from a pre-compiled Template servlet."""
        
        ##################################################           
        ## Verify argument keywords and types

        S = types.StringType
        U = types.UnicodeType
        L = types.ListType
        T = types.TupleType
        D = types.DictType
        F = types.FileType
        C = types.ClassType
        M = types.ModuleType
        N = types.NoneType
        vt = VerifyType.VerifyType
        vtc = VerifyType.VerifyTypeClass
        try:
            vt(source, 'source', [N,S,U], 'string or None')
            if searchList is not Unspecified:
                vt(searchList, 'searchList', [L,T], 'list or tuple')
            vt(file, 'file', [N,S,U,F], 'string, file open for reading, or None')
            vtc(filter, 'filter', [S,C], 'string or class', 
                Filters.Filter,
                '(if class, must be subclass of Cheetah.Filters.Filter)')
            vt(filtersLib, 'filtersLib', [S,M], 'string or module',
                '(if module, must contain subclasses of Cheetah.Filters.Filter)')
            vtc(errorCatcher, 'errorCatcher', [N,S,C], 'string, class or None',
               ErrorCatchers.ErrorCatcher,
               '(if class, must be subclass of Cheetah.ErrorCatchers.ErrorCatcher)')
            if compilerSettings is not Unspecified:
                vt(compilerSettings, 'compilerSettings', [D], 'dictionary')
        except TypeError, reason:
            # Re-raise the exception here so that the traceback will end in
            # this function rather than in some utility function.
            raise TypeError(reason)
        
        if source is not None and file is not None:
            raise TypeError("you must supply either a source string or the" + 
                            " 'file' keyword argument, but not both")
                    
        ##################################################           
        ## Do superclass initialization.

        SettingsManager.__init__(self)
        Servlet.__init__(self)

        ##################################################           
        ## Setup instance state attributes used during the life of template
        ## post-compile

        self._initCheetahAttributes(
            searchList=searchList, filter=filter, filtersLib=filtersLib,
            errorCatcher=errorCatcher,
            _globalSetVars=_globalSetVars,
            _preBuiltSearchList=_preBuiltSearchList)
        
        ##################################################
        ## Now, compile if we're meant to
        if source is not None or file is not None:
            if compilerSettings is not Unspecified:
                self._compilerSettings = compilerSettings
            else:
                self._compilerSettings = self._getCompilerSettings(source, file) or {}

            self._generatedModuleCode = None
            self._generatedClassCode = None
            
            self._compile(source, file)

    def _initCheetahAttributes(self,
                               searchList=Unspecified,
                               filter='EncodeUnicode', # which filter from Cheetah.Filters
                               filtersLib=Filters,
                               errorCatcher=None,
                               _globalSetVars=Unspecified,
                               _preBuiltSearchList=Unspecified):

        self._CHEETAH_globalSetVars = {}
        if _globalSetVars is not Unspecified:
            # this is intended to be used internally by Nested Templates in #include's
            self._CHEETAH_globalSetVars = _globalSetVars
            
        if _preBuiltSearchList is not Unspecified:
            # happens with nested Template obj creation from #include's
            self._CHEETAH_searchList = list(_preBuiltSearchList)
            self._CHEETAH_searchList.append(self)
        else:
            # create our own searchList
            self._CHEETAH_searchList = [self._CHEETAH_globalSetVars]
            if searchList is not Unspecified:
                self._CHEETAH_searchList.extend(list(searchList))
            self._CHEETAH_searchList.append( self )

        self._CHEETAH_cacheRegions = {}
        self._CHEETAH_indenter = Indenter()
        self._CHEETAH_filtersLib = filtersLib
        self._CHEETAH_filters = {}
        if type(filter) in StringTypes:
            filterName = filter
            klass = getattr(self._CHEETAH_filtersLib, filterName)
        else:
            klass = filter
            filterName = klass.__name__            
        self._CHEETAH_currentFilter = self._CHEETAH_filters[filterName] = klass(self).filter
        self._CHEETAH_initialFilter = self._CHEETAH_currentFilter
        self._CHEETAH_errorCatchers = {}
        if errorCatcher:
            if type(errorCatcher) in StringTypes:
                errorCatcherClass = getattr(ErrorCatchers, errorCatcher)
            elif type(errorCatcher) == ClassType:
                errorCatcherClass = errorCatcher

            self._CHEETAH_errorCatcher = self._CHEETAH_errorCatchers[errorCatcher.__class__.__name__] = \
                                 errorCatcherClass(self)
        else:
            self._CHEETAH_errorCatcher = None
        self._CHEETAH_initErrorCatcher = self._CHEETAH_errorCatcher        

        if not hasattr(self, 'transaction'):
            self.transaction = None
        self._CHEETAH_instanceInitialized = True
            
    def _compile(self, source=None, file=None, moduleName=None, mainMethodName=None):
        
        """Compile the template. This method is automatically called by __init__
        when __init__ is fed a file or source string.

        USERS SHOULD *NEVER* CALL THIS METHOD THEMSELVES.
        """       
       
        if file and type(file) in StringTypes and not moduleName and \
           re.match(r'[a-zA-Z_][a-zA-Z_0-9]*$', file):
            moduleName = os.path.splitext(os.path.split(file)[1])[0]
        elif not moduleName:
            moduleName='GenTemplate'

        self._fileMtime = None
        self._fileDirName = None
        self._fileBaseName = None
        if file and type(file) in StringTypes:
            file = self.serverSidePath(file)
            self._fileMtime = os.path.getmtime(file)
            self._fileDirName, self._fileBaseName = os.path.split(file)
        self._filePath = file

        mainMethodName = mainMethodName or self._defaultMainMethodName
            
        compilerClass = self._getCompilerClass(source, file)        
        compilerSettings = self._compilerSettings or {}
        compiler = compilerClass(source, file,
                                 moduleName=moduleName,
                                 mainMethodName=mainMethodName,
                                 templateObj=self,
                                 settings=compilerSettings,
                                 )
        compiler.compile()
        encoding = compiler.getModuleEncoding()
        self._generatedModuleCode = compiler.getModuleCode()
        self._generatedClassCode = str(compiler._finishedClassIndex[moduleName])

        compiler._templateObj = None
        compiler.__dict__ = {}
        del compiler

    def generatedModuleCode(self):
        """Return the module code the compiler generated, or None if no
        compilation took place."""
        
        return self._generatedModuleCode
    
    def generatedClassCode(self):        
        """Return the class code the compiler generated, or None if no
        compilation took place."""

        return self._generatedClassCode
    
    def searchList(self):
        """Return a reference to the searchlist"""
        return self._CHEETAH_searchList

    def errorCatcher(self):
        """Return a reference to the current errorCatcher"""
        return self._CHEETAH_errorCatcher

    def refreshCache(self, cacheRegionKey=None, cacheKey=None):        
        """Refresh a cache item."""
        
        if not cacheRegionKey:
            # clear all template's cache regions
            self._CHEETAH_cacheRegions.clear()
        else:
            region = self._CHEETAH_cacheRegions.get(cacheRegionKey, CacheRegion())
            if not cacheKey:
                # clear the desired region and all its cache
                region.clear()
            else:
                # clear one specific cache of a specific region
                cache = region.getCache(cacheKey)
                if cache:
                    cache.clear()

    def shutdown(self):
        """Break reference cycles before discarding a servlet."""
        try:
            Servlet.shutdown(self)
        except:
            pass
        self._CHEETAH_searchList = None
        self.__dict__ = {}
            
    ## utility functions ##   

    def getVar(self, varName, default=Unspecified, autoCall=True):        
        """Get a variable from the searchList.  If the variable can't be found
        in the searchList, it returns the default value if one was given, or
        raises NameMapper.NotFound."""
        
        try:
            return VFSL(self.searchList(), varName.replace('$',''), autoCall)
        except NotFound:
            if default is not Unspecified:
                return default
            else:
                raise
    
    def varExists(self, varName, autoCall=True):
        """Test if a variable name exists in the searchList."""
        try:
            VFSL(self.searchList(), varName.replace('$',''), autoCall)
            return True
        except NotFound:
            return False


    hasVar = varExists
    

    def getFileContents(self, path):
        """A hook for getting the contents of a file.  The default
        implementation just uses the Python open() function to load local files.
        This method could be reimplemented to allow reading of remote files via
        various protocols, as PHP allows with its 'URL fopen wrapper'"""
        
        fp = open(path,'r')
        output = fp.read()
        fp.close()
        return output

    
    def runAsMainProgram(self):        
        """Allows enable the Template to function as a standalone command-line
        program for static page generation.

        Type 'python yourtemplate.py --help to see what it's capabable of.
        """

        from TemplateCmdLineIface import CmdLineIface
        CmdLineIface(templateObj=self).run()
        

    ##################################################
    ## internal methods -- not to be called by end-users
    ## @@TR 2005-01-01:  note that I plan to get rid of all of this in a future
    ## release     
    
    
    def _bindCompiledMethod(self, methodCompiler):        
        """Called by the Compiler class, to add new methods at runtime as the
        compilation process proceeds."""
        
        genCode = str(methodCompiler).strip() + '\n'
        methodName  = methodCompiler.methodName()
        try:
            exec genCode                    # in this namespace!!
        except:
            err = sys.stderr
            print >> err, 'Cheetah was trying to execute the ' + \
                  'following code but Python found a syntax error in it:'
            print >> err
            print >> err,  genCode
            raise
            

        genMeth = self._bindFunctionAsMethod(locals()[methodName])

        setattr(self,methodName, genMeth)
        if methodName == 'respond':
            self.__str__ = genMeth
            self.__repr__ = genMeth

          
    def _bindFunctionAsMethod(self, function):
        """Used to dynamically bind a plain function as a method of the
        Template instance."""
        return new.instancemethod(function, self, self.__class__)


    def _includeCheetahSource(self, srcArg, trans=None, includeFrom='file', raw=False):        
        """This is the method that #include directives translate into."""

        if not hasattr(self, '_CHEETAH_cheetahIncludes'):
            self._CHEETAH_cheetahIncludes = {}

        _includeID = srcArg
            
        if not self._CHEETAH_cheetahIncludes.has_key(_includeID):
            if includeFrom == 'file':
                path = self.serverSidePath(srcArg)
                if not raw:
                    nestedTemplate = Template(source=None,
                                              file=path,
                                              _preBuiltSearchList=self.searchList(),
                                              _globalSetVars = self._CHEETAH_globalSetVars,
                                              )
                    if not hasattr(nestedTemplate, 'respond'):
                        nestedTemplate.compileTemplate()
                    self._CHEETAH_cheetahIncludes[_includeID] = nestedTemplate
                else:
                    self._CHEETAH_cheetahIncludes[_includeID] = self.getFileContents(path)
            else:                       # from == 'str'
                if not raw:
                    nestedTemplate = Template(
                        source=srcArg,
                        _preBuiltSearchList=self.searchList(),
                        _globalSetVars = self._CHEETAH_globalSetVars,
                        )
                    if not hasattr(nestedTemplate, 'respond'):
                        nestedTemplate.compileTemplate()
                    self._CHEETAH_cheetahIncludes[_includeID] = nestedTemplate
                else:
                    self._CHEETAH_cheetahIncludes[_includeID] = srcArg
        ##

        if not raw:
            self._CHEETAH_cheetahIncludes[_includeID].respond(trans)
        else:
            trans.response().write(self._CHEETAH_cheetahIncludes[_includeID])


    def _genTmpFilename(self):        
        """Generate a temporary file name.  This is used internally by the
        Compiler to do correct importing from Cheetah templates when the
        template is compiled via the Template class' interface rather than via
        'cheetah compile'."""
       
        return (
            ''.join(map(lambda x: '%02d' % x, time.localtime(time.time())[:6])) + 
            str(randrange(10000, 99999)) +
            '.py')

    def _importAsDummyModule(self, contents):
        """Used by the Compiler to do correct importing from Cheetah templates
        when the template is compiled via the Template class' interface rather
        than via 'cheetah compile'.
        """
        mod = self._getDummyModuleForDynamicCompileHack()
        co = compile(contents+'\n', mod.__file__, 'exec')
        exec co in mod.__dict__
        return mod

    def _getDummyModuleForDynamicCompileHack(self):
        if not hasattr(self, '_dummyModule'):
            tmpFilename = self._genTmpFilename()
            name = tmpFilename.replace('.py','')            
            self._dummyModule = new.module(name)
            self._dummyModule.__file__ = tmpFilename
        return self._dummyModule

T = Template   # Short and sweet for debugging at the >>> prompt.

# vim: shiftwidth=4 tabstop=4 expandtab
