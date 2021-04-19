#! /usr/bin/env python
# Last Change: Sat Jul 21 09:00 PM 2007 J

# Copyright (C) 2007-2009 Cournapeau David <cournape@gmail.com>
#               2010 Fabian Pedregosa <fabian.pedregosa@inria.fr>

descr   = """A set of python modules for machine learning and data mining"""

from os.path import join
import os
import sys

DISTNAME            = 'scikits.learn' 
DESCRIPTION         = 'A set of python modules for machine learning and data mining'
LONG_DESCRIPTION    = descr
MAINTAINER          = 'Fabian Pedregosa'
MAINTAINER_EMAIL    = 'fabian.pedregosa@inria.fr'
URL                 = 'http://scikit-learn.sourceforge.net'
LICENSE             = 'new BSD'
DOWNLOAD_URL        = 'http://sourceforge.net/projects/scikit-learn/files/'
VERSION             = '0.4-git'

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
import scipy.linalg # TODO: use numpy.linalg instead
import scipy.sparse as sp # needed by LeastAngleRegression

from .cd_fast import lasso_coordinate_descent, enet_coordinate_descent
from .utils.extmath import fast_logdet, density
from .cross_val import KFold
from .minilearn import lars_fit_wrap


###
### TODO: intercept for all models
### We should define a common function to center data instead of
### repeating the same code inside each fit method.
###
### Also, bayesian_ridge_regression and bayesian_regression_ard
### should be squashed into its respective objects.
###

class LinearModel(object):
    """Base class for Linear Models"""

    def __init__(self, coef=None):
        # weights of the model (can be lazily initialized by the ``fit`` method)
        self.coef_ = coef

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

    def compute_rsquared(self, X, Y):
        """Compute explained variance a.k.a. r^2"""
        self.rsquared_ = 1 - np.linalg.norm(Y - np.dot(X, self.coef_))**2 \
                         / np.linalg.norm(Y)**2


class LinearRegression(LinearModel):
    """
    Ordinary least squares Linear Regression.

    Parameters
    ----------
    This class takes no parameters

    Attributes
    ----------
    coef_ : array
        Estimated coefficients for the linear regression problem.

    intercept_ : array
        Independent term in the linear model.

    This is just plain linear regression wrapped is a Predictor object.
    """

    def fit(self,X,Y, intercept=True):
        """
        Fit linear model.

        Parameters
        ----------
        X : numpy array of shape [nsamples,nfeatures]
            Training data
        Y : numpy array of shape [nsamples]
            Target values
        intercept : boolen
            wether to calculate the intercept for this model. If set
            to false, no intercept will be used in calculations
            (e.g. data is expected to be already centered).

        Returns
        -------
        self : returns an instance of self.
        """
        X = np.asanyarray( X )
        Y = np.asanyarray( Y )

        if intercept:
            # augmented X array to store the intercept
            X = np.c_[X, np.ones(X.shape[0])]
        self.coef_, self.residues_, self.rank_, self.singular_ = \
                np.linalg.lstsq(X, Y)
        if intercept:
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
    alpha : ridge parameter. Small positive values of alpha improve
    the coditioning of the problem and reduce the variance of the
    estimates.
    
    Examples
    --------
    # With more samples than features
    >>> import numpy as np
    >>> nsamples, nfeatures = 10, 5
    >>> np.random.seed(0)
    >>> Y = np.random.randn(nsamples)
    >>> X = np.random.randn(nsamples, nfeatures)
    >>> clf = Ridge(alpha=1.0)
    >>> clf.fit(X, Y) #doctest: +ELLIPSIS
    <scikits.learn.glm.Ridge object at 0x...>

    See also
    --------
    http://scikit-learn.sourceforge.net/doc/modules/linreg.html
    """

    def __init__(self, alpha=1.0):
        self.alpha = alpha

    def fit(self, X, Y, intercept=True):
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
        nsamples, nfeatures = X.shape

        self._intercept = intercept
        if self._intercept:
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


class BayesianRidge (LinearModel):
    """
    Encapsulate various bayesian regression algorithms
    """

    def __init__(self, ll_bool=False, step_th=300, th_w=1.e-12):
        self.ll_bool = ll_bool
        self.step_th = step_th
        self.th_w = th_w

    def fit(self, X, Y, intercept=True):
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
        X = np.asanyarray(X, dtype=np.float)
        Y = np.asanyarray(Y, dtype=np.float)

        self._intercept = intercept
        if self._intercept:
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

        return self


class ARDRegression (LinearModel):
    """
    Encapsulate various bayesian regression algorithms
    """
    # TODO: add intercept

    def __init__(self, ll_bool=False, step_th=300, th_w=1.e-12,\
        alpha_th=1.e+16):
        self.ll_bool = ll_bool
        self.step_th = step_th
        self.th_w = th_w
        self.alpha_th = alpha_th

    def fit(self, X, Y):
        X = np.asanyarray(X, dtype=np.float)
        Y = np.asanyarray(Y, dtype=np.float)
        self.w ,self.alpha ,self.beta ,self.sigma ,self.log_likelihood = \
            bayesian_regression_ard(X, Y, self.step_th, self.th_w,\
            self.alpha_th, self.ll_bool)
        return self

    def predict(self, T):
        return np.dot(T, self.w)



### helper methods
### we should homogeneize this

def bayesian_ridge_regression( X , Y, step_th=300, th_w = 1.e-12, ll_bool=False):
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

    The lasso estimate solves the minization of the least-squares
    penalty with alpha * ||beta||_1 added, where alpha is a constant and
    ||beta||_1 is the L1-norm of the parameter vector.

    This formulation is useful in some context due to its tendency to
    prefer solutions with fewer parameter values, effectively reducing
    the number of variables upon which the given solution is
    dependent. For this reason, the LASSO and its variants are
    fundamental to the field of compressed sensing.

    Parameters
    ----------
    alpha : double, optional
        Constant that multiplies the L1 term. Defaults to 1.0

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
    Lasso Coordinate Descent
    >>> print clf.coef_
    [ 0.85  0.  ]
    >>> print clf.intercept_
    0.15

    Notes
    -----
    The algorithm used to fit the model is coordinate descent.x
    """

    def __init__(self, alpha=1.0, coef=None, tol=1e-4):
        super(Lasso, self).__init__(coef)
        self.alpha = float(alpha)
        self.tol = tol

    def fit(self, X, Y, intercept=True, maxit=1000):
        """
        Fit Lasso model.

        Parameters
        ----------
        X : numpy array of shape [nsamples,nfeatures]
            Training data
        Y : numpy array of shape [nsamples]
            Target values
        intercept : boolean
            whether to calculate the intercept for this model. If set
            to false, no intercept will be used in calculations
            (e.g. data is expected to be already centered).

        Returns
        -------
        self : returns an instance of self.
        """
        X = np.asanyarray(X, dtype=np.float64)
        Y = np.asanyarray(Y, dtype=np.float64)

        self._intercept = intercept
        if self._intercept:
            self._xmean = X.mean(axis=0)
            self._ymean = Y.mean(axis=0)
            X = X - self._xmean
            Y = Y - self._ymean
        else:
            self._xmean = 0.
            self._ymean = 0.

        nsamples = X.shape[0]
        alpha = self.alpha * nsamples

        if self.coef_ is None:
            self.coef_ = np.zeros(X.shape[1], dtype=np.float64)

        self.coef_, self.dual_gap_, self.eps_ = \
                    lasso_coordinate_descent(self.coef_, alpha, X, Y, maxit, \
                    10, self.tol)

        self.intercept_ = self._ymean - np.dot(self._xmean, self.coef_)

        # TODO: why not define a method rsquared that computes this ?
        self.compute_rsquared(X, Y)

        if self.dual_gap_ > self.eps_:
            warnings.warn('Objective did not converge, you might want to increase the number of interations')

        # return self for chaining fit and predict calls
        return self

    def __repr__(self):
        return "Lasso Coordinate Descent"


class ElasticNet(LinearModel):
    """Linear Model trained with L1 and L2 prior as regularizer

    rho=1 is the lasso penalty. Currently, rho <= 0.01 is not
    reliable, unless you supply your own sequence of alpha.

    Parameters
    ----------
    alpha : double
        TODO
    rho : double
        The ElasticNet mixing parameter, with 0 < rho <= 1.
    """

    def __init__(self, alpha=1.0, rho=0.5, coef=None, tol=1e-4):
        super(ElasticNet, self).__init__(coef)
        self.alpha = alpha
        self.rho = rho
        self.tol = tol

    def fit(self, X, Y, intercept=True, maxit=1000):
        """Fit Elastic Net model with coordinate descent"""
        X = np.asanyarray(X, dtype=np.float64)
        Y = np.asanyarray(Y, dtype=np.float64)

        self._intercept = intercept
        if self._intercept:
            self._xmean = X.mean(axis=0)
            self._ymean = Y.mean(axis=0)
            X = X - self._xmean
            Y = Y - self._ymean
        else:
            self._xmean = 0
            self._ymean = 0

        if self.coef_ is None:
            self.coef_ = np.zeros(X.shape[1], dtype=np.float64)

        nsamples = X.shape[0]
        alpha = self.alpha * self.rho * nsamples
        beta = self.alpha * (1.0 - self.rho) * nsamples
        self.coef_, self.dual_gap_, self.eps_ = \
                enet_coordinate_descent(self.coef_, alpha, beta, X, Y,
                                        maxit, 10, self.tol)

        self.intercept_ = self._ymean - np.dot(self._xmean, self.coef_)

        self.compute_rsquared(X, Y)

        if self.dual_gap_ > self.eps_:
            warnings.warn('Objective did not converge, you might want to increase the number of interations')

        # return self for chaining fit and predict calls
        return self

    def __repr__(self):
        return "ElasticNet cd"


#########################################################################
#                                                                       #
# The following classes store linear models along a regularization path #
#                                                                       #
#########################################################################

def lasso_path(X, y, eps=1e-3, n_alphas=100, alphas=None, **fit_kwargs):
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

    fit_kwargs : kwargs, optional
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
    coef = None # init coef_
    models = []
    for alpha in alphas:
        model = Lasso(coef=coef, alpha=alpha)
        model.fit(X, y, **fit_kwargs)
        coef = model.coef_.copy()
        models.append(model)
    return models

def enet_path(X, y, rho=0.5, eps=1e-3, n_alphas=100, alphas=None, **fit_kwargs):
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

    fit_kwargs : kwargs
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
    coef = None # init coef_
    models = []
    for alpha in alphas:
        model = ElasticNet(coef=coef, alpha=alpha, rho=rho)
        model.fit(X, y, **fit_kwargs)
        coef = model.coef_.copy()
        models.append(model)
    return models

def optimized_lasso(X, y, cv=None, n_alphas=100, alphas=None,
                                eps=1e-3, **fit_kwargs):
    """Compute an optimized Lasso model

    Parameters
    ----------
    X : numpy array of shape [nsamples,nfeatures]
        Training data

    Y : numpy array of shape [nsamples]
        Target values

    rho : float, optional
        float between 0 and 1 passed to ElasticNet (scaling between
        l1 and l2 penalties)

    cv : cross-validation generator, optional
         If None, KFold will be used.

    eps : float, optional
        Length of the path. eps=1e-3 means that
        alpha_min / alpha_max = 1e-3.

    n_alphas : int, optional
        Number of alphas along the regularization path

    alphas : numpy array, optional
        List of alphas where to compute the models.
        If None alphas are set automatically

    fit_kwargs : kwargs
        keyword arguments passed to the Lasso fit method

    Returns
    -------
    model : a Lasso instance model

    Notes
    -----
    See examples/lasso_path_with_crossvalidation.py for an example.
    """
    # Start to compute path on full data
    models = lasso_path(X, y, eps=eps, n_alphas=n_alphas, alphas=alphas,
                                **fit_kwargs)

    n_samples = y.size
    # init cross-validation generator
    cv = cv if cv else KFold(n_samples, 5)

    alphas = [model.alpha for model in models]
    n_alphas = len(alphas)
    # Compute path for all folds and compute MSE to get the best alpha
    mse_alphas = np.zeros(n_alphas)
    for train, test in cv:
        models_train = lasso_path(X[train], y[train], eps, n_alphas,
                                    alphas=alphas, **fit_kwargs)
        for i_alpha, model in enumerate(models_train):
            y_ = model.predict(X[test])
            mse_alphas[i_alpha] += ((y_ - y[test]) ** 2).mean()

    i_best_alpha = np.argmin(mse_alphas)
    return models[i_best_alpha]

def optimized_enet(X, y, rho=0.5, cv=None, n_alphas=100, alphas=None,
                                 eps=1e-3, **fit_kwargs):
    """Returns an ElasticNet model that is optimized in the sense of
    cross validation.

    Parameters
    ----------
    X : numpy array of shape [nsamples,nfeatures]
        Training data

    Y : numpy array of shape [nsamples]
        Target values

    rho : float, optional
        float between 0 and 1 passed to ElasticNet (scaling between
        l1 and l2 penalties)

    cv : cross-validation generator, optional
         If None, KFold will be used.

    eps : float, optional
        Length of the path. eps=1e-3 means that
        alpha_min / alpha_max = 1e-3.

    n_alphas : int, optional
        Number of alphas along the regularization path

    alphas : numpy array, optional
        List of alphas where to compute the models.
        If None alphas are set automatically

    fit_kwargs : kwargs
        keyword arguments passed to the ElasticNet fit method

    Returns
    -------
    model : a Lasso instance model

    Notes
    -----
    See examples/lasso_path_with_crossvalidation.py for an example.
    """
    # Start to compute path on full data
    models = enet_path(X, y, rho=rho, eps=eps, n_alphas=n_alphas,
                                alphas=alphas, **fit_kwargs)

    n_samples = y.size
    # init cross-validation generator
    cv = cv if cv else KFold(n_samples, 5)

    alphas = [model.alpha for model in models]
    n_alphas = len(alphas)
    # Compute path for all folds and compute MSE to get the best alpha
    mse_alphas = np.zeros(n_alphas)
    for train, test in cv:
        models_train = enet_path(X[train], y[train], rho=rho,
                                    alphas=alphas, eps=eps, n_alphas=n_alphas,
                                    **fit_kwargs)
        for i_alpha, model in enumerate(models_train):
            y_ = model.predict(X[test])
            mse_alphas[i_alpha] += ((y_ - y[test]) ** 2).mean()

    i_best_alpha = np.argmin(mse_alphas)
    return models[i_best_alpha]

class LinearModelCV(LinearModel):
    """Base class for iterative model fitting along a regularization path"""

    def __init__(self, eps=1e-3, n_alphas=100, alphas=None):
        self.eps = eps
        self.n_alphas = n_alphas
        self.alphas = alphas

    def fit(self, X, y, cv=None, **fit_kwargs):
        """Fit linear model with coordinate descent along decreasing alphas
        """
        X = np.asanyarray(X, dtype=np.float64)
        y = np.asanyarray(y, dtype=np.float64)

        self.path_ = []
        n_samples = X.shape[0]

        model = self.path(X, y, cv=cv, eps=self.eps, n_alphas=self.n_alphas,
                                    **fit_kwargs)

        self.__dict__.update(model.__dict__)
        return self

class LassoCV(LinearModelCV):
    """Lasso linear model with iterative fitting along a regularization path

    The best model is then sselected by cross-validation.
    """

    @property
    def path(self):
        return optimized_lasso

class ElasticNetCV(LinearModelCV):
    """Elastic Net model with iterative fitting along a regularization path"""

    @property
    def path(self):
        return optimized_enet

    def __init__(self, rho=0.5, **kwargs):
        super(ElasticNetCV, self).__init__(**kwargs)
        self.rho = rho


class LeastAngleRegression (LinearModel):
    """
    LeastAngleRegression using the LARS algorithm



    WARNING: this is alpha quality, use it at your own risk
    TODO: add intercept

    coef_ is the **normalized** coefficient.

    Notes
    -----
    predict does only work correctly in the case of normalized
    predictors.
    
    """

    def fit (self, X, Y, intercept=True, n_features=None, normalize=True):
        """


        n_features : int
            number of features to get into the model

        TODO: resize (not create) arrays, check shape,
            add a real intercept
        """
        X  = np.asanyarray(X, dtype=np.float64, order='C')
        _Y = np.asanyarray(Y, dtype=np.float64, order='C')

        if Y is _Y: Y = _Y.copy()
        else: Y = _Y

        if n_features is None:
            n_features = min(*X.shape) - 1

        sum_k = n_features * (n_features + 1) /2
        self.alphas_ = np.zeros(n_features + 1, dtype=np.float64)
        self._cholesky = np.zeros(sum_k, dtype=np.float64)
        self.beta_ = np.zeros(sum_k , dtype=np.float64)
        coef_row = np.zeros(sum_k, dtype=np.int32)
        coef_col = np.zeros(sum_k, dtype=np.int32)


        if normalize:
            self._xmean = X.mean(0)
            self._ymean = Y.mean(0)
            X = X - self._xmean
            Y = Y - self._ymean
            self._norms = np.apply_along_axis (np.linalg.norm, 0, X)
            X /= self._norms

        lars_fit_wrap(0, X, Y, self.beta_, self.alphas_, coef_row,
                      coef_col, self._cholesky, n_features)

        self.coef_path_ = sp.coo_matrix((self.beta_,
                                        (coef_row, coef_col)),
                                        shape=(X.shape[1], n_features+1)).todense()

        self.coef_ = np.ravel(self.coef_path_[:, n_features])

        # self.intercept_ = self._ymean - np.dot(self._xmean, self.coef_)

        return self


    def predict(self, X, normalize=True):
        """
        TODO: add intercept
        """
        X = np.asanyarray(X)
        if normalize:
            X -= self._xmean
            X /= self._norms
        return  np.dot(X, self.coef_)

        

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
    init(obs)
        Initialize model parameters from `obs`.
    fit(obs)
        Estimate model parameters from `obs` using the EM algorithm.

    Examples
    --------
    >>> gmm = GMM(2, ndim=1)
    >>> obs = numpy.concatenate((numpy.random.randn(100, 1),
    ...                          10 + numpy.random.randn(300, 1)))
    >>> # Roughly initialize the model parameters.
    >>> gmm.init(obs)
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

    def __init__(self, nstates, cvtype='diag'):
        """Create a Gaussian mixture model

        Initializes parameters such that every mixture component has
        zero mean and identity covariance.

        Parameters
        ----------
        ndim : int
            Dimensionality of the mixture components.
        nstates : int
            Number of mixture components.
        cvtype : string (read-only)
            String describing the type of covariance parameters to
            use.  Must be one of 'spherical', 'tied', 'diag', 'full'.
            Defaults to 'diag'.
        """

        self._nstates = nstates
        self._cvtype = cvtype

        if not cvtype in ['spherical', 'tied', 'diag', 'full']:
            raise ValueError('bad cvtype')

        self.weights = np.tile(1.0 / nstates, nstates)
        self.labels = [None] * nstates

    # Read-only properties.
    @property
    def cvtype(self):
        """Covariance type of the model.

        Must be one of 'spherical', 'tied', 'diag', 'full'.
        """
        return self._cvtype

    @property
    def nstates(self):
        """Number of mixture components in the model."""
        return self._nstates

    @property
    def covars(self):
        """
        Return covars as a full matrix
        """
        if self.cvtype == 'full':
            return self._covars
        elif self.cvtype == 'diag':
            return [np.diag(cov) for cov in self._covars]
        elif self.cvtype == 'tied':
            print np.tile(self._covars, 2)
            return [self._covars]*self._nstates
        elif self.cvtype == 'spherical':
            return [np.eye(self._nstates) * f for f in self._covars]

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
        lpr = (lmvnpdf(obs, self.means, self._covars, self._cvtype)
               + self._log_weights)
        logprob = logsum(lpr, axis=1)
        posteriors = np.exp(lpr - logprob[:,np.newaxis])
        return logprob, posteriors


    def predict (self, X):
        """
        Predict label for data

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
        
    def rvs(self, ndim, n=1):
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

        obs = np.empty((n, ndim))
        for x in xrange(n):
            rand = np.random.rand()
            c = (weight_cdf > rand).argmax()
            if self._cvtype == 'tied':
                cv = self._covars
            else:
                cv = self._covars[c]
            obs[x] = sample_gaussian(self.means[c], cv, self._cvtype)
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
            self.means, tmp = cluster.vq.kmeans2(X, self._nstates, **kwargs)

        if 'w' in init_params:
            self.weights = np.tile(1.0 / self._nstates, self._nstates)

        if 'c' in init_params:
            cv = np.cov(X.T)
            if not cv.shape:
                cv.shape = (1, 1)
            self._covars = _distribute_covar_matrix_to_match_cvtype(
                cv, self._cvtype, self._nstates)


        covar_mstep_fun = {'spherical': _covar_mstep_spherical,
                           'diag': _covar_mstep_diag,
                           #'tied': _covar_mstep_tied,
                           #'full': _covar_mstep_full,
                           'tied': _covar_mstep_slow,
                           'full': _covar_mstep_slow,
                           }[self._cvtype]

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
            w = posteriors.sum(axis=0)
            avg_obs = np.dot(posteriors.T, X)
            norm = 1.0 / w[:,np.newaxis]
            
            if 'w' in params:
                self.weights = w / w.sum()
            if 'm' in params:
                self.means = avg_obs * norm
            if 'c' in params:
                self._covars = covar_mstep_fun(self, X, posteriors,
                                               avg_obs, norm, min_covar)

        return logprob

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
    avg_means2 = gmm.means**2 
    avg_obs_means = gmm.means * avg_obs * norm
    return avg_obs2 - 2 * avg_obs_means + avg_means2 + min_covar

def _covar_mstep_spherical(*args):
    return _covar_mstep_diag(*args).mean(axis=1)

def _covar_mstep_full(gmm, obs, posteriors, avg_obs, norm, min_covar):
    print "THIS IS BROKEN"
    # Eq. 12 from K. Murphy, "Fitting a Conditional Linear Gaussian
    # Distribution"
    avg_obs2 = np.dot(obs.T, obs)
    #avg_obs2 = np.dot(obs.T, avg_obs)
    ndim = obs.shape[1]
    cv = np.empty((gmm._nstates, ndim, ndim))
    for c in xrange(gmm._nstates):
        wobs = obs.T * posteriors[:,c]
        avg_obs2 = np.dot(wobs, obs) / posteriors[:,c].sum()
        mu = gmm.means[c][np.newaxis]
        cv[c] = (avg_obs2 - np.dot(mu, mu.T)
                 + min_covar * np.eye(ndim))
    return cv

def _covar_mstep_tied2(*args):
    return _covar_mstep_full(*args).mean(axis=0)

def _covar_mstep_tied(gmm, obs, posteriors, avg_obs, norm, min_covar):
    print "THIS IS BROKEN"
    # Eq. 15 from K. Murphy, "Fitting a Conditional Linear Gaussian
    # Distribution"
    ndim = obs.shape[1]
    avg_obs2 = np.dot(obs.T, obs)
    avg_means2 = np.dot(gmm.means.T, gmm.means)
    return (avg_obs2 - avg_means2 + min_covar * np.eye(ndim))

def _covar_mstep_slow(gmm, obs, posteriors, avg_obs, norm, min_covar):
    w = posteriors.sum(axis=0)
    covars = np.zeros(gmm._covars.shape)
    for c in xrange(gmm._nstates):
        mu = gmm.means[c]
        #cv = np.dot(mu.T, mu)
        ndim = obs.shape[1]
        avg_obs2 = np.zeros((ndim, ndim))
        for t,o in enumerate(obs):
            avg_obs2 += posteriors[t,c] * np.outer(o, o)
        cv = (avg_obs2 / w[c]
              - 2 * np.outer(avg_obs[c] / w[c], mu)
              + np.outer(mu, mu)
              + min_covar * np.eye(ndim))
        if gmm.cvtype == 'spherical':
            covars[c] = np.diag(cv).mean()
        elif gmm.cvtype == 'diag':
            covars[c] = np.diag(cv)
        elif gmm.cvtype == 'full':
            covars[c] = cv
        elif gmm.cvtype == 'tied':
            covars += cv / gmm._nstates
    return covars

# $Id$

import numpy as np
import exceptions, warnings
import scipy.linalg as linalg

class LDA(object):
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
    <scikits.learn.lda.LDA object at 0x...>
    >>> print clf.predict([[-0.8, -1]])
    [1]

    See also
    --------
    QDA

    """
    def __init__(self, priors = None, use_svd = True):
        #use_svd : if True, use linalg.svd alse use computational
        #          trick with covariance matrix
        if not priors is None:
            self.priors = np.asarray(priors)
        else: self.priors = None
        self.use_svd = use_svd

    def fit(self, X, y, tol = 1.0e-4):
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
        if self.use_svd == True:
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
        X = np.asarray(X)
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
from .ball_tree import BallTree

