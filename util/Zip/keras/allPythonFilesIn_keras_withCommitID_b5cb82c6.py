import pyux
import keras
import json


import keras.backend.tensorflow_backend
import keras.backend.theano_backend
import keras.backend.cntk_backend
import keras.backend.numpy_backend
import keras.utils.test_utils

sign = pyux.sign(keras)

with open('api.json', 'w') as f:
    json.dump(sign, f)

from setuptools import setup
from setuptools import find_packages

long_description = '''
Keras is a high-level neural networks API,
written in Python and capable of running on top of
TensorFlow, CNTK, or Theano.

Use Keras if you need a deep learning library that:

- Allows for easy and fast prototyping
  (through user friendliness, modularity, and extensibility).
- Supports both convolutional networks and recurrent networks,
  as well as combinations of the two.
- Runs seamlessly on CPU and GPU.

Read the documentation at: https://keras.io/

For a detailed overview of what makes Keras special, see:
https://keras.io/why-use-keras/

Keras is compatible with Python 2.7-3.6
and is distributed under the MIT license.
'''

setup(name='Keras',
      version='2.4.0',
      description='Deep Learning for humans',
      long_description=long_description,
      author='Francois Chollet',
      author_email='francois.chollet@gmail.com',
      url='https://github.com/keras-team/keras',
      download_url='https://github.com/keras-team/keras/tarball/2.3.0',
      license='MIT',
      install_requires=['tensorflow>=2.2.0',
                        'numpy>=1.9.1',
                        'scipy>=0.14',
                        'pyyaml',
                        'h5py'],
      extras_require={
          'visualize': ['pydot>=1.2.4'],
          'tests': ['pytest',
                    'pytest-pep8',
                    'pytest-xdist',
                    'flaky',
                    'pytest-cov',
                    'pandas',
                    'requests',
                    'markdown'],
      },
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'Intended Audience :: Education',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules'
      ],
      packages=find_packages())

"""Built-in metrics."""
from tensorflow.keras.metrics import *

from tensorflow.keras.backend import *
"""Model-related utilities."""
from .engine.input_layer import Input
from .engine.input_layer import InputLayer
from .engine.training import Model
from .engine.sequential import Sequential
from .engine.saving import save_model
from .engine.saving import load_model
from .engine.saving import model_from_config
from .engine.saving import model_from_yaml
from .engine.saving import model_from_json

from tensorflow.keras.models import clone_model

"""Built-in activation functions."""

from tensorflow.keras.activations import softmax
from tensorflow.keras.activations import elu
from tensorflow.keras.activations import selu
from tensorflow.keras.activations import softplus
from tensorflow.keras.activations import softsign
from tensorflow.keras.activations import relu
from tensorflow.keras.activations import tanh
from tensorflow.keras.activations import sigmoid
from tensorflow.keras.activations import hard_sigmoid
from tensorflow.keras.activations import exponential
from tensorflow.keras.activations import linear

from tensorflow.keras.activations import get
from tensorflow.keras.activations import serialize
from tensorflow.keras.activations import deserialize

from . import utils
from . import activations
from . import applications
from . import backend
from . import datasets
from . import engine
from . import layers
from . import preprocessing
from . import wrappers
from . import callbacks
from . import constraints
from . import initializers
from . import metrics
from . import models
from . import losses
from . import optimizers
from . import regularizers

# Also importable from root
from .layers import Input
from .models import Model
from .models import Sequential

from tensorflow.keras import __version__

"""Built-in regularizers."""
from tensorflow.keras.regularizers import *

"""Legacy objectives module.

Only kept for backwards API compatibility.
"""
from __future__ import absolute_import
from .losses import *

"""Built-in weight initializers."""

from tensorflow.keras.initializers import *
from tensorflow.keras.callbacks import *

"""Built-in loss functions."""
from tensorflow.keras.losses import *

"""Constraints: functions that impose constraints on weight values.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tensorflow.keras.constraints import Constraint

from tensorflow.keras.constraints import MaxNorm
from tensorflow.keras.constraints import NonNeg
from tensorflow.keras.constraints import UnitNorm
from tensorflow.keras.constraints import MinMaxNorm

from tensorflow.keras.constraints import get
from tensorflow.keras.constraints import serialize
from tensorflow.keras.constraints import deserialize

# Aliases.

max_norm = MaxNorm
non_neg = NonNeg
unit_norm = UnitNorm
min_max_norm = MinMaxNorm


# Legacy aliases.
maxnorm = max_norm
nonneg = non_neg
unitnorm = unit_norm


from . import scikit_learn

"""Wrapper for using the Scikit-Learn API with Keras models."""
from tensorflow.keras.wrappers.scikit_learn import *

"""Layers that can merge several inputs into one."""

from tensorflow.keras.layers import Add
from tensorflow.keras.layers import Subtract
from tensorflow.keras.layers import Multiply
from tensorflow.keras.layers import Average
from tensorflow.keras.layers import Maximum
from tensorflow.keras.layers import Minimum
from tensorflow.keras.layers import Concatenate
from tensorflow.keras.layers import Dot
from tensorflow.keras.layers import add
from tensorflow.keras.layers import subtract
from tensorflow.keras.layers import multiply
from tensorflow.keras.layers import average
from tensorflow.keras.layers import maximum
from tensorflow.keras.layers import minimum
from tensorflow.keras.layers import concatenate
from tensorflow.keras.layers import dot

"""Convolutional layers."""
from tensorflow.keras.layers import Conv1D
from tensorflow.keras.layers import Conv2D
from tensorflow.keras.layers import Conv3D
from tensorflow.keras.layers import Conv2DTranspose
from tensorflow.keras.layers import Conv3DTranspose
from tensorflow.keras.layers import SeparableConv1D
from tensorflow.keras.layers import SeparableConv2D
from tensorflow.keras.layers import DepthwiseConv2D
from tensorflow.keras.layers import UpSampling1D
from tensorflow.keras.layers import UpSampling2D
from tensorflow.keras.layers import UpSampling3D
from tensorflow.keras.layers import ZeroPadding1D
from tensorflow.keras.layers import ZeroPadding2D
from tensorflow.keras.layers import ZeroPadding3D
from tensorflow.keras.layers import Cropping1D
from tensorflow.keras.layers import Cropping2D
from tensorflow.keras.layers import Cropping3D

# Aliases

Convolution1D = Conv1D
Convolution2D = Conv2D
Convolution3D = Conv3D
SeparableConvolution1D = SeparableConv1D
SeparableConvolution2D = SeparableConv2D
Convolution2DTranspose = Conv2DTranspose
Deconvolution2D = Deconv2D = Conv2DTranspose
Deconvolution3D = Deconv3D = Conv3DTranspose

# imports for backwards namespace compatibility

from .pooling import AveragePooling1D
from .pooling import AveragePooling2D
from .pooling import AveragePooling3D
from .pooling import MaxPooling1D
from .pooling import MaxPooling2D
from .pooling import MaxPooling3D

"""Recurrent layers and their base classes."""

from tensorflow.keras.layers import RNN
from tensorflow.keras.layers import StackedRNNCells

from tensorflow.keras.layers import SimpleRNN
from tensorflow.keras.layers import GRU
from tensorflow.keras.layers import LSTM

from tensorflow.keras.layers import SimpleRNNCell
from tensorflow.keras.layers import GRUCell
from tensorflow.keras.layers import LSTMCell

"""Locally-connected layers."""

from tensorflow.keras.layers import LocallyConnected1D
from tensorflow.keras.layers import LocallyConnected2D

"""Pooling layers."""

from tensorflow.keras.layers import MaxPooling1D
from tensorflow.keras.layers import MaxPooling2D
from tensorflow.keras.layers import MaxPooling3D

from tensorflow.keras.layers import AveragePooling1D
from tensorflow.keras.layers import AveragePooling2D
from tensorflow.keras.layers import AveragePooling3D

from tensorflow.keras.layers import GlobalAveragePooling1D
from tensorflow.keras.layers import GlobalAveragePooling2D
from tensorflow.keras.layers import GlobalAveragePooling3D

from tensorflow.keras.layers import GlobalMaxPooling1D
from tensorflow.keras.layers import GlobalMaxPooling2D
from tensorflow.keras.layers import GlobalMaxPooling3D


# Aliases

AvgPool1D = AveragePooling1D
MaxPool1D = MaxPooling1D
AvgPool2D = AveragePooling2D
MaxPool2D = MaxPooling2D
AvgPool3D = AveragePooling3D
MaxPool3D = MaxPooling3D
GlobalMaxPool1D = GlobalMaxPooling1D
GlobalMaxPool2D = GlobalMaxPooling2D
GlobalMaxPool3D = GlobalMaxPooling3D
GlobalAvgPool1D = GlobalAveragePooling1D
GlobalAvgPool2D = GlobalAveragePooling2D
GlobalAvgPool3D = GlobalAveragePooling3D

from tensorflow.keras.layers import *

from . import advanced_activations
from . import convolutional
from . import convolutional_recurrent
from . import core
from . import embeddings
from . import experimental
from . import local
from . import merge
from . import noise
from . import normalization
from . import pooling
from . import recurrent
from . import wrappers

"""Core Keras layers."""

from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Activation
from tensorflow.keras.layers import ActivityRegularization
from tensorflow.keras.layers import Lambda
from tensorflow.keras.layers import Masking

from tensorflow.keras.layers import Dropout
from tensorflow.keras.layers import SpatialDropout1D
from tensorflow.keras.layers import SpatialDropout2D
from tensorflow.keras.layers import SpatialDropout3D

from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import Permute
from tensorflow.keras.layers import RepeatVector
from tensorflow.keras.layers import Reshape

"""Embedding layer."""

from tensorflow.keras.layers import Embedding

"""Layers that augment the functionality of a base layer."""

from tensorflow.keras.layers import Wrapper
from tensorflow.keras.layers import TimeDistributed
from tensorflow.keras.layers import Bidirectional

"""Layers that operate regularization via the addition of noise."""

from tensorflow.keras.layers import GaussianNoise
from tensorflow.keras.layers import GaussianDropout
from tensorflow.keras.layers import AlphaDropout

"""Layers that act as activation functions."""

from tensorflow.keras.layers import LeakyReLU
from tensorflow.keras.layers import PReLU
from tensorflow.keras.layers import ELU
from tensorflow.keras.layers import ThresholdedReLU
from tensorflow.keras.layers import Softmax
from tensorflow.keras.layers import ReLU

"""Normalization layers."""

from tensorflow.keras.layers import BatchNormalization

"""Recurrent layers backed by cuDNN."""

from tensorflow.keras.layers import GRU as CuDNNGRU
from tensorflow.keras.layers import LSTM as CuDNNLSTM

"""Convolutional-recurrent layers."""

from tensorflow.keras.layers import ConvLSTM2D

from tensorflow.keras.layers.experimental import *
from tensorflow.keras.layers.experimental.preprocessing import *

"""CIFAR100 small images classification dataset."""

from tensorflow.keras.datasets.cifar100 import load_data

"""Fashion-MNIST dataset."""

from tensorflow.keras.datasets.fashion_mnist import load_data

from . import mnist
from . import imdb
from . import reuters
from . import cifar10
from . import cifar100
from . import boston_housing
from . import fashion_mnist

"""IMDB sentiment classification dataset."""

from tensorflow.keras.datasets.imdb import load_data
from tensorflow.keras.datasets.imdb import get_word_index

"""Boston housing price regression dataset."""

from tensorflow.keras.datasets.boston_housing import load_data

"""Reuters topic classification dataset."""

from tensorflow.keras.datasets.reuters import load_data
from tensorflow.keras.datasets.reuters import get_word_index

"""CIFAR10 small images classification dataset."""

from tensorflow.keras.datasets.cifar10 import load_data

"""MNIST handwritten digits dataset."""

from tensorflow.keras.datasets.mnist import load_data

"""Utilities related to layer/model functionality.
"""
from .conv_utils import convert_kernel
from .. import backend as K
import numpy as np


from tensorflow.keras.utils import get_source_inputs
from tensorflow.python.keras.utils.layer_utils import print_summary


def count_params(weights):
    """Count the total number of scalars composing the weights.

    # Arguments
        weights: An iterable containing the weights on which to compute params

    # Returns
        The total number of scalars composing the weights
    """
    weight_ids = set()
    total = 0
    for w in weights:
        if id(w) not in weight_ids:
            weight_ids.add(id(w))
            total += int(K.count_params(w))
    return total


def convert_all_kernels_in_model(model):
    """Converts all convolution kernels in a model from Theano to TensorFlow.

    Also works from TensorFlow to Theano.

    # Arguments
        model: target model for the conversion.
    """
    # Note: SeparableConvolution not included
    # since only supported by TF.
    conv_classes = {
        'Conv1D',
        'Conv2D',
        'Conv3D',
        'Conv2DTranspose',
    }
    to_assign = []
    for layer in model.layers:
        if layer.__class__.__name__ in conv_classes:
            original_kernel = K.get_value(layer.kernel)
            converted_kernel = convert_kernel(original_kernel)
            to_assign.append((layer.kernel, converted_kernel))
    K.batch_set_value(to_assign)


def convert_dense_weights_data_format(dense,
                                      previous_feature_map_shape,
                                      target_data_format='channels_first'):
    """Utility useful when changing a convnet's `data_format`.

    When porting the weights of a convnet from one data format to the other,
    if the convnet includes a `Flatten` layer
    (applied to the last convolutional feature map)
    followed by a `Dense` layer, the weights of that `Dense` layer
    should be updated to reflect the new dimension ordering.

    # Arguments
        dense: The target `Dense` layer.
        previous_feature_map_shape: A shape tuple of 3 integers,
            e.g. `(512, 7, 7)`. The shape of the convolutional
            feature map right before the `Flatten` layer that
            came before the target `Dense` layer.
        target_data_format: One of "channels_last", "channels_first".
            Set it "channels_last"
            if converting a "channels_first" model to "channels_last",
            or reciprocally.
    """
    assert target_data_format in {'channels_last', 'channels_first'}
    kernel, bias = dense.get_weights()
    for i in range(kernel.shape[1]):
        if target_data_format == 'channels_first':
            c, h, w = previous_feature_map_shape
            original_fm_shape = (h, w, c)
            ki = kernel[:, i].reshape(original_fm_shape)
            ki = np.transpose(ki, (2, 0, 1))  # last -> first
        else:
            h, w, c = previous_feature_map_shape
            original_fm_shape = (c, h, w)
            ki = kernel[:, i].reshape(original_fm_shape)
            ki = np.transpose(ki, (1, 2, 0))  # first -> last
        kernel[:, i] = np.reshape(ki, (np.prod(previous_feature_map_shape),))
    dense.set_weights([kernel, bias])

"""Python utilities required by Keras."""

import inspect
import sys

from tensorflow.keras.utils import CustomObjectScope
from tensorflow.keras.utils import custom_object_scope
from tensorflow.keras.utils import get_custom_objects
from tensorflow.keras.utils import serialize_keras_object
from tensorflow.keras.utils import deserialize_keras_object
from tensorflow.keras.utils import Progbar


def to_list(x, allow_tuple=False):
    """Normalizes a list/tensor into a list.

    If a tensor is passed, we return
    a list of size 1 containing the tensor.

    # Arguments
        x: target object to be normalized.
        allow_tuple: If False and x is a tuple,
            it will be converted into a list
            with a single element (the tuple).
            Else converts the tuple to a list.

    # Returns
        A list.
    """
    if isinstance(x, list):
        return x
    if allow_tuple and isinstance(x, tuple):
        return list(x)
    return [x]


def unpack_singleton(x):
    """Gets the first element if the iterable has only one value.

    Otherwise return the iterable.

    # Argument
        x: A list or tuple.

    # Returns
        The same iterable or the first element.
    """
    if len(x) == 1:
        return x[0]
    return x


def object_list_uid(object_list):
    object_list = to_list(object_list)
    return ', '.join((str(abs(id(x))) for x in object_list))


def is_all_none(iterable_or_element):
    iterable = to_list(iterable_or_element, allow_tuple=True)
    for element in iterable:
        if element is not None:
            return False
    return True


def slice_arrays(arrays, start=None, stop=None):
    """Slices an array or list of arrays.

    This takes an array-like, or a list of
    array-likes, and outputs:
        - arrays[start:stop] if `arrays` is an array-like
        - [x[start:stop] for x in arrays] if `arrays` is a list

    Can also work on list/array of indices: `_slice_arrays(x, indices)`

    # Arguments
        arrays: Single array or list of arrays.
        start: can be an integer index (start index)
            or a list/array of indices
        stop: integer (stop index); should be None if
            `start` was a list.

    # Returns
        A slice of the array(s).
    """
    if arrays is None:
        return [None]
    elif isinstance(arrays, list):
        if hasattr(start, '__len__'):
            # hdf5 datasets only support list objects as indices
            if hasattr(start, 'shape'):
                start = start.tolist()
            return [None if x is None else x[start] for x in arrays]
        else:
            return [None if x is None else x[start:stop] for x in arrays]
    else:
        if hasattr(start, '__len__'):
            if hasattr(start, 'shape'):
                start = start.tolist()
            return arrays[start]
        elif hasattr(start, '__getitem__'):
            return arrays[start:stop]
        else:
            return [None]


def transpose_shape(shape, target_format, spatial_axes):
    """Converts a tuple or a list to the correct `data_format`.

    It does so by switching the positions of its elements.

    # Arguments
        shape: Tuple or list, often representing shape,
            corresponding to `'channels_last'`.
        target_format: A string, either `'channels_first'` or `'channels_last'`.
        spatial_axes: A tuple of integers.
            Correspond to the indexes of the spatial axes.
            For example, if you pass a shape
            representing (batch_size, timesteps, rows, cols, channels),
            then `spatial_axes=(2, 3)`.

    # Returns
        A tuple or list, with the elements permuted according
        to `target_format`.

    # Example
    ```python
        >>> from keras.utils.generic_utils import transpose_shape
        >>> transpose_shape((16, 128, 128, 32),'channels_first', spatial_axes=(1, 2))
        (16, 32, 128, 128)
        >>> transpose_shape((16, 128, 128, 32), 'channels_last', spatial_axes=(1, 2))
        (16, 128, 128, 32)
        >>> transpose_shape((128, 128, 32), 'channels_first', spatial_axes=(0, 1))
        (32, 128, 128)
    ```

    # Raises
        ValueError: if `value` or the global `data_format` invalid.
    """
    if target_format == 'channels_first':
        new_values = shape[:spatial_axes[0]]
        new_values += (shape[-1],)
        new_values += tuple(shape[x] for x in spatial_axes)

        if isinstance(shape, list):
            return list(new_values)
        return new_values
    elif target_format == 'channels_last':
        return shape
    else:
        raise ValueError('The `data_format` argument must be one of '
                         '"channels_first", "channels_last". Received: ' +
                         str(target_format))


def check_for_unexpected_keys(name, input_dict, expected_values):
    unknown = set(input_dict.keys()).difference(expected_values)
    if unknown:
        raise ValueError('Unknown entries in {} dictionary: {}. Only expected '
                         'following keys: {}'.format(name, list(unknown),
                                                     expected_values))


def has_arg(fn, name, accept_all=False):
    """Checks if a callable accepts a given keyword argument.
    For Python 2, checks if there is an argument with the given name.
    For Python 3, checks if there is an argument with the given name, and
    also whether this argument can be called with a keyword (i.e. if it is
    not a positional-only argument).
    # Arguments
        fn: Callable to inspect.
        name: Check if `fn` can be called with `name` as a keyword argument.
        accept_all: What to return if there is no parameter called `name`
                    but the function accepts a `**kwargs` argument.
    # Returns
        bool, whether `fn` accepts a `name` keyword argument.
    """
    if sys.version_info < (3,):
        arg_spec = inspect.getargspec(fn)
        if accept_all and arg_spec.keywords is not None:
            return True
        return (name in arg_spec.args)
    elif sys.version_info < (3, 3):
        arg_spec = inspect.getfullargspec(fn)
        if accept_all and arg_spec.varkw is not None:
            return True
        return (name in arg_spec.args or
                name in arg_spec.kwonlyargs)
    else:
        signature = inspect.signature(fn)
        parameter = signature.parameters.get(name)
        if parameter is None:
            if accept_all:
                for param in signature.parameters.values():
                    if param.kind == inspect.Parameter.VAR_KEYWORD:
                        return True
            return False
        return (parameter.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                   inspect.Parameter.KEYWORD_ONLY))

from tensorflow.keras.utils import *

"""Utilities used in convolutional layers."""

import numpy as np


def normalize_tuple(value, n, name):
    """Transforms a single int or iterable of ints into an int tuple.

    # Arguments
        value: The value to validate and convert. Could be an int, or any iterable
          of ints.
        n: The size of the tuple to be returned.
        name: The name of the argument being validated, e.g. `strides` or
          `kernel_size`. This is only used to format error messages.

    # Returns
        A tuple of n integers.

    # Raises
        ValueError: If something else than an int/long or iterable thereof was
        passed.
    """
    if isinstance(value, int):
        return (value,) * n
    else:
        try:
            value_tuple = tuple(value)
        except TypeError:
            raise ValueError('The `{}` argument must be a tuple of {} '
                             'integers. Received: {}'.format(name, n, value))
        if len(value_tuple) != n:
            raise ValueError('The `{}` argument must be a tuple of {} '
                             'integers. Received: {}'.format(name, n, value))
        for single_value in value_tuple:
            try:
                int(single_value)
            except ValueError:
                raise ValueError('The `{}` argument must be a tuple of {} '
                                 'integers. Received: {} including element {} '
                                 'of type {}'.format(name, n, value, single_value,
                                                     type(single_value)))
    return value_tuple


def normalize_padding(value):
    padding = value.lower()
    allowed = {'valid', 'same', 'causal'}
    if padding not in allowed:
        raise ValueError('The `padding` argument must be one of "valid", "same" '
                         '(or "causal" for Conv1D). Received: {}'.format(padding))
    return padding


def convert_kernel(kernel):
    """Converts a Numpy kernel matrix from Theano format to TensorFlow format.

    Also works reciprocally, since the transformation is its own inverse.

    # Arguments
        kernel: Numpy array (3D, 4D or 5D).

    # Returns
        The converted kernel.

    # Raises
        ValueError: in case of invalid kernel shape or invalid data_format.
    """
    kernel = np.asarray(kernel)
    if not 3 <= kernel.ndim <= 5:
        raise ValueError('Invalid kernel shape:', kernel.shape)
    slices = [slice(None, None, -1) for _ in range(kernel.ndim)]
    no_flip = (slice(None, None), slice(None, None))
    slices[-2:] = no_flip
    return np.copy(kernel[tuple(slices)])


def conv_output_length(input_length, filter_size,
                       padding, stride, dilation=1):
    """Determines output length of a convolution given input length.

    # Arguments
        input_length: integer.
        filter_size: integer.
        padding: one of `"same"`, `"valid"`, `"full"`.
        stride: integer.
        dilation: dilation rate, integer.

    # Returns
        The output length (integer).
    """
    if input_length is None:
        return None
    assert padding in {'same', 'valid', 'full', 'causal'}
    dilated_filter_size = (filter_size - 1) * dilation + 1
    if padding == 'same':
        output_length = input_length
    elif padding == 'valid':
        output_length = input_length - dilated_filter_size + 1
    elif padding == 'causal':
        output_length = input_length
    elif padding == 'full':
        output_length = input_length + dilated_filter_size - 1
    return (output_length + stride - 1) // stride


def conv_input_length(output_length, filter_size, padding, stride):
    """Determines input length of a convolution given output length.

    # Arguments
        output_length: integer.
        filter_size: integer.
        padding: one of `"same"`, `"valid"`, `"full"`.
        stride: integer.

    # Returns
        The input length (integer).
    """
    if output_length is None:
        return None
    assert padding in {'same', 'valid', 'full'}
    if padding == 'same':
        pad = filter_size // 2
    elif padding == 'valid':
        pad = 0
    elif padding == 'full':
        pad = filter_size - 1
    return (output_length - 1) * stride - 2 * pad + filter_size


def deconv_length(dim_size, stride_size, kernel_size, padding,
                  output_padding, dilation=1):
    """Determines output length of a transposed convolution given input length.

    # Arguments
        dim_size: Integer, the input length.
        stride_size: Integer, the stride along the dimension of `dim_size`.
        kernel_size: Integer, the kernel size along the dimension of
            `dim_size`.
        padding: One of `"same"`, `"valid"`, `"full"`.
        output_padding: Integer, amount of padding along the output dimension,
            Can be set to `None` in which case the output length is inferred.
        dilation: dilation rate, integer.

    # Returns
        The output length (integer).
    """
    assert padding in {'same', 'valid', 'full'}
    if dim_size is None:
        return None

    # Get the dilated kernel size
    kernel_size = (kernel_size - 1) * dilation + 1

    # Infer length if output padding is None, else compute the exact length
    if output_padding is None:
        if padding == 'valid':
            dim_size = dim_size * stride_size + max(kernel_size - stride_size, 0)
        elif padding == 'full':
            dim_size = dim_size * stride_size - (stride_size + kernel_size - 2)
        elif padding == 'same':
            dim_size = dim_size * stride_size
    else:
        if padding == 'same':
            pad = kernel_size // 2
        elif padding == 'valid':
            pad = 0
        elif padding == 'full':
            pad = kernel_size - 1

        dim_size = ((dim_size - 1) * stride_size + kernel_size - 2 * pad +
                    output_padding)

    return dim_size

"""Utilities for file download and caching."""

from tensorflow.keras.utils import get_file

from tensorflow.keras.utils import Sequence
from tensorflow.keras.utils import SequenceEnqueuer
from tensorflow.keras.utils import OrderedEnqueuer
from tensorflow.keras.utils import GeneratorEnqueuer

"""Utilities related to disk I/O."""

from tensorflow.keras.utils import HDF5Matrix

"""Multi-GPU training utilities."""

from tensorflow.keras.utils import multi_gpu_model

"""Utilities related to model visualization."""

from tensorflow.keras.utils import model_to_dot
from tensorflow.keras.utils import plot_model

"""Numpy-related utilities."""

from tensorflow.keras.utils import to_categorical
from tensorflow.keras.utils import normalize

from tensorflow.keras.optimizers import *

from tensorflow.keras.optimizers.schedules import *

from tensorflow.keras.applications.inception_resnet_v2 import InceptionResNetV2
from tensorflow.keras.applications.inception_resnet_v2 import decode_predictions
from tensorflow.keras.applications.inception_resnet_v2 import preprocess_input

"""Utilities for ImageNet data preprocessing & prediction decoding."""
from tensorflow.keras.applications.imagenet_utils import decode_predictions
from tensorflow.keras.applications.imagenet_utils import preprocess_input

from tensorflow.keras.applications.densenet import DenseNet121
from tensorflow.keras.applications.densenet import DenseNet169
from tensorflow.keras.applications.densenet import DenseNet201
from tensorflow.keras.applications.densenet import decode_predictions
from tensorflow.keras.applications.densenet import preprocess_input

from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import decode_predictions
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

from .vgg16 import VGG16
from .vgg19 import VGG19
from .resnet50 import ResNet50
from .inception_v3 import InceptionV3
from .inception_resnet_v2 import InceptionResNetV2
from .xception import Xception
from .mobilenet import MobileNet
from .mobilenet_v2 import MobileNetV2
from .densenet import DenseNet121, DenseNet169, DenseNet201
from .nasnet import NASNetMobile, NASNetLarge
from .resnet import ResNet101, ResNet152
from .resnet_v2 import ResNet50V2, ResNet101V2, ResNet152V2

from tensorflow.keras.applications.mobilenet import MobileNet
from tensorflow.keras.applications.mobilenet import decode_predictions
from tensorflow.keras.applications.mobilenet import preprocess_input

from tensorflow.keras.applications.inception_v3 import InceptionV3
from tensorflow.keras.applications.inception_v3 import decode_predictions
from tensorflow.keras.applications.inception_v3 import preprocess_input

from tensorflow.keras.applications.resnet import ResNet50
from tensorflow.keras.applications.resnet import ResNet101
from tensorflow.keras.applications.resnet import ResNet152
from tensorflow.keras.applications.resnet import decode_predictions
from tensorflow.keras.applications.resnet import preprocess_input

from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.applications.vgg16 import decode_predictions
from tensorflow.keras.applications.vgg16 import preprocess_input

from tensorflow.keras.applications.vgg19 import VGG19
from tensorflow.keras.applications.vgg19 import decode_predictions
from tensorflow.keras.applications.vgg19 import preprocess_input

from tensorflow.keras.applications.xception import Xception
from tensorflow.keras.applications.xception import decode_predictions
from tensorflow.keras.applications.xception import preprocess_input

from tensorflow.keras.applications.nasnet import NASNetMobile
from tensorflow.keras.applications.nasnet import NASNetLarge
from tensorflow.keras.applications.nasnet import decode_predictions
from tensorflow.keras.applications.nasnet import preprocess_input

from tensorflow.keras.applications.resnet_v2 import ResNet50V2
from tensorflow.keras.applications.resnet_v2 import ResNet101V2
from tensorflow.keras.applications.resnet_v2 import ResNet152V2
from tensorflow.keras.applications.resnet_v2 import decode_predictions
from tensorflow.keras.applications.resnet_v2 import preprocess_input

from tensorflow.keras.applications.resnet import ResNet50
from tensorflow.keras.applications.resnet import decode_predictions
from tensorflow.keras.applications.resnet import preprocess_input

"""Utilities for preprocessing sequence data."""

from tensorflow.keras.preprocessing.sequence import *

from tensorflow.keras.preprocessing import *

"""Utilities for text input preprocessing."""

from tensorflow.keras.preprocessing.text import *
"""Utilities for real-time data augmentation on image data."""

from tensorflow.keras.preprocessing.image import *

"""Contains the base Layer class, from which all layers inherit."""
from tensorflow.keras.layers import Layer
from tensorflow.keras.layers import InputSpec

"""Model saving utilities."""
from tensorflow.keras.models import save_model
from tensorflow.keras.models import load_model
from tensorflow.keras.models import model_from_config
from tensorflow.keras.models import model_from_yaml
from tensorflow.keras.models import model_from_json

# note: `Node` is an internal class,
# it isn't meant to be used by Keras users.
from .input_layer import Input
from .input_layer import InputLayer
from .base_layer import InputSpec
from .base_layer import Layer
from .network import get_source_inputs
from .training import Model

"""Input layer code (`Input` and `InputLayer`)."""
from tensorflow.keras.layers import InputLayer
from tensorflow.keras import Input


"""Sequential model class."""
from tensorflow.keras import Sequential

"""A `Network` is way to compose layers: the topological form of a `Model`."""

from tensorflow.keras import Model as Network
from tensorflow.keras.utils import get_source_inputs

"""This module is deprecated, but kept around for backwards compatibility.
"""
from .base_layer import Layer, InputSpec
from .input_layer import Input, InputLayer
from .network import Network, get_source_inputs

"""Training-related part of the Keras engine."""
from tensorflow.keras import Model

import pytest
from keras import backend as K


@pytest.fixture(autouse=True)
def clear_session_after_test():
    """Test wrapper to clean up after TensorFlow and CNTK tests.

    This wrapper runs for all the tests in the keras test suite.
    """
    yield
    if K.backend() == 'tensorflow' or K.backend() == 'cntk':
        K.clear_session()

import pytest
import numpy as np
from numpy.testing import assert_allclose
from flaky import flaky

import keras
from keras import metrics
from keras import backend as K

all_metrics = [
    metrics.binary_accuracy,
    metrics.categorical_accuracy,
    metrics.mean_squared_error,
    metrics.mean_absolute_error,
    metrics.mean_absolute_percentage_error,
    metrics.mean_squared_logarithmic_error,
    metrics.squared_hinge,
    metrics.hinge,
    metrics.categorical_crossentropy,
    metrics.binary_crossentropy,
    metrics.poisson,
]

all_sparse_metrics = [
    metrics.sparse_categorical_accuracy,
    metrics.sparse_categorical_crossentropy,
]


@pytest.mark.parametrize('metric', all_metrics)
def test_metrics(metric):
    y_a = K.variable(np.random.random((6, 7)))
    y_b = K.variable(np.random.random((6, 7)))
    output = metric(y_a, y_b)
    assert K.eval(output).shape == (6,)


@pytest.mark.parametrize('metric', all_sparse_metrics)
def test_sparse_metrics(metric):
    y_a = K.variable(np.random.randint(0, 7, (6,)), dtype=K.floatx())
    y_b = K.variable(np.random.random((6, 7)), dtype=K.floatx())
    assert K.eval(metric(y_a, y_b)).shape == (6,)


@pytest.mark.parametrize('shape', [(6,), (6, 3), (6, 3, 1)])
def test_sparse_categorical_accuracy_correctness(shape):
    y_a = K.variable(np.random.randint(0, 7, shape), dtype=K.floatx())
    y_b_shape = shape + (7,)
    y_b = K.variable(np.random.random(y_b_shape), dtype=K.floatx())
    # use one_hot embedding to convert sparse labels to equivalent dense labels
    y_a_dense_labels = K.cast(K.one_hot(K.cast(y_a, dtype='int32'), 7),
                              dtype=K.floatx())
    sparse_categorical_acc = metrics.sparse_categorical_accuracy(y_a, y_b)
    categorical_acc = metrics.categorical_accuracy(y_a_dense_labels, y_b)
    assert np.allclose(K.eval(sparse_categorical_acc), K.eval(categorical_acc))


def test_serialize():
    '''This is a mock 'round trip' of serialize and deserialize.
    '''

    class MockMetric:
        def __init__(self):
            self.__name__ = "mock_metric"

    mock = MockMetric()
    found = metrics.serialize(mock)
    assert found == "mock_metric"

    found = metrics.deserialize('mock_metric',
                                custom_objects={'mock_metric': True})
    assert found is True


def test_invalid_get():

    with pytest.raises(ValueError):
        metrics.get(5)


@pytest.mark.skipif((K.backend() == 'cntk'),
                    reason='CNTK backend does not support top_k yet')
def test_top_k_categorical_accuracy():
    y_pred = K.variable(np.array([[0.3, 0.2, 0.1], [0.1, 0.2, 0.7]]))
    y_true = K.variable(np.array([[0, 1, 0], [1, 0, 0]]))
    success_result = K.eval(metrics.top_k_categorical_accuracy(y_true, y_pred,
                                                               k=3))
    assert np.mean(success_result) == 1
    partial_result = K.eval(metrics.top_k_categorical_accuracy(y_true, y_pred,
                                                               k=2))
    assert np.mean(partial_result) == 0.5
    failure_result = K.eval(metrics.top_k_categorical_accuracy(y_true, y_pred,
                                                               k=1))
    assert np.mean(failure_result) == 0


@pytest.mark.skipif((K.backend() == 'cntk'),
                    reason='CNTK backend does not support top_k yet')
@pytest.mark.parametrize('y_pred, y_true', [
    # Test correctness if the shape of y_true is (num_samples, 1)
    (np.array([[0.3, 0.2, 0.1], [0.1, 0.2, 0.7]]), np.array([[1], [0]])),
    # Test correctness if the shape of y_true is (num_samples,)
    (np.array([[0.3, 0.2, 0.1], [0.1, 0.2, 0.7]]), np.array([1, 0])),
])
def test_sparse_top_k_categorical_accuracy(y_pred, y_true):
    y_pred = K.variable(y_pred)
    y_true = K.variable(y_true)
    success_result = K.eval(
        metrics.sparse_top_k_categorical_accuracy(y_true, y_pred, k=3))

    assert np.mean(success_result) == 1
    partial_result = K.eval(
        metrics.sparse_top_k_categorical_accuracy(y_true, y_pred, k=2))

    assert np.mean(partial_result) == 0.5
    failure_result = K.eval(
        metrics.sparse_top_k_categorical_accuracy(y_true, y_pred, k=1))

    assert np.mean(failure_result) == 0


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import numpy as np
from numpy.testing import assert_allclose

from keras import backend as K
from keras import activations

from keras.layers.core import Dense


def get_standard_values():
    """A set of floats used for testing the activations.
    """
    return np.array([[0, 0.1, 0.5, 0.9, 1.0]], dtype=K.floatx())


def test_serialization():
    all_activations = ['softmax', 'relu', 'elu', 'tanh',
                       'sigmoid', 'hard_sigmoid', 'linear',
                       'softplus', 'softsign', 'selu']
    for name in all_activations:
        fn = activations.get(name)
        ref_fn = getattr(activations, name)
        assert fn == ref_fn
        config = activations.serialize(fn)
        fn = activations.deserialize(config)
        assert fn == ref_fn


def test_get_fn():
    """Activations has a convenience "get" function. All paths of this
    function are tested here, although the behaviour in some instances
    seems potentially surprising (e.g. situation 3)
    """

    # 1. Default returns linear
    a = activations.get(None)
    assert a == activations.linear

    # # 2. Passing in a layer raises a warning
    # layer = Dense(32)
    # with pytest.warns(UserWarning):
    #     a = activations.get(layer)

    # 3. Callables return themselves
    a = activations.get(lambda x: 5)
    assert a(None) == 5

    # 4. Anything else is not a valid argument
    with pytest.raises(TypeError):
        a = activations.get(6)


def test_softmax_valid():
    """Test using a reference implementation of softmax.
    """
    def softmax(values):
        m = np.max(values)
        e = np.exp(values - m)
        return e / np.sum(e)

    x = K.placeholder(ndim=2)
    f = K.function([x], [activations.softmax(x)])
    test_values = get_standard_values()

    result = f([test_values])[0]
    expected = softmax(test_values)
    assert_allclose(result, expected, rtol=1e-05)


def test_softmax_invalid():
    """Test for the expected exception behaviour on invalid input
    """

    x = K.placeholder(ndim=1)

    # One dimensional arrays are supposed to raise a value error
    with pytest.raises(ValueError):
        f = K.function([x], [activations.softmax(x)])


def test_softmax_3d():
    """Test using a reference implementation of softmax.
    """
    def softmax(values, axis):
        m = np.max(values, axis=axis, keepdims=True)
        e = np.exp(values - m)
        return e / np.sum(e, axis=axis, keepdims=True)

    x = K.placeholder(ndim=3)
    f = K.function([x], [activations.softmax(x, axis=1)])
    test_values = get_standard_values()[:, :, np.newaxis].copy()

    result = f([test_values])[0]
    expected = softmax(test_values, axis=1)
    assert_allclose(result, expected, rtol=1e-05)


def test_time_distributed_softmax():
    x = K.placeholder(shape=(1, 1, 5))
    f = K.function([x], [activations.softmax(x)])
    test_values = get_standard_values()
    test_values = np.reshape(test_values, (1, 1, np.size(test_values)))
    f([test_values])[0]


def test_softplus():
    """Test using a reference softplus implementation.
    """
    def softplus(x):
        return np.log(np.ones_like(x) + np.exp(x))

    x = K.placeholder(ndim=2)
    f = K.function([x], [activations.softplus(x)])
    test_values = get_standard_values()

    result = f([test_values])[0]
    expected = softplus(test_values)
    assert_allclose(result, expected, rtol=1e-05)


def test_softsign():
    """Test using a reference softsign implementation.
    """
    def softsign(x):
        return np.divide(x, np.ones_like(x) + np.absolute(x))

    x = K.placeholder(ndim=2)
    f = K.function([x], [activations.softsign(x)])
    test_values = get_standard_values()

    result = f([test_values])[0]
    expected = softsign(test_values)
    assert_allclose(result, expected, rtol=1e-05)


def test_sigmoid():
    """Test using a numerically stable reference sigmoid implementation.
    """
    def ref_sigmoid(x):
        if x >= 0:
            return 1 / (1 + np.exp(-x))
        else:
            z = np.exp(x)
            return z / (1 + z)
    sigmoid = np.vectorize(ref_sigmoid)

    x = K.placeholder(ndim=2)
    f = K.function([x], [activations.sigmoid(x)])
    test_values = get_standard_values()

    result = f([test_values])[0]
    expected = sigmoid(test_values)
    assert_allclose(result, expected, rtol=1e-05)


def test_hard_sigmoid():
    """Test using a reference hard sigmoid implementation.
    """
    def ref_hard_sigmoid(x):
        x = (x * 0.2) + 0.5
        z = 0.0 if x <= 0 else (1.0 if x >= 1 else x)
        return z
    hard_sigmoid = np.vectorize(ref_hard_sigmoid)

    x = K.placeholder(ndim=2)
    f = K.function([x], [activations.hard_sigmoid(x)])
    test_values = get_standard_values()

    result = f([test_values])[0]
    expected = hard_sigmoid(test_values)
    assert_allclose(result, expected, rtol=1e-05)


def test_relu():
    x = K.placeholder(ndim=2)
    f = K.function([x], [activations.relu(x)])

    test_values = get_standard_values()
    result = f([test_values])[0]
    assert_allclose(result, test_values, rtol=1e-05)

    # Test max_value
    test_values = np.array([[0.5, 1.5]], dtype=K.floatx())
    f = K.function([x], [activations.relu(x, max_value=1.)])
    result = f([test_values])[0]
    assert np.max(result) <= 1.

    # Test max_value == 6.
    test_values = np.array([[0.5, 6.]], dtype=K.floatx())
    f = K.function([x], [activations.relu(x, max_value=1.)])
    result = f([test_values])[0]
    assert np.max(result) <= 6.


def test_elu():
    x = K.placeholder(ndim=2)
    f = K.function([x], [activations.elu(x, 0.5)])

    test_values = get_standard_values()
    result = f([test_values])[0]
    assert_allclose(result, test_values, rtol=1e-05)

    negative_values = np.array([[-1, -2]], dtype=K.floatx())
    result = f([negative_values])[0]
    true_result = (np.exp(negative_values) - 1) / 2

    assert_allclose(result, true_result)


def test_selu():
    x = K.placeholder(ndim=2)
    f = K.function([x], [activations.selu(x)])
    alpha = 1.6732632423543772848170429916717
    scale = 1.0507009873554804934193349852946

    positive_values = get_standard_values()
    result = f([positive_values])[0]
    assert_allclose(result, positive_values * scale, rtol=1e-05)

    negative_values = np.array([[-1, -2]], dtype=K.floatx())

    result = f([negative_values])[0]
    true_result = (np.exp(negative_values) - 1) * scale * alpha

    assert_allclose(result, true_result)


def test_tanh():
    test_values = get_standard_values()

    x = K.placeholder(ndim=2)
    exp = activations.tanh(x)
    f = K.function([x], [exp])

    result = f([test_values])[0]
    expected = np.tanh(test_values)
    assert_allclose(result, expected, rtol=1e-05)


def test_linear():
    xs = [1, 5, True, None]
    for x in xs:
        assert(x == activations.linear(x))


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import numpy as np
from numpy.testing import assert_allclose

from keras import backend as K
from keras import constraints


def get_test_values():
    return [0.1, 0.5, 3, 8, 1e-7]


def get_example_array():
    np.random.seed(3537)
    example_array = np.random.random((100, 100)) * 100. - 50.
    example_array[0, 0] = 0.  # 0 could possibly cause trouble
    return example_array


def test_serialization():
    all_activations = ['max_norm', 'non_neg',
                       'unit_norm', 'min_max_norm']
    for name in all_activations:
        fn = constraints.get(name)
        ref_fn = getattr(constraints, name)()
        assert fn.__class__ == ref_fn.__class__
        config = constraints.serialize(fn)
        fn = constraints.deserialize(config)
        assert fn.__class__ == ref_fn.__class__


def test_max_norm():
    array = get_example_array()
    for m in get_test_values():
        norm_instance = constraints.max_norm(m)
        normed = norm_instance(K.variable(array))
        assert(np.all(K.eval(normed) < m))

    # a more explicit example
    norm_instance = constraints.max_norm(2.0)
    x = np.array([[0, 0, 0], [1.0, 0, 0], [3, 0, 0], [3, 3, 3]]).T
    x_normed_target = np.array([[0, 0, 0], [1.0, 0, 0],
                                [2.0, 0, 0],
                                [2. / np.sqrt(3),
                                 2. / np.sqrt(3),
                                 2. / np.sqrt(3)]]).T
    x_normed_actual = K.eval(norm_instance(K.variable(x)))
    assert_allclose(x_normed_actual, x_normed_target, rtol=1e-05)


def test_non_neg():
    non_neg_instance = constraints.non_neg()
    normed = non_neg_instance(K.variable(get_example_array()))
    assert(np.all(np.min(K.eval(normed), axis=1) == 0.))


def test_unit_norm():
    unit_norm_instance = constraints.unit_norm()
    normalized = unit_norm_instance(K.variable(get_example_array()))
    norm_of_normalized = np.sqrt(np.sum(K.eval(normalized) ** 2, axis=0))
    # In the unit norm constraint, it should be equal to 1.
    difference = norm_of_normalized - 1.
    largest_difference = np.max(np.abs(difference))
    assert(np.abs(largest_difference) < 10e-5)


def test_min_max_norm():
    array = get_example_array()
    for m in get_test_values():
        norm_instance = constraints.min_max_norm(min_value=m, max_value=m * 2)
        normed = norm_instance(K.variable(array))
        value = K.eval(normed)
        l2 = np.sqrt(np.sum(np.square(value), axis=0))
        assert l2[l2 < m].size == 0
        assert l2[l2 > m * 2 + 1e-5].size == 0


if __name__ == '__main__':
    pytest.main([__file__])

"""Tests for metric objects training and evaluation."""
import pytest
import numpy as np

from keras import metrics
from keras import backend as K
from keras.layers import Dense
from keras.models import Sequential


if K.backend() == 'cntk':
    pytestmark = pytest.mark.skip


METRICS = [
    metrics.Accuracy,
    metrics.MeanSquaredError,
    metrics.Hinge,
    metrics.CategoricalHinge,
    metrics.SquaredHinge,
    metrics.FalsePositives,
    metrics.TruePositives,
    metrics.FalseNegatives,
    metrics.TrueNegatives,
    metrics.BinaryAccuracy,
    metrics.CategoricalAccuracy,
    metrics.TopKCategoricalAccuracy,
    metrics.LogCoshError,
    metrics.Poisson,
    metrics.KLDivergence,
    metrics.CosineSimilarity,
    metrics.MeanAbsoluteError,
    metrics.MeanAbsolutePercentageError,
    metrics.MeanSquaredError,
    metrics.MeanSquaredLogarithmicError,
    metrics.RootMeanSquaredError,
    metrics.BinaryCrossentropy,
    metrics.CategoricalCrossentropy,
    metrics.Precision,
    metrics.Recall,
    metrics.AUC,
]
SPARSE_METRICS = [
    metrics.SparseCategoricalAccuracy,
    metrics.SparseTopKCategoricalAccuracy,
    metrics.SparseCategoricalCrossentropy
]


@pytest.mark.parametrize('metric_cls', METRICS)
def test_training_and_eval(metric_cls):
    model = Sequential([Dense(2, activation='sigmoid', input_shape=(3,))])
    model.compile('rmsprop', 'mse', metrics=[metric_cls()])
    x = np.random.uniform(0, 1, size=(10, 3))
    y = np.random.uniform(0, 1, size=(10, 2))
    model.fit(x, y)
    model.evaluate(x, y)


@pytest.mark.parametrize('metric_cls', SPARSE_METRICS)
def test_sparse_metrics(metric_cls):
    model = Sequential([Dense(1, input_shape=(3,))])
    model.compile('rmsprop', 'mse', metrics=[metric_cls()])
    x = np.random.uniform(0, 1, size=(10, 3))
    y = np.random.uniform(0, 1, size=(10,))
    model.fit(x, y)
    model.evaluate(x, y)


def test_sensitivity_metrics():
    metrics_list = [
        metrics.SensitivityAtSpecificity(0.5),
        metrics.SpecificityAtSensitivity(0.5),
    ]
    model = Sequential([Dense(2, activation='sigmoid', input_shape=(3,))])
    model.compile('rmsprop', 'mse', metrics=metrics_list)
    x = np.random.uniform(0, 1, size=(10, 3))
    y = np.random.uniform(0, 1, size=(10, 2))
    model.fit(x, y)
    model.evaluate(x, y)


@pytest.mark.skipif(True, reason='It is a flaky test, see #13477 for more context.')
def test_mean_iou():
    import tensorflow as tf
    if not tf.__version__.startswith('2.'):
        return

    model = Sequential([Dense(1, activation='sigmoid', input_shape=(3,))])
    model.compile('rmsprop', 'mse', metrics=[metrics.MeanIoU(2)])
    x = np.random.uniform(0, 1, size=(10, 3))
    y = np.random.uniform(0, 1, size=(10,))
    model.fit(x, y)
    model.evaluate(x, y)

from __future__ import print_function
import pytest
import numpy as np
from numpy.testing import assert_allclose

from keras.utils import test_utils
from keras import optimizers, Input
from keras.models import Sequential, Model, load_model
from keras.layers.core import Dense, Activation, Lambda
from keras.utils.np_utils import to_categorical
from keras import backend as K
import tempfile


num_classes = 2


def get_test_data():
    np.random.seed(1337)
    (x_train, y_train), _ = test_utils.get_test_data(num_train=1000,
                                                     num_test=200,
                                                     input_shape=(10,),
                                                     classification=True,
                                                     num_classes=num_classes)
    y_train = to_categorical(y_train)
    return x_train, y_train


def _test_optimizer(optimizer, target=0.6):
    x_train, y_train = get_test_data()

    model = Sequential()
    model.add(Dense(10, input_shape=(x_train.shape[1],)))
    model.add(Activation('relu'))
    model.add(Dense(y_train.shape[1]))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy',
                  optimizer=optimizer,
                  metrics=['accuracy'])

    history = model.fit(x_train, y_train, epochs=3, batch_size=16, verbose=0)
    assert history.history['accuracy'][-1] >= target
    config = optimizers.serialize(optimizer)
    optim = optimizers.deserialize(config)
    new_config = optimizers.serialize(optim)
    new_config['class_name'] = new_config['class_name'].lower()
    assert sorted(config.keys()) == sorted(new_config.keys())
    # for k in config['config'].keys():
    #     assert config['config'][k] == new_config['config'][k]

    # Test constraints.
    model = Sequential()
    dense = Dense(10,
                  input_shape=(x_train.shape[1],),
                  kernel_constraint=lambda x: 0. * x + 1.,
                  bias_constraint=lambda x: 0. * x + 2.,)
    model.add(dense)
    model.add(Activation('relu'))
    model.add(Dense(y_train.shape[1]))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy',
                  optimizer=optimizer,
                  metrics=['accuracy'])
    model.train_on_batch(x_train[:10], y_train[:10])
    kernel, bias = dense.get_weights()
    assert_allclose(kernel, 1.)
    assert_allclose(bias, 2.)

    # Test saving.
    model = Sequential()
    model.add(Dense(1, input_dim=1))
    model.compile(loss='mse', optimizer=optimizer)
    model.fit(np.zeros((1, 1)), np.zeros((1, 1)))

    _, fname = tempfile.mkstemp('.h5')
    model.save(fname)
    model2 = load_model(fname)

    for w1, w2 in zip(model.get_weights(), model2.get_weights()):
        assert_allclose(w1, w2)


@pytest.mark.skipif((K.backend() != 'tensorflow'),
                    reason='Only Tensorflow raises a '
                           'ValueError if the gradient is null.')
def test_no_grad():
    inp = Input([3])
    x = Dense(10)(inp)
    x = Lambda(
        lambda l: 1.0 * K.reshape(K.cast(K.argmax(l), 'float32'), [-1, 1]),
        output_shape=lambda x: [x[0], 1])(x)
    mod = Model(inp, x)
    mod.compile('sgd', 'mse')
    with pytest.raises(ValueError):
        mod.fit(np.zeros([10, 3]), np.zeros([10, 1], np.float32),
                batch_size=10, epochs=10)


@pytest.mark.skipif((K.backend() == 'cntk'),
                    reason='Flaky with CNTK')
def test_sgd():
    sgd = optimizers.SGD(lr=0.01, momentum=0.9, nesterov=True)
    _test_optimizer(sgd)


def test_rmsprop():
    _test_optimizer(optimizers.RMSprop())
    _test_optimizer(optimizers.RMSprop(decay=1e-3))


def test_adagrad():
    _test_optimizer(optimizers.Adagrad(lr=1.))
    _test_optimizer(optimizers.Adagrad(lr=1., decay=1e-3))


def test_adadelta():
    _test_optimizer(optimizers.Adadelta(lr=1.), target=0.4)
    _test_optimizer(optimizers.Adadelta(lr=1., decay=1e-3), target=0.4)


def test_adam():
    _test_optimizer(optimizers.Adam())
    _test_optimizer(optimizers.Adam(decay=1e-3))


def test_adamax():
    _test_optimizer(optimizers.Adamax(lr=1.))
    _test_optimizer(optimizers.Adamax(lr=1., decay=1e-3))


def test_nadam():
    _test_optimizer(optimizers.Nadam())


def test_adam_amsgrad():
    _test_optimizer(optimizers.Adam(amsgrad=True))
    _test_optimizer(optimizers.Adam(amsgrad=True, decay=1e-3))


@pytest.mark.skipif((K.backend() == 'cntk'),
                    reason='Flaky with CNTK')
def test_clipnorm():
    sgd = optimizers.SGD(lr=0.01, momentum=0.9, clipnorm=0.5)
    _test_optimizer(sgd)


@pytest.mark.skipif((K.backend() == 'cntk'),
                    reason='Flaky with CNTK')
def test_clipvalue():
    sgd = optimizers.SGD(lr=0.01, momentum=0.9, clipvalue=0.5)
    _test_optimizer(sgd)


@pytest.mark.skipif((K.backend() != 'tensorflow'),
                    reason='Requires TensorFlow backend')
def test_tfoptimizer():
    from keras import constraints
    import tensorflow as tf
    if tf.__version__.startswith('1.'):
        optimizer = optimizers.TFOptimizer(tf.train.AdamOptimizer())
    else:
        optimizer = tf.keras.optimizers.Adam()

    model = Sequential()
    model.add(Dense(num_classes, input_shape=(3,),
                    kernel_constraint=constraints.MaxNorm(1)))
    model.compile(loss='mean_squared_error', optimizer=optimizer)
    model.fit(np.random.random((5, 3)), np.random.random((5, num_classes)),
              epochs=1, batch_size=5, verbose=0)

    if tf.__version__.startswith('1.'):
        with pytest.raises(NotImplementedError):
            optimizer.weights
        with pytest.raises(NotImplementedError):
            optimizer.get_config()
        with pytest.raises(NotImplementedError):
            optimizer.from_config(None)


if __name__ == '__main__':
    pytest.main([__file__])

import pytest

from keras.models import Sequential, Model
from keras.layers import Dense, Input, Average
from keras.utils import np_utils
from keras.utils import test_utils
from keras import regularizers
from keras import backend as K

data_dim = 5
num_classes = 2
batch_size = 10


def get_data():
    (x_train, y_train), _ = test_utils.get_test_data(
        num_train=batch_size,
        num_test=batch_size,
        input_shape=(data_dim,),
        classification=True,
        num_classes=num_classes)
    y_train = np_utils.to_categorical(y_train, num_classes)

    return x_train, y_train


def create_model(kernel_regularizer=None, activity_regularizer=None):
    model = Sequential()
    model.add(Dense(num_classes,
                    kernel_regularizer=kernel_regularizer,
                    activity_regularizer=activity_regularizer,
                    input_shape=(data_dim,)))
    return model


def create_multi_input_model_from(layer1, layer2):
    input_1 = Input(shape=(data_dim,))
    input_2 = Input(shape=(data_dim,))
    out1 = layer1(input_1)
    out2 = layer2(input_2)
    out = Average()([out1, out2])
    model = Model([input_1, input_2], out)
    model.add_loss(K.mean(out2))
    model.add_loss(lambda: 1)
    model.add_loss(lambda: 1)
    return model


def test_kernel_regularization():
    x_train, y_train = get_data()
    for reg in [regularizers.l1(),
                regularizers.l2(),
                regularizers.l1_l2()]:
        model = create_model(kernel_regularizer=reg)
        model.compile(loss='categorical_crossentropy', optimizer='sgd')
        assert len(model.losses) == 1
        model.train_on_batch(x_train, y_train)


def test_activity_regularization():
    x_train, y_train = get_data()
    for reg in [regularizers.l1(), regularizers.l2()]:
        model = create_model(activity_regularizer=reg)
        model.compile(loss='categorical_crossentropy', optimizer='sgd')
        assert len(model.losses) == 1
        model.train_on_batch(x_train, y_train)


def test_regularization_shared_layer():
    dense_layer = Dense(num_classes,
                        kernel_regularizer=regularizers.l1(),
                        activity_regularizer=regularizers.l1())

    model = create_multi_input_model_from(dense_layer, dense_layer)
    model.compile(loss='categorical_crossentropy', optimizer='sgd')
    assert len(model.losses) == 6


def test_regularization_shared_model():
    dense_layer = Dense(num_classes,
                        kernel_regularizer=regularizers.l1(),
                        activity_regularizer=regularizers.l1())

    input_tensor = Input(shape=(data_dim,))
    dummy_model = Model(input_tensor, dense_layer(input_tensor))

    model = create_multi_input_model_from(dummy_model, dummy_model)
    model.compile(loss='categorical_crossentropy', optimizer='sgd')
    # assert len(model.losses) == 6


def test_regularization_shared_layer_in_different_models():
    shared_dense = Dense(num_classes,
                         kernel_regularizer=regularizers.l1(),
                         activity_regularizer=regularizers.l1())
    models = []
    for _ in range(2):
        input_tensor = Input(shape=(data_dim,))
        unshared_dense = Dense(num_classes, kernel_regularizer=regularizers.l1())
        out = unshared_dense(shared_dense(input_tensor))
        models.append(Model(input_tensor, out))

    model = create_multi_input_model_from(*models)
    model.compile(loss='categorical_crossentropy', optimizer='sgd')
    # assert len(model.losses) == 8


if __name__ == '__main__':
    pytest.main([__file__])

"""Tests for Keras metrics classes."""
import pytest
import numpy as np
import math

from keras import metrics
from keras import backend as K


if K.backend() != 'tensorflow':
    # Need TensorFlow to use metric.__call__
    pytestmark = pytest.mark.skip


class TestSum(object):

    def test_sum(self):
        m = metrics.Sum(name='my_sum', dtype='float32')

        # check config
        assert m.name == 'my_sum'
        assert m.stateful
        assert m.dtype == 'float32'
        assert len(m.weights) == 1

        # check initial state
        assert K.eval(m.total) == 0

        # check __call__
        assert K.eval(m(100.0)) == 100
        assert K.eval(m.total) == 100

        # check update_state() and result() + state accumulation + tensor input
        result = m([1, 5])
        assert np.isclose(K.eval(result), 106)
        assert K.eval(m.total) == 106  # 100 + 1 + 5

        # check reset_states()
        m.reset_states()
        assert K.eval(m.total) == 0

    def test_sum_with_sample_weight(self):
        m = metrics.Sum(dtype='float64')
        assert m.dtype == 'float64'

        # check scalar weight
        result_t = m(100, sample_weight=0.5)
        assert K.eval(result_t) == 50
        assert K.eval(m.total) == 50

        # check weights not scalar and weights rank matches values rank
        result_t = m([1, 5], sample_weight=[1, 0.2])
        result = K.eval(result_t)
        assert np.isclose(result, 52.)  # 50 + 1 + 5 * 0.2
        assert np.isclose(K.eval(m.total), 52.)

        # check weights broadcast
        result_t = m([1, 2], sample_weight=0.5)
        assert np.isclose(K.eval(result_t), 53.5)  # 52 + 0.5 + 1
        assert np.isclose(K.eval(m.total), 53.5)

        # check weights squeeze
        result_t = m([1, 5], sample_weight=[[1], [0.2]])
        assert np.isclose(K.eval(result_t), 55.5)  # 53.5 + 1 + 1
        assert np.isclose(K.eval(m.total), 55.5)

        # check weights expand
        result_t = m([[1], [5]], sample_weight=[1, 0.2])
        assert np.isclose(K.eval(result_t), 57.5, 2)  # 55.5 + 1 + 1
        assert np.isclose(K.eval(m.total), 57.5, 1)

        # check values reduced to the dimensions of weight
        result_t = m([[[1., 2.], [3., 2.], [0.5, 4.]]], sample_weight=[0.5])
        result = np.round(K.eval(result_t), decimals=2)
        # result = (prev: 57.5) + 0.5 + 1 + 1.5 + 1 + 0.25 + 2
        assert np.isclose(result, 63.75, 2)
        assert np.isclose(K.eval(m.total), 63.75, 2)


class TestMean(object):

    def test_mean(self):
        m = metrics.Mean(name='my_mean')

        # check config
        assert m.name == 'my_mean'
        assert m.stateful
        assert m.dtype == 'float32'
        assert len(m.weights) == 2

        # check initial state
        assert K.eval(m.total) == 0
        assert K.eval(m.count) == 0

        # check __call__()
        assert K.eval(m(100)) == 100
        assert K.eval(m.total) == 100
        assert K.eval(m.count) == 1

        # check update_state() and result()
        result = m([1, 5])
        assert np.isclose(K.eval(result), 106. / 3)
        assert K.eval(m.total) == 106  # 100 + 1 + 5
        assert K.eval(m.count) == 3

        # check reset_states()
        m.reset_states()
        assert K.eval(m.total) == 0
        assert K.eval(m.count) == 0

        # Check save and restore config
        m2 = metrics.Mean.from_config(m.get_config())
        assert m2.name == 'my_mean'
        assert m2.stateful
        assert m2.dtype == 'float32'
        assert len(m2.weights) == 2

    def test_mean_with_sample_weight(self):
        m = metrics.Mean(dtype='float64')
        assert m.dtype == 'float64'

        # check scalar weight
        result_t = m(100, sample_weight=0.5)
        assert K.eval(result_t) == 50. / 0.5
        assert K.eval(m.total) == 50
        assert K.eval(m.count) == 0.5

        # check weights not scalar and weights rank matches values rank
        result_t = m([1, 5], sample_weight=[1, 0.2])
        result = K.eval(result_t)
        assert np.isclose(result, 52. / 1.7)
        assert np.isclose(K.eval(m.total), 52)  # 50 + 1 + 5 * 0.2
        assert np.isclose(K.eval(m.count), 1.7)  # 0.5 + 1.2

        # check weights broadcast
        result_t = m([1, 2], sample_weight=0.5)
        assert np.isclose(K.eval(result_t), 53.5 / 2.7, rtol=3)
        assert np.isclose(K.eval(m.total), 53.5, rtol=3)  # 52 + 0.5 + 1
        assert np.isclose(K.eval(m.count), 2.7, rtol=3)  # 1.7 + 0.5 + 0.5

        # check weights squeeze
        result_t = m([1, 5], sample_weight=[[1], [0.2]])
        assert np.isclose(K.eval(result_t), 55.5 / 3.9, rtol=3)
        assert np.isclose(K.eval(m.total), 55.5, rtol=3)  # 53.5 + 1 + 1
        assert np.isclose(K.eval(m.count), 3.9, rtol=3)  # 2.7 + 1.2

        # check weights expand
        result_t = m([[1], [5]], sample_weight=[1, 0.2])
        assert np.isclose(K.eval(result_t), 57.5 / 5.1, rtol=3)
        assert np.isclose(K.eval(m.total), 57.5, rtol=3)  # 55.5 + 1 + 1
        assert np.isclose(K.eval(m.count), 5.1, rtol=3)  # 3.9 + 1.2

    def test_multiple_instances(self):
        m = metrics.Mean()
        m2 = metrics.Mean()

        assert m.name == 'mean'
        assert m2.name == 'mean'

        # check initial state
        assert K.eval(m.total) == 0
        assert K.eval(m.count) == 0
        assert K.eval(m2.total) == 0
        assert K.eval(m2.count) == 0

        # check __call__()
        assert K.eval(m(100)) == 100
        assert K.eval(m.total) == 100
        assert K.eval(m.count) == 1
        assert K.eval(m2.total) == 0
        assert K.eval(m2.count) == 0

        assert K.eval(m2([63, 10])) == 36.5
        assert K.eval(m2.total) == 73
        assert K.eval(m2.count) == 2
        assert K.eval(m.result()) == 100
        assert K.eval(m.total) == 100
        assert K.eval(m.count) == 1


class TestAccuracy(object):

    def test_accuracy(self):
        acc_obj = metrics.Accuracy(name='my_acc')

        # check config
        assert acc_obj.name == 'my_acc'
        assert acc_obj.stateful
        assert len(acc_obj.weights) == 2
        assert acc_obj.dtype == 'float32'

        # verify that correct value is returned
        result = K.eval(acc_obj([[1], [2], [3], [4]], [[1], [2], [3], [4]]))
        assert result == 1  # 2/2

        # Check save and restore config
        a2 = metrics.Accuracy.from_config(acc_obj.get_config())
        assert a2.name == 'my_acc'
        assert a2.stateful
        assert len(a2.weights) == 2
        assert a2.dtype, 'float32'

        # check with sample_weight
        result_t = acc_obj([[2], [1]], [[2], [0]], sample_weight=[[0.5], [0.2]])
        result = K.eval(result_t)
        assert np.isclose(result, 4.5 / 4.7, atol=1e-3)

    def test_binary_accuracy(self):
        acc_obj = metrics.BinaryAccuracy(name='my_acc')

        # check config
        assert acc_obj.name == 'my_acc'
        assert acc_obj.stateful
        assert len(acc_obj.weights) == 2
        assert acc_obj.dtype == 'float32'

        # verify that correct value is returned
        result_t = acc_obj([[1], [0]], [[1], [0]])
        result = K.eval(result_t)
        assert result == 1  # 2/2

        # check y_pred squeeze
        result_t = acc_obj([[1], [1]], [[[1]], [[0]]])
        result = K.eval(result_t)
        assert np.isclose(result, 3. / 4., atol=1e-3)

        # check y_true squeeze
        result_t = acc_obj([[[1]], [[1]]], [[1], [0]])
        result = K.eval(result_t)
        assert np.isclose(result, 4. / 6., atol=1e-3)

        # check with sample_weight
        result_t = acc_obj([[1], [1]], [[1], [0]], [[0.5], [0.2]])
        result = K.eval(result_t)
        assert np.isclose(result, 4.5 / 6.7, atol=1e-3)

    def test_binary_accuracy_threshold(self):
        acc_obj = metrics.BinaryAccuracy(threshold=0.7)
        result_t = acc_obj([[1], [1], [0], [0]], [[0.9], [0.6], [0.4], [0.8]])
        result = K.eval(result_t)
        assert np.isclose(result, 0.5, atol=1e-3)

    def test_categorical_accuracy(self):
        acc_obj = metrics.CategoricalAccuracy(name='my_acc')

        # check config
        assert acc_obj.name == 'my_acc'
        assert acc_obj.stateful
        assert len(acc_obj.weights) == 2
        assert acc_obj.dtype == 'float32'

        # verify that correct value is returned
        result_t = acc_obj([[0, 0, 1], [0, 1, 0]],
                           [[0.1, 0.1, 0.8], [0.05, 0.95, 0]])
        result = K.eval(result_t)
        assert result == 1  # 2/2

        # check with sample_weight
        result_t = acc_obj([[0, 0, 1], [0, 1, 0]],
                           [[0.1, 0.1, 0.8], [0.05, 0, 0.95]],
                           [[0.5], [0.2]])
        result = K.eval(result_t)
        assert np.isclose(result, 2.5 / 2.7, atol=1e-3)  # 2.5/2.7

    def test_sparse_categorical_accuracy(self):
        acc_obj = metrics.SparseCategoricalAccuracy(name='my_acc')

        # check config
        assert acc_obj.name == 'my_acc'
        assert acc_obj.stateful
        assert len(acc_obj.weights) == 2
        assert acc_obj.dtype == 'float32'

        # verify that correct value is returned
        result_t = acc_obj([[2], [1]],
                           [[0.1, 0.1, 0.8],
                           [0.05, 0.95, 0]])
        result = K.eval(result_t)
        assert result == 1  # 2/2

        # check with sample_weight
        result_t = acc_obj([[2], [1]],
                           [[0.1, 0.1, 0.8], [0.05, 0, 0.95]],
                           [[0.5], [0.2]])
        result = K.eval(result_t)
        assert np.isclose(result, 2.5 / 2.7, atol=1e-3)

    def test_sparse_categorical_accuracy_mismatched_dims(self):
        acc_obj = metrics.SparseCategoricalAccuracy(name='my_acc')

        # check config
        assert acc_obj.name == 'my_acc'
        assert acc_obj.stateful
        assert len(acc_obj.weights) == 2
        assert acc_obj.dtype == 'float32'

        # verify that correct value is returned
        result_t = acc_obj([2, 1], [[0.1, 0.1, 0.8], [0.05, 0.95, 0]])
        result = K.eval(result_t)
        assert result == 1  # 2/2

        # check with sample_weight
        result_t = acc_obj([2, 1], [[0.1, 0.1, 0.8], [0.05, 0, 0.95]],
                           [[0.5], [0.2]])
        result = K.eval(result_t)
        assert np.isclose(result, 2.5 / 2.7, atol=1e-3)


class TestMeanSquaredErrorTest(object):

    def test_config(self):
        mse_obj = metrics.MeanSquaredError(name='my_mse', dtype='int32')
        assert mse_obj.name == 'my_mse'
        assert mse_obj.dtype == 'int32'

        # Check save and restore config
        mse_obj2 = metrics.MeanSquaredError.from_config(mse_obj.get_config())
        assert mse_obj2.name == 'my_mse'
        assert mse_obj2.dtype == 'int32'

    def test_unweighted(self):
        mse_obj = metrics.MeanSquaredError()
        y_true = ((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                  (1, 1, 1, 1, 0), (0, 0, 0, 0, 1))
        y_pred = ((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                  (0, 1, 0, 1, 0), (1, 1, 1, 1, 1))

        result = mse_obj(y_true, y_pred)
        np.isclose(0.5, K.eval(result), atol=1e-5)

    def test_weighted(self):
        mse_obj = metrics.MeanSquaredError()
        y_true = ((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                  (1, 1, 1, 1, 0), (0, 0, 0, 0, 1))
        y_pred = ((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                  (0, 1, 0, 1, 0), (1, 1, 1, 1, 1))
        sample_weight = (1., 1.5, 2., 2.5)
        result = mse_obj(y_true, y_pred, sample_weight=sample_weight)
        np.isclose(0.54285, K.eval(result), atol=1e-5)


class TestHinge(object):

    def test_config(self):
        hinge_obj = metrics.Hinge(name='hinge', dtype='int32')
        assert hinge_obj.name == 'hinge'
        assert hinge_obj.dtype == 'int32'

        # Check save and restore config
        hinge_obj2 = metrics.Hinge.from_config(hinge_obj.get_config())
        assert hinge_obj2.name == 'hinge'
        assert hinge_obj2.dtype == 'int32'

    def test_unweighted(self):
        hinge_obj = metrics.Hinge()
        y_true = K.constant([[0, 1, 0, 1], [0, 0, 1, 1]])
        y_pred = K.constant([[-0.3, 0.2, -0.1, 1.6],
                             [-0.25, -1., 0.5, 0.6]])

        result = hinge_obj(y_true, y_pred)
        assert np.allclose(0.506, K.eval(result), atol=1e-3)

    def test_weighted(self):
        hinge_obj = metrics.Hinge()
        y_true = K.constant([[-1, 1, -1, 1], [-1, -1, 1, 1]])
        y_pred = K.constant([[-0.3, 0.2, -0.1, 1.6],
                             [-0.25, -1., 0.5, 0.6]])
        sample_weight = K.constant([1.5, 2.])

        result = hinge_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(0.493, K.eval(result), atol=1e-3)


class TestSquaredHinge(object):

    def test_config(self):
        sq_hinge_obj = metrics.SquaredHinge(name='sq_hinge', dtype='int32')
        assert sq_hinge_obj.name == 'sq_hinge'
        assert sq_hinge_obj.dtype == 'int32'

        # Check save and restore config
        sq_hinge_obj2 = metrics.SquaredHinge.from_config(
            sq_hinge_obj.get_config())
        assert sq_hinge_obj2.name == 'sq_hinge'
        assert sq_hinge_obj2.dtype == 'int32'

    def test_unweighted(self):
        sq_hinge_obj = metrics.SquaredHinge()
        y_true = K.constant([[0, 1, 0, 1], [0, 0, 1, 1]])
        y_pred = K.constant([[-0.3, 0.2, -0.1, 1.6],
                             [-0.25, -1., 0.5, 0.6]])

        result = sq_hinge_obj(y_true, y_pred)
        assert np.allclose(0.364, K.eval(result), atol=1e-3)

    def test_weighted(self):
        sq_hinge_obj = metrics.SquaredHinge()
        y_true = K.constant([[-1, 1, -1, 1], [-1, -1, 1, 1]])
        y_pred = K.constant([[-0.3, 0.2, -0.1, 1.6],
                             [-0.25, -1., 0.5, 0.6]])
        sample_weight = K.constant([1.5, 2.])

        result = sq_hinge_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(0.347, K.eval(result), atol=1e-3)


class TestCategoricalHinge(object):

    def test_config(self):
        cat_hinge_obj = metrics.CategoricalHinge(
            name='cat_hinge', dtype='int32')
        assert cat_hinge_obj.name == 'cat_hinge'
        assert cat_hinge_obj.dtype == 'int32'

        # Check save and restore config
        cat_hinge_obj2 = metrics.CategoricalHinge.from_config(
            cat_hinge_obj.get_config())
        assert cat_hinge_obj2.name == 'cat_hinge'
        assert cat_hinge_obj2.dtype == 'int32'

    def test_unweighted(self):
        cat_hinge_obj = metrics.CategoricalHinge()
        y_true = K.constant(((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                             (1, 1, 1, 1, 0), (0, 0, 0, 0, 1)))
        y_pred = K.constant(((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                             (0, 1, 0, 1, 0), (1, 1, 1, 1, 1)))

        result = cat_hinge_obj(y_true, y_pred)
        assert np.allclose(0.5, K.eval(result), atol=1e-5)

    def test_weighted(self):
        cat_hinge_obj = metrics.CategoricalHinge()
        y_true = K.constant(((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                             (1, 1, 1, 1, 0), (0, 0, 0, 0, 1)))
        y_pred = K.constant(((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                             (0, 1, 0, 1, 0), (1, 1, 1, 1, 1)))
        sample_weight = K.constant((1., 1.5, 2., 2.5))
        result = cat_hinge_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(0.5, K.eval(result), atol=1e-5)


class TestTopKCategoricalAccuracy(object):

    def test_config(self):
        a_obj = metrics.TopKCategoricalAccuracy(name='topkca', dtype='int32')
        assert a_obj.name == 'topkca'
        assert a_obj.dtype == 'int32'

        a_obj2 = metrics.TopKCategoricalAccuracy.from_config(a_obj.get_config())
        assert a_obj2.name == 'topkca'
        assert a_obj2.dtype == 'int32'

    def test_correctness(self):
        a_obj = metrics.TopKCategoricalAccuracy()
        y_true = [[0, 0, 1], [0, 1, 0]]
        y_pred = [[0.1, 0.9, 0.8], [0.05, 0.95, 0]]

        result = a_obj(y_true, y_pred)
        assert 1 == K.eval(result)  # both the samples match

        # With `k` < 5.
        a_obj = metrics.TopKCategoricalAccuracy(k=1)
        result = a_obj(y_true, y_pred)
        assert 0.5 == K.eval(result)  # only sample #2 matches

        # With `k` > 5.
        y_true = ([[0, 0, 1, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0]])
        y_pred = [[0.5, 0.9, 0.1, 0.7, 0.6, 0.5, 0.4],
                  [0.05, 0.95, 0, 0, 0, 0, 0]]
        a_obj = metrics.TopKCategoricalAccuracy(k=6)
        result = a_obj(y_true, y_pred)
        assert 0.5 == K.eval(result)  # only 1 sample matches.

    def test_weighted(self):
        a_obj = metrics.TopKCategoricalAccuracy(k=2)
        y_true = [[0, 1, 0], [1, 0, 0], [0, 0, 1]]
        y_pred = [[0, 0.9, 0.1], [0, 0.9, 0.1], [0, 0.9, 0.1]]
        sample_weight = (1.0, 0.0, 1.0)
        result = a_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(1.0, K.eval(result), atol=1e-5)


class TestSparseTopKCategoricalAccuracy(object):

    def test_config(self):
        a_obj = metrics.SparseTopKCategoricalAccuracy(
            name='stopkca', dtype='int32')
        assert a_obj.name == 'stopkca'
        assert a_obj.dtype == 'int32'

        a_obj2 = metrics.SparseTopKCategoricalAccuracy.from_config(
            a_obj.get_config())
        assert a_obj2.name == 'stopkca'
        assert a_obj2.dtype == 'int32'

    def test_correctness(self):
        a_obj = metrics.SparseTopKCategoricalAccuracy()
        y_true = [2, 1]
        y_pred = [[0.1, 0.9, 0.8], [0.05, 0.95, 0]]

        result = a_obj(y_true, y_pred)
        assert 1 == K.eval(result)  # both the samples match

        # With `k` < 5.
        a_obj = metrics.SparseTopKCategoricalAccuracy(k=1)
        result = a_obj(y_true, y_pred)
        assert 0.5 == K.eval(result)  # only sample #2 matches

        # With `k` > 5.
        y_pred = [[0.5, 0.9, 0.1, 0.7, 0.6, 0.5, 0.4],
                  [0.05, 0.95, 0, 0, 0, 0, 0]]
        a_obj = metrics.SparseTopKCategoricalAccuracy(k=6)
        result = a_obj(y_true, y_pred)
        assert 0.5 == K.eval(result)  # only 1 sample matches.

    def test_weighted(self):
        a_obj = metrics.SparseTopKCategoricalAccuracy(k=2)
        y_true = [1, 0, 2]
        y_pred = [[0, 0.9, 0.1], [0, 0.9, 0.1], [0, 0.9, 0.1]]
        sample_weight = (1.0, 0.0, 1.0)
        result = a_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(1.0, K.eval(result), atol=1e-5)


class TestLogCoshError(object):

    def setup(self):
        self.y_pred = np.asarray([1, 9, 2, -5, -2, 6]).reshape((2, 3))
        self.y_true = np.asarray([4, 8, 12, 8, 1, 3]).reshape((2, 3))
        self.batch_size = 6
        error = self.y_pred - self.y_true
        self.expected_results = np.log((np.exp(error) + np.exp(-error)) / 2)

    def test_config(self):
        logcosh_obj = metrics.LogCoshError(name='logcosh', dtype='int32')
        assert logcosh_obj.name == 'logcosh'
        assert logcosh_obj.dtype == 'int32'

    def test_unweighted(self):
        self.setup()
        logcosh_obj = metrics.LogCoshError()

        result = logcosh_obj(self.y_true, self.y_pred)
        expected_result = np.sum(self.expected_results) / self.batch_size
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_weighted(self):
        self.setup()
        logcosh_obj = metrics.LogCoshError()
        sample_weight = [[1.2], [3.4]]
        result = logcosh_obj(self.y_true, self.y_pred, sample_weight=sample_weight)

        sample_weight = np.asarray([1.2, 1.2, 1.2, 3.4, 3.4, 3.4]).reshape((2, 3))
        expected_result = np.multiply(self.expected_results, sample_weight)
        expected_result = np.sum(expected_result) / np.sum(sample_weight)
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)


class TestPoisson(object):

    def setup(self):
        self.y_pred = np.asarray([1, 9, 2, 5, 2, 6]).reshape((2, 3))
        self.y_true = np.asarray([4, 8, 12, 8, 1, 3]).reshape((2, 3))
        self.batch_size = 6
        self.expected_results = self.y_pred - np.multiply(
            self.y_true, np.log(self.y_pred))

    def test_config(self):
        poisson_obj = metrics.Poisson(name='poisson', dtype='int32')
        assert poisson_obj.name == 'poisson'
        assert poisson_obj.dtype == 'int32'

        poisson_obj2 = metrics.Poisson.from_config(poisson_obj.get_config())
        assert poisson_obj2.name == 'poisson'
        assert poisson_obj2.dtype == 'int32'

    def test_unweighted(self):
        self.setup()
        poisson_obj = metrics.Poisson()

        result = poisson_obj(self.y_true, self.y_pred)
        expected_result = np.sum(self.expected_results) / self.batch_size
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_weighted(self):
        self.setup()
        poisson_obj = metrics.Poisson()
        sample_weight = [[1.2], [3.4]]

        result = poisson_obj(self.y_true, self.y_pred, sample_weight=sample_weight)
        sample_weight = np.asarray([1.2, 1.2, 1.2, 3.4, 3.4, 3.4]).reshape((2, 3))
        expected_result = np.multiply(self.expected_results, sample_weight)
        expected_result = np.sum(expected_result) / np.sum(sample_weight)
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)


class TestKLDivergence(object):

    def setup(self):
        self.y_pred = np.asarray([.4, .9, .12, .36, .3, .4]).reshape((2, 3))
        self.y_true = np.asarray([.5, .8, .12, .7, .43, .8]).reshape((2, 3))
        self.batch_size = 2
        self.expected_results = np.multiply(
            self.y_true, np.log(self.y_true / self.y_pred))

    def test_config(self):
        k_obj = metrics.KLDivergence(name='kld', dtype='int32')
        assert k_obj.name == 'kld'
        assert k_obj.dtype == 'int32'

        k_obj2 = metrics.KLDivergence.from_config(k_obj.get_config())
        assert k_obj2.name == 'kld'
        assert k_obj2.dtype == 'int32'

    def test_unweighted(self):
        self.setup()
        k_obj = metrics.KLDivergence()

        result = k_obj(self.y_true, self.y_pred)
        expected_result = np.sum(self.expected_results) / self.batch_size
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_weighted(self):
        self.setup()
        k_obj = metrics.KLDivergence()
        sample_weight = [[1.2], [3.4]]
        result = k_obj(self.y_true, self.y_pred, sample_weight=sample_weight)

        sample_weight = np.asarray([1.2, 1.2, 1.2, 3.4, 3.4, 3.4]).reshape((2, 3))
        expected_result = np.multiply(self.expected_results, sample_weight)
        expected_result = np.sum(expected_result) / (1.2 + 3.4)
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)


class TestCosineSimilarity(object):

    def l2_norm(self, x, axis):
        epsilon = 1e-12
        square_sum = np.sum(np.square(x), axis=axis, keepdims=True)
        x_inv_norm = 1 / np.sqrt(np.maximum(square_sum, epsilon))
        return np.multiply(x, x_inv_norm)

    def setup(self, axis=1):
        self.np_y_true = np.asarray([[1, 9, 2], [-5, -2, 6]], dtype=np.float32)
        self.np_y_pred = np.asarray([[4, 8, 12], [8, 1, 3]], dtype=np.float32)

        y_true = self.l2_norm(self.np_y_true, axis)
        y_pred = self.l2_norm(self.np_y_pred, axis)
        self.expected_loss = np.sum(np.multiply(y_true, y_pred), axis=(axis,))

        self.y_true = K.constant(self.np_y_true)
        self.y_pred = K.constant(self.np_y_pred)

    def test_config(self):
        cosine_obj = metrics.CosineSimilarity(
            axis=2, name='my_cos', dtype='int32')
        assert cosine_obj.name == 'my_cos'
        assert cosine_obj.dtype == 'int32'

        # Check save and restore config
        cosine_obj2 = metrics.CosineSimilarity.from_config(cosine_obj.get_config())
        assert cosine_obj2.name == 'my_cos'
        assert cosine_obj2.dtype == 'int32'

    def test_unweighted(self):
        self.setup()
        cosine_obj = metrics.CosineSimilarity()
        loss = cosine_obj(self.y_true, self.y_pred)
        expected_loss = np.mean(self.expected_loss)
        assert np.allclose(K.eval(loss), expected_loss, 3)

    def test_weighted(self):
        self.setup()
        cosine_obj = metrics.CosineSimilarity()
        sample_weight = np.asarray([1.2, 3.4])
        loss = cosine_obj(
            self.y_true,
            self.y_pred,
            sample_weight=K.constant(sample_weight))
        expected_loss = np.sum(
            self.expected_loss * sample_weight) / np.sum(sample_weight)
        assert np.allclose(K.eval(loss), expected_loss, 3)

    def test_axis(self):
        self.setup(axis=1)
        cosine_obj = metrics.CosineSimilarity(axis=1)
        loss = cosine_obj(self.y_true, self.y_pred)
        expected_loss = np.mean(self.expected_loss)
        assert np.allclose(K.eval(loss), expected_loss, 3)


class TestMeanAbsoluteError(object):

    def test_config(self):
        mae_obj = metrics.MeanAbsoluteError(name='my_mae', dtype='int32')
        assert mae_obj.name == 'my_mae'
        assert mae_obj.dtype == 'int32'

        # Check save and restore config
        mae_obj2 = metrics.MeanAbsoluteError.from_config(mae_obj.get_config())
        assert mae_obj2.name == 'my_mae'
        assert mae_obj2.dtype == 'int32'

    def test_unweighted(self):
        mae_obj = metrics.MeanAbsoluteError()
        y_true = K.constant(((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                             (1, 1, 1, 1, 0), (0, 0, 0, 0, 1)))
        y_pred = K.constant(((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                             (0, 1, 0, 1, 0), (1, 1, 1, 1, 1)))

        result = mae_obj(y_true, y_pred)
        assert np.allclose(0.5, K.eval(result), atol=1e-5)

    def test_weighted(self):
        mae_obj = metrics.MeanAbsoluteError()
        y_true = K.constant(((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                             (1, 1, 1, 1, 0), (0, 0, 0, 0, 1)))
        y_pred = K.constant(((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                             (0, 1, 0, 1, 0), (1, 1, 1, 1, 1)))
        sample_weight = K.constant((1., 1.5, 2., 2.5))
        result = mae_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(0.54285, K.eval(result), atol=1e-5)


class TestMeanAbsolutePercentageError(object):

    def test_config(self):
        mape_obj = metrics.MeanAbsolutePercentageError(
            name='my_mape', dtype='int32')
        assert mape_obj.name == 'my_mape'
        assert mape_obj.dtype == 'int32'

        # Check save and restore config
        mape_obj2 = metrics.MeanAbsolutePercentageError.from_config(
            mape_obj.get_config())
        assert mape_obj2.name == 'my_mape'
        assert mape_obj2.dtype == 'int32'

    def test_unweighted(self):
        mape_obj = metrics.MeanAbsolutePercentageError()
        y_true = K.constant(((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                            (1, 1, 1, 1, 0), (0, 0, 0, 0, 1)))
        y_pred = K.constant(((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                            (0, 1, 0, 1, 0), (1, 1, 1, 1, 1)))

        result = mape_obj(y_true, y_pred)
        assert np.allclose(35e7, K.eval(result), atol=1e-5)

    def test_weighted(self):
        mape_obj = metrics.MeanAbsolutePercentageError()
        y_true = K.constant(((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                            (1, 1, 1, 1, 0), (0, 0, 0, 0, 1)))
        y_pred = K.constant(((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                            (0, 1, 0, 1, 0), (1, 1, 1, 1, 1)))
        sample_weight = K.constant((1., 1.5, 2., 2.5))
        result = mape_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(40e7, K.eval(result), atol=1e-5)


class TestMeanSquaredError(object):

    def test_config(self):
        mse_obj = metrics.MeanSquaredError(name='my_mse', dtype='int32')
        assert mse_obj.name == 'my_mse'
        assert mse_obj.dtype == 'int32'

        # Check save and restore config
        mse_obj2 = metrics.MeanSquaredError.from_config(mse_obj.get_config())
        assert mse_obj2.name == 'my_mse'
        assert mse_obj2.dtype == 'int32'

    def test_unweighted(self):
        mse_obj = metrics.MeanSquaredError()
        y_true = K.constant(((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                             (1, 1, 1, 1, 0), (0, 0, 0, 0, 1)))
        y_pred = K.constant(((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                            (0, 1, 0, 1, 0), (1, 1, 1, 1, 1)))

        result = mse_obj(y_true, y_pred)
        assert np.allclose(0.5, K.eval(result), atol=1e-5)

    def test_weighted(self):
        mse_obj = metrics.MeanSquaredError()
        y_true = K.constant(((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                            (1, 1, 1, 1, 0), (0, 0, 0, 0, 1)))
        y_pred = K.constant(((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                            (0, 1, 0, 1, 0), (1, 1, 1, 1, 1)))
        sample_weight = K.constant((1., 1.5, 2., 2.5))
        result = mse_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(0.54285, K.eval(result), atol=1e-5)


class TestMeanSquaredLogarithmicError(object):

    def test_config(self):
        msle_obj = metrics.MeanSquaredLogarithmicError(
            name='my_msle', dtype='int32')
        assert msle_obj.name == 'my_msle'
        assert msle_obj.dtype == 'int32'

        # Check save and restore config
        msle_obj2 = metrics.MeanSquaredLogarithmicError.from_config(
            msle_obj.get_config())
        assert msle_obj2.name == 'my_msle'
        assert msle_obj2.dtype == 'int32'

    def test_unweighted(self):
        msle_obj = metrics.MeanSquaredLogarithmicError()
        y_true = K.constant(((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                            (1, 1, 1, 1, 0), (0, 0, 0, 0, 1)))
        y_pred = K.constant(((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                            (0, 1, 0, 1, 0), (1, 1, 1, 1, 1)))

        result = msle_obj(y_true, y_pred)
        assert np.allclose(0.24022, K.eval(result), atol=1e-5)

    def test_weighted(self):
        msle_obj = metrics.MeanSquaredLogarithmicError()
        y_true = K.constant(((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                            (1, 1, 1, 1, 0), (0, 0, 0, 0, 1)))
        y_pred = K.constant(((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                            (0, 1, 0, 1, 0), (1, 1, 1, 1, 1)))
        sample_weight = K.constant((1., 1.5, 2., 2.5))
        result = msle_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(0.26082, K.eval(result), atol=1e-5)


class TestRootMeanSquaredError(object):

    def test_config(self):
        rmse_obj = metrics.RootMeanSquaredError(name='rmse', dtype='int32')
        assert rmse_obj.name == 'rmse'
        assert rmse_obj.dtype == 'int32'

        rmse_obj2 = metrics.RootMeanSquaredError.from_config(rmse_obj.get_config())
        assert rmse_obj2.name == 'rmse'
        assert rmse_obj2.dtype == 'int32'

    def test_unweighted(self):
        rmse_obj = metrics.RootMeanSquaredError()
        y_true = K.constant((2, 4, 6))
        y_pred = K.constant((1, 3, 2))

        update_op = rmse_obj(y_true, y_pred)
        K.eval(update_op)
        result = rmse_obj(y_true, y_pred)
        # error = [-1, -1, -4], square(error) = [1, 1, 16], mean = 18/3 = 6
        assert np.allclose(math.sqrt(6), K.eval(result), atol=1e-3)

    def test_weighted(self):
        rmse_obj = metrics.RootMeanSquaredError()
        y_true = K.constant((2, 4, 6, 8))
        y_pred = K.constant((1, 3, 2, 3))
        sample_weight = K.constant((0, 1, 0, 1))
        result = rmse_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(math.sqrt(13), K.eval(result), atol=1e-3)


class TestBinaryCrossentropy(object):

    def test_config(self):
        bce_obj = metrics.BinaryCrossentropy(
            name='bce', dtype='int32', label_smoothing=0.2)
        assert bce_obj.name == 'bce'
        assert bce_obj.dtype == 'int32'

        old_config = bce_obj.get_config()
        assert np.allclose(old_config['label_smoothing'], 0.2, atol=1e-3)

    def test_unweighted(self):
        bce_obj = metrics.BinaryCrossentropy()
        y_true = np.asarray([1, 0, 1, 0]).reshape([2, 2])
        y_pred = np.asarray([1, 1, 1, 0], dtype=np.float32).reshape([2, 2])
        result = bce_obj(y_true, y_pred)

        assert np.allclose(K.eval(result), 3.833, atol=1e-3)

    def test_unweighted_with_logits(self):
        bce_obj = metrics.BinaryCrossentropy(from_logits=True)

        y_true = [[1, 0, 1], [0, 1, 1]]
        y_pred = [[100.0, -100.0, 100.0], [100.0, 100.0, -100.0]]
        result = bce_obj(y_true, y_pred)

        assert np.allclose(K.eval(result), 33.333, atol=1e-3)

    def test_weighted(self):
        bce_obj = metrics.BinaryCrossentropy()
        y_true = np.asarray([1, 0, 1, 0]).reshape([2, 2])
        y_pred = np.asarray([1, 1, 1, 0], dtype=np.float32).reshape([2, 2])
        sample_weight = [1.5, 2.]
        result = bce_obj(y_true, y_pred, sample_weight=sample_weight)

        assert np.allclose(K.eval(result), 3.285, atol=1e-3)

    def test_weighted_from_logits(self):
        bce_obj = metrics.BinaryCrossentropy(from_logits=True)
        y_true = [[1, 0, 1], [0, 1, 1]]
        y_pred = [[100.0, -100.0, 100.0], [100.0, 100.0, -100.0]]
        sample_weight = [2., 2.5]
        result = bce_obj(y_true, y_pred, sample_weight=sample_weight)

        assert np.allclose(K.eval(result), 37.037, atol=1e-3)

    def test_label_smoothing(self):
        logits = ((100., -100., -100.))
        y_true = ((1, 0, 1))
        label_smoothing = 0.1
        bce_obj = metrics.BinaryCrossentropy(
            from_logits=True, label_smoothing=label_smoothing)
        result = bce_obj(y_true, logits)
        expected_value = (100.0 + 50.0 * label_smoothing) / 3.0
        assert np.allclose(expected_value, K.eval(result), atol=1e-3)


class TestCategoricalCrossentropy(object):

    def test_config(self):
        cce_obj = metrics.CategoricalCrossentropy(
            name='cce', dtype='int32', label_smoothing=0.2)
        assert cce_obj.name == 'cce'
        assert cce_obj.dtype == 'int32'

        old_config = cce_obj.get_config()
        assert np.allclose(old_config['label_smoothing'], 0.2, 1e-3)

    def test_unweighted(self):
        cce_obj = metrics.CategoricalCrossentropy()

        y_true = np.asarray([[0, 1, 0], [0, 0, 1]])
        y_pred = np.asarray([[0.05, 0.95, 0], [0.1, 0.8, 0.1]])
        result = cce_obj(y_true, y_pred)

        assert np.allclose(K.eval(result), 1.176, atol=1e-3)

    def test_unweighted_from_logits(self):
        cce_obj = metrics.CategoricalCrossentropy(from_logits=True)

        y_true = np.asarray([[0, 1, 0], [0, 0, 1]])
        logits = np.asarray([[1, 9, 0], [1, 8, 1]], dtype=np.float32)
        result = cce_obj(y_true, logits)

        assert np.allclose(K.eval(result), 3.5011, atol=1e-3)

    def test_weighted(self):
        cce_obj = metrics.CategoricalCrossentropy()

        y_true = np.asarray([[0, 1, 0], [0, 0, 1]])
        y_pred = np.asarray([[0.05, 0.95, 0], [0.1, 0.8, 0.1]])
        sample_weight = [1.5, 2.]
        result = cce_obj(y_true, y_pred, sample_weight=sample_weight)

        assert np.allclose(K.eval(result), 1.338, atol=1e-3)

    def test_weighted_from_logits(self):
        cce_obj = metrics.CategoricalCrossentropy(from_logits=True)

        y_true = np.asarray([[0, 1, 0], [0, 0, 1]])
        logits = np.asarray([[1, 9, 0], [1, 8, 1]], dtype=np.float32)
        sample_weight = [1.5, 2.]
        result = cce_obj(y_true, logits, sample_weight=sample_weight)

        assert np.allclose(K.eval(result), 4.0012, atol=1e-3)

    def test_label_smoothing(self):
        y_true = np.asarray([[0, 1, 0], [0, 0, 1]])
        logits = np.asarray([[1, 9, 0], [1, 8, 1]], dtype=np.float32)
        label_smoothing = 0.1

        cce_obj = metrics.CategoricalCrossentropy(
            from_logits=True, label_smoothing=label_smoothing)
        loss = cce_obj(y_true, logits)
        assert np.allclose(K.eval(loss), 3.667, atol=1e-3)


class TestSparseCategoricalCrossentropy(object):

    def test_config(self):
        scce_obj = metrics.SparseCategoricalCrossentropy(
            name='scce', dtype='int32')
        assert scce_obj.name == 'scce'
        assert scce_obj.dtype == 'int32'

    def test_unweighted(self):
        scce_obj = metrics.SparseCategoricalCrossentropy()

        y_true = np.asarray([1, 2])
        y_pred = np.asarray([[0.05, 0.95, 0], [0.1, 0.8, 0.1]])
        result = scce_obj(y_true, y_pred)

        assert np.allclose(K.eval(result), 1.176, atol=1e-3)

    def test_unweighted_from_logits(self):
        scce_obj = metrics.SparseCategoricalCrossentropy(from_logits=True)

        y_true = np.asarray([1, 2])
        logits = np.asarray([[1, 9, 0], [1, 8, 1]], dtype=np.float32)
        result = scce_obj(y_true, logits)

        assert np.allclose(K.eval(result), 3.5011, atol=1e-3)

    def test_weighted(self):
        scce_obj = metrics.SparseCategoricalCrossentropy()

        y_true = np.asarray([1, 2])
        y_pred = np.asarray([[0.05, 0.95, 0], [0.1, 0.8, 0.1]])
        sample_weight = [1.5, 2.]
        result = scce_obj(y_true, y_pred, sample_weight=sample_weight)

        assert np.allclose(K.eval(result), 1.338, atol=1e-3)

    def test_weighted_from_logits(self):
        scce_obj = metrics.SparseCategoricalCrossentropy(from_logits=True)
        y_true = np.asarray([1, 2])
        logits = np.asarray([[1, 9, 0], [1, 8, 1]], dtype=np.float32)
        sample_weight = [1.5, 2.]
        result = scce_obj(y_true, logits, sample_weight=sample_weight)

        assert np.allclose(K.eval(result), 4.0012, atol=1e-3)

    def test_axis(self):
        scce_obj = metrics.SparseCategoricalCrossentropy(axis=0)

        y_true = np.asarray([1, 2])
        y_pred = np.asarray([[0.05, 0.1], [0.95, 0.8], [0, 0.1]])
        result = scce_obj(y_true, y_pred)

        assert np.allclose(K.eval(result), 1.176, atol=1e-3)

"""Tests for Keras metrics correctness."""

import numpy as np

import keras
from keras import layers
from keras import losses
from keras import metrics
from keras import backend as K


def get_multi_io_model():
    inp_1 = layers.Input(shape=(1,), name='input_1')
    inp_2 = layers.Input(shape=(1,), name='input_2')
    dense = layers.Dense(3, kernel_initializer='ones', trainable=False)
    x_1 = dense(inp_1)
    x_2 = dense(inp_2)
    out_1 = layers.Dense(
        1, kernel_initializer='ones', name='output_1', trainable=False)(x_1)
    out_2 = layers.Dense(
        1, kernel_initializer='ones', name='output_2', trainable=False)(x_2)
    return keras.Model([inp_1, inp_2], [out_1, out_2])


def custom_generator_multi_io(sample_weights=None):
    batch_size = 2
    num_samples = 4
    inputs = np.asarray([[1.], [2.], [3.], [4.]])
    targets_1 = np.asarray([[2.], [4.], [6.], [8.]])
    targets_2 = np.asarray([[1.], [2.], [3.], [4.]])
    w1 = sample_weights[0] if sample_weights else None
    w2 = sample_weights[1] if sample_weights else None
    i = 0
    while True:
        batch_index = i * batch_size % num_samples
        i += 1
        start = batch_index
        end = start + batch_size
        x = [inputs[start:end], inputs[start:end]]
        y = [targets_1[start:end], targets_2[start:end]]
        if sample_weights:
            w = [
                None if w1 is None else w1[start:end],
                None if w2 is None else w2[start:end]
            ]
        else:
            w = None
        yield x, y, w


class TestMetricsCorrectnessMultiIO(object):

    def _get_compiled_multi_io_model(self):
        model = get_multi_io_model()
        model.compile(
            optimizer='rmsprop',
            loss=losses.MeanSquaredError(),
            metrics=[metrics.MeanSquaredError(name='mean_squared_error')],
            weighted_metrics=[
                metrics.MeanSquaredError(name='mean_squared_error_2')
            ])
        return model

    def setUp(self):
        self.x = np.asarray([[1.], [2.], [3.], [4.]])
        self.y1 = np.asarray([[2.], [4.], [6.], [8.]])
        self.y2 = np.asarray([[1.], [2.], [3.], [4.]])
        self.sample_weight_1 = np.asarray([2., 3., 4., 5.])
        self.sample_weight_2 = np.asarray([3.5, 2.5, 1.5, 0.5])
        self.class_weight_1 = {2: 2, 4: 3, 6: 4, 8: 5}
        self.class_weight_2 = {1: 3.5, 2: 2.5, 3: 1.5, 4: 0.5}

        # y_true_1 = [[2.], [4.], [6.], [8.]], y_pred = [[3.], [6.], [9.], [12.]]
        # y_true_2 = [[1.], [2.], [3.], [4.]], y_pred = [[3.], [6.], [9.], [12.]]

        # Weighted metric `output_1`:
        #   Total = ((3 - 2)^2 * 2  + (6 - 4)^2 * 3) +
        #           ((9 - 6)^2 * 4 + (12 - 8)^2 * 5)
        #         = 130
        #   Count = (2 + 3) + (4 + 5)
        #   Result = 9.2857141

        # Weighted metric `output_2`:
        #   Total = ((3 - 1)^2 * 3.5 + (6 - 2)^2 * 2.5) +
        #           ((9 - 3)^2 * 1.5 + (12 - 4)^2 * 0.5)
        #         = 140
        #   Count = (3.5 + 2.5) + (1.5 + 0.5)
        #   Result = 17.5

        # Loss `output_1` with weights:
        #   Total = ((3 - 2)^2 * 2  + (6 - 4)^2 * 3) +
        #           ((9 - 6)^2 * 4 + (12 - 8)^2 * 5)
        #         = 130
        #   Count = 2 + 2
        #   Result = 32.5

        # Loss `output_1` without weights/Metric `output_1`:
        #   Total = ((3 - 2)^2 + (6 - 4)^2) + ((9 - 6)^2 + (12 - 8)^2) = 30
        #   Count = 2 + 2
        #   Result = 7.5

        # Loss `output_2` with weights:
        #   Total = ((3 - 1)^2 * 3.5 + (6 - 2)^2 * 2.5) +
        #           ((9 - 3)^2 * 1.5 + (12 - 4)^2 * 0.5)
        #         = 140
        #   Count = 2 + 2
        #   Result = 35

        # Loss `output_2` without weights/Metric `output_2`:
        #   Total = ((3 - 1)^2 + (6 - 2)^2) + ((9 - 3)^2 + (12 - 4)^2) = 120
        #   Count = 2 + 2
        #   Result = 30

        # Total loss with weights = 32.5 + 35 = 67.5
        # Total loss without weights = 7.5 + 30 = 37.5

        self.expected_fit_result_with_weights = {
            'output_1_mean_squared_error': [7.5, 7.5],
            'output_2_mean_squared_error': [30, 30],
            'output_1_mean_squared_error_2': [9.286, 9.286],
            'output_2_mean_squared_error_2': [17.5, 17.5],
            'loss': [67.5, 67.5],
            'output_1_loss': [32.5, 32.5],
            'output_2_loss': [35, 35],
        }

        self.expected_fit_result_with_weights_output_2 = {
            'output_1_mean_squared_error': [7.5, 7.5],
            'output_2_mean_squared_error': [30, 30],
            'output_1_mean_squared_error_2': [7.5, 7.5],
            'output_2_mean_squared_error_2': [17.5, 17.5],
            'loss': [42.5, 42.5],
            'output_1_loss': [7.5, 7.5],
            'output_2_loss': [35, 35],
        }

        self.expected_fit_result = {
            'output_1_mean_squared_error': [7.5, 7.5],
            'output_2_mean_squared_error': [30, 30],
            'output_1_mean_squared_error_2': [7.5, 7.5],
            'output_2_mean_squared_error_2': [30, 30],
            'loss': [37.5, 37.5],
            'output_1_loss': [7.5, 7.5],
            'output_2_loss': [30, 30],
        }

        # In the order: 'loss', 'output_1_loss', 'output_2_loss',
        # 'output_1_mean_squared_error', 'output_1_mean_squared_error_2',
        # 'output_2_mean_squared_error', 'output_2_mean_squared_error_2'
        self.expected_batch_result_with_weights = [
            67.5, 32.5, 35, 7.5, 9.286, 30, 17.5
        ]
        self.expected_batch_result_with_weights_output_2 = [
            42.5, 7.5, 35, 7.5, 7.5, 30, 17.5
        ]
        self.expected_batch_result = [37.5, 7.5, 30, 7.5, 7.5, 30, 30]

    def test_fit(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        history = model.fit([self.x, self.x], [self.y1, self.y2],
                            batch_size=2,
                            epochs=2,
                            shuffle=False)
        for key, value in self.expected_fit_result.items():
            np.allclose(history.history[key], value, 1e-3)

    def test_fit_with_sample_weight(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        history = model.fit([self.x, self.x], [self.y1, self.y2],
                            sample_weight={
                                'output_1': self.sample_weight_1,
                                'output_2': self.sample_weight_2},
                            batch_size=2,
                            epochs=2,
                            shuffle=False)
        for key, value in self.expected_fit_result_with_weights.items():
            np.allclose(history.history[key], value, 1e-3)

        # Set weights for one output (use batch size).
        history = model.fit([self.x, self.x], [self.y1, self.y2],
                            sample_weight={'output_2': self.sample_weight_2},
                            batch_size=2,
                            epochs=2,
                            shuffle=False)

        for key, value in self.expected_fit_result_with_weights_output_2.items():
            np.allclose(history.history[key], value, 1e-3)

    def DISABLED_test_fit_with_class_weight(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        history = model.fit([self.x, self.x], [self.y1, self.y2],
                            class_weight={
                                'output_1': self.class_weight_1,
                                'output_2': self.class_weight_2},
                            batch_size=2,
                            epochs=2,
                            shuffle=False)
        for key, value in self.expected_fit_result_with_weights.items():
            np.allclose(history.history[key], value, 1e-3)

        # Set weights for one output.
        history = model.fit([self.x, self.x], [self.y1, self.y2],
                            class_weight={'output_2': self.class_weight_2},
                            batch_size=2,
                            epochs=2,
                            shuffle=False)

        for key, value in self.expected_fit_result_with_weights_output_2.items():
            np.allclose(history.history[key], value, 1e-3)

    def test_eval(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        eval_result = model.evaluate([self.x, self.x], [self.y1, self.y2],
                                     batch_size=2)
        np.allclose(eval_result, self.expected_batch_result, 1e-3)

    def test_eval_with_sample_weight(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        eval_result = model.evaluate([self.x, self.x], [self.y1, self.y2],
                                     batch_size=2,
                                     sample_weight={
                                         'output_1': self.sample_weight_1,
                                         'output_2': self.sample_weight_2})
        np.allclose(eval_result, self.expected_batch_result_with_weights,
                    1e-3)

        # Set weights for one output.
        model = self._get_compiled_multi_io_model()
        eval_result = model.evaluate([self.x, self.x], [self.y1, self.y2],
                                     batch_size=2,
                                     sample_weight={
                                         'output_2': self.sample_weight_2})
        np.allclose(eval_result,
                    self.expected_batch_result_with_weights_output_2, 1e-3)

        # Verify that metric value is same with arbitrary weights and batch size.
        x = np.random.random((50, 1))
        y = np.random.random((50, 1))
        w = np.random.random((50,))
        mse1 = model.evaluate([x, x], [y, y], sample_weight=[w, w], batch_size=5)[3]
        mse2 = model.evaluate([x, x], [y, y], sample_weight=[w, w],
                              batch_size=10)[3]
        np.allclose(mse1, mse2, 1e-3)

    def test_train_on_batch(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        result = model.train_on_batch([self.x, self.x], [self.y1, self.y2])
        np.allclose(result, self.expected_batch_result, 1e-3)

    def test_train_on_batch_with_sample_weight(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        result = model.train_on_batch([self.x, self.x], [self.y1, self.y2],
                                      sample_weight={
                                          'output_1': self.sample_weight_1,
                                          'output_2': self.sample_weight_2})
        np.allclose(result, self.expected_batch_result_with_weights, 1e-3)

        # Set weights for one output.
        result = model.train_on_batch([self.x, self.x], [self.y1, self.y2],
                                      sample_weight={
                                          'output_2': self.sample_weight_2})
        np.allclose(result, self.expected_batch_result_with_weights_output_2, 1e-3)

    def DISABLED_test_train_on_batch_with_class_weight(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        result = model.train_on_batch([self.x, self.x], [self.y1, self.y2],
                                      class_weight={
                                          'output_1': self.class_weight_1,
                                          'output_2': self.class_weight_2})
        np.allclose(result, self.expected_batch_result_with_weights, 1e-3)

        # Set weights for one output.
        result = model.train_on_batch([self.x, self.x], [self.y1, self.y2],
                                      class_weight={
                                          'output_2': self.class_weight_2})
        np.allclose(result,
                    self.expected_batch_result_with_weights_output_2, 1e-3)

    def test_test_on_batch(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        result = model.test_on_batch([self.x, self.x], [self.y1, self.y2])
        np.allclose(result, self.expected_batch_result, 1e-3)

    def test_test_on_batch_with_sample_weight(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        result = model.test_on_batch([self.x, self.x], [self.y1, self.y2],
                                     sample_weight={
                                         'output_1': self.sample_weight_1,
                                         'output_2': self.sample_weight_2})
        np.allclose(result, self.expected_batch_result_with_weights, 1e-3)

        # Set weights for one output.
        result = model.test_on_batch([self.x, self.x], [self.y1, self.y2],
                                     sample_weight={
                                         'output_2': self.sample_weight_2})
        np.allclose(result,
                    self.expected_batch_result_with_weights_output_2, 1e-3)

    def test_fit_generator(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        history = model.fit_generator(
            custom_generator_multi_io(), steps_per_epoch=2, epochs=2)
        for key, value in self.expected_fit_result.items():
            np.allclose(history.history[key], value, 1e-3)

    def DISABLED_test_fit_generator_with_sample_weight(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        history = model.fit_generator(
            custom_generator_multi_io(
                sample_weights=[self.sample_weight_1, self.sample_weight_2]),
            steps_per_epoch=2,
            epochs=2)
        for key, value in self.expected_fit_result_with_weights.items():
            np.allclose(history.history[key], value, 1e-3)

        # Set weights for one output.
        history = model.fit_generator(
            custom_generator_multi_io(sample_weights=[None, self.sample_weight_2]),
            steps_per_epoch=2,
            epochs=2)
        for key, value in self.expected_fit_result_with_weights_output_2.items():
            np.allclose(history.history[key], value, 1e-3)

    def DISABLED_test_fit_generator_with_class_weight(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        history = model.fit_generator(
            custom_generator_multi_io(),
            class_weight={
                'output_1': self.class_weight_1,
                'output_2': self.class_weight_2,
            },
            steps_per_epoch=2,
            epochs=2)
        for key, value in self.expected_fit_result_with_weights.items():
            np.allclose(history.history[key], value, 1e-3)

        # Set weights for one output.
        history = model.fit_generator(
            custom_generator_multi_io(),
            class_weight={'output_2': self.class_weight_2},
            steps_per_epoch=2,
            epochs=2)
        for key, value in self.expected_fit_result_with_weights_output_2.items():
            np.allclose(history.history[key], value, 1e-3)

    def test_eval_generator(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        eval_result = model.evaluate_generator(custom_generator_multi_io(), steps=2)
        np.allclose(eval_result, self.expected_batch_result, 1e-3)

    def DISABLED_test_eval_generator_with_sample_weight(self):
        self.setUp()
        model = self._get_compiled_multi_io_model()
        eval_result = model.evaluate_generator(
            custom_generator_multi_io(
                sample_weights=[self.sample_weight_1, self.sample_weight_2]),
            steps=2)
        np.allclose(eval_result, self.expected_batch_result_with_weights, 1e-3)

        # Set weights for one output.
        eval_result = model.evaluate_generator(
            custom_generator_multi_io(sample_weights=[None, self.sample_weight_2]),
            steps=2)
        np.allclose(eval_result,
                    self.expected_batch_result_with_weights_output_2, 1e-3)

"""Tests for Keras confusion matrix metrics classes."""
import pytest
import numpy as np

from keras import metrics
from keras import backend as K
from tensorflow.python.keras.utils import metrics_utils

if K.backend() != 'tensorflow':
    # Need TensorFlow to use metric.__call__
    pytestmark = pytest.mark.skip

import tensorflow as tf


class TestFalsePositives(object):

    def test_config(self):
        fp_obj = metrics.FalsePositives(name='my_fp', thresholds=[0.4, 0.9])
        assert fp_obj.name == 'my_fp'
        assert len(fp_obj.weights) == 1
        assert fp_obj.thresholds == [0.4, 0.9]

        # Check save and restore config
        fp_obj2 = metrics.FalsePositives.from_config(fp_obj.get_config())
        assert fp_obj2.name == 'my_fp'
        assert len(fp_obj2.weights) == 1
        assert fp_obj2.thresholds == [.4, 0.9]

    def test_unweighted(self):
        fp_obj = metrics.FalsePositives()

        y_true = ((0, 1, 0, 1, 0), (0, 0, 1, 1, 1), (1, 1, 1, 1, 0), (0, 0, 0, 0, 1))
        y_pred = ((0, 0, 1, 1, 0), (1, 1, 1, 1, 1), (0, 1, 0, 1, 0), (1, 1, 1, 1, 1))

        result = fp_obj(y_true, y_pred)
        assert np.allclose(7., K.eval(result))

    def test_weighted(self):
        fp_obj = metrics.FalsePositives()
        y_true = ((0, 1, 0, 1, 0), (0, 0, 1, 1, 1), (1, 1, 1, 1, 0), (0, 0, 0, 0, 1))
        y_pred = ((0, 0, 1, 1, 0), (1, 1, 1, 1, 1), (0, 1, 0, 1, 0), (1, 1, 1, 1, 1))
        sample_weight = (1., 1.5, 2., 2.5)
        result = fp_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(14., K.eval(result))

    def test_unweighted_with_thresholds(self):
        fp_obj = metrics.FalsePositives(thresholds=[0.15, 0.5, 0.85])

        y_pred = ((0.9, 0.2, 0.8, 0.1), (0.2, 0.9, 0.7, 0.6),
                  (0.1, 0.2, 0.4, 0.3), (0, 1, 0.7, 0.3))
        y_true = ((0, 1, 1, 0), (1, 0, 0, 0), (0, 0, 0, 0), (1, 1, 1, 1))

        result = fp_obj(y_true, y_pred)
        assert np.allclose([7., 4., 2.], K.eval(result))

    def test_weighted_with_thresholds(self):
        fp_obj = metrics.FalsePositives(thresholds=[0.15, 0.5, 0.85])

        y_pred = ((0.9, 0.2, 0.8, 0.1), (0.2, 0.9, 0.7, 0.6),
                  (0.1, 0.2, 0.4, 0.3), (0, 1, 0.7, 0.3))
        y_true = ((0, 1, 1, 0), (1, 0, 0, 0), (0, 0, 0, 0), (1, 1, 1, 1))
        sample_weight = ((1.0, 2.0, 3.0, 5.0), (7.0, 11.0, 13.0, 17.0),
                         (19.0, 23.0, 29.0, 31.0), (5.0, 15.0, 10.0, 0))

        result = fp_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose([125., 42., 12.], K.eval(result))

    def test_threshold_limit(self):
        with pytest.raises(Exception):
            metrics.FalsePositives(thresholds=[-1, 0.5, 2])

        with pytest.raises(Exception):
            metrics.FalsePositives(thresholds=[None])


class TestTruePositives(object):

    def test_config(self):
        tp_obj = metrics.TruePositives(name='my_tp', thresholds=[0.4, 0.9])
        assert tp_obj.name == 'my_tp'
        assert len(tp_obj.weights) == 1
        assert tp_obj.thresholds == [0.4, 0.9]

        # Check save and restore config
        tp_obj2 = metrics.TruePositives.from_config(tp_obj.get_config())
        assert tp_obj2.name == 'my_tp'
        assert len(tp_obj2.weights) == 1
        assert tp_obj2.thresholds == [0.4, 0.9]

    def test_unweighted(self):
        tp_obj = metrics.TruePositives()

        y_true = ((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                  (1, 1, 1, 1, 0), (0, 0, 0, 0, 1))
        y_pred = ((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                  (0, 1, 0, 1, 0), (1, 1, 1, 1, 1))

        result = tp_obj(y_true, y_pred)
        assert np.allclose(7., K.eval(result))

    def test_weighted(self):
        tp_obj = metrics.TruePositives()
        y_true = ((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                  (1, 1, 1, 1, 0), (0, 0, 0, 0, 1))
        y_pred = ((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                  (0, 1, 0, 1, 0), (1, 1, 1, 1, 1))
        sample_weight = (1., 1.5, 2., 2.5)
        result = tp_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(12., K.eval(result))

    def test_unweighted_with_thresholds(self):
        tp_obj = metrics.TruePositives(thresholds=[0.15, 0.5, 0.85])

        y_pred = ((0.9, 0.2, 0.8, 0.1), (0.2, 0.9, 0.7, 0.6),
                  (0.1, 0.2, 0.4, 0.3), (0, 1, 0.7, 0.3))
        y_true = ((0, 1, 1, 0), (1, 0, 0, 0), (0, 0, 0, 0),
                  (1, 1, 1, 1))

        result = tp_obj(y_true, y_pred)
        assert np.allclose([6., 3., 1.], K.eval(result))

    def test_weighted_with_thresholds(self):
        tp_obj = metrics.TruePositives(thresholds=[0.15, 0.5, 0.85])

        y_pred = ((0.9, 0.2, 0.8, 0.1), (0.2, 0.9, 0.7, 0.6),
                  (0.1, 0.2, 0.4, 0.3), (0, 1, 0.7, 0.3))
        y_true = ((0, 1, 1, 0), (1, 0, 0, 0), (0, 0, 0, 0),
                  (1, 1, 1, 1))

        result = tp_obj(y_true, y_pred, sample_weight=37.)
        assert np.allclose([222., 111., 37.], K.eval(result))


class TestTrueNegatives(object):

    def test_config(self):
        tn_obj = metrics.TrueNegatives(name='my_tn', thresholds=[0.4, 0.9])
        assert tn_obj.name == 'my_tn'
        assert len(tn_obj.weights) == 1
        assert tn_obj.thresholds == [0.4, 0.9]

        # Check save and restore config
        tn_obj2 = metrics.TrueNegatives.from_config(tn_obj.get_config())
        assert tn_obj2.name == 'my_tn'
        assert len(tn_obj2.weights) == 1
        assert tn_obj2.thresholds == [0.4, 0.9]

    def test_unweighted(self):
        tn_obj = metrics.TrueNegatives()

        y_true = ((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                  (1, 1, 1, 1, 0), (0, 0, 0, 0, 1))
        y_pred = ((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                  (0, 1, 0, 1, 0), (1, 1, 1, 1, 1))

        result = tn_obj(y_true, y_pred)
        assert np.allclose(3., K.eval(result))

    def test_weighted(self):
        tn_obj = metrics.TrueNegatives()
        y_true = ((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                  (1, 1, 1, 1, 0), (0, 0, 0, 0, 1))
        y_pred = ((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                  (0, 1, 0, 1, 0), (1, 1, 1, 1, 1))
        sample_weight = (1., 1.5, 2., 2.5)
        result = tn_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(4., K.eval(result))

    def test_unweighted_with_thresholds(self):
        tn_obj = metrics.TrueNegatives(thresholds=[0.15, 0.5, 0.85])

        y_pred = ((0.9, 0.2, 0.8, 0.1), (0.2, 0.9, 0.7, 0.6),
                  (0.1, 0.2, 0.4, 0.3), (0, 1, 0.7, 0.3))
        y_true = ((0, 1, 1, 0), (1, 0, 0, 0), (0, 0, 0, 0), (1, 1, 1, 1))

        result = tn_obj(y_true, y_pred)
        assert np.allclose([2., 5., 7.], K.eval(result))

    def test_weighted_with_thresholds(self):
        tn_obj = metrics.TrueNegatives(thresholds=[0.15, 0.5, 0.85])

        y_pred = ((0.9, 0.2, 0.8, 0.1), (0.2, 0.9, 0.7, 0.6),
                  (0.1, 0.2, 0.4, 0.3), (0, 1, 0.7, 0.3))
        y_true = ((0, 1, 1, 0), (1, 0, 0, 0), (0, 0, 0, 0), (1, 1, 1, 1))
        sample_weight = ((0.0, 2.0, 3.0, 5.0),)

        result = tn_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose([5., 15., 23.], K.eval(result))


class TestFalseNegatives(object):

    def test_config(self):
        fn_obj = metrics.FalseNegatives(name='my_fn', thresholds=[0.4, 0.9])
        assert fn_obj.name == 'my_fn'
        assert len(fn_obj.weights) == 1
        assert fn_obj.thresholds == [0.4, 0.9]

        # Check save and restore config
        fn_obj2 = metrics.FalseNegatives.from_config(fn_obj.get_config())
        assert fn_obj2.name == 'my_fn'
        assert len(fn_obj2.weights) == 1
        assert fn_obj2.thresholds == [0.4, 0.9]

    def test_unweighted(self):
        fn_obj = metrics.FalseNegatives()

        y_true = ((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                  (1, 1, 1, 1, 0), (0, 0, 0, 0, 1))
        y_pred = ((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                  (0, 1, 0, 1, 0), (1, 1, 1, 1, 1))

        result = fn_obj(y_true, y_pred)
        assert np.allclose(3., K.eval(result))

    def test_weighted(self):
        fn_obj = metrics.FalseNegatives()
        y_true = ((0, 1, 0, 1, 0), (0, 0, 1, 1, 1),
                  (1, 1, 1, 1, 0), (0, 0, 0, 0, 1))
        y_pred = ((0, 0, 1, 1, 0), (1, 1, 1, 1, 1),
                  (0, 1, 0, 1, 0), (1, 1, 1, 1, 1))
        sample_weight = (1., 1.5, 2., 2.5)
        result = fn_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(5., K.eval(result))

    def test_unweighted_with_thresholds(self):
        fn_obj = metrics.FalseNegatives(thresholds=[0.15, 0.5, 0.85])

        y_pred = ((0.9, 0.2, 0.8, 0.1), (0.2, 0.9, 0.7, 0.6),
                  (0.1, 0.2, 0.4, 0.3), (0, 1, 0.7, 0.3))
        y_true = ((0, 1, 1, 0), (1, 0, 0, 0), (0, 0, 0, 0), (1, 1, 1, 1))

        result = fn_obj(y_true, y_pred)
        assert np.allclose([1., 4., 6.], K.eval(result))

    def test_weighted_with_thresholds(self):
        fn_obj = metrics.FalseNegatives(thresholds=[0.15, 0.5, 0.85])

        y_pred = ((0.9, 0.2, 0.8, 0.1), (0.2, 0.9, 0.7, 0.6),
                  (0.1, 0.2, 0.4, 0.3), (0, 1, 0.7, 0.3))
        y_true = ((0, 1, 1, 0), (1, 0, 0, 0), (0, 0, 0, 0), (1, 1, 1, 1))
        sample_weight = ((3.0,), (5.0,), (7.0,), (4.0,))

        result = fn_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose([4., 16., 23.], K.eval(result))


class TestSensitivityAtSpecificity(object):

    def test_config(self):
        s_obj = metrics.SensitivityAtSpecificity(
            0.4, num_thresholds=100, name='sensitivity_at_specificity_1')
        assert s_obj.name == 'sensitivity_at_specificity_1'
        assert len(s_obj.weights) == 4
        assert s_obj.specificity == 0.4
        assert s_obj.num_thresholds == 100

        # Check save and restore config
        s_obj2 = metrics.SensitivityAtSpecificity.from_config(s_obj.get_config())
        assert s_obj2.name == 'sensitivity_at_specificity_1'
        assert len(s_obj2.weights) == 4
        assert s_obj2.specificity == 0.4
        assert s_obj2.num_thresholds == 100

    def test_unweighted_all_correct(self):
        s_obj = metrics.SensitivityAtSpecificity(0.7, num_thresholds=1)
        inputs = np.random.randint(0, 2, size=(100, 1))
        y_pred = K.constant(inputs, dtype='float32')
        y_true = K.constant(inputs)
        result = s_obj(y_true, y_pred)
        assert np.isclose(1, K.eval(result))

    def test_unweighted_high_specificity(self):
        s_obj = metrics.SensitivityAtSpecificity(0.8)
        pred_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.1, 0.45, 0.5, 0.8, 0.9]
        label_values = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]

        y_pred = K.constant(pred_values, dtype='float32')
        y_true = K.constant(label_values)
        result = s_obj(y_true, y_pred)
        assert np.isclose(0.8, K.eval(result))

    def test_unweighted_low_specificity(self):
        s_obj = metrics.SensitivityAtSpecificity(0.4)
        pred_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.01, 0.02, 0.25, 0.26, 0.26]
        label_values = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]

        y_pred = K.constant(pred_values, dtype='float32')
        y_true = K.constant(label_values)
        result = s_obj(y_true, y_pred)
        assert np.isclose(0.6, K.eval(result))

    def test_weighted(self):
        s_obj = metrics.SensitivityAtSpecificity(0.4)
        pred_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.01, 0.02, 0.25, 0.26, 0.26]
        label_values = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        weight_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        y_pred = K.constant(pred_values, dtype='float32')
        y_true = K.constant(label_values, dtype='float32')
        weights = K.constant(weight_values)
        result = s_obj(y_true, y_pred, sample_weight=weights)
        assert np.isclose(0.675, K.eval(result))

    def test_invalid_specificity(self):
        with pytest.raises(Exception):
            metrics.SensitivityAtSpecificity(-1)

    def test_invalid_num_thresholds(self):
        with pytest.raises(Exception):
            metrics.SensitivityAtSpecificity(0.4, num_thresholds=-1)


class TestSpecificityAtSensitivity(object):

    def test_config(self):
        s_obj = metrics.SpecificityAtSensitivity(
            0.4, num_thresholds=100, name='specificity_at_sensitivity_1')
        assert s_obj.name == 'specificity_at_sensitivity_1'
        assert len(s_obj.weights) == 4
        assert s_obj.sensitivity == 0.4
        assert s_obj.num_thresholds == 100

        # Check save and restore config
        s_obj2 = metrics.SpecificityAtSensitivity.from_config(s_obj.get_config())
        assert s_obj2.name == 'specificity_at_sensitivity_1'
        assert len(s_obj2.weights) == 4
        assert s_obj2.sensitivity == 0.4
        assert s_obj2.num_thresholds == 100

    def test_unweighted_all_correct(self):
        s_obj = metrics.SpecificityAtSensitivity(0.7, num_thresholds=1)
        inputs = np.random.randint(0, 2, size=(100, 1))
        y_pred = K.constant(inputs, dtype='float32')
        y_true = K.constant(inputs)
        result = s_obj(y_true, y_pred)
        assert np.isclose(1, K.eval(result))

    def DISABLED_test_unweighted_high_sensitivity(self):
        s_obj = metrics.SpecificityAtSensitivity(0.8)
        pred_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.1, 0.45, 0.5, 0.8, 0.9]
        label_values = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]

        y_pred = K.constant(pred_values, dtype='float32')
        y_true = K.constant(label_values)
        result = s_obj(y_true, y_pred)
        assert np.isclose(0.4, K.eval(result))

    def test_unweighted_low_sensitivity(self):
        s_obj = metrics.SpecificityAtSensitivity(0.4)
        pred_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.01, 0.02, 0.25, 0.26, 0.26]
        label_values = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]

        y_pred = K.constant(pred_values, dtype='float32')
        y_true = K.constant(label_values)
        result = s_obj(y_true, y_pred)
        assert np.isclose(0.6, K.eval(result))

    def test_weighted(self):
        s_obj = metrics.SpecificityAtSensitivity(0.4)
        pred_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.01, 0.02, 0.25, 0.26, 0.26]
        label_values = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        weight_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        y_pred = K.constant(pred_values, dtype='float32')
        y_true = K.constant(label_values, dtype='float32')
        weights = K.constant(weight_values)
        result = s_obj(y_true, y_pred, sample_weight=weights)
        assert np.isclose(0.4, K.eval(result))

    def test_invalid_sensitivity(self):
        with pytest.raises(Exception):
            metrics.SpecificityAtSensitivity(-1)

    def test_invalid_num_thresholds(self):
        with pytest.raises(Exception):
            metrics.SpecificityAtSensitivity(0.4, num_thresholds=-1)


class TestAUC(object):

    def setup(self):
        self.num_thresholds = 3
        self.y_pred = K.constant([0, 0.5, 0.3, 0.9], dtype='float32')
        self.y_true = K.constant([0, 0, 1, 1])
        self.sample_weight = [1, 2, 3, 4]

        # threshold values are [0 - 1e-7, 0.5, 1 + 1e-7]
        # y_pred when threshold = 0 - 1e-7  : [1, 1, 1, 1]
        # y_pred when threshold = 0.5       : [0, 0, 0, 1]
        # y_pred when threshold = 1 + 1e-7  : [0, 0, 0, 0]

        # without sample_weight:
        # tp = np.sum([[0, 0, 1, 1], [0, 0, 0, 1], [0, 0, 0, 0]], axis=1)
        # fp = np.sum([[1, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], axis=1)
        # fn = np.sum([[0, 0, 0, 0], [0, 0, 1, 0], [0, 0, 1, 1]], axis=1)
        # tn = np.sum([[0, 0, 0, 0], [1, 1, 0, 0], [1, 1, 0, 0]], axis=1)

        # tp = [2, 1, 0], fp = [2, 0, 0], fn = [0, 1, 2], tn = [0, 2, 2]

        # with sample_weight:
        # tp = np.sum([[0, 0, 3, 4], [0, 0, 0, 4], [0, 0, 0, 0]], axis=1)
        # fp = np.sum([[1, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], axis=1)
        # fn = np.sum([[0, 0, 0, 0], [0, 0, 3, 0], [0, 0, 3, 4]], axis=1)
        # tn = np.sum([[0, 0, 0, 0], [1, 2, 0, 0], [1, 2, 0, 0]], axis=1)

        # tp = [7, 4, 0], fp = [3, 0, 0], fn = [0, 3, 7], tn = [0, 3, 3]

    def test_config(self):
        auc_obj = metrics.AUC(
            num_thresholds=100,
            curve='PR',
            summation_method='majoring',
            name='auc_1')
        assert auc_obj.name == 'auc_1'
        assert len(auc_obj.weights) == 4
        assert auc_obj.num_thresholds == 100
        assert auc_obj.curve == metrics_utils.AUCCurve.PR
        assert auc_obj.summation_method == metrics_utils.AUCSummationMethod.MAJORING

        # Check save and restore config.
        auc_obj2 = metrics.AUC.from_config(auc_obj.get_config())
        assert auc_obj2.name == 'auc_1'
        assert len(auc_obj2.weights) == 4
        assert auc_obj2.num_thresholds == 100
        assert auc_obj2.curve == metrics_utils.AUCCurve.PR
        assert auc_obj2.summation_method == metrics_utils.AUCSummationMethod.MAJORING

    def test_config_manual_thresholds(self):
        auc_obj = metrics.AUC(
            num_thresholds=None,
            curve='PR',
            summation_method='majoring',
            name='auc_1',
            thresholds=[0.3, 0.5])
        assert auc_obj.name == 'auc_1'
        assert len(auc_obj.weights) == 4
        assert auc_obj.num_thresholds == 4
        assert np.allclose(auc_obj.thresholds, [0.0, 0.3, 0.5, 1.0], atol=1e-3)
        assert auc_obj.curve == metrics_utils.AUCCurve.PR
        assert auc_obj.summation_method == metrics_utils.AUCSummationMethod.MAJORING

        # Check save and restore config.
        auc_obj2 = metrics.AUC.from_config(auc_obj.get_config())
        assert auc_obj2.name == 'auc_1'
        assert len(auc_obj2.weights) == 4
        assert auc_obj2.num_thresholds == 4
        assert auc_obj2.curve == metrics_utils.AUCCurve.PR
        assert auc_obj2.summation_method == metrics_utils.AUCSummationMethod.MAJORING

    def test_unweighted_all_correct(self):
        self.setup()
        auc_obj = metrics.AUC()
        result = auc_obj(self.y_true, self.y_true)
        assert K.eval(result) == 1

    def test_unweighted(self):
        self.setup()
        auc_obj = metrics.AUC(num_thresholds=self.num_thresholds)
        result = auc_obj(self.y_true, self.y_pred)

        # tp = [2, 1, 0], fp = [2, 0, 0], fn = [0, 1, 2], tn = [0, 2, 2]
        # recall = [2/2, 1/(1+1), 0] = [1, 0.5, 0]
        # fp_rate = [2/2, 0, 0] = [1, 0, 0]
        # heights = [(1 + 0.5)/2, (0.5 + 0)/2] = [0.75, 0.25]
        # widths = [(1 - 0), (0 - 0)] = [1, 0]
        expected_result = (0.75 * 1 + 0.25 * 0)
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_manual_thresholds(self):
        self.setup()
        # Verify that when specified, thresholds are used instead of num_thresholds.
        auc_obj = metrics.AUC(num_thresholds=2, thresholds=[0.5])
        assert auc_obj.num_thresholds == 3
        assert np.allclose(auc_obj.thresholds, [0.0, 0.5, 1.0], atol=1e-3)
        result = auc_obj(self.y_true, self.y_pred)

        # tp = [2, 1, 0], fp = [2, 0, 0], fn = [0, 1, 2], tn = [0, 2, 2]
        # recall = [2/2, 1/(1+1), 0] = [1, 0.5, 0]
        # fp_rate = [2/2, 0, 0] = [1, 0, 0]
        # heights = [(1 + 0.5)/2, (0.5 + 0)/2] = [0.75, 0.25]
        # widths = [(1 - 0), (0 - 0)] = [1, 0]
        expected_result = (0.75 * 1 + 0.25 * 0)
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_weighted_roc_interpolation(self):
        self.setup()
        auc_obj = metrics.AUC(num_thresholds=self.num_thresholds)
        result = auc_obj(self.y_true, self.y_pred, sample_weight=self.sample_weight)

        # tp = [7, 4, 0], fp = [3, 0, 0], fn = [0, 3, 7], tn = [0, 3, 3]
        # recall = [7/7, 4/(4+3), 0] = [1, 0.571, 0]
        # fp_rate = [3/3, 0, 0] = [1, 0, 0]
        # heights = [(1 + 0.571)/2, (0.571 + 0)/2] = [0.7855, 0.2855]
        # widths = [(1 - 0), (0 - 0)] = [1, 0]
        expected_result = (0.7855 * 1 + 0.2855 * 0)
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_weighted_roc_majoring(self):
        self.setup()
        auc_obj = metrics.AUC(
            num_thresholds=self.num_thresholds, summation_method='majoring')
        result = auc_obj(self.y_true, self.y_pred, sample_weight=self.sample_weight)

        # tp = [7, 4, 0], fp = [3, 0, 0], fn = [0, 3, 7], tn = [0, 3, 3]
        # recall = [7/7, 4/(4+3), 0] = [1, 0.571, 0]
        # fp_rate = [3/3, 0, 0] = [1, 0, 0]
        # heights = [max(1, 0.571), max(0.571, 0)] = [1, 0.571]
        # widths = [(1 - 0), (0 - 0)] = [1, 0]
        expected_result = (1 * 1 + 0.571 * 0)
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_weighted_roc_minoring(self):
        self.setup()
        auc_obj = metrics.AUC(
            num_thresholds=self.num_thresholds, summation_method='minoring')
        result = auc_obj(self.y_true, self.y_pred, sample_weight=self.sample_weight)

        # tp = [7, 4, 0], fp = [3, 0, 0], fn = [0, 3, 7], tn = [0, 3, 3]
        # recall = [7/7, 4/(4+3), 0] = [1, 0.571, 0]
        # fp_rate = [3/3, 0, 0] = [1, 0, 0]
        # heights = [min(1, 0.571), min(0.571, 0)] = [0.571, 0]
        # widths = [(1 - 0), (0 - 0)] = [1, 0]
        expected_result = (0.571 * 1 + 0 * 0)
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_weighted_pr_majoring(self):
        self.setup()
        auc_obj = metrics.AUC(
            num_thresholds=self.num_thresholds,
            curve='PR',
            summation_method='majoring')
        result = auc_obj(self.y_true, self.y_pred, sample_weight=self.sample_weight)

        # tp = [7, 4, 0], fp = [3, 0, 0], fn = [0, 3, 7], tn = [0, 3, 3]
        # precision = [7/(7+3), 4/4, 0] = [0.7, 1, 0]
        # recall = [7/7, 4/(4+3), 0] = [1, 0.571, 0]
        # heights = [max(0.7, 1), max(1, 0)] = [1, 1]
        # widths = [(1 - 0.571), (0.571 - 0)] = [0.429, 0.571]
        expected_result = (1 * 0.429 + 1 * 0.571)
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_weighted_pr_minoring(self):
        self.setup()
        auc_obj = metrics.AUC(
            num_thresholds=self.num_thresholds,
            curve='PR',
            summation_method='minoring')
        result = auc_obj(self.y_true, self.y_pred, sample_weight=self.sample_weight)

        # tp = [7, 4, 0], fp = [3, 0, 0], fn = [0, 3, 7], tn = [0, 3, 3]
        # precision = [7/(7+3), 4/4, 0] = [0.7, 1, 0]
        # recall = [7/7, 4/(4+3), 0] = [1, 0.571, 0]
        # heights = [min(0.7, 1), min(1, 0)] = [0.7, 0]
        # widths = [(1 - 0.571), (0.571 - 0)] = [0.429, 0.571]
        expected_result = (0.7 * 0.429 + 0 * 0.571)
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_weighted_pr_interpolation(self):
        self.setup()
        auc_obj = metrics.AUC(num_thresholds=self.num_thresholds, curve='PR')
        result = auc_obj(self.y_true, self.y_pred, sample_weight=self.sample_weight)

        # auc = (slope / Total Pos) * [dTP - intercept * log(Pb/Pa)]

        # tp = [7, 4, 0], fp = [3, 0, 0], fn = [0, 3, 7], tn = [0, 3, 3]
        # P = tp + fp = [10, 4, 0]
        # dTP = [7-4, 4-0] = [3, 4]
        # dP = [10-4, 4-0] = [6, 4]
        # slope = dTP/dP = [0.5, 1]
        # intercept = (TPa+(slope*Pa) = [(4 - 0.5*4), (0 - 1*0)] = [2, 0]
        # (Pb/Pa) = (Pb/Pa) if Pb > 0 AND Pa > 0 else 1 = [10/4, 4/0] = [2.5, 1]
        # auc * TotalPos = [(0.5 * (3 + 2 * log(2.5))), (1 * (4 + 0))]
        #                = [2.416, 4]
        # auc = [2.416, 4]/(tp[1:]+fn[1:])
        # expected_result = (2.416 / 7 + 4 / 7)
        expected_result = 0.345 + 0.571
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_invalid_num_thresholds(self):
        with pytest.raises(Exception):
            metrics.AUC(num_thresholds=-1)

        with pytest.raises(Exception):
            metrics.AUC(num_thresholds=1)

    def test_invalid_curve(self):
        with pytest.raises(Exception):
            metrics.AUC(curve='Invalid')

    def test_invalid_summation_method(self):
        with pytest.raises(Exception):
            metrics.AUC(summation_method='Invalid')


class TestPrecisionTest(object):

    def test_config(self):
        p_obj = metrics.Precision(
            name='my_precision', thresholds=[0.4, 0.9], top_k=15, class_id=12)
        assert p_obj.name == 'my_precision'
        assert len(p_obj.weights) == 2
        assert ([v.name for v in p_obj.weights] ==
                ['true_positives:0', 'false_positives:0'])
        assert p_obj.thresholds == [0.4, 0.9]
        assert p_obj.top_k == 15
        assert p_obj.class_id == 12

        # Check save and restore config
        p_obj2 = metrics.Precision.from_config(p_obj.get_config())
        assert p_obj2.name == 'my_precision'
        assert len(p_obj2.weights) == 2
        assert p_obj2.thresholds == [0.4, 0.9]
        assert p_obj2.top_k == 15
        assert p_obj2.class_id == 12

    def test_unweighted(self):
        p_obj = metrics.Precision()
        y_pred = K.constant([1, 0, 1, 0], shape=(1, 4))
        y_true = K.constant([0, 1, 1, 0], shape=(1, 4))
        result = p_obj(y_true, y_pred)
        assert np.isclose(0.5, K.eval(result))

    def test_unweighted_all_incorrect(self):
        p_obj = metrics.Precision(thresholds=[0.5])
        inputs = np.random.randint(0, 2, size=(100, 1))
        y_pred = K.constant(inputs)
        y_true = K.constant(1 - inputs)
        result = p_obj(y_true, y_pred)
        assert np.isclose(0, K.eval(result))

    def test_weighted(self):
        p_obj = metrics.Precision()
        y_pred = K.constant([[1, 0, 1, 0], [1, 0, 1, 0]])
        y_true = K.constant([[0, 1, 1, 0], [1, 0, 0, 1]])
        result = p_obj(
            y_true,
            y_pred,
            sample_weight=K.constant([[1, 2, 3, 4], [4, 3, 2, 1]]))
        weighted_tp = 3.0 + 4.0
        weighted_positives = (1.0 + 3.0) + (4.0 + 2.0)
        expected_precision = weighted_tp / weighted_positives
        assert np.isclose(expected_precision, K.eval(result))

    def test_unweighted_with_threshold(self):
        p_obj = metrics.Precision(thresholds=[0.5, 0.7])
        y_pred = K.constant([1, 0, 0.6, 0], shape=(1, 4))
        y_true = K.constant([0, 1, 1, 0], shape=(1, 4))
        result = p_obj(y_true, y_pred)
        assert np.allclose([0.5, 0.], K.eval(result), 0)

    def test_weighted_with_threshold(self):
        p_obj = metrics.Precision(thresholds=[0.5, 1.])
        y_true = K.constant([[0, 1], [1, 0]], shape=(2, 2))
        y_pred = K.constant([[1, 0], [0.6, 0]],
                            shape=(2, 2),
                            dtype='float32')
        weights = K.constant([[4, 0], [3, 1]],
                             shape=(2, 2),
                             dtype='float32')
        result = p_obj(y_true, y_pred, sample_weight=weights)
        weighted_tp = 0 + 3.
        weighted_positives = (0 + 3.) + (4. + 0.)
        expected_precision = weighted_tp / weighted_positives
        assert np.allclose([expected_precision, 0], K.eval(result), 1e-3)

    def test_unweighted_top_k(self):
        p_obj = metrics.Precision(top_k=3)
        y_pred = K.constant([0.2, 0.1, 0.5, 0, 0.2], shape=(1, 5))
        y_true = K.constant([0, 1, 1, 0, 0], shape=(1, 5))
        result = p_obj(y_true, y_pred)
        assert np.isclose(1. / 3, K.eval(result))

    def test_weighted_top_k(self):
        p_obj = metrics.Precision(top_k=3)
        y_pred1 = K.constant([0.2, 0.1, 0.4, 0, 0.2], shape=(1, 5))
        y_true1 = K.constant([0, 1, 1, 0, 1], shape=(1, 5))
        K.eval(
            p_obj(
                y_true1,
                y_pred1,
                sample_weight=K.constant([[1, 4, 2, 3, 5]])))

        y_pred2 = K.constant([0.2, 0.6, 0.4, 0.2, 0.2], shape=(1, 5))
        y_true2 = K.constant([1, 0, 1, 1, 1], shape=(1, 5))
        result = p_obj(y_true2, y_pred2, sample_weight=K.constant(3))

        tp = (2 + 5) + (3 + 3)
        predicted_positives = (1 + 2 + 5) + (3 + 3 + 3)
        expected_precision = float(tp) / predicted_positives
        assert np.isclose(expected_precision, K.eval(result))

    def test_unweighted_class_id(self):
        p_obj = metrics.Precision(class_id=2)

        y_pred = K.constant([0.2, 0.1, 0.6, 0, 0.2], shape=(1, 5))
        y_true = K.constant([0, 1, 1, 0, 0], shape=(1, 5))
        result = p_obj(y_true, y_pred)
        assert np.isclose(1, K.eval(result))
        assert np.isclose(1, K.eval(p_obj.true_positives))
        assert np.isclose(0, K.eval(p_obj.false_positives))

        y_pred = K.constant([0.2, 0.1, 0, 0, 0.2], shape=(1, 5))
        y_true = K.constant([0, 1, 1, 0, 0], shape=(1, 5))
        result = p_obj(y_true, y_pred)
        assert np.isclose(1, K.eval(result))
        assert np.isclose(1, K.eval(p_obj.true_positives))
        assert np.isclose(0, K.eval(p_obj.false_positives))

        y_pred = K.constant([0.2, 0.1, 0.6, 0, 0.2], shape=(1, 5))
        y_true = K.constant([0, 1, 0, 0, 0], shape=(1, 5))
        result = p_obj(y_true, y_pred)
        assert np.isclose(0.5, K.eval(result))
        assert np.isclose(1, K.eval(p_obj.true_positives))
        assert np.isclose(1, K.eval(p_obj.false_positives))

    def test_unweighted_top_k_and_class_id(self):
        p_obj = metrics.Precision(class_id=2, top_k=2)

        y_pred = K.constant([0.2, 0.6, 0.3, 0, 0.2], shape=(1, 5))
        y_true = K.constant([0, 1, 1, 0, 0], shape=(1, 5))
        result = p_obj(y_true, y_pred)
        assert np.isclose(1, K.eval(result))
        assert np.isclose(1, K.eval(p_obj.true_positives))
        assert np.isclose(0, K.eval(p_obj.false_positives))

        y_pred = K.constant([1, 1, 0.9, 1, 1], shape=(1, 5))
        y_true = K.constant([0, 1, 1, 0, 0], shape=(1, 5))
        result = p_obj(y_true, y_pred)
        assert np.isclose(1, K.eval(result))
        assert np.isclose(1, K.eval(p_obj.true_positives))
        assert np.isclose(0, K.eval(p_obj.false_positives))

    def test_unweighted_top_k_and_threshold(self):
        p_obj = metrics.Precision(thresholds=.7, top_k=2)

        y_pred = K.constant([0.2, 0.8, 0.6, 0, 0.2], shape=(1, 5))
        y_true = K.constant([0, 1, 1, 0, 1], shape=(1, 5))
        result = p_obj(y_true, y_pred)
        assert np.isclose(1, K.eval(result))
        assert np.isclose(1, K.eval(p_obj.true_positives))
        assert np.isclose(0, K.eval(p_obj.false_positives))


class TestRecall(object):

    def test_config(self):
        r_obj = metrics.Recall(
            name='my_recall', thresholds=[0.4, 0.9], top_k=15, class_id=12)
        assert r_obj.name == 'my_recall'
        assert len(r_obj.weights) == 2
        assert ([v.name for v in r_obj.weights] ==
                ['true_positives:0', 'false_negatives:0'])
        assert r_obj.thresholds == [0.4, 0.9]
        assert r_obj.top_k == 15
        assert r_obj.class_id == 12

        # Check save and restore config
        r_obj2 = metrics.Recall.from_config(r_obj.get_config())
        assert r_obj2.name == 'my_recall'
        assert len(r_obj2.weights) == 2
        assert r_obj2.thresholds == [0.4, 0.9]
        assert r_obj2.top_k == 15
        assert r_obj2.class_id == 12

    def test_unweighted(self):
        r_obj = metrics.Recall()
        y_pred = K.constant([1, 0, 1, 0], shape=(1, 4))
        y_true = K.constant([0, 1, 1, 0], shape=(1, 4))
        result = r_obj(y_true, y_pred)
        assert np.isclose(0.5, K.eval(result))

    def test_unweighted_all_incorrect(self):
        r_obj = metrics.Recall(thresholds=[0.5])
        inputs = np.random.randint(0, 2, size=(100, 1))
        y_pred = K.constant(inputs)
        y_true = K.constant(1 - inputs)
        result = r_obj(y_true, y_pred)
        assert np.isclose(0, K.eval(result))

    def test_weighted(self):
        r_obj = metrics.Recall()
        y_pred = K.constant([[1, 0, 1, 0], [0, 1, 0, 1]])
        y_true = K.constant([[0, 1, 1, 0], [1, 0, 0, 1]])
        result = r_obj(
            y_true,
            y_pred,
            sample_weight=K.constant([[1, 2, 3, 4], [4, 3, 2, 1]]))
        weighted_tp = 3.0 + 1.0
        weighted_t = (2.0 + 3.0) + (4.0 + 1.0)
        expected_recall = weighted_tp / weighted_t
        assert np.isclose(expected_recall, K.eval(result))

    def test_unweighted_with_threshold(self):
        r_obj = metrics.Recall(thresholds=[0.5, 0.7])
        y_pred = K.constant([1, 0, 0.6, 0], shape=(1, 4))
        y_true = K.constant([0, 1, 1, 0], shape=(1, 4))
        result = r_obj(y_true, y_pred)
        assert np.allclose([0.5, 0.], K.eval(result), 0)

    def test_weighted_with_threshold(self):
        r_obj = metrics.Recall(thresholds=[0.5, 1.])
        y_true = K.constant([[0, 1], [1, 0]], shape=(2, 2))
        y_pred = K.constant([[1, 0], [0.6, 0]],
                            shape=(2, 2),
                            dtype='float32')
        weights = K.constant([[1, 4], [3, 2]],
                             shape=(2, 2),
                             dtype='float32')
        result = r_obj(y_true, y_pred, sample_weight=weights)
        weighted_tp = 0 + 3.
        weighted_positives = (0 + 3.) + (4. + 0.)
        expected_recall = weighted_tp / weighted_positives
        assert np.allclose([expected_recall, 0], K.eval(result), 1e-3)

    def test_unweighted_top_k(self):
        r_obj = metrics.Recall(top_k=3)
        y_pred = K.constant([0.2, 0.1, 0.5, 0, 0.2], shape=(1, 5))
        y_true = K.constant([0, 1, 1, 0, 0], shape=(1, 5))
        result = r_obj(y_true, y_pred)
        assert np.isclose(0.5, K.eval(result))

    def test_weighted_top_k(self):
        r_obj = metrics.Recall(top_k=3)
        y_pred1 = K.constant([0.2, 0.1, 0.4, 0, 0.2], shape=(1, 5))
        y_true1 = K.constant([0, 1, 1, 0, 1], shape=(1, 5))
        K.eval(
            r_obj(
                y_true1,
                y_pred1,
                sample_weight=K.constant([[1, 4, 2, 3, 5]])))

        y_pred2 = K.constant([0.2, 0.6, 0.4, 0.2, 0.2], shape=(1, 5))
        y_true2 = K.constant([1, 0, 1, 1, 1], shape=(1, 5))
        result = r_obj(y_true2, y_pred2, sample_weight=K.constant(3))

        tp = (2 + 5) + (3 + 3)
        positives = (4 + 2 + 5) + (3 + 3 + 3 + 3)
        expected_recall = float(tp) / positives
        assert np.isclose(expected_recall, K.eval(result))

    def test_unweighted_class_id(self):
        r_obj = metrics.Recall(class_id=2)

        y_pred = K.constant([0.2, 0.1, 0.6, 0, 0.2], shape=(1, 5))
        y_true = K.constant([0, 1, 1, 0, 0], shape=(1, 5))
        result = r_obj(y_true, y_pred)
        assert np.isclose(1, K.eval(result))
        assert np.isclose(1, K.eval(r_obj.true_positives))
        assert np.isclose(0, K.eval(r_obj.false_negatives))

        y_pred = K.constant([0.2, 0.1, 0, 0, 0.2], shape=(1, 5))
        y_true = K.constant([0, 1, 1, 0, 0], shape=(1, 5))
        result = r_obj(y_true, y_pred)
        assert np.isclose(0.5, K.eval(result))
        assert np.isclose(1, K.eval(r_obj.true_positives))
        assert np.isclose(1, K.eval(r_obj.false_negatives))

        y_pred = K.constant([0.2, 0.1, 0.6, 0, 0.2], shape=(1, 5))
        y_true = K.constant([0, 1, 0, 0, 0], shape=(1, 5))
        result = r_obj(y_true, y_pred)
        assert np.isclose(0.5, K.eval(result))
        assert np.isclose(1, K.eval(r_obj.true_positives))
        assert np.isclose(1, K.eval(r_obj.false_negatives))

    def test_unweighted_top_k_and_class_id(self):
        r_obj = metrics.Recall(class_id=2, top_k=2)

        y_pred = K.constant([0.2, 0.6, 0.3, 0, 0.2], shape=(1, 5))
        y_true = K.constant([0, 1, 1, 0, 0], shape=(1, 5))
        result = r_obj(y_true, y_pred)
        assert np.isclose(1, K.eval(result))
        assert np.isclose(1, K.eval(r_obj.true_positives))
        assert np.isclose(0, K.eval(r_obj.false_negatives))

        y_pred = K.constant([1, 1, 0.9, 1, 1], shape=(1, 5))
        y_true = K.constant([0, 1, 1, 0, 0], shape=(1, 5))
        result = r_obj(y_true, y_pred)
        assert np.isclose(0.5, K.eval(result))
        assert np.isclose(1, K.eval(r_obj.true_positives))
        assert np.isclose(1, K.eval(r_obj.false_negatives))

    def test_unweighted_top_k_and_threshold(self):
        r_obj = metrics.Recall(thresholds=.7, top_k=2)

        y_pred = K.constant([0.2, 0.8, 0.6, 0, 0.2], shape=(1, 5))
        y_true = K.constant([1, 1, 1, 0, 1], shape=(1, 5))
        result = r_obj(y_true, y_pred)
        assert np.isclose(0.25, K.eval(result))
        assert np.isclose(1, K.eval(r_obj.true_positives))
        assert np.isclose(3, K.eval(r_obj.false_negatives))


@pytest.mark.skipif(not tf.__version__.startswith('2.'),
                    reason='Requires TF 2')
class TestMeanIoU(object):

    def test_config(self):
        m_obj = metrics.MeanIoU(num_classes=2, name='mean_iou')
        assert m_obj.name == 'mean_iou'
        assert m_obj.num_classes == 2

        m_obj2 = metrics.MeanIoU.from_config(m_obj.get_config())
        assert m_obj2.name == 'mean_iou'
        assert m_obj2.num_classes == 2

    def test_unweighted(self):
        y_pred = K.constant([0, 1, 0, 1], shape=(1, 4))
        y_true = K.constant([0, 0, 1, 1], shape=(1, 4))

        m_obj = metrics.MeanIoU(num_classes=2)
        result = m_obj(y_true, y_pred)

        # cm = [[1, 1],
        #       [1, 1]]
        # sum_row = [2, 2], sum_col = [2, 2], true_positives = [1, 1]
        # iou = true_positives / (sum_row + sum_col - true_positives))
        expected_result = (1. / (2 + 2 - 1) + 1. / (2 + 2 - 1)) / 2
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_weighted(self):
        y_pred = K.constant([0, 1, 0, 1], dtype='float32')
        y_true = K.constant([0, 0, 1, 1])
        sample_weight = K.constant([0.2, 0.3, 0.4, 0.1])

        m_obj = metrics.MeanIoU(num_classes=2)
        result = m_obj(y_true, y_pred, sample_weight=sample_weight)

        # cm = [[0.2, 0.3],
        #       [0.4, 0.1]]
        # sum_row = [0.6, 0.4], sum_col = [0.5, 0.5], true_positives = [0.2, 0.1]
        # iou = true_positives / (sum_row + sum_col - true_positives))
        expected_result = (0.2 / (0.6 + 0.5 - 0.2) + 0.1 / (0.4 + 0.5 - 0.1)) / 2
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_multi_dim_input(self):
        y_pred = K.constant([[0, 1], [0, 1]], dtype='float32')
        y_true = K.constant([[0, 0], [1, 1]])
        sample_weight = K.constant([[0.2, 0.3], [0.4, 0.1]])

        m_obj = metrics.MeanIoU(num_classes=2)
        result = m_obj(y_true, y_pred, sample_weight=sample_weight)

        # cm = [[0.2, 0.3],
        #       [0.4, 0.1]]
        # sum_row = [0.6, 0.4], sum_col = [0.5, 0.5], true_positives = [0.2, 0.1]
        # iou = true_positives / (sum_row + sum_col - true_positives))
        expected_result = (0.2 / (0.6 + 0.5 - 0.2) + 0.1 / (0.4 + 0.5 - 0.1)) / 2
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

    def test_zero_valid_entries(self):
        m_obj = metrics.MeanIoU(num_classes=2)
        assert np.allclose(K.eval(m_obj.result()), 0, atol=1e-3)

    def test_zero_and_non_zero_entries(self):
        y_pred = K.constant([1], dtype='float32')
        y_true = K.constant([1])

        m_obj = metrics.MeanIoU(num_classes=2)
        result = m_obj(y_true, y_pred)

        # cm = [[0, 0],
        #       [0, 1]]
        # sum_row = [0, 1], sum_col = [0, 1], true_positives = [0, 1]
        # iou = true_positives / (sum_row + sum_col - true_positives))
        expected_result = (0. + 1. / (1 + 1 - 1)) / 1
        assert np.allclose(K.eval(result), expected_result, atol=1e-3)

import pytest
import numpy as np

import keras
from keras import losses
from keras.losses import Reduction
from keras import backend as K
from keras.utils import custom_object_scope


all_functions = [losses.mean_squared_error,
                 losses.mean_absolute_error,
                 losses.mean_absolute_percentage_error,
                 losses.mean_squared_logarithmic_error,
                 losses.squared_hinge,
                 losses.hinge,
                 losses.categorical_crossentropy,
                 losses.binary_crossentropy,
                 losses.kullback_leibler_divergence,
                 losses.poisson,
                 losses.cosine_similarity,
                 losses.logcosh,
                 losses.categorical_hinge]
all_classes = [
    losses.Hinge,
    losses.SquaredHinge,
    losses.CategoricalHinge,
    losses.Poisson,
    losses.LogCosh,
    losses.KLDivergence,
    losses.Huber,
    # losses.SparseCategoricalCrossentropy,
    losses.BinaryCrossentropy,
    losses.MeanSquaredLogarithmicError,
    losses.MeanAbsolutePercentageError,
    losses.MeanAbsoluteError,
    losses.MeanSquaredError,
]


class MSE_MAE_loss(losses.Loss):
    """Loss function with internal state, for testing serialization code."""

    def __init__(self, mse_fraction):
        self.mse_fraction = mse_fraction
        super(MSE_MAE_loss, self).__init__()

    def __call__(self, y_true, y_pred, sample_weight=None):
        return (self.mse_fraction * losses.mse(y_true, y_pred) +
                (1 - self.mse_fraction) * losses.mae(y_true, y_pred))

    def get_config(self):
        return {'mse_fraction': self.mse_fraction}


class TestLossFunctions(object):

    @pytest.mark.parametrize('loss_fn', all_functions)
    def test_objective_shapes_3d(self, loss_fn):
        y_a = K.variable(np.random.random((5, 6, 7)))
        y_b = K.variable(np.random.random((5, 6, 7)))
        objective_output = loss_fn(y_a, y_b)
        assert K.eval(objective_output).shape == (5, 6)

    @pytest.mark.parametrize('loss_fn', all_functions)
    def test_objective_shapes_2d(self, loss_fn):
        y_a = K.variable(np.random.random((6, 7)))
        y_b = K.variable(np.random.random((6, 7)))
        objective_output = loss_fn(y_a, y_b)
        assert K.eval(objective_output).shape == (6,)

    def test_cce_one_hot(self):
        y_a = K.variable(np.random.randint(0, 7, (5, 6)))
        y_b = K.variable(np.random.random((5, 6, 7)))
        objective_output = losses.sparse_categorical_crossentropy(y_a, y_b)
        assert K.eval(objective_output).shape == (5, 6)

        y_a = K.variable(np.random.randint(0, 7, (6,)))
        y_b = K.variable(np.random.random((6, 7)))
        assert K.eval(losses.sparse_categorical_crossentropy(y_a, y_b)).shape == (6,)

    def test_categorical_hinge(self):
        y_pred = K.variable(np.array([[0.3, 0.2, 0.1],
                                      [0.1, 0.2, 0.7]]))
        y_true = K.variable(np.array([[0, 1, 0],
                                      [1, 0, 0]]))
        expected_loss = ((0.3 - 0.2 + 1) + (0.7 - 0.1 + 1)) / 2.0
        loss = K.eval(losses.categorical_hinge(y_true, y_pred))
        assert np.isclose(expected_loss, np.mean(loss))

    def test_sparse_categorical_crossentropy(self):
        y_pred = K.variable(np.array([[0.3, 0.6, 0.1],
                                      [0.1, 0.2, 0.7]]))
        y_true = K.variable(np.array([1, 2]))
        expected_loss = - (np.log(0.6) + np.log(0.7)) / 2
        loss = K.eval(losses.sparse_categorical_crossentropy(y_true, y_pred))
        assert np.isclose(expected_loss, np.mean(loss))

    def test_sparse_categorical_crossentropy_4d(self):
        y_pred = K.variable(np.array([[[[0.7, 0.1, 0.2],
                                        [0.0, 0.3, 0.7],
                                        [0.1, 0.1, 0.8]],
                                       [[0.3, 0.7, 0.0],
                                        [0.3, 0.4, 0.3],
                                        [0.2, 0.5, 0.3]],
                                       [[0.8, 0.1, 0.1],
                                        [1.0, 0.0, 0.0],
                                        [0.4, 0.3, 0.3]]]]))
        y_true = K.variable(np.array([[[0, 1, 0],
                                       [2, 1, 0],
                                       [2, 2, 1]]]))
        expected_loss = - (np.log(0.7) + np.log(0.3) + np.log(0.1) +
                           np.log(K.epsilon()) + np.log(0.4) + np.log(0.2) +
                           np.log(0.1) + np.log(K.epsilon()) + np.log(0.3)) / 9
        loss = K.eval(losses.sparse_categorical_crossentropy(y_true, y_pred))
        assert np.isclose(expected_loss, np.mean(loss))

    def test_serializing_loss_class(self):
        orig_loss_class = MSE_MAE_loss(0.3)
        with custom_object_scope({'MSE_MAE_loss': MSE_MAE_loss}):
            serialized = losses.serialize(orig_loss_class)

        with custom_object_scope({'MSE_MAE_loss': MSE_MAE_loss}):
            deserialized = losses.deserialize(serialized)
        assert isinstance(deserialized, MSE_MAE_loss)
        assert deserialized.mse_fraction == 0.3

    def test_serializing_model_with_loss_class(self, tmpdir):
        model_filename = str(tmpdir / 'custom_loss.hdf')

        with custom_object_scope({'MSE_MAE_loss': MSE_MAE_loss}):
            loss = MSE_MAE_loss(0.3)
            inputs = keras.layers.Input((2,))
            outputs = keras.layers.Dense(1, name='model_output')(inputs)
            model = keras.models.Model(inputs, outputs)
            model.compile(optimizer='sgd', loss={'model_output': loss})
            model.fit(np.random.rand(256, 2), np.random.rand(256, 1))
            model.save(model_filename)

        with custom_object_scope({'MSE_MAE_loss': MSE_MAE_loss}):
            loaded_model = keras.models.load_model(model_filename)
            loaded_model.predict(np.random.rand(128, 2))


skipif_not_tf = pytest.mark.skipif(
    K.backend() != 'tensorflow',
    reason='Need TensorFlow to __call__ a loss')


class TestLossClasses(object):

    @pytest.mark.parametrize('cls', all_classes)
    def test_objective_shapes_3d(self, cls):
        y_a = K.variable(np.random.random((5, 6, 7)))
        y_b = K.variable(np.random.random((5, 6, 7)))
        sw = K.variable(np.random.random((5, 6)))
        obj_fn = cls(name='test')
        objective_output = obj_fn(y_a, y_b, sample_weight=sw)
        assert K.eval(objective_output).shape == ()

    @pytest.mark.parametrize('cls', all_classes)
    def test_objective_shapes_2d(self, cls):
        y_a = K.variable(np.random.random((6, 7)))
        y_b = K.variable(np.random.random((6, 7)))
        sw = K.variable(np.random.random((6,)))
        obj_fn = cls(name='test')
        objective_output = obj_fn(y_a, y_b, sample_weight=sw)
        assert K.eval(objective_output).shape == ()


@skipif_not_tf
class TestMeanSquaredError:

    def test_config(self):
        mse_obj = losses.MeanSquaredError(
            reduction=Reduction.SUM, name='mse_1')
        assert mse_obj.name == 'mse_1'
        assert mse_obj.reduction == Reduction.SUM

    def test_all_correct_unweighted(self):
        mse_obj = losses.MeanSquaredError()
        y_true = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mse_obj(y_true, y_true)
        assert np.isclose(K.eval(loss), 0.0)

    def test_unweighted(self):
        mse_obj = losses.MeanSquaredError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mse_obj(y_true, y_pred)
        assert np.isclose(K.eval(loss), 49.5, atol=1e-3)

    def test_scalar_weighted(self):
        mse_obj = losses.MeanSquaredError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mse_obj(y_true, y_pred, sample_weight=2.3)
        assert np.isclose(K.eval(loss), 113.85, atol=1e-3)

    def test_sample_weighted(self):
        mse_obj = losses.MeanSquaredError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        sample_weight = K.constant([1.2, 3.4], shape=(2, 1))
        loss = mse_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.isclose(K.eval(loss), 767.8 / 6, atol=1e-3)

    def test_timestep_weighted(self):
        mse_obj = losses.MeanSquaredError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3, 1))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3, 1))
        sample_weight = K.constant([3, 6, 5, 0, 4, 2], shape=(2, 3))
        loss = mse_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.isclose(K.eval(loss), 97.833, atol=1e-3)

    def test_zero_weighted(self):
        mse_obj = losses.MeanSquaredError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mse_obj(y_true, y_pred, sample_weight=0)
        assert np.isclose(K.eval(loss), 0.0)

    def test_invalid_sample_weight(self):
        mse_obj = losses.MeanSquaredError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3, 1))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3, 1))
        sample_weight = K.constant([3, 6, 5, 0], shape=(2, 2))
        with pytest.raises(Exception):
            mse_obj(y_true, y_pred, sample_weight=sample_weight)

    def test_no_reduction(self):
        mse_obj = losses.MeanSquaredError(
            reduction=Reduction.NONE)
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mse_obj(y_true, y_pred, sample_weight=2.3)
        assert np.allclose(K.eval(loss), [84.3333, 143.3666], atol=1e-3)

    def test_sum_reduction(self):
        mse_obj = losses.MeanSquaredError(
            reduction=Reduction.SUM)
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mse_obj(y_true, y_pred, sample_weight=2.3)
        assert np.isclose(K.eval(loss), 227.69998, atol=1e-3)


@skipif_not_tf
class TestMeanAbsoluteError(object):

    def test_config(self):
        mae_obj = losses.MeanAbsoluteError(
            reduction=Reduction.SUM, name='mae_1')
        assert mae_obj.name == 'mae_1'
        assert mae_obj.reduction == Reduction.SUM

    def test_all_correct_unweighted(self):
        mae_obj = losses.MeanAbsoluteError()
        y_true = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mae_obj(y_true, y_true)
        assert np.isclose(K.eval(loss), 0.0, atol=1e-3)

    def test_unweighted(self):
        mae_obj = losses.MeanAbsoluteError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mae_obj(y_true, y_pred)
        assert np.isclose(K.eval(loss), 5.5, atol=1e-3)

    def test_scalar_weighted(self):
        mae_obj = losses.MeanAbsoluteError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mae_obj(y_true, y_pred, sample_weight=2.3)
        assert np.isclose(K.eval(loss), 12.65, atol=1e-3)

    def test_sample_weighted(self):
        mae_obj = losses.MeanAbsoluteError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        sample_weight = K.constant([1.2, 3.4], shape=(2, 1))
        loss = mae_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.isclose(K.eval(loss), 81.4 / 6, atol=1e-3)

    def test_timestep_weighted(self):
        mae_obj = losses.MeanAbsoluteError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3, 1))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3, 1))
        sample_weight = K.constant([3, 6, 5, 0, 4, 2], shape=(2, 3))
        loss = mae_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.isclose(K.eval(loss), 13.833, atol=1e-3)

    def test_zero_weighted(self):
        mae_obj = losses.MeanAbsoluteError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mae_obj(y_true, y_pred, sample_weight=0)
        assert np.isclose(K.eval(loss), 0.0, atol=1e-3)

    def test_invalid_sample_weight(self):
        mae_obj = losses.MeanAbsoluteError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3, 1))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3, 1))
        sample_weight = K.constant([3, 6, 5, 0], shape=(2, 2))
        with pytest.raises(Exception):
            mae_obj(y_true, y_pred, sample_weight=sample_weight)

    def test_no_reduction(self):
        mae_obj = losses.MeanAbsoluteError(
            reduction=Reduction.NONE)
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mae_obj(y_true, y_pred, sample_weight=2.3)
        assert np.allclose(K.eval(loss), [10.7333, 14.5666], atol=1e-3)

    def test_sum_reduction(self):
        mae_obj = losses.MeanAbsoluteError(
            reduction=Reduction.SUM)
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mae_obj(y_true, y_pred, sample_weight=2.3)
        assert np.isclose(K.eval(loss), 25.29999, atol=1e-3)


@skipif_not_tf
class TestMeanAbsolutePercentageError(object):

    def test_config(self):
        mape_obj = losses.MeanAbsolutePercentageError(
            reduction=Reduction.SUM, name='mape_1')
        assert mape_obj.name == 'mape_1'
        assert mape_obj.reduction == Reduction.SUM

    def test_all_correct_unweighted(self):
        mape_obj = losses.MeanAbsolutePercentageError()
        y_true = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mape_obj(y_true, y_true)
        assert np.allclose(K.eval(loss), 0.0, atol=1e-3)

    def test_unweighted(self):
        mape_obj = losses.MeanAbsolutePercentageError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mape_obj(y_true, y_pred)
        assert np.allclose(K.eval(loss), 211.8518, atol=1e-3)

    def test_scalar_weighted(self):
        mape_obj = losses.MeanAbsolutePercentageError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mape_obj(y_true, y_pred, sample_weight=2.3)
        assert np.allclose(K.eval(loss), 487.259, atol=1e-3)

    def test_sample_weighted(self):
        mape_obj = losses.MeanAbsolutePercentageError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        sample_weight = K.constant([1.2, 3.4], shape=(2, 1))
        loss = mape_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(K.eval(loss), 422.8888, atol=1e-3)

    def test_timestep_weighted(self):
        mape_obj = losses.MeanAbsolutePercentageError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3, 1))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3, 1))
        sample_weight = K.constant([3, 6, 5, 0, 4, 2], shape=(2, 3))
        loss = mape_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(K.eval(loss), 694.4445, atol=1e-3)

    def test_zero_weighted(self):
        mape_obj = losses.MeanAbsolutePercentageError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mape_obj(y_true, y_pred, sample_weight=0)
        assert np.allclose(K.eval(loss), 0.0, atol=1e-3)

    def test_no_reduction(self):
        mape_obj = losses.MeanAbsolutePercentageError(
            reduction=Reduction.NONE)
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = mape_obj(y_true, y_pred, sample_weight=2.3)
        assert np.allclose(K.eval(loss), [621.8518, 352.6666], atol=1e-3)


@skipif_not_tf
class TestMeanSquaredLogarithmicError(object):

    def test_config(self):
        msle_obj = losses.MeanSquaredLogarithmicError(
            reduction=Reduction .SUM, name='mape_1')
        assert msle_obj.name == 'mape_1'
        assert msle_obj.reduction == Reduction .SUM

    def test_unweighted(self):
        msle_obj = losses.MeanSquaredLogarithmicError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = msle_obj(y_true, y_pred)
        assert np.allclose(K.eval(loss), 1.4370, atol=1e-3)

    def test_scalar_weighted(self):
        msle_obj = losses.MeanSquaredLogarithmicError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = msle_obj(y_true, y_pred, sample_weight=2.3)
        assert np.allclose(K.eval(loss), 3.3051, atol=1e-3)

    def test_sample_weighted(self):
        msle_obj = losses.MeanSquaredLogarithmicError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        sample_weight = K.constant([1.2, 3.4], shape=(2, 1))
        loss = msle_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(K.eval(loss), 3.7856, atol=1e-3)

    def test_timestep_weighted(self):
        msle_obj = losses.MeanSquaredLogarithmicError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3, 1))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3, 1))
        sample_weight = K.constant([3, 6, 5, 0, 4, 2], shape=(2, 3))
        loss = msle_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.allclose(K.eval(loss), 2.6473, atol=1e-3)

    def test_zero_weighted(self):
        msle_obj = losses.MeanSquaredLogarithmicError()
        y_true = K.constant([1, 9, 2, -5, -2, 6], shape=(2, 3))
        y_pred = K.constant([4, 8, 12, 8, 1, 3], shape=(2, 3))
        loss = msle_obj(y_true, y_pred, sample_weight=0)
        assert np.allclose(K.eval(loss), 0.0, atol=1e-3)


@skipif_not_tf
class TestBinaryCrossentropy(object):

    def test_config(self):
        bce_obj = losses.BinaryCrossentropy(
            reduction=Reduction.SUM, name='bce_1')
        assert bce_obj.name == 'bce_1'
        assert bce_obj.reduction == Reduction.SUM

    def test_all_correct_unweighted(self):
        y_true = K.constant([[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
        bce_obj = losses.BinaryCrossentropy()
        loss = bce_obj(y_true, y_true)
        assert np.isclose(K.eval(loss), 0.0, atol=1e-3)

        # Test with logits.
        logits = K.constant([[100.0, -100.0, -100.0],
                             [-100.0, 100.0, -100.0],
                             [-100.0, -100.0, 100.0]])
        bce_obj = losses.BinaryCrossentropy(from_logits=True)
        loss = bce_obj(y_true, logits)
        assert np.isclose(K.eval(loss), 0.0, 3)

    def test_unweighted(self):
        y_true = np.asarray([1, 0, 1, 0]).reshape([2, 2])
        y_pred = np.asarray([1, 1, 1, 0], dtype=np.float32).reshape([2, 2])
        bce_obj = losses.BinaryCrossentropy()
        loss = bce_obj(y_true, y_pred)

        # EPSILON = 1e-7, y = y_true, y` = y_pred, Y_MAX = 0.9999999
        # y` = clip(output, EPSILON, 1. - EPSILON)
        # y` = [Y_MAX, Y_MAX, Y_MAX, EPSILON]

        # Loss = -(y log(y` + EPSILON) + (1 - y) log(1 - y` + EPSILON))
        #      = [-log(Y_MAX + EPSILON), -log(1 - Y_MAX + EPSILON),
        #         -log(Y_MAX + EPSILON), -log(1)]
        #      = [0, 15.33, 0, 0]
        # Reduced loss = 15.33 / 4

        assert np.isclose(K.eval(loss), 3.833, atol=1e-3)

        # Test with logits.
        y_true = K.constant([[1., 0., 1.], [0., 1., 1.]])
        logits = K.constant([[100.0, -100.0, 100.0], [100.0, 100.0, -100.0]])
        bce_obj = losses.BinaryCrossentropy(from_logits=True)
        loss = bce_obj(y_true, logits)

        # Loss = max(x, 0) - x * z + log(1 + exp(-abs(x)))
        #            (where x = logits and z = y_true)
        #      = [((100 - 100 * 1 + log(1 + exp(-100))) +
        #          (0 + 100 * 0 + log(1 + exp(-100))) +
        #          (100 - 100 * 1 + log(1 + exp(-100))),
        #         ((100 - 100 * 0 + log(1 + exp(-100))) +
        #          (100 - 100 * 1 + log(1 + exp(-100))) +
        #          (0 + 100 * 1 + log(1 + exp(-100))))]
        #      = [(0 + 0 + 0) / 3, 200 / 3]
        # Reduced loss = (0 + 66.666) / 2

        assert np.isclose(K.eval(loss), 33.333, atol=1e-3)

    def test_scalar_weighted(self):
        bce_obj = losses.BinaryCrossentropy()
        y_true = np.asarray([1, 0, 1, 0]).reshape([2, 2])
        y_pred = np.asarray([1, 1, 1, 0], dtype=np.float32).reshape([2, 2])
        loss = bce_obj(y_true, y_pred, sample_weight=2.3)

        # EPSILON = 1e-7, y = y_true, y` = y_pred, Y_MAX = 0.9999999
        # y` = clip(output, EPSILON, 1. - EPSILON)
        # y` = [Y_MAX, Y_MAX, Y_MAX, EPSILON]

        # Loss = -(y log(y` + EPSILON) + (1 - y) log(1 - y` + EPSILON))
        #      = [-log(Y_MAX + EPSILON), -log(1 - Y_MAX + EPSILON),
        #         -log(Y_MAX + EPSILON), -log(1)]
        #      = [0, 15.33, 0, 0]
        # Weighted loss = [0, 15.33 * 2.3, 0, 0]
        # Reduced loss = 15.33 * 2.3 / 4

        assert np.isclose(K.eval(loss), 8.817, atol=1e-3)

        # Test with logits.
        y_true = K.constant([[1, 0, 1], [0, 1, 1]])
        logits = K.constant([[100.0, -100.0, 100.0], [100.0, 100.0, -100.0]])
        bce_obj = losses.BinaryCrossentropy(from_logits=True)
        loss = bce_obj(y_true, logits, sample_weight=2.3)

        # Loss = max(x, 0) - x * z + log(1 + exp(-abs(x)))
        #            (where x = logits and z = y_true)
        # Loss = [(0 + 0 + 0) / 3, 200 / 3]
        # Weighted loss = [0 * 2.3, 66.666 * 2.3]
        # Reduced loss = (0 + 66.666 * 2.3) / 2

        assert np.isclose(K.eval(loss), 76.667, atol=1e-3)

    def test_sample_weighted(self):
        bce_obj = losses.BinaryCrossentropy()
        y_true = np.asarray([1, 0, 1, 0]).reshape([2, 2])
        y_pred = np.asarray([1, 1, 1, 0], dtype=np.float32).reshape([2, 2])
        sample_weight = K.constant([1.2, 3.4], shape=(2, 1))
        loss = bce_obj(y_true, y_pred, sample_weight=sample_weight)

        # EPSILON = 1e-7, y = y_true, y` = y_pred, Y_MAX = 0.9999999
        # y` = clip(output, EPSILON, 1. - EPSILON)
        # y` = [Y_MAX, Y_MAX, Y_MAX, EPSILON]

        # Loss = -(y log(y` + EPSILON) + (1 - y) log(1 - y` + EPSILON))
        #      = [-log(Y_MAX + EPSILON), -log(1 - Y_MAX + EPSILON),
        #         -log(Y_MAX + EPSILON), -log(1)]
        #      = [0, 15.33, 0, 0]
        # Reduced loss = 15.33 * 1.2 / 4

        assert np.isclose(K.eval(loss), 4.6, atol=1e-3)

        # Test with logits.
        y_true = K.constant([[1, 0, 1], [0, 1, 1]])
        logits = K.constant([[100.0, -100.0, 100.0], [100.0, 100.0, -100.0]])
        weights = K.constant([4, 3])
        bce_obj = losses.BinaryCrossentropy(from_logits=True)
        loss = bce_obj(y_true, logits, sample_weight=weights)

        # Loss = max(x, 0) - x * z + log(1 + exp(-abs(x)))
        #            (where x = logits and z = y_true)
        # Loss = [(0 + 0 + 0)/3, 200 / 3]
        # Weighted loss = [0 * 4, 66.666 * 3]
        # Reduced loss = (0 + 66.666 * 3) / 2

        assert np.isclose(K.eval(loss), 100, atol=1e-3)

    def test_no_reduction(self):
        y_true = K.constant([[1, 0, 1], [0, 1, 1]])
        logits = K.constant([[100.0, -100.0, 100.0], [100.0, 100.0, -100.0]])
        bce_obj = losses.BinaryCrossentropy(
            from_logits=True, reduction=Reduction.NONE)
        loss = bce_obj(y_true, logits)

        # Loss = max(x, 0) - x * z + log(1 + exp(-abs(x)))
        #            (where x = logits and z = y_true)
        # Loss = [(0 + 0 + 0)/3, (200)/3]

        assert np.allclose(K.eval(loss), (0., 66.6666), atol=1e-3)

    def test_label_smoothing(self):
        logits = K.constant([[100.0, -100.0, -100.0]])
        y_true = K.constant([[1, 0, 1]])
        label_smoothing = 0.1
        # Loss: max(x, 0) - x * z + log(1 + exp(-abs(x)))
        #            (where x = logits and z = y_true)
        # Label smoothing: z' = z * (1 - L) + 0.5L
        #                  1  = 1 - 0.5L
        #                  0  = 0.5L
        # Applying the above two fns to the given input:
        # (100 - 100 * (1 - 0.5 L)  + 0 +
        #  0   + 100 * (0.5 L)      + 0 +
        #  0   + 100 * (1 - 0.5 L)  + 0) * (1/3)
        #  = (100 + 50L) * 1/3
        bce_obj = losses.BinaryCrossentropy(
            from_logits=True, label_smoothing=label_smoothing)
        loss = bce_obj(y_true, logits)
        expected_value = (100.0 + 50.0 * label_smoothing) / 3.0
        assert np.isclose(K.eval(loss), expected_value, atol=1e-3)


@skipif_not_tf
class TestCategoricalCrossentropy(object):

    def test_config(self):
        cce_obj = losses.CategoricalCrossentropy(
            reduction=Reduction.SUM, name='bce_1')
        assert cce_obj.name == 'bce_1'
        assert cce_obj.reduction == Reduction.SUM

    def test_all_correct_unweighted(self):
        y_true = K.constant([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        y_pred = K.constant([[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
        cce_obj = losses.CategoricalCrossentropy()
        loss = cce_obj(y_true, y_pred)
        assert np.isclose(K.eval(loss), 0.0, atol=1e-3)

        # Test with logits.
        logits = K.constant([[10., 0., 0.], [0., 10., 0.], [0., 0., 10.]])
        cce_obj = losses.CategoricalCrossentropy(from_logits=True)
        loss = cce_obj(y_true, logits)
        assert np.isclose(K.eval(loss), 0.0, atol=1e-3)

    def test_unweighted(self):
        cce_obj = losses.CategoricalCrossentropy()
        y_true = K.constant([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        y_pred = K.constant(
            [[.9, .05, .05], [.5, .89, .6], [.05, .01, .94]])
        loss = cce_obj(y_true, y_pred)
        assert np.isclose(K.eval(loss), .3239, atol=1e-3)

        # Test with logits.
        logits = K.constant([[8., 1., 1.], [0., 9., 1.], [2., 3., 5.]])
        cce_obj = losses.CategoricalCrossentropy(from_logits=True)
        loss = cce_obj(y_true, logits)
        assert np.isclose(K.eval(loss), .05737, atol=1e-3)

    def test_scalar_weighted(self):
        cce_obj = losses.CategoricalCrossentropy()
        y_true = K.constant([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        y_pred = K.constant(
            [[.9, .05, .05], [.5, .89, .6], [.05, .01, .94]])
        loss = cce_obj(y_true, y_pred, sample_weight=2.3)
        assert np.isclose(K.eval(loss), .7449, atol=1e-3)

        # Test with logits.
        logits = K.constant([[8., 1., 1.], [0., 9., 1.], [2., 3., 5.]])
        cce_obj = losses.CategoricalCrossentropy(from_logits=True)
        loss = cce_obj(y_true, logits, sample_weight=2.3)
        assert np.isclose(K.eval(loss), .132, atol=1e-3)

    def test_sample_weighted(self):
        cce_obj = losses.CategoricalCrossentropy()
        y_true = K.constant([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        y_pred = K.constant(
            [[.9, .05, .05], [.5, .89, .6], [.05, .01, .94]])
        sample_weight = K.constant([[1.2], [3.4], [5.6]], shape=(3, 1))
        loss = cce_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.isclose(K.eval(loss), 1.0696, atol=1e-3)

        # Test with logits.
        logits = K.constant([[8., 1., 1.], [0., 9., 1.], [2., 3., 5.]])
        cce_obj = losses.CategoricalCrossentropy(from_logits=True)
        loss = cce_obj(y_true, logits, sample_weight=sample_weight)
        assert np.isclose(K.eval(loss), 0.31829, atol=1e-3)

    def test_no_reduction(self):
        y_true = K.constant([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        logits = K.constant([[8., 1., 1.], [0., 9., 1.], [2., 3., 5.]])
        cce_obj = losses.CategoricalCrossentropy(
            from_logits=True, reduction=Reduction.NONE)
        loss = cce_obj(y_true, logits)
        assert np.allclose(K.eval(loss), (0.001822, 0.000459, 0.169846), atol=1e-3)

    def test_label_smoothing(self):
        logits = K.constant([[100.0, -100.0, -100.0]])
        y_true = K.constant([[1, 0, 0]])
        label_smoothing = 0.1
        # Softmax Cross Entropy Loss: -\sum_i p_i \log q_i
        # where for a softmax activation
        # \log q_i = x_i - \log \sum_j \exp x_j
        #          = x_i - x_max - \log \sum_j \exp (x_j - x_max)
        # For our activations, [100, -100, -100]
        # \log ( exp(0) + exp(-200) + exp(-200) ) = 0
        # so our log softmaxes become: [0, -200, -200]
        # Label smoothing: z' = z * (1 - L) + L/n
        #                  1  = 1 - L + L/n
        #                  0  = L/n
        # Applying the above two fns to the given input:
        # -0 * (1 - L + L/n) + 200 * L/n + 200 * L/n = 400 L/n
        cce_obj = losses.CategoricalCrossentropy(
            from_logits=True, label_smoothing=label_smoothing)
        loss = cce_obj(y_true, logits)
        expected_value = 400.0 * label_smoothing / 3.0
        assert np.isclose(K.eval(loss), expected_value, atol=1e-3)


@skipif_not_tf
class TestSparseCategoricalCrossentropy(object):

    def test_config(self):
        cce_obj = losses.SparseCategoricalCrossentropy(
            reduction=Reduction.SUM, name='scc')
        assert cce_obj.name == 'scc'
        assert cce_obj.reduction == Reduction.SUM

    def test_all_correct_unweighted(self):
        y_true = K.constant([[0], [1], [2]])
        y_pred = K.constant([[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
        cce_obj = losses.SparseCategoricalCrossentropy()
        loss = cce_obj(y_true, y_pred)
        assert np.isclose(K.eval(loss), 0.0, atol=1e-3)

        # Test with logits.
        logits = K.constant([[10., 0., 0.], [0., 10., 0.], [0., 0., 10.]])
        cce_obj = losses.SparseCategoricalCrossentropy(from_logits=True)
        loss = cce_obj(y_true, logits)
        assert np.isclose(K.eval(loss), 0.0, atol=1e-3)

    def test_unweighted(self):
        cce_obj = losses.SparseCategoricalCrossentropy()
        y_true = K.constant([0, 1, 2])
        y_pred = K.constant(
            [[.9, .05, .05], [.5, .89, .6], [.05, .01, .94]])
        loss = cce_obj(y_true, y_pred)
        assert np.isclose(K.eval(loss), .3239, atol=1e-3)

        # Test with logits.
        logits = K.constant([[8., 1., 1.], [0., 9., 1.], [2., 3., 5.]])
        cce_obj = losses.SparseCategoricalCrossentropy(from_logits=True)
        loss = cce_obj(y_true, logits)
        assert np.isclose(K.eval(loss), .0573, atol=1e-3)

    def test_scalar_weighted(self):
        cce_obj = losses.SparseCategoricalCrossentropy()
        y_true = K.constant([[0], [1], [2]])
        y_pred = K.constant(
            [[.9, .05, .05], [.5, .89, .6], [.05, .01, .94]])
        loss = cce_obj(y_true, y_pred, sample_weight=2.3)
        assert np.isclose(K.eval(loss), .7449, atol=1e-3)

        # Test with logits.
        logits = K.constant([[8., 1., 1.], [0., 9., 1.], [2., 3., 5.]])
        cce_obj = losses.SparseCategoricalCrossentropy(from_logits=True)
        loss = cce_obj(y_true, logits, sample_weight=2.3)
        assert np.isclose(K.eval(loss), .1317, atol=1e-3)

    def test_sample_weighted(self):
        cce_obj = losses.SparseCategoricalCrossentropy()
        y_true = K.constant([[0], [1], [2]])
        y_pred = K.constant(
            [[.9, .05, .05], [.5, .89, .6], [.05, .01, .94]])
        sample_weight = K.constant([[1.2], [3.4], [5.6]], shape=(3, 1))
        loss = cce_obj(y_true, y_pred, sample_weight=sample_weight)
        assert np.isclose(K.eval(loss), 1.0696, atol=1e-3)

        # Test with logits.
        logits = K.constant([[8., 1., 1.], [0., 9., 1.], [2., 3., 5.]])
        cce_obj = losses.SparseCategoricalCrossentropy(from_logits=True)
        loss = cce_obj(y_true, logits, sample_weight=sample_weight)
        assert np.isclose(K.eval(loss), 0.31829, atol=1e-3)

    def test_no_reduction(self):
        y_true = K.constant([[0], [1], [2]])
        logits = K.constant([[8., 1., 1.], [0., 9., 1.], [2., 3., 5.]])
        cce_obj = losses.SparseCategoricalCrossentropy(
            from_logits=True, reduction=Reduction.NONE)
        loss = cce_obj(y_true, logits)
        assert np.allclose(K.eval(loss), (0.001822, 0.000459, 0.169846), atol=1e-3)


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import numpy as np

from keras.utils.test_utils import get_test_data

from keras.models import Sequential
from keras.layers.core import Dense, Activation
from keras.wrappers.scikit_learn import KerasClassifier, KerasRegressor

input_dim = 5
hidden_dims = 5
num_train = 100
num_test = 50
num_classes = 3
batch_size = 32
epochs = 1
verbosity = 0
optim = 'adam'
loss = 'categorical_crossentropy'

np.random.seed(42)
(X_train, y_train), (X_test, y_test) = get_test_data(
    num_train=num_train, num_test=num_test, input_shape=(input_dim,),
    classification=True, num_classes=num_classes)


def build_fn_clf(hidden_dims):
    model = Sequential()
    model.add(Dense(input_dim, input_shape=(input_dim,)))
    model.add(Activation('relu'))
    model.add(Dense(hidden_dims))
    model.add(Activation('relu'))
    model.add(Dense(num_classes))
    model.add(Activation('softmax'))
    model.compile(optimizer='sgd', loss='categorical_crossentropy',
                  metrics=['accuracy'])
    return model


def test_classify_build_fn():
    clf = KerasClassifier(
        build_fn=build_fn_clf, hidden_dims=hidden_dims,
        batch_size=batch_size, epochs=epochs)

    assert_classification_works(clf)
    assert_string_classification_works(clf)


def test_classify_class_build_fn():
    class ClassBuildFnClf(object):

        def __call__(self, hidden_dims):
            return build_fn_clf(hidden_dims)

    clf = KerasClassifier(
        build_fn=ClassBuildFnClf(), hidden_dims=hidden_dims,
        batch_size=batch_size, epochs=epochs)

    assert_classification_works(clf)
    assert_string_classification_works(clf)


def test_classify_inherit_class_build_fn():
    class InheritClassBuildFnClf(KerasClassifier):

        def __call__(self, hidden_dims):
            return build_fn_clf(hidden_dims)

    clf = InheritClassBuildFnClf(
        build_fn=None, hidden_dims=hidden_dims,
        batch_size=batch_size, epochs=epochs)

    assert_classification_works(clf)
    assert_string_classification_works(clf)


def assert_classification_works(clf):
    clf.fit(X_train, y_train, sample_weight=np.ones(X_train.shape[0]),
            batch_size=batch_size, epochs=epochs)

    score = clf.score(X_train, y_train, batch_size=batch_size)
    assert np.isscalar(score) and np.isfinite(score)

    preds = clf.predict(X_test, batch_size=batch_size)
    assert preds.shape == (num_test, )
    for prediction in np.unique(preds):
        assert prediction in range(num_classes)

    proba = clf.predict_proba(X_test, batch_size=batch_size)
    assert proba.shape == (num_test, num_classes)
    assert np.allclose(np.sum(proba, axis=1), np.ones(num_test))


def assert_string_classification_works(clf):
    string_classes = ['cls{}'.format(x) for x in range(num_classes)]
    str_y_train = np.array(string_classes)[y_train]

    clf.fit(X_train, str_y_train, batch_size=batch_size, epochs=epochs)

    score = clf.score(X_train, str_y_train, batch_size=batch_size)
    assert np.isscalar(score) and np.isfinite(score)

    preds = clf.predict(X_test, batch_size=batch_size)
    assert preds.shape == (num_test, )
    for prediction in np.unique(preds):
        assert prediction in string_classes

    proba = clf.predict_proba(X_test, batch_size=batch_size)
    assert proba.shape == (num_test, num_classes)
    assert np.allclose(np.sum(proba, axis=1), np.ones(num_test))


def build_fn_reg(hidden_dims=50):
    model = Sequential()
    model.add(Dense(input_dim, input_shape=(input_dim,)))
    model.add(Activation('relu'))
    model.add(Dense(hidden_dims))
    model.add(Activation('relu'))
    model.add(Dense(1))
    model.add(Activation('linear'))
    model.compile(optimizer='sgd', loss='mean_absolute_error',
                  metrics=['accuracy'])
    return model


def test_regression_build_fn():
    reg = KerasRegressor(
        build_fn=build_fn_reg, hidden_dims=hidden_dims,
        batch_size=batch_size, epochs=epochs)

    assert_regression_works(reg)


def test_regression_class_build_fn():
    class ClassBuildFnReg(object):

        def __call__(self, hidden_dims):
            return build_fn_reg(hidden_dims)

    reg = KerasRegressor(
        build_fn=ClassBuildFnReg(), hidden_dims=hidden_dims,
        batch_size=batch_size, epochs=epochs)

    assert_regression_works(reg)


def test_regression_inherit_class_build_fn():
    class InheritClassBuildFnReg(KerasRegressor):

        def __call__(self, hidden_dims):
            return build_fn_reg(hidden_dims)

    reg = InheritClassBuildFnReg(
        build_fn=None, hidden_dims=hidden_dims,
        batch_size=batch_size, epochs=epochs)

    assert_regression_works(reg)


def assert_regression_works(reg):
    reg.fit(X_train, y_train, batch_size=batch_size, epochs=epochs)

    score = reg.score(X_train, y_train, batch_size=batch_size)
    assert np.isscalar(score) and np.isfinite(score)

    preds = reg.predict(X_test, batch_size=batch_size)
    assert preds.shape == (num_test, )


def DISABLED_test_regression_predict_shape_correct_num_test_0():
    assert_regression_predict_shape_correct(num_test=0)


def DISABLED_test_regression_predict_shape_correct_num_test_1():
    assert_regression_predict_shape_correct(num_test=1)


def assert_regression_predict_shape_correct(num_test):
    reg = KerasRegressor(
        build_fn=build_fn_reg, hidden_dims=hidden_dims,
        batch_size=batch_size, epochs=epochs)
    reg.fit(X_train, y_train, batch_size=batch_size, epochs=epochs)

    preds = reg.predict(X_test[:num_test], batch_size=batch_size)
    assert preds.shape == (num_test, )


if __name__ == '__main__':
    pytest.main([__file__])

# Usage of sklearn's grid_search
# from sklearn import grid_search
# parameters = dict(hidden_dims = [20, 30], batch_size=[64, 128],
#                   epochs=[2], verbose=[0])
# classifier = Inherit_class_build_fn_clf()
# clf = grid_search.GridSearchCV(classifier, parameters)
# clf.fit(X_train, y_train)
# parameters = dict(hidden_dims = [20, 30], batch_size=[64, 128],
#                   epochs=[2], verbose=[0])
# regressor = Inherit_class_build_fn_reg()
# reg = grid_search.GridSearchCV(regressor, parameters,
#                                scoring='mean_squared_error',
#                                n_jobs=1, cv=2, verbose=2)
# reg.fit(X_train_reg, y_train_reg)

import pytest
from keras.utils.test_utils import layer_test
from keras import layers
from keras import backend as K


@pytest.mark.parametrize('activation_layer',
                         [layers.LeakyReLU,
                          layers.ELU])
@pytest.mark.parametrize('alpha', [0., .5, -1.])
def test_linear_unit_activations(activation_layer,
                                 alpha):
    layer_test(activation_layer, kwargs={'alpha': alpha},
               input_shape=(2, 3, 4))


def test_prelu():
    layer_test(layers.PReLU, kwargs={},
               input_shape=(2, 3, 4))


def test_prelu_share():
    layer_test(layers.PReLU, kwargs={'shared_axes': 1},
               input_shape=(2, 3, 4))


def test_thresholded_relu():
    layer_test(layers.ThresholdedReLU, kwargs={'theta': 0.5},
               input_shape=(2, 3, 4))


@pytest.mark.parametrize('axis', [1, -1])
def test_softmax(axis):
    layer_test(layers.Softmax, kwargs={'axis': axis},
               input_shape=(2, 3, 4))


def test_relu():
    layer_test(layers.ReLU,
               kwargs={'max_value': 10,
                       'negative_slope': 0.2,
                       'threshold': 3.0},
               input_shape=(2, 3, 4))
    layer_test(layers.ReLU,
               kwargs={'max_value': 6},
               input_shape=(2, 3, 4))
    layer_test(layers.ReLU,
               kwargs={'negative_slope': 0.2},
               input_shape=(2, 3, 4))

    # max_value of ReLU layer cannot be negative value
    with pytest.raises(ValueError):
        layer_test(layers.ReLU, kwargs={'max_value': -2.0},
                   input_shape=(2, 3, 4))

    # negative_slope of ReLU layer cannot be negative value
    with pytest.raises(ValueError):
        layer_test(layers.ReLU, kwargs={'negative_slope': -2.0},
                   input_shape=(2, 3, 4))



if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import numpy as np
from numpy.testing import assert_allclose

import keras
from keras.utils.test_utils import layer_test
from keras.layers import recurrent
from keras.layers import embeddings
from keras.models import Sequential
from keras.models import Model
from keras.engine import Input
from keras.layers import Masking
from keras import regularizers
from keras import backend as K

num_samples, timesteps, embedding_dim, units = 2, 5, 4, 3
embedding_num = 12


rnn_test = pytest.mark.parametrize('layer_class',
                                   [recurrent.SimpleRNN,
                                    recurrent.GRU,
                                    recurrent.LSTM])


rnn_cell_test = pytest.mark.parametrize('cell_class',
                                        [recurrent.SimpleRNNCell,
                                         recurrent.GRUCell,
                                         recurrent.LSTMCell])


@rnn_test
def test_return_sequences(layer_class):
    layer_test(layer_class,
               kwargs={'units': units,
                       'return_sequences': True},
               input_shape=(num_samples, timesteps, embedding_dim))


@rnn_test
def test_dynamic_behavior(layer_class):
    layer = layer_class(units, input_shape=(None, embedding_dim))
    model = Sequential()
    model.add(layer)
    model.compile('sgd', 'mse')
    x = np.random.random((num_samples, timesteps, embedding_dim))
    y = np.random.random((num_samples, units))
    model.train_on_batch(x, y)


@rnn_test
def DISABLED_test_stateful_invalid_use(layer_class):
    layer = layer_class(units,
                        stateful=True,
                        batch_input_shape=(num_samples,
                                           timesteps,
                                           embedding_dim))
    model = Sequential()
    model.add(layer)
    model.compile('sgd', 'mse')
    x = np.random.random((num_samples * 2, timesteps, embedding_dim))
    y = np.random.random((num_samples * 2, units))
    with pytest.raises(ValueError):
        model.fit(x, y)
    with pytest.raises(ValueError):
        model.predict(x, batch_size=num_samples + 1)


@rnn_test
@pytest.mark.skipif((K.backend() in ['theano']),
                    reason='Not supported.')
def test_dropout(layer_class):
    for unroll in [True, False]:
        layer_test(layer_class,
                   kwargs={'units': units,
                           'dropout': 0.1,
                           'recurrent_dropout': 0.1,
                           'unroll': unroll},
                   input_shape=(num_samples, timesteps, embedding_dim))

        # Test that dropout is applied during training
        x = K.ones((num_samples, timesteps, embedding_dim))
        layer = layer_class(units, dropout=0.5, recurrent_dropout=0.5,
                            input_shape=(timesteps, embedding_dim))
        y = layer(x)

        y = layer(x, training=True)

        # Test that dropout is not applied during testing
        x = np.random.random((num_samples, timesteps, embedding_dim))
        layer = layer_class(units, dropout=0.5, recurrent_dropout=0.5,
                            unroll=unroll,
                            input_shape=(timesteps, embedding_dim))
        model = Sequential([layer])
        y1 = model.predict(x)
        y2 = model.predict(x)
        assert_allclose(y1, y2)


@rnn_test
def test_statefulness(layer_class):
    model = Sequential()
    model.add(embeddings.Embedding(embedding_num, embedding_dim,
                                   mask_zero=True,
                                   input_length=timesteps,
                                   batch_input_shape=(num_samples, timesteps)))
    layer = layer_class(units, return_sequences=False,
                        stateful=True,
                        weights=None)
    model.add(layer)
    model.compile(optimizer='sgd', loss='mse')
    out1 = model.predict(np.ones((num_samples, timesteps)))
    assert(out1.shape == (num_samples, units))

    # train once so that the states change
    model.train_on_batch(np.ones((num_samples, timesteps)),
                         np.ones((num_samples, units)))
    out2 = model.predict(np.ones((num_samples, timesteps)))

    # if the state is not reset, output should be different
    assert(out1.max() != out2.max())

    # check that output changes after states are reset
    # (even though the model itself didn't change)
    layer.reset_states()
    out3 = model.predict(np.ones((num_samples, timesteps)))
    assert(out2.max() != out3.max())

    # check that container-level reset_states() works
    model.reset_states()
    out4 = model.predict(np.ones((num_samples, timesteps)))
    assert_allclose(out3, out4, atol=1e-5)

    # check that the call to `predict` updated the states
    out5 = model.predict(np.ones((num_samples, timesteps)))
    assert(out4.max() != out5.max())


@rnn_test
def test_masking_correctness(layer_class):
    # Check masking: output with left padding and right padding
    # should be the same.
    model = Sequential()
    model.add(embeddings.Embedding(embedding_num, embedding_dim,
                                   mask_zero=True,
                                   input_length=timesteps,
                                   batch_input_shape=(num_samples, timesteps)))
    layer = layer_class(units, return_sequences=False)
    model.add(layer)
    model.compile(optimizer='sgd', loss='mse')

    left_padded_input = np.ones((num_samples, timesteps))
    left_padded_input[0, :1] = 0
    left_padded_input[1, :2] = 0
    out6 = model.predict(left_padded_input)

    right_padded_input = np.ones((num_samples, timesteps))
    right_padded_input[0, -1:] = 0
    right_padded_input[1, -2:] = 0
    out7 = model.predict(right_padded_input)

    assert_allclose(out7, out6, atol=1e-5)


@pytest.mark.skipif(K.backend() == 'cntk', reason='Not supported.')
def test_masking_correctness_output_not_equal_to_first_state():

    class Cell(keras.layers.Layer):

        def __init__(self):
            self.state_size = None
            self.output_size = None
            super(Cell, self).__init__()

        def build(self, input_shape):
            self.state_size = input_shape[-1]
            self.output_size = input_shape[-1]

        def call(self, inputs, states):
            return inputs, [s + 1 for s in states]

    num_samples = 5
    num_timesteps = 4
    state_size = input_size = 3  # also equal to `output_size`

    # random inputs and state values
    x_vals = np.random.random((num_samples, num_timesteps, input_size))
    # last timestep masked for first sample (all zero inputs masked by Masking layer)
    x_vals[0, -1, :] = 0
    s_initial_vals = np.random.random((num_samples, state_size))

    # final outputs equal to last inputs
    y_vals_expected = x_vals[:, -1].copy()
    # except for first sample, where it is equal to second to last value due to mask
    y_vals_expected[0] = x_vals[0, -2]

    s_final_vals_expected = s_initial_vals.copy()
    # states are incremented `num_timesteps - 1` times for first sample
    s_final_vals_expected[0] += (num_timesteps - 1)
    # and `num_timesteps - 1` times for remaining samples
    s_final_vals_expected[1:] += num_timesteps

    for unroll in [True, False]:
        x = Input((num_timesteps, input_size), name="x")
        x_masked = Masking()(x)
        s_initial = Input((state_size,), name="s_initial")
        y, s_final = recurrent.RNN(Cell(),
                                   return_state=True,
                                   unroll=unroll)(x_masked, initial_state=s_initial)
        model = Model([x, s_initial], [y, s_final])
        model.compile(optimizer='sgd', loss='mse')

        y_vals, s_final_vals = model.predict([x_vals, s_initial_vals])
        assert_allclose(y_vals,
                        y_vals_expected,
                        err_msg="Unexpected output for unroll={}".format(unroll))
        assert_allclose(s_final_vals,
                        s_final_vals_expected,
                        err_msg="Unexpected state for unroll={}".format(unroll))


@pytest.mark.skipif(K.backend() == 'cntk', reason='Not supported.')
def test_masking_correctness_output_size_not_equal_to_first_state_size():

    class Cell(keras.layers.Layer):

        def __init__(self):
            self.state_size = None
            self.output_size = None
            super(Cell, self).__init__()

        def build(self, input_shape):
            self.state_size = input_shape[-1]
            self.output_size = input_shape[-1] * 2

        def call(self, inputs, states):
            return keras.layers.concatenate([inputs] * 2), [s + 1 for s in states]

    num_samples = 5
    num_timesteps = 6
    input_size = state_size = 7

    # random inputs and state values
    x_vals = np.random.random((num_samples, num_timesteps, input_size))
    # last timestep masked for first sample (all zero inputs masked by Masking layer)
    x_vals[0, -1, :] = 0
    s_initial_vals = np.random.random((num_samples, state_size))

    # final outputs equal to last inputs concatenated
    y_vals_expected = np.concatenate([x_vals[:, -1]] * 2, axis=-1)
    # except for first sample, where it is equal to second to last value due to mask
    y_vals_expected[0] = np.concatenate([x_vals[0, -2]] * 2, axis=-1)

    s_final_vals_expected = s_initial_vals.copy()
    # states are incremented `num_timesteps - 1` times for first sample
    s_final_vals_expected[0] += (num_timesteps - 1)
    # and `num_timesteps - 1` times for remaining samples
    s_final_vals_expected[1:] += num_timesteps

    for unroll in [True, False]:
        x = Input((num_timesteps, input_size), name="x")
        x_masked = Masking()(x)
        s_initial = Input((state_size,), name="s_initial")
        y, s_final = recurrent.RNN(Cell(),
                                   return_state=True,
                                   unroll=unroll)(x_masked, initial_state=s_initial)
        model = Model([x, s_initial], [y, s_final])
        model.compile(optimizer='sgd', loss='mse')

        y_vals, s_final_vals = model.predict([x_vals, s_initial_vals])
        assert_allclose(y_vals,
                        y_vals_expected,
                        err_msg="Unexpected output for unroll={}".format(unroll))
        assert_allclose(s_final_vals,
                        s_final_vals_expected,
                        err_msg="Unexpected state for unroll={}".format(unroll))


@rnn_test
def test_implementation_mode(layer_class):
    for mode in [1, 2]:
        # Without dropout
        layer_test(layer_class,
                   kwargs={'units': units,
                           'implementation': mode},
                   input_shape=(num_samples, timesteps, embedding_dim))
        # With dropout
        layer_test(layer_class,
                   kwargs={'units': units,
                           'implementation': mode,
                           'dropout': 0.1,
                           'recurrent_dropout': 0.1},
                   input_shape=(num_samples, timesteps, embedding_dim))
        # Without bias
        layer_test(layer_class,
                   kwargs={'units': units,
                           'implementation': mode,
                           'use_bias': False},
                   input_shape=(num_samples, timesteps, embedding_dim))


@rnn_test
def test_regularizer(layer_class):
    layer = layer_class(units, return_sequences=False, weights=None,
                        input_shape=(timesteps, embedding_dim),
                        kernel_regularizer=regularizers.l1(0.01),
                        recurrent_regularizer=regularizers.l1(0.01),
                        bias_regularizer='l2')
    layer.build((None, None, embedding_dim))
    assert len(layer.losses) == 3
    assert len(layer.cell.losses) == 3

    layer = layer_class(units, return_sequences=False, weights=None,
                        input_shape=(timesteps, embedding_dim),
                        activity_regularizer='l2')
    assert layer.activity_regularizer
    x = K.variable(np.ones((num_samples, timesteps, embedding_dim)))
    layer(x)


@rnn_test
def test_trainability(layer_class):
    layer = layer_class(units)
    layer.build((None, None, embedding_dim))
    assert len(layer.weights) == 3
    assert len(layer.trainable_weights) == 3
    assert len(layer.non_trainable_weights) == 0
    layer.trainable = False
    assert len(layer.weights) == 3
    assert len(layer.trainable_weights) == 0
    assert len(layer.non_trainable_weights) == 3
    layer.trainable = True
    assert len(layer.weights) == 3
    assert len(layer.trainable_weights) == 3
    assert len(layer.non_trainable_weights) == 0


def test_masking_layer():
    ''' This test based on a previously failing issue here:
    https://github.com/keras-team/keras/issues/1567
    '''
    inputs = np.random.random((6, 3, 4))
    targets = np.abs(np.random.random((6, 3, 5)))
    targets /= targets.sum(axis=-1, keepdims=True)

    model = Sequential()
    model.add(Masking(input_shape=(3, 4)))
    model.add(recurrent.SimpleRNN(units=5, return_sequences=True, unroll=False))
    model.compile(loss='categorical_crossentropy', optimizer='adam')
    model.fit(inputs, targets, epochs=1, batch_size=100, verbose=1)

    model = Sequential()
    model.add(Masking(input_shape=(3, 4)))
    model.add(recurrent.SimpleRNN(units=5, return_sequences=True, unroll=True))
    model.compile(loss='categorical_crossentropy', optimizer='adam')
    model.fit(inputs, targets, epochs=1, batch_size=100, verbose=1)


@rnn_test
def test_from_config(layer_class):
    stateful_flags = (False, True)
    for stateful in stateful_flags:
        l1 = layer_class(units=1, stateful=stateful)
        l2 = layer_class.from_config(l1.get_config())
        assert l1.get_config() == l2.get_config()


@rnn_test
def test_specify_initial_state_keras_tensor(layer_class):
    num_states = 2 if layer_class is recurrent.LSTM else 1

    # Test with Keras tensor
    inputs = Input((timesteps, embedding_dim))
    initial_state = [Input((units,)) for _ in range(num_states)]
    layer = layer_class(units)
    if len(initial_state) == 1:
        output = layer(inputs, initial_state=initial_state[0])
    else:
        output = layer(inputs, initial_state=initial_state)
    assert id(initial_state[0]) in [
        id(x) for x in layer._inbound_nodes[0].input_tensors]

    model = Model([inputs] + initial_state, output)
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    inputs = np.random.random((num_samples, timesteps, embedding_dim))
    initial_state = [np.random.random((num_samples, units))
                     for _ in range(num_states)]
    targets = np.random.random((num_samples, units))
    model.fit([inputs] + initial_state, targets)


@rnn_test
def test_specify_initial_state_non_keras_tensor(layer_class):
    num_states = 2 if layer_class is recurrent.LSTM else 1

    # Test with non-Keras tensor
    inputs = Input((timesteps, embedding_dim))
    initial_state = [K.random_normal_variable((num_samples, units), 0, 1)
                     for _ in range(num_states)]
    layer = layer_class(units)
    output = layer(inputs, initial_state=initial_state)

    model = Model(inputs, output)
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    inputs = np.random.random((num_samples, timesteps, embedding_dim))
    targets = np.random.random((num_samples, units))
    model.fit(inputs, targets)


@rnn_test
def test_reset_states_with_values(layer_class):
    num_states = 2 if layer_class is recurrent.LSTM else 1

    layer = layer_class(units, stateful=True)
    layer.build((num_samples, timesteps, embedding_dim))
    layer.reset_states()
    assert len(layer.states) == num_states
    assert layer.states[0] is not None
    np.testing.assert_allclose(K.eval(layer.states[0]),
                               np.zeros(K.int_shape(layer.states[0])),
                               atol=1e-4)
    state_shapes = [K.int_shape(state) for state in layer.states]
    values = [np.ones(shape) for shape in state_shapes]
    if len(values) == 1:
        values = values[0]
    layer.reset_states(values)
    np.testing.assert_allclose(K.eval(layer.states[0]),
                               np.ones(K.int_shape(layer.states[0])),
                               atol=1e-4)

    # Test fit with invalid data
    with pytest.raises(ValueError):
        layer.reset_states([1] * (len(layer.states) + 1))


@rnn_test
def test_initial_states_as_other_inputs(layer_class):
    num_states = 2 if layer_class is recurrent.LSTM else 1

    # Test with Keras tensor
    main_inputs = Input((timesteps, embedding_dim))
    initial_state = [Input((units,)) for _ in range(num_states)]
    inputs = [main_inputs] + initial_state

    layer = layer_class(units)
    output = layer(inputs)
    assert id(initial_state[0]) in [
        id(x) for x in layer._inbound_nodes[0].input_tensors]

    model = Model(inputs, output)
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    main_inputs = np.random.random((num_samples, timesteps, embedding_dim))
    initial_state = [np.random.random((num_samples, units))
                     for _ in range(num_states)]
    targets = np.random.random((num_samples, units))
    model.train_on_batch([main_inputs] + initial_state, targets)


@rnn_test
def test_specify_state_with_masking(layer_class):
    ''' This test based on a previously failing issue here:
    https://github.com/keras-team/keras/issues/1567
    '''
    num_states = 2 if layer_class is recurrent.LSTM else 1

    inputs = Input((timesteps, embedding_dim))
    _ = Masking()(inputs)
    initial_state = [Input((units,)) for _ in range(num_states)]
    output = layer_class(units)(inputs, initial_state=initial_state)

    model = Model([inputs] + initial_state, output)
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    inputs = np.random.random((num_samples, timesteps, embedding_dim))
    initial_state = [np.random.random((num_samples, units))
                     for _ in range(num_states)]
    targets = np.random.random((num_samples, units))
    model.fit([inputs] + initial_state, targets)


@rnn_test
def test_return_state(layer_class):
    num_states = 2 if layer_class is recurrent.LSTM else 1

    inputs = Input(batch_shape=(num_samples, timesteps, embedding_dim))
    layer = layer_class(units, return_state=True, stateful=True)
    outputs = layer(inputs)
    output, state = outputs[0], outputs[1:]
    assert len(state) == num_states
    model = Model(inputs, state[0])

    inputs = np.random.random((num_samples, timesteps, embedding_dim))
    state = model.predict(inputs)
    np.testing.assert_allclose(K.eval(layer.states[0]), state, atol=1e-4)


@rnn_test
def test_state_reuse(layer_class):
    inputs = Input(batch_shape=(num_samples, timesteps, embedding_dim))
    layer = layer_class(units, return_state=True, return_sequences=True)
    outputs = layer(inputs)
    output, state = outputs[0], outputs[1:]
    output = layer_class(units)(output, initial_state=state)
    model = Model(inputs, output)

    inputs = np.random.random((num_samples, timesteps, embedding_dim))
    outputs = model.predict(inputs)


@rnn_test
@pytest.mark.skipif((K.backend() in ['theano']),
                    reason='Not supported.')
def test_state_reuse_with_dropout(layer_class):
    input1 = Input(batch_shape=(num_samples, timesteps, embedding_dim))
    layer = layer_class(units, return_state=True, return_sequences=True, dropout=0.2)
    state = layer(input1)[1:]

    input2 = Input(batch_shape=(num_samples, timesteps, embedding_dim))
    output = layer_class(units)(input2, initial_state=state)
    model = Model([input1, input2], output)

    inputs = [np.random.random((num_samples, timesteps, embedding_dim)),
              np.random.random((num_samples, timesteps, embedding_dim))]
    outputs = model.predict(inputs)


def test_minimal_rnn_cell_non_layer():

    class MinimalRNNCell(object):

        def __init__(self, units, input_dim):
            self.units = units
            self.state_size = units
            self.kernel = keras.backend.variable(
                np.random.random((input_dim, units)))

        def call(self, inputs, states):
            prev_output = states[0]
            output = keras.backend.dot(inputs, self.kernel) + prev_output
            return output, [output]

    # Basic test case.
    cell = MinimalRNNCell(32, 5)
    x = keras.Input((None, 5))
    layer = recurrent.RNN(cell)
    y = layer(x)
    model = keras.models.Model(x, y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(np.zeros((6, 5, 5)), np.zeros((6, 32)))

    # Test stacking.
    cells = [MinimalRNNCell(8, 5),
             MinimalRNNCell(32, 8),
             MinimalRNNCell(32, 32)]
    layer = recurrent.RNN(cells)
    y = layer(x)
    model = keras.models.Model(x, y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(np.zeros((6, 5, 5)), np.zeros((6, 32)))


def test_minimal_rnn_cell_non_layer_multiple_states():

    class MinimalRNNCell(object):

        def __init__(self, units, input_dim):
            self.units = units
            self.state_size = (units, units)
            self.kernel = keras.backend.variable(
                np.random.random((input_dim, units)))

        def call(self, inputs, states):
            prev_output_1 = states[0]
            prev_output_2 = states[1]
            output = keras.backend.dot(inputs, self.kernel)
            output += prev_output_1
            output -= prev_output_2
            return output, [output * 2, output * 3]

    # Basic test case.
    cell = MinimalRNNCell(32, 5)
    x = keras.Input((None, 5))
    layer = recurrent.RNN(cell)
    y = layer(x)
    model = keras.models.Model(x, y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(np.zeros((6, 5, 5)), np.zeros((6, 32)))

    # Test stacking.
    cells = [MinimalRNNCell(8, 5),
             MinimalRNNCell(16, 8),
             MinimalRNNCell(32, 16)]
    layer = recurrent.RNN(cells)
    y = layer(x)
    model = keras.models.Model(x, y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(np.zeros((6, 5, 5)), np.zeros((6, 32)))


def test_minimal_rnn_cell_layer():

    class MinimalRNNCell(keras.layers.Layer):

        def __init__(self, units, **kwargs):
            self.units = units
            self.state_size = units
            super(MinimalRNNCell, self).__init__(**kwargs)

        def build(self, input_shape):
            # no time axis in the input shape passed to RNN cells
            assert len(input_shape) == 2

            self.kernel = self.add_weight(shape=(input_shape[-1], self.units),
                                          initializer='uniform',
                                          name='kernel')
            self.recurrent_kernel = self.add_weight(
                shape=(self.units, self.units),
                initializer='uniform',
                name='recurrent_kernel')
            self.built = True

        def call(self, inputs, states):
            prev_output = states[0]
            h = keras.backend.dot(inputs, self.kernel)
            output = h + keras.backend.dot(prev_output, self.recurrent_kernel)
            return output, [output]

        def get_config(self):
            config = {'units': self.units}
            base_config = super(MinimalRNNCell, self).get_config()
            return dict(list(base_config.items()) + list(config.items()))

    # Test basic case.
    x = keras.Input((None, 5))
    cell = MinimalRNNCell(32)
    layer = recurrent.RNN(cell)
    y = layer(x)
    model = keras.models.Model(x, y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(np.zeros((6, 5, 5)), np.zeros((6, 32)))

    # Test basic case serialization.
    x_np = np.random.random((6, 5, 5))
    y_np = model.predict(x_np)
    weights = model.get_weights()
    config = layer.get_config()
    with keras.utils.CustomObjectScope({'MinimalRNNCell': MinimalRNNCell}):
        layer = recurrent.RNN.from_config(config)
    y = layer(x)
    model = keras.models.Model(x, y)
    model.set_weights(weights)
    y_np_2 = model.predict(x_np)
    assert_allclose(y_np, y_np_2, atol=1e-4)

    # Test stacking.
    cells = [MinimalRNNCell(8),
             MinimalRNNCell(12),
             MinimalRNNCell(32)]
    layer = recurrent.RNN(cells)
    y = layer(x)
    model = keras.models.Model(x, y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(np.zeros((6, 5, 5)), np.zeros((6, 32)))

    # Test stacked RNN serialization.
    x_np = np.random.random((6, 5, 5))
    y_np = model.predict(x_np)
    weights = model.get_weights()
    config = layer.get_config()
    with keras.utils.CustomObjectScope({'MinimalRNNCell': MinimalRNNCell}):
        layer = recurrent.RNN.from_config(config)
    y = layer(x)
    model = keras.models.Model(x, y)
    model.set_weights(weights)
    y_np_2 = model.predict(x_np)
    assert_allclose(y_np, y_np_2, atol=1e-4)


@rnn_cell_test
def test_builtin_rnn_cell_layer(cell_class):
    # Test basic case.
    x = keras.Input((None, 5))
    cell = cell_class(32)
    layer = recurrent.RNN(cell)
    y = layer(x)
    model = keras.models.Model(x, y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(np.zeros((6, 5, 5)), np.zeros((6, 32)))

    # Test basic case serialization.
    x_np = np.random.random((6, 5, 5))
    y_np = model.predict(x_np)
    weights = model.get_weights()
    config = layer.get_config()
    layer = recurrent.RNN.from_config(config)
    y = layer(x)
    model = keras.models.Model(x, y)
    model.set_weights(weights)
    y_np_2 = model.predict(x_np)
    assert_allclose(y_np, y_np_2, atol=1e-4)

    # Test stacking.
    cells = [cell_class(8),
             cell_class(12),
             cell_class(32)]
    layer = recurrent.RNN(cells)
    y = layer(x)
    model = keras.models.Model(x, y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(np.zeros((6, 5, 5)), np.zeros((6, 32)))

    # Test stacked RNN serialization.
    x_np = np.random.random((6, 5, 5))
    y_np = model.predict(x_np)
    weights = model.get_weights()
    config = layer.get_config()
    layer = recurrent.RNN.from_config(config)
    y = layer(x)
    model = keras.models.Model(x, y)
    model.set_weights(weights)
    y_np_2 = model.predict(x_np)
    assert_allclose(y_np, y_np_2, atol=1e-4)


@pytest.mark.skipif((K.backend() in ['cntk', 'theano']),
                    reason='Not supported.')
def test_stacked_rnn_dropout():
    cells = [recurrent.LSTMCell(3, dropout=0.1, recurrent_dropout=0.1),
             recurrent.LSTMCell(3, dropout=0.1, recurrent_dropout=0.1)]
    layer = recurrent.RNN(cells)

    x = keras.Input((None, 5))
    y = layer(x)
    model = keras.models.Model(x, y)
    model.compile('sgd', 'mse')
    x_np = np.random.random((6, 5, 5))
    y_np = np.random.random((6, 3))
    model.train_on_batch(x_np, y_np)


def test_stacked_rnn_attributes():
    cells = [recurrent.LSTMCell(3),
             recurrent.LSTMCell(3, kernel_regularizer='l2')]
    layer = recurrent.RNN(cells)
    layer.build((None, None, 5))

    # Test regularization losses
    assert len(layer.losses) == 1

    # Test weights
    assert len(layer.trainable_weights) == 6
    cells[0].trainable = False
    assert len(layer.trainable_weights) == 3
    assert len(layer.non_trainable_weights) == 3

    x = keras.Input((None, 5))
    y = K.sum(x)
    cells[0].add_loss(y, inputs=x)


def test_stacked_rnn_compute_output_shape():
    cells = [recurrent.LSTMCell(3),
             recurrent.LSTMCell(6)]
    layer = recurrent.RNN(cells, return_state=True, return_sequences=True)
    output_shape = layer.compute_output_shape((None, timesteps, embedding_dim))
    expected_output_shape = [(None, timesteps, 6),
                             (None, 3),
                             (None, 3),
                             (None, 6),
                             (None, 6)]
    assert [tuple(s) for s in output_shape] == expected_output_shape

    # Test reverse_state_order = True for stacked cell.
    stacked_cell = recurrent.StackedRNNCells(
        cells, reverse_state_order=True)
    layer = recurrent.RNN(
        stacked_cell, return_state=True, return_sequences=True)
    output_shape = layer.compute_output_shape((None, timesteps, embedding_dim))
    expected_output_shape = [(None, timesteps, 6),
                             (None, 6),
                             (None, 6),
                             (None, 3),
                             (None, 3)]
    assert [tuple(s) for s in output_shape] == expected_output_shape


@rnn_test
def test_batch_size_equal_one(layer_class):
    inputs = Input(batch_shape=(1, timesteps, embedding_dim))
    layer = layer_class(units)
    outputs = layer(inputs)
    model = Model(inputs, outputs)
    model.compile('sgd', 'mse')
    x = np.random.random((1, timesteps, embedding_dim))
    y = np.random.random((1, units))
    model.train_on_batch(x, y)


def DISABLED_test_rnn_cell_with_constants_layer():

    class RNNCellWithConstants(keras.layers.Layer):

        def __init__(self, units, **kwargs):
            self.units = units
            self.state_size = units
            super(RNNCellWithConstants, self).__init__(**kwargs)

        def build(self, input_shape):
            if not isinstance(input_shape, list):
                raise TypeError('expects `constants` shape')
            [input_shape, constant_shape] = input_shape
            # will (and should) raise if more than one constant passed

            self.input_kernel = self.add_weight(
                shape=(input_shape[-1], self.units),
                initializer='uniform',
                name='kernel')
            self.recurrent_kernel = self.add_weight(
                shape=(self.units, self.units),
                initializer='uniform',
                name='recurrent_kernel')
            self.constant_kernel = self.add_weight(
                shape=(constant_shape[-1], self.units),
                initializer='uniform',
                name='constant_kernel')
            self.built = True

        def call(self, inputs, states, constants):
            [prev_output] = states
            [constant] = constants
            h_input = keras.backend.dot(inputs, self.input_kernel)
            h_state = keras.backend.dot(prev_output, self.recurrent_kernel)
            h_const = keras.backend.dot(constant, self.constant_kernel)
            output = h_input + h_state + h_const
            return output, [output]

        def get_config(self):
            config = {'units': self.units}
            base_config = super(RNNCellWithConstants, self).get_config()
            return dict(list(base_config.items()) + list(config.items()))

    # Test basic case.
    x = keras.Input((None, 5))
    c = keras.Input((3,))
    cell = RNNCellWithConstants(32)
    layer = recurrent.RNN(cell)
    y = layer(x, constants=c)
    model = keras.models.Model([x, c], y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(
        [np.zeros((6, 5, 5)), np.zeros((6, 3))],
        np.zeros((6, 32))
    )

    # Test basic case serialization.
    x_np = np.random.random((6, 5, 5))
    c_np = np.random.random((6, 3))
    y_np = model.predict([x_np, c_np])
    weights = model.get_weights()
    config = layer.get_config()
    custom_objects = {'RNNCellWithConstants': RNNCellWithConstants}
    with keras.utils.CustomObjectScope(custom_objects):
        layer = recurrent.RNN.from_config(config.copy())
    y = layer(x, constants=c)
    model = keras.models.Model([x, c], y)
    model.set_weights(weights)
    y_np_2 = model.predict([x_np, c_np])
    assert_allclose(y_np, y_np_2, atol=1e-4)

    # test flat list inputs
    with keras.utils.CustomObjectScope(custom_objects):
        layer = recurrent.RNN.from_config(config.copy())
    y = layer([x, c])
    model = keras.models.Model([x, c], y)
    model.set_weights(weights)
    y_np_3 = model.predict([x_np, c_np])
    assert_allclose(y_np, y_np_3, atol=1e-4)

    # Test stacking.
    cells = [recurrent.GRUCell(8),
             RNNCellWithConstants(12),
             RNNCellWithConstants(32)]
    layer = recurrent.RNN(cells)
    y = layer(x, constants=c)
    model = keras.models.Model([x, c], y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(
        [np.zeros((6, 5, 5)), np.zeros((6, 3))],
        np.zeros((6, 32))
    )

    # Test stacked RNN serialization.
    x_np = np.random.random((6, 5, 5))
    c_np = np.random.random((6, 3))
    y_np = model.predict([x_np, c_np])
    weights = model.get_weights()
    config = layer.get_config()
    with keras.utils.CustomObjectScope(custom_objects):
        layer = recurrent.RNN.from_config(config.copy())
    y = layer(x, constants=c)
    model = keras.models.Model([x, c], y)
    model.set_weights(weights)
    y_np_2 = model.predict([x_np, c_np])
    assert_allclose(y_np, y_np_2, atol=1e-4)


def DISABLED_test_rnn_cell_with_constants_layer_passing_initial_state():

    class RNNCellWithConstants(keras.layers.Layer):

        def __init__(self, units, **kwargs):
            self.units = units
            self.state_size = units
            super(RNNCellWithConstants, self).__init__(**kwargs)

        def build(self, input_shape):
            if not isinstance(input_shape, list):
                raise TypeError('expects constants shape')
            [input_shape, constant_shape] = input_shape
            # will (and should) raise if more than one constant passed

            self.input_kernel = self.add_weight(
                shape=(input_shape[-1], self.units),
                initializer='uniform',
                name='kernel')
            self.recurrent_kernel = self.add_weight(
                shape=(self.units, self.units),
                initializer='uniform',
                name='recurrent_kernel')
            self.constant_kernel = self.add_weight(
                shape=(constant_shape[-1], self.units),
                initializer='uniform',
                name='constant_kernel')
            self.built = True

        def call(self, inputs, states, constants):
            [prev_output] = states
            [constant] = constants
            h_input = keras.backend.dot(inputs, self.input_kernel)
            h_state = keras.backend.dot(prev_output, self.recurrent_kernel)
            h_const = keras.backend.dot(constant, self.constant_kernel)
            output = h_input + h_state + h_const
            return output, [output]

        def get_config(self):
            config = {'units': self.units}
            base_config = super(RNNCellWithConstants, self).get_config()
            return dict(list(base_config.items()) + list(config.items()))

    # Test basic case.
    x = keras.Input((None, 5))
    c = keras.Input((3,))
    s = keras.Input((32,))
    cell = RNNCellWithConstants(32)
    layer = recurrent.RNN(cell)
    y = layer(x, initial_state=s, constants=c)
    model = keras.models.Model([x, s, c], y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(
        [np.zeros((6, 5, 5)), np.zeros((6, 32)), np.zeros((6, 3))],
        np.zeros((6, 32))
    )

    # Test basic case serialization.
    x_np = np.random.random((6, 5, 5))
    s_np = np.random.random((6, 32))
    c_np = np.random.random((6, 3))
    y_np = model.predict([x_np, s_np, c_np])
    weights = model.get_weights()
    config = layer.get_config()
    custom_objects = {'RNNCellWithConstants': RNNCellWithConstants}
    with keras.utils.CustomObjectScope(custom_objects):
        layer = recurrent.RNN.from_config(config.copy())
    y = layer(x, initial_state=s, constants=c)
    model = keras.models.Model([x, s, c], y)
    model.set_weights(weights)
    y_np_2 = model.predict([x_np, s_np, c_np])
    assert_allclose(y_np, y_np_2, atol=1e-4)

    # verify that state is used
    y_np_2_different_s = model.predict([x_np, s_np + 10., c_np])
    with pytest.raises(AssertionError):
        assert_allclose(y_np, y_np_2_different_s, atol=1e-4)

    # test flat list inputs
    with keras.utils.CustomObjectScope(custom_objects):
        layer = recurrent.RNN.from_config(config.copy())
    y = layer([x, s, c])
    model = keras.models.Model([x, s, c], y)
    model.set_weights(weights)
    y_np_3 = model.predict([x_np, s_np, c_np])
    assert_allclose(y_np, y_np_3, atol=1e-4)


@rnn_test
def DISABLED_test_rnn_cell_identity_initializer(layer_class):
    inputs = Input(shape=(1, 2))
    layer = layer_class(2, recurrent_initializer='identity')
    layer(inputs)
    recurrent_kernel = layer.get_weights()[1]
    num_kernels = recurrent_kernel.shape[1] // recurrent_kernel.shape[0]
    assert np.array_equal(recurrent_kernel,
                          np.concatenate([np.identity(2)] * num_kernels, axis=1))


@pytest.mark.skipif(K.backend() == 'cntk', reason='Not supported.')
def test_inconsistent_output_state_size():

    class PlusOneRNNCell(keras.layers.Layer):
        """Add one to the input and state.

        This cell is used for testing state_size and output_size."""

        def __init__(self, num_unit, **kwargs):
            self.state_size = num_unit
            super(PlusOneRNNCell, self).__init__(**kwargs)

        def build(self, input_shape):
            self.output_size = input_shape[-1]

        def call(self, inputs, states):
            return inputs + 1, [states[0] + 1]

    batch = 32
    time_step = 4
    state_size = 5
    input_size = 6
    cell = PlusOneRNNCell(state_size)
    x = keras.Input((None, input_size))
    layer = recurrent.RNN(cell)
    y = layer(x)

    assert cell.state_size == state_size
    init_state = layer.get_initial_state(x)
    assert len(init_state) == 1
    if K.backend() != 'theano':
        # theano does not support static shape inference.
        assert K.int_shape(init_state[0]) == (None, state_size)

    model = keras.models.Model(x, y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(
        np.zeros((batch, time_step, input_size)),
        np.zeros((batch, input_size)))
    assert model.output_shape == (None, input_size)


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import numpy as np
from numpy.testing import assert_allclose
from keras import layers
from keras import models
from keras import backend as K
from keras.utils.test_utils import layer_test
from keras.layers import merge


def test_merge_add():
    i1 = layers.Input(shape=(4, 5))
    i2 = layers.Input(shape=(4, 5))
    i3 = layers.Input(shape=(4, 5))
    o = layers.add([i1, i2, i3])
    assert K.int_shape(o) == (None, 4, 5)
    model = models.Model([i1, i2, i3], o)

    add_layer = layers.Add()
    o2 = add_layer([i1, i2, i3])
    assert add_layer.output_shape == (None, 4, 5)

    x1 = np.random.random((2, 4, 5))
    x2 = np.random.random((2, 4, 5))
    x3 = np.random.random((2, 4, 5))
    out = model.predict([x1, x2, x3])
    assert out.shape == (2, 4, 5)
    assert_allclose(out, x1 + x2 + x3, atol=1e-4)

    assert add_layer.compute_mask([i1, i2, i3], [None, None, None]) is None
    assert np.all(K.eval(add_layer.compute_mask(
        [i1, i2, i3], [K.variable(x1), K.variable(x2), K.variable(x3)])))

    # Test invalid use case
    with pytest.raises(ValueError):
        add_layer.compute_mask([i1, i2, i3], x1)
    with pytest.raises(ValueError):
        add_layer.compute_mask(i1, [None, None, None])
    with pytest.raises(ValueError):
        add_layer.compute_mask([i1, i2, i3], [None, None])


def test_merge_subtract():
    i1 = layers.Input(shape=(4, 5))
    i2 = layers.Input(shape=(4, 5))
    i3 = layers.Input(shape=(4, 5))
    i4 = layers.Input(shape=(3, 5))
    o = layers.subtract([i1, i2])
    assert K.int_shape(o) == (None, 4, 5)
    model = models.Model([i1, i2], o)

    subtract_layer = layers.Subtract()
    o2 = subtract_layer([i1, i2])
    assert subtract_layer.output_shape == (None, 4, 5)

    x1 = np.random.random((2, 4, 5))
    x2 = np.random.random((2, 4, 5))
    out = model.predict([x1, x2])
    assert out.shape == (2, 4, 5)
    assert_allclose(out, x1 - x2, atol=1e-4)

    assert subtract_layer.compute_mask([i1, i2], [None, None]) is None
    assert np.all(K.eval(subtract_layer.compute_mask(
        [i1, i2], [K.variable(x1), K.variable(x2)])))

    # Test invalid use case
    with pytest.raises(ValueError):
        subtract_layer.compute_mask([i1, i2], x1)
    with pytest.raises(ValueError):
        subtract_layer.compute_mask(i1, [None, None])
    with pytest.raises(ValueError):
        subtract_layer([i1, i2, i3])
    with pytest.raises(ValueError):
        subtract_layer([i1])


def test_merge_multiply():
    i1 = layers.Input(shape=(4, 5))
    i2 = layers.Input(shape=(4, 5))
    i3 = layers.Input(shape=(4, 5))
    o = layers.multiply([i1, i2, i3])
    assert K.int_shape(o) == (None, 4, 5)
    model = models.Model([i1, i2, i3], o)

    mul_layer = layers.Multiply()
    o2 = mul_layer([i1, i2, i3])
    assert mul_layer.output_shape == (None, 4, 5)

    x1 = np.random.random((2, 4, 5))
    x2 = np.random.random((2, 4, 5))
    x3 = np.random.random((2, 4, 5))
    out = model.predict([x1, x2, x3])
    assert out.shape == (2, 4, 5)
    assert_allclose(out, x1 * x2 * x3, atol=1e-4)


def test_merge_average():
    i1 = layers.Input(shape=(4, 5))
    i2 = layers.Input(shape=(4, 5))
    o = layers.average([i1, i2])
    assert K.int_shape(o) == (None, 4, 5)
    model = models.Model([i1, i2], o)

    avg_layer = layers.Average()
    o2 = avg_layer([i1, i2])
    assert avg_layer.output_shape == (None, 4, 5)

    x1 = np.random.random((2, 4, 5))
    x2 = np.random.random((2, 4, 5))
    out = model.predict([x1, x2])
    assert out.shape == (2, 4, 5)
    assert_allclose(out, 0.5 * (x1 + x2), atol=1e-4)


def test_merge_maximum():
    i1 = layers.Input(shape=(4, 5))
    i2 = layers.Input(shape=(4, 5))
    o = layers.maximum([i1, i2])
    assert K.int_shape(o) == (None, 4, 5)
    model = models.Model([i1, i2], o)

    max_layer = layers.Maximum()
    o2 = max_layer([i1, i2])
    assert max_layer.output_shape == (None, 4, 5)

    x1 = np.random.random((2, 4, 5))
    x2 = np.random.random((2, 4, 5))
    out = model.predict([x1, x2])
    assert out.shape == (2, 4, 5)
    assert_allclose(out, np.maximum(x1, x2), atol=1e-4)


def test_merge_minimum():
    i1 = layers.Input(shape=(4, 5))
    i2 = layers.Input(shape=(4, 5))
    o = layers.minimum([i1, i2])
    assert K.int_shape(o) == (None, 4, 5)
    model = models.Model([i1, i2], o)

    max_layer = layers.Minimum()
    o2 = max_layer([i1, i2])
    assert max_layer.output_shape == (None, 4, 5)

    x1 = np.random.random((2, 4, 5))
    x2 = np.random.random((2, 4, 5))
    out = model.predict([x1, x2])
    assert out.shape == (2, 4, 5)
    assert_allclose(out, np.minimum(x1, x2), atol=1e-4)


def test_merge_concatenate():
    i1 = layers.Input(shape=(None, 5))
    i2 = layers.Input(shape=(None, 5))
    o = layers.concatenate([i1, i2], axis=1)
    assert K.int_shape(o) == (None, None, 5)
    model = models.Model([i1, i2], o)

    i1 = layers.Input(shape=(4, 5))
    i2 = layers.Input(shape=(4, 5))
    o = layers.concatenate([i1, i2], axis=1)
    assert K.int_shape(o) == (None, 8, 5)
    model = models.Model([i1, i2], o)

    concat_layer = layers.Concatenate(axis=1)
    o2 = concat_layer([i1, i2])
    assert concat_layer.output_shape == (None, 8, 5)

    x1 = np.random.random((2, 4, 5))
    x2 = np.random.random((2, 4, 5))
    out = model.predict([x1, x2])
    assert out.shape == (2, 8, 5)
    assert_allclose(out, np.concatenate([x1, x2], axis=1), atol=1e-4)

    x3 = np.random.random((1, 1, 1))
    nb_layers = 4
    x_i = layers.Input(shape=(None, None))
    x_list = [x_i]
    x = x_i
    for i in range(nb_layers):
        x_list.append(x)
        x = layers.concatenate(x_list, axis=1)
    concat_model = models.Model(x_i, x)
    concat_out = concat_model.predict([x3])
    x3 = np.repeat(x3, 16, axis=1)
    assert concat_out.shape == (1, 16, 1)
    assert_allclose(concat_out, x3)

    assert concat_layer.compute_mask([i1, i2], [None, None]) is None
    assert np.all(K.eval(concat_layer.compute_mask(
        [i1, i2], [K.variable(x1), K.variable(x2)])).reshape(-1))

    # Test invalid use case
    concat_layer = layers.Concatenate(axis=1)
    with pytest.raises(ValueError):
        concat_layer.compute_mask([i1, i2], x1)
    with pytest.raises(ValueError):
        concat_layer.compute_mask(i1, [None, None])
    with pytest.raises(ValueError):
        concat_layer.compute_mask([i1, i2], [None])
    with pytest.raises(ValueError):
        concat_layer([i1])


def test_merge_dot():
    i1 = layers.Input(shape=(4,))
    i2 = layers.Input(shape=(4,))
    o = layers.dot([i1, i2], axes=1)
    assert K.int_shape(o) == (None, 1)
    model = models.Model([i1, i2], o)

    dot_layer = layers.Dot(axes=1)
    o2 = dot_layer([i1, i2])
    assert dot_layer.output_shape == (None, 1)

    x1 = np.random.random((2, 4))
    x2 = np.random.random((2, 4))
    out = model.predict([x1, x2])
    assert out.shape == (2, 1)
    expected = np.zeros((2, 1))
    expected[0, 0] = np.dot(x1[0], x2[0])
    expected[1, 0] = np.dot(x1[1], x2[1])
    assert_allclose(out, expected, atol=1e-4)

    # Test with negative tuple of axes.
    o = layers.dot([i1, i2], axes=(-1, -1))
    assert K.int_shape(o) == (None, 1)
    model = models.Model([i1, i2], o)
    out = model.predict([x1, x2])
    assert out.shape == (2, 1)
    assert_allclose(out, expected, atol=1e-4)


def test_merge_broadcast():
    # shapes provided
    i1 = layers.Input(shape=(4, 5))
    i2 = layers.Input(shape=(5,))
    ops = [layers.add, layers.maximum]
    for op in ops:
        o = op([i1, i2])
        assert K.int_shape(o) == (None, 4, 5)
        model = models.Model([i1, i2], o)

        x1 = np.random.random((2, 4, 5))
        x2 = np.random.random((2, 5))
        out = model.predict([x1, x2])
        assert out.shape == (2, 4, 5)

    # shapes not provided
    i1 = layers.Input(shape=(None, None))
    i2 = layers.Input(shape=(None,))
    ops = [layers.add, layers.maximum]
    for op in ops:
        o = op([i1, i2])
        assert K.int_shape(o) == (None, None, None)
        model = models.Model([i1, i2], o)

        x1 = np.random.random((2, 4, 5))
        x2 = np.random.random((2, 5))
        out = model.predict([x1, x2])
        assert out.shape == (2, 4, 5)

    # ndim not provided
    if K.backend() == 'tensorflow':
        k_ndim = K.ndim
        K.ndim = lambda _: None

        i1 = layers.Input(shape=(None, None))
        i2 = layers.Input(shape=(None,))
        ops = [layers.add, layers.maximum]
        for op in ops:
            o = op([i1, i2])
            assert K.int_shape(o) == (None, None, None)
            model = models.Model([i1, i2], o)

            x1 = np.random.random((2, 4, 5))
            x2 = np.random.random((2, 5))
            out = model.predict([x1, x2])
            assert out.shape == (2, 4, 5)
        K.ndim = k_ndim


def test_masking_concatenate():
    input1 = layers.Input(shape=(6,))
    input2 = layers.Input(shape=(6,))
    x1 = layers.Embedding(10, 5, input_length=6, mask_zero=True)(input1)
    x2 = layers.Embedding(10, 5, input_length=6, mask_zero=True)(input2)
    x = layers.concatenate([x1, x2])
    x = layers.TimeDistributed(layers.Dense(3, activation='softmax'))(x)
    models.Model(inputs=[input1, input2], outputs=[x])


if __name__ == '__main__':
    pytest.main([__file__])

import pytest

from keras.utils.test_utils import layer_test
from keras.layers import local


def test_locallyconnected_1d():
    num_samples = 2
    num_steps = 8
    input_dim = 5
    filter_length = 3
    filters = 4
    padding = 'valid'
    strides = 1

    layer_test(local.LocallyConnected1D,
               kwargs={'filters': filters,
                       'kernel_size': filter_length,
                       'padding': padding,
                       'kernel_regularizer': 'l2',
                       'bias_regularizer': 'l2',
                       'activity_regularizer': 'l2',
                       'strides': strides},
               input_shape=(num_samples, num_steps, input_dim))


def test_locallyconnected_2d():
    num_samples = 5
    filters = 3
    stack_size = 4
    num_row = 6
    num_col = 8
    padding = 'valid'

    for strides in [(1, 1), (2, 2)]:
        layer_test(local.LocallyConnected2D,
                   kwargs={'filters': filters,
                           'kernel_size': 3,
                           'padding': padding,
                           'kernel_regularizer': 'l2',
                           'bias_regularizer': 'l2',
                           'activity_regularizer': 'l2',
                           'strides': strides,
                           'data_format': 'channels_last'},
                   input_shape=(num_samples, num_row, num_col, stack_size))

        layer_test(local.LocallyConnected2D,
                   kwargs={'filters': filters,
                           'kernel_size': (3, 3),
                           'padding': padding,
                           'kernel_regularizer': 'l2',
                           'bias_regularizer': 'l2',
                           'activity_regularizer': 'l2',
                           'strides': strides,
                           'data_format': 'channels_first'},
                   input_shape=(num_samples, stack_size, num_row, num_col))


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
from keras.utils.test_utils import layer_test
from keras.layers.embeddings import Embedding
from keras.models import Sequential
import keras.backend as K


def test_embedding():
    layer_test(Embedding,
               kwargs={'output_dim': 4, 'input_dim': 10, 'input_length': 2},
               input_shape=(3, 2),
               input_dtype='int32',
               expected_output_dtype=K.floatx())
    layer_test(Embedding,
               kwargs={'output_dim': 4, 'input_dim': 10, 'mask_zero': True},
               input_shape=(3, 2),
               input_dtype='int32',
               expected_output_dtype=K.floatx())
    layer_test(Embedding,
               kwargs={'output_dim': 4, 'input_dim': 10, 'mask_zero': True},
               input_shape=(3, 2, 5),
               input_dtype='int32',
               expected_output_dtype=K.floatx())
    layer_test(Embedding,
               kwargs={'output_dim': 4, 'input_dim': 10, 'mask_zero': True,
                       'input_length': (None, 5)},
               input_shape=(3, 2, 5),
               input_dtype='int32',
               expected_output_dtype=K.floatx())


@pytest.mark.parametrize('input_shape',
                         [(3, 4, 5),
                          (3, 5)])
def DISABLED_test_embedding_invalid(input_shape):

    # len(input_length) should be equal to len(input_shape) - 1
    with pytest.raises(ValueError):
        model = Sequential([Embedding(
            input_dim=10,
            output_dim=4,
            input_length=2,
            input_shape=input_shape)])


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import numpy as np
from numpy.testing import assert_allclose

from keras.layers import Input
from keras import regularizers
from keras.utils.test_utils import layer_test
from keras.layers import normalization
from keras.models import Sequential, Model
from keras import backend as K

input_1 = np.arange(10)
input_2 = np.zeros(10)
input_3 = np.ones((10))
input_4 = np.expand_dims(np.arange(10.), axis=1)
input_shapes = [np.ones((10, 10)), np.ones((10, 10, 10))]


def test_basic_batchnorm():
    layer_test(normalization.BatchNormalization,
               kwargs={'momentum': 0.9,
                       'epsilon': 0.1,
                       'gamma_regularizer': regularizers.l2(0.01),
                       'beta_regularizer': regularizers.l2(0.01)},
               input_shape=(3, 4, 2))
    layer_test(normalization.BatchNormalization,
               kwargs={'momentum': 0.9,
                       'epsilon': 0.1,
                       'axis': 1},
               input_shape=(1, 4, 1))
    layer_test(normalization.BatchNormalization,
               kwargs={'gamma_initializer': 'ones',
                       'beta_initializer': 'ones',
                       'moving_mean_initializer': 'zeros',
                       'moving_variance_initializer': 'ones'},
               input_shape=(3, 4, 2, 4))
    if K.backend() != 'theano':
        layer_test(normalization.BatchNormalization,
                   kwargs={'momentum': 0.9,
                           'epsilon': 0.1,
                           'axis': 1,
                           'scale': False,
                           'center': False},
                   input_shape=(3, 4, 2, 4))


def test_batchnorm_correctness_1d():
    np.random.seed(1337)
    model = Sequential()
    norm = normalization.BatchNormalization(input_shape=(10,), momentum=0.8)
    model.add(norm)
    model.compile(loss='mse', optimizer='rmsprop')

    # centered on 5.0, variance 10.0
    x = np.random.normal(loc=5.0, scale=10.0, size=(1000, 10))
    model.fit(x, x, epochs=5, verbose=0)
    out = model.predict(x)
    out -= K.eval(norm.beta)
    out /= K.eval(norm.gamma)

    assert_allclose(out.mean(), 0.0, atol=1e-1)
    assert_allclose(out.std(), 1.0, atol=1e-1)


def test_batchnorm_correctness_2d():
    np.random.seed(1337)
    model = Sequential()
    norm = normalization.BatchNormalization(axis=1, input_shape=(10, 6),
                                            momentum=0.8)
    model.add(norm)
    model.compile(loss='mse', optimizer='rmsprop')

    # centered on 5.0, variance 10.0
    x = np.random.normal(loc=5.0, scale=10.0, size=(1000, 10, 6))
    model.fit(x, x, epochs=5, verbose=0)
    out = model.predict(x)
    out -= np.reshape(K.eval(norm.beta), (1, 10, 1))
    out /= np.reshape(K.eval(norm.gamma), (1, 10, 1))

    assert_allclose(out.mean(axis=(0, 2)), 0.0, atol=1.1e-1)
    assert_allclose(out.std(axis=(0, 2)), 1.0, atol=1.1e-1)


def test_batchnorm_training_argument():
    np.random.seed(1337)
    bn1 = normalization.BatchNormalization(input_shape=(10,))
    x1 = Input(shape=(10,))
    y1 = bn1(x1, training=True)
    assert bn1.updates

    model1 = Model(x1, y1)
    x = np.random.normal(loc=5.0, scale=10.0, size=(20, 10))
    output_a = model1.predict(x)

    model1.compile(loss='mse', optimizer='rmsprop')
    model1.fit(x, x, epochs=1, verbose=0)
    output_b = model1.predict(x)
    assert np.abs(np.sum(output_a - output_b)) > 0.1
    assert_allclose(output_b.mean(), 0.0, atol=1e-1)
    assert_allclose(output_b.std(), 1.0, atol=1e-1)

    bn2 = normalization.BatchNormalization(input_shape=(10,))
    x2 = Input(shape=(10,))
    bn2(x2, training=False)
    assert not bn2.updates


def test_batchnorm_mode_twice():
    # This is a regression test for issue #4881 with the old
    # batch normalization functions in the Theano backend.
    model = Sequential()
    model.add(normalization.BatchNormalization(input_shape=(10, 5, 5), axis=1))
    model.add(normalization.BatchNormalization(input_shape=(10, 5, 5), axis=1))
    model.compile(loss='mse', optimizer='sgd')

    x = np.random.normal(loc=5.0, scale=10.0, size=(20, 10, 5, 5))
    model.fit(x, x, epochs=1, verbose=0)
    model.predict(x)


def test_batchnorm_convnet():
    np.random.seed(1337)
    model = Sequential()
    norm = normalization.BatchNormalization(axis=1, input_shape=(3, 4, 4),
                                            momentum=0.8)
    model.add(norm)
    model.compile(loss='mse', optimizer='sgd')

    # centered on 5.0, variance 10.0
    x = np.random.normal(loc=5.0, scale=10.0, size=(1000, 3, 4, 4))
    model.fit(x, x, epochs=4, verbose=0)
    out = model.predict(x)
    out -= np.reshape(K.eval(norm.beta), (1, 3, 1, 1))
    out /= np.reshape(K.eval(norm.gamma), (1, 3, 1, 1))

    assert_allclose(np.mean(out, axis=(0, 2, 3)), 0.0, atol=1e-1)
    assert_allclose(np.std(out, axis=(0, 2, 3)), 1.0, atol=1e-1)


@pytest.mark.skipif((K.backend() == 'theano'),
                    reason='Bug with theano backend')
def test_batchnorm_convnet_no_center_no_scale():
    np.random.seed(1337)
    model = Sequential()
    norm = normalization.BatchNormalization(axis=-1, center=False, scale=False,
                                            input_shape=(3, 4, 4), momentum=0.8)
    model.add(norm)
    model.compile(loss='mse', optimizer='sgd')

    # centered on 5.0, variance 10.0
    x = np.random.normal(loc=5.0, scale=10.0, size=(1000, 3, 4, 4))
    model.fit(x, x, epochs=4, verbose=0)
    out = model.predict(x)

    assert_allclose(np.mean(out, axis=(0, 2, 3)), 0.0, atol=1e-1)
    assert_allclose(np.std(out, axis=(0, 2, 3)), 1.0, atol=1e-1)


def test_shared_batchnorm():
    '''Test that a BN layer can be shared
    across different data streams.
    '''
    # Test single layer reuse
    bn = normalization.BatchNormalization(input_shape=(10,))
    x1 = Input(shape=(10,))
    bn(x1)

    x2 = Input(shape=(10,))
    y2 = bn(x2)

    x = np.random.normal(loc=5.0, scale=10.0, size=(2, 10))
    model = Model(x2, y2)
    model.compile('sgd', 'mse')
    model.train_on_batch(x, x)

    # Test model-level reuse
    x3 = Input(shape=(10,))
    y3 = model(x3)
    new_model = Model(x3, y3)
    new_model.compile('sgd', 'mse')
    new_model.train_on_batch(x, x)


def test_that_trainable_disables_updates():
    val_a = np.random.random((10, 4))
    val_out = np.random.random((10, 4))

    a = Input(shape=(4,))
    layer = normalization.BatchNormalization(input_shape=(4,))
    b = layer(a)
    model = Model(a, b)

    model.trainable = False
    assert not model.updates

    model.compile('sgd', 'mse')
    assert not model.updates

    x1 = model.predict(val_a)
    model.train_on_batch(val_a, val_out)
    x2 = model.predict(val_a)
    assert_allclose(x1, x2, atol=1e-7)

    model.trainable = True
    model.compile('sgd', 'mse')
    assert model.updates

    model.train_on_batch(val_a, val_out)
    x2 = model.predict(val_a)
    assert np.abs(np.sum(x1 - x2)) > 1e-5

    layer.trainable = False
    model.compile('sgd', 'mse')
    assert not model.updates

    x1 = model.predict(val_a)
    model.train_on_batch(val_a, val_out)
    x2 = model.predict(val_a)
    assert_allclose(x1, x2, atol=1e-7)


def test_batchnorm_trainable():
    bn_mean = 0.5
    bn_std = 10.

    def get_model(bn_mean, bn_std):
        input = Input(shape=(1,))
        x = normalization.BatchNormalization()(input)
        model = Model(input, x)
        model.set_weights([np.array([1.]), np.array([0.]),
                           np.array([bn_mean]), np.array([bn_std ** 2])])
        return model
    # Simulates training-mode with trainable layer. Should use mini-batch statistics.
    model = get_model(bn_mean, bn_std)
    model.compile(loss='mse', optimizer='rmsprop')
    out = model(input_4, training=True).numpy()
    assert_allclose((input_4 - np.mean(input_4)) / np.std(input_4), out, atol=1e-3)


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import numpy as np
from numpy.testing import assert_allclose

from keras import backend as K
from keras.models import Sequential, Model
from keras.layers import convolutional_recurrent, Input, Masking, Lambda
from keras.utils.test_utils import layer_test
from keras import regularizers

num_row = 3
num_col = 3
filters = 2
num_samples = 1
input_channel = 2
input_num_row = 5
input_num_col = 5
sequence_len = 2


@pytest.mark.parametrize('data_format', ['channels_first', 'channels_last'])
@pytest.mark.parametrize('return_sequences', [True, False])
@pytest.mark.parametrize('use_mask', [True, False])
def DISABLED_test_convolutional_recurrent(data_format, return_sequences, use_mask):

    class Masking5D(Masking):
        """Regular masking layer returns wrong shape of mask for RNN"""
        def compute_mask(self, inputs, mask=None):
            return K.any(K.not_equal(inputs, 0.), axis=[2, 3, 4])

    if data_format == 'channels_first':
        inputs = np.random.rand(num_samples, sequence_len,
                                input_channel,
                                input_num_row, input_num_col)
    else:
        inputs = np.random.rand(num_samples, sequence_len,
                                input_num_row, input_num_col,
                                input_channel)

    # test for return state:
    x = Input(batch_shape=inputs.shape)
    kwargs = {'data_format': data_format,
              'return_sequences': return_sequences,
              'return_state': True,
              'stateful': True,
              'filters': filters,
              'kernel_size': (num_row, num_col),
              'padding': 'valid'}
    layer = convolutional_recurrent.ConvLSTM2D(**kwargs)
    layer.build(inputs.shape)
    if use_mask:
        outputs = layer(Masking5D()(x))
    else:
        outputs = layer(x)
    output, states = outputs[0], outputs[1:]
    assert len(states) == 2
    model = Model(x, states[0])
    state = model.predict(inputs)
    np.testing.assert_allclose(K.eval(layer.states[0]), state, atol=1e-4)

    # test for output shape:
    output = layer_test(convolutional_recurrent.ConvLSTM2D,
                        kwargs={'data_format': data_format,
                                'return_sequences': return_sequences,
                                'filters': filters,
                                'kernel_size': (num_row, num_col),
                                'padding': 'valid'},
                        input_shape=inputs.shape)


def test_convolutional_recurrent_statefulness():

    data_format = 'channels_last'
    return_sequences = False
    inputs = np.random.rand(num_samples, sequence_len,
                            input_num_row, input_num_col,
                            input_channel)
    # Tests for statefulness
    model = Sequential()
    kwargs = {'data_format': data_format,
              'return_sequences': return_sequences,
              'filters': filters,
              'kernel_size': (num_row, num_col),
              'stateful': True,
              'batch_input_shape': inputs.shape,
              'padding': 'same'}
    layer = convolutional_recurrent.ConvLSTM2D(**kwargs)

    model.add(layer)
    model.compile(optimizer='sgd', loss='mse')
    out1 = model.predict(np.ones_like(inputs))

    # train once so that the states change
    model.train_on_batch(np.ones_like(inputs),
                         np.random.random(out1.shape))
    out2 = model.predict(np.ones_like(inputs))

    # if the state is not reset, output should be different
    assert(out1.max() != out2.max())

    # check that output changes after states are reset
    # (even though the model itself didn't change)
    layer.reset_states()
    out3 = model.predict(np.ones_like(inputs))
    assert(out2.max() != out3.max())

    # check that container-level reset_states() works
    model.reset_states()
    out4 = model.predict(np.ones_like(inputs))
    assert_allclose(out3, out4, atol=1e-5)

    # check that the call to `predict` updated the states
    out5 = model.predict(np.ones_like(inputs))
    assert(out4.max() != out5.max())

    # cntk doesn't support eval convolution with static
    # variable, will enable it later
    if K.backend() != 'cntk':
        # check regularizers
        kwargs = {'data_format': data_format,
                  'return_sequences': return_sequences,
                  'kernel_size': (num_row, num_col),
                  'stateful': True,
                  'filters': filters,
                  'batch_input_shape': inputs.shape,
                  'kernel_regularizer': regularizers.L1L2(l1=0.01),
                  'recurrent_regularizer': regularizers.L1L2(l1=0.01),
                  'bias_regularizer': 'l2',
                  'activity_regularizer': 'l2',
                  'kernel_constraint': 'max_norm',
                  'recurrent_constraint': 'max_norm',
                  'bias_constraint': 'max_norm',
                  'padding': 'same'}

        layer = convolutional_recurrent.ConvLSTM2D(**kwargs)
        layer.build(inputs.shape)
        assert len(layer.losses) == 3
        assert layer.activity_regularizer
        output = layer(K.variable(np.ones(inputs.shape)))
        assert len(layer.losses) == 4
        K.eval(output)

    # check dropout
    layer_test(convolutional_recurrent.ConvLSTM2D,
               kwargs={'data_format': data_format,
                       'return_sequences': return_sequences,
                       'filters': filters,
                       'kernel_size': (num_row, num_col),
                       'padding': 'same',
                       'dropout': 0.1,
                       'recurrent_dropout': 0.1},
               input_shape=inputs.shape)

    # check state initialization
    layer = convolutional_recurrent.ConvLSTM2D(
        filters=filters, kernel_size=(num_row, num_col),
        data_format=data_format, return_sequences=return_sequences)
    layer.build(inputs.shape)
    x = Input(batch_shape=inputs.shape)
    initial_state = layer.get_initial_state(x)
    y = layer(x, initial_state=initial_state)
    model = Model(x, y)
    assert (model.predict(inputs).shape ==
            layer.compute_output_shape(inputs.shape))


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import numpy as np
import copy
from numpy.testing import assert_allclose
from keras.utils import CustomObjectScope
from keras.layers import wrappers, Input, Layer
from keras.layers import RNN
from keras import layers
from keras.models import Sequential, Model, model_from_json
from keras import backend as K
from keras.utils.generic_utils import object_list_uid, to_list


def test_TimeDistributed():
    # first, test with Dense layer
    model = Sequential()
    model.add(wrappers.TimeDistributed(layers.Dense(2), input_shape=(3, 4)))
    model.add(layers.Activation('relu'))
    model.compile(optimizer='rmsprop', loss='mse')
    model.fit(np.random.random((10, 3, 4)), np.random.random((10, 3, 2)),
              epochs=1,
              batch_size=10)

    # test config
    model.get_config()

    # test when specifying a batch_input_shape
    test_input = np.random.random((1, 3, 4))
    test_output = model.predict(test_input)
    weights = model.layers[0].get_weights()

    reference = Sequential()
    reference.add(wrappers.TimeDistributed(layers.Dense(2),
                                           batch_input_shape=(1, 3, 4)))
    reference.add(layers.Activation('relu'))
    reference.compile(optimizer='rmsprop', loss='mse')
    reference.layers[0].set_weights(weights)

    reference_output = reference.predict(test_input)
    assert_allclose(test_output, reference_output, atol=1e-05)

    # test with Embedding
    model = Sequential()
    model.add(wrappers.TimeDistributed(layers.Embedding(5, 6),
                                       batch_input_shape=(10, 3, 4),
                                       dtype='int32'))
    model.compile(optimizer='rmsprop', loss='mse')
    model.fit(np.random.randint(5, size=(10, 3, 4), dtype='int32'),
              np.random.random((10, 3, 4, 6)), epochs=1, batch_size=10)

    # compare to not using batch_input_shape
    test_input = np.random.randint(5, size=(10, 3, 4), dtype='int32')
    test_output = model.predict(test_input)
    weights = model.layers[0].get_weights()

    reference = Sequential()
    reference.add(wrappers.TimeDistributed(layers.Embedding(5, 6),
                                           input_shape=(3, 4), dtype='int32'))
    reference.compile(optimizer='rmsprop', loss='mse')
    reference.layers[0].set_weights(weights)

    reference_output = reference.predict(test_input)
    assert_allclose(test_output, reference_output, atol=1e-05)

    # test with Conv2D
    model = Sequential()
    model.add(wrappers.TimeDistributed(layers.Conv2D(5, (2, 2),
                                                     padding='same'),
                                       input_shape=(2, 4, 4, 3)))
    model.add(layers.Activation('relu'))
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(np.random.random((1, 2, 4, 4, 3)),
                         np.random.random((1, 2, 4, 4, 5)))

    model = model_from_json(model.to_json())
    model.summary()

    # test stacked layers
    model = Sequential()
    model.add(wrappers.TimeDistributed(layers.Dense(2), input_shape=(3, 4)))
    model.add(wrappers.TimeDistributed(layers.Dense(3)))
    model.add(layers.Activation('relu'))
    model.compile(optimizer='rmsprop', loss='mse')

    model.fit(np.random.random((10, 3, 4)), np.random.random((10, 3, 3)),
              epochs=1, batch_size=10)

    # test wrapping Sequential model
    model = Sequential()
    model.add(layers.Dense(3, input_dim=2))
    outer_model = Sequential()
    outer_model.add(wrappers.TimeDistributed(model, input_shape=(3, 2)))
    outer_model.compile(optimizer='rmsprop', loss='mse')
    outer_model.fit(np.random.random((10, 3, 2)), np.random.random((10, 3, 3)),
                    epochs=1, batch_size=10)

    # test with functional API
    x = Input(shape=(3, 2))
    y = wrappers.TimeDistributed(model)(x)
    outer_model = Model(x, y)
    outer_model.compile(optimizer='rmsprop', loss='mse')
    outer_model.fit(np.random.random((10, 3, 2)), np.random.random((10, 3, 3)),
                    epochs=1, batch_size=10)

    # test with BatchNormalization
    model = Sequential()
    model.add(wrappers.TimeDistributed(
        layers.BatchNormalization(center=True, scale=True),
        name='bn', input_shape=(10, 2)))
    model.compile(optimizer='rmsprop', loss='mse')
    # Assert that mean and variance are 0 and 1.
    td = model.layers[0]
    assert np.array_equal(td.get_weights()[2], np.array([0, 0]))
    assert np.array_equal(td.get_weights()[3], np.array([1, 1]))
    # Train
    model.train_on_batch(np.random.normal(loc=2, scale=2, size=(1, 10, 2)),
                         np.broadcast_to(np.array([0, 1]), (1, 10, 2)))
    # Assert that mean and variance changed.
    assert not np.array_equal(td.get_weights()[2], np.array([0, 0]))
    assert not np.array_equal(td.get_weights()[3], np.array([1, 1]))


@pytest.mark.skipif((K.backend() == 'cntk'),
                    reason='Flaky with CNTK backend')
def test_TimeDistributed_learning_phase():
    # test layers that need learning_phase to be set
    np.random.seed(1234)
    x = Input(shape=(3, 2))
    y = wrappers.TimeDistributed(layers.Dropout(.999))(x, training=True)
    model = Model(x, y)
    y = model.predict(np.random.random((10, 3, 2)))
    assert_allclose(np.mean(y), 0., atol=1e-1, rtol=1e-1)


def test_TimeDistributed_trainable():
    # test layers that need learning_phase to be set
    x = Input(shape=(3, 2))
    layer = wrappers.TimeDistributed(layers.BatchNormalization())
    _ = layer(x)
    assert len(layer.trainable_weights) == 2
    layer.trainable = False
    assert len(layer.trainable_weights) == 0
    layer.trainable = True
    assert len(layer.trainable_weights) == 2


@pytest.mark.skipif((K.backend() == 'cntk'),
                    reason='Unknown timestamps for RNN not supported in CNTK.')
def test_TimeDistributed_with_masked_embedding_and_unspecified_shape():
    # test with unspecified shape and Embeddings with mask_zero
    model = Sequential()
    model.add(wrappers.TimeDistributed(layers.Embedding(5, 6, mask_zero=True),
                                       input_shape=(None, None)))
    # the shape so far: (N, t_1, t_2, 6)
    model.add(wrappers.TimeDistributed(layers.SimpleRNN(7, return_sequences=True)))
    model.add(wrappers.TimeDistributed(layers.SimpleRNN(8, return_sequences=False)))
    model.add(layers.SimpleRNN(1, return_sequences=False))
    model.compile(optimizer='rmsprop', loss='mse')
    model_input = np.random.randint(low=1, high=5, size=(10, 3, 4), dtype='int32')
    for i in range(4):
        model_input[i, i:, i:] = 0
    model.fit(model_input,
              np.random.random((10, 1)), epochs=1, batch_size=10)
    mask_outputs = [model.layers[0].compute_mask(model.input)]
    for layer in model.layers[1:]:
        mask_outputs.append(layer.compute_mask(layer.input, mask_outputs[-1]))
    func = K.function([model.input], mask_outputs[:-1])
    mask_outputs_val = func([model_input])
    ref_mask_val_0 = model_input > 0         # embedding layer
    ref_mask_val_1 = ref_mask_val_0          # first RNN layer
    ref_mask_val_2 = np.any(ref_mask_val_1, axis=-1)     # second RNN layer
    ref_mask_val = [ref_mask_val_0, ref_mask_val_1, ref_mask_val_2]
    for i in range(3):
        assert np.array_equal(mask_outputs_val[i], ref_mask_val[i])
    assert mask_outputs[-1] is None  # final layer


def test_TimeDistributed_with_masking_layer():
    # test with Masking layer
    model = Sequential()
    model.add(wrappers.TimeDistributed(layers.Masking(mask_value=0.,),
                                       input_shape=(None, 4)))
    model.add(wrappers.TimeDistributed(layers.Dense(5)))
    model.compile(optimizer='rmsprop', loss='mse')
    model_input = np.random.randint(low=1, high=5, size=(10, 3, 4))
    for i in range(4):
        model_input[i, i:, :] = 0.
    model.compile(optimizer='rmsprop', loss='mse')
    model.fit(model_input,
              np.random.random((10, 3, 5)), epochs=1, batch_size=6)
    mask_outputs = [model.layers[0].compute_mask(model.input)]
    mask_outputs += [model.layers[1].compute_mask(model.layers[1].input,
                                                  mask_outputs[-1])]
    func = K.function([model.input], mask_outputs)
    mask_outputs_val = func([model_input])
    assert np.array_equal(mask_outputs_val[0], np.any(model_input, axis=-1))
    assert np.array_equal(mask_outputs_val[1], np.any(model_input, axis=-1))


def test_regularizers():
    model = Sequential()
    model.add(wrappers.TimeDistributed(
        layers.Dense(2, kernel_regularizer='l1'), input_shape=(3, 4)))
    model.add(layers.Activation('relu'))
    model.compile(optimizer='rmsprop', loss='mse')
    assert len(model.layers[0].layer.losses) == 1
    assert len(model.layers[0].losses) == 1
    assert len(model.layers[0].get_losses_for(None)) == 1
    assert len(model.losses) == 1

    model = Sequential()
    model.add(wrappers.TimeDistributed(
        layers.Dense(2, activity_regularizer='l1'), input_shape=(3, 4)))
    model.add(layers.Activation('relu'))
    model.compile(optimizer='rmsprop', loss='mse')
    assert len(model.losses) == 1


def test_Bidirectional():
    rnn = layers.SimpleRNN
    samples = 2
    dim = 2
    timesteps = 2
    output_dim = 2
    dropout_rate = 0.2
    for mode in ['sum', 'concat']:
        x = np.random.random((samples, timesteps, dim))
        target_dim = 2 * output_dim if mode == 'concat' else output_dim
        y = np.random.random((samples, target_dim))

        # test with Sequential model
        model = Sequential()
        model.add(wrappers.Bidirectional(rnn(output_dim, dropout=dropout_rate,
                                             recurrent_dropout=dropout_rate),
                                         merge_mode=mode,
                                         input_shape=(timesteps, dim)))
        model.compile(loss='mse', optimizer='sgd')
        model.fit(x, y, epochs=1, batch_size=1)

        # test config
        model.get_config()
        model = model_from_json(model.to_json())
        model.summary()

        # test stacked bidirectional layers
        model = Sequential()
        model.add(wrappers.Bidirectional(rnn(output_dim,
                                             return_sequences=True),
                                         merge_mode=mode,
                                         input_shape=(timesteps, dim)))
        model.add(wrappers.Bidirectional(rnn(output_dim), merge_mode=mode))
        model.compile(loss='mse', optimizer='sgd')
        model.fit(x, y, epochs=1, batch_size=1)

        # Bidirectional and stateful
        inputs = Input(batch_shape=(1, timesteps, dim))
        outputs = wrappers.Bidirectional(rnn(output_dim, stateful=True),
                                         merge_mode=mode)(inputs)
        model = Model(inputs, outputs)
        model.compile(loss='mse', optimizer='sgd')
        model.fit(x, y, epochs=1, batch_size=1)


@pytest.mark.skipif((K.backend() == 'cntk'),
                    reason='Unknown timestamps not supported in CNTK.')
def test_Bidirectional_dynamic_timesteps():
    # test with functional API with dynamic length
    rnn = layers.SimpleRNN
    samples = 2
    dim = 2
    timesteps = 2
    output_dim = 2
    dropout_rate = 0.2
    for mode in ['sum', 'concat']:
        x = np.random.random((samples, timesteps, dim))
        target_dim = 2 * output_dim if mode == 'concat' else output_dim
        y = np.random.random((samples, target_dim))

        inputs = Input((None, dim))
        outputs = wrappers.Bidirectional(rnn(output_dim, dropout=dropout_rate,
                                             recurrent_dropout=dropout_rate),
                                         merge_mode=mode)(inputs)
        model = Model(inputs, outputs)
        model.compile(loss='mse', optimizer='sgd')
        model.fit(x, y, epochs=1, batch_size=1)


@pytest.mark.parametrize('merge_mode', ['sum', 'mul', 'ave', 'concat', None])
def test_Bidirectional_merged_value(merge_mode):
    rnn = layers.LSTM
    samples = 2
    dim = 5
    timesteps = 3
    units = 3
    X = [np.random.rand(samples, timesteps, dim)]

    if merge_mode == 'sum':
        merge_func = lambda y, y_rev: y + y_rev
    elif merge_mode == 'mul':
        merge_func = lambda y, y_rev: y * y_rev
    elif merge_mode == 'ave':
        merge_func = lambda y, y_rev: (y + y_rev) / 2
    elif merge_mode == 'concat':
        merge_func = lambda y, y_rev: np.concatenate((y, y_rev), axis=-1)
    else:
        merge_func = lambda y, y_rev: [y, y_rev]

    # basic case
    inputs = Input((timesteps, dim))
    layer = wrappers.Bidirectional(rnn(units, return_sequences=True),
                                   merge_mode=merge_mode)
    f_merged = K.function([inputs], to_list(layer(inputs)))
    f_forward = K.function([inputs], [layer.forward_layer(inputs)])
    f_backward = K.function([inputs],
                            [K.reverse(layer.backward_layer(inputs), 1)])

    y_merged = f_merged(X)
    y_expected = to_list(merge_func(f_forward(X)[0], f_backward(X)[0]))
    assert len(y_merged) == len(y_expected)
    for x1, x2 in zip(y_merged, y_expected):
        assert_allclose(x1, x2, atol=1e-5)

    # test return_state
    inputs = Input((timesteps, dim))
    layer = wrappers.Bidirectional(rnn(units, return_state=True),
                                   merge_mode=merge_mode)
    f_merged = K.function([inputs], layer(inputs))
    f_forward = K.function([inputs], layer.forward_layer(inputs))
    f_backward = K.function([inputs], layer.backward_layer(inputs))
    n_states = len(layer.layer.states)

    y_merged = f_merged(X)
    y_forward = f_forward(X)
    y_backward = f_backward(X)
    y_expected = to_list(merge_func(y_forward[0], y_backward[0]))
    assert len(y_merged) == len(y_expected) + n_states * 2
    for x1, x2 in zip(y_merged, y_expected):
        assert_allclose(x1, x2, atol=1e-5)

    # test if the state of a BiRNN is the concatenation of the underlying RNNs
    y_merged = y_merged[-n_states * 2:]
    y_forward = y_forward[-n_states:]
    y_backward = y_backward[-n_states:]
    for state_birnn, state_inner in zip(y_merged, y_forward + y_backward):
        assert_allclose(state_birnn, state_inner, atol=1e-5)


@pytest.mark.skipif(K.backend() == 'theano', reason='Not supported.')
@pytest.mark.parametrize('merge_mode', ['sum', 'concat', None])
def test_Bidirectional_dropout(merge_mode):
    rnn = layers.LSTM
    samples = 2
    dim = 5
    timesteps = 3
    units = 3
    X = [np.random.rand(samples, timesteps, dim)]

    inputs = Input((timesteps, dim))
    wrapped = wrappers.Bidirectional(rnn(units, dropout=0.2, recurrent_dropout=0.2),
                                     merge_mode=merge_mode)
    outputs = to_list(wrapped(inputs, training=True))

    inputs = Input((timesteps, dim))
    wrapped = wrappers.Bidirectional(rnn(units, dropout=0.2, return_state=True),
                                     merge_mode=merge_mode)
    outputs = to_list(wrapped(inputs))

    model = Model(inputs, outputs)

    y1 = to_list(model.predict(X))
    y2 = to_list(model.predict(X))
    for x1, x2 in zip(y1, y2):
        assert_allclose(x1, x2, atol=1e-5)


def test_Bidirectional_state_reuse():
    rnn = layers.LSTM
    samples = 2
    dim = 5
    timesteps = 3
    units = 3

    input1 = Input((timesteps, dim))
    layer = wrappers.Bidirectional(rnn(units, return_state=True,
                                       return_sequences=True))
    state = layer(input1)[1:]

    # test passing invalid initial_state: passing a tensor
    input2 = Input((timesteps, dim))
    with pytest.raises(ValueError):
        output = wrappers.Bidirectional(rnn(units))(input2, initial_state=state[0])

    # test valid usage: passing a list
    output = wrappers.Bidirectional(rnn(units))(input2, initial_state=state)
    model = Model([input1, input2], output)
    assert len(model.layers) == 4
    assert isinstance(model.layers[-1].input, list)
    inputs = [np.random.rand(samples, timesteps, dim),
              np.random.rand(samples, timesteps, dim)]
    outputs = model.predict(inputs)


def DISABLED_test_Bidirectional_with_constants():
    class RNNCellWithConstants(Layer):
        def __init__(self, units, **kwargs):
            self.units = units
            self.state_size = units
            super(RNNCellWithConstants, self).__init__(**kwargs)

        def build(self, input_shape):
            if not isinstance(input_shape, list):
                raise TypeError('expects constants shape')
            [input_shape, constant_shape] = input_shape
            # will (and should) raise if more than one constant passed

            self.input_kernel = self.add_weight(
                shape=(input_shape[-1], self.units),
                initializer='uniform',
                name='kernel')
            self.recurrent_kernel = self.add_weight(
                shape=(self.units, self.units),
                initializer='uniform',
                name='recurrent_kernel')
            self.constant_kernel = self.add_weight(
                shape=(constant_shape[-1], self.units),
                initializer='uniform',
                name='constant_kernel')
            self.built = True

        def call(self, inputs, states, constants):
            [prev_output] = states
            [constant] = constants
            h_input = K.dot(inputs, self.input_kernel)
            h_state = K.dot(prev_output, self.recurrent_kernel)
            h_const = K.dot(constant, self.constant_kernel)
            output = h_input + h_state + h_const
            return output, [output]

        def get_config(self):
            config = {'units': self.units}
            base_config = super(RNNCellWithConstants, self).get_config()
            return dict(list(base_config.items()) + list(config.items()))

    # Test basic case.
    x = Input((5, 5))
    c = Input((3,))
    cell = RNNCellWithConstants(32)
    custom_objects = {'RNNCellWithConstants': RNNCellWithConstants}
    with CustomObjectScope(custom_objects):
        layer = wrappers.Bidirectional(RNN(cell))
    y = layer(x, constants=c)
    model = Model([x, c], y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(
        [np.zeros((6, 5, 5)), np.zeros((6, 3))],
        np.zeros((6, 64))
    )

    # Test basic case serialization.
    x_np = np.random.random((6, 5, 5))
    c_np = np.random.random((6, 3))
    y_np = model.predict([x_np, c_np])
    weights = model.get_weights()
    config = layer.get_config()
    with CustomObjectScope(custom_objects):
        layer = wrappers.Bidirectional.from_config(copy.deepcopy(config))
    y = layer(x, constants=c)
    model = Model([x, c], y)
    model.set_weights(weights)
    y_np_2 = model.predict([x_np, c_np])
    assert_allclose(y_np, y_np_2, atol=1e-4)

    # test flat list inputs
    with CustomObjectScope(custom_objects):
        layer = wrappers.Bidirectional.from_config(copy.deepcopy(config))
    y = layer([x, c])
    model = Model([x, c], y)
    model.set_weights(weights)
    y_np_3 = model.predict([x_np, c_np])
    assert_allclose(y_np, y_np_3, atol=1e-4)


def DISABLED_test_Bidirectional_with_constants_layer_passing_initial_state():
    class RNNCellWithConstants(Layer):
        def __init__(self, units, **kwargs):
            self.units = units
            self.state_size = units
            super(RNNCellWithConstants, self).__init__(**kwargs)

        def build(self, input_shape):
            if not isinstance(input_shape, list):
                raise TypeError('expects constants shape')
            [input_shape, constant_shape] = input_shape
            # will (and should) raise if more than one constant passed

            self.input_kernel = self.add_weight(
                shape=(input_shape[-1], self.units),
                initializer='uniform',
                name='kernel')
            self.recurrent_kernel = self.add_weight(
                shape=(self.units, self.units),
                initializer='uniform',
                name='recurrent_kernel')
            self.constant_kernel = self.add_weight(
                shape=(constant_shape[-1], self.units),
                initializer='uniform',
                name='constant_kernel')
            self.built = True

        def call(self, inputs, states, constants):
            [prev_output] = states
            [constant] = constants
            h_input = K.dot(inputs, self.input_kernel)
            h_state = K.dot(prev_output, self.recurrent_kernel)
            h_const = K.dot(constant, self.constant_kernel)
            output = h_input + h_state + h_const
            return output, [output]

        def get_config(self):
            config = {'units': self.units}
            base_config = super(RNNCellWithConstants, self).get_config()
            return dict(list(base_config.items()) + list(config.items()))

    # Test basic case.
    x = Input((5, 5))
    c = Input((3,))
    s_for = Input((32,))
    s_bac = Input((32,))
    cell = RNNCellWithConstants(32)
    custom_objects = {'RNNCellWithConstants': RNNCellWithConstants}
    with CustomObjectScope(custom_objects):
        layer = wrappers.Bidirectional(RNN(cell))
    y = layer(x, initial_state=[s_for, s_bac], constants=c)
    model = Model([x, s_for, s_bac, c], y)
    model.compile(optimizer='rmsprop', loss='mse')
    model.train_on_batch(
        [np.zeros((6, 5, 5)), np.zeros((6, 32)),
         np.zeros((6, 32)), np.zeros((6, 3))],
        np.zeros((6, 64))
    )

    # Test basic case serialization.
    x_np = np.random.random((6, 5, 5))
    s_fw_np = np.random.random((6, 32))
    s_bk_np = np.random.random((6, 32))
    c_np = np.random.random((6, 3))
    y_np = model.predict([x_np, s_fw_np, s_bk_np, c_np])
    weights = model.get_weights()
    config = layer.get_config()
    with CustomObjectScope(custom_objects):
        layer = wrappers.Bidirectional.from_config(copy.deepcopy(config))
    y = layer(x, initial_state=[s_for, s_bac], constants=c)
    model = Model([x, s_for, s_bac, c], y)
    model.set_weights(weights)
    y_np_2 = model.predict([x_np, s_fw_np, s_bk_np, c_np])
    assert_allclose(y_np, y_np_2, atol=1e-4)

    # verify that state is used
    y_np_2_different_s = model.predict([x_np, s_fw_np + 10., s_bk_np + 10., c_np])
    with pytest.raises(AssertionError):
        assert_allclose(y_np, y_np_2_different_s, atol=1e-4)

    # test flat list inputs
    with CustomObjectScope(custom_objects):
        layer = wrappers.Bidirectional.from_config(copy.deepcopy(config))
    y = layer([x, s_for, s_bac, c])
    model = Model([x, s_for, s_bac, c], y)
    model.set_weights(weights)
    y_np_3 = model.predict([x_np, s_fw_np, s_bk_np, c_np])
    assert_allclose(y_np, y_np_3, atol=1e-4)


def test_Bidirectional_trainable():
    # test layers that need learning_phase to be set
    x = Input(shape=(3, 2))
    layer = wrappers.Bidirectional(layers.SimpleRNN(3))
    _ = layer(x)
    assert len(layer.trainable_weights) == 6
    layer.trainable = False
    assert len(layer.trainable_weights) == 0
    layer.trainable = True
    assert len(layer.trainable_weights) == 6


def test_Bidirectional_updates():
    x = Input(shape=(3, 2))
    layer = wrappers.Bidirectional(layers.SimpleRNN(3))
    layer.forward_layer.add_update(0, inputs=x)
    layer.forward_layer.add_update(1, inputs=None)
    layer.backward_layer.add_update(0, inputs=x)
    layer.backward_layer.add_update(1, inputs=None)


def test_Bidirectional_losses():
    x = Input(shape=(3, 2))
    layer = wrappers.Bidirectional(
        layers.SimpleRNN(3, kernel_regularizer='l1', bias_regularizer='l1'))
    _ = layer(x)
    layer.forward_layer.add_loss(lambda: 0)
    layer.forward_layer.add_loss(lambda: 1)
    layer.backward_layer.add_loss(lambda: 0)
    layer.backward_layer.add_loss(lambda: 1)


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import numpy as np
from numpy.testing import assert_allclose

from keras import backend as K
from keras import layers
from keras.models import Model
from keras.models import Sequential
from keras.utils.test_utils import layer_test
from keras import regularizers
from keras import constraints
from keras.layers import deserialize as deserialize_layer


def test_masking():
    layer_test(layers.Masking,
               kwargs={},
               input_shape=(3, 2, 3))


def test_dropout():
    layer_test(layers.Dropout,
               kwargs={'rate': 0.5},
               input_shape=(3, 2))

    layer_test(layers.Dropout,
               kwargs={'rate': 0.5, 'noise_shape': [3, 1]},
               input_shape=(3, 2))

    layer_test(layers.Dropout,
               kwargs={'rate': 0.5, 'noise_shape': [None, 1]},
               input_shape=(3, 2))

    layer_test(layers.SpatialDropout1D,
               kwargs={'rate': 0.5},
               input_shape=(2, 3, 4))

    for data_format in ['channels_last', 'channels_first']:
        for shape in [(4, 5), (4, 5, 6)]:
            if data_format == 'channels_last':
                input_shape = (2,) + shape + (3,)
            else:
                input_shape = (2, 3) + shape
            if len(shape) == 2:
                layer = layers.SpatialDropout2D
            else:
                layer = layers.SpatialDropout3D
            layer_test(layer,
                       kwargs={'rate': 0.5,
                               'data_format': data_format},
                       input_shape=input_shape)

            # Test invalid use cases
            with pytest.raises(ValueError):
                layer_test(layer,
                           kwargs={'rate': 0.5,
                                   'data_format': 'channels_middle'},
                           input_shape=input_shape)


def test_activation():
    # with string argument
    layer_test(layers.Activation,
               kwargs={'activation': 'relu'},
               input_shape=(3, 2))

    # with function argument
    layer_test(layers.Activation,
               kwargs={'activation': K.relu},
               input_shape=(3, 2))


@pytest.mark.parametrize('target_shape,input_shape',
                         [((8, 1), (3, 2, 4)),
                          ((-1, 1), (3, 2, 4)),
                          ((1, -1), (3, 2, 4)),
                          ((-1, 1), (None, None, 4))])
def test_reshape(target_shape, input_shape):
    layer_test(layers.Reshape,
               kwargs={'target_shape': target_shape},
               input_shape=input_shape)


def test_permute():
    layer_test(layers.Permute,
               kwargs={'dims': (2, 1)},
               input_shape=(3, 2, 4))


def test_flatten():

    def test_4d():
        np_inp_channels_last = np.arange(24, dtype='float32').reshape(
                                        (1, 4, 3, 2))

        np_output_cl = layer_test(layers.Flatten,
                                  kwargs={'data_format':
                                          'channels_last'},
                                  input_data=np_inp_channels_last)

        np_inp_channels_first = np.transpose(np_inp_channels_last,
                                             [0, 3, 1, 2])

        np_output_cf = layer_test(layers.Flatten,
                                  kwargs={'data_format':
                                          'channels_first'},
                                  input_data=np_inp_channels_first,
                                  expected_output=np_output_cl)

    def test_3d():
        np_inp_channels_last = np.arange(12, dtype='float32').reshape(
            (1, 4, 3))

        np_output_cl = layer_test(layers.Flatten,
                                  kwargs={'data_format':
                                          'channels_last'},
                                  input_data=np_inp_channels_last)

        np_inp_channels_first = np.transpose(np_inp_channels_last,
                                             [0, 2, 1])

        np_output_cf = layer_test(layers.Flatten,
                                  kwargs={'data_format':
                                          'channels_first'},
                                  input_data=np_inp_channels_first,
                                  expected_output=np_output_cl)

    def test_5d():
        np_inp_channels_last = np.arange(120, dtype='float32').reshape(
            (1, 5, 4, 3, 2))

        np_output_cl = layer_test(layers.Flatten,
                                  kwargs={'data_format':
                                          'channels_last'},
                                  input_data=np_inp_channels_last)

        np_inp_channels_first = np.transpose(np_inp_channels_last,
                                             [0, 4, 1, 2, 3])

        np_output_cf = layer_test(layers.Flatten,
                                  kwargs={'data_format':
                                          'channels_first'},
                                  input_data=np_inp_channels_first,
                                  expected_output=np_output_cl)
    test_3d()
    test_4d()
    test_5d()


def test_repeat_vector():
    layer_test(layers.RepeatVector,
               kwargs={'n': 3},
               input_shape=(3, 2))


def test_lambda():
    layer_test(layers.Lambda,
               kwargs={'function': lambda x: x + 1},
               input_shape=(3, 2))

    layer_test(layers.Lambda,
               kwargs={'function': lambda x, a, b: x * a + b,
                       'arguments': {'a': 0.6, 'b': 0.4}},
               input_shape=(3, 2))

    def antirectifier(x):
        x -= K.mean(x, axis=1, keepdims=True)
        x = K.l2_normalize(x, axis=1)
        pos = K.relu(x)
        neg = K.relu(-x)
        return K.concatenate([pos, neg], axis=1)

    def antirectifier_output_shape(input_shape):
        shape = list(input_shape)
        assert len(shape) == 2  # only valid for 2D tensors
        shape[-1] *= 2
        return tuple(shape)

    layer_test(layers.Lambda,
               kwargs={'function': antirectifier,
                       'output_shape': antirectifier_output_shape},
               input_shape=(3, 2))

    # test layer with multiple outputs
    def test_multiple_outputs():
        def func(x):
            return [x * 0.2, x * 0.3]

        def output_shape(input_shape):
            return [input_shape, input_shape]

        def mask(inputs, mask=None):
            return [None, None]

        i = layers.Input(shape=(3, 2, 1))
        o = layers.Lambda(function=func,
                          output_shape=output_shape,
                          mask=mask)(i)

        o1, o2 = o

        model = Model(i, o)

        x = np.random.random((4, 3, 2, 1))
        out1, out2 = model.predict(x)
        assert out1.shape == (4, 3, 2, 1)
        assert out2.shape == (4, 3, 2, 1)
        assert_allclose(out1, x * 0.2, atol=1e-4)
        assert_allclose(out2, x * 0.3, atol=1e-4)

    test_multiple_outputs()

    # test layer with multiple outputs and no
    # explicit mask
    def test_multiple_outputs_no_mask():
        def func(x):
            return [x * 0.2, x * 0.3]

        def output_shape(input_shape):
            return [input_shape, input_shape]

        i = layers.Input(shape=(3, 2, 1))
        o = layers.Lambda(function=func,
                          output_shape=output_shape)(i)

        o = layers.add(o)
        model = Model(i, o)

        i2 = layers.Input(shape=(3, 2, 1))
        o2 = model(i2)
        model2 = Model(i2, o2)

        x = np.random.random((4, 3, 2, 1))
        out = model2.predict(x)
        assert out.shape == (4, 3, 2, 1)
        assert_allclose(out, x * 0.2 + x * 0.3, atol=1e-4)

    test_multiple_outputs_no_mask()

    # test serialization with function
    def f(x):
        return x + 1

    ld = layers.Lambda(f)
    config = ld.get_config()
    ld = deserialize_layer({'class_name': 'Lambda', 'config': config})

    # test with lambda
    ld = layers.Lambda(
        lambda x: K.concatenate([K.square(x), x]),
        output_shape=lambda s: tuple(list(s)[:-1] + [2 * s[-1]]))
    config = ld.get_config()
    ld = layers.Lambda.from_config(config)

    # test serialization with output_shape function
    def f(x):
        return K.concatenate([K.square(x), x])

    def f_shape(s):
        return tuple(list(s)[:-1] + [2 * s[-1]])

    ld = layers.Lambda(f, output_shape=f_shape)
    config = ld.get_config()
    ld = deserialize_layer({'class_name': 'Lambda', 'config': config})


@pytest.mark.skipif((K.backend() == 'theano'),
                    reason="theano cannot compute "
                           "the output shape automatically.")
def test_lambda_output_shape():
    layer_test(layers.Lambda,
               kwargs={'function': lambda x: K.mean(x, axis=-1)},
               input_shape=(3, 2, 4))


def test_dense():
    layer_test(layers.Dense,
               kwargs={'units': 3},
               input_shape=(3, 2))

    layer_test(layers.Dense,
               kwargs={'units': 3},
               input_shape=(3, 4, 2))

    layer_test(layers.Dense,
               kwargs={'units': 3},
               input_shape=(None, None, 2))

    layer_test(layers.Dense,
               kwargs={'units': 3},
               input_shape=(3, 4, 5, 2))

    layer_test(layers.Dense,
               kwargs={'units': 3,
                       'kernel_regularizer': regularizers.l2(0.01),
                       'bias_regularizer': regularizers.l1(0.01),
                       'activity_regularizer': regularizers.L1L2(l1=0.01, l2=0.01),
                       'kernel_constraint': constraints.MaxNorm(1),
                       'bias_constraint': constraints.max_norm(1)},
               input_shape=(3, 2))

    layer = layers.Dense(3,
                         kernel_regularizer=regularizers.l1(0.01),
                         bias_regularizer='l1')
    layer.build((None, 4))
    assert len(layer.losses) == 2


def test_activity_regularization():
    layer = layers.ActivityRegularization(l1=0.01, l2=0.01)

    # test in functional API
    x = layers.Input(shape=(3,))
    z = layers.Dense(2)(x)
    y = layer(z)
    model = Model(x, y)
    model.compile('rmsprop', 'mse')

    model.predict(np.random.random((2, 3)))

    # test serialization
    model_config = model.get_config()
    model = Model.from_config(model_config)
    model.compile('rmsprop', 'mse')


def DISABLED_test_sequential_as_downstream_of_masking_layer():

    inputs = layers.Input(shape=(3, 4))
    x = layers.Masking(mask_value=0., input_shape=(3, 4))(inputs)
    s = Sequential()
    s.add(layers.Dense(5, input_shape=(4,)))
    s.add(layers.Activation('relu'))
    x = layers.TimeDistributed(s)(x)
    model = Model(inputs=inputs, outputs=x)
    model.compile(optimizer='rmsprop', loss='mse')
    model_input = np.random.randint(low=1, high=5, size=(10, 3, 4))
    for i in range(4):
        model_input[i, i:, :] = 0.
    model.fit(model_input,
              np.random.random((10, 3, 5)), epochs=1, batch_size=6)

    mask_outputs = [model.layers[1].compute_mask(model.layers[1].input)]
    mask_outputs += [model.layers[2].compute_mask(model.layers[2].input,
                                                  mask_outputs[-1])]
    func = K.function([inputs], mask_outputs)
    mask_outputs_val = func([model_input])
    assert np.array_equal(mask_outputs_val[0], np.any(model_input, axis=-1))
    assert np.array_equal(mask_outputs_val[1], np.any(model_input, axis=-1))


if __name__ == '__main__':
    pytest.main([__file__])

import numpy as np
import pytest

from keras.utils.test_utils import layer_test
from keras import layers
from keras.models import Sequential


@pytest.mark.parametrize(
    'padding,stride,data_format',
    [(padding, stride, data_format)
     for padding in ['valid', 'same']
     for stride in [1, 2]
     for data_format in ['channels_first', 'channels_last']]
)
def test_maxpooling_1d(padding, stride, data_format):
    layer_test(layers.MaxPooling1D,
               kwargs={'strides': stride,
                       'padding': padding,
                       'data_format': data_format},
               input_shape=(3, 5, 4))


@pytest.mark.parametrize(
    'strides',
    [(1, 1), (2, 3)]
)
def test_maxpooling_2d(strides):
    pool_size = (3, 3)
    layer_test(layers.MaxPooling2D,
               kwargs={'strides': strides,
                       'padding': 'valid',
                       'pool_size': pool_size},
               input_shape=(3, 5, 6, 4))


@pytest.mark.parametrize(
    'strides,data_format,input_shape',
    [(2, None, (3, 11, 12, 10, 4)),
     (3, 'channels_first', (3, 4, 11, 12, 10))]
)
def test_maxpooling_3d(strides, data_format, input_shape):
    pool_size = (3, 3, 3)
    layer_test(layers.MaxPooling3D,
               kwargs={'strides': strides,
                       'padding': 'valid',
                       'data_format': data_format,
                       'pool_size': pool_size},
               input_shape=input_shape)


@pytest.mark.parametrize(
    'padding,stride,data_format',
    [(padding, stride, data_format)
     for padding in ['valid', 'same']
     for stride in [1, 2]
     for data_format in ['channels_first', 'channels_last']]
)
def test_averagepooling_1d(padding, stride, data_format):
    layer_test(layers.AveragePooling1D,
               kwargs={'strides': stride,
                       'padding': padding,
                       'data_format': data_format},
               input_shape=(3, 5, 4))


@pytest.mark.parametrize(
    'strides,padding,data_format,input_shape',
    [((2, 2), 'same', None, (3, 5, 6, 4)),
     ((2, 2), 'valid', None, (3, 5, 6, 4))]
)
def test_averagepooling_2d(strides, padding, data_format, input_shape):
    layer_test(layers.AveragePooling2D,
               kwargs={'strides': strides,
                       'padding': padding,
                       'pool_size': (2, 2),
                       'data_format': data_format},
               input_shape=input_shape)


@pytest.mark.parametrize(
    'strides,data_format,input_shape',
    [(2, None, (3, 11, 12, 10, 4)),
     (3, 'channels_first', (3, 4, 11, 12, 10))]
)
def test_averagepooling_3d(strides, data_format, input_shape):
    pool_size = (3, 3, 3)

    layer_test(layers.AveragePooling3D,
               kwargs={'strides': strides,
                       'padding': 'valid',
                       'data_format': data_format,
                       'pool_size': pool_size},
               input_shape=input_shape)


@pytest.mark.parametrize(
    'data_format,pooling_class',
    [(data_format, pooling_class)
     for data_format in ['channels_first', 'channels_last']
     for pooling_class in [layers.GlobalMaxPooling1D,
                           layers.GlobalAveragePooling1D]]
)
def test_globalpooling_1d(data_format, pooling_class):
    layer_test(pooling_class,
               kwargs={'data_format': data_format},
               input_shape=(3, 4, 5))


def test_globalpooling_1d_supports_masking():
    # Test GlobalAveragePooling1D supports masking
    model = Sequential()
    model.add(layers.Masking(mask_value=0., input_shape=(3, 4)))
    model.add(layers.GlobalAveragePooling1D())
    model.compile(loss='mae', optimizer='adam')

    model_input = np.random.randint(low=1, high=5, size=(2, 3, 4))
    model_input[0, 1:, :] = 0
    output = model.predict(model_input)
    assert np.array_equal(output[0], model_input[0, 0, :])


@pytest.mark.parametrize(
    'data_format,pooling_class',
    [(data_format, pooling_class)
     for data_format in ['channels_first', 'channels_last']
     for pooling_class in [layers.GlobalMaxPooling2D,
                           layers.GlobalAveragePooling2D]]
)
def test_globalpooling_2d(data_format, pooling_class):
    layer_test(pooling_class,
               kwargs={'data_format': data_format},
               input_shape=(3, 4, 5, 6))


@pytest.mark.parametrize(
    'data_format,pooling_class',
    [(data_format, pooling_class)
     for data_format in ['channels_first', 'channels_last']
     for pooling_class in [layers.GlobalMaxPooling3D,
                           layers.GlobalAveragePooling3D]]
)
def test_globalpooling_3d(data_format, pooling_class):
    layer_test(pooling_class,
               kwargs={'data_format': data_format},
               input_shape=(3, 4, 3, 4, 3))


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import numpy as np
from numpy.testing import assert_allclose

from keras.utils.test_utils import layer_test
from keras import backend as K
from keras.layers import convolutional
from keras.models import Sequential


# TensorFlow does not support full convolution.
if K.backend() == 'theano':
    _convolution_paddings = ['valid', 'same', 'full']
else:
    _convolution_paddings = ['valid', 'same']


@pytest.mark.parametrize(
    'layer_kwargs,input_length,expected_output',
    [
        # Causal
        ({'filters': 1, 'kernel_size': 2, 'dilation_rate': 1, 'padding': 'causal',
          'kernel_initializer': 'ones', 'use_bias': False},
         4, [[[0], [1], [3], [5]]]),
        # Non-causal
        ({'filters': 1, 'kernel_size': 2, 'dilation_rate': 1, 'padding': 'valid',
          'kernel_initializer': 'ones', 'use_bias': False},
         4, [[[1], [3], [5]]]),
        # Causal dilated with larger kernel size
        ({'filters': 1, 'kernel_size': 3, 'dilation_rate': 2, 'padding': 'causal',
          'kernel_initializer': 'ones', 'use_bias': False},
         10, np.float32([[[0], [1], [2], [4], [6], [9], [12], [15], [18], [21]]])),
    ]
)
def test_causal_dilated_conv(layer_kwargs, input_length, expected_output):
    input_data = np.reshape(np.arange(input_length, dtype='float32'),
                            (1, input_length, 1))
    layer_test(convolutional.Conv1D, input_data=input_data,
               kwargs=layer_kwargs, expected_output=expected_output)


@pytest.mark.parametrize(
    'padding,strides',
    [(padding, strides)
     for padding in _convolution_paddings
     for strides in [1, 2]
     if not (padding == 'same' and strides != 1)]
)
def test_conv_1d(padding, strides):
    batch_size = 2
    steps = 8
    input_dim = 2
    kernel_size = 3
    filters = 3

    layer_test(convolutional.Conv1D,
               kwargs={'filters': filters,
                       'kernel_size': kernel_size,
                       'padding': padding,
                       'strides': strides},
               input_shape=(batch_size, steps, input_dim))

    layer_test(convolutional.Conv1D,
               kwargs={'filters': filters,
                       'kernel_size': kernel_size,
                       'padding': padding,
                       'kernel_regularizer': 'l2',
                       'bias_regularizer': 'l2',
                       'activity_regularizer': 'l2',
                       'kernel_constraint': 'max_norm',
                       'bias_constraint': 'max_norm',
                       'strides': strides},
               input_shape=(batch_size, steps, input_dim))


def test_conv_1d_dilation():
    batch_size = 2
    steps = 8
    input_dim = 2
    kernel_size = 3
    filters = 3
    padding = _convolution_paddings[-1]

    layer_test(convolutional.Conv1D,
               kwargs={'filters': filters,
                       'kernel_size': kernel_size,
                       'padding': padding,
                       'dilation_rate': 2},
               input_shape=(batch_size, steps, input_dim))


def DISABLED_test_conv_1d_channels_first():
    batch_size = 2
    steps = 8
    input_dim = 2
    kernel_size = 3
    filters = 3

    layer_test(convolutional.Conv1D,
               kwargs={'filters': filters,
                       'kernel_size': kernel_size,
                       'data_format': 'channels_first'},
               input_shape=(batch_size, input_dim, steps))


@pytest.mark.parametrize(
    'strides,padding',
    [(strides, padding)
     for padding in _convolution_paddings
     for strides in [(1, 1), (2, 2)]
     if not (padding == 'same' and strides != (1, 1))]
)
def test_convolution_2d(strides, padding):
    num_samples = 2
    filters = 2
    stack_size = 3
    kernel_size = (3, 2)
    num_row = 7
    num_col = 6

    layer_test(convolutional.Conv2D,
               kwargs={'filters': filters,
                       'kernel_size': kernel_size,
                       'padding': padding,
                       'strides': strides,
                       'data_format': 'channels_last'},
               input_shape=(num_samples, stack_size, num_row, num_col))


def test_convolution_2d_dilation():
    num_samples = 2
    filters = 2
    stack_size = 3
    kernel_size = (3, 2)
    num_row = 7
    num_col = 6
    padding = 'valid'

    layer_test(convolutional.Conv2D,
               kwargs={'filters': filters,
                       'kernel_size': kernel_size,
                       'padding': padding,
                       'dilation_rate': (2, 2)},
               input_shape=(num_samples, num_row, num_col, stack_size))


def test_convolution_2d_invalid():
    filters = 2
    padding = _convolution_paddings[-1]
    kernel_size = (3, 2)

    with pytest.raises(ValueError):
        model = Sequential([convolutional.Conv2D(
            filters=filters, kernel_size=kernel_size, padding=padding,
            batch_input_shape=(None, None, 5, None))])


@pytest.mark.parametrize(
    'padding,out_padding,strides',
    [(padding, out_padding, strides)
     for padding in _convolution_paddings
     for out_padding in [None, (0, 0), (1, 1)]
     for strides in [(1, 1), (2, 2)]
     if (not (padding == 'same' and strides != (1, 1))
         and not(strides == (1, 1) and out_padding == (1, 1)))]
)
def test_conv2d_transpose(padding, out_padding, strides):
    num_samples = 2
    filters = 2
    stack_size = 3
    num_row = 5
    num_col = 6

    layer_test(convolutional.Conv2DTranspose,
               kwargs={'filters': filters,
                       'kernel_size': 3,
                       'padding': padding,
                       'output_padding': out_padding,
                       'strides': strides,
                       'data_format': 'channels_last'},
               input_shape=(num_samples, num_row, num_col, stack_size),
               fixed_batch_size=True)


def test_conv2d_transpose_dilation():

    layer_test(convolutional.Conv2DTranspose,
               kwargs={'filters': 2,
                       'kernel_size': 3,
                       'padding': 'same',
                       'data_format': 'channels_last',
                       'dilation_rate': (2, 2)},
               input_shape=(2, 5, 6, 3))

    # Check dilated conv transpose returns expected output
    input_data = np.arange(48).reshape((1, 4, 4, 3)).astype(np.float32)
    expected_output = np.float32([[192, 228, 192, 228],
                                  [336, 372, 336, 372],
                                  [192, 228, 192, 228],
                                  [336, 372, 336, 372]]).reshape((1, 4, 4, 1))

    layer_test(convolutional.Conv2DTranspose,
               input_data=input_data,
               kwargs={'filters': 1,
                       'kernel_size': 3,
                       'padding': 'same',
                       'data_format': 'channels_last',
                       'dilation_rate': (2, 2),
                       'kernel_initializer': 'ones'},
               expected_output=expected_output)


def test_conv2d_transpose_channels_first():
    num_samples = 2
    filters = 2
    stack_size = 3
    num_row = 5
    num_col = 6
    padding = 'valid'
    strides = (2, 2)

    layer_test(convolutional.Conv2DTranspose,
               kwargs={'filters': filters,
                       'kernel_size': 3,
                       'padding': padding,
                       'data_format': 'channels_first',
                       'activation': None,
                       'kernel_regularizer': 'l2',
                       'bias_regularizer': 'l2',
                       'activity_regularizer': 'l2',
                       'kernel_constraint': 'max_norm',
                       'bias_constraint': 'max_norm',
                       'strides': strides},
               input_shape=(num_samples, stack_size, num_row, num_col),
               fixed_batch_size=True)


def test_conv2d_transpose_invalid():
    filters = 2
    stack_size = 3
    num_row = 5
    num_col = 6
    padding = 'valid'

    with pytest.raises(ValueError):
        model = Sequential([convolutional.Conv2DTranspose(
            filters=filters,
            kernel_size=3,
            padding=padding,
            use_bias=True,
            batch_input_shape=(None, None, 5, None))])

    # Test invalid output padding for given stride. Output padding equal to stride
    with pytest.raises(ValueError):
        model = Sequential([convolutional.Conv2DTranspose(
            filters=filters,
            kernel_size=3,
            padding=padding,
            output_padding=(0, 3),
            strides=(1, 3),
            batch_input_shape=(None, num_row, num_col, stack_size))])

    # Output padding greater than stride
    with pytest.raises(ValueError):
        model = Sequential([convolutional.Conv2DTranspose(
            filters=filters,
            kernel_size=3,
            padding=padding,
            output_padding=(2, 2),
            strides=(1, 3),
            batch_input_shape=(None, num_row, num_col, stack_size))])


@pytest.mark.parametrize(
    'padding,strides,multiplier,dilation_rate',
    [(padding, strides, multiplier, dilation_rate)
     for padding in _convolution_paddings
     for strides in [1, 2]
     for multiplier in [1, 2]
     for dilation_rate in [1, 2]
     if (not (padding == 'same' and strides != 1)
         and not (dilation_rate != 1 and strides != 1)
         and not (dilation_rate != 1 and K.backend() == 'cntk'))]
)
def test_separable_conv_1d(padding, strides, multiplier, dilation_rate):
    num_samples = 2
    filters = 6
    stack_size = 3
    num_step = 9

    layer_test(convolutional.SeparableConv1D,
               kwargs={'filters': filters,
                       'kernel_size': 3,
                       'padding': padding,
                       'strides': strides,
                       'depth_multiplier': multiplier,
                       'dilation_rate': dilation_rate},
               input_shape=(num_samples, num_step, stack_size))


def test_separable_conv_1d_additional_args():
    num_samples = 2
    filters = 6
    stack_size = 3
    num_step = 9
    padding = 'valid'
    multiplier = 2

    layer_test(convolutional.SeparableConv1D,
               kwargs={'filters': filters,
                       'kernel_size': 3,
                       'padding': padding,
                       # 'data_format': 'channels_first',
                       'activation': None,
                       'depthwise_regularizer': 'l2',
                       'pointwise_regularizer': 'l2',
                       'bias_regularizer': 'l2',
                       'activity_regularizer': 'l2',
                       'pointwise_constraint': 'unit_norm',
                       'depthwise_constraint': 'unit_norm',
                       'strides': 1,
                       'use_bias': True,
                       'depth_multiplier': multiplier},
               input_shape=(num_samples, stack_size, num_step))


def test_separable_conv_1d_invalid():
    filters = 6
    padding = 'valid'
    with pytest.raises(ValueError):
        model = Sequential([convolutional.SeparableConv1D(
            filters=filters, kernel_size=3, padding=padding,
            batch_input_shape=(None, 5, None))])


@pytest.mark.parametrize(
    'padding,strides,multiplier,dilation_rate',
    [(padding, strides, multiplier, dilation_rate)
     for padding in _convolution_paddings
     for strides in [(1, 1), (2, 2)]
     for multiplier in [1, 2]
     for dilation_rate in [(1, 1), (2, 2), (2, 1), (1, 2)]
     if (not (padding == 'same' and strides != (1, 1))
         and not (dilation_rate != (1, 1) and strides != (1, 1))
         and not (dilation_rate != (1, 1) and multiplier == dilation_rate[0])
         and not (dilation_rate != (1, 1) and K.backend() == 'cntk'))]
)
def test_separable_conv_2d(padding, strides, multiplier, dilation_rate):
    num_samples = 2
    filters = 6
    stack_size = 3
    num_row = 7
    num_col = 6

    layer_test(
        convolutional.SeparableConv2D,
        kwargs={'filters': filters,
                'kernel_size': (3, 3),
                'padding': padding,
                'strides': strides,
                'depth_multiplier': multiplier,
                'dilation_rate': dilation_rate},
        input_shape=(num_samples, num_row, num_col, stack_size))


def test_separable_conv_2d_additional_args():
    num_samples = 2
    filters = 6
    stack_size = 3
    num_row = 7
    num_col = 6
    padding = 'valid'
    strides = (2, 2)
    multiplier = 2

    layer_test(convolutional.SeparableConv2D,
               kwargs={'filters': filters,
                       'kernel_size': 3,
                       'padding': padding,
                       # 'data_format': 'channels_first',
                       'activation': None,
                       'depthwise_regularizer': 'l2',
                       'pointwise_regularizer': 'l2',
                       'bias_regularizer': 'l2',
                       'activity_regularizer': 'l2',
                       'pointwise_constraint': 'unit_norm',
                       'depthwise_constraint': 'unit_norm',
                       'strides': strides,
                       'depth_multiplier': multiplier},
               input_shape=(num_samples, stack_size, num_row, num_col))


def test_separable_conv_2d_invalid():
    filters = 6
    padding = 'valid'
    with pytest.raises(ValueError):
        model = Sequential([convolutional.SeparableConv2D(
            filters=filters, kernel_size=3, padding=padding,
            batch_input_shape=(None, None, 5, None))])


@pytest.mark.parametrize(
    'padding,strides,multiplier,dilation_rate',
    [(padding, strides, multiplier, dilation_rate)
     for padding in _convolution_paddings
     for strides in [(1, 1), (2, 2)]
     for multiplier in [1, 2]
     for dilation_rate in [(1, 1), (2, 2), (2, 1), (1, 2)]
     if (not (padding == 'same' and strides != (1, 1))
         and not (dilation_rate != (1, 1) and strides != (1, 1))
         and not (dilation_rate != (1, 1) and multiplier == dilation_rate[0])
         and not (dilation_rate != (1, 1) and K.backend() == 'cntk'))]
)
def test_depthwise_conv_2d(padding, strides, multiplier, dilation_rate):
    num_samples = 2
    stack_size = 3
    num_row = 7
    num_col = 6

    layer_test(convolutional.DepthwiseConv2D,
               kwargs={'kernel_size': (3, 3),
                       'padding': padding,
                       'strides': strides,
                       'depth_multiplier': multiplier,
                       'dilation_rate': dilation_rate},
               input_shape=(num_samples,
                            num_row,
                            num_col,
                            stack_size))


def test_depthwise_conv_2d_additional_args():
    num_samples = 2
    stack_size = 3
    num_row = 7
    num_col = 6
    padding = 'valid'
    strides = (2, 2)
    multiplier = 2

    layer_test(convolutional.DepthwiseConv2D,
               kwargs={'kernel_size': 3,
                       'padding': padding,
                       # 'data_format': 'channels_first',
                       'activation': None,
                       'depthwise_regularizer': 'l2',
                       'bias_regularizer': 'l2',
                       'activity_regularizer': 'l2',
                       'depthwise_constraint': 'unit_norm',
                       'use_bias': True,
                       'strides': strides,
                       'depth_multiplier': multiplier},
               input_shape=(num_samples, stack_size, num_row, num_col))


def test_depthwise_conv_2d_invalid():
    padding = 'valid'
    with pytest.raises(ValueError):
        Sequential([convolutional.DepthwiseConv2D(
            kernel_size=3,
            padding=padding,
            batch_input_shape=(None, None, 5, None))])


@pytest.mark.parametrize(
    'padding,strides',
    [(padding, strides)
     for padding in _convolution_paddings
     for strides in [(1, 1, 1), (2, 2, 2)]
     if not (padding == 'same' and strides != (1, 1, 1))]
)
def test_convolution_3d(padding, strides):
    num_samples = 2
    filters = 2
    stack_size = 3

    input_len_dim1 = 9
    input_len_dim2 = 8
    input_len_dim3 = 8

    layer_test(convolutional.Convolution3D,
               kwargs={'filters': filters,
                       'kernel_size': 3,
                       'padding': padding,
                       'strides': strides},
               input_shape=(num_samples,
                            input_len_dim1, input_len_dim2, input_len_dim3,
                            stack_size))


def test_convolution_3d_additional_args():
    num_samples = 2
    filters = 2
    stack_size = 3
    padding = 'valid'
    strides = (2, 2, 2)

    input_len_dim1 = 9
    input_len_dim2 = 8
    input_len_dim3 = 8

    layer_test(convolutional.Convolution3D,
               kwargs={'filters': filters,
                       'kernel_size': (1, 2, 3),
                       'padding': padding,
                       'activation': None,
                       'kernel_regularizer': 'l2',
                       'bias_regularizer': 'l2',
                       'activity_regularizer': 'l2',
                       'kernel_constraint': 'max_norm',
                       'bias_constraint': 'max_norm',
                       'strides': strides},
               input_shape=(num_samples,
                            input_len_dim1, input_len_dim2, input_len_dim3,
                            stack_size))


@pytest.mark.parametrize(
    'padding,out_padding,strides,data_format',
    [(padding, out_padding, strides, data_format)
     for padding in _convolution_paddings
     for out_padding in [None, (0, 0, 0), (1, 1, 1)]
     for strides in [(1, 1, 1), (2, 2, 2)]
     # for data_format in ['channels_first', 'channels_last']
     for data_format in ['channels_last']
     if (not (padding == 'same' and strides != (1, 1, 1))
         and not (strides == (1, 1, 1) and out_padding == (1, 1, 1)))]
)
def test_conv3d_transpose(padding, out_padding, strides, data_format):
    filters = 2
    stack_size = 3
    num_depth = 7
    num_row = 5
    num_col = 6

    layer_test(
        convolutional.Conv3DTranspose,
        kwargs={'filters': filters,
                'kernel_size': 3,
                'padding': padding,
                'output_padding': out_padding,
                'strides': strides,
                'data_format': data_format},
        input_shape=(None, num_depth, num_row, num_col, stack_size),
        fixed_batch_size=True)


def test_conv3d_transpose_additional_args():
    filters = 2
    stack_size = 3
    num_depth = 7
    num_row = 5
    num_col = 6
    padding = 'valid'
    strides = (2, 2, 2)

    layer_test(convolutional.Conv3DTranspose,
               kwargs={'filters': filters,
                       'kernel_size': 3,
                       'padding': padding,
                       # 'data_format': 'channels_first',
                       'activation': None,
                       'kernel_regularizer': 'l2',
                       'bias_regularizer': 'l2',
                       'activity_regularizer': 'l2',
                       'kernel_constraint': 'max_norm',
                       'bias_constraint': 'max_norm',
                       'use_bias': True,
                       'strides': strides},
               input_shape=(None, stack_size, num_depth, num_row, num_col),
               fixed_batch_size=True)


def test_conv3d_transpose_invalid():
    filters = 2
    stack_size = 3
    num_depth = 7
    num_row = 5
    num_col = 6
    padding = 'valid'

    # Test invalid use case
    with pytest.raises(ValueError):
        model = Sequential([convolutional.Conv3DTranspose(
            filters=filters,
            kernel_size=3,
            padding=padding,
            batch_input_shape=(None, None, 5, None, None))])

    # Test invalid output padding for given stride. Output padding equal
    # to stride
    with pytest.raises(ValueError):
        model = Sequential([convolutional.Conv3DTranspose(
            filters=filters,
            kernel_size=3,
            padding=padding,
            output_padding=(0, 3, 3),
            strides=(1, 3, 4),
            batch_input_shape=(None, num_depth, num_row, num_col, stack_size))])

    # Output padding greater than stride
    with pytest.raises(ValueError):
        model = Sequential([convolutional.Conv3DTranspose(
            filters=filters,
            kernel_size=3,
            padding=padding,
            output_padding=(2, 2, 3),
            strides=(1, 3, 4),
            batch_input_shape=(None, num_depth, num_row, num_col, stack_size))])


def test_zero_padding_1d():
    num_samples = 2
    input_dim = 2
    num_steps = 5
    shape = (num_samples, num_steps, input_dim)
    inputs = np.ones(shape)

    # basic test
    layer_test(convolutional.ZeroPadding1D,
               kwargs={'padding': 2},
               input_shape=inputs.shape)
    layer_test(convolutional.ZeroPadding1D,
               kwargs={'padding': (1, 2)},
               input_shape=inputs.shape)

    # correctness test
    layer = convolutional.ZeroPadding1D(padding=2)
    layer.build(shape)
    outputs = layer(K.variable(inputs))
    np_output = K.eval(outputs)
    for offset in [0, 1, -1, -2]:
        assert_allclose(np_output[:, offset, :], 0.)
    assert_allclose(np_output[:, 2:-2, :], 1.)

    layer = convolutional.ZeroPadding1D(padding=(1, 2))
    layer.build(shape)
    outputs = layer(K.variable(inputs))
    np_output = K.eval(outputs)
    for left_offset in [0]:
        assert_allclose(np_output[:, left_offset, :], 0.)
    for right_offset in [-1, -2]:
        assert_allclose(np_output[:, right_offset, :], 0.)
    assert_allclose(np_output[:, 1:-2, :], 1.)
    layer.get_config()


@pytest.mark.parametrize(
    'data_format,padding',
    [(data_format, padding)
     for data_format in ['channels_first', 'channels_last']
     for padding in [(2, 2), ((1, 2), (3, 4))]]
)
def test_zero_padding_2d(data_format, padding):
    num_samples = 2
    stack_size = 2
    input_num_row = 4
    input_num_col = 5

    if data_format == 'channels_last':
        inputs = np.ones((num_samples, input_num_row, input_num_col, stack_size))
    else:
        inputs = np.ones((num_samples, stack_size, input_num_row, input_num_col))

    layer_test(convolutional.ZeroPadding2D,
               kwargs={'padding': padding, 'data_format': data_format},
               input_shape=inputs.shape)


@pytest.mark.parametrize('data_format',
                         ['channels_first', 'channels_last'])
def test_zero_padding_2d_correctness(data_format):
    num_samples = 2
    stack_size = 2
    input_num_row = 4
    input_num_col = 5
    inputs = np.ones((num_samples, stack_size, input_num_row, input_num_col))

    layer = convolutional.ZeroPadding2D(padding=(2, 2),
                                        data_format=data_format)
    layer.build(inputs.shape)
    outputs = layer(K.variable(inputs))
    np_output = K.eval(outputs)
    if data_format == 'channels_last':
        for offset in [0, 1, -1, -2]:
            assert_allclose(np_output[:, offset, :, :], 0.)
            assert_allclose(np_output[:, :, offset, :], 0.)
        assert_allclose(np_output[:, 2:-2, 2:-2, :], 1.)
    elif data_format == 'channels_first':
        for offset in [0, 1, -1, -2]:
            assert_allclose(np_output[:, :, offset, :], 0.)
            assert_allclose(np_output[:, :, :, offset], 0.)
        assert_allclose(np_output[:, 2:-2, 2:-2, :], 1.)

    layer = convolutional.ZeroPadding2D(padding=((1, 2), (3, 4)),
                                        data_format=data_format)
    layer.build(inputs.shape)
    outputs = layer(K.variable(inputs))
    np_output = K.eval(outputs)
    if data_format == 'channels_last':
        for top_offset in [0]:
            assert_allclose(np_output[:, top_offset, :, :], 0.)
        for bottom_offset in [-1, -2]:
            assert_allclose(np_output[:, bottom_offset, :, :], 0.)
        for left_offset in [0, 1, 2]:
            assert_allclose(np_output[:, :, left_offset, :], 0.)
        for right_offset in [-1, -2, -3, -4]:
            assert_allclose(np_output[:, :, right_offset, :], 0.)
        assert_allclose(np_output[:, 1:-2, 3:-4, :], 1.)
    elif data_format == 'channels_first':
        for top_offset in [0]:
            assert_allclose(np_output[:, :, top_offset, :], 0.)
        for bottom_offset in [-1, -2]:
            assert_allclose(np_output[:, :, bottom_offset, :], 0.)
        for left_offset in [0, 1, 2]:
            assert_allclose(np_output[:, :, :, left_offset], 0.)
        for right_offset in [-1, -2, -3, -4]:
            assert_allclose(np_output[:, :, :, right_offset], 0.)
        assert_allclose(np_output[:, :, 1:-2, 3:-4], 1.)


@pytest.mark.parametrize(
    'data_format,padding',
    [(data_format, padding)
     for data_format in ['channels_first', 'channels_last']
     for padding in [(2, 2, 2), ((1, 2), (3, 4), (0, 2))]]
)
def DISABLED_test_zero_padding_3d(data_format, padding):
    num_samples = 2
    stack_size = 2
    input_len_dim1 = 4
    input_len_dim2 = 5
    input_len_dim3 = 3
    inputs = np.ones((num_samples,
                     input_len_dim1, input_len_dim2, input_len_dim3,
                     stack_size))

    layer_test(convolutional.ZeroPadding3D,
               kwargs={'padding': padding, 'data_format': data_format},
               input_shape=inputs.shape)


@pytest.mark.parametrize('data_format',
                         ['channels_first', 'channels_last'])
def test_zero_padding_3d_correctness(data_format):
    num_samples = 2
    stack_size = 2
    input_len_dim1 = 4
    input_len_dim2 = 5
    input_len_dim3 = 3
    inputs = np.ones((num_samples,
                      input_len_dim1, input_len_dim2, input_len_dim3,
                      stack_size))

    layer = convolutional.ZeroPadding3D(padding=(2, 2, 2),
                                        data_format=data_format)
    layer.build(inputs.shape)
    outputs = layer(K.variable(inputs))
    np_output = K.eval(outputs)
    if data_format == 'channels_last':
        for offset in [0, 1, -1, -2]:
            assert_allclose(np_output[:, offset, :, :, :], 0.)
            assert_allclose(np_output[:, :, offset, :, :], 0.)
            assert_allclose(np_output[:, :, :, offset, :], 0.)
        assert_allclose(np_output[:, 2:-2, 2:-2, 2:-2, :], 1.)
    elif data_format == 'channels_first':
        for offset in [0, 1, -1, -2]:
            assert_allclose(np_output[:, :, offset, :, :], 0.)
            assert_allclose(np_output[:, :, :, offset, :], 0.)
            assert_allclose(np_output[:, :, :, :, offset], 0.)
        assert_allclose(np_output[:, :, 2:-2, 2:-2, 2:-2], 1.)

    layer = convolutional.ZeroPadding3D(padding=((1, 2), (3, 4), (0, 2)),
                                        data_format=data_format)
    layer.build(inputs.shape)
    outputs = layer(K.variable(inputs))
    np_output = K.eval(outputs)
    if data_format == 'channels_last':
        for dim1_offset in [0, -1, -2]:
            assert_allclose(np_output[:, dim1_offset, :, :, :], 0.)
        for dim2_offset in [0, 1, 2, -1, -2, -3, -4]:
            assert_allclose(np_output[:, :, dim2_offset, :, :], 0.)
        for dim3_offset in [-1, -2]:
            assert_allclose(np_output[:, :, :, dim3_offset, :], 0.)
        assert_allclose(np_output[:, 1:-2, 3:-4, 0:-2, :], 1.)
    elif data_format == 'channels_first':
        for dim1_offset in [0, -1, -2]:
            assert_allclose(np_output[:, :, dim1_offset, :, :], 0.)
        for dim2_offset in [0, 1, 2, -1, -2, -3, -4]:
            assert_allclose(np_output[:, :, :, dim2_offset, :], 0.)
        for dim3_offset in [-1, -2]:
            assert_allclose(np_output[:, :, :, :, dim3_offset], 0.)
        assert_allclose(np_output[:, :, 1:-2, 3:-4, 0:-2], 1.)


def test_upsampling_1d():
    layer_test(convolutional.UpSampling1D,
               kwargs={'size': 2},
               input_shape=(3, 5, 4))


@pytest.mark.parametrize('data_format',
                         ['channels_first', 'channels_last'])
def test_upsampling_2d(data_format):
    num_samples = 2
    stack_size = 2
    input_num_row = 11
    input_num_col = 12

    if data_format == 'channels_first':
        inputs = np.random.rand(num_samples, stack_size, input_num_row,
                                input_num_col)
    else:  # tf
        inputs = np.random.rand(num_samples, input_num_row, input_num_col,
                                stack_size)

    # basic test
    layer_test(convolutional.UpSampling2D,
               kwargs={'size': (2, 2), 'data_format': data_format},
               input_shape=inputs.shape)

    for length_row in [2]:
        for length_col in [2, 3]:
            layer = convolutional.UpSampling2D(
                size=(length_row, length_col),
                data_format=data_format)
            layer.build(inputs.shape)
            outputs = layer(K.variable(inputs))
            np_output = K.eval(outputs)
            if data_format == 'channels_first':
                assert np_output.shape[2] == length_row * input_num_row
                assert np_output.shape[3] == length_col * input_num_col
            else:  # tf
                assert np_output.shape[1] == length_row * input_num_row
                assert np_output.shape[2] == length_col * input_num_col

            # compare with numpy
            if data_format == 'channels_first':
                expected_out = np.repeat(inputs, length_row, axis=2)
                expected_out = np.repeat(expected_out, length_col, axis=3)
            else:  # tf
                expected_out = np.repeat(inputs, length_row, axis=1)
                expected_out = np.repeat(expected_out, length_col, axis=2)

            assert_allclose(np_output, expected_out)


@pytest.mark.parametrize('data_format',
                         ['channels_first', 'channels_last'])
def test_upsampling_2d_bilinear(data_format):
    num_samples = 2
    stack_size = 2
    input_num_row = 11
    input_num_col = 12

    if data_format == 'channels_first':
        inputs = np.random.rand(num_samples, stack_size, input_num_row,
                                input_num_col)
    else:  # tf
        inputs = np.random.rand(num_samples, input_num_row, input_num_col,
                                stack_size)

    # basic test
    layer_test(convolutional.UpSampling2D,
               kwargs={'size': (2, 2),
                       'data_format': data_format,
                       'interpolation': 'bilinear'},
               input_shape=inputs.shape)

    for length_row in [2]:
        for length_col in [2, 3]:
            layer = convolutional.UpSampling2D(
                size=(length_row, length_col),
                data_format=data_format)
            layer.build(inputs.shape)
            outputs = layer(K.variable(inputs))
            np_output = K.eval(outputs)
            if data_format == 'channels_first':
                assert np_output.shape[2] == length_row * input_num_row
                assert np_output.shape[3] == length_col * input_num_col
            else:  # tf
                assert np_output.shape[1] == length_row * input_num_row
                assert np_output.shape[2] == length_col * input_num_col


@pytest.mark.parametrize('data_format',
                         ['channels_first', 'channels_last'])
def test_upsampling_3d(data_format):
    num_samples = 2
    stack_size = 2
    input_len_dim1 = 10
    input_len_dim2 = 11
    input_len_dim3 = 12

    if data_format == 'channels_first':
        inputs = np.random.rand(num_samples,
                                stack_size,
                                input_len_dim1, input_len_dim2, input_len_dim3)
    else:  # tf
        inputs = np.random.rand(num_samples,
                                input_len_dim1, input_len_dim2, input_len_dim3,
                                stack_size)

    # basic test
    layer_test(convolutional.UpSampling3D,
               kwargs={'size': (2, 2, 2), 'data_format': data_format},
               input_shape=inputs.shape)

    for length_dim1 in [2, 3]:
        for length_dim2 in [2]:
            for length_dim3 in [3]:
                layer = convolutional.UpSampling3D(
                    size=(length_dim1, length_dim2, length_dim3),
                    data_format=data_format)
                layer.build(inputs.shape)
                outputs = layer(K.variable(inputs))
                np_output = K.eval(outputs)
                if data_format == 'channels_first':
                    assert np_output.shape[2] == length_dim1 * input_len_dim1
                    assert np_output.shape[3] == length_dim2 * input_len_dim2
                    assert np_output.shape[4] == length_dim3 * input_len_dim3
                else:  # tf
                    assert np_output.shape[1] == length_dim1 * input_len_dim1
                    assert np_output.shape[2] == length_dim2 * input_len_dim2
                    assert np_output.shape[3] == length_dim3 * input_len_dim3

                # compare with numpy
                if data_format == 'channels_first':
                    expected_out = np.repeat(inputs, length_dim1, axis=2)
                    expected_out = np.repeat(expected_out, length_dim2, axis=3)
                    expected_out = np.repeat(expected_out, length_dim3, axis=4)
                else:  # tf
                    expected_out = np.repeat(inputs, length_dim1, axis=1)
                    expected_out = np.repeat(expected_out, length_dim2, axis=2)
                    expected_out = np.repeat(expected_out, length_dim3, axis=3)

                assert_allclose(np_output, expected_out)


def test_cropping_1d():
    num_samples = 2
    time_length = 4
    input_len_dim1 = 2
    inputs = np.random.rand(num_samples, time_length, input_len_dim1)

    layer_test(convolutional.Cropping1D,
               kwargs={'cropping': (2, 2)},
               input_shape=inputs.shape)


def test_cropping_2d():
    num_samples = 2
    stack_size = 2
    input_len_dim1 = 9
    input_len_dim2 = 9
    cropping = ((2, 2), (3, 3))

    for data_format in ['channels_first', 'channels_last']:
        if data_format == 'channels_first':
            inputs = np.random.rand(num_samples, stack_size,
                                    input_len_dim1, input_len_dim2)
        else:
            inputs = np.random.rand(num_samples,
                                    input_len_dim1, input_len_dim2,
                                    stack_size)
        # basic test
        layer_test(convolutional.Cropping2D,
                   kwargs={'cropping': cropping,
                           'data_format': data_format},
                   input_shape=inputs.shape)
        # correctness test
        layer = convolutional.Cropping2D(cropping=cropping,
                                         data_format=data_format)
        layer.build(inputs.shape)
        outputs = layer(K.variable(inputs))
        np_output = K.eval(outputs)
        # compare with numpy
        if data_format == 'channels_first':
            expected_out = inputs[:,
                                  :,
                                  cropping[0][0]: -cropping[0][1],
                                  cropping[1][0]: -cropping[1][1]]
        else:
            expected_out = inputs[:,
                                  cropping[0][0]: -cropping[0][1],
                                  cropping[1][0]: -cropping[1][1],
                                  :]
        assert_allclose(np_output, expected_out)

    for data_format in ['channels_first', 'channels_last']:
        if data_format == 'channels_first':
            inputs = np.random.rand(num_samples, stack_size,
                                    input_len_dim1, input_len_dim2)
        else:
            inputs = np.random.rand(num_samples,
                                    input_len_dim1, input_len_dim2,
                                    stack_size)
        # another correctness test (no cropping)
        cropping = ((0, 0), (0, 0))
        layer = convolutional.Cropping2D(cropping=cropping,
                                         data_format=data_format)
        layer.build(inputs.shape)
        outputs = layer(K.variable(inputs))
        np_output = K.eval(outputs)
        # compare with input
        assert_allclose(np_output, inputs)

    # Test invalid use cases
    with pytest.raises(ValueError):
        layer = convolutional.Cropping2D(cropping=((1, 1),))
    with pytest.raises(ValueError):
        layer = convolutional.Cropping2D(cropping=lambda x: x)


def test_cropping_3d():
    num_samples = 2
    stack_size = 2
    input_len_dim1 = 8
    input_len_dim2 = 8
    input_len_dim3 = 8
    cropping = ((2, 2), (3, 3), (2, 3))

    for data_format in ['channels_last', 'channels_first']:
        if data_format == 'channels_first':
            inputs = np.random.rand(num_samples, stack_size,
                                    input_len_dim1, input_len_dim2, input_len_dim3)
        else:
            inputs = np.random.rand(num_samples,
                                    input_len_dim1, input_len_dim2,
                                    input_len_dim3, stack_size)
        # basic test
        layer_test(convolutional.Cropping3D,
                   kwargs={'cropping': cropping,
                           'data_format': data_format},
                   input_shape=inputs.shape)
        # correctness test
        layer = convolutional.Cropping3D(cropping=cropping,
                                         data_format=data_format)
        layer.build(inputs.shape)
        outputs = layer(K.variable(inputs))
        np_output = K.eval(outputs)
        # compare with numpy
        if data_format == 'channels_first':
            expected_out = inputs[:,
                                  :,
                                  cropping[0][0]: -cropping[0][1],
                                  cropping[1][0]: -cropping[1][1],
                                  cropping[2][0]: -cropping[2][1]]
        else:
            expected_out = inputs[:,
                                  cropping[0][0]: -cropping[0][1],
                                  cropping[1][0]: -cropping[1][1],
                                  cropping[2][0]: -cropping[2][1],
                                  :]
        assert_allclose(np_output, expected_out)

    for data_format in ['channels_last', 'channels_first']:
        if data_format == 'channels_first':
            inputs = np.random.rand(num_samples, stack_size,
                                    input_len_dim1, input_len_dim2, input_len_dim3)
        else:
            inputs = np.random.rand(num_samples,
                                    input_len_dim1, input_len_dim2,
                                    input_len_dim3, stack_size)
        # another correctness test (no cropping)
        cropping = ((0, 0), (0, 0), (0, 0))
        layer = convolutional.Cropping3D(cropping=cropping,
                                         data_format=data_format)
        layer.build(inputs.shape)
        outputs = layer(K.variable(inputs))
        np_output = K.eval(outputs)
        # compare with input
        assert_allclose(np_output, inputs)

    # Test invalid use cases
    with pytest.raises(ValueError):
        layer = convolutional.Cropping3D(cropping=((1, 1),))
    with pytest.raises(ValueError):
        layer = convolutional.Cropping3D(cropping=lambda x: x)


@pytest.mark.parametrize(
    'input_shape,conv_class',
    [((2, 4, 2), convolutional.Conv1D),
     ((2, 4, 4, 2), convolutional.Conv2D),
     ((2, 4, 4, 4, 2), convolutional.Conv3D)]
)
def test_conv_float64(input_shape, conv_class):
    kernel_size = 3
    strides = 1
    filters = 3
    K.set_floatx('float64')
    layer_test(conv_class,
               kwargs={'filters': filters,
                       'kernel_size': kernel_size,
                       'padding': 'valid',
                       'strides': strides},
               input_shape=input_shape)
    K.set_floatx('float32')


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
from keras.utils.test_utils import layer_test
from keras.layers import noise
from keras import backend as K


@pytest.mark.skipif((K.backend() == 'cntk'),
                    reason="cntk does not support it yet")
def test_GaussianNoise():
    layer_test(noise.GaussianNoise,
               kwargs={'stddev': 1.},
               input_shape=(3, 2, 3))


@pytest.mark.skipif((K.backend() == 'cntk'),
                    reason="cntk does not support it yet")
def test_GaussianDropout():
    layer_test(noise.GaussianDropout,
               kwargs={'rate': 0.5},
               input_shape=(3, 2, 3))


@pytest.mark.skipif((K.backend() == 'cntk'),
                    reason="cntk does not support it yet")
def test_AlphaDropout():
    layer_test(noise.AlphaDropout,
               kwargs={'rate': 0.1},
               input_shape=(3, 2, 3))


if __name__ == '__main__':
    pytest.main([__file__])

import os
import multiprocessing

import numpy as np
import pytest
from numpy.testing import assert_allclose
from csv import reader
from csv import Sniffer
import shutil
from collections import defaultdict
from keras import optimizers
from keras import initializers
from keras import callbacks
from keras.models import Sequential, Model
from keras.layers import Input, Dense, Dropout, add, dot, Lambda, Layer
from keras.layers import Conv2D
from keras.layers import MaxPooling2D
from keras.layers import GlobalAveragePooling1D
from keras.layers import GlobalAveragePooling2D
from keras.layers import BatchNormalization
from keras.utils.test_utils import get_test_data
from keras.utils.generic_utils import to_list
from keras.utils.generic_utils import unpack_singleton
from keras import backend as K
from keras.utils import np_utils

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


input_dim = 2
num_hidden = 4
num_classes = 2
batch_size = 5
train_samples = 20
test_samples = 20


def data_generator(x, y, batch_size):
    x = to_list(x)
    y = to_list(y)
    max_batch_index = len(x[0]) // batch_size
    i = 0
    while 1:
        x_batch = [array[i * batch_size: (i + 1) * batch_size] for array in x]
        x_batch = unpack_singleton(x_batch)

        y_batch = [array[i * batch_size: (i + 1) * batch_size] for array in y]
        y_batch = unpack_singleton(y_batch)
        yield x_batch, y_batch
        i += 1
        i = i % max_batch_index


# Changing the default arguments of get_test_data.
def get_data_callbacks(num_train=train_samples,
                       num_test=test_samples,
                       input_shape=(input_dim,),
                       classification=True,
                       num_classes=num_classes):
    return get_test_data(num_train=num_train,
                         num_test=num_test,
                         input_shape=input_shape,
                         classification=classification,
                         num_classes=num_classes)


class Counter(callbacks.Callback):
    """Counts the number of times each callback method was run.

    # Arguments
        method_counts: dict, contains the counts of time
            each callback method was run.
    """

    def __init__(self):
        self.method_counts = defaultdict(int)
        methods_to_count = [
            'on_batch_begin', 'on_batch_end', 'on_epoch_begin', 'on_epoch_end',
            'on_train_batch_begin', 'on_train_batch_end',
            'on_test_batch_begin', 'on_test_batch_end',
            'on_predict_batch_begin', 'on_predict_batch_end',
            'on_train_begin', 'on_train_end',
            'on_predict_begin', 'on_predict_end',
            'on_test_begin', 'on_test_end',
        ]
        for method_name in methods_to_count:
            setattr(self, method_name,
                    self.wrap_with_counts(
                        method_name, getattr(self, method_name)))

    def wrap_with_counts(self, method_name, method):

        def _call_and_count(*args, **kwargs):
            self.method_counts[method_name] += 1
            return method(*args, **kwargs)

        return _call_and_count


class TestCallbackCounts(object):

    def _check_counts(self, counter, expected_counts):
        """Checks that counts registered by `counter` are those expected."""
        for method_name, expected_count in expected_counts.items():
            count = counter.method_counts[method_name]
            assert count == expected_count, \
                'For method {}: expected {}, got: {}'.format(
                    method_name, expected_count, count)

    def _get_model(self):
        layers = [
            Dense(10, activation='relu', input_dim=input_dim),
            Dense(num_classes, activation='softmax')
        ]
        model = Sequential(layers=layers)
        model.compile(optimizer='adam', loss='binary_crossentropy')
        return model

    def test_callback_hooks_are_called_in_fit(self):
        np.random.seed(1337)
        (X_train, y_train), (X_test, y_test) = get_data_callbacks(num_train=10,
                                                                  num_test=4)
        y_train = np_utils.to_categorical(y_train)
        y_test = np_utils.to_categorical(y_test)

        model = self._get_model()
        counter = Counter()
        model.fit(X_train, y_train, validation_data=(X_test, y_test),
                  batch_size=2, epochs=5, callbacks=[counter])

        self._check_counts(
            counter, {
                'on_batch_begin': 25,
                'on_batch_end': 25,
                'on_epoch_begin': 5,
                'on_epoch_end': 5,
                'on_predict_batch_begin': 0,
                'on_predict_batch_end': 0,
                'on_predict_begin': 0,
                'on_predict_end': 0,
                'on_test_batch_begin': 10,
                'on_test_batch_end': 10,
                'on_test_begin': 5,
                'on_test_end': 5,
                'on_train_batch_begin': 25,
                'on_train_batch_end': 25,
                'on_train_begin': 1,
                'on_train_end': 1,
            })

    def test_callback_hooks_are_called_in_evaluate(self):
        np.random.seed(1337)
        (_, _), (X_test, y_test) = get_data_callbacks(num_test=10)

        y_test = np_utils.to_categorical(y_test)

        model = self._get_model()
        counter = Counter()
        model.evaluate(X_test, y_test, batch_size=2, callbacks=[counter])
        self._check_counts(
            counter, {
                'on_test_batch_begin': 5,
                'on_test_batch_end': 5,
                'on_test_begin': 1,
                'on_test_end': 1,
                'on_batch_begin': 0,
                'on_batch_end': 0,
                'on_epoch_begin': 0,
                'on_epoch_end': 0,
                'on_predict_batch_begin': 0,
                'on_predict_batch_end': 0,
                'on_predict_begin': 0,
                'on_predict_end': 0,
                'on_train_batch_begin': 0,
                'on_train_batch_end': 0,
                'on_train_begin': 0,
                'on_train_end': 0,
            })

    def test_callback_hooks_are_called_in_predict(self):
        np.random.seed(1337)
        (_, _), (X_test, _) = get_data_callbacks(num_test=10)

        model = self._get_model()
        counter = Counter()
        model.predict(X_test, batch_size=2, callbacks=[counter])
        self._check_counts(
            counter, {
                'on_predict_batch_begin': 5,
                'on_predict_batch_end': 5,
                'on_predict_begin': 1,
                'on_predict_end': 1,
                'on_batch_begin': 0,
                'on_batch_end': 0,
                'on_epoch_begin': 0,
                'on_epoch_end': 0,
                'on_test_batch_begin': 0,
                'on_test_batch_end': 0,
                'on_test_begin': 0,
                'on_test_end': 0,
                'on_train_batch_begin': 0,
                'on_train_batch_end': 0,
                'on_train_begin': 0,
                'on_train_end': 0,
            })

    def test_callback_hooks_are_called_in_fit_generator(self):
        np.random.seed(1337)
        (X_train, y_train), (X_test, y_test) = get_data_callbacks(num_train=10,
                                                                  num_test=4)
        y_train = np_utils.to_categorical(y_train)
        y_test = np_utils.to_categorical(y_test)
        train_generator = data_generator(X_train, y_train, batch_size=2)
        validation_generator = data_generator(X_test, y_test, batch_size=2)

        model = self._get_model()
        counter = Counter()
        model.fit_generator(train_generator,
                            steps_per_epoch=len(X_train) // 2,
                            epochs=5,
                            validation_data=validation_generator,
                            validation_steps=len(X_test) // 2,
                            callbacks=[counter])

        self._check_counts(
            counter, {
                'on_batch_begin': 25,
                'on_batch_end': 25,
                'on_epoch_begin': 5,
                'on_epoch_end': 5,
                'on_predict_batch_begin': 0,
                'on_predict_batch_end': 0,
                'on_predict_begin': 0,
                'on_predict_end': 0,
                'on_test_batch_begin': 10,
                'on_test_batch_end': 10,
                'on_test_begin': 5,
                'on_test_end': 5,
                'on_train_batch_begin': 25,
                'on_train_batch_end': 25,
                'on_train_begin': 1,
                'on_train_end': 1,
            })

    def test_callback_hooks_are_called_in_evaluate_generator(self):
        np.random.seed(1337)
        (_, _), (X_test, y_test) = get_data_callbacks(num_test=10)
        y_test = np_utils.to_categorical(y_test)

        model = self._get_model()
        counter = Counter()
        model.evaluate_generator(data_generator(X_test, y_test, batch_size=2),
                                 steps=len(X_test) // 2, callbacks=[counter])
        self._check_counts(
            counter, {
                'on_test_batch_begin': 5,
                'on_test_batch_end': 5,
                'on_test_begin': 1,
                'on_test_end': 1,
                'on_batch_begin': 0,
                'on_batch_end': 0,
                'on_epoch_begin': 0,
                'on_epoch_end': 0,
                'on_predict_batch_begin': 0,
                'on_predict_batch_end': 0,
                'on_predict_begin': 0,
                'on_predict_end': 0,
                'on_train_batch_begin': 0,
                'on_train_batch_end': 0,
                'on_train_begin': 0,
                'on_train_end': 0,
            })

    def test_callback_hooks_are_called_in_predict_generator(self):
        np.random.seed(1337)
        (_, _), (X_test, _) = get_data_callbacks(num_test=10)

        def data_generator(x, batch_size):
            x = to_list(x)
            max_batch_index = len(x[0]) // batch_size
            i = 0
            while 1:
                x_batch = [
                    array[i * batch_size: (i + 1) * batch_size] for array in x]
                x_batch = unpack_singleton(x_batch)

                yield x_batch
                i += 1
                i = i % max_batch_index

        model = self._get_model()
        counter = Counter()
        model.predict_generator(data_generator(X_test, batch_size=2),
                                steps=len(X_test) // 2, callbacks=[counter])
        self._check_counts(
            counter, {
                'on_predict_batch_begin': 5,
                'on_predict_batch_end': 5,
                'on_predict_begin': 1,
                'on_predict_end': 1,
                'on_batch_begin': 0,
                'on_batch_end': 0,
                'on_epoch_begin': 0,
                'on_epoch_end': 0,
                'on_test_batch_begin': 0,
                'on_test_batch_end': 0,
                'on_test_begin': 0,
                'on_test_end': 0,
                'on_train_batch_begin': 0,
                'on_train_batch_end': 0,
                'on_train_begin': 0,
                'on_train_end': 0,
            })

    def test_callback_list_methods(self):
        counter = Counter()
        callback_list = callbacks.CallbackList([counter])

        batch = 0
        callback_list.on_test_batch_begin(batch)
        callback_list.on_test_batch_end(batch)
        callback_list.on_predict_batch_begin(batch)
        callback_list.on_predict_batch_end(batch)

        self._check_counts(
            counter, {
                'on_test_batch_begin': 1,
                'on_test_batch_end': 1,
                'on_predict_batch_begin': 1,
                'on_predict_batch_end': 1,
                'on_predict_begin': 0,
                'on_predict_end': 0,
                'on_batch_begin': 0,
                'on_batch_end': 0,
                'on_epoch_begin': 0,
                'on_epoch_end': 0,
                'on_test_begin': 0,
                'on_test_end': 0,
                'on_train_batch_begin': 0,
                'on_train_batch_end': 0,
                'on_train_begin': 0,
                'on_train_end': 0,
            })


def test_TerminateOnNaN():
    np.random.seed(1337)
    (X_train, y_train), (X_test, y_test) = get_data_callbacks()

    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)
    cbks = [callbacks.TerminateOnNaN()]
    model = Sequential()
    initializer = initializers.Constant(value=1e5)
    for _ in range(5):
        model.add(Dense(num_hidden, input_dim=input_dim, activation='relu',
                        kernel_initializer=initializer))
    model.add(Dense(num_classes, activation='linear'))
    model.compile(loss='mean_squared_error',
                  optimizer='rmsprop')

    # case 1 fit
    history = model.fit(X_train, y_train,
                        batch_size=batch_size,
                        validation_data=(X_test, y_test),
                        callbacks=cbks,
                        epochs=20)
    loss = history.history['loss']
    assert len(loss) == 1
    assert np.isnan(loss[0])
    assert len(history.history) < 20

    history = model.fit_generator(data_generator(X_train, y_train, batch_size),
                                  len(X_train),
                                  validation_data=(X_test, y_test),
                                  callbacks=cbks,
                                  epochs=20)
    loss = history.history['loss']
    assert len(loss) == 1
    assert np.isnan(loss[0])
    assert len(history.history) < 20


def test_stop_training_csv(tmpdir):
    np.random.seed(1337)
    fp = str(tmpdir / 'test.csv')
    (X_train, y_train), (X_test, y_test) = get_data_callbacks()

    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)
    cbks = [callbacks.TerminateOnNaN(), callbacks.CSVLogger(fp)]
    model = Sequential()
    for _ in range(5):
        model.add(Dense(num_hidden, input_dim=input_dim, activation='relu'))
    model.add(Dense(num_classes, activation='linear'))
    model.compile(loss='mean_squared_error',
                  optimizer='rmsprop')

    def data_generator():
        i = 0
        max_batch_index = len(X_train) // batch_size
        tot = 0
        while 1:
            if tot > 3 * len(X_train):
                yield (np.ones([batch_size, input_dim]) * np.nan,
                       np.ones([batch_size, num_classes]) * np.nan)
            else:
                yield (X_train[i * batch_size: (i + 1) * batch_size],
                       y_train[i * batch_size: (i + 1) * batch_size])
            i += 1
            tot += 1
            i = i % max_batch_index

    history = model.fit_generator(data_generator(),
                                  len(X_train) // batch_size,
                                  validation_data=(X_test, y_test),
                                  callbacks=cbks,
                                  epochs=20)
    loss = history.history['loss']
    assert len(loss) > 1
    assert loss[-1] == np.inf or np.isnan(loss[-1])

    values = []
    with open(fp) as f:
        for x in reader(f):
            values.append(x)

    assert 'nan' in values[-1], 'The last epoch was not logged.'
    os.remove(fp)


def test_ModelCheckpoint(tmpdir):
    np.random.seed(1337)
    filepath = str(tmpdir / 'checkpoint.h5')
    (X_train, y_train), (X_test, y_test) = get_data_callbacks()
    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)
    # case 1
    monitor = 'val_loss'
    save_best_only = False
    mode = 'auto'

    model = Sequential()
    model.add(Dense(num_hidden, input_dim=input_dim, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))
    model.compile(loss='categorical_crossentropy',
                  optimizer='rmsprop',
                  metrics=['accuracy'])

    cbks = [callbacks.ModelCheckpoint(filepath, monitor=monitor,
                                      save_best_only=save_best_only, mode=mode)]
    model.fit(X_train, y_train, batch_size=batch_size,
              validation_data=(X_test, y_test), callbacks=cbks, epochs=1)
    assert os.path.isfile(filepath)
    os.remove(filepath)

    # case 2
    mode = 'min'
    cbks = [callbacks.ModelCheckpoint(filepath, monitor=monitor,
                                      save_best_only=save_best_only, mode=mode)]
    model.fit(X_train, y_train, batch_size=batch_size,
              validation_data=(X_test, y_test), callbacks=cbks, epochs=1)
    assert os.path.isfile(filepath)
    os.remove(filepath)

    # case 3
    mode = 'max'
    monitor = 'val_accuracy'
    cbks = [callbacks.ModelCheckpoint(filepath,
                                      monitor=monitor,
                                      save_best_only=save_best_only,
                                      mode=mode)]
    model.fit(X_train, y_train, batch_size=batch_size,
              validation_data=(X_test, y_test), callbacks=cbks, epochs=1)
    assert os.path.isfile(filepath)
    os.remove(filepath)

    # case 4
    save_best_only = True
    cbks = [callbacks.ModelCheckpoint(filepath,
                                      monitor=monitor,
                                      save_best_only=save_best_only,
                                      mode=mode)]
    model.fit(X_train, y_train, batch_size=batch_size,
              validation_data=(X_test, y_test), callbacks=cbks, epochs=1)
    assert os.path.isfile(filepath)
    os.remove(filepath)

    # case 5
    save_best_only = False
    period = 2
    mode = 'auto'
    filepath = 'checkpoint.{epoch:02d}.h5'
    cbks = [callbacks.ModelCheckpoint(filepath,
                                      monitor=monitor,
                                      save_best_only=save_best_only,
                                      mode=mode,
                                      period=period)]
    model.fit(X_train, y_train, batch_size=batch_size,
              validation_data=(X_test, y_test), callbacks=cbks, epochs=4)
    assert os.path.isfile(filepath.format(epoch=2))
    assert os.path.isfile(filepath.format(epoch=4))
    assert not os.path.exists(filepath.format(epoch=1))
    assert not os.path.exists(filepath.format(epoch=3))
    os.remove(filepath.format(epoch=2))
    os.remove(filepath.format(epoch=4))
    assert not tmpdir.listdir()


def test_EarlyStopping():
    np.random.seed(1337)
    (X_train, y_train), (X_test, y_test) = get_data_callbacks()
    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)
    model = Sequential()
    model.add(Dense(num_hidden, input_dim=input_dim, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))
    model.compile(loss='categorical_crossentropy',
                  optimizer='rmsprop',
                  metrics=['accuracy'])
    mode = 'max'
    monitor = 'val_acc'
    patience = 0
    cbks = [callbacks.EarlyStopping(patience=patience,
                                    monitor=monitor,
                                    mode=mode)]
    history = model.fit(X_train, y_train,
                        batch_size=batch_size,
                        validation_data=(X_test, y_test),
                        callbacks=cbks,
                        epochs=20)
    mode = 'auto'
    monitor = 'val_acc'
    patience = 2
    cbks = [callbacks.EarlyStopping(patience=patience,
                                    monitor=monitor,
                                    mode=mode)]
    history = model.fit(X_train, y_train,
                        batch_size=batch_size,
                        validation_data=(X_test, y_test),
                        callbacks=cbks,
                        epochs=20)


def test_EarlyStopping_reuse():
    np.random.seed(1337)
    patience = 3
    data = np.random.random((100, 1))
    labels = np.where(data > 0.5, 1, 0)
    model = Sequential((
        Dense(1, input_dim=1, activation='relu'),
        Dense(1, activation='sigmoid'),
    ))
    model.compile(optimizer='sgd',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])
    stopper = callbacks.EarlyStopping(monitor='acc', patience=patience)
    weights = model.get_weights()

    hist = model.fit(data, labels, callbacks=[stopper], epochs=20)
    assert len(hist.epoch) >= patience

    # This should allow training to go for at least `patience` epochs
    model.set_weights(weights)
    hist = model.fit(data, labels, callbacks=[stopper], epochs=20)
    assert len(hist.epoch) >= patience


def test_EarlyStopping_patience():
    class DummyModel(object):
        def __init__(self):
            self.stop_training = False

        def get_weights(self):
            return []

        def set_weights(self, weights):
            pass

    early_stop = callbacks.EarlyStopping(monitor='val_loss', patience=2)
    early_stop.model = DummyModel()

    losses = [0.0860, 0.1096, 0.1040, 0.1019]

    # Should stop after epoch 3,
    # as the loss has not improved after patience=2 epochs.
    epochs_trained = 0
    early_stop.on_train_begin()

    for epoch in range(len(losses)):
        epochs_trained += 1
        early_stop.on_epoch_end(epoch, logs={'val_loss': losses[epoch]})

        if early_stop.model.stop_training:
            break

    assert epochs_trained == 3


def test_EarlyStopping_baseline():
    class DummyModel(object):
        def __init__(self):
            self.stop_training = False

        def get_weights(self):
            return []

        def set_weights(self, weights):
            pass

    def baseline_tester(acc_levels):
        early_stop = callbacks.EarlyStopping(monitor='val_acc', baseline=0.75,
                                             patience=2)
        early_stop.model = DummyModel()
        epochs_trained = 0
        early_stop.on_train_begin()
        for epoch in range(len(acc_levels)):
            epochs_trained += 1
            early_stop.on_epoch_end(epoch, logs={'val_acc': acc_levels[epoch]})
            if early_stop.model.stop_training:
                break
        return epochs_trained

    acc_levels = [0.55, 0.76, 0.81, 0.81]
    baseline_met = baseline_tester(acc_levels)
    acc_levels = [0.55, 0.74, 0.81, 0.81]
    baseline_not_met = baseline_tester(acc_levels)

    # All epochs should run because baseline was met in second epoch
    assert baseline_met == 4
    # Baseline was not met by second epoch and should stop
    assert baseline_not_met == 2


def test_EarlyStopping_final_weights():
    class DummyModel(object):
        def __init__(self):
            self.stop_training = False
            self.weights = -1

        def get_weights(self):
            return self.weights

        def set_weights(self, weights):
            self.weights = weights

        def set_weight_to_epoch(self, epoch):
            self.weights = epoch

    early_stop = callbacks.EarlyStopping(monitor='val_loss', patience=2)
    early_stop.model = DummyModel()

    losses = [0.2, 0.15, 0.1, 0.11, 0.12]

    epochs_trained = 0
    early_stop.on_train_begin()

    for epoch in range(len(losses)):
        epochs_trained += 1
        early_stop.model.set_weight_to_epoch(epoch=epoch)
        early_stop.on_epoch_end(epoch, logs={'val_loss': losses[epoch]})

        if early_stop.model.stop_training:
            break

    # The best configuration is in the epoch 2 (loss = 0.1000),
    # so with patience=2 we need to end up at epoch 4
    assert early_stop.model.get_weights() == 4


def test_EarlyStopping_final_weights_when_restoring_model_weights():
    class DummyModel(object):
        def __init__(self):
            self.stop_training = False
            self.weights = -1

        def get_weights(self):
            return self.weights

        def set_weights(self, weights):
            self.weights = weights

        def set_weight_to_epoch(self, epoch):
            self.weights = epoch

    early_stop = callbacks.EarlyStopping(monitor='val_loss', patience=2,
                                         restore_best_weights=True)
    early_stop.model = DummyModel()

    losses = [0.2, 0.15, 0.1, 0.11, 0.12]

    # The best configuration is in the epoch 2 (loss = 0.1000).

    epochs_trained = 0
    early_stop.on_train_begin()

    for epoch in range(len(losses)):
        epochs_trained += 1
        early_stop.model.set_weight_to_epoch(epoch=epoch)
        early_stop.on_epoch_end(epoch, logs={'val_loss': losses[epoch]})

        if early_stop.model.stop_training:
            break

    # The best configuration is in epoch 2 (loss = 0.1000),
    # and while patience = 2, we're restoring the best weights,
    # so we end up at the epoch with the best weights, i.e. epoch 2
    assert early_stop.model.get_weights() == 2


def test_LearningRateScheduler():
    np.random.seed(1337)
    (X_train, y_train), (X_test, y_test) = get_data_callbacks()
    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)
    model = Sequential()
    model.add(Dense(num_hidden, input_dim=input_dim, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))
    model.compile(loss='categorical_crossentropy',
                  optimizer='sgd',
                  metrics=['accuracy'])

    cbks = [callbacks.LearningRateScheduler(lambda x: 1. / (1. + x))]
    model.fit(X_train, y_train, batch_size=batch_size,
              validation_data=(X_test, y_test), callbacks=cbks, epochs=5)
    assert (float(K.get_value(model.optimizer.lr)) - 0.2) < K.epsilon()


def test_ReduceLROnPlateau():
    np.random.seed(1337)
    (X_train, y_train), (X_test, y_test) = get_data_callbacks()
    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)

    def make_model():
        np.random.seed(1337)
        model = Sequential()
        model.add(Dense(num_hidden, input_dim=input_dim, activation='relu'))
        model.add(Dense(num_classes, activation='softmax'))

        model.compile(loss='categorical_crossentropy',
                      optimizer=optimizers.SGD(lr=0.1),
                      metrics=['accuracy'])
        return model

    model = make_model()

    # This should reduce the LR after the first epoch (due to high epsilon).
    cbks = [callbacks.ReduceLROnPlateau(monitor='val_loss',
                                        factor=0.1,
                                        min_delta=10,
                                        patience=1,
                                        cooldown=5)]
    model.fit(X_train, y_train,
              batch_size=batch_size,
              validation_data=(X_test, y_test),
              callbacks=cbks,
              epochs=5,
              verbose=2)
    assert_allclose(
        float(K.get_value(model.optimizer.lr)), 0.01, atol=K.epsilon())

    model = make_model()
    cbks = [callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.1,
                                        min_delta=0, patience=1, cooldown=5)]
    model.fit(X_train, y_train,
              batch_size=batch_size,
              validation_data=(X_test, y_test),
              callbacks=cbks,
              epochs=5,
              verbose=2)
    assert_allclose(
        float(K.get_value(model.optimizer.lr)), 0.1, atol=K.epsilon())


def test_ReduceLROnPlateau_patience():
    class DummyOptimizer(object):
        def __init__(self):
            self.lr = K.variable(1.0)

    class DummyModel(object):
        def __init__(self):
            self.optimizer = DummyOptimizer()

    reduce_on_plateau = callbacks.ReduceLROnPlateau(monitor='val_loss',
                                                    patience=2)
    reduce_on_plateau.model = DummyModel()

    losses = [0.0860, 0.1096, 0.1040]
    lrs = []

    for epoch in range(len(losses)):
        reduce_on_plateau.on_epoch_end(epoch, logs={'val_loss': losses[epoch]})
        lrs.append(K.get_value(reduce_on_plateau.model.optimizer.lr))

    # The learning rates should be 1.0 except the last one
    assert all([lr == 1.0 for lr in lrs[:-1]]) and lrs[-1] < 1.0


def DISABLED_test_ReduceLROnPlateau_backwards_compatibility():
    import warnings
    with warnings.catch_warnings(record=True) as ws:
        reduce_on_plateau = callbacks.ReduceLROnPlateau(epsilon=1e-13)
        # Check if warnings are disabled
        if os.environ.get("PYTHONWARNINGS") != "ignore":
            assert "`epsilon` argument is deprecated" in str(ws[0].message)
    assert not hasattr(reduce_on_plateau, 'epsilon')
    assert hasattr(reduce_on_plateau, 'min_delta')
    assert reduce_on_plateau.min_delta == 1e-13


def test_CSVLogger(tmpdir):
    np.random.seed(1337)
    filepath = str(tmpdir / 'log.tsv')
    sep = '\t'
    (X_train, y_train), (X_test, y_test) = get_data_callbacks()
    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)

    def make_model():
        np.random.seed(1337)
        model = Sequential()
        model.add(Dense(num_hidden, input_dim=input_dim, activation='relu'))
        model.add(Dense(num_classes, activation='softmax'))

        model.compile(loss='categorical_crossentropy',
                      optimizer=optimizers.SGD(lr=0.1),
                      metrics=['accuracy'])
        return model

    # case 1, create new file with defined separator
    model = make_model()
    cbks = [callbacks.CSVLogger(filepath, separator=sep)]
    model.fit(X_train, y_train, batch_size=batch_size,
              validation_data=(X_test, y_test), callbacks=cbks, epochs=1)

    assert os.path.isfile(filepath)
    with open(filepath) as csvfile:
        dialect = Sniffer().sniff(csvfile.read())
    assert dialect.delimiter == sep
    del model
    del cbks

    # case 2, append data to existing file, skip header
    model = make_model()
    cbks = [callbacks.CSVLogger(filepath, separator=sep, append=True)]
    model.fit(X_train, y_train, batch_size=batch_size,
              validation_data=(X_test, y_test), callbacks=cbks, epochs=1)

    # case 3, reuse of CSVLogger object
    model.fit(X_train, y_train, batch_size=batch_size,
              validation_data=(X_test, y_test), callbacks=cbks, epochs=2)

    import re
    with open(filepath) as csvfile:
        list_lines = csvfile.readlines()
        for line in list_lines:
            assert line.count(sep) == 4
        assert len(list_lines) == 5
        output = " ".join(list_lines)
        assert len(re.findall('epoch', output)) == 1

    os.remove(filepath)
    assert not tmpdir.listdir()


def DISABLED_test_CallbackValData():
    np.random.seed(1337)
    (X_train, y_train), (X_test, y_test) = get_data_callbacks()
    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)
    model = Sequential()
    model.add(Dense(num_hidden, input_dim=input_dim, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))
    model.compile(loss='categorical_crossentropy',
                  optimizer='sgd',
                  metrics=['accuracy'])

    cbk = callbacks.LambdaCallback(on_train_end=lambda x: 1)
    model.fit(X_train, y_train, batch_size=batch_size,
              validation_data=(X_test, y_test), callbacks=[cbk], epochs=1)

    cbk2 = callbacks.LambdaCallback(on_train_end=lambda x: 1)
    train_generator = data_generator(X_train, y_train, batch_size)
    model.fit_generator(train_generator, len(X_train), epochs=1,
                        validation_data=(X_test, y_test),
                        callbacks=[cbk2])

    # callback validation data should always have x, y, and sample weights
    assert len(cbk.validation_data) == len(cbk2.validation_data) == 3
    assert cbk.validation_data[0] is cbk2.validation_data[0]
    assert cbk.validation_data[1] is cbk2.validation_data[1]
    assert cbk.validation_data[2].shape == cbk2.validation_data[2].shape


def test_LambdaCallback():
    np.random.seed(1337)
    (X_train, y_train), (X_test, y_test) = get_data_callbacks()
    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)
    model = Sequential()
    model.add(Dense(num_hidden, input_dim=input_dim, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))
    model.compile(loss='categorical_crossentropy',
                  optimizer='sgd',
                  metrics=['accuracy'])

    # Start an arbitrary process that should run during model training and
    # be terminated after training has completed.
    def f():
        while True:
            pass

    p = multiprocessing.Process(target=f)
    p.start()
    cleanup_callback = callbacks.LambdaCallback(
        on_train_end=lambda logs: p.terminate())

    cbks = [cleanup_callback]
    model.fit(X_train, y_train, batch_size=batch_size,
              validation_data=(X_test, y_test), callbacks=cbks, epochs=5)
    p.join()
    assert not p.is_alive()


@pytest.mark.skipif(K.backend() != 'tensorflow', reason='Uses TensorBoard')
def test_TensorBoard_with_ReduceLROnPlateau(tmpdir):
    import shutil
    np.random.seed(np.random.randint(1, 1e7))
    filepath = str(tmpdir / 'logs')

    (X_train, y_train), (X_test, y_test) = get_data_callbacks()
    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)

    model = Sequential()
    model.add(Dense(num_hidden, input_dim=input_dim, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))
    model.compile(loss='binary_crossentropy',
                  optimizer='sgd',
                  metrics=['accuracy'])

    cbks = [
        callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=4,
            verbose=1),
        callbacks.TensorBoard(
            log_dir=filepath)]

    model.fit(X_train, y_train, batch_size=batch_size,
              validation_data=(X_test, y_test), callbacks=cbks, epochs=2)

    assert os.path.isdir(filepath)
    shutil.rmtree(filepath)
    assert not tmpdir.listdir()


def tests_RemoteMonitor():
    (X_train, y_train), (X_test, y_test) = get_data_callbacks()
    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)
    model = Sequential()
    model.add(Dense(num_hidden, input_dim=input_dim, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))
    model.compile(loss='categorical_crossentropy',
                  optimizer='rmsprop',
                  metrics=['accuracy'])
    cbks = [callbacks.RemoteMonitor()]

    with patch('requests.post'):
        model.fit(X_train, y_train, batch_size=batch_size,
                  validation_data=(X_test, y_test), callbacks=cbks, epochs=1)


def tests_RemoteMonitorWithJsonPayload():
    (X_train, y_train), (X_test, y_test) = get_data_callbacks()
    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)
    model = Sequential()
    model.add(Dense(num_hidden, input_dim=input_dim, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))
    model.compile(loss='categorical_crossentropy',
                  optimizer='rmsprop',
                  metrics=['accuracy'])
    cbks = [callbacks.RemoteMonitor(send_as_json=True)]

    with patch('requests.post'):
        model.fit(X_train, y_train, batch_size=batch_size,
                  validation_data=(X_test, y_test), callbacks=cbks, epochs=1)


if __name__ == '__main__':
    pytest.main([__file__])

import os
import numpy as np
import pytest
import shutil

from keras import callbacks
from keras.models import Sequential, Model
from keras import layers
from keras import backend as K
from keras.utils import np_utils
from keras.utils.test_utils import get_test_data
from keras.utils.generic_utils import to_list
from keras.utils.generic_utils import unpack_singleton


input_dim = 2
num_hidden = 4
num_classes = 2
batch_size = 5
train_samples = 20
test_samples = 20


if K.backend() != 'tensorflow':
    pytestmark = pytest.mark.skip


def data_generator(x, y, batch_size):
    x = to_list(x)
    y = to_list(y)
    max_batch_index = len(x[0]) // batch_size
    i = 0
    while 1:
        x_batch = [array[i * batch_size: (i + 1) * batch_size] for array in x]
        x_batch = unpack_singleton(x_batch)

        y_batch = [array[i * batch_size: (i + 1) * batch_size] for array in y]
        y_batch = unpack_singleton(y_batch)
        yield x_batch, y_batch
        i += 1
        i = i % max_batch_index


# Changing the default arguments of get_test_data.
def get_data_callbacks(num_train=train_samples,
                       num_test=test_samples,
                       input_shape=(input_dim,),
                       classification=True,
                       num_classes=num_classes):
    return get_test_data(num_train=num_train,
                         num_test=num_test,
                         input_shape=input_shape,
                         classification=classification,
                         num_classes=num_classes)


@pytest.mark.parametrize('update_freq', ['batch', 'epoch', 9])
def DISABLED_test_TensorBoard(tmpdir, update_freq):
    np.random.seed(np.random.randint(1, 1e7))
    filepath = str(tmpdir / 'logs')

    (X_train, y_train), (X_test, y_test) = get_data_callbacks()
    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)

    class DummyStatefulMetric(layers.Layer):

        def __init__(self, name='dummy_stateful_metric', **kwargs):
            super(DummyStatefulMetric, self).__init__(name=name, **kwargs)
            self.stateful = True
            self.state = K.variable(value=0, dtype='int32')

        def reset_states(self):
            pass

        def __call__(self, y_true, y_pred):
            return self.state

    inp = layers.Input((input_dim,))
    hidden = layers.Dense(num_hidden, activation='relu')(inp)
    hidden = layers.Dropout(0.1)(hidden)
    hidden = layers.BatchNormalization()(hidden)
    output = layers.Dense(num_classes, activation='softmax')(hidden)
    model = Model(inputs=inp, outputs=output)
    model.compile(loss='categorical_crossentropy',
                  optimizer='sgd',
                  metrics=['accuracy', DummyStatefulMetric()])

    # we must generate new callbacks for each test, as they aren't stateless
    def callbacks_factory(histogram_freq=0,
                          embeddings_freq=0,
                          write_images=False,
                          write_grads=False):
        if embeddings_freq:
            embeddings_layer_names = ['dense_1']
            embeddings_data = X_test
        else:
            embeddings_layer_names = None
            embeddings_data = None
        return [callbacks.TensorBoard(log_dir=filepath,
                                      histogram_freq=histogram_freq,
                                      write_images=write_images,
                                      write_grads=write_grads,
                                      embeddings_freq=embeddings_freq,
                                      embeddings_layer_names=embeddings_layer_names,
                                      embeddings_data=embeddings_data,
                                      update_freq=update_freq)]

    # fit without validation data
    model.fit(X_train, y_train, batch_size=batch_size,
              callbacks=callbacks_factory(),
              epochs=2)

    # fit with validation data and accuracy
    model.fit(X_train, y_train, batch_size=batch_size,
              validation_data=(X_test, y_test),
              callbacks=callbacks_factory(),
              epochs=2)

    # fit generator without validation data
    train_generator = data_generator(X_train, y_train, batch_size)
    model.fit_generator(train_generator, len(X_train), epochs=2,
                        callbacks=callbacks_factory())

    # fit generator with validation data and accuracy
    train_generator = data_generator(X_train, y_train, batch_size)
    model.fit_generator(train_generator, len(X_train), epochs=2,
                        validation_data=(X_test, y_test),
                        callbacks=callbacks_factory(histogram_freq=1))

    assert os.path.isdir(filepath)
    shutil.rmtree(filepath)
    assert not tmpdir.listdir()


def test_TensorBoard_multi_input_output(tmpdir):
    np.random.seed(np.random.randint(1, 1e7))
    filepath = str(tmpdir / 'logs')

    (X_train, y_train), (X_test, y_test) = get_data_callbacks(
        input_shape=(input_dim, input_dim))

    y_test = np_utils.to_categorical(y_test)
    y_train = np_utils.to_categorical(y_train)

    inp1 = layers.Input((input_dim, input_dim))
    inp2 = layers.Input((input_dim, input_dim))
    inp_3d = layers.add([inp1, inp2])
    inp_2d = layers.GlobalAveragePooling1D()(inp_3d)
    # test a layer with a list of output tensors
    inp_pair = layers.Lambda(lambda x: x)([inp_3d, inp_2d])
    hidden = layers.dot(inp_pair, axes=-1)
    hidden = layers.Dense(num_hidden, activation='relu')(hidden)
    hidden = layers.Dropout(0.1)(hidden)
    output1 = layers.Dense(num_classes, activation='softmax')(hidden)
    output2 = layers.Dense(num_classes, activation='softmax')(hidden)
    model = Model(inputs=[inp1, inp2], outputs=[output1, output2])
    model.compile(loss='categorical_crossentropy',
                  optimizer='sgd',
                  metrics=['accuracy'])

    # we must generate new callbacks for each test, as they aren't stateless
    def callbacks_factory(histogram_freq=0,
                          embeddings_freq=0,
                          write_images=False,
                          write_grads=False):
        if embeddings_freq:
            embeddings_layer_names = ['dense_1']
            embeddings_data = [X_test] * 2
        else:
            embeddings_layer_names = None
            embeddings_data = None
        return [callbacks.TensorBoard(log_dir=filepath,
                                      histogram_freq=histogram_freq,
                                      write_images=write_images,
                                      write_grads=write_grads,
                                      embeddings_freq=embeddings_freq,
                                      embeddings_layer_names=embeddings_layer_names,
                                      embeddings_data=embeddings_data)]

    # fit without validation data
    model.fit([X_train] * 2, [y_train] * 2, batch_size=batch_size,
              callbacks=callbacks_factory(),
              epochs=3)

    # fit with validation data and accuracy
    model.fit([X_train] * 2, [y_train] * 2, batch_size=batch_size,
              validation_data=([X_test] * 2, [y_test] * 2),
              callbacks=callbacks_factory(histogram_freq=1),
              epochs=2)

    train_generator = data_generator([X_train] * 2, [y_train] * 2, batch_size)

    # fit generator without validation data
    model.fit_generator(train_generator, len(X_train), epochs=2,
                        callbacks=callbacks_factory())

    # fit generator with validation data and accuracy
    model.fit_generator(train_generator, len(X_train), epochs=2,
                        validation_data=([X_test] * 2, [y_test] * 2),
                        callbacks=callbacks_factory())

    assert os.path.isdir(filepath)
    shutil.rmtree(filepath)
    assert not tmpdir.listdir()


def test_TensorBoard_convnet(tmpdir):
    np.random.seed(np.random.randint(1, 1e7))
    filepath = str(tmpdir / 'logs')

    input_shape = (16, 16, 3)
    (x_train, y_train), (x_test, y_test) = get_data_callbacks(
        num_train=500,
        num_test=200,
        input_shape=input_shape)
    y_train = np_utils.to_categorical(y_train)
    y_test = np_utils.to_categorical(y_test)

    model = Sequential([
        layers.Conv2D(filters=8, kernel_size=3,
                      activation='relu',
                      input_shape=input_shape),
        layers.MaxPooling2D(pool_size=2),
        layers.Conv2D(filters=4, kernel_size=(3, 3),
                      activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.GlobalAveragePooling2D(),
        layers.Dense(num_classes, activation='softmax')
    ])
    model.compile(loss='categorical_crossentropy',
                  optimizer='rmsprop',
                  metrics=['accuracy'])
    tsb = callbacks.TensorBoard(filepath, histogram_freq=1)
    cbks = [tsb]
    model.summary()
    history = model.fit(x_train, y_train, epochs=2, batch_size=16,
                        validation_data=(x_test, y_test),
                        callbacks=cbks,
                        verbose=0)
    assert os.path.isdir(filepath)
    shutil.rmtree(filepath)
    assert not tmpdir.listdir()


def test_TensorBoard_display_float_from_logs(tmpdir):
    filepath = str(tmpdir / 'logs')

    input_shape = (3,)
    (x_train, y_train), _ = get_data_callbacks(num_train=10,
                                               num_test=0,
                                               input_shape=input_shape)
    y_train = np_utils.to_categorical(y_train)

    model = Sequential([
        layers.Dense(num_classes, activation='softmax')
    ])
    model.compile(loss='categorical_crossentropy',
                  optimizer='rmsprop')

    class CustomCallback(callbacks.Callback):

        def on_epoch_end(self, epoch, logs=None):
            logs['test'] = 0.

    tsb = callbacks.TensorBoard(log_dir=filepath)
    cbks = [CustomCallback(), tsb]
    model.fit(x_train, y_train, epochs=2, batch_size=16,
              callbacks=cbks,
              verbose=0)
    assert os.path.isdir(filepath)
    shutil.rmtree(filepath)
    assert not tmpdir.listdir()

import tempfile

import numpy as np
import pytest

from keras.datasets import boston_housing
from keras.datasets import imdb
from keras.datasets import reuters


@pytest.fixture
def fake_downloaded_boston_path(monkeypatch):
    num_rows = 100
    num_cols = 10
    rng = np.random.RandomState(123)

    x = rng.randint(1, 100, size=(num_rows, num_cols))
    y = rng.normal(loc=100, scale=15, size=num_rows)

    with tempfile.NamedTemporaryFile('wb', delete=True) as f:
        np.savez(f, x=x, y=y)
        monkeypatch.setattr(boston_housing, 'get_file',
                            lambda *args, **kwargs: f.name)
        yield f.name


@pytest.fixture
def fake_downloaded_imdb_path(monkeypatch):
    train_rows = 100
    test_rows = 20
    seq_length = 10
    rng = np.random.RandomState(123)

    x_train = rng.randint(1, 100, size=(train_rows, seq_length))
    y_train = rng.binomial(n=1, p=0.5, size=train_rows)
    x_test = rng.randint(1, 100, size=(test_rows, seq_length))
    y_test = rng.binomial(n=1, p=0.5, size=test_rows)

    with tempfile.NamedTemporaryFile('wb', delete=True) as f:
        np.savez(f, x_train=x_train, y_train=y_train, x_test=x_test, y_test=y_test)
        monkeypatch.setattr(imdb, 'get_file', lambda *args, **kwargs: f.name)
        yield f.name


@pytest.fixture
def fake_downloaded_reuters_path(monkeypatch):
    num_rows = 100
    seq_length = 10
    rng = np.random.RandomState(123)

    x = rng.randint(1, 100, size=(num_rows, seq_length))
    y = rng.binomial(n=1, p=0.5, size=num_rows)

    with tempfile.NamedTemporaryFile('wb', delete=True) as f:
        np.savez(f, x=x, y=y)
        monkeypatch.setattr(reuters, 'get_file', lambda *args, **kwargs: f.name)
        yield f.name


def DISABLED_test_boston_load_does_not_affect_global_rng(fake_downloaded_boston_path):
    np.random.seed(1337)
    before = np.random.randint(0, 100, size=10)

    np.random.seed(1337)
    boston_housing.load_data(path=fake_downloaded_boston_path, seed=9876)
    after = np.random.randint(0, 100, size=10)

    assert np.array_equal(before, after)


def DISABLED_test_imdb_load_does_not_affect_global_rng(fake_downloaded_imdb_path):
    np.random.seed(1337)
    before = np.random.randint(0, 100, size=10)

    np.random.seed(1337)
    imdb.load_data(path=fake_downloaded_imdb_path, seed=9876)
    after = np.random.randint(0, 100, size=10)

    assert np.array_equal(before, after)


def DISABLED_test_reuters_load_does_not_affect_global_rng(fake_downloaded_reuters_path):
    np.random.seed(1337)
    before = np.random.randint(0, 100, size=10)

    np.random.seed(1337)
    reuters.load_data(path=fake_downloaded_reuters_path, seed=9876)
    after = np.random.randint(0, 100, size=10)

    assert np.array_equal(before, after)

import sys
import pytest
import numpy as np
import marshal
from keras.utils.generic_utils import custom_object_scope
from keras.utils.generic_utils import has_arg
from keras.utils.generic_utils import Progbar
from keras import activations
from keras import regularizers


def test_progbar():
    values_s = [None,
                [['key1', 1], ['key2', 1e-4]],
                [['key3', 1], ['key2', 1e-4]]]

    for target in (len(values_s) - 1, None):
        for verbose in (0, 1, 2):
            bar = Progbar(target, width=30, verbose=verbose, interval=0.05)
            for current, values in enumerate(values_s):
                bar.update(current, values=values)


def test_custom_objects_scope():

    def custom_fn():
        pass

    class CustomClass(object):
        pass

    with custom_object_scope({'CustomClass': CustomClass,
                              'custom_fn': custom_fn}):
        act = activations.get('custom_fn')
        assert act == custom_fn
        cl = regularizers.get('CustomClass')
        assert cl.__class__ == CustomClass


@pytest.mark.parametrize('fn, name, accept_all, expected', [
    ('f(x)', 'x', False, True),
    ('f(x)', 'y', False, False),
    ('f(x)', 'y', True, False),
    ('f(x, y)', 'y', False, True),
    ('f(x, y=1)', 'y', False, True),
    ('f(x, **kwargs)', 'x', False, True),
    ('f(x, **kwargs)', 'y', False, False),
    ('f(x, **kwargs)', 'y', True, True),
    ('f(x, y=1, **kwargs)', 'y', False, True),
    # Keyword-only arguments (Python 3 only)
    ('f(x, *args, y=1)', 'y', False, True),
    ('f(x, *args, y=1)', 'z', True, False),
    ('f(x, *, y=1)', 'x', False, True),
    ('f(x, *, y=1)', 'y', False, True),
    # lambda
    (lambda x: x, 'x', False, True),
    (lambda x: x, 'y', False, False),
    (lambda x: x, 'y', True, False),
])
def test_has_arg(fn, name, accept_all, expected):
    if isinstance(fn, str):
        context = dict()
        try:
            exec('def {}: pass'.format(fn), context)
        except SyntaxError:
            if sys.version_info >= (3,):
                raise
            pytest.skip('Function is not compatible with Python 2')
        # Sometimes exec adds builtins to the context
        context.pop('__builtins__', None)
        fn, = context.values()

    assert has_arg(fn, name, accept_all) is expected


@pytest.mark.xfail(sys.version_info < (3, 3),
                   reason='inspect API does not reveal positional-only arguments')
def test_has_arg_positional_only():
    assert has_arg(pow, 'x') is False


if __name__ == '__main__':
    pytest.main([__file__])

"""Tests for functions in np_utils.py.
"""
import numpy as np
import pytest
from keras.utils import to_categorical


def test_to_categorical():
    num_classes = 5
    shapes = [(1,), (3,), (4, 3), (5, 4, 3), (3, 1), (3, 2, 1)]
    expected_shapes = [(1, num_classes),
                       (3, num_classes),
                       (4, 3, num_classes),
                       (5, 4, 3, num_classes),
                       (3, num_classes),
                       (3, 2, num_classes)]
    labels = [np.random.randint(0, num_classes, shape) for shape in shapes]
    one_hots = [to_categorical(label, num_classes) for label in labels]
    for label, one_hot, expected_shape in zip(labels,
                                              one_hots,
                                              expected_shapes):
        # Check shape
        assert one_hot.shape == expected_shape
        # Make sure there are only 0s and 1s
        assert np.array_equal(one_hot, one_hot.astype(bool))
        # Make sure there is exactly one 1 in a row
        assert np.all(one_hot.sum(axis=-1) == 1)
        # Get original labels back from one hots
        assert np.all(np.argmax(one_hot, -1).reshape(label.shape) == label)


if __name__ == '__main__':
    pytest.main([__file__])

"""Tests for functions in data_utils.py.
"""
import os
import time
import sys
import tarfile
import threading
import signal
import shutil
import zipfile
from itertools import cycle
import multiprocessing as mp
import numpy as np
import pytest
import six
from six.moves.urllib.parse import urljoin
from six.moves.urllib.request import pathname2url
from six.moves import reload_module

from flaky import flaky

from keras.utils import GeneratorEnqueuer
from keras.utils import OrderedEnqueuer
from keras.utils import Sequence
from tensorflow.python.keras.utils.data_utils import _hash_file
from keras.utils.data_utils import get_file
from tensorflow.python.keras.utils.data_utils import validate_file
from keras import backend as K

pytestmark = pytest.mark.skipif(
    six.PY2 and 'TRAVIS_PYTHON_VERSION' in os.environ,
    reason='Temporarily disabled until the use_multiprocessing problem is solved')

skip_generators = pytest.mark.skipif(K.backend() in {'tensorflow', 'cntk'} and
                                     'TRAVIS_PYTHON_VERSION' in os.environ,
                                     reason='Generators do not work with `spawn`.')


def use_spawn(func):
    """Decorator which uses `spawn` when possible.
    This is useful on Travis to avoid memory issues.
    """

    @six.wraps(func)
    def wrapper(*args, **kwargs):
        if sys.version_info > (3, 4) and os.name != 'nt':
            mp.set_start_method('spawn', force=True)
            out = func(*args, **kwargs)
            mp.set_start_method('fork', force=True)
        else:
            out = func(*args, **kwargs)
        return out

    return wrapper


if sys.version_info < (3,):
    def next(x):
        return x.next()


@pytest.fixture
def in_tmpdir(tmpdir):
    """Runs a function in a temporary directory.

    Checks that the directory is empty afterwards.
    """
    with tmpdir.as_cwd():
        yield None
    assert not tmpdir.listdir()


def test_data_utils(in_tmpdir):
    """Tests get_file from a url, plus extraction and validation.
    """
    dirname = 'data_utils'

    with open('test.txt', 'w') as text_file:
        text_file.write('Float like a butterfly, sting like a bee.')

    with tarfile.open('test.tar.gz', 'w:gz') as tar_file:
        tar_file.add('test.txt')

    with zipfile.ZipFile('test.zip', 'w') as zip_file:
        zip_file.write('test.txt')

    origin = urljoin('file://', pathname2url(os.path.abspath('test.tar.gz')))

    path = get_file(dirname, origin, untar=True)
    filepath = path + '.tar.gz'
    data_keras_home = os.path.dirname(os.path.dirname(os.path.abspath(filepath)))
    os.remove(filepath)

    _keras_home = os.path.join(os.path.abspath('.'), '.keras')
    if not os.path.exists(_keras_home):
        os.makedirs(_keras_home)
    os.environ['KERAS_HOME'] = _keras_home
    path = get_file(dirname, origin, untar=True)
    filepath = path + '.tar.gz'
    data_keras_home = os.path.dirname(os.path.dirname(os.path.abspath(filepath)))
    os.environ.pop('KERAS_HOME')
    shutil.rmtree(_keras_home)

    path = get_file(dirname, origin, untar=True)
    filepath = path + '.tar.gz'
    hashval_sha256 = _hash_file(filepath)
    hashval_md5 = _hash_file(filepath, algorithm='md5')
    path = get_file(dirname, origin, md5_hash=hashval_md5, untar=True)
    path = get_file(filepath, origin, file_hash=hashval_sha256, extract=True)
    assert os.path.exists(filepath)
    assert validate_file(filepath, hashval_sha256)
    assert validate_file(filepath, hashval_md5)
    os.remove(filepath)
    os.remove('test.tar.gz')

    origin = urljoin('file://', pathname2url(os.path.abspath('test.zip')))

    hashval_sha256 = _hash_file('test.zip')
    hashval_md5 = _hash_file('test.zip', algorithm='md5')
    path = get_file(dirname, origin, md5_hash=hashval_md5, extract=True)
    path = get_file(dirname, origin, file_hash=hashval_sha256, extract=True)
    assert os.path.exists(path)
    assert validate_file(path, hashval_sha256)
    assert validate_file(path, hashval_md5)

    os.remove(path)
    os.remove(os.path.join(os.path.dirname(path), 'test.txt'))
    os.remove('test.txt')
    os.remove('test.zip')


"""Enqueuers Tests"""


class threadsafe_iter:
    """Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.
    """

    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        with self.lock:
            return next(self.it)


def threadsafe_generator(f):
    """A decorator that takes a generator function and makes it thread-safe.
    """

    def g(*a, **kw):
        return threadsafe_iter(f(*a, **kw))

    return g


class DummySequence(Sequence):
    def __init__(self, shape, value=1.0):
        self.shape = shape
        self.inner = value

    def __getitem__(self, item):
        time.sleep(0.05)
        return np.ones(self.shape, dtype=np.uint32) * item * self.inner

    def __len__(self):
        return 100

    def on_epoch_end(self):
        self.inner *= 5.0


class LengthChangingSequence(Sequence):
    def __init__(self, shape, size=100, value=1.0):
        self.shape = shape
        self.inner = value
        self.size = size

    def __getitem__(self, item):
        time.sleep(0.05)
        return np.ones(self.shape, dtype=np.uint32) * item * self.inner

    def __len__(self):
        return self.size

    def on_epoch_end(self):
        self.size = int(np.ceil(self.size / 2))
        self.inner *= 5.0


class FaultSequence(Sequence):
    def __getitem__(self, item):
        raise IndexError(item, 'is not present')

    def __len__(self):
        return 100

    def on_epoch_end(self):
        pass


class SlowSequence(Sequence):
    def __init__(self, shape, value=1.0):
        self.shape = shape
        self.inner = value
        self.wait = True

    def __getitem__(self, item):
        if self.wait:
            self.wait = False
            time.sleep(40)
        return np.ones(self.shape, dtype=np.uint32) * item * self.inner

    def __len__(self):
        return 10

    def on_epoch_end(self):
        pass


@threadsafe_generator
def create_generator_from_sequence_threads(ds):
    for i in cycle(range(len(ds))):
        yield ds[i]


def create_generator_from_sequence_pcs(ds):
    for i in cycle(range(len(ds))):
        yield ds[i]


def test_generator_enqueuer_threads():
    enqueuer = GeneratorEnqueuer(create_generator_from_sequence_threads(
        DummySequence([3, 10, 10, 3])), use_multiprocessing=False)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    acc = []
    for i in range(100):
        acc.append(int(next(gen_output)[0, 0, 0, 0]))

    """
     Not comparing the order since it is not guaranteed.
     It may get ordered, but not a lot, one thread can take
     the GIL before he was supposed to.
    """
    assert len(set(acc) - set(range(100))) == 0, "Output is not the same"
    enqueuer.stop()


@skip_generators
def DISABLED_test_generator_enqueuer_processes():
    enqueuer = GeneratorEnqueuer(create_generator_from_sequence_pcs(
        DummySequence([3, 10, 10, 3])), use_multiprocessing=True)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    acc = []
    for i in range(100):
        acc.append(int(next(gen_output)[0, 0, 0, 0]))
    assert acc != list(range(100)), ('Order was keep in GeneratorEnqueuer '
                                     'with processes')
    enqueuer.stop()


def test_generator_enqueuer_threadsafe():
    enqueuer = GeneratorEnqueuer(create_generator_from_sequence_pcs(
        DummySequence([3, 10, 10, 3])), use_multiprocessing=False)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    with pytest.raises(RuntimeError) as e:
        [next(gen_output) for _ in range(10)]
    assert 'thread-safe' in str(e.value)
    enqueuer.stop()


# TODO: resolve flakyness issue. Tracked with #11587
@flaky(rerun_filter=lambda err, *args: issubclass(err[0], StopIteration))
def test_generator_enqueuer_fail_threads():
    enqueuer = GeneratorEnqueuer(create_generator_from_sequence_threads(
        FaultSequence()), use_multiprocessing=False)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    with pytest.raises(IndexError):
        next(gen_output)


@skip_generators
def DISABLED_test_generator_enqueuer_fail_processes():
    enqueuer = GeneratorEnqueuer(create_generator_from_sequence_pcs(
        FaultSequence()), use_multiprocessing=True)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    with pytest.raises(IndexError):
        next(gen_output)


def test_ordered_enqueuer_threads():
    enqueuer = OrderedEnqueuer(DummySequence([3, 10, 10, 3]),
                               use_multiprocessing=False)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    acc = []
    for i in range(100):
        acc.append(next(gen_output)[0, 0, 0, 0])
    assert acc == list(range(100)), ('Order was not keep in GeneratorEnqueuer '
                                     'with threads')
    enqueuer.stop()


def test_ordered_enqueuer_threads_not_ordered():
    enqueuer = OrderedEnqueuer(DummySequence([3, 10, 10, 3]),
                               use_multiprocessing=False,
                               shuffle=True)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    acc = []
    for i in range(100):
        acc.append(next(gen_output)[0, 0, 0, 0])
    assert acc != list(range(100)), ('Order was not keep in GeneratorEnqueuer '
                                     'with threads')
    enqueuer.stop()


@use_spawn
def test_ordered_enqueuer_processes():
    enqueuer = OrderedEnqueuer(DummySequence([3, 10, 10, 3]),
                               use_multiprocessing=True)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    acc = []
    for i in range(100):
        acc.append(next(gen_output)[0, 0, 0, 0])
    assert acc == list(range(100)), ('Order was not keep in GeneratorEnqueuer '
                                     'with processes')
    enqueuer.stop()


def test_ordered_enqueuer_fail_threads():
    enqueuer = OrderedEnqueuer(FaultSequence(), use_multiprocessing=False)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    with pytest.raises(IndexError):
        next(gen_output)


def DISABLED_test_ordered_enqueuer_timeout_threads():
    enqueuer = OrderedEnqueuer(SlowSequence([3, 10, 10, 3]),
                               use_multiprocessing=False)

    def handler(signum, frame):
        raise TimeoutError('Sequence deadlocked')

    old = signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, 60)
    with pytest.warns(UserWarning) as record:
        enqueuer.start(5, 10)
        gen_output = enqueuer.get()
        for epoch_num in range(2):
            acc = []
            for i in range(10):
                acc.append(next(gen_output)[0, 0, 0, 0])
            assert acc == list(range(10)), 'Order was not keep in ' \
                                           'OrderedEnqueuer with threads'
        enqueuer.stop()
    assert len(record) == 1
    assert str(record[0].message) == 'The input 0 could not be retrieved. ' \
                                     'It could be because a worker has died.'
    signal.setitimer(signal.ITIMER_REAL, 0)
    signal.signal(signal.SIGALRM, old)


@use_spawn
def test_on_epoch_end_processes():
    enqueuer = OrderedEnqueuer(DummySequence([3, 10, 10, 3]),
                               use_multiprocessing=True)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    acc = []
    for i in range(200):
        acc.append(next(gen_output)[0, 0, 0, 0])
    assert acc[100:] == list([k * 5 for k in range(100)]), (
        'Order was not keep in GeneratorEnqueuer with processes')
    enqueuer.stop()


@use_spawn
def test_context_switch():
    enqueuer = OrderedEnqueuer(DummySequence([3, 10, 10, 3]),
                               use_multiprocessing=True)
    enqueuer2 = OrderedEnqueuer(DummySequence([3, 10, 10, 3], value=15),
                                use_multiprocessing=True)
    enqueuer.start(3, 10)
    enqueuer2.start(3, 10)
    gen_output = enqueuer.get()
    gen_output2 = enqueuer2.get()
    acc = []
    for i in range(100):
        acc.append(next(gen_output)[0, 0, 0, 0])
    assert acc[-1] == 99
    # One epoch is completed so enqueuer will switch the Sequence

    acc = []
    for i in range(100):
        acc.append(next(gen_output2)[0, 0, 0, 0])
    assert acc[-1] == 99 * 15
    # One epoch has been completed so enqueuer2 will switch

    # Be sure that both Sequence were updated
    assert next(gen_output)[0, 0, 0, 0] == 0
    assert next(gen_output)[0, 0, 0, 0] == 5
    assert next(gen_output2)[0, 0, 0, 0] == 0
    assert next(gen_output2)[0, 0, 0, 0] == 15 * 5

    # Tear down everything
    enqueuer.stop()
    enqueuer2.stop()


def DISABLED_test_on_epoch_end_threads():
    enqueuer = OrderedEnqueuer(DummySequence([3, 10, 10, 3]),
                               use_multiprocessing=False)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    acc = []
    for i in range(100):
        acc.append(next(gen_output)[0, 0, 0, 0])
    acc = []
    for i in range(100):
        acc.append(next(gen_output)[0, 0, 0, 0])
    assert acc == list([k * 5 for k in range(100)]), (
        'Order was not keep in GeneratorEnqueuer with processes')
    enqueuer.stop()


def DISABLED_test_on_epoch_end_threads_sequence_change_length():
    seq = LengthChangingSequence([3, 10, 10, 3])
    enqueuer = OrderedEnqueuer(seq,
                               use_multiprocessing=False)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    acc = []
    for i in range(100):
        acc.append(next(gen_output)[0, 0, 0, 0])
    assert acc == list(range(100)), ('Order was not keep in GeneratorEnqueuer '
                                     'with threads')

    enqueuer.join_end_of_epoch()
    assert len(seq) == 50
    acc = []
    for i in range(50):
        acc.append(next(gen_output)[0, 0, 0, 0])
    assert acc == list([k * 5 for k in range(50)]), (
        'Order was not keep in GeneratorEnqueuer with processes')
    enqueuer.stop()


@use_spawn
def test_ordered_enqueuer_fail_processes():
    enqueuer = OrderedEnqueuer(FaultSequence(), use_multiprocessing=True)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    with pytest.raises(IndexError):
        next(gen_output)


@threadsafe_generator
def create_finite_generator_from_sequence_threads(ds):
    for i in range(len(ds)):
        yield ds[i]


def create_finite_generator_from_sequence_pcs(ds):
    for i in range(len(ds)):
        yield ds[i]


# TODO: resolve flakyness issue. Tracked with #11586
@flaky(rerun_filter=lambda err, *args: issubclass(err[0], AssertionError))
def test_finite_generator_enqueuer_threads():
    enqueuer = GeneratorEnqueuer(create_finite_generator_from_sequence_threads(
        DummySequence([3, 10, 10, 3])), use_multiprocessing=False)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    acc = []
    for output in gen_output:
        acc.append(int(output[0, 0, 0, 0]))
    assert set(acc) == set(range(100)), "Output is not the same"
    enqueuer.stop()


@skip_generators
def DISABLED_test_finite_generator_enqueuer_processes():
    enqueuer = GeneratorEnqueuer(create_finite_generator_from_sequence_pcs(
        DummySequence([3, 10, 10, 3])), use_multiprocessing=True)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    acc = []
    for output in gen_output:
        acc.append(int(output[0, 0, 0, 0]))
    assert acc != list(range(100)), ('Order was keep in GeneratorEnqueuer '
                                     'with processes')
    enqueuer.stop()


@pytest.mark.skipif('TRAVIS_PYTHON_VERSION' in os.environ,
                    reason='Takes 150s to run')
def DISABLED_test_missing_inputs():
    missing_idx = 10

    class TimeOutSequence(DummySequence):
        def __getitem__(self, item):
            if item == missing_idx:
                time.sleep(120)
            return super(TimeOutSequence, self).__getitem__(item)

    enqueuer = GeneratorEnqueuer(create_finite_generator_from_sequence_pcs(
        TimeOutSequence([3, 2, 2, 3])), use_multiprocessing=True)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    with pytest.warns(UserWarning, match='An input could not be retrieved.'):
        for _ in range(4 * missing_idx):
            next(gen_output)

    enqueuer = OrderedEnqueuer(TimeOutSequence([3, 2, 2, 3]),
                               use_multiprocessing=True)
    enqueuer.start(3, 10)
    gen_output = enqueuer.get()
    warning_msg = "The input {} could not be retrieved.".format(missing_idx)
    with pytest.warns(UserWarning, match=warning_msg):
        for _ in range(11):
            next(gen_output)


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import numpy as np
from numpy.testing import assert_allclose
from keras import backend as K
from keras.layers import Conv2D
from keras.layers import Dense
from keras.layers import Flatten
from keras.models import Sequential
from keras.utils import layer_utils


def DISABLED_test_convert_weights():
    def get_model(shape, data_format):
        model = Sequential()
        model.add(Conv2D(filters=2,
                         kernel_size=(4, 3),
                         input_shape=shape,
                         data_format=data_format))
        model.add(Flatten())
        model.add(Dense(5))
        return model

    for data_format in ['channels_first', 'channels_last']:
        if data_format == 'channels_first':
            shape = (3, 5, 5)
            target_shape = (5, 5, 3)
            prev_shape = (2, 3, 2)
            flip = lambda x: np.flip(np.flip(x, axis=2), axis=3)
            transpose = lambda x: np.transpose(x, (0, 2, 3, 1))
            target_data_format = 'channels_last'
        elif data_format == 'channels_last':
            shape = (5, 5, 3)
            target_shape = (3, 5, 5)
            prev_shape = (2, 2, 3)
            flip = lambda x: np.flip(np.flip(x, axis=1), axis=2)
            transpose = lambda x: np.transpose(x, (0, 3, 1, 2))
            target_data_format = 'channels_first'

        model1 = get_model(shape, data_format)
        model2 = get_model(target_shape, target_data_format)
        conv = K.function([model1.input], [model1.layers[0].output])

        x = np.random.random((1,) + shape)

        # Test equivalence of convert_all_kernels_in_model
        convout1 = conv([x])[0]
        layer_utils.convert_all_kernels_in_model(model1)
        convout2 = flip(conv([flip(x)])[0])

        assert_allclose(convout1, convout2, atol=1e-5)

        # Test equivalence of convert_dense_weights_data_format
        out1 = model1.predict(x)
        layer_utils.convert_dense_weights_data_format(
            model1.layers[2], prev_shape, target_data_format)
        for (src, dst) in zip(model1.layers, model2.layers):
            dst.set_weights(src.get_weights())
        out2 = model2.predict(transpose(x))

        assert_allclose(out1, out2, atol=1e-5)


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import os
import sys
import numpy as np
from keras import Input, Model

from keras.layers import Conv2D, Bidirectional
from keras.layers import Dense
from keras.layers import Embedding
from keras.layers import Flatten
from keras.layers import LSTM
from keras.layers import TimeDistributed
from keras.models import Sequential
from keras.utils import vis_utils


def test_plot_model():
    model = Sequential()
    model.add(Conv2D(2, kernel_size=(2, 3), input_shape=(3, 5, 5), name='conv'))
    model.add(Flatten(name='flat'))
    model.add(Dense(5, name='dense1'))
    vis_utils.plot_model(model, to_file='model1.png', show_layer_names=False)
    os.remove('model1.png')

    model = Sequential()
    model.add(LSTM(16, return_sequences=True, input_shape=(2, 3), name='lstm'))
    model.add(TimeDistributed(Dense(5, name='dense2')))
    vis_utils.plot_model(model, to_file='model2.png', show_shapes=True)
    os.remove('model2.png')

    inner_input = Input(shape=(2, 3), dtype='float32', name='inner_input')
    inner_lstm = Bidirectional(LSTM(16, name='inner_lstm'), name='bd')(inner_input)
    encoder = Model(inner_input, inner_lstm, name='Encoder_Model')
    outer_input = Input(shape=(5, 2, 3), dtype='float32', name='input')
    inner_encoder = TimeDistributed(encoder, name='td_encoder')(outer_input)
    lstm = LSTM(16, name='outer_lstm')(inner_encoder)
    preds = Dense(5, activation='softmax', name='predictions')(lstm)
    model = Model(outer_input, preds)
    vis_utils.plot_model(model, to_file='model3.png', show_shapes=True,
                         expand_nested=True, dpi=300)
    os.remove('model3.png')


def test_plot_sequential_embedding():
    """Fixes #11376"""
    model = Sequential()
    model.add(Embedding(10000, 256, input_length=400, name='embed'))
    vis_utils.plot_model(model,
                         to_file='model1.png',
                         show_shapes=True,
                         show_layer_names=True)
    os.remove('model1.png')


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import numpy as np
from keras.utils import conv_utils
from keras import backend as K


def test_normalize_tuple():
    assert conv_utils.normalize_tuple(5, 2, 'kernel_size') == (5, 5)
    assert conv_utils.normalize_tuple([7, 9], 2, 'kernel_size') == (7, 9)

    with pytest.raises(ValueError):
        conv_utils.normalize_tuple(None, 2, 'kernel_size')
    with pytest.raises(ValueError):
        conv_utils.normalize_tuple([2, 3, 4], 2, 'kernel_size')
    with pytest.raises(ValueError):
        conv_utils.normalize_tuple(['str', 'impossible'], 2, 'kernel_size')


def test_invalid_padding():
    with pytest.raises(ValueError):
        conv_utils.normalize_padding('diagonal')


def test_invalid_convert_kernel():
    with pytest.raises(ValueError):
        conv_utils.convert_kernel(np.zeros((10, 20)))


def test_conv_output_length():
    assert conv_utils.conv_output_length(None, 7, 'same', 1) is None
    assert conv_utils.conv_output_length(224, 7, 'same', 1) == 224
    assert conv_utils.conv_output_length(224, 7, 'same', 2) == 112
    assert conv_utils.conv_output_length(32, 5, 'valid', 1) == 28
    assert conv_utils.conv_output_length(32, 5, 'valid', 2) == 14
    assert conv_utils.conv_output_length(32, 5, 'causal', 1) == 32
    assert conv_utils.conv_output_length(32, 5, 'causal', 2) == 16
    assert conv_utils.conv_output_length(32, 5, 'full', 1) == 36
    assert conv_utils.conv_output_length(32, 5, 'full', 2) == 18

    with pytest.raises(AssertionError):
        conv_utils.conv_output_length(32, 5, 'diagonal', 2)


def test_conv_input_length():
    assert conv_utils.conv_input_length(None, 7, 'same', 1) is None
    assert conv_utils.conv_input_length(112, 7, 'same', 1) == 112
    assert conv_utils.conv_input_length(112, 7, 'same', 2) == 223
    assert conv_utils.conv_input_length(28, 5, 'valid', 1) == 32
    assert conv_utils.conv_input_length(14, 5, 'valid', 2) == 31
    assert conv_utils.conv_input_length(36, 5, 'full', 1) == 32
    assert conv_utils.conv_input_length(18, 5, 'full', 2) == 31

    with pytest.raises(AssertionError):
        conv_utils.conv_output_length(18, 5, 'diagonal', 2)


def test_deconv_length():
    assert conv_utils.deconv_length(None, 1, 7, 'same', None) is None
    assert conv_utils.deconv_length(224, 1, 7, 'same', None) == 224
    assert conv_utils.deconv_length(224, 2, 7, 'same', None) == 448
    assert conv_utils.deconv_length(32, 1, 5, 'valid', None) == 36
    assert conv_utils.deconv_length(32, 2, 5, 'valid', None) == 67
    assert conv_utils.deconv_length(32, 1, 5, 'full', None) == 28
    assert conv_utils.deconv_length(32, 2, 5, 'full', None) == 59
    assert conv_utils.deconv_length(224, 1, 7, 'same', 0) == 224
    assert conv_utils.deconv_length(224, 2, 7, 'same', 0) == 447
    assert conv_utils.deconv_length(224, 2, 7, 'same', 1) == 448
    assert conv_utils.deconv_length(32, 1, 5, 'valid', 0) == 36
    assert conv_utils.deconv_length(32, 2, 5, 'valid', 0) == 67
    assert conv_utils.deconv_length(32, 2, 5, 'valid', 1) == 68
    assert conv_utils.deconv_length(6, 1, 3, 'full', 0) == 4
    assert conv_utils.deconv_length(6, 2, 3, 'full', 1) == 10
    assert conv_utils.deconv_length(6, 2, 3, 'full', 2) == 11


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import keras
import numpy as np
from keras import layers
from keras import backend as K


def test_sublayer_tracking():
    # basic case
    class MyLayer(layers.Layer):

        def __init__(self):
            super(MyLayer, self).__init__()
            self._input_shape = (2, 4)
            self.dense = layers.Dense(3)
            self.bidir = layers.Bidirectional(keras.layers.LSTM(2))

        def call(self, inputs):
            return self.dense(self.bidir(inputs))

    layer = MyLayer()
    assert len(layer._layers) == 2
    layer(K.constant(np.random.random((2,) + layer._input_shape)))
    assert len(layer.weights) == 2 + 3 + 3
    assert len(layer._layers[0].weights) == 2
    assert len(layer._layers[1].weights) == 6

    # recursive case
    class MyRecursiveLayer(layers.Layer):

        def __init__(self):
            super(MyRecursiveLayer, self).__init__()
            self._input_shape = (2, 4)
            self.my_layer = MyLayer()
            self.dense = layers.Dense(3)
            self.bidir = layers.Bidirectional(
                keras.layers.LSTM(2, return_sequences=True))

        def call(self, inputs):
            return self.my_layer(self.dense(self.bidir(inputs)))

    layer = MyRecursiveLayer()
    assert len(layer._layers) == 3
    layer(K.constant(np.random.random((2,) + layer._input_shape)))
    assert len(layer.weights) == 16

    # subnetwork case
    class MyLayerWithSubnetwork(keras.layers.Layer):

        def __init__(self):
            super(MyLayerWithSubnetwork, self).__init__()
            self._input_shape = (2,)
            self.dense = layers.Dense(3)
            self.sequential = keras.Sequential(
                [layers.Dense(5), layers.Dense(1)], name='seq')
            inputs = keras.Input((1,))
            outputs = layers.Dense(1)(inputs)
            self.functional = keras.Model(inputs, outputs, name='func')

        def call(self, inputs):
            x = self.dense(inputs)
            x = self.sequential(x)
            return self.functional(x)

    layer = MyLayerWithSubnetwork()
    assert len(layer._layers) == 3
    layer(K.constant(np.random.random((2,) + layer._input_shape)))
    assert len(layer.weights) == 2 + (2 + 2) + 2
    assert len(layer._layers[0].weights) == 2
    assert len(layer._layers[1].weights) == 4
    assert len(layer._layers[2].weights) == 2


def test_weight_tracking():

    class MyLayer(layers.Layer):

        def __init__(self):
            super(MyLayer, self).__init__()
            self._input_shape = (2,)
            self.dense = layers.Dense(3)
            self.w1 = K.variable(0, name='w1')

        def build(self, input_shape):
            self.w2 = K.variable(1, name='w2')
            self.w3 = self.add_weight(
                'w3', shape=(), trainable=False, initializer='zeros')

        def call(self, inputs):
            return self.dense(inputs) + self.w1 + self.w2

    layer = MyLayer()
    layer(K.constant(np.random.random((2,) + layer._input_shape)))
    assert len(layer.weights) == 5
    assert len(layer.trainable_weights) == 4
    assert len(layer.non_trainable_weights) == 1
    assert len(layer._trainable_weights) == 2
    assert layer._trainable_weights[0] is layer.w1
    assert layer._trainable_weights[1] is layer.w2
    assert len(layer._non_trainable_weights) == 1
    assert layer._non_trainable_weights[0] is layer.w3


def test_loss_tracking():
    # basic case
    class MyLayer(layers.Layer):

        def __init__(self):
            super(MyLayer, self).__init__()
            self.dense = layers.Dense(
                3, kernel_regularizer='l2', activity_regularizer='l2')

        def call(self, inputs):
            return self.dense(inputs)

    inputs = keras.Input((2,))
    outputs = MyLayer()(inputs)
    model = keras.Model(inputs, outputs)

    assert len(model.layers) == 2  # includes input layer
    assert len(model.weights) == 2
    assert len(model.losses) == 2
    assert len(model.get_losses_for(None)) == 1
    assert len(model.get_losses_for(inputs)) == 1


@pytest.mark.skipif(K.backend() != 'tensorflow',
                    reason='Requires TF symbols')
def test_tf_keras_guide():
    import tensorflow as tf

    class Linear(layers.Layer):

        def __init__(self, units=32, input_dim=32):
            super(Linear, self).__init__()
            w_init = tf.random_normal_initializer()
            self.w = tf.Variable(initial_value=w_init(shape=(input_dim, units),
                                                      dtype='float32'),
                                 trainable=True)
            b_init = tf.zeros_initializer()
            self.b = tf.Variable(initial_value=b_init(shape=(units,),
                                                      dtype='float32'),
                                 trainable=True)

        def call(self, inputs):
            return tf.matmul(inputs, self.w) + self.b

    x = tf.ones((2, 2))
    linear_layer = Linear(4, 2)
    y = linear_layer(x)

    assert len(linear_layer.trainable_weights) == 2

    class Linear(layers.Layer):

        def __init__(self, units=32):
            super(Linear, self).__init__()
            self.units = units

        def build(self, input_shape):
            self.w = self.add_weight(shape=(input_shape[-1], self.units),
                                     initializer='random_normal',
                                     trainable=True)
            self.b = self.add_weight(shape=(self.units,),
                                     initializer='random_normal',
                                     trainable=True)

        def call(self, inputs):
            return tf.matmul(inputs, self.w) + self.b

    class MLPBlock(layers.Layer):

        def __init__(self):
            super(MLPBlock, self).__init__()
            self.linear_1 = Linear(32)
            self.linear_2 = Linear(32)
            self.linear_3 = Linear(1)

        def call(self, inputs):
            x = self.linear_1(inputs)
            x = tf.nn.relu(x)
            x = self.linear_2(x)
            x = tf.nn.relu(x)
            return self.linear_3(x)

    mlp = MLPBlock()
    y = mlp(tf.ones(shape=(3, 64)))
    assert len(mlp.weights) == 6
    assert len(mlp.trainable_weights) == 6

    class OuterLayer(layers.Layer):

        def __init__(self):
            super(OuterLayer, self).__init__()
            self.dense = layers.Dense(
                32, kernel_regularizer=tf.keras.regularizers.l2(1e-3))

        def call(self, inputs):
            return self.dense(inputs)

    layer = OuterLayer()
    _ = layer(tf.zeros((1, 1)))
    assert len(layer.losses) == 1

import pytest
import numpy as np
from numpy.testing import assert_allclose

from keras.applications import imagenet_utils as utils
from keras.models import Model
from keras.layers import Input, Lambda


def test_preprocess_input():
    # Test image batch with float and int image input
    x = np.random.uniform(0, 255, (2, 10, 10, 3))
    xint = x.astype('int32')
    assert utils.preprocess_input(x).shape == x.shape
    assert utils.preprocess_input(xint).shape == xint.shape

    out1 = utils.preprocess_input(x, 'channels_last')
    out1int = utils.preprocess_input(xint, 'channels_last')
    out2 = utils.preprocess_input(np.transpose(x, (0, 3, 1, 2)),
                                  'channels_first')
    out2int = utils.preprocess_input(np.transpose(xint, (0, 3, 1, 2)),
                                     'channels_first')
    assert_allclose(out1, out2.transpose(0, 2, 3, 1))
    assert_allclose(out1int, out2int.transpose(0, 2, 3, 1))

    # Test single image
    x = np.random.uniform(0, 255, (10, 10, 3))
    xint = x.astype('int32')
    assert utils.preprocess_input(x).shape == x.shape
    assert utils.preprocess_input(xint).shape == xint.shape

    out1 = utils.preprocess_input(x, 'channels_last')
    out1int = utils.preprocess_input(xint, 'channels_last')
    out2 = utils.preprocess_input(np.transpose(x, (2, 0, 1)),
                                  'channels_first')
    out2int = utils.preprocess_input(np.transpose(xint, (2, 0, 1)),
                                     'channels_first')
    assert_allclose(out1, out2.transpose(1, 2, 0))
    assert_allclose(out1int, out2int.transpose(1, 2, 0))

    # Test that writing over the input data works predictably
    for mode in ['torch', 'tf']:
        x = np.random.uniform(0, 255, (2, 10, 10, 3))
        xint = x.astype('int')
        x2 = utils.preprocess_input(x, mode=mode)
        xint2 = utils.preprocess_input(xint)
        assert_allclose(x, x2)
        assert xint.astype('float').max() != xint2.max()
    # Caffe mode works differently from the others
    x = np.random.uniform(0, 255, (2, 10, 10, 3))
    xint = x.astype('int')
    x2 = utils.preprocess_input(x, data_format='channels_last', mode='caffe')
    xint2 = utils.preprocess_input(xint)
    assert_allclose(x, x2[..., ::-1])
    assert xint.astype('float').max() != xint2.max()


def test_preprocess_input_symbolic():
    # Test image batch
    x = np.random.uniform(0, 255, (2, 10, 10, 3))
    inputs = Input(shape=x.shape[1:])
    outputs = Lambda(utils.preprocess_input, output_shape=x.shape[1:])(inputs)
    model = Model(inputs, outputs)
    assert model.predict(x).shape == x.shape

    outputs1 = Lambda(lambda x: utils.preprocess_input(x, 'channels_last'),
                      output_shape=x.shape[1:])(inputs)
    model1 = Model(inputs, outputs1)
    out1 = model1.predict(x)
    x2 = np.transpose(x, (0, 3, 1, 2))
    inputs2 = Input(shape=x2.shape[1:])
    outputs2 = Lambda(lambda x: utils.preprocess_input(x, 'channels_first'),
                      output_shape=x2.shape[1:])(inputs2)
    model2 = Model(inputs2, outputs2)
    out2 = model2.predict(x2)
    assert_allclose(out1, out2.transpose(0, 2, 3, 1))

    # Test single image
    x = np.random.uniform(0, 255, (10, 10, 3))
    inputs = Input(shape=x.shape)
    outputs = Lambda(utils.preprocess_input, output_shape=x.shape)(inputs)
    model = Model(inputs, outputs)
    assert model.predict(x[np.newaxis])[0].shape == x.shape

    outputs1 = Lambda(lambda x: utils.preprocess_input(x, 'channels_last'),
                      output_shape=x.shape)(inputs)
    model1 = Model(inputs, outputs1)
    out1 = model1.predict(x[np.newaxis])[0]
    x2 = np.transpose(x, (2, 0, 1))
    inputs2 = Input(shape=x2.shape)
    outputs2 = Lambda(lambda x: utils.preprocess_input(x, 'channels_first'),
                      output_shape=x2.shape)(inputs2)
    model2 = Model(inputs2, outputs2)
    out2 = model2.predict(x2[np.newaxis])[0]
    assert_allclose(out1, out2.transpose(1, 2, 0))


def DISABLED_test_decode_predictions():
    # Disabled due to SSL issues on Travis.
    x = np.zeros((2, 1000))
    x[0, 372] = 1.0
    x[1, 549] = 1.0
    outs = utils.decode_predictions(x, top=1)
    scores = [out[0][2] for out in outs]
    assert scores[0] == scores[1]

    # the numbers of columns and ImageNet classes are not identical.
    with pytest.raises(ValueError):
        utils.decode_predictions(np.ones((2, 100)))


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
import random
import os
from multiprocessing import Process, Queue
from keras import applications
from keras import backend as K


MODEL_LIST = [
    (applications.ResNet50, 2048),
    (applications.ResNet101, 2048),
    (applications.ResNet152, 2048),
    (applications.ResNet50V2, 2048),
    (applications.ResNet101V2, 2048),
    (applications.ResNet152V2, 2048),
    (applications.VGG16, 512),
    (applications.VGG19, 512),
    (applications.Xception, 2048),
    (applications.InceptionV3, 2048),
    (applications.InceptionResNetV2, 1536),
    (applications.MobileNet, 1024),
    (applications.MobileNetV2, 1280),
    (applications.DenseNet121, 1024),
    (applications.DenseNet169, 1664),
    (applications.DenseNet201, 1920),
    # Note that NASNetLarge is too heavy to test on Travis.
    (applications.NASNetMobile, 1056)
]


def _get_output_shape(model_fn):
    if K.backend() == 'cntk':
        # Create model in a subprocess so that
        # the memory consumed by InceptionResNetV2 will be
        # released back to the system after this test
        # (to deal with OOM error on CNTK backend).
        # TODO: remove the use of multiprocessing from these tests
        # once a memory clearing mechanism
        # is implemented in the CNTK backend.
        def target(queue):
            model = model_fn()
            queue.put(model.output_shape)
        queue = Queue()
        p = Process(target=target, args=(queue,))
        p.start()
        p.join()
        # The error in a subprocess won't propagate
        # to the main process, so we check if the model
        # is successfully created by checking if the output shape
        # has been put into the queue
        assert not queue.empty(), 'Model creation failed.'
        return queue.get_nowait()
    else:
        model = model_fn()
        return model.output_shape


def _test_application_basic(app, last_dim=1000):
    output_shape = _get_output_shape(lambda: app(weights=None))
    assert output_shape == (None, last_dim)


def _test_application_notop(app, last_dim):
    output_shape = _get_output_shape(
        lambda: app(weights=None, include_top=False))
    assert len(output_shape) == 4
    assert output_shape[-1] == last_dim


def test_applications():
    for _ in range(3):
        app, last_dim = random.choice(MODEL_LIST)
        _test_application_basic(app)
        _test_application_notop(app, last_dim)


if __name__ == '__main__':
    pytest.main([__file__])

from math import ceil

import numpy as np
from numpy.testing import assert_allclose, assert_raises

import pytest

from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing.sequence import make_sampling_table
from keras.preprocessing.sequence import skipgrams
from keras.preprocessing.sequence import TimeseriesGenerator


def test_pad_sequences():
    a = [[1], [1, 2], [1, 2, 3]]

    # test padding
    b = pad_sequences(a, maxlen=3, padding='pre')
    assert_allclose(b, [[0, 0, 1], [0, 1, 2], [1, 2, 3]])
    b = pad_sequences(a, maxlen=3, padding='post')
    assert_allclose(b, [[1, 0, 0], [1, 2, 0], [1, 2, 3]])

    # test truncating
    b = pad_sequences(a, maxlen=2, truncating='pre')
    assert_allclose(b, [[0, 1], [1, 2], [2, 3]])
    b = pad_sequences(a, maxlen=2, truncating='post')
    assert_allclose(b, [[0, 1], [1, 2], [1, 2]])

    # test value
    b = pad_sequences(a, maxlen=3, value=1)
    assert_allclose(b, [[1, 1, 1], [1, 1, 2], [1, 2, 3]])


def test_pad_sequences_vector():
    a = [[[1, 1]],
         [[2, 1], [2, 2]],
         [[3, 1], [3, 2], [3, 3]]]

    # test padding
    b = pad_sequences(a, maxlen=3, padding='pre')
    assert_allclose(b, [[[0, 0], [0, 0], [1, 1]],
                        [[0, 0], [2, 1], [2, 2]],
                        [[3, 1], [3, 2], [3, 3]]])
    b = pad_sequences(a, maxlen=3, padding='post')
    assert_allclose(b, [[[1, 1], [0, 0], [0, 0]],
                        [[2, 1], [2, 2], [0, 0]],
                        [[3, 1], [3, 2], [3, 3]]])

    # test truncating
    b = pad_sequences(a, maxlen=2, truncating='pre')
    assert_allclose(b, [[[0, 0], [1, 1]],
                        [[2, 1], [2, 2]],
                        [[3, 2], [3, 3]]])

    b = pad_sequences(a, maxlen=2, truncating='post')
    assert_allclose(b, [[[0, 0], [1, 1]],
                        [[2, 1], [2, 2]],
                        [[3, 1], [3, 2]]])

    # test value
    b = pad_sequences(a, maxlen=3, value=1)
    assert_allclose(b, [[[1, 1], [1, 1], [1, 1]],
                        [[1, 1], [2, 1], [2, 2]],
                        [[3, 1], [3, 2], [3, 3]]])


def test_make_sampling_table():
    a = make_sampling_table(3)
    assert_allclose(a, np.asarray([0.00315225, 0.00315225, 0.00547597]),
                    rtol=.1)


def test_skipgrams():
    # test with no window size and binary labels
    couples, labels = skipgrams(np.arange(3), vocabulary_size=3)
    for couple in couples:
        assert couple[0] in [0, 1, 2] and couple[1] in [0, 1, 2]

    # test window size and categorical labels
    couples, labels = skipgrams(np.arange(5), vocabulary_size=5, window_size=1,
                                categorical=True)
    for couple in couples:
        assert couple[0] - couple[1] <= 3
    for l in labels:
        assert len(l) == 2


def test_TimeseriesGenerator():
    data = np.array([[i] for i in range(50)])
    targets = np.array([[i] for i in range(50)])

    data_gen = TimeseriesGenerator(data, targets,
                                   length=10, sampling_rate=2,
                                   batch_size=2)
    assert len(data_gen) == 20
    assert (np.allclose(data_gen[0][0],
                        np.array([[[0], [2], [4], [6], [8]],
                                  [[1], [3], [5], [7], [9]]])))
    assert (np.allclose(data_gen[0][1],
                        np.array([[10], [11]])))
    assert (np.allclose(data_gen[1][0],
                        np.array([[[2], [4], [6], [8], [10]],
                                  [[3], [5], [7], [9], [11]]])))
    assert (np.allclose(data_gen[1][1],
                        np.array([[12], [13]])))

    data_gen = TimeseriesGenerator(data, targets,
                                   length=10, sampling_rate=2, reverse=True,
                                   batch_size=2)
    assert len(data_gen) == 20
    assert (np.allclose(data_gen[0][0],
                        np.array([[[8], [6], [4], [2], [0]],
                                  [[9], [7], [5], [3], [1]]])))
    assert (np.allclose(data_gen[0][1],
                        np.array([[10], [11]])))

    data_gen = TimeseriesGenerator(data, targets,
                                   length=10, sampling_rate=2, shuffle=True,
                                   batch_size=1)
    batch = data_gen[0]
    r = batch[1][0][0]
    assert (np.allclose(batch[0],
                        np.array([[[r - 10],
                                   [r - 8],
                                   [r - 6],
                                   [r - 4],
                                   [r - 2]]])))
    assert (np.allclose(batch[1], np.array([[r], ])))

    data_gen = TimeseriesGenerator(data, targets,
                                   length=10, sampling_rate=2, stride=2,
                                   batch_size=2)
    assert len(data_gen) == 10
    assert (np.allclose(data_gen[1][0],
                        np.array([[[4], [6], [8], [10], [12]],
                                  [[6], [8], [10], [12], [14]]])))
    assert (np.allclose(data_gen[1][1],
                        np.array([[14], [16]])))

    data_gen = TimeseriesGenerator(data, targets,
                                   length=10, sampling_rate=2,
                                   start_index=10, end_index=30,
                                   batch_size=2)
    assert len(data_gen) == 6
    assert (np.allclose(data_gen[0][0],
                        np.array([[[10], [12], [14], [16], [18]],
                                  [[11], [13], [15], [17], [19]]])))
    assert (np.allclose(data_gen[0][1],
                        np.array([[20], [21]])))

    data = np.array([np.random.random_sample((1, 2, 3, 4)) for i in range(50)])
    targets = np.array([np.random.random_sample((3, 2, 1)) for i in range(50)])
    data_gen = TimeseriesGenerator(data, targets,
                                   length=10, sampling_rate=2,
                                   start_index=10, end_index=30,
                                   batch_size=2)
    assert len(data_gen) == 6
    assert np.allclose(data_gen[0][0], np.array(
        [np.array(data[10:19:2]), np.array(data[11:20:2])]))
    assert (np.allclose(data_gen[0][1],
                        np.array([targets[20], targets[21]])))

    with assert_raises(ValueError) as context:
        TimeseriesGenerator(data, targets, length=50)
    error = str(context.exception)
    assert '`start_index+length=50 > end_index=49` is disallowed' in error


def test_TimeSeriesGenerator_doesnt_miss_any_sample():
    x = np.array([[i] for i in range(10)])

    for length in range(3, 10):
        g = TimeseriesGenerator(x, x,
                                length=length,
                                batch_size=1)
        expected = max(0, len(x) - length)
        actual = len(g)

        assert expected == actual

        if len(g) > 0:
            # All elements in range(length, 10) should be used as current step
            expected = np.arange(length, 10).reshape(-1, 1)

            y = np.concatenate([g[ix][1] for ix in range(len(g))], axis=0)
            assert_allclose(y, expected)

    x = np.array([[i] for i in range(23)])

    strides = (1, 1, 5, 7, 3, 5, 3)
    lengths = (3, 3, 4, 3, 1, 3, 7)
    batch_sizes = (6, 6, 6, 5, 6, 6, 6)
    shuffles = (False, True, True, False, False, False, False)

    for stride, length, batch_size, shuffle in zip(strides,
                                                   lengths,
                                                   batch_sizes,
                                                   shuffles):
        g = TimeseriesGenerator(x, x,
                                length=length,
                                sampling_rate=1,
                                stride=stride,
                                start_index=0,
                                end_index=None,
                                shuffle=shuffle,
                                reverse=False,
                                batch_size=batch_size)
        if shuffle:
            # all batches have the same size when shuffle is True.
            expected_sequences = ceil(
                (23 - length) / float(batch_size * stride)) * batch_size
        else:
            # last batch will be different if `(samples - length) / stride`
            # is not a multiple of `batch_size`.
            expected_sequences = ceil((23 - length) / float(stride))

        expected_batches = ceil(expected_sequences / float(batch_size))

        y = [g[ix][1] for ix in range(len(g))]

        actual_sequences = sum(len(_y) for _y in y)
        actual_batches = len(y)

        assert expected_sequences == actual_sequences
        assert expected_batches == actual_batches


if __name__ == '__main__':
    pytest.main([__file__])

# -*- coding: utf-8 -*-

import numpy as np
import pytest

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.text import one_hot
from keras.preprocessing.text import hashing_trick
from keras.preprocessing.text import text_to_word_sequence


def test_one_hot():
    text = 'The cat sat on the mat.'
    encoded = one_hot(text, 5)
    assert len(encoded) == 6
    assert np.max(encoded) <= 4
    assert np.min(encoded) >= 0


def test_hashing_trick_hash():
    text = 'The cat sat on the mat.'
    encoded = hashing_trick(text, 5)
    assert len(encoded) == 6
    assert np.max(encoded) <= 4
    assert np.min(encoded) >= 1


def test_hashing_trick_md5():
    text = 'The cat sat on the mat.'
    encoded = hashing_trick(text, 5, hash_function='md5')
    assert len(encoded) == 6
    assert np.max(encoded) <= 4
    assert np.min(encoded) >= 1


def test_tokenizer():
    texts = ['The cat sat on the mat.',
             'The dog sat on the log.',
             'Dogs and cats living together.']
    tokenizer = Tokenizer(num_words=10)
    tokenizer.fit_on_texts(texts)

    sequences = []
    for seq in tokenizer.texts_to_sequences_generator(texts):
        sequences.append(seq)
    assert np.max(np.max(sequences)) < 10
    assert np.min(np.min(sequences)) == 1

    tokenizer.fit_on_sequences(sequences)

    for mode in ['binary', 'count', 'tfidf', 'freq']:
        matrix = tokenizer.texts_to_matrix(texts, mode)


def test_sequential_fit():
    texts = ['The cat sat on the mat.',
             'The dog sat on the log.',
             'Dogs and cats living together.']
    word_sequences = [
        ['The', 'cat', 'is', 'sitting'],
        ['The', 'dog', 'is', 'standing']
    ]

    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(texts)
    tokenizer.fit_on_texts(word_sequences)

    assert tokenizer.document_count == 5

    tokenizer.texts_to_matrix(texts)
    tokenizer.texts_to_matrix(word_sequences)


def test_text_to_word_sequence():
    text = 'hello! ? world!'
    assert text_to_word_sequence(text) == ['hello', 'world']


def test_text_to_word_sequence_multichar_split():
    text = 'hello!stop?world!'
    assert text_to_word_sequence(text, split='stop') == ['hello', 'world']


def test_text_to_word_sequence_unicode():
    text = u'ali! veli? kÄ±rk dokuz elli'
    assert (text_to_word_sequence(text) ==
            [u'ali', u'veli', u'kÄ±rk', u'dokuz', u'elli'])


def test_text_to_word_sequence_unicode_multichar_split():
    text = u'ali!stopveli?stopkÄ±rkstopdokuzstopelli'
    assert (text_to_word_sequence(text, split='stop') ==
            [u'ali', u'veli', u'kÄ±rk', u'dokuz', u'elli'])


def test_tokenizer_unicode():
    texts = [u'ali veli kÄ±rk dokuz elli',
             u'ali veli kÄ±rk dokuz elli veli kÄ±rk dokuz']
    tokenizer = Tokenizer(num_words=5)
    tokenizer.fit_on_texts(texts)

    assert len(tokenizer.word_counts) == 5


def test_tokenizer_oov_flag():
    """
    Test of Out of Vocabulary (OOV) flag in Tokenizer
    """
    x_train = ['This text has only known words']
    x_test = ['This text has some unknown words']  # 2 OOVs: some, unknown

    # Default, without OOV flag
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(x_train)
    x_test_seq = tokenizer.texts_to_sequences(x_test)
    assert len(x_test_seq[0]) == 4  # discards 2 OOVs

    # With OOV feature
    tokenizer = Tokenizer(oov_token='<unk>')
    tokenizer.fit_on_texts(x_train)
    x_test_seq = tokenizer.texts_to_sequences(x_test)
    assert len(x_test_seq[0]) == 6  # OOVs marked in place


if __name__ == '__main__':
    pytest.main([__file__])

import pytest
from keras.preprocessing import image
from PIL import Image
import numpy as np
import os
import tempfile
import shutil


class TestImage(object):

    def setup_class(cls):
        cls.img_w = cls.img_h = 20
        rgb_images = []
        gray_images = []
        for n in range(8):
            bias = np.random.rand(cls.img_w, cls.img_h, 1) * 64
            variance = np.random.rand(cls.img_w, cls.img_h, 1) * (255 - 64)
            imarray = np.random.rand(cls.img_w, cls.img_h, 3) * variance + bias
            im = Image.fromarray(imarray.astype('uint8')).convert('RGB')
            rgb_images.append(im)

            imarray = np.random.rand(cls.img_w, cls.img_h, 1) * variance + bias
            im = Image.fromarray(imarray.astype('uint8').squeeze()).convert('L')
            gray_images.append(im)

        cls.all_test_images = [rgb_images, gray_images]

    def teardown_class(cls):
        del cls.all_test_images

    def test_image_data_generator(self, tmpdir):
        for test_images in self.all_test_images:
            img_list = []
            for im in test_images:
                img_list.append(image.img_to_array(im)[None, ...])

            images = np.vstack(img_list)
            generator = image.ImageDataGenerator(
                featurewise_center=True,
                samplewise_center=True,
                featurewise_std_normalization=True,
                samplewise_std_normalization=True,
                zca_whitening=True,
                rotation_range=90.,
                width_shift_range=0.1,
                height_shift_range=0.1,
                shear_range=0.5,
                zoom_range=0.2,
                channel_shift_range=0.,
                brightness_range=(1, 5),
                fill_mode='nearest',
                cval=0.5,
                horizontal_flip=True,
                vertical_flip=True)
            generator.fit(images, augment=True)

            num_samples = images.shape[0]
            for x, y in generator.flow(images, np.arange(num_samples),
                                       shuffle=False, save_to_dir=str(tmpdir),
                                       batch_size=3):
                assert x.shape == images[:3].shape
                assert list(y) == [0, 1, 2]
                break

            # Test with sample weights
            for x, y, w in generator.flow(images, np.arange(num_samples),
                                          shuffle=False,
                                          sample_weight=np.arange(num_samples) + 1,
                                          save_to_dir=str(tmpdir),
                                          batch_size=3):
                assert x.shape == images[:3].shape
                assert list(y) == [0, 1, 2]
                assert list(w) == [1, 2, 3]
                break

            # Test with `shuffle=True`
            for x, y in generator.flow(images, np.arange(num_samples),
                                       shuffle=True, save_to_dir=str(tmpdir),
                                       batch_size=3):
                assert x.shape == images[:3].shape
                # Check that the sequence is shuffled.
                assert list(y) != [0, 1, 2]
                break

            # Test without y
            for x in generator.flow(images, None,
                                    shuffle=True, save_to_dir=str(tmpdir),
                                    batch_size=3):
                assert type(x) is np.ndarray
                assert x.shape == images[:3].shape
                # Check that the sequence is shuffled.
                break

            # Test with a single miscellaneous input data array
            dsize = images.shape[0]
            x_misc1 = np.random.random(dsize)

            for i, (x, y) in enumerate(generator.flow((images, x_misc1),
                                                      np.arange(dsize),
                                                      shuffle=False, batch_size=2)):
                assert x[0].shape == images[:2].shape
                assert (x[1] == x_misc1[(i * 2):((i + 1) * 2)]).all()
                if i == 2:
                    break

            # Test with two miscellaneous inputs
            x_misc2 = np.random.random((dsize, 3, 3))

            for i, (x, y) in enumerate(generator.flow((images, [x_misc1, x_misc2]),
                                                      np.arange(dsize),
                                                      shuffle=False, batch_size=2)):
                assert x[0].shape == images[:2].shape
                assert (x[1] == x_misc1[(i * 2):((i + 1) * 2)]).all()
                assert (x[2] == x_misc2[(i * 2):((i + 1) * 2)]).all()
                if i == 2:
                    break

            # Test cases with `y = None`
            x = generator.flow(images, None, batch_size=3).next()
            assert type(x) is np.ndarray
            assert x.shape == images[:3].shape
            x = generator.flow((images, x_misc1), None,
                               batch_size=3, shuffle=False).next()
            assert type(x) is list
            assert x[0].shape == images[:3].shape
            assert (x[1] == x_misc1[:3]).all()
            x = generator.flow((images, [x_misc1, x_misc2]), None,
                               batch_size=3, shuffle=False).next()
            assert type(x) is list
            assert x[0].shape == images[:3].shape
            assert (x[1] == x_misc1[:3]).all()
            assert (x[2] == x_misc2[:3]).all()

            # Test some failure cases:
            x_misc_err = np.random.random((dsize + 1, 3, 3))

            with pytest.raises(ValueError) as e_info:
                generator.flow((images, x_misc_err), np.arange(dsize), batch_size=3)
            assert 'All of the arrays in' in str(e_info.value)

            with pytest.raises(ValueError) as e_info:
                generator.flow((images, x_misc1),
                               np.arange(dsize + 1),
                               batch_size=3)
            assert '`x` (images tensor) and `y` (labels) ' in str(e_info.value)

            # Test `flow` behavior as Sequence
            seq = generator.flow(images, np.arange(images.shape[0]),
                                 shuffle=False, save_to_dir=str(tmpdir),
                                 batch_size=3)
            assert len(seq) == images.shape[0] // 3 + 1
            x, y = seq[0]
            assert x.shape == images[:3].shape
            assert list(y) == [0, 1, 2]

            # Test with `shuffle=True`
            seq = generator.flow(images, np.arange(images.shape[0]),
                                 shuffle=True, save_to_dir=str(tmpdir),
                                 batch_size=3, seed=123)
            x, y = seq[0]
            # Check that the sequence is shuffled.
            assert list(y) != [0, 1, 2]

            # `on_epoch_end` should reshuffle the sequence.
            seq.on_epoch_end()
            x2, y2 = seq[0]
            assert list(y) != list(y2)

    def test_image_data_generator_with_split_value_error(self):
        with pytest.raises(ValueError):
            generator = image.ImageDataGenerator(validation_split=5)

    def test_image_data_generator_invalid_data(self):
        generator = image.ImageDataGenerator(
            featurewise_center=True,
            samplewise_center=True,
            featurewise_std_normalization=True,
            samplewise_std_normalization=True,
            zca_whitening=True,
            data_format='channels_last')
        # Test fit with invalid data
        with pytest.raises(ValueError):
            x = np.random.random((3, 10, 10))
            generator.fit(x)

        # Test flow with invalid data
        with pytest.raises(ValueError):
            x = np.random.random((32, 10, 10))
            generator.flow(np.arange(x.shape[0]))

    def test_image_data_generator_fit(self):
        generator = image.ImageDataGenerator(
            featurewise_center=True,
            samplewise_center=True,
            featurewise_std_normalization=True,
            samplewise_std_normalization=True,
            zca_whitening=True,
            zoom_range=(0.2, 0.2),
            data_format='channels_last')
        # Test grayscale
        x = np.random.random((32, 10, 10, 1))
        generator.fit(x)
        # Test RBG
        x = np.random.random((32, 10, 10, 3))
        generator.fit(x)
        # Test more samples than dims
        x = np.random.random((32, 4, 4, 1))
        generator.fit(x)
        generator = image.ImageDataGenerator(
            featurewise_center=True,
            samplewise_center=True,
            featurewise_std_normalization=True,
            samplewise_std_normalization=True,
            zca_whitening=True,
            data_format='channels_first')
        # Test grayscale
        x = np.random.random((32, 1, 10, 10))
        generator.fit(x)
        # Test RBG
        x = np.random.random((32, 3, 10, 10))
        generator.fit(x)
        # Test more samples than dims
        x = np.random.random((32, 1, 4, 4))
        generator.fit(x)

    def test_directory_iterator(self, tmpdir):
        num_classes = 2

        # create folders and subfolders
        paths = []
        for cl in range(num_classes):
            class_directory = 'class-{}'.format(cl)
            classpaths = [
                class_directory,
                os.path.join(class_directory, 'subfolder-1'),
                os.path.join(class_directory, 'subfolder-2'),
                os.path.join(class_directory, 'subfolder-1', 'sub-subfolder')
            ]
            for path in classpaths:
                tmpdir.join(path).mkdir()
            paths.append(classpaths)

        # save the images in the paths
        count = 0
        filenames = []
        for test_images in self.all_test_images:
            for im in test_images:
                # rotate image class
                im_class = count % num_classes
                # rotate subfolders
                classpaths = paths[im_class]
                filename = os.path.join(classpaths[count % len(classpaths)],
                                        'image-{}.jpg'.format(count))
                filenames.append(filename)
                im.save(str(tmpdir / filename))
                count += 1

        # create iterator
        generator = image.ImageDataGenerator()
        dir_iterator = generator.flow_from_directory(str(tmpdir))

        # check number of classes and images
        assert len(dir_iterator.class_indices) == num_classes
        assert len(dir_iterator.classes) == count
        assert set(dir_iterator.filenames) == set(filenames)

        # Test invalid use cases
        with pytest.raises(ValueError):
            generator.flow_from_directory(str(tmpdir), color_mode='cmyk')
        with pytest.raises(ValueError):
            generator.flow_from_directory(str(tmpdir), class_mode='output')

        def preprocessing_function(x):
            """This will fail if not provided by a Numpy array.
            Note: This is made to enforce backward compatibility.
            """

            assert x.shape == (26, 26, 3)
            assert type(x) is np.ndarray

            return np.zeros_like(x)

        # Test usage as Sequence
        generator = image.ImageDataGenerator(
            preprocessing_function=preprocessing_function)
        dir_seq = generator.flow_from_directory(str(tmpdir),
                                                target_size=(26, 26),
                                                color_mode='rgb',
                                                batch_size=3,
                                                class_mode='categorical')
        assert len(dir_seq) == count // 3 + 1
        x1, y1 = dir_seq[1]
        assert x1.shape == (3, 26, 26, 3)
        assert y1.shape == (3, num_classes)
        x1, y1 = dir_seq[5]
        assert (x1 == 0).all()

        with pytest.raises(ValueError):
            x1, y1 = dir_seq[9]

    def test_directory_iterator_class_mode_input(self, tmpdir):
        tmpdir.join('class-1').mkdir()

        # save the images in the paths
        count = 0
        for test_images in self.all_test_images:
            for im in test_images:
                filename = str(tmpdir / 'class-1' / 'image-{}.jpg'.format(count))
                im.save(filename)
                count += 1

        # create iterator
        generator = image.ImageDataGenerator()
        dir_iterator = generator.flow_from_directory(str(tmpdir),
                                                     class_mode='input')
        batch = next(dir_iterator)

        # check if input and output have the same shape
        assert(batch[0].shape == batch[1].shape)
        # check if the input and output images are not the same numpy array
        input_img = batch[0][0]
        output_img = batch[1][0]
        output_img[0][0][0] += 1
        assert(input_img[0][0][0] != output_img[0][0][0])

    @pytest.mark.parametrize('validation_split,num_training', [
        (0.25, 12),
        (0.40, 10),
        (0.50, 8),
    ])
    def test_directory_iterator_with_validation_split(self, validation_split,
                                                      num_training):
        num_classes = 2
        tmp_folder = tempfile.mkdtemp(prefix='test_images')

        # create folders and subfolders
        paths = []
        for cl in range(num_classes):
            class_directory = 'class-{}'.format(cl)
            classpaths = [
                class_directory,
                os.path.join(class_directory, 'subfolder-1'),
                os.path.join(class_directory, 'subfolder-2'),
                os.path.join(class_directory, 'subfolder-1', 'sub-subfolder')
            ]
            for path in classpaths:
                os.mkdir(os.path.join(tmp_folder, path))
            paths.append(classpaths)

        # save the images in the paths
        count = 0
        filenames = []
        for test_images in self.all_test_images:
            for im in test_images:
                # rotate image class
                im_class = count % num_classes
                # rotate subfolders
                classpaths = paths[im_class]
                filename = os.path.join(classpaths[count % len(classpaths)],
                                        'image-{}.jpg'.format(count))
                filenames.append(filename)
                im.save(os.path.join(tmp_folder, filename))
                count += 1

        # create iterator
        generator = image.ImageDataGenerator(validation_split=validation_split)

        with pytest.raises(ValueError):
            generator.flow_from_directory(tmp_folder, subset='foo')

        train_iterator = generator.flow_from_directory(tmp_folder,
                                                       subset='training')
        assert train_iterator.samples == num_training

        valid_iterator = generator.flow_from_directory(tmp_folder,
                                                       subset='validation')
        assert valid_iterator.samples == count - num_training

        # check number of classes and images
        assert len(train_iterator.class_indices) == num_classes
        assert len(train_iterator.classes) == num_training
        assert len(set(train_iterator.filenames) & set(filenames)) == num_training

        shutil.rmtree(tmp_folder)

    def test_img_utils(self):
        height, width = 10, 8

        # Test th data format
        x = np.random.random((3, height, width))
        img = image.array_to_img(x, data_format='channels_first')
        assert img.size == (width, height)
        x = image.img_to_array(img, data_format='channels_first')
        assert x.shape == (3, height, width)
        # Test 2D
        x = np.random.random((1, height, width))
        img = image.array_to_img(x, data_format='channels_first')
        assert img.size == (width, height)
        x = image.img_to_array(img, data_format='channels_first')
        assert x.shape == (1, height, width)

        # Test tf data format
        x = np.random.random((height, width, 3))
        img = image.array_to_img(x, data_format='channels_last')
        assert img.size == (width, height)
        x = image.img_to_array(img, data_format='channels_last')
        assert x.shape == (height, width, 3)
        # Test 2D
        x = np.random.random((height, width, 1))
        img = image.array_to_img(x, data_format='channels_last')
        assert img.size == (width, height)
        x = image.img_to_array(img, data_format='channels_last')
        assert x.shape == (height, width, 1)

        # Test invalid use case
        with pytest.raises(ValueError):
            x = np.random.random((height, width))  # not 3D
            img = image.array_to_img(x, data_format='channels_first')
        with pytest.raises(ValueError):  # unknown data_format
            x = np.random.random((height, width, 3))
            img = image.array_to_img(x, data_format='channels')
        with pytest.raises(ValueError):  # neither RGB nor gray-scale
            x = np.random.random((height, width, 5))
            img = image.array_to_img(x, data_format='channels_last')
        with pytest.raises(ValueError):  # unknown data_format
            x = np.random.random((height, width, 3))
            img = image.img_to_array(x, data_format='channels')
        with pytest.raises(ValueError):  # neither RGB nor gray-scale
            x = np.random.random((height, width, 5, 3))
            img = image.img_to_array(x, data_format='channels_last')

    def test_random_transforms(self):
        x = np.random.random((2, 28, 28))
        assert image.random_rotation(x, 45).shape == (2, 28, 28)
        assert image.random_shift(x, 1, 1).shape == (2, 28, 28)
        assert image.random_shear(x, 20).shape == (2, 28, 28)
        assert image.random_zoom(x, (5, 5)).shape == (2, 28, 28)
        assert image.random_channel_shift(x, 20).shape == (2, 28, 28)

        # Test get_random_transform with predefined seed
        seed = 1
        generator = image.ImageDataGenerator(
            rotation_range=90.,
            width_shift_range=0.1,
            height_shift_range=0.1,
            shear_range=0.5,
            zoom_range=0.2,
            channel_shift_range=0.1,
            brightness_range=(1, 5),
            horizontal_flip=True,
            vertical_flip=True)
        transform_dict = generator.get_random_transform(x.shape, seed)
        transform_dict2 = generator.get_random_transform(x.shape, seed * 2)
        assert transform_dict['theta'] != 0
        assert transform_dict['theta'] != transform_dict2['theta']
        assert transform_dict['tx'] != 0
        assert transform_dict['tx'] != transform_dict2['tx']
        assert transform_dict['ty'] != 0
        assert transform_dict['ty'] != transform_dict2['ty']
        assert transform_dict['shear'] != 0
        assert transform_dict['shear'] != transform_dict2['shear']
        assert transform_dict['zx'] != 0
        assert transform_dict['zx'] != transform_dict2['zx']
        assert transform_dict['zy'] != 0
        assert transform_dict['zy'] != transform_dict2['zy']
        assert transform_dict['channel_shift_intensity'] != 0
        assert (transform_dict['channel_shift_intensity'] !=
                transform_dict2['channel_shift_intensity'])
        assert transform_dict['brightness'] != 0
        assert transform_dict['brightness'] != transform_dict2['brightness']

        # Test get_random_transform without any randomness
        generator = image.ImageDataGenerator()
        transform_dict = generator.get_random_transform(x.shape, seed)
        assert transform_dict['theta'] == 0
        assert transform_dict['tx'] == 0
        assert transform_dict['ty'] == 0
        assert transform_dict['shear'] == 0
        assert transform_dict['zx'] == 1
        assert transform_dict['zy'] == 1
        assert transform_dict['channel_shift_intensity'] is None
        assert transform_dict['brightness'] is None

    def test_deterministic_transform(self):
        x = np.ones((32, 32, 3))
        generator = image.ImageDataGenerator(
            rotation_range=90,
            fill_mode='constant')
        x = np.random.random((32, 32, 3))
        assert np.allclose(generator.apply_transform(x, {'flip_vertical': True}),
                           x[::-1, :, :])
        assert np.allclose(generator.apply_transform(x, {'flip_horizontal': True}),
                           x[:, ::-1, :])
        x = np.ones((3, 3, 3))
        x_rotated = np.array([[[0., 0., 0.],
                               [0., 0., 0.],
                               [1., 1., 1.]],
                              [[0., 0., 0.],
                               [1., 1., 1.],
                               [1., 1., 1.]],
                              [[0., 0., 0.],
                               [0., 0., 0.],
                               [1., 1., 1.]]])
        assert np.allclose(generator.apply_transform(x, {'theta': 45}),
                           x_rotated)
        assert np.allclose(image.apply_affine_transform(
            x, theta=45, channel_axis=2, fill_mode='constant'), x_rotated)

    def test_batch_standardize(self):
        # ImageDataGenerator.standardize should work on batches
        for test_images in self.all_test_images:
            img_list = []
            for im in test_images:
                img_list.append(image.img_to_array(im)[None, ...])

            images = np.vstack(img_list)
            generator = image.ImageDataGenerator(
                featurewise_center=True,
                samplewise_center=True,
                featurewise_std_normalization=True,
                samplewise_std_normalization=True,
                zca_whitening=True,
                rotation_range=90.,
                width_shift_range=0.1,
                height_shift_range=0.1,
                shear_range=0.5,
                zoom_range=0.2,
                channel_shift_range=0.,
                brightness_range=(1, 5),
                fill_mode='nearest',
                cval=0.5,
                horizontal_flip=True,
                vertical_flip=True)
            generator.fit(images, augment=True)

            transformed = np.copy(images)
            for i, im in enumerate(transformed):
                transformed[i] = generator.random_transform(im)
            transformed = generator.standardize(transformed)

    def test_load_img(self, tmpdir):
        filename = str(tmpdir / 'image.png')

        original_im_array = np.array(255 * np.random.rand(100, 100, 3),
                                     dtype=np.uint8)
        original_im = image.array_to_img(original_im_array, scale=False)
        original_im.save(filename)

        # Test that loaded image is exactly equal to original.

        loaded_im = image.load_img(filename)
        loaded_im_array = image.img_to_array(loaded_im)
        assert loaded_im_array.shape == original_im_array.shape
        assert np.all(loaded_im_array == original_im_array)

        loaded_im = image.load_img(filename, grayscale=True)
        loaded_im_array = image.img_to_array(loaded_im)
        assert loaded_im_array.shape == (original_im_array.shape[0],
                                         original_im_array.shape[1], 1)

        # Test that nothing is changed when target size is equal to original.

        loaded_im = image.load_img(filename, target_size=(100, 100))
        loaded_im_array = image.img_to_array(loaded_im)
        assert loaded_im_array.shape == original_im_array.shape
        assert np.all(loaded_im_array == original_im_array)

        loaded_im = image.load_img(filename, grayscale=True,
                                   target_size=(100, 100))
        loaded_im_array = image.img_to_array(loaded_im)
        assert loaded_im_array.shape == (original_im_array.shape[0],
                                         original_im_array.shape[1], 1)

        # Test down-sampling with bilinear interpolation.

        loaded_im = image.load_img(filename, target_size=(25, 25))
        loaded_im_array = image.img_to_array(loaded_im)
        assert loaded_im_array.shape == (25, 25, 3)

        loaded_im = image.load_img(filename, grayscale=True,
                                   target_size=(25, 25))
        loaded_im_array = image.img_to_array(loaded_im)
        assert loaded_im_array.shape == (25, 25, 1)

        # Test down-sampling with nearest neighbor interpolation.

        loaded_im_nearest = image.load_img(filename, target_size=(25, 25),
                                           interpolation="nearest")
        loaded_im_array_nearest = image.img_to_array(loaded_im_nearest)
        assert loaded_im_array_nearest.shape == (25, 25, 3)
        assert np.any(loaded_im_array_nearest != loaded_im_array)

        # Check that exception is raised if interpolation not supported.

        loaded_im = image.load_img(filename, interpolation="unsupported")
        with pytest.raises(ValueError):
            loaded_im = image.load_img(filename, target_size=(25, 25),
                                       interpolation="unsupported")


if __name__ == '__main__':
    pytest.main([__file__])


# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import re
import inspect
import os
import shutil
import six

try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib

import keras
from keras import backend as K
from keras.backend import numpy_backend

from docs.structure import EXCLUDE
from docs.structure import PAGES
from docs.structure import template_np_implementation
from docs.structure import template_hidden_np_implementation

import sys
if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding('utf8')

keras_dir = pathlib.Path(__file__).resolve().parents[1]


def get_function_signature(function, method=True):
    wrapped = getattr(function, '_original_function', None)
    if wrapped is None:
        signature = inspect.getfullargspec(function)
    else:
        signature = inspect.getfullargspec(wrapped)
    defaults = signature.defaults
    if method:
        args = signature.args[1:]
    else:
        args = signature.args
    if defaults:
        kwargs = zip(args[-len(defaults):], defaults)
        args = args[:-len(defaults)]
    else:
        kwargs = []
    st = '%s.%s(' % (clean_module_name(function.__module__), function.__name__)

    for a in args:
        st += str(a) + ', '
    for a, v in kwargs:
        if isinstance(v, str):
            v = '\'' + v + '\''
        st += str(a) + '=' + str(v) + ', '
    if kwargs or args:
        signature = st[:-2] + ')'
    else:
        signature = st + ')'
    return post_process_signature(signature)


def get_class_signature(cls):
    try:
        class_signature = get_function_signature(cls.__init__)
        class_signature = class_signature.replace('__init__', cls.__name__)
    except (TypeError, AttributeError):
        # in case the class inherits from object and does not
        # define __init__
        class_signature = "{clean_module_name}.{cls_name}()".format(
            clean_module_name=cls.__module__,
            cls_name=cls.__name__
        )
    return post_process_signature(class_signature)


def post_process_signature(signature):
    parts = re.split(r'\.(?!\d)', signature)
    if len(parts) >= 4:
        if parts[1] == 'layers':
            signature = 'keras.layers.' + '.'.join(parts[3:])
        if parts[1] == 'utils':
            signature = 'keras.utils.' + '.'.join(parts[3:])
        if parts[1] == 'backend':
            signature = 'keras.backend.' + '.'.join(parts[3:])
        if parts[1] == 'callbacks':
            signature = 'keras.callbacks.' + '.'.join(parts[3:])
    return signature


def clean_module_name(name):
    if name.startswith('keras_applications'):
        name = name.replace('keras_applications', 'keras.applications')
    if name.startswith('keras_preprocessing'):
        name = name.replace('keras_preprocessing', 'keras.preprocessing')
    return name


def class_to_source_link(cls):
    module_name = clean_module_name(cls.__module__)
    path = module_name.replace('.', '/')
    path += '.py'
    line = inspect.getsourcelines(cls)[-1]
    link = ('https://github.com/keras-team/'
            'keras/blob/master/' + path + '#L' + str(line))
    return '[[source]](' + link + ')'


def code_snippet(snippet):
    result = '```python\n'
    result += snippet.encode('unicode_escape').decode('utf8') + '\n'
    result += '```\n'
    return result


def count_leading_spaces(s):
    ws = re.search(r'\S', s)
    if ws:
        return ws.start()
    else:
        return 0


def process_list_block(docstring, starting_point, section_end,
                       leading_spaces, marker):
    ending_point = docstring.find('\n\n', starting_point)
    block = docstring[starting_point:
                      (ending_point - 1 if ending_point > -1
                       else section_end)]
    # Place marker for later reinjection.
    docstring_slice = docstring[
        starting_point:section_end].replace(block, marker)
    docstring = (docstring[:starting_point] +
                 docstring_slice +
                 docstring[section_end:])
    lines = block.split('\n')
    # Remove the computed number of leading white spaces from each line.
    lines = [re.sub('^' + ' ' * leading_spaces, '', line) for line in lines]
    # Usually lines have at least 4 additional leading spaces.
    # These have to be removed, but first the list roots have to be detected.
    top_level_regex = r'^    ([^\s\\\(]+):(.*)'
    top_level_replacement = r'- __\1__:\2'
    lines = [re.sub(top_level_regex, top_level_replacement, line)
             for line in lines]
    # All the other lines get simply the 4 leading space (if present) removed
    lines = [re.sub(r'^    ', '', line) for line in lines]
    # Fix text lines after lists
    indent = 0
    text_block = False
    for i in range(len(lines)):
        line = lines[i]
        spaces = re.search(r'\S', line)
        if spaces:
            # If it is a list element
            if line[spaces.start()] == '-':
                indent = spaces.start() + 1
                if text_block:
                    text_block = False
                    lines[i] = '\n' + line
            elif spaces.start() < indent:
                text_block = True
                indent = spaces.start()
                lines[i] = '\n' + line
        else:
            text_block = False
            indent = 0
    block = '\n'.join(lines)
    return docstring, block


def process_docstring(docstring):
    # First, extract code blocks and process them.
    code_blocks = []
    if '```' in docstring:
        tmp = docstring[:]
        while '```' in tmp:
            tmp = tmp[tmp.find('```'):]
            index = tmp[3:].find('```') + 6
            snippet = tmp[:index]
            # Place marker in docstring for later reinjection.
            docstring = docstring.replace(
                snippet, '$CODE_BLOCK_%d' % len(code_blocks))
            snippet_lines = snippet.split('\n')
            # Remove leading spaces.
            num_leading_spaces = snippet_lines[-1].find('`')
            snippet_lines = ([snippet_lines[0]] +
                             [line[num_leading_spaces:]
                             for line in snippet_lines[1:]])
            # Most code snippets have 3 or 4 more leading spaces
            # on inner lines, but not all. Remove them.
            inner_lines = snippet_lines[1:-1]
            leading_spaces = None
            for line in inner_lines:
                if not line or line[0] == '\n':
                    continue
                spaces = count_leading_spaces(line)
                if leading_spaces is None:
                    leading_spaces = spaces
                if spaces < leading_spaces:
                    leading_spaces = spaces
            if leading_spaces:
                snippet_lines = ([snippet_lines[0]] +
                                 [line[leading_spaces:]
                                  for line in snippet_lines[1:-1]] +
                                 [snippet_lines[-1]])
            snippet = '\n'.join(snippet_lines)
            code_blocks.append(snippet)
            tmp = tmp[index:]

    # Format docstring lists.
    section_regex = r'\n( +)# (.*)\n'
    section_idx = re.search(section_regex, docstring)
    shift = 0
    sections = {}
    while section_idx and section_idx.group(2):
        anchor = section_idx.group(2)
        leading_spaces = len(section_idx.group(1))
        shift += section_idx.end()
        next_section_idx = re.search(section_regex, docstring[shift:])
        if next_section_idx is None:
            section_end = -1
        else:
            section_end = shift + next_section_idx.start()
        marker = '$' + anchor.replace(' ', '_') + '$'
        docstring, content = process_list_block(docstring,
                                                shift,
                                                section_end,
                                                leading_spaces,
                                                marker)
        sections[marker] = content
        # `docstring` has changed, so we can't use `next_section_idx` anymore
        # we have to recompute it
        section_idx = re.search(section_regex, docstring[shift:])

    # Format docstring section titles.
    docstring = re.sub(r'\n(\s+)# (.*)\n',
                       r'\n\1__\2__\n\n',
                       docstring)

    # Strip all remaining leading spaces.
    lines = docstring.split('\n')
    docstring = '\n'.join([line.lstrip(' ') for line in lines])

    # Reinject list blocks.
    for marker, content in sections.items():
        docstring = docstring.replace(marker, content)

    # Reinject code blocks.
    for i, code_block in enumerate(code_blocks):
        docstring = docstring.replace(
            '$CODE_BLOCK_%d' % i, code_block)
    return docstring


def add_np_implementation(function, docstring):
    np_implementation = getattr(numpy_backend, function.__name__)
    code = inspect.getsource(np_implementation)
    code_lines = code.split('\n')
    for i in range(len(code_lines)):
        if code_lines[i]:
            # if there is something on the line, add 8 spaces.
            code_lines[i] = '        ' + code_lines[i]
    code = '\n'.join(code_lines[:-1])

    if len(code_lines) < 10:
        section = template_np_implementation.replace('{{code}}', code)
    else:
        section = template_hidden_np_implementation.replace('{{code}}', code)
    return docstring.replace('{{np_implementation}}', section)


def read_file(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def collect_class_methods(cls, methods):
    if isinstance(methods, (list, tuple)):
        return [getattr(cls, m) if isinstance(m, str) else m for m in methods]
    methods = []
    for _, method in inspect.getmembers(cls, predicate=inspect.isroutine):
        if method.__name__[0] == '_' or method.__name__ in EXCLUDE:
            continue
        methods.append(method)
    return methods


def render_function(function, method=True):
    subblocks = []
    signature = get_function_signature(function, method=method)
    if method:
        signature = signature.replace(
            clean_module_name(function.__module__) + '.', '')
    subblocks.append('### ' + function.__name__ + '\n')
    subblocks.append(code_snippet(signature))
    docstring = function.__doc__
    if docstring:
        if ('backend' in signature and
                '{{np_implementation}}' in docstring):
            docstring = add_np_implementation(function, docstring)
        subblocks.append(process_docstring(docstring))
    return '\n\n'.join(subblocks)


def read_page_data(page_data, type):
    assert type in ['classes', 'functions', 'methods']
    data = page_data.get(type, [])
    for module in page_data.get('all_module_{}'.format(type), []):
        module_data = []
        for name in dir(module):
            if name[0] == '_' or name in EXCLUDE:
                continue
            module_member = getattr(module, name)
            if (inspect.isclass(module_member) and type == 'classes' or
               inspect.isfunction(module_member) and type == 'functions'):
                instance = module_member
                if module.__name__ in instance.__module__:
                    if instance not in module_data:
                        module_data.append(instance)
        module_data.sort(key=lambda x: id(x))
        data += module_data
    return data


def get_module_docstring(filepath):
    """Extract the module docstring.

    Also finds the line at which the docstring ends.
    """
    co = compile(open(filepath, encoding='utf-8').read(), filepath, 'exec')
    if co.co_consts and isinstance(co.co_consts[0], six.string_types):
        docstring = co.co_consts[0]
    else:
        print('Could not get the docstring from ' + filepath)
        docstring = ''
    return docstring, co.co_firstlineno


def copy_examples(examples_dir, destination_dir):
    """Copy the examples directory in the documentation.

    Prettify files by extracting the docstrings written in Markdown.
    """
    pathlib.Path(destination_dir).mkdir(exist_ok=True)
    for file in os.listdir(examples_dir):
        if not file.endswith('.py'):
            continue
        module_path = os.path.join(examples_dir, file)
        docstring, starting_line = get_module_docstring(module_path)
        destination_file = os.path.join(destination_dir, file[:-2] + 'md')
        with open(destination_file, 'w+', encoding='utf-8') as f_out, \
                open(os.path.join(examples_dir, file),
                     'r+', encoding='utf-8') as f_in:

            f_out.write(docstring + '\n\n')

            # skip docstring
            for _ in range(starting_line):
                next(f_in)

            f_out.write('```python\n')
            # next line might be empty.
            line = next(f_in)
            if line != '\n':
                f_out.write(line)

            # copy the rest of the file.
            for line in f_in:
                f_out.write(line)
            f_out.write('```')


def generate(sources_dir):
    """Generates the markdown files for the documentation.

    # Arguments
        sources_dir: Where to put the markdown files.
    """
    template_dir = os.path.join(str(keras_dir), 'docs', 'templates')

    if K.backend() != 'tensorflow':
        raise RuntimeError('The documentation must be built '
                           'with the TensorFlow backend because this '
                           'is the only backend with docstrings.')

    print('Cleaning up existing sources directory.')
    if os.path.exists(sources_dir):
        shutil.rmtree(sources_dir)

    print('Populating sources directory with templates.')
    shutil.copytree(template_dir, sources_dir)

    readme = read_file(os.path.join(str(keras_dir), 'README.md'))
    index = read_file(os.path.join(template_dir, 'index.md'))
    index = index.replace('{{autogenerated}}', readme[readme.find('##'):])
    with open(os.path.join(sources_dir, 'index.md'), 'w', encoding='utf-8') as f:
        f.write(index)

    print('Generating docs for Keras %s.' % keras.__version__)
    for page_data in PAGES:
        classes = read_page_data(page_data, 'classes')

        blocks = []
        for element in classes:
            if not isinstance(element, (list, tuple)):
                element = (element, [])
            cls = element[0]
            subblocks = []
            signature = get_class_signature(cls)
            subblocks.append('<span style="float:right;">' +
                             class_to_source_link(cls) + '</span>')
            if element[1]:
                subblocks.append('## ' + cls.__name__ + ' class\n')
            else:
                subblocks.append('### ' + cls.__name__ + '\n')
            subblocks.append(code_snippet(signature))
            docstring = cls.__doc__
            if docstring:
                subblocks.append(process_docstring(docstring))
            methods = collect_class_methods(cls, element[1])
            if methods:
                subblocks.append('\n---')
                subblocks.append('## ' + cls.__name__ + ' methods\n')
                subblocks.append('\n---\n'.join(
                    [render_function(method, method=True)
                     for method in methods]))
            blocks.append('\n'.join(subblocks))

        methods = read_page_data(page_data, 'methods')

        for method in methods:
            blocks.append(render_function(method, method=True))

        functions = read_page_data(page_data, 'functions')

        for function in functions:
            blocks.append(render_function(function, method=False))

        if not blocks:
            raise RuntimeError('Found no content for page ' +
                               page_data['page'])

        mkdown = '\n----\n\n'.join(blocks)
        # Save module page.
        # Either insert content into existing page,
        # or create page otherwise.
        page_name = page_data['page']
        path = os.path.join(sources_dir, page_name)
        if os.path.exists(path):
            template = read_file(path)
            if '{{autogenerated}}' not in template:
                raise RuntimeError('Template found for ' + path +
                                   ' but missing {{autogenerated}}'
                                   ' tag.')
            mkdown = template.replace('{{autogenerated}}', mkdown)
            print('...inserting autogenerated content into template:', path)
        else:
            print('...creating new page with autogenerated content:', path)
        subdir = os.path.dirname(path)
        if not os.path.exists(subdir):
            os.makedirs(subdir)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(mkdown)

    shutil.copyfile(os.path.join(str(keras_dir), 'CONTRIBUTING.md'),
                    os.path.join(str(sources_dir), 'contributing.md'))
    copy_examples(os.path.join(str(keras_dir), 'examples'),
                  os.path.join(str(sources_dir), 'examples'))


if __name__ == '__main__':
    generate(os.path.join(str(keras_dir), 'docs', 'sources'))

# -*- coding: utf-8 -*-
'''
General documentation architecture:

Home
Index

- Getting started
    Getting started with the sequential model
    Getting started with the functional api
    FAQ

- Models
    About Keras models
        explain when one should use Sequential or functional API
        explain compilation step
        explain weight saving, weight loading
        explain serialization, deserialization
    Sequential
    Model (functional API)

- Layers
    About Keras layers
        explain common layer functions: get_weights, set_weights, get_config
        explain input_shape
        explain usage on non-Keras tensors
    Core Layers
    Convolutional Layers
    Pooling Layers
    Locally-connected Layers
    Recurrent Layers
    Embedding Layers
    Merge Layers
    Advanced Activations Layers
    Normalization Layers
    Noise Layers
    Layer Wrappers
    Writing your own Keras layers

- Preprocessing
    Sequence Preprocessing
    Text Preprocessing
    Image Preprocessing

Losses
Metrics
Optimizers
Activations
Callbacks
Datasets
Applications
Backend
Initializers
Regularizers
Constraints
Visualization
Scikit-learn API
Utils
Contributing

'''
from keras import utils
from keras import layers
from keras.layers import advanced_activations
from keras.layers import noise
from keras.layers import wrappers
from keras import initializers
from keras import optimizers
from keras import callbacks
from keras import models
from keras import losses
from keras import metrics
from keras import backend
from keras import constraints
from keras import activations
from keras import preprocessing


EXCLUDE = {
    'Optimizer',
    'TFOptimizer',
    'Wrapper',
    'get_session',
    'set_session',
    'CallbackList',
    'serialize',
    'deserialize',
    'get',
    'set_image_dim_ordering',
    'normalize_data_format',
    'image_dim_ordering',
    'get_variable_shape',
    'Constraint'
}

# For each class to document, it is possible to:
# 1) Document only the class: [classA, classB, ...]
# 2) Document all its methods: [classA, (classB, "*")]
# 3) Choose which methods to document (methods listed as strings):
# [classA, (classB, ["method1", "method2", ...]), ...]
# 4) Choose which methods to document (methods listed as qualified names):
# [classA, (classB, [module.classB.method1, module.classB.method2, ...]), ...]
PAGES = [
    {
        'page': 'models/sequential.md',
        'methods': [
            models.Sequential.compile,
            models.Sequential.fit,
            models.Sequential.evaluate,
            models.Sequential.predict,
            models.Sequential.train_on_batch,
            models.Sequential.test_on_batch,
            models.Sequential.predict_on_batch,
            models.Sequential.fit_generator,
            models.Sequential.evaluate_generator,
            models.Sequential.predict_generator,
            models.Sequential.get_layer,
        ],
    },
    {
        'page': 'models/model.md',
        'methods': [
            models.Model.compile,
            models.Model.fit,
            models.Model.evaluate,
            models.Model.predict,
            models.Model.train_on_batch,
            models.Model.test_on_batch,
            models.Model.predict_on_batch,
            models.Model.fit_generator,
            models.Model.evaluate_generator,
            models.Model.predict_generator,
            models.Model.get_layer,
        ]
    },
    {
        'page': 'layers/core.md',
        'classes': [
            layers.Dense,
            layers.Activation,
            layers.Dropout,
            layers.Flatten,
            layers.Input,
            layers.Reshape,
            layers.Permute,
            layers.RepeatVector,
            layers.Lambda,
            layers.ActivityRegularization,
            layers.Masking,
            layers.SpatialDropout1D,
            layers.SpatialDropout2D,
            layers.SpatialDropout3D,
        ],
    },
    {
        'page': 'layers/convolutional.md',
        'classes': [
            layers.Conv1D,
            layers.Conv2D,
            layers.SeparableConv1D,
            layers.SeparableConv2D,
            layers.DepthwiseConv2D,
            layers.Conv2DTranspose,
            layers.Conv3D,
            layers.Conv3DTranspose,
            layers.Cropping1D,
            layers.Cropping2D,
            layers.Cropping3D,
            layers.UpSampling1D,
            layers.UpSampling2D,
            layers.UpSampling3D,
            layers.ZeroPadding1D,
            layers.ZeroPadding2D,
            layers.ZeroPadding3D,
        ],
    },
    {
        'page': 'layers/pooling.md',
        'classes': [
            layers.MaxPooling1D,
            layers.MaxPooling2D,
            layers.MaxPooling3D,
            layers.AveragePooling1D,
            layers.AveragePooling2D,
            layers.AveragePooling3D,
            layers.GlobalMaxPooling1D,
            layers.GlobalAveragePooling1D,
            layers.GlobalMaxPooling2D,
            layers.GlobalAveragePooling2D,
            layers.GlobalMaxPooling3D,
            layers.GlobalAveragePooling3D,
        ],
    },
    {
        'page': 'layers/local.md',
        'classes': [
            layers.LocallyConnected1D,
            layers.LocallyConnected2D,
        ],
    },
    {
        'page': 'layers/recurrent.md',
        'classes': [
            layers.RNN,
            layers.SimpleRNN,
            layers.GRU,
            layers.LSTM,
            layers.ConvLSTM2D,
            layers.ConvLSTM2DCell,
            layers.SimpleRNNCell,
            layers.GRUCell,
            layers.LSTMCell,
            layers.CuDNNGRU,
            layers.CuDNNLSTM,
        ],
    },
    {
        'page': 'layers/embeddings.md',
        'classes': [
            layers.Embedding,
        ],
    },
    {
        'page': 'layers/normalization.md',
        'classes': [
            layers.BatchNormalization,
        ],
    },
    {
        'page': 'layers/advanced-activations.md',
        'all_module_classes': [advanced_activations],
    },
    {
        'page': 'layers/noise.md',
        'all_module_classes': [noise],
    },
    {
        'page': 'layers/merge.md',
        'classes': [
            layers.Add,
            layers.Subtract,
            layers.Multiply,
            layers.Average,
            layers.Maximum,
            layers.Minimum,
            layers.Concatenate,
            layers.Dot,
        ],
        'functions': [
            layers.add,
            layers.subtract,
            layers.multiply,
            layers.average,
            layers.maximum,
            layers.minimum,
            layers.concatenate,
            layers.dot,
        ]
    },
    {
        'page': 'preprocessing/sequence.md',
        'functions': [
            preprocessing.sequence.pad_sequences,
            preprocessing.sequence.skipgrams,
            preprocessing.sequence.make_sampling_table,
        ],
        'classes': [
            preprocessing.sequence.TimeseriesGenerator,
        ]
    },
    {
        'page': 'preprocessing/image.md',
        'classes': [
            (preprocessing.image.ImageDataGenerator, '*')
        ]
    },
    {
        'page': 'preprocessing/text.md',
        'functions': [
            preprocessing.text.hashing_trick,
            preprocessing.text.one_hot,
            preprocessing.text.text_to_word_sequence,
        ],
        'classes': [
            preprocessing.text.Tokenizer,
        ]
    },
    {
        'page': 'layers/wrappers.md',
        'all_module_classes': [wrappers],
    },
    {
        'page': 'metrics.md',
        'all_module_functions': [metrics],
    },
    {
        'page': 'losses.md',
        'all_module_functions': [losses],
    },
    {
        'page': 'initializers.md',
        'all_module_functions': [initializers],
        'all_module_classes': [initializers],
    },
    {
        'page': 'optimizers.md',
        'all_module_classes': [optimizers],
    },
    {
        'page': 'callbacks.md',
        'all_module_classes': [callbacks],
    },
    {
        'page': 'activations.md',
        'all_module_functions': [activations],
    },
    {
        'page': 'backend.md',
        'all_module_functions': [backend],
    },
    {
        'page': 'constraints.md',
        'all_module_classes': [constraints],
    },
    {
        'page': 'utils.md',
        'functions': [utils.to_categorical,
                      utils.normalize,
                      utils.get_file,
                      utils.print_summary,
                      utils.plot_model,
                      utils.multi_gpu_model],
        'classes': [utils.CustomObjectScope,
                    utils.HDF5Matrix,
                    utils.Sequence],
    },
]

ROOT = 'http://keras.io/'

template_np_implementation = """# Numpy implementation

    ```python
{{code}}
    ```
"""

template_hidden_np_implementation = """# Numpy implementation

    <details>
    <summary>Show the Numpy implementation</summary>

    ```python
{{code}}
    ```

    </details>
"""

'''Trains a simple deep NN on the MNIST dataset.

Gets to 98.40% test accuracy after 20 epochs
(there is *a lot* of margin for parameter tuning).
2 seconds per epoch on a K520 GPU.
'''

from __future__ import print_function

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import RMSprop

batch_size = 128
num_classes = 10
epochs = 20

# the data, split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

x_train = x_train.reshape(60000, 784)
x_test = x_test.reshape(10000, 784)
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

model = Sequential()
model.add(Dense(512, activation='relu', input_shape=(784,)))
model.add(Dropout(0.2))
model.add(Dense(512, activation='relu'))
model.add(Dropout(0.2))
model.add(Dense(num_classes, activation='softmax'))

model.summary()

model.compile(loss='categorical_crossentropy',
              optimizer=RMSprop(),
              metrics=['accuracy'])

history = model.fit(x_train, y_train,
                    batch_size=batch_size,
                    epochs=epochs,
                    verbose=1,
                    validation_data=(x_test, y_test))
score = model.evaluate(x_test, y_test, verbose=0)
print('Test loss:', score[0])
print('Test accuracy:', score[1])

'''This is a reproduction of the IRNN experiment
with pixel-by-pixel sequential MNIST in
"A Simple Way to Initialize Recurrent Networks of Rectified Linear Units"
by Quoc V. Le, Navdeep Jaitly, Geoffrey E. Hinton

arxiv:1504.00941v2 [cs.NE] 7 Apr 2015
http://arxiv.org/pdf/1504.00941v2.pdf

Optimizer is replaced with RMSprop which yields more stable and steady
improvement.

Reaches 0.93 train/test accuracy after 900 epochs
(which roughly corresponds to 1687500 steps in the original paper.)
'''

from __future__ import print_function

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Activation
from keras.layers import SimpleRNN
from keras import initializers
from keras.optimizers import RMSprop

batch_size = 32
num_classes = 10
epochs = 200
hidden_units = 100

learning_rate = 1e-6
clip_norm = 1.0

# the data, split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

x_train = x_train.reshape(x_train.shape[0], -1, 1)
x_test = x_test.reshape(x_test.shape[0], -1, 1)
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

print('Evaluate IRNN...')
model = Sequential()
model.add(SimpleRNN(hidden_units,
                    kernel_initializer=initializers.RandomNormal(stddev=0.001),
                    recurrent_initializer=initializers.Identity(gain=1.0),
                    activation='relu',
                    input_shape=x_train.shape[1:]))
model.add(Dense(num_classes))
model.add(Activation('softmax'))
rmsprop = RMSprop(learning_rate=learning_rate)
model.compile(loss='categorical_crossentropy',
              optimizer=rmsprop,
              metrics=['accuracy'])

model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          verbose=1,
          validation_data=(x_test, y_test))

scores = model.evaluate(x_test, y_test, verbose=0)
print('IRNN test score:', scores[0])
print('IRNN test accuracy:', scores[1])

'''Trains a simple convnet on the MNIST dataset.

Gets to 99.25% test accuracy after 12 epochs
(there is still a lot of margin for parameter tuning).
16 seconds per epoch on a GRID K520 GPU.
'''

from __future__ import print_function
import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K

batch_size = 128
num_classes = 10
epochs = 12

# input image dimensions
img_rows, img_cols = 28, 28

# the data, split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

if K.image_data_format() == 'channels_first':
    x_train = x_train.reshape(x_train.shape[0], 1, img_rows, img_cols)
    x_test = x_test.reshape(x_test.shape[0], 1, img_rows, img_cols)
    input_shape = (1, img_rows, img_cols)
else:
    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)
    input_shape = (img_rows, img_cols, 1)

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

model = Sequential()
model.add(Conv2D(32, kernel_size=(3, 3),
                 activation='relu',
                 input_shape=input_shape))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes, activation='softmax'))

model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer=keras.optimizers.Adadelta(),
              metrics=['accuracy'])

model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          verbose=1,
          validation_data=(x_test, y_test))
score = model.evaluate(x_test, y_test, verbose=0)
print('Test loss:', score[0])
print('Test accuracy:', score[1])

'''
#Example script to generate text from Nietzsche's writings.

At least 20 epochs are required before the generated text
starts sounding coherent.

It is recommended to run this script on GPU, as recurrent
networks are quite computationally intensive.

If you try this script on new data, make sure your corpus
has at least ~100k characters. ~1M is better.
'''

from __future__ import print_function
from keras.callbacks import LambdaCallback
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.optimizers import RMSprop
from keras.utils.data_utils import get_file
import numpy as np
import random
import sys
import io

path = get_file(
    'nietzsche.txt',
    origin='https://s3.amazonaws.com/text-datasets/nietzsche.txt')
with io.open(path, encoding='utf-8') as f:
    text = f.read().lower()
print('corpus length:', len(text))

chars = sorted(list(set(text)))
print('total chars:', len(chars))
char_indices = dict((c, i) for i, c in enumerate(chars))
indices_char = dict((i, c) for i, c in enumerate(chars))

# cut the text in semi-redundant sequences of maxlen characters
maxlen = 40
step = 3
sentences = []
next_chars = []
for i in range(0, len(text) - maxlen, step):
    sentences.append(text[i: i + maxlen])
    next_chars.append(text[i + maxlen])
print('nb sequences:', len(sentences))

print('Vectorization...')
x = np.zeros((len(sentences), maxlen, len(chars)), dtype=np.bool)
y = np.zeros((len(sentences), len(chars)), dtype=np.bool)
for i, sentence in enumerate(sentences):
    for t, char in enumerate(sentence):
        x[i, t, char_indices[char]] = 1
    y[i, char_indices[next_chars[i]]] = 1


# build the model: a single LSTM
print('Build model...')
model = Sequential()
model.add(LSTM(128, input_shape=(maxlen, len(chars))))
model.add(Dense(len(chars), activation='softmax'))

optimizer = RMSprop(learning_rate=0.01)
model.compile(loss='categorical_crossentropy', optimizer=optimizer)


def sample(preds, temperature=1.0):
    # helper function to sample an index from a probability array
    preds = np.asarray(preds).astype('float64')
    preds = np.log(preds) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1, preds, 1)
    return np.argmax(probas)


def on_epoch_end(epoch, _):
    # Function invoked at end of each epoch. Prints generated text.
    print()
    print('----- Generating text after Epoch: %d' % epoch)

    start_index = random.randint(0, len(text) - maxlen - 1)
    for diversity in [0.2, 0.5, 1.0, 1.2]:
        print('----- diversity:', diversity)

        generated = ''
        sentence = text[start_index: start_index + maxlen]
        generated += sentence
        print('----- Generating with seed: "' + sentence + '"')
        sys.stdout.write(generated)

        for i in range(400):
            x_pred = np.zeros((1, maxlen, len(chars)))
            for t, char in enumerate(sentence):
                x_pred[0, t, char_indices[char]] = 1.

            preds = model.predict(x_pred, verbose=0)[0]
            next_index = sample(preds, diversity)
            next_char = indices_char[next_index]

            sentence = sentence[1:] + next_char

            sys.stdout.write(next_char)
            sys.stdout.flush()
        print()

print_callback = LambdaCallback(on_epoch_end=on_epoch_end)

model.fit(x, y,
          batch_size=128,
          epochs=60,
          callbacks=[print_callback])

'''Example of VAE on MNIST dataset using CNN

The VAE has a modular design. The encoder, decoder and VAE
are 3 models that share weights. After training the VAE model,
the encoder can be used to  generate latent vectors.
The decoder can be used to generate MNIST digits by sampling the
latent vector from a Gaussian distribution with mean=0 and std=1.

# Reference

[1] Kingma, Diederik P., and Max Welling.
"Auto-encoding variational bayes."
https://arxiv.org/abs/1312.6114
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from keras.layers import Dense, Input
from keras.layers import Conv2D, Flatten, Lambda
from keras.layers import Reshape, Conv2DTranspose
from keras.models import Model
from keras.datasets import mnist
from keras.losses import mse, binary_crossentropy
from keras.utils import plot_model
from keras import backend as K

import numpy as np
import matplotlib.pyplot as plt
import argparse
import os


# reparameterization trick
# instead of sampling from Q(z|X), sample eps = N(0,I)
# then z = z_mean + sqrt(var)*eps
def sampling(args):
    """Reparameterization trick by sampling fr an isotropic unit Gaussian.

    # Arguments
        args (tensor): mean and log of variance of Q(z|X)

    # Returns
        z (tensor): sampled latent vector
    """

    z_mean, z_log_var = args
    batch = K.shape(z_mean)[0]
    dim = K.int_shape(z_mean)[1]
    # by default, random_normal has mean=0 and std=1.0
    epsilon = K.random_normal(shape=(batch, dim))
    return z_mean + K.exp(0.5 * z_log_var) * epsilon


def plot_results(models,
                 data,
                 batch_size=128,
                 model_name="vae_mnist"):
    """Plots labels and MNIST digits as function of 2-dim latent vector

    # Arguments
        models (tuple): encoder and decoder models
        data (tuple): test data and label
        batch_size (int): prediction batch size
        model_name (string): which model is using this function
    """

    encoder, decoder = models
    x_test, y_test = data
    os.makedirs(model_name, exist_ok=True)

    filename = os.path.join(model_name, "vae_mean.png")
    # display a 2D plot of the digit classes in the latent space
    z_mean, _, _ = encoder.predict(x_test,
                                   batch_size=batch_size)
    plt.figure(figsize=(12, 10))
    plt.scatter(z_mean[:, 0], z_mean[:, 1], c=y_test)
    plt.colorbar()
    plt.xlabel("z[0]")
    plt.ylabel("z[1]")
    plt.savefig(filename)
    plt.show()

    filename = os.path.join(model_name, "digits_over_latent.png")
    # display a 30x30 2D manifold of digits
    n = 30
    digit_size = 28
    figure = np.zeros((digit_size * n, digit_size * n))
    # linearly spaced coordinates corresponding to the 2D plot
    # of digit classes in the latent space
    grid_x = np.linspace(-4, 4, n)
    grid_y = np.linspace(-4, 4, n)[::-1]

    for i, yi in enumerate(grid_y):
        for j, xi in enumerate(grid_x):
            z_sample = np.array([[xi, yi]])
            x_decoded = decoder.predict(z_sample)
            digit = x_decoded[0].reshape(digit_size, digit_size)
            figure[i * digit_size: (i + 1) * digit_size,
                   j * digit_size: (j + 1) * digit_size] = digit

    plt.figure(figsize=(10, 10))
    start_range = digit_size // 2
    end_range = n * digit_size + start_range + 1
    pixel_range = np.arange(start_range, end_range, digit_size)
    sample_range_x = np.round(grid_x, 1)
    sample_range_y = np.round(grid_y, 1)
    plt.xticks(pixel_range, sample_range_x)
    plt.yticks(pixel_range, sample_range_y)
    plt.xlabel("z[0]")
    plt.ylabel("z[1]")
    plt.imshow(figure, cmap='Greys_r')
    plt.savefig(filename)
    plt.show()


# MNIST dataset
(x_train, y_train), (x_test, y_test) = mnist.load_data()

image_size = x_train.shape[1]
x_train = np.reshape(x_train, [-1, image_size, image_size, 1])
x_test = np.reshape(x_test, [-1, image_size, image_size, 1])
x_train = x_train.astype('float32') / 255
x_test = x_test.astype('float32') / 255

# network parameters
input_shape = (image_size, image_size, 1)
batch_size = 128
kernel_size = 3
filters = 16
latent_dim = 2
epochs = 30

# VAE model = encoder + decoder
# build encoder model
inputs = Input(shape=input_shape, name='encoder_input')
x = inputs
for i in range(2):
    filters *= 2
    x = Conv2D(filters=filters,
               kernel_size=kernel_size,
               activation='relu',
               strides=2,
               padding='same')(x)

# shape info needed to build decoder model
shape = K.int_shape(x)

# generate latent vector Q(z|X)
x = Flatten()(x)
x = Dense(16, activation='relu')(x)
z_mean = Dense(latent_dim, name='z_mean')(x)
z_log_var = Dense(latent_dim, name='z_log_var')(x)

# use reparameterization trick to push the sampling out as input
# note that "output_shape" isn't necessary with the TensorFlow backend
z = Lambda(sampling, output_shape=(latent_dim,), name='z')([z_mean, z_log_var])

# instantiate encoder model
encoder = Model(inputs, [z_mean, z_log_var, z], name='encoder')
encoder.summary()
plot_model(encoder, to_file='vae_cnn_encoder.png', show_shapes=True)

# build decoder model
latent_inputs = Input(shape=(latent_dim,), name='z_sampling')
x = Dense(shape[1] * shape[2] * shape[3], activation='relu')(latent_inputs)
x = Reshape((shape[1], shape[2], shape[3]))(x)

for i in range(2):
    x = Conv2DTranspose(filters=filters,
                        kernel_size=kernel_size,
                        activation='relu',
                        strides=2,
                        padding='same')(x)
    filters //= 2

outputs = Conv2DTranspose(filters=1,
                          kernel_size=kernel_size,
                          activation='sigmoid',
                          padding='same',
                          name='decoder_output')(x)

# instantiate decoder model
decoder = Model(latent_inputs, outputs, name='decoder')
decoder.summary()
plot_model(decoder, to_file='vae_cnn_decoder.png', show_shapes=True)

# instantiate VAE model
outputs = decoder(encoder(inputs)[2])
vae = Model(inputs, outputs, name='vae')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    help_ = "Load h5 model trained weights"
    parser.add_argument("-w", "--weights", help=help_)
    help_ = "Use mse loss instead of binary cross entropy (default)"
    parser.add_argument("-m", "--mse", help=help_, action='store_true')
    args = parser.parse_args()
    models = (encoder, decoder)
    data = (x_test, y_test)

    # VAE loss = mse_loss or xent_loss + kl_loss
    if args.mse:
        reconstruction_loss = mse(K.flatten(inputs), K.flatten(outputs))
    else:
        reconstruction_loss = binary_crossentropy(K.flatten(inputs),
                                                  K.flatten(outputs))

    reconstruction_loss *= image_size * image_size
    kl_loss = 1 + z_log_var - K.square(z_mean) - K.exp(z_log_var)
    kl_loss = K.sum(kl_loss, axis=-1)
    kl_loss *= -0.5
    vae_loss = K.mean(reconstruction_loss + kl_loss)
    vae.add_loss(vae_loss)
    vae.compile(optimizer='rmsprop')
    vae.summary()
    plot_model(vae, to_file='vae_cnn.png', show_shapes=True)

    if args.weights:
        vae.load_weights(args.weights)
    else:
        # train the autoencoder
        vae.fit(x_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=(x_test, None))
        vae.save_weights('vae_cnn_mnist.h5')

    plot_results(models, data, batch_size=batch_size, model_name="vae_cnn")

'''
#Restore a character-level sequence to sequence model from to generate predictions.

This script loads the ```s2s.h5``` model saved by [lstm_seq2seq.py
](/examples/lstm_seq2seq/) and generates sequences from it. It assumes
that no changes have been made (for example: ```latent_dim``` is unchanged,
and the input data and model architecture are unchanged).

See [lstm_seq2seq.py](/examples/lstm_seq2seq/) for more details on the
model architecture and how it is trained.
'''
from __future__ import print_function

from keras.models import Model, load_model
from keras.layers import Input
import numpy as np

batch_size = 64  # Batch size for training.
epochs = 100  # Number of epochs to train for.
latent_dim = 256  # Latent dimensionality of the encoding space.
num_samples = 10000  # Number of samples to train on.
# Path to the data txt file on disk.
data_path = 'fra-eng/fra.txt'

# Vectorize the data.  We use the same approach as the training script.
# NOTE: the data must be identical, in order for the character -> integer
# mappings to be consistent.
# We omit encoding target_texts since they are not needed.
input_texts = []
target_texts = []
input_characters = set()
target_characters = set()
with open(data_path, 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')
for line in lines[: min(num_samples, len(lines) - 1)]:
    input_text, target_text, _ = line.split('\t')
    # We use "tab" as the "start sequence" character
    # for the targets, and "\n" as "end sequence" character.
    target_text = '\t' + target_text + '\n'
    input_texts.append(input_text)
    target_texts.append(target_text)
    for char in input_text:
        if char not in input_characters:
            input_characters.add(char)
    for char in target_text:
        if char not in target_characters:
            target_characters.add(char)

input_characters = sorted(list(input_characters))
target_characters = sorted(list(target_characters))
num_encoder_tokens = len(input_characters)
num_decoder_tokens = len(target_characters)
max_encoder_seq_length = max([len(txt) for txt in input_texts])
max_decoder_seq_length = max([len(txt) for txt in target_texts])

print('Number of samples:', len(input_texts))
print('Number of unique input tokens:', num_encoder_tokens)
print('Number of unique output tokens:', num_decoder_tokens)
print('Max sequence length for inputs:', max_encoder_seq_length)
print('Max sequence length for outputs:', max_decoder_seq_length)

input_token_index = dict(
    [(char, i) for i, char in enumerate(input_characters)])
target_token_index = dict(
    [(char, i) for i, char in enumerate(target_characters)])

encoder_input_data = np.zeros(
    (len(input_texts), max_encoder_seq_length, num_encoder_tokens),
    dtype='float32')

for i, input_text in enumerate(input_texts):
    for t, char in enumerate(input_text):
        encoder_input_data[i, t, input_token_index[char]] = 1.

# Restore the model and construct the encoder and decoder.
model = load_model('s2s.h5')

encoder_inputs = model.input[0]   # input_1
encoder_outputs, state_h_enc, state_c_enc = model.layers[2].output   # lstm_1
encoder_states = [state_h_enc, state_c_enc]
encoder_model = Model(encoder_inputs, encoder_states)

decoder_inputs = model.input[1]   # input_2
decoder_state_input_h = Input(shape=(latent_dim,), name='input_3')
decoder_state_input_c = Input(shape=(latent_dim,), name='input_4')
decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
decoder_lstm = model.layers[3]
decoder_outputs, state_h_dec, state_c_dec = decoder_lstm(
    decoder_inputs, initial_state=decoder_states_inputs)
decoder_states = [state_h_dec, state_c_dec]
decoder_dense = model.layers[4]
decoder_outputs = decoder_dense(decoder_outputs)
decoder_model = Model(
    [decoder_inputs] + decoder_states_inputs,
    [decoder_outputs] + decoder_states)

# Reverse-lookup token index to decode sequences back to
# something readable.
reverse_input_char_index = dict(
    (i, char) for char, i in input_token_index.items())
reverse_target_char_index = dict(
    (i, char) for char, i in target_token_index.items())


# Decodes an input sequence.  Future work should support beam search.
def decode_sequence(input_seq):
    # Encode the input as state vectors.
    states_value = encoder_model.predict(input_seq)

    # Generate empty target sequence of length 1.
    target_seq = np.zeros((1, 1, num_decoder_tokens))
    # Populate the first character of target sequence with the start character.
    target_seq[0, 0, target_token_index['\t']] = 1.

    # Sampling loop for a batch of sequences
    # (to simplify, here we assume a batch of size 1).
    stop_condition = False
    decoded_sentence = ''
    while not stop_condition:
        output_tokens, h, c = decoder_model.predict(
            [target_seq] + states_value)

        # Sample a token
        sampled_token_index = np.argmax(output_tokens[0, -1, :])
        sampled_char = reverse_target_char_index[sampled_token_index]
        decoded_sentence += sampled_char

        # Exit condition: either hit max length
        # or find stop character.
        if (sampled_char == '\n' or
           len(decoded_sentence) > max_decoder_seq_length):
            stop_condition = True

        # Update the target sequence (of length 1).
        target_seq = np.zeros((1, 1, num_decoder_tokens))
        target_seq[0, 0, sampled_token_index] = 1.

        # Update states
        states_value = [h, c]

    return decoded_sentence


for seq_index in range(100):
    # Take one sequence (part of the training set)
    # for trying out decoding.
    input_seq = encoder_input_data[seq_index: seq_index + 1]
    decoded_sentence = decode_sequence(input_seq)
    print('-')
    print('Input sentence:', input_texts[seq_index])
    print('Decoded sentence:', decoded_sentence)

'''
#This example demonstrates the use of fasttext for text classification

Based on Joulin et al's paper:

[Bags of Tricks for Efficient Text Classification
](https://arxiv.org/abs/1607.01759)

Results on IMDB datasets with uni and bi-gram embeddings:

Embedding|Accuracy, 5 epochs|Speed (s/epoch)|Hardware
:--------|-----------------:|----:|:-------
Uni-gram |            0.8813|    8|i7 CPU
Bi-gram  |            0.9056|    2|GTx 980M GPU

'''

from __future__ import print_function
import numpy as np

from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Embedding
from keras.layers import GlobalAveragePooling1D
from keras.datasets import imdb


def create_ngram_set(input_list, ngram_value=2):
    """
    Extract a set of n-grams from a list of integers.

    >>> create_ngram_set([1, 4, 9, 4, 1, 4], ngram_value=2)
    {(4, 9), (4, 1), (1, 4), (9, 4)}

    >>> create_ngram_set([1, 4, 9, 4, 1, 4], ngram_value=3)
    [(1, 4, 9), (4, 9, 4), (9, 4, 1), (4, 1, 4)]
    """
    return set(zip(*[input_list[i:] for i in range(ngram_value)]))


def add_ngram(sequences, token_indice, ngram_range=2):
    """
    Augment the input list of list (sequences) by appending n-grams values.

    Example: adding bi-gram
    >>> sequences = [[1, 3, 4, 5], [1, 3, 7, 9, 2]]
    >>> token_indice = {(1, 3): 1337, (9, 2): 42, (4, 5): 2017}
    >>> add_ngram(sequences, token_indice, ngram_range=2)
    [[1, 3, 4, 5, 1337, 2017], [1, 3, 7, 9, 2, 1337, 42]]

    Example: adding tri-gram
    >>> sequences = [[1, 3, 4, 5], [1, 3, 7, 9, 2]]
    >>> token_indice = {(1, 3): 1337, (9, 2): 42, (4, 5): 2017, (7, 9, 2): 2018}
    >>> add_ngram(sequences, token_indice, ngram_range=3)
    [[1, 3, 4, 5, 1337, 2017], [1, 3, 7, 9, 2, 1337, 42, 2018]]
    """
    new_sequences = []
    for input_list in sequences:
        new_list = input_list[:]
        for ngram_value in range(2, ngram_range + 1):
            for i in range(len(new_list) - ngram_value + 1):
                ngram = tuple(new_list[i:i + ngram_value])
                if ngram in token_indice:
                    new_list.append(token_indice[ngram])
        new_sequences.append(new_list)

    return new_sequences

# Set parameters:
# ngram_range = 2 will add bi-grams features
ngram_range = 1
max_features = 20000
maxlen = 400
batch_size = 32
embedding_dims = 50
epochs = 5

print('Loading data...')
(x_train, y_train), (x_test, y_test) = imdb.load_data(num_words=max_features)
print(len(x_train), 'train sequences')
print(len(x_test), 'test sequences')
print('Average train sequence length: {}'.format(
    np.mean(list(map(len, x_train)), dtype=int)))
print('Average test sequence length: {}'.format(
    np.mean(list(map(len, x_test)), dtype=int)))

if ngram_range > 1:
    print('Adding {}-gram features'.format(ngram_range))
    # Create set of unique n-gram from the training set.
    ngram_set = set()
    for input_list in x_train:
        for i in range(2, ngram_range + 1):
            set_of_ngram = create_ngram_set(input_list, ngram_value=i)
            ngram_set.update(set_of_ngram)

    # Dictionary mapping n-gram token to a unique integer.
    # Integer values are greater than max_features in order
    # to avoid collision with existing features.
    start_index = max_features + 1
    token_indice = {v: k + start_index for k, v in enumerate(ngram_set)}
    indice_token = {token_indice[k]: k for k in token_indice}

    # max_features is the highest integer that could be found in the dataset.
    max_features = np.max(list(indice_token.keys())) + 1

    # Augmenting x_train and x_test with n-grams features
    x_train = add_ngram(x_train, token_indice, ngram_range)
    x_test = add_ngram(x_test, token_indice, ngram_range)
    print('Average train sequence length: {}'.format(
        np.mean(list(map(len, x_train)), dtype=int)))
    print('Average test sequence length: {}'.format(
        np.mean(list(map(len, x_test)), dtype=int)))

print('Pad sequences (samples x time)')
x_train = sequence.pad_sequences(x_train, maxlen=maxlen)
x_test = sequence.pad_sequences(x_test, maxlen=maxlen)
print('x_train shape:', x_train.shape)
print('x_test shape:', x_test.shape)

print('Build model...')
model = Sequential()

# we start off with an efficient embedding layer which maps
# our vocab indices into embedding_dims dimensions
model.add(Embedding(max_features,
                    embedding_dims,
                    input_length=maxlen))

# we add a GlobalAveragePooling1D, which will average the embeddings
# of all words in the document
model.add(GlobalAveragePooling1D())

# We project onto a single unit output layer, and squash it with a sigmoid:
model.add(Dense(1, activation='sigmoid'))

model.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          validation_data=(x_test, y_test))

# -*- coding: utf-8 -*-

import numpy as np
import argparse
import cv2
import matplotlib.pyplot as plt

from keras.models import Model

import keras.applications.resnet50 as resnet
from keras.layers import UpSampling2D, Conv2D

# Set an appropriate image file
parser = argparse.ArgumentParser(description='Class activation maps with Keras.')
parser.add_argument('input_image', metavar='base', type=str,
                    help='Path to the image to use.')
args = parser.parse_args()
input_image = args.input_image


################################################################
# The following parameters can be changed to other models
# that use global average pooling.
# e.g.) InceptionResnetV2 / NASNetLarge
NETWORK_INPUT_SIZE = 224
MODEL_CLASS = resnet.ResNet50
PREPROCESS_FN = resnet.preprocess_input
LAST_CONV_LAYER = 'activation_49'
PRED_LAYER = 'fc1000'
################################################################

# number of imagenet classes
N_CLASSES = 1000


def load_img(fname, input_size, preprocess_fn):
    original_img = cv2.imread(fname)[:, :, ::-1]
    original_size = (original_img.shape[1], original_img.shape[0])
    img = cv2.resize(original_img, (input_size, input_size))
    imgs = np.expand_dims(preprocess_fn(img), axis=0)
    return imgs, original_img, original_size


def get_cam_model(model_class,
                  input_size=224,
                  last_conv_layer='activation_49',
                  pred_layer='fc1000'):
    model = model_class(input_shape=(input_size, input_size, 3))

    final_params = model.get_layer(pred_layer).get_weights()
    final_params = (final_params[0].reshape(
        1, 1, -1, N_CLASSES), final_params[1])

    last_conv_output = model.get_layer(last_conv_layer).output
    x = UpSampling2D(size=(32, 32), interpolation='bilinear')(
        last_conv_output)
    x = Conv2D(filters=N_CLASSES, kernel_size=(
        1, 1), name='predictions_2')(x)

    cam_model = Model(inputs=model.input,
                      outputs=[model.output, x])
    cam_model.get_layer('predictions_2').set_weights(final_params)
    return cam_model


def postprocess(preds, cams, top_k=1):
    idxes = np.argsort(preds[0])[-top_k:]
    class_activation_map = np.zeros_like(cams[0, :, :, 0])
    for i in idxes:
        class_activation_map += cams[0, :, :, i]
    return class_activation_map


# 1. load image
imgs, original_img, original_size = load_img(input_image,
                                             input_size=NETWORK_INPUT_SIZE,
                                             preprocess_fn=resnet.preprocess_input)

# 2. prediction
model = get_cam_model(resnet.ResNet50,
                      NETWORK_INPUT_SIZE,
                      LAST_CONV_LAYER,
                      PRED_LAYER)
preds, cams = model.predict(imgs)

# 4. post processing
class_activation_map = postprocess(preds, cams)

# 5. plot image+cam to original size
plt.imshow(original_img, alpha=0.5)
plt.imshow(cv2.resize(class_activation_map,
                      original_size), cmap='jet', alpha=0.5)
plt.show()

'''
#This example demonstrates the use of Convolution1D for text classification.

Gets to 0.89 test accuracy after 2 epochs. </br>
90s/epoch on Intel i5 2.4Ghz CPU. </br>
10s/epoch on Tesla K40 GPU.
'''
from __future__ import print_function

from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from keras.layers import Embedding
from keras.layers import Conv1D, GlobalMaxPooling1D
from keras.datasets import imdb

# set parameters:
max_features = 5000
maxlen = 400
batch_size = 32
embedding_dims = 50
filters = 250
kernel_size = 3
hidden_dims = 250
epochs = 2

print('Loading data...')
(x_train, y_train), (x_test, y_test) = imdb.load_data(num_words=max_features)
print(len(x_train), 'train sequences')
print(len(x_test), 'test sequences')

print('Pad sequences (samples x time)')
x_train = sequence.pad_sequences(x_train, maxlen=maxlen)
x_test = sequence.pad_sequences(x_test, maxlen=maxlen)
print('x_train shape:', x_train.shape)
print('x_test shape:', x_test.shape)

print('Build model...')
model = Sequential()

# we start off with an efficient embedding layer which maps
# our vocab indices into embedding_dims dimensions
model.add(Embedding(max_features,
                    embedding_dims,
                    input_length=maxlen))
model.add(Dropout(0.2))

# we add a Convolution1D, which will learn filters
# word group filters of size filter_length:
model.add(Conv1D(filters,
                 kernel_size,
                 padding='valid',
                 activation='relu',
                 strides=1))
# we use max pooling:
model.add(GlobalMaxPooling1D())

# We add a vanilla hidden layer:
model.add(Dense(hidden_dims))
model.add(Dropout(0.2))
model.add(Activation('relu'))

# We project onto a single unit output layer, and squash it with a sigmoid:
model.add(Dense(1))
model.add(Activation('sigmoid'))

model.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])
model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          validation_data=(x_test, y_test))

'''
#Trains an LSTM model on the IMDB sentiment classification task.

The dataset is actually too small for LSTM to be of any advantage
compared to simpler, much faster methods such as TF-IDF + LogReg.

**Notes**

- RNNs are tricky. Choice of batch size is important,
choice of loss and optimizer is critical, etc.
Some configurations won't converge.

- LSTM loss decrease patterns during training can be quite different
from what you see with CNNs/MLPs/etc.

'''
from __future__ import print_function

from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import Dense, Embedding
from keras.layers import LSTM
from keras.datasets import imdb

max_features = 20000
# cut texts after this number of words (among top max_features most common words)
maxlen = 80
batch_size = 32

print('Loading data...')
(x_train, y_train), (x_test, y_test) = imdb.load_data(num_words=max_features)
print(len(x_train), 'train sequences')
print(len(x_test), 'test sequences')

print('Pad sequences (samples x time)')
x_train = sequence.pad_sequences(x_train, maxlen=maxlen)
x_test = sequence.pad_sequences(x_test, maxlen=maxlen)
print('x_train shape:', x_train.shape)
print('x_test shape:', x_test.shape)

print('Build model...')
model = Sequential()
model.add(Embedding(max_features, 128))
model.add(LSTM(128, dropout=0.2, recurrent_dropout=0.2))
model.add(Dense(1, activation='sigmoid'))

# try using different optimizers and different optimizer configs
model.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

print('Train...')
model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=15,
          validation_data=(x_test, y_test))
score, acc = model.evaluate(x_test, y_test,
                            batch_size=batch_size)
print('Test score:', score)
print('Test accuracy:', acc)

'''
#Trains a Bidirectional LSTM on the IMDB sentiment classification task.

Output after 4 epochs on CPU: ~0.8146
Time per epoch on CPU (Core i7): ~150s.
'''

from __future__ import print_function
import numpy as np

from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import Dense, Dropout, Embedding, LSTM, Bidirectional
from keras.datasets import imdb


max_features = 20000
# cut texts after this number of words
# (among top max_features most common words)
maxlen = 100
batch_size = 32

print('Loading data...')
(x_train, y_train), (x_test, y_test) = imdb.load_data(num_words=max_features)
print(len(x_train), 'train sequences')
print(len(x_test), 'test sequences')

print('Pad sequences (samples x time)')
x_train = sequence.pad_sequences(x_train, maxlen=maxlen)
x_test = sequence.pad_sequences(x_test, maxlen=maxlen)
print('x_train shape:', x_train.shape)
print('x_test shape:', x_test.shape)
y_train = np.array(y_train)
y_test = np.array(y_test)

model = Sequential()
model.add(Embedding(max_features, 128, input_length=maxlen))
model.add(Bidirectional(LSTM(64)))
model.add(Dropout(0.5))
model.add(Dense(1, activation='sigmoid'))

# try using different optimizers and different optimizer configs
model.compile('adam', 'binary_crossentropy', metrics=['accuracy'])

print('Train...')
model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=4,
          validation_data=[x_test, y_test])

'''Example of how to use sklearn wrapper

Builds simple CNN models on MNIST and uses sklearn's GridSearchCV to find best model
'''

from __future__ import print_function

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.wrappers.scikit_learn import KerasClassifier
from keras import backend as K
from sklearn.model_selection import GridSearchCV


num_classes = 10

# input image dimensions
img_rows, img_cols = 28, 28

# load training data and do basic data normalization
(x_train, y_train), (x_test, y_test) = mnist.load_data()

if K.image_data_format() == 'channels_first':
    x_train = x_train.reshape(x_train.shape[0], 1, img_rows, img_cols)
    x_test = x_test.reshape(x_test.shape[0], 1, img_rows, img_cols)
    input_shape = (1, img_rows, img_cols)
else:
    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)
    input_shape = (img_rows, img_cols, 1)

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255

# convert class vectors to binary class matrices
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)


def make_model(dense_layer_sizes, filters, kernel_size, pool_size):
    '''Creates model comprised of 2 convolutional layers followed by dense layers

    dense_layer_sizes: List of layer sizes.
        This list has one number for each layer
    filters: Number of convolutional filters in each convolutional layer
    kernel_size: Convolutional kernel size
    pool_size: Size of pooling area for max pooling
    '''

    model = Sequential()
    model.add(Conv2D(filters, kernel_size,
                     padding='valid',
                     input_shape=input_shape))
    model.add(Activation('relu'))
    model.add(Conv2D(filters, kernel_size))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size=pool_size))
    model.add(Dropout(0.25))

    model.add(Flatten())
    for layer_size in dense_layer_sizes:
        model.add(Dense(layer_size))
        model.add(Activation('relu'))
    model.add(Dropout(0.5))
    model.add(Dense(num_classes))
    model.add(Activation('softmax'))

    model.compile(loss='categorical_crossentropy',
                  optimizer='adadelta',
                  metrics=['accuracy'])
    return model


dense_size_candidates = [[32], [64], [32, 32], [64, 64]]
my_classifier = KerasClassifier(make_model, batch_size=32)
validator = GridSearchCV(my_classifier,
                         param_grid={'dense_layer_sizes': dense_size_candidates,
                                     # epochs is avail for tuning even when not
                                     # an argument to model building function
                                     'epochs': [3, 6],
                                     'filters': [8],
                                     'kernel_size': [3],
                                     'pool_size': [2]},
                         scoring='neg_log_loss',
                         n_jobs=1)
validator.fit(x_train, y_train)

print('The parameters of the best model are: ')
print(validator.best_params_)

# validator.best_estimator_ returns sklearn-wrapped version of best model.
# validator.best_estimator_.model returns the (unwrapped) keras model
best_model = validator.best_estimator_.model
metric_names = best_model.metrics_names
metric_values = best_model.evaluate(x_test, y_test)
for metric, value in zip(metric_names, metric_values):
    print(metric, ': ', value)

"""Example of using Hierarchical RNN (HRNN) to classify MNIST digits.

HRNNs can learn across multiple levels
of temporal hierarchy over a complex sequence.
Usually, the first recurrent layer of an HRNN
encodes a sentence (e.g. of word vectors)
into a  sentence vector.
The second recurrent layer then encodes a sequence of
such vectors (encoded by the first layer) into a document vector.
This document vector is considered to preserve both
the word-level and sentence-level structure of the context.

# References

- [A Hierarchical Neural Autoencoder for Paragraphs and Documents]
    (https://arxiv.org/abs/1506.01057)
    Encodes paragraphs and documents with HRNN.
    Results have shown that HRNN outperforms standard
    RNNs and may play some role in more sophisticated generation tasks like
    summarization or question answering.
- [Hierarchical recurrent neural network for skeleton based action recognition]
    (http://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=7298714)
    Achieved state-of-the-art results on
    skeleton based action recognition with 3 levels
    of bidirectional HRNN combined with fully connected layers.

In the below MNIST example the first LSTM layer first encodes every
column of pixels of shape (28, 1) to a column vector of shape (128,).
The second LSTM layer encodes then these 28 column vectors of shape (28, 128)
to a image vector representing the whole image.
A final Dense layer is added for prediction.

After 5 epochs: train acc: 0.9858, val acc: 0.9864
"""
from __future__ import print_function

import keras
from keras.datasets import mnist
from keras.models import Model
from keras.layers import Input, Dense, TimeDistributed
from keras.layers import LSTM

# Training parameters.
batch_size = 32
num_classes = 10
epochs = 5

# Embedding dimensions.
row_hidden = 128
col_hidden = 128

# The data, split between train and test sets.
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# Reshapes data to 4D for Hierarchical RNN.
x_train = x_train.reshape(x_train.shape[0], 28, 28, 1)
x_test = x_test.reshape(x_test.shape[0], 28, 28, 1)
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# Converts class vectors to binary class matrices.
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

row, col, pixel = x_train.shape[1:]

# 4D input.
x = Input(shape=(row, col, pixel))

# Encodes a row of pixels using TimeDistributed Wrapper.
encoded_rows = TimeDistributed(LSTM(row_hidden))(x)

# Encodes columns of encoded rows.
encoded_columns = LSTM(col_hidden)(encoded_rows)

# Final predictions and model.
prediction = Dense(num_classes, activation='softmax')(encoded_columns)
model = Model(x, prediction)
model.compile(loss='categorical_crossentropy',
              optimizer='rmsprop',
              metrics=['accuracy'])

# Training.
model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          verbose=1,
          validation_data=(x_test, y_test))

# Evaluation.
scores = model.evaluate(x_test, y_test, verbose=0)
print('Test loss:', scores[0])
print('Test accuracy:', scores[1])

'''Neural doodle with Keras

# Script Usage

## Arguments
```
--nlabels:              # of regions (colors) in mask images
--style-image:          image to learn style from
--style-mask:           semantic labels for style image
--target-mask:          semantic labels for target image (your doodle)
--content-image:        optional image to learn content from
--target-image-prefix:  path prefix for generated target images
```

## Example 1: doodle using a style image, style mask
and target mask.
```
python neural_doodle.py --nlabels 4 --style-image Monet/style.png \
--style-mask Monet/style_mask.png --target-mask Monet/target_mask.png \
--target-image-prefix generated/monet
```

## Example 2: doodle using a style image, style mask,
target mask and an optional content image.
```
python neural_doodle.py --nlabels 4 --style-image Renoir/style.png \
--style-mask Renoir/style_mask.png --target-mask Renoir/target_mask.png \
--content-image Renoir/creek.jpg \
--target-image-prefix generated/renoir
```

# References

- [Dmitry Ulyanov's blog on fast-neural-doodle]
    (http://dmitryulyanov.github.io/feed-forward-neural-doodle/)
- [Torch code for fast-neural-doodle]
    (https://github.com/DmitryUlyanov/fast-neural-doodle)
- [Torch code for online-neural-doodle]
    (https://github.com/DmitryUlyanov/online-neural-doodle)
- [Paper Texture Networks: Feed-forward Synthesis of Textures and Stylized Images]
    (http://arxiv.org/abs/1603.03417)
- [Discussion on parameter tuning]
    (https://github.com/keras-team/keras/issues/3705)

# Resources

Example images can be downloaded from
https://github.com/DmitryUlyanov/fast-neural-doodle/tree/master/data
'''
from __future__ import print_function
import time
import argparse
import numpy as np
from scipy.optimize import fmin_l_bfgs_b

from keras import backend as K
from keras.layers import Input, AveragePooling2D
from keras.models import Model
from keras.preprocessing.image import load_img, save_img, img_to_array
from keras.applications import vgg19

# Command line arguments
parser = argparse.ArgumentParser(description='Keras neural doodle example')
parser.add_argument('--nlabels', type=int,
                    help='number of semantic labels'
                    ' (regions in differnet colors)'
                    ' in style_mask/target_mask')
parser.add_argument('--style-image', type=str,
                    help='path to image to learn style from')
parser.add_argument('--style-mask', type=str,
                    help='path to semantic mask of style image')
parser.add_argument('--target-mask', type=str,
                    help='path to semantic mask of target image')
parser.add_argument('--content-image', type=str, default=None,
                    help='path to optional content image')
parser.add_argument('--target-image-prefix', type=str,
                    help='path prefix for generated results')
args = parser.parse_args()

style_img_path = args.style_image
style_mask_path = args.style_mask
target_mask_path = args.target_mask
content_img_path = args.content_image
target_img_prefix = args.target_image_prefix
use_content_img = content_img_path is not None

num_labels = args.nlabels
num_colors = 3  # RGB
# determine image sizes based on target_mask
ref_img = img_to_array(load_img(target_mask_path))
img_nrows, img_ncols = ref_img.shape[:2]

num_iterations = 50

total_variation_weight = 50.
style_weight = 1.
content_weight = 0.1 if use_content_img else 0

content_feature_layers = ['block5_conv2']
# To get better generation qualities, use more conv layers for style features
style_feature_layers = ['block1_conv1', 'block2_conv1', 'block3_conv1',
                        'block4_conv1', 'block5_conv1']


# helper functions for reading/processing images
def preprocess_image(image_path):
    img = load_img(image_path, target_size=(img_nrows, img_ncols))
    img = img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = vgg19.preprocess_input(img)
    return img


def deprocess_image(x):
    if K.image_data_format() == 'channels_first':
        x = x.reshape((3, img_nrows, img_ncols))
        x = x.transpose((1, 2, 0))
    else:
        x = x.reshape((img_nrows, img_ncols, 3))
    # Remove zero-center by mean pixel
    x[:, :, 0] += 103.939
    x[:, :, 1] += 116.779
    x[:, :, 2] += 123.68
    # 'BGR'->'RGB'
    x = x[:, :, ::-1]
    x = np.clip(x, 0, 255).astype('uint8')
    return x


def kmeans(xs, k):
    assert xs.ndim == 2
    try:
        from sklearn.cluster import k_means
        _, labels, _ = k_means(xs.astype('float64'), k)
    except ImportError:
        from scipy.cluster.vq import kmeans2
        _, labels = kmeans2(xs, k, missing='raise')
    return labels


def load_mask_labels():
    '''Load both target and style masks.
    A mask image (nr x nc) with m labels/colors will be loaded
    as a 4D boolean tensor:
        (1, m, nr, nc) for 'channels_first' or (1, nr, nc, m) for 'channels_last'
    '''
    target_mask_img = load_img(target_mask_path,
                               target_size=(img_nrows, img_ncols))
    target_mask_img = img_to_array(target_mask_img)
    style_mask_img = load_img(style_mask_path,
                              target_size=(img_nrows, img_ncols))
    style_mask_img = img_to_array(style_mask_img)
    if K.image_data_format() == 'channels_first':
        mask_vecs = np.vstack([style_mask_img.reshape((3, -1)).T,
                               target_mask_img.reshape((3, -1)).T])
    else:
        mask_vecs = np.vstack([style_mask_img.reshape((-1, 3)),
                               target_mask_img.reshape((-1, 3))])

    labels = kmeans(mask_vecs, num_labels)
    style_mask_label = labels[:img_nrows *
                              img_ncols].reshape((img_nrows, img_ncols))
    target_mask_label = labels[img_nrows *
                               img_ncols:].reshape((img_nrows, img_ncols))

    stack_axis = 0 if K.image_data_format() == 'channels_first' else -1
    style_mask = np.stack([style_mask_label == r for r in range(num_labels)],
                          axis=stack_axis)
    target_mask = np.stack([target_mask_label == r for r in range(num_labels)],
                           axis=stack_axis)

    return (np.expand_dims(style_mask, axis=0),
            np.expand_dims(target_mask, axis=0))


# Create tensor variables for images
if K.image_data_format() == 'channels_first':
    shape = (1, num_colors, img_nrows, img_ncols)
else:
    shape = (1, img_nrows, img_ncols, num_colors)

style_image = K.variable(preprocess_image(style_img_path))
target_image = K.placeholder(shape=shape)
if use_content_img:
    content_image = K.variable(preprocess_image(content_img_path))
else:
    content_image = K.zeros(shape=shape)

images = K.concatenate([style_image, target_image, content_image], axis=0)

# Create tensor variables for masks
raw_style_mask, raw_target_mask = load_mask_labels()
style_mask = K.variable(raw_style_mask.astype('float32'))
target_mask = K.variable(raw_target_mask.astype('float32'))
masks = K.concatenate([style_mask, target_mask], axis=0)

# index constants for images and tasks variables
STYLE, TARGET, CONTENT = 0, 1, 2

# Build image model, mask model and use layer outputs as features
# image model as VGG19
image_model = vgg19.VGG19(include_top=False, input_tensor=images)

# mask model as a series of pooling
mask_input = Input(tensor=masks, shape=(None, None, None), name='mask_input')
x = mask_input
for layer in image_model.layers[1:]:
    name = 'mask_%s' % layer.name
    if 'conv' in layer.name:
        x = AveragePooling2D((3, 3), padding='same', strides=(
            1, 1), name=name)(x)
    elif 'pool' in layer.name:
        x = AveragePooling2D((2, 2), name=name)(x)
mask_model = Model(mask_input, x)

# Collect features from image_model and task_model
image_features = {}
mask_features = {}
for img_layer, mask_layer in zip(image_model.layers, mask_model.layers):
    if 'conv' in img_layer.name:
        assert 'mask_' + img_layer.name == mask_layer.name
        layer_name = img_layer.name
        img_feat, mask_feat = img_layer.output, mask_layer.output
        image_features[layer_name] = img_feat
        mask_features[layer_name] = mask_feat


# Define loss functions
def gram_matrix(x):
    assert K.ndim(x) == 3
    features = K.batch_flatten(x)
    gram = K.dot(features, K.transpose(features))
    return gram


def region_style_loss(style_image, target_image, style_mask, target_mask):
    '''Calculate style loss between style_image and target_image,
    for one common region specified by their (boolean) masks
    '''
    assert 3 == K.ndim(style_image) == K.ndim(target_image)
    assert 2 == K.ndim(style_mask) == K.ndim(target_mask)
    if K.image_data_format() == 'channels_first':
        masked_style = style_image * style_mask
        masked_target = target_image * target_mask
        num_channels = K.shape(style_image)[0]
    else:
        masked_style = K.permute_dimensions(
            style_image, (2, 0, 1)) * style_mask
        masked_target = K.permute_dimensions(
            target_image, (2, 0, 1)) * target_mask
        num_channels = K.shape(style_image)[-1]
    num_channels = K.cast(num_channels, dtype='float32')
    s = gram_matrix(masked_style) / K.mean(style_mask) / num_channels
    c = gram_matrix(masked_target) / K.mean(target_mask) / num_channels
    return K.mean(K.square(s - c))


def style_loss(style_image, target_image, style_masks, target_masks):
    '''Calculate style loss between style_image and target_image,
    in all regions.
    '''
    assert 3 == K.ndim(style_image) == K.ndim(target_image)
    assert 3 == K.ndim(style_masks) == K.ndim(target_masks)
    loss = K.variable(0)
    for i in range(num_labels):
        if K.image_data_format() == 'channels_first':
            style_mask = style_masks[i, :, :]
            target_mask = target_masks[i, :, :]
        else:
            style_mask = style_masks[:, :, i]
            target_mask = target_masks[:, :, i]
        loss = loss + region_style_loss(style_image,
                                        target_image,
                                        style_mask,
                                        target_mask)
    return loss


def content_loss(content_image, target_image):
    return K.sum(K.square(target_image - content_image))


def total_variation_loss(x):
    assert 4 == K.ndim(x)
    if K.image_data_format() == 'channels_first':
        a = K.square(x[:, :, :img_nrows - 1, :img_ncols - 1] -
                     x[:, :, 1:, :img_ncols - 1])
        b = K.square(x[:, :, :img_nrows - 1, :img_ncols - 1] -
                     x[:, :, :img_nrows - 1, 1:])
    else:
        a = K.square(x[:, :img_nrows - 1, :img_ncols - 1, :] -
                     x[:, 1:, :img_ncols - 1, :])
        b = K.square(x[:, :img_nrows - 1, :img_ncols - 1, :] -
                     x[:, :img_nrows - 1, 1:, :])
    return K.sum(K.pow(a + b, 1.25))


# Overall loss is the weighted sum of content_loss, style_loss and tv_loss
# Each individual loss uses features from image/mask models.
loss = K.variable(0)
for layer in content_feature_layers:
    content_feat = image_features[layer][CONTENT, :, :, :]
    target_feat = image_features[layer][TARGET, :, :, :]
    loss = loss + content_weight * content_loss(content_feat, target_feat)

for layer in style_feature_layers:
    style_feat = image_features[layer][STYLE, :, :, :]
    target_feat = image_features[layer][TARGET, :, :, :]
    style_masks = mask_features[layer][STYLE, :, :, :]
    target_masks = mask_features[layer][TARGET, :, :, :]
    sl = style_loss(style_feat, target_feat, style_masks, target_masks)
    loss = loss + (style_weight / len(style_feature_layers)) * sl

loss = loss + total_variation_weight * total_variation_loss(target_image)
loss_grads = K.gradients(loss, target_image)

# Evaluator class for computing efficiency
outputs = [loss]
if isinstance(loss_grads, (list, tuple)):
    outputs += loss_grads
else:
    outputs.append(loss_grads)

f_outputs = K.function([target_image], outputs)


def eval_loss_and_grads(x):
    if K.image_data_format() == 'channels_first':
        x = x.reshape((1, 3, img_nrows, img_ncols))
    else:
        x = x.reshape((1, img_nrows, img_ncols, 3))
    outs = f_outputs([x])
    loss_value = outs[0]
    if len(outs[1:]) == 1:
        grad_values = outs[1].flatten().astype('float64')
    else:
        grad_values = np.array(outs[1:]).flatten().astype('float64')
    return loss_value, grad_values


class Evaluator(object):

    def __init__(self):
        self.loss_value = None
        self.grads_values = None

    def loss(self, x):
        assert self.loss_value is None
        loss_value, grad_values = eval_loss_and_grads(x)
        self.loss_value = loss_value
        self.grad_values = grad_values
        return self.loss_value

    def grads(self, x):
        assert self.loss_value is not None
        grad_values = np.copy(self.grad_values)
        self.loss_value = None
        self.grad_values = None
        return grad_values


evaluator = Evaluator()

# Generate images by iterative optimization
if K.image_data_format() == 'channels_first':
    x = np.random.uniform(0, 255, (1, 3, img_nrows, img_ncols)) - 128.
else:
    x = np.random.uniform(0, 255, (1, img_nrows, img_ncols, 3)) - 128.

for i in range(num_iterations):
    print('Start of iteration', i, '/', num_iterations)
    start_time = time.time()
    x, min_val, info = fmin_l_bfgs_b(evaluator.loss, x.flatten(),
                                     fprime=evaluator.grads, maxfun=20)
    print('Current loss value:', min_val)
    # save current generated image
    img = deprocess_image(x.copy())
    fname = target_img_prefix + '_at_iteration_%d.png' % i
    save_img(fname, img)
    end_time = time.time()
    print('Image saved as', fname)
    print('Iteration %d completed in %ds' % (i, end_time - start_time))

'''
#How to use a stateful LSTM model, stateful vs stateless LSTM performance comparison

[More documentation about the Keras LSTM model](/layers/recurrent/#lstm)

The models are trained on an input/output pair, where
the input is a generated uniformly distributed
random sequence of length = `input_len`,
and the output is a moving average of the input with window length = `tsteps`.
Both `input_len` and `tsteps` are defined in the "editable parameters"
section.

A larger `tsteps` value means that the LSTM will need more memory
to figure out the input-output relationship.
This memory length is controlled by the `lahead` variable (more details below).

The rest of the parameters are:

- `input_len`: the length of the generated input sequence
- `lahead`: the input sequence length that the LSTM
  is trained on for each output point
- `batch_size`, `epochs`: same parameters as in the `model.fit(...)`
  function

When `lahead > 1`, the model input is preprocessed to a "rolling window view"
of the data, with the window length = `lahead`.
This is similar to sklearn's `view_as_windows`
with `window_shape` [being a single number.](
http://scikit-image.org/docs/0.10.x/api/skimage.util.html#view-as-windows)

When `lahead < tsteps`, only the stateful LSTM converges because its
statefulness allows it to see beyond the capability that lahead
gave it to fit the n-point average. The stateless LSTM does not have
this capability, and hence is limited by its `lahead` parameter,
which is not sufficient to see the n-point average.

When `lahead >= tsteps`, both the stateful and stateless LSTM converge.
'''
from __future__ import print_function
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from keras.models import Sequential
from keras.layers import Dense, LSTM

# ----------------------------------------------------------
# EDITABLE PARAMETERS
# Read the documentation in the script head for more details
# ----------------------------------------------------------

# length of input
input_len = 1000

# The window length of the moving average used to generate
# the output from the input in the input/output pair used
# to train the LSTM
# e.g. if tsteps=2 and input=[1, 2, 3, 4, 5],
#      then output=[1.5, 2.5, 3.5, 4.5]
tsteps = 2

# The input sequence length that the LSTM is trained on for each output point
lahead = 1

# training parameters passed to "model.fit(...)"
batch_size = 1
epochs = 10

# ------------
# MAIN PROGRAM
# ------------

print("*" * 33)
if lahead >= tsteps:
    print("STATELESS LSTM WILL ALSO CONVERGE")
else:
    print("STATELESS LSTM WILL NOT CONVERGE")
print("*" * 33)

np.random.seed(1986)

print('Generating Data...')


def gen_uniform_amp(amp=1, xn=10000):
    """Generates uniform random data between
    -amp and +amp
    and of length xn

    # Arguments
        amp: maximum/minimum range of uniform data
        xn: length of series
    """
    data_input = np.random.uniform(-1 * amp, +1 * amp, xn)
    data_input = pd.DataFrame(data_input)
    return data_input

# Since the output is a moving average of the input,
# the first few points of output will be NaN
# and will be dropped from the generated data
# before training the LSTM.
# Also, when lahead > 1,
# the preprocessing step later of "rolling window view"
# will also cause some points to be lost.
# For aesthetic reasons,
# in order to maintain generated data length = input_len after pre-processing,
# add a few points to account for the values that will be lost.
to_drop = max(tsteps - 1, lahead - 1)
data_input = gen_uniform_amp(amp=0.1, xn=input_len + to_drop)

# set the target to be a N-point average of the input
expected_output = data_input.rolling(window=tsteps, center=False).mean()

# when lahead > 1, need to convert the input to "rolling window view"
# https://docs.scipy.org/doc/numpy/reference/generated/numpy.repeat.html
if lahead > 1:
    data_input = np.repeat(data_input.values, repeats=lahead, axis=1)
    data_input = pd.DataFrame(data_input)
    for i, c in enumerate(data_input.columns):
        data_input[c] = data_input[c].shift(i)

# drop the nan
expected_output = expected_output[to_drop:]
data_input = data_input[to_drop:]

print('Input shape:', data_input.shape)
print('Output shape:', expected_output.shape)
print('Input head: ')
print(data_input.head())
print('Output head: ')
print(expected_output.head())
print('Input tail: ')
print(data_input.tail())
print('Output tail: ')
print(expected_output.tail())

print('Plotting input and expected output')
plt.plot(data_input[0][:10], '.')
plt.plot(expected_output[0][:10], '-')
plt.legend(['Input', 'Expected output'])
plt.title('Input')
plt.show()


def create_model(stateful):
    model = Sequential()
    model.add(LSTM(20,
              input_shape=(lahead, 1),
              batch_size=batch_size,
              stateful=stateful))
    model.add(Dense(1))
    model.compile(loss='mse', optimizer='adam')
    return model

print('Creating Stateful Model...')
model_stateful = create_model(stateful=True)


# split train/test data
def split_data(x, y, ratio=0.8):
    to_train = int(input_len * ratio)
    # tweak to match with batch_size
    to_train -= to_train % batch_size

    x_train = x[:to_train]
    y_train = y[:to_train]
    x_test = x[to_train:]
    y_test = y[to_train:]

    # tweak to match with batch_size
    to_drop = x.shape[0] % batch_size
    if to_drop > 0:
        x_test = x_test[:-1 * to_drop]
        y_test = y_test[:-1 * to_drop]

    # some reshaping
    reshape_3 = lambda x: x.values.reshape((x.shape[0], x.shape[1], 1))
    x_train = reshape_3(x_train)
    x_test = reshape_3(x_test)

    reshape_2 = lambda x: x.values.reshape((x.shape[0], 1))
    y_train = reshape_2(y_train)
    y_test = reshape_2(y_test)

    return (x_train, y_train), (x_test, y_test)


(x_train, y_train), (x_test, y_test) = split_data(data_input, expected_output)
print('x_train.shape: ', x_train.shape)
print('y_train.shape: ', y_train.shape)
print('x_test.shape: ', x_test.shape)
print('y_test.shape: ', y_test.shape)

print('Training')
for i in range(epochs):
    print('Epoch', i + 1, '/', epochs)
    # Note that the last state for sample i in a batch will
    # be used as initial state for sample i in the next batch.
    # Thus we are simultaneously training on batch_size series with
    # lower resolution than the original series contained in data_input.
    # Each of these series are offset by one step and can be
    # extracted with data_input[i::batch_size].
    model_stateful.fit(x_train,
                       y_train,
                       batch_size=batch_size,
                       epochs=1,
                       verbose=1,
                       validation_data=(x_test, y_test),
                       shuffle=False)
    model_stateful.reset_states()

print('Predicting')
predicted_stateful = model_stateful.predict(x_test, batch_size=batch_size)

print('Creating Stateless Model...')
model_stateless = create_model(stateful=False)

print('Training')
model_stateless.fit(x_train,
                    y_train,
                    batch_size=batch_size,
                    epochs=epochs,
                    verbose=1,
                    validation_data=(x_test, y_test),
                    shuffle=False)

print('Predicting')
predicted_stateless = model_stateless.predict(x_test, batch_size=batch_size)

# ----------------------------

print('Plotting Results')
plt.subplot(3, 1, 1)
plt.plot(y_test)
plt.title('Expected')
plt.subplot(3, 1, 2)
# drop the first "tsteps-1" because it is not possible to predict them
# since the "previous" timesteps to use do not exist
plt.plot((y_test - predicted_stateful).flatten()[tsteps - 1:])
plt.title('Stateful: Expected - Predicted')
plt.subplot(3, 1, 3)
plt.plot((y_test - predicted_stateless).flatten())
plt.title('Stateless: Expected - Predicted')
plt.show()

"""
#Trains a ResNet on the CIFAR10 dataset.

ResNet v1:
[Deep Residual Learning for Image Recognition
](https://arxiv.org/pdf/1512.03385.pdf)

ResNet v2:
[Identity Mappings in Deep Residual Networks
](https://arxiv.org/pdf/1603.05027.pdf)


Model|n|200-epoch accuracy|Original paper accuracy |sec/epoch GTX1080Ti
:------------|--:|-------:|-----------------------:|---:
ResNet20   v1|  3| 92.16 %|                 91.25 %|35
ResNet32   v1|  5| 92.46 %|                 92.49 %|50
ResNet44   v1|  7| 92.50 %|                 92.83 %|70
ResNet56   v1|  9| 92.71 %|                 93.03 %|90
ResNet110  v1| 18| 92.65 %|            93.39+-.16 %|165
ResNet164  v1| 27|     - %|                 94.07 %|  -
ResNet1001 v1|N/A|     - %|                 92.39 %|  -

&nbsp;

Model|n|200-epoch accuracy|Original paper accuracy |sec/epoch GTX1080Ti
:------------|--:|-------:|-----------------------:|---:
ResNet20   v2|  2|     - %|                     - %|---
ResNet32   v2|N/A| NA    %|            NA         %| NA
ResNet44   v2|N/A| NA    %|            NA         %| NA
ResNet56   v2|  6| 93.01 %|            NA         %|100
ResNet110  v2| 12| 93.15 %|            93.63      %|180
ResNet164  v2| 18|     - %|            94.54      %|  -
ResNet1001 v2|111|     - %|            95.08+-.14 %|  -
"""

from __future__ import print_function
import keras
from keras.layers import Dense, Conv2D, BatchNormalization, Activation
from keras.layers import AveragePooling2D, Input, Flatten
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, LearningRateScheduler
from keras.callbacks import ReduceLROnPlateau
from keras.preprocessing.image import ImageDataGenerator
from keras.regularizers import l2
from keras import backend as K
from keras.models import Model
from keras.datasets import cifar10
import numpy as np
import os

# Training parameters
batch_size = 32  # orig paper trained all networks with batch_size=128
epochs = 200
data_augmentation = True
num_classes = 10

# Subtracting pixel mean improves accuracy
subtract_pixel_mean = True

# Model parameter
# ----------------------------------------------------------------------------
#           |      | 200-epoch | Orig Paper| 200-epoch | Orig Paper| sec/epoch
# Model     |  n   | ResNet v1 | ResNet v1 | ResNet v2 | ResNet v2 | GTX1080Ti
#           |v1(v2)| %Accuracy | %Accuracy | %Accuracy | %Accuracy | v1 (v2)
# ----------------------------------------------------------------------------
# ResNet20  | 3 (2)| 92.16     | 91.25     | -----     | -----     | 35 (---)
# ResNet32  | 5(NA)| 92.46     | 92.49     | NA        | NA        | 50 ( NA)
# ResNet44  | 7(NA)| 92.50     | 92.83     | NA        | NA        | 70 ( NA)
# ResNet56  | 9 (6)| 92.71     | 93.03     | 93.01     | NA        | 90 (100)
# ResNet110 |18(12)| 92.65     | 93.39+-.16| 93.15     | 93.63     | 165(180)
# ResNet164 |27(18)| -----     | 94.07     | -----     | 94.54     | ---(---)
# ResNet1001| (111)| -----     | 92.39     | -----     | 95.08+-.14| ---(---)
# ---------------------------------------------------------------------------
n = 3

# Model version
# Orig paper: version = 1 (ResNet v1), Improved ResNet: version = 2 (ResNet v2)
version = 1

# Computed depth from supplied model parameter n
if version == 1:
    depth = n * 6 + 2
elif version == 2:
    depth = n * 9 + 2

# Model name, depth and version
model_type = 'ResNet%dv%d' % (depth, version)

# Load the CIFAR10 data.
(x_train, y_train), (x_test, y_test) = cifar10.load_data()

# Input image dimensions.
input_shape = x_train.shape[1:]

# Normalize data.
x_train = x_train.astype('float32') / 255
x_test = x_test.astype('float32') / 255

# If subtract pixel mean is enabled
if subtract_pixel_mean:
    x_train_mean = np.mean(x_train, axis=0)
    x_train -= x_train_mean
    x_test -= x_train_mean

print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')
print('y_train shape:', y_train.shape)

# Convert class vectors to binary class matrices.
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)


def lr_schedule(epoch):
    """Learning Rate Schedule

    Learning rate is scheduled to be reduced after 80, 120, 160, 180 epochs.
    Called automatically every epoch as part of callbacks during training.

    # Arguments
        epoch (int): The number of epochs

    # Returns
        lr (float32): learning rate
    """
    lr = 1e-3
    if epoch > 180:
        lr *= 0.5e-3
    elif epoch > 160:
        lr *= 1e-3
    elif epoch > 120:
        lr *= 1e-2
    elif epoch > 80:
        lr *= 1e-1
    print('Learning rate: ', lr)
    return lr


def resnet_layer(inputs,
                 num_filters=16,
                 kernel_size=3,
                 strides=1,
                 activation='relu',
                 batch_normalization=True,
                 conv_first=True):
    """2D Convolution-Batch Normalization-Activation stack builder

    # Arguments
        inputs (tensor): input tensor from input image or previous layer
        num_filters (int): Conv2D number of filters
        kernel_size (int): Conv2D square kernel dimensions
        strides (int): Conv2D square stride dimensions
        activation (string): activation name
        batch_normalization (bool): whether to include batch normalization
        conv_first (bool): conv-bn-activation (True) or
            bn-activation-conv (False)

    # Returns
        x (tensor): tensor as input to the next layer
    """
    conv = Conv2D(num_filters,
                  kernel_size=kernel_size,
                  strides=strides,
                  padding='same',
                  kernel_initializer='he_normal',
                  kernel_regularizer=l2(1e-4))

    x = inputs
    if conv_first:
        x = conv(x)
        if batch_normalization:
            x = BatchNormalization()(x)
        if activation is not None:
            x = Activation(activation)(x)
    else:
        if batch_normalization:
            x = BatchNormalization()(x)
        if activation is not None:
            x = Activation(activation)(x)
        x = conv(x)
    return x


def resnet_v1(input_shape, depth, num_classes=10):
    """ResNet Version 1 Model builder [a]

    Stacks of 2 x (3 x 3) Conv2D-BN-ReLU
    Last ReLU is after the shortcut connection.
    At the beginning of each stage, the feature map size is halved (downsampled)
    by a convolutional layer with strides=2, while the number of filters is
    doubled. Within each stage, the layers have the same number filters and the
    same number of filters.
    Features maps sizes:
    stage 0: 32x32, 16
    stage 1: 16x16, 32
    stage 2:  8x8,  64
    The Number of parameters is approx the same as Table 6 of [a]:
    ResNet20 0.27M
    ResNet32 0.46M
    ResNet44 0.66M
    ResNet56 0.85M
    ResNet110 1.7M

    # Arguments
        input_shape (tensor): shape of input image tensor
        depth (int): number of core convolutional layers
        num_classes (int): number of classes (CIFAR10 has 10)

    # Returns
        model (Model): Keras model instance
    """
    if (depth - 2) % 6 != 0:
        raise ValueError('depth should be 6n+2 (eg 20, 32, 44 in [a])')
    # Start model definition.
    num_filters = 16
    num_res_blocks = int((depth - 2) / 6)

    inputs = Input(shape=input_shape)
    x = resnet_layer(inputs=inputs)
    # Instantiate the stack of residual units
    for stack in range(3):
        for res_block in range(num_res_blocks):
            strides = 1
            if stack > 0 and res_block == 0:  # first layer but not first stack
                strides = 2  # downsample
            y = resnet_layer(inputs=x,
                             num_filters=num_filters,
                             strides=strides)
            y = resnet_layer(inputs=y,
                             num_filters=num_filters,
                             activation=None)
            if stack > 0 and res_block == 0:  # first layer but not first stack
                # linear projection residual shortcut connection to match
                # changed dims
                x = resnet_layer(inputs=x,
                                 num_filters=num_filters,
                                 kernel_size=1,
                                 strides=strides,
                                 activation=None,
                                 batch_normalization=False)
            x = keras.layers.add([x, y])
            x = Activation('relu')(x)
        num_filters *= 2

    # Add classifier on top.
    # v1 does not use BN after last shortcut connection-ReLU
    x = AveragePooling2D(pool_size=8)(x)
    y = Flatten()(x)
    outputs = Dense(num_classes,
                    activation='softmax',
                    kernel_initializer='he_normal')(y)

    # Instantiate model.
    model = Model(inputs=inputs, outputs=outputs)
    return model


def resnet_v2(input_shape, depth, num_classes=10):
    """ResNet Version 2 Model builder [b]

    Stacks of (1 x 1)-(3 x 3)-(1 x 1) BN-ReLU-Conv2D or also known as
    bottleneck layer
    First shortcut connection per layer is 1 x 1 Conv2D.
    Second and onwards shortcut connection is identity.
    At the beginning of each stage, the feature map size is halved (downsampled)
    by a convolutional layer with strides=2, while the number of filter maps is
    doubled. Within each stage, the layers have the same number filters and the
    same filter map sizes.
    Features maps sizes:
    conv1  : 32x32,  16
    stage 0: 32x32,  64
    stage 1: 16x16, 128
    stage 2:  8x8,  256

    # Arguments
        input_shape (tensor): shape of input image tensor
        depth (int): number of core convolutional layers
        num_classes (int): number of classes (CIFAR10 has 10)

    # Returns
        model (Model): Keras model instance
    """
    if (depth - 2) % 9 != 0:
        raise ValueError('depth should be 9n+2 (eg 56 or 110 in [b])')
    # Start model definition.
    num_filters_in = 16
    num_res_blocks = int((depth - 2) / 9)

    inputs = Input(shape=input_shape)
    # v2 performs Conv2D with BN-ReLU on input before splitting into 2 paths
    x = resnet_layer(inputs=inputs,
                     num_filters=num_filters_in,
                     conv_first=True)

    # Instantiate the stack of residual units
    for stage in range(3):
        for res_block in range(num_res_blocks):
            activation = 'relu'
            batch_normalization = True
            strides = 1
            if stage == 0:
                num_filters_out = num_filters_in * 4
                if res_block == 0:  # first layer and first stage
                    activation = None
                    batch_normalization = False
            else:
                num_filters_out = num_filters_in * 2
                if res_block == 0:  # first layer but not first stage
                    strides = 2    # downsample

            # bottleneck residual unit
            y = resnet_layer(inputs=x,
                             num_filters=num_filters_in,
                             kernel_size=1,
                             strides=strides,
                             activation=activation,
                             batch_normalization=batch_normalization,
                             conv_first=False)
            y = resnet_layer(inputs=y,
                             num_filters=num_filters_in,
                             conv_first=False)
            y = resnet_layer(inputs=y,
                             num_filters=num_filters_out,
                             kernel_size=1,
                             conv_first=False)
            if res_block == 0:
                # linear projection residual shortcut connection to match
                # changed dims
                x = resnet_layer(inputs=x,
                                 num_filters=num_filters_out,
                                 kernel_size=1,
                                 strides=strides,
                                 activation=None,
                                 batch_normalization=False)
            x = keras.layers.add([x, y])

        num_filters_in = num_filters_out

    # Add classifier on top.
    # v2 has BN-ReLU before Pooling
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = AveragePooling2D(pool_size=8)(x)
    y = Flatten()(x)
    outputs = Dense(num_classes,
                    activation='softmax',
                    kernel_initializer='he_normal')(y)

    # Instantiate model.
    model = Model(inputs=inputs, outputs=outputs)
    return model


if version == 2:
    model = resnet_v2(input_shape=input_shape, depth=depth)
else:
    model = resnet_v1(input_shape=input_shape, depth=depth)

model.compile(loss='categorical_crossentropy',
              optimizer=Adam(learning_rate=lr_schedule(0)),
              metrics=['accuracy'])
model.summary()
print(model_type)

# Prepare model model saving directory.
save_dir = os.path.join(os.getcwd(), 'saved_models')
model_name = 'cifar10_%s_model.{epoch:03d}.h5' % model_type
if not os.path.isdir(save_dir):
    os.makedirs(save_dir)
filepath = os.path.join(save_dir, model_name)

# Prepare callbacks for model saving and for learning rate adjustment.
checkpoint = ModelCheckpoint(filepath=filepath,
                             monitor='val_acc',
                             verbose=1,
                             save_best_only=True)

lr_scheduler = LearningRateScheduler(lr_schedule)

lr_reducer = ReduceLROnPlateau(factor=np.sqrt(0.1),
                               cooldown=0,
                               patience=5,
                               min_lr=0.5e-6)

callbacks = [checkpoint, lr_reducer, lr_scheduler]

# Run training, with or without data augmentation.
if not data_augmentation:
    print('Not using data augmentation.')
    model.fit(x_train, y_train,
              batch_size=batch_size,
              epochs=epochs,
              validation_data=(x_test, y_test),
              shuffle=True,
              callbacks=callbacks)
else:
    print('Using real-time data augmentation.')
    # This will do preprocessing and realtime data augmentation:
    datagen = ImageDataGenerator(
        # set input mean to 0 over the dataset
        featurewise_center=False,
        # set each sample mean to 0
        samplewise_center=False,
        # divide inputs by std of dataset
        featurewise_std_normalization=False,
        # divide each input by its std
        samplewise_std_normalization=False,
        # apply ZCA whitening
        zca_whitening=False,
        # epsilon for ZCA whitening
        zca_epsilon=1e-06,
        # randomly rotate images in the range (deg 0 to 180)
        rotation_range=0,
        # randomly shift images horizontally
        width_shift_range=0.1,
        # randomly shift images vertically
        height_shift_range=0.1,
        # set range for random shear
        shear_range=0.,
        # set range for random zoom
        zoom_range=0.,
        # set range for random channel shifts
        channel_shift_range=0.,
        # set mode for filling points outside the input boundaries
        fill_mode='nearest',
        # value used for fill_mode = "constant"
        cval=0.,
        # randomly flip images
        horizontal_flip=True,
        # randomly flip images
        vertical_flip=False,
        # set rescaling factor (applied before any other transformation)
        rescale=None,
        # set function that will be applied on each input
        preprocessing_function=None,
        # image data format, either "channels_first" or "channels_last"
        data_format=None,
        # fraction of images reserved for validation (strictly between 0 and 1)
        validation_split=0.0)

    # Compute quantities required for featurewise normalization
    # (std, mean, and principal components if ZCA whitening is applied).
    datagen.fit(x_train)

    # Fit the model on the batches generated by datagen.flow().
    model.fit_generator(datagen.flow(x_train, y_train, batch_size=batch_size),
                        validation_data=(x_test, y_test),
                        epochs=epochs, verbose=1, workers=4,
                        callbacks=callbacks)

# Score trained model.
scores = model.evaluate(x_test, y_test, verbose=1)
print('Test loss:', scores[0])
print('Test accuracy:', scores[1])

'''Example of VAE on MNIST dataset using MLP

The VAE has a modular design. The encoder, decoder and VAE
are 3 models that share weights. After training the VAE model,
the encoder can be used to generate latent vectors.
The decoder can be used to generate MNIST digits by sampling the
latent vector from a Gaussian distribution with mean = 0 and std = 1.

# Reference

[1] Kingma, Diederik P., and Max Welling.
"Auto-Encoding Variational Bayes."
https://arxiv.org/abs/1312.6114
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import keras
from keras.layers import Lambda, Input, Dense
from keras.models import Model
from keras.datasets import mnist
from keras.losses import mse, binary_crossentropy
from keras.utils import plot_model
from keras import backend as K

import numpy as np
import matplotlib.pyplot as plt
import argparse
import os


# reparameterization trick
# instead of sampling from Q(z|X), sample epsilon = N(0,I)
# z = z_mean + sqrt(var) * epsilon
def sampling(args):
    """Reparameterization trick by sampling from an isotropic unit Gaussian.

    # Arguments
        args (tensor): mean and log of variance of Q(z|X)

    # Returns
        z (tensor): sampled latent vector
    """

    z_mean, z_log_var = args
    batch = K.shape(z_mean)[0]
    dim = K.int_shape(z_mean)[1]
    # by default, random_normal has mean = 0 and std = 1.0
    epsilon = K.random_normal(shape=(batch, dim))
    return z_mean + K.exp(0.5 * z_log_var) * epsilon


def plot_results(models,
                 data,
                 batch_size=128,
                 model_name="vae_mnist"):
    """Plots labels and MNIST digits as a function of the 2D latent vector

    # Arguments
        models (tuple): encoder and decoder models
        data (tuple): test data and label
        batch_size (int): prediction batch size
        model_name (string): which model is using this function
    """

    encoder, decoder = models
    x_test, y_test = data
    os.makedirs(model_name, exist_ok=True)

    filename = os.path.join(model_name, "vae_mean.png")
    # display a 2D plot of the digit classes in the latent space
    z_mean, _, _ = encoder.predict(x_test,
                                   batch_size=batch_size)
    plt.figure(figsize=(12, 10))
    plt.scatter(z_mean[:, 0], z_mean[:, 1], c=y_test)
    plt.colorbar()
    plt.xlabel("z[0]")
    plt.ylabel("z[1]")
    plt.savefig(filename)
    plt.show()

    filename = os.path.join(model_name, "digits_over_latent.png")
    # display a 30x30 2D manifold of digits
    n = 30
    digit_size = 28
    figure = np.zeros((digit_size * n, digit_size * n))
    # linearly spaced coordinates corresponding to the 2D plot
    # of digit classes in the latent space
    grid_x = np.linspace(-4, 4, n)
    grid_y = np.linspace(-4, 4, n)[::-1]

    for i, yi in enumerate(grid_y):
        for j, xi in enumerate(grid_x):
            z_sample = np.array([[xi, yi]])
            x_decoded = decoder.predict(z_sample)
            digit = x_decoded[0].reshape(digit_size, digit_size)
            figure[i * digit_size: (i + 1) * digit_size,
                   j * digit_size: (j + 1) * digit_size] = digit

    plt.figure(figsize=(10, 10))
    start_range = digit_size // 2
    end_range = (n - 1) * digit_size + start_range + 1
    pixel_range = np.arange(start_range, end_range, digit_size)
    sample_range_x = np.round(grid_x, 1)
    sample_range_y = np.round(grid_y, 1)
    plt.xticks(pixel_range, sample_range_x)
    plt.yticks(pixel_range, sample_range_y)
    plt.xlabel("z[0]")
    plt.ylabel("z[1]")
    plt.imshow(figure, cmap='Greys_r')
    plt.savefig(filename)
    plt.show()


# MNIST dataset
(x_train, y_train), (x_test, y_test) = mnist.load_data()

image_size = x_train.shape[1]
original_dim = image_size * image_size
x_train = np.reshape(x_train, [-1, original_dim])
x_test = np.reshape(x_test, [-1, original_dim])
x_train = x_train.astype('float32') / 255
x_test = x_test.astype('float32') / 255

# network parameters
input_shape = (original_dim, )
intermediate_dim = 512
batch_size = 128
latent_dim = 2
epochs = 50

# VAE model = encoder + decoder
# build encoder model
inputs = Input(shape=input_shape, name='encoder_input')
x = Dense(intermediate_dim, activation='relu')(inputs)
z_mean = Dense(latent_dim, name='z_mean')(x)
z_log_var = Dense(latent_dim, name='z_log_var')(x)

# use reparameterization trick to push the sampling out as input
# note that "output_shape" isn't necessary with the TensorFlow backend
z = Lambda(sampling, output_shape=(latent_dim,), name='z')([z_mean, z_log_var])

# instantiate encoder model
encoder = Model(inputs, [z_mean, z_log_var, z], name='encoder')
encoder.summary()
plot_model(encoder, to_file='vae_mlp_encoder.png', show_shapes=True)

# build decoder model
latent_inputs = Input(shape=(latent_dim,), name='z_sampling')
x = Dense(intermediate_dim, activation='relu')(latent_inputs)
outputs = Dense(original_dim, activation='sigmoid')(x)

# instantiate decoder model
decoder = Model(latent_inputs, outputs, name='decoder')
decoder.summary()
plot_model(decoder, to_file='vae_mlp_decoder.png', show_shapes=True)

# instantiate VAE model
outputs = decoder(encoder(inputs)[2])
vae = Model(inputs, outputs, name='vae_mlp')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    help_ = "Load h5 model trained weights"
    parser.add_argument("-w", "--weights", help=help_)
    help_ = "Use mse loss instead of binary cross entropy (default)"
    parser.add_argument("-m",
                        "--mse",
                        help=help_, action='store_true')
    args = parser.parse_args()
    models = (encoder, decoder)
    data = (x_test, y_test)

    # VAE loss = mse_loss or xent_loss + kl_loss
    if args.mse:
        reconstruction_loss = mse(inputs, outputs)
    else:
        reconstruction_loss = binary_crossentropy(inputs,
                                                  outputs)

    reconstruction_loss *= original_dim
    kl_loss = 1 + z_log_var - K.square(z_mean) - K.exp(z_log_var)
    kl_loss = K.sum(kl_loss, axis=-1)
    kl_loss *= -0.5
    vae_loss = K.mean(reconstruction_loss + kl_loss)
    vae.add_loss(vae_loss)
    vae.compile(optimizer='adam')

    if args.weights:
        vae.load_weights(args.weights)
    else:
        # train the autoencoder
        vae.fit(x_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=(x_test, None))
        vae.save_weights('vae_mlp_mnist.h5')

    plot_results(models,
                 data,
                 batch_size=batch_size,
                 model_name="vae_mlp")

'''
# Trains two recurrent neural networks based upon a story and a question.

The resulting merged vector is then queried to answer a range of bAbI tasks.

The results are comparable to those for an LSTM model provided in Weston et al.:
"Towards AI-Complete Question Answering: A Set of Prerequisite Toy Tasks"
http://arxiv.org/abs/1502.05698

Task Number                  | FB LSTM Baseline | Keras QA
---                          | ---              | ---
QA1 - Single Supporting Fact | 50               | 52.1
QA2 - Two Supporting Facts   | 20               | 37.0
QA3 - Three Supporting Facts | 20               | 20.5
QA4 - Two Arg. Relations     | 61               | 62.9
QA5 - Three Arg. Relations   | 70               | 61.9
QA6 - yes/No Questions       | 48               | 50.7
QA7 - Counting               | 49               | 78.9
QA8 - Lists/Sets             | 45               | 77.2
QA9 - Simple Negation        | 64               | 64.0
QA10 - Indefinite Knowledge  | 44               | 47.7
QA11 - Basic Coreference     | 72               | 74.9
QA12 - Conjunction           | 74               | 76.4
QA13 - Compound Coreference  | 94               | 94.4
QA14 - Time Reasoning        | 27               | 34.8
QA15 - Basic Deduction       | 21               | 32.4
QA16 - Basic Induction       | 23               | 50.6
QA17 - Positional Reasoning  | 51               | 49.1
QA18 - Size Reasoning        | 52               | 90.8
QA19 - Path Finding          | 8                | 9.0
QA20 - Agent's Motivations   | 91               | 90.7

For the resources related to the bAbI project, refer to:
https://research.facebook.com/researchers/1543934539189348

### Notes

- With default word, sentence, and query vector sizes, the GRU model achieves:
  - 52.1% test accuracy on QA1 in 20 epochs (2 seconds per epoch on CPU)
  - 37.0% test accuracy on QA2 in 20 epochs (16 seconds per epoch on CPU)
In comparison, the Facebook paper achieves 50% and 20% for the LSTM baseline.

- The task does not traditionally parse the question separately. This likely
improves accuracy and is a good example of merging two RNNs.

- The word vector embeddings are not shared between the story and question RNNs.

- See how the accuracy changes given 10,000 training samples (en-10k) instead
of only 1000. 1000 was used in order to be comparable to the original paper.

- Experiment with GRU, LSTM, and JZS1-3 as they give subtly different results.

- The length and noise (i.e. 'useless' story components) impact the ability of
LSTMs / GRUs to provide the correct answer. Given only the supporting facts,
these RNNs can achieve 100% accuracy on many tasks. Memory networks and neural
networks that use attentional processes can efficiently search through this
noise to find the relevant statements, improving performance substantially.
This becomes especially obvious on QA2 and QA3, both far longer than QA1.
'''

from __future__ import print_function
from functools import reduce
import re
import tarfile

import numpy as np

from keras.utils.data_utils import get_file
from keras.layers.embeddings import Embedding
from keras import layers
from keras.layers import recurrent
from keras.models import Model
from keras.preprocessing.sequence import pad_sequences


def tokenize(sent):
    '''Return the tokens of a sentence including punctuation.

    >>> tokenize('Bob dropped the apple. Where is the apple?')
    ['Bob', 'dropped', 'the', 'apple', '.', 'Where', 'is', 'the', 'apple', '?']
    '''
    return [x.strip() for x in re.split(r'(\W+)', sent) if x.strip()]


def parse_stories(lines, only_supporting=False):
    '''Parse stories provided in the bAbi tasks format

    If only_supporting is true,
    only the sentences that support the answer are kept.
    '''
    data = []
    story = []
    for line in lines:
        line = line.decode('utf-8').strip()
        nid, line = line.split(' ', 1)
        nid = int(nid)
        if nid == 1:
            story = []
        if '\t' in line:
            q, a, supporting = line.split('\t')
            q = tokenize(q)
            if only_supporting:
                # Only select the related substory
                supporting = map(int, supporting.split())
                substory = [story[i - 1] for i in supporting]
            else:
                # Provide all the substories
                substory = [x for x in story if x]
            data.append((substory, q, a))
            story.append('')
        else:
            sent = tokenize(line)
            story.append(sent)
    return data


def get_stories(f, only_supporting=False, max_length=None):
    '''Given a file name, read the file, retrieve the stories,
    and then convert the sentences into a single story.

    If max_length is supplied,
    any stories longer than max_length tokens will be discarded.
    '''
    data = parse_stories(f.readlines(), only_supporting=only_supporting)
    flatten = lambda data: reduce(lambda x, y: x + y, data)
    data = [(flatten(story), q, answer) for story, q, answer in data
            if not max_length or len(flatten(story)) < max_length]
    return data


def vectorize_stories(data, word_idx, story_maxlen, query_maxlen):
    xs = []
    xqs = []
    ys = []
    for story, query, answer in data:
        x = [word_idx[w] for w in story]
        xq = [word_idx[w] for w in query]
        # let's not forget that index 0 is reserved
        y = np.zeros(len(word_idx) + 1)
        y[word_idx[answer]] = 1
        xs.append(x)
        xqs.append(xq)
        ys.append(y)
    return (pad_sequences(xs, maxlen=story_maxlen),
            pad_sequences(xqs, maxlen=query_maxlen), np.array(ys))

RNN = recurrent.LSTM
EMBED_HIDDEN_SIZE = 50
SENT_HIDDEN_SIZE = 100
QUERY_HIDDEN_SIZE = 100
BATCH_SIZE = 32
EPOCHS = 20
print('RNN / Embed / Sent / Query = {}, {}, {}, {}'.format(RNN,
                                                           EMBED_HIDDEN_SIZE,
                                                           SENT_HIDDEN_SIZE,
                                                           QUERY_HIDDEN_SIZE))

try:
    path = get_file('babi-tasks-v1-2.tar.gz',
                    origin='https://s3.amazonaws.com/text-datasets/'
                           'babi_tasks_1-20_v1-2.tar.gz')
except:
    print('Error downloading dataset, please download it manually:\n'
          '$ wget http://www.thespermwhale.com/jaseweston/babi/tasks_1-20_v1-2'
          '.tar.gz\n'
          '$ mv tasks_1-20_v1-2.tar.gz ~/.keras/datasets/babi-tasks-v1-2.tar.gz')
    raise

# Default QA1 with 1000 samples
# challenge = 'tasks_1-20_v1-2/en/qa1_single-supporting-fact_{}.txt'
# QA1 with 10,000 samples
# challenge = 'tasks_1-20_v1-2/en-10k/qa1_single-supporting-fact_{}.txt'
# QA2 with 1000 samples
challenge = 'tasks_1-20_v1-2/en/qa2_two-supporting-facts_{}.txt'
# QA2 with 10,000 samples
# challenge = 'tasks_1-20_v1-2/en-10k/qa2_two-supporting-facts_{}.txt'
with tarfile.open(path) as tar:
    train = get_stories(tar.extractfile(challenge.format('train')))
    test = get_stories(tar.extractfile(challenge.format('test')))

vocab = set()
for story, q, answer in train + test:
    vocab |= set(story + q + [answer])
vocab = sorted(vocab)

# Reserve 0 for masking via pad_sequences
vocab_size = len(vocab) + 1
word_idx = dict((c, i + 1) for i, c in enumerate(vocab))
story_maxlen = max(map(len, (x for x, _, _ in train + test)))
query_maxlen = max(map(len, (x for _, x, _ in train + test)))

x, xq, y = vectorize_stories(train, word_idx, story_maxlen, query_maxlen)
tx, txq, ty = vectorize_stories(test, word_idx, story_maxlen, query_maxlen)

print('vocab = {}'.format(vocab))
print('x.shape = {}'.format(x.shape))
print('xq.shape = {}'.format(xq.shape))
print('y.shape = {}'.format(y.shape))
print('story_maxlen, query_maxlen = {}, {}'.format(story_maxlen, query_maxlen))

print('Build model...')

sentence = layers.Input(shape=(story_maxlen,), dtype='int32')
encoded_sentence = layers.Embedding(vocab_size, EMBED_HIDDEN_SIZE)(sentence)
encoded_sentence = RNN(SENT_HIDDEN_SIZE)(encoded_sentence)

question = layers.Input(shape=(query_maxlen,), dtype='int32')
encoded_question = layers.Embedding(vocab_size, EMBED_HIDDEN_SIZE)(question)
encoded_question = RNN(QUERY_HIDDEN_SIZE)(encoded_question)

merged = layers.concatenate([encoded_sentence, encoded_question])
preds = layers.Dense(vocab_size, activation='softmax')(merged)

model = Model([sentence, question], preds)
model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

print('Training')
model.fit([x, xq], y,
          batch_size=BATCH_SIZE,
          epochs=EPOCHS,
          validation_split=0.05)

print('Evaluation')
loss, acc = model.evaluate([tx, txq], ty,
                           batch_size=BATCH_SIZE)
print('Test loss / test accuracy = {:.4f} / {:.4f}'.format(loss, acc))

'''
#This example demonstrates how to write custom layers for Keras.

We build a custom activation layer called 'Antirectifier',
which modifies the shape of the tensor that passes through it.
We need to specify two methods: `compute_output_shape` and `call`.

Note that the same result can also be achieved via a Lambda layer.

Because our custom layer is written with primitives from the Keras
backend (`K`), our code can run both on TensorFlow and Theano.
'''

from __future__ import print_function
import keras
from keras.models import Sequential
from keras import layers
from keras.datasets import mnist
from keras import backend as K


class Antirectifier(layers.Layer):
    '''This is the combination of a sample-wise
    L2 normalization with the concatenation of the
    positive part of the input with the negative part
    of the input. The result is a tensor of samples that are
    twice as large as the input samples.

    It can be used in place of a ReLU.

    # Input shape
        2D tensor of shape (samples, n)

    # Output shape
        2D tensor of shape (samples, 2*n)

    # Theoretical justification
        When applying ReLU, assuming that the distribution
        of the previous output is approximately centered around 0.,
        you are discarding half of your input. This is inefficient.

        Antirectifier allows to return all-positive outputs like ReLU,
        without discarding any data.

        Tests on MNIST show that Antirectifier allows to train networks
        with twice less parameters yet with comparable
        classification accuracy as an equivalent ReLU-based network.
    '''

    def compute_output_shape(self, input_shape):
        shape = list(input_shape)
        assert len(shape) == 2  # only valid for 2D tensors
        shape[-1] *= 2
        return tuple(shape)

    def call(self, inputs):
        inputs -= K.mean(inputs, axis=1, keepdims=True)
        inputs = K.l2_normalize(inputs, axis=1)
        pos = K.relu(inputs)
        neg = K.relu(-inputs)
        return K.concatenate([pos, neg], axis=1)

# global parameters
batch_size = 128
num_classes = 10
epochs = 40

# the data, split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

x_train = x_train.reshape(60000, 784)
x_test = x_test.reshape(10000, 784)
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

# build the model
model = Sequential()
model.add(layers.Dense(256, input_shape=(784,)))
model.add(Antirectifier())
model.add(layers.Dropout(0.1))
model.add(layers.Dense(256))
model.add(Antirectifier())
model.add(layers.Dropout(0.1))
model.add(layers.Dense(num_classes))
model.add(layers.Activation('softmax'))

# compile the model
model.compile(loss='categorical_crossentropy',
              optimizer='rmsprop',
              metrics=['accuracy'])

# train the model
model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          verbose=1,
          validation_data=(x_test, y_test))

# next, compare with an equivalent network
# with2x bigger Dense layers and ReLU

'''This script loads pre-trained word embeddings (GloVe embeddings)
into a frozen Keras Embedding layer, and uses it to
train a text classification model on the 20 Newsgroup dataset
(classification of newsgroup messages into 20 different categories).

GloVe embedding data can be found at:
http://nlp.stanford.edu/data/glove.6B.zip
(source page: http://nlp.stanford.edu/projects/glove/)

20 Newsgroup data can be found at:
http://www.cs.cmu.edu/afs/cs.cmu.edu/project/theo-20/www/data/news20.html
'''

from __future__ import print_function

import os
import sys
import numpy as np
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from keras.layers import Dense, Input, GlobalMaxPooling1D
from keras.layers import Conv1D, MaxPooling1D, Embedding
from keras.models import Model
from keras.initializers import Constant


BASE_DIR = ''
GLOVE_DIR = os.path.join(BASE_DIR, 'glove.6B')
TEXT_DATA_DIR = os.path.join(BASE_DIR, '20_newsgroup')
MAX_SEQUENCE_LENGTH = 1000
MAX_NUM_WORDS = 20000
EMBEDDING_DIM = 100
VALIDATION_SPLIT = 0.2

# first, build index mapping words in the embeddings set
# to their embedding vector

print('Indexing word vectors.')

embeddings_index = {}
with open(os.path.join(GLOVE_DIR, 'glove.6B.100d.txt')) as f:
    for line in f:
        word, coefs = line.split(maxsplit=1)
        coefs = np.fromstring(coefs, 'f', sep=' ')
        embeddings_index[word] = coefs

print('Found %s word vectors.' % len(embeddings_index))

# second, prepare text samples and their labels
print('Processing text dataset')

texts = []  # list of text samples
labels_index = {}  # dictionary mapping label name to numeric id
labels = []  # list of label ids
for name in sorted(os.listdir(TEXT_DATA_DIR)):
    path = os.path.join(TEXT_DATA_DIR, name)
    if os.path.isdir(path):
        label_id = len(labels_index)
        labels_index[name] = label_id
        for fname in sorted(os.listdir(path)):
            if fname.isdigit():
                fpath = os.path.join(path, fname)
                args = {} if sys.version_info < (3,) else {'encoding': 'latin-1'}
                with open(fpath, **args) as f:
                    t = f.read()
                    i = t.find('\n\n')  # skip header
                    if 0 < i:
                        t = t[i:]
                    texts.append(t)
                labels.append(label_id)

print('Found %s texts.' % len(texts))

# finally, vectorize the text samples into a 2D integer tensor
tokenizer = Tokenizer(num_words=MAX_NUM_WORDS)
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)

word_index = tokenizer.word_index
print('Found %s unique tokens.' % len(word_index))

data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)

labels = to_categorical(np.asarray(labels))
print('Shape of data tensor:', data.shape)
print('Shape of label tensor:', labels.shape)

# split the data into a training set and a validation set
indices = np.arange(data.shape[0])
np.random.shuffle(indices)
data = data[indices]
labels = labels[indices]
num_validation_samples = int(VALIDATION_SPLIT * data.shape[0])

x_train = data[:-num_validation_samples]
y_train = labels[:-num_validation_samples]
x_val = data[-num_validation_samples:]
y_val = labels[-num_validation_samples:]

print('Preparing embedding matrix.')

# prepare embedding matrix
num_words = min(MAX_NUM_WORDS, len(word_index) + 1)
embedding_matrix = np.zeros((num_words, EMBEDDING_DIM))
for word, i in word_index.items():
    if i >= MAX_NUM_WORDS:
        continue
    embedding_vector = embeddings_index.get(word)
    if embedding_vector is not None:
        # words not found in embedding index will be all-zeros.
        embedding_matrix[i] = embedding_vector

# load pre-trained word embeddings into an Embedding layer
# note that we set trainable = False so as to keep the embeddings fixed
embedding_layer = Embedding(num_words,
                            EMBEDDING_DIM,
                            embeddings_initializer=Constant(embedding_matrix),
                            input_length=MAX_SEQUENCE_LENGTH,
                            trainable=False)

print('Training model.')

# train a 1D convnet with global maxpooling
sequence_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype='int32')
embedded_sequences = embedding_layer(sequence_input)
x = Conv1D(128, 5, activation='relu')(embedded_sequences)
x = MaxPooling1D(5)(x)
x = Conv1D(128, 5, activation='relu')(x)
x = MaxPooling1D(5)(x)
x = Conv1D(128, 5, activation='relu')(x)
x = GlobalMaxPooling1D()(x)
x = Dense(128, activation='relu')(x)
preds = Dense(len(labels_index), activation='softmax')(x)

model = Model(sequence_input, preds)
model.compile(loss='categorical_crossentropy',
              optimizer='rmsprop',
              metrics=['acc'])

model.fit(x_train, y_train,
          batch_size=128,
          epochs=10,
          validation_data=(x_val, y_val))

'''
#Sequence to sequence example in Keras (character-level).

This script demonstrates how to implement a basic character-level
sequence-to-sequence model. We apply it to translating
short English sentences into short French sentences,
character-by-character. Note that it is fairly unusual to
do character-level machine translation, as word-level
models are more common in this domain.

**Summary of the algorithm**

- We start with input sequences from a domain (e.g. English sentences)
    and corresponding target sequences from another domain
    (e.g. French sentences).
- An encoder LSTM turns input sequences to 2 state vectors
    (we keep the last LSTM state and discard the outputs).
- A decoder LSTM is trained to turn the target sequences into
    the same sequence but offset by one timestep in the future,
    a training process called "teacher forcing" in this context.
    It uses as initial state the state vectors from the encoder.
    Effectively, the decoder learns to generate `targets[t+1...]`
    given `targets[...t]`, conditioned on the input sequence.
- In inference mode, when we want to decode unknown input sequences, we:
    - Encode the input sequence into state vectors
    - Start with a target sequence of size 1
        (just the start-of-sequence character)
    - Feed the state vectors and 1-char target sequence
        to the decoder to produce predictions for the next character
    - Sample the next character using these predictions
        (we simply use argmax).
    - Append the sampled character to the target sequence
    - Repeat until we generate the end-of-sequence character or we
        hit the character limit.

**Data download**

[English to French sentence pairs.
](http://www.manythings.org/anki/fra-eng.zip)

[Lots of neat sentence pairs datasets.
](http://www.manythings.org/anki/)

**References**

- [Sequence to Sequence Learning with Neural Networks
   ](https://arxiv.org/abs/1409.3215)
- [Learning Phrase Representations using
    RNN Encoder-Decoder for Statistical Machine Translation
    ](https://arxiv.org/abs/1406.1078)
'''
from __future__ import print_function

from keras.models import Model
from keras.layers import Input, LSTM, Dense
import numpy as np

batch_size = 64  # Batch size for training.
epochs = 100  # Number of epochs to train for.
latent_dim = 256  # Latent dimensionality of the encoding space.
num_samples = 10000  # Number of samples to train on.
# Path to the data txt file on disk.
data_path = 'fra-eng/fra.txt'

# Vectorize the data.
input_texts = []
target_texts = []
input_characters = set()
target_characters = set()
with open(data_path, 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')
for line in lines[: min(num_samples, len(lines) - 1)]:
    input_text, target_text, _ = line.split('\t')
    # We use "tab" as the "start sequence" character
    # for the targets, and "\n" as "end sequence" character.
    target_text = '\t' + target_text + '\n'
    input_texts.append(input_text)
    target_texts.append(target_text)
    for char in input_text:
        if char not in input_characters:
            input_characters.add(char)
    for char in target_text:
        if char not in target_characters:
            target_characters.add(char)

input_characters = sorted(list(input_characters))
target_characters = sorted(list(target_characters))
num_encoder_tokens = len(input_characters)
num_decoder_tokens = len(target_characters)
max_encoder_seq_length = max([len(txt) for txt in input_texts])
max_decoder_seq_length = max([len(txt) for txt in target_texts])

print('Number of samples:', len(input_texts))
print('Number of unique input tokens:', num_encoder_tokens)
print('Number of unique output tokens:', num_decoder_tokens)
print('Max sequence length for inputs:', max_encoder_seq_length)
print('Max sequence length for outputs:', max_decoder_seq_length)

input_token_index = dict(
    [(char, i) for i, char in enumerate(input_characters)])
target_token_index = dict(
    [(char, i) for i, char in enumerate(target_characters)])

encoder_input_data = np.zeros(
    (len(input_texts), max_encoder_seq_length, num_encoder_tokens),
    dtype='float32')
decoder_input_data = np.zeros(
    (len(input_texts), max_decoder_seq_length, num_decoder_tokens),
    dtype='float32')
decoder_target_data = np.zeros(
    (len(input_texts), max_decoder_seq_length, num_decoder_tokens),
    dtype='float32')

for i, (input_text, target_text) in enumerate(zip(input_texts, target_texts)):
    for t, char in enumerate(input_text):
        encoder_input_data[i, t, input_token_index[char]] = 1.
    encoder_input_data[i, t + 1:, input_token_index[' ']] = 1.
    for t, char in enumerate(target_text):
        # decoder_target_data is ahead of decoder_input_data by one timestep
        decoder_input_data[i, t, target_token_index[char]] = 1.
        if t > 0:
            # decoder_target_data will be ahead by one timestep
            # and will not include the start character.
            decoder_target_data[i, t - 1, target_token_index[char]] = 1.
    decoder_input_data[i, t + 1:, target_token_index[' ']] = 1.
    decoder_target_data[i, t:, target_token_index[' ']] = 1.
# Define an input sequence and process it.
encoder_inputs = Input(shape=(None, num_encoder_tokens))
encoder = LSTM(latent_dim, return_state=True)
encoder_outputs, state_h, state_c = encoder(encoder_inputs)
# We discard `encoder_outputs` and only keep the states.
encoder_states = [state_h, state_c]

# Set up the decoder, using `encoder_states` as initial state.
decoder_inputs = Input(shape=(None, num_decoder_tokens))
# We set up our decoder to return full output sequences,
# and to return internal states as well. We don't use the
# return states in the training model, but we will use them in inference.
decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True)
decoder_outputs, _, _ = decoder_lstm(decoder_inputs,
                                     initial_state=encoder_states)
decoder_dense = Dense(num_decoder_tokens, activation='softmax')
decoder_outputs = decoder_dense(decoder_outputs)

# Define the model that will turn
# `encoder_input_data` & `decoder_input_data` into `decoder_target_data`
model = Model([encoder_inputs, decoder_inputs], decoder_outputs)

# Run training
model.compile(optimizer='rmsprop', loss='categorical_crossentropy',
              metrics=['accuracy'])
model.fit([encoder_input_data, decoder_input_data], decoder_target_data,
          batch_size=batch_size,
          epochs=epochs,
          validation_split=0.2)
# Save model
model.save('s2s.h5')

# Next: inference mode (sampling).
# Here's the drill:
# 1) encode input and retrieve initial decoder state
# 2) run one step of decoder with this initial state
# and a "start of sequence" token as target.
# Output will be the next target token
# 3) Repeat with the current target token and current states

# Define sampling models
encoder_model = Model(encoder_inputs, encoder_states)

decoder_state_input_h = Input(shape=(latent_dim,))
decoder_state_input_c = Input(shape=(latent_dim,))
decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
decoder_outputs, state_h, state_c = decoder_lstm(
    decoder_inputs, initial_state=decoder_states_inputs)
decoder_states = [state_h, state_c]
decoder_outputs = decoder_dense(decoder_outputs)
decoder_model = Model(
    [decoder_inputs] + decoder_states_inputs,
    [decoder_outputs] + decoder_states)

# Reverse-lookup token index to decode sequences back to
# something readable.
reverse_input_char_index = dict(
    (i, char) for char, i in input_token_index.items())
reverse_target_char_index = dict(
    (i, char) for char, i in target_token_index.items())


def decode_sequence(input_seq):
    # Encode the input as state vectors.
    states_value = encoder_model.predict(input_seq)

    # Generate empty target sequence of length 1.
    target_seq = np.zeros((1, 1, num_decoder_tokens))
    # Populate the first character of target sequence with the start character.
    target_seq[0, 0, target_token_index['\t']] = 1.

    # Sampling loop for a batch of sequences
    # (to simplify, here we assume a batch of size 1).
    stop_condition = False
    decoded_sentence = ''
    while not stop_condition:
        output_tokens, h, c = decoder_model.predict(
            [target_seq] + states_value)

        # Sample a token
        sampled_token_index = np.argmax(output_tokens[0, -1, :])
        sampled_char = reverse_target_char_index[sampled_token_index]
        decoded_sentence += sampled_char

        # Exit condition: either hit max length
        # or find stop character.
        if (sampled_char == '\n' or
           len(decoded_sentence) > max_decoder_seq_length):
            stop_condition = True

        # Update the target sequence (of length 1).
        target_seq = np.zeros((1, 1, num_decoder_tokens))
        target_seq[0, 0, sampled_token_index] = 1.

        # Update states
        states_value = [h, c]

    return decoded_sentence


for seq_index in range(100):
    # Take one sequence (part of the training set)
    # for trying out decoding.
    input_seq = encoder_input_data[seq_index: seq_index + 1]
    decoded_sentence = decode_sequence(input_seq)
    print('-')
    print('Input sentence:', input_texts[seq_index])
    print('Decoded sentence:', decoded_sentence)

'''Trains a denoising autoencoder on MNIST dataset.

Denoising is one of the classic applications of autoencoders.
The denoising process removes unwanted noise that corrupted the
true signal.

Noise + Data ---> Denoising Autoencoder ---> Data

Given a training dataset of corrupted data as input and
true signal as output, a denoising autoencoder can recover the
hidden structure to generate clean data.

This example has modular design. The encoder, decoder and autoencoder
are 3 models that share weights. For example, after training the
autoencoder, the encoder can be used to  generate latent vectors
of input data for low-dim visualization like PCA or TSNE.
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import keras
from keras.layers import Activation, Dense, Input
from keras.layers import Conv2D, Flatten
from keras.layers import Reshape, Conv2DTranspose
from keras.models import Model
from keras import backend as K
from keras.datasets import mnist
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

np.random.seed(1337)

# MNIST dataset
(x_train, _), (x_test, _) = mnist.load_data()

image_size = x_train.shape[1]
x_train = np.reshape(x_train, [-1, image_size, image_size, 1])
x_test = np.reshape(x_test, [-1, image_size, image_size, 1])
x_train = x_train.astype('float32') / 255
x_test = x_test.astype('float32') / 255

# Generate corrupted MNIST images by adding noise with normal dist
# centered at 0.5 and std=0.5
noise = np.random.normal(loc=0.5, scale=0.5, size=x_train.shape)
x_train_noisy = x_train + noise
noise = np.random.normal(loc=0.5, scale=0.5, size=x_test.shape)
x_test_noisy = x_test + noise

x_train_noisy = np.clip(x_train_noisy, 0., 1.)
x_test_noisy = np.clip(x_test_noisy, 0., 1.)

# Network parameters
input_shape = (image_size, image_size, 1)
batch_size = 128
kernel_size = 3
latent_dim = 16
# Encoder/Decoder number of CNN layers and filters per layer
layer_filters = [32, 64]

# Build the Autoencoder Model
# First build the Encoder Model
inputs = Input(shape=input_shape, name='encoder_input')
x = inputs
# Stack of Conv2D blocks
# Notes:
# 1) Use Batch Normalization before ReLU on deep networks
# 2) Use MaxPooling2D as alternative to strides>1
# - faster but not as good as strides>1
for filters in layer_filters:
    x = Conv2D(filters=filters,
               kernel_size=kernel_size,
               strides=2,
               activation='relu',
               padding='same')(x)

# Shape info needed to build Decoder Model
shape = K.int_shape(x)

# Generate the latent vector
x = Flatten()(x)
latent = Dense(latent_dim, name='latent_vector')(x)

# Instantiate Encoder Model
encoder = Model(inputs, latent, name='encoder')
encoder.summary()

# Build the Decoder Model
latent_inputs = Input(shape=(latent_dim,), name='decoder_input')
x = Dense(shape[1] * shape[2] * shape[3])(latent_inputs)
x = Reshape((shape[1], shape[2], shape[3]))(x)

# Stack of Transposed Conv2D blocks
# Notes:
# 1) Use Batch Normalization before ReLU on deep networks
# 2) Use UpSampling2D as alternative to strides>1
# - faster but not as good as strides>1
for filters in layer_filters[::-1]:
    x = Conv2DTranspose(filters=filters,
                        kernel_size=kernel_size,
                        strides=2,
                        activation='relu',
                        padding='same')(x)

x = Conv2DTranspose(filters=1,
                    kernel_size=kernel_size,
                    padding='same')(x)

outputs = Activation('sigmoid', name='decoder_output')(x)

# Instantiate Decoder Model
decoder = Model(latent_inputs, outputs, name='decoder')
decoder.summary()

# Autoencoder = Encoder + Decoder
# Instantiate Autoencoder Model
autoencoder = Model(inputs, decoder(encoder(inputs)), name='autoencoder')
autoencoder.summary()

autoencoder.compile(loss='mse', optimizer='adam')

# Train the autoencoder
autoencoder.fit(x_train_noisy,
                x_train,
                validation_data=(x_test_noisy, x_test),
                epochs=30,
                batch_size=batch_size)

# Predict the Autoencoder output from corrupted test images
x_decoded = autoencoder.predict(x_test_noisy)

# Display the 1st 8 corrupted and denoised images
rows, cols = 10, 30
num = rows * cols
imgs = np.concatenate([x_test[:num], x_test_noisy[:num], x_decoded[:num]])
imgs = imgs.reshape((rows * 3, cols, image_size, image_size))
imgs = np.vstack(np.split(imgs, rows, axis=1))
imgs = imgs.reshape((rows * 3, -1, image_size, image_size))
imgs = np.vstack([np.hstack(i) for i in imgs])
imgs = (imgs * 255).astype(np.uint8)
plt.figure()
plt.axis('off')
plt.title('Original images: top rows, '
          'Corrupted Input: middle rows, '
          'Denoised Input:  third rows')
plt.imshow(imgs, interpolation='none', cmap='gray')
Image.fromarray(imgs).save('corrupted_and_denoised.png')
plt.show()

'''
#Deep Dreaming in Keras.

Run the script with:
```python
python deep_dream.py path_to_your_base_image.jpg prefix_for_results
```
e.g.:
```python
python deep_dream.py img/mypic.jpg results/dream
```
'''
from __future__ import print_function

from keras.preprocessing.image import load_img, save_img, img_to_array
import numpy as np
import scipy
import argparse

from keras.applications import inception_v3
from keras import backend as K

parser = argparse.ArgumentParser(description='Deep Dreams with Keras.')
parser.add_argument('base_image_path', metavar='base', type=str,
                    help='Path to the image to transform.')
parser.add_argument('result_prefix', metavar='res_prefix', type=str,
                    help='Prefix for the saved results.')

args = parser.parse_args()
base_image_path = args.base_image_path
result_prefix = args.result_prefix

# These are the names of the layers
# for which we try to maximize activation,
# as well as their weight in the final loss
# we try to maximize.
# You can tweak these setting to obtain new visual effects.
settings = {
    'features': {
        'mixed2': 0.2,
        'mixed3': 0.5,
        'mixed4': 2.,
        'mixed5': 1.5,
    },
}


def preprocess_image(image_path):
    # Util function to open, resize and format pictures
    # into appropriate tensors.
    img = load_img(image_path)
    img = img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = inception_v3.preprocess_input(img)
    return img


def deprocess_image(x):
    # Util function to convert a tensor into a valid image.
    if K.image_data_format() == 'channels_first':
        x = x.reshape((3, x.shape[2], x.shape[3]))
        x = x.transpose((1, 2, 0))
    else:
        x = x.reshape((x.shape[1], x.shape[2], 3))
    x /= 2.
    x += 0.5
    x *= 255.
    x = np.clip(x, 0, 255).astype('uint8')
    return x

K.set_learning_phase(0)

# Build the InceptionV3 network with our placeholder.
# The model will be loaded with pre-trained ImageNet weights.
model = inception_v3.InceptionV3(weights='imagenet',
                                 include_top=False)
dream = model.input
print('Model loaded.')

# Get the symbolic outputs of each "key" layer (we gave them unique names).
layer_dict = dict([(layer.name, layer) for layer in model.layers])

# Define the loss.
loss = K.variable(0.)
for layer_name in settings['features']:
    # Add the L2 norm of the features of a layer to the loss.
    if layer_name not in layer_dict:
        raise ValueError('Layer ' + layer_name + ' not found in model.')
    coeff = settings['features'][layer_name]
    x = layer_dict[layer_name].output
    # We avoid border artifacts by only involving non-border pixels in the loss.
    scaling = K.prod(K.cast(K.shape(x), 'float32'))
    if K.image_data_format() == 'channels_first':
        loss = loss + coeff * K.sum(K.square(x[:, :, 2: -2, 2: -2])) / scaling
    else:
        loss = loss + coeff * K.sum(K.square(x[:, 2: -2, 2: -2, :])) / scaling

# Compute the gradients of the dream wrt the loss.
grads = K.gradients(loss, dream)[0]
# Normalize gradients.
grads /= K.maximum(K.mean(K.abs(grads)), K.epsilon())

# Set up function to retrieve the value
# of the loss and gradients given an input image.
outputs = [loss, grads]
fetch_loss_and_grads = K.function([dream], outputs)


def eval_loss_and_grads(x):
    outs = fetch_loss_and_grads([x])
    loss_value = outs[0]
    grad_values = outs[1]
    return loss_value, grad_values


def resize_img(img, size):
    img = np.copy(img)
    if K.image_data_format() == 'channels_first':
        factors = (1, 1,
                   float(size[0]) / img.shape[2],
                   float(size[1]) / img.shape[3])
    else:
        factors = (1,
                   float(size[0]) / img.shape[1],
                   float(size[1]) / img.shape[2],
                   1)
    return scipy.ndimage.zoom(img, factors, order=1)


def gradient_ascent(x, iterations, step, max_loss=None):
    for i in range(iterations):
        loss_value, grad_values = eval_loss_and_grads(x)
        if max_loss is not None and loss_value > max_loss:
            break
        print('..Loss value at', i, ':', loss_value)
        x += step * grad_values
    return x


"""Process:

- Load the original image.
- Define a number of processing scales (i.e. image shapes),
    from smallest to largest.
- Resize the original image to the smallest scale.
- For every scale, starting with the smallest (i.e. current one):
    - Run gradient ascent
    - Upscale image to the next scale
    - Reinject the detail that was lost at upscaling time
- Stop when we are back to the original size.

To obtain the detail lost during upscaling, we simply
take the original image, shrink it down, upscale it,
and compare the result to the (resized) original image.
"""


# Playing with these hyperparameters will also allow you to achieve new effects
step = 0.01  # Gradient ascent step size
num_octave = 3  # Number of scales at which to run gradient ascent
octave_scale = 1.4  # Size ratio between scales
iterations = 20  # Number of ascent steps per scale
max_loss = 10.

img = preprocess_image(base_image_path)
if K.image_data_format() == 'channels_first':
    original_shape = img.shape[2:]
else:
    original_shape = img.shape[1:3]
successive_shapes = [original_shape]
for i in range(1, num_octave):
    shape = tuple([int(dim / (octave_scale ** i)) for dim in original_shape])
    successive_shapes.append(shape)
successive_shapes = successive_shapes[::-1]
original_img = np.copy(img)
shrunk_original_img = resize_img(img, successive_shapes[0])

for shape in successive_shapes:
    print('Processing image shape', shape)
    img = resize_img(img, shape)
    img = gradient_ascent(img,
                          iterations=iterations,
                          step=step,
                          max_loss=max_loss)
    upscaled_shrunk_original_img = resize_img(shrunk_original_img, shape)
    same_size_original = resize_img(original_img, shape)
    lost_detail = same_size_original - upscaled_shrunk_original_img

    img += lost_detail
    shrunk_original_img = resize_img(original_img, shape)

save_img(result_prefix + '.png', deprocess_image(np.copy(img)))

'''Trains and evaluate a simple MLP
on the Reuters newswire topic classification task.
'''
from __future__ import print_function

import numpy as np
import keras
from keras.datasets import reuters
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from keras.preprocessing.text import Tokenizer

max_words = 1000
batch_size = 32
epochs = 5

print('Loading data...')
(x_train, y_train), (x_test, y_test) = reuters.load_data(num_words=max_words,
                                                         test_split=0.2)
print(len(x_train), 'train sequences')
print(len(x_test), 'test sequences')

num_classes = np.max(y_train) + 1
print(num_classes, 'classes')

print('Vectorizing sequence data...')
tokenizer = Tokenizer(num_words=max_words)
x_train = tokenizer.sequences_to_matrix(x_train, mode='binary')
x_test = tokenizer.sequences_to_matrix(x_test, mode='binary')
print('x_train shape:', x_train.shape)
print('x_test shape:', x_test.shape)

print('Convert class vector to binary class matrix '
      '(for use with categorical_crossentropy)')
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)
print('y_train shape:', y_train.shape)
print('y_test shape:', y_test.shape)

print('Building model...')
model = Sequential()
model.add(Dense(512, input_shape=(max_words,)))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

history = model.fit(x_train, y_train,
                    batch_size=batch_size,
                    epochs=epochs,
                    verbose=1,
                    validation_split=0.1)
score = model.evaluate(x_test, y_test,
                       batch_size=batch_size, verbose=1)
print('Test score:', score[0])
print('Test accuracy:', score[1])

# -*- coding: utf-8 -*-
'''
# An implementation of sequence to sequence learning for performing addition

Input: "535+61"
Output: "596"
Padding is handled by using a repeated sentinel character (space)

Input may optionally be reversed, shown to increase performance in many tasks in:
"Learning to Execute"
http://arxiv.org/abs/1410.4615
and
"Sequence to Sequence Learning with Neural Networks"
http://papers.nips.cc/paper/5346-sequence-to-sequence-learning-with-neural-networks.pdf
Theoretically it introduces shorter term dependencies between source and target.

Two digits reversed:
+ One layer LSTM (128 HN), 5k training examples = 99% train/test accuracy in 55 epochs

Three digits reversed:
+ One layer LSTM (128 HN), 50k training examples = 99% train/test accuracy in 100 epochs

Four digits reversed:
+ One layer LSTM (128 HN), 400k training examples = 99% train/test accuracy in 20 epochs

Five digits reversed:
+ One layer LSTM (128 HN), 550k training examples = 99% train/test accuracy in 30 epochs
'''  # noqa

from __future__ import print_function
from keras.models import Sequential
from keras import layers
import numpy as np
from six.moves import range


class CharacterTable(object):
    """Given a set of characters:
    + Encode them to a one-hot integer representation
    + Decode the one-hot or integer representation to their character output
    + Decode a vector of probabilities to their character output
    """
    def __init__(self, chars):
        """Initialize character table.

        # Arguments
            chars: Characters that can appear in the input.
        """
        self.chars = sorted(set(chars))
        self.char_indices = dict((c, i) for i, c in enumerate(self.chars))
        self.indices_char = dict((i, c) for i, c in enumerate(self.chars))

    def encode(self, C, num_rows):
        """One-hot encode given string C.

        # Arguments
            C: string, to be encoded.
            num_rows: Number of rows in the returned one-hot encoding. This is
                used to keep the # of rows for each data the same.
        """
        x = np.zeros((num_rows, len(self.chars)))
        for i, c in enumerate(C):
            x[i, self.char_indices[c]] = 1
        return x

    def decode(self, x, calc_argmax=True):
        """Decode the given vector or 2D array to their character output.

        # Arguments
            x: A vector or a 2D array of probabilities or one-hot representations;
                or a vector of character indices (used with `calc_argmax=False`).
            calc_argmax: Whether to find the character index with maximum
                probability, defaults to `True`.
        """
        if calc_argmax:
            x = x.argmax(axis=-1)
        return ''.join(self.indices_char[x] for x in x)


class colors:
    ok = '\033[92m'
    fail = '\033[91m'
    close = '\033[0m'

# Parameters for the model and dataset.
TRAINING_SIZE = 50000
DIGITS = 3
REVERSE = True

# Maximum length of input is 'int + int' (e.g., '345+678'). Maximum length of
# int is DIGITS.
MAXLEN = DIGITS + 1 + DIGITS

# All the numbers, plus sign and space for padding.
chars = '0123456789+ '
ctable = CharacterTable(chars)

questions = []
expected = []
seen = set()
print('Generating data...')
while len(questions) < TRAINING_SIZE:
    f = lambda: int(''.join(np.random.choice(list('0123456789'))
                    for i in range(np.random.randint(1, DIGITS + 1))))
    a, b = f(), f()
    # Skip any addition questions we've already seen
    # Also skip any such that x+Y == Y+x (hence the sorting).
    key = tuple(sorted((a, b)))
    if key in seen:
        continue
    seen.add(key)
    # Pad the data with spaces such that it is always MAXLEN.
    q = '{}+{}'.format(a, b)
    query = q + ' ' * (MAXLEN - len(q))
    ans = str(a + b)
    # Answers can be of maximum size DIGITS + 1.
    ans += ' ' * (DIGITS + 1 - len(ans))
    if REVERSE:
        # Reverse the query, e.g., '12+345  ' becomes '  543+21'. (Note the
        # space used for padding.)
        query = query[::-1]
    questions.append(query)
    expected.append(ans)
print('Total addition questions:', len(questions))

print('Vectorization...')
x = np.zeros((len(questions), MAXLEN, len(chars)), dtype=np.bool)
y = np.zeros((len(questions), DIGITS + 1, len(chars)), dtype=np.bool)
for i, sentence in enumerate(questions):
    x[i] = ctable.encode(sentence, MAXLEN)
for i, sentence in enumerate(expected):
    y[i] = ctable.encode(sentence, DIGITS + 1)

# Shuffle (x, y) in unison as the later parts of x will almost all be larger
# digits.
indices = np.arange(len(y))
np.random.shuffle(indices)
x = x[indices]
y = y[indices]

# Explicitly set apart 10% for validation data that we never train over.
split_at = len(x) - len(x) // 10
(x_train, x_val) = x[:split_at], x[split_at:]
(y_train, y_val) = y[:split_at], y[split_at:]

print('Training Data:')
print(x_train.shape)
print(y_train.shape)

print('Validation Data:')
print(x_val.shape)
print(y_val.shape)

# Try replacing GRU, or SimpleRNN.
RNN = layers.LSTM
HIDDEN_SIZE = 128
BATCH_SIZE = 128
LAYERS = 1

print('Build model...')
model = Sequential()
# "Encode" the input sequence using an RNN, producing an output of HIDDEN_SIZE.
# Note: In a situation where your input sequences have a variable length,
# use input_shape=(None, num_feature).
model.add(RNN(HIDDEN_SIZE, input_shape=(MAXLEN, len(chars))))
# As the decoder RNN's input, repeatedly provide with the last output of
# RNN for each time step. Repeat 'DIGITS + 1' times as that's the maximum
# length of output, e.g., when DIGITS=3, max output is 999+999=1998.
model.add(layers.RepeatVector(DIGITS + 1))
# The decoder RNN could be multiple layers stacked or a single layer.
for _ in range(LAYERS):
    # By setting return_sequences to True, return not only the last output but
    # all the outputs so far in the form of (num_samples, timesteps,
    # output_dim). This is necessary as TimeDistributed in the below expects
    # the first dimension to be the timesteps.
    model.add(RNN(HIDDEN_SIZE, return_sequences=True))

# Apply a dense layer to the every temporal slice of an input. For each of step
# of the output sequence, decide which character should be chosen.
model.add(layers.TimeDistributed(layers.Dense(len(chars), activation='softmax')))
model.compile(loss='categorical_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])
model.summary()

# Train the model each generation and show predictions against the validation
# dataset.
for iteration in range(1, 200):
    print()
    print('-' * 50)
    print('Iteration', iteration)
    model.fit(x_train, y_train,
              batch_size=BATCH_SIZE,
              epochs=1,
              validation_data=(x_val, y_val))
    # Select 10 samples from the validation set at random so we can visualize
    # errors.
    for i in range(10):
        ind = np.random.randint(0, len(x_val))
        rowx, rowy = x_val[np.array([ind])], y_val[np.array([ind])]
        preds = model.predict_classes(rowx, verbose=0)
        q = ctable.decode(rowx[0])
        correct = ctable.decode(rowy[0])
        guess = ctable.decode(preds[0], calc_argmax=False)
        print('Q', q[::-1] if REVERSE else q, end=' ')
        print('T', correct, end=' ')
        if correct == guess:
            print(colors.ok + 'â˜‘' + colors.close, end=' ')
        else:
            print(colors.fail + 'â˜’' + colors.close, end=' ')
        print(guess)

'''
#Trains a memory network on the bAbI dataset.

References:

- Jason Weston, Antoine Bordes, Sumit Chopra, Tomas Mikolov, Alexander M. Rush,
  ["Towards AI-Complete Question Answering:
  A Set of Prerequisite Toy Tasks"](http://arxiv.org/abs/1502.05698)

- Sainbayar Sukhbaatar, Arthur Szlam, Jason Weston, Rob Fergus,
  ["End-To-End Memory Networks"](http://arxiv.org/abs/1503.08895)

Reaches 98.6% accuracy on task 'single_supporting_fact_10k' after 120 epochs.
Time per epoch: 3s on CPU (core i7).
'''
from __future__ import print_function

from keras.models import Sequential, Model
from keras.layers.embeddings import Embedding
from keras.layers import Input, Activation, Dense, Permute, Dropout
from keras.layers import add, dot, concatenate
from keras.layers import LSTM
from keras.utils.data_utils import get_file
from keras.preprocessing.sequence import pad_sequences
from functools import reduce
import tarfile
import numpy as np
import re


def tokenize(sent):
    '''Return the tokens of a sentence including punctuation.

    >>> tokenize('Bob dropped the apple. Where is the apple?')
    ['Bob', 'dropped', 'the', 'apple', '.', 'Where', 'is', 'the', 'apple', '?']
    '''
    return [x.strip() for x in re.split(r'(\W+)?', sent) if x.strip()]


def parse_stories(lines, only_supporting=False):
    '''Parse stories provided in the bAbi tasks format

    If only_supporting is true, only the sentences
    that support the answer are kept.
    '''
    data = []
    story = []
    for line in lines:
        line = line.decode('utf-8').strip()
        nid, line = line.split(' ', 1)
        nid = int(nid)
        if nid == 1:
            story = []
        if '\t' in line:
            q, a, supporting = line.split('\t')
            q = tokenize(q)
            if only_supporting:
                # Only select the related substory
                supporting = map(int, supporting.split())
                substory = [story[i - 1] for i in supporting]
            else:
                # Provide all the substories
                substory = [x for x in story if x]
            data.append((substory, q, a))
            story.append('')
        else:
            sent = tokenize(line)
            story.append(sent)
    return data


def get_stories(f, only_supporting=False, max_length=None):
    '''Given a file name, read the file,
    retrieve the stories,
    and then convert the sentences into a single story.

    If max_length is supplied,
    any stories longer than max_length tokens will be discarded.
    '''
    data = parse_stories(f.readlines(), only_supporting=only_supporting)
    flatten = lambda data: reduce(lambda x, y: x + y, data)
    data = [(flatten(story), q, answer) for story, q, answer in data
            if not max_length or len(flatten(story)) < max_length]
    return data


def vectorize_stories(data):
    inputs, queries, answers = [], [], []
    for story, query, answer in data:
        inputs.append([word_idx[w] for w in story])
        queries.append([word_idx[w] for w in query])
        answers.append(word_idx[answer])
    return (pad_sequences(inputs, maxlen=story_maxlen),
            pad_sequences(queries, maxlen=query_maxlen),
            np.array(answers))

try:
    path = get_file('babi-tasks-v1-2.tar.gz',
                    origin='https://s3.amazonaws.com/text-datasets/'
                           'babi_tasks_1-20_v1-2.tar.gz')
except:
    print('Error downloading dataset, please download it manually:\n'
          '$ wget http://www.thespermwhale.com/jaseweston/babi/tasks_1-20_v1-2'
          '.tar.gz\n'
          '$ mv tasks_1-20_v1-2.tar.gz ~/.keras/datasets/babi-tasks-v1-2.tar.gz')
    raise


challenges = {
    # QA1 with 10,000 samples
    'single_supporting_fact_10k': 'tasks_1-20_v1-2/en-10k/qa1_'
                                  'single-supporting-fact_{}.txt',
    # QA2 with 10,000 samples
    'two_supporting_facts_10k': 'tasks_1-20_v1-2/en-10k/qa2_'
                                'two-supporting-facts_{}.txt',
}
challenge_type = 'single_supporting_fact_10k'
challenge = challenges[challenge_type]

print('Extracting stories for the challenge:', challenge_type)
with tarfile.open(path) as tar:
    train_stories = get_stories(tar.extractfile(challenge.format('train')))
    test_stories = get_stories(tar.extractfile(challenge.format('test')))

vocab = set()
for story, q, answer in train_stories + test_stories:
    vocab |= set(story + q + [answer])
vocab = sorted(vocab)

# Reserve 0 for masking via pad_sequences
vocab_size = len(vocab) + 1
story_maxlen = max(map(len, (x for x, _, _ in train_stories + test_stories)))
query_maxlen = max(map(len, (x for _, x, _ in train_stories + test_stories)))

print('-')
print('Vocab size:', vocab_size, 'unique words')
print('Story max length:', story_maxlen, 'words')
print('Query max length:', query_maxlen, 'words')
print('Number of training stories:', len(train_stories))
print('Number of test stories:', len(test_stories))
print('-')
print('Here\'s what a "story" tuple looks like (input, query, answer):')
print(train_stories[0])
print('-')
print('Vectorizing the word sequences...')

word_idx = dict((c, i + 1) for i, c in enumerate(vocab))
inputs_train, queries_train, answers_train = vectorize_stories(train_stories)
inputs_test, queries_test, answers_test = vectorize_stories(test_stories)

print('-')
print('inputs: integer tensor of shape (samples, max_length)')
print('inputs_train shape:', inputs_train.shape)
print('inputs_test shape:', inputs_test.shape)
print('-')
print('queries: integer tensor of shape (samples, max_length)')
print('queries_train shape:', queries_train.shape)
print('queries_test shape:', queries_test.shape)
print('-')
print('answers: binary (1 or 0) tensor of shape (samples, vocab_size)')
print('answers_train shape:', answers_train.shape)
print('answers_test shape:', answers_test.shape)
print('-')
print('Compiling...')

# placeholders
input_sequence = Input((story_maxlen,))
question = Input((query_maxlen,))

# encoders
# embed the input sequence into a sequence of vectors
input_encoder_m = Sequential()
input_encoder_m.add(Embedding(input_dim=vocab_size,
                              output_dim=64))
input_encoder_m.add(Dropout(0.3))
# output: (samples, story_maxlen, embedding_dim)

# embed the input into a sequence of vectors of size query_maxlen
input_encoder_c = Sequential()
input_encoder_c.add(Embedding(input_dim=vocab_size,
                              output_dim=query_maxlen))
input_encoder_c.add(Dropout(0.3))
# output: (samples, story_maxlen, query_maxlen)

# embed the question into a sequence of vectors
question_encoder = Sequential()
question_encoder.add(Embedding(input_dim=vocab_size,
                               output_dim=64,
                               input_length=query_maxlen))
question_encoder.add(Dropout(0.3))
# output: (samples, query_maxlen, embedding_dim)

# encode input sequence and questions (which are indices)
# to sequences of dense vectors
input_encoded_m = input_encoder_m(input_sequence)
input_encoded_c = input_encoder_c(input_sequence)
question_encoded = question_encoder(question)

# compute a 'match' between the first input vector sequence
# and the question vector sequence
# shape: `(samples, story_maxlen, query_maxlen)`
match = dot([input_encoded_m, question_encoded], axes=(2, 2))
match = Activation('softmax')(match)

# add the match matrix with the second input vector sequence
response = add([match, input_encoded_c])  # (samples, story_maxlen, query_maxlen)
response = Permute((2, 1))(response)  # (samples, query_maxlen, story_maxlen)

# concatenate the match matrix with the question vector sequence
answer = concatenate([response, question_encoded])

# the original paper uses a matrix multiplication for this reduction step.
# we choose to use a RNN instead.
answer = LSTM(32)(answer)  # (samples, 32)

# one regularization layer -- more would probably be needed.
answer = Dropout(0.3)(answer)
answer = Dense(vocab_size)(answer)  # (samples, vocab_size)
# we output a probability distribution over the vocabulary
answer = Activation('softmax')(answer)

# build the final model
model = Model([input_sequence, question], answer)
model.compile(optimizer='rmsprop', loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# train
model.fit([inputs_train, queries_train], answers_train,
          batch_size=32,
          epochs=120,
          validation_data=([inputs_test, queries_test], answers_test))

# -*- coding: utf-8 -*-
'''
# Optical character recognition
This example uses a convolutional stack followed by a recurrent stack
and a CTC logloss function to perform optical character recognition
of generated text images. I have no evidence of whether it actually
learns general shapes of text, or just is able to recognize all
the different fonts thrown at it...the purpose is more to demonstrate CTC
inside of Keras.  Note that the font list may need to be updated
for the particular OS in use.

This starts off with 4 letter words.  For the first 12 epochs, the
difficulty is gradually increased using the TextImageGenerator class
which is both a generator class for test/train data and a Keras
callback class. After 20 epochs, longer sequences are thrown at it
by recompiling the model to handle a wider image and rebuilding
the word list to include two words separated by a space.

The table below shows normalized edit distance values. Theano uses
a slightly different CTC implementation, hence the different results.

Epoch |   TF   |   TH
-----:|-------:|-------:
    10|  0.027 | 0.064
    15|  0.038 | 0.035
    20|  0.043 | 0.045
    25|  0.014 | 0.019

# Additional dependencies

This requires ```cairo``` and ```editdistance``` packages:

First, install the Cairo library: https://cairographics.org/

Then install Python dependencies:

```python
pip install cairocffi
pip install editdistance
```

Created by Mike Henry
https://github.com/mbhenry/
'''
import os
import itertools
import codecs
import re
import datetime
import cairocffi as cairo
import editdistance
import numpy as np
from scipy import ndimage
import pylab
from keras import backend as K
from keras.layers.convolutional import Conv2D, MaxPooling2D
from keras.layers import Input, Dense, Activation
from keras.layers import Reshape, Lambda
from keras.layers.merge import add, concatenate
from keras.models import Model
from keras.layers.recurrent import GRU
from keras.optimizers import SGD
from keras.utils.data_utils import get_file
from keras.preprocessing import image
import keras.callbacks


OUTPUT_DIR = 'image_ocr'

# character classes and matching regex filter
regex = r'^[a-z ]+$'
alphabet = u'abcdefghijklmnopqrstuvwxyz '

np.random.seed(55)


# this creates larger "blotches" of noise which look
# more realistic than just adding gaussian noise
# assumes greyscale with pixels ranging from 0 to 1

def speckle(img):
    severity = np.random.uniform(0, 0.6)
    blur = ndimage.gaussian_filter(np.random.randn(*img.shape) * severity, 1)
    img_speck = (img + blur)
    img_speck[img_speck > 1] = 1
    img_speck[img_speck <= 0] = 0
    return img_speck


# paints the string in a random location the bounding box
# also uses a random font, a slight random rotation,
# and a random amount of speckle noise

def paint_text(text, w, h, rotate=False, ud=False, multi_fonts=False):
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
    with cairo.Context(surface) as context:
        context.set_source_rgb(1, 1, 1)  # White
        context.paint()
        # this font list works in CentOS 7
        if multi_fonts:
            fonts = [
                'Century Schoolbook', 'Courier', 'STIX',
                'URW Chancery L', 'FreeMono']
            context.select_font_face(
                np.random.choice(fonts),
                cairo.FONT_SLANT_NORMAL,
                np.random.choice([cairo.FONT_WEIGHT_BOLD, cairo.FONT_WEIGHT_NORMAL]))
        else:
            context.select_font_face('Courier',
                                     cairo.FONT_SLANT_NORMAL,
                                     cairo.FONT_WEIGHT_BOLD)
        context.set_font_size(25)
        box = context.text_extents(text)
        border_w_h = (4, 4)
        if box[2] > (w - 2 * border_w_h[1]) or box[3] > (h - 2 * border_w_h[0]):
            raise IOError(('Could not fit string into image.'
                           'Max char count is too large for given image width.'))

        # teach the RNN translational invariance by
        # fitting text box randomly on canvas, with some room to rotate
        max_shift_x = w - box[2] - border_w_h[0]
        max_shift_y = h - box[3] - border_w_h[1]
        top_left_x = np.random.randint(0, int(max_shift_x))
        if ud:
            top_left_y = np.random.randint(0, int(max_shift_y))
        else:
            top_left_y = h // 2
        context.move_to(top_left_x - int(box[0]), top_left_y - int(box[1]))
        context.set_source_rgb(0, 0, 0)
        context.show_text(text)

    buf = surface.get_data()
    a = np.frombuffer(buf, np.uint8)
    a.shape = (h, w, 4)
    a = a[:, :, 0]  # grab single channel
    a = a.astype(np.float32) / 255
    a = np.expand_dims(a, 0)
    if rotate:
        a = image.random_rotation(a, 3 * (w - top_left_x) / w + 1)
    a = speckle(a)

    return a


def shuffle_mats_or_lists(matrix_list, stop_ind=None):
    ret = []
    assert all([len(i) == len(matrix_list[0]) for i in matrix_list])
    len_val = len(matrix_list[0])
    if stop_ind is None:
        stop_ind = len_val
    assert stop_ind <= len_val

    a = list(range(stop_ind))
    np.random.shuffle(a)
    a += list(range(stop_ind, len_val))
    for mat in matrix_list:
        if isinstance(mat, np.ndarray):
            ret.append(mat[a])
        elif isinstance(mat, list):
            ret.append([mat[i] for i in a])
        else:
            raise TypeError('`shuffle_mats_or_lists` only supports '
                            'numpy.array and list objects.')
    return ret


# Translation of characters to unique integer values
def text_to_labels(text):
    ret = []
    for char in text:
        ret.append(alphabet.find(char))
    return ret


# Reverse translation of numerical classes back to characters
def labels_to_text(labels):
    ret = []
    for c in labels:
        if c == len(alphabet):  # CTC Blank
            ret.append("")
        else:
            ret.append(alphabet[c])
    return "".join(ret)


# only a-z and space..probably not to difficult
# to expand to uppercase and symbols

def is_valid_str(in_str):
    search = re.compile(regex, re.UNICODE).search
    return bool(search(in_str))


# Uses generator functions to supply train/test with
# data. Image renderings and text are created on the fly
# each time with random perturbations

class TextImageGenerator(keras.callbacks.Callback):

    def __init__(self, monogram_file, bigram_file, minibatch_size,
                 img_w, img_h, downsample_factor, val_split,
                 absolute_max_string_len=16):

        self.minibatch_size = minibatch_size
        self.img_w = img_w
        self.img_h = img_h
        self.monogram_file = monogram_file
        self.bigram_file = bigram_file
        self.downsample_factor = downsample_factor
        self.val_split = val_split
        self.blank_label = self.get_output_size() - 1
        self.absolute_max_string_len = absolute_max_string_len

    def get_output_size(self):
        return len(alphabet) + 1

    # num_words can be independent of the epoch size due to the use of generators
    # as max_string_len grows, num_words can grow
    def build_word_list(self, num_words, max_string_len=None, mono_fraction=0.5):
        assert max_string_len <= self.absolute_max_string_len
        assert num_words % self.minibatch_size == 0
        assert (self.val_split * num_words) % self.minibatch_size == 0
        self.num_words = num_words
        self.string_list = [''] * self.num_words
        tmp_string_list = []
        self.max_string_len = max_string_len
        self.Y_data = np.ones([self.num_words, self.absolute_max_string_len]) * -1
        self.X_text = []
        self.Y_len = [0] * self.num_words

        def _is_length_of_word_valid(word):
            return (max_string_len == -1 or
                    max_string_len is None or
                    len(word) <= max_string_len)

        # monogram file is sorted by frequency in english speech
        with codecs.open(self.monogram_file, mode='r', encoding='utf-8') as f:
            for line in f:
                if len(tmp_string_list) == int(self.num_words * mono_fraction):
                    break
                word = line.rstrip()
                if _is_length_of_word_valid(word):
                    tmp_string_list.append(word)

        # bigram file contains common word pairings in english speech
        with codecs.open(self.bigram_file, mode='r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if len(tmp_string_list) == self.num_words:
                    break
                columns = line.lower().split()
                word = columns[0] + ' ' + columns[1]
                if is_valid_str(word) and _is_length_of_word_valid(word):
                    tmp_string_list.append(word)
        if len(tmp_string_list) != self.num_words:
            raise IOError('Could not pull enough words'
                          'from supplied monogram and bigram files.')
        # interlace to mix up the easy and hard words
        self.string_list[::2] = tmp_string_list[:self.num_words // 2]
        self.string_list[1::2] = tmp_string_list[self.num_words // 2:]

        for i, word in enumerate(self.string_list):
            self.Y_len[i] = len(word)
            self.Y_data[i, 0:len(word)] = text_to_labels(word)
            self.X_text.append(word)
        self.Y_len = np.expand_dims(np.array(self.Y_len), 1)

        self.cur_val_index = self.val_split
        self.cur_train_index = 0

    # each time an image is requested from train/val/test, a new random
    # painting of the text is performed
    def get_batch(self, index, size, train):
        # width and height are backwards from typical Keras convention
        # because width is the time dimension when it gets fed into the RNN
        if K.image_data_format() == 'channels_first':
            X_data = np.ones([size, 1, self.img_w, self.img_h])
        else:
            X_data = np.ones([size, self.img_w, self.img_h, 1])

        labels = np.ones([size, self.absolute_max_string_len])
        input_length = np.zeros([size, 1])
        label_length = np.zeros([size, 1])
        source_str = []
        for i in range(size):
            # Mix in some blank inputs.  This seems to be important for
            # achieving translational invariance
            if train and i > size - 4:
                if K.image_data_format() == 'channels_first':
                    X_data[i, 0, 0:self.img_w, :] = self.paint_func('')[0, :, :].T
                else:
                    X_data[i, 0:self.img_w, :, 0] = self.paint_func('',)[0, :, :].T
                labels[i, 0] = self.blank_label
                input_length[i] = self.img_w // self.downsample_factor - 2
                label_length[i] = 1
                source_str.append('')
            else:
                if K.image_data_format() == 'channels_first':
                    X_data[i, 0, 0:self.img_w, :] = (
                        self.paint_func(self.X_text[index + i])[0, :, :].T)
                else:
                    X_data[i, 0:self.img_w, :, 0] = (
                        self.paint_func(self.X_text[index + i])[0, :, :].T)
                labels[i, :] = self.Y_data[index + i]
                input_length[i] = self.img_w // self.downsample_factor - 2
                label_length[i] = self.Y_len[index + i]
                source_str.append(self.X_text[index + i])
        inputs = {'the_input': X_data,
                  'the_labels': labels,
                  'input_length': input_length,
                  'label_length': label_length,
                  'source_str': source_str  # used for visualization only
                  }
        outputs = {'ctc': np.zeros([size])}  # dummy data for dummy loss function
        return (inputs, outputs)

    def next_train(self):
        while 1:
            ret = self.get_batch(self.cur_train_index,
                                 self.minibatch_size, train=True)
            self.cur_train_index += self.minibatch_size
            if self.cur_train_index >= self.val_split:
                self.cur_train_index = self.cur_train_index % 32
                (self.X_text, self.Y_data, self.Y_len) = shuffle_mats_or_lists(
                    [self.X_text, self.Y_data, self.Y_len], self.val_split)
            yield ret

    def next_val(self):
        while 1:
            ret = self.get_batch(self.cur_val_index,
                                 self.minibatch_size, train=False)
            self.cur_val_index += self.minibatch_size
            if self.cur_val_index >= self.num_words:
                self.cur_val_index = self.val_split + self.cur_val_index % 32
            yield ret

    def on_train_begin(self, logs={}):
        self.build_word_list(16000, 4, 1)
        self.paint_func = lambda text: paint_text(
            text, self.img_w, self.img_h,
            rotate=False, ud=False, multi_fonts=False)

    def on_epoch_begin(self, epoch, logs={}):
        # rebind the paint function to implement curriculum learning
        if 3 <= epoch < 6:
            self.paint_func = lambda text: paint_text(
                text, self.img_w, self.img_h,
                rotate=False, ud=True, multi_fonts=False)
        elif 6 <= epoch < 9:
            self.paint_func = lambda text: paint_text(
                text, self.img_w, self.img_h,
                rotate=False, ud=True, multi_fonts=True)
        elif epoch >= 9:
            self.paint_func = lambda text: paint_text(
                text, self.img_w, self.img_h,
                rotate=True, ud=True, multi_fonts=True)
        if epoch >= 21 and self.max_string_len < 12:
            self.build_word_list(32000, 12, 0.5)


# the actual loss calc occurs here despite it not being
# an internal Keras loss function

def ctc_lambda_func(args):
    y_pred, labels, input_length, label_length = args
    # the 2 is critical here since the first couple outputs of the RNN
    # tend to be garbage:
    y_pred = y_pred[:, 2:, :]
    return K.ctc_batch_cost(labels, y_pred, input_length, label_length)


# For a real OCR application, this should be beam search with a dictionary
# and language model.  For this example, best path is sufficient.

def decode_batch(test_func, word_batch):
    out = test_func([word_batch])[0]
    ret = []
    for j in range(out.shape[0]):
        out_best = list(np.argmax(out[j, 2:], 1))
        out_best = [k for k, g in itertools.groupby(out_best)]
        outstr = labels_to_text(out_best)
        ret.append(outstr)
    return ret


class VizCallback(keras.callbacks.Callback):

    def __init__(self, run_name, test_func, text_img_gen, num_display_words=6):
        self.test_func = test_func
        self.output_dir = os.path.join(
            OUTPUT_DIR, run_name)
        self.text_img_gen = text_img_gen
        self.num_display_words = num_display_words
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def show_edit_distance(self, num):
        num_left = num
        mean_norm_ed = 0.0
        mean_ed = 0.0
        while num_left > 0:
            word_batch = next(self.text_img_gen)[0]
            num_proc = min(word_batch['the_input'].shape[0], num_left)
            decoded_res = decode_batch(self.test_func,
                                       word_batch['the_input'][0:num_proc])
            for j in range(num_proc):
                edit_dist = editdistance.eval(decoded_res[j],
                                              word_batch['source_str'][j])
                mean_ed += float(edit_dist)
                mean_norm_ed += float(edit_dist) / len(word_batch['source_str'][j])
            num_left -= num_proc
        mean_norm_ed = mean_norm_ed / num
        mean_ed = mean_ed / num
        print('\nOut of %d samples:  Mean edit distance:'
              '%.3f Mean normalized edit distance: %0.3f'
              % (num, mean_ed, mean_norm_ed))

    def on_epoch_end(self, epoch, logs={}):
        self.model.save_weights(
            os.path.join(self.output_dir, 'weights%02d.h5' % (epoch)))
        self.show_edit_distance(256)
        word_batch = next(self.text_img_gen)[0]
        res = decode_batch(self.test_func,
                           word_batch['the_input'][0:self.num_display_words])
        if word_batch['the_input'][0].shape[0] < 256:
            cols = 2
        else:
            cols = 1
        for i in range(self.num_display_words):
            pylab.subplot(self.num_display_words // cols, cols, i + 1)
            if K.image_data_format() == 'channels_first':
                the_input = word_batch['the_input'][i, 0, :, :]
            else:
                the_input = word_batch['the_input'][i, :, :, 0]
            pylab.imshow(the_input.T, cmap='Greys_r')
            pylab.xlabel(
                'Truth = \'%s\'\nDecoded = \'%s\'' %
                (word_batch['source_str'][i], res[i]))
        fig = pylab.gcf()
        fig.set_size_inches(10, 13)
        pylab.savefig(os.path.join(self.output_dir, 'e%02d.png' % (epoch)))
        pylab.close()


def train(run_name, start_epoch, stop_epoch, img_w):
    # Input Parameters
    img_h = 64
    words_per_epoch = 16000
    val_split = 0.2
    val_words = int(words_per_epoch * (val_split))

    # Network parameters
    conv_filters = 16
    kernel_size = (3, 3)
    pool_size = 2
    time_dense_size = 32
    rnn_size = 512
    minibatch_size = 32

    if K.image_data_format() == 'channels_first':
        input_shape = (1, img_w, img_h)
    else:
        input_shape = (img_w, img_h, 1)

    fdir = os.path.dirname(
        get_file('wordlists.tgz',
                 origin='http://www.mythic-ai.com/datasets/wordlists.tgz',
                 untar=True))

    img_gen = TextImageGenerator(
        monogram_file=os.path.join(fdir, 'wordlist_mono_clean.txt'),
        bigram_file=os.path.join(fdir, 'wordlist_bi_clean.txt'),
        minibatch_size=minibatch_size,
        img_w=img_w,
        img_h=img_h,
        downsample_factor=(pool_size ** 2),
        val_split=words_per_epoch - val_words)
    act = 'relu'
    input_data = Input(name='the_input', shape=input_shape, dtype='float32')
    inner = Conv2D(conv_filters, kernel_size, padding='same',
                   activation=act, kernel_initializer='he_normal',
                   name='conv1')(input_data)
    inner = MaxPooling2D(pool_size=(pool_size, pool_size), name='max1')(inner)
    inner = Conv2D(conv_filters, kernel_size, padding='same',
                   activation=act, kernel_initializer='he_normal',
                   name='conv2')(inner)
    inner = MaxPooling2D(pool_size=(pool_size, pool_size), name='max2')(inner)

    conv_to_rnn_dims = (img_w // (pool_size ** 2),
                        (img_h // (pool_size ** 2)) * conv_filters)
    inner = Reshape(target_shape=conv_to_rnn_dims, name='reshape')(inner)

    # cuts down input size going into RNN:
    inner = Dense(time_dense_size, activation=act, name='dense1')(inner)

    # Two layers of bidirectional GRUs
    # GRU seems to work as well, if not better than LSTM:
    gru_1 = GRU(rnn_size, return_sequences=True,
                kernel_initializer='he_normal', name='gru1')(inner)
    gru_1b = GRU(rnn_size, return_sequences=True,
                 go_backwards=True, kernel_initializer='he_normal',
                 name='gru1_b')(inner)
    gru1_merged = add([gru_1, gru_1b])
    gru_2 = GRU(rnn_size, return_sequences=True,
                kernel_initializer='he_normal', name='gru2')(gru1_merged)
    gru_2b = GRU(rnn_size, return_sequences=True, go_backwards=True,
                 kernel_initializer='he_normal', name='gru2_b')(gru1_merged)

    # transforms RNN output to character activations:
    inner = Dense(img_gen.get_output_size(), kernel_initializer='he_normal',
                  name='dense2')(concatenate([gru_2, gru_2b]))
    y_pred = Activation('softmax', name='softmax')(inner)
    Model(inputs=input_data, outputs=y_pred).summary()

    labels = Input(name='the_labels',
                   shape=[img_gen.absolute_max_string_len], dtype='float32')
    input_length = Input(name='input_length', shape=[1], dtype='int64')
    label_length = Input(name='label_length', shape=[1], dtype='int64')
    # Keras doesn't currently support loss funcs with extra parameters
    # so CTC loss is implemented in a lambda layer
    loss_out = Lambda(
        ctc_lambda_func, output_shape=(1,),
        name='ctc')([y_pred, labels, input_length, label_length])

    # clipnorm seems to speeds up convergence
    sgd = SGD(learning_rate=0.02,
              decay=1e-6,
              momentum=0.9,
              nesterov=True)

    model = Model(inputs=[input_data, labels, input_length, label_length],
                  outputs=loss_out)

    # the loss calc occurs elsewhere, so use a dummy lambda func for the loss
    model.compile(loss={'ctc': lambda y_true, y_pred: y_pred}, optimizer=sgd)
    if start_epoch > 0:
        weight_file = os.path.join(
            OUTPUT_DIR,
            os.path.join(run_name, 'weights%02d.h5' % (start_epoch - 1)))
        model.load_weights(weight_file)
    # captures output of softmax so we can decode the output during visualization
    test_func = K.function([input_data], [y_pred])

    viz_cb = VizCallback(run_name, test_func, img_gen.next_val())

    model.fit_generator(
        generator=img_gen.next_train(),
        steps_per_epoch=(words_per_epoch - val_words) // minibatch_size,
        epochs=stop_epoch,
        validation_data=img_gen.next_val(),
        validation_steps=val_words // minibatch_size,
        callbacks=[viz_cb, img_gen],
        initial_epoch=start_epoch)


if __name__ == '__main__':
    run_name = datetime.datetime.now().strftime('%Y:%m:%d:%H:%M:%S')
    train(run_name, 0, 20, 128)
    # increase to wider images and start at epoch 20.
    # The learned weights are reloaded
    train(run_name, 20, 25, 512)

'''Trains a Siamese MLP on pairs of digits from the MNIST dataset.

It follows Hadsell-et-al.'06 [1] by computing the Euclidean distance on the
output of the shared network and by optimizing the contrastive loss (see paper
for more details).

# References

- Dimensionality Reduction by Learning an Invariant Mapping
    http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf

Gets to 97.2% test accuracy after 20 epochs.
2 seconds per epoch on a Titan X Maxwell GPU
'''
from __future__ import absolute_import
from __future__ import print_function
import numpy as np

import random
from keras.datasets import mnist
from keras.models import Model
from keras.layers import Input, Flatten, Dense, Dropout, Lambda
from keras.optimizers import RMSprop
from keras import backend as K

num_classes = 10
epochs = 20


def euclidean_distance(vects):
    x, y = vects
    sum_square = K.sum(K.square(x - y), axis=1, keepdims=True)
    return K.sqrt(K.maximum(sum_square, K.epsilon()))


def eucl_dist_output_shape(shapes):
    shape1, shape2 = shapes
    return (shape1[0], 1)


def contrastive_loss(y_true, y_pred):
    '''Contrastive loss from Hadsell-et-al.'06
    http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf
    '''
    margin = 1
    square_pred = K.square(y_pred)
    margin_square = K.square(K.maximum(margin - y_pred, 0))
    return K.mean(y_true * square_pred + (1 - y_true) * margin_square)


def create_pairs(x, digit_indices):
    '''Positive and negative pair creation.
    Alternates between positive and negative pairs.
    '''
    pairs = []
    labels = []
    n = min([len(digit_indices[d]) for d in range(num_classes)]) - 1
    for d in range(num_classes):
        for i in range(n):
            z1, z2 = digit_indices[d][i], digit_indices[d][i + 1]
            pairs += [[x[z1], x[z2]]]
            inc = random.randrange(1, num_classes)
            dn = (d + inc) % num_classes
            z1, z2 = digit_indices[d][i], digit_indices[dn][i]
            pairs += [[x[z1], x[z2]]]
            labels += [1, 0]
    return np.array(pairs), np.array(labels)


def create_base_network(input_shape):
    '''Base network to be shared (eq. to feature extraction).
    '''
    input = Input(shape=input_shape)
    x = Flatten()(input)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.1)(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.1)(x)
    x = Dense(128, activation='relu')(x)
    return Model(input, x)


def compute_accuracy(y_true, y_pred):
    '''Compute classification accuracy with a fixed threshold on distances.
    '''
    pred = y_pred.ravel() < 0.5
    return np.mean(pred == y_true)


def accuracy(y_true, y_pred):
    '''Compute classification accuracy with a fixed threshold on distances.
    '''
    return K.mean(K.equal(y_true, K.cast(y_pred < 0.5, y_true.dtype)))


# the data, split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
input_shape = x_train.shape[1:]

# create training+test positive and negative pairs
digit_indices = [np.where(y_train == i)[0] for i in range(num_classes)]
tr_pairs, tr_y = create_pairs(x_train, digit_indices)

digit_indices = [np.where(y_test == i)[0] for i in range(num_classes)]
te_pairs, te_y = create_pairs(x_test, digit_indices)

# network definition
base_network = create_base_network(input_shape)

input_a = Input(shape=input_shape)
input_b = Input(shape=input_shape)

# because we re-use the same instance `base_network`,
# the weights of the network
# will be shared across the two branches
processed_a = base_network(input_a)
processed_b = base_network(input_b)

distance = Lambda(euclidean_distance,
                  output_shape=eucl_dist_output_shape)([processed_a, processed_b])

model = Model([input_a, input_b], distance)

# train
rms = RMSprop()
model.compile(loss=contrastive_loss, optimizer=rms, metrics=[accuracy])
model.fit([tr_pairs[:, 0], tr_pairs[:, 1]], tr_y,
          batch_size=128,
          epochs=epochs,
          validation_data=([te_pairs[:, 0], te_pairs[:, 1]], te_y))

# compute final accuracy on training and test sets
y_pred = model.predict([tr_pairs[:, 0], tr_pairs[:, 1]])
tr_acc = compute_accuracy(tr_y, y_pred)
y_pred = model.predict([te_pairs[:, 0], te_pairs[:, 1]])
te_acc = compute_accuracy(te_y, y_pred)

print('* Accuracy on training set: %0.2f%%' % (100 * tr_acc))
print('* Accuracy on test set: %0.2f%%' % (100 * te_acc))

# -*- coding: utf-8 -*-
"""
#Train an Auxiliary Classifier GAN (ACGAN) on the MNIST dataset.

[More details on Auxiliary Classifier GANs.](https://arxiv.org/abs/1610.09585)

You should start to see reasonable images after ~5 epochs, and good images
by ~15 epochs. You should use a GPU, as the convolution-heavy operations are
very slow on the CPU. Prefer the TensorFlow backend if you plan on iterating,
as the compilation time can be a blocker using Theano.

Timings:

Hardware           | Backend | Time / Epoch
:------------------|:--------|------------:
 CPU               | TF      | 3 hrs
 Titan X (maxwell) | TF      | 4 min
 Titan X (maxwell) | TH      | 7 min

Consult [Auxiliary Classifier Generative Adversarial Networks in Keras
](https://github.com/lukedeo/keras-acgan) for more information and example output.
"""
from __future__ import print_function

from collections import defaultdict
try:
    import cPickle as pickle
except ImportError:
    import pickle
from PIL import Image

from six.moves import range

from keras.datasets import mnist
from keras import layers
from keras.layers import Input, Dense, Reshape, Flatten, Embedding, Dropout
from keras.layers import BatchNormalization
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.convolutional import Conv2DTranspose, Conv2D
from keras.models import Sequential, Model
from keras.optimizers import Adam
from keras.utils.generic_utils import Progbar
import numpy as np

np.random.seed(1337)
num_classes = 10


def build_generator(latent_size):
    # we will map a pair of (z, L), where z is a latent vector and L is a
    # label drawn from P_c, to image space (..., 28, 28, 1)
    cnn = Sequential()

    cnn.add(Dense(3 * 3 * 384, input_dim=latent_size, activation='relu'))
    cnn.add(Reshape((3, 3, 384)))

    # upsample to (7, 7, ...)
    cnn.add(Conv2DTranspose(192, 5, strides=1, padding='valid',
                            activation='relu',
                            kernel_initializer='glorot_normal'))
    cnn.add(BatchNormalization())

    # upsample to (14, 14, ...)
    cnn.add(Conv2DTranspose(96, 5, strides=2, padding='same',
                            activation='relu',
                            kernel_initializer='glorot_normal'))
    cnn.add(BatchNormalization())

    # upsample to (28, 28, ...)
    cnn.add(Conv2DTranspose(1, 5, strides=2, padding='same',
                            activation='tanh',
                            kernel_initializer='glorot_normal'))

    # this is the z space commonly referred to in GAN papers
    latent = Input(shape=(latent_size, ))

    # this will be our label
    image_class = Input(shape=(1,), dtype='int32')

    cls = Embedding(num_classes, latent_size,
                    embeddings_initializer='glorot_normal')(image_class)

    # hadamard product between z-space and a class conditional embedding
    h = layers.multiply([latent, cls])

    fake_image = cnn(h)

    return Model([latent, image_class], fake_image)


def build_discriminator():
    # build a relatively standard conv net, with LeakyReLUs as suggested in
    # the reference paper
    cnn = Sequential()

    cnn.add(Conv2D(32, 3, padding='same', strides=2,
                   input_shape=(28, 28, 1)))
    cnn.add(LeakyReLU(0.2))
    cnn.add(Dropout(0.3))

    cnn.add(Conv2D(64, 3, padding='same', strides=1))
    cnn.add(LeakyReLU(0.2))
    cnn.add(Dropout(0.3))

    cnn.add(Conv2D(128, 3, padding='same', strides=2))
    cnn.add(LeakyReLU(0.2))
    cnn.add(Dropout(0.3))

    cnn.add(Conv2D(256, 3, padding='same', strides=1))
    cnn.add(LeakyReLU(0.2))
    cnn.add(Dropout(0.3))

    cnn.add(Flatten())

    image = Input(shape=(28, 28, 1))

    features = cnn(image)

    # first output (name=generation) is whether or not the discriminator
    # thinks the image that is being shown is fake, and the second output
    # (name=auxiliary) is the class that the discriminator thinks the image
    # belongs to.
    fake = Dense(1, activation='sigmoid', name='generation')(features)
    aux = Dense(num_classes, activation='softmax', name='auxiliary')(features)

    return Model(image, [fake, aux])


if __name__ == '__main__':
    # batch and latent size taken from the paper
    epochs = 100
    batch_size = 100
    latent_size = 100

    # Adam parameters suggested in https://arxiv.org/abs/1511.06434
    adam_lr = 0.0002
    adam_beta_1 = 0.5

    # build the discriminator
    print('Discriminator model:')
    discriminator = build_discriminator()
    discriminator.compile(
        optimizer=Adam(learning_rate=adam_lr, beta_1=adam_beta_1),
        loss=['binary_crossentropy', 'sparse_categorical_crossentropy']
    )
    discriminator.summary()

    # build the generator
    generator = build_generator(latent_size)

    latent = Input(shape=(latent_size, ))
    image_class = Input(shape=(1,), dtype='int32')

    # get a fake image
    fake = generator([latent, image_class])

    # we only want to be able to train generation for the combined model
    discriminator.trainable = False
    fake, aux = discriminator(fake)
    combined = Model([latent, image_class], [fake, aux])

    print('Combined model:')
    combined.compile(
        optimizer=Adam(learning_rate=adam_lr, beta_1=adam_beta_1),
        loss=['binary_crossentropy', 'sparse_categorical_crossentropy']
    )
    combined.summary()

    # get our mnist data, and force it to be of shape (..., 28, 28, 1) with
    # range [-1, 1]
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    x_train = (x_train.astype(np.float32) - 127.5) / 127.5
    x_train = np.expand_dims(x_train, axis=-1)

    x_test = (x_test.astype(np.float32) - 127.5) / 127.5
    x_test = np.expand_dims(x_test, axis=-1)

    num_train, num_test = x_train.shape[0], x_test.shape[0]

    train_history = defaultdict(list)
    test_history = defaultdict(list)

    for epoch in range(1, epochs + 1):
        print('Epoch {}/{}'.format(epoch, epochs))

        num_batches = int(np.ceil(x_train.shape[0] / float(batch_size)))
        progress_bar = Progbar(target=num_batches)

        epoch_gen_loss = []
        epoch_disc_loss = []

        for index in range(num_batches):
            # get a batch of real images
            image_batch = x_train[index * batch_size:(index + 1) * batch_size]
            label_batch = y_train[index * batch_size:(index + 1) * batch_size]

            # generate a new batch of noise
            noise = np.random.uniform(-1, 1, (len(image_batch), latent_size))

            # sample some labels from p_c
            sampled_labels = np.random.randint(0, num_classes, len(image_batch))

            # generate a batch of fake images, using the generated labels as a
            # conditioner. We reshape the sampled labels to be
            # (len(image_batch), 1) so that we can feed them into the embedding
            # layer as a length one sequence
            generated_images = generator.predict(
                [noise, sampled_labels.reshape((-1, 1))], verbose=0)

            x = np.concatenate((image_batch, generated_images))

            # use one-sided soft real/fake labels
            # Salimans et al., 2016
            # https://arxiv.org/pdf/1606.03498.pdf (Section 3.4)
            soft_zero, soft_one = 0, 0.95
            y = np.array(
                [soft_one] * len(image_batch) + [soft_zero] * len(image_batch))
            aux_y = np.concatenate((label_batch, sampled_labels), axis=0)

            # we don't want the discriminator to also maximize the classification
            # accuracy of the auxiliary classifier on generated images, so we
            # don't train discriminator to produce class labels for generated
            # images (see https://openreview.net/forum?id=rJXTf9Bxg).
            # To preserve sum of sample weights for the auxiliary classifier,
            # we assign sample weight of 2 to the real images.
            disc_sample_weight = [np.ones(2 * len(image_batch)),
                                  np.concatenate((np.ones(len(image_batch)) * 2,
                                                  np.zeros(len(image_batch))))]

            # see if the discriminator can figure itself out...
            epoch_disc_loss.append(discriminator.train_on_batch(
                x, [y, aux_y], sample_weight=disc_sample_weight))

            # make new noise. we generate 2 * batch size here such that we have
            # the generator optimize over an identical number of images as the
            # discriminator
            noise = np.random.uniform(-1, 1, (2 * len(image_batch), latent_size))
            sampled_labels = np.random.randint(0, num_classes, 2 * len(image_batch))

            # we want to train the generator to trick the discriminator
            # For the generator, we want all the {fake, not-fake} labels to say
            # not-fake
            trick = np.ones(2 * len(image_batch)) * soft_one

            epoch_gen_loss.append(combined.train_on_batch(
                [noise, sampled_labels.reshape((-1, 1))],
                [trick, sampled_labels]))

            progress_bar.update(index + 1)

        print('Testing for epoch {}:'.format(epoch))

        # evaluate the testing loss here

        # generate a new batch of noise
        noise = np.random.uniform(-1, 1, (num_test, latent_size))

        # sample some labels from p_c and generate images from them
        sampled_labels = np.random.randint(0, num_classes, num_test)
        generated_images = generator.predict(
            [noise, sampled_labels.reshape((-1, 1))], verbose=False)

        x = np.concatenate((x_test, generated_images))
        y = np.array([1] * num_test + [0] * num_test)
        aux_y = np.concatenate((y_test, sampled_labels), axis=0)

        # see if the discriminator can figure itself out...
        discriminator_test_loss = discriminator.evaluate(
            x, [y, aux_y], verbose=False)

        discriminator_train_loss = np.mean(np.array(epoch_disc_loss), axis=0)

        # make new noise
        noise = np.random.uniform(-1, 1, (2 * num_test, latent_size))
        sampled_labels = np.random.randint(0, num_classes, 2 * num_test)

        trick = np.ones(2 * num_test)

        generator_test_loss = combined.evaluate(
            [noise, sampled_labels.reshape((-1, 1))],
            [trick, sampled_labels], verbose=False)

        generator_train_loss = np.mean(np.array(epoch_gen_loss), axis=0)

        # generate an epoch report on performance
        train_history['generator'].append(generator_train_loss)
        train_history['discriminator'].append(discriminator_train_loss)

        test_history['generator'].append(generator_test_loss)
        test_history['discriminator'].append(discriminator_test_loss)

        print('{0:<22s} | {1:4s} | {2:15s} | {3:5s}'.format(
            'component', *discriminator.metrics_names))
        print('-' * 65)

        ROW_FMT = '{0:<22s} | {1:<4.2f} | {2:<15.4f} | {3:<5.4f}'
        print(ROW_FMT.format('generator (train)',
                             *train_history['generator'][-1]))
        print(ROW_FMT.format('generator (test)',
                             *test_history['generator'][-1]))
        print(ROW_FMT.format('discriminator (train)',
                             *train_history['discriminator'][-1]))
        print(ROW_FMT.format('discriminator (test)',
                             *test_history['discriminator'][-1]))

        # save weights every epoch
        generator.save_weights(
            'params_generator_epoch_{0:03d}.hdf5'.format(epoch), True)
        discriminator.save_weights(
            'params_discriminator_epoch_{0:03d}.hdf5'.format(epoch), True)

        # generate some digits to display
        num_rows = 40
        noise = np.tile(np.random.uniform(-1, 1, (num_rows, latent_size)),
                        (num_classes, 1))

        sampled_labels = np.array([
            [i] * num_rows for i in range(num_classes)
        ]).reshape(-1, 1)

        # get a batch to display
        generated_images = generator.predict(
            [noise, sampled_labels], verbose=0)

        # prepare real images sorted by class label
        real_labels = y_train[(epoch - 1) * num_rows * num_classes:
                              epoch * num_rows * num_classes]
        indices = np.argsort(real_labels, axis=0)
        real_images = x_train[(epoch - 1) * num_rows * num_classes:
                              epoch * num_rows * num_classes][indices]

        # display generated images, white separator, real images
        img = np.concatenate(
            (generated_images,
             np.repeat(np.ones_like(x_train[:1]), num_rows, axis=0),
             real_images))

        # arrange them into a grid
        img = (np.concatenate([r.reshape(-1, 28)
                               for r in np.split(img, 2 * num_classes + 1)
                               ], axis=-1) * 127.5 + 127.5).astype(np.uint8)

        Image.fromarray(img).save(
            'plot_epoch_{0:03d}_generated.png'.format(epoch))

    with open('acgan-history.pkl', 'wb') as f:
        pickle.dump({'train': train_history, 'test': test_history}, f)

'''# Sequence-to-sequence example in Keras (character-level).

This script demonstrates how to implement a basic character-level CNN
sequence-to-sequence model. We apply it to translating
short English sentences into short French sentences,
character-by-character. Note that it is fairly unusual to
do character-level machine translation, as word-level
models are much more common in this domain. This example
is for demonstration purposes only.

**Summary of the algorithm**

- We start with input sequences from a domain (e.g. English sentences)
    and corresponding target sequences from another domain
    (e.g. French sentences).
- An encoder CNN encodes the input character sequence.
- A decoder CNN is trained to turn the target sequences into
    the same sequence but offset by one timestep in the future,
    a training process called "teacher forcing" in this context.
    It uses the output from the encoder.
    Effectively, the decoder learns to generate `targets[t+1...]`
    given `targets[...t]`, conditioned on the input sequence.
- In inference mode, when we want to decode unknown input sequences, we:
    - Encode the input sequence.
    - Start with a target sequence of size 1
        (just the start-of-sequence character)
    - Feed the input sequence and 1-char target sequence
        to the decoder to produce predictions for the next character
    - Sample the next character using these predictions
        (we simply use argmax).
    - Append the sampled character to the target sequence
    - Repeat until we hit the character limit.

**Data download**

[English to French sentence pairs.
](http://www.manythings.org/anki/fra-eng.zip)

[Lots of neat sentence pairs datasets.
](http://www.manythings.org/anki/)

**References**

- lstm_seq2seq.py
- https://wanasit.github.io/attention-based-sequence-to-sequence-in-keras.html
'''
from __future__ import print_function

import numpy as np

from keras.layers import Input, Convolution1D, Dot, Dense, Activation, Concatenate
from keras.models import Model

batch_size = 64  # Batch size for training.
epochs = 100  # Number of epochs to train for.
num_samples = 10000  # Number of samples to train on.
# Path to the data txt file on disk.
data_path = 'fra-eng/fra.txt'

# Vectorize the data.
input_texts = []
target_texts = []
input_characters = set()
target_characters = set()
with open(data_path, 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')
for line in lines[: min(num_samples, len(lines) - 1)]:
    input_text, target_text = line.split('\t')
    # We use "tab" as the "start sequence" character
    # for the targets, and "\n" as "end sequence" character.
    target_text = '\t' + target_text + '\n'
    input_texts.append(input_text)
    target_texts.append(target_text)
    for char in input_text:
        if char not in input_characters:
            input_characters.add(char)
    for char in target_text:
        if char not in target_characters:
            target_characters.add(char)

input_characters = sorted(list(input_characters))
target_characters = sorted(list(target_characters))
num_encoder_tokens = len(input_characters)
num_decoder_tokens = len(target_characters)
max_encoder_seq_length = max([len(txt) for txt in input_texts])
max_decoder_seq_length = max([len(txt) for txt in target_texts])

print('Number of samples:', len(input_texts))
print('Number of unique input tokens:', num_encoder_tokens)
print('Number of unique output tokens:', num_decoder_tokens)
print('Max sequence length for inputs:', max_encoder_seq_length)
print('Max sequence length for outputs:', max_decoder_seq_length)

input_token_index = dict(
    [(char, i) for i, char in enumerate(input_characters)])
target_token_index = dict(
    [(char, i) for i, char in enumerate(target_characters)])

encoder_input_data = np.zeros(
    (len(input_texts), max_encoder_seq_length, num_encoder_tokens),
    dtype='float32')
decoder_input_data = np.zeros(
    (len(input_texts), max_decoder_seq_length, num_decoder_tokens),
    dtype='float32')
decoder_target_data = np.zeros(
    (len(input_texts), max_decoder_seq_length, num_decoder_tokens),
    dtype='float32')

for i, (input_text, target_text) in enumerate(zip(input_texts, target_texts)):
    for t, char in enumerate(input_text):
        encoder_input_data[i, t, input_token_index[char]] = 1.
    for t, char in enumerate(target_text):
        # decoder_target_data is ahead of decoder_input_data by one timestep
        decoder_input_data[i, t, target_token_index[char]] = 1.
        if t > 0:
            # decoder_target_data will be ahead by one timestep
            # and will not include the start character.
            decoder_target_data[i, t - 1, target_token_index[char]] = 1.

# Define an input sequence and process it.
encoder_inputs = Input(shape=(None, num_encoder_tokens))
# Encoder
x_encoder = Convolution1D(256, kernel_size=3, activation='relu',
                          padding='causal')(encoder_inputs)
x_encoder = Convolution1D(256, kernel_size=3, activation='relu',
                          padding='causal', dilation_rate=2)(x_encoder)
x_encoder = Convolution1D(256, kernel_size=3, activation='relu',
                          padding='causal', dilation_rate=4)(x_encoder)

decoder_inputs = Input(shape=(None, num_decoder_tokens))
# Decoder
x_decoder = Convolution1D(256, kernel_size=3, activation='relu',
                          padding='causal')(decoder_inputs)
x_decoder = Convolution1D(256, kernel_size=3, activation='relu',
                          padding='causal', dilation_rate=2)(x_decoder)
x_decoder = Convolution1D(256, kernel_size=3, activation='relu',
                          padding='causal', dilation_rate=4)(x_decoder)
# Attention
attention = Dot(axes=[2, 2])([x_decoder, x_encoder])
attention = Activation('softmax')(attention)

context = Dot(axes=[2, 1])([attention, x_encoder])
decoder_combined_context = Concatenate(axis=-1)([context, x_decoder])

decoder_outputs = Convolution1D(64, kernel_size=3, activation='relu',
                                padding='causal')(decoder_combined_context)
decoder_outputs = Convolution1D(64, kernel_size=3, activation='relu',
                                padding='causal')(decoder_outputs)
# Output
decoder_dense = Dense(num_decoder_tokens, activation='softmax')
decoder_outputs = decoder_dense(decoder_outputs)

# Define the model that will turn
# `encoder_input_data` & `decoder_input_data` into `decoder_target_data`
model = Model([encoder_inputs, decoder_inputs], decoder_outputs)
model.summary()

# Run training
model.compile(optimizer='adam', loss='categorical_crossentropy')
model.fit([encoder_input_data, decoder_input_data], decoder_target_data,
          batch_size=batch_size,
          epochs=epochs,
          validation_split=0.2)
# Save model
model.save('cnn_s2s.h5')

# Next: inference mode (sampling).

# Define sampling models
reverse_input_char_index = dict(
    (i, char) for char, i in input_token_index.items())
reverse_target_char_index = dict(
    (i, char) for char, i in target_token_index.items())

nb_examples = 100
in_encoder = encoder_input_data[:nb_examples]
in_decoder = np.zeros(
    (len(input_texts), max_decoder_seq_length, num_decoder_tokens),
    dtype='float32')

in_decoder[:, 0, target_token_index["\t"]] = 1

predict = np.zeros(
    (len(input_texts), max_decoder_seq_length),
    dtype='float32')

for i in range(max_decoder_seq_length - 1):
    predict = model.predict([in_encoder, in_decoder])
    predict = predict.argmax(axis=-1)
    predict_ = predict[:, i].ravel().tolist()
    for j, x in enumerate(predict_):
        in_decoder[j, i + 1, x] = 1

for seq_index in range(nb_examples):
    # Take one sequence (part of the training set)
    # for trying out decoding.
    output_seq = predict[seq_index, :].ravel().tolist()
    decoded = []
    for x in output_seq:
        if reverse_target_char_index[x] == "\n":
            break
        else:
            decoded.append(reverse_target_char_index[x])
    decoded_sentence = "".join(decoded)
    print('-')
    print('Input sentence:', input_texts[seq_index])
    print('Decoded sentence:', decoded_sentence)

"""
#Visualization of the filters of VGG16, via gradient ascent in input space.

This script can run on CPU in a few minutes.

Results example: ![Visualization](http://i.imgur.com/4nj4KjN.jpg)
"""
from __future__ import print_function

import time
import numpy as np
from PIL import Image as pil_image
from keras.preprocessing.image import save_img
from keras import layers
from keras.applications import vgg16
from keras import backend as K


def normalize(x):
    """utility function to normalize a tensor.

    # Arguments
        x: An input tensor.

    # Returns
        The normalized input tensor.
    """
    return x / (K.sqrt(K.mean(K.square(x))) + K.epsilon())


def deprocess_image(x):
    """utility function to convert a float array into a valid uint8 image.

    # Arguments
        x: A numpy-array representing the generated image.

    # Returns
        A processed numpy-array, which could be used in e.g. imshow.
    """
    # normalize tensor: center on 0., ensure std is 0.25
    x -= x.mean()
    x /= (x.std() + K.epsilon())
    x *= 0.25

    # clip to [0, 1]
    x += 0.5
    x = np.clip(x, 0, 1)

    # convert to RGB array
    x *= 255
    if K.image_data_format() == 'channels_first':
        x = x.transpose((1, 2, 0))
    x = np.clip(x, 0, 255).astype('uint8')
    return x


def process_image(x, former):
    """utility function to convert a valid uint8 image back into a float array.
       Reverses `deprocess_image`.

    # Arguments
        x: A numpy-array, which could be used in e.g. imshow.
        former: The former numpy-array.
                Need to determine the former mean and variance.

    # Returns
        A processed numpy-array representing the generated image.
    """
    if K.image_data_format() == 'channels_first':
        x = x.transpose((2, 0, 1))
    return (x / 255 - 0.5) * 4 * former.std() + former.mean()


def visualize_layer(model,
                    layer_name,
                    step=1.,
                    epochs=15,
                    upscaling_steps=9,
                    upscaling_factor=1.2,
                    output_dim=(412, 412),
                    filter_range=(0, None)):
    """Visualizes the most relevant filters of one conv-layer in a certain model.

    # Arguments
        model: The model containing layer_name.
        layer_name: The name of the layer to be visualized.
                    Has to be a part of model.
        step: step size for gradient ascent.
        epochs: Number of iterations for gradient ascent.
        upscaling_steps: Number of upscaling steps.
                         Starting image is in this case (80, 80).
        upscaling_factor: Factor to which to slowly upgrade
                          the image towards output_dim.
        output_dim: [img_width, img_height] The output image dimensions.
        filter_range: Tupel[lower, upper]
                      Determines the to be computed filter numbers.
                      If the second value is `None`,
                      the last filter will be inferred as the upper boundary.
    """

    def _generate_filter_image(input_img,
                               layer_output,
                               filter_index):
        """Generates image for one particular filter.

        # Arguments
            input_img: The input-image Tensor.
            layer_output: The output-image Tensor.
            filter_index: The to be processed filter number.
                          Assumed to be valid.

        #Returns
            Either None if no image could be generated.
            or a tuple of the image (array) itself and the last loss.
        """
        s_time = time.time()

        # we build a loss function that maximizes the activation
        # of the nth filter of the layer considered
        if K.image_data_format() == 'channels_first':
            loss = K.mean(layer_output[:, filter_index, :, :])
        else:
            loss = K.mean(layer_output[:, :, :, filter_index])

        # we compute the gradient of the input picture wrt this loss
        grads = K.gradients(loss, input_img)[0]

        # normalization trick: we normalize the gradient
        grads = normalize(grads)

        # this function returns the loss and grads given the input picture
        iterate = K.function([input_img], [loss, grads])

        # we start from a gray image with some random noise
        intermediate_dim = tuple(
            int(x / (upscaling_factor ** upscaling_steps)) for x in output_dim)
        if K.image_data_format() == 'channels_first':
            input_img_data = np.random.random(
                (1, 3, intermediate_dim[0], intermediate_dim[1]))
        else:
            input_img_data = np.random.random(
                (1, intermediate_dim[0], intermediate_dim[1], 3))
        input_img_data = (input_img_data - 0.5) * 20 + 128

        # Slowly upscaling towards the original size prevents
        # a dominating high-frequency of the to visualized structure
        # as it would occur if we directly compute the 412d-image.
        # Behaves as a better starting point for each following dimension
        # and therefore avoids poor local minima
        for up in reversed(range(upscaling_steps)):
            # we run gradient ascent for e.g. 20 steps
            for _ in range(epochs):
                loss_value, grads_value = iterate([input_img_data])
                input_img_data += grads_value * step

                # some filters get stuck to 0, we can skip them
                if loss_value <= K.epsilon():
                    return None

            # Calculate upscaled dimension
            intermediate_dim = tuple(
                int(x / (upscaling_factor ** up)) for x in output_dim)
            # Upscale
            img = deprocess_image(input_img_data[0])
            img = np.array(pil_image.fromarray(img).resize(intermediate_dim,
                                                           pil_image.BICUBIC))
            input_img_data = np.expand_dims(
                process_image(img, input_img_data[0]), 0)

        # decode the resulting input image
        img = deprocess_image(input_img_data[0])
        e_time = time.time()
        print('Costs of filter {:3}: {:5.0f} ( {:4.2f}s )'.format(filter_index,
                                                                  loss_value,
                                                                  e_time - s_time))
        return img, loss_value

    def _draw_filters(filters, n=None):
        """Draw the best filters in a nxn grid.

        # Arguments
            filters: A List of generated images and their corresponding losses
                     for each processed filter.
            n: dimension of the grid.
               If none, the largest possible square will be used
        """
        if n is None:
            n = int(np.floor(np.sqrt(len(filters))))

        # the filters that have the highest loss are assumed to be better-looking.
        # we will only keep the top n*n filters.
        filters.sort(key=lambda x: x[1], reverse=True)
        filters = filters[:n * n]

        # build a black picture with enough space for
        # e.g. our 8 x 8 filters of size 412 x 412, with a 5px margin in between
        MARGIN = 5
        width = n * output_dim[0] + (n - 1) * MARGIN
        height = n * output_dim[1] + (n - 1) * MARGIN
        stitched_filters = np.zeros((width, height, 3), dtype='uint8')

        # fill the picture with our saved filters
        for i in range(n):
            for j in range(n):
                img, _ = filters[i * n + j]
                width_margin = (output_dim[0] + MARGIN) * i
                height_margin = (output_dim[1] + MARGIN) * j
                stitched_filters[
                    width_margin: width_margin + output_dim[0],
                    height_margin: height_margin + output_dim[1], :] = img

        # save the result to disk
        save_img('vgg_{0:}_{1:}x{1:}.png'.format(layer_name, n), stitched_filters)

    # this is the placeholder for the input images
    assert len(model.inputs) == 1
    input_img = model.inputs[0]

    # get the symbolic outputs of each "key" layer (we gave them unique names).
    layer_dict = dict([(layer.name, layer) for layer in model.layers[1:]])

    output_layer = layer_dict[layer_name]
    assert isinstance(output_layer, layers.Conv2D)

    # Compute to be processed filter range
    filter_lower = filter_range[0]
    filter_upper = (filter_range[1]
                    if filter_range[1] is not None
                    else len(output_layer.get_weights()[1]))
    assert(filter_lower >= 0
           and filter_upper <= len(output_layer.get_weights()[1])
           and filter_upper > filter_lower)
    print('Compute filters {:} to {:}'.format(filter_lower, filter_upper))

    # iterate through each filter and generate its corresponding image
    processed_filters = []
    for f in range(filter_lower, filter_upper):
        img_loss = _generate_filter_image(input_img, output_layer.output, f)

        if img_loss is not None:
            processed_filters.append(img_loss)

    print('{} filter processed.'.format(len(processed_filters)))
    # Finally draw and store the best filters to disk
    _draw_filters(processed_filters)


if __name__ == '__main__':
    # the name of the layer we want to visualize
    # (see model definition at keras/applications/vgg16.py)
    LAYER_NAME = 'block5_conv1'

    # build the VGG16 network with ImageNet weights
    vgg = vgg16.VGG16(weights='imagenet', include_top=False)
    print('Model loaded.')
    vgg.summary()

    # example function call
    visualize_layer(vgg, LAYER_NAME)

'''This is an implementation of Net2Net experiment with MNIST in
'Net2Net: Accelerating Learning via Knowledge Transfer'
by Tianqi Chen, Ian Goodfellow, and Jonathon Shlens

arXiv:1511.05641v4 [cs.LG] 23 Apr 2016
http://arxiv.org/abs/1511.05641

# Notes

- What:
  + Net2Net is a group of methods to transfer knowledge from a teacher neural
    net to a student net,so that the student net can be trained faster than
    from scratch.
  + The paper discussed two specific methods of Net2Net, i.e. Net2WiderNet
    and Net2DeeperNet.
  + Net2WiderNet replaces a model with an equivalent wider model that has
    more units in each hidden layer.
  + Net2DeeperNet replaces a model with an equivalent deeper model.
  + Both are based on the idea of 'function-preserving transformations of
    neural nets'.
- Why:
  + Enable fast exploration of multiple neural nets in experimentation and
    design process,by creating a series of wider and deeper models with
    transferable knowledge.
  + Enable 'lifelong learning system' by gradually adjusting model complexity
    to data availability,and reusing transferable knowledge.

# Experiments

- Teacher model: a basic CNN model trained on MNIST for 3 epochs.
- Net2WiderNet experiment:
  + Student model has a wider Conv2D layer and a wider FC layer.
  + Comparison of 'random-padding' vs 'net2wider' weight initialization.
  + With both methods, after 1 epoch, student model should perform as well as
    teacher model, but 'net2wider' is slightly better.
- Net2DeeperNet experiment:
  + Student model has an extra Conv2D layer and an extra FC layer.
  + Comparison of 'random-init' vs 'net2deeper' weight initialization.
  + After 1 epoch, performance of 'net2deeper' is better than 'random-init'.
- Hyper-parameters:
  + SGD with momentum=0.9 is used for training teacher and student models.
  + Learning rate adjustment: it's suggested to reduce learning rate
    to 1/10 for student model.
  + Addition of noise in 'net2wider' is used to break weight symmetry
    and thus enable full capacity of student models. It is optional
    when a Dropout layer is used.

# Results

- Tested with TF backend and 'channels_last' image_data_format.
- Running on GPU GeForce GTX Titan X Maxwell
- Performance Comparisons - validation loss values during first 3 epochs:

Teacher model ...
(0) teacher_model:             0.0537   0.0354   0.0356

Experiment of Net2WiderNet ...
(1) wider_random_pad:          0.0320   0.0317   0.0289
(2) wider_net2wider:           0.0271   0.0274   0.0270

Experiment of Net2DeeperNet ...
(3) deeper_random_init:        0.0682   0.0506   0.0468
(4) deeper_net2deeper:         0.0292   0.0294   0.0286
'''

from __future__ import print_function
import numpy as np
import keras
from keras import backend as K
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Dense, Flatten
from keras.optimizers import SGD
from keras.datasets import mnist

if K.image_data_format() == 'channels_first':
    input_shape = (1, 28, 28)  # image shape
else:
    input_shape = (28, 28, 1)  # image shape
num_classes = 10  # number of classes
epochs = 3


# load and pre-process data
def preprocess_input(x):
    return x.astype('float32').reshape((-1,) + input_shape) / 255


def preprocess_output(y):
    return keras.utils.to_categorical(y)

(x_train, y_train), (x_test, y_test) = mnist.load_data()
x_train, x_test = map(preprocess_input, [x_train, x_test])
y_train, y_test = map(preprocess_output, [y_train, y_test])
print('Loading MNIST data...')
print('x_train shape:', x_train.shape, 'y_train shape:', y_train.shape)
print('x_test shape:', x_test.shape, 'y_test shape', y_test.shape)


# knowledge transfer algorithms
def wider2net_conv2d(teacher_w1, teacher_b1, teacher_w2, new_width, init):
    '''Get initial weights for a wider conv2d layer with a bigger filters,
    by 'random-padding' or 'net2wider'.

    # Arguments
        teacher_w1: `weight` of conv2d layer to become wider,
          of shape (filters1, num_channel1, kh1, kw1)
        teacher_b1: `bias` of conv2d layer to become wider,
          of shape (filters1, )
        teacher_w2: `weight` of next connected conv2d layer,
          of shape (filters2, num_channel2, kh2, kw2)
        new_width: new `filters` for the wider conv2d layer
        init: initialization algorithm for new weights,
          either 'random-pad' or 'net2wider'
    '''
    assert teacher_w1.shape[0] == teacher_w2.shape[1], (
        'successive layers from teacher model should have compatible shapes')
    assert teacher_w1.shape[3] == teacher_b1.shape[0], (
        'weight and bias from same layer should have compatible shapes')
    assert new_width > teacher_w1.shape[3], (
        'new width (filters) should be bigger than the existing one')

    n = new_width - teacher_w1.shape[3]
    if init == 'random-pad':
        new_w1 = np.random.normal(0, 0.1, size=teacher_w1.shape[:3] + (n,))
        new_b1 = np.ones(n) * 0.1
        new_w2 = np.random.normal(
            0, 0.1,
            size=teacher_w2.shape[:2] + (n, teacher_w2.shape[3]))
    elif init == 'net2wider':
        index = np.random.randint(teacher_w1.shape[3], size=n)
        factors = np.bincount(index)[index] + 1.
        new_w1 = teacher_w1[:, :, :, index]
        new_b1 = teacher_b1[index]
        new_w2 = teacher_w2[:, :, index, :] / factors.reshape((1, 1, -1, 1))
    else:
        raise ValueError('Unsupported weight initializer: %s' % init)

    student_w1 = np.concatenate((teacher_w1, new_w1), axis=3)
    if init == 'random-pad':
        student_w2 = np.concatenate((teacher_w2, new_w2), axis=2)
    elif init == 'net2wider':
        # add small noise to break symmetry, so that student model will have
        # full capacity later
        noise = np.random.normal(0, 5e-2 * new_w2.std(), size=new_w2.shape)
        student_w2 = np.concatenate((teacher_w2, new_w2 + noise), axis=2)
        student_w2[:, :, index, :] = new_w2
    student_b1 = np.concatenate((teacher_b1, new_b1), axis=0)

    return student_w1, student_b1, student_w2


def wider2net_fc(teacher_w1, teacher_b1, teacher_w2, new_width, init):
    '''Get initial weights for a wider fully connected (dense) layer
       with a bigger nout, by 'random-padding' or 'net2wider'.

    # Arguments
        teacher_w1: `weight` of fc layer to become wider,
          of shape (nin1, nout1)
        teacher_b1: `bias` of fc layer to become wider,
          of shape (nout1, )
        teacher_w2: `weight` of next connected fc layer,
          of shape (nin2, nout2)
        new_width: new `nout` for the wider fc layer
        init: initialization algorithm for new weights,
          either 'random-pad' or 'net2wider'
    '''
    assert teacher_w1.shape[1] == teacher_w2.shape[0], (
        'successive layers from teacher model should have compatible shapes')
    assert teacher_w1.shape[1] == teacher_b1.shape[0], (
        'weight and bias from same layer should have compatible shapes')
    assert new_width > teacher_w1.shape[1], (
        'new width (nout) should be bigger than the existing one')

    n = new_width - teacher_w1.shape[1]
    if init == 'random-pad':
        new_w1 = np.random.normal(0, 0.1, size=(teacher_w1.shape[0], n))
        new_b1 = np.ones(n) * 0.1
        new_w2 = np.random.normal(0, 0.1, size=(n, teacher_w2.shape[1]))
    elif init == 'net2wider':
        index = np.random.randint(teacher_w1.shape[1], size=n)
        factors = np.bincount(index)[index] + 1.
        new_w1 = teacher_w1[:, index]
        new_b1 = teacher_b1[index]
        new_w2 = teacher_w2[index, :] / factors[:, np.newaxis]
    else:
        raise ValueError('Unsupported weight initializer: %s' % init)

    student_w1 = np.concatenate((teacher_w1, new_w1), axis=1)
    if init == 'random-pad':
        student_w2 = np.concatenate((teacher_w2, new_w2), axis=0)
    elif init == 'net2wider':
        # add small noise to break symmetry, so that student model will have
        # full capacity later
        noise = np.random.normal(0, 5e-2 * new_w2.std(), size=new_w2.shape)
        student_w2 = np.concatenate((teacher_w2, new_w2 + noise), axis=0)
        student_w2[index, :] = new_w2
    student_b1 = np.concatenate((teacher_b1, new_b1), axis=0)

    return student_w1, student_b1, student_w2


def deeper2net_conv2d(teacher_w):
    '''Get initial weights for a deeper conv2d layer by net2deeper'.

    # Arguments
        teacher_w: `weight` of previous conv2d layer,
          of shape (kh, kw, num_channel, filters)
    '''
    kh, kw, num_channel, filters = teacher_w.shape
    student_w = np.zeros_like(teacher_w)
    for i in range(filters):
        student_w[(kh - 1) // 2, (kw - 1) // 2, i, i] = 1.
    student_b = np.zeros(filters)
    return student_w, student_b


def copy_weights(teacher_model, student_model, layer_names):
    '''Copy weights from teacher_model to student_model,
     for layers with names listed in layer_names
    '''
    for name in layer_names:
        weights = teacher_model.get_layer(name=name).get_weights()
        student_model.get_layer(name=name).set_weights(weights)


# methods to construct teacher_model and student_models
def make_teacher_model(x_train, y_train,
                       x_test, y_test,
                       epochs):
    '''Train and benchmark performance of a simple CNN.
    (0) Teacher model
    '''
    model = Sequential()
    model.add(Conv2D(64, 3, input_shape=input_shape,
                     padding='same', name='conv1'))
    model.add(MaxPooling2D(2, name='pool1'))
    model.add(Conv2D(64, 3, padding='same', name='conv2'))
    model.add(MaxPooling2D(2, name='pool2'))
    model.add(Flatten(name='flatten'))
    model.add(Dense(64, activation='relu', name='fc1'))
    model.add(Dense(num_classes, activation='softmax', name='fc2'))
    model.compile(loss='categorical_crossentropy',
                  optimizer=SGD(learning_rate=0.01, momentum=0.9),
                  metrics=['accuracy'])

    model.fit(x_train, y_train,
              epochs=epochs,
              validation_data=(x_test, y_test))
    return model


def make_wider_student_model(teacher_model,
                             x_train, y_train,
                             x_test, y_test,
                             init, epochs):
    '''Train a wider student model based on teacher_model,
       with either 'random-pad' (baseline) or 'net2wider'
    '''
    new_conv1_width = 128
    new_fc1_width = 128

    model = Sequential()
    # a wider conv1 compared to teacher_model
    model.add(Conv2D(new_conv1_width, 3, input_shape=input_shape,
                     padding='same', name='conv1'))
    model.add(MaxPooling2D(2, name='pool1'))
    model.add(Conv2D(64, 3, padding='same', name='conv2'))
    model.add(MaxPooling2D(2, name='pool2'))
    model.add(Flatten(name='flatten'))
    # a wider fc1 compared to teacher model
    model.add(Dense(new_fc1_width, activation='relu', name='fc1'))
    model.add(Dense(num_classes, activation='softmax', name='fc2'))

    # The weights for other layers need to be copied from teacher_model
    # to student_model, except for widened layers
    # and their immediate downstreams, which will be initialized separately.
    # For this example there are no other layers that need to be copied.

    w_conv1, b_conv1 = teacher_model.get_layer('conv1').get_weights()
    w_conv2, b_conv2 = teacher_model.get_layer('conv2').get_weights()
    new_w_conv1, new_b_conv1, new_w_conv2 = wider2net_conv2d(
        w_conv1, b_conv1, w_conv2, new_conv1_width, init)
    model.get_layer('conv1').set_weights([new_w_conv1, new_b_conv1])
    model.get_layer('conv2').set_weights([new_w_conv2, b_conv2])

    w_fc1, b_fc1 = teacher_model.get_layer('fc1').get_weights()
    w_fc2, b_fc2 = teacher_model.get_layer('fc2').get_weights()
    new_w_fc1, new_b_fc1, new_w_fc2 = wider2net_fc(
        w_fc1, b_fc1, w_fc2, new_fc1_width, init)
    model.get_layer('fc1').set_weights([new_w_fc1, new_b_fc1])
    model.get_layer('fc2').set_weights([new_w_fc2, b_fc2])

    model.compile(loss='categorical_crossentropy',
                  optimizer=SGD(learning_rate=0.001, momentum=0.9),
                  metrics=['accuracy'])

    model.fit(x_train, y_train,
              epochs=epochs,
              validation_data=(x_test, y_test))


def make_deeper_student_model(teacher_model,
                              x_train, y_train,
                              x_test, y_test,
                              init, epochs):
    '''Train a deeper student model based on teacher_model,
       with either 'random-init' (baseline) or 'net2deeper'
    '''
    model = Sequential()
    model.add(Conv2D(64, 3, input_shape=input_shape,
                     padding='same', name='conv1'))
    model.add(MaxPooling2D(2, name='pool1'))
    model.add(Conv2D(64, 3, padding='same', name='conv2'))
    # add another conv2d layer to make original conv2 deeper
    if init == 'net2deeper':
        prev_w, _ = model.get_layer('conv2').get_weights()
        new_weights = deeper2net_conv2d(prev_w)
        model.add(Conv2D(64, 3, padding='same',
                         name='conv2-deeper', weights=new_weights))
    elif init == 'random-init':
        model.add(Conv2D(64, 3, padding='same', name='conv2-deeper'))
    else:
        raise ValueError('Unsupported weight initializer: %s' % init)
    model.add(MaxPooling2D(2, name='pool2'))
    model.add(Flatten(name='flatten'))
    model.add(Dense(64, activation='relu', name='fc1'))
    # add another fc layer to make original fc1 deeper
    if init == 'net2deeper':
        # net2deeper for fc layer with relu, is just an identity initializer
        model.add(Dense(64, kernel_initializer='identity',
                        activation='relu', name='fc1-deeper'))
    elif init == 'random-init':
        model.add(Dense(64, activation='relu', name='fc1-deeper'))
    else:
        raise ValueError('Unsupported weight initializer: %s' % init)
    model.add(Dense(num_classes, activation='softmax', name='fc2'))

    # copy weights for other layers
    copy_weights(teacher_model, model, layer_names=[
                 'conv1', 'conv2', 'fc1', 'fc2'])

    model.compile(loss='categorical_crossentropy',
                  optimizer=SGD(learning_rate=0.001, momentum=0.9),
                  metrics=['accuracy'])

    model.fit(x_train, y_train,
              epochs=epochs,
              validation_data=(x_test, y_test))


# experiments setup
def net2wider_experiment():
    '''Benchmark performances of
    (1) a wider student model with `random_pad` initializer
    (2) a wider student model with `Net2WiderNet` initializer
    '''
    print('\nExperiment of Net2WiderNet ...')

    print('\n(1) building wider student model by random padding ...')
    make_wider_student_model(teacher_model,
                             x_train, y_train,
                             x_test, y_test,
                             init='random-pad',
                             epochs=epochs)
    print('\n(2) building wider student model by net2wider ...')
    make_wider_student_model(teacher_model,
                             x_train, y_train,
                             x_test, y_test,
                             init='net2wider',
                             epochs=epochs)


def net2deeper_experiment():
    '''Benchmark performances of
    (3) a deeper student model with `random_init` initializer
    (4) a deeper student model with `Net2DeeperNet` initializer
    '''
    print('\nExperiment of Net2DeeperNet ...')

    print('\n(3) building deeper student model by random init ...')
    make_deeper_student_model(teacher_model,
                              x_train, y_train,
                              x_test, y_test,
                              init='random-init',
                              epochs=epochs)
    print('\n(4) building deeper student model by net2deeper ...')
    make_deeper_student_model(teacher_model,
                              x_train, y_train,
                              x_test, y_test,
                              init='net2deeper',
                              epochs=epochs)


print('\n(0) building teacher model ...')
teacher_model = make_teacher_model(x_train, y_train,
                                   x_test, y_test,
                                   epochs=epochs)

# run the experiments
net2wider_experiment()
net2deeper_experiment()

'''
#Train a recurrent convolutional network on the IMDB sentiment classification task.

Gets to 0.8498 test accuracy after 2 epochs. 41 s/epoch on K520 GPU.
'''
from __future__ import print_function

from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from keras.layers import Embedding
from keras.layers import LSTM
from keras.layers import Conv1D, MaxPooling1D
from keras.datasets import imdb

# Embedding
max_features = 20000
maxlen = 100
embedding_size = 128

# Convolution
kernel_size = 5
filters = 64
pool_size = 4

# LSTM
lstm_output_size = 70

# Training
batch_size = 30
epochs = 2

'''
Note:
batch_size is highly sensitive.
Only 2 epochs are needed as the dataset is very small.
'''

print('Loading data...')
(x_train, y_train), (x_test, y_test) = imdb.load_data(num_words=max_features)
print(len(x_train), 'train sequences')
print(len(x_test), 'test sequences')

print('Pad sequences (samples x time)')
x_train = sequence.pad_sequences(x_train, maxlen=maxlen)
x_test = sequence.pad_sequences(x_test, maxlen=maxlen)
print('x_train shape:', x_train.shape)
print('x_test shape:', x_test.shape)

print('Build model...')

model = Sequential()
model.add(Embedding(max_features, embedding_size, input_length=maxlen))
model.add(Dropout(0.25))
model.add(Conv1D(filters,
                 kernel_size,
                 padding='valid',
                 activation='relu',
                 strides=1))
model.add(MaxPooling1D(pool_size=pool_size))
model.add(LSTM(lstm_output_size))
model.add(Dense(1))
model.add(Activation('sigmoid'))

model.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

print('Train...')
model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          validation_data=(x_test, y_test))
score, acc = model.evaluate(x_test, y_test, batch_size=batch_size)
print('Test score:', score)
print('Test accuracy:', acc)

'''Compares self-normalizing MLPs with regular MLPs.

Compares the performance of a simple MLP using two
different activation functions: RELU and SELU
on the Reuters newswire topic classification task.

# Reference

- Klambauer, G., Unterthiner, T., Mayr, A., & Hochreiter, S. (2017).
  Self-Normalizing Neural Networks. arXiv preprint arXiv:1706.02515.
  https://arxiv.org/abs/1706.02515
'''
from __future__ import print_function

import numpy as np
import matplotlib.pyplot as plt
import keras
from keras.datasets import reuters
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
from keras.layers.noise import AlphaDropout
from keras.preprocessing.text import Tokenizer

max_words = 1000
batch_size = 16
epochs = 40
plot = True


def create_network(n_dense=6,
                   dense_units=16,
                   activation='selu',
                   dropout=AlphaDropout,
                   dropout_rate=0.1,
                   kernel_initializer='lecun_normal',
                   optimizer='adam',
                   num_classes=1,
                   max_words=max_words):
    """Generic function to create a fully-connected neural network.

    # Arguments
        n_dense: int > 0. Number of dense layers.
        dense_units: int > 0. Number of dense units per layer.
        dropout: keras.layers.Layer. A dropout layer to apply.
        dropout_rate: 0 <= float <= 1. The rate of dropout.
        kernel_initializer: str. The initializer for the weights.
        optimizer: str/keras.optimizers.Optimizer. The optimizer to use.
        num_classes: int > 0. The number of classes to predict.
        max_words: int > 0. The maximum number of words per data point.

    # Returns
        A Keras model instance (compiled).
    """
    model = Sequential()
    model.add(Dense(dense_units, input_shape=(max_words,),
                    kernel_initializer=kernel_initializer))
    model.add(Activation(activation))
    model.add(dropout(dropout_rate))

    for i in range(n_dense - 1):
        model.add(Dense(dense_units, kernel_initializer=kernel_initializer))
        model.add(Activation(activation))
        model.add(dropout(dropout_rate))

    model.add(Dense(num_classes))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy',
                  optimizer=optimizer,
                  metrics=['accuracy'])
    return model


network1 = {
    'n_dense': 6,
    'dense_units': 16,
    'activation': 'relu',
    'dropout': Dropout,
    'dropout_rate': 0.5,
    'kernel_initializer': 'glorot_uniform',
    'optimizer': 'sgd'
}

network2 = {
    'n_dense': 6,
    'dense_units': 16,
    'activation': 'selu',
    'dropout': AlphaDropout,
    'dropout_rate': 0.1,
    'kernel_initializer': 'lecun_normal',
    'optimizer': 'sgd'
}

print('Loading data...')
(x_train, y_train), (x_test, y_test) = reuters.load_data(num_words=max_words,
                                                         test_split=0.2)
print(len(x_train), 'train sequences')
print(len(x_test), 'test sequences')

num_classes = np.max(y_train) + 1
print(num_classes, 'classes')

print('Vectorizing sequence data...')
tokenizer = Tokenizer(num_words=max_words)
x_train = tokenizer.sequences_to_matrix(x_train, mode='binary')
x_test = tokenizer.sequences_to_matrix(x_test, mode='binary')
print('x_train shape:', x_train.shape)
print('x_test shape:', x_test.shape)

print('Convert class vector to binary class matrix '
      '(for use with categorical_crossentropy)')
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)
print('y_train shape:', y_train.shape)
print('y_test shape:', y_test.shape)

print('\nBuilding network 1...')

model1 = create_network(num_classes=num_classes, **network1)
history_model1 = model1.fit(x_train,
                            y_train,
                            batch_size=batch_size,
                            epochs=epochs,
                            verbose=1,
                            validation_split=0.1)

score_model1 = model1.evaluate(x_test,
                               y_test,
                               batch_size=batch_size,
                               verbose=1)


print('\nBuilding network 2...')
model2 = create_network(num_classes=num_classes, **network2)

history_model2 = model2.fit(x_train,
                            y_train,
                            batch_size=batch_size,
                            epochs=epochs,
                            verbose=1,
                            validation_split=0.1)

score_model2 = model2.evaluate(x_test,
                               y_test,
                               batch_size=batch_size,
                               verbose=1)

print('\nNetwork 1 results')
print('Hyperparameters:', network1)
print('Test score:', score_model1[0])
print('Test accuracy:', score_model1[1])
print('Network 2 results')
print('Hyperparameters:', network2)
print('Test score:', score_model2[0])
print('Test accuracy:', score_model2[1])

plt.plot(range(epochs),
         history_model1.history['val_loss'],
         'g-',
         label='Network 1 Val Loss')
plt.plot(range(epochs),
         history_model2.history['val_loss'],
         'r-',
         label='Network 2 Val Loss')
plt.plot(range(epochs),
         history_model1.history['loss'],
         'g--',
         label='Network 1 Loss')
plt.plot(range(epochs),
         history_model2.history['loss'],
         'r--',
         label='Network 2 Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.savefig('comparison_of_networks.png')

'''Transfer learning toy example.

1 - Train a simple convnet on the MNIST dataset the first 5 digits [0..4].
2 - Freeze convolutional layers and fine-tune dense layers
   for the classification of digits [5..9].

Get to 99.8% test accuracy after 5 epochs
for the first five digits classifier
and 99.2% for the last five digits after transfer + fine-tuning.
'''

from __future__ import print_function

import datetime
import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K

now = datetime.datetime.now

batch_size = 128
num_classes = 5
epochs = 5

# input image dimensions
img_rows, img_cols = 28, 28
# number of convolutional filters to use
filters = 32
# size of pooling area for max pooling
pool_size = 2
# convolution kernel size
kernel_size = 3

if K.image_data_format() == 'channels_first':
    input_shape = (1, img_rows, img_cols)
else:
    input_shape = (img_rows, img_cols, 1)


def train_model(model, train, test, num_classes):
    x_train = train[0].reshape((train[0].shape[0],) + input_shape)
    x_test = test[0].reshape((test[0].shape[0],) + input_shape)
    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')
    x_train /= 255
    x_test /= 255
    print('x_train shape:', x_train.shape)
    print(x_train.shape[0], 'train samples')
    print(x_test.shape[0], 'test samples')

    # convert class vectors to binary class matrices
    y_train = keras.utils.to_categorical(train[1], num_classes)
    y_test = keras.utils.to_categorical(test[1], num_classes)

    model.compile(loss='categorical_crossentropy',
                  optimizer='adadelta',
                  metrics=['accuracy'])

    t = now()
    model.fit(x_train, y_train,
              batch_size=batch_size,
              epochs=epochs,
              verbose=1,
              validation_data=(x_test, y_test))
    print('Training time: %s' % (now() - t))
    score = model.evaluate(x_test, y_test, verbose=0)
    print('Test score:', score[0])
    print('Test accuracy:', score[1])


# the data, split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# create two datasets one with digits below 5 and one with 5 and above
x_train_lt5 = x_train[y_train < 5]
y_train_lt5 = y_train[y_train < 5]
x_test_lt5 = x_test[y_test < 5]
y_test_lt5 = y_test[y_test < 5]

x_train_gte5 = x_train[y_train >= 5]
y_train_gte5 = y_train[y_train >= 5] - 5
x_test_gte5 = x_test[y_test >= 5]
y_test_gte5 = y_test[y_test >= 5] - 5

# define two groups of layers: feature (convolutions) and classification (dense)
feature_layers = [
    Conv2D(filters, kernel_size,
           padding='valid',
           input_shape=input_shape),
    Activation('relu'),
    Conv2D(filters, kernel_size),
    Activation('relu'),
    MaxPooling2D(pool_size=pool_size),
    Dropout(0.25),
    Flatten(),
]

classification_layers = [
    Dense(128),
    Activation('relu'),
    Dropout(0.5),
    Dense(num_classes),
    Activation('softmax')
]

# create complete model
model = Sequential(feature_layers + classification_layers)

# train model for 5-digit classification [0..4]
train_model(model,
            (x_train_lt5, y_train_lt5),
            (x_test_lt5, y_test_lt5), num_classes)

# freeze feature layers and rebuild model
for l in feature_layers:
    l.trainable = False

# transfer: train dense layers for new classification task [5..9]
train_model(model,
            (x_train_gte5, y_train_gte5),
            (x_test_gte5, y_test_gte5), num_classes)

'''Trains a stacked what-where autoencoder built on residual blocks on the
MNIST dataset. It exemplifies two influential methods that have been developed
in the past few years.

The first is the idea of properly 'unpooling.' During any max pool, the
exact location (the 'where') of the maximal value in a pooled receptive field
is lost, however it can be very useful in the overall reconstruction of an
input image. Therefore, if the 'where' is handed from the encoder
to the corresponding decoder layer, features being decoded can be 'placed' in
the right location, allowing for reconstructions of much higher fidelity.

# References

- Visualizing and Understanding Convolutional Networks
  Matthew D Zeiler, Rob Fergus
  https://arxiv.org/abs/1311.2901v3
- Stacked What-Where Auto-encoders
  Junbo Zhao, Michael Mathieu, Ross Goroshin, Yann LeCun
  https://arxiv.org/abs/1506.02351v8

The second idea exploited here is that of residual learning. Residual blocks
ease the training process by allowing skip connections that give the network
the ability to be as linear (or non-linear) as the data sees fit.  This allows
for much deep networks to be easily trained. The residual element seems to
be advantageous in the context of this example as it allows a nice symmetry
between the encoder and decoder. Normally, in the decoder, the final
projection to the space where the image is reconstructed is linear, however
this does not have to be the case for a residual block as the degree to which
its output is linear or non-linear is determined by the data it is fed.
However, in order to cap the reconstruction in this example, a hard softmax is
applied as a bias because we know the MNIST digits are mapped to [0, 1].

# References
- Deep Residual Learning for Image Recognition
  Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
  https://arxiv.org/abs/1512.03385v1
- Identity Mappings in Deep Residual Networks
  Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun
  https://arxiv.org/abs/1603.05027v3
'''
from __future__ import print_function
import numpy as np

from keras.datasets import mnist
from keras.models import Model
from keras.layers import Activation
from keras.layers import UpSampling2D, Conv2D, MaxPooling2D
from keras.layers import Input, BatchNormalization, ELU
import matplotlib.pyplot as plt
import keras.backend as K
from keras import layers


def convresblock(x, nfeats=8, ksize=3, nskipped=2, elu=True):
    """The proposed residual block from [4].

    Running with elu=True will use ELU nonlinearity and running with
    elu=False will use BatchNorm + RELU nonlinearity.  While ELU's are fast
    due to the fact they do not suffer from BatchNorm overhead, they may
    overfit because they do not offer the stochastic element of the batch
    formation process of BatchNorm, which acts as a good regularizer.

    # Arguments
        x: 4D tensor, the tensor to feed through the block
        nfeats: Integer, number of feature maps for conv layers.
        ksize: Integer, width and height of conv kernels in first convolution.
        nskipped: Integer, number of conv layers for the residual function.
        elu: Boolean, whether to use ELU or BN+RELU.

    # Input shape
        4D tensor with shape:
        `(batch, channels, rows, cols)`

    # Output shape
        4D tensor with shape:
        `(batch, filters, rows, cols)`
    """
    y0 = Conv2D(nfeats, ksize, padding='same')(x)
    y = y0
    for i in range(nskipped):
        if elu:
            y = ELU()(y)
        else:
            y = BatchNormalization(axis=1)(y)
            y = Activation('relu')(y)
        y = Conv2D(nfeats, 1, padding='same')(y)
    return layers.add([y0, y])


def getwhere(x):
    ''' Calculate the 'where' mask that contains switches indicating which
    index contained the max value when MaxPool2D was applied.  Using the
    gradient of the sum is a nice trick to keep everything high level.'''
    y_prepool, y_postpool = x
    return K.gradients(K.sum(y_postpool), y_prepool)

# This example assume 'channels_first' data format.
K.set_image_data_format('channels_first')

# input image dimensions
img_rows, img_cols = 28, 28

# the data, split between train and test sets
(x_train, _), (x_test, _) = mnist.load_data()

x_train = x_train.reshape(x_train.shape[0], 1, img_rows, img_cols)
x_test = x_test.reshape(x_test.shape[0], 1, img_rows, img_cols)
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# The size of the kernel used for the MaxPooling2D
pool_size = 2
# The total number of feature maps at each layer
nfeats = [8, 16, 32, 64, 128]
# The sizes of the pooling kernel at each layer
pool_sizes = np.array([1, 1, 1, 1, 1]) * pool_size
# The convolution kernel size
ksize = 3
# Number of epochs to train for
epochs = 5
# Batch size during training
batch_size = 128

if pool_size == 2:
    # if using a 5 layer net of pool_size = 2
    x_train = np.pad(x_train, [[0, 0], [0, 0], [2, 2], [2, 2]],
                     mode='constant')
    x_test = np.pad(x_test, [[0, 0], [0, 0], [2, 2], [2, 2]], mode='constant')
    nlayers = 5
elif pool_size == 3:
    # if using a 3 layer net of pool_size = 3
    x_train = x_train[:, :, :-1, :-1]
    x_test = x_test[:, :, :-1, :-1]
    nlayers = 3
else:
    import sys
    sys.exit('Script supports pool_size of 2 and 3.')

# Shape of input to train on (note that model is fully convolutional however)
input_shape = x_train.shape[1:]
# The final list of the size of axis=1 for all layers, including input
nfeats_all = [input_shape[0]] + nfeats

# First build the encoder, all the while keeping track of the 'where' masks
img_input = Input(shape=input_shape)

# We push the 'where' masks to the following list
wheres = [None] * nlayers
y = img_input
for i in range(nlayers):
    y_prepool = convresblock(y, nfeats=nfeats_all[i + 1], ksize=ksize)
    y = MaxPooling2D(pool_size=(pool_sizes[i], pool_sizes[i]))(y_prepool)
    wheres[i] = layers.Lambda(
        getwhere, output_shape=lambda x: x[0])([y_prepool, y])

# Now build the decoder, and use the stored 'where' masks to place the features
for i in range(nlayers):
    ind = nlayers - 1 - i
    y = UpSampling2D(size=(pool_sizes[ind], pool_sizes[ind]))(y)
    y = layers.multiply([y, wheres[ind]])
    y = convresblock(y, nfeats=nfeats_all[ind], ksize=ksize)

# Use hard_simgoid to clip range of reconstruction
y = Activation('hard_sigmoid')(y)

# Define the model and it's mean square error loss, and compile it with Adam
model = Model(img_input, y)
model.compile('adam', 'mse')

# Fit the model
model.fit(x_train, x_train,
          batch_size=batch_size,
          epochs=epochs,
          validation_data=(x_test, x_test))

# Plot
x_recon = model.predict(x_test[:25])
x_plot = np.concatenate((x_test[:25], x_recon), axis=1)
x_plot = x_plot.reshape((5, 10, input_shape[-2], input_shape[-1]))
x_plot = np.vstack([np.hstack(x) for x in x_plot])
plt.figure()
plt.axis('off')
plt.title('Test Samples: Originals/Reconstructions')
plt.imshow(x_plot, interpolation='none', cmap='gray')
plt.savefig('reconstructions.png')

'''
#Train a simple deep CNN on the CIFAR10 small images dataset.

It gets to 75% validation accuracy in 25 epochs, and 79% after 50 epochs.
(it's still underfitting at that point, though).
'''

from __future__ import print_function
import keras
from keras.datasets import cifar10
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Conv2D, MaxPooling2D
import os

batch_size = 32
num_classes = 10
epochs = 100
data_augmentation = True
num_predictions = 20
save_dir = os.path.join(os.getcwd(), 'saved_models')
model_name = 'keras_cifar10_trained_model.h5'

# The data, split between train and test sets:
(x_train, y_train), (x_test, y_test) = cifar10.load_data()
print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# Convert class vectors to binary class matrices.
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

model = Sequential()
model.add(Conv2D(32, (3, 3), padding='same',
                 input_shape=x_train.shape[1:]))
model.add(Activation('relu'))
model.add(Conv2D(32, (3, 3)))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Conv2D(64, (3, 3), padding='same'))
model.add(Activation('relu'))
model.add(Conv2D(64, (3, 3)))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(512))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes))
model.add(Activation('softmax'))

# initiate RMSprop optimizer
opt = keras.optimizers.RMSprop(learning_rate=0.0001, decay=1e-6)

# Let's train the model using RMSprop
model.compile(loss='categorical_crossentropy',
              optimizer=opt,
              metrics=['accuracy'])

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255

if not data_augmentation:
    print('Not using data augmentation.')
    model.fit(x_train, y_train,
              batch_size=batch_size,
              epochs=epochs,
              validation_data=(x_test, y_test),
              shuffle=True)
else:
    print('Using real-time data augmentation.')
    # This will do preprocessing and realtime data augmentation:
    datagen = ImageDataGenerator(
        featurewise_center=False,  # set input mean to 0 over the dataset
        samplewise_center=False,  # set each sample mean to 0
        featurewise_std_normalization=False,  # divide inputs by std of the dataset
        samplewise_std_normalization=False,  # divide each input by its std
        zca_whitening=False,  # apply ZCA whitening
        zca_epsilon=1e-06,  # epsilon for ZCA whitening
        rotation_range=0,  # randomly rotate images in the range (degrees, 0 to 180)
        # randomly shift images horizontally (fraction of total width)
        width_shift_range=0.1,
        # randomly shift images vertically (fraction of total height)
        height_shift_range=0.1,
        shear_range=0.,  # set range for random shear
        zoom_range=0.,  # set range for random zoom
        channel_shift_range=0.,  # set range for random channel shifts
        # set mode for filling points outside the input boundaries
        fill_mode='nearest',
        cval=0.,  # value used for fill_mode = "constant"
        horizontal_flip=True,  # randomly flip images
        vertical_flip=False,  # randomly flip images
        # set rescaling factor (applied before any other transformation)
        rescale=None,
        # set function that will be applied on each input
        preprocessing_function=None,
        # image data format, either "channels_first" or "channels_last"
        data_format=None,
        # fraction of images reserved for validation (strictly between 0 and 1)
        validation_split=0.0)

    # Compute quantities required for feature-wise normalization
    # (std, mean, and principal components if ZCA whitening is applied).
    datagen.fit(x_train)

    # Fit the model on the batches generated by datagen.flow().
    model.fit_generator(datagen.flow(x_train, y_train,
                                     batch_size=batch_size),
                        epochs=epochs,
                        validation_data=(x_test, y_test),
                        workers=4)

# Save model and weights
if not os.path.isdir(save_dir):
    os.makedirs(save_dir)
model_path = os.path.join(save_dir, model_name)
model.save(model_path)
print('Saved trained model at %s ' % model_path)

# Score trained model.
scores = model.evaluate(x_test, y_test, verbose=1)
print('Test loss:', scores[0])
print('Test accuracy:', scores[1])

"""
#This script demonstrates the use of a convolutional LSTM network.

This network is used to predict the next frame of an artificially
generated movie which contains moving squares.
"""
from keras.models import Sequential
from keras.layers.convolutional import Conv3D
from keras.layers.convolutional_recurrent import ConvLSTM2D
from keras.layers.normalization import BatchNormalization
import numpy as np
import pylab as plt

# We create a layer which take as input movies of shape
# (n_frames, width, height, channels) and returns a movie
# of identical shape.

seq = Sequential()
seq.add(ConvLSTM2D(filters=40, kernel_size=(3, 3),
                   input_shape=(None, 40, 40, 1),
                   padding='same', return_sequences=True))
seq.add(BatchNormalization())

seq.add(ConvLSTM2D(filters=40, kernel_size=(3, 3),
                   padding='same', return_sequences=True))
seq.add(BatchNormalization())

seq.add(ConvLSTM2D(filters=40, kernel_size=(3, 3),
                   padding='same', return_sequences=True))
seq.add(BatchNormalization())

seq.add(ConvLSTM2D(filters=40, kernel_size=(3, 3),
                   padding='same', return_sequences=True))
seq.add(BatchNormalization())

seq.add(Conv3D(filters=1, kernel_size=(3, 3, 3),
               activation='sigmoid',
               padding='same', data_format='channels_last'))
seq.compile(loss='binary_crossentropy', optimizer='adadelta')


# Artificial data generation:
# Generate movies with 3 to 7 moving squares inside.
# The squares are of shape 1x1 or 2x2 pixels,
# which move linearly over time.
# For convenience we first create movies with bigger width and height (80x80)
# and at the end we select a 40x40 window.

def generate_movies(n_samples=1200, n_frames=15):
    row = 80
    col = 80
    noisy_movies = np.zeros((n_samples, n_frames, row, col, 1), dtype=np.float)
    shifted_movies = np.zeros((n_samples, n_frames, row, col, 1),
                              dtype=np.float)

    for i in range(n_samples):
        # Add 3 to 7 moving squares
        n = np.random.randint(3, 8)

        for j in range(n):
            # Initial position
            xstart = np.random.randint(20, 60)
            ystart = np.random.randint(20, 60)
            # Direction of motion
            directionx = np.random.randint(0, 3) - 1
            directiony = np.random.randint(0, 3) - 1

            # Size of the square
            w = np.random.randint(2, 4)

            for t in range(n_frames):
                x_shift = xstart + directionx * t
                y_shift = ystart + directiony * t
                noisy_movies[i, t, x_shift - w: x_shift + w,
                             y_shift - w: y_shift + w, 0] += 1

                # Make it more robust by adding noise.
                # The idea is that if during inference,
                # the value of the pixel is not exactly one,
                # we need to train the network to be robust and still
                # consider it as a pixel belonging to a square.
                if np.random.randint(0, 2):
                    noise_f = (-1)**np.random.randint(0, 2)
                    noisy_movies[i, t,
                                 x_shift - w - 1: x_shift + w + 1,
                                 y_shift - w - 1: y_shift + w + 1,
                                 0] += noise_f * 0.1

                # Shift the ground truth by 1
                x_shift = xstart + directionx * (t + 1)
                y_shift = ystart + directiony * (t + 1)
                shifted_movies[i, t, x_shift - w: x_shift + w,
                               y_shift - w: y_shift + w, 0] += 1

    # Cut to a 40x40 window
    noisy_movies = noisy_movies[::, ::, 20:60, 20:60, ::]
    shifted_movies = shifted_movies[::, ::, 20:60, 20:60, ::]
    noisy_movies[noisy_movies >= 1] = 1
    shifted_movies[shifted_movies >= 1] = 1
    return noisy_movies, shifted_movies

# Train the network
noisy_movies, shifted_movies = generate_movies(n_samples=1200)
seq.fit(noisy_movies[:1000], shifted_movies[:1000], batch_size=10,
        epochs=300, validation_split=0.05)

# Testing the network on one movie
# feed it with the first 7 positions and then
# predict the new positions
which = 1004
track = noisy_movies[which][:7, ::, ::, ::]

for j in range(16):
    new_pos = seq.predict(track[np.newaxis, ::, ::, ::, ::])
    new = new_pos[::, -1, ::, ::, ::]
    track = np.concatenate((track, new), axis=0)


# And then compare the predictions
# to the ground truth
track2 = noisy_movies[which][::, ::, ::, ::]
for i in range(15):
    fig = plt.figure(figsize=(10, 5))

    ax = fig.add_subplot(121)

    if i >= 7:
        ax.text(1, 3, 'Predictions !', fontsize=20, color='w')
    else:
        ax.text(1, 3, 'Initial trajectory', fontsize=20)

    toplot = track[i, ::, ::, 0]

    plt.imshow(toplot)
    ax = fig.add_subplot(122)
    plt.text(1, 3, 'Ground truth', fontsize=20)

    toplot = track2[i, ::, ::, 0]
    if i >= 2:
        toplot = shifted_movies[which][i - 1, ::, ::, 0]

    plt.imshow(toplot)
    plt.savefig('%i_animate.png' % (i + 1))

'''Neural style transfer with Keras.

Run the script with:
```
python neural_style_transfer.py path_to_your_base_image.jpg \
    path_to_your_reference.jpg prefix_for_results
```
e.g.:
```
python neural_style_transfer.py img/tuebingen.jpg \
    img/starry_night.jpg results/my_result
```
Optional parameters:
```
--iter, To specify the number of iterations \
    the style transfer takes place (Default is 10)
--content_weight, The weight given to the content loss (Default is 0.025)
--style_weight, The weight given to the style loss (Default is 1.0)
--tv_weight, The weight given to the total variation loss (Default is 1.0)
```

It is preferable to run this script on GPU, for speed.

Example result: https://twitter.com/fchollet/status/686631033085677568

# Details

Style transfer consists in generating an image
with the same "content" as a base image, but with the
"style" of a different picture (typically artistic).

This is achieved through the optimization of a loss function
that has 3 components: "style loss", "content loss",
and "total variation loss":

- The total variation loss imposes local spatial continuity between
the pixels of the combination image, giving it visual coherence.

- The style loss is where the deep learning keeps in --that one is defined
using a deep convolutional neural network. Precisely, it consists in a sum of
L2 distances between the Gram matrices of the representations of
the base image and the style reference image, extracted from
different layers of a convnet (trained on ImageNet). The general idea
is to capture color/texture information at different spatial
scales (fairly large scales --defined by the depth of the layer considered).

 - The content loss is a L2 distance between the features of the base
image (extracted from a deep layer) and the features of the combination image,
keeping the generated image close enough to the original one.

# References
    - [A Neural Algorithm of Artistic Style](http://arxiv.org/abs/1508.06576)
'''

from __future__ import print_function
from keras.preprocessing.image import load_img, save_img, img_to_array
import numpy as np
from scipy.optimize import fmin_l_bfgs_b
import time
import argparse

from keras.applications import vgg19
from keras import backend as K

parser = argparse.ArgumentParser(description='Neural style transfer with Keras.')
parser.add_argument('base_image_path', metavar='base', type=str,
                    help='Path to the image to transform.')
parser.add_argument('style_reference_image_path', metavar='ref', type=str,
                    help='Path to the style reference image.')
parser.add_argument('result_prefix', metavar='res_prefix', type=str,
                    help='Prefix for the saved results.')
parser.add_argument('--iter', type=int, default=10, required=False,
                    help='Number of iterations to run.')
parser.add_argument('--content_weight', type=float, default=0.025, required=False,
                    help='Content weight.')
parser.add_argument('--style_weight', type=float, default=1.0, required=False,
                    help='Style weight.')
parser.add_argument('--tv_weight', type=float, default=1.0, required=False,
                    help='Total Variation weight.')

args = parser.parse_args()
base_image_path = args.base_image_path
style_reference_image_path = args.style_reference_image_path
result_prefix = args.result_prefix
iterations = args.iter

# these are the weights of the different loss components
total_variation_weight = args.tv_weight
style_weight = args.style_weight
content_weight = args.content_weight

# dimensions of the generated picture.
width, height = load_img(base_image_path).size
img_nrows = 400
img_ncols = int(width * img_nrows / height)

# util function to open, resize and format pictures into appropriate tensors


def preprocess_image(image_path):
    img = load_img(image_path, target_size=(img_nrows, img_ncols))
    img = img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = vgg19.preprocess_input(img)
    return img

# util function to convert a tensor into a valid image


def deprocess_image(x):
    if K.image_data_format() == 'channels_first':
        x = x.reshape((3, img_nrows, img_ncols))
        x = x.transpose((1, 2, 0))
    else:
        x = x.reshape((img_nrows, img_ncols, 3))
    # Remove zero-center by mean pixel
    x[:, :, 0] += 103.939
    x[:, :, 1] += 116.779
    x[:, :, 2] += 123.68
    # 'BGR'->'RGB'
    x = x[:, :, ::-1]
    x = np.clip(x, 0, 255).astype('uint8')
    return x

# get tensor representations of our images
base_image = K.variable(preprocess_image(base_image_path))
style_reference_image = K.variable(preprocess_image(style_reference_image_path))

# this will contain our generated image
if K.image_data_format() == 'channels_first':
    combination_image = K.placeholder((1, 3, img_nrows, img_ncols))
else:
    combination_image = K.placeholder((1, img_nrows, img_ncols, 3))

# combine the 3 images into a single Keras tensor
input_tensor = K.concatenate([base_image,
                              style_reference_image,
                              combination_image], axis=0)

# build the VGG19 network with our 3 images as input
# the model will be loaded with pre-trained ImageNet weights
model = vgg19.VGG19(input_tensor=input_tensor,
                    weights='imagenet', include_top=False)
print('Model loaded.')

# get the symbolic outputs of each "key" layer (we gave them unique names).
outputs_dict = dict([(layer.name, layer.output) for layer in model.layers])

# compute the neural style loss
# first we need to define 4 util functions

# the gram matrix of an image tensor (feature-wise outer product)


def gram_matrix(x):
    assert K.ndim(x) == 3
    if K.image_data_format() == 'channels_first':
        features = K.batch_flatten(x)
    else:
        features = K.batch_flatten(K.permute_dimensions(x, (2, 0, 1)))
    gram = K.dot(features, K.transpose(features))
    return gram

# the "style loss" is designed to maintain
# the style of the reference image in the generated image.
# It is based on the gram matrices (which capture style) of
# feature maps from the style reference image
# and from the generated image


def style_loss(style, combination):
    assert K.ndim(style) == 3
    assert K.ndim(combination) == 3
    S = gram_matrix(style)
    C = gram_matrix(combination)
    channels = 3
    size = img_nrows * img_ncols
    return K.sum(K.square(S - C)) / (4.0 * (channels ** 2) * (size ** 2))

# an auxiliary loss function
# designed to maintain the "content" of the
# base image in the generated image


def content_loss(base, combination):
    return K.sum(K.square(combination - base))

# the 3rd loss function, total variation loss,
# designed to keep the generated image locally coherent


def total_variation_loss(x):
    assert K.ndim(x) == 4
    if K.image_data_format() == 'channels_first':
        a = K.square(
            x[:, :, :img_nrows - 1, :img_ncols - 1] - x[:, :, 1:, :img_ncols - 1])
        b = K.square(
            x[:, :, :img_nrows - 1, :img_ncols - 1] - x[:, :, :img_nrows - 1, 1:])
    else:
        a = K.square(
            x[:, :img_nrows - 1, :img_ncols - 1, :] - x[:, 1:, :img_ncols - 1, :])
        b = K.square(
            x[:, :img_nrows - 1, :img_ncols - 1, :] - x[:, :img_nrows - 1, 1:, :])
    return K.sum(K.pow(a + b, 1.25))


# combine these loss functions into a single scalar
loss = K.variable(0.0)
layer_features = outputs_dict['block5_conv2']
base_image_features = layer_features[0, :, :, :]
combination_features = layer_features[2, :, :, :]
loss = loss + content_weight * content_loss(base_image_features,
                                            combination_features)

feature_layers = ['block1_conv1', 'block2_conv1',
                  'block3_conv1', 'block4_conv1',
                  'block5_conv1']
for layer_name in feature_layers:
    layer_features = outputs_dict[layer_name]
    style_reference_features = layer_features[1, :, :, :]
    combination_features = layer_features[2, :, :, :]
    sl = style_loss(style_reference_features, combination_features)
    loss = loss + (style_weight / len(feature_layers)) * sl
loss = loss + total_variation_weight * total_variation_loss(combination_image)

# get the gradients of the generated image wrt the loss
grads = K.gradients(loss, combination_image)

outputs = [loss]
if isinstance(grads, (list, tuple)):
    outputs += grads
else:
    outputs.append(grads)

f_outputs = K.function([combination_image], outputs)


def eval_loss_and_grads(x):
    if K.image_data_format() == 'channels_first':
        x = x.reshape((1, 3, img_nrows, img_ncols))
    else:
        x = x.reshape((1, img_nrows, img_ncols, 3))
    outs = f_outputs([x])
    loss_value = outs[0]
    if len(outs[1:]) == 1:
        grad_values = outs[1].flatten().astype('float64')
    else:
        grad_values = np.array(outs[1:]).flatten().astype('float64')
    return loss_value, grad_values

# this Evaluator class makes it possible
# to compute loss and gradients in one pass
# while retrieving them via two separate functions,
# "loss" and "grads". This is done because scipy.optimize
# requires separate functions for loss and gradients,
# but computing them separately would be inefficient.


class Evaluator(object):

    def __init__(self):
        self.loss_value = None
        self.grads_values = None

    def loss(self, x):
        assert self.loss_value is None
        loss_value, grad_values = eval_loss_and_grads(x)
        self.loss_value = loss_value
        self.grad_values = grad_values
        return self.loss_value

    def grads(self, x):
        assert self.loss_value is not None
        grad_values = np.copy(self.grad_values)
        self.loss_value = None
        self.grad_values = None
        return grad_values


evaluator = Evaluator()

# run scipy-based optimization (L-BFGS) over the pixels of the generated image
# so as to minimize the neural style loss
x = preprocess_image(base_image_path)

for i in range(iterations):
    print('Start of iteration', i)
    start_time = time.time()
    x, min_val, info = fmin_l_bfgs_b(evaluator.loss, x.flatten(),
                                     fprime=evaluator.grads, maxfun=20)
    print('Current loss value:', min_val)
    # save current generated image
    img = deprocess_image(x.copy())
    fname = result_prefix + '_at_iteration_%d.png' % i
    save_img(fname, img)
    end_time = time.time()
    print('Image saved as', fname)
    print('Iteration %d completed in %ds' % (i, end_time - start_time))

