#! /usr/bin/env python
# Last Change: Sat Jul 21 09:00 PM 2007 J

# Copyright (C) 2007-2009 Cournapeau David <cournape@gmail.com>
#               2010 Fabian Pedregosa <fabian.pedregosa@inria.fr>

descr   = """A set of python modules for machine learning and data mining"""

from os.path import join
import os
import sys
import shutil

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
        install_requires=[
              'numpy >= 1.1'],
        maintainer  = MAINTAINER,
        include_package_data = True,
        maintainer_email = MAINTAINER_EMAIL,
        description = DESCRIPTION,
        license = LICENSE,
        url = URL,
        version = VERSION,
        download_url = DOWNLOAD_URL,
        long_description = LONG_DESCRIPTION,
        test_suite="nose.collector", # for python setup.py test
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

# Author: Alexandre Gramfort <alexandre.gramfort@inria.fr>
#         Fabian Pedregosa <fabian.pedregosa@inria.fr>
#         Olivier Grisel <olivier.grisel@ensta.org>
#         Vincent Michel <vincent.michel@inria.fr>
#
# License: BSD Style.


"""
Generalized Linear models.
"""

import warnings

import numpy as np
import scipy.linalg 
import scipy.sparse as sp # needed by LeastAngleRegression

from . import cd_fast
from .utils.extmath import fast_logdet
from .cross_val import KFold
from ._minilearn import lars_fit_wrap
from .base import BaseEstimator

###
### TODO: intercept for all models
### We should define a common function to center data instead of
### repeating the same code inside each fit method.
###
### Also, bayesian_ridge_regression and bayesian_regression_ard
### should be squashed into its respective objects.
###

class LinearModel(BaseEstimator):
    """Base class for Linear Models"""

    def predict(self, X):
        """
        Predict using the linear model

        Parameters
        ----------
        X : numpy array of shape [nsamples,nfeatures]

        Returns
        -------
        C : array, shape = [nsample]
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
            return ("<%s \n  Fitted: explained variance=%s>" %
                    (repr(self), self.explained_variance_))
        else:
            return "<%s \n  Not fitted to data>" % repr(self)


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
        X : numpy array of shape [nsamples,nfeatures]
            Training data
        Y : numpy array of shape [nsamples]
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
            self.intercept_ = np.zeros(self.coef_X.shape[1])
        return self


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
    >>> nsamples, nfeatures = 10, 5
    >>> np.random.seed(0)
    >>> Y = np.random.randn(nsamples)
    >>> X = np.random.randn(nsamples, nfeatures)
    >>> clf = Ridge(alpha=1.0)
    >>> clf.fit(X, Y) #doctest: +ELLIPSIS
    Ridge(alpha=1.0,
          fit_intercept=True)
    """

    def __init__(self, alpha=1.0, fit_intercept=True):
        self.alpha = alpha
        self.fit_intercept = True


    def fit(self, X, Y, **params):
        """
        Fit Ridge regression model

        Parameters
        ----------
        X : numpy array of shape [nsamples,nfeatures]
            Training data
        Y : numpy array of shape [nsamples]
            Target values

        Returns
        -------
        self : returns an instance of self.
        """
        self._set_params(**params)
        nsamples, nfeatures = X.shape

        if self.fit_intercept:
            self._xmean = X.mean(axis=0)
            self._ymean = Y.mean(axis=0)
            X = X - self._xmean
            Y = Y - self._ymean
        else:
            self._xmean = 0.
            self._ymean = 0.

        if nsamples > nfeatures:
            # w = inv(X^t X + alpha*Id) * X.T y
            self.coef_ = scipy.linalg.solve(
                np.dot(X.T, X) + self.alpha * np.eye(nfeatures),
                np.dot(X.T, Y))
        else:
            # w = X.T * inv(X X^t + alpha*Id) y
            self.coef_ = np.dot(X.T, scipy.linalg.solve(
                np.dot(X, X.T) + self.alpha * np.eye(nsamples), Y))

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
        X : numpy array of shape [nsamples,nfeatures]
            Training data
        Y : numpy array of shape [nsamples]
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
    sigma = scipy.linalg.pinv(alpha*ones + beta*gram)
    w = np.dot(beta*sigma,np.dot(X.T,Y))
    old_w = np.copy(w)
    eigen = np.real(scipy.linalg.eigvals(gram.T))
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
        sigma = scipy.linalg.pinv(alpha*ones + beta*gram)
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
    sigma = scipy.linalg.pinv(alpha*ones + beta*gram)
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
        sigma = scipy.linalg.pinv(alpha[keep_a]*ones+ beta*gram)
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
        ll += np.dot(Y.T,np.dot(scipy.linalg.pinv(C_),Y))
        log_likelihood.append(-0.5*ll)

    return w, alpha, beta, sigma, log_likelihood


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
    `coef_` : array, shape = [nfeatures]
        parameter vector (w in the fomulation formula)

    `intercept_` : float
        independent term in decision function.

    Examples
    --------
    >>> from scikits.learn import glm
    >>> clf = glm.Lasso(alpha=0.1)
    >>> clf.fit([[0,0], [1, 1], [2, 2]], [0, 1, 2])
    Lasso(alpha=0.1,
          coef_=[ 0.85  0.  ],
          fit_intercept=True)
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
        X: numpy array of shape [nsamples,nfeatures]
            Training data

        Y: numpy array of shape [nsamples]
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

        nsamples = X.shape[0]
        alpha = self.alpha * nsamples

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

        nsamples = X.shape[0]
        alpha = self.alpha * self.rho * nsamples
        beta = self.alpha * (1.0 - self.rho) * nsamples

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
    X : numpy array of shape [nsamples,nfeatures]
        Training data

    Y : numpy array of shape [nsamples]
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
    nsamples = X.shape[0]
    if alphas is None:
        alpha_max = np.abs(np.dot(X.T, y)).max() / nsamples
        alphas = np.linspace(np.log(alpha_max), np.log(eps * alpha_max), n_alphas)
        alphas = np.exp(alphas)
    else:
        alphas = np.sort(alphas)[::-1] # make sure alphas are properly ordered
    coef_ = None # init coef_
    models = []
    for alpha in alphas:
        model = Lasso(coef_=coef_, alpha=alpha)
        model.fit(X, y, **fit_params)
        if verbose: print model
        coef_ = model.coef_.copy()
        models.append(model)
    return models