class Neighbors:
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
  >>> neigh.fit(samples, labels) #doctest: +ELLIPSIS
  <scikits.learn.neighbors.Neighbors instance at 0x...>
  >>> print neigh.predict([[0,0,0]])
  [ 0.]
  """

  def __init__(self, k = 5, window_size = 1):
    """
    Internally uses the ball tree datastructure and algorithm for fast
    neighbors lookups on high dimensional datasets.
    """
    self._k = k
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
    >>> neigh.fit(samples, labels) #doctest: +ELLIPSIS
    <scikits.learn.neighbors.Neighbors instance at 0x...>
    >>> print neigh.kneighbors([1., 1., 1.])
    (array(0.5), array(2))

    As you can see, it returns [0.5], and [2], which means that the
    element is at distance 0.5 and is the third element of samples
    (indexes start at 0). You can also query for multiple points:

    >>> print neigh.kneighbors([[0., 1., 0.], [1., 0., 1.]])
    (array([ 0.5       ,  1.11803399]), array([1, 2]))

    """
    if k is None: k = self._k
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
    >>> neigh.fit(samples, labels) #doctest: +ELLIPSIS
    <scikits.learn.neighbors.Neighbors instance at 0x...>
    >>> print neigh.predict([.2, .1, .2])
    0
    >>> print neigh.predict([[0., -1., 0.], [3., 2., 0.]])
    [0 1]
    """
    T = np.asanyarray(T)
    if k is None: k = self._k
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

"""
Machine Learning module for python.
"""

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
from ConfigParser import ConfigParser

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    from numpy.distutils.system_info import get_info, get_standard_file, BlasNotFoundError
    config = Configuration('learn',parent_package,top_path)

    site_cfg  = ConfigParser()
    site_cfg.read(get_standard_file('site.cfg'))

    config.add_subpackage('em')
    config.add_subpackage('datasets')
    config.add_subpackage('feature_selection')
    config.add_subpackage('utils')

    # libsvm
    libsvm_includes = [numpy.get_include()]
    libsvm_libraries = []
    libsvm_library_dirs = []
    libsvm_sources = [join('src', '_libsvm.c')]

    if site_cfg.has_section('libsvm'):
        libsvm_includes.append(site_cfg.get('libsvm', 'include_dirs'))
        libsvm_libraries.append(site_cfg.get('libsvm', 'libraries'))
        libsvm_library_dirs.append(site_cfg.get('libsvm', 'library_dirs'))
    else:
        libsvm_sources.append(join('src', 'svm.cpp'))

    config.add_extension('_libsvm',
                         sources=libsvm_sources,
                         include_dirs=libsvm_includes,
                         libraries=libsvm_libraries,
                         library_dirs=libsvm_library_dirs,
                         depends=[join('src', 'svm.h'),
                                 join('src', 'libsvm_helper.c'),
                                  ])

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
    blas_lib = blas_info.pop('libraries', ['blas'])
    extra_compile_args = blas_info.pop('extra_compile_args', [])

    if not blas_info:
        config.add_library('blas', blas_sources)
        warnings.warn(BlasNotFoundError.__doc__)

    config.add_extension('_liblinear',
                         sources=liblinear_sources,
                         libraries = blas_lib,
                         include_dirs=['src',
                                       numpy.get_include()],
                         depends=[join('src', 'linear.h'),
                                  join('src', 'tron.h'),
                                  join('src', 'blas', 'blas.h'),
                                  join('src', 'blas', 'blasp.h')],
                         extra_compile_args=extra_compile_args)
    ## end liblinear module

    # minilear needs cblas, fortran-compiled BLAS will not be sufficient
    if not blas_info or (
        ('NO_ATLAS_INFO', 1) in blas_info.get('define_macros', [])):
        config.add_library('cblas',
                           sources=[
                               join('src', 'cblas', '*.c'),
                               ]
                           )

    minilearn_sources = [
        join('src', 'minilearn', 'lars.c'),
        join('src', 'minilearn', '_minilearn.c')]

    extra_compile_args += ['-std=c99', '-g']

    config.add_extension('_minilearn',
                         sources=minilearn_sources,
                         libraries = ['blas', 'cblas'],
                         include_dirs=[join('src', 'minilearn'),
                                       join('src', 'cblas'),
                                       numpy.get_include()],
                         extra_compile_args=extra_compile_args,
                         )

    config.add_extension('ball_tree',
                         sources=[join('src', 'BallTree.cpp')],
                         include_dirs=[numpy.get_include()]
                         )

    config.add_extension('cd_fast',
                         sources=[join('src', 'cd_fast.c')],
                         # libraries=['m'],
                         include_dirs=[numpy.get_include()])


    config.add_subpackage('utils')

    # add the test directory
    config.add_data_dir('tests')

    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())

"""
Univariate features selection.
"""

# Authors: V. Michel, B. Thirion, G. Varoquaux, A. Gramfort, E. Duchesnay
# License: BSD 3 clause

import numpy as np
from scipy import stats

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


class UnivariateFilter(object):

    def __init__(self, score_func):
        """
        Initialize the univariate feature selection.
        Func : function taking two arrays X and y, and returning an array.
        score_func returning both scores and pvalues
        """
        assert callable(score_func), ValueError(
                "The score function should be a callable, '%s' (type %s) "
                "was passed." % (score_func, type(score_func))
            )
        self.score_func = score_func

    def fit(self,X,y):
        """
        Evaluate the function
        """
        _scores = self.score_func(X, y)
        self._scores = _scores[0]
        self._pvalues = _scores[1]
        #self._rank = np.argsort(self._pvalues)
        return self

    def get_selected_features(self):
        """
        Returns the indices of the selected features
        """
        return self._support


######################################################################
# Specific filters
######################################################################

class SelectPercentile(UnivariateFilter):
    """
    Filter : Select the best percentile of the p_values
    """
    def transform(self,X,percentile):
        """
        Transform the data.
        """
        assert percentile<=100, ValueError('percentile should be \
                            between 0 and 100 (%f given)' %(percentile))
        alpha = stats.scoreatpercentile(self._pvalues, percentile)
        self._support = (p_values <= alpha)
        return X[:,self._support]

class SelectKBest(UnivariateFilter):
    """
    Filter : Select the k lowest p-values
    """
    def transform(self,X,k):
        assert k<=len(self._pvalues), ValueError('cannot select %d features'
                                    ' among %d ' % (k, len(self._pvalues)))
        alpha = np.sort(self._pvalues)[k-1]
        self._support = (self._pvalues <= alpha)
        return X[:,self._support]


class SelectFpr(UnivariateFilter):
    """
    Filter : Select the pvalues below alpha
    """
    def transform(self,X,alpha):
        self._support = (self._pvalues < alpha)
        return X[:,self._support]


class SelectFdr(UnivariateFilter):
    """
    Filter : Select the p-values corresponding to an estimated false
    discovery rate of alpha. This uses the Benjamini-Hochberg procedure
    """
    def transform(self,X,alpha):
        sv = np.sort(self._pvalues)
        threshold = sv[sv < alpha*np.arange(len(self._pvalues))].max()
        self._support = (self._pvalues < threshold)
        return X[:,self._support]


class SelectFwe(UnivariateFilter):
    """
    Filter : Select the p-values corresponding to a corrected p-value of alpha
    """
    def transform(self,X,alpha):
        self._support = (self._pvalues < alpha/len(self._pvalues))
        return X[:,self._support]



if __name__ == "__main__":
    import scikits.learn.datasets.samples_generator as sg
    from scikits.learn.svm import SVR, SVC

    X,y = sg.sparse_uncorrelated(50,100)
    univariate_filter = SelectKBest(f_regression)
    X_r = univariate_filter.fit(X, y).transform(X, k=5)
    clf = SVR(kernel='linear', C=1.)
    y_ = clf.fit(X_r, y).predict(X_r)
    print univariate_filter._support.astype(int)

    ### now change k
    X_r = univariate_filter.transform(X, k=2)
    y_ = clf.fit(X_r, y).predict(X)
    print univariate_filter._support.astype(int)

"""
Utilities for cross validation.
"""

# Author: Alexandre Gramfort <alexandre.gramfort@inria.fr>,
#         Gael Varoquaux    <gael.varoquaux@normalesup.org>
# License: BSD Style.

# $Id$

import numpy as np
from scikits.learn.utils.extmath import factorial, combinations

################################################################################
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


################################################################################
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


################################################################################
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
        j = np.ceil(n/k)

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

################################################################################
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


def split(train_indices, test_indices, *args):
    """
    For each arg return a train and test subsets defined by indexes provided
    in train_indices and test_indices
    """
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


class BaseLibsvm(object):
    """
    Base class for classifiers that use libsvm as library for
    support vector machine classification and regression.

    Should not be used directly, use derived classes instead
    """

    _kernel_types = ['linear', 'poly', 'rbf', 'sigmoid', 'precomputed']
    _svm_types = ['c_svc', 'nu_svc', 'one_class', 'epsilon_svr', 'nu_svr']

    def __init__(self, impl, kernel, degree, gamma, coef0, cache_size,
                 eps, C, nu, p, shrinking, probability):
        self.solver_type = self._svm_types.index(impl)
        if callable(kernel):
            self._kernfunc = kernel
            self.kernel = -1
        else: self.kernel = self._kernel_types.index(kernel)
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
        self.support_ = np.empty((0,0), dtype=np.float64, order='C')
        self.dual_coef_ = np.empty((0,0), dtype=np.float64, order='C')
        self.intercept_ = np.empty(0, dtype=np.float64, order='C')

        # only used in classification
        self.nSV_ = np.empty(0, dtype=np.int32, order='C')


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

        self.weight = np.asarray(class_weight.values(), dtype=np.float64, order='C')
        self.weight_label = np.asarray(class_weight.keys(), dtype=np.int32, order='C')

        # in the case of precomputed kernel given as a function, we
        # have to compute explicitly the kernel matrix
        if self.kernel < 0:
            # TODO: put keyword copy to copy on demand
            _X = np.asanyarray(self._kernfunc(X, X), dtype=np.float64, order='C')
             # you must store a reference to X to compute the kernel in predict
             # there's a way around this, but it involves patching libsvm
            self.__Xfit = X
            kernel_type = 4
        else:
            _X = X
            kernel_type = self.kernel

        # check dimensions
        if _X.shape[0] != Y.shape[0]: raise ValueError("Incompatible shapes")

        if (self.gamma == 0): self.gamma = 1.0/_X.shape[0]
        self.label_, self.probA_, self.probB_ = _libsvm.train_wrap(_X, Y,
                 self.solver_type, kernel_type, self.degree,
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

        # in the case of precomputed kernel given as function, we have
        # to manually calculate the kernel matrix ...
        if self.kernel < 0:
            _T = np.asanyarray(self._kernfunc(T, self.__Xfit), dtype=np.float64, order='C')
            kernel_type = 4
        else:
            _T = T
            kernel_type = self.kernel
        return _libsvm.predict_from_model_wrap(_T, self.support_,
                      self.dual_coef_, self.intercept_,
                      self.solver_type, kernel_type, self.degree,
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
            raise ValueError("probability estimates must be enabled to use this method")
        T = np.atleast_2d(np.asanyarray(T, dtype=np.float64, order='C'))
        pprob = _libsvm.predict_prob_from_model_wrap(T, self.support_,
                      self.dual_coef_, self.intercept_, self.solver_type,
                      self.kernel, self.degree, self.gamma,
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
        return _libsvm.predict_margin_from_model_wrap(T, self.support_,
                      self.dual_coef_, self.intercept_, self.solver_type,
                      self.kernel, self.degree, self.gamma,
                      self.coef0, self.eps, self.C, 
                      self.weight_label, self.weight,
                      self.nu, self.cache_size,
                      self.p, self.shrinking, self.probability,
                      self.nSV_, self.label_,
                      self.probA_, self.probB_)



    @property
    def coef_(self):
        if self._kernel_types[self.kernel] != 'linear':
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

    probability: boolean, optional (False by default)
        especify if probability estimates must be enabled
        must be enabled prior to calling prob_predict

    coef0 : float, optional

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
    >>> clf.fit(X, Y)    #doctest: +ELLIPSIS
    <scikits.learn.svm.SVC object at 0x...>
    >>> print clf.predict([[-0.8, -1]])
    [ 1.]

    See also
    --------
    SVR
    """

    def __init__(self, impl='c_svc', kernel='rbf', degree=3, gamma=0.0, coef0=0.0,
                 cache_size=100.0, eps=1e-3, C=1.0, 
                 nu=0.5, p=0.1, shrinking=True, probability=False):
        BaseLibsvm.__init__(self, impl, kernel, degree, gamma, coef0,
                         cache_size, eps, C, nu, p,
                         shrinking, probability)

class SVR(BaseLibsvm):
    """
    Support Vector Regression.

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
                 cache_size=100.0, eps=1e-3, C=1.0, 
                 nu=0.5, p=0.1, shrinking=True, probability=False):
        BaseLibsvm.__init__(self, 'epsilon_svr', kernel, degree, gamma, coef0,
                         cache_size, eps, C, nu, p,
                         shrinking, probability)

class OneClassSVM(BaseLibsvm):
    """
    Outlayer detection

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


class LinearSVC(object):
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
        self.solver_type = "P%s_L%s_D%d"  % (
            penalty.upper(), loss.upper(), int(dual))
        if not (self.solver_type in self._solver_type_dict.keys()):
            raise ValueError('Not supported set of arguments: '
                             + self.solver_type)
        self.eps = eps
        self.C = C

    def fit(self, X, Y):
        """
        X : array-like, shape = [nsamples, nfeatures]
            Training vector, where nsamples in the number of samples and
            nfeatures is the number of features.
        Y : array, shape = [nsamples]
            Target vector relative to X
        """
        
        X = np.asanyarray(X, dtype=np.float64, order='C')
        Y = np.asanyarray(Y, dtype=np.int32, order='C')
        self.raw_coef, self.label_, self.bias_ = \
                       _liblinear.train_wrap(X, Y,
                       self._solver_type_dict[self.solver_type],
                       self.eps, 1.0, self.C, self._weight_label,
                       self._weight)
        return self

    def predict(self, T):
        T = np.atleast_2d(np.asanyarray(T, dtype=np.float64, order='C'))
        return _liblinear.predict_wrap(T, self.raw_coef, self._solver_type_dict[self.solver_type],
                                      self.eps, self.C,
                                      self._weight_label,
                                      self._weight, self.label_,
                                      self.bias_)

    def predict_proba(self, T):
        raise NotImplementedError('liblinear does not provide this functionality')

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

#! /usr/bin/python
#
# Copyrighted David Cournapeau
# Last Change: Thu Jul 12 04:00 PM 2007 J
"""This module implements various basic functions related to multivariate
gaussian, such as pdf estimation, confidence interval/ellipsoids, etc..."""

__docformat__ = 'restructuredtext'

import numpy as N
import numpy.linalg as lin
#from numpy.random import randn
from scipy.stats import chi2
import misc

# Error classes
class DenError(Exception):
    """Base class for exceptions in this module.
    
    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error"""
    def __init__(self, message):
        self.message    = message
        Exception.__init__(self)
    
    def __str__(self):
        return self.message

# The following function do all the fancy stuff to check that parameters
# are Ok, and call the right implementation if args are OK.
def gauss_den(x, mu, va, log = False):
    """Compute multivariate Gaussian density at points x for 
    mean mu and variance va.
    
    :Parameters:
        x : ndarray
            points where to estimate the pdf.  each row of the array is one
            point of d dimension
        mu : ndarray
            mean of the pdf. Should have same dimension d than points in x.
        va : ndarray
            variance of the pdf. If va has d elements, va is interpreted as the
            diagonal elements of the actual covariance matrix. Otherwise,
            should be a dxd matrix (and positive definite).
        log : boolean
            if True, returns the log-pdf instead of the pdf.

    :Returns:
        pdf : ndarray
            Returns a rank 1 array of the pdf at points x.

    Note
    ----
        Vector are row vectors, except va which can be a matrix
        (row vector variance for diagonal variance)."""
    
    lmu  = N.atleast_2d(mu)
    lva  = N.atleast_2d(va)
    lx   = N.atleast_2d(x)
    
    #=======================#
    # Checking parameters   #
    #=======================#
    if len(N.shape(lmu)) != 2:
        raise DenError("mu is not rank 2")
        
    if len(N.shape(lva)) != 2:
        raise DenError("va is not rank 2")
        
    if len(N.shape(lx)) != 2:
        raise DenError("x is not rank 2")
        
    d = N.shape(lx)[1]
    (dm0, dm1) = N.shape(lmu)
    (dv0, dv1) = N.shape(lva)
    
    # Check x and mu same dimension
    if dm0 != 1:
        msg = "mean must be a row vector!"
        raise DenError(msg)
    if dm1 != d:
        msg = "x and mu not same dim"
        raise DenError(msg)
    # Check va and mu same size
    if dv1 != d:
        msg = "mu and va not same dim"
        raise DenError(msg)
    if dv0 != 1 and dv0 != d:
        msg = "va not square"
        raise DenError(msg)

    #===============#
    # Computation   #
    #===============#
    if d == 1:
        # scalar case
        return _scalar_gauss_den(lx[:, 0], lmu[0, 0], lva[0, 0], log)
    elif dv0 == 1:
        # Diagonal matrix case
        return _diag_gauss_den(lx, lmu, lva, log)
    elif dv1 == dv0:
        # full case
        return  _full_gauss_den(lx, lmu, lva, log)
    else:
        raise DenError("variance mode not recognized, this is a bug")

# Those 3 functions do almost all the actual computation
def _scalar_gauss_den(x, mu, va, log):
    """ This function is the actual implementation
    of gaussian pdf in scalar case. It assumes all args
    are conformant, so it should not be used directly
    
    Call gauss_den instead"""
    d       = mu.size
    inva    = 1/va
    fac     = (2*N.pi) ** (-d/2.0) * N.sqrt(inva)
    inva    *= -0.5
    y       = ((x-mu) ** 2) * inva
    if not log:
        y   = fac * N.exp(y)
    else:
        y   += N.log(fac)

    return y
    
def _diag_gauss_den(x, mu, va, log):
    """ This function is the actual implementation
    of gaussian pdf in scalar case. It assumes all args
    are conformant, so it should not be used directly
    
    Call gauss_den instead"""
    # Diagonal matrix case
    d   = mu.size
    #n   = x.shape[0]
    if not log:
        inva = 1/va[0]
        fac = (2*N.pi) ** (-d/2.0) * N.prod(N.sqrt(inva))
        inva *= -0.5
        x = x - mu
        x **= 2
        y = fac * N.exp(N.dot(x, inva))
    else:
        # XXX optimize log case as non log case above
        y = _scalar_gauss_den(x[:, 0], mu[0, 0], va[0, 0], log)
        for i in range(1, d):
            y +=  _scalar_gauss_den(x[:, i], mu[0, i], va[0, i], log)
    return y

