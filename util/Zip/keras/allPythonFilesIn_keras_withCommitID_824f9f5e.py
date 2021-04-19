from setuptools import setup
from setuptools import find_packages

setup(name = 'Keras',
      version = '0.1.1',
      description = 'Theano-based Deep Learning library',
      author = 'Francois Chollet',
      author_email = 'francois.chollet@gmail.com',
      url = 'https://github.com/fchollet/keras',
      download_url = 'https://github.com/fchollet/keras/tarball/0.1.1',
      license = 'MIT',
      install_requires = ['theano'],
      packages = find_packages(),
)
from __future__ import absolute_import
from __future__ import print_function
import theano
import theano.tensor as T
import numpy as np
import warnings, time, copy

from . import optimizers
from . import objectives
from . import callbacks as cbks
from .utils.generic_utils import Progbar, printv
from .layers import containers
from six.moves import range

def standardize_y(y):
    if not hasattr(y, 'shape'):
        y = np.asarray(y)
    if len(y.shape) == 1:
        y = np.reshape(y, (len(y), 1))
    return y

def make_batches(size, batch_size):
    nb_batch = int(np.ceil(size/float(batch_size)))
    return [(i*batch_size, min(size, (i+1)*batch_size)) for i in range(0, nb_batch)]

def standardize_X(X):
    if type(X) == list:
        return X
    else:
        return [X]

def slice_X(X, start=None, stop=None):
    if type(X) == list:
        if hasattr(start, '__len__'):
            return [x[start] for x in X]
        else:
            return [x[start:stop] for x in X]
    else:
        if hasattr(start, '__len__'):
            return X[start]
        else:
            return X[start:stop]

def calculate_loss_weights(Y, sample_weight=None, class_weight=None):
    if sample_weight is not None:
        if isinstance(sample_weight, list):
            w = np.array(sample_weight)
        else:
            w = sample_weight
    elif isinstance(class_weight, dict):
        if Y.shape[1] > 1:
            y_classes = Y.argmax(axis=1)
        elif Y.shape[1] == 1:
            y_classes = np.reshape(Y, Y.shape[0])
        else:
            y_classes = Y
        w = np.array(map(lambda x: class_weight[x], y_classes))
    else:
        w = np.ones((Y.shape[0]))
    return w

class Model(object):

    def compile(self, optimizer, loss, class_mode="categorical", theano_mode=None):
        self.optimizer = optimizers.get(optimizer)
        self.loss = objectives.get(loss)

        # input of model 
        self.X_train = self.get_input(train=True)
        self.X_test = self.get_input(train=False)

        self.y_train = self.get_output(train=True)
        self.y_test = self.get_output(train=False)

        # target of model
        self.y = T.zeros_like(self.y_train)

        # parameter for rescaling the objective function
        self.loss_weights = T.vector()

        train_loss = self.loss(self.y, self.y_train, self.loss_weights)
        test_score = self.loss(self.y, self.y_test)

        if class_mode == "categorical":
            train_accuracy = T.mean(T.eq(T.argmax(self.y, axis=-1), T.argmax(self.y_train, axis=-1)))
            test_accuracy = T.mean(T.eq(T.argmax(self.y, axis=-1), T.argmax(self.y_test, axis=-1)))

        elif class_mode == "binary":
            train_accuracy = T.mean(T.eq(self.y, T.round(self.y_train)))
            test_accuracy = T.mean(T.eq(self.y, T.round(self.y_test)))
        else:
            raise Exception("Invalid class mode:" + str(class_mode))
        self.class_mode = class_mode

        updates = self.optimizer.get_updates(self.params, self.regularizers, self.constraints, train_loss)

        if type(self.X_train) == list:
            train_ins = self.X_train + [self.y, self.loss_weights]
            test_ins = self.X_test + [self.y]
            predict_ins = self.X_test
        else:
            train_ins = [self.X_train, self.y, self.loss_weights]
            test_ins = [self.X_test, self.y]
            predict_ins = [self.X_test]

        self._train = theano.function(train_ins, train_loss, 
            updates=updates, allow_input_downcast=True, mode=theano_mode)
        self._train_with_acc = theano.function(train_ins, [train_loss, train_accuracy], 
            updates=updates, allow_input_downcast=True, mode=theano_mode)
        self._predict = theano.function(predict_ins, self.y_test, 
            allow_input_downcast=True, mode=theano_mode)
        self._test = theano.function(test_ins, test_score, 
            allow_input_downcast=True, mode=theano_mode)
        self._test_with_acc = theano.function(test_ins, [test_score, test_accuracy], 
            allow_input_downcast=True, mode=theano_mode)


    def train(self, X, y, accuracy=False, sample_weight=None, class_weight=None):
        X = standardize_X(X)
        y = standardize_y(y)

        w = calculate_loss_weights(y, sample_weight=sample_weight, class_weight=class_weight)

        ins = X + [y, w]
        if accuracy:
            return self._train_with_acc(*ins)
        else:
            return self._train(*ins)
        

    def test(self, X, y, accuracy=False):
        X = standardize_X(X)
        y = standardize_y(y)
        ins = X + [y]
        if accuracy:
            return self._test_with_acc(*ins)
        else:
            return self._test(*ins)


    def fit(self, X, y, batch_size=128, nb_epoch=100, verbose=1, callbacks=[],
            validation_split=0., validation_data=None, shuffle=True, show_accuracy=False,
            sample_weight=None, class_weight=None):

        X = standardize_X(X)
        y = standardize_y(y)

        sample_weight = calculate_loss_weights(y, sample_weight=sample_weight, class_weight=class_weight)

        do_validation = False
        if validation_data:
            try:
                X_val, y_val = validation_data
            except:
                raise Exception("Invalid format for validation data; provide a tuple (X_val, y_val). \
                    X_val may be a numpy array or a list of numpy arrays depending on your model input.")
            do_validation = True
            X_val = standardize_X(X_val)
            y_val = standardize_y(y_val)
            if verbose:
                print("Train on %d samples, validate on %d samples" % (len(y), len(y_val)))
        else:
            if 0 < validation_split < 1:
                # If a validation split size is given (e.g. validation_split=0.2)
                # then split X into smaller X and X_val,
                # and split y into smaller y and y_val.
                do_validation = True
                split_at = int(len(y) * (1 - validation_split))
                (X, X_val) = (slice_X(X, 0, split_at), slice_X(X, split_at))
                (y, y_val) = (y[0:split_at], y[split_at:])
                if verbose:
                    print("Train on %d samples, validate on %d samples" % (len(y), len(y_val)))

        index_array = np.arange(len(y))

        callbacks = cbks.CallbackList(callbacks)
        if verbose:
            callbacks.append(cbks.BaseLogger())
        callbacks.append(cbks.History())

        callbacks._set_model(self)
        callbacks._set_params({
            'batch_size': batch_size,
            'nb_epoch': nb_epoch,
            'nb_sample': len(y),
            'verbose': verbose,
            'do_validation': do_validation,
            'show_accuracy': show_accuracy
        })
        callbacks.on_train_begin()

        for epoch in range(nb_epoch):
            callbacks.on_epoch_begin(epoch)
            if shuffle:
                np.random.shuffle(index_array)

            batches = make_batches(len(y), batch_size)
            for batch_index, (batch_start, batch_end) in enumerate(batches):
                batch_ids = index_array[batch_start:batch_end]
                X_batch = slice_X(X, batch_ids)
                y_batch = y[batch_ids]

                w = sample_weight[batch_ids]

                batch_logs = {}
                batch_logs['batch'] = batch_index
                batch_logs['size'] = len(batch_ids)
                callbacks.on_batch_begin(batch_index, batch_logs)

                ins = X_batch + [y_batch, w]
                if show_accuracy:
                    loss, acc = self._train_with_acc(*ins)
                    batch_logs['accuracy'] = acc
                else:
                    loss = self._train(*ins)
                batch_logs['loss'] = loss

                callbacks.on_batch_end(batch_index, batch_logs)
                
                if batch_index == len(batches) - 1: # last batch
                    # validation
                    epoch_logs = {}
                    if do_validation:
                        if show_accuracy:
                            val_loss, val_acc = self.evaluate(X_val, y_val, batch_size=batch_size, \
                                verbose=0, show_accuracy=True)
                            epoch_logs['val_accuracy'] = val_acc
                        else:
                            val_loss = self.evaluate(X_val, y_val, batch_size=batch_size, verbose=0)
                        epoch_logs['val_loss'] = val_loss

            callbacks.on_epoch_end(epoch, epoch_logs)

        callbacks.on_train_end()
        # return history
        return callbacks.callbacks[-1]

    def predict(self, X, batch_size=128, verbose=1):
        X = standardize_X(X)
        batches = make_batches(len(X[0]), batch_size)
        if verbose == 1:
            progbar = Progbar(target=len(X[0]))
        for batch_index, (batch_start, batch_end) in enumerate(batches):
            X_batch = slice_X(X, batch_start, batch_end)
            batch_preds = self._predict(*X_batch)

            if batch_index == 0:
                shape = (len(X[0]),) + batch_preds.shape[1:]
                preds = np.zeros(shape)
            preds[batch_start:batch_end] = batch_preds

            if verbose == 1:
                progbar.update(batch_end)

        return preds

    def predict_proba(self, X, batch_size=128, verbose=1):
        preds = self.predict(X, batch_size, verbose)
        if preds.min() < 0 or preds.max() > 1:
            warnings.warn("Network returning invalid probability values.")
        return preds


    def predict_classes(self, X, batch_size=128, verbose=1):
        proba = self.predict(X, batch_size=batch_size, verbose=verbose)
        if self.class_mode == "categorical":
            return proba.argmax(axis=-1)
        else:
            return (proba > 0.5).astype('int32')


    def evaluate(self, X, y, batch_size=128, show_accuracy=False, verbose=1):
        X = standardize_X(X)
        y = standardize_y(y)

        if show_accuracy:
            tot_acc = 0.
        tot_score = 0.
        seen = 0

        batches = make_batches(len(y), batch_size)
        if verbose:
            progbar = Progbar(target=len(y), verbose=verbose)
        for batch_index, (batch_start, batch_end) in enumerate(batches):
            X_batch = slice_X(X, batch_start, batch_end)
            y_batch = y[batch_start:batch_end]

            ins = X_batch + [y_batch]
            if show_accuracy:
                loss, acc = self._test_with_acc(*ins)
                tot_acc += acc * len(y_batch)
                log_values = [('loss', loss), ('acc.', acc)]
            else:
                loss = self._test(*ins)
                log_values = [('loss', loss)]
            tot_score += loss * len(y_batch)
            seen += len(y_batch)

            # logging
            if verbose:
                progbar.update(batch_end, log_values)

        if show_accuracy:
            return tot_score / seen, tot_acc / seen
        else:
            return tot_score / seen


class Sequential(Model, containers.Sequential):
    '''
        Inherits from Model the following methods:
            - compile
            - train
            - test
            - evaluate
            - fit
            - predict
            - predict_proba
            - predict_classes
        Inherits from containers.Sequential the following methods:
            - add 
            - get_output
            - get_input
            - get_weights
            - set_weights
    '''
    def __init__(self):
        self.layers = []
        self.params = [] # learnable
        self.regularizers = [] # same size as params
        self.constraints = [] # same size as params


    def get_config(self, verbose=0):
        layers = []
        for i, l in enumerate(self.layers):
            config = l.get_config()
            layers.append(config)
        if verbose:
            printv(layers)
        return layers


    def save_weights(self, filepath, overwrite=False):
        # Save weights from all layers to HDF5
        import h5py
        import os.path
        # if file exists and should not be overwritten
        if not overwrite and os.path.isfile(filepath):
            import sys
            get_input = input
            if sys.version_info[:2] <= (2, 7):
                get_input = raw_input
            overwrite = get_input('[WARNING] %s already exists - overwrite? [y/n]' % (filepath))
            while overwrite not in ['y', 'n']:
                overwrite = get_input('Enter "y" (overwrite) or "n" (cancel).')
            if overwrite == 'n':
                return
            print('[TIP] Next time specify overwrite=True in save_weights!')

        f = h5py.File(filepath, 'w')
        f.attrs['nb_layers'] = len(self.layers)
        for k, l in enumerate(self.layers):
            g = f.create_group('layer_{}'.format(k))
            weights = l.get_weights()
            g.attrs['nb_params'] = len(weights)
            for n, param in enumerate(weights):
                param_name = 'param_{}'.format(n)
                param_dset = g.create_dataset(param_name, param.shape, dtype=param.dtype)
                param_dset[:] = param
        f.flush()
        f.close()

    def load_weights(self, filepath):
        # Loads weights from HDF5 file
        import h5py
        f = h5py.File(filepath)
        for k in range(f.attrs['nb_layers']):
            g = f['layer_{}'.format(k)]
            weights = [g['param_{}'.format(p)] for p in range(g.attrs['nb_params'])]
            self.layers[k].set_weights(weights)
        f.close()



from __future__ import absolute_import
import theano
import theano.tensor as T
import types

def softmax(x):
    return T.nnet.softmax(x)

def time_distributed_softmax(x):
    xshape = x.shape
    X = x.reshape((xshape[0] * xshape[1], xshape[2]))
    return T.nnet.softmax(X).reshape(xshape)

def softplus(x):
    return T.nnet.softplus(x)

def relu(x):
    return (x + abs(x)) / 2.0

def tanh(x):
    return T.tanh(x)

def sigmoid(x):
    return T.nnet.sigmoid(x)

def hard_sigmoid(x):
    return T.nnet.hard_sigmoid(x)

def linear(x):
    return x

from .utils.generic_utils import get_from_module
def get(identifier):
    return get_from_module(identifier, globals(), 'activation function')

from __future__ import absolute_import
import theano
import theano.tensor as T
import numpy as np

def l1(l=.01):
    def l1wrap(g, p):
        g += T.sgn(p) * l
        return g
    return l1wrap

def l2(l=.01):
    def l2wrap(g, p):
        g += p * l
        return g
    return l2wrap

def l1l2(l1=.01, l2=.01):
    def l1l2wrap(g, p):
        g += T.sgn(p) * l1
        g += p * l2
        return g
    return l1l2wrap

def identity(g, p):
    return g
from __future__ import absolute_import
import theano
import theano.tensor as T
import numpy as np

from .utils.theano_utils import shared_zeros, shared_scalar
from six.moves import zip

def clip_norm(g, c, n):
    if c > 0:
        g = T.switch(T.ge(n, c), g*c/n, g)
    return g

def kl_divergence(p, p_hat):
    return p_hat - p + p*T.log(p/p_hat)

class Optimizer(object):
    
    def get_updates(self, params, grads):
        raise NotImplementedError

    def get_gradients(self, cost, params, regularizers):
        grads = T.grad(cost, params)

        if hasattr(self, 'clipnorm') and self.clipnorm > 0:
            norm = T.sqrt(sum([T.sum(g**2) for g in grads]))
            grads = [clip_norm(g, self.clipnorm, norm) for g in grads]

        new_grads = []
        for p, g, r in zip(params, grads, regularizers):
            g = r(g, p)
            new_grads.append(g)

        return new_grads


class SGD(Optimizer):

    def __init__(self, lr=0.01, momentum=0., decay=0., nesterov=False, *args, **kwargs):
        self.__dict__.update(kwargs)
        self.__dict__.update(locals())
        self.iterations = shared_scalar(0)

    def get_updates(self, params, regularizers, constraints, cost):
        grads = self.get_gradients(cost, params, regularizers)
        lr = self.lr * (1.0 / (1.0 + self.decay * self.iterations))
        updates = [(self.iterations, self.iterations+1.)]

        for p, g, c in zip(params, grads, constraints):
            m = shared_zeros(p.get_value().shape) # momentum
            v = self.momentum * m - lr * g # velocity
            updates.append((m, v)) 

            if self.nesterov:
                new_p = p + self.momentum * v - lr * g
            else:
                new_p = p + v

            updates.append((p, c(new_p))) # apply constraints
        return updates


class RMSprop(Optimizer):

    def __init__(self, lr=0.001, rho=0.9, epsilon=1e-6, *args, **kwargs):
        self.__dict__.update(kwargs)
        self.__dict__.update(locals())

    def get_updates(self, params, regularizers, constraints, cost):
        grads = self.get_gradients(cost, params, regularizers)
        accumulators = [shared_zeros(p.get_value().shape) for p in params]
        updates = []

        for p, g, a, c in zip(params, grads, accumulators, constraints):
            new_a = self.rho * a + (1 - self.rho) * g ** 2 # update accumulator
            updates.append((a, new_a))

            new_p = p - self.lr * g / T.sqrt(new_a + self.epsilon)
            updates.append((p, c(new_p))) # apply constraints
            
        return updates


