#! /usr/bin/env python
# Last Change: Sat Jul 21 09:00 PM 2007 J

# Copyright (C) 2007-2009 Cournapeau David <cournape@gmail.com>
#               2010 Fabian Pedregosa <fabian.pedregosa@inria.fr>

descr   = """A set of python modules for machine learning and data mining"""

import os

DISTNAME            = 'scikits.learn' 
DESCRIPTION         = 'A set of python modules for machine learning and data mining'
LONG_DESCRIPTION    = descr
MAINTAINER          = 'Fabian Pedregosa'
MAINTAINER_EMAIL    = 'fabian.pedregosa@inria.fr'
URL                 = 'http://scikit-learn.sourceforge.net'
LICENSE             = 'new BSD'
DOWNLOAD_URL        = 'http://sourceforge.net/projects/scikit-learn/files/'
VERSION             = '0.5-git'

import setuptools # we are using a setuptools namespace
from numpy.distutils.core import setup

def configuration(parent_package='',top_path=None):
    if os.path.exists('MANIFEST'): os.remove('MANIFEST')

    from numpy.distutils.misc_util import Configuration
    config = Configuration(None, parent_package,top_path,
        namespace_packages=['scikits'])

    config.add_subpackage('scikits.learn')
    config.add_data_files('scikits/__init__.py')

    return config

if __name__ == "__main__":
    setup(configuration = configuration,
        name = DISTNAME,
        maintainer  = MAINTAINER,
        include_package_data = True,
        maintainer_email = MAINTAINER_EMAIL,
        description = DESCRIPTION,
        license = LICENSE,
        url = URL,
        version = VERSION,
        download_url = DOWNLOAD_URL,
        long_description = LONG_DESCRIPTION,
        zip_safe=False, # the package can run out of an .egg file
        classifiers = 
            ['Intended Audience :: Science/Research',
             'Intended Audience :: Developers',
             'License :: OSI Approved',
             'Programming Language :: C',
             'Programming Language :: Python',
             'Topic :: Software Development',
             'Topic :: Scientific/Engineering',
             'Operating System :: Microsoft :: Windows',
             'Operating System :: POSIX',
             'Operating System :: Unix',
             'Operating System :: MacOS'
             ]
    )

__import__('pkg_resources').declare_namespace(__name__)

# Author: Alexandre Gramfort <alexandre.gramfort@inria.fr>
#
# License: BSD Style.

import numpy as np

def confusion_matrix(y, y_):
    """
    compute confusion matrix
    to evaluate the accuracy of a classification result

    By definition a confusion matrix cm is such that

    cm[i,j] is equal to the number of observations known to be in group i
    but predicted to be in group j

    Parameters
    ==========

    y : array, shape = [n_samples]
        true targets

    y_ : array, shape = [n_samples]
        estimated targets

    Returns
    =======
    cm : array, shape = [n_classes,n_classes]
        confusion matrix

    References
    ==========
    http://en.wikipedia.org/wiki/Confusion_matrix
    """
    # removing possible NaNs in targets (they are ignored)
    clean_y = y[np.isfinite(y)].ravel()
    clean_y_ = y_[np.isfinite(y_)].ravel()

    labels = np.r_[np.unique(clean_y).ravel(),np.unique(clean_y_).ravel()]
    labels = np.unique(labels)
    n_labels = labels.size

    cm = np.empty((n_labels,n_labels))
    for i, label_i in enumerate(labels):
        for j, label_j in enumerate(labels):
            cm[i,j] = np.sum(np.logical_and(y==label_i, y_==label_j))

    return cm

def roc(y, probas_):
    """compute Receiver operating characteristic (ROC)

    Parameters
    ==========

    y : array, shape = [n_samples]
        true targets

    probas_ : array, shape = [n_samples]
        estimated probabilities

    Returns
    =======
    fpr : array, shape = [n]
        False Positive Rates

    tpr : array, shape = [n]
        True Positive Rates

    thresholds : array, shape = [n]
        Thresholds on proba_ used to compute fpr and tpr

    References
    ==========
    http://en.wikipedia.org/wiki/Receiver_operating_characteristic
    """
    y = y.ravel()
    probas_ = probas_.ravel()
    thresholds = np.sort(np.unique(probas_))[::-1]
    n_thresholds = thresholds.size
    tpr = np.empty(n_thresholds) # True positive rate
    fpr = np.empty(n_thresholds) # False positive rate
    n_pos = float(np.sum(y==1)) # nb of true positive
    n_neg = float(np.sum(y==0)) # nb of true negative
    for i, t in enumerate(thresholds):
        tpr[i] = np.sum(y[probas_>=t]==1) / n_pos
        fpr[i] = np.sum(y[probas_>=t]==0) / n_neg

    return fpr, tpr, thresholds

def auc(x, y):
    """Compute Area Under the Curve (AUC)
    using the trapezoidal rule

    Parameters
    ==========

    x : array, shape = [n]
        x coordinates

    y : array, shape = [n]
        y coordinates

    Returns
    =======
    auc : float

    """
    x = np.asanyarray(x)
    y = np.asanyarray(y)
    h = np.diff(x)
    area = np.sum(h * (y[1:]+y[:-1])) / 2.0
    return area

def precision_recall(y, probas_):
    """compute Precision-Recall

    Parameters
    ==========

    y : array, shape = [n_samples]
        true targets

    probas_ : array, shape = [n_samples]
        estimated probabilities

    Returns
    =======
    precision : array, shape = [n]
        Precision values

    recall : array, shape = [n]
        Recall values

    thresholds : array, shape = [n]
        Thresholds on proba_ used to compute precision and recall

    References
    ==========
    http://en.wikipedia.org/wiki/Precision_and_recall
    """
    y = y.ravel()
    probas_ = probas_.ravel()
    thresholds = np.sort(np.unique(probas_))
    n_thresholds = thresholds.size + 1
    precision = np.empty(n_thresholds)
    recall = np.empty(n_thresholds)
    for i, t in enumerate(thresholds):
        true_pos = np.sum(y[probas_>=t]==1)
        false_pos = np.sum(y[probas_>=t]==0)
        false_neg = np.sum(y[probas_<t]==1)
        precision[i] = true_pos / float(true_pos + false_pos)
        recall[i] = true_pos / float(true_pos + false_neg)

    precision[-1] = 1.0
    recall[-1] = 0.0
    return precision, recall, thresholds


###############################################################################
# Loss functions


def zero_one(y_pred, y_true):
    """Zero-One loss
    returns the number of differences
    """
    return np.sum(y_pred != y_true)


def mean_square_error(y_pred, y_true):
    """Mean Square Error
    returns the mean square error
    """
    return np.linalg.norm(y_pred != y_true) ** 2


def explained_variance(y_pred, y_true):
    """Explained variance
    returns the explained variance
    """
    return 1 - np.var(y_true - y_pred) / np.var(y_true)


#
# Gaussian Mixture Models
#
# Author: Ron Weiss <ronweiss@gmail.com>
#         Fabian Pedregosa <fabian.pedregosa@inria.fr>
#

import itertools

import numpy as np
from scipy import cluster

from .base import BaseEstimator

#######################################################
#
# This module is experimental. It is meant to replace
# the em module, but before that happens, some work
# must be done:
#
#   - migrate the plotting methods from em (see
#     em.gauss_mix.GM.plot)
#   - profile and benchmark
#   - adopt naming scheme used in other modules (svm, glm)
#     for estimated parameters (trailing underscore, etc.)
#
#######################################################


def logsum(A, axis=None):
    """Computes the sum of A assuming A is in the log domain.

    Returns log(sum(exp(A), axis)) while minimizing the possibility of
    over/underflow.
    """
    Amax = A.max(axis)
    if axis and A.ndim > 1:
        shape = list(A.shape)
        shape[axis] = 1
        Amax.shape = shape
    Asum = np.log(np.sum(np.exp(A - Amax), axis))
    Asum += Amax.reshape(Asum.shape)
    if axis:
        # Look out for underflow.
        Asum[np.isnan(Asum)] = - np.Inf
    return Asum


def normalize(A, axis=None):
    A += np.finfo(float).eps
    Asum = A.sum(axis)
    if axis and A.ndim > 1:
        # Make sure we don't divide by zero.
        Asum[Asum == 0] = 1
        shape = list(A.shape)
        shape[axis] = 1
        Asum.shape = shape
    return A / Asum


def lmvnpdf(obs, means, covars, cvtype='diag'):
    """Compute the log probability under a multivariate Gaussian distribution.

    Parameters
    ----------
    obs : array_like, shape (O, D)
        List of D-dimensional data points.  Each row corresponds to a
        single data point.
    means : array_like, shape (C, D)
        List of D-dimensional mean vectors for C Gaussians.  Each row
        corresponds to a single mean vector.
    covars : array_like
        List of C covariance parameters for each Gaussian.  The shape
        depends on `cvtype`:
            (C,)      if 'spherical',
            (D, D)    if 'tied',
            (C, D)    if 'diag',
            (C, D, D) if 'full'
    cvtype : string
        Type of the covariance parameters.  Must be one of
        'spherical', 'tied', 'diag', 'full'.  Defaults to 'diag'.

    Returns
    -------
    lpr : array_like, shape (O, C)
        Array containing the log probabilities of each data point in
        `obs` under each of the C multivariate Gaussian distributions.
    """
    lmvnpdf_dict = {'spherical': _lmvnpdfspherical,
                    'tied': _lmvnpdftied,
                    'diag': _lmvnpdfdiag,
                    'full': _lmvnpdffull}
    return lmvnpdf_dict[cvtype](obs, means, covars)


def sample_gaussian(mean, covar, cvtype='diag', n=1):
    """Generate random samples from a Gaussian distribution.

    Parameters
    ----------
    mean : array_like, shape (n_dim,)
        Mean of the distribution.
    covars : array_like
        Covariance of the distribution.  The shape depends on `cvtype`:
            scalar  if 'spherical',
            (D)     if 'diag',
            (D, D)  if 'tied', or 'full'
    cvtype : string
        Type of the covariance parameters.  Must be one of
        'spherical', 'tied', 'diag', 'full'.  Defaults to 'diag'.
    n : int
        Number of samples to generate.

    Returns
    -------
    obs : array, shape (n, n_dim)
        Randomly generated sample
    """
    ndim = len(mean)
    rand = np.random.randn(ndim, n)
    if n == 1:
        rand.shape = (ndim,)

    if cvtype == 'spherical':
        rand *= np.sqrt(covar)
    elif cvtype == 'diag':
        rand = np.dot(np.diag(np.sqrt(covar)), rand)
    else:
        U, s, V = np.linalg.svd(covar)
        sqrtS = np.diag(np.sqrt(s))
        sqrt_covar = np.dot(U, np.dot(sqrtS, V))
        rand = np.dot(sqrt_covar, rand)

    return (rand.T + mean).T


class GMM(BaseEstimator):
    """Gaussian Mixture Model

    Representation of a Gaussian mixture model probability distribution.
    This class allows for easy evaluation of, sampling from, and
    maximum-likelihood estimation of the parameters of a GMM distribution.

    Attributes
    ----------
    cvtype : string (read-only)
        String describing the type of covariance parameters used by
        the GMM.  Must be one of 'spherical', 'tied', 'diag', 'full'.
    n_dim : int (read-only)
        Dimensionality of the Gaussians.
    n_states : int (read-only)
        Number of states (mixture components).
    weights : array, shape (`n_states`,)
        Mixing weights for each mixture component.
    means : array, shape (`n_states`, `n_dim`)
        Mean parameters for each mixture component.
    covars : array
        Covariance parameters for each mixture component.  The shape
        depends on `cvtype`:
            (`n_states`,)                   if 'spherical',
            (`n_dim`, `n_dim`)              if 'tied',
            (`n_states`, `n_dim`)           if 'diag',
            (`n_states`, `n_dim`, `n_dim`)  if 'full'
    labels : list, len `n_states`
        Optional labels for each mixture component.

    Methods
    -------
    decode(X)
        Find most likely mixture components for each point in `X`.
    eval(X)
        Compute the log likelihood of `X` under the model and the
        posterior distribution over mixture components.
    fit(X)
        Estimate model parameters from `X` using the EM algorithm.
    predict(X)
        Like decode, find most likely mixtures components for each
        observation in `X`.
    rvs(n=1)
        Generate `n` samples from the model.
    score(X)
        Compute the log likelihood of `X` under the model.

    Examples
    --------
    >>> import numpy as np
    >>> g = GMM(n_states=2, n_dim=1)
    >>> # The initial parameters are fixed.
    >>> print np.round(g.weights, 2)
    [ 0.5  0.5]
    >>> print np.round(g.means, 2)
    [[ 0.]
     [ 0.]]
    >>> print np.round(g.covars, 2)
    [[[ 1.]]
    <BLANKLINE>
     [[ 1.]]]

    >>> # Generate random observations with two modes centered on 0
    >>> # and 10 to use for training.
    >>> np.random.seed(0)
    >>> obs = np.concatenate((np.random.randn(100, 1),
    ...                       10 + np.random.randn(300, 1)))
    >>> _ = g.fit(obs)
    >>> print np.round(g.weights, 2)
    [ 0.75  0.25]
    >>> print np.round(g.means, 2)
    [[ 9.94]
     [ 0.06]]
    >>> print np.round(g.covars, 2)
    [[[ 0.96]]
    <BLANKLINE>
     [[ 1.02]]]
    >>> print g.predict([[0], [2], [9], [10]])
    [1 1 0 0]
    >>> print np.round(g.score([[0], [2], [9], [10]]), 2)
    [-2.32 -4.16 -1.65 -1.19]

    >>> # Refit the model on new data (initial parameters remain the
    >>> #same), this time with an even split between the two modes.
    >>> _ = g.fit(20 * [[0]] +  20 * [[10]])
    >>> print np.round(g.weights, 2)
    [ 0.5  0.5]
    """

    def __init__(self, n_states=1, n_dim=1, cvtype='diag', weights=None,
                 means=None, covars=None):
        """Create a Gaussian mixture model

        Initializes parameters such that every mixture component has
        zero mean and identity covariance.

        Parameters
        ----------
        n_states : int
            Number of mixture components.
        n_dim : int
            Dimensionality of the mixture components.
        cvtype : string (read-only)
            String describing the type of covariance parameters to
            use.  Must be one of 'spherical', 'tied', 'diag', 'full'.
            Defaults to 'diag'.
        """

        self._n_states = n_states
        self._n_dim = n_dim
        self._cvtype = cvtype

        if not cvtype in ['spherical', 'tied', 'diag', 'full']:
            raise ValueError('bad cvtype')

        if weights is None:
            weights = np.tile(1.0 / n_states, n_states)
        self.weights = weights

        if means is None:
            means = np.zeros((n_states, n_dim))
        self.means = means

        if covars is None:
            covars = _distribute_covar_matrix_to_match_cvtype(
                np.eye(n_dim), cvtype, n_states)
        self.covars = covars

        self.labels = [None] * n_states

    # Read-only properties.
    @property
    def cvtype(self):
        """Covariance type of the model.

        Must be one of 'spherical', 'tied', 'diag', 'full'.
        """
        return self._cvtype

    @property
    def n_dim(self):
        """Dimensionality of the mixture components."""
        return self._n_dim

    @property
    def n_states(self):
        """Number of mixture components in the model."""
        return self._n_states

    def _get_covars(self):
        """Return covars as a full matrix."""
        if self.cvtype == 'full':
            return self._covars
        elif self.cvtype == 'diag':
            return [np.diag(cov) for cov in self._covars]
        elif self.cvtype == 'tied':
            return [self._covars] * self._n_states
        elif self.cvtype == 'spherical':
            return [np.eye(self._n_states) * f for f in self._covars]

    def _set_covars(self, covars):
        covars = np.asanyarray(covars)
        _validate_covars(covars, self._cvtype, self._n_states, self._n_dim)
        self._covars = covars

    covars = property(_get_covars, _set_covars)

    def _get_means(self):
        """Mean parameters for each mixture component."""
        return self._means

    def _set_means(self, means):
        means = np.asarray(means)
        if means.shape != (self._n_states, self._n_dim):
            raise ValueError('means must have shape (n_states, n_dim)')
        self._means = means.copy()

    means = property(_get_means, _set_means)

    def _get_weights(self):
        """Mixing weights for each mixture component."""
        return np.exp(self._log_weights)

    def _set_weights(self, weights):
        if len(weights) != self._n_states:
            raise ValueError('weights must have length n_states')
        if not np.allclose(np.sum(weights), 1.0):
            raise ValueError('weights must sum to 1.0')

        self._log_weights = np.log(np.asarray(weights).copy())

    weights = property(_get_weights, _set_weights)

    def eval(self, obs):
        """Evaluate the model on data

        Compute the log probability of `obs` under the model and
        return the posterior distribution (responsibilities) of each
        mixture component for each element of `obs`.

        Parameters
        ----------
        obs : array_like, shape (n, n_dim)
            List of n_dim-dimensional data points.  Each row corresponds to a
            single data point.

        Returns
        -------
        logprob : array_like, shape (n,)
            Log probabilities of each data point in `obs`
        posteriors: array_like, shape (n, n_states)
            Posterior probabilities of each mixture component for each
            observation
        """
        obs = np.asanyarray(obs)
        lpr = (lmvnpdf(obs, self._means, self._covars, self._cvtype)
               + self._log_weights)
        logprob = logsum(lpr, axis=1)
        posteriors = np.exp(lpr - logprob[:,np.newaxis])
        return logprob, posteriors

    def score(self, obs):
        """Compute the log probability under the model.

        Parameters
        ----------
        obs : array_like, shape (n, n_dim)
            List of n_dim-dimensional data points.  Each row corresponds to a
            single data point.

        Returns
        -------
        logprob : array_like, shape (n,)
            Log probabilities of each data point in `obs`
        """
        logprob, posteriors = self.eval(obs)
        return logprob

    def decode(self, obs):
        """Find most likely mixture components for each point in `obs`.

        Parameters
        ----------
        obs : array_like, shape (n, n_dim)
            List of n_dim-dimensional data points.  Each row corresponds to a
            single data point.

        Returns
        -------
        logprobs : array_like, shape (n,)
            Log probability of each point in `obs` under the model.
        components : array_like, shape (n,)
            Index of the most likelihod mixture components for each observation
        """
        logprob, posteriors = self.eval(obs)
        return logprob, posteriors.argmax(axis=1)

    def predict(self, X):
        """Predict label for data.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]

        Returns
        -------
        C : array, shape = [n_samples]
        """
        logprob, components = self.decode(X)
        return components

    def rvs(self, n=1):
        """Generate random samples from the model.

        Parameters
        ----------
        n : int
            Number of samples to generate.

        Returns
        -------
        obs : array_like, shape (n, n_dim)
            List of samples
        """
        weight_pdf = self.weights
        weight_cdf = np.cumsum(weight_pdf)

        obs = np.empty((n, self._n_dim))
        for x in xrange(n):
            rand = np.random.rand()
            c = (weight_cdf > rand).argmax()
            if self._cvtype == 'tied':
                cv = self._covars
            else:
                cv = self._covars[c]
            obs[x] = sample_gaussian(self._means[c], cv, self._cvtype)
        return obs

    def fit(self, X, n_iter=10, min_covar=1e-3, thresh=1e-2, params='wmc',
            init_params='wmc', **kwargs):
        """Estimate model parameters with the expectation-maximization
        algorithm.

        A initialization step is performed before entering the em
        algorithm. If you want to avoid this step, set the keyword
        argument init_params to the empty string ''. Likewise, if you
        would like just to do an initialization, call this method with
        n_iter=0.

        Parameters
        ----------
        X : array_like, shape (n, n_dim)
            List of n_dim-dimensional data points.  Each row corresponds to a
            single data point.
        n_iter : int, optional
            Number of EM iterations to perform.
        min_covar : float, optional
            Floor on the diagonal of the covariance matrix to prevent
            overfitting.  Defaults to 1e-3.
        thresh : float, optional
            Convergence threshold.
        params : string, optional
            Controls which parameters are updated in the training
            process.  Can contain any combination of 'w' for weights,
            'm' for means, and 'c' for covars.  Defaults to 'wmc'.
        init_params : string, optional
            Controls which parameters are updated in the initialization
            process.  Can contain any combination of 'w' for weights,
            'm' for means, and 'c' for covars.  Defaults to 'wmc'.
        kwargs : keyword, optional
            Keyword arguments passed to scipy.cluster.vq.kmeans2
        """

        ## initialization step

        X = np.asanyarray(X, dtype=np.float64)

        if 'm' in init_params:
            if not 'minit' in kwargs:
                kwargs.update({'minit': 'points'})
            self._means, tmp = cluster.vq.kmeans2(X, self._n_states, **kwargs)

        if 'w' in init_params:
            self.weights = np.tile(1.0 / self._n_states, self._n_states)

        if 'c' in init_params:
            cv = np.cov(X.T)
            if not cv.shape:
                cv.shape = (1, 1)
            self._covars = _distribute_covar_matrix_to_match_cvtype(
                cv, self._cvtype, self._n_states)

        # EM algorithm
        logprob = []
        for i in xrange(n_iter):
            # Expectation step
            curr_logprob, posteriors = self.eval(X)
            logprob.append(curr_logprob.sum())

            # Check for convergence.
            if i > 0 and abs(logprob[-1] - logprob[-2]) < thresh:
                break

            # Maximization step
            self._do_mstep(X, posteriors, params, min_covar)

        return self

    def _do_mstep(self, X, posteriors, params, min_covar=0):
            w = posteriors.sum(axis=0)
            avg_obs = np.dot(posteriors.T, X)
            norm = 1.0 / (w[:,np.newaxis] + 1e-200)

            if 'w' in params:
                self._log_weights = np.log(w / w.sum())
            if 'm' in params:
                self._means = avg_obs * norm
            if 'c' in params:
                covar_mstep_func = _covar_mstep_funcs[self._cvtype]
                self._covars = covar_mstep_func(self, X, posteriors,
                                                avg_obs, norm, min_covar)

            return w


##
## some helper routines
##


def _lmvnpdfdiag(obs, means=0.0, covars=1.0):
    nobs, ndim = obs.shape
    # (x-y).T A (x-y) = x.T A x - 2x.T A y + y.T A y
    #lpr = -0.5 * (np.tile((np.sum((means**2) / covars, 1)
    #                  + np.sum(np.log(covars), 1))[np.newaxis,:], (nobs,1))
    lpr = -0.5 * (ndim * np.log(2 * np.pi) + np.sum(np.log(covars), 1)
                  + np.sum((means ** 2) / covars, 1)
                  - 2 * np.dot(obs, (means / covars).T)
                  + np.dot(obs ** 2, (1.0 / covars).T))
    return lpr


def _lmvnpdfspherical(obs, means=0.0, covars=1.0):
    cv = covars.copy()
    if covars.ndim == 1:
        cv = cv[:,np.newaxis]
    return _lmvnpdfdiag(obs, means, np.tile(cv, (1, obs.shape[-1])))


def _lmvnpdftied(obs, means, covars):
    nobs, ndim = obs.shape
    # (x-y).T A (x-y) = x.T A x - 2x.T A y + y.T A y
    icv = np.linalg.inv(covars)
    lpr = -0.5 * (ndim * np.log(2 * np.pi) + np.log(np.linalg.det(covars))
                  + np.sum(obs * np.dot(obs, icv), 1)[:,np.newaxis]
                  - 2 * np.dot(np.dot(obs, icv), means.T)
                  + np.sum(means * np.dot(means, icv), 1))
    return lpr


def _lmvnpdffull(obs, means, covars):
    # FIXME: this representation of covars is going to lose for caching
    nobs, ndim = obs.shape
    nmix = len(means)
    lpr = np.empty((nobs,nmix))
    for c, (mu, cv) in enumerate(itertools.izip(means, covars)):
        icv = np.linalg.inv(cv)
        lpr[:,c] = -0.5 * (ndim * np.log(2 * np.pi)
                           + np.log(np.linalg.det(cv)))
        for o, currobs in enumerate(obs):
            dzm = (currobs - mu)
            lpr[o,c] += -0.5 * np.dot(np.dot(dzm, icv), dzm.T)
        #dzm = (obs - mu)
        #lpr[:,c] = -0.5 * (np.dot(np.dot(dzm, np.linalg.inv(cv)), dzm.T)
        #                   + np.log(2 * np.pi) + np.linalg.det(cv)).diagonal()
    return lpr


def _validate_covars(covars, cvtype, nmix, ndim):
    if cvtype == 'spherical':
        if len(covars) != nmix:
            raise ValueError("'spherical' covars must have length nmix")
        elif np.any(covars <= 0):
            raise ValueError("'spherical' covars must be non-negative")
    elif cvtype == 'tied':
        if covars.shape != (ndim, ndim):
            raise ValueError("'tied' covars must have shape (ndim, ndim)")
        elif (not np.allclose(covars, covars.T)
              or np.any(np.linalg.eigvalsh(covars) <= 0)):
            raise ValueError("'tied' covars must be symmetric, "
                             "positive-definite")
    elif cvtype == 'diag':
        if covars.shape != (nmix, ndim):
            raise ValueError("'diag' covars must have shape (nmix, ndim)")
        elif np.any(covars <= 0):
            raise ValueError("'diag' covars must be non-negative")
    elif cvtype == 'full':
        if covars.shape != (nmix, ndim, ndim):
            raise ValueError("'full' covars must have shape "
                             "(nmix, ndim, ndim)")
        for n,cv in enumerate(covars):
            if (not np.allclose(cv, cv.T)
                or np.any(np.linalg.eigvalsh(cv) <= 0)):
                raise ValueError("component %d of 'full' covars must be "
                                 "symmetric, positive-definite" % n)


def _distribute_covar_matrix_to_match_cvtype(tiedcv, cvtype, n_states):
    if cvtype == 'spherical':
        cv = np.tile(np.diag(tiedcv).mean(), n_states)
    elif cvtype == 'tied':
        cv = tiedcv
    elif cvtype == 'diag':
        cv = np.tile(np.diag(tiedcv), (n_states, 1))
    elif cvtype == 'full':
        cv = np.tile(tiedcv, (n_states, 1, 1))
    else:
        raise (ValueError,
               "cvtype must be one of 'spherical', 'tied', 'diag', 'full'")
    return cv


def _covar_mstep_diag(gmm, obs, posteriors, avg_obs, norm, min_covar):
    # For column vectors:
    # covars_c = average((obs(t) - means_c) (obs(t) - means_c).T,
    #                    weights_c)
    # (obs(t) - means_c) (obs(t) - means_c).T
    #     = obs(t) obs(t).T - 2 obs(t) means_c.T + means_c means_c.T
    #
    # But everything here is a row vector, so all of the
    # above needs to be transposed.
    avg_obs2 = np.dot(posteriors.T, obs * obs) * norm
    avg_means2 = gmm._means ** 2
    avg_obs_means = gmm._means * avg_obs * norm
    return avg_obs2 - 2 * avg_obs_means + avg_means2 + min_covar


def _covar_mstep_spherical(*args):
    return _covar_mstep_diag(*args).mean(axis=1)


def _covar_mstep_full(gmm, obs, posteriors, avg_obs, norm, min_covar):
    print "THIS IS BROKEN"
    # Eq. 12 from K. Murphy, "Fitting a Conditional Linear Gaussian
    # Distribution"
    avg_obs2 = np.dot(obs.T, obs)
    #avg_obs2 = np.dot(obs.T, avg_obs)
    cv = np.empty((gmm._n_states, gmm._n_dim, gmm._n_dim))
    for c in xrange(gmm._n_states):
        wobs = obs.T * posteriors[:,c]
        avg_obs2 = np.dot(wobs, obs) / posteriors[:,c].sum()
        mu = gmm._means[c][np.newaxis]
        cv[c] = (avg_obs2 - np.dot(mu, mu.T)
                 + min_covar * np.eye(gmm._n_dim))
    return cv


def _covar_mstep_tied2(*args):
    return _covar_mstep_full(*args).mean(axis=0)


def _covar_mstep_tied(gmm, obs, posteriors, avg_obs, norm, min_covar):
    print "THIS IS BROKEN"
    # Eq. 15 from K. Murphy, "Fitting a Conditional Linear Gaussian
    avg_obs2 = np.dot(obs.T, obs)
    avg_means2 = np.dot(gmm._means.T, gmm._means)
    return (avg_obs2 - avg_means2 + min_covar * np.eye(gmm._n_dim))


def _covar_mstep_slow(gmm, obs, posteriors, avg_obs, norm, min_covar):
    w = posteriors.sum(axis=0)
    covars = np.zeros(gmm._covars.shape)
    for c in xrange(gmm._n_states):
        mu = gmm._means[c]
        #cv = np.dot(mu.T, mu)
        avg_obs2 = np.zeros((gmm._n_dim, gmm._n_dim))
        for t,o in enumerate(obs):
            avg_obs2 += posteriors[t,c] * np.outer(o, o)
        cv = (avg_obs2 / w[c]
              - 2 * np.outer(avg_obs[c] / w[c], mu)
              + np.outer(mu, mu)
              + min_covar * np.eye(gmm._n_dim))
        if gmm.cvtype == 'spherical':
            covars[c] = np.diag(cv).mean()
        elif gmm.cvtype == 'diag':
            covars[c] = np.diag(cv)
        elif gmm.cvtype == 'full':
            covars[c] = cv
        elif gmm.cvtype == 'tied':
            covars += cv / gmm._n_states
    return covars


_covar_mstep_funcs = {'spherical': _covar_mstep_spherical,
                      'diag': _covar_mstep_diag,
                      #'tied': _covar_mstep_tied,
                      #'full': _covar_mstep_full,
                      'tied': _covar_mstep_slow,
                      'full': _covar_mstep_slow}

import exceptions, warnings

import numpy as np
import scipy.linalg as linalg
import scipy.ndimage as ndimage

from .base import BaseEstimator, ClassifierMixin

class LDA(BaseEstimator, ClassifierMixin):
    """
    Linear Discriminant Analysis (LDA)

    Parameters
    ----------
    X : array-like, shape = [n_samples, n_features]
        Training vector, where n_samples in the number of samples and
        n_features is the number of features.
    y : array, shape = [n_samples]
        Target vector relative to X

    priors : array, optional, shape = [n_classes]
        Priors on classes

    use_svd : bool, optional
         Specify if the SVD from scipy should be used.

    Attributes
    ----------
    `means_` : array-like, shape = [n_classes, n_features]
        Class means
    `xbar_` : float, shape = [n_features]
        Over all mean
    `priors_` : array-like, shape = [n_classes]
        Class priors (sum to 1)
    `covariance_` : array-like, shape = [n_features, n_features]
        Covariance matrix (shared by all classes)

    Methods
    -------
    fit(X, y) : self
        Fit the model

    predict(X) : array
        Predict using the model.

    Examples
    --------
    >>> import numpy as np
    >>> from scikits.learn.lda import LDA
    >>> X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])
    >>> y = np.array([1, 1, 1, 2, 2, 2])
    >>> clf = LDA()
    >>> clf.fit(X, y)
    LDA(priors=None, use_svd=True)
    >>> print clf.predict([[-0.8, -1]])
    [1]

    See also
    --------
    QDA

    """
    def __init__(self, priors=None, use_svd=True):
        #use_svd : if True, use linalg.svd alse use computational
        #          trick with covariance matrix
        if not priors is None:
            self.priors = np.asarray(priors)
        else: self.priors = None
        self.use_svd = use_svd

    def fit(self, X, y, store_covariance=False, tol=1.0e-4, **params):
        """
        Fit the LDA model according to the given training data and parameters.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]
            Training vector, where n_samples in the number of samples and
            n_features is the number of features.
        y : array, shape = [n_samples]
            Target values (integers)
        store_covariance : boolean
            If True the covariance matrix (shared by all classes) is computed
            and stored in self.covariance_ attribute.
        """
        self._set_params(**params)
        X = np.asanyarray(X)
        y = np.asanyarray(y)
        if X.ndim!=2:
            raise exceptions.ValueError('X must be a 2D array')
        n_samples = X.shape[0]
        n_features = X.shape[1]
        classes = np.unique(y).astype(np.int32)
        n_classes = classes.size
        if n_classes < 2:
            raise exceptions.ValueError('y has less than 2 classes')
        classes_indices = [(y == c).ravel() for c in classes]
        if self.priors is None:
            counts = np.array(ndimage.measurements.sum(np.ones(len(y)),
                                                    y, index=classes))
            self.priors_ = counts / float(n_samples)
        else:
            self.priors_ = self.priors

        # Group means n_classes*n_features matrix
        means = []
        Xc = []
        cov = None
        if store_covariance:
            cov = np.zeros((n_features, n_features))
        for group_indices in classes_indices:
            Xg = X[group_indices, :]
            meang = Xg.mean(0)
            means.append(meang)
            # centered group data
            Xgc = Xg - meang
            Xc.append(Xgc)
            if store_covariance:
                cov += np.dot(Xgc.T, Xgc)
        if store_covariance:
            cov /= (n_samples - n_classes)
            self.covariance_ = cov
            
        means = np.asarray(means)
        Xc = np.concatenate(Xc, 0)

        # ----------------------------
        # 1) within (univariate) scaling by with classes std-dev
        scaling = 1. / Xc.std(0)
        fac = float(1) / (n_samples - n_classes)
        # ----------------------------
        # 2) Within variance scaling
        X = np.sqrt(fac) * (Xc * scaling)
        # SVD of centered (within)scaled data
        if self.use_svd == True:
            U, S, V = linalg.svd(X, full_matrices=0)
        else:
            S, V = self.svd(X)

        rank = np.sum(S > tol)
        if rank < n_features:
            warnings.warn("Variables are collinear")
        # Scaling of within covariance is: V' 1/S
        scaling = (scaling * V.T[:, :rank].T).T / S[:rank]
        ## ----------------------------
        ## 3) Between variance scaling
        # Overall mean
        xbar = np.dot(self.priors_, means)
        # Scale weighted centers
        X = np.dot(((np.sqrt((n_samples * self.priors_)*fac)) *
                          (means - xbar).T).T, scaling)
        # Centers are living in a space with n_classes-1 dim (maximum)
        # Use svd to find projection in the space spamed by the
        # (n_classes) centers
        if self.use_svd:
            U, S, V = linalg.svd(X, full_matrices=0)
        else:
            S, V = self._svd(X)

        rank = np.sum(S > tol*S[0])
        # compose the scalings
        scaling = np.dot(scaling, V.T[:, :rank])
        self.scaling = scaling
        self.means_ = means
        self.xbar_ = xbar
        self.classes = classes
        return self

    def _svd(self, X):
        #computational trick to compute svd. U, S, V=linalg.svd(X)
        K = np.dot(X.T, X)
        S, V = linalg.eigh(K)
        S = np.sqrt(np.maximum(S, 1e-30))
        S_sort = -np.sort(-S)[:X.shape[0]]
        S_argsort = np.argsort(-S).tolist()
        V = V.T[S_argsort, :]
        V = V[:X.shape[0], :]
        return S_sort, V

    def decision_function(self, X):
        """
        This function return the decision function values related to each
        class on an array of test vectors X.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]

        Returns
        -------
        C : array, shape = [n_samples, n_classes]
        """
        X = np.asanyarray(X)
        scaling = self.scaling
        # Remove overall mean (center) and scale
        # a) data
        X = np.dot(X - self.xbar_, scaling)
        # b) centers
        dm = np.dot(self.means_ - self.xbar_, scaling)
        # for each class k, compute the linear discrinant function(p. 87 Hastie)
        # of sphered (scaled data)
        return -0.5 * np.sum(dm ** 2, 1) + \
                np.log(self.priors_) + np.dot(X, dm.T)


    def predict(self, X):
        """
        This function does classification on an array of test vectors X.

        The predicted class C for each sample in X is returned.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]

        Returns
        -------
        C : array, shape = [n_samples]
        """
        d = self.decision_function(X)
        y_pred = self.classes[d.argmax(1)]
        return y_pred

    def predict_proba(self, X):
        """
        This function return posterior probabilities of classification
        according to each class on an array of test vectors X.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]

        Returns
        -------
        C : array, shape = [n_samples, n_classes]
        """
        values = self.decision_function(X)
        # compute the likelihood of the underlying gaussian models
        # up to a multiplicative constant.
        likelihood = np.exp(values - values.min(axis=1)[:, np.newaxis])
        # compute posterior probabilities
        return likelihood / likelihood.sum(axis=1)[:, np.newaxis]

import numpy as np
from . import _liblinear

from .base import ClassifierMixin
from .svm import BaseLibLinear

class LogisticRegression(BaseLibLinear, ClassifierMixin):
    """
    Logistic Regression.

    Implements L1 and L2 regularized logistic regression.

    Parameters
    ----------
    X : array-like, shape = [n_samples, n_features]
        Training vector, where n_samples in the number of samples and
        n_features is the number of features.
    Y : array, shape = [n_samples]
        Target vector relative to X

    penalty : string, 'l1' or 'l2'
        Used to specify the norm used in the penalization

    C : float
        Specifies the strength of the regularization. The smaller it is
        the bigger in the regularization.

    intercept : bool, default: True
        Specifies if a constant (a.k.a. bias or intercept) should be
        added the decision function

    Attributes
    ----------

    `coef_` : array, shape = [n_classes-1, n_features]
        Coefficient of the features in the decision function.

    `intercept_` : array, shape = [n_classes-1]
        intercept (a.k.a. bias) added to the decision function.
        It is available only when parameter intercept is set to True

    Methods
    -------
    fit(X, Y) : self
        Fit the model

    predict(X) : array
        Predict using the model.

    See also
    --------
    LinearSVC

    References
    ----------
    LIBLINEAR -- A Library for Large Linear Classification
    http://www.csie.ntu.edu.tw/~cjlin/liblinear/
    """

    def __init__(self, penalty='l2', eps=1e-4, C=1.0, has_intercept=True):
        super(LogisticRegression, self).__init__ (penalty=penalty, loss='lr',
            dual=False, eps=eps, C=C, has_intercept=has_intercept)

    def predict_proba(self, T):
        T = np.asanyarray(T, dtype=np.float64, order='C')
        return _liblinear.predict_prob_wrap(T, self.raw_coef_, self._get_solver_type(),
                                      self.eps, self.C,
                                      self._weight_label,
                                      self._weight, self.label_,
                                      self._get_bias())

"""
k-Nearest Neighbor Algorithm.

Uses BallTree algorithm, which is an efficient way to perform fast
neighbor searches in high dimensionality.
"""
import numpy as np
from scipy import stats

from .base import BaseEstimator, ClassifierMixin
from .ball_tree import BallTree

class Neighbors(BaseEstimator, ClassifierMixin):
  """
  Classifier implementing k-Nearest Neighbor Algorithm.

  Parameters
  ----------
  data : array-like, shape (n, k)
      The data points to be indexed. This array is not copied, and so
      modifying this data will result in bogus results.
  labels : array
      An array representing labels for the data (only arrays of
      integers are supported).
  k : int
      default number of neighbors.
  window_size : int
      the default window size.

  Examples
  --------
  >>> samples = [[0.,0.,1.], [1.,0.,0.], [2.,2.,2.], [2.,5.,4.]]
  >>> labels = [0,0,1,1]
  >>> neigh = Neighbors(k=3)
  >>> neigh.fit(samples, labels)
  Neighbors(k=3, window_size=1)
  >>> print neigh.predict([[0,0,0]])
  [ 0.]
  """

  def __init__(self, k=5, window_size=1):
    """
    Internally uses the ball tree datastructure and algorithm for fast
    neighbors lookups on high dimensional datasets.
    """
    self.k = k
    self.window_size = window_size

  def fit(self, X, Y=()):
    # we need Y to be an integer, because after we'll use it an index
    self.Y = np.asanyarray(Y, dtype=np.int)
    self.ball_tree = BallTree(X, self.window_size)
    return self

  def kneighbors(self, data, k=None):
    """
    Finds the K-neighbors of a point.

    Parameters
    ----------
    point : array-like
        The new point.
    k : int
        Number of neighbors to get (default is the value
        passed to the constructor).

    Returns
    -------
    dist : array
        Array representing the lenghts to point.
    ind : array
        Array representing the indices of the nearest points in the
        population matrix.

    Examples
    --------
    In the following example, we construnct a Neighbors class from an
    array representing our data set and ask who's the closest point to
    [1,1,1]

    >>> import numpy as np
    >>> samples = [[0., 0., 0.], [0., .5, 0.], [1., 1., .5]]
    >>> labels = [0, 0, 1]
    >>> neigh = Neighbors(k=1)
    >>> neigh.fit(samples, labels)
    Neighbors(k=1, window_size=1)
    >>> print neigh.kneighbors([1., 1., 1.])
    (array(0.5), array(2))

    As you can see, it returns [0.5], and [2], which means that the
    element is at distance 0.5 and is the third element of samples
    (indexes start at 0). You can also query for multiple points:

    >>> print neigh.kneighbors([[0., 1., 0.], [1., 0., 1.]])
    (array([ 0.5       ,  1.11803399]), array([1, 2]))

    """
    if k is None: 
        k=self.k
    return self.ball_tree.query(data, k=k)


  def predict(self, T, k=None):
    """
    Predict the class labels for the provided data.

    Parameters
    ----------
    test: array
        A 2-D array representing the test point.
    k : int
        Number of neighbors to get (default is the value
        passed to the constructor).

    Returns
    -------
    labels: array
        List of class labels (one for each data sample).

    Examples
    --------
    >>> import numpy as np
    >>> samples = [[0., 0., 0.], [0., .5, 0.], [1., 1., .5]]
    >>> labels = [0, 0, 1]
    >>> neigh = Neighbors(k=1)
    >>> neigh.fit(samples, labels)
    Neighbors(k=1, window_size=1)
    >>> print neigh.predict([.2, .1, .2])
    0
    >>> print neigh.predict([[0., -1., 0.], [3., 2., 0.]])
    [0 1]
    """
    T = np.asanyarray(T)
    if k is None: 
        k=self.k
    return _predict_from_BallTree(self.ball_tree, self.Y, T, k=k)


def _predict_from_BallTree(ball_tree, Y, test, k):
    """
    Predict target from BallTree object containing the data points.

    This is a helper method, not meant to be used directly. It will
    not check that input is of the correct type.
    """
    Y_ = Y[ball_tree.query(test, k=k, return_distance=False)]
    if k == 1: return Y_
    return (stats.mode(Y_, axis=1)[0]).ravel()

# Author: Alexandre Gramfort <alexandre.gramfort@inria.fr>
#         Vincent Michel <vincent.michel@inria.fr>
#
# License: BSD Style.

"""Recursive feature elimination
for feature ranking
"""

import numpy as np
from .base import BaseEstimator

class RFE(BaseEstimator):
    """
    Feature ranking with Recursive feature elimination

    Parameters
    ----------
    estimator : object
         object

    n_features : int
        Number of features to select

    percentage : float
        The percentage of features to remove at each iteration
        Should be between (0, 1].  By default 0.1 will be taken.

    Attributes
    ----------
    `support_` : array-like, shape = [n_features]
        Mask of estimated support

    `ranking_` : array-like, shape = [n_features]
        Mask of the ranking of features

    Methods
    -------
    fit(X, y) : self
        Fit the model

    transform(X) : array
        Reduce X to support

    Examples
    --------
    >>>

    References
    ----------
    Guyon, I., Weston, J., Barnhill, S., & Vapnik, V. (2002). Gene
    selection for cancer classification using support vector
    machines. Mach. Learn., 46(1-3), 389--422.
    """

    def __init__(self, estimator=None, n_features=None, percentage=0.1):
        self.n_features = n_features
        self.percentage = percentage
        self.estimator = estimator

    def fit(self, X, y):
        """Fit the RFE model according to the given training data and parameters.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]
            Training vector, where n_samples in the number of samples and
            n_features is the number of features.
        y : array, shape = [n_samples]
            Target values (integers in classification, real numbers in
            regression)
        """
        n_features_total = X.shape[1]
        estimator = self.estimator
        support_ = np.ones(n_features_total, dtype=np.bool)
        ranking_ = np.ones(n_features_total, dtype=np.int)
        while np.sum(support_) > self.n_features:
            estimator.fit(X[:,support_], y)
            # rank features based on coef_ (handle multi class)
            abs_coef_ = np.sum(estimator.coef_ ** 2, axis=0)
            sorted_abs_coef_ = np.sort(abs_coef_)
            thresh = sorted_abs_coef_[np.int(np.sum(support_)*self.percentage)]
            support_[support_] = abs_coef_ > thresh
            ranking_[support_] += 1
        self.support_ = support_
        self.ranking_ = ranking_
        return self

    def transform(self, X, copy=True):
        """Reduce X to the features selected during the fit

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]
            Vector, where n_samples in the number of samples and
            n_features is the number of features.
        """
        X_r = X[:,self.support_]
        return X_r.copy() if copy else X_r



class RFECV(RFE):
    """
    Feature ranking with Recursive feature elimination.
    Automatic tuning by Cross-validation.
    """

    def __init__(self, estimator=None, n_features=None, percentage=0.1,
                  loss_func=None):
        self.n_features = n_features
        self.percentage = percentage
        self.estimator = estimator
        self.loss_func = loss_func

    def fit(self, X, y, cv=None):
        """Fit the RFE model according to the given training data and
            parameters. Tuning by cross-validation

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]
            Training vector, where n_samples in the number of samples and
            n_features is the number of features.
        y : array, shape = [n_samples]
            Target values (integers in classification, real numbers in
            regression)
        cv : cross-validation instance
        """
        rfe = RFE(estimator=self.estimator, n_features=self.n_features,
                          percentage=self.percentage)
        self.ranking_ = rfe.fit(X, y).ranking_
        clf = self.estimator
        n_models = np.max(self.ranking_)
        self.cv_scores_ = np.zeros(n_models)

        for train, test in cv:
            ranking_ = rfe.fit(X[train], y[train]).ranking_

            assert n_models == np.max(ranking_)
            for k in range(n_models):
                mask = ranking_ >= (k+1)
                clf.fit(X[train][:,mask], y[train])
                y_pred = clf.predict(X[test][:,mask])
                self.cv_scores_[k] += self.loss_func(y[test], y_pred)

        self.support_ = self.ranking_ >= (np.argmin(self.cv_scores_) + 1)
        return self


"""
Machine Learning module in python
=================================

scikits.learn is a Python module integrating classique machine
learning algorithms in the tightly-nit world of scientific Python
packages (numpy, scipy, matplotlib).

It aims to provide simple and efficient solutions to learning problems
that are accessible to everybody and reusable in various contexts:
machine-learning as a versatile tool for science and engineering.

See http://scikit-learn.sourceforge.net for complete documentation.
"""

from . import cross_val
from . import ball_tree
from . import cluster
from . import gmm
from . import glm
from . import logistic
from . import lda
from . import metrics
from . import svm
from . import features

__all__ = ['cross_val', 'ball_tree', 'cluster', 'gmm', 'glm', 'logistic', 'lda',
           'metrics', 'svm', 'features']

__version__ = '0.5-git'


# Author: Vincent Michel <vincent.michel@inria.fr>
# License: BSD Style.
import numpy as np

from .base import BaseEstimator, ClassifierMixin

class GNB(BaseEstimator, ClassifierMixin):
    """
    Gaussian Naive Bayes (GNB)

    Parameters
    ----------
    X : array-like, shape = [n_samples, n_features]
        Training vector, where n_samples in the number of samples and
        n_features is the number of features.
    y : array, shape = [n_samples]
        Target vector relative to X

    Attributes
    ----------
    proba_y : array, shape = nb of classes
              probability of each class.
    theta : array of shape nb_class*nb_features
            mean of each feature for the different class
    sigma : array of shape nb_class*nb_features
            variance of each feature for the different class


    Methods
    -------
    fit(X, y) : self
        Fit the model

    predict(X) : array
        Predict using the model.

    predict_proba(X) : array
        Predict the probability of each class using the model.

    Examples
    --------
    >>> X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])
    >>> Y = np.array([1, 1, 1, 2, 2, 2])
    >>> clf = GNB()
    >>> clf.fit(X, Y)
    GNB()
    >>> print clf.predict([[-0.8, -1]])
    [1]

    See also
    --------

    """
    def __init__(self):
        pass

    def fit(self, X, y):
        theta = []
        sigma = []
        proba_y = []
        unique_y = np.unique(y)
        for yi in unique_y:
            theta.append(np.mean(X[y==yi,:], 0))
            sigma.append(np.var(X[y==yi,:], 0))
            proba_y.append(np.float(np.sum(y==yi)) / np.size(y))
        self.theta = np.array(theta)
        self.sigma = np.array(sigma)
        self.proba_y = np.array(proba_y)
        self.unique_y = unique_y
        return self


    def predict(self, X):
        y_pred = self.unique_y[np.argmax(self.predict_proba(X),1)]
        return y_pred


    def predict_proba(self, X):
        joint_log_likelihood = []
        for i in range(np.size(self.unique_y)):
            jointi = np.log(self.proba_y[i])
            n_ij = - 0.5 * np.sum(np.log(np.pi*self.sigma[i,:]))
            n_ij -= 0.5 * np.sum( ((X - self.theta[i,:])**2) /\
                                    (self.sigma[i,:]),1)
            joint_log_likelihood.append(jointi+n_ij)
        joint_log_likelihood = np.array(joint_log_likelihood).T
        proba = np.exp(joint_log_likelihood)
        proba = proba / np.sum(proba,1)[:,np.newaxis]
        return proba



from os.path import join
import warnings
import numpy
import sys
if sys.version_info[0] < 3:
    from ConfigParser import ConfigParser
else:
    from configparser import ConfigParser

def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration
    from numpy.distutils.system_info import get_info, get_standard_file, \
        BlasNotFoundError
    config = Configuration('learn', parent_package, top_path)

    site_cfg  = ConfigParser()
    site_cfg.read(get_standard_file('site.cfg'))

    config.add_subpackage('datasets')
    config.add_subpackage('features')
    config.add_subpackage('features/tests')
    config.add_subpackage('cluster')
    config.add_subpackage('cluster/tests')
    config.add_subpackage('feature_selection')
    config.add_subpackage('feature_selection/tests')
    config.add_subpackage('sparse')
    config.add_subpackage('sparse/tests/')
    config.add_subpackage('utils')
    config.add_subpackage('utils/tests')
    config.add_subpackage('externals')

    # Section LibSVM
    libsvm_includes = [numpy.get_include()]
    libsvm_libraries = []
    libsvm_library_dirs = []
    libsvm_sources = [join('src', 'libsvm', '_libsvm.c')]

    # we try to link against system-wide libsvm
    if site_cfg.has_section('libsvm'):
        libsvm_includes.append(site_cfg.get('libsvm', 'include_dirs'))
        libsvm_libraries.append(site_cfg.get('libsvm', 'libraries'))
        libsvm_library_dirs.append(site_cfg.get('libsvm', 'library_dirs'))
    else:
        # if not specified, we build our own libsvm
        libsvm_sources.append(join('src', 'libsvm', 'svm.cpp'))

    config.add_extension('_libsvm',
                         sources=libsvm_sources,
                         include_dirs=libsvm_includes,
                         libraries=libsvm_libraries,
                         library_dirs=libsvm_library_dirs,
                         depends=[join('src', 'libsvm', 'svm.h'),
                                  join('src', 'libsvm', 'libsvm_helper.c')],
                         # add this for gdb debug
                         extra_compile_args=['-O0 -fno-inline']
                                  )

    ### liblinear module
    blas_sources = [join('src', 'blas', 'daxpy.c'),
                    join('src', 'blas', 'ddot.c'),
                    join('src', 'blas', 'dnrm2.c'),
                    join('src', 'blas', 'dscal.c')]

    liblinear_sources = [join('src', 'liblinear', '_liblinear.c'),
                         join('src', 'liblinear', '*.cpp')]

    # we try to link agains system-wide blas
    blas_info = get_info('blas_opt', 0)

    if not blas_info:
        config.add_library('blas', blas_sources)
        warnings.warn(BlasNotFoundError.__doc__)

    config.add_extension('_liblinear',
                         sources=liblinear_sources,
                         libraries = blas_info.pop('libraries', ['blas']),
                         include_dirs=['src',
                                       numpy.get_include(),
                                       blas_info.pop('include_dirs', [])],
                         depends=[join('src', 'liblinear', '*.h')],
                         **blas_info)

    ## end liblinear module

    # minilear needs cblas, fortran-compiled BLAS will not be sufficient
    blas_info = get_info('blas_opt', 0)
    if (not blas_info) or (
        ('NO_ATLAS_INFO', 1) in blas_info.get('define_macros', [])) :
        config.add_library('cblas',
                           sources=[
                               join('src', 'cblas', '*.c'),
                               ]
                           )
        cblas_libs = ['cblas']
        blas_info.pop('libraries', None)
    else:
        cblas_libs = blas_info.pop('libraries', [])

    minilearn_sources = [
        join('src', 'minilearn', 'lars.c'),
        join('src', 'minilearn', '_minilearn.c')]

    config.add_extension('_minilearn',
                         sources = minilearn_sources,
                         libraries = cblas_libs,
                         include_dirs=[join('src', 'minilearn'),
                                       join('src', 'cblas'),
                                       numpy.get_include(),
                                       blas_info.pop('include_dirs', [])],
                         extra_compile_args=['-std=c99'] + \
                                             blas_info.pop('extra_compile_args', []),
                         **blas_info
                         )

    config.add_extension('ball_tree',
                         sources=[join('src', 'BallTree.cpp')],
                         include_dirs=[numpy.get_include()]
                         )

    config.add_subpackage('utils')

    # this has to be build *after* cblas
    config.add_subpackage('glm')

    # add the test directory
    config.add_data_dir('tests')

    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())

"""
Quadratic Discriminant Analysis
"""

# Author: Matthieu Perrot <matthieu.perrot@gmail.com>
#
# License: BSD Style.

import exceptions
import warnings

import numpy as np
import scipy.ndimage as ndimage

from .base import BaseEstimator, ClassifierMixin

# FIXME :
# - in fit(X, y) method, many checks are common with other models (in particular
#   LDA model) and should be factorized : may be in BaseEstimator ?

class QDA(BaseEstimator, ClassifierMixin):
    """
    Quadratic Discriminant Analysis (QDA)

    Parameters
    ----------
    X : array-like, shape = [n_samples, n_features]
        Training vector, where n_samples in the number of samples and
        n_features is the number of features.
    y : array, shape = [n_samples]
        Target vector relative to X

    priors : array, optional, shape = [n_classes]
        Priors on classes

    Attributes
    ----------
    `means_` : array-like, shape = [n_classes, n_features]
        Class means
    `priors_` : array-like, shape = [n_classes]
        Class priors (sum to 1)
    `covariances_` : list of array-like, shape = [n_features, n_features]
        Covariance matrices of each class

    Methods
    -------
    fit(X, y) : self
        Fit the model

    predict(X) : array
        Predict using the model.

    Examples
    --------
    >>> from scikits.learn.qda import QDA
    >>> import numpy as np
    >>> X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])
    >>> y = np.array([1, 1, 1, 2, 2, 2])
    >>> clf = QDA()
    >>> clf.fit(X, y)
    QDA(priors=None)
    >>> print clf.predict([[-0.8, -1]])
    [1]

    See also
    --------
    LDA

    """
    def __init__(self, priors=None):
        if priors is not None:
            self.priors = np.asarray(priors)
        else: self.priors = None

    def fit(self, X, y, store_covariances=False, tol=1.0e-4, **params):
        """
        Fit the QDA model according to the given training data and parameters.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]
            Training vector, where n_samples in the number of samples and
            n_features is the number of features.
        y : array, shape = [n_samples]
            Target values (integers)
        store_covariances : boolean
            If True the covariance matrices are computed and stored in
            self.covariances_ attribute.
        """
        self._set_params(**params)
        X = np.asanyarray(X)
        y = np.asanyarray(y)
        if X.ndim!=2:
            raise exceptions.ValueError('X must be a 2D array')
        if X.shape[0] != y.shape[0]:
            raise ValueError("Incompatible shapes")
        n_samples = X.shape[0]
        n_features = X.shape[1]
        classes = np.unique(y).astype(np.int32)
        n_classes = classes.size
        if n_classes < 2:
            raise exceptions.ValueError('y has less than 2 classes')
        classes_indices = [(y == c).ravel() for c in classes]
        if self.priors is None:
            counts = np.array(ndimage.measurements.sum(np.ones(len(y)),
                                                    y, index=classes))
            self.priors_ = counts / float(n_samples)
        else:
            self.priors_ = self.priors

        cov = None
        if store_covariances:
            cov = []
        means = []
        scalings = []
        rotations = []
        for group_indices in classes_indices:
            Xg = X[group_indices, :]
            meang = Xg.mean(0)
            means.append(meang)
            Xgc = Xg - meang
            # Xgc = U * S * V.T
            U, S, Vt = np.linalg.svd(Xgc, full_matrices=False)
            rank = np.sum(S > tol)
            if rank < n_features:
                warnings.warn("Variables are collinear")
            S2 = (S ** 2) / (len(Xg) - 1)
            if store_covariances:
                # cov = V * (S^2 / (n-1)) * V.T
                cov.append(np.dot(S2 * Vt.T, Vt))
            scalings.append(S2)
            rotations.append(Vt.T)
        if store_covariances:
            self.covariances_ = cov
        self.means_ = np.asarray(means)
        self.scalings = np.asarray(scalings)
        self.rotations = rotations
        self.classes = classes
        return self

    def decision_function(self, X):
        """
        This function return the decision function values related to each
        class on an array of test vectors X.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]

        Returns
        -------
        C : array, shape = [n_samples, n_classes]
        """
        X = np.asanyarray(X)
        norm2 = []
        for i in range(len(self.classes)):
            R = self.rotations[i]
            S = self.scalings[i]
            Xm = X - self.means_[i]
            X2 = np.dot(Xm, R * (S ** (-0.5)))
            norm2.append(np.sum(X2 ** 2, 1))
        norm2 = np.array(norm2).T # shape : len(X), n_classes
        return -0.5 * (norm2 + np.sum(np.log(self.scalings), 1)) + \
               np.log(self.priors_)

    def predict(self, X):
        """
        This function does classification on an array of test vectors X.

        The predicted class C for each sample in X is returned.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]

        Returns
        -------
        C : array, shape = [n_samples]
        """
        d = self.decision_function(X)
        y_pred = self.classes[d.argmax(1)]
        return y_pred

    def predict_proba(self, X):
        """
        This function return posterior probabilities of classification
        according to each class on an array of test vectors X.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]

        Returns
        -------
        C : array, shape = [n_samples, n_classes]
        """
        values = self.decision_function(X)
        # compute the likelihood of the underlying gaussian models
        # up to a multiplicative constant.
        likelihood = np.exp(values - values.min(axis=1)[:, np.newaxis])
        # compute posterior probabilities
        return likelihood / likelihood.sum(axis=1)[:, np.newaxis]

from .base import BaseEstimator

class Pipeline(BaseEstimator):
    """
    Pipeline of transformers with a final predictor
    Sequentialy apply a list of transformers and a final predictor
    A transformer implements fit & transform methods
    A predictor implements fit & predict methods
    
    Example
    =======
    
    >>> from scikits.learn import svm, datasets
    >>> from scikits.learn.datasets import samples_generator
    >>> from scikits.learn.feature_selection import SelectKBest, f_regression
    >>> from scikits.learn.pipeline import Pipeline

    >>> # generate some data to play with
    >>> X, y = samples_generator.test_dataset_classif(k=5)

    >>> # ANOVA SVM-C
    >>> anova_filter = SelectKBest(f_regression, k=5)
    >>> clf = svm.SVC(kernel='linear')
    
    >>> anova_svm = Pipeline([anova_filter], clf)
    >>> _ = anova_svm.fit(X,y)
    
    >>> prediction = anova_svm.predict(X)
    """
    def __init__(self, transformers=[], estimator=None):
        """
        methods: list of UnivRanking objects,
        ie.: with fit/reduce/getSelectedFeatures methods
        """
        for t in  transformers:
            assert hasattr(t, "fit") and hasattr(t, "transform"), ValueError(
                "All transformers should implement fit and transform",
                "'%s' (type %s) )" % (t, type(t))
        )
        assert hasattr(estimator, "fit") and hasattr(estimator, "predict"), \
            ValueError("Predictor should implement fit and predict",
                "'%s' (type %s) )" % (t, type(t))
        )
        self.transformers = transformers
        self.estimator = estimator

    def fit(self, X, y=None):
        Xt = X
        for transformer in self.transformers:
            Xt = transformer.fit(Xt, y).transform(Xt)
        self.estimator.fit(Xt, y)
        return self
    
    def predict(self, X):
        Xt=X
        for transformer in self.transformers:
            Xt = transformer.transform(Xt)
        return self.estimator.predict(Xt)
        
    def score(self, X, y=None):
        Xt = X
        for transformer in self.transformers:
            Xt = transformer.fit(Xt, y).transform(Xt)
        return self.estimator.score(Xt, y)
 

from .externals.joblib import Parallel, delayed

try:
    from itertools import product
except:
    def product(*args, **kwds):
        pools = map(tuple, args) * kwds.get('repeat', 1)
        result = [[]]
        for pool in pools:
            result = [x+[y] for x in result for y in pool]
        for prod in result:
            yield tuple(prod)


def iter_grid(param_grid):
    """ Generators on the combination of the various parameter lists given.

        Parameters
        -----------
        kwargs: keyword arguments, lists
            Each keyword argument must be a list of values that should
            be explored.

        Returns
        --------
        params: dictionary
            Dictionnary with the input parameters taking the various
            values succesively.

        Examples
        ---------
        >>> param_grid = {'a':[1, 2], 'b':[True, False]}
        >>> list(iter_grid(param_grid))
        [{'a': 1, 'b': True}, {'a': 1, 'b': False}, {'a': 2, 'b': True}, {'a': 2, 'b': False}]
    """
    if hasattr(param_grid, 'has_key'):
        param_grid = [param_grid]
    for p in param_grid:
        keys = p.keys()
        for v in product(*p.values()):
            params = dict(zip(keys,v))
            yield params

def fit_grid_point(X, y, klass, orignal_params, clf_params, cv,
                                        loss_func, **fit_params):
    """Run fit on one set of parameters
    Returns the score and the instance of the classifier
    """
    params = orignal_params.copy()
    params.update(clf_params)
    n_samples, n_features = X.shape
    clf = klass(**params)
    score = 0
    for train, test in cv:
        clf.fit(X[train], y[train], **fit_params)
        if loss_func is not None:
            y_pred = clf.predict(X[test])
            score -= loss_func(y[test], y_pred)
        else:
            score += clf.score(X[test], y[test])

    return clf, score


class GridSearchCV(object):
    """
    Grid search on the parameters of a classifier.

    Important members are fit, predict.

    GridSearchCV implements a "fit" method and a "predict" method like
    any classifier except that the parameters of the classifier
    used to predict is optimized by cross-validation

    Parameters
    ----------
    estimator: object type that implements the "fit" and "predict" methods
        A object of that type is instanciated for each grid point

    param_grid: dict
        a dictionary of parameters that are used the generate the grid

    loss_func : function that takes 2 arguments and compares them in
        order to evaluate the performance of prediciton (small is good)

    fit_params : dict
        parameters to pass to the fit method

    n_jobs : int
        number of jobs to run in parallel (default 1)

    Methods
    -------
    fit(X, Y) : self
        Fit the model

    predict(X) : array
        Predict using the model.

    Examples
    --------
    >>> import numpy as np
    >>> from scikits.learn.cross_val import LeaveOneOut
    >>> from scikits.learn.svm import SVC
    >>> X = np.array([[-1, -1], [-2, -1], [1, 1], [2, 1]])
    >>> y = np.array([1, 1, 2, 2])
    >>> parameters = {'kernel':('linear', 'rbf'), 'C':[1, 10]}
    >>> svc = SVC()
    >>> clf = GridSearchCV(svc, parameters, n_jobs=1)
    >>> print clf.fit(X, y).predict([[-0.8, -1]])
    [ 1.]
    """

    def __init__(self, estimator, param_grid, loss_func=None,
                        fit_params={}, n_jobs=1):
        assert hasattr(estimator, 'fit') and hasattr(estimator, 'predict'), (
            "estimator should a be an estimator implementing 'fit' and "
            "'predict' methods, %s (type %s) was passed" % (clf, type(clf))
            )
        if loss_func is None:
            assert hasattr(estimator, 'score'), ValueError(
                    "If no loss_func is specified, the estimator passed "
                    "should have a 'score' method. The estimator %s "
                    "does not." % estimator
                    )

        self.estimator = estimator
        self.param_grid = param_grid
        self.loss_func = loss_func
        self.n_jobs = n_jobs
        self.fit_params = fit_params


    def fit(self, X, y, cv=None, **kw):
        """Run fit with all sets of parameters
        Returns the best classifier

        Parameters
        ----------

        X: array, [n_samples, n_features]
            Training vector, where n_samples in the number of samples and
            n_features is the number of features.

        y: array, [n_samples]
            Target vector relative to X

        cv : crossvalidation generator
            see scikits.learn.cross_val module

        """
        if cv is None:
            n_samples = y.size
            from scikits.learn.cross_val import KFold
            cv = KFold(n_samples, 2)

        grid = iter_grid(self.param_grid)
        klass = self.estimator.__class__
        orignal_params = self.estimator._get_params()
        out = Parallel(n_jobs=self.n_jobs)(
            delayed(fit_grid_point)(X, y, klass, orignal_params, clf_params,
                    cv, self.loss_func, **self.fit_params)
                    for clf_params in grid)

        # Out is a list of pairs: estimator, score
        key = lambda pair: pair[1]
        best_estimator = max(out, key=key)[0] # get maximum score

        self.best_estimator = best_estimator
        self.predict = best_estimator.predict

        return self


if __name__ == '__main__':
    from scikits.learn.svm import SVC
    from scikits.learn import datasets

    iris = datasets.load_iris()

    # Add the noisy data to the informative features
    X = iris.data
    y = iris.target

    svc = SVC(kernel='linear')
    clf = GridSearchCV(svc, {'C':[1, 10]}, n_jobs=1)
    print clf.fit(X, y).predict([[-0.8, -1]])

"""
Utilities for cross validation.
"""

# Author: Alexandre Gramfort <alexandre.gramfort@inria.fr>,
#         Gael Varoquaux    <gael.varoquaux@normalesup.org>
# License: BSD Style.

from math import ceil
import numpy as np

from .base import ClassifierMixin
from .utils.extmath import factorial, combinations
from .externals.joblib import Parallel, delayed

##############################################################################
class LeaveOneOut(object):
    """
    Leave-One-Out cross validation iterator:
    Provides train/test indexes to split data in train test sets
    """

    def __init__(self, n):
        """
        Leave-One-Out cross validation iterator:
        Provides train/test indexes to split data in train test sets

        Parameters
        ===========
        n: int
            Total number of elements

        Examples
        ========
        >>> from scikits.learn import cross_val
        >>> X = [[1, 2], [3, 4]]
        >>> y = [1, 2]
        >>> loo = cross_val.LeaveOneOut(2)
        >>> len(loo)
        2
        >>> print loo
        scikits.learn.cross_val.LeaveOneOut(n=2)
        >>> for train_index, test_index in loo:
        ...    print "TRAIN:", train_index, "TEST:", test_index
        ...    X_train, X_test, y_train, y_test = cross_val.split(train_index, test_index, X, y)
        ...    print X_train, X_test, y_train, y_test
        TRAIN: [False  True] TEST: [ True False]
        [[3 4]] [[1 2]] [2] [1]
        TRAIN: [ True False] TEST: [False  True]
        [[1 2]] [[3 4]] [1] [2]
        """
        self.n = n


    def __iter__(self):
        n = self.n
        for i in xrange(n):
            test_index  = np.zeros(n, dtype=np.bool)
            test_index[i] = True
            train_index = np.logical_not(test_index)
            yield train_index, test_index


    def __repr__(self):
        return '%s.%s(n=%i)' % (self.__class__.__module__,
                                self.__class__.__name__,
                                self.n,
                                )

    def __len__(self):
        return self.n


##############################################################################
class LeavePOut(object):
    """
    Leave-P-Out cross validation iterator:
    Provides train/test indexes to split data in train test sets

    """

    def __init__(self, n, p):
        """
        Leave-P-Out cross validation iterator:
        Provides train/test indexes to split data in train test sets

        Parameters
        ===========
        n: int
            Total number of elements
        p: int
            Size test sets

        Examples
        ========
        >>> from scikits.learn import cross_val
        >>> X = [[1, 2], [3, 4], [5, 6], [7, 8]]
        >>> y = [1, 2, 3, 4]
        >>> lpo = cross_val.LeavePOut(4, 2)
        >>> len(lpo)
        6
        >>> print lpo
        scikits.learn.cross_val.LeavePOut(n=4, p=2)
        >>> for train_index, test_index in lpo:
        ...    print "TRAIN:", train_index, "TEST:", test_index
        ...    X_train, X_test, y_train, y_test = cross_val.split(train_index, test_index, X, y)
        TRAIN: [False False  True  True] TEST: [ True  True False False]
        TRAIN: [False  True False  True] TEST: [ True False  True False]
        TRAIN: [False  True  True False] TEST: [ True False False  True]
        TRAIN: [ True False False  True] TEST: [False  True  True False]
        TRAIN: [ True False  True False] TEST: [False  True False  True]
        TRAIN: [ True  True False False] TEST: [False False  True  True]
        """
        self.n = n
        self.p = p


    def __iter__(self):
        n = self.n
        p = self.p
        comb = combinations(range(n), p)
        for idx in comb:
            test_index = np.zeros(n, dtype=np.bool)
            test_index[np.array(idx)] = True
            train_index = np.logical_not(test_index)
            yield train_index, test_index


    def __repr__(self):
        return '%s.%s(n=%i, p=%i)' % (
                                self.__class__.__module__,
                                self.__class__.__name__,
                                self.n,
                                self.p,
                                )

    def __len__(self):
        return factorial(self.n) / factorial(self.n - self.p) \
               / factorial(self.p)


##############################################################################
class KFold(object):
    """
    K-Folds cross validation iterator:
    Provides train/test indexes to split data in train test sets
    """

    def __init__(self, n, k):
        """
        K-Folds cross validation iterator:
        Provides train/test indexes to split data in train test sets

        Parameters
        ===========
        n: int
            Total number of elements
        k: int
            number of folds

        Examples
        ========
        >>> from scikits.learn import cross_val
        >>> X = [[1, 2], [3, 4], [1, 2], [3, 4]]
        >>> y = [1, 2, 3, 4]
        >>> kf = cross_val.KFold(4, k=2)
        >>> len(kf)
        2
        >>> print kf
        scikits.learn.cross_val.KFold(n=4, k=2)
        >>> for train_index, test_index in kf:
        ...    print "TRAIN:", train_index, "TEST:", test_index
        ...    X_train, X_test, y_train, y_test = cross_val.split(train_index, test_index, X, y)
        TRAIN: [False False  True  True] TEST: [ True  True False False]
        TRAIN: [ True  True False False] TEST: [False False  True  True]

        Note
        ====
        All the folds have size trunc(n/k), the last one has the complementary
        """
        assert k>0, ValueError('cannot have k below 1')
        assert k<n, ValueError('cannot have k=%d greater than %d'% (k, n))
        self.n = n
        self.k = k


    def __iter__(self):
        n = self.n
        k = self.k
        j = ceil(n / k)

        for i in xrange(k):
            test_index  = np.zeros(n, dtype=np.bool)
            if i<k-1:
                test_index[i*j:(i+1)*j] = True
            else:
                test_index[i*j:] = True
            train_index = np.logical_not(test_index)
            yield train_index, test_index


    def __repr__(self):
        return '%s.%s(n=%i, k=%i)' % (
                                self.__class__.__module__,
                                self.__class__.__name__,
                                self.n,
                                self.k,
                                )

    def __len__(self):
        return self.k


##############################################################################
class StratifiedKFold(object):
    """
    Stratified K-Folds cross validation iterator:
    Provides train/test indexes to split data in train test sets
    
    This cross-validation object is a variation of KFold, which
    returns stratified folds. The folds are made by preserving
    the percentage of samples for each class.
    
    """

    # XXX: Should maybe have an argument to raise when 
    # folds are not balanced
    def __init__(self, y, k):
        """
        K-Folds cross validation iterator:
        Provides train/test indexes to split data in train test sets

        Parameters
        ===========
        y: array, [n_samples]
            Samples to split in K folds
        k: int
            number of folds

        Examples
        ========
        >>> from scikits.learn import cross_val
        >>> X = [[1, 2], [3, 4], [1, 2], [3, 4]]
        >>> y = [0, 0, 1, 1]
        >>> skf = cross_val.StratifiedKFold(y, k=2)
        >>> len(skf)
        2
        >>> print skf
        scikits.learn.cross_val.StratifiedKFold(labels=[0 0 1 1], k=2)
        >>> for train_index, test_index in skf:
        ...    print "TRAIN:", train_index, "TEST:", test_index
        ...    X_train, X_test, y_train, y_test = cross_val.split(train_index, test_index, X, y)
        TRAIN: [False  True False  True] TEST: [ True False  True False]
        TRAIN: [ True False  True False] TEST: [False  True False  True]

        Note
        ====
        All the folds have size trunc(n/k), the last one has the complementary
        """
        y = np.asanyarray(y)
        n = y.size
        assert k>0, ValueError('cannot have k below 1')
        assert k<n, ValueError('cannot have k=%d greater than %d'% (k, n))
        self.y = y
        self.k = k


    def __iter__(self):
        y = self.y.copy()
        k = self.k
        n = y.size

        classes = np.unique(y)

        idx_c = dict()
        j_c = dict()
        n_c = dict()
        for c in classes:
            idx_c[c] = np.where(y == c)[0]
            n_c[c] = len(idx_c[c])
            j_c[c] = int(ceil(n_c[c] / k))

        for i in xrange(k):
            test_index  = np.zeros(n, dtype=np.bool)
            for c in classes:
                if i<k-1:
                    test_index_c = range(i*j_c[c], (i+1)*j_c[c])
                else:
                    test_index_c = range(i*j_c[c], n_c[c])
                test_index[idx_c[c][test_index_c]] = True

            train_index = np.logical_not(test_index)
            yield train_index, test_index


    def __repr__(self):
        return '%s.%s(labels=%s, k=%i)' % (
                                self.__class__.__module__,
                                self.__class__.__name__,
                                self.y,
                                self.k,
                                )

    def __len__(self):
        return self.k


##############################################################################
class LeaveOneLabelOut(object):
    """
    Leave-One-Label_Out cross-validation iterator:
    Provides train/test indexes to split data in train test sets
    """

    def __init__(self, labels):
        """
        Leave-One-Label_Out cross validation:
        Provides train/test indexes to split data in train test sets

        Parameters
        ----------
        labels : list
                List of labels

        Examples
        ----------
        >>> from scikits.learn import cross_val
        >>> X = [[1, 2], [3, 4], [5, 6], [7, 8]]
        >>> y = [1, 2, 1, 2]
        >>> labels = [1, 1, 2, 2]
        >>> lol = cross_val.LeaveOneLabelOut(labels)
        >>> len(lol)
        2
        >>> print lol
        scikits.learn.cross_val.LeaveOneLabelOut(labels=[1, 1, 2, 2])
        >>> for train_index, test_index in lol:
        ...    print "TRAIN:", train_index, "TEST:", test_index
        ...    X_train, X_test, y_train, y_test = cross_val.split(train_index, \
            test_index, X, y)
        ...    print X_train, X_test, y_train, y_test
        TRAIN: [False False  True  True] TEST: [ True  True False False]
        [[5 6]
         [7 8]] [[1 2]
         [3 4]] [1 2] [1 2]
        TRAIN: [ True  True False False] TEST: [False False  True  True]
        [[1 2]
         [3 4]] [[5 6]
         [7 8]] [1 2] [1 2]

        """
        self.labels = labels
        self.n_labels = np.unique(labels).size


    def __iter__(self):
        # We make a copy here to avoid side-effects during iteration
        labels = np.array(self.labels, copy=True)
        for i in np.unique(labels):
            test_index  = np.zeros(len(labels), dtype=np.bool)
            test_index[labels==i] = True
            train_index = np.logical_not(test_index)
            yield train_index, test_index


    def __repr__(self):
        return '%s.%s(labels=%s)' % (
                                self.__class__.__module__,
                                self.__class__.__name__,
                                self.labels,
                                )

    def __len__(self):
        return self.n_labels


##############################################################################
class LeavePLabelOut(object):
    """
    Leave-P-Label_Out cross-validation iterator:
    Provides train/test indexes to split data in train test sets
    """

    def __init__(self, labels, p):
        """
        Leave-P-Label_Out cross validation:
        Provides train/test indexes to split data in train test sets

        Parameters
        ----------
        labels : list
                List of labels

        Examples
        ----------
        >>> from scikits.learn import cross_val
        >>> X = [[1, 2], [3, 4], [5, 6]]
        >>> y = [1, 2, 1]
        >>> labels = [1, 2, 3]
        >>> lpl = cross_val.LeavePLabelOut(labels, p=2)
        >>> len(lpl)
        3
        >>> print lpl
        scikits.learn.cross_val.LeavePLabelOut(labels=[1, 2, 3], p=2)
        >>> for train_index, test_index in lpl:
        ...    print "TRAIN:", train_index, "TEST:", test_index
        ...    X_train, X_test, y_train, y_test = cross_val.split(train_index, \
            test_index, X, y)
        ...    print X_train, X_test, y_train, y_test
        TRAIN: [False False  True] TEST: [ True  True False]
        [[5 6]] [[1 2]
         [3 4]] [1] [1 2]
        TRAIN: [False  True False] TEST: [ True False  True]
        [[3 4]] [[1 2]
         [5 6]] [2] [1 1]
        TRAIN: [ True False False] TEST: [False  True  True]
        [[1 2]] [[3 4]
         [5 6]] [1] [2 1]

        """
        self.labels = labels
        self.unique_labels = np.unique(self.labels)
        self.n_labels = self.unique_labels.size
        self.p = p

    def __iter__(self):
        # We make a copy here to avoid side-effects during iteration
        labels = np.array(self.labels, copy=True)
        unique_labels = np.unique(labels)
        n_labels = unique_labels.size
        comb = combinations(range(n_labels), self.p)

        for idx in comb:
            test_index = np.zeros(labels.size, dtype=np.bool)
            idx = np.array(idx)
            for l in unique_labels[idx]:
                test_index[labels == l] = True
            train_index = np.logical_not(test_index)
            yield train_index, test_index

    def __repr__(self):
        return '%s.%s(labels=%s, p=%s)' % (
                                self.__class__.__module__,
                                self.__class__.__name__,
                                self.labels,
                                self.p,
                                )

    def __len__(self):
        return factorial(self.n_labels) / factorial(self.n_labels - self.p) \
               / factorial(self.p)

    
##############################################################################

def _cross_val_score(estimator, X, y, score_func, train, test):
    """ Inner loop for cross validation.
    """
    if score_func is None:
        score_func = lambda self, *args: estimator.score(*args)
    if y is None:
        return score_func(estimator.fit(X[train]), X[test])
    return score_func(estimator.fit(X[train], y[train]), X[test], y[test])


def cross_val_score(estimator, X, y=None, score_func=None, cv=None, 
                n_jobs=1, verbose=0):
    """ Evaluate a score by cross-validation.

        Parameters
        ===========
        estimator: estimator object implementing 'fit'
            The object to use to fit the data
        X: array-like of shape at least 2D
            The data to fit.
        y: array-like, optional
            The target variable to try to predict in the case of
            supervised learning.
        score_func: callable, optional
            callable taking as arguments the fitted estimator, the
            test data (X_test) and the test target (y_test) if y is
            not None.
        cv: cross-validation generator, optional
            A cross-validation generator. If None, a 3-fold cross
            validation is used or 3-fold stratified cross-validation
            when y is supplied.
        n_jobs: integer, optional
            The number of CPUs to use to do the computation. -1 means
            'all CPUs'.
        verbose: integer, optional
            The verbosity level
    """
    # XXX: should have a n_jobs to be able to do this in parallel.
    n_samples = len(X)
    if cv is None:
        if y is not None and isinstance(estimator, ClassifierMixin):
            cv = StratifiedKFold(y, k=3)
        else:
            cv = KFold(n_samples, k=3)
    if score_func is None:
        assert hasattr(estimator, 'score'), ValueError(
                "If no score_func is specified, the estimator passed "
                "should have a 'score' method. The estimator %s "
                "does not." % estimator
                )
    scores = Parallel(n_jobs=n_jobs, verbose=verbose)(
                delayed(_cross_val_score)(estimator, X, y, score_func, 
                                                        train, test)
                for train, test in cv)
    return np.array(scores)


################################################################################
# Depreciated
def split(train_indices, test_indices, *args):
    """
    For each arg return a train and test subsets defined by indexes provided
    in train_indices and test_indices
    """
    import warnings
    warnings.warn('split is deprecated and will be removed, '
                    'please use indexing instead')
    ret = []
    for arg in args:
        arg = np.asanyarray(arg)
        arg_train = arg[train_indices]
        arg_test  = arg[test_indices]
        ret.append(arg_train)
        ret.append(arg_test)
    return ret

import numpy as np

from . import _libsvm
from . import _liblinear
from .base import BaseEstimator, RegressorMixin, ClassifierMixin

#
# TODO: some cleanup: is nSV_ really needed ?

class _BaseLibSVM(BaseEstimator):
    """
    Base class for classifiers that use libsvm as library for
    support vector machine classification and regression.

    Should not be used directly, use derived classes instead
    """

    _kernel_types = ['linear', 'poly', 'rbf', 'sigmoid', 'precomputed']
    _svm_types = ['c_svc', 'nu_svc', 'one_class', 'epsilon_svr', 'nu_svr']

    def __init__(self, impl, kernel, degree, gamma, coef0, cache_size,
                 eps, C, nu, p, shrinking, probability):
        assert impl in self._svm_types, \
            "impl should be one of %s, %s was given" % (
                self._svm_types, impl)
        assert kernel in self._kernel_types or callable(kernel), \
            "kernel should be one of %s or a callable, %s was given." % (
                self._kernel_types, kernel)
        self.kernel = kernel
        self.impl = impl
        self.degree = degree
        self.gamma = gamma
        self.coef0 = coef0
        self.cache_size = cache_size
        self.eps = eps
        self.C = C
        self.nu = nu
        self.p = p
        self.shrinking = shrinking
        self.probability = probability

    def _get_kernel(self, X):
        """ Get the kernel type code as well as the data transformed by
            the kernel (if the kernel is a callable.
        """
        if callable(self.kernel):
            # in the case of precomputed kernel given as a function, we
            # have to compute explicitly the kernel matrix
            _X = np.asanyarray(self.kernel(X, self.__Xfit), 
                               dtype=np.float64, order='C')
            kernel_type = 4
        else: 
            kernel_type = self._kernel_types.index(self.kernel)
            _X = X
        return kernel_type, _X


    def fit(self, X, Y, class_weight={}):
        """
        Fit the SVM model according to the given training data and parameters.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]
            Training vector, where n_samples in the number of samples and
            n_features is the number of features.
        Y : array, shape = [n_samples]
            Target values (integers in classification, real numbers in
            regression)
        weight : dict , {class_label : weight}
            Weights associated with classes. If not given, all classes
            are supposed to have weight one.
        """
        X = np.asanyarray(X, dtype=np.float64, order='C')
        Y = np.asanyarray(Y, dtype=np.float64, order='C')

        # container for when we call fit
        self.support_   = np.empty((0,0), dtype=np.float64, order='C')
        self.dual_coef_ = np.empty((0,0), dtype=np.float64, order='C')
        self.intercept_ = np.empty(0,     dtype=np.float64, order='C')

        # only used in classification
        self.nSV_ = np.empty(0, dtype=np.int32, order='C')


        if callable(self.kernel):
             # you must store a reference to X to compute the kernel in predict
             # there's a way around this, but it involves patching libsvm
            # TODO: put keyword copy to copy on demand
            self.__Xfit = X
        kernel_type, _X = self._get_kernel(X)

        self.weight = np.asarray(class_weight.values(), 
                                 dtype=np.float64, order='C')
        self.weight_label = np.asarray(class_weight.keys(), 
                                       dtype=np.int32, order='C')

        # check dimensions
        if _X.shape[0] != Y.shape[0]: 
            raise ValueError("Incompatible shapes")
        solver_type = self._svm_types.index(self.impl)

        if (self.gamma == 0): 
            self.gamma = 1.0/_X.shape[0]

        self.label_, self.probA_, self.probB_ = _libsvm.train_wrap(_X, Y,
                 solver_type, kernel_type, self.degree,
                 self.gamma, self.coef0, self.eps, self.C,
                 self.support_, self.dual_coef_,
                 self.intercept_, self.weight_label, self.weight,
                 self.nSV_, self.nu, self.cache_size, self.p,
                 int(self.shrinking),
                 int(self.probability))
        return self


    def predict(self, T):
        """
        This function does classification or regression on an array of
        test vectors T.

        For a classification model, the predicted class for each
        sample in T is returned.  For a regression model, the function
        value of T calculated is returned.

        For an one-class model, +1 or -1 is returned.

        Parameters
        ----------
        T : array-like, shape = [n_samples, n_features]


        Returns
        -------
        C : array, shape = [nsample]
        """
        T = np.atleast_2d(np.asanyarray(T, dtype=np.float64, order='C'))

        kernel_type, T = self._get_kernel(T)
        return _libsvm.predict_from_model_wrap(T, self.support_,
                      self.dual_coef_, self.intercept_,
                      self._svm_types.index(self.impl),
                      kernel_type, self.degree,
                      self.gamma, self.coef0, self.eps, self.C,
                      self.weight_label, self.weight,
                      self.nu, self.cache_size, self.p,
                      int(self.shrinking), int(self.probability),
                      self.nSV_, self.label_, self.probA_,
                      self.probB_)


    def predict_proba(self, T):
        """
        This function does classification or regression on a test vector T
        given a model with probability information.

        Parameters
        ----------
        T : array-like, shape = [n_samples, n_features]

        Returns
        -------
        T : array-like, shape = [n_samples, n_classes]
            Returns the probability of the sample for each class in
            the model, where classes are ordered by arithmetical
            order.

        Notes
        -----
        The probability model is created using cross validation, so
        the results can be slightly different than those obtained by
        predict. Also, it will meaningless results on very small
        datasets.
        """
        if not self.probability:
            raise ValueError(
                    "probability estimates must be enabled to use this method")
        T = np.atleast_2d(np.asanyarray(T, dtype=np.float64, order='C'))
        kernel_type, T = self._get_kernel(T)
        pprob = _libsvm.predict_prob_from_model_wrap(T, self.support_,
                      self.dual_coef_, self.intercept_, 
                      self._svm_types.index(self.impl),
                      kernel_type, self.degree, self.gamma,
                      self.coef0, self.eps, self.C, 
                      self.weight_label, self.weight,
                      self.nu, self.cache_size,
                      self.p, int(self.shrinking), int(self.probability),
                      self.nSV_, self.label_,
                      self.probA_, self.probB_)
        return pprob[:, np.argsort(self.label_)]
        

    def predict_margin(self, T):
        """
        Calculate the distance of the samples in T to the separating hyperplane.

        Parameters
        ----------
        T : array-like, shape = [n_samples, n_features]
        """
        T = np.atleast_2d(np.asanyarray(T, dtype=np.float64, order='C'))
        kernel_type, T = self._get_kernel(T)
        return _libsvm.predict_margin_from_model_wrap(T, self.support_,
                      self.dual_coef_, self.intercept_, 
                      self._svm_types.index(self.impl),
                      kernel_type, self.degree, self.gamma,
                      self.coef0, self.eps, self.C, 
                      self.weight_label, self.weight,
                      self.nu, self.cache_size,
                      self.p, int(self.shrinking), int(self.probability),
                      self.nSV_, self.label_,
                      self.probA_, self.probB_)


    @property
    def coef_(self):
        if self.kernel != 'linear':
            raise NotImplementedError('coef_ is only available when using a linear kernel')
        return np.dot(self.dual_coef_, self.support_)



class BaseLibLinear(BaseEstimator):
    """
    Base for classes binding liblinear (dense and sparse versions)
    """

    _weight_label = np.empty(0, dtype=np.int32)
    _weight = np.empty(0, dtype=np.float64)

    _solver_type_dict = {
        'PL2_LLR_D0' : 0, # L2 penalty logistic regression
        'PL2_LL2_D1' : 1, # L2 penalty, L2 loss, dual problem
        'PL2_LL2_D0' : 2, # L2 penalty, L2 loss, primal problem
        'PL2_LL1_D1' : 3, # L2 penalty, L1 Loss, dual problem
        'PL1_LL2_D0' : 5, # L1 penalty, L2 Loss, primal problem
        'PL1_LLR_D0' : 6, # L1 penalty logistic regression
        }

    def __init__(self, penalty='l2', loss='l2', dual=True, eps=1e-4, C=1.0,
                 has_intercept=True):
        self.penalty = penalty
        self.loss = loss
        self.dual = dual
        self.eps = eps
        self.C = C
        self.has_intercept = has_intercept
        # Check that the arguments given are valid:
        self._get_solver_type()

    def _get_solver_type(self):
        """ Return the magic number for the solver described by the
            settings.
        """
        solver_type = "P%s_L%s_D%d"  % (
            self.penalty.upper(), self.loss.upper(), int(self.dual))
        if not solver_type in self._solver_type_dict:
            raise ValueError('Not supported set of arguments: '
                             + solver_type)
        return self._solver_type_dict[solver_type]

    def fit(self, X, Y, **params):
        """
        Parameters
        ----------
        X : array-like, shape = [nsamples, nfeatures]
            Training vector, where nsamples in the number of samples and
            nfeatures is the number of features.
        Y : array, shape = [nsamples]
            Target vector relative to X
        """
        self._set_params(**params)

        X = np.asanyarray(X, dtype=np.float64, order='C')
        Y = np.asanyarray(Y, dtype=np.int32, order='C')
        self.raw_coef_, self.label_ = \
                       _liblinear.train_wrap(X, Y,
                       self._get_solver_type(),
                       self.eps, self._get_bias(), self.C, self._weight_label,
                       self._weight)
        return self

    def predict(self, T):
        """
        This function does classification or regression on an array of
        test vectors T.

        For a classification model, the predicted class for each
        sample in T is returned.  For a regression model, the function
        value of T calculated is returned.

        For an one-class model, +1 or -1 is returned.

        Parameters
        ----------
        T : array-like, shape = [n_samples, n_features]


        Returns
        -------
        C : array, shape = [nsample]
        """
        T = np.asanyarray(T, dtype=np.float64, order='C')
        return _liblinear.predict_wrap(T, self.raw_coef_,
                                      self._get_solver_type(),
                                      self.eps, self.C,
                                      self._weight_label,
                                      self._weight, self.label_,
                                      self._get_bias())

    @property
    def intercept_(self):
        if self.has_intercept > 0:
            return self.raw_coef_[:,-1]
        return 0.0

    @property
    def coef_(self):
        if self.has_intercept > 0:
            return self.raw_coef_[:,:-1]
        return self.raw_coef_

    def predict_proba(self, T):
        # how can this be, logisitic *does* implement this
        raise NotImplementedError(
                'liblinear does not provide this functionality')


    def _get_bias(self):
        """
        Due to some pecularities in libliner, parameter bias must be a
        double indicating if the intercept should be computed:
        positive for true, negative for false
        """
        return int  (self.has_intercept) - .5

################################################################################
# Public API
# No processing should go into these classes

class SVC(_BaseLibSVM, ClassifierMixin):
    """
    C-Support Vector Classification.

    Parameters
    ----------

    C : float, optional (default=1.0)
        penalty parameter C of the error term.
    
    kernel : string, optional
         Specifies the kernel type to be used in the algorithm.
         one of 'linear', 'poly', 'rbf', 'sigmoid', 'precomputed'.
         If none is given 'rbf' will be used.

    degree : int, optional
        degree of kernel function
        is significant only in poly, rbf, sigmoid

    gamma : float, optional (default=0.0)
        kernel coefficient for rbf

    coef0 : float, optional
        independent term in kernel function. It is only significant
        in poly/sigmoid.

    probability: boolean, optional (False by default)
        enable probability estimates. This must be enabled prior
        to calling prob_predict.

    shrinking: boolean, optional
         wether to use the shrinking heuristic.

    eps: float, optional
         precision for stopping criteria

    cache_size: float, optional
         specify the size of the cache (in MB)

    Attributes
    ----------
    `support_` : array-like, shape = [nSV, n_features]
        Support vectors.

    `dual_coef_` : array, shape = [n_class-1, nSV]
        Coefficients of the support vector in the decision function.

    `coef_` : array, shape = [n_class-1, n_features]
        Weights asigned to the features (coefficients in the primal
        problem). This is only available in the case of linear kernel.

    `intercept_` : array, shape = [n_class * (n_class-1) / 2]
        Constants in decision function.


    Examples
    --------
    >>> X = np.array([[-1, -1], [-2, -1], [1, 1], [2, 1]])
    >>> Y = np.array([1, 1, 2, 2])
    >>> clf = SVC()
    >>> clf.fit(X, Y)
    SVC(kernel='rbf', C=1.0, probability=False, degree=3, coef0=0.0, eps=0.001,
      cache_size=100.0,
      shrinking=True,
      gamma=0.25)
    >>> print clf.predict([[-0.8, -1]])
    [ 1.]

    See also
    --------
    SVR, LinearSVC
    """

    def __init__(self, C=1.0, kernel='rbf', degree=3, gamma=0.0,
                 coef0=0.0, shrinking=True, probability=False,
                 eps=1e-3, cache_size=100.0):

        _BaseLibSVM.__init__(self, 'c_svc', kernel, degree, gamma, coef0,
                         cache_size, eps, C, 0., 0.,
                         shrinking, probability)


class NuSVC(_BaseLibSVM, ClassifierMixin):
    """
    Nu-Support Vector Classification.

    Parameters
    ----------

    nu : float, optional
        An upper bound on the fraction of training errors and a lower
        bound of the fraction of support vectors. Should be in the
        interval (0, 1].  By default 0.5 will be taken.  Only
        available if impl='nu_svc'

    kernel : string, optional
         Specifies the kernel type to be used in the algorithm.
         one of 'linear', 'poly', 'rbf', 'sigmoid', 'precomputed'.
         If none is given 'rbf' will be used.

    degree : int, optional
        degree of kernel function
        is significant only in poly, rbf, sigmoid

    gamma : float, optional (default=0.0)
        kernel coefficient for rbf

    probability: boolean, optional (False by default)
        enable probability estimates. This must be enabled prior
        to calling prob_predict.

    coef0 : float, optional
        independent term in kernel function. It is only significant
        in poly/sigmoid.

    shrinking: boolean, optional
         wether to use the shrinking heuristic.

    eps: float, optional
         precision for stopping criteria

    cache_size: float, optional
         specify the size of the cache (in MB)


    Attributes
    ----------
    `support_` : array-like, shape = [nSV, n_features]
        Support vectors.

    `dual_coef_` : array, shape = [n_classes-1, nSV]
        Coefficients of the support vector in the decision function.

    `coef_` : array, shape = [n_classes-1, n_features]
        Weights asigned to the features (coefficients in the primal
        problem). This is only available in the case of linear kernel.

    `intercept_` : array, shape = [n_class * (n_class-1) / 2]
        Constants in decision function.


    Methods
    -------
    fit(X, Y) : self
        Fit the model

    predict(X) : array
        Predict using the model.

    predict_proba(X) : array
        Return probability estimates.

    predict_margin(X) : array
        Return distance to predicted margin.

    Examples
    --------
    >>> X = np.array([[-1, -1], [-2, -1], [1, 1], [2, 1]])
    >>> Y = np.array([1, 1, 2, 2])
    >>> clf = NuSVC()
    >>> clf.fit(X, Y)
    NuSVC(kernel='rbf', probability=False, degree=3, coef0=0.0, eps=0.001,
       cache_size=100.0,
       shrinking=True,
       nu=0.5,
       gamma=0.25)
    >>> print clf.predict([[-0.8, -1]])
    [ 1.]

    See also
    --------
    SVC, LinearSVC, SVR
    """

    def __init__(self, nu=0.5, kernel='rbf', degree=3, gamma=0.0,
                 coef0=0.0, shrinking=True, probability=False,
                 eps=1e-3, cache_size=100.0):

        _BaseLibSVM.__init__(self, 'nu_svc', kernel, degree, gamma, coef0,
                         cache_size, eps, 0., nu, 0.,
                         shrinking, probability)


class SVR(_BaseLibSVM, RegressorMixin):
    """
    Support Vector Regression.

    Parameters
    ----------

    nu : float, optional
        An upper bound on the fraction of training errors and a lower bound of
        the fraction of support vectors. Should be in the interval (0, 1].  By
        default 0.5 will be taken.  Only available if impl='nu_svc'

    kernel : string, optional
         Specifies the kernel type to be used in the algorithm.
         one of 'linear', 'poly', 'rbf', 'sigmoid', 'precomputed'.
         If none is given 'rbf' will be used.

    p : float
        epsilon in the epsilon-SVR model.

    degree : int, optional
        degree of kernel function
        is significant only in poly, rbf, sigmoid

    gamma : float, optional (default=0.0)
        kernel coefficient for rbf

    C : float, optional (default=1.0)
        penalty parameter C of the error term.
    
    probability: boolean, optional (False by default)
        enable probability estimates. This must be enabled prior
        to calling prob_predict.

    coef0 : float, optional
        independent term in kernel function. It is only significant
        in poly/sigmoid.

    Attributes
    ----------
    `support_` : array-like, shape = [nSV, n_features]
        Support vectors

    `dual_coef_` : array, shape = [n_classes-1, nSV]
        Coefficients of the support vector in the decision function.

    `coef_` : array, shape = [n_classes-1, n_features]
        Weights asigned to the features (coefficients in the primal
        problem). This is only available in the case of linear kernel.

    `intercept_` : array, shape = [n_class * (n_class-1) / 2]
        Constants in decision function.

    See also
    --------
    NuSVR
    """
    def __init__(self, kernel='rbf', degree=3, gamma=0.0, coef0=0.0,
                 cache_size=100.0, eps=1e-3, C=1.0, nu=0.5, p=0.1,
                 shrinking=True, probability=False):

        _BaseLibSVM.__init__(self, 'epsilon_svr', kernel, degree, gamma, coef0,
                         cache_size, eps, C, nu, p,
                         shrinking, probability)


class NuSVR(_BaseLibSVM, RegressorMixin):
    """
    Nu Support Vector Regression. Similar to NuSVC, for regression,
    uses a paramter nu to control the number of support
    vectors. However, unlike NuSVC, where nu replaces with C, here nu
    replaces with the parameter p of SVR.

    Parameters
    ----------

    nu : float, optional
        An upper bound on the fraction of training errors and a lower bound of
        the fraction of support vectors. Should be in the interval (0, 1].  By
        default 0.5 will be taken.  Only available if impl='nu_svc'


    C : float, optional (default=1.0)
        penalty parameter C of the error term.
    
    kernel : string, optional
         Specifies the kernel type to be used in the algorithm.
         one of 'linear', 'poly', 'rbf', 'sigmoid', 'precomputed'.
         If none is given 'rbf' will be used.

    degree : int, optional
        degree of kernel function
        is significant only in poly, rbf, sigmoid

    gamma : float, optional (default=0.0)
        kernel coefficient for rbf

    probability: boolean, optional (False by default)
        enable probability estimates. This must be enabled prior
        to calling prob_predict.

    coef0 : float, optional
        independent term in kernel function. It is only significant
        in poly/sigmoid.

    Attributes
    ----------
    `support_` : array-like, shape = [nSV, n_features]
        Support vectors

    `dual_coef_` : array, shape = [n_classes-1, nSV]
        Coefficients of the support vector in the decision function.

    `coef_` : array, shape = [n_classes-1, n_features]
        Weights asigned to the features (coefficients in the primal
        problem). This is only available in the case of linear kernel.

    `intercept_` : array, shape = [n_class * (n_class-1) / 2]
        Constants in decision function.

    See also
    --------
    NuSVR
    """

    def __init__(self, nu=0.5, C=1.0, kernel='rbf', degree=3,
                 gamma=0.0, coef0=0.0, shrinking=True,
                 probability=False, cache_size=100.0, eps=1e-3):

        _BaseLibSVM.__init__(self, 'epsilon_svr', kernel, degree, gamma, coef0,
                         cache_size, eps, C, nu, 0.,
                         shrinking, probability)



class OneClassSVM(_BaseLibSVM):
    """
    Outlayer detection

    Parameters
    ----------

    kernel : string, optional Specifies the kernel type to be used in
         the algorithm. one of 'linear', 'poly', 'rbf', 'sigmoid',
         'precomputed'. If none is given 'rbf' will be used.

    nu : float, optional An upper bound on the fraction of training
        errors and a lower bound of the fraction of support
        vectors. Should be in the interval (0, 1].  By default 0.5
        will be taken. 

    degree : int, optional
        degree of kernel function. Significant only in poly, rbf, sigmoid

    gamma : float, optional (default=0.0)
        kernel coefficient for rbf.

    C : float, optional (default=1.0)
        penalty parameter C of the error term.
    
    probability: boolean, optional (False by default)
        enable probability estimates. Must be enabled prior to calling
        prob_predict.

    coef0 : float, optional
        independent term in kernel function. It is only significant in
        poly/sigmoid.

    Attributes
    ----------
    `support_` : array-like, shape = [nSV, n_features]
        Support vectors


    `dual_coef_` : array, shape = [n_classes-1, nSV]
        Coefficient of the support vector in the decision function.

    `coef_` : array, shape = [n_classes-1, n_features]
        Weights asigned to the features (coefficients in the primal
        problem). This is only available in the case of linear kernel.
    
    `intercept_` : array, shape = [n_classes-1]
        constants in decision function

    """
    def __init__(self, kernel='rbf', degree=3, gamma=0.0, coef0=0.0,
                 cache_size=100.0, eps=1e-3, C=1.0, 
                 nu=0.5, p=0.1, shrinking=True, probability=False):
        _BaseLibSVM.__init__(self, 'one_class', kernel, degree, gamma, coef0,
                         cache_size, eps, C, nu, p,
                         shrinking, probability)
    
    def fit(self, X, Y=None):
        if Y is None:
            n_samples = X.shape[0]
            Y = [0] * n_samples
        super(OneClassSVM, self).fit(X, Y)


class LinearSVC(BaseLibLinear, ClassifierMixin):
    """
    Linear Support Vector Classification.

    Similar to SVC with parameter kernel='linear', but uses internally
    liblinear rather than libsvm, so it has more flexibility in the
    choice of penalties and loss functions and should be faster for
    huge datasets.

    Parameters
    ----------
    loss : string, 'l1' or 'l2' (default 'l2')
        Specifies the loss function. With 'l1' it is the standard SVM
        loss (a.k.a. hinge Loss) while with 'l2' it is the squared loss.
        (a.k.a. squared hinge Loss)

    penalty : string, 'l1' or 'l2' (default 'l2')
        Specifies the norm used in the penalization. The 'l2'
        penalty is the standard used in SVC. The 'l1' leads to coef_
        vectors that are sparse.

    dual : bool, (default True)
        Select the algorithm to either solve the dual or primal
        optimization problem.


    Attributes
    ----------
    `support_` : array-like, shape = [nSV, n_features]
        Support vectors.

    `dual_coef_` : array, shape = [n_class-1, nSV]
        Coefficients of the support vector in the decision function.

    `coef_` : array, shape = [n_class-1, n_features]
        Weights asigned to the features (coefficients in the primal
        problem). This is only available in the case of linear kernel.

    `intercept_` : array, shape = [n_class-1]
        Constants in decision function.

    Notes
    -----
    Some features of liblinear are still not wrapped, like the Cramer
    & Singer algorithm.

    """

    pass

"""
Base class for all estimators.

"""
# Author: Gael Varoquaux <gael.varoquaux@normalesup.org>

# License: BSD Style
import inspect

import numpy as np

from .metrics import explained_variance

################################################################################
class BaseEstimator(object):
    """ Base class for all estimators in the scikit learn

        Note
        =====

        All estimators should specify all the parameters that can be set
        at the class level in their __init__ as explicit keyword
        arguments (no *args, **kwargs).

    """

    @classmethod
    def _get_param_names(cls):
        try:
            args, varargs, kw, default = inspect.getargspec(cls.__init__)
            assert varargs is None, (
                'scikit learn estimators should always specify their '
                'parameters in the signature of their init (no varargs).'
                )
            # Remove 'self'
            # XXX: This is going to fail if the init is a staticmethod, but
            # who would do this?
            args.pop(0)
        except TypeError:
            # No explicit __init__
            args = []
        return args


    def _get_params(self):
        out = dict()
        for key in self._get_param_names():
            out[key] = getattr(self, key)
        return out


    def _set_params(self, **params):
        """ Set the parameters of the estimator.
        """
        valid_params = self._get_param_names()
        for key, value in params.iteritems():
            assert key in valid_params, ('Invalid parameter %s '
                'for estimator %s' %
                (key, self.__class__.__name__))
            setattr(self, key, value)


    def __repr__(self):
        options = np.get_printoptions()
        np.set_printoptions(precision=5, threshold=64, edgeitems=2)
        class_name = self.__class__.__name__

        # Do a multi-line justified repr:
        params_list = list()
        this_line_length = len(class_name)
        line_sep = ',\n' + (1+len(class_name)/2)*' '
        for i, (k, v) in enumerate(self._get_params().iteritems()):
            if type(v) is float:
                # use str for representing floating point numbers
                # this way we get consistent representation across
                # architectures and versions.
                this_repr  = '%s=%s' % (k, str(v))
            else:
                # use repr of the rest
                this_repr  = '%s=%s' % (k, repr(v))
            if i > 0: 
                if (this_line_length + len(this_repr) >= 75
                                            or '\n' in this_repr):
                    params_list.append(line_sep)
                    this_line_length += len(line_sep)
                else:
                    params_list.append(', ')
                    this_line_length += 2
            params_list.append(this_repr)
            this_line_length += len(this_repr)

        params_str = ''.join(params_list)
        np.set_printoptions(**options)
        return '%s(%s)' % (
                class_name,
                params_str
            )


################################################################################
class ClassifierMixin(object):
    """ Mixin class for all classifiers in the scikit learn
    """

    def score(self, X, y):
        """
        Number of samples correctly classified.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]
            Training set.

        y : array-like, shape = [n_samples]
             Labels for X.

        Returns
        -------
        z : integer
        """
        return np.sum(self.predict(X) == y)


################################################################################
class RegressorMixin(object):
    """ Mixin class for all regression estimators in the scikit learn
    """

    def score(self, X, y):
        """
        Explained variance.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]
            Training set.

        y : array-like, shape = [n_samples]

        Returns
        -------
        z : float
        """
        return explained_variance(y, self.predict(X))

# Hidden Markov Models
#
# Author: Ron Weiss <ronweiss@gmail.com>

import string

import numpy as np
import scipy as sp

from .base import BaseEstimator
from .gmm import (GMM, lmvnpdf, logsum, normalize, sample_gaussian,
                 _distribute_covar_matrix_to_match_cvtype, _validate_covars)

ZEROLOGPROB = -1e200


class _BaseHMM(BaseEstimator):
    """Hidden Markov Model base class.

    Representation of a hidden Markov model probability distribution.
    This class allows for easy evaluation of, sampling from, and
    maximum-likelihood estimation of the parameters of a HMM.

    See the instance documentation for details specific to a
    particular object.

    Attributes
    ----------
    n_states : int (read-only)
        Number of states in the model.
    transmat : array, shape (`n_states`, `n_states`)
        Matrix of transition probabilities between states.
    startprob : array, shape ('n_states`,)
        Initial state occupation distribution.
    labels : list, len `n_states`
        Optional labels for each state.

    Methods
    -------
    eval(X)
        Compute the log likelihood of `X` under the HMM.
    decode(X)
        Find most likely state sequence for each point in `X` using the
        Viterbi algorithm.
    rvs(n=1)
        Generate `n` samples from the HMM.
    fit(X)
        Estimate HMM parameters from `X`.
    predict(X)
        Like decode, find most likely state sequence corresponding to `X`.
    score(X)
        Compute the log likelihood of `X` under the model.

    See Also
    --------
    GMM : Gaussian mixture model
    """

    # This class implements the public interface to all HMMs that
    # derive from it, including all of the machinery for the
    # forward-backward and Viterbi algorithms.  Subclasses need only
    # implement _generate_sample_from_state(), _compute_log_likelihood(),
    # _init(), _initialize_sufficient_statistics(),
    # _accumulate_sufficient_statistics(), and _do_mstep(), all of
    # which depend on the specific emission distribution.
    #
    # Subclasses will probably also want to implement properties for
    # the emission distribution parameters to expose them publically.

    def __init__(self, n_states=1, startprob=None, transmat=None,
                 startprob_prior=None, transmat_prior=None, labels=None):
        self._n_states = n_states

        if startprob is None:
            startprob = np.tile(1.0 / n_states, n_states)
        self.startprob = startprob

        if startprob_prior is None:
            startprob_prior = 1.0
        self.startprob_prior = startprob_prior
        
        if transmat is None:
            transmat = np.tile(1.0 / n_states, (n_states, n_states))
        self.transmat = transmat

        if transmat_prior is None:
            transmat_prior = 1.0
        self.transmat_prior = transmat_prior

        if labels is None:
            labels = [None] * n_states
        self.labels = labels

    def eval(self, obs, maxrank=None, beamlogprob=-np.Inf):
        """Compute the log probability under the model and compute posteriors

        Implements rank and beam pruning in the forward-backward
        algorithm to speed up inference in large models.

        Parameters
        ----------
        obs : array_like, shape (n, n_dim)
            Sequence of n_dim-dimensional data points.  Each row
            corresponds to a single point in the sequence.
        maxrank : int
            Maximum rank to evaluate for rank pruning.  If not None,
            only consider the top `maxrank` states in the inner
            sum of the forward algorithm recursion.  Defaults to None
            (no rank pruning).  See The HTK Book for more details.
        beamlogprob : float
            Width of the beam-pruning beam in log-probability units.
            Defaults to -numpy.Inf (no beam pruning).  See The HTK
            Book for more details.

        Returns
        -------
        logprob : array_like, shape (n,)
            Log probabilities of the sequence `obs`
        posteriors: array_like, shape (n, n_states)
            Posterior probabilities of each state for each
            observation

        See Also
        --------
        score : Compute the log probability under the model
        decode : Find most likely state sequence corresponding to a `obs`
        """
        obs = np.asanyarray(obs)
        framelogprob = self._compute_log_likelihood(obs)
        logprob, fwdlattice = self._do_forward_pass(framelogprob, maxrank,
                                                    beamlogprob)
        bwdlattice = self._do_backward_pass(framelogprob, fwdlattice, maxrank,
                                            beamlogprob)
        gamma = fwdlattice + bwdlattice
        # gamma is guaranteed to be correctly normalized by logprob at
        # all frames, unless we do approximate inference using pruning.
        # So, we will normalize each frame explicitly in case we
        # pruned too aggressively.
        posteriors = np.exp(gamma.T - logsum(gamma, axis=1)).T
        return logprob, posteriors

    def score(self, obs, maxrank=None, beamlogprob=-np.Inf):
        """Compute the log probability under the model.

        Parameters
        ----------
        obs : array_like, shape (n, n_dim)
            Sequence of n_dim-dimensional data points.  Each row
            corresponds to a single data point.
        maxrank : int
            Maximum rank to evaluate for rank pruning.  If not None,
            only consider the top `maxrank` states in the inner
            sum of the forward algorithm recursion.  Defaults to None
            (no rank pruning).  See The HTK Book for more details.
        beamlogprob : float
            Width of the beam-pruning beam in log-probability units.
            Defaults to -numpy.Inf (no beam pruning).  See The HTK
            Book for more details.

        Returns
        -------
        logprob : array_like, shape (n,)
            Log probabilities of each data point in `obs`

        See Also
        --------
        eval : Compute the log probability under the model and posteriors
        decode : Find most likely state sequence corresponding to a `obs`
        """
        obs = np.asanyarray(obs)
        framelogprob = self._compute_log_likelihood(obs)
        logprob, fwdlattice = self._do_forward_pass(framelogprob, maxrank,
                                                    beamlogprob)
        return logprob

    def decode(self, obs, maxrank=None, beamlogprob=-np.Inf):
        """Find most likely state sequence corresponding to `obs`.

        Uses the Viterbi algorithm.

        Parameters
        ----------
        obs : array_like, shape (n, n_dim)
            List of n_dim-dimensional data points.  Each row corresponds to a
            single data point.
        maxrank : int
            Maximum rank to evaluate for rank pruning.  If not None,
            only consider the top `maxrank` states in the inner
            sum of the forward algorithm recursion.  Defaults to None
            (no rank pruning).  See The HTK Book for more details.
        beamlogprob : float
            Width of the beam-pruning beam in log-probability units.
            Defaults to -numpy.Inf (no beam pruning).  See The HTK
            Book for more details.

        Returns
        -------
        viterbi_logprob : float
            Log probability of the maximum likelihood path through the HMM
        states : array_like, shape (n,)
            Index of the most likely states for each observation

        See Also
        --------
        eval : Compute the log probability under the model and posteriors
        score : Compute the log probability under the model
        """
        obs = np.asanyarray(obs)
        framelogprob = self._compute_log_likelihood(obs)
        logprob, state_sequence = self._do_viterbi_pass(framelogprob, maxrank,
                                                        beamlogprob)
        return logprob, state_sequence

    def predict(self, obs, **kwargs):
        """Find most likely state sequence corresponding to `obs`.

        Parameters
        ----------
        obs : array_like, shape (n, n_dim)
            List of n_dim-dimensional data points.  Each row corresponds to a
            single data point.
        maxrank : int
            Maximum rank to evaluate for rank pruning.  If not None,
            only consider the top `maxrank` states in the inner
            sum of the forward algorithm recursion.  Defaults to None
            (no rank pruning).  See The HTK Book for more details.
        beamlogprob : float
            Width of the beam-pruning beam in log-probability units.
            Defaults to -numpy.Inf (no beam pruning).  See The HTK
            Book for more details.

        Returns
        -------
        states : array_like, shape (n,)
            Index of the most likely states for each observation
        """
        logprob, state_sequence = self.decode(obs, **kwargs)
        return state_sequence

    def rvs(self, n=1):
        """Generate random samples from the model.

        Parameters
        ----------
        n : int
            Number of samples to generate.

        Returns
        -------
        obs : array_like, length `n`
            List of samples
        """

        startprob_pdf = self.startprob
        startprob_cdf = np.cumsum(startprob_pdf)
        transmat_pdf = self.transmat
        transmat_cdf = np.cumsum(transmat_pdf, 1)

        # Initial state.
        rand = np.random.rand()
        currstate = (startprob_cdf > rand).argmax()
        obs = [self._generate_sample_from_state(currstate)]

        for x in xrange(n-1):
            rand = np.random.rand()
            currstate = (transmat_cdf[currstate] > rand).argmax()
            obs.append(self._generate_sample_from_state(currstate))

        return np.array(obs)

    def fit(self, obs, n_iter=10, thresh=1e-2, params=string.letters,
            init_params=string.letters,
            maxrank=None, beamlogprob=-np.Inf, **kwargs):
        """Estimate model parameters.

        An initialization step is performed before entering the EM
        algorithm. If you want to avoid this step, set the keyword
        argument init_params to the empty string ''. Likewise, if you
        would like just to do an initialization, call this method with
        n_iter=0.

        Parameters
        ----------
        obs : list
            List of array-like observation sequences (shape (n_i, n_dim)).
        n_iter : int, optional
            Number of iterations to perform.
        thresh : float, optional
            Convergence threshold.
        params : string, optional
            Controls which parameters are updated in the training
            process.  Can contain any combination of 's' for startprob,
            't' for transmat, 'm' for means, and 'c' for covars, etc.
            Defaults to all parameters.
        init_params : string, optional
            Controls which parameters are initialized prior to
            training.  Can contain any combination of 's' for
            startprob, 't' for transmat, 'm' for means, and 'c' for
            covars, etc.  Defaults to all parameters.
        maxrank : int, optional
            Maximum rank to evaluate for rank pruning.  If not None,
            only consider the top `maxrank` states in the inner
            sum of the forward algorithm recursion.  Defaults to None
            (no rank pruning).  See "The HTK Book" for more details.
        beamlogprob : float, optional
            Width of the beam-pruning beam in log-probability units.
            Defaults to -numpy.Inf (no beam pruning).  See "The HTK
            Book" for more details.

        Notes
        -----
        In general, `logprob` should be non-decreasing unless
        aggressive pruning is used.  Decreasing `logprob` is generally
        a sign of overfitting (e.g. a covariance parameter getting too
        small).  You can fix this by getting more training data, or
        decreasing `covars_prior`.
        """
        obs = np.asanyarray(obs)

        self._init(obs, init_params, **kwargs)

        logprob = []
        for i in xrange(n_iter):
            # Expectation step
            stats = self._initialize_sufficient_statistics()
            curr_logprob = 0
            for seq in obs:
                framelogprob = self._compute_log_likelihood(seq)
                lpr, fwdlattice = self._do_forward_pass(framelogprob, maxrank,
                                                       beamlogprob)
                bwdlattice = self._do_backward_pass(framelogprob, fwdlattice,
                                                   maxrank, beamlogprob)
                gamma = fwdlattice + bwdlattice
                posteriors = np.exp(gamma.T - logsum(gamma, axis=1)).T
                curr_logprob += lpr
                self._accumulate_sufficient_statistics(
                    stats, seq, framelogprob, posteriors, fwdlattice,
                    bwdlattice, params)
            logprob.append(curr_logprob)

            # Check for convergence.
            if i > 0 and abs(logprob[-1] - logprob[-2]) < thresh:
                break

            # Maximization step
            self._do_mstep(stats, params, **kwargs)

        return self

    @property
    def n_states(self):
        """Number of states in the model."""
        return self._n_states

    def _get_startprob(self):
        """Mixing startprob for each state."""
        return np.exp(self._log_startprob)

    def _set_startprob(self, startprob):
        if len(startprob) != self._n_states:
            raise ValueError('startprob must have length n_states')
        if not np.allclose(np.sum(startprob), 1.0):
            raise ValueError('startprob must sum to 1.0')

        self._log_startprob = np.log(np.asanyarray(startprob).copy())

    startprob = property(_get_startprob, _set_startprob)

    def _get_transmat(self):
        """Matrix of transition probabilities."""
        return np.exp(self._log_transmat)

    def _set_transmat(self, transmat):
        if np.asanyarray(transmat).shape != (self._n_states, self._n_states):
            raise ValueError('transmat must have shape (n_states, n_states)')
        if not np.all(np.allclose(np.sum(transmat, axis=1), 1.0)):
            raise ValueError('Rows of transmat must sum to 1.0')

        self._log_transmat = np.log(np.asanyarray(transmat).copy())
        underflow_idx = np.isnan(self._log_transmat)
        self._log_transmat[underflow_idx] = -np.Inf

    transmat = property(_get_transmat, _set_transmat)

    def _do_viterbi_pass(self, framelogprob, maxrank=None,
                         beamlogprob=-np.Inf):
        nobs = len(framelogprob)
        lattice = np.zeros((nobs, self._n_states))
        traceback = np.zeros((nobs, self._n_states), dtype=np.int)

        lattice[0] = self._log_startprob + framelogprob[0]
        for n in xrange(1, nobs):
            idx = self._prune_states(lattice[n-1], maxrank, beamlogprob)
            pr = self._log_transmat[idx].T + lattice[n-1,idx]
            lattice[n] = np.max(pr, axis=1) + framelogprob[n]
            traceback[n] = np.argmax(pr, axis=1)
        lattice[lattice <= ZEROLOGPROB] = -np.Inf

        # Do traceback.
        reverse_state_sequence = []
        s = lattice[-1].argmax()
        logprob = lattice[-1,s]
        for frame in reversed(traceback):
            reverse_state_sequence.append(s)
            s = frame[s]

        reverse_state_sequence.reverse()
        return logprob, np.array(reverse_state_sequence)

    def _do_forward_pass(self, framelogprob, maxrank=None,
                         beamlogprob=-np.Inf):
        nobs = len(framelogprob)
        fwdlattice = np.zeros((nobs, self._n_states))

        fwdlattice[0] = self._log_startprob + framelogprob[0]
        for n in xrange(1, nobs):
            idx = self._prune_states(fwdlattice[n-1], maxrank, beamlogprob)
            fwdlattice[n] = (logsum(self._log_transmat[idx].T
                                    + fwdlattice[n-1,idx], axis=1)
                             + framelogprob[n])
        fwdlattice[fwdlattice <= ZEROLOGPROB] = -np.Inf

        return logsum(fwdlattice[-1]), fwdlattice

    def _do_backward_pass(self, framelogprob, fwdlattice, maxrank=None,
                          beamlogprob=-np.Inf):
        nobs = len(framelogprob)
        bwdlattice = np.zeros((nobs, self._n_states))

        for n in xrange(nobs - 1, 0, -1):
            # Do HTK style pruning (p. 137 of HTK Book version 3.4).
            # Don't bother computing backward probability if
            # fwdlattice * bwdlattice is more than a certain distance
            # from the total log likelihood.
            idx = self._prune_states(bwdlattice[n] + fwdlattice[n], None,
                                     -50)
                                     #beamlogprob)
                                     #-np.Inf)
            bwdlattice[n-1] = logsum(self._log_transmat[:,idx]
                                     + bwdlattice[n,idx] + framelogprob[n,idx],
                                     axis=1)
        bwdlattice[bwdlattice <= ZEROLOGPROB] = -np.Inf

        return bwdlattice

    def _prune_states(self, lattice_frame, maxrank, beamlogprob):
        """ Returns indices of the active states in `lattice_frame`
        after rank and beam pruning.
        """
        # Beam pruning
        threshlogprob = logsum(lattice_frame) + beamlogprob

        # Rank pruning
        if maxrank:
            # How big should our rank pruning histogram be?
            nbins = 3 * len(lattice_frame)

            lattice_min = lattice_frame[lattice_frame > ZEROLOGPROB].min() - 1
            hst, cdf = np.histogram(lattice_frame, bins=nbins,
                                    range=(lattice_min, lattice_frame.max()))

            # Want to look at the high ranks.
            hst = hst[::-1].cumsum()
            cdf = cdf[::-1]

            rankthresh = cdf[hst >= min(maxrank, self._n_states)].max()

            # Only change the threshold if it is stricter than the beam
            # threshold.
            threshlogprob = max(threshlogprob, rankthresh)

        # Which states are active?
        state_idx, = np.nonzero(lattice_frame >= threshlogprob)
        return state_idx

    def _compute_log_likelihood(self, obs):
        pass

    def _generate_sample_from_state(self, state):
        pass

    def _init(self, obs, params, **kwargs):
        if 's' in params:
            self.startprob[:] = 1.0 / self._n_states
        if 't' in params:
            self.transmat[:] = 1.0 / self._n_states

    # Methods used by self.fit()
    
    def _initialize_sufficient_statistics(self):
        stats = {'nobs': 0,
                 'start': np.zeros(self._n_states),
                 'trans': np.zeros((self._n_states, self._n_states))}
        return stats

    def _accumulate_sufficient_statistics(self, stats, seq, framelogprob,
                                          posteriors, fwdlattice, bwdlattice,
                                          params):
        stats['nobs'] += 1
        if 's' in params:
            stats['start'] += posteriors[0]
        if 't' in params:
            for t in xrange(len(framelogprob)):
                zeta = (fwdlattice[t-1][:,np.newaxis] + self._log_transmat
                        + framelogprob[t] + bwdlattice[t])
                stats['trans'] += np.exp(zeta - logsum(zeta))

    def _do_mstep(self, stats, params, **kwargs):
        # Based on Huang, Acero, Hon, "Spoken Language Processing",
        # p. 443 - 445
        if 's' in params:
            self.startprob = normalize(
                np.maximum(self.startprob_prior - 1.0 + stats['start'], 1e-20))
        if 't' in params:
            self.transmat = normalize(
                np.maximum(self.transmat_prior - 1.0 + stats['trans'], 1e-20),
                axis=1)


class GaussianHMM(_BaseHMM):
    """Hidden Markov Model with Gaussian emissions

    Representation of a hidden Markov model probability distribution.
    This class allows for easy evaluation of, sampling from, and
    maximum-likelihood estimation of the parameters of a HMM.

    Attributes
    ----------
    cvtype : string (read-only)
        String describing the type of covariance parameters used by
        the model.  Must be one of 'spherical', 'tied', 'diag', 'full'.
    n_dim : int (read-only)
        Dimensionality of the Gaussian emissions.
    n_states : int (read-only)
        Number of states in the model.
    transmat : array, shape (`n_states`, `n_states`)
        Matrix of transition probabilities between states.
    startprob : array, shape ('n_states`,)
        Initial state occupation distribution.
    means : array, shape (`n_states`, `n_dim`)
        Mean parameters for each state.
    covars : array
        Covariance parameters for each state.  The shape depends on
        `cvtype`:
            (`n_states`,)                   if 'spherical',
            (`n_dim`, `n_dim`)              if 'tied',
            (`n_states`, `n_dim`)           if 'diag',
            (`n_states`, `n_dim`, `n_dim`)  if 'full'
    labels : list, len `n_states`
        Optional labels for each state.

    Methods
    -------
    eval(X)
        Compute the log likelihood of `X` under the HMM.
    decode(X)
        Find most likely state sequence for each point in `X` using the
        Viterbi algorithm.
    rvs(n=1)
        Generate `n` samples from the HMM.
    init(X)
        Initialize HMM parameters from `X`.
    fit(X)
        Estimate HMM parameters from `X` using the Baum-Welch algorithm.
    predict(X)
        Like decode, find most likely state sequence corresponding to `X`.
    score(X)
        Compute the log likelihood of `X` under the model.

    Examples
    --------
    >>> ghmm = GaussianHMM(n_states=2, n_dim=1)

    See Also
    --------
    GMM : Gaussian mixture model
    """
    
    def __init__(self, n_states=1, n_dim=1, cvtype='diag', startprob=None,
                 transmat=None, labels=None, means=None, covars=None,
                 startprob_prior=None, transmat_prior=None,
                 means_prior=None, means_weight=0,
                 covars_prior=1e-2, covars_weight=1):
        """Create a hidden Markov model with Gaussian emissions.

        Initializes parameters such that every state has zero mean and
        identity covariance.

        Parameters
        ----------
        n_states : int
            Number of states.
        n_dim : int
            Dimensionality of the emissions.
        cvtype : string
            String describing the type of covariance parameters to
            use.  Must be one of 'spherical', 'tied', 'diag', 'full'.
            Defaults to 'diag'.
        """
        super(GaussianHMM, self).__init__(n_states, startprob, transmat,
                                          startprob_prior=startprob_prior,
                                          transmat_prior=transmat_prior,
                                          labels=labels)

        self._n_dim = n_dim
        self._cvtype = cvtype
        if not cvtype in ['spherical', 'tied', 'diag', 'full']:
            raise ValueError('bad cvtype')

        if means is None:
            means = np.zeros((n_states, n_dim))
        self.means = means

        self.means_prior = means_prior
        self.means_weight = means_weight

        if covars is None:
            covars = _distribute_covar_matrix_to_match_cvtype(np.eye(n_dim),
                                                              cvtype, n_states)
        self.covars = covars

        self.covars_prior = covars_prior
        self.covars_weight = covars_weight

    # Read-only properties.
    @property
    def cvtype(self):
        """Covariance type of the model.

        Must be one of 'spherical', 'tied', 'diag', 'full'.
        """
        return self._cvtype

    @property
    def n_dim(self):
        """Dimensionality of the emissions."""
        return self._n_dim

    def _get_means(self):
        """Mean parameters for each state."""
        return self._means

    def _set_means(self, means):
        means = np.asanyarray(means)
        if means.shape != (self._n_states, self._n_dim):
            raise ValueError('means must have shape (n_states, n_dim)')
        self._means = means.copy()

    means = property(_get_means, _set_means)

    def _get_covars(self):
        """Covariance parameters for each state."""
        return self._covars

    def _set_covars(self, covars):
        covars = np.asanyarray(covars)
        _validate_covars(covars, self._cvtype, self._n_states, self._n_dim)
        self._covars = covars.copy()

    covars = property(_get_covars, _set_covars)

    def _compute_log_likelihood(self, obs):
        return lmvnpdf(obs, self._means, self._covars, self._cvtype)

    def _generate_sample_from_state(self, state):
        if self._cvtype == 'tied':
            cv = self._covars
        else:
            cv = self._covars[state]
        return sample_gaussian(self._means[state], cv, self._cvtype)

    def _init(self, obs, params='stmc', **kwargs):
        super(GaussianHMM, self)._init(obs, params=params)


        if 'm' in params:
            self._means, tmp = sp.cluster.vq.kmeans2(obs[0], self._n_states,
                                                     **kwargs)
        if 'c' in params:
            cv = np.cov(obs[0].T)
            if not cv.shape:
                cv.shape = (1, 1)
            self._covars = _distribute_covar_matrix_to_match_cvtype(
                cv, self._cvtype, self._n_states)

    def _initialize_sufficient_statistics(self):
        stats = super(GaussianHMM, self)._initialize_sufficient_statistics()
        stats['post'] = np.zeros(self._n_states)
        stats['obs'] = np.zeros((self._n_states, self._n_dim))
        stats['obs**2'] = np.zeros((self._n_states, self._n_dim))
        stats['obs*obs.T'] = np.zeros((self._n_states, self._n_dim,
                                       self._n_dim))
        return stats

    def _accumulate_sufficient_statistics(self, stats, obs, framelogprob,
                                          posteriors, fwdlattice, bwdlattice,
                                          params):
        super(GaussianHMM, self)._accumulate_sufficient_statistics(
            stats, obs, framelogprob, posteriors, fwdlattice, bwdlattice,
            params)

        if 'm' in params or 'c' in params:
            stats['post'] += posteriors.sum(axis=0)
            stats['obs'] += np.dot(posteriors.T, obs)

        if 'c' in params:
            if self._cvtype in ('spherical', 'diag'):
                stats['obs**2'] += np.dot(posteriors.T, obs**2)
            elif self._cvtype in ('tied', 'full'):
                for t, o in enumerate(obs):
                    obsobsT = np.outer(o, o)
                    for c in xrange(self._n_states):
                        stats['obs*obs.T'][c] += posteriors[t,c] * obsobsT

    def _do_mstep(self, stats, params, **kwargs):
        super(GaussianHMM, self)._do_mstep(stats, params)

        # Based on Huang, Acero, Hon, "Spoken Language Processing",
        # p. 443 - 445
        denom = stats['post'][:,np.newaxis]
        if 'm' in params:
            prior = self.means_prior
            weight = self.means_weight
            if prior is None:
                weight = 0
                prior = 0
            self._means = (weight * prior + stats['obs']) / (weight + denom)

        if 'c' in params:
            covars_prior = self.covars_prior
            covars_weight = self.covars_weight
            if covars_prior is None:
                covars_weight = 0
                covars_prior = 0

            means_prior = self.means_prior
            means_weight = self.means_weight
            if means_prior is None:
                means_weight = 0
                means_prior = 0
            meandiff = self._means - means_prior

            if self._cvtype in ('spherical', 'diag'):
                cv_num = (means_weight * (meandiff)**2
                          + stats['obs**2']
                          - 2 * self._means * stats['obs']
                          + self._means**2 * denom)
                cv_den = max(covars_weight - 1, 0) + denom
                if self._cvtype == 'spherical':
                    self._covars = (covars_prior / cv_den.mean(axis=1)
                                   + np.mean(cv_num / cv_den, axis=1))
                elif self._cvtype == 'diag':
                    self._covars = (covars_prior + cv_num) / cv_den
            elif self._cvtype in ('tied', 'full'):
                cvnum = np.empty((self._n_states, self._n_dim, self._n_dim))
                for c in xrange(self._n_states):
                    cvnum[c] = (means_weight * np.outer(meandiff[c],
                                                        meandiff[c])
                                + stats['obs*obs.T'][c]
                                - 2 * np.outer(stats['obs'][c], self._means[c])
                                + np.outer(self._means[c], self._means[c])
                                * stats['post'][c])
                cvweight = max(covars_weight - self._n_dim, 0)
                if self._cvtype == 'tied':
                    self._covars = ((covars_prior + cvnum.sum(axis=0))
                                    / (cvweight + stats['post'].sum()))
                elif self._cvtype == 'full':
                    self._covars = ((covars_prior + cvnum)
                                   / (cvweight + stats['post'][:,None,None]))


class MultinomialHMM(_BaseHMM):
    """Hidden Markov Model with multinomial (discrete) emissions

    Attributes
    ----------
    n_states : int (read-only)
        Number of states in the model.
    nsymbols : int
        Number of symbols (TODO: explain the difference with n_states)
    transmat : array, shape (`n_states`, `n_states`)
        Matrix of transition probabilities between states.
    startprob : array, shape ('n_states`,)
        Initial state occupation distribution.
    emissionprob: array, shape ('n_states`, K)
        Probability of emitting a given symbol when in each state.  K
        is the number of possible symbols in the observations.
    labels : list, len `n_states`
        Optional labels for each state.

    Methods
    -------
    eval(X)
        Compute the log likelihood of `X` under the HMM.
    decode(X)
        Find most likely state sequence for each point in `X` using the
        Viterbi algorithm.
    rvs(n=1)
        Generate `n` samples from the HMM.
    init(X)
        Initialize HMM parameters from `X`.
    fit(X)
        Estimate HMM parameters from `X` using the Baum-Welch algorithm.
    predict(X)
        Like decode, find most likely state sequence corresponding to `X`.
    score(X)
        Compute the log likelihood of `X` under the model.

    Examples
    --------
    >>> mhmm = MultinomialHMM(n_states=2, nsymbols=3)

    See Also
    --------
    GaussianHMM : HMM with Gaussian emissions
    """

    def __init__(self, n_states=1, nsymbols=1, startprob=None, transmat=None,
                 startprob_prior=None, transmat_prior=None,
                 labels=None, emissionprob=None):
        """Create a hidden Markov model with multinomial emissions.

        Parameters
        ----------
        n_states : int
            Number of states.
        """
        super(MultinomialHMM, self).__init__(n_states, startprob, transmat,
                                             startprob_prior=startprob_prior,
                                             transmat_prior=transmat_prior,
                                             labels=labels)
        self._nsymbols = nsymbols
        if not emissionprob:
            emissionprob = normalize(np.random.rand(self.n_states,
                                                    self.nsymbols), 1)
        self.emissionprob = emissionprob

    # Read-only properties.
    @property
    def nsymbols(self):
        return self._nsymbols

    def _get_emissionprob(self):
        """Emission probability distribution for each state."""
        return np.exp(self._log_emissionprob)

    def _set_emissionprob(self, emissionprob):
        emissionprob = np.asanyarray(emissionprob)
        if emissionprob.shape != (self._n_states, self._nsymbols):
            raise ValueError('emissionprob must have shape '
                             '(n_states, nsymbols)')

        self._log_emissionprob = np.log(emissionprob)
        underflow_idx = np.isnan(self._log_emissionprob)
        self._log_emissionprob[underflow_idx] = -np.Inf

    emissionprob = property(_get_emissionprob, _set_emissionprob)

    def _compute_log_likelihood(self, obs):
        return self._log_emissionprob[:,obs].T

    def _generate_sample_from_state(self, state):
        cdf = np.cumsum(self.emissionprob[state,:])
        rand = np.random.rand()
        symbol = (cdf > rand).argmax()
        return symbol

    def _init(self, obs, params='ste', **kwargs):
        super(MultinomialHMM, self)._init(obs, params=params)

        if 'e' in params:
            emissionprob = normalize(np.random.rand(self._n_states,
                                                    self._nsymbols), 1)
            self.emissionprob = emissionprob

    def _initialize_sufficient_statistics(self):
        stats = super(MultinomialHMM, self)._initialize_sufficient_statistics()
        stats['obs'] = np.zeros((self._n_states, self._nsymbols))
        return stats

    def _accumulate_sufficient_statistics(self, stats, obs, framelogprob,
                                          posteriors, fwdlattice, bwdlattice,
                                          params):
        super(MultinomialHMM, self)._accumulate_sufficient_statistics(
            stats, obs, framelogprob, posteriors, fwdlattice, bwdlattice,
            params)
        if 'e' in params:
            for t,symbol in enumerate(obs):
                stats['obs'][:,symbol] += posteriors[t,:]

    def _do_mstep(self, stats, params, **kwargs):
        super(MultinomialHMM, self)._do_mstep(stats, params)
        if 'e' in params:
            self.emissionprob = (stats['obs']
                                 / stats['obs'].sum(1)[:,np.newaxis])


class GMMHMM(_BaseHMM):
    """Hidden Markov Model with Gaussin mixture emissions

    Attributes
    ----------
    n_states : int (read-only)
        Number of states in the model.
    transmat : array, shape (`n_states`, `n_states`)
        Matrix of transition probabilities between states.
    startprob : array, shape ('n_states`,)
        Initial state occupation distribution.
    gmms: array of GMM objects, length 'n_states`
        GMM emission distributions for each state
    labels : list, len `n_states`
        Optional labels for each state.

    Methods
    -------
    eval(X)
        Compute the log likelihood of `X` under the HMM.
    decode(X)
        Find most likely state sequence for each point in `X` using the
        Viterbi algorithm.
    rvs(n=1)
        Generate `n` samples from the HMM.
    init(X)
        Initialize HMM parameters from `X`.
    fit(X)
        Estimate HMM parameters from `X` using the Baum-Welch algorithm.
    predict(X)
        Like decode, find most likely state sequence corresponding to `X`.
    score(X)
        Compute the log likelihood of `X` under the model.

    Examples
    --------
    >>> hmm = GMMHMM(n_states=2, n_mix=10, n_dim=3)

    See Also
    --------
    GaussianHMM : HMM with Gaussian emissions
    """

    def __init__(self, n_states=1, n_dim=1, n_mix=1, startprob=None,
                 transmat=None, startprob_prior=None, transmat_prior=None,
                 labels=None, gmms=None, cvtype=None):
        """Create a hidden Markov model with GMM emissions.

        Parameters
        ----------
        n_states : int
            Number of states.
        n_dim : int (read-only)
            Dimensionality of the emissions.
        """
        super(GMMHMM, self).__init__(n_states, startprob, transmat,
                                     startprob_prior=startprob_prior,
                                     transmat_prior=transmat_prior,
                                     labels=labels)

        self._n_dim = n_dim

        if gmms is None:
            gmms = []
            for x in xrange(self.n_states):
                if cvtype is None:
                    g = GMM(n_mix, n_dim)
                else:
                    g = GMM(n_mix, n_dim, cvtype=cvtype)
                gmms.append(g)
        self.gmms = gmms

    # Read-only properties.
    @property
    def n_dim(self):
        """Dimensionality of the emissions from this HMM."""
        return self._n_dim

    def _compute_log_likelihood(self, obs):
        return np.array([g.score(obs) for g in self.gmms]).T

    def _generate_sample_from_state(self, state):
        return self.gmms[state].rvs(1).flatten()

    def _init(self, obs, params='stwmc', **kwargs):
        super(GMMHMM, self)._init(obs, params=params)

        allobs = np.concatenate(obs, 0)
        for g in self.gmms:
            g.fit(allobs, n_iter=0, init_params=params)

    def _initialize_sufficient_statistics(self):
        stats = super(GMMHMM, self)._initialize_sufficient_statistics()
        stats['norm'] = [np.zeros(g.weights.shape) for g in self.gmms]
        stats['means'] = [np.zeros(np.shape(g.means)) for g in self.gmms]
        stats['covars'] = [np.zeros(np.shape(g._covars)) for g in self.gmms]
        return stats

    def _accumulate_sufficient_statistics(self, stats, obs, framelogprob,
                                          posteriors, fwdlattice, bwdlattice,
                                          params):
        super(GMMHMM, self)._accumulate_sufficient_statistics(
            stats, obs, framelogprob, posteriors, fwdlattice, bwdlattice,
            params)
        
        for state,g in enumerate(self.gmms):
            gmm_logprob, gmm_posteriors = g.eval(obs)
            gmm_posteriors *= posteriors[:,state][:,np.newaxis]
            tmpgmm = GMM(g.n_states, g.n_dim, cvtype=g.cvtype)
            norm = tmpgmm._do_mstep(obs, gmm_posteriors, params)

            stats['norm'][state] += norm
            if 'm' in params:
                stats['means'][state] += tmpgmm.means * norm[:,np.newaxis]
            if 'c' in params:
                if tmpgmm.cvtype == 'tied':
                    stats['covars'][state] += tmpgmm._covars * norm.sum()
                else:
                    cvnorm = np.copy(norm)
                    shape = np.ones(tmpgmm._covars.ndim)
                    shape[0] = np.shape(tmpgmm._covars)[0]
                    cvnorm.shape = shape
                    stats['covars'][state] += tmpgmm._covars * cvnorm

    def _do_mstep(self, stats, params, covars_prior=1e-2, **kwargs):
        super(GMMHMM, self)._do_mstep(stats, params)
        # All we have left to do is apply covars_prior to the parameters
        # we updated in _accumulate_sufficient_statistics.
        for state,g in enumerate(self.gmms):
            norm = stats['norm'][state]
            if 'w' in params:
                g.weights = normalize(norm)
            if 'm' in params:
                g.means = stats['means'][state] / norm[:,np.newaxis]
            if 'c' in params:
                if g.cvtype == 'tied':
                    g.covars = (stats['covars'][state]
                                + covars_prior * np.eye(g.n_dim)) / norm.sum()
                else:
                    cvnorm = np.copy(norm)
                    shape = np.ones(g._covars.ndim)
                    shape[0] = np.shape(g._covars)[0]
                    cvnorm.shape = shape
                    if g.cvtype == 'spherical' or g.cvtype == 'diag':
                        g.covars = (stats['covars'][state]
                                    + covars_prior) / cvnorm
                    elif g.cvtype == 'full':
                        eye = np.eye(g.n_dim)
                        g.covars = ((stats['covars'][state]
                                     + covars_prior * eye[np.newaxis,:,:])
                                    / cvnorm)

""" Algorithms for clustering : Meanshift,  Affinity propagation and spectral 
clustering.

Author: Alexandre Gramfort alexandre.gramfort@inria.fr
        Gael Varoquaux gael.varoquaux@normalesup.org
"""

from math import floor
import numpy as np

from ..base import BaseEstimator

def euclidian_distances(X, Y=None):
    """
    Considering the rows of X (and Y=X) as vectors, compute the
    distance matrix between each pair of vector

    Parameters
    ----------
    X, array of shape (n_samples_1, n_features)

    Y, array of shape (n_samples_2, n_features), default None
            if Y is None, then Y=X is used instead

    Returns
    -------
    distances, array of shape (n_samples_1, n_samples_2)
    """
    if Y is None:
        Y = X
    if X.shape[1] != Y.shape[1]:
        raise ValueError, "incompatible dimension for X and Y matrices"

    XX = np.sum(X * X, axis=1)[:,np.newaxis]
    if Y is None:
        YY = XX.T
    else:
        YY = np.sum(Y * Y, axis=1)[np.newaxis,:]
    distances = XX + YY # Using broadcasting
    distances -= 2 * np.dot(X, Y.T)
    distances = np.maximum(distances, 0)
    distances = np.sqrt(distances)
    return distances


def estimate_bandwidth(X, quantile=0.3):
    """Estimate the bandwith ie the radius to use with an RBF kernel
    in the MeanShift algorithm

    X: array [n_samples, n_features]
        Input points

    quantile: float, default 0.3
        should be between [0, 1]
        0.5 means that the median is all pairwise distances is used
    """
    distances = euclidian_distances(X)
    distances = np.triu(distances, 1)
    distances_sorted = np.sort(distances[distances > 0])
    bandwidth = distances_sorted[floor(quantile * len(distances_sorted))]
    return bandwidth


def mean_shift(X, bandwidth=None):
    """Perform MeanShift Clustering of data using a flat kernel

    Parameters
    ----------

    X : array [n_samples, n_features]
        Input points

    bandwidth : float, optional
        kernel bandwidth
        If bandwidth is not defined, it is set using
        a heuristic given by the median of all pairwise distances

    Returns
    -------

    cluster_centers : array [n_clusters, n_features]
        Coordinates of cluster centers

    labels : array [n_samples]
        cluster labels for each point

    Notes
    -----
    See examples/plot_meanshift.py for an example.

    K. Funkunaga and L.D. Hosteler, "The Estimation of the Gradient of a
    Density Function, with Applications in Pattern Recognition"

    """

    if bandwidth is None:
        bandwidth = estimate_bandwidth(X)

    n_points, n_features = X.shape

    n_clusters = 0
    bandwidth_squared = bandwidth**2
    points_idx_init = np.arange(n_points)
    stop_thresh     = 1e-3*bandwidth # when mean has converged
    cluster_centers = [] # center of clusters
    # track if a points been seen already
    been_visited_flag = np.zeros(n_points, dtype=np.bool)
    # number of points to possibly use as initilization points
    n_points_init = n_points
    # used to resolve conflicts on cluster membership
    cluster_votes = []

    random_state = np.random.RandomState(0)

    while n_points_init:
        # pick a random seed point
        tmp_index   = random_state.randint(n_points_init)
        # use this point as start of mean
        start_idx   = points_idx_init[tmp_index]
        my_mean     = X[start_idx, :] # intilize mean to this points location
        # points that will get added to this cluster
        my_members  = np.zeros(n_points, dtype=np.bool)
        # used to resolve conflicts on cluster membership
        this_cluster_votes = np.zeros(n_points, dtype=np.uint16)

        while True: # loop until convergence

            # dist squared from mean to all points still active
            sqrt_dist_to_all = np.sum((my_mean - X)**2, axis=1)

            # points within bandwidth
            in_idx = sqrt_dist_to_all < bandwidth_squared
            # add a vote for all the in points belonging to this cluster
            this_cluster_votes[in_idx] += 1

            my_old_mean  = my_mean # save the old mean
            my_mean      = np.mean(X[in_idx,:], axis=0) # compute the new mean
            # add any point within bandwidth to the cluster
            my_members   = np.logical_or(my_members, in_idx)
            # mark that these points have been visited
            been_visited_flag[my_members] = True

            if np.linalg.norm(my_mean-my_old_mean) < stop_thresh:

                # check for merge possibilities
                merge_with = -1
                for c in range(n_clusters):
                    # distance from possible new clust max to old clust max
                    dist_to_other = np.linalg.norm(my_mean -
                                                        cluster_centers[c])
                    # if its within bandwidth/2 merge new and old
                    if dist_to_other < bandwidth/2:
                        merge_with = c
                        break

                if merge_with >= 0: # something to merge
                    # record the max as the mean of the two merged
                    # (I know biased twoards new ones)
                    cluster_centers[merge_with] = 0.5 * (my_mean+
                                                cluster_centers[merge_with])
                    # add these votes to the merged cluster
                    cluster_votes[merge_with] += this_cluster_votes
                else: # its a new cluster
                    n_clusters += 1 # increment clusters
                    cluster_centers.append(my_mean) # record the mean
                    cluster_votes.append(this_cluster_votes)

                break

        # we can initialize with any of the points not yet visited
        points_idx_init = np.where(been_visited_flag == False)[0]
        n_points_init   = points_idx_init.size # number of active points in set

    # a point belongs to the cluster with the most votes
    labels = np.argmax(cluster_votes, axis=0)

    return cluster_centers, labels


################################################################################
class MeanShift(BaseEstimator):
    """MeanShift clustering


    Parameters
    ----------

    bandwidth: float, optional
        Bandwith used in the RBF kernel
        If not set, the bandwidth is estimated.
        See clustering.estimate_bandwidth

    Methods
    -------

    fit(X):
        Compute MeanShift clustering

    Attributes
    ----------

    cluster_centers_: array, [n_clusters, n_features]
        Coordinates of cluster centers

    labels_:
        Labels of each point

    Notes
    -----

    Reference:

    K. Funkunaga and L.D. Hosteler, "The Estimation of the Gradient of a
    Density Function, with Applications in Pattern Recognition"

    The algorithmic complexity of the mean shift algorithm is O(T n^2)
    with n the number of samples and T the number of iterations. It is
    not adviced for a large number of samples.
    """

    def __init__(self, bandwidth=None):
        self.bandwidth = bandwidth

    def fit(self, X, **params):
        """ Compute MeanShift
        
            Parameters
            -----------
            X : array [n_samples, n_features]
                Input points

        """
        self._set_params(**params)
        self.cluster_centers_, self.labels_ = mean_shift(X, self.bandwidth)
        return self



"""
Clustering algorithms
"""

from .spectral import spectral_clustering, SpectralClustering
from .mean_shift_ import mean_shift, MeanShift, estimate_bandwidth
from .affinity_propagation_ import affinity_propagation, AffinityPropagation
from .k_means_ import k_means, KMeans


""" K-means clustering
"""

# Authors: Gael Varoquaux <gael.xaroquaux@normalesup.org>
#          Thomas Rueckstiess <ruecksti@in.tum.de>
# License: BSD


import numpy as np

from scipy import cluster

from ..base import BaseEstimator

# kinit originaly from pybrain:
# http://github.com/pybrain/pybrain/raw/master/pybrain/auxiliary/kmeans.py
def k_init(X, k, n_samples_max=500):
    """ Init k seeds according to kmeans++

        Parameters
        -----------
        X: array, shape (n_samples, n_features)
            The data
        k: integer
            The number of seeds to choose
        n_samples_max: integer, optional
            The maximum number of samples to use: the complexity of the 
            algorithm is n_samples**2, if n_samples > n_samples_max,
            we use the Niquist strategy, and choose our centers in the 
            n_samples_max samples randomly choosen.

        Notes
        ------
        Selects initial cluster centers for k-mean clustering in a smart way 
        to speed up convergence. see: Arthur, D. and Vassilvitskii, S. 
        "k-means++: the advantages of careful seeding". ACM-SIAM symposium 
        on Discrete algorithms. 2007

        Implementation from Yong Sun's website
        http://blogs.sun.com/yongsun/entry/k_means_and_k_means
    """
    n_samples = X.shape[0]
    if n_samples >= n_samples_max:
        X = X[np.random.randint(n_samples, size=n_samples_max)]
        n_samples = n_samples_max

    'choose the 1st seed randomly, and store D(x)^2 in D[]'
    centers = [X[np.random.randint(n_samples)]]
    D = ((X - centers[0])**2).sum(axis=-1)

    for _ in range(k - 1):
        bestDsum = bestIdx = -1

        for i in range(n_samples):
            'Dsum = sum_{x in X} min(D(x)^2,||x-xi||^2)'
            Dsum = np.minimum(D, ((X - X[i])**2).sum(axis=-1)
                              ).sum()

            if bestDsum < 0 or Dsum < bestDsum:
                bestDsum, bestIdx = Dsum, i

        centers.append(X[bestIdx])
        D = np.minimum(D, ((X - X[bestIdx])**2).sum(axis=-1))

    return np.array(centers)


def k_means(X, k, init='k-means++', n_iter=300, 
                        thresh=1e-5, missing='warn'):
    """ K-means clustering algorithm.

    Parameters
    ----------
    data : ndarray
        A M by N array of M observations in N dimensions or a length
        M array of M one-dimensional observations.

    k : int or ndarray
        The number of clusters to form as well as the number of
        centroids to generate. If minit initialization string is
        'matrix', or if a ndarray is given instead, it is
        interpreted as initial cluster to use instead.

    n_iter : int
        Number of iterations of the k-means algrithm to run. Note
        that this differs in meaning from the iters parameter to
        the kmeans function.

    thresh : float
        (not used yet).

    init : {'k-means++', 'random', 'points', 'matrix'}
        Method for initialization, default to 'k-means++':

        'k-means++' : selects initial cluster centers for k-mean
        clustering in a smart way to speed up convergence. See section
        Notes in k_init for more details.

        'random': generate k centroids from a Gaussian with mean and
        variance estimated from the data.

        'points': choose k observations (rows) at random from data for
        the initial centroids.

        'matrix': interpret the k parameter as a k by M (or length k
        array for one-dimensional data) array of initial centroids.

    Returns
    -------
    centroid : ndarray
        A k by N array of centroids found at the last iteration of
        k-means.

    label : ndarray
        label[i] is the code or index of the centroid the
        i'th observation is closest to.

    Notes
    ------
    This is currently scipy.cluster.vq.kmeans2 with the
    additional 'k-means++' initialization.

    """
    if init == 'k-means++':
        k = k_init(X, k)
        init='points'
    return cluster.vq.kmeans2(X, k, minit=init, missing=missing,
                                iter=n_iter)


################################################################################

class KMeans(BaseEstimator):
    """ K-Means clustering

    Parameters
    ----------

    data : ndarray
        A M by N array of M observations in N dimensions or a length
        M array of M one-dimensional observations.

    k : int or ndarray
        The number of clusters to form as well as the number of
        centroids to generate. If init initialization string is
        'matrix', or if a ndarray is given instead, it is
        interpreted as initial cluster to use instead.

    n_iter : int
        Number of iterations of the k-means algrithm to run. Note
        that this differs in meaning from the iters parameter to
        the kmeans function.

    thresh : float
        (not used yet).

    init : {'k-means++', 'random', 'points', 'matrix'}
        Method for initialization, defaults to 'k-means++':

        'k-means++' : selects initial cluster centers for k-mean
        clustering in a smart way to speed up convergence. See section
        Notes in k_init for more details.

        'random': generate k centroids from a Gaussian with mean and
        variance estimated from the data.

        'points': choose k observations (rows) at random from data for
        the initial centroids.

        'matrix': interpret the k parameter as a k by M (or length k
        array for one-dimensional data) array of initial centroids.

    Methods
    -------

    fit(X):
        Compute K-Means clustering

    Attributes
    ----------

    cluster_centers_: array, [n_clusters, n_features]
        Coordinates of cluster centers

    labels_:
        Labels of each point

    Notes
    ------

    The k-means problem is solved using the Lloyd algorithm.

    The average complexity is given by O(k n T), were n is the number of 
    samples and T is the number of iteration.

    The worst case complexity is given by O(n^(k+2/p)) with 
    n = n_samples, p = n_features. (D. Arthur and S. Vassilvitskii, 
    'How slow is the k-means method?' SoCG2006)

    In practice, the K-means algorithm is very fast (on of the fastest
    clustering algorithms available), but it falls in local minimas, and 
    it can be useful to restarts it several times.
    """


    def __init__(self, k=8, init='k-means++', n_iter=300, missing='warn'):
        self.k = k
        self.init = init
        self.n_iter = n_iter
        self.missing = missing

    def fit(self, X, **params):
        """ Compute k-means"""
        X = np.asanyarray(X)
        self._set_params(**params)
        self.cluster_centers_, self.labels_ = k_means(X, 
                    k=self.k, init=self.init, missing=self.missing,
                    n_iter=self.n_iter)
        return self
 

""" Algorithms for clustering : Meanshift,  Affinity propagation and spectral 
clustering.

Author: Alexandre Gramfort alexandre.gramfort@inria.fr
        Gael Varoquaux gael.varoquaux@normalesup.org
"""

import numpy as np

from ..base import BaseEstimator


def affinity_propagation(S, p=None, convit=30, maxit=200, damping=0.5,
            copy=True):
    """Perform Affinity Propagation Clustering of data

    Parameters
    ----------

    S: array [n_points, n_points]
        Matrix of similarities between points
    p: array [n_points,] or float, optional
        Preferences for each point
    damping : float, optional
        Damping factor
    copy: boolean, optional
        If copy is False, the affinity matrix is modified inplace by the
        algorithm, for memory efficiency

    Returns
    -------

    cluster_centers_indices: array [n_clusters]
        index of clusters centers

    labels : array [n_points]
        cluster labels for each point

    Notes
    -----
    See examples/plot_affinity_propagation.py for an example.

    Reference:
    Brendan J. Frey and Delbert Dueck, "Clustering by Passing Messages
    Between Data Points", Science Feb. 2007

    """
    if copy:
        # Copy the affinity matrix to avoid modifying it inplace
        S = S.copy()

    n_points = S.shape[0]

    assert S.shape[0] == S.shape[1]

    if p is None:
        p = np.median(S)

    if damping < 0.5 or damping >= 1:
        raise ValueError('damping must be >= 0.5 and < 1')

    random_state = np.random.RandomState(0)

    # Place preferences on the diagonal of S
    S.flat[::(n_points+1)] = p

    A = np.zeros((n_points, n_points))
    R = np.zeros((n_points, n_points)) # Initialize messages

    # Remove degeneracies
    S += (  np.finfo(np.double).eps*S
          + np.finfo(np.double).tiny*100
         )*random_state.randn(n_points, n_points)

    # Execute parallel affinity propagation updates
    e = np.zeros((n_points, convit))

    ind = np.arange(n_points)

    for it in range(maxit):
        # Compute responsibilities
        Rold = R.copy()
        AS = A + S

        I = np.argmax(AS, axis=1)
        Y = AS[np.arange(n_points), I]#np.max(AS, axis=1)

        AS[ind, I[ind]] = - np.finfo(np.double).max

        Y2 = np.max(AS, axis=1)
        R = S - Y[:, np.newaxis]

        R[ind, I[ind]] = S[ind, I[ind]] - Y2[ind]

        R = (1-damping)*R + damping*Rold # Damping

        # Compute availabilities
        Aold = A
        Rp = np.maximum(R, 0)
        Rp.flat[::n_points+1] = R.flat[::n_points+1]

        A = np.sum(Rp, axis=0)[np.newaxis, :] - Rp

        dA = np.diag(A)
        A = np.minimum(A, 0)

        A.flat[::n_points+1] = dA

        A = (1-damping)*A + damping*Aold # Damping

        # Check for convergence
        E = (np.diag(A) + np.diag(R)) > 0
        e[:, it % convit] = E
        K = np.sum(E, axis=0)

        if it >= convit:
            se = np.sum(e, axis=1);
            unconverged = np.sum((se == convit) + (se == 0)) != n_points
            if (not unconverged and (K>0)) or (it==maxit):
                print "Converged after %d iterations." % it
                break
    else:
        print "Did not converged"

    I = np.where(np.diag(A+R) > 0)[0]
    K = I.size # Identify exemplars

    if K > 0:
        c = np.argmax(S[:, I], axis=1)
        c[I] = np.arange(K) # Identify clusters
        # Refine the final set of exemplars and clusters and return results
        for k in range(K):
            ii = np.where(c==k)[0]
            j = np.argmax(np.sum(S[ii, ii], axis=0))
            I[k] = ii[j]

        c = np.argmax(S[:, I], axis=1)
        c[I] = np.arange(K)
        labels = I[c]
        # Reduce labels to a sorted, gapless, list
        cluster_centers_indices = np.unique(labels)
        labels = np.searchsorted(cluster_centers_indices, labels)
    else:
        labels = np.empty((n_points, 1))
        cluster_centers_indices = None
        labels.fill(np.nan)

    return cluster_centers_indices, labels

################################################################################
class AffinityPropagation(BaseEstimator):
    """Perform Affinity Propagation Clustering of data

    Parameters
    ----------

    damping : float, optional
        Damping factor

    maxit : int, optional
        Maximum number of iterations

    convit : int, optional
        Number of iterations with no change in the number
        of estimated clusters that stops the convergence.

    copy: boolean, optional
        Make a copy of input data. True by default.

    Methods
    -------

    fit:
        Compute the clustering

    Attributes
    ----------

    cluster_centers_indices_ : array, [n_clusters]
        Indices of cluster centers

    labels_ : array, [n_samples]
        Labels of each point

    Notes
    -----
    See examples/plot_affinity_propagation.py for an example.

    Reference:

    Brendan J. Frey and Delbert Dueck, "Clustering by Passing Messages
    Between Data Points", Science Feb. 2007

    The algorithmic complexity of affinity propagation is quadratic
    in the number of points. 
    """

    def __init__(self, damping=.5, maxit=200, convit=30, copy=True):
        self.damping = damping
        self.maxit = maxit
        self.convit = convit
        self.copy = copy

    def fit(self, S, p=None, **params):
        """compute MeanShift

        Parameters
        ----------

        S: array [n_points, n_points]
            Matrix of similarities between points
        p: array [n_points,] or float, optional
            Preferences for each point
        damping : float, optional
            Damping factor
        copy: boolean, optional
            If copy is False, the affinity matrix is modified inplace by the
            algorithm, for memory efficiency

        """
        self._set_params(**params)
        self.cluster_centers_indices_, self.labels_ = affinity_propagation(S, p,
                maxit=self.maxit, convit=self.convit, damping=self.damping,
                copy=self.copy)
        return self


""" Algorithms for  spectral clustering.
"""

# Author: Gael Varoquaux gael.varoquaux@normalesup.org
# License: BSD
import warnings

import numpy as np

from scipy import sparse
from scipy.sparse.linalg.eigen.arpack import eigen_symmetric
from scipy.sparse.linalg import lobpcg
try:
    from pyamg import smoothed_aggregation_solver
    amg_loaded = True
except ImportError:
    amg_loaded = False 

from ..base import BaseEstimator
from ..utils.graph import graph_laplacian
from .k_means_ import k_means


def spectral_embedding(adjacency, k=8, mode=None):
    """ Spectral embedding: project the sample on the k first
        eigen vectors of the graph laplacian. 

        Parameters
        -----------
        adjacency: array-like or sparse matrix, shape: (p, p)
            The adjacency matrix of the graph to embed.
        k: integer, optional
            The dimension of the projection subspace.
        mode: {None, 'arpack' or 'amg'}
            The eigenvalue decomposition strategy to use. AMG (Algebraic
            MultiGrid) is much faster, but requires pyamg to be
            installed.

        Returns
        --------
        embedding: array, shape: (p, k)
            The reduced samples

        Notes
        ------
        The graph should contain only one connect component,
        elsewhere the results make little sens.
    """
    n_nodes = adjacency.shape[0]
    # XXX: Should we check that the matrices given is symmetric
    if mode == 'amg' and not amg_loaded:
        warnings.warn('pyamg not available, using scipy.sparse')
    if mode is None:
        mode = ('amg' if amg_loaded else 'arpack')
    laplacian, dd = graph_laplacian(adjacency,
                                    normed=True, return_diag=True)
    if (mode == 'arpack' 
        or not sparse.isspmatrix(laplacian)
        or n_nodes < 5*k # This is the threshold under which lobpcg has bugs 
       ):
        # We need to put the diagonal at zero
        if not sparse.isspmatrix(laplacian):
            laplacian[::n_nodes+1] = 0
        else:
            laplacian = laplacian.tocoo()
            diag_idx = (laplacian.row == laplacian.col)
            laplacian.data[diag_idx] = 0
            # If the matrix has a small number of diagonals (as in the
            # case of structured matrices comming from images), the
            # dia format might be best suited for matvec products:
            n_diags = np.unique(laplacian.row - laplacian.col).size
            if n_diags <= 7:
                # 3 or less outer diagonals on each side
                laplacian = laplacian.todia()
            else:
                # csr has the fastest matvec and is thus best suited to
                # arpack
                laplacian = laplacian.tocsr()
        lambdas, diffusion_map = eigen_symmetric(-laplacian, k=k, which='LA')
        embedding = diffusion_map.T[::-1]*dd
    elif mode == 'amg':
        # Use AMG to get a preconditionner and speed up the eigenvalue
        # problem.
        laplacian = laplacian.astype(np.float) # lobpcg needs the native float
        ml = smoothed_aggregation_solver(laplacian.tocsr())
        X = np.random.rand(laplacian.shape[0], k)
        X[:, 0] = 1. / dd.ravel()
        M = ml.aspreconditioner()
        lambdas, diffusion_map = lobpcg(laplacian, X, M=M, tol=1.e-12, 
                                        largest=False)
        embedding = diffusion_map.T * dd
        if embedding.shape[0] == 1: raise ValueError
    else:
        raise ValueError("Unknown value for mode: '%s'." % mode)
    return embedding


def spectral_clustering(adjacency, k=8, mode=None):
    """ Spectral clustering: apply k-means to a projection of the 
        graph laplacian, finds normalized graph cuts.

        Parameters
        -----------
        adjacency: array-like or sparse matrix, shape: (p, p)
            The adjacency matrix of the graph to embed.
        k: integer, optional
            The dimension of the projection subspace.
        mode: {None, 'arpack' or 'amg'}
            The eigenvalue decomposition strategy to use. AMG (Algebraic
            MultiGrid) is much faster, but requires pyamg to be
            installed.

        Returns
        --------
        labels: array of integers, shape: p
            The labels of the clusters.
        centers: array of integers, shape: k
            The indices of the cluster centers

        Notes
        ------
        The graph should contain only one connect component,
        elsewhere the results make little sens.
    """
    maps = spectral_embedding(adjacency, k=k, mode=mode)
    maps = maps[1:]
    _, labels = k_means(maps.T, k)
    return labels


################################################################################
class SpectralClustering(BaseEstimator):
    """ Spectral clustering: apply k-means to a projection of the 
        graph laplacian, finds normalized graph cuts.

        Parameters
        -----------
        k: integer, optional
            The dimension of the projection subspace.
        mode: {None, 'arpack' or 'amg'}
            The eigenvalue decomposition strategy to use. AMG (Algebraic
            MultiGrid) is much faster, but requires pyamg to be
            installed.

        Methods
        -------

        fit(X):
            Compute spectral clustering 

        Attributes
        ----------

        labels_:
            Labels of each point

    """


    def __init__(self, k=8, mode=None):
        self.k = k
        self.mode = mode

    
    def fit(self, X, **params):
        """ Compute the spectral clustering from the adjacency matrix of
            the graph.
        
            Parameters
            -----------
            X: array-like or sparse matrix, shape: (p, p)
                The adjacency matrix of the graph to embed.

            Notes
            ------
            If the pyamg package is installed, it is used. This
            greatly speeds up computation.
        """
        self._set_params(**params)
        self.labels_ = spectral_clustering(X, 
                                k=self.k, mode=self.mode)
        return self



"""
Common utilities for testing clustering.

"""

import numpy as np

################################################################################
# Generate sample data
################################################################################

def generate_clustered_data(seed=0, n_clusters=3, n_features=2,
                            n_samples_per_cluster=20, std=.4):
    prng = np.random.RandomState(seed)

    means = np.array([[ 1,  1, 1, 0], 
                      [-1, -1, 0, 1], 
                      [ 1, -1, 1, 1],
                      [ -1, 1, 1, 0],
                    ])

    X = np.empty((0, n_features))
    for i in range(n_clusters):
        X = np.r_[X, means[i][:n_features] 
                    + std*prng.randn(n_samples_per_cluster, n_features)]
    return X


# srn.py
# by: Fred Mailhot
# last mod: 2006-08-18

import numpy as N
from scipy.optimize import leastsq

class srn:
    """Class to define, train and test a simple recurrent network
    """

    _type = 'srn'
    _outfxns = ('linear','logistic','softmax')

    def __init__(self,ni,nh,no,f='linear',w=None):
        """ Set up instance of srn. Initial weights are drawn from a 
        zero-mean Gaussian w/ variance is scaled by fan-in.
        Input:
            ni  - <int> # of inputs
            nh  - <int> # of hidden & context units
            no  - <int> # of outputs
            f   - <str> output activation fxn
            w   - <array dtype=Float> weight vector
        """
        if f not in self._outfxns:
            print "Undefined activation fxn. Using linear"
            self.outfxn = 'linear'
        else:
            self.outfxn = f
        self.ni = ni
        self.nh = nh
        self.nc = nh
        self.no = no
        if w:
            self.nw = N.size(w)
            self.wp = w
            self.w1 = N.zeros((ni,nh),dtype=Float)    # input-hidden wts
            self.b1 = N.zeros((1,nh),dtype=Float)     # input biases
            self.wc = N.zeros((nh,nh),dtype=Float)    # context wts
            self.w2 = N.zeros((nh,no),dtype=Float)    # hidden-output wts
            self.b2 = N.zeros((1,no),dtype=Float)     # hidden biases
            self.unpack()
        else:
            # N.B. I just understood something about the way reshape() works
            # that should simplify things, allowing me to just make changes
            # to the packed weight vector, and using "views" for the fwd
            # propagation.
            # I'll implement this next week.
            self.nw = (ni+1)*nh + (nh*nh) + (nh+1)*no
            self.w1 = N.random.randn(ni,nh)/N.sqrt(ni+1)
            self.b1 = N.random.randn(1,nh)/N.sqrt(ni+1)
            self.wc = N.random.randn(nh,nh)/N.sqrt(nh+1)
            self.w2 = N.random.randn(nh,no)/N.sqrt(nh+1)
            self.b2 = N.random.randn(1,no)/N.sqrt(nh+1)
            self.pack()

    def unpack(self):
        """ Decompose 1-d vector of weights w into appropriate weight 
        matrices (w1,b1,w2,b2) and reinsert them into net
        """
        self.w1 = N.array(self.wp)[:self.ni*self.nh].reshape(self.ni,self.nh)
        self.b1 = N.array(self.wp)[(self.ni*self.nh):(self.ni*self.nh)+self.nh].reshape(1,self.nh)
        self.wc = N.array(self.wp)[(self.ni*self.nh)+self.nh:(self.ni*self.nh)+self.nh+(self.nh*self.nh)].reshape(self.nh,self.nh)
        self.w2 = N.array(self.wp)[(self.ni*self.nh)+self.nh+(self.nh*self.nh):(self.ni*self.nh)+self.nh+(self.nh*self.nh)+(self.nh*self.no)].reshape(self.nh,self.no)
        self.b2 = N.array(self.wp)[(self.ni*self.nh)+self.nh+(self.nh*self.nh)+(self.nh*self.no):].reshape(1,self.no)

    def pack(self):
        """ Compile weight matrices w1,b1,wc,w2,b2 from net into a
        single vector, suitable for optimization routines.
        """
        self.wp = N.hstack([self.w1.reshape(N.size(self.w1)),
                            self.b1.reshape(N.size(self.b1)),
                            self.wc.reshape(N.size(self.wc)),
                            self.w2.reshape(N.size(self.w2)),
                            self.b2.reshape(N.size(self.b2))])

    def fwd_all(self,x,w=None):
        """ Propagate values forward through the net. 
        Input:
            x   - matrix of all input patterns
            w   - 1-d vector of weights
        Returns:
            y   - matrix of all outputs
        """
        if w is not None:
            self.wp = w
        self.unpack()
        
        ### NEW ATTEMPT ###
        z = N.array(N.ones(self.nh)*0.5)    # init to 0.5, it will be updated on-the-fly
        o = N.zeros((x.shape[0],self.no))   # this will hold the non-squashed outputs
        for i in range(len(x)):
            z = N.tanh(N.dot(x[i],self.w1) + N.dot(z,self.wc) + self.b1)
            o[i] = (N.dot(z,self.w2) + self.b2)[0]
            
        # compute vector of context values for current weight matrix
        #c = N.tanh(N.dot(x,self.w1) + N.dot(N.ones((len(x),1)),self.b1))
        #c = N.vstack([c[1:],c[0]])
        # compute vector of hidden unit values
        #z = N.tanh(N.dot(x,self.w1) + N.dot(c,self.wc) + N.dot(N.ones((len(x),1)),self.b1))
        # compute vector of net outputs
        #o = N.dot(z,self.w2) + N.dot(N.ones((len(z),1)),self.b2)
        
        # compute final output activations
        if self.outfxn == 'linear':
            y = o
        elif self.outfxn == 'logistic':     # TODO: check for overflow here...
            y = 1/(1+N.exp(-o))
        elif self.outfxn == 'softmax':      # TODO: and here...
            tmp = N.exp(o)
            y = tmp/(N.sum(temp,1)*N.ones((1,self.no)))
            
        return y
        
    def errfxn(self,w,x,t):
        """ Return vector of squared-errors for the leastsq optimizer
        """
        y = self.fwd_all(x,w)
        return N.sum(N.array(y-t)**2,axis=1)

    def train(self,x,t):
        """ Train a multilayer perceptron using scipy's leastsq optimizer
        Input:
            x   - matrix of input data
            t   - matrix of target outputs
        Returns:
            post-optimization weight vector
        """
        return leastsq(self.errfxn,self.wp,args=(x,t))

    def test_all(self,x,t):
        """ Test network on an array (size>1) of patterns
        Input:
            x   - array of input data
            t   - array of targets
        Returns:
            sum-squared-error over all data
        """
        return N.sum(self.errfxn(self.wp,x,t),axis=0)
                                                                                    
    
def main():
    """ Set up a 1-2-1 SRN to solve the temporal-XOR problem from Elman 1990.
    """
    from scipy.io import read_array, write_array
    print "\nCreating 1-2-1 SRN for 'temporal-XOR'"
    net = srn(1,2,1,'logistic')
    print "\nLoading training and test sets...",
    trn_input = read_array('data/txor-trn.dat')
    trn_targs = N.hstack([trn_input[1:],trn_input[0]])
    trn_input = trn_input.reshape(N.size(trn_input),1)
    trn_targs = trn_targs.reshape(N.size(trn_targs),1)
    tst_input = read_array('data/txor-tst.dat')
    tst_targs = N.hstack([tst_input[1:],tst_input[0]])
    tst_input = tst_input.reshape(N.size(tst_input),1)
    tst_targs = tst_targs.reshape(N.size(tst_targs),1)
    print "done."
    print "\nInitial SSE:\n"
    print "\ttraining set: ",net.test_all(trn_input,trn_targs)
    print "\ttesting set: ",net.test_all(tst_input,tst_targs),"\n"
    net.wp = net.train(trn_input,trn_targs)[0]
    print "\nFinal SSE:\n"
    print "\ttraining set: ",net.test_all(trn_input,trn_targs)
    print "\ttesting set: ",net.test_all(tst_input,tst_targs),"\n"
    
if __name__ == '__main__':
    main()


# req'd file for SciPy package (see DEVELOPERS.txt)
# Fred Mailhot
# 2006-06-13

"""
An artificial neural network module for scipy, adding standard feedforward architectures
(MLP and RBF), as well as some recurrent architectures (e.g. SRN).

Each of {mlp,srn,rbf}.py contains a class to define, train and test a network,
along with a main() functions that demos on a toy dataset.
"""


# mlp.py
# by: Fred Mailhot
# last mod: 2006-08-19

import numpy as N
from scipy.optimize import leastsq

class mlp:
    """Class to define, train and test a multilayer perceptron.
    """

    _type = 'mlp'
    _outfxns = ('linear','logistic','softmax')

    def __init__(self,ni,nh,no,f='linear',w=None):
        """ Set up instance of mlp. Initial weights are drawn from a 
        zero-mean Gaussian w/ variance is scaled by fan-in.
        Input:
            ni  - <int> # of inputs
            nh  - <int> # of hidden units
            no  - <int> # of outputs
            f   - <str> output activation fxn
            w   - <array of float> vector of initial weights
        """
        if f not in self._outfxns:
            print "Undefined activation fxn. Using linear"
            self.outfxn = 'linear'
        else:
            self.outfxn = f
        self.ni = ni
        self.nh = nh
        self.no = no
        #self.alg = alg
        if w:
            self.nw = N.size(w)
            self.wp = w
            self.w1 = N.zeros((ni,nh),dtype=Float)
            self.b1 = N.zeros((1,nh),dtype=Float)
            self.w2 = N.zeros((nh,no),dtype=Float)
            self.b2 = N.zeros((1,no),dtype=Float)
            self.unpack()
        else:
            self.nw = (ni+1)*nh + (nh+1)*no
            self.w1 = N.random.randn(ni,nh)/N.sqrt(ni+1)
            self.b1 = N.random.randn(1,nh)/N.sqrt(ni+1)
            self.w2 = N.random.randn(nh,no)/N.sqrt(nh+1)
            self.b2 = N.random.randn(1,no)/N.sqrt(nh+1)
            self.pack()

    def unpack(self):
        """ Decompose 1-d vector of weights w into appropriate weight 
        matrices (w1,b1,w2,b2) and reinsert them into net
        """
        self.w1 = N.array(self.wp)[:self.ni*self.nh].reshape(self.ni,self.nh)
        self.b1 = N.array(self.wp)[(self.ni*self.nh):(self.ni*self.nh)+self.nh].reshape(1,self.nh)
        self.w2 = N.array(self.wp)[(self.ni*self.nh)+self.nh:(self.ni*self.nh)+self.nh+(self.nh*self.no)].reshape(self.nh,self.no)
        self.b2 = N.array(self.wp)[(self.ni*self.nh)+self.nh+(self.nh*self.no):].reshape(1,self.no)

    def pack(self):
        """ Compile weight matrices w1,b1,w2,b2 from net into a
        single vector, suitable for optimization routines.
        """
        self.wp = N.hstack([self.w1.reshape(N.size(self.w1)),
                            self.b1.reshape(N.size(self.b1)),
                            self.w2.reshape(N.size(self.w2)),
                            self.b2.reshape(N.size(self.b2))])

    def fwd_all(self,x,w=None):
        """ Propagate values forward through the net. 
        Input:
            x   - array (size>1) of input patterns
            w   - optional 1-d vector of weights 
        Returns:
            y   - array of outputs for all input patterns
        """
        if w is not None:
            self.wp = w
        self.unpack()
        # compute vector of hidden unit values
        z = N.tanh(N.dot(x,self.w1) + N.dot(N.ones((len(x),1)),self.b1))
        # compute vector of net outputs
        o = N.dot(z,self.w2) + N.dot(N.ones((len(z),1)),self.b2)
        # compute final output activations
        if self.outfxn == 'linear':
            y = o
        elif self.outfxn == 'logistic':     # TODO: check for overflow here...
            y = 1/(1+N.exp(-o))
        elif self.outfxn == 'softmax':      # TODO: and here...
            tmp = N.exp(o)
            y = tmp/(N.sum(temp,1)*N.ones((1,self.no)))
            
        return N.array(y)

    def errfxn(self,w,x,t):
        """ Return vector of squared-errors for the leastsq optimizer
        """
        y = self.fwd_all(x,w)
        return N.sum(N.array(y-t)**2,axis=1)

    def train(self,x,t):
        """ Train network using scipy's leastsq optimizer
        Input:
            x   - array of input data 
            t   - array of targets
            
            N.B. x and t comprise the *entire* collection of training data
            
        Returns:
            post-optimization weight vector
        """
        return leastsq(self.errfxn,self.wp,args=(x,t))

    def test_all(self,x,t):
        """ Test network on an array (size>1) of patterns
        Input:
            x   - array of input data
            t   - array of targets
        Returns:
            sum-squared-error over all data
        """
        return N.sum(self.errfxn(self.wp,x,t),axis=0)

def main():
    """ Build/train/test MLP 
    """
    from scipy.io import read_array, write_array
    print "\nCreating 2-2-1 MLP with logistic outputs"
    net = mlp(2,2,1,'logistic')
    print "\nLoading training and test sets...",
    trn_input = read_array('data/xor-trn.dat',lines=(3,-1),columns=(0,(1,2)))
    trn_targs = read_array('data/xor-trn.dat',lines=(3,-1),columns=(2,-1))
    trn_targs = trn_targs.reshape(N.size(trn_targs),1)
    tst_input = read_array('data/xor-tst.dat',lines=(3,-1),columns=(0,(1,2)))
    tst_targs = read_array('data/xor-tst.dat',lines=(3,-1),columns=(2,-1))
    tst_targs = tst_targs.reshape(N.size(tst_targs),1)
    print "done."
    print "\nInitial SSE:\n"
    print "\ttraining set: ",net.test_all(trn_input,trn_targs)
    print "\ttesting set: ",net.test_all(tst_input,tst_targs),"\n"
    net.wp = net.train(trn_input,trn_targs)[0]
    print "\nFinal SSE:\n"
    print "\ttraining set: ",net.test_all(trn_input,trn_targs)
    print "\ttesting set: ",net.test_all(tst_input,tst_targs),"\n"
        
if __name__ == '__main__':
    main()


# rbf2.py
# tilde
# 2006/08/20

import numpy as N
import random
from scipy.optimize import leastsq

class rbf:
    """Class to define/train/test a radial basis function network
    """

    _type = 'rbf'
    _outfxns = ('linear','logistic','softmax')


    def __init__(self,ni,no,f='linear'):
        """ Set up instance of RBF net. N.B. RBF centers and variance are selected at training time 
        Input:
            ni  - <int> # of inputs
            no  - <int> # of outputs
            f   - <str> output activation fxn
        """
        
        self.ni = ni
        self.no = no
        self.outfxn = f

    def unpack(self):
        """ Decompose 1-d vector of weights w into appropriate weight
        matrices (self.{w/b}) and reinsert them into net
        """
        self.w = N.array(self.wp)[:self.centers.shape[0]*self.no].reshape(self.centers.shape[0],self.no)
        self.b = N.array(self.wp)[(self.centers.shape[0]*self.no):].reshape(1,self.no)

    def pack(self):
        """ Compile weight matrices w,b from net into a
        single vector, suitable for optimization routines.
        """
        self.wp = N.hstack([self.w.reshape(N.size(self.w)),
                            self.b.reshape(N.size(self.b))])

    def fwd_all(self,X,w=None):
        """ Propagate values forward through the net.
        Inputs:
                inputs      - vector of input values
                w           - packed array of weights
        Returns:
                array of outputs for all input patterns
        """
        if w is not None:
            self.wp = w
        self.unpack()
        # compute hidden unit values
        z = N.zeros((len(X),self.centers.shape[0]))
        for i in range(len(X)):
             z[i] = N.exp((-1.0/(2*self.variance))*(N.sum((X[i]-self.centers)**2,axis=1)))
        # compute net outputs
        o = N.dot(z,self.w) + N.dot(N.ones((len(z),1)),self.b)
        # compute final output activations
        if self.outfxn == 'linear':
            y = o
        elif self.outfxn == 'logistic':     # TODO: check for overflow here...
            y = 1/(1+N.exp(-o))
        elif self.outfxn == 'softmax':      # TODO: and here...
            tmp = N.exp(o)
            y = tmp/(N.sum(temp,1)*N.ones((1,self.no)))

        return N.array(y)


    def err_fxn(self,w,X,Y):
        """ Return vector of squared-errors for the leastsq optimizer
        """
        O = self.fwd_all(X,w)
        return N.sum(N.array(O-Y)**2,axis=1)

    def train(self,X,Y):
        """ Train RBF network:
            (i) select fixed centers randomly from input data (10%)
            (ii) set fixed variance from max dist between centers
            (iii) learn output weights using scipy's leastsq optimizer
        """
        # set centers & variance
        self.centers = N.array(random.sample(X,len(X)/10))
        d_max = 0.0
        for i in self.centers:
            for j in self.centers:
                tmp = N.sum(N.sqrt((i-j)**2),axis=0)
                if tmp > d_max:
                    d_max = tmp
        self.variance = d_max/(2.0*len(X))
        # train weights
        self.nw = self.centers.shape[0]*self.no
        self.w = N.random.randn(self.centers.shape[0],self.no)/N.sqrt(self.centers.shape[0]+1)
        self.b = N.random.randn(1,self.no)/N.sqrt(self.centers.shape[0]+1)
        self.pack()
        self.wp = leastsq(self.err_fxn,self.wp,args=(X,Y))[0]

    def test_all(self,X,Y):
        """ Test network on an array (size>1) of patterns
        Input:
            x   - array of input data
            t   - array of targets
        Returns:
            sum-squared-error over all data
        """
        return N.sum(self.err_fxn(self.wp,X,Y),axis=0)

def main():
    """ Build/train/test RBF net
    """
    from scipy.io import read_array
    print "\nCreating RBF net"
    net = rbf(12,2)
    print "\nLoading training and test sets...",
    X_trn = read_array('data/oil-trn.dat',columns=(0,(1,12)),lines=(3,-1))
    Y_trn = read_array('data/oil-trn.dat',columns=(12,-1),lines=(3,-1))
    X_tst = read_array('data/oil-tst.dat',columns=(0,(1,12)),lines=(3,-1))
    Y_tst = read_array('data/oil-tst.dat',columns=(12,-1),lines=(3,-1))
    print "done."
    #print "\nInitial SSE:\n"
    #print "\ttraining set: ",net.test_all(X_trn,Y_trn)
    #print "\ttesting set: ",net.test_all(X_tst,Y_tst),"\n"
    print "Training...",
    net.train(X_trn,Y_trn)
    print "done."
    print "\nFinal SSE:\n"
    print "\ttraining set: ",net.test_all(X_trn,Y_trn)
    print "\ttesting set: ",net.test_all(X_tst,Y_tst),"\n"


if __name__ == '__main__':
    main()

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('ann', parent_package, top_path )

    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup( **configuration( top_path = '' ).todict() )

import numpy as np
import numpy.random as nr


"""
Samples generator

"""

# Author: B. Thirion, G. Varoquaux, A. Gramfort, V. Michel
# License: BSD 3 clause


def samples_classif():
    pass

######################################################################
# Generate Dataset for test
######################################################################

def test_dataset_classif(n_samples=100, n_features=100, param=[1,1],
                             k=0, seed=None):
    """
    Generate an snp matrix

    Parameters
    ----------
    n_samples : 100, int,
        the number of subjects
    n_features : 100, int,
        the number of features
    param : [1,1], list,
        parameter of a dirichlet density
        that is used to generate multinomial densities
        from which the n_featuress will be samples
    k : 0, int,
        number of informative features
    seed : None, int or np.random.RandomState
        if seed is an instance of np.random.RandomState,
        it is used to initialize the random generator

    Returns
    -------
    x : array of shape(n_samples, n_features),
        the design matrix
    y : array of shape (n_samples),
        the subject labels

    """
    assert k<=n_features, ValueError('cannot have %d informative features and'
                                   ' %d features' % (k, n_features))
    if isinstance(seed, np.random.RandomState):
        random = seed
    elif seed is not None:
        random = np.random.RandomState(seed)
    else:
        random = np.random

    x = random.randn(n_samples, n_features)
    y = np.zeros(n_samples)
    param = np.ravel(np.array(param)).astype(np.float)
    for n in range(n_samples):
        y[n] = np.nonzero(random.multinomial(1, param/param.sum()))[0]
    x[:,:k] += 3*y[:,np.newaxis]
    return x, y

def test_dataset_reg(n_samples=100, n_features=100, k=0, seed=None):
    """
    Generate an snp matrix

    Parameters
    ----------
    n_samples : 100, int,
        the number of subjects
    n_features : 100, int,
        the number of features
    k : 0, int,
        number of informative features
    seed : None, int or np.random.RandomState
        if seed is an instance of np.random.RandomState,
        it is used to initialize the random generator

    Returns
    -------
    x : array of shape(n_samples, n_features),
        the design matrix
    y : array of shape (n_samples),
        the subject data

    """
    assert k<n_features, ValueError('cannot have %d informative fetaures and'
                                   ' %d features' % (k, n_features))
    if isinstance(seed, np.random.RandomState):
        random = seed
    elif seed is not None:
        random = np.random.RandomState(seed)
    else:
        random = np.random

    x = random.randn(n_samples, n_features)
    y = random.randn(n_samples)
    x[:,:k] += y[:, np.newaxis]
    return x, y





######################################################################
# Generate Dataset for regression
######################################################################


def sparse_uncorrelated(nb_samples=100, nb_features=10):
    """
    Function creating simulated data with sparse uncorrelated design.
    (cf.Celeux et al. 2009,  Bayesian regularization in regression)
    X = NR.normal(0,1)
    Y = NR.normal(X[:,0]+2*X[:,1]-2*X[:,2]-1.5*X[:,3])
    The number of features is at least 10.

    Parameters
    ----------
    nb_samples : int
                 number of samples (defaut is 100).
    nb_features : int
                  number of features (defaut is 5).

    Returns
    -------
    X : numpy array of shape (nb_samples, nb_features) for input samples
    Y : numpy array of shape (nb_samples) for labels
    """
    X = nr.normal(loc=0, scale=1, size=(nb_samples, nb_features))
    Y = nr.normal(loc=X[:, 0] + 2 * X[:, 1] - 2 * X[:,2] - 1.5 * X[:, 3],
                  scale = np.ones(nb_samples))
    return X, Y


def friedman(nb_samples=100, nb_features=10,noise_std=1):
    """
    Function creating simulated data with non linearities 
    (cf.Friedman 1993)
    X = NR.normal(0,1)
    Y = 10*sin(X[:,0]*X[:,1]) + 20*(X[:,2]-0.5)**2 + 10*X[:,3] + 5*X[:,4]
    The number of features is at least 5.

    Parameters
    ----------
    nb_samples : int
                 number of samples (defaut is 100).
    nb_features : int
                  number of features (defaut is 10).
    noise_std : float
		std of the noise, which is added as noise_std*NR.normal(0,1)
    Returns
    -------
    X : numpy array of shape (nb_samples, nb_features) for input samples
    Y : numpy array of shape (nb_samples) for labels

    """
    X = nr.normal(loc=0, scale=1, size=(nb_samples, nb_features))
    Y = 10*np.sin(X[:,0]*X[:,1]) + 20*(X[:,2]-0.5)**2 + 10*X[:,3] + 5*X[:,4]
    Y += noise_std*nr.normal(loc=0,scale=1,size=(nb_samples))
    return X,Y

# Copyright (c) 2010 Olivier Grisel <olivier.grisel@ensta.org>
# License: Simplified BSD
"""Glue code to load http://mlcomp.org data as a scikit.learn dataset"""

import os
import numpy as np
from scikits.learn.datasets.base import Bunch
from scikits.learn.features.text import HashingVectorizer
from scikits.learn.features.text import SparseHashingVectorizer


def _load_document_classification(dataset_path, metadata, set_, sparse, **kw):
    """Loader implementation for the DocumentClassification format"""
    target = []
    target_names = {}
    filenames = []
    vectorizer = kw.get('vectorizer')
    if vectorizer is None:
        if sparse:
            vectorizer = SparseHashingVectorizer()
        else:
            vectorizer = HashingVectorizer()

    # TODO: make it possible to plug a several pass system to filter-out tokens
    # that occur in more than 30% of the documents for instance.

    # TODO: use joblib.Parallel or multiprocessing to parallelize the following
    # (provided this is not IO bound)

    dataset_path = os.path.join(dataset_path, set_)
    folders = [f for f in sorted(os.listdir(dataset_path))
               if os.path.isdir(os.path.join(dataset_path, f))]
    for label, folder in enumerate(folders):
        target_names[label] = folder
        folder_path = os.path.join(dataset_path, folder)
        documents = [os.path.join(folder_path, d)
                     for d in sorted(os.listdir(folder_path))]
        vectorizer.vectorize_files(documents)
        target.extend(len(documents) * [label])
        filenames.extend(documents)

    return Bunch(data=vectorizer.get_vectors(), target=np.array(target),
                 target_names=target_names, filenames=filenames,
                 DESCR=metadata.get('description'))


LOADERS = {
    'DocumentClassification': _load_document_classification,
    # TODO: implement the remaining domain formats
}


def load_mlcomp(name_or_id, set_="raw", mlcomp_root=None, sparse=False,
                **kwargs):
    """Load a datasets as downloaded from http://mlcomp.org

    Parameters
    ----------

    name_or_id : the integer id or the string name metadata of the MLComp
                 dataset to load

    set_ : select the portion to load: 'train', 'test' or 'raw'

    mlcomp_root : the filesystem path to the root folder where MLComp datasets
                  are stored, if mlcomp_root is None, the MLCOMP_DATASETS_HOME
                  environment variable is looked up instead.

    sparse : boolean if True then use a scipy.sparse matrix for the data field,
             False by default

    **kwargs : domain specific kwargs to be passed to the dataset loader.

    Returns
    -------

    data : Bunch
        Dictionnary-like object, the interesting attributes are:
        'data', the data to learn, 'target', the classification labels,
        'target_names', the meaning of the labels, and 'DESCR', the
        full description of the dataset.

    Note on the lookup process: depending on the type of name_or_id,
    will choose between integer id lookup or metadata name lookup by
    looking at the unzipped archives and metadata file.

    TODO: implement zip dataset loading too
    """

    if mlcomp_root is None:
        try:
            mlcomp_root = os.environ['MLCOMP_DATASETS_HOME']
        except KeyError:
            raise ValueError("MLCOMP_DATASETS_HOME env variable is undefined")

    mlcomp_root = os.path.expanduser(mlcomp_root)
    mlcomp_root = os.path.abspath(mlcomp_root)
    mlcomp_root = os.path.normpath(mlcomp_root)

    if not os.path.exists(mlcomp_root):
        raise ValueError("Could not find folder: " + mlcomp_root)

    # dataset lookup
    if isinstance(name_or_id, int):
        # id lookup
        dataset_path = os.path.join(mlcomp_root, str(name_or_id))
    else:
        # assume name based lookup
        dataset_path = None
        expected_name_line = "name: " + name_or_id
        for dataset in os.listdir(mlcomp_root):
            metadata_file = os.path.join(mlcomp_root, dataset, 'metadata')
            if not os.path.exists(metadata_file):
                continue
            for line in file(metadata_file):
                if line.strip() == expected_name_line:
                    dataset_path = os.path.join(mlcomp_root, dataset)
                    break
        if dataset_path is None:
            raise ValueError("Could not find dataset with metadata line: " +
                             expected_name_line)

    # loading the dataset metadata
    metadata = dict()
    metadata_file = os.path.join(dataset_path, 'metadata')
    if not os.path.exists(metadata_file):
        raise ValueError(dataset_path + ' is not a valid MLComp dataset')
    for line in file(metadata_file):
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

    format = metadata.get('format', 'unknow')
    loader = LOADERS.get(format)
    if loader is None:
        raise ValueError("No loader implemented for format: " + format)
    return loader(dataset_path, metadata, set_=set_, sparse=sparse, **kwargs)



from base import load_iris, load_digits, load_diabetes
from mlcomp import load_mlcomp


#!/usr/bin/env python

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('datasets',parent_package,top_path)
    config.add_data_dir('data')
    config.add_data_dir('descr')
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())

"""
Base IO code for all datasets
"""

# Copyright (c) 2007 David Cournapeau <cournape@gmail.com>
#               2010 Fabian Pedregosa <fabian.pedregosa@inria.fr>
# License: Simplified BSD

import csv
import os

import numpy as np


class Bunch(dict):
    """ Container object for datasets: dictionnary-like object that
        exposes its keys as attributes.
    """

    def __init__(self, **kwargs):
        dict.__init__(self, kwargs)
        self.__dict__ = self


################################################################################

def load_iris():
    """load the iris dataset and returns it.
    
    Returns
    -------
    data : Bunch
        Dictionnary-like object, the interesting attributes are:
        'data', the data to learn, 'target', the classification labels, 
        'target_names', the meaning of the labels, and 'DESCR', the
        full description of the dataset.

    Example
    -------
    Let's say you are interested in the samples 10, 25, and 50, and want to
    know their class name.

    >>> data = load_iris()
    >>> print data.target[[10, 25, 50]]
    [0 0 1]
    >>> print data.target_names
    ['setosa' 'versicolor' 'virginica']
    """
    
    data_file = csv.reader(open(os.path.dirname(__file__) 
                        + '/data/iris.csv'))
    fdescr = open(os.path.dirname(__file__) 
                        + '/descr/iris.rst')
    temp = data_file.next()
    n_samples = int(temp[0])
    n_features = int(temp[1])
    target_names = np.array(temp[2:])
    data = np.empty((n_samples, n_features))
    target = np.empty((n_samples,), dtype=np.int)
    for i, ir in enumerate(data_file):
        data[i] = np.asanyarray(ir[:-1], dtype=np.float)
        target[i] = np.asanyarray(ir[-1], dtype=np.int)
    return Bunch(data=data, target=target, target_names=target_names, 
                 DESCR=fdescr.read())


def load_digits():
    """load the digits dataset and returns it.
    
    Returns
    -------
    data : Bunch
        Dictionnary-like object, the interesting attributes are:
        'data', the data to learn, `images`, the images corresponding
        to each sample, 'target', the classification labels for each
        sample, 'target_names', the meaning of the labels, and 'DESCR', 
        the full description of the dataset.

    Example
    -------
    To load the data and visualize the images::

        import pylab as pl
        digits = datasets.load_digits()
        pl.gray()
        # Visualize the first image:
        pl.matshow(digits.raw_data[0])

    """
    
    data = np.loadtxt(os.path.join(os.path.dirname(__file__) 
                        + '/data/digits.csv.gz'), delimiter=',')
    fdescr = open(os.path.join(os.path.dirname(__file__) 
                        + '/descr/digits.rst'))
    target = data[:, -1]
    flat_data = data[:, :-1]
    images = flat_data.view()
    images.shape = (-1, 8, 8)
    return Bunch(data=flat_data, target=target.astype(np.int), 
                 target_names=np.arange(10), 
                 images=images,
                 DESCR=fdescr.read())



def load_diabetes():
    data = np.loadtxt(os.path.join(os.path.dirname(__file__) +
                                   '/data/diabetes.csv'))
    target = data[:, -1]
    data   = data[:, :-1]
    return Bunch (data=data, target=target)


"""
External, bundled dependencies.

"""


# -*- coding: utf-8 -*-

def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('externals',parent_package,top_path)
    config.add_subpackage('joblib')
    config.add_subpackage('joblib/test')

    return config


"""
Represent an exception with a lot of information.

Provides 2 useful functions:

format_exc: format an exception into a complete traceback, with full
            debugging instruction.

format_outer_frames: format the current position in the stack call.

Adapted from IPython's VerboseTB.
"""
# Authors: Gael Varoquaux < gael dot varoquaux at normalesup dot org >
#          Nathaniel Gray <n8gray@caltech.edu>
#          Fernando Perez <fperez@colorado.edu>
# Copyright: 2010, Gael Varoquaux
#            2001-2004, Fernando Perez
#            2001 Nathaniel Gray
# License: BSD 3 clause


import inspect
import keyword
import linecache
import os
import pydoc
import string
import sys
import time
import tokenize
import traceback
import types

INDENT        = ' '*8

################################################################################
# some internal-use functions
def safe_repr(value):
    """Hopefully pretty robust repr equivalent."""
    # this is pretty horrible but should always return *something*
    try:
        return pydoc.text.repr(value)
    except KeyboardInterrupt:
        raise
    except:
        try:
            return repr(value)
        except KeyboardInterrupt:
            raise
        except:
            try:
                # all still in an except block so we catch
                # getattr raising
                name = getattr(value, '__name__', None)
                if name:
                    # ick, recursion
                    return safe_repr(name)
                klass = getattr(value, '__class__', None)
                if klass:
                    return '%s instance' % safe_repr(klass)
            except KeyboardInterrupt:
                raise
            except:
                return 'UNRECOVERABLE REPR FAILURE'

def eq_repr(value, repr=safe_repr): 
    return '=%s' % repr(value)


################################################################################
def uniq_stable(elems):
    """uniq_stable(elems) -> list

    Return from an iterable, a list of all the unique elements in the input,
    but maintaining the order in which they first appear.

    A naive solution to this problem which just makes a dictionary with the
    elements as keys fails to respect the stability condition, since
    dictionaries are unsorted by nature.

    Note: All elements in the input must be hashable.
    """
    unique = []
    unique_set = set()
    for nn in elems:
        if nn not in unique_set:
            unique.append(nn)
            unique_set.add(nn)
    return unique


################################################################################
def fix_frame_records_filenames(records):
    """Try to fix the filenames in each record from inspect.getinnerframes().
    
    Particularly, modules loaded from within zip files have useless filenames
    attached to their code object, and inspect.getinnerframes() just uses it.
    """
    fixed_records = []
    for frame, filename, line_no, func_name, lines, index in records:
        # Look inside the frame's globals dictionary for __file__, which should
        # be better.
        better_fn = frame.f_globals.get('__file__', None)
        if isinstance(better_fn, str):
            # Check the type just in case someone did something weird with
            # __file__. It might also be None if the error occurred during
            # import.
            filename = better_fn
        fixed_records.append((frame, filename, line_no, func_name, lines, index))           
    return fixed_records


def _fixed_getframes(etb, context=1, tb_offset=0):
    LNUM_POS, LINES_POS, INDEX_POS =  2, 4, 5

    records  = fix_frame_records_filenames(inspect.getinnerframes(etb, context))

    # If the error is at the console, don't build any context, since it would
    # otherwise produce 5 blank lines printed out (there is no file at the
    # console)
    rec_check = records[tb_offset:]
    try:
        rname = rec_check[0][1]
        if rname == '<ipython console>' or rname.endswith('<string>'):
            return rec_check
    except IndexError:
        pass

    aux = traceback.extract_tb(etb)
    assert len(records) == len(aux)
    for i, (file, lnum, _, _) in  enumerate(aux):
        maybeStart = lnum-1 - context//2
        start =  max(maybeStart, 0)
        end   = start + context
        lines = linecache.getlines(file)[start:end]
        # pad with empty lines if necessary
        if maybeStart < 0:
            lines = (['\n'] * -maybeStart) + lines
        if len(lines) < context:
            lines += ['\n'] * (context - len(lines))
        buf = list(records[i])
        buf[LNUM_POS] = lnum
        buf[INDEX_POS] = lnum - 1 - start
        buf[LINES_POS] = lines
        records[i] = tuple(buf)
    return records[tb_offset:]


def _format_traceback_lines(lnum, index, lines, lvals=None):
    numbers_width = 7
    res = []
    i = lnum - index

    for line in lines:
        if i == lnum:
            # This is the line with the error
            pad = numbers_width - len(str(i))
            if pad >= 3:
                marker = '-'*(pad-3) + '-> '
            elif pad == 2:
                marker = '> '    
            elif pad == 1:
                marker = '>'
            else:
                marker = ''
            num = marker + str(i)
        else:
            num = '%*s' % (numbers_width,i)
        line = '%s %s' %(num, line)

        res.append(line)
        if lvals and i == lnum:
            res.append(lvals + '\n')
        i = i + 1
    return res


def format_records(records):   #, print_globals=False):
    # Loop over all records printing context and info
    frames = []
    abspath = os.path.abspath
    for frame, file, lnum, func, lines, index in records:
        #print '*** record:',file,lnum,func,lines,index  # dbg
        try:
            file = file and abspath(file) or '?'
        except OSError:
            # if file is '<console>' or something not in the filesystem,
            # the abspath call will throw an OSError.  Just ignore it and
            # keep the original file string.
            pass
        link = file
        try:
            args, varargs, varkw, locals = inspect.getargvalues(frame)
        except:
            # This can happen due to a bug in python2.3.  We should be
            # able to remove this try/except when 2.4 becomes a
            # requirement.  Bug details at http://python.org/sf/1005466
            print "\nJoblib's exception reporting continues...\n"
            
        if func == '?':
            call = ''
        else:
            # Decide whether to include variable details or not
            try:
                call = 'in %s%s' % (func,inspect.formatargvalues(args,
                                            varargs, varkw,
                                            locals, formatvalue=eq_repr))
            except KeyError:
                # Very odd crash from inspect.formatargvalues().  The
                # scenario under which it appeared was a call to
                # view(array,scale) in NumTut.view.view(), where scale had
                # been defined as a scalar (it should be a tuple). Somehow
                # inspect messes up resolving the argument list of view()
                # and barfs out. At some point I should dig into this one
                # and file a bug report about it.
                print "\nJoblib's exception reporting continues...\n"
                call = 'in %s(***failed resolving arguments***)' % func

        # Initialize a list of names on the current line, which the
        # tokenizer below will populate.
        names = []

        def tokeneater(token_type, token, start, end, line):
            """Stateful tokeneater which builds dotted names.

            The list of names it appends to (from the enclosing scope) can
            contain repeated composite names.  This is unavoidable, since
            there is no way to disambguate partial dotted structures until
            the full list is known.  The caller is responsible for pruning
            the final list of duplicates before using it."""
            
            # build composite names
            if token == '.':
                try:
                    names[-1] += '.'
                    # store state so the next token is added for x.y.z names
                    tokeneater.name_cont = True
                    return
                except IndexError:
                    pass
            if token_type == tokenize.NAME and token not in keyword.kwlist:
                if tokeneater.name_cont:
                    # Dotted names
                    names[-1] += token
                    tokeneater.name_cont = False
                else:
                    # Regular new names.  We append everything, the caller
                    # will be responsible for pruning the list later.  It's
                    # very tricky to try to prune as we go, b/c composite
                    # names can fool us.  The pruning at the end is easy
                    # to do (or the caller can print a list with repeated
                    # names if so desired.
                    names.append(token)
            elif token_type == tokenize.NEWLINE:
                raise IndexError
        # we need to store a bit of state in the tokenizer to build
        # dotted names
        tokeneater.name_cont = False

        def linereader(file=file, lnum=[lnum], getline=linecache.getline):
            line = getline(file, lnum[0])
            lnum[0] += 1
            return line

        # Build the list of names on this line of code where the exception
        # occurred.
        try:
            # This builds the names list in-place by capturing it from the
            # enclosing scope.
            tokenize.tokenize(linereader, tokeneater)
        except IndexError:
            # signals exit of tokenizer
            pass
        except tokenize.TokenError,msg:
            print ("An unexpected error occurred while tokenizing input\n"
                    "The following traceback may be corrupted or invalid\n"
                    "The error message is: %s\n" % msg)
        
        # prune names list of duplicates, but keep the right order
        unique_names = uniq_stable(names)

        # Start loop over vars
        lvals = []
        for name_full in unique_names:
            name_base = name_full.split('.',1)[0]
            if name_base in frame.f_code.co_varnames:
                if locals.has_key(name_base):
                    try:
                        value = repr(eval(name_full,locals))
                    except:
                        value = "undefined"
                else:
                    value = "undefined"
                name = name_full
                lvals.append('%s = %s' % (name,value))
            #elif print_globals:
            #    if frame.f_globals.has_key(name_base):
            #        try:
            #            value = repr(eval(name_full,frame.f_globals))
            #        except:
            #            value = "undefined"
            #    else:
            #        value = "undefined"
            #    name = 'global %s' % name_full
            #    lvals.append('%s = %s' % (name,value))
        if lvals:
            lvals = '%s%s' % (INDENT, ('\n%s' % INDENT).join(lvals))
        else:
            lvals = ''

        level = '%s\n%s %s\n' % (75*'.', link, call)

        if index is None:
            frames.append(level)
        else:
            frames.append('%s%s' % (level,''.join(
                _format_traceback_lines(lnum, index, lines, lvals))))
           
    return frames


################################################################################
def format_exc(etype, evalue, etb, context=5, tb_offset=0):
    """ Return a nice text document describing the traceback.
    
        Parameters
        -----------
        etype, evalue, etb: as returned by sys.exc_info
        context: number of lines of the source file to plot
        tb_offset: the number of stack frame not to use (0 = use all)

    """
    # some locals
    try:
        etype = etype.__name__
    except AttributeError:
        pass

    # Header with the exception type, python version, and date
    pyver = 'Python ' + string.split(sys.version)[0] + ': ' + sys.executable
    date = time.ctime(time.time())
    pid = 'PID: %i' % os.getpid()
    
    head = '%s%s%s\n%s%s%s' % (etype, ' '*(75-len(str(etype))-len(date)),
                           date, pid, ' '*(75-len(str(pid))-len(pyver)),
                           pyver)

    # Flush cache before calling inspect.  This helps alleviate some of the
    # problems with python 2.3's inspect.py.
    linecache.checkcache()
    # Drop topmost frames if requested
    try:
        records = _fixed_getframes(etb, context, tb_offset)
    except:
        raise
        print '\nUnfortunately, your original traceback can not be constructed.\n'
        return ''

    # Get (safely) a string form of the exception info
    try:
        etype_str,evalue_str = map(str,(etype,evalue))
    except:
        # User exception is improperly defined.
        etype,evalue = str,sys.exc_info()[:2]
        etype_str,evalue_str = map(str,(etype,evalue))
    # ... and format it
    exception = ['%s: %s' % (etype_str, evalue_str)]
    if type(evalue) is types.InstanceType:
        try:
            names = [w for w in dir(evalue) if isinstance(w, basestring)]
        except:
            # Every now and then, an object with funny inernals blows up
            # when dir() is called on it.  We do the best we can to report
            # the problem and continue
            exception.append(
                    'Exception reporting error (object with broken dir()):'
                    )
            etype_str, evalue_str = map(str,sys.exc_info()[:2])
            exception.append('%s: %s' % (etype_str, evalue_str))
            names = []
        for name in names:
            value = safe_repr(getattr(evalue, name))
            exception.append('\n%s%s = %s' % (INDENT, name, value))

    frames = format_records(records)
    return '%s\n%s\n%s' % (head,'\n'.join(frames),''.join(exception[0]) )


################################################################################
def format_outer_frames(context=5, stack_start=None, stack_end=None,
                        ignore_ipython=True):
    LNUM_POS, LINES_POS, INDEX_POS =  2, 4, 5
    records = inspect.getouterframes(inspect.currentframe())
    output = list()

    for i, (frame, filename, line_no, func_name, lines, index) \
                                                in enumerate(records):
        # Look inside the frame's globals dictionary for __file__, which should
        # be better.
        better_fn = frame.f_globals.get('__file__', None)
        if isinstance(better_fn, str):
            # Check the type just in case someone did something weird with
            # __file__. It might also be None if the error occurred during
            # import.
            filename = better_fn
            if filename.endswith('.pyc'):
                filename = filename[:-4] + '.py'
        if ignore_ipython:
            # Hack to avoid printing the interals of IPython
            if (os.path.basename(filename) == 'iplib.py' 
                        and func_name in ('safe_execfile', 'runcode')):
                break
        maybeStart = line_no -1 - context//2
        start =  max(maybeStart, 0)
        end   = start + context
        lines = linecache.getlines(filename)[start:end]
        # pad with empty lines if necessary
        if maybeStart < 0:
            lines = (['\n'] * -maybeStart) + lines
        if len(lines) < context:
            lines += ['\n'] * (context - len(lines))
        buf = list(records[i])
        buf[LNUM_POS] = line_no
        buf[INDEX_POS] = line_no - 1 - start
        buf[LINES_POS] = lines
        output.append(tuple(buf))
    return '\n'.join(format_records(output[stack_end:stack_start:-1]))




"""
A context object for caching a function's return value each time it
is called with the same input arguments.

"""

# Author: Gael Varoquaux <gael dot varoquaux at normalesup dot org> 
# Copyright (c) 2009 Gael Varoquaux
# License: BSD Style, 3 clauses.


import os
import shutil
import sys
import time
import pydoc
try:
    import cPickle as pickle
except ImportError:
    import pickle
import functools
import traceback
import warnings
import inspect
try:
    # json is in the standard library for Python >= 2.6
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # Not the end of the world: we'll do without this functionality
        json = None

# Local imports
from .hashing import hash
from .func_inspect import get_func_code, get_func_name, filter_args
from .logger import Logger, format_time
from . import numpy_pickle

FIRST_LINE_TEXT = "# first line:"

# TODO: The following object should have a data store object as a sub
# object, and the interface to persist and query should be separated in
# the data store.
#
# This would enable creating 'Memory' objects with a different logic for 
# pickling that would simply span a MemorizedFunc with the same
# store (or do we want to copy it to avoid cross-talks?), for instance to
# implement HDF5 pickling. 

# TODO: Same remark for the logger, and probably use the Python logging
# mechanism.

# TODO: Track history as objects are called, to be able to garbage
# collect them.


def extract_first_line(func_code):
    """ Extract the first line information from the function code
        text if available.
    """
    if func_code.startswith(FIRST_LINE_TEXT):
        func_code = func_code.split('\n')
        first_line = int(func_code[0][len(FIRST_LINE_TEXT):])
        func_code = '\n'.join(func_code[1:])
    else:
        first_line = -1
    return func_code, first_line


class JobLibCollisionWarning(UserWarning):
    """ Warn that there might be a collision between names of functions.
    """


################################################################################
# class `Memory`
################################################################################
class MemorizedFunc(Logger):
    """ Callable object decorating a function for caching its return value 
        each time it is called.
    
        All values are cached on the filesystem, in a deep directory
        structure. Methods are provided to inspect the cache or clean it.

        Attributes
        ----------
        func: callable
            The original, undecorated, function.
        cachedir: string
            Path to the base cache directory of the memory context.
        ignore: list or None
            List of variable names to ignore when choosing whether to
            recompute.
        mmap_mode: {None, 'r+', 'r', 'w+', 'c'}
            The memmapping mode used when loading from cache
            numpy arrays. See numpy.load for the meaning of the
            arguments. Only used if save_npy was true when the
            cache was created.
        verbose: int, optional
            The verbosity flag, controls messages that are issued as 
            the function is revaluated.
    """
    #-------------------------------------------------------------------------
    # Public interface
    #-------------------------------------------------------------------------
   
    def __init__(self, func, cachedir, ignore=None, save_npy=True, 
                             mmap_mode=None, verbose=1):
        """
            Parameters
            ----------
            func: callable
                The function to decorate
            cachedir: string
                The path of the base directory to use as a data store
            ignore: list or None
                List of variable names to ignore.
            save_npy: boolean, optional
                If True, numpy arrays are saved outside of the pickle
                files in the cache, as npy files.
            mmap_mode: {None, 'r+', 'r', 'w+', 'c'}, optional
                The memmapping mode used when loading from cache
                numpy arrays. See numpy.load for the meaning of the
                arguments. Only used if save_npy was true when the
                cache was created.
            verbose: int, optional
                Verbosity flag, controls the debug messages that are issued 
                as functions are revaluated.
        """
        Logger.__init__(self)
        self._verbose = verbose
        self.cachedir = cachedir
        self.func = func
        self.save_npy = save_npy
        self.mmap_mode = mmap_mode
        if ignore is None:
            ignore = []
        self.ignore = ignore
        if not os.path.exists(self.cachedir):
            os.makedirs(self.cachedir)
        try:
            functools.update_wrapper(self, func)
        except:
            " Objects like ufunc don't like that "
        if inspect.isfunction(func):
            doc = pydoc.TextDoc().document(func
                                    ).replace('\n', '\n\n', 1)
        else:
            # Pydoc does a poor job on other objects
            doc = func.__doc__
        self.__doc__ = 'Memoized version of %s' % doc


    def __call__(self, *args, **kwargs):
        # Compare the function code with the previous to see if the
        # function code has changed
        output_dir = self.get_output_dir(*args, **kwargs)
        # FIXME: The statements below should be try/excepted
        if not (self._check_previous_func_code(stacklevel=3) and 
                                 os.path.exists(output_dir)):
            return self.call(*args, **kwargs)
        else:
            try:
                return self.load_output(output_dir)
            except Exception, e:
                # XXX: Should use an exception logger
                self.warn(
                'Exception while loading results for '
                '(args=%s, kwargs=%s)\n %s' %
                    (args, kwargs, traceback.format_exc())
                    )
                      
                shutil.rmtree(output_dir)
                return self.call(*args, **kwargs)

    #-------------------------------------------------------------------------
    # Private interface
    #-------------------------------------------------------------------------
   
    def _get_func_dir(self, mkdir=True):
        """ Get the directory corresponding to the cache for the
            function.
        """
        module, name = get_func_name(self.func)
        module.append(name)
        func_dir = os.path.join(self.cachedir, *module)
        if mkdir and not os.path.exists(func_dir):
            try:
                os.makedirs(func_dir)
            except OSError:
                """ Dir exists: we have a race condition here, when using 
                    multiprocessing.
                """
                # XXX: Ugly
        return func_dir


    def get_output_dir(self, *args, **kwargs):
        """ Returns the directory in which are persisted the results
            of the function corresponding to the given arguments.

            The results can be loaded using the .load_output method.
        """
        coerce_mmap = (self.mmap_mode is not None)
        argument_hash = hash(filter_args(self.func, self.ignore,
                             *args, **kwargs), 
                             coerce_mmap=coerce_mmap)
        output_dir = os.path.join(self._get_func_dir(self.func),
                                    argument_hash)
        return output_dir
        

    def _write_func_code(self, filename, func_code, first_line):
        """ Write the function code and the filename to a file.
        """
        func_code = '%s %i\n%s' % (FIRST_LINE_TEXT, first_line, func_code)
        file(filename, 'w').write(func_code)


    def _check_previous_func_code(self, stacklevel=2):
        """ 
            stacklevel is the depth a which this function is called, to
            issue useful warnings to the user.
        """
        # Here, we go through some effort to be robust to dynamically
        # changing code and collision. We cannot inspect.getsource
        # because it is not reliable when using IPython's magic "%run".
        func_code, source_file, first_line = get_func_code(self.func)
        func_dir = self._get_func_dir()
        func_code_file = os.path.join(func_dir, 'func_code.py')

        if not os.path.exists(func_code_file): 
            self._write_func_code(func_code_file, func_code, first_line)
            return False
        old_func_code, old_first_line = \
                        extract_first_line(file(func_code_file).read())
        if old_func_code == func_code:
            return True

        # We have differing code, is this because we are refering to
        # differing functions, or because the function we are refering as 
        # changed?

        if old_first_line == first_line == -1:
            _, func_name = get_func_name(self.func, resolv_alias=False)
            if not first_line == -1:
                func_description = '%s (%s:%i)' % (func_name, 
                                                source_file, first_line)
            else:
                func_description = func_name
            warnings.warn(JobLibCollisionWarning(
                "Cannot detect name collisions for function '%s'"
                        % func_description), stacklevel=stacklevel)

        # Fetch the code at the old location and compare it. If it is the
        # same than the code store, we have a collision: the code in the
        # file has not changed, but the name we have is pointing to a new
        # code block.
        if (not old_first_line == first_line 
                                    and source_file is not None
                                    and os.path.exists(source_file)):
            _, func_name = get_func_name(self.func, resolv_alias=False)
            num_lines = len(func_code.split('\n'))
            on_disk_func_code = file(source_file).readlines()[
                        old_first_line-1:old_first_line-1+num_lines-1]
            on_disk_func_code = ''.join(on_disk_func_code)
            if on_disk_func_code.rstrip() == old_func_code.rstrip():
                warnings.warn(JobLibCollisionWarning(
                'Possible name collisions between functions '
                "'%s' (%s:%i) and '%s' (%s:%i)" %
                (func_name, source_file, old_first_line, 
                 func_name, source_file, first_line)),
                 stacklevel=stacklevel)

        # The function has changed, wipe the cache directory.
        # XXX: Should be using warnings, and giving stacklevel
        self.clear(warn=True)
        return False


    def clear(self, warn=True):
        """ Empty the function's cache. 
        """
        func_dir = self._get_func_dir(mkdir=False)
        if self._verbose and warn:
            self.warn("Clearing cache %s" % func_dir)
        if os.path.exists(func_dir):
            shutil.rmtree(func_dir)
        os.makedirs(func_dir)
        func_code, _, first_line = get_func_code(self.func)
        func_code_file = os.path.join(func_dir, 'func_code.py')
        self._write_func_code(func_code_file, func_code, first_line)


    def call(self, *args, **kwargs):
        """ Force the execution of the function with the given arguments and 
            persist the output values.
        """
        if self._verbose:
            print self.format_call(*args, **kwargs)
            start_time = time.time()
        output_dir = self.get_output_dir(*args, **kwargs)
        output = self.func(*args, **kwargs)
        self._persist_output(output, output_dir)
        self._persist_input(output_dir, *args, **kwargs)
        if self._verbose:
            _, name = get_func_name(self.func)
            msg = '%s - %s' % (name, 
                               format_time(time.time() - start_time))
            print max(0, (80 - len(msg)))*'_' + msg
        return output


    def format_call(self, *args, **kwds):
        """ Returns a nicely formatted statement displaying the function 
            call with the given arguments.
        """
        path, signature = self.format_signature(self.func, *args,
                            **kwds)
        msg = '%s\n[Memory] Calling %s...\n%s' % (80*'_', path, signature)
        return msg
        # XXX: Not using logging framework
        #self.debug(msg)

    def format_signature(self, func, *args, **kwds):
        # XXX: This should be moved out to a function
        # XXX: Should this use inspect.formatargvalues/formatargspec?
        module, name = get_func_name(func)
        module = [m for m in module if m]
        if module:
            module.append(name)
            module_path = '.'.join(module)
        else:
            module_path = name
        arg_str = list()
        previous_length = 0
        for arg in args:
            arg = self.format(arg, indent=2)
            if len(arg) > 1500:
                arg = '%s...' % arg[:700]
            if previous_length > 80:
                arg = '\n%s' % arg
            previous_length = len(arg)
            arg_str.append(arg)
        arg_str.extend(['%s=%s' % (v, self.format(i)) for v, i in
                                    kwds.iteritems()])
        arg_str = ', '.join(arg_str)

        signature = '%s(%s)' % (name, arg_str)
        return module_path, signature

    # Make make public

    def _persist_output(self, output, dir):
        """ Persist the given output tuple in the directory.
        """
        if not os.path.exists(dir):
            os.makedirs(dir)
        filename = os.path.join(dir, 'output.pkl')

        if 'numpy' in sys.modules and self.save_npy:
            numpy_pickle.dump(output, filename) 
        else:
            output_file = file(filename, 'w')
            pickle.dump(output, output_file, protocol=2)
            output_file.close()


    def _persist_input(self, output_dir, *args, **kwargs):
        """ Save a small summary of the call using json format in the
            output directory.
        """
        argument_dict = filter_args(self.func, self.ignore,
                                    *args, **kwargs)
        if json is not None:
            json.dump(
                dict((k, repr(v)) 
                    for k, v in argument_dict.iteritems()),
                file(os.path.join(output_dir, 'input_args.json'), 'w'),
                )

    def load_output(self, output_dir):
        """ Read the results of a previous calculation from the directory
            it was cached in.
        """
        filename = os.path.join(output_dir, 'output.pkl')
        if self.save_npy:
            return numpy_pickle.load(filename, 
                                     mmap_mode=self.mmap_mode)
        else:
            output_file = file(filename, 'r')
            return pickle.load(output_file)

    # XXX: Need a method to check if results are available.

    #-------------------------------------------------------------------------
    # Private `object` interface
    #-------------------------------------------------------------------------
   
    def __repr__(self):
        return '%s(func=%s, cachedir=%s)' % (
                    self.__class__.__name__,
                    self.func,
                    repr(self.cachedir),
                    )



################################################################################
# class `Memory`
################################################################################
class Memory(Logger):
    """ A context object for caching a function's return value each time it
        is called with the same input arguments.
    
        All values are cached on the filesystem, in a deep directory
        structure.

        see :ref:`memory`
    """
    #-------------------------------------------------------------------------
    # Public interface
    #-------------------------------------------------------------------------
   
    def __init__(self, cachedir, save_npy=True, mmap_mode=None,
                       verbose=1):
        """
            Parameters
            ----------
            cachedir: string or None
                The path of the base directory to use as a data store
                or None. If None is given, no caching is done and
                the Memory object is completely transparent.
            save_npy: boolean, optional
                If True, numpy arrays are saved outside of the pickle
                files in the cache, as npy files.
            mmap_mode: {None, 'r+', 'r', 'w+', 'c'}, optional
                The memmapping mode used when loading from cache
                numpy arrays. See numpy.load for the meaning of the
                arguments. Only used if save_npy was true when the
                cache was created.
            verbose: int, optional
                Verbosity flag, controls the debug messages that are issued 
                as functions are revaluated.
        """
        # XXX: Bad explaination of the None value of cachedir
        Logger.__init__(self)
        self._verbose = verbose
        self.cachedir = cachedir
        self.save_npy = save_npy
        self.mmap_mode = mmap_mode
        if cachedir is not None and not os.path.exists(self.cachedir):
            os.makedirs(self.cachedir)


    def cache(self, func=None, ignore=None):
        """ Decorates the given function func to only compute its return
            value for input arguments not cached on disk.

            Returns
            -------
            decorated_func: MemorizedFunc object
                The returned object is a MemorizedFunc object, that is 
                callable (behaves like a function), but offers extra
                methods for cache lookup and management. See the
                documentation for :class:`joblib.memory.MemorizedFunc`.
        """
        if func is None:
            # Partial application, to be able to specify extra keyword 
            # arguments in decorators
            return functools.partial(self.cache, ignore=ignore)
        if self.cachedir is None:
            return func
        return MemorizedFunc(func, cachedir=self.cachedir,
                                   save_npy=self.save_npy,
                                   mmap_mode=self.mmap_mode,
                                   ignore=ignore,
                                   verbose=self._verbose)


    def clear(self, warn=True):
        """ Erase the complete cache directory.
        """
        if warn:
            self.warn('Flushing completely the cache')
        shutil.rmtree(self.cachedir)
        os.makedirs(self.cachedir)


    def eval(self, func, *args, **kwargs):
        """ Eval function func with arguments `*args` and `**kwargs`,
            in the context of the memory.

            This method works similarly to the builtin `apply`, except
            that the function is called only if the cache is not
            up to date.

        """
        if self.cachedir is None:
            return func(*args, **kwargs)
        return self.cache(func)(*args, **kwargs)

    #-------------------------------------------------------------------------
    # Private `object` interface
    #-------------------------------------------------------------------------
   
    def __repr__(self):
        return '%s(cachedir=%s)' % (
                    self.__class__.__name__,
                    repr(self.cachedir),
                    )



"""
My own variation on function-specific inspect-like features.
"""

# Author: Gael Varoquaux <gael dot varoquaux at normalesup dot org> 
# Copyright (c) 2009 Gael Varoquaux
# License: BSD Style, 3 clauses.

import itertools
import inspect
import warnings
import os

def get_func_code(func):
    """ Attempts to retrieve a reliable function code hash.
    
        The reason we don't use inspect.getsource is that it caches the
        source, whereas we want this to be modified on the fly when the
        function is modified.

        Returns
        -------
        func_code: string
            The function code
        source_file: string
            The path to the file in which the function is defined.
        first_line: int
            The first line of the code in the source file.

        Notes
        ------
        This function does a bit more magic than inspect, and is thus
        more robust.
    """
    source_file = None
    try:
        # Try to retrieve the source code.
        source_file = func.func_code.co_filename
        source_file_obj = file(source_file)
        first_line = func.func_code.co_firstlineno
        # All the lines after the function definition:
        source_lines = list(itertools.islice(source_file_obj, first_line-1, None))
        return ''.join(inspect.getblock(source_lines)), source_file, first_line
    except:
        # If the source code fails, we use the hash. This is fragile and
        # might change from one session to another.
        if hasattr(func, 'func_code'):
            return str(func.func_code.__hash__()), source_file, -1
        else:
            # Weird objects like numpy ufunc don't have func_code
            # This is fragile, as quite often the id of the object is
            # in the repr, so it might not persist accross sessions,
            # however it will work for ufuncs.
            return repr(func), source_file, -1


def get_func_name(func, resolv_alias=True):  
    """ Return the function import path (as a list of module names), and
        a name for the function.

        Parameters
        ----------
        func: callable
            The func to inspect
        resolv_alias: boolean, optional
            If true, possible local alias are indicated.
    """
    if hasattr(func, '__module__'):
        module = func.__module__
    else:
        try:
            module = inspect.getmodule(func)
        except TypeError:
            if hasattr(func, '__class__'):
                module = func.__class__.__module__
            else:
                module = 'unkown'
    if module is None:
        # Happens in doctests, eg
        module = ''
    if module == '__main__':
        try:
            filename = inspect.getsourcefile(func)
        except:
            filename = None
        if filename is not None:
            filename = filename.replace('/', '-')
            if filename.endswith('.py'):
                filename = filename[:-3]
            module = module + '-' + filename
    module = module.split('.')
    if hasattr(func, 'func_name'):
        name = func.func_name
    elif hasattr(func, '__name__'): 
        name = func.__name__
    else:
        name = 'unkown'
    # Hack to detect functions not defined at the module-level
    if resolv_alias:
        # TODO: Maybe add a warning here?
        if hasattr(func, 'func_globals') and name in func.func_globals:
            if not func.func_globals[name] is func:
                name = '%s-alias' % name
    if inspect.ismethod(func):
        # We need to add the name of the class    
        if hasattr(func, 'im_class'):
            klass = func.im_class
            module.append(klass.__name__)
    if os.name == 'nt':
        # Stupid windows can't encode certain characters in filenames
        import urllib
        for char in ('<', '>', '!', ':'):
            name = name.replace(char, urllib.quote(char))
    return module, name


def filter_args(func, ignore_lst, *args, **kwargs):
    """ Filters the given args and kwargs using a list of arguments to
        ignore, and a function specification.

        Parameters
        ----------
        func: callable
            Function giving the argument specification
        ignore_lst: list of strings
            List of arguments to ignore (either a name of an argument 
            in the function spec, or '*', or '**')
        *args: list
            Positional arguments passed to the function.
        **kwargs: dict
            Keyword arguments passed to the function

        Returns
        -------
        filtered_args: list
            List of filtered positionnal arguments.
        filtered_kwdargs: dict
            List of filtered Keyword arguments.
    """
    args = list(args)
    if isinstance(ignore_lst, basestring):
        # Catch a common mistake
        raise ValueError('ignore_lst must be a list of parameters to ignore '
            '%s (type %s) was given' % (ignore_lst, type(ignore_lst)))
    # Special case for functools.partial objects
    if (not inspect.ismethod(func) and not inspect.isfunction(func)): 
        if ignore_lst:
            warnings.warn('Cannot inspect object %s, ignore list will '
                'not work.' % func, stacklevel=2)
        return {'*':args, '**':kwargs}
    arg_spec = inspect.getargspec(func)
    # We need to if/them to account for different versions of Python
    if hasattr(arg_spec, 'args'):
        arg_names    = arg_spec.args
        arg_defaults = arg_spec.defaults
        arg_keywords = arg_spec.keywords
        arg_varargs  = arg_spec.varargs
    else:
        arg_names, arg_varargs, arg_keywords, arg_defaults = arg_spec
    arg_defaults = arg_defaults or {}
    if inspect.ismethod(func):
        # First argument is 'self', it has been removed by Python
        # we need to add it back:
        args = [func.im_self, ] + args
    # XXX: Maybe I need an inspect.isbuiltin to detect C-level methods, such 
    # as on ndarrays.

    _, name = get_func_name(func, resolv_alias=False)
    arg_dict = dict()
    arg_position = 0
    for arg_position, arg_name in enumerate(arg_names):
        if arg_position < len(args):
            # Positional argument or keyword argument given as positional
            arg_dict[arg_name] = args[arg_position]
        else:
            position = arg_position - len(arg_names)
            if arg_name in kwargs:
                arg_dict[arg_name] = kwargs.pop(arg_name)
            else:
                try:
                    arg_dict[arg_name] = arg_defaults[position]
                except IndexError:
                    # Missing argument
                    raise ValueError('Wrong number of arguments for %s%s:\n'
                                     '     %s(%s, %s) was called.'
                        % (name, 
                           inspect.formatargspec(*inspect.getargspec(func)),
                           name,
                           repr(args)[1:-1],
                           ', '.join('%s=%s' % (k, v) 
                                    for k, v in kwargs.iteritems())
                           )
                        )
                    


    varkwargs = dict()
    for arg_name, arg_value in kwargs.iteritems():
        if arg_name in arg_dict:
            arg_dict[arg_name] = arg_value
        elif arg_keywords is not None:
            varkwargs[arg_name] = arg_value
        else:
            raise TypeError("Ignore list for %s() contains an unexpected "
                            "keyword argument '%s'" % (name, arg_name))

    if arg_keywords is not None:
        arg_dict['**'] = varkwargs
    if arg_varargs is not None:
        varargs = args[arg_position+1:]
        arg_dict['*'] = varargs

    # Now remove the arguments to be ignored
    for item in ignore_lst:
        if item in arg_dict:
            arg_dict.pop(item)
        else:
            raise ValueError("Ignore list: argument '%s' is not defined for "
            "function %s%s" % 
                            (item, name,
                             inspect.formatargspec(arg_names,
                                                   arg_varargs,
                                                   arg_keywords,
                                                   arg_defaults,
                                                   )))
    # XXX: Return a sorted list of pairs?
    return arg_dict 


""" Joblib is a set of tools to provide **lightweight pipelining in
Python**. In particular, joblib offers:

  1. transparent disk-caching of the output values and lazy re-evaluation
     (memoize pattern)

  2. easy simple parallel computing

  3. logging and tracing of the execution

Joblib is optimized to be fast and robust in particular on large,
long-running functions and has specific optimizations for `numpy` arrays.

____

* The latest user documentation for `joblib` can be found on
  http://packages.python.org/joblib/

* The latest packages can be downloaded from
  http://pypi.python.org/pypi/joblib

* Instructions for developpers can be found at:
  http://github.com/joblib/joblib

joblib is **BSD-licensed**.

Vision
--------

Joblib came out of long-running data-analysis Python scripts. The long
term vision is to provide tools for scientists to achieve better
reproducibility when running jobs, without changing the way numerical
code looks like. However, Joblib can also be used to provide a
light-weight make replacement.

The main problems identified are:

 1) **Lazy evaluation:** People need to rerun over and over the same
    script as it is tuned, but end up commenting out steps, or
    uncommenting steps, as they are needed, as they take long to run.

 2) **Persistence:** It is difficult to persist in an efficient way
    arbitrary objects containing large numpy arrays. In addition,
    hand-written persistence to disk does not link easily the file on
    disk to the corresponding Python object it was persists from in the
    script. This leads to people not a having a hard time resuming the
    job, eg after a crash and persistence getting in the way of work.

The approach taken by Joblib to address these problems is not to build a
heavy framework and coerce user into using it (e.g. with an explicit
pipeline). It strives to leave your code and your flow control as
unmodified as possible.

Current features
------------------

1) **Transparent and fast disk-caching of output value:** a make-like
   functionality for Python functions that works well for arbitrary
   Python objects, including very large numpy arrays. The goal is 
   to separate operations in a set of steps with well-defined inputs and 
   outputs, that are saved and reran only if necessary, by using standard 
   Python functions::

      >>> from joblib import Memory
      >>> mem = Memory(cachedir='/tmp/joblib')
      >>> import numpy as np
      >>> a = np.vander(np.arange(3))
      >>> square = mem.cache(np.square)
      >>> b = square(a)
      ________________________________________________________________________________
      [Memory] Calling square...
      square(array([[0, 0, 1],
             [1, 1, 1],
             [4, 2, 1]]))
      ___________________________________________________________square - 0.0s, 0.0min

      >>> c = square(a)
      >>> # The above call did not trigger an evaluation

2) **Embarrassingly parallel helper:** to make is easy to write readable 
   parallel code and debug it quickly:

      >>> from joblib import Parallel, delayed
      >>> from math import sqrt
      >>> Parallel(n_jobs=1)(delayed(sqrt)(i**2) for i in range(10))
      [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]


3) **Logging/tracing:** The different functionalities will
   progressively acquire better logging mechanism to help track what
   has been ran, and capture I/O easily. In addition, Joblib will
   provide a few I/O primitives, to easily define define logging and
   display streams, and provide a way of compiling a report. 
   We want to be able to quickly inspect what has been run.

Contributing
-------------

The code is `hosted <http://github.com/GaelVaroquaux/joblib>`_ on github.
It is easy to clone the project and experiment with making your own
modifications. If you need extra features, don't hesitate to contribute
them.

.. 
    >>> import shutil ; shutil.rmtree('/tmp/joblib/')

"""

__version__ = '0.4.4'


from .memory import Memory
from .logger import PrintTime, Logger
from .hashing import hash
from .numpy_pickle import dump, load
from .parallel import Parallel, delayed


"""
Helpers for logging.

This module needs much love to become useful.
"""

# Author: Gael Varoquaux <gael dot varoquaux at normalesup dot org> 
# Copyright (c) 2008 Gael Varoquaux
# License: BSD Style, 3 clauses.


import time
import sys
import os
import shutil
import logging
import pprint

def format_time(t):
    return "%.1fs, %.1fmin" % (t, t/60.)

def short_format_time(t):
    if t > 60:
        return "%4.1fmin" % (t/60.)
    else:
        return " %5.1fs" % (t)

################################################################################
# class `Logger`
################################################################################
class Logger(object):
    """ Base class for logging messages.
    """
    
    def __init__(self, depth=3):
        """
            Parameters
            ----------
            depth: int, optional
                The depth of objects printed.
        """
        self.depth = depth

    def warn(self, msg):
        logging.warn("[%s]: %s" % (self, msg))

    def debug(self, msg):
        # XXX: This conflicts with the debug flag used in children class
        logging.debug("[%s]: %s" % (self, msg))

    def format(self, obj, indent=0):
        """ Return the formated representation of the object.
        """
        if 'numpy' in sys.modules:
            import numpy as np
            print_options = np.get_printoptions()
            np.set_printoptions(precision=6, threshold=64, edgeitems=1)
        else:
            print_options = None
        out = pprint.pformat(obj, depth=self.depth, indent=indent)
        if print_options:
            np.set_printoptions(**print_options)
        return out


################################################################################
# class `PrintTime`
################################################################################
class PrintTime(object):
    """ Print and log messages while keeping track of time.
    """

    def __init__(self, logfile=None, logdir=None):
        if logfile is not None and logdir is not None:
            raise ValueError('Cannot specify both logfile and logdir')
        # XXX: Need argument docstring
        self.last_time = time.time()
        self.start_time = self.last_time
        if logdir is not None:
            logfile = os.path.join(logdir, 'joblib.log')
        self.logfile = logfile
        if logfile is not None:
            if not os.path.exists(os.path.dirname(logfile)):
                os.makedirs(os.path.dirname(logfile))
            if os.path.exists(logfile):
                # Rotate the logs
                for i in range(1, 9):
                    if os.path.exists(logfile+'.%i' % i):
                        try:
                            shutil.move(logfile+'.%i' % i, 
                                        logfile+'.%i' % (i+1))
                        except:
                            "No reason failing here"
                # Use a copy rather than a move, so that a process
                # monitoring this file does not get lost.
                try:
                    shutil.copy(logfile, logfile+'.1')
                except:
                    "No reason failing here"
            try:
                logfile = file(logfile, 'w')
                logfile.write('\nLogging joblib python script\n')
                logfile.write('\n---%s---\n' % time.ctime(self.last_time))
            except:
                """ Multiprocessing writing to files can create race
                    conditions. Rather fail silently than crash the
                    caculation.
                """
                # XXX: We actually need a debug flag to disable this
                # silent failure.


    def __call__(self, msg='', total=False):
        """ Print the time elapsed between the last call and the current
            call, with an optional message.
        """
        if not total:
            time_lapse = time.time() - self.last_time
            full_msg = "%s: %s" % (msg, format_time(time_lapse) )
        else:
            # FIXME: Too much logic duplicated
            time_lapse = time.time() - self.start_time
            full_msg = "%s: %.2fs, %.1f min" % (msg, time_lapse, time_lapse/60)
        print >> sys.stderr, full_msg
        if self.logfile is not None:
            try:
                print >> file(self.logfile, 'a'), full_msg
            except:
                """ Multiprocessing writing to files can create race
                    conditions. Rather fail silently than crash the
                    caculation.
                """
                # XXX: We actually need a debug flag to disable this
                # silent failure.
        self.last_time = time.time()




"""
A pickler to save numpy arrays in separate .npy files.
"""

# Author: Gael Varoquaux <gael dot varoquaux at normalesup dot org> 
# Copyright (c) 2009 Gael Varoquaux
# License: BSD Style, 3 clauses.

import pickle
import traceback
import os

################################################################################
# Utility objects for persistence.

class NDArrayWrapper(object):
    """ An object to be persisted instead of numpy arrays.

        The only thing this object does, is store the filename in wich
        the array has been persisted.
    """
    def __init__(self, filename):
        self.filename = filename


################################################################################
# Pickler classes

class NumpyPickler(pickle.Pickler):
    """ A pickler subclass that extracts ndarrays and saves them in .npy
        files outside of the pickle.
    """

    def __init__(self, filename):
        self._filename = filename
        self._filenames = [filename, ]
        self.file = open(filename, 'wb')
        # Count the number of npy files that we have created:
        self._npy_counter = 0
        pickle.Pickler.__init__(self, self.file,
                                protocol=pickle.HIGHEST_PROTOCOL)
        # delayed import of numpy, to avoid tight coupling
        import numpy as np
        self.np = np

    def save(self, obj):
        """ Subclass the save method, to save ndarray subclasses in npy
            files, rather than pickling them. Off course, this is a 
            total abuse of the Pickler class.
        """
        if isinstance(obj, self.np.ndarray):
            self._npy_counter += 1
            try:
                filename = '%s_%02i.npy' % (self._filename,
                                            self._npy_counter )
                self._filenames.append(filename)
                self.np.save(filename, obj)
                obj = NDArrayWrapper(os.path.basename(filename))
            except:
                self._npy_counter -= 1
                # XXX: We should have a logging mechanism
                print 'Failed to save %s to .npy file:\n%s' % (
                        type(obj),
                        traceback.format_exc())
        pickle.Pickler.save(self, obj)



class NumpyUnpickler(pickle.Unpickler):
    """ A subclass of the Unpickler to unpickle our numpy pickles.
    """
    dispatch = pickle.Unpickler.dispatch.copy()

    def __init__(self, filename, mmap_mode=None):
        self._filename = filename
        self.mmap_mode = mmap_mode
        self._dirname  = os.path.dirname(filename)
        self.file = open(filename, 'rb')
        pickle.Unpickler.__init__(self, self.file)
        import numpy as np
        self.np = np


    def load_build(self):
        """ This method is called to set the state of a knewly created
            object. 
            
            We capture it to replace our place-holder objects,
            NDArrayWrapper, by the array we are interested in. We
            replace directly in the stack of pickler.
        """
        pickle.Unpickler.load_build(self)
        if isinstance(self.stack[-1], NDArrayWrapper):
            nd_array_wrapper = self.stack.pop()
            if self.np.__version__ >= '1.3':
                array = self.np.load(os.path.join(self._dirname,
                                                nd_array_wrapper.filename),
                                                mmap_mode=self.mmap_mode)
            else:
                # Numpy does not have mmap_mode before 1.3
                array = self.np.load(os.path.join(self._dirname,
                                                nd_array_wrapper.filename))
            self.stack.append(array)


    # Be careful to register our new method.
    dispatch[pickle.BUILD] = load_build


################################################################################
# Utility functions

def dump(value, filename):
    """ Persist an arbitrary Python object into a filename, with numpy arrays 
        saved as separate .npy files.

        See Also
        --------
        joblib.load : corresponding loader
    """
    try:
        pickler = NumpyPickler(filename)
        pickler.dump(value)
    finally:
        if 'pickler' in locals() and hasattr(pickler, 'file'):
            pickler.file.flush()
            pickler.file.close()
    return pickler._filenames


def load(filename, mmap_mode=None):
    """ Reconstruct a Python object and the numpy arrays it contains from 
        a persisted file.

        This function loads the numpy array files saved separately. If
        the mmap_mode argument is given, it is passed to np.save and
        arrays are loaded as memmaps. As a consequence, the reconstructed
        object might not match the original pickled object.

        See Also
        --------
        joblib.dump : function to save the object
    """
    try:
        unpickler = NumpyUnpickler(filename, mmap_mode=mmap_mode)
        obj = unpickler.load()
    finally:
        if 'unpickler' in locals() and hasattr(unpickler, 'file'):
            unpickler.file.close()
    return obj


"""
Helpers for embarassingly parallel code.
"""
# Author: Gael Varoquaux < gael dot varoquaux at normalesup dot org >
# Copyright: 2010, Gael Varoquaux
# License: BSD 3 clause

import sys
import functools
import time
try:
    import cPickle as pickle
except:
    import pickle

try:
    import multiprocessing
except ImportError:
    multiprocessing = None

from .format_stack import format_exc, format_outer_frames
from .logger import Logger, short_format_time

################################################################################

class JoblibException(Exception):
    """ A simple exception with an error message that you can get to.
    """

    def __init__(self, message):
        self.message = message

    def __reduce__(self):
        # For pickling
        return self.__class__, (self.message,), {}

    def __repr__(self):
        return '%s\n%s\n%s\n%s' % (
                    self.__class__.__name__,
                    75*'_',
                    self.message,
                    75*'_')

    __str__ = __repr__


class SafeFunction(object):
    """ Wraps a function to make it exception with full traceback in
        their representation.
        Useful for parallel computing with multiprocessing, for which 
        exceptions cannot be captured.
    """

    def __init__(self, func):
        self.func = func


    def __call__(self, *args, **kwargs):
        try:
            return self.func(*args, **kwargs)
        except:
            e_type, e_value, e_tb = sys.exc_info()
            text = format_exc(e_type, e_value, e_tb, context=10,
                             tb_offset=1)
            raise JoblibException(text)

def print_progress(msg, index, total, start_time, n_jobs=1):
    # XXX: Not using the logger framework: need to
    # learn to use logger better.
    if total > 2*n_jobs:
        # Report less often
        if not index % n_jobs == 0:
            return
    elapsed_time = time.time() - start_time
    remaining_time = (elapsed_time/(index + 1)*
                (total - index - 1.))
    sys.stderr.write('[%s]: Done %3i out of %3i |elapsed: %s remaining: %s\n'
            % (msg,
                index+1, 
                total, 
                short_format_time(elapsed_time),
                short_format_time(remaining_time),
                ))


################################################################################
def delayed(function):
    """ Decorator used to capture the arguments of a function.
    """
    # Try to pickle the input function, to catch the problems early when
    # using with multiprocessing
    pickle.dumps(function)

    @functools.wraps(function)
    def delayed_function(*args, **kwargs):
        return function, args, kwargs
    return delayed_function



class Parallel(Logger):
    ''' Helper class for readable parallel mapping.

        Parameters
        -----------
        n_jobs: int
            The number of jobs to use for the computation. If -1 all CPUs
            are used. If 1 is given, no parallel computing code is used
            at all, which is useful for debuging.
        verbose: int, optional
            The verbosity level. If 1 is given, the elapsed time as well
            as the estimated remaining time are displayed.
        
        Notes
        -----

        This object uses the multiprocessing module to compute in
        parallel the application of a function to many different
        arguments. The main functionnality it brings in addition to 
        using the raw multiprocessing API are (see examples for details):

            * More readable code, in particular since it avoids 
              constructing list of arguments.

            * Easier debuging:
                - informative tracebacks even when the error happens on
                  the client side
                - using 'n_jobs=1' enables to turn off parallel computing
                  for debuging without changing the codepath
                - early capture of pickling errors

            * An optional progress meter.

        Examples
        --------

        A simple example:

        >>> from math import sqrt
        >>> from joblib import Parallel, delayed
        >>> Parallel(n_jobs=1)(delayed(sqrt)(i**2) for i in range(10))
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]

        Reshaping the output when the function has several return
        values:
        
        >>> from math import modf
        >>> from joblib import Parallel, delayed
        >>> r = Parallel(n_jobs=1)(delayed(modf)(i/2.) for i in range(10))
        >>> res, i = zip(*r)
        >>> res
        (0.0, 0.5, 0.0, 0.5, 0.0, 0.5, 0.0, 0.5, 0.0, 0.5)
        >>> i
        (0.0, 0.0, 1.0, 1.0, 2.0, 2.0, 3.0, 3.0, 4.0, 4.0)
       
        The progress meter::

            >>> from time import sleep
            >>> from joblib import Parallel, delayed
            >>> r = Parallel(n_jobs=2, verbose=1)(delayed(sleep)(.1) for _ in range(10)) #doctest: +SKIP
            [Parallel(n_jobs=2)]: Done   1 out of  10 |elapsed:    0.1s remaining:    0.9s
            [Parallel(n_jobs=2)]: Done   3 out of  10 |elapsed:    0.2s remaining:    0.5s
            [Parallel(n_jobs=2)]: Done   5 out of  10 |elapsed:    0.3s remaining:    0.3s
            [Parallel(n_jobs=2)]: Done   7 out of  10 |elapsed:    0.4s remaining:    0.2s
            [Parallel(n_jobs=2)]: Done   9 out of  10 |elapsed:    0.5s remaining:    0.1s

        Traceback example, note how the ligne of the error is indicated 
        as well as the values of the parameter passed to the function that
        triggered the exception, eventhough the traceback happens in the 
        child process::

         >>> from string import atoi
         >>> from joblib import Parallel, delayed
         >>> Parallel(n_jobs=2)(delayed(atoi)(n) for n in ('1', '300', 30)) #doctest: +SKIP
         #...
         ---------------------------------------------------------------------------
         Sub-process traceback: 
         ---------------------------------------------------------------------------
         TypeError                                          Fri Jul  2 20:32:05 2010
         PID: 4151                                     Python 2.6.5: /usr/bin/python
         ...........................................................................
         /usr/lib/python2.6/string.pyc in atoi(s=30, base=10)
             398     is chosen from the leading characters of s, 0 for octal, 0x or
             399     0X for hexadecimal.  If base is 16, a preceding 0x or 0X is
             400     accepted.
             401 
             402     """
         --> 403     return _int(s, base)
             404 
             405 
             406 # Convert string to long integer
             407 def atol(s, base=10):
         
         TypeError: int() can't convert non-string with explicit base
         ___________________________________________________________________________

    '''
    def __init__(self, n_jobs=None, verbose=0):
        self.verbose = verbose
        self.n_jobs = n_jobs
        # Not starting the pool in the __init__ is a design decision, to
        # be able to close it ASAP, and not burden the user with closing
        # it.


    def __call__(self, iterable):
        n_jobs = self.n_jobs
        if n_jobs == -1:
            if multiprocessing is None:
                 n_jobs = 1
            else:
                n_jobs = multiprocessing.cpu_count()

        if n_jobs is None or multiprocessing is None or n_jobs == 1:
            n_jobs = 1
            from __builtin__ import apply
        else:
            pool = multiprocessing.Pool(n_jobs)
            apply = pool.apply_async

        output = list()
        start_time = time.time()
        try:
            for index, (function, args, kwargs) in enumerate(iterable):
                if n_jobs > 1:
                    function = SafeFunction(function)
                output.append(apply(function, args, kwargs))
                if self.verbose and n_jobs == 1:
                    print '[%s]: Done job %3i | elapsed: %s' % (
                            self, index, 
                            short_format_time(time.time() - start_time)
                        )
            if n_jobs > 1:
                start_time = time.time()
                jobs = output
                output = list()
                for index, job in enumerate(jobs):
                    try:
                        output.append(job.get())
                        if self.verbose:
                            print_progress(self, index, len(jobs), start_time,
                                           n_jobs=n_jobs)
                    except JoblibException, exception:
                        # Capture exception to add information on 
                        # the local stack in addition to the distant
                        # stack
                        this_report = format_outer_frames(
                                                context=10,
                                                stack_start=1,
                                                )
                        report = """Multiprocessing exception:
%s
---------------------------------------------------------------------------
Sub-process traceback: 
---------------------------------------------------------------------------
%s""" % (
                                    this_report,
                                    exception.message,
                                )
                        raise JoblibException(report)
        finally:
            if n_jobs > 1:
                pool.close()
                pool.join()
        return output


    def __repr__(self):
        return '%s(n_jobs=%s)' % (
                    self.__class__.__name__,
                    self.n_jobs,
                )




"""
Fast cryptographic hash of Python objects, with a special case for fast 
hashing of numpy arrays.
"""

# Author: Gael Varoquaux <gael dot varoquaux at normalesup dot org> 
# Copyright (c) 2009 Gael Varoquaux
# License: BSD Style, 3 clauses.

import pickle
import hashlib
import sys
import cStringIO


class Hasher(pickle.Pickler):
    """ A subclass of pickler, to do cryptographic hashing, rather than
        pickling.
    """

    def __init__(self, hash_name='md5'):
        self.stream = cStringIO.StringIO()
        pickle.Pickler.__init__(self, self.stream, protocol=2)
        # Initialise the hash obj
        self._hash = hashlib.new(hash_name)

    def hash(self, obj, return_digest=True):
        self.dump(obj)
        dumps = self.stream.getvalue()
        self._hash.update(dumps)
        if return_digest:
            return self._hash.hexdigest()


class NumpyHasher(Hasher):
    """ Special case the haser for when numpy is loaded.
    """

    def __init__(self, hash_name='md5', coerce_mmap=False):
        """
            Parameters
            ----------
            hash_name: string
                The hash algorithm to be used
            coerce_mmap: boolean
                Make no difference between np.memmap and np.ndarray
                objects.
        """
        self.coerce_mmap = coerce_mmap
        Hasher.__init__(self, hash_name=hash_name)
        # delayed import of numpy, to avoid tight coupling
        import numpy as np
        self.np = np

    def save(self, obj):
        """ Subclass the save method, to hash ndarray subclass, rather
            than pickling them. Off course, this is a total abuse of
            the Pickler class.
        """
        if isinstance(obj, self.np.ndarray):
            # Compute a hash of the object:
            try:
                self._hash.update(self.np.getbuffer(obj))
            except TypeError:
                # Cater for non-single-segment arrays: this creates a
                # copy, and thus aleviates this issue.
                # XXX: There might be a more efficient way of doing this
                self._hash.update(self.np.getbuffer(obj.flatten()))

            # We store the class, to be able to distinguish between 
            # Objects with the same binary content, but different
            # classes.
            if self.coerce_mmap and isinstance(obj, self.np.memmap):
                # We don't make the difference between memmap and
                # normal ndarrays, to be able to reload previously
                # computed results with memmap.
                klass = self.np.ndarray
            else:
                klass = obj.__class__
            # We also return the dtype and the shape, to distinguish 
            # different views on the same data with different dtypes.

            # The object will be pickled by the pickler hashed at the end.
            obj = (klass, ('HASHED', obj.dtype, obj.shape, obj.strides))
        Hasher.save(self, obj)


def hash(obj, hash_name='md5', coerce_mmap=False):
    """ Quick calculation of a hash to identify uniquely Python objects 
        containing numpy arrays.

    
        Parameters
        -----------
        hash_name: 'md5' or 'sha1'
            Hashing algorithm used. sha1 is supposedly safer, but md5 is 
            faster.
        coerce_mmap: boolean
            Make no difference between np.memmap and np.ndarray
    """
    if 'numpy' in sys.modules:
        hasher = NumpyHasher(hash_name=hash_name, coerce_mmap=coerce_mmap)
    else:
        hasher = Hasher(hash_name=hash_name)
    return hasher.hash(obj)




"""
Small utilities for testing.
"""
import nose

# A decorator to run tests only when numpy is available
try:
    import numpy as np
    def with_numpy(func):
        """ A decorator to skip tests requiring numpy.
        """
        return func

except ImportError:    
    def with_numpy(func):
        """ A decorator to skip tests requiring numpy.
        """
        def my_func():
            raise nose.SkipTest('Test requires numpy')
        return my_func
    np = None



"""Package for modules that deal with feature extraction from raw data"""

# Author: Olivier Grisel <olivier.grisel@ensta.org>
#
# License: BSD Style.
"""Utilities to build feature vectors from text documents"""

from collections import defaultdict
import re
import unicodedata
import numpy as np
import scipy.sparse as sp

ENGLISH_STOP_WORDS = set([
    "a", "about", "above", "across", "after", "afterwards", "again", "against",
    "all", "almost", "alone", "along", "already", "also", "although", "always",
    "am", "among", "amongst", "amoungst", "amount", "an", "and", "another",
    "any", "anyhow", "anyone", "anything", "anyway", "anywhere", "are",
    "around", "as", "at", "back", "be", "became", "because", "become",
    "becomes", "becoming", "been", "before", "beforehand", "behind", "being",
    "below", "beside", "besides", "between", "beyond", "bill", "both", "bottom",
    "but", "by", "call", "can", "cannot", "cant", "co", "computer", "con",
    "could", "couldnt", "cry", "de", "describe", "detail", "do", "done", "down",
    "due", "during", "each", "eg", "eight", "either", "eleven", "else",
    "elsewhere", "empty", "enough", "etc", "even", "ever", "every", "everyone",
    "everything", "everywhere", "except", "few", "fifteen", "fify", "fill",
    "find", "fire", "first", "five", "for", "former", "formerly", "forty",
    "found", "four", "from", "front", "full", "further", "get", "give", "go",
    "had", "has", "hasnt", "have", "he", "hence", "her", "here", "hereafter",
    "hereby", "herein", "hereupon", "hers", "herself", "him", "himself", "his",
    "how", "however", "hundred", "i", "ie", "if", "in", "inc", "indeed",
    "interest", "into", "is", "it", "its", "itself", "keep", "last", "latter",
    "latterly", "least", "less", "ltd", "made", "many", "may", "me",
    "meanwhile", "might", "mill", "mine", "more", "moreover", "most", "mostly",
    "move", "much", "must", "my", "myself", "name", "namely", "neither", "never",
    "nevertheless", "next", "nine", "no", "nobody", "none", "noone", "nor",
    "not", "nothing", "now", "nowhere", "of", "off", "often", "on", "once",
    "one", "only", "onto", "or", "other", "others", "otherwise", "our", "ours",
    "ourselves", "out", "over", "own", "part", "per", "perhaps", "please",
    "put", "rather", "re", "same", "see", "seem", "seemed", "seeming", "seems",
    "serious", "several", "she", "should", "show", "side", "since", "sincere",
    "six", "sixty", "so", "some", "somehow", "someone", "something", "sometime",
    "sometimes", "somewhere", "still", "such", "system", "take", "ten", "than",
    "that", "the", "their", "them", "themselves", "then", "thence", "there",
    "thereafter", "thereby", "therefore", "therein", "thereupon", "these",
    "they", "thick", "thin", "third", "this", "those", "though", "three",
    "through", "throughout", "thru", "thus", "to", "together", "too", "top",
    "toward", "towards", "twelve", "twenty", "two", "un", "under", "until",
    "up", "upon", "us", "very", "via", "was", "we", "well", "were", "what",
    "whatever", "when", "whence", "whenever", "where", "whereafter", "whereas",
    "whereby", "wherein", "whereupon", "wherever", "whether", "which", "while",
    "whither", "who", "whoever", "whole", "whom", "whose", "why", "will",
    "with", "within", "without", "would", "yet", "you", "your", "yours",
    "yourself", "yourselves"])


def strip_accents(s):
    """Transform accentuated unicode symbols into their simple counterpart"""
    return ''.join((c for c in unicodedata.normalize('NFD', s)
                    if unicodedata.category(c) != 'Mn'))


class WordNGramAnalyzer(object):
    """Simple analyzer: transform a text document into a sequence of word tokens

    This simple implementation does:
      - lower case conversion
      - unicode accents removal
      - token extraction using unicode regexp word bounderies for token of
        minimum size of 2 symbols
      - output token n-grams (unigram only by default)
    """

    token_pattern = re.compile(r"\b\w\w+\b", re.U)

    def __init__(self, default_charset='utf-8', min_n=1, max_n=1,
                 stop_words=None):
        self.charset = default_charset
        self.stop_words = stop_words
        self.min_n = min_n
        self.max_n = max_n

    def analyze(self, text_document):
        if isinstance(text_document, str):
            text_document = text_document.decode(self.charset, 'ignore')

        # lowercasing and accents removal
        text_document = strip_accents(text_document.lower())

        # word boundaries tokenizer
        tokens = self.token_pattern.findall(text_document)

        # handle token n-grams
        if self.min_n != 1 or self.max_n != 1:
            original_tokens = tokens
            tokens = []
            n_original_tokens = len(original_tokens)
            for n in xrange(self.min_n, self.max_n + 1):
                if n_original_tokens < n:
                    continue
                for i in xrange(n_original_tokens - n + 1):
                    tokens.append(" ".join(original_tokens[i: i + n]))

        # handle stop words
        if self.stop_words is not None:
            tokens = [w for w in tokens if w not in self.stop_words]

        return tokens


class CharNGramAnalyzer(object):
    """Compute character n-grams features of a text document

    This analyzer is interesting since it is language agnostic and will work
    well even for language where word segmentation is not as trivial as English
    such as Chinese and German for instance.

    Because of this, it can be considered a basic morphological analyzer.
    """

    white_spaces = re.compile(r"\s\s+")

    def __init__(self, default_charset='utf-8', min_n=3, max_n=6):
        self.charset = default_charset
        self.min_n = min_n
        self.max_n = max_n

    def analyze(self, text_document):
        if isinstance(text_document, str):
            text_document = text_document.decode(self.charset, 'ignore')
        text_document = strip_accents(text_document.lower())

        # normalize white spaces
        text_document = self.white_spaces.sub(" ", text_document)

        text_len = len(text_document)
        ngrams = []
        for n in xrange(self.min_n, self.max_n + 1):
            if text_len < n:
                continue
            for i in xrange(text_len - n):
                ngrams.append(text_document[i: i + n])
        return ngrams


DEFAULT_ANALYZER = WordNGramAnalyzer(min_n=1, max_n=1)


class HashingVectorizer(object):
    """Compute term frequencies vectors using hashed term space

    See the Hashing-trick related papers referenced by John Langford on this
    page to get a grasp on the usefulness of this representation:

      http://hunch.net/~jl/projects/hash_reps/index.html

    dim is the number of buckets, higher dim means lower collision rate but
    also higher memory requirements and higher processing times on the
    resulting tfidf vectors.

    Documents is a sequence of lists of tokens to initialize the DF estimates.

    TODO handle bigrams in a smart way such as demonstrated here:

      http://streamhacker.com/2010/05/24/text-classification-sentiment-analysis-stopwords-collocations/

    """
    # TODO: implement me using the murmurhash that might be faster: but profile
    # me first :)

    def __init__(self, dim=5000, probes=1, use_idf=True,
                 analyzer=DEFAULT_ANALYZER):
        self.dim = dim
        self.probes = probes
        self.analyzer = analyzer
        self.use_idf = use_idf

        # start counts at one to avoid zero division while
        # computing IDF
        self.df_counts = np.ones(dim, dtype=long)
        self.tf_vectors = None

    def hash_sign(self, token, probe=0):
        """Compute the hash of token with number proble and hashed sign"""
        h = hash(token + (probe * u"#"))
        return abs(h) % self.dim, 1.0 if h % 2 == 0 else -1.0

    def _sample_document(self, text, tf_vector, update_estimates=True):
        """Extract features from text and update running freq estimates"""
        tokens = self.analyzer.analyze(text)
        for token in tokens:
            # TODO add support for cooccurence tokens in a sentence
            # window
            for probe in xrange(self.probes):
                i, incr = self.hash_sign(token, probe)
                tf_vector[i] += incr
        tf_vector /= len(tokens) * self.probes

        if update_estimates and self.use_idf:
            # update the running DF estimate
            self.df_counts += tf_vector != 0.0
        return tf_vector

    def get_idf(self):
        n_samples = float(len(self.tf_vectors))
        return np.log(n_samples / self.df_counts)

    def get_tfidf(self):
        """Compute the TF-log(IDF) vectors of the sampled documents"""
        if self.tf_vectors is None:
            return None
        return self.tf_vectors * self.get_idf()

    def vectorize(self, text_documents):
        """Vectorize a batch of documents in python utf-8 strings or unicode"""
        tf_vectors = np.zeros((len(text_documents), self.dim))
        for i, text in enumerate(text_documents):
            self._sample_document(text, tf_vectors[i])

        if self.tf_vectors is None:
            self.tf_vectors = tf_vectors
        else:
            self.tf_vectors = np.vstack((self.tf_vectors, tf_vectors))

    def vectorize_files(self, document_filepaths):
        """Vectorize a batch of documents stored in utf-8 text files"""
        tf_vectors = np.zeros((len(document_filepaths), self.dim))
        for i, filepath in enumerate(document_filepaths):
            self._sample_document(file(filepath).read(), tf_vectors[i])

        if self.tf_vectors is None:
            self.tf_vectors = tf_vectors
        else:
            self.tf_vectors = np.vstack((self.tf_vectors, tf_vectors))

    def get_vectors(self):
        if self.use_idf:
            return self.get_tfidf()
        else:
            return self.tf_vectors


class SparseHashingVectorizer(object):
    """Compute term freq vectors using hashed term space in a sparse matrix

    The logic is the same as HashingVectorizer but it is possible to use much
    larger dimension vectors without memory issues thanks to the usage of
    scipy.sparse datastructure to store the tf vectors.
    """

    def __init__(self, dim=100000, probes=1, use_idf=True,
                 analyzer=DEFAULT_ANALYZER):
        self.dim = dim
        self.probes = probes
        self.analyzer = analyzer
        self.use_idf = use_idf

        # start counts at one to avoid zero division while
        # computing IDF
        self.df_counts = np.ones(dim, dtype=long)
        self.tf_vectors = None

    def hash_sign(self, token, probe=0):
        h = hash(token + (probe * u"#"))
        return abs(h) % self.dim, 1.0 if h % 2 == 0 else -1.0

    def _sample_document(self, text, tf_vectors, idx=0, update_estimates=True):
        """Extract features from text and update running freq estimates"""

        tokens = self.analyzer.analyze(text)
        counts = defaultdict(lambda: 0.0)
        for token in tokens:
            # TODO add support for cooccurence tokens in a sentence
            # window
            for probe in xrange(self.probes):
                i, incr = self.hash_sign(token, probe)
                counts[i] += incr
        for k, v in counts.iteritems():
            if v == 0.0:
                # can happen if equally frequent conflicting features
                continue
            tf_vectors[idx, k] = v / (len(tokens) * self.probes)

            if update_estimates and self.use_idf:
                # update the running DF estimate
                self.df_counts[k] += 1

    def get_idf(self):
        n_samples = float(self.tf_vectors.shape[0])
        return np.log(n_samples / self.df_counts)

    def get_tfidf(self):
        """Compute the TF-log(IDF) vectors of the sampled documents"""
        coo = self.tf_vectors.tocoo()
        tf_idf = sp.lil_matrix(coo.shape)
        idf = self.get_idf()
        data, row, col = coo.data, coo.row, coo.col
        for i in xrange(len(data)):
            tf_idf[row[i], col[i]] = data[i] * idf[col[i]]
        return tf_idf.tocsr()

    def vectorize(self, text_documents):
        """Vectorize a batch of documents in python utf-8 strings or unicode"""
        tf_vectors = sp.dok_matrix((len(text_documents), self.dim))
        for i, text in enumerate(text_documents):
            self._sample_document(text, tf_vectors, i)

        if self.tf_vectors is None:
            self.tf_vectors = tf_vectors
        else:
            self.tf_vectors = sp.vstack((self.tf_vectors, tf_vectors))

    def vectorize_files(self, document_filepaths):
        """Vectorize a batch of utf-8 text files"""
        tf_vectors = sp.dok_matrix((len(document_filepaths), self.dim))
        for i, filepath in enumerate(document_filepaths):
            self._sample_document(file(filepath).read(), tf_vectors, i)

        if self.tf_vectors is None:
            self.tf_vectors = tf_vectors
        else:
            self.tf_vectors = sp.vstack((self.tf_vectors, tf_vectors))

    def get_vectors(self):
        if self.use_idf:
            return self.get_tfidf()
        else:
            return self.tf_vectors



"""
Utilities to extract features from images.
"""

# Authors: Emmanuelle Gouillart <emmanuelle.gouillart@normalesup.org>
#          Gael Varoquaux <gael.varoquaux@normalesup.org>
# License: BSD

import numpy as np
from scipy import sparse
from ..utils.fixes import in1d

################################################################################
# From an image to a graph

def _make_edges_3d(n_x, n_y, n_z=1):
    """ Returns a list of edges for a 3D image.
    
        Parameters
        ===========
        n_x: integer
            The size of the grid in the x direction.
        n_y: integer
            The size of the grid in the y direction.
        n_z: integer, optional
            The size of the grid in the z direction, defaults to 1
    """
    vertices = np.arange(n_x*n_y*n_z).reshape((n_x, n_y, n_z))
    edges_deep = np.vstack((vertices[:, :, :-1].ravel(),
                            vertices[:, :, 1:].ravel()))
    edges_right = np.vstack((vertices[:, :-1].ravel(), vertices[:, 1:].ravel()))
    edges_down = np.vstack((vertices[:-1].ravel(), vertices[1:].ravel()))
    edges = np.hstack((edges_deep, edges_right, edges_down))
    return edges


def _compute_gradient_3d(edges, img):
    n_x, n_y, n_z = img.shape
    gradient = np.abs(img[edges[0]/(n_y*n_z), \
                                (edges[0] % (n_y*n_z))/n_z, \
                                (edges[0] % (n_y*n_z))%n_z] - \
                           img[edges[1]/(n_y*n_z), \
                                (edges[1] % (n_y*n_z))/n_z, \
                                (edges[1] % (n_y*n_z)) % n_z])
    return gradient


# XXX: Why mask the image after computing the weights?

def _mask_edges_weights(mask, edges, weights):
    """ Given a image mask and the 
    """
    inds = np.arange(mask.size)
    inds = inds[mask.ravel()]
    ind_mask = np.logical_and(in1d(edges[0], inds),
                              in1d(edges[1], inds))
    edges, weights = edges[:, ind_mask], weights[ind_mask]
    maxval = edges.max()
    order = np.searchsorted(np.unique(edges.ravel()), np.arange(maxval+1))
    edges = order[edges]
    return edges, weights


def img_to_graph(img, mask=None,
                    return_as=sparse.coo_matrix):
    """ Create a graph of the pixel-to-pixel connections with the
        gradient of the image as a the edge value.

        Parameters
        ===========
        img: ndarray, 2D or 3D
            2D or 3D image
        mask : ndarray of booleans, optional
            An optional mask of the image, to consider only part of the 
            pixels.
        return_as: np.ndarray or a sparse matrix class, optional
            The class to use to build the returned adjacency matrix.
    """
    img = np.atleast_3d(img)
    n_x, n_y, n_z = img.shape
    edges   = _make_edges_3d(n_x, n_y, n_z)
    weights = _compute_gradient_3d(edges, img)
    if mask is not None:
        edges, weights = _mask_edges_weights(mask, edges, weights)
        img = img.squeeze()[mask]
    else:
        img = img.ravel()
    n_voxels = img.size
    diag_idx = np.arange(n_voxels)
    i_idx = np.hstack((edges[0], edges[1]))
    j_idx = np.hstack((edges[1], edges[0]))
    graph = sparse.coo_matrix((np.hstack((weights, weights, img)),
                              (np.hstack((i_idx, diag_idx)),
                               np.hstack((j_idx, diag_idx)))),
                              shape=(n_voxels, n_voxels))
    if return_as is np.ndarray:
        return graph.todense()
    return return_as(graph)




"""Compressed Sparse graph algorithms"""
# Backported from scipy 0.9: scipy.sparse.csgraph

__docformat__ = "restructuredtext en"

__all__ = ['cs_graph_components']

import numpy as np

from sparsetools import cs_graph_components as _cs_graph_components

from scipy.sparse.csr import csr_matrix
from scipy.sparse.base import isspmatrix

_msg0 = 'x must be a symmetric square matrix!'
_msg1 = _msg0 + '(has shape %s)'

def cs_graph_components(x):
    """
    Determine connected compoments of a graph stored as a compressed sparse row
    or column matrix. For speed reasons, the symmetry of the matrix x is not
    checked.

    Parameters
    -----------
    x: ndarray-like, 2 dimensions, or sparse matrix
        The adjacency matrix of the graph. Only the upper triangular part
        is used.

    Returns
    --------
    n_comp: int
        The number of connected components.
    label: ndarray (ints, 1 dimension):
        The label array of each connected component (-2 is used to
        indicate empty rows: 0 everywhere, including diagonal).

    Notes
    ------

    The matrix is assumed to be symmetric and the upper triangular part
    of the matrix is used. The matrix is converted to a CSR matrix unless
    it is already a CSR.

    Example
    -------

    >>> from scipy.sparse import cs_graph_components
    >>> import numpy as np
    >>> D = np.eye(4)
    >>> D[0,1] = D[1,0] = 1
    >>> cs_graph_components(D)
    (3, array([0, 0, 1, 2]))
    >>> from scipy.sparse import dok_matrix 
    >>> cs_graph_components(dok_matrix(D))
    (3, array([0, 0, 1, 2]))

    """
    try:
        shape = x.shape
    except AttributeError:
        raise ValueError(_msg0)
    
    if not ((len(x.shape) == 2) and (x.shape[0] == x.shape[1])):
        raise ValueError(_msg1 % x.shape)

    if isspmatrix(x):
        x = x.tocsr()
    else:
        x = csr_matrix(x)
    
    label = np.empty((shape[0],), dtype=x.indptr.dtype)

    n_comp = _cs_graph_components(shape[0], x.indptr, x.indices, label)

    return n_comp, label



"""
Fixes for older version of numpy and scipy.
"""
# Authors: Emmanuelle Gouillart <emmanuelle.gouillart@normalesup.org>
#          Gael Varoquaux <gael.varoquaux@normalesup.org>
# License: BSD

import numpy as np

def unique(ar, return_index=False, return_inverse=False):
    """ A replacement for np.unique that appeared in numpy 1.4.
    """
    try:
        ar = ar.flatten()
    except AttributeError:
        if not return_inverse and not return_index:
            items = sorted(set(ar))
            return np.asarray(items)
        else:
            ar = np.asanyarray(ar).flatten()
    
    if ar.size == 0:
        if return_inverse and return_index:
            return ar, np.empty(0, np.bool), np.empty(0, np.bool)
        elif return_inverse or return_index:
            return ar, np.empty(0, np.bool)
        else: 
            return ar
        
    if return_inverse or return_index:
        perm = ar.argsort()
        aux = ar[perm]
        flag = np.concatenate(([True], aux[1:] != aux[:-1]))
        if return_inverse:
            iflag = np.cumsum(flag) - 1
            iperm = perm.argsort()
            if return_index:
                return aux[flag], perm[flag], iflag[iperm]
            else:
                return aux[flag], iflag[iperm]
        else:
            return aux[flag], perm[flag]

    else:
        ar.sort()
        flag = np.concatenate(([True], ar[1:] != ar[:-1]))
        return ar[flag]


def _in1d(ar1, ar2, assume_unique=False):
    """ Replacement for in1d that is provided for numpy >= 1.4
    """
    if not assume_unique:
        ar1, rev_idx = unique(ar1, return_inverse=True)
        ar2 = np.unique(ar2)
    ar = np.concatenate( (ar1, ar2) )
    # We need this to be a stable sort, so always use 'mergesort'
    # here. The values from the first array should always come before
    # the values from the second array.
    order = ar.argsort(kind='mergesort')
    sar = ar[order]
    equal_adj = (sar[1:] == sar[:-1])
    flag = np.concatenate( (equal_adj, [False] ) )
    indx = order.argsort(kind='mergesort')[:len( ar1 )]

    if assume_unique:
        return flag[indx]
    else:
        return flag[indx][rev_idx]


if np.__version__ >= '1.4':
    from numpy import in1d
else:
    in1d = _in1d




"""
Graph utilities and algorithms

Graphs are represented with their adjacency matrices, preferably using 
sparse matrices.
"""

# Authors: Aric Hagberg <hagberg@lanl.gov> 
#          Gael Varoquaux <gael.varoquaux@normalesup.org>
# License: BSD

import numpy as np
from scipy import sparse

################################################################################
# Path and connected component analysis.
# Code adapted from networkx

def single_source_shortest_path_length(graph, source, cutoff=None):
    """Return the shortest path length from source to all reachable nodes.

    Returns a dictionary of shortest path lengths keyed by target.

    Parameters
    ----------
    graph: sparse matrix or 2D array (preferably LIL matrix)
        Adjency matrix of the graph
    source : node label
       Starting node for path
    cutoff : integer, optional
        Depth to stop the search - only
        paths of length <= cutoff are returned.

    Examples
    --------
    >>> import numpy as np
    >>> graph = np.array([[ 0, 1, 0, 0],
    ...                   [ 1, 0, 1, 0],
    ...                   [ 0, 1, 0, 1],
    ...                   [ 0, 0, 1, 0]])
    >>> single_source_shortest_path_length(graph, 0)
    {0: 0, 1: 1, 2: 2, 3: 3}
    >>> single_source_shortest_path_length(np.ones((6, 6)), 2)
    {2: 0, 3: 1, 4: 1, 5: 1}
    """
    if sparse.isspmatrix(graph):
        graph = graph.tolil()
    else:
        graph = sparse.lil_matrix(graph)
    seen = {}                  # level (number of hops) when seen in BFS
    level = 0                  # the current level
    next_level = [source]    # dict of nodes to check at next level
    while next_level:
        this_level = next_level  # advance to next level
        next_level = set()       # and start a new list (fringe)
        for v in this_level:
            if v not in seen: 
                seen[v] = level # set the level of vertex v
                neighbors = np.array(graph.rows[v])
                # Restrict to the upper triangle
                neighbors = neighbors[neighbors > v]
                next_level.update(neighbors) 
        if cutoff is not None and cutoff <= level:
            break
        level += 1
    return seen  # return all path lengths as dictionary


if hasattr(sparse, 'cs_graph_components'):
    cs_graph_components = sparse.cs_graph_components
else:
    from ._csgraph import cs_graph_components


################################################################################
# Graph laplacian
def _graph_laplacian_sparse(graph, normed=False, return_diag=False):
    n_nodes = graph.shape[0]
    if not graph.format == 'coo':
        lap = -graph.tocoo()
    else:
        lap = -graph.copy()
    diag_mask = (lap.row == lap.col)
    if not diag_mask.sum() == n_nodes:
        # The sparsity pattern of the matrix has holes on the diagonal,
        # we need to fix that
        diag_idx = lap.row[diag_mask]
        lap = lap.tolil()
        diagonal_holes = list(set(range(n_nodes)).difference(
                                diag_idx))
        lap[diagonal_holes, diagonal_holes] = 1
        lap = lap.tocoo()
        diag_mask = (lap.row == lap.col)
    lap.data[diag_mask] = 0
    w = -np.asarray(lap.sum(axis=1)).squeeze()
    if normed:
        w = np.sqrt(w)
        w_zeros = w == 0
        w[w_zeros] = 1
        lap.data /= w[lap.row]
        lap.data /= w[lap.col]
        lap.data[diag_mask] = (1-w_zeros).astype(lap.data.dtype)
    else:
        lap.data[diag_mask] = w[lap.row[diag_mask]]
    if return_diag:
        return lap, w
    return lap


def _graph_laplacian_dense(graph, normed=False, return_diag=False):
    n_nodes = graph.shape[0]
    lap = -graph.copy()
    lap.flat[::n_nodes+1] = 0
    w = -lap.sum(axis=0)
    if normed:
        w = np.sqrt(w)
        w_zeros = w == 0
        w[w_zeros] = 1
        lap /= w
        lap /= w[:, np.newaxis]
        lap.flat[::n_nodes+1] = 1-w_zeros
    else:
        lap.flat[::n_nodes+1] = w
    if return_diag:
        return lap, w
    return lap
    

def graph_laplacian(graph, normed=False, return_diag=False):
    if normed and (np.issubdtype(graph.dtype, np.int)
                    or np.issubdtype(graph.dtype, np.uint)):
        graph = graph.astype(np.float)
    if sparse.isspmatrix(graph):
        return _graph_laplacian_sparse(graph, normed=normed,
                                       return_diag=return_diag)
    else:
        # We have a numpy array
        return _graph_laplacian_dense(graph, normed=normed,
                                       return_diag=return_diag)
 


def configuration(parent_package='',top_path=None):
    import numpy
    from numpy.distutils.misc_util import Configuration

    config = Configuration('utils', parent_package, top_path)

    config.add_subpackage('sparsetools')

    return config


import sys
import math
import numpy as np

#XXX: We should have a function with numpy's slogdet API
def _fast_logdet(A):
    """
    Compute log(det(A)) for A symmetric
    Equivalent to : np.log(nl.det(A))
    but more robust
    It returns -Inf if det(A) is non positive or is not defined.
    """
    # XXX: Should be implemented as in numpy, using ATLAS
    # http://projects.scipy.org/numpy/browser/trunk/numpy/linalg/linalg.py#L1559
    ld = np.sum(np.log(np.diag(A)))
    a = np.exp(ld/A.shape[0])
    d = np.linalg.det(A/a)
    ld += np.log(d)
    if not np.isfinite(ld):
        return -np.inf
    return ld

def _fast_logdet_numpy(A):
    """
    Compute log(det(A)) for A symmetric
    Equivalent to : np.log(nl.det(A))
    but more robust
    It returns -Inf if det(A) is non positive or is not defined.
    """
    sign, ld = np.linalg.slogdet(A)
    if not sign > 0:
        return -np.inf
    return ld


# Numpy >= 1.5 provides a fast logdet
if hasattr(np.linalg, 'slogdet'):
    fast_logdet = _fast_logdet_numpy
else:
    fast_logdet = _fast_logdet

if sys.version_info[1] < 6:
    # math.factorial is only available in 2.6
    def factorial(x) :
        # simple recursive implementation
        if x == 0: return 1
        return x * factorial(x-1)
else:
    factorial = math.factorial


if sys.version_info[1] < 6:
    def combinations(seq, r=None):
        """Generator returning combinations of items from sequence <seq>
        taken <r> at a time. Order is not significant. If <r> is not given,
        the entire sequence is returned.
        """
        if r == None:
            r = len(seq)
        if r <= 0:
            yield []
        else:
            for i in xrange(len(seq)):
                for cc in combinations(seq[i+1:], r-1):
                    yield [seq[i]]+cc

else:
    import itertools
    combinations = itertools.combinations



def density(w, **kwargs):
    """Compute density of a sparse vector
        Return a value between 0 and 1
    """
    d = 0 if w is None else float((w != 0).sum()) / w.size
    return d

# This file was automatically generated by SWIG (http://www.swig.org).
# Version 1.3.40
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.
# This file is compatible with both classic and new-style classes.

from sys import version_info
if version_info >= (2,6,0):
    def swig_import_helper():
        from os.path import dirname
        import imp
        fp = None
        try:
            fp, pathname, description = imp.find_module('_csgraph', [dirname(__file__)])
        except ImportError:
            import _csgraph
            return _csgraph
        if fp is not None:
            try:
                _mod = imp.load_module('_csgraph', fp, pathname, description)
            finally:
                fp.close()
            return _mod
    _csgraph = swig_import_helper()
    del swig_import_helper
else:
    import _csgraph
del version_info
try:
    _swig_property = property
except NameError:
    pass # Python < 2.2 doesn't have 'property'.
def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
    if (name == "thisown"): return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'SwigPyObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    if (not static) or hasattr(self,name):
        self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)

def _swig_setattr(self,class_type,name,value):
    return _swig_setattr_nondynamic(self,class_type,name,value,0)

def _swig_getattr(self,class_type,name):
    if (name == "thisown"): return self.this.own()
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError(name)

def _swig_repr(self):
    try: strthis = "proxy of " + self.this.__repr__()
    except: strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

try:
    _object = object
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0



def cs_graph_components(*args):
  """cs_graph_components(int n_nod, int Ap, int Aj, int flag) -> int"""
  return _csgraph.cs_graph_components(*args)



"""sparsetools - a collection of routines for sparse matrix operations
"""

from csgraph import cs_graph_components


def configuration(parent_package='',top_path=None):
    import numpy
    from numpy.distutils.misc_util import Configuration

    config = Configuration('sparsetools',parent_package,top_path)

    fmt = 'csgraph'
    sources = [ fmt + '_wrap.cxx' ]
    depends = [ fmt + '.h' ]
    config.add_extension('_' + fmt, sources=sources,
                         define_macros=[('__STDC_FORMAT_MACROS', 1)], 
                         depends=depends)

    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())



"""
Feature slection module for python.
"""
from .univariate_selection import (f_classif, f_regression, 
                                    SelectPercentile, SelectKBest,
                                    SelectFpr, SelectFdr, SelectFwe,
                                    GenericUnivariateSelect)

"""
Univariate features selection.
"""

# Authors: V. Michel, B. Thirion, G. Varoquaux, A. Gramfort, E. Duchesnay
# License: BSD 3 clause

import numpy as np
from scipy import stats

from ..base import BaseEstimator

######################################################################
# Scoring functions
######################################################################

def f_classif(X, y):
    """
    Compute the Anova F-value for the provided sample

    Parameters
    ----------
    X : array of shape (n_samples, n_features)
        the set of regressors sthat will tested sequentially
    y : array of shape(n_samples)
        the data matrix

    Returns
    -------
    F : array of shape (m),
        the set of F values
    pval : array of shape(m),
        the set of p-values
    """
    X = np.asanyarray(X)
    args = [X[y==k] for k in np.unique(y)]
    return stats.f_oneway(*args)


def f_regression(X, y, center=True):
    """
    Quick linear model for testing the effect of a single regressor,
    sequentially for many regressors
    This is done in 3 steps:
    1. the regressor of interest and the data are orthogonalized
    wrt constant regressors
    2. the cross correlation between data and regressors is computed
    3. it is converted to an F score then to a p-value

    Parameters
    ----------
    X : array of shape (n_samples, n_features)
        the set of regressors sthat will tested sequentially
    y : array of shape(n_samples)
        the data matrix

    center : True, bool,
        If true, X and y are centered

    Returns
    -------
    F : array of shape (m),
        the set of F values
    pval : array of shape(m)
        the set of p-values
    """

    # orthogonalize everything wrt to confounds
    y = y.copy()
    X = X.copy()
    if center:
        y -= np.mean(y)
        X -= np.mean(X, 0)

    # compute the correlation
    X /= np.sqrt(np.sum(X**2,0))
    y /= np.sqrt(np.sum(y**2))
    corr = np.dot(y, X)

    # convert to p-value
    dof = y.size-2
    F = corr**2/(1-corr**2)*dof
    pv = stats.f.sf(F, 1, dof)
    return F, pv


######################################################################
# General class for filter univariate selection
######################################################################


class _AbstractUnivariateFilter(BaseEstimator):
    """ Abstract class, not meant to be used directly
    """

    def __init__(self, score_func):
        """ Initialize the univariate feature selection.

        Parameters
        ===========
        score_func: callable
            function taking two arrays X and y, and returning 2 arrays:
            both scores and pvalues
        """
        assert callable(score_func), ValueError(
                "The score function should be a callable, '%s' (type %s) "
                "was passed." % (score_func, type(score_func))
            )
        self.score_func = score_func


    def fit(self, X, y):
        """
        Evaluate the function
        """
        _scores = self.score_func(X, y)
        self._scores = _scores[0]
        self._pvalues = _scores[1]
        return self


    def transform(self, X, **params):
        """
        Transform a new matrix using the selected features
        """
        self._set_params(**params)
        return X[:, self.get_support()]


######################################################################
# Specific filters
######################################################################

class SelectPercentile(_AbstractUnivariateFilter):
    """
    Filter : Select the best percentile of the p_values
    """

    def __init__(self, score_func, percentile=10):
        """ Initialize the univariate feature selection.

        Parameters
        ===========
        score_func: callable
            function taking two arrays X and y, and returning 2 arrays:
            both scores and pvalues
        percentile: int, optional
            percent of features to keep
        """
        self.percentile = percentile
        _AbstractUnivariateFilter.__init__(self, score_func)

    def get_support(self):
        percentile = self.percentile
        assert percentile<=100, ValueError('percentile should be \
                            between 0 and 100 (%f given)' %(percentile))
        alpha = stats.scoreatpercentile(self._pvalues, percentile)
        return (self._pvalues <= alpha)


class SelectKBest(_AbstractUnivariateFilter):
    """
    Filter : Select the k lowest p-values
    """
    def __init__(self, score_func, k=10):
        """ Initialize the univariate feature selection.

        Parameters
        ===========
        score_func: callable
            function taking two arrays X and y, and returning 2 arrays:
            both scores and pvalues
        percentile: int, optional
            percent of features to keep
        """
        self.k = k
        _AbstractUnivariateFilter.__init__(self, score_func)

    def get_support(self):
        k = self.k
        assert k<=len(self._pvalues), ValueError('cannot select %d features'
                                    ' among %d ' % (k, len(self._pvalues)))
        alpha = np.sort(self._pvalues)[k-1]
        return (self._pvalues <= alpha)


class SelectFpr(_AbstractUnivariateFilter):
    """
    Filter : Select the pvalues below alpha
    """
    def __init__(self, score_func, alpha=5e-2):
        """ Initialize the univariate feature selection.

        Parameters
        ===========
        score_func: callable
            function taking two arrays X and y, and returning 2 arrays:
            both scores and pvalues
        alpha: float, optional
            the highest p-value for features to keep
        """
        self.alpha = alpha
        _AbstractUnivariateFilter.__init__(self, score_func)

    def get_support(self):
        alpha = self.alpha
        return (self._pvalues < alpha)


class SelectFdr(_AbstractUnivariateFilter):
    """
    Filter : Select the p-values corresponding to an estimated false
    discovery rate of alpha. This uses the Benjamini-Hochberg procedure
    """
    def __init__(self, score_func, alpha=5e-2):
        """ Initialize the univariate feature selection.

        Parameters
        ===========
        score_func: callable
            function taking two arrays X and y, and returning 2 arrays:
            both scores and pvalues
        alpha: float, optional
            the highest uncorrected p-value for features to keep
        """
        self.alpha = alpha
        _AbstractUnivariateFilter.__init__(self, score_func)

    def get_support(self):
        alpha = self.alpha
        sv = np.sort(self._pvalues)
        threshold = sv[sv < alpha*np.arange(len(self._pvalues))].max()
        return (self._pvalues < threshold)


class SelectFwe(_AbstractUnivariateFilter):
    """
    Filter : Select the p-values corresponding to a corrected p-value of alpha
    """
    def __init__(self, score_func, alpha=5e-2):
        """ Initialize the univariate feature selection.

        Parameters
        ===========
        score_func: callable
            function taking two arrays X and y, and returning 2 arrays:
            both scores and pvalues
        alpha: float, optional
            the highest uncorrected p-value for features to keep
        """
        self.alpha = alpha
        _AbstractUnivariateFilter.__init__(self, score_func)

    def get_support(self):
        alpha = self.alpha
        return (self._pvalues < alpha/len(self._pvalues))


######################################################################
# Generic filter
######################################################################

class GenericUnivariateSelect(_AbstractUnivariateFilter):
    _selection_modes = {'percentile':   SelectPercentile,
                        'k_best':       SelectKBest,
                        'fpr':          SelectFpr,
                        'fdr':          SelectFdr,
                        'fwe':          SelectFwe,
                        }

    def __init__(self, score_func, mode='percentile', param=1e-5):
        """ Initialize the univariate feature selection.

        Parameters
        ===========
        score_func: callable
            Function taking two arrays X and y, and returning 2 arrays:
            both scores and pvalues
        mode: {%s}
            Feature selection mode
        param: float or int depending on the feature selection mode
            Parameter of the corresponding mode
        """ % self._selection_modes.keys()
        assert callable(score_func), ValueError(
                "The score function should be a callable, '%s' (type %s) "
                "was passed." % (score_func, type(score_func))
            )
        assert mode in self._selection_modes, ValueError(
                "The mode passed should be one of %s, '%s', (type %s) "
                "was passed." % (
                        self._selection_modes.keys(),
                        mode, type(mode)))
        self.score_func = score_func
        self.mode = mode
        self.param = param


    def get_support(self):
        selector = self._selection_modes[self.mode](lambda x:x)
        selector._pvalues = self._pvalues
        selector._scores  = self._scores
        # Now make some acrobaties to set the right named parameter in
        # the selector
        possible_params = selector._get_param_names()
        possible_params.remove('score_func')
        selector._set_params(**{possible_params[0]: self.param})
        return selector.get_support()





"""
To run this, you'll need to have installed.

  * pymvpa
  * libsvm and it's python bindings
  * scikit-learn (of course)

Does two benchmarks

First, we fix a training set, increase the number of
samples to classify and plot number of classified samples as a
function of time.

In the second benchmark, we increase the number of dimensions of the
training set, classify a sample and plot the time taken as a function of the number of dimensions.
"""
import numpy as np
import pylab as pl
import gc
from datetime import datetime

# to store the results
scikit_results = []
svm_results = []
mvpa_results = []

mu_second = 0.0 + 10**6 # number of microseconds in a second

def bench_scikit(X, Y, T):
    """
    bench with scikit-learn bindings on libsvm
    """
    import scikits.learn
    from scikits.learn.svm import SVC

    gc.collect()

    # start time
    tstart = datetime.now()
    clf = SVC(kernel='linear');
    clf.fit(X, Y);
    Z = clf.predict(T)
    delta = (datetime.now() - tstart)
    # stop time

    scikit_results.append(delta.seconds + delta.microseconds/mu_second)

def bench_svm(X, Y, T):
    """
    bench with swig-generated wrappers that come with libsvm
    """

    import svm

    X1 = X.tolist()
    Y1 = Y.tolist()
    T1 = T.tolist()

    gc.collect()

    # start time
    tstart = datetime.now()
    problem = svm.svm_problem(Y1, X1)
    param = svm.svm_parameter(svm_type=0, kernel_type=0)
    model = svm.svm_model(problem, param)
    for i in T.tolist():
        model.predict(i)
    delta = (datetime.now() - tstart)
    # stop time
    svm_results.append(delta.seconds + delta.microseconds/mu_second)

def bench_pymvpa(X, Y, T):
    """
    bench with pymvpa (by default uses a custom swig-generated wrapper
    around libsvm)
    """
    from mvpa.datasets import Dataset
    from mvpa.clfs import svm
    data = Dataset(samples=X, labels=Y)

    gc.collect()

    # start time
    tstart = datetime.now()
    clf = svm.LinearCSVMC()
    clf.train(data)
    Z = clf.predict(T)
    delta = (datetime.now() - tstart)
    # stop time
    mvpa_results.append(delta.seconds + delta.microseconds/mu_second)

if __name__ == '__main__':

    from scikits.learn.datasets import load_iris
    iris = load_iris()
    X = iris.data
    Y = iris.target

    n = 40
    step = 100
    for i in range(n):
        print '============================================'
        print 'Entering iteration %s of %s' % (i, n)
        print '============================================'
        T = np.random.randn(step*i, 4)
        bench_scikit(X, Y, T)
        bench_pymvpa(X, Y, T)
        bench_svm(X, Y, T)

    import pylab as pl
    xx = range(0, n*step, step)
    pl.title('Classification in the Iris dataset (5-d space)')
    pl.plot(xx, scikit_results, 'b-', label='scikit-learn')
    pl.plot(xx, svm_results,'r-', label='libsvm-swig')
    pl.plot(xx, mvpa_results, 'g-', label='pymvpa')
    pl.legend()
    pl.xlabel('number of samples to classify')
    pl.ylabel('time (in microseconds)')
    pl.show()

    # now do a bench where the number of points is fixed
    # and the variable is the number of dimensions
    from scikits.learn.datasets.samples_generator import friedman, sparse_uncorrelated

    scikit_results = []
    svm_results = []
    mvpa_results = []
    n = 40
    step = 500
    start_dim = 400

    print '============================================'
    print 'Warning: this is going to take a looong time'
    print '============================================'

    dimension = start_dim
    for i in range(0, n):
        print '============================================'
        print 'Entering iteration %s of %s' % (i, n)
        print '============================================'
        dimension += step
        X, Y = sparse_uncorrelated(nb_features=dimension, nb_samples=100)
        Y = Y.astype(np.int)
        T, _ = friedman(nb_features=dimension, nb_samples=100)
        bench_scikit(X, Y, T)
        bench_svm(X, Y, T)
        bench_pymvpa(X, Y, T)

    xx = np.arange(start_dim, start_dim+n*step, step)
    pl.title('Classification in high dimensional spaces')
    pl.plot(xx, scikit_results, 'b-', label='scikit-learn')
    pl.plot(xx, svm_results,'r-', label='libsvm-swig')
    pl.plot(xx, mvpa_results, 'g-', label='mvpa')
    pl.legend()
    pl.xlabel('number of dimensions')
    pl.ylabel('time (in seconds)')
    pl.axis('tight')
    pl.show()


from scikits.learn.ball_tree import BallTree, knn_brute
import numpy as np
from time import time

from scipy.spatial import cKDTree
import sys
import pylab as pl

def compare_nbrs(nbrs1,nbrs2):
    assert nbrs1.shape == nbrs2.shape
    if(nbrs1.ndim == 2):
        N,k = nbrs1.shape
        for i in range(N):
            for j in range(k):
                if nbrs1[i,j]==i:
                    continue
                elif nbrs1[i,j] not in nbrs2[i]:
                    return False
        return True
    elif(nbrs1.ndim == 1):
        N = len(nbrs1)
        return numpy.all(nbrs1 == nbrs2)

N = 1000
ls = 1 # leaf size
k = 20
BT_results = []
KDT_results = []

for i in range(1, 10):
    print 'Iteration %s' %i
    D = i*100
    M = np.random.random([N, D])

    t0 = time()
    BT = BallTree(M, ls)
    d, nbrs1 = BT.query(M, k)
    delta = time() - t0
    BT_results.append(delta)

    t0 = time()
    KDT = cKDTree(M, ls)
    d, nbrs2 = KDT.query(M, k)
    delta = time() - t0
    KDT_results.append(delta)

    # this checks we get the correct result
    assert compare_nbrs(nbrs1,nbrs2)

xx = 100*np.arange(1, 10)
pl.plot(xx, BT_results, label='scikits.learn (BallTree)')
pl.plot(xx, KDT_results, label='scipy (cKDTree)')
pl.xlabel('number of dimensions')
pl.ylabel('time (seconds)')
pl.legend()
pl.show()
    

"""
This script compares the performance of the Ball Tree code with 
scipy.spatial.cKDTree.

Then run the simple timings script:
 python bench_kdtree.py 1000 100
"""

from scikits.learn.ball_tree import BallTree, knn_brute
import numpy
from time import time

from scipy.spatial import cKDTree
import sys


def compare_nbrs(nbrs1,nbrs2):
    assert nbrs1.shape == nbrs2.shape
    if(nbrs1.ndim == 2):
        N,k = nbrs1.shape
        for i in range(N):
            for j in range(k):
                if nbrs1[i,j]==i:
                    continue
                elif nbrs1[i,j] not in nbrs2[i]:
                    return False
        return True
    elif(nbrs1.ndim == 1):
        N = len(nbrs1)
        return numpy.all(nbrs1 == nbrs2)
    

def test_time(N=1000, D=100, ls=1, k=20):
    M = numpy.random.random([N,D])

    print "---------------------------------------------------"
    print "%i neighbors of %i points in %i dimensions:" % (k,N,D)
    print "   (leaf size = %i)" % ls
    print "  -------------"
    
    t0 = time()
    BT = BallTree(M,ls)
    print "  Ball Tree construction     : %.3g sec" % ( time()-t0 )
    d,nbrs1 = BT.query(M,k)
    print "  total (construction+query) : %.3g sec" % ( time()-t0 )
    print "  -------------"

    
    t0 = time()
    KDT = cKDTree(M,ls)
    print "  KD tree construction       : %.3g sec" % ( time()-t0 )
    d,nbrs2 = KDT.query(M,k)
    print "  total (construction+query) : %.3g sec" % ( time()-t0 )
    print "  -------------"
   
    print "  neighbors match: ",
    print ( compare_nbrs(nbrs1,nbrs2) )
    print "  -------------"

if __name__ == '__main__':
    if len(sys.argv)==3:
        N,D = map(int,sys.argv[1:])
        ls = 20
        k = min(20,N)
        
    elif len(sys.argv)==4:
        N,D,ls = map(int,sys.argv[1:])
        k = min(20,N)

    elif len(sys.argv)==5:
        N,D,ls,k = map(int,sys.argv[1:])
        
    else:
        print "usage: bench_balltree.py N D [leafsize=20], [k=20]"
        exit()
    
    
    test_time(N,D,ls,k)
    
    
    

"""
To run this, you'll need to have installed.

  * glmnet-python
  * scikit-learn (of course)

Does two benchmarks

First, we fix a training set and increase the number of
samples. Then we plot the computation time as function of
the number of samples.

In the second benchmark, we increase the number of dimensions of the
training set. Then we plot the computation time as function of
the number of dimensions.

In both cases, only 10% of the features are informative.
"""
import numpy as np
import pylab as pl
import gc
from time import time

# alpha = 1.0
alpha = 0.1
# alpha = 0.01


def rmse(a, b):
    return np.sqrt(np.mean((a - b) ** 2))


def make_data(n_samples=100, n_tests=100, n_features=100, k=10,
              noise=0.1, seed=0):

    # deterministic test
    np.random.seed(seed)

    # generate random input set
    X = np.random.randn(n_samples, n_features)
    X_test = np.random.randn(n_tests, n_features)

    # generate a ground truth model with only the first 10 features being non
    # zeros (the other features are not correlated to Y and should be ignored by
    # the L1 regularizer)
    coef_ = np.random.randn(n_features)
    coef_[k:] = 0.0

    # generate the ground truth Y from the reference model and X
    Y = np.dot(X, coef_)
    if noise > 0.0:
        Y += np.random.normal(scale=noise, size=Y.shape)

    Y_test = np.dot(X_test, coef_)
    if noise > 0.0:
        Y_test += np.random.normal(scale=noise, size=Y_test.shape)

    return X, Y, X_test, Y_test, coef_


def bench(factory, X, Y, X_test, Y_test, ref_coef):
    gc.collect()

    # start time
    tstart = time()
    clf = factory(alpha=alpha).fit(X, Y)
    delta = (time() - tstart)
    # stop time

    print "rmse: %f" % rmse(Y_test, clf.predict(X_test))
    print "mean coef abs diff: %f" % abs(ref_coef - clf.coef_.ravel()).mean()
    return delta


if __name__ == '__main__':
    from glmnet.elastic_net import Lasso as GlmnetLasso
    from scikits.learn.glm import Lasso as ScikitLasso

    scikit_results = []
    glmnet_results = []
    n = 20
    step = 500
    n_features = 1000
    k = n_features / 10
    n_tests = 1000
    for i in range(1, n + 1):
        print '=================='
        print 'Iteration %s of %s' % (i, n)
        print '=================='
        X, Y, X_test, Y_test, coef_ = make_data(
            n_samples=(i * step), n_tests=n_tests, n_features=n_features,
            noise=0.1, k=k)

        print "benching scikit: "
        scikit_results.append(bench(ScikitLasso, X, Y, X_test, Y_test, coef_))
        print "benching glmnet: "
        glmnet_results.append(bench(GlmnetLasso, X, Y, X_test, Y_test, coef_))

    pl.clf()
    xx = range(0, n*step, step)
    pl.title('Lasso regression on sample dataset (%d features)' % n_features)
    pl.plot(xx, scikit_results, 'b-', label='scikit-learn')
    pl.plot(xx, glmnet_results,'r-', label='glmnet')
    pl.legend()
    pl.xlabel('number of samples to classify')
    pl.ylabel('time (in seconds)')
    pl.show()

    # now do a bench where the number of points is fixed
    # and the variable is the number of features

    scikit_results = []
    glmnet_results = []
    n = 20
    step = 100
    n_samples = 500

    for i in range(1, n + 1):
        print '=================='
        print 'Iteration %02d of %02d' % (i, n)
        print '=================='
        n_features = i * step
        k = n_features / 10
        X, Y, X_test, Y_test, coef_ = make_data(
            n_samples=n_samples, n_tests=n_tests, n_features=n_features,
            noise=0.1, k=k)

        print "benching scikit: "
        scikit_results.append(bench(ScikitLasso, X, Y, X_test, Y_test, coef_))
        print "benching glmnet: "
        glmnet_results.append(bench(GlmnetLasso, X, Y, X_test, Y_test, coef_))

    xx = np.arange(100, 100 + n * step, step)
    pl.figure()
    pl.title('Regression in high dimensional spaces (%d samples)' % n_samples)
    pl.plot(xx, scikit_results, 'b-', label='scikit-learn')
    pl.plot(xx, glmnet_results,'r-', label='glmnet')
    pl.legend()
    pl.xlabel('number of features')
    pl.ylabel('time (in seconds)')
    pl.axis('tight')
    pl.show()


import svm
"""
Support Vector Machine algorithms for sparse matrices.

Warning: this module is a work in progress. It is not tested and surely
contains bugs.

Notes
-----

Some fields, like dual_coef_ are not sparse matrices strictly speaking.
However, they are converted to a sparse matrix for consistency and
efficiency when multiplying to other sparse matrices.

Author: Fabian Pedregosa <fabian.pedregosa@inria.fr>
License: New BSD
"""

import numpy as np
from scipy import sparse

from ..base import ClassifierMixin
from ..svm import _BaseLibSVM, BaseLibLinear
from .. import _libsvm, _liblinear

class _SparseBaseLibSVM(_BaseLibSVM):

    _kernel_types = ['linear', 'poly', 'rbf', 'sigmoid', 'precomputed']
    _svm_types = ['c_svc', 'nu_svc', 'one_class', 'epsilon_svr', 'nu_svr']

    def __init__(self, impl, kernel, degree, gamma, coef0, cache_size,
                 eps, C, nu, p, shrinking, probability):
        assert impl in self._svm_types, \
            "impl should be one of %s, %s was given" % (
                self._svm_types, impl)
        assert kernel in self._kernel_types or callable(kernel), \
            "kernel should be one of %s or a callable, %s was given." % (
                self._kernel_types, kernel)
        self.kernel = kernel
        self.impl = impl
        self.degree = degree
        self.gamma = gamma
        self.coef0 = coef0
        self.cache_size = cache_size
        self.eps = eps
        self.C = C
        self.nu = nu
        self.p = p
        self.shrinking = int(shrinking)
        self.probability = int(probability)

        # container for when we call fit
        self._support_data    = np.empty (0, dtype=np.float64, order='C')
        self._support_indices = np.empty (0, dtype=np.int32, order='C')
        self._support_indptr  = np.empty (0, dtype=np.int32, order='C')

        # strictly speaking, dual_coef is not sparse (see Notes above)
        self._dual_coef_data    = np.empty (0, dtype=np.float64, order='C')
        self._dual_coef_indices = np.empty (0, dtype=np.int32,   order='C')
        self._dual_coef_indptr  = np.empty (0, dtype=np.int32,   order='C')
        self.intercept_         = np.empty (0, dtype=np.float64, order='C')

        # only used in classification
        self.nSV_ = np.empty(0, dtype=np.int32, order='C')


    def fit(self, X, Y, class_weight={}):
        """
        X is expected to be a sparse matrix. For maximum effiency, use a
        sparse matrix in csr format (scipy.sparse.csr_matrix)
        """

        X = sparse.csr_matrix(X)
        X.data = np.asanyarray(X.data, dtype=np.float64, order='C')
        Y      = np.asanyarray(Y,      dtype=np.float64, order='C')

        solver_type = self._svm_types.index(self.impl)
        kernel_type = self._kernel_types.index(self.kernel)

        self.weight       = np.asarray(class_weight.values(),
                                      dtype=np.float64, order='C')
        self.weight_label = np.asarray(class_weight.keys(),
                                       dtype=np.int32, order='C')

        self.label_, self.probA_, self.probB_ = _libsvm.csr_train_wrap(
                 X.shape[1], X.data, X.indices, X.indptr, Y,
                 solver_type, kernel_type, self.degree,
                 self.gamma, self.coef0, self.eps, self.C,
                 self._support_data, self._support_indices,
                 self._support_indptr, self._dual_coef_data,
                 self.intercept_, self.weight_label, self.weight,
                 self.nSV_, self.nu, self.cache_size, self.p,
                 self.shrinking,
                 int(self.probability))

        # TODO: explicitly specify size
        self.support_ = sparse.csr_matrix((self._support_data,
                                           self._support_indices,
                                           self._support_indptr))

        # TODO: is this always a 1-d array ?
        n_classes = len(self.label_) - 1
        dual_coef_indices =  np.tile(np.arange(self.support_.shape[0]),
                                     n_classes)
        dual_coef_indptr = np.arange(0, dual_coef_indices.size + 1,
                                     dual_coef_indices.size / n_classes)

        self.dual_coef_ = sparse.csr_matrix((self._dual_coef_data,
                                             dual_coef_indices,
                                             dual_coef_indptr))

        return self


    def predict(self, T):
        """
        This function does classification or regression on an array of
        test vectors T.

        For a classification model, the predicted class for each
        sample in T is returned.  For a regression model, the function
        value of T calculated is returned.

        For an one-class model, +1 or -1 is returned.

        Parameters
        ----------
        T : scipy.sparse.csr, shape = [n_samples, n_features]

        Returns
        -------
        C : array, shape = [nsample]
        """
        T = sparse.csr_matrix(T)
        T.data = np.asanyarray(T.data, dtype=np.float64, order='C')
        kernel_type = self._kernel_types.index(self.kernel)
        return _libsvm.csr_predict_from_model_wrap(T.data,
                      T.indices, T.indptr, self.support_.data,
                      self.support_.indices, self.support_.indptr,
                      self.dual_coef_.data, self.intercept_,
                      self._svm_types.index(self.impl),
                      kernel_type, self.degree,
                      self.gamma, self.coef0, self.eps, self.C,
                      self.weight_label, self.weight,
                      self.nu, self.cache_size, self.p,
                      self.shrinking, self.probability,
                      self.nSV_, self.label_, self.probA_,
                      self.probB_)


class SVC(_SparseBaseLibSVM):
    """SVC for sparse matrices (csr)

    For best results, this accepts a matrix in csr format
    (scipy.sparse.csr), but should be able to convert from any array-like
    object (including other sparse representations).
    """

    def __init__(self, kernel='rbf', degree=3, gamma=0.0, coef0=0.0,
                 cache_size=100.0, eps=1e-3, C=1.0, shrinking=True,
                 probability=False):

        _SparseBaseLibSVM.__init__(self, 'c_svc', kernel, degree, gamma, coef0,
                         cache_size, eps, C, 0., 0.,
                         shrinking, probability)



class NuSVC (_SparseBaseLibSVM):
    """NuSVC for sparse matrices (csr)

    For best results, this accepts a matrix in csr format
    (scipy.sparse.csr), but should be able to convert from any array-like
    object (including other sparse representations).
    """


    def __init__(self, nu=0.5, kernel='rbf', degree=3, gamma=0.0,
                 coef0=0.0, shrinking=True, probability=False,
                 eps=1e-3, cache_size=100.0):

        _SparseBaseLibSVM.__init__(self, 'nu_svc', kernel, degree,
                         gamma, coef0, cache_size, eps, 0., nu, 0.,
                         shrinking, probability)




class SVR (_SparseBaseLibSVM):
    """SVR for sparse matrices (csr)

    For best results, this accepts a matrix in csr format
    (scipy.sparse.csr), but should be able to convert from any array-like
    object (including other sparse representations).
    """


    def __init__(self, kernel='rbf', degree=3, gamma=0.0, coef0=0.0,
                 cache_size=100.0, eps=1e-3, C=1.0, nu=0.5, p=0.1,
                 shrinking=True, probability=False):

        _SparseBaseLibSVM.__init__(self, 'epsilon_svr', kernel,
                         degree, gamma, coef0, cache_size, eps, C, nu,
                         p, shrinking, probability)





class NuSVR (_SparseBaseLibSVM):
    """NuSVR for sparse matrices (csr)

    For best results, this accepts a matrix in csr format
    (scipy.sparse.csr), but should be able to convert from any array-like
    object (including other sparse representations).
    """

    def __init__(self, nu=0.5, C=1.0, kernel='rbf', degree=3,
                 gamma=0.0, coef0=0.0, shrinking=True,
                 probability=False, cache_size=100.0, eps=1e-3):

        _SparseBaseLibSVM.__init__(self, 'epsilon_svr', kernel,
                         degree, gamma, coef0, cache_size, eps, C, nu,
                         0., shrinking, probability)



class OneClassSVM (_SparseBaseLibSVM):
    """NuSVR for sparse matrices (csr)

    For best results, this accepts a matrix in csr format
    (scipy.sparse.csr), but should be able to convert from any array-like
    object (including other sparse representations).
    """

    def __init__(self, kernel='rbf', degree=3, gamma=0.0, coef0=0.0,
                 cache_size=100.0, eps=1e-3, C=1.0, 
                 nu=0.5, p=0.1, shrinking=True, probability=False):

        _SparseBaseLibSVM.__init__(self, 'one_class', kernel, degree,
                         gamma, coef0, cache_size, eps, C, nu, p,
                         shrinking, probability)
    
    def fit(self, X, Y=None):
        if Y is None:
            n_samples = X.shape[0]
            Y = [0] * n_samples
        super(OneClassSVM, self).fit(X, Y)



class LinearSVC(BaseLibLinear, ClassifierMixin):
    """
    Linear Support Vector Classification, Sparse Version

    Similar to SVC with parameter kernel='linear', but uses internally
    liblinear rather than libsvm, so it has more flexibility in the
    choice of penalties and loss functions and should be faster for
    huge datasets.

    Parameters
    ----------
    loss : string, 'l1' or 'l2' (default 'l2')
        Specifies the loss function. With 'l1' it is the standard SVM
        loss (a.k.a. hinge Loss) while with 'l2' it is the squared loss.
        (a.k.a. squared hinge Loss)

    penalty : string, 'l1' or 'l2' (default 'l2')
        Specifies the norm used in the penalization. The 'l2'
        penalty is the standard used in SVC. The 'l1' leads to coef_
        vectors that are sparse.

    dual : bool, (default True)
        Select the algorithm to either solve the dual or primal
        optimization problem.


    Attributes
    ----------
    `support_` : array-like, shape = [nSV, n_features]
        Support vectors

    `dual_coef_` : array, shape = [n_classes-1, nSV]
        Coefficient of the support vector in the decision function,
        where n_classes is the number of classes and nSV is the number
        of support vectors.

    `coef_` : array, shape = [n_classes-1, n_features]
        Wiehgiths asigned to the features (coefficients in the primal
        problem). This is only available in the case of linear kernel.

    `intercept_` : array, shape = [n_classes-1]
        constants in decision function


    Notes
    -----
    Some features of liblinear are still not wrapped, like the Cramer
    & Singer algorithm.

    References
    ----------
    LIBLINEAR -- A Library for Large Linear Classification
    http://www.csie.ntu.edu.tw/~cjlin/liblinear/

    """

    _weight_label = np.empty(0, dtype=np.int32)
    _weight = np.empty(0, dtype=np.float64)


    def fit(self, X, Y, **params):
        """
        Parameters
        ==========
        X : array-like, shape = [n_samples, n_features]
            Training vector, where n_samples in the number of samples and
            n_features is the number of features.
        Y : array, shape = [n_samples]
            Target vector relative to X
        """
        self._set_params(**params)
        X = sparse.csr_matrix(X)
        X.data = np.asanyarray(X.data, dtype=np.float64, order='C')
        Y = np.asanyarray(Y, dtype=np.int32, order='C')

        self.raw_coef_, self.label_ = \
                       _liblinear.csr_train_wrap(X.shape[1], X.data, X.indices,
                       X.indptr, Y,
                       self._get_solver_type(),
                       self.eps, self._get_bias(), self.C, self._weight_label,
                       self._weight)
        return self

    def predict(self, T):
        T = sparse.csr_matrix(T)
        T.data = np.asanyarray(T.data, dtype=np.float64, order='C')
        return _liblinear.csr_predict_wrap(T.shape[1],
                                      T.data, T.indices, T.indptr,
                                      self.raw_coef_,
                                      self._get_solver_type(),
                                      self.eps, self.C,
                                      self._weight_label,
                                      self._weight, self.label_,
                                      self._get_bias())


# Author: Alexandre Gramfort <alexandre.gramfort@inria.fr>
#         Fabian Pedregosa <fabian.pedregosa@inria.fr>
#         Olivier Grisel <olivier.grisel@ensta.org>
#
# License: BSD Style.

import warnings
import numpy as np

from .base import LinearModel
from ..cross_val import KFold
from . import cd_fast


class Lasso(LinearModel):
    """
    Linear Model trained with L1 prior as regularizer (a.k.a. the
    lasso).

    Parameters
    ----------
    alpha : float, optional
        Constant that multiplies the L1 term. Defaults to 1.0

    fit_intercept : boolean
        whether to calculate the intercept for this model. If set
        to false, no intercept will be used in calculations
        (e.g. data is expected to be already centered).

    Attributes
    ----------
    `coef_` : array, shape = [n_features]
        parameter vector (w in the fomulation formula)

    `intercept_` : float
        independent term in decision function.

    Examples
    --------
    >>> from scikits.learn import glm
    >>> clf = glm.Lasso(alpha=0.1)
    >>> clf.fit([[0,0], [1, 1], [2, 2]], [0, 1, 2])
    Lasso(alpha=0.1, coef_=array([ 0.85,  0.  ]), fit_intercept=True)
    >>> print clf.coef_
    [ 0.85  0.  ]
    >>> print clf.intercept_
    0.15

    Notes
    -----
    The algorithm used to fit the model is coordinate descent.
    """

    def __init__(self, alpha=1.0, fit_intercept=True, coef_=None):
        self.alpha = alpha
        self.fit_intercept = fit_intercept
        self.coef_ = coef_


    def fit(self, X, Y, maxit=1000, tol=1e-4, **params):
        """
        Fit Lasso model.

        Parameters
        ----------
        X: numpy array of shape [n_samples,n_features]
            Training data

        Y: numpy array of shape [n_samples]
            Target values

        maxit: int, optional
            maximum number of coordinate descent iterations used to
            fit the model. In case
        tol: float, optional
            fit tolerance

        Returns
        -------
        self : returns an instance of self.
        """
        self._set_params(**params)

        X = np.asanyarray(X, dtype=np.float64)
        Y = np.asanyarray(Y, dtype=np.float64)

        if self.fit_intercept:
            self._xmean = X.mean(axis=0)
            self._ymean = Y.mean(axis=0)
            X = X - self._xmean
            Y = Y - self._ymean
        else:
            self._xmean = np.zeros(X.shape[1])
            self._ymean = np.zeros(X.shape[0])

        n_samples = X.shape[0]
        alpha = self.alpha * n_samples

        if self.coef_ is None:
            self.coef_ = np.zeros(X.shape[1], dtype=np.float64)

        X = np.asfortranarray(X) # make data contiguous in memory
        self.coef_, self.dual_gap_, self.eps_ = \
                    cd_fast.lasso_coordinate_descent(self.coef_,
                    alpha, X, Y, maxit, tol)

        self.intercept_ = self._ymean - np.dot(self._xmean, self.coef_)

        if self.dual_gap_ > self.eps_:
            warnings.warn('Objective did not converge, you might want '
                                'to increase the number of interations')

        # Store explained variance for __str__
        self.explained_variance_ = self._explained_variance(X, Y)

        # return self for chaining fit and predict calls
        return self


class ElasticNet(Lasso):
    """Linear Model trained with L1 and L2 prior as regularizer

    rho=1 is the lasso penalty. Currently, rho <= 0.01 is not
    reliable, unless you supply your own sequence of alpha.

    Parameters
    ----------
    alpha : float
        Constant that multiplies the L1 term. Defaults to 1.0
    rho : float
        The ElasticNet mixing parameter, with 0 < rho <= 1.
    corf: ndarray of shape n_features
        The initial coeffients to warm-start the optimization
    fit_intercept: bool
        Whether the intercept should be estimated or not. If False, the
        data is assumed to be already centered.
    """

    def __init__(self, alpha=1.0, rho=0.5, coef_=None, 
                fit_intercept=True):
        self.alpha = alpha
        self.rho = rho
        self.coef_ = coef_
        self.fit_intercept = fit_intercept


    def fit(self, X, Y, maxit=1000, tol=1e-4, **params):
        """Fit Elastic Net model with coordinate descent"""
        self._set_params(**params)
        X = np.asanyarray(X, dtype=np.float64)
        Y = np.asanyarray(Y, dtype=np.float64)

        if self.fit_intercept:
            self._xmean = X.mean(axis=0)
            self._ymean = Y.mean(axis=0)
            X = X - self._xmean
            Y = Y - self._ymean
        else:
            self._xmean = np.zeros(X.shape[1])
            self._ymean = np.zeros(X.shape[0])

        if self.coef_ is None:
            self.coef_ = np.zeros(X.shape[1], dtype=np.float64)

        n_samples = X.shape[0]
        alpha = self.alpha * self.rho * n_samples
        beta = self.alpha * (1.0 - self.rho) * n_samples

        X = np.asfortranarray(X) # make data contiguous in memory

        self.coef_, self.dual_gap_, self.eps_ = \
                cd_fast.enet_coordinate_descent(self.coef_, alpha, beta, X, Y,
                                        maxit, tol)

        self.intercept_ = self._ymean - np.dot(self._xmean, self.coef_)

        if self.dual_gap_ > self.eps_:
            warnings.warn('Objective did not converge, you might want'
                                'to increase the number of interations')

        # Store explained variance for __str__
        self.explained_variance_ = self._explained_variance(X, Y)

        # return self for chaining fit and predict calls
        return self


################################################################################
# Classes to store linear models along a regularization path 
################################################################################

def lasso_path(X, y, eps=1e-3, n_alphas=100, alphas=None,
               verbose=False, fit_params=dict()):
    """
    Compute Lasso path with coordinate descent

    Parameters
    ----------
    X : numpy array of shape [n_samples,n_features]
        Training data

    Y : numpy array of shape [n_samples]
        Target values

    eps : float, optional
        Length of the path. eps=1e-3 means that
        alpha_min / alpha_max = 1e-3

    n_alphas : int, optional
        Number of alphas along the regularization path

    alphas : numpy array, optional
        List of alphas where to compute the models.
        If None alphas are set automatically

    fit_params : dict, optional
        keyword arguments passed to the Lasso fit method

    Returns
    -------
    models : a list of models along the regularization path

    Notes
    -----
    See examples/plot_lasso_coordinate_descent_path.py for an example.
    """
    n_samples = X.shape[0]
    if alphas is None:
        alpha_max = np.abs(np.dot(X.T, y)).max() / n_samples
        alphas = np.logspace(np.log10(alpha_max*eps), np.log10(alpha_max),
                             num=n_alphas)[::-1]
    else:
        # XXX: Maybe should reorder the models when outputing them, so
        # that they are ordered in the order of the initial alphas
        alphas = np.sort(alphas)[::-1] # make sure alphas are properly ordered
    coef_ = None # init coef_
    models = []
    for alpha in alphas:
        model = Lasso(coef_=coef_, alpha=alpha)
        model.fit(X, y, **fit_params)
        if verbose: 
            print model
        coef_ = model.coef_.copy()
        models.append(model)
    return models

def enet_path(X, y, rho=0.5, eps=1e-3, n_alphas=100, alphas=None,
              verbose=False, fit_params=dict()):

    """Compute Elastic-Net path with coordinate descent

    Parameters
    ----------
    X : numpy array of shape [n_samples,n_features]
        Training data

    Y : numpy array of shape [n_samples]
        Target values

    eps : float
        Length of the path. eps=1e-3 means that
        alpha_min / alpha_max = 1e-3

    n_alphas : int, optional
        Number of alphas along the regularization path

    alphas : numpy array, optional
        List of alphas where to compute the models.
        If None alphas are set automatically

    fit_params : dict, optional
        keyword arguments passed to the ElasticNet fit method

    Returns
    -------
    models : a list of models along the regularization path

    Notes
    -----
    See examples/plot_lasso_coordinate_descent_path.py for an example.
    """
    n_samples = X.shape[0]
    if alphas is None:
        alpha_max = np.abs(np.dot(X.T, y)).max() / (n_samples*rho)
        alphas = np.logspace(np.log10(alpha_max*eps), np.log10(alpha_max),
                             num=n_alphas)[::-1]
    else:
        alphas = np.sort(alphas)[::-1] # make sure alphas are properly ordered
    coef_ = None # init coef_
    models = []
    for alpha in alphas:
        model = ElasticNet(coef_=coef_, alpha=alpha, rho=rho)
        model.fit(X, y, **fit_params)
        if verbose: print model
        coef_ = model.coef_.copy()
        models.append(model)
    return models


class LinearModelCV(LinearModel):
    """Base class for iterative model fitting along a regularization path"""

    def __init__(self, eps=1e-3, n_alphas=100, alphas=None):
        self.eps = eps
        self.n_alphas = n_alphas
        self.alphas = alphas


    def fit(self, X, y, cv=None, **fit_params):
        """Fit linear model with coordinate descent along decreasing alphas
        using cross-validation

        Parameters
        ----------

        X : numpy array of shape [n_samples,n_features]
            Training data

        Y : numpy array of shape [n_samples]
            Target values

        cv : cross-validation generator, optional
             If None, KFold will be used.

        fit_params : kwargs
            keyword arguments passed to the Lasso fit method

        """

        X = np.asanyarray(X, dtype=np.float64)
        y = np.asanyarray(y, dtype=np.float64)

        n_samples = X.shape[0]

        # Start to compute path on full data
        models = self.path(X, y, fit_params=fit_params, **self._get_params())

        alphas = [model.alpha for model in models]
        n_alphas = len(alphas)

        # init cross-validation generator
        cv = cv if cv else KFold(n_samples, 5)

        params = self._get_params()
        params['alphas'] = alphas
        params['n_alphas'] = n_alphas

        # Compute path for all folds and compute MSE to get the best alpha
        mse_alphas = np.zeros(n_alphas)
        for train, test in cv:
            models_train = self.path(X[train], y[train], fit_params=fit_params,
                                        **params)
            for i_alpha, model in enumerate(models_train):
                y_ = model.predict(X[test])
                mse_alphas[i_alpha] += ((y_ - y[test]) ** 2).mean()

        i_best_alpha = np.argmin(mse_alphas)
        model = models[i_best_alpha]

        self.coef_ = model.coef_
        self.intercept_ = model.intercept_
        self.explained_variance_ = model.explained_variance_
        self.alpha = model.alpha
        self.alphas = np.asarray(alphas)
        return self


class LassoCV(LinearModelCV):
    """Lasso linear model with iterative fitting along a regularization path

    The best model is selected by cross-validation.

    Parameters
    ----------
    eps : float, optional
        Length of the path. eps=1e-3 means that
        alpha_min / alpha_max = 1e-3.

    n_alphas : int, optional
        Number of alphas along the regularization path

    alphas : numpy array, optional
        List of alphas where to compute the models.
        If None alphas are set automatically

    Notes
    -----
    See examples/glm/lasso_path_with_crossvalidation.py for an example.
    """

    path = staticmethod(lasso_path)


class ElasticNetCV(LinearModelCV):
    """Elastic Net model with iterative fitting along a regularization path

    The best model is selected by cross-validation.

    Parameters
    ----------
    rho : float, optional
        float between 0 and 1 passed to ElasticNet (scaling between
        l1 and l2 penalties)

    eps : float, optional
        Length of the path. eps=1e-3 means that
        alpha_min / alpha_max = 1e-3.

    n_alphas : int, optional
        Number of alphas along the regularization path

    alphas : numpy array, optional
        List of alphas where to compute the models.
        If None alphas are set automatically

    Notes
    -----
    See examples/glm/lasso_path_with_crossvalidation.py for an example.
    """

    path = staticmethod(enet_path)

    def __init__(self, rho=0.5, eps=1e-3, n_alphas=100, alphas=None):
        self.rho = rho
        self.eps = eps
        self.n_alphas = n_alphas
        self.alphas = alphas

# Least Angle Regression algorithm. See doc/module/glm for a
# complete discussion.
#
# Author: Fabian Pedregosa <fabian.pedregosa@inria.fr>
#         Alexandre Gramfort <alexandre.gramfort@inria.fr>
#
# License: BSD Style.

import numpy as np
from scipy import linalg
from .base import LinearModel
import scipy.sparse as sp # needed by LeastAngleRegression
from .._minilearn import lars_fit_wrap


# Notes: np.ma.dot copies the masked array before doing the dot
# product. Maybe we should implement in C our own masked_dot that does
# not make unnecessary copies.

# all linalg.solve solve a triangular system, so this could be heavily
# optimized by binding (in scipy ?) trsv or trsm

def lars_path(X, y, max_iter=None, alpha_min=0, method="lar", precompute=True):
    """ Compute Least Angle Regression and LASSO path

        Parameters
        -----------
        X: array, shape: (n, p)
            Input data
        y: array, shape: (n)
            Input targets
        max_iter: integer, optional
            The number of 'kink' in the path
        alpha_min: float, optional
            The minimum correlation along the path. It corresponds
            to the regularization parameter alpha parameter in the Lasso.
        method: 'lar' or 'lasso'
            Specifies the problem solved: the LAR or its variant the LASSO-LARS
            that gives the solution of the LASSO problem for any regularization
            parameter.

        Returns
        --------
        alphas: array, shape: (k)
            The alphas along the path
        
        active: array, shape (?)
            Indices of active variables at the end of the path.
        
        coefs: array, shape (p,k)
            Coefficients along the path

        Notes
        ------
        XXX : add reference papers and wikipedia page
    
    TODOS:
    precompute : empty for now

    TODO: detect stationary points.
    Lasso variant
    store full path
    """

    X = np.atleast_2d(X)
    y = np.atleast_1d(y)

    n_samples, n_features = X.shape

    if max_iter is None:
        max_iter = min(n_samples, n_features)

    max_pred = max_iter # OK for now

    beta     = np.zeros ((max_iter + 1, X.shape[1]))
    alphas   = np.zeros (max_iter + 1)
    n_iter, n_pred = 0, 0
    active   = list()
    # holds the sign of covariance
    sign_active = np.empty (max_pred, dtype=np.int8)
    drop = False

    # will hold the cholesky factorization
    # only lower part is referenced. We do not create it as
    # empty array because chol_solve calls chkfinite on the
    # whole array, which can cause problems.
    L = np.zeros ((max_pred, max_pred), dtype=np.float64)

    Xt  = X.T
    Xna = Xt.view(np.ma.MaskedArray) # variables not in the active set
                                     # should have a better name

    Xna.soften_mask()

    while 1:


        # Calculate covariance matrix and get maximum
        res = y - np.dot (X, beta[n_iter]) # there are better ways
        Cov = np.ma.dot (Xna, res)

        imax    = np.ma.argmax (np.ma.abs(Cov)) #rename
        Cov_max =  Cov.data [imax]

        alpha = np.abs(Cov_max) #sum (np.abs(beta[n_iter]))
        alphas [n_iter] = alpha

        if (n_iter >= max_iter or n_pred >= max_pred ):
            break

        if (alpha < alpha_min): break


        if not drop:

            # Update the Cholesky factorization of (Xa * Xa') #
            #                                                 #
            #          ( L   0 )                              #
            #   L  ->  (       )  , where L * w = b           #
            #          ( w   z )    z = 1 - ||w||             #
            #                                                 #
            #   where u is the last added to the active set   #

            n_pred += 1
            active.append(imax)
            Xna[imax] = np.ma.masked
            Cov[imax] = np.ma.masked

            sign_active [n_pred-1] = np.sign (Cov_max)

            X_max = Xt[imax]

            c = np.dot (X_max, X_max)
            L [n_pred-1, n_pred-1] = c

            if n_pred > 1:
                b = np.dot (X_max, Xa.T)

                # please refactor me, using linalg.solve is overkill
                L [n_pred-1, :n_pred-1] = linalg.solve (L[:n_pred-1, :n_pred-1], b)
                v = np.dot(L [n_pred-1, :n_pred-1], L [n_pred - 1, :n_pred -1])
                L [n_pred-1,  n_pred-1] = np.sqrt (c - v)
        else:
            drop = False

        Xa = Xt[active] # also Xna[~Xna.mask]

        # Now we go into the normal equations dance.
        # (Golub & Van Loan, 1996)

        b = np.copysign (Cov_max.repeat(n_pred), sign_active[:n_pred])
        b = linalg.cho_solve ((L[:n_pred, :n_pred], True),  b)

        C = A = np.abs(Cov_max)
        u = np.dot (Xa.T, b)
        a = np.ma.dot (Xna, u)

        # equation 2.13, there's probably a simpler way
        g1 = (C - Cov) / (A - a)
        g2 = (C + Cov) / (A + a)

        # one for the border cases
        g = np.ma.concatenate((g1, g2))

        g = g[g > 0.]
        gamma_ = np.ma.min (g)

        if n_pred >= X.shape[1]:
            gamma_ = 1.

        if method == 'lasso':

            z = - beta[n_iter, active] / b
            z[z <= 0.] = np.inf

            idx = np.argmin(z)

            if z[idx] < gamma_:
                gamma_ = z[idx]
                drop = True

        n_iter += 1
        beta[n_iter, active] = beta[n_iter - 1, active] + gamma_ * b

        if drop:
            n_pred -= 1
            drop_idx = active.pop (idx)
            # please please please remove this masked arrays pain from me
            Xna[drop_idx] = Xna.data[drop_idx]
            print 'dropped ', idx, ' at ', n_iter, ' iteration'
            Xa = Xt[active] # duplicate
            L[:n_pred, :n_pred] = linalg.cholesky(np.dot(Xa, Xa.T), lower=True)
            sign_active = np.delete (sign_active, idx) # do an append to maintain size
            sign_active = np.append (sign_active, 0.)
            # should be done using cholesky deletes


    if alpha < alpha_min: # interpolate
        # interpolation factor 0 <= ss < 1
        ss = (alphas[n_iter-1] - alpha_min) / (alphas[n_iter-1] - alphas[n_iter])
        beta[n_iter] = beta[n_iter-1] + ss*(beta[n_iter] - beta[n_iter-1]);
        alphas[n_iter] = alpha_min
        alphas = alphas[:n_iter+1]
        beta = beta[:n_iter+1]

    return alphas, active, beta.T


class LARS (LinearModel):
    """ Least Angle Regression model a.k.a. LAR
    
    Parameters
    ----------
    n_features : int, optional
        Number of selected active features

    XXX : todo add fit_intercept
    fit_intercept : boolean
        whether to calculate the intercept for this model. If set
        to false, no intercept will be used in calculations
        (e.g. data is expected to be already centered).

    Attributes
    ----------
    `coef_` : array, shape = [n_features]
        parameter vector (w in the fomulation formula)

    XXX : add intercept_
    `intercept_` : float
        independent term in decision function.

    Examples
    --------
    >>> from scikits.learn import glm
    >>> clf = glm.LARS(n_features=1)
    >>> clf.fit([[-1,1], [0, 0], [1, 1]], [-1, 0, -1])
    LARS(normalize=True, n_features=1)
    >>> print clf.coef_
    [ 0.         -0.81649658]

    Notes
    -----
    See also scikits.learn.glm.LassoLARS that fits a LASSO model
    using a variant of Least Angle Regression
    
    XXX : add ref + wikipedia page
    
    See examples. XXX : add examples names
    """
    def __init__(self, n_features, normalize=True):
        self.n_features = n_features
        self.normalize = normalize
        self.coef_ = None

    def fit (self, X, y, **params):
        self._set_params(**params)
                # will only normalize non-zero columns

        X = np.atleast_2d(X)
        y = np.atleast_1d(y)

        if self.normalize:
            self._xmean = X.mean(0)
            self._ymean = y.mean(0)
            X = X - self._xmean
            y = y - self._ymean
            self._norms = np.apply_along_axis (np.linalg.norm, 0, X)
            nonzeros = np.flatnonzero(self._norms)
            X[:, nonzeros] /= self._norms[nonzeros]

        method = 'lar'
        alphas_, active, coef_path_ = lars_path(X, y,
                                max_iter=self.n_features, method=method)
        self.coef_ = coef_path_[:,-1]
        return self


class LassoLARS (LinearModel):
    """ Lasso model fit with Least Angle Regression a.k.a. LARS
    
    It is a Linear Model trained with an L1 prior as regularizer.
    lasso).

    Parameters
    ----------
    alpha : float, optional
        Constant that multiplies the L1 term. Defaults to 1.0

    XXX : todo add fit_intercept
    fit_intercept : boolean
        whether to calculate the intercept for this model. If set
        to false, no intercept will be used in calculations
        (e.g. data is expected to be already centered).

    Attributes
    ----------
    `coef_` : array, shape = [n_features]
        parameter vector (w in the fomulation formula)

    XXX : add intercept_
    `intercept_` : float
        independent term in decision function.

    Examples
    --------
    >>> from scikits.learn import glm
    >>> clf = glm.LassoLARS(alpha=0.1)
    >>> clf.fit([[-1,1], [0, 0], [1, 1]], [-1, 0, -1])
    LassoLARS(normalize=True, alpha=0.1, max_iter=None)
    >>> print clf.coef_
    [ 0.         -0.51649658]

    Notes
    -----
    See also scikits.learn.glm.Lasso that fits the same model using
    an alternative optimization strategy called 'coordinate descent.'
    """

    def __init__(self, alpha=1.0, max_iter=None, normalize=True):
        """ XXX : add doc
                # will only normalize non-zero columns
        """
        self.alpha = alpha
        self.normalize = normalize
        self.coef_ = None
        self.max_iter = max_iter

    def fit (self, X, y, **params):
        """ XXX : add doc
        """
        self._set_params(**params)

        X = np.atleast_2d(X)
        y = np.atleast_1d(y)

        n_samples = X.shape[0]
        alpha = self.alpha * n_samples # scale alpha with number of samples

        if self.normalize:
            self._xmean = X.mean(0)
            self._ymean = y.mean(0)
            X = X - self._xmean
            y = y - self._ymean
            self._norms = np.apply_along_axis (np.linalg.norm, 0, X)
            nonzeros = np.flatnonzero(self._norms)
            X[:, nonzeros] /= self._norms[nonzeros]

        method = 'lasso'
        alphas_, active, coef_path_ = lars_path(X, y,
                                            alpha_min=alpha, method=method,
                                            max_iter=self.max_iter)

        self.coef_ = coef_path_[:,-1]
        return self


#### OLD C-based LARS : will probably be removed


class LeastAngleRegression(LinearModel):
    """
    Least Angle Regression using the LARS algorithm.

    Attributes
    ----------
    `coef_` : array, shape = [n_features]
        parameter vector (w in the fomulation formula)

    `intercept_` : float
        independent term in decision function.

    `coef_path_` : array, shape = [max_features + 1, n_features]
         Full coeffients path.

    Notes
    -----
    predict does only work correctly in the case of normalized
    predictors.

    See also
    --------
    scikits.learn.glm.Lasso

    """

    def __init__(self):
        self.alphas_ = np.empty(0, dtype=np.float64)
        self._chol   = np.empty(0, dtype=np.float64)
        self.beta_    = np.empty(0, dtype=np.float64)

    def fit (self, X, Y, fit_intercept=True, max_features=None, normalize=True):
        """
        Fit the model according to data X, Y.

        Parameters
        ----------
        X : numpy array of shape [n_samples,n_features]
            Training data

        Y : numpy array of shape [n_samples]
            Target values

        fit_intercept : boolean, optional
            wether to calculate the intercept for this model. If set
            to false, no intercept will be used in calculations
            (e.g. data is expected to be already centered).

        max_features : int, optional
            number of features to get into the model. The iterative
            will stop just before the `max_features` variable enters
            in the active set. If not specified, min(N, p) - 1
            will be used.

        normalize : boolean
            whether to normalize (make all non-zero columns have mean
            0 and norm 1).
        """
        ## TODO: resize (not create) arrays, check shape,
        ##    add a real intercept

        X  = np.asanyarray(X, dtype=np.float64, order='C')
        _Y = np.asanyarray(Y, dtype=np.float64, order='C')

        if Y is _Y: Y = _Y.copy()
        else: Y = _Y

        if max_features is None:
            max_features = min(*X.shape)-1

        sum_k = max_features * (max_features + 1) /2
        self.alphas_.resize(max_features + 1)
        self._chol.resize(sum_k)
        self.beta_.resize(sum_k)
        coef_row = np.zeros(sum_k, dtype=np.int32)
        coef_col = np.zeros(sum_k, dtype=np.int32)


        if normalize:
            # will only normalize non-zero columns
            self._xmean = X.mean(0)
            self._ymean = Y.mean(0)
            X = X - self._xmean
            Y = Y - self._ymean
            self._norms = np.apply_along_axis (np.linalg.norm, 0, X)
            nonzeros = np.flatnonzero(self._norms)
            X[:, nonzeros] /= self._norms[nonzeros]
        else:
            self._xmean = 0.
            self._ymean = 0.

        lars_fit_wrap(0, X, Y, self.beta_, self.alphas_, coef_row,
                      coef_col, self._chol, max_features)

        self.coef_path_ = sp.coo_matrix((self.beta_,
                                        (coef_row, coef_col)),
                                        shape=(X.shape[1], max_features+1)).todense()

        self.coef_ = np.ravel(self.coef_path_[:, max_features])

        if fit_intercept:
            self.intercept_ = self._ymean
        else:
            self.intercept_ = 0.

        return self


    def predict(self, X, normalize=True):
        """
        Predict using the linear model.

        Parameters
        ----------
        X : numpy array of shape [n_samples,n_features]

        Returns
        -------
        C : array, shape = [n_samples]
            Returns predicted values.
        """
        X = np.asanyarray(X, dtype=np.float64, order='C')
        if normalize:
            X -= self._xmean
            X /= self._norms
        return  np.dot(X, self.coef_) + self.intercept_


    

"""
Generalized linear models
=========================

scikits.learn.glm is a module to fit genelarized linear models.
It includes Ridge regression, Bayesian Regression, Lasso and
Elastic Net estimators computed with Least Angle Regression
and coordinate descent.

"""

from .base import LinearRegression
from .lars import LARS, LassoLARS, lars_path, LeastAngleRegression
from .coordinate_descent import Lasso, ElasticNet, LassoCV, ElasticNetCV, \
                                lasso_path, enet_path
from .bayes import Ridge, BayesianRidge, ARDRegression


from os.path import join
import warnings
import numpy
import sys
if sys.version_info[0] < 3:
    from ConfigParser import ConfigParser
else:
    from configparser import ConfigParser

def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration
    from numpy.distutils.system_info import get_info, get_standard_file, BlasNotFoundError
    config = Configuration('glm', parent_package, top_path)

    site_cfg  = ConfigParser()
    site_cfg.read(get_standard_file('site.cfg'))


    # cd fast needs CBLAS
    blas_info = get_info('blas_opt', 0)
    if (not blas_info) or (
        ('NO_ATLAS_INFO', 1) in blas_info.get('define_macros', [])) :
        cblas_libs = ['cblas']
        blas_info.pop('libraries', None)
    else:
        cblas_libs = blas_info.pop('libraries', [])

    config.add_extension('cd_fast',
                         sources=[join('src', 'cd_fast.c')],
                         libraries=cblas_libs,
                         include_dirs=[join('..', 'src', 'cblas'),
                                       numpy.get_include(),
                                       blas_info.pop('include_dirs', [])],
                         extra_compile_args=['-std=c99'] + \
                                             blas_info.pop('extra_compile_args', []),
                         **blas_info
                         )


    # add other directories
    config.add_subpackage('tests')
    config.add_subpackage('benchmarks')

    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())


import numpy as np
from scipy import linalg

from .base import LinearModel

class Ridge(LinearModel):
    """
    Ridge regression.

    Parameters
    ----------
    alpha : float
        Small positive values of alpha improve the coditioning of the
        problem and reduce the variance of the estimates.
    fit_intercept : boolean
        wether to calculate the intercept for this model. If set
        to false, no intercept will be used in calculations
        (e.g. data is expected to be already centered).

    Examples
    --------
    >>> import numpy as np
    >>> n_samples, n_features = 10, 5
    >>> np.random.seed(0)
    >>> Y = np.random.randn(n_samples)
    >>> X = np.random.randn(n_samples, n_features)
    >>> clf = Ridge(alpha=1.0)
    >>> clf.fit(X, Y)
    Ridge(alpha=1.0, fit_intercept=True)
    """

    def __init__(self, alpha=1.0, fit_intercept=True):
        self.alpha = alpha
        self.fit_intercept = fit_intercept


    def fit(self, X, Y, **params):
        """
        Fit Ridge regression model

        Parameters
        ----------
        X : numpy array of shape [n_samples,n_features]
            Training data
        Y : numpy array of shape [n_samples]
            Target values

        Returns
        -------
        self : returns an instance of self.
        """
        self._set_params(**params)
        n_samples, n_features = X.shape

        if self.fit_intercept:
            self._xmean = X.mean(axis=0)
            self._ymean = Y.mean(axis=0)
            X = X - self._xmean
            Y = Y - self._ymean
        else:
            self._xmean = 0.
            self._ymean = 0.

        if n_samples > n_features:
            # w = inv(X^t X + alpha*Id) * X.T y
            self.coef_ = linalg.solve(
                np.dot(X.T, X) + self.alpha * np.eye(n_features),
                np.dot(X.T, Y))
        else:
            # w = X.T * inv(X X^t + alpha*Id) y
            self.coef_ = np.dot(X.T, linalg.solve(
                np.dot(X, X.T) + self.alpha * np.eye(n_samples), Y))

        self.intercept_ = self._ymean - np.dot(self._xmean, self.coef_)
        return self


class BayesianRidge(LinearModel):
    """
    Encapsulate various bayesian regression algorithms
    """

    def __init__(self, ll_bool=False, step_th=300, th_w=1.e-12,
                fit_intercept=True):
        self.ll_bool = ll_bool
        self.step_th = step_th
        self.th_w = th_w
        self.fit_intercept = fit_intercept


    def fit(self, X, Y, **params):
        """
        Parameters
        ----------
        X : numpy array of shape [n_samples,n_features]
            Training data
        Y : numpy array of shape [n_samples]
            Target values

        Returns
        -------
        self : returns an instance of self.
        """
        self._set_params(**params)
        X = np.asanyarray(X, dtype=np.float)
        Y = np.asanyarray(Y, dtype=np.float)

        if self.fit_intercept:
            self._xmean = X.mean(axis=0)
            self._ymean = Y.mean(axis=0)
            X = X - self._xmean
            Y = Y - self._ymean
        else:
            self._xmean = 0.
            self._ymean = 0.

        # todo, shouldn't most of these have trailing underscores ?
        self.coef_, self.alpha, self.beta, self.sigma, self.log_likelihood = \
            bayesian_ridge_regression(X, Y, self.step_th, self.th_w, self.ll_bool)

        self.intercept_ = self._ymean - np.dot(self._xmean, self.coef_)

        # Store explained variance for __str__
        self.explained_variance_ = self._explained_variance(X, Y)

        return self


class ARDRegression(LinearModel):
    """
    Encapsulate various bayesian regression algorithms
    """
    # TODO: add intercept

    def __init__(self, ll_bool=False, step_th=300, th_w=1.e-12,
            alpha_th=1e16):
        self.ll_bool = ll_bool
        self.step_th = step_th
        self.th_w = th_w
        self.alpha_th = alpha_th

    def fit(self, X, Y, **params):
        self._set_params(**params)
        X = np.asanyarray(X, dtype=np.float)
        Y = np.asanyarray(Y, dtype=np.float)
        self.w ,self.alpha ,self.beta ,self.sigma ,self.log_likelihood = \
            bayesian_regression_ard(X, Y, self.step_th, self.th_w,\
            self.alpha_th, self.ll_bool)

        # Store explained variance for __str__
        self.explained_variance_ = self._explained_variance(X, Y)
        return self

    def predict(self, T):
        return np.dot(T, self.w)



### helper methods
### we should homogeneize this

def bayesian_ridge_regression(X , Y, step_th=300, th_w = 1.e-12, ll_bool=False):
    """
    Bayesian ridge regression. Optimize the regularization parameters alpha
    (precision of the weights) and beta (precision of the noise) within a simple
    bayesian framework (MAP).

    Parameters
    ----------
    X : numpy array of shape (length,features)
    data
    Y : numpy array of shape (length)
    target
    step_th : int (defaut is 300)
          Stop the algorithm after a given number of steps.
    th_w : float (defaut is 1.e-12)
       Stop the algorithm if w has converged.
    ll_bool  : boolean (default is False).
           If True, compute the log-likelihood at each step of the model.

    Returns
    -------
    w : numpy array of shape (nb_features)
         mean of the weights distribution.
    alpha : float
       precision of the weights.
    beta : float
       precision of the noise.
    sigma : numpy array of shape (nb_features,nb_features)
        variance-covariance matrix of the weights
    log_likelihood : list of float of size steps.
             Compute (if asked) the log-likelihood of the model.

    Examples
    --------
    >>> X = np.array([[1], [2]])
    >>> Y = np.array([1, 2])
    >>> w = bayesian_ridge_regression(X,Y)

    Notes
    -----
    See Bishop p 167-169 for more details.
    """

    beta = 1./np.var(Y)
    alpha = 1.0

    log_likelihood = []
    has_converged = False
    gram = np.dot(X.T, X)
    ones = np.eye(gram.shape[1])
    sigma = linalg.pinv(alpha*ones + beta*gram)
    w = np.dot(beta*sigma,np.dot(X.T,Y))
    old_w = np.copy(w)
    eigen = np.real(linalg.eigvals(gram.T))
    while not has_converged and step_th:

        ### Update Parameters
        # alpha
        lmbd_ = np.dot(beta, eigen)
        gamma_ = (lmbd_/(alpha + lmbd_)).sum()
        alpha = gamma_/np.dot(w.T, w)

        # beta
        residual_ = (Y - np.dot(X, w))**2
        beta = (X.shape[0]-gamma_) / residual_.sum()

        ### Compute mu and sigma
        sigma = linalg.pinv(alpha*ones + beta*gram)
        w = np.dot(beta*sigma,np.dot(X.T,Y))
        step_th -= 1

        # convergence : compare w
        has_converged =  (np.sum(np.abs(w-old_w))<th_w)
        old_w = w

    ### Compute the log likelihood
    if ll_bool:
        residual_ = (Y - np.dot(X, w))**2
        ll = 0.5*X.shape[1]*np.log(alpha) + 0.5*X.shape[0]*np.log(beta)
        ll -= (0.5*beta*residual_.sum()+ 0.5*alpha*np.dot(w.T,w))
        ll -= fast_logdet(alpha*ones + beta*gram)
        ll -= X.shape[0]*np.log(2*np.pi)
        log_likelihood.append(ll)

    return w, alpha, beta, sigma, log_likelihood



def bayesian_regression_ard(X, Y, step_th=300, th_w=1.e-12, \
                alpha_th=1.e+16, ll_bool=False):
    """
    Bayesian ard-based regression. Optimize the regularization parameters alpha
    (vector of precisions of the weights) and beta (precision of the noise).


    Parameters
    ----------
    X : numpy array of shape (length,features)
    data
    Y : numpy array of shape (length)
    target
    step_th : int (defaut is 300)
          Stop the algorithm after a given number of steps.
    th_w : float (defaut is 1.e-12)
       Stop the algorithm if w has converged.
    alpha_th : number
           threshold on the alpha, to avoid divergence. Remove those features
       from the weights computation if is alpha > alpha_th  (default is
        1.e+16).
    ll_bool  : boolean (default is False).
           If True, compute the log-likelihood at each step of the model.

    Returns
    -------
    w : numpy array of shape (nb_features)
         mean of the weights distribution.
    alpha : numpy array of shape (nb_features)
       precision of the weights.
    beta : float
       precision of the noise.
    sigma : numpy array of shape (nb_features,nb_features)
        variance-covariance matrix of the weights
    log_likelihood : list of float of size steps.
             Compute (if asked) the log-likelihood of the model.

    Examples
    --------

    Notes
    -----
    See Bishop chapter 7.2. for more details.
    This should be resived. It is not efficient and I wonder if we
    can't use libsvm for this.
    """
    gram = np.dot(X.T, X)
    beta = 1./np.var(Y)
    alpha = np.ones(gram.shape[1])


    log_likelihood = None
    if ll_bool :
        log_likelihood = []
    has_converged = False
    ones = np.eye(gram.shape[1])
    sigma = linalg.pinv(alpha*ones + beta*gram)
    w = np.dot(beta*sigma,np.dot(X.T,Y))
    old_w = np.copy(w)
    keep_a  = np.ones(X.shape[1],dtype=bool)
    while not has_converged and step_th:

        # alpha
        gamma_ = 1 - alpha[keep_a]*np.diag(sigma)
        alpha[keep_a] = gamma_/w[keep_a]**2

        # beta
        residual_ = (Y - np.dot(X[:,keep_a], w[keep_a]))**2
        beta = (X.shape[0]-gamma_.sum()) / residual_.sum()

        ### Avoid divergence of the values by setting a maximum values of the
        ### alpha
        keep_a = alpha<alpha_th
        gram = np.dot(X.T[keep_a,:], X[:,keep_a])

        ### Compute mu and sigma
        ones = np.eye(gram.shape[1])
        sigma = linalg.pinv(alpha[keep_a]*ones+ beta*gram)
        w[keep_a] = np.dot(beta*sigma,np.dot(X.T[keep_a,:],Y))
        step_th -= 1

        # convergence : compare w
        has_converged =  (np.sum(np.abs(w-old_w))<th_w)
        old_w = w


    ### Compute the log likelihood
    if ll_bool :
        A_ = np.eye(X.shape[1])/alpha
        C_ = (1./beta)*np.eye(X.shape[0]) + np.dot(X,np.dot(A_,X.T))
        ll = X.shape[0]*np.log(2*np.pi)+fast_logdet(C_)
        ll += np.dot(Y.T,np.dot(linalg.pinv(C_),Y))
        log_likelihood.append(-0.5*ll)

    return w, alpha, beta, sigma, log_likelihood


# Author: Alexandre Gramfort <alexandre.gramfort@inria.fr>
#         Fabian Pedregosa <fabian.pedregosa@inria.fr>
#         Olivier Grisel <olivier.grisel@ensta.org>
#         Vincent Michel <vincent.michel@inria.fr>
#
# License: BSD Style.


"""
Generalized Linear models.
"""

import numpy as np

from ..base import BaseEstimator, RegressorMixin

###
### TODO: intercept for all models
### We should define a common function to center data instead of
### repeating the same code inside each fit method.
###
### Also, bayesian_ridge_regression and bayesian_regression_ard
### should be squashed into its respective objects.
###

class LinearModel(BaseEstimator, RegressorMixin):
    """Base class for Linear Models"""

    def predict(self, X):
        """
        Predict using the linear model

        Parameters
        ----------
        X : numpy array of shape [n_samples,n_features]

        Returns
        -------
        C : array, shape = [n_samples]
            Returns predicted values.
        """
        X = np.asanyarray(X)
        return np.dot(X, self.coef_) + self.intercept_

    def _explained_variance(self, X, Y):
        """Compute explained variance a.k.a. r^2"""
        ## TODO: this should have a tests.
        return 1 - np.linalg.norm(Y - self.predict(X))**2 \
                         / np.linalg.norm(Y)**2

    def __str__(self):
        if self.coef_ is not None:
            return ("%s \n%s #... Fitted: explained variance=%s" %
                    (repr(self), ' '*len(self.__class__.__name__),  
                     self.explained_variance_))
        else:
            return "%s \n#... Not fitted to data" % repr(self)


class LinearRegression(LinearModel):
    """
    Ordinary least squares Linear Regression.

    Attributes
    ----------
    `coef_` : array
        Estimated coefficients for the linear regression problem.

    `intercept_` : array
        Independent term in the linear model.

    Notes
    -----
    From the implementation point of view, this is just plain Ordinary
    Least Squares (numpy.linalg.lstsq) wrapped as a predictor object.

    """

    def __init__(self, fit_intercept=True):
        self.fit_intercept = fit_intercept


    def fit(self, X, Y, **params):
        """
        Fit linear model.

        Parameters
        ----------
        X : numpy array of shape [n_samples,n_features]
            Training data
        Y : numpy array of shape [n_samples]
            Target values
        fit_intercept : boolean, optional
            wether to calculate the intercept for this model. If set
            to false, no intercept will be used in calculations
            (e.g. data is expected to be already centered).

        Returns
        -------
        self : returns an instance of self.
        """
        self._set_params(**params)
        X = np.asanyarray( X )
        Y = np.asanyarray( Y )

        if self.fit_intercept:
            # augmented X array to store the intercept
            X = np.c_[X, np.ones(X.shape[0])]
        self.coef_, self.residues_, self.rank_, self.singular_ = \
                np.linalg.lstsq(X, Y)
        if self.fit_intercept:
            self.intercept_ = self.coef_[-1]
            self.coef_ = self.coef_[:-1]
        else:
            self.intercept_ = 0
        return self



"""
Benchmark for the LARS algorithm.

Work in progress
"""

from datetime import datetime
import numpy as np
from scikits.learn import glm

n, m = 100, 50000

X = np.random.randn(n, m)
y = np.random.randn(n)

print "Computing regularization path using the LARS ..."
start = datetime.now()
alphas, active, path = glm.lars_path(X, y, method='lasso')
print "This took ", datetime.now() - start




"""
=======================================
Receiver operating characteristic (ROC)
=======================================

Example of Receiver operating characteristic (ROC) metric to
evaluate the quality of the output of a classifier.
"""

import random
import numpy as np
import pylab as pl
from scikits.learn import svm, datasets
from scikits.learn.metrics import roc, auc

# import some data to play with
iris = datasets.load_iris()
X = iris.data
y = iris.target
X, y = X[y!=2], y[y!=2]
n_samples, n_features = X.shape
p = range(n_samples)
random.seed(0)
random.shuffle(p)
X, y = X[p], y[p]
half = int(n_samples/2)

# Add noisy features
X = np.c_[X,np.random.randn(n_samples, 200*n_features)]

# Run classifier
classifier = svm.SVC(kernel='linear', probability=True)
probas_ = classifier.fit(X[:half],y[:half]).predict_proba(X[half:])

# Compute ROC curve and area the curve
fpr, tpr, thresholds = roc(y[half:], probas_[:,1])
roc_auc = auc(fpr, tpr)
print "Area under the ROC curve : %f" % roc_auc

# Plot ROC curve
pl.figure(-1)
pl.clf()
pl.plot(fpr, tpr, label='ROC curve (area = %0.2f)' % roc_auc)
pl.plot([0, 1], [0, 1], 'k--')
pl.xlim([0.0,1.0])
pl.ylim([0.0,1.0])
pl.xlabel('False Positive Rate')
pl.ylabel('True Positive Rate')
pl.title('Receiver operating characteristic example')
pl.legend(loc="lower right")
pl.show()

"""
================
Confusion matrix
================

Example of confusion matrix usage to evaluate the quality
of the output of a classifier.
"""

import random
import pylab as pl
from scikits.learn import svm, datasets
from scikits.learn.metrics import confusion_matrix

# import some data to play with
iris = datasets.load_iris()
X = iris.data
y = iris.target
n_samples, n_features = X.shape
p = range(n_samples)
random.seed(0)
random.shuffle(p)
X, y = X[p], y[p]
half = int(n_samples/2)

# Run classifier
classifier = svm.SVC(kernel='linear')
y_ = classifier.fit(X[:half],y[:half]).predict(X[half:])

# Compute confusion matrix
cm = confusion_matrix(y[half:], y_)

print cm

# Show confusion matrix
pl.matshow(cm)
pl.title('Confusion matrix')
pl.colorbar()
pl.show()
"""
=================
Nearest Neighbors
=================

Sample usage of Support Vector Machines to classify a sample.
It will plot the decision surface and the support vectors.
"""

import numpy as np
import pylab as pl
from scikits.learn import neighbors, datasets

# import some data to play with
iris = datasets.load_iris()
X = iris.data[:, :2] # we only take the first two features. We could
                     # avoid this ugly slicing by using a two-dim dataset
Y = iris.target

h=.02 # step size in the mesh

# we create an instance of SVM and fit out data. We do not scale our
# data since we want to plot the support vectors
clf = neighbors.Neighbors()
clf.fit(X, Y)

# Plot the decision boundary. For that, we will asign a color to each
# point in the mesh [x_min, m_max]x[y_min, y_max].
x_min, x_max = X[:,0].min()-1, X[:,0].max()+1
y_min, y_max = X[:,1].min()-1, X[:,1].max()+1
xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])

# Put the result into a color plot
Z = Z.reshape(xx.shape)
pl.set_cmap(pl.cm.Paired)
pl.pcolormesh(xx, yy, Z)

# Plot also the training points
pl.scatter(X[:,0], X[:,1], c=Y)
# and the support vectors
pl.title('3-Class classification using Nearest Neighbors')
pl.axis('tight')
pl.show()

"""
Recursive feature elimination
=======================================================================

A recursive feature elimination is performed prior to SVM classification.
"""

from scikits.learn.svm import SVC
from scikits.learn.cross_val import StratifiedKFold
from scikits.learn import datasets
from scikits.learn.rfe import RFE, RFECV
from scikits.learn.metrics import zero_one


################################################################################
# Loading the Digits dataset
digits = datasets.load_digits()

# To apply an classifier on this data, we need to flatten the image, to
# turn the data in a (samples, feature) matrix:
n_samples = len(digits.images)
X = digits.images.reshape((n_samples, -1))
y = digits.target


################################################################################
# Create the RFE object and compute a cross-validated score

svc = SVC(kernel="linear", C=1)
rfe = RFE(estimator=svc, n_features=1, percentage=0.1)
rfe.fit(X, y)

image_ranking_ = rfe.ranking_.reshape(digits.images[0].shape)

import pylab as pl
pl.matshow(image_ranking_)
pl.colorbar()
pl.title('Ranking of voxels with RFE')
pl.show()


"""
============================
Linear Discriminant Analysis
============================

A classification example using Linear Discriminant Analysis (LDA).

"""

import numpy as np

################################################################################
# import some data to play with

# The IRIS dataset
from scikits.learn import datasets
iris = datasets.load_iris()

# Some noisy data not correlated
E = np.random.normal(size=(len(iris.data), 35))

# Add the noisy data to the informative features
X = np.hstack((iris.data, E))
y = iris.target

################################################################################
# LDA
from scikits.learn.lda import LDA
lda = LDA()

y_pred = lda.fit(X, y).predict(X)

print "Number of mislabeled points : %d"%(y != y_pred).sum()

"""
===============================================================
Receiver operating characteristic (ROC) with cross validation
===============================================================

Example of Receiver operating characteristic (ROC) metric to
evaluate the quality of the output of a classifier using
cross-validation.
"""

import numpy as np
from scipy import interp
import pylab as pl

from scikits.learn import svm, datasets
from scikits.learn.metrics import roc, auc
from scikits.learn.cross_val import StratifiedKFold

################################################################################
# Data IO and generation

# import some data to play with
iris = datasets.load_iris()
X = iris.data
y = iris.target
X, y = X[y!=2], y[y!=2]
n_samples, n_features = X.shape

# Add noisy features
X = np.c_[X,np.random.randn(n_samples, 200*n_features)]

################################################################################
# Classification and ROC analysis

# Run classifier with crossvalidation and plot ROC curves
cv = StratifiedKFold(y, k=6)
classifier = svm.SVC(kernel='linear', probability=True)

mean_tpr = 0.0
mean_fpr = np.linspace(0, 1, 100)
all_tpr = []

for i, (train, test) in enumerate(cv):
    probas_ = classifier.fit(X[train], y[train]).predict_proba(X[test])
    # Compute ROC curve and area the curve
    fpr, tpr, thresholds = roc(y[test], probas_[:,1])
    mean_tpr += interp(mean_fpr, fpr, tpr)
    mean_tpr[0] = 0.0
    roc_auc = auc(fpr, tpr)
    pl.plot(fpr, tpr, lw=1, label='ROC fold %d (area = %0.2f)' % (i, roc_auc))

pl.plot([0, 1], [0, 1], '--', color=(0.6,0.6,0.6), label='Luck')

mean_tpr /= len(cv)
mean_tpr[-1] = 1.0
mean_auc = auc(mean_fpr, mean_tpr)
pl.plot(mean_fpr, mean_tpr, 'k--', 
        label='Mean ROC (area = %0.2f)' % mean_auc, lw=2)

pl.xlim([-0.05,1.05])
pl.ylim([-0.05,1.05])
pl.xlabel('False Positive Rate')
pl.ylabel('True Positive Rate')
pl.title('Receiver operating characteristic example')
pl.legend(loc="lower right")
pl.show()

"""
Parameter estimation using grid search with a nested cross-validation
=======================================================================

The classifier is optimized by "nested" cross-validation using the
GridSearchCV object.

The performance of the selected parameters is evaluated using
cross-validation (different than the nested cross-validation that is used
to select the best classifier). 

"""

import numpy as np
from scikits.learn.svm import SVC
from scikits.learn.cross_val import StratifiedKFold
from scikits.learn.grid_search import GridSearchCV
from scikits.learn import datasets
from scikits.learn.metrics import zero_one

################################################################################
# Loading the Digits dataset
digits = datasets.load_digits()

# To apply an classifier on this data, we need to flatten the image, to
# turn the data in a (samples, feature) matrix:
n_samples = len(digits.images)
X = digits.images.reshape((n_samples, -1))
y = digits.target

################################################################################
# Set the parameters by cross-validation
tuned_parameters = [{'kernel':('rbf', ), 'gamma':[1e-3, 1e-4]},
                    {'kernel':('linear', )}]

clf = GridSearchCV(SVC(C=1), tuned_parameters, n_jobs=2)

y_pred = []
y_true = []
for train, test in StratifiedKFold(y, 2):
    cv = StratifiedKFold(y[train], 5)
    y_pred.append(clf.fit(X[train], y[train], cv=cv).predict(X[test]))
    y_true.append(y[test])

y_pred = np.concatenate(y_pred)
y_true = np.concatenate(y_true)
classif_rate = np.mean(y_pred == y_true) * 100
print "Classification rate : %f" % classif_rate

"""
===============================
Univariate Feature Selection
===============================

An example showing univariate feature selection.

Noisy (non informative) features are added to the iris data and
univariate feature selection is applied. For each feature, we plot the
p-values for the univariate feature selection and the corresponding
weights of an SVM. We can see that univariate feature selection
selects the informative features and that these have larger SVM weights.

In the total set of features, only the 4 first ones are significant. We
can see that they have the highest score with univariate feature
selection. The SVM attributes small weights to these features, but these
weight are non zero. Applying univariate feature selection before the SVM
increases the SVM weight attributed to the significant features, and will
thus improve classification.
"""

import numpy as np
import pylab as pl


################################################################################
# import some data to play with

# The IRIS dataset
from scikits.learn import datasets, svm
iris = datasets.load_iris()

# Some noisy data not correlated
E = np.random.normal(size=(len(iris.data), 35))

# Add the noisy data to the informative features
x = np.hstack((iris.data, E))
y = iris.target

################################################################################
pl.figure(1)
pl.clf()

x_indices = np.arange(x.shape[-1])

################################################################################
# Univariate feature selection
from scikits.learn.feature_selection import SelectFpr, f_classif
# As a scoring function, we use a F test for classification
# We use the default selection function: the 10% most significant
# features

selector = SelectFpr(f_classif, alpha=0.1)
selector.fit(x, y)
scores = -np.log10(selector._pvalues)
scores /= scores.max()
pl.bar(x_indices-.45, scores, width=.3,
        label=r'Univariate score ($-Log(p_{value})$)',
        color='g')

################################################################################
# Compare to the weights of an SVM
clf = svm.SVC(kernel='linear')
clf.fit(x, y)

svm_weights = (clf.coef_**2).sum(axis=0)
svm_weights /= svm_weights.max()
pl.bar(x_indices-.15, svm_weights, width=.3, label='SVM weight',
        color='r')


# ################################################################################
# # Now fit an SVM with added feature selection
# selector = univ_selection.Univ(
#                 score_func=univ_selection.f_classif)

# selector.fit(x, clf.predict(x))
# svm_weights = (clf.support_**2).sum(axis=0)
# svm_weights /= svm_weights.max()
# full_svm_weights = np.zeros(selector.support_.shape)
# full_svm_weights[selector.support_] = svm_weights
# pl.bar(x_indices+.15, full_svm_weights, width=.3,
#         label='SVM weight after univariate selection',
#         color='b')

pl.title("Comparing feature selection")
pl.xlabel('Feature number')
pl.yticks(())
pl.axis('tight')
pl.legend(loc='upper right')
pl.show()


"""

===========================================
Finding structure in the stock market
===========================================



An example of playing with stock market data to try and find some
structure in it.
"""
# Author: Gael Varoquaux gael.varoquaux@normalesup.org
# License: BSD

import datetime
from matplotlib import finance
import numpy as np

from scikits.learn import cluster

# Choose a time period reasonnably calm (not too long ago so that we get
# high-tech firms, and before the 2008 crash)
d1 = datetime.datetime(2003, 01, 01)
d2 = datetime.datetime(2008, 01, 01)

symbol_dict = {
        'TOT'  : 'Total',
        'XOM'  : 'Exxon',
        'CVX'  : 'Chevron',
        'COP'  : 'ConocoPhillips',
        'VLO'  : 'Valero Energy',
        'MSFT' : 'Microsoft',
        'IBM'  : 'IBM',
        'TWX'  : 'Time Warner',
        'CMCSA': 'Comcast',
        'CVC'  : 'Cablevision',
        'YHOO' : 'Yahoo',
        'DELL' : 'Dell',
        'HPQ'  : 'Hewlett-Packard',
        'AMZN' : 'Amazon',
        'TM'   : 'Toyota',
        'CAJ'  : 'Canon',
        'MTU'  : 'Mitsubishi',
        'SNE'  : 'Sony',
        'F'    : 'Ford',
        'HMC'  : 'Honda',
        'NAV'  : 'Navistar',
        'NOC'  : 'Northrop Grumman',
        'BA'   : 'Boeing',
        'KO'   : 'Coca Cola',
        'MMM'  : '3M',
        'MCD'  : 'Mc Donalds',
        'PEP'  : 'Pepsi',
        'KFT'  : 'Kraft Foods',
        'K'    : 'Kellogg',
        'UN'   : 'Unilever',
        'MAR'  : 'Marriott',
        'PG'   : 'Procter Gamble',
        'CL'   : 'Colgate-Palmolive',
        'NWS'  : 'News Corporation',
        'GE'   : 'General Electrics',
        'WFC'  : 'Wells Fargo',
        'JPM'  : 'JPMorgan Chase',
        'AIG'  : 'AIG',
        'AXP'  : 'American express',
        'BAC'  : 'Bank of America',
        'GS'   : 'Goldman Sachs',
        'AAPL' : 'Apple',
        'SAP'  : 'SAP',
        'CSCO' : 'Cisco',
        'TXN'  : 'Texas instruments',
        'XRX'  : 'Xerox',
        'LMT'  : 'Lookheed Martin',
        'WMT'  : 'Wal-Mart',
        'WAG'  : 'Walgreen',
        'HD'   : 'Home Depot',
        'GSK'  : 'GlaxoSmithKline',
        'PFE'  : 'Pfizer',
        'SNY'  : 'Sanofi-Aventis',
        'NVS'  : 'Novartis',
        'KMB'  : 'Kimberly-Clark',
        'R'    : 'Ryder',
        'GD'   : 'General Dynamics',
        'RTN'  : 'Raytheon',
        'CVS'  : 'CVS',
        'CAT'  : 'Caterpillar',
        'DD'   : 'DuPont de Nemours',
    }

symbols, names = np.array(symbol_dict.items()).T

quotes = [finance.quotes_historical_yahoo(symbol, d1, d2, asobject=True)
                for symbol in symbols]

#volumes = np.array([q.volume for q in quotes]).astype(np.float)
open    = np.array([q.open   for q in quotes]).astype(np.float)
close   = np.array([q.close  for q in quotes]).astype(np.float)
variation = close - open
correlations = np.corrcoef(variation)

_, labels = cluster.affinity_propagation(correlations)

for i in range(labels.max()+1):
    print 'Cluster %i: %s' % ((i+1),
                              ', '.join(names[labels==i]))

"""
================================
Classification of text documents
================================

This is an example showing how the scikit-learn can be used to classify
documents by topics using a bag-of-words approach.

The dataset used in this example is the 20 newsgroups dataset and should be
downloaded from the http://mlcomp.org (free registration required):

  http://mlcomp.org/datasets/379

Once downloaded unzip the arhive somewhere on your filesystem. For instance in::

  % mkdir -p ~/data/mlcomp
  % cd  ~/data/mlcomp
  % unzip /path/to/dataset-379-20news-18828_XXXXX.zip

You should get a folder ``~/data/mlcomp/379`` with a file named ``metadata`` and
subfolders ``raw``, ``train`` and ``test`` holding the text documents organized by
newsgroups.

Then set the ``MLCOMP_DATASETS_HOME`` environment variable pointing to
the root folder holding the uncompressed archive::

  % export MLCOMP_DATASETS_HOME="~/data/mlcomp"

Then you are ready to run this example using your favorite python shell::

  % ipython examples/mlcomp_document_classification.py

"""
# Author: Olivier Grisel <olivier.grisel@ensta.org>
# License: Simplified BSD

from time import time
import sys
import os
import numpy as np
import pylab as pl

from scikits.learn.datasets import load_mlcomp
from scikits.learn.svm import LinearSVC
from scikits.learn.metrics import confusion_matrix

if 'MLCOMP_DATASETS_HOME' not in os.environ:
    print "Please follow those instructions to get started:"
    print __doc__
    sys.exit(0)

# Load the training set
print "Loading 20 newsgroups training set... "
t0 = time()
news_train = load_mlcomp('20news-18828', 'train')
print "done in %fs" % (time() - t0)

# The documents have been hashed into TF-IDF (Term Frequencies times Inverse
# Document Frequencies) vectors of a fixed dimension.
# Currently most scikits.learn wrappers or algorithm implementations are unable
# to leverage efficiently a sparse datastracture; hence we use a dense
# representation of a text dataset. Efficient handling of sparse data
# structures should be expected in an upcoming version of scikits.learn
print "n_samples: %d, n_features: %d" % news_train.data.shape

print "Training a linear classification model with L1 penalty... "
parameters = {
    'loss': 'l1',
    'penalty': 'l2',
    'C': 10,
    'dual': True,
    'eps': 1e-4,
}
print "parameters:", parameters
t0 = time()
clf = LinearSVC(**parameters).fit(news_train.data, news_train.target)
print "done in %fs" % (time() - t0)
print "Percentage of non zeros coef: %f" % (np.mean(clf.coef_ != 0) * 100)

print "Loading 20 newsgroups test set... "
t0 = time()
news_test = load_mlcomp('20news-18828', 'test')
print "done in %fs" % (time() - t0)

print "Predicting the labels of the test set..."
t0 = time()
pred = clf.predict(news_test.data)
print "done in %fs" % (time() - t0)
print "Classification accuracy: %f" % (np.mean(pred == news_test.target) * 100)

cm = confusion_matrix(news_test.target, pred)
print "Confusion matrix:"
print cm

# Show confusion matrix
pl.matshow(cm)
pl.title('Confusion matrix')
pl.colorbar()
pl.show()

"""
Recursive feature elimination with cross-validation
===================================================
"""

# Recursive feature elimination with automatic tuning of the
# number of features selected with cross-validation

from scikits.learn.svm import SVC
from scikits.learn.cross_val import StratifiedKFold
from scikits.learn.rfe import RFECV
from scikits.learn.datasets import samples_generator
from scikits.learn.metrics import zero_one

################################################################################
# Loading a dataset

X, y = samples_generator.test_dataset_classif(n_features=500, k=5, seed=0)

################################################################################
# Create the RFE object and compute a cross-validated score

svc = SVC(kernel='linear')
rfecv = RFECV(estimator=svc, n_features=2, percentage=0.1, loss_func=zero_one)
rfecv.fit(X, y, cv=StratifiedKFold(y, 2))

print 'Optimal number of features : %d' % rfecv.support_.sum()

import pylab as pl
pl.figure()
pl.plot(rfecv.cv_scores_)
pl.show()


"""
==========================
Pipeline Anova SVM
==========================

Simple usages of pipeline:
- ANOVA SVM-C
"""

from scikits.learn import svm
from scikits.learn.datasets import samples_generator
from scikits.learn.feature_selection.univariate_selection import SelectKBest,f_regression
from scikits.learn.pipeline import Pipeline

# import some data to play with
X, y = samples_generator.test_dataset_classif(k=5)


# ANOVA SVM-C
# 1) anova filter, take 5 best ranked features 
anova_filter = SelectKBest(f_regression, k=5)
# 2) svm
clf = svm.SVC(kernel='linear')

anova_svm = Pipeline([anova_filter], clf)
anova_svm.fit(X, y)
anova_svm.predict(X)


"""
============================
Gaussian Naive Bayes
============================

A classification example using Gaussian Naive Bayes (GNB).

"""

import numpy as np
import pylab as pl


################################################################################
# import some data to play with

# The IRIS dataset
from scikits.learn import datasets, svm
iris = datasets.load_iris()


X = iris.data
y = iris.target

################################################################################
# GNB
from scikits.learn.naive_bayes import GNB
gnb = GNB()

y_pred = gnb.fit(X, y).predict(X)

print "Number of mislabeled points : %d" % (y != y_pred).sum()

"""
======================================================
Classification of text documents using sparse features
======================================================

This is an example showing how the scikit-learn can be used to classify
documents by topics using a bag-of-words approach. This example uses
a scipy.sparse matrix to store the features instead of standard numpy arrays.

The dataset used in this example is the 20 newsgroups dataset and should be
downloaded from the http://mlcomp.org (free registration required):

  http://mlcomp.org/datasets/379

Once downloaded unzip the arhive somewhere on your filesystem. For instance in::

  % mkdir -p ~/data/mlcomp
  % cd  ~/data/mlcomp
  % unzip /path/to/dataset-379-20news-18828_XXXXX.zip

You should get a folder ``~/data/mlcomp/379`` with a file named ``metadata`` and
subfolders ``raw``, ``train`` and ``test`` holding the text documents organized by
newsgroups.

Then set the ``MLCOMP_DATASETS_HOME`` environment variable pointing to
the root folder holding the uncompressed archive::

  % export MLCOMP_DATASETS_HOME="~/data/mlcomp"

Then you are ready to run this example using your favorite python shell::

  % ipython examples/mlcomp_sparse_document_classification.py

"""
# Author: Olivier Grisel <olivier.grisel@ensta.org>
# License: Simplified BSD

from time import time
import sys
import os
import numpy as np
import scipy.sparse as sp
import pylab as pl

from scikits.learn.datasets import load_mlcomp
from scikits.learn.sparse.svm import LinearSVC
from scikits.learn.metrics import confusion_matrix

if 'MLCOMP_DATASETS_HOME' not in os.environ:
    print "Please follow those instructions to get started:"
    print __doc__
    sys.exit(0)

# Load the training set
print "Loading 20 newsgroups training set... "
t0 = time()
news_train = load_mlcomp('20news-18828', 'train', sparse=True)
print "done in %fs" % (time() - t0)

print "news_train.data is sparse: ",
print sp.issparse(news_train.data)

# The documents have been hashed into TF-IDF (Term Frequencies times Inverse
# Document Frequencies) vectors of a fixed dimension.
print "n_samples: %d, n_features: %d" % news_train.data.shape

print "Training a linear SVM (hinge loss and L2 regularizer)..."
parameters = {
    'loss': 'l2',
    'penalty': 'l2',
    'C': 10,
    'dual': False,
    'eps': 1e-4,
}
print "parameters:", parameters
t0 = time()
clf = LinearSVC(**parameters).fit(news_train.data, news_train.target)
print "done in %fs" % (time() - t0)
print "Percentage of non zeros coef: %f" % (np.mean(clf.coef_ != 0) * 100)

print "Loading 20 newsgroups test set... "
t0 = time()
news_test = load_mlcomp('20news-18828', 'test', sparse=True)
print "done in %fs" % (time() - t0)

print "Predicting the labels of the test set..."
t0 = time()
pred = clf.predict(news_test.data)
print "done in %fs" % (time() - t0)
print "Classification accuracy: %f" % (np.mean(pred == news_test.target) * 100)

cm = confusion_matrix(news_test.target, pred)
print "Confusion matrix:"
print cm

# Show confusion matrix
pl.matshow(cm)
pl.title('Confusion matrix')
pl.colorbar()
pl.show()

"""
==============================================================
Linear Discriminant Analysis & Quadratic Discriminant Analysis
==============================================================

Plot the confidence ellipsoids of each class and decision boundary
"""

from scipy import linalg
import numpy as np
import pylab as pl
import matplotlib as mpl
from matplotlib import collections, colors

from scikits.learn.lda import LDA
from scikits.learn.qda import QDA

################################################################################
# colormap
cmap = colors.LinearSegmentedColormap('red_blue_classes',
    {'red' : [(0, 1, 1), (1, 0.7, 0.7)],
     'green' : [(0, 0.7, 0.7), (1, 0.7, 0.7)],
     'blue' : [(0, 0.7, 0.7), (1, 1, 1)]
    })
pl.cm.register_cmap(cmap=cmap)


################################################################################
# generate datasets
def dataset_fixed_cov():
    '''Generate 2 Gaussians samples with the same covariance matrix'''
    n, dim = 300, 2
    np.random.seed(0)
    C = np.array([[0., -0.23], [0.83, .23]])
    X = np.r_[np.dot(np.random.randn(n, dim), C),
              np.dot(np.random.randn(n, dim), C) + np.array([1, 1])]
    y = np.hstack((np.zeros(n), np.ones(n)))
    return X, y

def dataset_cov():
    '''Generate 2 Gaussians samples with different covariance matrices'''
    n, dim = 300, 2
    np.random.seed(0)
    C = np.array([[0., -1.], [2.5, .7]]) * 2.
    X = np.r_[np.dot(np.random.randn(n, dim), C),
              np.dot(np.random.randn(n, dim), C.T) + np.array([1, 4])]
    y = np.hstack((np.zeros(n), np.ones(n)))
    return X, y


################################################################################
# plot functions
def plot_data(lda, X, y, y_pred, fig_index):
    splot = pl.subplot(2, 2, fig_index)
    if fig_index == 1:
        pl.title('Linear Discriminant Analysis')
        pl.ylabel('Fixed covariance')
    elif fig_index == 2:
        pl.title('Quadratic Discriminant Analysis')
    elif fig_index == 3:
        pl.ylabel('Different covariances')

    tp = (y == y_pred) # True Positive
    tp0, tp1 = tp[y == 0], tp[y == 1]
    X0, X1 = X[y == 0], X[y == 1]
    X0_tp, X0_fp = X0[tp0], X0[tp0 != True]
    X1_tp, X1_fp = X1[tp1], X1[tp1 != True]
    xmin, xmax = X[:, 0].min(), X[:, 0].max()
    ymin, ymax = X[:, 1].min(), X[:, 1].max()

    # class 0: dots 
    pl.plot(X0_tp[:, 0], X0_tp[:, 1], 'o', color='red')
    pl.plot(X0_fp[:, 0], X0_fp[:, 1], '.', color='#990000') # dark red

    # class 1: dots
    pl.plot(X1_tp[:, 0], X1_tp[:, 1], 'o', color='blue')
    pl.plot(X1_fp[:, 0], X1_fp[:, 1], '.', color='#000099') # dark blue

    # class 0 and 1 : areas
    nx, ny = 200, 100
    x_min, x_max = pl.xlim()
    y_min, y_max = pl.ylim()
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, nx),
                         np.linspace(y_min, y_max, ny))
    Z = lda.predict_proba(np.c_[xx.ravel(), yy.ravel()])
    Z = Z[:, 1].reshape(xx.shape)
    pl.pcolormesh(xx, yy, Z, cmap='red_blue_classes',
                        norm=colors.Normalize(0., 1.))
    pl.contour(xx, yy, Z, [0.5], linewidths=2., colors='k')

    # means
    pl.plot(lda.means_[0][0], lda.means_[0][1],
            'o', color='black', markersize=10)
    pl.plot(lda.means_[1][0], lda.means_[1][1],
            'o', color='black', markersize=10)

    return splot

def plot_ellipse(splot, mean, cov, color):
    v, w = linalg.eigh(cov)
    u = w[0] / linalg.norm(w[0])
    angle = np.arctan(u[1]/u[0])
    angle = 180 * angle / np.pi # convert to degrees
    # filled gaussian at 2 standard deviation
    ell = mpl.patches.Ellipse(mean, 2 * v[0] ** 0.5, 2 * v[1] ** 0.5,
                                            180 + angle, color=color)
    ell.set_clip_box(splot.bbox)
    ell.set_alpha(0.5)
    splot.add_artist(ell)

def plot_lda_cov(lda, splot):
    plot_ellipse(splot, lda.means_[0], lda.covariance_, 'red')
    plot_ellipse(splot, lda.means_[1], lda.covariance_, 'blue')

def plot_qda_cov(qda, splot):
    plot_ellipse(splot, qda.means_[0], qda.covariances_[0], 'red')
    plot_ellipse(splot, qda.means_[1], qda.covariances_[1], 'blue')

################################################################################
for i, (X, y) in enumerate([dataset_fixed_cov(), dataset_cov()]):
    # LDA
    lda = LDA()
    y_pred = lda.fit(X, y, store_covariance=True).predict(X)
    splot = plot_data(lda, X, y, y_pred, fig_index=2 * i + 1)
    plot_lda_cov(lda, splot)
    pl.axis('tight')

    # QDA
    qda = QDA()
    y_pred = qda.fit(X, y, store_covariances=True).predict(X)
    splot = plot_data(qda, X, y, y_pred, fig_index=2 * i + 2)
    plot_qda_cov(qda, splot)
    pl.axis('tight')
pl.suptitle('LDA vs QDA')
pl.show()

"""
==============================================================
Linear Discriminant Analysis & Quadratic Discriminant Analysis
==============================================================

Plot the confidence ellipsoids of each class and decision boundary
"""

from scipy import linalg
import numpy as np
import pylab as pl
import matplotlib as mpl

from scikits.learn.lda import LDA
from scikits.learn.qda import QDA

################################################################################
# load sample dataset
from scikits.learn.datasets import load_iris

iris = load_iris()
X = iris.data[:,:2] # Take only 2 dimensions
y = iris.target
X = X[y > 0]
y = y[y > 0]
y -= 1
target_names = iris.target_names[1:]

################################################################################
# LDA
lda = LDA()
y_pred = lda.fit(X, y, store_covariance=True).predict(X)

# QDA
qda = QDA()
y_pred = qda.fit(X, y, store_covariances=True).predict(X)

###############################################################################
# Plot results

def plot_ellipse(splot, mean, cov, color):
    v, w = linalg.eigh(cov)
    u = w[0] / linalg.norm(w[0])
    angle = np.arctan(u[1]/u[0])
    angle = 180 * angle / np.pi # convert to degrees
    # filled gaussian at 2 standard deviation
    ell = mpl.patches.Ellipse(mean, 2 * v[0] ** 0.5, 2 * v[1] ** 0.5,
                                            180 + angle, color=color)
    ell.set_clip_box(splot.bbox)
    ell.set_alpha(0.5)
    splot.add_artist(ell)

xx, yy = np.meshgrid(np.linspace(4, 8.5, 200), np.linspace(1.5, 4.5, 200))
X_grid = np.c_[xx.ravel(), yy.ravel()]
zz_lda = lda.predict_proba(X_grid)[:,1].reshape(xx.shape)
zz_qda = qda.predict_proba(X_grid)[:,1].reshape(xx.shape)

pl.figure()
splot = pl.subplot(1, 2, 1)
pl.contourf(xx, yy, zz_lda > 0.5, alpha=0.5)
pl.scatter(X[y==0,0], X[y==0,1], c='b', label=target_names[0])
pl.scatter(X[y==1,0], X[y==1,1], c='r', label=target_names[1])
pl.contour(xx, yy, zz_lda, [0.5], linewidths=2., colors='k')
plot_ellipse(splot, lda.means_[0], lda.covariance_, 'b')
plot_ellipse(splot, lda.means_[1], lda.covariance_, 'r')
pl.legend()
pl.axis('tight')
pl.title('Linear Discriminant Analysis')

splot = pl.subplot(1, 2, 2)
pl.contourf(xx, yy, zz_qda > 0.5, alpha=0.5)
pl.scatter(X[y==0,0], X[y==0,1], c='b', label=target_names[0])
pl.scatter(X[y==1,0], X[y==1,1], c='r', label=target_names[1])
pl.contour(xx, yy, zz_qda, [0.5], linewidths=2., colors='k')
plot_ellipse(splot, qda.means_[0], qda.covariances_[0], 'b')
plot_ellipse(splot, qda.means_[1], qda.covariances_[1], 'r')
pl.legend()
pl.axis('tight')
pl.title('Quadratic Discriminant Analysis')
pl.show()

"""
================
Precision-Recall
================

Example of Precision-Recall metric to evaluate the quality
of the output of a classifier.
"""

import random
import pylab as pl
import numpy as np
from scikits.learn import svm, datasets
from scikits.learn.metrics import precision_recall

# import some data to play with
iris = datasets.load_iris()
X = iris.data
y = iris.target
X, y = X[y!=2], y[y!=2] # Keep also 2 classes (0 and 1)
n_samples, n_features = X.shape
p = range(n_samples) # Shuffle samples
random.seed(0)
random.shuffle(p)
X, y = X[p], y[p]
half = int(n_samples/2)

# Add noisy features
np.random.seed(0)
X = np.c_[X,np.random.randn(n_samples, 200*n_features)]

# Run classifier
classifier = svm.SVC(kernel='linear', probability=True)
probas_ = classifier.fit(X[:half],y[:half]).predict_proba(X[half:])

# Compute Precision-Recall and plot curve
precision, recall, thresholds = precision_recall(y[half:], probas_[:,1])

pl.figure(-1)
pl.clf()
pl.plot(recall, precision, label='Precision-Recall curve')
pl.xlabel('Recall')
pl.ylabel('Precision')
pl.ylim([0.0,1.05])
pl.xlim([0.0,1.0])
pl.title('Precision-Recall example')
pl.legend(loc="lower left")
pl.show()
"""
===============================
Plot classification probability
===============================

Plot the classification probability for different classifiers. We use a 3
class dataset, and we classify it with a Support Vector classifier, as
well as L1 and L2 penalized logistic regression.

The logistic regression is not a multiclass classifier out of the box. As
a result it can identify only the first class.
"""
# Author: Alexandre Gramfort <alexandre.gramfort@inria.fr>
# License: BSD Style.

# $Id$

import pylab as pl
import numpy as np

from scikits.learn.logistic import LogisticRegression
from scikits.learn.svm import SVC
from scikits.learn import datasets

iris = datasets.load_iris()
X = iris.data[:, :2] # we only take the first two features for visualization
y = iris.target

n_features = X.shape[1]

C = 1.0

# Create different classifiers. The logistic regression cannot do
# multiclass out of the box.
classifiers = {
                'L1 logistic': LogisticRegression(C=C, penalty='l1'),
                'L2 logistic': LogisticRegression(C=C, penalty='l2'),
                'Linear SVC': SVC(kernel='linear', C=C, probability=True),
              }

n_classifiers = len(classifiers)

pl.figure(figsize=(3*2, n_classifiers*2))
pl.subplots_adjust(bottom=.2, top=.95)

for index, (name, classifier) in enumerate(classifiers.iteritems()):
    classifier.fit(X, y)

    y_pred = classifier.predict(X)
    classif_rate = np.mean(y_pred.ravel() == y.ravel()) * 100
    print  "classif_rate for %s : %f " % (name, classif_rate)

    # View probabilities=
    xx = np.linspace(3,9,100)
    yy = np.linspace(1,5,100).T
    xx, yy = np.meshgrid(xx, yy)
    Xfull = np.c_[xx.ravel(),yy.ravel()]
    probas = classifier.predict_proba(Xfull)
    n_classes = np.unique(y_pred).size
    for k in range(n_classes):
        pl.subplot(n_classifiers, n_classes, index*n_classes + k + 1)
        pl.title("Class %d" % k)
        if k == 0:
            pl.ylabel(name)
        imshow_handle = pl.imshow(probas[:, k].reshape((100, 100)), 
                                  extent=(3, 9, 1, 5), origin='lower')
        pl.xticks(())
        pl.yticks(())
        idx = (y_pred == k)
        if idx.any(): 
            pl.scatter(X[idx, 0], X[idx, 1], marker='o', c='k')

ax = pl.axes([0.15, 0.04, 0.7, 0.05])
pl.title("Probability")
pl.colorbar(imshow_handle, cax=ax, orientation='horizontal')

pl.show()

"""
===================
Logistic Regression
===================

with l1 and l2 penalty
"""
# Author: Alexandre Gramfort <alexandre.gramfort@inria.fr>
# License: BSD Style.

# $Id$

import numpy as np

from scikits.learn.logistic import LogisticRegression
from scikits.learn import datasets

iris = datasets.load_iris()
X = iris.data
y = iris.target

# Set regularization parameter
C = 0.1

classifier_l1_LR = LogisticRegression(C=C, penalty='l1')
classifier_l2_LR = LogisticRegression(C=C, penalty='l2')
classifier_l1_LR.fit(X, y)
classifier_l2_LR.fit(X, y)

hyperplane_coefficients_l1_LR = classifier_l1_LR.coef_[:]
hyperplane_coefficients_l2_LR = classifier_l2_LR.coef_[:]

# hyperplane_coefficients_l1_LR contains zeros due to the
# L1 sparsity inducing norm

pct_non_zeros_l1_LR = np.mean(hyperplane_coefficients_l1_LR != 0) * 100
pct_non_zeros_l2_LR = np.mean(hyperplane_coefficients_l2_LR != 0) * 100

print "Percentage of non zeros coefficients (L1) : %f" % pct_non_zeros_l1_LR
print "Percentage of non zeros coefficients (L2) : %f" % pct_non_zeros_l2_LR

"""
================================
Recognizing hand-written digits
================================

An example showing how the scikit-learn can be used to recognize images of 
hand-written digits.

"""
# Author: Gael Varoquaux <gael dot varoquaux at normalesup dot org>
# License: Simplified BSD

# Standard scientific Python imports
import pylab as pl

# The digits dataset
from scikits.learn import datasets
digits = datasets.load_digits()

# The data that we are interesting in is made of 8x8 images of digits,
# let's have a look at the first 3 images. We know which digit they
# represent: it is given in the 'target' of the dataset.
for index, (image, label) in enumerate(zip(digits.images, digits.target)[:4]):
    pl.subplot(2, 4, index+1)
    pl.imshow(image, cmap=pl.cm.gray_r)
    pl.title('Training: %i' % label)

# To apply an classifier on this data, we need to flatten the image, to
# turn the data in a (samples, feature) matrix:
n_samples = len(digits.images)
data = digits.images.reshape((n_samples, -1))

# Import a classifier:
from scikits.learn import svm
classifier = svm.SVC()

# We learn the digits on the first half of the digits
classifier.fit(data[:n_samples/2], digits.target[:n_samples/2])

# Now predict the value of the digit on the second half:
predicted = classifier.predict(data[n_samples/2:])

for index, (image, prediction) in enumerate(zip(
                                       digits.images[n_samples/2:], 
                                       predicted
                                    )[:4]):
    pl.subplot(2, 4, index+5)
    pl.imshow(image, cmap=pl.cm.gray_r)
    pl.title('Prediction: %i' % prediction)


pl.show()

"""
=================================
Gaussian Mixture Model Ellipsoids
=================================

Plot the confidence ellipsoids of a mixture of two gaussians.
"""

import numpy as np
from scikits.learn import gmm
import itertools

import pylab as pl
import matplotlib as mpl

n, m = 300, 2

# generate random sample, two components
np.random.seed(0)
C = np.array([[0., -0.7], [3.5, .7]])
X = np.r_[np.dot(np.random.randn(n, 2), C),
          np.random.randn(n, 2) + np.array([3, 3])]

clf = gmm.GMM(n_states=2, n_dim=2, cvtype='full')
clf.fit(X)

splot = pl.subplot(111, aspect='equal')
color_iter = itertools.cycle (['r', 'g', 'b', 'c'])

Y_ = clf.predict(X)

for i, (mean, covar, color) in enumerate(zip(clf.means, clf.covars, color_iter)):
    v, w = np.linalg.eigh(covar)
    u = w[0] / np.linalg.norm(w[0])
    pl.scatter(X[Y_==i, 0], X[Y_==i, 1], .8, color=color)
    angle = np.arctan(u[1]/u[0])
    angle = 180 * angle / np.pi # convert to degrees
    ell = mpl.patches.Ellipse (mean, v[0], v[1], 180 + angle, color=color)
    ell.set_clip_box(splot.bbox)
    ell.set_alpha(0.5)
    splot.add_artist(ell)

pl.show()


"""
=============================================
Density Estimation for a mixture of Gaussians
=============================================

Plot the density estimation of a mixture of two gaussians. Data is
generated from two gaussians with different centers and covariance
matrices.
"""

import itertools
import numpy as np
import pylab as pl
from scikits.learn import gmm

n, m = 300, 2

# generate random sample, two components
np.random.seed(0)
C = np.array([[0., -0.7], [3.5, .7]])
X_train = np.r_[np.dot(np.random.randn(n, 2), C),
          np.random.randn(n, 2) + np.array([20, 20])]

clf = gmm.GMM(n_states=2, n_dim=2, cvtype='full')
clf.fit(X_train)

x = np.linspace(-20.0, 30.0) 
y = np.linspace(-20.0, 40.0) 
X, Y = np.meshgrid(x, y)
XX = np.c_[X.ravel(), Y.ravel()]
Z =  np.log(-clf.eval(XX)[0])
Z = Z.reshape(X.shape)

CS = pl.contour(X, Y, Z)
CB = pl.colorbar(CS, shrink=0.8, extend='both')
pl.scatter(X_train[:, 0], X_train[:, 1], .8)

pl.axis('tight')
pl.show()


"""

Demo of affinity propagation clustering algorithm
====================================================

Reference:
Brendan J. Frey and Delbert Dueck, "Clustering by Passing Messages
Between Data Points", Science Feb. 2007

"""

import numpy as np
from scikits.learn.cluster import AffinityPropagation

################################################################################
# Generate sample data
################################################################################
np.random.seed(0)

n_points_per_cluster = 100
n_clusters = 3
n_points = n_points_per_cluster*n_clusters
means = np.array([[1,1],[-1,-1],[1,-1]])
std = .5

X = np.empty((0, 2))
for i in range(n_clusters):
    X = np.r_[X, means[i] + std * np.random.randn(n_points_per_cluster, 2)]

################################################################################
# Compute similarities
################################################################################
X_norms = np.sum(X*X, axis=1)
S = - X_norms[:,np.newaxis] - X_norms[np.newaxis,:] + 2 * np.dot(X, X.T)
p = 10*np.median(S)

################################################################################
# Compute Affinity Propagation
################################################################################

af = AffinityPropagation()
af.fit(S, p)
cluster_centers_indices = af.cluster_centers_indices_
labels = af.labels_

n_clusters_ = len(cluster_centers_indices)

print 'Estimated number of clusters: %d' % n_clusters_

################################################################################
# Plot result
################################################################################

import pylab as pl
from itertools import cycle

pl.close('all')
pl.figure(1)
pl.clf()

colors = cycle('bgrcmykbgrcmykbgrcmykbgrcmyk')
for k, col in zip(range(n_clusters_), colors):
    class_members = labels == k
    cluster_center = X[cluster_centers_indices[k]]
    pl.plot(X[class_members,0], X[class_members,1], col+'.')
    pl.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col,
                                    markeredgecolor='k', markersize=14)
    for x in X[class_members]:
        pl.plot([cluster_center[0], x[0]], [cluster_center[1], x[1]], col)

pl.title('Estimated number of clusters: %d' % n_clusters_)
pl.show()


"""
===========================================
Segmenting the picture of Lena in regions
===========================================

This example uses spectral clustering on a graph created from
voxel-to-voxel difference on an image to break this image into multiple
partly-homogenous regions.

This procedure (spectral clustering on an image) is an efficient
approximate solution for finding normalized graph cuts.
"""

# Author: Gael Varoquaux <gael.varoquaux@normalesup.org>
# License: BSD

import numpy as np
import scipy as sp
import pylab as pl

from scikits.learn.features import image
from scikits.learn.cluster import spectral_clustering

lena = sp.lena()
# Downsample the image by a factor of 4
lena = lena[::2, ::2] + lena[1::2, ::2] + lena[::2, 1::2] + lena[1::2, 1::2]
lena = lena[::2, ::2] + lena[1::2, ::2] + lena[::2, 1::2] + lena[1::2, 1::2]

# Convert the image into a graph with the value of the gradient on the
# edges.
graph = image.img_to_graph(lena)

# Take a decreasing function of the gradient: an exponential
# The smaller beta is, the more independant the segmentation is of the
# actual image. For beta=1, the segmentation is close to a voronoi
beta = 5
eps  = 1e-6
graph.data = np.exp(-beta*graph.data/lena.std()) + eps

# Apply spectral clustering (this step goes much faster if you have pyamg
# installed)
N_REGIONS = 11
labels = spectral_clustering(graph, k=N_REGIONS)
labels = labels.reshape(lena.shape)

################################################################################
# Visualize the resulting regions
pl.figure(figsize=(5, 5))
pl.imshow(lena,   cmap=pl.cm.gray)
for l in range(N_REGIONS):
    pl.contour(labels == l, contours=1,
            colors=[pl.cm.spectral(l/float(N_REGIONS)), ])
pl.xticks(())
pl.yticks(())
pl.show()

"""

===========================================
Spectral clustering for image segmentation
===========================================

In this example, an image with connected circles is generated and
spectral clustering is used to separate the circles. 

In these settings, the spectral clustering approach solves the problem
know as 'normalized graph cuts': the image is seen as a graph of
connected voxels, and the spectral clustering algorithm amounts to
choosing graph cuts defining regions while minimizing the ratio of the 
gradient along the cut, and the volume of the region.

As the algorithm tries to balance the volume (ie balance the region
sizes), if we take circles with different sizes, the segmentation fails.

In addition, as there is no useful information in the intensity of the image,
or its gradient, we choose to perform the spectral clustering on a graph
that is only weakly informed by the gradient. This is close to performing
a Voronoi partition of the graph.

In addition, we use the mask of the objects to restrict the graph to the
outline of the objects. In this example, we are interested in
separating the objects one from the other, and not from the background.
"""
# Authors:  Emmanuelle Gouillart <emmanuelle.gouillart@normalesup.org>
#           Gael Varoquaux <gael.varoquaux@normalesup.org>
# License: BSD

import numpy as np
import pylab as pl

from scikits.learn.features import image
from scikits.learn.cluster import spectral_clustering

################################################################################
l = 100
x, y = np.indices((l, l))

center1 = (28, 24)
center2 = (40, 50)
center3 = (67, 58)
center4 = (24, 70)

radius1, radius2, radius3, radius4 = 16, 14, 15, 14

circle1 = (x - center1[0])**2 + (y - center1[1])**2 < radius1**2
circle2 = (x - center2[0])**2 + (y - center2[1])**2 < radius2**2
circle3 = (x - center3[0])**2 + (y - center3[1])**2 < radius3**2
circle4 = (x - center4[0])**2 + (y - center4[1])**2 < radius4**2

################################################################################
# 4 circles
img = circle1 + circle2 + circle3 + circle4
mask = img.astype(bool)
img = img.astype(float)

img += 1 + 0.2*np.random.randn(*img.shape)

# Convert the image into a graph with the value of the gradient on the
# edges.
graph = image.img_to_graph(img, mask=mask)

# Take a decreasing function of the gradient: we take it weakly
# dependant from the gradient the segmentation is close to a voronoi
graph.data = np.exp(-graph.data/graph.data.std())

labels = spectral_clustering(graph, k=4)
label_im = -np.ones(mask.shape)
label_im[mask] = labels

pl.figure(1, figsize=(8, 8))
pl.clf()
pl.subplot(2, 2, 1)
pl.imshow(img)
pl.subplot(2, 2, 3)
pl.imshow(label_im)

################################################################################
# 2 circles
img = circle1 + circle2
mask = img.astype(bool)
img = img.astype(float)

img += 1 + 0.2*np.random.randn(*img.shape)

graph = image.img_to_graph(img, mask=mask)
graph.data = np.exp(-graph.data/graph.data.std())

labels = spectral_clustering(graph, k=2)
label_im = -np.ones(mask.shape)
label_im[mask] = labels

pl.subplot(2, 2, 2)
pl.imshow(img)
pl.subplot(2, 2, 4)
pl.imshow(label_im)

pl.show()

"""

A demo of the mean-shift clustering algorithm
===============================================

Reference:
K. Funkunaga and L.D. Hosteler, "The Estimation of the Gradient of a
Density Function, with Applications in Pattern Recognition"

"""

import numpy as np
from scikits.learn.cluster import MeanShift, estimate_bandwidth

################################################################################
# Generate sample data
np.random.seed(0)

n_points_per_cluster = 250
n_clusters = 3
n_points = n_points_per_cluster*n_clusters
means = np.array([[1,1],[-1,-1],[1,-1]])
std = .6
clustMed = []

X = np.empty((0, 2))
for i in range(n_clusters):
    X = np.r_[X, means[i] + std * np.random.randn(n_points_per_cluster, 2)]

################################################################################
# Compute clustering with MeanShift
bandwidth = estimate_bandwidth(X, quantile=0.3)
ms = MeanShift(bandwidth=bandwidth)
ms.fit(X)
labels = ms.labels_
cluster_centers = ms.cluster_centers_

labels_unique = np.unique(labels)
n_clusters_ = len(labels_unique)

print "number of estimated clusters : %d" % n_clusters_

################################################################################
# Plot result
import pylab as pl
from itertools import cycle

pl.figure(1)
pl.clf()

colors = cycle('bgrcmykbgrcmykbgrcmykbgrcmyk')
for k, col in zip(range(n_clusters_), colors):
    my_members = labels == k
    cluster_center = cluster_centers[k]
    pl.plot(X[my_members,0], X[my_members,1], col+'.')
    pl.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col,
                                    markeredgecolor='k', markersize=14)
pl.title('Estimated number of clusters: %d' % n_clusters_)
pl.show()

"""
==================================================
Plot different SVM classifiers in the iris dataset
==================================================

Comparison of different linear SVM classifiers on the iris dataset. It
will plot the decision surface and the support vectors.

"""

import numpy as np
import pylab as pl
from scikits.learn import svm, datasets

# import some data to play with
iris = datasets.load_iris()
X = iris.data[:, :2] # we only take the first two features. We could
                     # avoid this ugly slicing by using a two-dim dataset
Y = iris.target

h=.02 # step size in the mesh

# we create an instance of SVM and fit out data. We do not scale our
# data since we want to plot the support vectors
svc     = svm.SVC(kernel='linear').fit(X, Y)
rbf_svc = svm.SVC(kernel='poly').fit(X, Y)
nu_svc  = svm.NuSVC(kernel='linear').fit(X,Y)
lin_svc = svm.LinearSVC().fit(X, Y)

# create a mesh to plot in
x_min, x_max = X[:,0].min()-1, X[:,0].max()+1
y_min, y_max = X[:,1].min()-1, X[:,1].max()+1
xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                     np.arange(y_min, y_max, h))

# title for the plots
titles = ['SVC with linear kernel',
          'SVC with polynomial (degree 3) kernel',
          'NuSVC with linear kernel',
          'LinearSVC (linear kernel)']


pl.set_cmap(pl.cm.Paired)

for i, clf in enumerate((svc, rbf_svc, nu_svc, lin_svc)):
    # Plot the decision boundary. For that, we will asign a color to each
    # point in the mesh [x_min, m_max]x[y_min, y_max].
    pl.subplot(2, 2, i+1)
    Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])

    # Put the result into a color plot
    Z = Z.reshape(xx.shape)
    pl.set_cmap(pl.cm.Paired)
    pl.contourf(xx, yy, Z)
    pl.axis('tight')

    # Plot also the training points
    pl.scatter(X[:,0], X[:,1], c=Y)

    pl.title(titles[i])
    
pl.axis('tight')
pl.show()

"""
=================
Non-linear SVM
=================


"""

import numpy as np
import pylab as pl
from scikits.learn import svm

xx, yy = np.meshgrid(np.linspace(-5, 5, 500), np.linspace(-5, 5, 500))
np.random.seed(0)
X = np.random.randn(300, 2)
Y = np.logical_xor(X[:,0]>0, X[:,1]>0)

# fit the model
clf = svm.NuSVC()
clf.fit(X, Y)

# plot the line, the points, and the nearest vectors to the plane
Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)

pl.set_cmap(pl.cm.Paired)
pl.pcolormesh(xx, yy, Z)
pl.scatter(X[:,0], X[:,1], c=Y)

pl.axis('tight')
pl.show()


"""
===========================================
SVM: Maximum separating margin hyperplane
===========================================

"""

import numpy as np
import pylab as pl
from scikits.learn import svm

# we create 40 separable points
np.random.seed(0)
X = np.r_[np.random.randn(20, 2) - [2,2], np.random.randn(20, 2) + [2, 2]]
Y = [0]*20 + [1]*20

# fit the model
clf = svm.SVC(kernel='linear')
clf.fit(X, Y)

# get the separating hyperplane
w =  clf.coef_[0]
a = -w[0]/w[1]
xx = np.linspace(-5, 5)
yy = a*xx - (clf.intercept_[0])/w[1]

# plot the parallels to the separating hyperplane that pass through the
# support vectors
b = clf.support_[0]
yy_down = a*xx + (b[1] - a*b[0])
b = clf.support_[-1]
yy_up = a*xx + (b[1] - a*b[0])

# plot the line, the points, and the nearest vectors to the plane
pl.set_cmap(pl.cm.Paired)
pl.plot(xx, yy, 'k-')
pl.plot(xx, yy_down, 'k--')
pl.plot(xx, yy_up, 'k--')
pl.scatter(X[:,0], X[:,1], c=Y)
pl.scatter(clf.support_[:,0], clf.support_[:,1], marker='+')

pl.axis('tight')
pl.show()


"""
======================
SVM with custom kernel
======================

Simple usage of Support Vector Machines to classify a sample. It will
plot the decision surface and the support vectors.

"""
import numpy as np
import pylab as pl
from scikits.learn import svm, datasets

# import some data to play with
iris = datasets.load_iris()
X = iris.data[:, :2] # we only take the first two features. We could
                     # avoid this ugly slicing by using a two-dim dataset
Y = iris.target


def my_kernel(x, y):
    """
    We create a custom kernel:

                 (2  0)
    k(x, y) = x  (    ) y.T
                 (0  1)
    """
    M = np.array([[2, 0], [0, 1.0]])
    return np.dot(np.dot(x, M), y.T)
    

h=.02 # step size in the mesh

# we create an instance of SVM and fit out data. 
clf = svm.SVC(kernel=my_kernel)
clf.fit(X, Y)

# Plot the decision boundary. For that, we will asign a color to each
# point in the mesh [x_min, m_max]x[y_min, y_max].
x_min, x_max = X[:,0].min()-1, X[:,0].max()+1
y_min, y_max = X[:,1].min()-1, X[:,1].max()+1
xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])

# Put the result into a color plot
Z = Z.reshape(xx.shape)
pl.set_cmap(pl.cm.Paired)
pl.pcolormesh(xx, yy, Z)

# Plot also the training points
pl.scatter(X[:,0], X[:,1], c=Y)
pl.title('3-Class classification using Support Vector Machine with custom kernel')
pl.axis('tight')
pl.show()

"""
=================================================
SVM-Anova: SVM with univariate feature selection
=================================================

This example shows how to perform univariate feature before running a SVC
(support vector classifier) to improve the classification scores.
"""
import numpy as np
import pylab as pl
from scikits.learn import svm, datasets, feature_selection, cross_val
from scikits.learn.pipeline import Pipeline

################################################################################
# Import some data to play with
digits = datasets.load_digits()
y = digits.target
n_samples = len(y)
X = digits.data.reshape((n_samples, -1))

################################################################################
# Create a feature-selection transform and an instance of SVM that we
# combine together to have an full-blown estimator

transform = feature_selection.SelectPercentile(feature_selection.f_classif)

clf = Pipeline([transform], svm.SVC())

################################################################################
# Plot the cross-validation score as a function of percentile of features
score_means = list()
score_stds  = list()
percentiles = (10, 20, 30, 40, 50, 60, 70, 80, 90, 100)

for percentile in percentiles:
    transform._set_params(percentile=percentile)
    # Compute cross-validation score using all CPUs
    this_scores = cross_val.cross_val_score(clf, X, y, n_jobs=1)
    score_means.append(this_scores.mean())
    score_stds.append(this_scores.std())

pl.errorbar(percentiles, score_means, np.array(score_stds))

pl.title(
    'Performance of the SVM-Anova varying the percentile of features selected')
pl.xlabel('Percentile')
pl.ylabel('Cross-validation errors rate')

pl.axis('tight')
pl.show()

"""
==========================================
One-class SVM with non-linear kernel (RBF)
==========================================
"""

import numpy as np
import pylab as pl
from scikits.learn import svm

xx, yy = np.meshgrid(np.linspace(-7, 7, 500), np.linspace(-7, 7, 500))
X = 0.3 * np.random.randn(100, 2)
X = np.r_[X + 2, X - 2]

# Add 10 % of outliers (leads to nu=0.1)
X = np.r_[X, np.random.uniform(low=-6, high=6, size=(20, 2))]

# fit the model
clf = svm.OneClassSVM(nu=0.1, kernel="rbf", gamma=0.1)
clf.fit(X)

# plot the line, the points, and the nearest vectors to the plane
Z = clf.predict_margin(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)
y_pred = clf.predict(X)

pl.set_cmap(pl.cm.Paired)
pl.contourf(xx, yy, Z)
pl.scatter(X[y_pred>0,0], X[y_pred>0,1], c='white', label='inliers')
pl.scatter(X[y_pred<=0,0], X[y_pred<=0,1], c='black', label='outliers')
pl.axis('tight')
pl.legend()
pl.show()

"""
================================================
SVM: Separating hyperplane with weighted classes
================================================

"""

import numpy as np
import pylab as pl
from scikits.learn import svm

# we create 40 separable points
np.random.seed(0)
n_samples_1 = 1000
n_samples_2 = 100
X = np.r_[1.5*np.random.randn(n_samples_1, 2), 0.5*np.random.randn(n_samples_2, 2) + [2, 2]]
Y = [0]*(n_samples_1) + [1]*(n_samples_2)

# fit the model and get the separating hyperplane
clf = svm.SVC(kernel='linear')
clf.fit(X, Y)

w = clf.coef_[0]
a = -w[0]/w[1]
xx = np.linspace(-5, 5)
yy = a*xx - (clf.intercept_[0])/w[1]


# get the separating hyperplane using weighted classes
wclf = svm.SVC(kernel='linear')
wclf.fit(X, Y, {1: 10})

ww = wclf.coef_[0]
wa = -ww[0]/ww[1]
wyy = wa*xx - (wclf.intercept_[0])/ww[1]

# plot separating hyperplanes and samples
pl.set_cmap(pl.cm.Paired)
pl.plot(xx, yy, 'k-')
pl.plot(xx, wyy, 'k--')
pl.scatter(X[:,0], X[:,1], c=Y)

pl.axis('tight')
pl.show()


"""
================================================
Support Vector Regression (SVR) using RBF kernel
================================================
"""
###############################################################################
# Generate sample data
import numpy as np

X = np.sort(5*np.random.rand(40, 1), axis=0)
y = np.sin(X).ravel()

###############################################################################
# Add noise to targets
y[::5] += 3*(0.5 - np.random.rand(8))

###############################################################################
# Fit regression model
from scikits.learn.svm import SVR

svr_rbf = SVR(kernel='rbf', C=1e4, gamma=0.1)
svr_lin = SVR(kernel='linear', C=1e4)
svr_poly = SVR(kernel='poly', C=1e4, degree=2)
y_rbf = svr_rbf.fit(X, y).predict(X)
y_lin = svr_lin.fit(X, y).predict(X)
y_poly = svr_poly.fit(X, y).predict(X)

###############################################################################
# look at the results
import pylab as pl
pl.scatter(X, y, c='k', label='data')
pl.hold('on')
pl.plot(X, y_rbf, c='g', label='RBF model')
pl.plot(X, y_lin, c='r', label='Linear model')
pl.plot(X, y_poly, c='b', label='Polynomial model')
pl.xlabel('data')
pl.ylabel('target')
pl.title('Support Vector Regression')
pl.legend()
pl.show()

"""
Ordinary Least Squares
======================

Simple Ordinary Least Squares example, we draw the linear least
squares solution for a random set of points in the plane.
"""
import numpy as np
import pylab as pl

from scikits.learn import glm

# this is our test set, it's just a straight line with some
# gaussian noise
xmin, xmax = -5, 5
n_samples = 100
X = [[i] for i in np.linspace(xmin, xmax, n_samples)]
Y = 2 + 0.5 * np.linspace(xmin, xmax, n_samples) \
      + np.random.randn(n_samples, 1).ravel()

# run the classifier
clf = glm.LinearRegression()
clf.fit(X, Y)

# and plot the result
pl.scatter(X, Y, color='black')
pl.plot(X, clf.predict(X), color='blue', linewidth=3)
pl.show()


#!/usr/bin/env python
"""
======================
Least Angle Regression
======================

"""

# Author: Fabian Pedregosa <fabian.pedregosa@inria.fr>
#         Alexandre Gramfort <alexandre.gramfort@inria.fr>
# License: BSD Style.

from datetime import datetime
import itertools
import numpy as np
import pylab as pl

from scikits.learn import glm
from scikits.learn import datasets

diabetes = datasets.load_diabetes()
X = diabetes.data
y = diabetes.target


################################################################################
# Demo path functions
################################################################################

print "Computing regularization path using the LARS ..."
start = datetime.now()
# should not use a fit predict to get the path
clf = glm.LeastAngleRegression().fit(X, y, normalize=True)
print "This took ", datetime.now() - start

alphas = -np.log10(clf.alphas_)

# # Display results
color_iter = itertools.cycle(['r', 'g', 'b', 'c'])

for coef_, color in zip(clf.coef_path_, color_iter):
    pl.plot(alphas, coef_.T, color)

ymin, ymax = pl.ylim()
pl.vlines(alphas, ymin, ymax, linestyle='dashed')
pl.xlabel('-Log(lambda)') # XXX : wrong label
pl.ylabel('Coefficients')
pl.title('Least Angle Regression (LAR) Path')
pl.axis('tight')
pl.show()


"""
========================
Lasso regression example
========================

"""

import numpy as np

################################################################################
# generate some sparse data to play with

n_samples, n_features = 50, 200
X = np.random.randn(n_samples, n_features)
coef = 3*np.random.randn(n_features)
coef[10:] = 0 # sparsify coef
y = np.dot(X, coef)

# add noise
y += 0.01*np.random.normal((n_samples,))

# Split data in train set and test set
n_samples = X.shape[0]
X_train, y_train = X[:n_samples/2], y[:n_samples/2]
X_test, y_test = X[n_samples/2:], y[n_samples/2:]

################################################################################
# Lasso
from scikits.learn.glm import Lasso

alpha = 0.1
lasso = Lasso(alpha=alpha)

y_pred_lasso = lasso.fit(X_train, y_train).predict(X_test)
print lasso
print "r^2 on test data : %f" % (1 - np.linalg.norm(y_test - y_pred_lasso)**2
                                      / np.linalg.norm(y_test)**2)

################################################################################
# ElasticNet
from scikits.learn.glm import ElasticNet

enet = ElasticNet(alpha=alpha, rho=0.7)

y_pred_enet = enet.fit(X_train, y_train).predict(X_test)
print enet
print "r^2 on test data : %f" % (1 - np.linalg.norm(y_test - y_pred_enet)**2
                                      / np.linalg.norm(y_test)**2)


"""
=====================
Lasso and Elastic Net
=====================

Lasso and elastic net (L1 and L2 penalisation) implemented using a
coordinate descent.
"""

# Author: Alexandre Gramfort <alexandre.gramfort@inria.fr>
# License: BSD Style.

from itertools import cycle
import numpy as np
import pylab as pl

from scikits.learn.glm import lasso_path, enet_path

n_samples, n_features = 100, 10
np.random.seed(0)
y = np.random.randn(n_samples)
X = np.random.randn(n_samples, n_features)

################################################################################
# Fit models
################################################################################

################################################################################
# Demo path functions
################################################################################

eps = 1e-2 # the smaller it is the longer is the path

print "Computing regularization path using the lasso..."
models = lasso_path(X, y, eps=eps)
alphas_lasso = np.array([model.alpha for model in models])
coefs_lasso = np.array([model.coef_ for model in models])

print "Computing regularization path using the elastic net..."
models = enet_path(X, y, eps=eps, rho=0.6)
alphas_enet = np.array([model.alpha for model in models])
coefs_enet = np.array([model.coef_ for model in models])

# Display results
color_iter = cycle(['b', 'g', 'r', 'c', 'm', 'y', 'k'])
for color, coef_lasso, coef_enet in zip(color_iter,
                            coefs_lasso.T, coefs_enet.T):
    pl.plot(-np.log10(alphas_lasso), coef_lasso, color)
    pl.plot(-np.log10(alphas_enet), coef_enet, color + 'x')

pl.xlabel('-Log(lambda)')
pl.ylabel('weights')
pl.title('Lasso and Elastic-Net Paths')
pl.legend(['Lasso','Elastic-Net'])
pl.axis('tight')
pl.show()


#!/usr/bin/env python
"""
=================================
Lasso with Least Angle Regression
=================================

"""

# Author: Fabian Pedregosa <fabian.pedregosa@inria.fr>
#         Alexandre Gramfort <alexandre.gramfort@inria.fr>
# License: BSD Style.

from datetime import datetime
import itertools
import numpy as np
import pylab as pl

from scikits.learn import glm
from scikits.learn import datasets

diabetes = datasets.load_diabetes()
X = diabetes.data
y = diabetes.target
# someting's wrong with our dataset
X[:, 6] = -X[:, 6]

################################################################################
# Demo path functions
################################################################################


print "Computing regularization path using the LARS ..."
start = datetime.now()
alphas, active, path = glm.lars_path(X, y, method='lasso', max_iter=12)
print "This took ", datetime.now() - start

alphas = np.sum(np.abs(path.T), axis=1)
alphas /= alphas[-1]

# # Display results
color_iter = itertools.cycle(['r', 'g', 'b', 'c'])

for coef_, color in zip(path, color_iter):
    pl.plot(alphas, coef_.T, color)

ymin, ymax = pl.ylim()
pl.vlines(alphas, ymin, ymax, linestyle='dashed')
pl.xlabel('-Log(lambda)') # XXX : wrong label
pl.ylabel('Coefficients')
pl.title('LASSO Path')
pl.axis('tight')
pl.show()


"""
=========================================================
Lasso parameter estimation with path and cross-validation
=========================================================

"""

import numpy as np

################################################################################
# generate some sparse data to play with

n_samples, n_features = 60, 100

np.random.seed(1)
X = np.random.randn(n_samples, n_features)
coef = 3*np.random.randn(n_features)
coef[10:] = 0 # sparsify coef
y = np.dot(X, coef)

# add noise
y += 0.01 * np.random.normal((n_samples,))

# Split data in train set and test set
X_train, y_train = X[:n_samples/2], y[:n_samples/2]
X_test, y_test = X[n_samples/2:], y[n_samples/2:]


################################################################################
# Lasso with path and cross-validation using LassoCV path
from scikits.learn.glm import LassoCV
from scikits.learn.cross_val import KFold

cv = KFold(n_samples/2, 5)
lasso_cv = LassoCV()

# fit_params = {'maxit':100}

y_ = lasso_cv.fit(X_train, y_train, cv=cv, maxit=100).predict(X_test)

print "Optimal regularization parameter  = %s" % lasso_cv.alpha

# Compute explained variance on test data
print "r^2 on test data : %f" % (1 - np.linalg.norm(y_test - y_)**2
                                      / np.linalg.norm(y_test)**2)


# -*- coding: utf-8 -*-
#
# scikit-learn documentation build configuration file, created by
# sphinx-quickstart on Fri Jan  8 09:13:42 2010.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys, os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('sphinxext'))

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.autosummary', 'numpydoc', 'sphinx.ext.pngmath',
              'gen_rst']

autosummary_generate=True
autodoc_default_flags=['inherited-members']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'scikits.learn'
copyright = u'2010, scikits.learn developers'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '0.5'
# The full version, including alpha/beta/rc tags.
release = '0.5-git'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
#unused_docs = []

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ['_build']

# The reST default role (used for this markup: `text`) to use for all documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
html_theme = 'default'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#html_theme_options = {}

# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_use_modindex = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = 'scikit-learndoc'


# -- Options for LaTeX output --------------------------------------------------

# The paper size ('letter' or 'a4').
#latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
#latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'scikits.learn.tex', u'scikits.learn documentation',
   u'scikits.learn developers', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# Additional stuff for the LaTeX preamble.
latex_preamble = """
\usepackage{amsmath}\usepackage{amsfonts}
"""

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_use_modindex = True


"""
Example generation for the scikit learn

Generate the rst files for the examples by iterating over the python
example files.

Files that generate images should start with 'plot'

"""
import os
import shutil
import traceback

fileList = []

import matplotlib
matplotlib.use('Agg')

import token, tokenize      

rst_template = """

.. _example_%(short_fname)s:

%(docstring)s

**Source code:** :download:`%(fname)s <%(fname)s>`

.. literalinclude:: %(fname)s
    :lines: %(end_row)s-
    """

plot_rst_template = """

.. _example_%(short_fname)s:

%(docstring)s

.. image:: images/%(image_name)s
    :align: center

**Source code:** :download:`%(fname)s <%(fname)s>`

.. literalinclude:: %(fname)s
    :lines: %(end_row)s-
    """


def extract_docstring(filename):
    """ Extract a module-level docstring, if any
    """
    lines = file(filename).readlines()
    start_row = 0
    if lines[0].startswith('#!'):
        lines.pop(0)
        start_row = 1

    docstring = ''
    first_par = ''
    tokens = tokenize.generate_tokens(lines.__iter__().next)
    for tok_type, tok_content, _, (erow, _), _ in tokens:
        tok_type = token.tok_name[tok_type]    
        if tok_type in ('NEWLINE', 'COMMENT', 'NL', 'INDENT', 'DEDENT'):
            continue
        elif tok_type == 'STRING':
            docstring = eval(tok_content)
            # If the docstring is formatted with several paragraphs, extract
            # the first one:
            paragraphs = '\n'.join(line.rstrip() 
                                for line in docstring.split('\n')).split('\n\n')
            if len(paragraphs) > 0:
                first_par = paragraphs[0]
        break
    return docstring, first_par, erow+1+start_row


def generate_example_rst(app):
    """ Generate the list of examples, as well as the contents of
        examples.
    """ 
    root_dir = os.path.join(app.builder.srcdir, 'auto_examples')
    example_dir = os.path.abspath(app.builder.srcdir +  '/../' + 'examples')
    if not os.path.exists(example_dir):
        os.makedirs(example_dir)
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)

    # we create an index.rst with all examples
    fhindex = file(os.path.join(root_dir, 'index.rst'), 'w')
    fhindex.write("""\
.. _examples-index:

Examples
==========

    :Release: |version|
    :Date: |today|

""")
    # Here we don't use an os.walk, but we recurse only twice: flat is
    # better than nested.
    generate_dir_rst('.', fhindex, example_dir, root_dir)
    for dir in sorted(os.listdir(example_dir)):
        if dir == '.svn':
            continue
        if os.path.isdir(os.path.join(example_dir, dir)):
            generate_dir_rst(dir, fhindex, example_dir, root_dir)
    fhindex.flush()


def generate_dir_rst(dir, fhindex, example_dir, root_dir):
    """ Generate the rst file for an example directory.
    """
    target_dir = os.path.join(root_dir, dir)
    src_dir = os.path.join(example_dir, dir)
    if not os.path.exists(os.path.join(src_dir, 'README.txt')):
        raise IOError('Example directory %s does not have a README.txt file' 
                        % src_dir)
    fhindex.write("""

%s

.. toctree::

""" % file(os.path.join(src_dir, 'README.txt')).read())
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    for fname in sorted(os.listdir(src_dir)):
        if fname.endswith('py'): 
            generate_file_rst(fname, target_dir, src_dir)
            fhindex.write('    %s\n' % (os.path.join(dir, fname[:-3])))


def generate_file_rst(fname, target_dir, src_dir):
    """ Generate the rst file for a given example.
    """
    image_name = fname[:-2] + 'png'
    global rst_template, plot_rst_template
    this_template = rst_template
    last_dir = os.path.split(src_dir)[-1]
    # to avoid leading . in file names
    if last_dir == '.': last_dir = ''
    else: last_dir += '_'
    short_fname =  last_dir + fname
    src_file = os.path.join(src_dir, fname)
    example_file = os.path.join(target_dir, fname)
    shutil.copyfile(src_file, example_file)
    if fname.startswith('plot'):
        # generate the plot as png image if file name
        # starts with plot and if it is more recent than an
        # existing image.
        if not os.path.exists(
                            os.path.join(target_dir, 'images')):
            os.makedirs(os.path.join(target_dir, 'images'))
        image_file = os.path.join(target_dir, 'images', image_name)
        if (not os.path.exists(image_file) or
                os.stat(image_file).st_mtime <= 
                    os.stat(src_file).st_mtime):
            print 'plotting %s' % fname
            import matplotlib.pyplot as plt
            plt.close('all')
            try:
                execfile(example_file, {'pl' : plt})
                plt.savefig(image_file)
            except:
                print 80*'_'
                print '%s is not compiling:' % fname
                traceback.print_exc()
                print 80*'_'
        this_template = plot_rst_template

    docstring, short_desc, end_row = extract_docstring(example_file)

    f = open(os.path.join(target_dir, fname[:-2] + 'rst'),'w')
    f.write( this_template % locals())
    f.flush()


def setup(app):
    app.connect('builder-inited', generate_example_rst)


import re, inspect, textwrap, pydoc
import sphinx
from docscrape import NumpyDocString, FunctionDoc, ClassDoc

class SphinxDocString(NumpyDocString):
    def __init__(self, docstring, config={}):
        self.use_plots = config.get('use_plots', False)
        NumpyDocString.__init__(self, docstring, config=config)

    # string conversion routines
    def _str_header(self, name, symbol='`'):
        return ['.. rubric:: ' + name, '']

    def _str_field_list(self, name):
        return [':' + name + ':']

    def _str_indent(self, doc, indent=4):
        out = []
        for line in doc:
            out += [' '*indent + line]
        return out

    def _str_signature(self):
        return ['']
        if self['Signature']:
            return ['``%s``' % self['Signature']] + ['']
        else:
            return ['']

    def _str_summary(self):
        return self['Summary'] + ['']

    def _str_extended_summary(self):
        return self['Extended Summary'] + ['']

    def _str_param_list(self, name):
        out = []
        if self[name]:
            out += self._str_field_list(name)
            out += ['']
            for param,param_type,desc in self[name]:
                out += self._str_indent(['**%s** : %s' % (param.strip(),
                                                          param_type)])
                out += ['']
                out += self._str_indent(desc,8)
                out += ['']
        return out

    @property
    def _obj(self):
        if hasattr(self, '_cls'):
            return self._cls
        elif hasattr(self, '_f'):
            return self._f
        return None

    def _str_member_list(self, name):
        """
        Generate a member listing, autosummary:: table where possible,
        and a table where not.

        """
        out = []
        if self[name]:
            out += ['.. rubric:: %s' % name, '']
            prefix = getattr(self, '_name', '')

            if prefix:
                prefix = '~%s.' % prefix

            autosum = []
            others = []
            for param, param_type, desc in self[name]:
                param = param.strip()
                if not self._obj or hasattr(self._obj, param):
                    autosum += ["   %s%s" % (prefix, param)]
                else:
                    others.append((param, param_type, desc))

            if autosum:
                out += ['.. autosummary::', '   :toctree:', '']
                out += autosum

            if others:
                maxlen_0 = max([len(x[0]) for x in others])
                maxlen_1 = max([len(x[1]) for x in others])
                hdr = "="*maxlen_0 + "  " + "="*maxlen_1 + "  " + "="*10
                fmt = '%%%ds  %%%ds  ' % (maxlen_0, maxlen_1)
                n_indent = maxlen_0 + maxlen_1 + 4
                out += [hdr]
                for param, param_type, desc in others:
                    out += [fmt % (param.strip(), param_type)]
                    out += self._str_indent(desc, n_indent)
                out += [hdr]
            out += ['']
        return out

    def _str_section(self, name):
        out = []
        if self[name]:
            out += self._str_header(name)
            out += ['']
            content = textwrap.dedent("\n".join(self[name])).split("\n")
            out += content
            out += ['']
        return out

    def _str_see_also(self, func_role):
        out = []
        if self['See Also']:
            see_also = super(SphinxDocString, self)._str_see_also(func_role)
            out = ['.. seealso::', '']
            out += self._str_indent(see_also[2:])
        return out

    def _str_warnings(self):
        out = []
        if self['Warnings']:
            out = ['.. warning::', '']
            out += self._str_indent(self['Warnings'])
        return out

    def _str_index(self):
        idx = self['index']
        out = []
        if len(idx) == 0:
            return out

        out += ['.. index:: %s' % idx.get('default','')]
        for section, references in idx.iteritems():
            if section == 'default':
                continue
            elif section == 'refguide':
                out += ['   single: %s' % (', '.join(references))]
            else:
                out += ['   %s: %s' % (section, ','.join(references))]
        return out

    def _str_references(self):
        out = []
        if self['References']:
            out += self._str_header('References')
            if isinstance(self['References'], str):
                self['References'] = [self['References']]
            out.extend(self['References'])
            out += ['']
            # Latex collects all references to a separate bibliography,
            # so we need to insert links to it
            if sphinx.__version__ >= "0.6":
                out += ['.. only:: latex','']
            else:
                out += ['.. latexonly::','']
            items = []
            for line in self['References']:
                m = re.match(r'.. \[([a-z0-9._-]+)\]', line, re.I)
                if m:
                    items.append(m.group(1))
            out += ['   ' + ", ".join(["[%s]_" % item for item in items]), '']
        return out

    def _str_examples(self):
        examples_str = "\n".join(self['Examples'])

        if (self.use_plots and 'import matplotlib' in examples_str
                and 'plot::' not in examples_str):
            out = []
            out += self._str_header('Examples')
            out += ['.. plot::', '']
            out += self._str_indent(self['Examples'])
            out += ['']
            return out
        else:
            return self._str_section('Examples')

    def __str__(self, indent=0, func_role="obj"):
        out = []
        out += self._str_signature()
        out += self._str_index() + ['']
        out += self._str_summary()
        out += self._str_extended_summary()
        for param_list in ('Parameters', 'Returns', 'Raises'):
            out += self._str_param_list(param_list)
        out += self._str_warnings()
        out += self._str_see_also(func_role)
        out += self._str_section('Notes')
        out += self._str_references()
        out += self._str_examples()
        for param_list in ('Attributes', 'Methods'):
            out += self._str_member_list(param_list)
        out = self._str_indent(out,indent)
        return '\n'.join(out)

class SphinxFunctionDoc(SphinxDocString, FunctionDoc):
    def __init__(self, obj, doc=None, config={}):
        self.use_plots = config.get('use_plots', False)
        FunctionDoc.__init__(self, obj, doc=doc, config=config)

class SphinxClassDoc(SphinxDocString, ClassDoc):
    def __init__(self, obj, doc=None, func_doc=None, config={}):
        self.use_plots = config.get('use_plots', False)
        ClassDoc.__init__(self, obj, doc=doc, func_doc=None, config=config)

class SphinxObjDoc(SphinxDocString):
    def __init__(self, obj, doc=None, config={}):
        self._f = obj
        SphinxDocString.__init__(self, doc, config=config)

def get_doc_object(obj, what=None, doc=None, config={}):
    if what is None:
        if inspect.isclass(obj):
            what = 'class'
        elif inspect.ismodule(obj):
            what = 'module'
        elif callable(obj):
            what = 'function'
        else:
            what = 'object'
    if what == 'class':
        return SphinxClassDoc(obj, func_doc=SphinxFunctionDoc, doc=doc,
                              config=config)
    elif what in ('function', 'method'):
        return SphinxFunctionDoc(obj, doc=doc, config=config)
    else:
        if doc is None:
            doc = pydoc.getdoc(obj)
        return SphinxObjDoc(obj, doc, config=config)

"""
========
numpydoc
========

Sphinx extension that handles docstrings in the Numpy standard format. [1]

It will:

- Convert Parameters etc. sections to field lists.
- Convert See Also section to a See also entry.
- Renumber references.
- Extract the signature from the docstring, if it can't be determined otherwise.

.. [1] http://projects.scipy.org/numpy/wiki/CodingStyleGuidelines#docstring-standard

"""

import os, re, pydoc
from docscrape_sphinx import get_doc_object, SphinxDocString
from sphinx.util.compat import Directive
import inspect

def mangle_docstrings(app, what, name, obj, options, lines,
                      reference_offset=[0]):

    cfg = dict(use_plots=app.config.numpydoc_use_plots,
               show_class_members=app.config.numpydoc_show_class_members)

    if what == 'module':
        # Strip top title
        title_re = re.compile(ur'^\s*[#*=]{4,}\n[a-z0-9 -]+\n[#*=]{4,}\s*',
                              re.I|re.S)
        lines[:] = title_re.sub(u'', u"\n".join(lines)).split(u"\n")
    else:
        doc = get_doc_object(obj, what, u"\n".join(lines), config=cfg)
        lines[:] = unicode(doc).split(u"\n")

    if app.config.numpydoc_edit_link and hasattr(obj, '__name__') and \
           obj.__name__:
        if hasattr(obj, '__module__'):
            v = dict(full_name=u"%s.%s" % (obj.__module__, obj.__name__))
        else:
            v = dict(full_name=obj.__name__)
        lines += [u'', u'.. htmlonly::', '']
        lines += [u'    %s' % x for x in
                  (app.config.numpydoc_edit_link % v).split("\n")]

    # replace reference numbers so that there are no duplicates
    references = []
    for line in lines:
        line = line.strip()
        m = re.match(ur'^.. \[([a-z0-9_.-])\]', line, re.I)
        if m:
            references.append(m.group(1))

    # start renaming from the longest string, to avoid overwriting parts
    references.sort(key=lambda x: -len(x))
    if references:
        for i, line in enumerate(lines):
            for r in references:
                if re.match(ur'^\d+$', r):
                    new_r = u"R%d" % (reference_offset[0] + int(r))
                else:
                    new_r = u"%s%d" % (r, reference_offset[0])
                lines[i] = lines[i].replace(u'[%s]_' % r,
                                            u'[%s]_' % new_r)
                lines[i] = lines[i].replace(u'.. [%s]' % r,
                                            u'.. [%s]' % new_r)

    reference_offset[0] += len(references)

def mangle_signature(app, what, name, obj, options, sig, retann):
    # Do not try to inspect classes that don't define `__init__`
    if (inspect.isclass(obj) and
        (not hasattr(obj, '__init__') or
        'initializes x; see ' in pydoc.getdoc(obj.__init__))):
        return '', ''

    if not (callable(obj) or hasattr(obj, '__argspec_is_invalid_')): return
    if not hasattr(obj, '__doc__'): return

    doc = SphinxDocString(pydoc.getdoc(obj))
    if doc['Signature']:
        sig = re.sub(u"^[^(]*", u"", doc['Signature'])
        return sig, u''

def setup(app, get_doc_object_=get_doc_object):
    global get_doc_object
    get_doc_object = get_doc_object_

    app.connect('autodoc-process-docstring', mangle_docstrings)
    app.connect('autodoc-process-signature', mangle_signature)
    app.add_config_value('numpydoc_edit_link', None, False)
    app.add_config_value('numpydoc_use_plots', None, False)
    app.add_config_value('numpydoc_show_class_members', True, True)

    # Extra mangling domains
    app.add_domain(NumpyPythonDomain)
    app.add_domain(NumpyCDomain)

#------------------------------------------------------------------------------
# Docstring-mangling domains
#------------------------------------------------------------------------------

from docutils.statemachine import ViewList
from sphinx.domains.c import CDomain
from sphinx.domains.python import PythonDomain

class ManglingDomainBase(object):
    directive_mangling_map = {}

    def __init__(self, *a, **kw):
        super(ManglingDomainBase, self).__init__(*a, **kw)
        self.wrap_mangling_directives()

    def wrap_mangling_directives(self):
        for name, objtype in self.directive_mangling_map.items():
            self.directives[name] = wrap_mangling_directive(
                self.directives[name], objtype)

class NumpyPythonDomain(ManglingDomainBase, PythonDomain):
    name = 'np'
    directive_mangling_map = {
        'function': 'function',
        'class': 'class',
        'exception': 'class',
        'method': 'function',
        'classmethod': 'function',
        'staticmethod': 'function',
        'attribute': 'attribute',
    }

class NumpyCDomain(ManglingDomainBase, CDomain):
    name = 'np-c'
    directive_mangling_map = {
        'function': 'function',
        'member': 'attribute',
        'macro': 'function',
        'type': 'class',
        'var': 'object',
    }

def wrap_mangling_directive(base_directive, objtype):
    class directive(base_directive):
        def run(self):
            env = self.state.document.settings.env

            name = None
            if self.arguments:
                m = re.match(r'^(.*\s+)?(.*?)(\(.*)?', self.arguments[0])
                name = m.group(2).strip()

            if not name:
                name = self.arguments[0]

            lines = list(self.content)
            mangle_docstrings(env.app, objtype, name, None, None, lines)
            self.content = ViewList(lines, self.content.parent)

            return base_directive.run(self)

    return directive


"""Extract reference documentation from the NumPy source tree.

"""

import inspect
import textwrap
import re
import pydoc
from StringIO import StringIO
from warnings import warn

class Reader(object):
    """A line-based string reader.

    """
    def __init__(self, data):
        """
        Parameters
        ----------
        data : str
           String with lines separated by '\n'.

        """
        if isinstance(data,list):
            self._str = data
        else:
            self._str = data.split('\n') # store string as list of lines

        self.reset()

    def __getitem__(self, n):
        return self._str[n]

    def reset(self):
        self._l = 0 # current line nr

    def read(self):
        if not self.eof():
            out = self[self._l]
            self._l += 1
            return out
        else:
            return ''

    def seek_next_non_empty_line(self):
        for l in self[self._l:]:
            if l.strip():
                break
            else:
                self._l += 1

    def eof(self):
        return self._l >= len(self._str)

    def read_to_condition(self, condition_func):
        start = self._l
        for line in self[start:]:
            if condition_func(line):
                return self[start:self._l]
            self._l += 1
            if self.eof():
                return self[start:self._l+1]
        return []

    def read_to_next_empty_line(self):
        self.seek_next_non_empty_line()
        def is_empty(line):
            return not line.strip()
        return self.read_to_condition(is_empty)

    def read_to_next_unindented_line(self):
        def is_unindented(line):
            return (line.strip() and (len(line.lstrip()) == len(line)))
        return self.read_to_condition(is_unindented)

    def peek(self,n=0):
        if self._l + n < len(self._str):
            return self[self._l + n]
        else:
            return ''

    def is_empty(self):
        return not ''.join(self._str).strip()


class NumpyDocString(object):
    def __init__(self, docstring, config={}):
        docstring = textwrap.dedent(docstring).split('\n')

        self._doc = Reader(docstring)
        self._parsed_data = {
            'Signature': '',
            'Summary': [''],
            'Extended Summary': [],
            'Parameters': [],
            'Returns': [],
            'Raises': [],
            'Warns': [],
            'Other Parameters': [],
            'Attributes': [],
            'Methods': [],
            'See Also': [],
            'Notes': [],
            'Warnings': [],
            'References': '',
            'Examples': '',
            'index': {}
            }

        self._parse()

    def __getitem__(self,key):
        return self._parsed_data[key]

    def __setitem__(self,key,val):
        if not self._parsed_data.has_key(key):
            warn("Unknown section %s" % key)
        else:
            self._parsed_data[key] = val

    def _is_at_section(self):
        self._doc.seek_next_non_empty_line()

        if self._doc.eof():
            return False

        l1 = self._doc.peek().strip()  # e.g. Parameters

        if l1.startswith('.. index::'):
            return True

        l2 = self._doc.peek(1).strip() #    ---------- or ==========
        return l2.startswith('-'*len(l1)) or l2.startswith('='*len(l1))

    def _strip(self,doc):
        i = 0
        j = 0
        for i,line in enumerate(doc):
            if line.strip(): break

        for j,line in enumerate(doc[::-1]):
            if line.strip(): break

        return doc[i:len(doc)-j]

    def _read_to_next_section(self):
        section = self._doc.read_to_next_empty_line()

        while not self._is_at_section() and not self._doc.eof():
            if not self._doc.peek(-1).strip(): # previous line was empty
                section += ['']

            section += self._doc.read_to_next_empty_line()

        return section

    def _read_sections(self):
        while not self._doc.eof():
            data = self._read_to_next_section()
            name = data[0].strip()

            if name.startswith('..'): # index section
                yield name, data[1:]
            elif len(data) < 2:
                yield StopIteration
            else:
                yield name, self._strip(data[2:])

    def _parse_param_list(self,content):
        r = Reader(content)
        params = []
        while not r.eof():
            header = r.read().strip()
            if ' : ' in header:
                arg_name, arg_type = header.split(' : ')[:2]
            else:
                arg_name, arg_type = header, ''

            desc = r.read_to_next_unindented_line()
            desc = dedent_lines(desc)

            params.append((arg_name,arg_type,desc))

        return params


    _name_rgx = re.compile(r"^\s*(:(?P<role>\w+):`(?P<name>[a-zA-Z0-9_.-]+)`|"
                           r" (?P<name2>[a-zA-Z0-9_.-]+))\s*", re.X)
    def _parse_see_also(self, content):
        """
        func_name : Descriptive text
            continued text
        another_func_name : Descriptive text
        func_name1, func_name2, :meth:`func_name`, func_name3

        """
        items = []

        def parse_item_name(text):
            """Match ':role:`name`' or 'name'"""
            m = self._name_rgx.match(text)
            if m:
                g = m.groups()
                if g[1] is None:
                    return g[3], None
                else:
                    return g[2], g[1]
            raise ValueError("%s is not a item name" % text)

        def push_item(name, rest):
            if not name:
                return
            name, role = parse_item_name(name)
            items.append((name, list(rest), role))
            del rest[:]

        current_func = None
        rest = []

        for line in content:
            if not line.strip(): continue

            m = self._name_rgx.match(line)
            if m and line[m.end():].strip().startswith(':'):
                push_item(current_func, rest)
                current_func, line = line[:m.end()], line[m.end():]
                rest = [line.split(':', 1)[1].strip()]
                if not rest[0]:
                    rest = []
            elif not line.startswith(' '):
                push_item(current_func, rest)
                current_func = None
                if ',' in line:
                    for func in line.split(','):
                        push_item(func, [])
                elif line.strip():
                    current_func = line
            elif current_func is not None:
                rest.append(line.strip())
        push_item(current_func, rest)
        return items

    def _parse_index(self, section, content):
        """
        .. index: default
           :refguide: something, else, and more

        """
        def strip_each_in(lst):
            return [s.strip() for s in lst]

        out = {}
        section = section.split('::')
        if len(section) > 1:
            out['default'] = strip_each_in(section[1].split(','))[0]
        for line in content:
            line = line.split(':')
            if len(line) > 2:
                out[line[1]] = strip_each_in(line[2].split(','))
        return out

    def _parse_summary(self):
        """Grab signature (if given) and summary"""
        if self._is_at_section():
            return

        summary = self._doc.read_to_next_empty_line()
        summary_str = " ".join([s.strip() for s in summary]).strip()
        if re.compile('^([\w., ]+=)?\s*[\w\.]+\(.*\)$').match(summary_str):
            self['Signature'] = summary_str
            if not self._is_at_section():
                self['Summary'] = self._doc.read_to_next_empty_line()
        else:
            self['Summary'] = summary

        if not self._is_at_section():
            self['Extended Summary'] = self._read_to_next_section()

    def _parse(self):
        self._doc.reset()
        self._parse_summary()

        for (section,content) in self._read_sections():
            if not section.startswith('..'):
                section = ' '.join([s.capitalize() for s in section.split(' ')])
            if section in ('Parameters', 'Attributes', 'Methods',
                           'Returns', 'Raises', 'Warns'):
                self[section] = self._parse_param_list(content)
            elif section.startswith('.. index::'):
                self['index'] = self._parse_index(section, content)
            elif section == 'See Also':
                self['See Also'] = self._parse_see_also(content)
            else:
                self[section] = content

    # string conversion routines

    def _str_header(self, name, symbol='-'):
        return [name, len(name)*symbol]

    def _str_indent(self, doc, indent=4):
        out = []
        for line in doc:
            out += [' '*indent + line]
        return out

    def _str_signature(self):
        if self['Signature']:
            return [self['Signature'].replace('*','\*')] + ['']
        else:
            return ['']

    def _str_summary(self):
        if self['Summary']:
            return self['Summary'] + ['']
        else:
            return []

    def _str_extended_summary(self):
        if self['Extended Summary']:
            return self['Extended Summary'] + ['']
        else:
            return []

    def _str_param_list(self, name):
        out = []
        if self[name]:
            out += self._str_header(name)
            for param,param_type,desc in self[name]:
                out += ['%s : %s' % (param, param_type)]
                out += self._str_indent(desc)
            out += ['']
        return out

    def _str_section(self, name):
        out = []
        if self[name]:
            out += self._str_header(name)
            out += self[name]
            out += ['']
        return out

    def _str_see_also(self, func_role):
        if not self['See Also']: return []
        out = []
        out += self._str_header("See Also")
        last_had_desc = True
        for func, desc, role in self['See Also']:
            if role:
                link = ':%s:`%s`' % (role, func)
            elif func_role:
                link = ':%s:`%s`' % (func_role, func)
            else:
                link = "`%s`_" % func
            if desc or last_had_desc:
                out += ['']
                out += [link]
            else:
                out[-1] += ", %s" % link
            if desc:
                out += self._str_indent([' '.join(desc)])
                last_had_desc = True
            else:
                last_had_desc = False
        out += ['']
        return out

    def _str_index(self):
        idx = self['index']
        out = []
        out += ['.. index:: %s' % idx.get('default','')]
        for section, references in idx.iteritems():
            if section == 'default':
                continue
            out += ['   :%s: %s' % (section, ', '.join(references))]
        return out

    def __str__(self, func_role=''):
        out = []
        out += self._str_signature()
        out += self._str_summary()
        out += self._str_extended_summary()
        for param_list in ('Parameters','Returns','Raises'):
            out += self._str_param_list(param_list)
        out += self._str_section('Warnings')
        out += self._str_see_also(func_role)
        for s in ('Notes','References','Examples'):
            out += self._str_section(s)
        for param_list in ('Attributes', 'Methods'):
            out += self._str_param_list(param_list)
        out += self._str_index()
        return '\n'.join(out)


def indent(str,indent=4):
    indent_str = ' '*indent
    if str is None:
        return indent_str
    lines = str.split('\n')
    return '\n'.join(indent_str + l for l in lines)

def dedent_lines(lines):
    """Deindent a list of lines maximally"""
    return textwrap.dedent("\n".join(lines)).split("\n")

def header(text, style='-'):
    return text + '\n' + style*len(text) + '\n'


class FunctionDoc(NumpyDocString):
    def __init__(self, func, role='func', doc=None, config={}):
        self._f = func
        self._role = role # e.g. "func" or "meth"

        if doc is None:
            if func is None:
                raise ValueError("No function or docstring given")
            doc = inspect.getdoc(func) or ''
        NumpyDocString.__init__(self, doc)

        if not self['Signature'] and func is not None:
            func, func_name = self.get_func()
            try:
                # try to read signature
                argspec = inspect.getargspec(func)
                argspec = inspect.formatargspec(*argspec)
                argspec = argspec.replace('*','\*')
                signature = '%s%s' % (func_name, argspec)
            except TypeError, e:
                signature = '%s()' % func_name
            self['Signature'] = signature

    def get_func(self):
        func_name = getattr(self._f, '__name__', self.__class__.__name__)
        if inspect.isclass(self._f):
            func = getattr(self._f, '__call__', self._f.__init__)
        else:
            func = self._f
        return func, func_name

    def __str__(self):
        out = ''

        func, func_name = self.get_func()
        signature = self['Signature'].replace('*', '\*')

        roles = {'func': 'function',
                 'meth': 'method'}

        if self._role:
            if not roles.has_key(self._role):
                print "Warning: invalid role %s" % self._role
            out += '.. %s:: %s\n    \n\n' % (roles.get(self._role,''),
                                             func_name)

        out += super(FunctionDoc, self).__str__(func_role=self._role)
        return out


class ClassDoc(NumpyDocString):
    def __init__(self, cls, doc=None, modulename='', func_doc=FunctionDoc,
                 config={}):
        if not inspect.isclass(cls) and cls is not None:
            raise ValueError("Expected a class or None, but got %r" % cls)
        self._cls = cls

        if modulename and not modulename.endswith('.'):
            modulename += '.'
        self._mod = modulename

        if doc is None:
            if cls is None:
                raise ValueError("No class or documentation string given")
            doc = pydoc.getdoc(cls)

        NumpyDocString.__init__(self, doc)

        if config.get('show_class_members', True):
            if not self['Methods']:
                self['Methods'] = [(name, '', '')
                                   for name in sorted(self.methods)]
            if not self['Attributes']:
                self['Attributes'] = [(name, '', '')
                                      for name in sorted(self.properties)]

    @property
    def methods(self):
        if self._cls is None:
            return []
        return [name for name,func in inspect.getmembers(self._cls)
                if not name.startswith('_') and callable(func)]

    @property
    def properties(self):
        if self._cls is None:
            return []
        return [name for name,func in inspect.getmembers(self._cls)
                if not name.startswith('_') and func is None]

