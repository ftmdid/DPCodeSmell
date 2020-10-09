import theano
from theano import tensor as T
from theano.sandbox.rng_mrg import MRG_RandomStreams as RandomStreams
from theano.tensor.signal import downsample
import numpy as np
from .common import _FLOATX, _EPSILON


# INTERNAL UTILS

def _on_gpu():
    '''Returns whether the session is set to
    run on GPU or not (i.e. on CPU).
    '''
    return theano.config.device[:3] == 'gpu'


if _on_gpu():
    '''Import cuDNN only if running on GPU:
    not having Cuda install should not
    prevent from running the present code.
    '''
    from theano.sandbox.cuda import dnn


# VARIABLE MANIPULATION

def variable(value, dtype=_FLOATX, name=None):
    '''Instantiate a tensor variable.
    '''
    value = np.asarray(value, dtype=dtype)
    return theano.shared(value=value, name=name, strict=False)


def placeholder(shape=None, ndim=None, dtype=_FLOATX, name=None):
    '''Instantiate an input data placeholder variable.
    '''
    if shape is None and ndim is None:
        raise Exception('Specify either a shape or ndim value.')
    if shape is not None:
        ndim = len(shape)
    if ndim == 0:
        return T.scalar(name=name, dtype=dtype)
    elif ndim == 1:
        return T.vector(name=name, dtype=dtype)
    elif ndim == 2:
        return T.matrix(name=name, dtype=dtype)
    elif ndim == 3:
        return T.tensor3(name=name, dtype=dtype)
    elif ndim == 4:
        return T.tensor4(name=name, dtype=dtype)
    else:
        raise Exception('ndim too large: ' + str(ndim))


def shape(x):
    '''Return the shape of a tensor.

    Warning: type returned will be different for
    Theano backend (Theano tensor type) and TF backend (TF TensorShape).
    '''
    return x.shape


def eval(x):
    '''Run a graph.
    '''
    return x.eval()


def zeros(shape, dtype=_FLOATX, name=None):
    '''Instantiate an all-zeros variable.
    '''
    return variable(np.zeros(shape), dtype, name)


def ones(shape, dtype=_FLOATX, name=None):
    '''Instantiate an all-ones variable.
    '''
    return variable(np.ones(shape), dtype, name)


def ones_like(x):
    return T.ones_like(x)


def zeros_like(x):
    return T.zeros_like(x)


# LINEAR ALGEBRA

'''
Assumed overridden:
+, -, /, *, +=, -=, *=, /=
'''


def dot(x, y):
    return T.dot(x, y)


def transpose(x):
    return T.transpose(x)


def embedding(reference, indices):
    '''reference: a tensor.
    indices: an int tensor of indices.

    Return: a tensor of same type as reference.
    '''
    return reference[indices]


# ELEMENT-WISE OPERATIONS

def max(x, axis=None, keepdims=False):
    return T.max(x, axis=axis, keepdims=keepdims)


def min(x, axis=None, keepdims=False):
    return T.min(x, axis=axis, keepdims=keepdims)


def sum(x, axis=None, keepdims=False):
    '''Sum of the values in a tensor, alongside the specified axis.
    '''
    return T.sum(x, axis=axis, keepdims=keepdims)


def mul(x, axis=None, keepdims=False):
    '''Multiply the values in a tensor, alongside the specified axis.
    '''
    return T.mul(x, axis=axis, keepdims=keepdims)


def mean(x, axis=None, keepdims=False):
    return T.mean(x, axis=axis, keepdims=keepdims)


def any(x, axis=None, keepdims=False):
    '''Bitwise reduction (logical OR).
    '''
    return T.any(x, axis=axis, keepdims=keepdims)


def argmax(x, axis=-1):
    return T.argmax(x, axis=axis, keepdims=False)


def argmin(x, axis=-1):
    return T.argmin(x, axis=axis, keepdims=False)


def square(x):
    return T.sqr(x)


def abs(x):
    return T.abs_(x)