class Adagrad(Optimizer):

    def __init__(self, lr=0.01, epsilon=1e-6, *args, **kwargs):
        self.__dict__.update(kwargs)
        self.__dict__.update(locals())

    def get_updates(self, params, regularizers, constraints, cost):
        grads = self.get_gradients(cost, params, regularizers)
        accumulators = [shared_zeros(p.get_value().shape) for p in params]
        updates = []

        for p, g, a, c in zip(params, grads, accumulators, constraints):
            new_a = a + g ** 2 # update accumulator
            updates.append((a, new_a))

            new_p = p - self.lr * g / T.sqrt(new_a + self.epsilon)
            updates.append((p, c(new_p))) # apply constraints
        return updates


class Adadelta(Optimizer):
    '''
        Reference: http://arxiv.org/abs/1212.5701
    '''
    def __init__(self, lr=1.0, rho=0.95, epsilon=1e-6, *args, **kwargs):
        self.__dict__.update(kwargs)
        self.__dict__.update(locals())

    def get_updates(self, params, regularizers, constraints, cost):
        grads = self.get_gradients(cost, params, regularizers)
        accumulators = [shared_zeros(p.get_value().shape) for p in params]
        delta_accumulators = [shared_zeros(p.get_value().shape) for p in params]
        updates = []

        for p, g, a, d_a, c in zip(params, grads, accumulators, delta_accumulators, constraints):
            new_a = self.rho * a + (1 - self.rho) * g ** 2 # update accumulator
            updates.append((a, new_a))

            # use the new accumulator and the *old* delta_accumulator
            update = g * T.sqrt(d_a + self.epsilon) / T.sqrt(new_a + self.epsilon)

            new_p = p - self.lr * update
            updates.append((p, c(new_p))) # apply constraints

            # update delta_accumulator
            new_d_a = self.rho * d_a + (1 - self.rho) * update ** 2
            updates.append((d_a, new_d_a))
        return updates


class Adam(Optimizer):
    '''
        Reference: http://arxiv.org/abs/1412.6980

        Default parameters follow those provided in the original paper

        lambda is renamed kappa.
    '''
    def __init__(self, lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-8, kappa=1-1e-8, *args, **kwargs):
        self.__dict__.update(kwargs)
        self.__dict__.update(locals())
        self.iterations = shared_scalar(0)

    def get_updates(self, params, regularizers, constraints, cost):
        grads = self.get_gradients(cost, params, regularizers)
        updates = [(self.iterations, self.iterations+1.)]

        i = self.iterations
        beta_1_t = self.beta_1 * (self.kappa**i)

        # the update below seems missing from the paper, but is obviously required
        beta_2_t = self.beta_2 * (self.kappa**i) 

        for p, g, c in zip(params, grads, constraints):
            m = theano.shared(p.get_value() * 0.) # zero init of moment
            v = theano.shared(p.get_value() * 0.) # zero init of velocity

            m_t = (beta_1_t * m) + (1 - beta_1_t) * g
            v_t = (beta_2_t * v) + (1 - beta_2_t) * (g**2)

            m_b_t = m_t / (1 - beta_1_t)
            v_b_t = v_t / (1 - beta_2_t)

            p_t = p - self.lr * m_b_t / (T.sqrt(v_b_t) + self.epsilon)
            
            updates.append((m, m_t))
            updates.append((v, v_t))
            updates.append((p, c(p_t))) # apply constraints
        return updates

# aliases
sgd = SGD
rmsprop = RMSprop
adagrad = Adagrad
adadelta = Adadelta
adam = Adam

from .utils.generic_utils import get_from_module
def get(identifier):
    return get_from_module(identifier, globals(), 'optimizer', instantiate=True)

from __future__ import absolute_import
import theano
import theano.tensor as T
import numpy as np
from six.moves import range

epsilon = 1.0e-9

def mean_squared_error(y_true, y_pred, weight=None):
    if weight is not None:
        return T.sqr(weight.reshape((weight.shape[0], 1))*(y_pred - y_true)).mean()
    else:
        return T.sqr(y_pred - y_true).mean()

def mean_absolute_error(y_true, y_pred, weight=None):
    if weight is not None:
        return T.abs_(weight.reshape((weight.shape[0], 1))*(y_pred - y_true)).mean()
    else:
        return T.abs_(y_pred - y_true).mean()

def squared_hinge(y_true, y_pred, weight=None):
    if weight is not None:
        weight = weight.reshape((weight.shape[0], 1))
        return T.sqr(weight*T.maximum(1. - (y_true * y_pred), 0.)).mean()
    else:
        return T.sqr(T.maximum(1. - y_true * y_pred, 0.)).mean()

def hinge(y_true, y_pred, weight=None):
    if weight is not None:
        weight = weight.reshape((weight.shape[0], 1))
        return (weight*T.maximum(1. - (y_true * y_pred), 0.)).mean()
    else:
        return T.maximum(1. - y_true * y_pred, 0.).mean()

def categorical_crossentropy(y_true, y_pred, weight=None):
    '''Expects a binary class matrix instead of a vector of scalar classes
    '''
    y_pred = T.clip(y_pred, epsilon, 1.0 - epsilon)
    # scale preds so that the class probas of each sample sum to 1
    y_pred /= y_pred.sum(axis=1, keepdims=True) 
    cce = T.nnet.categorical_crossentropy(y_pred, y_true)
    if weight is not None:
        # return avg. of scaled cat. crossentropy
        return (weight*cce).mean()
    else:
        return cce.mean()

def binary_crossentropy(y_true, y_pred, weight=None):
    y_pred = T.clip(y_pred, epsilon, 1.0 - epsilon)
    bce = T.nnet.binary_crossentropy(y_pred, y_true)
    if weight is not None:
        return (weight.reshape((weight.shape[0], 1))*bce).mean()
    else:
        return bce.mean()

# aliases
mse = MSE = mean_squared_error
mae = MAE = mean_absolute_error

from .utils.generic_utils import get_from_module
def get(identifier):
    return get_from_module(identifier, globals(), 'objective')

def to_categorical(y):
    '''Convert class vector (integers from 0 to nb_classes)
    to binary class matrix, for use with categorical_crossentropy
    '''
    nb_classes = np.max(y)+1
    Y = np.zeros((len(y), nb_classes))
    for i in range(len(y)):
        Y[i, y[i]] = 1.
    return Y

from __future__ import absolute_import
from __future__ import print_function
import theano
import theano.tensor as T
import numpy as np
import warnings
import time
from collections import deque

from .utils.generic_utils import Progbar

class CallbackList(object):

    def __init__(self, callbacks=[], queue_length=10):
        self.callbacks = [c for c in callbacks]
        self.queue_length = queue_length

    def append(self, callback):
        self.callbacks.append(callback)

    def _set_params(self, params):
        for callback in self.callbacks:
            callback._set_params(params)

    def _set_model(self, model):
        for callback in self.callbacks:
            callback._set_model(model)

    def on_epoch_begin(self, epoch, logs={}):
        for callback in self.callbacks:
            callback.on_epoch_begin(epoch, logs)
        self._delta_t_batch = 0.
        self._delta_ts_batch_begin = deque([], maxlen=self.queue_length)
        self._delta_ts_batch_end = deque([], maxlen=self.queue_length)

    def on_epoch_end(self, epoch, logs={}):
        for callback in self.callbacks:
            callback.on_epoch_end(epoch, logs)

    def on_batch_begin(self, batch, logs={}):
        t_before_callbacks = time.time()
        for callback in self.callbacks:
            callback.on_batch_begin(batch, logs)
        self._delta_ts_batch_begin.append(time.time() - t_before_callbacks)
        delta_t_median = np.median(self._delta_ts_batch_begin)
        if self._delta_t_batch > 0. and delta_t_median > 0.95 * self._delta_t_batch \
            and delta_t_median > 0.1:
            warnings.warn('Method on_batch_begin() is slow compared '
                'to the batch update (%f). Check your callbacks.' % delta_t_median)
        self._t_enter_batch = time.time()

    def on_batch_end(self, batch, logs={}):
        self._delta_t_batch = time.time() - self._t_enter_batch
        t_before_callbacks = time.time()
        for callback in self.callbacks:
            callback.on_batch_end(batch, logs)
        self._delta_ts_batch_end.append(time.time() - t_before_callbacks)
        delta_t_median = np.median(self._delta_ts_batch_end)
        if self._delta_t_batch > 0. and delta_t_median > 0.95 * self._delta_t_batch \
            and delta_t_median > 0.1:
            warnings.warn('Method on_batch_end() is slow compared '
                'to the batch update (%f). Check your callbacks.' % delta_t_median)

    def on_train_begin(self, logs={}):
        for callback in self.callbacks:
            callback.on_train_begin(logs)

    def on_train_end(self, logs={}):
        for callback in self.callbacks:
            callback.on_train_end(logs)


class Callback(object):

    def __init__(self):
        pass

    def _set_params(self, params):
        self.params = params

    def _set_model(self, model):
        self.model = model

    def on_epoch_begin(self, epoch, logs={}):
        pass

    def on_epoch_end(self, epoch, logs={}):
        pass

    def on_batch_begin(self, batch, logs={}):
        pass

    def on_batch_end(self, batch, logs={}):
        pass

    def on_train_begin(self, logs={}):
        pass

    def on_train_end(self, logs={}):
        pass

class BaseLogger(Callback):

    def on_train_begin(self, logs={}):
        self.verbose = self.params['verbose']

    def on_epoch_begin(self, epoch, logs={}):
        if self.verbose:
            print('Epoch %d' % epoch)
            self.progbar = Progbar(target=self.params['nb_sample'], \
                verbose=self.verbose)
        self.current = 0
        self.tot_loss = 0.
        self.tot_acc = 0.

    def on_batch_begin(self, batch, logs={}):
        if self.current < self.params['nb_sample']:
            self.log_values = []

    def on_batch_end(self, batch, logs={}):
        batch_size = logs.get('size', 0)
        self.current += batch_size

        loss = logs.get('loss')
        self.log_values.append(('loss', loss))
        self.tot_loss += loss * batch_size
        if self.params['show_accuracy']:
            accuracy = logs.get('accuracy')
            self.log_values.append(('acc.', accuracy))
            self.tot_acc += accuracy * batch_size
        # skip progbar update for the last batch; will be handled by on_epoch_end
        if self.verbose and self.current < self.params['nb_sample']:
            self.progbar.update(self.current, self.log_values)

    def on_epoch_end(self, epoch, logs={}):
        self.log_values.append(('loss', self.tot_loss / self.current))
        if self.params['show_accuracy']:
            self.log_values.append(('acc.', self.tot_acc / self.current))
        if self.params['do_validation']:
            val_loss = logs.get('val_loss')
            self.log_values.append(('val. loss', val_loss))
            if self.params['show_accuracy']:
                val_acc = logs.get('val_accuracy')
                self.log_values.append(('val. acc.', val_acc))
        self.progbar.update(self.current, self.log_values)


class History(Callback):

    def on_train_begin(self, logs={}):
        self.epoch = []
        self.loss = []
        if self.params['show_accuracy']:
            self.accuracy = []
        if self.params['do_validation']:
            self.validation_loss = []
            if self.params['show_accuracy']:
                self.validation_accuracy = []

    def on_epoch_begin(self, epoch, logs={}):
        self.seen = 0
        self.tot_loss = 0.
        self.tot_accuracy = 0.

    def on_batch_end(self, batch, logs={}):
        batch_size = logs.get('size', 0)
        self.seen += batch_size
        self.tot_loss += logs.get('loss', 0.) * batch_size
        if self.params['show_accuracy']:
            self.tot_accuracy += logs.get('accuracy', 0.) * batch_size

    def on_epoch_end(self, epoch, logs={}):
        val_loss = logs.get('val_loss')
        val_acc = logs.get('val_accuracy')
        self.epoch.append(epoch)
        self.loss.append(self.tot_loss / self.seen)
        if self.params['show_accuracy']:
            self.accuracy.append(self.tot_accuracy / self.seen)
        if self.params['do_validation']:
            self.validation_loss.append(val_loss)
            if self.params['show_accuracy']:
                self.validation_accuracy.append(val_acc)

class ModelCheckpoint(Callback):
    def __init__(self, filepath, verbose=0, save_best_only=False):
        super(Callback, self).__init__()
        
        self.verbose = verbose
        self.filepath = filepath
        self.save_best_only = save_best_only
        self.loss = []
        self.best_loss = np.Inf
        self.val_loss = []
        self.best_val_loss = np.Inf

    def on_epoch_end(self, epoch, logs={}):
        '''currently, on_epoch_end receives epoch_logs from keras.models.Sequential.fit
        which does only contain, if at all, the validation loss and validation accuracy'''
        if self.save_best_only and self.params['do_validation']:
            cur_val_loss = logs.get('val_loss')
            self.val_loss.append(cur_val_loss)
            if cur_val_loss < self.best_val_loss:
                if self.verbose > 0:
                    print("Epoch %05d: validation loss improved from %0.5f to %0.5f, saving model to %s"
                        % (epoch, self.best_val_loss, cur_val_loss, self.filepath))
                self.best_val_loss = cur_val_loss
                self.model.save_weights(self.filepath, overwrite=True)
            else:
                if self.verbose > 0:
                    print("Epoch %05d: validation loss did not improve" % (epoch))
        elif self.save_best_only and not self.params['do_validation']:
            import warnings
            warnings.warn("Can save best model only with validation data, skipping", RuntimeWarning)
        elif not self.save_best_only:
            if self.verbose > 0:
                print("Epoch %05d: saving model to %s" % (epoch, self.filepath))
            self.model.save_weights(self.filepath, overwrite=True)


from __future__ import absolute_import
import theano
import theano.tensor as T
import numpy as np

def maxnorm(m=2):
    def maxnorm_wrap(p):
        norms = T.sqrt(T.sum(T.sqr(p), axis=0))
        desired = T.clip(norms, 0, m)
        p = p * (desired / (1e-7 + norms))
        return p
    return maxnorm_wrap

def nonneg(p):
    p *= T.ge(p, 0)
    return p

def identity(g):
    return g

def unitnorm(e):
    return e / T.sqrt(T.sum(e**2, axis=-1, keepdims=True))

from __future__ import absolute_import
import theano
import theano.tensor as T
import numpy as np

from .utils.theano_utils import sharedX, shared_zeros

def get_fans(shape):
    fan_in = shape[0] if len(shape) == 2 else np.prod(shape[1:])
    fan_out = shape[1] if len(shape) == 2 else shape[0]
    return fan_in, fan_out


def uniform(shape, scale=0.05):
    return sharedX(np.random.uniform(low=-scale, high=scale, size=shape))

def normal(shape, scale=0.05):
    return sharedX(np.random.randn(*shape) * scale)

def lecun_uniform(shape):
    ''' Reference: LeCun 98, Efficient Backprop
        http://yann.lecun.com/exdb/publis/pdf/lecun-98b.pdf
    '''
    fan_in, fan_out = get_fans(shape)
    scale = 1./np.sqrt(fan_in)
    return uniform(shape, scale)

def glorot_normal(shape):
    ''' Reference: Glorot & Bengio, AISTATS 2010
    '''
    fan_in, fan_out = get_fans(shape)
    s = np.sqrt(2. / (fan_in + fan_out))
    return normal(shape, s)

def glorot_uniform(shape):
    fan_in, fan_out = get_fans(shape)
    s = np.sqrt(2. / (fan_in + fan_out))
    return uniform(shape, s)
    
def he_normal(shape):
    ''' Reference:  He et al., http://arxiv.org/abs/1502.01852
    '''
    fan_in, fan_out = get_fans(shape)
    s = np.sqrt(2. / fan_in)
    return normal(shape, s)

def he_uniform(shape):
    fan_in, fan_out = get_fans(shape)
    s = np.sqrt(2. / fan_in)
    return uniform(shape, s)

def orthogonal(shape, scale=1.1):
    ''' From Lasagne
    '''
    flat_shape = (shape[0], np.prod(shape[1:]))
    a = np.random.normal(0.0, 1.0, flat_shape)
    u, _, v = np.linalg.svd(a, full_matrices=False)
    q = u if u.shape == flat_shape else v # pick the one with the correct shape
    q = q.reshape(shape)
    return sharedX(scale * q[:shape[0], :shape[1]])

def zero(shape):
    return shared_zeros(shape)


from .utils.generic_utils import get_from_module
def get(identifier):
    return get_from_module(identifier, globals(), 'initialization')


from __future__ import absolute_import
import copy
import numpy as np

from ..utils.np_utils import to_categorical

