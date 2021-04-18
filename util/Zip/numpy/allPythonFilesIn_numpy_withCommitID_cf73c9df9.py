"""
Wrapper functions to more user-friendly calling of certain math functions
whose output data-type is different than the input data-type in certain
domains of the input.
"""

__all__ = ['sqrt', 'log', 'log2', 'logn','log10', 'power', 'arccos',
           'arcsin', 'arctanh']

import numpy.core.numeric as nx
import numpy.core.numerictypes as nt
from numpy.core.numeric import asarray, any
from numpy.lib.type_check import isreal


#__all__.extend([key for key in dir(nx.umath)
#                if key[0] != '_' and key not in __all__])

_ln2 = nx.log(2.0)

def _tocomplex(arr):
    if isinstance(arr.dtype, (nt.single, nt.byte, nt.short, nt.ubyte,
                              nt.ushort)):
        return arr.astype(nt.csingle)
    else:
        return arr.astype(nt.cdouble)

def _fix_real_lt_zero(x):
    x = asarray(x)
    if any(isreal(x) & (x<0)):
        x = _tocomplex(x)
    return x

def _fix_int_lt_zero(x):
    x = asarray(x)
    if any(isreal(x) & (x < 0)):
        x = x * 1.0
    return x

def _fix_real_abs_gt_1(x):
    x = asarray(x)
    if any(isreal(x) & (abs(x)>1)):
        x = _tocomplex(x)
    return x

def sqrt(x):
    x = _fix_real_lt_zero(x)
    return nx.sqrt(x)

def log(x):
    x = _fix_real_lt_zero(x)
    return nx.log(x)

def log10(x):
    x = _fix_real_lt_zero(x)
    return nx.log10(x)

def logn(n, x):
    """ Take log base n of x.
    """
    x = _fix_real_lt_zero(x)
    n = _fix_real_lt_zero(n)
    return nx.log(x)/nx.log(n)

def log2(x):
    """ Take log base 2 of x.
    """
    x = _fix_real_lt_zero(x)
    return nx.log(x)/_ln2

def power(x, p):
    x = _fix_real_lt_zero(x)
    p = _fix_int_lt_zero(p)
    return nx.power(x, p)

def arccos(x):
    x = _fix_real_abs_gt_1(x)
    return nx.arccos(x)

def arcsin(x):
    x = _fix_real_abs_gt_1(x)
    return nx.arcsin(x)

def arctanh(x):
    x = _fix_real_abs_gt_1(x)
    return nx.arctanh(x)


__all__ = ['savetxt', 'loadtxt',
           'loads', 'load',
           'save',
           'DataSource',
          ]

import numpy as np

from cPickle import load as _cload, loads
from _datasource import DataSource
_file = file

def load(file):
    """Load a binary file.

    Read a binary file (either a pickle or a binary NumPy array file .npy) and
    return the resulting arrays. 

    Parameters:
    -----------
    file - the file to read. This can be a string, or any file-like object

    Returns:
    --------
    result - array or tuple of arrays stored in the file.  If file contains 
             pickle data, then whatever is stored in the pickle is returned.
    """
    if isinstance(file, type("")):
        file = _file(file,"rb")
    # Code to distinguish from pickle and NumPy binary

    # if pickle:
        return _cload(file)