def _full_gauss_den(x, mu, va, log):
    """ This function is the actual implementation
    of gaussian pdf in full matrix case. 
    
    It assumes all args are conformant, so it should 
    not be used directly Call gauss_den instead
    
    Does not check if va is definite positive (on inversible 
    for that matter), so the inverse computation and/or determinant
    would throw an exception."""
    d       = mu.size
    inva    = lin.inv(va)
    fac     = 1 / N.sqrt( (2*N.pi) ** d * N.fabs(lin.det(va)))

    # we are using a trick with sum to "emulate" 
    # the matrix multiplication inva * x without any explicit loop
    #y   = -0.5 * N.sum(N.dot((x-mu), inva) * (x-mu), 1)
    y   = -0.5 * N.dot(N.dot((x-mu), inva) * (x-mu), 
                       N.ones((mu.size, 1), x.dtype))[:, 0]

    if not log:
        y   = fac * N.exp(y)
    else:
        y   = y + N.log(fac)
 
    return y

# To get coordinatea of a confidence ellipse from multi-variate gaussian pdf
def gauss_ell(mu, va, dim = misc.DEF_VIS_DIM, npoints = misc.DEF_ELL_NP, \
        level = misc.DEF_LEVEL):
    """Given a mean and covariance for multi-variate
    gaussian, returns the coordinates of the confidense ellipsoid.
    
    Compute npoints coordinates for the ellipse of confidence of given level
    (all points will be inside the ellipsoides with a probability equal to
    level).
    
    :Parameters:
        mu : ndarray
            mean of the pdf
        va : ndarray
            variance of the pdf
        dim : sequence
            sequences of two integers which represent the dimensions where to
            project the ellipsoid.
        npoints: int
            number of points to generate for the ellipse.
        level : float
            level of confidence (between 0 and 1).

    :Returns:
        Returns the coordinate x and y of the ellipse."""
    if level >= 1 or level <= 0:
        raise ValueError("level should be a scale strictly between 0 and 1.""")
    
    mu = N.atleast_1d(mu)
    va = N.atleast_1d(va)
    d = N.shape(mu)[0]
    c = N.array(dim)

    if N.any(c < 0) or N.any(c >= d):
        raise ValueError("dim elements should be >= 0 and < %d (dimension"\
                " of the variance)" % d)
    if N.size(mu) == N.size(va):
        mode    = 'diag'
    else:
        if N.ndim(va) == 2:
            if N.shape(va)[0] == N.shape(va)[1]:
                mode    = 'full'
            else:
                raise DenError("variance not square")
        else:
            raise DenError("mean and variance are not dim conformant")

    # When X is a sample from multivariante N(mu, sigma), (X-mu)Sigma^-1(X-mu)
    # follows a Chi2(d) law. Here, we only take 2 dimension, so Chi2 with 2
    # degree of freedom (See Wasserman. This is easy to see with characteristic
    # functions)
    chi22d  = chi2(2)
    mahal   = N.sqrt(chi22d.ppf(level))
    
    # Generates a circle of npoints
    theta   = N.linspace(0, 2 * N.pi, npoints)
    circle  = mahal * N.array([N.cos(theta), N.sin(theta)])

    # Get the dimension which we are interested in:
    mu  = mu[c]
    if mode == 'diag':
        va      = va[c]
        elps    = N.outer(mu, N.ones(npoints))
        elps    += N.dot(N.diag(N.sqrt(va)), circle)
    elif mode == 'full':
        va  = va[c, :][:, c]
        # Method: compute the cholesky decomp of each cov matrix, that is
        # compute cova such as va = cova * cova' 
        # WARN: scipy is different than matlab here, as scipy computes a lower
        # triangular cholesky decomp: 
        #   - va = cova * cova' (scipy)
        #   - va = cova' * cova (matlab)
        # So take care when comparing results with matlab !
        cova    = lin.cholesky(va)
        elps    = N.outer(mu, N.ones(npoints))
        elps    += N.dot(cova, circle)
    else:
        raise ValueError("var mode not recognized")

    return elps[0, :], elps[1, :]

def logsumexp(x):
    """Compute log(sum(exp(x), 1)) while avoiding underflow.
    
    :Parameters:
        x : ndarray
            data in log domain to sum"""
    axis = 1
    mc = N.max(x, axis)
    return mc + N.log(N.sum(N.exp(x-mc[:, N.newaxis]), axis))

def multiple_gauss_den(data, mu, va, log = False):
    """Helper function to generate several Gaussian
    pdf (different parameters) at the same points

    :Parameters:
        data : ndarray
            points where to estimate the pdfs (n,d).
        mu : ndarray
            mean of the pdf, of shape (k,d). One row of dimension d per
            different component, the number of rows k being the number of
            component
        va : ndarray
            variance of the pdf. One row per different component for diagonal
            covariance (k, d), or d rows per component for full matrix pdf
            (k*d,d).
        log : boolean
            if True, returns the log-pdf instead of the pdf.

    :Returns:
        Returns a (n, k) array, each column i being the pdf of the ith mean and
        ith variance."""
    mu = N.atleast_2d(mu)
    va = N.atleast_2d(va)

    k = N.shape(mu)[0]
    n = N.shape(data)[0]
    d = N.shape(mu)[1]
    
    y = N.zeros((k, n))
    if N.size(mu) == N.size(va):
        for i in range(k):
            y[i] = gauss_den(data, mu[i, :], va[i, :], log)
        return y.T
    else:
        for i in range(k):
            y[i] = gauss_den(data, mu[i, :], va[d*i:d*i+d, :], log)
        return y.T

if __name__ == "__main__":
    pass

# Last Change: Mon Jul 02 06:00 PM 2007 J

#========================================================
# Constants used throughout the module (def args, etc...)
#========================================================
# This is the default dimension for representing confidence ellipses
DEF_VIS_DIM = (0, 1)
DEF_ELL_NP = 100
DEF_LEVEL = 0.39

#=====================================================================
# "magic number", that is number used to control regularization and co
# Change them at your risk !
#=====================================================================

# max deviation allowed when comparing double (this is actually stupid,
# I should actually use a number of decimals)
MAX_DBL_DEV    = 1e-10

## # max conditional number allowed
## _MAX_COND       = 1e8
## _MIN_INV_COND   = 1/_MAX_COND
## 
## # Default alpha for regularization
## _DEF_ALPHA  = 1e-1
## 
## # Default min delta for regularization
## _MIN_DBL_DELTA  = 1e-5
## 

class curry:
    def __init__(self, fun, *args, **kwargs):
        self.fun = fun
        self.pending = args[:]
        self.kwargs = kwargs.copy()

    def __call__(self, *args, **kwargs):
        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs

        return self.fun(*(self.pending + args), **kw)

# /usr/bin/python
# Last Change: Tue Jul 17 11:00 PM 2007 J

"""Module implementing GM, a class which represents Gaussian mixtures.

GM instances can be used to create, sample mixtures. They also provide
different plotting facilities, such as isodensity contour for multi dimensional
models, ellipses of confidence."""

__docformat__ = 'restructuredtext'

import numpy as N
from numpy.random import randn, rand
import numpy.linalg as lin
import densities as D
import misc

# Right now, two main usages of a Gaussian Model are possible
#   - init a Gaussian Model with meta-parameters, and trains it
#   - set-up a Gaussian Model to sample it, draw ellipsoides 
#   of confidences. In this case, we would like to init it with
#   known values of parameters. This can be done with the class method 
#   fromval

# TODO:
#   - change bounds methods of GM class instanciations so that it cannot 
#   be used as long as w, mu and va are not set
#   - We have to use scipy now for chisquare pdf, so there may be other
#   methods to be used, ie for implementing random index.
#   - there is no check on internal state of the GM, that is does w, mu and va
#   values make sense (eg singular values) - plot1d is still very rhough. There
#   should be a sensible way to modify the result plot (maybe returns a dic
#   with global pdf, component pdf and fill matplotlib handles). Should be
#   coherent with plot
class GmParamError(Exception):
    """Exception raised for errors in gmm params

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """
    def __init__(self, message):
        Exception.__init__(self)
        self.message    = message
    
    def __str__(self):
        return self.message

class GM:
    """Gaussian Mixture class. This is a simple container class
    to hold Gaussian Mixture parameters (weights, mean, etc...).
    It can also draw itself (confidence ellipses) and samples itself.
    """

    # I am not sure it is useful to have a spherical mode...
    _cov_mod    = ['diag', 'full']

    #===============================
    # Methods to construct a mixture
    #===============================
    def __init__(self, d, k, mode = 'diag'):
        """Init a Gaussian Mixture.

        :Parameters:
            d : int
                dimension of the mixture.
            k : int
                number of component in the mixture.
            mode : string
                mode of covariance

        :Returns:
            an instance of GM.

        Note
        ----

        Only full and diag mode are supported for now.

        :SeeAlso:
            If you want to build a Gaussian Mixture with knowns weights, means
            and variances, you can use GM.fromvalues method directly"""
        if mode not in self._cov_mod:
            raise GmParamError("mode %s not recognized" + str(mode))

        self.d      = d
        self.k      = k
        self.mode   = mode

        # Init to 0 all parameters, with the right dimensions.
        # Not sure this is useful in python from an efficiency POV ?
        self.w   = N.zeros(k)
        self.mu  = N.zeros((k, d))
        if mode == 'diag':
            self.va  = N.zeros((k, d))
        elif mode == 'full':
            self.va  = N.zeros((k * d, d))

        self.__is_valid   = False
        if d > 1:
            self.__is1d = False
        else:
            self.__is1d = True

    def set_param(self, weights, mu, sigma):
        """Set parameters of the model. 
        
        Args should be conformant with metparameters d and k given during
        initialisation.
        
        :Parameters:
            weights : ndarray
                weights of the mixture (k elements)
            mu : ndarray
                means of the mixture. One component's mean per row, k row for k
                components.
            sigma : ndarray
                variances of the mixture. For diagonal models, one row contains
                the diagonal elements of the covariance matrix. For full
                covariance, d rows for one variance.

        Examples
        --------
        Create a 3 component, 2 dimension mixture with full covariance matrices

        >>> w = numpy.array([0.2, 0.5, 0.3])
        >>> mu = numpy.array([[0., 0.], [1., 1.]])
        >>> va = numpy.array([[1., 0.], [0., 1.], [2., 0.5], [0.5, 1]])
        >>> gm = GM(2, 3, 'full')
        >>> gm.set_param(w, mu, va)

        :SeeAlso:
            If you know already the parameters when creating the model, you can
            simply use the method class GM.fromvalues."""
        #XXX: when fromvalues is called, parameters are called twice...
        k, d, mode  = check_gmm_param(weights, mu, sigma)
        if not k == self.k:
            raise GmParamError("Number of given components is %d, expected %d" 
                    % (k, self.k))
        if not d == self.d:
            raise GmParamError("Dimension of the given model is %d, "\
                "expected %d" % (d, self.d))
        if not mode == self.mode and not d == 1:
            raise GmParamError("Given covariance mode is %s, expected %s"
                    % (mode, self.mode))
        self.w  = weights
        self.mu = mu
        self.va = sigma

        self.__is_valid   = True

    @classmethod
    def fromvalues(cls, weights, mu, sigma):
        """This class method can be used to create a GM model
        directly from its parameters weights, mean and variance
        
        :Parameters:
            weights : ndarray
                weights of the mixture (k elements)
            mu : ndarray
                means of the mixture. One component's mean per row, k row for k
                components.
            sigma : ndarray
                variances of the mixture. For diagonal models, one row contains
                the diagonal elements of the covariance matrix. For full
                covariance, d rows for one variance.

        :Returns:
            gm : GM
                an instance of GM.

        Examples
        --------

        >>> w, mu, va   = GM.gen_param(d, k)
        >>> gm  = GM(d, k)
        >>> gm.set_param(w, mu, va)

        and
        
        >>> w, mu, va   = GM.gen_param(d, k)
        >>> gm  = GM.fromvalue(w, mu, va)

        are strictly equivalent."""
        k, d, mode  = check_gmm_param(weights, mu, sigma)
        res = cls(d, k, mode)
        res.set_param(weights, mu, sigma)
        return res
        
    #=====================================================
    # Fundamental facilities (sampling, confidence, etc..)
    #=====================================================
    def sample(self, nframes):
        """ Sample nframes frames from the model.
        
        :Parameters:
            nframes : int
                number of samples to draw.
        
        :Returns:
            samples : ndarray
                samples in the format one sample per row (nframes, d)."""
        if not self.__is_valid:
            raise GmParamError("""Parameters of the model has not been 
                set yet, please set them using self.set_param()""")

        # State index (ie hidden var)
        sti = gen_rand_index(self.w, nframes)
        # standard gaussian samples
        x   = randn(nframes, self.d)        

        if self.mode == 'diag':
            x   = self.mu[sti, :]  + x * N.sqrt(self.va[sti, :])
        elif self.mode == 'full':
            # Faster:
            cho = N.zeros((self.k, self.va.shape[1], self.va.shape[1]))
            for i in range(self.k):
                # Using cholesky looks more stable than sqrtm; sqrtm is not
                # available in numpy anyway, only in scipy...
                cho[i]  = lin.cholesky(self.va[i*self.d:i*self.d+self.d, :])

            for s in range(self.k):
                tmpind      = N.where(sti == s)[0]
                x[tmpind]   = N.dot(x[tmpind], cho[s].T) + self.mu[s]
        else:
            raise GmParamError("cov matrix mode not recognized, "\
                    "this is a bug !")

        return x

    def conf_ellipses(self, dim = misc.DEF_VIS_DIM, npoints = misc.DEF_ELL_NP, 
            level = misc.DEF_LEVEL):
        """Returns a list of confidence ellipsoids describing the Gmm
        defined by mu and va. Check densities.gauss_ell for details

        :Parameters:
            dim : sequence
                sequences of two integers which represent the dimensions where to
                project the ellipsoid.
            npoints : int
                number of points to generate for the ellipse.
            level : float
                level of confidence (between 0 and 1).

        :Returns:
            xe : sequence
                a list of x coordinates for the ellipses (Xe[i] is the array
                containing x coordinates of the ith Gaussian)
            ye : sequence
                a list of y coordinates for the ellipses.

        Examples
        --------
            Suppose we have w, mu and va as parameters for a mixture, then:
            
            >>> gm      = GM(d, k)
            >>> gm.set_param(w, mu, va)
            >>> X       = gm.sample(1000)
            >>> Xe, Ye  = gm.conf_ellipsoids()
            >>> pylab.plot(X[:,0], X[:, 1], '.')
            >>> for k in len(w):
            ...    pylab.plot(Xe[k], Ye[k], 'r')
                
            Will plot samples X draw from the mixture model, and
            plot the ellipses of equi-probability from the mean with
            default level of confidence."""
        if self.__is1d:
            raise ValueError("This function does not make sense for 1d "
                "mixtures.")

        if not self.__is_valid:
            raise GmParamError("""Parameters of the model has not been 
                set yet, please set them using self.set_param()""")

        xe  = []
        ye  = []   
        if self.mode == 'diag':
            for i in range(self.k):
                x, y  = D.gauss_ell(self.mu[i, :], self.va[i, :], 
                        dim, npoints, level)
                xe.append(x)
                ye.append(y)
        elif self.mode == 'full':
            for i in range(self.k):
                x, y  = D.gauss_ell(self.mu[i, :], 
                        self.va[i*self.d:i*self.d+self.d, :], 
                        dim, npoints, level)
                xe.append(x)
                ye.append(y)

        return xe, ye
    
    def check_state(self):
        """Returns true if the parameters of the model are valid. 

        For Gaussian mixtures, this means weights summing to 1, and variances
        to be positive definite.
        """
        if not self.__is_valid:
            raise GmParamError("Parameters of the model has not been"\
                "set yet, please set them using self.set_param()")

        # Check condition number for cov matrix
        if self.mode == 'diag':
            tinfo = N.finfo(self.va.dtype)
            if N.any(self.va < tinfo.eps):
                raise GmParamError("variances are singular")
        elif self.mode == 'full':
            try:
                d = self.d
                for i in range(self.k):
                    N.linalg.cholesky(self.va[i*d:i*d+d, :])
            except N.linalg.LinAlgError:
                raise GmParamError("matrix %d is singular " % i)

        else:
            raise GmParamError("Unknown mode")

        return True

    @classmethod
    def gen_param(cls, d, nc, mode = 'diag', spread = 1):
        """Generate random, valid parameters for a gaussian mixture model.

        :Parameters:
            d : int
                the dimension
            nc : int
                the number of components
            mode : string
                covariance matrix mode ('full' or 'diag').

        :Returns:
            w : ndarray
                weights of the mixture
            mu : ndarray
                means of the mixture
            w : ndarray
                variances of the mixture

        Notes
        -----
        This is a class method.
        """
        w   = N.abs(randn(nc))
        w   = w / sum(w, 0)

        mu  = spread * N.sqrt(d) * randn(nc, d)
        if mode == 'diag':
            va  = N.abs(randn(nc, d))
        elif mode == 'full':
            # If A is invertible, A'A is positive definite
            va  = randn(nc * d, d)
            for k in range(nc):
                va[k*d:k*d+d]   = N.dot( va[k*d:k*d+d], 
                    va[k*d:k*d+d].transpose())
        else:
            raise GmParamError('cov matrix mode not recognized')

        return w, mu, va

    #gen_param = classmethod(gen_param)

    def pdf(self, x, log = False):
        """Computes the pdf of the model at given points.

        :Parameters:
            x : ndarray
                points where to estimate the pdf. One row for one
                multi-dimensional sample (eg to estimate the pdf at 100
                different points in 10 dimension, data's shape should be (100,
                20)).
            log : bool
                If true, returns the log pdf instead of the pdf.

        :Returns:
            y : ndarray
                the pdf at points x."""
        if log:
            return D.logsumexp(
                    D.multiple_gauss_den(x, self.mu, self.va, log = True)
                        + N.log(self.w))
        else:
            return N.sum(D.multiple_gauss_den(x, self.mu, self.va) * self.w, 1)

    def pdf_comp(self, x, cid, log = False):
        """Computes the pdf of the model at given points, at given component.

        :Parameters:
            x : ndarray
                points where to estimate the pdf. One row for one
                multi-dimensional sample (eg to estimate the pdf at 100
                different points in 10 dimension, data's shape should be (100,
                20)).
            cid: int
                the component index.
            log : bool
                If true, returns the log pdf instead of the pdf.

        :Returns:
            y : ndarray
                the pdf at points x."""
        if self.mode == 'diag':
            va = self.va[cid]
        elif self.mode == 'full':
            va = self.va[cid*self.d:(cid+1)*self.d]
        else:
            raise GmParamError("""var mode %s not supported""" % self.mode)

        if log:
            return D.gauss_den(x, self.mu[cid], va, log = True) \
                   + N.log(self.w[cid])
        else:
            return D.multiple_gauss_den(x, self.mu[cid], va) * self.w[cid]

    #=================
    # Plotting methods
    #=================
    def plot(self, dim = misc.DEF_VIS_DIM, npoints = misc.DEF_ELL_NP, 
            level = misc.DEF_LEVEL):
        """Plot the ellipsoides directly for the model
        
        Returns a list of lines handle, so that their style can be modified. By
        default, the style is red color, and nolegend for all of them.
        
        :Parameters:
            dim : sequence
                sequence of two integers, the dimensions of interest.
            npoints : int
                Number of points to use for the ellipsoids.
            level : int
                level of confidence (to use with fill argument)
        
        :Returns:
            h : sequence
                Returns a list of lines handle so that their properties
                can be modified (eg color, label, etc...):

        Note
        ----
        Does not work for 1d. Requires matplotlib
        
        :SeeAlso:
            conf_ellipses is used to compute the ellipses. Use this if you want
            to plot with something else than matplotlib."""
        if self.__is1d:
            raise ValueError("This function does not make sense for 1d "
                "mixtures.")

        if not self.__is_valid:
            raise GmParamError("""Parameters of the model has not been 
                set yet, please set them using self.set_param()""")

        k       = self.k
        xe, ye  = self.conf_ellipses(dim, npoints, level)
        try:
            import pylab as P
            return [P.plot(xe[i], ye[i], 'r', label='_nolegend_')[0] for i in
                    range(k)]
        except ImportError:
            raise GmParamError("matplotlib not found, cannot plot...")

    def plot1d(self, level = misc.DEF_LEVEL, fill = False, gpdf = False):
        """Plots the pdf of each component of the 1d mixture.
        
        :Parameters:
            level : int
                level of confidence (to use with fill argument)
            fill : bool
                if True, the area of the pdf corresponding to the given
                confidence intervales is filled.
            gpdf : bool
                if True, the global pdf is plot.
        
        :Returns:
            h : dict
                Returns a dictionary h of plot handles so that their properties
                can be modified (eg color, label, etc...):
                - h['pdf'] is a list of lines, one line per component pdf
                - h['gpdf'] is the line for the global pdf
                - h['conf'] is a list of filling area
        """
        if not self.__is1d:
            raise ValueError("This function does not make sense for "\
                "mixtures which are not unidimensional")

        from scipy.stats import norm
        pval    = N.sqrt(self.va[:, 0]) * norm(0, 1).ppf((1+level)/2)

        # Compute reasonable min/max for the normal pdf: [-mc * std, mc * std]
        # gives the range we are taking in account for each gaussian
        mc  = 3
        std = N.sqrt(self.va[:, 0])
        mi  = N.amin(self.mu[:, 0] - mc * std)
        ma  = N.amax(self.mu[:, 0] + mc * std)

        np  = 500
        x   = N.linspace(mi, ma, np)
        # Prepare the dic of plot handles to return
        ks  = ['pdf', 'conf', 'gpdf']
        hp  = dict((i, []) for i in ks)

        # Compute the densities
        y   = D.multiple_gauss_den(x[:, N.newaxis], self.mu, self.va, \
                                   log = True) \
              + N.log(self.w)
        yt  = self.pdf(x[:, N.newaxis])

        try:
            import pylab as P
            for c in range(self.k):
                h   = P.plot(x, N.exp(y[:, c]), 'r', label ='_nolegend_')
                hp['pdf'].extend(h)
                if fill:
                    # Compute x coordinates of filled area
                    id1 = -pval[c] + self.mu[c]
                    id2 = pval[c] + self.mu[c]
                    xc  = x[:, N.where(x>id1)[0]]
                    xc  = xc[:, N.where(xc<id2)[0]]
                    
                    # Compute the graph for filling
                    yf  = self.pdf_comp(xc, c)
                    xc  = N.concatenate(([xc[0]], xc, [xc[-1]]))
                    yf  = N.concatenate(([0], yf, [0]))
                    h   = P.fill(xc, yf, facecolor = 'b', alpha = 0.1, 
                                 label='_nolegend_')
                    hp['conf'].extend(h)
            if gpdf:
                h = P.plot(x, yt, 'r:', label='_nolegend_')
                hp['gpdf']  = h
            return hp
        except ImportError:
            raise GmParamError("matplotlib not found, cannot plot...")

    def density_on_grid(self, dim = misc.DEF_VIS_DIM, nx = 50, ny = 50,
            nl = 20, maxlevel = 0.95, v = None):
        """Do all the necessary computation for contour plot of mixture's
        density.
        
        :Parameters:
            dim : sequence
                sequence of two integers, the dimensions of interest.
            nx : int
                Number of points to use for the x axis of the grid
            ny : int
                Number of points to use for the y axis of the grid
            nl : int
                Number of contour to plot.
        
        :Returns:
            X : ndarray
                points of the x axis of the grid
            Y : ndarray
                points of the y axis of the grid
            Z : ndarray
                values of the density on X and Y
            V : ndarray
                Contour values to display.
            
        Note
        ----
        X, Y, Z and V are as expected by matplotlib contour function."""
        if self.__is1d:
            raise ValueError("This function does not make sense for 1d "
                             "mixtures.")

        # Ok, it is a bit gory. Basically, we want to compute the size of the
        # grid. We use conf_ellipse, which will return a couple of points for
        # each component, and we can find a grid size which then is just big
        # enough to contain all ellipses. This won't work well if two
        # ellipsoids are crossing each other a lot (because this assumes that
        # at a given point, one component is largely dominant for its
        # contribution to the pdf).

        xe, ye = self.conf_ellipses(level = maxlevel, dim = dim)
        ax = [N.min(xe), N.max(xe), N.min(ye), N.max(ye)]

        w = ax[1] - ax[0]
        h = ax[3] - ax[2]
        x, y, lden = self._densityctr(N.linspace(ax[0]-0.2*w, 
                                                 ax[1]+0.2*w, nx), 
                                      N.linspace(ax[2]-0.2*h, 
                                                 ax[3]+0.2*h, ny), 
                                      dim = dim)
        # XXX: how to find "good" values for level ?
        if v is None:
            v = N.linspace(-5, N.max(lden), nl)
        return x, y, lden, N.array(v)

    def _densityctr(self, rangex, rangey, dim = misc.DEF_VIS_DIM):
        """Helper function to compute density contours on a grid."""
        gr = N.meshgrid(rangex, rangey)
        x = gr[0].flatten()
        y = gr[1].flatten()
        xdata = N.concatenate((x[:, N.newaxis], y[:, N.newaxis]), axis = 1)
        dmu = self.mu[:, dim]
        dva = self._get_va(dim)
        den = GM.fromvalues(self.w, dmu, dva).pdf(xdata, log = True)
        den = den.reshape(len(rangey), len(rangex))

        return gr[0], gr[1], den

    def _get_va(self, dim):
        """Returns variance limited do 2 dimension in tuple dim."""
        assert len(dim) == 2
        dim = N.array(dim)
        if dim.any() < 0 or dim.any() >= self.d:
            raise ValueError("dim elements should be between 0 and dimension"
                             " of the mixture.")

        if self.mode == 'diag':
            return self.va[:, dim]
        elif self.mode == 'full':
            ld = dim.size
            vaselid = N.empty((ld * self.k, ld), N.int)
            for i in range(self.k):
                vaselid[ld*i] = dim[0] + i * self.d
                vaselid[ld*i+1] = dim[1] + i * self.d
            vadid = N.empty((ld * self.k, ld), N.int)
            for i in range(self.k):
                vadid[ld*i] = dim
                vadid[ld*i+1] = dim
            return self.va[vaselid, vadid]
        else:
            raise ValueError("Unkown mode")

    # Syntactic sugar
    def __repr__(self):
        msg = ""
        msg += "Gaussian Mixture:\n"
        msg += " -> %d dimensions\n" % self.d
        msg += " -> %d components\n" % self.k
        msg += " -> %s covariance \n" % self.mode
        if self.__is_valid:
            msg += "Has initial values"""
        else:
            msg += "Has no initial values yet"""
        return msg

    def __str__(self):
        return self.__repr__()