def enet_path(X, y, rho=0.5, eps=1e-3, n_alphas=100, alphas=None,
              verbose=False, fit_params=dict()):

    """Compute Elastic-Net path with coordinate descent

    Parameters
    ----------
    X : numpy array of shape [nsamples,nfeatures]
        Training data

    Y : numpy array of shape [nsamples]
        Target values

    eps : float
        Length of the path. eps=1e-3 means that
        alpha_min / alpha_max = 1e-3

    n_alphas : int
        Number of alphas along the regularization path

    alphas : numpy array
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
    nsamples = X.shape[0]
    if alphas is None:
        alpha_max = np.abs(np.dot(X.T, y)).max() / (nsamples*rho)
        alphas = np.linspace(np.log(alpha_max), np.log(eps * alpha_max), n_alphas)
        alphas = np.exp(alphas)
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

        X : numpy array of shape [nsamples,nfeatures]
            Training data

        Y : numpy array of shape [nsamples]
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
        self.alpha = model.alpha
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
    See examples/lasso_path_with_crossvalidation.py for an example.
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
    See examples/lasso_path_with_crossvalidation.py for an example.
    """

    path = staticmethod(enet_path)

    def __init__(self, rho=0.5, eps=1e-3, n_alphas=100, alphas=None):
        self.rho = rho
        self.eps = eps
        self.n_alphas = n_alphas
        self.alphas = alphas


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
        X : numpy array of shape [nsamples,nfeatures]
            Training data

        Y : numpy array of shape [nsamples]
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
        X : numpy array of shape [nsamples,nfeatures]

        Returns
        -------
        C : array, shape = [nsample]
            Returns predicted values.
        """
        X = np.asanyarray(X, dtype=np.float64, order='C')
        if normalize:
            X -= self._xmean
            X /= self._norms
        return  np.dot(X, self.coef_) + self.intercept_



#
# Gaussian Mixture Models
#
# Author: Ron Weiss <ronweiss@gmail.com>
#         Fabian Pedregosa <fabian.pedregosa@inria.fr>
#

import itertools
import time

import numpy as np
from scipy import cluster

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
        Asum[np.isnan(Asum)] = -np.Inf
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
    mean : array_like, shape (ndim,)
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
    obs : array, shape (n, ndim)
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


class GMM(object):
    """Gaussian Mixture Model

    Representation of a Gaussian mixture model probability distribution.
    This class allows for easy evaluation of, sampling from, and
    maximum-likelihood estimation of the parameters of a GMM distribution.

    Attributes
    ----------
    cvtype : string (read-only)
        String describing the type of covariance parameters used by
        the GMM.  Must be one of 'spherical', 'tied', 'diag', 'full'.
    ndim : int (read-only)
        Dimensionality of the Gaussians.
    nstates : int (read-only)
        Number of states (mixture components).
    weights : array, shape (`nstates`,)
        Mixing weights for each mixture component.
    means : array, shape (`nstates`, `ndim`)
        Mean parameters for each mixture component.
    covars : array
        Covariance parameters for each mixture component.  The shape
        depends on `cvtype`:
            (`nstates`,)                if 'spherical',
            (`ndim`, `ndim`)            if 'tied',
            (`nstates`, `ndim`)         if 'diag',
            (`nstates`, `ndim`, `ndim`) if 'full'
    labels : list, len `nstates`
        Optional labels for each mixture component.

    Methods
    -------
    eval(obs)
        Compute the log likelihood of `obs` under the model.
    decode(obs)
        Find most likely mixture components for each point in `obs`.
    rvs(n=1)
        Generate `n` samples from the model.
    fit(obs)
        Estimate model parameters from `obs` using the EM algorithm.
    predict(obs)
        Like decode, find most likely mixtures components for each
        observation in `obs`.

    Examples
    --------
    >>> gmm = GMM(2, ndim=1)
    >>> obs = numpy.concatenate((numpy.random.randn(100, 1),
    ...                          10 + numpy.random.randn(300, 1)))
    >>> gmm.fit(obs)
    >>> gmm.weights, gmm.means, gmm.covars
    (array([ 0.25,  0.75]),
     array([[ -0.22744484],
           [ 10.07096441]]),
     array([[ 1.02857617],
           [ 1.11389491]]))
    >>> gmm.decode([0, 2, 9, 10])
    array([0, 0, 1, 1])
    >>> # Refit the model on new data (initial parameters remain the same).
    >>> gmm.fit(numpy.concatenate((20 * [0], 20 * [10])))
    """

    def __init__(self, nstates=1, ndim=1, cvtype='diag', weights=None,
                 means=None, covars=None):
        """Create a Gaussian mixture model

        Initializes parameters such that every mixture component has
        zero mean and identity covariance.

        Parameters
        ----------
        nstates : int
            Number of mixture components.
        ndim : int
            Dimensionality of the mixture components.
        cvtype : string (read-only)
            String describing the type of covariance parameters to
            use.  Must be one of 'spherical', 'tied', 'diag', 'full'.
            Defaults to 'diag'.
        """

        self._nstates = nstates
        self._ndim = ndim
        self._cvtype = cvtype

        if not cvtype in ['spherical', 'tied', 'diag', 'full']:
            raise ValueError('bad cvtype')

        if weights is None:
            weights = np.tile(1.0 / nstates, nstates)
        self.weights = weights

        if means is None:
            means = np.zeros((nstates, ndim))
        self.means = means

        if covars is None:
            covars = _distribute_covar_matrix_to_match_cvtype(
                np.eye(ndim), cvtype, nstates)
        self.covars = covars
        
        self.labels = [None] * nstates

    # Read-only properties.
    @property
    def cvtype(self):
        """Covariance type of the model.

        Must be one of 'spherical', 'tied', 'diag', 'full'.
        """
        return self._cvtype

    @property
    def ndim(self):
        """Dimensionality of the mixture components."""
        return self._ndim

    @property
    def nstates(self):
        """Number of mixture components in the model."""
        return self._nstates

    def _get_covars(self):
        """Return covars as a full matrix."""
        if self.cvtype == 'full':
            return self._covars
        elif self.cvtype == 'diag':
            return [np.diag(cov) for cov in self._covars]
        elif self.cvtype == 'tied':
            return [self._covars]*self._nstates
        elif self.cvtype == 'spherical':
            return [np.eye(self._nstates) * f for f in self._covars]

    def _set_covars(self, covars):
        covars = np.asanyarray(covars)
        _validate_covars(covars, self._cvtype, self._nstates, self._ndim)
        self._covars = covars

    covars = property(_get_covars, _set_covars)

    def _get_means(self):
        """Mean parameters for each mixture component."""
        return self._means

    def _set_means(self, means):
        means = np.asarray(means)
        if means.shape != (self._nstates, self._ndim):
            raise ValueError, 'means must have shape (nstates, ndim)'
        self._means = means.copy()

    means = property(_get_means, _set_means)
    
    def _get_weights(self):
        """Mixing weights for each mixture component."""
        return np.exp(self._log_weights)

    def _set_weights(self, weights):
        if len(weights) != self._nstates:
            raise ValueError, 'weights must have length nstates'
        if not np.allclose(np.sum(weights), 1.0):
            raise ValueError, 'weights must sum to 1.0'
        
        self._log_weights = np.log(np.asarray(weights).copy())

    weights = property(_get_weights, _set_weights)

    def eval(self, obs):
        """Evaluate the model on data

        Compute the log probability of `obs` under the model and
        return the posterior distribution (responsibilities) of each
        mixture component for each element of `obs`

        Parameters
        ----------
        obs : array_like, shape (n, ndim)
            List of ndim-dimensional data points.  Each row corresponds to a
            single data point.

        Returns
        -------
        logprob : array_like, shape (n,)
            Log probabilities of each data point in `obs`
        posteriors: array_like, shape (n, nstates)
            Posterior probabilities of each mixture component for each
            observation
        """
        obs = np.asanyarray(obs)
        lpr = (lmvnpdf(obs, self._means, self._covars, self._cvtype)
               + self._log_weights)
        logprob = logsum(lpr, axis=1)
        posteriors = np.exp(lpr - logprob[:,np.newaxis])
        return logprob, posteriors


    def predict (self, X):
        """Predict label for data

        Parameters
        ----------
        T : array-like, shape = [nsamples, nfeatures]

        Returns
        -------
        C : array, shape = [nsample]
        
        """
        logprob, posteriors = self.eval(X)
        return np.argmax(posteriors, axis=1)
    

    def lpdf(self, obs):
        """Compute the log probability under the model.

        Parameters
        ----------
        obs : array_like, shape (n, ndim)
            List of ndim-dimensional data points.  Each row corresponds to a
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
        obs : array_like, shape (n, ndim)
            List of ndim-dimensional data points.  Each row corresponds to a
            single data point.

        Returns
        -------
        components : array_like, shape (n,)
            Index of the most likelihod mixture components for each observation
        """
        logprob, posteriors = self.eval(obs)
        return logprob, posteriors.argmax(axis=1)
        
    def rvs(self, n=1):
        """Generate random samples from the model.

        Parameters
        ----------
        n : int
            Number of samples to generate.

        Returns
        -------
        obs : array_like, shape (n, ndim)
            List of samples
        """
        weight_pdf = self.weights
        weight_cdf = np.cumsum(weight_pdf)

        obs = np.empty((n, self._ndim))
        for x in xrange(n):
            rand = np.random.rand()
            c = (weight_cdf > rand).argmax()
            if self._cvtype == 'tied':
                cv = self._covars
            else:
                cv = self._covars[c]
            obs[x] = sample_gaussian(self._means[c], cv, self._cvtype)
        return obs

    def fit(self, X, niter=10, min_covar=1.0, thresh=1e-2, params='wmc',
            init_params='wmc', **kwargs):
        """Estimate model parameters with the expectation-maximization
        algorithm.

        A initialization step is performed before entering the em
        algorithm. If you want to avoid this step, set the keyword
        argument init_params to the empty string ''. Likewise, if you
        would like just to do an initialization, call this method with
        niter=0.

        Parameters
        ----------
        X : array_like, shape (n, ndim)
            List of ndim-dimensional data points.  Each row corresponds to a
            single data point.
        niter : int, optional
            Number of EM iterations to perform.
        min_covar : float, optional
            Floor on the diagonal of the covariance matrix to prevent
            overfitting.  Defaults to 1.0.
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

        Returns
        -------
        logprob : list
            Log probabilities of each data point in `X` for each iteration
        """

        ## initialization step

        X = np.asanyarray(X, dtype=np.float64)

        if 'm' in init_params:
            if not 'minit' in kwargs:
                kwargs.update({'minit': 'points'})
            self._means, tmp = cluster.vq.kmeans2(X, self._nstates, **kwargs)

        if 'w' in init_params:
            self.weights = np.tile(1.0 / self._nstates, self._nstates)

        if 'c' in init_params:
            cv = np.cov(X.T)
            if not cv.shape:
                cv.shape = (1, 1)
            self._covars = _distribute_covar_matrix_to_match_cvtype(
                cv, self._cvtype, self._nstates)

        # EM algorithm
        logprob = []
        for i in xrange(niter):
            # Expectation step
            curr_logprob, posteriors = self.eval(X)
            logprob.append(curr_logprob.sum())

            # Check for convergence.
            if i > 0 and abs(logprob[-1] - logprob[-2]) < thresh:
                break

            # Maximization step
            self._do_mstep(X, posteriors, params, min_covar)

        return logprob

    def _do_mstep(self, X, posteriors, params, min_covar=0):
            w = posteriors.sum(axis=0)
            avg_obs = np.dot(posteriors.T, X)
            norm = 1.0 / w[:,np.newaxis]
            
            if 'w' in params:
                self._weights = w / w.sum()
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
    #                      + np.sum(np.log(covars), 1))[np.newaxis,:], (nobs,1))
    lpr = -0.5 * (ndim * np.log(2 * np.pi) + np.sum(np.log(covars), 1)
                  + np.sum((means**2) / covars, 1)
                  - 2 * np.dot(obs, (means / covars).T)
                  + np.dot(obs**2, (1.0 / covars).T))
    return lpr

def _lmvnpdfspherical(obs, means=0.0, covars=1.0):
    cv = covars.copy()
    if covars.ndim == 1:
        cv = cv[:,np.newaxis]
    return _lmvnpdfdiag(obs, means, np.tile(cv, (1, obs.shape[-1])))

def _lmvnpdftied(obs, means, covars):
    nobs, ndim = obs.shape
    nmix = len(means)
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
        lpr[:,c] = -0.5 * (ndim * np.log(2 * np.pi) + np.log(np.linalg.det(cv)))
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
            raise ValueError, "'spherical' covars must have length nmix"
        elif np.any(covars <= 0):
            raise ValueError, "'spherical' covars must be non-negative"
    elif cvtype == 'tied':
        if covars.shape != (ndim, ndim):
            raise ValueError, "'tied' covars must have shape (ndim, ndim)"
        elif (not np.allclose(covars, covars.T)
              or np.any(np.linalg.eigvalsh(covars) <= 0)):
            raise (ValueError,
                   "'tied' covars must be symmetric, positive-definite")
    elif cvtype == 'diag':
        if covars.shape != (nmix, ndim):
            raise ValueError, "'diag' covars must have shape (nmix, ndim)"
        elif np.any(covars <= 0):
            raise ValueError, "'diag' covars must be non-negative"
    elif cvtype == 'full':
        if covars.shape != (nmix, ndim, ndim):
            raise (ValueError,
                   "'full' covars must have shape (nmix, ndim, ndim)")
        for n,cv in enumerate(covars):
            if (not np.allclose(cv, cv.T)
                or np.any(np.linalg.eigvalsh(cv) <= 0)):
                raise (ValueError,
                       "component %d of 'full' covars must be symmetric,"
                       "positive-definite" % n)

def _distribute_covar_matrix_to_match_cvtype(tiedcv, cvtype, nstates):
    if cvtype == 'spherical':
        cv = np.tile(np.diag(tiedcv).mean(), nstates)
    elif cvtype == 'tied':
        cv = tiedcv
    elif cvtype == 'diag':
        cv = np.tile(np.diag(tiedcv), (nstates, 1))
    elif cvtype == 'full':
        cv = np.tile(tiedcv, (nstates, 1, 1))
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
    avg_means2 = gmm._means**2 
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
    cv = np.empty((gmm._nstates, gmm._ndim, gmm._ndim))
    for c in xrange(gmm._nstates):
        wobs = obs.T * posteriors[:,c]
        avg_obs2 = np.dot(wobs, obs) / posteriors[:,c].sum()
        mu = gmm._means[c][np.newaxis]
        cv[c] = (avg_obs2 - np.dot(mu, mu.T)
                 + min_covar * np.eye(gmm._ndim))
    return cv

def _covar_mstep_tied2(*args):
    return _covar_mstep_full(*args).mean(axis=0)

def _covar_mstep_tied(gmm, obs, posteriors, avg_obs, norm, min_covar):
    print "THIS IS BROKEN"
    # Eq. 15 from K. Murphy, "Fitting a Conditional Linear Gaussian
    avg_obs2 = np.dot(obs.T, obs)
    avg_means2 = np.dot(gmm._means.T, gmm._means)
    return (avg_obs2 - avg_means2 + min_covar * np.eye(gmm._ndim))

def _covar_mstep_slow(gmm, obs, posteriors, avg_obs, norm, min_covar):
    w = posteriors.sum(axis=0)
    covars = np.zeros(gmm._covars.shape)
    for c in xrange(gmm._nstates):
        mu = gmm._means[c]
        #cv = np.dot(mu.T, mu)
        avg_obs2 = np.zeros((gmm._ndim, gmm._ndim))
        for t,o in enumerate(obs):
            avg_obs2 += posteriors[t,c] * np.outer(o, o)
        cv = (avg_obs2 / w[c]
              - 2 * np.outer(avg_obs[c] / w[c], mu)
              + np.outer(mu, mu)
              + min_covar * np.eye(gmm._ndim))
        if gmm.cvtype == 'spherical':
            covars[c] = np.diag(cv).mean()
        elif gmm.cvtype == 'diag':
            covars[c] = np.diag(cv)
        elif gmm.cvtype == 'full':
            covars[c] = cv
        elif gmm.cvtype == 'tied':
            covars += cv / gmm._nstates
    return covars

_covar_mstep_funcs = {'spherical': _covar_mstep_spherical,
                      'diag': _covar_mstep_diag,
                      #'tied': _covar_mstep_tied,
                      #'full': _covar_mstep_full,
                      'tied': _covar_mstep_slow,
                      'full': _covar_mstep_slow}


# $Id$

import exceptions, warnings

import numpy as np
import scipy.linalg as linalg

from .base import BaseEstimator

class LDA(BaseEstimator):
    """
    Linear Discriminant Analysis (LDA)

    Parameters
    ----------
    X : array-like, shape = [nsamples, nfeatures]
        Training vector, where nsamples in the number of samples and
        nfeatures is the number of features.
    Y : array, shape = [nsamples]
        Target vector relative to X

    priors : array, optional, shape = [n_classes]
        Priors on classes

    use_svd : bool, optional
         Specify if the SVD from scipy should be used.

    Attributes
    ----------
    `means_` : array-like, shape = [n_classes, n_features]
        Class means
    `xbar` : float, shape = [n_features]
        Over all mean

    Methods
    -------
    fit(X, y) : self
        Fit the model

    predict(X) : array
        Predict using the model.

    Examples
    --------
    >>> X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])
    >>> Y = np.array([1, 1, 1, 2, 2, 2])
    >>> clf = LDA()
    >>> clf.fit(X, Y)    #doctest: +ELLIPSIS
    LDA(priors=None,
        use_svd=True)
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

    def fit(self, X, y, tol=1.0e-4, **params):
        self._set_params(**params)
        X = np.asanyarray(X)
        y = np.asanyarray(y)
        if X.ndim!=2:
            raise exceptions.ValueError('X must be a 2D array')
        n_samples = X.shape[0]
        n_features = X.shape[1]
        classes = np.unique(y)
        n_classes = classes.size
        if n_classes < 2:
            raise exceptions.ValueError('Y has less than 2 classes')
        classes_indices = [(y == c).ravel() for c in classes]
        if self.priors is None:
            counts = np.array([float(np.sum(group_indices)) \
                               for group_indices in classes_indices])
            self.priors_ = counts / n_samples
        else:
            self.priors_ = self.priors

        # Group means n_classes*n_features matrix
        means = []
        Xc = []
        for group_indices in classes_indices:
            Xg = X[group_indices, :]
            meang = Xg.mean(0)
            means.append(meang)
            # centered group data
            Xgc = Xg - meang
            Xc.append(Xgc)
        means = np.asarray(means)
        Xc = np.concatenate(Xc, 0)
        # ----------------------------
        # 1) within (univariate) scaling by with classes std-dev
        scaling = np.diag(1 / Xc.std(0))
        fac = float(1) / (n_samples - n_classes)
        # ----------------------------
        # 2) Within variance scaling
        X = np.sqrt(fac) * np.dot(Xc, scaling)
        # SVD of centered (within)scaled data
        if self.use_svd == True:
            U, S, V = linalg.svd(X, full_matrices=0)
        else:
            S, V = self.svd(X)

        rank = np.sum(S > tol)
        if rank < n_features:
            warnings.warn("Variables are collinear")
        # Scaling of within covariance is: V' 1/S
        scaling = np.dot(np.dot(scaling, V.T[:, :rank]), np.diag(1 / S[:rank]))
        ## ----------------------------
        ## 3) Between variance scaling
        # Overall mean
        xbar = np.dot(self.priors_, means)
        # Scale weighted centers
        X = np.dot(np.dot(np.diag(np.sqrt((n_samples * self.priors_)*fac)),
                          (means - xbar)),
                   scaling)
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
        self.xbar = xbar
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

    def predict(self, X):
        probas = self.predict_proba(X)
        y_pred = self.classes[probas.argmax(1)]
        return y_pred

    def predict_proba(self, X):
        #Ensure X is an array
        X = np.asanyarray(X)
        scaling = self.scaling
        # Remove overall mean (center) and scale
        # a) data
        X = np.dot(X - self.xbar, scaling)
        # b) centers
        dm = np.dot(self.means_ - self.xbar, scaling)
        # for each class k, compute the linear discrinant function(p. 87 Hastie)
        # of sphered (scaled data)
        dist = 0.5*np.sum(dm**2, 1) - np.log(self.priors_) - np.dot(X, dm.T)
        # take exp of min dist
        dist = np.exp(-dist + dist.min(1).reshape(X.shape[0], 1))
        # normalize by p(x)=sum_k p(x|k)
        probas = dist / dist.sum(1).reshape(X.shape[0], 1)
        # classify according to the maximun a posteriori
        return probas

"""Algorithms for clustering : Meanshift and Affinity propagation

Author: Alexandre Gramfort alexandre.gramfort@inria.fr
        Gael Varoquaux gael.varoquaux@normalesup.org
"""

import numpy as np

from .base import BaseEstimator

################################################################################
# MeanShift
################################################################################

def mean_shift(X, bandwidth):
    """Perform MeanShift Clustering of data using a flat kernel

    Parameters
    ==========

    X : array [n_samples, n_features]
        Input points

    bandwidth : float
        kernel bandwidth

    Returns
    ========

    cluster_centers: array [n_clusters, n_features]

    labels : array [n_samples]
        cluster labels for each point

    Notes:
    =====
    See examples/plot_meanshift.py for an example.

    K. Funkunaga and L.D. Hosteler, "The Estimation of the Gradient of a
    Density Function, with Applications in Pattern Recognition"

    """

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
    """MeanShift clustering"""

    def __init__(self, bandwidth):
        self.bandwidth = bandwidth

    def fit(self, X, **params):
        """compute MeanShift"""
        self._set_params(**params)
        self.cluster_centers, self.labels = mean_shift(X, self.bandwidth)
        return self


