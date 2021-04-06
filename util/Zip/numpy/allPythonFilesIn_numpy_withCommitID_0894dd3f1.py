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
                    
            except (TypeError, KeyError):
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
    import tempfile        
    python_name = "python%d%d_compiled" % tuple(sys.version_info[:2])    
    if sys.platform != 'win32':
        try:
            path = os.path.join(os.environ['HOME'],'.' + python_name)
        except KeyError:
            temp_dir = `os.getuid()` + '_' + python_name
            path = os.path.join(tempfile.gettempdir(),temp_dir)        
    else:
        path = os.path.join(tempfile.gettempdir(),python_name)
        
    if not os.path.exists(path):
        os.mkdir(path)
        os.chmod(path,0700) # make it only accessible by this user.
    if not os.access(path,os.W_OK):
        print 'warning: default directory is not write accessible.'
        print 'defualt:', path
    return path

def intermediate_dir():
    """ Location in temp dir for storing .cpp and .o  files during
        builds.
    """
    import tempfile        
    python_name = "python%d%d_intermediate" % tuple(sys.version_info[:2])    
    path = os.path.join(tempfile.gettempdir(),python_name)
    if not os.path.exists(path):
        os.mkdir(path)
    return path
    
def default_temp_dir():
    path = os.path.join(default_dir(),'temp')
    if not os.path.exists(path):
        os.mkdir(path)
        os.chmod(path,0700) # make it only accessible by this user.
    if not os.access(path,os.W_OK):
        print 'warning: default directory is not write accessible.'
        print 'defualt:', path
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
    try:
        # code reliant on the fact that we are using dumbdbm
        if dumb and mode == 'r' and not os.path.exists(catalog_file+'.dat'):
            sh = None
        else:
            sh = shelve.open(catalog_file,mode)
    except: # not sure how to pin down which error to catch yet
        sh = None
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
        
def test():
    from scipy_test import module_test
    module_test(__name__,__file__)

def test_suite():
    from scipy_test import module_test_suite
    return module_test_suite(__name__,__file__)    

#!/usr/bin/env python

import os
from glob import glob
from scipy_distutils.misc_util import get_path, default_config_dict, dot_join

def configuration(parent_package=''):
    parent_path = parent_package
    local_path = get_path(__name__)
    config = default_config_dict('weave',parent_package)
    config['packages'].append(dot_join(parent_package,'weave.tests'))
    test_path = os.path.join(local_path,'tests')
    config['package_dir']['weave.tests'] = test_path
    
    scxx_files = glob(os.path.join(local_path,'scxx','*.h'))
    install_path = os.path.join(parent_path,'weave','scxx')
    config['data_files'].extend( [(install_path,scxx_files)])

    cxx_files = glob(os.path.join(local_path,'CXX','*.*'))
    install_path = os.path.join(parent_path,'weave','CXX')
    config['data_files'].extend( [(install_path,cxx_files)])
    
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
    setup(**configuration())

""" C/C++ code strings needed for converting most non-sequence
    Python variables:
        module_support_code -- several routines used by most other code 
                               conversion methods.  It holds the only
                               CXX dependent code in this file.  The CXX
                               stuff is used for exceptions
        file_convert_code
        instance_convert_code
        callable_convert_code
        module_convert_code
        
        scalar_convert_code
        non_template_scalar_support_code               
            Scalar conversion covers int, float, double, complex,
            and double complex.  While Python doesn't support all these,
            Numeric does and so all of them are made available.
            Python longs are currently converted to C ints.  Any
            better way to handle this?
"""

import base_info

#############################################################
# Basic module support code
#############################################################

module_support_code = \
"""

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
  PyErr_SetString(exc, msg);
  throw 1;
}

void handle_bad_type(PyObject* py_obj, char* good_type, char* var_name)
{
    char msg[500];
    sprintf(msg,"received '%s' type instead of '%s' for variable '%s'",
            find_type(py_obj),good_type,var_name);
    throw_error(PyExc_TypeError,msg);    
}

void handle_conversion_error(PyObject* py_obj, char* good_type, char* var_name)
{
    char msg[500];
    sprintf(msg,"Conversion Error:, received '%s' type instead of '%s' for variable '%s'",
            find_type(py_obj),good_type,var_name);
    throw_error(PyExc_TypeError,msg);
}

"""

#############################################################
# File conversion support code
#############################################################

file_convert_code =  \
"""

FILE* convert_to_file(PyObject* py_obj, char* name)
{
    if (!py_obj || !PyFile_Check(py_obj))
        handle_conversion_error(py_obj,"file", name);

    // Cleanup code should call DECREF
    Py_INCREF(py_obj);
    return PyFile_AsFile(py_obj);
}

FILE* py_to_file(PyObject* py_obj, char* name)
{
    if (!py_obj || !PyFile_Check(py_obj))
        handle_bad_type(py_obj,"file", name);

    // Cleanup code should call DECREF
    Py_INCREF(py_obj);
    return PyFile_AsFile(py_obj);
}

PyObject* file_to_py(FILE* file, char* name, char* mode)
{
    PyObject* py_obj = NULL;
    //extern int fclose(FILE *);
    return (PyObject*) PyFile_FromFile(file, name, mode, fclose);
}

"""

#############################################################
# Instance conversion code
#############################################################

instance_convert_code = \
"""

PyObject* convert_to_instance(PyObject* py_obj, char* name)
{
    if (!py_obj || !PyFile_Check(py_obj))
        handle_conversion_error(py_obj,"instance", name);

    // Should I INCREF???
    // Py_INCREF(py_obj);
    // just return the raw python pointer.
    return py_obj;
}

PyObject* py_to_instance(PyObject* py_obj, char* name)
{
    if (!py_obj || !PyFile_Check(py_obj))
        handle_bad_type(py_obj,"instance", name);

    // Should I INCREF???
    // Py_INCREF(py_obj);
    // just return the raw python pointer.
    return py_obj;
}

PyObject* instance_to_py(PyObject* instance)
{
    // Don't think I need to do anything...
    return (PyObject*) instance;
}

"""

#############################################################
# Callable conversion code
#############################################################

callable_convert_code = \
"""

PyObject* convert_to_callable(PyObject* py_obj, char* name)
{
    if (!py_obj || !PyCallable_Check(py_obj))
        handle_conversion_error(py_obj,"callable", name);

    // Should I INCREF???
    // Py_INCREF(py_obj);
    // just return the raw python pointer.
    return py_obj;
}

PyObject* py_to_callable(PyObject* py_obj, char* name)
{
    if (!py_obj || !PyCallable_Check(py_obj))
        handle_bad_type(py_obj,"callable", name);

    // Should I INCREF???
    // Py_INCREF(py_obj);
    // just return the raw python pointer.
    return py_obj;
}

PyObject* callable_to_py(PyObject* callable)
{
    // Don't think I need to do anything...
    return (PyObject*) callable;
}

"""

#############################################################
# Module conversion code
#############################################################

module_convert_code = \
"""
PyObject* convert_to_module(PyObject* py_obj, char* name)
{
    if (!py_obj || !PyModule_Check(py_obj))
        handle_conversion_error(py_obj,"module", name);

    // Should I INCREF???
    // Py_INCREF(py_obj);
    // just return the raw python pointer.
    return py_obj;
}

PyObject* py_to_module(PyObject* py_obj, char* name)
{
    if (!py_obj || !PyModule_Check(py_obj))
        handle_bad_type(py_obj,"module", name);

    // Should I INCREF???
    // Py_INCREF(py_obj);
    // just return the raw python pointer.
    return py_obj;
}

PyObject* module_to_py(PyObject* module)
{
    // Don't think I need to do anything...
    return (PyObject*) module;
}

"""

#############################################################
# Scalar conversion code
#############################################################

import base_info

# this code will not build with msvc...
scalar_support_code = \
"""
// conversion routines

template<class T> 
static T convert_to_scalar(PyObject* py_obj,char* name)
{
    //never used.
    return (T) 0;
}
template<>
static int convert_to_scalar<int>(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyInt_Check(py_obj))
        handle_conversion_error(py_obj,"int", name);
    return (int) PyInt_AsLong(py_obj);
}

template<>
static long convert_to_scalar<long>(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyLong_Check(py_obj))
        handle_conversion_error(py_obj,"long", name);
    return (long) PyLong_AsLong(py_obj);
}

template<> 
static double convert_to_scalar<double>(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyFloat_Check(py_obj))
        handle_conversion_error(py_obj,"float", name);
    return PyFloat_AsDouble(py_obj);
}

template<> 
static float convert_to_scalar<float>(PyObject* py_obj,char* name)
{
    return (float) convert_to_scalar<double>(py_obj,name);
}

// complex not checked.
template<> 
static std::complex<float> convert_to_scalar<std::complex<float> >(PyObject* py_obj,
                                                              char* name)
{
    if (!py_obj || !PyComplex_Check(py_obj))
        handle_conversion_error(py_obj,"complex", name);
    return std::complex<float>((float) PyComplex_RealAsDouble(py_obj),
                               (float) PyComplex_ImagAsDouble(py_obj));    
}
template<> 
static std::complex<double> convert_to_scalar<std::complex<double> >(
                                            PyObject* py_obj,char* name)
{
    if (!py_obj || !PyComplex_Check(py_obj))
        handle_conversion_error(py_obj,"complex", name);
    return std::complex<double>(PyComplex_RealAsDouble(py_obj),
                                PyComplex_ImagAsDouble(py_obj));    
}

/////////////////////////////////
// standard translation routines

template<class T> 
static T py_to_scalar(PyObject* py_obj,char* name)
{
    //never used.
    return (T) 0;
}
template<>
static int py_to_scalar<int>(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyInt_Check(py_obj))
        handle_bad_type(py_obj,"int", name);
    return (int) PyInt_AsLong(py_obj);
}

template<>
static long py_to_scalar<long>(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyLong_Check(py_obj))
        handle_bad_type(py_obj,"long", name);
    return (long) PyLong_AsLong(py_obj);
}

template<> 
static double py_to_scalar<double>(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyFloat_Check(py_obj))
        handle_bad_type(py_obj,"float", name);
    return PyFloat_AsDouble(py_obj);
}

template<> 
static float py_to_scalar<float>(PyObject* py_obj,char* name)
{
    return (float) py_to_scalar<double>(py_obj,name);
}

// complex not checked.
template<> 
static std::complex<float> py_to_scalar<std::complex<float> >(PyObject* py_obj,
                                                              char* name)
{
    if (!py_obj || !PyComplex_Check(py_obj))
        handle_bad_type(py_obj,"complex", name);
    return std::complex<float>((float) PyComplex_RealAsDouble(py_obj),
                               (float) PyComplex_ImagAsDouble(py_obj));    
}
template<> 
static std::complex<double> py_to_scalar<std::complex<double> >(
                                            PyObject* py_obj,char* name)
{
    if (!py_obj || !PyComplex_Check(py_obj))
        handle_bad_type(py_obj,"complex", name);
    return std::complex<double>(PyComplex_RealAsDouble(py_obj),
                                PyComplex_ImagAsDouble(py_obj));    
}
"""    

non_template_scalar_support_code = \
"""

// Conversion Errors

static int convert_to_int(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyInt_Check(py_obj))
        handle_conversion_error(py_obj,"int", name);
    return (int) PyInt_AsLong(py_obj);
}

static long convert_to_long(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyLong_Check(py_obj))
        handle_conversion_error(py_obj,"long", name);
    return (long) PyLong_AsLong(py_obj);
}

static double convert_to_float(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyFloat_Check(py_obj))
        handle_conversion_error(py_obj,"float", name);
    return PyFloat_AsDouble(py_obj);
}

// complex not checked.
static std::complex<double> convert_to_complex(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyComplex_Check(py_obj))
        handle_conversion_error(py_obj,"complex", name);
    return std::complex<double>(PyComplex_RealAsDouble(py_obj),
                                PyComplex_ImagAsDouble(py_obj));    
}

/////////////////////////////////////
// The following functions are used for scalar conversions in msvc
// because it doesn't handle templates as well.

static int py_to_int(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyInt_Check(py_obj))
        handle_bad_type(py_obj,"int", name);
    return (int) PyInt_AsLong(py_obj);
}

static long py_to_long(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyLong_Check(py_obj))
        handle_bad_type(py_obj,"long", name);
    return (long) PyLong_AsLong(py_obj);
}

static double py_to_float(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyFloat_Check(py_obj))
        handle_bad_type(py_obj,"float", name);
    return PyFloat_AsDouble(py_obj);
}

// complex not checked.
static std::complex<double> py_to_complex(PyObject* py_obj,char* name)
{
    if (!py_obj || !PyComplex_Check(py_obj))
        handle_bad_type(py_obj,"complex", name);
    return std::complex<double>(PyComplex_RealAsDouble(py_obj),
                                PyComplex_ImagAsDouble(py_obj));    
}
"""    

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
    from fastumath import *
except:
    pass # fastumath not available    
    
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
    from code_blocks import module_header

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
    ast_list = ast.tolist()
    
    expr_code = ast_to_blitz_expr(ast_list)
    arg_list = harvest_variables(ast_list)
    arg_specs = assign_variable_types(arg_list,locals())
    
    func,template_types = create_function('test_function',expr_code,arg_list,arg_specs)
    init,used_names = create_module_init('compile_sample','test_function',template_types)
    #wrapper = create_wrapper(mod_name,func_name,used_names)
    return string.join( [module_header,func,init],'\n')
    """
def test():
    from scipy_test import module_test
    module_test(__name__,__file__)

def test_suite():
    from scipy_test import module_test_suite
    return module_test_suite(__name__,__file__)    

if __name__ == "__main__":
    test_function()
from base_spec import base_converter
from scalar_spec import numeric_to_c_type_mapping
from Numeric import *
from types import *
import os
import blitz_info

class array_converter(base_converter):
    _build_information = [blitz_info.array_info()]

    def type_match(self,value):
        return type(value) is ArrayType

    def type_spec(self,name,value):
        new_spec = array_converter()
        new_spec.name = name
        new_spec.numeric_type = value.typecode()
        new_spec.dims = len(value.shape)
        if new_spec.dims > 11:
            msg = "Error converting variable '" + name + "'.  " \
                  "blitz only supports arrays up to 11 dimensions."
            raise ValueError, msg
        return new_spec

    def declaration_code(self,templatize = 0,inline=0):
        if inline:
            code = self.inline_decl_code()
        else:
            code = self.standard_decl_code()
        return code

    def inline_decl_code(self):
        type = numeric_to_c_type_mapping[self.numeric_type]
        dims = self.dims
        name = self.name
        var_name = self.retrieve_py_variable(inline=1)
        arr_name = name + '_arr_obj'
        # We've had to inject quite a bit of code in here to handle the Aborted error
        # caused by exceptions.  The templates made the easy fix (with MACROS) for all
        # other types difficult here.  Oh well.
        templ = '// blitz_array_declaration\n' \
                'py_%(name)s= %(var_name)s;\n' \
                'PyArrayObject* %(arr_name)s = convert_to_numpy(py_%(name)s,"%(name)s");\n' \
                'conversion_numpy_check_size(%(arr_name)s,%(dims)s,"%(name)s");\n' \
                'conversion_numpy_check_type(%(arr_name)s,py_type<%(type)s>::code,"%(name)s");\n' \
                'blitz::Array<%(type)s,%(dims)d> %(name)s =' \
                ' convert_to_blitz<%(type)s,%(dims)d>(%(arr_name)s,"%(name)s");\n' \
                'blitz::TinyVector<int,%(dims)d> _N%(name)s = %(name)s.shape();\n'
        code = templ % locals()
        return code

    def standard_decl_code(self):
        type = numeric_to_c_type_mapping[self.numeric_type]
        dims = self.dims
        name = self.name
        var_name = self.retrieve_py_variable(inline=0)
        arr_name = name + '_arr_obj'
        # We've had to inject quite a bit of code in here to handle the Aborted error
        # caused by exceptions.  The templates made the easy fix (with MACROS) for all
        # other types difficult here.  Oh well.
        templ = '// blitz_array_declaration\n' \
                'PyArrayObject* %(arr_name)s = convert_to_numpy(%(var_name)s,"%(name)s");\n' \
                'conversion_numpy_check_size(%(arr_name)s,%(dims)s,"%(name)s");\n' \
                'conversion_numpy_check_type(%(arr_name)s,py_type<%(type)s>::code,"%(name)s");\n' \
                'blitz::Array<%(type)s,%(dims)d> %(name)s =' \
                ' convert_to_blitz<%(type)s,%(dims)d>(%(arr_name)s,"%(name)s");\n' \
                'blitz::TinyVector<int,%(dims)d> _N%(name)s = %(name)s.shape();\n'
        code = templ % locals()
        return code

    def local_dict_code(self):
        code = '// for now, array "%s" is not returned as arryas are edited' \
               ' in place (should this change?)\n' % (self.name)
        return code

    def cleanup_code(self):
        # could use Py_DECREF here I think and save NULL test.
        code = "Py_XDECREF(py_%s);\n" % self.name
        return code

    def __repr__(self):
        msg = "(array:: name: %s, type: %s, dims: %d)" % \
                  (self.name, self.numeric_type, self.dims)
        return msg

    def __cmp__(self,other):
        #only works for equal
        return cmp(self.name,other.name) or  \
               cmp(self.numeric_type,other.numeric_type) or \
               cmp(self.dims, other.dims) or \
               cmp(self.__class__, other.__class__)


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
    """Match `data' to `pattern', with variable extraction.

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
    def type_spec(self,name,value): pass
    def declaration_code(self,templatize = 0):   return ""
    def local_dict_code(self): return ""
    def cleanup_code(self): return ""
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
        
    def py_references(self): return map(lambda x: x.py_reference(),self)
    def py_pointers(self): return map(lambda x: x.py_pointer(),self)
    def py_variables(self): return map(lambda x: x.py_variable(),self)

    def references(self): return map(lambda x: x.py_reference(),self)
    def pointers(self): return map(lambda x: x.pointer(),self)    
    def variables(self): return map(lambda x: x.variable(),self)
    
    def variable_as_strings(self): 
        return map(lambda x: x.variable_as_string(),self)

    