class _bagobj(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

class _npz_obj(dict):
    pass

def save(file, arr):
    """Save an array to a binary file (specified as a string or file-like object).

    If the file is a string, then if it does not have the .npy extension, it is appended
        and a file open. 

    Data is saved to the open file in NumPy-array format

    Example:
    --------
    import numpy as np
    ...
    np.save('myfile', a)
    a = np.load('myfile.npy')
    """    
    # code to save to numpy binary here...

    

# Adapted from matplotlib

def _getconv(dtype):
    typ = dtype.type
    if issubclass(typ, np.bool_):
        return lambda x: bool(int(x))
    if issubclass(typ, np.integer):
        return int
    elif issubclass(typ, np.floating):
        return float
    elif issubclass(typ, np.complex):
        return complex
    else:
        return str


def _string_like(obj):
    try: obj + ''
    except (TypeError, ValueError): return 0
    return 1

def loadtxt(fname, dtype=float, comments='#', delimiter=None, converters=None,
            skiprows=0, usecols=None, unpack=False):
    """
    Load ASCII data from fname into an array and return the array.

    The data must be regular, same number of values in every row

    fname can be a filename or a file handle.  Support for gzipped files is
    automatic, if the filename ends in .gz

    See scipy.io.loadmat to read and write matfiles.

    Example usage:

      X = loadtxt('test.dat')  # data in two columns
      t = X[:,0]
      y = X[:,1]

    Alternatively, you can do the same with "unpack"; see below

      X = loadtxt('test.dat')    # a matrix of data
      x = loadtxt('test.dat')    # a single column of data


    dtype - the data-type of the resulting array.  If this is a
    record data-type, the the resulting array will be 1-d and each row will
    be interpreted as an element of the array. The number of columns
    used must match the number of fields in the data-type in this case.

    comments - the character used to indicate the start of a comment
    in the file

    delimiter is a string-like character used to seperate values in the
    file. If delimiter is unspecified or none, any whitespace string is
    a separator.

    converters, if not None, is a dictionary mapping column number to
    a function that will convert that column to a float.  Eg, if
    column 0 is a date string: converters={0:datestr2num}

    skiprows is the number of rows from the top to skip

    usecols, if not None, is a sequence of integer column indexes to
    extract where 0 is the first column, eg usecols=(1,4,5) to extract
    just the 2nd, 5th and 6th columns

    unpack, if True, will transpose the matrix allowing you to unpack
    into named arguments on the left hand side

        t,y = load('test.dat', unpack=True) # for  two column data
        x,y,z = load('somefile.dat', usecols=(3,5,7), unpack=True)

    """

    if _string_like(fname):
        if fname.endswith('.gz'):
            import gzip
            fh = gzip.open(fname)
        else:
            fh = file(fname)
    elif hasattr(fname, 'seek'):
        fh = fname
    else:
        raise ValueError('fname must be a string or file handle')
    X = []

    dtype = np.dtype(dtype)
    defconv = _getconv(dtype)
    converterseq = None
    if converters is None:
        converters = {}
        if dtype.names is not None:
            converterseq = [_getconv(dtype.fields[name][0]) \
                            for name in dtype.names]

    for i,line in enumerate(fh):
        if i<skiprows: continue
        line = line[:line.find(comments)].strip()
        if not len(line): continue
        vals = line.split(delimiter)
        if converterseq is None:
            converterseq = [converters.get(j,defconv) \
                            for j in xrange(len(vals))]
        if usecols is not None:
            row = [converterseq[j](vals[j]) for j in usecols]
        else:
            row = [converterseq[j](val) for j,val in enumerate(vals)]
        if dtype.names is not None:
            row = tuple(row)
        X.append(row)

    X = np.array(X, dtype)
    r,c = X.shape
    if r==1 or c==1:
        X.shape = max([r,c]),
    if unpack: return X.T
    else:  return X


# adjust so that fmt can change across columns if desired.

def savetxt(fname, X, fmt='%.18e',delimiter=' '):
    """
    Save the data in X to file fname using fmt string to convert the
    data to strings

    fname can be a filename or a file handle.  If the filename ends in .gz,
    the file is automatically saved in compressed gzip format.  The load()
    command understands gzipped files transparently.

    Example usage:

    save('test.out', X)         # X is an array
    save('test1.out', (x,y,z))  # x,y,z equal sized 1D arrays
    save('test2.out', x)        # x is 1D
    save('test3.out', x, fmt='%1.4e')  # use exponential notation

    delimiter is used to separate the fields, eg delimiter ',' for
    comma-separated values
    """

    if _string_like(fname):
        if fname.endswith('.gz'):
            import gzip
            fh = gzip.open(fname,'wb')
        else:
            fh = file(fname,'w')
    elif hasattr(fname, 'seek'):
        fh = fname
    else:
        raise ValueError('fname must be a string or file handle')


    X = np.asarray(X)
    origShape = None
    if len(X.shape)==1:
        origShape = X.shape
        X.shape = len(X), 1
    for row in X:
        fh.write(delimiter.join([fmt%val for val in row]) + '\n')

    if origShape is not None:
        X.shape = origShape





"""
Standard container-class for easy multiple-inheritance.
Try to inherit from the ndarray instead of using this class as this is not
complete.
"""

from numpy.core import array, asarray, absolute, add, subtract, multiply, \
     divide, remainder, power, left_shift, right_shift, bitwise_and, \
     bitwise_or, bitwise_xor, invert, less, less_equal, not_equal, equal, \
     greater, greater_equal, shape, reshape, arange, sin, sqrt, transpose

class container(object):
    def __init__(self, data, dtype=None, copy=True):
        self.array = array(data, dtype, copy=copy)

    def __repr__(self):
        if len(self.shape) > 0:
            return self.__class__.__name__+repr(self.array)[len("array"):]
        else:
            return self.__class__.__name__+"("+repr(self.array)+")"

    def __array__(self,t=None):
        if t: return self.array.astype(t)
        return self.array

    # Array as sequence
    def __len__(self): return len(self.array)

    def __getitem__(self, index):
        return self._rc(self.array[index])

    def __getslice__(self, i, j):
        return self._rc(self.array[i:j])


    def __setitem__(self, index, value):
        self.array[index] = asarray(value,self.dtype)
    def __setslice__(self, i, j, value):
        self.array[i:j] = asarray(value,self.dtype)

    def __abs__(self):
        return self._rc(absolute(self.array))
    def __neg__(self):
        return self._rc(-self.array)

    def __add__(self, other):
        return self._rc(self.array+asarray(other))
    __radd__ = __add__

    def __iadd__(self, other):
        add(self.array, other, self.array)
        return self

    def __sub__(self, other):
        return self._rc(self.array-asarray(other))
    def __rsub__(self, other):
        return self._rc(asarray(other)-self.array)
    def __isub__(self, other):
        subtract(self.array, other, self.array)
        return self

    def __mul__(self, other):
        return self._rc(multiply(self.array,asarray(other)))
    __rmul__ = __mul__
    def __imul__(self, other):
        multiply(self.array, other, self.array)
        return self

    def __div__(self, other):
        return self._rc(divide(self.array,asarray(other)))
    def __rdiv__(self, other):
        return self._rc(divide(asarray(other),self.array))
    def __idiv__(self, other):
        divide(self.array, other, self.array)
        return self

    def __mod__(self, other):
        return self._rc(remainder(self.array, other))
    def __rmod__(self, other):
        return self._rc(remainder(other, self.array))
    def __imod__(self, other):
        remainder(self.array, other, self.array)
        return self

    def __divmod__(self, other):
        return (self._rc(divide(self.array,other)),
                self._rc(remainder(self.array, other)))
    def __rdivmod__(self, other):
        return (self._rc(divide(other, self.array)),
                self._rc(remainder(other, self.array)))

    def __pow__(self,other):
        return self._rc(power(self.array,asarray(other)))
    def __rpow__(self,other):
        return self._rc(power(asarray(other),self.array))
    def __ipow__(self,other):
        power(self.array, other, self.array)
        return self

    def __lshift__(self,other):
        return self._rc(left_shift(self.array, other))
    def __rshift__(self,other):
        return self._rc(right_shift(self.array, other))
    def __rlshift__(self,other):
        return self._rc(left_shift(other, self.array))
    def __rrshift__(self,other):
        return self._rc(right_shift(other, self.array))
    def __ilshift__(self,other):
        left_shift(self.array, other, self.array)
        return self
    def __irshift__(self,other):
        right_shift(self.array, other, self.array)
        return self

    def __and__(self, other):
        return self._rc(bitwise_and(self.array, other))
    def __rand__(self, other):
        return self._rc(bitwise_and(other, self.array))
    def __iand__(self, other):
        bitwise_and(self.array, other, self.array)
        return self

    def __xor__(self, other):
        return self._rc(bitwise_xor(self.array, other))
    def __rxor__(self, other):
        return self._rc(bitwise_xor(other, self.array))
    def __ixor__(self, other):
        bitwise_xor(self.array, other, self.array)
        return self

    def __or__(self, other):
        return self._rc(bitwise_or(self.array, other))
    def __ror__(self, other):
        return self._rc(bitwise_or(other, self.array))
    def __ior__(self, other):
        bitwise_or(self.array, other, self.array)
        return self

    def __neg__(self):
        return self._rc(-self.array)
    def __pos__(self):
        return self._rc(self.array)
    def __abs__(self):
        return self._rc(abs(self.array))
    def __invert__(self):
        return self._rc(invert(self.array))

    def _scalarfunc(self, func):
        if len(self.shape) == 0:
            return func(self[0])
        else:
            raise TypeError, "only rank-0 arrays can be converted to Python scalars."

    def __complex__(self): return self._scalarfunc(complex)
    def __float__(self): return self._scalarfunc(float)
    def __int__(self): return self._scalarfunc(int)
    def __long__(self): return self._scalarfunc(long)
    def __hex__(self): return self._scalarfunc(hex)
    def __oct__(self): return self._scalarfunc(oct)

    def __lt__(self,other): return self._rc(less(self.array,other))
    def __le__(self,other): return self._rc(less_equal(self.array,other))
    def __eq__(self,other): return self._rc(equal(self.array,other))
    def __ne__(self,other): return self._rc(not_equal(self.array,other))
    def __gt__(self,other): return self._rc(greater(self.array,other))
    def __ge__(self,other): return self._rc(greater_equal(self.array,other))

    def copy(self): return self._rc(self.array.copy())

    def tostring(self): return self.array.tostring()

    def byteswap(self): return self._rc(self.array.byteswap())

    def astype(self, typecode): return self._rc(self.array.astype(typecode))

    def _rc(self, a):
        if len(shape(a)) == 0: return a
        else: return self.__class__(a)

    def __array_wrap__(self, *args):
        return self.__class__(args[0])

    def __setattr__(self,attr,value):
        if attr == 'array':
            object.__setattr__(self, attr, value)
            return
        try:
            self.array.__setattr__(attr, value)
        except AttributeError:
            object.__setattr__(self, attr, value)

    # Only called after other approaches fail.
    def __getattr__(self,attr):
        if (attr == 'array'):
            return object.__getattribute__(self, attr)
        return self.array.__getattribute__(attr)

#############################################################
# Test of class container
#############################################################
if __name__ == '__main__':
    temp=reshape(arange(10000),(100,100))

    ua=container(temp)
    # new object created begin test
    print dir(ua)
    print shape(ua),ua.shape # I have changed Numeric.py

    ua_small=ua[:3,:5]
    print ua_small
    ua_small[0,0]=10  # this did not change ua[0,0], which is not normal behavior
    print ua_small[0,0],ua[0,0]
    print sin(ua_small)/3.*6.+sqrt(ua_small**2)
    print less(ua_small,103),type(less(ua_small,103))
    print type(ua_small*reshape(arange(15),shape(ua_small)))
    print reshape(ua_small,(5,3))
    print transpose(ua_small)

from info import __doc__
from numpy.version import version as __version__

from type_check import *
from index_tricks import *
from function_base import *
from shape_base import *
from twodim_base import *
from ufunclike import *

import scimath as emath
from polynomial import *
from machar import *
from getlimits import *
#import convertcode
from utils import *
from arraysetops import *
from io import *
import math

__all__ = ['emath','math']
__all__ += type_check.__all__
__all__ += index_tricks.__all__
__all__ += function_base.__all__
__all__ += shape_base.__all__
__all__ += twodim_base.__all__
__all__ += ufunclike.__all__
__all__ += polynomial.__all__
__all__ += machar.__all__
__all__ += getlimits.__all__
__all__ += utils.__all__
__all__ += arraysetops.__all__
__all__ += io.__all__

def test(level=1, verbosity=1):
    from numpy.testing import NumpyTest
    return NumpyTest().test(level, verbosity)

""" Basic functions for manipulating 2d arrays

"""

__all__ = ['diag','diagflat','eye','fliplr','flipud','rot90','tri','triu',
           'tril','vander','histogram2d']

from numpy.core.numeric import asanyarray, equal, subtract, arange, \
     zeros, arange, greater_equal, multiply, ones, asarray

def fliplr(m):
    """ returns an array m with the rows preserved and columns flipped
        in the left/right direction.  Works on the first two dimensions of m.
    """
    m = asanyarray(m)
    if m.ndim < 2:
        raise ValueError, "Input must be >= 2-d."
    return m[:, ::-1]

def flipud(m):
    """ returns an array with the columns preserved and rows flipped in
        the up/down direction.  Works on the first dimension of m.
    """
    m = asanyarray(m)
    if m.ndim < 1:
        raise ValueError, "Input must be >= 1-d."
    return m[::-1,...]

def rot90(m, k=1):
    """ returns the array found by rotating m by k*90
    degrees in the counterclockwise direction.  Works on the first two
    dimensions of m.
    """
    m = asanyarray(m)
    if m.ndim < 2:
        raise ValueError, "Input must >= 2-d."
    k = k % 4
    if k == 0: return m
    elif k == 1: return fliplr(m).swapaxes(0,1)
    elif k == 2: return fliplr(flipud(m))
    else: return fliplr(m.swapaxes(0,1))  # k==3

def eye(N, M=None, k=0, dtype=float):
    """ eye returns a N-by-M 2-d array where the  k-th diagonal is all ones,
        and everything else is zeros.
    """
    if M is None: M = N
    m = equal(subtract.outer(arange(N), arange(M)),-k)
    if m.dtype != dtype:
        m = m.astype(dtype)
    return m

def diag(v, k=0):
    """ returns a copy of the the k-th diagonal if v is a 2-d array
        or returns a 2-d array with v as the k-th diagonal if v is a
        1-d array.
    """
    v = asarray(v)
    s = v.shape
    if len(s)==1:
        n = s[0]+abs(k)
        res = zeros((n,n), v.dtype)
        if (k>=0):
            i = arange(0,n-k)
            fi = i+k+i*n
        else:
            i = arange(0,n+k)
            fi = i+(i-k)*n
        res.flat[fi] = v
        return res
    elif len(s)==2:
        N1,N2 = s
        if k >= 0:
            M = min(N1,N2-k)
            i = arange(0,M)
            fi = i+k+i*N2
        else:
            M = min(N1+k,N2)
            i = arange(0,M)
            fi = i + (i-k)*N2
        return v.flat[fi]
    else:
        raise ValueError, "Input must be 1- or 2-d."

def diagflat(v,k=0):
    try:
        wrap = v.__array_wrap__
    except AttributeError:
        wrap = None
    v = asarray(v).ravel()
    s = len(v)
    n = s + abs(k)
    res = zeros((n,n), v.dtype)
    if (k>=0):
        i = arange(0,n-k)
        fi = i+k+i*n
    else:
        i = arange(0,n+k)
        fi = i+(i-k)*n
    res.flat[fi] = v
    if not wrap:
        return res
    return wrap(res)

def tri(N, M=None, k=0, dtype=float):
    """ returns a N-by-M array where all the diagonals starting from
        lower left corner up to the k-th are all ones.
    """
    if M is None: M = N
    m = greater_equal(subtract.outer(arange(N), arange(M)),-k)
    return m.astype(dtype)

def tril(m, k=0):
    """ returns the elements on and below the k-th diagonal of m.  k=0 is the
        main diagonal, k > 0 is above and k < 0 is below the main diagonal.
    """
    m = asanyarray(m)
    out = multiply(tri(m.shape[0], m.shape[1], k=k, dtype=int),m)
    return out

def triu(m, k=0):
    """ returns the elements on and above the k-th diagonal of m.  k=0 is the
        main diagonal, k > 0 is above and k < 0 is below the main diagonal.
    """
    m = asanyarray(m)
    out = multiply((1-tri(m.shape[0], m.shape[1], k-1, int)),m)
    return out

# borrowed from John Hunter and matplotlib
def vander(x, N=None):
    """
    X = vander(x,N=None)

    The Vandermonde matrix of vector x.  The i-th column of X is the
    the i-th power of x.  N is the maximum power to compute; if N is
    None it defaults to len(x).

    """
    x = asarray(x)
    if N is None: N=len(x)
    X = ones( (len(x),N), x.dtype)
    for i in range(N-1):
        X[:,i] = x**(N-i-1)
    return X


def histogram2d(x,y, bins=10, range=None, normed=False, weights=None):
    """histogram2d(x,y, bins=10, range=None, normed=False) -> H, xedges, yedges

    Compute the 2D histogram from samples x,y.

    :Parameters:
      - `x,y` : Sample arrays (1D).
      - `bins` : Number of bins -or- [nbin x, nbin y] -or-
             [bin edges] -or- [x bin edges, y bin edges].
      - `range` : A sequence of lower and upper bin edges (default: [min, max]).
      - `normed` : Boolean, if False, return the number of samples in each bin,
                if True, returns the density.
      - `weights` : An array of weights. The weights are normed only if normed
                is True. Should weights.sum() not equal N, the total bin count \
                will not be equal to the number of samples.

    :Return:
      - `hist` :    Histogram array.
      - `xedges, yedges` : Arrays defining the bin edges.

    Example:
      >>> x = random.randn(100,2)
      >>> hist2d, xedges, yedges = histogram2d(x, bins = (6, 7))

    :SeeAlso: histogramdd
    """
    from numpy import histogramdd

    try:
        N = len(bins)
    except TypeError:
        N = 1

    if N != 1 and N != 2:
        xedges = yedges = asarray(bins, float)
        bins = [xedges, yedges]
    hist, edges = histogramdd([x,y], bins, range, normed, weights)
    return hist, edges[0], edges[1]

""" Machine limits for Float32 and Float64 and (long double) if available...
"""

__all__ = ['finfo','iinfo']

from machar import MachAr
import numpy.core.numeric as numeric
import numpy.core.numerictypes as ntypes
from numpy.core.numeric import array
import numpy as N

def _frz(a):
    """fix rank-0 --> rank-1"""
    if a.ndim == 0: a.shape = (1,)
    return a

_convert_to_float = {
    ntypes.csingle: ntypes.single,
    ntypes.complex_: ntypes.float_,
    ntypes.clongfloat: ntypes.longfloat
    }

class finfo(object):
    """Machine limits for floating point types.

    :Parameters:
        dtype : floating point type or instance

    :SeeAlso:
      - numpy.lib.machar.MachAr

    """

    _finfo_cache = {}

    def __new__(cls, dtype):
        obj = cls._finfo_cache.get(dtype,None)
        if obj is not None:
            return obj
        dtypes = [dtype]
        newdtype = numeric.obj2sctype(dtype)
        if newdtype is not dtype:
            dtypes.append(newdtype)
            dtype = newdtype
        if not issubclass(dtype, numeric.inexact):
            raise ValueError, "data type %r not inexact" % (dtype)
        obj = cls._finfo_cache.get(dtype,None)
        if obj is not None:
            return obj
        if not issubclass(dtype, numeric.floating):
            newdtype = _convert_to_float[dtype]
            if newdtype is not dtype:
                dtypes.append(newdtype)
                dtype = newdtype
        obj = cls._finfo_cache.get(dtype,None)
        if obj is not None:
            return obj
        obj = object.__new__(cls)._init(dtype)
        for dt in dtypes:
            cls._finfo_cache[dt] = obj
        return obj

    def _init(self, dtype):
        self.dtype = dtype
        if dtype is ntypes.double:
            itype = ntypes.int64
            fmt = '%24.16e'
            precname = 'double'
        elif dtype is ntypes.single:
            itype = ntypes.int32
            fmt = '%15.7e'
            precname = 'single'
        elif dtype is ntypes.longdouble:
            itype = ntypes.longlong
            fmt = '%s'
            precname = 'long double'
        else:
            raise ValueError, repr(dtype)

        machar = MachAr(lambda v:array([v], dtype),
                        lambda v:_frz(v.astype(itype))[0],
                        lambda v:array(_frz(v)[0], dtype),
                        lambda v: fmt % array(_frz(v)[0], dtype),
                        'numpy %s precision floating point number' % precname)

        for word in ['precision', 'iexp',
                     'maxexp','minexp','negep',
                     'machep']:
            setattr(self,word,getattr(machar, word))
        for word in ['tiny','resolution','epsneg']:
            setattr(self,word,getattr(machar, word).squeeze())
        self.max = machar.huge.flat[0]
        self.min = -self.max
        self.eps = machar.eps.flat[0]
        self.nexp = machar.iexp
        self.nmant = machar.it
        self.machar = machar
        self._str_tiny = machar._str_xmin
        self._str_max = machar._str_xmax
        self._str_epsneg = machar._str_epsneg
        self._str_eps = machar._str_eps
        self._str_resolution = machar._str_resolution
        return self

    def __str__(self):
        return '''\
Machine parameters for %(dtype)s
---------------------------------------------------------------------
precision=%(precision)3s   resolution=%(_str_resolution)s
machep=%(machep)6s   eps=     %(_str_eps)s
negep =%(negep)6s   epsneg=  %(_str_epsneg)s
minexp=%(minexp)6s   tiny=    %(_str_tiny)s
maxexp=%(maxexp)6s   max=     %(_str_max)s
nexp  =%(nexp)6s   min=       -max
---------------------------------------------------------------------
''' % self.__dict__


class iinfo:
    """Limits for integer types.

    :Parameters:
        type : integer type or instance

    """

    _min_vals = {}
    _max_vals = {}

    def __init__(self, type):
        self.dtype = N.dtype(type)
        self.kind = self.dtype.kind
        self.bits = self.dtype.itemsize * 8
        self.key = "%s%d" % (self.kind, self.bits)
        if not self.kind in 'iu':
            raise ValueError("Invalid integer data type.")

    def min(self):
        """Minimum value of given dtype."""
        if self.kind == 'u':
            return 0
        else:
            try:
                val = iinfo._min_vals[self.key]
            except KeyError:
                val = int(-(1L << (self.bits-1)))
                iinfo._min_vals[self.key] = val
            return val

    min = property(min)

    def max(self):
        """Maximum value of given dtype."""
        try:
            val = iinfo._max_vals[self.key]
        except KeyError:
            if self.kind == 'u':
                val = int((1L << self.bits) - 1)
            else:
                val = int((1L << (self.bits-1)) - 1)
            iinfo._max_vals[self.key] = val
        return val

    max = property(max)

if __name__ == '__main__':
    f = finfo(ntypes.single)
    print 'single epsilon:',f.eps
    print 'single tiny:',f.tiny
    f = finfo(ntypes.float)
    print 'float epsilon:',f.eps
    print 'float tiny:',f.tiny
    f = finfo(ntypes.longfloat)
    print 'longfloat epsilon:',f.eps
    print 'longfloat tiny:',f.tiny

from tokenize import  generate_tokens
import token
import sys
def insert(s1, s2, posn):
    """insert s1 into s2 at positions posn

    >>> insert("XX", "abcdef", [2, 4])
    'abXXcdXXef'
    """
    pieces = []
    start = 0
    for end in posn + [len(s2)]:
        pieces.append(s2[start:end])
        start = end
    return s1.join(pieces)

def insert_dtype(readline, output=None):
    """
    >>> from StringIO import StringIO
    >>> src = "zeros((2,3), dtype=float); zeros((2,3));"
    >>> insert_dtype(StringIO(src).readline)
    zeros((2,3), dtype=float); zeros((2,3), dtype=int);
    """
    if output is None:
        output = sys.stdout
    tokens = generate_tokens(readline)
    flag = 0
    parens = 0
    argno = 0
    posn = []
    nodtype = True
    prevtok = None
    kwarg = 0
    for (tok_type, tok, (srow, scol), (erow, ecol), line) in tokens:
        if not flag and tok_type == token.NAME and tok in ('zeros', 'ones', 'empty'):
            flag = 1
        else:
            if tok == '(':
                parens += 1
            elif tok == ')':
                parens -= 1
                if parens == 0:
                    if nodtype and argno < 1:
                        posn.append(scol)
                    argno = 0
                    flag = 0
                    nodtype = True
                    argno = 0
            elif tok == '=':
                kwarg = 1
                if prevtok == 'dtype':
                    nodtype = False
            elif tok == ',':
                argno += (parens == 1)
        if len(line) == ecol:
            output.write(insert(', dtype=int', line, posn))
            posn = []
        prevtok = tok

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

## Automatically adapted for numpy Sep 19, 2005 by convertcode.py

__all__ = ['unravel_index',
           'mgrid',
           'ogrid',
           'r_', 'c_', 's_',
           'index_exp', 'ix_',
           'ndenumerate','ndindex']

import sys
import numpy.core.numeric as _nx
from numpy.core.numeric import asarray, ScalarType, array
import math

import function_base
import numpy.core.defmatrix as matrix
makemat = matrix.matrix

# contributed by Stefan van der Walt
def unravel_index(x,dims):
    """Convert a flat index into an index tuple for an array of given shape.

    e.g. for a 2x2 array, unravel_index(2,(2,2)) returns (1,0).

    Example usage:
      p = x.argmax()
      idx = unravel_index(p,x.shape)
      x[idx] == x.max()

    Note:  x.flat[p] == x.max()

      Thus, it may be easier to use flattened indexing than to re-map
      the index to a tuple.
    """
    if x > _nx.prod(dims)-1 or x < 0:
        raise ValueError("Invalid index, must be 0 <= x <= number of elements.")

    idx = _nx.empty_like(dims)

    # Take dimensions
    # [a,b,c,d]
    # Reverse and drop first element
    # [d,c,b]
    # Prepend [1]
    # [1,d,c,b]
    # Calculate cumulative product
    # [1,d,dc,dcb]
    # Reverse
    # [dcb,dc,d,1]
    dim_prod = _nx.cumprod([1] + list(dims)[:0:-1])[::-1]
    # Indeces become [x/dcb % a, x/dc % b, x/d % c, x/1 % d]
    return tuple(x/dim_prod % dims)

def ix_(*args):
    """ Construct an open mesh from multiple sequences.

    This function takes n 1-d sequences and returns n outputs with n
    dimensions each such that the shape is 1 in all but one dimension and
    the dimension with the non-unit shape value cycles through all n
    dimensions.

    Using ix_() one can quickly construct index arrays that will index
    the cross product.

    a[ix_([1,3,7],[2,5,8])]  returns the array

    a[1,2]  a[1,5]  a[1,8]
    a[3,2]  a[3,5]  a[3,8]
    a[7,2]  a[7,5]  a[7,8]
    """
    out = []
    nd = len(args)
    baseshape = [1]*nd
    for k in range(nd):
        new = _nx.asarray(args[k])
        if (new.ndim != 1):
            raise ValueError, "Cross index must be 1 dimensional"
        if issubclass(new.dtype.type, _nx.bool_):
            new = new.nonzero()[0]
        baseshape[k] = len(new)
        new = new.reshape(tuple(baseshape))
        out.append(new)
        baseshape[k] = 1
    return tuple(out)

class nd_grid(object):
    """ Construct a "meshgrid" in N-dimensions.

        grid = nd_grid() creates an instance which will return a mesh-grid
        when indexed.  The dimension and number of the output arrays are equal
        to the number of indexing dimensions.  If the step length is not a
        complex number, then the stop is not inclusive.

        However, if the step length is a COMPLEX NUMBER (e.g. 5j), then the
        integer part of it's magnitude is interpreted as specifying the
        number of points to create between the start and stop values, where
        the stop value IS INCLUSIVE.

        If instantiated with an argument of sparse=True, the mesh-grid is
        open (or not fleshed out) so that only one-dimension of each returned
        argument is greater than 1

        Example:

           >>> mgrid = nd_grid()
           >>> mgrid[0:5,0:5]
           array([[[0, 0, 0, 0, 0],
                   [1, 1, 1, 1, 1],
                   [2, 2, 2, 2, 2],
                   [3, 3, 3, 3, 3],
                   [4, 4, 4, 4, 4]],
           <BLANKLINE>
                  [[0, 1, 2, 3, 4],
                   [0, 1, 2, 3, 4],
                   [0, 1, 2, 3, 4],
                   [0, 1, 2, 3, 4],
                   [0, 1, 2, 3, 4]]])
           >>> mgrid[-1:1:5j]
           array([-1. , -0.5,  0. ,  0.5,  1. ])

           >>> ogrid = nd_grid(sparse=True)
           >>> ogrid[0:5,0:5]
           [array([[0],
                  [1],
                  [2],
                  [3],
                  [4]]), array([[0, 1, 2, 3, 4]])]

    """
    def __init__(self, sparse=False):
        self.sparse = sparse
    def __getitem__(self,key):
        try:
            size = []
            typ = int
            for k in range(len(key)):
                step = key[k].step
                start = key[k].start
                if start is None: start=0
                if step is None: step=1
                if isinstance(step, complex):
                    size.append(int(abs(step)))
                    typ = float
                else:
                    size.append(math.ceil((key[k].stop - start)/(step*1.0)))
                if isinstance(step, float) or \
                    isinstance(start, float) or \
                    isinstance(key[k].stop, float):
                    typ = float
            if self.sparse:
                nn = map(lambda x,t: _nx.arange(x, dtype=t), size, \
                                     (typ,)*len(size))
            else:
                nn = _nx.indices(size, typ)
            for k in range(len(size)):
                step = key[k].step
                start = key[k].start
                if start is None: start=0
                if step is None: step=1
                if isinstance(step, complex):
                    step = int(abs(step))
                    if step != 1:
                        step = (key[k].stop - start)/float(step-1)
                nn[k] = (nn[k]*step+start)
            if self.sparse:
                slobj = [_nx.newaxis]*len(size)
                for k in range(len(size)):
                    slobj[k] = slice(None,None)
                    nn[k] = nn[k][slobj]
                    slobj[k] = _nx.newaxis
            return nn
        except (IndexError, TypeError):
            step = key.step
            stop = key.stop
            start = key.start
            if start is None: start = 0
            if isinstance(step, complex):
                step = abs(step)
                length = int(step)
                if step != 1:
                    step = (key.stop-start)/float(step-1)
                stop = key.stop+step
                return _nx.arange(0, length,1, float)*step + start
            else:
                return _nx.arange(start, stop, step)

    def __getslice__(self,i,j):
        return _nx.arange(i,j)

    def __len__(self):
        return 0

mgrid = nd_grid(sparse=False)
ogrid = nd_grid(sparse=True)

class concatenator(object):
    """Translates slice objects to concatenation along an axis.
    """
    def _retval(self, res):
        if self.matrix:
            oldndim = res.ndim
            res = makemat(res)
            if oldndim == 1 and self.col:
                res = res.T
        self.axis = self._axis
        self.matrix = self._matrix
        self.col = 0
        return res

    def __init__(self, axis=0, matrix=False, ndmin=1, trans1d=-1):
        self._axis = axis
        self._matrix = matrix
        self.axis = axis
        self.matrix = matrix
        self.col = 0
        self.trans1d = trans1d
        self.ndmin = ndmin

    def __getitem__(self,key):
        trans1d = self.trans1d
        ndmin = self.ndmin
        if isinstance(key, str):
            frame = sys._getframe().f_back
            mymat = matrix.bmat(key,frame.f_globals,frame.f_locals)
            return mymat
        if type(key) is not tuple:
            key = (key,)
        objs = []
        scalars = []
        final_dtypedescr = None
        for k in range(len(key)):
            scalar = False
            if type(key[k]) is slice:
                step = key[k].step
                start = key[k].start
                stop = key[k].stop
                if start is None: start = 0
                if step is None:
                    step = 1
                if isinstance(step, complex):
                    size = int(abs(step))
                    newobj = function_base.linspace(start, stop, num=size)
                else:
                    newobj = _nx.arange(start, stop, step)
                if ndmin > 1:
                    newobj = array(newobj,copy=False,ndmin=ndmin)
                    if trans1d != -1:
                        newobj = newobj.swapaxes(-1,trans1d)
            elif isinstance(key[k],str):
                if k != 0:
                    raise ValueError, "special directives must be the"\
                          "first entry."
                key0 = key[0]
                if key0 in 'rc':
                    self.matrix = True
                    self.col = (key0 == 'c')
                    continue
                if ',' in key0:
                    vec = key0.split(',')
                    try:
                        self.axis, ndmin = \
                                   [int(x) for x in vec[:2]]
                        if len(vec) == 3:
                            trans1d = int(vec[2])
                        continue
                    except:
                        raise ValueError, "unknown special directive"
                try:
                    self.axis = int(key[k])
                    continue
                except (ValueError, TypeError):
                    raise ValueError, "unknown special directive"
            elif type(key[k]) in ScalarType:
                newobj = array(key[k],ndmin=ndmin)
                scalars.append(k)
                scalar = True
            else:
                newobj = key[k]
                if ndmin > 1:
                    tempobj = array(newobj, copy=False, subok=True)
                    newobj = array(newobj, copy=False, subok=True,
                                   ndmin=ndmin)
                    if trans1d != -1 and tempobj.ndim < ndmin:
                        k2 = ndmin-tempobj.ndim
                        if (trans1d < 0):
                            trans1d += k2 + 1
                        defaxes = range(ndmin)
                        k1 = trans1d
                        axes = defaxes[:k1] + defaxes[k2:] + \
                               defaxes[k1:k2]
                        newobj = newobj.transpose(axes)
                    del tempobj
            objs.append(newobj)
            if isinstance(newobj, _nx.ndarray) and not scalar:
                if final_dtypedescr is None:
                    final_dtypedescr = newobj.dtype
                elif newobj.dtype > final_dtypedescr:
                    final_dtypedescr = newobj.dtype
        if final_dtypedescr is not None:
            for k in scalars:
                objs[k] = objs[k].astype(final_dtypedescr)
        res = _nx.concatenate(tuple(objs),axis=self.axis)
        return self._retval(res)

    def __getslice__(self,i,j):
        res = _nx.arange(i,j)
        return self._retval(res)

    def __len__(self):
        return 0

# separate classes are used here instead of just making r_ = concatentor(0),
# etc. because otherwise we couldn't get the doc string to come out right
# in help(r_)

class r_class(concatenator):
    """Translates slice objects to concatenation along the first axis.

        For example:
        >>> r_[array([1,2,3]), 0, 0, array([4,5,6])]
        array([1, 2, 3, 0, 0, 4, 5, 6])

    """
    def __init__(self):
        concatenator.__init__(self, 0)

r_ = r_class()

class c_class(concatenator):
    """Translates slice objects to concatenation along the second axis.
    """
    def __init__(self):
        concatenator.__init__(self, -1, ndmin=2, trans1d=0)

c_ = c_class()

class ndenumerate(object):
    """
    A simple nd index iterator over an array.

    Example:
    >>> a = array([[1,2],[3,4]])
    >>> for index, x in ndenumerate(a):
    ...     print index, x
    (0, 0) 1
    (0, 1) 2
    (1, 0) 3
    (1, 1) 4
    """
    def __init__(self, arr):
        self.iter = asarray(arr).flat

    def next(self):
        return self.iter.coords, self.iter.next()

    def __iter__(self):
        return self


class ndindex(object):
    """Pass in a sequence of integers corresponding
    to the number of dimensions in the counter.  This iterator
    will then return an N-dimensional counter.

    Example:
    >>> for index in ndindex(3,2,1):
    ...     print index
    (0, 0, 0)
    (0, 1, 0)
    (1, 0, 0)
    (1, 1, 0)
    (2, 0, 0)
    (2, 1, 0)

    """

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], tuple):
            args = args[0]
        self.nd = len(args)
        self.ind = [0]*self.nd
        self.index = 0
        self.maxvals = args
        tot = 1
        for k in range(self.nd):
            tot *= args[k]
        self.total = tot

    def _incrementone(self, axis):
        if (axis < 0):  # base case
            return
        if (self.ind[axis] < self.maxvals[axis]-1):
            self.ind[axis] += 1
        else:
            self.ind[axis] = 0
            self._incrementone(axis-1)

    def ndincr(self):
        self._incrementone(self.nd-1)

    def next(self):
        if (self.index >= self.total):
            raise StopIteration
        val = tuple(self.ind)
        self.index += 1
        self.ndincr()
        return val

    def __iter__(self):
        return self




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

class _index_expression_class(object):
    """
    A nicer way to build up index tuples for arrays.

    For any index combination, including slicing and axis insertion,
    'a[indices]' is the same as 'a[index_exp[indices]]' for any
    array 'a'. However, 'index_exp[indices]' can be used anywhere
    in Python code and returns a tuple of slice objects that can be
    used in the construction of complex index expressions.
    """
    maxint = sys.maxint
    def __init__(self, maketuple):
        self.maketuple = maketuple

    def __getitem__(self, item):
        if self.maketuple and type(item) != type(()):
            return (item,)
        else:
            return item

    def __len__(self):
        return self.maxint

    def __getslice__(self, start, stop):
        if stop == self.maxint:
            stop = None
        return self[start:stop:None]

