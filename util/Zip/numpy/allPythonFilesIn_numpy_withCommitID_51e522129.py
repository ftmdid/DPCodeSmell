from Numeric import *
from fastumath import *

import os

def remove_ignored_patterns(files,pattern):
    from fnmatch import fnmatch
    good_files = []
    for file in files:
        if not fnmatch(file,pattern):
            good_files.append(file)
    return good_files        
    
def remove_ignored_files(original,ignored_files,cur_dir):
    """ This is actually expanded to do pattern matching.
    
    """
    if not ignored_files: ignored_files = []
    ignored_modules = map(lambda x: x+'.py',ignored_files)
    ignored_packages = ignored_files[:]
    # always ignore setup.py and __init__.py files
    ignored_files = ['setup.py','setup_*.py','__init__.py']
    ignored_files += ignored_modules + ignored_packages
    ignored_files = map(lambda x,cur_dir=cur_dir: os.path.join(cur_dir,x),
                        ignored_files)
    #print 'ignored:', ignored_files    
    #good_files = filter(lambda x,ignored = ignored_files: x not in ignored,
    #                    original)
    good_files = original
    for pattern in ignored_files:
        good_files = remove_ignored_patterns(good_files,pattern)
        
    return good_files
                            
def harvest_modules(package,ignore=None):
    """* Retreive a list of all modules that live within a package.

         Only retreive files that are immediate children of the
         package -- do not recurse through child packages or
         directories.  The returned list contains actual modules, not
         just their names.
    *"""
    import os,sys

    d,f = os.path.split(package.__file__)

    # go through the directory and import every py file there.
    import glob
    common_dir = os.path.join(d,'*.py')
    py_files = glob.glob(common_dir)
    #py_files.remove(os.path.join(d,'__init__.py'))
    #py_files.remove(os.path.join(d,'setup.py'))
        
    py_files = remove_ignored_files(py_files,ignore,d)
    #print 'py_files:', py_files
    try:
        prefix = package.__name__
    except:
        prefix = ''
                
    all_modules = []
    for file in py_files:
        d,f = os.path.split(file)
        base,ext =  os.path.splitext(f)        
        mod = prefix + '.' + base
        #print 'module: import ' + mod
        try:
            exec ('import ' + mod)
            all_modules.append(eval(mod))
        except:
            print 'FAILURE to import ' + mod
            output_exception()                
        
    return all_modules

def harvest_packages(package,ignore = None):
    """ Retreive a list of all sub-packages that live within a package.

         Only retreive packages that are immediate children of this
         package -- do not recurse through child packages or
         directories.  The returned list contains actual package objects, not
         just their names.
    """
    import os,sys
    join = os.path.join

    d,f = os.path.split(package.__file__)

    common_dir = os.path.abspath(d)
    all_files = os.listdir(d)
    
    all_files = remove_ignored_files(all_files,ignore,'')
    #print 'all_files:', all_files
    try:
        prefix = package.__name__
    except:
        prefix = ''
    all_packages = []
    for directory in all_files:        
        path = join(common_dir,directory)
        if os.path.isdir(path) and \
           os.path.exists(join(path,'__init__.py')):
            sub_package = prefix + '.' + directory
            #print 'sub-package import ' + sub_package
            try:
                exec ('import ' + sub_package)
                all_packages.append(eval(sub_package))
            except:
                print 'FAILURE to import ' + sub_package
                output_exception() 
    return all_packages

def harvest_modules_and_packages(package,ignore=None):
    """ Retreive list of all packages and modules that live within a package.

         See harvest_packages() and harvest_modules()
    """
    all = harvest_modules(package,ignore) + harvest_packages(package,ignore)
    return all

def harvest_test_suites(package,ignore = None):
    import unittest
    suites=[]
    test_modules = harvest_modules_and_packages(package,ignore)
    #for i in test_modules:
    #    print i.__name__
    for module in test_modules:
        if hasattr(module,'test_suite'):
            try:
                suite = module.test_suite()
                if suite:
                    suites.append(suite)    
                else:
                    msg = "    !! FAILURE without error - shouldn't happen" + \
                          module.__name__                
                    print msg
            except:
                print '   !! FAILURE building test for ', module.__name__                
                print '   ',
                output_exception()            
        else:
            print 'No test suite found for ', module.__name__
    total_suite = unittest.TestSuite(suites)
    return total_suite

def module_test(mod_name,mod_file):
    """*

    *"""
    import os,sys,string
    #print 'testing', mod_name
    d,f = os.path.split(mod_file)

    # add the tests directory to the python path
    test_dir = os.path.join(d,'tests')
    sys.path.append(test_dir)

    # call the "test_xxx.test()" function for the appropriate
    # module.

    # This should deal with package naming issues correctly
    short_mod_name = string.split(mod_name,'.')[-1]
    test_module = 'test_' + short_mod_name
    test_string = 'import %s;reload(%s);%s.test()' % \
                  ((test_module,)*3)

    # This would be better cause it forces a reload of the orginal
    # module.  It doesn't behave with packages however.
    #test_string = 'reload(%s);import %s;reload(%s);%s.test()' % \
    #              ((mod_name,) + (test_module,)*3)
    exec(test_string)

    # remove test directory from python path.
    sys.path = sys.path[:-1]

def module_test_suite(mod_name,mod_file):
    #try:
        import os,sys,string
        print ' creating test suite for:', mod_name
        d,f = os.path.split(mod_file)

        # add the tests directory to the python path
        test_dir = os.path.join(d,'tests')
        sys.path.append(test_dir)

        # call the "test_xxx.test()" function for the appropriate
        # module.

        # This should deal with package naming issues correctly
        short_mod_name = string.split(mod_name,'.')[-1]
        test_module = 'test_' + short_mod_name
        test_string = 'import %s;reload(%s);suite = %s.test_suite()' % ((test_module,)*3)
        #print test_string
        exec(test_string)

        # remove test directory from python path.
        sys.path = sys.path[:-1]
        return suite
    #except:
    #    print '    !! FAILURE loading test suite from', test_module, ':'
    #    print '   ',
    #    output_exception()            


# Utility function to facilitate testing.

def assert_equal(actual,desired,err_msg='',verbose=1):
    """ Raise an assertion if two items are not
        equal.  I think this should be part of unittest.py
    """
    msg = '\nItems are not equal:\n' + err_msg
    try:
        if ( verbose and len(str(desired)) < 100 and len(str(actual)) ):
            msg =  msg \
                 + 'DESIRED: ' + str(desired) \
                 + '\nACTUAL: ' + str(actual)
    except:
        msg =  msg \
             + 'DESIRED: ' + str(desired) \
             + '\nACTUAL: ' + str(actual)
    assert desired == actual, msg

def assert_almost_equal(actual,desired,decimal=7,err_msg='',verbose=1):
    """ Raise an assertion if two items are not
        equal.  I think this should be part of unittest.py
    """
    msg = '\nItems are not equal:\n' + err_msg
    try:
        if ( verbose and len(str(desired)) < 100 and len(str(actual)) ):
            msg =  msg \
                 + 'DESIRED: ' + str(desired) \
                 + '\nACTUAL: ' + str(actual)
    except:
        msg =  msg \
             + 'DESIRED: ' + str(desired) \
             + '\nACTUAL: ' + str(actual)
    assert round(abs(desired - actual),decimal) == 0, msg


def assert_array_equal(x,y):
    try:
        assert(alltrue(equal(shape(x),shape(y))))
        reduced = equal(x,y)
        assert(alltrue(ravel(reduced)))
    except ValueError:
        print shape(x),shape(y)
        raise ValueError, 'arrays are not equal'

def assert_array_almost_equal(x,y,decimal=6):
    try:
        assert(alltrue(equal(shape(x),shape(y))))
        reduced = equal(around(abs(x-y),decimal))
        assert(alltrue(ravel(reduced)))
    except ValueError:
        print shape(x),shape(y)
        print x, y
        raise ValueError, 'arrays are not almost equal'

import traceback,sys
def output_exception():
    try:
        type, value, tb = sys.exc_info()
        info = traceback.extract_tb(tb)
        #this is more verbose
        #traceback.print_exc()
        filename, lineno, function, text = info[-1] # last line only
        print "%s:%d: %s: %s (in %s)" %\
              (filename, lineno, type.__name__, str(value), function)
    finally:
        type = value = tb = None # clean up

#!/usr/bin/env python
import os
from distutils.core import setup
from scipy_distutils.misc_util import get_path 
   