class KerasClassifier(object):
    """
    Implementation of the scikit-learn classifier API for Keras.

    Parameters
    ----------
    model : object
        An un-compiled Keras model object is required to use the scikit-learn wrapper.
    optimizer : string, optional
        Optimization method used by the model during compilation/training.
    loss : string, optional
        Loss function used by the model during compilation/training.
    """
    def __init__(self, model, optimizer='adam', loss='categorical_crossentropy'):
        self.model = model
        self.optimizer = optimizer
        self.loss = loss
        self.compiled_model_ = None
        self.classes_ = []
        self.config_ = []
        self.weights_ = []

    def get_params(self, deep=True):
        """
        Get parameters for this estimator.

        Parameters
        ----------
        deep: boolean, optional
            If True, will return the parameters for this estimator and
            contained subobjects that are estimators.

        Returns
        -------
        params : dict
            Dictionary of parameter names mapped to their values.
        """
        return {'model': self.model, 'optimizer': self.optimizer, 'loss': self.loss}

    def set_params(self, **params):
        """
        Set the parameters of this estimator.

        Parameters
        ----------
        params: dict
            Dictionary of parameter names mapped to their values.

        Returns
        -------
        self
        """
        for parameter, value in params.items():
            setattr(self, parameter, value)
        return self

    def fit(self, X, y, batch_size=128, nb_epoch=100, verbose=0, shuffle=True):
        """
        Fit the model according to the given training data.

        Makes a copy of the un-compiled model definition to use for
        compilation and fitting, leaving the original definition
        intact.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Training samples where n_samples in the number of samples
            and n_features is the number of features.
        y : array-like, shape = (n_samples) or (n_samples, n_outputs)
            True labels for X.
        batch_size : int, optional
            Number of training samples evaluated at a time.
        nb_epochs : int, optional
            Number of training epochs.
        verbose : int, optional
            Verbosity level.
        shuffle : boolean, optional
            Indicator to shuffle the training data.

        Returns
        -------
        self : object
            Returns self.
        """
        if len(y.shape) == 1:
            self.classes_ = list(np.unique(y))
            if self.loss == 'categorical_crossentropy':
                y = to_categorical(y)
        else:
            self.classes_ = np.arange(0, y.shape[1])

        self.compiled_model_ = copy.deepcopy(self.model)
        self.compiled_model_.compile(optimizer=self.optimizer, loss=self.loss)
        self.compiled_model_.fit(X, y, batch_size=batch_size, nb_epoch=nb_epoch, verbose=verbose, shuffle=shuffle)
        self.config_ = self.model.get_config()
        self.weights_ = self.model.get_weights()

        return self

    def score(self, X, y, batch_size=128, verbose=0):
        """
        Returns the mean accuracy on the given test data and labels.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Test samples where n_samples in the number of samples
            and n_features is the number of features.
        y : array-like, shape = (n_samples) or (n_samples, n_outputs)
            True labels for X.
        batch_size : int, optional
            Number of test samples evaluated at a time.
        verbose : int, optional
            Verbosity level.

        Returns
        -------
        score : float
            Mean accuracy of self.predict(X) wrt. y.
        """
        loss, accuracy = self.compiled_model_.evaluate(X, y, batch_size=batch_size,
                                                       show_accuracy=True, verbose=verbose)
        return accuracy

    def predict(self, X, batch_size=128, verbose=0):
        """
        Returns the class predictions for the given test data.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Test samples where n_samples in the number of samples
            and n_features is the number of features.
        batch_size : int, optional
            Number of test samples evaluated at a time.
        verbose : int, optional
            Verbosity level.

        Returns
        -------
        preds : array-like, shape = (n_samples)
            Class predictions.
        """
        return self.compiled_model_.predict_classes(X, batch_size=batch_size, verbose=verbose)

    def predict_proba(self, X, batch_size=128, verbose=0):
        """
        Returns class probability estimates for the given test data.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Test samples where n_samples in the number of samples
            and n_features is the number of features.
        batch_size : int, optional
            Number of test samples evaluated at a time.
        verbose : int, optional
            Verbosity level.

        Returns
        -------
        proba : array-like, shape = (n_samples, n_outputs)
            Class probability estimates.
        """
        return self.compiled_model_.predict_proba(X, batch_size=batch_size, verbose=verbose)

# -*- coding: utf-8 -*-
from __future__ import absolute_import

import theano
import theano.tensor as T
from theano.tensor.signal import downsample

from .. import activations, initializations
from ..utils.theano_utils import shared_zeros
from ..layers.core import Layer


class Convolution1D(Layer):
    def __init__(self, nb_filter, stack_size, filter_length,
        init='uniform', activation='linear', weights=None,
        image_shape=None, border_mode='valid', subsample_length=1,
        W_regularizer=None, b_regularizer=None, W_constraint=None, b_constraint=None):

        nb_row = 1
        nb_col = filter_length
        
        self.nb_filter = nb_filter
        self.stack_size = stack_size
        self.filter_length = filter_length
        self.subsample_length = subsample_length
        self.init = initializations.get(init)
        self.activation = activations.get(activation)
        self.subsample = (1, subsample_length)
        self.border_mode = border_mode
        self.image_shape = image_shape

        self.input = T.tensor4()
        self.W_shape = (nb_filter, stack_size, nb_row, nb_col)
        self.W = self.init(self.W_shape)
        self.b = shared_zeros((nb_filter,))

        self.params = [self.W, self.b]

        self.regularizers = [W_regularizer, b_regularizer]
        self.constraints = [W_constraint, b_constraint]

        if weights is not None:
            self.set_weights(weights)

    def get_output(self, train):
        X = self.get_input(train)

        conv_out = theano.tensor.nnet.conv.conv2d(X, self.W,
            border_mode=self.border_mode, subsample=self.subsample, image_shape=self.image_shape)
        output = self.activation(conv_out + self.b.dimshuffle('x', 0, 'x', 'x'))
        return output

    def get_config(self):
        return {"name":self.__class__.__name__,
            "nb_filter":self.nb_filter,
            "stack_size":self.stack_size,
            "filter_length":self.filter_length,
            "init":self.init.__name__,
            "activation":self.activation.__name__,
            "image_shape":self.image_shape,
            "border_mode":self.border_mode,
            "subsample_length":self.subsample_length}


class MaxPooling1D(Layer):
    def __init__(self, pool_length=2, ignore_border=True):
        self.pool_length = pool_length
        self.poolsize = (1, pool_length)
        self.ignore_border = ignore_border
        
        self.input = T.tensor4()
        self.params = []

    def get_output(self, train):
        X = self.get_input(train)
        output = downsample.max_pool_2d(X, self.poolsize, ignore_border=self.ignore_border)
        return output

    def get_config(self):
        return {"name":self.__class__.__name__,
            "pool_length":self.pool_length,
            "ignore_border":self.ignore_border}



class Convolution2D(Layer):
    def __init__(self, nb_filter, stack_size, nb_row, nb_col, 
        init='glorot_uniform', activation='linear', weights=None, 
        image_shape=None, border_mode='valid', subsample=(1,1),
        W_regularizer=None, b_regularizer=None, W_constraint=None, b_constraint=None):
        super(Convolution2D,self).__init__()

        self.init = initializations.get(init)
        self.activation = activations.get(activation)
        self.subsample = subsample
        self.border_mode = border_mode
        self.image_shape = image_shape
        self.nb_filter = nb_filter
        self.stack_size = stack_size
        self.nb_row = nb_row
        self.nb_col = nb_col

        self.input = T.tensor4()
        self.W_shape = (nb_filter, stack_size, nb_row, nb_col)
        self.W = self.init(self.W_shape)
        self.b = shared_zeros((nb_filter,))

        self.params = [self.W, self.b]

        self.regularizers = [W_regularizer, b_regularizer]
        self.constraints = [W_constraint, b_constraint]

        if weights is not None:
            self.set_weights(weights)

    def get_output(self, train):
        X = self.get_input(train)

        conv_out = theano.tensor.nnet.conv.conv2d(X, self.W, 
            border_mode=self.border_mode, subsample=self.subsample, image_shape=self.image_shape)
        output = self.activation(conv_out + self.b.dimshuffle('x', 0, 'x', 'x'))
        return output

    def get_config(self):
        return {"name":self.__class__.__name__,
            "nb_filter":self.nb_filter,
            "stack_size":self.stack_size,
            "nb_row":self.nb_row,
            "nb_col":self.nb_col,
            "init":self.init.__name__,
            "activation":self.activation.__name__,
            "image_shape":self.image_shape,
            "border_mode":self.border_mode,
            "subsample":self.subsample}


class MaxPooling2D(Layer):
    def __init__(self, poolsize=(2, 2), ignore_border=True):
        super(MaxPooling2D,self).__init__()
        self.input = T.tensor4()
        self.poolsize = poolsize
        self.ignore_border = ignore_border

    def get_output(self, train):
        X = self.get_input(train)
        output = downsample.max_pool_2d(X, self.poolsize, ignore_border=self.ignore_border)
        return output

    def get_config(self):
        return {"name":self.__class__.__name__,
            "poolsize":self.poolsize,
            "ignore_border":self.ignore_border}



# class ZeroPadding2D(Layer): TODO

# class Convolution3D: TODO

# class MaxPooling3D: TODO
        

# -*- coding: utf-8 -*-
from __future__ import absolute_import
import theano
import theano.tensor as T
import numpy as np

from .. import activations, initializations
from ..utils.theano_utils import shared_zeros, alloc_zeros_matrix
from ..layers.core import Layer
from six.moves import range

class SimpleRNN(Layer):
    '''
        Fully connected RNN where output is to fed back to input.

        Not a particularly useful model, 
        included for demonstration purposes 
        (demonstrates how to use theano.scan to build a basic RNN).
    '''
    def __init__(self, input_dim, output_dim, 
        init='glorot_uniform', inner_init='orthogonal', activation='sigmoid', weights=None,
        truncate_gradient=-1, return_sequences=False):
        super(SimpleRNN,self).__init__()
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.truncate_gradient = truncate_gradient
        self.activation = activations.get(activation)
        self.return_sequences = return_sequences
        self.input = T.tensor3()

        self.W = self.init((self.input_dim, self.output_dim))
        self.U = self.inner_init((self.output_dim, self.output_dim))
        self.b = shared_zeros((self.output_dim))
        self.params = [self.W, self.U, self.b]

        if weights is not None:
            self.set_weights(weights)

    def _step(self, x_t, h_tm1, u):
        '''
            Variable names follow the conventions from: 
            http://deeplearning.net/software/theano/library/scan.html

        '''
        return self.activation(x_t + T.dot(h_tm1, u))

    def get_output(self, train):
        X = self.get_input(train) # shape: (nb_samples, time (padded with zeros at the end), input_dim)
        # new shape: (time, nb_samples, input_dim) -> because theano.scan iterates over main dimension
        X = X.dimshuffle((1,0,2)) 

        x = T.dot(X, self.W) + self.b
        
        # scan = theano symbolic loop.
        # See: http://deeplearning.net/software/theano/library/scan.html
        # Iterate over the first dimension of the x array (=time).
        outputs, updates = theano.scan(
            self._step, # this will be called with arguments (sequences[i], outputs[i-1], non_sequences[i])
            sequences=x, # tensors to iterate over, inputs to _step
            # initialization of the output. Input to _step with default tap=-1.
            outputs_info=T.unbroadcast(alloc_zeros_matrix(X.shape[1], self.output_dim), 1),
            non_sequences=self.U, # static inputs to _step
            truncate_gradient=self.truncate_gradient
        )
        if self.return_sequences:
            return outputs.dimshuffle((1,0,2))
        return outputs[-1]

    def get_config(self):
        return {"name":self.__class__.__name__,
            "input_dim":self.input_dim,
            "output_dim":self.output_dim,
            "init":self.init.__name__,
            "inner_init":self.inner_init.__name__,
            "activation":self.activation.__name__,
            "truncate_gradient":self.truncate_gradient,
            "return_sequences":self.return_sequences}


class SimpleDeepRNN(Layer):
    '''
        Fully connected RNN where the output of multiple timesteps 
        (up to "depth" steps in the past) is fed back to the input:

        output = activation( W.x_t + b + inner_activation(U_1.h_tm1) + inner_activation(U_2.h_tm2) + ... )

        This demonstrates how to build RNNs with arbitrary lookback. 
        Also (probably) not a super useful model.
    '''
    def __init__(self, input_dim, output_dim, depth=3,
        init='glorot_uniform', inner_init='orthogonal', 
        activation='sigmoid', inner_activation='hard_sigmoid',
        weights=None, truncate_gradient=-1, return_sequences=False):
        super(SimpleDeepRNN,self).__init__()
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.truncate_gradient = truncate_gradient
        self.activation = activations.get(activation)
        self.inner_activation = activations.get(inner_activation)
        self.depth = depth
        self.return_sequences = return_sequences
        self.input = T.tensor3()

        self.W = self.init((self.input_dim, self.output_dim))
        self.Us = [self.inner_init((self.output_dim, self.output_dim)) for _ in range(self.depth)]
        self.b = shared_zeros((self.output_dim))
        self.params = [self.W] + self.Us + [self.b]

        if weights is not None:
            self.set_weights(weights)

    def _step(self, *args):
        o = args[0]
        for i in range(1, self.depth+1):
            o += self.inner_activation(T.dot(args[i], args[i+self.depth]))
        return self.activation(o)

    def get_output(self, train):
        X = self.get_input(train)
        X = X.dimshuffle((1,0,2)) 

        x = T.dot(X, self.W) + self.b
        
        outputs, updates = theano.scan(
            self._step,
            sequences=x,
            outputs_info=[dict(
                initial=T.alloc(np.cast[theano.config.floatX](0.), self.depth, X.shape[1], self.output_dim),
                taps = [(-i-1) for i in range(self.depth)]
            )],
            non_sequences=self.Us,
            truncate_gradient=self.truncate_gradient
        )
        if self.return_sequences:
            return outputs.dimshuffle((1,0,2))
        return outputs[-1]

    def get_config(self):
        return {"name":self.__class__.__name__,
            "input_dim":self.input_dim,
            "output_dim":self.output_dim,
            "depth":self.depth,
            "init":self.init.__name__,
            "inner_init":self.inner_init.__name__,
            "activation":self.activation.__name__,
            "inner_activation":self.inner_activation.__name__,
            "truncate_gradient":self.truncate_gradient,
            "return_sequences":self.return_sequences}



class GRU(Layer):
    '''
        Gated Recurrent Unit - Cho et al. 2014

        Acts as a spatiotemporal projection,
        turning a sequence of vectors into a single vector.

        Eats inputs with shape:
        (nb_samples, max_sample_length (samples shorter than this are padded with zeros at the end), input_dim)

        and returns outputs with shape:
        if not return_sequences:
            (nb_samples, output_dim)
        if return_sequences:
            (nb_samples, max_sample_length, output_dim)

        References:
            On the Properties of Neural Machine Translation: Encoderâ€“Decoder Approaches
                http://www.aclweb.org/anthology/W14-4012
            Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling
                http://arxiv.org/pdf/1412.3555v1.pdf
    '''
    def __init__(self, input_dim, output_dim=128, 
        init='glorot_uniform', inner_init='orthogonal',
        activation='sigmoid', inner_activation='hard_sigmoid',
        weights=None, truncate_gradient=-1, return_sequences=False):

        super(GRU,self).__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.truncate_gradient = truncate_gradient
        self.return_sequences = return_sequences

        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.activation = activations.get(activation)
        self.inner_activation = activations.get(inner_activation)
        self.input = T.tensor3()

        self.W_z = self.init((self.input_dim, self.output_dim))
        self.U_z = self.inner_init((self.output_dim, self.output_dim))
        self.b_z = shared_zeros((self.output_dim))

        self.W_r = self.init((self.input_dim, self.output_dim))
        self.U_r = self.inner_init((self.output_dim, self.output_dim))
        self.b_r = shared_zeros((self.output_dim))

        self.W_h = self.init((self.input_dim, self.output_dim)) 
        self.U_h = self.inner_init((self.output_dim, self.output_dim))
        self.b_h = shared_zeros((self.output_dim))

        self.params = [
            self.W_z, self.U_z, self.b_z,
            self.W_r, self.U_r, self.b_r,
            self.W_h, self.U_h, self.b_h,
        ]

        if weights is not None:
            self.set_weights(weights)

    def _step(self, 
        xz_t, xr_t, xh_t, 
        h_tm1, 
        u_z, u_r, u_h):
        z = self.inner_activation(xz_t + T.dot(h_tm1, u_z))
        r = self.inner_activation(xr_t + T.dot(h_tm1, u_r))
        hh_t = self.activation(xh_t + T.dot(r * h_tm1, u_h))
        h_t = z * h_tm1 + (1 - z) * hh_t
        return h_t

    def get_output(self, train):
        X = self.get_input(train) 
        X = X.dimshuffle((1,0,2)) 

        x_z = T.dot(X, self.W_z) + self.b_z
        x_r = T.dot(X, self.W_r) + self.b_r
        x_h = T.dot(X, self.W_h) + self.b_h
        outputs, updates = theano.scan(
            self._step, 
            sequences=[x_z, x_r, x_h], 
            outputs_info=T.unbroadcast(alloc_zeros_matrix(X.shape[1], self.output_dim), 1),
            non_sequences=[self.U_z, self.U_r, self.U_h],
            truncate_gradient=self.truncate_gradient
        )
        if self.return_sequences:
            return outputs.dimshuffle((1,0,2))
        return outputs[-1]

    def get_config(self):
        return {"name":self.__class__.__name__,
            "input_dim":self.input_dim,
            "output_dim":self.output_dim,
            "init":self.init.__name__,
            "inner_init":self.inner_init.__name__,
            "activation":self.activation.__name__,
            "inner_activation":self.inner_activation.__name__,
            "truncate_gradient":self.truncate_gradient,
            "return_sequences":self.return_sequences}