# Function to generate a random index: this is kept outside any class,
# as the function can be useful for other
def gen_rand_index(p, n):
    """Generate a N samples vector containing random index between 1 
    and length(p), each index i with probability p(i)"""
    # TODO Check args here
    
    # TODO: check each value of inverse distribution is
    # different
    invcdf  = N.cumsum(p)
    uni     = rand(n)
    index   = N.zeros(n, dtype=int)

    # This one should be a bit faster
    for k in range(len(p)-1, 0, -1):
        blop        = N.where(N.logical_and(invcdf[k-1] <= uni, 
                    uni < invcdf[k]))
        index[blop] = k
        
    return index

def check_gmm_param(w, mu, va):
    """Check that w, mu and va are valid parameters for
    a mixture of gaussian.
    
    w should sum to 1, there should be the same number of component in each
    param, the variances should be positive definite, etc... 
    
    :Parameters:
        w : ndarray
            vector or list of weigths of the mixture (K elements)
        mu : ndarray
            matrix: K * d
        va : ndarray
            list of variances (vector K * d or square matrices Kd * d)

    :Returns:
        k : int
            number of components
        d : int
            dimension
        mode : string
            'diag' if diagonal covariance, 'full' of full matrices
    """
        
    # Check that w is valid
    if not len(w.shape) == 1:
        raise GmParamError('weight should be a rank 1 array')

    if N.fabs(N.sum(w)  - 1) > misc.MAX_DBL_DEV:
        raise GmParamError('weight does not sum to 1')
    
    # Check that mean and va have the same number of components
    k = len(w)

    if N.ndim(mu) < 2:
        msg = "mu should be a K,d matrix, and a row vector if only 1 comp"
        raise GmParamError(msg)
    if N.ndim(va) < 2:
        msg = """va should be a K,d / K *d, d matrix, and a row vector if
        only 1 diag comp"""
        raise GmParamError(msg)

    (km, d)     = mu.shape
    (ka, da)    = va.shape

    if not k == km:
        msg = "not same number of component in mean and weights"
        raise GmParamError(msg)

    if not d == da:
        msg = "not same number of dimensions in mean and variances"
        raise GmParamError(msg)

    if km == ka:
        mode = 'diag'
    else:
        mode = 'full'
        if not ka == km*d:
            msg = "not same number of dimensions in mean and variances"
            raise GmParamError(msg)
        
    return k, d, mode
        
if __name__ == '__main__':
    pass

# /usr/bin/python
# Last Change: Sat Dec 20 04:00 PM 2008 J

# This is not meant to be used yet !!!! I am not sure how to integrate this
# stuff inside the package yet. The cases are:
#   - we have a set of data, and we want to test online EM compared to normal
#   EM 
#   - we do not have all the data before putting them in online EM: eg current
#   frame depends on previous frame in some way.

# TODO:
#   - Add biblio
#   - Look back at articles for discussion for init, regularization and
#   convergence rates
#   - the function sufficient_statistics does not really return SS. This is not
#   a big problem, but it would be better to really return them as the name
#   implied.

import numpy as N
from numpy import mean
from numpy.testing import assert_array_almost_equal, assert_array_equal

from gmm_em import ExpMixtureModel#, GMM, EM
from gauss_mix import GM
#from gauss_mix import GM
from scipy.cluster.vq import kmeans2 as kmean
import densities2 as D

import copy
from numpy.random import seed

# Clamp
clamp   = 1e-8

# Error classes
class OnGmmError(Exception):
    """Base class for exceptions in this module."""
    pass