import swig_info

# THIS IS PLATFORM DEPENDENT FOR NOW. 
# YOU HAVE TO SPECIFY YOUR WXWINDOWS DIRECTORY

wx_dir = 'C:\\wx230\\include'

class wx_info(swig_info.swig_info):
    _headers = ['"wx/wx.h"']
    _include_dirs = [wx_dir]
    _define_macros=[('wxUSE_GUI', '1')]
    _libraries = ['wx23_1']
    _library_dirs = ['c:/wx230/lib']
# should re-write compiled functions to take a local and global dict
# as input.
import sys,os
import ext_tools
import string
import catalog
import inline_info, cxx_info

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
        declare_return = 'PyObject *return_val = NULL;\n'    \
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
        catch_code =  "catch(...)                       \n"   \
                      "{                                \n" + \
                      "    return_val =  Py::Null();    \n"   \
                      "    exception_occured = 1;       \n"   \
                      "}                                \n"   
        return_code = "    /* cleanup code */                   \n" + \
                           cleanup_code                             + \
                      "    if(!return_val && !exception_occured)\n"   \
                      "    {\n                                  \n"   \
                      "        Py_INCREF(Py_None);              \n"   \
                      "        return_val = Py_None;            \n"   \
                      "    }\n                                  \n"   \
                      "    return return_val;           \n"           \
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
        self._build_information.append(inline_info.inline_info())