################################################################################
# Affinity Propagation
################################################################################

def affinity_propagation(S, p=None, convit=30, maxit=200, damping=0.5,
            copy=True):
    """Perform Affinity Propagation Clustering of data

    Parameters
    ===========

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
    ========

    cluster_centers_indices: array [n_clusters]
        index of clusters centers

    labels : array [n_points]
        cluster labels for each point

    Notes
    =====
    See examples/plot_affinity_propagation.py for an example.

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
    """Affinity Propagation clustering"""

    def __init__(self, damping=.5):
        self.damping = damping

    def fit(self, S, p=None, maxit=200, convit=30, **params):
        """compute MeanShift"""
        self._set_params(**params)
        self.cluster_centers_indices, self.labels = affinity_propagation(S, p,
                maxit=maxit, convit=convit, damping=self.damping)
        return self

import numpy as np
from . import _liblinear


class LogisticRegression(object):
    """
    Logistic Regression.

    Implements L1 and L2 regularized logistic regression.

    Parameters
    ----------
    X : array-like, shape = [nsamples, nfeatures]
        Training vector, where nsamples in the number of samples and
        nfeatures is the number of features.
    Y : array, shape = [nsamples]
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

    `coef_` : array, shape = [nclasses-1, nfeatures]
        Coefficient of the features in the decision function.

    `intercept_` : array, shape = [nclasses-1]
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
    def __init__(self, penalty='l2', eps=1e-4, C=1.0, intercept=True):
        self.solver_type = self._penalties[penalty.lower()]
        self.eps = eps
        self.C = C
        if intercept:
            self.bias_ = 1.0
        else:
            self.bias_ = -1.0

    _penalties = {'l2': 0, 'l1' : 6}
    _weight_label = np.empty(0, dtype=np.int32)
    _weight = np.empty(0, dtype=np.float64)

    def fit(self, X, Y):
        X = np.asanyarray(X, dtype=np.float64, order='C')
        Y = np.asanyarray(Y, dtype=np.int32, order='C')
        self.raw_coef_, self.label_, self.bias_ = _liblinear.train_wrap(X,
                                          Y, self.solver_type, self.eps, self.bias_,
                                          self.C,
                                          self._weight_label,
                                          self._weight)
        return self

    def predict(self, T):
        T = np.asanyarray(T, dtype=np.float64, order='C')
        return _liblinear.predict_wrap(T, self.raw_coef_, self.solver_type,
                                      self.eps, self.C,
                                      self._weight_label,
                                      self._weight, self.label_,
                                      self.bias_)

    def predict_proba(self, T):
        T = np.asanyarray(T, dtype=np.float64, order='C')
        return _liblinear.predict_prob_wrap(T, self.raw_coef_, self.solver_type,
                                      self.eps, self.C,
                                      self._weight_label,
                                      self._weight, self.label_,
                                      self.bias_)

    @property
    def intercept_(self):
        if self.bias_ > 0:
            return self.raw_coef_[:,-1]
        return 0.0

    @property
    def coef_(self):
        if self.bias_ > 0:
            return self.raw_coef_[:,:-1]
        return self.raw_coef_


"""
k-Nearest Neighbor Algorithm.

Uses BallTree algorithm, which is an efficient way to perform fast
neighbor searches in high dimensionality.
"""
import numpy as np
from scipy import stats

from .base import BaseEstimator
from .ball_tree import BallTree

class Neighbors(BaseEstimator):
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
  Neighbors(k=3,
            window_size=1)
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
    Neighbors(k=1,
              window_size=1)
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
    Neighbors(k=1,
              window_size=1)
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

"""Recursive feature elimination
for feature ranking
"""

import numpy as np
from .base import BaseEstimator
# from base import BaseEstimator

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
    `support_` : array-like, shape = [nfeatures]
        Mask of estimated support

    `ranking_` : array-like, shape = [nfeatures]
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
        X : array-like, shape = [nsamples, nfeatures]
            Training vector, where nsamples in the number of samples and
            nfeatures is the number of features.
        y : array, shape = [nsamples]
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
        X : array-like, shape = [nsamples, nfeatures]
            Vector, where nsamples in the number of samples and
            nfeatures is the number of features.
        """
        X_r = X[:,self.support_]
        return X_r.copy() if copy else X_r

if __name__ == '__main__':
    from scikits.learn.svm import SVC
    from scikits.learn import datasets
    iris = datasets.load_iris()

    # Add the noisy data to the informative features
    X = iris.data
    y = iris.target

    svc = SVC(kernel='linear')
    rfe = RFE(estimator=svc, n_features=2, percentage=0.1)
    rfe.fit(X, y)
    print rfe.support_

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

import cross_val
import ball_tree
import gmm
import glm
import logistic
import lda
import metrics
import svm
import features

__all__ = ['cross_val', 'ball_tree', 'gmm', 'glm', 'logistic', 'lda',
           'metrics', 'svm', 'features']

__version__ = '0.5-git'


import string

import numpy as np

from gmm import *

class HMMTrainer(object):
    """Base class for HMM training algorithms."""

    @property
    def emission_type(self):
        pass

    def train(self, hmm, obs, niter=10, thresh=1e-2, params=string.letters,
              maxrank=None, beamlogprob=-np.Inf, **kwargs):
        """Estimate model parameters.

        Parameters
        ----------
        hmm : HMM object
            HMM to train.
        obs : list
            List of array-like observation sequences (shape (n_i, ndim)).
        niter : int
            Number of iterations to perform.
        thresh : float
            Convergence threshold.
        params : string
            Controls which parameters are updated in the training
            process.  Can contain any combination of 's' for startprob,
            't' for transmat, 'm' for means, and 'c' for covars, etc.
            Defaults to all parameters.
        maxrank : int
            Maximum rank to evaluate for rank pruning.  If not None,
            only consider the top `maxrank` states in the inner
            sum of the forward algorithm recursion.  Defaults to None
            (no rank pruning).  See "The HTK Book" for more details.
        beamlogprob : float
            Width of the beam-pruning beam in log-probability units.
            Defaults to -numpy.Inf (no beam pruning).  See The HTK
            Book for more details.

        Returns
        -------
        logprob : list
            Log probabilities of the training data after each iteration.

        Notes
        -----
        In general, `logprob` should be non-decreasing unless
        aggressive pruning is used.  Decreasing `logprob` is generally
        a sign of overfitting (e.g. a covariance parameter getting too
        small).  You can fix this by using a different trainer
        (e.g. based on model adaptation), getting more training data,
        or decreasing `covarprior`.
        """
        logprob = []
        for i in xrange(niter):
            # Expectation step
            stats = self._initialize_sufficient_statistics(hmm)
            curr_logprob = 0
            for seq in obs:
                framelogprob = hmm._compute_log_likelihood(seq)
                lpr, fwdlattice = hmm._do_forward_pass(framelogprob, maxrank,
                                                       beamlogprob)
                bwdlattice = hmm._do_backward_pass(framelogprob, fwdlattice,
                                                   maxrank, beamlogprob)
                gamma = fwdlattice + bwdlattice
                posteriors = np.exp(gamma.T - logsum(gamma, axis=1)).T
                curr_logprob += lpr
                self._accumulate_sufficient_statistics(hmm, stats, seq,
                                                       framelogprob, posteriors,
                                                       fwdlattice, bwdlattice,
                                                       params)
            logprob.append(curr_logprob)

            # Check for convergence.
            if i > 0 and abs(logprob[-1] - logprob[-2]) < thresh:
                break

            # Maximization step
            self._do_mstep(hmm, stats, params, **kwargs)

        return logprob

    def _initialize_sufficient_statistics(self, hmm):
        pass

    def _accumulate_sufficient_statistics(self, hmm, stats, seq, framelogprob, 
                                          posteriors, fwdlattice,
                                          bwdlattice, params):
        pass
    
    def _do_mstep(self, hmm, stats, params, **kwargs):
        pass


class BaseHMMBaumWelchTrainer(HMMTrainer):
    """Base class for HMM trainers.

    Uses the Baum-Welch algorithm to train the startprob and transmat
    parameters.
    """
    emission_type = None

    def _initialize_sufficient_statistics(self, hmm):
        stats = {'nobs':  0,
                 'start': np.zeros(hmm._nstates),
                 'trans': np.zeros((hmm._nstates, hmm._nstates))}
        return stats

    def _accumulate_sufficient_statistics(self, hmm, stats, seq, framelogprob, 
                                          posteriors, fwdlattice, bwdlattice,
                                          params):
        stats['nobs'] += 1
        if 's' in params:
            stats['start'] += posteriors[0]
        if 't' in params:
            for t in xrange(len(framelogprob)):
                zeta = (fwdlattice[t-1][:,np.newaxis] + hmm._log_transmat
                        + framelogprob[t] + bwdlattice[t])
                stats['trans'] += np.exp(zeta - logsum(zeta))

    def _do_mstep(self, hmm, stats, params, **kwargs):
        if 's' in params:
            hmm.startprob = stats['start'] / stats['start'].sum()
        if 't' in params:
            hmm.transmat = normalize(stats['trans'], axis=1)


class GaussianHMMBaumWelchTrainer(BaseHMMBaumWelchTrainer):
    """Baum-Welch maximum likelihood trainer for HMMs with Gaussian emissions."""
    emission_type = 'gaussian'

    def _initialize_sufficient_statistics(self, hmm):
        stats = super(GaussianHMMBaumWelchTrainer,
                      self)._initialize_sufficient_statistics(hmm)
        stats['post']      = np.zeros(hmm._nstates)
        stats['obs']       = np.zeros((hmm._nstates, hmm._ndim))
        stats['obs**2']    = np.zeros((hmm._nstates, hmm._ndim))
        stats['obs*obs.T'] = np.zeros((hmm._nstates, hmm._ndim, hmm._ndim))
        return stats

    def _accumulate_sufficient_statistics(self, hmm, stats, obs, framelogprob,
                                          posteriors, fwdlattice, bwdlattice,
                                          params):
        super(GaussianHMMBaumWelchTrainer,
              self)._accumulate_sufficient_statistics(hmm, stats, obs,
                                                      framelogprob, posteriors,
                                                      fwdlattice, bwdlattice,
                                                      params)

        if 'm' in params or 'c' in params:
            stats['post'] += posteriors.sum(axis=0)
            stats['obs'] += np.dot(posteriors.T, obs)

        if 'c' in params:
            if hmm._cvtype in ('spherical', 'diag'):
                stats['obs**2'] += np.dot(posteriors.T, obs**2)
            elif hmm._cvtype in ('tied', 'full'):  
                for t, o in enumerate(obs):
                    obsobsT = np.outer(o, o)
                    for c in xrange(hmm._nstates):
                        stats['obs*obs.T'][c] += posteriors[t,c] * obsobsT
                  
    def _do_mstep(self, hmm, stats, params, covarprior=1e-2, **kwargs):
        super(GaussianHMMBaumWelchTrainer, self)._do_mstep(hmm, stats, params)

        denom = stats['post'][:,np.newaxis]
        if 'm' in params:
            hmm._means = stats['obs'] / denom

        if 'c' in params:
            if hmm._cvtype in ('spherical', 'diag'):
                cv = ((stats['obs**2']
                       - 2 * hmm._means * stats['obs']
                       + hmm._means**2 * denom
                       + covarprior)
                      / (1.0 + denom))
                if hmm._cvtype == 'spherical':
                    hmm._covars = cv.mean(axis=1)
                elif hmm._cvtype == 'diag':
                    hmm._covars = cv
            elif hmm._cvtype in ('tied', 'full'):
                cvnum = np.empty((hmm._nstates, hmm._ndim, hmm._ndim))
                cvprior = np.eye(hmm._ndim) * covarprior
                for c in xrange(hmm._nstates):
                    cvnum[c] = (stats['obs*obs.T'][c]
                                - 2 * np.outer(stats['obs'][c], hmm._means[c])
                                + np.outer(hmm._means[c] * stats['post'][c],
                                           hmm._means[c]))
                if hmm._cvtype == 'tied':
                    hmm._covars = ((cvnum.sum(0) + cvprior)
                                   / (1.0 + stats['post'].sum(0)))
                elif hmm._cvtype == 'full':
                    hmm._covars = ((cvnum + cvprior)
                                   / (1.0 + stats['post'][:,np.newaxis,np.newaxis]))


class GaussianHMMMAPTrainer(GaussianHMMBaumWelchTrainer):
    """HMM trainer based on maximum-a-posteriori (MAP) adaptation.
    """
    emission_type = 'gaussian'

    def __init__(self, startprob_prior=None, transmat_prior=None,
                 means_prior=None, means_weight=0,
                 covars_prior=None, covars_weight=0):
        """Initialize MAP trainer with the parameters for the prior
        distribution.
        """
        self.startprob_prior = startprob_prior
        self.transmat_prior = transmat_prior
        self.means_prior = means_prior
        self.means_weight = means_weight
        self.covars_prior = covars_prior
        self.covars_weight = covars_weight

    def _do_mstep(self, hmm, stats, params, **kwargs):
        # Based on Huang, Acero, Hon, "Spoken Language Processing", p. 443 - 445
        if 's' in params:
            prior = self.startprob_prior
            if prior is None:
                prior = 1.0
            hmm.startprob = normalize(np.maximum(prior - 1.0 + stats['start'],
                                                 1e-20))

        if 't' in params:
            prior = self.transmat_prior
            if prior is None:
                prior = 1.0
            hmm.transmat = normalize(np.maximum(prior - 1.0 + stats['trans'],
                                                1e-20), axis=1)

        denom = stats['post'][:,np.newaxis]
        if 'm' in params:
            prior = self.means_prior
            weight = self.means_weight
            if prior is None:
                weight = 0
                prior = 0
            hmm._means = (weight * prior + stats['obs']) / (weight + denom)

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
            meandiff = hmm._means - means_prior

            if hmm._cvtype in ('spherical', 'diag'):
                cv_num = (means_weight * (meandiff)**2
                          + stats['obs**2']
                          - 2 * hmm._means * stats['obs']
                          + hmm._means**2 * denom)
                cv_den = max(covars_weight - 1, 0) + denom
                if hmm._cvtype == 'spherical':
                    hmm._covars = (covars_prior / cv_den.mean(axis=1)
                                   + np.mean(cv_num / cv_den, axis=1))
                elif hmm._cvtype == 'diag':
                    hmm._covars = (covars_prior + cv_num) / cv_den
            elif hmm._cvtype in ('tied', 'full'):
                cvnum = np.empty((hmm._nstates, hmm._ndim, hmm._ndim))
                for c in xrange(hmm._nstates):
                    cvnum[c] = (means_weight * np.outer(meandiff[c], meandiff[c])
                                + stats['obs*obs.T'][c] 
                                - 2 * np.outer(stats['obs'][c], hmm._means[c])
                                + np.outer(hmm._means[c], hmm._means[c])
                                * stats['post'][c])
                cvweight = max(covars_weight - hmm._ndim, 0)
                if hmm._cvtype == 'tied':
                    hmm._covars = ((covars_prior + cvnum.sum(axis=0))
                                    / (cvweight + stats['post'].sum()))
                elif hmm._cvtype == 'full':
                    hmm._covars = ((covars_prior + cvnum)
                                   / (cvweight + stats['post'][:,None,None]))

 

class MultinomialHMMBaumWelchTrainer(BaseHMMBaumWelchTrainer):
    "Baum-Welch maximum likelihood trainer for HMM with multinomial emissions."
    emission_type = 'multinomial'

    def _initialize_sufficient_statistics(self, hmm):
        stats = super(MultinomialHMMBaumWelchTrainer,
                      self)._initialize_sufficient_statistics(hmm)
        stats['obs']  = np.zeros((hmm._nstates, hmm._nsymbols))
        return stats

    def _accumulate_sufficient_statistics(self, hmm, stats, obs, framelogprob,
                                          posteriors, fwdlattice, bwdlattice,
                                          params):
        super(MultinomialHMMBaumWelchTrainer,
              self)._accumulate_sufficient_statistics(hmm, stats, obs,
                                                      framelogprob, posteriors,
                                                      fwdlattice, bwdlattice,
                                                      params)
        if 'e' in params:
            for t,symbol in enumerate(obs):
                stats['obs'][:,symbol] += posteriors[t,:]
                  
    def _do_mstep(self, hmm, stats, params, covarprior=1e-2, **kwargs):
        super(MultinomialHMMBaumWelchTrainer, self)._do_mstep(hmm, stats,
                                                              params)

        if 'e' in params:
            hmm.emissionprob = stats['obs'] / stats['obs'].sum(1)[:,np.newaxis]


class GMMHMMBaumWelchTrainer(BaseHMMBaumWelchTrainer):
    "Baum-Welch maximum likelihood trainer for HMM with GMM emissions."
    emission_type = 'gmm'

    def _initialize_sufficient_statistics(self, hmm):
        stats = super(GMMHMMBaumWelchTrainer,
                      self)._initialize_sufficient_statistics(hmm)
        stats['norm'] = [np.zeros(g.weights.shape) for g in hmm.gmms]
        stats['means'] = [np.zeros(np.shape(g.means)) for g in hmm.gmms]
        stats['covars'] = [np.zeros(np.shape(g._covars)) for g in hmm.gmms]
        return stats

    def _accumulate_sufficient_statistics(self, hmm, stats, obs, framelogprob,
                                          posteriors, fwdlattice, bwdlattice,
                                          params):
        super(GMMHMMBaumWelchTrainer,
              self)._accumulate_sufficient_statistics(hmm, stats, obs,
                                                      framelogprob, posteriors,
                                                      fwdlattice, bwdlattice,
                                                      params)
        for state,g in enumerate(hmm.gmms):
            gmm_logprob, gmm_posteriors = g.eval(obs)
            gmm_posteriors *= posteriors[:,state][:,np.newaxis]
            tmpgmm = GMM(g.nstates, g.ndim, cvtype=g.cvtype)
            norm = tmpgmm._do_mstep(obs, gmm_posteriors, params, min_covar=0)

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
                  
    def _do_mstep(self, hmm, stats, params, covarprior=1e-2, **kwargs):
        super(GMMHMMBaumWelchTrainer, self)._do_mstep(hmm, stats, params)
        # All we have left to do is apply covarprior to the parameters
        # we updated in _accumulate_sufficient_statistics.
        for state,g in enumerate(hmm.gmms):
            norm = stats['norm'][state]
            #print norm
            if 'w' in params:
                g.weights = normalize(norm) 
            if 'm' in params:
                g.means = stats['means'][state] / norm[:,np.newaxis]
            if 'c' in params:
                if g.cvtype == 'tied':
                    g.covars = (stats['covars'][state]
                                + covarprior * np.eye(g.ndim)) / norm.sum()
                else:
                    cvnorm = np.copy(norm)
                    shape = np.ones(g._covars.ndim)
                    shape[0] = np.shape(g._covars)[0]
                    cvnorm.shape = shape
                    if g.cvtype == 'spherical' or g.cvtype == 'diag':
                        g.covars = (stats['covars'][state]
                                    + covarprior) / cvnorm
                    elif g.cvtype == 'full':
                        g.covars = ((stats['covars'][state]
                                     + covarprior*np.eye(g.ndim)[np.newaxis,:,:])
                                    / cvnorm)
        

# Author: Vincent Michel <vincent.michel@inria.fr>
# License: BSD Style.
import numpy as np

class GNB(object):
    """
    Gaussian Naive Bayes (GNB)

    Parameters
    ----------
    X : array-like, shape = [nsamples, nfeatures]
        Training vector, where nsamples in the number of samples and
        nfeatures is the number of features.
    y : array, shape = [nsamples]
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
    >>> clf.fit(X, Y)    #doctest: +ELLIPSIS
    <scikits.learn.naive_bayes.GNB object at 0x...>
    >>> print clf.predict([[-0.8, -1]])
    [1]

    See also
    --------

    """

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

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    from numpy.distutils.system_info import get_info, get_standard_file, BlasNotFoundError
    config = Configuration('learn',parent_package,top_path)

    site_cfg  = ConfigParser()
    site_cfg.read(get_standard_file('site.cfg'))

    config.add_subpackage('datasets')
    config.add_subpackage('features')
    config.add_subpackage('feature_selection')
    config.add_subpackage('utils')

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
                                  join('src', 'libsvm', 'libsvm_helper.c')]
                                  )

    ### liblinear module
    blas_sources = [join('src', 'blas', 'daxpy.c'),
                    join('src', 'blas', 'ddot.c'),
                    join('src', 'blas', 'dnrm2.c'),
                    join('src', 'blas', 'dscal.c')]

    liblinear_sources = [join('src', 'linear.cpp'),
                         join('src', '_liblinear.c'),
                         join('src', 'tron.cpp')]

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
                         depends=[join('src', 'linear.h'),
                                  join('src', 'tron.h'),
                                  join('src', 'blas', 'blas.h'),
                                  join('src', 'blas', 'blasp.h')],
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

    config.add_extension('cd_fast',
                         sources=[join('src', 'cd_fast.c')],
                         libraries=cblas_libs,
                         include_dirs=[join('src', 'cblas'),
                                       numpy.get_include(),
                                       blas_info.pop('include_dirs', [])],
                         extra_compile_args=['-std=c99'] + \
                                             blas_info.pop('extra_compile_args', []),
                         **blas_info
                         )


    config.add_subpackage('utils')

    # add the test directory
    config.add_data_dir('tests')

    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())

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
    >>> from scikits.learn.feature_selection.univariate_selection import UnivariateFilter,SelectKBest,f_regression
    >>> from scikits.learn.pipeline import Pipeline

    >>> # import some data to play with
    >>> X,y = samples_generator.test_dataset_classif(k=5)

    >>> # ANOVA SVM-C
    >>> anova_filter = UnivariateFilter(SelectKBest(k=5), f_regression)
    >>> clf = svm.SVC(kernel='linear')
    
    >>> anova_svm = Pipeline([anova_filter],clf)
    >>> anova_svm.fit(X,y)
    >>> anova_svm.predict(X)
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

    def fit(self, X, y):
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
        

import numpy as np

from joblib import Parallel, delayed

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


def iter_grid(**kwargs):
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
        >>> list(iter_grid(a=[1, 2], b=[True, False]))
        [{'a': 1, 'b': True}, {'a': 1, 'b': False}, {'a': 2, 'b': True}, {'a': 2, 'b': False}]
    """
    keys = kwargs.keys()
    for v in product(*kwargs.values()):
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
    y_pred = list()
    y_true = list()
    for train, test in cv:
        clf.fit(X[train], y[train], **fit_params)
        y_pred.append(clf.predict(X[test]))
        y_true.append(y[test])

    y_true = np.concatenate(y_true)
    y_pred = np.concatenate(y_pred)

    score = loss_func(y_true, y_pred)
    return clf, score