def install_package():
    """ Install the scipy_test module.  The dance with the current directory 
        is done to fool distutils into thinking it is run from the 
        scipy_distutils directory even if it was invoked from another script
        located in a different location.
    """
    path = get_path(__name__)
    old_path = os.getcwd()
    os.chdir(path)
    try:
        setup (name = "scipy_test",
               version = "0.1",
               description = "Supports testing of SciPy and other heirarchical packages",
               author = "Eric Jones",
               licence = "BSD Style",
               url = 'http://www.scipy.org',
               py_modules = ['scipy_test']
               )
    finally:
        os.chdir(old_path)
    
if __name__ == '__main__':
    install_package()

#!/usr/bin/env python
from setup_scipy_test import install_package
    
if __name__ == '__main__':
    install_package()

import os,sys

def get_path(mod_name):
    """ This function makes sure installation is done from the
        correct directory no matter if it is installed from the
        command line or from another package.
        
    """
    if mod_name == '__main__':
        d = os.path.abspath('.')
    else:
        #import scipy_distutils.setup
        mod = __import__(mod_name)
        file = mod.__file__
        d,f = os.path.split(os.path.abspath(file))
    return d

def add_local_to_path(mod_name):
    local_path = get_path(mod_name)
    sys.path.insert(0,local_path)
    
def add_grandparent_to_path(mod_name):
    local_path = get_path(mod_name)
    gp_dir = os.path.split(local_path)[0]
    sys.path.insert(0,gp_dir)

def restore_path():
    del sys.path[0]

def append_package_dir_to_path(package_name):           
    """ Search for a directory with package_name and append it to PYTHONPATH
        
        The local directory is searched first and then the parent directory.
    """
    # first see if it is in the current path
    # then try parent.  If it isn't found, fail silently
    # and let the import error occur.
    
    # not an easy way to clean up after this...
    import os,sys
    if os.path.exists(package_name):
        sys.path.append(package_name)
    elif os.path.exists(os.path.join('..',package_name)):
        sys.path.append(os.path.join('..',package_name))

def get_package_config(package_name):
    """ grab the configuration info from the setup_xxx.py file
        in a package directory.  The package directory is searched
        from the current directory, so setting the path to the
        setup.py file directory of the file calling this is usually
        needed to get search the path correct.
    """
    append_package_dir_to_path(package_name)
    mod = __import__('setup_'+package_name)
    config = mod.configuration()
    return config

def package_config(primary,dependencies=[]):
    """ Create a configuration dictionary ready for setup.py from
        a list of primary and dependent package names.  Each
        package listed must have a directory with the same name
        in the current or parent working directory.  Further, it
        should have a setup_xxx.py module within that directory that
        has a configuration() file in it. 
    """
    config = []
    config.extend([get_package_config(x) for x in primary])
    config.extend([get_package_config(x) for x in dependencies])        
    config_dict = merge_config_dicts(config)
    return config_dict
        
list_keys = ['packages', 'ext_modules', 'data_files',
             'include_dirs', 'libraries', 'fortran_libraries',
                 'headers']
dict_keys = ['package_dir']             

def default_config_dict():
    d={}
    for key in list_keys: d[key] = []
    for key in dict_keys: d[key] = {}
    return d

def merge_config_dicts(config_list):
    result = default_config_dict()    
    for d in config_list:
        for key in list_keys:
            result[key].extend(d.get(key,[]))
        for key in dict_keys:
            result[key].update(d.get(key,{}))
    return result
"""scipy_distutils

   Modified version of distutils to handle fortran source code, f2py,
   and other issues in the scipy build process.
"""

# Need to do something here to get distutils subsumed...

from distutils.core import *
from distutils.core import setup as old_setup

from distutils.cmd import Command
from distutils.extension import Extension

# Our dist is different than the standard one.
from scipy_distutils.dist import Distribution

from scipy_distutils.command import build
from scipy_distutils.command import build_py
from scipy_distutils.command import build_ext
from scipy_distutils.command import build_clib
from scipy_distutils.command import build_flib
from scipy_distutils.command import sdist
from scipy_distutils.command import install_data
from scipy_distutils.command import install
from scipy_distutils.command import install_headers

def setup(**attr):
    distclass = Distribution
    cmdclass = {'build':            build.build,
                'build_flib':       build_flib.build_flib,
                'build_ext':        build_ext.build_ext,
                'build_py':         build_py.build_py,                
                'build_clib':       build_clib.build_clib,
                'sdist':            sdist.sdist,
                'install_data':     install_data.install_data,
                'install':          install.install,
                'install_headers':  install_headers.install_headers
                }
                      
    new_attr = attr.copy()
    if new_attr.has_key('cmdclass'):
        cmdclass.update(new_attr['cmdclass'])        
    new_attr['cmdclass'] = cmdclass
    
    if not new_attr.has_key('distclass'):
        new_attr['distclass'] = distclass    
    
    return old_setup(**new_attr)

"""
Support code for building Python extensions on Windows.

    # NT stuff
    # 1. Make sure libpython<version>.a exists for gcc.  If not, build it.
    # 2. Force windows to use gcc (we're struggling with MSVC and g77 support) 
    # 3. Force windows to use g77

"""

import os, sys
import distutils.ccompiler

# I'd really like to pull this out of scipy and make it part of distutils...
import scipy_distutils.command.build_flib as build_flib


if sys.platform == 'win32':
    # NT stuff
    # 1. Make sure libpython<version>.a exists for gcc.  If not, build it.
    # 2. Force windows to use gcc (we're struggling with MSVC and g77 support) 
    # 3. Force windows to use g77
    
    # 1.  Build libpython<version> from .lib and .dll if they don't exist.    
    def import_library_exists():
            """ on windows platforms, make sure a gcc import library exists
            """
            if sys.platform == 'win32':
                lib_name = "libpython%d%d.a" % tuple(sys.version_info[:2])
                full_path = os.path.join(sys.prefix,'libs',lib_name)
                #print full_path
                if not os.path.exists(full_path):
                    return 0
            return 1
        
    def build_import_library():
        """ Build the import libraries for Mingw32-gcc on Windows
        """
        # lib2def lives in compiler
        sys.path.append(os.path.join('.','compiler'))

        import lib2def
        #libfile, deffile = parse_cmd()
        #if deffile == None:
        #    deffile = sys.stdout
        #else:
        #    deffile = open(deffile, 'w')
        lib_name = "python%d%d.lib" % tuple(sys.version_info[:2])    
        lib_file = os.path.join(sys.prefix,'libs',lib_name)
        def_name = "python%d%d.def" % tuple(sys.version_info[:2])    
        def_file = os.path.join(sys.prefix,'libs',def_name)
        nm_cmd = '%s %s' % (lib2def.DEFAULT_NM, lib_file)
        nm_output = lib2def.getnm(nm_cmd)
        dlist, flist = lib2def.parse_nm(nm_output)
        lib2def.output_def(dlist, flist, lib2def.DEF_HEADER, open(def_file, 'w'))
        
        out_name = "libpython%d%d.a" % tuple(sys.version_info[:2])
        out_file = os.path.join(sys.prefix,'libs',out_name)
        dll_name = "python%d%d.dll" % tuple(sys.version_info[:2])
        args = (dll_name,def_file,out_file)
        cmd = 'dlltool --dllname %s --def %s --output-lib %s' % args
        print cmd
        success = not os.system(cmd)
        # for now, fail silently
        if not success:
            print "WARNING: failed to build import library for gcc. "\
                  "Linking will fail."
        #if not success:
        #    msg = "Couldn't find import library, and failed to build it."
        #    raise DistutilsPlatformError, msg
    
    def set_windows_compiler(compiler):
        distutils.ccompiler._default_compilers = (
        
            # Platform string mappings
        
            # on a cygwin built python we can use gcc like an ordinary UNIXish
            # compiler
            ('cygwin.*', 'unix'),
            
            # OS name mappings
            ('posix', 'unix'),
            ('nt', compiler),
            ('mac', 'mwerks'),
            
            )                
    def use_msvc():
        set_windows_compiler('msvc')
    
    def use_gcc(): 
        set_windows_compiler('mingw32')   
    
    def use_g77():
        build_flib.all_compilers = [build_flib.gnu_fortran_compiler]    
    
    # 2. force the use of gcc on windows platform
    use_gcc()
    # 3. force the use of g77 on windows platform
    use_g77()
    if not import_library_exists():
        build_import_library()

    