def sqrt(x):
    x = T.clip(x, 0., np.inf)
    return T.sqrt(x)


def exp(x):
    return T.exp(x)


def log(x):
    return T.log(x)


def round(x):
    return T.round(x)


def clip(x, min_value, max_value):
    if max_value < min_value:
        max_value = min_value
    return T.clip(x, min_value, max_value)


def equal(x, y):
    return T.eq(x, y)


def maximum(x, y):
    return T.maximum(x, y)


def minimum(x, y):
    return T.minimum(x, y)


# SHAPE OPERATIONS

def concatenate(tensors, axis=-1):
    return T.concatenate(tensors, axis=axis)


def reshape(x, shape):
    return T.reshape(x, shape)


def permute_dimensions(x, pattern):
    '''Transpose dimensions.

    pattern should be a tuple or list of
    dimension indices, e.g. [0, 2, 1].
    '''
    pattern = tuple(pattern)
    return x.dimshuffle(pattern)


def repeat(x, n, axis=-1):
    return T.extra_ops.repeat(x, n, axis=axis)


def flatten(x):
    x = T.reshape(x, (x.shape[0], T.prod(x.shape) // x.shape[0]))
    return x


# VALUE MANIPULATION

def get_value(x):
    if not hasattr(x, 'get_value'):
        raise Exception("'get_value() can only be called on a variable. " +
                        "If you have an expression instead, use eval().")
    return x.get_value()


def set_value(x, value):
    x.set_value(np.asarray(value, dtype=x.dtype))


# GRAPH MANIPULATION

class Function(object):

    def __init__(self, inputs, outputs, updates=[], **kwargs):
        self.function = theano.function(inputs, outputs, updates=updates,
                                        allow_input_downcast=True, **kwargs)

    def __call__(self, inputs):
        if len(inputs) == 1:
            inputs = inputs[0]  # Theano is pretty dumb there tbh
        return self.function(inputs)


def function(inputs, outputs, updates=[]):
    return Function(inputs, outputs, updates=updates)


def gradients(loss, variables):
    return T.grad(loss, variables)


# CONTROL FLOW

def rnn(step_function, inputs, initial_states, go_backwards=False):
    '''TODO

    Wrapper for scan
    '''
    pass


def switch(condition, then_expression, else_expression):
    '''condition: scalar tensor.
    '''
    return T.switch(condition, then_expression, else_expression)


# NN OPERATIONS

def relu(x, alpha=0., max_value=None):
    x = T.nnet.relu(x, alpha)
    if max_value is not None:
        x = T.minimum(x, max_value)
    return x


def softmax(x):
    return T.nnet.softmax(x)


def softplus(x):
    return T.nnet.softplus(x)


def categorical_crossentropy(output, target, from_logits=False):
    if from_logits:
        output = T.nnet.softmax(output)
    else:
        # scale preds so that the class probas of each sample sum to 1
        output /= output.sum(axis=-1, keepdims=True)
    # avoid numerical instability with _EPSILON clipping
    output = T.clip(output, _EPSILON, 1.0 - _EPSILON)
    return T.nnet.categorical_crossentropy(output, target)


def binary_crossentropy(output, target, from_logits=False):
    if from_logits:
        output = T.nnet.sigmoid(output)
    # avoid numerical instability with _EPSILON clipping
    output = T.clip(output, _EPSILON, 1.0 - _EPSILON)
    return T.nnet.binary_crossentropy(output, target)


def sigmoid(x):
    return T.nnet.sigmoid(x)


def hard_sigmoid(x):
    return T.nnet.hard_sigmoid(x)


def tanh(x):
    return T.tanh(x)


def dropout(x, level, seed=None):
    if level < 0. or level >= 1:
        raise Exception('Dropout level must be in interval [0, 1[.')
    if seed is None:
        seed = np.random.randint(10e6)
    rng = RandomStreams(seed=seed)
    retain_prob = 1. - level
    x *= rng.binomial(x.shape, p=retain_prob, dtype=x.dtype)
    x /= retain_prob
    return x


# CONVOLUTIONS


def conv2d(x, kernel, strides=(1, 1), border_mode='valid', dim_ordering='th'):
    '''
    Run on cuDNN if available.
    border_mode: string, "same" or "valid".
    '''
    if dim_ordering not in {'th', 'tf'}:
        raise Exception('Unknown dim_ordering ' + str(dim_ordering))

    if dim_ordering == 'tf':
        # TF uses the last dimension as channel dimension,
        # instead of the 2nd one.
        # TH input shape: (samples, input_depth, rows, cols)
        # TF input shape: (samples, rows, cols, input_depth)
        # TH kernel shape: (depth, input_depth, rows, cols)
        # TF kernel shape: (rows, cols, input_depth, depth)
        x = x.dimshuffle((0, 3, 1, 2))
        kernel = kernel.dimshuffle((3, 2, 0, 1))

    if _on_gpu() and dnn.dnn_available():
        if border_mode == 'same':
            assert(strides == (1, 1))
            pad_x = (kernel.shape[2] - strides[0]) // 2
            pad_y = (kernel.shape[3] - strides[1]) // 2
            conv_out = dnn.dnn_conv(img=x,
                                    kerns=kernel,
                                    border_mode=(pad_x, pad_y))
        else:
            conv_out = dnn.dnn_conv(img=x,
                                    kerns=kernel,
                                    border_mode=border_mode,
                                    subsample=strides)
    else:
        if border_mode == 'same':
            th_border_mode = 'full'
            assert(strides == (1, 1))
        elif border_mode == 'valid':
            th_border_mode = 'valid'
        else:
            raise Exception('Border mode not supported: ' + str(border_mode))

        conv_out = T.nnet.conv.conv2d(x, kernel,
                                      border_mode=th_border_mode,
                                      subsample=strides)
        if border_mode == 'same':
            shift_x = (kernel.shape[2] - 1) // 2
            shift_y = (kernel.shape[3] - 1) // 2
            conv_out = conv_out[:, :,
                                shift_x:x.shape[2] + shift_x,
                                shift_y:x.shape[3] + shift_y]
    if dim_ordering == 'tf':
        conv_out = conv_out.dimshuffle((0, 2, 3, 1))
    return conv_out


def maxpool2d(x, pool_size, strides=(1, 1), border_mode='valid', dim_ordering='th'):
    if border_mode == 'same':
        # TODO: add implementation for border_mode="same"
        raise Exception('border_mode="same" not supported with Theano.')
    elif border_mode == 'valid':
        ignore_border = True
        padding = (0, 0)
    else:
        raise Exception('Invalid border mode: ' + str(border_mode))

    if dim_ordering not in {'th', 'tf'}:
        raise Exception('Unknown dim_ordering ' + str(dim_ordering))

    if dim_ordering == 'tf':
        x = x.dimshuffle((0, 3, 1, 2))

    pool_out = downsample.max_pool_2d(x,
                                      ds=pool_size,
                                      st=strides,
                                      ignore_border=ignore_border,
                                      padding=padding,
                                      mode='average_exc_pad')
    if dim_ordering == 'tf':
        pool_out = pool_out.dimshuffle((0, 2, 3, 1))
    return pool_out


# RANDOMNESS

def random_normal(shape, mean=0.0, std=1.0, dtype=_FLOATX, seed=None):
    if seed is None:
        seed = np.random.randint(10e6)
    rng = RandomStreams(seed=seed)
    return rng.normal(size=shape, avg=mean, std=std, dtype=dtype)


def random_uniform(shape, low=0.0, high=1.0, dtype=_FLOATX, seed=None):
    if seed is None:
        seed = np.random.randint(10e6)
    rng = RandomStreams(seed=seed)
    return rng.uniform(shape, low=low, high=high, dtype=dtype)



'''
more TODO:

shape_padright/left
tensordot
batched_tensordot

addbroadcast -> remove usage?
unbroadcast -> remove usage?
'''