class GridSearchCV(object):
    """
    Object to run a grid search on the parameters of a classifier.

    Important memmbers are fit, predict.

    GridSearchCV implements a "fit" method and a "predict" method like
    any classifier except that the parameters of the classifier
    used to predict is optimized by cross-validation

    Parameters
    ---------
    estimator: object type that implements the "fit" and "predict" methods
        A object of that type is instanciated for each grid point

    param_grid: dict
        a dictionary of parameters that are used the generate the grid

    cross_val_factory : a generator to run crossvalidation

    loss_func : function that takes 2 arguments and compares them in
        order to evaluate the performance of prediciton (small is good)

    n_jobs : int
        number of jobs to run in parallel (default 1)

    Optional Parameters
    -------------------

    Members
    -------

    Examples
    --------
    >>> import numpy as np
    >>> from scikits.learn.cross_val import LeaveOneOut
    >>> from scikits.learn.svm import SVC
    >>> X = np.array([[-1, -1], [-2, -1], [1, 1], [2, 1]])
    >>> y = np.array([1, 1, 2, 2])
    >>> parameters = {'kernel':('linear', 'rbf'), 'C':[1, 10]}
    >>> def loss_func(y1, y2):
    ...     return np.mean(y1 != y2)
    >>> svc = SVC()
    >>> clf = GridSearchCV(svc, parameters, loss_func, n_jobs=1)
    >>> print clf.fit(X, y).predict([[-0.8, -1]])
    [ 1.]
    """
    # XXX: cross_val_factory should have a default
    def __init__(self, estimator, param_grid, loss_func,
                        fit_params={}, n_jobs=1):
        assert hasattr(estimator, 'fit') and hasattr(estimator, 'predict'), (
            "estimator should a be an estimator implementing 'fit' and "
            "'predict' methods, %s (type %s) was passed" % (clf, type(clf))
            )
        self.estimator = estimator
        self.param_grid = param_grid
        self.loss_func = loss_func
        self.n_jobs = n_jobs
        self.fit_params = fit_params


    def fit(self, X, y, cv=None, **kw):
        """Run fit with all sets of parameters
        Returns the best classifier
        """

        if cv is None:
            n_samples = y.size
            from scikits.learn.cross_val import KFold
            cv = KFold(n_samples, 2)

        grid = iter_grid(**self.param_grid)
        klass = self.estimator.__class__
        orignal_params = self.estimator._get_params()
        out = Parallel(n_jobs=self.n_jobs)(
            delayed(fit_grid_point)(X, y, klass, orignal_params, clf_params,
                    cv, self.loss_func, **self.fit_params) 
                    for clf_params in grid)

        # Out is a list of pairs: estimator, score
        key = lambda pair: pair[1]
        best_estimator = min(out, key=key)[0]

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
    def loss_func(y1, y2):
        return np.mean(y1 != y2)
    clf = GridSearchCV(svc, {'C':[1, 10]}, loss_func, n_jobs=2)
    print clf.fit(X, y).predict([[-0.8, -1]])

"""
Utilities for cross validation.
"""

# Author: Alexandre Gramfort <alexandre.gramfort@inria.fr>,
#         Gael Varoquaux    <gael.varoquaux@normalesup.org>
# License: BSD Style.

from math import ceil
import numpy as np

from .utils.extmath import factorial, combinations
from .grid_search import GridSearchCV

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
import _libsvm
import _liblinear

from .base import BaseEstimator