class LSTM(Layer):
    '''
        Acts as a spatiotemporal projection,
        turning a sequence of vectors into a single vector.

        Eats inputs with shape:
        (nb_samples, max_sample_length (samples shorter than this are padded with zeros at the end), input_dim)

        and returns outputs with shape:
        if not return_sequences:
            (nb_samples, output_dim)
        if return_sequences:
            (nb_samples, max_sample_length, output_dim)

        For a step-by-step description of the algorithm, see:
        http://deeplearning.net/tutorial/lstm.html

        References:
            Long short-term memory (original 97 paper)
                http://deeplearning.cs.cmu.edu/pdfs/Hochreiter97_lstm.pdf
            Learning to forget: Continual prediction with LSTM
                http://www.mitpressjournals.org/doi/pdf/10.1162/089976600300015015
            Supervised sequence labelling with recurrent neural networks
                http://www.cs.toronto.edu/~graves/preprint.pdf
    '''
    def __init__(self, input_dim, output_dim=128, 
        init='glorot_uniform', inner_init='orthogonal', 
        activation='tanh', inner_activation='hard_sigmoid',
        weights=None, truncate_gradient=-1, return_sequences=False):
    
        super(LSTM,self).__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.truncate_gradient = truncate_gradient
        self.return_sequences = return_sequences

        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.activation = activations.get(activation)
        self.inner_activation = activations.get(inner_activation)
        self.input = T.tensor3()

        self.W_i = self.init((self.input_dim, self.output_dim))
        self.U_i = self.inner_init((self.output_dim, self.output_dim))
        self.b_i = shared_zeros((self.output_dim))

        self.W_f = self.init((self.input_dim, self.output_dim))
        self.U_f = self.inner_init((self.output_dim, self.output_dim))
        self.b_f = shared_zeros((self.output_dim))

        self.W_c = self.init((self.input_dim, self.output_dim))
        self.U_c = self.inner_init((self.output_dim, self.output_dim))
        self.b_c = shared_zeros((self.output_dim))

        self.W_o = self.init((self.input_dim, self.output_dim))
        self.U_o = self.inner_init((self.output_dim, self.output_dim))
        self.b_o = shared_zeros((self.output_dim))

        self.params = [
            self.W_i, self.U_i, self.b_i,
            self.W_c, self.U_c, self.b_c,
            self.W_f, self.U_f, self.b_f,
            self.W_o, self.U_o, self.b_o,
        ]

        if weights is not None:
            self.set_weights(weights)

    def _step(self, 
        xi_t, xf_t, xo_t, xc_t, 
        h_tm1, c_tm1, 
        u_i, u_f, u_o, u_c): 
        i_t = self.inner_activation(xi_t + T.dot(h_tm1, u_i))
        f_t = self.inner_activation(xf_t + T.dot(h_tm1, u_f))
        c_t = f_t * c_tm1 + i_t * self.activation(xc_t + T.dot(h_tm1, u_c))
        o_t = self.inner_activation(xo_t + T.dot(h_tm1, u_o))
        h_t = o_t * self.activation(c_t)
        return h_t, c_t

    def get_output(self, train):
        X = self.get_input(train) 
        X = X.dimshuffle((1,0,2))

        xi = T.dot(X, self.W_i) + self.b_i
        xf = T.dot(X, self.W_f) + self.b_f
        xc = T.dot(X, self.W_c) + self.b_c
        xo = T.dot(X, self.W_o) + self.b_o
        
        [outputs, memories], updates = theano.scan(
            self._step, 
            sequences=[xi, xf, xo, xc],
            outputs_info=[
                T.unbroadcast(alloc_zeros_matrix(X.shape[1], self.output_dim), 1),
                T.unbroadcast(alloc_zeros_matrix(X.shape[1], self.output_dim), 1)
            ], 
            non_sequences=[self.U_i, self.U_f, self.U_o, self.U_c], 
            truncate_gradient=self.truncate_gradient 
        )
        if self.return_sequences:
            return outputs.dimshuffle((1,0,2))
        return outputs[-1]

    def get_config(self):
        return {"name":self.__class__.__name__,
            "input_dim":self.input_dim,
            "output_dim":self.output_dim,
            "init":self.init.__name__,
            "inner_init":self.inner_init.__name__,
            "activation":self.activation.__name__,
            "inner_activation":self.inner_activation.__name__,
            "truncate_gradient":self.truncate_gradient,
            "return_sequences":self.return_sequences}
        


# -*- coding: utf-8 -*-
from __future__ import absolute_import

import theano.tensor as T
from ..layers.core import Layer
from six.moves import range

def ndim_tensor(ndim):
    if ndim == 2:
        return T.matrix()
    elif ndim == 3:
        return T.tensor3()
    elif ndim == 4:
        return T.tensor4()
    return T.matrix()

class Sequential(Layer):
    def __init__(self, layers=[]):
        self.layers = []
        self.params = []
        self.regularizers = []
        self.constraints = []
        for layer in layers:
            self.add(layer)

    def connect(self, layer):
        self.layers[0].previous = layer

    def add(self, layer):
        self.layers.append(layer)
        if len(self.layers) > 1:
            self.layers[-1].connect(self.layers[-2])
        
        params, regularizers, constraints = layer.get_params()
        self.params += params
        self.regularizers += regularizers
        self.constraints += constraints

    def get_output(self, train=False):
        return self.layers[-1].get_output(train)

    def get_input(self, train=False):
        if not hasattr(self.layers[0], 'input'):
            for l in self.layers:
                if hasattr(l, 'input'):
                    break
            ndim = l.input.ndim 
            self.layers[0].input = ndim_tensor(ndim)
        return self.layers[0].get_input(train)

    @property
    def input(self):
        return self.get_input()

    def get_weights(self):
        weights = []
        for layer in self.layers:
            weights += layer.get_weights()
        return weights

    def set_weights(self, weights):
        for i in range(len(self.layers)):
            nb_param = len(self.layers[i].params)
            self.layers[i].set_weights(weights[:nb_param])
            weights = weights[nb_param:]

    def get_config(self):
        return {"name":self.__class__.__name__,
            "layers":[layer.get_config() for layer in self.layers]}

# -*- coding: utf-8 -*-
from __future__ import absolute_import, division

import theano
import theano.tensor as T

from .. import activations, initializations
from ..utils.theano_utils import shared_zeros, floatX
from ..utils.generic_utils import make_tuple
from .. import regularizers
from .. import constraints

from theano.sandbox.rng_mrg import MRG_RandomStreams as RandomStreams
from six.moves import zip
srng = RandomStreams()

class Layer(object):
    def __init__(self):
        self.params = []

    def connect(self, layer):
        self.previous = layer

    def get_output(self, train):
        raise NotImplementedError

    def get_input(self, train):
        if hasattr(self, 'previous'):
            return self.previous.get_output(train=train)
        else:
            return self.input

    def set_weights(self, weights):
        for p, w in zip(self.params, weights):
            if p.eval().shape != w.shape:
                raise Exception("Layer shape %s not compatible with weight shape %s." % (p.eval().shape, w.shape))
            p.set_value(floatX(w))

    def get_weights(self):
        weights = []
        for p in self.params:
            weights.append(p.get_value())
        return weights

    def get_config(self):
        return {"name":self.__class__.__name__}

    def get_params(self):
        regs = []
        consts = []

        if hasattr(self, 'regularizers') and len(self.regularizers) == len(self.params):
            for r in self.regularizers:
                if r:
                    regs.append(r)
                else:
                    regs.append(regularizers.identity)
        elif hasattr(self, 'regularizer') and self.regularizer:
            regs += [self.regularizer for _ in range(len(self.params))]
        else:
            regs += [regularizers.identity for _ in range(len(self.params))]

        if hasattr(self, 'constraints') and len(self.constraints) == len(self.params):
            for c in self.constraints:
                if c:
                    consts.append(c)
                else:
                    consts.append(constraints.identity)
        elif hasattr(self, 'constraint') and self.constraint:
            consts += [self.constraint for _ in range(len(self.params))]
        else:
            consts += [constraints.identity for _ in range(len(self.params))]

        return self.params, regs, consts


class Merge(object): 
    def __init__(self, models, mode='sum'):
        ''' Merge the output of a list of models into a single tensor.
            mode: {'sum', 'concat'}
        '''
        if len(models) < 2:
            raise Exception("Please specify two or more input models to merge")
        self.mode = mode
        self.models = models
        self.params = []
        self.regularizers = []
        self.constraints = []
        for m in self.models:
            self.params += m.params
            self.regularizers += m.regularizers
            self.constraints += m.constraints

    def get_params(self):
        return self.params, self.regularizers, self.constraints

    def get_output(self, train=False):
        if self.mode == 'sum':
            s = self.models[0].get_output(train)
            for i in range(1, len(self.models)):
                s += self.models[i].get_output(train)
            return s
        elif self.mode == 'concat':
            inputs = [self.models[i].get_output(train) for i in range(len(self.models))]
            return T.concatenate(inputs, axis=-1)
        else:
            raise Exception('Unknown merge mode')

    def get_input(self, train=False):
        res = []
        for i in range(len(self.models)):
            o = self.models[i].get_input(train)
            if type(o) == list:
                res += o
            else:
                res.append(o)
        return res

    @property
    def input(self):
        return self.get_input()

    def get_weights(self):
        weights = []
        for m in self.models:
            weights += m.get_weights()
        return weights

    def set_weights(self, weights):
        for i in range(len(self.models)):
            nb_param = len(self.models[i].params)
            self.models[i].set_weights(weights[:nb_param])
            weights = weights[nb_param:]

    def get_config(self):
        return {"name":self.__class__.__name__,
            "models":[m.get_config() for m in self.models],
            "mode":self.mode}


class Dropout(Layer):
    '''
        Hinton's dropout.
    '''
    def __init__(self, p):
        super(Dropout,self).__init__()
        self.p = p

    def get_output(self, train):
        X = self.get_input(train)
        if self.p > 0.:
            retain_prob = 1. - self.p
            if train:
                X *= srng.binomial(X.shape, p=retain_prob, dtype=theano.config.floatX)
            else:
                X *= retain_prob
        return X

    def get_config(self):
        return {"name":self.__class__.__name__,
            "p":self.p}


class Activation(Layer):
    '''
        Apply an activation function to an output.
    '''
    def __init__(self, activation, target=0, beta=0.1):
        super(Activation,self).__init__()
        self.activation = activations.get(activation)
        self.target = target
        self.beta = beta

    def get_output(self, train):
        X = self.get_input(train)
        return self.activation(X)

    def get_config(self):
        return {"name":self.__class__.__name__,
            "activation":self.activation.__name__,
            "target":self.target,
            "beta":self.beta}


class Reshape(Layer):
    '''
        Reshape an output to a certain shape.
        Can't be used as first layer in a model (no fixed input!)
        First dimension is assumed to be nb_samples.
    '''
    def __init__(self, *dims):
        super(Reshape,self).__init__()
        self.dims = dims

    def get_output(self, train):
        X = self.get_input(train)
        nshape = make_tuple(X.shape[0], *self.dims)
        return theano.tensor.reshape(X, nshape)

    def get_config(self):
        return {"name":self.__class__.__name__,
            "dims":self.dims}


class Flatten(Layer):
    '''
        Reshape input to flat shape.
        First dimension is assumed to be nb_samples.
    '''
    def __init__(self):
        super(Flatten,self).__init__()

    def get_output(self, train):
        X = self.get_input(train)
        size = theano.tensor.prod(X.shape) // X.shape[0]
        nshape = (X.shape[0], size)
        return theano.tensor.reshape(X, nshape)


class RepeatVector(Layer):
    '''
        Repeat input n times.

        Dimensions of input are assumed to be (nb_samples, dim).
        Return tensor of shape (nb_samples, n, dim).
    '''
    def __init__(self, n):
        super(RepeatVector,self).__init__()
        self.n = n

    def get_output(self, train):
        X = self.get_input(train)
        tensors = [X]*self.n
        stacked = theano.tensor.stack(*tensors)
        return stacked.dimshuffle((1,0,2))

    def get_config(self):
        return {"name":self.__class__.__name__,
            "n":self.n}


class Dense(Layer):
    '''
        Just your regular fully connected NN layer.
    '''
    def __init__(self, input_dim, output_dim, init='glorot_uniform', activation='linear', weights=None, 
        W_regularizer=None, b_regularizer=None, W_constraint=None, b_constraint=None):

        super(Dense,self).__init__()
        self.init = initializations.get(init)
        self.activation = activations.get(activation)
        self.input_dim = input_dim
        self.output_dim = output_dim

        self.input = T.matrix()
        self.W = self.init((self.input_dim, self.output_dim))
        self.b = shared_zeros((self.output_dim))

        self.params = [self.W, self.b]

        self.regularizers = [W_regularizer, b_regularizer]
        self.constraints = [W_constraint, b_constraint]

        if weights is not None:
            self.set_weights(weights)

    def get_output(self, train):
        X = self.get_input(train)
        output = self.activation(T.dot(X, self.W) + self.b)
        return output

    def get_config(self):
        return {"name":self.__class__.__name__,
            "input_dim":self.input_dim,
            "output_dim":self.output_dim,
            "init":self.init.__name__,
            "activation":self.activation.__name__}


class TimeDistributedDense(Layer):
    '''
       Apply a same DenseLayer for each dimension[1] (shared_dimension) input
       Especially useful after a recurrent network with 'return_sequence=True'
       Tensor input dimensions:   (nb_sample, shared_dimension, input_dim)
       Tensor output dimensions:  (nb_sample, shared_dimension, output_dim)

    '''
    def __init__(self, input_dim, output_dim, init='glorot_uniform', activation='linear', weights=None, 
        W_regularizer=None, b_regularizer=None, W_constraint=None, b_constraint=None):

        super(TimeDistributedDense,self).__init__()
        self.init = initializations.get(init)
        self.activation = activations.get(activation)
        self.input_dim = input_dim
        self.output_dim = output_dim

        self.input = T.tensor3()
        self.W = self.init((self.input_dim, self.output_dim))
        self.b = shared_zeros((self.output_dim))

        self.params = [self.W, self.b]

        self.regularizers = [W_regularizer, b_regularizer]
        self.constraints = [W_constraint, b_constraint]

        if weights is not None:
            self.set_weights(weights)

    def get_output(self, train):
        X = self.get_input(train)

        def act_func(X):
            return self.activation(T.dot(X, self.W) + self.b)

        output, _ = theano.scan(fn = act_func,
                                sequences = X.dimshuffle(1,0,2),
                                outputs_info=None)
        return output.dimshuffle(1,0,2)

    def get_config(self):
        return {"name":self.__class__.__name__,
            "input_dim":self.input_dim,
            "output_dim":self.output_dim,
            "init":self.init.__name__,
            "activation":self.activation.__name__}