#!/usr/bin/env python
import os
from distutils.core import setup
from misc_util import get_path 
   
def install_package():
    """ Install the scipy_distutils.  The dance with the current directory is done
        to fool distutils into thinking it is run from the scipy_distutils directory
        even if it was invoked from another script located in a different location.
    """
    path = get_path(__name__)
    old_path = os.getcwd()
    os.chdir(path)
    try:
        setup (name = "scipy_distutils",
               version = "0.1",
               description = "Changes to distutils needed for SciPy -- mostly Fortran support",
               author = "Travis Oliphant, Eric Jones, and Pearu Peterson",
               licence = "BSD Style",
               url = 'http://www.scipy.org',
               packages = ['scipy_distutils','scipy_distutils.command'],
               package_dir = {'scipy_distutils':path}
               )
    finally:
        os.chdir(old_path)
    
if __name__ == '__main__':
    install_package()

from distutils.dist import *
from distutils.dist import Distribution as OldDistribution
from distutils.errors import DistutilsSetupError

from types import *

class Distribution (OldDistribution):
    def __init__ (self, attrs=None):
        self.fortran_libraries = None
        OldDistribution.__init__(self, attrs)
    
    def has_f_libraries(self):
        print 'has_f_libraries'
        return self.fortran_libraries and len(self.fortran_libraries) > 0

    def check_data_file_list(self):
        """Ensure that the list of data_files (presumably provided as a
           command option 'data_files') is valid, i.e. it is a list of
           2-tuples, where the tuples are (name, list_of_libraries).
           Raise DistutilsSetupError if the structure is invalid anywhere;
           just returns otherwise."""
        print 'check_data_file_list'
        if type(self.data_files) is not ListType:
            raise DistutilsSetupError, \
                  "'data_files' option must be a list of tuples"

        for lib in self.data_files:
            if type(lib) is not TupleType and len(lib) != 2:
                raise DistutilsSetupError, \
                      "each element of 'data_files' must a 2-tuple"

            if type(lib[0]) is not StringType:
                raise DistutilsSetupError, \
                      "first element of each tuple in 'data_files' " + \
                      "must be a string (the package with the data_file)"

            if type(lib[1]) is not ListType:
                raise DistutilsSetupError, \
                      "second element of each tuple in 'data_files' " + \
                      "must be a list of files."
        # for lib

    # check_data_file_list ()
   
    def get_data_files (self):
        print 'get_data_files'
        self.check_data_file_list()
        filenames = []
        
        # Gets data files specified
        for ext in self.data_files:
            filenames.extend(ext[1])

        return filenames

# Need to override the build command to include building of fortran libraries
# This class must be used as the entry for the build key in the cmdclass
#    dictionary which is given to the setup command.

from distutils.command.build import *
from distutils.command.build import build as old_build

class build(old_build):
    def has_f_libraries(self):
        return self.distribution.has_f_libraries()
    sub_commands = [('build_py',      old_build.has_pure_modules),
                    ('build_clib',    old_build.has_c_libraries),
                    ('build_flib',    has_f_libraries), # new feature
                    ('build_ext',     old_build.has_ext_modules),
                    ('build_scripts', old_build.has_scripts),
                   ]

""" Modified version of build_ext that handles fortran source files and f2py 

    The f2py_sources() method is pretty much a copy of the swig_sources()
    method in the standard build_ext class , but modified to use f2py.  It
    also.
    
    slightly_modified_standard_build_extension() is a verbatim copy of
    the standard build_extension() method with a single line changed so that
    preprocess_sources() is called instead of just swig_sources().  This new
    function is a nice place to stick any source code preprocessing functions
    needed.
    
    build_extension() handles building any needed static fortran libraries
    first and then calls our slightly_modified_..._extenstion() to do the
    rest of the processing in the (mostly) standard way.    
"""

import os, string
from types import *

from distutils.dep_util import newer_group, newer
from distutils.command.build_ext import *
from distutils.command.build_ext import build_ext as old_build_ext

class build_ext (old_build_ext):
    def run (self):
        if self.distribution.has_f_libraries():
            build_flib = self.get_finalized_command('build_flib')
            self.libraries.extend(build_flib.get_library_names() or [])
            self.library_dirs.extend(build_flib.get_library_dirs() or [])
            #self.library_dirs.extend(build_flib.get_library_dirs() or [])
            #runtime_dirs = build_flib.get_runtime_library_dirs()
            #self.runtime_library_dirs.extend(runtime_dirs or [])
            
            #?? what is this ??
            self.library_dirs.append(build_flib.build_flib)
            
        old_build_ext.run(self)

    def preprocess_sources(self,sources):
        sources = self.swig_sources(sources)        
        sources = self.f2py_sources(sources)
        return sources
        
    def build_extension(self, ext):
        # support for building static fortran libraries
        if self.distribution.has_f_libraries():
            build_flib = self.get_finalized_command('build_flib')
            moreargs = build_flib.fcompiler.get_extra_link_args()
            if moreargs != []:                
                if ext.extra_link_args is None:
                    ext.extra_link_args = moreargs
                else:
                    ext.extra_link_args += moreargs
            # be sure to include fortran runtime library directory names
            runtime_dirs = build_flib.get_runtime_library_dirs()
            ext.runtime_library_dirs.extend(runtime_dirs or [])
            linker_so = build_flib.fcompiler.get_linker_so()
            if linker_so is not None:
                self.compiler.linker_so = linker_so
        # end of fortran source support
        # f2py support handled slightly_modified..._extenstion.
        return self.slightly_modified_standard_build_extension(ext)
        
    def slightly_modified_standard_build_extension(self, ext):
        """
            This is pretty much a verbatim copy of the build_extension()
            function in distutils with a single change to make it possible
            to pre-process f2py as well as swig source files before 
            compilation.
        """
        sources = ext.sources
        if sources is None or type(sources) not in (ListType, TupleType):
            raise DistutilsSetupError, \
                  ("in 'ext_modules' option (extension '%s'), " +
                   "'sources' must be present and must be " +
                   "a list of source filenames") % ext.name
        sources = list(sources)

        fullname = self.get_ext_fullname(ext.name)
        if self.inplace:
            # ignore build-lib -- put the compiled extension into
            # the source tree along with pure Python modules

            modpath = string.split(fullname, '.')
            package = string.join(modpath[0:-1], '.')
            base = modpath[-1]

            build_py = self.get_finalized_command('build_py')
            package_dir = build_py.get_package_dir(package)
            ext_filename = os.path.join(package_dir,
                                        self.get_ext_filename(base))
        else:
            ext_filename = os.path.join(self.build_lib,
                                        self.get_ext_filename(fullname))

        if not (self.force or newer_group(sources, ext_filename, 'newer')):
            self.announce("skipping '%s' extension (up-to-date)" %
                          ext.name)
            return
        else:
            self.announce("building '%s' extension" % ext.name)

        # I copied this hole stinken function just to change from
        # self.swig_sources to self.preprocess_sources...
        sources = self.preprocess_sources(sources)

        # Next, compile the source code to object files.

        # XXX not honouring 'define_macros' or 'undef_macros' -- the
        # CCompiler API needs to change to accommodate this, and I
        # want to do one thing at a time!

        # Two possible sources for extra compiler arguments:
        #   - 'extra_compile_args' in Extension object
        #   - CFLAGS environment variable (not particularly
        #     elegant, but people seem to expect it and I
        #     guess it's useful)
        # The environment variable should take precedence, and
        # any sensible compiler will give precedence to later
        # command line args.  Hence we combine them in order:
        extra_args = ext.extra_compile_args or []

        macros = ext.define_macros[:]
        for undef in ext.undef_macros:
            macros.append((undef,))

        # XXX and if we support CFLAGS, why not CC (compiler
        # executable), CPPFLAGS (pre-processor options), and LDFLAGS
        # (linker options) too?
        # XXX should we use shlex to properly parse CFLAGS?

        if os.environ.has_key('CFLAGS'):
            extra_args.extend(string.split(os.environ['CFLAGS']))

        objects = self.compiler.compile(sources,
                                        output_dir=self.build_temp,
                                        macros=macros,
                                        include_dirs=ext.include_dirs,
                                        debug=self.debug,
                                        extra_postargs=extra_args)

        # Now link the object files together into a "shared object" --
        # of course, first we have to figure out all the other things
        # that go into the mix.
        if ext.extra_objects:
            objects.extend(ext.extra_objects)
        extra_args = ext.extra_link_args or []


        self.compiler.link_shared_object(
            objects, ext_filename, 
            libraries=self.get_libraries(ext),
            library_dirs=ext.library_dirs,
            runtime_library_dirs=ext.runtime_library_dirs,
            extra_postargs=extra_args,
            export_symbols=self.get_export_symbols(ext), 
            debug=self.debug,
            build_temp=self.build_temp)

    def f2py_sources (self, sources):

        """Walk the list of source files in 'sources', looking for f2py
        interface (.pyf) files.  Run f2py on all that are found, and
        return a modified 'sources' list with f2py source files replaced
        by the generated C (or C++) files.
        """

        import f2py2e

        new_sources = []
        f2py_sources = []
        f2py_targets = {}

        # XXX this drops generated C/C++ files into the source tree, which
        # is fine for developers who want to distribute the generated
        # source -- but there should be an option to put f2py output in
        # the temp dir.

        target_ext = 'module.c'

        for source in sources:
            (base, ext) = os.path.splitext(source)
            if ext == ".pyf":             # f2py interface file
                new_sources.append(base + target_ext)
                f2py_sources.append(source)
                f2py_targets[source] = new_sources[-1]
            else:
                new_sources.append(source)

        if not f2py_sources:
            return new_sources

        # a bit of a hack, but I think it'll work.  Just include one of
        # the fortranobject.c files that was copied into most 
        d,f = os.path.split(f2py_sources[0])
        new_sources.append(os.path.join(d,'fortranobject.c'))

        f2py_opts = ['--no-wrap-functions', '--no-latex-doc',
                     '--no-makefile','--no-setup']
        for source in f2py_sources:
            target = f2py_targets[source]
            if newer(source,target):
                self.announce("f2py-ing %s to %s" % (source, target))
                f2py2e.run_main(f2py_opts + [source])

        return new_sources
    # f2py_sources ()

    def get_source_files (self):
        self.check_extensions_list(self.extensions)
        filenames = []

        # Get sources and any include files in the same directory.
        for ext in self.extensions:
            filenames.extend(ext.sources)
            filenames.extend(get_headers(get_directories(ext.sources)))

        return filenames

