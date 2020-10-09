"""Built-in optimizer classes.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import six
import copy
import numpy as np
from six.moves import zip

from . import backend as K
from .utils.generic_utils import serialize_keras_object
from .utils.generic_utils import deserialize_keras_object
from .legacy import interfaces

if K.backend() == 'tensorflow':
    import tensorflow as tf


def clip_norm(g, c, n):
    """Clip the gradient `g` if the L2 norm `n` exceeds `c`.

    # Arguments
        g: Tensor, the gradient tensor
        c: float >= 0. Gradients will be clipped
            when their L2 norm exceeds this value.
        n: Tensor, actual norm of `g`.

    # Returns
        Tensor, the gradient clipped if required.
    """
    if c <= 0:  # if clipnorm == 0 no need to add ops to the graph
        return g

    # tf require using a special op to multiply IndexedSliced by scalar
    if K.backend() == 'tensorflow':
        condition = n >= c
        then_expression = tf.scalar_mul(c / n, g)
        else_expression = g

        # saving the shape to avoid converting sparse tensor to dense
        if isinstance(then_expression, tf.Tensor):
            g_shape = copy.copy(then_expression.get_shape())
        elif isinstance(then_expression, tf.IndexedSlices):
            g_shape = copy.copy(then_expression.dense_shape)
        if condition.dtype != tf.bool:
            condition = tf.cast(condition, 'bool')
        g = tf.cond(condition,
                    lambda: then_expression,
                    lambda: else_expression)
        if isinstance(then_expression, tf.Tensor):
            g.set_shape(g_shape)
        elif isinstance(then_expression, tf.IndexedSlices):
            g._dense_shape = g_shape
    else:
        g = K.switch(K.greater_equal(n, c), g * c / n, g)
    return g


class Optimizer(object):
    """Abstract optimizer base class.

    Note: this is the parent class of all optimizers, not an actual optimizer
    that can be used for training models.

    All Keras optimizers support the following keyword arguments:

        clipnorm: float >= 0. Gradients will be clipped
            when their L2 norm exceeds this value.
        clipvalue: float >= 0. Gradients will be clipped
            when their absolute value exceeds this value.
    """

    def __init__(self, **kwargs):
        allowed_kwargs = {'clipnorm', 'clipvalue'}
        for k in kwargs:
            if k not in allowed_kwargs:
                raise TypeError('Unexpected keyword argument '
                                'passed to optimizer: ' + str(k))
        self.__dict__.update(kwargs)
        self.updates = []
        self.weights = []

    @interfaces.legacy_get_updates_support
    def get_updates(self, loss, params):
        raise NotImplementedError

    def get_gradients(self, loss, params):
        grads = K.gradients(loss, params)
        if None in grads:
            raise ValueError('An operation has `None` for gradient. '
                             'Please make sure that all of your ops have a '
                             'gradient defined (i.e. are differentiable). '
                             'Common ops without gradient: '
                             'K.argmax, K.round, K.eval.')
        if hasattr(self, 'clipnorm') and self.clipnorm > 0:
            norm = K.sqrt(sum([K.sum(K.square(g)) for g in grads]))
            grads = [clip_norm(g, self.clipnorm, norm) for g in grads]
        if hasattr(self, 'clipvalue') and self.clipvalue > 0:
            grads = [K.clip(g, -self.clipvalue, self.clipvalue) for g in grads]
        return grads

    def set_weights(self, weights):
        """Sets the weights of the optimizer, from Numpy arrays.

        Should only be called after computing the gradients
        (otherwise the optimizer has no weights).

        # Arguments
            weights: a list of Numpy arrays. The number
                of arrays and their shape must match
                number of the dimensions of the weights
                of the optimizer (i.e. it should match the
                output of `get_weights`).

        # Raises
            ValueError: in case of incompatible weight shapes.
        """
        params = self.weights
        if len(params) != len(weights):
            raise ValueError('Length of the specified weight list (' +
                             str(len(weights)) +
                             ') does not match the number of weights ' +
                             'of the optimizer (' + str(len(params)) + ')')
        weight_value_tuples = []
        param_values = K.batch_get_value(params)
        for pv, p, w in zip(param_values, params, weights):
            if pv.shape != w.shape:
                raise ValueError('Optimizer weight shape ' +
                                 str(pv.shape) +
                                 ' not compatible with '
                                 'provided weight shape ' + str(w.shape))
            weight_value_tuples.append((p, w))
        K.batch_set_value(weight_value_tuples)

    def get_weights(self):
        """Returns the current value of the weights of the optimizer.

        # Returns
            A list of numpy arrays.
        """
        return K.batch_get_value(self.weights)

    def get_config(self):
        config = {}
        if hasattr(self, 'clipnorm'):
            config['clipnorm'] = self.clipnorm
        if hasattr(self, 'clipvalue'):
            config['clipvalue'] = self.clipvalue
        return config

    @classmethod
    def from_config(cls, config):
        return cls(**config)


class SGD(Optimizer):
    """Stochastic gradient descent optimizer.

    Includes support for momentum,
    learning rate decay, and Nesterov momentum.

    # Arguments
        learning_rate: float >= 0. Learning rate.
        momentum: float >= 0. Parameter that accelerates SGD
            in the relevant direction and dampens oscillations.
        nesterov: boolean. Whether to apply Nesterov momentum.
    """

    def __init__(self, learning_rate=0.01, momentum=0.,
                 nesterov=False, **kwargs):
        self.initial_decay = kwargs.pop('decay', 0.0)
        with K.name_scope(self.__class__.__name__):
            self.iterations = K.variable(0, dtype='int64', name='iterations')
            learning_rate = kwargs.pop('lr', learning_rate)
            self.lr = K.variable(learning_rate, name='learning_rate')
            self.momentum = K.variable(momentum, name='momentum')
            self.decay = K.variable(self.initial_decay, name='decay')
        self._momentum = True if momentum > 0. else False
        self.nesterov = nesterov
        super(SGD, self).__init__(**kwargs)

    @interfaces.legacy_get_updates_support
    def get_updates(self, loss, params):
        grads = self.get_gradients(loss, params)
        self.updates = [K.update_add(self.iterations, 1)]

        lr = self.lr
        if self.initial_decay > 0:
            lr = lr * (1. / (1. + self.decay * K.cast(self.iterations,
                                                      K.dtype(self.decay))))
        self.weights = [self.iterations]
        if self._momentum:
            shapes = [K.int_shape(p) for p in params]
            moments = [K.zeros(shape) for shape in shapes]
            self.weights.extend([K.zeros(shape) for shape in shapes])
        else:
            moments = [None] * len(params)
        for p, g, m in zip(params, grads, moments):
            if self._momentum:
                # momentum optimizer
                v = self.momentum * m - lr * g  # velocity
                self.updates.append(K.update(m, v))
                if self.nesterov:
                    new_p = p + self.momentum * v - lr * g
                else:
                    new_p = p + v
            else:
                # sgd optimizer.
                new_p = p - lr * g
            # Apply constraints.
            if getattr(p, 'constraint', None) is not None:
                new_p = p.constraint(new_p)

            self.updates.append(K.update(p, new_p))

        return self.updates

    def get_config(self):
        config = {'learning_rate': float(K.get_value(self.lr)),
                  'momentum': float(K.get_value(self.momentum)),
                  'decay': float(K.get_value(self.decay)),
                  'nesterov': self.nesterov}
        base_config = super(SGD, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class RMSprop(Optimizer):
    """RMSProp optimizer.

    It is recommended to leave the parameters of this optimizer
    at their default values
    (except the learning rate, which can be freely tuned).

    # Arguments
        learning_rate: float >= 0. Learning rate.
        rho: float >= 0.
        momentum: float hyperparameter >= 0 that accelerates RMSprop in the relevant
            direction and dampens oscillations.
        centered: If True, gradients are normalized by the estimated variance of
            the gradient; if False, by the uncentered second moment. Setting this to
            True may help with training, but is slightly more expensive in terms of
            computation and memory. Defaults to False.

    # References
        - [rmsprop: Divide the gradient by a running average of its recent magnitude
           ](http://www.cs.toronto.edu/~tijmen/csc321/slides/lecture_slides_lec6.pdf)
    """

    def __init__(self, learning_rate=0.001, rho=0.9, momentum=0., centered=False,
                 **kwargs):
        self.initial_decay = kwargs.pop('decay', 0.0)
        self._momentum = True if momentum > 0. else False
        with K.name_scope(self.__class__.__name__):
            learning_rate = kwargs.pop('lr', learning_rate)
            self.lr = K.variable(learning_rate, name='learning_rate')
            self.rho = K.variable(rho, name='rho')
            self.decay = K.variable(self.initial_decay, name='decay')
            self.iterations = K.variable(0, dtype='int64', name='iterations')
            if self._momentum:
                self.momentum = K.variable(momentum, name='momentum')
        self.epsilon = kwargs.pop('epsilon', K.epsilon())
        self.centered = centered
        super(RMSprop, self).__init__(**kwargs)

    @interfaces.legacy_get_updates_support
    def get_updates(self, loss, params):
        grads = self.get_gradients(loss, params)
        accumulators = [K.zeros(K.int_shape(p), dtype=K.dtype(p)) for p in params]
        self.weights = [self.iterations] + accumulators
        self.updates = [K.update_add(self.iterations, 1)]

        lr = self.lr
        if self.initial_decay > 0:
            lr = lr * (1. / (1. + self.decay * K.cast(self.iterations,
                                                      K.dtype(self.decay))))

        if self._momentum:
            ms = [K.zeros(K.int_shape(p), dtype=K.dtype(p)) for p in params]
            self.weights.extend(ms)
            if self.centered:
                mgs = [K.zeros(K.int_shape(p), dtype=K.dtype(p)) for p in params]
                self.weights.extend(mgs)
            else:
                mgs = [None] * len(params)
        else:
            ms = [None] * len(params)
            mgs = [None] * len(params)

        for p, g, a, m, mg in zip(params, grads, accumulators, ms, mgs):
            new_a = self.rho * a + (1. - self.rho) * K.square(g)
            self.updates.append(K.update(a, new_a))
            if m:
                if mg:
                    new_mg = self.rho * mg + (1. - self.rho) * g
                    new_m = self.momentum * m + lr * g / K.sqrt(
                        new_a - K.square(new_mg) + self.epsilon)
                    self.updates.append(K.update(mg, new_mg))
                else:
                    new_m = self.momentum * m + lr * g / K.sqrt(new_a + self.epsilon)
                self.updates.append(K.update(m, new_m))
                new_p = p - new_m
            else:
                new_p = p - lr * g / (K.sqrt(new_a) + self.epsilon)
            # Apply constraints.
            if getattr(p, 'constraint', None) is not None:
                new_p = p.constraint(new_p)

            self.updates.append(K.update(p, new_p))

        return self.updates

    def set_weights(self, weights):
        params = self.weights
        # Override set_weights for backward compatibility of Keras 2.2.4 optimizer
        # since it does not include iteration at head of the weight list. Set
        # iteration to 0.
        if len(params) == len(weights) + 1:
            weights = [np.array(0)] + weights
        super(RMSprop, self).set_weights(weights)

    def get_config(self):
        config = {'learning_rate': float(K.get_value(self.lr)),
                  'rho': float(K.get_value(self.rho)),
                  'decay': float(K.get_value(self.decay)),
                  'epsilon': self.epsilon}
        base_config = super(RMSprop, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Adagrad(Optimizer):
    """Adagrad optimizer.

    Adagrad is an optimizer with parameter-specific learning rates,
    which are adapted relative to how frequently a parameter gets
    updated during training. The more updates a parameter receives,
    the smaller the learning rate.

    It is recommended to leave the parameters of this optimizer
    at their default values.

    # Arguments
        learning_rate: float >= 0. Initial learning rate.
        initial_accumulator_value: A floating point value.
            Starting value for the accumulators, must be positive.

    # References
        - [Adaptive Subgradient Methods for Online Learning and Stochastic
           Optimization](http://www.jmlr.org/papers/volume12/duchi11a/duchi11a.pdf)
    """

    def __init__(self, learning_rate=0.001, initial_accumulator_value=0.1, **kwargs):
        self.initial_decay = kwargs.pop('decay', 0.0)
        with K.name_scope(self.__class__.__name__):
            learning_rate = kwargs.pop('lr', learning_rate)
            self.lr = K.variable(learning_rate, name='learning_rate')
            self.decay = K.variable(self.initial_decay, name='decay')
            self.iterations = K.variable(0, dtype='int64', name='iterations')
        self.epsilon = kwargs.pop('epsilon', K.epsilon())
        self._initial_accumulator_value = initial_accumulator_value
        super(Adagrad, self).__init__(**kwargs)

    @interfaces.legacy_get_updates_support
    def get_updates(self, loss, params):
        grads = self.get_gradients(loss, params)
        shapes = [K.int_shape(p) for p in params]
        accumulators = [K.variable(np.full(shape, self._initial_accumulator_value))
                        for shape in shapes]
        self.weights = [self.iterations] + accumulators
        self.updates = [K.update_add(self.iterations, 1)]

        lr = self.lr
        if self.initial_decay > 0:
            lr = lr * (1. / (1. + self.decay * K.cast(self.iterations,
                                                      K.dtype(self.decay))))

        for p, g, a in zip(params, grads, accumulators):
            new_a = a + K.square(g)  # update accumulator
            self.updates.append(K.update(a, new_a))
            new_p = p - lr * g / (K.sqrt(new_a) + self.epsilon)

            # Apply constraints.
            if getattr(p, 'constraint', None) is not None:
                new_p = p.constraint(new_p)

            self.updates.append(K.update(p, new_p))
        return self.updates

    def set_weights(self, weights):
        params = self.weights
        # Override set_weights for backward compatibility of Keras 2.2.4 optimizer
        # since it does not include iteration at head of the weight list. Set
        # iteration to 0.
        if len(params) == len(weights) + 1:
            weights = [np.array(0)] + weights
        super(Adagrad, self).set_weights(weights)

    def get_config(self):
        config = {'learning_rate': float(K.get_value(self.lr)),
                  'decay': float(K.get_value(self.decay)),
                  'initial_accumulator_value': self._initial_accumulator_value}
        base_config = super(Adagrad, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Adadelta(Optimizer):
    """Adadelta optimizer.

    Adadelta is a more robust extension of Adagrad
    that adapts learning rates based on a moving window of gradient updates,
    instead of accumulating all past gradients. This way, Adadelta continues
    learning even when many updates have been done. Compared to Adagrad, in the
    original version of Adadelta you don't have to set an initial learning
    rate. In this version, initial learning rate and decay factor can
    be set, as in most other Keras optimizers.

    It is recommended to leave the parameters of this optimizer
    at their default values.

    # Arguments
        learning_rate: float >= 0. Initial learning rate, defaults to 1.
            It is recommended to leave it at the default value.
        rho: float >= 0. Adadelta decay factor, corresponding to fraction of
            gradient to keep at each time step.

    # References
        - [Adadelta - an adaptive learning rate method](
           https://arxiv.org/abs/1212.5701)
    """

    def __init__(self, learning_rate=0.001, rho=0.95, **kwargs):
        self.initial_decay = kwargs.pop('decay', 0.0)
        with K.name_scope(self.__class__.__name__):
            learning_rate = kwargs.pop('lr', learning_rate)
            self.lr = K.variable(learning_rate, name='learning_rate')
            self.decay = K.variable(self.initial_decay, name='decay')
            self.iterations = K.variable(0, dtype='int64', name='iterations')
        self.rho = rho
        self.epsilon = kwargs.pop('epsilon', K.epsilon())
        super(Adadelta, self).__init__(**kwargs)

    @interfaces.legacy_get_updates_support
    def get_updates(self, loss, params):
        grads = self.get_gradients(loss, params)
        shapes = [K.int_shape(p) for p in params]
        accumulators = [K.zeros(shape) for shape in shapes]
        delta_accumulators = [K.zeros(shape) for shape in shapes]
        self.weights = [self.iterations] + accumulators + delta_accumulators
        self.updates = [K.update_add(self.iterations, 1)]

        lr = self.lr
        if self.initial_decay > 0:
            lr = lr * (1. / (1. + self.decay * K.cast(self.iterations,
                                                      K.dtype(self.decay))))

        for p, g, a, d_a in zip(params, grads, accumulators, delta_accumulators):
            # update accumulator
            new_a = self.rho * a + (1. - self.rho) * K.square(g)
            self.updates.append(K.update(a, new_a))

            # use the new accumulator and the *old* delta_accumulator
            update = g * K.sqrt(d_a + self.epsilon) / K.sqrt(new_a + self.epsilon)
            new_p = p - lr * update

            # Apply constraints.
            if getattr(p, 'constraint', None) is not None:
                new_p = p.constraint(new_p)

            self.updates.append(K.update(p, new_p))

            # update delta_accumulator
            new_d_a = self.rho * d_a + (1 - self.rho) * K.square(update)
            self.updates.append(K.update(d_a, new_d_a))
        return self.updates

    def set_weights(self, weights):
        params = self.weights
        # Override set_weights for backward compatibility of Keras 2.2.4 optimizer
        # since it does not include iteration at head of the weight list. Set
        # iteration to 0.
        if len(params) == len(weights) + 1:
            weights = [np.array(0)] + weights
        super(Adadelta, self).set_weights(weights)

    def get_config(self):
        config = {'learning_rate': float(K.get_value(self.lr)),
                  'rho': self.rho,
                  'decay': float(K.get_value(self.decay))}
        base_config = super(Adadelta, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Adam(Optimizer):
    """Adam optimizer.

    Default parameters follow those provided in the original paper.

    # Arguments
        learning_rate: float >= 0. Learning rate.
        beta_1: float, 0 < beta < 1. Generally close to 1.
        beta_2: float, 0 < beta < 1. Generally close to 1.
        amsgrad: boolean. Whether to apply the AMSGrad variant of this
            algorithm from the paper "On the Convergence of Adam and
            Beyond".

    # References
        - [Adam - A Method for Stochastic Optimization](
           https://arxiv.org/abs/1412.6980v8)
        - [On the Convergence of Adam and Beyond](
           https://openreview.net/forum?id=ryQu7f-RZ)
    """

    def __init__(self, learning_rate=0.001, beta_1=0.9, beta_2=0.999,
                 amsgrad=False, **kwargs):
        self.initial_decay = kwargs.pop('decay', 0.0)
        with K.name_scope(self.__class__.__name__):
            self.iterations = K.variable(0, dtype='int64', name='iterations')
            learning_rate = kwargs.pop('lr', learning_rate)
            self.lr = K.variable(learning_rate, name='learning_rate')
            self.beta_1 = K.variable(beta_1, name='beta_1')
            self.beta_2 = K.variable(beta_2, name='beta_2')
            self.decay = K.variable(self.initial_decay, name='decay')
        self.epsilon = kwargs.pop('epsilon', K.epsilon())
        self.amsgrad = amsgrad
        super(Adam, self).__init__(**kwargs)

    @interfaces.legacy_get_updates_support
    def get_updates(self, loss, params):
        grads = self.get_gradients(loss, params)
        self.updates = [K.update_add(self.iterations, 1)]

        lr = self.lr
        if self.initial_decay > 0:
            lr = lr * (1. / (1. + self.decay * K.cast(self.iterations,
                                                      K.dtype(self.decay))))

        t = K.cast(self.iterations, K.floatx()) + 1
        lr_t = lr * (K.sqrt(1. - K.pow(self.beta_2, t)) /
                     (1. - K.pow(self.beta_1, t)))

        ms = [K.zeros(K.int_shape(p), dtype=K.dtype(p)) for p in params]
        vs = [K.zeros(K.int_shape(p), dtype=K.dtype(p)) for p in params]
        self.weights = [self.iterations] + ms + vs
        if self.amsgrad:
            vhats = [K.zeros(K.int_shape(p), dtype=K.dtype(p)) for p in params]
            self.weights.extend(vhats)
        else:
            vhats = [None] * len(params)
        for p, g, m, v, vhat in zip(params, grads, ms, vs, vhats):
            m_t = (self.beta_1 * m) + (1. - self.beta_1) * g
            v_t = (self.beta_2 * v) + (1. - self.beta_2) * K.square(g)
            self.updates.append(K.update(m, m_t))
            self.updates.append(K.update(v, v_t))
            if self.amsgrad:
                vhat_t = K.maximum(vhat, v_t)
                p_t = p - lr_t * m_t / (K.sqrt(vhat_t) + self.epsilon)
                self.updates.append(K.update(vhat, vhat_t))
            else:
                p_t = p - lr_t * m_t / (K.sqrt(v_t) + self.epsilon)
            new_p = p_t
            # Apply constraints.
            if getattr(p, 'constraint', None) is not None:
                new_p = p.constraint(new_p)
            self.updates.append(K.update(p, new_p))

        return self.updates

    def set_weights(self, weights):
        params = self.weights
        # If the weights are generated by Keras V1 optimizer, it includes vhats
        # even without amsgrad, i.e, V1 optimizer has 3x + 1 variables, while V2
        # optimizer has 2x + 1 variables. Filter vhats out for compatibility.
        num_vars = int((len(params) - 1) / 2)
        if len(weights) == 3 * num_vars + 1:
            weights = weights[:len(params)]
        super(Adam, self).set_weights(weights)

    def get_config(self):
        config = {'learning_rate': float(K.get_value(self.lr)),
                  'beta_1': float(K.get_value(self.beta_1)),
                  'beta_2': float(K.get_value(self.beta_2)),
                  'decay': float(K.get_value(self.decay)),
                  'amsgrad': self.amsgrad}
        base_config = super(Adam, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Adamax(Optimizer):
    """Adamax optimizer from Adam paper's Section 7.

    It is a variant of Adam based on the infinity norm.
    Default parameters follow those provided in the paper.

    # Arguments
        learning_rate: float >= 0. Learning rate.
        beta_1: float, 0 < beta < 1. Generally close to 1.
        beta_2: float, 0 < beta < 1. Generally close to 1.

    # References
        - [Adam - A Method for Stochastic Optimization](
           https://arxiv.org/abs/1412.6980v8)
    """

    def __init__(self, learning_rate=0.001, beta_1=0.9, beta_2=0.999, **kwargs):
        self.initial_decay = kwargs.pop('decay', 0.0)
        with K.name_scope(self.__class__.__name__):
            self.iterations = K.variable(0, dtype='int64', name='iterations')
            learning_rate = kwargs.pop('lr', learning_rate)
            self.lr = K.variable(learning_rate, name='learning_rate')
            self.beta_1 = K.variable(beta_1, name='beta_1')
            self.beta_2 = K.variable(beta_2, name='beta_2')
            self.decay = K.variable(self.initial_decay, name='decay')
        self.epsilon = kwargs.pop('epsilon', K.epsilon())
        super(Adamax, self).__init__(**kwargs)

    @interfaces.legacy_get_updates_support
    def get_updates(self, loss, params):
        grads = self.get_gradients(loss, params)
        self.updates = [K.update_add(self.iterations, 1)]

        lr = self.lr
        if self.initial_decay > 0:
            lr = lr * (1. / (1. + self.decay * K.cast(self.iterations,
                                                      K.dtype(self.decay))))

        t = K.cast(self.iterations, K.floatx()) + 1
        lr_t = lr / (1. - K.pow(self.beta_1, t))

        shapes = [K.int_shape(p) for p in params]
        # zero init of 1st moment
        ms = [K.zeros(shape) for shape in shapes]
        # zero init of exponentially weighted infinity norm
        us = [K.zeros(shape) for shape in shapes]
        self.weights = [self.iterations] + ms + us

        for p, g, m, u in zip(params, grads, ms, us):

            m_t = (self.beta_1 * m) + (1. - self.beta_1) * g
            u_t = K.maximum(self.beta_2 * u, K.abs(g))
            p_t = p - lr_t * m_t / (u_t + self.epsilon)

            self.updates.append(K.update(m, m_t))
            self.updates.append(K.update(u, u_t))
            new_p = p_t

            # Apply constraints.
            if getattr(p, 'constraint', None) is not None:
                new_p = p.constraint(new_p)

            self.updates.append(K.update(p, new_p))
        return self.updates

    def get_config(self):
        config = {'learning_rate': float(K.get_value(self.lr)),
                  'beta_1': float(K.get_value(self.beta_1)),
                  'beta_2': float(K.get_value(self.beta_2)),
                  'decay': float(K.get_value(self.decay))}
        base_config = super(Adamax, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Nadam(Optimizer):
    """Nesterov Adam optimizer.

    Much like Adam is essentially RMSprop with momentum,
    Nadam is RMSprop with Nesterov momentum.

    Default parameters follow those provided in the paper.
    It is recommended to leave the parameters of this optimizer
    at their default values.

    # Arguments
        learning_rate: float >= 0. Learning rate.
        beta_1: float, 0 < beta < 1. Generally close to 1.
        beta_2: float, 0 < beta < 1. Generally close to 1.

    # References
        - [Nadam report](http://cs229.stanford.edu/proj2015/054_report.pdf)
        - [On the importance of initialization and momentum in deep learning](
           http://www.cs.toronto.edu/~fritz/absps/momentum.pdf)
    """

    def __init__(self, learning_rate=0.001, beta_1=0.9, beta_2=0.999, **kwargs):
        self.schedule_decay = kwargs.pop('schedule_decay', 0.004)
        with K.name_scope(self.__class__.__name__):
            self.iterations = K.variable(0, dtype='int64', name='iterations')
            self.m_schedule = K.variable(1., name='m_schedule')
            learning_rate = kwargs.pop('lr', learning_rate)
            self.lr = K.variable(learning_rate, name='learning_rate')
            self.beta_1 = K.variable(beta_1, name='beta_1')
            self.beta_2 = K.variable(beta_2, name='beta_2')
        self.epsilon = kwargs.pop('epsilon', K.epsilon())
        super(Nadam, self).__init__(**kwargs)

    @interfaces.legacy_get_updates_support
    def get_updates(self, loss, params):
        grads = self.get_gradients(loss, params)
        self.updates = [K.update_add(self.iterations, 1)]

        t = K.cast(self.iterations, K.floatx()) + 1

        # Due to the recommendations in [2], i.e. warming momentum schedule
        momentum_cache_t = self.beta_1 * (1. - 0.5 * (
            K.pow(K.cast_to_floatx(0.96), t * self.schedule_decay)))
        momentum_cache_t_1 = self.beta_1 * (1. - 0.5 * (
            K.pow(K.cast_to_floatx(0.96), (t + 1) * self.schedule_decay)))
        m_schedule_new = self.m_schedule * momentum_cache_t
        m_schedule_next = self.m_schedule * momentum_cache_t * momentum_cache_t_1
        self.updates.append((self.m_schedule, m_schedule_new))

        shapes = [K.int_shape(p) for p in params]
        ms = [K.zeros(shape) for shape in shapes]
        vs = [K.zeros(shape) for shape in shapes]

        self.weights = [self.iterations, self.m_schedule] + ms + vs

        for p, g, m, v in zip(params, grads, ms, vs):
            # the following equations given in [1]
            g_prime = g / (1. - m_schedule_new)
            m_t = self.beta_1 * m + (1. - self.beta_1) * g
            m_t_prime = m_t / (1. - m_schedule_next)
            v_t = self.beta_2 * v + (1. - self.beta_2) * K.square(g)
            v_t_prime = v_t / (1. - K.pow(self.beta_2, t))
            m_t_bar = (1. - momentum_cache_t) * g_prime + (
                momentum_cache_t_1 * m_t_prime)

            self.updates.append(K.update(m, m_t))
            self.updates.append(K.update(v, v_t))

            p_t = p - self.lr * m_t_bar / (K.sqrt(v_t_prime) + self.epsilon)
            new_p = p_t

            # Apply constraints.
            if getattr(p, 'constraint', None) is not None:
                new_p = p.constraint(new_p)

            self.updates.append(K.update(p, new_p))
        return self.updates

    def set_weights(self, weights):
        params = self.weights
        # Override set_weights for backward compatibility of Keras 2.2.4 optimizer
        # since it does not include iteration at head of the weight list. Set
        # iteration to 0.
        if len(params) == len(weights) + 1:
            weights = [weights[0]] + [np.array(1.)] + weights[1:]
        super(Nadam, self).set_weights(weights)

    def get_config(self):
        config = {'learning_rate': float(K.get_value(self.lr)),
                  'beta_1': float(K.get_value(self.beta_1)),
                  'beta_2': float(K.get_value(self.beta_2)),
                  'schedule_decay': self.schedule_decay}
        base_config = super(Nadam, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class TFOptimizer(Optimizer):
    """Wrapper class for native TensorFlow optimizers.

    # Arguments
        optimizer: Selected optimizer
    """

    def __init__(self, optimizer):
        self.optimizer = optimizer
        with K.name_scope(self.__class__.__name__):
            self.iterations = K.variable(0, dtype='int64', name='iterations')

    @interfaces.legacy_get_updates_support
    def get_updates(self, loss, params):
        grads = self.optimizer.compute_gradients(loss, var_list=params)
        self.updates = [K.update_add(self.iterations, 1)]
        opt_update = self.optimizer.apply_gradients(
            grads, global_step=self.iterations)
        self.updates.append(opt_update)
        return self.updates

    @property
    def weights(self):
        raise NotImplementedError

    def get_config(self):
        raise NotImplementedError

    def from_config(self, config):
        raise NotImplementedError


# Aliases.

sgd = SGD
rmsprop = RMSprop
adagrad = Adagrad
adadelta = Adadelta
adam = Adam
adamax = Adamax
nadam = Nadam


def serialize(optimizer):
    return serialize_keras_object(optimizer)


def deserialize(config, custom_objects=None):
    """Inverse of the `serialize` function.

    # Arguments
        config: Optimizer configuration dictionary.
        custom_objects: Optional dictionary mapping
            names (strings) to custom objects
            (classes and functions)
            to be considered during deserialization.

    # Returns
        A Keras Optimizer instance.
    """
    all_classes = {
        'sgd': SGD,
        'rmsprop': RMSprop,
        'adagrad': Adagrad,
        'adadelta': Adadelta,
        'adam': Adam,
        'adamax': Adamax,
        'nadam': Nadam,
        'tfoptimizer': TFOptimizer,
    }
    # Make deserialization case-insensitive for built-in optimizers.
    if config['class_name'].lower() in all_classes:
        config['class_name'] = config['class_name'].lower()
    return deserialize_keras_object(config,
                                    module_objects=all_classes,
                                    custom_objects=custom_objects,
                                    printable_module_name='optimizer')


def get(identifier):
    """Retrieves a Keras Optimizer instance.

    # Arguments
        identifier: Optimizer identifier, one of
            - String: name of an optimizer
            - Dictionary: configuration dictionary.
            - Keras Optimizer instance (it will be returned unchanged).
            - TensorFlow Optimizer instance
                (it will be wrapped as a Keras Optimizer).

    # Returns
        A Keras Optimizer instance.

    # Raises
        ValueError: If `identifier` cannot be interpreted.
    """
    if K.backend() == 'tensorflow':
        # Wrap TF optimizer instances
        if isinstance(identifier, tf.train.Optimizer):
            return TFOptimizer(identifier)
    if isinstance(identifier, dict):
        return deserialize(identifier)
    elif isinstance(identifier, six.string_types):
        config = {'class_name': str(identifier), 'config': {}}
        return deserialize(config)
    if isinstance(identifier, Optimizer):
        return identifier
    else:
        raise ValueError('Could not interpret optimizer identifier: ' +
                         str(identifier))