class OnGmmParamError:
    """Exception raised for errors in gmm params

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message    = message
    
    def __str__(self):
        return self.message

class OnGMM(ExpMixtureModel):
    """A Class for 'online' (ie recursive) EM. Instead
    of running the E step on the whole data, the sufficient statistics
    are updated for each new frame of data, and used in the (unchanged)
    M step"""
    def init_random(self, init_data):
        """ Init the model at random."""
        k   = self.gm.k
        d   = self.gm.d
        if self.gm.mode == 'diag':
            w  = N.ones(k) / k

            # Init the internal state of EM
            self.cx = N.outer(w, mean(init_data, 0))
            self.cxx = N.outer(w, mean(init_data ** 2, 0))

            # w, mu and va init is the same that in the standard case
            (code, label) = kmean(init_data, init_data[0:k, :], iter = 10,
                    minit = 'matrix')
            mu = code.copy()
            va = N.zeros((k, d))
            for i in range(k):
                for j in range(d):
                    va [i, j] = N.cov(init_data[N.where(label==i), j], 
                            rowvar = 0)
        else:
            raise OnGmmParamError("""init_online not implemented for
                    mode %s yet""", self.gm.mode)

        self.gm.set_param(w, mu, va)
        # c* are the parameters which are computed at every step (ie
        # when a new frame is taken into account
        self.cw     = self.gm.w
        self.cmu    = self.gm.mu
        self.cva    = self.gm.va

        # p* are the parameters used when computing gaussian densities
        # they are always the same than c* in the online case
        self.pw     = self.cw
        self.pmu    = self.cmu
        self.pva    = self.cva

    def init_kmean(self, init_data, niter = 5):
        """ Init the model using kmean."""
        k   = self.gm.k
        d   = self.gm.d
        if self.gm.mode == 'diag':
            w  = N.ones(k) / k

            # Init the internal state of EM
            self.cx = N.outer(w, mean(init_data, 0))
            self.cxx = N.outer(w, mean(init_data ** 2, 0))

            # w, mu and va init is the same that in the standard case
            (code, label) = kmean(init_data, init_data[0:k, :], 
                    iter = niter, minit = 'matrix')
            mu = code.copy()
            va = N.zeros((k, d))
            for i in range(k):
                for j in range(d):
                    va[i, j] = N.cov(init_data[N.where(label==i), j], 
                            rowvar = 0)
        else:
            raise OnGmmParamError("""init_online not implemented for
                    mode %s yet""", self.gm.mode)

        self.gm.set_param(w, mu, va)
        # c* are the parameters which are computed at every step (ie
        # when a new frame is taken into account
        self.cw     = self.gm.w
        self.cmu    = self.gm.mu
        self.cva    = self.gm.va

        # p* are the parameters used when computing gaussian densities
        # they are the same than c* in the online case
        # self.pw     = self.cw.copy()
        # self.pmu    = self.cmu.copy()
        # self.pva    = self.cva.copy()
        self.pw     = self.cw
        self.pmu    = self.cmu
        self.pva    = self.cva

    def __init__(self, gm, init_data, init = 'kmean'):
        self.gm = gm
        
        # Possible init methods
        init_methods = {'kmean' : self.init_kmean}

        self.init   = init_methods[init]

    def compute_sufficient_statistics_frame(self, frame, nu):
        """ sufficient_statistics(frame, nu) for one frame of data
        
        frame has to be rank 1 !"""
        gamma   = multiple_gauss_den_frame(frame, self.pmu, self.pva)
        gamma   *= self.pw
        gamma   /= N.sum(gamma)
        # <1>(t) = cw(t), self.cw = cw(t), each element is one component running weight
        #self.cw	= (1 - nu) * self.cw + nu * gamma
        self.cw	*= (1 - nu)
        self.cw += nu * gamma

        for k in range(self.gm.k):
            self.cx[k]   = (1 - nu) * self.cx[k] + nu * frame * gamma[k]
            self.cxx[k]  = (1 - nu) * self.cxx[k] + nu * frame ** 2 * gamma[k]

    def update_em_frame(self):
        for k in range(self.gm.k):
            self.cmu[k]  = self.cx[k] / self.cw[k]
            self.cva[k]  = self.cxx[k] / self.cw[k] - self.cmu[k] ** 2
    
import _rawden

class OnGMM1d(ExpMixtureModel):
    """Special purpose case optimized for 1d dimensional cases.
    
    Require each frame to be a float, which means the API is a bit
    different than OnGMM. You are trading elegance for speed here !"""
    def init_kmean(self, init_data, niter = 5):
        """ Init the model using kmean."""
        assert init_data.ndim == 1
        k   = self.gm.k
        w   = N.ones(k) / k

        # Init the internal state of EM
        self.cx     = w * mean(init_data)
        self.cxx    = w * mean(init_data ** 2)

        # w, mu and va init is the same that in the standard case
        (code, label)   = kmean(init_data[:, N.newaxis], \
                init_data[0:k, N.newaxis], iter = niter)
        mu          = code.copy()
        va          = N.zeros((k, 1))
        for i in range(k):
            va[i] = N.cov(init_data[N.where(label==i)], rowvar = 0)

        self.gm.set_param(w, mu, va)
        # c* are the parameters which are computed at every step (ie
        # when a new frame is taken into account
        self.cw     = self.gm.w
        self.cmu    = self.gm.mu[:, 0]
        self.cva    = self.gm.va[:, 0]

        # p* are the parameters used when computing gaussian densities
        # they are the same than c* in the online case
        # self.pw     = self.cw.copy()
        # self.pmu    = self.cmu.copy()
        # self.pva    = self.cva.copy()
        self.pw     = self.cw
        self.pmu    = self.cmu
        self.pva    = self.cva

    def __init__(self, gm, init_data, init = 'kmean'):
        self.gm = gm
        if self.gm.d is not 1:
            raise RuntimeError("expects 1d gm only !")

        # Possible init methods
        init_methods    = {'kmean' : self.init_kmean}
        self.init       = init_methods[init]

    def compute_sufficient_statistics_frame(self, frame, nu):
        """expects frame and nu to be float. Returns
        cw, cxx and cxx, eg the sufficient statistics."""
        _rawden.compute_ss_frame_1d(frame, self.cw, self.cmu, self.cva, 
                self.cx, self.cxx, nu)
        return self.cw, self.cx, self.cxx

    def update_em_frame(self, cw, cx, cxx):
        """Update EM state using SS as returned by 
        compute_sufficient_statistics_frame. """
        self.cmu    = cx / cw
        self.cva    = cxx / cw - self.cmu ** 2

    def compute_em_frame(self, frame, nu):
        """Run a whole em step for one frame. frame and nu should be float;
        if you don't need to split E and M steps, this is faster than calling 
        compute_sufficient_statistics_frame and update_em_frame"""
        _rawden.compute_em_frame_1d(frame, self.cw, self.cmu, self.cva, \
                self.cx, self.cxx, nu)

def compute_factor(nframes, ku = 0.005, t0 = 200, nu0 = 0.2):
    lamb    = 1 - 1/(N.arange(-1, nframes - 1) * ku + t0)
    nu      = N.zeros((nframes, 1), N.float64)
    nu[0]   = nu0
    for i in range(1, nframes):
        nu[i]   = 1./(1 + lamb[i] / nu[i-1])
    return nu

def online_gmm_em(data, ninit, k, mode = 'diag', step = None):
    """ Emulate online_gmm_em of matlab, but uses scipy.sandbox.pyem"""
    nframes = data.shape[0]
    if data.ndim > 1:
        d   = data.shape[1]
    else:
        d       = 1
        data    = data[:, N.newaxis]

    nu      = compute_factor(nframes)

    ogm         = GM(d, k, mode)
    ogmm        = OnGMM1d(ogm, 'kmean')
    init_data   = data[:ninit, 0]
    # We force 10 iteration for equivalence with matlab
    ogmm.init(init_data, niter = 10)
    # print "after init in python online_gmm_em"
    # print ogmm.gm.w
    # print ogmm.gm.mu
    # print ogmm.gm.va

    wt  = []
    mut = []
    vat = []

    for t in range(nframes):
        #ogmm.compute_sufficient_statistics(data[t:t+1, :], nu[t])
        #ogmm.update_em()
        # Shit of 1 to agree exactly with matlab (index starting at 1)
        # This is totally arbitrary otherwise
        ogmm.compute_em_frame(data[t], nu[t])
        if ((t+1) % step) == 0:
            wt.append(ogmm.cw.copy())
            mut.append(ogmm.cmu.copy())
            vat.append(ogmm.cva.copy())

    mut = [m[:, N.newaxis] for m in mut]
    vat = [v[:, N.newaxis] for v in vat]
    ogmm.gm.set_param(ogmm.cw, ogmm.cmu[:, N.newaxis], ogmm.cva[:, N.newaxis])
    #ogmm.gm.set_param(ogmm.cw, ogmm.cmu, ogmm.cva)

    return ogm, wt, mut, vat

#class OnlineEM:
#    def __init__(self, ogm):
#        """Init Online Em algorithm with ogm, an instance of OnGMM."""
#        if not isinstance(ogm, OnGMM):
#            raise TypeError("expect a OnGMM instance for the model")
#
#    def init_em(self):
#        pass
#
#    def train(self, data, nu):
#        pass
#
#    def train_frame(self, frame, nu):
#        pass

def multiple_gauss_den_frame(data, mu, va):
    """Helper function to generate several Gaussian
    pdf (different parameters) from one frame of data.
    
    Semantics depending on data's rank
        - rank 0: mu and va expected to have rank 0 or 1
        - rank 1: mu and va expected to have rank 2."""
    if N.ndim(data) == 0:
        # scalar case
        k   = mu.size
        inva    = 1/va
        fac     = (2*N.pi) ** (-1/2.0) * N.sqrt(inva)
        y       = ((data-mu) ** 2) * -0.5 * inva
        return   fac * N.exp(y.ravel())
    elif N.ndim(data) == 1:
        # multi variate case (general case)
        k   = mu.shape[0]
        y   = N.zeros(k, data.dtype)
        if mu.size == va.size:
            # diag case
            for i in range(k):
                #y[i] = D.gauss_den(data, mu[i], va[i])
                # This is a bit hackish: _diag_gauss_den implementation's
                # changes can break this, but I don't see how to easily fix this
                y[i] = D._diag_gauss_den(data, mu[i], va[i], False, -1)
            return y
        else:
            raise RuntimeError("full not implemented yet")
            #for i in range(K):
            #    y[i] = D.gauss_den(data, mu[i, :], 
            #                va[d*i:d*i+d, :])
            #return y.T
    else:
        raise RuntimeError("frame should be rank 0 or 1 only")
        

if __name__ == '__main__':
    pass
    #d       = 1
    #k       = 2
    #mode    = 'diag'
    #nframes = int(5e3)
    #emiter  = 4
    #seed(5)

    ##+++++++++++++++++++++++++++++++++++++++++++++++++
    ## Generate a model with k components, d dimensions
    ##+++++++++++++++++++++++++++++++++++++++++++++++++
    #w, mu, va   = GM.gen_param(d, k, mode, spread = 1.5)
    #gm          = GM.fromvalues(w, mu, va)
    ## Sample nframes frames  from the model
    #data        = gm.sample(nframes)

    ##++++++++++++++++++++++++++++++++++++++++++
    ## Approximate the models with classical EM
    ##++++++++++++++++++++++++++++++++++++++++++
    ## Init the model
    #lgm = GM(d, k, mode)
    #gmm = GMM(lgm, 'kmean')
    #gmm.init(data)

    #gm0    = copy.copy(gmm.gm)
    ## The actual EM, with likelihood computation
    #like    = N.zeros(emiter)
    #for i in range(emiter):
    #    g, tgd  = gmm.sufficient_statistics(data)
    #    like[i] = N.sum(N.log(N.sum(tgd, 1)), axis = 0)
    #    gmm.update_em(data, g)

    ##++++++++++++++++++++++++++++++++++++++++
    ## Approximate the models with online EM
    ##++++++++++++++++++++++++++++++++++++++++
    #ogm     = GM(d, k, mode)
    #ogmm    = OnGMM(ogm, 'kmean')
    #init_data   = data[0:nframes / 20, :]
    #ogmm.init(init_data)

    ## Forgetting param
    #ku		= 0.005
    #t0		= 200
    #lamb	= 1 - 1/(N.arange(-1, nframes-1) * ku + t0)
    #nu0		= 0.2
    #nu		= N.zeros((len(lamb), 1))
    #nu[0]	= nu0
    #for i in range(1, len(lamb)):
    #    nu[i]	= 1./(1 + lamb[i] / nu[i-1])

    #print "meth1"
    ## object version of online EM
    #for t in range(nframes):
    #    ogmm.compute_sufficient_statistics_frame(data[t], nu[t])
    #    ogmm.update_em_frame()

    #ogmm.gm.set_param(ogmm.cw, ogmm.cmu, ogmm.cva)

    ## 1d optimized version
    #ogm2        = GM(d, k, mode)
    #ogmm2       = OnGMM1d(ogm2, 'kmean')
    #ogmm2.init(init_data[:, 0])

    #print "meth2"
    ## object version of online EM
    #for t in range(nframes):
    #    ogmm2.compute_sufficient_statistics_frame(data[t, 0], nu[t])
    #    ogmm2.update_em_frame()

    ##ogmm2.gm.set_param(ogmm2.cw, ogmm2.cmu, ogmm2.cva)

    #print ogmm.cw
    #print ogmm2.cw
    ##+++++++++++++++
    ## Draw the model
    ##+++++++++++++++
    #print "drawing..."
    #import pylab as P
    #P.subplot(2, 1, 1)

    #if not d == 1:
    #    # Draw what is happening
    #    P.plot(data[:, 0], data[:, 1], '.', label = '_nolegend_')

    #    h   = gm.plot()    
    #    [i.set_color('g') for i in h]
    #    h[0].set_label('true confidence ellipsoides')

    #    h   = gm0.plot()    
    #    [i.set_color('k') for i in h]
    #    h[0].set_label('initial confidence ellipsoides')

    #    h   = lgm.plot()    
    #    [i.set_color('r') for i in h]
    #    h[0].set_label('confidence ellipsoides found by EM')

    #    h   = ogmm.gm.plot()    
    #    [i.set_color('m') for i in h]
    #    h[0].set_label('confidence ellipsoides found by Online EM')

    #    # P.legend(loc = 0)
    #else:
    #    # Real confidence ellipses
    #    h   = gm.plot1d()
    #    [i.set_color('g') for i in h['pdf']]
    #    h['pdf'][0].set_label('true pdf')

    #    # Initial confidence ellipses as found by kmean
    #    h0  = gm0.plot1d()
    #    [i.set_color('k') for i in h0['pdf']]
    #    h0['pdf'][0].set_label('initial pdf')

    #    # Values found by EM
    #    hl  = lgm.plot1d(fill = 1, level = 0.66)
    #    [i.set_color('r') for i in hl['pdf']]
    #    hl['pdf'][0].set_label('pdf found by EM')

    #    P.legend(loc = 0)

    #    # Values found by Online EM
    #    hl  = ogmm.gm.plot1d(fill = 1, level = 0.66)
    #    [i.set_color('m') for i in hl['pdf']]
    #    hl['pdf'][0].set_label('pdf found by Online EM')

    #    P.legend(loc = 0)

    #P.subplot(2, 1, 2)
    #P.plot(nu)
    #P.title('Learning rate')
    #P.show()

#! /usr/bin/python
#
# Copyrighted David Cournapeau
# Last Change: Sat Jun 02 07:00 PM 2007 J

# New version, with default numpy ordering.

import numpy as N
import numpy.linalg as lin
from numpy.random import randn
from scipy.stats import chi2

# Error classes
class DenError(Exception):
    """Base class for exceptions in this module.
    
    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error"""
    def __init__(self, message):
        self.message    = message
    
    def __str__(self):
        return self.message

#============
# Public API
#============
# The following function do all the fancy stuff to check that parameters
# are Ok, and call the right implementation if args are OK.
def gauss_den(x, mu, va, log = False, axis = -1):
    """ Compute multivariate Gaussian density at points x for 
    mean mu and variance va along specified axis:
        
    requirements:
        * mean must be rank 0 (1d) or rank 1 (multi variate gaussian)
        * va must be rank 0 (1d), rank 1(multi variate, diag covariance) or rank 2 
        (multivariate, full covariance).
        * in 1 dimension case, any rank for mean and va is ok, as long as their size
        is 1 (eg they contain only 1 element)
    
    Caution: if x is rank 1, it is assumed you have a 1d problem. You cannot compute
    the gaussian densities of only one sample of dimension d; for this, you have
    to use a rank 2 !

    If log is True, than the log density is returned 
    (useful for underflow ?)"""

    # If data is rank 1, then we have 1 dimension problem.
    if x.ndim == 1:
        d   = 1
        n   = x.size
        if not N.size(mu) == 1:
            raise DenError("for 1 dimension problem, mean must have only one element")
            
        if not N.size(va) == 1:
            raise DenError("for 1 dimension problem, mean must have only one element")
        
        return _scalar_gauss_den(x, mu, va, log)
    # If data is rank 2, then we may have 1 dimension or multi-variate problem
    elif x.ndim == 2:
        oaxis   = (axis + 1) % 2
        n       = x.shape[axis]
        d       = x.shape[oaxis]

        # Get away with 1d case now
        if d == 1:
            return _scalar_gauss_den(x, mu, va, log)

        # Now, d > 1 (numpy attributes should be valid on mean and va now)
        if not N.size(mu) == d or not mu.ndim == 1:
            raise DenError("data is %d dimension, but mean's shape is %s" \
                    % (d, N.shape(mu)) + " (should be (%d,))" % d)
            
        isfull  = (va.ndim == 2)
        if not (N.size(va) == d or (isfull and va.shape[0] == va.shape[1] == d)):
            raise DenError("va has an invalid shape or number of elements")

        if isfull:
            # Compute along rows
            if oaxis == 0:
                return  _full_gauss_den(x, mu[:, N.newaxis], va, log, axis)
            else:
                return  _full_gauss_den(x, mu, va, log, axis)
        else:
            return _diag_gauss_den(x, mu, va, log, axis)
    else:
        raise RuntimeError("Sorry, only rank up to 2 supported")
        
# To plot a confidence ellipse from multi-variate gaussian pdf
def gauss_ell(mu, va, dim = [0, 1], npoints = 100, level = 0.39):
    """ Given a mean and covariance for multi-variate
    gaussian, returns npoints points for the ellipse
    of confidence given by level (all points will be inside
    the ellipsoides with a probability equal to level)
    
    Returns the coordinate x and y of the ellipse"""
    
    c       = N.array(dim)

    if mu.size < 2:
        raise RuntimeError("this function only make sense for dimension 2 and more")

    if mu.size == va.size:
        mode    = 'diag'
    else:
        if va.ndim == 2:
            if va.shape[0] == va.shape[1]:
                mode    = 'full'
            else:
                raise DenError("variance not square")
        else:
            raise DenError("mean and variance are not dim conformant")

    # If X ~ N(mu, va), then [X` * va^(-1/2) * X] ~ Chi2
    chi22d  = chi2(2)
    mahal   = N.sqrt(chi22d.ppf(level))
    
    # Generates a circle of npoints
    theta   = N.linspace(0, 2 * N.pi, npoints)
    circle  = mahal * N.array([N.cos(theta), N.sin(theta)])

    # Get the dimension which we are interested in:
    mu  = mu[dim]
    if mode == 'diag':
        va      = va[dim]
        elps    = N.outer(mu, N.ones(npoints))
        elps    += N.dot(N.diag(N.sqrt(va)), circle)
    elif mode == 'full':
        va  = va[c,:][:,c]
        # Method: compute the cholesky decomp of each cov matrix, that is
        # compute cova such as va = cova * cova' 
        # WARN: scipy is different than matlab here, as scipy computes a lower
        # triangular cholesky decomp: 
        #   - va = cova * cova' (scipy)
        #   - va = cova' * cova (matlab)
        # So take care when comparing results with matlab !
        cova    = lin.cholesky(va)
        elps    = N.outer(mu, N.ones(npoints))
        elps    += N.dot(cova, circle)
    else:
        raise DenParam("var mode not recognized")

    return elps[0, :], elps[1, :]

#=============
# Private Api
#=============
# Those 3 functions do almost all the actual computation
def _scalar_gauss_den(x, mu, va, log):
    """ This function is the actual implementation
    of gaussian pdf in scalar case. It assumes all args
    are conformant, so it should not be used directly
    
    Call gauss_den instead"""
    inva    = 1/va
    fac     = (2*N.pi) ** (-1/2.0) * N.sqrt(inva)
    y       = ((x-mu) ** 2) * -0.5 * inva
    if not log:
        y   = fac * N.exp(y.ravel())
    else:
        y   = y + log(fac)

    return y
    
def _diag_gauss_den(x, mu, va, log, axis):
    """ This function is the actual implementation
    of gaussian pdf in scalar case. It assumes all args
    are conformant, so it should not be used directly
    
    Call gauss_den instead"""
    # Diagonal matrix case
    d   = mu.size
    if axis % 2 == 0:
        x  = N.swapaxes(x, 0, 1)

    if not log:
        inva    = 1/va[0]
        fac     = (2*N.pi) ** (-d/2.0) * N.sqrt(inva)
        y       =  (x[0] - mu[0]) ** 2 * inva * -0.5
        for i in range(1, d):
            inva    = 1/va[i]
            fac     *= N.sqrt(inva)
            y       += (x[i] - mu[i]) ** 2 * inva * -0.5
        y   = fac * N.exp(y)
    else:
        y   = _scalar_gauss_den(x[0], mu[0], va[0], log)
        for i in range(1, d):
            y    +=  _scalar_gauss_den(x[i], mu[i], va[i], log)

    return y

def _full_gauss_den(x, mu, va, log, axis):
    """ This function is the actual implementation
    of gaussian pdf in full matrix case. 
    
    It assumes all args are conformant, so it should 
    not be used directly Call gauss_den instead
    
    Does not check if va is definite positive (on inversible 
    for that matter), so the inverse computation and/or determinant
    would throw an exception."""
    d       = mu.size
    inva    = lin.inv(va)
    fac     = 1 / N.sqrt( (2*N.pi) ** d * N.fabs(lin.det(va)))

    # # Slow version (does not work since version 0.6)
    # n       = N.size(x, 0)
    # y       = N.zeros(n)
    # for i in range(n):
    #     y[i] = N.dot(x[i,:],
    #              N.dot(inva, N.transpose(x[i,:])))
    # y *= -0.5

    # we are using a trick with sum to "emulate" 
    # the matrix multiplication inva * x without any explicit loop
    if axis % 2 == 1:
        y   = N.dot(inva, (x-mu))
        y   = -0.5 * N.sum(y * (x-mu), 0)
    else:
        y   = N.dot((x-mu), inva)
        y   = -0.5 * N.sum(y * (x-mu), 1)

    if not log:
        y   = fac * N.exp(y)
    else:
        y   = y + N.log(fac)
 
    return y


#! /usr/bin/python
#
# Copyrighted David Cournapeau
# Last Change: Sat Jun 09 10:00 PM 2007 J

"""This module implements some function of densities module in C for efficiency
reasons.  gaussian, such as pdf estimation, confidence interval/ellipsoids,
etc..."""

__docformat__ = 'restructuredtext'

# This module uses a C implementation through ctypes, for diagonal cases
# TODO:
#   - portable way to find/open the shared library
#   - full cov matrice
#   - test before inclusion

import numpy as N
import numpy.linalg as lin
#from numpy.random import randn
#from scipy.stats import chi2
#import densities as D

import ctypes
from ctypes import c_uint, c_int
from numpy.ctypeslib import ndpointer, load_library

ctypes_major    = int(ctypes.__version__.split('.')[0])
if ctypes_major < 1:
    raise ImportError(msg =  "version of ctypes is %s, expected at least %s"\
            % (ctypes.__version__, '1.0.1'))

# Requirements for diag gden
_gden   = load_library('c_gden.so', __file__)
arg1    = ndpointer(dtype=N.float64)
arg2    = c_uint
arg3    = c_uint
arg4    = ndpointer(dtype=N.float64)
arg5    = ndpointer(dtype=N.float64)
arg6    = ndpointer(dtype=N.float64)
_gden.gden_diag.argtypes    = [arg1, arg2, arg3, arg4, arg5, arg6]
_gden.gden_diag.restype     = c_int

# Error classes
class DenError(Exception):
    """Base class for exceptions in this module.
    
    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error"""
    def __init__(self, message):
        self.message    = message
    
    def __str__(self):
        return self.message

# The following function do all the fancy stuff to check that parameters
# are Ok, and call the right implementation if args are OK.
def gauss_den(x, mu, va, log = False):
    """ Compute multivariate Gaussian density at points x for 
    mean mu and variance va.
    
    Vector are row vectors, except va which can be a matrix
    (row vector variance for diagonal variance)
    
    If log is True, than the log density is returned 
    (useful for underflow ?)"""
    mu  = N.atleast_2d(mu)
    va  = N.atleast_2d(va)
    x   = N.atleast_2d(x)
    
    #=======================#
    # Checking parameters   #
    #=======================#
    if len(N.shape(mu)) != 2:
        raise DenError("mu is not rank 2")
        
    if len(N.shape(va)) != 2:
        raise DenError("va is not rank 2")
        
    if len(N.shape(x)) != 2:
        raise DenError("x is not rank 2")
        
    (n, d)      = N.shape(x)
    (dm0, dm1)  = N.shape(mu)
    (dv0, dv1)  = N.shape(va)
    
    # Check x and mu same dimension
    if dm0 != 1:
        msg = "mean must be a row vector!"
        raise DenError(msg)
    if dm1 != d:
        msg = "x and mu not same dim"
        raise DenError(msg)
    # Check va and mu same size
    if dv1 != d:
        msg = "mu and va not same dim"
        raise DenError(msg)
    if dv0 != 1 and dv0 != d:
        msg = "va not square"
        raise DenError(msg)

    #===============#
    # Computation   #
    #===============#
    if d == 1:
        # scalar case
        return _scalar_gauss_den(x[:, 0], mu[0, 0], va[0, 0], log)
    elif dv0 == 1:
        # Diagonal matrix case
        return _diag_gauss_den(x, mu, va, log)
    elif dv1 == dv0:
        # full case
        return  _full_gauss_den(x, mu, va, log)
    else:
        raise DenError("variance mode not recognized, this is a bug")

# Those 3 functions do almost all the actual computation
def _scalar_gauss_den(x, mu, va, log):
    """ This function is the actual implementation
    of gaussian pdf in scalar case. It assumes all args
    are conformant, so it should not be used directly
    
    ** Expect centered data (ie with mean removed) **

    Call gauss_den instead"""
    d       = mu.size
    inva    = 1/va
    fac     = (2*N.pi) ** (-d/2.0) * N.sqrt(inva)
    y       = ((x-mu) ** 2) * -0.5 * inva
    if not log:
        y   = fac * N.exp(y)
    else:
        y   = y + log(fac)

    return y
    
def _diag_gauss_den(x, mu, va, log):
    """ This function is the actual implementation
    of gaussian pdf in scalar case. It assumes all args
    are conformant, so it should not be used directly
    
    ** Expect centered data (ie with mean removed) **

    Call gauss_den instead"""
    # Diagonal matrix case
    d   = mu.size
    n   = x.shape[0]
    if not log:
        y       = N.zeros(n)
        vat     = va.copy()
        # _gden.gden_diag(N.require(x, requirements = 'C'), n, d, 
        #         N.require(mu, requirements = 'C'),
        #         N.require(inva, requirements = 'C'),
        #         N.require(y, requirements = 'C'))
        x       = N.require(x, requirements = 'C')
        mu      = N.require(mu, requirements = 'C')
        vat     = N.require(vat, requirements = 'C')
        y       = N.require(y, requirements = 'C')
        _gden.gden_diag(x, n, d, mu, vat, y)
        return y
        # _gden.gden_diag.restype     = c_int
        # _gden.gden_diag.argtypes    = [POINTER(c_double), c_uint, c_uint,
        #         POINTER(c_double), POINTER(c_double), POINTER(c_double)]

        # y   = N.zeros(n)
        # inva= 1/va
        # _gden.gden_diag(x.ctypes.data_as(POINTER(c_double)),
        #     n, d,
        #     mu.ctypes.data_as(POINTER(c_double)),
        #     inva.ctypes.data_as(POINTER(c_double)),
        #     y.ctypes.data_as(POINTER(c_double)))
    else:
        y   = _scalar_gauss_den(x[:, 0], mu[0, 0], va[0, 0], log)
        for i in range(1, d):
            y    +=  _scalar_gauss_den(x[:, i], mu[0, i], va[0, i], log)
        return y

def _full_gauss_den(x, mu, va, log):
    """ This function is the actual implementation
    of gaussian pdf in full matrix case. 
    
    It assumes all args are conformant, so it should 
    not be used directly Call gauss_den instead
    
    ** Expect centered data (ie with mean removed) **

    Does not check if va is definite positive (on inversible 
    for that matter), so the inverse computation and/or determinant
    would throw an exception."""
    d       = mu.size
    inva    = lin.inv(va)
    fac     = 1 / N.sqrt( (2*N.pi) ** d * N.fabs(lin.det(va)))

    # we are using a trick with sum to "emulate" 
    # the matrix multiplication inva * x without any explicit loop
    y   = N.dot((x-mu), inva)
    y   = -0.5 * N.sum(y * (x-mu), 1)

    if not log:
        y   = fac * N.exp(y)
    else:
        y   = y + N.log(fac)
 
    return y

if __name__ == "__main__":
    pass
    ##=========================================
    ## Test accuracy between pure and C python
    ##=========================================
    #mu  = N.array([2.0, 3])
    #va  = N.array([5.0, 3])

    ## Generate a multivariate gaussian of mean mu and covariance va
    #nframes = 1e4
    #X       = randn(nframes, 2)
    #Yc      = N.dot(N.diag(N.sqrt(va)), X.transpose())
    #Yc      = Yc.transpose() + mu

    #Y   = D.gauss_den(Yc, mu, va)
    #Yt  = gauss_den(Yc, mu, va)

    #print "Diff is " + str(N.sqrt(N.sum((Y-Yt) ** 2))/nframes/2)

#! /usr/bin/env python
# Last Change: Sun Sep 07 04:00 PM 2008 J

from info import __doc__

from gauss_mix import GmParamError, GM
from gmm_em import GmmParamError, GMM, EM
from online_em import OnGMM as _OnGMM

__all__ = filter(lambda s:not s.startswith('_'), dir())

#! /usr/bin/env python
# Last Change: Mon Jul 02 02:00 PM 2007 J
# TODO:
#   - check how to handle cmd line build options with distutils and use
#   it in the building process

"""This is a small python package to estimate Gaussian Mixtures Models
from data, using Expectation Maximization.

Maximum likelihood EM for mixture of Gaussian is implemented, with BIC computation
for number of cluster assessment.

There is also an experimental online EM version (the EM is updated for each new
sample), and I plan to add Variational Bayes and/or MCMC support for Bayesian approach
for estimating meta parameters of mixtures. """
from os.path import join

def configuration(parent_package='',top_path=None, package_name='em'):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('em',parent_package, top_path)
    config.add_data_dir('examples')
    config.add_data_dir('tests')
    config.add_data_dir('profile_data')
    config.add_extension('c_gden',
                         sources=[join('src', 'c_gden.c')])
    config.add_extension('_rawden',
                         sources=[join('src', 'pure_den.c')])

    return config

if __name__ == "__main__":
    from numpy.distutils.core import setup
    setup(**configuration(top_path='').todict())

"""
Routines for Gaussian Mixture Models and learning with Expectation Maximization 
===============================================================================

This module contains classes and function to compute multivariate Gaussian
densities (diagonal and full covariance matrices), Gaussian mixtures, Gaussian
mixtures models and an Em trainer.

More specifically, the module defines the following classes, functions:

- densities.gauss_den: function to compute multivariate Gaussian pdf 
- gauss_mix.GM: defines the GM (Gaussian Mixture) class. A Gaussian Mixture can
  be created from its parameters weights, mean and variances, or from its meta
  parameters d (dimension of the Gaussian) and k (number of components in the
  mixture). A Gaussian Model can then be sampled or plot (if d>1, plot
  confidence ellipsoids projected on 2 chosen dimensions, if d == 1, plot the
  pdf of each component and fill the zone of confidence for a given level)
- gmm_em.GMM: defines a class GMM (Gaussian Mixture Model). This class is
  constructed from a GM model gm, and can be used to train gm. The GMM can be
  initiated by kmean or at random, and can compute sufficient statistics, and
  update its parameters from the sufficient statistics.
- kmean.kmean: implements a kmean algorithm. We cannot use scipy.cluster.vq
  kmeans, since its does not give membership of observations.

Example of use: 
---------------

>>> #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
>>> # Create an artificial 2 dimension, 3 clusters GM model, samples it
>>> #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
>>> w, mu, va   = GM.gen_param(2, 3, 'diag', spread = 1.5)
>>> gm          = GM.fromvalues(w, mu, va)
>>> 
>>> # Sample 1000 frames  from the model
>>> data    = gm.sample(1000)
>>> 
>>> #++++++++++++++++++++++++
>>> # Learn the model with EM
>>> #++++++++++++++++++++++++
>>> # Init the model
>>> lgm = GM(d, k, mode)
>>> gmm = GMM(lgm, 'kmean')
>>> 
>>> # The actual EM, with likelihood computation. The threshold
>>> # is compared to the (linearly appromixated) derivative of the likelihood
>>> em      = EM()
>>> like    = em.train(data, gmm, maxiter = 30, thresh = 1e-8)

Files example.py and example2.py show more capabilities of the toolbox, including
plotting capabilities (using matplotlib) and model selection using Bayesian 
Information Criterion (BIC).

Bibliography:

- Maximum likelihood from incomplete data via the EM algorithm in Journal of
  the Royal Statistical Society, Series B, 39(1):1--38, 1977, by A. P.
  Dempster, N. M. Laird, and D. B. Rubin
- Bayesian Approaches to Gaussian Mixture Modelling (1998) by Stephen J.
  Roberts, Dirk Husmeier, Iead Rezek, William Penny in IEEE Transactions on
  Pattern Analysis and Machine Intelligence
     