"""
    I don't know much about this one, so I'm not going to mess with 
    it much. (eric)
"""
from distutils.command.install import *
from distutils.command.install_headers import install_headers as old_install_headers

class install_headers (old_install_headers):
    def run (self):
        headers = self.distribution.headers
        if not headers:
            return
        # hack to force headers into Numeric instead of SciPy
        import os
        d,f = os.path.split(self.install_dir)
        self.install_dir = os.path.join(d,'Numeric')        
        self.mkpath(self.install_dir)
        for header in headers:
            (out, _) = self.copy_file(header, self.install_dir)
            self.outfiles.append(out)    

from distutils.command.build_py import *
from distutils.command.build_py import build_py as old_build_py
from fnmatch import fnmatch

def is_setup_script(file):
    return (fnmatch(file,"setup.py") or fnmatch(file,"setup_*.py"))
    
class build_py(old_build_py):
    def find_package_modules (self, package, package_dir):
        # we filter all files that are setup.py or setup_xxx.py        
        self.check_package(package, package_dir)
        module_files = glob(os.path.join(package_dir, "*.py"))
        modules = []
        setup_script = os.path.abspath(self.distribution.script_name)

        for f in module_files:
            abs_f = os.path.abspath(f)
            if abs_f != setup_script and not is_setup_script(f):
                module = os.path.splitext(os.path.basename(f))[0]
                modules.append((package, module, f))
            else:
                self.debug_print("excluding %s" % setup_script)
        return modules


"""distutils.command

Package containing implementation of all the standard Distutils
commands."""

__revision__ = "$Id$"

distutils_all = [  'build_py',
                   'build_scripts',
                   'clean',
                   'install_lib',
                   'install_scripts',
                   'bdist',
                   'bdist_dumb',
                   'bdist_rpm',
                   'bdist_wininst',
                ]

__import__('distutils.command',globals(),locals(),distutils_all)

__all__ = ['build',
           'build_ext',
           'build_clib',
           'build_flib',
           'install',
           'install_data',
           'install_headers',
           'sdist',
          ] + distutils_all

from distutils.command.sdist import *
from distutils.command.sdist import sdist as old_sdist

class sdist(old_sdist):
    def add_defaults (self):
        old_sdist.add_defaults(self)
        if self.distribution.has_f_libraries():
            build_flib = self.get_finalized_command('build_flib')
            self.filelist.extend(build_flib.get_source_files())

        if self.distribution.has_data_files():
            self.filelist.extend(self.distribution.get_data_files())

    def make_release_tree (self, base_dir, files):
        """Create the directory tree that will become the source
        distribution archive.  All directories implied by the filenames in
        'files' are created under 'base_dir', and then we hard link or copy
        (if hard linking is unavailable) those files into place.
        Essentially, this duplicates the developer's source tree, but in a
        directory named after the distribution, containing only the files
        to be distributed.
        """
        # Create all the directories under 'base_dir' necessary to
        # put 'files' there; the 'mkpath()' is just so we don't die
        # if the manifest happens to be empty.
        dest_files = remove_common_base(files)
        self.mkpath(base_dir)
        dir_util.create_tree(base_dir, dest_files,
                             verbose=self.verbose, dry_run=self.dry_run)

        # And walk over the list of files, either making a hard link (if
        # os.link exists) to each one that doesn't already exist in its
        # corresponding location under 'base_dir', or copying each file
        # that's out-of-date in 'base_dir'.  (Usually, all files will be
        # out-of-date, because by default we blow away 'base_dir' when
        # we're done making the distribution archives.)
    
        if hasattr(os, 'link'):        # can make hard links on this system
            link = 'hard'
            msg = "making hard links in %s..." % base_dir
        else:                           # nope, have to copy
            link = None
            msg = "copying files to %s..." % base_dir

        if not files:
            self.warn("no files to distribute -- empty manifest?")
        else:
            self.announce(msg)
        
        dest_files = [os.path.join(base_dir,file) for file in dest_files]
        file_pairs = zip(files,dest_files)    
        for file,dest in file_pairs:
            if not os.path.isfile(file):
                self.warn("'%s' not a regular file -- skipping" % file)
            else:
                #ej: here is the only change -- made to handle
                # absolute paths to files as well as relative
                #par,file_name = os.path.split(file)
                #dest = os.path.join(base_dir, file_name)
                # end of changes
                
                # old code
                #dest = os.path.join(base_dir, file)
                #end old code
                self.copy_file(file, dest, link=link)

        self.distribution.metadata.write_pkg_info(base_dir)
        #raise ValueError
    # make_release_tree ()

def remove_common_base(files):
    """ Remove the greatest common base directory from all the
        absolute file paths in the list of files.  files in the
        list without a parent directory are not affected.
    """
    rel_files = filter(lambda x: not os.path.dirname(x),files)
    abs_files = filter(os.path.dirname,files)
    base = find_common_base(abs_files)
    # will leave files with local path unaffected
    # and maintains original file order
    results = [string.replace(file,base,'') for file in files]
    return results

def find_common_base(files):
    """ Find the "greatest common base directory" of a list of files
    """
    if not files:
        return files
    result = ''
    d,f = os.path.split(files[0])
    keep_looking = 1    
    while(keep_looking and d):
        keep_looking = 0
        for file in files:
            if string.find('start'+file,'start'+d) == -1:
                keep_looking = 1
                break
        if keep_looking:
            d,f = os.path.split(d)
        else:
            result = d
            
    if d: 
        d = os.path.join(d,'')
    return d        
"""distutils.command.build_clib

Implements the Distutils 'build_clib' command, to build a C/C++ library
that is included in the module distribution and needed by an extension
module."""

# created (an empty husk) 1999/12/18, Greg Ward
# fleshed out 2000/02/03-04

__revision__ = "$Id$"


# XXX this module has *lots* of code ripped-off quite transparently from
# build_ext.py -- not surprisingly really, as the work required to build
# a static library from a collection of C source files is not really all
# that different from what's required to build a shared object file from
# a collection of C source files.  Nevertheless, I haven't done the
# necessary refactoring to account for the overlap in code between the
# two modules, mainly because a number of subtle details changed in the
# cut 'n paste.  Sigh.