class AutoEncoder(Layer):
    '''
        A customizable autoencoder model.
        If output_reconstruction then dim(input) = dim(output)
        else dim(output) = dim(hidden)
    '''
    def __init__(self, encoder, decoder, output_reconstruction=True, tie_weights=False, weights=None):

        super(AutoEncoder,self).__init__()

        self.output_reconstruction = output_reconstruction
        self.tie_weights = tie_weights
        self.encoder = encoder
        self.decoder = decoder

        self.decoder.connect(self.encoder)

        self.params = []
        self.regularizers = []
        self.constraints = []
        for layer in [self.encoder, self.decoder]:
            self.params += layer.params
            if hasattr(layer, 'regularizers'):
                self.regularizers += layer.regularizers
            if hasattr(layer, 'constraints'):
                self.constraints += layer.constraints

        if weights is not None:
            self.set_weights(weights)

    def connect(self, node):
        self.encoder.previous = node

    def get_weights(self):
        weights = []
        for layer in [self.encoder, self.decoder]:
            weights += layer.get_weights()
        return weights

    def set_weights(self, weights):
        nb_param = len(self.encoder.params)
        self.encoder.set_weights(weights[:nb_param])
        self.decoder.set_weights(weights[nb_param:])

    def get_input(self, train=False):
        return self.encoder.get_input(train)

    @property
    def input(self):
        return self.encoder.input

    def _get_hidden(self, train):
        return self.encoder.get_output(train)

    def get_output(self, train):
        if not train and not self.output_reconstruction:
            return self.encoder.get_output(train)

        decoded = self.decoder.get_output(train)

        if self.tie_weights:
            encoder_params = self.encoder.get_weights()
            decoder_params = self.decoder.get_weights()
            for dec_param, enc_param in zip(decoder_params, encoder_params):
                if len(dec_param.shape) > 1:
                    enc_param = dec_param.T

        return decoded

    def get_config(self):
        return {"name":self.__class__.__name__,
                "encoder_config":self.encoder.get_config(),
                "decoder_config":self.decoder.get_config(),
                "output_reconstruction":self.output_reconstruction,
                "tie_weights":self.tie_weights}


class DenoisingAutoEncoder(AutoEncoder):
    '''
        A denoising autoencoder model that inherits the base features from autoencoder
    '''
    def __init__(self, encoder=None, decoder=None, output_reconstruction=True, tie_weights=False, weights=None, corruption_level=0.3):
        super(DenoisingAutoEncoder, self).__init__(encoder, decoder, output_reconstruction, tie_weights, weights)
        self.corruption_level = corruption_level

    def _get_corrupted_input(self, input):
        """
            http://deeplearning.net/tutorial/dA.html
        """
        return srng.binomial(size=(self.input_dim, 1), n=1,
                             p=1-self.corruption_level,
                             dtype=theano.config.floatX) * input

    def get_input(self, train=False):
        uncorrupted_input = super(DenoisingAutoEncoder, self).get_input(train)
        return self._get_corrupted_input(uncorrupted_input)

    def get_config(self):
        return {"name":self.__class__.__name__,
                "encoder_config":self.encoder.get_config(),
                "decoder_config":self.decoder.get_config(),
                "corruption_level":self.corruption_level,
                "output_reconstruction":self.output_reconstruction,
                "tie_weights":self.tie_weights}


class MaxoutDense(Layer):
    '''
        Max-out layer, nb_feature is the number of pieces in the piecewise linear approx.
        Refer to http://arxiv.org/pdf/1302.4389.pdf
    '''
    def __init__(self, input_dim, output_dim, nb_feature=4, init='glorot_uniform', weights=None, 
        W_regularizer=None, b_regularizer=None, W_constraint=None, b_constraint=None):

        super(MaxoutDense,self).__init__()
        self.init = initializations.get(init)
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.nb_feature = nb_feature

        self.input = T.matrix()
        self.W = self.init((self.nb_feature, self.input_dim, self.output_dim))
        self.b = shared_zeros((self.nb_feature, self.output_dim))

        self.params = [self.W, self.b]

        self.regularizers = [W_regularizer, b_regularizer]
        self.constraints = [W_constraint, b_constraint]

        if weights is not None:
            self.set_weights(weights)

    def get_output(self, train):
        X = self.get_input(train)
        # -- don't need activation since it's just linear.
        output = T.max(T.dot(X, self.W) + self.b, axis=1)
        return output

    def get_config(self):
        return {"name":self.__class__.__name__,
            "input_dim":self.input_dim,
            "output_dim":self.output_dim,
            "init":self.init.__name__,
            "nb_feature" : self.nb_feature}

from __future__ import absolute_import
import theano
import theano.tensor as T

from .. import activations, initializations
from ..layers.core import Layer
from ..constraints import unitnorm


class Embedding(Layer):
    '''
        Turn positive integers (indexes) into denses vectors of fixed size. 
        eg. [[4], [20]] -> [[0.25, 0.1], [0.6, -0.2]]

        @input_dim: size of vocabulary (highest input integer + 1)
        @out_dim: size of dense representation
    '''
    def __init__(self, input_dim, output_dim, init='uniform', weights=None, W_regularizer=None, W_constraint=None):
        super(Embedding,self).__init__()
        self.init = initializations.get(init)
        self.input_dim = input_dim
        self.output_dim = output_dim

        self.input = T.imatrix()
        self.W = self.init((self.input_dim, self.output_dim))
        self.params = [self.W]
        self.constraints = [W_constraint]
        self.regularizers = [W_regularizer]

        if weights is not None:
            self.set_weights(weights)

    def get_output(self, train=False):
        X = self.get_input(train)
        out = self.W[X]
        return out

    def get_config(self):
        return {"name":self.__class__.__name__,
            "input_dim":self.input_dim,
            "output_dim":self.output_dim,
            "init":self.init.__name__}


class WordContextProduct(Layer):
    '''
        This layer turns a pair of words (a pivot word + a context word, 
        ie. a word from the same context, or a random, out-of-context word),
        indentified by their index in a vocabulary, into two dense reprensentations
        (word representation and context representation).

        Then it returns activation(dot(pivot_embedding, context_embedding)),
        which can be trained to encode the probability 
        of finding the context word in the context of the pivot word
        (or reciprocally depending on your training procedure).

        The layer ingests integer tensors of shape:
        (nb_samples, 2)
        and outputs a float tensor of shape
        (nb_samples, 1)

        The 2nd dimension encodes (pivot, context).
        input_dim is the size of the vocabulary.

        For more context, see Mikolov et al.:
            Efficient Estimation of Word reprensentations in Vector Space
            http://arxiv.org/pdf/1301.3781v3.pdf
    '''
    def __init__(self, input_dim, proj_dim=128, 
        init='uniform', activation='sigmoid', weights=None):
        super(WordContextProduct,self).__init__()
        self.input_dim = input_dim
        self.proj_dim = proj_dim
        self.init = initializations.get(init)
        self.activation = activations.get(activation)

        self.input = T.imatrix()
        # two different embeddings for pivot word and its context
        # because p(w|c) != p(c|w)
        self.W_w = self.init((input_dim, proj_dim))
        self.W_c = self.init((input_dim, proj_dim))

        self.params = [self.W_w, self.W_c]

        if weights is not None:
            self.set_weights(weights)


    def get_output(self, train=False):
        X = self.get_input(train)
        w = self.W_w[X[:, 0]] # nb_samples, proj_dim
        c = self.W_c[X[:, 1]] # nb_samples, proj_dim

        dot = T.sum(w * c, axis=1)
        dot = theano.tensor.reshape(dot, (X.shape[0], 1))
        return self.activation(dot)

    def get_config(self):
        return {"name":self.__class__.__name__,
            "input_dim":self.input_dim,
            "proj_dim":self.proj_dim,
            "init":self.init.__name__,
            "activation":self.activation.__name__}


from ..layers.core import Layer
from ..utils.theano_utils import shared_zeros

class LeakyReLU(Layer):
    def __init__(self, alpha=0.3):
        super(LeakyReLU,self).__init__()
        self.alpha = alpha

    def get_output(self, train):
        X = self.get_input(train)
        return ((X + abs(X)) / 2.0) + self.alpha * ((X - abs(X)) / 2.0)

    def get_config(self):
        return {"name":self.__class__.__name__,
            "alpha":self.alpha}


class PReLU(Layer):
    '''
        Reference: 
            Delving Deep into Rectifiers: Surpassing Human-Level Performance on ImageNet Classification
                http://arxiv.org/pdf/1502.01852v1.pdf
    '''
    def __init__(self, input_shape):
        super(PReLU,self).__init__()
        self.alphas = shared_zeros(input_shape)
        self.params = [self.alphas]
        self.input_shape = input_shape

    def get_output(self, train):
        X = self.get_input(train)
        pos = ((X + abs(X)) / 2.0)
        neg = self.alphas * ((X - abs(X)) / 2.0)
        return pos + neg

    def get_config(self):
        return {"name":self.__class__.__name__,
        "input_shape":self.input_shape}

from ..layers.core import Layer
from ..utils.theano_utils import shared_zeros
from .. import initializations

import theano.tensor as T

class BatchNormalization(Layer):
    '''
        Reference: 
            Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift
                http://arxiv.org/pdf/1502.03167v3.pdf

            mode: 0 -> featurewise normalization
                  1 -> samplewise normalization (may sometimes outperform featurewise mode)

            momentum: momentum term in the computation of a running estimate of the mean and std of the data
    '''
    def __init__(self, input_shape, epsilon=1e-6, mode=0, momentum=0.9, weights=None):
        super(BatchNormalization,self).__init__()
        self.init = initializations.get("uniform")
        self.input_shape = input_shape
        self.epsilon = epsilon
        self.mode = mode
        self.momentum = momentum

        self.gamma = self.init((self.input_shape))
        self.beta = shared_zeros(self.input_shape)

        self.running_mean = None
        self.running_std = None

        self.params = [self.gamma, self.beta]
        if weights is not None:
            self.set_weights(weights)

    def get_output(self, train):
        X = self.get_input(train)

        if self.mode == 0:
            if train:
                m = X.mean(axis=0)
                # manual computation of std to prevent NaNs
                std = T.mean((X-m)**2 + self.epsilon, axis=0) ** 0.5
                X_normed = (X - m) / (std + self.epsilon)

                if self.running_mean is None:
                    self.running_mean = m
                    self.running_std = std
                else:
                    self.running_mean *= self.momentum
                    self.running_mean += (1-self.momentum) * m
                    self.running_std *= self.momentum
                    self.running_std += (1-self.momentum) * std
            else:
                X_normed = (X - self.running_mean) / (self.running_std + self.epsilon)

        elif self.mode == 1:
            m = X.mean(axis=-1, keepdims=True)
            std = X.std(axis=-1, keepdims=True)
            X_normed = (X - m) / (std + self.epsilon)

        out = self.gamma * X_normed + self.beta
        return out

    def get_config(self):
        return {"name":self.__class__.__name__,
            "input_shape":self.input_shape,
            "epsilon":self.epsilon,
            "mode":self.mode}

from __future__ import absolute_import
from .cifar import load_batch
from .data_utils import get_file
import numpy as np
import os

def load_data(label_mode='fine'):
    if label_mode not in ['fine', 'coarse']:
        raise Exception('label_mode must be one of "fine" "coarse".')

    dirname = "cifar-100-python"
    origin = "http://www.cs.toronto.edu/~kriz/cifar-100-python.tar.gz"
    path = get_file(dirname, origin=origin, untar=True)

    nb_test_samples = 10000
    nb_train_samples = 50000

    fpath = os.path.join(path, 'train')
    X_train, y_train = load_batch(fpath, label_key=label_mode+'_labels')

    fpath = os.path.join(path, 'test')
    X_test, y_test = load_batch(fpath, label_key=label_mode+'_labels')

    y_train = np.reshape(y_train, (len(y_train), 1))
    y_test = np.reshape(y_test, (len(y_test), 1))

    return (X_train, y_train), (X_test, y_test) 

from __future__ import absolute_import
import six.moves.cPickle
import gzip
from .data_utils import get_file
import random
from six.moves import zip

def load_data(path="imdb.pkl", nb_words=None, skip_top=0, maxlen=None, test_split=0.2, seed=113):
    path = get_file(path, origin="https://s3.amazonaws.com/text-datasets/imdb.pkl")

    if path.endswith(".gz"):
        f = gzip.open(path, 'rb')
    else:
        f = open(path, 'rb')

    X, labels = six.moves.cPickle.load(f)
    f.close()

    random.seed(seed)
    random.shuffle(X)
    random.seed(seed)
    random.shuffle(labels)

    if maxlen:
        new_X = []
        new_labels = []
        for x, y in zip(X, labels):
            if len(x) < maxlen:
                new_X.append(x)
                new_labels.append(y)
        X = new_X
        labels = new_labels

    if not nb_words:
        nb_words = max([max(x) for x in X])

    X = [[0 if (w >= nb_words or w < skip_top) else w for w in x] for x in X]
    X_train = X[:int(len(X)*(1-test_split))]
    y_train = labels[:int(len(X)*(1-test_split))]

    X_test = X[int(len(X)*(1-test_split)):]
    y_test = labels[int(len(X)*(1-test_split)):]

    return (X_train, y_train), (X_test, y_test)


from __future__ import absolute_import
from __future__ import print_function
import tarfile, inspect, os
from six.moves.urllib.request import urlretrieve
from ..utils.generic_utils import Progbar

def get_file(fname, origin, untar=False):
    datadir = os.path.expanduser(os.path.join('~', '.keras', 'datasets'))
    if not os.path.exists(datadir):
        os.makedirs(datadir)

    if untar:
        untar_fpath = os.path.join(datadir, fname)
        fpath = untar_fpath + '.tar.gz'
    else:
        fpath = os.path.join(datadir, fname)

    try:
        f = open(fpath)
    except:
        print('Downloading data from',  origin)

        global progbar
        progbar = None
        def dl_progress(count, block_size, total_size):
            global progbar
            if progbar is None:
                progbar = Progbar(total_size)
            else:
                progbar.update(count*block_size)

        urlretrieve(origin, fpath, dl_progress)
        progbar = None

    if untar:
        if not os.path.exists(untar_fpath):
            print('Untaring file...')
            tfile = tarfile.open(fpath, 'r:gz')
            tfile.extractall(path=datadir)
            tfile.close()
        return untar_fpath

    return fpath


# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from .data_utils import get_file
import string
import random
import os
import six.moves.cPickle
from six.moves import zip

def make_reuters_dataset(path=os.path.join('datasets', 'temp', 'reuters21578'), min_samples_per_topic=15):
    import re
    from ..preprocessing.text import Tokenizer

    wire_topics = []
    topic_counts = {}
    wire_bodies = []

    for fname in os.listdir(path):
        if 'sgm' in fname:
            s = open(path + fname).read()
            tag = '<TOPICS>'
            while tag in s:
                s = s[s.find(tag)+len(tag):]
                topics = s[:s.find('</')]
                
                if topics and not '</D><D>' in topics:
                    topic = topics.replace('<D>', '').replace('</D>', '')
                    wire_topics.append(topic)
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
                else:
                    continue

                bodytag = '<BODY>'
                body = s[s.find(bodytag)+len(bodytag):]
                body = body[:body.find('</')]
                wire_bodies.append(body)

    # only keep most common topics
    items = list(topic_counts.items())
    items.sort(key = lambda x: x[1])
    kept_topics = set()
    for x in items:
        print(x[0] + ': ' + str(x[1]))
        if x[1] >= min_samples_per_topic:
            kept_topics.add(x[0])
    print('-')
    print('Kept topics:', len(kept_topics))

    # filter wires with rare topics
    kept_wires = []
    labels = []
    topic_indexes = {}
    for t, b in zip(wire_topics, wire_bodies):
        if t in kept_topics:
            if t not in topic_indexes:
                topic_index = len(topic_indexes)
                topic_indexes[t] = topic_index
            else:
                topic_index = topic_indexes[t]

            labels.append(topic_index)
            kept_wires.append(b)

    # vectorize wires
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(kept_wires)
    X = tokenizer.texts_to_sequences(kept_wires)

    print('Sanity check:')
    for w in ["banana", "oil", "chocolate", "the", "dsft"]:
        print('...index of', w, ':', tokenizer.word_index.get(w))

    dataset = (X, labels) 
    print('-')
    print('Saving...')
    six.moves.cPickle.dump(dataset, open(os.path.join('datasets', 'data', 'reuters.pkl'), 'w'))
    six.moves.cPickle.dump(tokenizer.word_index, open(os.path.join('datasets','data', 'reuters_word_index.pkl'), 'w'))



def load_data(path="reuters.pkl", nb_words=None, skip_top=0, maxlen=None, test_split=0.2, seed=113):
    path = get_file(path, origin="https://s3.amazonaws.com/text-datasets/reuters.pkl")
    f = open(path, 'rb')

    X, labels = six.moves.cPickle.load(f)
    f.close()
    random.seed(seed)
    random.shuffle(X)
    random.seed(seed)
    random.shuffle(labels)

    if maxlen:
        new_X = []
        new_labels = []
        for x, y in zip(X, labels):
            if len(x) < maxlen:
                new_X.append(x)
                new_labels.append(y)
        X = new_X
        labels = new_labels

    if not nb_words:
        nb_words = max([max(x) for x in X])

    X = [[0 if (w >= nb_words or w < skip_top) else w for w in x] for x in X]
    X_train = X[:int(len(X)*(1-test_split))]
    y_train = labels[:int(len(X)*(1-test_split))]

    X_test = X[int(len(X)*(1-test_split)):]
    y_test = labels[int(len(X)*(1-test_split)):]

    return (X_train, y_train), (X_test, y_test)