index_exp = _index_expression_class(1)
s_ = _index_expression_class(0)

# End contribution from Konrad.

__all__ = ['atleast_1d','atleast_2d','atleast_3d','vstack','hstack',
           'column_stack','row_stack', 'dstack','array_split','split','hsplit',
           'vsplit','dsplit','apply_over_axes','expand_dims',
           'apply_along_axis', 'kron', 'tile', 'get_array_wrap']

import numpy.core.numeric as _nx
from numpy.core.numeric import asarray, zeros, newaxis, outer, \
     concatenate, isscalar, array, asanyarray
from numpy.core.fromnumeric import product, reshape

def apply_along_axis(func1d,axis,arr,*args):
    """ Execute func1d(arr[i],*args) where func1d takes 1-D arrays
        and arr is an N-d array.  i varies so as to apply the function
        along the given axis for each 1-d subarray in arr.
    """
    arr = asarray(arr)
    nd = arr.ndim
    if axis < 0:
        axis += nd
    if (axis >= nd):
        raise ValueError("axis must be less than arr.ndim; axis=%d, rank=%d."
            % (axis,nd))
    ind = [0]*(nd-1)
    i = zeros(nd,'O')
    indlist = range(nd)
    indlist.remove(axis)
    i[axis] = slice(None,None)
    outshape = asarray(arr.shape).take(indlist)
    i.put(indlist, ind)
    res = func1d(arr[tuple(i.tolist())],*args)
    #  if res is a number, then we have a smaller output array
    if isscalar(res):
        outarr = zeros(outshape,asarray(res).dtype)
        outarr[tuple(ind)] = res
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
            i.put(indlist,ind)
            res = func1d(arr[tuple(i.tolist())],*args)
            outarr[tuple(ind)] = res
            k += 1
        return outarr
    else:
        Ntot = product(outshape)
        holdshape = outshape
        outshape = list(arr.shape)
        outshape[axis] = len(res)
        outarr = zeros(outshape,asarray(res).dtype)
        outarr[tuple(i.tolist())] = res
        k = 1
        while k < Ntot:
            # increment the index
            ind[-1] += 1
            n = -1
            while (ind[n] >= holdshape[n]) and (n > (1-nd)):
                ind[n-1] += 1
                ind[n] = 0
                n -= 1
            i.put(indlist, ind)
            res = func1d(arr[tuple(i.tolist())],*args)
            outarr[tuple(i.tolist())] = res
            k += 1
        return outarr


def apply_over_axes(func, a, axes):
    """Apply a function repeatedly over multiple axes, keeping the same shape
    for the resulting array.

    func is called as res = func(a, axis).  The result is assumed
    to be either the same shape as a or have one less dimension.
    This call is repeated for each axis in the axes sequence.
    """
    val = asarray(a)
    N = a.ndim
    if array(axes).ndim == 0:
        axes = (axes,)
    for axis in axes:
        if axis < 0: axis = N + axis
        args = (val, axis)
        res = func(*args)
        if res.ndim == val.ndim:
            val = res
        else:
            res = expand_dims(res,axis)
            if res.ndim == val.ndim:
                val = res
            else:
                raise ValueError, "function is not returning"\
                      " an array of correct shape"
    return val

def expand_dims(a, axis):
    """Expand the shape of a by including newaxis before given axis.
    """
    a = asarray(a)
    shape = a.shape
    if axis < 0:
        axis = axis + len(shape) + 1
    return a.reshape(shape[:axis] + (1,) + shape[axis:])


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
        res.append(array(ary,copy=False,subok=True,ndmin=1))
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
        res.append(array(ary,copy=False,subok=True,ndmin=2))
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
            result = ary.reshape(1,1,1)
        elif len(ary.shape) == 1:
            result = ary[newaxis,:,newaxis]
        elif len(ary.shape) == 2:
            result = ary[:,:,newaxis]
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
            Take a sequence of arrays and stack them vertically
            to make a single array.  All arrays in the sequence
            must have the same shape along all but the first axis.
            vstack will rebuild arrays divided by vsplit.
        Arguments:
            tup -- sequence of arrays.  All arrays must have the same
                   shape.
        Examples:
            >>> import numpy
            >>> a = array((1,2,3))
            >>> b = array((2,3,4))
            >>> numpy.vstack((a,b))
            array([[1, 2, 3],
                   [2, 3, 4]])
            >>> a = array([[1],[2],[3]])
            >>> b = array([[2],[3],[4]])
            >>> numpy.vstack((a,b))
            array([[1],
                   [2],
                   [3],
                   [2],
                   [3],
                   [4]])

    """
    return _nx.concatenate(map(atleast_2d,tup),0)

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
            >>> import numpy
            >>> a = array((1,2,3))
            >>> b = array((2,3,4))
            >>> numpy.hstack((a,b))
            array([1, 2, 3, 2, 3, 4])
            >>> a = array([[1],[2],[3]])
            >>> b = array([[2],[3],[4]])
            >>> numpy.hstack((a,b))
            array([[1, 2],
                   [2, 3],
                   [3, 4]])

    """
    return _nx.concatenate(map(atleast_1d,tup),1)

row_stack = vstack

def column_stack(tup):
    """ Stack 1D arrays as columns into a 2D array

        Description:
            Take a sequence of 1D arrays and stack them as columns
            to make a single 2D array.  All arrays in the sequence
            must have the same first dimension.  2D arrays are
            stacked as-is, just like with hstack.  1D arrays are turned
            into 2D columns first.

        Arguments:
            tup -- sequence of 1D or 2D arrays.  All arrays must have the same
                   first dimension.
        Examples:
            >>> import numpy
            >>> a = array((1,2,3))
            >>> b = array((2,3,4))
            >>> numpy.column_stack((a,b))
            array([[1, 2],
                   [2, 3],
                   [3, 4]])

    """
    arrays = []
    for v in tup:
        arr = array(v,copy=False,subok=True)
        if arr.ndim < 2:
            arr = array(arr,copy=False,subok=True,ndmin=2).T
        arrays.append(arr)
    return _nx.concatenate(arrays,1)

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
        >>> import numpy
        >>> a = array((1,2,3))
        >>> b = array((2,3,4))
        >>> numpy.dstack((a,b))
        array([[[1, 2],
                [2, 3],
                [3, 4]]])
        >>> a = array([[1],[2],[3]])
        >>> b = array([[2],[3],[4]])
        >>> numpy.dstack((a,b))
        array([[[1, 2]],
        <BLANKLINE>
               [[2, 3]],
        <BLANKLINE>
               [[3, 4]]])

    """
    return _nx.concatenate(map(atleast_3d,tup),2)

def _replace_zero_by_x_arrays(sub_arys):
    for i in range(len(sub_arys)):
        if len(_nx.shape(sub_arys[i])) == 0:
            sub_arys[i] = _nx.array([])
        elif _nx.sometrue(_nx.equal(_nx.shape(sub_arys[i]),0)):
            sub_arys[i] = _nx.array([])
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
           of rows.  This seems like the appropriate default,
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
        div_points = _nx.array(section_sizes).cumsum()

    sub_arys = []
    sary = _nx.swapaxes(ary,axis,0)
    for i in range(Nsections):
        st = div_points[i]; end = div_points[i+1]
        sub_arys.append(_nx.swapaxes(sary[st:end],axis,0))

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
           of rows.  This seems like the appropriate default
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
            >>> import numpy
            >>> a= array((1,2,3,4))
            >>> numpy.hsplit(a,2)
            [array([1, 2]), array([3, 4])]
            >>> a = array([[1,2,3,4],[1,2,3,4]])
            >>> hsplit(a,2)
            [array([[1, 2],
                   [1, 2]]), array([[3, 4],
                   [3, 4]])]

    """
    if len(_nx.shape(ary)) == 0:
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
            import numpy
            >>> a = array([[1,2,3,4],
            ...            [1,2,3,4]])
            >>> numpy.vsplit(a,2)
            [array([[1, 2, 3, 4]]), array([[1, 2, 3, 4]])]

    """
    if len(_nx.shape(ary)) < 2:
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
            >>> dsplit(a,2)
            [array([[[1, 2],
                    [1, 2]]]), array([[[3, 4],
                    [3, 4]]])]

    """
    if len(_nx.shape(ary)) < 3:
        raise ValueError, 'vsplit only works on arrays of 3 or more dimensions'
    return split(ary,indices_or_sections,2)

def get_array_wrap(*args):
    """Find the wrapper for the array with the highest priority.

    In case of ties, leftmost wins. If no wrapper is found, return None
    """
    wrappers = [(getattr(x, '__array_priority__', 0), -i,
                 x.__array_wrap__) for i, x in enumerate(args)
                                   if hasattr(x, '__array_wrap__')]
    wrappers.sort()
    if wrappers:
        return wrappers[-1][-1]
    return None

def kron(a,b):
    """kronecker product of a and b

    Kronecker product of two arrays is block array
    [[ a[ 0 ,0]*b, a[ 0 ,1]*b, ... , a[ 0 ,n-1]*b  ],
     [ ...                                   ...   ],
     [ a[m-1,0]*b, a[m-1,1]*b, ... , a[m-1,n-1]*b  ]]
    """
    wrapper = get_array_wrap(a, b)
    b = asanyarray(b)
    a = array(a,copy=False,subok=True,ndmin=b.ndim)
    ndb, nda = b.ndim, a.ndim
    if (nda == 0 or ndb == 0):
        return _nx.multiply(a,b)
    as_ = a.shape
    bs = b.shape
    if not a.flags.contiguous:
        a = reshape(a, as_)
    if not b.flags.contiguous:
        b = reshape(b, bs)
    nd = ndb
    if (ndb != nda):
        if (ndb > nda):
            as_ = (1,)*(ndb-nda) + as_
        else:
            bs = (1,)*(nda-ndb) + bs
            nd = nda
    result = outer(a,b).reshape(as_+bs)
    axis = nd-1
    for _ in xrange(nd):
        result = concatenate(result, axis=axis)
    if wrapper is not None:
        result = wrapper(result)
    return result


def tile(A, reps):
    """Repeat an array the number of times given in the integer tuple, reps.

    If reps has length d, the result will have dimension of max(d, A.ndim).
    If reps is scalar it is treated as a 1-tuple.

    If A.ndim < d, A is promoted to be d-dimensional by prepending new axes.
    So a shape (3,) array is promoted to (1,3) for 2-D replication,
    or shape (1,1,3) for 3-D replication.
    If this is not the desired behavior, promote A to d-dimensions manually
    before calling this function.

    If d < A.ndim, tup is promoted to A.ndim by pre-pending 1's to it.  Thus
    for an A.shape of (2,3,4,5), a tup of (2,2) is treated as (1,1,2,2)


    Examples:
    >>> a = array([0,1,2])
    >>> tile(a,2)
    array([0, 1, 2, 0, 1, 2])
    >>> tile(a,(1,2))
    array([[0, 1, 2, 0, 1, 2]])
    >>> tile(a,(2,2))
    array([[0, 1, 2, 0, 1, 2],
           [0, 1, 2, 0, 1, 2]])
    >>> tile(a,(2,1,2))
    array([[[0, 1, 2, 0, 1, 2]],
    <BLANKLINE>
           [[0, 1, 2, 0, 1, 2]]])

    See Also:
       repeat
    """
    try:
        tup = tuple(reps)
    except TypeError:
        tup = (reps,)
    d = len(tup)
    c = _nx.array(A,copy=False,subok=True,ndmin=d)
    shape = list(c.shape)
    n = max(c.size,1)
    if (d < c.ndim):
        tup = (1,)*(c.ndim-d) + tup
    for i, nrep in enumerate(tup):
        if nrep!=1:
            c = c.reshape(-1,n).repeat(nrep,0)
        dim_in = shape[i]
        dim_out = dim_in*nrep
        shape[i] = dim_out
        n /= max(dim_in,1)
    return c.reshape(shape)

"""
Machine arithmetics - determine the parameters of the
floating-point arithmetic system
"""
# Author: Pearu Peterson, September 2003


__all__ = ['MachAr']

from numpy.core.fromnumeric import any

# Need to speed this up...especially for longfloat

class MachAr(object):
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
    def __init__(self, float_conv=float,int_conv=int,
                 float_to_float=float,
                 float_to_str = lambda v:'%24.16e' % v,
                 title = 'Python floating point number'):
        """
          float_conv - convert integer to float (array)
          int_conv   - convert float (array) to integer
          float_to_float - convert float array to float
          float_to_str - convert array float to str
          title        - description of used floating point numbers
        """
        max_iterN = 10000
        msg = "Did not converge after %d tries with %s"
        one = float_conv(1)
        two = one + one
        zero = one - one

        # Do we really need to do this?  Aren't they 2 and 2.0?
        # Determine ibeta and beta
        a = one
        for _ in xrange(max_iterN):
            a = a + a
            temp = a + one
            temp1 = temp - a
            if any(temp1 - one != zero):
                break
        else:
            raise RuntimeError, msg % (_, one.dtype)
        b = one
        for _ in xrange(max_iterN):
            b = b + b
            temp = a + b
            itemp = int_conv(temp-a)
            if any(itemp != 0):
                break
        else:
            raise RuntimeError, msg % (_, one.dtype)
        ibeta = itemp
        beta = float_conv(ibeta)

        # Determine it and irnd
        it = -1
        b = one
        for _ in xrange(max_iterN):
            it = it + 1
            b = b * beta
            temp = b + one
            temp1 = temp - b
            if any(temp1 - one != zero):
                break
        else:
            raise RuntimeError, msg % (_, one.dtype)

        betah = beta / two
        a = one
        for _ in xrange(max_iterN):
            a = a + a
            temp = a + one
            temp1 = temp - a
            if any(temp1 - one != zero):
                break
        else:
            raise RuntimeError, msg % (_, one.dtype)
        temp = a + betah
        irnd = 0
        if any(temp-a != zero):
            irnd = 1
        tempa = a + beta
        temp = tempa + betah
        if irnd==0 and any(temp-tempa != zero):
            irnd = 2

        # Determine negep and epsneg
        negep = it + 3
        betain = one / beta
        a = one
        for i in range(negep):
            a = a * betain
        b = a
        for _ in xrange(max_iterN):
            temp = one - a
            if any(temp-one != zero):
                break
            a = a * beta
            negep = negep - 1
            # Prevent infinite loop on PPC with gcc 4.0:
            if negep < 0:
                raise RuntimeError, "could not determine machine tolerance " \
                                    "for 'negep', locals() -> %s" % (locals())
        else:
            raise RuntimeError, msg % (_, one.dtype)
        negep = -negep
        epsneg = a

        # Determine machep and eps
        machep = - it - 3
        a = b

        for _ in xrange(max_iterN):
            temp = one + a
            if any(temp-one != zero):
                break
            a = a * beta
            machep = machep + 1
        else:
            raise RuntimeError, msg % (_, one.dtype)
        eps = a

        # Determine ngrd
        ngrd = 0
        temp = one + eps
        if irnd==0 and any(temp*one - one != zero):
            ngrd = 1

        # Determine iexp
        i = 0
        k = 1
        z = betain
        t = one + eps
        nxres = 0
        for _ in xrange(max_iterN):
            y = z
            z = y*y
            a = z*one # Check here for underflow
            temp = z*t
            if any(a+a == zero) or any(abs(z)>=y):
                break
            temp1 = temp * betain
            if any(temp1*beta == z):
                break
            i = i + 1
            k = k + k
        else:
            raise RuntimeError, msg % (_, one.dtype)
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
        for _ in xrange(max_iterN):
            xmin = y
            y = y * betain
            a = y * one
            temp = y * t
            if any(a+a != zero) and any(abs(y) < xmin):
                k = k + 1
                temp1 = temp * betain
                if any(temp1*beta == y) and any(temp != y):
                    nxres = 3
                    xmin = y
                    break
            else:
                break
        else:
            raise RuntimeError, msg % (_, one.dtype)
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
        if any(a != y):
            maxexp = maxexp - 2
        xmax = one - epsneg
        if any(xmax*one != xmax):
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
        self._str_resolution = float_to_str(resolution)

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


if __name__ == '__main__':
    print MachAr()

from os.path import join

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration

    config = Configuration('lib',parent_package,top_path)

    config.add_include_dirs(join('..','core','include'))


    config.add_extension('_compiled_base',
                         sources=[join('src','_compiled_base.c')]
                         )

    config.add_data_dir('tests')

    return config

if __name__=='__main__':
    from numpy.distutils.core import setup
    setup(configuration=configuration)

import os
import sys
import inspect
import types
from numpy.core.numerictypes import obj2sctype, generic
from numpy.core.multiarray import dtype as _dtype
from numpy.core import product, ndarray

__all__ = ['issubclass_', 'get_numpy_include', 'issubsctype',
           'issubdtype', 'deprecate', 'deprecate_with_doc',
           'get_numarray_include',
           'get_include', 'info', 'source', 'who',
           'byte_bounds', 'may_share_memory']

def issubclass_(arg1, arg2):
    try:
        return issubclass(arg1, arg2)
    except TypeError:
        return False

def issubsctype(arg1, arg2):
    return issubclass(obj2sctype(arg1), obj2sctype(arg2))

def issubdtype(arg1, arg2):
    if issubclass_(arg2, generic):
        return issubclass(_dtype(arg1).type, arg2)
    mro = _dtype(arg2).type.mro()
    if len(mro) > 1:
        val = mro[1]
    else:
        val = mro[0]
    return issubclass(_dtype(arg1).type, val)

def get_include():
    """Return the directory in the package that contains the numpy/*.h header
    files.

    Extension modules that need to compile against numpy should use this
    function to locate the appropriate include directory. Using distutils:

      import numpy
      Extension('extension_name', ...
                include_dirs=[numpy.get_include()])
    """
    import numpy
    if numpy.show_config is None:
        # running from numpy source directory
        d = os.path.join(os.path.dirname(numpy.__file__), 'core', 'include')
    else:
        # using installed numpy core headers
        import numpy.core as core
        d = os.path.join(os.path.dirname(core.__file__), 'include')
    return d

def get_numarray_include(type=None):
    """Return the directory in the package that contains the numpy/*.h header
    files.

    Extension modules that need to compile against numpy should use this
    function to locate the appropriate include directory. Using distutils:

      import numpy
      Extension('extension_name', ...
                include_dirs=[numpy.get_numarray_include()])
    """
    from numpy.numarray import get_numarray_include_dirs
    include_dirs = get_numarray_include_dirs()
    if type is None:
        return include_dirs[0]
    else:
        return include_dirs + [get_include()]


if sys.version_info < (2, 4):
    # Can't set __name__ in 2.3
    import new
    def _set_function_name(func, name):
        func = new.function(func.func_code, func.func_globals,
                            name, func.func_defaults, func.func_closure)
        return func
else:
    def _set_function_name(func, name):
        func.__name__ = name
        return func

def deprecate(func, oldname=None, newname=None):
    """Deprecate old functions.
    Issues a DeprecationWarning, adds warning to oldname's docstring,
    rebinds oldname.__name__ and returns new function object.

    Example:
    oldfunc = deprecate(newfunc, 'oldfunc', 'newfunc')

    """

    import warnings
    if oldname is None:
        oldname = func.func_name
    if newname is None:
        str1 = "%s is deprecated" % (oldname,)
        depdoc = "%s is DEPRECATED!" % (oldname,)
    else:
        str1 = "%s is deprecated, use %s" % (oldname, newname),
        depdoc = '%s is DEPRECATED! -- use %s instead' % (oldname, newname,)
        
    def newfunc(*args,**kwds):
        warnings.warn(str1, DeprecationWarning)
        return func(*args, **kwds)

    newfunc = _set_function_name(newfunc, oldname)
    doc = func.__doc__
    if doc is None:
        doc = depdoc
    else:
        doc = '\n'.join([depdoc, doc])
    newfunc.__doc__ = doc
    try:
        d = func.__dict__
    except AttributeError:
        pass
    else:
        newfunc.__dict__.update(d)
    return newfunc