import os, string
from glob import glob
from types import *
from distutils.core import Command
from distutils.errors import *
from distutils.sysconfig import customize_compiler


def show_compilers ():
    from distutils.ccompiler import show_compilers
    show_compilers()

def get_headers(directory_list):
    # get *.h files from list of directories
    headers = []
    for dir in directory_list:
        head = glob(os.path.join(dir,"*.h"))
        headers.extend(head)

    return headers

def get_directories(list_of_sources):
    # get unique directories from list of sources.
    direcs = []
    for file in list_of_sources:
        dir = os.path.split(file)
        if dir[0] != '' and not dir[0] in direcs:
            direcs.append(dir[0])

    return direcs


class build_clib (Command):

    description = "build C/C++ libraries used by Python extensions"

    user_options = [
        ('build-clib', 'b',
         "directory to build C/C++ libraries to"),
        ('build-temp', 't',
         "directory to put temporary build by-products"),
        ('debug', 'g',
         "compile with debugging information"),
        ('force', 'f',
         "forcibly build everything (ignore file timestamps)"),
        ('compiler=', 'c',
         "specify the compiler type"),
        ]

    boolean_options = ['debug', 'force']

    help_options = [
        ('help-compiler', None,
         "list available compilers", show_compilers),
        ]

    def initialize_options (self):
        self.build_clib = None
        self.build_temp = None

        # List of libraries to build
        self.libraries = None

        # Compilation options for all libraries
        self.include_dirs = None
        self.define = None
        self.undef = None
        self.debug = None
        self.force = 0
        self.compiler = None

    # initialize_options()


    def finalize_options (self):

        # This might be confusing: both build-clib and build-temp default
        # to build-temp as defined by the "build" command.  This is because
        # I think that C libraries are really just temporary build
        # by-products, at least from the point of view of building Python
        # extensions -- but I want to keep my options open.
        self.set_undefined_options('build',
                                   ('build_temp', 'build_clib'),
                                   ('build_temp', 'build_temp'),
                                   ('compiler', 'compiler'),
                                   ('debug', 'debug'),
                                   ('force', 'force'))

        self.libraries = self.distribution.libraries
        if self.libraries:
            self.check_library_list(self.libraries)

        if self.include_dirs is None:
            self.include_dirs = self.distribution.include_dirs or []
        if type(self.include_dirs) is StringType:
            self.include_dirs = string.split(self.include_dirs,
                                             os.pathsep)

        # XXX same as for build_ext -- what about 'self.define' and
        # 'self.undef' ?

    # finalize_options()


    def run (self):

        if not self.libraries:
            return

        # Yech -- this is cut 'n pasted from build_ext.py!
        from distutils.ccompiler import new_compiler
        self.compiler = new_compiler(compiler=self.compiler,
                                     verbose=self.verbose,
                                     dry_run=self.dry_run,
                                     force=self.force)
        customize_compiler(self.compiler)

        if self.include_dirs is not None:
            self.compiler.set_include_dirs(self.include_dirs)
        if self.define is not None:
            # 'define' option is a list of (name,value) tuples
            for (name,value) in self.define:
                self.compiler.define_macro(name, value)
        if self.undef is not None:
            for macro in self.undef:
                self.compiler.undefine_macro(macro)

        self.build_libraries(self.libraries)

    # run()


    def check_library_list (self, libraries):
        """Ensure that the list of libraries (presumably provided as a
           command option 'libraries') is valid, i.e. it is a list of
           2-tuples, where the tuples are (library_name, build_info_dict).
           Raise DistutilsSetupError if the structure is invalid anywhere;
           just returns otherwise."""

        # Yechh, blecch, ackk: this is ripped straight out of build_ext.py,
        # with only names changed to protect the innocent!

        if type(libraries) is not ListType:
            raise DistutilsSetupError, \
                  "'libraries' option must be a list of tuples"

        for lib in libraries:
            if type(lib) is not TupleType and len(lib) != 2:
                raise DistutilsSetupError, \
                      "each element of 'libraries' must a 2-tuple"

            if type(lib[0]) is not StringType:
                raise DistutilsSetupError, \
                      "first element of each tuple in 'libraries' " + \
                      "must be a string (the library name)"
            if '/' in lib[0] or (os.sep != '/' and os.sep in lib[0]):
                raise DistutilsSetupError, \
                      ("bad library name '%s': " + 
                       "may not contain directory separators") % \
                      lib[0]

            if type(lib[1]) is not DictionaryType:
                raise DistutilsSetupError, \
                      "second element of each tuple in 'libraries' " + \
                      "must be a dictionary (build info)"
        # for lib

    # check_library_list ()


    def get_library_names (self):
        # Assume the library list is valid -- 'check_library_list()' is
        # called from 'finalize_options()', so it should be!

        if not self.libraries:
            return None

        lib_names = []
        for (lib_name, build_info) in self.libraries:
            lib_names.append(lib_name)
        return lib_names

    # get_library_names ()


    def get_source_files (self):
        self.check_library_list(self.libraries)
        filenames = []

        # Gets source files specified and any "*.h" header files in
        # those directories.        
        for ext in self.libraries:
            filenames.extend(ext[1]['sources'])
            filenames.extend(get_headers(get_directories(ext[1]['sources'])))

        return filenames

    def build_libraries (self, libraries):

        compiler = self.compiler

        for (lib_name, build_info) in libraries:
            sources = build_info.get('sources')
            if sources is None or type(sources) not in (ListType, TupleType):
                raise DistutilsSetupError, \
                      ("in 'libraries' option (library '%s'), " +
                       "'sources' must be present and must be " +
                       "a list of source filenames") % lib_name
            sources = list(sources)

            self.announce("building '%s' library" % lib_name)

            # First, compile the source code to object files in the library
            # directory.  (This should probably change to putting object
            # files in a temporary build directory.)
            macros = build_info.get('macros')
            include_dirs = build_info.get('include_dirs')
            objects = self.compiler.compile(sources,
                                            output_dir=self.build_temp,
                                            macros=macros,
                                            include_dirs=include_dirs,
                                            debug=self.debug)

            # Now "link" the object files together into a static library.
            # (On Unix at least, this isn't really linking -- it just
            # builds an archive.  Whatever.)
            self.compiler.create_static_lib(objects, lib_name,
                                            output_dir=self.build_clib,
                                            debug=self.debug)

        # for libraries

    # build_libraries ()

# class build_lib

from types import StringType
from distutils.command.install import *
from distutils.command.install import install as old_install
from distutils.util import convert_path
from distutils.file_util import write_file
from distutils.errors import DistutilsOptionError

#install support for Numeric.pth setup
class install(old_install):
    def finalize_options (self):
        old_install.finalize_options(self)
        self.install_lib = self.install_libbase
        
    def handle_extra_path (self):
        if self.extra_path is None:
            self.extra_path = self.distribution.extra_path

        if self.extra_path is not None:
            if type(self.extra_path) is StringType:
                self.extra_path = string.split(self.extra_path, ',')
            if len(self.extra_path) == 1:
                path_file = extra_dirs = self.extra_path[0]
            elif len(self.extra_path) == 2:
                (path_file, extra_dirs) = self.extra_path
            else:
                raise DistutilsOptionError, \
                      "'extra_path' option must be a list, tuple, or " + \
                      "comma-separated string with 1 or 2 elements"

            # convert to local form in case Unix notation used (as it
            # should be in setup scripts)
            extra_dirs = convert_path(extra_dirs)

        else:
            path_file = None
            extra_dirs = ''

        # XXX should we warn if path_file and not extra_dirs? (in which
        # case the path file would be harmless but pointless)
        self.path_file = path_file
        self.extra_dirs = ''
        self.pth_file = extra_dirs

    # handle_extra_path ()

    def create_path_file (self):
        filename = os.path.join(self.install_libbase,
                                self.path_file + ".pth")
        if self.install_path_file:
            self.execute(write_file,
                         (filename, [self.pth_file]),
                         "creating %s" % filename)
        else:
            self.warn("path file '%s' not created" % filename)
