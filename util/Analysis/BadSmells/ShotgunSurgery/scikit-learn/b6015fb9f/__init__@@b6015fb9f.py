#! /usr/bin/env python
# Last Change: Fri Oct 20 11:00 AM 2006 J

from info import __doc__

from gauss_mix import GmParamError, GM
from gmm_em import GmmParamError, GMM, EM
from online_em import OnGMM as _OnGMM

__all__ = [s for s in dir() if not s.startswith('_')]

from numpy.testing import NumpyTest
test = NumpyTest().test