def deprecate_with_doc(somestr):
    """Decorator to deprecate functions and provide detailed documentation
    with 'somestr' that is added to the functions docstring.

    Example:
    depmsg = 'function numpy.lib.foo has been merged into numpy.lib.io.foobar'
    @deprecate_with_doc(depmsg)
    def foo():
        pass

    """

    def _decorator(func):
        newfunc = deprecate(func)
        newfunc.__doc__ += "\n" + somestr
        return newfunc
    return _decorator

get_numpy_include = deprecate(get_include, 'get_numpy_include', 'get_include')


#--------------------------------------------
# Determine if two arrays can share memory
#--------------------------------------------

def byte_bounds(a):
    """(low, high) are pointers to the end-points of an array

    low is the first byte
    high is just *past* the last byte

    If the array is not single-segment, then it may not actually
    use every byte between these bounds.

    The array provided must conform to the Python-side of the array interface
    """
    ai = a.__array_interface__
    a_data = ai['data'][0]
    astrides = ai['strides']
    ashape = ai['shape']
    nd_a = len(ashape)
    bytes_a = int(ai['typestr'][2:])

    a_low = a_high = a_data
    if astrides is None: # contiguous case
        a_high += product(ashape, dtype=int)*bytes_a
    else:
        for shape, stride in zip(ashape, astrides):
            if stride < 0:
                a_low += (shape-1)*stride
            else:
                a_high += (shape-1)*stride
        a_high += bytes_a
    return a_low, a_high


def may_share_memory(a, b):
    """Determine if two arrays can share memory

    The memory-bounds of a and b are computed.  If they overlap then
    this function returns True.  Otherwise, it returns False.

    A return of True does not necessarily mean that the two arrays
    share any element.  It just means that they *might*.
    """
    a_low, a_high = byte_bounds(a)
    b_low, b_high = byte_bounds(b)
    if b_low >= a_high or a_low >= b_high:
        return False
    return True

#-----------------------------------------------------------------------------
# Function for output and information on the variables used.
#-----------------------------------------------------------------------------


def who(vardict=None):
    """Print the Numpy arrays in the given dictionary (or globals() if None).
    """
    if vardict is None:
        frame = sys._getframe().f_back
        vardict = frame.f_globals
    sta = []
    cache = {}
    for name in vardict.keys():
        if isinstance(vardict[name],ndarray):
            var = vardict[name]
            idv = id(var)
            if idv in cache.keys():
                namestr = name + " (%s)" % cache[idv]
                original=0
            else:
                cache[idv] = name
                namestr = name
                original=1
            shapestr = " x ".join(map(str, var.shape))
            bytestr = str(var.itemsize*product(var.shape))
            sta.append([namestr, shapestr, bytestr, var.dtype.name,
                        original])

    maxname = 0
    maxshape = 0
    maxbyte = 0
    totalbytes = 0
    for k in range(len(sta)):
        val = sta[k]
        if maxname < len(val[0]):
            maxname = len(val[0])
        if maxshape < len(val[1]):
            maxshape = len(val[1])
        if maxbyte < len(val[2]):
            maxbyte = len(val[2])
        if val[4]:
            totalbytes += int(val[2])

    if len(sta) > 0:
        sp1 = max(10,maxname)
        sp2 = max(10,maxshape)
        sp3 = max(10,maxbyte)
        prval = "Name %s Shape %s Bytes %s Type" % (sp1*' ', sp2*' ', sp3*' ')
        print prval + "\n" + "="*(len(prval)+5) + "\n"

    for k in range(len(sta)):
        val = sta[k]
        print "%s %s %s %s %s %s %s" % (val[0], ' '*(sp1-len(val[0])+4),
                                        val[1], ' '*(sp2-len(val[1])+5),
                                        val[2], ' '*(sp3-len(val[2])+5),
                                        val[3])
    print "\nUpper bound on total bytes  =       %d" % totalbytes
    return

#-----------------------------------------------------------------------------


# NOTE:  pydoc defines a help function which works simliarly to this
#  except it uses a pager to take over the screen.

# combine name and arguments and split to multiple lines of
#  width characters.  End lines on a comma and begin argument list
#  indented with the rest of the arguments.
def _split_line(name, arguments, width):
    firstwidth = len(name)
    k = firstwidth
    newstr = name
    sepstr = ", "
    arglist = arguments.split(sepstr)
    for argument in arglist:
        if k == firstwidth:
            addstr = ""
        else:
            addstr = sepstr
        k = k + len(argument) + len(addstr)
        if k > width:
            k = firstwidth + 1 + len(argument)
            newstr = newstr + ",\n" + " "*(firstwidth+2) + argument
        else:
            newstr = newstr + addstr + argument
    return newstr

_namedict = None
_dictlist = None

# Traverse all module directories underneath globals
# to see if something is defined
def _makenamedict(module='numpy'):
    module = __import__(module, globals(), locals(), [])
    thedict = {module.__name__:module.__dict__}
    dictlist = [module.__name__]
    totraverse = [module.__dict__]
    while 1:
        if len(totraverse) == 0:
            break
        thisdict = totraverse.pop(0)
        for x in thisdict.keys():
            if isinstance(thisdict[x],types.ModuleType):
                modname = thisdict[x].__name__
                if modname not in dictlist:
                    moddict = thisdict[x].__dict__
                    dictlist.append(modname)
                    totraverse.append(moddict)
                    thedict[modname] = moddict
    return thedict, dictlist

def info(object=None,maxwidth=76,output=sys.stdout,toplevel='numpy'):
    """Get help information for a function, class, or module.

       Example:
          >>> from numpy import *
          >>> info(polyval) # doctest: +SKIP

          polyval(p, x)

            Evaluate the polymnomial p at x.

            Description:
                If p is of length N, this function returns the value:
                p[0]*(x**N-1) + p[1]*(x**N-2) + ... + p[N-2]*x + p[N-1]
    """
    global _namedict, _dictlist
    import pydoc

    if hasattr(object,'_ppimport_importer') or \
       hasattr(object, '_ppimport_module'):
        object = object._ppimport_module
    elif hasattr(object, '_ppimport_attr'):
        object = object._ppimport_attr

    if object is None:
        info(info)
    elif isinstance(object, ndarray):
        import numpy.numarray as nn
        nn.info(object, output=output, numpy=1)
    elif isinstance(object, str):
        if _namedict is None:
            _namedict, _dictlist = _makenamedict(toplevel)
        numfound = 0
        objlist = []
        for namestr in _dictlist:
            try:
                obj = _namedict[namestr][object]
                if id(obj) in objlist:
                    print >> output, "\n     *** Repeat reference found in %s *** " % namestr
                else:
                    objlist.append(id(obj))
                    print >> output, "     *** Found in %s ***" % namestr
                    info(obj)
                    print >> output, "-"*maxwidth
                numfound += 1
            except KeyError:
                pass
        if numfound == 0:
            print >> output, "Help for %s not found." % object
        else:
            print >> output, "\n     *** Total of %d references found. ***" % numfound

    elif inspect.isfunction(object):
        name = object.func_name
        arguments = inspect.formatargspec(*inspect.getargspec(object))

        if len(name+arguments) > maxwidth:
            argstr = _split_line(name, arguments, maxwidth)
        else:
            argstr = name + arguments

        print >> output, " " + argstr + "\n"
        print >> output, inspect.getdoc(object)

    elif inspect.isclass(object):
        name = object.__name__
        arguments = "()"
        try:
            if hasattr(object, '__init__'):
                arguments = inspect.formatargspec(*inspect.getargspec(object.__init__.im_func))
                arglist = arguments.split(', ')
                if len(arglist) > 1:
                    arglist[1] = "("+arglist[1]
                    arguments = ", ".join(arglist[1:])
        except:
            pass

        if len(name+arguments) > maxwidth:
            argstr = _split_line(name, arguments, maxwidth)
        else:
            argstr = name + arguments

        print >> output, " " + argstr + "\n"
        doc1 = inspect.getdoc(object)
        if doc1 is None:
            if hasattr(object,'__init__'):
                print >> output, inspect.getdoc(object.__init__)
        else:
            print >> output, inspect.getdoc(object)

        methods = pydoc.allmethods(object)
        if methods != []:
            print >> output, "\n\nMethods:\n"
            for meth in methods:
                if meth[0] == '_':
                    continue
                thisobj = getattr(object, meth, None)
                if thisobj is not None:
                    methstr, other = pydoc.splitdoc(inspect.getdoc(thisobj) or "None")
                print >> output, "  %s  --  %s" % (meth, methstr)

    elif type(object) is types.InstanceType: ## check for __call__ method
        print >> output, "Instance of class: ", object.__class__.__name__
        print >> output
        if hasattr(object, '__call__'):
            arguments = inspect.formatargspec(*inspect.getargspec(object.__call__.im_func))
            arglist = arguments.split(', ')
            if len(arglist) > 1:
                arglist[1] = "("+arglist[1]
                arguments = ", ".join(arglist[1:])
            else:
                arguments = "()"

            if hasattr(object,'name'):
                name = "%s" % object.name
            else:
                name = "<name>"
            if len(name+arguments) > maxwidth:
                argstr = _split_line(name, arguments, maxwidth)
            else:
                argstr = name + arguments

            print >> output, " " + argstr + "\n"
            doc = inspect.getdoc(object.__call__)
            if doc is not None:
                print >> output, inspect.getdoc(object.__call__)
            print >> output, inspect.getdoc(object)

        else:
            print >> output, inspect.getdoc(object)

    elif inspect.ismethod(object):
        name = object.__name__
        arguments = inspect.formatargspec(*inspect.getargspec(object.im_func))
        arglist = arguments.split(', ')
        if len(arglist) > 1:
            arglist[1] = "("+arglist[1]
            arguments = ", ".join(arglist[1:])
        else:
            arguments = "()"

        if len(name+arguments) > maxwidth:
            argstr = _split_line(name, arguments, maxwidth)
        else:
            argstr = name + arguments

        print >> output, " " + argstr + "\n"
        print >> output, inspect.getdoc(object)

    elif hasattr(object, '__doc__'):
        print >> output, inspect.getdoc(object)


def source(object, output=sys.stdout):
    """Write source for this object to output.
    """
    try:
        print >> output,  "In file: %s\n" % inspect.getsourcefile(object)
        print >> output,  inspect.getsource(object)
    except:
        print >> output,  "Not available for this object."

__docformat__ = "restructuredtext en"
__all__ = ['logspace', 'linspace',
           'select', 'piecewise', 'trim_zeros',
           'copy', 'iterable',
           'diff', 'gradient', 'angle', 'unwrap', 'sort_complex', 'disp',
           'unique', 'extract', 'place', 'nansum', 'nanmax', 'nanargmax',
           'nanargmin', 'nanmin', 'vectorize', 'asarray_chkfinite', 'average',
           'histogram', 'histogramdd', 'bincount', 'digitize', 'cov',
           'corrcoef', 'msort', 'median', 'sinc', 'hamming', 'hanning',
           'bartlett', 'blackman', 'kaiser', 'trapz', 'i0', 'add_newdoc',
           'add_docstring', 'meshgrid', 'delete', 'insert', 'append',
           'interp'
           ]

import types
import numpy.core.numeric as _nx
from numpy.core.numeric import ones, zeros, arange, concatenate, array, \
     asarray, asanyarray, empty, empty_like, asanyarray, ndarray, around
from numpy.core.numeric import ScalarType, dot, where, newaxis, intp, \
     integer, isscalar
from numpy.core.umath import pi, multiply, add, arctan2,  \
     frompyfunc, isnan, cos, less_equal, sqrt, sin, mod, exp, log10
from numpy.core.fromnumeric import ravel, nonzero, choose, sort
from numpy.core.numerictypes import typecodes
from numpy.lib.shape_base import atleast_1d, atleast_2d
from numpy.lib.twodim_base import diag
from _compiled_base import _insert, add_docstring
from _compiled_base import digitize, bincount, interp
from arraysetops import setdiff1d

#end Fernando's utilities

def linspace(start, stop, num=50, endpoint=True, retstep=False):
    """Return evenly spaced numbers.

    Return num evenly spaced samples from start to stop.  If
    endpoint is True, the last sample is stop. If retstep is
    True then return (seq, step_value), where step_value used.

    :Parameters:
        start : {float}
            The value the sequence starts at.
        stop : {float}
            The value the sequence stops at. If ``endpoint`` is false, then
            this is not included in the sequence. Otherwise it is
            guaranteed to be the last value.
        num : {integer}
            Number of samples to generate. Default is 50.
        endpoint : {boolean}
            If true, ``stop`` is the last sample. Otherwise, it is not
            included. Default is true.
        retstep : {boolean}
            If true, return ``(samples, step)``, where ``step`` is the
            spacing used in generating the samples.

    :Returns:
        samples : {array}
            ``num`` equally spaced samples from the range [start, stop]
            or [start, stop).
        step : {float} (Only if ``retstep`` is true)
            Size of spacing between samples.

    :See Also:
        `arange` : Similiar to linspace, however, when used with
            a float endpoint, that endpoint may or may not be included.
        `logspace`
    """
    num = int(num)
    if num <= 0:
        return array([], float)
    if endpoint:
        if num == 1:
            return array([float(start)])
        step = (stop-start)/float((num-1))
        y = _nx.arange(0, num) * step + start
        y[-1] = stop
    else:
        step = (stop-start)/float(num)
        y = _nx.arange(0, num) * step + start
    if retstep:
        return y, step
    else:
        return y

def logspace(start,stop,num=50,endpoint=True,base=10.0):
    """Evenly spaced numbers on a logarithmic scale.

    Computes int(num) evenly spaced exponents from base**start to
    base**stop. If endpoint=True, then last number is base**stop
    """
    y = linspace(start,stop,num=num,endpoint=endpoint)
    return _nx.power(base,y)

def iterable(y):
    try: iter(y)
    except: return 0
    return 1

def histogram(a, bins=10, range=None, normed=False):
    """Compute the histogram from a set of data.

    Parameters:

        a : array
            The data to histogram. n-D arrays will be flattened.

        bins : int or sequence of floats
            If an int, then the number of equal-width bins in the given range.
            Otherwise, a sequence of the lower bound of each bin.

        range : (float, float)
            The lower and upper range of the bins. If not provided, then
            (a.min(), a.max()) is used. Values outside of this range are
            allocated to the closest bin.

        normed : bool
            If False, the result array will contain the number of samples in
            each bin.  If True, the result array is the value of the
            probability *density* function at the bin normalized such that the
            *integral* over the range is 1. Note that the sum of all of the
            histogram values will not usually be 1; it is not a probability
            *mass* function.

    Returns:

        hist : array
            The values of the histogram. See `normed` for a description of the
            possible semantics.

        lower_edges : float array
            The lower edges of each bin.

    SeeAlso:

        histogramdd

    """
    a = asarray(a).ravel()

    if (range is not None):
        mn, mx = range
        if (mn > mx):
            raise AttributeError, 'max must be larger than min in range parameter.'

    if not iterable(bins):
        if range is None:
            range = (a.min(), a.max())
        mn, mx = [mi+0.0 for mi in range]
        if mn == mx:
            mn -= 0.5
            mx += 0.5
        bins = linspace(mn, mx, bins, endpoint=False)
    else:
        if(any(bins[1:]-bins[:-1] < 0)):
            raise AttributeError, 'bins must increase monotonically.'

    # best block size probably depends on processor cache size
    block = 65536
    n = sort(a[:block]).searchsorted(bins)
    for i in xrange(block, a.size, block):
        n += sort(a[i:i+block]).searchsorted(bins)
    n = concatenate([n, [len(a)]])
    n = n[1:]-n[:-1]

    if normed:
        db = bins[1] - bins[0]
        return 1.0/(a.size*db) * n, bins
    else:
        return n, bins

def histogramdd(sample, bins=10, range=None, normed=False, weights=None):
    """histogramdd(sample, bins=10, range=None, normed=False, weights=None)

    Return the N-dimensional histogram of the sample.

    Parameters:

        sample : sequence or array
            A sequence containing N arrays or an NxM array. Input data.

        bins : sequence or scalar
            A sequence of edge arrays, a sequence of bin counts, or a scalar
            which is the bin count for all dimensions. Default is 10.

        range : sequence
            A sequence of lower and upper bin edges. Default is [min, max].

        normed : boolean
            If False, return the number of samples in each bin, if True,
            returns the density.

        weights : array
            Array of weights.  The weights are normed only if normed is True.
            Should the sum of the weights not equal N, the total bin count will
            not be equal to the number of samples.

    Returns:

        hist : array
            Histogram array.

        edges : list
            List of arrays defining the lower bin edges.

    SeeAlso:

        histogram

    Example

        >>> x = random.randn(100,3)
        >>> hist3d, edges = histogramdd(x, bins = (5, 6, 7))

    """

    try:
        # Sample is an ND-array.
        N, D = sample.shape
    except (AttributeError, ValueError):
        # Sample is a sequence of 1D arrays.
        sample = atleast_2d(sample).T
        N, D = sample.shape

    nbin = empty(D, int)
    edges = D*[None]
    dedges = D*[None]
    if weights is not None:
        weights = asarray(weights)

    try:
        M = len(bins)
        if M != D:
            raise AttributeError, 'The dimension of bins must be a equal to the dimension of the sample x.'
    except TypeError:
        bins = D*[bins]

    # Select range for each dimension
    # Used only if number of bins is given.
    if range is None:
        smin = atleast_1d(array(sample.min(0), float))
        smax = atleast_1d(array(sample.max(0), float))
    else:
        smin = zeros(D)
        smax = zeros(D)
        for i in arange(D):
            smin[i], smax[i] = range[i]

    # Make sure the bins have a finite width.
    for i in arange(len(smin)):
        if smin[i] == smax[i]:
            smin[i] = smin[i] - .5
            smax[i] = smax[i] + .5

    # Create edge arrays
    for i in arange(D):
        if isscalar(bins[i]):
            nbin[i] = bins[i] + 2 # +2 for outlier bins
            edges[i] = linspace(smin[i], smax[i], nbin[i]-1)
        else:
            edges[i] = asarray(bins[i], float)
            nbin[i] = len(edges[i])+1  # +1 for outlier bins
        dedges[i] = diff(edges[i])

    nbin =  asarray(nbin)

    # Compute the bin number each sample falls into.
    Ncount = {}
    for i in arange(D):
        Ncount[i] = digitize(sample[:,i], edges[i])

    # Using digitize, values that fall on an edge are put in the right bin.
    # For the rightmost bin, we want values equal to the right
    # edge to be counted in the last bin, and not as an outlier.
    outliers = zeros(N, int)
    for i in arange(D):
        # Rounding precision
        decimal = int(-log10(dedges[i].min())) +6
        # Find which points are on the rightmost edge.
        on_edge = where(around(sample[:,i], decimal) == around(edges[i][-1], decimal))[0]
        # Shift these points one bin to the left.
        Ncount[i][on_edge] -= 1

    # Flattened histogram matrix (1D)
    hist = zeros(nbin.prod(), float)

    # Compute the sample indices in the flattened histogram matrix.
    ni = nbin.argsort()
    shape = []
    xy = zeros(N, int)
    for i in arange(0, D-1):
        xy += Ncount[ni[i]] * nbin[ni[i+1:]].prod()
    xy += Ncount[ni[-1]]

    # Compute the number of repetitions in xy and assign it to the flattened histmat.
    if len(xy) == 0:
        return zeros(nbin-2, int), edges

    flatcount = bincount(xy, weights)
    a = arange(len(flatcount))
    hist[a] = flatcount

    # Shape into a proper matrix
    hist = hist.reshape(sort(nbin))
    for i in arange(nbin.size):
        j = ni[i]
        hist = hist.swapaxes(i,j)
        ni[i],ni[j] = ni[j],ni[i]

    # Remove outliers (indices 0 and -1 for each dimension).
    core = D*[slice(1,-1)]
    hist = hist[core]

    # Normalize if normed is True
    if normed:
        s = hist.sum()
        for i in arange(D):
            shape = ones(D, int)
            shape[i] = nbin[i]-2
            hist = hist / dedges[i].reshape(shape)
        hist /= s

    return hist, edges