""" Implements the build_flib command which should go into Distutils
    at some point.
     
    Note:
    Right now, we're dynamically linking to the Fortran libraries on 
    some platforms (Sun for sure).  This is fine for local installations
    but a bad thing for redistribution because these libraries won't
    live on any machine that doesn't have a fortran compiler installed.
    It is pretty hard (impossible?) to get gcc to pass the right compiler
    flags on Sun to get the linker to use static libs for the fortran
    stuff.  Investigate further...

Bugs:
 ***  Options -e and -x have no effect when used with --help-compiler
       options. E.g. 
       ./setup.py build_flib --help-compiler -e g77-3.0
      finds g77-2.95.
      How to extract these options inside the show_compilers function?
 ***  Option --force has no effect when switching a compiler. One must
      manually remove .o files that were generated earlier by a
      different compiler.
 ***  compiler.is_available() method may not work correctly on nt
      because of lack of knowledge how to get exit status in
      run_command function. However, it may give reasonable results
      based on a version string.
 ***  Some vendors provide different compilers for F77 and F90
      compilations. Currently, checking the availability of these
      compilers is based on only checking the availability of the
      corresponding F77 compiler. If it exists, then F90 is assumed
      to exist also.

Open issues:
 ***  User-defined compiler flags. Do we need --fflags?

Fortran compilers (as to be used with --fcompiler= option):
      Absoft
      Sun
      SGI
      Gnu
      Intel
      Itanium
      NAG
      VAST
"""

import distutils
import distutils.dep_util, distutils.dir_util
import os,sys,string
import commands,re
from types import *
from distutils.command.build_clib import build_clib
from distutils.errors import *

if os.name == 'nt':
    def run_command(command):
        """ not sure how to get exit status on nt. """
        in_pipe,out_pipe = os.popen4(command)
        in_pipe.close()
        text = out_pipe.read()
        return 0, text
else:
    run_command = commands.getstatusoutput
    
def show_compilers():
    for compiler_class in all_compilers:
        compiler = compiler_class()
        if compiler.is_available():
            print compiler

class build_flib (build_clib):

    description = "build f77/f90 libraries used by Python extensions"

    user_options = [
        ('build-flib', 'b',
         "directory to build f77/f90 libraries to"),
        ('build-temp', 't',
         "directory to put temporary build by-products"),
        ('debug', 'g',
         "compile with debugging information"),
        ('force', 'f',
         "forcibly build everything (ignore file timestamps)"),
        ('fcompiler=', 'c',
         "specify the compiler type"),
        ('fcompiler-exec=', 'e',
         "specify the path to F77 compiler"),
        ('f90compiler-exec=', 'x',
         "specify the path to F90 compiler"),
        ]

    boolean_options = ['debug', 'force']

    help_options = [
        ('help-compiler', None,
         "list available compilers", show_compilers),
        ]

    def initialize_options (self):

        self.build_flib = None
        self.build_temp = None

        self.fortran_libraries = None
        self.define = None
        self.undef = None
        self.debug = None
        self.force = 0
        self.fcompiler = None
        self.fcompiler_exec = None
        self.f90compiler_exec = None

    # initialize_options()

    def finalize_options (self):
        self.set_undefined_options('build',
                                   ('build_temp', 'build_flib'),
                                   ('build_temp', 'build_temp'),
                                   ('debug', 'debug'),
                                   ('force', 'force'))
        fc = find_fortran_compiler(self.fcompiler,
                                   self.fcompiler_exec,
                                   self.f90compiler_exec)
        if not fc:
            raise DistutilsOptionError, 'Fortran compiler not available: %s'%(self.fcompiler)
        else:
            self.announce(' using %s Fortran compiler' % fc)
        self.fcompiler = fc
        self.fortran_libraries = self.distribution.fortran_libraries
        if self.fortran_libraries:
            self.check_library_list(self.fortran_libraries)

    # finalize_options()

    def run (self):
        if not self.fortran_libraries:
            return
        self.build_libraries(self.fortran_libraries)

    # run ()

    def get_library_names(self):
        if not self.fortran_libraries:
            return None

        lib_names = [] 

        for (lib_name, build_info) in self.fortran_libraries:
            lib_names.append(lib_name)

        if self.fcompiler is not None:
            lib_names.extend(self.fcompiler.get_libraries())
            
        return lib_names

    # get_library_names ()

    def get_library_dirs(self):
        if not self.fortran_libraries:
            return []#None

        lib_dirs = [] 

        if self.fcompiler is not None:
            lib_dirs.extend(self.fcompiler.get_library_dirs())
            
        return lib_dirs

    # get_library_dirs ()

    def get_runtime_library_dirs(self):
        if not self.fortran_libraries:
            return []#None

        lib_dirs = [] 

        if self.fcompiler is not None:
            lib_dirs.extend(self.fcompiler.get_runtime_library_dirs())
            
        return lib_dirs

    # get_library_dirs ()

    def get_source_files (self):
        self.check_library_list(self.fortran_libraries)
        filenames = []

        # Gets source files specified 
        for ext in self.fortran_libraries:
            filenames.extend(ext[1]['sources'])

        return filenames    
                
    def build_libraries (self, fortran_libraries):
        
        fcompiler = self.fcompiler
        
        for (lib_name, build_info) in fortran_libraries:
            sources = build_info.get('sources')
            if sources is None or type(sources) not in (ListType, TupleType):
                raise DistutilsSetupError, \
                      ("in 'fortran_libraries' option (library '%s'), " +
                       "'sources' must be present and must be " +
                       "a list of source filenames") % lib_name
            sources = list(sources)
            module_dirs = build_info.get('module_dirs')
            module_files = build_info.get('module_files')
            self.announce(" building '%s' library" % lib_name)
            
            if module_files:
                fcompiler.build_library(lib_name, module_files,
                                        temp_dir=self.build_temp)
                
            fcompiler.build_library(lib_name, sources,
                                    module_dirs, temp_dir=self.build_temp)

        # for loop

    # build_libraries ()