def get_word_index(path="reuters_word_index.pkl"):
    path = get_file(path, origin="https://s3.amazonaws.com/text-datasets/reuters_word_index.pkl")
    f = open(path, 'rb')
    return six.moves.cPickle.load(f)


if __name__ == "__main__":
    make_reuters_dataset()
    (X_train, y_train), (X_test, y_test) = load_data()

# -*- coding: utf-8 -*-
from __future__ import absolute_import
import sys
import six.moves.cPickle
from six.moves import range

def load_batch(fpath, label_key='labels'):
    f = open(fpath, 'rb')
    if sys.version_info < (3,):
        d = six.moves.cPickle.load(f)
    else:
        d = six.moves.cPickle.load(f, encoding="bytes")
        # decode utf8
        for k, v in d.items():
            del(d[k])
            d[k.decode("utf8")] = v
    f.close()
    data = d["data"]
    labels = d[label_key]

    data = data.reshape(data.shape[0], 3, 32, 32)
    return data, labels

from __future__ import absolute_import
from .cifar import load_batch
from .data_utils import get_file
import numpy as np
import os

def load_data():
    dirname = "cifar-10-batches-py"
    origin = "http://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
    path = get_file(dirname, origin=origin, untar=True)

    nb_test_samples = 10000
    nb_train_samples = 50000

    X_train = np.zeros((nb_train_samples, 3, 32, 32), dtype="uint8")
    y_train = np.zeros((nb_train_samples,), dtype="uint8")

    for i in range(1, 6):
        fpath = os.path.join(path, 'data_batch_' + str(i))
        data, labels = load_batch(fpath)
        X_train[(i-1)*10000:i*10000, :, :, :] = data
        y_train[(i-1)*10000:i*10000] = labels
    
    fpath = os.path.join(path, 'test_batch')
    X_test, y_test = load_batch(fpath)

    y_train = np.reshape(y_train, (len(y_train), 1))
    y_test = np.reshape(y_test, (len(y_test), 1))

    return (X_train, y_train), (X_test, y_test) 
# -*- coding: utf-8 -*-
import gzip
from .data_utils import get_file
import six.moves.cPickle
import sys

def load_data(path="mnist.pkl.gz"):
    path = get_file(path, origin="https://s3.amazonaws.com/img-datasets/mnist.pkl.gz")

    if path.endswith(".gz"):
        f = gzip.open(path, 'rb')
    else:
        f = open(path, 'rb')

    if sys.version_info < (3,):
        data = six.moves.cPickle.load(f)
    else:
        data = six.moves.cPickle.load(f, encoding="bytes")

    f.close()

    return data # (X_train, y_train), (X_test, y_test)

import pydot
from keras.layers.core import Merge
from keras.models import Model
from collections import Counter

class Grapher(object):

    def __init__(self):
        self.names = {}
        self.class_counts = Counter()

    def get_name(self, model):
        """
        returns the name of the model instance. If model does not have a `name` attribute, then it will be assigned
        a generic (and unique) identifier based on its class
        """
        if hasattr(model, 'name'):
            return model.name
        clz = model.__class__.__name__
        if model not in self.names:
            self.class_counts[clz] += 1
            self.names[model] = clz + str(self.class_counts[clz])
        return self.names[model]

    def add_edge(self, f, t, graph):
        if f: graph.add_edge(pydot.Edge(f, t))
        return t

    def add_model(self, model, graph, parent=None):
        """
        Recursively adds `model` and its components to the pydot graph
        """
        this = self.get_name(model)
        if isinstance(model, Model):
            parent = self.add_edge(parent, this, graph)
            for child in reversed(model.layers):
                parent = self.add_model(child, graph, parent)
        elif isinstance(model, Merge):
            for child in model.models:
                self.add_model(child, graph, this)
            return self.add_edge(parent, this, graph)
        else:
            return self.add_edge(parent, this, graph)

    def plot(self, model, to_file):
        """
        creates a graph visualizing the structure of `model` and writes it to `to_file`
        """
        graph = pydot.Dot(graph_type='graph')
        self.add_model(model, graph)
        graph.write_png(to_file)

from __future__ import absolute_import
import numpy as np
import time
import sys

def get_from_module(identifier, module_params, module_name, instantiate=False):
    if type(identifier) is str:
        res = module_params.get(identifier)
        if not res:
            raise Exception('Invalid ' + str(module_name) + ': ' + str(identifier))
        if instantiate:
            return res()
        else:
            return res
    return identifier

def make_tuple(*args):
    return args

def printv(v, prefix=''):
    if type(v) == dict:
        if 'name' in v:
            print(prefix + '#' + v['name'])
            del v['name']
        prefix += '...'
        for nk, nv in v.items():
            if type(nv) in [dict, list]:
                print(prefix + nk + ':')
                printv(nv, prefix)
            else:
                print(prefix + nk + ':' + str(nv))
    elif type(v) == list:
        prefix += '...'
        for i, nv in enumerate(v):
            print(prefix + '#' + str(i))
            printv(nv, prefix) 
    else:
        prefix += '...'
        print(prefix + str(v))

class Progbar(object):
    def __init__(self, target, width=30, verbose=1):
        '''
            @param target: total number of steps expected
        '''
        self.width = width
        self.target = target
        self.sum_values = {}
        self.unique_values = []
        self.start = time.time()
        self.total_width = 0
        self.seen_so_far = 0
        self.verbose = verbose

    def update(self, current, values=[]):
        '''
            @param current: index of current step
            @param values: list of tuples (name, value_for_last_step).
            The progress bar will display averages for these values.
        '''
        for k, v in values:
            if k not in self.sum_values:
                self.sum_values[k] = [v * (current-self.seen_so_far), current-self.seen_so_far]
                self.unique_values.append(k)
            else:
                self.sum_values[k][0] += v * (current-self.seen_so_far)
                self.sum_values[k][1] += (current-self.seen_so_far)
        self.seen_so_far = current

        now = time.time()
        if self.verbose == 1:
            prev_total_width = self.total_width
            sys.stdout.write("\b" * prev_total_width)
            sys.stdout.write("\r")

            numdigits = int(np.floor(np.log10(self.target))) + 1
            barstr = '%%%dd/%%%dd [' % (numdigits, numdigits)
            bar = barstr % (current, self.target)
            prog = float(current)/self.target
            prog_width = int(self.width*prog)
            if prog_width > 0:
                bar += ('='*(prog_width-1))
                if current < self.target:
                    bar += '>'
                else:
                    bar += '='
            bar += ('.'*(self.width-prog_width))
            bar += ']'
            sys.stdout.write(bar)
            self.total_width = len(bar)
            
            if current:
                time_per_unit = (now - self.start) / current
            else:
                time_per_unit = 0
            eta = time_per_unit*(self.target - current)
            info = ''
            if current < self.target:
                info += ' - ETA: %ds' % eta
            else:
                info += ' - %ds' % (now - self.start)
            for k in self.unique_values:
                info += ' - %s: %.4f' % (k, self.sum_values[k][0]/ max(1, self.sum_values[k][1]))

            self.total_width += len(info)
            if prev_total_width > self.total_width:
                info += ((prev_total_width-self.total_width) * " ")

            sys.stdout.write(info)
            sys.stdout.flush()

            if current >= self.target:
                sys.stdout.write("\n")

        if self.verbose == 2:
            if current >= self.target:
                info = '%ds' % (now - self.start)
                for k in self.unique_values:
                    info += ' - %s: %.4f' % (k, self.sum_values[k][0]/ max(1, self.sum_values[k][1]))
                sys.stdout.write(info + "\n")


    def add(self, n, values=[]):
        self.update(self.seen_so_far+n, values)

from __future__ import absolute_import
import numpy as np
import theano
import theano.tensor as T

def floatX(X):
    return np.asarray(X, dtype=theano.config.floatX)

def sharedX(X, dtype=theano.config.floatX, name=None):
    return theano.shared(np.asarray(X, dtype=dtype), name=name)

def shared_zeros(shape, dtype=theano.config.floatX, name=None):
    return sharedX(np.zeros(shape), dtype=dtype, name=name)

def shared_scalar(val=0., dtype=theano.config.floatX, name=None):
    return theano.shared(np.cast[dtype](val))

def shared_ones(shape, dtype=theano.config.floatX, name=None):
    return sharedX(np.ones(shape), dtype=dtype, name=name)

def alloc_zeros_matrix(*dims):
    return T.alloc(np.cast[theano.config.floatX](0.), *dims)


from __future__ import absolute_import
import h5py
import numpy as np
from collections import defaultdict

class HDF5Matrix:
    
    refs = defaultdict(int)

    def __init__(self, datapath, dataset, start, end, normalizer=None):
        if datapath not in list(self.refs.keys()):
            f = h5py.File(datapath)
            self.refs[datapath] = f
        else:
            f = self.refs[datapath]
        self.start = start
        self.end = end
        self.data = f[dataset]
        self.normalizer = normalizer
    
    def __len__(self):
        return self.end - self.start

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.stop + self.start <= self.end:
                idx = slice(key.start+self.start, key.stop + self.start)
            else:
                raise IndexError
        elif isinstance(key, int):
            if key + self.start < self.end:
                idx = key+self.start
            else:
                raise IndexError
        elif isinstance(key, np.ndarray):
            if np.max(key) + self.start < self.end:
                idx = (self.start + key).tolist()
            else:
                raise IndexError
        elif isinstance(key, list):
            if max(key) + self.start < self.end:
                idx = [x + self.start for x in key]
            else:
                raise IndexError
        if self.normalizer is not None:
            return self.normalizer(self.data[idx])
        else:
            return self.data[idx]

    @property
    def shape(self):
        return tuple([self.end - self.start, self.data.shape[1]])


def save_array(array, name):
    import tables
    f = tables.open_file(name, 'w')
    atom = tables.Atom.from_dtype(array.dtype)
    ds = f.createCArray(f.root, 'data', atom, array.shape)
    ds[:] = array
    f.close()

def load_array(name):
    import tables
    f = tables.open_file(name)
    array = f.root.data
    a=np.empty(shape=array.shape, dtype=array.dtype)
    a[:]=array[:]
    f.close()
    return a

from __future__ import absolute_import
import numpy as np
import scipy as sp
from six.moves import range
from six.moves import zip

def to_categorical(y, nb_classes=None):
    '''Convert class vector (integers from 0 to nb_classes)
    to binary class matrix, for use with categorical_crossentropy
    '''
    y = np.asarray(y, dtype='int32')
    if not nb_classes:
        nb_classes = np.max(y)+1
    Y = np.zeros((len(y), nb_classes))
    for i in range(len(y)):
        Y[i, y[i]] = 1.
    return Y

def normalize(a, axis=-1, order=2):
    l2 = np.atleast_1d(np.linalg.norm(a, order, axis))
    l2[l2==0] = 1
    return a / np.expand_dims(l2, axis)


def binary_logloss(p, y):
    epsilon = 1e-15
    p = sp.maximum(epsilon, p)
    p = sp.minimum(1-epsilon, p)
    res = sum(y*sp.log(p) + sp.subtract(1,y)*sp.log(sp.subtract(1,p)))
    res *= -1.0/len(y)
    return res

def multiclass_logloss(P, Y):
    score = 0.
    npreds = [P[i][Y[i]-1] for i in range(len(Y))]
    score = -(1./len(Y)) * np.sum(np.log(npreds))
    return score

def accuracy(p, y):
    return np.mean([a==b for a, b in zip(p, y)])

def probas_to_classes(y_pred):
    if len(y_pred.shape) > 1 and y_pred.shape[1] > 1:
        return categorical_probas_to_classes(y_pred)
    return np.array([1 if p > 0.5 else 0 for p in y_pred])

def categorical_probas_to_classes(p):
    return np.argmax(p, axis=1)

from __future__ import absolute_import
# -*- coding: utf-8 -*-
import numpy as np
import random
from six.moves import range

def pad_sequences(sequences, maxlen=None, dtype='int32'):
    """
        Pad each sequence to the same length: 
        the length of the longuest sequence.

        If maxlen is provided, any sequence longer
        than maxlen is truncated to maxlen.
    """
    lengths = [len(s) for s in sequences]

    nb_samples = len(sequences)
    if maxlen is None:
        maxlen = np.max(lengths)

    x = np.zeros((nb_samples, maxlen)).astype(dtype)
    for idx, s in enumerate(sequences):
        x[idx, :lengths[idx]] = s[:maxlen]
    return x


def make_sampling_table(size, sampling_factor=1e-5):
    '''
        This generates an array where the ith element
        is the probability that a word of rank i would be sampled,
        according to the sampling distribution used in word2vec.
        
        The word2vec formula is:
            p(word) = min(1, sqrt(word.frequency/sampling_factor) / (word.frequency/sampling_factor))

        We assume that the word frequencies follow Zipf's law (s=1) to derive 
        a numerical approximation of frequency(rank):
           frequency(rank) ~ 1/(rank * (log(rank) + gamma) + 1/2 - 1/(12*rank))
        where gamma is the Euler-Mascheroni constant.
    '''
    gamma = 0.577
    rank = np.array(list(range(size)))
    rank[0] = 1
    inv_fq = rank * (np.log(rank) + gamma) + 0.5 - 1./(12.*rank)
    f = sampling_factor * inv_fq
    return np.minimum(1., f / np.sqrt(f))


def skipgrams(sequence, vocabulary_size, 
    window_size=4, negative_samples=1., shuffle=True, 
    categorical=False, sampling_table=None):
    ''' 
        Take a sequence (list of indexes of words), 
        returns couples of [word_index, other_word index] and labels (1s or 0s),
        where label = 1 if 'other_word' belongs to the context of 'word',
        and label=0 if 'other_word' is ramdomly sampled

        @param vocabulary_size: int. maximum possible word index + 1
        @param window_size: int. actually half-window. The window of a word wi will be [i-window_size, i+window_size+1]
        @param negative_samples: float >= 0. 0 for no negative (=random) samples. 1 for same number as positive samples. etc.
        @param categorical: bool. if False, labels will be integers (eg. [0, 1, 1 .. ]), 
            if True labels will be categorical eg. [[1,0],[0,1],[0,1] .. ]

        Note: by convention, index 0 in the vocabulary is a non-word and will be skipped.
    '''
    couples = []
    labels = []
    for i, wi in enumerate(sequence):
        if not wi:
            continue
        if sampling_table is not None:
            if sampling_table[wi] < random.random():
                continue

        window_start = max(0, i-window_size)
        window_end = min(len(sequence), i+window_size+1)
        for j in range(window_start, window_end):
            if j != i:
                wj = sequence[j]
                if not wj:
                    continue
                couples.append([wi, wj])
                if categorical:
                    labels.append([0,1])
                else:
                    labels.append(1)

    if negative_samples > 0:
        nb_negative_samples = int(len(labels) * negative_samples)
        words = [c[0] for c in couples]
        random.shuffle(words)

        couples += [[words[i%len(words)], random.randint(1, vocabulary_size-1)] for i in range(nb_negative_samples)]
        if categorical:
            labels += [[1,0]]*nb_negative_samples
        else:
            labels += [0]*nb_negative_samples

    if shuffle:
        seed = random.randint(0,10e6)
        random.seed(seed)
        random.shuffle(couples)
        random.seed(seed)
        random.shuffle(labels)

    return couples, labels


# -*- coding: utf-8 -*-
'''
    These preprocessing utils would greatly benefit
    from a fast Cython rewrite.
'''
from __future__ import absolute_import

import string, sys
import numpy as np
from six.moves import range
from six.moves import zip

if sys.version_info < (3,):
    maketrans = string.maketrans
else:
    maketrans = str.maketrans

def base_filter():
    f = string.punctuation
    f = f.replace("'", '')
    f += '\t\n'
    return f

def text_to_word_sequence(text, filters=base_filter(), lower=True, split=" "):
    '''prune: sequence of characters to filter out
    '''
    if lower:
        text = text.lower()
    text = text.translate(maketrans(filters, split*len(filters)))
    seq = text.split(split)
    return [_f for _f in seq if _f]


def one_hot(text, n, filters=base_filter(), lower=True, split=" "):
    seq = text_to_word_sequence(text)
    return [(abs(hash(w))%(n-1)+1) for w in seq]