def average(a, axis=None, weights=None, returned=False):
    """Average the array over the given axis.  If the axis is None,
    average over all dimensions of the array.  Equivalent to
    a.mean(axis) and to

      a.sum(axis) / size(a, axis)

    If weights are given, result is:
        sum(a * weights,axis) / sum(weights,axis),
    where the weights must have a's shape or be 1D with length the
    size of a in the given axis. Integer weights are converted to
    Float.  Not specifying weights is equivalent to specifying
    weights that are all 1.

    If 'returned' is True, return a tuple: the result and the sum of
    the weights or count of values. The shape of these two results
    will be the same.

    Raises ZeroDivisionError if appropriate.  (The version in MA does
    not -- it returns masked values).

    """
    if axis is None:
        a = array(a).ravel()
        if weights is None:
            n = add.reduce(a)
            d = len(a) * 1.0
        else:
            w = array(weights).ravel() * 1.0
            n = add.reduce(multiply(a, w))
            d = add.reduce(w)
    else:
        a = array(a)
        ash = a.shape
        if ash == ():
            a.shape = (1,)
        if weights is None:
            n = add.reduce(a, axis)
            d = ash[axis] * 1.0
            if returned:
                d = ones(n.shape) * d
        else:
            w = array(weights, copy=False) * 1.0
            wsh = w.shape
            if wsh == ():
                wsh = (1,)
            if wsh == ash:
                n = add.reduce(a*w, axis)
                d = add.reduce(w, axis)
            elif wsh == (ash[axis],):
                ni = ash[axis]
                r = [newaxis]*ni
                r[axis] = slice(None, None, 1)
                w1 = eval("w["+repr(tuple(r))+"]*ones(ash, float)")
                n = add.reduce(a*w1, axis)
                d = add.reduce(w1, axis)
            else:
                raise ValueError, 'averaging weights have wrong shape'

    if not isinstance(d, ndarray):
        if d == 0.0:
            raise ZeroDivisionError, 'zero denominator in average()'
    if returned:
        return n/d, d
    else:
        return n/d

def asarray_chkfinite(a):
    """Like asarray, but check that no NaNs or Infs are present.
    """
    a = asarray(a)
    if (a.dtype.char in typecodes['AllFloat']) \
           and (_nx.isnan(a).any() or _nx.isinf(a).any()):
        raise ValueError, "array must not contain infs or NaNs"
    return a

def piecewise(x, condlist, funclist, *args, **kw):
    """Return a piecewise-defined function.

    x is the domain

    condlist is a list of boolean arrays or a single boolean array
      The length of the condition list must be n2 or n2-1 where n2
      is the length of the function list.  If len(condlist)==n2-1, then
      an 'otherwise' condition is formed by |'ing all the conditions
      and inverting.

    funclist is a list of functions to call of length (n2).
      Each function should return an array output for an array input
      Each function can take (the same set) of extra arguments and
      keyword arguments which are passed in after the function list.
      A constant may be used in funclist for a function that returns a
      constant (e.g. val  and lambda x: val are equivalent in a funclist).

    The output is the same shape and type as x and is found by
      calling the functions on the appropriate portions of x.

    Note: This is similar to choose or select, except
          the the functions are only evaluated on elements of x
          that satisfy the corresponding condition.

    The result is
           |--
           |  f1(x)  for condition1
     y = --|  f2(x)  for condition2
           |   ...
           |  fn(x)  for conditionn
           |--

    """
    x = asanyarray(x)
    n2 = len(funclist)
    if not isinstance(condlist, type([])):
        condlist = [condlist]
    n = len(condlist)
    if n == n2-1:  # compute the "otherwise" condition.
        totlist = condlist[0]
        for k in range(1, n):
            totlist |= condlist[k]
        condlist.append(~totlist)
        n += 1
    if (n != n2):
        raise ValueError, "function list and condition list must be the same"
    y = empty(x.shape, x.dtype)
    for k in range(n):
        item = funclist[k]
        if not callable(item):
            y[condlist[k]] = item
        else:
            y[condlist[k]] = item(x[condlist[k]], *args, **kw)
    return y

def select(condlist, choicelist, default=0):
    """Return an array composed of different elements in choicelist,
    depending on the list of conditions.

    :Parameters:
        condlist : list of N boolean arrays of length M
            The conditions C_0 through C_(N-1) which determine
            from which vector the output elements are taken.
        choicelist : list of N arrays of length M
            Th vectors V_0 through V_(N-1), from which the output
            elements are chosen.

    :Returns:
        output : 1-dimensional array of length M
            The output at position m is the m-th element of the first
            vector V_n for which C_n[m] is non-zero.  Note that the
            output depends on the order of conditions, since the
            first satisfied condition is used.

            Equivalent to:

                output = []
                for m in range(M):
                    output += [V[m] for V,C in zip(values,cond) if C[m]]
                              or [default]

    """
    n = len(condlist)
    n2 = len(choicelist)
    if n2 != n:
        raise ValueError, "list of cases must be same length as list of conditions"
    choicelist = [default] + choicelist
    S = 0
    pfac = 1
    for k in range(1, n+1):
        S += k * pfac * asarray(condlist[k-1])
        if k < n:
            pfac *= (1-asarray(condlist[k-1]))
    # handle special case of a 1-element condition but
    #  a multi-element choice
    if type(S) in ScalarType or max(asarray(S).shape)==1:
        pfac = asarray(1)
        for k in range(n2+1):
            pfac = pfac + asarray(choicelist[k])
        if type(S) in ScalarType:
            S = S*ones(asarray(pfac).shape, type(S))
        else:
            S = S*ones(asarray(pfac).shape, S.dtype)
    return choose(S, tuple(choicelist))

def _asarray1d(arr, copy=False):
    """Ensure 1D array for one array.
    """
    if copy:
        return asarray(arr).flatten()
    else:
        return asarray(arr).ravel()

def copy(a):
    """Return an array copy of the given object.
    """
    return array(a, copy=True)

# Basic operations

def gradient(f, *varargs):
    """Calculate the gradient of an N-dimensional scalar function.

    Uses central differences on the interior and first differences on boundaries
    to give the same shape.

    Inputs:

      f -- An N-dimensional array giving samples of a scalar function

      varargs -- 0, 1, or N scalars giving the sample distances in each direction

    Outputs:

      N arrays of the same shape as f giving the derivative of f with respect
      to each dimension.

    """
    N = len(f.shape)  # number of dimensions
    n = len(varargs)
    if n == 0:
        dx = [1.0]*N
    elif n == 1:
        dx = [varargs[0]]*N
    elif n == N:
        dx = list(varargs)
    else:
        raise SyntaxError, "invalid number of arguments"

    # use central differences on interior and first differences on endpoints

    outvals = []

    # create slice objects --- initially all are [:, :, ..., :]
    slice1 = [slice(None)]*N
    slice2 = [slice(None)]*N
    slice3 = [slice(None)]*N

    otype = f.dtype.char
    if otype not in ['f', 'd', 'F', 'D']:
        otype = 'd'

    for axis in range(N):
        # select out appropriate parts for this dimension
        out = zeros(f.shape, f.dtype.char)
        slice1[axis] = slice(1, -1)
        slice2[axis] = slice(2, None)
        slice3[axis] = slice(None, -2)
        # 1D equivalent -- out[1:-1] = (f[2:] - f[:-2])/2.0
        out[slice1] = (f[slice2] - f[slice3])/2.0
        slice1[axis] = 0
        slice2[axis] = 1
        slice3[axis] = 0
        # 1D equivalent -- out[0] = (f[1] - f[0])
        out[slice1] = (f[slice2] - f[slice3])
        slice1[axis] = -1
        slice2[axis] = -1
        slice3[axis] = -2
        # 1D equivalent -- out[-1] = (f[-1] - f[-2])
        out[slice1] = (f[slice2] - f[slice3])

        # divide by step size
        outvals.append(out / dx[axis])

        # reset the slice object in this dimension to ":"
        slice1[axis] = slice(None)
        slice2[axis] = slice(None)
        slice3[axis] = slice(None)

    if N == 1:
        return outvals[0]
    else:
        return outvals


def diff(a, n=1, axis=-1):
    """Calculate the nth order discrete difference along given axis.
    """
    if n == 0:
        return a
    if n < 0:
        raise ValueError, 'order must be non-negative but got ' + repr(n)
    a = asanyarray(a)
    nd = len(a.shape)
    slice1 = [slice(None)]*nd
    slice2 = [slice(None)]*nd
    slice1[axis] = slice(1, None)
    slice2[axis] = slice(None, -1)
    slice1 = tuple(slice1)
    slice2 = tuple(slice2)
    if n > 1:
        return diff(a[slice1]-a[slice2], n-1, axis=axis)
    else:
        return a[slice1]-a[slice2]

try:
    add_docstring(digitize,
r"""digitize(x,bins)

Return the index of the bin to which each value of x belongs.

Each index i returned is such that bins[i-1] <= x < bins[i] if
bins is monotonically increasing, or bins [i-1] > x >= bins[i] if
bins is monotonically decreasing.

Beyond the bounds of the bins 0 or len(bins) is returned as appropriate.

""")
except RuntimeError:
    pass

try:
    add_docstring(bincount,
r"""bincount(x,weights=None)

Return the number of occurrences of each value in x.

x must be a list of non-negative integers.  The output, b[i],
represents the number of times that i is found in x.  If weights
is specified, every occurrence of i at a position p contributes
weights[p] instead of 1.

See also: histogram, digitize, unique.

""")
except RuntimeError:
    pass

try:
    add_docstring(add_docstring,
r"""docstring(obj, docstring)

Add a docstring to a built-in obj if possible.
If the obj already has a docstring raise a RuntimeError
If this routine does not know how to add a docstring to the object
raise a TypeError

""")
except RuntimeError:
    pass

try:
    add_docstring(interp,
r"""interp(x, xp, fp, left=None, right=None)

Return the value of a piecewise-linear function at each value in x.

The piecewise-linear function, f, is defined by the known data-points fp=f(xp).
The xp points must be sorted in increasing order but this is not checked.

For values of x < xp[0] return the value given by left.  If left is None, then
return fp[0].
For values of x > xp[-1] return the value given by right. If right is None, then
return fp[-1].
"""
                  )
except RuntimeError:
    pass


def angle(z, deg=0):
    """Return the angle of the complex argument z.
    """
    if deg:
        fact = 180/pi
    else:
        fact = 1.0
    z = asarray(z)
    if (issubclass(z.dtype.type, _nx.complexfloating)):
        zimag = z.imag
        zreal = z.real
    else:
        zimag = 0
        zreal = z
    return arctan2(zimag, zreal) * fact

def unwrap(p, discont=pi, axis=-1):
    """Unwrap radian phase p by changing absolute jumps greater than
       'discont' to their 2*pi complement along the given axis.
    """
    p = asarray(p)
    nd = len(p.shape)
    dd = diff(p, axis=axis)
    slice1 = [slice(None, None)]*nd     # full slices
    slice1[axis] = slice(1, None)
    ddmod = mod(dd+pi, 2*pi)-pi
    _nx.putmask(ddmod, (ddmod==-pi) & (dd > 0), pi)
    ph_correct = ddmod - dd;
    _nx.putmask(ph_correct, abs(dd)<discont, 0)
    up = array(p, copy=True, dtype='d')
    up[slice1] = p[slice1] + ph_correct.cumsum(axis)
    return up

def sort_complex(a):
    """ Sort 'a' as a complex array using the real part first and then
    the imaginary part if the real part is equal (the default sort order
    for complex arrays).  This function is a wrapper ensuring a complex
    return type.

    """
    b = array(a,copy=True)
    b.sort()
    if not issubclass(b.dtype.type, _nx.complexfloating):
        if b.dtype.char in 'bhBH':
            return b.astype('F')
        elif b.dtype.char == 'g':
            return b.astype('G')
        else:
            return b.astype('D')
    else:
        return b

def trim_zeros(filt, trim='fb'):
    """ Trim the leading and trailing zeros from a 1D array.

    Example:
        >>> import numpy
        >>> a = array((0, 0, 0, 1, 2, 3, 2, 1, 0))
        >>> numpy.trim_zeros(a)
        array([1, 2, 3, 2, 1])

    """
    first = 0
    trim = trim.upper()
    if 'F' in trim:
        for i in filt:
            if i != 0.: break
            else: first = first + 1
    last = len(filt)
    if 'B' in trim:
        for i in filt[::-1]:
            if i != 0.: break
            else: last = last - 1
    return filt[first:last]

import sys
if sys.hexversion < 0x2040000:
    from sets import Set as set

def unique(x):
    """Return sorted unique items from an array or sequence.

    Example:
    >>> unique([5,2,4,0,4,4,2,2,1])
    array([0, 1, 2, 4, 5])

    """
    try:
        tmp = x.flatten()
        if tmp.size == 0:
            return tmp
        tmp.sort()
        idx = concatenate(([True],tmp[1:]!=tmp[:-1]))
        return tmp[idx]
    except AttributeError:
        items = list(set(x))
        items.sort()
        return asarray(items)

def extract(condition, arr):
    """Return the elements of ravel(arr) where ravel(condition) is True
    (in 1D).

    Equivalent to compress(ravel(condition), ravel(arr)).
    """
    return _nx.take(ravel(arr), nonzero(ravel(condition))[0])

def place(arr, mask, vals):
    """Similar to putmask arr[mask] = vals but the 1D array vals has the
    same number of elements as the non-zero values of mask. Inverse of
    extract.

    """
    return _insert(arr, mask, vals)

def nansum(a, axis=None):
    """Sum the array over the given axis, treating NaNs as 0.
    """
    y = array(a,subok=True)
    if not issubclass(y.dtype.type, _nx.integer):
        y[isnan(a)] = 0
    return y.sum(axis)

def nanmin(a, axis=None):
    """Find the minimium over the given axis, ignoring NaNs.
    """
    y = array(a,subok=True)
    if not issubclass(y.dtype.type, _nx.integer):
        y[isnan(a)] = _nx.inf
    return y.min(axis)

def nanargmin(a, axis=None):
    """Find the indices of the minimium over the given axis ignoring NaNs.
    """
    y = array(a, subok=True)
    if not issubclass(y.dtype.type, _nx.integer):
        y[isnan(a)] = _nx.inf
    return y.argmin(axis)

def nanmax(a, axis=None):
    """Find the maximum over the given axis ignoring NaNs.
    """
    y = array(a, subok=True)
    if not issubclass(y.dtype.type, _nx.integer):
        y[isnan(a)] = -_nx.inf
    return y.max(axis)

def nanargmax(a, axis=None):
    """Find the maximum over the given axis ignoring NaNs.
    """
    y = array(a,subok=True)
    if not issubclass(y.dtype.type, _nx.integer):
        y[isnan(a)] = -_nx.inf
    return y.argmax(axis)

