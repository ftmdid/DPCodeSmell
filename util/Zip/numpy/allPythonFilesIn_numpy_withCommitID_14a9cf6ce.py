#!/usr/bin/env python
"""
Bundle of SciPy core modules:
  scipy_test
  scipy_distutils
  scipy_base
  weave

Usage:
   python setup.py install
   python setup.py sdist -f
"""

import os
import sys

from scipy_distutils.core import setup
from scipy_distutils.misc_util import default_config_dict
from scipy_distutils.misc_util import get_path, merge_config_dicts

bundle_packages = ['scipy_distutils','scipy_test','scipy_base','weave']

def setup_package():
    old_path = os.getcwd()
    local_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    os.chdir(local_path)
    sys.path.insert(0, local_path)

    try:
        configs = [{'name':'Scipy_core'}]
        versions = []
        for n in bundle_packages:
            sys.path.insert(0,os.path.join(local_path,n))
            try:
                mod = __import__('setup_'+n)
                configs.append(mod.configuration(parent_path=local_path))
                mod = __import__(n+'_version')
                versions.append(mod)
            finally:
                del sys.path[0]
   
        config_dict = merge_config_dicts(configs)

        major = max([v.major for v in versions])
        minor = max([v.minor for v in versions])
        micro = max([v.micro for v in versions])
        release_level = min([v.release_level for v in versions])
        release_level = ''
        cvs_minor = reduce(lambda a,b:a+b,[v.cvs_minor for v in versions],0)
        cvs_serial = reduce(lambda a,b:a+b,[v.cvs_serial for v in versions],0)

        if release_level:
            scipy_core_version = '%(major)d.%(minor)d.%(micro)d'\
                                 '_%(release_level)s'\
                                 '_%(cvs_minor)d.%(cvs_serial)d' % (locals ())
        else:
            scipy_core_version = '%(major)d.%(minor)d.%(micro)d'\
                                 '_%(cvs_minor)d.%(cvs_serial)d' % (locals ())

        print 'SciPy Core Version %s' % scipy_core_version
        setup( version = scipy_core_version,
               maintainer = "SciPy Developers",
               maintainer_email = "scipy-dev@scipy.org",
               description = "SciPy core modules: scipy_{distutils,test,base}",
               license = "SciPy License (BSD Style)",
               url = "http://www.scipy.org",
               **config_dict
               )

    finally:
        del sys.path[0]
        os.chdir(old_path)

if __name__ == "__main__":
    setup_package()

""" Track relationships between compiled extension functions & code fragments

    catalog keeps track of which compiled(or even standard) functions are 
    related to which code fragments.  It also stores these relationships
    to disk so they are remembered between Python sessions.  When 
    
        a = 1
        compiler.inline('printf("printed from C: %d",a);',['a'] )
     
    is called, inline() first looks to see if it has seen the code 
    'printf("printed from C");' before.  If not, it calls 
    
        catalog.get_functions('printf("printed from C: %d", a);')
    
    which returns a list of all the function objects that have been compiled
    for the code fragment.  Multiple functions can occur because the code
    could be compiled for different types for 'a' (although not likely in
    this case). The catalog first looks in its cache and quickly returns
    a list of the functions if possible.  If the cache lookup fails, it then
    looks through possibly multiple catalog files on disk and fills its
    cache with all the functions that match the code fragment.  
    
    In case where the code fragment hasn't been compiled, inline() compiles
    the code and then adds it to the catalog:
    
        function = <code to compile function>
        catalog.add_function('printf("printed from C: %d", a);',function)
           
    add_function() adds function to the front of the cache.  function,
    along with the path information to its module, are also stored in a
    persistent catalog for future use by python sessions.    
"""       

import os,sys,string
import pickle
import tempfile

try:
    import dbhash
    import shelve
    dumb = 0
except ImportError:
    import dumb_shelve as shelve
    dumb = 1

#For testing...
#import dumb_shelve as shelve
#dumb = 1

#import shelve
#dumb = 0
    
def getmodule(object):
    """ Discover the name of the module where object was defined.
    
        This is an augmented version of inspect.getmodule that can discover 
        the parent module for extension functions.
    """
    import inspect
    value = inspect.getmodule(object)
    if value is None:
        #walk trough all modules looking for function
        for name,mod in sys.modules.items():
            # try except used because of some comparison failures
            # in wxPoint code.  Need to review this
            try:
                if mod and object in mod.__dict__.values():
                    value = mod
                    # if it is a built-in module, keep looking to see
                    # if a non-builtin also has it.  Otherwise quit and
                    # consider the module found. (ain't perfect, but will 
                    # have to do for now).
                    if string.find('(built-in)',str(mod)) is -1:
                        break
                    
            except (TypeError, KeyError, ImportError):
                pass        
    return value

def expr_to_filename(expr):
    """ Convert an arbitrary expr string to a valid file name.
    
        The name is based on the md5 check sum for the string and
        Something that was a little more human readable would be 
        nice, but the computer doesn't seem to care.
    """
    import md5
    base = 'sc_'
    return base + md5.new(expr).hexdigest()

def unique_file(d,expr):
    """ Generate a unqiue file name based on expr in directory d
    
        This is meant for use with building extension modules, so
        a file name is considered unique if none of the following
        extension '.cpp','.o','.so','module.so','.py', or '.pyd'
        exists in directory d.  The fully qualified path to the
        new name is returned.  You'll need to append your own
        extension to it before creating files.
    """
    files = os.listdir(d)
    #base = 'scipy_compile'
    base = expr_to_filename(expr)
    for i in range(1000000):
        fname = base + `i`
        if not (fname+'.cpp' in files or
                fname+'.o' in files or
                fname+'.so' in files or
                fname+'module.so' in files or
                fname+'.py' in files or
                fname+'.pyd' in files):
            break
    return os.path.join(d,fname)

def create_dir(p):
    """ Create a directory and any necessary intermediate directories."""
    if not os.path.exists(p):
        try:
            os.mkdir(p)
        except OSError:
            # perhaps one or more intermediate path components don't exist
            # try to create them
            base,dir = os.path.split(p)
            create_dir(base)
            # don't enclose this one in try/except - we want the user to
            # get failure info
            os.mkdir(p)

def is_writable(dir):
    dummy = os.path.join(dir, "dummy")
    try:
        open(dummy, 'w')
    except IOError:
        return 0
    os.unlink(dummy)
    return 1

def whoami():
    """return a string identifying the user."""
    return os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"

def default_dir():
    """ Return a default location to store compiled files and catalogs.
        
        XX is the Python version number in all paths listed below
        On windows, the default location is the temporary directory
        returned by gettempdir()/pythonXX.
        
        On Unix, ~/.pythonXX_compiled is the default location.  If it doesn't
        exist, it is created.  The directory is marked rwx------.
        
        If for some reason it isn't possible to build a default directory
        in the user's home, /tmp/<uid>_pythonXX_compiled is used.  If it 
        doesn't exist, it is created.  The directory is marked rwx------
        to try and keep people from being able to sneak a bad module
        in on you.        
    """
    python_name = "python%d%d_compiled" % tuple(sys.version_info[:2])    
    if sys.platform != 'win32':
        try:
            path = os.path.join(os.environ['HOME'],'.' + python_name)
        except KeyError:
            temp_dir = `os.getuid()` + '_' + python_name
            path = os.path.join(tempfile.gettempdir(),temp_dir)        
        
        # add a subdirectory for the OS.
        # It might be better to do this at a different location so that
        # it wasn't only the default directory that gets this behavior.    
        #path = os.path.join(path,sys.platform)
    else:
        path = os.path.join(tempfile.gettempdir(),"%s"%whoami(),python_name)
        
    if not os.path.exists(path):
        create_dir(path)
        os.chmod(path,0700) # make it only accessible by this user.
    if not is_writable(path):
        print 'warning: default directory is not write accessible.'
        print 'default:', path
    return path

def intermediate_dir():
    """ Location in temp dir for storing .cpp and .o  files during
        builds.
    """
    python_name = "python%d%d_intermediate" % tuple(sys.version_info[:2])    
    path = os.path.join(tempfile.gettempdir(),"%s"%whoami(),python_name)
    if not os.path.exists(path):
        create_dir(path)
    return path
    
def default_temp_dir():
    path = os.path.join(default_dir(),'temp')
    if not os.path.exists(path):
        create_dir(path)
        os.chmod(path,0700) # make it only accessible by this user.
    if not is_writable(path):
        print 'warning: default directory is not write accessible.'
        print 'default:', path
    return path

    
def os_dependent_catalog_name():
    """ Generate catalog name dependent on OS and Python version being used.
    
        This allows multiple platforms to have catalog files in the
        same directory without stepping on each other.  For now, it 
        bases the name of the value returned by sys.platform and the
        version of python being run.  If this isn't enough to descriminate
        on some platforms, we can try to add other info.  It has 
        occured to me that if we get fancy enough to optimize for different
        architectures, then chip type might be added to the catalog name also.
    """
    version = '%d%d' % sys.version_info[:2]
    return sys.platform+version+'compiled_catalog'
    
def catalog_path(module_path):
    """ Return the full path name for the catalog file in the given directory.
    
        module_path can either be a file name or a path name.  If it is a 
        file name, the catalog file name in its parent directory is returned.
        If it is a directory, the catalog file in that directory is returned.

        If module_path doesn't exist, None is returned.  Note though, that the
        catalog file does *not* have to exist, only its parent.  '~', shell
        variables, and relative ('.' and '..') paths are all acceptable.
        
        catalog file names are os dependent (based on sys.platform), so this 
        should support multiple platforms sharing the same disk space 
        (NFS mounts). See os_dependent_catalog_name() for more info.
    """
    module_path = os.path.expanduser(module_path)
    module_path = os.path.expandvars(module_path)
    module_path = os.path.abspath(module_path)
    if not os.path.exists(module_path):
        catalog_file = None
    elif not os.path.isdir(module_path):
        module_path,dummy = os.path.split(module_path)
        catalog_file = os.path.join(module_path,os_dependent_catalog_name())
    else:    
        catalog_file = os.path.join(module_path,os_dependent_catalog_name())
    return catalog_file

def get_catalog(module_path,mode='r'):
    """ Return a function catalog (shelve object) from the path module_path

        If module_path is a directory, the function catalog returned is
        from that directory.  If module_path is an actual module_name,
        then the function catalog returned is from its parent directory.
        mode uses the standard 'c' = create, 'n' = new, 'r' = read, 
        'w' = write file open modes available for anydbm databases.
        
        Well... it should be.  Stuck with dumbdbm for now and the modes
        almost don't matter.  We do some checking for 'r' mode, but that
        is about it.
        
        See catalog_path() for more information on module_path.
    """
    if mode not in ['c','r','w','n']:
        msg = " mode must be 'c', 'n', 'r', or 'w'.  See anydbm for more info"
        raise ValueError, msg
    catalog_file = catalog_path(module_path)
    if (dumb and os.path.exists(catalog_file+'.dat')) \
           or os.path.exists(catalog_file):
        sh = shelve.open(catalog_file,mode)
    else:
        if mode=='r':
            sh = None
        else:
            sh = shelve.open(catalog_file,mode)
    return sh

class catalog:
    """ Stores information about compiled functions both in cache and on disk.
    
        catalog stores (code, list_of_function) pairs so that all the functions
        that have been compiled for code are available for calling (usually in
        inline or blitz).
        
        catalog keeps a dictionary of previously accessed code values cached 
        for quick access.  It also handles the looking up of functions compiled 
        in previously called Python sessions on disk in function catalogs. 
        catalog searches the directories in the PYTHONCOMPILED environment 
        variable in order loading functions that correspond to the given code 
        fragment.  A default directory is also searched for catalog functions. 
        On unix, the default directory is usually '~/.pythonxx_compiled' where 
        xx is the version of Python used. On windows, it is the directory 
        returned by temfile.gettempdir().  Functions closer to the front are of 
        the variable list are guaranteed to be closer to the front of the 
        function list so that they will be called first.  See 
        get_cataloged_functions() for more info on how the search order is 
        traversed.
        
        Catalog also handles storing information about compiled functions to
        a catalog.  When writing this information, the first writable catalog
        file in PYTHONCOMPILED path is used.  If a writable catalog is not
        found, it is written to the catalog in the default directory.  This
        directory should always be writable.
    """
    def __init__(self,user_path_list=None):
        """ Create a catalog for storing/searching for compiled functions. 
        
            user_path_list contains directories that should be searched 
            first for function catalogs.  They will come before the path
            entries in the PYTHONCOMPILED environment varilable.
        """
        if type(user_path_list) == type('string'):
            self.user_path_list = [user_path_list]
        elif user_path_list:
            self.user_path_list = user_path_list
        else:
            self.user_path_list = []
        self.cache = {}
        self.module_dir = None
        self.paths_added = 0
        
    def set_module_directory(self,module_dir):
        """ Set the path that will replace 'MODULE' in catalog searches.
        
            You should call clear_module_directory() when your finished
            working with it.
        """
        self.module_dir = module_dir
    def get_module_directory(self):
        """ Return the path used to replace the 'MODULE' in searches.
        """
        return self.module_dir
    def clear_module_directory(self):
        """ Reset 'MODULE' path to None so that it is ignored in searches.        
        """
        self.module_dir = None
        
    def get_environ_path(self):
        """ Return list of paths from 'PYTHONCOMPILED' environment variable.
        
            On Unix the path in PYTHONCOMPILED is a ':' separated list of
            directories.  On Windows, a ';' separated list is used. 
        """
        paths = []
        if os.environ.has_key('PYTHONCOMPILED'):
            path_string = os.environ['PYTHONCOMPILED'] 
            if sys.platform == 'win32':
                #probably should also look in registry
                paths = path_string.split(';')
            else:    
                paths = path_string.split(':')
        return paths    

    def build_search_order(self):
        """ Returns a list of paths that are searched for catalogs.  
        
            Values specified in the catalog constructor are searched first,
            then values found in the PYTHONCOMPILED environment variable.
            The directory returned by default_dir() is always returned at
            the end of the list.
            
            There is a 'magic' path name called 'MODULE' that is replaced
            by the directory defined by set_module_directory().  If the
            module directory hasn't been set, 'MODULE' is ignored.
        """
        
        paths = self.user_path_list + self.get_environ_path()
        search_order = []
        for path in paths:
            if path == 'MODULE':
                if self.module_dir:
                    search_order.append(self.module_dir)
            else:
                search_order.append(path)
        search_order.append(default_dir())
        return search_order

    def get_catalog_files(self):
        """ Returns catalog file list in correct search order.
          
            Some of the catalog files may not currently exists.
            However, all will be valid locations for a catalog
            to be created (if you have write permission).
        """
        files = map(catalog_path,self.build_search_order())
        files = filter(lambda x: x is not None,files)
        return files

    def get_existing_files(self):
        """ Returns all existing catalog file list in correct search order.
        """
        files = self.get_catalog_files()
        # open every stinking file to check if it exists.
        # This is because anydbm doesn't provide a consistent naming 
        # convention across platforms for its files 
        existing_files = []
        for file in files:
            if get_catalog(os.path.dirname(file),'r') is not None:
                existing_files.append(file)
        # This is the non-portable (and much faster) old code
        #existing_files = filter(os.path.exists,files)
        return existing_files

    def get_writable_file(self,existing_only=0):
        """ Return the name of the first writable catalog file.
        
            Its parent directory must also be writable.  This is so that
            compiled modules can be written to the same directory.
        """
        # note: both file and its parent directory must be writeable
        if existing_only:
            files = self.get_existing_files()
        else:
            files = self.get_catalog_files()
        # filter for (file exists and is writable) OR directory is writable
        def file_test(x):
            from os import access, F_OK, W_OK
            return (access(x,F_OK) and access(x,W_OK) or
                    access(os.path.dirname(x),W_OK))
        writable = filter(file_test,files)
        if writable:
            file = writable[0]
        else:
            file = None
        return file
        
    def get_writable_dir(self):
        """ Return the parent directory of first writable catalog file.
        
            The returned directory has write access.
        """
        return os.path.dirname(self.get_writable_file())
        
    def unique_module_name(self,code,module_dir=None):
        """ Return full path to unique file name that in writable location.
        
            The directory for the file is the first writable directory in 
            the catalog search path.  The unique file name is derived from
            the code fragment.  If, module_dir is specified, it is used
            to replace 'MODULE' in the search path.
        """
        if module_dir is not None:
            self.set_module_directory(module_dir)
        try:
            d = self.get_writable_dir()
        finally:
            if module_dir is not None:
                self.clear_module_directory()
        return unique_file(d,code)

    def path_key(self,code):
        """ Return key for path information for functions associated with code.
        """
        return '__path__' + code
        
    def configure_path(self,cat,code):
        """ Add the python path for the given code to the sys.path
        
            unconfigure_path() should be called as soon as possible after
            imports associated with code are finished so that sys.path 
            is restored to normal.
        """
        try:
            paths = cat[self.path_key(code)]
            self.paths_added = len(paths)
            sys.path = paths + sys.path
        except:
            self.paths_added = 0            
                    
    def unconfigure_path(self):
        """ Restores sys.path to normal after calls to configure_path()
        
            Remove the previously added paths from sys.path
        """
        sys.path = sys.path[self.paths_added:]
        self.paths_added = 0

    def get_cataloged_functions(self,code):
        """ Load all functions associated with code from catalog search path.
        
            Sometimes there can be trouble loading a function listed in a
            catalog file because the actual module that holds the function 
            has been moved or deleted.  When this happens, that catalog file
            is "repaired", meaning the entire entry for this function is 
            removed from the file.  This only affects the catalog file that
            has problems -- not the others in the search path.
            
            The "repair" behavior may not be needed, but I'll keep it for now.
        """
        mode = 'r'
        cat = None
        function_list = []
        for path in self.build_search_order():
            cat = get_catalog(path,mode)
            if cat is not None and cat.has_key(code):
                # set up the python path so that modules for this
                # function can be loaded.
                self.configure_path(cat,code)
                try:                    
                    function_list += cat[code]
                except: #SystemError and ImportError so far seen                        
                    # problems loading a function from the catalog.  Try to
                    # repair the cause.
                    cat.close()
                    self.repair_catalog(path,code)
                self.unconfigure_path()             
        return function_list


    def repair_catalog(self,catalog_path,code):
        """ Remove entry for code from catalog_path
        
            Occasionally catalog entries could get corrupted. An example
            would be when a module that had functions in the catalog was
            deleted or moved on the disk.  The best current repair method is 
            just to trash the entire catalog entry for this piece of code.  
            This may loose function entries that are valid, but thats life.
            
            catalog_path must be writable for repair.  If it isn't, the
            function exists with a warning.            
        """
        writable_cat = None
        if not os.path.exists(catalog_path):
            return
        try:
            writable_cat = get_catalog(catalog_path,'w')
        except:
            print 'warning: unable to repair catalog entry\n %s\n in\n %s' % \
                  (code,catalog_path)
            return          
        if writable_cat.has_key(code):
            print 'repairing catalog by removing key'
            del writable_cat[code]
        
        # it is possible that the path key doesn't exist (if the function registered
        # was a built-in function), so we have to check if the path exists before
        # arbitrarily deleting it.
        path_key = self.path_key(code)       
        if writable_cat.has_key(path_key):
            del writable_cat[path_key]   
            
    def get_functions_fast(self,code):
        """ Return list of functions for code from the cache.
        
            Return an empty list if the code entry is not found.
        """
        return self.cache.get(code,[])
                
    def get_functions(self,code,module_dir=None):
        """ Return the list of functions associated with this code fragment.
        
            The cache is first searched for the function.  If an entry
            in the cache is not found, then catalog files on disk are 
            searched for the entry.  This is slooooow, but only happens
            once per code object.  All the functions found in catalog files
            on a cache miss are loaded into the cache to speed up future calls.
            The search order is as follows:
            
                1. user specified path (from catalog initialization)
                2. directories from the PYTHONCOMPILED environment variable
                3. The temporary directory on your platform.

            The path specified by module_dir will replace the 'MODULE' 
            place holder in the catalog search path. See build_search_order()
            for more info on the search path. 
        """        
        # Fast!! try cache first.
        if self.cache.has_key(code):
            return self.cache[code]
        
        # 2. Slow!! read previously compiled functions from disk.
        try:
            self.set_module_directory(module_dir)
            function_list = self.get_cataloged_functions(code)
            # put function_list in cache to save future lookups.
            if function_list:
                self.cache[code] = function_list
            # return function_list, empty or otherwise.
        finally:
            self.clear_module_directory()
        return function_list

    def add_function(self,code,function,module_dir=None):
        """ Adds a function to the catalog.
        
            The function is added to the cache as well as the first
            writable file catalog found in the search path.  If no
            code entry exists in the cache, the on disk catalogs
            are loaded into the cache and function is added to the
            beginning of the function list.
            
            The path specified by module_dir will replace the 'MODULE' 
            place holder in the catalog search path. See build_search_order()
            for more info on the search path. 
        """    

        # 1. put it in the cache.
        if self.cache.has_key(code):
            if function not in self.cache[code]:
                self.cache[code].insert(0,function)
            else:
                # if it is in the cache, then it is also
                # been persisted 
                return
        else:           
            # Load functions and put this one up front
            self.cache[code] = self.get_functions(code)          
            self.fast_cache(code,function)
        # 2. Store the function entry to disk.    
        try:
            self.set_module_directory(module_dir)
            self.add_function_persistent(code,function)
        finally:
            self.clear_module_directory()
        
    def add_function_persistent(self,code,function):
        """ Store the code->function relationship to disk.
        
            Two pieces of information are needed for loading functions
            from disk -- the function pickle (which conveniently stores
            the module name, etc.) and the path to its module's directory.
            The latter is needed so that the function can be loaded no
            matter what the user's Python path is.
        """       
        # add function to data in first writable catalog
        mode = 'c' # create if doesn't exist, otherwise, use existing
        cat_dir = self.get_writable_dir()
        cat = get_catalog(cat_dir,mode)
        if cat is None:
            cat_dir = default_dir()
            cat = get_catalog(cat_dir,mode)
        if cat is None:
            cat_dir = default_dir()                            
            cat_file = catalog_path(cat_dir)
            print 'problems with default catalog -- removing'
            import glob
            files = glob.glob(cat_file+'*')
            for f in files:
                os.remove(f)
            cat = get_catalog(cat_dir,mode)
        if cat is None:
            raise ValueError, 'Failed to access a catalog for storing functions'    
        # Prabhu was getting some corrupt catalog errors.  I'll put a try/except
        # to protect against this, but should really try and track down the issue.
        function_list = [function]
        try:
            function_list = function_list + cat.get(code,[])
        except pickle.UnpicklingError:
            pass
        cat[code] = function_list
        # now add needed path information for loading function
        module = getmodule(function)
        try:
            # built in modules don't have the __file__ extension, so this
            # will fail.  Just pass in this case since path additions aren't
            # needed for built-in modules.
            mod_path,f=os.path.split(os.path.abspath(module.__file__))
            pkey = self.path_key(code)
            cat[pkey] = [mod_path] + cat.get(pkey,[])
        except:
            pass
	cat.close()

    def fast_cache(self,code,function):
        """ Move function to the front of the cache entry for code
        
            If future calls to the function have the same type signature,
            this will speed up access significantly because the first
            function call is correct.
            
            Note:  The cache added to the inline_tools module is significantly
                   faster than always calling get_functions, so this isn't
                   as necessary as it used to be.  Still, it's probably worth
                   doing.              
        """
        try:
            if self.cache[code][0] == function:
                return
        except: # KeyError, IndexError   
            pass
        try:
            self.cache[code].remove(function)
        except ValueError:
            pass
        # put new function at the beginning of the list to search.
        self.cache[code].insert(0,function)

#!/usr/bin/env python

import os
from glob import glob
from scipy_distutils.misc_util import get_path, default_config_dict, dot_join

def configuration(parent_package='',parent_path=None):
    parent_path2 = parent_path
    parent_path = parent_package
    local_path = get_path(__name__,parent_path2)
    config = default_config_dict('weave',parent_package)
    config['packages'].append(dot_join(parent_package,'weave.tests'))
    test_path = os.path.join(local_path,'tests')
    config['package_dir']['weave.tests'] = test_path
    
    scxx_files = glob(os.path.join(local_path,'scxx','*.*'))
    install_path = os.path.join(parent_path,'weave','scxx')
    config['data_files'].extend( [(install_path,scxx_files)])
    
    blitz_files = glob(os.path.join(local_path,'blitz-20001213','blitz','*.*'))
    install_path = os.path.join(parent_path,'weave','blitz-20001213',
                                'blitz')
    config['data_files'].extend( [(install_path,blitz_files)])
    
    array_files = glob(os.path.join(local_path,'blitz-20001213','blitz',
                                    'array','*.*'))
    install_path = os.path.join(parent_path,'weave','blitz-20001213',
                                'blitz','array')
    config['data_files'].extend( [(install_path,array_files)])
    
    meta_files = glob(os.path.join(local_path,'blitz-20001213','blitz',
                                    'meta','*.*'))
    install_path = os.path.join(parent_path,'weave','blitz-20001213',
                                'blitz','meta')
    config['data_files'].extend( [(install_path,meta_files)])

    swig_files = glob(os.path.join(local_path,'swig','*.c'))
    install_path = os.path.join(parent_path,'weave','swig')
    config['data_files'].extend( [(install_path,swig_files)])

    doc_files = glob(os.path.join(local_path,'doc','*.html'))
    install_path = os.path.join(parent_path,'weave','doc')
    config['data_files'].extend( [(install_path,doc_files)])

    example_files = glob(os.path.join(local_path,'examples','*.py'))
    install_path = os.path.join(parent_path,'weave','examples')
    config['data_files'].extend( [(install_path,example_files)])
    
    return config

if __name__ == '__main__':    
    from scipy_distutils.core import setup
    setup(version = "0.3.0",
          description = "Tools for inlining C/C++ in Python",
          author = "Eric Jones",
          author_email = "eric@enthought.com",
          licence = "SciPy License (BSD Style)",
          url = 'http://www.scipy.org',
          **configuration(parent_path=''))

from types import *
from base_spec import base_converter
import base_info

#----------------------------------------------------------------------------
# C++ code template for converting code from python objects to C++ objects
#
# This is silly code.  There is absolutely no reason why these simple
# conversion functions should be classes.  However, some versions of 
# Mandrake Linux ship with broken C++ compilers (or libraries) that do not
# handle exceptions correctly when they are thrown from functions.  However,
# exceptions thrown from class methods always work, so we make everything
# a class method to solve this error.
#----------------------------------------------------------------------------

#----------------------------------------------------------------------------
# speed note
# the convert_to_int macro below takes about 25 ns per conversion on my
# 850 MHz PIII.  A slightly more sophisticated macro version can trim this
# to 20 ns, but this savings is dang near useless because the other 
# overhead swamps it...
#----------------------------------------------------------------------------
py_to_c_template = \
"""
class %(type_name)s_handler
{
public:    
    %(return_type)s convert_to_%(type_name)s(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        %(inc_ref_count)s
        if (!py_obj || !%(check_func)s(py_obj))
            handle_conversion_error(py_obj,"%(type_name)s", name);    
        return %(to_c_return)s;
    }
    
    %(return_type)s py_to_%(type_name)s(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !%(check_func)s(py_obj))
            handle_bad_type(py_obj,"%(type_name)s", name);    
        %(inc_ref_count)s
        return %(to_c_return)s;
    }
};

%(type_name)s_handler x__%(type_name)s_handler = %(type_name)s_handler();
#define convert_to_%(type_name)s(py_obj,name) \\
        x__%(type_name)s_handler.convert_to_%(type_name)s(py_obj,name)
#define py_to_%(type_name)s(py_obj,name) \\
        x__%(type_name)s_handler.py_to_%(type_name)s(py_obj,name)

"""

#----------------------------------------------------------------------------
# C++ code template for converting code from C++ objects to Python objects
#
#----------------------------------------------------------------------------

simple_c_to_py_template = \
"""
PyObject* %(type_name)s_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}

"""

class common_base_converter(base_converter):
    
    def __init__(self):
        self.init_info()
        self._build_information = [self.generate_build_info()]
    
    def init_info(self):
        self.matching_types = []
        self.headers = []
        self.include_dirs = []
        self.libraries = []
        self.library_dirs = []
        self.sources = []
        self.support_code = []
        self.module_init_code = []
        self.warnings = []
        self.define_macros = []
        self.extra_compile_args = []
        self.extra_link_args = []
        self.use_ref_count = 1
        self.name = "no_name"
        self.c_type = 'PyObject*'
        self.return_type = 'PyObject*'
        self.to_c_return = 'py_obj'
    
    def info_object(self):
        return base_info.custom_info()
        
    def generate_build_info(self):
        info = self.info_object()
        for header in self.headers:
            info.add_header(header)
        for d in self.include_dirs:
            info.add_include_dir(d)
        for lib in self.libraries:
            info.add_library(lib)
        for d in self.library_dirs:
            info.add_library_dir(d)
        for source in self.sources:
            info.add_source(source)
        for code in self.support_code:
            info.add_support_code(code)
        info.add_support_code(self.py_to_c_code())
        info.add_support_code(self.c_to_py_code())
        for init_code in self.module_init_code:
            info.add_module_init_code(init_code)
        for macro in self.define_macros:
            info.add_define_macro(macro)
        for warning in self.warnings:
            info.add_warning(warning)
        for arg in self.extra_compile_args:
            info.add_extra_compile_args(arg)
        for arg in self.extra_link_args:
            info.add_extra_link_args(arg)
        return info

    def type_match(self,value):
        return type(value) in self.matching_types

    def get_var_type(self,value):
        return type(value)
        
    def type_spec(self,name,value):
        # factory
        new_spec = self.__class__()
        new_spec.name = name        
        new_spec.var_type = self.get_var_type(value)
        return new_spec

    def template_vars(self,inline=0):
        d = {}
        d['type_name'] = self.type_name
        d['check_func'] = self.check_func
        d['c_type'] = self.c_type
        d['return_type'] = self.return_type
        d['to_c_return'] = self.to_c_return
        d['name'] = self.name
        d['py_var'] = self.py_variable()
        d['var_lookup'] = self.retrieve_py_variable(inline)
        code = 'convert_to_%(type_name)s(%(py_var)s,"%(name)s")' % d
        d['var_convert'] = code
        if self.use_ref_count:
            d['inc_ref_count'] = "Py_XINCREF(py_obj);"
        else:
            d['inc_ref_count'] = ""
        return d

    def py_to_c_code(self):
        return py_to_c_template % self.template_vars()

    def c_to_py_code(self):
        return simple_c_to_py_template % self.template_vars()
        
    def declaration_code(self,templatize = 0,inline=0):
        code = '%(py_var)s = %(var_lookup)s;\n'   \
               '%(c_type)s %(name)s = %(var_convert)s;\n' %  \
               self.template_vars(inline=inline)
        return code       

    def cleanup_code(self):
        if self.use_ref_count:
            code =  'Py_XDECREF(%(py_var)s);\n' % self.template_vars()
            #code += 'printf("cleaning up %(py_var)s\\n");\n' % self.template_vars()
        else:
            code = ""    
        return code
    
    def __repr__(self):
        msg = "(file:: name: %s)" % self.name
        return msg
    def __cmp__(self,other):
        #only works for equal
        result = -1
        try:
            result = cmp(self.name,other.name) or \
                     cmp(self.__class__, other.__class__)
        except AttributeError:
            pass
        return result            

#----------------------------------------------------------------------------
# Module Converter
#----------------------------------------------------------------------------
class module_converter(common_base_converter):
    def init_info(self):
        common_base_converter.init_info(self)
        self.type_name = 'module'
        self.check_func = 'PyModule_Check'    
        # probably should test for callable classes here also.
        self.matching_types = [ModuleType]

#----------------------------------------------------------------------------
# String Converter
#----------------------------------------------------------------------------
class string_converter(common_base_converter):
    def init_info(self):
        common_base_converter.init_info(self)
        self.type_name = 'string'
        self.check_func = 'PyString_Check'    
        self.c_type = 'std::string'
        self.return_type = 'std::string'
        self.to_c_return = "std::string(PyString_AsString(py_obj))"
        self.matching_types = [StringType]
        self.headers.append('<string>')
    def c_to_py_code(self):
        # !! Need to dedent returned code.
        code = """
               PyObject* string_to_py(std::string s)
               {
                   return PyString_FromString(s.c_str());
               }
               """
        return code        

#----------------------------------------------------------------------------
# Unicode Converter
#----------------------------------------------------------------------------
class unicode_converter(common_base_converter):
    def init_info(self):
        common_base_converter.init_info(self)
        self.type_name = 'unicode'
        self.check_func = 'PyUnicode_Check'
        # This isn't supported by gcc 2.95.3 -- MSVC works fine with it.    
        #self.c_type = 'std::wstring'
        #self.to_c_return = "std::wstring(PyUnicode_AS_UNICODE(py_obj))"
        self.c_type = 'Py_UNICODE*'
        self.return_type = self.c_type
        self.to_c_return = "PyUnicode_AS_UNICODE(py_obj)"
        self.matching_types = [UnicodeType]
        #self.headers.append('<string>')
           
    def declaration_code(self,templatize = 0,inline=0):
        # since wstring doesn't seem to work everywhere, we need to provide
        # the length variable Nxxx for the unicode string xxx.
        code = '%(py_var)s = %(var_lookup)s;\n'                     \
               '%(c_type)s %(name)s = %(var_convert)s;\n'           \
               'int N%(name)s = PyUnicode_GET_SIZE(%(py_var)s);\n'  \
               % self.template_vars(inline=inline)


        return code               
#----------------------------------------------------------------------------
# File Converter
#----------------------------------------------------------------------------
class file_converter(common_base_converter):
    def init_info(self):
        common_base_converter.init_info(self)
        self.type_name = 'file'
        self.check_func = 'PyFile_Check'    
        self.c_type = 'FILE*'
        self.return_type = self.c_type
        self.to_c_return = "PyFile_AsFile(py_obj)"
        self.headers = ['<stdio.h>']
        self.matching_types = [FileType]

    def c_to_py_code(self):
        # !! Need to dedent returned code.
        code = """
               PyObject* file_to_py(FILE* file, char* name, char* mode)
               {
                   PyObject* py_obj = NULL;
                   //extern int fclose(FILE *);
                   return (PyObject*) PyFile_FromFile(file, name, mode, fclose);
               }
               """
        return code        

#----------------------------------------------------------------------------
#
# Scalar Number Conversions
#
#----------------------------------------------------------------------------

# the following typemaps are for 32 bit platforms.  A way to do this
# general case? maybe ask numeric types how long they are and base
# the decisions on that.

#----------------------------------------------------------------------------
# Standard Python numeric --> C type maps
#----------------------------------------------------------------------------
num_to_c_types = {}
num_to_c_types[type(1)]  = 'int'
num_to_c_types[type(1.)] = 'double'
num_to_c_types[type(1.+1.j)] = 'std::complex<double> '
# !! hmmm. The following is likely unsafe...
num_to_c_types[type(1L)]  = 'int'

#----------------------------------------------------------------------------
# Numeric array Python numeric --> C type maps
#----------------------------------------------------------------------------
num_to_c_types['T'] = 'T' # for templates
num_to_c_types['F'] = 'std::complex<float> '
num_to_c_types['D'] = 'std::complex<double> '
num_to_c_types['f'] = 'float'
num_to_c_types['d'] = 'double'
num_to_c_types['1'] = 'char'
num_to_c_types['b'] = 'unsigned char'
num_to_c_types['s'] = 'short'
num_to_c_types['w'] = 'unsigned short'
num_to_c_types['i'] = 'int'
num_to_c_types['u'] = 'unsigned int'

# not strictly correct, but shoulld be fine fo numeric work.
# add test somewhere to make sure long can be cast to int before using.
num_to_c_types['l'] = 'int'

class scalar_converter(common_base_converter):
    def init_info(self):
        common_base_converter.init_info(self)
        self.warnings = ['disable: 4275', 'disable: 4101']
        self.headers = ['<complex>','<math.h>']
        self.use_ref_count = 0

class int_converter(scalar_converter):
    def init_info(self):
        scalar_converter.init_info(self)
        self.type_name = 'int'
        self.check_func = 'PyInt_Check'    
        self.c_type = 'int'
        self.return_type = 'int'
        self.to_c_return = "(int) PyInt_AsLong(py_obj)"
        self.matching_types = [IntType]

class long_converter(scalar_converter):
    def init_info(self):
        scalar_converter.init_info(self)
        # !! long to int conversion isn't safe!
        self.type_name = 'long'
        self.check_func = 'PyLong_Check'    
        self.c_type = 'int'
        self.return_type = 'int'
        self.to_c_return = "(int) PyLong_AsLong(py_obj)"
        self.matching_types = [LongType]

class float_converter(scalar_converter):
    def init_info(self):
        scalar_converter.init_info(self)
        # Not sure this is really that safe...
        self.type_name = 'float'
        self.check_func = 'PyFloat_Check'    
        self.c_type = 'double'
        self.return_type = 'double'
        self.to_c_return = "PyFloat_AsDouble(py_obj)"
        self.matching_types = [FloatType]

class complex_converter(scalar_converter):
    def init_info(self):
        scalar_converter.init_info(self)
        self.type_name = 'complex'
        self.check_func = 'PyComplex_Check'    
        self.c_type = 'std::complex<double>'
        self.return_type = 'std::complex<double>'
        self.to_c_return = "std::complex<double>(PyComplex_RealAsDouble(py_obj),"\
                                                "PyComplex_ImagAsDouble(py_obj))"
        self.matching_types = [ComplexType]

#----------------------------------------------------------------------------
#
# List, Tuple, and Dict converters.
#
# Based on SCXX by Gordon McMillan
#----------------------------------------------------------------------------
import os, c_spec # yes, I import myself to find out my __file__ location.
local_dir,junk = os.path.split(os.path.abspath(c_spec.__file__))   
scxx_dir = os.path.join(local_dir,'scxx')

class scxx_converter(common_base_converter):
    def init_info(self):
        common_base_converter.init_info(self)
        self.headers = ['"scxx/object.h"','"scxx/list.h"','"scxx/tuple.h"',
                        '"scxx/dict.h"','<iostream>']
        self.include_dirs = [local_dir,scxx_dir]
        self.sources = [os.path.join(scxx_dir,'weave_imp.cpp'),]

class list_converter(scxx_converter):
    def init_info(self):
        scxx_converter.init_info(self)
        self.type_name = 'list'
        self.check_func = 'PyList_Check'    
        self.c_type = 'py::list'
        self.return_type = 'py::list'
        self.to_c_return = 'py::list(py_obj)'
        self.matching_types = [ListType]
        # ref counting handled by py::list
        self.use_ref_count = 0

class tuple_converter(scxx_converter):
    def init_info(self):
        scxx_converter.init_info(self)
        self.type_name = 'tuple'
        self.check_func = 'PyTuple_Check'    
        self.c_type = 'py::tuple'
        self.return_type = 'py::tuple'
        self.to_c_return = 'py::tuple(py_obj)'
        self.matching_types = [TupleType]
        # ref counting handled by py::tuple
        self.use_ref_count = 0

class dict_converter(scxx_converter):
    def init_info(self):
        scxx_converter.init_info(self)
        self.type_name = 'dict'
        self.check_func = 'PyDict_Check'    
        self.c_type = 'py::dict'
        self.return_type = 'py::dict'
        self.to_c_return = 'py::dict(py_obj)'
        self.matching_types = [DictType]
        # ref counting handled by py::dict
        self.use_ref_count = 0

#----------------------------------------------------------------------------
# Instance Converter
#----------------------------------------------------------------------------
class instance_converter(scxx_converter):
    def init_info(self):
        scxx_converter.init_info(self)
        self.type_name = 'instance'
        self.check_func = 'PyInstance_Check'    
        self.c_type = 'py::object'
        self.return_type = 'py::object'
        self.to_c_return = 'py::object(py_obj)'
        self.matching_types = [InstanceType]
        # ref counting handled by py::object
        self.use_ref_count = 0

#----------------------------------------------------------------------------
# Catchall Converter
#
# catch all now handles callable objects
#----------------------------------------------------------------------------
class catchall_converter(scxx_converter):
    def init_info(self):
        scxx_converter.init_info(self)
        self.type_name = 'catchall'
        self.check_func = ''    
        self.c_type = 'py::object'
        self.return_type = 'py::object'
        self.to_c_return = 'py::object(py_obj)'
        # ref counting handled by py::object
        self.use_ref_count = 0
    def type_match(self,value):
        return 1

if __name__ == "__main__":
    x = list_converter().type_spec("x",1)
    print x.py_to_c_code()
    print
    print x.c_to_py_code()
    print
    print x.declaration_code(inline=1)
    print
    print x.cleanup_code()

import parser
import string
import copy
import os,sys
import ast_tools
import token,symbol
import slice_handler
import size_check
import converters

from ast_tools import *

from Numeric import *
# The following try/except so that non-SciPy users can still use blitz
try:
    from scipy_base.fastumath import *
except:
    pass # scipy_base.fastumath not available    
    
from types import *

import inline_tools
from inline_tools import attempt_function_call
function_catalog = inline_tools.function_catalog
function_cache = inline_tools.function_cache
  
def blitz(expr,local_dict=None, global_dict=None,check_size=1,verbose=0,**kw):
    # this could call inline, but making a copy of the
    # code here is more efficient for several reasons.
    global function_catalog
          
    # this grabs the local variables from the *previous* call
    # frame -- that is the locals from the function that called
    # inline.
    call_frame = sys._getframe().f_back
    if local_dict is None:
        local_dict = call_frame.f_locals
    if global_dict is None:
        global_dict = call_frame.f_globals

    # 1. Check the sizes of the arrays and make sure they are compatible.
    #    This is expensive, so unsetting the check_size flag can save a lot
    #    of time.  It also can cause core-dumps if the sizes of the inputs 
    #    aren't compatible.    
    if check_size and not size_check.check_expr(expr,local_dict,global_dict):
        raise 'inputs failed to pass size check.'
    
    # 2. try local cache    
    try:
        results = apply(function_cache[expr],(local_dict,global_dict))
        return results
    except: 
        pass
    try:
        results = attempt_function_call(expr,local_dict,global_dict)
    # 3. build the function    
    except ValueError:
        # This section is pretty much the only difference 
        # between blitz and inline
        ast = parser.suite(expr)
        ast_list = ast.tolist()
        expr_code = ast_to_blitz_expr(ast_list)
        arg_names = harvest_variables(ast_list)
        module_dir = global_dict.get('__file__',None)
        #func = inline_tools.compile_function(expr_code,arg_names,
        #                                    local_dict,global_dict,
        #                                    module_dir,auto_downcast = 1)
        func = inline_tools.compile_function(expr_code,arg_names,local_dict,        
                                             global_dict,module_dir,
                                             compiler='gcc',auto_downcast=1,
                                             verbose = verbose,
                                             type_converters = converters.blitz,
                                             **kw)
        function_catalog.add_function(expr,func,module_dir)
        try:                                            
            results = attempt_function_call(expr,local_dict,global_dict)
        except ValueError:                                                
            print 'warning: compilation failed. Executing as python code'
            exec expr in global_dict, local_dict
            
def ast_to_blitz_expr(ast_seq):
    """ Convert an ast_sequence to a blitz expression.
    """
    
    # Don't overwrite orignal sequence in call to transform slices.
    ast_seq = copy.deepcopy(ast_seq)    
    slice_handler.transform_slices(ast_seq)
    
    # Build the actual program statement from ast_seq
    expr = ast_tools.ast_to_string(ast_seq)
    
    # Now find and replace specific symbols to convert this to
    # a blitz++ compatible statement.
    # I'm doing this with string replacement here.  It could
    # also be done on the actual ast tree (and probably should from
    # a purest standpoint...).
    
    # this one isn't necessary but it helps code readability
    # and compactness. It requires that 
    #   Range _all = blitz::Range::all();
    # be included in the generated code.    
    # These could all alternatively be done to the ast in
    # build_slice_atom()
    expr = string.replace(expr,'slice(_beg,_end)', '_all' )    
    expr = string.replace(expr,'slice', 'blitz::Range' )
    expr = string.replace(expr,'[','(')
    expr = string.replace(expr,']', ')' )
    expr = string.replace(expr,'_stp', '1' )
    
    # Instead of blitz::fromStart and blitz::toEnd.  This requires
    # the following in the generated code.
    #   Range _beg = blitz::fromStart;
    #   Range _end = blitz::toEnd;
    #expr = string.replace(expr,'_beg', 'blitz::fromStart' )
    #expr = string.replace(expr,'_end', 'blitz::toEnd' )
    
    return expr + ';\n'

def test_function():
    expr = "ex[:,1:,1:] = k +  ca_x[:,1:,1:] * ex[:,1:,1:]" \
                         "+ cb_y_x[:,1:,1:] * (hz[:,1:,1:] - hz[:,:-1,1:])"\
                         "- cb_z_x[:,1:,1:] * (hy[:,1:,1:] - hy[:,1:,:-1])"        
    #ast = parser.suite('a = (b + c) * sin(d)')
    ast = parser.suite(expr)
    k = 1.
    ex = ones((1,1,1),typecode=Float32)
    ca_x = ones((1,1,1),typecode=Float32)
    cb_y_x = ones((1,1,1),typecode=Float32)
    cb_z_x = ones((1,1,1),typecode=Float32)
    hz = ones((1,1,1),typecode=Float32)
    hy = ones((1,1,1),typecode=Float32)
    blitz(expr)

"""
    build_info holds classes that define the information
    needed for building C++ extension modules for Python that
    handle different data types.  The information includes
    such as include files, libraries, and even code snippets.
       
    array_info -- for building functions that use Python
                  Numeric arrays.
"""

import base_info
import standard_array_spec
from Numeric import *
from types import *
import os

blitz_support_code =  \
"""

// This should be declared only if they are used by some function
// to keep from generating needless warnings. for now, we'll always
// declare them.

int _beg = blitz::fromStart;
int _end = blitz::toEnd;
blitz::Range _all = blitz::Range::all();

template<class T, int N>
static blitz::Array<T,N> convert_to_blitz(PyArrayObject* arr_obj,const char* name)
{    
    blitz::TinyVector<int,N> shape(0);
    blitz::TinyVector<int,N> strides(0);
    int stride_acc = 1;
    //for (int i = N-1; i >=0; i--)
    for (int i = 0; i < N; i++)
    {
        shape[i] = arr_obj->dimensions[i];
        strides[i] = arr_obj->strides[i]/sizeof(T);
    }
    //return blitz::Array<T,N>((T*) arr_obj->data,shape,        
    return blitz::Array<T,N>((T*) arr_obj->data,shape,strides,
                             blitz::neverDeleteData);
}

template<class T, int N>
static blitz::Array<T,N> py_to_blitz(PyArrayObject* arr_obj,const char* name)
{
    
    blitz::TinyVector<int,N> shape(0);
    blitz::TinyVector<int,N> strides(0);
    int stride_acc = 1;
    //for (int i = N-1; i >=0; i--)
    for (int i = 0; i < N; i++)
    {
        shape[i] = arr_obj->dimensions[i];
        strides[i] = arr_obj->strides[i]/sizeof(T);
    }
    //return blitz::Array<T,N>((T*) arr_obj->data,shape,        
    return blitz::Array<T,N>((T*) arr_obj->data,shape,strides,
                             blitz::neverDeleteData);
}
"""

import os, blitz_spec
local_dir,junk = os.path.split(os.path.abspath(blitz_spec.__file__))   
blitz_dir = os.path.join(local_dir,'blitz-20001213')

# The need to warn about compilers made the info_object method in
# converters necessary and also this little class necessary.  
# The spec/info unification needs to continue so that this can 
# incorporated into the spec somehow.

class array_info(base_info.custom_info):    
    # throw error if trying to use msvc compiler
    
    def check_compiler(self,compiler):        
        msvc_msg = 'Unfortunately, the blitz arrays used to support numeric' \
                   ' arrays will not compile with MSVC.' \
                   '  Please try using mingw32 (www.mingw.org).'
        if compiler == 'msvc':
            return ValueError, self.msvc_msg        


class array_converter(standard_array_spec.array_converter):
    def init_info(self):
        standard_array_spec.array_converter.init_info(self)
        blitz_headers = ['"blitz/array.h"','"Numeric/arrayobject.h"',
                          '<complex>','<math.h>']
        self.headers.extend(blitz_headers)
        self.include_dirs = [blitz_dir]
        self.support_code.append(blitz_support_code)
        
        # type_name is used to setup the initial type conversion.  Even
        # for blitz conversion, the first step is to convert it to a
        # standard numpy array.
        #self.type_name = 'blitz'
        self.type_name = 'numpy'
        
    def info_object(self):
        return array_info()

    def type_spec(self,name,value):
        new_spec = standard_array_spec.array_converter.type_spec(self,name,value)
        new_spec.dims = len(value.shape)
        if new_spec.dims > 11:
            msg = "Error converting variable '" + name + "'.  " \
                  "blitz only supports arrays up to 11 dimensions."
            raise ValueError, msg
        return new_spec

    def template_vars(self,inline=0):
        res = standard_array_spec.array_converter.template_vars(self,inline)    
        if hasattr(self,'dims'):
            res['dims'] = self.dims
        return res    

    def declaration_code(self,templatize = 0,inline=0):
        code = '%(py_var)s = %(var_lookup)s;\n'   \
               '%(c_type)s %(array_name)s = %(var_convert)s;\n'  \
               'conversion_numpy_check_type(%(array_name)s,%(num_typecode)s,"%(name)s");\n' \
               'conversion_numpy_check_size(%(array_name)s,%(dims)s,"%(name)s");\n' \
               'blitz::Array<%(num_type)s,%(dims)d> %(name)s =' \
               ' convert_to_blitz<%(num_type)s,%(dims)d>(%(array_name)s,"%(name)s");\n' \
               'blitz::TinyVector<int,%(dims)d> N%(name)s = %(name)s.shape();\n'
        code = code % self.template_vars(inline=inline)
        return code

    def __cmp__(self,other):
        #only works for equal
        return ( cmp(self.name,other.name) or  
                 cmp(self.var_type,other.var_type) or 
                 cmp(self.dims, other.dims) or 
                 cmp(self.__class__, other.__class__) )


class base_converter:
    """
        Properties:
        headers --  list of strings that name the header files needed by this
                    object.
        include_dirs -- list of directories where the header files can be found.
        libraries   -- list of libraries needed to link to when compiling
                       extension.
        library_dirs -- list of directories to search for libraries.

        support_code -- list of strings.  Each string is a subroutine needed
                        by the type.  Functions that are used in the conversion
                        between Python and C++ files are examples of these.

        Methods:

        type_match(value) returns 1 if this class is used to represent type
                          specification for value.
        type_spec(name, value)  returns a new object (of this class) that is
                                used to produce C++ code for value.
        declaration_code()    returns C++ code fragment for type declaration and
                              conversion of python object to C++ object.
        cleanup_code()    returns C++ code fragment for cleaning up after the
                          variable after main C++ code fragment has executed.

    """
    _build_information = []
    compiler = ''   
                
    def set_compiler(self,compiler):
        self.compiler = compiler
    def type_match(self,value):
        raise NotImplementedError, "You must override method in derived class"
    def build_information(self):
        return self._build_information
    def type_spec(self,name,value): 
        pass
    def declaration_code(self,templatize = 0):   
        return ""
    def local_dict_code(self): 
        return ""
    def cleanup_code(self): 
        return ""
    def retrieve_py_variable(self,inline=0):
        # this needs a little coordination in name choices with the
        # ext_inline_function class.
        if inline:
            vn = 'get_variable("%s",raw_locals,raw_globals)' % self.name
        else:
            vn = 'py_' + self.name   
        return vn
        
    def py_reference(self):
        return "&py_" + self.name
    def py_pointer(self):
        return "*py_" + self.name
    def py_variable(self):
        return "py_" + self.name
    def reference(self):
        return "&" + self.name
    def pointer(self):
        return "*" + self.name
    def init_flag(self):
        return self.name + "_used"
    
    def variable(self):
        return self.name
    def variable_as_string(self):
        return '"' + self.name + '"'

import UserList
import base_info

class arg_spec_list(UserList.UserList):    
    def build_information(self): 
        all_info = base_info.info_list()
        for i in self:
            all_info.extend(i.build_information())
        return all_info
        
    def py_references(self): 
        return map(lambda x: x.py_reference(),self)
    def py_pointers(self): 
        return map(lambda x: x.py_pointer(),self)
    def py_variables(self): 
        return map(lambda x: x.py_variable(),self)

    def references(self): 
        return map(lambda x: x.py_reference(),self)
    def pointers(self): 
        return map(lambda x: x.pointer(),self)    
    def variables(self): 
        return map(lambda x: x.variable(),self)
    def init_flags(self): 
        return map(lambda x: x.init_flag(),self)
    def variable_as_strings(self): 
        return map(lambda x: x.variable_as_string(),self)

    
"""
C/C++ integration
=================

        1. inline() -- a function for including C/C++ code within Python
        2. blitz()  -- a function for compiling Numeric expressions to C++
        3. ext_tools-- a module that helps construct C/C++ extension modules.
        4. accelerate -- a module that inline accelerates Python functions
"""
postpone_import = 1
standalone = 1

# should re-write compiled functions to take a local and global dict
# as input.
import sys,os
import ext_tools
import string
import catalog
import common_info

# not an easy way for the user_path_list to come in here.
# the PYTHONCOMPILED environment variable offers the most hope.

function_catalog = catalog.catalog()


class inline_ext_function(ext_tools.ext_function):
    # Some specialization is needed for inline extension functions
    def function_declaration_code(self):
       code  = 'static PyObject* %s(PyObject*self, PyObject* args)\n{\n'
       return code % self.name

    def template_declaration_code(self):
        code = 'template<class T>\n' \
               'static PyObject* %s(PyObject*self, PyObject* args)\n{\n'
        return code % self.name

    def parse_tuple_code(self):
        """ Create code block for PyArg_ParseTuple.  Variable declarations
            for all PyObjects are done also.

            This code got a lot uglier when I added local_dict...
        """
        declare_return = 'py::object return_val;\n'    \
                         'int exception_occured = 0;\n'    \
                         'PyObject *py__locals = NULL;\n' \
                         'PyObject *py__globals = NULL;\n'

        py_objects = ', '.join(self.arg_specs.py_pointers())
        if py_objects:
            declare_py_objects = 'PyObject ' + py_objects +';\n'
        else:
            declare_py_objects = ''

        py_vars = ' = '.join(self.arg_specs.py_variables())
        if py_vars:
            init_values = py_vars + ' = NULL;\n\n'
        else:
            init_values = ''

        parse_tuple = 'if(!PyArg_ParseTuple(args,"OO:compiled_func",'\
                                           '&py__locals,'\
                                           '&py__globals))\n'\
                      '    return NULL;\n'

        return   declare_return + declare_py_objects + \
                 init_values + parse_tuple

    def arg_declaration_code(self):
        arg_strings = []
        for arg in self.arg_specs:
            arg_strings.append(arg.declaration_code(inline=1))
        code = string.join(arg_strings,"")
        return code

    def arg_cleanup_code(self):
        arg_strings = []
        for arg in self.arg_specs:
            arg_strings.append(arg.cleanup_code())
        code = string.join(arg_strings,"")
        return code

    def arg_local_dict_code(self):
        arg_strings = []
        for arg in self.arg_specs:
            arg_strings.append(arg.local_dict_code())
        code = string.join(arg_strings,"")
        return code


    def function_code(self):
        from ext_tools import indent
        decl_code = indent(self.arg_declaration_code(),4)
        cleanup_code = indent(self.arg_cleanup_code(),4)
        function_code = indent(self.code_block,4)
        #local_dict_code = indent(self.arg_local_dict_code(),4)

        try_code =    'try                              \n' \
                      '{                                \n' \
                      '    PyObject* raw_locals = py_to_raw_dict('       \
                                             'py__locals,"_locals");\n'  \
                      '    PyObject* raw_globals = py_to_raw_dict('      \
                                          'py__globals,"_globals");\n' + \
                      '    /* argument conversion code */     \n' + \
                           decl_code                               + \
                      '    /* inline code */                   \n' + \
                           function_code                           + \
                      '    /*I would like to fill in changed    '   \
                              'locals and globals here...*/   \n'   \
                      '\n}                                       \n'
        catch_code =  "catch(...)                        \n"   \
                      "{                                 \n" + \
                      "    return_val =  py::object();   \n"   \
                      "    exception_occured = 1;        \n"   \
                      "}                                 \n"   
        return_code = "    /* cleanup code */                   \n" + \
                           cleanup_code                             + \
                      "    if(!(PyObject*)return_val && !exception_occured)\n"   \
                      "    {\n                                  \n"   \
                      "        return_val = Py_None;            \n"   \
                      "    }\n                                  \n"   \
                      "    return return_val.disown();          \n"           \
                      "}                                \n"

        all_code = self.function_declaration_code()         + \
                       indent(self.parse_tuple_code(),4)    + \
                       indent(try_code,4)                   + \
                       indent(catch_code,4)                 + \
                       return_code

        return all_code

    def python_function_definition_code(self):
        args = (self.name, self.name)
        function_decls = '{"%s",(PyCFunction)%s , METH_VARARGS},\n' % args
        return function_decls

class inline_ext_module(ext_tools.ext_module):
    def __init__(self,name,compiler=''):
        ext_tools.ext_module.__init__(self,name,compiler)
        self._build_information.append(common_info.inline_info())

function_cache = {}
def inline(code,arg_names=[],local_dict = None, global_dict = None,
           force = 0,
           compiler='',
           verbose = 0,
           support_code = None,
           headers = [],
           customize=None,
           type_converters = None,
           auto_downcast=1,
           **kw):
    """ Inline C/C++ code within Python scripts.

        inline() compiles and executes C/C++ code on the fly.  Variables
        in the local and global Python scope are also available in the
        C/C++ code.  Values are passed to the C/C++ code by assignment
        much like variables passed are passed into a standard Python
        function.  Values are returned from the C/C++ code through a
        special argument called return_val.  Also, the contents of
        mutable objects can be changed within the C/C++ code and the
        changes remain after the C code exits and returns to Python.

        inline has quite a few options as listed below.  Also, the keyword
        arguments for distutils extension modules are accepted to
        specify extra information needed for compiling.

        code -- string. A string of valid C++ code.  It should not specify a
                return statement.  Instead it should assign results that
                need to be returned to Python in the return_val.
        arg_names -- optional. list of strings. A list of Python variable names 
                     that should be transferred from Python into the C/C++ 
                     code.  It defaults to an empty string.
        local_dict -- optional. dictionary. If specified, it is a dictionary
                      of values that should be used as the local scope for the
                      C/C++ code.  If local_dict is not specified the local
                      dictionary of the calling function is used.
        global_dict -- optional. dictionary.  If specified, it is a dictionary
                       of values that should be used as the global scope for
                       the C/C++ code.  If global_dict is not specified the
                       global dictionary of the calling function is used.
        force --      optional. 0 or 1. default 0.  If 1, the C++ code is
                      compiled every time inline is called.  This is really
                      only useful for debugging, and probably only useful if
                      your editing support_code a lot.
        compiler --   optional. string.  The name of compiler to use when
                      compiling.  On windows, it understands 'msvc' and 'gcc'
                      as well as all the compiler names understood by
                      distutils.  On Unix, it'll only understand the values
                      understoof by distutils. ( I should add 'gcc' though
                      to this).

                      On windows, the compiler defaults to the Microsoft C++
                      compiler.  If this isn't available, it looks for mingw32
                      (the gcc compiler).

                      On Unix, it'll probably use the same compiler that was
                      used when compiling Python. Cygwin's behavior should be
                      similar.
        verbose --    optional. 0,1, or 2. defualt 0.  Speficies how much
                      much information is printed during the compile phase
                      of inlining code.  0 is silent (except on windows with
                      msvc where it still prints some garbage). 1 informs
                      you when compiling starts, finishes, and how long it
                      took.  2 prints out the command lines for the compilation
                      process and can be useful if your having problems
                      getting code to work.  Its handy for finding the name
                      of the .cpp file if you need to examine it.  verbose has
                      no affect if the compilation isn't necessary.
        support_code -- optional. string.  A string of valid C++ code declaring
                        extra code that might be needed by your compiled
                        function.  This could be declarations of functions,
                        classes, or structures.
        headers      -- optional. list of strings.  A list of strings specifying
                        header files to use when compiling the code.  The list 
                        might look like ["<vector>","'my_header'"].  Note that 
                        the header strings need to be in a form than can be 
                        pasted at the end of a #include statement in the 
                        C++ code.
        customize --   optional. base_info.custom_info object. An alternative
                       way to specifiy support_code, headers, etc. needed by
                       the function see the compiler.base_info module for more
                       details. (not sure this'll be used much).
        type_converters -- optional. list of type converters. These
                          guys are what convert Python data types to C/C++ data
                          types.  If you'd like to use a different set of type
                          conversions than the default, specify them here. Look
                          in the type conversions section of the main
                          documentation for examples.
        auto_downcast -- optional. 0 or 1. default 1.  This only affects
                         functions that have Numeric arrays as input variables.
                         Setting this to 1 will cause all floating point values
                         to be cast as float instead of double if all the
                         Numeric arrays are of type float.  If even one of the
                         arrays has type double or double complex, all
                         variables maintain there standard types.

        Distutils keywords.  These are cut and pasted from Greg Ward's
        distutils.extension.Extension class for convenience:

        sources : [string]
          list of source filenames, relative to the distribution root
          (where the setup script lives), in Unix form (slash-separated)
          for portability.  Source files may be C, C++, SWIG (.i),
          platform-specific resource files, or whatever else is recognized
          by the "build_ext" command as source for a Python extension.
          Note: The module_path file is always appended to the front of this
                list
        include_dirs : [string]
          list of directories to search for C/C++ header files (in Unix
          form for portability)
        define_macros : [(name : string, value : string|None)]
          list of macros to define; each macro is defined using a 2-tuple,
          where 'value' is either the string to define it to or None to
          define it without a particular value (equivalent of "#define
          FOO" in source or -DFOO on Unix C compiler command line)
        undef_macros : [string]
          list of macros to undefine explicitly
        library_dirs : [string]
          list of directories to search for C/C++ libraries at link time
        libraries : [string]
          list of library names (not filenames or paths) to link against
        runtime_library_dirs : [string]
          list of directories to search for C/C++ libraries at run time
          (for shared extensions, this is when the extension is loaded)
        extra_objects : [string]
          list of extra files to link with (eg. object files not implied
          by 'sources', static library that must be explicitly specified,
          binary resource files, etc.)
        extra_compile_args : [string]
          any extra platform- and compiler-specific information to use
          when compiling the source files in 'sources'.  For platforms and
          compilers where "command line" makes sense, this is typically a
          list of command-line arguments, but for other platforms it could
          be anything.
        extra_link_args : [string]
          any extra platform- and compiler-specific information to use
          when linking object files together to create the extension (or
          to create a new static Python interpreter).  Similar
          interpretation as for 'extra_compile_args'.
        export_symbols : [string]
          list of symbols to be exported from a shared extension.  Not
          used on all platforms, and not generally necessary for Python
          extensions, which typically export exactly one symbol: "init" +
          extension_name.
    """
    # this grabs the local variables from the *previous* call
    # frame -- that is the locals from the function that called
    # inline.
    global function_catalog

    call_frame = sys._getframe().f_back
    if local_dict is None:
        local_dict = call_frame.f_locals
    if global_dict is None:
        global_dict = call_frame.f_globals
    if force:
        module_dir = global_dict.get('__file__',None)
        func = compile_function(code,arg_names,local_dict,
                                global_dict,module_dir,
                                compiler=compiler,
                                verbose=verbose,
                                support_code = support_code,
                                headers = headers,
                                customize=customize,
                                type_converters = type_converters,
                                auto_downcast = auto_downcast,
                                **kw)

        function_catalog.add_function(code,func,module_dir)
        results = attempt_function_call(code,local_dict,global_dict)
    else:
        # 1. try local cache
        try:
            results = apply(function_cache[code],(local_dict,global_dict))
            return results
        except TypeError, msg: 
            msg = str(msg).strip()
            if msg[:16] == "Conversion Error":
                pass
            else:
                raise TypeError, msg
        except NameError, msg: 
            msg = str(msg).strip()
            if msg[:16] == "Conversion Error":
                pass
            else:
                raise NameError, msg
        except KeyError:
            pass
        # 2. try function catalog
        try:
            results = attempt_function_call(code,local_dict,global_dict)
        # 3. build the function
        except ValueError:
            # compile the library
            module_dir = global_dict.get('__file__',None)
            func = compile_function(code,arg_names,local_dict,
                                    global_dict,module_dir,
                                    compiler=compiler,
                                    verbose=verbose,
                                    support_code = support_code,
                                    headers = headers,
                                    customize=customize,
                                    type_converters = type_converters,
                                    auto_downcast = auto_downcast,
                                    **kw)

            function_catalog.add_function(code,func,module_dir)
            results = attempt_function_call(code,local_dict,global_dict)
    return results

def attempt_function_call(code,local_dict,global_dict):
    # we try 3 levels here -- a local cache first, then the
    # catalog cache, and then persistent catalog.
    #
    global function_cache
    # 2. try catalog cache.
    function_list = function_catalog.get_functions_fast(code)
    for func in function_list:
        try:
            results = apply(func,(local_dict,global_dict))
            function_catalog.fast_cache(code,func)
            function_cache[code] = func
            return results
        except TypeError, msg: # should specify argument types here.
            # This should really have its own error type, instead of
            # checking the beginning of the message, but I don't know
            # how to define that yet.
            msg = str(msg)
            if msg[:16] == "Conversion Error":
                pass
            else:
                raise TypeError, msg
        except NameError, msg: 
            msg = str(msg).strip()
            if msg[:16] == "Conversion Error":
                pass
            else:
                raise NameError, msg                
    # 3. try persistent catalog
    module_dir = global_dict.get('__file__',None)
    function_list = function_catalog.get_functions(code,module_dir)
    for func in function_list:
        try:
            results = apply(func,(local_dict,global_dict))
            function_catalog.fast_cache(code,func)
            function_cache[code] = func
            return results
        except: # should specify argument types here.
            pass
    # if we get here, the function wasn't found
    raise ValueError, 'function with correct signature not found'

def inline_function_code(code,arg_names,local_dict=None,
                         global_dict=None,auto_downcast = 1,
                         type_converters=None,compiler=''):
    call_frame = sys._getframe().f_back
    if local_dict is None:
        local_dict = call_frame.f_locals
    if global_dict is None:
        global_dict = call_frame.f_globals
    ext_func = inline_ext_function('compiled_func',code,arg_names,
                                   local_dict,global_dict,auto_downcast,
                                   type_converters = type_converters)
    import build_tools
    compiler = build_tools.choose_compiler(compiler)
    ext_func.set_compiler(compiler)
    return ext_func.function_code()

def compile_function(code,arg_names,local_dict,global_dict,
                     module_dir,
                     compiler='',
                     verbose = 0,
                     support_code = None,
                     headers = [],
                     customize = None,
                     type_converters = None,
                     auto_downcast=1,
                     **kw):
    # figure out where to store and what to name the extension module
    # that will contain the function.
    #storage_dir = catalog.intermediate_dir()
    module_path = function_catalog.unique_module_name(code,module_dir)
    storage_dir, module_name = os.path.split(module_path)
    mod = inline_ext_module(module_name,compiler)

    # create the function.  This relies on the auto_downcast and
    # type factories setting
    ext_func = inline_ext_function('compiled_func',code,arg_names,
                                   local_dict,global_dict,auto_downcast,
                                   type_converters = type_converters)
    mod.add_function(ext_func)

    # if customize (a custom_info object), then set the module customization.
    if customize:
        mod.customize = customize

    # add the extra "support code" needed by the function to the module.
    if support_code:
        mod.customize.add_support_code(support_code)
    
    # add the extra headers needed by the function to the module.
    for header in headers:
        mod.customize.add_header(header)
        
    # compile code in correct location, with the given compiler and verbosity
    # setting.  All input keywords are passed through to distutils
    mod.compile(location=storage_dir,compiler=compiler,
                verbose=verbose, **kw)

    # import the module and return the function.  Make sure
    # the directory where it lives is in the python path.
    try:
        sys.path.insert(0,storage_dir)
        exec 'import ' + module_name
        func = eval(module_name+'.compiled_func')
    finally:
        del sys.path[0]
    return func


"""
This module allows one to use SWIG2 (SWIG version >= 1.3) wrapped
objects from Weave.  SWIG-1.3 wraps objects differently from SWIG-1.1.

The code here is based on wx_spec.py.  However, this module is more
like a template for any SWIG2 wrapped converter.  To wrap specific
code that uses SWIG the user simply needs to override the defaults in
the swig2_converter class.

By default this code assumes that the user will not link with the SWIG
runtime library (libswigpy under *nix).  In this case no type checking
will be performed by SWIG.

To turn on type checking and link with the SWIG runtime library, there
are two approaches.

 1. If you are writing a customized converter based on this code then
    in the overloaded init_info, just call swig2_converter.init_info
    with runtime=1 and add the swig runtime library to the libraries
    loaded.

 2. If you are using the default swig2_converter you need to add two
    keyword arguments to your weave.inline call:

     a. Add a define_macros=[('SWIG_NOINCLUDE', None)]

     b. Add the swigpy library to the libraries like so:
        libraries=['swigpy']

Prabhu Ramachandran <prabhu@aero.iitm.ernet.in>
"""

import common_info
from c_spec import common_base_converter
import converters
import swigptr2

#----------------------------------------------------------------------
# This code obtains the C++ pointer given a a SWIG2 wrapped C++ object
# in Python.
#----------------------------------------------------------------------

swig2_py_to_c_template = \
"""
class %(type_name)s_handler
{
public:    
    %(c_type)s convert_to_%(type_name)s(PyObject* py_obj, const char* name)
    {
        %(c_type)s c_ptr;
        swig_type_info *ty = SWIG_TypeQuery("%(c_type)s");
        // work on this error reporting...
        if (SWIG_ConvertPtr(py_obj, (void **) &c_ptr, ty,
            SWIG_POINTER_EXCEPTION | 0) == -1) {
            handle_conversion_error(py_obj,"%(type_name)s", name);
        }
        %(inc_ref_count)s
        return c_ptr;
    }
    
    %(c_type)s py_to_%(type_name)s(PyObject* py_obj,const char* name)
    {
        %(c_type)s c_ptr;
        swig_type_info *ty = SWIG_TypeQuery("%(c_type)s");
        // work on this error reporting...
        if (SWIG_ConvertPtr(py_obj, (void **) &c_ptr, ty,
            SWIG_POINTER_EXCEPTION | 0) == -1) {
            handle_bad_type(py_obj,"%(type_name)s", name);
        }
        %(inc_ref_count)s
        return c_ptr;
    }
};

%(type_name)s_handler x__%(type_name)s_handler = %(type_name)s_handler();
#define convert_to_%(type_name)s(py_obj,name) \\
        x__%(type_name)s_handler.convert_to_%(type_name)s(py_obj,name)
#define py_to_%(type_name)s(py_obj,name) \\
        x__%(type_name)s_handler.py_to_%(type_name)s(py_obj,name)

"""

#----------------------------------------------------------------------
# This code generates a new SWIG pointer object given a C++ pointer.
#
# Important note: The thisown flag of the returned object is set to 0
# by default.
#----------------------------------------------------------------------

swig2_c_to_py_template = """
PyObject* %(type_name)s_to_py(void *obj)
{
    swig_type_info *ty = SWIG_TypeQuery("%(c_type)s");
    return SWIG_NewPointerObj(obj, ty, 0);
}
"""

class swig2_converter(common_base_converter):
    """ A converter for SWIG >= 1.3 wrapped objects."""
    def __init__(self,class_name="undefined"):
        self.class_name = class_name
        common_base_converter.__init__(self)

    def init_info(self, runtime=0):
        """Keyword arguments:
        
          runtime -- If false (default), the user does not need to
          link to the swig runtime (libswipy).  In this case no SWIG
          type checking is performed.  If true, the user must link to
          the swipy runtime library and in this case type checking
          will be performed.  This option is useful when you derive a
          subclass of this one for your object converters.          
        """
        common_base_converter.init_info(self)
        # These are generated on the fly instead of defined at 
        # the class level.
        self.type_name = self.class_name
        self.c_type = self.class_name + "*"
        self.return_type = self.class_name + "*"
        self.to_c_return = None # not used
        self.check_func = None # not used

        if runtime:
            self.define_macros.append(("SWIG_NOINCLUDE", None))
        self.support_code.append(swigptr2.swigptr2_code)
    
    def type_match(self,value):        
        """ This is a generic type matcher for SWIG-1.3 objects.  For
        specific instances, override this function."""
        is_match = 0
        try:
            data = value.this.split('_')
            if data[2] == 'p':
                is_match = 1
        except AttributeError:
            pass
        return is_match

    def generate_build_info(self):
        if self.class_name != "undefined":
            res = common_base_converter.generate_build_info(self)
        else:
            # if there isn't a class_name, we don't want the
            # support_code to be included
            import base_info
            res = base_info.base_info()
        return res
        
    def py_to_c_code(self):
        return swig2_py_to_c_template % self.template_vars()

    def c_to_py_code(self):
        return swig2_c_to_py_template % self.template_vars()
                    
    def type_spec(self,name,value):
        """ This returns a generic type converter for SWIG-1.3
        objects.  For specific instances, override this function if
        necessary."""        
        # factory
        class_name = value.this.split('_')[-1]
        new_spec = self.__class__(class_name)
        new_spec.name = name        
        return new_spec

    def __cmp__(self,other):
        #only works for equal
        res = -1
        try:
            res = cmp(self.name,other.name) or \
                  cmp(self.__class__, other.__class__) or \
                  cmp(self.class_name, other.class_name) or \
                  cmp(self.type_name,other.type_name)
        except:
            pass
        return res

#----------------------------------------------------------------------
# Uncomment the next line if you want this to be a default converter
# that is magically invoked by inline.
#----------------------------------------------------------------------
#converters.default.insert(0, swig2_converter())

major = 0
minor = 3
micro = 1
#release_level = 'alpha'
release_level = ''
try:
    from __cvs_version__ import cvs_version
    cvs_minor = cvs_version[-3]
    cvs_serial = cvs_version[-1]
except ImportError,msg:
    print msg
    cvs_minor = 0
    cvs_serial = 0

if release_level:
    weave_version = '%(major)d.%(minor)d.%(micro)d_%(release_level)s'\
                    '_%(cvs_minor)d.%(cvs_serial)d' % (locals ())
else:
    weave_version = '%(major)d.%(minor)d.%(micro)d'\
                    '_%(cvs_minor)d.%(cvs_serial)d' % (locals ())

from shelve import Shelf
import zlib
from cStringIO import  StringIO
import  cPickle  
import dumbdbm_patched

class DbfilenameShelf(Shelf):
    """Shelf implementation using the "anydbm" generic dbm interface.

    This is initialized with the filename for the dbm database.
    See the module's __doc__ string for an overview of the interface.
    """
    
    def __init__(self, filename, flag='c'):
        Shelf.__init__(self, dumbdbm_patched.open(filename, flag))

    def __getitem__(self, key):
        compressed = self.dict[key]
        try:
            r = zlib.decompress(compressed)
        except zlib.error:
            r = compressed
        return cPickle.loads(r) 
        
    def __setitem__(self, key, value):
        s = cPickle.dumps(value,1)
        self.dict[key] = zlib.compress(s)

def open(filename, flag='c'):
    """Open a persistent dictionary for reading and writing.

    Argument is the filename for the dbm database.
    See the module's __doc__ string for an overview of the interface.
    """
    
    return DbfilenameShelf(filename, flag)

from c_spec import common_base_converter
from c_spec import num_to_c_types
from Numeric import *
from types import *
import os


num_typecode = {}
num_typecode['c'] = 'PyArray_CHAR'
num_typecode['1'] = 'PyArray_SBYTE'
num_typecode['b'] = 'PyArray_UBYTE'
num_typecode['s'] = 'PyArray_SHORT'
num_typecode['w'] = 'PyArray_USHORT'
num_typecode['i'] = 'PyArray_INT' # PyArray_INT has troubles ?? What does this note mean ??
num_typecode['u'] = 'PyArray_UINT'
num_typecode['l'] = 'PyArray_LONG'
num_typecode['f'] = 'PyArray_FLOAT'
num_typecode['d'] = 'PyArray_DOUBLE'
num_typecode['F'] = 'PyArray_CFLOAT'
num_typecode['D'] = 'PyArray_CDOUBLE'

type_check_code = \
"""
class numpy_type_handler
{
public:
    void conversion_numpy_check_type(PyArrayObject* arr_obj, int numeric_type,
                                     const char* name)
    {
        // Make sure input has correct numeric type.
        // allow character and byte to match
        // also allow int and long to match
        int arr_type = arr_obj->descr->type_num;
        if ( arr_type != numeric_type &&
            !(numeric_type == PyArray_CHAR  && arr_type == PyArray_SBYTE) &&
            !(numeric_type == PyArray_SBYTE && arr_type == PyArray_CHAR)  &&
            !(numeric_type == PyArray_INT   && arr_type == PyArray_LONG)  &&
            !(numeric_type == PyArray_LONG  && arr_type == PyArray_INT)) 
        {

            char* type_names[20] = {"char","unsigned byte","byte", "short", "unsigned short",
                                    "int", "unsigned int", "long", "float", "double", 
                                    "complex float","complex double", "object","ntype",
                                    "unkown"};
            char msg[500];
            sprintf(msg,"Conversion Error: received '%s' typed array instead of '%s' typed array for variable '%s'",
                    type_names[arr_type],type_names[numeric_type],name);
            throw_error(PyExc_TypeError,msg);    
        }
    }
    
    void numpy_check_type(PyArrayObject* arr_obj, int numeric_type, const char* name)
    {
        // Make sure input has correct numeric type.
        int arr_type = arr_obj->descr->type_num;
        if ( arr_type != numeric_type &&
            !(numeric_type == PyArray_CHAR  && arr_type == PyArray_SBYTE) &&
            !(numeric_type == PyArray_SBYTE && arr_type == PyArray_CHAR)  &&
            !(numeric_type == PyArray_INT   && arr_type == PyArray_LONG)  &&
            !(numeric_type == PyArray_LONG  && arr_type == PyArray_INT)) 
        {
            char* type_names[20] = {"char","unsigned byte","byte", "short", 
                                    "unsigned short", "int", "unsigned int",
                                    "long", "float", "double", 
                                    "complex float", "complex double", 
                                    "object","ntype","unkown"};
            char msg[500];
            sprintf(msg,"received '%s' typed array instead of '%s' typed array for variable '%s'",
                    type_names[arr_type],type_names[numeric_type],name);
            throw_error(PyExc_TypeError,msg);    
        }
    }
};

numpy_type_handler x__numpy_type_handler = numpy_type_handler();
#define conversion_numpy_check_type x__numpy_type_handler.conversion_numpy_check_type
#define numpy_check_type x__numpy_type_handler.numpy_check_type

"""

size_check_code = \
"""
class numpy_size_handler
{
public:
    void conversion_numpy_check_size(PyArrayObject* arr_obj, int Ndims, 
                                     const char* name)
    {
        if (arr_obj->nd != Ndims)
        {
            char msg[500];
            sprintf(msg,"Conversion Error: received '%d' dimensional array instead of '%d' dimensional array for variable '%s'",
                    arr_obj->nd,Ndims,name);
            throw_error(PyExc_TypeError,msg);
        }    
    }
    
    void numpy_check_size(PyArrayObject* arr_obj, int Ndims, const char* name)
    {
        if (arr_obj->nd != Ndims)
        {
            char msg[500];
            sprintf(msg,"received '%d' dimensional array instead of '%d' dimensional array for variable '%s'",
                    arr_obj->nd,Ndims,name);
            throw_error(PyExc_TypeError,msg);
        }    
    }
};

numpy_size_handler x__numpy_size_handler = numpy_size_handler();
#define conversion_numpy_check_size x__numpy_size_handler.conversion_numpy_check_size
#define numpy_check_size x__numpy_size_handler.numpy_check_size

"""

numeric_init_code = \
"""
Py_Initialize();
import_array();
PyImport_ImportModule("Numeric");
"""
    
class array_converter(common_base_converter):

    def init_info(self):
        common_base_converter.init_info(self)
        self.type_name = 'numpy'
        self.check_func = 'PyArray_Check'    
        self.c_type = 'PyArrayObject*'
        self.return_type = 'PyArrayObject*'
        self.to_c_return = '(PyArrayObject*) py_obj'
        self.matching_types = [ArrayType]
        self.headers = ['"Numeric/arrayobject.h"','<complex>','<math.h>']
        self.support_code = [size_check_code, type_check_code]
        self.module_init_code = [numeric_init_code]    
               
    def get_var_type(self,value):
        return value.typecode()
    
    def template_vars(self,inline=0):
        res = common_base_converter.template_vars(self,inline)    
        if hasattr(self,'var_type'):
            res['num_type'] = num_to_c_types[self.var_type]
            res['num_typecode'] = num_typecode[self.var_type]
        res['array_name'] = self.name + "_array"
        return res
         
    def declaration_code(self,templatize = 0,inline=0):
        code = '%(py_var)s = %(var_lookup)s;\n'   \
               '%(c_type)s %(array_name)s = %(var_convert)s;\n'  \
               'conversion_numpy_check_type(%(array_name)s,%(num_typecode)s,"%(name)s");\n' \
               'int* N%(name)s = %(array_name)s->dimensions;\n' \
               'int* S%(name)s = %(array_name)s->strides;\n' \
               'int D%(name)s = %(array_name)s->nd;\n' \
               '%(num_type)s* %(name)s = (%(num_type)s*) %(array_name)s->data;\n' 
        code = code % self.template_vars(inline=inline)
        return code

#
# weave - C/C++ integration
#

from info_weave import __doc__
from weave_version import weave_version as __version__

try:
    from blitz_tools import blitz
except ImportError:
    pass # Numeric wasn't available    
    
from inline_tools import inline
import ext_tools
from ext_tools import ext_module, ext_function
try:
    from accelerate_tools import accelerate
except:
    pass

from scipy_test.testing import ScipyTest
test = ScipyTest('weave').test

import token
import symbol
import parser

from types import ListType, TupleType, StringType, IntType

def int_to_symbol(i):
    """ Convert numeric symbol or token to a desriptive name.
    """
    try: 
        return symbol.sym_name[i]
    except KeyError:
        return token.tok_name[i]
    
def translate_symbols(ast_tuple):
    """ Translate numeric grammar symbols in an ast_tuple descriptive names.
    
        This simply traverses the tree converting any integer value to values
        found in symbol.sym_name or token.tok_name.
    """    
    new_list = []
    for item in ast_tuple:
        if type(item) == IntType:
            new_list.append(int_to_symbol(item))
        elif type(item) in [TupleType,ListType]:
            new_list.append(translate_symbols(item))
        else:     
            new_list.append(item)
    if type(ast_tuple) == TupleType:
        return tuple(new_list)
    else:
        return new_list

def ast_to_string(ast_seq):
    """* Traverse an ast tree sequence, printing out all leaf nodes.
       
         This effectively rebuilds the expression the tree was built
         from.  I guess its probably missing whitespace.  How bout
         indent stuff and new lines?  Haven't checked this since we're
         currently only dealing with simple expressions.
    *"""
    output = ''
    for item in ast_seq:
        if type(item) is StringType:
            output = output + item
        elif type(item) in [ListType,TupleType]:
            output = output + ast_to_string(item)
    return output                    

def build_atom(expr_string):
    """ Build an ast for an atom from the given expr string.
    
        If expr_string is not a string, it is converted to a string
        before parsing to an ast_tuple.
    """
    # the [1][1] indexing below starts atoms at the third level
    # deep in the resulting parse tree.  parser.expr will return
    # a tree rooted with eval_input -> test_list -> test ...
    # I'm considering test to be the root of atom symbols.
    # It might be a better idea to move down a little in the
    # parse tree. Any benefits? Right now, this works fine. 
    if type(expr_string) == StringType:
        ast = parser.expr(expr_string).totuple()[1][1]
    else:
        ast = parser.expr(`expr_string`).totuple()[1][1]
    return ast

def atom_tuple(expr_string):
    return build_atom(expr_string)

def atom_list(expr_string):
    return tuples_to_lists(build_atom(expr_string))
    
def find_first_pattern(ast_tuple,pattern_list):
    """* Find the first occurence of a pattern one of a list of patterns 
        in ast_tuple.
        
        Used for testing at the moment.
        
        ast_tuple    -- tuple or list created by ast.totuple() or ast.tolist().
        pattern_list -- A single pattern or list of patterns to search
                        for in the ast_tuple.  If a single pattern is 
                        used, it MUST BE A IN A TUPLE format.
        Returns:
            found -- true/false indicating whether pattern was found
            data  -- dictionary of data from first matching pattern in tree.
                     (see match function by Jeremy Hylton).    
    *"""
    found,data = 0,{}
    
    # convert to a list if input wasn't a list
    if type(pattern_list) != ListType:
        pattern_list = [pattern_list]

    # look for any of the patterns in a list of patterns 
    for pattern in pattern_list:
        found,data = match(pattern,ast_tuple)
        if found: 
            break                    
            
    # if we didn't find the pattern, search sub-trees of the parse tree
    if not found:        
        for item in ast_tuple:            
            if type(item) in [TupleType,ListType]:
                # only search sub items if they are a list or tuple.
                 found, data = find_first_pattern(item,pattern_list)
            if found: 
                break     
    return found,data

name_pattern = (token.NAME, ['var'])

def remove_duplicates(lst):
    output = []
    for item in lst:
        if item not in output:
            output.append(item)
    return output

reserved_names = ['sin']

def remove_reserved_names(lst):
    """ These are functions names -- don't create variables for them
        There is a more reobust approach, but this ought to work pretty
        well.
    """
    output = []
    for item in lst:
        if item not in reserved_names:
            output.append(item)
    return output

def harvest_variables(ast_list):    
    """ Retreive all the variables that need to be defined.
    """    
    variables = []
    if type(ast_list) in (ListType,TupleType):
        found,data = match(name_pattern,ast_list)
        if found:
            variables.append(data['var'])
        for item in ast_list:
            if type(item) in (ListType,TupleType):
                 variables.extend(harvest_variables(item))
    variables = remove_duplicates(variables)                 
    variables = remove_reserved_names(variables)                     
    return variables

def match(pattern, data, vars=None):
    """match `data' to `pattern', with variable extraction.

    pattern
        Pattern to match against, possibly containing variables.

    data
        Data to be checked and against which variables are extracted.

    vars
        Dictionary of variables which have already been found.  If not
        provided, an empty dictionary is created.

    The `pattern' value may contain variables of the form ['varname'] which
    are allowed to match anything.  The value that is matched is returned as
    part of a dictionary which maps 'varname' to the matched value.  'varname'
    is not required to be a string object, but using strings makes patterns
    and the code which uses them more readable.

    This function returns two values: a boolean indicating whether a match
    was found and a dictionary mapping variable names to their associated
    values.
    
    From the Demo/Parser/example.py file
    """
    if vars is None:
        vars = {}
    if type(pattern) is ListType:       # 'variables' are ['varname']
        vars[pattern[0]] = data
        return 1, vars
    if type(pattern) is not TupleType:
        return (pattern == data), vars
    if len(data) != len(pattern):
        return 0, vars
    for pattern, data in map(None, pattern, data):
        same, vars = match(pattern, data, vars)
        if not same:
            break
    return same, vars


def tuples_to_lists(ast_tuple):
    """ Convert an ast object tree in tuple form to list form.
    """
    if type(ast_tuple) not in [ListType,TupleType]:
        return ast_tuple
        
    new_list = []
    for item in ast_tuple:
        new_list.append(tuples_to_lists(item))
    return new_list


"""
A little tree I built to help me understand the parse trees.
       -----------303------------------------------
       |                                           |    
      304                -------------------------307-------------------------
       |                 |             |           |             |           |
   1 'result'          9 '['          308        12 ','         308      10 ']'
                                       |                         |
                             ---------309--------          -----309--------         
                             |                  |          |              | 
                          291|304            291|304    291|304           |
                             |                  |          |              |
                            1 'a1'   11 ':'   1 'a2'     2 '10'         11 ':'                                      
"""

""" Tools for compiling C/C++ code to extension modules

    The main function, build_extension(), takes the C/C++ file
    along with some other options and builds a Python extension.
    It uses distutils for most of the heavy lifting.
    
    choose_compiler() is also useful (mainly on windows anyway)
    for trying to determine whether MSVC++ or gcc is available.
    MSVC doesn't handle templates as well, so some of the code emitted
    by the python->C conversions need this info to choose what kind
    of code to create.
    
    The other main thing here is an alternative version of the MingW32
    compiler class.  The class makes it possible to build libraries with
    gcc even if the original version of python was built using MSVC.  It
    does this by converting a pythonxx.lib file to a libpythonxx.a file.
    Note that you need write access to the pythonxx/lib directory to do this.
"""

import sys,os,string,time
import tempfile
import exceptions
import commands

import platform_info

# If linker is 'gcc', this will convert it to 'g++'
# necessary to make sure stdc++ is linked in cross-platform way.
import distutils.sysconfig
import distutils.dir_util
old_init_posix = distutils.sysconfig._init_posix

def _init_posix():
    old_init_posix()
    ld = distutils.sysconfig._config_vars['LDSHARED']
    #distutils.sysconfig._config_vars['LDSHARED'] = ld.replace('gcc','g++')
    # FreeBSD names gcc as cc, so the above find and replace doesn't work.    
    # So, assume first entry in ld is the name of the linker -- gcc or cc or 
    # whatever.  This is a sane assumption, correct?
    # If the linker is gcc, set it to g++
    link_cmds = ld.split()    
    if gcc_exists(link_cmds[0]):
        link_cmds[0] = 'g++'
        ld = ' '.join(link_cmds)
    

    if (sys.platform == 'darwin'):
        # The Jaguar distributed python 2.2 has -arch i386 in the link line
        # which doesn't seem right.  It omits all kinds of warnings, so 
        # remove it.
        ld = ld.replace('-arch i386','')
        
        # The following line is a HACK to fix a problem with building the
        # freetype shared library under Mac OS X:
        ld += ' -framework AppKit'
        
        # 2.3a1 on OS X emits a ton of warnings about long double.  OPT
        # appears to not have all the needed flags set while CFLAGS does.
        cfg_vars = distutils.sysconfig._config_vars
        cfg_vars['OPT'] = cfg_vars['CFLAGS']        
    distutils.sysconfig._config_vars['LDSHARED'] = ld           
    
distutils.sysconfig._init_posix = _init_posix    
# end force g++


class CompileError(exceptions.Exception):
    pass


def create_extension(module_path, **kw):
    """ Create an Extension that can be buil by setup.py
        
        See build_extension for information on keyword arguments.
    """
    # some (most?) platforms will fail to link C++ correctly
    # unless scipy_distutils is used.
    try:
        from scipy_distutils.core import Extension
    except ImportError:
        from distutils.core import Extension
    
    # this is a screwy trick to get rid of a ton of warnings on Unix
    import distutils.sysconfig
    distutils.sysconfig.get_config_vars()
    if distutils.sysconfig._config_vars.has_key('OPT'):
        flags = distutils.sysconfig._config_vars['OPT']        
        flags = flags.replace('-Wall','')
        distutils.sysconfig._config_vars['OPT'] = flags
    
    # get the name of the module and the extension directory it lives in.  
    module_dir,cpp_name = os.path.split(os.path.abspath(module_path))
    module_name,ext = os.path.splitext(cpp_name)    
           
    # the business end of the function
    sources = kw.get('sources',[])
    kw['sources'] = [module_path] + sources        
        
    #--------------------------------------------------------------------
    # added access to environment variable that user can set to specify
    # where python (and other) include files are located.  This is 
    # very useful on systems where python is installed by the root, but
    # the user has also installed numerous packages in their own 
    # location.
    #--------------------------------------------------------------------
    if os.environ.has_key('PYTHONINCLUDE'):
        path_string = os.environ['PYTHONINCLUDE']        
        if sys.platform == "win32":
            extra_include_dirs = path_string.split(';')
        else:  
            extra_include_dirs = path_string.split(':')
        include_dirs = kw.get('include_dirs',[])
        kw['include_dirs'] = include_dirs + extra_include_dirs

    # SunOS specific
    # fix for issue with linking to libstdc++.a. see:
    # http://mail.python.org/pipermail/python-dev/2001-March/013510.html
    platform = sys.platform
    version = sys.version.lower()
    if platform[:5] == 'sunos' and version.find('gcc') != -1:
        extra_link_args = kw.get('extra_link_args',[])
        kw['extra_link_args'] = ['-mimpure-text'] +  extra_link_args
        
    ext = Extension(module_name, **kw)
    return ext    
                            
def build_extension(module_path,compiler_name = '',build_dir = None,
                    temp_dir = None, verbose = 0, **kw):
    """ Build the file given by module_path into a Python extension module.
    
        build_extensions uses distutils to build Python extension modules.
        kw arguments not used are passed on to the distutils extension
        module.  Directory settings can handle absoulte settings, but don't
        currently expand '~' or environment variables.
        
        module_path   -- the full path name to the c file to compile.  
                         Something like:  /full/path/name/module_name.c 
                         The name of the c/c++ file should be the same as the
                         name of the module (i.e. the initmodule() routine)
        compiler_name -- The name of the compiler to use.  On Windows if it 
                         isn't given, MSVC is used if it exists (is found).
                         gcc is used as a second choice. If neither are found, 
                         the default distutils compiler is used. Acceptable 
                         names are 'gcc', 'msvc' or any of the compiler names 
                         shown by distutils.ccompiler.show_compilers()
        build_dir     -- The location where the resulting extension module 
                         should be placed. This location must be writable.  If
                         it isn't, several default locations are tried.  If the 
                         build_dir is not in the current python path, a warning
                         is emitted, and it is added to the end of the path.
                         build_dir defaults to the current directory.
        temp_dir      -- The location where temporary files (*.o or *.obj)
                         from the build are placed. This location must be 
                         writable.  If it isn't, several default locations are 
                         tried.  It defaults to tempfile.gettempdir()
        verbose       -- 0, 1, or 2.  0 is as quiet as possible. 1 prints
                         minimal information.  2 is noisy.                 
        **kw          -- keyword arguments. These are passed on to the 
                         distutils extension module.  Most of the keywords
                         are listed below.

        Distutils keywords.  These are cut and pasted from Greg Ward's
        distutils.extension.Extension class for convenience:
        
        sources : [string]
          list of source filenames, relative to the distribution root
          (where the setup script lives), in Unix form (slash-separated)
          for portability.  Source files may be C, C++, SWIG (.i),
          platform-specific resource files, or whatever else is recognized
          by the "build_ext" command as source for a Python extension.
          Note: The module_path file is always appended to the front of this
                list                
        include_dirs : [string]
          list of directories to search for C/C++ header files (in Unix
          form for portability)          
        define_macros : [(name : string, value : string|None)]
          list of macros to define; each macro is defined using a 2-tuple,
          where 'value' is either the string to define it to or None to
          define it without a particular value (equivalent of "#define
          FOO" in source or -DFOO on Unix C compiler command line)          
        undef_macros : [string]
          list of macros to undefine explicitly
        library_dirs : [string]
          list of directories to search for C/C++ libraries at link time
        libraries : [string]
          list of library names (not filenames or paths) to link against
        runtime_library_dirs : [string]
          list of directories to search for C/C++ libraries at run time
          (for shared extensions, this is when the extension is loaded)
        extra_objects : [string]
          list of extra files to link with (eg. object files not implied
          by 'sources', static library that must be explicitly specified,
          binary resource files, etc.)
        extra_compile_args : [string]
          any extra platform- and compiler-specific information to use
          when compiling the source files in 'sources'.  For platforms and
          compilers where "command line" makes sense, this is typically a
          list of command-line arguments, but for other platforms it could
          be anything.
        extra_link_args : [string]
          any extra platform- and compiler-specific information to use
          when linking object files together to create the extension (or
          to create a new static Python interpreter).  Similar
          interpretation as for 'extra_compile_args'.
        export_symbols : [string]
          list of symbols to be exported from a shared extension.  Not
          used on all platforms, and not generally necessary for Python
          extensions, which typically export exactly one symbol: "init" +
          extension_name.
    """
    success = 0
    try:
        from scipy_distutils.core import setup, Extension
        from scipy_distutils.log import set_verbosity
        set_verbosity(-1)
    except ImportError:
        from distutils.core import setup, Extension
    
    # this is a screwy trick to get rid of a ton of warnings on Unix
    import distutils.sysconfig
    distutils.sysconfig.get_config_vars()
    if distutils.sysconfig._config_vars.has_key('OPT'):
        flags = distutils.sysconfig._config_vars['OPT']        
        flags = flags.replace('-Wall','')
        distutils.sysconfig._config_vars['OPT'] = flags
    
    # get the name of the module and the extension directory it lives in.  
    module_dir,cpp_name = os.path.split(os.path.abspath(module_path))
    module_name,ext = os.path.splitext(cpp_name)    
       
    # configure temp and build directories
    temp_dir = configure_temp_dir(temp_dir)    
    build_dir = configure_build_dir(module_dir)
    
    # dag. We keep having to add directories to the path to keep 
    # object files separated from each other.  gcc2.x and gcc3.x C++ 
    # object files are not compatible, so we'll stick them in a sub
    # dir based on their version.  This will add an md5 check sum
    # of the compiler binary to the directory name to keep objects
    # from different compilers in different locations.
    
    compiler_dir = platform_info.get_compiler_dir(compiler_name)
    temp_dir = os.path.join(temp_dir,compiler_dir)
    distutils.dir_util.mkpath(temp_dir)
    
    compiler_name = choose_compiler(compiler_name)
            
    configure_sys_argv(compiler_name,temp_dir,build_dir)
    
    # the business end of the function
    try:
        if verbose == 1:
            print 'Compiling code...'
            
        # set compiler verboseness 2 or more makes it output results
        if verbose > 1:
            verb = 1                
        else:
            verb = 0
        
        t1 = time.time()        
        ext = create_extension(module_path,**kw)
        # the switcheroo on SystemExit here is meant to keep command line
        # sessions from exiting when compiles fail.
        builtin = sys.modules['__builtin__']
        old_SysExit = builtin.__dict__['SystemExit']
        builtin.__dict__['SystemExit'] = CompileError
        
        # distutils for MSVC messes with the environment, so we save the
        # current state and restore them afterward.
        import copy
        environ = copy.deepcopy(os.environ)
        try:
            setup(name = module_name, ext_modules = [ext],verbose=verb)
        finally:
            # restore state
            os.environ = environ        
            # restore SystemExit
            builtin.__dict__['SystemExit'] = old_SysExit
        t2 = time.time()
        
        if verbose == 1:
            print 'finished compiling (sec): ', t2 - t1    
        success = 1
        configure_python_path(build_dir)
    except SyntaxError: #TypeError:
        success = 0    
            
    # restore argv after our trick...            
    restore_sys_argv()

    return success

old_argv = []
def configure_sys_argv(compiler_name,temp_dir,build_dir):
    # We're gonna play some tricks with argv here to pass info to distutils 
    # which is really built for command line use. better way??
    global old_argv
    old_argv = sys.argv[:]        
    sys.argv = ['','build_ext','--build-lib', build_dir,
                               '--build-temp',temp_dir]    
    if compiler_name == 'gcc':
        sys.argv.insert(2,'--compiler='+compiler_name)
    elif compiler_name:
        sys.argv.insert(2,'--compiler='+compiler_name)

def restore_sys_argv():
    sys.argv = old_argv
            
def configure_python_path(build_dir):    
    #make sure the module lives in a directory on the python path.
    python_paths = [os.path.abspath(x) for x in sys.path]
    if os.path.abspath(build_dir) not in python_paths:
        #print "warning: build directory was not part of python path."\
        #      " It has been appended to the path."
        sys.path.append(os.path.abspath(build_dir))

def choose_compiler(compiler_name=''):
    """ Try and figure out which compiler is gonna be used on windows.
        On other platforms, it just returns whatever value it is given.
        
        converts 'gcc' to 'mingw32' on win32
    """
    if sys.platform == 'win32':        
        if not compiler_name:
            # On Windows, default to MSVC and use gcc if it wasn't found
            # wasn't found.  If neither are found, go with whatever
            # the default is for distutils -- and probably fail...
            if msvc_exists():
                compiler_name = 'msvc'
            elif gcc_exists():
                compiler_name = 'mingw32'
        elif compiler_name == 'gcc':
                compiler_name = 'mingw32'
    else:
        # don't know how to force gcc -- look into this.
        if compiler_name == 'gcc':
                compiler_name = 'unix'                    
    return compiler_name
    
def gcc_exists(name = 'gcc'):
    """ Test to make sure gcc is found 
       
        Does this return correct value on win98???
    """
    result = 0
    cmd = '%s -v' % name
    try:
        w,r=os.popen4(cmd)
        w.close()
        str_result = r.read()
        #print str_result
        if string.find(str_result,'Reading specs') != -1:
            result = 1
    except:
        # This was needed because the msvc compiler messes with
        # the path variable. and will occasionlly mess things up
        # so much that gcc is lost in the path. (Occurs in test
        # scripts)
        result = not os.system(cmd)
    return result

def msvc_exists():
    """ Determine whether MSVC is available on the machine.
    """
    result = 0
    try:
        w,r=os.popen4('cl')
        w.close()
        str_result = r.read()
        #print str_result
        if string.find(str_result,'Microsoft') != -1:
            result = 1
    except:
        #assume we're ok if devstudio exists
        import distutils.msvccompiler
        version = distutils.msvccompiler.get_devstudio_version()
        if version:
            result = 1
    return result

if os.name == 'nt':
    def run_command(command):
        """ not sure how to get exit status on nt. """
        in_pipe,out_pipe = os.popen4(command)
        in_pipe.close()
        text = out_pipe.read()
        return 0, text
else:
    run_command = commands.getstatusoutput

        
def configure_temp_dir(temp_dir=None):
    if temp_dir is None:         
        temp_dir = tempfile.gettempdir()
    elif not os.path.exists(temp_dir) or not os.access(temp_dir,os.W_OK):
        print "warning: specified temp_dir '%s' does not exist " \
              "or is not writable. Using the default temp directory" % \
              temp_dir
        temp_dir = tempfile.gettempdir()

    # final check that that directories are writable.        
    if not os.access(temp_dir,os.W_OK):
        msg = "Either the temp or build directory wasn't writable. Check" \
              " these locations: '%s'" % temp_dir  
        raise ValueError, msg
    return temp_dir

def configure_build_dir(build_dir=None):
    # make sure build_dir exists and is writable
    if build_dir and (not os.path.exists(build_dir) or 
                      not os.access(build_dir,os.W_OK)):
        print "warning: specified build_dir '%s' does not exist " \
               "or is not writable. Trying default locations" % build_dir
        build_dir = None
        
    if build_dir is None:
        #default to building in the home directory of the given module.        
        build_dir = os.curdir
        # if it doesn't work use the current directory.  This should always
        # be writable.    
        if not os.access(build_dir,os.W_OK):
            print "warning:, neither the module's directory nor the "\
                  "current directory are writable.  Using the temporary"\
                  "directory."
            build_dir = tempfile.gettempdir()

    # final check that that directories are writable.
    if not os.access(build_dir,os.W_OK):
        msg = "The build directory wasn't writable. Check" \
              " this location: '%s'" % build_dir
        raise ValueError, msg
        
    return os.path.abspath(build_dir)        
    
if sys.platform == 'win32':
    import distutils.cygwinccompiler
    from distutils.version import StrictVersion
    from distutils.ccompiler import gen_preprocess_options, gen_lib_options
    from distutils.errors import DistutilsExecError, CompileError, UnknownFileError
    
    from distutils.unixccompiler import UnixCCompiler 
    
    # the same as cygwin plus some additional parameters
    class Mingw32CCompiler(distutils.cygwinccompiler.CygwinCCompiler):
        """ A modified MingW32 compiler compatible with an MSVC built Python.
            
        """
    
        compiler_type = 'mingw32'
    
        def __init__ (self,
                      verbose=0,
                      dry_run=0,
                      force=0):
    
            distutils.cygwinccompiler.CygwinCCompiler.__init__ (self, 
                                                       verbose,dry_run, force)
            
            # we need to support 3.2 which doesn't match the standard
            # get_versions methods regex
            if self.gcc_version is None:
                import re
                out = os.popen('gcc' + ' -dumpversion','r')
                out_string = out.read()
                out.close()
                result = re.search('(\d+\.\d+)',out_string)
                if result:
                    self.gcc_version = StrictVersion(result.group(1))            

            # A real mingw32 doesn't need to specify a different entry point,
            # but cygwin 2.91.57 in no-cygwin-mode needs it.
            if self.gcc_version <= "2.91.57":
                entry_point = '--entry _DllMain@12'
            else:
                entry_point = ''
            if self.linker_dll == 'dllwrap':
                self.linker = 'dllwrap' + ' --driver-name g++'
            elif self.linker_dll == 'gcc':
                self.linker = 'g++'    

            # **changes: eric jones 4/11/01
            # 1. Check for import library on Windows.  Build if it doesn't exist.
            if not import_library_exists():
                build_import_library()
    
            # **changes: eric jones 4/11/01
            # 2. increased optimization and turned off all warnings
            # 3. also added --driver-name g++
            #self.set_executables(compiler='gcc -mno-cygwin -O2 -w',
            #                     compiler_so='gcc -mno-cygwin -mdll -O2 -w',
            #                     linker_exe='gcc -mno-cygwin',
            #                     linker_so='%s --driver-name g++ -mno-cygwin -mdll -static %s' 
            #                                % (self.linker, entry_point))
            if self.gcc_version <= "3.0.0":
                self.set_executables(compiler='gcc -mno-cygwin -O2 -w',
                                     compiler_so='gcc -mno-cygwin -mdll -O2 -w -Wstrict-prototypes',
                                     linker_exe='g++ -mno-cygwin',
                                     linker_so='%s -mno-cygwin -mdll -static %s' 
                                                % (self.linker, entry_point))
            else:            
                self.set_executables(compiler='gcc -mno-cygwin -O2 -w',
                                     compiler_so='gcc -O2 -w -Wstrict-prototypes',
                                     linker_exe='g++ ',
                                     linker_so='g++ -shared')
            # added for python2.3 support
            # we can't pass it through set_executables because pre 2.2 would fail
            self.compiler_cxx = ['g++']
            
            # Maybe we should also append -mthreads, but then the finished
            # dlls need another dll (mingwm10.dll see Mingw32 docs)
            # (-mthreads: Support thread-safe exception handling on `Mingw32')       
            
            # no additional libraries needed 
            self.dll_libraries=[]
            
        # __init__ ()

        def link(self,
                 target_desc,
                 objects,
                 output_filename,
                 output_dir,
                 libraries,
                 library_dirs,
                 runtime_library_dirs,
                 export_symbols=None, # export_symbols, we do this in our def-file
                 debug=0,
                 extra_preargs=None,
                 extra_postargs=None,
                 build_temp=None,
                 target_lang=None):
            if self.gcc_version < "3.0.0":
                distutils.cygwinccompiler.CygwinCCompiler.link(self,
                               target_desc,
                               objects,
                               output_filename,
                               output_dir,
                               libraries,
                               library_dirs,
                               runtime_library_dirs,
                               None, # export_symbols, we do this in our def-file
                               debug,
                               extra_preargs,
                               extra_postargs,
                               build_temp,
                               target_lang)
            else:
                UnixCCompiler.link(self,
                               target_desc,
                               objects,
                               output_filename,
                               output_dir,
                               libraries,
                               library_dirs,
                               runtime_library_dirs,
                               None, # export_symbols, we do this in our def-file
                               debug,
                               extra_preargs,
                               extra_postargs,
                               build_temp,
                               target_lang)

        
    # On windows platforms, we want to default to mingw32 (gcc)
    # because msvc can't build blitz stuff.
    # We should also check the version of gcc available...
    #distutils.ccompiler._default_compilers['nt'] = 'mingw32'
    #distutils.ccompiler._default_compilers = (('nt', 'mingw32'))
    # reset the Mingw32 compiler in distutils to the one defined above
    distutils.cygwinccompiler.Mingw32CCompiler = Mingw32CCompiler
    
    def import_library_exists():
        """ on windows platforms, make sure a gcc import library exists
        """
        if os.name == 'nt':
            lib_name = "libpython%d%d.a" % tuple(sys.version_info[:2])
            full_path = os.path.join(sys.prefix,'libs',lib_name)
            if not os.path.exists(full_path):
                return 0
        return 1
    
    def build_import_library():
        """ Build the import libraries for Mingw32-gcc on Windows
        """
        from scipy_distutils import lib2def
        #libfile, deffile = parse_cmd()
        #if deffile is None:
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
        success = not os.system(cmd)
        # for now, fail silently
        if not success:
            print 'WARNING: failed to build import library for gcc. Linking will fail.'
        #if not success:
        #    msg = "Couldn't find import library, and failed to build it."
        #    raise DistutilsPlatformError, msg
    

# swigptr.py

swigptr_code = """

/***********************************************************************
 * $Header$
 * swig_lib/python/python.cfg
 *
 * Contains variable linking and pointer type-checking code.
 ************************************************************************/

#include <string.h>
#include <stdlib.h>

#ifdef __cplusplus
extern "C" {
#endif
#include "Python.h"

/* Definitions for Windows/Unix exporting */
#if defined(_WIN32) || defined(__WIN32__)
#   if defined(_MSC_VER)
#       define SWIGEXPORT(a) __declspec(dllexport) a
#   else
#       if defined(__BORLANDC__)
#           define SWIGEXPORT(a) a _export
#       else
#           define SWIGEXPORT(a) a
#       endif
#   endif
#else
#   define SWIGEXPORT(a) a
#endif

#ifdef SWIG_GLOBAL
#define SWIGSTATICRUNTIME(a) SWIGEXPORT(a)
#else
#define SWIGSTATICRUNTIME(a) static a
#endif

typedef struct {
  char  *name;
  PyObject *(*get_attr)(void);
  int (*set_attr)(PyObject *);
} swig_globalvar;

typedef struct swig_varlinkobject {
  PyObject_HEAD
  swig_globalvar **vars;
  int      nvars;
  int      maxvars;
} swig_varlinkobject;

/* ----------------------------------------------------------------------
   swig_varlink_repr()

   Function for python repr method
   ---------------------------------------------------------------------- */

static PyObject *
swig_varlink_repr(swig_varlinkobject *v)
{
  v = v;
  return PyString_FromString("<Global variables>");
}

/* ---------------------------------------------------------------------
   swig_varlink_print()

   Print out all of the global variable names
   --------------------------------------------------------------------- */

static int
swig_varlink_print(swig_varlinkobject *v, FILE *fp, int flags)
{

  int i = 0;
  flags = flags;
  fprintf(fp,"Global variables { ");
  while (v->vars[i]) {
    fprintf(fp,"%s", v->vars[i]->name);
    i++;
    if (v->vars[i]) fprintf(fp,", ");
  }
  fprintf(fp," }\\n");
  return 0;
}

/* --------------------------------------------------------------------
   swig_varlink_getattr

   This function gets the value of a variable and returns it as a
   PyObject.   In our case, we'll be looking at the datatype and
   converting into a number or string
   -------------------------------------------------------------------- */

static PyObject *
swig_varlink_getattr(swig_varlinkobject *v, char *n)
{
  int i = 0;
  char temp[128];

  while (v->vars[i]) {
    if (strcmp(v->vars[i]->name,n) == 0) {
      return (*v->vars[i]->get_attr)();
    }
    i++;
  }
  sprintf(temp,"C global variable %s not found.", n);
  PyErr_SetString(PyExc_NameError,temp);
  return NULL;
}

/* -------------------------------------------------------------------
   swig_varlink_setattr()

   This function sets the value of a variable.
   ------------------------------------------------------------------- */

static int
swig_varlink_setattr(swig_varlinkobject *v, char *n, PyObject *p)
{
  char temp[128];
  int i = 0;
  while (v->vars[i]) {
    if (strcmp(v->vars[i]->name,n) == 0) {
      return (*v->vars[i]->set_attr)(p);
    }
    i++;
  }
  sprintf(temp,"C global variable %s not found.", n);
  PyErr_SetString(PyExc_NameError,temp);
  return 1;
}

statichere PyTypeObject varlinktype = {
/*  PyObject_HEAD_INIT(&PyType_Type)  Note : This doesn't work on some machines */
  PyObject_HEAD_INIT(0)
  0,
  "varlink",                          /* Type name    */
  sizeof(swig_varlinkobject),         /* Basic size   */
  0,                                  /* Itemsize     */
  0,                                  /* Deallocator  */
  (printfunc) swig_varlink_print,     /* Print        */
  (getattrfunc) swig_varlink_getattr, /* get attr     */
  (setattrfunc) swig_varlink_setattr, /* Set attr     */
  0,                                  /* tp_compare   */
  (reprfunc) swig_varlink_repr,       /* tp_repr      */
  0,                                  /* tp_as_number */
  0,                                  /* tp_as_mapping*/
  0,                                  /* tp_hash      */
};

/* Create a variable linking object for use later */

SWIGSTATICRUNTIME(PyObject *)
SWIG_newvarlink(void)
{
  swig_varlinkobject *result = 0;
  result = PyMem_NEW(swig_varlinkobject,1);
  varlinktype.ob_type = &PyType_Type;    /* Patch varlinktype into a PyType */
  result->ob_type = &varlinktype;
  /*  _Py_NewReference(result);  Does not seem to be necessary */
  result->nvars = 0;
  result->maxvars = 64;
  result->vars = (swig_globalvar **) malloc(64*sizeof(swig_globalvar *));
  result->vars[0] = 0;
  result->ob_refcnt = 0;
  Py_XINCREF((PyObject *) result);
  return ((PyObject*) result);
}

SWIGSTATICRUNTIME(void)
SWIG_addvarlink(PyObject *p, char *name,
           PyObject *(*get_attr)(void), int (*set_attr)(PyObject *p))
{
  swig_varlinkobject *v;
  v= (swig_varlinkobject *) p;

  if (v->nvars >= v->maxvars -1) {
    v->maxvars = 2*v->maxvars;
    v->vars = (swig_globalvar **) realloc(v->vars,v->maxvars*sizeof(swig_globalvar *));
    if (v->vars == NULL) {
      fprintf(stderr,"SWIG : Fatal error in initializing Python module.\\n");
      exit(1);
    }
  }
  v->vars[v->nvars] = (swig_globalvar *) malloc(sizeof(swig_globalvar));
  v->vars[v->nvars]->name = (char *) malloc(strlen(name)+1);
  strcpy(v->vars[v->nvars]->name,name);
  v->vars[v->nvars]->get_attr = get_attr;
  v->vars[v->nvars]->set_attr = set_attr;
  v->nvars++;
  v->vars[v->nvars] = 0;
}

/* -----------------------------------------------------------------------------
 * Pointer type-checking
 * ----------------------------------------------------------------------------- */

/* SWIG pointer structure */
typedef struct SwigPtrType {
  char               *name;               /* Datatype name                  */
  int                 len;                /* Length (used for optimization) */
  void               *(*cast)(void *);    /* Pointer casting function       */
  struct SwigPtrType *next;               /* Linked list pointer            */
} SwigPtrType;

/* Pointer cache structure */
typedef struct {
  int                 stat;               /* Status (valid) bit             */
  SwigPtrType        *tp;                 /* Pointer to type structure      */
  char                name[256];          /* Given datatype name            */
  char                mapped[256];        /* Equivalent name                */
} SwigCacheType;

static int SwigPtrMax  = 64;           /* Max entries that can be currently held */
static int SwigPtrN    = 0;            /* Current number of entries              */
static int SwigPtrSort = 0;            /* Status flag indicating sort            */
static int SwigStart[256];             /* Starting positions of types            */
static SwigPtrType *SwigPtrTable = 0;  /* Table containing pointer equivalences  */

/* Cached values */
#define SWIG_CACHESIZE  8
#define SWIG_CACHEMASK  0x7
static SwigCacheType SwigCache[SWIG_CACHESIZE];
static int SwigCacheIndex = 0;
static int SwigLastCache = 0;

/* Sort comparison function */
static int swigsort(const void *data1, const void *data2) {
        SwigPtrType *d1 = (SwigPtrType *) data1;
        SwigPtrType *d2 = (SwigPtrType *) data2;
        return strcmp(d1->name,d2->name);
}

/* Register a new datatype with the type-checker */
SWIGSTATICRUNTIME(void)
SWIG_RegisterMapping(char *origtype, char *newtype, void *(*cast)(void *)) {
  int i;
  SwigPtrType *t = 0,*t1;

  /* Allocate the pointer table if necessary */
  if (!SwigPtrTable) {
    SwigPtrTable = (SwigPtrType *) malloc(SwigPtrMax*sizeof(SwigPtrType));
  }

  /* Grow the table */
  if (SwigPtrN >= SwigPtrMax) {
    SwigPtrMax = 2*SwigPtrMax;
    SwigPtrTable = (SwigPtrType *) realloc((char *) SwigPtrTable,SwigPtrMax*sizeof(SwigPtrType));
  }
  for (i = 0; i < SwigPtrN; i++) {
    if (strcmp(SwigPtrTable[i].name,origtype) == 0) {
      t = &SwigPtrTable[i];
      break;
    }
  }
  if (!t) {
    t = &SwigPtrTable[SwigPtrN++];
    t->name = origtype;
    t->len = strlen(t->name);
    t->cast = 0;
    t->next = 0;
  }

  /* Check for existing entries */
  while (t->next) {
    if ((strcmp(t->name,newtype) == 0)) {
      if (cast) t->cast = cast;
      return;
    }
    t = t->next;
  }
  t1 = (SwigPtrType *) malloc(sizeof(SwigPtrType));
  t1->name = newtype;
  t1->len = strlen(t1->name);
  t1->cast = cast;
  t1->next = 0;
  t->next = t1;
  SwigPtrSort = 0;
}

/* Make a pointer value string */
SWIGSTATICRUNTIME(void)
SWIG_MakePtr(char *c, const void *ptr, char *type) {
  static char hex[17] = "0123456789abcdef";
  unsigned long p, s;
  char result[24], *r;
  r = result;
  p = (unsigned long) ptr;
  if (p > 0) {
    while (p > 0) {
      s = p & 0xf;
      *(r++) = hex[s];
      p = p >> 4;
    }
    *r = '_';
    while (r >= result)
      *(c++) = *(r--);
    strcpy (c, type);
  } else {
    strcpy (c, "NULL");
  }
}

/* Function for getting a pointer value */
SWIGSTATICRUNTIME(char *)
SWIG_GetPtr(char *c, void **ptr, char *t)
{
  //std::cout << t << " " << c << std::endl;
  unsigned long p;
  char temp_type[256], *name;
  int  i, len, start, end;
  SwigPtrType *sp,*tp;
  SwigCacheType *cache;
  register int d;
  p = 0;
  /* Pointer values must start with leading underscore */
  if (*c != '_') {
    *ptr = (void *) 0;
    if (strcmp(c,"NULL") == 0) return (char *) 0;
    else c;
  }
  c++;
  /* Extract hex value from pointer */
  while (d = *c) {
    if ((d >= '0') && (d <= '9'))
      p = (p << 4) + (d - '0');
    else if ((d >= 'a') && (d <= 'f'))
      p = (p << 4) + (d - ('a'-10));
    else
      break;
    c++;
  }
  *ptr = (void *) p;
  //std::cout << t << " " << c << std::endl;
  if ((!t) || (strcmp(t,c)==0))
      return (char *) 0;
  else
  {
      // added ej -- if type check fails, its always an error.
      return (char*) 1;
  }
  if (!SwigPtrSort) {
    qsort((void *) SwigPtrTable, SwigPtrN, sizeof(SwigPtrType), swigsort);
    for (i = 0; i < 256; i++) SwigStart[i] = SwigPtrN;
    for (i = SwigPtrN-1; i >= 0; i--) SwigStart[(int) (SwigPtrTable[i].name[1])] = i;
    for (i = 255; i >= 1; i--) {
      if (SwigStart[i-1] > SwigStart[i])
        SwigStart[i-1] = SwigStart[i];
    }
    SwigPtrSort = 1;
    for (i = 0; i < SWIG_CACHESIZE; i++) SwigCache[i].stat = 0;
  }
  /* First check cache for matches.  Uses last cache value as starting point */
  cache = &SwigCache[SwigLastCache];
  for (i = 0; i < SWIG_CACHESIZE; i++) {
    if (cache->stat && (strcmp(t,cache->name) == 0) && (strcmp(c,cache->mapped) == 0)) {
      cache->stat++;
      if (cache->tp->cast) *ptr = (*(cache->tp->cast))(*ptr);
      return (char *) 0;
    }
    SwigLastCache = (SwigLastCache+1) & SWIG_CACHEMASK;
    if (!SwigLastCache) cache = SwigCache;
    else cache++;
  }
  /* Type mismatch.  Look through type-mapping table */
  start = SwigStart[(int) t[1]];
  end = SwigStart[(int) t[1]+1];
  sp = &SwigPtrTable[start];

  /* Try to find a match */
  while (start <= end) {
    if (strncmp(t,sp->name,sp->len) == 0) {
      name = sp->name;
      len = sp->len;
      tp = sp->next;
      /* Try to find entry for our given datatype */
      while(tp) {
        if (tp->len >= 255) {
          return c;
        }
        strcpy(temp_type,tp->name);
        strncat(temp_type,t+len,255-tp->len);
        if (strcmp(c,temp_type) == 0) {
          strcpy(SwigCache[SwigCacheIndex].mapped,c);
          strcpy(SwigCache[SwigCacheIndex].name,t);
          SwigCache[SwigCacheIndex].stat = 1;
          SwigCache[SwigCacheIndex].tp = tp;
          SwigCacheIndex = SwigCacheIndex & SWIG_CACHEMASK;
          /* Get pointer value */
          *ptr = (void *) p;
          if (tp->cast) *ptr = (*(tp->cast))(*ptr);
          return (char *) 0;
        }
        tp = tp->next;
      }
    }
    sp++;
    start++;
  }
  return c;
}

/* New object-based GetPointer function. This uses the Python abstract
 * object interface to automatically dereference the 'this' attribute
 * of shadow objects. */

SWIGSTATICRUNTIME(char *)
SWIG_GetPtrObj(PyObject *obj, void **ptr, char *type) {
  PyObject *sobj = obj;
  char     *str;
  if (!PyString_Check(obj)) {
    sobj = PyObject_GetAttrString(obj,"this");
    if (!sobj) return "";
  }
  str = PyString_AsString(sobj);
  //printf("str: %s\\n", str);
  return SWIG_GetPtr(str,ptr,type);
}

#ifdef __cplusplus
}
#endif

"""
import common_info
from c_spec import common_base_converter
import sys,os

# these may need user configuration.
if sys.platform == "win32":
    wx_base = r'c:\third\wxpython-2.4.0.7'
else:
    # probably should do some more discovery here.
    wx_base = '/usr/lib/wxPython'

def get_wxconfig(flag):
    wxconfig = os.path.join(wx_base,'bin','wx-config')
    import commands
    res,settings = commands.getstatusoutput(wxconfig + ' --' + flag)
    if res:
        msg = wxconfig + ' failed. Impossible to learn wxPython settings'
        raise RuntimeError, msg
    return settings.split()

wx_to_c_template = \
"""
class %(type_name)s_handler
{
public:    
    %(c_type)s convert_to_%(type_name)s(PyObject* py_obj, const char* name)
    {
        %(c_type)s wx_ptr;        
        // work on this error reporting...
        if (SWIG_GetPtrObj(py_obj,(void **) &wx_ptr,"_%(type_name)s_p"))
            handle_conversion_error(py_obj,"%(type_name)s", name);
        %(inc_ref_count)s
        return wx_ptr;
    }
    
    %(c_type)s py_to_%(type_name)s(PyObject* py_obj,const char* name)
    {
        %(c_type)s wx_ptr;        
        // work on this error reporting...
        if (SWIG_GetPtrObj(py_obj,(void **) &wx_ptr,"_%(type_name)s_p"))
            handle_bad_type(py_obj,"%(type_name)s", name);
        %(inc_ref_count)s
        return wx_ptr;
    }    
};

%(type_name)s_handler x__%(type_name)s_handler = %(type_name)s_handler();
#define convert_to_%(type_name)s(py_obj,name) \\
        x__%(type_name)s_handler.convert_to_%(type_name)s(py_obj,name)
#define py_to_%(type_name)s(py_obj,name) \\
        x__%(type_name)s_handler.py_to_%(type_name)s(py_obj,name)

"""

class wx_converter(common_base_converter):
    def __init__(self,class_name="undefined"):
        self.class_name = class_name
        common_base_converter.__init__(self)

    def init_info(self):
        common_base_converter.init_info(self)
        # These are generated on the fly instead of defined at 
        # the class level.
        self.type_name = self.class_name
        self.c_type = self.class_name + "*"
        self.return_type = self.class_name + "*"
        self.to_c_return = None # not used
        self.check_func = None # not used
        self.headers.append('"wx/wx.h"')
        if sys.platform == "win32":        
            # These will be used in many cases
            self.headers.append('<windows.h>')        
            
            # These are needed for linking.
            self.libraries.extend(['kernel32','user32','gdi32','comdlg32',
                                   'winspool', 'winmm', 'shell32', 
                                   'oldnames', 'comctl32', 'ctl3d32',
                                   'odbc32', 'ole32', 'oleaut32', 
                                   'uuid', 'rpcrt4', 'advapi32', 'wsock32'])
                                   
            # not sure which of these macros are needed.
            self.define_macros.append(('WIN32', '1'))
            self.define_macros.append(('__WIN32__', '1'))
            self.define_macros.append(('_WINDOWS', '1'))
            self.define_macros.append(('STRICT', '1'))
            # I think this will only work on NT/2000/XP set
            # set to 0x0400 for earlier versions.
            # Hmmm.  setting this breaks stuff
            #self.define_macros.append(('WINVER', '0x0350'))

            self.library_dirs.append(os.path.join(wx_base,'lib'))
            #self.include_dirs.append(os.path.join(wx_base,'include'))            
            self.include_dirs.append(wx_base)            
            self.include_dirs.append(os.path.join(wx_base,'include'))            
            self.include_dirs.append(os.path.join(wx_base,'include','msw'))            
            # how do I discover unicode or not unicode??            
            # non-unicode            
            self.libraries.append('wxmsw24h')
            self.include_dirs.append(os.path.join(wx_base,'lib'))
            
            # unicode
            #self.libraries.append('wxmswuh')
            #self.include_dirs.append(os.path.join(wx_base,'lib','mswdlluh'))
            #self.define_macros.append(('UNICODE', '1'))
        else:
            # make sure the gtk files are available 
            # ?? Do I need to link to them?
            self.headers.append('"gdk/gdk.h"')
            # !! This shouldn't be hard coded.
            self.include_dirs.append("/usr/include/gtk-1.2")
            self.include_dirs.append("/usr/include/glib-1.2")
            self.include_dirs.append("/usr/lib/glib/include")
            cxxflags = get_wxconfig('cxxflags')
            libflags = get_wxconfig('libs') + get_wxconfig('gl-libs')
            
            #older versions of wx do not support the ldflags.
            try:
                ldflags = get_wxconfig('ldflags')
            except RuntimeError:
                ldflags = []
                    
            self.extra_compile_args.extend(cxxflags)
            self.extra_link_args.extend(libflags)
            self.extra_link_args.extend(ldflags)            
        self.support_code.append(common_info.swig_support_code)
    
    def type_match(self,value):
        is_match = 0
        try:
            wx_class = value.this.split('_')[-2]
            if wx_class[:2] == 'wx':
                is_match = 1
        except AttributeError:
            pass
        return is_match

    def generate_build_info(self):
        if self.class_name != "undefined":
            res = common_base_converter.generate_build_info(self)
        else:
            # if there isn't a class_name, we don't want the
            # we don't want the support_code to be included
            import base_info
            res = base_info.base_info()
        return res
        
    def py_to_c_code(self):
        return wx_to_c_template % self.template_vars()

    #def c_to_py_code(self):
    #    return simple_c_to_py_template % self.template_vars()
                    
    def type_spec(self,name,value):
        # factory
        class_name = value.this.split('_')[-2]
        new_spec = self.__class__(class_name)
        new_spec.name = name        
        return new_spec

    def __cmp__(self,other):
        #only works for equal
        res = -1
        try:
            res = cmp(self.name,other.name) or \
                  cmp(self.__class__, other.__class__) or \
                  cmp(self.class_name, other.class_name) or \
                  cmp(self.type_name,other.type_name)
        except:
            pass
        return res

#!/usr/bin/env python
import os,sys
from scipy_distutils.core import setup
from scipy_distutils.misc_util import get_path, merge_config_dicts
from scipy_distutils.misc_util import package_config

# Enough changes to bump the number.  We need a global method for
# versioning
version = "0.3.0"
   
def stand_alone_package(with_dependencies = 0):
    path = get_path(__name__)
    old_path = os.getcwd()
    os.chdir(path)
    try:
        primary =     ['weave']
        if with_dependencies:
            dependencies= ['scipy_distutils','scipy_test','scipy_base']       
        else:
            dependencies = []    
        
        print 'dep:', dependencies
        config_dict = package_config(primary,dependencies)
        config_dict['name'] = 'weave'
        setup (version = version,
               description = "Tools for inlining C/C++ in Python",
               author = "Eric Jones",
               author_email = "eric@enthought.com",
               licence = "SciPy License (BSD Style)",
               url = 'http://www.scipy.org',
               **config_dict
               )        
    finally:
        os.chdir(old_path)

if __name__ == '__main__':
    import sys
    if '--without-dependencies' in sys.argv:
        with_dependencies = 0
        sys.argv.remove('--without-dependencies')
    else:
        with_dependencies = 1    
    stand_alone_package(with_dependencies)
    

""" This converter works with classes protected by a namespace with
    SWIG pointers (Python strings).  To use it to wrap classes in
    a C++ namespace called "ft", use the following:
    
    class ft_converter(cpp_namespace_converter):
        namespace = 'ft::'        
"""

from weave import common_info
from weave import  base_info
from weave.base_spec import base_converter

cpp_support_template = \
"""
static %(cpp_struct)s* convert_to_%(cpp_clean_struct)s(PyObject* py_obj,char* name)
{
    %(cpp_struct)s *cpp_ptr = 0;
    char* str = PyString_AsString(py_obj);
    if (!str)
        handle_conversion_error(py_obj,"%(cpp_struct)s", name);
    // work on this error reporting...
    //std::cout << "in:" << name << " " py_obj << std::endl;
    if (SWIG_GetPtr(str,(void **) &cpp_ptr,"_%(cpp_struct)s_p"))
    {
        handle_conversion_error(py_obj,"%(cpp_struct)s", name);
    }
    //std::cout << "out:" << name << " " << str << std::endl;
    return cpp_ptr;
}    

static %(cpp_struct)s* py_to_%(cpp_clean_struct)s(PyObject* py_obj,char* name)
{
    %(cpp_struct)s *cpp_ptr;
    char* str = PyString_AsString(py_obj);
    if (!str)
        handle_conversion_error(py_obj,"%(cpp_struct)s", name);
    // work on this error reporting...
    if (SWIG_GetPtr(str,(void **) &cpp_ptr,"_%(cpp_struct)s_p"))
    {
        handle_conversion_error(py_obj,"%(cpp_struct)s", name);
    }
    return cpp_ptr;
}    

std::string %(cpp_clean_struct)s_to_py( %(cpp_struct)s* cpp_ptr)
{
    char ptr_string[%(ptr_string_len)s]; 
    SWIG_MakePtr(ptr_string, cpp_ptr, "_%(cpp_struct)s_p");
    return std::string(ptr_string);
}              

"""        

class cpp_namespace_converter(base_converter):
    _build_information = [common_info.swig_info()]
    def __init__(self,class_name=None):
        self.type_name = 'unkown cpp_object'
        self.name =  'no name'        
        if class_name:
            # customize support_code for whatever type I was handed.
            clean_name = class_name.replace('::','_')
            clean_name = clean_name.replace('<','_')
            clean_name = clean_name.replace('>','_')
            clean_name = clean_name.replace(' ','_')
            # should be enough for 64 bit machines
            str_len = len(clean_name) + 20 
            vals = {'cpp_struct': class_name,
                    'cpp_clean_struct': clean_name,
                    'ptr_string_len': str_len }
            specialized_support = cpp_support_template % vals
            custom = base_info.base_info()
            custom._support_code = [specialized_support]
            self._build_information = self._build_information + [custom]
            self.type_name = class_name

    def type_match(self,value):
        try:
            cpp_ident = value.split('_')[2]
            if cpp_ident.find(self.namespace) != -1:
                return 1
        except:
            pass
        return 0
            
    def type_spec(self,name,value):
        # factory
        ptr_fields = value.split('_')
        class_name = '_'.join(ptr_fields[2:-1])
        new_spec = self.__class__(class_name)
        new_spec.name = name        
        return new_spec
        
    def declaration_code(self,inline=0):
        type = self.type_name
        clean_type = type.replace('::','_')
        name = self.name
        var_name = self.retrieve_py_variable(inline)
        template = '%(type)s *%(name)s = '\
                   'convert_to_%(clean_type)s(%(var_name)s,"%(name)s");\n'
        code = template % locals()
        return code
        
    def __repr__(self):
        msg = "(%s:: name: %s)" % (self.type_name,self.name)
        return msg
    def __cmp__(self,other):
        #only works for equal
        return cmp(self.name,other.name) or \
               cmp(self.__class__, other.__class__) or \
               cmp(self.type_name,other.type_name)

#**************************************************************************#
#* FILE   **************    accelerate_tools.py    ************************#
#**************************************************************************#
#* Author: Patrick Miller February  9 2002                                *#
#**************************************************************************#
"""
accelerate_tools contains the interface for on-the-fly building of
C++ equivalents to Python functions.
"""
#**************************************************************************#

from types import InstanceType,FunctionType,IntType,FloatType,StringType,TypeType,XRangeType
import inspect
import md5
import weave
import imp
from bytecodecompiler import CXXCoder,Type_Descriptor,Function_Descriptor

def CStr(s):
    "Hacky way to get legal C string from Python string"
    if s is None: return '""'
    assert type(s) == StringType,"Only None and string allowed"
    r = repr('"'+s) # Better for embedded quotes
    return '"'+r[2:-1]+'"'


##################################################################
#                         CLASS INSTANCE                         #
##################################################################
class Instance(Type_Descriptor):
    cxxtype = 'PyObject*'
    
    def __init__(self,prototype):
	self.prototype	= prototype
	return

    def check(self,s):
        return "PyInstance_Check(%s)"%s

    def inbound(self,s):
        return s

    def outbound(self,s):
        return s,0

    def get_attribute(self,name):
        proto = getattr(self.prototype,name)
        T = lookup_type(proto)
        code = 'tempPY = PyObject_GetAttrString(%%(rhs)s,"%s");\n'%name
        convert = T.inbound('tempPY')
        code += '%%(lhsType)s %%(lhs)s = %s;\n'%convert
        return T,code

    def set_attribute(self,name):
        proto = getattr(self.prototype,name)
        T = lookup_type(proto)
        convert,owned = T.outbound('%(rhs)s')
        code = 'tempPY = %s;'%convert
        if not owned:
            code += ' Py_INCREF(tempPY);'
        code += ' PyObject_SetAttrString(%%(lhs)s,"%s",tempPY);'%name
        code += ' Py_DECREF(tempPY);\n'
        return T,code

##################################################################
#                          CLASS BASIC                           #
##################################################################
class Basic(Type_Descriptor):
    owned = 1
    def check(self,s):
        return "%s(%s)"%(self.checker,s)
    def inbound(self,s):
        return "%s(%s)"%(self.inbounder,s)
    def outbound(self,s):
        return "%s(%s)"%(self.outbounder,s),self.owned

class Basic_Number(Basic):
    def literalizer(self,s):
        return str(s)
    def binop(self,symbol,a,b):
        assert symbol in ['+','-','*','/'],symbol
        return '%s %s %s'%(a,symbol,b),self

class Integer(Basic_Number):
    cxxtype = "long"
    checker = "PyInt_Check"
    inbounder = "PyInt_AsLong"
    outbounder = "PyInt_FromLong"

class Double(Basic_Number):
    cxxtype = "double"
    checker = "PyFloat_Check"
    inbounder = "PyFloat_AsDouble"
    outbounder = "PyFloat_FromDouble"

class String(Basic):
    cxxtype = "char*"
    checker = "PyString_Check"
    inbounder = "PyString_AsString"
    outbounder = "PyString_FromString"

    def literalizer(self,s):
        return CStr(s)

# -----------------------------------------------
# Singletonize the type names
# -----------------------------------------------
Integer = Integer()
Double = Double()
String = String()

import Numeric

class Vector(Type_Descriptor):
    cxxtype = 'PyArrayObject*'
    refcount = 1
    dims = 1
    module_init_code = 'import_array();\n'
    inbounder = "(PyArrayObject*)"
    outbounder = "(PyObject*)"
    owned = 0 # Convertion is by casting!

    prerequisites = Type_Descriptor.prerequisites+\
                   ['#include "Numeric/arrayobject.h"']
    dims = 1
    def check(self,s):
        return "PyArray_Check(%s) && ((PyArrayObject*)%s)->nd == %d &&  ((PyArrayObject*)%s)->descr->type_num == %s"%(
            s,s,self.dims,s,self.typecode)

    def inbound(self,s):
        return "%s(%s)"%(self.inbounder,s)
    def outbound(self,s):
        return "%s(%s)"%(self.outbounder,s),self.owned

    def getitem(self,A,v,t):
        assert self.dims == len(v),'Expect dimension %d'%self.dims
        code = '*((%s*)(%s->data'%(self.cxxbase,A)
        for i in range(self.dims):
            # assert that ''t[i]'' is an integer
            code += '+%s*%s->strides[%d]'%(v[i],A,i)
        code += '))'
        return code,self.pybase
    def setitem(self,A,v,t):
        return self.getitem(A,v,t)

class matrix(Vector):
    dims = 2

class IntegerVector(Vector):
    typecode = 'PyArray_INT'
    cxxbase = 'int'
    pybase = Integer

class Integermatrix(matrix):
    typecode = 'PyArray_INT'
    cxxbase = 'int'
    pybase = Integer

class LongVector(Vector):
    typecode = 'PyArray_LONG'
    cxxbase = 'long'
    pybase = Integer

class Longmatrix(matrix):
    typecode = 'PyArray_LONG'
    cxxbase = 'long'
    pybase = Integer

class DoubleVector(Vector):
    typecode = 'PyArray_DOUBLE'
    cxxbase = 'double'
    pybase = Double

class Doublematrix(matrix):
    typecode = 'PyArray_DOUBLE'
    cxxbase = 'double'
    pybase = Double


##################################################################
#                          CLASS XRANGE                          #
##################################################################
class XRange(Type_Descriptor):
    cxxtype = 'XRange'
    prerequisites = ['''
    class XRange {
    public:
    XRange(long aLow, long aHigh, long aStep=1)
    : low(aLow),high(aHigh),step(aStep)
    {
    }
    XRange(long aHigh)
    : low(0),high(aHigh),step(1)
    {
    }
    long low;
    long high;
    long step;
    };''']

# -----------------------------------------------
# Singletonize the type names
# -----------------------------------------------
IntegerVector = IntegerVector()
Integermatrix = Integermatrix()
LongVector = LongVector()
Longmatrix = Longmatrix()
DoubleVector = DoubleVector()
Doublematrix = Doublematrix()
XRange = XRange()


typedefs = {
    IntType: Integer,
    FloatType: Double,
    StringType: String,
    (Numeric.ArrayType,1,'i'): IntegerVector,
    (Numeric.ArrayType,2,'i'): Integermatrix,
    (Numeric.ArrayType,1,'l'): LongVector,
    (Numeric.ArrayType,2,'l'): Longmatrix,
    (Numeric.ArrayType,1,'d'): DoubleVector,
    (Numeric.ArrayType,2,'d'): Doublematrix,
    XRangeType : XRange,
    }

import math
functiondefs = {
    (len,(String,)):
    Function_Descriptor(code='strlen(%s)',return_type=Integer),
    
    (len,(LongVector,)):
    Function_Descriptor(code='PyArray_Size((PyObject*)%s)',return_type=Integer),

    (float,(Integer,)):
    Function_Descriptor(code='(double)(%s)',return_type=Double),
    
    (range,(Integer,Integer)):
    Function_Descriptor(code='XRange(%s)',return_type=XRange),

    (range,(Integer)):
    Function_Descriptor(code='XRange(%s)',return_type=XRange),

    (math.sin,(Double,)):
    Function_Descriptor(code='sin(%s)',return_type=Double),

    (math.cos,(Double,)):
    Function_Descriptor(code='cos(%s)',return_type=Double),

    (math.sqrt,(Double,)):
    Function_Descriptor(code='sqrt(%s)',return_type=Double),
    }
    


##################################################################
#                      FUNCTION LOOKUP_TYPE                      #
##################################################################
def lookup_type(x):
    T = type(x)
    try:
        return typedefs[T]
    except:
        import Numeric
        if isinstance(T,Numeric.ArrayType):
            return typedefs[(T,len(x.shape),x.typecode())]
        elif T == InstanceType:
            return Instance(x)
        else:
            raise NotImplementedError,T

##################################################################
#                        class ACCELERATE                        #
##################################################################
class accelerate:
    
    def __init__(self, function, *args, **kw):
        assert type(function) == FunctionType
        self.function = function
        self.module = inspect.getmodule(function)
        if self.module is None:
            import __main__
            self.module = __main__
        self.__call_map = {}

    def __cache(self,*args):
        raise TypeError

    def __call__(self,*args):
        try:
            return self.__cache(*args)
        except TypeError:
            # Figure out type info -- Do as tuple so its hashable
            signature = tuple( map(lookup_type,args) )
            
            # If we know the function, call it
            try:
                fast = self.__call_map[signature]
            except:
                fast = self.singleton(signature)
                self.__cache = fast
                self.__call_map[signature] = fast
            return fast(*args)

    def signature(self,*args):
        # Figure out type info -- Do as tuple so its hashable
        signature = tuple( map(lookup_type,args) )
        return self.singleton(signature)


    def singleton(self,signature):
        identifier = self.identifier(signature)
        
        # Generate a new function, then call it
        f = self.function

        # See if we have an accelerated version of module
        try:
            print 'lookup',self.module.__name__+'_weave'
            accelerated_module = __import__(self.module.__name__+'_weave')
            print 'have accelerated',self.module.__name__+'_weave'
            fast = getattr(accelerated_module,identifier)
            return fast
        except ImportError:
            accelerated_module = None
        except AttributeError:
            pass

        P = self.accelerate(signature,identifier)

        E = weave.ext_tools.ext_module(self.module.__name__+'_weave')
        E.add_function(P)
        E.generate_file()
        weave.build_tools.build_extension(self.module.__name__+'_weave.cpp',verbose=2)

        if accelerated_module:
            raise NotImplementedError,'Reload'
        else:
            accelerated_module = __import__(self.module.__name__+'_weave')

        fast = getattr(accelerated_module,identifier)
        return fast

    def identifier(self,signature):
        # Build an MD5 checksum
        f = self.function
        co = f.func_code
        identifier = str(signature)+\
                     str(co.co_argcount)+\
                     str(co.co_consts)+\
                     str(co.co_varnames)+\
                     co.co_code
        return 'F'+md5.md5(identifier).hexdigest()
        
    def accelerate(self,signature,identifier):
        P = Python2CXX(self.function,signature,name=identifier)
        return P

    def code(self,*args):
        if len(args) != self.function.func_code.co_argcount:
            raise TypeError,'%s() takes exactly %d arguments (%d given)'%(
                self.function.__name__,
                self.function.func_code.co_argcount,
                len(args))
        signature = tuple( map(lookup_type,args) )
        ident = self.function.__name__
        return self.accelerate(signature,ident).function_code()
        

##################################################################
#                        CLASS PYTHON2CXX                        #
##################################################################
class Python2CXX(CXXCoder):
    def typedef_by_value(self,v):
        T = lookup_type(v)
        if T not in self.used:
            self.used.append(T)
        return T

    def function_by_signature(self,signature):
        descriptor = functiondefs[signature]
        if descriptor.return_type not in self.used:
            self.used.append(descriptor.return_type)
        return descriptor

    def __init__(self,f,signature,name=None):
        # Make sure function is a function
        import types
        assert type(f) == FunctionType
        # and check the input type signature
        assert reduce(lambda x,y: x and y,
                      map(lambda x: isinstance(x,Type_Descriptor),
                          signature),
                      1),'%s not all type objects'%signature
        self.arg_specs = []
        self.customize = weave.base_info.custom_info()

        CXXCoder.__init__(self,f,signature,name)

        return

    def function_code(self):
        code = self.wrapped_code()
        for T in self.used:
            if T != None and T.module_init_code:
                self.customize.add_module_init_code(T.module_init_code)
        return code

    def python_function_definition_code(self):
        return '{ "%s", wrapper_%s, METH_VARARGS, %s },\n'%(
            self.name,
            self.name,
            CStr(self.function.__doc__))

from Numeric import *

# The following try/except so that non-SciPy users can still use blitz
try:
    from scipy_base.fastumath import *
except:
    pass # scipy_base.fastumath not available    

from ast_tools import *
from types import *
import sys

def time_it():
    import time
    
    expr = "ex[:,1:,1:] =   ca_x[:,1:,1:] * ex[:,1:,1:]" \
                         "+ cb_y_x[:,1:,1:] * (hz[:,1:,1:] - hz[:,:-1,1:])" \
                         "- cb_z_x[:,1:,1:] * (hy[:,1:,1:] - hy[:,1:,:-1])"        
    ex = ones((10,10,10),typecode=Float32)
    ca_x = ones((10,10,10),typecode=Float32)
    cb_y_x = ones((10,10,10),typecode=Float32)
    cb_z_x = ones((10,10,10),typecode=Float32)
    hz = ones((10,10,10),typecode=Float32)
    hy = ones((10,10,10),typecode=Float32)
    
    N = 1
    t1 = time.time()
    for i in range(N):
        passed = check_expr(expr,locals())
    t2 = time.time()
    print 'time per call:', (t2 - t1)/N
    print 'passed:', passed
    
def check_expr(expr,local_vars,global_vars={}):
    """ Currently only checks expressions (not suites).
        Doesn't check that lhs = rhs. checked by compiled func though
    """
    values ={}
    
    #first handle the globals
    for var,val in global_vars.items():
        if type(val) in [ArrayType]: 
            values[var] = dummy_array(val,name=var)
        elif type(val) in [IntType,LongType,FloatType,ComplexType]:    
            values[var] = val
    #now handle the locals        
    for var,val in local_vars.items():
        if type(val) in [ArrayType]: 
            values[var] = dummy_array(val,name=var)
        elif type(val) in [IntType,LongType,FloatType,ComplexType]:    
            values[var] = val
    exec(expr,values)
    try:
        exec(expr,values)
    except:
        try:
            eval(expr,values)
        except:
            return 0    
    return 1                
        
empty = array(())
empty_slice = slice(None)

def make_same_length(x,y):
    try:
        Nx = len(x)
    except:
        Nx = 0
    try:
        Ny = len(y)
    except:
        Ny = 0
    if Nx == Ny == 0:
        return empty,empty
    elif Nx == Ny:
        return asarray(x),asarray(y)
    else:    
        diff = abs(Nx - Ny)
        front = ones(diff,Int)
        if Nx > Ny:
            return asarray(x), concatenate((front,y))
        elif Ny > Nx:
            return concatenate((front,x)),asarray(y)            

def binary_op_size(xx,yy):
    """ This returns the resulting size from operating on xx, and yy
        with a binary operator.  It accounts for broadcasting, and
        throws errors if the array sizes are incompatible.
    """
    x,y = make_same_length(xx,yy)
    res = zeros(len(x))
    for i in range(len(x)):
        if x[i] == y[i]:
            res[i] = x[i]
        elif x[i] == 1:
            res[i] = y[i]
        elif y[i] == 1:
            res[i] = x[i]
        else:
            # offer more information here about which variables.
            raise ValueError, "frames are not aligned"
    return res    
class dummy_array:
    def __init__(self,ary,ary_is_shape = 0,name=None):
        self.name = name
        if ary_is_shape:
            self.shape = ary
            #self.shape = asarray(ary)
        else:
            try:
                self.shape = shape(ary)
            except:
                self.shape = empty
        #self.value = ary        
    def binary_op(self,other):
        try: 
            x = other.shape
        except AttributeError:
            x = empty                      
        new_shape = binary_op_size(self.shape,x)
        return dummy_array(new_shape,1)
    def __cmp__(self,other):
        # This isn't an exact compare, but does work for == 
        # cluge for Numeric
        if type(other) in [IntType,LongType,FloatType,ComplexType]:
            return 0
        if len(self.shape) == len(other.shape) == 0:
            return 0
        return not alltrue(equal(self.shape,other.shape))

    def __add__(self,other): return self.binary_op(other)
    def __radd__(self,other): return self.binary_op(other)
    def __sub__(self,other): return self.binary_op(other)
    def __rsub__(self,other): return self.binary_op(other)
    def __mul__(self,other): return self.binary_op(other)
    def __rmul__(self,other): return self.binary_op(other)
    def __div__(self,other): return self.binary_op(other)
    def __rdiv__(self,other): return self.binary_op(other)
    def __mod__(self,other): return self.binary_op(other)
    def __rmod__(self,other): return self.binary_op(other)
    def __lshift__(self,other): return self.binary_op(other)
    def __rshift__(self,other): return self.binary_op(other)
    # unary ops
    def __neg__(self,other): return self
    def __pos__(self,other): return self
    def __abs__(self,other): return self
    def __invert__(self,other): return self   
    # Not sure what to do with coersion ops.  Ignore for now.
    #
    # not currently supported by compiler.
    # __divmod__
    # __pow__
    # __rpow__
    # __and__
    # __or__
    # __xor__
    # item access and slicing    
    def __setitem__(self,indices,val):
        #ignore for now
        pass
    def __len__(self):
        return self.shape[0]
    def __getslice__(self,i,j):
        # enabling the following would make class compatible with
        # lists.  Its current incarnation is compatible with arrays.
        # Both this and Numeric should have this FIXED to correspond
        # to lists.
        #i = max(i, 0); j = max(j, 0)
        return self.__getitem__((slice(i,j),))
    def __getitem__(self,indices):
        # ayeyaya this is a mess
        #print indices, type(indices), indices.shape       
        if type(indices) is not TupleType:
            indices = (indices,)
        if Ellipsis in indices:
            raise IndexError, "Ellipsis not currently supported"
        new_dims = []            
        dim = 0    
        for index in indices:
            try:
                dim_len = self.shape[dim]
            except IndexError:
                raise IndexError, "To many indices specified"
                
            #if (type(index) is SliceType and index.start == index.stop == index.step):
            if (index is empty_slice):
                slc_len = dim_len
            elif type(index) is SliceType:
                beg,end,step = index.start,index.stop,index.step                
                # handle if they are dummy arrays
                #if hasattr(beg,'value') and type(beg.value) != ArrayType:
                #    beg = beg.value
                #if hasattr(end,'value') and type(end.value) != ArrayType:
                #    end = end.value
                #if hasattr(step,'value') and type(step.value) != ArrayType:
                #    step = step.value    
                if beg is None: beg = 0
                if end == sys.maxint or  end is None:
                    end = dim_len
                if step is None: 
                    step = 1
                    
                if beg < 0: beg += dim_len
                if end < 0: end += dim_len
                # the following is list like behavior,
                # which isn't adhered to by arrays. 
                # FIX THIS ANOMOLY IN NUMERIC!
                if beg < 0: beg = 0
                if beg > dim_len: beg = dim_len
                if end < 0: end = 0
                if end > dim_len: end = dim_len
                # This is rubbish. 
                if  beg == end:
                    beg,end,step = 0,0,1
                elif  beg >= dim_len and step > 0:
                    beg,end,step = 0,0,1
                #elif index.step > 0 and beg <= end:
                elif step > 0 and beg <= end:
                    pass #slc_len = abs(divide(end-beg-1,step)+1)     
                # handle [::-1] and [-1::-1] correctly    
                #elif index.step > 0 and beg > end:
                elif step > 0 and beg > end:
                    beg,end,step = 0,0,1
                elif(step < 0 and index.start is None and index.stop is None):
                    beg,end,step = 0,dim_len,-step
                elif(step < 0 and index.start is None):
                    # +1 because negative stepping is inclusive
                    beg,end,step = end+1,dim_len,-step 
                elif(step < 0 and index.stop is None):
                    beg,end,step = 0,beg+1,-step
                elif(step < 0 and beg > end):                    
                    beg,end,step = end,beg,-step
                elif(step < 0 and beg < end):                    
                    beg,end,step = 0,0,-step
                slc_len = abs(divide(end-beg-1,step)+1)
                new_dims.append(slc_len)
            else:
                if index < 0: index += dim_len
                if index >=0 and index < dim_len:
                    #this reduces the array dimensions by one
                    pass
                else:
                    raise IndexError, "Index out of range"            
            dim += 1        
        new_dims.extend(self.shape[dim:])
        if 0 in new_dims:
            raise IndexError, "Zero length slices not currently supported"
        return dummy_array(new_dims,1)
    def __repr__(self):
        val = str((self.name, str(self.shape)))
        return val    

def unary(ary):
    return ary

def not_implemented(ary):
    return ary
    
#all imported from Numeric and need to be reassigned.
unary_op = [arccos, arcsin, arctan, cos, cosh, sin, sinh, 
            exp,ceil,floor,fabs,log,log10,sqrt]

unsupported = [argmin,argmax, argsort,around, absolute,sign,negative,floor]

for func in unary_op:
    func = unary
    
for func in unsupported:
    func = not_implemented
    
def reduction(ary,axis=0):
    if axis < 0:
        axis += len(ary.shape) 
    if axis < 0 or axis >= len(ary.shape):
        raise ValueError, "Dimension not in array"        
    new_dims = list(ary.shape[:axis]) + list(ary.shape[axis+1:])
    return dummy_array(new_dims,1)           

# functions currently not supported by compiler
# reductions are gonna take some array reordering for the general case,
# so this is gonna take some thought (probably some tree manipulation).
def take(ary,axis=0): raise NotImplemented
# and all the rest

"""
    base_info holds classes that define the information
    needed for building C++ extension modules for Python that
    handle different data types.  The information includes
    such as include files, libraries, and even code snippets.
    
    base_info -- base class for cxx_info, blitz_info, etc.                  
    info_list -- a handy list class for working with multiple
                 info classes at the same time.            
"""
import os
import UserList

class base_info:
    _warnings =[]
    _headers = []
    _include_dirs = []
    _libraries = []
    _library_dirs = []
    _support_code = []
    _module_init_code = []
    _sources = []
    _define_macros = []
    _undefine_macros = []
    _extra_compile_args = []
    _extra_link_args = []
    compiler = ''
    def set_compiler(self,compiler):
        self.check_compiler(compiler)
        self.compiler = compiler
    # it would probably be better to specify what the arguments are
    # to avoid confusion, but I don't think these classes will get
    # very complicated, and I don't really know the variety of things
    # that should be passed in at this point.
    def check_compiler(self,compiler):
        pass        
    def warnings(self):   
        return self._warnings
    def headers(self):   
        return self._headers
    def include_dirs(self):
        return self._include_dirs
    def libraries(self):
        return self._libraries
    def library_dirs(self):
        return self._library_dirs
    def support_code(self):
        return self._support_code
    def module_init_code(self):
        return self._module_init_code
    def sources(self):
        return self._sources
    def define_macros(self):
        return self._define_macros
    def undefine_macros(self):
        return self._undefine_macros
    def extra_compile_args(self):
        return self._extra_compile_args
    def extra_link_args(self):
        return self._extra_link_args        
        
class custom_info(base_info):
    def __init__(self):
        self._warnings =[]
        self._headers = []
        self._include_dirs = []
        self._libraries = []
        self._library_dirs = []
        self._support_code = []
        self._module_init_code = []
        self._sources = []
        self._define_macros = []
        self._undefine_macros = []
        self._extra_compile_args = []
        self._extra_link_args = []

    def add_warning(self,warning):
        self._warnings.append(warning)
    def add_header(self,header):
        self._headers.append(header)
    def add_include_dir(self,include_dir):
        self._include_dirs.append(include_dir)
    def add_library(self,library):
        self._libraries.append(library)
    def add_library_dir(self,library_dir):
        self._library_dirs.append(library_dir)
    def add_support_code(self,support_code):
        self._support_code.append(support_code)
    def add_module_init_code(self,module_init_code):
        self._module_init_code.append(module_init_code)
    def add_source(self,source):
        self._sources.append(source)
    def add_define_macro(self,define_macro):
        self._define_macros.append(define_macro)
    def add_undefine_macro(self,undefine_macro):
        self._undefine_macros.append(undefine_macro)    
    def add_extra_compile_arg(self,compile_arg):
        return self._extra_compile_args.append(compile_arg)
    def add_extra_link_arg(self,link_arg):
        return self._extra_link_args.append(link_arg)        

class info_list(UserList.UserList):
    def get_unique_values(self,attribute):
        all_values = []        
        for info in self:
            vals = eval('info.'+attribute+'()')
            all_values.extend(vals)
        return unique_values(all_values)

    def extra_compile_args(self):
        return self.get_unique_values('extra_compile_args')
    def extra_link_args(self):
        return self.get_unique_values('extra_link_args')
    def sources(self):
        return self.get_unique_values('sources')    
    def define_macros(self):
        return self.get_unique_values('define_macros')
    def sources(self):
        return self.get_unique_values('sources')
    def warnings(self):
        return self.get_unique_values('warnings')
    def headers(self):
        return self.get_unique_values('headers')
    def include_dirs(self):
        return self.get_unique_values('include_dirs')
    def libraries(self):
        return self.get_unique_values('libraries')
    def library_dirs(self):
        return self.get_unique_values('library_dirs')
    def support_code(self):
        return self.get_unique_values('support_code')
    def module_init_code(self):
        return self.get_unique_values('module_init_code')

def unique_values(lst):
    all_values = []        
    for value in lst:
        if value not in all_values:
            all_values.append(value)
    return all_values


# This code allows one to use SWIG wrapped objects from weave.  This
# code is specific to SWIG-1.3 and above where things are different.
# The code is basically all copied out from the SWIG wrapper code but
# it has been hand edited for brevity.
#
# Prabhu Ramachandran <prabhu@aero.iitm.ernet.in>

swigptr2_code = """

#include "Python.h"

/*************************************************************** -*- c -*-
 * python/precommon.swg
 *
 * Rename all exported symbols from common.swg, to avoid symbol
 * clashes if multiple interpreters are included
 *
 ************************************************************************/

#define SWIG_TypeCheck       SWIG_Python_TypeCheck
#define SWIG_TypeCast        SWIG_Python_TypeCast
#define SWIG_TypeName        SWIG_Python_TypeName
#define SWIG_TypeQuery       SWIG_Python_TypeQuery
#define SWIG_PackData        SWIG_Python_PackData 
#define SWIG_UnpackData      SWIG_Python_UnpackData 


/***********************************************************************
 * common.swg
 *
 *     This file contains generic SWIG runtime support for pointer
 *     type checking as well as a few commonly used macros to control
 *     external linkage.
 *
 * Author : David Beazley (beazley@cs.uchicago.edu)
 *
 * Copyright (c) 1999-2000, The University of Chicago
 * 
 * This file may be freely redistributed without license or fee provided
 * this copyright message remains intact.
 ************************************************************************/

#include <string.h>

#if defined(_WIN32) || defined(__WIN32__) || defined(__CYGWIN__)
#  if defined(_MSC_VER) || defined(__GNUC__)
#    if defined(STATIC_LINKED)
#      define SWIGEXPORT(a) a
#      define SWIGIMPORT(a) extern a
#    else
#      define SWIGEXPORT(a) __declspec(dllexport) a
#      define SWIGIMPORT(a) extern a
#    endif
#  else
#    if defined(__BORLANDC__)
#      define SWIGEXPORT(a) a _export
#      define SWIGIMPORT(a) a _export
#    else
#      define SWIGEXPORT(a) a
#      define SWIGIMPORT(a) a
#    endif
#  endif
#else
#  define SWIGEXPORT(a) a
#  define SWIGIMPORT(a) a
#endif

#ifdef SWIG_GLOBAL
#  define SWIGRUNTIME(a) SWIGEXPORT(a)
#else
#  define SWIGRUNTIME(a) static a
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef void *(*swig_converter_func)(void *);
typedef struct swig_type_info *(*swig_dycast_func)(void **);

typedef struct swig_type_info {
  const char             *name;
  swig_converter_func     converter;
  const char             *str;
  void                   *clientdata;
  swig_dycast_func        dcast;
  struct swig_type_info  *next;
  struct swig_type_info  *prev;
} swig_type_info;

#ifdef SWIG_NOINCLUDE

SWIGIMPORT(swig_type_info *) SWIG_TypeCheck(char *c, swig_type_info *);
SWIGIMPORT(void *)           SWIG_TypeCast(swig_type_info *, void *);
SWIGIMPORT(const char *)     SWIG_TypeName(const swig_type_info *);
SWIGIMPORT(swig_type_info *) SWIG_TypeQuery(const char *);
SWIGIMPORT(char *)           SWIG_PackData(char *, void *, int);
SWIGIMPORT(char *)           SWIG_UnpackData(char *, void *, int);

#else

static swig_type_info *swig_type_list = 0;

/* Check the typename */
SWIGRUNTIME(swig_type_info *) 
SWIG_TypeCheck(char *c, swig_type_info *ty) {
  swig_type_info *s;
  if (!ty) return 0;        /* Void pointer */
  s = ty->next;             /* First element always just a name */
  do {
    if (strcmp(s->name,c) == 0) {
      if (s == ty->next) return s;
      /* Move s to the top of the linked list */
      s->prev->next = s->next;
      if (s->next) {
        s->next->prev = s->prev;
      }
      /* Insert s as second element in the list */
      s->next = ty->next;
      if (ty->next) ty->next->prev = s;
      ty->next = s;
      s->prev = ty;
      return s;
    }
    s = s->next;
  } while (s && (s != ty->next));
  return 0;
}

/* Cast a pointer up an inheritance hierarchy */
SWIGRUNTIME(void *) 
SWIG_TypeCast(swig_type_info *ty, void *ptr) {
  if ((!ty) || (!ty->converter)) return ptr;
  return (*ty->converter)(ptr);
}

/* Return the name associated with this type */
SWIGRUNTIME(const char *)
SWIG_TypeName(const swig_type_info *ty) {
  return ty->name;
}

/* 
   Compare two type names skipping the space characters, therefore
   "char*" == "char *" and "Class<int>" == "Class<int >", etc.

   Return 0 when the two name types are equivalent, as in
   strncmp, but skipping ' '.
*/
static int
SWIG_TypeNameComp(const char *f1, const char *l1,
		  const char *f2, const char *l2) {
  for (;(f1 != l1) && (f2 != l2); ++f1, ++f2) {
    while ((*f1 == ' ') && (f1 != l1)) ++f1;
    while ((*f2 == ' ') && (f2 != l2)) ++f2;
    if (*f1 != *f2) return *f1 - *f2;
  }
  return (l1 - f1) - (l2 - f2);
}

/*
  Check type equivalence in a name list like <name1>|<name2>|...
*/
static int
SWIG_TypeEquiv(const char *nb, const char *tb) {
  int equiv = 0;
  const char* te = tb + strlen(tb);
  const char* ne = nb;
  while (!equiv && *ne) {
    for (nb = ne; *ne; ++ne) {
      if (*ne == '|') break;
    }
    equiv = SWIG_TypeNameComp(nb, ne, tb, te) == 0;
    if (*ne) ++ne;
  }
  return equiv;
}
  

/* Search for a swig_type_info structure */
SWIGRUNTIME(swig_type_info *)
SWIG_TypeQuery(const char *name) {
  swig_type_info *ty = swig_type_list;
  while (ty) {
    if (ty->str && (SWIG_TypeEquiv(ty->str,name))) return ty;
    if (ty->name && (strcmp(name,ty->name) == 0)) return ty;
    ty = ty->prev;
  }
  return 0;
}

/* Pack binary data into a string */
SWIGRUNTIME(char *)
SWIG_PackData(char *c, void *ptr, int sz) {
  static char hex[17] = "0123456789abcdef";
  int i;
  unsigned char *u = (unsigned char *) ptr;
  register unsigned char uu;
  for (i = 0; i < sz; i++,u++) {
    uu = *u;
    *(c++) = hex[(uu & 0xf0) >> 4];
    *(c++) = hex[uu & 0xf];
  }
  return c;
}

/* Unpack binary data from a string */
SWIGRUNTIME(char *)
SWIG_UnpackData(char *c, void *ptr, int sz) {
  register unsigned char uu = 0;
  register int d;
  unsigned char *u = (unsigned char *) ptr;
  int i;
  for (i = 0; i < sz; i++, u++) {
    d = *(c++);
    if ((d >= '0') && (d <= '9'))
      uu = ((d - '0') << 4);
    else if ((d >= 'a') && (d <= 'f'))
      uu = ((d - ('a'-10)) << 4);
    d = *(c++);
    if ((d >= '0') && (d <= '9'))
      uu |= (d - '0');
    else if ((d >= 'a') && (d <= 'f'))
      uu |= (d - ('a'-10));
    *u = uu;
  }
  return c;
}

#endif

#ifdef __cplusplus
}
#endif

/***********************************************************************
 * python.swg
 *
 *     This file contains the runtime support for Python modules
 *     and includes code for managing global variables and pointer
 *     type checking.
 *
 * Author : David Beazley (beazley@cs.uchicago.edu)
 ************************************************************************/

#include "Python.h"

#ifdef __cplusplus
extern "C" {
#endif

#define SWIG_PY_INT     1
#define SWIG_PY_FLOAT   2
#define SWIG_PY_STRING  3
#define SWIG_PY_POINTER 4
#define SWIG_PY_BINARY  5

/* Flags for pointer conversion */

#define SWIG_POINTER_EXCEPTION     0x1
#define SWIG_POINTER_DISOWN        0x2

/* Exception handling in wrappers */
#define SWIG_fail   goto fail

/* Constant information structure */
typedef struct swig_const_info {
    int type;
    char *name;
    long lvalue;
    double dvalue;
    void   *pvalue;
    swig_type_info **ptype;
} swig_const_info;

/* Common SWIG API */
#define SWIG_ConvertPtr(obj, pp, type, flags) \
  SWIG_Python_ConvertPtr(obj, pp, type, flags)
#define SWIG_NewPointerObj(p, type, flags) \
  SWIG_Python_NewPointerObj(p, type, flags)
#define SWIG_MustGetPtr(p, type, argnum, flags) \
  SWIG_Python_MustGetPtr(p, type, argnum, flags)
 

typedef double (*py_objasdbl_conv)(PyObject *obj);

#ifdef SWIG_NOINCLUDE

SWIGIMPORT(int)               SWIG_Python_ConvertPtr(PyObject *, void **, swig_type_info *, int);
SWIGIMPORT(PyObject *)        SWIG_Python_NewPointerObj(void *, swig_type_info *,int own);
SWIGIMPORT(void *)            SWIG_Python_MustGetPtr(PyObject *, swig_type_info *, int, int);

#else


/* Convert a pointer value */
SWIGRUNTIME(int)
SWIG_Python_ConvertPtr(PyObject *obj, void **ptr, swig_type_info *ty, int flags) {
  swig_type_info *tc;
  char  *c = 0;
  static PyObject *SWIG_this = 0;
  int    newref = 0;
  PyObject  *pyobj = 0;

  if (!obj) return 0;
  if (obj == Py_None) {
    *ptr = 0;
    return 0;
  }
#ifdef SWIG_COBJECT_TYPES
  if (!(PyCObject_Check(obj))) {
    if (!SWIG_this)
      SWIG_this = PyString_FromString("this");
    pyobj = obj;
    obj = PyObject_GetAttr(obj,SWIG_this);
    newref = 1;
    if (!obj) goto type_error;
    if (!PyCObject_Check(obj)) {
      Py_DECREF(obj);
      goto type_error;
    }
  }  
  *ptr = PyCObject_AsVoidPtr(obj);
  c = (char *) PyCObject_GetDesc(obj);
  if (newref) Py_DECREF(obj);
  goto cobject;
#else
  if (!(PyString_Check(obj))) {
    if (!SWIG_this)
      SWIG_this = PyString_FromString("this");
    pyobj = obj;
    obj = PyObject_GetAttr(obj,SWIG_this);
    newref = 1;
    if (!obj) goto type_error;
    if (!PyString_Check(obj)) {
      Py_DECREF(obj);
      goto type_error;
    }
  } 
  c = PyString_AsString(obj);
  /* Pointer values must start with leading underscore */
  if (*c != '_') {
    *ptr = (void *) 0;
    if (strcmp(c,"NULL") == 0) {
      if (newref) { Py_DECREF(obj); }
      return 0;
    } else {
      if (newref) { Py_DECREF(obj); }
      goto type_error;
    }
  }
  c++;
  c = SWIG_UnpackData(c,ptr,sizeof(void *));
  if (newref) { Py_DECREF(obj); }
#endif

#ifdef SWIG_COBJECT_TYPES
cobject:
#endif

  if (ty) {
    tc = SWIG_TypeCheck(c,ty);
    if (!tc) goto type_error;
    *ptr = SWIG_TypeCast(tc,(void*) *ptr);
  }

  if ((pyobj) && (flags & SWIG_POINTER_DISOWN)) {
    PyObject *zero = PyInt_FromLong(0);
    PyObject_SetAttrString(pyobj,(char*)"thisown",zero);
    Py_DECREF(zero);
  }
  return 0;

type_error:
  PyErr_Clear();
  if (flags & SWIG_POINTER_EXCEPTION) {
    if (ty && c) {
      PyErr_Format(PyExc_TypeError, 
		   "Type error. Got %s, expected %s",
		   c, ty->name);
    } else {
      PyErr_SetString(PyExc_TypeError,"Expected a pointer");
    }
  }
  return -1;
}

/* Convert a pointer value, signal an exception on a type mismatch */
SWIGRUNTIME(void *)
SWIG_Python_MustGetPtr(PyObject *obj, swig_type_info *ty, int argnum, int flags) {
  void *result;
  SWIG_Python_ConvertPtr(obj, &result, ty, flags | SWIG_POINTER_EXCEPTION);
  return result;
}

/* Create a new pointer object */
SWIGRUNTIME(PyObject *)
SWIG_Python_NewPointerObj(void *ptr, swig_type_info *type, int own) {
  PyObject *robj;
  if (!ptr) {
    Py_INCREF(Py_None);
    return Py_None;
  }
#ifdef SWIG_COBJECT_TYPES
  robj = PyCObject_FromVoidPtrAndDesc((void *) ptr, (char *) type->name, NULL);
#else
  {
    char result[1024];
    char *r = result;
    *(r++) = '_';
    r = SWIG_PackData(r,&ptr,sizeof(void *));
    strcpy(r,type->name);
    robj = PyString_FromString(result);
  }
#endif
  if (!robj || (robj == Py_None)) return robj;
  if (type->clientdata) {
    PyObject *inst;
    PyObject *args = Py_BuildValue((char*)"(O)", robj);
    Py_DECREF(robj);
    inst = PyObject_CallObject((PyObject *) type->clientdata, args);
    Py_DECREF(args);
    if (inst) {
      if (own) {
        PyObject *n = PyInt_FromLong(1);
        PyObject_SetAttrString(inst,(char*)"thisown",n);
        Py_DECREF(n);
      }
      robj = inst;
    }
  }
  return robj;
}

#endif

#ifdef __cplusplus
}
#endif

"""

#**************************************************************************#
#* FILE   **************    bytecodecompiler.py    ************************#
#************************************************************************ **#
#* Author: Patrick Miller February  9 2002                                *#
#* Copyright (C) 2002 Patrick J. Miller                                   *#
#**************************************************************************#
#*  *#
#**************************************************************************#
from types import *
import string
import inspect

##################################################################
#                       CLASS __DESCRIPTOR                       #
##################################################################
class __Descriptor:
    prerequisites = []
    refcount = 0
    def __repr__(self):
        return self.__module__+'.'+self.__class__.__name__

##################################################################
#                     CLASS TYPE_DESCRIPTOR                      #
##################################################################
class Type_Descriptor(__Descriptor):
    module_init_code = ''

##################################################################
#                   CLASS FUNCTION_DESCRIPTOR                    #
##################################################################
class Function_Descriptor(__Descriptor):
    def __init__(self,code,return_type,support=''):
	self.code	= code
	self.return_type	= return_type
        self.support = support
	return

        
            

haveArgument = 90 # Opcodes greater-equal to this have argument
byName = {
    'STOP_CODE': 0,
    'POP_TOP': 1,
    'ROT_TWO': 2,
    'ROT_THREE': 3,
    'DUP_TOP': 4,
    'ROT_FOUR': 5,
    'UNARY_POSITIVE': 10,
    'UNARY_NEGATIVE': 11,
    'UNARY_NOT': 12,
    'UNARY_CONVERT': 13,
    'UNARY_INVERT': 15,
    'BINARY_POWER': 19,
    'BINARY_MULTIPLY': 20,
    'BINARY_DIVIDE': 21,
    'BINARY_MODULO': 22,
    'BINARY_ADD': 23,
    'BINARY_SUBTRACT': 24,
    'BINARY_SUBSCR': 25,
    'BINARY_FLOOR_DIVIDE': 26,
    'BINARY_TRUE_DIVIDE': 27,
    'INPLACE_FLOOR_DIVIDE': 28,
    'INPLACE_TRUE_DIVIDE': 29,
    'SLICE': 30,
    'STORE_SLICE': 40,
    'DELETE_SLICE': 50,
    'INPLACE_ADD': 55,
    'INPLACE_SUBTRACT': 56,
    'INPLACE_MULTIPLY': 57,
    'INPLACE_DIVIDE': 58,
    'INPLACE_MODULO': 59,
    'STORE_SUBSCR': 60,
    'DELETE_SUBSCR': 61,
    'BINARY_LSHIFT': 62,
    'BINARY_RSHIFT': 63,
    'BINARY_AND': 64,
    'BINARY_XOR': 65,
    'BINARY_OR': 66,
    'INPLACE_POWER': 67,
    'GET_ITER': 68,
    'PRINT_EXPR': 70,
    'PRINT_ITEM': 71,
    'PRINT_NEWLINE': 72,
    'PRINT_ITEM_TO': 73,
    'PRINT_NEWLINE_TO': 74,
    'INPLACE_LSHIFT': 75,
    'INPLACE_RSHIFT': 76,
    'INPLACE_AND': 77,
    'INPLACE_XOR': 78,
    'INPLACE_OR': 79,
    'BREAK_LOOP': 80,
    'LOAD_LOCALS': 82,
    'RETURN_VALUE': 83,
    'IMPORT_STAR': 84,
    'EXEC_STMT': 85,
    'YIELD_VALUE': 86,
    'POP_BLOCK': 87,
    'END_FINALLY': 88,
    'BUILD_CLASS': 89,
    'STORE_NAME': 90,
    'DELETE_NAME': 91,
    'UNPACK_SEQUENCE': 92,
    'FOR_ITER': 93,
    'STORE_ATTR': 95,
    'DELETE_ATTR': 96,
    'STORE_GLOBAL': 97,
    'DELETE_GLOBAL': 98,
    'DUP_TOPX': 99,
    'LOAD_CONST': 100,
    'LOAD_NAME': 101,
    'BUILD_TUPLE': 102,
    'BUILD_LIST': 103,
    'BUILD_MAP': 104,
    'LOAD_ATTR': 105,
    'COMPARE_OP': 106,
    'IMPORT_NAME': 107,
    'IMPORT_FROM': 108,
    'JUMP_FORWARD': 110,
    'JUMP_IF_FALSE': 111,
    'JUMP_IF_TRUE': 112,
    'JUMP_ABSOLUTE': 113,
    'FOR_LOOP': 114,
    'LOAD_GLOBAL': 116,
    'CONTINUE_LOOP': 119,
    'SETUP_LOOP': 120,
    'SETUP_EXCEPT': 121,
    'SETUP_FINALLY': 122,
    'LOAD_FAST': 124,
    'STORE_FAST': 125,
    'DELETE_FAST': 126,
    'SET_LINENO': 127,
    'RAISE_VARARGS': 130,
    'CALL_FUNCTION': 131,
    'MAKE_FUNCTION': 132,
    'BUILD_SLICE': 133,
    'MAKE_CLOSURE': 134,
    'LOAD_CLOSURE': 135,
    'LOAD_DEREF': 136,
    'STORE_DEREF': 137,
    'CALL_FUNCTION_VAR': 140,
    'CALL_FUNCTION_KW': 141,
    'CALL_FUNCTION_VAR_KW': 142,
    }

# -----------------------------------------------
# Build one in the reverse sense
# -----------------------------------------------
byOpcode = {}
for name,op in map(None, byName.keys(), byName.values()):
    byOpcode[op] = name
    del name
    del op
    

##################################################################
#                       FUNCTION OPCODIZE                        #
##################################################################
def opcodize(s):
    "Slightly more readable form"
    length = len(s)
    i = 0
    answer = []
    while i < length:
        bytecode = ord(s[i])
        name = byOpcode[bytecode]
        if bytecode >= haveArgument:
            argument = 256*ord(s[i+2])+ord(s[i+1])
            i += 3
        else:
            argument = None
            i += 1
        answer.append((bytecode,argument,name))
    return answer



##################################################################
#                         FUNCTION LIST                          #
##################################################################
def listing(f):
    "Pretty print the internals of your function"
    assert type(f) == FunctionType,"Arg %r must be a function"%f
    filename = f.func_code.co_filename
    try:
        lines = open(filename).readlines()
    except:
        lines = None
    pc = 0
    s = ''
    lastLine = None
    for op,arg,name in opcodize(f.func_code.co_code):
        if lines and name == 'SET_LINENO':
            source = lines[arg-1][:-1]
            while lastLine and lastLine < arg-1:
                nonEmittingSource = lines[lastLine][:-1]
                lastLine += 1
                s += '%3s  %20s %5s : %s\n'%(
                    '','','',nonEmittingSource)
            lastLine = arg
        else:
            source = ''
        if arg is None: arg = ''
        s += '%3d] %20s %5s : %s\n'%(pc,name,arg,source)
        if op >= haveArgument:
            pc += 3
        else:
            pc += 1
    return s

##################################################################
#                     CLASS BYTECODEMEANING                      #
##################################################################
class ByteCodeMeaning:
    def fetch(self, pc,code):
        opcode = ord(code[pc])
        if opcode >= haveArgument:
            argument = 256*ord(code[pc+2])+ord(code[pc+1])
            next = pc+3
        else:
            argument = None
            next = pc+1
        return next,opcode,argument
    
    def execute(self,pc,opcode,argument):
        name = byOpcode[opcode]
        method = getattr(self,name)
        if argument is None:
            return apply(method,(pc,))
        else:
            return apply(method,(pc,argument,))

    def evaluate(self, pc,code):
        next, opcode,argument = self.fetch(pc,code)
        goto = self.execute(next,opcode,argument)
        if goto == -1:
            return None # Must be done
        elif goto is None:
            return next # Normal
        else:
            raise 'xx'

    symbols = { 0: 'less', 1: 'lesseq', 2: 'equal', 3: 'notequal',
                4: 'greater', 5: 'greatereq', 6: 'in', 7: 'not in',
                8: 'is', 9: 'is not', 10: 'exe match',
                11 : 'bad',
                }
    def cmp_op(self,opname):
        return self.symbols[opname]
    
    def STOP_CODE(self,pc):
        "Indicates end-of-code to the compiler, not used by the interpreter."
        raise NotImplementedError
    def POP_TOP(self,pc):
        "Removes the top-of-stack (TOS) item."
        raise NotImplementedError

    def ROT_TWO(self,pc):
        "Swaps the two top-most stack items."
        raise NotImplementedError

    def ROT_THREE(self,pc):
        "Lifts second and third stack item one position up, moves top down to position three."
        raise NotImplementedError

    def ROT_FOUR(self,pc):
        "Lifts second, third and forth stack item one position up, moves top down to position four."
        raise NotImplementedError

    def DUP_TOP(self,pc):
        "Duplicates the reference on top of the stack."
        raise NotImplementedError

    # Unary Operations take the top of the stack, apply the operation, and push the result back on the stack.

    def UNARY_POSITIVE(self,pc):
        "Implements TOS = +TOS."
        raise NotImplementedError

    def UNARY_NEGATIVE(self,pc):
        "Implements TOS = -TOS."
        raise NotImplementedError

    def UNARY_NOT(self,pc):
        "Implements TOS = not TOS."
        raise NotImplementedError

    def UNARY_CONVERT(self,pc):
        "Implements TOS = `TOS`."
        raise NotImplementedError

    def UNARY_INVERT(self,pc):
        "Implements TOS = ~TOS."
        raise NotImplementedError

    #Binary operations remove the top of the stack (TOS) and the second top-most stack item (TOS1) from the stack. They perform the operation, and put the result back on the stack.

    def BINARY_POWER(self,pc):
        "Implements TOS = TOS1 ** TOS."
        raise NotImplementedError

    def BINARY_MULTIPLY(self,pc):
        "Implements TOS = TOS1 * TOS."
        raise NotImplementedError

    def BINARY_DIVIDE(self,pc):
        "Implements TOS = TOS1 / TOS."
        raise NotImplementedError

    def BINARY_MODULO(self,pc):
        "Implements TOS = TOS1 % TOS."
        raise NotImplementedError

    def BINARY_ADD(self,pc):
        "Implements TOS = TOS1 + TOS."
        raise NotImplementedError

    def BINARY_SUBTRACT(self,pc):
        "Implements TOS = TOS1 - TOS."
        raise NotImplementedError

    def BINARY_SUBSCR(self,pc):
        "Implements TOS = TOS1[TOS]."
        raise NotImplementedError

    def BINARY_LSHIFT(self,pc):
        "Implements TOS = TOS1 << TOS."
        raise NotImplementedError

    def BINARY_RSHIFT(self,pc):
        "Implements TOS = TOS1 >> TOS."
        raise NotImplementedError

    def BINARY_AND(self,pc):
        "Implements TOS = TOS1 & TOS."
        raise NotImplementedError

    def BINARY_XOR(self,pc):
        "Implements TOS = TOS1 ^ TOS."
        raise NotImplementedError

    def BINARY_OR(self,pc):
        "Implements TOS = TOS1 | TOS."
        raise NotImplementedError

    #In-place operations are like binary operations, in that they remove TOS and TOS1, and push the result back on the stack, but the operation is done in-place when TOS1 supports it, and the resulting TOS may be (but does not have to be) the original TOS1.

    def INPLACE_POWER(self,pc):
        "Implements in-place TOS = TOS1 ** TOS."
        raise NotImplementedError

    def INPLACE_MULTIPLY(self,pc):
        "Implements in-place TOS = TOS1 * TOS."
        raise NotImplementedError

    def INPLACE_DIVIDE(self,pc):
        "Implements in-place TOS = TOS1 / TOS."
        raise NotImplementedError

    def INPLACE_MODULO(self,pc):
        "Implements in-place TOS = TOS1 % TOS."
        raise NotImplementedError

    def INPLACE_ADD(self,pc):
        "Implements in-place TOS = TOS1 + TOS."
        raise NotImplementedError

    def INPLACE_SUBTRACT(self,pc):
        "Implements in-place TOS = TOS1 - TOS."
        raise NotImplementedError

    def INPLACE_LSHIFT(self,pc):
        "Implements in-place TOS = TOS1 << TOS."
        raise NotImplementedError

    def INPLACE_RSHIFT(self,pc):
        "Implements in-place TOS = TOS1 >> TOS."
        raise NotImplementedError

    def INPLACE_AND(self,pc):
        "Implements in-place TOS = TOS1 & TOS."
        raise NotImplementedError

    def INPLACE_XOR(self,pc):
        "Implements in-place TOS = TOS1 ^ TOS."
        raise NotImplementedError

    def INPLACE_OR(self,pc):
        "Implements in-place TOS = TOS1 | TOS."
        raise NotImplementedError

    #The slice opcodes take up to three parameters.

    def SLICE_0(self,pc):
        "Implements TOS = TOS[:]."
        raise NotImplementedError

    def SLICE_1(self,pc):
        "Implements TOS = TOS1[TOS:]."
        raise NotImplementedError

    def SLICE_2(self,pc):
        "Implements TOS = TOS1[:TOS1]."
        raise NotImplementedError

    def SLICE_3(self,pc):
        "Implements TOS = TOS2[TOS1:TOS]."
        raise NotImplementedError

    #Slice assignment needs even an additional parameter. As any statement, they put nothing on the stack.

    def STORE_SLICE_0(self,pc):
        "Implements TOS[:] = TOS1."
        raise NotImplementedError

    def STORE_SLICE_1(self,pc):
        "Implements TOS1[TOS:] = TOS2."
        raise NotImplementedError

    def STORE_SLICE_2(self,pc):
        "Implements TOS1[:TOS] = TOS2."
        raise NotImplementedError

    def STORE_SLICE_3(self,pc):
        "Implements TOS2[TOS1:TOS] = TOS3."
        raise NotImplementedError

    def DELETE_SLICE_0(self,pc):
        "Implements del TOS[:]."
        raise NotImplementedError

    def DELETE_SLICE_1(self,pc):
        "Implements del TOS1[TOS:]."
        raise NotImplementedError

    def DELETE_SLICE_2(self,pc):
        "Implements del TOS1[:TOS]."
        raise NotImplementedError

    def DELETE_SLICE_3(self,pc):
        "Implements del TOS2[TOS1:TOS]."
        raise NotImplementedError

    def STORE_SUBSCR(self,pc):
        "Implements TOS1[TOS] = TOS2."
        raise NotImplementedError

    def DELETE_SUBSCR(self,pc):
        "Implements del TOS1[TOS]."
        raise NotImplementedError

    def PRINT_EXPR(self,pc):
        "Implements the expression statement for the interactive mode. TOS is removed from the stack and printed. In non-interactive mode, an expression statement is terminated with POP_STACK."
        raise NotImplementedError

    def PRINT_ITEM(self,pc):
        "Prints TOS to the file-like object bound to sys.stdout. There is one such instruction for each item in the print statement."
        raise NotImplementedError

    def PRINT_ITEM_TO(self,pc):
        "Like PRINT_ITEM, but prints the item second from TOS to the file-like object at TOS. This is used by the extended print statement."
        raise NotImplementedError

    def PRINT_NEWLINE(self,pc):
        "Prints a new line on sys.stdout. This is generated as the last operation of a print statement, unless the statement ends with a comma."
        raise NotImplementedError

    def PRINT_NEWLINE_TO(self,pc):
        "Like PRINT_NEWLINE, but prints the new line on the file-like object on the TOS. This is used by the extended print statement."
        raise NotImplementedError

    def BREAK_LOOP(self,pc):
        "Terminates a loop due to a break statement."
        raise NotImplementedError

    def LOAD_LOCALS(self,pc):
        "Pushes a reference to the locals of the current scope on the stack. This is used in the code for a class definition: After the class body is evaluated, the locals are passed to the class definition."
        raise NotImplementedError

    def RETURN_VALUE(self,pc):
        "Returns with TOS to the caller of the function."
        raise NotImplementedError

    def IMPORT_STAR(self,pc):
        "Loads all symbols not starting with _ directly from the module TOS to the local namespace. The module is popped after loading all names. This opcode implements from module import *."
        raise NotImplementedError

    def EXEC_STMT(self,pc):
        "Implements exec TOS2,TOS1,TOS. The compiler fills missing optional parameters with None."
        raise NotImplementedError

    def POP_BLOCK(self,pc):
        "Removes one block from the block stack. Per frame, there is a stack of blocks, denoting nested loops, try statements, and such."
        raise NotImplementedError

    def END_FINALLY(self,pc):
        "Terminates a finally clause. The interpreter recalls whether the exception has to be re-raised, or whether the function returns, and continues with the outer-next block."
        raise NotImplementedError

    def BUILD_CLASS(self,pc):
        "Creates a new class object. TOS is the methods dictionary, TOS1 the tuple of the names of the base classes, and TOS2 the class name."
        raise NotImplementedError

    #All of the following opcodes expect arguments. An argument is two bytes, with the more significant byte last.

    def STORE_NAME(self,pc,namei):
        "Implements name = TOS. namei is the index of name in the attribute co_names of the code object. The compiler tries to use STORE_LOCAL or STORE_GLOBAL if possible."
        raise NotImplementedError

    def DELETE_NAME(self,pc,namei):
        "Implements del name, where namei is the index into co_names attribute of the code object."
        raise NotImplementedError

    def UNPACK_SEQUENCE(self,pc,count):
        "Unpacks TOS into count individual values, which are put onto the stack right-to-left."
        raise NotImplementedError

    def DUP_TOPX(self,pc,count):
        "Duplicate count items, keeping them in the same order. Due to implementation limits, count should be between 1 and 5 inclusive."
        raise NotImplementedError

    def STORE_ATTR(self,pc,namei):
        "Implements TOS.name = TOS1, where namei is the index of name in co_names."
        raise NotImplementedError

    def DELETE_ATTR(self,pc,namei):
        "Implements del TOS.name, using namei as index into co_names."
        raise NotImplementedError

    def STORE_GLOBAL(self,pc,namei):
        "Works as STORE_NAME, but stores the name as a global."
        raise NotImplementedError

    def DELETE_GLOBAL(self,pc,namei):
        "Works as DELETE_NAME, but deletes a global name."
        raise NotImplementedError

    def LOAD_CONST(self,pc,consti):
        "Pushes co_consts[consti] onto the stack."
        raise NotImplementedError

    def LOAD_NAME(self,pc,namei):
        "Pushes the value associated with co_names[namei] onto the stack."
        raise NotImplementedError

    def BUILD_TUPLE(self,pc,count):
        "Creates a tuple consuming count items from the stack, and pushes the resulting tuple onto the stack."
        raise NotImplementedError

    def BUILD_LIST(self,pc,count):
        "Works as BUILD_TUPLE, but creates a list."
        raise NotImplementedError

    def BUILD_MAP(self,pc,zero):
        "Pushes a new empty dictionary object onto the stack. The argument is ignored and set to zero by the compiler."
        raise NotImplementedError

    def LOAD_ATTR(self,pc,namei):
        "Replaces TOS with getattr(TOS, co_names[namei]."
        raise NotImplementedError

    def COMPARE_OP(self,pc,opname):
        "Performs a Boolean operation. The operation name can be found in cmp_op[opname]."
        raise NotImplementedError

    def IMPORT_NAME(self,pc,namei):
        "Imports the module co_names[namei]. The module object is pushed onto the stack. The current namespace is not affected: for a proper import statement, a subsequent STORE_FAST instruction modifies the namespace."
        raise NotImplementedError

    def IMPORT_FROM(self,pc,namei):
        "Loads the attribute co_names[namei] from the module found in TOS. The resulting object is pushed onto the stack, to be subsequently stored by a STORE_FAST instruction."
        raise NotImplementedError

    def JUMP_FORWARD(self,pc,delta):
        "Increments byte code counter by delta."
        raise NotImplementedError

    def JUMP_IF_TRUE(self,pc,delta):
        "If TOS is true, increment the byte code counter by delta. TOS is left on the stack."
        raise NotImplementedError

    def JUMP_IF_FALSE(self,pc,delta):
        "If TOS is false, increment the byte code counter by delta. TOS is not changed."
        raise NotImplementedError

    def JUMP_ABSOLUTE(self,pc,target):
        "Set byte code counter to target."
        raise NotImplementedError

    def FOR_LOOP(self,pc,delta):
        "Iterate over a sequence. TOS is the current index, TOS1 the sequence. First, the next element is computed. If the sequence is exhausted, increment byte code counter by delta. Otherwise, push the sequence, the incremented counter, and the current item onto the stack."
        raise NotImplementedError

    def LOAD_GLOBAL(self,pc,namei):
        "Loads the global named co_names[namei] onto the stack."
        raise NotImplementedError

    def SETUP_LOOP(self,pc,delta):
        "Pushes a block for a loop onto the block stack. The block spans from the current instruction with a size of delta bytes."
        raise NotImplementedError

    def SETUP_EXCEPT(self,pc,delta):
        "Pushes a try block from a try-except clause onto the block stack. delta points to the first except block."
        raise NotImplementedError

    def SETUP_FINALLY(self,pc,delta):
        "Pushes a try block from a try-except clause onto the block stack. delta points to the finally block."
        raise NotImplementedError

    def LOAD_FAST(self,pc,var_num):
        "Pushes a reference to the local co_varnames[var_num] onto the stack."
        raise NotImplementedError

    def STORE_FAST(self,pc,var_num):
        "Stores TOS into the local co_varnames[var_num]."
        raise NotImplementedError

    def DELETE_FAST(self,pc,var_num):
        "Deletes local co_varnames[var_num]."
        raise NotImplementedError

    def LOAD_CLOSURE(self,pc,i):
        "Pushes a reference to the cell contained in slot i of the cell and free variable storage. The name of the variable is co_cellvars[i] if i is less than the length of co_cellvars. Otherwise it is co_freevars[i - len(co_cellvars)]."
        raise NotImplementedError

    def LOAD_DEREF(self,pc,i):
        "Loads the cell contained in slot i of the cell and free variable storage. Pushes a reference to the object the cell contains on the stack."
        raise NotImplementedError

    def STORE_DEREF(self,pc,i):
        "Stores TOS into the cell contained in slot i of the cell and free variable storage."
        raise NotImplementedError

    def SET_LINENO(self,pc,lineno):
        "Sets the current line number to lineno."
        raise NotImplementedError

    def RAISE_VARARGS(self,pc,argc):
        "Raises an exception. argc indicates the number of parameters to the raise statement, ranging from 0 to 3. The handler will find the traceback as TOS2, the parameter as TOS1, and the exception as TOS."
        raise NotImplementedError

    def CALL_FUNCTION(self,pc,argc):
        "Calls a function. The low byte of argc indicates the number of positional parameters, the high byte the number of keyword parameters. On the stack, the opcode finds the keyword parameters first. For each keyword argument, the value is on top of the key. Below the keyword parameters, the positional parameters are on the stack, with the right-most parameter on top. Below the parameters, the function object to call is on the stack."
        raise NotImplementedError

    def MAKE_FUNCTION(self,pc,argc):
        "Pushes a new function object on the stack. TOS is the code associated with the function. The function object is defined to have argc default parameters, which are found below TOS."
        raise NotImplementedError

    def MAKE_CLOSURE(self,pc,argc):
        "Creates a new function object, sets its func_closure slot, and pushes it on the stack. TOS is the code associated with the function. If the code object has N free variables, the next N items on the stack are the cells for these variables. The function also has argc default parameters, where are found before the cells."
        raise NotImplementedError

    def BUILD_SLICE(self,pc,argc):
        "Pushes a slice object on the stack. argc must be 2 or 3. If it is 2, slice(TOS1, TOS) is pushed; if it is 3, slice(TOS2, TOS1, TOS) is pushed. See the slice() built-in function for more information."
        raise NotImplementedError

    def EXTENDED_ARG(self,pc,ext):
        "Prefixes any opcode which has an argument too big to fit into the default two bytes. ext holds two additional bytes which, taken together with the subsequent opcode's argument, comprise a four-byte argument, ext being the two most-significant bytes."
        raise NotImplementedError

    def CALL_FUNCTION_VAR(self,pc,argc):
        "Calls a function. argc is interpreted as in CALL_FUNCTION. The top element on the stack contains the variable argument list, followed by keyword and positional arguments."
        raise NotImplementedError

    def CALL_FUNCTION_KW(self,pc,argc):
        "Calls a function. argc is interpreted as in CALL_FUNCTION. The top element on the stack contains the keyword arguments dictionary, followed by explicit keyword and positional arguments."
        raise NotImplementedError

    def CALL_FUNCTION_VAR_KW(self,pc,argc):
        "Calls a function. argc is interpreted as in CALL_FUNCTION. The top element on the stack contains the keyword arguments dictionary, followed by the variable-arguments tuple, followed by explicit keyword and positional arguments."
        raise NotImplementedError

    

##################################################################
#                         CLASS CXXCODER                         #
##################################################################
class CXXCoder(ByteCodeMeaning):

    ##################################################################
    #                    MEMBER TYPEDEF_BY_VALUE                     #
    ##################################################################
    def typedef_by_value(self,v):
        raise NotImplementedError # VIRTUAL
    
    ##################################################################
    #                        MEMBER __INIT__                         #
    ##################################################################
    def __init__(self,function,signature,name=None):
        assert type(function) == FunctionType,"Arg must be a user function"
        assert not function.func_defaults ,"Function cannot have default args (yet)"
        if name is None: name = function.func_name
        self.name = name
        self.function = function
        self.signature = signature
        self.codeobject = function.func_code
        self.__uid = 0 # Builds temps
        self.__indent = 1
        return

    ##################################################################
    #                        MEMBER EVALUATE                         #
    ##################################################################
    def evaluate(self, pc,code):
        # See if we posted any forwards for this offset
        if self.forwards.has_key(pc):
            for f in self.forwards[pc]:
                f()
            self.forwards[pc] = []
        return ByteCodeMeaning.evaluate(self,pc,code)
    
    ##################################################################
    #                        MEMBER GENERATE                         #
    ##################################################################
    def generate(self):
        self.forwards = {} # Actions on forward interprets
        self.__body = '' # Body will be built
        self.helpers = [] # headers and stuff

        # -----------------------------------------------
        # OK, crack open the function object and build
        # initial stack (not a real frame!)
        # -----------------------------------------------
        arglen = self.codeobject.co_argcount
        nlocals = self.codeobject.co_nlocals

        self.consts = self.codeobject.co_consts
        self.stack = list(self.codeobject.co_varnames)
        self.types = list(self.signature)+[None]*(nlocals-arglen)
        self.used = []
        for T in self.types:
            if T not in self.used: self.used.append(T)

        # -----------------------------------------------
        # One pass through the byte codes to generate
        # the body
        # -----------------------------------------------
        code = self.codeobject.co_code
        bytes = len(code)
        pc = 0
        while pc != None and pc < bytes:
            pc = self.evaluate(pc,code)

        # -----------------------------------------------
        # Return?
        # -----------------------------------------------
        if self.rtype == NoneType:
            rtype = 'void'
        else:
            rtype = self.rtype.cxxtype
            
        # -----------------------------------------------
        # Insert code body if available
        # -----------------------------------------------
        source = inspect.getsource(self.function)
        if not source: source = ''
        comments = inspect.getcomments(self.function)
        if comments: source = comments+source
        code = string.join(map(lambda x: '/////// '+x,string.split(source,'\n')),
                           '\n')+'\n'

        # -----------------------------------------------
        # Add in the headers
        # -----------------------------------------------
        code += '#include "Python.h"\n'
        for T in self.used:
            if T is None: continue
            for pre in T.prerequisites:
                code += pre
                code += '\n'

        # -----------------------------------------------
        # Real body
        # -----------------------------------------------
        code += '\n'
        code += '\nstatic %s %s('%(rtype,self.name)
        for i in range(len(self.signature)):
            if i != 0: code += ', '
            n = self.stack[i]
            t = self.types[i]
            code += '%s %s'%(t.cxxtype,n)
        code += ') {\n'
        code += ' PyObject* tempPY= 0;\n'


        # Add in non-argument temporaries
        # Assuming first argcount locals are positional args
        for i in range(self.codeobject.co_argcount,
                       self.codeobject.co_nlocals):
            t = self.types[i]
            code += '%s %s;\n'%(
                t.cxxtype,
                self.codeobject.co_varnames[i],
                )

        # Add in the body
        code += self.__body
        code += '}\n\n'
        return code


    ##################################################################
    #                      MEMBER WRAPPED_CODE                       #
    ##################################################################
    def wrapped_code(self):
        code = self.generate()
        
        # -----------------------------------------------
        # Wrapper
        # -----------------------------------------------
        code += 'static PyObject* wrapper_%s(PyObject*,PyObject* args) {\n'%self.name
        code += '  // Length check\n'
        code += '  if ( PyTuple_Size(args) != %d ) {\n'%len(self.signature)
        code += '     PyErr_SetString(PyExc_TypeError,"Expected %d arguments");\n'%len(self.signature)
        code += '     return 0;\n'
        code += '  }\n'

        code += '\n  // Load Py versions of args\n'
        for i in range(len(self.signature)):
            T = self.signature[i]
            code += '  PyObject* py_%s = PyTuple_GET_ITEM(args,%d);\n'%(
                self.codeobject.co_varnames[i],i
                )

            code += '  if ( !(%s) ) {\n'% \
                    T.check('py_'+self.codeobject.co_varnames[i])
            #code += '    PyObject_Print(py_A,stdout,0); puts("");\n'
            #code += '    printf("nd=%d typecode=%d\\n",((PyArrayObject*)py_A)->nd,((PyArrayObject*)py_A)->descr->type_num);\n'
            code += '    PyErr_SetString(PyExc_TypeError,"Bad type for arg %d (expected %s)");\n'%(
                i+1,
                T.__class__.__name__)
            code += '    return 0;\n'
            code += '  }\n'
        
        code += '\n  // Do conversions\n'
        argnames = []
        for i in range(len(self.signature)):
            T = self.signature[i]

            code += '  %s %s=%s;\n'%(
                T.cxxtype,
                self.codeobject.co_varnames[i],
                T.inbound('py_'+self.codeobject.co_varnames[i]),
                )
            code += '  if ( PyErr_Occurred() ) return 0;\n'
            argnames.append(self.codeobject.co_varnames[i])

        code += '\n  // Compute result\n'
        if self.rtype != NoneType:
            code += '  %s _result = '%(
                self.rtype.cxxtype,
                )
        else:
            code += '  '
        code += '%s(%s);\n'%(
            self.name,
            string.join(argnames,','),
            )


        code += '\n  // Pack return\n'
        if ( self.rtype == NoneType ):
            code += '  Py_INCREF(Py_None);\n'
            code += '  return Py_None;\n'
        else:
            result,owned = self.rtype.outbound('_result')
            if not owned:
                code += '  Py_INCREF(_result);\n'
            code += '  return %s;\n'%result
        code += '}\n'
        return code

    def indent(self):
        self.__indent += 1
        return

    def dedent(self):
        self.__indent -= 1
        return

    ##################################################################
    #                          MEMBER EMIT                           #
    ##################################################################
    def emit(self,s):
        self.__body += ' '*(3*self.__indent)
        self.__body += s
        self.__body += '\n'
        return

    ##################################################################
    #                          MEMBER PUSH                           #
    ##################################################################
    def push(self,v,t):
        self.stack.append(v)
        self.types.append(t)
        return

    ##################################################################
    #                           MEMBER POP                           #
    ##################################################################
    def pop(self):
        v = self.stack[-1]
        assert type(v) != TupleType
        del self.stack[-1]
        t = self.types[-1]
        assert type(t) != TupleType
        del self.types[-1]
        return v,t

    ##################################################################
    #                        MEMBER PUSHTUPLE                        #
    ##################################################################
    def pushTuple(self,V,T):
        assert type(V) == TupleType
        self.stack.append(V)
        assert type(V) == TupleType
        self.types.append(T)
        return


    ##################################################################
    #                        MEMBER POPTUPLE                         #
    ##################################################################
    def popTuple(self):
        v = self.stack[-1]
        assert type(v) == TupleType
        del self.stack[-1]
        t = self.types[-1]
        assert type(t) == TupleType
        del self.types[-1]
        return v,t
    ##################################################################
    #                        MEMBER MULTIARG                         #
    ##################################################################
    def multiarg(self):
        return type(self.stack[-1]) == TupleType
    
    ##################################################################
    #                         MEMBER UNIQUE                          #
    ##################################################################
    def unique(self):
        self.__uid += 1
        return 't%d'%self.__uid

    ##################################################################
    #                          MEMBER POST                           #
    ##################################################################
    def post(self,pc,action):
        if not self.forwards.has_key(pc):
            self.forwards[pc] = []
        self.forwards[pc].append(action)
        return

    ##################################################################
    #                       MEMBER EMIT_VALUE                        #
    ##################################################################
    def emit_value(self, v):
        descriptor = self.typedef_by_value(v)
    
        # Convert representation to CXX rhs
        rhs = descriptor.literalizer(v)
        lhs = self.unique()
        self.emit('%s %s = %s;'%(
            descriptor.cxxtype,
            lhs,
            rhs))
        self.push(lhs,descriptor)
        return        

    ##################################################################
    #                       MEMBER GLOBAL_INFO                       #
    ##################################################################
    def global_info(self,var_num):
        # This is the name value is known by
        var_name = self.codeobject.co_names[var_num]

        # First, figure out who owns this global
        import sys
        myHash = id(self.function.func_globals)
        for module_name in sys.modules.keys():
            module = sys.modules[module_name]
            if module and id(module.__dict__) == myHash:
                break
        else:
            raise ValueError,'Cannot locate module owning %s'%varname
        return module_name,var_name


    ##################################################################
    #                         MEMBER CODEUP                          #
    ##################################################################
    def codeup(self, rhs, rhs_type):
        lhs = self.unique()
        self.emit('%s %s = %s;\n'%(
            rhs_type.cxxtype,
            lhs,
            rhs))
        print self.__body
        self.push(lhs,rhs_type)
        return        
        

    ##################################################################
    #                          MEMBER BINOP                          #
    ##################################################################
    def binop(self,pc,symbol):
        v2,t2 = self.pop()
        v1,t1 = self.pop()

        if t1 == t2:
            rhs,rhs_type = t1.binop(symbol,v1,v2)
        else:
            rhs,rhs_type = t1.binopMixed(symbol,v1,v2,t2)

        self.codeup(rhs,rhs_type)
        return

    ##################################################################
    #                       MEMBER BINARY_XXX                        #
    ##################################################################
    def BINARY_ADD(self,pc):
        return self.binop(pc,'+')
    def BINARY_SUBTRACT(self,pc):
        return self.binop(pc,'-')
    def BINARY_MULTIPLY(self,pc):
        print 'MULTIPLY',self.stack[-2],self.types[-2],'*',self.stack[-1],self.types[-1]
        return self.binop(pc,'*')
    def BINARY_DIVIDE(self,pc):
        return self.binop(pc,'/')
    def BINARY_MODULO(self,pc):
        return self.binop(pc,'%')
    def BINARY_SUBSCR(self,pc):
        if self.multiarg():
            v2,t2 = self.popTuple()
        else:
            v2,t2 = self.pop()
            v2 = (v2,)
            t2 = (t2,)
        v1,t1 = self.pop()
        rhs,rhs_type = t1.getitem(v1,v2,t2)
        self.codeup(rhs,rhs_type)
        return

    def STORE_SUBSCR(self,pc):
        if self.multiarg():
            v2,t2 = self.popTuple()
        else:
            v2,t2 = self.pop()
            v2 = (v2,)
            t2 = (t2,)
        v1,t1 = self.pop()
        v0,t0 = self.pop()
        
        rhs,rhs_type = t1.setitem(v1,v2,t2)
        assert rhs_type == t0,"Store the right thing"
        self.emit('%s = %s;'%(rhs,v0))
        return

    def COMPARE_OP(self,pc,opname):
        symbol = self.cmp_op(opname) # convert numeric to name
        return self.binop(pc,symbol)


    ##################################################################
    #                       MEMBER PRINT_ITEM                        #
    ##################################################################
    def PRINT_ITEM(self,pc):
        # Printing correctly is tricky... best to let Python
        # do the real work here
        w = self.unique()
        self.emit('PyObject* %s = PySys_GetObject("stdout");'%w)
        self.emit('if (PyFile_SoftSpace(%s,1)) PyFile_WriteString(" ",%s);'%(w,w))
        v,t = self.pop()

        py = self.unique()
        code,owned = t.outbound(v)
        self.emit('PyObject* %s = %s;'%(py, code))
        self.emit('PyFile_WriteObject(%s,%s,Py_PRINT_RAW);'%(
            py,w))
        if owned:
            self.emit('Py_XDECREF(%s);'%py)
        return


    ##################################################################
    #                      MEMBER PRINT_NEWLINE                      #
    ##################################################################
    def PRINT_NEWLINE(self,pc):
        # Printing correctly is tricky... best to let Python
        # do the real work here
        w = self.unique()
        self.emit('PyObject* %s = PySys_GetObject("stdout");'%w)
        self.emit('PyFile_WriteString("\\n",%s);'%w);
        self.emit('PyFile_SoftSpace(%s,0);'%w);
        return
        
    ##################################################################
    #                       MEMBER SET_LINENO                        #
    ##################################################################
    def SET_LINENO(self,pc,lineno):
        self.emit('// %s:%d'%(self.codeobject.co_filename,lineno))
        return

    ##################################################################
    #                         MEMBER POP_TOP                         #
    ##################################################################
    def POP_TOP(self,pc):
        v,t = self.pop()
        return

    ##################################################################
    #                       MEMBER LOAD_CONST                        #
    ##################################################################
    def LOAD_CONST(self,pc,consti):
        # Fetch the constant
        k = self.consts[consti]
        t = type(k)
        print 'LOAD_CONST',repr(k),t

        # Fetch a None is just skipped
        if t == NoneType:
            self.push('<void>',t) 
            return

        self.emit_value(k)
        return


    ##################################################################
    #                       MEMBER BUILD_TUPLE                       #
    ##################################################################
    def BUILD_TUPLE(self,pc,count):
        "Creates a tuple consuming count items from the stack, and pushes the resulting tuple onto the stack."
        V = []
        T = []
        for i in range(count):
            v,t = self.pop()
            V.append(v)
            T.append(t)
        V.reverse()
        T.reverse()
        self.pushTuple(tuple(V),tuple(T))
        return

    ##################################################################
    #                        MEMBER LOAD_FAST                        #
    ##################################################################
    def LOAD_FAST(self,pc,var_num):
        v = self.stack[var_num]
        t = self.types[var_num]
        print 'LOADFAST',var_num,v,t
        for VV,TT in map(None, self.stack, self.types):
            print VV,':',TT
        if t is None:
            raise TypeError,'%s used before set?'%v
            print self.__body
            print 'PC',pc
        self.push(v,t)
        return


    ##################################################################
    #                        MEMBER LOAD_ATTR                        #
    ##################################################################
    def LOAD_ATTR(self,pc,namei):
        v,t = self.pop()
        attr_name = self.codeobject.co_names[namei]
        print 'LOAD_ATTR',namei,v,t,attr_name
        aType,aCode = t.get_attribute(attr_name)
        print 'ATTR',aType
        print aCode
        lhs = self.unique()
        rhs = v
        lhsType = aType.cxxtype
        self.emit(aCode%locals())
        self.push(lhs,aType)
        return


    ##################################################################
    #                       MEMBER STORE_ATTR                        #
    ##################################################################
    def STORE_ATTR(self,pc,namei):
        v,t = self.pop()
        attr_name = self.codeobject.co_names[namei]
        print 'STORE_ATTR',namei,v,t,attr_name
        v2,t2 = self.pop()
        print 'SA value',v2,t2
        aType,aCode = t.set_attribute(attr_name)
        print 'ATTR',aType
        print aCode
        assert t2 is aType
        rhs = v2
        lhs = v
        self.emit(aCode%locals())
        return

    ##################################################################
    #                       MEMBER LOAD_GLOBAL                       #
    ##################################################################
    def LOAD_GLOBAL(self,pc,var_num):
        # Figure out the name and load it
        try:
            F = self.function.func_globals[self.codeobject.co_names[var_num]]
        except:
            F = __builtins__[self.codeobject.co_names[var_num]]

        # For functions, we see if we know about this function
        if callable(F):
            self.push(F,type(F))
            return

        # We need the name of the module that matches
        # the global state for the function and
        # the name of the variable
        module_name,var_name = self.global_info(var_num)

        # We hope it's type is correct
        t = type(F)
        descriptor = typedefs[t]
        native = self.unique()
        py = self.unique()
        mod = self.unique()

        self.emit('')
        self.emit('PyObject* %s = PyImport_ImportModule("%s");'%(
            mod,module_name))
        self.emit('PyObject* %s = PyObject_GetAttrString(%s,"%s");'%(
            py,mod,var_name))
        self.emit('%s %s = %s;'%(
            descriptor.cxxtype,
            native,
            descriptor.inbound%py))

        self.push(native,t)
        return

    def SETUP_LOOP(self,pc,delta):
        "Pushes a block for a loop onto the block stack. The block spans from the current instruction with a size of delta bytes."
        return

    def FOR_LOOP(self,pc,delta):
        "Iterate over a sequence. TOS is the current index, TOS1 the sequence. First, the next element is computed. If the sequence is exhausted, increment byte code counter by delta. Otherwise, push the sequence, the incremented counter, and the current item onto the stack."
        # Pull off control variable and range info
        v2,t2 = self.pop()
        v1,t1 = self.pop()
        self.emit('for(%s=%s.low; %s<%s.high; %s += %s.step) {'%(
            v2,v1,v2,v1,v2,v1))

        # Put range back on for assignment
        self.push(v2,t2)
        return

    def JUMP_ABSOLUTE(self,pc,target):
        "Set byte code counter to target."
        self.emit('}')
        return

    def POP_BLOCK(self,pc):
        "Removes one block from the block stack. Per frame, there is a stack of blocks, denoting nested loops, try statements, and such."
        return


    ##################################################################
    #                       MEMBER STORE_FAST                        #
    ##################################################################
    def STORE_FAST(self,pc,var_num):

        v,t = self.pop()
        print 'STORE FAST',var_num,v,t

        save = self.stack[var_num]
        saveT = self.types[var_num]

        # See if type is same....
        # Note that None means no assignment made yet
        if saveT is None or t == saveT:
            if t.refcount:
                self.emit('Py_XINCREF(%s);'%v)
                self.emit('Py_XDECREF(%s);'%save)
            self.emit('%s = %s;\n'%(save,v))
            self.types[var_num] = t
            return

        raise TypeError,(t,saveT)

    ##################################################################
    #                      MEMBER STORE_GLOBAL                       #
    ##################################################################
    def STORE_GLOBAL(self,pc,var_num):

        # We need the name of the module that matches
        # the global state for the function and
        # the name of the variable
        module_name,var_name = self.global_info(var_num)

        # Convert the value to Python object
        v,t = self.pop()
        descriptor = typedefs[t]
        py = self.unique()
        code,owned = descriptor.outbound(v)
        self.emit('PyObject* %s = %s;'%(py,code))
        if not owned:
            self.emit('Py_INCREF(%s);'%py)
        mod = self.unique()
        self.emit('PyObject* %s = PyImport_ImportModule("%s");'%(
            mod,module_name))
        self.emit('PyObject_SetAttrString(%s,"%s",%s);'%(
            mod,var_name,py))
        self.emit('Py_DECREF(%s);'%py)
        return

    ##################################################################
    #                      MEMBER CALL_FUNCTION                      #
    ##################################################################
    def CALL_FUNCTION(self,pc,argc):
        # Pull args off stack
        args = []
        types = []
        for i in range(argc):
            v,t = self.pop()
            args = [v]+args
            types = [t]+types
 
        # Pull function object off stack and get descriptor
        f,t = self.pop()
        signature = (f,tuple(types))
        descriptor = self.function_by_signature(signature)
        #self.prerequisites += descriptor['prerequisite']+'\n'
        
        # Build a rhs
        rhs = descriptor.code%string.join(args,',')

        # Build a statement
        temp = self.unique()
        self.emit('%s %s = %s;\n'%(
            descriptor.return_type.cxxtype,
            temp,
            rhs))

        self.push(temp,descriptor.return_type)
        return


    ##################################################################
    #                      MEMBER JUMP_IF_FALSE                      #
    ##################################################################
    def JUMP_IF_FALSE(self,pc,delta):
        v,t = self.pop()
        self.push(v,t)
        # We need to do some work when we get to the
        # else part (put the value that's gonna get
        # popped back on the stack, emit } else {,
        # ...)
        action = lambda v=v,t=t,self=self: (
            self.emit('} else {'),
            self.push(v,t),
            )
        self.post(pc+delta,action)
        if t != IntType: raise TypeError, 'Invalid comparison type %s'%t
        self.emit('if (%s) {\n'%v)
        return
    

    ##################################################################
    #                      MEMBER JUMP_FORWARD                       #
    ##################################################################
    def JUMP_FORWARD(self,pc,delta):
        # We need to close the if after the delta
        action = lambda self=self: (
            self.emit('}'),
            )
        self.post(pc+delta,action)
        return
    
    ##################################################################
    #                      MEMBER RETURN_VALUE                       #
    ##################################################################
    def RETURN_VALUE(self,pc):
        v,t = self.pop()
        if hasattr(self,'rtype'):
            print v,t
            if t == NoneType: return # just the extra return
            raise ValueError,'multiple returns'
        self.rtype = t
        if t == NoneType:
            self.emit('return;')
        else:
            self.emit('return %s;'%v)
        print 'return with',v
        return


import pprint
import string
from ast_tools import * 

def slice_ast_to_dict(ast_seq):
    sl_vars = {}
    if type(ast_seq) in (ListType,TupleType):
        for pattern in slice_patterns:
            found,data = match(pattern,ast_seq)
            if found:    
                sl_vars = {'begin':'_beg',
                           'end':'_end', 
                           'step':'_stp',
                           'single_index':'_index'}
                for key in data.keys():
                    data[key] = ast_to_string(data[key])
                sl_vars.update(data)
                break;        
    return sl_vars
            
def build_slice_atom(slice_vars, position):
    # Note: This produces slices that are incorrect for Python
    # evaluation because of slicing being exclusive in Python
    # and inclusive for blitz on the top end of the range.
    # This difference should really be handle in a blitz specific transform,
    # but I've put it here for convenience. This doesn't cause any
    # problems in code, its just a maintance hassle (I'll forget I did it here)
    # and inelegant.  *FIX ME*.
    
        
    ###########################################################################
    #                        Handling negative indices.
    #
    # Range indices that begin with a negative sign, '-', are assumed to be
    # negative.  Blitz++ interprets negative indices differently than 
    # Python.  To correct this, we subtract negative indices from the length
    # of the array (at run-time).  If indices do not start with a negative 
    # sign, they are assumed to be positive.
    #
    # This scheme doesn't work in the general case.  For example, if you
    # are calculating negative indices from a math expression that doesn't
    # start with the negative sign, then it will be assumed positive and
    # hence generate wrong results (and maybe a seg-fault).
    # 
    # I think this case can might be remedied by calculating all ranges on
    # the fly, and then subtracting them from the length of the array in 
    # that dimension if they are negative.  This is major code bloat in the
    # funcitons and more work.  Save till later...
    ###########################################################################
    # I don't think the strip is necessary, but it insures
    # that '-' is the first sign for negative indices.
    if slice_vars['single_index'] != '_index':
        expr = '%(single_index)s' % slice_vars        
    else:    
        begin = string.strip(slice_vars['begin'])
        if begin[0] == '-':
            slice_vars['begin'] = 'N' + slice_vars['var']+`position`+begin;
    
        end = string.strip(slice_vars['end'])
        if end != '_end' and end[0] != '-':
            #compensate for blitz using inclusive indexing on top end 
            #of slice for positive indices.
            slice_vars['end'] = end + '-1'
        if end[0] == '-':
            slice_vars['end'] = 'N%s[%d]%s-1' % (slice_vars['var'],position,end)
        
        if slice_vars['step'] == '_stp':
            # this if/then isn't strictly necessary, it'll
            # just keep the output code a little cleaner
            expr = 'slice(%(begin)s,%(end)s)' % slice_vars        
        else:        
            expr = 'slice(%(begin)s,%(end)s,%(step)s)' % slice_vars    
    val =  atom_list(expr)
    return val

def transform_subscript_list(subscript_dict):
    # this is gonna edit the ast_list...        
    subscript_list = subscript_dict['subscript_list']

    var = subscript_dict['var']
    #skip the first entry (the subscript_list symbol)
    slice_position = -1
    for i in range(1,len(subscript_list)):
        #skip commas...
        if subscript_list[i][0] != token.COMMA:
            slice_position += 1
            slice_vars = slice_ast_to_dict(subscript_list[i])

            slice_vars['var'] = var
            # create a slice(b,e,s) atom and insert in 
            # place of the x:y:z atom in the tree.            
            subscript_list[i] = build_slice_atom(slice_vars, slice_position)
        
def harvest_subscript_dicts(ast_list):
    """ Needs Tests!
    """
    subscript_lists = []
    if type(ast_list)  == ListType:
        found,data = match(indexed_array_pattern,ast_list)
        # data is a dict with 'var' = variable name
        # and 'subscript_list' = to the ast_seq for the subscript list
        if found:
            subscript_lists.append(data)
        for item in ast_list:
            if type(item) == ListType:
                 subscript_lists.extend(harvest_subscript_dicts(item))
    return subscript_lists

def transform_slices(ast_list):
    """ Walk through an ast_list converting all x:y:z subscripts
        to slice(x,y,z) subscripts.
    """
    all_dicts = harvest_subscript_dicts(ast_list)
    for subscript_dict in all_dicts:
        transform_subscript_list(subscript_dict)

slice_patterns = []
CLN = (token.COLON,':')
CLN2= (symbol.sliceop, (token.COLON, ':'))
CLN2_STEP = (symbol.sliceop, (token.COLON, ':'),['step'])
# [begin:end:step]
slice_patterns.append((symbol.subscript, ['begin'],CLN,['end'], CLN2_STEP ))
# [:end:step]
slice_patterns.append((symbol.subscript,           CLN,['end'], CLN2_STEP ))
# [begin::step]
slice_patterns.append((symbol.subscript, ['begin'],CLN,          CLN2_STEP ))
# [begin:end:]
slice_patterns.append((symbol.subscript, ['begin'],CLN,['end'], CLN2      ))
# [begin::]
slice_patterns.append((symbol.subscript, ['begin'],CLN,          CLN2      ))
# [:end:]
slice_patterns.append((symbol.subscript,           CLN,['end'], CLN2,     ))
# [::step]
slice_patterns.append((symbol.subscript,           CLN,          CLN2_STEP ))
# [::]
slice_patterns.append((symbol.subscript,           CLN,          CLN2      ))

# begin:end variants
slice_patterns.append((symbol.subscript, ['begin'],CLN,['end']))
slice_patterns.append((symbol.subscript,           CLN,['end']))
slice_patterns.append((symbol.subscript, ['begin'],CLN))
slice_patterns.append((symbol.subscript,           CLN))  

# a[0] variant -- can't believe I left this out...
slice_patterns.append((symbol.subscript,['single_index']))  

indexed_array_pattern = \
           (symbol.power,
             (symbol.atom,(token.NAME, ['var'])),
             (symbol.trailer,
                (token.LSQB, '['),
                   ['subscript_list'],
                (token.RSQB, ']')
             )
           )

import os, sys
import string, re

import catalog 
import build_tools
import converters
import base_spec

class ext_function_from_specs:
    def __init__(self,name,code_block,arg_specs):
        self.name = name
        self.arg_specs = base_spec.arg_spec_list(arg_specs)
        self.code_block = code_block
        self.compiler = ''
        self.customize = base_info.custom_info()
        
    def header_code(self):
        pass

    def function_declaration_code(self):
       code  = 'static PyObject* %s(PyObject*self, PyObject* args,' \
               ' PyObject* kywds)\n{\n'
       return code % self.name

    def template_declaration_code(self):
        code = 'template<class T>\n' \
               'static PyObject* %s(PyObject*self, PyObject* args,' \
               ' PyObject* kywds)\n{\n'
        return code % self.name

    #def cpp_function_declaration_code(self):
    #    pass
    #def cpp_function_call_code(self):
    #s    pass
        
    def parse_tuple_code(self):
        """ Create code block for PyArg_ParseTuple.  Variable declarations
            for all PyObjects are done also.
            
            This code got a lot uglier when I added local_dict...
        """
        join = string.join

        declare_return = 'py::object return_val;\n' \
                         'int exception_occured = 0;\n' \
                         'PyObject *py_local_dict = NULL;\n'
        arg_string_list = self.arg_specs.variable_as_strings() + ['"local_dict"']
        arg_strings = join(arg_string_list,',')
        if arg_strings: arg_strings += ','
        declare_kwlist = 'static char *kwlist[] = {%s NULL};\n' % arg_strings

        py_objects = join(self.arg_specs.py_pointers(),', ')
        init_flags = join(self.arg_specs.init_flags(),', ')
        init_flags_init = join(self.arg_specs.init_flags(),'= ')
        py_vars = join(self.arg_specs.py_variables(),' = ')
        if py_objects:
            declare_py_objects  = 'PyObject ' + py_objects +';\n'
            declare_py_objects += 'int '+ init_flags + ';\n'            
            init_values  = py_vars + ' = NULL;\n'
            init_values += init_flags_init + ' = 0;\n\n'
        else:
            declare_py_objects = ''
            init_values = ''    

        #Each variable is in charge of its own cleanup now.
        #cnt = len(arg_list)
        #declare_cleanup = "blitz::TinyVector<PyObject*,%d> clean_up(0);\n" % cnt

        ref_string = join(self.arg_specs.py_references(),', ')
        if ref_string:
            ref_string += ', &py_local_dict'
        else:
            ref_string = '&py_local_dict'
            
        format = "O"* len(self.arg_specs) + "|O" + ':' + self.name
        parse_tuple =  'if(!PyArg_ParseTupleAndKeywords(args,' \
                             'kywds,"%s",kwlist,%s))\n' % (format,ref_string)
        parse_tuple += '   return NULL;\n'

        return   declare_return + declare_kwlist + declare_py_objects  \
               + init_values + parse_tuple

    def arg_declaration_code(self):
        arg_strings = []
        for arg in self.arg_specs:
            arg_strings.append(arg.declaration_code())
            arg_strings.append(arg.init_flag() +" = 1;\n")
        code = string.join(arg_strings,"")
        return code

    def arg_cleanup_code(self):
        arg_strings = []
        have_cleanup = filter(lambda x:x.cleanup_code(),self.arg_specs)
        for arg in have_cleanup:
            code  = "if(%s)\n" % arg.init_flag()
            code += "{\n"
            code +=     indent(arg.cleanup_code(),4)
            code += "}\n"
            arg_strings.append(code)
        code = string.join(arg_strings,"")
        return code

    def arg_local_dict_code(self):
        arg_strings = []
        for arg in self.arg_specs:
            arg_strings.append(arg.local_dict_code())
        code = string.join(arg_strings,"")
        return code
        
    def function_code(self):
        decl_code = indent(self.arg_declaration_code(),4)
        cleanup_code = indent(self.arg_cleanup_code(),4)
        function_code = indent(self.code_block,4)
        local_dict_code = indent(self.arg_local_dict_code(),4)

        dict_code = "if(py_local_dict)                                  \n"   \
                    "{                                                  \n"   \
                    "    py::dict local_dict = py::dict(py_local_dict); \n" + \
                         local_dict_code                                    + \
                    "}                                                  \n"

        try_code =    "try                              \n"   \
                      "{                                \n" + \
                           decl_code                        + \
                      "    /*<function call here>*/     \n" + \
                           function_code                    + \
                           indent(dict_code,4)              + \
                      "\n}                                \n"
        catch_code =  "catch(...)                       \n"   \
                      "{                                \n" + \
                      "    return_val =  py::object();      \n"   \
                      "    exception_occured = 1;       \n"   \
                      "}                                \n"

        return_code = "    /*cleanup code*/                     \n" + \
                           cleanup_code                             + \
                      '    if(!(PyObject*)return_val && !exception_occured)\n'   \
                      '    {\n                                  \n'   \
                      '        return_val = Py_None;            \n'   \
                      '    }\n                                  \n'   \
                      '    return return_val.disown();           \n'           \
                      '}                                \n'

        all_code = self.function_declaration_code()         + \
                       indent(self.parse_tuple_code(),4)    + \
                       indent(try_code,4)                   + \
                       indent(catch_code,4)                 + \
                       return_code

        return all_code

    def python_function_definition_code(self):
        args = (self.name, self.name)
        function_decls = '{"%s",(PyCFunction)%s , METH_VARARGS|' \
                          'METH_KEYWORDS},\n' % args
        return function_decls

    def set_compiler(self,compiler):
        self.compiler = compiler
        for arg in self.arg_specs:
            arg.set_compiler(compiler)


class ext_function(ext_function_from_specs):
    def __init__(self,name,code_block, args, local_dict=None, global_dict=None,
                 auto_downcast=1, type_converters=None):
                    
        call_frame = sys._getframe().f_back
        if local_dict is None:
            local_dict = call_frame.f_locals
        if global_dict is None:
            global_dict = call_frame.f_globals
        if type_converters is None:
            type_converters = converters.default
        arg_specs = assign_variable_types(args,local_dict, global_dict,
                                          auto_downcast, type_converters)
        ext_function_from_specs.__init__(self,name,code_block,arg_specs)
        
            
import base_info

class ext_module:
    def __init__(self,name,compiler=''):
        standard_info = converters.standard_info
        self.name = name
        self.functions = []
        self.compiler = compiler
        self.customize = base_info.custom_info()
        self._build_information = base_info.info_list(standard_info)
        
    def add_function(self,func):
        self.functions.append(func)
    def module_code(self):
        code = self.warning_code() + \
               self.header_code()  + \
               self.support_code() + \
               self.function_code() + \
               self.python_function_definition_code() + \
               self.module_init_code()
        return code

    def arg_specs(self):
        all_arg_specs = base_spec.arg_spec_list()
        for func in self.functions:
            all_arg_specs += func.arg_specs
        return all_arg_specs

    def build_information(self):
        info = [self.customize] + self._build_information + \
               self.arg_specs().build_information()
        for func in self.functions:
            info.append(func.customize)
        #redundant, but easiest place to make sure compiler is set
        for i in info:
            i.set_compiler(self.compiler)
        return info
        
    def get_headers(self):
        all_headers = self.build_information().headers()

        # blitz/array.h always needs to be first so we hack that here...
        if '"blitz/array.h"' in all_headers:
            all_headers.remove('"blitz/array.h"')
            all_headers.insert(0,'"blitz/array.h"')
        return all_headers

    def warning_code(self):
        all_warnings = self.build_information().warnings()
        w=map(lambda x: "#pragma warning(%s)\n" % x,all_warnings)
        return ''.join(w)
        
    def header_code(self):
        h = self.get_headers()
        h= map(lambda x: '#include ' + x + '\n',h)
        return ''.join(h)

    def support_code(self):
        code = self.build_information().support_code()
        return ''.join(code)

    def function_code(self):
        all_function_code = ""
        for func in self.functions:
            all_function_code += func.function_code()
        return ''.join(all_function_code)

    def python_function_definition_code(self):
        all_definition_code = ""
        for func in self.functions:
            all_definition_code += func.python_function_definition_code()
        all_definition_code =  indent(''.join(all_definition_code),4)
        code = 'static PyMethodDef compiled_methods[] = \n' \
               '{\n' \
               '%s' \
               '    {NULL,      NULL}        /* Sentinel */\n' \
               '};\n'
        return code % (all_definition_code)

    def module_init_code(self):
        init_code_list =  self.build_information().module_init_code()
        init_code = indent(''.join(init_code_list),4)
        code = 'extern "C" void init%s()\n' \
               '{\n' \
               '%s' \
               '    (void) Py_InitModule("%s", compiled_methods);\n' \
               '}\n' % (self.name,init_code,self.name)
        return code

    def generate_file(self,file_name="",location='.'):
        code = self.module_code()
        if not file_name:
            file_name = self.name + '.cpp'
        name = generate_file_name(file_name,location)
        #return name
        return generate_module(code,name)

    def set_compiler(self,compiler):
        # This is not used anymore -- I think we should ditch it.
        #for i in self.arg_specs()
        #    i.set_compiler(compiler)
        for i in self.build_information():
            i.set_compiler(compiler)    
        for i in self.functions:
            i.set_compiler(compiler)
        self.compiler = compiler    

    def build_kw_and_file(self,location,kw):    
        arg_specs = self.arg_specs()
        info = self.build_information()
        _source_files = info.sources()
        # remove duplicates
        source_files = {}
        for i in _source_files:
            source_files[i] = None
        source_files = source_files.keys()
        
        # add internally specified macros, includes, etc. to the key words
        # values of the same names so that distutils will use them.
        kw['define_macros'] = kw.get('define_macros',[]) + \
                              info.define_macros()
        kw['include_dirs'] = kw.get('include_dirs',[]) + info.include_dirs()
        kw['libraries'] = kw.get('libraries',[]) + info.libraries()
        kw['library_dirs'] = kw.get('library_dirs',[]) + info.library_dirs()
        kw['extra_compile_args'] = kw.get('extra_compile_args',[]) + \
                                   info.extra_compile_args()
        kw['extra_link_args'] = kw.get('extra_link_args',[]) + \
                                   info.extra_link_args()
        kw['sources'] = kw.get('sources',[]) + source_files        
        file = self.generate_file(location=location)
        return kw,file
    
    def setup_extension(self,location='.',**kw):
        kw,file = self.build_kw_and_file(location,kw)
        return build_tools.create_extension(file, **kw)
            
    def compile(self,location='.',compiler=None, verbose = 0, **kw):
        
        if compiler is not None:
            self.compiler = compiler
        
        # !! removed -- we don't have any compiler dependent code
        # currently in spec or info classes    
        # hmm.  Is there a cleaner way to do this?  Seems like
        # choosing the compiler spagettis around a little.        
        #compiler = build_tools.choose_compiler(self.compiler)    
        #self.set_compiler(compiler)
        
        kw,file = self.build_kw_and_file(location,kw)
        
        # This is needed so that files build correctly even when different
        # versions of Python are running around.
        # Imported at beginning of file now to help with test paths.
        # import catalog 
        #temp = catalog.default_temp_dir()
        # for speed, build in the machines temp directory
        temp = catalog.intermediate_dir()
                
        success = build_tools.build_extension(file, temp_dir = temp,
                                              compiler_name = compiler,
                                              verbose = verbose, **kw)
        if not success:
            raise SystemError, 'Compilation failed'

def generate_file_name(module_name,module_location):
    module_file = os.path.join(module_location,module_name)
    return os.path.abspath(module_file)

def generate_module(module_string, module_file):
    """ generate the source code file.  Only overwrite
        the existing file if the actual source has changed.
    """
    file_changed = 1
    if os.path.exists(module_file):
        f =open(module_file,'r')
        old_string = f.read()
        f.close()
        if old_string == module_string:
            file_changed = 0
    if file_changed:
        print 'file changed'
        f =open(module_file,'w')
        f.write(module_string)
        f.close()
    return module_file

def assign_variable_types(variables,local_dict = {}, global_dict = {},
                          auto_downcast = 1,
                          type_converters = converters.default):
    incoming_vars = {}
    incoming_vars.update(global_dict)
    incoming_vars.update(local_dict)
    variable_specs = []
    errors={}
    for var in variables:
        try:
            example_type = incoming_vars[var]

            # look through possible type specs to find which one
            # should be used to for example_type
            spec = None
            for factory in type_converters:
                if factory.type_match(example_type):
                    spec = factory.type_spec(var,example_type)
                    break                
            if not spec:
                # should really define our own type.
                raise IndexError
            else:
                variable_specs.append(spec)
        except KeyError:
            errors[var] = ("The type and dimensionality specifications" +
                           "for variable '" + var + "' are missing.")
        except IndexError:
            errors[var] = ("Unable to convert variable '"+ var +
                           "' to a C++ type.")
    if errors:
        raise TypeError, format_error_msg(errors)

    if auto_downcast:
        variable_specs = downcast(variable_specs)
    return variable_specs

def downcast(var_specs):
    """ Cast python scalars down to most common type of
         arrays used.

         Right now, focus on complex and float types. Ignore int types.
         Require all arrays to have same type before forcing downcasts.

         Note: var_specs are currently altered in place (horrors...!)
    """
    numeric_types = []

    #grab all the numeric types associated with a variables.
    for var in var_specs:
        if hasattr(var,'numeric_type'):
            numeric_types.append(var.numeric_type)

    # if arrays are present, but none of them are double precision,
    # make all numeric types float or complex(float)
    if (    ('f' in numeric_types or 'F' in numeric_types) and
        not ('d' in numeric_types or 'D' in numeric_types) ):
        for var in var_specs:
            if hasattr(var,'numeric_type'):
                # really should do this some other way...
                if var.numeric_type == type(1+1j):
                    var.numeric_type = 'F'
                elif var.numeric_type == type(1.):
                    var.numeric_type = 'f'
    return var_specs

def indent(st,spaces):
    indention = ' '*spaces
    indented = indention + string.replace(st,'\n','\n'+indention)
    # trim off any trailing spaces
    indented = re.sub(r' +$',r'',indented)
    return indented

def format_error_msg(errors):
    #minimum effort right now...
    import pprint,cStringIO
    msg = cStringIO.StringIO()
    pprint.pprint(errors,msg)
    return msg.getvalue()

""" converters.py
"""

import common_info
import c_spec

#----------------------------------------------------------------------------
# The "standard" conversion classes
#----------------------------------------------------------------------------

default = [c_spec.int_converter(),
           c_spec.float_converter(),
           c_spec.complex_converter(),
           c_spec.unicode_converter(),
           c_spec.string_converter(),
           c_spec.list_converter(),
           c_spec.dict_converter(),
           c_spec.tuple_converter(),
           c_spec.file_converter(),
           c_spec.instance_converter(),]                          
          #common_spec.module_converter()]

#----------------------------------------------------------------------------
# If Numeric is installed, add numeric array converters to the default
# converter list.
#----------------------------------------------------------------------------
try: 
    import standard_array_spec
    default.append(standard_array_spec.array_converter())
except ImportError: 
    pass    

#----------------------------------------------------------------------------
# Add wxPython support
#
# RuntimeError can occur if wxPython isn't installed.
#----------------------------------------------------------------------------

try: 
    # this is currently safe because it doesn't import wxPython.
    import wx_spec
    default.insert(0,wx_spec.wx_converter())
except (RuntimeError,IndexError): 
    pass

#----------------------------------------------------------------------------
# Add VTK support
#----------------------------------------------------------------------------

try: 
    import vtk_spec
    default.insert(0,vtk_spec.vtk_converter())
except IndexError: 
    pass

#----------------------------------------------------------------------------
# Add "sentinal" catchall converter
#
# if everything else fails, this one is the last hope (it always works)
#----------------------------------------------------------------------------

default.append(c_spec.catchall_converter())

standard_info = [common_info.basic_module_info()]
standard_info += [x.generate_build_info() for x in default]

#----------------------------------------------------------------------------
# Blitz conversion classes
#
# same as default, but will convert Numeric arrays to blitz C++ classes 
# !! only available if Numeric is installed !!
#----------------------------------------------------------------------------
try:
    import blitz_spec
    blitz = [blitz_spec.array_converter()] + default
    #-----------------------------------
    # Add "sentinal" catchall converter
    #
    # if everything else fails, this one 
    # is the last hope (it always works)
    #-----------------------------------
    blitz.append(c_spec.catchall_converter())
except:
    pass


""" Information about platform and python version and compilers

    This information is manly used to build directory names that
    keep the object files and shared libaries straight when
    multiple platforms share the same file system.
"""

import os, sys

import distutils
from distutils.sysconfig import customize_compiler


try:
    from scipy_distutils.ccompiler import new_compiler
    from scipy_distutils.core import Extension, setup
    from scipy_distutils.command.build_ext import build_ext
except ImportError:
    from distutils.ccompiler import new_compiler
    from distutils.core import Extension, setup
    from distutils.command.build_ext import build_ext

import distutils.bcppcompiler

#from scipy_distutils import mingw32_support

def dummy_dist():
    # create a dummy distribution.  It will look at any site configuration files
    # and parse the command line to pick up any user configured stuff.  The 
    # resulting Distribution object is returned from setup.
    # Setting _setup_stop_after prevents the any commands from actually executing.
    distutils.core._setup_stop_after = "commandline"
    dist = setup(name="dummy")
    distutils.core._setup_stop_after = None
    return dist

def create_compiler_instance(dist):    
    # build_ext is in charge of building C/C++ files.
    # We are using it and dist to parse config files, and command line 
    # configurations.  There may be other ways to handle this, but I'm
    # worried I may miss one of the steps in distutils if I do it my self.
    #ext_builder = build_ext(dist)
    #ext_builder.finalize_options ()
    
    # For some reason the build_ext stuff wasn't picking up the compiler 
    # setting, so we grab it manually from the distribution object instead.
    opts = dist.command_options.get('build_ext',None)
    compiler_name = ''
    if opts:
        comp = opts.get('compiler',('',''))
        compiler_name = comp[1]
        
    # Create a new compiler, customize it based on the build settings,
    # and return it. 
    if not compiler_name:
        compiler_name = None
    print compiler_name    
    compiler = new_compiler(compiler=compiler_name)
    customize_compiler(compiler)
    return compiler

def compiler_exe_name(compiler):    
    exe_name = ''
    # this is really ugly...  Why aren't the attribute names 
    # standardized and used in a consistent way?
    if hasattr(compiler, "compiler"):
        # standard unix format
        exe_name = compiler.compiler[0]
    elif hasattr(compiler, "cc"):
        exe_name = compiler.cc
    elif compiler.__class__ is distutils.bcppcompiler.BCPPCompiler:
        exe_name = 'brcc32'
    return exe_name

def compiler_exe_path(exe_name):
    exe_path = None
    if os.path.exists(exe_name):
        exe_path = exe_name
    else:
        path_string = os.environ['PATH']
        path_string = os.path.expandvars(path_string)
        path_string = os.path.expanduser(path_string)
        paths = path_string.split(os.pathsep)
        for path in paths:
            path = os.path.join(path,exe_name)
            if os.path.exists(path):
                exe_path = path
                break               
            # needed to catch gcc on mingw32 installations.    
            path = path + '.exe'    
            if os.path.exists(path):
                exe_path = path
                break
    return exe_path

def check_sum(file):
    
    import md5
    try:
        f = open(file,'r')
        bytes = f.read(-1)
    except IOError:
        bytes = ''    
    chk_sum = md5.md5(bytes)
    return chk_sum.hexdigest()

def get_compiler_dir(compiler_name):
    """ Try to figure out the compiler directory based on the
        input compiler name.  This is fragile and really should
        be done at the distutils level inside the compiler.  I
        think it is only useful on windows at the moment.
    """
    compiler_type = choose_compiler(compiler_name)
    #print compiler_type
    configure_sys_argv(compiler_type)
    #print sys.argv
    dist = dummy_dist()    
    compiler_obj = create_compiler_instance(dist)
    #print compiler_obj.__class__
    exe_name = compiler_exe_name(compiler_obj)
    exe_path = compiler_exe_path(exe_name)
    if not exe_path:
        raise ValueError, "The '%s' compiler was not found." % compiler_name
    chk_sum = check_sum(exe_path)    
    restore_sys_argv()
    
    return 'compiler_'+chk_sum

#----------------------------------------------------------------------------
# Not needed -- used for testing.
#----------------------------------------------------------------------------

def choose_compiler(compiler_name=''):
    """ Try and figure out which compiler is gonna be used on windows.
        On other platforms, it just returns whatever value it is given.
        
        converts 'gcc' to 'mingw32' on win32
    """
    if not compiler_name:
        compiler_name = ''
        
    if sys.platform == 'win32':        
        if not compiler_name:
            # On Windows, default to MSVC and use gcc if it wasn't found
            # wasn't found.  If neither are found, go with whatever
            # the default is for distutils -- and probably fail...
            if msvc_exists():
                compiler_name = 'msvc'
            elif gcc_exists():
                compiler_name = 'mingw32'
        elif compiler_name == 'gcc':
                compiler_name = 'mingw32'
    else:
        # don't know how to force gcc -- look into this.
        if compiler_name == 'gcc':
                compiler_name = 'unix'                    
    return compiler_name

old_argv = []
def configure_sys_argv(compiler_name):
    # We're gonna play some tricks with argv here to pass info to distutils 
    # which is really built for command line use. better way??
    global old_argv
    old_argv = sys.argv[:]        
    sys.argv = ['','build_ext','--compiler='+compiler_name]

def restore_sys_argv():
    sys.argv = old_argv

def gcc_exists(name = 'gcc'):
    """ Test to make sure gcc is found 
       
        Does this return correct value on win98???
    """
    result = 0
    cmd = '%s -v' % name
    try:
        w,r=os.popen4(cmd)
        w.close()
        str_result = r.read()
        #print str_result
        if string.find(str_result,'Reading specs') != -1:
            result = 1
    except:
        # This was needed because the msvc compiler messes with
        # the path variable. and will occasionlly mess things up
        # so much that gcc is lost in the path. (Occurs in test
        # scripts)
        result = not os.system(cmd)
    return result

def msvc_exists():
    """ Determine whether MSVC is available on the machine.
    """
    result = 0
    try:
        w,r=os.popen4('cl')
        w.close()
        str_result = r.read()
        #print str_result
        if string.find(str_result,'Microsoft') != -1:
            result = 1
    except:
        #assume we're ok if devstudio exists
        import distutils.msvccompiler

        # There was a change to 'distutils.msvccompiler' between Python 2.2
        # and Python 2.3.
        #
        # In Python 2.2 the function is 'get_devstudio_versions'
        # In Python 2.3 the function is 'get_build_version'
        try:
            version = distutils.msvccompiler.get_devstudio_versions()
            
        except:
            version = distutils.msvccompiler.get_build_version()
            
        if version:
            result = 1
    return result

if __name__ == "__main__":
    """
    import time
    t1 = time.time()    
    dist = dummy_dist()    
    compiler_obj = create_compiler_instance(dist)
    exe_name = compiler_exe_name(compiler_obj)
    exe_path = compiler_exe_path(exe_name)
    chk_sum = check_sum(exe_path)    
    
    t2 = time.time()
    print 'compiler exe:', exe_path
    print 'check sum:', chk_sum
    print 'time (sec):', t2 - t1
    print
    """
    path = get_compiler_dir('gcc')
    print 'gcc path:', path
    print
    try: 
        path = get_compiler_dir('msvc')
        print 'gcc path:', path
    except ValueError:
        pass    

"""A dumb and slow but simple dbm clone.

For database spam, spam.dir contains the index (a text file),
spam.bak *may* contain a backup of the index (also a text file),
while spam.dat contains the data (a binary file).

XXX TO DO:

- seems to contain a bug when updating...

- reclaim free space (currently, space once occupied by deleted or expanded
items is never reused)

- support concurrent access (currently, if two processes take turns making
updates, they can mess up the index)

- support efficient access to large databases (currently, the whole index
is read when the database is opened, and some updates rewrite the whole index)

- support opening for read-only (flag = 'm')

"""

_os = __import__('os')
import __builtin__

_open = __builtin__.open

_BLOCKSIZE = 512

error = IOError             # For anydbm

class _Database:

    def __init__(self, file):
        self._dirfile = file + '.dir'
        self._datfile = file + '.dat'
        self._bakfile = file + '.bak'
        # Mod by Jack: create data file if needed
        try:
            f = _open(self._datfile, 'r')
        except IOError:
            f = _open(self._datfile, 'w')
        f.close()
        self._update()
    
    def _update(self):
        import string   
        self._index = {}
        try:
            f = _open(self._dirfile)
        except IOError:
            pass
        else:
            while 1:
                line = string.rstrip(f.readline())
                if not line: break
                key, (pos, siz) = eval(line)
                self._index[key] = (pos, siz)
            f.close()

    def _commit(self):
        try: _os.unlink(self._bakfile)
        except _os.error: pass
        try: _os.rename(self._dirfile, self._bakfile)
        except _os.error: pass
        f = _open(self._dirfile, 'w')
        for key, (pos, siz) in self._index.items():
            f.write("%s, (%s, %s)\n" % (`key`, `pos`, `siz`))
        f.close()
    
    def __getitem__(self, key):
        pos, siz = self._index[key] # may raise KeyError
        f = _open(self._datfile, 'rb')
        f.seek(pos)
        dat = f.read(siz)
        f.close()
        return dat
    
    def _addval(self, val):
        f = _open(self._datfile, 'rb+')
        f.seek(0, 2)
        pos = f.tell()
## Does not work under MW compiler
##      pos = ((pos + _BLOCKSIZE - 1) / _BLOCKSIZE) * _BLOCKSIZE
##      f.seek(pos)
        npos = ((pos + _BLOCKSIZE - 1) / _BLOCKSIZE) * _BLOCKSIZE
        f.write('\0'*(npos-pos))
        pos = npos
        
        f.write(val)
        f.close()
        return (pos, len(val))
    
    def _setval(self, pos, val):
        f = _open(self._datfile, 'rb+')
        f.seek(pos)
        f.write(val)
        f.close()
        return (pos, len(val))
    
    def _addkey(self, key, (pos, siz)):
        self._index[key] = (pos, siz)
        f = _open(self._dirfile, 'a')
        f.write("%s, (%s, %s)\n" % (`key`, `pos`, `siz`))
        f.close()
    
    def __setitem__(self, key, val):
        if not type(key) == type('') == type(val):
            raise TypeError, "keys and values must be strings"
        if not self._index.has_key(key):
            (pos, siz) = self._addval(val)
            self._addkey(key, (pos, siz))
        else:
            pos, siz = self._index[key]
            oldblocks = (siz + _BLOCKSIZE - 1) / _BLOCKSIZE
            newblocks = (len(val) + _BLOCKSIZE - 1) / _BLOCKSIZE
            if newblocks <= oldblocks:
                pos, siz = self._setval(pos, val)
                self._index[key] = pos, siz
            else:
                pos, siz = self._addval(val)
                self._index[key] = pos, siz
            self._addkey(key, (pos, siz))
    
    def __delitem__(self, key):
        del self._index[key]
        self._commit()
    
    def keys(self):
        return self._index.keys()
    
    def has_key(self, key):
        return self._index.has_key(key)
    
    def __len__(self):
        return len(self._index)
    
    def close(self):
        self._index = None
        self._datfile = self._dirfile = self._bakfile = None


def open(file, flag = None, mode = None):
    # flag, mode arguments are currently ignored
    return _Database(file)

""" Generic support code for: 
        error handling code found in every weave module      
        local/global dictionary access code for inline() modules
        swig pointer (old style) conversion support
        
"""

import base_info

module_support_code = \
"""

// global None value for use in functions.
namespace py {
object None = object(Py_None);
}

char* find_type(PyObject* py_obj)
{
    if(py_obj == NULL) return "C NULL value";
    if(PyCallable_Check(py_obj)) return "callable";
    if(PyString_Check(py_obj)) return "string";
    if(PyInt_Check(py_obj)) return "int";
    if(PyFloat_Check(py_obj)) return "float";
    if(PyDict_Check(py_obj)) return "dict";
    if(PyList_Check(py_obj)) return "list";
    if(PyTuple_Check(py_obj)) return "tuple";
    if(PyFile_Check(py_obj)) return "file";
    if(PyModule_Check(py_obj)) return "module";
    
    //should probably do more intergation (and thinking) on these.
    if(PyCallable_Check(py_obj) && PyInstance_Check(py_obj)) return "callable";
    if(PyInstance_Check(py_obj)) return "instance"; 
    if(PyCallable_Check(py_obj)) return "callable";
    return "unkown type";
}

void throw_error(PyObject* exc, const char* msg)
{
 //printf("setting python error: %s\\n",msg);
  PyErr_SetString(exc, msg);
  //printf("throwing error\\n");
  throw 1;
}

void handle_bad_type(PyObject* py_obj, const char* good_type, const char* var_name)
{
    char msg[500];
    sprintf(msg,"received '%s' type instead of '%s' for variable '%s'",
            find_type(py_obj),good_type,var_name);
    throw_error(PyExc_TypeError,msg);    
}

void handle_conversion_error(PyObject* py_obj, const char* good_type, const char* var_name)
{
    char msg[500];
    sprintf(msg,"Conversion Error:, received '%s' type instead of '%s' for variable '%s'",
            find_type(py_obj),good_type,var_name);
    throw_error(PyExc_TypeError,msg);
}

"""
#include "compile.h" /* Scary dangerous stuff */
#include "frameobject.h" /* Scary dangerous stuff */

class basic_module_info(base_info.base_info):
    _headers = ['"Python.h"','"compile.h"','"frameobject.h"']
    _support_code = [module_support_code]

#----------------------------------------------------------------------------
# inline() generated support code
#
# The following two function declarations handle access to variables in the 
# global and local dictionaries for inline functions.
#----------------------------------------------------------------------------

get_variable_support_code = \
"""
void handle_variable_not_found(char*  var_name)
{
    char msg[500];
    sprintf(msg,"Conversion Error: variable '%s' not found in local or global scope.",var_name);
    throw_error(PyExc_NameError,msg);
}
PyObject* get_variable(char* name,PyObject* locals, PyObject* globals)
{
    // no checking done for error -- locals and globals should
    // already be validated as dictionaries.  If var is NULL, the
    // function calling this should handle it.
    PyObject* var = NULL;
    var = PyDict_GetItemString(locals,name);
    if (!var)
    {
        var = PyDict_GetItemString(globals,name);
    }
    if (!var)
        handle_variable_not_found(name);
    return var;
}
"""

py_to_raw_dict_support_code = \
"""
PyObject* py_to_raw_dict(PyObject* py_obj, char* name)
{
    // simply check that the value is a valid dictionary pointer.
    if(!py_obj || !PyDict_Check(py_obj))
        handle_bad_type(py_obj, "dictionary", name);
    return py_obj;
}
"""

class inline_info(base_info.base_info):
    _support_code = [get_variable_support_code, py_to_raw_dict_support_code]


#----------------------------------------------------------------------------
# swig pointer support code
#
# The support code for swig is just slirped in from the swigptr.c file 
# from the *old* swig distribution.  The code from swigptr.c is now a string
# in swigptr.py to ease the process of incorporating it into py2exe 
# installations. New style swig pointers are not yet supported.
#----------------------------------------------------------------------------

import swigptr
swig_support_code = swigptr.swigptr_code

class swig_info(base_info.base_info):
    _support_code = [swig_support_code]

"""
VTK type converter.

This module handles conversion between VTK C++ and VTK Python objects
so that one can write inline C++ code to manipulate VTK Python
objects.  It requires that you have VTK and the VTK-Python wrappers
installed.  It has been tested with VTK 4.0 and above.  The code is
based on wx_spec.py.  You will need to call inline with include_dirs,
library_dirs and often even libraries appropriately set for this to
work without errors.  Sometimes you might need to include additional
headers.

Distributed under the SciPy License.

Authors:
  Prabhu Ramachandran <prabhu@aero.iitm.ernet.in>
  Eric Jones <eric@enthought.com>
"""

import common_info
from c_spec import common_base_converter


vtk_py_to_c_template = \
"""
class %(type_name)s_handler
{
public:
    %(c_type)s convert_to_%(type_name)s(PyObject* py_obj, const char* name)
    {
        %(c_type)s vtk_ptr = (%(c_type)s) vtkPythonGetPointerFromObject(py_obj, "%(type_name)s");
        if (!vtk_ptr)
            handle_conversion_error(py_obj,"%(type_name)s", name);
        %(inc_ref_count)s
        return vtk_ptr;
    }

    %(c_type)s py_to_%(type_name)s(PyObject* py_obj, const char* name)
    {
        %(c_type)s vtk_ptr = (%(c_type)s) vtkPythonGetPointerFromObject(py_obj, "%(type_name)s");
        if (!vtk_ptr)
            handle_bad_type(py_obj,"%(type_name)s", name);
        %(inc_ref_count)s
        return vtk_ptr;
    }
};

%(type_name)s_handler x__%(type_name)s_handler = %(type_name)s_handler();
#define convert_to_%(type_name)s(py_obj,name) \\
        x__%(type_name)s_handler.convert_to_%(type_name)s(py_obj,name)
#define py_to_%(type_name)s(py_obj,name) \\
        x__%(type_name)s_handler.py_to_%(type_name)s(py_obj,name)

"""

vtk_c_to_py_template = \
"""
PyObject* %(type_name)s_to_py(vtkObjectBase* obj)
{
    return vtkPythonGetObjectFromPointer(obj);
}
"""
                  

class vtk_converter(common_base_converter):
    def __init__(self,class_name="undefined"):
        self.class_name = class_name
        common_base_converter.__init__(self)

    def init_info(self):
        common_base_converter.init_info(self)
        # These are generated on the fly instead of defined at 
        # the class level.
        self.type_name = self.class_name
        self.c_type = self.class_name + "*"
        self.return_type = self.c_type        
        self.to_c_return = None # not used
        self.check_func = None # not used
        hdr = self.class_name + ".h"
        # Remember that you need both the quotes!
        self.headers.extend(['"vtkPythonUtil.h"', '"vtkObject.h"',
                             '"%s"'%hdr])
        #self.include_dirs.extend(vtk_inc)
        #self.define_macros.append(('SOME_VARIABLE', '1'))
        #self.library_dirs.extend(vtk_lib)
        self.libraries.extend(['vtkCommonPython', 'vtkCommon'])
        #self.support_code.append(common_info.swig_support_code)
    
    def type_match(self,value):
        is_match = 0
        try:
            if value.IsA('vtkObject'):
                is_match = 1
        except AttributeError:
            pass
        return is_match

    def generate_build_info(self):
        if self.class_name != "undefined":
            res = common_base_converter.generate_build_info(self)
        else:
            # if there isn't a class_name, we don't want the
            # we don't want the support_code to be included
            import base_info
            res = base_info.base_info()
        return res
        
    def py_to_c_code(self):
        return vtk_py_to_c_template % self.template_vars()

    def c_to_py_code(self):
        return vtk_c_to_py_template % self.template_vars()
                    
    def type_spec(self,name,value):
        # factory
        class_name = value.__class__.__name__
        new_spec = self.__class__(class_name)
        new_spec.name = name        
        return new_spec

    def __cmp__(self,other):
        #only works for equal
        res = -1
        try:
            res = cmp(self.name,other.name) or \
                  cmp(self.__class__, other.__class__) or \
                  cmp(self.class_name, other.class_name) or \
                  cmp(self.type_name,other.type_name)
        except:
            pass
        return res

import weave
import time

force = 0
N = 1000000

def list_append_scxx(a,Na):
    code = """
           for(int i = 0; i < Na;i++)
               a.append(i);  
           """
    weave.inline(code,['a','Na'],force=force,verbose=2,compiler='gcc')

def list_append_c(a,Na):
    code = """
           for(int i = 0; i < Na;i++)
           {
               PyObject* oth = PyInt_FromLong(i);
               int res = PyList_Append(py_a,oth);
               Py_DECREF(oth);
               if(res == -1)
               {
                 PyErr_Clear();  //Python sets one 
                 throw_error(PyExc_RuntimeError, "append failed");
               }  
           }
           """
    weave.inline(code,['a','Na'],force=force,compiler='gcc')

def list_append_py(a,Na):
    for i in xrange(Na):
        a.append(i)

def time_list_append(Na):
    """ Compare the list append method from scxx to using the Python API
        directly.
    """
    print 'list appending times:', 

    a = []
    t1 = time.time()
    list_append_c(a,Na)
    t2 = time.time()
    print 'py api: ', t2 - t1, '<note: first time takes longer -- repeat below>'
    
    a = []
    t1 = time.time()
    list_append_c(a,Na)
    t2 = time.time()
    print 'py api: ', t2 - t1
    
    a = []
    t1 = time.time()
    list_append_scxx(a,Na)
    t2 = time.time()
    print 'scxx:   ', t2 - t1    
    
    a = []
    t1 = time.time()
    list_append_c(a,Na)
    t2 = time.time()
    print 'python: ', t2 - t1

#----------------------------------------------------------------------------
#
#----------------------------------------------------------------------------

def list_copy_scxx(a,b):
    code = """
           for(int i = 0; i < a.length();i++)
               b[i] = a[i];  
           """
    weave.inline(code,['a','b'],force=force,verbose=2,compiler='gcc')

def list_copy_c(a,b):
    code = """
           for(int i = 0; i < a.length();i++)
           {
               int res = PySequence_SetItem(py_b,i,PyList_GET_ITEM(py_a,i));
               if(res == -1)
               {
                 PyErr_Clear();  //Python sets one 
                 throw_error(PyExc_RuntimeError, "append failed");
               }  
           }
           """
    weave.inline(code,['a','b'],force=force,compiler='gcc')

def list_copy_py(a,b):
    for item in a:
        b[i] = item

def time_list_copy(N):
    """ Compare the list append method from scxx to using the Python API
        directly.
    """
    print 'list copy times:', 

    a = [0] * N
    b = [1] * N
    t1 = time.time()
    list_copy_c(a,b)
    t2 = time.time()
    print 'py api: ', t2 - t1, '<note: first time takes longer -- repeat below>'
    
    a = [0] * N
    b = [1] * N
    t1 = time.time()
    list_copy_c(a,b)
    t2 = time.time()
    print 'py api: ', t2 - t1
    
    a = [0] * N
    b = [1] * N
    t1 = time.time()
    list_copy_scxx(a,b)
    t2 = time.time()
    print 'scxx:   ', t2 - t1    
    
    a = [0] * N
    b = [1] * N
    t1 = time.time()
    list_copy_c(a,b)
    t2 = time.time()
    print 'python: ', t2 - t1
            
if __name__ == "__main__":
    #time_list_append(N)
    time_list_copy(N)
import os,sys,string
import pprint 

def remove_whitespace(in_str):
    import string
    out = string.replace(in_str," ","")
    out = string.replace(out,"\t","")
    out = string.replace(out,"\n","")
    return out
    
def print_assert_equal(test_string,actual,desired):
    """this should probably be in scipy_test.testing
    """
    try:
        assert(actual == desired)
    except AssertionError:
        import cStringIO
        msg = cStringIO.StringIO()
        msg.write(test_string)
        msg.write(' failed\nACTUAL: \n')
        pprint.pprint(actual,msg)
        msg.write('DESIRED: \n')
        pprint.pprint(desired,msg)
        raise AssertionError, msg.getvalue()

###################################################
# mainly used by catalog tests               
###################################################
from scipy_distutils.misc_util import add_grandparent_to_path,restore_path

add_grandparent_to_path(__name__)
import catalog
restore_path()

import glob

def temp_catalog_files(prefix=''):
    # might need to add some more platform specific catalog file
    # suffixes to remove.  The .pag was recently added for SunOS
    d = catalog.default_dir()
    f = catalog.os_dependent_catalog_name()
    return glob.glob(os.path.join(d,prefix+f+'*'))

import tempfile

def clear_temp_catalog():
    """ Remove any catalog from the temp dir
    """
    global backup_dir 
    backup_dir =tempfile.mktemp()
    os.mkdir(backup_dir)
    for file in temp_catalog_files():
        move_file(file,backup_dir)
        #d,f = os.path.split(file)
        #backup = os.path.join(backup_dir,f)
        #os.rename(file,backup)

def restore_temp_catalog():
    """ Remove any catalog from the temp dir
    """
    global backup_dir
    cat_dir = catalog.default_dir()
    for file in os.listdir(backup_dir):
        file = os.path.join(backup_dir,file)
        d,f = os.path.split(file)
        dst_file = os.path.join(cat_dir, f)
        if os.path.exists(dst_file):
            os.remove(dst_file)
        #os.rename(file,dst_file)
        move_file(file,dst_file)
    os.rmdir(backup_dir)
    backup_dir = None
         
def empty_temp_dir():
    """ Create a sub directory in the temp directory for use in tests
    """
    import tempfile
    d = catalog.default_dir()
    for i in range(10000):
        new_d = os.path.join(d,tempfile.gettempprefix()[1:-1]+`i`)
        if not os.path.exists(new_d):
            os.mkdir(new_d)
            break
    return new_d

def cleanup_temp_dir(d):
    """ Remove a directory created by empty_temp_dir
        should probably catch errors
    """
    files = map(lambda x,d=d: os.path.join(d,x),os.listdir(d))
    for i in files:
        try:
            if os.path.isdir(i):
                cleanup_temp_dir(i)
            else:
                os.remove(i)
        except OSError:
            pass # failed to remove file for whatever reason 
                 # (maybe it is a DLL Python is currently using)        
    try:
        os.rmdir(d)
    except OSError:
        pass        
        

# from distutils -- old versions had bug, so copying here to make sure 
# a working version is available.
from distutils.errors import DistutilsFileError
import distutils.file_util
def move_file (src, dst,
               verbose=0,
               dry_run=0):

    """Move a file 'src' to 'dst'.  If 'dst' is a directory, the file will
    be moved into it with the same name; otherwise, 'src' is just renamed
    to 'dst'.  Return the new full name of the file.

    Handles cross-device moves on Unix using 'copy_file()'.  What about
    other systems???
    """
    from os.path import exists, isfile, isdir, basename, dirname
    import errno

    if verbose:
        print "moving %s -> %s" % (src, dst)

    if dry_run:
        return dst

    if not isfile(src):
        raise DistutilsFileError, \
              "can't move '%s': not a regular file" % src

    if isdir(dst):
        dst = os.path.join(dst, basename(src))
    elif exists(dst):
        raise DistutilsFileError, \
              "can't move '%s': destination '%s' already exists" % \
              (src, dst)

    if not isdir(dirname(dst)):
        raise DistutilsFileError, \
              "can't move '%s': destination '%s' not a valid path" % \
              (src, dst)

    copy_it = 0
    try:
        os.rename(src, dst)
    except os.error, (num, msg):
        if num == errno.EXDEV:
            copy_it = 1
        else:
            raise DistutilsFileError, \
                  "couldn't move '%s' to '%s': %s" % (src, dst, msg)

    if copy_it:
        distutils.file_util.copy_file(src, dst)
        try:
            os.unlink(src)
        except os.error, (num, msg):
            try:
                os.unlink(dst)
            except os.error:
                pass
            raise DistutilsFileError, \
                  ("couldn't move '%s' to '%s' by copy/delete: " +
                   "delete '%s' failed: %s") % \
                  (src, dst, src, msg)

    return dst

        
import sys
sys.path.insert(0,'..')
import inline_tools

import time

def print_compare(n):
    print 'Printing %d integers:'%n
    t1 = time.time()
    for i in range(n):
        print i,
    t2 = time.time()
    py = (t2-t1)
    
    # get it in cache
    inline_tools.inline('printf("%d",i);',['i'])
    t1 = time.time()
    for i in range(n):
        inline_tools.inline('printf("%d",i);',['i'])
    t2 = time.time()
    print ' speed in python:', py
    print ' speed in c:',(t2 - t1)    
    print ' speed up: %3.2f' % (py/(t2-t1))

def cout_example(lst):
    # get it in cache
    i = lst[0]
    inline_tools.inline('std::cout << i << std::endl;',['i'])
    t1 = time.time()
    for i in lst:
        inline_tools.inline('std::cout << i << std::endl;',['i'])
    t2 = time.time()
    
if __name__ == "__main__":
    n = 3000
    print_compare(n)    
    print "calling cout with integers:"
    cout_example([1,2,3])
    print "calling cout with strings:"
    cout_example(['a','bb', 'ccc'])
# Offers example of inline C for binary search algorithm.
# Borrowed from Kalle Svensson in the Python Cookbook.
# The results are nearly in the "not worth it" catagory.
#
# C:\home\ej\wrk\scipy\compiler\examples>python binary_search.py
# Binary search for 3000 items in 100000 length list of integers:
#  speed in python: 0.139999985695
#  speed in c: 0.0900000333786
#  speed up: 1.41
# search(a,3450) 3450 3450
# search(a,-1) -1 -1
# search(a,10001) 10001 10001
#
# Note -- really need to differentiate between conversion errors and
# run time errors.  This would reduce useless compiles and provide a
# more intelligent control of things.

import sys
sys.path.insert(0,'..')
#from compiler import inline_tools
import inline_tools
from bisect import bisect
import types

def c_int_search(seq,t,chk=1):
    # do partial type checking in Python.
    # checking that list items are ints should happen in py_to_scalar<int>
    #if chk:
    #    assert(type(t) is int)
    #    assert(type(seq) is list)
    code = """     
           #line 33 "binary_search.py"
           if (!PyList_Check(py_seq))
               py::fail(PyExc_TypeError, "seq must be a list");
           if (!PyInt_Check(py_t))
               py::fail(PyExc_TypeError, "t must be an integer");               
           int val, m, min = 0; 
           int max = seq.len()- 1;
           for(;;) 
           { 
               if (max < min )
               {
                   return_val = -1;
                   break;
               }
               m = (min + max) / 2;
               val = py_to_int(PyList_GET_ITEM(py_seq,m),"val");
               if (val < t)     
                   min = m + 1;
               else if (val > t)    
                   max = m - 1;
               else
               {
                   return_val = m;
                   break;
               }
           }      
           """    
    #return inline_tools.inline(code,['seq','t'],compiler='msvc')
    return inline_tools.inline(code,['seq','t'],verbose = 2)

def c_int_search_scxx(seq,t,chk=1):
    # do partial type checking in Python.
    # checking that list items are ints should happen in py_to_scalar<int>
    if chk:
        assert(type(t) is int)
        assert(type(seq) is list)
    code = """     
           #line 67 "binary_search.py"
           int val, m, min = 0; 
           int max = seq.len()- 1;
           for(;;) 
           { 
               if (max < min )
               {
                   return_val = -1;
                   break;
               }
               m = (min + max) / 2;
               val = seq[m];
               if (val < t)     
                   min = m + 1;
               else if (val > t)    
                   max = m - 1;
               else
               {
                   return_val = m;
                   break;
               }
           }      
           """    
    #return inline_tools.inline(code,['seq','t'],compiler='msvc')
    return inline_tools.inline(code,['seq','t'],verbose = 2)

try:
    from Numeric import *
    def c_array_int_search(seq,t):
        code = """     
               #line 62 "binary_search.py"
               int val, m, min = 0; 
               int max = Nseq[0] - 1;
               PyObject *py_val;
               for(;;) 
               { 
                   if (max < min )
                   {
                       return_val = PyInt_FromLong(-1);
                       break;
                   }
                   m = (min + max) / 2;
                   val = seq[m];
                   if (val < t)     
                       min = m + 1;
                   else if (val > t)    
                       max = m - 1;
                   else
                   {
                       return_val = PyInt_FromLong(m);
                       break;
                   }
               }        
               """    
        #return inline_tools.inline(code,['seq','t'],compiler='msvc')
        return inline_tools.inline(code,['seq','t'],verbose = 2,
                                   extra_compile_args=['-O2','-G6'])
except:
    pass
        
def py_int_search(seq, t):
    min = 0; max = len(seq) - 1
    while 1:
        if max < min:
            return -1
        m = (min + max) / 2
        if seq[m] < t:
            min = m + 1
        elif seq[m] > t:
            max = m - 1
        else:
            return m

import time

def search_compare(a,n):
    print 'Binary search for %d items in %d length list of integers:'%(n,m)
    t1 = time.time()
    for i in range(n):
        py_int_search(a,i)
    t2 = time.time()
    py = (t2-t1)
    print ' speed in python:', (t2 - t1)

    # bisect
    t1 = time.time()
    for i in range(n):
        bisect(a,i)
    t2 = time.time()
    bi = (t2-t1) +1e-20 # protect against div by zero
    print ' speed of bisect:', bi
    print ' speed up: %3.2f' % (py/bi)

    # get it in cache
    c_int_search(a,i)
    t1 = time.time()
    for i in range(n):
        c_int_search(a,i,chk=1)
    t2 = time.time()
    sp = (t2-t1)+1e-20 # protect against div by zero
    print ' speed in c:',sp
    print ' speed up: %3.2f' % (py/sp)

    # get it in cache
    c_int_search(a,i)
    t1 = time.time()
    for i in range(n):
        c_int_search(a,i,chk=0)
    t2 = time.time()
    sp = (t2-t1)+1e-20 # protect against div by zero
    print ' speed in c(no asserts):',sp    
    print ' speed up: %3.2f' % (py/sp)

    # get it in cache
    c_int_search_scxx(a,i)
    t1 = time.time()
    for i in range(n):
        c_int_search_scxx(a,i,chk=1)
    t2 = time.time()
    sp = (t2-t1)+1e-20 # protect against div by zero
    print ' speed for scxx:',sp
    print ' speed up: %3.2f' % (py/sp)

    # get it in cache
    c_int_search_scxx(a,i)
    t1 = time.time()
    for i in range(n):
        c_int_search_scxx(a,i,chk=0)
    t2 = time.time()
    sp = (t2-t1)+1e-20 # protect against div by zero
    print ' speed for scxx(no asserts):',sp    
    print ' speed up: %3.2f' % (py/sp)

    # get it in cache
    a = array(a)
    try:
        a = array(a)
        c_array_int_search(a,i)
        t1 = time.time()
        for i in range(n):
            c_array_int_search(a,i)
        t2 = time.time()
        sp = (t2-t1)+1e-20 # protect against div by zero
        print ' speed in c(Numeric arrays):',sp    
        print ' speed up: %3.2f' % (py/sp)
    except:
        pass
        
if __name__ == "__main__":
    # note bisect returns index+1 compared to other algorithms
    m= 100000
    a = range(m)
    n = 50000
    search_compare(a,n)    
    print 'search(a,3450)', c_int_search(a,3450), py_int_search(a,3450), bisect(a,3450)
    print 'search(a,-1)', c_int_search(a,-1), py_int_search(a,-1), bisect(a,-1)
    print 'search(a,10001)', c_int_search(a,10001), py_int_search(a,10001),bisect(a,10001)
""" Comparison of several different ways of calculating a "ramp"
    function.
    
    C:\home\ej\wrk\junk\scipy\weave\examples>python ramp.py 
    python (seconds*ratio): 128.149998188
    arr[500]: 0.0500050005001
    compiled numeric1 (seconds, speed up): 1.42199993134 90.1195530071
    arr[500]: 0.0500050005001
    compiled numeric2 (seconds, speed up): 0.950999975204 134.752893301
    arr[500]: 0.0500050005001
    compiled list1 (seconds, speed up): 53.100001812 2.41337088164
    arr[500]: 0.0500050005001
    compiled list4 (seconds, speed up): 30.5500030518 4.19476220578
    arr[500]: 0.0500050005001     

"""

import time
import weave
from Numeric import *

def Ramp(result, size, start, end):
    step = (end-start)/(size-1)
    for i in xrange(size):
        result[i] = start + step*i

def Ramp_numeric1(result,start,end):
    code = """
           const int size = Nresult[0];
           const double step = (end-start)/(size-1);
           double val = start;
           for (int i = 0; i < size; i++)
               *result++ = start + step*i;
           """
    weave.inline(code,['result','start','end'],compiler='gcc')

def Ramp_numeric2(result,start,end):
    code = """
           const int size = Nresult[0];
           double step = (end-start)/(size-1);
           double val = start;
           for (int i = 0; i < size; i++)
           {
              result[i] = val;
              val += step; 
           }
           """
    weave.inline(code,['result','start','end'],compiler='gcc')

def Ramp_list1(result, start, end):
    code = """
           const int size = result.len();
           const double step = (end-start)/(size-1);
           for (int i = 0; i < size; i++) 
               result[i] = start + step*i;
           """
    weave.inline(code, ["result","start", "end"], verbose=2)

def Ramp_list2(result, start, end):
    code = """
           const int size = result.len();
           const double step = (end-start)/(size-1);
           for (int i = 0; i < size; i++) 
           {
               PyObject* val = PyFloat_FromDouble( start + step*i );
               PySequence_SetItem(py_result,i, val);
           }
           """
    weave.inline(code, ["result", "start", "end"], verbose=2)
          
def main():
    N_array = 10000
    N_py = 200
    N_c = 10000
    
    ratio = float(N_c) / N_py    
    
    arr = [0]*N_array
    t1 = time.time()
    for i in xrange(N_py):
        Ramp(arr, N_array, 0.0, 1.0)
    t2 = time.time()
    py_time = (t2 - t1) * ratio
    print 'python (seconds*ratio):', py_time
    print 'arr[500]:', arr[500]
    
    arr1 = array([0]*N_array,Float64)
    # First call compiles function or loads from cache.
    # I'm not including this in the timing.
    Ramp_numeric1(arr1, 0.0, 1.0)
    t1 = time.time()
    for i in xrange(N_c):
        Ramp_numeric1(arr1, 0.0, 1.0)
    t2 = time.time()
    c_time = (t2 - t1)
    print 'compiled numeric1 (seconds, speed up):', c_time, py_time/ c_time
    print 'arr[500]:', arr1[500]

    arr2 = array([0]*N_array,Float64)
    # First call compiles function or loads from cache.
    # I'm not including this in the timing.
    Ramp_numeric2(arr2, 0.0, 1.0)
    t1 = time.time()
    for i in xrange(N_c):
        Ramp_numeric2(arr2, 0.0, 1.0)
    t2 = time.time()
    c_time = (t2 - t1)   
    print 'compiled numeric2 (seconds, speed up):', c_time, py_time/ c_time
    print 'arr[500]:', arr2[500]

    arr3 = [0]*N_array
    # First call compiles function or loads from cache.
    # I'm not including this in the timing.
    Ramp_list1(arr3, 0.0, 1.0)
    t1 = time.time()
    for i in xrange(N_py):
        Ramp_list1(arr3, 0.0, 1.0)
    t2 = time.time()
    c_time = (t2 - t1) * ratio  
    print 'compiled list1 (seconds, speed up):', c_time, py_time/ c_time
    print 'arr[500]:', arr3[500]
    
    arr4 = [0]*N_array
    # First call compiles function or loads from cache.
    # I'm not including this in the timing.
    Ramp_list2(arr4, 0.0, 1.0)
    t1 = time.time()
    for i in xrange(N_py):
        Ramp_list2(arr4, 0.0, 1.0)
    t2 = time.time()
    c_time = (t2 - t1) * ratio  
    print 'compiled list4 (seconds, speed up):', c_time, py_time/ c_time
    print 'arr[500]:', arr4[500]
    
    
if __name__ == '__main__':
    main()
# Borrowed from Alex Martelli's sort from Python cookbook using inlines
# 2x over fastest Python version -- again, maybe not worth the effort...
# Then again, 2x is 2x...
#
#    C:\home\eric\wrk\scipy\weave\examples>python dict_sort.py
#    Dict sort of 1000 items for 300 iterations:
#     speed in python: 0.250999927521
#    [0, 1, 2, 3, 4]
#     speed in c: 0.110000014305
#     speed up: 2.28
#    [0, 1, 2, 3, 4]
#     speed in c (scxx): 0.200000047684
#     speed up: 1.25
#    [0, 1, 2, 3, 4] 

import sys
sys.path.insert(0,'..')
import inline_tools

def c_sort(adict):
    assert(type(adict) is dict)
    code = """
           #line 24 "dict_sort.py" 
           py::list keys = adict.keys();
           py::list items(keys.length());
           keys.sort(); 
           PyObject* item = NULL;
           int N = keys.length();
           for(int i = 0; i < N;i++)
           {
              item = PyList_GetItem(keys,i);
              item = PyDict_GetItem(adict,item);
              Py_XINCREF(item);
              PyList_SetItem(items,i,item);              
           }           
           return_val = items;
           """   
    return inline_tools.inline(code,['adict'])

def c_sort2(adict):
    assert(type(adict) is dict)
    code = """
           #line 44 "dict_sort.py"     
           py::list keys = adict.keys();
           py::list items(keys.len());
           keys.sort(); 
           int N = keys.length();
           for(int i = 0; i < N;i++)
              items[i] = adict[keys[i]];
           return_val = items;
           """   
    return inline_tools.inline(code,['adict'],verbose=1)

# (IMHO) the simplest approach:
def sortedDictValues1(adict):
    items = adict.items()
    items.sort()
    return [value for key, value in items]

# an alternative implementation, which
# happens to run a bit faster for large
# dictionaries on my machine:
def sortedDictValues2(adict):
    keys = adict.keys()
    keys.sort()
    return [adict[key] for key in keys]

# a further slight speed-up on my box
# is to map a bound-method:
def sortedDictValues3(adict):
    keys = adict.keys()
    keys.sort()
    return map(adict.get, keys)

import time

def sort_compare(a,n):
    print 'Dict sort of %d items for %d iterations:'%(len(a),n)
    t1 = time.time()
    for i in range(n):
        b=sortedDictValues3(a)
    t2 = time.time()
    py = (t2-t1)
    print ' speed in python:', (t2 - t1)
    print b[:5]
    
    b=c_sort(a)
    t1 = time.time()
    for i in range(n):
        b=c_sort(a)
    t2 = time.time()
    print ' speed in c (Python API):',(t2 - t1)    
    print ' speed up: %3.2f' % (py/(t2-t1))
    print b[:5]

    b=c_sort2(a)
    t1 = time.time()
    for i in range(n):
        b=c_sort2(a)
    t2 = time.time()
    print ' speed in c (scxx):',(t2 - t1)    
    print ' speed up: %3.2f' % (py/(t2-t1))
    print b[:5]

def setup_dict(m):
    " does insertion order matter?"
    import whrandom
    a = range(m)
    d = {}
    for i in range(m):
        key = whrandom.choice(a)
        a.remove(key)
        d[key]=key
    return d    
if __name__ == "__main__":
    m = 1000
    a = setup_dict(m)
    n = 3000
    sort_compare(a,n)    

# h:\wrk\scipy\weave\examples>python object.py
# initial val: 1
# inc result: 2
# after set attr: 5

import weave

#----------------------------------------------------------------------------
# get/set attribute and call methods example
#----------------------------------------------------------------------------

class foo:
    def __init__(self):
        self.val = 1
    def inc(self,amount):
        self.val += 1
        return self.val
obj = foo()
code = """
       int i = obj.attr("val");
       std::cout << "initial val: " << i << std::endl;
       
       py::tuple args(1);
       args[0] = 2; 
       i = obj.mcall("inc",args);
       std::cout << "inc result: " << i << std::endl;
       
       obj.set_attr("val",5);
       i = obj.attr("val");
       std::cout << "after set attr: " << i << std::endl;
       """
weave.inline(code,['obj'])       
       
#----------------------------------------------------------------------------
# indexing of values.
#----------------------------------------------------------------------------
from UserList import UserList
obj = UserList([1,[1,2],"hello"])
code = """
       int i;
       // find obj length and accesss each of its items
       std::cout << "UserList items: ";
       for(i = 0; i < obj.length(); i++)
           std::cout << obj[i] << " ";
       std::cout << std::endl;
       // assign new values to each of its items
       for(i = 0; i < obj.length(); i++)
           obj[i] = "goodbye";
       """
weave.inline(code,['obj'])       
print "obj with new values:", obj
import sys
sys.path.insert(0,'..')
import inline_tools

def multi_return():
    return 1, '2nd'

def c_multi_return():

    code =  """
 	        py::tuple results(2);
 	        results[0] = 1;
 	        results[1] = "2nd";
 	        return_val = results; 	        
            """
    return inline_tools.inline(code,[])


def compare(m):
    import time
    t1 = time.time()
    for i in range(m):
        py_result = multi_return()
    t2 = time.time()
    py = t2 - t1
    print 'python speed:', py
    
    #load cache
    result = c_multi_return()
    t1 = time.time()
    for i in range(m):
        c_result = c_multi_return()
    t2 = time.time()
    c = t2-t1
    print 'c speed:', c
    print 'speed up:', py / c
    print 'or slow down (more likely:', c / py
    print 'python result:', py_result
    print 'c result:', c_result
    
if __name__ == "__main__":
    compare(10000)
""" 
"""
# C:\home\ej\wrk\scipy\weave\examples>python vq.py
# vq with 1000 observation, 10 features and 30 codes fo 100 iterations
#  speed in python: 0.150119999647
# [25 29] [ 2.49147266  3.83021032]
#  speed in standard c: 0.00710999965668
# [25 29] [ 2.49147266  3.83021032]
#  speed up: 21.11
#  speed inline/blitz: 0.0186300003529
# [25 29] [ 2.49147272  3.83021021]
#  speed up: 8.06
#  speed inline/blitz2: 0.00461000084877
# [25 29] [ 2.49147272  3.83021021]
#  speed up: 32.56
 
import Numeric
from Numeric import *
import sys
sys.path.insert(0,'..')
import inline_tools
import converters
blitz_type_converters = converters.blitz
import c_spec

def vq(obs,code_book):
    # make sure we're looking at arrays.
    obs = asarray(obs)
    code_book = asarray(code_book)
    # check for 2d arrays and compatible sizes.
    obs_sh = shape(obs)
    code_book_sh = shape(code_book)
    assert(len(obs_sh) == 2 and len(code_book_sh) == 2)   
    assert(obs_sh[1] == code_book_sh[1])   
    type = c_spec.num_to_c_types[obs.typecode()]
    # band aid for now.
    ar_type = 'PyArray_FLOAT'
    code =  """
            #line 37 "vq.py"
            // Use tensor notation.            
            blitz::Array<%(type)s,2> dist_sq(Ncode_book[0],Nobs[0]);
 	        blitz::firstIndex i;    
            blitz::secondIndex j;   
            blitz::thirdIndex k;
            dist_sq = sum(pow2(obs(j,k) - code_book(i,k)),k);
            // Surely there is a better way to do this...
            PyArrayObject* py_code = (PyArrayObject*) PyArray_FromDims(1,&Nobs[0],PyArray_LONG);
 	        blitz::Array<int,1> code((int*)(py_code->data),
                                     blitz::shape(Nobs[0]), blitz::neverDeleteData);
 	        code = minIndex(dist_sq(j,i),j);
 	        
 	        PyArrayObject* py_min_dist = (PyArrayObject*) PyArray_FromDims(1,&Nobs[0],PyArray_FLOAT);
 	        blitz::Array<float,1> min_dist((float*)(py_min_dist->data),
 	                                       blitz::shape(Nobs[0]), blitz::neverDeleteData);
 	        min_dist = sqrt(min(dist_sq(j,i),j));
 	        py::tuple results(2);
 	        results[0] = py_code;
 	        results[1] = py_min_dist;
 	        return_val = results; 	        
            """ % locals()
    code, distortion = inline_tools.inline(code,['obs','code_book'],
                                           type_converters = blitz_type_converters,
                                           compiler = 'gcc',
                                           verbose = 1)
    return code, distortion

def vq2(obs,code_book):
    """ doesn't use blitz (except in conversion)
        ALSO DOES NOT HANDLE STRIDED ARRAYS CORRECTLY
    """
    # make sure we're looking at arrays.
    obs = asarray(obs)
    code_book = asarray(code_book)
    # check for 2d arrays and compatible sizes.
    obs_sh = shape(obs)
    code_book_sh = shape(code_book)
    assert(len(obs_sh) == 2 and len(code_book_sh) == 2)   
    assert(obs_sh[1] == code_book_sh[1])   
    assert(obs.typecode() == code_book.typecode())   
    type = c_spec.num_to_c_types[obs.typecode()]
    # band aid for now.
    ar_type = 'PyArray_FLOAT'
    code =  """
            #line 83 "vq.py"
            // THIS DOES NOT HANDLE STRIDED ARRAYS CORRECTLY
            // Surely there is a better way to do this...
            PyArrayObject* py_code = (PyArrayObject*) PyArray_FromDims(1,&Nobs[0],PyArray_LONG);	        
 	        PyArrayObject* py_min_dist = (PyArrayObject*) PyArray_FromDims(1,&Nobs[0],PyArray_FLOAT);
 	        
            int* raw_code = (int*)(py_code->data);
            float* raw_min_dist = (float*)(py_min_dist->data);
            %(type)s* raw_obs = obs.data();
            %(type)s* raw_code_book = code_book.data(); 
            %(type)s* this_obs = NULL;
            %(type)s* this_code = NULL; 
            int Nfeatures = Nobs[1];
            float diff,dist;
            for(int i=0; i < Nobs[0]; i++)
            {
                this_obs = &raw_obs[i*Nfeatures];
                raw_min_dist[i] = (%(type)s)10000000.; // big number
                for(int j=0; j < Ncode_book[0]; j++)
                {
                    this_code = &raw_code_book[j*Nfeatures];
                    dist = 0;
                    for(int k=0; k < Nfeatures; k++)
                    {
                        diff = this_obs[k] - this_code[k];
                        dist +=  diff*diff;
                    }
                    dist = dist;
                    if (dist < raw_min_dist[i])
                    {
                        raw_code[i] = j;
                        raw_min_dist[i] = dist;                           
                    }    
                }
                raw_min_dist[i] = sqrt(raw_min_dist[i]);
 	        }
 	        py::tuple results(2);
 	        results[0] = py_code;
 	        results[1] = py_min_dist;
 	        return_val = results; 	        
            """ % locals()
    code, distortion = inline_tools.inline(code,['obs','code_book'],
                                         type_converters = blitz_type_converters,
                                         compiler = 'gcc',
                                         verbose = 1)
    return code, distortion


def vq3(obs,code_book):
    """ Uses standard array conversion completely bi-passing blitz.
        THIS DOES NOT HANDLE STRIDED ARRAYS CORRECTLY
    """
    # make sure we're looking at arrays.
    obs = asarray(obs)
    code_book = asarray(code_book)
    # check for 2d arrays and compatible sizes.
    obs_sh = shape(obs)
    code_book_sh = shape(code_book)
    assert(len(obs_sh) == 2 and len(code_book_sh) == 2)   
    assert(obs_sh[1] == code_book_sh[1])   
    assert(obs.typecode() == code_book.typecode())   
    type = c_spec.num_to_c_types[obs.typecode()]
    code =  """
            #line 139 "vq.py"
            // Surely there is a better way to do this...
            PyArrayObject* py_code = (PyArrayObject*) PyArray_FromDims(1,&Nobs[0],PyArray_LONG);	        
 	        PyArrayObject* py_min_dist = (PyArrayObject*) PyArray_FromDims(1,&Nobs[0],PyArray_FLOAT);
 	        
            int* code_data = (int*)(py_code->data);
            float* min_dist_data = (float*)(py_min_dist->data);
            %(type)s* this_obs = NULL;
            %(type)s* this_code = NULL; 
            int Nfeatures = Nobs[1];
            float diff,dist;

            for(int i=0; i < Nobs[0]; i++)
            {
                this_obs = &obs_data[i*Nfeatures];
                min_dist_data[i] = (float)10000000.; // big number
                for(int j=0; j < Ncode_book[0]; j++)
                {
                    this_code = &code_book_data[j*Nfeatures];
                    dist = 0;
                    for(int k=0; k < Nfeatures; k++)
                    {
                        diff = this_obs[k] - this_code[k];
                        dist +=  diff*diff;
                    }
                    if (dist < min_dist_data[i])
                    {
                        code_data[i] = j;
                        min_dist_data[i] = dist;                           
                    }    
                }
                min_dist_data[i] = sqrt(min_dist_data[i]);
 	        }
 	        py::tuple results(2);
 	        results[0] = py_code;
 	        results[1] = py_min_dist;
 	        return_val = results; 	        
            """ % locals()
    # this is an unpleasant way to specify type factories -- work on it.
    import ext_tools
    code, distortion = inline_tools.inline(code,['obs','code_book'])
    return code, distortion

import time
import RandomArray
def compare(m,Nobs,Ncodes,Nfeatures):
    obs = RandomArray.normal(0.,1.,(Nobs,Nfeatures))
    codes = RandomArray.normal(0.,1.,(Ncodes,Nfeatures))
    import scipy.cluster.vq
    scipy.cluster.vq
    print 'vq with %d observation, %d features and %d codes for %d iterations' % \
           (Nobs,Nfeatures,Ncodes,m)
    t1 = time.time()
    for i in range(m):
        code,dist = scipy.cluster.vq.py_vq(obs,codes)
    t2 = time.time()
    py = (t2-t1)
    print ' speed in python:', (t2 - t1)/m
    print code[:2],dist[:2]
    
    t1 = time.time()
    for i in range(m):
        code,dist = scipy.cluster.vq.vq(obs,codes)
    t2 = time.time()
    print ' speed in standard c:', (t2 - t1)/m
    print code[:2],dist[:2]
    print ' speed up: %3.2f' % (py/(t2-t1))
    
    # load into cache    
    b = vq(obs,codes)
    t1 = time.time()
    for i in range(m):
        code,dist = vq(obs,codes)
    t2 = time.time()
    print ' speed inline/blitz:',(t2 - t1)/ m    
    print code[:2],dist[:2]
    print ' speed up: %3.2f' % (py/(t2-t1))

    # load into cache    
    b = vq2(obs,codes)
    t1 = time.time()
    for i in range(m):
        code,dist = vq2(obs,codes)
    t2 = time.time()
    print ' speed inline/blitz2:',(t2 - t1)/ m    
    print code[:2],dist[:2]
    print ' speed up: %3.2f' % (py/(t2-t1))

    # load into cache    
    b = vq3(obs,codes)
    t1 = time.time()
    for i in range(m):
        code,dist = vq3(obs,codes)
    t2 = time.time()
    print ' speed using C arrays:',(t2 - t1)/ m    
    print code[:2],dist[:2]
    print ' speed up: %3.2f' % (py/(t2-t1))
    
if __name__ == "__main__":
    compare(100,1000,30,10)    
    #compare(1,10,2,10)    

"""
Storing actual strings instead of their md5 value appears to 
be about 10 times faster.

>>> md5_speed.run(200,50000)
md5 build(len,sec): 50000 0.870999932289
md5 retrv(len,sec): 50000 0.680999994278
std build(len,sec): 50000 0.259999990463
std retrv(len,sec): 50000 0.0599999427795

This test actually takes several minutes to generate the random
keys used to populate the dictionaries.  Here is a smaller run,
but with longer keys.

>>> md5_speed.run(1000,4000)
md5 build(len,sec,per): 4000 0.129999995232 3.24999988079e-005
md5 retrv(len,sec,per): 4000 0.129999995232 3.24999988079e-005
std build(len,sec,per): 4000 0.0500000715256 1.25000178814e-005
std retrv(len,sec,per): 4000 0.00999999046326 2.49999761581e-006

Results are similar, though not statistically to good because of
the short times used and the available clock resolution.

Still, I think it is safe to say that, for speed, it is better 
to store entire strings instead of using md5 versions of 
their strings.  Yeah, the expected result, but it never hurts
to check...

"""
import random, md5, time, cStringIO

def speed(n,m):
    s = 'a'*n
    t1 = time.time()            
    for i in range(m):
        q= md5.new(s).digest()
    t2 = time.time()
    print (t2 - t1) / m

#speed(50,1e6)

def generate_random(avg_length,count):
    all_str = []
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    lo,hi = [30,avg_length*2+30]
    for i in range(count):
        new_str = cStringIO.StringIO()
        l = random.randrange(lo,hi)
        for i in range(l):
            new_str.write(random.choice(alphabet))
        all_str.append(new_str.getvalue())
    return all_str    
    
def md5_dict(lst):
    catalog = {}
    t1 = time.time()
    for s in lst:
        key= md5.new(s).digest()
        catalog[key] = None
    t2 = time.time()    
    print 'md5 build(len,sec,per):', len(lst), t2 - t1, (t2-t1)/len(lst)
    
    t1 = time.time()
    for s in lst:
        key= md5.new(s).digest()
        val = catalog[key]
    t2 = time.time()    
    print 'md5 retrv(len,sec,per):', len(lst), t2 - t1, (t2-t1)/len(lst)

def std_dict(lst):
    catalog = {}
    t1 = time.time()
    for s in lst:
        catalog[s] = None
    t2 = time.time()    
    print 'std build(len,sec,per):', len(lst), t2 - t1, (t2-t1)/len(lst)
    
    t1 = time.time()
    for s in lst:
        val = catalog[s]
    t2 = time.time()    
    print 'std retrv(len,sec,per):', len(lst), t2 - t1, (t2-t1)/len(lst)

def run(m=200,n=10):
    lst = generate_random(m,n)
    md5_dict(lst)
    std_dict(lst)

run(2000,100)    
#       C:\home\eric\wrk\scipy\weave\examples>python functional.py
#       desired: [2, 3, 4]
#       actual: [2, 3, 4]
#       actual2: [2, 3, 4]
#       python speed: 0.039999961853
#       SCXX speed: 0.0599999427795
#       speed up: 0.666666666667
#       c speed: 0.0200001001358
#       speed up: 1.99998807913

import sys
sys.path.insert(0,'..')
import inline_tools
from types import *
def c_list_map(func,seq):
    """ Uses CXX C code to implement a simple map-like function.
        It does not provide any error checking.
    """
    assert(type(func) in [FunctionType,MethodType,type(len)])
    code = """
           #line 22 "functional.py"
           py::tuple args(1);
           int N = seq.len();    
           py::list result(N);
           for(int i = 0; i < N;i++)
           {
              args[0] = seq[i];
              result[i] = func.call(args);
           }           
           return_val = result;
           """   
    return inline_tools.inline(code,['func','seq'])

def c_list_map2(func,seq):
    """ Uses Python API more than CXX to implement a simple map-like function.
        It does not provide any error checking.
    """
    assert(type(func) in [FunctionType,MethodType,type(len)])
    code = """
           #line 40 "functional.py"
           py::tuple args(1);    
           PyObject* py_args = (PyObject*)args;
           py::list result(seq.len());
           PyObject* py_result = (PyObject*)result;
           PyObject* item = NULL;
           PyObject* this_result = NULL;
           int N = seq.len();
           for(int i = 0; i < N;i++)
           {
              item = PyList_GET_ITEM(py_seq,i);
              Py_INCREF(item);
              PyTuple_SetItem(py_args,0,item);
              this_result = PyEval_CallObject(py_func,py_args);
              PyList_SetItem(py_result,i,this_result);              
           }           
           return_val = result;
           """   
    return inline_tools.inline(code,['func','seq'])
    
def main():
    seq = ['aa','bbb','cccc']
    print 'desired:', map(len,seq)
    print 'actual:', c_list_map(len,seq)
    print 'actual2:', c_list_map2(len,seq)

def time_it(m,n):
    import time
    seq = ['aadasdf'] * n
    t1 = time.time()
    for i in range(m):
        result = map(len,seq)
    t2 = time.time()
    py = t2 - t1
    print 'python speed:', py
    
    #load cache
    result = c_list_map(len,seq)
    t1 = time.time()
    for i in range(m):
        result = c_list_map(len,seq)
    t2 = time.time()
    c = t2-t1
    print 'SCXX speed:', c
    print 'speed up:', py / c

    #load cache
    result = c_list_map2(len,seq)
    t1 = time.time()
    for i in range(m):
        result = c_list_map2(len,seq)
    t2 = time.time()
    c = t2-t1
    print 'c speed:', c
    print 'speed up:', py / c

if __name__ == "__main__":
    main()
    time_it(100,1000)
#
#        C:\home\eric\wrk\scipy\weave\examples>python ramp2.py
#        python (seconds): 2.94499993324
#        arr[500]: 0.0500050005001
#        
#        compiled numeric (seconds, speed up): 3.47500002384 42.3740994682
#        arr[500]: 0.0500050005001

import time
from weave import ext_tools
from Numeric import *

def Ramp(result, size, start, end):
    step = (end-start)/(size-1)
    for i in xrange(size):
        result[i] = start + step*i

def build_ramp_ext():
    mod = ext_tools.ext_module('ramp_ext')
    
    # type declarations
    result = array([0],Float64)
    start,end = 0.,0.
    code = """
           const int size = Nresult[0];
           const double step = (end-start)/(size-1);
           double val = start;
           for (int i = 0; i < size; i++)
           {
              result[i] = val;
              val += step; 
           }
           """
    func = ext_tools.ext_function('Ramp',code,['result','start','end'])
    mod.add_function(func)
    mod.compile(compiler='gcc')
         
def main():    
    arr = [0]*10000
    t1 = time.time()
    for i in xrange(200):
        Ramp(arr, 10000, 0.0, 1.0)
    t2 = time.time()
    py_time = t2 - t1
    print 'python (seconds):', py_time
    print 'arr[500]:', arr[500]
    print
    
    try:
        import ramp_ext
    except:
        build_ramp_ext()
        import ramp_ext
    arr = array([0]*10000,Float64)
    for i in xrange(10000):
        ramp_ext.Ramp(arr, 0.0, 1.0)
    t2 = time.time()
    c_time = (t2 - t1)    
    print 'compiled numeric (seconds, speed up):', c_time, (py_time*10000/200.)/ c_time
    print 'arr[500]:', arr[500]
    
if __name__ == '__main__':
    main()
# This tests the amount of overhead added for inline() function calls.
# It isn't a "real world" test, but is somewhat informative.
# C:\home\ej\wrk\scipy\weave\examples>python py_none.py
# python: 0.0199999809265
# inline: 0.160000085831
# speed up: 0.124999813736 (this is about a factor of 8 slower)

import time
import sys
sys.path.insert(0,'..')
from inline_tools import inline

def py_func():
    return None

n = 10000
t1 = time.time()    
for i in range(n):
    py_func()
t2 = time.time()
py_time = t2 - t1
print 'python:', py_time    

inline("",[])
t1 = time.time()    
for i in range(n):
    inline("",[])
t2 = time.time()
print 'inline:', (t2-t1)    
print 'speed up:', py_time/(t2-t1)    
print 'or (more likely) slow down:', (t2-t1)/py_time
""" Implements a fast replacement for calling DrawLines with an array as an
    argument.  It uses weave, so you'll need that installed.

    Copyright:   Space Telescope Science Institute
    License:     BSD Style
    Designed by: Enthought, Inc.
    Author:      Eric Jones eric@enthought.com

    I wrote this because I was seeing very bad performance for DrawLines when
    called with a large number of points -- 5000-30000. Now, I have found the
    performance is sometimes OK, and sometimes very poor.  Drawing to a
    MemoryDC seems to be worse than drawing to the screen.  My first cut of the
    routine just called PolyLine directly, but I got lousy performance for this
    also.  After noticing the slowdown as the array length grew was much worse
    than linear, I tried the following "chunking" algorithm.  It is much more
    efficient (sometimes by 2 orders of magnitude, but usually only a factor
    of 3).  There is a slight drawback in that it will draw end caps for each
    chunk of the array which is not strictly correct.  I don't imagine this is
    a major issue, but remains an open issue.

"""
import weave
from RandomArray import *
from Numeric import *
from wxPython.wx import *

"""
const int n_pts = _Nline[0];
const int bunch_size = 100;
const int bunches = n_pts / bunch_size;
const int left_over = n_pts % bunch_size;

for (int i = 0; i < bunches; i++)
{
    Polyline(hdc,(POINT*)p_data,bunch_size);
    p_data += bunch_size*2; //*2 for two longs per point
}
Polyline(hdc,(POINT*)p_data,left_over);
"""

def polyline(dc,line,xoffset=0,yoffset=0):
    #------------------------------------------------------------------------
    # Make sure the array is the correct size/shape 
    #------------------------------------------------------------------------
    shp = line.shape
    assert(len(shp)==2 and shp[1] == 2)

    #------------------------------------------------------------------------
    # Offset data if necessary
    #------------------------------------------------------------------------
    if xoffset or yoffset:
        line = line + array((xoffset,yoffset),line.typecode())
    
    #------------------------------------------------------------------------
    # Define the win32 version of the function
    #------------------------------------------------------------------------        
    if sys.platform == 'win32':
        # win32 requires int type for lines.
        if (line.typecode() != Int or not line.iscontiguous()):
            line = line.astype(Int)   
        code = """
               HDC hdc = (HDC) dc->GetHDC();                    
               Polyline(hdc,(POINT*)line,Nline[0]);
               """
    else:
        if (line.typecode() != UInt16 or 
            not line.iscontiguous()):
            line = line.astype(UInt16)   
        code = """
               GdkWindow* win = dc->m_window;                    
               GdkGC* pen = dc->m_penGC;
               gdk_draw_lines(win,pen,(GdkPoint*)line,Nline[0]);         
               """
    weave.inline(code,['dc','line'])

    
    #------------------------------------------------------------------------
    # Find the maximum and minimum points in the drawing list and add
    # them to the bounding box.    
    #------------------------------------------------------------------------
    max_pt = maximum.reduce(line,0)
    min_pt = minimum.reduce(line,0)
    dc.CalcBoundingBox(max_pt[0],max_pt[1])
    dc.CalcBoundingBox(min_pt[0],min_pt[1])    

#-----------------------------------------------------------------------------
# Define a new version of DrawLines that calls the optimized
# version for Numeric arrays when appropriate.
#-----------------------------------------------------------------------------
def NewDrawLines(dc,line):
    """
    """
    if (type(line) is ArrayType):
        polyline(dc,line)
    else:
        dc.DrawLines(line)            

#-----------------------------------------------------------------------------
# And attach our new method to the wxPaintDC class
# !! We have disabled it and called polyline directly in this example
# !! to get timing comparison between the old and new way.
#-----------------------------------------------------------------------------
#wxPaintDC.DrawLines = NewDrawLines
        
if __name__ == '__main__':
    from wxPython.wx import *
    import time

    class Canvas(wxWindow):
        def __init__(self, parent, id = -1, size = wxDefaultSize):
            wxWindow.__init__(self, parent, id, wxPoint(0, 0), size,
                              wxSUNKEN_BORDER | wxWANTS_CHARS)
            self.calc_points()
            EVT_PAINT(self, self.OnPaint)
            EVT_SIZE(self, self.OnSize)

        def calc_points(self):
            w,h = self.GetSizeTuple()            
            #x = randint(0+50, w-50, self.point_count)
            #y = randint(0+50, h-50, len(x))
            x = arange(0,w,typecode=Int32)
            y = h/2.*sin(x*2*pi/w)+h/2.
            y = y.astype(Int32)
            self.points = concatenate((x[:,NewAxis],y[:,NewAxis]),-1)

        def OnSize(self,event):
            self.calc_points()
            self.Refresh()

        def OnPaint(self,event):
            w,h = self.GetSizeTuple()            
            print len(self.points)
            dc = wxPaintDC(self)
            dc.BeginDrawing()

            # This first call is slow because your either compiling (very slow)
            # or loading a DLL (kinda slow)
            # Resize the window to get a more realistic timing.
            pt_copy = self.points.copy()
            t1 = time.clock()
            offset = array((1,0))
            mod = array((w,0))
            x = pt_copy[:,0];
            ang = 2*pi/w;
            
            size = 1
            red_pen = wxPen('red',size)            
            white_pen = wxPen('white',size)
            blue_pen = wxPen('blue',size)
            pens = iter([red_pen,white_pen,blue_pen])
            phase = 10
            for i in range(1500):
                if phase > 2*pi:
                    phase = 0                
                    try:
                        pen = pens.next()
                    except:
                        pens = iter([red_pen,white_pen,blue_pen])
                        pen = pens.next()
                    dc.SetPen(pen)
                polyline(dc,pt_copy)            
                next_y = (h/2.*sin(x*ang-phase)+h/2.).astype(Int32)            
                pt_copy[:,1] = next_y
                phase += ang
            t2 = time.clock()
            print 'Weave Polyline:', t2-t1

            t1 = time.clock()
            pt_copy = self.points.copy()
            pens = iter([red_pen,white_pen,blue_pen])
            phase = 10
            for i in range(1500):
                if phase > 2*pi:
                    phase = 0                
                    try:
                        pen = pens.next()
                    except:
                        pens = iter([red_pen,white_pen,blue_pen])
                        pen = pens.next()
                    dc.SetPen(pen)
                dc.DrawLines(pt_copy)
                next_y = (h/2.*sin(x*ang-phase)+h/2.).astype(Int32)            
                pt_copy[:,1] = next_y
                phase += ang
            t2 = time.clock()
            dc.SetPen(red_pen)
            print 'wxPython DrawLines:', t2-t1

            dc.EndDrawing()

    class CanvasWindow(wxFrame):
        def __init__(self, id=-1, title='Canvas',size=(500,500)):
            parent = NULL
            wxFrame.__init__(self, parent,id,title, size=size)
            self.canvas = Canvas(self)
            self.Show(1)

    class MyApp(wxApp):
        def OnInit(self):
            frame = CanvasWindow(title="Speed Examples",size=(500,500))
            frame.Show(true)
            return true

    app = MyApp(0)
    app.MainLoop()
    
""" This is taken from the scrolled window example from the demo.

    Take a look at the DoDrawing2() method below.  The first 6 lines
    or so have been translated into C++.
    
"""


import sys
sys.path.insert(0,'..')
import inline_tools

from wxPython.wx import *

class MyCanvas(wxScrolledWindow):
    def __init__(self, parent, id = -1, size = wxDefaultSize):
        wxScrolledWindow.__init__(self, parent, id, wxPoint(0, 0), size, wxSUNKEN_BORDER)

        self.lines = []
        self.maxWidth  = 1000
        self.maxHeight = 1000

        self.SetBackgroundColour(wxNamedColor("WHITE"))
        EVT_LEFT_DOWN(self, self.OnLeftButtonEvent)
        EVT_LEFT_UP(self,   self.OnLeftButtonEvent)
        EVT_MOTION(self,    self.OnLeftButtonEvent)

        EVT_PAINT(self, self.OnPaint)


        self.SetCursor(wxStockCursor(wxCURSOR_PENCIL))
        #bmp = images.getTest2Bitmap()
        #mask = wxMaskColour(bmp, wxBLUE)
        #bmp.SetMask(mask)
        #self.bmp = bmp

        self.SetScrollbars(20, 20, self.maxWidth/20, self.maxHeight/20)

    def getWidth(self):
        return self.maxWidth

    def getHeight(self):
        return self.maxHeight


    def OnPaint(self, event):
        dc = wxPaintDC(self)
        self.PrepareDC(dc)
        self.DoDrawing2(dc)


    def DoDrawing(self, dc):
        dc.BeginDrawing()
        dc.SetPen(wxPen(wxNamedColour('RED')))
        dc.DrawRectangle(5, 5, 50, 50)

        dc.SetBrush(wxLIGHT_GREY_BRUSH)#
        dc.SetPen(wxPen(wxNamedColour('BLUE'), 4))
        dc.DrawRectangle(15, 15, 50, 50)

        dc.SetFont(wxFont(14, wxSWISS, wxNORMAL, wxNORMAL))
        dc.SetTextForeground(wxColour(0xFF, 0x20, 0xFF))
        te = dc.GetTextExtent("Hello World")
        dc.DrawText("Hello World", 60, 65)

        dc.SetPen(wxPen(wxNamedColour('VIOLET'), 4))
        dc.DrawLine(5, 65+te[1], 60+te[0], 65+te[1])

        lst = [(100,110), (150,110), (150,160), (100,160)]
        dc.DrawLines(lst, -60)
        dc.SetPen(wxGREY_PEN)
        dc.DrawPolygon(lst, 75)
        dc.SetPen(wxGREEN_PEN)
        dc.DrawSpline(lst+[(100,100)])

        #dc.DrawBitmap(self.bmp, 200, 20, true)
        #dc.SetTextForeground(wxColour(0, 0xFF, 0x80))
        #dc.DrawText("a bitmap", 200, 85)

        font = wxFont(20, wxSWISS, wxNORMAL, wxNORMAL)
        dc.SetFont(font)
        dc.SetTextForeground(wxBLACK)
        for a in range(0, 360, 45):
            dc.DrawRotatedText("Rotated text...", 300, 300, a)

        dc.SetPen(wxTRANSPARENT_PEN)
        dc.SetBrush(wxBLUE_BRUSH)
        dc.DrawRectangle(50,500,50,50)
        dc.DrawRectangle(100,500,50,50)

        dc.SetPen(wxPen(wxNamedColour('RED')))
        dc.DrawEllipticArc(200, 500, 50, 75, 0, 90)

        self.DrawSavedLines(dc)
        dc.EndDrawing()

    def DoDrawing2(self, dc):
        
        red = wxNamedColour("RED");
        blue = wxNamedColour("BLUE");
        grey_brush = wxLIGHT_GREY_BRUSH;
        code = \
        """
        //#line 108 "wx_example.py"
        dc->BeginDrawing();
        dc->SetPen(wxPen(*red,4,wxSOLID));
        dc->DrawRectangle(5, 5, 50, 50);

        dc->SetBrush(*grey_brush);
        dc->SetPen(wxPen(*blue, 4,wxSOLID));
        dc->DrawRectangle(15, 15, 50, 50);
        """
        inline_tools.inline(code,['dc','red','blue','grey_brush'],verbose=2)
        
        dc.SetFont(wxFont(14, wxSWISS, wxNORMAL, wxNORMAL))
        dc.SetTextForeground(wxColour(0xFF, 0x20, 0xFF))
        te = dc.GetTextExtent("Hello World")
        dc.DrawText("Hello World", 60, 65)

        dc.SetPen(wxPen(wxNamedColour('VIOLET'), 4))
        dc.DrawLine(5, 65+te[1], 60+te[0], 65+te[1])

        lst = [(100,110), (150,110), (150,160), (100,160)]
        dc.DrawLines(lst, -60)
        dc.SetPen(wxGREY_PEN)
        dc.DrawPolygon(lst, 75)
        dc.SetPen(wxGREEN_PEN)
        dc.DrawSpline(lst+[(100,100)])

        #dc.DrawBitmap(self.bmp, 200, 20, true)
        #dc.SetTextForeground(wxColour(0, 0xFF, 0x80))
        #dc.DrawText("a bitmap", 200, 85)

        font = wxFont(20, wxSWISS, wxNORMAL, wxNORMAL)
        dc.SetFont(font)
        dc.SetTextForeground(wxBLACK)
        for a in range(0, 360, 45):
            dc.DrawRotatedText("Rotated text...", 300, 300, a)

        dc.SetPen(wxTRANSPARENT_PEN)
        dc.SetBrush(wxBLUE_BRUSH)
        dc.DrawRectangle(50,500,50,50)
        dc.DrawRectangle(100,500,50,50)

        dc.SetPen(wxPen(wxNamedColour('RED')))
        dc.DrawEllipticArc(200, 500, 50, 75, 0, 90)

        self.DrawSavedLines(dc)
        dc.EndDrawing()


    def DrawSavedLines(self, dc):
        dc.SetPen(wxPen(wxNamedColour('MEDIUM FOREST GREEN'), 4))
        for line in self.lines:
            for coords in line:
                apply(dc.DrawLine, coords)


    def SetXY(self, event):
        self.x, self.y = self.ConvertEventCoords(event)

    def ConvertEventCoords(self, event):
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        return (event.GetX() + (xView * xDelta),
                event.GetY() + (yView * yDelta))

    def OnLeftButtonEvent(self, event):
        if event.LeftDown():
            self.SetXY(event)
            self.curLine = []
            self.CaptureMouse()

        elif event.Dragging():
            dc = wxClientDC(self)
            self.PrepareDC(dc)
            dc.BeginDrawing()
            dc.SetPen(wxPen(wxNamedColour('MEDIUM FOREST GREEN'), 4))
            coords = (self.x, self.y) + self.ConvertEventCoords(event)
            self.curLine.append(coords)
            apply(dc.DrawLine, coords)
            self.SetXY(event)
            dc.EndDrawing()

        elif event.LeftUp():
            self.lines.append(self.curLine)
            self.curLine = []
            self.ReleaseMouse()

#---------------------------------------------------------------------------
# This example isn't currently used.

class py_canvas(wx.wxWindow):   
    def __init__(self, parent, id = -1, pos=wx.wxPyDefaultPosition,
                 size=wx.wxPyDefaultSize, **attr):
        wx.wxWindow.__init__(self, parent, id, pos,size)
        #wx.EVT_PAINT(self,self.on_paint)
        background = wx.wxNamedColour('white')
        
        code = """
               self->SetBackgroundColour(*background);
               """
        inline_tools.inline(code,['self','background'],compiler='msvc')               
#----------------------------------------------------------------------------

class MyFrame(wxFrame):
    def __init__(self, parent, ID, title, pos=wxDefaultPosition,
                 size=wxDefaultSize, style=wxDEFAULT_FRAME_STYLE):
        wxFrame.__init__(self, parent, ID, title, pos, size, style)
        #panel = wxPanel(self, -1)
        self.GetSize()
        #button = wxButton(panel, 1003, "Close Me")
        #button.SetPosition(wxPoint(15, 15))
        #EVT_BUTTON(self, 1003, self.OnCloseMe)
        #EVT_CLOSE(self, self.OnCloseWindow)
        #canvas = py_canvas(self,-1)
        canvas = MyCanvas(self,-1)
        canvas.Show(true)
        
class MyApp(wxApp):
    def OnInit(self):
        win = MyFrame(NULL, -1, "This is a wxFrame", size=(350, 200),
                      style = wxDEFAULT_FRAME_STYLE)# |  wxFRAME_TOOL_WINDOW )
        win.Show(true)
        return true
    
if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()

import sys
sys.path.insert(0,'..')
import inline_tools


support_code = """
               PyObject* length(std::string a)
               {
                   int l = a.length();
                   return PyInt_FromLong(l);
               }
               """
a='some string'
val = inline_tools.inline("return_val = length(a);",['a'],
                          support_code=support_code)
print val

               
# examples/increment_example.py

#from weave import ext_tools

# use the following so that development version is used.
import sys
sys.path.insert(0,'..')
import ext_tools

def build_increment_ext():
    """ Build a simple extension with functions that increment numbers.
        The extension will be built in the local directory.
    """        
    mod = ext_tools.ext_module('increment_ext')

    a = 1 # effectively a type declaration for 'a' in the 
          # following functions.

    ext_code = "return_val = PyInt_FromLong(a+1);"    
    func = ext_tools.ext_function('increment',ext_code,['a'])
    mod.add_function(func)
    
    ext_code = "return_val = PyInt_FromLong(a+2);"    
    func = ext_tools.ext_function('increment_by_2',ext_code,['a'])
    mod.add_function(func)
            
    mod.compile()

if __name__ == "__main__":
    try:
        import increment_ext
    except ImportError:
        build_increment_ext()
        import increment_ext
    a = 1
    print 'a, a+1:', a, increment_ext.increment(a)
    print 'a, a+2:', a, increment_ext.increment_by_2(a)    

# Typical run:
# C:\home\eric\wrk\scipy\weave\examples>python fibonacci.py
# Recursively computing the first 30 fibonacci numbers:
#  speed in python: 4.31599998474
#  speed in c: 0.0499999523163
#  speed up: 86.32
# Looping to compute the first 30 fibonacci numbers:
#  speed in python: 0.000520999908447
#  speed in c: 5.00000715256e-005
#  speed up: 10.42
# fib(30) 832040 832040 832040 832040

import sys
sys.path.insert(0,'..')
import ext_tools

def build_fibonacci():
    """ Builds an extension module with fibonacci calculators.
    """
    mod = ext_tools.ext_module('fibonacci_ext')
    a = 1 # this is effectively a type declaration
    
    # recursive fibonacci in C 
    fib_code = """
                   int fib1(int a)
                   {                   
                       if(a <= 2)
                           return 1;
                       else
                           return fib1(a-2) + fib1(a-1);  
                   }                         
               """
    ext_code = """
                   return_val = fib1(a);
               """    
    fib = ext_tools.ext_function('c_fib1',ext_code,['a'])
    fib.customize.add_support_code(fib_code)
    mod.add_function(fib)

    # looping fibonacci in C
    fib_code = """
                    int fib2( int a )
                    {
                        int last, next_to_last, result;
            
                        if( a <= 2 )
                            return 1;            
                        last = next_to_last = 1;
                        for(int i = 2; i < a; i++ )
                        {
                            result = last + next_to_last;
                            next_to_last = last;
                            last = result;
                        }
            
                        return result;
                    }    
               """
    ext_code = """
                   return_val = fib2(a);
               """    
    fib = ext_tools.ext_function('c_fib2',ext_code,['a'])
    fib.customize.add_support_code(fib_code)
    mod.add_function(fib)       
    mod.compile()

try:
    import fibonacci_ext
except ImportError:
    build_fibonacci()
    import fibonacci_ext
c_fib1 = fibonacci_ext.c_fib1
c_fib2 = fibonacci_ext.c_fib2

#################################################################
# This where it might normally end, but we've added some timings
# below. Recursive solutions are much slower, and C is 10-50x faster
# than equivalent in Python for this simple little routine
#
#################################################################

def py_fib1(a):
    if a <= 2:
        return 1
    else:
        return py_fib1(a-2) + py_fib1(a-1)

def py_fib2(a):
    if a <= 2:
        return 1            
    last = next_to_last = 1
    for i in range(2,a):
        result = last + next_to_last
        next_to_last = last
        last = result
    return result;

import time

def recurse_compare(n):
    print 'Recursively computing the first %d fibonacci numbers:' % n
    t1 = time.time()
    for i in range(n):
        py_fib1(i)
    t2 = time.time()
    py = t2- t1
    print ' speed in python:', t2 - t1
    
    #load into cache
    c_fib1(i)
    t1 = time.time()
    for i in range(n):
        c_fib1(i)
    t2 = time.time()    
    print ' speed in c:',t2 - t1    
    print ' speed up: %3.2f' % (py/(t2-t1))

def loop_compare(m,n):
    print 'Looping to compute the first %d fibonacci numbers:' % n
    t1 = time.time()
    for i in range(m):
        for i in range(n):
            py_fib2(i)
    t2 = time.time()
    py = (t2-t1)
    print ' speed in python:', (t2 - t1)/m
    
    #load into cache
    c_fib2(i)
    t1 = time.time()
    for i in range(m):
        for i in range(n):
            c_fib2(i)
    t2 = time.time()
    print ' speed in c:',(t2 - t1)/ m    
    print ' speed up: %3.2f' % (py/(t2-t1))
    
if __name__ == "__main__":
    n = 30
    recurse_compare(n)
    m= 1000    
    loop_compare(m,n)    
    print 'fib(30)', c_fib1(30),py_fib1(30),c_fib2(30),py_fib2(30)
""" Cast Copy Tranpose is used in Numeric's LinearAlgebra.py to convert
    C ordered arrays to Fortran order arrays before calling Fortran
    functions.  A couple of C implementations are provided here that 
    show modest speed improvements.  One is an "inplace" transpose that
    does an in memory transpose of an arrays elements.  This is the
    fastest approach and is beneficial if you don't need to keep the
    original array.    
"""
# C:\home\ej\wrk\scipy\compiler\examples>python cast_copy_transpose.py
# Cast/Copy/Transposing (150,150)array 1 times
#  speed in python: 0.870999932289
#  speed in c: 0.25
#  speed up: 3.48
#  inplace transpose c: 0.129999995232
#  speed up: 6.70

import Numeric
from Numeric import *
import sys
sys.path.insert(0,'..')
import inline_tools
import c_spec
from converters import blitz as cblitz

def _cast_copy_transpose(type,a_2d):
    assert(len(shape(a_2d)) == 2)
    new_array = zeros(shape(a_2d),type)
    code = """
           for(int i = 0; i < Na_2d[0]; i++)
               for(int j = 0; j < Na_2d[1]; j++)
                   new_array(i,j) = a_2d(j,i);  
           """ 
    inline_tools.inline(code,['new_array','a_2d'],
                        type_converters = cblitz,
                        compiler='gcc',
                        verbose = 1)
    return new_array

def _cast_copy_transpose2(type,a_2d):
    assert(len(shape(a_2d)) == 2)
    new_array = zeros(shape(a_2d),type)
    code = """
           const int I = Na_2d[0];
           const int J = Na_2d[1];
           for(int i = 0; i < I; i++)
           {
               int new_off = i*J;
               int old_off = i;
               for(int j = 0; j < J; j++)
               {
                   new_array[new_off++] = a_2d[old_off];
                   old_off += I; 
               }    
           } 
           """ 
    inline_tools.inline(code,['new_array','a_2d'],compiler='gcc',verbose=1)
    return new_array

def _inplace_transpose(a_2d):
    assert(len(shape(a_2d)) == 2)
    numeric_type = c_spec.num_to_c_types[a_2d.typecode()]
    code = """
           %s temp;
           for(int i = 0; i < Na_2d[0]; i++)
               for(int j = 0; j < Na_2d[1]; j++)
               {
                   temp = a_2d(i,j);
                   a_2d(i,j) = a_2d(j,i);
                   a_2d(j,i) = temp; 
               }     
           """ % numeric_type
    inline_tools.inline(code,['a_2d'],
                        type_converters = cblitz,
                        compiler='gcc',
                        extra_compile_args = ['-funroll-all-loops'],
                        verbose =2 )
    return a_2d
    #assert(len(shape(a_2d)) == 2)
    #type = a_2d.typecode()
    #new_array = zeros(shape(a_2d),type)
    ##trans_a_2d = transpose(a_2d)
    #numeric_type = c_spec.num_to_c_types[type]
    #code = """
    #       for(int i = 0; i < Na_2d[0]; i++)
    #           for(int j = 0; j < Na_2d[1]; j++)
    #               new_array(i,j) = (%s) a_2d(j,i);
    #       """ % numeric_type
    #inline_tools.inline(code,['new_array','a_2d'],
    #                    type_converters = cblitz,
    #                    compiler='gcc',
    #                    verbose = 1)
    #return new_array

def cast_copy_transpose(type,*arrays):
    results = []
    for a in arrays:
        results.append(_cast_copy_transpose(type,a))
    if len(results) == 1:
        return results[0]
    else:
        return results

def cast_copy_transpose2(type,*arrays):
    results = []
    for a in arrays:
        results.append(_cast_copy_transpose2(type,a))
    if len(results) == 1:
        return results[0]
    else:
        return results

def inplace_cast_copy_transpose(*arrays):
    results = []
    for a in arrays:
        results.append(_inplace_transpose(a))
    if len(results) == 1:
        return results[0]
    else:
        return results

def _castCopyAndTranspose(type, *arrays):
    cast_arrays = ()
    for a in arrays:
        if a.typecode() == type:
            cast_arrays = cast_arrays + (copy.copy(Numeric.transpose(a)),)
        else:
            cast_arrays = cast_arrays + (copy.copy(
                                       Numeric.transpose(a).astype(type)),)
    if len(cast_arrays) == 1:
            return cast_arrays[0]
    else:
        return cast_arrays

import time


def compare(m,n):
    a = ones((n,n),Float64)
    type = Float32
    print 'Cast/Copy/Transposing (%d,%d)array %d times' % (n,n,m)
    t1 = time.time()
    for i in range(m):
        for i in range(n):
            b = _castCopyAndTranspose(type,a)
    t2 = time.time()
    py = (t2-t1)
    print ' speed in python:', (t2 - t1)/m
    

    # load into cache    
    b = cast_copy_transpose(type,a)
    t1 = time.time()
    for i in range(m):
        for i in range(n):
            b = cast_copy_transpose(type,a)
    t2 = time.time()
    print ' speed in c (blitz):',(t2 - t1)/ m    
    print ' speed up   (blitz): %3.2f' % (py/(t2-t1))

    # load into cache    
    b = cast_copy_transpose2(type,a)
    t1 = time.time()
    for i in range(m):
        for i in range(n):
            b = cast_copy_transpose2(type,a)
    t2 = time.time()
    print ' speed in c (pointers):',(t2 - t1)/ m    
    print ' speed up   (pointers): %3.2f' % (py/(t2-t1))

    # inplace tranpose
    b = _inplace_transpose(a)
    t1 = time.time()
    for i in range(m):
        for i in range(n):
            b = _inplace_transpose(a)
    t2 = time.time()
    print ' inplace transpose c:',(t2 - t1)/ m    
    print ' speed up: %3.2f' % (py/(t2-t1))
    
if __name__ == "__main__":
    m,n = 1,500
    compare(m,n)    

#! /usr/bin/env python
#
# Copyright 2001-2002 by Vinay Sajip. All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of Vinay Sajip
# not be used in advertising or publicity pertaining to distribution
# of the software without specific, written prior permission.
# VINAY SAJIP DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# VINAY SAJIP BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
# For the change history, see README.txt in the distribution.
#
# This file is part of the Python logging distribution. See
# http://www.red-dove.com/python_logging.html
#

"""
Logging module for Python. Based on PEP 282 and comments thereto in
comp.lang.python, and influenced by Apache's log4j system.

Should work under Python versions >= 1.5.2, except that source line
information is not available unless 'inspect' is.

Copyright (C) 2001-2002 Vinay Sajip. All Rights Reserved.

To use, simply 'import logging' and log away!
"""

import sys, os, types, time, string, socket, cPickle, cStringIO

try:
    import thread
except ImportError:
    thread = None
try:
    import inspect
except ImportError:
    inspect = None

__author__  = "Vinay Sajip <vinay_sajip@red-dove.com>"
__status__  = "alpha"
__version__ = "0.4.1"
__date__    = "03 April 2002"

#---------------------------------------------------------------------------
#   Module data
#---------------------------------------------------------------------------

#
#_srcfile is used when walking the stack to check when we've got the first
# caller stack frame.
#If run as a script, __file__ is not bound.
#
if __name__ == "__main__":
    _srcFile = None
else:
    _srcfile = os.path.splitext(__file__)
    if _srcfile[1] in [".pyc", ".pyo"]:
        _srcfile = _srcfile[0] + ".py"
    else:
        _srcfile = __file__

#
#_start_time is used as the base when calculating the relative time of events
#
_start_time = time.time()

DEFAULT_TCP_LOGGING_PORT    = 9020
DEFAULT_UDP_LOGGING_PORT    = 9021
DEFAULT_HTTP_LOGGING_PORT   = 9022
SYSLOG_UDP_PORT             = 514

#
# Default levels and level names, these can be replaced with any positive set
# of values having corresponding names. There is a pseudo-level, ALL, which
# is only really there as a lower limit for user-defined levels. Handlers and
# loggers are initialized with ALL so that they will log all messages, even
# at user-defined levels.
#
CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARN = 30
INFO = 20
DEBUG = 10
ALL = 0

_levelNames = {
    CRITICAL : 'CRITICAL',
    ERROR    : 'ERROR',
    WARN     : 'WARN',
    INFO     : 'INFO',
    DEBUG    : 'DEBUG',
    ALL      : 'ALL',
}

def getLevelName(lvl):
    """
    Return the textual representation of logging level 'lvl'. If the level is
    one of the predefined levels (CRITICAL, ERROR, WARN, INFO, DEBUG) then you
    get the corresponding string. If you have associated levels with names
    using addLevelName then the name you have associated with 'lvl' is
    returned. Otherwise, the string "Level %s" % lvl is returned.
    """
    return _levelNames.get(lvl, ("Level %s" % lvl))

def addLevelName(lvl, levelName):
    """
    Associate 'levelName' with 'lvl'. This is used when converting levels
    to text during message formatting.
    """
    _levelNames[lvl] = levelName

#---------------------------------------------------------------------------
#   The logging record
#---------------------------------------------------------------------------

class LogRecord:
    """
    LogRecord instances are created every time something is logged. They
    contain all the information pertinent to the event being logged. The
    main information passed in is in msg and args, which are combined
    using msg % args to create the message field of the record. The record
    also includes information such as when the record was created, the
    source line where the logging call was made, and any exception
    information to be logged.
    """
    def __init__(self, name, lvl, pathname, lineno, msg, args, exc_info):
        """
        Initialize a logging record with interesting information.
        """
        ct = time.time()
        self.name = name
        self.msg = msg
        self.args = args
        self.level = getLevelName(lvl)
        self.lvl = lvl
        self.pathname = pathname
        try:
            self.filename = os.path.basename(pathname)
        except:
            self.filename = pathname
        self.exc_info = exc_info
        self.lineno = lineno
        self.created = ct
        self.msecs = (ct - long(ct)) * 1000
        self.relativeCreated = (self.created - _start_time) * 1000
        if thread:
            self.thread = thread.get_ident()
        else:
            self.thread = None

    def __str__(self):
        return '<LogRecord: %s, %s, %s, %s, "%s">'%(self.name, self.lvl,
            self.pathname, self.lineno, self.msg)

#---------------------------------------------------------------------------
#   Formatter classes and functions
#---------------------------------------------------------------------------

class Formatter:
    """
    Formatters need to know how a LogRecord is constructed. They are
    responsible for converting a LogRecord to (usually) a string which can
    be interpreted by either a human or an external system. The base Formatter
    allows a formatting string to be specified. If none is supplied, the
    default value of "%s(message)\\n" is used.

    The Formatter can be initialized with a format string which makes use of
    knowledge of the LogRecord attributes - e.g. the default value mentioned
    above makes use of the fact that the user's message and arguments are pre-
    formatted into a LogRecord's message attribute. Currently, the useful
    attributes in a LogRecord are described by:

    %(name)s            Name of the logger (logging channel)
    %(lvl)s             Numeric logging level for the message (DEBUG, INFO,
                        WARN, ERROR, CRITICAL)
    %(level)s           Text logging level for the message ("DEBUG", "INFO",
                        "WARN", "ERROR", "CRITICAL")
    %(pathname)s        Full pathname of the source file where the logging
                        call was issued (if available)
    %(filename)s        Filename portion of pathname
    %(lineno)d          Source line number where the logging call was issued
                        (if available)
    %(created)f         Time when the LogRecord was created (time.time()
                        return value)
    %(asctime)s         textual time when the LogRecord was created
    %(msecs)d           Millisecond portion of the creation time
    %(relativeCreated)d Time in milliseconds when the LogRecord was created,
                        relative to the time the logging module was loaded
                        (typically at application startup time)
    %(thread)d          Thread ID (if available)
    %(message)s         The result of msg % args, computed just as the
                        record is emitted
    %(msg)s             The raw formatting string provided by the user
    %(args)r            The argument tuple which goes with the formatting
                        string in the msg attribute
    """
    def __init__(self, fmt=None, datefmt=None):
        """
        Initialize the formatter either with the specified format string, or a
        default as described above. Allow for specialized date formatting with
        the optional datefmt argument (if omitted, you get the ISO8601 format).
        """
        if fmt:
            self._fmt = fmt
        else:
            self._fmt = "%(message)s"
        self.datefmt = datefmt

    def formatTime(self, record, datefmt=None):
        """
        This method should be called from format() by a formatter which
        wants to make use of a formatted time. This method can be overridden
        in formatters to provide for any specific requirement, but the
        basic behaviour is as follows: if datefmt (a string) is specfied,
        it is used with time.strftime to format the creation time of the
        record. Otherwise, the ISO8601 format is used. The resulting
        string is written to the asctime attribute of the   record.
        """
        ct = record.created
        if datefmt:
            s = time.strftime(datefmt, time.localtime(ct))
        else:
            t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ct))
            s = "%s,%03d" % (t, record.msecs)
        record.asctime = s

    def formatException(self, ei):
        """
        Format the specified exception information as a string. This
        default implementation just uses traceback.print_exception()
        """
        import traceback
        sio = cStringIO.StringIO()
        traceback.print_exception(ei[0], ei[1], ei[2], None, sio)
        s = sio.getvalue()
        sio.close()
        return s

    def format(self, record):
        """
        The record's attribute dictionary is used as the operand to a
        string formatting operation which yields the returned string.
        Before formatting the dictionary, a couple of preparatory steps
        are carried out. The message attribute of the record is computed
        using msg % args. If the formatting string contains "(asctime)",
        formatTime() is called to format the event time. If there is
        exception information, it is formatted using formatException()
        and appended to the message.
        """
        record.message = record.msg % record.args
        if string.find(self._fmt,"(asctime)") > 0:
            self.formatTime(record, self.datefmt)
        s = self._fmt % record.__dict__
        if record.exc_info:
            if s[-1] != "\n":
                s = s + "\n"
            s = s + self.formatException(record.exc_info)
        return s

#
#   The default formatter to use when no other is specified
#
_defaultFormatter = Formatter()

class BufferingFormatter:
    """
    A formatter suitable for formatting a number of records.
    """
    def __init__(self, linefmt=None):
        """
        Optionally specify a formatter which will be used to format each
        individual record.
        """
        if linefmt:
            self.linefmt = linefmt
        else:
            self.linefmt = _defaultFormatter

    def formatHeader(self, records):
        """
        Return the header string for the specified records.
        """
        return ""

    def formatFooter(self, records):
        """
        Return the footer string for the specified records.
        """
        return ""

    def format(self, records):
        """
        Format the specified records and return the result as a string.
        """
        rv = ""
        if len(records) > 0:
            rv = rv + self.formatHeader(records)
            for record in records:
                rv = rv + self.linefmt.format(record)
            rv = rv + self.formatFooter(records)
        return rv

#---------------------------------------------------------------------------
#   Filter classes and functions
#---------------------------------------------------------------------------

class Filter:
    """
    The base filter class. This class never filters anything, acting as
    a placeholder which defines the Filter interface. Loggers and Handlers
    can optionally use Filter instances to filter records   as desired.
    """
    def filter(self, record):
        """
        Is the specified record to be logged? Returns a boolean value.
        """
        return 1

class Filterer:
    """
    A base class for loggers and handlers which allows them to share
    common code.
    """
    def __init__(self):
        self.filters = []

    def addFilter(self, filter):
        """
        Add the specified filter to this handler.
        """
        if not (filter in self.filters):
            self.filters.append(filter)

    def removeFilter(self, filter):
        """
        Remove the specified filter from this handler.
        """
        if filter in self.filters:
            self.filters.remove(filter)

    def filter(self, record):
        """
        Determine if a record is loggable by consulting all the filters. The
        default is to allow the record to be logged; any filter can veto this
        and the record is then dropped. Returns a boolean value.
        """
        rv = 1
        for f in self.filters:
            if not f.filter(record):
                rv = 0
                break
        return rv

#---------------------------------------------------------------------------
#   Handler classes and functions
#---------------------------------------------------------------------------

_handlers = {}  #repository of handlers (for flushing when shutdown called)

class Handler(Filterer):
    """
    The base handler class. Acts as a placeholder which defines the Handler
    interface. Handlers can optionally use Formatter instances to format
    records as desired. By default, no formatter is specified; in this case,
    the 'raw' message as determined by record.message is logged.
    """
    def __init__(self, level=0):
        """
        Initializes the instance - basically setting the formatter to None
        and the filter list to empty.
        """
        Filterer.__init__(self)
        self.level = level
        self.formatter = None
        _handlers[self] = 1

    def setLevel(self, lvl):
        """
        Set the logging level of this handler.
        """
        self.level = lvl

    def format(self, record):
        """
        Do formatting for a record - if a formatter is set, use it.
        Otherwise, use the default formatter for the module.
        """
        if self.formatter:
            fmt = self.formatter
        else:
            fmt = _defaultFormatter
        return fmt.format(record)

    def emit(self, record):
        """
        Do whatever it takes to actually log the specified logging record.
        This version is intended to be implemented by subclasses and so
        raises a NotImplementedError.
        """
        raise NotImplementedError, 'emit must be implemented '\
                                    'by Handler subclasses'

    def handle(self, record):
        """
        Conditionally handle the specified logging record, depending on
        filters which may have been added   to the handler.
        """
        if self.filter(record):
            self.emit(record)

    def setFormatter(self, fmt):
        """
        Set the formatter for this handler.
        """
        self.formatter = fmt

    def flush(self):
        """
        Ensure all logging output has been flushed. This version does
        nothing and is intended to be implemented by subclasses.
        """
        pass

    def close(self):
        """
        Tidy up any resources used by the handler. This version does
        nothing and is intended to be implemented by subclasses.
        """
        pass

    def handleError(self):
        """
        This method should be called from handlers when an exception is
        encountered during an emit() call. By default it does nothing,
        which means that exceptions get silently ignored. This is what is
        mostly wanted for a logging system - most users will not care
        about errors in the logging system, they are more interested in
        application errors. You could, however, replace this with a custom
        handler if you wish.
        """
        #import traceback
        #ei = sys.exc_info()
        #traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
        #del ei
        pass

class StreamHandler(Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a stream. Note that this class does not close the stream, as
    sys.stdout or sys.stderr may be used.
    """
    def __init__(self, strm=None):
        """
        If strm is not specified, sys.stderr is used.
        """
        Handler.__init__(self)
        if not strm:
            strm = sys.stderr
        self.stream = strm
        self.formatter = None

    def flush(self):
        """
        Flushes the stream.
        """
        self.stream.flush()

    def emit(self, record):
        """
        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline
        [N.B. this may be removed depending on feedback]. If exception
        information is present, it is formatted using
        traceback.print_exception and appended to the stream.
        """
        try:
            msg = self.format(record)
            self.stream.write("%s\n" % msg)
            self.flush()
        except:
            self.handleError()

class FileHandler(StreamHandler):
    """
    A handler class which writes formatted logging records to disk files.
    """
    def __init__(self, filename, mode="a+"):
        """
        Open the specified file and use it as the stream for logging.
        By default, the file grows indefinitely. You can call setRollover()
        to allow the file to rollover at a predetermined size.
        """
        StreamHandler.__init__(self, open(filename, mode))
        self.max_size = 0
        self.backup_count = 0
        self.basefilename = filename
        self.backup_index = 0
        self.mode = mode

    def setRollover(self, max_size, backup_count):
        """
        Set the rollover parameters so that rollover occurs whenever the
        current log file is nearly max_size in length. If backup_count
        is >= 1, the system will successively create new files with the
        same pathname as the base file, but with extensions ".1", ".2"
        etc. appended to it. For example, with a backup_count of 5 and a
        base file name of "app.log", you would get "app.log", "app.log.1",
        "app.log.2", ... through to "app.log.5". When the last file reaches
        its size limit, the logging reverts to "app.log" which is truncated
        to zero length. If max_size is zero, rollover never occurs.
        """
        self.max_size = max_size
        self.backup_count = backup_count
        if max_size > 0:
            self.mode = "a+"

    def doRollover(self):
        """
        Do a rollover, as described in setRollover().
        """
        if self.backup_index >= self.backup_count:
            self.backup_index = 0
            fn = self.basefilename
        else:
            self.backup_index = self.backup_index + 1
            fn = "%s.%d" % (self.basefilename, self.backup_index)
        self.stream.close()
        self.stream = open(fn, "w+")

    def emit(self, record):
        """
        Output the record to the file, catering for rollover as described
        in setRollover().
        """
        if self.max_size > 0:                   # are we rolling over?
            msg = "%s\n" % self.format(record)
            if self.stream.tell() + len(msg) >= self.max_size:
                self.doRollover()
        StreamHandler.emit(self, record)

    def close(self):
        """
        Closes the stream.
        """
        self.stream.close()

class SocketHandler(StreamHandler):
    """
    A handler class which writes logging records, in pickle format, to
    a streaming socket. The socket is kept open across logging calls.
    If the peer resets it, an attempt is made   to reconnect on the next call.
    """

    def __init__(self, host, port):
        """
        Initializes the handler with a specific host address and port.
        """
        StreamHandler.__init__(self)
        self.host = host
        self.port = port
        self.sock = None
        self.closeOnError = 1

    def makeSocket(self):
        """
        A factory method which allows subclasses to define the precise
        type of socket they want.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        return s

    def send(self, s):
        """
        Send a pickled string to the socket. This function allows for
        partial sends which can happen when the network is busy.
        """
        sentsofar = 0
        left = len(s)
        while left > 0:
            sent = self.sock.send(s[sentsofar:])
            sentsofar = sentsofar + sent
            left = left - sent

    def makePickle(self, record):
        """
        Pickle the record in binary format with a length prefix.
        """
        s = cPickle.dumps(record.__dict__, 1)
        n = len(s)
        slen = "%c%c" % ((n >> 8) & 0xFF, n & 0xFF)
        return slen + s

    def handleError(self):
        """
        An error has occurred during logging. Most likely cause -
        connection lost. Close the socket so that we can retry on the
        next event.
        """
        if self.closeOnError and self.sock:
            self.sock.close()
            self.sock = None        #try to reconnect next time

    def emit(self, record):
        """
        Pickles the record and writes it to the socket in binary format.
        If there is an error    with the socket, silently drop the packet.
        """
        try:
            s = self.makePickle(record)
            if not self.sock:
                self.sock = self.makeSocket()
            self.send(s)
        except:
            self.handleError()

    def close(self):
        """
        Closes the socket.
        """
        if self.sock:
            self.sock.close()
            self.sock = None

class DatagramHandler(SocketHandler):
    """
    A handler class which writes logging records, in pickle format, to
    a datagram socket.
    """
    def __init__(self, host, port):
        """
        Initializes the handler with a specific host address and port.
        """
        SocketHandler.__init__(self, host, port)
        self.closeOnError = 0

    def makeSocket(self):
        """
        The factory method of SocketHandler is here overridden to create
        a UDP socket (SOCK_DGRAM).
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return s

    def sendto(self, s, addr):
        """
        Send a pickled string to a socket. This function allows for
        partial sends which can happen when the network is busy.
        """
        sentsofar = 0
        left = len(s)
        while left > 0:
            sent = self.sock.sendto(s[sentsofar:], addr)
            sentsofar = sentsofar + sent
            left = left - sent

    def emit(self, record):
        """
        Pickles the record and writes it to the socket in binary format.
        """
        try:
            s = self.makePickle(record)
            if not self.sock:
                self.sock = self.makeSocket()
            self.sendto(s, (self.host, self.port))
        except:
            self.handleError()

class SysLogHandler(Handler):
    """
    A handler class which sends formatted logging records to a syslog
    server. Based on Sam Rushing's syslog module:
    http://www.nightmare.com/squirl/python-ext/misc/syslog.py
    Contributed by Nicolas Untz (after which minor refactoring changes
    have been made).
    """

    # from <linux/sys/syslog.h>:
    # ======================================================================
    # priorities/facilities are encoded into a single 32-bit quantity, where
    # the bottom 3 bits are the priority (0-7) and the top 28 bits are the
    # facility (0-big number). Both the priorities and the facilities map
    # roughly one-to-one to strings in the syslogd(8) source code.  This
    # mapping is included in this file.
    #
    # priorities (these are ordered)

    LOG_EMERG     = 0       #  system is unusable
    LOG_ALERT     = 1       #  action must be taken immediately
    LOG_CRIT      = 2       #  critical conditions
    LOG_ERR       = 3       #  error conditions
    LOG_WARNING   = 4       #  warning conditions
    LOG_NOTICE    = 5       #  normal but significant condition
    LOG_INFO      = 6       #  informational
    LOG_DEBUG     = 7       #  debug-level messages

    #  facility codes
    LOG_KERN      = 0       #  kernel messages
    LOG_USER      = 1       #  random user-level messages
    LOG_MAIL      = 2       #  mail system
    LOG_DAEMON    = 3       #  system daemons
    LOG_AUTH      = 4       #  security/authorization messages
    LOG_SYSLOG    = 5       #  messages generated internally by syslogd
    LOG_LPR       = 6       #  line printer subsystem
    LOG_NEWS      = 7       #  network news subsystem
    LOG_UUCP      = 8       #  UUCP subsystem
    LOG_CRON      = 9       #  clock daemon
    LOG_AUTHPRIV  = 10  #  security/authorization messages (private)

    #  other codes through 15 reserved for system use
    LOG_LOCAL0    = 16      #  reserved for local use
    LOG_LOCAL1    = 17      #  reserved for local use
    LOG_LOCAL2    = 18      #  reserved for local use
    LOG_LOCAL3    = 19      #  reserved for local use
    LOG_LOCAL4    = 20      #  reserved for local use
    LOG_LOCAL5    = 21      #  reserved for local use
    LOG_LOCAL6    = 22      #  reserved for local use
    LOG_LOCAL7    = 23      #  reserved for local use

    priority_names = {
        "alert":    LOG_ALERT,
        "crit":     LOG_CRIT,
        "critical": LOG_CRIT,
        "debug":    LOG_DEBUG,
        "emerg":    LOG_EMERG,
        "err":      LOG_ERR,
        "error":    LOG_ERR,        #  DEPRECATED
        "info":     LOG_INFO,
        "notice":   LOG_NOTICE,
        "panic":    LOG_EMERG,      #  DEPRECATED
        "warn":     LOG_WARNING,    #  DEPRECATED
        "warning":  LOG_WARNING,
        }

    facility_names = {
        "auth":     LOG_AUTH,
        "authpriv": LOG_AUTHPRIV,
        "cron":     LOG_CRON,
        "daemon":   LOG_DAEMON,
        "kern":     LOG_KERN,
        "lpr":      LOG_LPR,
        "mail":     LOG_MAIL,
        "news":     LOG_NEWS,
        "security": LOG_AUTH,       #  DEPRECATED
        "syslog":   LOG_SYSLOG,
        "user":     LOG_USER,
        "uucp":     LOG_UUCP,
        "local0":   LOG_LOCAL0,
        "local1":   LOG_LOCAL1,
        "local2":   LOG_LOCAL2,
        "local3":   LOG_LOCAL3,
        "local4":   LOG_LOCAL4,
        "local5":   LOG_LOCAL5,
        "local6":   LOG_LOCAL6,
        "local7":   LOG_LOCAL7,
        }

    def __init__(self, address=('localhost', SYSLOG_UDP_PORT), facility=LOG_USER):
        """
        If address is not specified, UNIX socket is used.
        If facility is not specified, LOG_USER is used.
        """
        Handler.__init__(self)

        self.address = address
        self.facility = facility
        if type(address) == types.StringType:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.connect(address)
            self.unixsocket = 1
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.unixsocket = 0

        self.formatter = None

    # curious: when talking to the unix-domain '/dev/log' socket, a
    #   zero-terminator seems to be required.  this string is placed
    #   into a class variable so that it can be overridden if
    #   necessary.
    log_format_string = '<%d>%s\000'

    def encodePriority (self, facility, priority):
        """
        Encode the facility and priority. You can pass in strings or
        integers - if strings are passed, the facility_names and
        priority_names mapping dictionaries are used to convert them to
        integers.
        """
        if type(facility) == types.StringType:
            facility = self.facility_names[facility]
        if type(priority) == types.StringType:
            priority = self.priority_names[priority]
        return (facility << 3) | priority

    def close (self):
        """
        Closes the socket.
        """
        if self.unixsocket:
            self.socket.close()

    def emit(self, record):
        """
        The record is formatted, and then sent to the syslog server. If
        exception information is present, it is NOT sent to the server.
        """
        msg = self.format(record)
        """
        We need to convert record level to lowercase, maybe this will
        change in the future.
        """
        msg = self.log_format_string % (
            self.encodePriority(self.facility, string.lower(record.level)),
            msg)
        try:
            if self.unixsocket:
                self.socket.send(msg)
            else:
                self.socket.sendto(msg, self.address)
        except:
            self.handleError()

class SMTPHandler(Handler):
    """
    A handler class which sends an SMTP email for each logging event.
    """
    def __init__(self, mailhost, fromaddr, toaddrs, subject):
        """
        Initialize the instance with the from and to addresses and subject
        line of the email. To specify a non-standard SMTP port, use the
        (host, port) tuple format for the mailhost argument.
        """
        Handler.__init__(self)
        if type(mailhost) == types.TupleType:
            host, port = mailhost
            self.mailhost = host
            self.mailport = port
        else:
            self.mailhost = mailhost
            self.mailport = None
        self.fromaddr = fromaddr
        self.toaddrs = toaddrs
        self.subject = subject

    def getSubject(self, record):
        """
        If you want to specify a subject line which is record-dependent,
        override this method.
        """
        return self.subject

    def emit(self, record):
        """
        Format the record and send it to the specified addressees.
        """
        try:
            import smtplib
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port)
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s" % (
                            self.fromaddr,
                            string.join(self.toaddrs, ","),
                            self.getSubject(record), msg
                            )
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except:
            self.handleError()

class BufferingHandler(Handler):
    """
  A handler class which buffers logging records in memory. Whenever each
  record is added to the buffer, a check is made to see if the buffer should
  be flushed. If it should, then flush() is expected to do the needful.
    """
    def __init__(self, capacity):
        """
        Initialize the handler with the buffer size.
        """
        Handler.__init__(self)
        self.capacity = capacity
        self.buffer = []

    def shouldFlush(self, record):
        """
        Returns true if the buffer is up to capacity. This method can be
        overridden to implement custom flushing strategies.
        """
        return (len(self.buffer) >= self.capacity)

    def emit(self, record):
        """
        Append the record. If shouldFlush() tells us to, call flush() to process
        the buffer.
        """
        self.buffer.append(record)
        if self.shouldFlush(record):
            self.flush()

    def flush(self):
        """
        Override to implement custom flushing behaviour. This version just zaps
        the buffer to empty.
        """
        self.buffer = []

class MemoryHandler(BufferingHandler):
    """
    A handler class which buffers logging records in memory, periodically
    flushing them to a target handler. Flushing occurs whenever the buffer
    is full, or when an event of a certain severity or greater is seen.
    """
    def __init__(self, capacity, flushLevel=ERROR, target=None):
        """
        Initialize the handler with the buffer size, the level at which
        flushing should occur and an optional target. Note that without a
        target being set either here or via setTarget(), a MemoryHandler
        is no use to anyone!
        """
        BufferingHandler.__init__(self, capacity)
        self.flushLevel = flushLevel
        self.target = target

    def shouldFlush(self, record):
        """
        Check for buffer full or a record at the flushLevel or higher.
        """
        return (len(self.buffer) >= self.capacity) or \
                (record.lvl >= self.flushLevel)

    def setTarget(self, target):
        """
        Set the target handler for this handler.
        """
        self.target = target

    def flush(self):
        """
        For a MemoryHandler, flushing means just sending the buffered
        records to the target, if there is one. Override if you want
        different behaviour.
        """
        if self.target:
            for record in self.buffer:
                self.target.handle(record)
            self.buffer = []

class NTEventLogHandler(Handler):
    """
    A handler class which sends events to the NT Event Log. Adds a
    registry entry for the specified application name. If no dllname is
    provided, win32service.pyd (which contains some basic message
    placeholders) is used. Note that use of these placeholders will make
    your event logs big, as the entire message source is held in the log.
    If you want slimmer logs, you have to pass in the name of your own DLL
    which contains the message definitions you want to use in the event log.
    """
    def __init__(self, appname, dllname=None, logtype="Application"):
        Handler.__init__(self)
        try:
            import win32evtlogutil, win32evtlog
            self.appname = appname
            self._welu = win32evtlogutil
            if not dllname:
                import os
                dllname = os.path.split(self._welu.__file__)
                dllname = os.path.split(dllname[0])
                dllname = os.path.join(dllname[0], r'win32service.pyd')
            self.dllname = dllname
            self.logtype = logtype
            self._welu.AddSourceToRegistry(appname, dllname, logtype)
            self.deftype = win32evtlog.EVENTLOG_ERROR_TYPE
            self.typemap = {
                DEBUG   : win32evtlog.EVENTLOG_INFORMATION_TYPE,
                INFO    : win32evtlog.EVENTLOG_INFORMATION_TYPE,
                WARN    : win32evtlog.EVENTLOG_WARNING_TYPE,
                ERROR   : win32evtlog.EVENTLOG_ERROR_TYPE,
                CRITICAL: win32evtlog.EVENTLOG_ERROR_TYPE,
         }
        except ImportError:
            print "The Python Win32 extensions for NT (service, event "\
                        "logging) appear not to be available."
            self._welu = None

    def getMessageID(self, record):
        """
        Return the message ID for the event record. If you are using your
        own messages, you could do this by having the msg passed to the
        logger being an ID rather than a formatting string. Then, in here,
        you could use a dictionary lookup to get the message ID. This
        version returns 1, which is the base message ID in win32service.pyd.
        """
        return 1

    def getEventCategory(self, record):
        """
        Return the event category for the record. Override this if you
        want to specify your own categories. This version returns 0.
        """
        return 0

    def getEventType(self, record):
        """
        Return the event type for the record. Override this if you want
        to specify your own types. This version does a mapping using the
        handler's typemap attribute, which is set up in __init__() to a
        dictionary which contains mappings for DEBUG, INFO, WARN, ERROR
        and CRITICAL. If you are using your own levels you will either need
        to override this method or place a suitable dictionary in the
        handler's typemap attribute.
        """
        return self.typemap.get(record.lvl, self.deftype)

    def emit(self, record):
        """
        Determine the message ID, event category and event type. Then
        log the message in the NT event log.
        """
        if self._welu:
            try:
                id = self.getMessageID(record)
                cat = self.getEventCategory(record)
                type = self.getEventType(record)
                msg = self.format(record)
                self._welu.ReportEvent(self.appname, id, cat, type, [msg])
            except:
                self.handleError()

    def close(self):
        """
        You can remove the application name from the registry as a
        source of event log entries. However, if you do this, you will
        not be able to see the events as you intended in the Event Log
        Viewer - it needs to be able to access the registry to get the
        DLL name.
        """
        #self._welu.RemoveSourceFromRegistry(self.appname, self.logtype)
        pass

class HTTPHandler(Handler):
    """
    A class which sends records to a Web server, using either GET or
    POST semantics.
    """
    def __init__(self, host, url, method="GET"):
        """
        Initialize the instance with the host, the request URL, and the method
        ("GET" or "POST")
        """
        Handler.__init__(self)
        method = string.upper(method)
        if method not in ["GET", "POST"]:
            raise ValueError, "method must be GET or POST"
        self.host = host
        self.url = url
        self.method = method

    def emit(self, record):
        """
        Send the record to the Web server as an URL-encoded dictionary
        """
        try:
            import httplib, urllib
            h = httplib.HTTP(self.host)
            url = self.url
            data = urllib.urlencode(record.__dict__)
            if self.method == "GET":
                if (string.find(url, '?') >= 0):
                    sep = '&'
                else:
                    sep = '?'
                url = url + "%c%s" % (sep, data)
            h.putrequest(self.method, url)
            if self.method == "POST":
                h.putheader("Content-length", str(len(data)))
            h.endheaders()
            if self.method == "POST":
                h.send(data)
            h.getreply()    #can't do anything with the result
        except:
            self.handleError()

SOAP_MESSAGE = """<SOAP-ENV:Envelope
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:logging="http://www.red-dove.com/logging"
    SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
>
    <SOAP-ENV:Body>
        <logging:log>
%s
        </logging:log>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
"""

class SOAPHandler(Handler):
    """
    A class which sends records to a SOAP server.
    """
    def __init__(self, host, url):
        """
        Initialize the instance with the host and the request URL
        """
        Handler.__init__(self)
        self.host = host
        self.url = url

    def emit(self, record):
        """
        Send the record to the Web server as a SOAP message
        """
        try:
            import httplib, urllib
            h = httplib.HTTP(self.host)
            h.putrequest("POST", self.url)
            keys = record.__dict__.keys()
            keys.sort()
            args = ""
            for key in keys:
                v = record.__dict__[key]
                if type(v) == types.StringType:
                    t = "string"
                elif (type(v) == types.IntType) or (type(v) == types.LongType):
                    t = "integer"
                elif type(v) == types.FloatType:
                    t = "float"
                else:
                    t = "string"
                args = args + "%12s<logging:%s xsi:type=\"xsd:%s\">%s</logging:%s>\n" % ("",
                               key, t, str(v), key)
            data = SOAP_MESSAGE % args[:-1]
            #print data
            h.putheader("Content-type", "text/plain; charset=\"utf-8\"")
            h.putheader("Content-length", str(len(data)))
            h.endheaders()
            h.send(data)
            r = h.getreply()    #can't do anything with the result
            #print r
            f = h.getfile()
            #print f.read()
            f.close()
        except:
            self.handleError()

#---------------------------------------------------------------------------
#   Manager classes and functions
#---------------------------------------------------------------------------

class PlaceHolder:
    """
    PlaceHolder instances are used in the Manager logger hierarchy to take
    the place of nodes for which no loggers have been defined [FIXME add
    example].
    """
    def __init__(self, alogger):
        """
        Initialize with the specified logger being a child of this placeholder.
        """
        self.loggers = [alogger]

    def append(self, alogger):
        """
        Add the specified logger as a child of this placeholder.
        """
        if alogger not in self.loggers:
            self.loggers.append(alogger)

#
#   Determine which class to use when instantiating loggers.
#
_loggerClass = None

def setLoggerClass(klass):
    """
    Set the class to be used when instantiating a logger. The class should
    define __init__() such that only a name argument is required, and the
    __init__() should call Logger.__init__()
    """
    if klass != Logger:
        if type(klass) != types.ClassType:
            raise TypeError, "setLoggerClass is expecting a class"
        if not (Logger in klass.__bases__):
            raise TypeError, "logger not derived from logging.Logger: " + \
                            klass.__name__
    global _loggerClass
    _loggerClass = klass

class Manager:
    """
    There is [under normal circumstances] just one Manager instance, which
    holds the hierarchy of loggers.
    """
    def __init__(self, root):
        """
        Initialize the manager with the root node of the logger hierarchy.
        """
        self.root = root
        self.disable = 0
        self.emittedNoHandlerWarning = 0
        self.loggerDict = {}

    def getLogger(self, name):
        """
        Get a logger with the specified name, creating it if it doesn't
        yet exist. If a PlaceHolder existed for the specified name [i.e.
        the logger didn't exist but a child of it did], replace it with
        the created logger and fix up the parent/child references which
        pointed to the placeholder to now point to the logger.
        """
        rv = None
        if self.loggerDict.has_key(name):
            rv = self.loggerDict[name]
            if isinstance(rv, PlaceHolder):
                ph = rv
                rv = _loggerClass(name)
                rv.manager = self
                self.loggerDict[name] = rv
                self._fixupChildren(ph, rv)
                self._fixupParents(rv)
        else:
            rv = _loggerClass(name)
            rv.manager = self
            self.loggerDict[name] = rv
            self._fixupParents(rv)
        return rv

    def _fixupParents(self, alogger):
        """
        Ensure that there are either loggers or placeholders all the way
        from the specified logger to the root of the logger hierarchy.
        """
        name = alogger.name
        i = string.rfind(name, ".")
        rv = None
        while (i > 0) and not rv:
            substr = name[:i]
            if not self.loggerDict.has_key(substr):
                self.loggerDict[name] = PlaceHolder(alogger)
            else:
                obj = self.loggerDict[substr]
                if isinstance(obj, Logger):
                    rv = obj
                else:
                    assert isinstance(obj, PlaceHolder)
                    obj.append(alogger)
            i = string.rfind(name, ".", 0, i - 1)
        if not rv:
            rv = self.root
        alogger.parent = rv

    def _fixupChildren(self, ph, alogger):
        """
        Ensure that children of the placeholder ph are connected to the
        specified logger.
        """
        for c in ph.loggers:
            if string.find(c.parent.name, alogger.name) <> 0:
                alogger.parent = c.parent
                c.parent = alogger

#---------------------------------------------------------------------------
#   Logger classes and functions
#---------------------------------------------------------------------------

class Logger(Filterer):
    """
    Instances of the Logger class represent a single logging channel.
    """
    def __init__(self, name, level=0):
        """
        Initialize the logger with a name and an optional level.
        """
        Filterer.__init__(self)
        self.name = name
        self.level = level
        self.parent = None
        self.propagate = 1
        self.handlers = []

    def setLevel(self, lvl):
        """
        Set the logging level of this logger.
        """
        self.level = lvl

#   def getRoot(self):
#       """
#       Get the root of the logger hierarchy.
#       """
#       return Logger.root

    def debug(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'DEBUG'. To pass exception information,
        use the keyword argument exc_info with a true value, e.g.

        logger.debug("Houston, we have a %s", "thorny problem", exc_info=1)
        """
        if self.manager.disable >= DEBUG:
            return
        if DEBUG >= self.getEffectiveLevel():
            apply(self._log, (DEBUG, msg, args), kwargs)

    def info(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'INFO'. To pass exception information,
        use the keyword argument exc_info with a true value, e.g.

        logger.info("Houston, we have a %s", "interesting problem", exc_info=1)
        """
        if self.manager.disable >= INFO:
            return
        if INFO >= self.getEffectiveLevel():
            apply(self._log, (INFO, msg, args), kwargs)

    def warn(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'WARN'. To pass exception information,
        use the keyword argument exc_info with a true value, e.g.

        logger.warn("Houston, we have a %s", "bit of a problem", exc_info=1)
        """
        if self.manager.disable >= WARN:
            return
        if self.isEnabledFor(WARN):
            apply(self._log, (WARN, msg, args), kwargs)

    def error(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'ERROR'. To pass exception information,
        use the keyword argument exc_info with a true value, e.g.

        logger.error("Houston, we have a %s", "major problem", exc_info=1)
        """
        if self.manager.disable >= ERROR:
            return
        if self.isEnabledFor(ERROR):
            apply(self._log, (ERROR, msg, args), kwargs)

    def exception(self, msg, *args):
        """
        Convenience method for logging an ERROR with exception information
        """
        apply(self.error, (msg,) + args, {'exc_info': 1})

    def critical(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'CRITICAL'. To pass exception
        information, use the keyword argument exc_info with a true value, e.g.

        logger.critical("Houston, we have a %s", "major disaster", exc_info=1)
        """
        if self.manager.disable >= CRITICAL:
            return
        if CRITICAL >= self.getEffectiveLevel():
            apply(self._log, (CRITICAL, msg, args), kwargs)

    fatal = critical

    def log(self, lvl, msg, *args, **kwargs):
        """
        Log 'msg % args' with the severity 'lvl'. To pass exception
        information, use the keyword argument exc_info with a true value, e.g.
        logger.log(lvl, "We have a %s", "mysterious problem", exc_info=1)
        """
        if self.manager.disable >= lvl:
            return
        if self.isEnabledFor(lvl):
            apply(self._log, (lvl, msg, args), kwargs)

    def findCaller(self):
        """
        Find the stack frame of the caller so that we can note the source
        file name and line number.
        """
        frames = inspect.stack()[1:]
        for f in frames:
            if _srcfile != f[1]:
                return (f[1], f[2])
        return (None, None)

    def makeRecord(self, name, lvl, fn, lno, msg, args, exc_info):
        """
        A factory method which can be overridden in subclasses to create
        specialized LogRecords.
        """
        return LogRecord(name, lvl, fn, lno, msg, args, exc_info)

    def _log(self, lvl, msg, args, exc_info=None):
        """
        Low-level logging routine which creates a LogRecord and then calls
        all the handlers of this logger to handle the record.
        """
        if inspect:
            fn, lno = self.findCaller()
        else:
            fn, lno = "<unknown file>", 0
        if exc_info:
            exc_info = sys.exc_info()
        record = self.makeRecord(self.name, lvl, fn, lno, msg, args, exc_info)
        self.handle(record)

    def handle(self, record):
        """
        Call the handlers for the specified record. This method is used for
        unpickled records received from a socket, as well as those created
        locally. Logger-level filtering is applied.
        """
        if self.filter(record):
            self.callHandlers(record)

    def addHandler(self, hdlr):
        """
        Add the specified handler to this logger.
        """
        if not (hdlr in self.handlers):
            self.handlers.append(hdlr)

    def removeHandler(self, hdlr):
        """
        Remove the specified handler from this logger.
        """
        if hdlr in self.handlers:
            self.handlers.remove(hdlr)

    def callHandlers(self, record):
        """
        Loop through all handlers for this logger and its parents in the
        logger hierarchy. If no handler was found, output a one-off error
        message. Stop searching up the hierarchy whenever a logger with the
        "propagate" attribute set to zero is found - that will be the last
        logger whose handlers are called.
        """
        c = self
        found = 0
        while c:
            for hdlr in c.handlers:
                found = found + 1
                if record.lvl >= hdlr.level:
                    hdlr.handle(record)
            if not c.propagate:
                c = None    #break out
            else:
                c = c.parent
        if (found == 0) and not self.manager.emittedNoHandlerWarning:
            print "No handlers could be found for logger \"%s\"" % self.name
            self.manager.emittedNoHandlerWarning = 1

    def getEffectiveLevel(self):
        """
        Loop through this logger and its parents in the logger hierarchy,
        looking for a non-zero logging level. Return the first one found.
        """
        c = self
        while c:
            if c.level:
                return c.level
            c = c.parent
        #print "NCP", self.parent

    def isEnabledFor(self, lvl):
        """
        Is this logger enabled for level lvl?
        """
        if self.manager.disable >= lvl:
            return 0
        return lvl >= self.getEffectiveLevel()

class RootLogger(Logger):
    """
    A root logger is not that different to any other logger, except that
    it must have a logging level and there is only one instance of it in
    the hierarchy.
    """
    def __init__(self, lvl):
        """
        Initialize the logger with the name "root".
        """
        Logger.__init__(self, "root", lvl)

_loggerClass = Logger

root = RootLogger(DEBUG)
Logger.root = root
Logger.manager = Manager(Logger.root)

#---------------------------------------------------------------------------
# Configuration classes and functions
#---------------------------------------------------------------------------

BASIC_FORMAT = "%(asctime)s %(name)-19s %(level)-5s - %(message)s"

def basicConfig():
    """
    Do basic configuration for the logging system by creating a
    StreamHandler with a default Formatter and adding it to the
    root logger.
    """
    hdlr = StreamHandler()
    fmt = Formatter(BASIC_FORMAT)
    hdlr.setFormatter(fmt)
    root.addHandler(hdlr)

#def fileConfig(fname):
#    """
#    The old implementation - using dict-based configuration files.
#    Read the logging configuration from a file. Keep it simple for now.
#    """
#    file = open(fname, "r")
#    data = file.read()
#    file.close()
#    dict = eval(data)
#    handlers = dict.get("handlers", [])
#    loggers = dict.get("loggers", [])
#    formatters = dict.get("formatters", [])
#    for f in formatters:
#        fd = dict[f]
#        fc = fd.get("class", "logging.Formatter")
#        args = fd.get("args", ())
#        fc = eval(fc)
#        try:
#            fmt = apply(fc, args)
#        except:
#            print fc, args
#            raise
#        dict[f] = fmt
#
#    for h in handlers:
#        hd = dict[h]
#        hc = hd.get("class", "logging.StreamHandler")
#        args = hd.get("args", ())
#        hc = eval(hc)
#        fmt = hd.get("formatter", None)
#        if fmt:
#            fmt = dict.get(fmt, None)
#        try:
#            hdlr = apply(hc, args)
#        except:
#            print hc, args
#            raise
#        if fmt:
#            hdlr.setFormatter(fmt)
#        dict[h] = hdlr
#
#    for ln in loggers:
#        ld = dict[ln]
#        name = ld.get("name", None)
#        if name:
#            logger = getLogger(name)
#        else:
#            logger = getRootLogger()
#        logger.propagate = ld.get("propagate", 1)
#        hdlrs = ld.get("handlers", [])
#        for h in hdlrs:
#            hdlr = dict.get(h, None)
#            if hdlr:
#                logger.addHandler(hdlr)

def fileConfig(fname):
    """
    Read the logging configuration from a ConfigParser-format file.
    """
    import ConfigParser

    cp = ConfigParser.ConfigParser()
    cp.read(fname)
    #first, do the formatters...
    flist = cp.get("formatters", "keys")
    flist = string.split(flist, ",")
    formatters = {}
    for form in flist:
        sectname = "formatter_%s" % form
        fs = cp.get(sectname, "format", 1)
        dfs = cp.get(sectname, "datefmt", 1)
        f = Formatter(fs, dfs)
        formatters[form] = f
    #next, do the handlers...
    hlist = cp.get("handlers", "keys")
    hlist = string.split(hlist, ",")
    handlers = {}
    for hand in hlist:
        sectname = "handler_%s" % hand
        klass = cp.get(sectname, "class")
        fmt = cp.get(sectname, "formatter")
        lvl = cp.get(sectname, "level")
        klass = eval(klass)
        args = cp.get(sectname, "args")
        args = eval(args)
        h = apply(klass, args)
        h.setLevel(eval(lvl))
        h.setFormatter(formatters[fmt])
        #temporary hack for FileHandler.
        if klass == FileHandler:
            maxsize = cp.get(sectname, "maxsize")
            if maxsize:
                maxsize = eval(maxsize)
            else:
                maxsize = 0
            if maxsize:
                backcount = cp.get(sectname, "backcount")
                if backcount:
                    backcount = eval(backcount)
                else:
                    backcount = 0
                h.setRollover(maxsize, backcount)
        handlers[hand] = h
    #at last, the loggers...first the root...
    llist = cp.get("loggers", "keys")
    llist = string.split(llist, ",")
    llist.remove("root")
    sectname = "logger_root"
    log = root
    lvl = cp.get(sectname, "level")
    log.setLevel(eval(lvl))
    hlist = cp.get(sectname, "handlers")
    hlist = string.split(hlist, ",")
    for hand in hlist:
        log.addHandler(handlers[hand])
    #and now the others...
    for log in llist:
        sectname = "logger_%s" % log
        qn = cp.get(sectname, "qualname")
        lvl = cp.get(sectname, "level")
        propagate = cp.get(sectname, "propagate")
        logger = getLogger(qn)
        logger.setLevel(eval(lvl))
        logger.propagate = eval(propagate)
        hlist = cp.get(sectname, "handlers")
        hlist = string.split(hlist, ",")
        for hand in hlist:
            logger.addHandler(handlers[hand])


#---------------------------------------------------------------------------
# Utility functions at module level.
# Basically delegate everything to the root logger.
#---------------------------------------------------------------------------

def getLogger(name):
    """
    Return a logger with the specified name, creating it if necessary.
    If no name is specified, return the root logger.
    """
    if name:
        return Logger.manager.getLogger(name)
    else:
        return root

def getRootLogger():
    """
    Return the root logger.
    """
    return root

def critical(msg, *args, **kwargs):
    """
    Log a message with severity 'CRITICAL' on the root logger.
    """
    if len(root.handlers) == 0:
        basicConfig()
    apply(root.critical, (msg,)+args, kwargs)

fatal = critical

def error(msg, *args, **kwargs):
    """
    Log a message with severity 'ERROR' on the root logger.
    """
    if len(root.handlers) == 0:
        basicConfig()
    apply(root.error, (msg,)+args, kwargs)

def exception(msg, *args):
    """
    Log a message with severity 'ERROR' on the root logger,
    with exception information.
    """
    apply(error, (msg,)+args, {'exc_info': 1})

def warn(msg, *args, **kwargs):
    """
    Log a message with severity 'WARN' on the root logger.
    """
    if len(root.handlers) == 0:
        basicConfig()
    apply(root.warn, (msg,)+args, kwargs)

def info(msg, *args, **kwargs):
    """
    Log a message with severity 'INFO' on the root logger.
    """
    if len(root.handlers) == 0:
        basicConfig()
    apply(root.info, (msg,)+args, kwargs)

def debug(msg, *args, **kwargs):
    """
    Log a message with severity 'DEBUG' on the root logger.
    """
    if len(root.handlers) == 0:
        basicConfig()
    apply(root.debug, (msg,)+args, kwargs)

def disable(level):
    """
    Disable all logging calls less severe than 'level'.
    """
    root.manager.disable = level

def shutdown():
    """
    Perform any cleanup actions in the logging system (e.g. flushing
    buffers). Should be called at application exit.
    """
    for h in _handlers.keys():
        h.flush()
        h.close()

if __name__ == "__main__":
    print __doc__

#!/usr/bin/env python

import os
from scipy_distutils.misc_util import default_config_dict

def configuration(parent_package='',parent_path=None):
    package = 'scipy_test'
    config = default_config_dict(package,parent_package)
    return config

if __name__ == '__main__':
    from scipy_test_version import scipy_test_version
    print 'scipy_test Version',scipy_test_version
    from scipy_distutils.core import setup
    setup(version = scipy_test_version,
          maintainer = "SciPy Developers",
          maintainer_email = "scipy-dev@scipy.org",
          description = "SciPy test module",
          url = "http://www.scipy.org",
          license = "SciPy License (BSD Style)",
          **configuration()
          )

standalone = 1


from scipy_test_version import scipy_test_version as __version__

""" Auto test tools for SciPy

    Do not run this as root!  If you enter something
    like /usr as your test directory, it'll delete
    /usr/bin, usr/lib, etc.  So don't do it!!!
    
    
    Author: Eric Jones (eric@enthought.com)
"""
from distutils import file_util
from distutils import dir_util
from distutils.errors import DistutilsFileError
#import tarfile
import sys, os, stat, time
import gzip
import tempfile, cStringIO
import urllib
import logging

if sys.platform == 'cygwin':
    local_repository = "/cygdrive/i/tarballs"
elif sys.platform == 'win32':    
    local_repository = "i:\tarballs"
else:
    local_repository = "/home/shared/tarballs"

local_mail_server = "enthought.com"

python_ftp_url = "ftp://ftp.python.org/pub/python"
numeric_url = "http://prdownloads.sourceforge.net/numpy"
f2py_url = "http://cens.ioc.ee/projects/f2py2e/2.x"
scipy_url = "ftp://www.scipy.org/pub"
blas_url = "http://www.netlib.org/blas"
lapack_url = "http://www.netlib.org/lapack"
#atlas_url = "http://prdownloads.sourceforge.net/math-atlas"
atlas_url = "http://www.scipy.org/Members/eric"


#-----------------------------------------------------------------------------
# Generic installation class. 
# built to handle downloading/untarring/building/installing arbitrary software
#-----------------------------------------------------------------------------

class package_installation:    
    def __init__(self,version='', dst_dir = '.',
                 logger = None, python_exe='python'):
        #---------------------------------------------------------------------
        # These should be defined in sub-class before calling this
        # constructor
        #---------------------------------------------------------------------
        # 
        #self.package_url -- The name of the url where tarball can be found.
        #self.package_base_name -- The base name of the source tarball.
        #self.package_dir_name -- Top level directory of unpacked tarball
        #self.tarball_suffix -- usually tar.gz or .tgz
        #self.build_type -- 'make' or 'setup' for makefile or python setup file
        
        # Version of the software package.
        self.version = version

        # Only used by packages built with setup.py
        self.python_exe = python_exe
        
        # Directory where package is unpacked/built/installed
        self.dst_dir = os.path.abspath(dst_dir)        
        
        if not logger:
            self.logger = logging
        else:
            self.logger = logger    

        # make sure the destination exists
        make_dir(self.dst_dir,logger=self.logger)

        # Construct any derived names built from the above names.
        self.init_names()
        
    def init_names(self):            
        self.package_dir = os.path.join(self.dst_dir,self.package_dir_name)
        self.tarball = self.package_base_name + '.' + self.tarball_suffix

    def get_source(self):
        """ Grab the source tarball from a repository.
        
            Try a local repository first.  If the file isn't found,
            grab it from an ftp site.
        """
        local_found = 0
        if self.local_source_up_to_date():
            try:
                self.get_source_local()
                local_found = 1                
            except DistutilsFileError:
                pass
        
        if not local_found:
            self.get_source_ftp()
                    
    def local_source_up_to_date(self):
        """ Hook to test whether a file found in the repository is current
        """
        return 1
        
    def get_source_local(self):
        """ Grab the requested tarball from a local repository of source
            tarballs.  If it doesn't exist, an error is raised.
        """
        file = os.path.join(local_repository,self.tarball)        
        dst_file = os.path.join(self.dst_dir,self.tarball)
        self.logger.info("Searching local repository for %s" % file)
        try:
            copy_file(file,dst_file,self.logger)
        except DistutilsFileError, msg:
            self.logger.info("Not found:",msg)
            raise
        
    def get_source_ftp(self):
        """ Grab requested tarball from a ftp site specified as a url.           
        """
        url = '/'.join([self.package_url,self.tarball])
     
        self.logger.info('Opening: %s' % url)
        f = urllib.urlopen(url)
        self.logger.info('Downloading: this may take a while')
        contents = f.read(-1)
        f.close()
        self.logger.info('Finished download (size=%d)' % len(contents))
     
        output_file = os.path.join(self.dst_dir,self.tarball)
        write_file(output_file,contents,self.logger)

        # Put file in local repository so we don't have to download it again.
        self.logger.info("Caching file in repository" )
        src_file = output_file
        repos_file = os.path.join(local_repository,self.tarball)        
        copy_file(src_file,repos_file,self.logger)

    def unpack_source(self,sub_dir = None):
        """ equivalent to 'tar -xzvf file' in the given sub_dir
        """       
        tarfile = os.path.join(self.dst_dir,self.tarball)
        old_dir = None
        
        # copy and move into sub directory if it is specified.
        if sub_dir:
            dst_dir = os.path.join(self.dst_dir,sub_dir)
            dst_file = os.path.join(dst_dir,self.tarball)
            copy_file(tarfile,dst_file)
            change_dir(dst_dir,self.logger)
        try:
            try:
                # occasionally the tarball is not zipped, try this first.
                untar_file(self.tarball,self.dst_dir,
                           self.logger,silent_failure=1)
            except:
                # otherwise, handle the fact that it is zipped        
                dst = os.path.join(self.dst_dir,'tmp.tar')        
                decompress_file(tarfile,dst,self.logger)                
                untar_file(dst,self.dst_dir,self.logger)
                remove_file(dst,self.logger)
        finally:
            if old_dir:
                unchange_dir(self.logger)

    #def auto_configure(self):
    #    cmd = os.path.join('.','configure')
    #    try:
    #        text = run_command(cmd,self.package_dir,self.logger,log_output=0)
    #    except ValueError, e:
    #        status, text = e
    #        self.logger.exception('Configuration Error:\n'+text)
    def auto_configure(self):
        cmd = os.path.join('.','configure')
        text = run_command(cmd,self.package_dir,self.logger)
        
    def build_with_make(self):
        cmd = 'make'
        text = run_command(cmd,self.package_dir,self.logger)
        
    def install_with_make(self, prefix = None):
        if prefix is None:
            prefix = os.path.abspath(self.dst_dir)
        cmd = 'make install prefix=%s' % prefix
        text = run_command(cmd,self.package_dir,self.logger)
        
    def python_setup(self):
        cmd = self.python_exe + ' setup.py install'
        text = run_command(cmd,self.package_dir,self.logger)
        
    def _make(self,**kw):
        """ This generally needs to be overrridden in the derived class,
            but this will suffice for the standard configure/make process.            
        """
        self.logger.info("### Begin Configure: %s" % self.package_base_name)
        self.auto_configure()
        self.logger.info("### Finished Configure: %s" % self.package_base_name)
        self.logger.info("### Begin Build: %s" % self.package_base_name)
        self.build_with_make()
        self.logger.info("### Finished Build: %s" % self.package_base_name)
        self.logger.info("### Begin Install: %s" % self.package_base_name)
        self.install_with_make()
        self.logger.info("### Finished Install: %s" % self.package_base_name)

    def install(self):
        self.logger.info('####### Building:    %s' % self.package_base_name)
        self.logger.info('        Version:     %s' % self.version)
        self.logger.info('        Url:         %s' % self.package_url)
        self.logger.info('        Install dir: %s' % self.dst_dir)
        self.logger.info('        Package dir: %s' % self.package_dir)
        self.logger.info('        Suffix:      %s' % self.tarball_suffix)
        self.logger.info('        Build type:  %s' % self.build_type)

        self.logger.info("### Begin Get Source: %s" % self.package_base_name)
        self.get_source()
        self.unpack_source()
        self.logger.info("### Finished Get Source: %s" % self.package_base_name)

        if self.build_type == 'setup':
            self.python_setup()
        else:    
            self._make()
        self.logger.info('####### Finished Building: %s' % self.package_base_name)            
            
#-----------------------------------------------------------------------------
# Installation class for Python itself.
#-----------------------------------------------------------------------------
        
class python_installation(package_installation):
    
    def __init__(self,version='', dst_dir = '.',logger=None,python_exe='python'):
        
        # Specialization for Python.        
        self.package_base_name = 'Python-'+version
        self.package_dir_name = self.package_base_name
        self.package_url = '/'.join([python_ftp_url,version])
        self.tarball_suffix = 'tgz'
        self.build_type = 'make'
        
        package_installation.__init__(self,version,dst_dir,logger,python_exe)

    def write_install_config(self):    
        """ Make doesn't seem to install scripts in the correct places.
        
            Writing this to the python directory will solve the problem.
            [install_script]
            install-dir=<directory_name> 
        """
        self.logger.info('### Writing Install Script Hack')
        text = "[install_scripts]\n"\
               "install-dir='%s'" % os.path.join(self.dst_dir,'bin')
        file = os.path.join(self.package_dir,'setup.cfg')               
        write_file(file,text,self.logger,mode='w')
        self.logger.info('### Finished writing Install Script Hack')

    def install_with_make(self):
        """ Scripts were failing to install correctly, so a setuo.cfg
            file is written to force installation in the correct place.
        """        
        self.write_install_config()
        package_installation.install_with_make(self)

    def get_exe_name(self):
        pyname = os.path.join('.','python')
        cmd = pyname + """ -c "import sys;print '%d.%d' % sys.version_info[:2]" """
        text = run_command(cmd,self.package_dir,self.logger)
        exe = os.path.join(self.dst_dir,'bin','python'+text)
        return exe

#-----------------------------------------------------------------------------
# Installation class for Blas.
#-----------------------------------------------------------------------------

class blas_installation(package_installation):
    
    def __init__(self,version='', dst_dir = '.',logger=None,python_exe='python'):
        
        # Specialization for for "slow" blas
        self.package_base_name = 'blas'
        self.package_dir_name = 'BLAS'
        self.package_url = blas_url
        self.tarball_suffix = 'tgz'
        self.build_type = 'make'
                
        self.platform = 'LINUX'
        package_installation.__init__(self,version,dst_dir,logger,python_exe)

    def unpack_source(self,subdir=None):
        """ Dag.  blas.tgz doesn't have directory information -- its
            just a tar ball of fortran source code.  untar it in the
            BLAS directory
        """
        package_installation.unpack_source(self,self.package_dir_name)
            
    def auto_configure(self):
        # nothing to do.
        pass
    def build_with_make(self, **kw):
        libname = 'blas_LINUX.a'
        cmd = 'g77 -funroll-all-loops -fno-f2c -O3 -c *.f;ar -cru %s' % libname
        text = run_command(cmd,self.package_dir,self.logger)
        
    def install_with_make(self, **kw):
        # not really using make -- we'll just copy the file over.        
        src_file = os.path.join(self.package_dir,'blas_%s.a' % self.platform)
        dst_file = os.path.join(self.dst_dir,'lib','libblas.a')
        self.logger.info("Installing blas")
        copy_file(src_file,dst_file,self.logger)
        
#-----------------------------------------------------------------------------
# Installation class for Lapack.
#-----------------------------------------------------------------------------

class lapack_installation(package_installation):
    
    def __init__(self,version='', dst_dir = '.',logger=None,python_exe='python'):
        
        # Specialization for Lapack 3.0 + updates        
        self.package_base_name = 'lapack'
        self.package_dir_name = 'LAPACK'
        self.package_url = lapack_url
        self.tarball_suffix = 'tgz'
        self.build_type = 'make'
        
        self.platform = 'LINUX'
        package_installation.__init__(self,version,dst_dir,logger,python_exe)

    def auto_configure(self):
        # perhaps this should actually override auto_conifgure
        # before make, we need to copy the appropriate setup file in.
        # should work anywhere g77 works...
        make_inc = 'make.inc.' + self.platform
        src_file = os.path.join(self.package_dir,'INSTALL',make_inc)
        dst_file = os.path.join(self.package_dir,'make.inc')
        copy_file(src_file,dst_file,self.logger)
        
    def build_with_make(self, **kw):
        cmd = 'make install lapacklib'
        text = run_command(cmd,self.package_dir,self.logger)
        
    def install_with_make(self, **kw):
        # not really using make -- we'll just copy the file over.
        src_file = os.path.join(self.package_dir,'lapack_%s.a' % self.platform)
        dst_file = os.path.join(self.dst_dir,'lib','liblapack.a')        
        copy_file(src_file,dst_file,self.logger)

#-----------------------------------------------------------------------------
# Installation class for Numeric
#-----------------------------------------------------------------------------

class numeric_installation(package_installation):
    
    def __init__(self,version='', dst_dir = '.',logger=None,python_exe='python'):
        
        self.package_base_name = 'Numeric-'+version
        self.package_dir_name = self.package_base_name
        self.package_url = numeric_url
        self.tarball_suffix = 'tar.gz'
        self.build_type = 'setup'        

        package_installation.__init__(self,version,dst_dir,logger,python_exe)


#-----------------------------------------------------------------------------
# Installation class for f2py
#-----------------------------------------------------------------------------

class f2py_installation(package_installation):
    
    def __init__(self,version='', dst_dir = '.',logger=None,python_exe='python'):
        
        # Typical file format: F2PY-2.13.175-1250.tar.gz
        self.package_base_name = 'F2PY-'+version
        self.package_dir_name = self.package_base_name
        self.package_url = f2py_url
        self.tarball_suffix = 'tar.gz'
        self.build_type = 'setup'        
                
        package_installation.__init__(self,version,dst_dir,logger,python_exe)


#-----------------------------------------------------------------------------
# Installation class for Atlas.
# This is a binary install *NOT* a source install.
# The source install is a pain to automate.
#-----------------------------------------------------------------------------

class atlas_installation(package_installation):
    
    def __init__(self,version='', dst_dir = '.',logger=None,python_exe='python'):
        
        #self.package_base_name = 'atlas' + version
        #self.package_dir_name = 'ATLAS'
        self.package_base_name = 'atlas-RH7.1-PIII'
        self.package_dir_name = 'atlas'
        self.package_url = atlas_url
        self.tarball_suffix = 'tgz'
        self.build_type = 'make'        
        
        package_installation.__init__(self,version,dst_dir,logger,python_exe)

    def auto_configure(self,**kw):
        pass
    def build_with_make(self,**kw):
        pass
    def install_with_make(self, **kw):
        # just copy the tree over.
        dst = os.path.join(self.dst_dir,'lib','atlas')
        self.logger.info("Installing Atlas")
        copy_tree(self.package_dir,dst,self.logger)

#-----------------------------------------------------------------------------
# Installation class for scipy
#-----------------------------------------------------------------------------

class scipy_installation(package_installation):
    
    def __init__(self,version='', dst_dir = '.',logger=None,python_exe='python'):
        
        self.package_base_name = 'scipy_snapshot'
        self.package_dir_name = 'scipy'
        self.package_url = scipy_url
        self.tarball_suffix = 'tgz'
        self.build_type = 'setup'
        
        package_installation.__init__(self,version,dst_dir,logger,python_exe)
                    
    def local_source_up_to_date(self):
        """ Hook to test whether a file found in the repository is current
        """
        file = os.path.join(local_repository,self.tarball)
        up_to_date = 0
        try:
            file_time = os.stat(file)[stat.ST_MTIME]        
            fyear,fmonth,fday = time.localtime(file_time)[:3]
            year,month,day = time.localtime()[:3]
            if fyear == year and fmonth == month and fday == day:
                up_to_date = 1
                self.logger.info("Repository file up to date: %s" % file)
        except OSError, msg:
            pass
        return up_to_date
                
#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------


#if os.name == 'nt':
#    def exec_command(command):
#        """ not sure how to get exit status on nt. """
#        in_pipe,out_pipe = os.popen4(command)
#        in_pipe.close()
#        text = out_pipe.read()
#        return 0, text
#else:
#    import commands
#    exec_command = commands.getstatusoutput
   
# This may not work on Win98... The above stuff was to handle these machines.
import commands
exec_command = commands.getstatusoutput

def copy_file(src,dst,logger=None):
    if not logger:
        logger = logging
    logger.info("Copying %s->%s" % (src,dst))        
    try:
        file_util.copy_file(src,dst)
    except Exception, e:     
        logger.exception("Copy Failed")        
        raise

def copy_tree(src,dst,logger=None):
    if not logger:
        logger = logging
    logger.info("Copying directory tree %s->%s" % (src,dst))        
    try:
        dir_util.copy_tree(src,dst)
    except Exception, e:     
        logger.exception("Copy Failed")        
        raise

def remove_tree(directory,logger=None):
    if not logger:
        logger = logging
    logger.info("Removing directory tree %s" % directory)        
    try:
        dir_util.remove_tree(directory)
    except Exception, e:     
        logger.exception("Remove failed: %s" % e)        
        raise

def remove_file(file,logger=None):
    if not logger:
        logger = logging
    logger.info("Remove file %s" % file)        
    try:
        os.remove(file)
    except Exception, e:     
        logger.exception("Remove failed")        
        raise

def write_file(file,contents,logger=None,mode='wb'):
    if not logger:
        logger = logging
    logger.info('Write file: %s' % file)
    try:
        new_file = open(file,mode)
        new_file.write(contents)
        new_file.close()
    except Exception, e:     
        logger.exception("Write failed")        
        raise

def make_dir(name,logger=None):
    if not logger:
        logger = logging
    logger.info('Make directory: %s' % name)
    try:        
        dir_util.mkpath(os.path.abspath(name))
    except Exception, e:     
        logger.exception("Make Directory failed")        
        raise

# I know, I know...
old_dir = []

def change_dir(d, logger = None):
    if not logger:
        logger = logging
    global old_dir 
    cwd = os.getcwd()   
    old_dir.append(cwd)
    d = os.path.abspath(d)
    if d != old_dir[-1]:
        logger.info("Change directory: %s" % d)            
        try:
            os.chdir(d)
        except Exception, e:     
            logger.exception("Change directory failed")
            raise        
        #if d == '.':
        #    import sys,traceback
        #    f = sys._getframe()
        #    traceback.print_stack(f)

def unchange_dir(logger=None):
    if not logger:
        logger = logging            
    global old_dir
    try:
        cwd = os.getcwd()
        d = old_dir.pop(-1)            
        try:
            if d != cwd:
                logger.info("Change directory : %s" % d)
                os.chdir(d)
        except Exception, e:     
            logger.exception("Change directory failed")
            raise                    
    except IndexError:
        logger.exception("Change directory failed")
        
def decompress_file(src,dst,logger = None):
    if not logger:
        logger = logging
    logger.info("Upacking %s->%s" % (src,dst))
    try:
        f = gzip.open(src,'rb')
        contents = f.read(-1)
        f = open(dst, 'wb')
        f.write(contents)
    except Exception, e:     
        logger.exception("Unpack failed")
        raise        

    
def untar_file(file,dst_dir='.',logger = None,silent_failure = 0):    
    if not logger:
        logger = logging
    logger.info("Untarring file: %s" % (file))
    try:
        run_command('tar -xf ' + file,directory = dst_dir,
                    logger=logger, silent_failure = silent_failure)
    except Exception, e:
        if not silent_failure:     
            logger.exception("Untar failed")
        raise        

def unpack_file(file,logger = None):
    """ equivalent to 'tar -xzvf file'
    """
    dst = 'tmp.tar'
    decompress_file(file,dst,logger)                
    untar_file(dst.logger)
    remove_file(dst,logger)        


def run_command(cmd,directory='.',logger=None,silent_failure = 0):
    if not logger:
        logger = logging
    change_dir(directory,logger)    
    try:        
        msg = 'Running: %s' % cmd
        logger.info(msg)    
        status,text = exec_command(cmd)
        if status and silent_failure:
            msg = '(failed silently)'
            logger.info(msg)    
        if status and text and not silent_failure:
            logger.error('Command Failed (status=%d)\n'% status +text)
    finally:
        unchange_dir(logger)
    if status:
        raise ValueError, (status,text)
    return text            

def mail_report(from_addr,to_addr,subject,mail_server,
                build_log, test_results,info):
    
    msg = ''
    msg = msg + 'To: %s\n'   % to_addr
    msg = msg + 'Subject: %s\n' % subject
    msg = msg + '\r\n\r\n'

    for k,v in info.items():   
        msg = msg + '%s: %s\n' % (k,v)
    msg = msg + test_results + '\n'
    msg = msg + '-----------------------------\n' 
    msg = msg + '--------  BUILD LOG   -------\n' 
    msg = msg + '-----------------------------\n' 
    msg = msg + build_log
    print msg
    
    # mail results
    import smtplib 
    server = smtplib.SMTP(mail_server)    
    server.sendmail(from_addr, to_addr, msg)
    server.quit()
    

def full_scipy_build(build_dir = '.',
                     test_level = 10,
                     python_version  = '2.2.1',
                     numeric_version = '21.0',
                     f2py_version    = '2.13.175-1250',
                     atlas_version   = '3.3.14',
                     scipy_version   = 'snapshot'):
    
    # for now the atlas version is ignored.  Only the 
    # binaries for RH are supported at the moment.

    build_info = {'python_version' : python_version,
                  'test_level'     : test_level,
                  'numeric_version': numeric_version,
                  'f2py_version'   : f2py_version,
                  'atlas_version'  : atlas_version,
                  'scipy_version'  : scipy_version}
                    
    dst_dir = os.path.join(build_dir,sys.platform)

    logger = logging.Logger("SciPy Test")
    fmt = logging.Formatter(logging.BASIC_FORMAT)
    log_stream = cStringIO.StringIO()
    stream_handler = logging.StreamHandler(log_stream)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)
    # also write to stderr
    stderr = logging.StreamHandler()
    stderr.setFormatter(fmt)
    logger.addHandler(stderr)

    try:
        try:    
        
            # before doing anything, we need to wipe the 
            # /bin, /lib, /man, and /include directories
            # in dst_dir.  Don't run as root.            
            make_dir(dst_dir,logger=logger)            
            change_dir(dst_dir   , logger)
            for d in ['bin','lib','man','include']:
                try:            remove_tree(d, logger)
                except OSError: pass                
            unchange_dir(logger)
            
            python = python_installation(version=python_version,
                                         logger = logger,
                                         dst_dir = dst_dir)
            python.install()
            
            python_name = python.get_exe_name()
        
            numeric = numeric_installation(version=numeric_version,
                                           dst_dir = dst_dir,
                                           logger = logger,
                                           python_exe=python_name)
            numeric.install()
            
            f2py =  f2py_installation(version=f2py_version,
                                      logger = logger,
                                      dst_dir = dst_dir,
                                      python_exe=python_name)
            f2py.install()                                
        
            # download files don't have a version specified    
            #lapack =  lapack_installation(version='',
            #                              dst_dir = dst_dir
            #                              python_exe=python_name)
            #lapack.install()                                
        
            # download files don't have a version specified    
            #blas =  blas_installation(version='',
            #                          logger = logger,
            #                          dst_dir = dst_dir,
            #                          python_exe=python_name)
            #blas.install()                                
            
            # ATLAS
            atlas =  atlas_installation(version=atlas_version,
                                        logger = logger,
                                        dst_dir = dst_dir,
                                        python_exe=python_name)
            atlas.install()
            
            # version not currently used -- need to fix this.
            scipy =  scipy_installation(version=scipy_version,
                                        logger = logger,
                                        dst_dir = dst_dir,
                                        python_exe=python_name)
            scipy.install()                                
        
            # The change to tmp makes sure there isn't a scipy directory in 
            # the local scope.
            # All tests are run.
            logger.info('Beginning Test')
            cmd = python_name +' -c "import sys,scipy;suite=scipy.test(%d);"'\
                                % test_level
            test_results = run_command(cmd, logger=logger,
                                       directory = tempfile.gettempdir())
            build_info['results'] = 'test completed (check below for pass/fail)'
        except Exception, msg:
            test_results = ''
            build_info['results'] = 'build failed: %s' % msg
            logger.exception('Build failed')
    finally:    
        to_addr = "scipy-testlog@scipy.org"
        from_addr = "scipy-test@enthought.com"
        subject = '%s,py%s,num%s,scipy%s' % (sys.platform,python_version,
                                            numeric_version,scipy_version) 
        build_log = log_stream.getvalue()
        mail_report(from_addr,to_addr,subject,local_mail_server,
                    build_log,test_results,build_info)

if __name__ == '__main__':
    build_dir = '/tmp/scipy_test'
    level = 10

    full_scipy_build(build_dir = build_dir,
                     test_level = level,
                     python_version  = '2.2.1',
                     numeric_version = '21.0',
                     f2py_version    = '2.13.175-1250',
                     atlas_version   = '3.3.14',
                     scipy_version   = 'snapshot')

    # an older python
    full_scipy_build(build_dir = build_dir,
                     test_level = level,
                     python_version  = '2.1.3',
                     numeric_version = '21.0',
                     f2py_version    = '2.13.175-1250',
                     atlas_version   = '3.3.14',
                     scipy_version   = 'snapshot')

    # an older numeric
    full_scipy_build(build_dir = build_dir,
                     test_level = level,
                     python_version  = '2.1.3',
                     numeric_version = '20.3',
                     f2py_version    = '2.13.175-1250',
                     atlas_version   = '3.3.14',
                     scipy_version   = 'snapshot')

    # This fails because multiarray doesn't have 
    # arange defined.
    """
    full_scipy_build(build_dir = build_dir,
                     test_level = level,
                     python_version  = '2.1.3',
                     numeric_version = '20.0.0',
                     f2py_version    = '2.13.175-1250',
                     atlas_version   = '3.3.14',
                     scipy_version   = 'snapshot')

    full_scipy_build(build_dir = build_dir,
                     test_level = level,
                     python_version  = '2.1.3',
                     numeric_version = '19.0.0',
                     f2py_version    = '2.13.175-1250',
                     atlas_version   = '3.3.14',
                     scipy_version   = 'snapshot')

    full_scipy_build(build_dir = build_dir,
                     test_level = level,
                     python_version  = '2.1.3',
                     numeric_version = '18.4.1',
                     f2py_version    = '2.13.175-1250',
                     atlas_version   = '3.3.14',
                     scipy_version   = 'snapshot')
    """

major = 0
minor = 3
micro = 1
#release_level = 'alpha'
release_level = ''
try:
    from __cvs_version__ import cvs_version
    cvs_minor = cvs_version[-3]
    cvs_serial = cvs_version[-1]
except ImportError,msg:
    print msg
    cvs_minor = 0
    cvs_serial = 0

if release_level:
    scipy_test_version = '%(major)d.%(minor)d.%(micro)d_%(release_level)s'\
                              '_%(cvs_minor)d.%(cvs_serial)d' % (locals ())
else:
    scipy_test_version = '%(major)d.%(minor)d.%(micro)d'\
                              '_%(cvs_minor)d.%(cvs_serial)d' % (locals ())

"""
unixccompiler - can handle very long argument lists for ar.
"""

import os
import sys
import new

from distutils.errors import DistutilsExecError, LinkError, CompileError
from distutils.unixccompiler import *


import log

# Note that UnixCCompiler._compile appeared in Python 2.3
def UnixCCompiler__compile(self, obj, src, ext, cc_args, extra_postargs, pp_opts):
    display = '%s: %s' % (os.path.basename(self.compiler_so[0]),src)
    try:
        self.spawn(self.compiler_so + cc_args + [src, '-o', obj] +
                   extra_postargs, display = display)
    except DistutilsExecError, msg:
        raise CompileError, msg
UnixCCompiler._compile = new.instancemethod(UnixCCompiler__compile,
                                            None,
                                            UnixCCompiler)


def UnixCCompile_create_static_lib(self, objects, output_libname,
                                   output_dir=None, debug=0, target_lang=None):
    objects, output_dir = self._fix_object_args(objects, output_dir)

    output_filename = \
                    self.library_filename(output_libname, output_dir=output_dir)
        
    if self._need_link(objects, output_filename):
        self.mkpath(os.path.dirname(output_filename))
        tmp_objects = objects + self.objects
        while tmp_objects:
            objects = tmp_objects[:50]
            tmp_objects = tmp_objects[50:]
            display = '%s: adding %d object files to %s' % (os.path.basename(self.archiver[0]),
                                               len(objects),output_filename)
            self.spawn(self.archiver + [output_filename] + objects,
                       display = display)

        # Not many Unices required ranlib anymore -- SunOS 4.x is, I
        # think the only major Unix that does.  Maybe we need some
        # platform intelligence here to skip ranlib if it's not
        # needed -- or maybe Python's configure script took care of
        # it for us, hence the check for leading colon.
        if self.ranlib:
            display = '%s:@ %s' % (os.path.basename(self.ranlib[0]),
                                   output_filename)
            try:
                self.spawn(self.ranlib + [output_filename],
                           display = display)
            except DistutilsExecError, msg:
                raise LibError, msg
    else:
        log.debug("skipping %s (up-to-date)", output_filename)
    return

UnixCCompiler.create_static_lib = \
  new.instancemethod(UnixCCompile_create_static_lib,
                     None,UnixCCompiler)

#!/usr/bin/env python
"""
cpuinfo

Copyright 2002 Pearu Peterson all rights reserved,
Pearu Peterson <pearu@cens.ioc.ee>          
Permission to use, modify, and distribute this software is given under the 
terms of the SciPy (BSD style) license.  See LICENSE.txt that came with
this distribution for specifics.

Note:  This should be merged into proc at some point.  Perhaps proc should
be returning classes like this instead of using dictionaries.

NO WARRANTY IS EXPRESSED OR IMPLIED.  USE AT YOUR OWN RISK.
$Revision$
$Date$
Pearu Peterson
"""

__version__ = "$Id$"

__all__ = ['cpu']

import sys,string,re,types

class cpuinfo_base:
    """Holds CPU information and provides methods for requiring
    the availability of various CPU features.
    """

    def _try_call(self,func):
        try:
            return func()
        except:
            pass

    def __getattr__(self,name):
        if name[0]!='_':
            if hasattr(self,'_'+name):
                attr = getattr(self,'_'+name)
                if type(attr) is types.MethodType:
                    return lambda func=self._try_call,attr=attr : func(attr)
            else:
                return lambda : None
        raise AttributeError,name    

    def _getNCPUs(self):
        return 1

class linux_cpuinfo(cpuinfo_base):

    info = None
    
    def __init__(self):
        if self.info is not None:
            return
        info = []
        try:
            for line in open('/proc/cpuinfo').readlines():
                name_value = map(string.strip,string.split(line,':',1))
                if len(name_value)!=2:
                    continue
                name,value = name_value
                if not info or info[-1].has_key(name): # next processor
                    info.append({})
                info[-1][name] = value
        except:
            print sys.exc_value,'(ignoring)'
        self.__class__.info = info

    def _not_impl(self): pass

    # Athlon

    def _is_AMD(self):
        return self.info[0]['vendor_id']=='AuthenticAMD'

    def _is_AthlonK6_2(self):
        return self._is_AMD() and self.info[0]['model'] == '2'

    def _is_AthlonK6_3(self):
        return self._is_AMD() and self.info[0]['model'] == '3'

    def _is_AthlonK6(self):
        return re.match(r'.*?AMD-K6',self.info[0]['model name']) is not None

    def _is_AthlonK7(self):
        return re.match(r'.*?AMD-K7',self.info[0]['model name']) is not None

    def _is_AthlonMP(self):
        return re.match(r'.*?Athlon\(tm\) MP\b',
                        self.info[0]['model name']) is not None

    def _is_AthlonHX(self):
        return re.match(r'.*?Athlon HX\b',
                        self.info[0]['model name']) is not None

    def _is_Opteron(self):
        return re.match(r'.*?Opteron\b',
                        self.info[0]['model name']) is not None

    def _is_Hammer(self):
        return re.match(r'.*?Hammer\b',
                        self.info[0]['model name']) is not None

    # Alpha

    def _is_Alpha(self):
        return self.info[0]['cpu']=='Alpha'

    def _is_EV4(self):
        return self.is_Alpha() and self.info[0]['cpu model'] == 'EV4'

    def _is_EV5(self):
        return self.is_Alpha() and self.info[0]['cpu model'] == 'EV5'

    def _is_EV56(self):
        return self.is_Alpha() and self.info[0]['cpu model'] == 'EV56'

    def _is_PCA56(self):
        return self.is_Alpha() and self.info[0]['cpu model'] == 'PCA56'

    # Intel

    #XXX
    _is_i386 = _not_impl

    def _is_Intel(self):
        return self.info[0]['vendor_id']=='GenuineIntel'

    def _is_i486(self):
        return self.info[0]['cpu']=='i486'

    def _is_i586(self):
        return self.is_Intel() and self.info[0]['cpu family'] == '5'

    def _is_i686(self):
        return self.is_Intel() and self.info[0]['cpu family'] == '6'

    def _is_Celeron(self):
        return re.match(r'.*?Celeron',
                        self.info[0]['model name']) is not None

    def _is_Pentium(self):
        return re.match(r'.*?Pentium',
                        self.info[0]['model name']) is not None

    def _is_PentiumII(self):
        return re.match(r'.*?Pentium.*?II\b',
                        self.info[0]['model name']) is not None

    def _is_PentiumPro(self):
        return re.match(r'.*?PentiumPro\b',
                        self.info[0]['model name']) is not None

    def _is_PentiumMMX(self):
        return re.match(r'.*?Pentium.*?MMX\b',
                        self.info[0]['model name']) is not None

    def _is_PentiumIII(self):
        return re.match(r'.*?Pentium.*?III\b',
                        self.info[0]['model name']) is not None

    def _is_PentiumIV(self):
        return re.match(r'.*?Pentium.*?(IV|4)\b',
                        self.info[0]['model name']) is not None

    def _is_Itanium(self):
        return re.match(r'.*?Itanium\b',
                        self.info[0]['model name']) is not None



    # Varia

    def _is_singleCPU(self):
        return len(self.info) == 1

    def _getNCPUs(self):
        return len(self.info)

    def _has_fdiv_bug(self):
        return self.info[0]['fdiv_bug']=='yes'

    def _has_f00f_bug(self):
        return self.info[0]['f00f_bug']=='yes'

    def _has_mmx(self):
        return re.match(r'.*?\bmmx\b',self.info[0]['flags']) is not None

    def _has_sse(self):
        return re.match(r'.*?\bsse\b',self.info[0]['flags']) is not None

    def _has_sse2(self):
        return re.match(r'.*?\bsse2\b',self.info[0]['flags']) is not None

    def _has_3dnow(self):
        return re.match(r'.*?\b3dnow\b',self.info[0]['flags']) is not None

    def _has_3dnowext(self):
        return re.match(r'.*?\b3dnowext\b',self.info[0]['flags']) is not None

class irix_cpuinfo(cpuinfo_base):

    info = None
    
    def __init__(self):
        if self.info is not None:
            return
        info = []
        try:
            import commands
            status,output = commands.getstatusoutput('sysconf')
            if status not in [0,256]:
                return
            for line in output.split('\n'):
                name_value = map(string.strip,string.split(line,' ',1))
                if len(name_value)!=2:
                    continue
                name,value = name_value
                if not info:
                    info.append({})
                info[-1][name] = value
        except:
            print sys.exc_value,'(ignoring)'
        self.__class__.info = info

        #print info
    def _not_impl(self): pass

    def _is_singleCPU(self):
        return self.info[0].get('NUM_PROCESSORS') == '1'

    def _getNCPUs(self):
        return int(self.info[0].get('NUM_PROCESSORS'))

    def __cputype(self,n):
        return self.info[0].get('PROCESSORS').split()[0].lower() == 'r%s' % (n)
    def _is_r2000(self): return self.__cputype(2000)
    def _is_r3000(self): return self.__cputype(3000)
    def _is_r3900(self): return self.__cputype(3900)
    def _is_r4000(self): return self.__cputype(4000)
    def _is_r4100(self): return self.__cputype(4100)
    def _is_r4300(self): return self.__cputype(4300)
    def _is_r4400(self): return self.__cputype(4400)
    def _is_r4600(self): return self.__cputype(4600)
    def _is_r4650(self): return self.__cputype(4650)
    def _is_r5000(self): return self.__cputype(5000)
    def _is_r6000(self): return self.__cputype(6000)
    def _is_r8000(self): return self.__cputype(8000)
    def _is_r10000(self): return self.__cputype(10000)
    def _is_r12000(self): return self.__cputype(12000)
    def _is_rorion(self): return self.__cputype('orion')

    def get_ip(self):
        try: return self.info[0].get('MACHINE')
        except: pass
    def __machine(self,n):
        return self.info[0].get('MACHINE').lower() == 'ip%s' % (n)
    def _is_IP19(self): return self.__machine(19)
    def _is_IP20(self): return self.__machine(20)
    def _is_IP21(self): return self.__machine(21)
    def _is_IP22(self): return self.__machine(22)
    def _is_IP22_4k(self): return self.__machine(22) and self._is_r4000()
    def _is_IP22_5k(self): return self.__machine(22)  and self._is_r5000()
    def _is_IP24(self): return self.__machine(24)
    def _is_IP25(self): return self.__machine(25)
    def _is_IP26(self): return self.__machine(26)
    def _is_IP27(self): return self.__machine(27)
    def _is_IP28(self): return self.__machine(28)
    def _is_IP30(self): return self.__machine(30)
    def _is_IP32(self): return self.__machine(32)
    def _is_IP32_5k(self): return self.__machine(32) and self._is_r5000()
    def _is_IP32_10k(self): return self.__machine(32) and self._is_r10000()

class darwin_cpuinfo(cpuinfo_base):

    info = None
    
    def __init__(self):
        if self.info is not None:
            return
        info = []
        try:
            import commands
            status,output = commands.getstatusoutput('arch')
            if not status:
                if not info: info.append({})
                info[-1]['arch'] = string.strip(output)
            status,output = commands.getstatusoutput('machine')
            if not status:
                if not info: info.append({})
                info[-1]['machine'] = string.strip(output)
            status,output = commands.getstatusoutput('sysctl hw')
            if not status:
                if not info: info.append({})
                d = {}
                for l in string.split(output,'\n'):
                    l = map(string.strip,string.split(l, '='))
                    if len(l)==2:
                        d[l[0]]=l[1]
                info[-1]['sysctl_hw'] = d
        except:
            print sys.exc_value,'(ignoring)'
        self.__class__.info = info

    def _not_impl(self): pass

    def _getNCPUs(self):
        try: return int(self.info[0]['sysctl_hw']['hw.ncpu'])
        except: return 1

    def _is_Power_Macintosh(self):
        return self.info[0]['sysctl_hw']['hw.machine']=='Power Macintosh'

    def _is_i386(self):
        return self.info[0]['arch']=='i386'
    def _is_ppc(self):
        return self.info[0]['arch']=='ppc'

    def __machine(self,n):
        return self.info[0]['machine'] == 'ppc%s'%n
    def _is_ppc601(self): return self.__machine(601)
    def _is_ppc602(self): return self.__machine(602)
    def _is_ppc603(self): return self.__machine(603)
    def _is_ppc603e(self): return self.__machine('603e')
    def _is_ppc604(self): return self.__machine(604)
    def _is_ppc604e(self): return self.__machine('604e')
    def _is_ppc620(self): return self.__machine(620)
    def _is_ppc630(self): return self.__machine(630)
    def _is_ppc740(self): return self.__machine(740)
    def _is_ppc7400(self): return self.__machine(7400)
    def _is_ppc7450(self): return self.__machine(7450)
    def _is_ppc750(self): return self.__machine(750)
    def _is_ppc403(self): return self.__machine(403)
    def _is_ppc505(self): return self.__machine(505)
    def _is_ppc801(self): return self.__machine(801)
    def _is_ppc821(self): return self.__machine(821)
    def _is_ppc823(self): return self.__machine(823)
    def _is_ppc860(self): return self.__machine(860)

class sunos_cpuinfo(cpuinfo_base):

    info = None
    
    def __init__(self):
        if self.info is not None:
            return
        info = []
        try:
            import commands
            status,output = commands.getstatusoutput('arch')
            if not status:
                if not info: info.append({})
                info[-1]['arch'] = string.strip(output)
            status,output = commands.getstatusoutput('mach')
            if not status:
                if not info: info.append({})
                info[-1]['mach'] = string.strip(output)
            status,output = commands.getstatusoutput('uname -i')
            if not status:
                if not info: info.append({})
                info[-1]['uname_i'] = string.strip(output)
            status,output = commands.getstatusoutput('uname -X')
            if not status:
                if not info: info.append({})
                d = {}
                for l in string.split(output,'\n'):
                    l = map(string.strip,string.split(l, '='))
                    if len(l)==2:
                        d[l[0]]=l[1]
                info[-1]['uname_X'] = d
            status,output = commands.getstatusoutput('isainfo -b')
            if not status:
                if not info: info.append({})
                info[-1]['isainfo_b'] = string.strip(output)
            status,output = commands.getstatusoutput('isainfo -n')
            if not status:
                if not info: info.append({})
                info[-1]['isainfo_n'] = string.strip(output)
            status,output = commands.getstatusoutput('psrinfo -v 0')
            if not status:
                if not info: info.append({})
                for l in string.split(output,'\n'):
                    m = re.match(r'\s*The (?P<p>[\w\d]+) processor operates at',l)
                    if m:
                        info[-1]['processor'] = m.group('p')
                        break
        except:
            print sys.exc_value,'(ignoring)'
        self.__class__.info = info

    def _not_impl(self): pass

    def _is_32bit(self):
        return self.info[0]['isainfo_b']=='32'
    def _is_64bit(self):
        return self.info[0]['isainfo_b']=='64'

    def _is_i386(self):
        return self.info[0]['isainfo_n']=='i386'
    def _is_sparc(self):
        return self.info[0]['isainfo_n']=='sparc'
    def _is_sparcv9(self):
        return self.info[0]['isainfo_n']=='sparcv9'

    def _getNCPUs(self):
        try: return int(self.info[0]['uname_X']['NumCPU'])
        except: return 1

    def _is_sun4(self):
        return self.info[0]['arch']=='sun4'

    def _is_SUNW(self):
        return re.match(r'SUNW',self.info[0]['uname_i']) is not None
    def _is_sparcstation5(self):
        return re.match(r'.*SPARCstation-5',self.info[0]['uname_i']) is not None
    def _is_ultra1(self):
        return re.match(r'.*Ultra-1',self.info[0]['uname_i']) is not None
    def _is_ultra250(self):
        return re.match(r'.*Ultra-250',self.info[0]['uname_i']) is not None
    def _is_ultra2(self):
        return re.match(r'.*Ultra-2',self.info[0]['uname_i']) is not None
    def _is_ultra30(self):
        return re.match(r'.*Ultra-30',self.info[0]['uname_i']) is not None
    def _is_ultra4(self):
        return re.match(r'.*Ultra-4',self.info[0]['uname_i']) is not None
    def _is_ultra5_10(self):
        return re.match(r'.*Ultra-5_10',self.info[0]['uname_i']) is not None
    def _is_ultra5(self):
        return re.match(r'.*Ultra-5',self.info[0]['uname_i']) is not None
    def _is_ultra60(self):
        return re.match(r'.*Ultra-60',self.info[0]['uname_i']) is not None
    def _is_ultra80(self):
        return re.match(r'.*Ultra-80',self.info[0]['uname_i']) is not None
    def _is_ultraenterprice(self):
        return re.match(r'.*Ultra-Enterprise',self.info[0]['uname_i']) is not None
    def _is_ultraenterprice10k(self):
        return re.match(r'.*Ultra-Enterprise-10000',self.info[0]['uname_i']) is not None
    def _is_sunfire(self):
        return re.match(r'.*Sun-Fire',self.info[0]['uname_i']) is not None
    def _is_ultra(self):
        return re.match(r'.*Ultra',self.info[0]['uname_i']) is not None

    def _is_cpusparcv7(self):
        return self.info[0]['processor']=='sparcv7'
    def _is_cpusparcv8(self):
        return self.info[0]['processor']=='sparcv8'
    def _is_cpusparcv9(self):
        return self.info[0]['processor']=='sparcv9'

class win32_cpuinfo(cpuinfo_base):

    info = None
    pkey = "HARDWARE\\DESCRIPTION\\System\\CentralProcessor"
    # XXX: what does the value of
    #   HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System\CentralProcessor\0
    # mean?

    def __init__(self):
        if self.info is not None:
            return
        info = []
        try:
            #XXX: Bad style to use so long `try:...except:...`. Fix it!
            import _winreg
            pkey = "HARDWARE\\DESCRIPTION\\System\\CentralProcessor"
            prgx = re.compile(r"family\s+(?P<FML>\d+)\s+model\s+(?P<MDL>\d+)"\
                              "\s+stepping\s+(?P<STP>\d+)",re.IGNORECASE)
            chnd=_winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,pkey)
            pnum=0
            while 1:
                try:
                    proc=_winreg.EnumKey(chnd,pnum)
                except _winreg.error:
                    break
                else:
                    pnum+=1
                    print proc
                    info.append({"Processor":proc})
                    phnd=_winreg.OpenKey(chnd,proc)
                    pidx=0
                    while True:
                        try:
                            name,value,vtpe=_winreg.EnumValue(phnd,pidx)
                        except _winreg.error:
                            break
                        else:
                            pidx=pidx+1
                            info[-1][name]=value
                            if name=="Identifier":
                                srch=prgx.search(value)
                                if srch:
                                    info[-1]["Family"]=int(srch.group("FML"))
                                    info[-1]["Model"]=int(srch.group("MDL"))
                                    info[-1]["Stepping"]=int(srch.group("STP"))
        except:
            print sys.exc_value,'(ignoring)'
        self.__class__.info = info

    def _not_impl(self): pass

    # Athlon

    def _is_AMD(self):
        return self.info[0]['VendorIdentifier']=='AuthenticAMD'

    def _is_Am486(self):
        return self.is_AMD() and self.info[0]['Family']==4

    def _is_Am5x86(self):
        return self.is_AMD() and self.info[0]['Family']==4

    def _is_AMDK5(self):
        return self.is_AMD() and self.info[0]['Family']==5 \
               and self.info[0]['Model'] in [0,1,2,3]

    def _is_AMDK6(self):
        return self.is_AMD() and self.info[0]['Family']==5 \
               and self.info[0]['Model'] in [6,7]

    def _is_AMDK6_2(self):
        return self.is_AMD() and self.info[0]['Family']==5 \
               and self.info[0]['Model']==8

    def _is_AMDK6_3(self):
        return self.is_AMD() and self.info[0]['Family']==5 \
               and self.info[0]['Model']==9

    def _is_Athlon(self):
        return self.is_AMD() and self.info[0]['Family']==6

    def _is_Athlon64(self):
        return self.is_AMD() and self.info[0]['Family']==15 \
               and self.info[0]['Model']==4

    def _is_Opteron(self):
        return self.is_AMD() and self.info[0]['Family']==15 \
               and self.info[0]['Model']==5

    # Intel

    def _is_Intel(self):
        return self.info[0]['VendorIdentifier']=='GenuineIntel'

    def _is_i386(self):
        return self.info[0]['Family']==3

    def _is_i486(self):
        return self.info[0]['Family']==4

    def _is_i586(self):
        return self.is_Intel() and self.info[0]['Family']==5

    def _is_i686(self):
        return self.is_Intel() and self.info[0]['Family']==6

    def _is_Pentium(self):
        return self.is_Intel() and self.info[0]['Family']==5

    def _is_PentiumMMX(self):
        return self.is_Intel() and self.info[0]['Family']==5 \
               and self.info[0]['Model']==4

    def _is_PentiumPro(self):
        return self.is_Intel() and self.info[0]['Family']==6 \
               and self.info[0]['Model']==1

    def _is_PentiumII(self):
        return self.is_Intel() and self.info[0]['Family']==6 \
               and self.info[0]['Model'] in [3,5,6]

    def _is_PentiumIII(self):
        return self.is_Intel() and self.info[0]['Family']==6 \
               and self.info[0]['Model'] in [7,8,9,10,11]

    def _is_PentiumIV(self):
        return self.is_Intel() and self.info[0]['Family']==15

    # Varia

    def _is_singleCPU(self):
        return len(self.info) == 1

    def _getNCPUs(self):
        return len(self.info)

    def _has_mmx(self):
        if self.is_Intel():
            return (self.info[0]['Family']==5 and self.info[0]['Model']==4) \
                   or (self.info[0]['Family'] in [6,15])
        elif self.is_AMD():
            return self.info[0]['Family'] in [5,6,15]

    def _has_sse(self):
        if self.is_Intel():
            return (self.info[0]['Family']==6 and \
                    self.info[0]['Model'] in [7,8,9,10,11]) \
                    or self.info[0]['Family']==15
        elif self.is_AMD():
            return (self.info[0]['Family']==6 and \
                    self.info[0]['Model'] in [6,7,8,10]) \
                    or self.info[0]['Family']==15

    def _has_sse2(self):
        return self.info[0]['Family']==15

    def _has_3dnow(self):
        # XXX: does only AMD have 3dnow??
        return self.is_AMD() and self.info[0]['Family'] in [5,6,15]

    def _has_3dnowext(self):
        return self.is_AMD() and self.info[0]['Family'] in [6,15]

if sys.platform[:5] == 'linux': # variations: linux2,linux-i386 (any others?)
    cpuinfo = linux_cpuinfo
elif sys.platform[:4] == 'irix':
    cpuinfo = irix_cpuinfo
elif sys.platform == 'darwin':
    cpuinfo = darwin_cpuinfo
elif sys.platform[:5] == 'sunos':
    cpuinfo = sunos_cpuinfo
elif sys.platform[:5] == 'win32':
    cpuinfo = win32_cpuinfo
elif sys.platform[:6] == 'cygwin':
    cpuinfo = linux_cpuinfo
#XXX: other OS's. Eg. use _winreg on Win32. Or os.uname on unices.
else:
    cpuinfo = cpuinfo_base

cpu = cpuinfo()

if __name__ == "__main__":

    cpu.is_blaa()
    cpu.is_Intel()
    cpu.is_Alpha()

    print 'CPU information:',
    for name in dir(cpuinfo):
        if name[0]=='_' and name[1]!='_':
            r = getattr(cpu,name[1:])()
            if r:
                if r!=1:
                    print '%s=%s' %(name[1:],r),
                else:
                    print name[1:],
    print


import re
import os
import sys
import new

from distutils.ccompiler import *
from distutils import ccompiler
from distutils.sysconfig import customize_compiler
from distutils.version import LooseVersion

import log
from exec_command import exec_command
from misc_util import compiler_to_string
from distutils.spawn import _nt_quote_args            

# Using customized CCompiler.spawn.
def CCompiler_spawn(self, cmd, display=None):
    if display is None:
        display = cmd
        if type(display) is type([]): display = ' '.join(display)
    log.info(display)
    if type(cmd) is type([]) and os.name == 'nt':
        cmd = _nt_quote_args(cmd)
    s,o = exec_command(cmd)
    if s:
        if type(cmd) is type([]):
            cmd = ' '.join(cmd)
        print o
        raise DistutilsExecError,\
              'Command "%s" failed with exit status %d' % (cmd, s)
CCompiler.spawn = new.instancemethod(CCompiler_spawn,None,CCompiler)

def CCompiler_object_filenames(self, source_filenames, strip_dir=0, output_dir=''):
    if output_dir is None:
        output_dir = ''
    obj_names = []
    for src_name in source_filenames:
        base, ext = os.path.splitext(os.path.normpath(src_name))
        base = os.path.splitdrive(base)[1] # Chop off the drive
        base = base[os.path.isabs(base):]  # If abs, chop off leading /
        if base.startswith('..'):
            # Resolve starting relative path components, middle ones
            # (if any) have been handled by os.path.normpath above.
            i = base.rfind('..')+2
            d = base[:i]
            d = os.path.basename(os.path.abspath(d))
            base = d + base[i:]
        if ext not in self.src_extensions:
            raise UnknownFileError, \
                  "unknown file type '%s' (from '%s')" % (ext, src_name)
        if strip_dir:
            base = os.path.basename(base)
        obj_name = os.path.join(output_dir,base + self.obj_extension)
        obj_names.append(obj_name)
    return obj_names

CCompiler.object_filenames = new.instancemethod(CCompiler_object_filenames,
                                                None,CCompiler)

def CCompiler_compile(self, sources, output_dir=None, macros=None,
                      include_dirs=None, debug=0, extra_preargs=None,
                      extra_postargs=None, depends=None):
    if not sources:
        return []
    from fcompiler import FCompiler
    if isinstance(self, FCompiler):
        display = []
        for fc in ['f77','f90','fix']:
            fcomp = getattr(self,'compiler_'+fc)
            if fcomp is None:
                continue
            display.append("%s(%s) options: '%s'" % (os.path.basename(fcomp[0]),
                                                     fc,
                                                     ' '.join(fcomp[1:])))
        display = '\n'.join(display)
    else:
        ccomp = self.compiler_so
        display = "%s options: '%s'" % (os.path.basename(ccomp[0]),
                                        ' '.join(ccomp[1:]))
    log.info(display)
    macros, objects, extra_postargs, pp_opts, build = \
            self._setup_compile(output_dir, macros, include_dirs, sources,
                                depends, extra_postargs)
    cc_args = self._get_cc_args(pp_opts, debug, extra_preargs)
    display = "compile options: '%s'" % (' '.join(cc_args))
    if extra_postargs:
        display += "\nextra options: '%s'" % (' '.join(extra_postargs))
    log.info(display)
    
    # build any sources in same order as they were originally specified
    #   especially important for fortran .f90 files using modules
    if isinstance(self, FCompiler):
        objects_to_build = build.keys()
        for obj in objects:
            if obj in objects_to_build:
                src, ext = build[obj]
                self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)
    else:
        for obj, (src, ext) in build.items():
            self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)
        
    # Return *all* object filenames, not just the ones we just built.
    return objects

CCompiler.compile = new.instancemethod(CCompiler_compile,None,CCompiler)

def CCompiler_customize_cmd(self, cmd):
    """ Customize compiler using distutils command.
    """
    log.info('customize %s using %s' % (self.__class__.__name__,
                                        cmd.__class__.__name__))
    if getattr(cmd,'include_dirs',None) is not None:
        self.set_include_dirs(cmd.include_dirs)
    if getattr(cmd,'define',None) is not None:
        for (name,value) in cmd.define:
            self.define_macro(name, value)
    if getattr(cmd,'undef',None) is not None:
        for macro in cmd.undef:
            self.undefine_macro(macro)
    if getattr(cmd,'libraries',None) is not None:
        self.set_libraries(self.libraries + cmd.libraries)
    if getattr(cmd,'library_dirs',None) is not None:
        self.set_library_dirs(self.library_dirs + cmd.library_dirs)
    if getattr(cmd,'rpath',None) is not None:
        self.set_runtime_library_dirs(cmd.rpath)
    if getattr(cmd,'link_objects',None) is not None:
        self.set_link_objects(cmd.link_objects)
    return

CCompiler.customize_cmd = new.instancemethod(\
    CCompiler_customize_cmd,None,CCompiler)

def CCompiler_show_customization(self):
    if 0:
        for attrname in ['include_dirs','define','undef',
                         'libraries','library_dirs',
                         'rpath','link_objects']:
            attr = getattr(self,attrname,None)
            if not attr:
                continue
            log.info("compiler '%s' is set to %s" % (attrname,attr))
    try: self.get_version()
    except: pass
    if log._global_log.threshold<2:
        print '*'*80
        print self.__class__
        print compiler_to_string(self)
        print '*'*80

CCompiler.show_customization = new.instancemethod(\
    CCompiler_show_customization,None,CCompiler)


def CCompiler_customize(self, dist, need_cxx=0):
    # See FCompiler.customize for suggested usage.
    log.info('customize %s' % (self.__class__.__name__))
    customize_compiler(self)
    if need_cxx:
        if hasattr(self,'compiler') and self.compiler[0].find('gcc')>=0:
            if sys.version[:3]>='2.3':
                if not self.compiler_cxx:
                    self.compiler_cxx = [self.compiler[0].replace('gcc','g++')]\
                                        + self.compiler[1:]
            else:
                self.compiler_cxx = [self.compiler[0].replace('gcc','g++')]\
                                    + self.compiler[1:]
        else:
            log.warn('Missing compiler_cxx fix for '+self.__class__.__name__)
    return

CCompiler.customize = new.instancemethod(\
    CCompiler_customize,None,CCompiler)

def CCompiler_get_version(self, force=0, ok_status=[0]):
    """ Compiler version. Returns None if compiler is not available. """
    if not force and hasattr(self,'version'):
        return self.version
    if not (hasattr(self,'version_cmd') and
            hasattr(self,'version_pattern')):
        #log.warn('%s does not provide version_cmd and version_pattern attributes' \
        #         % (self.__class__))
        return

    cmd = ' '.join(self.version_cmd)
    status, output = exec_command(cmd,use_tee=0)
    version = None
    if status in ok_status:
        m = re.match(self.version_pattern,output)
        if m:
            version = m.group('version')
            assert version,`version`
            version = LooseVersion(version)
    self.version = version
    return version

CCompiler.get_version = new.instancemethod(\
    CCompiler_get_version,None,CCompiler)

if sys.platform == 'win32':
    compiler_class['mingw32'] = ('mingw32ccompiler', 'Mingw32CCompiler',
                                 "Mingw32 port of GNU C Compiler for Win32"\
                                 "(for MSC built Python)")
    if os.environ.get('OSTYPE','')=='msys' or \
           os.environ.get('MSYSTEM','')=='MINGW32':
        # On windows platforms, we want to default to mingw32 (gcc)
        # because msvc can't build blitz stuff.
        log.info('Setting mingw32 as default compiler for nt.')
        ccompiler._default_compilers = (('nt', 'mingw32'),) \
                                       + ccompiler._default_compilers


_distutils_new_compiler = new_compiler
def new_compiler (plat=None,
                  compiler=None,
                  verbose=0,
                  dry_run=0,
                  force=0):
    # Try first C compilers from scipy_distutils.
    if plat is None:
        plat = os.name
    try:
        if compiler is None:
            compiler = get_default_compiler(plat)
        (module_name, class_name, long_description) = compiler_class[compiler]
    except KeyError:
        msg = "don't know how to compile C/C++ code on platform '%s'" % plat
        if compiler is not None:
            msg = msg + " with '%s' compiler" % compiler
        raise DistutilsPlatformError, msg
    module_name = "scipy_distutils." + module_name
    try:
        __import__ (module_name)
    except ImportError, msg:
        print msg,'in scipy_distutils, trying from distutils..'
        module_name = module_name[6:]
        try:
            __import__(module_name)
        except ImportError, msg:
            raise DistutilsModuleError, \
                  "can't compile C/C++ code: unable to load module '%s'" % \
                  module_name
    try:
        module = sys.modules[module_name]
        klass = vars(module)[class_name]
    except KeyError:
        raise DistutilsModuleError, \
              ("can't compile C/C++ code: unable to find class '%s' " +
               "in module '%s'") % (class_name, module_name)
    compiler = klass(None, dry_run, force)
    log.debug('new_fcompiler returns %s' % (klass))
    return compiler

ccompiler.new_compiler = new_compiler


import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

class LaheyFCompiler(FCompiler):

    compiler_type = 'lahey'
    version_pattern =  r'Lahey/Fujitsu Fortran 95 Compiler Release (?P<version>[^\s*]*)'

    executables = {
        'version_cmd'  : ["lf95", "--version"],
        'compiler_f77' : ["lf95", "--fix"],
        'compiler_fix' : ["lf95", "--fix"],
        'compiler_f90' : ["lf95"],
        'linker_so'    : ["lf95","-shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    module_dir_switch = None  #XXX Fix me
    module_include_switch = None #XXX Fix me

    def get_flags_opt(self):
        return ['-O']
    def get_flags_debug(self):
        return ['-g','--chk','--chkglobal']
    def get_library_dirs(self):
        opt = []
        d = os.environ.get('LAHEY')
        if d:
            opt.append(os.path.join(d,'lib'))
        return opt
    def get_libraries(self):
        opt = []
        opt.extend(['fj9f6', 'fj9i6', 'fj9ipp', 'fj9e6'])
        return opt

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='lahey')
    compiler.customize()
    print compiler.get_version()


import os,sys,string
import re
import types
import glob

if sys.version[:3]<='2.1':
    from distutils import util
    util_get_platform = util.get_platform
    util.get_platform = lambda : util_get_platform().replace(' ','_')

# Hooks for colored terminal output.
# See also http://www.livinglogic.de/Python/ansistyle
def terminal_has_colors():
    if sys.platform=='cygwin' and not os.environ.has_key('USE_COLOR'):
        # Avoid importing curses that causes illegal operation
        # with a message:
        #  PYTHON2 caused an invalid page fault in
        #  module CYGNURSES7.DLL as 015f:18bbfc28
        # Details: Python 2.3.3 [GCC 3.3.1 (cygming special)]
        #          ssh to Win32 machine from debian
        #          curses.version is 2.2
        #          CYGWIN_98-4.10, release 1.5.7(0.109/3/2))
        return 0
    if hasattr(sys.stdout,'isatty') and sys.stdout.isatty(): 
        try:
            import curses
            curses.setupterm()
            if (curses.tigetnum("colors") >= 0
                and curses.tigetnum("pairs") >= 0
                and ((curses.tigetstr("setf") is not None 
                      and curses.tigetstr("setb") is not None) 
                     or (curses.tigetstr("setaf") is not None
                         and curses.tigetstr("setab") is not None)
                     or curses.tigetstr("scp") is not None)):
                return 1
        except Exception,msg:
            pass
    return 0

if terminal_has_colors():
    def red_text(s): return '\x1b[31m%s\x1b[0m'%s
    def green_text(s): return '\x1b[32m%s\x1b[0m'%s
    def yellow_text(s): return '\x1b[33m%s\x1b[0m'%s
    def blue_text(s): return '\x1b[34m%s\x1b[0m'%s
    def cyan_text(s): return '\x1b[35m%s\x1b[0m'%s
else:
    def red_text(s): return s
    def green_text(s): return s
    def yellow_text(s): return s
    def cyan_text(s): return s
    def blue_text(s): return s

class PostponedException:
    """Postpone exception until an attempt is made to use a resource."""
    #Example usage:
    #  try: import foo
    #  except ImportError: foo = PostponedException()
    __all__ = []
    def __init__(self):
        self._info = sys.exc_info()[:2]
        self.__doc__ = '%s: %s' % tuple(self._info)
    def __getattr__(self,name):
        raise self._info[0],self._info[1]

def get_path(mod_name,parent_path=None):
    """ This function makes sure installation is done from the
        correct directory no matter if it is installed from the
        command line or from another package or run_setup function.
        
    """
    if mod_name == '__main__':
        d = os.path.abspath('.')
    elif mod_name == '__builtin__':
        #builtin if/then added by Pearu for use in core.run_setup.        
        d = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        mod = __import__(mod_name)
        file = mod.__file__
        d = os.path.dirname(os.path.abspath(file))
    if parent_path is not None:
        pd = os.path.abspath(parent_path)
        if pd==d[:len(pd)]:
            d = d[len(pd)+1:]
    return d or '.'
    
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
        has a configuration() function in it. 
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

def default_config_dict(name = None, parent_name = None, local_path=None):
    """ Return a configuration dictionary for usage in
    configuration() function defined in file setup_<name>.py.
    """
    d={}
    for key in list_keys: d[key] = []
    for key in dict_keys: d[key] = {}

    full_name = dot_join(parent_name,name)

    if full_name:
        # XXX: The following assumes that default_config_dict is called
        #      only from setup_<name>.configuration().
        #      Todo: implement check for this assumption.
        if local_path is None:
            frame = get_frame(1)
            caller_name = eval('__name__',frame.f_globals,frame.f_locals)
            local_path = get_path(caller_name)
        test_path = os.path.join(local_path,'tests')
        if 0 and name and parent_name is None:
            # Useful for local builds
            d['version'] = get_version(path=local_path)
        if os.path.exists(os.path.join(local_path,'__init__.py')):
            d['packages'].append(full_name)
            d['package_dir'][full_name] = local_path
        if os.path.exists(test_path):
            d['packages'].append(dot_join(full_name,'tests'))
            d['package_dir'][dot_join(full_name,'tests')] = test_path
        d['name'] = full_name
        if 0 and not parent_name:
            # Include scipy_distutils to local distributions
            for p in ['.','..']:
                dir_name = os.path.abspath(os.path.join(local_path,
                                                        p,'scipy_distutils'))
                if os.path.exists(dir_name):
                    d['packages'].append('scipy_distutils')
                    d['packages'].append('scipy_distutils.command')
                    d['package_dir']['scipy_distutils'] = dir_name
                    break
    return d

def get_frame(level=0):
    try:
        return sys._getframe(level+1)
    except AttributeError:
        frame = sys.exc_info()[2].tb_frame
        for i in range(level+1):
            frame = frame.f_back
        return frame

def merge_config_dicts(config_list):
    result = default_config_dict()
    for d in config_list:
        if not d: continue
        name = d.get('name',None)
        if name is not None:
            result['name'] = name
            break
    for d in config_list:
        if not d: continue
        for key in list_keys:
            result[key].extend(d.get(key,[]))
        for key in dict_keys:
            result[key].update(d.get(key,{}))
    return result

def dict_append(d,**kws):
    for k,v in kws.items():
        if d.has_key(k):
            d[k].extend(v)
        else:
            d[k] = v

def dot_join(*args):
    return string.join(filter(None,args),'.')

def fortran_library_item(lib_name,
                         sources,
                         **attrs
                         ):   #obsolete feature
    """ Helper function for creating fortran_libraries items. """
    build_info = {'sources':sources}
    known_attrs = ['module_files','module_dirs',
                   'libraries','library_dirs']
    for key,value in attrs.items():
        if key not in known_attrs:
            raise TypeError,\
                  "fortran_library_item() got an unexpected keyword "\
                  "argument '%s'" % key
        build_info[key] = value
    
    return (lib_name,build_info)

def get_environ_include_dirs():  #obsolete feature
    includes = []
    if os.environ.has_key('PYTHONINCLUDE'):
        includes = os.environ['PYTHONINCLUDE'].split(os.pathsep)
    return includes

def get_build_temp():
    from distutils.util import get_platform
    plat_specifier = ".%s-%s" % (get_platform(), sys.version[0:3])
    return os.path.join('build','temp'+plat_specifier)

class SourceGenerator:  #obsolete feature
    """ SourceGenerator
    func    - creates target, arguments are (target,sources)+args
    sources - target source files
    args    - extra arguments to func

    If func is None then target must exist and it is touched whenever
    sources are newer.
    """
    def __init__(self,func,target,sources=[],*args):
        if not os.path.isabs(target) and func is not None:
            g = sys._getframe(1).f_globals
            fn = g.get('__file__',g.get('__name__'))
            if fn=='__main__': fn = sys.argv[0]
            caller_dir = os.path.abspath(os.path.dirname(fn))
            prefix = os.path.commonprefix([caller_dir,os.getcwd()])
            target_dir = caller_dir[len(prefix)+1:]
            target = os.path.join(get_build_temp(),target_dir,target)
        self.func = func
        self.target = target
        self.sources = sources
        self.args = args
    def __str__(self):
        return str(self.target)
    def generate(self):
        from distutils import dep_util,dir_util
        if dep_util.newer_group(self.sources,self.target):
            print 'Running generate',self.target
            dir_util.mkpath(os.path.dirname(self.target),verbose=1)
            if self.func is None:
                # Touch target
                os.utime(self.target,None)
            else:
                self.func(self.target,self.sources,*self.args)
        assert os.path.exists(self.target),`self.target`
        return self.target
    def __call__(self, extension, src_dir):
        return self.generate()

class SourceFilter:  #obsolete feature
    """ SourceFilter
    func    - implements criteria to filter sources
    sources - source files
    args    - extra arguments to func
    """
    def __init__(self,func,sources,*args):
        self.func = func
        self.sources = sources
        self.args = args
    def filter(self):
        return self.func(self.sources,*self.args)
    def __call__(self, extension, src_dir):
        return self.filter()

##

#XXX need support for .C that is also C++
cxx_ext_match = re.compile(r'.*[.](cpp|cxx|cc)\Z',re.I).match
fortran_ext_match = re.compile(r'.*[.](f90|f95|f77|for|ftn|f)\Z',re.I).match
f90_ext_match = re.compile(r'.*[.](f90|f95)\Z',re.I).match
f90_module_name_match = re.compile(r'\s*module\s*(?P<name>[\w_]+)',re.I).match
def get_f90_modules(source):
    """ Return a list of Fortran f90 module names that
    given source file defines.
    """
    if not f90_ext_match(source):
        return []
    modules = []
    f = open(source,'r')
    f_readlines = getattr(f,'xreadlines',f.readlines)
    for line in f_readlines():
        m = f90_module_name_match(line)
        if m:
            name = m.group('name')
            modules.append(name)
            # break  # XXX can we assume that there is one module per file?
    f.close()
    return modules

def all_strings(lst):
    """ Return True if all items in lst are string objects. """
    for item in lst:
        if type(item) is not types.StringType:
            return 0
    return 1

def has_f_sources(sources):
    """ Return True if sources contains Fortran files """
    for source in sources:
        if fortran_ext_match(source):
            return 1
    return 0

def has_cxx_sources(sources):
    """ Return True if sources contains C++ files """
    for source in sources:
        if cxx_ext_match(source):
            return 1
    return 0

def filter_sources(sources):
    """ Return four lists of filenames containing
    C, C++, Fortran, and Fortran 90 module sources,
    respectively.
    """
    c_sources = []
    cxx_sources = []
    f_sources = []
    fmodule_sources = []
    for source in sources:
        if fortran_ext_match(source):
            modules = get_f90_modules(source)
            if modules:
                fmodule_sources.append(source)
            else:
                f_sources.append(source)
        elif cxx_ext_match(source):
            cxx_sources.append(source)
        else:
            c_sources.append(source)            
    return c_sources, cxx_sources, f_sources, fmodule_sources

def compiler_to_string(compiler):
    props = []
    mx = 0
    keys = compiler.executables.keys()
    for key in ['version','libraries','library_dirs',
                'object_switch','compile_switch',
                'include_dirs','define','undef','rpath','link_objects']:
        if key not in keys:
            keys.append(key)
    for key in keys:
        if hasattr(compiler,key):
            v = getattr(compiler, key)
            mx = max(mx,len(key))
            props.append((key,`v`))
    lines = []
    format = '%-' +`mx+1`+ 's = %s'
    for prop in props:
        lines.append(format % prop)
    return '\n'.join(lines)

def _get_dirs_with_init((packages,path), dirname, names):
    """Internal: used by get_subpackages."""
    for bad in ['.svn','build']:
        if bad in names:
            del names[names.index(bad)]
    if os.path.isfile(os.path.join(dirname,'__init__.py')):
        if path==dirname: return
        package_name = '.'.join(dirname.split(os.sep)[len(path.split(os.sep)):])
        if package_name not in packages:
            packages.append(package_name)

def get_subpackages(path,
                    parent=None,
                    parent_path=None,
                    include_packages=[],
                    ignore_packages=[],
                    recursive=None):

    """
    Return a list of configurations found in a tree of Python
    packages.

    It is assumed that each package xxx in path/xxx has file
    path/xxx/info_xxx.py that follows convention specified in
    scipy/DEVELOPERS.txt.

    Packages that do not define info_*.py files or should override
    options in info*_.py files can be specified in include_packages
    list.

    Unless a package xxx is specified standalone, it will be installed
    as parent.xxx.

    Specifying parent_path is recommended for reducing verbosity of
    compilations.

    Packages in ignore_packages list will be ignored unless they are
    also in include_packages.

    If recursive is True then subpackages are searched recursively
    starting from the path and added to include_packages list.
    """

    config_list = []

    for info_file in glob.glob(os.path.join(path,'*','info_*.py')):
        package_name = os.path.basename(os.path.dirname(info_file))
        if package_name != os.path.splitext(os.path.basename(info_file))[0][5:]:
            print '  !! Mismatch of package name %r and %s' \
                  % (package_name, info_file)
            continue

        if package_name in ignore_packages:
            continue

        sys.path.insert(0,os.path.dirname(info_file))
        try:
            exec 'import %s as info_module' \
                 % (os.path.splitext(os.path.basename(info_file))[0])
            if not getattr(info_module,'ignore',0):
                exec 'import setup_%s as setup_module' % (package_name)
                if getattr(info_module,'standalone',0) or not parent:
                    args = ('',)
                else:
                    args = (parent,)
                if setup_module.configuration.func_code.co_argcount>1:
                    args = args + (parent_path,)
                config = setup_module.configuration(*args)
                config_list.append(config)
        finally:
            del sys.path[0]

    if recursive:
        os.path.walk(path,_get_dirs_with_init, (include_packages,path))

    for package_name in include_packages:
        dirname = os.path.join(*([path]+package_name.split('.')))
        setup_file = os.path.join(dirname,\
                                  'setup_' + package_name.split('.')[-1]+'.py')
        if not os.path.isfile(setup_file):
            print 'Assuming default configuration (%r was not found)' \
                  % (setup_file)

            config = default_config_dict(package_name, parent or '',
                                         local_path=dirname)
            config_list.append(config)
            continue
    
        sys.path.insert(0,dirname)
        try:
            exec 'import setup_%s as setup_module' % (package_name)
            if not parent:
                args = ('',)
            else:
                args = (parent,)
            if setup_module.configuration.func_code.co_argcount>1:
                args = args + (parent_path,)
            config = setup_module.configuration(*args)
            config_list.append(config)
        finally:
            del sys.path[0]
    return config_list

def generate_config_py(extension, build_dir):
    """ Generate <package>/config.py file containing system_info
    information used during building the package.

    Usage:\
        ext = Extension(dot_join(config['name'],'config'),
                        sources=[generate_config_py])
        config['ext_modules'].append(ext)
    """
    from scipy_distutils.system_info import system_info
    from distutils.dir_util import mkpath
    target = os.path.join(*([build_dir]+extension.name.split('.'))) + '.py'
    mkpath(os.path.dirname(target))
    f = open(target,'w')
    f.write('# This file is generated by %s\n' % (os.path.abspath(sys.argv[0])))
    f.write('# It contains system_info results at the time of building this package.\n')
    f.write('__all__ = ["get_info","show"]\n\n')
    for k,i in system_info.saved_results.items():
        f.write('%s=%r\n' % (k,i))
    f.write('\ndef get_info(name): g=globals(); return g.get(name,g.get(name+"_info",{}))\n')
    f.write('''
def show():
    for name,info_dict in globals().items():
        if name[0]=="_" or type(info_dict) is not type({}): continue
        print name+":"
        if not info_dict:
            print "  NOT AVAILABLE"
        for k,v in info_dict.items():
            v = str(v)
            if k==\'sources\' and len(v)>200: v = v[:60]+\' ...\\n... \'+v[-60:]
            print \'    %s = %s\'%(k,v)
        print
    return
    ''')

    f.close()
    return target

def generate_svn_version_py(extension, build_dir):
    """ Generate __svn_version__.py file containing SVN
    revision number of a module.
    
    To use, add the following codelet to setup
    configuration(..) function

      ext = Extension(dot_join(config['name'],'__svn_version__'),
                      sources=[generate_svn_version_py])
      ext.local_path = local_path
      config['ext_modules'].append(ext)

    """
    from distutils import dep_util
    local_path = extension.local_path
    target = os.path.join(build_dir, '__svn_version__.py')
    entries = os.path.join(local_path,'.svn','entries')
    if not dep_util.newer(entries, target):
        return target
    revision = get_svn_revision(local_path)
    f = open(target,'w')
    f.write('revision=%s\n' % (revision))
    f.close()
    return target

def get_svn_revision(path):
    """ Return path's SVN revision number.
    """
    entries = os.path.join(path,'.svn','entries')
    revision = None
    if os.path.isfile(entries):
        f = open(entries)
        m = re.search(r'revision="(?P<revision>\d+)"',f.read())
        f.close()
        if m:
            revision = int(m.group('revision'))
    return revision

if __name__ == '__main__':
    print 'terminal_has_colors:',terminal_has_colors()
    print red_text("This is red text")
    print yellow_text("This is yellow text")

import os
import sys

from cpuinfo import cpu
from gnufcompiler import GnuFCompiler
#from fcompiler import FCompiler

class VastFCompiler(GnuFCompiler):

    compiler_type = 'vast'
    version_pattern = r'\s*Pacific-Sierra Research vf90 '\
                      '(Personal|Professional)\s+(?P<version>[^\s]*)'

    # VAST f90 does not support -o with -c. So, object files are created
    # to the current directory and then moved to build directory
    object_switch = ' && function _mvfile { mv -v `basename $1` $1 ; } && _mvfile '

    executables = {
        'version_cmd'  : ["vf90", "-v"],
        'compiler_f77' : ["g77"],
        'compiler_fix' : ["f90", "-Wv,-ya"],
        'compiler_f90' : ["f90"],
        'linker_so'    : ["f90"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }
    module_dir_switch = None  #XXX Fix me
    module_include_switch = None #XXX Fix me

    def get_version_cmd(self):
        f90 = self.compiler_f90[0]
        d,b = os.path.split(f90)
        vf90 = os.path.join(d,'v'+b)
        return vf90

    def get_flags_arch(self):
        vast_version = self.get_version()
        gnu = GnuFCompiler()
        gnu.customize()
        self.version = gnu.get_version()
        opt = GnuFCompiler.get_flags_arch(self)
        self.version = vast_version
        return opt

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='vast')
    compiler.customize()
    print compiler.get_version()

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

class NAGFCompiler(FCompiler):

    compiler_type = 'nag'
    version_pattern =  r'NAGWare Fortran 95 compiler Release (?P<version>[^\s]*)'

    executables = {
        'version_cmd'  : ["f95", "-V"],
        'compiler_f77' : ["f95", "-fixed"],
        'compiler_fix' : ["f95", "-fixed"],
        'compiler_f90' : ["f95"],
        'linker_so'    : ["f95"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    def get_flags_linker_so(self):
        if sys.platform=='darwin':
            return ['-unsharedf95','-Wl,-bundle,-flat_namespace,-undefined,suppress']
        return ["-Wl,shared"]
    def get_flags_opt(self):
        return ['-O4']
    def get_flags_arch(self):
        return ['-target=native']
    def get_flags_debug(self):
        return ['-g','-gline','-g90','-nan','-C']

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='nag')
    compiler.customize()
    print compiler.get_version()

"""scipy_distutils.fcompiler

Contains FCompiler, an abstract base class that defines the interface
for the Scipy_distutils Fortran compiler abstraction model.

"""

import re
import os
import sys
import atexit
from types import StringType, NoneType, ListType, TupleType
from glob import glob

from distutils.version import StrictVersion
from scipy_distutils.ccompiler import CCompiler, gen_lib_options
# distutils.ccompiler provides the following functions:
#   gen_preprocess_options(macros, include_dirs)
#   gen_lib_options(compiler, library_dirs, runtime_library_dirs, libraries)
from distutils.errors import DistutilsModuleError,DistutilsArgError,\
     DistutilsExecError,CompileError,LinkError,DistutilsPlatformError
from distutils.core import Command
from distutils.util import split_quoted
from distutils.fancy_getopt import FancyGetopt
from distutils.sysconfig import get_config_var
from distutils.spawn import _nt_quote_args            


from scipy_distutils.command.config_compiler import config_fc

import log
from misc_util import compiler_to_string
from exec_command import find_executable, exec_command

class FCompiler(CCompiler):
    """ Abstract base class to define the interface that must be implemented
    by real Fortran compiler classes.

    Methods that subclasses may redefine:

        get_version_cmd(), get_linker_so(), get_version()
        get_flags(), get_flags_opt(), get_flags_arch(), get_flags_debug()
        get_flags_f77(), get_flags_opt_f77(), get_flags_arch_f77(),
        get_flags_debug_f77(), get_flags_f90(), get_flags_opt_f90(),
        get_flags_arch_f90(), get_flags_debug_f90(),
        get_flags_fix(), get_flags_linker_so(), get_flags_version()

    DON'T call these methods (except get_version) after
    constructing a compiler instance or inside any other method.
    All methods, except get_version_cmd() and get_flags_version(), may
    call get_version() method.

    After constructing a compiler instance, always call customize(dist=None)
    method that finalizes compiler construction and makes the following
    attributes available:
      compiler_f77
      compiler_f90
      compiler_fix
      linker_so
      archiver
      ranlib
      libraries
      library_dirs
    """
    # CCompiler defines the following attributes:
    #   compiler_type
    #   src_extensions
    #   obj_extension
    #   static_lib_extension
    #   shared_lib_extension
    #   static_lib_format
    #   shared_lib_format
    #   exe_extension
    #   language_map    ### REDEFINED
    #   language_order  ### REDEFINED
    # and the following public methods:
    #   set_executables(**args)
    #     set_executable(key,value)
    #   define_macro(name, value=None)
    #   undefine_macro(name)
    #   add_include_dir(dir)
    #   set_include_dirs(dirs)
    #   add_library(libname)
    #   set_libraries(libnames)
    #   add_library_dir(dir)
    #   set_library_dirs(dirs)
    #   add_runtime_library_dir(dir)
    #   set_runtime_library_dirs(dirs)
    #   add_link_object(object)
    #   set_link_objects(objects)
    #
    #   detect_language(sources)  ### USABLE
    #
    #   preprocess(source,output_file=None,macros=None,include_dirs=None,
    #              extra_preargs=None,extra_postargs=None)
    #   compile(sources, output_dir=None, macros=None,
    #           include_dirs=None, debug=0, extra_preargs=None,
    #           extra_postargs=None, depends=None)
    #   create_static_lib(objects,output_libname,output_dir=None,debug=0,target_lang=None):
    #   link(target_desc, objects, output_filename, output_dir=None,
    #        libraries=None, library_dirs=None, runtime_library_dirs=None,
    #        export_symbols=None, debug=0, extra_preargs=None, extra_postargs=None,
    #        build_temp=None, target_lang=None)
    #   link_shared_lib(objects, output_libname, output_dir=None,
    #                   libraries=None, library_dirs=None, runtime_library_dirs=None,
    #                   export_symbols=None, debug=0, extra_preargs=None,
    #                   extra_postargs=None, build_temp=None, target_lang=None)
    #   link_shared_object(objects,output_filename,output_dir=None,
    #                      libraries=None,library_dirs=None,runtime_library_dirs=None,
    #                      export_symbols=None,debug=0,extra_preargs=None,
    #                      extra_postargs=None,build_temp=None,target_lang=None)
    #   link_executable(objects,output_progname,output_dir=None,
    #                   libraries=None,library_dirs=None,runtime_library_dirs=None,
    #                   debug=0,extra_preargs=None,extra_postargs=None,target_lang=None)
    #
    #   library_dir_option(dir)
    #   runtime_library_dir_option(dir)
    #   library_option(lib)
    #   has_function(funcname,includes=None,include_dirs=None,
    #                libraries=None,library_dirs=None)
    #   find_library_file(dirs, lib, debug=0)
    #
    #   object_filenames(source_filenames, strip_dir=0, output_dir='')
    #   shared_object_filename(basename, strip_dir=0, output_dir='')
    #   executable_filenamee(basename, strip_dir=0, output_dir='')
    #   library_filename(libname, lib_type='static',strip_dir=0, output_dir=''):
    #
    #   announce(msg, level=1)
    #   debug_print(msg)
    #   warn(msg)
    #   execute(func, args, msg=None, level=1)
    #   spawn(cmd)
    #   move_file(src,dst)
    #   mkpath(name, mode=0777)
    #

    language_map = {'.f':'f77',
                    '.for':'f77',
                    '.F':'f77',    # XXX: needs preprocessor
                    '.ftn':'f77',
                    '.f77':'f77',
                    '.f90':'f90',
                    '.F90':'f90',  # XXX: needs preprocessor
                    '.f95':'f90',
                    }
    language_order = ['f90','f77']

    version_pattern = None

    executables = {
        'version_cmd'  : ["f77","-v"],
        'compiler_f77' : ["f77"],
        'compiler_f90' : ["f90"],
        'compiler_fix' : ["f90","-fixed"],
        'linker_so'    : ["f90","-shared"],
        #'linker_exe'   : ["f90"],  #  XXX do we need it??
        'archiver'     : ["ar","-cr"],
        'ranlib'       : None,
        }

    compile_switch = "-c"
    object_switch = "-o "   # Ending space matters! It will be stripped
                            # but if it is missing then object_switch
                            # will be prefixed to object file name by
                            # string concatenation.
    library_switch = "-o "  # Ditto!

    # Switch to specify where module files are created and searched
    # for USE statement.  Normally it is a string and also here ending
    # space matters. See above.
    module_dir_switch = None

    # Switch to specify where module files are searched for USE statement.
    module_include_switch = '-I' 

    pic_flags = []           # Flags to create position-independent code

    src_extensions = ['.for','.ftn','.f77','.f','.f90','.f95','.F','.F90']
    obj_extension = ".o"
    shared_lib_extension = get_config_var('SO')  # or .dll
    static_lib_extension = ".a"  # or .lib
    static_lib_format = "lib%s%s" # or %s%s
    shared_lib_format = "%s%s"
    exe_extension = ""

    ######################################################################
    ## Methods that subclasses may redefine. But don't call these methods!
    ## They are private to FCompiler class and may return unexpected
    ## results if used elsewhere. So, you have been warned..

    def get_version_cmd(self):
        """ Compiler command to print out version information. """
        f77 = self.executables['compiler_f77']
        if f77 is not None:
            f77 = f77[0]
        cmd = self.executables['version_cmd']
        if cmd is not None:
            cmd = cmd[0]
            if cmd==f77:
                cmd = self.compiler_f77[0]
            else:
                f90 = self.executables['compiler_f90']
                if f90 is not None:
                    f90 = f90[0]
                if cmd==f90:
                    cmd = self.compiler_f90[0]
        return cmd

    def get_linker_so(self):
        """ Linker command to build shared libraries. """
        f77 = self.executables['compiler_f77']
        if f77 is not None:
            f77 = f77[0]
        ln = self.executables['linker_so']
        if ln is not None:
            ln = ln[0]
            if ln==f77:
                ln = self.compiler_f77[0]
            else:
                f90 = self.executables['compiler_f90']
                if f90 is not None:
                    f90 = f90[0]
                if ln==f90:
                    ln = self.compiler_f90[0]
        return ln

    def get_flags(self):
        """ List of flags common to all compiler types. """
        return [] + self.pic_flags
    def get_flags_version(self):
        """ List of compiler flags to print out version information. """
        if self.executables['version_cmd']:
            return self.executables['version_cmd'][1:]
        return []
    def get_flags_f77(self):
        """ List of Fortran 77 specific flags. """
        if self.executables['compiler_f77']:
            return self.executables['compiler_f77'][1:]
        return []
    def get_flags_f90(self):
        """ List of Fortran 90 specific flags. """
        if self.executables['compiler_f90']:
            return self.executables['compiler_f90'][1:]
        return []
    def get_flags_fix(self):
        """ List of Fortran 90 fixed format specific flags. """
        if self.executables['compiler_fix']:
            return self.executables['compiler_fix'][1:]
        return []
    def get_flags_linker_so(self):
        """ List of linker flags to build a shared library. """
        if self.executables['linker_so']:
            return self.executables['linker_so'][1:]
        return []
    def get_flags_ar(self):
        """ List of archiver flags. """
        if self.executables['archiver']:
            return self.executables['archiver'][1:]
        return []
    def get_flags_opt(self):
        """ List of architecture independent compiler flags. """
        return []
    def get_flags_arch(self):
        """ List of architecture dependent compiler flags. """
        return []
    def get_flags_debug(self):
        """ List of compiler flags to compile with debugging information. """
        return []
    get_flags_opt_f77 = get_flags_opt_f90 = get_flags_opt
    get_flags_arch_f77 = get_flags_arch_f90 = get_flags_arch
    get_flags_debug_f77 = get_flags_debug_f90 = get_flags_debug

    def get_libraries(self):
        """ List of compiler libraries. """
        return self.libraries[:]
    def get_library_dirs(self):
        """ List of compiler library directories. """
        return self.library_dirs[:]

    ############################################################

    ## Public methods:

    def customize(self, dist=None):
        """ Customize Fortran compiler.

        This method gets Fortran compiler specific information from
        (i) class definition, (ii) environment, (iii) distutils config
        files, and (iv) command line.

        This method should be always called after constructing a
        compiler instance. But not in __init__ because Distribution
        instance is needed for (iii) and (iv).
        """
        log.info('customize %s' % (self.__class__.__name__))
        if dist is None:
            # These hooks are for testing only!
            from dist import Distribution
            dist = Distribution()
            dist.script_name = os.path.basename(sys.argv[0])
            dist.script_args = ['config_fc'] + sys.argv[1:]
            dist.cmdclass['config_fc'] = config_fc
            dist.parse_config_files()
            dist.parse_command_line()

        conf = dist.get_option_dict('config_fc')
        noopt = conf.get('noopt',[None,0])[1]
        if 0: # change to `if 1:` when making release.
            # Don't use architecture dependent compiler flags:
            noarch = 1
        else:
            noarch = conf.get('noarch',[None,noopt])[1]
        debug = conf.get('debug',[None,0])[1]

        f77 = self.__get_cmd('compiler_f77','F77',(conf,'f77exec'))
        f90 = self.__get_cmd('compiler_f90','F90',(conf,'f90exec'))
        # Temporarily setting f77,f90 compilers so that
        # version_cmd can use their executables.
        if f77:
            self.set_executables(compiler_f77=[f77])
        if f90:
            self.set_executables(compiler_f90=[f90])

        # Must set version_cmd before others as self.get_flags*
        # methods may call self.get_version.
        vers_cmd = self.__get_cmd(self.get_version_cmd)
        if vers_cmd:
            vflags = self.__get_flags(self.get_flags_version)
            self.set_executables(version_cmd=[vers_cmd]+vflags)

        if f77:
            f77flags = self.__get_flags(self.get_flags_f77,'F77FLAGS',
                                   (conf,'f77flags'))
        if f90:
            f90flags = self.__get_flags(self.get_flags_f90,'F90FLAGS',
                                       (conf,'f90flags'))

        # XXX Assuming that free format is default for f90 compiler.
        fix = self.__get_cmd('compiler_fix','F90',(conf,'f90exec'))
        if fix:
            fixflags = self.__get_flags(self.get_flags_fix) + f90flags

        oflags,aflags,dflags = [],[],[]
        if not noopt:
            oflags = self.__get_flags(self.get_flags_opt,'FOPT',(conf,'opt'))
            if f77 and self.get_flags_opt is not self.get_flags_opt_f77:
                f77flags += self.__get_flags(self.get_flags_opt_f77)
            if f90 and self.get_flags_opt is not self.get_flags_opt_f90:
                f90flags += self.__get_flags(self.get_flags_opt_f90)
            if fix and self.get_flags_opt is not self.get_flags_opt_f90:
                fixflags += self.__get_flags(self.get_flags_opt_f90)
            if not noarch:
                aflags = self.__get_flags(self.get_flags_arch,'FARCH',
                                          (conf,'arch'))
                if f77 and self.get_flags_arch is not self.get_flags_arch_f77:
                    f77flags += self.__get_flags(self.get_flags_arch_f77)
                if f90 and self.get_flags_arch is not self.get_flags_arch_f90:
                    f90flags += self.__get_flags(self.get_flags_arch_f90)
                if fix and self.get_flags_arch is not self.get_flags_arch_f90:
                    fixflags += self.__get_flags(self.get_flags_arch_f90)
        if debug:
            dflags = self.__get_flags(self.get_flags_debug,'FDEBUG')
            if f77  and self.get_flags_debug is not self.get_flags_debug_f77:
                f77flags += self.__get_flags(self.get_flags_debug_f77)
            if f90  and self.get_flags_debug is not self.get_flags_debug_f90:
                f90flags += self.__get_flags(self.get_flags_debug_f90)
            if fix and self.get_flags_debug is not self.get_flags_debug_f90:
                fixflags += self.__get_flags(self.get_flags_debug_f90)

        fflags = self.__get_flags(self.get_flags,'FFLAGS') \
                 + dflags + oflags + aflags

        if f77:
            self.set_executables(compiler_f77=[f77]+f77flags+fflags)
        if f90:
            self.set_executables(compiler_f90=[f90]+f90flags+fflags)
        if fix:
            self.set_executables(compiler_fix=[fix]+fixflags+fflags)

        #XXX: Do we need LDSHARED->SOSHARED, LDFLAGS->SOFLAGS
        linker_so = self.__get_cmd(self.get_linker_so,'LDSHARED')
        if linker_so:
            linker_so_flags = self.__get_flags(self.get_flags_linker_so,'LDFLAGS')
            self.set_executables(linker_so=[linker_so]+linker_so_flags)

        ar = self.__get_cmd('archiver','AR')
        if ar:
            arflags = self.__get_flags(self.get_flags_ar,'ARFLAGS')
            self.set_executables(archiver=[ar]+arflags)

        ranlib = self.__get_cmd('ranlib','RANLIB')
        if ranlib:
            self.set_executables(ranlib=[ranlib])

        self.set_library_dirs(self.get_library_dirs())
        self.set_libraries(self.get_libraries())

        verbose = conf.get('verbose',[None,0])[1]
        if verbose:
            self.dump_properties()
        return

    def dump_properties(self):
        """ Print out the attributes of a compiler instance. """
        props = []
        for key in self.executables.keys() + \
                ['version','libraries','library_dirs',
                 'object_switch','compile_switch']:
            if hasattr(self,key):
                v = getattr(self,key)
                props.append((key, None, '= '+`v`))
        props.sort()

        pretty_printer = FancyGetopt(props)
        for l in pretty_printer.generate_help("%s instance properties:" \
                                              % (self.__class__.__name__)):
            if l[:4]=='  --':
                l = '  ' + l[4:]
            print l
        return

    ###################

    def _compile(self, obj, src, ext, cc_args, extra_postargs, pp_opts):
        """Compile 'src' to product 'obj'."""
        if is_f_file(src):
            flavor = ':f77'
            compiler = self.compiler_f77
        elif is_free_format(src):
            flavor = ':f90'
            compiler = self.compiler_f90
            if compiler is None:
                raise DistutilsExecError, 'f90 not supported by '\
                      +self.__class__.__name__
        else:
            flavor = ':fix'
            compiler = self.compiler_fix
            if compiler is None:
                raise DistutilsExecError, 'f90 (fixed) not supported by '\
                      +self.__class__.__name__
        if self.object_switch[-1]==' ':
            o_args = [self.object_switch.strip(),obj]
        else:
            o_args = [self.object_switch.strip()+obj]

        assert self.compile_switch.strip()
        s_args = [self.compile_switch, src]

        if os.name == 'nt':
            compiler = _nt_quote_args(compiler)
        command = compiler + cc_args + s_args + o_args + extra_postargs

        display = '%s: %s' % (os.path.basename(compiler[0]) + flavor,
                              src)
        try:
            self.spawn(command,display=display)
        except DistutilsExecError, msg:
            raise CompileError, msg

        return

    def module_options(self, module_dirs, module_build_dir):
        options = []
        if self.module_dir_switch is not None:
            if self.module_dir_switch[-1]==' ':
                options.extend([self.module_dir_switch.strip(),module_build_dir])
            else:
                options.append(self.module_dir_switch.strip()+module_build_dir)
        else:
            print 'XXX: module_build_dir=%r option ignored' % (module_build_dir)
            print 'XXX: Fix module_dir_switch for ',self.__class__.__name__
        if self.module_include_switch is not None:
            for d in [module_build_dir]+module_dirs:
                options.append('%s%s' % (self.module_include_switch, d))
        else:
            print 'XXX: module_dirs=%r option ignored' % (module_dirs)
            print 'XXX: Fix module_include_switch for ',self.__class__.__name__
        return options

    def library_option(self, lib):
        return "-l" + lib
    def library_dir_option(self, dir):
        return "-L" + dir

#    def _get_cc_args(self, pp_opts, debug, extra_preargs):
#        return []

    if sys.version[:3]<'2.3':
        def compile(self, sources, output_dir=None, macros=None,
                    include_dirs=None, debug=0, extra_preargs=None,
                    extra_postargs=None, depends=None):
            if output_dir is None: output_dir = self.output_dir
            if macros is None: macros = self.macros
            elif type(macros) is ListType: macros = macros + (self.macros or [])
            if include_dirs is None: include_dirs = self.include_dirs
            elif type(include_dirs) in (ListType, TupleType):
                include_dirs = list(include_dirs) + (self.include_dirs or [])
            if extra_preargs is None: extra_preargs=[]
            from distutils.sysconfig import python_build
            objects = self.object_filenames(sources,strip_dir=python_build,
                                            output_dir=output_dir)
            from distutils.ccompiler import gen_preprocess_options
            pp_opts = gen_preprocess_options(macros, include_dirs)
            build = {}
            for i in range(len(sources)):
                src,obj = sources[i],objects[i]
                ext = os.path.splitext(src)[1]
                self.mkpath(os.path.dirname(obj))
                build[obj] = src, ext
            cc_args = [] #self._get_cc_args(pp_opts, debug, extra_preargs)
            for obj, (src, ext) in build.items():
                self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)
            return objects
        def detect_language(self, sources):
            return

    def link(self, target_desc, objects,
             output_filename, output_dir=None, libraries=None,
             library_dirs=None, runtime_library_dirs=None,
             export_symbols=None, debug=0, extra_preargs=None,
             extra_postargs=None, build_temp=None, target_lang=None):
        objects, output_dir = self._fix_object_args(objects, output_dir)
        libraries, library_dirs, runtime_library_dirs = \
            self._fix_lib_args(libraries, library_dirs, runtime_library_dirs)

        lib_opts = gen_lib_options(self, library_dirs, runtime_library_dirs,
                                   libraries)
        if type(output_dir) not in (StringType, NoneType):
            raise TypeError, "'output_dir' must be a string or None"
        if output_dir is not None:
            output_filename = os.path.join(output_dir, output_filename)

        if self._need_link(objects, output_filename):
            if self.library_switch[-1]==' ':
                o_args = [self.library_switch.strip(),output_filename]
            else:
                o_args = [self.library_switch.strip()+output_filename]
            ld_args = (objects + self.objects +
                       lib_opts + o_args)
            if debug:
                ld_args[:0] = ['-g']
            if extra_preargs:
                ld_args[:0] = extra_preargs
            if extra_postargs:
                ld_args.extend(extra_postargs)
            self.mkpath(os.path.dirname(output_filename))
            if target_desc == CCompiler.EXECUTABLE:
                raise NotImplementedError,self.__class__.__name__+'.linker_exe attribute'
            else:
                linker = self.linker_so[:]
            if os.name == 'nt':
                linker = _nt_quote_args(linker)
            command = linker + ld_args
            try:
                self.spawn(command)
            except DistutilsExecError, msg:
                raise LinkError, msg
        else:
            log.debug("skipping %s (up-to-date)", output_filename)
        return

    ############################################################

    ## Private methods:

    def __get_cmd(self, command, envvar=None, confvar=None):
        if command is None:
            var = None
        elif type(command) is type(''):
            var = self.executables[command]
            if var is not None:
                var = var[0]
        else:
            var = command()
        if envvar is not None:
            var = os.environ.get(envvar, var)
        if confvar is not None:
            var = confvar[0].get(confvar[1], [None,var])[1]
        return var

    def __get_flags(self, command, envvar=None, confvar=None):
        if command is None:
            var = []
        elif type(command) is type(''):
            var = self.executables[command][1:]
        else:
            var = command()
        if envvar is not None:
            var = os.environ.get(envvar, var)
        if confvar is not None:
            var = confvar[0].get(confvar[1], [None,var])[1]
        if type(var) is type(''):
            var = split_quoted(var)
        return var

    ## class FCompiler

##############################################################################

fcompiler_class = {'gnu':('gnufcompiler','GnuFCompiler',
                          "GNU Fortran Compiler"),
                   'pg':('pgfcompiler','PGroupFCompiler',
                         "Portland Group Fortran Compiler"),
                   'absoft':('absoftfcompiler','AbsoftFCompiler',
                             "Absoft Corp Fortran Compiler"),
                   'mips':('mipsfcompiler','MipsFCompiler',
                           "MIPSpro Fortran Compiler"),
                   'sun':('sunfcompiler','SunFCompiler',
                          "Sun|Forte Fortran 95 Compiler"),
                   'intel':('intelfcompiler','IntelFCompiler',
                            "Intel Fortran Compiler for 32-bit apps"),
                   'intelv':('intelfcompiler','IntelVisualFCompiler',
                             "Intel Visual Fortran Compiler for 32-bit apps"),
                   'intele':('intelfcompiler','IntelItaniumFCompiler',
                             "Intel Fortran Compiler for Itanium apps"),
                   'intelev':('intelfcompiler','IntelItaniumVisualFCompiler',
                              "Intel Visual Fortran Compiler for Itanium apps"),
                   'nag':('nagfcompiler','NAGFCompiler',
                          "NAGWare Fortran 95 Compiler"),
                   'compaq':('compaqfcompiler','CompaqFCompiler',
                             "Compaq Fortran Compiler"),
                   'compaqv':('compaqfcompiler','CompaqVisualFCompiler',
                             "DIGITAL|Compaq Visual Fortran Compiler"),
                   'vast':('vastfcompiler','VastFCompiler',
                           "Pacific-Sierra Research Fortran 90 Compiler"),
                   'hpux':('hpuxfcompiler','HPUXFCompiler',
                           "HP Fortran 90 Compiler"),
                   'lahey':('laheyfcompiler','LaheyFCompiler',
                            "Lahey/Fujitsu Fortran 95 Compiler"),
                   'ibm':('ibmfcompiler','IbmFCompiler',
                          "IBM XL Fortran Compiler"),
                   'f':('fcompiler','FFCompiler',
                        "Fortran Company/NAG F Compiler"),
                   }

_default_compilers = (
    # Platform mappings
    ('win32',('gnu','intelv','absoft','compaqv','intelev')),
    ('cygwin.*',('gnu','intelv','absoft','compaqv','intelev')),
    ('linux.*',('gnu','intel','lahey','pg','absoft','nag','vast','compaq',
                'intele')),
    ('darwin.*',('nag','absoft','ibm','gnu')),
    ('sunos.*',('forte','gnu','sun')),
    ('irix.*',('mips','gnu')),
    ('aix.*',('ibm','gnu')),
    # OS mappings
    ('posix',('gnu',)),
    ('nt',('gnu',)),
    ('mac',('gnu',)),
    )

def _find_existing_fcompiler(compilers, osname=None, platform=None):
    for compiler in compilers:
        v = None
        try:
            c = new_fcompiler(plat=platform, compiler=compiler)
            c.customize()
            v = c.get_version()
        except DistutilsModuleError:
            pass
        except Exception, msg:
            log.warn(msg)
        if v is not None:
            return compiler
    return

def get_default_fcompiler(osname=None, platform=None):
    """ Determine the default Fortran compiler to use for the given platform. """
    if osname is None:
        osname = os.name
    if platform is None:
        platform = sys.platform
    matching_compilers = []
    for pattern, compiler in _default_compilers:
        if re.match(pattern, platform) is not None or \
               re.match(pattern, osname) is not None:
            if type(compiler) is type(()):
                matching_compilers.extend(list(compiler))
            else:
                matching_compilers.append(compiler)
    if not matching_compilers:
        matching_compilers.append('gnu')
    compiler =  _find_existing_fcompiler(matching_compilers,
                                         osname=osname,
                                         platform=platform)
    if compiler is not None:
        return compiler
    return matching_compilers[0]

def new_fcompiler(plat=None,
                  compiler=None,
                  verbose=0,
                  dry_run=0,
                  force=0):
    """ Generate an instance of some FCompiler subclass for the supplied
    platform/compiler combination.
    """
    if plat is None:
        plat = os.name
    try:
        if compiler is None:
            compiler = get_default_fcompiler(plat)
        (module_name, class_name, long_description) = fcompiler_class[compiler]
    except KeyError:
        msg = "don't know how to compile Fortran code on platform '%s'" % plat
        if compiler is not None:
            msg = msg + " with '%s' compiler." % compiler
            msg = msg + " Supported compilers are: %s)" \
                  % (','.join(fcompiler_class.keys()))
        raise DistutilsPlatformError, msg

    try:
        module_name = 'scipy_distutils.'+module_name
        __import__ (module_name)
        module = sys.modules[module_name]
        klass = vars(module)[class_name]
    except ImportError:
        raise DistutilsModuleError, \
              "can't compile Fortran code: unable to load module '%s'" % \
              module_name
    except KeyError:
        raise DistutilsModuleError, \
              ("can't compile Fortran code: unable to find class '%s' " +
               "in module '%s'") % (class_name, module_name)
    compiler = klass(None, dry_run, force)
    log.debug('new_fcompiler returns %s' % (klass))
    return compiler

def show_fcompilers(dist = None):
    """ Print list of available compilers (used by the "--help-fcompiler"
    option to "config_fc").
    """
    if dist is None:
        from dist import Distribution
        dist = Distribution()
        dist.script_name = os.path.basename(sys.argv[0])
        dist.script_args = ['config_fc'] + sys.argv[1:]
        dist.cmdclass['config_fc'] = config_fc
        dist.parse_config_files()
        dist.parse_command_line()

    compilers = []
    compilers_na = []
    compilers_ni = []
    for compiler in fcompiler_class.keys():
        v = 'N/A'
        try:
            c = new_fcompiler(compiler=compiler)
            c.customize(dist)
            v = c.get_version()
        except DistutilsModuleError:
            pass
        except Exception, msg:
            log.warn(msg)
        if v is None:
            compilers_na.append(("fcompiler="+compiler, None,
                              fcompiler_class[compiler][2]))
        elif v=='N/A':
            compilers_ni.append(("fcompiler="+compiler, None,
                                 fcompiler_class[compiler][2]))
        else:
            compilers.append(("fcompiler="+compiler, None,
                              fcompiler_class[compiler][2] + ' (%s)' % v))
    compilers.sort()
    compilers_na.sort()
    pretty_printer = FancyGetopt(compilers)
    pretty_printer.print_help("List of available Fortran compilers:")
    pretty_printer = FancyGetopt(compilers_na)
    pretty_printer.print_help("List of unavailable Fortran compilers:")
    if compilers_ni:
        pretty_printer = FancyGetopt(compilers_ni)
        pretty_printer.print_help("List of unimplemented Fortran compilers:")
    print "For compiler details, run 'config_fc --verbose' setup command."

def dummy_fortran_file():
    import tempfile
    dummy_name = tempfile.mktemp()+'__dummy'
    dummy = open(dummy_name+'.f','w')
    dummy.write("      subroutine dummy()\n      end\n")
    dummy.close()
    def rm_file(name=dummy_name,log_threshold=log._global_log.threshold):
        save_th = log._global_log.threshold
        log.set_threshold(log_threshold)
        try: os.remove(name+'.f'); log.debug('removed '+name+'.f')
        except OSError: pass
        try: os.remove(name+'.o'); log.debug('removed '+name+'.o')
        except OSError: pass
        log.set_threshold(save_th)
    atexit.register(rm_file)
    return dummy_name

is_f_file = re.compile(r'.*[.](for|ftn|f77|f)\Z',re.I).match
_has_f_header = re.compile(r'-[*]-\s*fortran\s*-[*]-',re.I).search
_has_f90_header = re.compile(r'-[*]-\s*f90\s*-[*]-',re.I).search
_free_f90_start = re.compile(r'[^c*]\s*[^\s\d\t]',re.I).match
def is_free_format(file):
    """Check if file is in free format Fortran."""
    # f90 allows both fixed and free format, assuming fixed unless
    # signs of free format are detected.
    result = 0
    f = open(file,'r')
    line = f.readline()
    n = 15 # the number of non-comment lines to scan for hints
    if _has_f_header(line):
        n = 0
    elif _has_f90_header(line):
        n = 0
        result = 1
    while n>0 and line:
        if line[0]!='!':
            n -= 1
            if (line[0]!='\t' and _free_f90_start(line[:5])) or line[-2:-1]=='&':
                result = 1
                break
        line = f.readline()
    f.close()
    return result

if __name__ == '__main__':
    show_fcompilers()

# Python 2.3 distutils.log backported to Python 2.1.x, 2.2.x

import sys

def _fix_args(args,flag=1):
    if type(args) is type(''):
        return args.replace('%','%%')
    if flag and type(args) is type(()):
        return tuple([_fix_args(a,flag=0) for a in args])
    return args

if sys.version[:3]>='2.3':
    from distutils.log import *
    from distutils.log import Log as old_Log
    from distutils.log import _global_log
    class Log(old_Log):
        def _log(self, level, msg, args):
            if level>= self.threshold:
                if args:
                    print _global_color_map[level](msg % _fix_args(args))
                else:
                    print _global_color_map[level](msg)
                sys.stdout.flush()
    _global_log.__class__ = Log

else:
    exec """
# Here follows (slightly) modified copy of Python 2.3 distutils/log.py

DEBUG = 1
INFO = 2
WARN = 3
ERROR = 4
FATAL = 5
class Log:

    def __init__(self, threshold=WARN):
        self.threshold = threshold

    def _log(self, level, msg, args):
        if level >= self.threshold:
            print _global_color_map[level](msg % _fix_args(args))
            sys.stdout.flush()

    def log(self, level, msg, *args):
        self._log(level, msg, args)

    def debug(self, msg, *args):
        self._log(DEBUG, msg, args)

    def info(self, msg, *args):
        self._log(INFO, msg, args)
    
    def warn(self, msg, *args):
        self._log(WARN, red_text(msg), args)
    
    def error(self, msg, *args):
        self._log(ERROR, msg, args)
    
    def fatal(self, msg, *args):
        self._log(FATAL, msg, args)

_global_log = Log()
log = _global_log.log
debug = _global_log.debug
info = _global_log.info
warn = _global_log.warn
error = _global_log.error
fatal = _global_log.fatal

def set_threshold(level):
    _global_log.threshold = level


"""

def set_verbosity(v):
    if v<0:
        set_threshold(ERROR)
    elif v == 0:
        set_threshold(WARN)
    elif v == 1:
        set_threshold(INFO)
    elif v >= 2:
        set_threshold(DEBUG)

from misc_util import red_text, yellow_text, cyan_text
_global_color_map = {
    DEBUG:cyan_text,
    INFO:yellow_text,
    WARN:red_text,
    ERROR:red_text,
    FATAL:red_text
}

set_verbosity(1)

""" Functions for converting from DOS to UNIX line endings
"""

import sys, re, os

def dos2unix(file):
    "Replace CRLF with LF in argument files.  Print names of changed files."    
    if os.path.isdir(file):
        print file, "Directory!"
        return
        
    data = open(file, "rb").read()
    if '\0' in data:
        print file, "Binary!"
        return
        
    newdata = re.sub("\r\n", "\n", data)
    if newdata != data:
        print 'dos2unix:', file
        f = open(file, "wb")
        f.write(newdata)
        f.close()
        return file
    else:
        print file, 'ok'    

def dos2unix_one_dir(modified_files,dir_name,file_names):
    for file in file_names:
        full_path = os.path.join(dir_name,file)
        file = dos2unix(full_path)
        if file is not None:
            modified_files.append(file)

def dos2unix_dir(dir_name):
    modified_files = []
    os.path.walk(dir_name,dos2unix_one_dir,modified_files)
    return modified_files
#----------------------------------

def unix2dos(file):
    "Replace LF with CRLF in argument files.  Print names of changed files."    
    if os.path.isdir(file):
        print file, "Directory!"
        return
        
    data = open(file, "rb").read()
    if '\0' in data:
        print file, "Binary!"
        return
    newdata = re.sub("\r\n", "\n", data)
    newdata = re.sub("\n", "\r\n", newdata)
    if newdata != data:
        print 'unix2dos:', file
        f = open(file, "wb")
        f.write(newdata)
        f.close()
        return file
    else:
        print file, 'ok'    

def unix2dos_one_dir(modified_files,dir_name,file_names):
    for file in file_names:
        full_path = os.path.join(dir_name,file)
        unix2dos(full_path)
        if file is not None:
            modified_files.append(file)

def unix2dos_dir(dir_name):
    modified_files = []
    os.path.walk(dir_name,unix2dos_one_dir,modified_files)
    return modified_files
        
if __name__ == "__main__":
    import sys
    dos2unix_dir(sys.argv[1])

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

class MipsFCompiler(FCompiler):

    compiler_type = 'mips'
    version_pattern =  r'MIPSpro Compilers: Version (?P<version>[^\s*,]*)'

    executables = {
        'version_cmd'  : ["f90", "-version"],
        'compiler_f77' : ["f77", "-f77"],
        'compiler_fix' : ["f90", "-fixedform"],
        'compiler_f90' : ["f90"],
        'linker_so'    : ["f90","-shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : None
        }
    module_dir_switch = None #XXX: fix me
    module_include_switch = None #XXX: fix me
    pic_flags = ['-KPIC']

    def get_flags(self):
        return self.pic_flags + ['-n32']
    def get_flags_opt(self):
        return ['-O3']
    def get_flags_arch(self):
        opt = []
        for a in '19 20 21 22_4k 22_5k 24 25 26 27 28 30 32_5k 32_10k'.split():
            if getattr(cpu,'is_IP%s'%a)():
                opt.append('-TARG:platform=IP%s' % a)
                break
        return opt
    def get_flags_arch_f77(self):
        r = None
        if cpu.is_r10000(): r = 10000
        elif cpu.is_r12000(): r = 12000
        elif cpu.is_r8000(): r = 8000
        elif cpu.is_r5000(): r = 5000
        elif cpu.is_r4000(): r = 4000
        if r is not None:
            return ['r%s' % (r)]
        return []
    def get_flags_arch_f90(self):
        r = self.get_flags_arch_f77()
        if r:
            r[0] = '-' + r[0]
        return r

if __name__ == '__main__':
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='mips')
    compiler.customize()
    print compiler.get_version()


# http://www.absoft.com/literature/osxuserguide.pdf
# http://www.absoft.com/documentation.html

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler, dummy_fortran_file

class AbsoftFCompiler(FCompiler):

    compiler_type = 'absoft'
    version_pattern = r'FORTRAN 77 Compiler (?P<version>[^\s*,]*).*?Absoft Corp'

    # samt5735(8)$ f90 -V -c dummy.f
    # f90: Copyright Absoft Corporation 1994-2002; Absoft Pro FORTRAN Version 8.0
    # Note that fink installs g77 as f77, so need to use f90 for detection.

    executables = {
        'version_cmd'  : ["f77", "-V -c %(fname)s.f -o %(fname)s.o" \
                          % {'fname':dummy_fortran_file()}],
        'compiler_f77' : ["f77"],
        'compiler_fix' : ["f90"],
        'compiler_f90' : ["f90"],
        'linker_so'    : ["f77","-K","shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    module_dir_switch = None
    module_include_switch = '-p'

    def get_library_dirs(self):
        opt = FCompiler.get_library_dirs(self)
        d = os.environ.get('ABSOFT')
        if d:
            opt.append(os.path.join(d,'LIB'))
        return opt

    def get_libraries(self):
        opt = FCompiler.get_libraries(self)
        opt.extend(['fio','f90math','fmath'])
        if os.name =='nt':
            opt.append('COMDLG32')
        return opt

    def get_flags(self):
        opt = FCompiler.get_flags(self)
        if os.name != 'nt':
            opt.extend(['-s'])
            if self.get_version():
                if self.get_version()>='8.2':
                    opt.append('-fpic')
        return opt

    def get_flags_f77(self):
        opt = FCompiler.get_flags_f77(self)
        opt.extend(['-N22','-N90','-N110'])
        if os.name != 'nt':
            opt.append('-f')
            if self.get_version():
                if self.get_version()<='4.6':
                    opt.append('-B108')
                else:
                    # Though -N15 is undocumented, it works with
                    # Absoft 8.0 on Linux
                    opt.append('-N15')
        return opt

    def get_flags_f90(self):
        opt = FCompiler.get_flags_f90(self)
        opt.extend(["-YCFRL=1","-YCOM_NAMES=LCS","-YCOM_PFX","-YEXT_PFX",
                    "-YCOM_SFX=_","-YEXT_SFX=_","-YEXT_NAMES=LCS"])
        if self.get_version():
            if self.get_version()>'4.6':
                opt.extend(["-YDEALLOC=ALL"])                
        return opt

    def get_flags_fix(self):
        opt = FCompiler.get_flags_fix(self)
        opt.extend(["-YCFRL=1","-YCOM_NAMES=LCS","-YCOM_PFX","-YEXT_PFX",
                    "-YCOM_SFX=_","-YEXT_SFX=_","-YEXT_NAMES=LCS"])
        opt.extend(["-f","fixed"])
        return opt

    def get_flags_opt(self):
        opt = ['-O']
        return opt

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='absoft')
    compiler.customize()
    print compiler.get_version()

import re
import sys
import os
import string

__doc__ = """This module generates a DEF file from the symbols in
an MSVC-compiled DLL import library.  It correctly discriminates between
data and functions.  The data is collected from the output of the program
nm(1).

Usage:
    python lib2def.py [libname.lib] [output.def]
or
    python lib2def.py [libname.lib] > output.def

libname.lib defaults to python<py_ver>.lib and output.def defaults to stdout

Author: Robert Kern <kernr@mail.ncifcrf.gov>
Last Update: April 30, 1999
"""

__version__ = '0.1a'

import sys

py_ver = "%d%d" % tuple(sys.version_info[:2])

DEFAULT_NM = 'nm -Cs'

DEF_HEADER = """LIBRARY		python%s.dll
;CODE		PRELOAD MOVEABLE DISCARDABLE
;DATA		PRELOAD SINGLE

EXPORTS
""" % py_ver
# the header of the DEF file

FUNC_RE = re.compile(r"^(.*) in python%s\.dll" % py_ver, re.MULTILINE)
DATA_RE = re.compile(r"^_imp__(.*) in python%s\.dll" % py_ver, re.MULTILINE)

def parse_cmd():
    """Parses the command-line arguments.

libfile, deffile = parse_cmd()"""
    if len(sys.argv) == 3:
        if sys.argv[1][-4:] == '.lib' and sys.argv[2][-4:] == '.def':
            libfile, deffile = sys.argv[1:]
        elif sys.argv[1][-4:] == '.def' and sys.argv[2][-4:] == '.lib':
            deffile, libfile = sys.argv[1:]
        else:
            print "I'm assuming that your first argument is the library"
            print "and the second is the DEF file."
    elif len(sys.argv) == 2:
        if sys.argv[1][-4:] == '.def':
            deffile = sys.argv[1]
            libfile = 'python%s.lib' % py_ver
        elif sys.argv[1][-4:] == '.lib':
            deffile = None
            libfile = sys.argv[1]
    else:
        libfile = 'python%s.lib' % py_ver
        deffile = None
    return libfile, deffile

def getnm(nm_cmd = 'nm -Cs python%s.lib' % py_ver):
    """Returns the output of nm_cmd via a pipe.

nm_output = getnam(nm_cmd = 'nm -Cs py_lib')"""
    f = os.popen(nm_cmd)
    nm_output = f.read()
    f.close()
    return nm_output

def parse_nm(nm_output):
    """Returns a tuple of lists: dlist for the list of data
symbols and flist for the list of function symbols.

dlist, flist = parse_nm(nm_output)"""
    data = DATA_RE.findall(nm_output)
    func = FUNC_RE.findall(nm_output)

    flist = []
    for sym in data:
        if sym in func and (sym[:2] == 'Py' or sym[:3] == '_Py' or sym[:4] == 'init'):
            flist.append(sym)

    dlist = []
    for sym in data:
        if sym not in flist and (sym[:2] == 'Py' or sym[:3] == '_Py'):
            dlist.append(sym)
            
    dlist.sort()
    flist.sort()
    return dlist, flist

def output_def(dlist, flist, header, file = sys.stdout):
    """Outputs the final DEF file to a file defaulting to stdout.

output_def(dlist, flist, header, file = sys.stdout)"""
    for data_sym in dlist:
        header = header + '\t%s DATA\n' % data_sym
    header = header + '\n' # blank line
    for func_sym in flist:
        header = header + '\t%s\n' % func_sym
    file.write(header)

if __name__ == '__main__':
    libfile, deffile = parse_cmd()
    if deffile is None:
        deffile = sys.stdout
    else:
        deffile = open(deffile, 'w')
    nm_cmd = '%s %s' % (DEFAULT_NM, libfile)
    nm_output = getnm(nm_cmd)
    dlist, flist = parse_nm(nm_output)
    output_def(dlist, flist, DEF_HEADER, deffile)

#!/usr/bin/env python
"""
This file defines a set of system_info classes for getting
information about various resources (libraries, library directories,
include directories, etc.) in the system. Currently, the following
classes are available:

  atlas_info
  atlas_threads_info
  atlas_blas_info
  atlas_blas_threads_info
  lapack_atlas_info
  blas_info
  lapack_info
  blas_opt_info       # usage recommended
  lapack_opt_info     # usage recommended
  fftw_info,dfftw_info,sfftw_info
  fftw_threads_info,dfftw_threads_info,sfftw_threads_info
  djbfft_info
  x11_info
  lapack_src_info
  blas_src_info
  numpy_info
  numarray_info
  boost_python_info
  agg2_info
  wx_info
  gdk_pixbuf_xlib_2_info
  gdk_pixbuf_2_info
  gdk_x11_2_info
  gtkp_x11_2_info
  gtkp_2_info
  xft_info
  freetype2_info

Usage:
    info_dict = get_info(<name>)
  where <name> is a string 'atlas','x11','fftw','lapack','blas',
  'lapack_src', 'blas_src', etc. For a complete list of allowed names,
  see the definition of get_info() function below.

  Returned info_dict is a dictionary which is compatible with
  distutils.setup keyword arguments. If info_dict == {}, then the
  asked resource is not available (system_info could not find it).

  Several *_info classes specify an environment variable to specify
  the locations of software. When setting the corresponding environment
  variable to 'None' then the software will be ignored, even when it
  is available in system.

Global parameters:
  system_info.search_static_first - search static libraries (.a)
             in precedence to shared ones (.so, .sl) if enabled.
  system_info.verbosity - output the results to stdout if enabled.

The file 'site.cfg' in the same directory as this module is read
for configuration options. The format is that used by ConfigParser (i.e.,
Windows .INI style). The section DEFAULT has options that are the default
for each section. The available sections are fftw, atlas, and x11. Appropiate
defaults are used if nothing is specified.

The order of finding the locations of resources is the following:
 1. environment variable
 2. section in site.cfg
 3. DEFAULT section in site.cfg
Only the first complete match is returned.

Example:
----------
[DEFAULT]
library_dirs = /usr/lib:/usr/local/lib:/opt/lib
include_dirs = /usr/include:/usr/local/include:/opt/include
src_dirs = /usr/local/src:/opt/src
# search static libraries (.a) in preference to shared ones (.so)
search_static_first = 0

[fftw]
fftw_libs = rfftw, fftw
fftw_opt_libs = rfftw_threaded, fftw_threaded
# if the above aren't found, look for {s,d}fftw_libs and {s,d}fftw_opt_libs

[atlas]
library_dirs = /usr/lib/3dnow:/usr/lib/3dnow/atlas
# for overriding the names of the atlas libraries
atlas_libs = lapack, f77blas, cblas, atlas

[x11]
library_dirs = /usr/X11R6/lib
include_dirs = /usr/X11R6/include
----------

Authors:
  Pearu Peterson <pearu@cens.ioc.ee>, February 2002
  David M. Cooke <cookedm@physics.mcmaster.ca>, April 2002

Copyright 2002 Pearu Peterson all rights reserved,
Pearu Peterson <pearu@cens.ioc.ee>          
Permission to use, modify, and distribute this software is given under the 
terms of the SciPy (BSD style) license.  See LICENSE.txt that came with
this distribution for specifics.

NO WARRANTY IS EXPRESSED OR IMPLIED.  USE AT YOUR OWN RISK.
"""

__revision__ = '$Id$'

import sys,os,re,types
import warnings
from distutils.errors import DistutilsError
from glob import glob
import ConfigParser
from exec_command import find_executable, exec_command

from distutils.sysconfig import get_config_vars

if sys.platform == 'win32':
    default_lib_dirs = ['C:\\'] # probably not very helpful...
    default_include_dirs = []
    default_src_dirs = ['.']
    default_x11_lib_dirs = []
    default_x11_include_dirs = []
else:
    default_lib_dirs = ['/usr/local/lib', '/opt/lib', '/usr/lib',
                        '/sw/lib']
    default_include_dirs = ['/usr/local/include',
                            '/opt/include', '/usr/include',
                            '/sw/include']
    default_src_dirs = ['.','/usr/local/src', '/opt/src','/sw/src']
    default_x11_lib_dirs = ['/usr/X11R6/lib','/usr/X11/lib','/usr/lib']
    default_x11_include_dirs = ['/usr/X11R6/include','/usr/X11/include',
                                '/usr/include']

if os.path.join(sys.prefix, 'lib') not in default_lib_dirs:
    default_lib_dirs.insert(0,os.path.join(sys.prefix, 'lib'))
    default_include_dirs.append(os.path.join(sys.prefix, 'include'))
    default_src_dirs.append(os.path.join(sys.prefix, 'src'))

default_lib_dirs = filter(os.path.isdir, default_lib_dirs)
default_include_dirs = filter(os.path.isdir, default_include_dirs)
default_src_dirs = filter(os.path.isdir, default_src_dirs)

so_ext = get_config_vars('SO')[0] or ''

def get_info(name,notfound_action=0):
    """
    notfound_action:
      0 - do nothing
      1 - display warning message
      2 - raise error
    """
    cl = {'atlas':atlas_info,  # use lapack_opt or blas_opt instead
          'atlas_threads':atlas_threads_info,                # ditto
          'atlas_blas':atlas_blas_info,
          'atlas_blas_threads':atlas_blas_threads_info,
          'lapack_atlas':lapack_atlas_info,  # use lapack_opt instead
          'lapack_atlas_threads':lapack_atlas_threads_info,  # ditto
          'x11':x11_info,
          'fftw':fftw_info,
          'dfftw':dfftw_info,
          'sfftw':sfftw_info,
          'fftw_threads':fftw_threads_info,
          'dfftw_threads':dfftw_threads_info,
          'sfftw_threads':sfftw_threads_info,
          'djbfft':djbfft_info,
          'blas':blas_info,                  # use blas_opt instead
          'lapack':lapack_info,              # use lapack_opt instead
          'lapack_src':lapack_src_info,
          'blas_src':blas_src_info,
          'numpy':numpy_info,
          'numarray':numarray_info,
          'lapack_opt':lapack_opt_info,
          'blas_opt':blas_opt_info,
          'boost_python':boost_python_info,
          'agg2':agg2_info,
          'wx':wx_info,
          'gdk_pixbuf_xlib_2':gdk_pixbuf_xlib_2_info,
          'gdk-pixbuf-xlib-2.0':gdk_pixbuf_xlib_2_info,
          'gdk_pixbuf_2':gdk_pixbuf_2_info,
          'gdk-pixbuf-2.0':gdk_pixbuf_2_info,
          'gdk_x11_2':gdk_x11_2_info,
          'gdk-x11-2.0':gdk_x11_2_info,
          'gtkp_x11_2':gtkp_x11_2_info,
          'gtk+-x11-2.0':gtkp_x11_2_info,
          'gtkp_2':gtkp_2_info,
          'gtk+-2.0':gtkp_2_info,
          'xft':xft_info,
          'freetype2':freetype2_info,
          }.get(name.lower(),system_info)
    return cl().get_info(notfound_action)

class NotFoundError(DistutilsError):
    """Some third-party program or library is not found."""

class AtlasNotFoundError(NotFoundError):
    """
    Atlas (http://math-atlas.sourceforge.net/) libraries not found.
    Directories to search for the libraries can be specified in the
    scipy_distutils/site.cfg file (section [atlas]) or by setting
    the ATLAS environment variable."""

class LapackNotFoundError(NotFoundError):
    """
    Lapack (http://www.netlib.org/lapack/) libraries not found.
    Directories to search for the libraries can be specified in the
    scipy_distutils/site.cfg file (section [lapack]) or by setting
    the LAPACK environment variable."""

class LapackSrcNotFoundError(LapackNotFoundError):
    """
    Lapack (http://www.netlib.org/lapack/) sources not found.
    Directories to search for the sources can be specified in the
    scipy_distutils/site.cfg file (section [lapack_src]) or by setting
    the LAPACK_SRC environment variable."""

class BlasNotFoundError(NotFoundError):
    """
    Blas (http://www.netlib.org/blas/) libraries not found.
    Directories to search for the libraries can be specified in the
    scipy_distutils/site.cfg file (section [blas]) or by setting
    the BLAS environment variable."""

class BlasSrcNotFoundError(BlasNotFoundError):
    """
    Blas (http://www.netlib.org/blas/) sources not found.
    Directories to search for the sources can be specified in the
    scipy_distutils/site.cfg file (section [blas_src]) or by setting
    the BLAS_SRC environment variable."""

class FFTWNotFoundError(NotFoundError):
    """
    FFTW (http://www.fftw.org/) libraries not found.
    Directories to search for the libraries can be specified in the
    scipy_distutils/site.cfg file (section [fftw]) or by setting
    the FFTW environment variable."""

class DJBFFTNotFoundError(NotFoundError):
    """
    DJBFFT (http://cr.yp.to/djbfft.html) libraries not found.
    Directories to search for the libraries can be specified in the
    scipy_distutils/site.cfg file (section [djbfft]) or by setting
    the DJBFFT environment variable."""

class F2pyNotFoundError(NotFoundError):
    """
    f2py2e (http://cens.ioc.ee/projects/f2py2e/) module not found.
    Get it from above location, install it, and retry setup.py."""

class NumericNotFoundError(NotFoundError):
    """
    Numeric (http://www.numpy.org/) module not found.
    Get it from above location, install it, and retry setup.py."""

class X11NotFoundError(NotFoundError):
    """X11 libraries not found."""

class system_info:

    """ get_info() is the only public method. Don't use others.
    """
    section = 'DEFAULT'
    dir_env_var = None
    search_static_first = 0 # XXX: disabled by default, may disappear in
                            # future unless it is proved to be useful.
    verbosity = 1
    saved_results = {}

    notfounderror = NotFoundError

    def __init__ (self,
                  default_lib_dirs=default_lib_dirs,
                  default_include_dirs=default_include_dirs,
                  verbosity = 1,
                  ):
        self.__class__.info = {}
        self.local_prefixes = []
        defaults = {}
        defaults['library_dirs'] = os.pathsep.join(default_lib_dirs)
        defaults['include_dirs'] = os.pathsep.join(default_include_dirs)
        defaults['src_dirs'] = os.pathsep.join(default_src_dirs)
        defaults['search_static_first'] = str(self.search_static_first)
        self.cp = ConfigParser.ConfigParser(defaults)
        try:
            __file__
        except NameError:
            __file__ = sys.argv[0]
        cf = os.path.join(os.path.split(os.path.abspath(__file__))[0],
                          'site.cfg')
        self.cp.read([cf])
        if not self.cp.has_section(self.section):
            self.cp.add_section(self.section)
        self.search_static_first = self.cp.getboolean(self.section,
                                                      'search_static_first')
        assert isinstance(self.search_static_first, type(0))

    def set_info(self,**info):
        self.saved_results[self.__class__.__name__] = info

    def has_info(self):
        return self.saved_results.has_key(self.__class__.__name__)

    def get_info(self,notfound_action=0):
        """ Return a dictonary with items that are compatible
            with scipy_distutils.setup keyword arguments.
        """
        flag = 0
        if not self.has_info():
            flag = 1
            if self.verbosity>0:
                print self.__class__.__name__ + ':'
            if hasattr(self, 'calc_info'):
                self.calc_info()
            if notfound_action:
                if not self.has_info():
                    if notfound_action==1:
                        warnings.warn(self.notfounderror.__doc__)
                    elif notfound_action==2:
                        raise self.notfounderror,self.notfounderror.__doc__
                    else:
                        raise ValueError,`notfound_action`

            if self.verbosity>0:
                if not self.has_info():
                    print '  NOT AVAILABLE'
                    self.set_info()
                else:
                    print '  FOUND:'
            
        res = self.saved_results.get(self.__class__.__name__)
        if self.verbosity>0 and flag:
            for k,v in res.items():
                v = str(v)
                if k=='sources' and len(v)>200: v = v[:60]+' ...\n... '+v[-60:]
                print '    %s = %s'%(k,v)
            print
        
        return res

    def get_paths(self, section, key):
        dirs = self.cp.get(section, key).split(os.pathsep)
        if self.dir_env_var and os.environ.has_key(self.dir_env_var):
            d = os.environ[self.dir_env_var]
            if d=='None':
                print 'Disabled',self.__class__.__name__,'(%s is None)' % (self.dir_env_var)
                return []
            if os.path.isfile(d):
                dirs = [os.path.dirname(d)] + dirs
                l = getattr(self,'_lib_names',[])
                if len(l)==1:
                    b = os.path.basename(d)
                    b = os.path.splitext(b)[0]
                    if b[:3]=='lib':
                        print 'Replacing _lib_names[0]==%r with %r' \
                              % (self._lib_names[0], b[3:])
                        self._lib_names[0] = b[3:]
            else:
                dirs = d.split(os.pathsep) + dirs
        default_dirs = self.cp.get('DEFAULT', key).split(os.pathsep)
        dirs.extend(default_dirs)
        ret = []
        [ret.append(d) for d in dirs if os.path.isdir(d) and d not in ret]
        if self.verbosity>1:
            print '(',key,'=',':'.join(ret),')'
        return ret

    def get_lib_dirs(self, key='library_dirs'):
        return self.get_paths(self.section, key)

    def get_include_dirs(self, key='include_dirs'):
        return self.get_paths(self.section, key)

    def get_src_dirs(self, key='src_dirs'):
        return self.get_paths(self.section, key)

    def get_libs(self, key, default):
        try:
            libs = self.cp.get(self.section, key)
        except ConfigParser.NoOptionError:
            return default
        return [a.strip() for a in libs.split(',')]

    def check_libs(self,lib_dir,libs,opt_libs =[]):
        """ If static or shared libraries are available then return
            their info dictionary. """
        if self.search_static_first:
            exts = ['.a',so_ext]
        else:
            exts = [so_ext,'.a']
        if sys.platform=='cygwin':
            exts.append('.dll.a')
        for ext in exts:
            info = self._check_libs(lib_dir,libs,opt_libs,ext)
            if info is not None: return info

    def _lib_list(self, lib_dir, libs, ext):
        assert type(lib_dir) is type('')
        liblist = []
        for l in libs:
            p = self.combine_paths(lib_dir, 'lib'+l+ext)
            if p:
                assert len(p)==1
                liblist.append(p[0])
        return liblist

    def _extract_lib_names(self,libs):
        return [os.path.splitext(os.path.basename(p))[0][3:] \
                for p in libs]

    def _check_libs(self,lib_dir,libs, opt_libs, ext):
        found_libs = self._lib_list(lib_dir, libs, ext)
        if len(found_libs) == len(libs):
            found_libs = self._extract_lib_names(found_libs)
            info = {'libraries' : found_libs, 'library_dirs' : [lib_dir]}
            opt_found_libs = self._lib_list(lib_dir, opt_libs, ext)
            if len(opt_found_libs) == len(opt_libs):
                opt_found_libs = self._extract_lib_names(opt_found_libs)
                info['libraries'].extend(opt_found_libs)
            return info

    def combine_paths(self,*args):
        return combine_paths(*args,**{'verbosity':self.verbosity})

class fftw_info(system_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    libs = ['rfftw', 'fftw']
    includes = ['fftw.h','rfftw.h']
    macros = [('SCIPY_FFTW_H',None)]
    notfounderror = FFTWNotFoundError

    def __init__(self):
        system_info.__init__(self)

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()
        incl_dirs = self.get_include_dirs()
        incl_dir = None
        libs = self.get_libs(self.section+'_libs', self.libs)
        info = None
        for d in lib_dirs:
            r = self.check_libs(d,libs)
            if r is not None:
                info = r
                break
        if info is not None:
            flag = 0
            for d in incl_dirs:
                if len(self.combine_paths(d,self.includes))==2:
                    dict_append(info,include_dirs=[d])
                    flag = 1
                    incl_dirs = [d]
                    incl_dir = d
                    break
            if flag:
                dict_append(info,define_macros=self.macros)
            else:
                info = None
        if info is not None:
            self.set_info(**info)

class dfftw_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    libs = ['drfftw','dfftw']
    includes = ['dfftw.h','drfftw.h']
    macros = [('SCIPY_DFFTW_H',None)]

class sfftw_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    libs = ['srfftw','sfftw']
    includes = ['sfftw.h','srfftw.h']
    macros = [('SCIPY_SFFTW_H',None)]

class fftw_threads_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    libs = ['rfftw_threads','fftw_threads']
    includes = ['fftw_threads.h','rfftw_threads.h']
    macros = [('SCIPY_FFTW_THREADS_H',None)]

class dfftw_threads_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    libs = ['drfftw_threads','dfftw_threads']
    includes = ['dfftw_threads.h','drfftw_threads.h']
    macros = [('SCIPY_DFFTW_THREADS_H',None)]

class sfftw_threads_info(fftw_info):
    section = 'fftw'
    dir_env_var = 'FFTW'
    libs = ['srfftw_threads','sfftw_threads']
    includes = ['sfftw_threads.h','srfftw_threads.h']
    macros = [('SCIPY_SFFTW_THREADS_H',None)]

class djbfft_info(system_info):
    section = 'djbfft'
    dir_env_var = 'DJBFFT'
    notfounderror = DJBFFTNotFoundError

    def get_paths(self, section, key):
        pre_dirs = system_info.get_paths(self, section, key)
        dirs = []
        for d in pre_dirs:
            dirs.extend(self.combine_paths(d,['djbfft'])+[d])
        return [ d for d in dirs if os.path.isdir(d) ]

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()
        incl_dirs = self.get_include_dirs()
        info = None
        for d in lib_dirs:
            p = self.combine_paths (d,['djbfft.a'])
            if p:
                info = {'extra_objects':p}
                break
            p = self.combine_paths (d,['libdjbfft.a'])
            if p:
                info = {'libraries':['djbfft'],'library_dirs':[d]}
                break
        if info is None:
            return
        for d in incl_dirs:
            if len(self.combine_paths(d,['fftc8.h','fftfreq.h']))==2:
                dict_append(info,include_dirs=[d],
                            define_macros=[('SCIPY_DJBFFT_H',None)])
                self.set_info(**info)
                return


class atlas_info(system_info):
    section = 'atlas'
    dir_env_var = 'ATLAS'
    _lib_names = ['f77blas','cblas']
    notfounderror = AtlasNotFoundError

    def get_paths(self, section, key):
        pre_dirs = system_info.get_paths(self, section, key)
        dirs = []
        for d in pre_dirs:
            dirs.extend(self.combine_paths(d,['atlas*','ATLAS*',
                                         'sse','3dnow','sse2'])+[d])
        return [ d for d in dirs if os.path.isdir(d) ]

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()
        info = {}
        atlas_libs = self.get_libs('atlas_libs',
                                   self._lib_names + ['atlas'])
        lapack_libs = self.get_libs('lapack_libs',['lapack'])
        atlas = None
        lapack = None
        atlas_1 = None
        for d in lib_dirs:
            atlas = self.check_libs(d,atlas_libs,[])
            lapack_atlas = self.check_libs(d,['lapack_atlas'],[])
            if atlas is not None:
                lib_dirs2 = self.combine_paths(d,['atlas*','ATLAS*'])+[d]
                for d2 in lib_dirs2:
                    lapack = self.check_libs(d2,lapack_libs,[])
                    if lapack is not None:
                        break
                else:
                    lapack = None
                if lapack is not None:
                    break
            if atlas:
                atlas_1 = atlas
        print self.__class__
        if atlas is None:
            atlas = atlas_1
        if atlas is None:
            return
        include_dirs = self.get_include_dirs()
        h = (self.combine_paths(lib_dirs+include_dirs,'cblas.h') or [None])[0]
        if h:
            h = os.path.dirname(h)
            dict_append(info,include_dirs=[h])
        info['language'] = 'c'
        if lapack is not None:
            dict_append(info,**lapack)
            dict_append(info,**atlas)
        elif 'lapack_atlas' in atlas['libraries']:
            dict_append(info,**atlas)
            dict_append(info,define_macros=[('ATLAS_WITH_LAPACK_ATLAS',None)])
            self.set_info(**info)
            return
        else:
            dict_append(info,**atlas)
            dict_append(info,define_macros=[('ATLAS_WITHOUT_LAPACK',None)])
            message = """
*********************************************************************
    Could not find lapack library within the ATLAS installation.
*********************************************************************
"""
            warnings.warn(message)
            self.set_info(**info)
            return
        # Check if lapack library is complete, only warn if it is not.
        lapack_dir = lapack['library_dirs'][0]
        lapack_name = lapack['libraries'][0]
        lapack_lib = None
        for e in ['.a',so_ext]:
            fn = os.path.join(lapack_dir,'lib'+lapack_name+e)
            if os.path.exists(fn):
                lapack_lib = fn
                break
        if lapack_lib is not None:
            sz = os.stat(lapack_lib)[6]
            if sz <= 4000*1024:
                message = """
*********************************************************************
    Lapack library (from ATLAS) is probably incomplete:
      size of %s is %sk (expected >4000k)

    Follow the instructions in the KNOWN PROBLEMS section of the file
    scipy/INSTALL.txt.
*********************************************************************
""" % (lapack_lib,sz/1024)
                warnings.warn(message)
            else:
                info['language'] = 'f77'

        self.set_info(**info)

class atlas_blas_info(atlas_info):
    _lib_names = ['f77blas','cblas']

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()
        info = {}
        atlas_libs = self.get_libs('atlas_libs',
                                   self._lib_names + ['atlas'])
        atlas = None
        atlas_1 = None
        for d in lib_dirs:
            atlas = self.check_libs(d,atlas_libs,[])
            if atlas is not None:
                lib_dirs2 = self.combine_paths(d,['atlas*','ATLAS*'])+[d]
            if atlas:
                atlas_1 = atlas
        print self.__class__
        if atlas is None:
            atlas = atlas_1
        if atlas is None:
            return
        include_dirs = self.get_include_dirs()
        h = (self.combine_paths(lib_dirs+include_dirs,'cblas.h') or [None])[0]
        if h:
            h = os.path.dirname(h)
            dict_append(info,include_dirs=[h])
        info['language'] = 'c'

        dict_append(info,**atlas)

        self.set_info(**info)
        return

class atlas_threads_info(atlas_info):
    _lib_names = ['ptf77blas','ptcblas']

class atlas_blas_threads_info(atlas_blas_info):
    _lib_names = ['ptf77blas','ptcblas']

class lapack_atlas_info(atlas_info):
    _lib_names = ['lapack_atlas'] + atlas_info._lib_names

class lapack_atlas_threads_info(atlas_threads_info):
    _lib_names = ['lapack_atlas'] + atlas_threads_info._lib_names

class lapack_info(system_info):
    section = 'lapack'
    dir_env_var = 'LAPACK'
    _lib_names = ['lapack']
    notfounderror = LapackNotFoundError

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()

        lapack_libs = self.get_libs('lapack_libs', self._lib_names)
        for d in lib_dirs:
            lapack = self.check_libs(d,lapack_libs,[])
            if lapack is not None:
                info = lapack                
                break
        else:
            return
        info['language'] = 'f77'
        self.set_info(**info)

class lapack_src_info(system_info):
    section = 'lapack_src'
    dir_env_var = 'LAPACK_SRC'
    notfounderror = LapackSrcNotFoundError

    def get_paths(self, section, key):
        pre_dirs = system_info.get_paths(self, section, key)
        dirs = []
        for d in pre_dirs:
            dirs.extend([d] + self.combine_paths(d,['LAPACK*/SRC','SRC']))
        return [ d for d in dirs if os.path.isdir(d) ]

    def calc_info(self):
        src_dirs = self.get_src_dirs()
        src_dir = ''
        for d in src_dirs:
            if os.path.isfile(os.path.join(d,'dgesv.f')):
                src_dir = d
                break
        if not src_dir:
            #XXX: Get sources from netlib. May be ask first.
            return
        # The following is extracted from LAPACK-3.0/SRC/Makefile
        allaux='''
        ilaenv ieeeck lsame lsamen xerbla
        ''' # *.f
        laux = '''
        bdsdc bdsqr disna labad lacpy ladiv lae2 laebz laed0 laed1
        laed2 laed3 laed4 laed5 laed6 laed7 laed8 laed9 laeda laev2
        lagtf lagts lamch lamrg lanst lapy2 lapy3 larnv larrb larre
        larrf lartg laruv las2 lascl lasd0 lasd1 lasd2 lasd3 lasd4
        lasd5 lasd6 lasd7 lasd8 lasd9 lasda lasdq lasdt laset lasq1
        lasq2 lasq3 lasq4 lasq5 lasq6 lasr lasrt lassq lasv2 pttrf
        stebz stedc steqr sterf
        ''' # [s|d]*.f
        lasrc = '''
        gbbrd gbcon gbequ gbrfs gbsv gbsvx gbtf2 gbtrf gbtrs gebak
        gebal gebd2 gebrd gecon geequ gees geesx geev geevx gegs gegv
        gehd2 gehrd gelq2 gelqf gels gelsd gelss gelsx gelsy geql2
        geqlf geqp3 geqpf geqr2 geqrf gerfs gerq2 gerqf gesc2 gesdd
        gesv gesvd gesvx getc2 getf2 getrf getri getrs ggbak ggbal
        gges ggesx ggev ggevx ggglm gghrd gglse ggqrf ggrqf ggsvd
        ggsvp gtcon gtrfs gtsv gtsvx gttrf gttrs gtts2 hgeqz hsein
        hseqr labrd lacon laein lags2 lagtm lahqr lahrd laic1 lals0
        lalsa lalsd langb lange langt lanhs lansb lansp lansy lantb
        lantp lantr lapll lapmt laqgb laqge laqp2 laqps laqsb laqsp
        laqsy lar1v lar2v larf larfb larfg larft larfx largv larrv
        lartv larz larzb larzt laswp lasyf latbs latdf latps latrd
        latrs latrz latzm lauu2 lauum pbcon pbequ pbrfs pbstf pbsv
        pbsvx pbtf2 pbtrf pbtrs pocon poequ porfs posv posvx potf2
        potrf potri potrs ppcon ppequ pprfs ppsv ppsvx pptrf pptri
        pptrs ptcon pteqr ptrfs ptsv ptsvx pttrs ptts2 spcon sprfs
        spsv spsvx sptrf sptri sptrs stegr stein sycon syrfs sysv
        sysvx sytf2 sytrf sytri sytrs tbcon tbrfs tbtrs tgevc tgex2
        tgexc tgsen tgsja tgsna tgsy2 tgsyl tpcon tprfs tptri tptrs
        trcon trevc trexc trrfs trsen trsna trsyl trti2 trtri trtrs
        tzrqf tzrzf
        ''' # [s|c|d|z]*.f
        sd_lasrc = '''
        laexc lag2 lagv2 laln2 lanv2 laqtr lasy2 opgtr opmtr org2l
        org2r orgbr orghr orgl2 orglq orgql orgqr orgr2 orgrq orgtr
        orm2l orm2r ormbr ormhr orml2 ormlq ormql ormqr ormr2 ormr3
        ormrq ormrz ormtr rscl sbev sbevd sbevx sbgst sbgv sbgvd sbgvx
        sbtrd spev spevd spevx spgst spgv spgvd spgvx sptrd stev stevd
        stevr stevx syev syevd syevr syevx sygs2 sygst sygv sygvd
        sygvx sytd2 sytrd
        ''' # [s|d]*.f
        cz_lasrc = '''
        bdsqr hbev hbevd hbevx hbgst hbgv hbgvd hbgvx hbtrd hecon heev
        heevd heevr heevx hegs2 hegst hegv hegvd hegvx herfs hesv
        hesvx hetd2 hetf2 hetrd hetrf hetri hetrs hpcon hpev hpevd
        hpevx hpgst hpgv hpgvd hpgvx hprfs hpsv hpsvx hptrd hptrf
        hptri hptrs lacgv lacp2 lacpy lacrm lacrt ladiv laed0 laed7
        laed8 laesy laev2 lahef lanhb lanhe lanhp lanht laqhb laqhe
        laqhp larcm larnv lartg lascl laset lasr lassq pttrf rot spmv
        spr stedc steqr symv syr ung2l ung2r ungbr unghr ungl2 unglq
        ungql ungqr ungr2 ungrq ungtr unm2l unm2r unmbr unmhr unml2
        unmlq unmql unmqr unmr2 unmr3 unmrq unmrz unmtr upgtr upmtr
        ''' # [c|z]*.f
        #######
        sclaux = laux + ' econd '                  # s*.f
        dzlaux = laux + ' secnd '                  # d*.f
        slasrc = lasrc + sd_lasrc                  # s*.f
        dlasrc = lasrc + sd_lasrc                  # d*.f
        clasrc = lasrc + cz_lasrc + ' srot srscl ' # c*.f
        zlasrc = lasrc + cz_lasrc + ' drot drscl ' # z*.f
        oclasrc = ' icmax1 scsum1 '                # *.f
        ozlasrc = ' izmax1 dzsum1 '                # *.f
        sources = ['s%s.f'%f for f in (sclaux+slasrc).split()] \
                  + ['d%s.f'%f for f in (dzlaux+dlasrc).split()] \
                  + ['c%s.f'%f for f in (clasrc).split()] \
                  + ['z%s.f'%f for f in (zlasrc).split()] \
                  + ['%s.f'%f for f in (allaux+oclasrc+ozlasrc).split()]
        sources = [os.path.join(src_dir,f) for f in sources]
        #XXX: should we check here actual existence of source files?
        info = {'sources':sources,'language':'f77'}
        self.set_info(**info)

atlas_version_c_text = r'''
/* This file is generated from scipy_distutils/system_info.py */
#ifdef __CPLUSPLUS__
extern "C" {
#endif
#include "Python.h"
static PyMethodDef module_methods[] = { {NULL,NULL} };
DL_EXPORT(void) initatlas_version(void) {
  void ATL_buildinfo(void);
  ATL_buildinfo();
  Py_InitModule("atlas_version", module_methods);
}
#ifdef __CPLUSCPLUS__
}
#endif
'''

def get_atlas_version(**config):
    from core import Extension, setup
    import log
    magic = hex(hash(`config`))
    def atlas_version_c(extension, build_dir,magic=magic):
        source = os.path.join(build_dir,'atlas_version_%s.c' % (magic))
        if os.path.isfile(source):
            from distutils.dep_util import newer
            if newer(source,__file__):
                return source
        f = open(source,'w')
        f.write(atlas_version_c_text)
        f.close()
        return source
    ext = Extension('atlas_version',
                    sources=[atlas_version_c],
                    **config)
    extra_args = []
    for a in sys.argv:
        if re.match('[-][-]compiler[=]',a):
            extra_args.append(a)
    try:
        dist = setup(ext_modules=[ext],
                     script_name = 'get_atlas_version',
                     script_args = ['build_src','build_ext']+extra_args)
    except Exception,msg:
        print "##### msg: %s" % msg
        if not msg:
            msg = "Unknown Exception"
        log.warn(msg)
        return None

    from distutils.sysconfig import get_config_var
    so_ext = get_config_var('SO')
    build_ext = dist.get_command_obj('build_ext')
    target = os.path.join(build_ext.build_lib,'atlas_version'+so_ext)
    from exec_command import exec_command,get_pythonexe
    cmd = [get_pythonexe(),'-c',
           '"import imp;imp.load_dynamic(\\"atlas_version\\",\\"%s\\")"'\
           % (os.path.basename(target))]
    s,o = exec_command(cmd,execute_in=os.path.dirname(target),use_tee=0)
    atlas_version = None
    if not s:
        m = re.match(r'ATLAS version (?P<version>\d+[.]\d+[.]\d+)',o)
        if m:
            atlas_version = m.group('version')
    if atlas_version is None:
        if re.search(r'undefined symbol: ATL_buildinfo',o,re.M):
            atlas_version = '3.2.1_pre3.3.6'
        else:
            print 'Command:',' '.join(cmd)
            print 'Status:',s
            print 'Output:',o
    return atlas_version


class lapack_opt_info(system_info):
    
    def calc_info(self):

        if sys.platform=='darwin' and not os.environ.get('ATLAS',None):
            args = []
            link_args = []
            if os.path.exists('/System/Library/Frameworks/Accelerate.framework/'):
                args.extend(['-faltivec','-framework','Accelerate'])
                link_args.extend(['-Wl,-framework','-Wl,Accelerate'])
            elif os.path.exists('/System/Library/Frameworks/vecLib.framework/'):
                args.extend(['-faltivec','-framework','vecLib'])
                link_args.extend(['-Wl,-framework','-Wl,vecLib'])
            if args:
                self.set_info(extra_compile_args=args,
                              extra_link_args=link_args,
                              define_macros=[('NO_ATLAS_INFO',3)])
                return

        atlas_info = get_info('atlas_threads')
        if not atlas_info:
            atlas_info = get_info('atlas')
        #atlas_info = {} ## uncomment for testing
        atlas_version = None
        need_lapack = 0
        need_blas = 0
        info = {}
        if atlas_info:
            version_info = atlas_info.copy()
            version_info['libraries'] = [version_info['libraries'][-1]]
            atlas_version = get_atlas_version(**version_info)
            if not atlas_info.has_key('define_macros'):
                atlas_info['define_macros'] = []
            if atlas_version is None:
                atlas_info['define_macros'].append(('NO_ATLAS_INFO',2))
            else:
                atlas_info['define_macros'].append(('ATLAS_INFO',
                                                    '"\\"%s\\""' % atlas_version))
            l = atlas_info.get('define_macros',[])
            if ('ATLAS_WITH_LAPACK_ATLAS',None) in l \
                   or ('ATLAS_WITHOUT_LAPACK',None) in l:
                need_lapack = 1
            info = atlas_info
        else:
            warnings.warn(AtlasNotFoundError.__doc__)
            need_blas = 1
            need_lapack = 1
            dict_append(info,define_macros=[('NO_ATLAS_INFO',1)])

        if need_lapack:
            lapack_info = get_info('lapack')
            #lapack_info = {} ## uncomment for testing
            if lapack_info:
                dict_append(info,**lapack_info)
            else:
                warnings.warn(LapackNotFoundError.__doc__)
                lapack_src_info = get_info('lapack_src')
                if not lapack_src_info:
                    warnings.warn(LapackSrcNotFoundError.__doc__)
                    return
                dict_append(info,libraries=[('flapack_src',lapack_src_info)])

        if need_blas:
            blas_info = get_info('blas')
            #blas_info = {} ## uncomment for testing
            if blas_info:
                dict_append(info,**blas_info)
            else:
                warnings.warn(BlasNotFoundError.__doc__)
                blas_src_info = get_info('blas_src')
                if not blas_src_info:
                    warnings.warn(BlasSrcNotFoundError.__doc__)
                    return
                dict_append(info,libraries=[('fblas_src',blas_src_info)])

        self.set_info(**info)
        return


class blas_opt_info(system_info):
    
    def calc_info(self):

        if sys.platform=='darwin' and not os.environ.get('ATLAS',None):
            args = []
            link_args = []
            if os.path.exists('/System/Library/Frameworks/Accelerate.framework/'):
                args.extend(['-faltivec','-framework','Accelerate'])
                link_args.extend(['-Wl,-framework','-Wl,Accelerate'])
            elif os.path.exists('/System/Library/Frameworks/vecLib.framework/'):
                args.extend(['-faltivec','-framework','vecLib'])
                link_args.extend(['-Wl,-framework','-Wl,vecLib'])
            if args:
                self.set_info(extra_compile_args=args,
                              extra_link_args=link_args,
                              define_macros=[('NO_ATLAS_INFO',3)])
                return

        atlas_info = get_info('atlas_blas_threads')
        if not atlas_info:
            atlas_info = get_info('atlas_blas')
        atlas_version = None
        need_blas = 0
        info = {}
        if atlas_info:
            version_info = atlas_info.copy()
            version_info['libraries'] = [version_info['libraries'][-1]]
            atlas_version = get_atlas_version(**version_info)
            if not atlas_info.has_key('define_macros'):
                atlas_info['define_macros'] = []
            if atlas_version is None:
                atlas_info['define_macros'].append(('NO_ATLAS_INFO',2))
            else:
                atlas_info['define_macros'].append(('ATLAS_INFO',
                                                    '"\\"%s\\""' % atlas_version))
            info = atlas_info
        else:
            warnings.warn(AtlasNotFoundError.__doc__)
            need_blas = 1
            dict_append(info,define_macros=[('NO_ATLAS_INFO',1)])

        if need_blas:
            blas_info = get_info('blas')
            if blas_info:
                dict_append(info,**blas_info)
            else:
                warnings.warn(BlasNotFoundError.__doc__)
                blas_src_info = get_info('blas_src')
                if not blas_src_info:
                    warnings.warn(BlasSrcNotFoundError.__doc__)
                    return
                dict_append(info,libraries=[('fblas_src',blas_src_info)])

        self.set_info(**info)
        return


class blas_info(system_info):
    section = 'blas'
    dir_env_var = 'BLAS'
    _lib_names = ['blas']
    notfounderror = BlasNotFoundError

    def calc_info(self):
        lib_dirs = self.get_lib_dirs()

        blas_libs = self.get_libs('blas_libs', self._lib_names)
        for d in lib_dirs:
            blas = self.check_libs(d,blas_libs,[])
            if blas is not None:
                info = blas                
                break
        else:
            return
        info['language'] = 'f77'  # XXX: is it generally true?
        self.set_info(**info)


class blas_src_info(system_info):
    section = 'blas_src'
    dir_env_var = 'BLAS_SRC'
    notfounderror = BlasSrcNotFoundError

    def get_paths(self, section, key):
        pre_dirs = system_info.get_paths(self, section, key)
        dirs = []
        for d in pre_dirs:
            dirs.extend([d] + self.combine_paths(d,['blas']))
        return [ d for d in dirs if os.path.isdir(d) ]

    def calc_info(self):
        src_dirs = self.get_src_dirs()
        src_dir = ''
        for d in src_dirs:
            if os.path.isfile(os.path.join(d,'daxpy.f')):
                src_dir = d
                break
        if not src_dir:
            #XXX: Get sources from netlib. May be ask first.
            return
        blas1 = '''
        caxpy csscal dnrm2 dzasum saxpy srotg zdotc ccopy cswap drot
        dznrm2 scasum srotm zdotu cdotc dasum drotg icamax scnrm2
        srotmg zdrot cdotu daxpy drotm idamax scopy sscal zdscal crotg
        dcabs1 drotmg isamax sdot sswap zrotg cscal dcopy dscal izamax
        snrm2 zaxpy zscal csrot ddot dswap sasum srot zcopy zswap
        '''
        blas2 = '''
        cgbmv chpmv ctrsv dsymv dtrsv sspr2 strmv zhemv ztpmv cgemv
        chpr dgbmv dsyr lsame ssymv strsv zher ztpsv cgerc chpr2 dgemv
        dsyr2 sgbmv ssyr xerbla zher2 ztrmv cgeru ctbmv dger dtbmv
        sgemv ssyr2 zgbmv zhpmv ztrsv chbmv ctbsv dsbmv dtbsv sger
        stbmv zgemv zhpr chemv ctpmv dspmv dtpmv ssbmv stbsv zgerc
        zhpr2 cher ctpsv dspr dtpsv sspmv stpmv zgeru ztbmv cher2
        ctrmv dspr2 dtrmv sspr stpsv zhbmv ztbsv
        '''
        blas3 = '''
        cgemm csymm ctrsm dsyrk sgemm strmm zhemm zsyr2k chemm csyr2k
        dgemm dtrmm ssymm strsm zher2k zsyrk cher2k csyrk dsymm dtrsm
        ssyr2k zherk ztrmm cherk ctrmm dsyr2k ssyrk zgemm zsymm ztrsm
        '''
        sources = [os.path.join(src_dir,f+'.f') \
                   for f in (blas1+blas2+blas3).split()]
        #XXX: should we check here actual existence of source files?
        info = {'sources':sources,'language':'f77'}
        self.set_info(**info)

class x11_info(system_info):
    section = 'x11'
    notfounderror = X11NotFoundError

    def __init__(self):
        system_info.__init__(self,
                             default_lib_dirs=default_x11_lib_dirs,
                             default_include_dirs=default_x11_include_dirs)

    def calc_info(self):
        if sys.platform  in ['win32']:
            return
        lib_dirs = self.get_lib_dirs()
        include_dirs = self.get_include_dirs()
        x11_libs = self.get_libs('x11_libs', ['X11'])
        for lib_dir in lib_dirs:
            info = self.check_libs(lib_dir, x11_libs, [])
            if info is not None:
                break
        else:
            return
        inc_dir = None
        for d in include_dirs:
            if self.combine_paths(d, 'X11/X.h'):
                inc_dir = d
                break
        if inc_dir is not None:
            dict_append(info, include_dirs=[inc_dir])
        self.set_info(**info)

class numpy_info(system_info):
    section = 'numpy'
    modulename = 'Numeric'
    notfounderror = NumericNotFoundError

    def __init__(self):
        from distutils.sysconfig import get_python_inc
        include_dirs = []
        try:
            module = __import__(self.modulename)
            prefix = []
            for name in module.__file__.split(os.sep):
                if name=='lib':
                    break
                prefix.append(name)
            include_dirs.append(get_python_inc(prefix=os.sep.join(prefix)))
        except ImportError:
            pass
        py_incl_dir = get_python_inc()
        include_dirs.append(py_incl_dir)
        for d in default_include_dirs:
            d = os.path.join(d, os.path.basename(py_incl_dir))
            if d not in include_dirs:
                include_dirs.append(d)
        system_info.__init__(self,
                             default_lib_dirs=[],
                             default_include_dirs=include_dirs)

    def calc_info(self):
        try:
            module = __import__(self.modulename)
        except ImportError:
            return
        info = {}
        macros = [(self.modulename.upper()+'_VERSION',
                   '"\\"%s\\""' % (module.__version__))]
##         try:
##             macros.append(
##                 (self.modulename.upper()+'_VERSION_HEX',
##                  hex(vstr2hex(module.__version__))),
##                 )
##         except Exception,msg:
##             print msg
        dict_append(info, define_macros = macros)
        include_dirs = self.get_include_dirs()
        inc_dir = None
        for d in include_dirs:
            if self.combine_paths(d,
                                  os.path.join(self.modulename,
                                               'arrayobject.h')):
                inc_dir = d
                break
        if inc_dir is not None:
            dict_append(info, include_dirs=[inc_dir])
        if info:
            self.set_info(**info)
        return

class numarray_info(numpy_info):
    section = 'numarray'
    modulename = 'numarray'

class boost_python_info(system_info):
    section = 'boost_python'
    dir_env_var = 'BOOST'

    def get_paths(self, section, key):
        pre_dirs = system_info.get_paths(self, section, key)
        dirs = []
        for d in pre_dirs:
            dirs.extend([d] + self.combine_paths(d,['boost*']))
        return [ d for d in dirs if os.path.isdir(d) ]

    def calc_info(self):
        from distutils.sysconfig import get_python_inc
        src_dirs = self.get_src_dirs()
        src_dir = ''
        for d in src_dirs:
            if os.path.isfile(os.path.join(d,'libs','python','src','module.cpp')):
                src_dir = d
                break
        if not src_dir:
            return
        py_incl_dir = get_python_inc()
        srcs_dir = os.path.join(src_dir,'libs','python','src')
        bpl_srcs = glob(os.path.join(srcs_dir,'*.cpp'))
        bpl_srcs += glob(os.path.join(srcs_dir,'*','*.cpp'))
        info = {'libraries':[('boost_python_src',{'include_dirs':[src_dir,py_incl_dir],
                                                  'sources':bpl_srcs})],
                'include_dirs':[src_dir],
                }
        if info:
            self.set_info(**info)
        return

class agg2_info(system_info):
    section = 'agg2'
    dir_env_var = 'AGG2'

    def get_paths(self, section, key):
        pre_dirs = system_info.get_paths(self, section, key)
        dirs = []
        for d in pre_dirs:
            dirs.extend([d] + self.combine_paths(d,['agg2*']))
        return [ d for d in dirs if os.path.isdir(d) ]

    def calc_info(self):
        src_dirs = self.get_src_dirs()
        src_dir = ''
        for d in src_dirs:
            if os.path.isfile(os.path.join(d,'src','agg_affine_matrix.cpp')):
                src_dir = d
                break
        if not src_dir:
            return
        if sys.platform=='win32':
            agg2_srcs = glob(os.path.join(src_dir,'src','platform','win32','agg_win32_bmp.cpp'))
        else:
            agg2_srcs = glob(os.path.join(src_dir,'src','*.cpp'))
            agg2_srcs += [os.path.join(src_dir,'src','platform','X11','agg_platform_support.cpp')]
        
        info = {'libraries':[('agg2_src',{'sources':agg2_srcs,
                                          'include_dirs':[os.path.join(src_dir,'include')],
                                          })],
                'include_dirs':[os.path.join(src_dir,'include')],
                }
        if info:
            self.set_info(**info)
        return

class _pkg_config_info(system_info):
    section = None
    config_env_var = 'PKG_CONFIG'
    default_config_exe = 'pkg-config'
    append_config_exe = ''
    version_macro_name = None
    release_macro_name = None
    version_flag = '--modversion'

    def get_config_exe(self):
        if os.environ.has_key(self.config_env_var):
            return os.environ[self.config_env_var]
        return self.default_config_exe
    def get_config_output(self, config_exe, option):
        s,o = exec_command(config_exe+' '+self.append_config_exe+' '+option,use_tee=0)
        if not s:
            return o

    def calc_info(self):
        config_exe = find_executable(self.get_config_exe())
        if not os.path.isfile(config_exe):
            print 'File not found: %s. Cannot determine %s info.' \
                  % (config_exe, self.section)
            return
        info = {}
        macros = []
        libraries = []
        library_dirs = []
        include_dirs = []
        extra_link_args = []
        extra_compile_args = []
        version = self.get_config_output(config_exe,self.version_flag)
        if version:
            macros.append((self.__class__.__name__.split('.')[-1].upper(),
                           '"\\"%s\\""' % (version)))
            if self.version_macro_name:
                macros.append((self.version_macro_name+'_%s' % (version.replace('.','_')),None))
        if self.release_macro_name:
            release = self.get_config_output(config_exe,'--release')
            if release:
                macros.append((self.release_macro_name+'_%s' % (release.replace('.','_')),None))
        opts = self.get_config_output(config_exe,'--libs')
        if opts:
            for opt in opts.split():
                if opt[:2]=='-l':
                    libraries.append(opt[2:])
                elif opt[:2]=='-L':
                    library_dirs.append(opt[2:])
                else:
                    extra_link_args.append(opt)
        opts = self.get_config_output(config_exe,'--cxxflags')
        if opts:
            for opt in opts.split():
                if opt[:2]=='-I':
                    include_dirs.append(opt[2:])
                elif opt[:2]=='-D':
                    if '=' in opt:
                        n,v = opt[2:].split('=')
                        macros.append((n,v))
                    else:
                        macros.append((opt[2:],None))
                else:
                    extra_compile_args.append(opt)
        if macros: dict_append(info, define_macros = macros)
        if libraries: dict_append(info, libraries = libraries)
        if library_dirs: dict_append(info, library_dirs = library_dirs)
        if include_dirs: dict_append(info, include_dirs = include_dirs)
        if extra_link_args: dict_append(info, extra_link_args = extra_link_args)
        if extra_compile_args: dict_append(info, extra_compile_args = extra_compile_args)
        if info:
            self.set_info(**info)
        return

class wx_info(_pkg_config_info):
    section = 'wx'
    config_env_var = 'WX_CONFIG'
    default_config_exe = 'wx-config'
    append_config_exe = ''
    version_macro_name = 'WX_VERSION'
    release_macro_name = 'WX_RELEASE'
    version_flag = '--version'

class gdk_pixbuf_xlib_2_info(_pkg_config_info):
    section = 'gdk_pixbuf_xlib_2'
    append_config_exe = 'gdk-pixbuf-xlib-2.0'
    version_macro_name = 'GDK_PIXBUF_XLIB_VERSION'

class gdk_pixbuf_2_info(_pkg_config_info):
    section = 'gdk_pixbuf_2'
    append_config_exe = 'gdk-pixbuf-2.0'
    version_macro_name = 'GDK_PIXBUF_VERSION'

class gdk_x11_2_info(_pkg_config_info):
    section = 'gdk_x11_2'
    append_config_exe = 'gdk-x11-2.0'
    version_macro_name = 'GDK_X11_VERSION'

class gtkp_x11_2_info(_pkg_config_info):
    section = 'gtkp_x11_2'
    append_config_exe = 'gtk+-x11-2.0'
    version_macro_name = 'GTK_X11_VERSION'


class gtkp_2_info(_pkg_config_info):
    section = 'gtkp_2'
    append_config_exe = 'gtk+-2.0'
    version_macro_name = 'GTK_VERSION'

class xft_info(_pkg_config_info):
    section = 'xft'
    append_config_exe = 'xft'
    version_macro_name = 'XFT_VERSION'

class freetype2_info(_pkg_config_info):
    section = 'freetype2'
    append_config_exe = 'freetype2'
    version_macro_name = 'FREETYPE2_VERSION'

## def vstr2hex(version):
##     bits = []
##     n = [24,16,8,4,0]
##     r = 0
##     for s in version.split('.'):
##         r |= int(s) << n[0]
##         del n[0]
##     return r

#--------------------------------------------------------------------

def combine_paths(*args,**kws):
    """ Return a list of existing paths composed by all combinations of
        items from arguments.
    """
    r = []
    for a in args:
        if not a: continue
        if type(a) is types.StringType:
            a = [a]
        r.append(a)
    args = r
    if not args: return []
    if len(args)==1:
        result = reduce(lambda a,b:a+b,map(glob,args[0]),[])
    elif len (args)==2:
        result = []
        for a0 in args[0]:
            for a1 in args[1]:
                result.extend(glob(os.path.join(a0,a1)))
    else:
        result = combine_paths(*(combine_paths(args[0],args[1])+args[2:]))
    verbosity = kws.get('verbosity',1)
    if verbosity>1 and result:
        print '(','paths:',','.join(result),')'
    return result

language_map = {'c':0,'c++':1,'f77':2,'f90':3}
inv_language_map = {0:'c',1:'c++',2:'f77',3:'f90'}
def dict_append(d,**kws):
    languages = []
    for k,v in kws.items():
        if k=='language':
            languages.append(v)
            continue
        if d.has_key(k):
            if k in ['library_dirs','include_dirs','define_macros']:
                [d[k].append(vv) for vv in v if vv not in d[k]]
            else:
                d[k].extend(v)
        else:
            d[k] = v
    if languages:
        l = inv_language_map[max([language_map.get(l,0) for l in languages])]
        d['language'] = l
    return

def show_all():
    import system_info
    import pprint
    match_info = re.compile(r'.*?_info').match
    for n in filter(match_info,dir(system_info)):
        if n in ['system_info','get_info']: continue
        c = getattr(system_info,n)()
        c.verbosity = 2
        r = c.get_info()

if __name__ == "__main__":
    show_all()
    if 0:
        c = gdk_pixbuf_2_info()
        c.verbosity = 2
        c.get_info()

"""scipy_distutils

   Modified version of distutils to handle fortran source code, f2py,
   and other issues in the scipy build process.
"""

# Need to do something here to get distutils subsumed...

from scipy_distutils_version import scipy_distutils_version as __version__

import sys

# Must import local ccompiler ASAP in order to get
# customized CCompiler.spawn effective.
import ccompiler
import unixccompiler


from distutils.core import *
from distutils.core import setup as old_setup

from scipy_distutils.dist import Distribution
from scipy_distutils.extension import Extension
from scipy_distutils.command import build
from scipy_distutils.command import build_py
from scipy_distutils.command import config_compiler
from scipy_distutils.command import build_ext
from scipy_distutils.command import build_clib
from scipy_distutils.command import build_src
from scipy_distutils.command import sdist
from scipy_distutils.command import install_data
from scipy_distutils.command import install
from scipy_distutils.command import install_headers


def setup(**attr):

    distclass = Distribution
    cmdclass = {'build':            build.build,
                'build_src':        build_src.build_src,
                'config_fc':        config_compiler.config_fc,
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

    fortran_libraries = new_attr.get('fortran_libraries',None)

    if fortran_libraries is not None:
        print 64*'*'+"""
    Using fortran_libraries setup option is depreciated
    ---------------------------------------------------
    Use libraries option instead. Yes, scipy_distutils
    now supports Fortran sources in libraries.
"""+64*'*'
        new_attr['libraries'].extend(fortran_libraries)
        del new_attr['fortran_libraries']

    # Move extension source libraries to libraries
    libraries = []
    for ext in new_attr.get('ext_modules',[]):
        new_libraries = []
        for item in ext.libraries:
            if type(item) is type(()):
                lib_name,build_info = item
                _check_append_ext_library(libraries, item)
                new_libraries.append(lib_name)
            else:
                assert type(item) is type(''),`item`
                new_libraries.append(item)
        ext.libraries = new_libraries
    if libraries:
        if not new_attr.has_key('libraries'):
            new_attr['libraries'] = []
        for item in libraries:
            _check_append_library(new_attr['libraries'], item)

    return old_setup(**new_attr)

def _check_append_library(libraries, item):
    import warnings
    for libitem in libraries:
        if type(libitem) is type(()):
            if type(item) is type(()):
                if item[0]==libitem[0]:
                    if item[1] is libitem[1]:
                        return
                    warnings.warn("[0] libraries list contains '%s' with"\
                                  " different build_info" % (item[0]))
                    break
            else:
                if item==libitem[0]:
                    warnings.warn("[1] libraries list contains '%s' with"\
                                  " no build_info" % (item[0]))
                    break
        else:
            if type(item) is type(()):
                if item[0]==libitem:
                    warnings.warn("[2] libraries list contains '%s' with"\
                                  " no build_info" % (item[0]))
                    break
            else:
                if item==libitem:
                    return
    libraries.append(item)
    return

def _check_append_ext_library(libraries, (lib_name,build_info)):
    import warnings
    for item in libraries:
        if type(item) is type(()):
            if item[0]==lib_name:
                if item[1] is build_info:
                    return
                warnings.warn("[3] libraries list contains '%s' with"\
                              " different build_info" % (lib_name))
                break
        elif item==lib_name:
            warnings.warn("[4] libraries list contains '%s' with"\
                          " no build_info" % (lib_name))
            break
    libraries.append((lib_name,build_info))
    return


# http://www.pgroup.com

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

class PGroupFCompiler(FCompiler):

    compiler_type = 'pg'
    version_pattern =  r'\s*pg(f77|f90|hpf) (?P<version>[\d.-]+).*'

    executables = {
        'version_cmd'  : ["pgf77", "-V 2>/dev/null"],
        'compiler_f77' : ["pgf77"],
        'compiler_fix' : ["pgf90", "-Mfixed"],
        'compiler_f90' : ["pgf90"],
        'linker_so'    : ["pgf90","-shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }
    pic_flags = ['-fpic']
    module_dir_switch = '-module '
    module_include_switch = '-I'

    def get_flags(self):
        opt = ['-Minform=inform','-Mnosecond_underscore']
        return self.pic_flags + opt
    def get_flags_opt(self):
        return ['-fast']
    def get_flags_debug(self):
        return ['-g']

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='pg')
    compiler.customize()
    print compiler.get_version()

#!/usr/bin/env python
#
# exec_command
#
# Implements exec_command function that is (almost) equivalent to
# commands.getstatusoutput function but on NT, DOS systems the
# returned status is actually correct (though, the returned status
# values may be different by a factor). In addition, exec_command
# takes keyword arguments for (re-)defining environment variables.
#
# Provides functions:
#   exec_command  --- execute command in a specified directory and
#                     in the modified environment.
#   splitcmdline  --- inverse of ' '.join(argv)
#   find_executable --- locate a command using info from environment
#                     variable PATH. Equivalent to posix `which`
#                     command.
#
# Author: Pearu Peterson <pearu@cens.ioc.ee>
# Created: 11 January 2003
#
# Requires: Python 2.x
#
# Succesfully tested on:
#   os.name | sys.platform | comments
#   --------+--------------+----------
#   posix   | linux2       | Debian (sid) Linux, Python 2.1.3+, 2.2.3+, 2.3.3
#                            PyCrust 0.9.3, Idle 1.0.2
#   posix   | linux2       | Red Hat 9 Linux, Python 2.1.3, 2.2.2, 2.3.2
#   posix   | sunos5       | SunOS 5.9, Python 2.2, 2.3.2
#   posix   | darwin       | Darwin 7.2.0, Python 2.3
#   nt      | win32        | Windows Me
#                            Python 2.3(EE), Idle 1.0, PyCrust 0.7.2
#                            Python 2.1.1 Idle 0.8
#   nt      | win32        | Windows 98, Python 2.1.1. Idle 0.8
#   nt      | win32        | Cygwin 98-4.10, Python 2.1.1(MSC) - echo tests
#                            fail i.e. redefining environment variables may
#                            not work. FIXED: don't use cygwin echo!
#                            Comment: also `cmd /c echo` will not work
#                            but redefining environment variables do work.
#   posix   | cygwin       | Cygwin 98-4.10, Python 2.3.3(cygming special)
#   nt      | win32        | Windows XP, Python 2.3.3
#
# Known bugs:
# - Tests, that send messages to stderr, fail when executed from MSYS prompt
#   because the messages are lost at some point.

__all__ = ['exec_command','find_executable']

import os
import re
import sys
import tempfile

############################################################

from log import _global_log as log

############################################################

def get_pythonexe():
    pythonexe = sys.executable
    if os.name in ['nt','dos']:
        fdir,fn = os.path.split(pythonexe)
        fn = fn.upper().replace('PYTHONW','PYTHON')
        pythonexe = os.path.join(fdir,fn)
        assert os.path.isfile(pythonexe),`pythonexe`+' is not a file'
    return pythonexe

############################################################

def splitcmdline(line):
    """ Inverse of ' '.join(sys.argv).
    """
    log.debug('splitcmdline(%r)' % (line))
    lst = []
    flag = 0
    s,pc,cc = '','',''
    for nc in line+' ':
        if flag==0:
            flag = (pc != '\\' and \
                     ((cc=='"' and 1) or (cc=="'" and 2) or \
                       (cc==' ' and pc!=' ' and -2))) or flag
        elif flag==1:
            flag = (cc=='"' and pc!='\\' and nc==' ' and -1) or flag
        elif flag==2:
            flag = (cc=="'" and pc!='\\' and nc==' ' and -1) or flag
        if flag!=-2:
            s += cc
        if flag<0:
            flag = 0
            s = s.strip()
            if s:
                lst.append(s)
                s = ''
        pc,cc = cc,nc
    else:
        s = s.strip()
        if s:
            lst.append(s)
    log.debug('splitcmdline -> %r' % (lst))
    return lst

def test_splitcmdline():
    l = splitcmdline('a   b  cc')
    assert l==['a','b','cc'],`l`
    l = splitcmdline('a')
    assert l==['a'],`l`
    l = splitcmdline('a "  b  cc"')
    assert l==['a','"  b  cc"'],`l`
    l = splitcmdline('"a bcc"  -h')
    assert l==['"a bcc"','-h'],`l`
    l = splitcmdline(r'"\"a \" bcc" -h')
    assert l==[r'"\"a \" bcc"','-h'],`l`
    l = splitcmdline(" 'a bcc'  -h")
    assert l==["'a bcc'",'-h'],`l`
    l = splitcmdline(r"'\'a \' bcc' -h")
    assert l==[r"'\'a \' bcc'",'-h'],`l`

############################################################

def find_executable(exe, path=None):
    """ Return full path of a executable.
    """
    log.debug('find_executable(%r)' % exe)
    orig_exe = exe
    if path is None:
        path = os.environ.get('PATH',os.defpath)
    if os.name=='posix' and sys.version[:3]>'2.1':
        realpath = os.path.realpath
    else:
        realpath = lambda a:a
    if exe[0]=='"':
        exe = exe[1:-1]
    suffices = ['']
    if os.name in ['nt','dos','os2']:
        fn,ext = os.path.splitext(exe)
        extra_suffices = ['.exe','.com','.bat']
        if ext.lower() not in extra_suffices:
            suffices = extra_suffices
    if os.path.isabs(exe):
        paths = ['']
    else:
        paths = map(os.path.abspath, path.split(os.pathsep))
        if 0 and os.name == 'nt':
            new_paths = []
            cygwin_paths = []
            for path in paths:
                d,p = os.path.splitdrive(path)
                if p.lower().find('cygwin') >= 0:
                    cygwin_paths.append(path)
                else:
                    new_paths.append(path)
            paths = new_paths + cygwin_paths
    for path in paths:
        fn = os.path.join(path,exe)
        for s in suffices:
            f_ext = fn+s
            if not os.path.islink(f_ext):
                # see comment below.
                f_ext = realpath(f_ext)
            if os.path.isfile(f_ext) and os.access(f_ext,os.X_OK):
                log.debug('Found executable %s' % f_ext)
                return f_ext
    if os.path.islink(exe):
        # Don't follow symbolic links. E.g. when using colorgcc then
        # gcc -> /usr/bin/colorgcc
        # g77 -> /usr/bin/colorgcc
        pass
    else:
        exe = realpath(exe)
    if not os.path.isfile(exe) or os.access(exe,os.X_OK):
        log.warn('Could not locate executable %s' % orig_exe)
        return orig_exe
    return exe

############################################################

def _preserve_environment( names ):
    log.debug('_preserve_environment(%r)' % (names))
    env = {}
    for name in names:
        env[name] = os.environ.get(name)
    return env

def _update_environment( **env ):
    log.debug('_update_environment(...)')
    for name,value in env.items():
        os.environ[name] = value or ''

def exec_command( command,
                  execute_in='', use_shell=None, use_tee = None,
                  _with_python = 1,
                  **env ):
    """ Return (status,output) of executed command.

    command is a concatenated string of executable and arguments.
    The output contains both stdout and stderr messages.
    The following special keyword arguments can be used:
      use_shell - execute `sh -c command`
      use_tee   - pipe the output of command through tee
      execute_in - before command `cd execute_in` and after `cd -`.

    On NT, DOS systems the returned status is correct for external commands.
    Wild cards will not work for non-posix systems or when use_shell=0.
    """
    log.debug('exec_command(%r,%s)' % (command,\
         ','.join(['%s=%r'%kv for kv in env.items()])))

    if use_tee is None:
        use_tee = os.name=='posix'
    if use_shell is None:
        use_shell = os.name=='posix'
    execute_in = os.path.abspath(execute_in)
    oldcwd = os.path.abspath(os.getcwd())

    if __name__[-12:] == 'exec_command':
        exec_dir = os.path.dirname(os.path.abspath(__file__))
    elif os.path.isfile('exec_command.py'):
        exec_dir = os.path.abspath('.')
    else:
        exec_dir = os.path.abspath(sys.argv[0])
        if os.path.isfile(exec_dir):
            exec_dir = os.path.dirname(exec_dir)

    if oldcwd!=execute_in:
        os.chdir(execute_in)
        log.debug('New cwd: %s' % execute_in)
    else:
        log.debug('Retaining cwd: %s' % oldcwd)

    oldenv = _preserve_environment( env.keys() )
    _update_environment( **env )

    try:
        # _exec_command is robust but slow, it relies on
        # usable sys.std*.fileno() descriptors. If they
        # are bad (like in win32 Idle, PyCrust environments)
        # then _exec_command_python (even slower)
        # will be used as a last resort.
        #
        # _exec_command_posix uses os.system and is faster
        # but not on all platforms os.system will return
        # a correct status.
        if _with_python and (0 or sys.__stdout__.fileno()==-1):
            st = _exec_command_python(command,
                                      exec_command_dir = exec_dir,
                                      **env)
        elif os.name=='posix':
            st = _exec_command_posix(command,
                                     use_shell=use_shell,
                                     use_tee=use_tee,
                                     **env)
        else:
            st = _exec_command(command, use_shell=use_shell,
                               use_tee=use_tee,**env)
    finally:
        if oldcwd!=execute_in:
            os.chdir(oldcwd)
            log.debug('Restored cwd to %s' % oldcwd)
        _update_environment(**oldenv)

    return st

def _exec_command_posix( command,
                         use_shell = None,
                         use_tee = None,
                         **env ):
    log.debug('_exec_command_posix(...)')

    if type(command) is type([]):
        command_str = ' '.join(command)
    else:
        command_str = command

    tmpfile = tempfile.mktemp()
    stsfile = None
    if use_tee:
        stsfile = tempfile.mktemp()
        filter = ''
        if use_tee == 2:
            filter = r'| tr -cd "\n" | tr "\n" "."; echo'
        command_posix = '( %s ; echo $? > %s ) 2>&1 | tee %s %s'\
                      % (command_str,stsfile,tmpfile,filter)
    else:
        stsfile = tempfile.mktemp()
        command_posix = '( %s ; echo $? > %s ) > %s 2>&1'\
                        % (command_str,stsfile,tmpfile)
        #command_posix = '( %s ) > %s 2>&1' % (command_str,tmpfile)

    log.debug('Running os.system(%r)' % (command_posix))
    status = os.system(command_posix)

    if use_tee:
        if status:
            # if command_tee fails then fall back to robust exec_command
            log.warn('_exec_command_posix failed (status=%s)' % status)
            return _exec_command(command, use_shell=use_shell, **env)

    if stsfile is not None:
        f = open(stsfile,'r')
        status_text = f.read()
        status = int(status_text)
        f.close()
        os.remove(stsfile)

    f = open(tmpfile,'r')
    text = f.read()
    f.close()
    os.remove(tmpfile)

    if text[-1:]=='\n':
        text = text[:-1]
    
    return status, text


def _exec_command_python(command,
                         exec_command_dir='', **env):
    log.debug('_exec_command_python(...)')

    python_exe = get_pythonexe()
    cmdfile = tempfile.mktemp()
    stsfile = tempfile.mktemp()
    outfile = tempfile.mktemp()

    f = open(cmdfile,'w')
    f.write('import os\n')
    f.write('import sys\n')
    f.write('sys.path.insert(0,%r)\n' % (exec_command_dir))
    f.write('from exec_command import exec_command\n')
    f.write('del sys.path[0]\n')
    f.write('cmd = %r\n' % command)
    f.write('os.environ = %r\n' % (os.environ))
    f.write('s,o = exec_command(cmd, _with_python=0, **%r)\n' % (env))
    f.write('f=open(%r,"w")\nf.write(str(s))\nf.close()\n' % (stsfile))
    f.write('f=open(%r,"w")\nf.write(o)\nf.close()\n' % (outfile))
    f.close()

    cmd = '%s %s' % (python_exe, cmdfile)
    status = os.system(cmd)
    assert not status,`cmd`+' failed'
    os.remove(cmdfile)

    f = open(stsfile,'r')
    status = int(f.read())
    f.close()
    os.remove(stsfile)
    
    f = open(outfile,'r')
    text = f.read()
    f.close()
    os.remove(outfile)
    
    return status, text

def quote_arg(arg):
    if arg[0]!='"' and ' ' in arg:
        return '"%s"' % arg
    return arg

def _exec_command( command, use_shell=None, use_tee = None, **env ):
    log.debug('_exec_command(...)')
    
    if use_shell is None:
        use_shell = os.name=='posix'
    if use_tee is None:
        use_tee = os.name=='posix'

    using_command = 0
    if use_shell:
        # We use shell (unless use_shell==0) so that wildcards can be
        # used.
        sh = os.environ.get('SHELL','/bin/sh')
        if type(command) is type([]):
            argv = [sh,'-c',' '.join(command)]
        else:
            argv = [sh,'-c',command]
    else:
        # On NT, DOS we avoid using command.com as it's exit status is
        # not related to the exit status of a command.
        if type(command) is type([]):
            argv = command[:]
        else:
            argv = splitcmdline(command)

    if hasattr(os,'spawnvpe'):
        spawn_command = os.spawnvpe
    else:
        spawn_command = os.spawnve
        argv[0] = find_executable(argv[0])
        if not os.path.isfile(argv[0]):
            log.warn('Executable %s does not exist' % (argv[0]))
            if os.name in ['nt','dos']:
                # argv[0] might be internal command
                argv = [os.environ['COMSPEC'],'/C'] + argv
                using_command = 1

    # sys.__std*__ is used instead of sys.std* because environments
    # like IDLE, PyCrust, etc overwrite sys.std* commands.
    so_fileno = sys.__stdout__.fileno()
    se_fileno = sys.__stderr__.fileno()
    so_flush = sys.__stdout__.flush
    se_flush = sys.__stderr__.flush
    so_dup = os.dup(so_fileno)
    se_dup = os.dup(se_fileno)

    outfile = tempfile.mktemp()
    fout = open(outfile,'w')
    if using_command:
        errfile = tempfile.mktemp()
        ferr = open(errfile,'w')

    log.debug('Running %s(%s,%r,%r,os.environ)' \
              % (spawn_command.__name__,os.P_WAIT,argv[0],argv))

    argv0 = argv[0]
    if not using_command:
        argv[0] = quote_arg(argv0)

    so_flush()
    se_flush()
    os.dup2(fout.fileno(),so_fileno)
    if using_command:
        #XXX: disabled for now as it does not work from cmd under win32.
        #     Tests fail on msys
        os.dup2(ferr.fileno(),se_fileno)
    else:
        os.dup2(fout.fileno(),se_fileno)
    try:
        status = spawn_command(os.P_WAIT,argv0,argv,os.environ)
    except OSError,errmess:
        status = 999
        sys.stderr.write('%s: %s'%(errmess,argv[0]))

    so_flush()
    se_flush()
    os.dup2(so_dup,so_fileno)
    os.dup2(se_dup,se_fileno)

    fout.close()
    fout = open(outfile,'r')
    text = fout.read()
    fout.close()
    os.remove(outfile)

    if using_command:
        ferr.close()
        ferr = open(errfile,'r')
        errmess = ferr.read()
        ferr.close()
        os.remove(errfile)
        if errmess and not status:
            # Not sure how to handle the case where errmess
            # contains only warning messages and that should
            # not be treated as errors.
            #status = 998
            if text:
                text = text + '\n'
            #text = '%sCOMMAND %r FAILED: %s' %(text,command,errmess)
            text = text + errmess
            print errmess
    if text[-1:]=='\n':
        text = text[:-1]
    if status is None:
        status = 0

    if use_tee:
        print text

    return status, text


def test_nt(**kws):
    pythonexe = get_pythonexe()
    echo = find_executable('echo')
    using_cygwin_echo = echo != 'echo'
    if using_cygwin_echo:
        log.warn('Using cygwin echo in win32 environment is not supported')

        s,o=exec_command(pythonexe\
                         +' -c "import os;print os.environ.get(\'AAA\',\'\')"')
        assert s==0 and o=='',(s,o)
        
        s,o=exec_command(pythonexe\
                         +' -c "import os;print os.environ.get(\'AAA\')"',
                         AAA='Tere')
        assert s==0 and o=='Tere',(s,o)

        os.environ['BBB'] = 'Hi'
        s,o=exec_command(pythonexe\
                         +' -c "import os;print os.environ.get(\'BBB\',\'\')"')
        assert s==0 and o=='Hi',(s,o)

        s,o=exec_command(pythonexe\
                         +' -c "import os;print os.environ.get(\'BBB\',\'\')"',
                         BBB='Hey')
        assert s==0 and o=='Hey',(s,o)

        s,o=exec_command(pythonexe\
                         +' -c "import os;print os.environ.get(\'BBB\',\'\')"')
        assert s==0 and o=='Hi',(s,o)
    elif 0:
        s,o=exec_command('echo Hello')
        assert s==0 and o=='Hello',(s,o)

        s,o=exec_command('echo a%AAA%')
        assert s==0 and o=='a',(s,o)

        s,o=exec_command('echo a%AAA%',AAA='Tere')
        assert s==0 and o=='aTere',(s,o)

        os.environ['BBB'] = 'Hi'
        s,o=exec_command('echo a%BBB%')
        assert s==0 and o=='aHi',(s,o)

        s,o=exec_command('echo a%BBB%',BBB='Hey')
        assert s==0 and o=='aHey', (s,o)
        s,o=exec_command('echo a%BBB%')
        assert s==0 and o=='aHi',(s,o)

        s,o=exec_command('this_is_not_a_command')
        assert s and o!='',(s,o)

        s,o=exec_command('type not_existing_file')
        assert s and o!='',(s,o)

    s,o=exec_command('echo path=%path%')
    assert s==0 and o!='',(s,o)
    
    s,o=exec_command('%s -c "import sys;sys.stderr.write(sys.platform)"' \
                     % pythonexe)
    assert s==0 and o=='win32',(s,o)

    s,o=exec_command('%s -c "raise \'Ignore me.\'"' % pythonexe)
    assert s==1 and o,(s,o)

    s,o=exec_command('%s -c "import sys;sys.stderr.write(\'0\');sys.stderr.write(\'1\');sys.stderr.write(\'2\')"'\
                     % pythonexe)
    assert s==0 and o=='012',(s,o)

    s,o=exec_command('%s -c "import sys;sys.exit(15)"' % pythonexe)
    assert s==15 and o=='',(s,o)

    s,o=exec_command('%s -c "print \'Heipa\'"' % pythonexe)
    assert s==0 and o=='Heipa',(s,o)

    print 'ok'

def test_posix(**kws):
    s,o=exec_command("echo Hello",**kws)
    assert s==0 and o=='Hello',(s,o)

    s,o=exec_command('echo $AAA',**kws)
    assert s==0 and o=='',(s,o)

    s,o=exec_command('echo "$AAA"',AAA='Tere',**kws)
    assert s==0 and o=='Tere',(s,o)


    s,o=exec_command('echo "$AAA"',**kws)
    assert s==0 and o=='',(s,o)

    os.environ['BBB'] = 'Hi'
    s,o=exec_command('echo "$BBB"',**kws)
    assert s==0 and o=='Hi',(s,o)

    s,o=exec_command('echo "$BBB"',BBB='Hey',**kws)
    assert s==0 and o=='Hey',(s,o)

    s,o=exec_command('echo "$BBB"',**kws)
    assert s==0 and o=='Hi',(s,o)


    s,o=exec_command('this_is_not_a_command',**kws)
    assert s!=0 and o!='',(s,o)

    s,o=exec_command('echo path=$PATH',**kws)
    assert s==0 and o!='',(s,o)
    
    s,o=exec_command('python -c "import sys,os;sys.stderr.write(os.name)"',**kws)
    assert s==0 and o=='posix',(s,o)

    s,o=exec_command('python -c "raise \'Ignore me.\'"',**kws)
    assert s==1 and o,(s,o)

    s,o=exec_command('python -c "import sys;sys.stderr.write(\'0\');sys.stderr.write(\'1\');sys.stderr.write(\'2\')"',**kws)
    assert s==0 and o=='012',(s,o)

    s,o=exec_command('python -c "import sys;sys.exit(15)"',**kws)
    assert s==15 and o=='',(s,o)

    s,o=exec_command('python -c "print \'Heipa\'"',**kws)
    assert s==0 and o=='Heipa',(s,o)
    
    print 'ok'

def test_execute_in(**kws):
    pythonexe = get_pythonexe()
    tmpfile = tempfile.mktemp()
    fn = os.path.basename(tmpfile)
    tmpdir = os.path.dirname(tmpfile)
    f = open(tmpfile,'w')
    f.write('Hello')
    f.close()

    s,o = exec_command('%s -c "print \'Ignore the following IOError:\','\
                       'open(%r,\'r\')"' % (pythonexe,fn),**kws)
    assert s and o!='',(s,o)
    s,o = exec_command('%s -c "print open(%r,\'r\').read()"' % (pythonexe,fn),
                       execute_in = tmpdir,**kws)
    assert s==0 and o=='Hello',(s,o)
    os.remove(tmpfile)
    print 'ok'

def test_svn(**kws):
    s,o = exec_command(['svn','status'],**kws)
    assert s,(s,o)
    print 'svn ok'

def test_cl(**kws):
    if os.name=='nt':
        s,o = exec_command(['cl','/V'],**kws)
        assert s,(s,o)
        print 'cl ok'

if os.name=='posix':
    test = test_posix
elif os.name in ['nt','dos']:
    test = test_nt
else:
    raise NotImplementedError,'exec_command tests for '+os.name

############################################################

if __name__ == "__main__":

    test_splitcmdline()
    test(use_tee=0)
    test(use_tee=1)
    test_execute_in(use_tee=0)
    test_execute_in(use_tee=1)
    test_svn(use_tee=1)
    test_cl(use_tee=1)


import re
import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler
from exec_command import exec_command, find_executable

class GnuFCompiler(FCompiler):

    compiler_type = 'gnu'
    version_pattern = r'GNU Fortran ((\(GCC[^\)]*(\)\)|\)))|)\s*'\
                      '(?P<version>[^\s*\)]+)'

    # 'g77 --version' results
    # SunOS: GNU Fortran (GCC 3.2) 3.2 20020814 (release)
    # Debian: GNU Fortran (GCC) 3.3.3 20040110 (prerelease) (Debian)
    #         GNU Fortran (GCC) 3.3.3 (Debian 20040401)
    #         GNU Fortran 0.5.25 20010319 (prerelease)
    # Redhat: GNU Fortran (GCC 3.2.2 20030222 (Red Hat Linux 3.2.2-5)) 3.2.2 20030222 (Red Hat Linux 3.2.2-5)

    for fc_exe in map(find_executable,['g77','f77']):
        if os.path.isfile(fc_exe):
            break
    executables = {
        'version_cmd'  : [fc_exe,"--version"],
        'compiler_f77' : [fc_exe,"-Wall","-fno-second-underscore"],
        'compiler_f90' : None,
        'compiler_fix' : None,
        'linker_so'    : [fc_exe],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"],
        }
    module_dir_switch = None
    module_include_switch = None

    # Cygwin: f771: warning: -fPIC ignored for target (all code is position independent)
    if os.name != 'nt' and sys.platform!='cygwin':
        pic_flags = ['-fPIC']

    #def get_linker_so(self):
    #    # win32 linking should be handled by standard linker
    #    # Darwin g77 cannot be used as a linker.
    #    #if re.match(r'(darwin)', sys.platform):
    #    #    return
    #    return FCompiler.get_linker_so(self)

    def get_flags_linker_so(self):
        opt = []
        if sys.platform=='darwin':
            if os.path.realpath(sys.executable).startswith('/System'):
                # This is when Python is from Apple framework
                opt.extend(["-Wl,-framework","-Wl,Python"])
            #else we are running in Fink python.
            opt.extend(["-lcc_dynamic","-bundle"])
        else:
            opt.append("-shared")
        if sys.platform[:5]=='sunos':
            # SunOS often has dynamically loaded symbols defined in the
            # static library libg2c.a  The linker doesn't like this.  To
            # ignore the problem, use the -mimpure-text flag.  It isn't
            # the safest thing, but seems to work. 'man gcc' says:
            # ".. Instead of using -mimpure-text, you should compile all
            #  source code with -fpic or -fPIC."
            opt.append('-mimpure-text')
        return opt

    def get_libgcc_dir(self):
        status, output = exec_command('%s -print-libgcc-file-name' \
                                      % (self.compiler_f77[0]),use_tee=0)        
        if not status:
            return os.path.dirname(output)
        return

    def get_library_dirs(self):
        opt = []
        if sys.platform[:5] != 'linux':
            d = self.get_libgcc_dir()
            if d:
                opt.append(d)
        return opt

    def get_libraries(self):
        opt = []
        d = self.get_libgcc_dir()
        if d is not None:
            for g2c in ['g2c-pic','g2c']:
                f = self.static_lib_format % (g2c, self.static_lib_extension)
                if os.path.isfile(os.path.join(d,f)):
                    break
        else:
            g2c = 'g2c'
        if sys.platform=='win32':
            opt.extend(['gcc',g2c])
        else:
            opt.append(g2c)
        return opt

    def get_flags_debug(self):
        return ['-g']

    def get_flags_opt(self):
        opt = ['-O3','-funroll-loops']
        return opt

    def get_flags_arch(self):
        opt = []
        if sys.platform=='darwin':
            if os.name != 'posix':
                # this should presumably correspond to Apple
                if cpu.is_ppc():
                    opt.append('-arch ppc')
                elif cpu.is_i386():
                    opt.append('-arch i386')
            for a in '601 602 603 603e 604 604e 620 630 740 7400 7450 750'\
                    '403 505 801 821 823 860'.split():
                if getattr(cpu,'is_ppc%s'%a)():
                    opt.append('-mcpu='+a)
                    opt.append('-mtune='+a)
                    break    
            return opt
        march_flag = 1
        # 0.5.25 corresponds to 2.95.x
        if self.get_version() == '0.5.26': # gcc 3.0
            if cpu.is_AthlonK6():
                opt.append('-march=k6')
            elif cpu.is_AthlonK7():
                opt.append('-march=athlon')
            else:
                march_flag = 0
        # Note: gcc 3.2 on win32 has breakage with -march specified
        elif self.get_version() >= '3.1.1' \
            and not sys.platform=='win32': # gcc >= 3.1.1
            if cpu.is_AthlonK6():
                opt.append('-march=k6')
            elif cpu.is_AthlonK6_2():
                opt.append('-march=k6-2')
            elif cpu.is_AthlonK6_3():
                opt.append('-march=k6-3')
            elif cpu.is_AthlonK7():
                opt.append('-march=athlon')
            elif cpu.is_AthlonMP():
                opt.append('-march=athlon-mp')
                # there's also: athlon-tbird, athlon-4, athlon-xp
            elif cpu.is_PentiumIV():
                opt.append('-march=pentium4')
            elif cpu.is_PentiumIII():
                opt.append('-march=pentium3')
            elif cpu.is_PentiumII():
                opt.append('-march=pentium2')
            else:
                march_flag = 0
            if cpu.has_mmx(): opt.append('-mmmx')      
            if self.get_version() > '3.2.2':
                if cpu.has_sse2(): opt.append('-msse2')
                if cpu.has_sse(): opt.append('-msse')
            if cpu.has_3dnow(): opt.append('-m3dnow')
        else:
            march_flag = 0
        if march_flag:
            pass
        elif cpu.is_i686():
            opt.append('-march=i686')
        elif cpu.is_i586():
            opt.append('-march=i586')
        elif cpu.is_i486():
            opt.append('-march=i486')
        elif cpu.is_i386():
            opt.append('-march=i386')
        if cpu.is_Intel():
            opt.extend(['-malign-double','-fomit-frame-pointer'])
        return opt

if __name__ == '__main__':
    from scipy_distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    #compiler = new_fcompiler(compiler='gnu')
    compiler = GnuFCompiler()
    compiler.customize()
    print compiler.get_version()

#!/usr/bin/python

# takes templated file .xxx.src and produces .xxx file  where .xxx is .pyf .f90 or .f
#  using the following template rules

# <...>  is the template All blocks in a source file with names that
#         contain '<..>' will be replicated according to the
#         rules in '<..>'.

# The number of comma-separeted words in '<..>' will determine the number of
#   replicates.
 
# '<..>' may have two different forms, named and short. For example,

#named:
#   <p=d,s,z,c> where anywhere inside a block '<p>' will be replaced with
#  'd', 's', 'z', and 'c' for each replicate of the block.

#  <_c>  is already defined: <_c=s,d,c,z>
#  <_t>  is already defined: <_t=real,double precision,complex,double complex>

#short:
#  <d,s,z,c>, a short form of the named, useful when no <p> appears inside 
#  a block.

#  Note that all <..> forms in a block must have the same number of
#    comma-separated entries. 

__all__ = ['process_str']

import string,os,sys
if sys.version[:3]>='2.3':
    import re
else:
    import pre as re
    False = 0
    True = 1

comment_block_exp = re.compile(r'/\*(?:\s|.)*?\*/')
subroutine_exp = re.compile(r'subroutine (?:\s|.)*?end subroutine.*')
function_exp = re.compile(r'function (?:\s|.)*?end function.*')
reg = re.compile(r"\ssubroutine\s(.+)\(.*\)")

def parse_structure(astr):
    spanlist = []
    for typ in [subroutine_exp, function_exp]:
        ind = 0
        while 1:
            a = typ.search(astr[ind:])
            if a is None:
                break
            tup = a.span()
            tup = (ind+tup[0],ind+tup[1])
            spanlist.append(tup)
            ind  = tup[1]

    spanlist.sort()
    return spanlist

# return n copies of substr with template replacement
_special_names = {'_c':'s,d,c,z',
                  '_t':'real,double precision,complex,double complex'
                  }
template_re = re.compile(r"<([\w]*)>")
named_re = re.compile(r"<([\w]*)=([, \w]*)>")
list_re = re.compile(r"<([\w ]+(,\s*[\w]+)+)>")

def conv(astr):
    b = astr.split(',')
    return ','.join([x.strip().lower() for x in b])

def unique_key(adict):
    # this obtains a unique key given a dictionary
    # currently it works by appending together n of the letters of the
    #   current keys and increasing n until a unique key is found
    # -- not particularly quick
    allkeys = adict.keys()
    done = False
    n = 1
    while not done:
        newkey = "".join([x[:n] for x in allkeys])
        if newkey in allkeys:
            n += 1
        else:
            done = True
    return newkey

def listrepl(match):
    global _names
    thelist = conv(match.group(1))
    name = None
    for key in _names.keys():    # see if list is already in dictionary
        if _names[key] == thelist:
            name = key
    if name is None:      # this list is not in the dictionary yet
        name = "%s" % unique_key(_names)
        _names[name] = thelist
    return "<%s>" % name

def namerepl(match):
    global _names, _thissub
    name = match.group(1)
    return _names[name][_thissub]

def expand_sub(substr,extra=''):
    global _names, _thissub
    # find all named replacements
    reps = named_re.findall(substr)
    _names = {}
    _names.update(_special_names)
    numsubs = None
    for rep in reps:
        name = rep[0].strip().lower()
        thelist,num = conv(rep[1])
        _names[name] = thelist

    substr = named_re.sub(r"<\1>",substr)  # get rid of definition templates
    substr = list_re.sub(listrepl, substr) # convert all lists to named templates
                                           #  newnames are constructed as needed

    # make lists out of string entries in name dictionary
    for name in _names.keys():
        entry = _names[name]
        entrylist = entry.split(',')
        _names[name] = entrylist
        num = len(entrylist)
        if numsubs is None:
            numsubs = num
        elif (numsubs != num):
            raise ValueError, "Mismatch in number to replace"

    # now replace all keys for each of the lists
    mystr = ''
    for k in range(numsubs):
        _thissub = k
        mystr += template_re.sub(namerepl, substr)
        mystr += "\n\n" + extra
    return mystr

_head = \
"""C  This file was autogenerated from a template  DO NOT EDIT!!!!
C     Changes should be made to the original source (.src) file
C

"""

def get_line_header(str,beg):
    extra = []
    ind = beg-1
    char = str[ind]
    while (ind > 0) and (char != '\n'):
        extra.insert(0,char)
        ind = ind - 1
        char = str[ind]
    return ''.join(extra)
    
def process_str(allstr):
    newstr = allstr.lower()
    writestr = _head

    struct = parse_structure(newstr)
    #  return a (sorted) list of tuples for each function or subroutine
    #  each tuple is the start and end of a subroutine or function to be expanded
    
    oldend = 0
    for sub in struct:
        writestr += newstr[oldend:sub[0]]
        expanded = expand_sub(newstr[sub[0]:sub[1]],get_line_header(newstr,sub[0]))
        writestr += expanded
        oldend =  sub[1]

    writestr += newstr[oldend:]
    return writestr


if __name__ == "__main__":

    try:
        file = sys.argv[1]
    except IndexError:
        fid = sys.stdin
        outfile = sys.stdout
    else:
        fid = open(file,'r')
        (base, ext) = os.path.splitext(file)
        newname = base
        outfile = open(newname,'w')

    allstr = fid.read()
    writestr = process_str(allstr)
    outfile.write(writestr)

"""
Support code for building Python extensions on Windows.

    # NT stuff
    # 1. Make sure libpython<version>.a exists for gcc.  If not, build it.
    # 2. Force windows to use gcc (we're struggling with MSVC and g77 support) 
    # 3. Force windows to use g77

"""

import os
import sys
import log

import scipy_distutils.ccompiler

# NT stuff
# 1. Make sure libpython<version>.a exists for gcc.  If not, build it.
# 2. Force windows to use gcc (we're struggling with MSVC and g77 support) 
#    --> this is done in scipy_distutils/ccompiler.py
# 3. Force windows to use g77

import distutils.cygwinccompiler
from distutils.version import StrictVersion
from scipy_distutils.ccompiler import gen_preprocess_options, gen_lib_options
from distutils.errors import DistutilsExecError, CompileError, UnknownFileError

from distutils.unixccompiler import UnixCCompiler 
    
# the same as cygwin plus some additional parameters
class Mingw32CCompiler(distutils.cygwinccompiler.CygwinCCompiler):
    """ A modified MingW32 compiler compatible with an MSVC built Python.
    
    """
    
    compiler_type = 'mingw32'
    
    def __init__ (self,
                  verbose=0,
                  dry_run=0,
                  force=0):
    
        distutils.cygwinccompiler.CygwinCCompiler.__init__ (self, 
                                                       verbose,dry_run, force)
            
        # we need to support 3.2 which doesn't match the standard
        # get_versions methods regex
        if self.gcc_version is None:
            import re
            out = os.popen('gcc -dumpversion','r')
            out_string = out.read()
            out.close()
            result = re.search('(\d+\.\d+)',out_string)
            if result:
                self.gcc_version = StrictVersion(result.group(1))            

        # A real mingw32 doesn't need to specify a different entry point,
        # but cygwin 2.91.57 in no-cygwin-mode needs it.
        if self.gcc_version <= "2.91.57":
            entry_point = '--entry _DllMain@12'
        else:
            entry_point = ''

        if self.linker_dll == 'dllwrap':
            self.linker = 'dllwrap  --driver-name g++'
        elif self.linker_dll == 'gcc':
            self.linker = 'g++'    

        # **changes: eric jones 4/11/01
        # 1. Check for import library on Windows.  Build if it doesn't exist.

        build_import_library()

        # **changes: eric jones 4/11/01
        # 2. increased optimization and turned off all warnings
        # 3. also added --driver-name g++
        #self.set_executables(compiler='gcc -mno-cygwin -O2 -w',
        #                     compiler_so='gcc -mno-cygwin -mdll -O2 -w',
        #                     linker_exe='gcc -mno-cygwin',
        #                     linker_so='%s --driver-name g++ -mno-cygwin -mdll -static %s' 
        #                                % (self.linker, entry_point))
        if self.gcc_version <= "3.0.0":
            self.set_executables(compiler='gcc -mno-cygwin -O2 -w',
                                 compiler_so='gcc -mno-cygwin -mdll -O2 -w -Wstrict-prototypes',
                                 linker_exe='g++ -mno-cygwin',
                                 linker_so='%s -mno-cygwin -mdll -static %s' 
                                 % (self.linker, entry_point))
        else:            
            self.set_executables(compiler='gcc -mno-cygwin -O2 -Wall',
                                 compiler_so='gcc -O2 -Wall -Wstrict-prototypes',
                                 linker_exe='g++ ',
                                 linker_so='g++ -shared')
        # added for python2.3 support
        # we can't pass it through set_executables because pre 2.2 would fail
        self.compiler_cxx = ['g++']
            
        # Maybe we should also append -mthreads, but then the finished
        # dlls need another dll (mingwm10.dll see Mingw32 docs)
        # (-mthreads: Support thread-safe exception handling on `Mingw32')       
        
        # no additional libraries needed 
        self.dll_libraries=[]
        return

    # __init__ ()

    def link(self,
             target_desc,
             objects,
             output_filename,
             output_dir,
             libraries,
             library_dirs,
             runtime_library_dirs,
             export_symbols = None,
             debug=0,
             extra_preargs=None,
             extra_postargs=None,
             build_temp=None,
             target_lang=None):
        args = (self,
                target_desc,
                objects,
                output_filename,
                output_dir,
                libraries,
                library_dirs,
                runtime_library_dirs,
                None, #export_symbols, we do this in our def-file
                debug,
                extra_preargs,
                extra_postargs,
                build_temp,
                target_lang)
        if self.gcc_version < "3.0.0":
            func = distutils.cygwinccompiler.CygwinCCompiler.link
        else:
            func = UnixCCompiler.link
        func(*args[:func.im_func.func_code.co_argcount])
        return

    def object_filenames (self,
                          source_filenames,
                          strip_dir=0,
                          output_dir=''):
        if output_dir is None: output_dir = ''
        obj_names = []
        for src_name in source_filenames:
            # use normcase to make sure '.rc' is really '.rc' and not '.RC'
            (base, ext) = os.path.splitext (os.path.normcase(src_name))
            
            # added these lines to strip off windows drive letters
            # without it, .o files are placed next to .c files
            # instead of the build directory
            drv,base = os.path.splitdrive(base)
            if drv:
                base = base[1:]
                
            if ext not in (self.src_extensions + ['.rc','.res']):
                raise UnknownFileError, \
                      "unknown file type '%s' (from '%s')" % \
                      (ext, src_name)
            if strip_dir:
                base = os.path.basename (base)
            if ext == '.res' or ext == '.rc':
                # these need to be compiled to object files
                obj_names.append (os.path.join (output_dir,
                                                base + ext + self.obj_extension))
            else:
                obj_names.append (os.path.join (output_dir,
                                                base + self.obj_extension))
        return obj_names
    
    # object_filenames ()

    
def build_import_library():
    """ Build the import libraries for Mingw32-gcc on Windows
    """
    if os.name != 'nt':
        return
    lib_name = "python%d%d.lib" % tuple(sys.version_info[:2])    
    lib_file = os.path.join(sys.prefix,'libs',lib_name)
    out_name = "libpython%d%d.a" % tuple(sys.version_info[:2])
    out_file = os.path.join(sys.prefix,'libs',out_name)
    if not os.path.isfile(lib_file):
        log.warn('Cannot build import library: "%s" not found' % (lib_file))
        return
    if os.path.isfile(out_file):
        log.debug('Skip building import library: "%s" exists' % (out_file))
        return
    log.info('Building import library: "%s"' % (out_file))

    from scipy_distutils import lib2def

    def_name = "python%d%d.def" % tuple(sys.version_info[:2])    
    def_file = os.path.join(sys.prefix,'libs',def_name)
    nm_cmd = '%s %s' % (lib2def.DEFAULT_NM, lib_file)
    nm_output = lib2def.getnm(nm_cmd)
    dlist, flist = lib2def.parse_nm(nm_output)
    lib2def.output_def(dlist, flist, lib2def.DEF_HEADER, open(def_file, 'w'))
    
    dll_name = "python%d%d.dll" % tuple(sys.version_info[:2])
    args = (dll_name,def_file,out_file)
    cmd = 'dlltool --dllname %s --def %s --output-lib %s' % args
    status = os.system(cmd)
    # for now, fail silently
    if status:
        log.warn('Failed to build import library for gcc. Linking will fail.')
    #if not success:
    #    msg = "Couldn't find import library, and failed to build it."
    #    raise DistutilsPlatformError, msg
    return


__revision__ = "$Id$"
import warnings
warnings.warn("""
*******************************************************************
The content of mingw32_support.py (this file) has been moved to
mingw32ccompiler.py. If you see this message then it may be because
f2py2e version older than 2.39.235 was importing this file. You can
either ignore this message or upgrade to the latest f2py2e version.
The last action is recommended as in future this file might be removed
and then for older f2py2e releases removing 'import mingw32_support'
statement manually is required.
*******************************************************************""")

"""distutils.extension

Provides the Extension class, used to describe C/C++ extension
modules in setup scripts.

Overridden to support f2py and SourceGenerator.
"""

__revision__ = "$Id$"

from distutils.extension import Extension as old_Extension
from scipy_distutils.misc_util import SourceGenerator, SourceFilter

import re
cxx_ext_re = re.compile(r'.*[.](cpp|cxx|cc)\Z',re.I).match
fortran_pyf_ext_re = re.compile(r'.*[.](f90|f95|f77|for|ftn|f|pyf)\Z',re.I).match

class Extension(old_Extension):
    def __init__ (self, name, sources,
                  include_dirs=None,
                  define_macros=None,
                  undef_macros=None,
                  library_dirs=None,
                  libraries=None,
                  runtime_library_dirs=None,
                  extra_objects=None,
                  extra_compile_args=None,
                  extra_link_args=None,
                  export_symbols=None,
                  depends=None,
                  language=None,
                  f2py_options=None,
                  module_dirs=None,
                 ):
        old_Extension.__init__(self,name, [],
                               include_dirs,
                               define_macros,
                               undef_macros,
                               library_dirs,
                               libraries,
                               runtime_library_dirs,
                               extra_objects,
                               extra_compile_args,
                               extra_link_args,
                               export_symbols)
        # Avoid assert statements checking that sources contains strings:
        self.sources = sources

        # Python 2.3 distutils new features
        self.depends = depends or []
        self.language = language

        self.f2py_options = f2py_options or []
        self.module_dirs = module_dirs or []

    def has_cxx_sources(self):
        for source in self.sources:
            if isinstance(source,SourceGenerator) \
               or isinstance(source,SourceFilter):
                for s in source.sources:
                    if cxx_ext_re(s):
                        return 1
            if cxx_ext_re(str(source)):
                return 1
        return 0

    def has_f2py_sources(self):
        for source in self.sources:
            if isinstance(source,SourceGenerator) \
               or isinstance(source,SourceFilter):
                for s in source.sources:
                    if fortran_pyf_ext_re(s):
                        return 1
            elif fortran_pyf_ext_re(source):
                return 1
        return 0

    def generate_sources(self):
        new_sources = []
        for source in self.sources:
            if isinstance(source, SourceGenerator):
                new_sources.append(source.generate())
            elif isinstance(source, SourceFilter):
                new_sources.extend(source.filter())
            else:
                new_sources.append(source)
        self.sources = new_sources
                
    def get_sources(self):
        sources = []
        for source in self.sources:
            if isinstance(source,SourceGenerator):
                sources.extend(source.sources)
            elif isinstance(source,SourceFilter):
                sources.extend(source.sources)
            else:
                sources.append(source)
        return sources

# class Extension

#!/usr/bin/env python

import os
from glob import glob
from misc_util import get_path, default_config_dict, dot_join

def configuration(parent_package='',parent_path=None):
    package = 'scipy_distutils'
    local_path = get_path(__name__,parent_path)
    config = default_config_dict(package,parent_package)

    sub_package = dot_join(parent_package,package,'command')
    config['packages'].append(sub_package)
    config['package_dir'][sub_package] = os.path.join(local_path,'command')

    #for name in glob(os.path.join(local_path,'tests','*_ext')):
    #    p = dot_join(parent_package,package,'tests',os.path.basename(name))
    #    config['packages'].append(p)
    #    config['package_dir'][p] = name

    config['data_files'].append((package,[os.path.join(local_path,'sample_site.cfg')]))
    return config

if __name__ == '__main__':
    from scipy_distutils_version import scipy_distutils_version
    print 'scipy_distutils Version',scipy_distutils_version
    from core import setup
    config = configuration(parent_path='')
    for k,v in config.items():
        if not v:
            del config[k]
    setup(version = scipy_distutils_version,
          description = "Changes to distutils needed for SciPy "\
          "-- mostly Fortran support",
          author = "Travis Oliphant, Eric Jones, and Pearu Peterson",
          author_email = "scipy-dev@scipy.org",
          license = "SciPy License (BSD Style)",
          url = 'http://www.scipy.org',
          **config
          )

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

class HPUXFCompiler(FCompiler):

    compiler_type = 'hpux'
    version_pattern =  r'HP F90 (?P<version>[^\s*,]*)'

    executables = {
        'version_cmd'  : ["f90", "+version"],
        'compiler_f77' : ["f90"],
        'compiler_fix' : ["f90"],
        'compiler_f90' : ["f90"],
        'linker_so'    : None,
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }
    module_dir_switch = None #XXX: fix me
    module_include_switch = None #XXX: fix me
    pic_flags = ['+pic=long']
    def get_flags(self):
        return self.pic_flags + ['+ppu']
    def get_flags_opt(self):
        return ['-O3']
    def get_libraries(self):
        return ['m']
    def get_version(self, force=0, ok_status=[256,0]):
        # XXX status==256 may indicate 'unrecognized option' or
        #     'no input file'. So, version_cmd needs more work.
        return FCompiler.get_version(self,force,ok_status)

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(10)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='hpux')
    compiler.customize()
    print compiler.get_version()

import os
import re
import sys

from fcompiler import FCompiler
import log

class IbmFCompiler(FCompiler):

    compiler_type = 'ibm'
    version_pattern =  r'xlf\(1\)\s*IBM XL Fortran Version (?P<version>[^\s*]*)'

    executables = {
        'version_cmd'  : ["xlf"],
        'compiler_f77' : ["xlf"],
        'compiler_fix' : ["xlf90", "-qfixed"],
        'compiler_f90' : ["xlf90"],
        'linker_so'    : ["xlf95"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    def get_flags(self):
        return ['-qextname']

    def get_flags_debug(self):
        return ['-g']

    def get_flags_linker_so(self):
        opt = []
        if sys.platform=='darwin':
            opt.append('-Wl,-bundle,-flat_namespace,-undefined,suppress')
        else:
            opt.append('-bshared')
        version = self.get_version(ok_status=[0,40])
        if version is not None:
            import tempfile
            xlf_cfg = '/etc/opt/ibmcmp/xlf/%s/xlf.cfg' % version
            new_cfg = tempfile.mktemp()+'_xlf.cfg'
            log.info('Creating '+new_cfg)
            fi = open(xlf_cfg,'r')
            fo = open(new_cfg,'w')
            crt1_match = re.compile(r'\s*crt\s*[=]\s*(?P<path>.*)/crt1.o').match
            for line in fi.readlines():
                m = crt1_match(line)
                if m:
                    fo.write('crt = %s/bundle1.o\n' % (m.group('path')))
                else:
                    fo.write(line)
            fi.close()
            fo.close()
            opt.append('-F'+new_cfg)
        return opt

    def get_flags_opt(self):
        return ['-O5']

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='ibm')
    compiler.customize()
    print compiler.get_version()


#http://www.compaq.com/fortran/docs/

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

class CompaqFCompiler(FCompiler):

    compiler_type = 'compaq'
    version_pattern = r'Compaq Fortran (?P<version>[^\s]*).*'

    if sys.platform[:5]=='linux':
        fc_exe = 'fort'
    else:
        fc_exe = 'f90'

    executables = {
        'version_cmd'  : [fc_exe, "-version"],
        'compiler_f77' : [fc_exe, "-f77rtl","-fixed"],
        'compiler_fix' : [fc_exe, "-fixed"],
        'compiler_f90' : [fc_exe],
        'linker_so'    : [fc_exe],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    module_dir_switch = None  #XXX Fix me
    module_include_switch = None #XXX Fix me

    def get_flags(self):
        return ['-assume no2underscore','-nomixed_str_len_arg']
    def get_flags_debug(self):
        return ['-g','-check bounds']
    def get_flags_opt(self):
        return ['-O4','-align dcommons','-assume bigarrays',
                '-assume nozsize','-math_library fast']
    def get_flags_arch(self):
        return ['-arch host', '-tune host']
    def get_flags_linker_so(self):
        if sys.platform[:5]=='linux':
            return ['-shared']
        return ['-shared','-Wl,-expect_unresolved,*']

class CompaqVisualFCompiler(FCompiler):

    compiler_type = 'compaqv'
    version_pattern = r'(DIGITAL|Compaq) Visual Fortran Optimizing Compiler'\
                      ' Version (?P<version>[^\s]*).*'

    compile_switch = '/compile_only'
    object_switch = '/object:'
    library_switch = '/OUT:'      #No space after /OUT:!

    static_lib_extension = ".lib"
    static_lib_format = "%s%s"
    module_dir_switch = None  #XXX Fix me
    module_include_switch = None #XXX Fix me

    ar_exe = 'lib.exe'
    fc_exe = 'DF'
    if sys.platform=='win32':
        from distutils.msvccompiler import MSVCCompiler
        ar_exe = MSVCCompiler().lib

    executables = {
        'version_cmd'  : ['DF', "/what"],
        'compiler_f77' : ['DF', "/f77rtl","/fixed"],
        'compiler_fix' : ['DF', "/fixed"],
        'compiler_f90' : ['DF'],
        'linker_so'    : ['DF'],
        'archiver'     : [ar_exe, "/OUT:"],
        'ranlib'       : None
        }

    def get_flags(self):
        return ['/nologo','/MD','/WX','/iface=(cref,nomixed_str_len_arg)',
                '/names:lowercase','/assume:underscore']
    def get_flags_opt(self):
        return ['/Ox','/fast','/optimize:5','/unroll:0','/math_library:fast']
    def get_flags_arch(self):
        return ['/threads']
    def get_flags_debug(self):
        return ['/debug']

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='compaq')
    compiler.customize()
    print compiler.get_version()

major = 0
minor = 3
micro = 1
#release_level = 'alpha'
release_level = ''
try:
    from __cvs_version__ import cvs_version
    cvs_minor = cvs_version[-3]
    cvs_serial = cvs_version[-1]
except ImportError,msg:
    print msg
    cvs_minor = 0
    cvs_serial = 0

if release_level:
    scipy_distutils_version = '%(major)d.%(minor)d.%(micro)d_%(release_level)s'\
                              '_%(cvs_minor)d.%(cvs_serial)d' % (locals ())
else:
    scipy_distutils_version = '%(major)d.%(minor)d.%(micro)d'\
                              '_%(cvs_minor)d.%(cvs_serial)d' % (locals ())

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler

class SunFCompiler(FCompiler):

    compiler_type = 'sun'
    version_pattern = r'(f90|f95): (Sun|Forte Developer 7|WorkShop 6 update \d+) Fortran 95 (?P<version>[^\s]+).*'

    executables = {
        'version_cmd'  : ["f90", "-V"],
        'compiler_f77' : ["f90"],
        'compiler_fix' : ["f90", "-fixed"],
        'compiler_f90' : ["f90"],
        'linker_so'    : ["f90","-Bdynamic","-G"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }
    module_dir_switch = '-moddir='
    module_include_switch = '-M'
    pic_flags = ['-xcode=pic32']

    def get_flags_f77(self):
        ret = ["-ftrap=%none"]
        if (self.get_version() or '') >= '7':
            ret.append("-f77")
        else:
            ret.append("-fixed")
        return ret
    def get_opt(self):
        return ['-fast','-dalign']
    def get_arch(self):
        return ['-xtarget=generic']
    def get_libraries(self):
        opt = []
        opt.extend(['fsu','sunmath','mvec','f77compat'])
        return opt

if __name__ == '__main__':
    from scipy_distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='sun')
    compiler.customize()
    print compiler.get_version()

standalone = 1


import sys
from distutils.dist import Distribution as OldDistribution
from distutils.errors import DistutilsSetupError
from types import *

class Distribution (OldDistribution):

    if sys.version[:3]<'2.2':
        # For backward compatibility. Use libraries
        # instead of fortran_libraries.
        fortran_libraries = None

    def return_false(self):
        # Used by build_ext.run()
        return 0

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
        return
   
    def get_data_files (self):
        print 'get_data_files'
        self.check_data_file_list()
        filenames = []
        
        # Gets data files specified
        for ext in self.data_files:
            filenames.extend(ext[1])

        return filenames

# http://developer.intel.com/software/products/compilers/flin/

import os
import sys

from cpuinfo import cpu
from fcompiler import FCompiler, dummy_fortran_file
from exec_command import find_executable

class IntelFCompiler(FCompiler):

    compiler_type = 'intel'
    version_pattern = r'Intel\(R\) Fortran Compiler for 32-bit '\
                      'applications, Version (?P<version>[^\s*]*)'

    for fc_exe in map(find_executable,['ifort','ifc']):
        if os.path.isfile(fc_exe):
            break

    executables = {
        'version_cmd'  : [fc_exe, "-FI -V -c %(fname)s.f -o %(fname)s.o" \
                          % {'fname':dummy_fortran_file()}],
        'compiler_f77' : [fc_exe,"-72","-w90","-w95"],
        'compiler_fix' : [fc_exe,"-FI"],
        'compiler_f90' : [fc_exe],
        'linker_so'    : [fc_exe,"-shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

    pic_flags = ['-KPIC']
    module_dir_switch = '-module ' # Don't remove ending space!
    module_include_switch = '-I'

    def get_flags(self):
        opt = self.pic_flags + ["-cm"]
        return opt

    def get_flags_opt(self):
        return ['-O3','-unroll']

    def get_flags_arch(self):
        opt = []
        if cpu.has_fdiv_bug():
            opt.append('-fdiv_check')
        if cpu.has_f00f_bug():
            opt.append('-0f_check')
        if cpu.is_PentiumPro() or cpu.is_PentiumII():
            opt.extend(['-tpp6','-xi'])
        elif cpu.is_PentiumIII():
            opt.append('-tpp6')
        elif cpu.is_Pentium():
            opt.append('-tpp5')
        elif cpu.is_PentiumIV():
            opt.extend(['-tpp7','-xW'])
        if cpu.has_mmx():
            opt.append('-xM')
        return opt

    def get_flags_linker_so(self):
        opt = FCompiler.get_flags_linker_so(self)
        v = self.get_version()
        if v and v >= '8.0':
            opt.append('-nofor_main')
        return opt

class IntelItaniumFCompiler(IntelFCompiler):
    compiler_type = 'intele'
    version_pattern = r'Intel\(R\) Fortran 90 Compiler Itanium\(TM\) Compiler'\
                      ' for the Itanium\(TM\)-based applications,'\
                      ' Version (?P<version>[^\s*]*)'

    for fc_exe in map(find_executable,['efort','efc','ifort']):
        if os.path.isfile(fc_exe):
            break

    executables = {
        'version_cmd'  : [fc_exe, "-FI -V -c %(fname)s.f -o %(fname)s.o" \
                          % {'fname':dummy_fortran_file()}],
        'compiler_f77' : [fc_exe,"-FI","-w90","-w95"],
        'compiler_fix' : [fc_exe,"-FI"],
        'compiler_f90' : [fc_exe],
        'linker_so'    : [fc_exe,"-shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }

class IntelVisualFCompiler(FCompiler):

    compiler_type = 'intelv'
    version_pattern = r'Intel\(R\) Fortran Compiler for 32-bit applications, '\
                      'Version (?P<version>[^\s*]*)'

    ar_exe = 'lib.exe'
    fc_exe = 'ifl'
    if sys.platform=='win32':
        from distutils.msvccompiler import MSVCCompiler
        ar_exe = MSVCCompiler().lib

    executables = {
        'version_cmd'  : [fc_exe, "-FI -V -c %(fname)s.f -o %(fname)s.o" \
                          % {'fname':dummy_fortran_file()}],
        'compiler_f77' : [fc_exe,"-FI","-w90","-w95"],
        'compiler_fix' : [fc_exe,"-FI","-4L72","-w"],
        'compiler_f90' : [fc_exe],
        'linker_so'    : [fc_exe,"-shared"],
        'archiver'     : [ar_exe, "/verbose", "/OUT:"],
        'ranlib'       : None
        }

    compile_switch = '/c '
    object_switch = '/Fo'     #No space after /Fo!
    library_switch = '/OUT:'  #No space after /OUT:!
    module_dir_switch = '/module:' #No space after /module:
    module_include_switch = '/I'

    def get_flags(self):
        opt = ['/nologo','/MD','/nbs','/Qlowercase','/us']
        return opt

    def get_flags_debug(self):
        return ['/4Yb','/d2']

    def get_flags_opt(self):
        return ['/O3','/Qip','/Qipo','/Qipo_obj']

    def get_flags_arch(self):
        opt = []
        if cpu.is_PentiumPro() or cpu.is_PentiumII():
            opt.extend(['/G6','/Qaxi'])
        elif cpu.is_PentiumIII():
            opt.extend(['/G6','/QaxK'])
        elif cpu.is_Pentium():
            opt.append('/G5')
        elif cpu.is_PentiumIV():
            opt.extend(['/G7','/QaxW'])
        if cpu.has_mmx():
            opt.append('/QaxM')
        return opt

class IntelItaniumVisualFCompiler(IntelVisualFCompiler):

    compiler_type = 'intelev'
    version_pattern = r'Intel\(R\) Fortran 90 Compiler Itanium\(TM\) Compiler'\
                      ' for the Itanium\(TM\)-based applications,'\
                      ' Version (?P<version>[^\s*]*)'

    fc_exe = 'efl' # XXX this is a wild guess
    ar_exe = IntelVisualFCompiler.ar_exe

    executables = {
        'version_cmd'  : [fc_exe, "-FI -V -c %(fname)s.f -o %(fname)s.o" \
                          % {'fname':dummy_fortran_file()}],
        'compiler_f77' : [fc_exe,"-FI","-w90","-w95"],
        'compiler_fix' : [fc_exe,"-FI","-4L72","-w"],
        'compiler_f90' : [fc_exe],
        'linker_so'    : [fc_exe,"-shared"],
        'archiver'     : [ar_exe, "/verbose", "/OUT:"],
        'ranlib'       : None
        }

if __name__ == '__main__':
    from distutils import log
    log.set_verbosity(2)
    from fcompiler import new_fcompiler
    compiler = new_fcompiler(compiler='intel')
    compiler.customize()
    print compiler.get_version()



import os
from scipy_distutils.core import setup, Extension
from distutils.dep_util import newer

fib3_f = '''
C FILE: FIB3.F
      SUBROUTINE FIB(A,N)
C
C     CALCULATE FIRST N FIBONACCI NUMBERS
C
      INTEGER N
      REAL*8 A(N)
Cf2py intent(in) n
Cf2py intent(out) a
Cf2py depend(n) a
      DO I=1,N
         IF (I.EQ.1) THEN
            A(I) = 0.0D0
         ELSEIF (I.EQ.2) THEN
            A(I) = 1.0D0
         ELSE 
            A(I) = A(I-1) + A(I-2)
         ENDIF
      ENDDO
      END
C END FILE FIB3.F
'''

package = 'gen_ext'

def source_func(ext, src_dir):
    source = os.path.join(src_dir,'fib3.f')
    if newer(__file__, source):
        f = open(source,'w')
        f.write(fib3_f)
        f.close()
    return [source]

ext = Extension(package+'.fib3',[source_func])

setup(
    name = package,
    ext_modules = [ext],
    packages = [package+'.tests',package],
    package_dir = {package:'.'})




import os
from scipy_distutils.core import setup, Extension

package = 'f2py_f90_ext'

ext = Extension(package+'.foo',['src/foo_free.f90'],
                include_dirs=['include'],
                f2py_options=['--include_paths','include'])

setup(
    name = package,
    ext_modules = [ext],
    packages = [package+'.tests',package],
    package_dir = {package:'.'})




import os
from scipy_distutils.core import setup, Extension

ext = Extension('f2py_ext.fib2',['src/fib2.pyf','src/fib1.f'])

setup(
    name = 'f2py_ext',
    ext_modules = [ext],
    packages = ['f2py_ext.tests','f2py_ext'],
    package_dir = {'f2py_ext':'.'})




import os
from scipy_distutils.core import setup, Extension

ext_c = Extension('swig_ext._example',['src/example.i','src/example.c'])
ext_cpp = Extension('swig_ext._example2',['src/zoo.i','src/zoo.cc'],
                    depends=['src/zoo.h'],include_dirs=['src'])

setup(
    name = 'swig_ext',
    ext_modules = [ext_c,ext_cpp],
    packages = ['swig_ext.tests','swig_ext'],
    package_dir = {'swig_ext':'.'})


# Need to override the build command to include building of fortran libraries
# This class must be used as the entry for the build key in the cmdclass
#    dictionary which is given to the setup command.

__revision__ = "$Id$"

import sys, os
from distutils import util
from distutils.command.build import build as old_build

class build(old_build):

    sub_commands = [('config_fc',     lambda *args: 1), # new feature
                    ('build_src',     old_build.has_ext_modules), # new feature
                    ('build_py',      old_build.has_pure_modules),
                    ('build_clib',    old_build.has_c_libraries),
                    ('build_ext',     old_build.has_ext_modules),
                    ('build_scripts', old_build.has_scripts),
                   ]

    def get_plat_specifier(self):
        """ Return a unique string that identifies this platform.
            The string is used to build path names and contains no
            spaces or control characters. (we hope)
        """        
        plat_specifier = ".%s-%s" % (util.get_platform(), sys.version[0:3])
        
        #--------------------------------------------------------------------
        # get rid of spaces -- added for OS X support.
        # Use '_' like python2.3
        #--------------------------------------------------------------------
        plat_specifier = plat_specifier.replace(' ','_')
        
        #--------------------------------------------------------------------
        # make lower case ?? is this desired'
        #--------------------------------------------------------------------
        #plat_specifier = plat_specifier.lower()
        
        return plat_specifier
        
    def finalize_options (self):

        #--------------------------------------------------------------------
        # This line is re-factored to a function -- everything else in the
        # function is identical to the finalize_options function in the
        # standard distutils build.
        #--------------------------------------------------------------------
        #plat_specifier = ".%s-%s" % (get_platform(), sys.version[0:3])        
        plat_specifier = self.get_plat_specifier()
        
        # 'build_purelib' and 'build_platlib' just default to 'lib' and
        # 'lib.<plat>' under the base build directory.  We only use one of
        # them for a given distribution, though --
        if self.build_purelib is None:
            self.build_purelib = os.path.join(self.build_base, 'lib')
        if self.build_platlib is None:
            self.build_platlib = os.path.join(self.build_base,
                                              'lib' + plat_specifier)

        # 'build_lib' is the actual directory that we will use for this
        # particular module distribution -- if user didn't supply it, pick
        # one of 'build_purelib' or 'build_platlib'.
        if self.build_lib is None:
            if self.distribution.ext_modules:
                self.build_lib = self.build_platlib
            else:
                self.build_lib = self.build_purelib

        # 'build_temp' -- temporary directory for compiler turds,
        # "build/temp.<plat>"
        if self.build_temp is None:
            self.build_temp = os.path.join(self.build_base,
                                           'temp' + plat_specifier)
        if self.build_scripts is None:
            self.build_scripts = os.path.join(self.build_base,
                                              'scripts-' + sys.version[0:3])

    # finalize_options ()


import sys
from distutils.core import Command

#XXX: Implement confic_cc for enhancing C/C++ compiler options.

class config_fc(Command):
    """ Distutils command to hold user specified options
    to Fortran compilers.

    config_fc command is used by the FCompiler.customize() method.
    """

    user_options = [
        ('fcompiler=',None,"specify Fortran compiler type"),
        ('f77exec=', None, "specify F77 compiler command"),
        ('f90exec=', None, "specify F90 compiler command"),
        ('f77flags=',None,"specify F77 compiler flags"),
        ('f90flags=',None,"specify F90 compiler flags"),
        ('opt=',None,"specify optimization flags"),
        ('arch=',None,"specify architecture specific optimization flags"),
        ('debug','g',"compile with debugging information"),
        ('noopt',None,"compile without optimization"),
        ('noarch',None,"compile without arch-dependent optimization"),
        ('help-fcompiler',None,"list available Fortran compilers"),
        ]

    boolean_options = ['debug','noopt','noarch','help-fcompiler']

    def initialize_options(self):
        self.fcompiler = None
        self.f77exec = None
        self.f90exec = None
        self.f77flags = None
        self.f90flags = None
        self.opt = None
        self.arch = None
        self.debug = None
        self.noopt = None
        self.noarch = None
        self.help_fcompiler = None
        return

    def finalize_options(self):
        if self.help_fcompiler:
            from scipy_distutils.fcompiler import show_fcompilers
            show_fcompilers(self.distribution)
            sys.exit()
        return

    def run(self):
        # Do nothing.
        return



""" Modified version of build_ext that handles fortran source files.
"""

import os
import string
import sys
from glob import glob
from types import *

from distutils.dep_util import newer_group, newer
from distutils.command.build_ext import build_ext as old_build_ext

from scipy_distutils.command.build_clib import get_headers,get_directories
from scipy_distutils import misc_util, log
from scipy_distutils.misc_util import filter_sources, has_f_sources, \
     has_cxx_sources
from distutils.errors import DistutilsFileError


class build_ext (old_build_ext):

    description = "build C/C++/F extensions (compile/link to build directory)"

    user_options = old_build_ext.user_options + [
        ('fcompiler=', None,
         "specify the Fortran compiler type"),
        ]

    def initialize_options(self):
        old_build_ext.initialize_options(self)
        self.fcompiler = None
        return

    def finalize_options(self):
        old_build_ext.finalize_options(self)
        self.set_undefined_options('config_fc',
                                   ('fcompiler', 'fcompiler'))
        return

    def run(self):
        if not self.extensions:
            return

        # Make sure that extension sources are complete.
        for ext in self.extensions:
            if not misc_util.all_strings(ext.sources):
                raise TypeError,'Extension "%s" sources contains unresolved'\
                      ' items (call build_src before build_ext).' % (ext.name)

        if self.distribution.has_c_libraries():
            build_clib = self.get_finalized_command('build_clib')
            self.library_dirs.append(build_clib.build_clib)
        else:
            build_clib = None

        # Not including C libraries to the list of
        # extension libraries automatically to prevent
        # bogus linking commands. Extensions must
        # explicitly specify the C libraries that they use.

        # Determine if Fortran compiler is needed.
        if build_clib and build_clib.fcompiler is not None:
            need_f_compiler = 1
        else:
            need_f_compiler = 0
            for ext in self.extensions:
                if has_f_sources(ext.sources):
                    need_f_compiler = 1
                    break
                if getattr(ext,'language','c') in ['f77','f90']:
                    need_f_compiler = 1
                    break

        # Determine if C++ compiler is needed.
        need_cxx_compiler = 0
        for ext in self.extensions:
            if has_cxx_sources(ext.sources):
                need_cxx_compiler = 1
                break
            if getattr(ext,'language','c')=='c++':
                need_cxx_compiler = 1
                break

        from distutils.ccompiler import new_compiler
        self.compiler = new_compiler(compiler=self.compiler,
                                     verbose=self.verbose,
                                     dry_run=self.dry_run,
                                     force=self.force)
        self.compiler.customize(self.distribution,need_cxx=need_cxx_compiler)
        self.compiler.customize_cmd(self)
        self.compiler.show_customization()
 
        # Initialize Fortran/C++ compilers if needed.
        if need_f_compiler:
            from scipy_distutils.fcompiler import new_fcompiler
            self.fcompiler = new_fcompiler(compiler=self.fcompiler,
                                           verbose=self.verbose,
                                           dry_run=self.dry_run,
                                           force=self.force)
            self.fcompiler.customize(self.distribution)
            self.fcompiler.customize_cmd(self)
            self.fcompiler.show_customization()

        # Build extensions
        self.build_extensions()
        return

    def swig_sources(self, sources):
        # Do nothing. Swig sources have beed handled in build_src command.
        return sources

    def build_extension(self, ext):
        sources = ext.sources
        if sources is None or type(sources) not in (ListType, TupleType):
            raise DistutilsSetupError, \
                  ("in 'ext_modules' option (extension '%s'), " +
                   "'sources' must be present and must be " +
                   "a list of source filenames") % ext.name
        sources = list(sources)

        if not sources:
            return

        fullname = self.get_ext_fullname(ext.name)
        if self.inplace:
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
        depends = sources + ext.depends

        if not (self.force or newer_group(depends, ext_filename, 'newer')):
            log.debug("skipping '%s' extension (up-to-date)", ext.name)
            return
        else:
            log.info("building '%s' extension", ext.name)

        extra_args = ext.extra_compile_args or []
        macros = ext.define_macros[:]
        for undef in ext.undef_macros:
            macros.append((undef,))

        c_sources, cxx_sources, f_sources, fmodule_sources = \
                   filter_sources(ext.sources)
        if self.compiler.compiler_type=='msvc':
            if cxx_sources:
                # Needed to compile kiva.agg._agg extension.
                extra_args.append('/Zm1000')
            # this hack works around the msvc compiler attributes
            # problem, msvc uses its own convention :(
            c_sources += cxx_sources
            cxx_sources = []

        if sys.version[:3]>='2.3':
            kws = {'depends':ext.depends}
        else:
            kws = {}

        c_objects = []
        if c_sources:
            log.info("compling C sources")
            c_objects = self.compiler.compile(c_sources,
                                              output_dir=self.build_temp,
                                              macros=macros,
                                              include_dirs=ext.include_dirs,
                                              debug=self.debug,
                                              extra_postargs=extra_args,
                                              **kws)
        if cxx_sources:
            log.info("compling C++ sources")

            old_compiler = self.compiler.compiler_so[0]
            self.compiler.compiler_so[0] = self.compiler.compiler_cxx[0]

            c_objects += self.compiler.compile(cxx_sources,
                                              output_dir=self.build_temp,
                                              macros=macros,
                                              include_dirs=ext.include_dirs,
                                              debug=self.debug,
                                              extra_postargs=extra_args,
                                              **kws)
            self.compiler.compiler_so[0] = old_compiler

        check_for_f90_modules = not not fmodule_sources

        if f_sources or fmodule_sources:
            extra_postargs = []
            include_dirs = ext.include_dirs[:]
            module_dirs = ext.module_dirs[:]

            if check_for_f90_modules:
                module_build_dir = os.path.join(\
                    self.build_temp,os.path.dirname(\
                    self.get_ext_filename(fullname)))

                self.mkpath(module_build_dir)
                if self.fcompiler.module_dir_switch is None:
                    existing_modules = glob('*.mod')
                extra_postargs += self.fcompiler.module_options(\
                    module_dirs,module_build_dir)

            f_objects = []
            if fmodule_sources:
                log.info("compling Fortran 90 module sources")
                f_objects = self.fcompiler.compile(fmodule_sources,
                                                   output_dir=self.build_temp,
                                                   macros=macros,
                                                   include_dirs=include_dirs,
                                                   debug=self.debug,
                                                   extra_postargs=extra_postargs,
                                                   depends=ext.depends)

            if check_for_f90_modules \
                   and self.fcompiler.module_dir_switch is None:
                for f in glob('*.mod'):
                    if f in existing_modules:
                        continue
                    try:
                        self.move_file(f, module_build_dir)
                    except DistutilsFileError:  # already exists in destination
                        os.remove(f)
                        
            if f_sources:
                log.info("compling Fortran sources")
                f_objects += self.fcompiler.compile(f_sources,
                                                    output_dir=self.build_temp,
                                                    macros=macros,
                                                    include_dirs=include_dirs,
                                                    debug=self.debug,
                                                    extra_postargs=extra_postargs,
                                                    depends=ext.depends)
        else:
            f_objects = []

        objects = c_objects + f_objects

        if ext.extra_objects:
            objects.extend(ext.extra_objects)
        extra_args = ext.extra_link_args or []

        try:
            old_linker_so_0 = self.compiler.linker_so[0]
        except:
            pass
        
        use_fortran_linker = getattr(ext,'language','c') in ['f77','f90']
        c_libraries = []
        c_library_dirs = []
        if use_fortran_linker or f_sources:
            use_fortran_linker = 1
        elif self.distribution.has_c_libraries():            
            build_clib = self.get_finalized_command('build_clib')
            f_libs = []
            for (lib_name, build_info) in build_clib.libraries:
                if has_f_sources(build_info.get('sources',[])):
                    f_libs.append(lib_name)
                if lib_name in ext.libraries:
                    # XXX: how to determine if c_libraries contain
                    # fortran compiled sources?
                    c_libraries.extend(build_info.get('libraries',[]))
                    c_library_dirs.extend(build_info.get('library_dirs',[]))
            for l in ext.libraries:
                if l in f_libs:
                    use_fortran_linker = 1
                    break

        # Always use system linker when using MSVC compiler.
        if self.compiler.compiler_type=='msvc' and use_fortran_linker:
            c_libraries.extend(self.fcompiler.libraries)
            c_library_dirs.extend(self.fcompiler.library_dirs)
            use_fortran_linker = 0

        if use_fortran_linker:
            if cxx_sources:
                # XXX: Which linker should be used, Fortran or C++?
                log.warn('mixing Fortran and C++ is untested')
            link = self.fcompiler.link_shared_object
            language = ext.language or self.fcompiler.detect_language(f_sources)
        else:
            link = self.compiler.link_shared_object
            if sys.version[:3]>='2.3':
                language = ext.language or self.compiler.detect_language(sources)
            else:
                language = ext.language
            if cxx_sources:
                self.compiler.linker_so[0] = self.compiler.compiler_cxx[0]

        if sys.version[:3]>='2.3':
            kws = {'target_lang':language}
        else:
            kws = {}

        link(objects, ext_filename,
             libraries=self.get_libraries(ext) + c_libraries,
             library_dirs=ext.library_dirs + c_library_dirs,
             runtime_library_dirs=ext.runtime_library_dirs,
             extra_postargs=extra_args,
             export_symbols=self.get_export_symbols(ext),
             debug=self.debug,
             build_temp=self.build_temp,**kws)

        try:
            self.compiler.linker_so[0] = old_linker_so_0
        except:
            pass

        return

    def get_source_files (self):
        self.check_extensions_list(self.extensions)
        filenames = []
        def visit_func(filenames,dirname,names):
            if os.path.basename(dirname) in ['CVS','.svn']:
                names[:] = []
                return
            for name in names:
                if name[-1] in "~#":
                    continue
                fullname = os.path.join(dirname,name)
                if os.path.isfile(fullname):
                    filenames.append(fullname)
        # Get sources and any include files in the same directory.
        for ext in self.extensions:
            sources = filter(lambda s:type(s) is StringType,ext.sources)
            filenames.extend(sources)
            filenames.extend(get_headers(get_directories(sources)))
            for d in ext.depends:
                if is_local_src_dir(d):
                    os.path.walk(d,visit_func,filenames)
                elif os.path.isfile(d):
                    filenames.append(d)
        return filenames

    def get_outputs (self):
        self.check_extensions_list(self.extensions)

        outputs = []
        for ext in self.extensions:
            if not ext.sources:
                continue
            fullname = self.get_ext_fullname(ext.name)
            outputs.append(os.path.join(self.build_lib,
                                        self.get_ext_filename(fullname)))
        return outputs

def is_local_src_dir(directory):
    """ Return true if directory is local directory.
    """
    abs_dir = os.path.abspath(directory)
    c = os.path.commonprefix([os.getcwd(),abs_dir])
    new_dir = abs_dir[len(c):].split(os.sep)
    if new_dir and not new_dir[0]:
        new_dir = new_dir[1:]
    if new_dir and new_dir[0]=='build':
        return 0
    new_dir = os.sep.join(new_dir)
    return os.path.isdir(new_dir)

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


from distutils.command.build_py import build_py as old_build_py

class build_py(old_build_py):

    def find_package_modules(self, package, package_dir):
        modules = old_build_py.find_package_modules(self, package, package_dir)

        # Find build_src generated *.py files.
        build_src = self.get_finalized_command('build_src')
        modules += build_src.py_modules.get(package,[])

        return modules

""" Build swig, f2py, weave, sources.
"""

import os
import re

from distutils.cmd import Command
from distutils.command import build_ext, build_py
from distutils.util import convert_path
from distutils.dep_util import newer_group, newer

from scipy_distutils import log
from scipy_distutils.misc_util import fortran_ext_match, all_strings
from scipy_distutils.from_template import process_str

class build_src(build_ext.build_ext):

    description = "build sources from SWIG, F2PY files or a function"

    user_options = [
        ('build-src=', 'd', "directory to \"build\" sources to"),
        ('f2pyflags=', None, "additonal flags to f2py"),
        ('swigflags=', None, "additional flags to swig"),
        ('force', 'f', "forcibly build everything (ignore file timestamps)"),
        ('inplace', 'i',
         "ignore build-lib and put compiled extensions into the source " +
         "directory alongside your pure Python modules"),
        ]

    boolean_options = ['force','inplace']

    help_options = []

    def initialize_options(self):
        self.extensions = None
        self.package = None
        self.py_modules = None
        self.build_src = None
        self.build_lib = None
        self.build_base = None
        self.force = None
        self.inplace = None
        self.package_dir = None
        self.f2pyflags = None
        self.swigflags = None
        return

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_base', 'build_base'),
                                   ('build_lib', 'build_lib'),
                                   ('force', 'force'))
        if self.package is None:
            self.package = self.distribution.ext_package
        self.extensions = self.distribution.ext_modules
        self.libraries = self.distribution.libraries or []
        self.py_modules = self.distribution.py_modules
        if self.build_src is None:
            self.build_src = os.path.join(self.build_base, 'src')
        if self.inplace is None:
            build_ext = self.get_finalized_command('build_ext')
            self.inplace = build_ext.inplace

        # py_modules is used in build_py.find_package_modules
        self.py_modules = {}

        if self.f2pyflags is None:
            self.f2pyflags = []
        else:
            self.f2pyflags = self.f2pyflags.split() # XXX spaces??

        if self.swigflags is None:
            self.swigflags = []
        else:
            self.swigflags = self.swigflags.split() # XXX spaces??
        return

    def run(self):
        if not (self.extensions or self.libraries):
            return
        self.build_sources()
        return

    def build_sources(self):
        self.check_extensions_list(self.extensions)

        for ext in self.extensions:
            self.build_extension_sources(ext)

        for libname_info in self.libraries:
            self.build_library_sources(*libname_info)

        return

    def build_library_sources(self, lib_name, build_info):
        sources = list(build_info.get('sources',[]))

        if not sources:
            return

        log.info('building library "%s" sources' % (lib_name))

        sources = self.generate_sources(sources, (lib_name, build_info))

        build_info['sources'] = sources
        return

    def build_extension_sources(self, ext):
        sources = list(ext.sources)

        log.info('building extension "%s" sources' % (ext.name))

        fullname = self.get_ext_fullname(ext.name)

        modpath = fullname.split('.')
        package = '.'.join(modpath[0:-1])

        if self.inplace:
            build_py = self.get_finalized_command('build_py')
            self.ext_target_dir = build_py.get_package_dir(package)

        sources = self.generate_sources(sources, ext)

        sources = self.template_sources(sources, ext)
        
        sources = self.swig_sources(sources, ext)

        sources = self.f2py_sources(sources, ext)

        sources, py_files = self.filter_py_files(sources)

        if not self.py_modules.has_key(package):
            self.py_modules[package] = []
        modules = []
        for f in py_files:
            module = os.path.splitext(os.path.basename(f))[0]
            modules.append((package, module, f))
        self.py_modules[package] += modules

        ext.sources = sources
        return

    def generate_sources(self, sources, extension):
        new_sources = []
        func_sources = []
        for source in sources:
            if type(source) is type(''):
                new_sources.append(source)
            else:
                func_sources.append(source)
        if not func_sources:
            return new_sources
        if self.inplace:
            build_dir = self.ext_target_dir
        else:
            if type(extension) is type(()):
                name = extension[0]
            else:
                name = extension.name
            build_dir = os.path.join(*([self.build_src]\
                                       +name.split('.')[:-1]))
        self.mkpath(build_dir)
        for func in func_sources:
            source = func(extension, build_dir)
            if type(source) is type([]):
                [log.info("  adding '%s' to sources." % (s)) for s in source]
                new_sources.extend(source)
            else:
                log.info("  adding '%s' to sources." % (source))
                new_sources.append(source)
        return new_sources

    def filter_py_files(self, sources):
        new_sources = []
        py_files = []
        for source in sources:
            (base, ext) = os.path.splitext(source)
            if ext=='.py':        
                py_files.append(source)
            else:
                new_sources.append(source)
        return new_sources, py_files

    def template_sources(self, sources, extension):
        new_sources = []
        for source in sources:
            (base, ext) = os.path.splitext(source)
            if ext == '.src':  # Template file
                if self.inplace:
                    target_dir = os.path.dirname(base)
                else:
                    target_dir = appendpath(self.build_src, os.path.dirname(base))
                self.mkpath(target_dir)
                target_file = os.path.join(target_dir,os.path.basename(base))
                if (self.force or newer(source, target_file)):
                    fid = open(source)
                    outstr = process_str(fid.read())
                    fid.close()
                    fid = open(target_file,'w')
                    fid.write(outstr)
                    fid.close()
                new_sources.append(target_file)
            else:
                new_sources.append(source)
        return new_sources            
        
    def f2py_sources(self, sources, extension):
        new_sources = []
        f2py_sources = []
        f_sources = []
        f2py_targets = {}
        target_dirs = []
        ext_name = extension.name.split('.')[-1]
        skip_f2py = 0

        for source in sources:
            (base, ext) = os.path.splitext(source)
            if ext == '.pyf': # F2PY interface file
                if self.inplace:
                    target_dir = os.path.dirname(base)
                else:
                    target_dir = appendpath(self.build_src, os.path.dirname(base))
                if os.path.isfile(source):
                    name = get_f2py_modulename(source)
                    assert name==ext_name,'mismatch of extension names: '\
                           +source+' provides'\
                           ' '+`name`+' but expected '+`ext_name`
                    target_file = os.path.join(target_dir,name+'module.c')
                else:
                    log.debug('  source %s does not exist: skipping f2py\'ing.' \
                              % (source))
                    name = ext_name
                    skip_f2py = 1
                    target_file = os.path.join(target_dir,name+'module.c')
                    if not os.path.isfile(target_file):
                        log.debug('  target %s does not exist:\n   '\
                                  'Assuming %smodule.c was generated with '\
                                  '"build_src --inplace" command.' \
                                  % (target_file, name))
                        target_dir = os.path.dirname(base)
                        target_file = os.path.join(target_dir,name+'module.c')
                        assert os.path.isfile(target_file),`target_file`+' missing'
                        log.debug('   Yes! Using %s as up-to-date target.' \
                                  % (target_file))
                target_dirs.append(target_dir)
                f2py_sources.append(source)
                f2py_targets[source] = target_file
                new_sources.append(target_file)
            elif fortran_ext_match(ext):
                f_sources.append(source)
            else:
                new_sources.append(source)

        if not (f2py_sources or f_sources):
            return new_sources

        map(self.mkpath, target_dirs)

        f2py_options = extension.f2py_options + self.f2pyflags
        if f2py_sources:
            assert len(f2py_sources)==1,\
                   'only one .pyf file is allowed per extension module but got'\
                   ' more:'+`f2py_sources`
            source = f2py_sources[0]
            target_file = f2py_targets[source]
            target_dir = os.path.dirname(target_file)
            depends = [source] + extension.depends
            if (self.force or newer_group(depends, target_file,'newer')) \
                   and not skip_f2py:
                log.info("f2py: %s" % (source))
                import f2py2e
                f2py2e.run_main(f2py_options + ['--build-dir',target_dir,source])
            else:
                log.debug("  skipping '%s' f2py interface (up-to-date)" % (source))
        else:
            #XXX TODO: --inplace support for sdist command
            target_dir = self.build_src
            target_file = os.path.join(target_dir,ext_name + 'module.c')
            new_sources.append(target_file)
            depends = f_sources + extension.depends
            if (self.force or newer_group(depends, target_file, 'newer')) \
                   and not skip_f2py:
                import f2py2e
                log.info("f2py:> %s" % (target_file))
                self.mkpath(target_dir)
                f2py2e.run_main(f2py_options + ['--lower',
                                                '--build-dir',target_dir]+\
                                ['-m',ext_name]+f_sources)
            else:
                log.debug("  skipping f2py fortran files for '%s' (up-to-date)"\
                          % (target_file))

        assert os.path.isfile(target_file),`target_file`+' missing'

        target_c = os.path.join(self.build_src,'fortranobject.c')
        target_h = os.path.join(self.build_src,'fortranobject.h')
        log.info("  adding '%s' to sources." % (target_c))
        new_sources.append(target_c)
        if self.build_src not in extension.include_dirs:
            log.info("  adding '%s' to include_dirs." \
                     % (self.build_src))
            extension.include_dirs.append(self.build_src)

        if not skip_f2py:
            import f2py2e
            d = os.path.dirname(f2py2e.__file__)
            source_c = os.path.join(d,'src','fortranobject.c')
            source_h = os.path.join(d,'src','fortranobject.h')
            if newer(source_c,target_c) or newer(source_h,target_h):
                self.mkpath(os.path.dirname(target_c))
                self.copy_file(source_c,target_c)
                self.copy_file(source_h,target_h)
        else:
            assert os.path.isfile(target_c),`target_c` + ' missing'
            assert os.path.isfile(target_h),`target_h` + ' missing'
   
        for name_ext in ['-f2pywrappers.f','-f2pywrappers2.f90']:
            filename = os.path.join(target_dir,ext_name + name_ext)
            if os.path.isfile(filename):
                log.info("  adding '%s' to sources." % (filename))
                f_sources.append(filename)

        return new_sources + f_sources

    def swig_sources(self, sources, extension):
        new_sources = []
        swig_sources = []
        swig_targets = {}
        target_dirs = []
        py_files = []     # swig generated .py files
        target_ext = '.c'
        typ = None
        is_cpp = 0
        skip_swig = 0
        ext_name = extension.name.split('.')[-1]

        for source in sources:
            (base, ext) = os.path.splitext(source)
            if ext == '.i': # SWIG interface file
                if self.inplace:
                    target_dir = os.path.dirname(base)
                    py_target_dir = self.ext_target_dir
                else:
                    target_dir = appendpath(self.build_src, os.path.dirname(base))
                    py_target_dir = target_dir
                if os.path.isfile(source):
                    name = get_swig_modulename(source)
                    assert name==ext_name[1:],'mismatch of extension names: '\
                           +source+' provides'\
                           ' '+`name`+' but expected '+`ext_name[1:]`
                    if typ is None:
                        typ = get_swig_target(source)
                        is_cpp = typ=='c++'
                        if is_cpp:
                            target_ext = '.cpp'
                    else:
                        assert typ == get_swig_target(source),`typ`
                    target_file = os.path.join(target_dir,'%s_wrap%s' \
                                               % (name, target_ext))
                else:
                    log.debug('  source %s does not exist: skipping swig\'ing.' \
                             % (source))
                    name = ext_name[1:]
                    skip_swig = 1
                    target_file = _find_swig_target(target_dir, name)
                    if not os.path.isfile(target_file):
                        log.debug('  target %s does not exist:\n   '\
                                  'Assuming %s_wrap.{c,cpp} was generated with '\
                                  '"build_src --inplace" command.' \
                                 % (target_file, name))
                        target_dir = os.path.dirname(base)
                        target_file = _find_swig_target(target_dir, name)
                        assert os.path.isfile(target_file),`target_file`+' missing'
                        log.debug('   Yes! Using %s as up-to-date target.' \
                                  % (target_file))
                target_dirs.append(target_dir)
                new_sources.append(target_file)
                py_files.append(os.path.join(py_target_dir, name+'.py'))
                swig_sources.append(source)
                swig_targets[source] = new_sources[-1]
            else:
                new_sources.append(source)

        if not swig_sources:
            return new_sources

        if skip_swig:
            return new_sources + py_files

        map(self.mkpath, target_dirs)
        swig = self.find_swig()
        swig_cmd = [swig, "-python"]
        if is_cpp:
            swig_cmd.append('-c++')
        for d in extension.include_dirs:
            swig_cmd.append('-I'+d)
        for source in swig_sources:
            target = swig_targets[source]
            depends = [source] + extension.depends
            if self.force or newer_group(depends, target, 'newer'):
                log.info("%s: %s" % (os.path.basename(swig) \
                                     + (is_cpp and '++' or ''), source))
                self.spawn(swig_cmd + self.swigflags \
                           + ["-o", target, '-outdir', py_target_dir, source])
            else:
                log.debug("  skipping '%s' swig interface (up-to-date)" \
                         % (source))

        return new_sources + py_files

def appendpath(prefix,path):
    if os.path.isabs(path):
        absprefix = os.path.abspath(prefix)
        d = os.path.commonprefix([absprefix,path])
        subpath = path[len(d):]
        assert not os.path.isabs(subpath),`subpath`
        return os.path.join(prefix,subpath)
    return os.path.join(prefix, path)

#### SWIG related auxiliary functions ####
_swig_module_name_match = re.compile(r'\s*%module\s*(?P<name>[\w_]+)',
                                     re.I).match
_has_c_header = re.compile(r'-[*]-\s*c\s*-[*]-',re.I).search
_has_cpp_header = re.compile(r'-[*]-\s*c[+][+]\s*-[*]-',re.I).search

def get_swig_target(source):
    f = open(source,'r')
    result = 'c'
    line = f.readline()
    if _has_cpp_header(line):
        result = 'c++'
    if _has_c_header(line):
        result = 'c'
    f.close()
    return result

def get_swig_modulename(source):
    f = open(source,'r')
    f_readlines = getattr(f,'xreadlines',f.readlines)
    for line in f_readlines():
        m = _swig_module_name_match(line)
        if m:
            name = m.group('name')
            break
    f.close()
    return name

def _find_swig_target(target_dir,name):
    for ext in ['.cpp','.c']:
        target = os.path.join(target_dir,'%s_wrap%s' % (name, ext))
        if os.path.isfile(target):
            break
    return target

#### F2PY related auxiliary functions ####

_f2py_module_name_match = re.compile(r'\s*python\s*module\s*(?P<name>[\w_]+)',
                                re.I).match
_f2py_user_module_name_match = re.compile(r'\s*python\s*module\s*(?P<name>[\w_]*?'\
                                     '__user__[\w_]*)',re.I).match

def get_f2py_modulename(source):
    name = None
    f = open(source)
    f_readlines = getattr(f,'xreadlines',f.readlines)
    for line in f_readlines():
        m = _f2py_module_name_match(line)
        if m:
            if _f2py_user_module_name_match(line): # skip *__user__* names
                continue
            name = m.group('name')
            break
    f.close()
    return name

##########################################

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
           'config_compiler',
           'build_src',
           'build_ext',
           'build_clib',
           'install',
           'install_data',
           'install_headers',
           'sdist',
          ] + distutils_all


import os
import sys

from distutils.command.sdist import *
from distutils.command.sdist import sdist as old_sdist
from scipy_distutils import log
from scipy_distutils import line_endings

class sdist(old_sdist):
    def add_defaults (self):
        old_sdist.add_defaults(self)

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

        
    
        if 0 and hasattr(os, 'link'):        # can make hard links on this system
            link = 'hard'
            msg = "making hard links in %s..." % base_dir
        else:                           # nope, have to copy
            link = None
            msg = "copying files to %s..." % base_dir
        self._use_hard_link = not not link

        if not files:
            log.warn("no files to distribute -- empty manifest?")
        else:
            log.info(msg)
        
        dest_files = [os.path.join(base_dir,file) for file in dest_files]
        file_pairs = zip(files,dest_files)
        for file,dest in file_pairs:
            if not os.path.isfile(file):
                log.warn("'%s' not a regular file -- skipping", file)
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

    def make_distribution (self):
        """ Overridden to force a build of zip files to have Windows line 
            endings and tar balls to have Unix line endings.
            
            Create the source distribution(s).  First, we create the release
            tree with 'make_release_tree()'; then, we create all required
            archive files (according to 'self.formats') from the release tree.
            Finally, we clean up by blowing away the release tree (unless
            'self.keep_temp' is true).  The list of archive files created is
            stored so it can be retrieved later by 'get_archive_files()'.
        """
        # Don't warn about missing meta-data here -- should be (and is!)
        # done elsewhere.
        base_dir = self.distribution.get_fullname()
        base_name = os.path.join(self.dist_dir, base_dir)
        files = map(os.path.abspath, self.filelist.files)
        self.make_release_tree(base_dir, files)
        archive_files = []              # remember names of files we create
        for fmt in self.formats:
            modified_files,restore_func = self.convert_line_endings(base_dir,fmt)
            file = self.make_archive(base_name, fmt, base_dir=base_dir)
            archive_files.append(file)
            if self._use_hard_link:
                map(restore_func,modified_files)

        self.archive_files = archive_files

        if not self.keep_temp:
            dir_util.remove_tree(base_dir, self.verbose, self.dry_run)

    def convert_line_endings(self,base_dir,fmt):
        """ Convert all text files in a tree to have correct line endings.
            
            gztar --> \n   (Unix style)
            zip   --> \r\n (Windows style)
        """
        if fmt == 'gztar':
            return line_endings.dos2unix_dir(base_dir),line_endings.unix2dos
        elif fmt == 'zip':
            return line_endings.unix2dos_dir(base_dir),line_endings.dos2unix
        return [],lambda a:None

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
    results = [file[len(base):] for file in files]
    return results

def find_common_base(files):
    """ Find the "greatest common base directory" of a list of files
    """
    if not files:
        return ''
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

""" Modified version of build_clib that handles fortran source files.
"""

import os
import string
import sys
import re
from glob import glob
from types import *
from distutils.command.build_clib import build_clib as old_build_clib
from distutils.command.build_clib import show_compilers

from scipy_distutils import log, misc_util
from distutils.dep_util import newer_group
from scipy_distutils.misc_util import filter_sources, \
     has_f_sources, has_cxx_sources

def get_headers(directory_list):
    # get *.h files from list of directories
    headers = []
    for dir in directory_list:
        head = glob(os.path.join(dir,"*.h")) #XXX: *.hpp files??
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

class build_clib(old_build_clib):

    description = "build C/C++/F libraries used by Python extensions"

    user_options = old_build_clib.user_options + [
        ('fcompiler=', None,
         "specify the Fortran compiler type"),
        ]

    def initialize_options(self):
        old_build_clib.initialize_options(self)
        self.fcompiler = None
        return

    def finalize_options(self):
        old_build_clib.finalize_options(self)
        self.set_undefined_options('build_ext',
                                   ('fcompiler', 'fcompiler'))

        #XXX: This is hackish and probably unnecessary,
        #     could we get rid of this?
        from scipy_distutils import misc_util
        extra_includes = misc_util.get_environ_include_dirs()
        if extra_includes:
            print "XXX: are you sure you'll need PYTHONINCLUDES env. variable??"
        self.include_dirs.extend(extra_includes)

        return

    def have_f_sources(self):
        for (lib_name, build_info) in self.libraries:
            if has_f_sources(build_info.get('sources',[])):
                return 1
        return 0

    def have_cxx_sources(self):
        for (lib_name, build_info) in self.libraries:
            if has_cxx_sources(build_info.get('sources',[])):
                return 1
        return 0

    def run(self):
        if not self.libraries:
            return

        # Make sure that library sources are complete.
        for (lib_name, build_info) in self.libraries:
            if not misc_util.all_strings(build_info.get('sources',[])):
                raise TypeError,'Library "%s" sources contains unresolved'\
                      ' items (call build_src before built_clib).' % (lib_name)

        from distutils.ccompiler import new_compiler
        self.compiler = new_compiler(compiler=self.compiler,
                                     dry_run=self.dry_run,
                                     force=self.force)
        self.compiler.customize(self.distribution,need_cxx=self.have_cxx_sources())

        libraries = self.libraries
        self.libraries = None
        self.compiler.customize_cmd(self)
        self.libraries = libraries

        self.compiler.show_customization()

        if self.have_f_sources():
            from scipy_distutils.fcompiler import new_fcompiler
            self.fcompiler = new_fcompiler(compiler=self.fcompiler,
                                           verbose=self.verbose,
                                           dry_run=self.dry_run,
                                           force=self.force)
            self.fcompiler.customize(self.distribution)
    
            libraries = self.libraries
            self.libraries = None
            self.fcompiler.customize_cmd(self)
            self.libraries = libraries

            self.fcompiler.show_customization()

        self.build_libraries(self.libraries)
        return

    def get_source_files(self):
        from build_ext import is_local_src_dir
        self.check_library_list(self.libraries)
        filenames = []
        def visit_func(filenames,dirname,names):
            if os.path.basename(dirname) in ['CVS','.svn']:
                names[:] = []
                return
            for name in names:
                if name[-1] in "#~":
                    continue
                fullname = os.path.join(dirname,name)
                if os.path.isfile(fullname):
                    filenames.append(fullname)
        for (lib_name, build_info) in self.libraries:
            sources = build_info.get('sources',[])
            sources = filter(lambda s:type(s) is StringType,sources)
            filenames.extend(sources)
            filenames.extend(get_headers(get_directories(sources)))
            depends = build_info.get('depends',[])
            for d in depends:
                if is_local_src_dir(d):
                    os.path.walk(d,visit_func,filenames)
                elif os.path.isfile(d):
                    filenames.append(d)
        return filenames

    def build_libraries(self, libraries):

        compiler = self.compiler
        fcompiler = self.fcompiler

        for (lib_name, build_info) in libraries:
            sources = build_info.get('sources')
            if sources is None or type(sources) not in (ListType, TupleType):
                raise DistutilsSetupError, \
                      ("in 'libraries' option (library '%s'), " +
                       "'sources' must be present and must be " +
                       "a list of source filenames") % lib_name
            sources = list(sources)

            lib_file = compiler.library_filename(lib_name,
                                                 output_dir=self.build_clib)

            depends = sources + build_info.get('depends',[])
            if not (self.force or newer_group(depends, lib_file, 'newer')):
                log.debug("skipping '%s' library (up-to-date)", lib_name)
                continue
            else:
                log.info("building '%s' library", lib_name)

            macros = build_info.get('macros')
            include_dirs = build_info.get('include_dirs')
            extra_postargs = build_info.get('extra_compiler_args') or []

            c_sources, cxx_sources, f_sources, fmodule_sources \
                       = filter_sources(sources)

            if self.compiler.compiler_type=='msvc':
                # this hack works around the msvc compiler attributes
                # problem, msvc uses its own convention :(
                c_sources += cxx_sources
                cxx_sources = []

            if fmodule_sources:
                print 'XXX: Fortran 90 module support not implemented or tested'
                f_sources.extend(fmodule_sources)

            objects = []
            if c_sources:
                log.info("compling C sources")
                objects = compiler.compile(c_sources,
                                           output_dir=self.build_temp,
                                           macros=macros,
                                           include_dirs=include_dirs,
                                           debug=self.debug,
                                           extra_postargs=extra_postargs)

            if cxx_sources:
                log.info("compling C++ sources")
                old_compiler = self.compiler.compiler_so[0]
                self.compiler.compiler_so[0] = self.compiler.compiler_cxx[0]

                cxx_objects = compiler.compile(cxx_sources,
                                               output_dir=self.build_temp,
                                               macros=macros,
                                               include_dirs=include_dirs,
                                               debug=self.debug,
                                               extra_postargs=extra_postargs)
                objects.extend(cxx_objects)

                self.compiler.compiler_so[0] = old_compiler

            if f_sources:
                log.info("compling Fortran sources")
                f_objects = fcompiler.compile(f_sources,
                                              output_dir=self.build_temp,
                                              macros=macros,
                                              include_dirs=include_dirs,
                                              debug=self.debug,
                                              extra_postargs=[])
                objects.extend(f_objects)

            self.compiler.create_static_lib(objects, lib_name,
                                            output_dir=self.build_clib,
                                            debug=self.debug)
        return

from types import StringType
from distutils.command.install import *
from distutils.command.install import install as old_install
from distutils.util import convert_path
from distutils.file_util import write_file
from distutils.errors import DistutilsOptionError
from scipy_distutils import log

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
            log.warn("path file '%s' not created" % filename)

from distutils.command.install_data import *
from distutils.command.install_data import install_data as old_install_data

#data installer with improved intelligence over distutils
#data files are copied into the project directory instead
#of willy-nilly
class install_data (old_install_data):
    def finalize_options (self):
        self.set_undefined_options('install',
                                   ('install_lib', 'install_dir'),
                                   ('root', 'root'),
                                   ('force', 'force'),
                                  )

"""
Wrapper functions to more user-friendly calling of certain math functions
whose output is different than the input in certain domains of the input.
"""

__all__ = ['sqrt', 'log', 'log2','logn','log10', 'power', 'arccos',
           'arcsin', 'arctanh']

import Numeric

from type_check import isreal, asarray
from function_base import any
import fastumath
from fastumath import *

__all__.extend([key for key in dir(fastumath) \
                if key[0]!='_' and key not in __all__])

def _tocomplex(arr):
    if arr.typecode() in ['f', 's', 'b', '1','w']:
        return arr.astype('F')
    else:
        return arr.astype('D')

def sqrt(x):
    x = asarray(x)
    if isreal(x) and any(x<0):
        x = _tocomplex(x)
    return fastumath.sqrt(x)

def log(x):
    x = asarray(x)
    if isreal(x) and any(x<0):
        x = _tocomplex(x)
    return fastumath.log(x)

def log10(x):
    x = asarray(x)
    if isreal(x) and any(x<0):
        x = _tocomplex(x)
    return fastumath.log10(x)    

def logn(n,x):
    """ Take log base n of x.
    """
    x = asarray(x)
    if isreal(x) and any(x<0):
        x = _tocomplex(x)
    if isreal(n) and (n<0):
        n = _tocomplex(n)
    return fastumath.log(x)/fastumath.log(n)

def log2(x):
    """ Take log base 2 of x.
    """
    x = asarray(x)
    if isreal(x) and any(x<0):
        x = _tocomplex(x)
    return fastumath.log(x)/fastumath.log(2)


def power(x, p):
    x = asarray(x)
    if isreal(x) and any(x<0):
        x = _tocomplex(x)
    return fastumath.power(x, p)
    
def arccos(x):
    x = asarray(x)
    if isreal(x) and any(abs(x)>1):
        x = _tocomplex(x)
    return fastumath.arccos(x)

def arcsin(x):
    x = asarray(x)
    if isreal(x) and any(abs(x)>1):
        x = _tocomplex(x)
    return fastumath.arcsin(x)

def arctanh(x):
    x = asarray(x)
    if isreal(x) and any(abs(x)>1):
        x = _tocomplex(x)
    return fastumath.arctanh(x)

#!/usr/bin/env python
"""
Postpone module import to future.

Python versions: 1.5.2 - 2.3.x
Author: Pearu Peterson <pearu@cens.ioc.ee>
Created: March 2003
$Revision$
$Date$
"""
__all__ = ['ppimport','ppimport_attr','ppresolve']

import os
import sys
import string
import types
import traceback

DEBUG=0

_ppimport_is_enabled = 1
def enable():
    """ Enable postponed importing."""
    global _ppimport_is_enabled
    _ppimport_is_enabled = 1

def disable():
    """ Disable postponed importing."""
    global _ppimport_is_enabled
    _ppimport_is_enabled = 0

class PPImportError(ImportError):
    pass

def _get_so_ext(_cache={}):
    so_ext = _cache.get('so_ext')
    if so_ext is None:
        if sys.platform[:5]=='linux':
            so_ext = '.so'
        else:
            try:
                # if possible, avoid expensive get_config_vars call
                from distutils.sysconfig import get_config_vars
                so_ext = get_config_vars('SO')[0] or ''
            except ImportError:
                #XXX: implement hooks for .sl, .dll to fully support
                #     Python 1.5.x   
                so_ext = '.so'
        _cache['so_ext'] = so_ext
    return so_ext

def _get_frame(level=0):
    try:
        return sys._getframe(level+1)
    except AttributeError:
        # Python<=2.0 support
        frame = sys.exc_info()[2].tb_frame
        for i in range(level+1):
            frame = frame.f_back
        return frame

def ppimport_attr(module, name):
    """ ppimport(module, name) is 'postponed' getattr(module, name)
    """
    global _ppimport_is_enabled
    if _ppimport_is_enabled and isinstance(module, _ModuleLoader):
        return _AttrLoader(module, name)
    return getattr(module, name)

class _AttrLoader:
    def __init__(self, module, name):
        self.__dict__['_ppimport_attr_module'] = module
        self.__dict__['_ppimport_attr_name'] = name

    def _ppimport_attr_getter(self):
        module = self.__dict__['_ppimport_attr_module']
        if isinstance(module, _ModuleLoader):
            # in case pp module was loaded by other means
            module = sys.modules[module.__name__]
        attr = getattr(module,
                       self.__dict__['_ppimport_attr_name'])
        try:
            d = attr.__dict__
            if d is not None:
                self.__dict__ = d
        except AttributeError:
            pass
        self.__dict__['_ppimport_attr'] = attr
        return attr

    def __getattr__(self, name):
        try:
            attr = self.__dict__['_ppimport_attr']
        except KeyError:
            attr = self._ppimport_attr_getter()
        if name=='_ppimport_attr':
            return attr
        return getattr(attr, name)

    def __repr__(self):
        if self.__dict__.has_key('_ppimport_attr'):
            return repr(self._ppimport_attr)
        module = self.__dict__['_ppimport_attr_module']
        name = self.__dict__['_ppimport_attr_name']
        return "<attribute %s of %s>" % (`name`,`module`)

    __str__ = __repr__

    # For function and class attributes.
    def __call__(self, *args, **kwds):
        return self._ppimport_attr(*args,**kwds)



def _is_local_module(p_dir,name,suffices):
    base = os.path.join(p_dir,name)
    for suffix in suffices:
        if os.path.isfile(base+suffix):
            if p_dir:
                return base+suffix
            return name+suffix

def ppimport(name):
    """ ppimport(name) -> module or module wrapper

    If name has been imported before, return module. Otherwise
    return ModuleLoader instance that transparently postpones
    module import until the first attempt to access module name
    attributes.
    """
    global _ppimport_is_enabled

    level = 1
    p_frame = _get_frame(level)
    while not p_frame.f_locals.has_key('__name__'):
        level = level + 1
        p_frame = _get_frame(level)

    p_name = p_frame.f_locals['__name__']
    if p_name=='__main__':
        p_dir = ''
        fullname = name
    elif p_frame.f_locals.has_key('__path__'):
        # python package
        p_path = p_frame.f_locals['__path__']
        p_dir = p_path[0]
        fullname = p_name + '.' + name
    else:
        # python module
        p_file = p_frame.f_locals['__file__']
        p_dir = os.path.dirname(p_file)
        fullname = p_name + '.' + name

    # module may be imported already
    module = sys.modules.get(fullname)
    if module is not None:
        if _ppimport_is_enabled:
            return module
        return module._ppimport_importer()

    so_ext = _get_so_ext()
    py_exts = ('.py','.pyc','.pyo')
    so_exts = (so_ext,'module'+so_ext)
    
    for d,n,fn,e in [\
        # name is local python module or local extension module
        (p_dir, name, fullname, py_exts+so_exts),
        # name is local package
        (os.path.join(p_dir, name), '__init__', fullname, py_exts),
        # name is package in parent directory (scipy specific)
        (os.path.join(os.path.dirname(p_dir), name), '__init__', name, py_exts),
        ]:
        location = _is_local_module(d, n, e)
        if location is not None:
            fullname = fn
            break

    if location is None:
        # name is to be looked in python sys.path.
        fullname = name
        location = 'sys.path'

    # Try once more if module is imported.
    # This covers the case when importing from python module
    module = sys.modules.get(fullname)
    if module is not None:
        if _ppimport_is_enabled:
            return module
        return module._ppimport_importer()
    # It is OK if name does not exists. The ImportError is
    # postponed until trying to use the module.

    loader = _ModuleLoader(fullname,location,p_frame=p_frame)
    if _ppimport_is_enabled:
        return loader

    return loader._ppimport_importer()


class _ModuleLoader:
    # Don't use it directly. Use ppimport instead.

    def __init__(self,name,location,p_frame=None):

        # set attributes, avoid calling __setattr__
        self.__dict__['__name__'] = name
        self.__dict__['__file__'] = location
        self.__dict__['_ppimport_p_frame'] = p_frame

        if location != 'sys.path':
            from scipy_test.testing import ScipyTest
            self.__dict__['test'] = ScipyTest(self).test

        # install loader
        sys.modules[name] = self

    def _ppimport_importer(self):
        name = self.__name__

        try:
            module = sys.modules[name]
	except KeyError:
            raise ImportError,self.__dict__.get('_ppimport_exc_info')[1]
        if module is not self:
            exc_info = self.__dict__.get('_ppimport_exc_info')
            if exc_info is not None:
                raise PPImportError,\
                      ''.join(traceback.format_exception(*exc_info))
            else:
                assert module is self,`(module, self)`

        # uninstall loader
        del sys.modules[name]

        if DEBUG:
            print 'Executing postponed import for %s' %(name)
        try:
            module = __import__(name,None,None,['*'])
        except Exception,msg: # ImportError:
            p_frame = self.__dict__.get('_ppimport_p_frame',None)
            if p_frame:
                print 'ppimport(%s) caller locals:' % (repr(name))
                for k in ['__name__','__file__']:
                    v = p_frame.f_locals.get(k,None)
                    if v is not None:
                        print '%s=%s' % (k,v)
            self.__dict__['_ppimport_exc_info'] = sys.exc_info()
            raise

        assert isinstance(module,types.ModuleType),`module`

        self.__dict__ = module.__dict__
        self.__dict__['_ppimport_module'] = module

        # XXX: Should we check the existence of module.test? Warn?
        from scipy_test.testing import ScipyTest
        module.test = ScipyTest(module).test

        return module

    def __setattr__(self, name, value):
        try:
            module = self.__dict__['_ppimport_module']
        except KeyError:
            module = self._ppimport_importer()
        return setattr(module, name, value)

    def __getattr__(self, name):
        try:
            module = self.__dict__['_ppimport_module']
        except KeyError:
            module = self._ppimport_importer()
        return getattr(module, name)

    def __repr__(self):
        global _ppimport_is_enabled
        if not _ppimport_is_enabled:
            try:
                module = self.__dict__['_ppimport_module']
            except KeyError:
                module = self._ppimport_importer()
            return module.__repr__()
        if self.__dict__.has_key('_ppimport_module'):
            status = 'imported'
        elif self.__dict__.has_key('_ppimport_exc_info'):
            status = 'import error'
        else:
            status = 'import postponed'
        return '<module %s from %s [%s]>' \
               % (`self.__name__`,`self.__file__`, status)

    __str__ = __repr__

def ppresolve(a):
    """ Return resolved object a.

    a can be module name, postponed module, postponed modules
    attribute, string representing module attribute, or any
    Python object.
    """
    if type(a) is type(''):
        ns = a.split('.')
        a = ppimport(ns[0])
        b = [ns[0]]
        del ns[0]
        while ns:
            if hasattr(a,'_ppimport_importer') or \
                   hasattr(a,'_ppimport_module'):
                a = a._ppimport_module
            if hasattr(a,'_ppimport_attr'):
                a = a._ppimport_attr
            b.append(ns[0])
            del ns[0]
            a = getattr(a,b[-1],ppimport('.'.join(b)))

    if hasattr(a,'_ppimport_importer') or \
           hasattr(a,'_ppimport_module'):
        a = a._ppimport_module
    if hasattr(a,'_ppimport_attr'):
        a = a._ppimport_attr
    return a


try:
    import pydoc as _pydoc
except ImportError:
    _pydoc = None

if _pydoc is not None:
    # Redefine __call__ method of help.__class__ to
    # support ppimport.
    import new as _new

    _old_pydoc_help_call = _pydoc.help.__class__.__call__
    def _scipy_pydoc_help_call(self,*args,**kwds):
        return _old_pydoc_help_call(self, *map(ppresolve,args), **kwds)
    _pydoc.help.__class__.__call__ = _new.instancemethod(_scipy_pydoc_help_call,
                                                         None,
                                                         _pydoc.help.__class__)

    _old_pydoc_Doc_document = _pydoc.Doc.document
    def _scipy_pydoc_Doc_document(self,*args,**kwds):
        args = (ppresolve(args[0]),) + args[1:]
        return _old_pydoc_Doc_document(self,*args,**kwds)
    _pydoc.Doc.document = _new.instancemethod(_scipy_pydoc_Doc_document,
                                              None,
                                              _pydoc.Doc)

    _old_pydoc_describe = _pydoc.describe
    def _scipy_pydoc_describe(object):
        return _old_pydoc_describe(ppresolve(object))
    _pydoc.describe = _scipy_pydoc_describe

    import inspect as _inspect
    _old_inspect_getfile = _inspect.getfile
    def _scipy_inspect_getfile(object):
        return _old_inspect_getfile(ppresolve(object))
    _inspect.getfile = _scipy_inspect_getfile

""" Machine limits for Float32 and Float64.
"""

__all__ = ['float_epsilon','float_tiny','float_min',
           'float_max','float_precision','float_resolution',
           'double_epsilon','double_tiny','double_min','double_max',
           'double_precision','double_resolution']

from machar import machar_double, machar_single

float_epsilon = machar_single.epsilon
float_tiny = machar_single.tiny
float_max = machar_single.huge
float_min = -float_max
float_precision = machar_single.precision
float_resolution = machar_single.resolution

double_epsilon = machar_double.epsilon
double_tiny = machar_double.tiny
double_max = machar_double.huge
double_min = -double_max
double_precision = machar_double.precision
double_resolution = machar_double.resolution

if __name__ == '__main__':
    print 'float epsilon:',float_epsilon
    print 'float tiny:',float_tiny
    print 'double epsilon:',double_epsilon
    print 'double tiny:',double_tiny


major = 0
minor = 3
micro = 1
#release_level = 'alpha'
release_level = ''
try:
    from __cvs_version__ import cvs_version
    cvs_minor = cvs_version[-3]
    cvs_serial = cvs_version[-1]
except ImportError,msg:
    print msg
    cvs_minor = 0
    cvs_serial = 0

if release_level:
    scipy_base_version = '%(major)d.%(minor)d.%(micro)d_%(release_level)s'\
                              '_%(cvs_minor)d.%(cvs_serial)d' % (locals ())
else:
    scipy_base_version = '%(major)d.%(minor)d.%(micro)d'\
                              '_%(cvs_minor)d.%(cvs_serial)d' % (locals ())


from info_scipy_base import __doc__
from scipy_base_version import scipy_base_version as __version__

from ppimport import ppimport, ppimport_attr

# The following statement is equivalent to
#
#   from Matrix import Matrix as mat
#
# but avoids expensive LinearAlgebra import when
# Matrix is not used.
mat = ppimport_attr(ppimport('Matrix'), 'Matrix')

# Force Numeric to use scipy_base.fastumath instead of Numeric.umath.
import fastumath  # no need to use scipy_base.fastumath
import sys as _sys
_sys.modules['umath'] = fastumath

import Numeric
from Numeric import *

import limits
from type_check import *
from index_tricks import *
from function_base import *
from shape_base import *
from matrix_base import *

from polynomial import *
from scimath import *
from machar import *
from pexec import *

Inf = inf = fastumath.PINF
try:
    NAN = NaN = nan = fastumath.NAN
except AttributeError:
    NaN = NAN = nan = fastumath.PINF/fastumath.PINF

from scipy_test.testing import ScipyTest
test = ScipyTest('scipy_base').test

#
# Title: Provides ParallelExec to execute commands in
#        other (background or parallel) threads.
# Author: Pearu Peteson <pearu@cens.ioc.ee>
# Created: October, 2003
#

__all__ = ['ParallelExec']

import sys
import threading
import Queue
import traceback
import types
import inspect
import time
import atexit

class ParallelExec(threading.Thread):
    """ Create a thread of parallel execution.
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.__queue = Queue.Queue(0)
        self.__frame = sys._getframe(1)
        self.setDaemon(1)
        self.start()

    def __call__(self,code,frame=None,wait=0):
        """ Execute code in parallel thread inside given frame (default
        frame is where this instance was created).
        If wait is True then __call__ returns after code is executed,
        otherwise code execution happens in background.
        """
        if wait:
            wait_for_code = threading.Event()
        else:
            wait_for_code = None
        self.__queue.put((code,frame,wait_for_code))
        if wait:
            wait_for_code.wait()

    def shutdown(self):
        """ Shutdown parallel thread."""
        self.__queue.put((None,None,None))

    def run(self):
        """ Called by threading.Thread."""
        while 1:
            code, frame, wait_for_code = self.__queue.get()
            if code is None:
                break
            if frame is None:
                frame = self.__frame
            try:
                exec (code, frame.f_globals,frame.f_locals)
            except Exception:
                traceback.print_exc()
            if wait_for_code is not None:
                wait_for_code.set()

import types
import Numeric
__all__ = ['mgrid','ogrid','r_','c_','index_exp']

from type_check import ScalarType, asarray
import function_base
import matrix_base

class nd_grid:
    """ Construct a "meshgrid" in N-dimensions.

        grid = nd_grid() creates an instance which will return a mesh-grid
        when indexed.  The dimension and number of the output arrays are equal
        to the number of indexing dimensions.  If the step length is not a
        complex number, then the stop is not inclusive.
    
        However, if the step length is a COMPLEX NUMBER (e.g. 5j), then the
        integer part of it's magnitude is interpreted as specifying the
        number of points to create between the start and stop values, where
        the stop value IS INCLUSIVE.

        If instantiated with an argument of 1, the mesh-grid is open or not
        fleshed out so that only one-dimension of each returned argument is
        greater than 1
    
        Example:
    
           >>> mgrid = nd_grid()
           >>> mgrid[0:5,0:5]
           array([[[0, 0, 0, 0, 0],
                   [1, 1, 1, 1, 1],
                   [2, 2, 2, 2, 2],
                   [3, 3, 3, 3, 3],
                   [4, 4, 4, 4, 4]],
                  [[0, 1, 2, 3, 4],
                   [0, 1, 2, 3, 4],
                   [0, 1, 2, 3, 4],
                   [0, 1, 2, 3, 4],
                   [0, 1, 2, 3, 4]]])
           >>> mgrid[-1:1:5j]
           array([-1. , -0.5,  0. ,  0.5,  1. ])

           >>> ogrid = nd_grid(1)
           >>> ogrid[0:5,0:5]
           [array([[0],[1],[2],[3],[4]]), array([[0, 1, 2, 3, 4]])] 
    """
    def __init__(self, sparse=0):
        self.sparse = sparse
    def __getitem__(self,key):
        try:
	    size = []
            typecode = Numeric.Int
	    for k in range(len(key)):
	        step = key[k].step
                start = key[k].start
                if start is None: start = 0
                if step is None:
                    step = 1
                if type(step) is type(1j):
                    size.append(int(abs(step)))
                    typecode = Numeric.Float
                else:
                    size.append(int((key[k].stop - start)/(step*1.0)))
                if isinstance(step,types.FloatType) or \
                   isinstance(start, types.FloatType) or \
                   isinstance(key[k].stop, types.FloatType):
                       typecode = Numeric.Float
            if self.sparse:
                nn = map(lambda x,t: Numeric.arange(x,typecode=t),size,(typecode,)*len(size))
            else:
                nn = Numeric.indices(size,typecode)
	    for k in range(len(size)):
                step = key[k].step
                if step is None:
                    step = 1
                if type(step) is type(1j):
                    step = int(abs(step))
                    step = (key[k].stop - key[k].start)/float(step-1)
                nn[k] = (nn[k]*step+key[k].start)
            if self.sparse:
                slobj = [Numeric.NewAxis]*len(size)
                for k in range(len(size)):
                    slobj[k] = slice(None,None)
                    nn[k] = nn[k][slobj]
                    slobj[k] = Numeric.NewAxis
	    return nn
        except (IndexError, TypeError):
            step = key.step
            stop = key.stop
            start = key.start
            if start is None: start = 0
            if type(step) is type(1j):
                step = abs(step)
                length = int(step)
                step = (key.stop-start)/float(step-1)
                stop = key.stop+step
                return Numeric.arange(0,length,1,Numeric.Float)*step + start
            else:
                return Numeric.arange(start, stop, step)
	    
    def __getslice__(self,i,j):
        return Numeric.arange(i,j)

    def __len__(self):
        return 0

mgrid = nd_grid()
ogrid = nd_grid(1)

import sys
class concatenator:
    """ Translates slice objects to concatenation along an axis.
    """
    def __init__(self, axis=0):
        self.axis = axis
    def __getitem__(self,key):
        if isinstance(key,types.StringType):
            frame = sys._getframe().f_back
            return array(matrix_base.bmat(key,frame.f_globals,frame.f_locals))
        if type(key) is not types.TupleType:
            key = (key,)
        objs = []
        for k in range(len(key)):
            if type(key[k]) is types.SliceType:
                typecode = Numeric.Int
	        step = key[k].step
                start = key[k].start
                stop = key[k].stop
                if start is None: start = 0
                if step is None:
                    step = 1
                if type(step) is type(1j):
                    size = int(abs(step))
                    typecode = Numeric.Float
                    endpoint = 1
                else:
                    size = int((stop - start)/(step*1.0))
                    endpoint = 0
                if isinstance(step,types.FloatType) or \
                   isinstance(start, types.FloatType) or \
                   isinstance(stop, types.FloatType):
                       typecode = Numeric.Float
                newobj = function_base.linspace(start, stop, num=size,
                                                endpoint=endpoint)
            elif type(key[k]) in ScalarType:
                newobj = asarray([key[k]])
            else:
                newobj = key[k]
            objs.append(newobj)
        return Numeric.concatenate(tuple(objs),axis=self.axis)
        
    def __getslice__(self,i,j):
        return Numeric.arange(i,j)

    def __len__(self):
        return 0

r_=concatenator(0)
c_=concatenator(-1)

# A nicer way to build up index tuples for arrays.
#
# You can do all this with slice() plus a few special objects,
# but there's a lot to remember. This version is simpler because
# it uses the standard array indexing syntax.
#
# Written by Konrad Hinsen <hinsen@cnrs-orleans.fr>
# last revision: 1999-7-23
#
# Cosmetic changes by T. Oliphant 2001
#
#
# This module provides a convenient method for constructing
# array indices algorithmically. It provides one importable object,
# 'index_expression'.
#
# For any index combination, including slicing and axis insertion,
# 'a[indices]' is the same as 'a[index_expression[indices]]' for any
# array 'a'. However, 'index_expression[indices]' can be used anywhere
# in Python code and returns a tuple of slice objects that can be
# used in the construction of complex index expressions.

class _index_expression_class:
    import sys
    maxint = sys.maxint

    def __getitem__(self, item):
        if type(item) != type(()):
            return (item,)
        else:
            return item

    def __len__(self):
        return self.maxint

    def __getslice__(self, start, stop):
        if stop == self.maxint:
            stop = None
        return self[start:stop:None]

index_exp = _index_expression_class()

# End contribution from Konrad.


import Numeric
from Numeric import *
from type_check import isscalar, asarray

__all__ = ['atleast_1d','atleast_2d','atleast_3d','vstack','hstack',
           'column_stack','dstack','array_split','split','hsplit',
           'vsplit','dsplit','squeeze','apply_over_axes','expand_dims',
           'apply_along_axis']

def apply_along_axis(func1d,axis,arr,*args):
    """ Execute func1d(arr[i],*args) where func1d takes 1-D arrays
        and arr is an N-d array.  i varies so as to apply the function
        along the given axis for each 1-d subarray in arr.
    """
    nd = Numeric.rank(arr)
    if axis < 0: axis += nd
    if (axis >= nd):
        raise ValueError, "axis must be less than the rank; "+\
              "axis=%d, rank=%d." % (axis,)
    ind = [0]*(nd-1)
    dims = Numeric.shape(arr)
    i = zeros(nd,'O')
    indlist = range(nd)
    indlist.remove(axis)
    i[axis] = slice(None,None)
    outshape = take(shape(arr),indlist)
    put(i,indlist,ind)
    res = func1d(arr[i],*args)
    #  if res is a number, then we have a smaller output array
    if isscalar(res):
        outarr = zeros(outshape,asarray(res).typecode())
        outarr[ind] = res
        Ntot = product(outshape)
        k = 1
        while k < Ntot:
            # increment the index
            ind[-1] += 1
            n = -1
            while (ind[n] >= outshape[n]) and (n > (1-nd)):
                ind[n-1] += 1
                ind[n] = 0
                n -= 1
            put(i,indlist,ind)
            res = func1d(arr[i],*args)
            outarr[ind] = res
            k += 1
        return outarr
    else:
        Ntot = product(outshape)
        holdshape = outshape
        outshape = list(shape(arr))
        outshape[axis] = len(res)
        outarr = zeros(outshape,asarray(res).typecode())
        outarr[i] = res
        k = 1
        while k < Ntot:
            # increment the index
            ind[-1] += 1
            n = -1
            while (ind[n] >= holdshape[n]) and (n > (1-nd)):
                ind[n-1] += 1
                ind[n] = 0
                n -= 1
            put(i,indlist,ind)
            res = func1d(arr[i],*args)
            outarr[i] = res
            k += 1
        return outarr
        
     
def apply_over_axes(func, a, axes):
    """Apply a function over multiple axes, keeping the same shape
    for the resulting array.
    """
    val = asarray(a)
    N = len(val.shape)
    if not type(axes) in SequenceType:
        axes = (axes,)
    for axis in axes:
        if axis < 0: axis = N + axis
        args = (val, axis)
        val = expand_dims(func(*args),axis)
    return val

def expand_dims(a, axis):
    """Expand the shape of a by including NewAxis before given axis.
    """
    a = asarray(a)
    shape = a.shape
    if axis < 0:
        axis = axis + len(shape) + 1
    a.shape = shape[:axis] + (1,) + shape[axis:]
    return a

def squeeze(a):
    "Returns a with any ones from the shape of a removed"
    a = asarray(a)
    b = asarray(a.shape)
    val = reshape (a, tuple (compress (not_equal (b, 1), b)))
    return val

def atleast_1d(*arys):
    """ Force a sequence of arrays to each be at least 1D.

         Description:
            Force an array to be at least 1D.  If an array is 0D, the 
            array is converted to a single row of values.  Otherwise,
            the array is unaltered.
         Arguments:
            *arys -- arrays to be converted to 1 or more dimensional array.
         Returns:
            input array converted to at least 1D array.
    """
    res = []
    for ary in arys:
        ary = asarray(ary)
        if len(ary.shape) == 0: 
            result = Numeric.array([ary[0]])
        else:
            result = ary
        res.append(result)
    if len(res) == 1:
        return res[0]
    else:
        return res

def atleast_2d(*arys):
    """ Force a sequence of arrays to each be at least 2D.

         Description:
            Force an array to each be at least 2D.  If the array
            is 0D or 1D, the array is converted to a single
            row of values.  Otherwise, the array is unaltered.
         Arguments:
            arys -- arrays to be converted to 2 or more dimensional array.
         Returns:
            input array converted to at least 2D array.
    """
    res = []
    for ary in arys:
        ary = asarray(ary)
        if len(ary.shape) == 0: 
            ary = Numeric.array([ary[0]])
        if len(ary.shape) == 1: 
            result = ary[NewAxis,:]
        else: 
            result = ary
        res.append(result)
    if len(res) == 1:
        return res[0]
    else:
        return res
        
def atleast_3d(*arys):
    """ Force a sequence of arrays to each be at least 3D.

         Description:
            Force an array each be at least 3D.  If the array is 0D or 1D, 
            the array is converted to a single 1xNx1 array of values where 
            N is the orginal length of the array. If the array is 2D, the 
            array is converted to a single MxNx1 array of values where MxN
            is the orginal shape of the array. Otherwise, the array is 
            unaltered.
         Arguments:
            arys -- arrays to be converted to 3 or more dimensional array.
         Returns:
            input array converted to at least 3D array.
    """
    res = []
    for ary in arys:
        ary = asarray(ary)
        if len(ary.shape) == 0:
            ary = Numeric.array([ary[0]])
        if len(ary.shape) == 1:
            result = ary[NewAxis,:,NewAxis]
        elif len(ary.shape) == 2:
            result = ary[:,:,NewAxis]
        else: 
            result = ary
        res.append(result)
    if len(res) == 1:
        return res[0]
    else:
        return res


def vstack(tup):
    """ Stack arrays in sequence vertically (row wise)

        Description:
            Take a sequence of arrays and stack them veritcally
            to make a single array.  All arrays in the sequence
            must have the same shape along all but the first axis. 
            vstack will rebuild arrays divided by vsplit.
        Arguments:
            tup -- sequence of arrays.  All arrays must have the same 
                   shape.
        Examples:
            >>> import scipy
            >>> a = array((1,2,3))
            >>> b = array((2,3,4))
            >>> scipy.vstack((a,b))
            array([[1, 2, 3],
                   [2, 3, 4]])
            >>> a = array([[1],[2],[3]])
            >>> b = array([[2],[3],[4]])
            >>> scipy.vstack((a,b))
            array([[1],
                   [2],
                   [3],
                   [2],
                   [3],
                   [4]])

    """
    return Numeric.concatenate(map(atleast_2d,tup),0)

def hstack(tup):
    """ Stack arrays in sequence horizontally (column wise)

        Description:
            Take a sequence of arrays and stack them horizontally
            to make a single array.  All arrays in the sequence
            must have the same shape along all but the second axis.
            hstack will rebuild arrays divided by hsplit.
        Arguments:
            tup -- sequence of arrays.  All arrays must have the same 
                   shape.
        Examples:
            >>> import scipy
            >>> a = array((1,2,3))
            >>> b = array((2,3,4))
            >>> scipy.hstack((a,b))
            array([1, 2, 3, 2, 3, 4])
            >>> a = array([[1],[2],[3]])
            >>> b = array([[2],[3],[4]])
            >>> scipy.hstack((a,b))
            array([[1, 2],
                   [2, 3],
                   [3, 4]])

    """
    return Numeric.concatenate(map(atleast_1d,tup),1)

def column_stack(tup):
    """ Stack 1D arrays as columns into a 2D array

        Description:
            Take a sequence of 1D arrays and stack them as columns
            to make a single 2D array.  All arrays in the sequence
            must have the same length.
        Arguments:
            tup -- sequence of 1D arrays.  All arrays must have the same 
                   length.
        Examples:
            >>> import scipy
            >>> a = array((1,2,3))
            >>> b = array((2,3,4))
            >>> scipy.vstack((a,b))
            array([[1, 2],
                   [2, 3],
                   [3, 4]])

    """
    arrays = map(Numeric.transpose,map(atleast_2d,tup))
    return Numeric.concatenate(arrays,1)
    
def dstack(tup):
    """ Stack arrays in sequence depth wise (along third dimension)

        Description:
            Take a sequence of arrays and stack them along the third axis.
            All arrays in the sequence must have the same shape along all 
            but the third axis.  This is a simple way to stack 2D arrays 
            (images) into a single 3D array for processing.
            dstack will rebuild arrays divided by dsplit.
        Arguments:
            tup -- sequence of arrays.  All arrays must have the same 
                   shape.
        Examples:
            >>> import scipy
            >>> a = array((1,2,3))
            >>> b = array((2,3,4))
            >>> scipy.dstack((a,b))
            array([       [[1, 2],
                    [2, 3],
                    [3, 4]]])
            >>> a = array([[1],[2],[3]])
            >>> b = array([[2],[3],[4]])
            >>> scipy.dstack((a,b))
            array([[        [1, 2]],
                   [        [2, 3]],
                   [        [3, 4]]])
    """
    return Numeric.concatenate(map(atleast_3d,tup),2)

def _replace_zero_by_x_arrays(sub_arys):
    for i in range(len(sub_arys)):
        if len(Numeric.shape(sub_arys[i])) == 0:
            sub_arys[i] = Numeric.array([])
        elif Numeric.sometrue(Numeric.equal(Numeric.shape(sub_arys[i]),0)):
            sub_arys[i] = Numeric.array([])   
    return sub_arys
    
def array_split(ary,indices_or_sections,axis = 0):
    """ Divide an array into a list of sub-arrays.

        Description:
           Divide ary into a list of sub-arrays along the
           specified axis.  If indices_or_sections is an integer,
           ary is divided into that many equally sized arrays.
           If it is impossible to make an equal split, each of the
           leading arrays in the list have one additional member.  If
           indices_or_sections is a list of sorted integers, its
           entries define the indexes where ary is split.

        Arguments:
           ary -- N-D array.
              Array to be divided into sub-arrays.
           indices_or_sections -- integer or 1D array.
              If integer, defines the number of (close to) equal sized
              sub-arrays.  If it is a 1D array of sorted indices, it
              defines the indexes at which ary is divided.  Any empty
              list results in a single sub-array equal to the original
              array.
           axis -- integer. default=0.
              Specifies the axis along which to split ary.
        Caveats:
           Currently, the default for axis is 0.  This
           means a 2D array is divided into multiple groups
           of rows.  This seems like the appropriate default, but
           we've agreed most other functions should default to
           axis=-1.  Perhaps we should use axis=-1 for consistency.
           However, we could also make the argument that SciPy
           works on "rows" by default.  sum() sums up rows of
           values.  split() will split data into rows.  Opinions?
    """
    try:
        Ntotal = ary.shape[axis]
    except AttributeError:
        Ntotal = len(ary)
    try: # handle scalar case.
        Nsections = len(indices_or_sections) + 1
        div_points = [0] + list(indices_or_sections) + [Ntotal]
    except TypeError: #indices_or_sections is a scalar, not an array.
        Nsections = int(indices_or_sections)
        if Nsections <= 0:
            raise ValueError, 'number sections must be larger than 0.'
        Neach_section,extras = divmod(Ntotal,Nsections)
        section_sizes = [0] + \
                        extras * [Neach_section+1] + \
                        (Nsections-extras) * [Neach_section]
        div_points = Numeric.add.accumulate(Numeric.array(section_sizes))

    sub_arys = []
    sary = Numeric.swapaxes(ary,axis,0)
    for i in range(Nsections):
        st = div_points[i]; end = div_points[i+1]
        sub_arys.append(Numeric.swapaxes(sary[st:end],axis,0))

    # there is a wierd issue with array slicing that allows
    # 0x10 arrays and other such things.  The following cluge is needed
    # to get around this issue.
    sub_arys = _replace_zero_by_x_arrays(sub_arys)
    # end cluge.

    return sub_arys

def split(ary,indices_or_sections,axis=0):
    """ Divide an array into a list of sub-arrays.

        Description:
           Divide ary into a list of sub-arrays along the
           specified axis.  If indices_or_sections is an integer,
           ary is divided into that many equally sized arrays.
           If it is impossible to make an equal split, an error is 
           raised.  This is the only way this function differs from
           the array_split() function. If indices_or_sections is a 
           list of sorted integers, its entries define the indexes
           where ary is split.

        Arguments:
           ary -- N-D array.
              Array to be divided into sub-arrays.
           indices_or_sections -- integer or 1D array.
              If integer, defines the number of (close to) equal sized
              sub-arrays.  If it is a 1D array of sorted indices, it
              defines the indexes at which ary is divided.  Any empty
              list results in a single sub-array equal to the original
              array.
           axis -- integer. default=0.
              Specifies the axis along which to split ary.
        Caveats:
           Currently, the default for axis is 0.  This
           means a 2D array is divided into multiple groups
           of rows.  This seems like the appropriate default, but
           we've agreed most other functions should default to
           axis=-1.  Perhaps we should use axis=-1 for consistency.
           However, we could also make the argument that SciPy
           works on "rows" by default.  sum() sums up rows of
           values.  split() will split data into rows.  Opinions?
    """
    try: len(indices_or_sections)
    except TypeError:
        sections = indices_or_sections
        N = ary.shape[axis]
        if N % sections:
            raise ValueError, 'array split does not result in an equal division'
    res = array_split(ary,indices_or_sections,axis)
    return res

def hsplit(ary,indices_or_sections):
    """ Split ary into multiple columns of sub-arrays

        Description:
            Split a single array into multiple sub arrays.  The array is
            divided into groups of columns.  If indices_or_sections is
            an integer, ary is divided into that many equally sized sub arrays.
            If it is impossible to make the sub-arrays equally sized, the
            operation throws a ValueError exception. See array_split and
            split for other options on indices_or_sections.                        
        Arguments:
           ary -- N-D array.
              Array to be divided into sub-arrays.
           indices_or_sections -- integer or 1D array.
              If integer, defines the number of (close to) equal sized
              sub-arrays.  If it is a 1D array of sorted indices, it
              defines the indexes at which ary is divided.  Any empty
              list results in a single sub-array equal to the original
              array.
        Returns:
            sequence of sub-arrays.  The returned arrays have the same 
            number of dimensions as the input array.
        Related:
            hstack, split, array_split, vsplit, dsplit.           
        Examples:
            >>> import scipy
            >>> a= array((1,2,3,4))
            >>> scipy.hsplit(a,2)
            [array([1, 2]), array([3, 4])]
            >>> a = array([[1,2,3,4],[1,2,3,4]])
            [array([[1, 2],
                   [1, 2]]), array([[3, 4],
                   [3, 4]])]
                   
    """
    if len(Numeric.shape(ary)) == 0:
        raise ValueError, 'hsplit only works on arrays of 1 or more dimensions'
    if len(ary.shape) > 1:
        return split(ary,indices_or_sections,1)
    else:
        return split(ary,indices_or_sections,0)
        
def vsplit(ary,indices_or_sections):
    """ Split ary into multiple rows of sub-arrays

        Description:
            Split a single array into multiple sub arrays.  The array is
            divided into groups of rows.  If indices_or_sections is
            an integer, ary is divided into that many equally sized sub arrays.
            If it is impossible to make the sub-arrays equally sized, the
            operation throws a ValueError exception. See array_split and
            split for other options on indices_or_sections.
        Arguments:
           ary -- N-D array.
              Array to be divided into sub-arrays.
           indices_or_sections -- integer or 1D array.
              If integer, defines the number of (close to) equal sized
              sub-arrays.  If it is a 1D array of sorted indices, it
              defines the indexes at which ary is divided.  Any empty
              list results in a single sub-array equal to the original
              array.
        Returns:
            sequence of sub-arrays.  The returned arrays have the same 
            number of dimensions as the input array.      
        Caveats:
           How should we handle 1D arrays here?  I am currently raising
           an error when I encounter them.  Any better approach?      
           
           Should we reduce the returned array to their minium dimensions
           by getting rid of any dimensions that are 1?
        Related:
            vstack, split, array_split, hsplit, dsplit.
        Examples:
            import scipy
            >>> a = array([[1,2,3,4],
            ...            [1,2,3,4]])
            >>> scipy.vsplit(a)
            [array([       [1, 2, 3, 4]]), array([       [1, 2, 3, 4]])]
                   
    """
    if len(Numeric.shape(ary)) < 2:
        raise ValueError, 'vsplit only works on arrays of 2 or more dimensions'
    return split(ary,indices_or_sections,0)

def dsplit(ary,indices_or_sections):
    """ Split ary into multiple sub-arrays along the 3rd axis (depth)

        Description:
            Split a single array into multiple sub arrays.  The array is
            divided into groups along the 3rd axis.  If indices_or_sections is
            an integer, ary is divided into that many equally sized sub arrays.
            If it is impossible to make the sub-arrays equally sized, the
            operation throws a ValueError exception. See array_split and
            split for other options on indices_or_sections.                        
        Arguments:
           ary -- N-D array.
              Array to be divided into sub-arrays.
           indices_or_sections -- integer or 1D array.
              If integer, defines the number of (close to) equal sized
              sub-arrays.  If it is a 1D array of sorted indices, it
              defines the indexes at which ary is divided.  Any empty
              list results in a single sub-array equal to the original
              array.
        Returns:
            sequence of sub-arrays.  The returned arrays have the same 
            number of dimensions as the input array.
        Caveats:
           See vsplit caveats.       
        Related:
            dstack, split, array_split, hsplit, vsplit.
        Examples:
            >>> a = array([[[1,2,3,4],[1,2,3,4]]])
            [array([       [[1, 2],
                    [1, 2]]]), array([       [[3, 4],
                    [3, 4]]])]
                                       
    """
    if len(Numeric.shape(ary)) < 3:
        raise ValueError, 'vsplit only works on arrays of 3 or more dimensions'
    return split(ary,indices_or_sections,2)


#
# Machine arithmetics - determine the parameters of the
# floating-point arithmetic system
#
# Author: Pearu Peterson, September 2003
#

__all__ = ['MachAr','machar_double','machar_single']

from Numeric import array

class MachAr:
    """Diagnosing machine parameters.

    The following attributes are available:

    ibeta  - radix in which numbers are represented
    it     - number of base-ibeta digits in the floating point mantissa M
    machep - exponent of the smallest (most negative) power of ibeta that,
             added to 1.0,
             gives something different from 1.0
    eps    - floating-point number beta**machep (floating point precision)
    negep  - exponent of the smallest power of ibeta that, substracted
             from 1.0, gives something different from 1.0
    epsneg - floating-point number beta**negep
    iexp   - number of bits in the exponent (including its sign and bias)
    minexp - smallest (most negative) power of ibeta consistent with there
             being no leading zeros in the mantissa
    xmin   - floating point number beta**minexp (the smallest (in
             magnitude) usable floating value)
    maxexp - smallest (positive) power of ibeta that causes overflow
    xmax   - (1-epsneg)* beta**maxexp (the largest (in magnitude)
             usable floating value)
    irnd   - in range(6), information on what kind of rounding is done
             in addition, and on how underflow is handled
    ngrd   - number of 'guard digits' used when truncating the product
             of two mantissas to fit the representation

    epsilon - same as eps
    tiny    - same as xmin
    huge    - same as xmax
    precision   - int(-log10(eps))
    resolution  - 10**(-precision)

    Reference:
      Numerical Recipies.
    """
    def __init__(self,
                 float_conv=float,
                 int_conv=int,
                 float_to_float=float,
                 float_to_str = lambda v:'%24.16e' % v,
                 title = 'Python floating point number',
                 ):
        """
          float_conv - convert integer to float (array)
          int_conv   - convert float (array) to integer
          float_to_float - convert float array to float
          float_to_str - convert array float to str
          title        - description of used floating point numbers
        """
        one = float_conv(1)
        two = one + one
        zero = one - one

        # Determine ibeta and beta
        a = one
        while 1:
            a = a + a
            temp = a + one
            temp1 = temp - a
            if temp1 - one != zero:
                break
        b = one
        while 1:
            b = b + b
            temp = a + b
            itemp = int_conv(temp-a)
            if itemp != 0:
                break
        ibeta = itemp
        beta = float_conv(ibeta)

        # Determine it and irnd
        it = 0
        b = one
        while 1:
            it = it + 1
            b = b * beta
            temp = b + one
            temp1 = temp - b
            if temp1 - one != zero:
                break

        betah = beta / two
        a = one
        while 1:
            a = a + a
            temp = a + one
            temp1 = temp - a
            if temp1 - one != zero:
                break
        temp = a + betah
        irnd = 0
        if temp-a != zero:
            irnd = 1
        tempa = a + beta
        temp = tempa + betah
        if irnd==0 and temp-tempa != zero:
            irnd = 2

        # Determine negep and epsneg
        negep = it + 3
        betain = one / beta
        a = one
        for i in range(negep):
            a = a * betain
        b = a
        while 1:
            temp = one - a
            if temp-one != zero:
                break
            a = a * beta
            negep = negep - 1
        negep = -negep
        epsneg = a

        # Determine machep and eps
        machep = - it - 3
        a = b

        while 1:
            temp = one + a
            if temp-one != zero:
                break
            a = a * beta
            machep = machep + 1
        eps = a

        # Determine ngrd
        ngrd = 0
        temp = one + eps
        if irnd==0 and temp*one - one != zero:
            ngrd = 1

        # Determine iexp
        i = 0
        k = 1
        z = betain
        t = one + eps
        nxres = 0
        while 1:
            y = z
            z = y*y
            a = z*one # Check here for underflow
            temp = z*t
            if a+a == zero or abs(z)>=y:
                break
            temp1 = temp * betain
            if temp1*beta == z:
                break
            i = i + 1
            k = k + k
        if ibeta != 10:
            iexp = i + 1
            mx = k + k
        else:
            iexp = 2
            iz = ibeta
            while k >= iz:
                iz = iz * ibeta
                iexp = iexp + 1
            mx = iz + iz - 1

        # Determine minexp and xmin
        while 1:
            xmin = y
            y = y * betain
            a = y * one
            temp = y * t
            if a+a != zero and abs(y) < xmin:
                k = k + 1
                temp1 = temp * betain
                if temp1*beta == y and temp != y:
                    nxres = 3
                    xmin = y
                    break
            else:
                break
        minexp = -k

        # Determine maxexp, xmax
        if mx <= k + k - 3 and ibeta != 10:
            mx = mx + mx
            iexp = iexp + 1
        maxexp = mx + minexp
        irnd = irnd + nxres
        if irnd >= 2:
            maxexp = maxexp - 2
        i = maxexp + minexp
        if ibeta == 2 and not i:
            maxexp = maxexp - 1
        if i > 20:
            maxexp = maxexp - 1
        if a != y:
            maxexp = maxexp - 2
        xmax = one - epsneg
        if xmax*one != xmax:
            xmax = one - beta*epsneg
        xmax = xmax / (xmin*beta*beta*beta)
        i = maxexp + minexp + 3
        for j in range(i):
            if ibeta==2:
                xmax = xmax + xmax
            else:
                xmax = xmax * beta

        self.ibeta = ibeta
        self.it = it
        self.negep = negep
        self.epsneg = float_to_float(epsneg)
        self._str_epsneg = float_to_str(epsneg)
        self.machep = machep
        self.eps = float_to_float(eps)
        self._str_eps = float_to_str(eps)
        self.ngrd = ngrd
        self.iexp = iexp
        self.minexp = minexp
        self.xmin = float_to_float(xmin)
        self._str_xmin = float_to_str(xmin)
        self.maxexp = maxexp
        self.xmax = float_to_float(xmax)
        self._str_xmax = float_to_str(xmax)
        self.irnd = irnd

        self.title = title
        # Commonly used parameters
        self.epsilon = self.eps
        self.tiny = self.xmin
        self.huge = self.xmax

        import math
        self.precision = int(-math.log10(float_to_float(self.eps)))
        ten = two + two + two + two + two
        resolution = ten ** (-self.precision)
        self.resolution = float_to_float(resolution)

    def __str__(self):
        return '''\
Machine parameters for %(title)s
---------------------------------------------------------------------
ibeta=%(ibeta)s it=%(it)s iexp=%(iexp)s ngrd=%(ngrd)s irnd=%(irnd)s
machep=%(machep)s     eps=%(_str_eps)s (beta**machep == epsilon)
negep =%(negep)s  epsneg=%(_str_epsneg)s (beta**epsneg)
minexp=%(minexp)s   xmin=%(_str_xmin)s (beta**minexp == tiny)
maxexp=%(maxexp)s    xmax=%(_str_xmax)s ((1-epsneg)*beta**maxexp == huge)
---------------------------------------------------------------------
''' % self.__dict__

machar_double = MachAr(lambda v:array([v],'d'),
                       lambda v:v.astype('i')[0],
                       lambda v:array(v[0],'d'),
                       lambda v:'%24.16e' % array(v[0],'d'),
                       'Numeric double precision floating point number')

machar_single = MachAr(lambda v:array([v],'f'),
                       lambda v:v.astype('i')[0],
                       lambda v:array(v[0],'f'),  #
                       lambda v:'%15.7e' % array(v[0],'f'),
                       'Numeric single precision floating point number')

if __name__ == '__main__':
    print MachAr()
    print machar_double
    print machar_single

#!/usr/bin/env python

import os, sys
from glob import glob
import shutil

def configuration(parent_package='',parent_path=None):
    from scipy_distutils.system_info import get_info, NumericNotFoundError
    from scipy_distutils.core import Extension
    from scipy_distutils.misc_util import get_path,default_config_dict,dot_join
    from scipy_distutils.misc_util import get_path,default_config_dict,\
         dot_join,SourceGenerator

    package = 'scipy_base'
    local_path = get_path(__name__,parent_path)
    config = default_config_dict(package,parent_package)

    numpy_info = get_info('numpy')
    if not numpy_info:
        raise NumericNotFoundError, NumericNotFoundError.__doc__

    # extra_compile_args -- trying to find something that is binary compatible
    #                       with msvc for returning Py_complex from functions
    extra_compile_args=[]
    
    # fastumath module
    # scipy_base.fastumath module
    umath_c_sources = ['fastumathmodule.c',
                       'fastumath_unsigned.inc','fastumath_nounsigned.inc']
    umath_c_sources = [os.path.join(local_path,x) for x in umath_c_sources]
    umath_c = SourceGenerator(func = None,
                              target = os.path.join(local_path,'fastumathmodule.c'),
                              sources = umath_c_sources)
    sources = [umath_c, os.path.join(local_path,'isnan.c')]
    define_macros = []
    if sys.byteorder == "little":
        define_macros.append(('USE_MCONF_LITE_LE',None))
    else:
        define_macros.append(('USE_MCONF_LITE_BE',None))
    ext = Extension(dot_join(package,'fastumath'),sources,
                    define_macros = define_macros,
                    extra_compile_args=extra_compile_args,
                    depends = umath_c_sources)
    config['ext_modules'].append(ext)
 
    # _compiled_base module
    sources = ['_compiled_base.c']
    sources = [os.path.join(local_path,x) for x in sources]
    ext = Extension(dot_join(package,'_compiled_base'),sources)
    config['ext_modules'].append(ext)

    # display_test module
    sources = [os.path.join(local_path,'src','display_test.c')]
    x11 = get_info('x11')
    if x11:
        x11['define_macros'] = [('HAVE_X11',None)]
    ext = Extension(dot_join(package,'display_test'), sources, **x11)
    config['ext_modules'].append(ext)

    return config

if __name__ == '__main__':
    from scipy_base_version import scipy_base_version
    print 'scipy_base Version',scipy_base_version
    from scipy_distutils.core import setup

    setup(version = scipy_base_version,
          maintainer = "SciPy Developers",
          maintainer_email = "scipy-dev@scipy.org",
          description = "SciPy base module",
          url = "http://www.scipy.org",
          license = "SciPy License (BSD Style)",
          **configuration()
          )

""" Basic functions for manipulating 2d arrays

"""

__all__ = ['diag','eye','fliplr','flipud','rot90','bmat']

from Numeric import *
from type_check import asarray
import Matrix

def fliplr(m):
    """ returns a 2-D matrix m with the rows preserved and columns flipped 
        in the left/right direction.  Only works with 2-D arrays.
    """
    m = asarray(m)
    if len(m.shape) != 2:
        raise ValueError, "Input must be 2-D."
    return m[:, ::-1]

def flipud(m):
    """ returns a 2-D matrix with the columns preserved and rows flipped in
        the up/down direction.  Only works with 2-D arrays.
    """
    m = asarray(m)
    if len(m.shape) != 2:
        raise ValueError, "Input must be 2-D."
    return m[::-1]
    
# reshape(x, m, n) is not used, instead use reshape(x, (m, n))

def rot90(m, k=1):
    """ returns the matrix found by rotating m by k*90 degrees in the 
        counterclockwise direction.
    """
    m = asarray(m)
    if len(m.shape) != 2:
        raise ValueError, "Input must be 2-D."
    k = k % 4
    if k == 0: return m
    elif k == 1: return transpose(fliplr(m))
    elif k == 2: return fliplr(flipud(m))
    else: return fliplr(transpose(m))  # k==3
    
def eye(N, M=None, k=0, typecode='d'):
    """ eye returns a N-by-M matrix where the  k-th diagonal is all ones, 
        and everything else is zeros.
    """
    if M is None: M = N
    if type(M) == type('d'): 
        typecode = M
        M = N
    m = equal(subtract.outer(arange(N), arange(M)),-k)
    if typecode is None:
        return m
    else:
        return m.astype(typecode)

def diag(v, k=0):
    """ returns the k-th diagonal if v is a matrix or returns a matrix 
        with v as the k-th diagonal if v is a vector.
    """
    v = asarray(v)
    s = v.shape
    if len(s)==1:
        n = s[0]+abs(k)
        if k > 0:
            v = concatenate((zeros(k, v.typecode()),v))
        elif k < 0:
            v = concatenate((v,zeros(-k, v.typecode())))
        return eye(n, k=k)*v
    elif len(s)==2:
        v = add.reduce(eye(s[0], s[1], k=k)*v)
        if k > 0: return v[k:]
        elif k < 0: return v[:k]
        else: return v
    else:
            raise ValueError, "Input must be 1- or 2-D."


def _from_string(str,gdict,ldict):
    rows = str.split(';')
    rowtup = []
    for row in rows:
        trow = row.split(',')
        coltup = []
        for col in trow:
            col = col.strip()
            try:
                thismat = gdict[col]
            except KeyError:
                try:
                    thismat = ldict[col]
                except KeyError:
                    raise KeyError, "%s not found" % (col,)
                                    
            coltup.append(thismat)
        rowtup.append(concatenate(coltup,axis=-1))
    return concatenate(rowtup,axis=0)

import sys
def bmat(obj,gdict=None,ldict=None):
    """Build a matrix object from string, nested sequence, or array.

    Ex:  F = bmat('A, B; C, D')  
         F = bmat([[A,B],[C,D]])
         F = bmat(r_[c_[A,B],c_[C,D]])

        all produce the same Matrix Object    [ A  B ]
                                              [ C  D ]
                                      
        if A, B, C, and D are appropriately shaped 2-d arrays.
    """
    if isinstance(obj, types.StringType):
        if gdict is None:
            # get previous frame
            frame = sys._getframe().f_back
            glob_dict = frame.f_globals
            loc_dict = frame.f_locals
        else:
            glob_dict = gdict
            loc_dict = ldict
        
        return Matrix.Matrix(_from_string(obj, glob_dict, loc_dict))
    
    if isinstance(obj, (types.TupleType, types.ListType)):
        # [[A,B],[C,D]]
        arr_rows = []
        for row in obj:
            if isinstance(row, ArrayType):  # not 2-d
                return Matrix.Matrix(concatenate(obj,axis=-1))
            else:
                arr_rows.append(concatenate(row,axis=-1))
        return Matrix.Matrix(concatenate(arr_rows,axis=0))
    if isinstance(obj, ArrayType):
        return Matrix.Matrix(obj)



import types
import Numeric
from Numeric import ravel, nonzero, array, choose, ones, zeros, \
     sometrue, alltrue, reshape
from type_check import ScalarType, isscalar, asarray
from shape_base import squeeze, atleast_1d
from fastumath import PINF as inf
from fastumath import *
import _compiled_base

__all__ = ['round','any','all','logspace','linspace','fix','mod',
           'select','trim_zeros','amax','amin', 'alen', 'ptp','cumsum','take',
           'copy', 'prod','cumprod','diff','angle','unwrap','sort_complex',
           'disp','unique','extract','insert','nansum','nanmax','nanargmax',
           'nanargmin','nanmin','sum','vectorize','asarray_chkfinite',
           'alter_numeric', 'restore_numeric','isaltered']

alter_numeric = _compiled_base.alter_numeric
restore_numeric = _compiled_base.restore_numeric

def isaltered():
    val = str(type(array([1])))
    return 'scipy' in val

round = Numeric.around

def asarray_chkfinite(x):
    """Like asarray except it checks to be sure no NaNs or Infs are present.
    """
    x = asarray(x)
    if not all(isfinite(x)):
        raise ValueError, "Array must not contain infs or nans."
    return x    

def any(x):
    """Return true if any elements of x are true:  sometrue(ravel(x))
    """
    return sometrue(ravel(x))


def all(x):
    """Return true if all elements of x are true:  alltrue(ravel(x))
    """
    return alltrue(ravel(x))

# Need this to change array type for low precision values
def sum(x,axis=0):  # could change default axis here
    x = asarray(x)
    if x.typecode() in ['1','s','b','w']:
        x = x.astype('l')
    return Numeric.sum(x,axis)
    

def logspace(start,stop,num=50,endpoint=1):
    """ Evenly spaced samples on a logarithmic scale.

        Return num evenly spaced samples from 10**start to 10**stop.  If
        endpoint=1 then last sample is 10**stop.
    """
    if num <= 0: return array([])
    if endpoint:
        step = (stop-start)/float((num-1))
        y = Numeric.arange(0,num) * step + start
    else:
        step = (stop-start)/float(num)
        y = Numeric.arange(0,num) * step + start
    return Numeric.power(10.0,y)

def linspace(start,stop,num=50,endpoint=1,retstep=0):
    """ Evenly spaced samples.
    
        Return num evenly spaced samples from start to stop.  If endpoint=1 then
        last sample is stop. If retstep is 1 then return the step value used.
    """
    if num <= 0: return array([])
    if endpoint:
        step = (stop-start)/float((num-1))
        y = Numeric.arange(0,num) * step + start        
    else:
        step = (stop-start)/float(num)
        y = Numeric.arange(0,num) * step + start
    if retstep:
        return y, step
    else:
        return y

def fix(x):
    """ Round x to nearest integer towards zero.
    """
    x = asarray(x)
    y = Numeric.floor(x)
    return Numeric.where(x<0,y+1,y)

def mod(x,y):
    """ x - y*floor(x/y)
    
        For numeric arrays, x % y has the same sign as x while
        mod(x,y) has the same sign as y.
    """
    return x - y*Numeric.floor(x*1.0/y)

def select(condlist, choicelist, default=0):
    """ Returns an array comprised from different elements of choicelist
        depending on the list of conditions.

        condlist is a list of condition arrays containing ones or zeros
    
        choicelist is a list of choice matrices (of the "same" size as the
        arrays in condlist).  The result array has the "same" size as the
        arrays in choicelist.  If condlist is [c0,...,cN-1] then choicelist
        must be of length N.  The elements of the choicelist can then be
        represented as [v0,...,vN-1]. The default choice if none of the
        conditions are met is given as the default argument. 
    
        The conditions are tested in order and the first one statisfied is
        used to select the choice. In other words, the elements of the
        output array are found from the following tree (notice the order of
        the conditions matters):
    
        if c0: v0
        elif c1: v1
        elif c2: v2
        ...
        elif cN-1: vN-1
        else: default
    
        Note, that one of the condition arrays must be large enough to handle
        the largest array in the choice list.
    """
    n = len(condlist)
    n2 = len(choicelist)
    if n2 != n:
        raise ValueError, "List of cases, must be same length as the list of conditions."
    choicelist.insert(0,default)    
    S = 0
    pfac = 1
    for k in range(1,n+1):
        S += k * pfac * asarray(condlist[k-1])
        if k < n:
            pfac *= (1-asarray(condlist[k-1]))
    # handle special case of a 1-element condition but
    #  a multi-element choice
    if type(S) in ScalarType or max(asarray(S).shape)==1:
        pfac = asarray(1)
        for k in range(n2+1):
            pfac = pfac + asarray(choicelist[k])            
        S = S*ones(asarray(pfac).shape)
    return choose(S, tuple(choicelist))

def _asarray1d(arr):
    """Ensure 1d array for one array.
    """
    m = asarray(arr)
    if len(m.shape)==0:
        m = reshape(m,(1,))
    return m

def copy(a):
    """Return an array copy of the object.
    """
    return array(a,copy=1)

def take(a, indices, axis=0):
    """Selects the elements in indices from array a along given axis.
    """
    try:
        a = Numeric.take(a,indices,axis)
    except ValueError:  # a is scalar
        pass
    return a
    
# Basic operations
def amax(m,axis=-1):
    """Returns the maximum of m along dimension axis. 
    """
    if axis is None:
        m = ravel(m)
        axis = 0
    else:
        m = _asarray1d(m)
    return maximum.reduce(m,axis)

def amin(m,axis=-1):
    """Returns the minimum of m along dimension axis.
    """
    if axis is None:
        m = ravel(m)
        axis = 0
    else:        
        m = _asarray1d(m)
    return minimum.reduce(m,axis)

def alen(m):
    """Returns the length of a Python object interpreted as an array
    """
    return len(asarray(m))

# Actually from Basis, but it fits in so naturally here...

def ptp(m,axis=-1):
    """Returns the maximum - minimum along the the given dimension
    """
    if axis is None:
        m = ravel(m)
        axis = 0
    else:
        m = _asarray1d(m)
    return amax(m,axis)-amin(m,axis)

def cumsum(m,axis=-1):
    """Returns the cumulative sum of the elements along the given axis
    """
    if axis is None:
        m = ravel(m)
        axis = 0
    else:
        m = _asarray1d(m)
    return add.accumulate(m,axis)

def prod(m,axis=-1):
    """Returns the product of the elements along the given axis
    """
    if axis is None:
        m = ravel(m)
        axis = 0
    else:
        m = _asarray1d(m)
    return multiply.reduce(m,axis)

def cumprod(m,axis=-1):
    """Returns the cumulative product of the elments along the given axis
    """
    if axis is None:
        m = ravel(m)
        axis = 0
    else:
        m = _asarray1d(m)
    return multiply.accumulate(m,axis)

def diff(x, n=1,axis=-1):
    """Calculates the nth order, discrete difference along given axis.
    """
    x = _asarray1d(x)
    nd = len(x.shape)
    slice1 = [slice(None)]*nd
    slice2 = [slice(None)]*nd
    slice1[axis] = slice(1,None)
    slice2[axis] = slice(None,-1)
    if n > 1:
        return diff(x[slice1]-x[slice2], n-1, axis=axis)
    else:
        return x[slice1]-x[slice2]

    
def angle(z,deg=0):
    """Return the angle of complex argument z."""
    if deg:
        fact = 180/pi
    else:
        fact = 1.0
    z = asarray(z)
    if z.typecode() in ['D','F']:
       zimag = z.imag
       zreal = z.real
    else:
       zimag = 0
       zreal = z
    return arctan2(zimag,zreal) * fact

def unwrap(p,discont=pi,axis=-1):
    """unwraps radian phase p by changing absolute jumps greater than
       discont to their 2*pi complement along the given axis.
    """
    p = asarray(p)
    nd = len(p.shape)
    dd = diff(p,axis=axis)
    slice1 = [slice(None,None)]*nd     # full slices
    slice1[axis] = slice(1,None)
    ddmod = mod(dd+pi,2*pi)-pi
    Numeric.putmask(ddmod,(ddmod==-pi) & (dd > 0),pi)
    ph_correct = ddmod - dd;
    Numeric.putmask(ph_correct,abs(dd)<discont,0)
    up = array(p,copy=1,typecode='d')
    up[slice1] = p[slice1] + cumsum(ph_correct,axis)
    return up

def sort_complex(a):
    """ Doesn't currently work for integer arrays -- only float or complex.
    """
    a = asarray(a,typecode=a.typecode().upper())
    def complex_cmp(x,y):
        res = cmp(x.real,y.real)
        if res == 0:
            res = cmp(x.imag,y.imag)
        return res
    l = a.tolist()                
    l.sort(complex_cmp)
    return array(l)

def trim_zeros(filt,trim='fb'):
    """ Trim the leading and trailing zeros from a 1D array.
    
        Example:
            >>> import scipy
            >>> a = array((0,0,0,1,2,3,2,1,0))
            >>> scipy.trim_zeros(a)
            array([1, 2, 3, 2, 1])
    """
    first = 0
    if 'f' in trim or 'F' in trim:
        for i in filt:
            if i != 0.: break
            else: first = first + 1
    last = len(filt)
    if 'b' in trim or 'B' in trim:
        for i in filt[::-1]:
            if i != 0.: break
            else: last = last - 1
    return filt[first:last]

def unique(inseq):
    """Returns unique items in 1-dimensional sequence.
    """
    set = {}
    for item in inseq:
        set[item] = None
    return asarray(set.keys())

def where(condition,x=None,y=None):
    """If x and y are both None, then return the (1-d equivalent) indices
    where condition is true.  Otherwise, return an array shaped like
    condition with elements of x and y in the places where condition is
    true or false respectively.
    """
    if (x is None) and (y is None):
             # Needs work for multidimensional arrays
        return nonzero(ravel(condition))
    else:
        return choose(not_equal(condition, 0), (y,x))
    
def extract(condition, arr):
    """Elements of ravel(condition) where ravel(condition) is true (1-d)

    Equivalent of compress(ravel(condition), ravel(arr))
    """
    return Numeric.take(ravel(arr), nonzero(ravel(condition)))

def insert(arr, mask, vals):
    """Similar to putmask arr[mask] = vals but 1d array vals has the
    same number of elements as the non-zero values of mask. Inverse of extract.
    """
    return _compiled_base._insert(arr, mask, vals)

def nansum(x,axis=-1):
    """Sum the array over the given axis treating nans as missing values.
    """
    x = _asarray1d(x).copy()
    Numeric.putmask(x,isnan(x),0)
    return Numeric.sum(x,axis)

def nanmin(x,axis=-1):
    """Find the minimium over the given axis ignoring nans.
    """
    x = _asarray1d(x).copy()
    Numeric.putmask(x,isnan(x),inf)
    return amin(x,axis)

def nanargmin(x,axis=-1):
    """Find the indices of the minimium over the given axis ignoring nans.
    """
    x = _asarray1d(x).copy()
    Numeric.putmask(x,isnan(x),inf)
    return argmin(x,axis)
    

def nanmax(x,axis=-1):
    """Find the maximum over the given axis ignoring nans.
    """
    x = _asarray1d(x).copy()
    Numeric.putmask(x,isnan(x),-inf)
    return amax(x,axis)

def nanargmax(x,axis=-1):
    """Find the maximum over the given axis ignoring nans.
    """
    x = _asarray1d(x).copy()
    Numeric.putmask(x,isnan(x),-inf)
    return argmax(x,axis)

def disp(mesg, device=None, linefeed=1):
    """Display a message to device (default is sys.stdout) with(out) linefeed.
    """
    if device is None:
        import sys
        device = sys.stdout
    if linefeed:
        device.write('%s\n' % mesg)
    else:
        device.write('%s' % mesg)
    device.flush()
    return

from _compiled_base import arraymap
class vectorize:
    """
 vectorize(somefunction)  Generalized Function class.

  Description:
 
    Define a vectorized function which takes nested sequence
    objects or Numeric arrays as inputs and returns a
    Numeric array as output, evaluating the function over successive
    tuples of the input arrays like the python map function except it uses
    the broadcasting rules of Numeric Python.

  Input:

    somefunction -- a Python function or method

  Example:

    def myfunc(a,b):
        if a > b:
            return a-b
        else
            return a+b

    vfunc = vectorize(myfunc)

    >>> vfunc([1,2,3,4],2)
    array([3,4,1,2])

    """
    def __init__(self,pyfunc,otypes=None,doc=None):
        if not callable(pyfunc) or type(pyfunc) is types.ClassType:
            raise TypeError, "Object is not a callable Python object."
        self.thefunc = pyfunc
        if doc is None:
            self.__doc__ = pyfunc.__doc__
        else:
            self.__doc__ = doc
        if otypes is None:
            self.otypes=''
        else:
            if isinstance(otypes,types.StringType):
                self.otypes=otypes
            else:
                raise ValueError, "Output types must be a string."

    def __call__(self,*args):
        try:
            return squeeze(arraymap(self.thefunc,args,self.otypes))
        except IndexError:
            return self.zerocall(*args)

    def zerocall(self,*args):
        # one of the args was a zeros array
        #  return zeros for each output
        #  first --- find number of outputs
        #  get it from self.otypes if possible
        #  otherwise evaluate function at 0.9
        N = len(self.otypes)
        if N==1:
            return zeros((0,),'d')
        elif N !=0:
            return (zeros((0,),'d'),)*N
        newargs = []
        args = atleast_1d(args)
        for arg in args:
            if arg.typecode() != 'O':
                newargs.append(0.9)
            else:
                newargs.append(arg[0])
        newargs = tuple(newargs)
        try:
            res = self.thefunc(*newargs)
        except:
            raise ValueError, "Zerocall is failing.  "\
                  "Try using otypes in vectorize."
        if isscalar(res):
            return zeros((0,),'d')
        else:
            return (zeros((0,),'d'),)*len(res)


""" Basic functions used by several sub-packages and useful to have in the
main name-space

Type handling
==============
iscomplexobj     --  Test for complex object, scalar result
isrealobj        --  Test for real object, scalar result
iscomplex        --  Test for complex elements, array result
isreal           --  Test for real elements, array result
imag             --  Imaginary part
real             --  Real part
real_if_close    --  Turns complex number with tiny imaginary part to real
isneginf         --  Tests for negative infinity ---|
isposinf         --  Tests for positive infinity    |
isnan            --  Tests for nans                 |----  array results
isinf            --  Tests for infinity             |
isfinite         --  Tests for finite numbers    ---| 
isscalar         --  True if argument is a scalar
nan_to_num       --  Replaces NaN's with 0 and infinities with large numbers
typename         --  Return english name for given typecode character
cast             --  Dictionary of functions to force cast to each type
common_type      --  Determine the 'minimum common type code' for a group
                       of arrays

Index tricks
==================
mgrid            --  Method which allows easy construction of N-d 'mesh-grids'
r_               --  Append and construct arrays -- turns slice objects into
                       ranges and concatenates them, for 2d arrays appends
                       rows.
c_               --  Append and construct arrays -- for 2d arrays appends
                       columns.

index_exp        --  Konrad Hinsen's index_expression class instance which
                     can be useful for building complicated slicing syntax.

Useful functions
==================
select           --  Extension of where to multiple conditions and choices
extract          --  Extract 1d array from flattened array according to mask
insert           --  Insert 1d array of values into Nd array according to mask
linspace         --  Evenly spaced samples in linear space
logspace         --  Evenly spaced samples in logarithmic space
fix              --  Round x to nearest integer towards zero
mod              --  Modulo mod(x,y) = x % y except keeps sign of y
amax             --  Array maximum along axis
amin             --  Array minimum along axis
ptp              --  Array max-min along axis
cumsum           --  Cumulative sum along axis
prod             --  Product of elements along axis
cumprod          --  Cumluative product along axis
diff             --  Discrete differences along axis
angle            --  Returns angle of complex argument
unwrap           --  Unwrap phase along given axis (1-d algorithm)
sort_complex     --  Sort a complex-array (based on real, then imaginary)
trim_zeros       --  trim the leading and trailing zeros from 1D array.

vectorize        -- a class that wraps a Python function taking scalar
                         arguments into a generalized function which
                         can handle arrays of arguments using the broadcast
                         rules of Numeric Python.

Shape manipulation
===================
squeeze          --  Return a with length-one dimensions removed.
atleast_1d       --  Force arrays to be > 1D
atleast_2d       --  Force arrays to be > 2D
atleast_3d       --  Force arrays to be > 3D
vstack           --  Stack arrays vertically (row on row)
hstack           --  Stack arrays horizontally (column on column)
column_stack     --  Stack 1D arrays as columns into 2D array
dstack           --  Stack arrays depthwise (along third dimension)
split            --  Divide array into a list of sub-arrays
hsplit           --  Split into columns
vsplit           --  Split into rows
dsplit           --  Split along third dimension

Matrix (2d array) manipluations
===============================
fliplr           --  2D array with columns flipped
flipud           --  2D array with rows flipped
rot90            --  Rotate a 2D array a multiple of 90 degrees
eye              --  Return a 2D array with ones down a given diagonal
diag             --  Construct a 2D array from a vector, or return a given
                       diagonal from a 2D array.                       
mat              --  Construct a Matrix

Polynomials
============
poly1d           --  A one-dimensional polynomial class

poly             --  Return polynomial coefficients from roots
roots            --  Find roots of polynomial given coefficients
polyint          --  Integrate polynomial
polyder          --  Differentiate polynomial
polyadd          --  Add polynomials
polysub          --  Substract polynomials
polymul          --  Multiply polynomials
polydiv          --  Divide polynomials
polyval          --  Evaluate polynomial at given argument

General functions
=================
vectorize -- Generalized Function class

Import tricks
=============
ppimport         --  Postpone module import until trying to use it
ppimport_attr    --  Postpone module import until trying to use its
                      attribute

Machine arithmetics
===================
machar_single    --  MachAr instance storing the parameters of system
                     single precision floating point arithmetics
machar_double    --  MachAr instance storing the parameters of system
                     double precision floating point arithmetics

Threading tricks
================
ParallelExec     --  Execute commands in parallel thread.
"""

standalone = 1


import types
import Numeric
from fastumath import isinf, isnan, isfinite
from Numeric import ArrayType, array, multiarray

__all__ = ['ScalarType','iscomplexobj','isrealobj','imag','iscomplex',
           'isscalar','isneginf','isposinf','isnan','isinf','isfinite',
           'isreal','nan_to_num','real','real_if_close',
           'typename','cast','common_type','typecodes', 'asarray']

def asarray(a, typecode=None, savespace=None):
   """asarray(a,typecode=None, savespace=0) returns a as a NumPy array.
   Unlike array(), no copy is performed if a is already an array.
   """
   if type(a) is ArrayType:
      if typecode is None or typecode == a.typecode():
         if savespace is None or a.spacesaver()==savespace:
            return a
      else:
         r = a.astype(typecode)
         if not (savespace is None or a.spacesaver()==savespace):
            r.savespace(savespace)
         return r
   return multiarray.array(a,typecode,copy=0,savespace=savespace or 0)

ScalarType = [types.IntType, types.LongType, types.FloatType, types.ComplexType]

typecodes = Numeric.typecodes
typecodes['AllInteger'] = '1silbwu'

try:
   Char = Numeric.Character
except AttributeError:
   Char = 'c'

toChar = lambda x: asarray(x).astype(Char)
toInt8 = lambda x: asarray(x).astype(Numeric.Int8)# or use variable names such as Byte
toUInt8 = lambda x: asarray(x).astype(Numeric.UnsignedInt8)
_unsigned = 0
if hasattr(Numeric,'UnsignedInt16'):
   toUInt16 = lambda x: asarray(x).astype(Numeric.UnsignedInt16)
   toUInt32 = lambda x: asarray(x).astype(Numeric.UnsignedInt32)
   _unsigned = 1
   
toInt16 = lambda x: asarray(x).astype(Numeric.Int16)
toInt32 = lambda x: asarray(x).astype(Numeric.Int32)
toInt = lambda x: asarray(x).astype(Numeric.Int)
toFloat32 = lambda x: asarray(x).astype(Numeric.Float32)
toFloat64 = lambda x: asarray(x).astype(Numeric.Float64)
toComplex32 = lambda x: asarray(x).astype(Numeric.Complex32)
toComplex64 = lambda x: asarray(x).astype(Numeric.Complex64)

# This is for pre Numeric 21.x compatiblity. Adding it is harmless.
if  not hasattr(Numeric,'Character'):
    Numeric.Character = 'c'
        
cast = {Numeric.Character: toChar,
        Numeric.UnsignedInt8: toUInt8,
        Numeric.Int8: toInt8,
        Numeric.Int16: toInt16,
        Numeric.Int32: toInt32,
        Numeric.Int: toInt,
        Numeric.Float32: toFloat32,
        Numeric.Float64: toFloat64,
        Numeric.Complex32: toComplex32,
        Numeric.Complex64: toComplex64}

if _unsigned:
   cast[Numeric.UnsignedInt16] = toUInt16
   cast[Numeric.UnsignedInt32] = toUInt32
   

def isscalar(num):
    if isinstance(num, ArrayType):
        return len(num.shape) == 0 and num.typecode() != 'O'
    return type(num) in ScalarType

def real(val):
    aval = asarray(val)
    if aval.typecode() in ['F', 'D']:
        return aval.real
    else:
        return aval

def imag(val):
    aval = asarray(val)
    if aval.typecode() in ['F', 'D']:
        return aval.imag
    else:
        return array(0,aval.typecode())*aval

def iscomplex(x):
    return imag(x) != Numeric.zeros(asarray(x).shape)

def isreal(x):
    return imag(x) == Numeric.zeros(asarray(x).shape)

def iscomplexobj(x):
    return asarray(x).typecode() in ['F', 'D']

def isrealobj(x):
    return not asarray(x).typecode() in ['F', 'D']

#-----------------------------------------------------------------------------

##def isnan(val):
##    # fast, but apparently not portable (according to notes by Tim Peters)
##    #return val != val
##    # very slow -- should really use cephes methods or *something* different
##    import ieee_754
##    vals = ravel(val)
##    if array_iscomplex(vals):
##        r = array(map(ieee_754.isnan,real(vals)))        
##        i = array(map(ieee_754.isnan,imag(vals)))
##        results = Numeric.logical_or(r,i)
##    else:        
##        results = array(map(ieee_754.isnan,vals))
##    if isscalar(val):
##        results = results[0]
##    return results

def isposinf(val):
    return isinf(val) & (val > 0)
    
def isneginf(val):
    return isinf(val) & (val < 0)
    
##def isinf(val):
##    return Numeric.logical_or(isposinf(val),isneginf(val))

##def isfinite(val):
##    vals = asarray(val)
##    if iscomplexobj(vals):
##        r = isfinite(real(vals))
##        i = isfinite(imag(vals))
##        results = Numeric.logical_and(r,i)
##    else:    
##        fin = Numeric.logical_not(isinf(val))
##        an = Numeric.logical_not(isnan(val))
##        results = Numeric.logical_and(fin,an)
##    return results        

def nan_to_num(x):
    # mapping:
    #    NaN -> 0
    #    Inf -> limits.double_max
    #   -Inf -> limits.double_min
    # complex not handled currently
    import limits
    try:
        t = x.typecode()
    except AttributeError:
        t = type(x)
    if t in [types.ComplexType,'F','D']:    
        y = nan_to_num(x.real) + 1j * nan_to_num(x.imag)
    else:    
        x = asarray(x)
        are_inf = isposinf(x)
        are_neg_inf = isneginf(x)
        are_nan = isnan(x)
        choose_array = are_neg_inf + are_nan * 2 + are_inf * 3
        y = Numeric.choose(choose_array,
                   (x,limits.double_min, 0., limits.double_max))
    return y

#-----------------------------------------------------------------------------

def real_if_close(a,tol=1e-13):
    a = asarray(a)
    if a.typecode() in ['F','D'] and Numeric.allclose(a.imag, 0, atol=tol):
        a = a.real
    return a


#-----------------------------------------------------------------------------

_namefromtype = {'c' : 'character',
                 '1' : 'signed char',
                 'b' : 'unsigned char',
                 's' : 'short',
                 'w' : 'unsigned short',
                 'i' : 'integer',
                 'u' : 'unsigned integer',
                 'l' : 'long integer',
                 'f' : 'float',
                 'd' : 'double',
                 'F' : 'complex float',
                 'D' : 'complex double',
                 'O' : 'object'
                 }

def typename(char):
    """Return an english name for the given typecode character.
    """
    return _namefromtype[char]

#-----------------------------------------------------------------------------

#determine the "minimum common type code" for a group of arrays.
array_kind = {'i':0, 'l': 0, 'f': 0, 'd': 0, 'F': 1, 'D': 1}
array_precision = {'i': 1, 'l': 1, 'f': 0, 'd': 1, 'F': 0, 'D': 1}
array_type = [['f', 'd'], ['F', 'D']]
def common_type(*arrays):
    kind = 0
    precision = 0
    for a in arrays:
        t = a.typecode()
        kind = max(kind, array_kind[t])
        precision = max(precision, array_precision[t])
    return array_type[kind][precision]

if __name__ == '__main__':
    print 'float epsilon:',float_epsilon
    print 'float tiny:',float_tiny
    print 'double epsilon:',double_epsilon
    print 'double tiny:',double_tiny

import Numeric
from Numeric import *
from scimath import *

from type_check import isscalar, asarray
from matrix_base import diag
from shape_base import hstack, atleast_1d
from function_base import trim_zeros, sort_complex

__all__ = ['poly','roots','polyint','polyder','polyadd','polysub','polymul',
           'polydiv','polyval','poly1d']
 
def get_eigval_func():
    try:
        import scipy.linalg
        eigvals = scipy.linalg.eigvals
    except ImportError:
        try:
            import linalg
            eigvals = linalg.eigvals
        except ImportError:
            try:
                import LinearAlgebra
                eigvals = LinearAlgebra.eigenvalues
            except:
                raise ImportError, \
                      "You must have scipy.linalg or LinearAlgebra to "\
                      "use this function."
    return eigvals

def poly(seq_of_zeros):
    """ Return a sequence representing a polynomial given a sequence of roots.

        If the input is a matrix, return the characteristic polynomial.
    
        Example:
    
         >>> b = roots([1,3,1,5,6])
         >>> poly(b)
         array([1., 3., 1., 5., 6.])
    """
    seq_of_zeros = atleast_1d(seq_of_zeros)    
    sh = shape(seq_of_zeros)
    if len(sh) == 2 and sh[0] == sh[1]:
        eig = get_eigval_func()
        seq_of_zeros=eig(seq_of_zeros)
    elif len(sh) ==1:
        pass
    else:
        raise ValueError, "input must be 1d or square 2d array."

    if len(seq_of_zeros) == 0:
        return 1.0

    a = [1]
    for k in range(len(seq_of_zeros)):
        a = convolve(a,[1, -seq_of_zeros[k]], mode=2)

        
    if a.typecode() in ['F','D']:
        # if complex roots are all complex conjugates, the roots are real.
        roots = asarray(seq_of_zeros,'D')
        pos_roots = sort_complex(compress(roots.imag > 0,roots))
        neg_roots = conjugate(sort_complex(compress(roots.imag < 0,roots)))
        if (len(pos_roots) == len(neg_roots) and
            alltrue(neg_roots == pos_roots)):
            a = a.real.copy()

    return a

def roots(p):
    """ Return the roots of the polynomial coefficients in p.

        The values in the rank-1 array p are coefficients of a polynomial.
        If the length of p is n+1 then the polynomial is
        p[0] * x**n + p[1] * x**(n-1) + ... + p[n-1]*x + p[n]
    """
    # If input is scalar, this makes it an array
    eig = get_eigval_func()
    p = atleast_1d(p)
    if len(p.shape) != 1:
        raise ValueError,"Input must be a rank-1 array."
        
    # find non-zero array entries
    non_zero = nonzero(ravel(p))

    # find the number of trailing zeros -- this is the number of roots at 0.
    trailing_zeros = len(p) - non_zero[-1] - 1

    # strip leading and trailing zeros
    p = p[int(non_zero[0]):int(non_zero[-1])+1]
    
    # casting: if incoming array isn't floating point, make it floating point.
    if p.typecode() not in ['f','d','F','D']:
        p = p.astype('d')

    N = len(p)
    if N > 1:
        # build companion matrix and find its eigenvalues (the roots)
        A = diag(ones((N-2,),p.typecode()),-1)
        A[0,:] = -p[1:] / p[0]
        roots = eig(A)
    else:
        return array([])

    # tack any zeros onto the back of the array    
    roots = hstack((roots,zeros(trailing_zeros,roots.typecode())))
    return roots

def polyint(p,m=1,k=None):
    """Return the mth analytical integral of the polynomial p.

    If k is None, then zero-valued constants of integration are used.
    otherwise, k should be a list of length m (or a scalar if m=1) to
    represent the constants of integration to use for each integration
    (starting with k[0])
    """
    m = int(m)
    if m < 0:
        raise ValueError, "Order of integral must be positive (see polyder)"
    if k is None:
        k = Numeric.zeros(m)
    k = atleast_1d(k)
    if len(k) == 1 and m > 1:
        k = k[0]*Numeric.ones(m)
    if len(k) < m:
        raise ValueError, \
              "k must be a scalar or a rank-1 array of length 1 or >m."
    if m == 0:
        return p
    else:
        truepoly = isinstance(p,poly1d)
        p = asarray(p)
        y = Numeric.zeros(len(p)+1,'d')
        y[:-1] = p*1.0/Numeric.arange(len(p),0,-1)
        y[-1] = k[0]        
        val = polyint(y,m-1,k=k[1:])
        if truepoly:
            val = poly1d(val)
        return val
            
def polyder(p,m=1):
    """Return the mth derivative of the polynomial p.
    """
    m = int(m)
    truepoly = isinstance(p,poly1d)
    p = asarray(p)
    n = len(p)-1
    y = p[:-1] * Numeric.arange(n,0,-1)
    if m < 0:
        raise ValueError, "Order of derivative must be positive (see polyint)"
    if m == 0:
        return p
    else:
        val = polyder(y,m-1)
        if truepoly:
            val = poly1d(val)
        return val

def polyval(p,x):
    """Evaluate the polynomial p at x.  If x is a polynomial then composition.

    Description:

      If p is of length N, this function returns the value:
      p[0]*(x**N-1) + p[1]*(x**N-2) + ... + p[N-2]*x + p[N-1]

      x can be a sequence and p(x) will be returned for all elements of x.
      or x can be another polynomial and the composite polynomial p(x) will be
      returned.
    """
    p = asarray(p)
    if isinstance(x,poly1d):
        y = 0
    else:
        x = asarray(x)
        y = Numeric.zeros(x.shape,x.typecode())
    for i in range(len(p)):
        y = x * y + p[i]
    return y

def polyadd(a1,a2):
    """Adds two polynomials represented as lists
    """
    truepoly = (isinstance(a1,poly1d) or isinstance(a2,poly1d))
    a1,a2 = map(atleast_1d,(a1,a2))
    diff = len(a2) - len(a1)
    if diff == 0:
        return a1 + a2
    elif diff > 0:
        zr = Numeric.zeros(diff)
        val = Numeric.concatenate((zr,a1)) + a2
    else:
        zr = Numeric.zeros(abs(diff))
        val = a1 + Numeric.concatenate((zr,a2))
    if truepoly:
        val = poly1d(val)
    return val

def polysub(a1,a2):
    """Subtracts two polynomials represented as lists
    """
    truepoly = (isinstance(a1,poly1d) or isinstance(a2,poly1d))
    a1,a2 = map(atleast_1d,(a1,a2))
    diff = len(a2) - len(a1)
    if diff == 0:
        return a1 - a2
    elif diff > 0:
        zr = Numeric.zeros(diff)
        val = Numeric.concatenate((zr,a1)) - a2
    else:
        zr = Numeric.zeros(abs(diff))
        val = a1 - Numeric.concatenate((zr,a2))
    if truepoly:
        val = poly1d(val)
    return val


def polymul(a1,a2):
    """Multiplies two polynomials represented as lists.
    """
    truepoly = (isinstance(a1,poly1d) or isinstance(a2,poly1d))
    val = Numeric.convolve(a1,a2)
    if truepoly:
        val = poly1d(val)
    return val

def polydiv(a1,a2):
    """Computes q and r polynomials so that a1(s) = q(s)*a2(s) + r(s)
    """
    truepoly = (isinstance(a1,poly1d) or isinstance(a2,poly1d))
    q, r = deconvolve(a1,a2)
    while Numeric.allclose(r[0], 0, rtol=1e-14) and (r.shape[-1] > 1):
        r = r[1:]
    if truepoly:
        q, r = map(poly1d,(q,r))
    return q, r

def deconvolve(signal, divisor):
    """Deconvolves divisor out of signal.
    """
    try:
        import scipy.signal
    except:
        print "You need scipy.signal to use this function."
    num = atleast_1d(signal)
    den = atleast_1d(divisor)
    N = len(num)
    D = len(den)
    if D > N:
        quot = [];
        rem = num;
    else:
        input = Numeric.ones(N-D+1,Numeric.Float)
        input[1:] = 0
        quot = scipy.signal.lfilter(num, den, input)
        rem = num - Numeric.convolve(den,quot,mode=2)
    return quot, rem

import re
_poly_mat = re.compile(r"[*][*]([0-9]*)")
def _raise_power(astr, wrap=70):
    n = 0
    line1 = ''
    line2 = ''
    output = ' '
    while 1:
        mat = _poly_mat.search(astr,n)
        if mat is None:
            break
        span = mat.span()
        power = mat.groups()[0]
        partstr = astr[n:span[0]]
        n = span[1]
        toadd2 = partstr + ' '*(len(power)-1)
        toadd1 = ' '*(len(partstr)-1) + power
        if ((len(line2)+len(toadd2) > wrap) or \
            (len(line1)+len(toadd1) > wrap)):
            output += line1 + "\n" + line2 + "\n "
            line1 = toadd1
            line2 = toadd2
        else:                
            line2 += partstr + ' '*(len(power)-1)
            line1 += ' '*(len(partstr)-1) + power
    output += line1 + "\n" + line2
    return output + astr[n:]
    
                       
class poly1d:
    """A one-dimensional polynomial class.

    p = poly1d([1,2,3]) constructs the polynomial x**2 + 2 x + 3

    p(0.5) evaluates the polynomial at the location
    p.r  is a list of roots
    p.c  is the coefficient array [1,2,3]
    p.order is the polynomial order (after leading zeros in p.c are removed)
    p[k] is the coefficient on the kth power of x (backwards from
         sequencing the coefficient array.

    polynomials can be added, substracted, multplied and divided (returns
         quotient and remainder).
    asarray(p) will also give the coefficient array, so polynomials can
         be used in all functions that accept arrays.
    """
    def __init__(self, c_or_r, r=0):
        if isinstance(c_or_r,poly1d):
            for key in c_or_r.__dict__.keys():
                self.__dict__[key] = c_or_r.__dict__[key]
            return
        if r:
            c_or_r = poly(c_or_r)
        c_or_r = atleast_1d(c_or_r)
        if len(c_or_r.shape) > 1:
            raise ValueError, "Polynomial must be 1d only."
        c_or_r = trim_zeros(c_or_r, trim='f')
        if len(c_or_r) == 0:
            c_or_r = Numeric.array([0])
        self.__dict__['coeffs'] = c_or_r
        self.__dict__['order'] = len(c_or_r) - 1

    def __array__(self,t=None):
        if t:
            return asarray(self.coeffs,t)
        else:
            return asarray(self.coeffs)

    def __coerce__(self,other):
        return None
    
    def __repr__(self):
        vals = repr(self.coeffs)
        vals = vals[6:-1]
        return "poly1d(%s)" % vals

    def __len__(self):
        return self.order

    def __str__(self):
        N = self.order
        thestr = "0"
        for k in range(len(self.coeffs)):
            coefstr ='%.4g' % abs(self.coeffs[k])
            if coefstr[-4:] == '0000':
                coefstr = coefstr[:-5]
            power = (N-k)
            if power == 0:
                if coefstr != '0':
                    newstr = '%s' % (coefstr,)
                else:
                    if k == 0:
                        newstr = '0'
                    else:
                        newstr = ''
            elif power == 1:
                if coefstr == '0':
                    newstr = ''
                elif coefstr == '1':
                    newstr = 'x'
                else:                    
                    newstr = '%s x' % (coefstr,)
            else:
                if coefstr == '0':
                    newstr = ''
                elif coefstr == '1':
                    newstr = 'x**%d' % (power,)
                else:                    
                    newstr = '%s x**%d' % (coefstr, power)

            if k > 0:
                if newstr != '':
                    if self.coeffs[k] < 0:
                        thestr = "%s - %s" % (thestr, newstr)
                    else:
                        thestr = "%s + %s" % (thestr, newstr)
            elif (k == 0) and (newstr != '') and (self.coeffs[k] < 0):
                thestr = "-%s" % (newstr,)
            else:
                thestr = newstr
        return _raise_power(thestr)
        

    def __call__(self, val):
        return polyval(self.coeffs, val)

    def __mul__(self, other):
        if isscalar(other):
            return poly1d(self.coeffs * other)
        else:
            other = poly1d(other)
            return poly1d(polymul(self.coeffs, other.coeffs))

    def __rmul__(self, other):
        if isscalar(other):
            return poly1d(other * self.coeffs)
        else:
            other = poly1d(other)
            return poly1d(polymul(self.coeffs, other.coeffs))        
    
    def __add__(self, other):
        other = poly1d(other)
        return poly1d(polyadd(self.coeffs, other.coeffs))        
        
    def __radd__(self, other):
        other = poly1d(other)
        return poly1d(polyadd(self.coeffs, other.coeffs))

    def __pow__(self, val):
        if not isscalar(val) or int(val) != val or val < 0:
            raise ValueError, "Power to non-negative integers only."
        res = [1]
        for k in range(val):
            res = polymul(self.coeffs, res)
        return poly1d(res)

    def __sub__(self, other):
        other = poly1d(other)
        return poly1d(polysub(self.coeffs, other.coeffs))

    def __rsub__(self, other):
        other = poly1d(other)
        return poly1d(polysub(other.coeffs, self.coeffs))

    def __div__(self, other):
        if isscalar(other):
            return poly1d(self.coeffs/other)
        else:
            other = poly1d(other)
            return map(poly1d,polydiv(self.coeffs, other.coeffs))

    def __rdiv__(self, other):
        if isscalar(other):
            return poly1d(other/self.coeffs)
        else:
            other = poly1d(other)
            return map(poly1d,polydiv(other.coeffs, self.coeffs))

    def __setattr__(self, key, val):
        raise ValueError, "Attributes cannot be changed this way."

    def __getattr__(self, key):
        if key in ['r','roots']:
            return roots(self.coeffs)
        elif key in ['c','coef','coefficients']:
            return self.coeffs
        elif key in ['o']:
            return self.order
        else:
            return self.__dict__[key]
        
    def __getitem__(self, val):
        ind = self.order - val
        if val > self.order:
            return 0
        if val < 0:
            return 0
        return self.coeffs[ind]

    def __setitem__(self, key, val):
        ind = self.order - key
        if key < 0:
            raise ValueError, "Does not support negative powers."
        if key > self.order:
            zr = Numeric.zeros(key-self.order,self.coeffs.typecode())
            self.__dict__['coeffs'] = Numeric.concatenate((zr,self.coeffs))
            self.__dict__['order'] = key
            ind = 0
        self.__dict__['coeffs'][ind] = val
        return

    def integ(self, m=1, k=0):
        return poly1d(polyint(self.coeffs,m=m,k=k))

    def deriv(self, m=1):
        return poly1d(polyder(self.coeffs,m=m))