class Tokenizer(object):
    def __init__(self, nb_words=None, filters=base_filter(), lower=True, split=" "):
        self.word_counts = {}
        self.word_docs = {}
        self.filters = filters
        self.split = split
        self.lower = lower
        self.nb_words = nb_words
        self.document_count = 0

    def fit_on_texts(self, texts):
        '''
            required before using texts_to_sequences or texts_to_matrix
            @param texts: can be a list or a generator (for memory-efficiency)
        '''
        self.document_count = 0
        for text in texts:
            self.document_count += 1
            seq = text_to_word_sequence(text, self.filters, self.lower, self.split)
            for w in seq:
                if w in self.word_counts:
                    self.word_counts[w] += 1
                else:
                    self.word_counts[w] = 1
            for w in set(seq):
                if w in self.word_docs:
                    self.word_docs[w] += 1
                else:
                    self.word_docs[w] = 1

        wcounts = list(self.word_counts.items())
        wcounts.sort(key = lambda x: x[1], reverse=True)
        sorted_voc = [wc[0] for wc in wcounts]
        self.word_index = dict(list(zip(sorted_voc, list(range(1, len(sorted_voc)+1)))))

        self.index_docs = {}
        for w, c in list(self.word_docs.items()):
            self.index_docs[self.word_index[w]] = c


    def fit_on_sequences(self, sequences):
        '''
            required before using sequences_to_matrix 
            (if fit_on_texts was never called)
        '''
        self.document_count = len(sequences)
        self.index_docs = {}
        for seq in sequences:
            seq = set(seq)
            for i in seq:
                if i not in self.index_docs:
                    self.index_docs[i] = 1
                else:
                    self.index_docs[i] += 1


    def texts_to_sequences(self, texts):
        '''
            Transform each text in texts in a sequence of integers.
            Only top "nb_words" most frequent words will be taken into account.
            Only words known by the tokenizer will be taken into account.

            Returns a list of sequences.
        '''
        res = []
        for vect in self.texts_to_sequences_generator(texts):
            res.append(vect)
        return res

    def texts_to_sequences_generator(self, texts):
        '''
            Transform each text in texts in a sequence of integers.
            Only top "nb_words" most frequent words will be taken into account.
            Only words known by the tokenizer will be taken into account.

            Yields individual sequences.
        '''
        nb_words = self.nb_words
        for text in texts:
            seq = text_to_word_sequence(text, self.filters, self.lower, self.split)
            vect = []
            for w in seq:
                i = self.word_index.get(w)
                if i is not None:
                    if nb_words and i >= nb_words:
                        pass
                    else:
                        vect.append(i)
            yield vect


    def texts_to_matrix(self, texts, mode="binary"):
        '''
            modes: binary, count, tfidf, freq
        '''
        sequences = self.texts_to_sequences(texts)
        return self.sequences_to_matrix(sequences, mode=mode)

    def sequences_to_matrix(self, sequences, mode="binary"):
        '''
            modes: binary, count, tfidf, freq
        '''
        if not self.nb_words:
            if self.word_index:
                nb_words = len(self.word_index)
            else:
                raise Exception("Specify a dimension (nb_words argument), or fit on some text data first")
        else:
            nb_words = self.nb_words

        if mode == "tfidf" and not self.document_count:
            raise Exception("Fit the Tokenizer on some data before using tfidf mode")

        X = np.zeros((len(sequences), nb_words))
        for i, seq in enumerate(sequences):
            if not seq:
                pass
            counts = {}
            for j in seq:
                if j >= nb_words:
                    pass
                if j not in counts:
                    counts[j] = 1.
                else:
                    counts[j] += 1
            for j, c in list(counts.items()):
                if mode == "count":
                    X[i][j] = c
                elif mode == "freq":
                    X[i][j] = c/len(seq)
                elif mode == "binary":
                    X[i][j] = 1
                elif mode == "tfidf":
                    tf = np.log(c/len(seq))
                    df = (1 + np.log(1 + self.index_docs.get(j, 0)/(1 + self.document_count)))
                    X[i][j] = tf / df
                else:
                    raise Exception("Unknown vectorization mode: " + str(mode))
        return X



                



    

from __future__ import absolute_import

import numpy as np
from scipy import ndimage
from scipy import linalg

from os import listdir
from os.path import isfile, join
import random, math
from six.moves import range

'''
    Fairly basic set of tools for realtime data augmentation on image data.
    Can easily be extended to include new transforms, new preprocessing methods, etc...
'''

def random_rotation(x, rg, fill_mode="nearest", cval=0.):
    angle = random.uniform(-rg, rg)
    x = ndimage.interpolation.rotate(x, angle, axes=(1,2), reshape=False, mode=fill_mode, cval=cval)
    return x

def random_shift(x, wrg, hrg, fill_mode="nearest", cval=0.):
    crop_left_pixels = 0
    crop_right_pixels = 0
    crop_top_pixels = 0
    crop_bottom_pixels = 0

    original_w = x.shape[1]
    original_h = x.shape[2]

    if wrg:
        crop = random.uniform(0., wrg)
        split = random.uniform(0, 1)
        crop_left_pixels = int(split*crop*x.shape[1])
        crop_right_pixels = int((1-split)*crop*x.shape[1])

    if hrg:
        crop = random.uniform(0., hrg)
        split = random.uniform(0, 1)
        crop_top_pixels = int(split*crop*x.shape[2])
        crop_bottom_pixels = int((1-split)*crop*x.shape[2])

    x = ndimage.interpolation.shift(x, (0, crop_left_pixels, crop_top_pixels), mode=fill_mode, cval=cval)
    return x

def horizontal_flip(x):
    for i in range(x.shape[0]):
        x[i] = np.fliplr(x[i])
    return x

def vertical_flip(x):
    for i in range(x.shape[0]):
        x[i] = np.flipud(x[i])
    return x


def random_barrel_transform(x, intensity):
    # TODO
    pass

def random_shear(x, intensity):
    # TODO
    pass

def random_channel_shift(x, rg):
    # TODO
    pass

def random_zoom(x, rg, fill_mode="nearest", cval=0.):
    zoom_w = random.uniform(1.-rg, 1.)
    zoom_h = random.uniform(1.-rg, 1.)
    x = ndimage.interpolation.zoom(x, zoom=(1., zoom_w, zoom_h), mode=fill_mode, cval=cval)
    return x # shape of result will be different from shape of input!




def array_to_img(x, scale=True):
    from PIL import Image
    x = x.transpose(1, 2, 0) 
    if scale:
        x += max(-np.min(x), 0)
        x /= np.max(x)
        x *= 255
    if x.shape[2] == 3:
        # RGB
        return Image.fromarray(x.astype("uint8"), "RGB")
    else:
        # grayscale
        return Image.fromarray(x[:,:,0].astype("uint8"), "L")


def img_to_array(img):
    x = np.asarray(img, dtype='float32')
    if len(x.shape)==3:
        # RGB: height, width, channel -> channel, height, width
        x = x.transpose(2, 0, 1)
    else:
        # grayscale: height, width -> channel, height, width
        x = x.reshape((1, x.shape[0], x.shape[1]))
    return x


def load_img(path, grayscale=False):
    from PIL import Image
    img = Image.open(open(path))
    if grayscale:
        img = img.convert('L')
    else: # Assure 3 channel even when loaded image is grayscale
        img = img.convert('RGB')
    return img


def list_pictures(directory, ext='jpg|jpeg|bmp|png'):
    return [join(directory,f) for f in listdir(directory) \
        if isfile(join(directory,f)) and re.match('([\w]+\.(?:' + ext + '))', f)]



class ImageDataGenerator(object):
    '''
        Generate minibatches with 
        realtime data augmentation.
    '''
    def __init__(self, 
            featurewise_center=True, # set input mean to 0 over the dataset
            samplewise_center=False, # set each sample mean to 0
            featurewise_std_normalization=True, # divide inputs by std of the dataset
            samplewise_std_normalization=False, # divide each input by its std

            zca_whitening=False, # apply ZCA whitening
            rotation_range=0., # degrees (0 to 180)
            width_shift_range=0., # fraction of total width
            height_shift_range=0., # fraction of total height
            horizontal_flip=False,
            vertical_flip=False,
        ):
        self.__dict__.update(locals())
        self.mean = None
        self.std = None
        self.principal_components = None


    def flow(self, X, y, batch_size=32, shuffle=False, seed=None, save_to_dir=None, save_prefix="", save_format="jpeg"):
        if seed:
            random.seed(seed)

        if shuffle:
            seed = random.randint(1, 10e6)
            np.random.seed(seed)
            np.random.shuffle(X)
            np.random.seed(seed)
            np.random.shuffle(y)

        nb_batch = int(math.ceil(float(X.shape[0])/batch_size))
        for b in range(nb_batch):
            batch_end = (b+1)*batch_size
            if batch_end > X.shape[0]:
                nb_samples = X.shape[0] - b*batch_size
            else:
                nb_samples = batch_size

            bX = np.zeros(tuple([nb_samples]+list(X.shape)[1:]))
            for i in range(nb_samples):
                x = X[b*batch_size+i]
                x = self.random_transform(x.astype("float32"))
                x = self.standardize(x)
                bX[i] = x

            if save_to_dir:
                for i in range(nb_samples):
                    img = array_to_img(bX[i], scale=True)
                    img.save(save_to_dir + "/" + save_prefix + "_" + str(i) + "." + save_format)

            yield bX, y[b*batch_size:b*batch_size+nb_samples]


    def standardize(self, x):
        if self.featurewise_center:
            x -= self.mean
        if self.featurewise_std_normalization:
            x /= self.std

        if self.zca_whitening:
            flatx = np.reshape(x, (x.shape[0]*x.shape[1]*x.shape[2]))
            whitex = np.dot(flatx, self.principal_components)
            x = np.reshape(whitex, (x.shape[0], x.shape[1], x.shape[2]))

        if self.samplewise_center:
            x -= np.mean(x)
        if self.samplewise_std_normalization:
            x /= np.std(x)

        return x


    def random_transform(self, x):
        if self.rotation_range:
            x = random_rotation(x, self.rotation_range)
        if self.width_shift_range or self.height_shift_range:
            x = random_shift(x, self.width_shift_range, self.height_shift_range)
        if self.horizontal_flip:
            if random.random() < 0.5:
                x = horizontal_flip(x)
        if self.vertical_flip:
            if random.random() < 0.5:
                x = vertical_flip(x)

        # TODO:
        # zoom
        # barrel/fisheye
        # shearing
        # channel shifting
        return x


    def fit(self, X, 
            augment=False, # fit on randomly augmented samples
            rounds=1, # if augment, how many augmentation passes over the data do we use
            seed=None
        ):
        '''
            Required for featurewise_center, featurewise_std_normalization and zca_whitening.
        '''
        X = np.copy(X)
        
        if augment:
            aX = np.zeros(tuple([rounds*X.shape[0]]+list(X.shape)[1:]))
            for r in range(rounds):
                for i in range(X.shape[0]):
                    img = array_to_img(X[i])
                    img = self.random_transform(img)
                    aX[i+r*X.shape[0]] = img_to_array(img)
            X = aX

        if self.featurewise_center:
            self.mean = np.mean(X, axis=0)
            X -= self.mean
        if self.featurewise_std_normalization:
            self.std = np.std(X, axis=0)
            X /= self.std

        if self.zca_whitening:
            flatX = np.reshape(X, (X.shape[0], X.shape[1]*X.shape[2]*X.shape[3]))
            fudge = 10e-6
            sigma = np.dot(flatX.T, flatX) / flatX.shape[1]
            U, S, V = linalg.svd(sigma)
            self.principal_components = np.dot(np.dot(U, np.diag(1. / np.sqrt(S + fudge))), U.T)



from __future__ import print_function
from keras.models import Sequential
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.datasets.data_utils import get_file
import numpy as np
import random, sys

'''
    Example script to generate text from Nietzsche's writings.

    At least 20 epochs are required before the generated text
    starts sounding coherent.

    It is recommended to run this script on GPU, as recurrent
    networks are quite computationally intensive.

    If you try this script on new data, make sure your corpus 
    has at least ~100k characters. ~1M is better.
'''

path = get_file('nietzsche.txt', origin="https://s3.amazonaws.com/text-datasets/nietzsche.txt")
text = open(path).read().lower()
print('corpus length:', len(text))

chars = set(text)
print('total chars:', len(chars))
char_indices = dict((c, i) for i, c in enumerate(chars))
indices_char = dict((i, c) for i, c in enumerate(chars))

# cut the text in semi-redundant sequences of maxlen characters
maxlen = 20
step = 3
sentences = []
next_chars = []
for i in range(0, len(text) - maxlen, step):
    sentences.append(text[i : i + maxlen])
    next_chars.append(text[i + maxlen])
print('nb sequences:', len(sentences))

print('Vectorization...')
X = np.zeros((len(sentences), maxlen, len(chars)))
y = np.zeros((len(sentences), len(chars)))
for i, sentence in enumerate(sentences):
    for t, char in enumerate(sentence):
        X[i, t, char_indices[char]] = 1.
    y[i, char_indices[next_chars[i]]] = 1.