Copyright: David Cournapeau 2006
License: BSD-style (see LICENSE.txt in main source directory)
"""
version = '0.5.7dev'

depends = ['linalg', 'stats']
ignore  = False

# /usr/bin/python
# Last Change: Mon Jul 02 07:00 PM 2007 J

"""Module implementing GMM, a class to estimate Gaussian mixture models using
EM, and EM, a class which use GMM instances to estimate models parameters using
the ExpectationMaximization algorithm."""

__docformat__ = 'restructuredtext'

# TODO:
#   - which methods to avoid va shrinking to 0 ? There are several options, 
#   not sure which ones are appropriates
#   - improve EM trainer
import numpy as N
from numpy.random import randn
#import _c_densities as densities
import densities
from scipy.cluster.vq import kmeans2 as kmean
from gauss_mix import GmParamError
from misc import curry

#from misc import _DEF_ALPHA, _MIN_DBL_DELTA, _MIN_INV_COND

_PRIOR_COUNT = 0.05
_COV_PRIOR = 0.1

# Error classes
class GmmError(Exception):
    """Base class for exceptions in this module."""
    def __init__(self):
        Exception.__init__(self)

class GmmParamError(GmmError):
    """Exception raised for errors in gmm params

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """
    def __init__(self, message):
        GmmError.__init__(self)
        self.message    = message
    
    def __str__(self):
        return self.message

class MixtureModel(object):
    """Class to model mixture """
    # XXX: Is this really needed ?
    pass

class ExpMixtureModel(MixtureModel):
    """Class to model mixture of exponential pdf (eg Gaussian, exponential,
    Laplace, etc..). This is a special case because some parts of EM are common
    for those models..."""
    pass

class GMM(ExpMixtureModel):
    """ A class to model a Gaussian Mixture Model (GMM). An instance of this
    class is created by giving weights, mean and variances in the ctor.  An
    instanciated object can be sampled, trained by EM. """
    def init_kmean(self, data, niter = 5):
        """ Init the model with kmean."""
        k = self.gm.k
        d = self.gm.d
        init = data[0:k, :]

        # XXX: This is bogus initialization should do better (in kmean with CV)
        (code, label)   = kmean(data, init, niter, minit = 'matrix')

        w   = N.ones(k) / k
        mu  = code.copy()
        if self.gm.mode == 'diag':
            va = N.zeros((k, d))
            for i in range(k):
                for j in range(d):
                    va[i, j] = N.cov(data[N.where(label==i), j], rowvar = 0)
        elif self.gm.mode == 'full':
            va  = N.zeros((k*d, d))
            for i in range(k):
                va[i*d:i*d+d, :] = \
                    N.cov(data[N.where(label==i)], rowvar = 0)
        else:
            raise GmmParamError("mode " + str(self.gm.mode) + \
                    " not recognized")

        self.gm.set_param(w, mu, va)

        self.isinit = True

    def init_random(self, data):
        """ Init the model at random."""
        k = self.gm.k
        d = self.gm.d
        w = N.ones(k) / k
        mu = randn(k, d)
        if self.gm.mode == 'diag':
            va  = N.fabs(randn(k, d))
        else:
            # If A is invertible, A'A is positive definite
            va  = randn(k * d, d)
            for i in range(k):
                va[i*d:i*d+d]   = N.dot( va[i*d:i*d+d], 
                    va[i*d:i*d+d].T)

        self.gm.set_param(w, mu, va)
        
        self.isinit = True

    def init_test(self, data):
        """Use values already in the model as initialization.
        
        Useful for testing purpose when reproducability is necessary. This does
        nothing but checking that the mixture model has valid initial
        values."""
        try:
            self.gm.check_state()
        except GmParamError, e:
            print "Model is not properly initalized, cannot init EM."
            raise ValueError("Message was %s" % str(e))
        
    def __init__(self, gm, init = 'kmean'):
        """Initialize a mixture model.
        
        Initialize the model from a GM instance. This class implements all the
        necessary functionalities for EM.

        :Parameters:
            gm : GM
                the mixture model to train.
            init : string
                initialization method to use."""
        self.gm = gm

        # Possible init methods
        init_methods = {'kmean': self.init_kmean, 'random' : self.init_random,
                'test': self.init_test}

        if init not in init_methods:
            raise GmmParamError('init method %s not recognized' + str(init))

        self.init   = init_methods[init]
        self.isinit = False
        self.initst = init

    def compute_responsabilities(self, data):
        """Compute responsabilities.
        
        Return normalized and non-normalized respondabilities for the model.
        
        Note
        ----
        Computes the latent variable distribution (a posteriori probability)
        knowing the explicit data for the Gaussian model (w, mu, var): gamma(t,
        i) = P[state = i | observation = data(t); w, mu, va]

        This is basically the E step of EM for finite mixtures."""
        # compute the gaussian pdf
        tgd	= densities.multiple_gauss_den(data, self.gm.mu, self.gm.va)
        # multiply by the weight
        tgd	*= self.gm.w
        # Normalize to get a pdf
        gd	= tgd  / N.sum(tgd, axis=1)[:, N.newaxis]

        return gd, tgd

    def compute_log_responsabilities(self, data):
        """Compute log responsabilities.
        
        Return normalized and non-normalized responsabilities for the model (in
        the log domain)
        
        Note
        ----
        Computes the latent variable distribution (a posteriori probability)
        knowing the explicit data for the Gaussian model (w, mu, var): gamma(t,
        i) = P[state = i | observation = data(t); w, mu, va]

        This is basically the E step of EM for finite mixtures."""
        # compute the gaussian pdf
        tgd	= densities.multiple_gauss_den(data, self.gm.mu, 
                                           self.gm.va, log = True)
        # multiply by the weight
        tgd	+= N.log(self.gm.w)
        # Normalize to get a (log) pdf
        gd	= tgd  - densities.logsumexp(tgd)[:, N.newaxis]

        return gd, tgd

    def _update_em_diag(self, data, gamma, ngamma):
        """Computes update of the Gaussian Mixture Model (M step) from the
        responsabilities gamma and normalized responsabilities ngamma, for
        diagonal models."""
        #XXX: caching SS may decrease memory consumption, but is this possible ?
        k = self.gm.k
        d = self.gm.d
        n = data.shape[0]
        invn = 1.0/n

        mu = N.zeros((k, d))
        va = N.zeros((k, d))

        for c in range(k):
            x = N.dot(gamma.T[c:c+1, :], data)[0, :]
            xx = N.dot(gamma.T[c:c+1, :], data ** 2)[0, :]

            mu[c, :] = x / ngamma[c]
            va[c, :] = xx  / ngamma[c] - mu[c, :] ** 2

        w   = invn * ngamma

        return w, mu, va

    def _update_em_full(self, data, gamma, ngamma):
        """Computes update of the Gaussian Mixture Model (M step) from the
        responsabilities gamma and normalized responsabilities ngamma, for
        full models."""
        k = self.gm.k
        d = self.gm.d
        n = data.shape[0]
        invn = 1.0/n

        # In full mode, this is the bottleneck: the triple loop
        # kills performances. This is pretty straightforward
        # algebra, so computing it in C should not be too difficult. The
        # real problem is to have valid covariance matrices, and to keep
        # them positive definite, maybe with special storage... Not sure
        # it really worth the risk
        mu  = N.zeros((k, d))
        va  = N.zeros((k*d, d))

        #XXX: caching SS may decrease memory consumption
        for c in range(k):
            #x   = N.sum(N.outer(gamma[:, c], 
            #            N.ones((1, d))) * data, axis = 0)
            x = N.dot(gamma.T[c:c+1, :], data)[0, :]
            xx = N.zeros((d, d))
            
            # This should be much faster than recursing on n...
            for i in range(d):
                for j in range(d):
                    xx[i, j] = N.sum(data[:, i] * data[:, j] * gamma.T[c, :],
                            axis = 0)

            mu[c, :] = x / ngamma[c]
            va[c*d:c*d+d, :] = xx  / ngamma[c] \
                    - N.outer(mu[c, :], mu[c, :])
        w   = invn * ngamma

        return w, mu, va

    def update_em(self, data, gamma):
        """Computes update of the Gaussian Mixture Model (M step)
        from the a posteriori pdf, computed by gmm_posterior
        (E step).
        """
        ngamma = N.sum(gamma, axis = 0)

        if self.gm.mode == 'diag':
            w, mu, va = self._update_em_diag(data, gamma, ngamma)
        elif self.gm.mode == 'full':
            w, mu, va = self._update_em_full(data, gamma, ngamma)
        else:
            raise GmmParamError("varmode not recognized")

        self.gm.set_param(w, mu, va)

    def likelihood(self, data):
        """ Returns the current log likelihood of the model given
        the data """
        assert(self.isinit)
        # compute the gaussian pdf
        tgd    = densities.multiple_gauss_den(data, self.gm.mu, 
                                           self.gm.va, log = True)
        # multiply by the weight
        tgd    += N.log(self.gm.w)

        return N.sum(densities.logsumexp(tgd), axis = 0)

    def bic(self, data):
        """ Returns the BIC (Bayesian Information Criterion), 
        also called Schwarz information criterion. Can be used 
        to choose between different models which have different
        number of clusters. The BIC is defined as:

        BIC = 2 * ln(L) - k * ln(n)

        where:
            * ln(L) is the log-likelihood of the estimated model
            * k is the number of degrees of freedom
            * n is the number of frames
        
        Not that depending on the literature, BIC may be defined as the opposite
        of the definition given here. """

        if self.gm.mode == 'diag':
            # for a diagonal model, we have k - 1 (k weigths, but one
            # constraint of normality) + k * d (means) + k * d (variances)
            free_deg    = self.gm.k * (self.gm.d * 2 + 1) - 1
        elif self.gm.mode == 'full':
            # for a full model, we have k - 1 (k weigths, but one constraint of
            # normality) + k * d (means) + k * d * d / 2 (each covariance
            # matrice has d **2 params, but with positivity constraint)
            if self.gm.d == 1:
                free_deg = self.gm.k * 3 - 1
            else:
                free_deg = self.gm.k * (self.gm.d + 1 + self.gm.d ** 2 / 2) - 1

        lk  = self.likelihood(data)
        n   = N.shape(data)[0]
        return bic(lk, free_deg, n)

    # syntactic sugar
    def __repr__(self):
        repre   = ""
        repre   += "Gaussian Mixture Model\n"
        repre   += " -> initialized by %s\n" % str(self.initst)
        repre   += self.gm.__repr__()
        return repre

class EM:
    """An EM trainer. An EM trainer
    trains from data, with a model
    
    Not really useful yet"""
    def __init__(self):
        pass
    
    def train(self, data, model, maxiter = 10, thresh = 1e-5, log = False):
        """Train a model using EM.

        Train a model using data, and stops when the likelihood increase
        between two consecutive iteration fails behind a threshold, or when the
        number of iterations > niter, whichever comes first

        :Parameters:
            data : ndarray
                contains the observed features, one row is one frame, ie one
                observation of dimension d
            model : GMM
                GMM instance.
            maxiter : int
                maximum number of iterations
            thresh : threshold
                if the slope of the likelihood falls below this value, the
                algorithm stops.

        :Returns:
            likelihood : ndarray
                one value per iteration.

        Note
        ----
        The model is trained, and its parameters updated accordingly, eg the
        results are put in the GMM instance.
        """
        if not isinstance(model, MixtureModel):
            raise TypeError("expect a MixtureModel as a model")

        # Initialize the data (may do nothing depending on the model)
        model.init(data)

        # Actual training
        if log:
            like = self._train_simple_em_log(data, model, maxiter, thresh)
        else:
            like = self._train_simple_em(data, model, maxiter, thresh)
        return like
    
    def _train_simple_em(self, data, model, maxiter, thresh):
        # Likelihood is kept
        like    = N.zeros(maxiter)

        # Em computation, with computation of the likelihood
        g, tgd  = model.compute_responsabilities(data)
        # TODO: do it in log domain instead
        like[0] = N.sum(N.log(N.sum(tgd, 1)), axis = 0)
        model.update_em(data, g)
        for i in range(1, maxiter):
            g, tgd  = model.compute_responsabilities(data)
            like[i] = N.sum(N.log(N.sum(tgd, 1)), axis = 0)
            model.update_em(data, g)
            if has_em_converged(like[i], like[i-1], thresh):
                return like[0:i]

    def _train_simple_em_log(self, data, model, maxiter, thresh):
        # Likelihood is kept
        like    = N.zeros(maxiter)

        # Em computation, with computation of the likelihood
        g, tgd  = model.compute_log_responsabilities(data)
        like[0] = N.sum(densities.logsumexp(tgd), axis = 0)
        model.update_em(data, N.exp(g))
        for i in range(1, maxiter):
            g, tgd  = model.compute_log_responsabilities(data)
            like[i] = N.sum(densities.logsumexp(tgd), axis = 0)
            model.update_em(data, N.exp(g))
            if has_em_converged(like[i], like[i-1], thresh):
                return like[0:i]

class RegularizedEM:
    # TODO: separate regularizer from EM class ?
    def __init__(self, pcnt = _PRIOR_COUNT, pval = _COV_PRIOR):
        """Create a regularized EM object.

        Covariances matrices are regularized after the E step.

        :Parameters:
            pcnt : float
                proportion of soft counts to be count as prior counts (e.g. if
                you have 1000 samples and the prior_count is 0.1, than the
                prior would "weight" 100 samples).
            pval : float
                value of the prior.
        """
        self.pcnt = pcnt
        self.pval = pval

    def train(self, data, model, maxiter = 20, thresh = 1e-5):
        """Train a model using EM.

        Train a model using data, and stops when the likelihood increase
        between two consecutive iteration fails behind a threshold, or when the
        number of iterations > niter, whichever comes first

        :Parameters:
            data : ndarray
                contains the observed features, one row is one frame, ie one
                observation of dimension d
            model : GMM
                GMM instance.
            maxiter : int
                maximum number of iterations
            thresh : threshold
                if the slope of the likelihood falls below this value, the
                algorithm stops.

        :Returns:
            likelihood : ndarray
                one value per iteration.

        Note
        ----
        The model is trained, and its parameters updated accordingly, eg the
        results are put in the GMM instance.
        """
        mode = model.gm.mode

        # Build regularizer
        if mode == 'diag':
            regularize = curry(regularize_diag, np = self.pcnt, prior =
                    self.pval * N.ones(model.gm.d))
        elif mode == 'full':
            regularize = curry(regularize_full, np = self.pcnt, prior =
                    self.pval * N.eye(model.gm.d))
        else:
            raise ValueError("unknown variance mode")

        model.init(data)
        regularize(model.gm.va)

        # Likelihood is kept
        like = N.empty(maxiter, N.float)

        # Em computation, with computation of the likelihood
        g, tgd  = model.compute_log_responsabilities(data)
        g = N.exp(g)
        model.update_em(data, g)
        regularize(model.gm.va)

        like[0] = N.sum(densities.logsumexp(tgd), axis = 0)
        for i in range(1, maxiter):
            g, tgd  = model.compute_log_responsabilities(data)
            g = N.exp(g)
            model.update_em(data, g)
            regularize(model.gm.va)

            like[i] = N.sum(densities.logsumexp(tgd), axis = 0)
            if has_em_converged(like[i], like[i-1], thresh):
                return like[0:i]

# Misc functions
def bic(lk, deg, n):
    """ Expects lk to be log likelihood """
    return 2 * lk - deg * N.log(n)

def has_em_converged(like, plike, thresh):
    """ given likelihood of current iteration like and previous
    iteration plike, returns true is converged: based on comparison
    of the slope of the likehood with thresh"""
    diff    = N.abs(like - plike)
    avg     = 0.5 * (N.abs(like) + N.abs(plike))
    if diff / avg < thresh:
        return True
    else:
        return False

def regularize_diag(va, np, prior):
    """np * n is the number of prior counts (np is a proportion, and n is the
    number of point).
    
    diagonal variance version"""
    k = va.shape[0]

    for i in range(k):
        va[i] *= 1. / (1 + np)
        va[i] += np / (1. + np) * prior

def regularize_full(va, np, prior):
    """np * n is the number of prior counts (np is a proportion, and n is the
    number of point)."""
    d = va.shape[1]
    k = va.shape[0] / d

    for i in range(k):
        va[i*d:i*d+d, :] *= 1. / (1 + np)
        va[i*d:i*d+d, :] += np / (1. + np) * prior

if __name__ == "__main__":
    pass

#! /usr/bin/env python
# Last Change: Sun Sep 07 04:00 PM 2008 J

# This script generates some random data used for testing EM implementations.
import copy
import numpy as N
from scipy.io import savemat, loadmat

from scikits.learn.em import GM, GMM, EM

def generate_dataset(d, k, mode, nframes):
    """Generate a dataset useful for EM anf GMM testing.
    
    returns:
        data : ndarray
            data from the true model.
        tgm : GM
            the true model (randomly generated)
        gm0 : GM
            the initial model
        gm : GM
            the trained model
    """
    # Generate a model
    w, mu, va = GM.gen_param(d, k, mode, spread = 2.0)
    tgm = GM.fromvalues(w, mu, va)

    # Generate data from the model
    data = tgm.sample(nframes)

    # Run EM on the model, by running the initialization separetely.
    gmm = GMM(GM(d, k, mode), 'test')
    gmm.init_random(data)
    gm0 = copy.copy(gmm.gm)

    gmm = GMM(copy.copy(gmm.gm), 'test')
    em = EM()
    em.train(data, gmm)

    return data, tgm, gm0, gmm.gm

def save_dataset(filename, data, tgm, gm0, gm):
    dic = {'tw': tgm.w, 'tmu': tgm.mu, 'tva': tgm.va,
            'w0': gm0.w, 'mu0' : gm0.mu, 'va0': gm0.va,
            'w': gm.w, 'mu': gm.mu, 'va': gm.va,
            'data': data}
    savemat(filename, dic)

def doall(d, k, mode):
    import pylab as P

    data, tgm, gm0, gm = generate_dataset(d, k, mode, 500)
    filename = mode + '_%dd' % d + '_%dk.mat' % k
    save_dataset(filename, data, tgm, gm0, gm)

    if d == 1:
        P.subplot(2, 1, 1)
        gm0.plot1d()
        h = tgm.plot1d(gpdf = True)
        P.hist(data[:, 0], 20, normed = 1, fill = False)

        P.subplot(2, 1, 2)
        gm.plot1d()
        tgm.plot1d(gpdf = True)
        P.hist(data[:, 0], 20, normed = 1, fill = False)
    else:
        P.subplot(2, 1, 1)
        gm0.plot()
        h = tgm.plot()
        [i.set_color('g') for i in h]
        P.plot(data[:, 0], data[:, 1], '.')

        P.subplot(2, 1, 2)
        gm.plot()
        h = tgm.plot()
        [i.set_color('g') for i in h]
        P.plot(data[:, 0], data[:, 1], '.')

    P.show()

if __name__ == '__main__':
    N.random.seed(0)
    d = 2
    k = 3
    mode = 'full'
    doall(d, k, mode)

    N.random.seed(0)
    d = 2
    k = 3
    mode = 'diag'
    doall(d, k, mode)

    N.random.seed(0)
    d = 1
    k = 4
    mode = 'diag'
    doall(d, k, mode)

"""This is here just to make local imports from this module"""

#! /usr/bin/env python

# Example of use of pyem toolbox. Feel free to change parameters
# such as dimension, number of components, mode of covariance.
#
# You can also try less trivial things such as adding outliers, sampling
# a mixture with full covariance and estimating it with a mixture with diagonal
# gaussians (replace the mode of the learned model lgm)
#
# Later, I hope to add functions for number of component estimation using eg BIC

import numpy as N
from numpy.random import seed

from scipy.sandbox.pyem import GM, GMM, EM
import copy

seed(2)
#+++++++++++++++++++++++++++++
# Meta parameters of the model
#   - k: Number of components
#   - d: dimension of each Gaussian
#   - mode: Mode of covariance matrix: full or diag (string)
#   - nframes: number of frames (frame = one data point = one
#   row of d elements)
k       = 4 
d       = 2
mode    = 'diag'
nframes = 1e3

#+++++++++++++++++++++++++++++++++++++++++++
# Create an artificial GMM model, samples it
#+++++++++++++++++++++++++++++++++++++++++++
w, mu, va   = GM.gen_param(d, k, mode, spread = 1.0)
gm          = GM.fromvalues(w, mu, va)

# Sample nframes frames  from the model
data    = gm.sample(nframes)

#++++++++++++++++++++++++
# Learn the model with EM
#++++++++++++++++++++++++

lgm     = []
kmax    = 6
bics    = N.zeros(kmax)
for i in range(kmax):
    # Init the model with an empty Gaussian Mixture, and create a Gaussian 
    # Mixture Model from it
    lgm.append(GM(d, i+1, mode))
    gmm = GMM(lgm[i], 'kmean')

    # The actual EM, with likelihood computation. The threshold
    # is compared to the (linearly appromixated) derivative of the likelihood
    em      = EM()
    em.train(data, gmm, maxiter = 30, thresh = 1e-10)
    bics[i] = gmm.bic(data)

print "Original model has %d clusters, bics says %d" % (k, N.argmax(bics)+1) 

#+++++++++++++++
# Draw the model
#+++++++++++++++
import pylab as P
P.subplot(3, 2, 1)

for k in range(kmax):
    P.subplot(3, 2, k+1)
    # Level is the confidence level for confidence ellipsoids: 1.0 means that
    # all points will be (almost surely) inside the ellipsoid
    level   = 0.8
    if not d == 1:
        P.plot(data[:, 0], data[:, 1], '.', label = '_nolegend_')

        # h keeps the handles of the plot, so that you can modify 
        # its parameters like label or color
        h   = lgm[k].plot(level = level)
        [i.set_color('r') for i in h]
        h[0].set_label('EM confidence ellipsoides')

        h   = gm.plot(level = level)
        [i.set_color('g') for i in h]
        h[0].set_label('Real confidence ellipsoides')
    else:
        # The 1d plotting function is quite elaborate: the confidence
        # interval are represented by filled areas, the pdf of the mixture and
        # the pdf of each component is drawn (optional)
        h   = gm.plot1d(level = level)
        [i.set_color('g') for i in h['pdf']]
        h['pdf'][0].set_label('true pdf')

        h0  = gm0.plot1d(level = level)
        [i.set_color('k') for i in h0['pdf']]
        h0['pdf'][0].set_label('initial pdf')

        hl  = lgm.plot1d(fill = 1, level = level)
        [i.set_color('r') for i in hl['pdf']]
        hl['pdf'][0].set_label('pdf found by EM')

        P.legend(loc = 0)

P.legend(loc = 0)
P.show()
# P.save('2d diag.png')

#! /usr/bin/env python

# Example of use of pyem toolbox. Feel free to change parameters
# such as dimension, number of components, mode of covariance.
#
# You can also try less trivial things such as adding outliers, sampling
# a mixture with full covariance and estimating it with a mixture with diagonal
# gaussians (replace the mode of the learned model lgm)
#
# Later, I hope to add functions for number of component estimation using eg BIC

import numpy as N
from numpy.random import seed

from scipy.sandbox.pyem import GM, GMM, EM
import copy

seed(1)
#+++++++++++++++++++++++++++++
# Meta parameters of the model
#   - k: Number of components
#   - d: dimension of each Gaussian
#   - mode: Mode of covariance matrix: full or diag (string)
#   - nframes: number of frames (frame = one data point = one
#   row of d elements)
k       = 2 
d       = 2
mode    = 'diag'
nframes = 1e3

#+++++++++++++++++++++++++++++++++++++++++++
# Create an artificial GM model, samples it
#+++++++++++++++++++++++++++++++++++++++++++
w, mu, va   = GM.gen_param(d, k, mode, spread = 1.5)
gm          = GM.fromvalues(w, mu, va)

# Sample nframes frames  from the model
data    = gm.sample(nframes)

#++++++++++++++++++++++++
# Learn the model with EM
#++++++++++++++++++++++++

# Init the model
lgm = GM(d, k, mode)
gmm = GMM(lgm, 'kmean')
gmm.init(data)

# Keep a copy for drawing later
gm0 = copy.copy(lgm)

# The actual EM, with likelihood computation. The threshold
# is compared to the (linearly appromixated) derivative of the likelihood
em      = EM()
like    = em.train(data, gmm, maxiter = 30, thresh = 1e-8)

#+++++++++++++++
# Draw the model
#+++++++++++++++
import pylab as P
P.subplot(2, 1, 1)

# Level is the confidence level for confidence ellipsoids: 1.0 means that
# all points will be (almost surely) inside the ellipsoid
level   = 0.8
if not d == 1:
    P.plot(data[:, 0], data[:, 1], '.', label = '_nolegend_')

    # h keeps the handles of the plot, so that you can modify 
    # its parameters like label or color
    h   = gm.plot(level = level)
    [i.set_color('g') for i in h]
    h[0].set_label('true confidence ellipsoides')

    # Initial confidence ellipses as found by kmean
    h   = gm0.plot(level = level)
    [i.set_color('k') for i in h]
    h[0].set_label('kmean confidence ellipsoides')

    # Values found by EM
    h   = lgm.plot(level = level)
    [i.set_color('r') for i in h]
    h[0].set_label('EM confidence ellipsoides')

    P.legend(loc = 0)
else:
    # The 1d plotting function is quite elaborate: the confidence
    # interval are represented by filled areas, the pdf of the mixture and
    # the pdf of each component is drawn (optional)
    h   = gm.plot1d(level = level)
    [i.set_color('g') for i in h['pdf']]
    h['pdf'][0].set_label('true pdf')

    h0  = gm0.plot1d(level = level)
    [i.set_color('k') for i in h0['pdf']]
    h0['pdf'][0].set_label('initial pdf')

    hl  = lgm.plot1d(fill = 1, level = level)
    [i.set_color('r') for i in hl['pdf']]
    hl['pdf'][0].set_label('pdf found by EM')

    P.legend(loc = 0)

P.subplot(2, 1, 2)
P.plot(like)
P.title('log likelihood')

P.show()
# P.save('2d diag.png')

import numpy as N
from scipy.sandbox.pyem import GM, GMM
import copy

def bench1(mode = 'diag'):
    #===========================================
    # GMM of 20 comp, 20 dimension, 1e4 frames
    #===========================================
    d       = 15
    k       = 30
    nframes = 1e5
    niter   = 10
    mode    = 'diag'

    print "============================================================="
    print "(%d dim, %d components) GMM with %d iterations, for %d frames" \
            % (d, k, niter, nframes)

    #+++++++++++++++++++++++++++++++++++++++++++
    # Create an artificial GMM model, samples it
    #+++++++++++++++++++++++++++++++++++++++++++
    print "Generating the mixture"
    # Generate a model with k components, d dimensions
    w, mu, va   = GM.gen_param(d, k, mode, spread = 3)
    # gm          = GM(d, k, mode)
    # gm.set_param(w, mu, va)
    gm          = GM.fromvalues(w, mu, va)

    # Sample nframes frames  from the model
    data    = gm.sample(nframes)

    #++++++++++++++++++++++++
    # Learn the model with EM
    #++++++++++++++++++++++++

    # Init the model
    print "Init a model for learning, with kmean for initialization"
    lgm = GM(d, k, mode)
    gmm = GMM(lgm, 'kmean')
    
    gmm.init(data)
    # Keep the initialized model for drawing
    gm0 = copy.copy(lgm)

    # The actual EM, with likelihood computation
    like    = N.zeros(niter)

    print "computing..."
    for i in range(niter):
        print "iteration %d" % i
        g, tgd  = gmm.sufficient_statistics(data)
        like[i] = N.sum(N.log(N.sum(tgd, 1)))
        gmm.update_em(data, g)

if __name__ == "__main__":
    import hotshot, hotshot.stats
    profile_file    = 'gmm.prof'
    prof    = hotshot.Profile(profile_file, lineevents=1)
    prof.runcall(bench1)
    p = hotshot.stats.load(profile_file)
    print p.sort_stats('cumulative').print_stats(20)
    prof.close()
    # import profile
    # profile.run('bench1()', 'gmmprof')
    # import pstats
    # p = pstats.Stats('gmmprof')
    # print p.sort_stats('cumulative').print_stats(20)


# /usr/bin/python
# Last Change: Wed Dec 06 08:00 PM 2006 J
import copy

import numpy as N

from gauss_mix import GM
from gmm_em import GMM

def _generate_data(nframes, d, k, mode = 'diag'):
    N.random.seed(0)
    w, mu, va   = GM.gen_param(d, k, mode, spread = 1.5)
    gm          = GM.fromvalues(w, mu, va)
    # Sample nframes frames  from the model
    data        = gm.sample(nframes)

    #++++++++++++++++++++++++++++++++++++++++++
    # Approximate the models with classical EM
    #++++++++++++++++++++++++++++++++++++++++++
    emiter  = 5
    # Init the model
    lgm = GM(d, k, mode)
    gmm = GMM(lgm, 'kmean')
    gmm.init(data)

    gm0    = copy.copy(gmm.gm)
    # The actual EM, with likelihood computation
    like    = N.zeros(emiter)
    for i in range(emiter):
        g, tgd  = gmm.sufficient_statistics(data)
        like[i] = N.sum(N.log(N.sum(tgd, 1)), axis = 0)
        gmm.update_em(data, g)

    return data, gm

nframes = int(5e3)
d       = 1
k       = 2
niter   = 1

def test_v1():
    # Generate test data
    data, gm    = _generate_data(nframes, d, k)
    for i in range(niter):
        iter_1(data, gm)

def test_v2():
    # Generate test data
    data, gm    = _generate_data(nframes, d, k)
    for i in range(niter):
        iter_2(data, gm)

def test_v3():
    # Generate test data
    data, gm    = _generate_data(nframes, d, k)
    for i in range(niter):
        iter_3(data, gm)

def test_v4():
    # Generate test data
    data, gm    = _generate_data(nframes, d, k)
    for i in range(niter):
        iter_4(data, gm)

def iter_1(data, gm):
    """Online EM with original densities + original API"""
    from online_em import OnGMM

    nframes     = data.shape[0]
    ogm         = copy.copy(gm)
    ogmm        = OnGMM(ogm, 'kmean')
    init_data   = data[0:nframes / 20, :]
    ogmm.init(init_data)

    # Forgetting param
    ku		= 0.005
    t0		= 200
    lamb	= 1 - 1/(N.arange(-1, nframes-1) * ku + t0)
    nu0		= 0.2
    nu		= N.zeros((len(lamb), 1))
    nu[0]	= nu0
    for i in range(1, len(lamb)):
        nu[i]	= 1./(1 + lamb[i] / nu[i-1])

    # object version of online EM
    for t in range(nframes):
        ogmm.compute_sufficient_statistics_frame(data[t], nu[t])
        ogmm.update_em_frame()

    ogmm.gm.set_param(ogmm.cw, ogmm.cmu, ogmm.cva)
    print ogmm.cw
    print ogmm.cmu
    print ogmm.cva

def iter_2(data, gm):
    """Online EM with densities2 + original API"""
    from online_em2 import OnGMM

    nframes     = data.shape[0]
    ogm         = copy.copy(gm)
    ogmm        = OnGMM(ogm, 'kmean')
    init_data   = data[0:nframes / 20, :]
    ogmm.init(init_data)

    # Forgetting param
    ku		= 0.005
    t0		= 200
    lamb	= 1 - 1/(N.arange(-1, nframes-1) * ku + t0)
    nu0		= 0.2
    nu		= N.zeros((len(lamb), 1))
    nu[0]	= nu0
    for i in range(1, len(lamb)):
        nu[i]	= 1./(1 + lamb[i] / nu[i-1])

    # object version of online EM
    for t in range(nframes):
        ogmm.compute_sufficient_statistics_frame(data[t], nu[t])
        ogmm.update_em_frame()

    ogmm.gm.set_param(ogmm.cw, ogmm.cmu, ogmm.cva)
    print ogmm.cw
    print ogmm.cmu
    print ogmm.cva

def iter_3(data, gm):
    """Online EM with densities + 1d API"""
    from online_em import OnGMM1d

    #def blop(self, frame, nu):
    #    self.compute_sufficient_statistics_frame(frame, nu)
    #OnGMM.blop  = blop

    nframes     = data.shape[0]
    ogm         = copy.copy(gm)
    ogmm        = OnGMM1d(ogm, 'kmean')
    init_data   = data[0:nframes / 20, :]
    ogmm.init(init_data[:, 0])

    # Forgetting param
    ku		= 0.005
    t0		= 200
    lamb	= 1 - 1/(N.arange(-1, nframes-1) * ku + t0)
    nu0		= 0.2
    nu		= N.zeros((len(lamb), 1))
    nu[0]	= nu0
    for i in range(1, len(lamb)):
        nu[i]	= 1./(1 + lamb[i] / nu[i-1])

    # object version of online EM
    for t in range(nframes):
        #assert ogmm.cw is ogmm.pw
        #assert ogmm.cva is ogmm.pva
        #assert ogmm.cmu is ogmm.pmu
        a, b, c = ogmm.compute_sufficient_statistics_frame(data[t, 0], nu[t])
        ##ogmm.blop(data[t,0], nu[t])
        ogmm.update_em_frame(a, b, c)

    #ogmm.gm.set_param(ogmm.cw, ogmm.cmu, ogmm.cva)
    print ogmm.cw
    print ogmm.cmu
    print ogmm.cva

def iter_4(data, gm):
    """Online EM with densities2 + 1d API"""
    from online_em2 import OnGMM1d

    #def blop(self, frame, nu):
    #    self.compute_sufficient_statistics_frame(frame, nu)
    #OnGMM.blop  = blop

    nframes     = data.shape[0]
    ogm         = copy.copy(gm)
    ogmm        = OnGMM1d(ogm, 'kmean')
    init_data   = data[0:nframes / 20, :]
    ogmm.init(init_data[:, 0])

    # Forgetting param
    ku		= 0.005
    t0		= 200
    lamb	= 1 - 1/(N.arange(-1, nframes-1) * ku + t0)
    nu0		= 0.2
    nu		= N.zeros((len(lamb), 1))
    nu[0]	= nu0
    for i in range(1, len(lamb)):
        nu[i]	= 1./(1 + lamb[i] / nu[i-1])

    # object version of online EM
    def blop():
        #for t in range(nframes):
        #    #assert ogmm.cw is ogmm.pw
        #    #assert ogmm.cva is ogmm.pva
        #    #assert ogmm.cmu is ogmm.pmu
        #    #a, b, c = ogmm.compute_sufficient_statistics_frame(data[t, 0], nu[t])
        #    ###ogmm.blop(data[t,0], nu[t])
        #    #ogmm.update_em_frame(a, b, c)
        #    ogmm.compute_em_frame(data[t, 0], nu[t])
        [ogmm.compute_em_frame(data[t, 0], nu[t]) for t in range(nframes)]
    blop()

    #ogmm.gm.set_param(ogmm.cw, ogmm.cmu, ogmm.cva)
    print ogmm.cw
    print ogmm.cmu
    print ogmm.cva



if __name__ == '__main__':
    #import hotshot, hotshot.stats
    #profile_file    = 'onem1.prof'
    #prof    = hotshot.Profile(profile_file, lineevents=1)
    #prof.runcall(test_v1)
    #p = hotshot.stats.load(profile_file)
    #print p.sort_stats('cumulative').print_stats(20)
    #prof.close()

    #import hotshot, hotshot.stats
    #profile_file    = 'onem2.prof'
    #prof    = hotshot.Profile(profile_file, lineevents=1)
    #prof.runcall(test_v2)
    #p = hotshot.stats.load(profile_file)
    #print p.sort_stats('cumulative').print_stats(20)
    #prof.close()

    import hotshot, hotshot.stats
    profile_file    = 'onem3.prof'
    prof    = hotshot.Profile(profile_file, lineevents=1)
    prof.runcall(test_v3)
    p = hotshot.stats.load(profile_file)
    print p.sort_stats('cumulative').print_stats(20)
    prof.close()

    import hotshot, hotshot.stats
    profile_file    = 'onem4.prof'
    prof    = hotshot.Profile(profile_file, lineevents=1)
    prof.runcall(test_v4)
    p = hotshot.stats.load(profile_file)
    print p.sort_stats('cumulative').print_stats(20)
    prof.close()
    #test_v1()
    #test_v2()
    #test_v3()

import numpy as N
from numpy.random import randn

from numpy.ctypeslib import load_library, ndpointer
from ctypes import cdll, c_uint, c_int, c_double, POINTER

lib = load_library("blop.so", "file")

arg1    = ndpointer(dtype=N.float64)
arg2    = c_uint
arg3    = c_uint
arg4    = ndpointer(dtype=N.float64)
arg5    = ndpointer(dtype=N.float64)

lib.compute.argtypes    = [arg1, arg2, arg3, arg4, arg5]
lib.compute.restype     = c_int
# Compare computing per component likelihood for frame per row vs frame per column
def component_likelihood(x, mu, va, log = False):
    """expect one frame to be one row (rank 2). mu and var are rank 1 array."""
    x -= mu
    x **= 2
    return N.exp(N.dot(x, N.ones((mu.size, 1), x.dtype)))

def component_likelihood3(x, mu, va, log = False):
    """expect one frame to be one row (rank 2). mu and var are rank 1 array."""
    y = N.empty(x.shape[0], x.dtype)
    lib.compute(x, x.shape[0], x.shape[1], mu, y)
    return y

def bench(func, mode = 'diag'):
    d       = 30
    n       = 1e5
    niter   = 10

    print "Compute %d times densities, %d dimension, %d frames" % (niter, d, n)
    mu  = 0.1 * randn(d)
    va  = 0.1 * abs(randn(d))
    
    X   = 0.1 * randn(n, d)
    for i in range(niter):
        Y   = func(X, mu, va)

def benchpy():
    bench(component_likelihood)

def benchpy3():
    bench(component_likelihood3)

def benchpy2():
    bench2(component_likelihood2)

if __name__ == "__main__":
    #import hotshot, hotshot.stats
    #profile_file    = 'gdenpy.prof'
    #prof    = hotshot.Profile(profile_file, lineevents=1)
    #prof.runcall(benchpy)
    #p = hotshot.stats.load(profile_file)
    #print p.sort_stats('cumulative').print_stats(20)
    #prof.close()

    #profile_file    = 'gdenc.prof'
    #prof    = hotshot.Profile(profile_file, lineevents=1)
    #prof.runcall(benchpy3)
    #p = hotshot.stats.load(profile_file)
    #print p.sort_stats('cumulative').print_stats(20)
    #prof.close()

    #import cProfile as profile
    #profile.run('benchpy()', 'fooprof')
    benchpy()
    benchpy3()

import numpy as np
import numpy.random as nr


"""
Samples generator