function_cache = {}
def inline(code,arg_names=[],local_dict = None, global_dict = None,
           force = 0,
           compiler='',
           verbose = 0,
           support_code = None,
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

def test():
    from scipy_test import module_test
    module_test(__name__,__file__)

def test_suite():
    from scipy_test import module_test_suite
    return module_test_suite(__name__,__file__)    

if __name__ == "__main__":
    test_function()


import cxx_info
from base_spec import base_converter
from types import *
import os

class base_cxx_converter(base_converter):
    _build_information = [cxx_info.cxx_info()]
    def type_spec(self,name,value):
        # factory
        new_spec = self.__class__()
        new_spec.name = name        
        return new_spec
    def __repr__(self):
        msg = "(%s:: name: %s)" % (self.type_name,self.name)
        return msg
    def __cmp__(self,other):
        #only works for equal
        return cmp(self.name,other.name) or \
               cmp(self.__class__, other.__class__)
        
class string_converter(base_cxx_converter):
    type_name = 'string'
    def type_match(self,value):
        return type(value) in [StringType]

    def declaration_code(self,templatize = 0,inline=0):
        var_name = self.retrieve_py_variable(inline)
        code = 'Py::String %s = convert_to_string(%s,"%s");\n' % \
               (self.name,var_name,self.name)
        return code       
    def local_dict_code(self):
        code = 'local_dict["%s"] = %s;\n' % (self.name,self.name)        
        return code


class list_converter(base_cxx_converter):
    type_name = 'list'
    def type_match(self,value):
        return type(value) in [ListType]

    def declaration_code(self,templatize = 0,inline=0):
        var_name = self.retrieve_py_variable(inline)
        code = 'Py::List %s = convert_to_list(%s,"%s");\n' % \
               (self.name,var_name,self.name)
        return code       
    def local_dict_code(self):
        code = 'local_dict["%s"] = %s;\n' % (self.name,self.name)        
        return code

class dict_converter(base_cxx_converter):
    type_name = 'dict'
    def type_match(self,value):
        return type(value) in [DictType]

    def declaration_code(self,templatize = 0,inline=0):
        var_name = self.retrieve_py_variable(inline)
        code = 'Py::Dict %s = convert_to_dict(%s,"%s");\n' % \
               (self.name,var_name,self.name)               
        return code
               
    def local_dict_code(self):
        code = 'local_dict["%s"] = %s;\n' % (self.name,self.name)        
        return code

class tuple_converter(base_cxx_converter):
    type_name = 'tuple'
    def type_match(self,value):
        return type(value) in [TupleType]

    def declaration_code(self,templatize = 0,inline=0):
        var_name = self.retrieve_py_variable(inline)
        code = 'Py::Tuple %s = convert_to_tuple(%s,"%s");\n' % \
               (self.name,var_name,self.name)
        return code       
    def local_dict_code(self):
        code = 'local_dict["%s"] = %s;\n' % (self.name,self.name)        
        return code

def test():
    from scipy_test import module_test
    module_test(__name__,__file__)

def test_suite():
    from scipy_test import module_test_suite
    return module_test_suite(__name__,__file__)    


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
    if deffile == None:
        deffile = sys.stdout
    else:
        deffile = open(deffile, 'w')
    nm_cmd = '%s %s' % (DEFAULT_NM, libfile)
    nm_output = getnm(nm_cmd)
    dlist, flist = parse_nm(nm_output)
    output_def(dlist, flist, DEF_HEADER, deffile)

from base_spec import base_converter
import common_info
from types import *
import os

class common_base_converter(base_converter):
    def type_spec(self,name,value):
        # factory
        new_spec = self.__class__()
        new_spec.name = name        
        return new_spec
    def __repr__(self):
        msg = "(file:: name: %s)" % self.name
        return msg
    def __cmp__(self,other):
        #only works for equal
        return cmp(self.name,other.name) or \
               cmp(self.__class__, other.__class__)
        
    
class file_converter(common_base_converter):
    type_name = 'file'
    _build_information = [common_info.file_info()]
    def type_match(self,value):
        return type(value) in [FileType]

    def declaration_code(self,templatize = 0,inline=0):
        var_name = self.retrieve_py_variable(inline)
        #code = 'PyObject* py_%s = %s;\n'   \
        #       'FILE* %s = convert_to_file(py_%s,"%s");\n' % \
        #       (self.name,var_name,self.name,self.name,self.name)
        code = 'PyObject* py_%s = %s;\n'   \
               'FILE* %s = convert_to_file(py_%s,"%s");\n' % \
               (self.name,var_name,self.name,self.name,self.name)
        return code       
    def cleanup_code(self):
        # could use Py_DECREF here I think and save NULL test.
        code = "Py_XDECREF(py_%s);\n" % self.name
        return code

class callable_converter(common_base_converter):
    type_name = 'callable'
    _build_information = [common_info.callable_info()]
    def type_match(self,value):
        # probably should test for callable classes here also.
        return type(value) in [FunctionType,MethodType,type(len)]

    def declaration_code(self,templatize = 0,inline=0):
        var_name = self.retrieve_py_variable(inline)
        code = 'PyObject* %s = convert_to_callable(%s,"%s");\n' % \
               (self.name,var_name,self.name)
        return code       

class instance_converter(common_base_converter):
    type_name = 'instance'
    _build_information = [common_info.instance_info()]
    def type_match(self,value):
        return type(value) in [InstanceType]

    def declaration_code(self,templatize = 0,inline=0):
        var_name = self.retrieve_py_variable(inline)
        code = 'PyObject* %s = convert_to_instance(%s,"%s");\n' % \
               (self.name,var_name,self.name)
        return code       

def test():
    from scipy_test import module_test
    module_test(__name__,__file__)

def test_suite():
    from scipy_test import module_test_suite
    return module_test_suite(__name__,__file__)    

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

import base_info
class inline_info(base_info.base_info):
    _support_code = [get_variable_support_code, py_to_raw_dict_support_code]

from base_spec import base_converter
from scalar_spec import numeric_to_c_type_mapping
from Numeric import *
from types import *
import os
import standard_array_info

class array_converter(base_converter):
    _build_information = [standard_array_info.array_info()]
    
    def type_match(self,value):
        return type(value) is ArrayType

    def type_spec(self,name,value):
        # factory
        new_spec = array_converter()
        new_spec.name = name
        new_spec.numeric_type = value.typecode()
        # dims not used, but here for compatibility with blitz_spec
        new_spec.dims = len(shape(value))
        return new_spec

    def declaration_code(self,templatize = 0,inline=0):
        if inline:
            code = self.inline_decl_code()
        else:
            code = self.standard_decl_code()
        return code
    
    def inline_decl_code(self):
        type = numeric_to_c_type_mapping[self.numeric_type]
        name = self.name
        var_name = self.retrieve_py_variable(inline=1)
        templ = '// %(name)s array declaration\n' \
                'py_%(name)s= %(var_name)s;\n' \
                'PyArrayObject* %(name)s = convert_to_numpy(py_%(name)s,"%(name)s");\n' \
                'int* _N%(name)s = %(name)s->dimensions;\n' \
                'int* _S%(name)s = %(name)s->strides;\n' \
                'int _D%(name)s = %(name)s->nd;\n' \
                '%(type)s* %(name)s_data = (%(type)s*) %(name)s->data;\n' 
        code = templ % locals()
        return code

    def standard_decl_code(self):    
        type = numeric_to_c_type_mapping[self.numeric_type]
        name = self.name
        templ = '// %(name)s array declaration\n' \
                'PyArrayObject* %(name)s = convert_to_numpy(py_%(name)s,"%(name)s");\n' \
                'int* _N%(name)s = %(name)s->dimensions;\n' \
                'int* _S%(name)s = %(name)s->strides;\n' \
                'int _D%(name)s = %(name)s->nd;\n' \
                '%(type)s* %(name)s_data = (%(type)s*) %(name)s->data;\n' 
        code = templ % locals()
        return code
    #def c_function_declaration_code(self):
    #    """
    #        This doesn't pass the size through.  That info is gonna have to 
    #        be redone in the c function.
    #    """
    #    templ_dict = {}
    #    templ_dict['type'] = numeric_to_c_type_mapping[self.numeric_type]
    #    templ_dict['dims'] = self.dims
    #    templ_dict['name'] = self.name
    #    code = 'blitz::Array<%(type)s,%(dims)d> &%(name)s' % templ_dict
    #    return code
        
    def local_dict_code(self):
        code = '// for now, array "%s" is not returned as arryas are edited' \
               ' in place (should this change?)\n' % (self.name)        
        return code

    def cleanup_code(self):
        # could use Py_DECREF here I think and save NULL test.
        code = "Py_XDECREF(py_%s);\n" % self.name
        return code

    def __repr__(self):
        msg = "(array:: name: %s, type: %s)" % \
                  (self.name, self.numeric_type)
        return msg

    def __cmp__(self,other):
        #only works for equal
        return cmp(self.name,other.name) or  \
               cmp(self.numeric_type,other.numeric_type) or \
               cmp(self.dims, other.dims) or \
               cmp(self.__class__, other.__class__)

def test():
    from scipy_test import module_test
    module_test(__name__,__file__)

def test_suite():
    from scipy_test import module_test_suite
    return module_test_suite(__name__,__file__)    

""" compiler provides several tools:

        1. inline() -- a function for including C/C++ code within Python
        2. blitz()  -- a function for compiling Numeric expressions to C++
        3. ext_tools-- a module that helps construct C/C++ extension modules.
        4. accelerate -- a module that inline accelerates Python functions
"""

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

#---- testing ----#

def test():
    import unittest
    runner = unittest.TextTestRunner()
    runner.run(test_suite())
    return runner

def test_suite():
    import scipy_test
    # this isn't a perfect fix, but it will work for
    # most cases I think.
    this_mod = __import__(__name__)
    return scipy_test.harvest_test_suites(this_mod)

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
    """Match `data' to `pattern', with variable extraction.

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

def test():
    from scipy_test import module_test
    module_test(__name__,__file__)

def test_suite():
    from scipy_test import module_test_suite
    return module_test_suite(__name__,__file__)    
    
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

# If linker is 'gcc', this will convert it to 'g++'
# necessary to make sure stdc++ is linked in cross-platform way.
import distutils.sysconfig

old_init_posix = distutils.sysconfig._init_posix

def _init_posix():
    old_init_posix()
    ld = distutils.sysconfig._config_vars['LDSHARED']
    distutils.sysconfig._config_vars['LDSHARED'] = ld.replace('gcc','g++')

distutils.sysconfig._init_posix = _init_posix    
# end force g++


class CompileError(exceptions.Exception):
    pass
    
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
    
    compiler_name = choose_compiler(compiler_name)
    configure_sys_argv(compiler_name,temp_dir,build_dir)
    
    # the business end of the function
    try:
        if verbose == 1:
            print 'Compiling code...'
            
        # set compiler verboseness 2 or more makes it output results
        if verbose > 1:  verb = 1                
        else:            verb = 0
        
        t1 = time.time()        
        # add module to the needed source code files and build extension
        sources = kw.get('sources',[])
        kw['sources'] = [module_path] + sources        
        
        # ! This was fixed at beginning of file by using g++ on most 
        # !machines.  We'll have to check how to handle it on non-gcc machines        
        ## add module to the needed source code files and build extension
        ## FIX this is g++ specific. It probably should be fixed for other
        ## Unices/compilers.  Find a generic solution
        #if compiler_name != 'msvc':
        #    libraries = kw.get('libraries',[])
        #    kw['libraries'] = ['stdc++'] +  libraries        
        # !
        
        # SunOS specific
        # fix for issue with linking to libstdc++.a. see:
        # http://mail.python.org/pipermail/python-dev/2001-March/013510.html
        platform = sys.platform
        version = sys.version.lower()
        if platform[:5] == 'sunos' and version.find('gcc') != -1:
            extra_link_args = kw.get('extra_link_args',[])
            kw['extra_link_args'] = ['-mimpure-text'] +  extra_link_args
            
        ext = Extension(module_name, **kw)
        
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
    
def gcc_exists():
    """ Test to make sure gcc is found 
       
        Does this return correct value on win98???
    """
    result = 0
    try:
        w,r=os.popen4('gcc -v')
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
        result = not os.system('gcc -v')
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

def configure_temp_dir(temp_dir=None):
    if temp_dir is None:         
        temp_dir = tempfile.gettempdir()
    elif not os.path.exists(temp_dir) or not os.access(temp_dir,os.W_OK):
        print "warning: specified temp_dir '%s' does not exist or is " \
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
        print "warning: specified build_dir '%s' does not exist or is " \
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
    # the same as cygwin plus some additional parameters
    class Mingw32CCompiler (distutils.cygwinccompiler.CygwinCCompiler):
        """ A modified MingW32 compiler compatible with an MSVC built Python.
            
        """
    
        compiler_type = 'mingw32'
    
        def __init__ (self,
                      verbose=0,
                      dry_run=0,
                      force=0):
    
            distutils.cygwinccompiler.CygwinCCompiler.__init__ (self, verbose, 
                                                                dry_run, force)
            
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
            self.set_executables(compiler='g++ -mno-cygwin -O2 -w',
                                 compiler_so='g++ -mno-cygwin -mdll -O2 -w -Wstrict-prototypes',
                                 linker_exe='g++ -mno-cygwin',
                                 linker_so='%s -mno-cygwin -mdll -static %s' 
                                            % (self.linker, entry_point))
            
            # Maybe we should also append -mthreads, but then the finished
            # dlls need another dll (mingwm10.dll see Mingw32 docs)
            # (-mthreads: Support thread-safe exception handling on `Mingw32')       
            
            # no additional libraries needed 
            self.dll_libraries=[]
            
        # __init__ ()
    
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
        import lib2def as lib2def
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
        success = not os.system(cmd)
        # for now, fail silently
        if not success:
            print 'WARNING: failed to build import library for gcc. Linking will fail.'
        #if not success:
        #    msg = "Couldn't find import library, and failed to build it."
        #    raise DistutilsPlatformError, msg
    
def test():
    from scipy_test import module_test
    module_test(__name__,__file__)

def test_suite():
    from scipy_test import module_test_suite
    return module_test_suite(__name__,__file__)    




""" support code and other things needed to compile support
    for numeric expressions in python.
    
    There are two sets of support code, one with templated
    functions and one without.  This is because msvc cannot
    handle the templated functions.  We need the templated
    versions for more complex support of numeric arrays with
    blitz. 
"""

import base_info

from conversion_code import scalar_support_code
#from conversion_code import non_template_scalar_support_code

class scalar_info(base_info.base_info):
    _warnings = ['disable: 4275', 'disable: 4101']
    _headers = ['<complex>','<math.h>']
    def support_code(self):
        return [scalar_support_code]
        # REMOVED WHEN TEMPLATE CODE REMOVED
        #if self.compiler != 'msvc':
        #     # maybe this should only be for gcc...
        #    return [scalar_support_code,non_template_scalar_support_code]
        #else:
        #    return [non_template_scalar_support_code]
            
""" C/C++ code strings needed for converting most non-sequence
    Python variables:
        module_support_code -- several routines used by most other code 
                               conversion methods.  It holds the only
                               CXX dependent code in this file.  The CXX
                               stuff is used for exceptions
        file_convert_code
        instance_convert_code
        callable_convert_code
        module_convert_code
        
        scalar_convert_code
        non_template_scalar_support_code               
            Scalar conversion covers int, float, double, complex,
            and double complex.  While Python doesn't support all these,
            Numeric does and so all of them are made available.
            Python longs are currently converted to C ints.  Any
            better way to handle this?
"""

import base_info

#############################################################
# Basic module support code
#############################################################

module_support_code = \
"""

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
  PyErr_SetString(exc, msg);
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

#############################################################
# File conversion support code
#############################################################

file_convert_code =  \
"""

class file_handler
{
public:
    FILE* convert_to_file(PyObject* py_obj, const char* name)
    {
        if (!py_obj || !PyFile_Check(py_obj))
            handle_conversion_error(py_obj,"file", name);
    
        // Cleanup code should call DECREF
        Py_INCREF(py_obj);
        return PyFile_AsFile(py_obj);
    }
    
    FILE* py_to_file(PyObject* py_obj, const char* name)
    {
        if (!py_obj || !PyFile_Check(py_obj))
            handle_bad_type(py_obj,"file", name);
    
        // Cleanup code should call DECREF
        Py_INCREF(py_obj);
        return PyFile_AsFile(py_obj);
    }
};

file_handler x__file_handler = file_handler();
#define convert_to_file(py_obj,name) x__file_handler.convert_to_file(py_obj,name)
#define py_to_file(py_obj,name) x__file_handler.py_to_file(py_obj,name)

PyObject* file_to_py(FILE* file, char* name, char* mode)
{
    PyObject* py_obj = NULL;
    //extern int fclose(FILE *);
    return (PyObject*) PyFile_FromFile(file, name, mode, fclose);
}

"""


#############################################################
# Instance conversion code
#############################################################

instance_convert_code = \
"""

class instance_handler
{
public:
    PyObject* convert_to_instance(PyObject* py_obj, const char* name)
    {
        if (!py_obj || !PyInstance_Check(py_obj))
            handle_conversion_error(py_obj,"instance", name);
    
        // Should I INCREF???
        // Py_INCREF(py_obj);
        // just return the raw python pointer.
        return py_obj;
    }
    
    PyObject* py_to_instance(PyObject* py_obj, const char* name)
    {
        if (!py_obj || !PyInstance_Check(py_obj))
            handle_bad_type(py_obj,"instance", name);
    
        // Should I INCREF???
        // Py_INCREF(py_obj);
        // just return the raw python pointer.
        return py_obj;
    }
};

instance_handler x__instance_handler = instance_handler();
#define convert_to_instance(py_obj,name) x__instance_handler.convert_to_instance(py_obj,name)
#define py_to_instance(py_obj,name) x__instance_handler.py_to_instance(py_obj,name)

PyObject* instance_to_py(PyObject* instance)
{
    // Don't think I need to do anything...
    return (PyObject*) instance;
}

"""

#############################################################
# Callable conversion code
#############################################################

callable_convert_code = \
"""

class callable_handler
{
public:    
    PyObject* convert_to_callable(PyObject* py_obj, const char* name)
    {
        if (!py_obj || !PyCallable_Check(py_obj))
            handle_conversion_error(py_obj,"callable", name);
    
        // Should I INCREF???
        // Py_INCREF(py_obj);
        // just return the raw python pointer.
        return py_obj;
    }
    
    PyObject* py_to_callable(PyObject* py_obj, const char* name)
    {
        if (!py_obj || !PyCallable_Check(py_obj))
            handle_bad_type(py_obj,"callable", name);
    
        // Should I INCREF???
        // Py_INCREF(py_obj);
        // just return the raw python pointer.
        return py_obj;
    }
};

callable_handler x__callable_handler = callable_handler();
#define convert_to_callable(py_obj,name) x__callable_handler.convert_to_callable(py_obj,name)
#define py_to_callable(py_obj,name) x__callable_handler.py_to_callable(py_obj,name)

PyObject* callable_to_py(PyObject* callable)
{
    // Don't think I need to do anything...
    return (PyObject*) callable;
}

"""

#############################################################
# Module conversion code
#############################################################

module_convert_code = \
"""
class module_handler
{
public:
    PyObject* convert_to_module(PyObject* py_obj, const char* name)
    {
        if (!py_obj || !PyModule_Check(py_obj))
            handle_conversion_error(py_obj,"module", name);
    
        // Should I INCREF???
        // Py_INCREF(py_obj);
        // just return the raw python pointer.
        return py_obj;
    }
    
    PyObject* py_to_module(PyObject* py_obj, const char* name)
    {
        if (!py_obj || !PyModule_Check(py_obj))
            handle_bad_type(py_obj,"module", name);
    
        // Should I INCREF???
        // Py_INCREF(py_obj);
        // just return the raw python pointer.
        return py_obj;
    }
};

module_handler x__module_handler = module_handler();
#define convert_to_module(py_obj,name) x__module_handler.convert_to_module(py_obj,name)
#define py_to_module(py_obj,name) x__module_handler.py_to_module(py_obj,name)

PyObject* module_to_py(PyObject* module)
{
    // Don't think I need to do anything...
    return (PyObject*) module;
}

"""

#############################################################
# Scalar conversion code
#############################################################

# These non-templated version is now used for most scalar conversions.
scalar_support_code = \
"""

class scalar_handler
{
public:    
    int convert_to_int(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyInt_Check(py_obj))
            handle_conversion_error(py_obj,"int", name);
        return (int) PyInt_AsLong(py_obj);
    }
    long convert_to_long(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyLong_Check(py_obj))
            handle_conversion_error(py_obj,"long", name);
        return (long) PyLong_AsLong(py_obj);
    }

    double convert_to_float(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyFloat_Check(py_obj))
            handle_conversion_error(py_obj,"float", name);
        return PyFloat_AsDouble(py_obj);
    }

    std::complex<double> convert_to_complex(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyComplex_Check(py_obj))
            handle_conversion_error(py_obj,"complex", name);
        return std::complex<double>(PyComplex_RealAsDouble(py_obj),
                                    PyComplex_ImagAsDouble(py_obj));    
    }

    int py_to_int(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyInt_Check(py_obj))
            handle_bad_type(py_obj,"int", name);
        return (int) PyInt_AsLong(py_obj);
    }
    
    long py_to_long(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyLong_Check(py_obj))
            handle_bad_type(py_obj,"long", name);
        return (long) PyLong_AsLong(py_obj);
    }
    
    double py_to_float(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyFloat_Check(py_obj))
            handle_bad_type(py_obj,"float", name);
        return PyFloat_AsDouble(py_obj);
    }
    
    std::complex<double> py_to_complex(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyComplex_Check(py_obj))
            handle_bad_type(py_obj,"complex", name);
        return std::complex<double>(PyComplex_RealAsDouble(py_obj),
                                    PyComplex_ImagAsDouble(py_obj));    
    }

};

scalar_handler x__scalar_handler = scalar_handler();
#define convert_to_int(py_obj,name) x__scalar_handler.convert_to_int(py_obj,name)
#define py_to_int(py_obj,name) x__scalar_handler.py_to_int(py_obj,name)

#define convert_to_long(py_obj,name) x__scalar_handler.convert_to_long(py_obj,name)
#define py_to_long(py_obj,name) x__scalar_handler.py_to_long(py_obj,name)

#define convert_to_float(py_obj,name) x__scalar_handler.convert_to_float(py_obj,name)
#define py_to_float(py_obj,name) x__scalar_handler.py_to_float(py_obj,name)

#define convert_to_complex(py_obj,name) x__scalar_handler.convert_to_complex(py_obj,name)
#define py_to_complex(py_obj,name) x__scalar_handler.py_to_complex(py_obj,name)

"""    


import wx_info
import base_info
from base_spec import base_converter
from types import *
import os

wx_support_template = \
"""
static %(wx_class)s* convert_to_%(wx_class)s(PyObject* py_obj,char* name)
{
    %(wx_class)s *wx_ptr;
    
    // work on this error reporting...
    if (SWIG_GetPtrObj(py_obj,(void **) &wx_ptr,"_%(wx_class)s_p"))
        handle_conversion_error(py_obj,"%(wx_class)s", name);
    return wx_ptr;
}    

static %(wx_class)s* py_to_%(wx_class)s(PyObject* py_obj,char* name)
{
    %(wx_class)s *wx_ptr;
    
    // work on this error reporting...
    if (SWIG_GetPtrObj(py_obj,(void **) &wx_ptr,"_%(wx_class)s_p"))
        handle_bad_type(py_obj,"%(wx_class)s", name);
    return wx_ptr;
}    
"""        

class wx_converter(base_converter):
    _build_information = [wx_info.wx_info()]
    def __init__(self,class_name=None):
        self.type_name = 'unkown wx_object'
        if class_name:
            # customize support_code for whatever type I was handed.
            vals = {'wx_class': class_name}
            specialized_support = wx_support_template % vals
            custom = base_info.base_info()
            custom._support_code = [specialized_support]
            self._build_information = self._build_information + [custom]
            self.type_name = class_name

    def type_match(self,value):
        try:
            class_name = value.this.split('_')[-2]
            if class_name[:2] == 'wx':
                return 1
        except AttributeError:
            pass
        return 0
            
    def type_spec(self,name,value):
        # factory
        class_name = value.this.split('_')[-2]
        new_spec = self.__class__(class_name)
        new_spec.name = name        
        return new_spec
    def declaration_code(self,inline=0):
        type = self.type_name
        name = self.name
        var_name = self.retrieve_py_variable(inline)
        template = '%(type)s *%(name)s = '\
                   'convert_to_%(type)s(%(var_name)s,"%(name)s");\n'
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

"""
# this should only be enabled on machines with access to a display device
# It'll cause problems otherwise.
def test():
    from scipy_test import module_test
    module_test(__name__,__file__)

def test_suite():
    from scipy_test import module_test_suite
    return module_test_suite(__name__,__file__)    
"""        
#!/usr/bin/env python
import os,sys
from scipy_distutils.core import setup
from scipy_distutils.misc_util import get_path, merge_config_dicts
from scipy_distutils.misc_util import package_config

# Enought changes to bump the number.  We need a global method for
# versioning
version = "0.2.3"
   
def stand_alone_package(with_dependencies = 0):
    path = get_path(__name__)
    old_path = os.getcwd()
    os.chdir(path)
    try:
        primary =     ['weave']
        if with_dependencies:
            dependencies= ['scipy_distutils', 'scipy_test']       
        else:
            dependencies = []    
        
        print 'dep:', dependencies
        config_dict = package_config(primary,dependencies)

        setup (name = "weave",
               version = version,
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
    

module_header = \
"""    
// blitz must be first, or you get have issues with isnan defintion.
#include <blitz/array.h> 

#include "Python.h" 
#include "Numeric/arrayobject.h" 

// Use Exception stuff from SCXX
#include "PWOBase.h" 

#include <stdio.h> 
#include <math.h> 
#include <complex>

static PyArrayObject* obj_to_numpy(PyObject* py_obj, char* name, 
                                  int Ndims, int numeric_type )
{
    PyArrayObject* arr_obj = NULL;

    // Make sure input is an array.
    if (!PyArray_Check(py_obj))
        throw_error(PyExc_TypeError,"Input array *name* must be an array.");

    arr_obj = (PyArrayObject*) py_obj;
    
    // Make sure input has correct numeric type.
    if (arr_obj->descr->type_num != numeric_type)
    {
        // This should be more explicit:
        // Put the desired and actual type in the message.
        // printf("%d,%d",arr_obj->descr->type_num,numeric_type);
        throw_error(PyExc_TypeError,
                    "Input array *name* is the wrong numeric type.");
    }
    
    // Make sure input has correct rank (defined as number of dimensions).
    // Currently, all arrays must have the same shape.
    // Broadcasting is not supported.
    // ...
    if (arr_obj->nd != Ndims)
    {
        // This should be more explicit:
        // Put the desired and actual dimensionality in message.
        throw_error(PyExc_TypeError,
                    "Input array *name* has wrong number of dimensions.");
    }    
    // check the size of arrays.  Acutally, the size of the "views" really
    // needs checking -- not the arrays.
    // ...
    
    // Any need to deal with INC/DEC REFs?
    Py_INCREF(py_obj);
    return arr_obj;
}

// simple meta-program templates to specify python typecodes
// for each of the numeric types.
template<class T>
class py_type{public: enum {code = 100};};
class py_type<char>{public: enum {code = PyArray_CHAR};};
class py_type<unsigned char>{public: enum { code = PyArray_UBYTE};};
class py_type<short>{public:  enum { code = PyArray_SHORT};};
class py_type<int>{public: enum { code = PyArray_INT};};
class py_type<long>{public: enum { code = PyArray_LONG};};
class py_type<float>{public: enum { code = PyArray_FLOAT};};
class py_type<double>{public: enum { code = PyArray_DOUBLE};};
class py_type<complex<float> >{public: enum { code = PyArray_CFLOAT};};
class py_type<complex<double> >{public: enum { code = PyArray_CDOUBLE};};

template<class T, int N>
static blitz::Array<T,N> py_to_blitz(PyObject* py_obj,char* name)
{

    PyArrayObject* arr_obj = obj_to_numpy(py_obj,name,N,py_type<T>::code);
    
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

template<class T> 
static T py_to_scalar(PyObject* py_obj,char* name)
{
    //never used.
    return (T) 0;
}
template<>
static int py_to_scalar<int>(PyObject* py_obj,char* name)
{
    return (int) PyLong_AsLong(py_obj);
}

template<>
static long py_to_scalar<long>(PyObject* py_obj,char* name)
{
    return (long) PyLong_AsLong(py_obj);
}
template<> 
static float py_to_scalar<float>(PyObject* py_obj,char* name)
{
    return (float) PyFloat_AsDouble(py_obj);
}
template<> 
static double py_to_scalar<double>(PyObject* py_obj,char* name)
{
    return PyFloat_AsDouble(py_obj);
}

// complex not checked.
template<> 
static std::complex<float> py_to_scalar<std::complex<float> >(PyObject* py_obj,
                                                              char* name)
{
    return std::complex<float>((float) PyComplex_RealAsDouble(py_obj),
                               (float) PyComplex_RealAsDouble(py_obj));    
}
template<> 
static std::complex<double> py_to_scalar<std::complex<double> >(
                                            PyObject* py_obj,char* name)
{
    return std::complex<double>(PyComplex_RealAsDouble(py_obj),
                                PyComplex_RealAsDouble(py_obj));    
}
"""    
import base_info, common_info

string_support_code = \
"""
class string_handler
{
public:
    static Py::String convert_to_string(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyString_Check(py_obj))
            handle_conversion_error(py_obj,"string", name);
        return Py::String(py_obj);
    }
    Py::String py_to_string(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyString_Check(py_obj))
            handle_bad_type(py_obj,"string", name);
        return Py::String(py_obj);
    }
};

string_handler x__string_handler = string_handler();

#define convert_to_string(py_obj,name) x__string_handler.convert_to_string(py_obj,name)
#define py_to_string(py_obj,name) x__string_handler.py_to_string(py_obj,name)
"""

list_support_code = \
"""

class list_handler
{
public:
    Py::List convert_to_list(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyList_Check(py_obj))
            handle_conversion_error(py_obj,"list", name);
        return Py::List(py_obj);
    }
    Py::List py_to_list(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyList_Check(py_obj))
            handle_bad_type(py_obj,"list", name);
        return Py::List(py_obj);
    }
};

list_handler x__list_handler = list_handler();
#define convert_to_list(py_obj,name) x__list_handler.convert_to_list(py_obj,name)
#define py_to_list(py_obj,name) x__list_handler.py_to_list(py_obj,name)

"""

dict_support_code = \
"""
class dict_handler
{
public:
    Py::Dict convert_to_dict(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyDict_Check(py_obj))
            handle_conversion_error(py_obj,"dict", name);
        return Py::Dict(py_obj);
    }
    Py::Dict py_to_dict(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyDict_Check(py_obj))
            handle_bad_type(py_obj,"dict", name);
        return Py::Dict(py_obj);
    }
};

dict_handler x__dict_handler = dict_handler();
#define convert_to_dict(py_obj,name) x__dict_handler.convert_to_dict(py_obj,name)
#define py_to_dict(py_obj,name) x__dict_handler.py_to_dict(py_obj,name)

"""

tuple_support_code = \
"""
class tuple_handler
{
public:
    Py::Tuple convert_to_tuple(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyTuple_Check(py_obj))
            handle_conversion_error(py_obj,"tuple", name);
        return Py::Tuple(py_obj);
    }
    Py::Tuple py_to_tuple(PyObject* py_obj,const char* name)
    {
        if (!py_obj || !PyTuple_Check(py_obj))
            handle_bad_type(py_obj,"tuple", name);
        return Py::Tuple(py_obj);
    }
};

tuple_handler x__tuple_handler = tuple_handler();
#define convert_to_tuple(py_obj,name) x__tuple_handler.convert_to_tuple(py_obj,name)
#define py_to_tuple(py_obj,name) x__tuple_handler.py_to_tuple(py_obj,name)
"""

import os, cxx_info
local_dir,junk = os.path.split(os.path.abspath(cxx_info.__file__))   
cxx_dir = os.path.join(local_dir,'CXX')

class cxx_info(base_info.base_info):
    _headers = ['"CXX/Objects.hxx"','"CXX/Extensions.hxx"','<algorithm>']
    _include_dirs = [local_dir]

    # should these be built to a library??
    _sources = [os.path.join(cxx_dir,'cxxsupport.cxx'),
                os.path.join(cxx_dir,'cxx_extensions.cxx'),
                os.path.join(cxx_dir,'IndirectPythonInterface.cxx'),
                os.path.join(cxx_dir,'cxxextensions.c')]
    _support_code = [string_support_code,list_support_code, dict_support_code,
                     tuple_support_code]

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

from types import FunctionType,IntType,FloatType,StringType,TypeType
import inspect
import md5
import weave
import bytecodecompiler

def CStr(s):
    "Hacky way to get legal C string from Python string"
    if s == None: return '""'
    assert type(s) == StringType,"Only None and string allowed"
    r = repr('"'+s) # Better for embedded quotes
    return '"'+r[2:-1]+'"'

class Basic(bytecodecompiler.Type_Descriptor):
    def check(self,s):
        return "%s(%s)"%(self.checker,s)
    def inbound(self,s):
        return "%s(%s)"%(self.inbounder,s)
    def outbound(self,s):
        return "%s(%s)"%(self.outbounder,s)

class Basic_Number(Basic):
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

import Numeric

class Vector(bytecodecompiler.Type_Descriptor):
    cxxtype = 'PyArrayObject*'
    prerequisites = bytecodecompiler.Type_Descriptor.prerequisites+\
                   ['#include "Numeric/arrayobject.h"',
                    'static PyObject* PyArray_AsPyObject(PyArrayObject* A) { PyObject* X = '
                    'reinterpret_cast<PyObject*>(A);'
                    'std::cerr << "Here in cast" << std::endl;'
                    'Py_XINCREF(X); return X;}']
    dims = 1
    def check(self,s):
        return "PyArray_Check(%s) /* && dims==%d && typecode==%s */"%(s,self.dims,self.typecode)
    def inbound(self,s):
        return "(PyArrayObject*)(%s)"%s
    def outbound(self,s):
        return "(PyObject*)(%s)"%s

class IntegerVector(Vector):
    typecode = 'l'

typedefs = {
    IntType: Integer(),
    FloatType: Double(),
    StringType: String(),
    (Numeric.ArrayType,1,'l'): IntegerVector(),
    }


##################################################################
#                      FUNCTION LOOKUP_TYPE                      #
##################################################################
def lookup_type(x):
    T = type(x)
    try:
        return typedefs[T]
    except:
        return typedefs[(T,len(x.shape),x.typecode())]

##################################################################
#                        class ACCELERATE                        #
##################################################################
class accelerate:
    
    def __init__(self, function, *args, **kw):
        assert type(function) == FunctionType
        self.function = function
        self.module = inspect.getmodule(function)
        if self.module == None:
            import __main__
            self.module = __main__
        self.__call_map = {}
        return

    def __call__(self,*args):
        # Figure out type info -- Do as tuple so its hashable
        signature = tuple( map(lookup_type,args) )

        # If we know the function, call it
        try:
            return self.__call_map[signature](*args)
        except:
            fast = self.singleton(signature)
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
            accelerated_module = __import__(self.module.__name__+'_weave')
            fast = getattr(accelerated_module,identifier)
            return fast
        except:
            accelerated_module = None

        P = self.accelerate(signature,identifier)

        E = weave.ext_tools.ext_module(self.module.__name__+'_weave')
        E.add_function(P)
        E.generate_file()
        weave.build_tools.build_extension(self.module.__name__+'_weave.cpp',verbose=2)

        if accelerated_module:
            accelerated_module = reload(accelerated_module)
        else:
            accelerated_module = __import__(self.module.__name__+'_weave')

        fast = getattr(accelerated_module,identifier)
        return fast

    def identifier(self,signature):
        # Build an MD5 checksum
        f = self.function
        co = f.func_code
        identifier = str(signature)+\
                     str(co.co_consts)+\
                     str(co.co_varnames)+\
                     co.co_code
        return 'F'+md5.md5(identifier).hexdigest()
        
    def accelerate(self,signature,identifier):
        P = Python2CXX(self.function,signature,name=identifier)
        return P

    def code(self,*args):
        signature = tuple( map(lookup_type,args) )
        ident = self.function.__name__
        return self.accelerate(signature,ident).function_code()
        

##################################################################
#                        CLASS PYTHON2CXX                        #
##################################################################
class Python2CXX(bytecodecompiler.CXXCoder):
    def typedef_by_value(self,v):
        T = lookup_type(v)
        if T not in self.used: self.used.append(T)
        return T

    def __init__(self,f,signature,name=None):
        # Make sure function is a function
        import types
        assert type(f) == FunctionType
        # and check the input type signature
        assert reduce(lambda x,y: x and y,
                      map(lambda x: isinstance(x,bytecodecompiler.Type_Descriptor),
                          signature),
                      1),'%s not all type objects'%signature
        self.arg_specs = []
        self.customize = weave.base_info.custom_info()

        bytecodecompiler.CXXCoder.__init__(self,f,signature,name)
        return

    def function_code(self):
        return self.wrapped_code()

    def python_function_definition_code(self):
        return '{ "%s", wrapper_%s, METH_VARARGS, %s },\n'%(
            self.name,
            self.name,
            CStr(self.function.__doc__))

from Numeric import *

# The following try/except so that non-SciPy users can still use blitz
try:
    from fastumath import *
except:
    pass # fastumath not available    

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
    
def test():
    from scipy_test import module_test
    module_test(__name__,__file__)

def test_suite():
    from scipy_test import module_test_suite
    return module_test_suite(__name__,__file__)    
    
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

class info_list(UserList.UserList):
    def get_unique_values(self,attribute):
        all_values = []        
        for info in self:
            vals = eval('info.'+attribute+'()')
            all_values.extend(vals)
        return unique_values(all_values)
    
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


import base_info

import os, swig_info
local_dir,junk = os.path.split(os.path.abspath(swig_info.__file__))   
f = open(os.path.join(local_dir,'swig','swigptr.c'))
swig_support_code = f.read()
f.close()

class swig_info(base_info.base_info):
    _support_code = [swig_support_code]
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
#                    CLASS CXXTYPEDESCRIPTION                    #
##################################################################
class Type_Descriptor:
    prerequisites = []
    def __repr__(self):
        return self.__module__+'.'+self.__class__.__name__


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
        if arg == None: arg = ''
        s += '%3d] %20s %5s : %s\n'%(pc,name,arg,source)
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
        if argument == None:
            return apply(method,(pc,))
        else:
            return apply(method,(pc,argument,))

    def evaluate(self, pc,code):
        next, opcode,argument = self.fetch(pc,code)
        goto = self.execute(next,opcode,argument)
        if goto == -1:
            return None # Must be done
        elif goto == None:
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
        if name == None: name = function.func_name
        self.name = name
        self.function = function
        self.signature = signature
        self.codeobject = function.func_code
        self.__uid = 0 # Builds temps
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
        arglen = len(self.signature)
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
        pc = 0
        while pc != None:
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
            print T.prerequisites
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

        # Add in non-argument temporaries
        # Assuming first argcount locals are positional args
        for i in range(self.codeobject.co_argcount,
                       self.codeobject.co_nlocals):
            t = self.types[i]
            descriptor = typedefs[t]
            code += '%s %s;\n'%(
                descriptor.cxxtype,
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

            code += '  if ( !%s ) {\n'% \
                    T.check('py_'+self.codeobject.co_varnames[i])
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
            result = self.rtype.outbound('_result')
            code += '  return %s;\n'%result
        code += '}\n'
        return code


    ##################################################################
    #                          MEMBER EMIT                           #
    ##################################################################
    def emit(self,s):
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
        del self.stack[-1]
        t = self.types[-1]
        del self.types[-1]
        return v,t

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
    #                          MEMBER BINOP                          #
    ##################################################################
    def binop(self,pc,symbol):
        v2,t2 = self.pop()
        v1,t1 = self.pop()

        if t1 == t2:
            rhs,rhs_type = t1.binop(symbol,v1,v2)
        else:
            raise NotImplementedError,'mixed types'
        
        lhs = self.unique()
        self.emit('%s %s = %s;\n'%(
            rhs_type.cxxtype,
            lhs,
            rhs))
        self.push(lhs,rhs_type)
        return        

    ##################################################################
    #                       MEMBER BINARY_XXX                        #
    ##################################################################
    def BINARY_ADD(self,pc):
        return self.binop(pc,'+')
    def BINARY_SUBTRACT(self,pc):
        return self.binop(pc,'-')
    def BINARY_MULTIPLY(self,pc):
        return self.binop(pc,'*')
    def BINARY_DIVIDE(self,pc):
        return self.binop(pc,'/')
    def BINARY_MODULO(self,pc):
        return self.binop(pc,'%')
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
        self.emit('PyObject* %s = %s;'%(py, t.outbound(v)))
        self.emit('PyFile_WriteObject(%s,%s,Py_PRINT_RAW);'%(
            py,w))
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

        # Fetch a None is just skipped
        if t == NoneType:
            self.push('<bogus>',t) 
            return

        self.emit_value(k)
        return


    ##################################################################
    #                        MEMBER LOAD_FAST                        #
    ##################################################################
    def LOAD_FAST(self,pc,var_num):
        v = self.stack[var_num]
        t = self.types[var_num]
        self.push(v,t)
        return

    ##################################################################
    #                       MEMBER LOAD_GLOBAL                       #
    ##################################################################
    def LOAD_GLOBAL(self,pc,var_num):
        # Figure out the name and load it
        try:
            F = self.function.func_globals[self.codeobject.co_names[var_num]]
        except:
            F = getattr(__builtins__,self.codeobject.co_names[var_num])

        # For functions, we see if we know about this function
        if callable(F):
            assert functiondefs.has_key(F),"Function %s is known"%F
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

    ##################################################################
    #                       MEMBER STORE_FAST                        #
    ##################################################################
    def STORE_FAST(self,pc,var_num):

        v,t = self.pop()

        save = self.stack[var_num]
        saveT = self.types[var_num]

        # See if type is same....
        # Note that None means no assignment made yet
        if saveT == None or t == saveT:
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
        self.emit('PyObject* %s = %s;'%(
            py,
            descriptor.outbound%v))
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
        descriptor = functiondefs[f]
        #self.prerequisites += descriptor['prerequisite']+'\n'
        
        # Look through descriptors for a match
        for inputs,outputs,format in descriptor:
            if inputs == types:
                break
        else:
            raise TypeError,f

        # Build a rhs
        rhs = format%string.join(args,',')

        # Build a statement
        assert len(outputs) == 1,"Single valued return"
        assert typedefs.has_key(outputs[0]),"Know about type %s"%outputs[0]
        description = typedefs[outputs[0]]
        temp = self.unique()
        self.emit('%s %s = %s;\n'%(
            description.cxxtype,
            temp,
            rhs))

        self.push(temp,outputs[0])
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
            raise ValueError,'multiple returns'
        self.rtype = t
        if t == NoneType:
            self.emit('return;')
        else:
            self.emit('return %s;'%v)
        return -1


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
            slice_vars['end'] = '_N%s[%d]%s-1' % (slice_vars['var'],position,end)
        
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

def test():
    import slice_handler
    from scipy_test import module_test
    module_test(slice_handler.__name__,slice_handler.__file__)

def test_suite():
    import slice_handler
    from scipy_test import module_test_suite
    return module_test_suite(slice_handler.__name__,slice_handler.__file__)

if __name__ == "__main__":    
    test()
"""
    build_info holds classes that define the information
    needed for building C++ extension modules for Python that
    handle different data types.  The information includes
    such as include files, libraries, and even code snippets.
       
    array_info -- for building functions that use Python
                  Numeric arrays.
"""

import base_info

blitz_support_code =  \
"""

// This should be declared only if they are used by some function
// to keep from generating needless warnings. for now, we'll always
// declare them.

int _beg = blitz::fromStart;
int _end = blitz::toEnd;
blitz::Range _all = blitz::Range::all();

// simple meta-program templates to specify python typecodes
// for each of the numeric types.
template<class T>
class py_type{public: enum {code = 100};};
class py_type<char>{public: enum {code = PyArray_CHAR};};
class py_type<unsigned char>{public: enum { code = PyArray_UBYTE};};
class py_type<short>{public:  enum { code = PyArray_SHORT};};
class py_type<int>{public: enum { code = PyArray_LONG};};// PyArray_INT has troubles;
class py_type<long>{public: enum { code = PyArray_LONG};};
class py_type<float>{public: enum { code = PyArray_FLOAT};};
class py_type<double>{public: enum { code = PyArray_DOUBLE};};
class py_type<std::complex<float> >{public: enum { code = PyArray_CFLOAT};};
class py_type<std::complex<double> >{public: enum { code = PyArray_CDOUBLE};};

template<class T, int N>
static blitz::Array<T,N> convert_to_blitz(PyArrayObject* arr_obj,const char* name)
{

    //This is now handled externally (for now) to deal with exception/Abort issue
    //PyArrayObject* arr_obj = convert_to_numpy(py_obj,name);
    //conversion_numpy_check_size(arr_obj,N,name);
    //conversion_numpy_check_type(arr_obj,py_type<T>::code,name);
    
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
    //This is now handled externally (for now) to deal with exception/Abort issue
    //PyArrayObject* arr_obj = py_to_numpy(py_obj,name);
    //numpy_check_size(arr_obj,N,name);
    //numpy_check_type(arr_obj,py_type<T>::code,name);
    
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

# this code will not build with msvc...
# This is only used for blitz stuff now.  The non-templated
# version, defined further down, is now used for most code.
scalar_support_code = \
"""
// conversion routines

template<class T> 
static T convert_to_scalar(PyObject* py_obj,const char* name)
{
    //never used.
    return (T) 0;
}
template<>
static int convert_to_scalar<int>(PyObject* py_obj,const char* name)
{
    if (!py_obj || !PyInt_Check(py_obj))
        handle_conversion_error(py_obj,"int", name);
    return (int) PyInt_AsLong(py_obj);
}

template<>
static long convert_to_scalar<long>(PyObject* py_obj,const char* name)
{
    if (!py_obj || !PyLong_Check(py_obj))
        handle_conversion_error(py_obj,"long", name);
    return (long) PyLong_AsLong(py_obj);
}

template<> 
static double convert_to_scalar<double>(PyObject* py_obj,const char* name)
{
    if (!py_obj || !PyFloat_Check(py_obj))
        handle_conversion_error(py_obj,"float", name);
    return PyFloat_AsDouble(py_obj);
}

template<> 
static float convert_to_scalar<float>(PyObject* py_obj,const char* name)
{
    return (float) convert_to_scalar<double>(py_obj,name);
}

// complex not checked.
template<> 
static std::complex<float> convert_to_scalar<std::complex<float> >(PyObject* py_obj,
                                                              const char* name)
{
    if (!py_obj || !PyComplex_Check(py_obj))
        handle_conversion_error(py_obj,"complex", name);
    return std::complex<float>((float) PyComplex_RealAsDouble(py_obj),
                               (float) PyComplex_ImagAsDouble(py_obj));    
}
template<> 
static std::complex<double> convert_to_scalar<std::complex<double> >(
                                            PyObject* py_obj,const char* name)
{
    if (!py_obj || !PyComplex_Check(py_obj))
        handle_conversion_error(py_obj,"complex", name);
    return std::complex<double>(PyComplex_RealAsDouble(py_obj),
                                PyComplex_ImagAsDouble(py_obj));    
}

/////////////////////////////////
// standard translation routines

template<class T> 
static T py_to_scalar(PyObject* py_obj,const char* name)
{
    //never used.
    return (T) 0;
}
template<>
static int py_to_scalar<int>(PyObject* py_obj,const char* name)
{
    if (!py_obj || !PyInt_Check(py_obj))
        handle_bad_type(py_obj,"int", name);
    return (int) PyInt_AsLong(py_obj);
}

template<>
static long py_to_scalar<long>(PyObject* py_obj,const char* name)
{
    if (!py_obj || !PyLong_Check(py_obj))
        handle_bad_type(py_obj,"long", name);
    return (long) PyLong_AsLong(py_obj);
}

template<> 
static double py_to_scalar<double>(PyObject* py_obj,const char* name)
{
    if (!py_obj || !PyFloat_Check(py_obj))
        handle_bad_type(py_obj,"float", name);
    return PyFloat_AsDouble(py_obj);
}

template<> 
static float py_to_scalar<float>(PyObject* py_obj,const char* name)
{
    return (float) py_to_scalar<double>(py_obj,name);
}

// complex not checked.
template<> 
static std::complex<float> py_to_scalar<std::complex<float> >(PyObject* py_obj,
                                                              const char* name)
{
    if (!py_obj || !PyComplex_Check(py_obj))
        handle_bad_type(py_obj,"complex", name);
    return std::complex<float>((float) PyComplex_RealAsDouble(py_obj),
                               (float) PyComplex_ImagAsDouble(py_obj));    
}
template<> 
static std::complex<double> py_to_scalar<std::complex<double> >(
                                            PyObject* py_obj,const char* name)
{
    if (!py_obj || !PyComplex_Check(py_obj))
        handle_bad_type(py_obj,"complex", name);
    return std::complex<double>(PyComplex_RealAsDouble(py_obj),
                                PyComplex_ImagAsDouble(py_obj));    
}
"""    

import standard_array_info
import os, blitz_info
local_dir,junk = os.path.split(os.path.abspath(blitz_info.__file__))   
blitz_dir = os.path.join(local_dir,'blitz-20001213')

class array_info(base_info.base_info):
    _include_dirs = [blitz_dir]
    _headers = ['"blitz/array.h"','"Numeric/arrayobject.h"','<complex>','<math.h>']
    
    _support_code = [standard_array_info.array_convert_code,
                     standard_array_info.type_check_code,
                     standard_array_info.size_check_code,
                     scalar_support_code,
                     blitz_support_code,
                    ]
    _module_init_code = [standard_array_info.numeric_init_code]    
    
    # throw error if trying to use msvc compiler
    
    def check_compiler(self,compiler):        
        msvc_msg = 'Unfortunately, the blitz arrays used to support numeric' \
                   ' arrays will not compile with MSVC.' \
                   '  Please try using mingw32 (www.mingw.org).'
        if compiler == 'msvc':
            return ValueError, self.msvc_msg        
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

        declare_return = 'PyObject *return_val = NULL;\n' \
                         'int exception_occured = 0;\n' \
                         'PyObject *py_local_dict = NULL;\n'
        arg_string_list = self.arg_specs.variable_as_strings() + ['"local_dict"']
        arg_strings = join(arg_string_list,',')
        if arg_strings: arg_strings += ','
        declare_kwlist = 'static char *kwlist[] = {%s NULL};\n' % arg_strings

        py_objects = join(self.arg_specs.py_pointers(),', ')
        if py_objects:
            declare_py_objects = 'PyObject ' + py_objects +';\n'
        else:
            declare_py_objects = ''
            
        py_vars = join(self.arg_specs.py_variables(),' = ')
        if py_vars:
            init_values = py_vars + ' = NULL;\n\n'
        else:
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
        decl_code = indent(self.arg_declaration_code(),4)
        cleanup_code = indent(self.arg_cleanup_code(),4)
        function_code = indent(self.code_block,4)
        local_dict_code = indent(self.arg_local_dict_code(),4)

        dict_code = "if(py_local_dict)                                  \n"   \
                    "{                                                  \n"   \
                    "    Py::Dict local_dict = Py::Dict(py_local_dict); \n" + \
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
                      "    return_val =  Py::Null();    \n"   \
                      "    exception_occured = 1;       \n"   \
                      "}                                \n"

        return_code = "    /*cleanup code*/                     \n" + \
                           cleanup_code                             + \
                      "    if(!return_val && !exception_occured)\n"   \
                      "    {\n                                  \n"   \
                      "        Py_INCREF(Py_None);              \n"   \
                      "        return_val = Py_None;            \n"   \
                      "    }\n                                  \n"   \
                      "    return return_val;           \n"           \
                      "}                                \n"

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
        
            
import base_info, common_info, cxx_info, scalar_info

class ext_module:
    def __init__(self,name,compiler=''):
        standard_info = [common_info.basic_module_info(),
                         common_info.file_info(),  
                         common_info.instance_info(),  
                         common_info.callable_info(),  
                         common_info.module_info(),  
                         cxx_info.cxx_info(),
                         scalar_info.scalar_info()]
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
        #for i in self.arg_specs()
        #    i.set_compiler(compiler)
        for i in self.build_information():
            i.set_compiler(compiler)    
        for i in self.functions:
            i.set_compiler(compiler)
        self.compiler = compiler    
        
    def compile(self,location='.',compiler=None, verbose = 0, **kw):
        
        if compiler is not None:
            self.compiler = compiler
        # hmm.  Is there a cleaner way to do this?  Seems like
        # choosing the compiler spagettis around a little.
        compiler = build_tools.choose_compiler(self.compiler)    
        self.set_compiler(compiler)
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
        kw['define_macros'] = kw.get('define_macros',[]) + info.define_macros()
        kw['include_dirs'] = kw.get('include_dirs',[]) + info.include_dirs()
        kw['libraries'] = kw.get('libraries',[]) + info.libraries()
        kw['library_dirs'] = kw.get('library_dirs',[]) + info.library_dirs()
        
        file = self.generate_file(location=location)
        # This is needed so that files build correctly even when different
        # versions of Python are running around.
        # Imported at beginning of file now to help with test paths.
        # import catalog 
        #temp = catalog.default_temp_dir()
        # for speed, build in the machines temp directory
        temp = catalog.intermediate_dir()
        success = build_tools.build_extension(file, temp_dir = temp,
                                              sources = source_files,                                              
                                              compiler_name = compiler,
                                              verbose = verbose, **kw)
        if not success:
            raise SystemError, 'Compilation failed'

def generate_file_name(module_name,module_location):
    module_file = os.path.join(module_location,module_name)
    return os.path.abspath(module_file)

def generate_module(module_string, module_file):
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

def test():
    from scipy_test import module_test
    module_test(__name__,__file__)

def test_suite():
    from scipy_test import module_test_suite
    return module_test_suite(__name__,__file__)    

""" converters.py
"""


import base_spec
import scalar_spec
import sequence_spec
import common_spec


#--------------------------------------------------------
# The "standard" conversion classes
#--------------------------------------------------------

default = [scalar_spec.int_converter(),
           scalar_spec.float_converter(),
           scalar_spec.complex_converter(),
           sequence_spec.string_converter(),
           sequence_spec.list_converter(),
           sequence_spec.dict_converter(),
           sequence_spec.tuple_converter(),
           common_spec.file_converter(),
           common_spec.callable_converter(),
           common_spec.instance_converter(),]                          
          #common_spec.module_converter()]

try: 
    import standard_array_spec
    default.append(standard_array_spec.array_converter())
except: 
    pass    

try: 
    # this is currently safe because it doesn't import wxPython.
    import wx_spec
    default.append(wx_spec.wx_converter())
except: 
    pass    

#--------------------------------------------------------
# Blitz conversion classes
#
# same as default, but will convert Numeric arrays to blitz
# C++ classes 
#--------------------------------------------------------
import blitz_spec
blitz = [blitz_spec.array_converter()] + default


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

from base_spec import base_converter
import scalar_info
#from Numeric import *
from types import *

# the following typemaps are for 32 bit platforms.  A way to do this
# general case? maybe ask numeric types how long they are and base
# the decisions on that.

numeric_to_c_type_mapping = {}

numeric_to_c_type_mapping['T'] = 'T' # for templates
numeric_to_c_type_mapping['F'] = 'std::complex<float> '
numeric_to_c_type_mapping['D'] = 'std::complex<double> '
numeric_to_c_type_mapping['f'] = 'float'
numeric_to_c_type_mapping['d'] = 'double'
numeric_to_c_type_mapping['1'] = 'char'
numeric_to_c_type_mapping['b'] = 'unsigned char'
numeric_to_c_type_mapping['s'] = 'short'
numeric_to_c_type_mapping['i'] = 'int'
# not strictly correct, but shoulld be fine fo numeric work.
# add test somewhere to make sure long can be cast to int before using.
numeric_to_c_type_mapping['l'] = 'int'

# standard Python numeric type mappings.
numeric_to_c_type_mapping[type(1)]  = 'int'
numeric_to_c_type_mapping[type(1.)] = 'double'
numeric_to_c_type_mapping[type(1.+1.j)] = 'std::complex<double> '
#hmmm. The following is likely unsafe...
numeric_to_c_type_mapping[type(1L)]  = 'int'

class scalar_converter(base_converter):
    _build_information = [scalar_info.scalar_info()]        

    def type_spec(self,name,value):
        # factory
        new_spec = self.__class__()
        new_spec.name = name
        new_spec.numeric_type = type(value)
        return new_spec
    
    def declaration_code(self,inline=0):
        type = numeric_to_c_type_mapping[self.numeric_type]
        func_type = self.type_name
        name = self.name
        var_name = self.retrieve_py_variable(inline)
        template = '%(type)s %(name)s = '\
                        'convert_to_%(func_type)s (%(var_name)s,"%(name)s");\n'
        code = template % locals()
        return code

    def __repr__(self):
        msg = "(%s:: name: %s, type: %s)" % \
               (self.type_name,self.name, self.numeric_type)
        return msg
    def __cmp__(self,other):
        #only works for equal
        return cmp(self.name,other.name) or \
               cmp(self.numeric_type,other.numeric_type) or \
               cmp(self.__class__, other.__class__)

class int_converter(scalar_converter):
    type_name = 'int'
    def type_match(self,value):
        return type(value) in [IntType, LongType]
        
    def local_dict_code(self):
        code = 'local_dict["%s"] = Py::Int(%s);\n' % (self.name,self.name)        
        return code
    
class float_converter(scalar_converter):
    type_name = 'float'
    def type_match(self,value):
        return type(value) in [FloatType]
    def local_dict_code(self):
        code = 'local_dict["%s"] = Py::Float(%s);\n' % (self.name,self.name)        
        return code

class complex_converter(scalar_converter):
    type_name = 'complex'
    def type_match(self,value):
        return type(value) in [ComplexType]
    def local_dict_code(self):
        code = 'local_dict["%s"] = Py::Complex(%s.real(),%s.imag());\n' % \
                (self.name,self.name,self.name)        
        return code

def test():
    from scipy_test import module_test
    module_test(__name__,__file__)

def test_suite():
    from scipy_test import module_test_suite
    return module_test_suite(__name__,__file__)    
        
""" Generic support code for handling standard Numeric arrays      
"""

import base_info

#############################################################
# Basic module support code
#############################################################

from conversion_code import module_support_code
from conversion_code import file_convert_code
from conversion_code import instance_convert_code
from conversion_code import callable_convert_code
from conversion_code import module_convert_code
from conversion_code import scalar_support_code
#from conversion_code import non_template_scalar_support_code

class basic_module_info(base_info.base_info):
    _headers = ['"Python.h"']
    _support_code = [module_support_code]

class file_info(base_info.base_info):
    _headers = ['<stdio.h>']
    _support_code = [file_convert_code]

class instance_info(base_info.base_info):
    _support_code = [instance_convert_code]

class callable_info(base_info.base_info):
    _support_code = [callable_convert_code]

class module_info(base_info.base_info):
    _support_code = [module_convert_code]

class scalar_info(base_info.base_info):
    _warnings = ['disable: 4275', 'disable: 4101']
    _headers = ['<complex>','<math.h>']
    def support_code(self):
        return [scalar_support_code]
    #def support_code(self):
    #    if self.compiler != 'msvc':
    #         # maybe this should only be for gcc...
    #        return [scalar_support_code,non_template_scalar_support_code]
    #    else:
    #        return [non_template_scalar_support_code]

""" Generic support code for handling standard Numeric arrays      
"""

import base_info


array_convert_code = \
"""

class numpy_handler
{
public:
    PyArrayObject* convert_to_numpy(PyObject* py_obj, const char* name)
    {
        PyArrayObject* arr_obj = NULL;
    
        if (!py_obj || !PyArray_Check(py_obj))
            handle_conversion_error(py_obj,"array", name);
    
        // Any need to deal with INC/DEC REFs?
        Py_INCREF(py_obj);
        return (PyArrayObject*) py_obj;
    }
    
    PyArrayObject* py_to_numpy(PyObject* py_obj, const char* name)
    {
        PyArrayObject* arr_obj = NULL;
    
        if (!py_obj || !PyArray_Check(py_obj))
            handle_bad_type(py_obj,"array", name);
    
        // Any need to deal with INC/DEC REFs?
        Py_INCREF(py_obj);
        return (PyArrayObject*) py_obj;
    }
};

numpy_handler x__numpy_handler = numpy_handler();
#define convert_to_numpy x__numpy_handler.convert_to_numpy
#define py_to_numpy x__numpy_handler.py_to_numpy
"""

type_check_code = \
"""
class numpy_type_handler
{
public:
    void conversion_numpy_check_type(PyArrayObject* arr_obj, int numeric_type,
                                     const char* name)
    {
        // Make sure input has correct numeric type.
        if (arr_obj->descr->type_num != numeric_type)
        {
            char* type_names[13] = {"char","unsigned byte","byte", "short", "int", 
                                    "long", "float", "double", "complex float",
                                    "complex double", "object","ntype","unkown"};
            char msg[500];
            sprintf(msg,"Conversion Error: received '%s' typed array instead of '%s' typed array for variable '%s'",
                    type_names[arr_obj->descr->type_num],type_names[numeric_type],name);
            throw_error(PyExc_TypeError,msg);    
        }
    }
    
    void numpy_check_type(PyArrayObject* arr_obj, int numeric_type, const char* name)
    {
        // Make sure input has correct numeric type.
        if (arr_obj->descr->type_num != numeric_type)
        {
            char* type_names[13] = {"char","unsigned byte","byte", "short", "int", 
                                    "long", "float", "double", "complex float",
                                    "complex double", "object","ntype","unkown"};
            char msg[500];
            sprintf(msg,"received '%s' typed array instead of '%s' typed array for variable '%s'",
                    type_names[arr_obj->descr->type_num],type_names[numeric_type],name);
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

class array_info(base_info.base_info):
    _headers = ['"Numeric/arrayobject.h"','<complex>','<math.h>']
    _support_code = [array_convert_code,size_check_code, type_check_code]
    _module_init_code = [numeric_init_code]    
import os,sys,string
import pprint 

def remove_whitespace(in_str):
    import string
    out = string.replace(in_str," ","")
    out = string.replace(out,"\t","")
    out = string.replace(out,"\n","")
    return out
    
def print_assert_equal(test_string,actual,desired):
    """this should probably be in scipy_test
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

def c_int_search(seq,t,chk=1):
    # do partial type checking in Python.
    # checking that list items are ints should happen in py_to_scalar<int>
    if chk:
        assert(type(t) == type(1))
        assert(type(seq) == type([]))
    code = """     
           #line 29 "binary_search.py"
           int val, m, min = 0; 
           int max = seq.length()- 1;
           PyObject *py_val;
           for(;;) 
           { 
               if (max < min )
               {
                   return_val = Py::new_reference_to(Py::Int(-1));
                   break;
               }
               m = (min + max) / 2;
               val = py_to_int(PyList_GetItem(seq.ptr(),m),"val");
               if (val < t)     
                   min = m + 1;
               else if (val > t)    
                   max = m - 1;
               else
               {
                   return_val = Py::new_reference_to(Py::Int(m));
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
               int max = _Nseq[0] - 1;
               PyObject *py_val;
               for(;;) 
               { 
                   if (max < min )
                   {
                       return_val = Py::new_reference_to(Py::Int(-1));
                       break;
                   }
                   m = (min + max) / 2;
                   val = seq_data[m];
                   if (val < t)     
                       min = m + 1;
                   else if (val > t)    
                       max = m - 1;
                   else
                   {
                       return_val = Py::new_reference_to(Py::Int(m));
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
    bi = (t2-t1)
    print ' speed of bisect:', bi
    print ' speed up: %3.2f' % (py/bi)

    # get it in cache
    c_int_search(a,i)
    t1 = time.time()
    for i in range(n):
        c_int_search(a,i,chk=1)
    t2 = time.time()
    print ' speed in c:',(t2 - t1)    
    print ' speed up: %3.2f' % (py/(t2-t1))

    # get it in cache
    c_int_search(a,i)
    t1 = time.time()
    for i in range(n):
        c_int_search(a,i,chk=0)
    t2 = time.time()
    print ' speed in c(no asserts):',(t2 - t1)    
    print ' speed up: %3.2f' % (py/(t2-t1))

    # get it in cache
    try:
        a = array(a)
        c_array_int_search(a,i)
        t1 = time.time()
        for i in range(n):
            c_array_int_search(a,i)
        t2 = time.time()
        print ' speed in c(Numeric arrays):',(t2 - t1)    
        print ' speed up: %3.2f' % (py/(t2-t1))
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

def Ramp_numeric1(result,size,start,end):
    code = """
           double step = (end-start)/(size-1);
           double val = start;
           for (int i = 0; i < size; i++)
               *result_data++ = start + step*i;
           """
    weave.inline(code,['result','size','start','end'],compiler='gcc')

def Ramp_numeric2(result,size,start,end):
    code = """
           double step = (end-start)/(size-1);
           double val = start;
           for (int i = 0; i < size; i++)
           {
              result_data[i] = val;
              val += step; 
           }
           """
    weave.inline(code,['result','size','start','end'],compiler='gcc')

def Ramp_list1(result, size, start, end):
    code = """
           double step = (end-start)/(size-1);
           int i;        
           for (i = 0; i < size; i++) 
           {
               result[i] = Py::Float(start + step*i);
           }
           """
    weave.inline(code, ["result", "size", "start", "end"], verbose=2)

def Ramp_list2(result, size, start, end):
    code = """
           double step = (end-start)/(size-1);
           int i;
           PyObject* raw_result = result.ptr();
           for (i = 0; i < size; i++) 
           {
               PyObject* val = PyFloat_FromDouble( start + step*i );
               PySequence_SetItem(raw_result,i, val);
           }
           """
    weave.inline(code, ["result", "size", "start", "end"], verbose=2)
          
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
    Ramp_numeric1(arr1, N_array, 0.0, 1.0)
    t1 = time.time()
    for i in xrange(N_c):
        Ramp_numeric1(arr1, N_array, 0.0, 1.0)
    t2 = time.time()
    c_time = (t2 - t1)
    print 'compiled numeric1 (seconds, speed up):', c_time, py_time/ c_time
    print 'arr[500]:', arr1[500]

    arr2 = array([0]*N_array,Float64)
    # First call compiles function or loads from cache.
    # I'm not including this in the timing.
    Ramp_numeric2(arr2, N_array, 0.0, 1.0)
    t1 = time.time()
    for i in xrange(N_c):
        Ramp_numeric2(arr2, N_array, 0.0, 1.0)
    t2 = time.time()
    c_time = (t2 - t1)   
    print 'compiled numeric2 (seconds, speed up):', c_time, py_time/ c_time
    print 'arr[500]:', arr2[500]

    arr3 = [0]*N_array
    # First call compiles function or loads from cache.
    # I'm not including this in the timing.
    Ramp_list1(arr3, N_array, 0.0, 1.0)
    t1 = time.time()
    for i in xrange(N_py):
        Ramp_list1(arr3, N_array, 0.0, 1.0)
    t2 = time.time()
    c_time = (t2 - t1) * ratio  
    print 'compiled list1 (seconds, speed up):', c_time, py_time/ c_time
    print 'arr[500]:', arr3[500]
    
    arr4 = [0]*N_array
    # First call compiles function or loads from cache.
    # I'm not including this in the timing.
    Ramp_list2(arr4, N_array, 0.0, 1.0)
    t1 = time.time()
    for i in xrange(N_py):
        Ramp_list2(arr4, N_array, 0.0, 1.0)
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
#    C:\home\ej\wrk\scipy\compiler\examples>python dict_sort.py
#    Dict sort of 1000 items for 300 iterations:
#     speed in python: 0.319999933243
#     [0, 1, 2, 3, 4]
#     speed in c: 0.159999966621
#     speed up: 2.00
#     [0, 1, 2, 3, 4]
 
import sys
sys.path.insert(0,'..')
import inline_tools

def c_sort(adict):
    assert(type(adict) == type({}))
    code = """
           #line 21 "dict_sort.py"     
           Py::List keys = adict.keys();
           Py::List items(keys.length());
           keys.sort(); // surely this isn't any slower than raw API calls
           PyObject* item = NULL;
           for(int i = 0; i < keys.length();i++)
           {
              item = PyList_GET_ITEM(keys.ptr(),i);
              item = PyDict_GetItem(adict.ptr(),item);
              Py_XINCREF(item);
              PyList_SetItem(items.ptr(),i,item);              
           }           
           return_val = Py::new_reference_to(items);
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
    print ' speed in c:',(t2 - t1)    
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
    n = 300
    sort_compare(a,n)    

import sys
sys.path.insert(0,'..')
import inline_tools

def multi_return():
    return 1, '2nd'

def c_multi_return():

    code =  """
 	        Py::Tuple results(2);
 	        results[0] = Py::Int(1);
 	        results[1] = Py::String("2nd");
 	        return_val = Py::new_reference_to(results); 	        
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
from blitz_tools import blitz_type_converters
import scalar_spec

def vq(obs,code_book):
    # make sure we're looking at arrays.
    obs = asarray(obs)
    code_book = asarray(code_book)
    # check for 2d arrays and compatible sizes.
    obs_sh = shape(obs)
    code_book_sh = shape(code_book)
    assert(len(obs_sh) == 2 and len(code_book_sh) == 2)   
    assert(obs_sh[1] == code_book_sh[1])   
    type = scalar_spec.numeric_to_c_type_mapping[obs.typecode()]
    # band aid for now.
    ar_type = 'PyArray_FLOAT'
    code =  """
            #line 37 "vq.py"
            // Use tensor notation.            
            blitz::Array<%(type)s,2> dist_sq(_Ncode_book[0],_Nobs[0]);
 	        blitz::firstIndex i;    
            blitz::secondIndex j;   
            blitz::thirdIndex k;
            dist_sq = sum(pow2(obs(j,k) - code_book(i,k)),k);
            // Surely there is a better way to do this...
            PyArrayObject* py_code = (PyArrayObject*) PyArray_FromDims(1,&_Nobs[0],PyArray_LONG);
 	        blitz::Array<int,1> code((int*)(py_code->data),
                                     blitz::shape(_Nobs[0]), blitz::neverDeleteData);
 	        code = minIndex(dist_sq(j,i),j);
 	        
 	        PyArrayObject* py_min_dist = (PyArrayObject*) PyArray_FromDims(1,&_Nobs[0],PyArray_FLOAT);
 	        blitz::Array<float,1> min_dist((float*)(py_min_dist->data),
 	                                       blitz::shape(_Nobs[0]), blitz::neverDeleteData);
 	        min_dist = sqrt(min(dist_sq(j,i),j));
 	        Py::Tuple results(2);
 	        results[0] = Py::Object((PyObject*)py_code);
 	        results[1] = Py::Object((PyObject*)py_min_dist);
 	        return_val = Py::new_reference_to(results); 	        
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
    type = scalar_spec.numeric_to_c_type_mapping[obs.typecode()]
    # band aid for now.
    ar_type = 'PyArray_FLOAT'
    code =  """
            #line 83 "vq.py"
            // THIS DOES NOT HANDLE STRIDED ARRAYS CORRECTLY
            // Surely there is a better way to do this...
            PyArrayObject* py_code = (PyArrayObject*) PyArray_FromDims(1,&_Nobs[0],PyArray_LONG);	        
 	        PyArrayObject* py_min_dist = (PyArrayObject*) PyArray_FromDims(1,&_Nobs[0],PyArray_FLOAT);
 	        
            int* raw_code = (int*)(py_code->data);
            float* raw_min_dist = (float*)(py_min_dist->data);
            %(type)s* raw_obs = obs.data();
            %(type)s* raw_code_book = code_book.data(); 
            %(type)s* this_obs = NULL;
            %(type)s* this_code = NULL; 
            int Nfeatures = _Nobs[1];
            float diff,dist;
            for(int i=0; i < _Nobs[0]; i++)
            {
                this_obs = &raw_obs[i*Nfeatures];
                raw_min_dist[i] = (%(type)s)10000000.; // big number
                for(int j=0; j < _Ncode_book[0]; j++)
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
 	        Py::Tuple results(2);
 	        results[0] = Py::Object((PyObject*)py_code);
 	        results[1] = Py::Object((PyObject*)py_min_dist);
 	        return_val = Py::new_reference_to(results); 	        
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
    type = scalar_spec.numeric_to_c_type_mapping[obs.typecode()]
    code =  """
            #line 139 "vq.py"
            // Surely there is a better way to do this...
            PyArrayObject* py_code = (PyArrayObject*) PyArray_FromDims(1,&_Nobs[0],PyArray_LONG);	        
 	        PyArrayObject* py_min_dist = (PyArrayObject*) PyArray_FromDims(1,&_Nobs[0],PyArray_FLOAT);
 	        
            int* code_data = (int*)(py_code->data);
            float* min_dist_data = (float*)(py_min_dist->data);
            %(type)s* this_obs = NULL;
            %(type)s* this_code = NULL; 
            int Nfeatures = _Nobs[1];
            float diff,dist;

            for(int i=0; i < _Nobs[0]; i++)
            {
                this_obs = &obs_data[i*Nfeatures];
                min_dist_data[i] = (float)10000000.; // big number
                for(int j=0; j < _Ncode_book[0]; j++)
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
 	        Py::Tuple results(2);
 	        results[0] = Py::Object((PyObject*)py_code);
 	        results[1] = Py::Object((PyObject*)py_min_dist);
 	        return Py::new_reference_to(results); 	        
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

run()    
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
           #line 12 "functional.py"
           Py::Tuple args(1);    
           Py::List result(seq.length());
           PyObject* this_result = NULL;
           for(int i = 0; i < seq.length();i++)
           {
              args[0] = seq[i];
              this_result = PyEval_CallObject(func,args.ptr());
              result[i] = Py::Object(this_result);
           }           
           return_val = Py::new_reference_to(result);
           """   
    return inline_tools.inline(code,['func','seq'])

def c_list_map2(func,seq):
    """ Uses Python API more than CXX to implement a simple map-like function.
        It does not provide any error checking.
    """
    assert(type(func) in [FunctionType,MethodType,type(len)])
    code = """
           #line 32 "functional.py"
           Py::Tuple args(1);    
           Py::List result(seq.length());
           PyObject* item = NULL;
           PyObject* this_result = NULL;
           for(int i = 0; i < seq.length();i++)
           {
              item = PyList_GET_ITEM(seq.ptr(),i);
              PyTuple_SetItem(args.ptr(),0,item);
              this_result = PyEval_CallObject(func,args.ptr());
              PyList_SetItem(result.ptr(),i,this_result);              
           }           
           return_val = Py::new_reference_to(result);
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
    print 'c speed:', c
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
    size,start,end = 0,0.,0.
    code = """
           double step = (end-start)/(size-1);
           double val = start;
           for (int i = 0; i < size; i++)
           {
              result_data[i] = val;
              val += step; 
           }
           """
    func = ext_tools.ext_function('Ramp',code,['result','size','start','end'])
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
        ramp_ext.Ramp(arr, 10000, 0.0, 1.0)
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
        #line 108 "wx_example.py"
        dc->BeginDrawing();
        dc->SetPen(wxPen(*red,4,wxSOLID));
        dc->DrawRectangle(5, 5, 50, 50);

        dc->SetBrush(*grey_brush);
        dc->SetPen(wxPen(*blue, 4,wxSOLID));
        dc->DrawRectangle(15, 15, 50, 50);
        """
        inline_tools.inline(code,['dc','red','blue','grey_brush'],compiler='msvc')
        
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
               PyObject* length(Py::String a)
               {
                   int l = a.length();
                   return Py::new_reference_to(Py::Int(l));
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

    ext_code = "return_val = Py::new_reference_to(Py::Int(a+1));"    
    func = ext_tools.ext_function('increment',ext_code,['a'])
    mod.add_function(func)
    
    ext_code = "return_val = Py::new_reference_to(Py::Int(a+2));"    
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
# C:\home\ej\wrk\scipy\compiler\examples>python fibonacci.py
# Recursively computing the first 30 fibonacci numbers:
#  speed in python: 3.98599994183
#  speed in c: 0.0800000429153
#  speed up: 49.82
# Loopin to compute the first 30 fibonacci numbers:
#  speed in python: 0.00053100001812
#  speed in c: 5.99999427795e-005
#  speed up: 8.85
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
                   int val = fib1(a);
                   return_val = Py::new_reference_to(Py::Int(val));
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
                   int val = fib2(a);
                   return_val = Py::new_reference_to(Py::Int(val));
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
    print 'Loopin to compute the first %d fibonacci numbers:' % n
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
import scalar_spec
from blitz_tools import blitz_type_converters

def _cast_copy_transpose(type,a_2d):
    assert(len(shape(a_2d)) == 2)
    new_array = zeros(shape(a_2d),type)
    #trans_a_2d = transpose(a_2d)
    numeric_type = scalar_spec.numeric_to_c_type_mapping[type]
    code = """
           for(int i = 0; i < _Na_2d[0]; i++)
               for(int j = 0; j < _Na_2d[1]; j++)
                   new_array(i,j) = (%s) a_2d(j,i);
           """ % numeric_type
    inline_tools.inline(code,['new_array','a_2d'],
                        type_converters = blitz_type_converters,
                        compiler='gcc',
                        verbose = 1)
    return new_array

def _inplace_transpose(a_2d):
    assert(len(shape(a_2d)) == 2)
    numeric_type = scalar_spec.numeric_to_c_type_mapping[a_2d.typecode()]
    code = """
           %s temp;
           for(int i = 0; i < _Na_2d[0]; i++)
               for(int j = 0; j < _Na_2d[1]; j++)
               {
                   temp = a_2d(i,j);
                   a_2d(i,j) = a_2d(j,i);
                   a_2d(j,i) = temp;
               }    
           """ % numeric_type
    inline_tools.inline(code,['a_2d'],
                        type_converters = blitz_type_converters,
                        compiler='gcc',def _cast_copy_transpose(type,a_2d):
    assert(len(shape(a_2d)) == 2)
    new_array = zeros(shape(a_2d),type)
    #trans_a_2d = transpose(a_2d)
    numeric_type = scalar_spec.numeric_to_c_type_mapping[type]
    code = """
           for(int i = 0; i < _Na_2d[0]; i++)
               for(int j = 0; j < _Na_2d[1]; j++)
                   new_array(i,j) = (%s) a_2d(j,i);
           """ % numeric_type
    inline_tools.inline(code,['new_array','a_2d'],
                        type_converters = blitz_type_converters,
                        compiler='gcc',
                        verbose = 1)
    return new_array

                        verbose = 1)
    return a_2d

def cast_copy_transpose(type,*arrays):
    results = []
    for a in arrays:
        results.append(_cast_copy_transpose(type,a))
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
    print ' speed in c:',(t2 - t1)/ m    
    print ' speed up: %3.2f' % (py/(t2-t1))

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
    m,n = 1,150
    compare(m,n)    

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

def assert_approx_equal(actual,desired,significant=7,err_msg='',verbose=1):
    """ Raise an assertion if two items are not
        equal.  I think this should be part of unittest.py
        Approximately equal is defined as the number of significant digits 
        correct
    """
    msg = '\nItems are not equal to %d significant digits:\n' % significant
    msg += err_msg
    sc_desired = desired/pow(10,math.floor(math.log10(desired)))
    sc_actual = actual/pow(10,math.floor(math.log10(actual)))
    try:
        if ( verbose and len(str(desired)) < 100 and len(str(actual)) ):
            msg =  msg \
                 + 'DESIRED: ' + str(desired) \
                 + '\nACTUAL: ' + str(actual)
    except:
        msg =  msg \
             + 'DESIRED: ' + str(desired) \
             + '\nACTUAL: ' + str(actual)
    assert math.fabs(sc_desired - sc_actual) < pow(10.,-1*significant), msg
    
try:
    # Numeric specific testss
    from Numeric import *
    from fastumath import *
    
    def assert_array_equal(x,y,err_msg=''):
        msg = '\nArrays are not equal'
        try:
            assert alltrue(equal(shape(x),shape(y))),\
                   msg + ' (shapes mismatch):\n\t' + err_msg
            reduced = equal(x,y)
            assert alltrue(ravel(reduced)),\
                   msg + ':\n\t' + err_msg
        except ValueError:
            print shape(x),shape(y)
            raise ValueError, 'arrays are not equal'
    
    def assert_array_almost_equal(x,y,decimal=6,err_msg=''):
        msg = '\nArrays are not almost equal'
        try:
            assert alltrue(equal(shape(x),shape(y))),\
                   msg + ' (shapes mismatch):\n\t' + err_msg
            reduced = equal(around(abs(x-y),decimal),0)
            assert alltrue(ravel(reduced)),\
                   msg + ':\n\t' + err_msg
        except ValueError:
            print sys.exc_value
            print shape(x),shape(y)
            print x, y
            raise ValueError, 'arrays are not almost equal'
except:
    pass # Numeric not installed
    
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
from scipy_distutils.misc_util import get_path, default_config_dict 

def configuration(parent_package=''):
    parent_path = parent_package
    if parent_package:
        parent_package += '.'
    local_path = get_path(__name__)

    config = default_config_dict()
    config['packages'].append(parent_package+'scipy_test')
    config['package_dir'][parent_package+'scipy_test'] = local_path
    return config
       
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

from scipy_test import *

#!/usr/bin/env python
from setup_scipy_test import install_package
    
if __name__ == '__main__':
    install_package()


import sys, os, glob

def get_x11_info():
    if sys.platform  == 'win32':
        return {}

    #XXX: add other combinations if needed
    libs = ['X11']
    prefixes = ['/usr','/usr/local','/opt']
    x11_names = ['X11R6','X11']
    header_files = ['X.h','X11/X.h']

    x11_lib,x11_lib_dir,x11_inc_dir = None,None,None
    for p in prefixes:
        for n in x11_names:
            d = os.path.join(p,n)
            if not os.path.exists(d): continue
            if x11_lib is None:
                # Find library and its location
                for l in libs:
                    if glob.glob(os.path.join(d,'lib','lib%s.*' % l)):
                        x11_lib = l
                        x11_lib_dir = os.path.join(d,'lib')
                        break
            if x11_inc_dir is None:
                # Find the location of header file
                for h in header_files:
                    if os.path.exists(os.path.join(d,'include',h)):
                        x11_inc_dir = os.path.join(d,'include')
                        break
        if None not in [x11_lib,x11_inc_dir]:
            break
    if None in [x11_lib,x11_inc_dir]:
        return {}
    info = {}
    info['libraries'] = [x11_lib]
    info['library_dirs'] = [x11_lib_dir]
    info['include_dirs'] = [x11_inc_dir]
    return info


import os,sys,string

def update_version(release_level='alpha',
                   path='.',
                   version_template = \
                   '%(major)d.%(minor)d.%(micro)d-%(release_level)s-%(serial)d',
                   major=None,
                   overwrite_version_py = 1):
    """
    Return version string calculated from CVS/Entries file(s) starting
    at <path>. If the version information is different from the one
    found in the <path>/__version__.py file, update_version updates
    the file automatically. The version information will be always
    increasing in time.
    If CVS tree does not exist (e.g. as in distribution packages),
    return the version string found from  <path>/__version__.py.
    If no version information is available, return None.

    Default version string is in the form

      <major>.<minor>.<micro>-<release_level>-<serial>

    The items have the following meanings:

      serial - shows cumulative changes in all files in the CVS
               repository
      micro  - a number that is equivalent to the number of files
      minor  - indicates the changes in micro value (files are added
               or removed)
      release_level - is alpha, beta, canditate, or final
      major  - indicates changes in release_level.

    """
    # Issues:
    # *** Recommend or not to add __version__.py file to CVS
    #     repository? If it is in CVS, then when commiting, the
    #     version information will change, but __version__.py
    #     is commited with the old version information. To get
    #     __version__.py also up to date, a second commit of the
    #     __version__.py file is required after you re-run
    #     update_version(..). To summarize:
    #     1) cvs commit ...
    #     2) python setup.py  # that should call update_version
    #     3) cvs commit -m "updating version" __version__.py

    release_level_map = {'alpha':0,
                         'beta':1,
                         'canditate':2,
                         'final':3}
    release_level_value = release_level_map.get(release_level)
    if release_level_value is None:
        print 'Warning: release_level=%s is not %s'\
              % (release_level,
                 string.join(release_level_map.keys(),','))

    cwd = os.getcwd()
    os.chdir(path)
    try:
        version_module = __import__('__version__')
        reload(version_module)
        old_version_info = version_module.version_info
        old_version = version_module.version
    except:
        print sys.exc_value
        old_version_info = None
        old_version = None
    os.chdir(cwd)

    cvs_revs = get_cvs_revision(path)
    if cvs_revs is None:
        return old_version

    minor = 1
    micro,serial = cvs_revs
    if old_version_info is not None:
        minor = old_version_info[1]
        old_release_level_value = release_level_map.get(old_version_info[3])
        if micro != old_version_info[2]: # files have beed added or removed
            minor = minor + 1
        if major is None:
            major = old_version_info[0]
            if old_release_level_value is not None:
                if old_release_level_value > release_level_value:
                    major = major + 1
    if major is None:
        major = 0

    version_info = (major,minor,micro,release_level,serial)
    version_dict = {'major':major,'minor':minor,'micro':micro,
                    'release_level':release_level,'serial':serial
                    }
    version = version_template % version_dict

    if version_info != old_version_info:
        print 'version increase detected: %s -> %s'%(old_version,version)
        version_file = os.path.join(path,'__version__.py')
        if not overwrite_version_py:
            print 'keeping %s with old version, returing new version' \
                  % (version_file)
            return version
        print 'updating version in %s' % version_file
        version_file = os.path.abspath(version_file)
        f = open(version_file,'w')
        f.write('# This file is automatically updated with update_version\n'\
                '# function from scipy_distutils.misc_util.py\n'\
                'version = %s\n'\
                'version_info = %s\n'%(repr(version),version_info))
        f.close()
    return version

def get_version(release_level='alpha',
                path='.',
                version_template = \
                '%(major)d.%(minor)d.%(micro)d-%(release_level)s-%(serial)d',
                major=None,
                ):
    """
    Return version string calculated from CVS/Entries file(s) starting
    at <path>. Does not change <path>/__version__.py.
    See also update_version(..) function.
    """
    return update_version(release_level = release_level,path = path,
                          version_template = version_template,
                          major = major,overwrite_version_py = 0)


def get_cvs_revision(path):
    """
    Return two last cumulative revision numbers of a CVS tree starting
    at <path>. The first number shows the number of files in the CVS
    tree (this is often true, but not always) and the second number
    characterizes the changes in these files.
    If <path>/CVS/Entries is not existing then return None.
    """
    entries_file = os.path.join(path,'CVS','Entries')
    if os.path.exists(entries_file):
        rev1,rev2 = 0,0
        for line in open(entries_file).readlines():
            items = string.split(line,'/')
            if items[0]=='D' and len(items)>1:
                try:
                    d1,d2 = get_cvs_revision(os.path.join(path,items[1]))
                except:
                    d1,d2 = 0,0
            elif items[0]=='' and len(items)>3 and items[1]!='__version__.py':
		last_numbers = map(eval,string.split(items[2],'.')[-2:])
		if len(last_numbers)==2:
		    d1,d2 = last_numbers
		else: # this is when 'cvs add' but not yet 'cvs commit'
		    d1,d2 = 0,0
            else:
                continue
            rev1,rev2 = rev1+d1,rev2+d2
        return rev1,rev2

def get_path(mod_name):
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
        #import scipy_distutils.setup
        mod = __import__(mod_name)
        file = mod.__file__
        d = os.path.dirname(os.path.abspath(file))
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

def default_config_dict(name = None, parent_name = None):
    d={}
    for key in list_keys: d[key] = []
    for key in dict_keys: d[key] = {}

    full_name = dot_join(parent_name,name)

    if full_name:
        # XXX: The following assumes that default_config_dict is called
        #      only from setup_<name>.configuration().
        frame = sys._getframe(1)
        caller_name = eval('__name__',frame.f_globals,frame.f_locals)
        local_path = get_path(caller_name)
        if name and not parent_name:
            # Useful for local builds
            d['version'] = update_version(path=local_path)

        if os.path.exists(os.path.join(local_path,'__init__.py')):
            d['packages'].append(full_name)
            d['package_dir'][full_name] = local_path
        d['name'] = full_name
        if not parent_name:
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

def merge_config_dicts(config_list):
    result = default_config_dict()
    for d in config_list:
        for key in list_keys:
            result[key].extend(d.get(key,[]))
        for key in dict_keys:
            result[key].update(d.get(key,{}))
    return result

def dot_join(*args):
    return string.join(filter(None,args),'.')

def fortran_library_item(lib_name,
                         sources,
                         **attrs
                         ):
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
    else:
        print file, 'ok'    

def dos2unix_one_dir(args,dir_name,file_names):
    for file in file_names:
        full_path = os.path.join(dir_name,file)
        dos2unix(full_path)
    
def dos2unix_dir(dir_name):
    os.path.walk(dir_name,dos2unix_one_dir,[])

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
        
    newdata = re.sub("\n", "\r\n", data)
    if newdata != data:
        print 'unix2dos:', file
        f = open(file, "wb")
        f.write(newdata)
        f.close()
    else:
        print file, 'ok'    

def unix2dos_one_dir(args,dir_name,file_names):
    for file in file_names:
        full_path = os.path.join(dir_name,file)
        unix2dos(full_path)
    
def unix2dos_dir(dir_name):
    os.path.walk(dir_name,unix2dos_one_dir,[])
        
if __name__ == "__main__":
    import sys
    dos2unix_dir(sys.argv[1])

"""scipy_distutils

   Modified version of distutils to handle fortran source code, f2py,
   and other issues in the scipy build process.
"""

# Need to do something here to get distutils subsumed...

from distutils.core import *
from distutils.core import setup as old_setup

from distutils.cmd import Command
from scipy_distutils.extension import Extension

# Our dist is different than the standard one.
from scipy_distutils.dist import Distribution

from scipy_distutils.command import build
from scipy_distutils.command import build_py
from scipy_distutils.command import build_ext
from scipy_distutils.command import build_clib
from scipy_distutils.command import build_flib
from scipy_distutils.command import run_f2py
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
                'run_f2py':         run_f2py.run_f2py,
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

# This file is automatically updated with update_version
# function from scipy_distutils.misc_util.py
version = '0.6.23-alpha-116'
version_info = (0, 6, 23, 'alpha', 116)

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
        # lib2def lives in weave
        sys.path.append(os.path.join('.','weave'))

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
from misc_util import get_path, update_version

def install_package():
    """ Install the scipy_distutils.  The dance with the current directory is done
        to fool distutils into thinking it is run from the scipy_distutils directory
        even if it was invoked from another script located in a different location.
    """
    path = get_path(__name__)
    old_path = os.getcwd()
    os.chdir(path)
    try:

        version = update_version('alpha')
        print 'scipy_distutils',version

        setup (name = "scipy_distutils",
               version = version,
               description = "Changes to distutils needed for SciPy -- mostly Fortran support",
               author = "Travis Oliphant, Eric Jones, and Pearu Peterson",
               author_email = "scipy-devel@scipy.org",
               licence = "BSD Style",
               url = 'http://www.scipy.org',
               packages = ['scipy_distutils','scipy_distutils.command'],
               package_dir = {'scipy_distutils':path}
               )
    finally:
        os.chdir(old_path)
    
if __name__ == '__main__':
    install_package()

"""distutils.extension

Provides the Extension class, used to describe C/C++ extension
modules in setup scripts.

Overridden to support f2py.
"""

# created 2000/05/30, Greg Ward

__revision__ = "$Id$"

from distutils.extension import Extension as old_Extension

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
                  f2py_options=None
                 ):
        old_Extension.__init__(self,name, sources,
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
        self.f2py_options = f2py_options or []
        
# class Extension

import os
from scipy_distutils.misc_util import get_path, default_config_dict

def configuration(parent_package=''):
    parent_path = parent_package
    if parent_package:
        parent_package += '.'
    local_path = get_path(__name__)

    config = default_config_dict()
    package = 'scipy_distutils'
    config['packages'].append(parent_package+package)
    config['package_dir'][package] = local_path 
    package = 'scipy_distutils.command'   
    config['packages'].append(parent_package+package),
    config['package_dir'][package] = os.path.join(local_path,'command')    
    return config

import os

def get_fftw_info():
    # FFTW (requires FFTW libraries to be previously installed)
    double_libraries = ['fftw_threads','rfftw_threads','fftw','rfftw']
    float_libraries = map(lambda x: 's'+x,double_libraries)

    if os.name == 'nt':
        fftw_dirs = ['c:\\fftw']
    else:
        base_dir = os.environ.get('FFTW')
        if base_dir is None:
            base_dir = os.environ['HOME']
        fftw_dirs = [os.path.join(base_dir,'lib')]
        double_libraries += ['pthread']
        float_libraries += ['pthread']

    return float_libraries, double_libraries, fftw_dirs

import sys, os
from misc_util import get_path

library_path = ''

def get_atlas_info():
    if sys.platform  == 'win32':
        if not library_path:
            atlas_library_dirs=['C:\\atlas\\WinNT_PIIISSE1']
        else:
            atlas_library_dirs = library_path
        blas_libraries = ['f77blas', 'cblas', 'atlas', 'g2c']
        lapack_libraries = ['lapack'] + blas_libraries 
    else:
        if not library_path:
            atlas_library_dirs = unix_atlas_directory(sys.platform)
        else:
            atlas_library_dirs = library_path
        blas_libraries = ['cblas','f77blas','atlas','g2c']
        lapack_libraries = ['lapack'] + blas_libraries
    return blas_libraries, lapack_libraries, atlas_library_dirs

def unix_atlas_directory(platform):
    """ Search a list of common locations looking for the atlas directory.
 
        Return None if the directory isn't found, otherwise return the
        directory name.  This isn't very sophisticated right now.  I can
        imagine doing an ftp to our server on platforms that we know about.
 
        Atlas is a highly optimized version of lapack and blas that is fast
        on almost all platforms.
    """
    result = [] #None
    # do a little looking for the linalg directory for atlas libraries
    #path = get_path(__name__)
    #local_atlas0 = os.path.join(path,platform,'atlas')
    #local_atlas1 = os.path.join(path,platform[:-1],'atlas')
 
    # first look for a system defined atlas directory
    dir_search = ['/usr/local/lib/atlas','/usr/lib/atlas']#,
    #              local_atlas0, local_atlas1]
    for directory in dir_search:
        if os.path.exists(directory):
            result = [directory]
    # we should really do an ftp search or something like that at this point.
    return result   

from distutils.dist import *
from distutils.dist import Distribution as OldDistribution
from distutils.errors import DistutilsSetupError

from types import *

import re
fortran_pyf_ext_re = re.compile(r'.*[.](f90|f95|f77|for|ftn|f|pyf)\Z',re.I).match

class Distribution (OldDistribution):
    def __init__ (self, attrs=None):
        self.fortran_libraries = None
        OldDistribution.__init__(self, attrs)

    def has_f2py_sources (self):
        if self.has_ext_modules():
            for ext in self.ext_modules:
                for source in ext.sources:
                    if fortran_pyf_ext_re(source):
                        return 1
        return 0

    def has_f_libraries(self):
        if self.fortran_libraries and len(self.fortran_libraries) > 0:
            return 1
        return self.has_f2py_sources() # f2py might generate fortran sources.

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
    def has_f2py_sources(self):
        return self.distribution.has_f2py_sources()

    sub_commands = [('build_py',      old_build.has_pure_modules),
                    ('build_clib',    old_build.has_c_libraries),
                    ('run_f2py',      has_f2py_sources), # new feature
                    ('build_flib',    has_f_libraries),  # new feature
                    ('build_ext',     old_build.has_ext_modules),
                    ('build_scripts', old_build.has_scripts),
                   ]

#!/usr/bin/env python
"""
cpuinfo

Copyright 2001 Pearu Peterson all rights reserved,
Pearu Peterson <pearu@cens.ioc.ee>          
Permission to use, modify, and distribute this software is given under the
terms of the LGPL.  See http://www.fsf.org

Note:  This should be merged into proc at some point.  Perhaps proc should
be returning classes like this instead of using dictionaries.

NO WARRANTY IS EXPRESSED OR IMPLIED.  USE AT YOUR OWN RISK.
$Revision$
$Date$
Pearu Peterson
"""

__version__ = "$Id$"

__all__ = ['cpuinfo']

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

    def _is_AthlonK6(self):
        return re.match(r'.*?AMD-K6',self.info[0]['model name']) is not None

    def _is_AthlonK7(self):
        return re.match(r'.*?AMD-K7',self.info[0]['model name']) is not None

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

    #XXX
    _is_Pentium = _is_PentiumPro = _is_PentiumIII = _is_PentiumIV = _not_impl

    def _is_PentiumII(self):
        return re.match(r'.*?Pentium II\b',
                        self.info[0]['model name']) is not None

    # Varia

    def _is_singleCPU(self):
        return len(self.info) == 1

    def _has_fdiv_bug(self):
        return self.info[0]['fdiv_bug']=='yes'

    def _has_f00f_bug(self):
        return self.info[0]['f00f_bug']=='yes'

    def _has_mmx(self):
        return re.match(r'.*?\bmmx',self.info[0]['flags']) is not None

if sys.platform[:5] == 'linux': # variations: linux2,linux-i386 (any others?)
    cpuinfo = linux_cpuinfo
#XXX: other OS's. Eg. use _winreg on Win32. Or os.uname on unices.
else:
    cpuinfo = cpuinfo_base


"""
laptop:
[{'cache size': '256 KB', 'cpu MHz': '399.129', 'processor': '0', 'fdiv_bug': 'no', 'coma_bug': 'no', 'model': '6', 'cpuid level': '2', 'model name': 'Mobile Pentium II', 'fpu_exception': 'yes', 'hlt_bug': 'no', 'bogomips': '796.26', 'vendor_id': 'GenuineIntel', 'fpu': 'yes', 'wp': 'yes', 'cpu family': '6', 'f00f_bug': 'no', 'stepping': '13', 'flags': 'fpu vme de pse tsc msr pae mce cx8 sep mtrr pge mca cmov pat pse36 mmx fxsr'}]

kev:
[{'cache size': '512 KB', 'cpu MHz': '350.799', 'processor': '0', 'fdiv_bug': 'no', 'coma_bug': 'no', 'model': '5', 'cpuid level': '2', 'model name': 'Pentium II (Deschutes)', 'fpu_exception': 'yes', 'hlt_bug': 'no', 'bogomips': '699.59', 'vendor_id': 'GenuineIntel', 'fpu': 'yes', 'wp': 'yes', 'cpu family': '6', 'f00f_bug': 'no', 'stepping': '3', 'flags': 'fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 mmx fxsr'}, {'cache size': '512 KB', 'cpu MHz': '350.799', 'processor': '1', 'fdiv_bug': 'no', 'coma_bug': 'no', 'model': '5', 'cpuid level': '2', 'model name': 'Pentium II (Deschutes)', 'fpu_exception': 'yes', 'hlt_bug': 'no', 'bogomips': '701.23', 'vendor_id': 'GenuineIntel', 'fpu': 'yes', 'wp': 'yes', 'cpu family': '6', 'f00f_bug': 'no', 'stepping': '3', 'flags': 'fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 mmx fxsr'}]

ath:
[{'cache size': '512 KB', 'cpu MHz': '503.542', 'processor': '0', 'fdiv_bug': 'no', 'coma_bug': 'no', 'model': '1', 'cpuid level': '1', 'model name': 'AMD-K7(tm) Processor', 'fpu_exception': 'yes', 'hlt_bug': 'no', 'bogomips': '1002.70', 'vendor_id': 'AuthenticAMD', 'fpu': 'yes', 'wp': 'yes', 'cpu family': '6', 'f00f_bug': 'no', 'stepping': '2', 'flags': 'fpu vme de pse tsc msr pae mce cx8 sep mtrr pge mca cmov pat mmx syscall mmxext 3dnowext 3dnow'}]

fiasco:
[{'max. addr. space #': '127', 'cpu': 'Alpha', 'cpu serial number': 'Linux_is_Great!', 'kernel unaligned acc': '0 (pc=0,va=0)', 'system revision': '0', 'system variation': 'LX164', 'cycle frequency [Hz]': '533185472', 'system serial number': 'MILO-2.0.35-c5.', 'timer frequency [Hz]': '1024.00', 'cpu model': 'EV56', 'platform string': 'N/A', 'cpu revision': '0', 'BogoMIPS': '530.57', 'cpus detected': '0', 'phys. address bits': '40', 'user unaligned acc': '1340 (pc=2000000ec90,va=20001156da4)', 'page size [bytes]': '8192', 'system type': 'EB164', 'cpu variation': '0'}]
"""

if __name__ == "__main__":
    cpu = cpuinfo()

    cpu.is_blaa()
    cpu.is_Intel()
    cpu.is_Alpha()

    print 'CPU information:',
    for name in dir(cpuinfo):
        if name[0]=='_' and name[1]!='_' and getattr(cpu,name[1:])():
            print name[1:],
    print

""" Modified version of build_ext that handles fortran source files.
"""

import os, string
from types import *

from distutils.dep_util import newer_group, newer
from distutils.command.build_ext import *
from distutils.command.build_ext import build_ext as old_build_ext

from scipy_distutils.command.build_clib import get_headers,get_directories

class build_ext (old_build_ext):

    def build_extension(self, ext):
        #XXX: anything else we need to save?
        save_linker_so = self.compiler.linker_so
        save_compiler_libs = self.compiler.libraries
        save_compiler_libs_dirs = self.compiler.library_dirs
        
        # support for building static fortran libraries
        need_f_libs = 0
        ext_name = string.split(ext.name,'.')[-1]
        if self.distribution.has_f_libraries():
            build_flib = self.get_finalized_command('build_flib')
            if build_flib.has_f_library(ext_name):
                need_f_libs = 1
            else:
                for lib_name in ext.libraries:
                    if build_flib.has_f_library(lib_name):
                        need_f_libs = 1
                        break
        print ext.name,ext_name,'needs fortran libraries',need_f_libs
        if need_f_libs:
            moreargs = build_flib.fcompiler.get_extra_link_args()
            if moreargs != []:
                if ext.extra_link_args is None:
                    ext.extra_link_args = moreargs
                else:
                    ext.extra_link_args += moreargs
            if build_flib.has_f_library(ext_name) and \
               ext_name not in ext.libraries:
                ext.libraries.append(ext_name)
            for lib_name in ext.libraries[:]:
                ext.libraries.extend(build_flib.get_library_names(lib_name))
                ext.library_dirs.extend(build_flib.get_library_dirs(lib_name))
            
            ext.library_dirs.append(build_flib.build_flib)
            runtime_dirs = build_flib.get_runtime_library_dirs()
            ext.runtime_library_dirs.extend(runtime_dirs or [])
            
            linker_so = build_flib.fcompiler.get_linker_so()
            if linker_so is not None:
                if linker_so is not save_linker_so:
                    print 'replacing linker_so %s with %s' %(save_linker_so,linker_so)
                    self.compiler.linker_so = linker_so
                    l = build_flib.get_fcompiler_library_names()
                    #l = self.compiler.libraries + l
                    self.compiler.libraries = l
                    l = build_flib.get_fcompiler_library_dirs()
                    #l = self.compiler.library_dirs + l
                    self.compiler.library_dirs = l

        # end of fortran source support
        res = old_build_ext.build_extension(self,ext)

        if save_linker_so is not self.compiler.linker_so:
            print 'restoring linker_so',save_linker_so
            self.compiler.linker_so = save_linker_so
            self.compiler.libraries = save_compiler_libs
            self.compiler.library_dirs = save_compiler_libs_dirs

        return res

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
    file = os.path.basename(file)
    return fnmatch(file,"setup.py")
#    return (fnmatch(file,"setup.py") or fnmatch(file,"setup_*.py"))
    
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
           'run_f2py',
           'install',
           'install_data',
           'install_headers',
           'sdist',
          ] + distutils_all

from distutils.command.sdist import *
from distutils.command.sdist import sdist as old_sdist

import sys, os
mod = __import__(__name__)
sys.path.append(os.path.dirname(mod.__file__))
import line_endings
sys.path = sys.path[:-1]

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
            self.convert_line_endings(base_dir,fmt)
            file = self.make_archive(base_name, fmt, base_dir=base_dir)
            archive_files.append(file)
                    
        self.archive_files = archive_files

        if not self.keep_temp:
            dir_util.remove_tree(base_dir, self.verbose, self.dry_run)

    def convert_line_endings(self,base_dir,fmt):
        """ Convert all text files in a tree to have correct line endings.
            
            gztar --> \n   (Unix style)
            zip   --> \r\n (Windows style)
        """
        if fmt == 'gztar':
            line_endings.dos2unix_dir(base_dir)
        elif fmt == 'zip':
            line_endings.unix2dos_dir(base_dir)
            
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

"""distutils.command.run_f2py

Implements the Distutils 'run_f2py' command.
"""

# created 2002/01/09, Pearu Peterson 

__revision__ = "$Id$"

from distutils.dep_util import newer
from scipy_distutils.core import Command

import re,os

module_name_re = re.compile(r'\s*python\s*module\s*(?P<name>[\w_]+)',re.I).match
user_module_name_re = re.compile(r'\s*python\s*module\s*(?P<name>[\w_]*?__user__[\w_]*)',re.I).match
fortran_ext_re = re.compile(r'.*[.](f90|f95|f77|for|ftn|f)\Z',re.I).match

class run_f2py(Command):

    description = "\"run_f2py\" runs f2py that builds Fortran wrapper sources"\
                  "(C and occasionally Fortran)."

    user_options = [('build-dir=', 'b',
                     "directory to build fortran wrappers to"),
                    ('debug-capi', None,
                     "generate C/API extensions with debugging code"),
                    ('no-wrap-functions', None,
                     "do not generate wrappers for Fortran functions,etc."),
                    ('force', 'f',
                     "forcibly build everything (ignore file timestamps)"),
                   ]

    def initialize_options (self):
        self.build_dir = None
        self.debug_capi = None
        self.force = None
        self.no_wrap_functions = None
        self.f2py_options = []
    # initialize_options()


    def finalize_options (self):
        self.set_undefined_options('build',
                                   ('build_temp', 'build_dir'),
                                   ('force', 'force'))

        self.f2py_options.extend(['--build-dir',self.build_dir])

        if self.debug_capi is not None:
            self.f2py_options.append('--debug-capi')
        if self.no_wrap_functions is not None:
            self.f2py_options.append('--no-wrap-functions')

    # finalize_options()

    def run (self):
        if self.distribution.has_ext_modules():
            # XXX: might need also
            #  build_flib = self.get_finalized_command('build_flib')
            #  ...
            # for getting extra f2py_options that are specific to
            # a given fortran compiler.
            for ext in self.distribution.ext_modules:
                ext.sources = self.f2py_sources(ext.sources,ext)
                self.fortran_sources_to_flib(ext)
    # run()

    def f2py_sources (self, sources, ext):

        """Walk the list of source files in 'sources', looking for f2py
        interface (.pyf) files.  Run f2py on all that are found, and
        return a modified 'sources' list with f2py source files replaced
        by the generated C (or C++) and Fortran files.
        If 'sources' contains not .pyf files, then create a temporary
        one from the Fortran files in 'sources'.
        """
        import string
        import f2py2e
        # f2py generates the following files for an extension module
        # with a name <modulename>:
        #   <modulename>module.c
        #   <modulename>-f2pywrappers.f  [occasionally]
        # In addition, <f2py2e-dir>/src/fortranobject.{c,h} are needed
        # for building f2py generated extension modules.
        # It is assumed that one pyf file contains defintions for exactly
        # one extension module.

        target_dir = self.build_dir
        
        new_sources = []
        f2py_sources = []
        fortran_sources = []
        f2py_targets = {}
        f2py_fortran_targets = {}
        target_ext = 'module.c'
        fortran_target_ext = '-f2pywrappers.f'

        for source in sources:
            (base, source_ext) = os.path.splitext(source)
            (source_dir, base) = os.path.split(base)
            if source_ext == ".pyf":                  # f2py interface file
                # get extension module name
                f = open(source)
                for line in f.xreadlines():
                    m = module_name_re(line)
                    if m:
                        if user_module_name_re(line): # skip *__user__* names
                            continue
                        base = m.group('name')
                        break
                f.close()
                if ext.name == 'untitled':
                    ext.name = base
                if base != string.split(ext.name,'.')[-1]:
                    # XXX: Should we do here more than just warn?
                    self.warn('%s provides %s but this extension is %s' \
                              % (source,`base`,`ext.name`))
                target_file = os.path.join(target_dir,base+target_ext)
                fortran_target_file = os.path.join(target_dir,base+fortran_target_ext)
                f2py_sources.append(source)
                f2py_targets[source] = target_file
                f2py_fortran_targets[source] = fortran_target_file
            elif fortran_ext_re(source_ext):
                fortran_sources.append(source)                
            else:
                new_sources.append(source)

        if not (f2py_sources or fortran_sources):
            return new_sources

        # make sure the target dir exists
        from distutils.dir_util import mkpath
        mkpath(target_dir)

        if not f2py_sources:
            # creating a temporary pyf file from fortran sources
            pyf_target = os.path.join(target_dir,ext.name+'.pyf')
            pyf_target_file = os.path.join(target_dir,ext.name+target_ext)
            pyf_fortran_target_file = os.path.join(target_dir,ext.name+fortran_target_ext)
            f2py_opts2 = ['-m',ext.name,'-h',pyf_target,'--overwrite-signature']
            for source in fortran_sources:
                if newer(source,pyf_target) or self.force:
                    self.announce("f2py-ing a new %s" % (pyf_target))
                    self.announce("f2py-opts: %s" % string.join(f2py_opts2,' '))
                    f2py2e.run_main(fortran_sources + f2py_opts2)
                    break
            f2py_sources.append(pyf_target)
            f2py_targets[pyf_target] = pyf_target_file
            f2py_fortran_targets[pyf_target] = pyf_fortran_target_file

        new_sources.extend(fortran_sources)

        if len(f2py_sources) > 1:
            self.warn('Only one .pyf file can be used per Extension but got %s.'\
                      % (len(f2py_sources)))

        # a bit of a hack, but I think it'll work.  Just include one of
        # the fortranobject.c files that was copied into most 
        d = os.path.dirname(f2py2e.__file__)
        new_sources.append(os.path.join(d,'src','fortranobject.c'))
        ext.include_dirs.append(os.path.join(d,'src'))

        f2py_options = ext.f2py_options + self.f2py_options

        for source in f2py_sources:
            target = f2py_targets[source]
            fortran_target = f2py_fortran_targets[source]
            if newer(source,target) or self.force:
                self.announce("f2py-ing %s to %s" % (source, target))
                self.announce("f2py-opts: %s" % string.join(f2py_options,' '))
                f2py2e.run_main(f2py_options + [source])
            new_sources.append(target)
            if os.path.exists(fortran_target):
                new_sources.append(fortran_target)

        return new_sources

    # f2py_sources ()

    def fortran_sources_to_flib(self, ext):
        """
        Extract fortran files from ext.sources and append them to
        fortran_libraries item having the same name as ext.
        """
        sources = []
        f_files = []

        for file in ext.sources:
            if fortran_ext_re(file):
                f_files.append(file)
            else:
                sources.append(file)
        if not f_files:
            return

        ext.sources = sources

        if self.distribution.fortran_libraries is None:
            self.distribution.fortran_libraries = []
        fortran_libraries = self.distribution.fortran_libraries

        name = ext.name
        flib = None
        for n,d in fortran_libraries:
            if n == name:
                flib = d
                break
        if flib is None:
            flib = {'sources':[]}
            fortran_libraries.append((name,flib))

        flib['sources'].extend(f_files)
        
# class run_f2py

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
            print type(libraries)
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
      Intel
      Itanium
      NAG
      Compaq
      Gnu
      VAST
"""

import distutils
import distutils.dep_util, distutils.dir_util
import os,sys,string
import commands,re
from types import *
from distutils.command.build_clib import build_clib
from distutils.errors import *

class FortranCompilerError (CCompilerError):
    """Some compile/link operation failed."""
class FortranCompileError (FortranCompilerError):
    """Failure to compile one or more Fortran source files."""

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
        if self.has_f_libraries():
            self.fortran_libraries = self.distribution.fortran_libraries
            self.check_library_list(self.fortran_libraries)

    # finalize_options()

    def has_f_libraries(self):
        return self.distribution.fortran_libraries \
               and len(self.distribution.fortran_libraries) > 0

    def run (self):
        if not self.has_f_libraries():
            return
        self.build_libraries(self.fortran_libraries)

    # run ()

    def has_f_library(self,name):
        if self.has_f_libraries():
            for (lib_name, build_info) in self.fortran_libraries:
                if lib_name == name:
                    return 1
        
    def get_library_names(self, name=None):
        if not self.has_f_libraries():
            return None

        lib_names = []

        if name is None:
            for (lib_name, build_info) in self.fortran_libraries:
                lib_names.append(lib_name)

            if self.fcompiler is not None:
                lib_names.extend(self.fcompiler.get_libraries())
        else:
            for (lib_name, build_info) in self.fortran_libraries:
                if name != lib_name: continue
                for n in build_info.get('libraries',[]):
                    lib_names.append(n)
                    #XXX: how to catch recursive calls here?
                    lib_names.extend(self.get_library_names(n))
                break
        return lib_names

    def get_fcompiler_library_names(self):
        if not self.has_f_libraries():
            return None
        if self.fcompiler is not None:
            return self.fcompiler.get_libraries()
        return []

    def get_fcompiler_library_dirs(self):
        if not self.has_f_libraries():
            return None
        if self.fcompiler is not None:
            return self.fcompiler.get_library_dirs()
        return []

    # get_library_names ()

    def get_library_dirs(self, name=None):
        if not self.has_f_libraries():
            return []

        lib_dirs = [] 

        if name is None:
            if self.fcompiler is not None:
                lib_dirs.extend(self.fcompiler.get_library_dirs())
        else:
            for (lib_name, build_info) in self.fortran_libraries:
                if name != lib_name: continue
                lib_dirs.extend(build_info.get('library_dirs',[]))
                for n in build_info.get('libraries',[]):
                    lib_dirs.extend(self.get_library_dirs(n))
                break

        return lib_dirs

    # get_library_dirs ()

    def get_runtime_library_dirs(self):
        if not self.has_f_libraries():
            return []

        lib_dirs = []

        if self.fcompiler is not None:
            lib_dirs.extend(self.fcompiler.get_runtime_library_dirs())
            
        return lib_dirs

    # get_library_dirs ()

    def get_source_files (self):
        if not self.has_f_libraries():
            return []

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
                    raise FortranCompileError, 'failure during compile' 
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

        if os.name == 'nt':
            # This is pure bunk...
            # Windows fails for long argument strings on the command line.
            # if objects is real long (> 2048 chars or so on my machine),
            # the command fails (cmd.exe /e:2048 on w2k)
            # for now we'll split linking into to steps which should work for
            objects = object_list[:]
            while objects:
                obj,objects = objects[:20],objects[20:]
                self.create_static_lib(obj,library_name,temp_dir)
        else:
            self.create_static_lib(object_list,library_name,temp_dir)

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
        if sys.platform == 'win32':
            self.libraries = ['gcc','g2c']
            self.library_dirs = self.find_lib_directories()
        else:
            # On linux g77 does not need lib_directories to be specified.
            self.libraries = ['g2c']

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
        opt = ' -O3 -funroll-loops '
        
        # only check for more optimization if g77 can handle
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
            if cpu.is_Intel():
                opt = opt + ' -malign-double '                
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
        self.f77_switches = self.f77_switches + ' -FI -w90 -w95 '

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
        elif cpu.has_mmx():
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

        self.f77_switches = self.f90_switches = switches
        self.f77_switches = self.f77_switches + ' -fixed '
        self.f77_debug = self.f90_debug = debug
        self.f77_opt = self.f90_opt = self.get_opt()

        self.ver_cmd = self.f77_compiler+' -V '

    def get_opt(self):
        opt = ' -O4 -target=native '
        return opt

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

class compaq_fortran_compiler(fortran_compiler_base):

    vendor = 'Compaq'
    ver_match = r'Compaq Fortran (?P<version>[^\s]*)'

    def __init__(self, fc = None, f90c = None):
        fortran_compiler_base.__init__(self)

        if fc is None:
            fc = 'fort'
        if f90c is None:
            f90c = fc

        self.f77_compiler = fc
        self.f90_compiler = f90c

        switches = ' -assume no2underscore -nomixed_str_len_arg '
        debug = ' -g -check_bounds '

        self.f77_switches = self.f90_switches = switches
        self.f77_debug = self.f90_debug = debug
        self.f77_opt = self.f90_opt = self.get_opt()

        # XXX: uncomment if required
        #self.libraries = ' -lUfor -lfor -lFutil -lcpml -lots -lc '

        # XXX: fix the version showing flag
        self.ver_cmd = self.f77_compiler+' -V '

    def get_opt(self):
        opt = ' -O4 -align dcommons -arch host -assume bigarrays -assume nozsize -math_library fast -tune host '
        return opt

    def get_linker_so(self):
        # XXX: is -shared needed?
        return [self.f77_compiler,'-shared']


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
                 intel_ia32_fortran_compiler,
                 intel_itanium_fortran_compiler,
                 nag_fortran_compiler,
                 compaq_fortran_compiler,
                 vast_fortran_compiler,
                 gnu_fortran_compiler,
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

