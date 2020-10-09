from .. import initializations
from ..layers.core import Layer, MaskedLayer
from ..utils.theano_utils import shared_zeros, shared_ones, sharedX
import theano.tensor as T
import numpy as np


class LeakyReLU(MaskedLayer):
    def __init__(self, alpha=0.3, **kwargs):
        super(LeakyReLU, self).__init__(**kwargs)
        self.alpha = alpha

    def get_output(self, train):
        X = self.get_input(train)
        return T.nnet.relu(X, self.alpha)

    def get_config(self):
        return {"name": self.__class__.__name__,
                "alpha": self.alpha}


class PReLU(MaskedLayer):
    '''
        Reference:
            Delving Deep into Rectifiers: Surpassing Human-Level Performance on ImageNet Classification
                http://arxiv.org/pdf/1502.01852v1.pdf
    '''
    def __init__(self, input_shape, init='zero', weights=None, **kwargs):
        super(PReLU, self).__init__(**kwargs)
        self.init = initializations.get(init)
        self.alphas = self.init(input_shape)
        self.params = [self.alphas]
        self.input_shape = input_shape

        if weights is not None:
            self.set_weights(weights)

    def get_output(self, train):
        X = self.get_input(train)
        pos = T.nnet.relu(X)
        neg = self.alphas * (X - abs(X)) * 0.5
        return pos + neg

    def get_config(self):
        return {"name": self.__class__.__name__,
                "input_shape": self.input_shape,
                "init": self.init.__name__}


class ParametricSoftplus(MaskedLayer):
    '''
        Parametric Softplus of the form: alpha * log(1 + exp(beta * X))

        Reference:
            Inferring Nonlinear Neuronal Computation Based on Physiologically Plausible Inputs
            http://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003143
    '''
    def __init__(self, input_shape, alpha_init=0.2,
                 beta_init=5.0, weights=None, **kwargs):

        super(ParametricSoftplus, self).__init__(**kwargs)
        self.alpha_init = alpha_init
        self.beta_init = beta_init
        self.alphas = sharedX(alpha_init * np.ones(input_shape))
        self.betas = sharedX(beta_init * np.ones(input_shape))
        self.params = [self.alphas, self.betas]
        self.input_shape = input_shape

        if weights is not None:
            self.set_weights(weights)

    def get_output(self, train):
        X = self.get_input(train)
        return T.nnet.softplus(self.betas * X) * self.alphas

    def get_config(self):
        return {"name": self.__class__.__name__,
                "input_shape": self.input_shape,
                "alpha_init": self.alpha_init,
                "beta_init": self.beta_init}


class ThresholdedLinear(MaskedLayer):
    '''
        Thresholded Linear Activation

        Reference:
            Zero-Bias Autoencoders and the Benefits of Co-Adapting Features
            http://arxiv.org/pdf/1402.3337.pdf
    '''
    def __init__(self, theta=1.0, **kwargs):
        super(ThresholdedLinear, self).__init__(**kwargs)
        self.theta = theta

    def get_output(self, train):
        X = self.get_input(train)
        return T.switch(abs(X) < self.theta, 0, X)

    def get_config(self):
        return {"name": self.__class__.__name__,
                "theta": self.theta}


class ThresholdedReLu(MaskedLayer):
    '''
        Thresholded Rectified Activation

        Reference:
            Zero-Bias Autoencoders and the Benefits of Co-Adapting Features
            http://arxiv.org/pdf/1402.3337.pdf
    '''
    def __init__(self, theta=1.0, **kwargs):
        super(ThresholdedReLu, self).__init__(**kwargs)
        self.theta = theta

    def get_output(self, train):
        X = self.get_input(train)
        return T.switch(X > self.theta, X, 0)

    def get_config(self):
        return {"name": self.__class__.__name__,
                "theta": self.theta}