class BaseLibsvm(BaseEstimator):
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
        self.shrinking = int(shrinking)
        self.probability = int(probability)

        # container for when we call fit
        self.support_   = np.empty((0,0), dtype=np.float64, order='C')
        self.dual_coef_ = np.empty((0,0), dtype=np.float64, order='C')
        self.intercept_ = np.empty(0,     dtype=np.float64, order='C')

        # only used in classification
        self.nSV_ = np.empty(0, dtype=np.int32, order='C')


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
        X : array-like, shape = [nsamples, nfeatures]
            Training vector, where nsamples in the number of samples and
            nfeatures is the number of features.
        Y : array, shape = [nsamples]
            Target values (integers in classification, real numbers in
            regression)
        weight : dict , {class_label : weight}
            Weights associated with classes. If not given, all classes
            are supposed to have weight one.
        """
        X = np.asanyarray(X, dtype=np.float64, order='C')
        Y = np.asanyarray(Y, dtype=np.float64, order='C')

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
                 self.shrinking,
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
        T : array-like, shape = [nsamples, nfeatures]

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
                      self.shrinking, self.probability,
                      self.nSV_, self.label_, self.probA_,
                      self.probB_)


    def predict_proba(self, T):
        """
        This function does classification or regression on a test vector T
        given a model with probability information.

        Parameters
        ----------
        T : array-like, shape = [nsamples, nfeatures]

        Returns
        -------
        T : array-like, shape = [nsamples, nclasses]
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
                      self.p, self.shrinking, self.probability,
                      self.nSV_, self.label_,
                      self.probA_, self.probB_)
        return pprob[:, np.argsort(self.label_)]
        

    def predict_margin(self, T):
        """
        Calculate the distance of the samples in T to the separating hyperplane.

        Parameters
        ----------
        T : array-like, shape = [nsamples, nfeatures]
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
                      self.p, self.shrinking, self.probability,
                      self.nSV_, self.label_,
                      self.probA_, self.probB_)



    @property
    def coef_(self):
        if self.kernel != 'linear':
            raise NotImplementedError('coef_ is only available when using a linear kernel')
        return np.dot(self.dual_coef_, self.support_)


###
# Public API
# No processing should go into these classes

class SVC(BaseLibsvm):
    """
    Classification using Support Vector Machines.

    This class implements the most common classification methods
    (C-SVC, Nu-SVC) using support vector machines.

    Parameters
    ----------
    impl : string, optional
        SVM implementation to choose from. This refers to different
        formulations of the SVM optimization problem.
        Can be one of 'c_svc', 'nu_svc'. By default 'c_svc' will be chosen.

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
    `support_` : array-like, shape = [nSV, nfeatures]
        Support vectors.

    `dual_coef_` : array, shape = [nclasses-1, nSV]
        Coefficients of the support vector in the decision function.

    `coef_` : array, shape = [nclasses-1, nfeatures]
        Weights asigned to the features (coefficients in the primal
        problem). This is only available in the case of linear kernel.

    `intercept_` : array, shape = [nclasses-1]
        Constants in decision function.


    Methods
    -------
    fit(X, Y) : self
        Fit the model

    predict(X) : array
        Predict using the model.

    predict_proba(X) : array
        Return probability estimates.

    Examples
    --------
    >>> X = np.array([[-1, -1], [-2, -1], [1, 1], [2, 1]])
    >>> Y = np.array([1, 1, 2, 2])
    >>> clf = SVC()
    >>> clf.fit(X, Y)
    SVC(kernel=rbf,
        C=1.0,
        probability=0,
        degree=3,
        shrinking=1,
        eps=0.001,
        p=0.1,
        impl=c_svc,
        cache_size=100.0,
        coef0=0.0,
        nu=0.5,
        gamma=0.25)
    >>> print clf.predict([[-0.8, -1]])
    [ 1.]

    See also
    --------
    SVR
    """

    def __init__(self, impl='c_svc', kernel='rbf', degree=3, gamma=0.0,
                 coef0=0.0,cache_size=100.0, eps=1e-3, C=1.0,nu=0.5, p=0.1,
                 shrinking=True, probability=False):

        BaseLibsvm.__init__(self, impl, kernel, degree, gamma, coef0,
                         cache_size, eps, C, nu, p,
                         shrinking, probability)



class SVR(BaseLibsvm):
    """
    Support Vector Regression.

    Parameters
    ----------
    impl : string, optional

        SVM implementation to choose from. This refers to different formulations
        of the SVM optimization problem. Can be one of 'epsilon_svr', 'nu_svr'.
        By default 'epsilon_svc' will be chosen.

    nu : float, optional
        An upper bound on the fraction of training errors and a lower bound of
        the fraction of support vectors. Should be in the interval (0, 1].  By
        default 0.5 will be taken.  Only available if impl='nu_svc'

    kernel : string, optional
         Specifies the kernel type to be used in the algorithm.
         one of 'linear', 'poly', 'rbf', 'sigmoid', 'precomputed'.
         If none is given 'rbf' will be used.

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
    `support_` : array-like, shape = [nSV, nfeatures]
        Support vectors

    `dual_coef_` : array, shape = [nclasses-1, nSV]
        Coefficients of the support vector in the decision function.

    `coef_` : array, shape = [nclasses-1, nfeatures]
        Weights asigned to the features (coefficients in the primal
        problem). This is only available in the case of linear kernel.

    `intercept_` : array, shape = [nclasses-1]
        constants in decision function

    Methods
    -------
    fit(X, Y) : self
        Fit the model

    predict(X) : array
        Predict using the model.

    predict_proba(X) : array
        Return probability estimates.

    See also
    --------
    SVC
    """
    def __init__(self, kernel='rbf', degree=3, gamma=0.0, coef0=0.0,
                 cache_size=100.0, eps=1e-3, C=1.0, nu=0.5, p=0.1,
                 shrinking=True, probability=False):

        BaseLibsvm.__init__(self, 'epsilon_svr', kernel, degree, gamma, coef0,
                         cache_size, eps, C, nu, p,
                         shrinking, probability)


class OneClassSVM(BaseLibsvm):
    """
    Outlayer detection

    Parameters
    ----------

    kernel : string, optional
         Specifies the kernel type to be used in the algorithm. one of 'linear',
         'poly', 'rbf', 'sigmoid', 'precomputed'. If none is given 'rbf' will be
         used.

    nu : float, optional
        An upper bound on the fraction of training errors and a lower bound of
        the fraction of support vectors. Should be in the interval (0, 1].  By
        default 0.5 will be taken.  Only available if impl='nu_svc'

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
    `support_` : array-like, shape = [nSV, nfeatures]
        Support vectors


    `dual_coef_` : array, shape = [nclasses-1, nSV]
        Coefficient of the support vector in the decision function.

    `coef_` : array, shape = [nclasses-1, nfeatures]
        Weights asigned to the features (coefficients in the primal
        problem). This is only available in the case of linear kernel.
    
    `intercept_` : array, shape = [nclasses-1]
        constants in decision function

    Methods
    -------
    fit(X, Y) : self
        Fit the model

    predict(X) : array
        Predict using the model.

    predict_proba(X) : array
        Return probability estimates.

    """
    def __init__(self, kernel='rbf', degree=3, gamma=0.0, coef0=0.0,
                 cache_size=100.0, eps=1e-3, C=1.0, 
                 nu=0.5, p=0.1, shrinking=True, probability=False):
        BaseLibsvm.__init__(self, 'one_class', kernel, degree, gamma, coef0,
                         cache_size, eps, C, nu, p,
                         shrinking, probability)


class LinearSVC(BaseEstimator):
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
    `support_` : array-like, shape = [nSV, nfeatures]
        Support vectors

    `dual_coef_` : array, shape = [nclasses-1, nSV]
        Coefficient of the support vector in the decision function,
        where nclasses is the number of classes and nSV is the number
        of support vectors.

    `coef_` : array, shape = [nclasses-1, nfeatures]
        Wiehgiths asigned to the features (coefficients in the primal
        problem). This is only available in the case of linear kernel.

    `intercept_` : array, shape = [nclasses-1]
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

    _solver_type_dict = {
        'PL2_LL2_D1' : 1, # L2 penalty, L2 loss, dual problem
        'PL2_LL2_D0' : 2, # L2 penalty, L2 loss, primal problem
        'PL2_LL1_D1' : 3, # L2 penalty, L1 Loss, dual problem
        'PL1_LL2_D0' : 5, # L2 penalty, L1 Loss, primal problem
        }

    def __init__(self, penalty='l2', loss='l2', dual=True, eps=1e-4, C=1.0):
        self.penalty = penalty
        self.loss = loss
        self.dual = dual
        self.eps = eps
        self.C = C
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
        ==========
        X : array-like, shape = [nsamples, nfeatures]
            Training vector, where nsamples in the number of samples and
            nfeatures is the number of features.
        Y : array, shape = [nsamples]
            Target vector relative to X
        """
        self._set_params(**params)
        
        X = np.asanyarray(X, dtype=np.float64, order='C')
        Y = np.asanyarray(Y, dtype=np.int32, order='C')
        self.raw_coef, self.label_, self.bias_ = \
                       _liblinear.train_wrap(X, Y,
                       self._get_solver_type(),
                       self.eps, 1.0, self.C, self._weight_label,
                       self._weight)
        return self

    def predict(self, T):
        T = np.atleast_2d(np.asanyarray(T, dtype=np.float64, order='C'))
        return _liblinear.predict_wrap(T, self.raw_coef, 
                                      self._get_solver_type(),
                                      self.eps, self.C,
                                      self._weight_label,
                                      self._weight, self.label_,
                                      self.bias_)

    def predict_proba(self, T):
        raise NotImplementedError(
                'liblinear does not provide this functionality')

    @property
    def intercept_(self):
        if self.bias_ > 0:
            return self.raw_coef[:,-1]
        return 0.0

    @property
    def coef_(self):
        if self.bias_ > 0:
            return self.raw_coef[:,:-1]
        return self.raw_coef_


"""
Base class for all estimators.

"""
# Author: Gael Varoquaux <gael.varoquaux@normalesup.org>

# License: BSD Style
import inspect

import numpy as np


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
        args, varargs, kw, default = inspect.getargspec(cls.__init__)
        assert varargs is None, (
            'scikit learn estimators should always specify their '
            'parameters in the signature of their init (no varargs).'
            )
        # Remove 'self'
        # XXX: This is going to fail if the init is a staticmethod, but
        # who would do this?
        args.pop(0)
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
        params_str = (',\n' + (1+len(class_name))*' ').join(
                                  '%s=%s' % (k, v) 
                                  for k, v in self._get_params().iteritems())
        np.set_printoptions(**options)
        return '%s(%s)' % (
                class_name,
                params_str
            )


# Hidden Markov Models
#
# Author: Ron Weiss <ronweiss@gmail.com>

import functools
import itertools
import string

import numpy as np
import scipy as sp
import scipy.cluster

import gmm
from gmm import *
from gmm import _distribute_covar_matrix_to_match_cvtype #, _validate_covars
import hmm_trainers

ZEROLOGPROB = -1e200

def HMM(emission_type='gaussian', *args, **kwargs):
    """Create an HMM object with the given emission_type."""
    supported_emission_types = dict([(str(x.emission_type).lower(), x)
                                     for x in _BaseHMM.__subclasses__()])
    emission_type = str(emission_type).lower()
    if emission_type in supported_emission_types.keys():
        return supported_emission_types[emission_type](*args, **kwargs)
    else:
        raise ValueError('Unknown emission_type')