# build the model: 2 stacked LSTM
print('Build model...')
model = Sequential()
model.add(LSTM(len(chars), 512, return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(512, 512, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(512, len(chars)))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

# helper function to sample an index from a probability array
def sample(a, diversity=0.75):
    if random.random() > diversity:
        return np.argmax(a)
    while 1:
        i = random.randint(0, len(a)-1)
        if a[i] > random.random():
            return i

# train the model, output generated text after each iteration
for iteration in range(1, 60):
    print()
    print('-' * 50)
    print('Iteration', iteration)
    model.fit(X, y, batch_size=128, nb_epoch=1)

    start_index = random.randint(0, len(text) - maxlen - 1)

    for diversity in [0.2, 0.4, 0.6, 0.8]:
        print()
        print('----- diversity:', diversity)

        generated = ''
        sentence = text[start_index : start_index + maxlen]
        generated += sentence
        print('----- Generating with seed: "' + sentence + '"')
        sys.stdout.write(generated)

        for iteration in range(400):
            x = np.zeros((1, maxlen, len(chars)))
            for t, char in enumerate(sentence):
                x[0, t, char_indices[char]] = 1.

            preds = model.predict(x, verbose=0)[0]
            next_index = sample(preds, diversity)
            next_char = indices_char[next_index]

            generated += next_char
            sentence = sentence[1:] + next_char

            sys.stdout.write(next_char)
            sys.stdout.flush()
        print()
from __future__ import absolute_import
from __future__ import print_function
import numpy as np

from keras.preprocessing import sequence
from keras.optimizers import SGD, RMSprop, Adagrad
from keras.utils import np_utils
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM, GRU
from keras.datasets import imdb

'''
    Train a LSTM on the IMDB sentiment classification task.

    The dataset is actually too small for LSTM to be of any advantage 
    compared to simpler, much faster methods such as TF-IDF+LogReg.

    Notes: 

    - RNNs are tricky. Choice of batch size is important, 
    choice of loss and optimizer is critical, etc. 
    Most configurations won't converge.

    - LSTM loss decrease during training can be quite different 
    from what you see with CNNs/MLPs/etc. It's more or less a sigmoid
    instead of an inverse exponential.

    GPU command:
        THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python imdb_lstm.py

    250s/epoch on GPU (GT 650M), vs. 400s/epoch on CPU (2.4Ghz Core i7).
'''

max_features=20000
maxlen = 100 # cut texts after this number of words (among top max_features most common words)
batch_size = 16

print("Loading data...")
(X_train, y_train), (X_test, y_test) = imdb.load_data(nb_words=max_features, test_split=0.2)
print(len(X_train), 'train sequences')
print(len(X_test), 'test sequences')

print("Pad sequences (samples x time)")
X_train = sequence.pad_sequences(X_train, maxlen=maxlen)
X_test = sequence.pad_sequences(X_test, maxlen=maxlen)
print('X_train shape:', X_train.shape)
print('X_test shape:', X_test.shape)

print('Build model...')
model = Sequential()
model.add(Embedding(max_features, 256))
model.add(LSTM(256, 128)) # try using a GRU instead, for fun
model.add(Dropout(0.5))
model.add(Dense(128, 1))
model.add(Activation('sigmoid'))

# try using different optimizers and different optimizer configs
model.compile(loss='binary_crossentropy', optimizer='adam', class_mode="binary")

print("Train...")
model.fit(X_train, y_train, batch_size=batch_size, nb_epoch=5, validation_split=0.1, show_accuracy=True)
score = model.evaluate(X_test, y_test, batch_size=batch_size)
print('Test score:', score)

classes = model.predict_classes(X_test, batch_size=batch_size)
acc = np_utils.accuracy(classes, y_test)
print('Test accuracy:', acc)


from __future__ import absolute_import
from __future__ import print_function

import numpy as np
import pandas as pd

from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.normalization import BatchNormalization
from keras.layers.advanced_activations import PReLU
from keras.utils import np_utils, generic_utils

from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler

'''
    This demonstrates how to reach a score of 0.4890 (local validation)
    on the Kaggle Otto challenge, with a deep net using Keras.

    Compatible Python 2.7-3.4 

    Recommended to run on GPU: 
        Command: THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python kaggle_otto_nn.py
        On EC2 g2.2xlarge instance: 19s/epoch. 6-7 minutes total training time.

    Best validation score at epoch 21: 0.4881 

    Try it at home:
        - with/without BatchNormalization (BatchNormalization helps!)
        - with ReLU or with PReLU (PReLU helps!)
        - with smaller layers, largers layers
        - with more layers, less layers
        - with different optimizers (SGD+momentum+decay is probably better than Adam!)

    Get the data from Kaggle: https://www.kaggle.com/c/otto-group-product-classification-challenge/data
'''

np.random.seed(1337) # for reproducibility

def load_data(path, train=True):
    df = pd.read_csv(path)
    X = df.values.copy()
    if train:
        np.random.shuffle(X) # https://youtu.be/uyUXoap67N8
        X, labels = X[:, 1:-1].astype(np.float32), X[:, -1]
        return X, labels
    else:
        X, ids = X[:, 1:].astype(np.float32), X[:, 0].astype(str)
        return X, ids

def preprocess_data(X, scaler=None):
    if not scaler:
        scaler = StandardScaler()
        scaler.fit(X)
    X = scaler.transform(X)
    return X, scaler

def preprocess_labels(labels, encoder=None, categorical=True):
    if not encoder:
        encoder = LabelEncoder()
        encoder.fit(labels)
    y = encoder.transform(labels).astype(np.int32)
    if categorical:
        y = np_utils.to_categorical(y)
    return y, encoder

def make_submission(y_prob, ids, encoder, fname):
    with open(fname, 'w') as f:
        f.write('id,')
        f.write(','.join([str(i) for i in encoder.classes_]))
        f.write('\n')
        for i, probs in zip(ids, y_prob):
            probas = ','.join([i] + [str(p) for p in probs.tolist()])
            f.write(probas)
            f.write('\n')
    print("Wrote submission to file {}.".format(fname))


print("Loading data...")
X, labels = load_data('train.csv', train=True)
X, scaler = preprocess_data(X)
y, encoder = preprocess_labels(labels)

X_test, ids = load_data('test.csv', train=False)
X_test, _ = preprocess_data(X_test, scaler)

nb_classes = y.shape[1]
print(nb_classes, 'classes')

dims = X.shape[1]
print(dims, 'dims')

print("Building model...")

model = Sequential()
model.add(Dense(dims, 512, init='glorot_uniform'))
model.add(PReLU((512,)))
model.add(BatchNormalization((512,)))
model.add(Dropout(0.5))

model.add(Dense(512, 512, init='glorot_uniform'))
model.add(PReLU((512,)))
model.add(BatchNormalization((512,)))
model.add(Dropout(0.5))

model.add(Dense(512, 512, init='glorot_uniform'))
model.add(PReLU((512,)))
model.add(BatchNormalization((512,)))
model.add(Dropout(0.5))

model.add(Dense(512, nb_classes, init='glorot_uniform'))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy', optimizer="adam")

print("Training model...")

model.fit(X, y, nb_epoch=20, batch_size=128, validation_split=0.15)

print("Generating submission...")

proba = model.predict_proba(X_test)
make_submission(proba, ids, encoder, fname='keras-otto.csv')



'''
    We loop over words in a dataset, and for each word, we look at a context window around the word. 
    We generate pairs of (pivot_word, other_word_from_same_context) with label 1,
    and pairs of (pivot_word, random_word) with label 0 (skip-gram method).

    We use the layer WordContextProduct to learn embeddings for the word couples,
    and compute a proximity score between the embeddings (= p(context|word)),
    trained with our positive and negative labels.

    We then use the weights computed by WordContextProduct to encode words 
    and demonstrate that the geometry of the embedding space 
    captures certain useful semantic properties.

    Read more about skip-gram in this particularly gnomic paper by Mikolov et al.: 
        http://arxiv.org/pdf/1301.3781v3.pdf

    Note: you should run this on GPU, otherwise training will be quite slow. 
    On a EC2 GPU instance, expect 3 hours per 10e6 comments (~10e8 words) per epoch with dim_proj=256.
    Should be much faster on a modern GPU.

    GPU command:
        THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python skipgram_word_embeddings.py

    Dataset: 5,845,908 Hacker News comments. 
    Obtain the dataset at: 
        https://mega.co.nz/#F!YohlwD7R!wec0yNO86SeaNGIYQBOR0A 
        (HNCommentsAll.1perline.json.bz2)
'''
from __future__ import absolute_import
from __future__ import print_function

import numpy as np
import theano
import six.moves.cPickle
import os, re, json

from keras.preprocessing import sequence, text
from keras.optimizers import SGD, RMSprop, Adagrad
from keras.utils import np_utils, generic_utils
from keras.models import Sequential
from keras.layers.embeddings import WordContextProduct, Embedding
from six.moves import range
from six.moves import zip

max_features = 50000 # vocabulary size: top 50,000 most common words in data
skip_top = 100 # ignore top 100 most common words
nb_epoch = 1
dim_proj = 256 # embedding space dimension

save = True
load_model = False
load_tokenizer = False
train_model = True
save_dir = os.path.expanduser("~/.keras/models")
model_load_fname = "HN_skipgram_model.pkl"
model_save_fname = "HN_skipgram_model.pkl"
tokenizer_fname = "HN_tokenizer.pkl"

data_path = os.path.expanduser("~/")+"HNCommentsAll.1perline.json"

# text preprocessing utils
html_tags = re.compile(r'<.*?>')
to_replace = [('&#x27;', "'")]
hex_tags = re.compile(r'&.*?;')

def clean_comment(comment):
    c = str(comment.encode("utf-8"))
    c = html_tags.sub(' ', c)
    for tag, char in to_replace:
        c = c.replace(tag, char)
    c = hex_tags.sub(' ', c)
    return c

def text_generator(path=data_path):
    f = open(path)
    for i, l in enumerate(f):
        comment_data = json.loads(l)
        comment_text = comment_data["comment_text"]
        comment_text = clean_comment(comment_text)
        if i % 10000 == 0:
            print(i)
        yield comment_text
    f.close()

# model management
if load_tokenizer:
    print('Load tokenizer...')
    tokenizer = six.moves.cPickle.load(open(os.path.join(save_dir, tokenizer_fname), 'rb'))
else:
    print("Fit tokenizer...")
    tokenizer = text.Tokenizer(nb_words=max_features)
    tokenizer.fit_on_texts(text_generator())
    if save:
        print("Save tokenizer...")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        six.moves.cPickle.dump(tokenizer, open(os.path.join(save_dir, tokenizer_fname), "wb"))

# training process
if train_model:
    if load_model:
        print('Load model...')
        model = six.moves.cPickle.load(open(os.path.join(save_dir, model_load_fname), 'rb'))
    else:
        print('Build model...')
        model = Sequential()
        model.add(WordContextProduct(max_features, proj_dim=dim_proj, init="uniform"))
        model.compile(loss='mse', optimizer='rmsprop')

    sampling_table = sequence.make_sampling_table(max_features)

    for e in range(nb_epoch):
        print('-'*40)
        print('Epoch', e)
        print('-'*40)

        progbar = generic_utils.Progbar(tokenizer.document_count)
        samples_seen = 0
        losses = []
        
        for i, seq in enumerate(tokenizer.texts_to_sequences_generator(text_generator())):
            # get skipgram couples for one text in the dataset
            couples, labels = sequence.skipgrams(seq, max_features, window_size=4, negative_samples=1., sampling_table=sampling_table)
            if couples:
                # one gradient update per sentence (one sentence = a few 1000s of word couples)
                X = np.array(couples, dtype="int32")
                loss = model.train(X, labels)
                losses.append(loss)
                if len(losses) % 100 == 0:
                    progbar.update(i, values=[("loss", np.mean(losses))])
                    losses = []
                samples_seen += len(labels)
        print('Samples seen:', samples_seen)
    print("Training completed!")

    if save:
        print("Saving model...")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        six.moves.cPickle.dump(model, open(os.path.join(save_dir, model_save_fname), "wb"))


print("It's test time!")

# recover the embedding weights trained with skipgram:
weights = model.layers[0].get_weights()[0]

# we no longer need this
del model

weights[:skip_top] = np.zeros((skip_top, dim_proj))
norm_weights = np_utils.normalize(weights)

word_index = tokenizer.word_index
reverse_word_index = dict([(v, k) for k, v in list(word_index.items())])
word_index = tokenizer.word_index

def embed_word(w):
    i = word_index.get(w)
    if (not i) or (i<skip_top) or (i>=max_features):
        return None
    return norm_weights[i]

def closest_to_point(point, nb_closest=10):
    proximities = np.dot(norm_weights, point)
    tups = list(zip(list(range(len(proximities))), proximities))
    tups.sort(key=lambda x: x[1], reverse=True)
    return [(reverse_word_index.get(t[0]), t[1]) for t in tups[:nb_closest]]  

def closest_to_word(w, nb_closest=10):
    i = word_index.get(w)
    if (not i) or (i<skip_top) or (i>=max_features):
        return []
    return closest_to_point(norm_weights[i].T, nb_closest)


''' the resuls in comments below were for: 
    5.8M HN comments
    dim_proj = 256
    nb_epoch = 2
    optimizer = rmsprop
    loss = mse
    max_features = 50000
    skip_top = 100
    negative_samples = 1.
    window_size = 4
    and frequency subsampling of factor 10e-5. 
'''

words = ["article", # post, story, hn, read, comments
"3", # 6, 4, 5, 2
"two", # three, few, several, each
"great", # love, nice, working, looking
"data", # information, memory, database
"money", # company, pay, customers, spend
"years", # ago, year, months, hours, week, days
"android", # ios, release, os, mobile, beta
"javascript", # js, css, compiler, library, jquery, ruby
"look", # looks, looking
"business", # industry, professional, customers
"company", # companies, startup, founders, startups
"after", # before, once, until
"own", # personal, our, having
"us", # united, country, american, tech, diversity, usa, china, sv
"using", # javascript, js, tools (lol)
"here", # hn, post, comments
]

for w in words:
    res = closest_to_word(w)
    print('====', w)
    for r in res:
        print(r)


from __future__ import absolute_import
from __future__ import print_function
import numpy as np

from keras.datasets import reuters
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.normalization import BatchNormalization
from keras.utils import np_utils
from keras.preprocessing.text import Tokenizer

'''
    Train and evaluate a simple MLP on the Reuters newswire topic classification task.
    GPU run command:
        THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python examples/reuters_mlp.py
    CPU run command:
        python examples/reuters_mlp.py
'''

max_words = 1000
batch_size = 32

print("Loading data...")
(X_train, y_train), (X_test, y_test) = reuters.load_data(nb_words=max_words, test_split=0.2)
print(len(X_train), 'train sequences')
print(len(X_test), 'test sequences')

nb_classes = np.max(y_train)+1
print(nb_classes, 'classes')

print("Vectorizing sequence data...")
tokenizer = Tokenizer(nb_words=max_words)
X_train = tokenizer.sequences_to_matrix(X_train, mode="binary")
X_test = tokenizer.sequences_to_matrix(X_test, mode="binary")
print('X_train shape:', X_train.shape)
print('X_test shape:', X_test.shape)

print("Convert class vector to binary class matrix (for use with categorical_crossentropy)")
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)
print('Y_train shape:', Y_train.shape)
print('Y_test shape:', Y_test.shape)

print("Building model...")
model = Sequential()
model.add(Dense(max_words, 256, init='normal'))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(256, nb_classes, init='normal'))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy', optimizer='adam')

history = model.fit(X_train, Y_train, nb_epoch=4, batch_size=batch_size, verbose=1, show_accuracy=True, validation_split=0.1)
score = model.evaluate(X_test, Y_test, batch_size=batch_size, verbose=1, show_accuracy=True)
print('Test score:', score[0])
print('Test accuracy:', score[1])

from __future__ import absolute_import
from __future__ import print_function
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.regularizers import l2, l1
from keras.constraints import maxnorm
from keras.optimizers import SGD, Adam, RMSprop
from keras.utils import np_utils
import numpy as np

'''
    Train a simple deep NN on the MNIST dataset.
'''

batch_size = 64
nb_classes = 10
nb_epoch = 20

np.random.seed(1337) # for reproducibility

# the data, shuffled and split between tran and test sets
(X_train, y_train), (X_test, y_test) = mnist.load_data()

X_train = X_train.reshape(60000,784)
X_test = X_test.reshape(10000,784)
X_train = X_train.astype("float32")
X_test = X_test.astype("float32")
X_train /= 255
X_test /= 255
print(X_train.shape[0], 'train samples')
print(X_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)

model = Sequential()
model.add(Dense(784, 128))
model.add(Activation('relu'))
model.add(Dropout(0.2))
model.add(Dense(128, 128))
model.add(Activation('relu'))
model.add(Dropout(0.2))
model.add(Dense(128, 10))
model.add(Activation('softmax'))

rms = RMSprop()
model.compile(loss='categorical_crossentropy', optimizer=rms)

model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch, show_accuracy=True, verbose=2, validation_data=(X_test, Y_test))
score = model.evaluate(X_test, Y_test, show_accuracy=True, verbose=0)
print('Test score:', score[0])
print('Test accuracy:', score[1])

from __future__ import absolute_import
from __future__ import print_function
from keras.datasets import cifar10
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import SGD, Adadelta, Adagrad
from keras.utils import np_utils, generic_utils
from six.moves import range

'''
    Train a (fairly simple) deep CNN on the CIFAR10 small images dataset.

    GPU run command:
        THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python cifar10_cnn.py

    It gets down to 0.65 test logloss in 25 epochs, and down to 0.55 after 50 epochs.
    (it's still underfitting at that point, though).

    Note: the data was pickled with Python 2, and some encoding issues might prevent you
    from loading it in Python 3. You might have to load it in Python 2, 
    save it in a different format, load it in Python 3 and repickle it.
'''

batch_size = 32
nb_classes = 10
nb_epoch = 200
data_augmentation = True

# the data, shuffled and split between tran and test sets
(X_train, y_train), (X_test, y_test) = cifar10.load_data()
print(X_train.shape[0], 'train samples')
print(X_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)

model = Sequential()

model.add(Convolution2D(32, 3, 3, 3, border_mode='full')) 
model.add(Activation('relu'))
model.add(Convolution2D(32, 32, 3, 3))
model.add(Activation('relu'))
model.add(MaxPooling2D(poolsize=(2, 2)))
model.add(Dropout(0.25))

model.add(Convolution2D(64, 32, 3, 3, border_mode='full')) 
model.add(Activation('relu'))
model.add(Convolution2D(64, 64, 3, 3)) 
model.add(Activation('relu'))
model.add(MaxPooling2D(poolsize=(2, 2)))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(64*8*8, 512, init='normal'))
model.add(Activation('relu'))
model.add(Dropout(0.5))

model.add(Dense(512, nb_classes, init='normal'))
model.add(Activation('softmax'))

# let's train the model using SGD + momentum (how original).
sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd)

if not data_augmentation:
    print("Not using data augmentation or normalization")

    X_train = X_train.astype("float32")
    X_test = X_test.astype("float32")
    X_train /= 255
    X_test /= 255
    model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=10)
    score = model.evaluate(X_test, Y_test, batch_size=batch_size)
    print('Test score:', score)

else:
    print("Using real time data augmentation")

    # this will do preprocessing and realtime data augmentation
    datagen = ImageDataGenerator(
        featurewise_center=True, # set input mean to 0 over the dataset
        samplewise_center=False, # set each sample mean to 0
        featurewise_std_normalization=True, # divide inputs by std of the dataset
        samplewise_std_normalization=False, # divide each input by its std
        zca_whitening=False, # apply ZCA whitening
        rotation_range=20, # randomly rotate images in the range (degrees, 0 to 180)
        width_shift_range=0.2, # randomly shift images horizontally (fraction of total width)
        height_shift_range=0.2, # randomly shift images vertically (fraction of total height)
        horizontal_flip=True, # randomly flip images
        vertical_flip=False) # randomly flip images

    # compute quantities required for featurewise normalization 
    # (std, mean, and principal components if ZCA whitening is applied)
    datagen.fit(X_train)

    for e in range(nb_epoch):
        print('-'*40)
        print('Epoch', e)
        print('-'*40)
        print("Training...")
        # batch train with realtime data augmentation
        progbar = generic_utils.Progbar(X_train.shape[0])
        for X_batch, Y_batch in datagen.flow(X_train, Y_train):
            loss = model.train(X_batch, Y_batch)
            progbar.add(X_batch.shape[0], values=[("train loss", loss)])

        print("Testing...")
        # test time!
        progbar = generic_utils.Progbar(X_test.shape[0])
        for X_batch, Y_batch in datagen.flow(X_test, Y_test):
            score = model.test(X_batch, Y_batch)
            progbar.add(X_batch.shape[0], values=[("test loss", score)])

            