def disp(mesg, device=None, linefeed=True):
    """Display a message to the given device (default is sys.stdout)
    with or without a linefeed.
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

# return number of input arguments and
#  number of default arguments
import re
def _get_nargs(obj):
    if not callable(obj):
        raise TypeError, "Object is not callable."
    if hasattr(obj,'func_code'):
        fcode = obj.func_code
        nargs = fcode.co_argcount
        if obj.func_defaults is not None:
            ndefaults = len(obj.func_defaults)
        else:
            ndefaults = 0
        if isinstance(obj, types.MethodType):
            nargs -= 1
        return nargs, ndefaults
    terr = re.compile(r'.*? takes exactly (?P<exargs>\d+) argument(s|) \((?P<gargs>\d+) given\)')
    try:
        obj()
        return 0, 0
    except TypeError, msg:
        m = terr.match(str(msg))
        if m:
            nargs = int(m.group('exargs'))
            ndefaults = int(m.group('gargs'))
            if isinstance(obj, types.MethodType):
                nargs -= 1
            return nargs, ndefaults
    raise ValueError, 'failed to determine the number of arguments for %s' % (obj)


class vectorize(object):
    """
 vectorize(somefunction, otypes=None, doc=None)
 Generalized Function class.

  Description:

    Define a vectorized function which takes nested sequence
    of objects or numpy arrays as inputs and returns a
    numpy array as output, evaluating the function over successive
    tuples of the input arrays like the python map function except it uses
    the broadcasting rules of numpy.

    Data-type of output of vectorized is determined by calling the function
    with the first element of the input.  This can be avoided by specifying
    the otypes argument as either a string of typecode characters or a list
    of data-types specifiers.  There should be one data-type specifier for
    each output.

  Input:

    somefunction -- a Python function or method

  Example:

    >>> def myfunc(a, b):
    ...    if a > b:
    ...        return a-b
    ...    else:
    ...        return a+b

    >>> vfunc = vectorize(myfunc)

    >>> vfunc([1, 2, 3, 4], 2)
    array([3, 4, 1, 2])

    """
    def __init__(self, pyfunc, otypes='', doc=None):
        self.thefunc = pyfunc
        self.ufunc = None
        nin, ndefault = _get_nargs(pyfunc)
        if nin == 0 and ndefault == 0:
            self.nin = None
            self.nin_wo_defaults = None
        else:
            self.nin = nin
            self.nin_wo_defaults = nin - ndefault
        self.nout = None
        if doc is None:
            self.__doc__ = pyfunc.__doc__
        else:
            self.__doc__ = doc
        if isinstance(otypes, types.StringType):
            self.otypes = otypes
            for char in self.otypes:
                if char not in typecodes['All']:
                    raise ValueError, "invalid otype specified"
        elif iterable(otypes):
            self.otypes = ''.join([_nx.dtype(x).char for x in otypes])
        else:
            raise ValueError, "output types must be a string of typecode characters or a list of data-types"
        self.lastcallargs = 0

    def __call__(self, *args):
        # get number of outputs and output types by calling
        #  the function on the first entries of args
        nargs = len(args)
        if self.nin:
            if (nargs > self.nin) or (nargs < self.nin_wo_defaults):
                raise ValueError, "mismatch between python function inputs"\
                      " and received arguments"

        # we need a new ufunc if this is being called with more arguments.
        if (self.lastcallargs != nargs):
            self.lastcallargs = nargs
            self.ufunc = None
            self.nout = None

        if self.nout is None or self.otypes == '':
            newargs = []
            for arg in args:
                newargs.append(asarray(arg).flat[0])
            theout = self.thefunc(*newargs)
            if isinstance(theout, types.TupleType):
                self.nout = len(theout)
            else:
                self.nout = 1
                theout = (theout,)
            if self.otypes == '':
                otypes = []
                for k in range(self.nout):
                    otypes.append(asarray(theout[k]).dtype.char)
                self.otypes = ''.join(otypes)

        # Create ufunc if not already created
        if (self.ufunc is None):
            self.ufunc = frompyfunc(self.thefunc, nargs, self.nout)

        # Convert to object arrays first
        newargs = [array(arg,copy=False,subok=True,dtype=object) for arg in args]
        if self.nout == 1:
            _res = array(self.ufunc(*newargs),copy=False,
                         subok=True,dtype=self.otypes[0])
        else:
            _res = tuple([array(x,copy=False,subok=True,dtype=c) \
                          for x, c in zip(self.ufunc(*newargs), self.otypes)])
        return _res

def cov(m, y=None, rowvar=1, bias=0):
    """Estimate the covariance matrix.

    If m is a vector, return the variance.  For matrices return the
    covariance matrix.

    If y is given it is treated as an additional (set of)
    variable(s).

    Normalization is by (N-1) where N is the number of observations
    (unbiased estimate).  If bias is 1 then normalization is by N.

    If rowvar is non-zero (default), then each row is a variable with
    observations in the columns, otherwise each column
    is a variable and the observations are in the rows.
    """

    X = array(m, ndmin=2, dtype=float)
    if X.shape[0] == 1:
        rowvar = 1
    if rowvar:
        axis = 0
        tup = (slice(None),newaxis)
    else:
        axis = 1
        tup = (newaxis, slice(None))


    if y is not None:
        y = array(y, copy=False, ndmin=2, dtype=float)
        X = concatenate((X,y),axis)

    X -= X.mean(axis=1-axis)[tup]
    if rowvar:
        N = X.shape[1]
    else:
        N = X.shape[0]

    if bias:
        fact = N*1.0
    else:
        fact = N-1.0

    if not rowvar:
        return (dot(X.T, X.conj()) / fact).squeeze()
    else:
        return (dot(X, X.T.conj()) / fact).squeeze()

def corrcoef(x, y=None, rowvar=1, bias=0):
    """The correlation coefficients
    """
    c = cov(x, y, rowvar, bias)
    try:
        d = diag(c)
    except ValueError: # scalar covariance
        return 1
    return c/sqrt(multiply.outer(d,d))

def blackman(M):
    """blackman(M) returns the M-point Blackman window.
    """
    if M < 1:
        return array([])
    if M == 1:
        return ones(1, float)
    n = arange(0,M)
    return 0.42-0.5*cos(2.0*pi*n/(M-1)) + 0.08*cos(4.0*pi*n/(M-1))

def bartlett(M):
    """bartlett(M) returns the M-point Bartlett window.
    """
    if M < 1:
        return array([])
    if M == 1:
        return ones(1, float)
    n = arange(0,M)
    return where(less_equal(n,(M-1)/2.0),2.0*n/(M-1),2.0-2.0*n/(M-1))

def hanning(M):
    """hanning(M) returns the M-point Hanning window.
    """
    if M < 1:
        return array([])
    if M == 1:
        return ones(1, float)
    n = arange(0,M)
    return 0.5-0.5*cos(2.0*pi*n/(M-1))

def hamming(M):
    """hamming(M) returns the M-point Hamming window.
    """
    if M < 1:
        return array([])
    if M == 1:
        return ones(1,float)
    n = arange(0,M)
    return 0.54-0.46*cos(2.0*pi*n/(M-1))

## Code from cephes for i0

_i0A = [
-4.41534164647933937950E-18,
 3.33079451882223809783E-17,
-2.43127984654795469359E-16,
 1.71539128555513303061E-15,
-1.16853328779934516808E-14,
 7.67618549860493561688E-14,
-4.85644678311192946090E-13,
 2.95505266312963983461E-12,
-1.72682629144155570723E-11,
 9.67580903537323691224E-11,
-5.18979560163526290666E-10,
 2.65982372468238665035E-9,
-1.30002500998624804212E-8,
 6.04699502254191894932E-8,
-2.67079385394061173391E-7,
 1.11738753912010371815E-6,
-4.41673835845875056359E-6,
 1.64484480707288970893E-5,
-5.75419501008210370398E-5,
 1.88502885095841655729E-4,
-5.76375574538582365885E-4,
 1.63947561694133579842E-3,
-4.32430999505057594430E-3,
 1.05464603945949983183E-2,
-2.37374148058994688156E-2,
 4.93052842396707084878E-2,
-9.49010970480476444210E-2,
 1.71620901522208775349E-1,
-3.04682672343198398683E-1,
 6.76795274409476084995E-1]

_i0B = [
-7.23318048787475395456E-18,
-4.83050448594418207126E-18,
 4.46562142029675999901E-17,
 3.46122286769746109310E-17,
-2.82762398051658348494E-16,
-3.42548561967721913462E-16,
 1.77256013305652638360E-15,
 3.81168066935262242075E-15,
-9.55484669882830764870E-15,
-4.15056934728722208663E-14,
 1.54008621752140982691E-14,
 3.85277838274214270114E-13,
 7.18012445138366623367E-13,
-1.79417853150680611778E-12,
-1.32158118404477131188E-11,
-3.14991652796324136454E-11,
 1.18891471078464383424E-11,
 4.94060238822496958910E-10,
 3.39623202570838634515E-9,
 2.26666899049817806459E-8,
 2.04891858946906374183E-7,
 2.89137052083475648297E-6,
 6.88975834691682398426E-5,
 3.36911647825569408990E-3,
 8.04490411014108831608E-1]

def _chbevl(x, vals):
    b0 = vals[0]
    b1 = 0.0

    for i in xrange(1,len(vals)):
        b2 = b1
        b1 = b0
        b0 = x*b1 - b2 + vals[i]

    return 0.5*(b0 - b2)

def _i0_1(x):
    return exp(x) * _chbevl(x/2.0-2, _i0A)

def _i0_2(x):
    return exp(x) * _chbevl(32.0/x - 2.0, _i0B) / sqrt(x)

def i0(x):
    x = atleast_1d(x).copy()
    y = empty_like(x)
    ind = (x<0)
    x[ind] = -x[ind]
    ind = (x<=8.0)
    y[ind] = _i0_1(x[ind])
    ind2 = ~ind
    y[ind2] = _i0_2(x[ind2])
    return y.squeeze()

## End of cephes code for i0

def kaiser(M,beta):
    """kaiser(M, beta) returns a Kaiser window of length M with shape parameter
    beta.
    """
    from numpy.dual import i0
    n = arange(0,M)
    alpha = (M-1)/2.0
    return i0(beta * sqrt(1-((n-alpha)/alpha)**2.0))/i0(beta)

def sinc(x):
    """sinc(x) returns sin(pi*x)/(pi*x) at all points of array x.
    """
    y = pi* where(x == 0, 1.0e-20, x)
    return sin(y)/y

def msort(a):
    b = array(a,subok=True,copy=True)
    b.sort(0)
    return b

def median(m):
    """median(m) returns a median of m along the first dimension of m.
    """
    sorted = msort(m)
    index = int(sorted.shape[0]/2)
    if sorted.shape[0] % 2 == 1:
        return sorted[index]
    else:
        return (sorted[index-1]+sorted[index])/2.0

def trapz(y, x=None, dx=1.0, axis=-1):
    """Integrate y(x) using samples along the given axis and the composite
    trapezoidal rule.  If x is None, spacing given by dx is assumed.
    """
    y = asarray(y)
    if x is None:
        d = dx
    else:
        d = diff(x,axis=axis)
    nd = len(y.shape)
    slice1 = [slice(None)]*nd
    slice2 = [slice(None)]*nd
    slice1[axis] = slice(1,None)
    slice2[axis] = slice(None,-1)
    return add.reduce(d * (y[slice1]+y[slice2])/2.0,axis)

#always succeed
def add_newdoc(place, obj, doc):
    """Adds documentation to obj which is in module place.

    If doc is a string add it to obj as a docstring

    If doc is a tuple, then the first element is interpreted as
       an attribute of obj and the second as the docstring
          (method, docstring)

    If doc is a list, then each element of the list should be a
       sequence of length two --> [(method1, docstring1),
       (method2, docstring2), ...]

    This routine never raises an error.
       """
    try:
        new = {}
        exec 'from %s import %s' % (place, obj) in new
        if isinstance(doc, str):
            add_docstring(new[obj], doc.strip())
        elif isinstance(doc, tuple):
            add_docstring(getattr(new[obj], doc[0]), doc[1].strip())
        elif isinstance(doc, list):
            for val in doc:
                add_docstring(getattr(new[obj], val[0]), val[1].strip())
    except:
        pass


# From matplotlib
def meshgrid(x,y):
    """
    For vectors x, y with lengths Nx=len(x) and Ny=len(y), return X, Y
    where X and Y are (Ny, Nx) shaped arrays with the elements of x
    and y repeated to fill the matrix

    EG,

      [X, Y] = meshgrid([1,2,3], [4,5,6,7])

       X =
         1   2   3
         1   2   3
         1   2   3
         1   2   3


       Y =
         4   4   4
         5   5   5
         6   6   6
         7   7   7
  """
    x = asarray(x)
    y = asarray(y)
    numRows, numCols = len(y), len(x)  # yes, reversed
    x = x.reshape(1,numCols)
    X = x.repeat(numRows, axis=0)

    y = y.reshape(numRows,1)
    Y = y.repeat(numCols, axis=1)
    return X, Y

def delete(arr, obj, axis=None):
    """Return a new array with sub-arrays along an axis deleted.

    Return a new array with the sub-arrays (i.e. rows or columns)
    deleted along the given axis as specified by obj

    obj may be a slice_object (s_[3:5:2]) or an integer
    or an array of integers indicated which sub-arrays to
    remove.

    If axis is None, then ravel the array first.

    Example:
    >>> arr = [[3,4,5],
    ...       [1,2,3],
    ...       [6,7,8]]

    >>> delete(arr, 1, 1)
    array([[3, 5],
           [1, 3],
           [6, 8]])
    >>> delete(arr, 1, 0)
    array([[3, 4, 5],
           [6, 7, 8]])
    """
    wrap = None
    if type(arr) is not ndarray:
        try:
            wrap = arr.__array_wrap__
        except AttributeError:
            pass


    arr = asarray(arr)
    ndim = arr.ndim
    if axis is None:
        if ndim != 1:
            arr = arr.ravel()
        ndim = arr.ndim;
        axis = ndim-1;
    if ndim == 0:
        if wrap:
            return wrap(arr)
        else:
            return arr.copy()
    slobj = [slice(None)]*ndim
    N = arr.shape[axis]
    newshape = list(arr.shape)
    if isinstance(obj, (int, long, integer)):
        if (obj < 0): obj += N
        if (obj < 0 or obj >=N):
            raise ValueError, "invalid entry"
        newshape[axis]-=1;
        new = empty(newshape, arr.dtype, arr.flags.fnc)
        slobj[axis] = slice(None, obj)
        new[slobj] = arr[slobj]
        slobj[axis] = slice(obj,None)
        slobj2 = [slice(None)]*ndim
        slobj2[axis] = slice(obj+1,None)
        new[slobj] = arr[slobj2]
    elif isinstance(obj, slice):
        start, stop, step = obj.indices(N)
        numtodel = len(xrange(start, stop, step))
        if numtodel <= 0:
            if wrap:
                return wrap(new)
            else:
                return arr.copy()
        newshape[axis] -= numtodel
        new = empty(newshape, arr.dtype, arr.flags.fnc)
        # copy initial chunk
        if start == 0:
            pass
        else:
            slobj[axis] = slice(None, start)
            new[slobj] = arr[slobj]
        # copy end chunck
        if stop == N:
            pass
        else:
            slobj[axis] = slice(stop-numtodel,None)
            slobj2 = [slice(None)]*ndim
            slobj2[axis] = slice(stop, None)
            new[slobj] = arr[slobj2]
        # copy middle pieces
        if step == 1:
            pass
        else:  # use array indexing.
            obj = arange(start, stop, step, dtype=intp)
            all = arange(start, stop, dtype=intp)
            obj = setdiff1d(all, obj)
            slobj[axis] = slice(start, stop-numtodel)
            slobj2 = [slice(None)]*ndim
            slobj2[axis] = obj
            new[slobj] = arr[slobj2]
    else: # default behavior
        obj = array(obj, dtype=intp, copy=0, ndmin=1)
        all = arange(N, dtype=intp)
        obj = setdiff1d(all, obj)
        slobj[axis] = obj
        new = arr[slobj]
    if wrap:
        return wrap(new)
    else:
        return new

def insert(arr, obj, values, axis=None):
    """Return a new array with values inserted along the given axis
    before the given indices

    If axis is None, then ravel the array first.

    The obj argument can be an integer, a slice, or a sequence of
    integers.

    Example:
    >>> a = array([[1,2,3],
    ...            [4,5,6],
    ...            [7,8,9]])

    >>> insert(a, [1,2], [[4],[5]], axis=0)
    array([[1, 2, 3],
           [4, 4, 4],
           [4, 5, 6],
           [5, 5, 5],
           [7, 8, 9]])
    """
    wrap = None
    if type(arr) is not ndarray:
        try:
            wrap = arr.__array_wrap__
        except AttributeError:
            pass

    arr = asarray(arr)
    ndim = arr.ndim
    if axis is None:
        if ndim != 1:
            arr = arr.ravel()
        ndim = arr.ndim
        axis = ndim-1
    if (ndim == 0):
        arr = arr.copy()
        arr[...] = values
        if wrap:
            return wrap(arr)
        else:
            return arr
    slobj = [slice(None)]*ndim
    N = arr.shape[axis]
    newshape = list(arr.shape)
    if isinstance(obj, (int, long, integer)):
        if (obj < 0): obj += N
        if obj < 0 or obj > N:
            raise ValueError, "index (%d) out of range (0<=index<=%d) "\
                  "in dimension %d" % (obj, N, axis)
        newshape[axis] += 1;
        new = empty(newshape, arr.dtype, arr.flags.fnc)
        slobj[axis] = slice(None, obj)
        new[slobj] = arr[slobj]
        slobj[axis] = obj
        new[slobj] = values
        slobj[axis] = slice(obj+1,None)
        slobj2 = [slice(None)]*ndim
        slobj2[axis] = slice(obj,None)
        new[slobj] = arr[slobj2]
        if wrap:
            return wrap(new)
        return new

    elif isinstance(obj, slice):
        # turn it into a range object
        obj = arange(*obj.indices(N),**{'dtype':intp})

    # get two sets of indices
    #  one is the indices which will hold the new stuff
    #  two is the indices where arr will be copied over

    obj = asarray(obj, dtype=intp)
    numnew = len(obj)
    index1 = obj + arange(numnew)
    index2 = setdiff1d(arange(numnew+N),index1)
    newshape[axis] += numnew
    new = empty(newshape, arr.dtype, arr.flags.fnc)
    slobj2 = [slice(None)]*ndim
    slobj[axis] = index1
    slobj2[axis] = index2
    new[slobj] = values
    new[slobj2] = arr

    if wrap:
        return wrap(new)
    return new

def append(arr, values, axis=None):
    """Append to the end of an array along axis (ravel first if None)
    """
    arr = asanyarray(arr)
    if axis is None:
        if arr.ndim != 1:
            arr = arr.ravel()
        values = ravel(values)
        axis = arr.ndim-1
    return concatenate((arr, values), axis=axis)

"""
Set operations for 1D numeric arrays based on sorting.

:Contains:
  ediff1d,
  unique1d,
  intersect1d,
  intersect1d_nu,
  setxor1d,
  setmember1d,
  union1d,
  setdiff1d

:Notes:

All functions work best with integer numerical arrays on input (e.g. indices).
For floating point arrays, innacurate results may appear due to usual round-off
and floating point comparison issues.

Except unique1d, union1d and intersect1d_nu, all functions expect inputs with
unique elements. Speed could be gained in some operations by an implementaion of
sort(), that can provide directly the permutation vectors, avoiding thus calls
to argsort().

Run _test_unique1d_speed() to compare performance of numpy.unique1d() and
numpy.unique() - it should be the same.

To do: Optionally return indices analogously to unique1d for all functions.

created:       01.11.2005
last revision: 07.01.2007