class fortran_compiler_base:

    vendor = None
    ver_match = None
    
    def __init__(self):
        # Default initialization. Constructors of derived classes MUST
        # call this functions.
        self.version = None
        
        self.f77_switches = ''
        self.f77_opt = ''
        self.f77_debug = ''
        
        self.f90_switches = ''
        self.f90_opt = ''
        self.f90_debug = ''
        
        self.libraries = []
        self.library_dirs = []

        if self.vendor is None:
            raise DistutilsInternalError,\
                  '%s must define vendor attribute'%(self.__class__)
        if self.ver_match is None:
            raise DistutilsInternalError,\
                  '%s must define ver_match attribute'%(self.__class__)

    def to_object(self,dirty_files,module_dirs=None, temp_dir=''):
        files = string.join(dirty_files)
        f90_files = get_f90_files(dirty_files)
        f77_files = get_f77_files(dirty_files)
        if f90_files != []:
            obj1 = self.f90_compile(f90_files,module_dirs,temp_dir = temp_dir)
        else:
            obj1 = []
        if f77_files != []:
            obj2 = self.f77_compile(f77_files, temp_dir = temp_dir)
        else:
            obj2 = []
        return obj1 + obj2

    def source_to_object_names(self,source_files, temp_dir=''):
        file_list = map(lambda x: os.path.basename(x),source_files)
        file_base_ext = map(lambda x: os.path.splitext(x),file_list)
        object_list = map(lambda x: x[0] +'.o',file_base_ext)
        object_files = map(lambda x,td=temp_dir: os.path.join(td,x),object_list)
        return object_files
        
    def source_and_object_pairs(self,source_files, temp_dir=''):
        object_files = self.source_to_object_names(source_files,temp_dir)
        file_pairs = zip(source_files,object_files)
        return file_pairs
 
    def f_compile(self,compiler,switches, source_files,
                  module_dirs=None, temp_dir=''):
        module_switch = self.build_module_switch(module_dirs)
        file_pairs = self.source_and_object_pairs(source_files,temp_dir)
        object_files = []
        for source,object in file_pairs:
            if distutils.dep_util.newer(source,object):
                cmd =  compiler + ' ' + switches + \
                       module_switch + ' -c ' + source + ' -o ' + object 
                print cmd
                failure = os.system(cmd)
                if failure:
                    raise ValueError, 'failure during compile' 
                object_files.append(object)
        return object_files
        #return all object files to make sure everything is archived 
        #return map(lambda x: x[1], file_pairs)

    def f90_compile(self,source_files,module_dirs=None, temp_dir=''):
        switches = string.join((self.f90_switches, self.f90_opt))
        return self.f_compile(self.f90_compiler,switches,
                              source_files, module_dirs,temp_dir)

    def f77_compile(self,source_files,module_dirs=None, temp_dir=''):
        switches = string.join((self.f77_switches, self.f77_opt))
        return self.f_compile(self.f77_compiler,switches,
                              source_files, module_dirs,temp_dir)


    def build_module_switch(self, module_dirs):
        return ''

    def create_static_lib(self, object_files, library_name,
                          output_dir='', debug=None):
        lib_file = os.path.join(output_dir,'lib'+library_name+'.a')
        newer = distutils.dep_util.newer
        # This doesn't work -- no way to know if the file is in the archive
        #object_files = filter(lambda o,lib=lib_file:\
        #                 distutils.dep_util.newer(o,lib),object_files)
        objects = string.join(object_files)
        if objects:
            cmd = 'ar -cur  %s %s' % (lib_file,objects)
            print cmd
            os.system(cmd)

    def build_library(self,library_name,source_list,module_dirs=None,
                      temp_dir = ''):
        #make sure the temp directory exists before trying to build files
        import distutils.dir_util
        distutils.dir_util.mkpath(temp_dir)
        #this compiles the files
        object_list = self.to_object(source_list,module_dirs,temp_dir)
        # actually we need to use all the object file names here to
        # make sure the library is always built.  It could occur that an
        # object file exists but hasn't been put in the archive. (happens
        # a lot when builds fail once and are restarted).
        object_list = self.source_to_object_names(source_list, temp_dir)
        #self.create_static_lib(object_list,library_name,temp_dir)           
        # This is pure bunk...
        # Windows fails for long argument strings on the command line.
        # if objects is real long (> 2048 chars or so on my machine),
        # the command fails (cmd.exe /e:2048 on w2k)
        # for now we'll split linking into to steps which should work for
        objects = object_list[:]
        while objects:
            obj,objects = objects[:20],objects[20:]
            self.create_static_lib(obj,library_name,temp_dir)

    def dummy_fortran_files(self):
        import tempfile 
        d = tempfile.gettempdir()
        dummy_name = os.path.join(d,'__dummy.f')
        dummy = open(dummy_name,'w')
        dummy.write("      subroutine dummy()\n      end\n")
        dummy.close()
        return (os.path.join(d,'__dummy.f'),os.path.join(d,'__dummy.o'))
    
    def is_available(self):
        return self.get_version()
        
    def get_version(self):
        """Return the compiler version. If compiler is not available,
        return empty string."""
        # XXX: Is there compilers that have no version? If yes,
        #      this test will fail even if the compiler is available.
        if self.version is not None:
            # Finding version is expensive, so return previously found
            # version string.
            return self.version
        self.version = ''
        # works I think only for unix...        
        #print 'command:', self.ver_cmd
        exit_status, out_text = run_command(self.ver_cmd)
        #print exit_status, out_text
        if not exit_status:
            m = re.match(self.ver_match,out_text)
            if m:
                self.version = m.group('version')
        return self.version

    def get_libraries(self):
        return self.libraries
    def get_library_dirs(self):
        return self.library_dirs
    def get_extra_link_args(self):
        return []
    def get_runtime_library_dirs(self):
        return []
    def get_linker_so(self):
        """
        If a compiler requires specific linker then return a list
        containing a linker executable name and linker options.
        Otherwise, return None.
        """

    def __str__(self):
        return "%s %s" % (self.vendor, self.get_version())


class absoft_fortran_compiler(fortran_compiler_base):

    vendor = 'Absoft'
    ver_match = r'FORTRAN 77 Compiler (?P<version>[^\s*,]*).*?Absoft Corp'
    
    def __init__(self, fc = None, f90c = None):
        fortran_compiler_base.__init__(self)
        if fc is None:
            fc = 'f77'
        if f90c is None:
            f90c = 'f90'

        self.f77_compiler = fc
        self.f90_compiler = f90c

        # got rid of -B108 cause it was generating 2 underscores instead
        # of one on the newest version.  Now we use -YEXT_SFX=_ to 
        # specify the output format
        if os.name == 'nt':
            self.f90_switches = '-f fixed  -YCFRL=1 -YCOM_NAMES=LCS' \
                                ' -YCOM_PFX  -YEXT_PFX -YEXT_NAMES=LCS' \
                                ' -YCOM_SFX=_ -YEXT_SFX=_ -YEXT_NAMES=LCS'        
            self.f90_opt = '-O -Q100'
            self.f77_switches = '-N22 -N90 -N110'
            self.f77_opt = '-O -Q100'
            self.libraries = ['fio', 'fmath', 'f90math', 'COMDLG32']
        else:
            self.f90_switches = '-ffixed  -YCFRL=1 -YCOM_NAMES=LCS' \
                                ' -YCOM_PFX  -YEXT_PFX -YEXT_NAMES=LCS' \
                                ' -YCOM_SFX=_ -YEXT_SFX=_ -YEXT_NAMES=LCS'        
            self.f90_opt = '-O -B101'                            
            self.f77_switches = '-N22 -N90 -N110 -B108'
            self.f77_opt = '-O -B101'

            self.libraries = ['fio', 'f77math', 'f90math']
        
        try:
            dir = os.environ['ABSOFT'] 
            self.library_dirs = [os.path.join(dir,'lib')]
        except KeyError:
            self.library_dirs = []

        self.ver_cmd = self.f77_compiler + ' -V -c %s -o %s' % \
                       self.dummy_fortran_files()

    def build_module_switch(self,module_dirs):
        res = ''
        if module_dirs:
            for mod in module_dirs:
                res = res + ' -p' + mod
        return res

    def get_extra_link_args(self):
        return []
        # Couldn't get this to link for anything using gcc.
        #dr = "c:\\Absoft62\\lib"
        #libs = ['fio.lib', 'COMDLG32.lib','fmath.lib', 'f90math.lib','libcomdlg32.a' ]        
        #libs = map(lambda x,dr=dr:os.path.join(dr,x),libs)
        #return libs


class sun_fortran_compiler(fortran_compiler_base):

    vendor = 'Sun'
    ver_match =  r'f77: (?P<version>[^\s*,]*)'

    def __init__(self, fc = None, f90c = None):
        fortran_compiler_base.__init__(self)
        if fc is None:
            fc = 'f77'
        if f90c is None:
            f90c = 'f90'

        self.f77_compiler = fc # not tested
        self.f77_switches = ' -pic '
        self.f77_opt = ' -fast -dalign '

        self.f90_compiler = f90c
        self.f90_switches = ' -fixed ' # ??? why fixed?
        self.f90_opt = ' -fast -dalign '

        self.libraries = ['f90', 'F77', 'M77', 'sunmath', 'm']
        #threaded
        #self.libraries = ['f90', 'F77_mt', 'sunmath_mt', 'm', 'thread']
        #self.libraries = []
        self.library_dirs = self.find_lib_dir()
        #print 'sun:',self.library_dirs

        self.ver_cmd = self.f77_compiler + ' -V'

    def build_module_switch(self,module_dirs):
        res = ''
        if module_dirs:
            for mod in module_dirs:
                res = res + ' -M' + mod
        return res

    def find_lib_dir(self):
        library_dirs = []
        lib_match = r'### f90: Note: LD_RUN_PATH\s*= '\
                     '(?P<lib_paths>[^\s.]*).*'
        cmd = self.f90_compiler + ' -dryrun dummy.f'
        exit_status, output = run_command(cmd)
        if not exit_status:
            libs = re.findall(lib_match,output)
            if libs:
                library_dirs = string.split(libs[0],':')
                self.get_version() # force version calculation
                compiler_home = os.path.dirname(library_dirs[0])
                library_dirs.append(os.path.join(compiler_home,
                                               self.version,'lib'))
        return library_dirs
    def get_runtime_library_dirs(self):
        return self.find_lib_dir()
    def get_extra_link_args(self):
        return ['-mimpure-text']


class mips_fortran_compiler(fortran_compiler_base):

    vendor = 'SGI'
    ver_match =  r'MIPSpro Compilers: Version (?P<version>[^\s*,]*)'
    
    def __init__(self, fc = None, f90c = None):
        fortran_compiler_base.__init__(self)
        if fc is None:
            fc = 'f77'
        if f90c is None:
            f90c = 'f90'

        self.f77_compiler = fc         # not tested
        self.f77_switches = ' -n32 -KPIC '
        self.f77_opt = ' -O3 '

        self.f90_compiler = f90c
        self.f90_switches = ' -n32 -KPIC -fixedform ' # why fixed ???
        self.f90_opt = ' '                            
        
        self.libraries = ['fortran', 'ftn', 'm']
        self.library_dirs = self.find_lib_dir()

        self.ver_cmd = self.f77_compiler + ' -version'

    def build_module_switch(self,module_dirs):
        res = ''
        return res 
    def find_lib_dir(self):
        library_dirs = []
        return library_dirs
    def get_runtime_library_dirs(self):
	return self.find_lib_dir() 
    def get_extra_link_args(self):
	return []