class _BaseHMM(object):
    """Hidden Markov Model base class.
    
    Representation of a hidden Markov model probability distribution.
    This class allows for easy evaluation of, sampling from, and
    maximum-likelihood estimation of the parameters of a HMM.

    See the instance documentation for details specific to a
    particular object.

    Attributes
    ----------
    nstates : int (read-only)
        Number of states in the model.
    transmat : array, shape (`nstates`, `nstates`)
        Matrix of transition probabilities between states.
    startprob : array, shape ('nstates`,)
        Initial state occupation distribution.
    labels : list, len `nstates`
        Optional labels for each state.

    Methods
    -------
    eval(obs)
        Compute the log likelihood of `obs` under the HMM.
    decode(obs)
        Find most likely state sequence for each point in `obs` using the
        Viterbi algorithm.
    rvs(n=1)
        Generate `n` samples from the HMM.
    fit(obs)
        Estimate HMM parameters from `obs`.
    predict(obs)
        Like decode, find most likely state sequence corresponding to `obs`.

    See Also
    --------
    GMM : Gaussian mixture model
    """

    # This class implements the public interface to all HMMs that
    # derive from it, including all of the machinery for the
    # forward-backward and Viterbi algorithms.  Subclasses need only
    # implement emission_type, and methods
    # _generate_sample_from_state(), _compute_log_likelihood(),
    # _init(), and a corresponding HMMTrainer instance, all of which
    # depend on the specific emission distribution.
    #
    # Subclasses will probably also want to implement properties for
    # the emission distribution parameters to expose them publically.

    @property
    def emission_type(self):
        """String identifier for the emission distribution used by this HMM"""
        return None

    def __init__(self, nstates, startprob=None, transmat=None, labels=None,
                 trainer=hmm_trainers.BaseHMMBaumWelchTrainer()):
        self._nstates = nstates

        if startprob is None:
            startprob = np.tile(1.0 / nstates, nstates)
        self.startprob = startprob

        if transmat is None:
            transmat = np.tile(1.0 / nstates, (nstates, nstates))
        self.transmat = transmat

        if labels is None:
            labels = [None] * nstates
        self.labels = labels

        self._default_trainer = trainer

    def eval(self, obs, maxrank=None, beamlogprob=-np.Inf):
        """Compute the log probability under the model and compute posteriors

        Implements rank and beam pruning in the forward-backward
        algorithm to speed up inference in large models.

        Parameters
        ----------
        obs : array_like, shape (n, ndim)
            Sequence of ndim-dimensional data points.  Each row
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
        posteriors: array_like, shape (n, nstates)
            Posterior probabilities of each state for each
            observation

        See Also
        --------
        lpdf : Compute the log probability under the model
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

    def lpdf(self, obs, maxrank=None, beamlogprob=-np.Inf):
        """Compute the log probability under the model.

        Parameters
        ----------
        obs : array_like, shape (n, ndim)
            Sequence of ndim-dimensional data points.  Each row
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
        eval : Compute the log probability under the model and compute posteriors
        decode : Find most likely state sequence corresponding to a `obs`
        """
        obs = np.asanyarray(obs)
        framelogprob = self._compute_log_likelihood(obs)
        logprob, fwdlattice =  self._do_forward_pass(framelogprob, maxrank,
                                                     beamlogprob)
        return logprob

    def decode(self, obs, maxrank=None, beamlogprob=-np.Inf):
        """Find most likely state sequence corresponding to `obs`.

        Uses the Viterbi algorithm.

        Parameters
        ----------
        obs : array_like, shape (n, ndim)
            List of ndim-dimensional data points.  Each row corresponds to a
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
        eval : Compute the log probability under the model and compute posteriors
        lpdf : Compute the log probability under the model
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
        obs : array_like, shape (n, ndim)
            List of ndim-dimensional data points.  Each row corresponds to a
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
        transmat_cdf = np.cumsum(transmat_pdf, 1);

        # Initial state.
        rand = np.random.rand()
        currstate = (startprob_cdf > rand).argmax()
        obs = [self._generate_sample_from_state(currstate)]

        for x in xrange(n-1):
            rand = np.random.rand()
            currstate = (transmat_cdf[currstate] > rand).argmax()
            obs.append(self._generate_sample_from_state(currstate))

        return np.array(obs)

    def fit(self, obs, niter=10, thresh=1e-2, params=string.letters,
            init_params=string.letters,
            maxrank=None, beamlogprob=-np.Inf, trainer=None, **kwargs):
        """Estimate model parameters with the Baum-Welch algorithm.

        An initialization step is performed before entering the EM
        algorithm. If you want to avoid this step, set the keyword
        argument init_params to the empty string ''. Likewise, if you
        would like just to do an initialization, call this method with
        niter=0.

        Parameters
        ----------
        obs : list
            List of array-like observation sequences (shape (n_i, ndim)).
        niter : int, optional
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

        Returns
        -------
        logprob : list
            Log probabilities of each data point in `obs` for each iteration
        """
        obs = np.asanyarray(obs)
        
        self._init(obs, init_params, **kwargs)
            
        if trainer is None:
            trainer = self._default_trainer
        
        if self.emission_type != trainer.emission_type:
            raise ValueError('trainer has incompatible emission_type')

        return trainer.train(self, obs, niter, thresh, params, maxrank,
                             beamlogprob, **kwargs)
    
    @property
    def nstates(self):
        """Number of states in the model."""
        return self._nstates

    def _get_startprob(self):
        """Mixing startprob for each state."""
        return np.exp(self._log_startprob)

    def _set_startprob(self, startprob):
        if len(startprob) != self._nstates:
            raise ValueError('startprob must have length nstates')
        if not np.allclose(np.sum(startprob), 1.0):
            raise ValueError('startprob must sum to 1.0')
        
        self._log_startprob = np.log(np.asanyarray(startprob).copy())

    startprob = property(_get_startprob, _set_startprob)

    def _get_transmat(self):
        """Matrix of transition probabilities."""
        return np.exp(self._log_transmat)

    def _set_transmat(self, transmat):
        if np.asanyarray(transmat).shape != (self._nstates, self._nstates):
            raise ValueError('transmat must have shape (nstates, nstates)')
        if not np.all(np.allclose(np.sum(transmat, axis=1), 1.0)):
            raise ValueError('Rows of transmat must sum to 1.0')
        
        self._log_transmat = np.log(np.asanyarray(transmat).copy())
        underflow_idx = np.isnan(self._log_transmat)
        self._log_transmat[underflow_idx] = -np.Inf

    transmat = property(_get_transmat, _set_transmat)
    
    def _do_viterbi_pass(self, framelogprob, maxrank=None, beamlogprob=-np.Inf):
        nobs = len(framelogprob)
        lattice = np.zeros((nobs, self._nstates))
        traceback = np.zeros((nobs, self._nstates), dtype=np.int) 

        lattice[0] = self._log_startprob + framelogprob[0]
        for n in xrange(1, nobs):
            idx = self._prune_states(lattice[n-1], maxrank, beamlogprob)
            pr = self._log_transmat[idx].T + lattice[n-1,idx]
            lattice[n]   = np.max(pr, axis=1) + framelogprob[n]
            traceback[n] = np.argmax(pr, axis=1)
        lattice[lattice <= ZEROLOGPROB] = -np.Inf;
        
        # Do traceback.
        reverse_state_sequence = []
        s = lattice[-1].argmax()
        logprob = lattice[-1,s]
        for frame in reversed(traceback):
            reverse_state_sequence.append(s)
            s = frame[s]

        reverse_state_sequence.reverse()
        return logprob, np.array(reverse_state_sequence)

    def _do_forward_pass(self, framelogprob, maxrank=None, beamlogprob=-np.Inf):
        nobs = len(framelogprob)
        fwdlattice = np.zeros((nobs, self._nstates))

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
        bwdlattice = np.zeros((nobs, self._nstates))

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

            rankthresh = cdf[hst >= min(maxrank, self._nstates)].max()
      
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
            self.startprob[:] = 1.0 / self._nstates
        if 't' in params:
            self.transmat[:] = 1.0 / self._nstates


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
    ndim : int (read-only)
        Dimensionality of the Gaussian emissions.
    nstates : int (read-only)
        Number of states in the model.
    transmat : array, shape (`nstates`, `nstates`)
        Matrix of transition probabilities between states.
    startprob : array, shape ('nstates`,)
        Initial state occupation distribution.
    means : array, shape (`nstates`, `ndim`)
        Mean parameters for each state.
    covars : array
        Covariance parameters for each state.  The shape depends on
        `cvtype`:
            (`nstates`,)                if 'spherical',
            (`ndim`, `ndim`)            if 'tied',
            (`nstates`, `ndim`)         if 'diag',
            (`nstates`, `ndim`, `ndim`) if 'full'
    labels : list, len `nstates`
        Optional labels for each state.

    Methods
    -------
    eval(obs)
        Compute the log likelihood of `obs` under the HMM.
    decode(obs)
        Find most likely state sequence for each point in `obs` using the
        Viterbi algorithm.
    rvs(n=1)
        Generate `n` samples from the HMM.
    init(obs)
        Initialize HMM parameters from `obs`.
    fit(obs)
        Estimate HMM parameters from `obs` using the Baum-Welch algorithm.
    predict(obs)
        Like decode, find most likely state sequence corresponding to `obs`.

    Examples
    --------
    >>> hmm = HMM('gaussian', nstates=2, ndim=1)

    See Also
    --------
    GMM : Gaussian mixture model
    """

    emission_type = 'gaussian'

    def __init__(self, nstates, ndim=1, cvtype='diag', startprob=None,
                 transmat=None, labels=None, means=None, covars=None,
                 trainer=hmm_trainers.GaussianHMMBaumWelchTrainer()):
        """Create a hidden Markov model with Gaussian emissions.

        Initializes parameters such that every state has zero mean and
        identity covariance.

        Parameters
        ----------
        nstates : int
            Number of states.
        ndim : int
            Dimensionality of the emissions.
        cvtype : string
            String describing the type of covariance parameters to
            use.  Must be one of 'spherical', 'tied', 'diag', 'full'.
            Defaults to 'diag'.
        """
        super(GaussianHMM, self).__init__(nstates, startprob, transmat, labels)

        self._ndim = ndim
        self._cvtype = cvtype
        if not cvtype in ['spherical', 'tied', 'diag', 'full']:
            raise ValueError('bad cvtype')
        
        if means is None:
            means = np.zeros((nstates, ndim))
        self.means = means

        if covars is None:
            covars = _distribute_covar_matrix_to_match_cvtype(np.eye(ndim),
                                                              cvtype, nstates)
        self.covars = covars

        self._default_trainer = trainer


    # Read-only properties.
    @property
    def cvtype(self):
        """Covariance type of the model.

        Must be one of 'spherical', 'tied', 'diag', 'full'.
        """
        return self._cvtype

    @property
    def ndim(self):
        """Dimensionality of the emissions."""
        return self._ndim

    def _get_means(self):
        """Mean parameters for each state."""
        return self._means

    def _set_means(self, means):
        means = np.asanyarray(means)
        if means.shape != (self._nstates, self._ndim):
            raise ValueError('means must have shape (nstates, ndim)')
        self._means = means.copy()

    means = property(_get_means, _set_means)

    def _get_covars(self):
        """Covariance parameters for each state."""
        return self._covars

    def _set_covars(self, covars):
        covars = np.asanyarray(covars)
        #_validate_covars(covars, self._cvtype, self._nstates, self._ndim)
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
            self._means, tmp = sp.cluster.vq.kmeans2(obs[0], self._nstates,
                                                     **kwargs)
        if 'c' in params:
            cv = np.cov(obs[0].T)
            if not cv.shape:
                cv.shape = (1, 1)
            self._covars = _distribute_covar_matrix_to_match_cvtype(
                cv, self._cvtype, self._nstates)


class MultinomialHMM(_BaseHMM):
    """Hidden Markov Model with multinomial (discrete) emissions

    Attributes
    ----------
    nstates : int (read-only)
        Number of states in the model.
    transmat : array, shape (`nstates`, `nstates`)
        Matrix of transition probabilities between states.
    startprob : array, shape ('nstates`,)
        Initial state occupation distribution.
    emissionprob: array, shape ('nstates`, K)
        Probability of emitting a given symbol when in each state.  K
        is the number of possible symbols in the observations.
    labels : list, len `nstates`
        Optional labels for each state.

    Methods
    -------
    eval(obs)
        Compute the log likelihood of `obs` under the HMM.
    decode(obs)
        Find most likely state sequence for each point in `obs` using the
        Viterbi algorithm.
    rvs(n=1)
        Generate `n` samples from the HMM.
    init(obs)
        Initialize HMM parameters from `obs`.
    fit(obs)
        Estimate HMM parameters from `obs` using the Baum-Welch algorithm.
    predict(obs)
        Like decode, find most likely state sequence corresponding to `obs`.

    Examples
    --------
    >>> hmm = HMM('multinomial', nstates=2)

    See Also
    --------
    GaussianHMM : HMM with Gaussian emissions
    """

    emission_type = 'multinomial'

    def __init__(self, nstates, nsymbols, startprob=None, transmat=None,
                 labels=None, emissionprob=None, 
                 trainer=hmm_trainers.MultinomialHMMBaumWelchTrainer()):
        """Create a hidden Markov model with multinomial emissions.

        Parameters
        ----------
        nstates : int
            Number of states.
        """
        super(MultinomialHMM, self).__init__(nstates, startprob, transmat,
                                             labels)
        self._nsymbols = nsymbols
        if not emissionprob:
            emissionprob = normalize(np.random.rand(self.nstates,
                                                    self.nsymbols), 1)
        self.emissionprob = emissionprob
        self._default_trainer = trainer

    # Read-only properties.
    @property
    def nsymbols(self):
        return self._nsymbols

    def _get_emissionprob(self):
        """Emission probability distribution for each state."""
        return np.exp(self._log_emissionprob)

    def _set_emissionprob(self, emissionprob):
        emissionprob = np.asanyarray(emissionprob)
        if emissionprob.shape != (self._nstates, self._nsymbols):
            raise ValueError('emissionprob must have shape (nstates, nsymbols)')

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
            emissionprob = normalize(np.random.rand(self._nstates,
                                                    self._nsymbols), 1)
            self.emissionprob = emissionprob


class GMMHMM(_BaseHMM):
    """Hidden Markov Model with Gaussin mixture emissions

    Attributes
    ----------
    nstates : int (read-only)
        Number of states in the model.
    transmat : array, shape (`nstates`, `nstates`)
        Matrix of transition probabilities between states.
    startprob : array, shape ('nstates`,)
        Initial state occupation distribution.
    gmms: array of GMM objects, length 'nstates`
        GMM emission distributions for each state
    labels : list, len `nstates`
        Optional labels for each state.

    Methods
    -------
    eval(obs)
        Compute the log likelihood of `obs` under the HMM.
    decode(obs)
        Find most likely state sequence for each point in `obs` using the
        Viterbi algorithm.
    rvs(n=1)
        Generate `n` samples from the HMM.
    init(obs)
        Initialize HMM parameters from `obs`.
    fit(obs)
        Estimate HMM parameters from `obs` using the Baum-Welch algorithm.
    predict(obs)
        Like decode, find most likely state sequence corresponding to `obs`.

    Examples
    --------
    >>> hmm = HMM('gmm', nstates=2, nmix=10, ndim=3)

    See Also
    --------
    GaussianHMM : HMM with Gaussian emissions
    """

    emission_type = 'gmm'

    def __init__(self, nstates, ndim, nmix=1, startprob=None, transmat=None,
                 labels=None, gmms=None,
                 trainer=hmm_trainers.GMMHMMBaumWelchTrainer(),
                 **kwargs):
        """Create a hidden Markov model with GMM emissions.

        Parameters
        ----------
        nstates : int
            Number of states.
        ndim : int (read-only)
            Dimensionality of the emissions.
        """
        super(GMMHMM, self).__init__(nstates, startprob, transmat,
                                     labels)

        self._ndim = ndim

        if gmms is None:
            gmms = []
            for x in xrange(self.nstates):
                gmms.append(gmm.GMM(nmix, ndim, **kwargs))
        self.gmms = gmms
        
        self._default_trainer = trainer

    # Read-only properties.
    @property
    def ndim(self):
        """Dimensionality of the emissions from this HMM."""
        return self._ndim

    def _compute_log_likelihood(self, obs):
        return np.array([g.lpdf(obs) for g in self.gmms]).T

    def _generate_sample_from_state(self, state):
        return self.gmms[state].rvs(1).flatten()

    def _init(self, obs, params='stwmc', **kwargs):
        super(GMMHMM, self)._init(obs, params=params)

        allobs = np.concatenate(obs, 0)
        for g in self.gmms:
            g.fit(allobs, niter=0, init_params=params)
        

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


def _load_document_classification(dataset_path, metadata, set_, **kw):
    """Loader implementation for the DocumentClassification format"""
    target = []
    target_names = {}
    filenames = []
    vectorizer = kw.get('vectorizer', HashingVectorizer())

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
        vectorizer.vectorize(documents)
        target.extend(len(documents) * [label])
        filenames.extend(documents)

    return Bunch(data=vectorizer.get_vectors(), target=np.array(target),
                 target_names=target_names, filenames=filenames,
                 DESCR=metadata.get('description'))


LOADERS = {
    'DocumentClassification': _load_document_classification,
    # TODO: implement the remaining domain formats
}


def load_mlcomp(name_or_id, set_="raw", mlcomp_root=None, **kwargs):
    """Load a datasets as downloaded from http://mlcomp.org

    Parameters
    ----------

    name_or_id : the integer id or the string name metadata of the MLComp
                 dataset to load

    set_ : select the portion to load: 'train', 'test' or 'raw'

    mlcomp_root : the filesystem path to the root folder where MLComp datasets
                  are stored, if mlcomp_root is None, the MLCOMP_DATASETS_HOME
                  environment variable is looked up instead.

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
    return loader(dataset_path, metadata, set_=set_, **kwargs)



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

"""Package for modules that deal with feature extraction from raw data"""

# Author: Olivier Grisel <olivier.grisel@ensta.org>
#
# License: BSD Style.
"""Utilities to build feature vectors from text documents"""

import re
import unicodedata
import numpy as np

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


class SimpleAnalyzer(object):
    """Simple analyzer: transform a text document into a sequence of tokens

    This simple implementation does:
        - lower case conversion
        - unicode accents removal
        - token extraction using unicode regexp word bounderies for token of
          minimum size of 2 symbols
    """

    token_pattern = re.compile(r"\b\w\w+\b", re.U)

    def __init__(self, default_charset='utf-8', stop_words=None):
        self.charset = default_charset
        self.stop_words = stop_words

    def analyze(self, text_document):
        if isinstance(text_document, str):
            text_document = text_document.decode(self.charset, 'ignore')
        text_document = strip_accents(text_document.lower())
        tokens = self.token_pattern.findall(text_document)
        if self.stop_words is not None:
            return [w for w in tokens if w not in self.stop_words]
        else:
            return tokens


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

    # TODO: make it possible to select between the current dense representation
    # and sparse alternatives from scipy.sparse once the liblinear and libsvm
    # wrappers have been updated to be able to handle it efficiently

    def __init__(self, dim=5000, probes=1, analyzer=SimpleAnalyzer(),
                 use_idf=True):
        self.dim = dim
        self.probes = probes
        self.analyzer = analyzer
        self.use_idf = use_idf

        # start counts at one to avoid zero division while
        # computing IDF
        self.df_counts = np.ones(dim, dtype=long)
        self.tf_vectors = None
        self.sampled = 0

    def hash_sign(self, token, probe=0):
        h = hash(token + (probe * u"#"))
        return abs(h) % self.dim, 1.0 if h % 2 == 0 else -1.0

    def sample_document(self, text, tf_vector=None, update_estimates=True):
        """Extract features from text and update running freq estimates"""
        if tf_vector is None:
            # allocate term frequency vector and stack to history
            tf_vector = np.zeros(self.dim, np.float64)
            if self.tf_vectors is None:
                self.tf_vectors = tf_vector.reshape((1, self.dim))
            else:
                self.tf_vectors = np.vstack((self.tf_vectors, tf_vector))
                tf_vector = self.tf_vectors[-1]

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
            self.sampled += 1
        return tf_vector

    def get_idf(self):
        return np.log(float(self.sampled) / self.df_counts)

    def get_tfidf(self):
        """Compute the TF-log(IDF) vectors of the sampled documents"""
        if self.tf_vectors is None:
            return None
        return self.tf_vectors * self.get_idf()

    def vectorize(self, document_filepaths):
        """Vectorize a batch of documents"""
        tf_vectors = np.zeros((len(document_filepaths), self.dim))
        for i, filepath in enumerate(document_filepaths):
            self.sample_document(file(filepath).read(), tf_vectors[i])

        if self.tf_vectors is None:
            self.tf_vectors = tf_vectors
        else:
            self.tf_vectors = np.vstack((self.tf_vectors, tf_vectors))

    def get_vectors(self):
        if self.use_idf:
            return self.get_tfidf()
        else:
            return self.tf_vectors



#! /usr/bin/env python
# Last Change: Fri Jan 23 08:00 PM 2009 J
from preprocessing import scale, nanscale, Scaler, NanScaler

__all__ = ['scale', 'nanscale', 'Scaler', 'NanScaler']

#! /usr/bin/env python
# Last Change: Mon Feb 02 11:00 PM 2009 J

# Various utilities for examples 

import numpy as N

"""Different tools for pre processing, like whitening or scaling data."""

_DEF_SCALE_MODE = 'sym'

#---------------------------------------------------------------------------
# Definition of scaling-related function (handle each feature independantly)
#---------------------------------------------------------------------------
def _scale_factor(data, mode = _DEF_SCALE_MODE):
    """Compute the scaling factors for data to be normalized.
    
    Note
    ----
    
    Does not handle data with nan."""
    n = N.min(data, 0)
    m = N.max(data, 0)
    if mode == 'sym':
        t = n + 0.5 * (m - n)
        s = 0.5 * (m - n)
    elif mode == 'right':
        t = n
        s = m - n
    else:
        raise ValueError("Mode %s not recognized" % mode)
    return t, s
    
def _nan_scale_factor(data, mode = _DEF_SCALE_MODE):
    """Compute the scaling factors for data to be normalized.
    
    This version handled data with Nan."""
    n = N.nanmin(data, 0)
    m = N.nanmax(data, 0)
    # If any t or s has Nan, this means that one feature has only Nan. This
    # will propagate Nan to new preprocessed data, which does not really
    # make sense: raise an exception in this case.
    if not (N.all(N.isfinite(n)) and N.all(N.isfinite(m))):
        raise ValueError("Nan scale factors: is any feature of data full"\
                         "of Nan ?")
    if mode == 'sym':
        t = n + 0.5 * (m - n)
        s = 0.5 * (m - n)
    elif mode == 'right':
        t = n
        s = m - n
    else:
        raise ValueError("Mode %s not recognized" % mode)
    return t, s
    
def schandlenan(f, note):
    """Decorator to generate scaling function handling / not handling Nan."""
    def decorator(func):
        ""
        def wrapper(data, mode = _DEF_SCALE_MODE):
            ""
            return func(data, mode, f)
        wrapper.__name__ = func.__name__
        wrapper.__dict__ = func.__dict__
        wrapper.__doc__ = \
"""Linearly scale data in place such as each col is in the range
[0..1] or [-1..1].

:Parameters:
    data : ndarray
        the data to scale. One feature per column (eg the
        normalization is done column-wise).
    mode : string
        - 'sym': normalized data are in the range [-1..1]
        - 'right': normalized data are in the range [0..1]

:Returns:
    s : ndarray
        the scaling factor.
    t : ndarray
        the translation factor
        
:SeeAlso:

Scaler, whiten.

Note:
-----

You can retrieve the original values with data = s * scaled + t.  

This is intended to normalize data for pre processing; in
perticular, the range after normalized do not have strong
constraints: some values may be higher than 1 due to precision
problems.\n\n""" + note
        return wrapper
    return decorator

@schandlenan(_scale_factor, "This function does NOT handle Nan.")
def scale(data, mode, scf):
    t, s = scf(data, mode)
    data -= t
    data /= s
    return s, t

@schandlenan(_nan_scale_factor, "This function DOES handle Nan.")
def nanscale(data, mode, scf):
    t, s = scf(data, mode)
    data -= t
    data /= s
    return s, t
#def scale(data, mode = _DEF_SCALE_MODE):
#    """Linearly scale data in place such as each col is in the range [0..1] or
#    [-1..1].
#
#    :Parameters:
#        data : ndarray
#            the data to scale. One feature per column (eg the normalization is
#            done column-wise).
#        mode : string
#            - 'sym': normalized data are in the range [-1..1]
#            - 'right': normalized data are in the range [0..1]
#
#    :Returns:
#        s : ndarray
#            the scaling factor.
#        t : ndarray
#            the translation factor
#            
#    :SeeAlso:
#
#    Scaler, whiten.
#
#    Note:
#    -----
#
#    Handle data with Nan values (are ignored)
#
#    You can retrieve the original values with data = s * scaled + t.  
#
#    This is intended to normalize data for pre processing; in perticular, the
#    range after normalized do not have strong constraints: some values may be
#    higher than 1 due to precision problems."""
#    t, s = _scale_factor(data, mode)
#    data -= t
#    data /= s
#    return s, t

def whiten():
    """Whiten data."""
    raise NotImplementedError("whitening not implemented yet")

class Scaler:
    """Class to implement a scaler, eg an object which can scale data, keep the
    scale factors, and rescale/unscale further data using those factors.

    For example, in supervised training, you may want to rescale some data,
    usually using the training data. Once the training is done with the scaled
    data, you need to scale the testing and unknown data by the same factor,
    and maybe also to "unscale" them afterwards."""
    def __init__(self, data, mode = _DEF_SCALE_MODE):
        """Init the scaler, computing scaling factor from data."""
        t, s = _scale_factor(data, mode)
        self.t = t
        self.s = s

    def scale(self, data):
        """Scale data *in-place*."""
        try:
            data -= self.t
            data /= self.s
        except ValueError, e:
            raise ValueError("data to scale should have the same number of"\
                             "features than data used when initializing the"\
                             "scaler")
        return data

    def unscale(self, data):
        """Unscale data *in-place*."""
        try:
            data *= self.s
            data += self.t
        except ValueError, e:
            raise ValueError("data to unscale should have the same number of"\
                             "features than data used when initializing the"\
                             "scaler")
        return data

class NanScaler(Scaler):
    """Special scaler which ignore Nan data."""
    def __init__(self, data, mode = _DEF_SCALE_MODE):
        """Init the scaler, computing scaling factor from data.

        Note
        ----

        If one feature has only Nan, the scaling parameters will contain Nan
        values, and as such, will propagate Nan to newly data fed to
        preprocess. To avoid this, an exception is raised."""
        t, s = _nan_scale_factor(data, mode)
        self.t = t
        self.s = s

import sys
import math
import numpy as np

def fast_logdet(A):
    """
    Compute log(det(A)) for A symmetric
    Equivalent to : np.log(nl.det(A))
    but more robust
    It returns -Inf if det(A) is non positive or is not defined.
    """
    ld = np.sum(np.log(np.diag(A)))
    a = np.exp(ld/A.shape[0])
    d = np.linalg.det(A/a)
    ld += np.log(d)
    if not np.isfinite(ld):
        return -np.inf
    return ld

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


"""
Feature slection module for python.
"""

"""
Univariate features selection.
"""

# Authors: V. Michel, B. Thirion, G. Varoquaux, A. Gramfort, E. Duchesnay
# License: BSD 3 clause

import numpy as np
from scipy import stats


######################################################################
# General class for filter univariate selection
######################################################################

class UnivariateFilter(object):
    """
    General class for filter univariate selection.
   
    Parameters
    ====================
    score_func : scoring function. Takes two arrays X and y, and returning two
                 arrays (scores and pvalues) of size X.shape[1].
    ranking : ranking function. Heuristic for selecting the features based on
              both the pvalues or the scores.

    Example
    =====================
    >>> import scikits.learn.datasets.samples_generator as sg
    >>> X,y = sg.sparse_uncorrelated(50,100)
    >>> univ_filter = UnivariateFilter(SelectKBest(k=5),f_regression)
    >>> X_r = univ_filter.fit(X, y).transform(X)

    """

  
    def __init__(self,ranking,score_func):

        assert callable(score_func), ValueError(
                "The score function should be a callable, '%s' (type %s) "
                "was passed." % (score_func, type(score_func))
            )
        self.score_func = score_func
        self.ranking = ranking

    def fit(self,X,y):
        """
        Evaluate the function
        """
        self._scores = self.score_func(X, y)
        #self._scores = _scores[0]
        #self._pvalues = _scores[1]
        #self._rank = np.argsort(self._pvalues)
        return self

    def transform(self,X,**kwargs):
        """
        Transform a new matrix using the selected features
        """
        self.support = self.ranking.support(self._scores,**kwargs)
        return X[:,self.support]





######################################################################
# Specific rankings
######################################################################

class SelectPercentile(object):
    """
    Filter : Select the best percentile of the p_values
    """
    def __init__(self,percentile):
        self.percentile = percentile

    def support(self,scores,percentile=None):
        if percentile is not None:
                self.percentile = percentile 
        assert self.percentile<=100, ValueError('percentile should be \
                            between 0 and 100 (%f given)' %(self.percentile))
        alpha = stats.scoreatpercentile(scores[1], self.percentile)
        return (scores[1] <= alpha)

class SelectKBest(object):
    """
    Filter : Select the k lowest p-values
    """
    def __init__(self,k):
        self.k = k

    def support(self,scores,k=None):
          if k is not None:
                self.k=k
          assert self.k<=len(scores[1]), ValueError('cannot select %d features'
                                  ' among %d ' % (self.k, len(scores[1])))
          alpha = np.sort(scores[1])[self.k-1]
          return (scores[1] <= alpha)

class SelectFpr(object):
    """
    Filter : Select the pvalues below alpha
    """
    def __init__(self,alpha):
        self.alpha = alpha

    def support(self,scores,alpha = None):
        if alpha is not None:
              self.alpha=alpha
        return (scores[1] < self.alpha)

class SelectFdr(object):
    """
    Filter : Select the p-values corresponding to an estimated false
    discovery rate of alpha. This uses the Benjamini-Hochberg procedure
    """
    def __init__(self,alpha):
        self.alpha = alpha

    def support(self,scores, alpha = None):
        if alpha is not None:
              self.alpha=alpha
        sv = np.sort(scores[1])
        threshold = sv[sv < self.alpha*np.arange(len(scores[1]))].max()
        return (scores[1] < threshold)

class SelectFwe(object):
    """
    Filter : Select the p-values corresponding to a corrected p-value of alpha
    """
    def __init__(self,alpha):
        self.alpha = alpha

    def support(self,scores,alpha = None):
        if alpha is not None:
              self.alpha=alpha
        return (scores[1] < self.alpha/len(scores[1]))


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






if __name__ == "__main__":
    import scikits.learn.datasets.samples_generator as sg
    from scikits.learn.svm import SVR, SVC

    X,y = sg.sparse_uncorrelated(50,100)
    univ_filter = UnivariateFilter(SelectKBest(k=5),f_regression)
    X_r_5 = univ_filter.fit(X, y).transform(X)
    X_r_10 = univ_filter.transform(X,k=10)
    univ_filter.ranking.k = 20
    #univ_filter.selector.k = 20
    X_r_20 = univ_filter.fit(X, y).transform(X)
    univ_filter.ranking = SelectPercentile(percentile = 50)
    X_r_50 = univ_filter.fit(X, y).transform(X)


    
    univ_filter = UnivariateFilter(SelectKBest(k=5),f_regression)
    X_r = univ_filter.fit(X, y).transform(X)
    print "Support :", univ_filter.support
    clf = SVR(kernel='linear', C=1.)
    y_ = clf.fit(X_r, y).predict(X_r)
    ### now change k
    X_r = univ_filter.transform(X, k=2)
    y_ = clf.fit(X_r, y).predict(X)
    print "Support :", univ_filter.support



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

Author: Fabian Pedregosa <fabian.pedregosa@inria.fr>
License: New BSD
"""

import numpy as np
from scipy import sparse

from ..base import BaseEstimator
from .. import svm, _libsvm

class SparseBaseLibsvm(BaseEstimator):

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
        self.dual_coef_       = np.empty ((0,0), dtype=np.float64, order='C')
        self.intercept_       = np.empty (0,     dtype=np.float64, order='C')

        # only used in classification
        self.nSV_ = np.empty(0, dtype=np.int32, order='C')


    def fit(self, X, Y, class_weight={}):

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
                 self._support_indptr, self.dual_coef_,
                 self.intercept_, self.weight_label, self.weight,
                 self.nSV_, self.nu, self.cache_size, self.p,
                 self.shrinking,
                 int(self.probability))

        self.support_ = sparse.csr_matrix((self._support_data, 
                                           self._support_indices,
                                           self._support_indptr))
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
        T : scipy.sparse.csr, shape = [nsamples, nfeatures]

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
                      self.dual_coef_, self.intercept_,
                      self._svm_types.index(self.impl),
                      kernel_type, self.degree,
                      self.gamma, self.coef0, self.eps, self.C,
                      self.weight_label, self.weight,
                      self.nu, self.cache_size, self.p,
                      self.shrinking, self.probability,
                      self.nSV_, self.label_, self.probA_,
                      self.probB_)

class SVC(SparseBaseLibsvm):
    """
    SVC for sparse matrices (csr)
    
    For best results, this accepts a matrix in csr format
    (scipy.sparse.csr), but should be able to convert from any array-like
    object (including other sparse representations).

    """
    def __init__(self, impl='c_svc', kernel='rbf', degree=3, gamma=0.0,
                 coef0=0.0,cache_size=100.0, eps=1e-3, C=1.0,nu=0.5, p=0.1,
                 shrinking=True, probability=False):

        SparseBaseLibsvm.__init__(self, impl, kernel, degree, gamma, coef0,
                         cache_size, eps, C, nu, p,
                         shrinking, probability)


"""

Demo of affinity propagation clustering algorithm
====================================================

Reference:
Brendan J. Frey and Delbert Dueck, "Clustering by Passing Messages
Between Data Points", Science Feb. 2007

"""

import numpy as np
from scikits.learn.clustering import affinity_propagation

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

cluster_centers_indices, labels = affinity_propagation(S, p)

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

import numpy as np
from scikits.learn.svm import SVC
from scikits.learn.cross_val import StratifiedKFold, GridSearchCV
from scikits.learn import datasets
from scikits.learn.rfe import RFE



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
rfe = RFE(estimator=svc, n_features=10, percentage=0.1)
clf = SVC(kernel="linear",C=1)

y_pred = []
y_true = []
for train, test in StratifiedKFold(y, 2):
    Xtrain, ytrain, Xtest, ytest = X[train], y[train], X[test], y[test]

    ### Fit and predict rfe
    support_ = rfe.fit(X[train], y[train]).support_
    y_pred.append(clf.fit(Xtrain[:,support_],ytrain).predict(
          Xtest[:,support_]))
    ranking_ = rfe.ranking_


y_true = np.concatenate(y_true)
y_pred = np.concatenate(y_pred)
classif_rate = np.mean(y_pred == y_true) * 100
print "Classification rate: %f" % classif_rate


    
image_support_ = rfe.support_.reshape(digits.images[0].shape)
import pylab as pl
pl.matshow(image_support_)
pl.colorbar()
pl.title('Voxels selected with RFE')

image_support_ = rfe.ranking_.reshape(digits.images[0].shape)
import pylab as pl
pl.matshow(image_support_)
pl.colorbar()
pl.title('Ranking of voxels with RFE')


### Create the happy curve
classif_score = []
for i in np.unique(ranking_):
    clf.fit(Xtrain[:,ranking_<=i],ytrain)
    classif_score.append(np.mean(clf.predict(Xtest[:,ranking_<=i])
                                == ytest) * 100)

import pylab as pl
pl.plot(classif_score)










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
from scikits.learn.cross_val import StratifiedKFold, GridSearchCV
from scikits.learn import datasets

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
tuned_parameters = {'kernel':('rbf', 'linear'), 
                    'gamma':[1e-3, 1e-4]}

def loss_func(y1, y2):
    return np.mean(y1 != y2)

clf = GridSearchCV(SVC(C=1), tuned_parameters, loss_func, n_jobs=2)

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

clf = gmm.GMM(2, ndim=2, cvtype='full')
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
from scikits.learn.feature_selection import univariate_selection as us
# As a scoring function, we use a F test for classification
# We use the default selection function: the 10% most significant
# features

selector = us.UnivariateFilter(us.SelectFpr(alpha=0.1),us.f_classif)
selector.fit(x, y)
scores = -np.log(selector._scores[1])
scores /= scores.max()
pl.bar(x_indices-.45, scores, width=.3, 
        label=r'Univariate score ($-\log(p\,values)$)', 
        color='g')

################################################################################
# Compare to the weights of an SVM
clf = svm.SVC(kernel='linear')
clf.fit(x, y)

svm_weights = (clf.support_**2).sum(axis=0)
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
pl.legend()
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

clf = gmm.GMM(2, ndim=2, cvtype='full')
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

from scikits.learn import clustering

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

_, labels = clustering.affinity_propagation(correlations)

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
==========================
Pipeline Anova SVM
==========================

Simple usages of pipeline:
- ANOVA SVM-C
"""

from scikits.learn import svm, datasets
from scikits.learn.datasets import samples_generator
from scikits.learn.feature_selection.univariate_selection import UnivariateFilter,SelectKBest,f_regression
from scikits.learn.pipeline import Pipeline

# import some data to play with
X,y = samples_generator.test_dataset_classif(k=5)


# ANOVA SVM-C
# 1) anova filter, take 5 best ranked features 
anova_filter = UnivariateFilter(SelectKBest(k=5), f_regression)
# 2) svm
clf = svm.SVC(kernel='linear')

anova_svm = Pipeline([anova_filter],clf)
anova_svm.fit(X,y)
anova_svm.predict(X)



"""

A demo of the mean-shift clustering algorithm
===============================================

Reference:
K. Funkunaga and L.D. Hosteler, "The Estimation of the Gradient of a
Density Function, with Applications in Pattern Recognition"

"""

import numpy as np
from scikits.learn.clustering import MeanShift

################################################################################
# Generate sample data
np.random.seed(0)

n_points_per_cluster = 250
n_clusters = 3
n_points = n_points_per_cluster*n_clusters
means = np.array([[1,1],[-1,-1],[1,-1]])
std = .6
bandwidth = 1.2
clustMed = []

X = np.empty((0, 2))
for i in range(n_clusters):
    X = np.r_[X, means[i] + std * np.random.randn(n_points_per_cluster, 2)]


################################################################################
# Compute clustering with MeanShift
ms = MeanShift(bandwidth=bandwidth)
ms.fit(X).labels
labels = ms.labels
cluster_centers = ms.cluster_centers

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
clf = svm.SVC(impl='nu_svc', kernel='rbf', C=100)
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
==========================
Linear SVM classifier
==========================

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

h=.02 # step size in the mesh

# we create an instance of SVM and fit out data. We do not scale our
# data since we want to plot the support vectors
clf = svm.SVC(kernel='linear')
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
pl.scatter(clf.support_[:,0], clf.support_[:, 1], marker='+')
pl.title('3-Class classification using Support Vector Machine. \n' + \
         'Support Vectors are hightlighted with a +')
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
==================
One-class SVM
==================
"""

import numpy as np
import pylab as pl
from scikits.learn import svm

xx, yy = np.meshgrid(np.linspace(-5, 5, 500), np.linspace(-5, 5, 500))
X = np.random.randn(100, 2)
Y = [0]*100

# fit the model
clf = svm.OneClassSVM(nu=0.5)
clf.fit(X, Y)

# plot the line, the points, and the nearest vectors to the plane
Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)

pl.set_cmap(pl.cm.Paired)
pl.pcolormesh(xx, yy, Z)
pl.scatter(X[:,0], X[:,1], c=Y)
pl.scatter(clf.support_[:,0], clf.support_[:,1], c='black')
pl.axis('tight')
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
nsamples_1 = 1000
nsamples_2 = 100
X = np.r_[1.5*np.random.randn(nsamples_1, 2), 0.5*np.random.randn(nsamples_2, 2) + [2, 2]]
Y = [0]*(nsamples_1) + [1]*(nsamples_2)

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
nsamples = 100
X = [[i] for i in np.linspace(xmin, xmax, nsamples)]
Y = 2 + 0.5 * np.linspace(xmin, xmax, nsamples) +  np.random.randn(nsamples, 1).ravel()

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
# License: BSD Style.

from datetime import datetime
import itertools
import numpy as np
import pylab as pl

from scikits.learn import glm
from scikits.learn import datasets

diabetes = datasets.load_diabetes()
X = diabetes.data
Y = diabetes.target


################################################################################
# Demo path functions
################################################################################

print "Computing regularization path using the LARS ..."
start = datetime.now()
clf = glm.LeastAngleRegression().fit(X, Y, normalize=True)
print "This took ", datetime.now() - start

alphas = -np.log10(clf.alphas_)

# # Display results
color_iter = itertools.cycle (['r', 'g', 'b', 'c'])

for coef_, color in zip(clf.coef_path_, color_iter):
    pl.plot(alphas, coef_.T, color)

ymin, ymax = pl.ylim()
pl.vlines(alphas, ymin, ymax, linestyle='dashed')
pl.xlabel('-Log(lambda)')
pl.ylabel('weights')
pl.title('Least Angle Regression (LAR) Paths')
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

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

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
# Import numpy to avoid an annoying bug in an example due to the use of 
# execfile
import numpy as np

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
                execfile(example_file)
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

def initialize(app):
    try:
        app.connect('autodoc-process-signature', mangle_signature)
    except:
        monkeypatch_sphinx_ext_autodoc()

def setup(app, get_doc_object_=get_doc_object):
    global get_doc_object
    get_doc_object = get_doc_object_

    app.connect('autodoc-process-docstring', mangle_docstrings)
    app.connect('builder-inited', initialize)
    app.add_config_value('numpydoc_edit_link', None, False)
    app.add_config_value('numpydoc_use_plots', None, False)
    app.add_config_value('numpydoc_show_class_members', True, True)

    # Extra mangling directives
    name_type = {
        'cfunction': 'function',
        'cmember': 'attribute',
        'cmacro': 'function',
        'ctype': 'class',
        'cvar': 'object',
        'class': 'class',
        'function': 'function',
        'attribute': 'attribute',
        'method': 'function',
        'staticmethod': 'function',
        'classmethod': 'function',
    }

    for name, objtype in name_type.items():
        app.add_directive('np-' + name, wrap_mangling_directive(name, objtype))

#------------------------------------------------------------------------------
# Input-mangling directives
#------------------------------------------------------------------------------
from docutils.statemachine import ViewList

def get_directive(name):
    from docutils.parsers.rst import directives
    try:
        return directives.directive(name, None, None)[0]
    except AttributeError:
        pass
    try:
        # docutils 0.4
        return directives._directives[name]
    except (AttributeError, KeyError):
        raise RuntimeError("No directive named '%s' found" % name)

def wrap_mangling_directive(base_directive_name, objtype):
    base_directive = get_directive(base_directive_name)

    if inspect.isfunction(base_directive):
        base_func = base_directive
        class base_directive(Directive):
            required_arguments = base_func.arguments[0]
            optional_arguments = base_func.arguments[1]
            final_argument_whitespace = base_func.arguments[2]
            option_spec = base_func.options
            has_content = base_func.content
            def run(self):
                return base_func(self.name, self.arguments, self.options,
                                 self.content, self.lineno,
                                 self.content_offset, self.block_text,
                                 self.state, self.state_machine)

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

#------------------------------------------------------------------------------
# Monkeypatch sphinx.ext.autodoc to accept argspecless autodocs (Sphinx < 0.5)
#------------------------------------------------------------------------------

def monkeypatch_sphinx_ext_autodoc():
    global _original_format_signature
    import sphinx.ext.autodoc

    if sphinx.ext.autodoc.format_signature is our_format_signature:
        return

    print "[numpydoc] Monkeypatching sphinx.ext.autodoc ..."
    _original_format_signature = sphinx.ext.autodoc.format_signature
    sphinx.ext.autodoc.format_signature = our_format_signature

def our_format_signature(what, obj):
    r = mangle_signature(None, what, None, obj, None, None, None)
    if r is not None:
        return r[0]
    else:
        return _original_format_signature(what, obj)

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
            doc = inspect.getdoc(func) or ''
        try:
            NumpyDocString.__init__(self, doc)
        except ValueError, e:
            print '*'*78
            print "ERROR: '%s' while parsing `%s`" % (e, self._f)
            print '*'*78
            #print "Docstring follows:"
            #print doclines
            #print '='*78

        if not self['Signature']:
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
        if not inspect.isclass(cls):
            raise ValueError("Initialise using a class. Got %r" % cls)
        self._cls = cls

        if modulename and not modulename.endswith('.'):
            modulename += '.'
        self._mod = modulename
        self._name = cls.__name__
        self._func_doc = func_doc

        if doc is None:
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
        return [name for name,func in inspect.getmembers(self._cls)
                if not name.startswith('_') and callable(func)]

    @property
    def properties(self):
        return [name for name,func in inspect.getmembers(self._cls)
                if not name.startswith('_') and func is None]