"""

# Author: B. Thirion, G. Varoquaux, A. Gramfort, V. Michel
# License: BSD 3 clause




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

from base import load_iris, load_digits, load_diabetes

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
    [0  0 1]
    >>> print data.target_names[data.target[[10, 25, 50]]]
    ['setosa' 'setosaosa' 'versicolor']
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


class UnivariateFilter(object):

    def __init__(self, score_func):
        """
        Initialize the univariate feature selection.
        Func : function taking two arrays X and y, and returning an array.
        score_func returning both scores and pvalues
        """
        assert callable(score_func), ValueError(
                "The score function should be a callable, '%s' (type %s) "
                "was passed." % (score_func, type(score_func))
            )
        self.score_func = score_func

    def fit(self,X,y):
        """
        Evaluate the function
        """
        _scores = self.score_func(X, y)
        self._scores = _scores[0]
        self._pvalues = _scores[1]
        #self._rank = np.argsort(self._pvalues)
        return self

    def transform(self,X,**kwargs):
        """
        Transform a new matrix using the selected features
        """
        return X[:,self.support(**kwargs)]


######################################################################
# Specific filters
######################################################################

class SelectPercentile(UnivariateFilter):
    """
    Filter : Select the best percentile of the p_values
    """
    def support(self,percentile):
        assert percentile<=100, ValueError('percentile should be \
                            between 0 and 100 (%f given)' %(percentile))
        alpha = stats.scoreatpercentile(self._pvalues, percentile)
        return (self._pvalues <= alpha)

class SelectKBest(UnivariateFilter):
    """
    Filter : Select the k lowest p-values
    """
    def support(self,k):
        assert k<=len(self._pvalues), ValueError('cannot select %d features'
                                    ' among %d ' % (k, len(self._pvalues)))
        alpha = np.sort(self._pvalues)[k-1]
        return (self._pvalues <= alpha)

class SelectFpr(UnivariateFilter):
    """
    Filter : Select the pvalues below alpha
    """
    def support(self,alpha):
        return (self._pvalues < alpha)


class SelectFdr(UnivariateFilter):
    """
    Filter : Select the p-values corresponding to an estimated false
    discovery rate of alpha. This uses the Benjamini-Hochberg procedure
    """
    def support(self,alpha):
        sv = np.sort(self._pvalues)
        threshold = sv[sv < alpha*np.arange(len(self._pvalues))].max()
        return (self._pvalues < threshold)


class SelectFwe(UnivariateFilter):
    """
    Filter : Select the p-values corresponding to a corrected p-value of alpha
    """
    def support(self,alpha):
        return (self._pvalues < alpha/len(self._pvalues))



if __name__ == "__main__":
    import scikits.learn.datasets.samples_generator as sg
    from scikits.learn.svm import SVR, SVC

    X,y = sg.sparse_uncorrelated(50,100)
    univariate_filter = SelectKBest(f_regression)
    X_r = univariate_filter.fit(X, y).transform(X, k=5)
    sel = univariate_filter.support(k=5)
    clf = SVR(kernel='linear', C=1.)
    y_ = clf.fit(X_r, y).predict(X_r)
    print sel

    ### now change k
    X_r = univariate_filter.transform(X, k=2)
    y_ = clf.fit(X_r, y).predict(X)
    print sel



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
pl.hold('on')
pl.plot([0, 1], [0, 1], 'k--')
pl.hold('off')
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
=======================================
Receiver operating characteristic (ROC)
=======================================

Example of Receiver operating characteristic (ROC) metric to
evaluate the quality of the output of a classifier using
cross-validation.
"""

import random

import numpy as np
from scipy import interp
import pylab as pl

from scikits.learn import svm, datasets
from scikits.learn.metrics import roc, auc
from scikits.learn.cross_val import KFold

################################################################################
# Data IO and generation

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

# Add noisy features
X = np.c_[X,np.random.randn(n_samples, 200*n_features)]

################################################################################
# Classification and ROC analysis

# Run classifier with crossvalidation and plot ROC curves
cv = KFold(n_samples, 6)
classifier = svm.SVC(kernel='linear', probability=True)

pl.figure(-1)
pl.clf()

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

from datetime import datetime
from itertools import cycle
import numpy as np
import pylab as pl

from scikits.learn.glm import lasso_path, enet_path

n_samples, n_features, maxit = 442, 10, 50

from scikits.learn import datasets

np.random.seed(0)
y = np.random.randn(n_samples)
X = np.random.randn(n_samples, n_features)

data = datasets.load_diabetes()
X = data.data
y = data.target

################################################################################
# Fit models
################################################################################

################################################################################
# Demo path functions
################################################################################

eps = 1e-2 # the smaller it is the longer is the path

print "Computing regularization path using the lasso..."
start = datetime.now()
models = lasso_path(X, y, eps=eps, intercept=False)
print "This took ", datetime.now() - start
alphas_lasso = np.array([model.alpha for model in models])
coefs_lasso = np.array([model.coef_ for model in models])

print "Computing regularization path using the elastic net..."
start = datetime.now()
models = enet_path(X, y, eps=eps, intercept=False, rho=0.6)
print "This took ", datetime.now() - start
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
Simple Gaussian Mixture model plotting example