class gnu_fortran_compiler(fortran_compiler_base):

    vendor = 'Gnu'
    ver_match = r'g77 version (?P<version>[^\s*]*)'

    def __init__(self, fc = None, f90c = None):
        fortran_compiler_base.__init__(self)
        self.libraries = ['gcc','g2c']
        self.library_dirs = self.find_lib_directories()

        if fc is None:
            fc = 'g77'
        if f90c is None:
            f90c = fc

        self.f77_compiler = fc

        switches = ' -Wall -fno-second-underscore '

        if os.name != 'nt':
            switches = switches + ' -fpic '

        self.f77_switches = switches

        self.ver_cmd = self.f77_compiler + ' -v '
        self.f77_opt = self.get_opt()

    def get_opt(self):
        import cpuinfo
        cpu = cpuinfo.cpuinfo()
        opt = ' -O3 '
        
        # only check for more optimizaiton if g77 can handle
        # it.
        if self.get_version():
            if self.version[0]=='3': # is g77 3.x.x
                if cpu.is_AthlonK6():
                    opt = opt + ' -march=k6 '
                elif cpu.is_AthlonK7():
                    opt = opt + ' -march=athlon '
            if cpu.is_i686():
                opt = opt + ' -march=i686 '
            elif cpu.is_i586():
                opt = opt + ' -march=i586 '
            elif cpu.is_i486():
                opt = opt + ' -march=i486 '
            elif cpu.is_i386():
                opt = opt + ' -march=i386 '
                
        return opt
        
    def find_lib_directories(self):
        lib_dir = []
        match = r'Reading specs from (.*)/specs'

        # works I think only for unix...        
        exit_status, out_text = run_command('g77 -v')
        if not exit_status:
            m = re.findall(match,out_text)
            if m:
				lib_dir= m #m[0]          
        return lib_dir

    def get_linker_so(self):
        # win32 linking should be handled by standard linker
        if sys.platform != 'win32':
            return [self.f77_compiler,'-shared']
 
    def f90_compile(self,source_files,module_files,temp_dir=''):
        raise DistutilsExecError, 'f90 not supported by Gnu'


#http://developer.intel.com/software/products/compilers/f50/linux/
class intel_ia32_fortran_compiler(fortran_compiler_base):

    vendor = 'Intel' # Intel(R) Corporation 
    ver_match = r'Intel\(R\) Fortran Compiler for 32-bit applications, Version (?P<version>[^\s*]*)'

    def __init__(self, fc = None, f90c = None):
        fortran_compiler_base.__init__(self)

        if fc is None:
            fc = 'ifc'
        if f90c is None:
            f90c = fc

        self.f77_compiler = fc
        self.f90_compiler = f90c

        switches = ' -KPIC '

        import cpuinfo
        cpu = cpuinfo.cpuinfo()
        if cpu.has_fdiv_bug():
            switches = switches + ' -fdiv_check '
        if cpu.has_f00f_bug():
            switches = switches + ' -0f_check '
        self.f77_switches = self.f90_switches = switches
        self.f77_switches = self.f77_switches + ' -FI '

        self.f77_opt = self.f90_opt = self.get_opt()
        
        debug = ' -g -C '
        self.f77_debug =  self.f90_debug = debug

        self.ver_cmd = self.f77_compiler+' -FI -V -c %s -o %s' %\
                       self.dummy_fortran_files()

    def get_opt(self):
        import cpuinfo
        cpu = cpuinfo.cpuinfo()
        opt = ' -O3 '
        if cpu.is_PentiumPro() or cpu.is_PentiumII():
            opt = opt + ' -tpp6 -xi '
        elif cpu.is_PentiumIII():
            opt = opt + ' -tpp6 '
        elif cpu.is_Pentium():
            opt = opt + ' -tpp5 '
        elif cpu.is_PentiumIV():
            opt = opt + ' -tpp7 -xW '
        if cpu.has_mmx():
            opt = opt + ' -xM '       
        return opt
        

    def get_linker_so(self):
        return [self.f77_compiler,'-shared']


class intel_itanium_fortran_compiler(intel_ia32_fortran_compiler):

    vendor = 'Itanium'
    ver_match = r'Intel\(R\) Fortran 90 Compiler Itanium\(TM\) Compiler for the Itanium\(TM\)-based applications, Version (?P<version>[^\s*]*)'

    def __init__(self, fc = None, f90c = None):
        if fc is None:
            fc = 'efc'
        intel_ia32_fortran_compiler.__init__(self, fc, f90c)


class nag_fortran_compiler(fortran_compiler_base):

    vendor = 'NAG'
    ver_match = r'NAGWare Fortran 95 compiler Release (?P<version>[^\s]*)'

    def __init__(self, fc = None, f90c = None):
        fortran_compiler_base.__init__(self)

        if fc is None:
            fc = 'f95'
        if f90c is None:
            f90c = fc

        self.f77_compiler = fc
        self.f90_compiler = f90c

        switches = ''
        debug = ' -g -gline -g90 -nan -C '
        opt = ' -O4 '

        self.f77_switches = self.f90_switches = switches
        self.f77_switches = self.f77_switches + ' -fixed '
        self.f77_debug = self.f90_debug = debug
        self.f77_opt = self.f90_opt = opt

        self.ver_cmd = self.f77_compiler+' -V '

    def get_linker_so(self):
        return [self.f77_compiler,'-Wl,-shared']


class vast_fortran_compiler(fortran_compiler_base):

    vendor = 'VAST'
    ver_match = r'\s*Pacific-Sierra Research vf90 (Personal|Professional)\s+(?P<version>[^\s]*)'

    def __init__(self, fc = None, f90c = None):
        fortran_compiler_base.__init__(self)

        if fc is None:
            fc = 'g77'
        if f90c is None:
            f90c = 'f90'

        self.f77_compiler = fc
        self.f90_compiler = f90c

        d,b = os.path.split(f90c)
        vf90 = os.path.join(d,'v'+b)
        self.ver_cmd = vf90+' -v '

        gnu = gnu_fortran_compiler(fc)
        if not gnu.is_available(): # VAST compiler requires g77.
            self.version = ''
            return
        if not self.is_available():
            return

        self.f77_switches = gnu.f77_switches
        self.f77_debug = gnu.f77_debug
        self.f77_opt = gnu.f77_opt        

        # XXX: need f90 switches, debug, opt

    def get_linker_so(self):
        return [self.f90_compiler,'-shared']


def match_extension(files,ext):
    match = re.compile(r'.*[.]('+ext+r')\Z',re.I).match
    return filter(lambda x,match = match: match(x),files)

def get_f77_files(files):
    return match_extension(files,'for|f77|ftn|f')

def get_f90_files(files):
    return match_extension(files,'f90|f95')

def get_fortran_files(files):
    return match_extension(files,'f90|f95|for|f77|ftn|f')

def find_fortran_compiler(vendor = None, fc = None, f90c = None):
    fcompiler = None
    for compiler_class in all_compilers:
        if vendor is not None and vendor != compiler_class.vendor:
            continue
        print compiler_class
        compiler = compiler_class(fc,f90c)
        if compiler.is_available():
            fcompiler = compiler
            break
    return fcompiler

all_compilers = [absoft_fortran_compiler,
                 mips_fortran_compiler,
                 sun_fortran_compiler,
                 gnu_fortran_compiler,
                 intel_ia32_fortran_compiler,
                 intel_itanium_fortran_compiler,
                 nag_fortran_compiler,
                 vast_fortran_compiler,
                 ]

if __name__ == "__main__":
    show_compilers()

from distutils.command.install_data import *
from distutils.command.install_data import install_data as old_install_data

#data installer with improved intelligence over distutils
#data files are copied into the project directory instead
#of willy-nilly
class install_data (old_install_data):
    def finalize_options (self):
        print 'hhhhhhhhhhhheeeeeeeeeeerrrrrrrrrrrreeeeeeeeeeeee'
        self.set_undefined_options('install',
                                   ('install_lib', 'install_dir'),
                                   ('root', 'root'),
                                   ('force', 'force'),
                                  )