:Author: Robert Cimrman
"""
__all__ = ['ediff1d', 'unique1d', 'intersect1d', 'intersect1d_nu', 'setxor1d',
           'setmember1d', 'union1d', 'setdiff1d']

import time
import numpy as nm

def ediff1d(ary, to_end = None, to_begin = None):
    """The differences between consecutive elements of an array, possibly with
    prefixed and/or appended values.

    :Parameters:
      - `ary` : array
        This array will be flattened before the difference is taken.
      - `to_end` : number, optional
        If provided, this number will be tacked onto the end of the returned
        differences.
      - `to_begin` : number, optional
        If provided, this number will be taked onto the beginning of the
        returned differences.

    :Returns:
      - `ed` : array
        The differences. Loosely, this will be (ary[1:] - ary[:-1]).
    """
    ary = nm.asarray(ary).flat
    ed = ary[1:] - ary[:-1]
    arrays = [ed]
    if to_begin is not None:
        arrays.insert(0, to_begin)
    if to_end is not None:
        arrays.append(to_end)

    if len(arrays) != 1:
        # We'll save ourselves a copy of a potentially large array in the common
        # case where neither to_begin or to_end was given.
        ed = nm.hstack(arrays)

    return ed

def unique1d(ar1, return_index=False):
    """Find the unique elements of 1D array.

    Most of the other array set operations operate on the unique arrays
    generated by this function.

    :Parameters:
      - `ar1` : array
        This array will be flattened if it is not already 1D.
      - `return_index` : bool, optional
        If True, also return the indices against ar1 that result in the unique
        array.

    :Returns:
      - `unique` : array
        The unique values.
      - `unique_indices` : int array, optional
        The indices of the unique values. Only provided if return_index is True.

    :See also:
      numpy.lib.arraysetops has a number of other functions for performing set
      operations on arrays.
    """
    ar = nm.asarray(ar1).flatten()
    if ar.size == 0:
        if return_index: return nm.empty(0, nm.bool), ar
        else: return ar

    if return_index:
        perm = ar.argsort()
        aux = ar[perm]
        flag = nm.concatenate( ([True], aux[1:] != aux[:-1]) )
        return perm[flag], aux[flag]

    else:
        ar.sort()
        flag = nm.concatenate( ([True], ar[1:] != ar[:-1]) )
        return ar[flag]

def intersect1d( ar1, ar2 ):
    """Intersection of 1D arrays with unique elements.

    Use unique1d() to generate arrays with only unique elements to use as inputs
    to this function. Alternatively, use intersect1d_nu() which will find the
    unique values for you.

    :Parameters:
      - `ar1` : array
      - `ar2` : array

    :Returns:
      - `intersection` : array

    :See also:
      numpy.lib.arraysetops has a number of other functions for performing set
      operations on arrays.
    """
    aux = nm.concatenate((ar1,ar2))
    aux.sort()
    return aux[aux[1:] == aux[:-1]]

def intersect1d_nu( ar1, ar2 ):
    """Intersection of 1D arrays with any elements.

    The input arrays do not have unique elements like intersect1d() requires.

    :Parameters:
      - `ar1` : array
      - `ar2` : array

    :Returns:
      - `intersection` : array

    :See also:
      numpy.lib.arraysetops has a number of other functions for performing set
      operations on arrays.
    """
    # Might be faster than unique1d( intersect1d( ar1, ar2 ) )?
    aux = nm.concatenate((unique1d(ar1), unique1d(ar2)))
    aux.sort()
    return aux[aux[1:] == aux[:-1]]

def setxor1d( ar1, ar2 ):
    """Set exclusive-or of 1D arrays with unique elements.

    Use unique1d() to generate arrays with only unique elements to use as inputs
    to this function.

    :Parameters:
      - `ar1` : array
      - `ar2` : array

    :Returns:
      - `xor` : array
        The values that are only in one, but not both, of the input arrays.

    :See also:
      numpy.lib.arraysetops has a number of other functions for performing set
      operations on arrays.
    """
    aux = nm.concatenate((ar1, ar2))
    if aux.size == 0:
        return aux

    aux.sort()
#    flag = ediff1d( aux, to_end = 1, to_begin = 1 ) == 0
    flag = nm.concatenate( ([True], aux[1:] != aux[:-1], [True] ) )
#    flag2 = ediff1d( flag ) == 0
    flag2 = flag[1:] == flag[:-1]
    return aux[flag2]

def setmember1d( ar1, ar2 ):
    """Return a boolean array of shape of ar1 containing True where the elements
    of ar1 are in ar2 and False otherwise.

    Use unique1d() to generate arrays with only unique elements to use as inputs
    to this function.

    :Parameters:
      - `ar1` : array
      - `ar2` : array

    :Returns:
      - `mask` : bool array
        The values ar1[mask] are in ar2.

    :See also:
      numpy.lib.arraysetops has a number of other functions for performing set
      operations on arrays.
    """
    zlike = nm.zeros_like
    ar = nm.concatenate( (ar1, ar2 ) )
    tt = nm.concatenate( (zlike( ar1 ), zlike( ar2 ) + 1) )
    # We need this to be a stable sort, so always use 'mergesort' here. The
    # values from the first array should always come before the values from the
    # second array.
    perm = ar.argsort(kind='mergesort')
    aux = ar[perm]
    aux2 = tt[perm]
#    flag = ediff1d( aux, 1 ) == 0
    flag = nm.concatenate( (aux[1:] == aux[:-1], [False] ) )

    ii = nm.where( flag * aux2 )[0]
    aux = perm[ii+1]
    perm[ii+1] = perm[ii]
    perm[ii] = aux

    indx = perm.argsort(kind='mergesort')[:len( ar1 )]

    return flag[indx]

def union1d( ar1, ar2 ):
    """Union of 1D arrays with unique elements.

    Use unique1d() to generate arrays with only unique elements to use as inputs
    to this function.

    :Parameters:
      - `ar1` : array
      - `ar2` : array

    :Returns:
      - `union` : array

    :See also:
      numpy.lib.arraysetops has a number of other functions for performing set
      operations on arrays.
    """
    return unique1d( nm.concatenate( (ar1, ar2) ) )

def setdiff1d( ar1, ar2 ):
    """Set difference of 1D arrays with unique elements.

    Use unique1d() to generate arrays with only unique elements to use as inputs
    to this function.

    :Parameters:
      - `ar1` : array
      - `ar2` : array

    :Returns:
      - `difference` : array
        The values in ar1 that are not in ar2.

    :See also:
      numpy.lib.arraysetops has a number of other functions for performing set
      operations on arrays.
    """
    aux = setmember1d(ar1,ar2)
    if aux.size == 0:
        return aux
    else:
        return nm.asarray(ar1)[aux == 0]

def _test_unique1d_speed( plot_results = False ):
#    exponents = nm.linspace( 2, 7, 9 )
    exponents = nm.linspace( 2, 7, 9 )
    ratios = []
    nItems = []
    dt1s = []
    dt2s = []
    for ii in exponents:

        nItem = 10 ** ii
        print 'using %d items:' % nItem
        a = nm.fix( nItem / 10 * nm.random.random( nItem ) )

        print 'unique:'
        tt = time.clock()
        b = nm.unique( a )
        dt1 = time.clock() - tt
        print dt1

        print 'unique1d:'
        tt = time.clock()
        c = unique1d( a )
        dt2 = time.clock() - tt
        print dt2


        if dt1 < 1e-8:
            ratio = 'ND'
        else:
            ratio = dt2 / dt1
        print 'ratio:', ratio
        print 'nUnique: %d == %d\n' % (len( b ), len( c ))

        nItems.append( nItem )
        ratios.append( ratio )
        dt1s.append( dt1 )
        dt2s.append( dt2 )

        assert nm.alltrue( b == c )

    print nItems
    print dt1s
    print dt2s
    print ratios

    if plot_results:
        import pylab

        def plotMe( fig, fun, nItems, dt1s, dt2s ):
            pylab.figure( fig )
            fun( nItems, dt1s, 'g-o', linewidth = 2, markersize = 8 )
            fun( nItems, dt2s, 'b-x', linewidth = 2, markersize = 8 )
            pylab.legend( ('unique', 'unique1d' ) )
            pylab.xlabel( 'nItem' )
            pylab.ylabel( 'time [s]' )

        plotMe( 1, pylab.loglog, nItems, dt1s, dt2s )
        plotMe( 2, pylab.plot, nItems, dt1s, dt2s )
        pylab.show()

if (__name__ == '__main__'):
    _test_unique1d_speed( plot_results = True )

## Automatically adapted for numpy Sep 19, 2005 by convertcode.py

__all__ = ['iscomplexobj','isrealobj','imag','iscomplex',
           'isreal','nan_to_num','real','real_if_close',
           'typename','asfarray','mintypecode','asscalar',
           'common_type']

import numpy.core.numeric as _nx
from numpy.core.numeric import asarray, asanyarray, array, isnan, \
                obj2sctype, zeros
from ufunclike import isneginf, isposinf

_typecodes_by_elsize = 'GDFgdfQqLlIiHhBb?'

def mintypecode(typechars,typeset='GDFgdf',default='d'):
    """ Return a minimum data type character from typeset that
    handles all typechars given

    The returned type character must be the smallest size such that
    an array of the returned type can handle the data from an array of
    type t for each t in typechars (or if typechars is an array,
    then its dtype.char).

    If the typechars does not intersect with the typeset, then default
    is returned.

    If t in typechars is not a string then t=asarray(t).dtype.char is
    applied.
    """
    typecodes = [(type(t) is type('') and t) or asarray(t).dtype.char\
                 for t in typechars]
    intersection = [t for t in typecodes if t in typeset]
    if not intersection:
        return default
    if 'F' in intersection and 'd' in intersection:
        return 'D'
    l = []
    for t in intersection:
        i = _typecodes_by_elsize.index(t)
        l.append((i,t))
    l.sort()
    return l[0][1]

def asfarray(a, dtype=_nx.float_):
    """asfarray(a,dtype=None) returns a as a float array."""
    dtype = _nx.obj2sctype(dtype)
    if not issubclass(dtype, _nx.inexact):
        dtype = _nx.float_
    return asarray(a,dtype=dtype)

def real(val):
    """Return the real part of val.

    Useful if val maybe a scalar or an array.
    """
    return asanyarray(val).real

def imag(val):
    """Return the imaginary part of val.

    Useful if val maybe a scalar or an array.
    """
    return asanyarray(val).imag

def iscomplex(x):
    """Return a boolean array where elements are True if that element
    is complex (has non-zero imaginary part).

    For scalars, return a boolean.
    """
    ax = asanyarray(x)
    if issubclass(ax.dtype.type, _nx.complexfloating):
        return ax.imag != 0
    res = zeros(ax.shape, bool)
    return +res  # convet to array-scalar if needed

def isreal(x):
    """Return a boolean array where elements are True if that element
    is real (has zero imaginary part)

    For scalars, return a boolean.
    """
    return imag(x) == 0

def iscomplexobj(x):
    """Return True if x is a complex type or an array of complex numbers.

    Unlike iscomplex(x), complex(3.0) is considered a complex object.
    """
    return issubclass( asarray(x).dtype.type, _nx.complexfloating)

def isrealobj(x):
    """Return True if x is not a complex type.

    Unlike isreal(x), complex(3.0) is considered a complex object.
    """
    return not issubclass( asarray(x).dtype.type, _nx.complexfloating)

#-----------------------------------------------------------------------------

def _getmaxmin(t):
    import getlimits
    f = getlimits.finfo(t)
    return f.max, f.min

def nan_to_num(x):
    """
    Returns a copy of replacing NaN's with 0 and Infs with large numbers

    The following mappings are applied:
        NaN -> 0
        Inf -> limits.double_max
       -Inf -> limits.double_min
    """
    try:
        t = x.dtype.type
    except AttributeError:
        t = obj2sctype(type(x))
    if issubclass(t, _nx.complexfloating):
        return nan_to_num(x.real) + 1j * nan_to_num(x.imag)
    else:
        try:
            y = x.copy()
        except AttributeError:
            y = array(x)
    if not issubclass(t, _nx.integer):
        if not y.shape:
            y = array([x])
            scalar = True
        else:
            scalar = False
        are_inf = isposinf(y)
        are_neg_inf = isneginf(y)
        are_nan = isnan(y)
        maxf, minf = _getmaxmin(y.dtype.type)
        y[are_nan] = 0
        y[are_inf] = maxf
        y[are_neg_inf] = minf
        if scalar:
            y = y[0]
    return y

#-----------------------------------------------------------------------------

def real_if_close(a,tol=100):
    """If a is a complex array, return it as a real array if the imaginary
    part is close enough to zero.

    "Close enough" is defined as tol*(machine epsilon of a's element type).
    """
    a = asanyarray(a)
    if not issubclass(a.dtype.type, _nx.complexfloating):
        return a
    if tol > 1:
        import getlimits
        f = getlimits.finfo(a.dtype.type)
        tol = f.eps * tol
    if _nx.allclose(a.imag, 0, atol=tol):
        a = a.real
    return a


def asscalar(a):
    """Convert an array of size 1 to its scalar equivalent.
    """
    return a.item()

#-----------------------------------------------------------------------------

_namefromtype = {'S1' : 'character',
                 '?' : 'bool',
                 'b' : 'signed char',
                 'B' : 'unsigned char',
                 'h' : 'short',
                 'H' : 'unsigned short',
                 'i' : 'integer',
                 'I' : 'unsigned integer',
                 'l' : 'long integer',
                 'L' : 'unsigned long integer',
                 'q' : 'long long integer',
                 'Q' : 'unsigned long long integer',
                 'f' : 'single precision',
                 'd' : 'double precision',
                 'g' : 'long precision',
                 'F' : 'complex single precision',
                 'D' : 'complex double precision',
                 'G' : 'complex long double precision',
                 'S' : 'string',
                 'U' : 'unicode',
                 'V' : 'void',
                 'O' : 'object'
                 }

def typename(char):
    """Return an english description for the given data type character.
    """
    return _namefromtype[char]

#-----------------------------------------------------------------------------

#determine the "minimum common type" for a group of arrays.
array_type = [[_nx.single, _nx.double, _nx.longdouble],
              [_nx.csingle, _nx.cdouble, _nx.clongdouble]]
array_precision = {_nx.single : 0,
                   _nx.double : 1,
                   _nx.longdouble : 2,
                   _nx.csingle : 0,
                   _nx.cdouble : 1,
                   _nx.clongdouble : 2}
def common_type(*arrays):
    """Given a sequence of arrays as arguments, return the best inexact
    scalar type which is "most" common amongst them.

    The return type will always be a inexact scalar type, even if all
    the arrays are integer arrays.
    """
    is_complex = False
    precision = 0
    for a in arrays:
        t = a.dtype.type
        if iscomplexobj(a):
            is_complex = True
        if issubclass(t, _nx.integer):
            p = 1
        else:
            p = array_precision.get(t, None)
            if p is None:
                raise TypeError("can't get common type for non-numeric array")
        precision = max(precision, p)
    if is_complex:
        return array_type[1][precision]
    else:
        return array_type[0][precision]

__doc_title__ = """Basic functions used by several sub-packages and
useful to have in the main name-space."""
__doc__ = __doc_title__ + """

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
cast             --  Dictionary of functions to force cast to each type
common_type      --  Determine the 'minimum common type code' for a group
                       of arrays
mintypecode      --  Return minimal allowed common typecode.

Index tricks
==================
mgrid            --  Method which allows easy construction of N-d 'mesh-grids'
r_               --  Append and construct arrays: turns slice objects into
                       ranges and concatenates them, for 2d arrays appends
                       rows.
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

vectorize        --  a class that wraps a Python function taking scalar
                         arguments into a generalized function which
                         can handle arrays of arguments using the broadcast
                         rules of numerix Python.

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
bmat             --  Build a Matrix from blocks

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

Import tricks
=============
ppimport         --  Postpone module import until trying to use it
ppimport_attr    --  Postpone module import until trying to use its
                      attribute
ppresolve        --  Import postponed module and return it.

Machine arithmetics
===================
machar_single    --  MachAr instance storing the parameters of system
                     single precision floating point arithmetics
machar_double    --  MachAr instance storing the parameters of system
                     double precision floating point arithmetics

Threading tricks
================
ParallelExec     --  Execute commands in parallel thread.

1D array set operations
=======================
Set operations for 1D numeric arrays based on sort() function.

ediff1d          --  Array difference (auxiliary function).
unique1d         --  Unique elements of 1D array.
intersect1d      --  Intersection of 1D arrays with unique elements.
intersect1d_nu   --  Intersection of 1D arrays with any elements.
setxor1d         --  Set exclusive-or of 1D arrays with unique elements.
setmember1d      --  Return an array of shape of ar1 containing 1 where
                     the elements of ar1 are in ar2 and 0 otherwise.
union1d          --  Union of 1D arrays with unique elements.
setdiff1d        --  Set difference of 1D arrays with unique elements.

"""

depends = ['core','testing']
global_symbols = ['*']

"""
Functions to operate on polynomials.
"""

__all__ = ['poly', 'roots', 'polyint', 'polyder', 'polyadd',
           'polysub', 'polymul', 'polydiv', 'polyval', 'poly1d',
           'polyfit', 'RankWarning']

import re
import warnings
import numpy.core.numeric as NX

from numpy.core import isscalar, abs
from numpy.lib.getlimits import finfo
from numpy.lib.twodim_base import diag, vander
from numpy.lib.shape_base import hstack, atleast_1d
from numpy.lib.function_base import trim_zeros, sort_complex
eigvals = None
lstsq = None
_single_eps = finfo(NX.single).eps
_double_eps = finfo(NX.double).eps

class RankWarning(UserWarning):
    """Issued by polyfit when Vandermonde matrix is rank deficient.
    """
    pass

def get_linalg_funcs():
    "Look for linear algebra functions in numpy"
    global eigvals, lstsq
    from numpy.dual import eigvals, lstsq
    return

def _eigvals(arg):
    "Return the eigenvalues of the argument"
    try:
        return eigvals(arg)
    except TypeError:
        get_linalg_funcs()
        return eigvals(arg)

def _lstsq(X, y, rcond):
    "Do least squares on the arguments"
    try:
        return lstsq(X, y, rcond)
    except TypeError:
        get_linalg_funcs()
        return lstsq(X, y, rcond)

def poly(seq_of_zeros):
    """ Return a sequence representing a polynomial given a sequence of roots.

    If the input is a matrix, return the characteristic polynomial.

    Example:

        >>> b = roots([1,3,1,5,6])
        >>> poly(b)
        array([ 1.,  3.,  1.,  5.,  6.])

    """
    seq_of_zeros = atleast_1d(seq_of_zeros)
    sh = seq_of_zeros.shape
    if len(sh) == 2 and sh[0] == sh[1]:
        seq_of_zeros = _eigvals(seq_of_zeros)
    elif len(sh) ==1:
        pass
    else:
        raise ValueError, "input must be 1d or square 2d array."

    if len(seq_of_zeros) == 0:
        return 1.0

    a = [1]
    for k in range(len(seq_of_zeros)):
        a = NX.convolve(a, [1, -seq_of_zeros[k]], mode='full')

    if issubclass(a.dtype.type, NX.complexfloating):
        # if complex roots are all complex conjugates, the roots are real.
        roots = NX.asarray(seq_of_zeros, complex)
        pos_roots = sort_complex(NX.compress(roots.imag > 0, roots))
        neg_roots = NX.conjugate(sort_complex(
                                        NX.compress(roots.imag < 0,roots)))
        if (len(pos_roots) == len(neg_roots) and
            NX.alltrue(neg_roots == pos_roots)):
            a = a.real.copy()

    return a

def roots(p):
    """ Return the roots of the polynomial coefficients in p.

        The values in the rank-1 array p are coefficients of a polynomial.
        If the length of p is n+1 then the polynomial is
        p[0] * x**n + p[1] * x**(n-1) + ... + p[n-1]*x + p[n]
    """
    # If input is scalar, this makes it an array
    p = atleast_1d(p)
    if len(p.shape) != 1:
        raise ValueError,"Input must be a rank-1 array."

    # find non-zero array entries
    non_zero = NX.nonzero(NX.ravel(p))[0]

    # Return an empty array if polynomial is all zeros
    if len(non_zero) == 0:
        return NX.array([])

    # find the number of trailing zeros -- this is the number of roots at 0.
    trailing_zeros = len(p) - non_zero[-1] - 1

    # strip leading and trailing zeros
    p = p[int(non_zero[0]):int(non_zero[-1])+1]

    # casting: if incoming array isn't floating point, make it floating point.
    if not issubclass(p.dtype.type, (NX.floating, NX.complexfloating)):
        p = p.astype(float)

    N = len(p)
    if N > 1:
        # build companion matrix and find its eigenvalues (the roots)
        A = diag(NX.ones((N-2,), p.dtype), -1)
        A[0, :] = -p[1:] / p[0]
        roots = _eigvals(A)
    else:
        roots = NX.array([])

    # tack any zeros onto the back of the array
    roots = hstack((roots, NX.zeros(trailing_zeros, roots.dtype)))
    return roots

def polyint(p, m=1, k=None):
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
        k = NX.zeros(m, float)
    k = atleast_1d(k)
    if len(k) == 1 and m > 1:
        k = k[0]*NX.ones(m, float)
    if len(k) < m:
        raise ValueError, \
              "k must be a scalar or a rank-1 array of length 1 or >m."
    if m == 0:
        return p
    else:
        truepoly = isinstance(p, poly1d)
        p = NX.asarray(p)
        y = NX.zeros(len(p)+1, float)
        y[:-1] = p*1.0/NX.arange(len(p), 0, -1)
        y[-1] = k[0]
        val = polyint(y, m-1, k=k[1:])
        if truepoly:
            val = poly1d(val)
        return val

def polyder(p, m=1):
    """Return the mth derivative of the polynomial p.
    """
    m = int(m)
    truepoly = isinstance(p, poly1d)
    p = NX.asarray(p)
    n = len(p)-1
    y = p[:-1] * NX.arange(n, 0, -1)
    if m < 0:
        raise ValueError, "Order of derivative must be positive (see polyint)"
    if m == 0:
        return p
    else:
        val = polyder(y, m-1)
        if truepoly:
            val = poly1d(val)
        return val

def polyfit(x, y, deg, rcond=None, full=False):
    """Least squares polynomial fit.

    Required arguments

        x -- vector of sample points
        y -- vector or 2D array of values to fit
        deg -- degree of the fitting polynomial

    Keyword arguments

        rcond -- relative condition number of the fit (default len(x)*eps)
        full -- return full diagnostic output (default False)

    Returns

        full == False -- coefficients
        full == True -- coefficients, residuals, rank, singular values, rcond.

    Warns

        RankWarning -- if rank is reduced and not full output

    Do a best fit polynomial of degree 'deg' of 'x' to 'y'.  Return value is a
    vector of polynomial coefficients [pk ... p1 p0].  Eg, for n=2

      p2*x0^2 +  p1*x0 + p0 = y1
      p2*x1^2 +  p1*x1 + p0 = y1
      p2*x2^2 +  p1*x2 + p0 = y2
      .....
      p2*xk^2 +  p1*xk + p0 = yk


    Method: if X is a the Vandermonde Matrix computed from x (see
    http://mathworld.wolfram.com/VandermondeMatrix.html), then the
    polynomial least squares solution is given by the 'p' in

      X*p = y

    where X is a len(x) x N+1 matrix, p is a N+1 length vector, and y
    is a len(x) x 1 vector

    This equation can be solved as

      p = (XT*X)^-1 * XT * y

    where XT is the transpose of X and -1 denotes the inverse. However, this
    method is susceptible to rounding errors and generally the singular value
    decomposition is preferred and that is the method used here. The singular
    value method takes a paramenter, 'rcond', which sets a limit on the
    relative size of the smallest singular value to be used in solving the
    equation. This may result in lowering the rank of the Vandermonde matrix,
    in which case a RankWarning is issued. If polyfit issues a RankWarning, try
    a fit of lower degree or replace x by x - x.mean(), both of which will
    generally improve the condition number. The routine already normalizes the
    vector x by its maximum absolute value to help in this regard. The rcond
    parameter may also be set to a value smaller than its default, but this may
    result in bad fits. The current default value of rcond is len(x)*eps, where
    eps is the relative precision of the floating type being used, generally
    around 1e-7 and 2e-16 for IEEE single and double precision respectively.
    This value of rcond is fairly conservative but works pretty well when x -
    x.mean() is used in place of x.

    The warnings can be turned off by:

    >>> import numpy
    >>> import warnings
    >>> warnings.simplefilter('ignore',numpy.RankWarning)

    DISCLAIMER: Power series fits are full of pitfalls for the unwary once the
    degree of the fit becomes large or the interval of sample points is badly
    centered. The basic problem is that the powers x**n are generally a poor
    basis for the functions on the sample interval with the result that the
    Vandermonde matrix is ill conditioned and computation of the polynomial
    values is sensitive to coefficient error. The quality of the resulting fit
    should be checked against the data whenever the condition number is large,
    as the quality of polynomial fits *can not* be taken for granted. If all
    you want to do is draw a smooth curve through the y values and polyfit is
    not doing the job, try centering the sample range or look into
    scipy.interpolate, which includes some nice spline fitting functions that
    may be of use.

    For more info, see
    http://mathworld.wolfram.com/LeastSquaresFittingPolynomial.html,
    but note that the k's and n's in the superscripts and subscripts
    on that page.  The linear algebra is correct, however.

    See also polyval

    """
    order = int(deg) + 1
    x = NX.asarray(x) + 0.0
    y = NX.asarray(y) + 0.0

    # check arguments.
    if deg < 0 :
        raise ValueError, "expected deg >= 0"
    if x.ndim != 1 or x.size == 0:
        raise TypeError, "expected non-empty vector for x"
    if y.ndim < 1 or y.ndim > 2 :
        raise TypeError, "expected 1D or 2D array for y"
    if x.shape[0] != y.shape[0] :
        raise TypeError, "expected x and y to have same length"

    # set rcond
    if rcond is None :
        xtype = x.dtype
        if xtype == NX.single or xtype == NX.csingle :
            rcond = len(x)*_single_eps
        else :
            rcond = len(x)*_double_eps

    # scale x to improve condition number
    scale = abs(x).max()
    if scale != 0 :
        x /= scale

    # solve least squares equation for powers of x
    v = vander(x, order)
    c, resids, rank, s = _lstsq(v, y, rcond)

    # warn on rank reduction, which indicates an ill conditioned matrix
    if rank != order and not full:
        msg = "Polyfit may be poorly conditioned"
        warnings.warn(msg, RankWarning)

    # scale returned coefficients
    if scale != 0 :
        c /= vander([scale], order)[0]

    if full :
        return c, resids, rank, s, rcond
    else :
        return c



def polyval(p, x):
    """Evaluate the polynomial p at x.  If x is a polynomial then composition.

    Description:

      If p is of length N, this function returns the value:
      p[0]*(x**N-1) + p[1]*(x**N-2) + ... + p[N-2]*x + p[N-1]

      x can be a sequence and p(x) will be returned for all elements of x.
      or x can be another polynomial and the composite polynomial p(x) will be
      returned.

      Notice:  This can produce inaccurate results for polynomials with
      significant variability. Use carefully.
    """
    p = NX.asarray(p)
    if isinstance(x, poly1d):
        y = 0
    else:
        x = NX.asarray(x)
        y = NX.zeros_like(x)
    for i in range(len(p)):
        y = x * y + p[i]
    return y

def polyadd(a1, a2):
    """Adds two polynomials represented as sequences
    """
    truepoly = (isinstance(a1, poly1d) or isinstance(a2, poly1d))
    a1 = atleast_1d(a1)
    a2 = atleast_1d(a2)
    diff = len(a2) - len(a1)
    if diff == 0:
        val = a1 + a2
    elif diff > 0:
        zr = NX.zeros(diff, a1.dtype)
        val = NX.concatenate((zr, a1)) + a2
    else:
        zr = NX.zeros(abs(diff), a2.dtype)
        val = a1 + NX.concatenate((zr, a2))
    if truepoly:
        val = poly1d(val)
    return val

def polysub(a1, a2):
    """Subtracts two polynomials represented as sequences
    """
    truepoly = (isinstance(a1, poly1d) or isinstance(a2, poly1d))
    a1 = atleast_1d(a1)
    a2 = atleast_1d(a2)
    diff = len(a2) - len(a1)
    if diff == 0:
        val = a1 - a2
    elif diff > 0:
        zr = NX.zeros(diff, a1.dtype)
        val = NX.concatenate((zr, a1)) - a2
    else:
        zr = NX.zeros(abs(diff), a2.dtype)
        val = a1 - NX.concatenate((zr, a2))
    if truepoly:
        val = poly1d(val)
    return val


def polymul(a1, a2):
    """Multiplies two polynomials represented as sequences.
    """
    truepoly = (isinstance(a1, poly1d) or isinstance(a2, poly1d))
    a1,a2 = poly1d(a1),poly1d(a2)
    val = NX.convolve(a1, a2)
    if truepoly:
        val = poly1d(val)
    return val

def polydiv(u, v):
    """Computes q and r polynomials so that u(s) = q(s)*v(s) + r(s)
    and deg r < deg v.
    """
    truepoly = (isinstance(u, poly1d) or isinstance(u, poly1d))
    u = atleast_1d(u)
    v = atleast_1d(v)
    m = len(u) - 1
    n = len(v) - 1
    scale = 1. / v[0]
    q = NX.zeros((max(m-n+1,1),), float)
    r = u.copy()
    for k in range(0, m-n+1):
        d = scale * r[k]
        q[k] = d
        r[k:k+n+1] -= d*v
    while NX.allclose(r[0], 0, rtol=1e-14) and (r.shape[-1] > 1):
        r = r[1:]
    if truepoly:
        q = poly1d(q)
        r = poly1d(r)
    return q, r

_poly_mat = re.compile(r"[*][*]([0-9]*)")
def _raise_power(astr, wrap=70):
    n = 0
    line1 = ''
    line2 = ''
    output = ' '
    while 1:
        mat = _poly_mat.search(astr, n)
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


class poly1d(object):
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

    p = poly1d([1,2,3], variable='lambda') will use lambda in the
    string representation of p.
    """
    coeffs = None
    order = None
    variable = None
    def __init__(self, c_or_r, r=0, variable=None):
        if isinstance(c_or_r, poly1d):
            for key in c_or_r.__dict__.keys():
                self.__dict__[key] = c_or_r.__dict__[key]
            if variable is not None:
                self.__dict__['variable'] = variable
            return
        if r:
            c_or_r = poly(c_or_r)
        c_or_r = atleast_1d(c_or_r)
        if len(c_or_r.shape) > 1:
            raise ValueError, "Polynomial must be 1d only."
        c_or_r = trim_zeros(c_or_r, trim='f')
        if len(c_or_r) == 0:
            c_or_r = NX.array([0.])
        self.__dict__['coeffs'] = c_or_r
        self.__dict__['order'] = len(c_or_r) - 1
        if variable is None:
            variable = 'x'
        self.__dict__['variable'] = variable

    def __array__(self, t=None):
        if t:
            return NX.asarray(self.coeffs, t)
        else:
            return NX.asarray(self.coeffs)

    def __repr__(self):
        vals = repr(self.coeffs)
        vals = vals[6:-1]
        return "poly1d(%s)" % vals

    def __len__(self):
        return self.order

    def __str__(self):
        thestr = "0"
        var = self.variable

        # Remove leading zeros
        coeffs = self.coeffs[NX.logical_or.accumulate(self.coeffs != 0)]
        N = len(coeffs)-1

        for k in range(len(coeffs)):
            coefstr ='%.4g' % abs(coeffs[k])
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
                elif coefstr == 'b':
                    newstr = var
                else:
                    newstr = '%s %s' % (coefstr, var)
            else:
                if coefstr == '0':
                    newstr = ''
                elif coefstr == 'b':
                    newstr = '%s**%d' % (var, power,)
                else:
                    newstr = '%s %s**%d' % (coefstr, var, power)

            if k > 0:
                if newstr != '':
                    if coeffs[k] < 0:
                        thestr = "%s - %s" % (thestr, newstr)
                    else:
                        thestr = "%s + %s" % (thestr, newstr)
            elif (k == 0) and (newstr != '') and (coeffs[k] < 0):
                thestr = "-%s" % (newstr,)
            else:
                thestr = newstr
        return _raise_power(thestr)


    def __call__(self, val):
        return polyval(self.coeffs, val)

    def __neg__(self):
        return poly1d(-self.coeffs)

    def __pos__(self):
        return self

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
        for _ in range(val):
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
            return polydiv(self, other)

    def __rdiv__(self, other):
        if isscalar(other):
            return poly1d(other/self.coeffs)
        else:
            other = poly1d(other)
            return polydiv(other, self)

    def __eq__(self, other):
        return NX.alltrue(self.coeffs == other.coeffs)

    def __ne__(self, other):
        return NX.any(self.coeffs != other.coeffs)

    def __setattr__(self, key, val):
        raise ValueError, "Attributes cannot be changed this way."

    def __getattr__(self, key):
        if key in ['r', 'roots']:
            return roots(self.coeffs)
        elif key in ['c','coef','coefficients']:
            return self.coeffs
        elif key in ['o']:
            return self.order
        else:
            try:
                return self.__dict__[key]
            except KeyError:
                raise AttributeError("'%s' has no attribute '%s'" % (self.__class__, key))

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
            zr = NX.zeros(key-self.order, self.coeffs.dtype)
            self.__dict__['coeffs'] = NX.concatenate((zr, self.coeffs))
            self.__dict__['order'] = key
            ind = 0
        self.__dict__['coeffs'][ind] = val
        return

    def __iter__(self):
        return iter(self.coeffs)

    def integ(self, m=1, k=0):
        """Return the mth analytical integral of this polynomial.
        See the documentation for polyint.
        """
        return poly1d(polyint(self.coeffs, m=m, k=k))

    def deriv(self, m=1):
        """Return the mth derivative of this polynomial.
        """
        return poly1d(polyder(self.coeffs, m=m))

# Stuff to do on module import

warnings.simplefilter('always',RankWarning)

"""A file interface for handling local and remote data files.
The goal of datasource is to abstract some of the file system operations when
dealing with data files so the researcher doesn't have to know all the
low-level details.  Through datasource, a researcher can obtain and use a
file with one function call, regardless of location of the file.

DataSource is meant to augment standard python libraries, not replace them.
It should work seemlessly with standard file IO operations and the os module.

DataSource files can originate locally or remotely:

- local files : '/home/guido/src/local/data.txt'
- URLs (http, ftp, ...) : 'http://www.scipy.org/not/real/data.txt'

DataSource files can also be compressed or uncompressed.  Currently only gzip
and bz2 are supported.

Example:

    >>> # Create a DataSource, use os.curdir (default) for local storage.
    >>> ds = datasource.DataSource()
    >>>
    >>> # Open a remote file.
    >>> # DataSource downloads the file, stores it locally in:
    >>> #     './www.google.com/index.html'
    >>> # opens the file and returns a file object.
    >>> fp = ds.open('http://www.google.com/index.html')
    >>>
    >>> # Use the file as you normally would
    >>> fp.read()
    >>> fp.close()

"""

__docformat__ = "restructuredtext en"

import bz2
import gzip
import os
import tempfile
from shutil import rmtree
from urllib2 import urlopen, URLError
from urlparse import urlparse


# TODO: .zip support, .tar support?
_file_openers = {".gz":gzip.open, ".bz2":bz2.BZ2File, None:file}


def open(path, mode='r', destpath=os.curdir):
    """Open ``path`` with ``mode`` and return the file object.

    If ``path`` is an URL, it will be downloaded, stored in the DataSource
    directory and opened from there.

    *Parameters*:

        path : {string}

        mode : {string}, optional

        destpath : {string}, optional
            Destination directory where URLs will be downloaded and stored.

    *Returns*:

        file object

    """

    ds = DataSource(destpath)
    return ds.open(path, mode)


class DataSource (object):
    """A generic data source file (file, http, ftp, ...).

    DataSources could be local files or remote files/URLs.  The files may
    also be compressed or uncompressed.  DataSource hides some of the low-level
    details of downloading the file, allowing you to simply pass in a valid
    file path (or URL) and obtain a file object.

    *Methods*:

        - exists : test if the file exists locally or remotely
        - abspath : get absolute path of the file in the DataSource directory
        - open : open the file

    *Example URL DataSource*::

        # Initialize DataSource with a local directory, default is os.curdir.
        ds = DataSource('/home/guido')

        # Open remote file.
        # File will be downloaded and opened from here:
        #     /home/guido/site/xyz.txt
        ds.open('http://fake.xyz.web/site/xyz.txt')

    *Example using DataSource for temporary files*::

        # Initialize DataSource with 'None' for the local directory.
        ds = DataSource(None)

        # Open local file.
        # Opened file exists in a temporary directory like:
        #     /tmp/tmpUnhcvM/foobar.txt
        # Temporary directories are deleted when the DataSource is deleted.
        ds.open('/home/guido/foobar.txt')

    *Notes*:
        BUG : URLs require a scheme string ('http://') to be used.
              www.google.com will fail.

              >>> repos.exists('www.google.com/index.html')
              False

              >>> repos.exists('http://www.google.com/index.html')
              True

    """

    def __init__(self, destpath=os.curdir):
        """Create a DataSource with a local path at destpath."""
        if destpath:
            self._destpath = os.path.abspath(destpath)
            self._istmpdest = False
        else:
            self._destpath = tempfile.mkdtemp()
            self._istmpdest = True

    def __del__(self):
        # Remove temp directories
        if self._istmpdest:
            rmtree(self._destpath)

    def _iszip(self, filename):
        """Test if the filename is a zip file by looking at the file extension.
        """
        fname, ext = os.path.splitext(filename)
        return ext in _file_openers.keys()

    def _iswritemode(self, mode):
        """Test if the given mode will open a file for writing."""

        # Currently only used to test the bz2 files.
        _writemodes = ("w", "+")
        for c in mode:
            if c in _writemodes:
                return True
        return False

    def _splitzipext(self, filename):
        """Split zip extension from filename and return filename.

        *Returns*:
            base, zip_ext : {tuple}

        """

        if self._iszip(filename):
            return os.path.splitext(filename)
        else:
            return filename, None

    def _possible_names(self, filename):
        """Return a tuple containing compressed filename variations."""
        names = [filename]
        if not self._iszip(filename):
            for zipext in _file_openers.keys():
                if zipext:
                    names.append(filename+zipext)
        return names

    def _isurl(self, path):
        """Test if path is a net location.  Tests the scheme and netloc."""

        # BUG : URLs require a scheme string ('http://') to be used.
        #       www.google.com will fail.
        #       Should we prepend the scheme for those that don't have it and
        #       test that also?  Similar to the way we append .gz and test for
        #       for compressed versions of files.

        scheme, netloc, upath, uparams, uquery, ufrag = urlparse(path)
        return bool(scheme and netloc)

    def _cache(self, path):
        """Cache the file specified by path.

        Creates a copy of the file in the datasource cache.

        """

        upath = self.abspath(path)

        # ensure directory exists
        if not os.path.exists(os.path.dirname(upath)):
            os.makedirs(os.path.dirname(upath))

        # TODO: Doesn't handle compressed files!
        if self._isurl(path):
            try:
                openedurl = urlopen(path)
                file(upath, 'w').write(openedurl.read())
            except URLError:
                raise URLError("URL not found: ", path)
        else:
            try:
                # TODO: Why not just copy the file with shutils.copyfile?
                fp = file(path, 'r')
                file(upath, 'w').write(fp.read())
            except IOError:
                raise IOError("File not found: ", path)
        return upath

    def _findfile(self, path):
        """Searches for ``path`` and returns full path if found.

        If path is an URL, _findfile will cache a local copy and return
        the path to the cached file.
        If path is a local file, _findfile will return a path to that local
        file.

        The search will include possible compressed versions of the file and
        return the first occurence found.

        """

        # Build list of possible local file paths
        if not self._isurl(path):
            # Valid local paths
            filelist = self._possible_names(path)
            # Paths in self._destpath
            filelist += self._possible_names(self.abspath(path))
        else:
            # Cached URLs in self._destpath
            filelist = self._possible_names(self.abspath(path))
            # Remote URLs
            filelist = filelist + self._possible_names(path)

        for name in filelist:
            if self.exists(name):
                if self._isurl(name):
                    name = self._cache(name)
                return name
        return None

    def abspath(self, path):
        """Return absolute path of ``path`` in the DataSource directory.

        If ``path`` is an URL, the ``abspath`` will be either the location
        the file exists locally or the location it would exist when opened
        using the ``open`` method.

        The functionality is idential to os.path.abspath.

        *Parameters*:

            path : {string}
                Can be a local file or a remote URL.

        *Returns*:

            Complete path, rooted in the DataSource destination directory.

        *See Also*:

            `open` : Method that downloads and opens files.

        """

        # TODO:  This should be more robust.  Handles case where path includes
        #        the destpath, but not other sub-paths. Failing case:
        #        path = /home/guido/datafile.txt
        #        destpath = /home/alex/
        #        upath = self.abspath(path)
        #        upath == '/home/alex/home/guido/datafile.txt'

        # handle case where path includes self._destpath
        splitpath = path.split(self._destpath, 2)
        if len(splitpath) > 1:
            path = splitpath[1]
        scheme, netloc, upath, uparams, uquery, ufrag = urlparse(path)
        return os.path.join(self._destpath, netloc, upath.strip(os.sep))

    def exists(self, path):
        """Test if ``path`` exists.

        Test if ``path`` exists as (and in this order):

        - a local file.
        - a remote URL that have been downloaded and stored locally in the
          DataSource directory.
        - a remote URL that has not been downloaded, but is valid and
          accessible.

        *Parameters*:

            path : {string}
                Can be a local file or a remote URL.

        *Returns*:

            boolean

        *See Also*:

            `abspath`

        *Notes*

            When ``path`` is an URL, ``exist`` will return True if it's either
            stored locally in the DataSource directory, or is a valid remote
            URL.  DataSource does not discriminate between to two, the file
            is accessible if it exists in either location.

        """

        # Test local path
        if os.path.exists(path):
            return True

        # Test cached url
        upath = self.abspath(path)
        if os.path.exists(upath):
            return True

        # Test remote url
        if self._isurl(path):
            try:
                netfile = urlopen(path)
                del(netfile)
                return True
            except URLError:
                return False
        return False

    def open(self, path, mode='r'):
        """Open ``path`` with ``mode`` and return the file object.

        If ``path`` is an URL, it will be downloaded, stored in the DataSource
        directory and opened from there.

        *Parameters*:

            path : {string}

            mode : {string}, optional


        *Returns*:

            file object

        """

        # TODO: There is no support for opening a file for writing which
        #       doesn't exist yet (creating a file).  Should there be?

        # TODO: Add a ``subdir`` parameter for specifying the subdirectory
        #       used to store URLs in self._destpath.

        if self._isurl(path) and self._iswritemode(mode):
            raise ValueError("URLs are not writeable")

        # NOTE: _findfile will fail on a new file opened for writing.
        found = self._findfile(path)
        if found:
            _fname, ext = self._splitzipext(found)
            if ext == 'bz2':
                mode.replace("+", "")
            return _file_openers[ext](found, mode=mode)
        else:
            raise IOError("%s not found." % path)


class Repository (DataSource):
    """A data Repository where multiple DataSource's share a base URL/directory.

    Repository extends DataSource by prepending a base URL (or directory) to
    all the files it handles. Use a Repository when you will be working with
    multiple files from one base URL.  Initialize the Respository with the
    base URL, then refer to each file by it's filename only.

    *Methods*:

        - exists : test if the file exists locally or remotely
        - abspath : get absolute path of the file in the DataSource directory
        - open : open the file

    *Toy example*::

        # Analyze all files in the repository.
        repos = Repository('/home/user/data/dir/')
        for filename in filelist:
            fp = repos.open(filename)
            fp.analyze()
            fp.close()

        # Similarly you could use a URL for a repository.
        repos = Repository('http://www.xyz.edu/data')

    """

    def __init__(self, baseurl, destpath=os.curdir):
        """Create a Repository with a shared url or directory of baseurl."""
        DataSource.__init__(self, destpath=destpath)
        self._baseurl = baseurl

    def __del__(self):
        DataSource.__del__(self)

    def _fullpath(self, path):
        """Return complete path for path.  Prepends baseurl if necessary."""
        splitpath = path.split(self._baseurl, 2)
        if len(splitpath) == 1:
            result = os.path.join(self._baseurl, path)
        else:
            result = path    # path contains baseurl already
        return result

    def _findfile(self, path):
        """Extend DataSource method to prepend baseurl to ``path``."""
        return DataSource._findfile(self, self._fullpath(path))

    def abspath(self, path):
        """Extend DataSource method to prepend baseurl to ``path``."""
        return DataSource.abspath(self, self._fullpath(path))

    def exists(self, path):
        """Extend DataSource method to prepend baseurl to ``path``."""
        return DataSource.exists(self, self._fullpath(path))

    def open(self, path, mode='r'):
        """Extend DataSource method to prepend baseurl to ``path``."""
        return DataSource.open(self, self._fullpath(path), mode)

    def listdir(self):
        '''List files in the source Repository.'''
        if self._isurl(self._baseurl):
            raise NotImplementedError, \
                  "Directory listing of URLs, not supported yet."
        else:
            return os.listdir(self._baseurl)

"""
Module of functions that are like ufuncs in acting on arrays and optionally
storing results in an output array.
"""
__all__ = ['fix', 'isneginf', 'isposinf', 'log2']

import numpy.core.numeric as nx
from numpy.core.numeric import asarray, empty, isinf, signbit, asanyarray
import numpy.core.umath as umath

def fix(x, y=None):
    """ Round x to nearest integer towards zero.
    """
    x = asanyarray(x)
    if y is None:
        y = nx.floor(x)
    else:
        nx.floor(x, y)
    if x.ndim == 0:
        if (x<0):
            y += 1
    else:
        y[x<0] = y[x<0]+1
    return y

def isposinf(x, y=None):
    """Return a boolean array y with y[i] True for x[i] = +Inf.

    If y is an array, the result replaces the contents of y.
    """
    if y is None:
        x = asarray(x)
        y = empty(x.shape, dtype=nx.bool_)
    umath.logical_and(isinf(x), ~signbit(x), y)
    return y

def isneginf(x, y=None):
    """Return a boolean array y with y[i] True for x[i] = -Inf.

    If y is an array, the result replaces the contents of y.
    """
    if y is None:
        x = asarray(x)
        y = empty(x.shape, dtype=nx.bool_)
    umath.logical_and(isinf(x), signbit(x), y)
    return y

_log2 = umath.log(2)
def log2(x, y=None):
    """Returns the base 2 logarithm of x

    If y is an array, the result replaces the contents of y.
    """
    x = asanyarray(x)
    if y is None:
        y = umath.log(x)
    else:
        umath.log(x, y)
    y /= _log2
    return y