TODO: use the faithful dataset
"""

import numpy as np
from scikits.learn import gmm, shortcuts
from datetime import datetime
import itertools

import pylab as pl
import matplotlib as mpl

n, m = 442, 2

np.random.seed(0)

C = np.array([[0., -0.7], [3.5, .7]]) # rotation and scale matrix

X = np.r_[np.dot(np.random.randn(n, 2), C),
          np.random.randn(n, 2) + np.array([3, 3])]

clf = gmm.GMM(2, cvtype='full')
clf.fit(X)

splot = pl.subplot(111, aspect='equal')

n_comp = len(clf.means) # number of components

color_iter = itertools.cycle (['r', 'g', 'b', 'c'])

Y_ = clf.predict(X)

for i, mean, covar, color in zip(range(n_comp), clf.means,
                                 clf.covars, color_iter):
    v, w = np.linalg.eigh(covar)
    u = w[0] / np.linalg.norm(w[0])
    pl.scatter(X[Y_==i, 0], X[Y_==i, 1], .8, color=color)
    angle = np.arctan(u[1]/u[0])
    angle = 180 * angle / np.pi # convert to degrees
    ell = mpl.patches.Ellipse (mean, v[0], v[1], 180 + angle, color=color) #, angle)
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
from scikits.learn.feature_selection import univ_selection 
# As a scoring function, we use a F test for classification
# We use the default selection function: the 10% most significant
# features
selector = univ_selection.UnivSelection(
                score_func=univ_selection.f_classif)

selector.fit(x, y)
scores = -np.log(selector.p_values_)
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

################################################################################
# Now fit an SVM with added feature selection
selector = univ_selection.UnivSelection(
                estimator=clf,
                score_func=univ_selection.f_classif)

selector.fit(x, y)
svm_weights = (clf.support_**2).sum(axis=0)
svm_weights /= svm_weights.max()
full_svm_weights = np.zeros(selector.support_.shape)
full_svm_weights[selector.support_] = svm_weights
pl.bar(x_indices+.15, full_svm_weights, width=.3, 
        label='SVM weight after univariate selection',
        color='b')


pl.title("Comparing feature selection")
pl.xlabel('Feature number')
pl.yticks(())
pl.axis('tight')
pl.legend()
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
# Lasso with path and cross-validation using optimized_lasso
from scikits.learn.cross_val import KFold
from scikits.learn.glm import optimized_lasso

# Instanciate cross-validation generator
cv = KFold(n_samples/2, 5)

# # Estimate optimized lasso model
lasso_opt = optimized_lasso(X_train, y_train, cv, n_alphas=100, eps=1e-3, maxit=100)
y_ = lasso_opt.predict(X_test)

print lasso_opt

# Compute explained variance on test data
print "r^2 on test data : %f" % (1 - np.linalg.norm(y_test - y_)**2
                                      / np.linalg.norm(y_test)**2)

################################################################################
# Lasso with path and cross-validation using LassoCV path
from scikits.learn.glm import LassoCV
lasso_cv = LassoCV()

y_pred = lasso_cv.fit(X_train, y_train).predict(X_test)

print lasso_cv

# Compute explained variance on test data
print "r^2 on test data : %f" % (1 - np.linalg.norm(y_test - y_)**2
                                      / np.linalg.norm(y_test)**2)


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

Density estimation
====================

This example shows how to do pdf estimation for one dimensional data. It
estimates a Gaussian mixture model for several number of components, and
it determines the "best" one according to the Bayesian Information
Criterion.

It uses old faitfhul waiting time as the one dimension data, and plots the best
model as well as the BIC as a function of the number of component.
"""

# Example of doing pdf estimation with EM algorithm. Requires matplotlib.
import numpy as N

import pylab as P
import matplotlib as MPL

from scikits.learn.em import EM, GM, GMM
import utils

oldfaithful = utils.get_faithful()

duration = oldfaithful[:, :1]
waiting = oldfaithful[:, 1:]

#dt = utils.scale(duration)
#dt = duration / 60.
dt = waiting / 60.

# This function train a mixture model with k components, returns the trained
# model and the BIC
def cluster(data, k):
    d = data.shape[1]
    gm = GM(d, k)
    gmm = GMM(gm)
    em = EM()
    em.train(data, gmm, maxiter = 20)
    return gm, gmm.bic(data)

# bc will contain a list of BIC values for each model trained, gml the
# corresponding mixture model
bc = []
gml = []

for k in range(1, 8):
    gm, b = cluster(dt, k = k)
    bc.append(b)
    gml.append(gm)

mbic = N.argmax(bc)

# Below is code to display a figure with histogram and best model (in the BIC
# sense) pdf, with the BIC as a function of the number of components on the
# right.
P.figure(figsize = [12, 7])
#---------------------------
# histogram + pdf estimation
#---------------------------
P.subplot(1, 2, 1)
h = gml[mbic].plot1d(gpdf=True)
# You can manipulate the differents parts of the plot through the returned
# handles
h['gpdf'][0].set_linestyle('-')
h['gpdf'][0].set_label('pdf of the mixture')
h['pdf'][0].set_label('pdf of individual component')
[l.set_linestyle('-') for l in h['pdf']]
[l.set_color('g') for l in h['pdf']]

prop = MPL.font_manager.FontProperties(size='smaller')
P.legend(loc = 'best', prop = prop)

P.hist(dt, 25, normed = 1, fill = False)
P.xlabel('waiting time between consecutive eruption (in min)')

#------------------------------------------
# BIC as a function of number of components
#------------------------------------------
P.subplot(1, 2, 2)
P.plot(N.arange(1, 8), bc, 'o:')
P.xlabel("number of components")
P.ylabel("BIC")
print "According to the BIC, model with %d components is better" % (N.argmax(bc) + 1)

"""
Simple mixture model example
=============================
"""

import numpy as np
import pylab as pl
from scikits.learn.em import GM

################################################################################
# Hyper parameters:
#   - K:    number of clusters
#   - d:    dimension
k   = 3
d   = 2

################################################################################
# Values for weights, mean and (diagonal) variances
#   - the weights are an array of rank 1
#   - mean is expected to be rank 2 with one row for one component
#   - variances are also expteced to be rank 2. For diagonal, one row
#   is one diagonal, for full, the first d rows are the first variance,
#   etc... In this case, the variance matrix should be k*d rows and d 
#   colums
w   = np.array([0.2, 0.45, 0.35])
mu  = np.array([[4.1, 3], [1, 5], [-2, -3]])
va  = np.array([[1, 1.5], [3, 4], [2, 3.5]])

################################################################################
# First method: directly from parameters:
# Both methods are equivalents.
gm      = GM.fromvalues(w, mu, va)

################################################################################
# Second method to build a GM instance:
gm      = GM(d, k, mode = 'diag')
# The set_params checks that w, mu, and va corresponds to k, d and m
gm.set_param(w, mu, va)

# Once set_params is called, both methods are equivalent. The 2d
# method is useful when using a GM object for learning (where
# the learner class will set the params), whereas the first one
# is useful when there is a need to quickly sample a model
# from existing values, without a need to give the hyper parameters

# Create a Gaussian Mixture from the parameters, and sample
# 1000 items from it (one row = one 2 dimension sample)
data    = gm.sample(1000)

# Plot the samples
pl.plot(data[:, 0], data[:, 1], '.')
# Plot the ellipsoids of confidence with a level a 75 %
gm.plot(level = 0.75)

"""
Ellipse fitting with Gaussian mixtures
=======================================

"""

# This is a simple test to check whether plotting ellipsoides of confidence and
# isodensity contours match
import numpy as N

import pylab as P

from scikits.learn.em import EM, GM, GMM

# Generate a simple mixture model, plot its confidence ellipses + isodensity
# curves for both diagonal and full covariance matrices
d = 3
k = 3
dim = [0, 2]
# diag model
w, mu, va = GM.gen_param(d, k)
dgm = GM.fromvalues(w, mu, va)
# full model
w, mu, va = GM.gen_param(d, k, 'full', spread = 1)
fgm = GM.fromvalues(w, mu, va)

def plot_model(gm, dim):
    X, Y, Z, V = gm.density_on_grid(dim = dim)
    h = gm.plot(dim = dim)
    [i.set_linestyle('-.') for i in h]
    P.contour(X, Y, Z, V)
    data = gm.sample(200)
    P.plot(data[:, dim[0]], data[:,dim[1]], '.')

# Plot the contours and the ellipsoids of confidence
P.subplot(2, 1, 1)
plot_model(dgm, dim)

P.subplot(2, 1, 2)
plot_model(fgm, dim)

P.show()

"""

Regularized Gaussian mixture on hand-written digits
====================================================

Example of using RegularizedEM with pendigits data.

If you want to do discriminant analysis with pendigits, you quickly have
problems with EM if you use directly the coordinates, because some points are
likely to be on the border, hence the corresponding component can have a
covariance matrix which easily becomes singular. Regularized EM avoids this
problem by using simple regularization on the mixture. You can play with pcount
and pval to see the effect on pdf estimation.

For now, regularized EM is pretty crude, but is enough for simple cases where
you need to avoid singular covariance matrices."""

import numpy as N
import pylab as P

from scikits.learn.em import EM, GM, GMM
# Experimental RegularizedEM
from scikits.learn.em.gmm_em import RegularizedEM
import utils

x, y = utils.get_pendigits()

# Take only the first point of pendigits for pdf estimation
dt1 = N.concatenate([x[:, N.newaxis], y[:, N.newaxis]], 1)
dt1 = utils.scale(dt1.astype(N.float))

# pcnt is the poportion of samples to use as prior count. Eg if you have 1000
# samples, and pcn is 0.1, then the prior count would be 100, and 1100 samples
# will be considered as overall when regularizing the parameters.
pcnt = 0.05
# You should try different values of pval. If pval is 0.1, then the
# regularization will be strong. If you use something like 0.01, really sharp
# components will appear. If the values are too small, the regularizer may not
# work (singular covariance matrices).
pval = 0.05

# This function train a mixture model with k components, returns the trained
# model and the BIC
def cluster(data, k, mode = 'full'):
    d = data.shape[1]
    gm = GM(d, k, mode)
    gmm = GMM(gm, 'random')
    em = RegularizedEM(pcnt = pcnt, pval = pval)
    em.train(data, gmm, maxiter = 20)
    return gm, gmm.bic(data)

# bc will contain a list of BIC values for each model trained
N.seterr(all = 'warn')
bc = []
mode = 'full'

P.figure()
for k in range(1, 5):
    # Train a model of k component, and plots isodensity curve
    P.subplot(2, 2, k)
    gm, b = cluster(dt1, k = k, mode = mode)
    bc.append(b)

    X, Y, Z, V = gm.density_on_grid(nl = 20)
    P.contour(X, Y, Z, V)
    P.plot(dt1[:, 0], dt1[:, 1], '.')
    P.xlabel('x coordinate (scaled)')
    P.ylabel('y coordinate (scaled)')

print "According to the BIC, model with %d components is better" % (N.argmax(bc) + 1)
P.show()

"""
Mixture of Gaussian expectation maximation example
====================================================

"""

import pylab
import numpy as np
from scikits.learn.em.densities2 import gauss_ell

#=========================================
# Test plotting a simple diag 2d variance:
#=========================================
va  = np.array([5, 3])
mu  = np.array([2, 3])

# Generate a multivariate gaussian of mean mu and covariance va
X       = np.random.randn(2, 1e3)
Yc      = np.dot(np.diag(np.sqrt(va)), X)
Yc      = Yc.transpose() + mu

# Plotting
Xe, Ye  = gauss_ell(mu, va, npoints = 100)
pylab.figure()
pylab.plot(Yc[:, 0], Yc[:, 1], '.')
pylab.plot(Xe, Ye, 'r')

#=========================================
# Test plotting a simple full 2d variance:
#=========================================
va  = np.array([[0.2, 0.1],[0.1, 0.5]])
mu  = np.array([0, 3])

# Generate a multivariate gaussian of mean mu and covariance va
X       = np.random.randn(1e3, 2)
Yc      = np.dot(np.linalg.cholesky(va), X.transpose())
Yc      = Yc.transpose() + mu

# Plotting
Xe, Ye  = gauss_ell(mu, va, npoints = 100, level=0.95)
pylab.figure()
pylab.plot(Yc[:, 0], Yc[:, 1], '.')
pylab.plot(Xe, Ye, 'r')
pylab.show()

"""
Simple Gaussian-mixture model example
======================================
"""

import numpy as np
from numpy.random import seed

from scikits.learn.em import GM, GMM, EM

seed(2)

k       = 4
d       = 2
mode    = 'diag'
nframes = 1e3

################################################################################
# Create an artificial GMM model, samples it
################################################################################
w, mu, va   = GM.gen_param(d, k, mode, spread = 1.0)
gm          = GM.fromvalues(w, mu, va)

# Sample nframes frames  from the model
data    = gm.sample(nframes)

################################################################################
# Learn the model with EM
################################################################################

# List of learned mixtures lgm[i] is a mixture with i+1 components
lgm     = []
kmax    = 6
bics    = np.zeros(kmax)
em      = EM()
for i in range(kmax):
    lgm.append(GM(d, i+1, mode))

    gmm = GMM(lgm[i], 'kmean')
    em.train(data, gmm, maxiter = 30, thresh = 1e-10)
    bics[i] = gmm.bic(data)

print "Original model has %d clusters, bics says %d" % (k, np.argmax(bics)+1)

################################################################################
# Draw the model
################################################################################
import pylab as pl
pl.subplot(3, 2, 1)

for k in range(kmax):
    pl.subplot(3, 2, k+1)
    level   = 0.9
    pl.plot(data[:, 0], data[:, 1], '.', label = '_nolegend_')

    # h keeps the handles of the plot, so that you can modify 
    # its parameters like label or color
    h   = lgm[k].plot(level = level)
    [i.set_color('r') for i in h]
    h[0].set_label('EM confidence ellipsoides')

    h   = gm.plot(level = level)
    [i.set_color('g') for i in h]
    h[0].set_label('Real confidence ellipsoides')

pl.legend(loc = 0)
pl.show()

#! /usr/bin/env python
# Last Change: Sun Jul 22 03:00 PM 2007 J

# Various utilities for examples 

import numpy as N

from scikits.learn.datasets import oldfaithful, pendigits

def get_faithful():
    """Return faithful data as a nx2 array, first column being duration, second
    being waiting time."""
    # Load faithful data, convert waiting into integer, remove L, M and S data
    data = oldfaithful.load()
    tmp1 = []
    tmp2 = []
    for i in data['data']:
        if not (i[0] == 'L' or i[0] == 'M' or i[0] == 'S'):
            tmp1.append(i[0])
            tmp2.append(i[1])
            
    waiting = N.array([int(i) for i in tmp1], dtype = N.float)
    duration = N.array([i for i in tmp2], dtype = N.float)

    waiting = waiting[:, N.newaxis]
    duration = duration[:, N.newaxis]

    return N.concatenate((waiting, duration), 1)

def get_pendigits():
    """Return faithful data as a nx2 array, first column being duration, second
    being waiting time."""
    # Load faithful data, convert waiting into integer, remove L, M and S data
    data = pendigits.training.load()
    return data['data']['x0'], data['data']['y0']

def scale(data):
    """ Scale data such as each col is in the range [0..1].

    Note: inplace."""
    n = N.min(data, 0)
    m = N.max(data, 0)

    data -= n
    data /= (m-n)
    return data


"""
Another simple mixture model example
=====================================
"""

from numpy.random import seed

from scikits.learn.em import GM, GMM, EM

# To reproduce results, fix the random seed
seed(1)

################################################################################
# Meta parameters of the model
#   - k: Number of components
#   - d: dimension of each Gaussian
#   - mode: Mode of covariance matrix: full or diag (string)
#   - nframes: number of frames (frame = one data point = one
#   row of d elements)
k       = 2
d       = 2
mode    = 'diag'
nframes = 1e3

################################################################################
# Create an artificial GM model, samples it
################################################################################

w, mu, va   = GM.gen_param(d, k, mode, spread = 1.5)
gm          = GM.fromvalues(w, mu, va)

# Sample nframes frames  from the model
data    = gm.sample(nframes)

################################################################################
# Learn the model with EM
################################################################################

# Create a Model from a Gaussian mixture with kmean initialization
lgm = GM(d, k, mode)
gmm = GMM(lgm, 'kmean')

# The actual EM, with likelihood computation. The threshold
# is compared to the (linearly appromixated) derivative of the likelihood
em      = EM()
like    = em.train(data, gmm, maxiter = 30, thresh = 1e-8)

# The computed parameters are in gmm.gm, which is the same than lgm
# (remember, python does not copy most objects by default). You can for example
# plot lgm against gm to compare

"""
Classification using mixture of Gaussian
=========================================

Example of doing classification with mixture of Gaussian. Note that this
is really a toy example: we do not use testing testset nor cross
validation.

We use the famous iris database used by Sir R.A. Fisher. You can try to change
the attributes used for classification, number of components used for the
mixtures, etc..."""

import numpy as N
import pylab as P
import matplotlib as MPL

from scikits.learn.em import EM, GMM, GM
import utils

data = utils.iris.load()
# cnames are the class names
cnames = data.keys()

#--------------------
# Data pre processing
#--------------------
# we use 25 samples of each class (eg half of iris), for
# learning, and the other half for testing. We use sepal width and petal width
# only
ln = 25
tn = 25
xdata = {}
ydata = {}
# learning data
ldata = {}

# you can change here the used attributes (sepal vs petal, width vs height)
for i in cnames:
    xdata[i] = data[i]['sepal width']
    ydata[i] = data[i]['petal width']
    ldata[i] = N.concatenate((xdata[i][:ln, N.newaxis], 
                              ydata[i][:ln, N.newaxis]), 
                             axis = 1)

tx = N.concatenate([xdata[i][ln:] for i in cnames])
ty = N.concatenate([ydata[i][ln:] for i in cnames])
tdata = N.concatenate((tx[:, N.newaxis], ty[:, N.newaxis]), axis = 1)

# tclass makes the correspondance class <-> index in the testing data tdata
tclass = {}
for i in range(3):
    tclass[cnames[i]] = N.arange(tn * i, tn * (i+1))

#----------------------------
# Learning and classification
#----------------------------
# This function train a mixture model with k components
def cluster(data, k, mode = 'full'):
    d = data.shape[1]
    gm = GM(d, k, mode)
    gmm = GMM(gm)
    em = EM()
    em.train(data, gmm, maxiter = 20)
    return gm

# Estimate each class with a mixture of nc components
nc = 2
mode = 'diag'
lmod = {}
for i in cnames:
    lmod[i] = cluster(ldata[i], nc, mode)

# Classifiy the testing data. Of course, the data are not really IID, because
# we did not shuffle the testing data, but in this case, this does not change
# anything.
p = N.empty((len(tdata), 3))
for i in range(3):
    # For each class, computes the likelihood for the testing data
    p[:, i] = lmod[cnames[i]].pdf(tdata)

# We then take the Maximum A Posteriori class (same than most likely model in
# this case, since each class is equiprobable)
cid = N.argmax(p, 1)
classification = {}
for i in range(3):
    classification[cnames[i]] = N.where(cid == i)[0]

correct = {}
incorrect = {}
for i in cnames:
    correct[i] = N.intersect1d(classification[i], tclass[i])
    incorrect[i] = N.setdiff1d(classification[i], tclass[i])

#-----------------
# Plot the results
#-----------------
csym = {'setosa' : 's', 'versicolor' : 'x', 'virginica' : 'o'}
r = 50.
P.figure(figsize = [600/r, 400/r])

prop = MPL.font_manager.FontProperties(size='smaller')

# Plot the learning data with the mixtures
P.subplot(2, 1, 1)
for i in lmod.values():
    #i.plot()
    X, Y, Z, V = i.density_on_grid()
    P.contourf(X, Y, Z, V)

for i in cnames:
    P.plot(ldata[i][:, 0], ldata[i][:, 1], csym[i], label = i + ' (learning)')
P.xlabel('sepal width')
P.ylabel('petal width')
P.legend(loc = 'best')

# Plot the results on test dataset (green for correctly classified, red for
# incorrectly classified)
P.subplot(2, 1, 2)
for i in cnames:
    P.plot(tx[correct[i]], ty[correct[i]], 'g' + csym[i], 
           label = '%s (correctly classified)' % i)
    if len(incorrect[i]) > 0:
        P.plot(tx[incorrect[i]], ty[incorrect[i]], 'r' + csym[i], 
               label = '%s (incorrectly classified)' % i)
P.legend(loc = 'best', prop = prop)
P.xlabel('sepal width')
P.ylabel('petal width')
P.savefig('dclass.png', dpi = 60)

"""
Density estimation with mixture models
======================================
"""

#! /usr/bin/env python
# Last Change: Sun Jul 22 12:00 PM 2007 J

# Example of doing pdf estimation with EM algorithm. Requires matplotlib.
import numpy as N
import pylab as P

from scikits.learn.em import EM, GM, GMM
import utils

oldfaithful = utils.get_faithful()

# We want the relationship between d(t) and w(t+1), but get_faithful gives
# d(t), w(t), so we have to shift to get the "usual" faithful data
waiting = oldfaithful[1:, 1:]
duration = oldfaithful[:len(waiting), :1]
dt = N.concatenate((duration, waiting), 1)

# Scale the data so that each component is in [0..1]
dt = utils.scale(dt)

# This function train a mixture model with k components, returns the trained
# model and the BIC
def cluster(data, k, mode = 'full'):
    d = data.shape[1]
    gm = GM(d, k, mode)
    gmm = GMM(gm)
    em = EM()
    em.train(data, gmm, maxiter = 20)
    return gm, gmm.bic(data)

# bc will contain a list of BIC values for each model trained
bc = []
mode = 'full'
P.figure()
for k in range(1, 5):
    # Train a model of k component, and plots isodensity curve
    P.subplot(2, 2, k)
    gm, b = cluster(dt, k = k, mode = mode)
    bc.append(b)

    X, Y, Z, V = gm.density_on_grid()
    P.contour(X, Y, Z, V)
    P.plot(dt[:, 0], dt[:, 1], '.')
    P.xlabel('duration time (scaled)')
    P.ylabel('waiting time (scaled)')

print "According to the BIC, model with %d components is better" % (N.argmax(bc) + 1)

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
version = '0.4'
# The full version, including alpha/beta/rc tags.
release = '0.4-git'

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

fileList = []

import matplotlib
matplotlib.use('Agg')
import IPython.Shell
mplshell = IPython.Shell.MatplotlibShell('mpl')
                          
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
            mplshell.magic_run(example_file)
            plt.savefig(image_file)
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
        'initializes x; see ' in pydoc.getdoc(obj.__init__)):
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

