from setuptools import setup
from setuptools import find_packages


setup(name='Keras',
      version='1.0.2',
      description='Deep Learning for Python',
      author='Francois Chollet',
      author_email='francois.chollet@gmail.com',
      url='https://github.com/fchollet/keras',
      download_url='https://github.com/fchollet/keras/tarball/1.0.2',
      license='MIT',
      install_requires=['theano', 'pyyaml', 'six'],
      extras_require={
          'h5py': ['h5py'],
      },
      packages=find_packages())

import numpy as np
from . import backend as K


def binary_accuracy(y_true, y_pred):
    return K.mean(K.equal(y_true, K.round(y_pred)))


def categorical_accuracy(y_true, y_pred):
    return K.mean(K.equal(K.argmax(y_true, axis=-1),
                  K.argmax(y_pred, axis=-1)))


def sparse_categorical_accuracy(y_true, y_pred):
    return K.mean(K.equal(K.max(y_true, axis=-1),
                          K.cast(K.argmax(y_pred, axis=-1), K.floatx())))


def mean_squared_error(y_true, y_pred):
    return K.mean(K.square(y_pred - y_true))


def mean_absolute_error(y_true, y_pred):
    return K.mean(K.abs(y_pred - y_true))


def mean_absolute_percentage_error(y_true, y_pred):
    diff = K.abs((y_true - y_pred) / K.clip(K.abs(y_true), K.epsilon(), np.inf))
    return 100. * K.mean(diff)


def mean_squared_logarithmic_error(y_true, y_pred):
    first_log = K.log(K.clip(y_pred, K.epsilon(), np.inf) + 1.)
    second_log = K.log(K.clip(y_true, K.epsilon(), np.inf) + 1.)
    return K.mean(K.square(first_log - second_log))


def squared_hinge(y_true, y_pred):
    return K.mean(K.square(K.maximum(1. - y_true * y_pred, 0.)))


def hinge(y_true, y_pred):
    return K.mean(K.maximum(1. - y_true * y_pred, 0.))


def categorical_crossentropy(y_true, y_pred):
    '''Expects a binary class matrix instead of a vector of scalar classes.
    '''
    return K.mean(K.categorical_crossentropy(y_pred, y_true))


def sparse_categorical_crossentropy(y_true, y_pred):
    '''expects an array of integer classes.
    Note: labels shape must have the same number of dimensions as output shape.
    If you get a shape error, add a length-1 dimension to labels.
    '''
    return K.mean(K.sparse_categorical_crossentropy(y_pred, y_true))


def binary_crossentropy(y_true, y_pred):
    return K.mean(K.binary_crossentropy(y_pred, y_true))


def poisson(y_true, y_pred):
    return K.mean(y_pred - y_true * K.log(y_pred + K.epsilon()))


def cosine_proximity(y_true, y_pred):
    y_true = K.l2_normalize(y_true, axis=-1)
    y_pred = K.l2_normalize(y_pred, axis=-1)
    return -K.mean(y_true * y_pred)


# aliases
mse = MSE = mean_squared_error
mae = MAE = mean_absolute_error
mape = MAPE = mean_absolute_percentage_error
msle = MSLE = mean_squared_logarithmic_error
cosine = cosine_proximity


from .utils.generic_utils import get_from_module
def get(identifier):
    return get_from_module(identifier, globals(), 'metric')

from __future__ import print_function
import warnings
import copy

from . import backend as K
from .engine.training import Model
from .engine.topology import get_source_inputs, Node
from .legacy.models import Graph


def model_from_config(config, custom_objects={}):
    from keras.utils.layer_utils import layer_from_config
    return layer_from_config(config, custom_objects=custom_objects)


def model_from_yaml(yaml_string, custom_objects={}):
    '''Parses a yaml model configuration file
    and returns a model instance.
    '''
    import yaml
    from keras.utils.layer_utils import layer_from_config
    config = yaml.load(yaml_string)
    return layer_from_config(config, custom_objects=custom_objects)


def model_from_json(json_string, custom_objects={}):
    '''Parses a JSON model configuration file
    and returns a model instance.
    '''
    import json
    from keras.utils.layer_utils import layer_from_config
    config = json.loads(json_string)
    return layer_from_config(config, custom_objects=custom_objects)


class Sequential(Model):
    '''Linear stack of layers.

    # Arguments
        layers: list of layers to add to the model.

    # Note
        The first layer passed to a Sequential model
        should have a defined input shape. What that
        means is that it should have received an `input_shape`
        or `batch_input_shape` argument,
        or for some type of layers (recurrent, Dense...)
        an `input_dim` argument.

    # Example

        ```python
            model = Sequential()
            # first layer must have a defined input shape
            model.add(Dense(32, input_dim=500))
            # afterwards, Keras does automatic shape inference
            model.add(Dense(32))

            # also possible (equivalent to the above):
            model = Sequential()
            model.add(Dense(32, input_shape=(500,)))
            model.add(Dense(32))

            # also possible (equivalent to the above):
            model = Sequential()
            # here the batch dimension is None,
            # which means any batch size will be accepted by the model.
            model.add(Dense(32, batch_input_shape=(None, 500)))
            model.add(Dense(32))
        ```
    '''
    def __init__(self, layers=[], name=None):
        self.layers = []  # stack of layers
        self.model = None  # internal Model instance
        self.inputs = []  # tensors
        self.outputs = []  # tensors (length 1)

        # model attributes
        self.inbound_nodes = []
        self.outbound_nodes = []
        self.built = False

        if not name:
            prefix = 'sequential_'
            name = prefix + str(K.get_uid(prefix))
        self.name = name

        for layer in layers:
            self.add(layer)

    def add(self, layer):
        '''Adds a layer instance on top of the layer stack.

        # Arguments
            layer: layer instance.
        '''
        if not self.outputs:
            # first layer in model: check that it is an input layer
            if len(layer.inbound_nodes) == 0:
                # create an input layer
                if not hasattr(layer, 'batch_input_shape'):
                    raise Exception('The first layer in a Sequential model must '
                                    'get an `input_shape` or '
                                    '`batch_input_shape` argument.')
                batch_input_shape = layer.batch_input_shape
                if hasattr(layer, 'input_dtype'):
                    input_dtype = layer.input_dtype
                else:
                    input_dtype = None
                layer.create_input_layer(batch_input_shape, input_dtype)

            if len(layer.inbound_nodes) != 1:
                raise Exception('A layer added to a Sequential model must '
                                'not already be connected somewhere else. '
                                'Model received layer ' + layer.name +
                                ' which has ' + str(len(layer.inbound_nodes)) +
                                ' pre-existing inbound connections.')

            if len(layer.inbound_nodes[0].output_tensors) != 1:
                raise Exception('All layers in a Sequential model '
                                'should have a single output tensor. '
                                'For multi-output layers, '
                                'use the functional API.')

            self.outputs = [layer.inbound_nodes[0].output_tensors[0]]
            self.inputs = get_source_inputs(self.outputs[0])

            # We create an input node, which we will keep updated
            # as we add more layers
            Node(outbound_layer=self,
                 inbound_layers=[],
                 node_indices=[],
                 tensor_indices=[],
                 input_tensors=self.inputs,
                 output_tensors=self.outputs,
                 # no model-level masking for now
                 input_masks=[None for _ in self.inputs],
                 output_masks=[None],
                 input_shapes=[x._keras_shape for x in self.inputs],
                 output_shapes=[self.outputs[0]._keras_shape])
        else:
            output_tensor = layer(self.outputs[0])
            if type(output_tensor) is list:
                raise Exception('All layers in a Sequential model '
                                'should have a single output tensor. '
                                'For multi-output layers, '
                                'use the functional API.')
            self.outputs = [output_tensor]
            # update self.inbound_nodes
            self.inbound_nodes[0].output_tensors = self.outputs
            self.inbound_nodes[0].output_shapes = [self.outputs[0]._keras_shape]

        self.layers.append(layer)
        self.built = False

    def call(self, x, mask=None):
        if not self.built:
            self.build()
        return self.model.call(x, mask)

    def build(self, input_shape=None):
        if not self.inputs or not self.outputs:
            raise Exception('Sequential model cannot be built: model is empty.'
                            ' Add some layers first.')
        # actually create the model
        self.model = Model(self.inputs, self.outputs[0], name=self.name + '_model')

        # mirror model attributes
        self.supports_masking = self.model.supports_masking
        self._output_mask_cache = self.model._output_mask_cache
        self._output_tensor_cache = self.model._output_tensor_cache
        self._output_shape_cache = self.model._output_shape_cache
        self.input_layers = self.model.input_layers
        self.input_layers_node_indices = self.model.input_layers_node_indices
        self.input_layers_tensor_indices = self.model.input_layers_tensor_indices
        self.output_layers = self.model.output_layers
        self.output_layers_node_indices = self.model.output_layers_node_indices
        self.output_layers_tensor_indices = self.model.output_layers_tensor_indices
        self.nodes_by_depth = self.model.nodes_by_depth
        self.container_nodes = self.model.container_nodes
        self.output_names = self.model.output_names
        self.input_names = self.model.input_names

        # make sure child model callbacks will call the parent Sequential model:
        self.model.callback_model = self

        self.built = True

    @property
    def uses_learning_phase(self):
        if not self.built:
            self.build()
        return self.model.uses_learning_phase

    @property
    def flattened_layers(self):
        layers = []
        if self.layers[0].__class__.__name__ == 'Merge':
            merge = self.layers[0]
            for layer in merge.layers:
                if hasattr(layer, 'flattened_layers'):
                    for sublayer in layer.flattened_layers:
                        if sublayer not in layers:
                            layers.append(sublayer)
                elif hasattr(layer, 'layers'):
                    for sublayer in layer.layers:
                        if sublayer not in layers:
                            layers.append(sublayer)
                else:
                    if layer not in layers:
                        layers.append(layer)
        else:
            if self.layers[0] not in layers:
                layers.append(self.layers[0])
        for layer in self.layers[1:]:
            if layer not in layers:
                layers.append(layer)
        return layers

    def _gather_list_attr(self, attr):
        all_attrs = []
        for layer in self.flattened_layers:
            all_attrs += getattr(layer, attr, [])
        return all_attrs

    def _gather_dict_attr(self, attr):
        all_attrs = {}
        for layer in self.flattened_layers:
            layer_dict = getattr(layer, attr, {})
            all_attrs = dict(list(all_attrs.items()) +
                             list(layer_dict.items()))
        return all_attrs

    @property
    def trainable_weights(self):
        # support for legacy behavior
        return self._gather_list_attr('trainable_weights')

    @property
    def non_trainable_weights(self):
        # support for legacy behavior
        return self._gather_list_attr('non_trainable_weights')

    @property
    def updates(self):
        # support for legacy behavior
        return self._gather_list_attr('updates')

    @property
    def state_updates(self):
        # support for legacy behavior
        return self._gather_list_attr('state_updates')

    @property
    def regularizers(self):
        # support for legacy behavior
        return self._gather_list_attr('regularizers')

    @property
    def constraints(self):
        # support for legacy behavior
        return self._gather_dict_attr('constraints')

    def get_weights(self):
        '''Returns the weights of the model,
        as a flat list of Numpy arrays.
        '''
        # support for legacy behavior
        weights = []
        for layer in self.flattened_layers:
            weights += layer.get_weights()
        return weights

    def set_weights(self, weights):
        '''Sets the weights of the model.
        The `weights` argument should be a list
        of Numpy arrays with shapes and types matching
        the output of `model.get_weights()`.
        '''
        # support for legacy behavior
        for layer in self.flattened_layers:
            nb_param = len(layer.get_weights())
            layer.set_weights(weights[:nb_param])
            weights = weights[nb_param:]

    @property
    def validation_data(self):
        return self.model.validation_data

    @property
    def training_data(self):
        return self.model.training_data

    def compile(self, optimizer, loss,
                metrics=[],
                sample_weight_mode=None,
                **kwargs):
        '''Configures the learning process.

        # Arguments
            optimizer: str (name of optimizer) or optimizer object.
                See [optimizers](/optimizers).
            loss: str (name of objective function) or objective function.
                See [objectives](/objectives).
            metrics: list of metrics to be evaluated by the model
                during training and testing.
                Typically you will use `metrics=['accuracy']`.
            sample_weight_mode: if you need to do timestep-wise
                sample weighting (2D weights), set this to "temporal".
                "None" defaults to sample-wise weights (1D).
            kwargs: for Theano backend, these are passed into K.function.
                Ignored for Tensorflow backend.

        # Example
            ```python
                model = Sequential()
                model.add(Dense(32, input_shape=(500,)))
                model.add(Dense(10, activation='softmax'))
                model.compile(optimizer='rmsprop',
                              loss='categorical_crossentropy',
                              metrics=['accuracy'])
            ```
        '''
        # create the underlying model
        self.build()
        # legacy kwarg support
        if 'class_mode' in kwargs:
            warnings.warn('"class_mode" argument is deprecated, '
                          'please remove it.')
            kwargs.pop('class_mode')
        # call compile method of Model class
        self.model.compile(optimizer, loss,
                           metrics=metrics,
                           sample_weight_mode=sample_weight_mode,
                           **kwargs)
        self.optimizer = self.model.optimizer
        self.loss = self.model.loss
        self.metrics_names = self.model.metrics_names
        self.sample_weight_mode = self.model.sample_weight_mode

    def fit(self, x, y, batch_size=32, nb_epoch=10, verbose=1, callbacks=[],
            validation_split=0., validation_data=None, shuffle=True,
            class_weight=None, sample_weight=None, **kwargs):
        '''Trains the model for a fixed number of epochs.

        # Arguments
            x: input data, as a Numpy array or list of Numpy arrays
                (if the model has multiple inputs).
            y: labels, as a Numpy array.
            batch_size: integer. Number of samples per gradient update.
            nb_epoch: integer, the number of epochs to train the model.
            verbose: 0 for no logging to stdout,
                1 for progress bar logging, 2 for one log line per epoch.
            callbacks: list of `keras.callbacks.Callback` instances.
                List of callbacks to apply during training.
                See [callbacks](/callbacks).
            validation_split: float (0. < x < 1).
                Fraction of the data to use as held-out validation data.
            validation_data: tuple (X, y) to be used as held-out
                validation data. Will override validation_split.
            shuffle: boolean or str (for 'batch').
                Whether to shuffle the samples at each epoch.
                'batch' is a special option for dealing with the
                limitations of HDF5 data; it shuffles in batch-sized chunks.
            class_weight: dictionary mapping classes to a weight value,
                used for scaling the loss function (during training only).
            sample_weight: Numpy array of weights for
                the training samples, used for scaling the loss function
                (during training only). You can either pass a flat (1D)
                Numpy array with the same length as the input samples
                (1:1 mapping between weights and samples),
                or in the case of temporal data,
                you can pass a 2D array with shape (samples, sequence_length),
                to apply a different weight to every timestep of every sample.
                In this case you should make sure to specify
                sample_weight_mode="temporal" in compile().

        # Returns
            A `History` object. Its `History.history` attribute is
            a record of training loss values and metrics values
            at successive epochs, as well as validation loss values
            and validation metrics values (if applicable).
        '''
        if self.model is None:
            raise Exception('The model needs to be compiled before being used.')
        if 'show_accuracy' in kwargs:
            kwargs.pop('show_accuracy')
            warnings.warn('The "show_accuracy" argument is deprecated, '
                          'instead you should pass the "accuracy" metric to '
                          'the model at compile time:\n'
                          '`model.compile(optimizer, loss, '
                          'metrics=["accuracy"])`')
        if kwargs:
            raise Exception('Received unknown keyword arguments: ' +
                            str(kwargs))
        return self.model.fit(x, y,
                              batch_size=batch_size,
                              nb_epoch=nb_epoch,
                              verbose=verbose,
                              callbacks=callbacks,
                              validation_split=validation_split,
                              validation_data=validation_data,
                              shuffle=shuffle,
                              class_weight=class_weight,
                              sample_weight=sample_weight)

    def evaluate(self, x, y, batch_size=32, verbose=1,
                 sample_weight=None, **kwargs):
        '''Computes the loss on some input data, batch by batch.

        # Arguments
            x: input data, as a Numpy array or list of Numpy arrays
                (if the model has multiple inputs).
            y: labels, as a Numpy array.
            batch_size: integer. Number of samples per gradient update.
            verbose: verbosity mode, 0 or 1.
            sample_weight: sample weights, as a Numpy array.

        # Returns
            Scalar test loss (if the model has no metrics)
            or list of scalars (if the model computes other metrics).
            The attribute `model.metrics_names` will give you
            the display labels for the scalar outputs.
        '''
        if self.model is None:
            raise Exception('The model needs to be compiled before being used.')
        if 'show_accuracy' in kwargs:
            kwargs.pop('show_accuracy')
            warnings.warn('The "show_accuracy" argument is deprecated, '
                          'instead you should pass the "accuracy" metric to '
                          'the model at compile time:\n'
                          '`model.compile(optimizer, loss, '
                          'metrics=["accuracy"])`')
        if kwargs:
            raise Exception('Received unknown keyword arguments: ' +
                            str(kwargs))
        return self.model.evaluate(x, y,
                                   batch_size=batch_size,
                                   verbose=verbose,
                                   sample_weight=sample_weight)

    def predict(self, x, batch_size=32, verbose=0):
        '''Generates output predictions for the input samples,
        processing the samples in a batched way.

        # Arguments
            x: the input data, as a Numpy array.
            batch_size: integer.
            verbose: verbosity mode, 0 or 1.

        # Returns
            A Numpy array of predictions.
        '''
        if self.model is None:
            self.build()
        return self.model.predict(x, batch_size=batch_size, verbose=verbose)

    def predict_on_batch(self, x):
        '''Returns predictions for a single batch of samples.
        '''
        return self.model.predict_on_batch(x)

    def train_on_batch(self, x, y, class_weight=None,
                       sample_weight=None, **kwargs):
        '''Single gradient update over one batch of samples.

        # Arguments
            x: input data, as a Numpy array or list of Numpy arrays
                (if the model has multiple inputs).
            y: labels, as a Numpy array.
            class_weight: dictionary mapping classes to a weight value,
                used for scaling the loss function (during training only).
            sample_weight: sample weights, as a Numpy array.

        # Returns
            Scalar training loss (if the model has no metrics)
            or list of scalars (if the model computes other metrics).
            The attribute `model.metrics_names` will give you
            the display labels for the scalar outputs.
        '''
        if 'accuracy' in kwargs:
            kwargs.pop('accuracy')
            warnings.warn('The "accuracy" argument is deprecated, '
                          'instead you should pass the "accuracy" metric to '
                          'the model at compile time:\n'
                          '`model.compile(optimizer, loss, '
                          'metrics=["accuracy"])`')
        if kwargs:
            raise Exception('Received unknown keyword arguments: ' +
                            str(kwargs))
        return self.model.train_on_batch(x, y,
                                         sample_weight=sample_weight,
                                         class_weight=class_weight)

    def test_on_batch(self, x, y,
                      sample_weight=None, **kwargs):
        '''Evaluates the model over a single batch of samples.

        # Arguments
            x: input data, as a Numpy array or list of Numpy arrays
                (if the model has multiple inputs).
            y: labels, as a Numpy array.
            sample_weight: sample weights, as a Numpy array.

        # Returns
            Scalar test loss (if the model has no metrics)
            or list of scalars (if the model computes other metrics).
            The attribute `model.metrics_names` will give you
            the display labels for the scalar outputs.
        '''
        if 'accuracy' in kwargs:
            kwargs.pop('accuracy')
            warnings.warn('The "accuracy" argument is deprecated, '
                          'instead you should pass the "accuracy" metric to '
                          'the model at compile time:\n'
                          '`model.compile(optimizer, loss, '
                          'metrics=["accuracy"])`')
        if kwargs:
            raise Exception('Received unknown keyword arguments: ' +
                            str(kwargs))
        return self.model.test_on_batch(x, y,
                                        sample_weight=sample_weight)

    def predict_proba(self, x, batch_size=32, verbose=1):
        '''Generates class probability predictions for the input samples
        batch by batch.

        # Arguments
            x: input data, as a Numpy array or list of Numpy arrays
                (if the model has multiple inputs).
            batch_size: integer.
            verbose: verbosity mode, 0 or 1.

        # Returns
            A Numpy array of probability predictions.
        '''
        preds = self.predict(x, batch_size, verbose)
        if preds.min() < 0. or preds.max() > 1.:
            warnings.warn('Network returning invalid probability values. '
                          'The last layer might not normalize predictions '
                          'into probabilities '
                          '(like softmax or sigmoid would).')
        return preds

    def predict_classes(self, x, batch_size=32, verbose=1):
        '''Generate class predictions for the input samples
        batch by batch.

        # Arguments
            x: input data, as a Numpy array or list of Numpy arrays
                (if the model has multiple inputs).
            batch_size: integer.
            verbose: verbosity mode, 0 or 1.

        # Returns
            A numpy array of class predictions.
        '''
        proba = self.predict(x, batch_size=batch_size, verbose=verbose)
        if proba.shape[-1] > 1:
            return proba.argmax(axis=-1)
        else:
            return (proba > 0.5).astype('int32')

    def fit_generator(self, generator, samples_per_epoch, nb_epoch,
                      verbose=1, callbacks=[],
                      validation_data=None, nb_val_samples=None,
                      class_weight=None, max_q_size=10, **kwargs):
        '''Fits the model on data generated batch-by-batch by
        a Python generator.
        The generator is run in parallel to the model, for efficiency.
        For instance, this allows you to do real-time data augmentation
        on images on CPU in parallel to training your model on GPU.

        # Arguments
            generator: a generator.
                The output of the generator must be either
                - a tuple (inputs, targets)
                - a tuple (inputs, targets, sample_weights).
                All arrays should contain the same number of samples.
                The generator is expected to loop over its data
                indefinitely. An epoch finishes when `samples_per_epoch`
                samples have been seen by the model.
            samples_per_epoch: integer, number of samples to process before
                going to the next epoch.
            nb_epoch: integer, total number of iterations on the data.
            verbose: verbosity mode, 0, 1, or 2.
            callbacks: list of callbacks to be called during training.
            validation_data: this can be either
                - a generator for the validation data
                - a tuple (inputs, targets)
                - a tuple (inputs, targets, sample_weights).
            nb_val_samples: only relevant if `validation_data` is a generator.
                number of samples to use from validation generator
                at the end of every epoch.
            class_weight: dictionary mapping class indices to a weight
                for the class.
            max_q_size: maximum size for the generator queue

        # Returns
            A `History` object.

        # Example

        ```python
            def generate_arrays_from_file(path):
                while 1:
                    f = open(path)
                    for line in f:
                        # create numpy arrays of input data
                        # and labels, from each line in the file
                        x, y = process_line(line)
                        yield (x, y)
                    f.close()

            model.fit_generator(generate_arrays_from_file('/my_file.txt'),
                                samples_per_epoch=10000, nb_epoch=10)
        ```
        '''
        if self.model is None:
            raise Exception('The model needs to be compiled before being used.')
        if 'show_accuracy' in kwargs:
            kwargs.pop('show_accuracy')
            warnings.warn('The "show_accuracy" argument is deprecated, '
                          'instead you should pass the "accuracy" metric to '
                          'the model at compile time:\n'
                          '`model.compile(optimizer, loss, '
                          'metrics=["accuracy"])`')
        if 'nb_worker' in kwargs:
            kwargs.pop('nb_worker')
            warnings.warn('The "nb_worker" argument is deprecated, '
                          'please remove it from your code.')
        if 'nb_val_worker' in kwargs:
            kwargs.pop('nb_val_worker')
            warnings.warn('The "nb_val_worker" argument is deprecated, '
                          'please remove it from your code.')
        if kwargs:
            raise Exception('Received unknown keyword arguments: ' +
                            str(kwargs))
        return self.model.fit_generator(generator,
                                        samples_per_epoch,
                                        nb_epoch,
                                        verbose=verbose,
                                        callbacks=callbacks,
                                        validation_data=validation_data,
                                        nb_val_samples=nb_val_samples,
                                        class_weight=class_weight,
                                        max_q_size=max_q_size)

    def evaluate_generator(self, generator, val_samples, max_q_size=10, **kwargs):
        '''Evaluates the model on a data generator. The generator should
        return the same kind of data as accepted by `test_on_batch`.

        Arguments:
            generator:
                generator yielding tuples (inputs, targets)
                or (inputs, targets, sample_weights)
            val_samples:
                total number of samples to generate from `generator`
                before returning.
            max_q_size: maximum size for the generator queue
        '''
        if self.model is None:
            raise Exception('The model needs to be compiled before being used.')
        if 'show_accuracy' in kwargs:
            kwargs.pop('show_accuracy')
            warnings.warn('The "show_accuracy" argument is deprecated, '
                          'instead you should pass the "accuracy" metric to '
                          'the model at compile time:\n'
                          '`model.compile(optimizer, loss, '
                          'metrics=["accuracy"])`')
        if 'verbose' in kwargs:
            kwargs.pop('verbose')
            warnings.warn('The "verbose" argument is deprecated.')
        if kwargs:
            raise Exception('Received unknown keyword arguments: ' +
                            str(kwargs))
        return self.model.evaluate_generator(generator,
                                             val_samples,
                                             max_q_size=max_q_size)

    def predict_generator(self, generator, val_samples, max_q_size=10):
        '''Generates predictions for the input samples from a data generator.
        The generator should return the same kind of data as accepted by
        `predict_on_batch`.

        # Arguments
            generator: generator yielding batches of input samples.
            val_samples: total number of samples to generate from `generator`
                before returning.
            max_q_size: maximum size for the generator queue

        # Returns
            A Numpy array of predictions.
        '''
        if self.model is None:
            raise Exception('The model needs to be compiled before being used.')
        return self.model.predict_generator(generator, val_samples,
                                            max_q_size=max_q_size)

    def get_config(self):
        '''Returns the model configuration
        as a Python dictionary.
        '''
        config = []
        if self.layers[0].__class__.__name__ == 'Merge':
            assert hasattr(self.layers[0], 'layers')
            layers = []
            for layer in self.layers[0].layers:
                layer_config = {'class_name': layer.__class__.__name__,
                                'config': layer.get_config()}
                layers.append(layer_config)
            merge_config = self.layers[0].get_config()
            merge_config['layers'] = layers
            config.append({'class_name': 'Merge', 'config': merge_config})
        else:
            config.append({'class_name': self.layers[0].__class__.__name__,
                           'config': self.layers[0].get_config()})
        for layer in self.layers[1:]:
            config.append({'class_name': layer.__class__.__name__,
                           'config': layer.get_config()})
        return copy.deepcopy(config)

    @classmethod
    def from_config(cls, config):
        '''Supports legacy formats
        '''
        from keras.utils.layer_utils import layer_from_config
        from keras.layers import Merge
        assert type(config) is list

        def normalize_legacy_config(conf):
            if 'class_name' not in conf:
                class_name = conf['name']
                name = conf.get('custom_name')
                conf['name'] = name
                new_config = {
                    'class_name': class_name,
                    'config': conf,
                }
                return new_config
            return conf

        model = cls()

        first_layer = config[0]
        first_layer = normalize_legacy_config(first_layer)
        if first_layer['class_name'] == 'Merge':
            merge_inputs = []
            first_layer_config = first_layer['config']
            for merge_input_config in first_layer_config.pop('layers'):
                merge_input = layer_from_config(merge_input_config)
                merge_inputs.append(merge_input)
            first_layer_config['layers'] = merge_inputs
            merge = Merge.from_config(first_layer_config)
            model.add(merge)
        else:
            layer = layer_from_config(first_layer)
            model.add(layer)

        for conf in config[1:]:
            conf = normalize_legacy_config(conf)
            layer = layer_from_config(conf)
            model.add(layer)
        return model

from __future__ import absolute_import
from . import backend as K


def softmax(x):
    ndim = K.ndim(x)
    if ndim == 2:
        return K.softmax(x)
    elif ndim == 3:
        e = K.exp(x - K.max(x, axis=-1, keepdims=True))
        s = K.sum(e, axis=-1, keepdims=True)
        return e / s
    else:
        raise Exception('Cannot apply softmax to a tensor that is not 2D or 3D. ' +
                        'Here, ndim=' + str(ndim))


def softplus(x):
    return K.softplus(x)


def softsign(x):
    return K.softsign(x)


def relu(x, alpha=0., max_value=None):
    return K.relu(x, alpha=alpha, max_value=max_value)


def tanh(x):
    return K.tanh(x)


def sigmoid(x):
    return K.sigmoid(x)


def hard_sigmoid(x):
    return K.hard_sigmoid(x)


def linear(x):
    '''
    The function returns the variable that is passed in, so all types work.
    '''
    return x


from .utils.generic_utils import get_from_module
def get(identifier):
    return get_from_module(identifier, globals(), 'activation function')

from __future__ import absolute_import
__version__ = '1.0.2'
from . import backend
from . import datasets
from . import engine
from . import layers
from . import preprocessing
from . import utils
from . import wrappers
from . import callbacks
from . import constraints
from . import initializations
from . import metrics
from . import models
from . import objectives
from . import optimizers
from . import regularizers

from __future__ import absolute_import
from . import backend as K


class Regularizer(object):
    def set_param(self, p):
        self.p = p

    def set_layer(self, layer):
        self.layer = layer

    def __call__(self, loss):
        return loss

    def get_config(self):
        return {'name': self.__class__.__name__}


class WeightRegularizer(Regularizer):
    def __init__(self, l1=0., l2=0.):
        self.l1 = K.cast_to_floatx(l1)
        self.l2 = K.cast_to_floatx(l2)
        self.uses_learning_phase = True

    def set_param(self, p):
        self.p = p

    def __call__(self, loss):
        if not hasattr(self, 'p'):
            raise Exception('Need to call `set_param` on '
                            'WeightRegularizer instance '
                            'before calling the instance. '
                            'Check that you are not passing '
                            'a WeightRegularizer instead of an '
                            'ActivityRegularizer '
                            '(i.e. activity_regularizer="l2" instead '
                            'of activity_regularizer="activity_l2".')
        regularized_loss = loss + K.sum(K.abs(self.p)) * self.l1
        regularized_loss += K.sum(K.square(self.p)) * self.l2
        return K.in_train_phase(regularized_loss, loss)

    def get_config(self):
        return {'name': self.__class__.__name__,
                'l1': self.l1,
                'l2': self.l2}


class ActivityRegularizer(Regularizer):
    def __init__(self, l1=0., l2=0.):
        self.l1 = K.cast_to_floatx(l1)
        self.l2 = K.cast_to_floatx(l2)
        self.uses_learning_phase = True

    def set_layer(self, layer):
        self.layer = layer

    def __call__(self, loss):
        if not hasattr(self, 'layer'):
            raise Exception('Need to call `set_layer` on '
                            'ActivityRegularizer instance '
                            'before calling the instance.')
        regularized_loss = loss
        for i in range(len(self.layer.inbound_nodes)):
            output = self.layer.get_output_at(i)
            regularized_loss += self.l1 * K.sum(K.mean(K.abs(output), axis=0))
            regularized_loss += self.l2 * K.sum(K.mean(K.square(output), axis=0))
        return K.in_train_phase(regularized_loss, loss)

    def get_config(self):
        return {'name': self.__class__.__name__,
                'l1': self.l1,
                'l2': self.l2}


def l1(l=0.01):
    return WeightRegularizer(l1=l)


def l2(l=0.01):
    return WeightRegularizer(l2=l)


def l1l2(l1=0.01, l2=0.01):
    return WeightRegularizer(l1=l1, l2=l2)


def activity_l1(l=0.01):
    return ActivityRegularizer(l1=l)


def activity_l2(l=0.01):
    return ActivityRegularizer(l2=l)


def activity_l1l2(l1=0.01, l2=0.01):
    return ActivityRegularizer(l1=l1, l2=l2)


from .utils.generic_utils import get_from_module
def get(identifier, kwargs=None):
    return get_from_module(identifier, globals(), 'regularizer',
                           instantiate=True, kwargs=kwargs)

from __future__ import absolute_import
from . import backend as K
import numpy as np
from .utils.generic_utils import get_from_module
from six.moves import zip


def clip_norm(g, c, n):
    if c > 0:
        g = K.switch(n >= c, g * c / n, g)
    return g


def kl_divergence(p, p_hat):
    return p_hat - p + p * K.log(p / p_hat)


class Optimizer(object):
    '''Abstract optimizer base class.

    Note: this is the parent class of all optimizers, not an actual optimizer
    that can be used for training models.

    All Keras optimizers support the following keyword arguments:

        clipnorm: float >= 0. Gradients will be clipped
            when their L2 norm exceeds this value.
        clipvalue: float >= 0. Gradients will be clipped
            when their absolute value exceeds this value.
    '''
    def __init__(self, **kwargs):
        allowed_kwargs = {'clipnorm', 'clipvalue'}
        for k in kwargs:
            if k not in allowed_kwargs:
                raise Exception('Unexpected keyword argument '
                                'passed to optimizer: ' + str(k))
        self.__dict__.update(kwargs)
        self.updates = []
        self.weights = []

    def get_state(self):
        return [K.get_value(u[0]) for u in self.updates]

    def set_state(self, value_list):
        assert len(self.updates) == len(value_list)
        for u, v in zip(self.updates, value_list):
            K.set_value(u[0], v)

    def get_updates(self, params, constraints, loss):
        raise NotImplementedError

    def get_gradients(self, loss, params):
        grads = K.gradients(loss, params)
        if hasattr(self, 'clipnorm') and self.clipnorm > 0:
            norm = K.sqrt(sum([K.sum(K.square(g)) for g in grads]))
            grads = [clip_norm(g, self.clipnorm, norm) for g in grads]
        if hasattr(self, 'clipvalue') and self.clipvalue > 0:
            grads = [K.clip(g, -self.clipvalue, self.clipvalue) for g in grads]
        return grads

    def set_weights(self, weights):
        '''Sets the weights of the optimizer, from Numpy arrays.

        Should only be called after computing the gradients
        (otherwise the optimizer has no weights).

        # Arguments
            weights: a list of Numpy arrays. The number
                of arrays and their shape must match
                number of the dimensions of the weights
                of the optimizer (i.e. it should match the
                output of `get_weights`).
        '''
        params = self.weights
        if len(params) != len(weights):
            raise Exception('Provided weight array does not match  weights (' +
                            str(len(params)) + ' optimizer params vs. ' +
                            str(len(weights)) + ' provided weights)')
        for p, w in zip(params, weights):
            if K.get_value(p).shape != w.shape:
                raise Exception('Optimizer weight shape ' +
                                str(K.get_value(p).shape) +
                                ' not compatible with '
                                'provided weight shape ' + str(w.shape))
            K.set_value(p, w)

    def get_weights(self):
        '''Returns the current weights of the optimizer,
        as a list of numpy arrays.
        '''
        weights = []
        for p in self.weights:
            weights.append(K.get_value(p))
        return weights

    def get_config(self):
        config = {'name': self.__class__.__name__}
        if hasattr(self, 'clipnorm'):
            config['clipnorm'] = self.clipnorm
        if hasattr(self, 'clipvalue'):
            config['clipvalue'] = self.clipvalue
        return config


class SGD(Optimizer):
    '''Stochastic gradient descent, with support for momentum,
    learning rate decay, and Nesterov momentum.

    # Arguments
        lr: float >= 0. Learning rate.
        momentum: float >= 0. Parameter updates momentum.
        decay: float >= 0. Learning rate decay over each update.
        nesterov: boolean. Whether to apply Nesterov momentum.
    '''
    def __init__(self, lr=0.01, momentum=0., decay=0.,
                 nesterov=False, **kwargs):
        super(SGD, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.iterations = K.variable(0.)
        self.lr = K.variable(lr)
        self.momentum = K.variable(momentum)
        self.decay = K.variable(decay)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        lr = self.lr * (1. / (1. + self.decay * self.iterations))
        self.updates = [(self.iterations, self.iterations + 1.)]

        # momentum
        self.weights = [K.variable(np.zeros(K.get_value(p).shape)) for p in params]
        for p, g, m in zip(params, grads, self.weights):
            v = self.momentum * m - lr * g  # velocity
            self.updates.append((m, v))

            if self.nesterov:
                new_p = p + self.momentum * v - lr * g
            else:
                new_p = p + v

            # apply constraints
            if p in constraints:
                c = constraints[p]
                new_p = c(new_p)
            self.updates.append((p, new_p))
        return self.updates

    def get_config(self):
        config = {'lr': float(K.get_value(self.lr)),
                  'momentum': float(K.get_value(self.momentum)),
                  'decay': float(K.get_value(self.decay)),
                  'nesterov': self.nesterov}
        base_config = super(SGD, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class RMSprop(Optimizer):
    '''RMSProp optimizer.

    It is recommended to leave the parameters of this optimizer
    at their default values
    (except the learning rate, which can be freely tuned).

    This optimizer is usually a good choice for recurrent
    neural networks.

    # Arguments
        lr: float >= 0. Learning rate.
        rho: float >= 0.
        epsilon: float >= 0. Fuzz factor.
    '''
    def __init__(self, lr=0.001, rho=0.9, epsilon=1e-6, **kwargs):
        super(RMSprop, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.lr = K.variable(lr)
        self.rho = K.variable(rho)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        # accumulators
        self.weights = [K.variable(np.zeros(K.get_value(p).shape)) for p in params]
        self.updates = []

        for p, g, a in zip(params, grads, self.weights):
            # update accumulator
            new_a = self.rho * a + (1. - self.rho) * K.square(g)
            self.updates.append((a, new_a))
            new_p = p - self.lr * g / K.sqrt(new_a + self.epsilon)

            # apply constraints
            if p in constraints:
                c = constraints[p]
                new_p = c(new_p)
            self.updates.append((p, new_p))
        return self.updates

    def get_config(self):
        config = {'lr': float(K.get_value(self.lr)),
                  'rho': float(K.get_value(self.rho)),
                  'epsilon': self.epsilon}
        base_config = super(RMSprop, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Adagrad(Optimizer):
    '''Adagrad optimizer.

    It is recommended to leave the parameters of this optimizer
    at their default values.

    # Arguments
        lr: float >= 0. Learning rate.
        epsilon: float >= 0.
    '''
    def __init__(self, lr=0.01, epsilon=1e-6, **kwargs):
        super(Adagrad, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.lr = K.variable(lr)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        # accumulators
        self.weights = [K.variable(np.zeros(K.get_value(p).shape)) for p in params]
        self.updates = []

        for p, g, a in zip(params, grads, self.weights):
            new_a = a + K.square(g)  # update accumulator
            self.updates.append((a, new_a))
            new_p = p - self.lr * g / K.sqrt(new_a + self.epsilon)
            # apply constraints
            if p in constraints:
                c = constraints[p]
                new_p = c(new_p)
            self.updates.append((p, new_p))
        return self.updates

    def get_config(self):
        config = {'lr': float(K.get_value(self.lr)),
                  'epsilon': self.epsilon}
        base_config = super(Adagrad, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Adadelta(Optimizer):
    '''Adadelta optimizer.

    It is recommended to leave the parameters of this optimizer
    at their default values.

    # Arguments
        lr: float >= 0. Learning rate.
            It is recommended to leave it at the default value.
        rho: float >= 0.
        epsilon: float >= 0. Fuzz factor.

    # References
        - [Adadelta - an adaptive learning rate method](http://arxiv.org/abs/1212.5701)
    '''
    def __init__(self, lr=1.0, rho=0.95, epsilon=1e-6, **kwargs):
        super(Adadelta, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.lr = K.variable(lr)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        accumulators = [K.variable(np.zeros(K.get_value(p).shape)) for p in params]
        delta_accumulators = [K.variable(np.zeros(K.get_value(p).shape)) for p in params]
        self.weights = accumulators + delta_accumulators
        self.updates = []

        for p, g, a, d_a in zip(params, grads, accumulators, delta_accumulators):
            # update accumulator
            new_a = self.rho * a + (1. - self.rho) * K.square(g)
            self.updates.append((a, new_a))

            # use the new accumulator and the *old* delta_accumulator
            update = g * K.sqrt(d_a + self.epsilon) / K.sqrt(new_a + self.epsilon)

            new_p = p - self.lr * update
            # apply constraints
            if p in constraints:
                c = constraints[p]
                new_p = c(new_p)
            self.updates.append((p, new_p))

            # update delta_accumulator
            new_d_a = self.rho * d_a + (1 - self.rho) * K.square(update)
            self.updates.append((d_a, new_d_a))
        return self.updates

    def get_config(self):
        config = {'lr': float(K.get_value(self.lr)),
                  'rho': self.rho,
                  'epsilon': self.epsilon}
        base_config = super(Adadelta, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Adam(Optimizer):
    '''Adam optimizer.

    Default parameters follow those provided in the original paper.

    # Arguments
        lr: float >= 0. Learning rate.
        beta_1/beta_2: floats, 0 < beta < 1. Generally close to 1.
        epsilon: float >= 0. Fuzz factor.

    # References
        - [Adam - A Method for Stochastic Optimization](http://arxiv.org/abs/1412.6980v8)
    '''
    def __init__(self, lr=0.001, beta_1=0.9, beta_2=0.999,
                 epsilon=1e-8, **kwargs):
        super(Adam, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.iterations = K.variable(0)
        self.lr = K.variable(lr)
        self.beta_1 = K.variable(beta_1)
        self.beta_2 = K.variable(beta_2)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        self.updates = [(self.iterations, self.iterations + 1)]

        t = self.iterations + 1
        lr_t = self.lr * K.sqrt(1. - K.pow(self.beta_2, t)) / (1. - K.pow(self.beta_1, t))

        ms = [K.variable(np.zeros(K.get_value(p).shape)) for p in params]
        vs = [K.variable(np.zeros(K.get_value(p).shape)) for p in params]
        self.weights = ms + vs

        for p, g, m, v in zip(params, grads, ms, vs):
            m_t = (self.beta_1 * m) + (1. - self.beta_1) * g
            v_t = (self.beta_2 * v) + (1. - self.beta_2) * K.square(g)
            p_t = p - lr_t * m_t / (K.sqrt(v_t) + self.epsilon)

            self.updates.append((m, m_t))
            self.updates.append((v, v_t))

            new_p = p_t
            # apply constraints
            if p in constraints:
                c = constraints[p]
                new_p = c(new_p)
            self.updates.append((p, new_p))
        return self.updates

    def get_config(self):
        config = {'lr': float(K.get_value(self.lr)),
                  'beta_1': float(K.get_value(self.beta_1)),
                  'beta_2': float(K.get_value(self.beta_2)),
                  'epsilon': self.epsilon}
        base_config = super(Adam, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Adamax(Optimizer):
    '''Adamax optimizer from Adam paper's Section 7. It is a variant
     of Adam based on the infinity norm.

    Default parameters follow those provided in the paper.

    # Arguments
        lr: float >= 0. Learning rate.
        beta_1/beta_2: floats, 0 < beta < 1. Generally close to 1.
        epsilon: float >= 0. Fuzz factor.

    # References
        - [Adam - A Method for Stochastic Optimization](http://arxiv.org/abs/1412.6980v8)
    '''
    def __init__(self, lr=0.002, beta_1=0.9, beta_2=0.999,
                 epsilon=1e-8, **kwargs):
        super(Adamax, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.iterations = K.variable(0.)
        self.lr = K.variable(lr)
        self.beta_1 = K.variable(beta_1)
        self.beta_2 = K.variable(beta_2)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        self.updates = [(self.iterations, self.iterations + 1)]

        t = self.iterations + 1
        lr_t = self.lr / (1. - K.pow(self.beta_1, t))

        # zero init of 1st moment
        ms = [K.variable(np.zeros(K.get_value(p).shape)) for p in params]
        # zero init of exponentially weighted infinity norm
        us = [K.variable(np.zeros(K.get_value(p).shape)) for p in params]
        self.weights = ms + us

        for p, g, m, u in zip(params, grads, ms, us):

            m_t = (self.beta_1 * m) + (1. - self.beta_1) * g
            u_t = K.maximum(self.beta_2 * u, K.abs(g))
            p_t = p - lr_t * m_t / (u_t + self.epsilon)

            self.updates.append((m, m_t))
            self.updates.append((u, u_t))

            new_p = p_t
            # apply constraints
            if p in constraints:
                c = constraints[p]
                new_p = c(new_p)
            self.updates.append((p, new_p))
        return self.updates

    def get_config(self):
        config = {'lr': float(K.get_value(self.lr)),
                  'beta_1': float(K.get_value(self.beta_1)),
                  'beta_2': float(K.get_value(self.beta_2)),
                  'epsilon': self.epsilon}
        base_config = super(Adamax, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


# aliases
sgd = SGD
rmsprop = RMSprop
adagrad = Adagrad
adadelta = Adadelta
adam = Adam
adamax = Adamax


def get(identifier, kwargs=None):
    return get_from_module(identifier, globals(), 'optimizer',
                           instantiate=True, kwargs=kwargs)

from __future__ import absolute_import
import numpy as np
from . import backend as K


def mean_squared_error(y_true, y_pred):
    return K.mean(K.square(y_pred - y_true), axis=-1)


def mean_absolute_error(y_true, y_pred):
    return K.mean(K.abs(y_pred - y_true), axis=-1)


def mean_absolute_percentage_error(y_true, y_pred):
    diff = K.abs((y_true - y_pred) / K.clip(K.abs(y_true), K.epsilon(), np.inf))
    return 100. * K.mean(diff, axis=-1)


def mean_squared_logarithmic_error(y_true, y_pred):
    first_log = K.log(K.clip(y_pred, K.epsilon(), np.inf) + 1.)
    second_log = K.log(K.clip(y_true, K.epsilon(), np.inf) + 1.)
    return K.mean(K.square(first_log - second_log), axis=-1)


def squared_hinge(y_true, y_pred):
    return K.mean(K.square(K.maximum(1. - y_true * y_pred, 0.)), axis=-1)


def hinge(y_true, y_pred):
    return K.mean(K.maximum(1. - y_true * y_pred, 0.), axis=-1)


def categorical_crossentropy(y_true, y_pred):
    '''Expects a binary class matrix instead of a vector of scalar classes.
    '''
    return K.categorical_crossentropy(y_pred, y_true)


def sparse_categorical_crossentropy(y_true, y_pred):
    '''expects an array of integer classes.
    Note: labels shape must have the same number of dimensions as output shape.
    If you get a shape error, add a length-1 dimension to labels.
    '''
    return K.sparse_categorical_crossentropy(y_pred, y_true)


def binary_crossentropy(y_true, y_pred):
    return K.mean(K.binary_crossentropy(y_pred, y_true), axis=-1)


def poisson(y_true, y_pred):
    return K.mean(y_pred - y_true * K.log(y_pred + K.epsilon()), axis=-1)


def cosine_proximity(y_true, y_pred):
    y_true = K.l2_normalize(y_true, axis=-1)
    y_pred = K.l2_normalize(y_pred, axis=-1)
    return -K.mean(y_true * y_pred, axis=-1)


# aliases
mse = MSE = mean_squared_error
mae = MAE = mean_absolute_error
mape = MAPE = mean_absolute_percentage_error
msle = MSLE = mean_squared_logarithmic_error
cosine = cosine_proximity

from .utils.generic_utils import get_from_module
def get(identifier):
    return get_from_module(identifier, globals(), 'objective')

from __future__ import absolute_import
from __future__ import print_function

import numpy as np
import time
import json
import warnings

from collections import deque
from .utils.generic_utils import Progbar
from keras import backend as K


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
        if self._delta_t_batch > 0. and delta_t_median > 0.95 * \
           self._delta_t_batch and delta_t_median > 0.1:
            warnings.warn('Method on_batch_begin() is slow compared '
                          'to the batch update (%f). Check your callbacks.'
                          % delta_t_median)
        self._t_enter_batch = time.time()

    def on_batch_end(self, batch, logs={}):
        if not hasattr(self, '_t_enter_batch'):
            self._t_enter_batch = time.time()
        self._delta_t_batch = time.time() - self._t_enter_batch
        t_before_callbacks = time.time()
        for callback in self.callbacks:
            callback.on_batch_end(batch, logs)
        self._delta_ts_batch_end.append(time.time() - t_before_callbacks)
        delta_t_median = np.median(self._delta_ts_batch_end)
        if self._delta_t_batch > 0. and (delta_t_median > 0.95 * self._delta_t_batch and delta_t_median > 0.1):
            warnings.warn('Method on_batch_end() is slow compared '
                          'to the batch update (%f). Check your callbacks.'
                          % delta_t_median)

    def on_train_begin(self, logs={}):
        for callback in self.callbacks:
            callback.on_train_begin(logs)

    def on_train_end(self, logs={}):
        for callback in self.callbacks:
            callback.on_train_end(logs)


class Callback(object):
    '''Abstract base class used to build new callbacks.

    # Properties
        params: dict. Training parameters
            (eg. verbosity, batch size, number of epochs...).
        model: instance of `keras.models.Model`.
            Reference of the model being trained.

    The `logs` dictionary that callback methods
    take as argument will contain keys for quantities relevant to
    the current batch or epoch.

    Currently, the `.fit()` method of the `Sequential` model class
    will include the following quantities in the `logs` that
    it passes to its callbacks:

        on_epoch_end: logs include `acc` and `loss`, and
            optionally include `val_loss`
            (if validation is enabled in `fit`), and `val_acc`
            (if validation and accuracy monitoring are enabled).
        on_batch_begin: logs include `size`,
            the number of samples in the current batch.
        on_batch_end: logs include `loss`, and optionally `acc`
            (if accuracy monitoring is enabled).
    '''
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
    '''Callback that accumulates epoch averages of
    the metrics being monitored.

    This callback is automatically applied to
    every Keras model.
    '''
    def on_epoch_begin(self, epoch, logs={}):
        self.seen = 0
        self.totals = {}

    def on_batch_end(self, batch, logs={}):
        batch_size = logs.get('size', 0)
        self.seen += batch_size

        for k, v in logs.items():
            if k in self.totals:
                self.totals[k] += v * batch_size
            else:
                self.totals[k] = v * batch_size

    def on_epoch_end(self, epoch, logs={}):
        for k in self.params['metrics']:
            if k in self.totals:
                # make value available to next callbacks
                logs[k] = self.totals[k] / self.seen


class ProgbarLogger(Callback):
    '''Callback that prints metrics to stdout.
    '''
    def on_train_begin(self, logs={}):
        self.verbose = self.params['verbose']
        self.nb_epoch = self.params['nb_epoch']

    def on_epoch_begin(self, epoch, logs={}):
        if self.verbose:
            print('Epoch %d/%d' % (epoch + 1, self.nb_epoch))
            self.progbar = Progbar(target=self.params['nb_sample'],
                                   verbose=self.verbose)
        self.seen = 0

    def on_batch_begin(self, batch, logs={}):
        if self.seen < self.params['nb_sample']:
            self.log_values = []

    def on_batch_end(self, batch, logs={}):
        batch_size = logs.get('size', 0)
        self.seen += batch_size

        for k in self.params['metrics']:
            if k in logs:
                self.log_values.append((k, logs[k]))

        # skip progbar update for the last batch;
        # will be handled by on_epoch_end
        if self.verbose and self.seen < self.params['nb_sample']:
            self.progbar.update(self.seen, self.log_values)

    def on_epoch_end(self, epoch, logs={}):
        for k in self.params['metrics']:
            if k in logs:
                self.log_values.append((k, logs[k]))
        if self.verbose:
            self.progbar.update(self.seen, self.log_values)


class History(Callback):
    '''Callback that records events
    into a `History` object.

    This callback is automatically applied to
    every Keras model. The `History` object
    gets returned by the `fit` method of models.
    '''
    def on_train_begin(self, logs={}):
        self.epoch = []
        self.history = {}

    def on_epoch_end(self, epoch, logs={}):
        self.epoch.append(epoch)
        for k, v in logs.items():
            if k not in self.history:
                self.history[k] = []
            self.history[k].append(v)


class ModelCheckpoint(Callback):
    '''Save the model after every epoch.

    `filepath` can contain named formatting options,
    which will be filled the value of `epoch` and
    keys in `logs` (passed in `on_epoch_end`).

    For example: if `filepath` is `weights.{epoch:02d}-{val_loss:.2f}.hdf5`,
    then multiple files will be save with the epoch number and
    the validation loss.

    # Arguments
        filepath: string, path to save the model file.
        monitor: quantity to monitor.
        verbose: verbosity mode, 0 or 1.
        save_best_only: if `save_best_only=True`,
            the latest best model according to
            the validation loss will not be overwritten.
        mode: one of {auto, min, max}.
            If `save_best_only=True`, the decision
            to overwrite the current save file is made
            based on either the maximization or the
            minization of the monitored. For `val_acc`,
            this should be `max`, for `val_loss` this should
            be `min`, etc. In `auto` mode, the direction is
            automatically inferred from the name of the monitored quantity.

    '''
    def __init__(self, filepath, monitor='val_loss', verbose=0,
                 save_best_only=False, mode='auto'):

        super(Callback, self).__init__()
        self.monitor = monitor
        self.verbose = verbose
        self.filepath = filepath
        self.save_best_only = save_best_only

        if mode not in ['auto', 'min', 'max']:
            warnings.warn('ModelCheckpoint mode %s is unknown, '
                          'fallback to auto mode.' % (mode),
                          RuntimeWarning)
            mode = 'auto'

        if mode == 'min':
            self.monitor_op = np.less
            self.best = np.Inf
        elif mode == 'max':
            self.monitor_op = np.greater
            self.best = -np.Inf
        else:
            if 'acc' in self.monitor:
                self.monitor_op = np.greater
                self.best = -np.Inf
            else:
                self.monitor_op = np.less
                self.best = np.Inf

    def on_epoch_end(self, epoch, logs={}):
        filepath = self.filepath.format(epoch=epoch, **logs)
        if self.save_best_only:
            current = logs.get(self.monitor)
            if current is None:
                warnings.warn('Can save best model only with %s available, '
                              'skipping.' % (self.monitor), RuntimeWarning)
            else:
                if self.monitor_op(current, self.best):
                    if self.verbose > 0:
                        print('Epoch %05d: %s improved from %0.5f to %0.5f,'
                              ' saving model to %s'
                              % (epoch, self.monitor, self.best,
                                 current, filepath))
                    self.best = current
                    self.model.save_weights(filepath, overwrite=True)
                else:
                    if self.verbose > 0:
                        print('Epoch %05d: %s did not improve' %
                              (epoch, self.monitor))
        else:
            if self.verbose > 0:
                print('Epoch %05d: saving model to %s' % (epoch, filepath))
            self.model.save_weights(filepath, overwrite=True)


class EarlyStopping(Callback):
    '''Stop training when a monitored quantity has stopped improving.

    # Arguments
        monitor: quantity to be monitored.
        patience: number of epochs with no improvement
            after which training will be stopped.
        verbose: verbosity mode.
        mode: one of {auto, min, max}. In 'min' mode,
            training will stop when the quantity
            monitored has stopped decreasing; in 'max'
            mode it will stop when the quantity
            monitored has stopped increasing.
    '''
    def __init__(self, monitor='val_loss', patience=0, verbose=0, mode='auto'):
        super(Callback, self).__init__()

        self.monitor = monitor
        self.patience = patience
        self.verbose = verbose
        self.wait = 0

        if mode not in ['auto', 'min', 'max']:
            warnings.warn('EarlyStopping mode %s is unknown, '
                          'fallback to auto mode.' % (self.mode), RuntimeWarning)
            mode = 'auto'

        if mode == 'min':
            self.monitor_op = np.less
            self.best = np.Inf
        elif mode == 'max':
            self.monitor_op = np.greater
            self.best = -np.Inf
        else:
            if 'acc' in self.monitor:
                self.monitor_op = np.greater
                self.best = -np.Inf
            else:
                self.monitor_op = np.less
                self.best = np.Inf

    def on_epoch_end(self, epoch, logs={}):
        current = logs.get(self.monitor)
        if current is None:
            warnings.warn('Early stopping requires %s available!' %
                          (self.monitor), RuntimeWarning)

        if self.monitor_op(current, self.best):
            self.best = current
            self.wait = 0
        else:
            if self.wait >= self.patience:
                if self.verbose > 0:
                    print('Epoch %05d: early stopping' % (epoch))
                self.model.stop_training = True
            self.wait += 1


class RemoteMonitor(Callback):
    '''Callback used to stream events to a server.

    Requires the `requests` library.

    # Arguments
        root: root url to which the events will be sent (at the end
            of every epoch). Events are sent to
            `root + '/publish/epoch/end/'`. Calls are HTTP POST,
            with a `data` argument which is a JSON-encoded dictionary
            of event data.
    '''
    def __init__(self, root='http://localhost:9000'):
        self.root = root

    def on_epoch_end(self, epoch, logs={}):
        import requests
        send = {}
        send['epoch'] = epoch
        for k, v in logs.items():
            send[k] = v

        try:
            requests.post(self.root + '/publish/epoch/end/',
                          {'data': json.dumps(send)})
        except:
            print('Warning: could not reach RemoteMonitor '
                  'root server at ' + str(self.root))


class LearningRateScheduler(Callback):
    '''Learning rate scheduler.

    # Arguments
        schedule: a function that takes an epoch index as input
            (integer, indexed from 0) and returns a new
            learning rate as output (float).
    '''
    def __init__(self, schedule):
        super(LearningRateScheduler, self).__init__()
        self.schedule = schedule

    def on_epoch_begin(self, epoch, logs={}):
        assert hasattr(self.model.optimizer, 'lr'), \
            'Optimizer must have a "lr" attribute.'
        lr = self.schedule(epoch)
        assert type(lr) == float, 'The output of the "schedule" function should be float.'
        K.set_value(self.model.optimizer.lr, lr)


class TensorBoard(Callback):
    ''' Tensorboard basic visualizations.

    This callback writes a log for TensorBoard, which allows
    you to visualize dynamic graphs of your training and test
    metrics, as well as activation histograms for the different
    layers in your model.

    TensorBoard is a visualization tool provided with TensorFlow.

    If you have installed TensorFlow with pip, you should be able
    to launch TensorBoard from the command line:
    ```
    tensorboard --logdir=/full_path_to_your_logs
    ```
    You can find more information about TensorBoard
    [here](https://www.tensorflow.org/versions/master/how_tos/summaries_and_tensorboard/index.html).

    # Arguments
        log_dir: the path of the directory where to save the log
            files to be parsed by tensorboard
        histogram_freq: frequency (in epochs) at which to compute activation
            histograms for the layers of the model. If set to 0,
            histograms won't be computed.
        write_graph: whether to visualize the graph in tensorboard. The log file can
            become quite large when write_graph is set to True.
    '''

    def __init__(self, log_dir='./logs', histogram_freq=0, write_graph=True):
        super(Callback, self).__init__()
        if K._BACKEND != 'tensorflow':
            raise Exception('TensorBoard callback only works '
                            'with the TensorFlow backend.')
        self.log_dir = log_dir
        self.histogram_freq = histogram_freq
        self.merged = None
        self.write_graph = write_graph

    def _set_model(self, model):
        import tensorflow as tf
        import keras.backend.tensorflow_backend as KTF

        self.model = model
        self.sess = KTF.get_session()
        if self.histogram_freq and self.merged is None:
            layers = self.model.layers
            for layer in layers:
                if hasattr(layer, 'W'):
                    tf.histogram_summary('{}_W'.format(layer), layer.W)
                if hasattr(layer, 'b'):
                    tf.histogram_summary('{}_b'.format(layer), layer.b)
                if hasattr(layer, 'output'):
                    tf.histogram_summary('{}_out'.format(layer),
                                         layer.output)
        self.merged = tf.merge_all_summaries()
        if self.write_graph:
            tf_version = tuple(int(i) for i in tf.__version__.split('.'))
            if tf_version >= (0, 8, 0):
                self.writer = tf.train.SummaryWriter(self.log_dir,
                                                     self.sess.graph)
            else:
                self.writer = tf.train.SummaryWriter(self.log_dir,
                                                     self.sess.graph_def)
        else:
            self.writer = tf.train.SummaryWriter(self.log_dir)

    def on_epoch_end(self, epoch, logs={}):
        import tensorflow as tf

        if self.model.validation_data and self.histogram_freq:
            if epoch % self.histogram_freq == 0:
                # TODO: implement batched calls to sess.run
                # (current call will likely go OOM on GPU)
                if self.model.uses_learning_phase:
                    cut_v_data = len(self.model.inputs)
                    val_data = self.model.validation_data[:cut_v_data] + [0]
                    tensors = self.model.inputs + [K.learning_phase()]
                else:
                    val_data = self.model.validation_data
                    tensors = self.model.inputs
                feed_dict = dict(zip(tensors, val_data))
                result = self.sess.run([self.merged], feed_dict=feed_dict)
                summary_str = result[0]
                self.writer.add_summary(summary_str, epoch)

        for name, value in logs.items():
            if name in ['batch', 'size']:
                continue
            summary = tf.Summary()
            summary_value = summary.value.add()
            summary_value.simple_value = value
            summary_value.tag = name
            self.writer.add_summary(summary, epoch)
        self.writer.flush()

from __future__ import absolute_import
from . import backend as K


class Constraint(object):
    def __call__(self, p):
        return p

    def get_config(self):
        return {'name': self.__class__.__name__}


class MaxNorm(Constraint):
    '''Constrain the weights incident to each hidden unit to have a norm less than or equal to a desired value.

    # Arguments
        m: the maximum norm for the incoming weights.
        axis: integer, axis along which to calculate weight norms. For instance,
            in a `Dense` layer the weight matrix has shape (input_dim, output_dim),
            set `axis` to `0` to constrain each weight vector of length (input_dim).
            In a `MaxoutDense` layer the weight tensor has shape (nb_feature, input_dim, output_dim),
            set `axis` to `1` to constrain each weight vector of length (input_dim),
            i.e. constrain the filters incident to the `max` operation.
            In a `Convolution2D` layer with the Theano backend, the weight tensor
            has shape (nb_filter, stack_size, nb_row, nb_col), set `axis` to `[1,2,3]`
            to constrain the weights of each filter tensor of size (stack_size, nb_row, nb_col).
            In a `Convolution2D` layer with the TensorFlow backend, the weight tensor
            has shape (nb_row, nb_col, stack_size, nb_filter), set `axis` to `[0,1,2]`
            to constrain the weights of each filter tensor of size (nb_row, nb_col, stack_size).

    # References
        - [Dropout: A Simple Way to Prevent Neural Networks from Overfitting Srivastava, Hinton, et al. 2014](http://www.cs.toronto.edu/~rsalakhu/papers/srivastava14a.pdf)
    '''
    def __init__(self, m=2, axis=0):
        self.m = m
        self.axis = axis

    def __call__(self, p):
        norms = K.sqrt(K.sum(K.square(p), axis=self.axis, keepdims=True))
        desired = K.clip(norms, 0, self.m)
        p = p * (desired / (K.epsilon() + norms))
        return p

    def get_config(self):
        return {'name': self.__class__.__name__,
                'm': self.m,
                'axis': self.axis}


class NonNeg(Constraint):
    '''Constrain the weights to be non-negative.
    '''
    def __call__(self, p):
        p *= K.cast(p >= 0., K.floatx())
        return p


class UnitNorm(Constraint):
    '''Constrain the weights incident to each hidden unit to have unit norm.

    # Arguments
        axis: integer, axis along which to calculate weight norms. For instance,
            in a `Dense` layer the weight matrix has shape (input_dim, output_dim),
            set `axis` to `0` to constrain each weight vector of length (input_dim).
            In a `MaxoutDense` layer the weight tensor has shape (nb_feature, input_dim, output_dim),
            set `axis` to `1` to constrain each weight vector of length (input_dim),
            i.e. constrain the filters incident to the `max` operation.
            In a `Convolution2D` layer with the Theano backend, the weight tensor
            has shape (nb_filter, stack_size, nb_row, nb_col), set `axis` to `[1,2,3]`
            to constrain the weights of each filter tensor of size (stack_size, nb_row, nb_col).
            In a `Convolution2D` layer with the TensorFlow backend, the weight tensor
            has shape (nb_row, nb_col, stack_size, nb_filter), set `axis` to `[0,1,2]`
            to constrain the weights of each filter tensor of size (nb_row, nb_col, stack_size).
    '''
    def __init__(self, axis=0):
        self.axis = axis

    def __call__(self, p):
        return p / (K.epsilon() + K.sqrt(K.sum(K.square(p), axis=self.axis, keepdims=True)))

    def get_config(self):
        return {'name': self.__class__.__name__,
                'axis': self.axis}


maxnorm = MaxNorm
nonneg = NonNeg
unitnorm = UnitNorm

from .utils.generic_utils import get_from_module
def get(identifier, kwargs=None):
    return get_from_module(identifier, globals(), 'constraint',
                           instantiate=True, kwargs=kwargs)

from __future__ import absolute_import
import numpy as np
from . import backend as K


def get_fans(shape, dim_ordering='th'):
    if len(shape) == 2:
        fan_in = shape[0]
        fan_out = shape[1]
    elif len(shape) == 4 or len(shape) == 5:
        # assuming convolution kernels (2D or 3D).
        # TH kernel shape: (depth, input_depth, ...)
        # TF kernel shape: (..., input_depth, depth)
        if dim_ordering == 'th':
            fan_in = np.prod(shape[1:])
            fan_out = shape[0]
        elif dim_ordering == 'tf':
            fan_in = np.prod(shape[:-1])
            fan_out = shape[-1]
        else:
            raise Exception('Invalid dim_ordering: ' + dim_ordering)
    else:
        # no specific assumptions
        fan_in = np.sqrt(np.prod(shape))
        fan_out = np.sqrt(np.prod(shape))
    return fan_in, fan_out


def uniform(shape, scale=0.05, name=None):
    return K.variable(np.random.uniform(low=-scale, high=scale, size=shape),
                      name=name)


def normal(shape, scale=0.05, name=None):
    return K.variable(np.random.normal(loc=0.0, scale=scale, size=shape),
                      name=name)


def lecun_uniform(shape, name=None, dim_ordering='th'):
    ''' Reference: LeCun 98, Efficient Backprop
        http://yann.lecun.com/exdb/publis/pdf/lecun-98b.pdf
    '''
    fan_in, fan_out = get_fans(shape, dim_ordering=dim_ordering)
    scale = np.sqrt(3. / fan_in)
    return uniform(shape, scale, name=name)


def glorot_normal(shape, name=None, dim_ordering='th'):
    ''' Reference: Glorot & Bengio, AISTATS 2010
    '''
    fan_in, fan_out = get_fans(shape, dim_ordering=dim_ordering)
    s = np.sqrt(2. / (fan_in + fan_out))
    return normal(shape, s, name=name)


def glorot_uniform(shape, name=None, dim_ordering='th'):
    fan_in, fan_out = get_fans(shape, dim_ordering=dim_ordering)
    s = np.sqrt(6. / (fan_in + fan_out))
    return uniform(shape, s, name=name)


def he_normal(shape, name=None, dim_ordering='th'):
    ''' Reference:  He et al., http://arxiv.org/abs/1502.01852
    '''
    fan_in, fan_out = get_fans(shape, dim_ordering=dim_ordering)
    s = np.sqrt(2. / fan_in)
    return normal(shape, s, name=name)


def he_uniform(shape, name=None, dim_ordering='th'):
    fan_in, fan_out = get_fans(shape, dim_ordering=dim_ordering)
    s = np.sqrt(6. / fan_in)
    return uniform(shape, s, name=name)


def orthogonal(shape, scale=1.1, name=None):
    ''' From Lasagne. Reference: Saxe et al., http://arxiv.org/abs/1312.6120
    '''
    flat_shape = (shape[0], np.prod(shape[1:]))
    a = np.random.normal(0.0, 1.0, flat_shape)
    u, _, v = np.linalg.svd(a, full_matrices=False)
    # pick the one with the correct shape
    q = u if u.shape == flat_shape else v
    q = q.reshape(shape)
    return K.variable(scale * q[:shape[0], :shape[1]], name=name)


def identity(shape, scale=1, name=None):
    if len(shape) != 2 or shape[0] != shape[1]:
        raise Exception('Identity matrix initialization can only be used '
                        'for 2D square matrices.')
    else:
        return K.variable(scale * np.identity(shape[0]), name=name)


def zero(shape, name=None):
    return K.zeros(shape, name=name)


def one(shape, name=None):
    return K.ones(shape, name=name)


from .utils.generic_utils import get_from_module
def get(identifier, **kwargs):
    return get_from_module(identifier, globals(),
                           'initialization', kwargs=kwargs)


from __future__ import absolute_import
import copy
import inspect
import types
import numpy as np

from ..utils.np_utils import to_categorical
from ..models import Sequential


class BaseWrapper(object):
    '''Base class for the Keras scikit-learn wrapper.

    Warning: This class should not be used directly.
    Use descendant classes instead.

    # Arguments
        build_fn: callable function or class instance
        sk_params: model parameters & fitting parameters

    The build_fn should construct, compile and return a Keras model, which
    will then be used to fit/predict. One of the following
    three values could be passed to build_fn:
    1. A function
    2. An instance of a class that implements the __call__ method
    3. None. This means you implement a class that inherits from either
    `KerasClassifier` or `KerasRegressor`. The __call__ method of the
    present class will then be treated as the default build_fn.

    `sk_params` takes both model parameters and fitting parameters. Legal model
    parameters are the arguments of `build_fn`. Note that like all other
    estimators in scikit-learn, 'build_fn' should provide defalult values for
    its arguments, so that you could create the estimator without passing any
    values to `sk_params`.

    `sk_params` could also accept parameters for calling `fit`, `predict`,
    `predict_proba`, and `score` methods (e.g., `nb_epoch`, `batch_size`).
    fitting (predicting) parameters are selected in the following order:

    1. Values passed to the dictionary arguments of
    `fit`, `predict`, `predict_proba`, and `score` methods
    2. Values passed to `sk_params`
    3. The default values of the `keras.models.Sequential`
    `fit`, `predict`, `predict_proba` and `score` methods

    When using scikit-learn's `grid_search` API, legal tunable parameters are
    those you could pass to `sk_params`, including fitting parameters.
    In other words, you could use `grid_search` to search for the best
    `batch_size` or `nb_epoch` as well as the model parameters.
    '''

    def __init__(self, build_fn=None, **sk_params):
        self.build_fn = build_fn
        self.sk_params = sk_params
        self.check_params(sk_params)

    def check_params(self, params):
        '''Check for user typos in "params" keys to avoid
        unwanted usage of default values

        # Arguments
            params: dictionary
                The parameters to be checked
        '''
        legal_params_fns = [Sequential.fit, Sequential.predict,
                            Sequential.predict_classes, Sequential.evaluate]
        if self.build_fn is None:
            legal_params_fns.append(self.__call__)
        elif not isinstance(self.build_fn, types.FunctionType):
            legal_params_fns.append(self.build_fn.__call__)
        else:
            legal_params_fns.append(self.build_fn)

        legal_params = []
        for fn in legal_params_fns:
            legal_params += inspect.getargspec(fn)[0]
        legal_params = set(legal_params)

        for params_name in params:
            if params_name not in legal_params:
                assert False, '{} is not a legal parameter'.format(params_name)

    def get_params(self, deep=True):
        '''Get parameters for this estimator.

        # Arguments
            deep: boolean, optional
                If True, will return the parameters for this estimator and
                contained sub-objects that are estimators.

        # Returns
            params : dict
                Dictionary of parameter names mapped to their values.
        '''
        res = copy.deepcopy(self.sk_params)
        res.update({'build_fn': self.build_fn})
        return res

    def set_params(self, **params):
        '''Set the parameters of this estimator.

        # Arguments
        params: dict
            Dictionary of parameter names mapped to their values.

        # Returns
            self
        '''
        self.check_params(params)
        self.sk_params.update(params)
        return self

    def fit(self, X, y, **kwargs):
        '''Construct a new model with build_fn and fit the model according
        to the given training data.

        # Arguments
            X : array-like, shape `(n_samples, n_features)`
                Training samples where n_samples in the number of samples
                and n_features is the number of features.
            y : array-like, shape `(n_samples,)` or `(n_samples, n_outputs)`
                True labels for X.
            kwargs: dictionary arguments
                Legal arguments are the arguments of `Sequential.fit`

        # Returns
            history : object
                details about the training history at each epoch.
        '''

        if self.build_fn is None:
            self.model = self.__call__(**self.filter_sk_params(self.__call__))
        elif not isinstance(self.build_fn, types.FunctionType):
            self.model = self.build_fn(
                **self.filter_sk_params(self.build_fn.__call__))
        else:
            self.model = self.build_fn(**self.filter_sk_params(self.build_fn))

        loss_name = self.model.loss
        if hasattr(loss_name, '__name__'):
            loss_name = loss_name.__name__
        if loss_name == 'categorical_crossentropy' and len(y.shape) != 2:
            y = to_categorical(y)

        fit_args = copy.deepcopy(self.filter_sk_params(Sequential.fit))
        fit_args.update(kwargs)

        history = self.model.fit(X, y, **fit_args)

        return history

    def filter_sk_params(self, fn, override={}):
        '''Filter sk_params and return those in fn's arguments

        # Arguments
            fn : arbitrary function
            override: dictionary, values to overrid sk_params

        # Returns
            res : dictionary dictionary containing variabls
                in both sk_params and fn's arguments.
        '''
        res = {}
        fn_args = inspect.getargspec(fn)[0]
        for name, value in self.sk_params.items():
            if name in fn_args:
                res.update({name: value})
        res.update(override)
        return res


class KerasClassifier(BaseWrapper):
    '''Implementation of the scikit-learn classifier API for Keras.
    '''

    def predict(self, X, **kwargs):
        '''Returns the class predictions for the given test data.

        # Arguments
            X: array-like, shape `(n_samples, n_features)`
                Test samples where n_samples in the number of samples
                and n_features is the number of features.
            kwargs: dictionary arguments
                Legal arguments are the arguments of `Sequential.predict_classes`.

        # Returns
            preds: array-like, shape `(n_samples,)`
                Class predictions.
        '''
        kwargs = self.filter_sk_params(Sequential.predict_classes, kwargs)
        return self.model.predict_classes(X, **kwargs)

    def predict_proba(self, X, **kwargs):
        '''Returns class probability estimates for the given test data.

        # Arguments
            X: array-like, shape `(n_samples, n_features)`
                Test samples where n_samples in the number of samples
                and n_features is the number of features.
            kwargs: dictionary arguments
                Legal arguments are the arguments of `Sequential.predict_classes`.

        # Returns
            proba: array-like, shape `(n_samples, n_outputs)`
                Class probability estimates.
        '''
        kwargs = self.filter_sk_params(Sequential.predict_proba, kwargs)
        return self.model.predict_proba(X, **kwargs)

    def score(self, X, y, **kwargs):
        '''Returns the mean accuracy on the given test data and labels.

        # Arguments
            X: array-like, shape `(n_samples, n_features)`
                Test samples where n_samples in the number of samples
                and n_features is the number of features.
            y: array-like, shape `(n_samples,)` or `(n_samples, n_outputs)`
                True labels for X.
            kwargs: dictionary arguments
                Legal arguments are the arguments of `Sequential.evaluate`.

        # Returns
            score: float
                Mean accuracy of predictions on X wrt. y.
        '''
        kwargs = self.filter_sk_params(Sequential.evaluate, kwargs)
        outputs = self.model.evaluate(X, y, **kwargs)
        if type(outputs) is not list:
            outputs = [outputs]
        for name, output in zip(self.model.metrics_names, outputs):
            if name == 'acc':
                return output
        raise Exception('The model is not configured to compute accuracy. '
                        'You should pass `metrics=["accuracy"]` to '
                        'the `model.compile()` method.')


class KerasRegressor(BaseWrapper):
    '''Implementation of the scikit-learn regressor API for Keras.
    '''

    def predict(self, X, **kwargs):
        '''Returns predictions for the given test data.

        # Arguments
            X: array-like, shape `(n_samples, n_features)`
                Test samples where n_samples in the number of samples
                and n_features is the number of features.
            kwargs: dictionary arguments
                Legal arguments are the arguments of `Sequential.predict`.
        # Returns
            preds: array-like, shape `(n_samples,)`
                Predictions.
        '''
        kwargs = self.filter_sk_params(Sequential.predict, kwargs)
        return self.model.predict(X, **kwargs)

    def score(self, X, y, **kwargs):
        '''Returns the mean loss on the given test data and labels.

        # Arguments
            X: array-like, shape `(n_samples, n_features)`
                Test samples where n_samples in the number of samples
                and n_features is the number of features.
            y: array-like, shape `(n_samples,)`
                True labels for X.
            kwargs: dictionary arguments
                Legal arguments are the arguments of `Sequential.evaluate`.

        # Returns
            score: float
                Mean accuracy of predictions on X wrt. y.
        '''
        kwargs = self.filter_sk_params(Sequential.evaluate, kwargs)
        loss = self.model.evaluate(X, y, **kwargs)
        if type(loss) is list:
            return loss[0]
        return loss

# -*- coding: utf-8 -*-
from __future__ import absolute_import

from .. import backend as K
from .. import activations, initializations, regularizers, constraints
from ..engine import Layer, InputSpec


def conv_output_length(input_length, filter_size, border_mode, stride):
    if input_length is None:
        return None
    assert border_mode in {'same', 'valid'}
    if border_mode == 'same':
        output_length = input_length
    elif border_mode == 'valid':
        output_length = input_length - filter_size + 1
    return (output_length + stride - 1) // stride


class Convolution1D(Layer):
    '''Convolution operator for filtering neighborhoods of one-dimensional inputs.
    When using this layer as the first layer in a model,
    either provide the keyword argument `input_dim`
    (int, e.g. 128 for sequences of 128-dimensional vectors),
    or `input_shape` (tuple of integers, e.g. (10, 128) for sequences
    of 10 vectors of 128-dimensional vectors).

    # Example

    ```python
        # apply a convolution 1d of length 3 to a sequence with 10 timesteps,
        # with 64 output filters
        model = Sequential()
        model.add(Convolution1D(64, 3, border_mode='same', input_shape=(10, 32)))
        # now model.output_shape == (None, 10, 64)

        # add a new conv1d on top
        model.add(Convolution1D(32, 3, border_mode='same'))
        # now model.output_shape == (None, 10, 32)
    ```

    # Arguments
        nb_filter: Number of convolution kernels to use
            (dimensionality of the output).
        filter_length: The extension (spatial or temporal) of each filter.
        init: name of initialization function for the weights of the layer
            (see [initializations](../initializations.md)),
            or alternatively, Theano function to use for weights initialization.
            This parameter is only relevant if you don't pass a `weights` argument.
        activation: name of activation function to use
            (see [activations](../activations.md)),
            or alternatively, elementwise Theano function.
            If you don't specify anything, no activation is applied
            (ie. "linear" activation: a(x) = x).
        weights: list of numpy arrays to set as initial weights.
        border_mode: 'valid' or 'same'.
        subsample_length: factor by which to subsample output.
        W_regularizer: instance of [WeightRegularizer](../regularizers.md)
            (eg. L1 or L2 regularization), applied to the main weights matrix.
        b_regularizer: instance of [WeightRegularizer](../regularizers.md),
            applied to the bias.
        activity_regularizer: instance of [ActivityRegularizer](../regularizers.md),
            applied to the network output.
        W_constraint: instance of the [constraints](../constraints.md) module
            (eg. maxnorm, nonneg), applied to the main weights matrix.
        b_constraint: instance of the [constraints](../constraints.md) module,
            applied to the bias.
        bias: whether to include a bias (i.e. make the layer affine rather than linear).
        input_dim: Number of channels/dimensions in the input.
            Either this argument or the keyword argument `input_shape`must be
            provided when using this layer as the first layer in a model.
        input_length: Length of input sequences, when it is constant.
            This argument is required if you are going to connect
            `Flatten` then `Dense` layers upstream
            (without it, the shape of the dense outputs cannot be computed).

    # Input shape
        3D tensor with shape: `(samples, steps, input_dim)`.

    # Output shape
        3D tensor with shape: `(samples, new_steps, nb_filter)`.
        `steps` value might have changed due to padding.
    '''
    def __init__(self, nb_filter, filter_length,
                 init='uniform', activation='linear', weights=None,
                 border_mode='valid', subsample_length=1,
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None,
                 bias=True, input_dim=None, input_length=None, **kwargs):

        if border_mode not in {'valid', 'same'}:
            raise Exception('Invalid border mode for Convolution1D:', border_mode)
        self.nb_filter = nb_filter
        self.filter_length = filter_length
        self.init = initializations.get(init, dim_ordering='th')
        self.activation = activations.get(activation)
        assert border_mode in {'valid', 'same'}, 'border_mode must be in {valid, same}'
        self.border_mode = border_mode
        self.subsample_length = subsample_length

        self.subsample = (subsample_length, 1)

        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)

        self.bias = bias
        self.input_spec = [InputSpec(ndim=3)]
        self.initial_weights = weights
        self.input_dim = input_dim
        self.input_length = input_length
        if self.input_dim:
            kwargs['input_shape'] = (self.input_length, self.input_dim)
        super(Convolution1D, self).__init__(**kwargs)

    def build(self, input_shape):
        input_dim = input_shape[2]
        self.W_shape = (self.nb_filter, input_dim, self.filter_length, 1)
        self.W = self.init(self.W_shape, name='{}_W'.format(self.name))
        if self.bias:
            self.b = K.zeros((self.nb_filter,), name='{}_b'.format(self.name))
            self.trainable_weights = [self.W, self.b]
        else:
            self.trainable_weights = [self.W]
        self.regularizers = []

        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.bias and self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        self.constraints = {}
        if self.W_constraint:
            self.constraints[self.W] = self.W_constraint
        if self.bias and self.b_constraint:
            self.constraints[self.b] = self.b_constraint

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def get_output_shape_for(self, input_shape):
        length = conv_output_length(input_shape[1],
                                    self.filter_length,
                                    self.border_mode,
                                    self.subsample[0])
        return (input_shape[0], length, self.nb_filter)

    def call(self, x, mask=None):
        x = K.expand_dims(x, -1)  # add a dimension of the right
        x = K.permute_dimensions(x, (0, 2, 1, 3))
        output = K.conv2d(x, self.W, strides=self.subsample,
                          border_mode=self.border_mode,
                          dim_ordering='th')
        if self.bias:
            output += K.reshape(self.b, (1, self.nb_filter, 1, 1))
        output = self.activation(output)
        output = K.squeeze(output, 3)  # remove the dummy 3rd dimension
        output = K.permute_dimensions(output, (0, 2, 1))
        return output

    def get_config(self):
        config = {'nb_filter': self.nb_filter,
                  'filter_length': self.filter_length,
                  'init': self.init.__name__,
                  'activation': self.activation.__name__,
                  'border_mode': self.border_mode,
                  'subsample_length': self.subsample_length,
                  'W_regularizer': self.W_regularizer.get_config() if self.W_regularizer else None,
                  'b_regularizer': self.b_regularizer.get_config() if self.b_regularizer else None,
                  'activity_regularizer': self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  'W_constraint': self.W_constraint.get_config() if self.W_constraint else None,
                  'b_constraint': self.b_constraint.get_config() if self.b_constraint else None,
                  'bias': self.bias,
                  'input_dim': self.input_dim,
                  'input_length': self.input_length}
        base_config = super(Convolution1D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Convolution2D(Layer):
    '''Convolution operator for filtering windows of two-dimensional inputs.
    When using this layer as the first layer in a model,
    provide the keyword argument `input_shape`
    (tuple of integers, does not include the sample axis),
    e.g. `input_shape=(3, 128, 128)` for 128x128 RGB pictures.

    # Examples

    ```python
        # apply a 3x3 convolution with 64 output filters on a 256x256 image:
        model = Sequential()
        model.add(Convolution2D(64, 3, 3, border_mode='same', input_shape=(3, 256, 256)))
        # now model.output_shape == (None, 64, 256, 256)

        # add a 3x3 convolution on top, with 32 output filters:
        model.add(Convolution2D(32, 3, 3, border_mode='same'))
        # now model.output_shape == (None, 32, 256, 256)
    ```

    # Arguments
        nb_filter: Number of convolution filters to use.
        nb_row: Number of rows in the convolution kernel.
        nb_col: Number of columns in the convolution kernel.
        init: name of initialization function for the weights of the layer
            (see [initializations](../initializations.md)), or alternatively,
            Theano function to use for weights initialization.
            This parameter is only relevant if you don't pass
            a `weights` argument.
        activation: name of activation function to use
            (see [activations](../activations.md)),
            or alternatively, elementwise Theano function.
            If you don't specify anything, no activation is applied
            (ie. "linear" activation: a(x) = x).
        weights: list of numpy arrays to set as initial weights.
        border_mode: 'valid' or 'same'.
        subsample: tuple of length 2. Factor by which to subsample output.
            Also called strides elsewhere.
        W_regularizer: instance of [WeightRegularizer](../regularizers.md)
            (eg. L1 or L2 regularization), applied to the main weights matrix.
        b_regularizer: instance of [WeightRegularizer](../regularizers.md),
            applied to the bias.
        activity_regularizer: instance of [ActivityRegularizer](../regularizers.md),
            applied to the network output.
        W_constraint: instance of the [constraints](../constraints.md) module
            (eg. maxnorm, nonneg), applied to the main weights matrix.
        b_constraint: instance of the [constraints](../constraints.md) module,
            applied to the bias.
        dim_ordering: 'th' or 'tf'. In 'th' mode, the channels dimension
            (the depth) is at index 1, in 'tf' mode is it at index 3.
        bias: whether to include a bias (i.e. make the layer affine rather than linear).

    # Input shape
        4D tensor with shape:
        `(samples, channels, rows, cols)` if dim_ordering='th'
        or 4D tensor with shape:
        `(samples, rows, cols, channels)` if dim_ordering='tf'.

    # Output shape
        4D tensor with shape:
        `(samples, nb_filter, new_rows, new_cols)` if dim_ordering='th'
        or 4D tensor with shape:
        `(samples, new_rows, new_cols, nb_filter)` if dim_ordering='tf'.
        `rows` and `cols` values might have changed due to padding.
    '''
    def __init__(self, nb_filter, nb_row, nb_col,
                 init='glorot_uniform', activation='linear', weights=None,
                 border_mode='valid', subsample=(1, 1), dim_ordering='th',
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None,
                 bias=True, **kwargs):

        if border_mode not in {'valid', 'same'}:
            raise Exception('Invalid border mode for Convolution2D:', border_mode)
        self.nb_filter = nb_filter
        self.nb_row = nb_row
        self.nb_col = nb_col
        self.init = initializations.get(init, dim_ordering=dim_ordering)
        self.activation = activations.get(activation)
        assert border_mode in {'valid', 'same'}, 'border_mode must be in {valid, same}'
        self.border_mode = border_mode
        self.subsample = tuple(subsample)
        assert dim_ordering in {'tf', 'th'}, 'dim_ordering must be in {tf, th}'
        self.dim_ordering = dim_ordering

        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)

        self.bias = bias
        self.input_spec = [InputSpec(ndim=4)]
        self.initial_weights = weights
        super(Convolution2D, self).__init__(**kwargs)

    def build(self, input_shape):
        if self.dim_ordering == 'th':
            stack_size = input_shape[1]
            self.W_shape = (self.nb_filter, stack_size, self.nb_row, self.nb_col)
        elif self.dim_ordering == 'tf':
            stack_size = input_shape[3]
            self.W_shape = (self.nb_row, self.nb_col, stack_size, self.nb_filter)
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)
        self.W = self.init(self.W_shape, name='{}_W'.format(self.name))
        if self.bias:
            self.b = K.zeros((self.nb_filter,), name='{}_b'.format(self.name))
            self.trainable_weights = [self.W, self.b]
        else:
            self.trainable_weights = [self.W]
        self.regularizers = []

        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.bias and self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        self.constraints = {}
        if self.W_constraint:
            self.constraints[self.W] = self.W_constraint
        if self.bias and self.b_constraint:
            self.constraints[self.b] = self.b_constraint

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def get_output_shape_for(self, input_shape):
        if self.dim_ordering == 'th':
            rows = input_shape[2]
            cols = input_shape[3]
        elif self.dim_ordering == 'tf':
            rows = input_shape[1]
            cols = input_shape[2]
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

        rows = conv_output_length(rows, self.nb_row,
                                  self.border_mode, self.subsample[0])
        cols = conv_output_length(cols, self.nb_col,
                                  self.border_mode, self.subsample[1])

        if self.dim_ordering == 'th':
            return (input_shape[0], self.nb_filter, rows, cols)
        elif self.dim_ordering == 'tf':
            return (input_shape[0], rows, cols, self.nb_filter)
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

    def call(self, x, mask=None):
        output = K.conv2d(x, self.W, strides=self.subsample,
                          border_mode=self.border_mode,
                          dim_ordering=self.dim_ordering,
                          filter_shape=self.W_shape)
        if self.bias:
            if self.dim_ordering == 'th':
                output += K.reshape(self.b, (1, self.nb_filter, 1, 1))
            elif self.dim_ordering == 'tf':
                output += K.reshape(self.b, (1, 1, 1, self.nb_filter))
            else:
                raise Exception('Invalid dim_ordering: ' + self.dim_ordering)
        output = self.activation(output)
        return output

    def get_config(self):
        config = {'nb_filter': self.nb_filter,
                  'nb_row': self.nb_row,
                  'nb_col': self.nb_col,
                  'init': self.init.__name__,
                  'activation': self.activation.__name__,
                  'border_mode': self.border_mode,
                  'subsample': self.subsample,
                  'dim_ordering': self.dim_ordering,
                  'W_regularizer': self.W_regularizer.get_config() if self.W_regularizer else None,
                  'b_regularizer': self.b_regularizer.get_config() if self.b_regularizer else None,
                  'activity_regularizer': self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  'W_constraint': self.W_constraint.get_config() if self.W_constraint else None,
                  'b_constraint': self.b_constraint.get_config() if self.b_constraint else None,
                  'bias': self.bias}
        base_config = super(Convolution2D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Convolution3D(Layer):
    '''Convolution operator for filtering windows of three-dimensional inputs.
    When using this layer as the first layer in a model,
    provide the keyword argument `input_shape`
    (tuple of integers, does not include the sample axis),
    e.g. `input_shape=(3, 10, 128, 128)` for 10 frames of 128x128 RGB pictures.

    Note: this layer will only work with Theano for the time being.

    # Arguments
        nb_filter: Number of convolution filters to use.
        kernel_dim1: Length of the first dimension in the covolution kernel.
        kernel_dim2: Length of the second dimension in the convolution kernel.
        kernel_dim3: Length of the third dimension in the convolution kernel.
        init: name of initialization function for the weights of the layer
            (see [initializations](../initializations.md)), or alternatively,
            Theano function to use for weights initialization.
            This parameter is only relevant if you don't pass
            a `weights` argument.
        activation: name of activation function to use
            (see [activations](../activations.md)),
            or alternatively, elementwise Theano function.
            If you don't specify anything, no activation is applied
            (ie. "linear" activation: a(x) = x).
        weights: list of numpy arrays to set as initial weights.
        border_mode: 'valid' or 'same'.
        subsample: tuple of length 3. Factor by which to subsample output.
            Also called strides elsewhere.
            Note: 'subsample' is implemented by slicing the output of conv3d with strides=(1,1,1).
        W_regularizer: instance of [WeightRegularizer](../regularizers.md)
            (eg. L1 or L2 regularization), applied to the main weights matrix.
        b_regularizer: instance of [WeightRegularizer](../regularizers.md),
            applied to the bias.
        activity_regularizer: instance of [ActivityRegularizer](../regularizers.md),
            applied to the network output.
        W_constraint: instance of the [constraints](../constraints.md) module
            (eg. maxnorm, nonneg), applied to the main weights matrix.
        b_constraint: instance of the [constraints](../constraints.md) module,
            applied to the bias.
        dim_ordering: 'th' or 'tf'. In 'th' mode, the channels dimension
            (the depth) is at index 1, in 'tf' mode is it at index 4.
        bias: whether to include a bias (i.e. make the layer affine rather than linear).

    # Input shape
        5D tensor with shape:
        `(samples, channels, conv_dim1, conv_dim2, conv_dim3)` if dim_ordering='th'
        or 5D tensor with shape:
        `(samples, conv_dim1, conv_dim2, conv_dim3, channels)` if dim_ordering='tf'.

    # Output shape
        5D tensor with shape:
        `(samples, nb_filter, new_conv_dim1, new_conv_dim2, new_conv_dim3)` if dim_ordering='th'
        or 5D tensor with shape:
        `(samples, new_conv_dim1, new_conv_dim2, new_conv_dim3, nb_filter)` if dim_ordering='tf'.
        `new_conv_dim1`, `new_conv_dim2` and `new_conv_dim3` values might have changed due to padding.
    '''

    def __init__(self, nb_filter, kernel_dim1, kernel_dim2, kernel_dim3,
                 init='glorot_uniform', activation='linear', weights=None,
                 border_mode='valid', subsample=(1, 1, 1), dim_ordering='th',
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None,
                 bias=True, **kwargs):
        if K._BACKEND != 'theano':
            raise Exception(self.__class__.__name__ +
                            ' is currently only working with Theano backend.')
        if border_mode not in {'valid', 'same'}:
            raise Exception('Invalid border mode for Convolution3D:', border_mode)
        self.nb_filter = nb_filter
        self.kernel_dim1 = kernel_dim1
        self.kernel_dim2 = kernel_dim2
        self.kernel_dim3 = kernel_dim3
        self.init = initializations.get(init, dim_ordering=dim_ordering)
        self.activation = activations.get(activation)
        assert border_mode in {'valid', 'same'}, 'border_mode must be in {valid, same}'
        self.border_mode = border_mode
        self.subsample = tuple(subsample)
        assert dim_ordering in {'tf', 'th'}, 'dim_ordering must be in {tf, th}'
        self.dim_ordering = dim_ordering

        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)

        self.bias = bias
        self.input_spec = [InputSpec(ndim=5)]
        self.initial_weights = weights
        super(Convolution3D, self).__init__(**kwargs)

    def build(self, input_shape):
        assert len(input_shape) == 5
        self.input_spec = [InputSpec(shape=input_shape)]

        if self.dim_ordering == 'th':
            stack_size = input_shape[1]
            self.W_shape = (self.nb_filter, stack_size,
                            self.kernel_dim1, self.kernel_dim2, self.kernel_dim3)
        elif self.dim_ordering == 'tf':
            stack_size = input_shape[4]
            self.W_shape = (self.kernel_dim1, self.kernel_dim2, self.kernel_dim3,
                            stack_size, self.nb_filter)
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

        self.W = self.init(self.W_shape, name='{}_W'.format(self.name))
        if self.bias:
            self.b = K.zeros((self.nb_filter,), name='{}_b'.format(self.name))
            self.trainable_weights = [self.W, self.b]
        else:
            self.trainable_weights = [self.W]

        self.regularizers = []
        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.bias and self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        self.constraints = {}
        if self.W_constraint:
            self.constraints[self.W] = self.W_constraint
        if self.bias and self.b_constraint:
            self.constraints[self.b] = self.b_constraint

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def get_output_shape_for(self, input_shape):
        if self.dim_ordering == 'th':
            conv_dim1 = input_shape[2]
            conv_dim2 = input_shape[3]
            conv_dim3 = input_shape[4]
        elif self.dim_ordering == 'tf':
            conv_dim1 = input_shape[1]
            conv_dim2 = input_shape[2]
            conv_dim3 = input_shape[3]
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

        conv_dim1 = conv_output_length(conv_dim1, self.kernel_dim1,
                                       self.border_mode, self.subsample[0])
        conv_dim2 = conv_output_length(conv_dim2, self.kernel_dim2,
                                       self.border_mode, self.subsample[1])
        conv_dim3 = conv_output_length(conv_dim3, self.kernel_dim3,
                                       self.border_mode, self.subsample[2])

        if self.dim_ordering == 'th':
            return (input_shape[0], self.nb_filter, conv_dim1, conv_dim2, conv_dim3)
        elif self.dim_ordering == 'tf':
            return (input_shape[0], conv_dim1, conv_dim2, conv_dim3, self.nb_filter)
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

    def call(self, x, mask=None):
        input_shape = self.input_spec[0].shape
        output = K.conv3d(x, self.W, strides=self.subsample,
                          border_mode=self.border_mode,
                          dim_ordering=self.dim_ordering,
                          volume_shape=input_shape,
                          filter_shape=self.W_shape)
        if self.bias:
            if self.dim_ordering == 'th':
                output += K.reshape(self.b, (1, self.nb_filter, 1, 1, 1))
            elif self.dim_ordering == 'tf':
                output += K.reshape(self.b, (1, 1, 1, 1, self.nb_filter))
            else:
                raise Exception('Invalid dim_ordering: ' + self.dim_ordering)
        output = self.activation(output)
        return output

    def get_config(self):
        config = {'nb_filter': self.nb_filter,
                  'kernel_dim1': self.kernel_dim1,
                  'kernel_dim2': self.kernel_dim2,
                  'kernel_dim3': self.kernel_dim3,
                  'dim_ordering': self.dim_ordering,
                  'init': self.init.__name__,
                  'activation': self.activation.__name__,
                  'border_mode': self.border_mode,
                  'subsample': self.subsample,
                  'W_regularizer': self.W_regularizer.get_config() if self.W_regularizer else None,
                  'b_regularizer': self.b_regularizer.get_config() if self.b_regularizer else None,
                  'activity_regularizer': self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  'W_constraint': self.W_constraint.get_config() if self.W_constraint else None,
                  'b_constraint': self.b_constraint.get_config() if self.b_constraint else None,
                  'bias': self.bias}
        base_config = super(Convolution3D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class _Pooling1D(Layer):
    '''Abstract class for different pooling 1D layers.
    '''
    input_dim = 3

    def __init__(self, pool_length=2, stride=None,
                 border_mode='valid', **kwargs):
        super(_Pooling1D, self).__init__(**kwargs)
        if stride is None:
            stride = pool_length
        self.pool_length = pool_length
        self.stride = stride
        self.st = (self.stride, 1)
        self.pool_size = (pool_length, 1)
        assert border_mode in {'valid', 'same'}, 'border_mode must be in {valid, same}'
        self.border_mode = border_mode
        self.input_spec = [InputSpec(ndim=3)]

    def get_output_shape_for(self, input_shape):
        length = conv_output_length(input_shape[1], self.pool_length,
                                    self.border_mode, self.stride)
        return (input_shape[0], length, input_shape[2])

    def _pooling_function(self, back_end, inputs, pool_size, strides,
                          border_mode, dim_ordering):
        raise NotImplementedError

    def call(self, x, mask=None):
        x = K.expand_dims(x, -1)   # add dummy last dimension
        x = K.permute_dimensions(x, (0, 2, 1, 3))
        output = self._pooling_function(inputs=x, pool_size=self.pool_size,
                                        strides=self.st,
                                        border_mode=self.border_mode,
                                        dim_ordering='th')
        output = K.permute_dimensions(output, (0, 2, 1, 3))
        return K.squeeze(output, 3)  # remove dummy last dimension

    def get_config(self):
        config = {'stride': self.stride,
                  'pool_length': self.pool_length,
                  'border_mode': self.border_mode}
        base_config = super(_Pooling1D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class MaxPooling1D(_Pooling1D):
    '''Max pooling operation for temporal data.

    # Input shape
        3D tensor with shape: `(samples, steps, features)`.

    # Output shape
        3D tensor with shape: `(samples, downsampled_steps, features)`.

    # Arguments
        pool_length: factor by which to downscale. 2 will halve the input.
        stride: integer or None. Stride value.
        border_mode: 'valid' or 'same'.
            Note: 'same' will only work with TensorFlow for the time being.
    '''

    def __init__(self, pool_length=2, stride=None,
                 border_mode='valid', **kwargs):
        super(MaxPooling1D, self).__init__(pool_length, stride,
                                           border_mode, **kwargs)

    def _pooling_function(self, inputs, pool_size, strides,
                          border_mode, dim_ordering):
        output = K.pool2d(inputs, pool_size, strides,
                          border_mode, dim_ordering, pool_mode='max')
        return output


class AveragePooling1D(_Pooling1D):
    '''Average pooling for temporal data.

    # Arguments
        pool_length: factor by which to downscale. 2 will halve the input.
        stride: integer or None. Stride value.
        border_mode: 'valid' or 'same'.
            Note: 'same' will only work with TensorFlow for the time being.

    # Input shape
        3D tensor with shape: `(samples, steps, features)`.

    # Output shape
        3D tensor with shape: `(samples, downsampled_steps, features)`.
    '''

    def __init__(self, pool_length=2, stride=None,
                 border_mode='valid', **kwargs):
        super(AveragePooling1D, self).__init__(pool_length, stride,
                                               border_mode, **kwargs)

    def _pooling_function(self, inputs, pool_size, strides,
                          border_mode, dim_ordering):
        output = K.pool2d(inputs, pool_size, strides,
                          border_mode, dim_ordering, pool_mode='avg')
        return output


class _Pooling2D(Layer):
    '''Abstract class for different pooling 2D layers.
    '''

    def __init__(self, pool_size=(2, 2), strides=None, border_mode='valid',
                 dim_ordering='th', **kwargs):
        super(_Pooling2D, self).__init__(**kwargs)
        self.pool_size = tuple(pool_size)
        if strides is None:
            strides = self.pool_size
        self.strides = tuple(strides)
        assert border_mode in {'valid', 'same'}, 'border_mode must be in {valid, same}'
        self.border_mode = border_mode
        assert dim_ordering in {'tf', 'th'}, 'dim_ordering must be in {tf, th}'
        self.dim_ordering = dim_ordering
        self.input_spec = [InputSpec(ndim=4)]

    def get_output_shape_for(self, input_shape):
        if self.dim_ordering == 'th':
            rows = input_shape[2]
            cols = input_shape[3]
        elif self.dim_ordering == 'tf':
            rows = input_shape[1]
            cols = input_shape[2]
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

        rows = conv_output_length(rows, self.pool_size[0],
                                  self.border_mode, self.strides[0])
        cols = conv_output_length(cols, self.pool_size[1],
                                  self.border_mode, self.strides[1])

        if self.dim_ordering == 'th':
            return (input_shape[0], input_shape[1], rows, cols)
        elif self.dim_ordering == 'tf':
            return (input_shape[0], rows, cols, input_shape[3])
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

    def _pooling_function(self, inputs, pool_size, strides,
                          border_mode, dim_ordering):
        raise NotImplementedError

    def call(self, x, mask=None):
        output = self._pooling_function(inputs=x, pool_size=self.pool_size,
                                        strides=self.strides,
                                        border_mode=self.border_mode,
                                        dim_ordering=self.dim_ordering)
        return output

    def get_config(self):
        config = {'pool_size': self.pool_size,
                  'border_mode': self.border_mode,
                  'strides': self.strides,
                  'dim_ordering': self.dim_ordering}
        base_config = super(_Pooling2D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class MaxPooling2D(_Pooling2D):
    '''Max pooling operation for spatial data.

    # Arguments
        pool_size: tuple of 2 integers,
            factors by which to downscale (vertical, horizontal).
            (2, 2) will halve the image in each dimension.
        strides: tuple of 2 integers, or None. Strides values.
        border_mode: 'valid' or 'same'.
            Note: 'same' will only work with TensorFlow for the time being.
        dim_ordering: 'th' or 'tf'. In 'th' mode, the channels dimension
            (the depth) is at index 1, in 'tf' mode is it at index 3.

    # Input shape
        4D tensor with shape:
        `(samples, channels, rows, cols)` if dim_ordering='th'
        or 4D tensor with shape:
        `(samples, rows, cols, channels)` if dim_ordering='tf'.

    # Output shape
        4D tensor with shape:
        `(nb_samples, channels, pooled_rows, pooled_cols)` if dim_ordering='th'
        or 4D tensor with shape:
        `(samples, pooled_rows, pooled_cols, channels)` if dim_ordering='tf'.
    '''

    def __init__(self, pool_size=(2, 2), strides=None, border_mode='valid',
                 dim_ordering='th', **kwargs):
        super(MaxPooling2D, self).__init__(pool_size, strides, border_mode,
                                           dim_ordering, **kwargs)

    def _pooling_function(self, inputs, pool_size, strides,
                          border_mode, dim_ordering):
        output = K.pool2d(inputs, pool_size, strides,
                          border_mode, dim_ordering, pool_mode='max')
        return output


class AveragePooling2D(_Pooling2D):
    '''Average pooling operation for spatial data.

    # Arguments
        pool_size: tuple of 2 integers,
            factors by which to downscale (vertical, horizontal).
            (2, 2) will halve the image in each dimension.
        strides: tuple of 2 integers, or None. Strides values.
        border_mode: 'valid' or 'same'.
            Note: 'same' will only work with TensorFlow for the time being.
        dim_ordering: 'th' or 'tf'. In 'th' mode, the channels dimension
            (the depth) is at index 1, in 'tf' mode is it at index 3.

    # Input shape
        4D tensor with shape:
        `(samples, channels, rows, cols)` if dim_ordering='th'
        or 4D tensor with shape:
        `(samples, rows, cols, channels)` if dim_ordering='tf'.

    # Output shape
        4D tensor with shape:
        `(nb_samples, channels, pooled_rows, pooled_cols)` if dim_ordering='th'
        or 4D tensor with shape:
        `(samples, pooled_rows, pooled_cols, channels)` if dim_ordering='tf'.
    '''

    def __init__(self, pool_size=(2, 2), strides=None, border_mode='valid',
                 dim_ordering='th', **kwargs):
        super(AveragePooling2D, self).__init__(pool_size, strides, border_mode,
                                               dim_ordering, **kwargs)

    def _pooling_function(self, inputs, pool_size, strides,
                          border_mode, dim_ordering):
        output = K.pool2d(inputs, pool_size, strides,
                          border_mode, dim_ordering, pool_mode='avg')
        return output


class _Pooling3D(Layer):
    '''Abstract class for different pooling 3D layers.
    '''

    def __init__(self, pool_size=(2, 2, 2), strides=None, border_mode='valid',
                 dim_ordering='th', **kwargs):
        super(_Pooling3D, self).__init__(**kwargs)
        self.pool_size = tuple(pool_size)
        if strides is None:
            strides = self.pool_size
        self.strides = tuple(strides)
        assert border_mode in {'valid', 'same'}, 'border_mode must be in {valid, same}'
        self.border_mode = border_mode
        assert dim_ordering in {'tf', 'th'}, 'dim_ordering must be in {tf, th}'
        self.dim_ordering = dim_ordering
        self.input_spec = [InputSpec(ndim=5)]

    def get_output_shape_for(self, input_shape):
        if self.dim_ordering == 'th':
            len_dim1 = input_shape[2]
            len_dim2 = input_shape[3]
            len_dim3 = input_shape[4]
        elif self.dim_ordering == 'tf':
            len_dim1 = input_shape[1]
            len_dim2 = input_shape[2]
            len_dim3 = input_shape[3]
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

        len_dim1 = conv_output_length(len_dim1, self.pool_size[0],
                                      self.border_mode, self.strides[0])
        len_dim2 = conv_output_length(len_dim2, self.pool_size[1],
                                      self.border_mode, self.strides[1])
        len_dim3 = conv_output_length(len_dim3, self.pool_size[2],
                                      self.border_mode, self.strides[2])

        if self.dim_ordering == 'th':
            return (input_shape[0], input_shape[1], len_dim1, len_dim2, len_dim3)
        elif self.dim_ordering == 'tf':
            return (input_shape[0], len_dim1, len_dim2, len_dim3, input_shape[4])
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

    def _pooling_function(self, inputs, pool_size, strides,
                          border_mode, dim_ordering):
        raise NotImplementedError

    def call(self, x, mask=None):
        output = self._pooling_function(inputs=x, pool_size=self.pool_size,
                                        strides=self.strides,
                                        border_mode=self.border_mode,
                                        dim_ordering=self.dim_ordering)
        return output

    def get_config(self):
        config = {'pool_size': self.pool_size,
                  'border_mode': self.border_mode,
                  'strides': self.strides,
                  'dim_ordering': self.dim_ordering}
        base_config = super(_Pooling3D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class MaxPooling3D(_Pooling3D):
    '''Max pooling operation for 3D data (spatial or spatio-temporal).

    Note: this layer will only work with Theano for the time being.

    # Arguments
        pool_size: tuple of 3 integers,
            factors by which to downscale (dim1, dim2, dim3).
            (2, 2, 2) will halve the size of the 3D input in each dimension.
        strides: tuple of 3 integers, or None. Strides values.
        border_mode: 'valid' or 'same'.
        dim_ordering: 'th' or 'tf'. In 'th' mode, the channels dimension
            (the depth) is at index 1, in 'tf' mode is it at index 4.

    # Input shape
        5D tensor with shape:
        `(samples, channels, len_pool_dim1, len_pool_dim2, len_pool_dim3)` if dim_ordering='th'
        or 5D tensor with shape:
        `(samples, len_pool_dim1, len_pool_dim2, len_pool_dim3, channels)` if dim_ordering='tf'.

    # Output shape
        5D tensor with shape:
        `(nb_samples, channels, pooled_dim1, pooled_dim2, pooled_dim3)` if dim_ordering='th'
        or 5D tensor with shape:
        `(samples, pooled_dim1, pooled_dim2, pooled_dim3, channels)` if dim_ordering='tf'.
    '''

    def __init__(self, pool_size=(2, 2, 2), strides=None, border_mode='valid',
                 dim_ordering='th', **kwargs):
        if K._BACKEND != 'theano':
            raise Exception(self.__class__.__name__ +
                            ' is currently only working with Theano backend.')
        super(MaxPooling3D, self).__init__(pool_size, strides, border_mode,
                                           dim_ordering, **kwargs)

    def _pooling_function(self, inputs, pool_size, strides,
                          border_mode, dim_ordering):
        output = K.pool3d(inputs, pool_size, strides,
                          border_mode, dim_ordering, pool_mode='max')
        return output


class AveragePooling3D(_Pooling3D):
    '''Average pooling operation for 3D data (spatial or spatio-temporal).

    Note: this layer will only work with Theano for the time being.

    # Arguments
        pool_size: tuple of 3 integers,
            factors by which to downscale (dim1, dim2, dim3).
            (2, 2, 2) will halve the size of the 3D input in each dimension.
        strides: tuple of 3 integers, or None. Strides values.
        border_mode: 'valid' or 'same'.
        dim_ordering: 'th' or 'tf'. In 'th' mode, the channels dimension
            (the depth) is at index 1, in 'tf' mode is it at index 4.

    # Input shape
        5D tensor with shape:
        `(samples, channels, len_pool_dim1, len_pool_dim2, len_pool_dim3)` if dim_ordering='th'
        or 5D tensor with shape:
        `(samples, len_pool_dim1, len_pool_dim2, len_pool_dim3, channels)` if dim_ordering='tf'.

    # Output shape
        5D tensor with shape:
        `(nb_samples, channels, pooled_dim1, pooled_dim2, pooled_dim3)` if dim_ordering='th'
        or 5D tensor with shape:
        `(samples, pooled_dim1, pooled_dim2, pooled_dim3, channels)` if dim_ordering='tf'.
    '''

    def __init__(self, pool_size=(2, 2, 2), strides=None, border_mode='valid',
                 dim_ordering='th', **kwargs):
        if K._BACKEND != 'theano':
            raise Exception(self.__class__.__name__ +
                            ' is currently only working with Theano backend.')
        super(AveragePooling3D, self).__init__(pool_size, strides, border_mode,
                                               dim_ordering, **kwargs)

    def _pooling_function(self, inputs, pool_size, strides,
                          border_mode, dim_ordering):
        output = K.pool3d(inputs, pool_size, strides,
                          border_mode, dim_ordering, pool_mode='avg')
        return output


class UpSampling1D(Layer):
    '''Repeat each temporal step `length` times along the time axis.

    # Arguments
        length: integer. Upsampling factor.

    # Input shape
        3D tensor with shape: `(samples, steps, features)`.

    # Output shape
        3D tensor with shape: `(samples, upsampled_steps, features)`.
    '''

    def __init__(self, length=2, **kwargs):
        self.length = length
        self.input_spec = [InputSpec(ndim=3)]
        super(UpSampling1D, self).__init__(**kwargs)

    def get_output_shape_for(self, input_shape):
        return (input_shape[0], self.length * input_shape[1], input_shape[2])

    def call(self, x, mask=None):
        output = K.repeat_elements(x, self.length, axis=1)
        return output

    def get_config(self):
        config = {'length': self.length}
        base_config = super(UpSampling1D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class UpSampling2D(Layer):
    '''Repeat the rows and columns of the data
    by size[0] and size[1] respectively.

    # Arguments
        size: tuple of 2 integers. The upsampling factors for rows and columns.
        dim_ordering: 'th' or 'tf'.
            In 'th' mode, the channels dimension (the depth)
            is at index 1, in 'tf' mode is it at index 3.

    # Input shape
        4D tensor with shape:
        `(samples, channels, rows, cols)` if dim_ordering='th'
        or 4D tensor with shape:
        `(samples, rows, cols, channels)` if dim_ordering='tf'.

    # Output shape
        4D tensor with shape:
        `(samples, channels, upsampled_rows, upsampled_cols)` if dim_ordering='th'
        or 4D tensor with shape:
        `(samples, upsampled_rows, upsampled_cols, channels)` if dim_ordering='tf'.
    '''

    def __init__(self, size=(2, 2), dim_ordering='th', **kwargs):
        self.size = tuple(size)
        assert dim_ordering in {'tf', 'th'}, 'dim_ordering must be in {tf, th}'
        self.dim_ordering = dim_ordering
        self.input_spec = [InputSpec(ndim=4)]
        super(UpSampling2D, self).__init__(**kwargs)

    def get_output_shape_for(self, input_shape):
        if self.dim_ordering == 'th':
            return (input_shape[0],
                    input_shape[1],
                    self.size[0] * input_shape[2],
                    self.size[1] * input_shape[3])
        elif self.dim_ordering == 'tf':
            return (input_shape[0],
                    self.size[0] * input_shape[1],
                    self.size[1] * input_shape[2],
                    input_shape[3])
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

    def call(self, x, mask=None):
        return K.resize_images(x, self.size[0], self.size[1],
                               self.dim_ordering)

    def get_config(self):
        config = {'size': self.size}
        base_config = super(UpSampling2D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class UpSampling3D(Layer):
    '''Repeat the first, second and third dimension of the data
    by size[0], size[1] and size[2] respectively.

    Note: this layer will only work with Theano for the time being.

    # Arguments
        size: tuple of 3 integers. The upsampling factors for dim1, dim2 and dim3.
        dim_ordering: 'th' or 'tf'.
            In 'th' mode, the channels dimension (the depth)
            is at index 1, in 'tf' mode is it at index 4.

    # Input shape
        5D tensor with shape:
        `(samples, channels, dim1, dim2, dim3)` if dim_ordering='th'
        or 5D tensor with shape:
        `(samples, dim1, dim2, dim3, channels)` if dim_ordering='tf'.

    # Output shape
        5D tensor with shape:
        `(samples, channels, upsampled_dim1, upsampled_dim2, upsampled_dim3)` if dim_ordering='th'
        or 5D tensor with shape:
        `(samples, upsampled_dim1, upsampled_dim2, upsampled_dim3, channels)` if dim_ordering='tf'.
    '''

    def __init__(self, size=(2, 2, 2), dim_ordering='th', **kwargs):
        if K._BACKEND != 'theano':
            raise Exception(self.__class__.__name__ +
                            ' is currently only working with Theano backend.') 
        self.size = tuple(size)
        assert dim_ordering in {'tf', 'th'}, 'dim_ordering must be in {tf, th}'
        self.dim_ordering = dim_ordering
        self.input_spec = [InputSpec(ndim=5)]
        super(UpSampling3D, self).__init__(**kwargs)

    def get_output_shape_for(self, input_shape):
        if self.dim_ordering == 'th':
            return (input_shape[0],
                    input_shape[1],
                    self.size[0] * input_shape[2],
                    self.size[1] * input_shape[3],
                    self.size[2] * input_shape[4])
        elif self.dim_ordering == 'tf':
            return (input_shape[0],
                    self.size[0] * input_shape[1],
                    self.size[1] * input_shape[2],
                    self.size[2] * input_shape[3],
                    input_shape[4])
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

    def call(self, x, mask=None):
        return K.resize_volumes(x, self.size[0], self.size[1], self.size[2],
                                self.dim_ordering)

    def get_config(self):
        config = {'size': self.size}
        base_config = super(UpSampling3D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ZeroPadding1D(Layer):
    '''Zero-padding layer for 1D input (e.g. temporal sequence).

    # Arguments
        padding: int
            How many zeros to add at the beginning and end of
            the padding dimension (axis 1).

    # Input shape
        3D tensor with shape (samples, axis_to_pad, features)

    # Output shape
        3D tensor with shape (samples, padded_axis, features)
    '''

    def __init__(self, padding=1, **kwargs):
        super(ZeroPadding1D, self).__init__(**kwargs)
        self.padding = padding
        self.input_spec = [InputSpec(ndim=3)]

    def get_output_shape_for(self, input_shape):
        length = input_shape[1] + self.padding * 2 if input_shape[1] is not None else None
        return (input_shape[0],
                length,
                input_shape[2])

    def call(self, x, mask=None):
        return K.temporal_padding(x, padding=self.padding)

    def get_config(self):
        config = {'padding': self.padding}
        base_config = super(ZeroPadding1D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ZeroPadding2D(Layer):
    '''Zero-padding layer for 2D input (e.g. picture).

    # Arguments
        padding: tuple of int (length 2)
            How many zeros to add at the beginning and end of
            the 2 padding dimensions (axis 3 and 4).

    # Input shape
        4D tensor with shape:
        (samples, depth, first_axis_to_pad, second_axis_to_pad)

    # Output shape
        4D tensor with shape:
        (samples, depth, first_padded_axis, second_padded_axis)
    '''

    def __init__(self, padding=(1, 1), dim_ordering='th', **kwargs):
        super(ZeroPadding2D, self).__init__(**kwargs)
        self.padding = tuple(padding)
        assert dim_ordering in {'tf', 'th'}, 'dim_ordering must be in {tf, th}'
        self.dim_ordering = dim_ordering
        self.input_spec = [InputSpec(ndim=4)]

    def get_output_shape_for(self, input_shape):
        if self.dim_ordering == 'th':
            width = input_shape[2] + 2 * self.padding[0] if input_shape[2] is not None else None
            height = input_shape[3] + 2 * self.padding[1] if input_shape[3] is not None else None
            return (input_shape[0],
                    input_shape[1],
                    width,
                    height)
        elif self.dim_ordering == 'tf':
            width = input_shape[1] + 2 * self.padding[0] if input_shape[1] is not None else None
            height = input_shape[2] + 2 * self.padding[1] if input_shape[2] is not None else None
            return (input_shape[0],
                    width,
                    height,
                    input_shape[3])
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

    def call(self, x, mask=None):
        return K.spatial_2d_padding(x, padding=self.padding,
                                    dim_ordering=self.dim_ordering)

    def get_config(self):
        config = {'padding': self.padding}
        base_config = super(ZeroPadding2D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ZeroPadding3D(Layer):
    '''Zero-padding layer for 3D data (spatial or spatio-temporal).

    Note: this layer will only work with Theano for the time being.

    # Arguments
        padding: tuple of int (length 3)
            How many zeros to add at the beginning and end of
            the 3 padding dimensions (axis 3, 4 and 5).

    # Input shape
        5D tensor with shape:
        (samples, depth, first_axis_to_pad, second_axis_to_pad, third_axis_to_pad)

    # Output shape
        5D tensor with shape:
        (samples, depth, first_padded_axis, second_padded_axis, third_axis_to_pad)
    '''

    def __init__(self, padding=(1, 1, 1), dim_ordering='th', **kwargs):
        if K._BACKEND != 'theano':
            raise Exception(self.__class__.__name__ +
                            ' is currently only working with Theano backend.')
        super(ZeroPadding3D, self).__init__(**kwargs)
        self.padding = tuple(padding)
        assert dim_ordering in {'tf', 'th'}, 'dim_ordering must be in {tf, th}'
        self.dim_ordering = dim_ordering
        self.input_spec = [InputSpec(ndim=5)]

    def get_output_shape_for(self, input_shape):
        if self.dim_ordering == 'th':
            dim1 = input_shape[2] + 2 * self.padding[0] if input_shape[2] is not None else None
            dim2 = input_shape[3] + 2 * self.padding[1] if input_shape[3] is not None else None
            dim3 = input_shape[4] + 2 * self.padding[2] if input_shape[4] is not None else None
            return (input_shape[0],
                    input_shape[1],
                    dim1,
                    dim2,
                    dim3)
        elif self.dim_ordering == 'tf':
            dim1 = input_shape[1] + 2 * self.padding[0] if input_shape[1] is not None else None
            dim2 = input_shape[2] + 2 * self.padding[1] if input_shape[2] is not None else None
            dim3 = input_shape[3] + 2 * self.padding[2] if input_shape[3] is not None else None
            return (input_shape[0],
                    dim1,
                    dim2,
                    dim3,
                    input_shape[4])
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

    def call(self, x, mask=None):
        return K.spatial_3d_padding(x, padding=self.padding,
                                    dim_ordering=self.dim_ordering)

    def get_config(self):
        config = {'padding': self.padding}
        base_config = super(ZeroPadding3D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

# -*- coding: utf-8 -*-
from __future__ import absolute_import
import numpy as np

from .. import backend as K
from .. import activations, initializations, regularizers
from ..engine import Layer, InputSpec


def time_distributed_dense(x, w, b=None, dropout=None,
                           input_dim=None, output_dim=None, timesteps=None):
    '''Apply y.w + b for every temporal slice y of x.
    '''
    if not input_dim:
        # won't work with TensorFlow
        input_dim = K.shape(x)[2]
    if not timesteps:
        # won't work with TensorFlow
        timesteps = K.shape(x)[1]
    if not output_dim:
        # won't work with TensorFlow
        output_dim = K.shape(w)[1]

    if dropout is not None and 0. < dropout < 1.:
        # apply the same dropout pattern at every timestep
        ones = K.ones_like(K.reshape(x[:, 0, :], (-1, input_dim)))
        dropout_matrix = K.dropout(ones, dropout)
        expanded_dropout_matrix = K.repeat(dropout_matrix, timesteps)
        x = K.in_train_phase(x * expanded_dropout_matrix, x)

    # collapse time dimension and batch dimension together
    x = K.reshape(x, (-1, input_dim))

    x = K.dot(x, w)
    if b:
        x = x + b
    # reshape to 3D tensor
    x = K.reshape(x, (-1, timesteps, output_dim))
    return x


class Recurrent(Layer):
    '''Abstract base class for recurrent layers.
    Do not use in a model -- it's not a valid layer!
    Use its children classes `LSTM`, `GRU` and `SimpleRNN` instead.

    All recurrent layers (`LSTM`, `GRU`, `SimpleRNN`) also
    follow the specifications of this class and accept
    the keyword arguments listed below.

    # Example

    ```python
        # as the first layer in a Sequential model
        model = Sequential()
        model.add(LSTM(32, input_shape=(10, 64)))
        # now model.output_shape == (None, 10, 32)
        # note: `None` is the batch dimension.

        # the following is identical:
        model = Sequential()
        model.add(LSTM(32, input_dim=64, input_length=10))

        # for subsequent layers, not need to specify the input size:
        model.add(LSTM(16))
    ```

    # Arguments
        weights: list of numpy arrays to set as initial weights.
            The list should have 3 elements, of shapes:
            `[(input_dim, output_dim), (output_dim, output_dim), (output_dim,)]`.
        return_sequences: Boolean. Whether to return the last output
            in the output sequence, or the full sequence.
        go_backwards: Boolean (default False).
            If True, process the input sequence backwards.
        stateful: Boolean (default False). If True, the last state
            for each sample at index i in a batch will be used as initial
            state for the sample of index i in the following batch.
        unroll: Boolean (default False). If True, the network will be unrolled,
            else a symbolic loop will be used. When using TensorFlow, the network
            is always unrolled, so this argument does not do anything.
            Unrolling can speed-up a RNN, although it tends to be more memory-intensive.
            Unrolling is only suitable for short sequences.
        consume_less: one of "cpu", "mem", or "gpu".
            Note that "gpu" mode is only available for LSTM.

            If set to "cpu", the RNN will use
            an implementation that uses fewer, larger matrix products,
            thus running faster on CPU but consuming more memory.

            If set to "mem", the RNN will use more matrix products,
            but smaller ones, thus running slower (may actually be faster on GPU)
            while consuming less memory.

            If set to "gpu" (LSTM only), the LSTM will combine the input gate,
            the forget gate and the output gate into a single matrix,
            enabling more time-efficient parallelization on the GPU. Note: RNN
            dropout must be shared for all gates, resulting in a slightly
            reduced regularization.
        input_dim: dimensionality of the input (integer).
            This argument (or alternatively, the keyword argument `input_shape`)
            is required when using this layer as the first layer in a model.
        input_length: Length of input sequences, to be specified
            when it is constant.
            This argument is required if you are going to connect
            `Flatten` then `Dense` layers upstream
            (without it, the shape of the dense outputs cannot be computed).
            Note that if the recurrent layer is not the first layer
            in your model, you would need to specify the input length
            at the level of the first layer
            (e.g. via the `input_shape` argument)

    # Input shape
        3D tensor with shape `(nb_samples, timesteps, input_dim)`.

    # Output shape
        - if `return_sequences`: 3D tensor with shape
            `(nb_samples, timesteps, output_dim)`.
        - else, 2D tensor with shape `(nb_samples, output_dim)`.

    # Masking
        This layer supports masking for input data with a variable number
        of timesteps. To introduce masks to your data,
        use an [Embedding](embeddings.md) layer with the `mask_zero` parameter
        set to `True`.

    # TensorFlow warning
        For the time being, when using the TensorFlow backend,
        the number of timesteps used must be specified in your model.
        Make sure to pass an `input_length` int argument to your
        recurrent layer (if it comes first in your model),
        or to pass a complete `input_shape` argument to the first layer
        in your model otherwise.


    # Note on using statefulness in RNNs
        You can set RNN layers to be 'stateful', which means that the states
        computed for the samples in one batch will be reused as initial states
        for the samples in the next batch.
        This assumes a one-to-one mapping between
        samples in different successive batches.

        To enable statefulness:
            - specify `stateful=True` in the layer constructor.
            - specify a fixed batch size for your model, by passing
                a `batch_input_shape=(...)` to the first layer in your model.
                This is the expected shape of your inputs *including the batch size*.
                It should be a tuple of integers, e.g. `(32, 10, 100)`.

        To reset the states of your model, call `.reset_states()` on either
        a specific layer, or on your entire model.

    # Note on using dropout with TensorFlow
        When using the TensorFlow backend, specify a fixed batch size for your model
        following the notes on statefulness RNNs.
    '''
    def __init__(self, weights=None,
                 return_sequences=False, go_backwards=False, stateful=False,
                 unroll=False, consume_less='cpu',
                 input_dim=None, input_length=None, **kwargs):
        self.return_sequences = return_sequences
        self.initial_weights = weights
        self.go_backwards = go_backwards
        self.stateful = stateful
        self.unroll = unroll
        self.consume_less = consume_less

        self.supports_masking = True
        self.input_spec = [InputSpec(ndim=3)]
        self.input_dim = input_dim
        self.input_length = input_length
        if self.input_dim:
            kwargs['input_shape'] = (self.input_length, self.input_dim)
        super(Recurrent, self).__init__(**kwargs)

    def get_output_shape_for(self, input_shape):
        if self.return_sequences:
            return (input_shape[0], input_shape[1], self.output_dim)
        else:
            return (input_shape[0], self.output_dim)

    def compute_mask(self, input, mask):
        if self.return_sequences:
            return mask
        else:
            return None

    def step(self, x, states):
        raise NotImplementedError

    def get_constants(self, x):
        return []

    def get_initial_states(self, x):
        # build an all-zero tensor of shape (samples, output_dim)
        initial_state = K.zeros_like(x)  # (samples, timesteps, input_dim)
        initial_state = K.sum(initial_state, axis=1)  # (samples, input_dim)
        reducer = K.zeros((self.input_dim, self.output_dim))
        initial_state = K.dot(initial_state, reducer)  # (samples, output_dim)
        initial_states = [initial_state for _ in range(len(self.states))]
        return initial_states

    def preprocess_input(self, x):
        return x

    def call(self, x, mask=None):
        # input shape: (nb_samples, time (padded with zeros), input_dim)
        # note that the .build() method of subclasses MUST define
        # self.input_spec with a complete input shape.
        input_shape = self.input_spec[0].shape
        if K._BACKEND == 'tensorflow':
            if not input_shape[1]:
                raise Exception('When using TensorFlow, you should define '
                                'explicitly the number of timesteps of '
                                'your sequences.\n'
                                'If your first layer is an Embedding, '
                                'make sure to pass it an "input_length" '
                                'argument. Otherwise, make sure '
                                'the first layer has '
                                'an "input_shape" or "batch_input_shape" '
                                'argument, including the time axis. '
                                'Found input shape at layer ' + self.name +
                                ': ' + str(input_shape))
        if self.stateful:
            initial_states = self.states
        else:
            initial_states = self.get_initial_states(x)
        constants = self.get_constants(x)
        preprocessed_input = self.preprocess_input(x)

        last_output, outputs, states = K.rnn(self.step, preprocessed_input,
                                             initial_states,
                                             go_backwards=self.go_backwards,
                                             mask=mask,
                                             constants=constants,
                                             unroll=self.unroll,
                                             input_length=input_shape[1])
        if self.stateful:
            self.updates = []
            for i in range(len(states)):
                self.updates.append((self.states[i], states[i]))

        if self.return_sequences:
            return outputs
        else:
            return last_output

    def get_config(self):
        config = {'return_sequences': self.return_sequences,
                  'go_backwards': self.go_backwards,
                  'stateful': self.stateful,
                  'unroll': self.unroll,
                  'consume_less': self.consume_less}
        if self.stateful:
            config['batch_input_shape'] = self.input_spec[0].shape
        else:
            config['input_dim'] = self.input_dim
            config['input_length'] = self.input_length

        base_config = super(Recurrent, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class SimpleRNN(Recurrent):
    '''Fully-connected RNN where the output is to be fed back to input.

    # Arguments
        output_dim: dimension of the internal projections and the final output.
        init: weight initialization function.
            Can be the name of an existing function (str),
            or a Theano function (see: [initializations](../initializations.md)).
        inner_init: initialization function of the inner cells.
        activation: activation function.
            Can be the name of an existing function (str),
            or a Theano function (see: [activations](../activations.md)).
        W_regularizer: instance of [WeightRegularizer](../regularizers.md)
            (eg. L1 or L2 regularization), applied to the input weights matrices.
        U_regularizer: instance of [WeightRegularizer](../regularizers.md)
            (eg. L1 or L2 regularization), applied to the recurrent weights matrices.
        b_regularizer: instance of [WeightRegularizer](../regularizers.md),
            applied to the bias.
        dropout_W: float between 0 and 1. Fraction of the input units to drop for input gates.
        dropout_U: float between 0 and 1. Fraction of the input units to drop for recurrent connections.

    # References
        - [A Theoretically Grounded Application of Dropout in Recurrent Neural Networks](http://arxiv.org/abs/1512.05287)
    '''
    def __init__(self, output_dim,
                 init='glorot_uniform', inner_init='orthogonal',
                 activation='tanh',
                 W_regularizer=None, U_regularizer=None, b_regularizer=None,
                 dropout_W=0., dropout_U=0., **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.activation = activations.get(activation)
        self.W_regularizer = regularizers.get(W_regularizer)
        self.U_regularizer = regularizers.get(U_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.dropout_W, self.dropout_U = dropout_W, dropout_U

        if self.dropout_W or self.dropout_U:
            self.uses_learning_phase = True
        super(SimpleRNN, self).__init__(**kwargs)

    def build(self, input_shape):
        self.input_spec = [InputSpec(shape=input_shape)]
        if self.stateful:
            self.reset_states()
        else:
            # initial states: all-zero tensor of shape (output_dim)
            self.states = [None]
        input_dim = input_shape[2]
        self.input_dim = input_dim

        self.W = self.init((input_dim, self.output_dim),
                           name='{}_W'.format(self.name))
        self.U = self.inner_init((self.output_dim, self.output_dim),
                                 name='{}_U'.format(self.name))
        self.b = K.zeros((self.output_dim,), name='{}_b'.format(self.name))

        self.regularizers = []
        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)
        if self.U_regularizer:
            self.U_regularizer.set_param(self.U)
            self.regularizers.append(self.U_regularizer)
        if self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        self.trainable_weights = [self.W, self.U, self.b]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def reset_states(self):
        assert self.stateful, 'Layer must be stateful.'
        input_shape = self.input_spec[0].shape
        if not input_shape[0]:
            raise Exception('If a RNN is stateful, a complete ' +
                            'input_shape must be provided (including batch size).')
        if hasattr(self, 'states'):
            K.set_value(self.states[0],
                        np.zeros((input_shape[0], self.output_dim)))
        else:
            self.states = [K.zeros((input_shape[0], self.output_dim))]

    def preprocess_input(self, x):
        if self.consume_less == 'cpu':
            input_shape = self.input_spec[0].shape
            input_dim = input_shape[2]
            timesteps = input_shape[1]
            return time_distributed_dense(x, self.W, self.b, self.dropout_W,
                                          input_dim, self.output_dim,
                                          timesteps)
        else:
            return x

    def step(self, x, states):
        prev_output = states[0]
        B_U = states[1]
        B_W = states[2]

        if self.consume_less == 'cpu':
            h = x
        else:
            h = K.dot(x * B_W, self.W) + self.b

        output = self.activation(h + K.dot(prev_output * B_U, self.U))
        return output, [output]

    def get_constants(self, x):
        constants = []
        if 0 < self.dropout_U < 1:
            ones = K.ones_like(K.reshape(x[:, 0, 0], (-1, 1)))
            ones = K.concatenate([ones] * self.output_dim, 1)
            B_U = K.in_train_phase(K.dropout(ones, self.dropout_U), ones)
            constants.append(B_U)
        else:
            constants.append(K.cast_to_floatx(1.))
        if self.consume_less == 'cpu' and 0 < self.dropout_W < 1:
            input_shape = self.input_spec[0].shape
            input_dim = input_shape[-1]
            ones = K.ones_like(K.reshape(x[:, 0, 0], (-1, 1)))
            ones = K.concatenate([ones] * input_dim, 1)
            B_W = K.in_train_phase(K.dropout(ones, self.dropout_W), ones)
            constants.append(B_W)
        else:
            constants.append(K.cast_to_floatx(1.))
        return constants

    def get_config(self):
        config = {'output_dim': self.output_dim,
                  'init': self.init.__name__,
                  'inner_init': self.inner_init.__name__,
                  'activation': self.activation.__name__,
                  'W_regularizer': self.W_regularizer.get_config() if self.W_regularizer else None,
                  'U_regularizer': self.U_regularizer.get_config() if self.U_regularizer else None,
                  'b_regularizer': self.b_regularizer.get_config() if self.b_regularizer else None,
                  'dropout_W': self.dropout_W,
                  'dropout_U': self.dropout_U}
        base_config = super(SimpleRNN, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class GRU(Recurrent):
    '''Gated Recurrent Unit - Cho et al. 2014.

    # Arguments
        output_dim: dimension of the internal projections and the final output.
        init: weight initialization function.
            Can be the name of an existing function (str),
            or a Theano function (see: [initializations](../initializations.md)).
        inner_init: initialization function of the inner cells.
        activation: activation function.
            Can be the name of an existing function (str),
            or a Theano function (see: [activations](../activations.md)).
        inner_activation: activation function for the inner cells.
        W_regularizer: instance of [WeightRegularizer](../regularizers.md)
            (eg. L1 or L2 regularization), applied to the input weights matrices.
        U_regularizer: instance of [WeightRegularizer](../regularizers.md)
            (eg. L1 or L2 regularization), applied to the recurrent weights matrices.
        b_regularizer: instance of [WeightRegularizer](../regularizers.md),
            applied to the bias.
        dropout_W: float between 0 and 1. Fraction of the input units to drop for input gates.
        dropout_U: float between 0 and 1. Fraction of the input units to drop for recurrent connections.

    # References
        - [On the Properties of Neural Machine Translation: Encoderâ€“Decoder Approaches](http://www.aclweb.org/anthology/W14-4012)
        - [Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling](http://arxiv.org/pdf/1412.3555v1.pdf)
        - [A Theoretically Grounded Application of Dropout in Recurrent Neural Networks](http://arxiv.org/abs/1512.05287)
    '''
    def __init__(self, output_dim,
                 init='glorot_uniform', inner_init='orthogonal',
                 activation='tanh', inner_activation='hard_sigmoid',
                 W_regularizer=None, U_regularizer=None, b_regularizer=None,
                 dropout_W=0., dropout_U=0., **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.activation = activations.get(activation)
        self.inner_activation = activations.get(inner_activation)
        self.W_regularizer = regularizers.get(W_regularizer)
        self.U_regularizer = regularizers.get(U_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.dropout_W, self.dropout_U = dropout_W, dropout_U

        if self.dropout_W or self.dropout_U:
            self.uses_learning_phase = True
        super(GRU, self).__init__(**kwargs)

    def build(self, input_shape):
        self.input_spec = [InputSpec(shape=input_shape)]
        input_dim = input_shape[2]
        self.input_dim = input_dim

        self.W_z = self.init((input_dim, self.output_dim),
                             name='{}_W_z'.format(self.name))
        self.U_z = self.inner_init((self.output_dim, self.output_dim),
                                   name='{}_U_z'.format(self.name))
        self.b_z = K.zeros((self.output_dim,), name='{}_b_z'.format(self.name))

        self.W_r = self.init((input_dim, self.output_dim),
                             name='{}_W_r'.format(self.name))
        self.U_r = self.inner_init((self.output_dim, self.output_dim),
                                   name='{}_U_r'.format(self.name))
        self.b_r = K.zeros((self.output_dim,), name='{}_b_r'.format(self.name))

        self.W_h = self.init((input_dim, self.output_dim),
                             name='{}_W_h'.format(self.name))
        self.U_h = self.inner_init((self.output_dim, self.output_dim),
                                   name='{}_U_h'.format(self.name))
        self.b_h = K.zeros((self.output_dim,), name='{}_b_h'.format(self.name))

        self.regularizers = []
        if self.W_regularizer:
            self.W_regularizer.set_param(K.concatenate([self.W_z,
                                                        self.W_r,
                                                        self.W_h]))
            self.regularizers.append(self.W_regularizer)
        if self.U_regularizer:
            self.U_regularizer.set_param(K.concatenate([self.U_z,
                                                        self.U_r,
                                                        self.U_h]))
            self.regularizers.append(self.U_regularizer)
        if self.b_regularizer:
            self.b_regularizer.set_param(K.concatenate([self.b_z,
                                                        self.b_r,
                                                        self.b_h]))
            self.regularizers.append(self.b_regularizer)

        self.trainable_weights = [self.W_z, self.U_z, self.b_z,
                                  self.W_r, self.U_r, self.b_r,
                                  self.W_h, self.U_h, self.b_h]
        if self.stateful:
            self.reset_states()
        else:
            # initial states: all-zero tensor of shape (output_dim)
            self.states = [None]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def reset_states(self):
        assert self.stateful, 'Layer must be stateful.'
        input_shape = self.input_spec[0].shape
        if not input_shape[0]:
            raise Exception('If a RNN is stateful, a complete ' +
                            'input_shape must be provided (including batch size).')
        if hasattr(self, 'states'):
            K.set_value(self.states[0],
                        np.zeros((input_shape[0], self.output_dim)))
        else:
            self.states = [K.zeros((input_shape[0], self.output_dim))]

    def preprocess_input(self, x):
        if self.consume_less == 'cpu':
            input_shape = self.input_spec[0].shape
            input_dim = input_shape[2]
            timesteps = input_shape[1]

            x_z = time_distributed_dense(x, self.W_z, self.b_z, self.dropout_W,
                                         input_dim, self.output_dim, timesteps)
            x_r = time_distributed_dense(x, self.W_r, self.b_r, self.dropout_W,
                                         input_dim, self.output_dim, timesteps)
            x_h = time_distributed_dense(x, self.W_h, self.b_h, self.dropout_W,
                                         input_dim, self.output_dim, timesteps)
            return K.concatenate([x_z, x_r, x_h], axis=2)
        else:
            return x

    def step(self, x, states):
        h_tm1 = states[0]  # previous memory
        B_U = states[1]  # dropout matrices for recurrent units
        B_W = states[2]

        if self.consume_less == 'cpu':
            x_z = x[:, :self.output_dim]
            x_r = x[:, self.output_dim: 2 * self.output_dim]
            x_h = x[:, 2 * self.output_dim:]
        else:
            x_z = K.dot(x * B_W[0], self.W_z) + self.b_z
            x_r = K.dot(x * B_W[1], self.W_r) + self.b_r
            x_h = K.dot(x * B_W[2], self.W_h) + self.b_h

        z = self.inner_activation(x_z + K.dot(h_tm1 * B_U[0], self.U_z))
        r = self.inner_activation(x_r + K.dot(h_tm1 * B_U[1], self.U_r))

        hh = self.activation(x_h + K.dot(r * h_tm1 * B_U[2], self.U_h))
        h = z * h_tm1 + (1 - z) * hh
        return h, [h]

    def get_constants(self, x):
        constants = []
        if 0 < self.dropout_U < 1:
            ones = K.ones_like(K.reshape(x[:, 0, 0], (-1, 1)))
            ones = K.concatenate([ones] * self.output_dim, 1)
            B_U = [K.in_train_phase(K.dropout(ones, self.dropout_U), ones) for _ in range(3)]
            constants.append(B_U)
        else:
            constants.append([K.cast_to_floatx(1.) for _ in range(3)])

        if 0 < self.dropout_W < 1:
            input_shape = self.input_spec[0].shape
            input_dim = input_shape[-1]
            ones = K.ones_like(K.reshape(x[:, 0, 0], (-1, 1)))
            ones = K.concatenate([ones] * input_dim, 1)
            B_W = [K.in_train_phase(K.dropout(ones, self.dropout_W), ones) for _ in range(3)]
            constants.append(B_W)
        else:
            constants.append([K.cast_to_floatx(1.) for _ in range(3)])
        return constants

    def get_config(self):
        config = {'output_dim': self.output_dim,
                  'init': self.init.__name__,
                  'inner_init': self.inner_init.__name__,
                  'activation': self.activation.__name__,
                  'inner_activation': self.inner_activation.__name__,
                  'W_regularizer': self.W_regularizer.get_config() if self.W_regularizer else None,
                  'U_regularizer': self.U_regularizer.get_config() if self.U_regularizer else None,
                  'b_regularizer': self.b_regularizer.get_config() if self.b_regularizer else None,
                  'dropout_W': self.dropout_W,
                  'dropout_U': self.dropout_U}
        base_config = super(GRU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class LSTM(Recurrent):
    '''Long-Short Term Memory unit - Hochreiter 1997.

    For a step-by-step description of the algorithm, see
    [this tutorial](http://deeplearning.net/tutorial/lstm.html).

    # Arguments
        output_dim: dimension of the internal projections and the final output.
        init: weight initialization function.
            Can be the name of an existing function (str),
            or a Theano function (see: [initializations](../initializations.md)).
        inner_init: initialization function of the inner cells.
        forget_bias_init: initialization function for the bias of the forget gate.
            [Jozefowicz et al.](http://www.jmlr.org/proceedings/papers/v37/jozefowicz15.pdf)
            recommend initializing with ones.
        activation: activation function.
            Can be the name of an existing function (str),
            or a Theano function (see: [activations](../activations.md)).
        inner_activation: activation function for the inner cells.
        W_regularizer: instance of [WeightRegularizer](../regularizers.md)
            (eg. L1 or L2 regularization), applied to the input weights matrices.
        U_regularizer: instance of [WeightRegularizer](../regularizers.md)
            (eg. L1 or L2 regularization), applied to the recurrent weights matrices.
        b_regularizer: instance of [WeightRegularizer](../regularizers.md),
            applied to the bias.
        dropout_W: float between 0 and 1. Fraction of the input units to drop for input gates.
        dropout_U: float between 0 and 1. Fraction of the input units to drop for recurrent connections.

    # References
        - [Long short-term memory](http://deeplearning.cs.cmu.edu/pdfs/Hochreiter97_lstm.pdf) (original 1997 paper)
        - [Learning to forget: Continual prediction with LSTM](http://www.mitpressjournals.org/doi/pdf/10.1162/089976600300015015)
        - [Supervised sequence labelling with recurrent neural networks](http://www.cs.toronto.edu/~graves/preprint.pdf)
        - [A Theoretically Grounded Application of Dropout in Recurrent Neural Networks](http://arxiv.org/abs/1512.05287)
    '''
    def __init__(self, output_dim,
                 init='glorot_uniform', inner_init='orthogonal',
                 forget_bias_init='one', activation='tanh',
                 inner_activation='hard_sigmoid',
                 W_regularizer=None, U_regularizer=None, b_regularizer=None,
                 dropout_W=0., dropout_U=0., **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.forget_bias_init = initializations.get(forget_bias_init)
        self.activation = activations.get(activation)
        self.inner_activation = activations.get(inner_activation)
        self.W_regularizer = regularizers.get(W_regularizer)
        self.U_regularizer = regularizers.get(U_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.dropout_W, self.dropout_U = dropout_W, dropout_U

        if self.dropout_W or self.dropout_U:
            self.uses_learning_phase = True
        super(LSTM, self).__init__(**kwargs)

    def build(self, input_shape):
        self.input_spec = [InputSpec(shape=input_shape)]
        self.input_dim = input_shape[2]

        if self.stateful:
            self.reset_states()
        else:
            # initial states: 2 all-zero tensors of shape (output_dim)
            self.states = [None, None]

        if self.consume_less == 'gpu':
            self.W = self.init((self.input_dim, 4 * self.output_dim),
                               name='{}_W'.format(self.name))
            self.U = self.inner_init((self.output_dim, 4 * self.output_dim),
                                     name='{}_U'.format(self.name))

            self.b = K.variable(np.hstack((np.zeros(self.output_dim),
                                           K.get_value(self.forget_bias_init(self.output_dim)),
                                           np.zeros(self.output_dim),
                                           np.zeros(self.output_dim))),
                                name='{}_b'.format(self.name))
            self.trainable_weights = [self.W, self.U, self.b]
        else:
            self.W_i = self.init((self.input_dim, self.output_dim),
                                 name='{}_W_i'.format(self.name))
            self.U_i = self.inner_init((self.output_dim, self.output_dim),
                                       name='{}_U_i'.format(self.name))
            self.b_i = K.zeros((self.output_dim,), name='{}_b_i'.format(self.name))

            self.W_f = self.init((self.input_dim, self.output_dim),
                                 name='{}_W_f'.format(self.name))
            self.U_f = self.inner_init((self.output_dim, self.output_dim),
                                       name='{}_U_f'.format(self.name))
            self.b_f = self.forget_bias_init((self.output_dim,),
                                             name='{}_b_f'.format(self.name))

            self.W_c = self.init((self.input_dim, self.output_dim),
                                 name='{}_W_c'.format(self.name))
            self.U_c = self.inner_init((self.output_dim, self.output_dim),
                                       name='{}_U_c'.format(self.name))
            self.b_c = K.zeros((self.output_dim,), name='{}_b_c'.format(self.name))

            self.W_o = self.init((self.input_dim, self.output_dim),
                                 name='{}_W_o'.format(self.name))
            self.U_o = self.inner_init((self.output_dim, self.output_dim),
                                       name='{}_U_o'.format(self.name))
            self.b_o = K.zeros((self.output_dim,), name='{}_b_o'.format(self.name))

            self.trainable_weights = [self.W_i, self.U_i, self.b_i,
                                      self.W_c, self.U_c, self.b_c,
                                      self.W_f, self.U_f, self.b_f,
                                      self.W_o, self.U_o, self.b_o]

            self.W = K.concatenate([self.W_i, self.W_f, self.W_c, self.W_o])
            self.U = K.concatenate([self.U_i, self.U_f, self.U_c, self.U_o])
            self.b = K.concatenate([self.b_i, self.b_f, self.b_c, self.b_o])

        self.regularizers = []
        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)
        if self.U_regularizer:
            self.U_regularizer.set_param(self.U)
            self.regularizers.append(self.U_regularizer)
        if self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def reset_states(self):
        assert self.stateful, 'Layer must be stateful.'
        input_shape = self.input_spec[0].shape
        if not input_shape[0]:
            raise Exception('If a RNN is stateful, a complete ' +
                            'input_shape must be provided (including batch size).')
        if hasattr(self, 'states'):
            K.set_value(self.states[0],
                        np.zeros((input_shape[0], self.output_dim)))
            K.set_value(self.states[1],
                        np.zeros((input_shape[0], self.output_dim)))
        else:
            self.states = [K.zeros((input_shape[0], self.output_dim)),
                           K.zeros((input_shape[0], self.output_dim))]

    def preprocess_input(self, x):
        if self.consume_less == 'cpu':
            if 0 < self.dropout_W < 1:
                dropout = self.dropout_W
            else:
                dropout = 0
            input_shape = self.input_spec[0].shape
            input_dim = input_shape[2]
            timesteps = input_shape[1]

            x_i = time_distributed_dense(x, self.W_i, self.b_i, dropout,
                                         input_dim, self.output_dim, timesteps)
            x_f = time_distributed_dense(x, self.W_f, self.b_f, dropout,
                                         input_dim, self.output_dim, timesteps)
            x_c = time_distributed_dense(x, self.W_c, self.b_c, dropout,
                                         input_dim, self.output_dim, timesteps)
            x_o = time_distributed_dense(x, self.W_o, self.b_o, dropout,
                                         input_dim, self.output_dim, timesteps)
            return K.concatenate([x_i, x_f, x_c, x_o], axis=2)
        else:
            return x

    def step(self, x, states):
        h_tm1 = states[0]
        c_tm1 = states[1]
        B_U = states[2]
        B_W = states[3]

        if self.consume_less == 'gpu':
            z = K.dot(x * B_W[0], self.W) + K.dot(h_tm1 * B_U[0], self.U) + self.b

            z0 = z[:, :self.output_dim]
            z1 = z[:, self.output_dim: 2 * self.output_dim]
            z2 = z[:, 2 * self.output_dim: 3 * self.output_dim]
            z3 = z[:, 3 * self.output_dim:]

            i = self.inner_activation(z0)
            f = self.inner_activation(z1)
            c = f * c_tm1 + i * self.activation(z2)
            o = self.inner_activation(z3)
        else:
            if self.consume_less == 'cpu':
                x_i = x[:, :self.output_dim]
                x_f = x[:, self.output_dim: 2 * self.output_dim]
                x_c = x[:, 2 * self.output_dim: 3 * self.output_dim]
                x_o = x[:, 3 * self.output_dim:]
            elif self.consume_less == 'mem':
                x_i = K.dot(x * B_W[0], self.W_i) + self.b_i
                x_f = K.dot(x * B_W[1], self.W_f) + self.b_f
                x_c = K.dot(x * B_W[2], self.W_c) + self.b_c
                x_o = K.dot(x * B_W[3], self.W_o) + self.b_o
            else:
                raise Exception('Unknown `consume_less` mode.')

            i = self.inner_activation(x_i + K.dot(h_tm1 * B_U[0], self.U_i))
            f = self.inner_activation(x_f + K.dot(h_tm1 * B_U[1], self.U_f))
            c = f * c_tm1 + i * self.activation(x_c + K.dot(h_tm1 * B_U[2], self.U_c))
            o = self.inner_activation(x_o + K.dot(h_tm1 * B_U[3], self.U_o))

        h = o * self.activation(c)
        return h, [h, c]

    def get_constants(self, x):
        constants = []
        if 0 < self.dropout_U < 1:
            ones = K.ones_like(K.reshape(x[:, 0, 0], (-1, 1)))
            ones = K.concatenate([ones] * self.output_dim, 1)
            B_U = [K.in_train_phase(K.dropout(ones, self.dropout_U), ones) for _ in range(4)]
            constants.append(B_U)
        else:
            constants.append([K.cast_to_floatx(1.) for _ in range(4)])

        if 0 < self.dropout_W < 1:
            input_shape = self.input_spec[0].shape
            input_dim = input_shape[-1]
            ones = K.ones_like(K.reshape(x[:, 0, 0], (-1, 1)))
            ones = K.concatenate([ones] * input_dim, 1)
            B_W = [K.in_train_phase(K.dropout(ones, self.dropout_W), ones) for _ in range(4)]
            constants.append(B_W)
        else:
            constants.append([K.cast_to_floatx(1.) for _ in range(4)])
        return constants

    def get_config(self):
        config = {'output_dim': self.output_dim,
                  'init': self.init.__name__,
                  'inner_init': self.inner_init.__name__,
                  'forget_bias_init': self.forget_bias_init.__name__,
                  'activation': self.activation.__name__,
                  'inner_activation': self.inner_activation.__name__,
                  'W_regularizer': self.W_regularizer.get_config() if self.W_regularizer else None,
                  'U_regularizer': self.U_regularizer.get_config() if self.U_regularizer else None,
                  'b_regularizer': self.b_regularizer.get_config() if self.b_regularizer else None,
                  'dropout_W': self.dropout_W,
                  'dropout_U': self.dropout_U}
        base_config = super(LSTM, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

from __future__ import absolute_import
from ..engine import Layer, Input, InputLayer, Merge, merge, InputSpec
from .core import *
from .convolutional import *
from .recurrent import *
from .normalization import *
from .embeddings import *
from .noise import *
from .advanced_activations import *
from .wrappers import *

# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division

import numpy as np

import copy
import inspect
import types as python_types
import marshal
import sys
import warnings

from .. import backend as K
from .. import activations, initializations, regularizers, constraints
from ..engine import InputSpec, Layer, Merge
from ..regularizers import ActivityRegularizer


class Masking(Layer):
    '''Masks an input sequence by using a mask value to
    identify timesteps to be skipped.

    For each timestep in the input tensor (dimension #1 in the tensor),
    if all values in the input tensor at that timestep
    are equal to `mask_value`, then the timestep will masked (skipped)
    in all downstream layers (as long as they support masking).

    If any downstream layer does not support masking yet receives such
    an input mask, an exception will be raised.

    # Example

    Consider a Numpy data array `x` of shape `(samples, timesteps, features)`,
    to be fed to a LSTM layer.
    You want to mask timestep #3 and #5 because you lack data for
    these timesteps. You can:

        - set `x[:, 3, :] = 0.` and `x[:, 5, :] = 0.`
        - insert a `Masking` layer with `mask_value=0.` before the LSTM layer:

    ```python
        model = Sequential()
        model.add(Masking(mask_value=0., input_shape=(timesteps, features)))
        model.add(LSTM(32))
    ```
    '''
    def __init__(self, mask_value=0., **kwargs):
        self.supports_masking = True
        self.mask_value = mask_value
        super(Masking, self).__init__(**kwargs)

    def compute_mask(self, input, input_mask=None):
        return K.any(K.not_equal(input, self.mask_value), axis=-1)

    def call(self, x, mask=None):
        boolean_mask = K.any(K.not_equal(x, self.mask_value),
                             axis=-1, keepdims=True)
        return x * K.cast(boolean_mask, K.floatx())

    def get_config(self):
        config = {'mask_value': self.mask_value}
        base_config = super(Masking, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Dropout(Layer):
    '''Applies Dropout to the input. Dropout consists in randomly setting
    a fraction `p` of input units to 0 at each update during training time,
    which helps prevent overfitting.

    # Arguments
        p: float between 0 and 1. Fraction of the input units to drop.

    # References
        - [Dropout: A Simple Way to Prevent Neural Networks from Overfitting](http://www.cs.toronto.edu/~rsalakhu/papers/srivastava14a.pdf)
    '''
    def __init__(self, p, **kwargs):
        self.p = p
        if 0. < self.p < 1.:
            self.uses_learning_phase = True
        self.supports_masking = True
        super(Dropout, self).__init__(**kwargs)

    def call(self, x, mask=None):
        if 0. < self.p < 1.:
            x = K.in_train_phase(K.dropout(x, level=self.p), x)
        return x

    def get_config(self):
        config = {'p': self.p}
        base_config = super(Dropout, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Activation(Layer):
    '''Applies an activation function to an output.

    # Arguments
        activation: name of activation function to use
            (see: [activations](../activations.md)),
            or alternatively, a Theano or TensorFlow operation.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as input.
    '''
    def __init__(self, activation, **kwargs):
        self.supports_masking = True
        self.activation = activations.get(activation)
        super(Activation, self).__init__(**kwargs)

    def call(self, x, mask=None):
        return self.activation(x)

    def get_config(self):
        config = {'activation': self.activation.__name__}
        base_config = super(Activation, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Reshape(Layer):
    '''Reshapes an output to a certain shape.

    # Arguments
        target_shape: target shape. Tuple of integers,
            does not include the samples dimension (batch size).

    # Input shape
        Arbitrary, although all dimensions in the input shaped must be fixed.
        Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        `(batch_size,) + target_shape`

    # Example

    ```python
        # as first layer in a Sequential model
        model = Sequential()
        model.add(Reshape((3, 4), input_shape=(12,)))
        # now: model.output_shape == (None, 3, 4)
        # note: `None` is the batch dimension

        # as intermediate layer in a Sequential model
        model.add(Reshape((6, 2)))
        # now: model.output_shape == (None, 6, 2)
    ```
    '''
    def __init__(self, target_shape, **kwargs):
        super(Reshape, self).__init__(**kwargs)
        self.target_shape = tuple(target_shape)

    def _fix_unknown_dimension(self, input_shape, output_shape):
        '''Find and replace a single missing dimension in an output shape
        given an input shape.

        A near direct port of the internal numpy function _fix_unknown_dimension
        in numpy/core/src/multiarray/shape.c

        # Arguments
            input_shape: shape of array being reshaped

            output_shape: desired shape of the array with at most
                a single -1 which indicates a dimension that should be
                derived from the input shape.

        # Returns
            The new output shape with a -1 replaced with its computed value.

            Raises a ValueError if the total array size of the output_shape is
            different then the input_shape, or more then one unknown dimension
            is specified.
        '''
        output_shape = list(output_shape)

        msg = 'total size of new array must be unchanged'

        known, unknown = 1, None
        for index, dim in enumerate(output_shape):
            if dim < 0:
                if unknown is None:
                    unknown = index
                else:
                    raise ValueError('can only specify one unknown dimension')
            else:
                known *= dim

        original = np.prod(input_shape, dtype=int)
        if unknown is not None:
            if known == 0 or original % known != 0:
                raise ValueError(msg)
            output_shape[unknown] = original // known
        elif original != known:
            raise ValueError(msg)

        return tuple(output_shape)

    def get_output_shape_for(self, input_shape):
        return (input_shape[0],) + self._fix_unknown_dimension(input_shape[1:], self.target_shape)

    def call(self, x, mask=None):
        # In case the target shape is not fully defined,
        # we need access to the shape of x.
        # solution:
        # 1) rely on x._keras_shape
        # 2) fallback: K.int_shape
        target_shape = self.target_shape
        if -1 in target_shape:
            # target shape not fully defined
            input_shape = None
            if hasattr(x, '_keras_shape'):
                input_shape = x._keras_shape
            elif hasattr(K, 'int_shape'):
                input_shape = K.int_shape(x)
            if input_shape is not None:
                target_shape = self.get_output_shape_for(input_shape)
        return K.reshape(x, (-1,) + target_shape)

    def get_config(self):
        config = {'target_shape': self.target_shape}
        base_config = super(Reshape, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Permute(Layer):
    '''Permutes the dimensions of the input according to a given pattern.

    Useful for e.g. connecting RNNs and convnets together.

    # Example

    ```python
        model = Sequential()
        model.add(Permute((2, 1), input_shape=(10, 64)))
        # now: model.output_shape == (None, 64, 10)
        # note: `None` is the batch dimension
    ```

    # Arguments
        dims: Tuple of integers. Permutation pattern, does not include the
            samples dimension. Indexing starts at 1.
            For instance, `(2, 1)` permutes the first and second dimension
            of the input.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same as the input shape, but with the dimensions re-ordered according
        to the specified pattern.
    '''
    def __init__(self, dims, **kwargs):
        self.dims = tuple(dims)
        super(Permute, self).__init__(**kwargs)

    def get_output_shape_for(self, input_shape):
        input_shape = list(input_shape)
        output_shape = copy.copy(input_shape)
        for i, dim in enumerate(self.dims):
            target_dim = input_shape[dim]
            output_shape[i+1] = target_dim
        return tuple(output_shape)

    def call(self, x, mask=None):
        return K.permute_dimensions(x, (0,) + self.dims)

    def get_config(self):
        config = {'dims': self.dims}
        base_config = super(Permute, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Flatten(Layer):
    '''Flattens the input. Does not affect the batch size.

    # Example

    ```python
        model = Sequential()
        model.add(Convolution2D(64, 3, 3, border_mode='same', input_shape=(3, 32, 32)))
        # now: model.output_shape == (None, 64, 32, 32)

        model.add(Flatten())
        # now: model.output_shape == (None, 65536)
    ```
    '''
    def __init__(self, **kwargs):
        self.input_spec = [InputSpec(ndim='3+')]
        super(Flatten, self).__init__(**kwargs)

    def get_output_shape_for(self, input_shape):
        if not all(input_shape[1:]):
            raise Exception('The shape of the input to "Flatten" '
                            'is not fully defined '
                            '(got ' + str(input_shape[1:]) + '. '
                            'Make sure to pass a complete "input_shape" '
                            'or "batch_input_shape" argument to the first '
                            'layer in your model.')
        return (input_shape[0], np.prod(input_shape[1:]))

    def call(self, x, mask=None):
        return K.batch_flatten(x)


class RepeatVector(Layer):
    '''Repeats the input n times.

    # Example

    ```python
        model = Sequential()
        model.add(Dense(32, input_dim=32))
        # now: model.output_shape == (None, 32)
        # note: `None` is the batch dimension

        model.add(RepeatVector(3))
        # now: model.output_shape == (None, 3, 32)
    ```

    # Arguments
        n: integer, repetition factor.

    # Input shape
        2D tensor of shape `(nb_samples, features)`.

    # Output shape
        3D tensor of shape `(nb_samples, n, features)`.
    '''
    def __init__(self, n, **kwargs):
        self.n = n
        self.input_spec = [InputSpec(ndim=2)]
        super(RepeatVector, self).__init__(**kwargs)

    def get_output_shape_for(self, input_shape):
        return (input_shape[0], self.n, input_shape[1])

    def call(self, x, mask=None):
        return K.repeat(x, self.n)

    def get_config(self):
        config = {'n': self.n}
        base_config = super(RepeatVector, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Lambda(Layer):
    '''Used for evaluating an arbitrary Theano / TensorFlow expression
    on the output of the previous layer.

    # Examples

    ```python
        # add a x -> x^2 layer
        model.add(Lambda(lambda x: x ** 2))
    ```
    ```python
        # add a layer that returns the concatenation
        # of the positive part of the input and
        # the opposite of the negative part

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

        model.add(Lambda(antirectifier, output_shape=antirectifier_output_shape))
    ```

    # Arguments
        function: The function to be evaluated.
            Takes one argument: the output of previous layer
        output_shape: Expected output shape from function.
            Could be a tuple or a function of the shape of the input
        arguments: optional dictionary of keyword arguments to be passed
            to the function.

    # Input shape
        Arbitrary. Use the keyword argument input_shape
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Specified by `output_shape` argument.
    '''
    def __init__(self, function, output_shape=None, arguments={}, **kwargs):
        self.function = function
        self.arguments = arguments
        if output_shape is None:
            self._output_shape = None
        elif type(output_shape) in {tuple, list}:
            self._output_shape = tuple(output_shape)
        else:
            if not hasattr(output_shape, '__call__'):
                raise Exception('In Lambda, `output_shape` '
                                'must be a list, a tuple, or a function.')
            self._output_shape = output_shape
        super(Lambda, self).__init__(**kwargs)

    def get_output_shape_for(self, input_shape):
        if self._output_shape is None:
            # if TensorFlow, we can infer the output shape directly:
            if K._BACKEND == 'tensorflow':
                if type(input_shape) is list:
                    xs = [K.placeholder(shape=shape) for shape in input_shape]
                    x = self.call(xs)
                else:
                    x = K.placeholder(shape=input_shape)
                    x = self.call(x)
                if type(x) is list:
                    return [K.int_shape(x_elem) for x_elem in x]
                else:
                    return K.int_shape(x)
            # otherwise, we default to the input shape
            return input_shape
        elif type(self._output_shape) in {tuple, list}:
            nb_samples = input_shape[0] if input_shape else None
            return (nb_samples,) + tuple(self._output_shape)
        else:
            shape = self._output_shape(input_shape)
            if type(shape) not in {list, tuple}:
                raise Exception('output_shape function must return a tuple')
            return tuple(shape)

    def call(self, x, mask=None):
        arguments = self.arguments
        arg_spec = inspect.getargspec(self.function)
        if 'mask' in arg_spec.args:
            arguments['mask'] = mask
        return self.function(x, **arguments)

    def get_config(self):
        py3 = sys.version_info[0] == 3

        if isinstance(self.function, python_types.LambdaType):
            if py3:
                function = marshal.dumps(self.function.__code__).decode('raw_unicode_escape')
            else:
                function = marshal.dumps(self.function.func_code).decode('raw_unicode_escape')
            function_type = 'lambda'
        else:
            function = self.function.__name__
            function_type = 'function'

        if isinstance(self._output_shape, python_types.LambdaType):
            if py3:
                output_shape = marshal.dumps(self._output_shape.__code__)
            else:
                output_shape = marshal.dumps(self._output_shape.func_code)
            output_shape_type = 'lambda'
        elif callable(self._output_shape):
            output_shape = self._output_shape.__name__
            output_shape_type = 'function'
        else:
            output_shape = self._output_shape
            output_shape_type = 'raw'

        config = {'function': function,
                  'function_type': function_type,
                  'output_shape': output_shape,
                  'output_shape_type': output_shape_type,
                  'arguments': self.arguments}
        base_config = super(Lambda, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

    @classmethod
    def from_config(cls, config):
        function_type = config.pop('function_type')
        if function_type == 'function':
            function = globals()[config['function']]
        elif function_type == 'lambda':
            function = marshal.loads(config['function'].encode('raw_unicode_escape'))
            function = python_types.FunctionType(function, globals())
        else:
            raise Exception('Unknown function type: ' + function_type)

        output_shape_type = config.pop('output_shape_type')
        if output_shape_type == 'function':
            output_shape = globals()[config['output_shape']]
        elif output_shape_type == 'lambda':
            output_shape = marshal.loads(config['output_shape'])
            output_shape = python_types.FunctionType(output_shape, globals())
        else:
            output_shape = config['output_shape']

        config['function'] = function
        config['output_shape'] = output_shape
        return cls(**config)


class Dense(Layer):
    '''Just your regular fully connected NN layer.

    # Example

    ```python
        # as first layer in a sequential model:
        model = Sequential()
        model.add(Dense(32, input_dim=16))
        # now the model will take as input arrays of shape (*, 16)
        # and output arrays of shape (*, 32)

        # this is equivalent to the above:
        model = Sequential()
        model.add(Dense(32, input_shape=(16,)))

        # after the first layer, you don't need to specify
        # the size of the input anymore:
        model.add(Dense(32))
    ```

    # Arguments
        output_dim: int > 0.
        init: name of initialization function for the weights of the layer
            (see [initializations](../initializations.md)),
            or alternatively, Theano function to use for weights
            initialization. This parameter is only relevant
            if you don't pass a `weights` argument.
        activation: name of activation function to use
            (see [activations](../activations.md)),
            or alternatively, elementwise Theano function.
            If you don't specify anything, no activation is applied
            (ie. "linear" activation: a(x) = x).
        weights: list of numpy arrays to set as initial weights.
            The list should have 2 elements, of shape `(input_dim, output_dim)`
            and (output_dim,) for weights and biases respectively.
        W_regularizer: instance of [WeightRegularizer](../regularizers.md)
            (eg. L1 or L2 regularization), applied to the main weights matrix.
        b_regularizer: instance of [WeightRegularizer](../regularizers.md),
            applied to the bias.
        activity_regularizer: instance of [ActivityRegularizer](../regularizers.md),
            applied to the network output.
        W_constraint: instance of the [constraints](../constraints.md) module
            (eg. maxnorm, nonneg), applied to the main weights matrix.
        b_constraint: instance of the [constraints](../constraints.md) module,
            applied to the bias.
        bias: whether to include a bias (i.e. make the layer affine rather than linear).
        input_dim: dimensionality of the input (integer).
            This argument (or alternatively, the keyword argument `input_shape`)
            is required when using this layer as the first layer in a model.

    # Input shape
        2D tensor with shape: `(nb_samples, input_dim)`.

    # Output shape
        2D tensor with shape: `(nb_samples, output_dim)`.
    '''
    def __init__(self, output_dim, init='glorot_uniform', activation='linear', weights=None,
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None,
                 bias=True, input_dim=None, **kwargs):
        self.init = initializations.get(init)
        self.activation = activations.get(activation)
        self.output_dim = output_dim
        self.input_dim = input_dim

        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)

        self.bias = bias
        self.initial_weights = weights
        self.input_spec = [InputSpec(ndim=2)]

        if self.input_dim:
            kwargs['input_shape'] = (self.input_dim,)
        super(Dense, self).__init__(**kwargs)

    def build(self, input_shape):
        assert len(input_shape) == 2
        input_dim = input_shape[1]
        self.input_spec = [InputSpec(dtype=K.floatx(),
                                     shape=(None, input_dim))]

        self.W = self.init((input_dim, self.output_dim),
                           name='{}_W'.format(self.name))
        if self.bias:
            self.b = K.zeros((self.output_dim,),
                             name='{}_b'.format(self.name))
            self.trainable_weights = [self.W, self.b]
        else:
            self.trainable_weights = [self.W]

        self.regularizers = []
        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.bias and self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        self.constraints = {}
        if self.W_constraint:
            self.constraints[self.W] = self.W_constraint
        if self.bias and self.b_constraint:
            self.constraints[self.b] = self.b_constraint

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def call(self, x, mask=None):
        output = K.dot(x, self.W)
        if self.bias:
            output += self.b
        return self.activation(output)

    def get_output_shape_for(self, input_shape):
        assert input_shape and len(input_shape) == 2
        return (input_shape[0], self.output_dim)

    def get_config(self):
        config = {'output_dim': self.output_dim,
                  'init': self.init.__name__,
                  'activation': self.activation.__name__,
                  'W_regularizer': self.W_regularizer.get_config() if self.W_regularizer else None,
                  'b_regularizer': self.b_regularizer.get_config() if self.b_regularizer else None,
                  'activity_regularizer': self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  'W_constraint': self.W_constraint.get_config() if self.W_constraint else None,
                  'b_constraint': self.b_constraint.get_config() if self.b_constraint else None,
                  'bias': self.bias,
                  'input_dim': self.input_dim}
        base_config = super(Dense, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ActivityRegularization(Layer):
    '''Layer that passes through its input unchanged, but applies an update
    to the cost function based on the activity.

    # Arguments
        l1: L1 regularization factor (positive float).
        l2: L2 regularization factor (positive float).

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as input.
    '''
    def __init__(self, l1=0., l2=0., **kwargs):
        self.supports_masking = True
        self.l1 = l1
        self.l2 = l2

        activity_regularizer = ActivityRegularizer(l1=l1, l2=l2)
        activity_regularizer.set_layer(self)
        self.regularizers = [activity_regularizer]
        super(ActivityRegularization, self).__init__(**kwargs)

    def get_config(self):
        config = {'l1': self.l1,
                  'l2': self.l2}
        base_config = super(ActivityRegularization, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class MaxoutDense(Layer):
    '''A dense maxout layer.

    A `MaxoutDense` layer takes the element-wise maximum of
    `nb_feature` `Dense(input_dim, output_dim)` linear layers.
    This allows the layer to learn a convex,
    piecewise linear activation function over the inputs.

    Note that this is a *linear* layer;
    if you wish to apply activation function
    (you shouldn't need to --they are universal function approximators),
    an `Activation` layer must be added after.

    # Arguments
        output_dim: int > 0.
        nb_feature: number of Dense layers to use internally.
        init: name of initialization function for the weights of the layer
            (see [initializations](../initializations.md)),
            or alternatively, Theano function to use for weights
            initialization. This parameter is only relevant
            if you don't pass a `weights` argument.
        activation: name of activation function to use
            (see [activations](../activations.md)),
            or alternatively, elementwise Theano function.
            If you don't specify anything, no activation is applied
            (ie. "linear" activation: a(x) = x).
        weights: list of numpy arrays to set as initial weights.
            The list should have 2 elements, of shape `(input_dim, output_dim)`
            and (output_dim,) for weights and biases respectively.
        W_regularizer: instance of [WeightRegularizer](../regularizers.md)
            (eg. L1 or L2 regularization), applied to the main weights matrix.
        b_regularizer: instance of [WeightRegularizer](../regularizers.md),
            applied to the bias.
        activity_regularizer: instance of [ActivityRegularizer](../regularizers.md),
            applied to the network output.
        W_constraint: instance of the [constraints](../constraints.md) module
            (eg. maxnorm, nonneg), applied to the main weights matrix.
        b_constraint: instance of the [constraints](../constraints.md) module,
            applied to the bias.
        bias: whether to include a bias (i.e. make the layer affine rather than linear).
        input_dim: dimensionality of the input (integer).
            This argument (or alternatively, the keyword argument `input_shape`)
            is required when using this layer as the first layer in a model.

    # Input shape
        2D tensor with shape: `(nb_samples, input_dim)`.

    # Output shape
        2D tensor with shape: `(nb_samples, output_dim)`.

    # References
        - [Maxout Networks](http://arxiv.org/pdf/1302.4389.pdf)
    '''
    def __init__(self, output_dim, nb_feature=4,
                 init='glorot_uniform', weights=None,
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None,
                 bias=True, input_dim=None, **kwargs):
        self.output_dim = output_dim
        self.nb_feature = nb_feature
        self.init = initializations.get(init)

        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)

        self.bias = bias
        self.initial_weights = weights
        self.input_spec = [InputSpec(ndim=2)]

        self.input_dim = input_dim
        if self.input_dim:
            kwargs['input_shape'] = (self.input_dim,)
        super(MaxoutDense, self).__init__(**kwargs)

    def build(self, input_shape):
        input_dim = input_shape[1]
        self.input_spec = [InputSpec(dtype=K.floatx(),
                                     shape=(None, input_dim))]

        self.W = self.init((self.nb_feature, input_dim, self.output_dim),
                           name='{}_W'.format(self.name))
        if self.bias:
            self.b = K.zeros((self.nb_feature, self.output_dim),
                             name='{}_b'.format(self.name))
            self.trainable_weights = [self.W, self.b]
        else:
            self.trainable_weights = [self.W]

        self.regularizers = []
        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.bias and self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        self.constraints = {}
        if self.W_constraint:
            self.constraints[self.W] = self.W_constraint
        if self.bias and self.b_constraint:
            self.constraints[self.b] = self.b_constraint

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def get_output_shape_for(self, input_shape):
        assert input_shape and len(input_shape) == 2
        return (input_shape[0], self.output_dim)

    def call(self, x, mask=None):
        # no activation, this layer is only linear.
        output = K.dot(x, self.W)
        if self.bias:
            output += self.b
        output = K.max(output, axis=1)
        return output

    def get_config(self):
        config = {'output_dim': self.output_dim,
                  'init': self.init.__name__,
                  'nb_feature': self.nb_feature,
                  'W_regularizer': self.W_regularizer.get_config() if self.W_regularizer else None,
                  'b_regularizer': self.b_regularizer.get_config() if self.b_regularizer else None,
                  'activity_regularizer': self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  'W_constraint': self.W_constraint.get_config() if self.W_constraint else None,
                  'b_constraint': self.b_constraint.get_config() if self.b_constraint else None,
                  'bias': self.bias,
                  'input_dim': self.input_dim}
        base_config = super(MaxoutDense, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Highway(Layer):
    '''Densely connected highway network,
    a natural extension of LSTMs to feedforward networks.

    # Arguments
        init: name of initialization function for the weights of the layer
            (see [initializations](../initializations.md)),
            or alternatively, Theano function to use for weights
            initialization. This parameter is only relevant
            if you don't pass a `weights` argument.
        transform_bias: value for the bias to take on initially (default -2)
        activation: name of activation function to use
            (see [activations](../activations.md)),
            or alternatively, elementwise Theano function.
            If you don't specify anything, no activation is applied
            (ie. "linear" activation: a(x) = x).
        weights: list of numpy arrays to set as initial weights.
            The list should have 2 elements, of shape `(input_dim, output_dim)`
            and (output_dim,) for weights and biases respectively.
        W_regularizer: instance of [WeightRegularizer](../regularizers.md)
            (eg. L1 or L2 regularization), applied to the main weights matrix.
        b_regularizer: instance of [WeightRegularizer](../regularizers.md),
            applied to the bias.
        activity_regularizer: instance of [ActivityRegularizer](../regularizers.md),
            applied to the network output.
        W_constraint: instance of the [constraints](../constraints.md) module
            (eg. maxnorm, nonneg), applied to the main weights matrix.
        b_constraint: instance of the [constraints](../constraints.md) module,
            applied to the bias.
        bias: whether to include a bias (i.e. make the layer affine rather than linear).
        input_dim: dimensionality of the input (integer).
            This argument (or alternatively, the keyword argument `input_shape`)
            is required when using this layer as the first layer in a model.

    # Input shape
        2D tensor with shape: `(nb_samples, input_dim)`.

    # Output shape
        2D tensor with shape: `(nb_samples, input_dim)`.

    # References
        - [Highway Networks](http://arxiv.org/pdf/1505.00387v2.pdf)
    '''
    def __init__(self, init='glorot_uniform', transform_bias=-2,
                 activation='linear', weights=None,
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None,
                 bias=True, input_dim=None, **kwargs):
        self.init = initializations.get(init)
        self.transform_bias = transform_bias
        self.activation = activations.get(activation)

        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)

        self.bias = bias
        self.initial_weights = weights
        self.input_spec = [InputSpec(ndim=2)]

        self.input_dim = input_dim
        if self.input_dim:
            kwargs['input_shape'] = (self.input_dim,)
        super(Highway, self).__init__(**kwargs)

    def build(self, input_shape):
        input_dim = input_shape[1]
        self.input_spec = [InputSpec(dtype=K.floatx(),
                                     shape=(None, input_dim))]

        self.W = self.init((input_dim, input_dim),
                           name='{}_W'.format(self.name))
        self.W_carry = self.init((input_dim, input_dim),
                                 name='{}_W_carry'.format(self.name))

        if self.bias:
            self.b = K.zeros((input_dim,), name='{}_b'.format(self.name))
            # initialize with a vector of values `transform_bias`
            self.b_carry = K.variable(np.ones((input_dim,)) * self.transform_bias,
                                      name='{}_b_carry'.format(self.name))
            self.trainable_weights = [self.W, self.b, self.W_carry, self.b_carry]
        else:
            self.trainable_weights = [self.W, self.W_carry]

        self.regularizers = []
        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.bias and self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        self.constraints = {}
        if self.W_constraint:
            self.constraints[self.W] = self.W_constraint
        if self.bias and self.b_constraint:
            self.constraints[self.b] = self.b_constraint

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def call(self, x, mask=None):
        y = K.dot(x, self.W_carry)
        if self.bias:
            y += self.b_carry
        transform_weight = activations.sigmoid(y)
        y = K.dot(x, self.W)
        if self.bias:
            y += self.b
        act = self.activation(y)
        act *= transform_weight
        output = act + (1 - transform_weight) * x
        return output

    def get_config(self):
        config = {'init': self.init.__name__,
                  'transform_bias': self.transform_bias,
                  'activation': self.activation.__name__,
                  'W_regularizer': self.W_regularizer.get_config() if self.W_regularizer else None,
                  'b_regularizer': self.b_regularizer.get_config() if self.b_regularizer else None,
                  'activity_regularizer': self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  'W_constraint': self.W_constraint.get_config() if self.W_constraint else None,
                  'b_constraint': self.b_constraint.get_config() if self.b_constraint else None,
                  'bias': self.bias,
                  'input_dim': self.input_dim}
        base_config = super(Highway, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class TimeDistributedDense(Layer):
    '''Apply a same Dense layer for each dimension[1] (time_dimension) input.
    Especially useful after a recurrent network with 'return_sequence=True'.

    Note: this layer is deprecated, prefer using the `TimeDistributed` wrapper:
    ```python
        model.add(TimeDistributed(Dense(32)))
    ```

    # Input shape
        3D tensor with shape `(nb_sample, time_dimension, input_dim)`.
    # Output shape
        3D tensor with shape `(nb_sample, time_dimension, output_dim)`.
    # Arguments
        output_dim: int > 0.
        init: name of initialization function for the weights of the layer
            (see [initializations](../initializations.md)),
            or alternatively, Theano function to use for weights
            initialization. This parameter is only relevant
            if you don't pass a `weights` argument.
        activation: name of activation function to use
            (see [activations](../activations.md)),
            or alternatively, elementwise Theano function.
            If you don't specify anything, no activation is applied
            (ie. "linear" activation: a(x) = x).
        weights: list of numpy arrays to set as initial weights.
            The list should have 2 elements, of shape `(input_dim, output_dim)`
            and (output_dim,) for weights and biases respectively.
        W_regularizer: instance of [WeightRegularizer](../regularizers.md)
            (eg. L1 or L2 regularization), applied to the main weights matrix.
        b_regularizer: instance of [WeightRegularizer](../regularizers.md),
            applied to the bias.
        activity_regularizer: instance of [ActivityRegularizer](../regularizers.md),
            applied to the network output.
        W_constraint: instance of the [constraints](../constraints.md) module
            (eg. maxnorm, nonneg), applied to the main weights matrix.
        b_constraint: instance of the [constraints](../constraints.md) module,
            applied to the bias.
        bias: whether to include a bias (i.e. make the layer affine rather than linear).
        input_dim: dimensionality of the input (integer).
            This argument (or alternatively, the keyword argument `input_shape`)
            is required when using this layer as the first layer in a model.
        input_length: length of inputs sequences
            (integer, or None for variable-length sequences).
    '''

    def __init__(self, output_dim,
                 init='glorot_uniform', activation='linear', weights=None,
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None,
                 bias=True, input_dim=None, input_length=None, **kwargs):
        warnings.warn('TimeDistributedDense is deprecated, '
                      'please use TimeDistributed(Dense(...)) instead.')
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.activation = activations.get(activation)

        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)

        self.bias = bias
        self.initial_weights = weights
        self.input_spec = [InputSpec(ndim=3)]
        self.supports_masking = True

        self.input_dim = input_dim
        self.input_length = input_length
        if self.input_dim:
            kwargs['input_shape'] = (self.input_length, self.input_dim)
        super(TimeDistributedDense, self).__init__(**kwargs)

    def build(self, input_shape):
        self.input_spec = [InputSpec(dtype=K.floatx(),
                                     shape=(None,) + input_shape[1:])]
        input_dim = input_shape[2]

        self.W = self.init((input_dim, self.output_dim),
                           name='{}_W'.format(self.name))
        if self.bias:
            self.b = K.zeros((self.output_dim,),
                             name='{}_b'.format(self.name))
            self.trainable_weights = [self.W, self.b]
        self.regularizers = []

        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.bias and self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        self.constraints = {}
        if self.W_constraint:
            self.constraints[self.W] = self.W_constraint
        if self.bias and self.b_constraint:
            self.constraints[self.b] = self.b_constraint

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def get_output_shape_for(self, input_shape):
        return (input_shape[0], input_shape[1], self.output_dim)

    def call(self, x, mask=None):
        input_shape = self.input_spec[0].shape
        # x has shape (samples, timesteps, input_dim)
        input_length = input_shape[1]
        # Note: input_length should always be provided when using tensorflow backend.
        if not input_length:
            if hasattr(K, 'int_shape'):
                input_length = K.int_shape(x)[1]
                if not input_length:
                    raise Exception(
                        'Layer ' + self.name +
                        ' requires to know the length of its input, '
                        'but it could not be inferred automatically. '
                        'Specify it manually by passing an input_shape '
                        'argument to the first layer in your model.')
            else:
                input_length = K.shape(x)[1]

        # Squash samples and timesteps into a single axis
        x = K.reshape(x, (-1, input_shape[-1]))  # (samples * timesteps, input_dim)
        y = K.dot(x, self.W)  # (samples * timesteps, output_dim)
        if self.bias:
            y += self.b
        # We have to reshape Y to (samples, timesteps, output_dim)
        y = K.reshape(y, (-1, input_length, self.output_dim))  # (samples, timesteps, output_dim)
        y = self.activation(y)
        return y

    def get_config(self):
        config = {'output_dim': self.output_dim,
                  'init': self.init.__name__,
                  'activation': self.activation.__name__,
                  'W_regularizer': self.W_regularizer.get_config() if self.W_regularizer else None,
                  'b_regularizer': self.b_regularizer.get_config() if self.b_regularizer else None,
                  'activity_regularizer': self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  'W_constraint': self.W_constraint.get_config() if self.W_constraint else None,
                  'b_constraint': self.b_constraint.get_config() if self.b_constraint else None,
                  'bias': self.bias,
                  'input_dim': self.input_dim,
                  'input_length': self.input_length}
        base_config = super(TimeDistributedDense, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

from __future__ import absolute_import

from .. import backend as K
from .. import initializations, regularizers, constraints
from ..engine import Layer


class Embedding(Layer):
    '''Turn positive integers (indexes) into dense vectors of fixed size.
    eg. [[4], [20]] -> [[0.25, 0.1], [0.6, -0.2]]

    This layer can only be used as the first layer in a model.

    # Example

    ```python
      model = Sequential()
      model.add(Embedding(1000, 64, input_length=10))
      # the model will take as input an integer matrix of size (batch, input_length).
      # the largest integer (i.e. word index) in the input should be no larger than 1000 (vocabulary size).
      # now model.output_shape == (None, 10, 64), where None is the batch dimension.

      input_array = np.random.randint(1000, size=(32, 10))

      model.compile('rmsprop', 'mse')
      output_array = model.predict(input_array)
      assert output_array.shape == (32, 10, 64)
    ```

    # Arguments
      input_dim: int >= 0. Size of the vocabulary, ie.
          1 + maximum integer index occurring in the input data.
      output_dim: int >= 0. Dimension of the dense embedding.
      init: name of initialization function for the weights
          of the layer (see: [initializations](../initializations.md)),
          or alternatively, Theano function to use for weights initialization.
          This parameter is only relevant if you don't pass a `weights` argument.
      weights: list of numpy arrays to set as initial weights.
          The list should have 1 element, of shape `(input_dim, output_dim)`.
      W_regularizer: instance of the [regularizers](../regularizers.md) module
        (eg. L1 or L2 regularization), applied to the embedding matrix.
      W_constraint: instance of the [constraints](../constraints.md) module
          (eg. maxnorm, nonneg), applied to the embedding matrix.
      mask_zero: Whether or not the input value 0 is a special "padding"
          value that should be masked out.
          This is useful for [recurrent layers](recurrent.md) which may take
          variable length input. If this is `True` then all subsequent layers
          in the model need to support masking or an exception will be raised.
      input_length: Length of input sequences, when it is constant.
          This argument is required if you are going to connect
          `Flatten` then `Dense` layers upstream
          (without it, the shape of the dense outputs cannot be computed).
      dropout: float between 0 and 1. Fraction of the embeddings to drop.

    # Input shape
        2D tensor with shape: `(nb_samples, sequence_length)`.

    # Output shape
        3D tensor with shape: `(nb_samples, sequence_length, output_dim)`.

    # References
        - [A Theoretically Grounded Application of Dropout in Recurrent Neural Networks](http://arxiv.org/abs/1512.05287)
    '''
    input_ndim = 2

    def __init__(self, input_dim, output_dim,
                 init='uniform', input_length=None,
                 W_regularizer=None, activity_regularizer=None,
                 W_constraint=None,
                 mask_zero=False,
                 weights=None, dropout=0., **kwargs):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.input_length = input_length
        self.mask_zero = mask_zero
        self.dropout = dropout

        self.W_constraint = constraints.get(W_constraint)

        self.W_regularizer = regularizers.get(W_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        if 0. < self.dropout < 1.:
            self.uses_learning_phase = True
        self.initial_weights = weights
        kwargs['input_shape'] = (self.input_length,)
        kwargs['input_dtype'] = 'int32'
        super(Embedding, self).__init__(**kwargs)

    def build(self, input_shape):
        self.W = self.init((self.input_dim, self.output_dim),
                           name='{}_W'.format(self.name))
        self.trainable_weights = [self.W]

        self.constraints = {}
        if self.W_constraint:
            self.constraints[self.W] = self.W_constraint

        self.regularizers = []
        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)

    def compute_mask(self, x, mask=None):
        if not self.mask_zero:
            return None
        else:
            return K.not_equal(x, 0)

    def get_output_shape_for(self, input_shape):
        if not self.input_length:
            input_length = input_shape[1]
        else:
            input_length = self.input_length
        return (input_shape[0], input_length, self.output_dim)

    def call(self, x, mask=None):
        if 0. < self.dropout < 1.:
            retain_p = 1. - self.dropout
            B = K.random_binomial((self.input_dim,), p=retain_p) * (1. / retain_p)
            B = K.expand_dims(B)
            W = K.in_train_phase(self.W * B, self.W)
        else:
            W = self.W
        out = K.gather(W, x)
        return out

    def get_config(self):
        config = {'input_dim': self.input_dim,
                  'output_dim': self.output_dim,
                  'init': self.init.__name__,
                  'input_length': self.input_length,
                  'mask_zero': self.mask_zero,
                  'activity_regularizer': self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  'W_regularizer': self.W_regularizer.get_config() if self.W_regularizer else None,
                  'W_constraint': self.W_constraint.get_config() if self.W_constraint else None,
                  'dropout': self.dropout}
        base_config = super(Embedding, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

from ..engine import Layer, InputSpec
from .. import backend as K


class Wrapper(Layer):

    def __init__(self, layer, **kwargs):
        self.layer = layer
        self.uses_learning_phase = layer.uses_learning_phase
        super(Wrapper, self).__init__(**kwargs)

    def build(self, input_shape=None):
        '''Assumes that self.layer is already set.
        Should be called at the end of .build() in the
        children classes.
        '''
        self.trainable_weights = getattr(self.layer, 'trainable_weights', [])
        self.non_trainable_weights = getattr(self.layer, 'non_trainable_weights', [])
        self.updates = getattr(self.layer, 'updates', [])
        self.regularizers = getattr(self.layer, 'regularizers', [])
        self.constraints = getattr(self.layer, 'constraints', {})

    def get_weights(self):
        weights = self.layer.get_weights()
        return weights

    def set_weights(self, weights):
        self.layer.set_weights(weights)

    def get_config(self):
        config = {'layer': {'class_name': self.layer.__class__.__name__,
                            'config': self.layer.get_config()}}
        base_config = super(Wrapper, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

    @classmethod
    def from_config(cls, config):
        from keras.utils.layer_utils import layer_from_config
        layer = layer_from_config(config.pop('layer'))
        return cls(layer, **config)


class TimeDistributed(Wrapper):
    """This wrapper allows to apply a layer to every
    temporal slice of an input.

    The input should be at least 3D,
    and the dimension of index one will be considered to be
    the temporal dimension.

    Consider a batch of 32 samples, where each sample is a sequence of 10
    vectors of 16 dimensions. The batch input shape of the layer is then `(32, 10, 16)`
    (and the `input_shape`, not including the samples dimension, is `(10, 16)`).

    You can then use `TimeDistributed` to apply a `Dense` layer to each of the 10 timesteps, independently:
    ```python
        # as the first layer in a model
        model = Sequential()
        model.add(TimeDistributed(Dense(8), input_shape=(10, 16)))
        # now model.output_shape == (None, 10, 8)

        # subsequent layers: no need for input_shape
        model.add(TimeDistributed(Dense(32)))
        # now model.output_shape == (None, 10, 32)
    ```

    The output will then have shape `(32, 10, 8)`.

    Note this is strictly equivalent to using `layers.core.TimeDistributedDense`.
    However what is different about `TimeDistributed`
    is that it can be used with arbitrary layers, not just `Dense`,
    for instance with a `Convolution2D` layer:

    ```python
        model = Sequential()
        model.add(TimeDistributed(Convolution2D(64, 3, 3), input_shape=(10, 3, 299, 299)))
    ```

    # Arguments
        layer: a layer instance.
    """
    def __init__(self, layer, **kwargs):
        self.supports_masking = True
        super(TimeDistributed, self).__init__(layer, **kwargs)

    def build(self, input_shape):
        assert len(input_shape) >= 3
        self.input_spec = [InputSpec(shape=input_shape)]
        if K._BACKEND == 'tensorflow':
            if not input_shape[1]:
                raise Exception('When using TensorFlow, you should define '
                                'explicitly the number of timesteps of '
                                'your sequences.\n'
                                'If your first layer is an Embedding, '
                                'make sure to pass it an "input_length" '
                                'argument. Otherwise, make sure '
                                'the first layer has '
                                'an "input_shape" or "batch_input_shape" '
                                'argument, including the time axis.')
        child_input_shape = (input_shape[0],) + input_shape[2:]
        if not self.layer.built:
            self.layer.build(child_input_shape)
            self.layer.built = True
        super(TimeDistributed, self).build()

    def get_output_shape_for(self, input_shape):
        child_input_shape = (input_shape[0],) + input_shape[2:]
        child_output_shape = self.layer.get_output_shape_for(child_input_shape)
        timesteps = input_shape[1]
        return (child_output_shape[0], timesteps) + child_output_shape[1:]

    def call(self, X, mask=None):
        input_shape = self.input_spec[0].shape
        if input_shape[0]:
            # batch size matters, use rnn-based implementation
            def step(x, states):
                output = self.layer.call(x)
                return output, []

            last_output, outputs, states = K.rnn(step, X,
                                                 initial_states=[])
            y = outputs
        else:
            # no batch size specified, therefore the layer will be able
            # to process batches of any size
            # we can go with reshape-based implementation for performance
            input_length = input_shape[1]
            if not input_length:
                input_length = K.shape(X)[1]
            X = K.reshape(X, (-1, ) + input_shape[2:])  # (nb_samples * timesteps, ...)
            y = self.layer.call(X)  # (nb_samples * timesteps, ...)
            # (nb_samples, timesteps, ...)
            output_shape = self.get_output_shape_for(input_shape)
            y = K.reshape(y, (-1, input_length) + output_shape[2:])
        return y

from __future__ import absolute_import
from ..engine import Layer
from .. import backend as K


class GaussianNoise(Layer):
    '''Apply to the input an additive zero-centred gaussian noise with
    standard deviation `sigma`. This is useful to mitigate overfitting
    (you could see it as a kind of random data augmentation).
    Gaussian Noise (GS) is a natural choice as corruption process
    for real valued inputs.

    As it is a regularization layer, it is only active at training time.

    # Arguments
        sigma: float, standard deviation of the noise distribution.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as input.
    '''
    def __init__(self, sigma, **kwargs):
        self.supports_masking = True
        self.sigma = sigma
        self.uses_learning_phase = True
        super(GaussianNoise, self).__init__(**kwargs)

    def call(self, x, mask=None):
        noise_x = x + K.random_normal(shape=K.shape(x),
                                      mean=0.,
                                      std=self.sigma)
        return K.in_train_phase(noise_x, x)

    def get_config(self):
        config = {'sigma': self.sigma}
        base_config = super(GaussianNoise, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class GaussianDropout(Layer):
    '''Apply to the input an multiplicative one-centred gaussian noise
    with standard deviation `sqrt(p/(1-p))`.

    As it is a regularization layer, it is only active at training time.

    # Arguments
        p: float, drop probability (as with `Dropout`).

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as input.

    # References
        [Dropout: A Simple Way to Prevent Neural Networks from Overfitting Srivastava, Hinton, et al. 2014](http://www.cs.toronto.edu/~rsalakhu/papers/srivastava14a.pdf)
    '''
    def __init__(self, p, **kwargs):
        self.supports_masking = True
        self.p = p
        if 0 < p < 1:
            self.uses_learning_phase = True
        super(GaussianDropout, self).__init__(**kwargs)

    def call(self, x, mask=None):
        if 0 < self.p < 1:
            noise_x = x * K.random_normal(shape=K.shape(x), mean=1.0,
                                          std=K.sqrt(self.p / (1.0 - self.p)))
            return K.in_train_phase(noise_x, x)
        return x

    def get_config(self):
        config = {'p': self.p}
        base_config = super(GaussianDropout, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

from .. import initializations
from ..engine import Layer
from .. import backend as K
import numpy as np


class LeakyReLU(Layer):
    '''Special version of a Rectified Linear Unit
    that allows a small gradient when the unit is not active:
    `f(x) = alpha * x for x < 0`,
    `f(x) = x for x >= 0`.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as the input.

    # Arguments
        alpha: float >= 0. Negative slope coefficient.
    '''
    def __init__(self, alpha=0.3, **kwargs):
        self.supports_masking = True
        self.alpha = alpha
        super(LeakyReLU, self).__init__(**kwargs)

    def call(self, x, mask=None):
        return K.relu(x, alpha=self.alpha)

    def get_config(self):
        config = {'alpha': self.alpha}
        base_config = super(LeakyReLU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class PReLU(Layer):
    '''Parametric Rectified Linear Unit:
    `f(x) = alphas * x for x < 0`,
    `f(x) = x for x >= 0`,
    where `alphas` is a learned array with the same shape as x.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as the input.

    # Arguments
        init: initialization function for the weights.
        weights: initial weights, as a list of a single numpy array.

    # References
        - [Delving Deep into Rectifiers: Surpassing Human-Level Performance on ImageNet Classification](http://arxiv.org/pdf/1502.01852v1.pdf)
    '''
    def __init__(self, init='zero', weights=None, **kwargs):
        self.supports_masking = True
        self.init = initializations.get(init)
        self.initial_weights = weights
        super(PReLU, self).__init__(**kwargs)

    def build(self, input_shape):
        self.alphas = self.init(input_shape[1:],
                                name='{}_alphas'.format(self.name))
        self.trainable_weights = [self.alphas]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def call(self, x, mask=None):
        pos = K.relu(x)
        neg = self.alphas * (x - abs(x)) * 0.5
        return pos + neg

    def get_config(self):
        config = {'init': self.init.__name__}
        base_config = super(PReLU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ELU(Layer):
    '''Exponential Linear Unit:
    `f(x) =  alpha * (exp(x) - 1.) for x < 0`,
    `f(x) = x for x >= 0`.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as the input.

    # Arguments
        alpha: scale for the negative factor.

    # References
        - [Fast and Accurate Deep Network Learning by Exponential Linear Units (ELUs)](http://arxiv.org/pdf/1511.07289v1.pdf)
    '''
    def __init__(self, alpha=1.0, **kwargs):
        self.supports_masking = True
        self.alpha = K.cast_to_floatx(alpha)
        super(ELU, self).__init__(**kwargs)

    def call(self, x, mask=None):
        pos = K.relu(x)
        neg = (x - abs(x)) * 0.5
        return pos + self.alpha * (K.exp(neg) - 1.)

    def get_config(self):
        config = {'alpha': self.alpha}
        base_config = super(ELU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ParametricSoftplus(Layer):
    '''Parametric Softplus:
    `alpha * log(1 + exp(beta * x))`

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as the input.

    # Arguments
        alpha_init: float. Initial value of the alpha weights.
        beta_init: float. Initial values of the beta weights.
        weights: initial weights, as a list of 2 numpy arrays.

    # References
        - [Inferring Nonlinear Neuronal Computation Based on Physiologically Plausible Inputs](http://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003143)
    '''
    def __init__(self, alpha_init=0.2, beta_init=5.0,
                 weights=None, **kwargs):
        self.supports_masking = True
        self.alpha_init = K.cast_to_floatx(alpha_init)
        self.beta_init = K.cast_to_floatx(beta_init)
        self.initial_weights = weights
        super(ParametricSoftplus, self).__init__(**kwargs)

    def build(self, input_shape):
        input_shape = input_shape[1:]
        self.alphas = K.variable(self.alpha_init * np.ones(input_shape),
                                 name='{}_alphas'.format(self.name))
        self.betas = K.variable(self.beta_init * np.ones(input_shape),
                                name='{}_betas'.format(self.name))
        self.trainable_weights = [self.alphas, self.betas]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def call(self, x, mask=None):
        return K.softplus(self.betas * x) * self.alphas

    def get_config(self):
        config = {'alpha_init': self.alpha_init,
                  'beta_init': self.beta_init}
        base_config = super(ParametricSoftplus, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ThresholdedReLU(Layer):
    '''Thresholded Rectified Linear Unit:
    `f(x) = x for x > theta`
    `f(x) = 0 otherwise`.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as the input.

    # Arguments
        theta: float >= 0. Threshold location of activation.

    # References
        - [Zero-Bias Autoencoders and the Benefits of Co-Adapting Features](http://arxiv.org/pdf/1402.3337.pdf)
    '''
    def __init__(self, theta=1.0, **kwargs):
        self.supports_masking = True
        self.theta = K.cast_to_floatx(theta)
        super(ThresholdedReLU, self).__init__(**kwargs)

    def call(self, x, mask=None):
        return x * K.cast(x > self.theta, K.floatx())

    def get_config(self):
        config = {'theta': self.theta}
        base_config = super(ThresholdedReLU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class SReLU(Layer):
    '''S-shaped Rectified Linear Unit.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as the input.

    # Arguments
        t_left_init: initialization function for the left part intercept
        a_left_init: initialization function for the left part slope
        t_right_init: initialization function for the right part intercept
        a_right_init: initialization function for the right part slope

    # References
        - [Deep Learning with S-shaped Rectified Linear Activation Units](http://arxiv.org/abs/1512.07030)
    '''
    def __init__(self, t_left_init='zero', a_left_init='glorot_uniform',
                 t_right_init='glorot_uniform', a_right_init='one', **kwargs):
        self.supports_masking = True
        self.t_left_init = t_left_init
        self.a_left_init = a_left_init
        self.t_right_init = t_right_init
        self.a_right_init = a_right_init
        super(SReLU, self).__init__(**kwargs)

    def build(self, input_shape):
        input_shape = input_shape[1:]

        t_left_init = initializations.get(self.t_left_init)
        a_left_init = initializations.get(self.a_left_init)
        t_right_init = initializations.get(self.t_right_init)
        a_right_init = initializations.get(self.a_right_init)

        self.t_left = t_left_init(input_shape,
                                  name='{}_t_left'.format(self.name))
        self.a_left = a_left_init(input_shape,
                                  name='{}_a_left'.format(self.name))
        self.t_right = t_right_init(input_shape,
                                    name='{}_t_right'.format(self.name))
        self.a_right = a_right_init(input_shape,
                                    name='{}_a_right'.format(self.name))
        # ensure the the right part is always to the right of the left
        self.t_right_actual = self.t_left + abs(self.t_right)
        self.trainable_weights = [self.t_left, self.a_left,
                                  self.t_right, self.a_right]

    def call(self, x, mask=None):
        Y_left_and_center = self.t_left + K.relu(x - self.t_left,
                                                 self.a_left,
                                                 self.t_right_actual - self.t_left)
        Y_right = K.relu(x - self.t_right_actual) * self.a_right
        return Y_left_and_center + Y_right

    def get_config(self):
        config = {'t_left_init': self.t_left_init,
                  'a_left_init': self.a_left_init,
                  't_right_init': self.t_right_init,
                  'a_right_init': self.a_right_init}
        base_config = super(SReLU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

from ..engine import Layer, InputSpec
from .. import initializations
from .. import backend as K


class BatchNormalization(Layer):
    '''Normalize the activations of the previous layer at each batch,
    i.e. applies a transformation that maintains the mean activation
    close to 0 and the activation standard deviation close to 1.

    # Arguments
        epsilon: small float > 0. Fuzz parameter.
        mode: integer, 0 or 1.
            - 0: feature-wise normalization.
                Each feature map in the input will
                be normalized separately. The axis on which
                to normalize is specified by the `axis` argument.
                Note that if the input is a 4D image tensor
                using Theano conventions (samples, channels, rows, cols)
                then you should set `axis` to `1` to normalize along
                the channels axis.
            - 1: sample-wise normalization. This mode assumes a 2D input.
        axis: integer, axis along which to normalize in mode 0. For instance,
            if your input tensor has shape (samples, channels, rows, cols),
            set axis to 1 to normalize per feature map (channels axis).
        momentum: momentum in the computation of the
            exponential average of the mean and standard deviation
            of the data, for feature-wise normalization.
        weights: Initialization weights.
            List of 2 numpy arrays, with shapes:
            `[(input_shape,), (input_shape,)]`
        beta_init: name of initialization function for shift parameter
            (see [initializations](../initializations.md)), or alternatively,
            Theano/TensorFlow function to use for weights initialization.
            This parameter is only relevant if you don't pass a `weights` argument.
        gamma_init: name of initialization function for scale parameter (see
            [initializations](../initializations.md)), or alternatively,
            Theano/TensorFlow function to use for weights initialization.
            This parameter is only relevant if you don't pass a `weights` argument.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as input.

    # References
        - [Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift](http://arxiv.org/pdf/1502.03167v3.pdf)
    '''
    def __init__(self, epsilon=1e-6, mode=0, axis=-1, momentum=0.9,
                 weights=None, beta_init='zero', gamma_init='one', **kwargs):
        self.beta_init = initializations.get(beta_init)
        self.gamma_init = initializations.get(gamma_init)
        self.epsilon = epsilon
        self.mode = mode
        self.axis = axis
        self.momentum = momentum
        self.initial_weights = weights
        self.uses_learning_phase = True
        super(BatchNormalization, self).__init__(**kwargs)

    def build(self, input_shape):
        self.input_spec = [InputSpec(shape=input_shape)]
        shape = (input_shape[self.axis],)

        self.gamma = self.gamma_init(shape, name='{}_gamma'.format(self.name))
        self.beta = self.beta_init(shape, name='{}_beta'.format(self.name))
        self.trainable_weights = [self.gamma, self.beta]

        self.running_mean = K.zeros(shape,
                                    name='{}_running_mean'.format(self.name))
        self.running_std = K.ones(shape,
                                  name='{}_running_std'.format(self.name))
        self.non_trainable_weights = [self.running_mean, self.running_std]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def call(self, x, mask=None):
        if self.mode == 0:
            input_shape = self.input_spec[0].shape

            reduction_axes = list(range(len(input_shape)))
            del reduction_axes[self.axis]
            broadcast_shape = [1] * len(input_shape)
            broadcast_shape[self.axis] = input_shape[self.axis]

            # case: train mode (uses stats of the current batch)
            mean = K.mean(x, axis=reduction_axes)
            brodcast_mean = K.reshape(mean, broadcast_shape)
            std = K.mean(K.square(x - brodcast_mean) + self.epsilon, axis=reduction_axes)
            std = K.sqrt(std)
            brodcast_std = K.reshape(std, broadcast_shape)
            mean_update = self.momentum * self.running_mean + (1-self.momentum) * mean
            std_update = self.momentum * self.running_std + (1-self.momentum) * std
            self.updates = [(self.running_mean, mean_update),
                            (self.running_std, std_update)]
            x_normed = (x - brodcast_mean) / (brodcast_std + self.epsilon)

            # case: test mode (uses running averages)
            brodcast_running_mean = K.reshape(self.running_mean, broadcast_shape)
            brodcast_running_std = K.reshape(self.running_std, broadcast_shape)
            x_normed_running = ((x - brodcast_running_mean) / (brodcast_running_std + self.epsilon))

            # pick the normalized form of x corresponding to the training phase
            x_normed = K.in_train_phase(x_normed, x_normed_running)
            out = K.reshape(self.gamma, broadcast_shape) * x_normed + K.reshape(self.beta, broadcast_shape)

        elif self.mode == 1:
            # sample-wise normalization
            m = K.mean(x, axis=-1, keepdims=True)
            std = K.std(x, axis=-1, keepdims=True)
            x_normed = (x - m) / (std + self.epsilon)
            out = self.gamma * x_normed + self.beta
        return out

    def get_config(self):
        config = {"epsilon": self.epsilon,
                  "mode": self.mode,
                  "axis": self.axis,
                  "momentum": self.momentum}
        base_config = super(BatchNormalization, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

from __future__ import absolute_import
from .cifar import load_batch
from ..utils.data_utils import get_file
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
from six.moves import cPickle
import gzip
from ..utils.data_utils import get_file
from six.moves import zip
import numpy as np


def load_data(path="imdb.pkl", nb_words=None, skip_top=0,
              maxlen=None, test_split=0.2, seed=113,
              start_char=1, oov_char=2, index_from=3):

    path = get_file(path, origin="https://s3.amazonaws.com/text-datasets/imdb.pkl")

    if path.endswith(".gz"):
        f = gzip.open(path, 'rb')
    else:
        f = open(path, 'rb')

    X, labels = cPickle.load(f)
    f.close()

    np.random.seed(seed)
    np.random.shuffle(X)
    np.random.seed(seed)
    np.random.shuffle(labels)

    if start_char is not None:
        X = [[start_char] + [w + index_from for w in x] for x in X]
    elif index_from:
        X = [[w + index_from for w in x] for x in X]

    if maxlen:
        new_X = []
        new_labels = []
        for x, y in zip(X, labels):
            if len(x) < maxlen:
                new_X.append(x)
                new_labels.append(y)
        X = new_X
        labels = new_labels
    if not X:
        raise Exception('After filtering for sequences shorter than maxlen=' +
                        str(maxlen) + ', no sequence was kept. '
                        'Increase maxlen.')
    if not nb_words:
        nb_words = max([max(x) for x in X])

    # by convention, use 2 as OOV word
    # reserve 'index_from' (=3 by default) characters: 0 (padding), 1 (start), 2 (OOV)
    if oov_char is not None:
        X = [[oov_char if (w >= nb_words or w < skip_top) else w for w in x] for x in X]
    else:
        nX = []
        for x in X:
            nx = []
            for w in x:
                if (w >= nb_words or w < skip_top):
                    nx.append(w)
            nX.append(nx)
        X = nX

    X_train = np.array(X[:int(len(X) * (1 - test_split))])
    y_train = np.array(labels[:int(len(X) * (1 - test_split))])

    X_test = np.array(X[int(len(X) * (1 - test_split)):])
    y_test = np.array(labels[int(len(X) * (1 - test_split)):])

    return (X_train, y_train), (X_test, y_test)

from ..utils.data_utils import *
import warnings

warnings.warn('data_utils has been moved to keras.utils.data_utils.')

# -*- coding: utf-8 -*-
from __future__ import absolute_import
from ..utils.data_utils import get_file
from six.moves import cPickle
from six.moves import zip
import numpy as np


def load_data(path="reuters.pkl", nb_words=None, skip_top=0,
              maxlen=None, test_split=0.2, seed=113,
              start_char=1, oov_char=2, index_from=3):

    path = get_file(path, origin="https://s3.amazonaws.com/text-datasets/reuters.pkl")
    f = open(path, 'rb')
    X, labels = cPickle.load(f)
    f.close()

    np.random.seed(seed)
    np.random.shuffle(X)
    np.random.seed(seed)
    np.random.shuffle(labels)

    if start_char is not None:
        X = [[start_char] + [w + index_from for w in x] for x in X]
    elif index_from:
        X = [[w + index_from for w in x] for x in X]

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

    # by convention, use 2 as OOV word
    # reserve 'index_from' (=3 by default) characters: 0 (padding), 1 (start), 2 (OOV)
    if oov_char is not None:
        X = [[oov_char if (w >= nb_words or w < skip_top) else w for w in x] for x in X]
    else:
        nX = []
        for x in X:
            nx = []
            for w in x:
                if (w >= nb_words or w < skip_top):
                    nx.append(w)
            nX.append(nx)
        X = nX

    X_train = X[:int(len(X) * (1 - test_split))]
    y_train = labels[:int(len(X) * (1 - test_split))]

    X_test = X[int(len(X) * (1 - test_split)):]
    y_test = labels[int(len(X) * (1 - test_split)):]

    return (X_train, y_train), (X_test, y_test)


def get_word_index(path="reuters_word_index.pkl"):
    path = get_file(path, origin="https://s3.amazonaws.com/text-datasets/reuters_word_index.pkl")
    f = open(path, 'rb')
    return cPickle.load(f)

# -*- coding: utf-8 -*-
from __future__ import absolute_import
import sys
from six.moves import cPickle
from six.moves import range


def load_batch(fpath, label_key='labels'):
    f = open(fpath, 'rb')
    if sys.version_info < (3,):
        d = cPickle.load(f)
    else:
        d = cPickle.load(f, encoding="bytes")
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
from ..utils.data_utils import get_file
import numpy as np
import os


def load_data():
    dirname = "cifar-10-batches-py"
    origin = "http://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
    path = get_file(dirname, origin=origin, untar=True)

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
from ..utils.data_utils import get_file
from six.moves import cPickle
import sys


def load_data(path="mnist.pkl.gz"):
    path = get_file(path, origin="https://s3.amazonaws.com/img-datasets/mnist.pkl.gz")

    if path.endswith(".gz"):
        f = gzip.open(path, 'rb')
    else:
        f = open(path, 'rb')

    if sys.version_info < (3,):
        data = cPickle.load(f)
    else:
        data = cPickle.load(f, encoding="bytes")

    f.close()
    return data  # (X_train, y_train), (X_test, y_test)

from collections import OrderedDict
import warnings
import copy

from .. import backend as K
from ..layers import InputLayer, Layer, Merge
from ..engine.training import Model


class Graph(Model):
    '''Arbitrary connection graph.

    THIS IS A LEGACY MODEL AND SHOULD NOT BE USED
    except for backwards compatibility support.

    For multi-inputs/multi-outputs models, or
    models using shared layers, use the functional API instead.
    '''

    def __init__(self, name=None):
        # model attributes
        self.inbound_nodes = []
        self.outbound_nodes = []
        self.built = False
        self.supports_masking = False

        # legacy attributes (we prefix them with _graph_)
        self._graph_namespace = set()  # strings
        self._graph_nodes = OrderedDict()  # layer-like
        self._graph_inputs = OrderedDict()  # layer-like
        self._graph_outputs = OrderedDict()  # layer-like
        self._graph_input_config = []  # dicts
        self._graph_output_config = []  # dicts
        self._graph_node_config = []  # dicts
        self._graph_shared_nodes_names = []

        if not name:
            prefix = 'graph_'
            name = prefix + str(K.get_uid(prefix))
        self.name = name

    def __call__(self, x, mask=None):
        self.build()
        return super(Graph, self).__call__(x, mask)

    def build(self, input_shape=None):
        # this will crash if the input/output layers have multiple nodes
        # no plans to support that case since Graph is deprecated
        input_tensors = [layer.output for layer in self._graph_inputs.values()]
        output_tensors = [layer.output for layer in self._graph_outputs.values()]
        # actually create the model
        super(Graph, self).__init__(input_tensors,
                                    output_tensors,
                                    name=self.name)
        self.built = True

    def compile(self, optimizer, loss,
                metrics=[],
                sample_weight_modes=None,
                loss_weights=None,
                **kwargs):
        '''Configures the learning process.

        # Arguments
            optimizer: str (name of optimizer) or optimizer object.
                See [optimizers](optimizers.md).
            loss: dictionary mapping the name(s) of the output(s) to
                a loss function (string name of objective function or
                objective function. See [objectives](objectives.md)).
            metrics: list of str (name of metrics) or
                list of metrics functions. See [metrics](metrics.md).
            sample_weight_modes: optional dictionary mapping certain
                output names to a sample weight mode ("temporal" and None
                are the only supported modes). If you need to do
                timestep-wise loss weighting on one of your graph outputs,
                you will need to set the sample weight mode for this output
                to "temporal".
            loss_weights: dictionary you can pass to specify a weight
                coefficient for each loss function (in a multi-output model).
                If no loss weight is specified for an output,
                the weight for this output's loss will be considered to be 1.
            kwargs: for Theano backend, these are passed into K.function.
                Ignored for Tensorflow backend.
        '''
        # create the underlying Model
        if not self.built:
            self.build()
        super(Graph, self).compile(optimizer, loss,
                                   metrics=metrics,
                                   sample_weight_mode=sample_weight_modes,
                                   loss_weights=loss_weights,
                                   **kwargs)

    def add_input(self, name, input_shape=None,
                  batch_input_shape=None, dtype='float'):
        '''Adds an input to the graph.

        # Arguments:
            name: string. The name of the new input.
                Must be unique in the graph.
            input_shape: a tuple of integers,
                the expected shape of the input samples.
                Does not include the batch size.
            batch_input_shape: a tuple of integers,
                the expected shape of the whole input batch,
                including the batch size.
            dtype: 'float', or 'int'.
        '''
        if name in self._graph_namespace:
            raise Exception('Duplicate node identifier: ' + name)
        self._graph_namespace.add(name)
        self.built = False

        if dtype[:3] == 'int':
            dtype = 'int32'
        elif dtype[:5] == 'float':
            dtype = K.floatx()
        else:
            raise Exception('Uknown dtype (should be "int" or "float"): ' +
                            str(dtype))

        # create input layer
        input_layer = InputLayer(input_shape=input_shape,
                                 batch_input_shape=batch_input_shape,
                                 name=name, input_dtype=dtype)
        self._graph_inputs[name] = input_layer

        # append input config to self._graph_input_config
        config = {'name': name, 'dtype': dtype}
        if batch_input_shape:
            config['batch_input_shape'] = batch_input_shape
        else:
            config['input_shape'] = input_shape
        self._graph_input_config.append(config)

    def add_node(self, layer, name, input=None, inputs=[],
                 merge_mode='concat', concat_axis=-1, dot_axes=-1,
                 create_output=False):
        '''Adds a node in the graph. It can be connected to multiple
        inputs, which will first be merged into one tensor
        according to the mode specified.

        # Arguments
            layer: the layer at the node.
            name: name for the node.
            input: when connecting the layer to a single input,
                this is the name of the incoming node.
            inputs: when connecting the layer to multiple inputs,
                this is a list of names of incoming nodes.
            merge_mode: one of {concat, sum, dot, ave, mul}
            concat_axis: when `merge_mode=='concat'`, this is the
                input concatenation axis.
            dot_axes: when `merge_mode='dot'`,
                this is the contraction axes specification;
                see the `Merge` layer for details.
            create_output: boolean. Set this to `True` if you want the output
                of your node to be an output of the graph.
        '''
        if name in self._graph_namespace:
            raise Exception('Duplicate node identifier: ' + name)
        self._graph_namespace.add(name)
        layer.name = name
        self.built = False

        if input:
            if input not in self._graph_namespace:
                raise Exception('Unknown node/input identifier: ' + input)
            if input in self._graph_nodes:
                layer.add_inbound_node(self._graph_nodes[input])
            elif input in self._graph_inputs:
                layer.add_inbound_node(self._graph_inputs[input])
        if inputs:
            to_merge = []
            for n in inputs:
                if n in self._graph_nodes:
                    to_merge.append(self._graph_nodes[n])
                elif n in self._graph_inputs:
                    to_merge.append(self._graph_inputs[n])
                else:
                    raise Exception('Unknown identifier: ' + n)
            merge = Merge(to_merge, mode=merge_mode,
                          concat_axis=concat_axis, dot_axes=dot_axes,
                          name='merge_inputs_for_' + name)
            layer.add_inbound_node(merge)
        self._graph_nodes[name] = layer
        self._graph_node_config.append({'name': name,
                                        'input': input,
                                        'inputs': inputs,
                                        'merge_mode': merge_mode,
                                        'concat_axis': concat_axis,
                                        'dot_axes': dot_axes,
                                        'create_output': create_output})
        if create_output:
            self.add_output(name, input=name)

    def add_shared_node(self, layer, name, inputs=[], merge_mode=None,
                        concat_axis=-1, dot_axes=-1, outputs=[],
                        create_output=False):
        '''Used to share a same layer across multiple nodes.

        Supposed, for instance, that you want to apply one same `Dense` layer
        after two different nodes ('node_a' and 'node_b').
        You can then add the dense layer as a shared node by calling:

        ```python
        model.add_shared_node(my_dense, name='shared_dense', inputs=['node_a', 'node_b'], ...)
        ```

        If you want access to the output of dense(node_a) and dense(node_b) separately,
        you can add these outputs to the Graph by passing an `outputs` argument:

        ```python
        model.add_shared_node(my_dense, name='shared_dense', inputs=['node_a', 'node_b'],
                              outputs=['dense_output_a', 'dense_outputs_b'])
        ```

        Otherwise you can merge these different outputs via `merge_mode`.
        In that case you can access the merged output
        under the identifier `name`.

        # Arguments
            layer: The layer to be shared across multiple inputs
            name: Name of the shared node
            inputs: List of names of input nodes
            merge_mode: Same meaning as `merge_mode` argument of `add_node()`
            concat_axis: Same meaning as `concat_axis` argument of `add_node()`
            dot_axes: Same meaning as `dot_axes` argument of `add_node()`
            outputs: Used when `merge_mode=None`. Names for the output nodes.
            create_output: Same meaning as `create_output` argument of `add_node()`.
        '''
        if name in self._graph_namespace:
            raise Exception('Duplicate node identifier: ' + name)
        self._graph_namespace.add(name)
        self.built = False

        for o in outputs:
            if o in self._graph_namespace:
                raise Exception('Duplicate node identifier: ' + o)
        if merge_mode:
            if merge_mode not in {'sum', 'ave', 'mul', 'dot', 'cos', 'concat'}:
                raise Exception('Invalid merge mode:', merge_mode)
        input_layers = []
        for i in range(len(inputs)):
            input = inputs[i]
            if input in self._graph_nodes:
                n = self._graph_nodes[input]
                input_layers.append(n)
            elif input in self._graph_inputs:
                n = self._graph_inputs[input]
                input_layers.append(n)
            else:
                raise Exception('Unknown identifier: ' + input)

        created_node_indices = []
        for input_layer in input_layers:
            created_node_indices.append(len(layer.inbound_nodes))
            layer.add_inbound_node(input_layer)

        if merge_mode:
            layer.name = 'input_for_' + name
            # collect all output nodes of layer and merge them into a single output
            merge = Merge([layer for _ in range(len(inputs))],
                          mode=merge_mode,
                          concat_axis=concat_axis, dot_axes=dot_axes,
                          node_indices=created_node_indices,
                          name=name)
            self._graph_nodes[name] = merge
            if create_output:
                self.add_output(name, input=name)
        else:
            layer.name = name
            # create one new layer per output node of layer,
            # and add them to the Graph with their own identifiers
            if len(outputs) != len(inputs):
                raise Exception('When using merge_mode=None, '
                                'you should provide a list of '
                                'output names (`output` argument) '
                                'the same size as `input`.')
            for i in range(len(outputs)):
                output_layer_name = outputs[i]
                output_layer = Layer(name=output_layer_name)
                output_layer.add_inbound_node(layer, created_node_indices[i])
                self._graph_namespace.add(output_layer_name)
                self._graph_nodes[output_layer_name] = output_layer
                if create_output:
                    self.add_output(output_layer_name, input=output_layer_name)

        self._graph_node_config.append({'name': name,
                                        'layer': {
                                            'config': layer.get_config(),
                                            'class_name': layer.__class__.__name__,
                                        },
                                        'inputs': inputs,
                                        'merge_mode': merge_mode,
                                        'concat_axis': concat_axis,
                                        'dot_axes': dot_axes,
                                        'outputs': outputs,
                                        'create_output': create_output if merge_mode else False})
        self._graph_shared_nodes_names.append(name)

    def add_output(self, name, input=None, inputs=[],
                   merge_mode='concat', concat_axis=-1, dot_axes=-1):
        '''Adds an output to the graph.

        This output can merge several node outputs into a single output.

        # Arguments
            name: name of the output.
            input: when connecting the layer to a single input,
                this is the name of the incoming node.
            inputs: when connecting the layer to multiple inputs,
                this is a list of names of incoming nodes.
            merge_mode: one of {concat, sum, dot, ave, mul}
            concat_axis: when `merge_mode=='concat'`, this is the
                input concatenation axis.
            dot_axes: when `merge_mode='dot'`,
                this is the contraction axes specification;
                see the `Merge layer for details.
        '''
        if name not in self._graph_namespace:
            self._graph_namespace.add(name)
        if name in self._graph_outputs:
            raise Exception('Duplicate output identifier:', name)
        self.built = False

        if input:
            if input in self._graph_nodes:
                layer = self._graph_nodes[input]
            elif input in self._graph_inputs:
                layer = self._graph_inputs[input]
            else:
                raise Exception('Unknown node/input identifier: ' + input)
            if layer.name == name:
                self._graph_outputs[name] = layer
            else:
                layer.name = name
                self._graph_outputs[name] = layer
        if inputs:
            to_merge = []
            for n in inputs:
                if n not in self._graph_nodes:
                    raise Exception('Unknown identifier: ' + n)
                to_merge.append(self._graph_nodes[n])
            merge = Merge(to_merge, mode=merge_mode,
                          concat_axis=concat_axis, dot_axes=dot_axes,
                          name=name)
            self._graph_outputs[name] = merge

        self._graph_output_config.append({'name': name,
                                          'input': input,
                                          'inputs': inputs,
                                          'merge_mode': merge_mode,
                                          'concat_axis': concat_axis,
                                          'dot_axes': dot_axes})

    def _get_x(self, data):
        x = []
        for key in self._graph_inputs.keys():
            if key not in data:
                raise Exception('Expected to be provided an array '
                                '(in dict argument `data`) for input "' +
                                key + '".')
            x.append(data[key])
        return x

    def _get_y(self, data):
        y = []
        for key in self._graph_outputs.keys():
            if key not in data:
                raise Exception('Expected to be provided an array '
                                '(in dict argument `data`) for output "' +
                                key + '".')
            y.append(data[key])
        return y

    def fit(self, data, batch_size=32, nb_epoch=10, verbose=1, callbacks=[],
            validation_split=0., validation_data=None, shuffle=True,
            class_weight=None, sample_weight=None, **kwargs):
        '''Trains the model for a fixed number of epochs.

        Returns a history object. Its `history` attribute is a record of
        training loss values at successive epochs,
        as well as validation loss values (if applicable).

        # Arguments
            data: dictionary mapping input names and outputs names to
                appropriate numpy arrays. All arrays should contain
                the same number of samples.
            batch_size: int. Number of samples per gradient update.
            nb_epoch: int.
            verbose: 0 for no logging to stdout,
                1 for progress bar logging, 2 for one log line per epoch.
            callbacks: `keras.callbacks.Callback` list. List of callbacks
                to apply during training. See [callbacks](callbacks.md).
            validation_split: float (0. < x < 1). Fraction of the data to
                use as held-out validation data.
            validation_data: dictionary mapping input names and outputs names
                to appropriate numpy arrays to be used as
                held-out validation data.
                All arrays should contain the same number of samples.
                Will override validation_split.
            shuffle: boolean. Whether to shuffle the samples at each epoch.
            class_weight: dictionary mapping output names to
                class weight dictionaries.
            sample_weight: dictionary mapping output names to
                numpy arrays of sample weights.
        '''
        if 'show_accuracy' in kwargs:
            kwargs.pop('show_accuracy')
            warnings.warn('The "show_accuracy" argument is deprecated, '
                          'instead you should pass the "accuracy" metric to '
                          'the model at compile time:\n'
                          '`model.compile(optimizer, loss, '
                          'metrics=["accuracy"])`')
        if kwargs:
            raise Exception('Received unknown keyword arguments: ' +
                            str(kwargs))
        x = self._get_x(data)
        y = self._get_y(data)

        if type(validation_data) is tuple:
            raise Exception('Cannot used sample_weight with '
                            'validation data with legacy Graph model. '
                            'validation_data should be a dictionary.')
        if validation_data:
            val_x = self._get_x(validation_data)
            val_y = self._get_y(validation_data)
            validation_data = (val_x, val_y)
        return super(Graph, self).fit(x, y,
                                      batch_size=batch_size,
                                      nb_epoch=nb_epoch,
                                      verbose=verbose,
                                      callbacks=callbacks,
                                      validation_split=validation_split,
                                      validation_data=validation_data,
                                      shuffle=shuffle,
                                      class_weight=class_weight,
                                      sample_weight=sample_weight)

    def evaluate(self, data, batch_size=128,
                 verbose=0, sample_weight={}, **kwargs):
        '''Computes the loss on some input data, batch by batch.

        Returns the scalar test loss over the data,
        or a list of metrics values (starting with the test loss)
        if applicable.

        Arguments: see `fit` method.
        '''
        if 'show_accuracy' in kwargs:
            kwargs.pop('show_accuracy')
            warnings.warn('The "show_accuracy" argument is deprecated, '
                          'instead you should pass the "accuracy" metric to '
                          'the model at compile time:\n'
                          '`model.compile(optimizer, loss, '
                          'metrics=["accuracy"])`')
        if kwargs:
            raise Exception('Received unknown keyword arguments: ' +
                            str(kwargs))
        x = self._get_x(data)
        y = self._get_y(data)
        return super(Graph, self).evaluate(x, y,
                                           batch_size=batch_size,
                                           verbose=verbose,
                                           sample_weight=sample_weight)

    def predict(self, data, batch_size=128, verbose=0):
        '''Generates output predictions for the input samples
        batch by batch.

        Arguments: see `fit` method.
        '''
        x = self._get_x(data)
        output_list = super(Graph, self).predict(x, batch_size=batch_size,
                                                 verbose=verbose)
        if not isinstance(output_list, list):
            output_list = [output_list]
        return dict(zip(self._graph_outputs, output_list))

    def train_on_batch(self, data,
                       class_weight={},
                       sample_weight={}, **kwargs):
        '''Single gradient update on a batch of samples.

        Returns the scalar train loss over the data,
        or a list of metrics values (starting with the test loss)
        if applicable.

        Arguments: see `fit` method.
        '''
        if 'accuracy' in kwargs:
            kwargs.pop('accuracy')
            warnings.warn('The "accuracy" argument is deprecated, '
                          'instead you should pass the "accuracy" metric to '
                          'the model at compile time:\n'
                          '`model.compile(optimizer, loss, '
                          'metrics=["accuracy"])`')
        if kwargs:
            raise Exception('Received unknown keyword arguments: ' +
                            str(kwargs))
        x = self._get_x(data)
        y = self._get_y(data)
        return super(Graph, self).train_on_batch(x, y,
                                                 sample_weight=sample_weight,
                                                 class_weight=class_weight)

    def test_on_batch(self, data, sample_weight={}, **kwargs):
        '''Test the network on a single batch of samples.

        Returns the scalar test loss over the data,
        or a list of metrics values (starting with the test loss)
        if applicable.

        Arguments: see `fit` method.
        '''
        if 'accuracy' in kwargs:
            kwargs.pop('accuracy')
            warnings.warn('The "accuracy" argument is deprecated, '
                          'instead you should pass the "accuracy" metric to '
                          'the model at compile time:\n'
                          '`model.compile(optimizer, loss, '
                          'metrics=["accuracy"])`')
        if kwargs:
            raise Exception('Received unknown keyword arguments: ' +
                            str(kwargs))
        x = self._get_x(data)
        y = self._get_y(data)
        return super(Graph, self).test_on_batch(x, y,
                                                sample_weight=sample_weight)

    def predict_on_batch(self, data):
        output_list = super(Graph, self).predict_on_batch(data)
        if not isinstance(output_list, list):
            output_list = [output_list]
        return dict(zip(self._graph_outputs, output_list))

    def fit_generator(self, generator, samples_per_epoch, nb_epoch,
                      verbose=1, callbacks=[],
                      validation_data=None, nb_val_samples=None,
                      class_weight={},
                      max_q_size=10, **kwargs):
        '''Fits a model on data generated batch-by-batch by a Python generator.
        The generator is run in parallel to the model, for efficiency.
        For instance, this allows you to do real-time data augmentation
        on images on CPU in parallel to training your model on GPU.

        # Arguments
            generator: a generator.
                The output of the generator must be either a tuple
                of dictionaries `(input_data, sample_weight)`
                or a dictionary `input_data`
                (mapping names of inputs and outputs to Numpy arrays).
                All arrays should contain the same number of samples.
                The generator is expected to loop over its data
                indefinitely. An epoch finishes when `samples_per_epoch`
                samples have been seen by the model.
            samples_per_epoch: integer, number of samples to process before
                going to the next epoch.
            nb_epoch: integer, total number of iterations on the data.
            verbose: verbosity mode, 0, 1, or 2.
            callbacks: list of callbacks to be called during training.
            validation_data: dictionary mapping input names and outputs names
                to appropriate numpy arrays to be used as
                held-out validation data, or a generator yielding such
                dictionaries. All arrays should contain the same number
                of samples. If a generator, will be called until more than
                `nb_val_samples` examples have been generated at the
                end of every epoch. These examples will then be used
                as the validation data.
            nb_val_samples: number of samples to use from validation
                generator at the end of every epoch.
            class_weight: dictionary mapping class indices to a weight
                for the class.

        # Returns
            A `History` object.

        # Examples

        ```python
            def generate_arrays_from_file(path):
                while 1:
                    f = open(path)
                    for line in f:
                        # create numpy arrays of input data
                        # and labels, from each line in the file
                        x1, x2, y = process_line(line)
                        yield ({'input_1': x1, 'input_2': x2, 'output': y})
                    f.close()

            graph.fit_generator(generate_arrays_from_file('/my_file.txt'),
                                samples_per_epoch=10000, nb_epoch=10)
        ```
        '''
        if 'show_accuracy' in kwargs:
            kwargs.pop('show_accuracy')
            warnings.warn('The "show_accuracy" argument is deprecated, '
                          'instead you should pass the "accuracy" metric to '
                          'the model at compile time:\n'
                          '`model.compile(optimizer, loss, '
                          'metrics=["accuracy"])`')
        if 'nb_worker' in kwargs:
            kwargs.pop('nb_worker')
            warnings.warn('The "nb_worker" argument is deprecated, '
                          'please remove it from your code.')
        if 'nb_val_worker' in kwargs:
            kwargs.pop('nb_val_worker')
            warnings.warn('The "nb_val_worker" argument is deprecated, '
                          'please remove it from your code.')
        if kwargs:
            raise Exception('Received unknown keyword arguments: ' +
                            str(kwargs))

        self._train_on_batch = self.train_on_batch
        self.train_on_batch = super(Graph, self).train_on_batch
        self._evaluate = self.evaluate
        self.evaluate = super(Graph, self).evaluate

        if validation_data and type(validation_data) is tuple:
            raise Exception('Cannot use sample_weight with '
                            'validation_data in legacy Graph model.')
        if validation_data and type(validation_data) is dict:
            validation_data = (self._get_x(validation_data),
                               self._get_y(validation_data))

        original_generator = generator

        def fixed_generator():
            while 1:
                data = next(original_generator)
                if type(data) is tuple:
                    data, sample_weight = data
                    x = self._get_x(data)
                    y = self._get_y(data)
                    yield x, y, sample_weight
                else:
                    x = self._get_x(data)
                    y = self._get_y(data)
                    yield x, y

        generator = fixed_generator()
        history = super(Graph, self).fit_generator(generator,
                                                   samples_per_epoch,
                                                   nb_epoch,
                                                   verbose=verbose,
                                                   callbacks=callbacks,
                                                   validation_data=validation_data,
                                                   nb_val_samples=nb_val_samples,
                                                   class_weight=class_weight,
                                                   max_q_size=max_q_size)
        self.train_on_batch = self._train_on_batch
        self.evaluate = self._evaluate
        return history

    def evaluate_generator(self, generator, val_samples,
                           verbose=1, max_q_size=10, **kwargs):
        '''Evaluates the model on a generator. The generator should
        return the same kind of data with every yield as accepted
        by `evaluate`.

        If `show_accuracy`, it returns a tuple `(loss, accuracy)`,
        otherwise it returns the loss value.

        Arguments:
            generator:
                generator yielding dictionaries of the kind accepted
                by `evaluate`, or tuples of such dictionaries and
                associated dictionaries of sample weights.
            val_samples:
                total number of samples to generate from `generator`
                to use in validation.

            Other arguments are the same as for `fit`.
        '''
        if 'show_accuracy' in kwargs:
            kwargs.pop('show_accuracy')
            warnings.warn('The "show_accuracy" argument is deprecated, '
                          'instead you should pass the "accuracy" metric to '
                          'the model at compile time:\n'
                          '`model.compile(optimizer, loss, '
                          'metrics=["accuracy"])`')
        if 'verbose' in kwargs:
            kwargs.pop('verbose')
            warnings.warn('The "verbose" argument is deprecated.')
        if kwargs:
            raise Exception('Received unknown keyword arguments: ' +
                            str(kwargs))

        self._test_on_batch = self.test_on_batch
        self.test_on_batch = super(Graph, self).test_on_batch

        original_generator = generator

        def fixed_generator():
            while 1:
                data = next(original_generator)
                if type(data) is tuple:
                    data, sample_weight = data
                    x = self._get_x(data)
                    y = self._get_y(data)
                    yield x, y, sample_weight
                else:
                    x = self._get_x(data)
                    y = self._get_y(data)
                    yield x, y

        generator = fixed_generator()
        history = super(Graph, self).evaluate_generator(generator,
                                                        val_samples,
                                                        max_q_size=max_q_size)
        self.test_on_batch = self._test_on_batch
        return history

    # get_weights, set_weights: inherited
    def get_config(self):
        config = {'input_config': self._graph_input_config,
                  'node_config': self._graph_node_config,
                  'output_config': self._graph_output_config}
        nodes = {}
        for name, node in self._graph_nodes.items():
            nodes[name] = {'class_name': node.__class__.__name__,
                           'config': node.get_config()}
            if name in self._graph_shared_nodes_names:
                nodes[name]['shared'] = True
        config['nodes'] = nodes
        return copy.deepcopy(config)

    @classmethod
    def from_config(cls, config):
        # TODO: test legacy support
        from keras.utils.layer_utils import layer_from_config

        def normalize_legacy_config(conf):
            if 'class_name' not in conf:
                class_name = conf['name']
                name = conf.get('custom_name')
                conf['name'] = name
                new_config = {
                    'class_name': class_name,
                    'config': conf,
                }
                return new_config
            return conf

        graph = cls()
        inputs = config.get('input_config')
        for input in inputs:
            graph.add_input(**input)

        nodes = config.get('node_config')
        for node in nodes:
            layer_config = config['nodes'][node['name']]
            layer_config = normalize_legacy_config(layer_config)
            if 'layer' in node:
                # for add_shared_node
                node['layer'] = layer_from_config(node['layer'])
            else:
                layer = layer_from_config(layer_config)
                node['layer'] = layer

            node['create_output'] = False  # outputs will be added below
            if layer_config.get('shared'):
                graph.add_shared_node(**node)
            else:
                graph.add_node(**node)

        outputs = config.get('output_config')
        for output in outputs:
            graph.add_output(**output)
        return graph

    def load_weights(self, fname):
        if not self.built:
            self.build()
        super(Graph, self).load_weights(fname)


from __future__ import print_function

from .generic_utils import get_from_module
from ..layers import *
from ..models import Model, Sequential, Graph
from .. import backend as K


def layer_from_config(config, custom_objects={}):
    '''
    # Arguments
        config: dict of the form {'class_name': str, 'config': dict}
        custom_objects: dict mapping class names (or function names)
            of custom (non-Keras) objects to class/functions

    # Returns
        Layer instance (may be Model, Sequential, Graph, Layer...)
    '''
    # Insert custom layers into globals so they can
    # be accessed by `get_from_module`.
    for cls_key in custom_objects:
        globals()[cls_key] = custom_objects[cls_key]

    class_name = config['class_name']

    if class_name == 'Sequential':
        layer_class = Sequential
    elif class_name == 'Graph':
        layer_class = Graph
    elif class_name in ['Model', 'Container']:
        layer_class = Model
    else:
        layer_class = get_from_module(class_name, globals(), 'layer',
                                      instantiate=False)
    return layer_class.from_config(config['config'])


def print_summary(layers, relevant_nodes=None):
    line_length = 100  # total length of printed lines
    positions = [35, 55, 67, 100]  # absolute positions of log elements in each line
    # header names for the different log elements
    to_display = ['Layer (type)', 'Output Shape', 'Param #', 'Connected to']

    def print_row(fields, positions):
        line = ''
        for i in range(len(fields)):
            line += str(fields[i])
            line = line[:positions[i]]
            line += ' ' * (positions[i] - len(line))
        print(line)

    print('_' * line_length)
    print_row(to_display, positions)
    print('=' * line_length)

    def print_layer_summary(layer):
        try:
            output_shape = layer.output_shape
        except:
            output_shape = 'multiple'
        connections = []
        for node_index, node in enumerate(layer.inbound_nodes):
            if relevant_nodes:
                node_key = layer.name + '_ib-' + str(node_index)
                if node_key not in relevant_nodes:
                    # node is node part of the current network
                    continue
            for i in range(len(node.inbound_layers)):
                inbound_layer = node.inbound_layers[i].name
                inbound_node_index = node.node_indices[i]
                inbound_tensor_index = node.tensor_indices[i]
                connections.append(inbound_layer + '[' + str(inbound_node_index) + '][' + str(inbound_tensor_index) + ']')

        name = layer.name
        cls_name = layer.__class__.__name__
        if not connections:
            first_connection = ''
        else:
            first_connection = connections[0]
        fields = [name + ' (' + cls_name + ')', output_shape, layer.count_params(), first_connection]
        print_row(fields, positions)
        if len(connections) > 1:
            for i in range(1, len(connections)):
                fields = ['', '', '', connections[i]]
                print_row(fields, positions)

    total_params = 0
    for i in range(len(layers)):
        print_layer_summary(layers[i])
        if i == len(layers) - 1:
            print('=' * line_length)
        else:
            print('_' * line_length)
        total_params += layers[i].count_params()

    print('Total params: %s' % total_params)
    print('_' * line_length)

from __future__ import absolute_import
import numpy as np
import time
import sys
import six


def get_from_module(identifier, module_params, module_name,
                    instantiate=False, kwargs=None):
    if isinstance(identifier, six.string_types):
        res = module_params.get(identifier)
        if not res:
            raise Exception('Invalid ' + str(module_name) + ': ' +
                            str(identifier))
        if instantiate and not kwargs:
            return res()
        elif instantiate and kwargs:
            return res(**kwargs)
        else:
            return res
    elif type(identifier) is dict:
        name = identifier.pop('name')
        res = module_params.get(name)
        if res:
            return res(**identifier)
        else:
            raise Exception('Invalid ' + str(module_name) + ': ' +
                            str(identifier))
    return identifier


def make_tuple(*args):
    return args


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
                self.sum_values[k] = [v * (current - self.seen_so_far), current - self.seen_so_far]
                self.unique_values.append(k)
            else:
                self.sum_values[k][0] += v * (current - self.seen_so_far)
                self.sum_values[k][1] += (current - self.seen_so_far)
        self.seen_so_far = current

        now = time.time()
        if self.verbose == 1:
            prev_total_width = self.total_width
            sys.stdout.write("\b" * prev_total_width)
            sys.stdout.write("\r")

            numdigits = int(np.floor(np.log10(self.target))) + 1
            barstr = '%%%dd/%%%dd [' % (numdigits, numdigits)
            bar = barstr % (current, self.target)
            prog = float(current) / self.target
            prog_width = int(self.width * prog)
            if prog_width > 0:
                bar += ('=' * (prog_width-1))
                if current < self.target:
                    bar += '>'
                else:
                    bar += '='
            bar += ('.' * (self.width - prog_width))
            bar += ']'
            sys.stdout.write(bar)
            self.total_width = len(bar)

            if current:
                time_per_unit = (now - self.start) / current
            else:
                time_per_unit = 0
            eta = time_per_unit * (self.target - current)
            info = ''
            if current < self.target:
                info += ' - ETA: %ds' % eta
            else:
                info += ' - %ds' % (now - self.start)
            for k in self.unique_values:
                info += ' - %s:' % k
                if type(self.sum_values[k]) is list:
                    avg = self.sum_values[k][0] / max(1, self.sum_values[k][1])
                    if abs(avg) > 1e-3:
                        info += ' %.4f' % avg
                    else:
                        info += ' %.4e' % avg
                else:
                    info += ' %s' % self.sum_values[k]

            self.total_width += len(info)
            if prev_total_width > self.total_width:
                info += ((prev_total_width - self.total_width) * " ")

            sys.stdout.write(info)
            sys.stdout.flush()

            if current >= self.target:
                sys.stdout.write("\n")

        if self.verbose == 2:
            if current >= self.target:
                info = '%ds' % (now - self.start)
                for k in self.unique_values:
                    info += ' - %s:' % k
                    avg = self.sum_values[k][0] / max(1, self.sum_values[k][1])
                    if avg > 1e-3:
                        info += ' %.4f' % avg
                    else:
                        info += ' %.4e' % avg
                sys.stdout.write(info + "\n")

    def add(self, n, values=[]):
        self.update(self.seen_so_far + n, values)


def display_table(rows, positions):

    def display_row(objects, positions):
        line = ''
        for i in range(len(objects)):
            line += str(objects[i])
            line = line[:positions[i]]
            line += ' ' * (positions[i] - len(line))
        print(line)

    for objects in rows:
        display_row(objects, positions)


try:
    # pydot-ng is a fork of pydot that is better maintained
    import pydot_ng as pydot
except ImportError:
    # fall back on pydot if necessary
    import pydot
if not pydot.find_graphviz():
    raise RuntimeError('Failed to import pydot. You must install pydot'
                       ' and graphviz for `pydotprint` to work.')


def model_to_dot(model, show_shapes=False):
    dot = pydot.Dot()
    dot.set('rankdir', 'TB')
    dot.set('concentrate', True)
    dot.set_node_defaults(shape='record')

    if model.__class__.__name__ == 'Sequential':
        if not model.built:
            model.build()
        model = model.model
    layers = model.layers

    # first, populate the nodes of the graph
    for layer in layers:
        layer_id = str(id(layer))
        label = str(layer.name) + ' (' + layer.__class__.__name__ + ')'

        if show_shapes:
            # Build the label that will actually contain a table with the
            # input/output
            try:
                outputlabels = str(layer.output_shape)
            except:
                outputlabels = 'multiple'
            if hasattr(layer, 'input_shape'):
                inputlabels = str(layer.input_shape)
            elif hasattr(layer, 'input_shapes'):
                inputlabels = ', '.join(
                    [str(ishape) for ishape in layer.input_shapes])
            else:
                inputlabels = 'multiple'
            label = '%s\n|{input:|output:}|{{%s}|{%s}}' % (label, inputlabels, outputlabels)

        node = pydot.Node(layer_id, label=label)
        dot.add_node(node)

    # second, add the edges
    for layer in layers:
        layer_id = str(id(layer))
        for i, node in enumerate(layer.inbound_nodes):
            node_key = layer.name + '_ib-' + str(i)
            if node_key in model.container_nodes:
                # add edges
                for inbound_layer in node.inbound_layers:
                    inbound_layer_id = str(id(inbound_layer))
                    layer_id = str(id(layer))
                    dot.add_edge(pydot.Edge(inbound_layer_id, layer_id))
    return dot


def plot(model, to_file='model.png', show_shapes=False):
    dot = model_to_dot(model, show_shapes)
    dot.write_png(to_file)

from __future__ import absolute_import
from __future__ import print_function

import tarfile
import os
import sys
import shutil
from six.moves.urllib.request import urlopen
from six.moves.urllib.error import URLError, HTTPError

from ..utils.generic_utils import Progbar


# Under Python 2, 'urlretrieve' relies on FancyURLopener from legacy
# urllib module, known to have issues with proxy management
if sys.version_info[0] == 2:
    def urlretrieve(url, filename, reporthook=None, data=None):
        def chunk_read(response, chunk_size=8192, reporthook=None):
            total_size = response.info().get('Content-Length').strip()
            total_size = int(total_size)
            count = 0
            while 1:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                count += 1
                if reporthook:
                    reporthook(count, chunk_size, total_size)
                yield chunk

        response = urlopen(url, data)
        with open(filename, 'wb') as fd:
            for chunk in chunk_read(response, reporthook=reporthook):
                fd.write(chunk)
else:
    from six.moves.urllib.request import urlretrieve


def get_file(fname, origin, untar=False):
    datadir_base = os.path.expanduser(os.path.join('~', '.keras'))
    if not os.access(datadir_base, os.W_OK):
        datadir_base = os.path.join('/tmp', '.keras')
    datadir = os.path.join(datadir_base, 'datasets')
    if not os.path.exists(datadir):
        os.makedirs(datadir)

    if untar:
        untar_fpath = os.path.join(datadir, fname)
        fpath = untar_fpath + '.tar.gz'
    else:
        fpath = os.path.join(datadir, fname)

    if not os.path.exists(fpath):
        print('Downloading data from',  origin)
        global progbar
        progbar = None

        def dl_progress(count, block_size, total_size):
            global progbar
            if progbar is None:
                progbar = Progbar(total_size)
            else:
                progbar.update(count*block_size)

        error_msg = 'URL fetch failure on {}: {} -- {}'
        try:
            try:
                urlretrieve(origin, fpath, dl_progress)
            except URLError as e:
                raise Exception(error_msg.format(origin, e.errno, e.reason))
            except HTTPError as e:
                raise Exception(error_msg.format(origin, e.code, e.msg))
        except (Exception, KeyboardInterrupt) as e:
            if os.path.exists(fpath):
                os.remove(fpath)
            raise
        progbar = None

    if untar:
        if not os.path.exists(untar_fpath):
            print('Untaring file...')
            tfile = tarfile.open(fpath, 'r:gz')
            try:
                tfile.extractall(path=datadir)
            except (Exception, KeyboardInterrupt) as e:
                if os.path.exists(untar_fpath):
                    if os.path.isfile(untar_fpath):
                        os.remove(untar_fpath)
                    else:
                        shutil.rmtree(untar_fpath)
                raise
            tfile.close()
        return untar_fpath

    return fpath

from __future__ import absolute_import
import h5py
import numpy as np
from collections import defaultdict


class HDF5Matrix():
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
    a = np.empty(shape=array.shape, dtype=array.dtype)
    a[:] = array[:]
    f.close()
    return a

from __future__ import absolute_import
import numpy as np
import scipy as sp
from six.moves import range
from six.moves import zip


def to_categorical(y, nb_classes=None):
    '''Convert class vector (integers from 0 to nb_classes)
    to binary class matrix, for use with categorical_crossentropy.
    '''
    if not nb_classes:
        nb_classes = np.max(y)+1
    Y = np.zeros((len(y), nb_classes))
    for i in range(len(y)):
        Y[i, y[i]] = 1.
    return Y


def normalize(a, axis=-1, order=2):
    l2 = np.atleast_1d(np.linalg.norm(a, order, axis))
    l2[l2 == 0] = 1
    return a / np.expand_dims(l2, axis)


def binary_logloss(p, y):
    epsilon = 1e-15
    p = sp.maximum(epsilon, p)
    p = sp.minimum(1-epsilon, p)
    res = sum(y * sp.log(p) + sp.subtract(1, y) * sp.log(sp.subtract(1, p)))
    res *= -1.0/len(y)
    return res


def multiclass_logloss(P, Y):
    npreds = [P[i][Y[i]-1] for i in range(len(Y))]
    score = -(1. / len(Y)) * np.sum(np.log(npreds))
    return score


def accuracy(p, y):
    return np.mean([a == b for a, b in zip(p, y)])


def probas_to_classes(y_pred):
    if len(y_pred.shape) > 1 and y_pred.shape[1] > 1:
        return categorical_probas_to_classes(y_pred)
    return np.array([1 if p > 0.5 else 0 for p in y_pred])


def categorical_probas_to_classes(p):
    return np.argmax(p, axis=1)


def convert_kernel(kernel, dim_ordering='th'):
    '''Converts a kernel matrix (numpy array)
    from Theano format to TensorFlow format
    (or reciprocally, since the transformation
    is its own inverse).
    '''
    new_kernel = np.copy(kernel)
    if dim_ordering == 'th':
        w = kernel.shape[2]
        h = kernel.shape[3]
        for i in range(w):
            for j in range(h):
                new_kernel[:, :, i, j] = kernel[:, :, w - i - 1, h - j - 1]
    elif dim_ordering == 'tf':
        w = kernel.shape[0]
        h = kernel.shape[1]
        for i in range(w):
            for j in range(h):
                new_kernel[i, j, :, :] = kernel[w - i - 1, h - j - 1, :, :]
    else:
        raise Exception('Invalid dim_ordering: ' + str(dim_ordering))
    return new_kernel

from __future__ import absolute_import
from __future__ import print_function
import os
import json
import sys
from .common import epsilon
from .common import floatx
from .common import set_epsilon
from .common import set_floatx
from .common import get_uid
from .common import cast_to_floatx

_keras_base_dir = os.path.expanduser('~')
if not os.access(_keras_base_dir, os.W_OK):
    _keras_base_dir = '/tmp'

_keras_dir = os.path.join(_keras_base_dir, '.keras')
if not os.path.exists(_keras_dir):
    os.makedirs(_keras_dir)

_BACKEND = 'theano'
_config_path = os.path.expanduser(os.path.join(_keras_dir, 'keras.json'))
if os.path.exists(_config_path):
    _config = json.load(open(_config_path))
    _floatx = _config.get('floatx', floatx())
    assert _floatx in {'float16', 'float32', 'float64'}
    _epsilon = _config.get('epsilon', epsilon())
    assert type(_epsilon) == float
    _backend = _config.get('backend', _BACKEND)
    assert _backend in {'theano', 'tensorflow'}

    set_floatx(_floatx)
    set_epsilon(_epsilon)
    _BACKEND = _backend
else:
    # save config file, for easy edition
    _config = {'floatx': floatx(),
               'epsilon': epsilon(),
               'backend': _BACKEND}
    with open(_config_path, 'w') as f:
        # add new line in order for bash 'cat' display the content correctly
        f.write(json.dumps(_config) + '\n')

if 'KERAS_BACKEND' in os.environ:
    _backend = os.environ['KERAS_BACKEND']
    assert _backend in {'theano', 'tensorflow'}
    _BACKEND = _backend

if _BACKEND == 'theano':
    sys.stderr.write('Using Theano backend.\n')
    from .theano_backend import *
elif _BACKEND == 'tensorflow':
    sys.stderr.write('Using TensorFlow backend.\n')
    from .tensorflow_backend import *
else:
    raise Exception('Unknown backend: ' + str(_BACKEND))

import theano
from theano import tensor as T
from theano.sandbox.rng_mrg import MRG_RandomStreams as RandomStreams
from theano.tensor.signal import pool
from theano.tensor.nnet import conv3d2d
from theano.sandbox import softsign as T_softsign
import inspect
import numpy as np
from .common import _FLOATX, _EPSILON


# INTERNAL UTILS
theano.config.floatX = _FLOATX
_LEARNING_PHASE = T.scalar(dtype='uint8', name='keras_learning_phase')  # 0 = test, 1 = train


def learning_phase():
    # False = test, True = train
    return _LEARNING_PHASE


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
    else:
        shape = tuple([None for _ in range(ndim)])

    broadcast = (False,) * ndim
    x = T.TensorType(dtype, broadcast)(name)
    x._keras_shape = shape
    x._uses_learning_phase = False
    return x


def shape(x):
    '''Return the shape of a tensor.

    Warning: type returned will be different for
    Theano backend (Theano tensor type) and TF backend (TF TensorShape).
    '''
    return x.shape


def ndim(x):
    return x.ndim


def dtype(x):
    return x.dtype


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


def eye(size, dtype=_FLOATX, name=None):
    '''Instantiate an identity matrix.
    '''
    return variable(np.eye(size), dtype, name)


def ones_like(x):
    return T.ones_like(x)


def zeros_like(x):
    return T.zeros_like(x)


def count_params(x):
    '''Return number of scalars in a tensor.

    Return: numpy integer.
    '''
    return np.prod(x.shape.eval())


def cast(x, dtype):
    return T.cast(x, dtype)


# LINEAR ALGEBRA

'''
Assumed overridden:
+, -, /, *, +=, -=, *=, /=
'''


def dot(x, y):
    return T.dot(x, y)


def batch_dot(x, y, axes=None):
    '''batchwise dot product
    batch_dot results in a tensor with less dimensions than the input.
    If the number of dimensions is reduced to 1, we use `expand_dims` to
    make sure that ndim is at least 2.

    # Example
        Assume x = [[1, 2]   and y = [[5, 6]
                    [3, 4]]           [7, 8]]
        batch_dot(x, y, axes=1) = [[17, 53]] which is the main diagonal
        of x.dot(y.T), although we never have to calculate the off-diagonal
        elements.


    # Arguments
        x, y: tensors with ndim >= 2
        axes: list (or single) int with target dimensions

    # Returns
        Tensor with ndim >= 2
    '''
    if type(axes) == int:
        axes = (axes, axes)
    if axes is None:
        # behaves like tf.batch_matmul as default
        axes = [x.ndim - 1, y.ndim - 2]
    out = T.batched_tensordot(x, y, axes=axes)
    if ndim(out) == 1:
        out = expand_dims(out, 1)
    return out


def transpose(x):
    return T.transpose(x)


def gather(reference, indices):
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


def prod(x, axis=None, keepdims=False):
    '''Multiply the values in a tensor, alongside the specified axis.
    '''
    return T.prod(x, axis=axis, keepdims=keepdims)


def mean(x, axis=None, keepdims=False):
    dtype = None
    if 'int' in x.dtype:
        dtype = _FLOATX
    return T.mean(x, axis=axis, keepdims=keepdims, dtype=dtype)


def std(x, axis=None, keepdims=False):
    return T.std(x, axis=axis, keepdims=keepdims)


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


def sign(x):
    return T.sgn(x)


def pow(x, a):
    return T.pow(x, a)


def clip(x, min_value, max_value):
    if max_value < min_value:
        max_value = min_value
    return T.clip(x, min_value, max_value)


def equal(x, y):
    return T.eq(x, y)


def not_equal(x, y):
    return T.neq(x, y)


def maximum(x, y):
    return T.maximum(x, y)


def minimum(x, y):
    return T.minimum(x, y)


def sin(x):
    return T.sin(x)


def cos(x):
    return T.cos(x)


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


def repeat_elements(x, rep, axis):
    '''Repeat the elements of a tensor along an axis, like np.repeat.

    If x has shape (s1, s2, s3) and axis=1, the output
    will have shape (s1, s2 * rep, s3).
    '''
    return T.repeat(x, rep, axis=axis)


def resize_images(X, height_factor, width_factor, dim_ordering):
    '''Resize the images contained in a 4D tensor of shape
    - [batch, channels, height, width] (for 'th' dim_ordering)
    - [batch, height, width, channels] (for 'tf' dim_ordering)
    by a factor of (height_factor, width_factor). Both factors should be
    positive integers.
    '''
    if dim_ordering == 'th':
        output = repeat_elements(X, height_factor, axis=2)
        output = repeat_elements(output, width_factor, axis=3)
        return output
    elif dim_ordering == 'tf':
        output = repeat_elements(X, height_factor, axis=1)
        output = repeat_elements(output, width_factor, axis=2)
        return output
    else:
        raise Exception('Invalid dim_ordering: ' + dim_ordering)


def resize_volumes(X, depth_factor, height_factor, width_factor, dim_ordering):
    '''Resize the volume contained in a 5D tensor of shape
    - [batch, channels, depth, height, width] (for 'th' dim_ordering)
    - [batch, depth, height, width, channels] (for 'tf' dim_ordering)
    by a factor of (depth_factor, height_factor, width_factor).
    Both factors should be positive integers.
    '''
    if dim_ordering == 'th':
        output = repeat_elements(X, depth_factor, axis=2)
        output = repeat_elements(output, height_factor, axis=3)
        output = repeat_elements(output, width_factor, axis=4)
        return output
    elif dim_ordering == 'tf':
        output = repeat_elements(X, depth_factor, axis=1)
        output = repeat_elements(output, height_factor, axis=2)
        output = repeat_elements(output, width_factor, axis=3)
        return output
    else:
        raise Exception('Invalid dim_ordering: ' + dim_ordering)


def repeat(x, n):
    '''Repeat a 2D tensor.

    If x has shape (samples, dim) and n=2,
    the output will have shape (samples, 2, dim).
    '''
    assert x.ndim == 2
    x = x.dimshuffle((0, 'x', 1))
    return T.extra_ops.repeat(x, n, axis=1)


def tile(x, n):
    return T.tile(x, n)


def flatten(x):
    return T.flatten(x)


def batch_flatten(x):
    '''Turn a n-D tensor into a 2D tensor where
    the first dimension is conserved.
    '''
    x = T.reshape(x, (x.shape[0], T.prod(x.shape) // x.shape[0]))
    return x


def expand_dims(x, dim=-1):
    '''Add a 1-sized dimension at index "dim".
    '''
    pattern = [i for i in range(x.type.ndim)]
    if dim < 0:
        if x.type.ndim == 0:
            dim = 0
        else:
            dim = dim % x.type.ndim + 1
    pattern.insert(dim, 'x')
    return x.dimshuffle(pattern)


def squeeze(x, axis):
    '''Remove a 1-dimension from the tensor at index "axis".
    '''
    x = T.addbroadcast(x, axis)
    return T.squeeze(x)


def temporal_padding(x, padding=1):
    '''Pad the middle dimension of a 3D tensor
    with "padding" zeros left and right.

    Appologies for the inane API, but Theano makes this
    really hard.
    '''
    input_shape = x.shape
    output_shape = (input_shape[0],
                    input_shape[1] + 2 * padding,
                    input_shape[2])
    output = T.zeros(output_shape)
    return T.set_subtensor(output[:, padding:x.shape[1] + padding, :], x)


def spatial_2d_padding(x, padding=(1, 1), dim_ordering='th'):
    '''Pad the 2nd and 3rd dimensions of a 4D tensor
    with "padding[0]" and "padding[1]" (resp.) zeros left and right.
    '''
    input_shape = x.shape
    if dim_ordering == 'th':
        output_shape = (input_shape[0],
                        input_shape[1],
                        input_shape[2] + 2 * padding[0],
                        input_shape[3] + 2 * padding[1])
        output = T.zeros(output_shape)
        indices = (slice(None),
                   slice(None),
                   slice(padding[0], input_shape[2] + padding[0]),
                   slice(padding[1], input_shape[3] + padding[1]))

    elif dim_ordering == 'tf':
        output_shape = (input_shape[0],
                        input_shape[1] + 2 * padding[0],
                        input_shape[2] + 2 * padding[1],
                        input_shape[3])
        output = T.zeros(output_shape)
        indices = (slice(None),
                   slice(padding[0], input_shape[1] + padding[0]),
                   slice(padding[1], input_shape[2] + padding[1]),
                   slice(None))
    else:
        raise Exception('Invalid dim_ordering: ' + dim_ordering)
    return T.set_subtensor(output[indices], x)


def spatial_3d_padding(x, padding=(1, 1, 1), dim_ordering='th'):
    '''Pad the 2nd, 3rd and 4th dimensions of a 5D tensor
    with "padding[0]", "padding[1]" and "padding[2]" (resp.) zeros left and right.
    '''
    input_shape = x.shape
    if dim_ordering == 'th':
        output_shape = (input_shape[0],
                        input_shape[1],
                        input_shape[2] + 2 * padding[0],
                        input_shape[3] + 2 * padding[1],
                        input_shape[4] + 2 * padding[2])
        output = T.zeros(output_shape)
        indices = (slice(None),
                   slice(None),
                   slice(padding[0], input_shape[2] + padding[0]),
                   slice(padding[1], input_shape[3] + padding[1]),
                   slice(padding[2], input_shape[4] + padding[2]))

    elif dim_ordering == 'tf':
        output_shape = (input_shape[0],
                        input_shape[1] + 2 * padding[0],
                        input_shape[2] + 2 * padding[1],
                        input_shape[3] + 2 * padding[2],
                        input_shape[4])
        output = T.zeros(output_shape)
        indices = (slice(None),
                   slice(padding[0], input_shape[1] + padding[0]),
                   slice(padding[1], input_shape[2] + padding[1]),
                   slice(padding[2], input_shape[3] + padding[2]),
                   slice(None))
    else:
        raise Exception('Invalid dim_ordering: ' + dim_ordering)
    return T.set_subtensor(output[indices], x)


def pack(x):
    return T.stack(*x)

# VALUE MANIPULATION


def get_value(x):
    if not hasattr(x, 'get_value'):
        raise Exception("'get_value() can only be called on a variable. " +
                        "If you have an expression instead, use eval().")
    return x.get_value()


def batch_get_value(xs):
    '''Returns the value of more than one tensor variable,
    as a list of Numpy arrays.
    '''
    return [get_value(x) for x in xs]


def set_value(x, value):
    x.set_value(np.asarray(value, dtype=x.dtype))


def batch_set_value(tuples):
    for x, value in tuples:
        x.set_value(np.asarray(value, dtype=x.dtype))


# GRAPH MANIPULATION

class Function(object):

    def __init__(self, inputs, outputs, updates=[], **kwargs):
        self.function = theano.function(inputs, outputs, updates=updates,
                                        allow_input_downcast=True,
                                        on_unused_input='warn',
                                        **kwargs)

    def __call__(self, inputs):
        assert type(inputs) in {list, tuple}
        return self.function(*inputs)


def function(inputs, outputs, updates=[], **kwargs):
    if len(kwargs) > 0:
        function_args = inspect.getargspec(theano.function)[0]
        for key in kwargs.keys():
            if key not in function_args:
                msg = "Invalid argument '%s' passed to K.function" % key
                raise ValueError(msg)
    return Function(inputs, outputs, updates=updates, **kwargs)


def gradients(loss, variables):
    return T.grad(loss, variables)


# CONTROL FLOW

def rnn(step_function, inputs, initial_states,
        go_backwards=False, mask=None, constants=None,
        unroll=False, input_length=None):
    '''Iterates over the time dimension of a tensor.

    # Arguments
        inputs: tensor of temporal data of shape (samples, time, ...)
            (at least 3D).
        step_function:
            Parameters:
                input: tensor with shape (samples, ...) (no time dimension),
                    representing input for the batch of samples at a certain
                    time step.
                states: list of tensors.
            Returns:
                output: tensor with shape (samples, ...) (no time dimension),
                new_states: list of tensors, same length and shapes
                    as 'states'.
        initial_states: tensor with shape (samples, ...) (no time dimension),
            containing the initial values for the states used in
            the step function.
        go_backwards: boolean. If True, do the iteration over
            the time dimension in reverse order.
        mask: binary tensor with shape (samples, time),
            with a zero for every element that is masked.
        constants: a list of constant values passed at each step.
        unroll: whether to unroll the RNN or to use a symbolic loop (`scan`).
        input_length: must be specified if using `unroll`.

    # Returns
        A tuple (last_output, outputs, new_states).
            last_output: the latest output of the rnn, of shape (samples, ...)
            outputs: tensor with shape (samples, time, ...) where each
                entry outputs[s, t] is the output of the step function
                at time t for sample s.
            new_states: list of tensors, latest states returned by
                the step function, of shape (samples, ...).
    '''
    ndim = inputs.ndim
    assert ndim >= 3, 'Input should be at least 3D.'

    if unroll:
        if input_length is None:
            raise Exception('When specifying `unroll=True`, an `input_length` '
                            'must be provided to `rnn`.')

    axes = [1, 0] + list(range(2, ndim))
    inputs = inputs.dimshuffle(axes)

    if constants is None:
        constants = []

    if mask is not None:
        if mask.ndim == ndim-1:
            mask = expand_dims(mask)
        assert mask.ndim == ndim
        mask = mask.dimshuffle(axes)

        if unroll:
            indices = list(range(input_length))
            if go_backwards:
                indices = indices[::-1]

            successive_outputs = []
            successive_states = []
            states = initial_states
            for i in indices:
                output, new_states = step_function(inputs[i], states + constants)

                if len(successive_outputs) == 0:
                    prev_output = zeros_like(output)
                else:
                    prev_output = successive_outputs[-1]

                output = T.switch(mask[i], output, prev_output)
                kept_states = []
                for state, new_state in zip(states, new_states):
                    kept_states.append(T.switch(mask[i], new_state, state))
                states = kept_states

                successive_outputs.append(output)
                successive_states.append(states)

            outputs = T.stack(*successive_outputs)
            states = []
            for i in range(len(successive_states[-1])):
                states.append(T.stack(*[states_at_step[i] for states_at_step in successive_states]))
        else:
            # build an all-zero tensor of shape (samples, output_dim)
            initial_output = step_function(inputs[0], initial_states + constants)[0] * 0
            # Theano gets confused by broadcasting patterns in the scan op
            initial_output = T.unbroadcast(initial_output, 0, 1)

            def _step(input, mask, output_tm1, *states):
                output, new_states = step_function(input, states)
                # output previous output if masked.
                output = T.switch(mask, output, output_tm1)
                return_states = []
                for state, new_state in zip(states, new_states):
                    return_states.append(T.switch(mask, new_state, state))
                return [output] + return_states

            results, _ = theano.scan(
                _step,
                sequences=[inputs, mask],
                outputs_info=[initial_output] + initial_states,
                non_sequences=constants,
                go_backwards=go_backwards)

            # deal with Theano API inconsistency
            if type(results) is list:
                outputs = results[0]
                states = results[1:]
            else:
                outputs = results
                states = []
    else:
        if unroll:
            indices = list(range(input_length))
            if go_backwards:
                indices = indices[::-1]

            successive_outputs = []
            successive_states = []
            states = initial_states
            for i in indices:
                output, states = step_function(inputs[i], states + constants)
                successive_outputs.append(output)
                successive_states.append(states)
            outputs = T.stack(*successive_outputs)
            states = []
            for i in range(len(successive_states[-1])):
                states.append(T.stack(*[states_at_step[i] for states_at_step in successive_states]))

        else:
            def _step(input, *states):
                output, new_states = step_function(input, states)
                return [output] + new_states

            results, _ = theano.scan(
                _step,
                sequences=inputs,
                outputs_info=[None] + initial_states,
                non_sequences=constants,
                go_backwards=go_backwards)

            # deal with Theano API inconsistency
            if type(results) is list:
                outputs = results[0]
                states = results[1:]
            else:
                outputs = results
                states = []

    outputs = T.squeeze(outputs)
    last_output = outputs[-1]

    axes = [1, 0] + list(range(2, outputs.ndim))
    outputs = outputs.dimshuffle(axes)
    states = [T.squeeze(state[-1]) for state in states]
    return last_output, outputs, states


def switch(condition, then_expression, else_expression):
    '''condition: scalar tensor.
    '''
    return T.switch(condition, then_expression, else_expression)


def in_train_phase(x, alt):
    x = T.switch(_LEARNING_PHASE, x, alt)
    x._uses_learning_phase = True
    return x


def in_test_phase(x, alt):
    x = T.switch(_LEARNING_PHASE, alt, x)
    x._uses_learning_phase = True
    return x


# NN OPERATIONS

def relu(x, alpha=0., max_value=None):
    assert hasattr(T.nnet, 'relu'), ('It looks like like your version of '
                                     'Theano is out of date. '
                                     'Install the latest version with:\n'
                                     'pip install git+git://github.com/Theano/Theano.git --upgrade --no-deps')
    x = T.nnet.relu(x, alpha)
    if max_value is not None:
        x = T.minimum(x, max_value)
    return x


def softmax(x):
    return T.nnet.softmax(x)


def softplus(x):
    return T.nnet.softplus(x)


def softsign(x):
    return T_softsign.softsign(x)


def categorical_crossentropy(output, target, from_logits=False):
    if from_logits:
        output = T.nnet.softmax(output)
    else:
        # scale preds so that the class probas of each sample sum to 1
        output /= output.sum(axis=-1, keepdims=True)
    # avoid numerical instability with _EPSILON clipping
    output = T.clip(output, _EPSILON, 1.0 - _EPSILON)
    return T.nnet.categorical_crossentropy(output, target)


def sparse_categorical_crossentropy(output, target, from_logits=False):
    target = T.cast(T.flatten(target), 'int32')
    target = T.extra_ops.to_one_hot(target, nb_class=output.shape[-1])
    target = reshape(target, shape(output))
    return categorical_crossentropy(output, target, from_logits)


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


def l2_normalize(x, axis):
    norm = T.sqrt(T.sum(T.square(x), axis=axis, keepdims=True))
    return x / norm


# CONVOLUTIONS

def conv2d(x, kernel, strides=(1, 1), border_mode='valid', dim_ordering='th',
           image_shape=None, filter_shape=None):
    '''
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
        if image_shape:
            image_shape = (image_shape[0], image_shape[3],
                           image_shape[1], image_shape[2])
        if filter_shape:
            filter_shape = (filter_shape[3], filter_shape[2],
                            filter_shape[0], filter_shape[1])

    if border_mode == 'same':
        th_border_mode = 'half'
        np_kernel = kernel.eval()
    elif border_mode == 'valid':
        th_border_mode = 'valid'
    else:
        raise Exception('Border mode not supported: ' + str(border_mode))

    # Theano might not accept long type
    def int_or_none(value):
        try:
            return int(value)
        except TypeError:
            return None

    if image_shape is not None:
        image_shape = tuple(int_or_none(v) for v in image_shape)

    if filter_shape is not None:
        filter_shape = tuple(int_or_none(v) for v in filter_shape)

    conv_out = T.nnet.conv2d(x, kernel,
                             border_mode=th_border_mode,
                             subsample=strides,
                             input_shape=image_shape,
                             filter_shape=filter_shape)

    if border_mode == 'same':
        if np_kernel.shape[2] % 2 == 0:
            conv_out = conv_out[:, :, :(x.shape[2] + strides[0] - 1) // strides[0], :]
        if np_kernel.shape[3] % 2 == 0:
            conv_out = conv_out[:, :, :, :(x.shape[3] + strides[1] - 1) // strides[1]]

    if dim_ordering == 'tf':
        conv_out = conv_out.dimshuffle((0, 2, 3, 1))
    return conv_out


def conv3d(x, kernel, strides=(1, 1, 1),
           border_mode='valid', dim_ordering='th',
           volume_shape=None, filter_shape=None):
    '''
    Run on cuDNN if available.
    border_mode: string, "same" or "valid".
    '''
    if dim_ordering not in {'th', 'tf'}:
        raise Exception('Unknown dim_ordering ' + str(dim_ordering))

    if border_mode not in {'same', 'valid'}:
        raise Exception('Invalid border mode: ' + str(border_mode))

    if dim_ordering == 'tf':
        # TF uses the last dimension as channel dimension,
        # instead of the 2nd one.
        # TH input shape: (samples, input_depth, conv_dim1, conv_dim2, conv_dim3)
        # TF input shape: (samples, conv_dim1, conv_dim2, conv_dim3, input_depth)
        # TH kernel shape: (out_depth, input_depth, kernel_dim1, kernel_dim2, kernel_dim3)
        # TF kernel shape: (kernel_dim1, kernel_dim2, kernel_dim3, input_depth, out_depth)
        x = x.dimshuffle((0, 4, 1, 2, 3))
        kernel = kernel.dimshuffle((4, 3, 0, 1, 2))
        if volume_shape:
            volume_shape = (volume_shape[0], volume_shape[4],
                            volume_shape[1], volume_shape[2], volume_shape[3])
        if filter_shape:
            filter_shape = (filter_shape[4], filter_shape[3],
                            filter_shape[0], filter_shape[1], filter_shape[2])

    if border_mode == 'same':
        assert(strides == (1, 1, 1))
        pad_dim1 = (kernel.shape[2] - 1)
        pad_dim2 = (kernel.shape[3] - 1)
        pad_dim3 = (kernel.shape[4] - 1)
        output_shape = (x.shape[0], x.shape[1],
                        x.shape[2] + pad_dim1,
                        x.shape[3] + pad_dim2,
                        x.shape[4] + pad_dim3)
        output = T.zeros(output_shape)
        indices = (slice(None), slice(None),
                   slice(pad_dim1 // 2, x.shape[2] + pad_dim1 // 2),
                   slice(pad_dim2 // 2, x.shape[3] + pad_dim2 // 2),
                   slice(pad_dim3 // 2, x.shape[4] + pad_dim3 // 2))
        x = T.set_subtensor(output[indices], x)
        border_mode = 'valid'

    border_mode_3d = (border_mode, border_mode, border_mode)
    conv_out = conv3d2d.conv3d(signals=x.dimshuffle(0, 2, 1, 3, 4),
                               filters=kernel.dimshuffle(0, 2, 1, 3, 4),
                               border_mode=border_mode_3d)
    conv_out = conv_out.dimshuffle(0, 2, 1, 3, 4)

    # support strides by manually slicing the output
    if strides != (1, 1, 1):
        conv_out = conv_out[:, :, ::strides[0], ::strides[1], ::strides[2]]

    if dim_ordering == 'tf':
        conv_out = conv_out.dimshuffle((0, 2, 3, 4, 1))

    return conv_out


def pool2d(x, pool_size, strides=(1, 1), border_mode='valid',
           dim_ordering='th', pool_mode='max'):
    if border_mode == 'same':
        w_pad = pool_size[0] - 2 if pool_size[0] % 2 == 1 else pool_size[0] - 1
        h_pad = pool_size[1] - 2 if pool_size[1] % 2 == 1 else pool_size[1] - 1
        padding = (w_pad, h_pad)
    elif border_mode == 'valid':
        padding = (0, 0)
    else:
        raise Exception('Invalid border mode: ' + str(border_mode))

    if dim_ordering not in {'th', 'tf'}:
        raise Exception('Unknown dim_ordering ' + str(dim_ordering))

    if dim_ordering == 'tf':
        x = x.dimshuffle((0, 3, 1, 2))

    if pool_mode == 'max':
        pool_out = pool.pool_2d(x, ds=pool_size, st=strides,
                                ignore_border=True,
                                padding=padding,
                                mode='max')
    elif pool_mode == 'avg':
        pool_out = pool.pool_2d(x, ds=pool_size, st=strides,
                                ignore_border=True,
                                padding=padding,
                                mode='average_exc_pad')
    else:
        raise Exception('Invalid pooling mode: ' + str(pool_mode))

    if border_mode == 'same':
        expected_width = (x.shape[2] + strides[0] - 1) // strides[0]
        expected_height = (x.shape[3] + strides[1] - 1) // strides[1]

        pool_out = pool_out[:, :,
                            : expected_width,
                            : expected_height]

    if dim_ordering == 'tf':
        pool_out = pool_out.dimshuffle((0, 2, 3, 1))
    return pool_out


def pool3d(x, pool_size, strides=(1, 1, 1), border_mode='valid',
           dim_ordering='th', pool_mode='max'):
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
        x = x.dimshuffle((0, 4, 1, 2, 3))

    if pool_mode == 'max':
        # pooling over conv_dim2, conv_dim1 (last two channels)
        output = pool.pool_2d(input=x.dimshuffle(0, 1, 4, 3, 2),
                              ds=(pool_size[1], pool_size[0]),
                              st=(strides[1], strides[0]),
                              ignore_border=ignore_border,
                              padding=padding,
                              mode='max')

        # pooling over conv_dim3
        pool_out = pool.pool_2d(input=output.dimshuffle(0, 1, 4, 3, 2),
                                ds=(1, pool_size[2]),
                                st=(1, strides[2]),
                                ignore_border=ignore_border,
                                padding=padding,
                                mode='max')

    elif pool_mode == 'avg':
        # pooling over conv_dim2, conv_dim1 (last two channels)
        output = pool.pool_2d(input=x.dimshuffle(0, 1, 4, 3, 2),
                              ds=(pool_size[1], pool_size[0]),
                              st=(strides[1], strides[0]),
                              ignore_border=ignore_border,
                              padding=padding,
                              mode='average_exc_pad')

        # pooling over conv_dim3
        pool_out = pool.pool_2d(input=output.dimshuffle(0, 1, 4, 3, 2),
                                ds=(1, pool_size[2]),
                                st=(1, strides[2]),
                                ignore_border=ignore_border,
                                padding=padding,
                                mode='average_exc_pad')
    else:
        raise Exception('Invalid pooling mode: ' + str(pool_mode))

    if dim_ordering == 'tf':
        pool_out = pool_out.dimshuffle((0, 2, 3, 4, 1))
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


def random_binomial(shape, p=0.0, dtype=_FLOATX, seed=None):
    if seed is None:
        seed = np.random.randint(10e6)
    rng = RandomStreams(seed=seed)
    return rng.binomial(shape, p=p, dtype=dtype)

import tensorflow as tf
import numpy as np
import os
import copy
import warnings
from .common import _FLOATX, _EPSILON

# INTERNAL UTILS

_SESSION = None
_LEARNING_PHASE = tf.placeholder(dtype='uint8', name='keras_learning_phase')  # 0 = test, 1 = train


def learning_phase():
    '''Returns the learning phase flag.

    The learning phase flag is an integer tensor (0 = test, 1 = train)
    to be passed as input to any Keras function
    that uses a different behavior at train time and test time.
    '''
    return _LEARNING_PHASE


def set_learning_phase(value):
    global _LEARNING_PHASE
    _LEARNING_PHASE = tf.constant(value, name='keras_learning_phase')


def get_session():
    '''Returns the TF session to be used by the backend.

    If a default TensorFlow session is available, we will return it.

    Else, we will return the global Keras session.

    If no global Keras session exists at this point:
    we will create a new global session.

    Note that you can manually set the global session
    via `K.set_session(sess)`.
    '''
    global _SESSION
    if tf.get_default_session() is not None:
        return tf.get_default_session()
    if _SESSION is None:
        if not os.environ.get('OMP_NUM_THREADS'):
            _SESSION = tf.Session(config=tf.ConfigProto(allow_soft_placement=True))
        else:
            nb_thread = int(os.environ.get('OMP_NUM_THREADS'))
            _SESSION = tf.Session(config=tf.ConfigProto(intra_op_parallelism_threads=nb_thread,
                                                        allow_soft_placement=True))
    return _SESSION


def set_session(session):
    '''Sets the global TF session.
    '''
    global _SESSION
    _SESSION = session


# VARIABLE MANIPULATION

def variable(value, dtype=_FLOATX, name=None):
    '''Instantiates a tensor.

    # Arguments
        value: numpy array, initial value of the tensor.
        dtype: tensor type.
        name: optional name string for the tensor.

    # Returns
        Tensor variable instance.
    '''
    v = tf.Variable(np.asarray(value, dtype=dtype), name=name)
    if tf.get_default_graph() is get_session().graph:
        try:
            get_session().run(v.initializer)
        except tf.errors.InvalidArgumentError:
            warnings.warn('Could not automatically initialize variable, '
                          'make sure you do it manually (e.g. via '
                          '`tf.initialize_all_variables()`).')
    else:
        warnings.warn('The default TensorFlow graph is not the graph '
                      'associated with the TensorFlow session currently '
                      'registered with Keras, and as such Keras '
                      'was not able to automatically initialize a variable. '
                      'You should consider registering the proper session '
                      'with Keras via `K.set_session(sess)`.')
    return v


def placeholder(shape=None, ndim=None, dtype=_FLOATX, name=None):
    '''Instantiates a placeholder.

    # Arguments
        shape: shape of the placeholder
            (integer tuple, may include None entries).
        ndim: number of axes of the tensor.
            At least one of {`shape`, `ndim`} must be specified.
            If both are specified, `shape` is used.
        dtype: placeholder type.
        name: optional name string for the placeholder.

    # Returns
        Placeholder tensor instance.
    '''
    if not shape:
        if ndim:
            shape = tuple([None for _ in range(ndim)])
    x = tf.placeholder(dtype, shape=shape, name=name)
    x._keras_shape = shape
    x._uses_learning_phase = False
    return x


def shape(x):
    '''Returns the symbolic shape of a tensor.
    '''
    return tf.shape(x)


def int_shape(x):
    '''Returns the shape of a tensor as a tuple of
    integers or None entries.
    '''
    shape = x.get_shape()
    return tuple([i.__int__() for i in shape])


def ndim(x):
    '''Returns the number of axes in a tensor, as an integer.
    '''
    dims = x.get_shape()._dims
    if dims is not None:
        return len(dims)
    return None


def dtype(x):
    '''Returns the dtype of a tensor, as a string.
    '''
    return x.dtype.name


def eval(x):
    '''Evaluates the value of a tensor.
    Returns a Numpy array.
    '''
    return x.eval(session=get_session())


def zeros(shape, dtype=_FLOATX, name=None):
    '''Instantiates an all-zeros tensor variable.
    '''
    return variable(np.zeros(shape), dtype, name)


def ones(shape, dtype=_FLOATX, name=None):
    '''Instantiates an all-ones tensor variable.
    '''
    return variable(np.ones(shape), dtype, name)


def eye(size, dtype=_FLOATX, name=None):
    '''Instantiate an identity matrix.
    '''
    return variable(np.eye(size), dtype, name)


def zeros_like(x, name=None):
    '''Instantiates an all-zeros tensor
    of the same shape as another tensor.
    '''
    return tf.zeros_like(x, name=name)


def ones_like(x, name=None):
    '''Instantiates an all-ones tensor
    of the same shape as another tensor.
    '''
    return tf.ones_like(x, name=name)


def count_params(x):
    '''Returns the number of scalars in a tensor.
    '''
    shape = x.get_shape()
    return np.prod([shape[i]._value for i in range(len(shape))])


def cast(x, dtype):
    '''Casts a tensor to a different dtype.
    '''
    return tf.cast(x, dtype)


# LINEAR ALGEBRA

def dot(x, y):
    '''Multiplies 2 tensors.
    When attempting to multiply a ND tensor
    with a ND tensor, reproduces the Theano behavior
    (e.g. (2, 3).(4, 3, 5) = (2, 4, 5))
    '''
    if ndim(x) is not None and (ndim(x) > 2 or ndim(y) > 2):
        x_shape = (-1,) + int_shape(x)[1:]
        y_shape = int_shape(y)
        y_permute_dim = list(range(ndim(y)))
        y_permute_dim = [y_permute_dim.pop(-2)] + y_permute_dim
        xt = tf.reshape(x, [-1, x_shape[-1]])
        yt = tf.reshape(tf.transpose(y, perm=y_permute_dim), [y_shape[-2], -1])
        return tf.reshape(tf.matmul(xt, yt), x_shape[:-1] + y_shape[:-2] + y_shape[-1:])
    out = tf.matmul(x, y)
    return out


def batch_dot(x, y, axes=None):
    '''Batchwise dot product.

    batch_dot results in a tensor with less dimensions than the input.
    If the number of dimensions is reduced to 1, we use `expand_dims` to
    make sure that ndim is at least 2.

    # Example
        Assume x = [[1, 2]   and y = [[5, 6]
                    [3, 4]]           [7, 8]]
        batch_dot(x, y, axes=1) = [[17, 53]] which is the main diagonal
        of x.dot(y.T), although we never have to calculate the off-diagonal
        elements.


    # Arguments
        x, y: tensors with ndim >= 2
        axes: list (or single) int with target dimensions

    # Returns
        Tensor with ndim >= 2
    '''
    if type(axes) == int:
        axes = (axes, axes)
    if axes is not None:
        adj_x = None if axes[0] == ndim(x) - 1 else True
        adj_y = True if axes[1] == ndim(y) - 1 else None
    else:
        adj_x = None
        adj_y = None
    out = tf.batch_matmul(x, y, adj_x=adj_x, adj_y=adj_y)
    if ndim(out) == 1:
        out = expand_dims(out, 1)
    return out


def transpose(x):
    '''Transposes a matrix.
    '''
    return tf.transpose(x)


def gather(reference, indices):
    '''Retrieves the vectors of indices `indices`
    in the 2D tensor `reference`.

    # Arguments
        reference: a 2D tensor.
        indices: an int tensor of indices.

    # Returns
        A 3D tensor of same type as `reference`.
    '''
    return tf.gather(reference, indices)


# ELEMENT-WISE OPERATIONS

def _normalize_axis(axis, ndim):
    if type(axis) is tuple:
        axis = list(axis)
    if type(axis) is list:
        for i, a in enumerate(axis):
            if a is not None and a < 0:
                axis[i] = a % ndim
    else:
        if axis is not None and axis < 0:
            axis = axis % ndim
    return axis


def max(x, axis=None, keepdims=False):
    '''Maximum value in a tensor.
    '''
    axis = _normalize_axis(axis, ndim(x))
    return tf.reduce_max(x, reduction_indices=axis, keep_dims=keepdims)


def min(x, axis=None, keepdims=False):
    '''Minimum value in a tensor.
    '''
    axis = _normalize_axis(axis, ndim(x))
    return tf.reduce_min(x, reduction_indices=axis, keep_dims=keepdims)


def sum(x, axis=None, keepdims=False):
    '''Sum of the values in a tensor, alongside the specified axis.
    '''
    axis = _normalize_axis(axis, ndim(x))
    return tf.reduce_sum(x, reduction_indices=axis, keep_dims=keepdims)


def prod(x, axis=None, keepdims=False):
    '''Multiplies the values in a tensor, alongside the specified axis.
    '''
    axis = _normalize_axis(axis, ndim(x))
    return tf.reduce_prod(x, reduction_indices=axis, keep_dims=keepdims)


def std(x, axis=None, keepdims=False):
    '''Standard deviation of a tensor, alongside the specificied axis.
    '''
    axis = _normalize_axis(axis, ndim(x))
    if x.dtype.base_dtype == tf.bool:
        x = tf.cast(x, _FLOATX)
    m = tf.reduce_mean(x, reduction_indices=axis, keep_dims=True)
    devs_squared = tf.square(x - m)
    return tf.sqrt(tf.reduce_mean(devs_squared,
                                  reduction_indices=axis,
                                  keep_dims=keepdims))


def mean(x, axis=None, keepdims=False):
    '''Mean of a tensor, alongside the specificied axis.
    '''
    axis = _normalize_axis(axis, ndim(x))
    if x.dtype.base_dtype == tf.bool:
        x = tf.cast(x, _FLOATX)
    return tf.reduce_mean(x, reduction_indices=axis, keep_dims=keepdims)


def any(x, axis=None, keepdims=False):
    '''Bitwise reduction (logical OR).

    Returns an uint8 tensor (0s and 1s).
    '''
    axis = _normalize_axis(axis, ndim(x))
    x = tf.cast(x, tf.bool)
    x = tf.reduce_any(x, reduction_indices=axis, keep_dims=keepdims)
    return tf.cast(x, tf.uint8)


def argmax(x, axis=-1):
    '''Returns the index of the maximum value
    along a tensor axis.
    '''
    if axis < 0:
        axis = axis % len(x.get_shape())
    return tf.argmax(x, axis)


def argmin(x, axis=-1):
    '''Returns the index of the minimum value
    along a tensor axis.
    '''
    if axis < 0:
        axis = axis % len(x.get_shape())
    return tf.argmin(x, axis)


def square(x):
    '''Element-wise square.
    '''
    return tf.square(x)


def abs(x):
    '''Element-wise absolute value.
    '''
    return tf.abs(x)


def sqrt(x):
    '''Element-wise square root.
    '''
    x = tf.clip_by_value(x, tf.cast(0., dtype=_FLOATX),
                         tf.cast(np.inf, dtype=_FLOATX))
    return tf.sqrt(x)


def exp(x):
    '''Element-wise exponential.
    '''
    return tf.exp(x)


def log(x):
    '''Element-wise log.
    '''
    return tf.log(x)


def round(x):
    '''Element-wise rounding to the closest integer.
    '''
    return tf.round(x)


def sign(x):
    '''Element-wise sign.
    '''
    return tf.sign(x)


def pow(x, a):
    '''Element-wise exponentiation.
    '''
    return tf.pow(x, a)


def clip(x, min_value, max_value):
    '''Element-wise value clipping.
    '''
    if max_value < min_value:
        max_value = min_value
    return tf.clip_by_value(x, tf.cast(min_value, dtype=_FLOATX),
                            tf.cast(max_value, dtype=_FLOATX))


def equal(x, y):
    '''Element-wise equality between two tensors.
    Returns a bool tensor.
    '''
    return tf.equal(x, y)


def not_equal(x, y):
    '''Element-wise inequality between two tensors.
    Returns a bool tensor.
    '''
    return tf.not_equal(x, y)


def maximum(x, y):
    '''Element-wise maximum of two tensors.
    '''
    return tf.maximum(x, y)


def minimum(x, y):
    '''Element-wise minimum of two tensors.
    '''
    return tf.minimum(x, y)


def sin(x):
    '''Computes sin of x element-wise.
    '''
    return tf.sin(x)


def cos(x):
    '''Computes cos of x element-wise.
    '''
    return tf.cos(x)


# SHAPE OPERATIONS

def concatenate(tensors, axis=-1):
    '''Concantes a list of tensors alongside the specified axis.
    '''
    if axis < 0:
        if len(tensors[0].get_shape()):
            axis = axis % len(tensors[0].get_shape())
        else:
            axis = 0
    return tf.concat(axis, tensors)


def reshape(x, shape):
    '''Reshapes a tensor to the specified shape.
    '''
    return tf.reshape(x, shape)


def permute_dimensions(x, pattern):
    '''Permutes axes in a tensor.

    # Arguments
        pattern: should be a tuple of
            dimension indices, e.g. (0, 2, 1).
    '''
    return tf.transpose(x, perm=pattern)


def resize_images(X, height_factor, width_factor, dim_ordering):
    '''Resizes the images contained in a 4D tensor of shape
    - [batch, channels, height, width] (for 'th' dim_ordering)
    - [batch, height, width, channels] (for 'tf' dim_ordering)
    by a factor of (height_factor, width_factor). Both factors should be
    positive integers.
    '''
    if dim_ordering == 'th':
        new_shape = tf.shape(X)[2:]
        new_shape *= tf.constant(np.array([height_factor, width_factor]).astype('int32'))
        X = permute_dimensions(X, [0, 2, 3, 1])
        X = tf.image.resize_nearest_neighbor(X, new_shape)
        return permute_dimensions(X, [0, 3, 1, 2])
    elif dim_ordering == 'tf':
        new_shape = tf.shape(X)[1:3]
        new_shape *= tf.constant(np.array([height_factor, width_factor]).astype('int32'))
        return tf.image.resize_nearest_neighbor(X, new_shape)
    else:
        raise Exception('Invalid dim_ordering: ' + dim_ordering)


def repeat_elements(x, rep, axis):
    '''Repeats the elements of a tensor along an axis, like np.repeat

    If x has shape (s1, s2, s3) and axis=1, the output
    will have shape (s1, s2 * rep, s3)
    '''
    x_shape = x.get_shape().as_list()
    # slices along the repeat axis
    splits = tf.split(axis, x_shape[axis], x)
    # repeat each slice the given number of reps
    x_rep = [s for s in splits for i in range(rep)]
    return tf.concat(axis, x_rep)


def repeat(x, n):
    '''Repeats a 2D tensor:

    if x has shape (samples, dim) and n=2,
    the output will have shape (samples, 2, dim)
    '''
    assert ndim(x) == 2
    tensors = [x] * n
    stacked = tf.pack(tensors)
    return tf.transpose(stacked, (1, 0, 2))


def tile(x, n):
    return tf.tile(x, n)


def flatten(x):
    return tf.reshape(x, [-1])


def batch_flatten(x):
    '''Turn a n-D tensor into a 2D tensor where
    the first dimension is conserved.
    '''
    x = tf.reshape(x, [-1, np.prod(x.get_shape()[1:].as_list())])
    return x


def expand_dims(x, dim=-1):
    '''Adds a 1-sized dimension at index "dim".
    '''
    return tf.expand_dims(x, dim)


def squeeze(x, axis):
    '''Removes a 1-dimension from the tensor at index "axis".
    '''
    return tf.squeeze(x, [axis])


def temporal_padding(x, padding=1):
    '''Pads the middle dimension of a 3D tensor
    with "padding" zeros left and right.
    '''
    pattern = [[0, 0], [padding, padding], [0, 0]]
    return tf.pad(x, pattern)


def spatial_2d_padding(x, padding=(1, 1), dim_ordering='th'):
    '''Pads the 2nd and 3rd dimensions of a 4D tensor
    with "padding[0]" and "padding[1]" (resp.) zeros left and right.
    '''
    if dim_ordering == 'th':
        pattern = [[0, 0], [0, 0],
                   [padding[0], padding[0]], [padding[1], padding[1]]]
    else:
        pattern = [[0, 0],
                   [padding[0], padding[0]], [padding[1], padding[1]],
                   [0, 0]]
    return tf.pad(x, pattern)


def pack(x):
    return tf.pack(x)


# VALUE MANIPULATION


def get_value(x):
    '''Returns the value of a tensor variable,
    as a Numpy array.
    '''
    return x.eval(session=get_session())


def batch_get_value(xs):
    '''Returns the value of more than one tensor variable,
    as a list of Numpy arrays.
    '''
    if xs:
        return get_session().run(xs)
    else:
        return []


def set_value(x, value):
    '''Sets the value of a tensor variable,
    from a Numpy array.
    '''
    tf.assign(x, np.asarray(value)).op.run(session=get_session())


def batch_set_value(tuples):
    '''Sets the values of many tensor variables at once.

    # Arguments
        tuples: a list of tuples `(tensor, value)`.
            `value` should be a Numpy array.
    '''
    if tuples:
        ops = [tf.assign(x, np.asarray(value)) for x, value in tuples]
        get_session().run(ops)

# GRAPH MANIPULATION

class Function(object):

    def __init__(self, inputs, outputs, updates=[]):
        assert type(inputs) in {list, tuple}, 'Input to a TensorFlow backend function should be a list or tuple.'
        assert type(outputs) in {list, tuple}, 'Output to a TensorFlow backend function should be a list or tuple.'
        assert type(updates) in {list, tuple}, 'Updates in a TensorFlow backend function should be a list or tuple.'
        self.inputs = list(inputs)
        self.outputs = list(outputs)
        with tf.control_dependencies(self.outputs):
            self.updates = [tf.assign(p, new_p) for (p, new_p) in updates]

    def __call__(self, inputs):
        assert type(inputs) in {list, tuple}
        names = [v.name for v in self.inputs]
        feed_dict = dict(zip(names, inputs))
        session = get_session()
        updated = session.run(self.outputs + self.updates, feed_dict=feed_dict)
        return updated[:len(self.outputs)]


def function(inputs, outputs, updates=[], **kwargs):
    '''Instantiates a Keras function.

    # Arguments
        inputs: list of placeholder/variable tensors.
        outputs: list of output tensors.
        updates: list of update tuples (old_tensor, new_tensor).
    '''
    if len(kwargs) > 0:
        msg = [
            "Expected no kwargs, you passed %s" % len(kwargs),
            "kwargs passed to function are ignored with Tensorflow backend"
        ]
        warnings.warn('\n'.join(msg))
    return Function(inputs, outputs, updates=updates)


def gradients(loss, variables):
    '''Returns the gradients of `variables` (list of tensor variables)
    with regard to `loss`.
    '''
    return tf.gradients(loss, variables)


# CONTROL FLOW

def rnn(step_function, inputs, initial_states,
        go_backwards=False, mask=None, constants=None,
        unroll=False, input_length=None):
    '''Iterates over the time dimension of a tensor.

    # Arguments
        inputs: tensor of temporal data of shape (samples, time, ...)
            (at least 3D).
        step_function:
            Parameters:
                input: tensor with shape (samples, ...) (no time dimension),
                    representing input for the batch of samples at a certain
                    time step.
                states: list of tensors.
            Returns:
                output: tensor with shape (samples, ...) (no time dimension),
                new_states: list of tensors, same length and shapes
                    as 'states'.
        initial_states: tensor with shape (samples, ...) (no time dimension),
            containing the initial values for the states used in
            the step function.
        go_backwards: boolean. If True, do the iteration over
            the time dimension in reverse order.
        mask: binary tensor with shape (samples, time, 1),
            with a zero for every element that is masked.
        constants: a list of constant values passed at each step.
        unroll: with TensorFlow the RNN is always unrolled, but with Theano you
            can use this boolean flag to unroll the RNN.
        input_length: not relevant in the TensorFlow implementation.
            Must be specified if using unrolling with Theano.

    # Returns
        A tuple (last_output, outputs, new_states).

        last_output: the latest output of the rnn, of shape (samples, ...)
        outputs: tensor with shape (samples, time, ...) where each
            entry outputs[s, t] is the output of the step function
            at time t for sample s.
        new_states: list of tensors, latest states returned by
            the step function, of shape (samples, ...).
    '''
    ndim = len(inputs.get_shape())
    assert ndim >= 3, "Input should be at least 3D."
    axes = [1, 0] + list(range(2, ndim))
    inputs = tf.transpose(inputs, (axes))
    input_list = tf.unpack(inputs)
    if constants is None:
        constants = []

    states = initial_states
    successive_states = []
    successive_outputs = []
    if go_backwards:
        input_list.reverse()

    if mask is not None:
        # Transpose not supported by bool tensor types, hence round-trip to uint8.
        mask = tf.cast(mask, tf.uint8)
        if len(mask.get_shape()) == ndim-1:
            mask = expand_dims(mask)
        mask = tf.cast(tf.transpose(mask, axes), tf.bool)
        mask_list = tf.unpack(mask)

        if go_backwards:
            mask_list.reverse()

        for input, mask_t in zip(input_list, mask_list):
            output, new_states = step_function(input, states + constants)

            # tf.select needs its condition tensor to be the same shape as its two
            # result tensors, but in our case the condition (mask) tensor is
            # (nsamples, 1), and A and B are (nsamples, ndimensions). So we need to
            # broadcast the mask to match the shape of A and B. That's what the
            # tile call does, is just repeat the mask along its second dimension
            # ndimensions times.
            tiled_mask_t = tf.tile(mask_t, tf.pack([1, tf.shape(output)[1]]))

            if len(successive_outputs) == 0:
                prev_output = zeros_like(output)
            else:
                prev_output = successive_outputs[-1]

            output = tf.select(tiled_mask_t, output, prev_output)

            return_states = []
            for state, new_state in zip(states, new_states):
                # (see earlier comment for tile explanation)
                tiled_mask_t = tf.tile(mask_t, tf.pack([1, tf.shape(new_state)[1]]))
                return_states.append(tf.select(tiled_mask_t, new_state, state))

            states = return_states
            successive_outputs.append(output)
            successive_states.append(states)
    else:
        for input in input_list:
            output, states = step_function(input, states + constants)
            successive_outputs.append(output)
            successive_states.append(states)

    last_output = successive_outputs[-1]
    outputs = tf.pack(successive_outputs)
    new_states = successive_states[-1]

    axes = [1, 0] + list(range(2, len(outputs.get_shape())))
    outputs = tf.transpose(outputs, axes)
    return last_output, outputs, new_states


def switch(condition, then_expression, else_expression):
    '''Switches between two operations depending on a scalar value (int or bool).
    Note that both `then_expression` and `else_expression`
    should be symbolic tensors of the *same shape*.

    # Arguments
        condition: scalar tensor.
        then_expression: TensorFlow operation.
        else_expression: TensorFlow operation.
    '''
    x_shape = copy.copy(then_expression.get_shape())
    x = tf.python.control_flow_ops.cond(tf.cast(condition, 'bool'),
                                        lambda: then_expression,
                                        lambda: else_expression)
    x.set_shape(x_shape)
    return x


def in_train_phase(x, alt):
    '''Selects `x` in train phase, and `alt` otherwise.
    Note that `alt` should have the *same shape* as `x`.
    '''
    x_shape = copy.copy(x.get_shape())
    x = tf.python.control_flow_ops.cond(tf.cast(_LEARNING_PHASE, 'bool'),
                                        lambda: x,
                                        lambda: alt)
    x._uses_learning_phase = True
    x.set_shape(x_shape)
    return x


def in_test_phase(x, alt):
    '''Selects `x` in test phase, and `alt` otherwise.
    Note that `alt` should have the *same shape* as `x`.
    '''
    x_shape = copy.copy(x.get_shape())
    x = tf.python.control_flow_ops.cond(tf.cast(_LEARNING_PHASE, 'bool'),
                                        lambda: alt,
                                        lambda: x)
    x._uses_learning_phase = True
    x.set_shape(x_shape)
    return x


# NN OPERATIONS

def relu(x, alpha=0., max_value=None):
    '''Rectified linear unit

    # Arguments
        alpha: slope of negative section.
        max_value: saturation threshold.
    '''
    negative_part = tf.nn.relu(-x)
    x = tf.nn.relu(x)
    if max_value is not None:
        x = tf.clip_by_value(x, tf.cast(0., dtype=_FLOATX),
                             tf.cast(max_value, dtype=_FLOATX))
    if isinstance(alpha, (tuple, list, np.ndarray)) or np.isscalar(alpha):
        alpha = tf.constant(alpha, dtype=_FLOATX)
    x -= alpha * negative_part
    return x


def softmax(x):
    '''Softmax of a tensor.
    '''
    return tf.nn.softmax(x)


def softplus(x):
    '''Softplus of a tensor.
    '''
    return tf.nn.softplus(x)


def softsign(x):
    return tf.nn.softsign(x)


def categorical_crossentropy(output, target, from_logits=False):
    '''Categorical crossentropy between an output tensor
    and a target tensor, where the target is a tensor of the same
    shape as the output.
    '''
    # Note: tf.nn.softmax_cross_entropy_with_logits
    # expects logits, Keras expects probabilities.
    if not from_logits:
        # scale preds so that the class probas of each sample sum to 1
        output /= tf.reduce_sum(output,
                                reduction_indices=len(output.get_shape()) - 1,
                                keep_dims=True)
        # manual computation of crossentropy
        output = tf.clip_by_value(output, tf.cast(_EPSILON, dtype=_FLOATX),
                                  tf.cast(1. - _EPSILON, dtype=_FLOATX))
        return - tf.reduce_sum(target * tf.log(output),
                               reduction_indices=len(output.get_shape()) - 1)
    else:
        return tf.nn.softmax_cross_entropy_with_logits(output, target)


def sparse_categorical_crossentropy(output, target, from_logits=False):
    '''Categorical crossentropy between an output tensor
    and a target tensor, where the target is an integer tensor.
    '''
    # Note: tf.nn.softmax_cross_entropy_with_logits
    # expects logits, Keras expects probabilities.
    if not from_logits:
        output = tf.clip_by_value(output, tf.cast(_EPSILON, dtype=_FLOATX),
                                  tf.cast(1.-_EPSILON, dtype=_FLOATX))
        output = tf.log(output)

    output_shape = output.get_shape()
    res = tf.nn.sparse_softmax_cross_entropy_with_logits(
        tf.reshape(output, [-1, int(output_shape[-1])]),
        cast(flatten(target), 'int64'))
    if len(output_shape) == 3:
        # if our output includes timesteps we need to reshape
        return tf.reshape(res, [-1, int(output_shape[-2])])
    else:
        return res


def binary_crossentropy(output, target, from_logits=False):
    '''Binary crossentropy between an output tensor and a target tensor.
    '''
    # Note: tf.nn.softmax_cross_entropy_with_logits
    # expects logits, Keras expects probabilities.
    if not from_logits:
        # transform back to logits
        output = tf.clip_by_value(output, tf.cast(_EPSILON, dtype=_FLOATX),
                                  tf.cast(1.-_EPSILON, dtype=_FLOATX))
        output = tf.log(output / (1 - output))
    return tf.nn.sigmoid_cross_entropy_with_logits(output, target)


def sigmoid(x):
    '''Element-wise sigmoid.
    '''
    return tf.nn.sigmoid(x)


def hard_sigmoid(x):
    '''Segment-wise linear approximation of sigmoid.
    Faster than sigmoid.
    '''
    x = (0.2 * x) + 0.5
    x = tf.clip_by_value(x, tf.cast(0., dtype=_FLOATX),
                         tf.cast(1., dtype=_FLOATX))
    return x


def tanh(x):
    '''Element-wise tanh.
    '''
    return tf.nn.tanh(x)


def dropout(x, level, seed=None):
    '''Sets entries in `x` to zero at random,
    while scaling the entire tensor.

    # Arguments
        x: tensor
        level: fraction of the entries in the tensor
            that will be set to 0
        seed: random seed to ensure determinism.
    '''
    retain_prob = 1. - level
    if seed is None:
        seed = np.random.randint(10e6)
    # the dummy 1. works around a TF bug
    # (float32_ref vs. float32 incomptability)
    return tf.nn.dropout(x * 1., retain_prob, seed=seed)


def l2_normalize(x, axis):
    '''Normalizes a tensor wrt the L2 norm alonside the specified axis.
    '''
    if axis < 0:
        axis = axis % len(x.get_shape())
    return tf.nn.l2_normalize(x, dim=axis)


# CONVOLUTIONS


def conv2d(x, kernel, strides=(1, 1), border_mode='valid', dim_ordering='th',
           image_shape=None, filter_shape=None):
    '''2D convolution.

    # Arguments
        kernel: kernel tensor.
        strides: strides tuple.
        border_mode: string, "same" or "valid".
        dim_ordering: "tf" or "th". Whether to use Theano or TensorFlow dimension ordering
        in inputs/kernels/ouputs.
    '''
    if border_mode == 'same':
        padding = 'SAME'
    elif border_mode == 'valid':
        padding = 'VALID'
    else:
        raise Exception('Invalid border mode: ' + str(border_mode))

    strides = (1,) + strides + (1,)

    if _FLOATX == 'float64':
        # tf conv2d only supports float32
        x = tf.cast(x, 'float32')
        kernel = tf.cast(kernel, 'float32')

    if dim_ordering == 'th':
        # TF uses the last dimension as channel dimension,
        # instead of the 2nd one.
        # TH input shape: (samples, input_depth, rows, cols)
        # TF input shape: (samples, rows, cols, input_depth)
        # TH kernel shape: (depth, input_depth, rows, cols)
        # TF kernel shape: (rows, cols, input_depth, depth)
        x = tf.transpose(x, (0, 2, 3, 1))
        kernel = tf.transpose(kernel, (2, 3, 1, 0))
        x = tf.nn.conv2d(x, kernel, strides, padding=padding)
        x = tf.transpose(x, (0, 3, 1, 2))
    elif dim_ordering == 'tf':
        x = tf.nn.conv2d(x, kernel, strides, padding=padding)
    else:
        raise Exception('Unknown dim_ordering: ' + str(dim_ordering))

    if _FLOATX == 'float64':
        x = tf.cast(x, 'float64')
    return x


def pool2d(x, pool_size, strides=(1, 1),
           border_mode='valid', dim_ordering='th', pool_mode='max'):
    '''2D Pooling.

    # Arguments
        pool_size: tuple of 2 integers.
        strides: tuple of 2 integers.
        border_mode: one of "valid", "same".
        dim_ordering: one of "th", "tf".
        pool_mode: one of "max", "avg".
    '''
    if border_mode == 'same':
        padding = 'SAME'
    elif border_mode == 'valid':
        padding = 'VALID'
    else:
        raise Exception('Invalid border mode: ' + str(border_mode))

    strides = (1,) + strides + (1,)
    pool_size = (1,) + pool_size + (1,)

    if _FLOATX == 'float64':
        # tf max_pool only supports float32
        x = tf.cast(x, 'float32')

    if dim_ordering in {'tf', 'th'}:
        if dim_ordering == 'th':
            # TF uses the last dimension as channel dimension,
            # instead of the 2nd one.
            # TH input shape: (samples, input_depth, rows, cols)
            # TF input shape: (samples, rows, cols, input_depth)
            # TH kernel shape: (depth, input_depth, rows, cols)
            # TF kernel shape: (rows, cols, input_depth, depth)
            x = tf.transpose(x, (0, 2, 3, 1))
        if pool_mode == 'max':
            x = tf.nn.max_pool(x, pool_size, strides, padding=padding)
        elif pool_mode == 'avg':
            x = tf.nn.avg_pool(x, pool_size, strides, padding=padding)
        else:
            raise Exception('Invalid pooling mode: ' + str(pool_mode))
        if dim_ordering == 'th':
            x = tf.transpose(x, (0, 3, 1, 2))
    else:
        raise Exception('Unknown dim_ordering: ' + str(dim_ordering))

    if _FLOATX == 'float64':
        x = tf.cast(x, 'float64')
    return x


# RANDOMNESS

def random_normal(shape, mean=0.0, std=1.0, dtype=_FLOATX, seed=None):
    if seed is None:
        seed = np.random.randint(10e6)
    return tf.random_normal(shape, mean=mean, stddev=std,
                            dtype=dtype, seed=seed)


def random_uniform(shape, low=0.0, high=1.0, dtype=_FLOATX, seed=None):
    if seed is None:
        seed = np.random.randint(10e6)
    return tf.random_uniform(shape, minval=low, maxval=high,
                             dtype=dtype, seed=seed)


def random_binomial(shape, p=0.0, dtype=_FLOATX, seed=None):
    if seed is None:
        seed = np.random.randint(10e6)
    return tf.select(tf.random_uniform(shape, dtype=dtype, seed=seed) <= p,
                     tf.ones(shape), tf.zeros(shape))

import numpy as np

# the type of float to use throughout the session.
_FLOATX = 'float32'
_EPSILON = 10e-8
_UID_PREFIXES = {}


def epsilon():
    return _EPSILON


def set_epsilon(e):
    global _EPSILON
    _EPSILON = e


def floatx():
    '''Returns the default float type, as a string
    (e.g. 'float16', 'float32', 'float64').
    '''
    return _FLOATX


def set_floatx(floatx):
    global _FLOATX
    if floatx not in {'float16', 'float32', 'float64'}:
        raise Exception('Unknown floatx type: ' + str(floatx))
    floatx = str(floatx)
    _FLOATX = floatx


def cast_to_floatx(x):
    '''Cast a Numpy array to floatx.
    '''
    return np.asarray(x, dtype=_FLOATX)


def get_uid(prefix=''):
    if prefix not in _UID_PREFIXES:
        _UID_PREFIXES[prefix] = 1
        return 1
    else:
        _UID_PREFIXES[prefix] += 1
        return _UID_PREFIXES[prefix]

from __future__ import absolute_import
# -*- coding: utf-8 -*-
import numpy as np
import random
from six.moves import range


def pad_sequences(sequences, maxlen=None, dtype='int32',
                  padding='pre', truncating='pre', value=0.):
    '''Pads each sequence to the same length:
    the length of the longest sequence.

    If maxlen is provided, any sequence longer
    than maxlen is truncated to maxlen.
    Truncation happens off either the beginning (default) or
    the end of the sequence.

    Supports post-padding and pre-padding (default).

    # Arguments
        sequences: list of lists where each element is a sequence
        maxlen: int, maximum length
        dtype: type to cast the resulting sequence.
        padding: 'pre' or 'post', pad either before or after each sequence.
        truncating: 'pre' or 'post', remove values from sequences larger than
            maxlen either in the beginning or in the end of the sequence
        value: float, value to pad the sequences to the desired value.

    # Returns
        x: numpy array with dimensions (number_of_sequences, maxlen)
    '''
    lengths = [len(s) for s in sequences]

    nb_samples = len(sequences)
    if maxlen is None:
        maxlen = np.max(lengths)

    # take the sample shape from the first non empty sequence
    # checking for consistency in the main loop below.
    sample_shape = tuple()
    for s in sequences:
        if len(s) > 0:
            sample_shape = np.asarray(s).shape[1:]
            break

    x = (np.ones((nb_samples, maxlen) + sample_shape) * value).astype(dtype)
    for idx, s in enumerate(sequences):
        if len(s) == 0:
            continue  # empty list was found
        if truncating == 'pre':
            trunc = s[-maxlen:]
        elif truncating == 'post':
            trunc = s[:maxlen]
        else:
            raise ValueError('Truncating type "%s" not understood' % truncating)

        # check `trunc` has expected shape
        trunc = np.asarray(trunc, dtype=dtype)
        if trunc.shape[1:] != sample_shape:
            raise ValueError('Shape of sample %s of sequence at position %s is different from expected shape %s' %
                             (trunc.shape[1:], idx, sample_shape))

        if padding == 'post':
            x[idx, :len(trunc)] = trunc
        elif padding == 'pre':
            x[idx, -len(trunc):] = trunc
        else:
            raise ValueError('Padding type "%s" not understood' % padding)
    return x


def make_sampling_table(size, sampling_factor=1e-5):
    '''This generates an array where the ith element
    is the probability that a word of rank i would be sampled,
    according to the sampling distribution used in word2vec.

    The word2vec formula is:
        p(word) = min(1, sqrt(word.frequency/sampling_factor) / (word.frequency/sampling_factor))

    We assume that the word frequencies follow Zipf's law (s=1) to derive
    a numerical approximation of frequency(rank):
       frequency(rank) ~ 1/(rank * (log(rank) + gamma) + 1/2 - 1/(12*rank))
        where gamma is the Euler-Mascheroni constant.

    # Arguments
        size: int, number of possible words to sample.
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
    '''Take a sequence (list of indexes of words),
    returns couples of [word_index, other_word index] and labels (1s or 0s),
    where label = 1 if 'other_word' belongs to the context of 'word',
    and label=0 if 'other_word' is ramdomly sampled

    # Arguments
        vocabulary_size: int. maximum possible word index + 1
        window_size: int. actually half-window.
            The window of a word wi will be [i-window_size, i+window_size+1]
        negative_samples: float >= 0. 0 for no negative (=random) samples.
            1 for same number as positive samples. etc.
        categorical: bool. if False, labels will be
            integers (eg. [0, 1, 1 .. ]),
            if True labels will be categorical eg. [[1,0],[0,1],[0,1] .. ]

    # Returns
        couples, lables: where `couples` are int pairs and
            `labels` are either 0 or 1.

    # Notes
        By convention, index 0 in the vocabulary is
        a non-word and will be skipped.
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

        couples += [[words[i %len(words)], random.randint(1, vocabulary_size-1)] for i in range(nb_negative_samples)]
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
'''These preprocessing utilities would greatly benefit
from a fast Cython rewrite.
'''
from __future__ import absolute_import

import string
import sys
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
    seq = text_to_word_sequence(text, filters=filters, lower=lower, split=split)
    return [(abs(hash(w)) % (n - 1) + 1) for w in seq]


class Tokenizer(object):
    def __init__(self, nb_words=None, filters=base_filter(),
                 lower=True, split=' ', char_level=False):
        '''The class allows to vectorize a text corpus, by turning each
        text into either a sequence of integers (each integer being the index
        of a token in a dictionary) or into a vector where the coefficient
        for each token could be binary, based on word count, based on tf-idf...

        # Arguments
            nb_words: the maximum number of words to keep, based
                on word frequency. Only the most common `nb_words` words will
                be kept.
            filters: a string where each element is a character that will be
                filtered from the texts. The default is all punctuation, plus
                tabs and line breaks, minus the `'` character.
            lower: boolean. Whether to convert the texts to lowercase.
            split: character or string to use for token splitting.
            char_level: if True, every character will be treated as a word.

        By default, all punctuation is removed, turning the texts into
        space-separated sequences of words
        (words maybe include the `'` character). These sequences are then
        split into lists of tokens. They will then be indexed or vectorized.

        `0` is a reserved index that won't be assigned to any word.
        '''
        self.word_counts = {}
        self.word_docs = {}
        self.filters = filters
        self.split = split
        self.lower = lower
        self.nb_words = nb_words
        self.document_count = 0
        self.char_level = char_level

    def fit_on_texts(self, texts):
        '''Required before using texts_to_sequences or texts_to_matrix

        # Arguments
            texts: can be a list of strings,
                or a generator of strings (for memory-efficiency)
        '''
        self.document_count = 0
        for text in texts:
            self.document_count += 1
            seq = text if self.char_level else text_to_word_sequence(text, self.filters, self.lower, self.split)
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
        wcounts.sort(key=lambda x: x[1], reverse=True)
        sorted_voc = [wc[0] for wc in wcounts]
        self.word_index = dict(list(zip(sorted_voc, list(range(1, len(sorted_voc) + 1)))))

        self.index_docs = {}
        for w, c in list(self.word_docs.items()):
            self.index_docs[self.word_index[w]] = c

    def fit_on_sequences(self, sequences):
        '''Required before using sequences_to_matrix
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
        '''Transforms each text in texts in a sequence of integers.
        Only top "nb_words" most frequent words will be taken into account.
        Only words known by the tokenizer will be taken into account.

        Returns a list of sequences.
        '''
        res = []
        for vect in self.texts_to_sequences_generator(texts):
            res.append(vect)
        return res

    def texts_to_sequences_generator(self, texts):
        '''Transforms each text in texts in a sequence of integers.
        Only top "nb_words" most frequent words will be taken into account.
        Only words known by the tokenizer will be taken into account.

        Yields individual sequences.

        # Arguments:
            texts: list of strings.
        '''
        nb_words = self.nb_words
        for text in texts:
            seq = text if self.char_level else text_to_word_sequence(text, self.filters, self.lower, self.split)
            vect = []
            for w in seq:
                i = self.word_index.get(w)
                if i is not None:
                    if nb_words and i >= nb_words:
                        continue
                    else:
                        vect.append(i)
            yield vect

    def texts_to_matrix(self, texts, mode='binary'):
        '''Convert a list of texts to a Numpy matrix,
        according to some vectorization mode.

        # Arguments:
            texts: list of strings.
            modes: one of "binary", "count", "tfidf", "freq"
        '''
        sequences = self.texts_to_sequences(texts)
        return self.sequences_to_matrix(sequences, mode=mode)

    def sequences_to_matrix(self, sequences, mode='binary'):
        '''Converts a list of sequences into a Numpy matrix,
        according to some vectorization mode.

        # Arguments:
            sequences: list of sequences
                (a sequence is a list of integer word indices).
            modes: one of "binary", "count", "tfidf", "freq"
        '''
        if not self.nb_words:
            if self.word_index:
                nb_words = len(self.word_index) + 1
            else:
                raise Exception('Specify a dimension (nb_words argument), '
                                'or fit on some text data first.')
        else:
            nb_words = self.nb_words

        if mode == 'tfidf' and not self.document_count:
            raise Exception('Fit the Tokenizer on some data '
                            'before using tfidf mode.')

        X = np.zeros((len(sequences), nb_words))
        for i, seq in enumerate(sequences):
            if not seq:
                continue
            counts = {}
            for j in seq:
                if j >= nb_words:
                    continue
                if j not in counts:
                    counts[j] = 1.
                else:
                    counts[j] += 1
            for j, c in list(counts.items()):
                if mode == 'count':
                    X[i][j] = c
                elif mode == 'freq':
                    X[i][j] = c / len(seq)
                elif mode == 'binary':
                    X[i][j] = 1
                elif mode == 'tfidf':
                    tf = np.log(c / len(seq))
                    df = (1 + np.log(1 + self.index_docs.get(j, 0) / (1 + self.document_count)))
                    X[i][j] = tf / df
                else:
                    raise Exception('Unknown vectorization mode: ' + str(mode))
        return X

'''Fairly basic set of tools for realtime data augmentation on image data.
Can easily be extended to include new transformations,
new preprocessing methods, etc...
'''
from __future__ import absolute_import

import numpy as np
import re
from scipy import linalg
import scipy.ndimage as ndi
from six.moves import range
import os
import threading


def random_rotation(x, rg, row_index=1, col_index=2, channel_index=0,
                    fill_mode='nearest', cval=0.):
    theta = np.pi / 180 * np.random.uniform(-rg, rg)
    rotation_matrix = np.array([[np.cos(theta), -np.sin(theta), 0],
                                [np.sin(theta), np.cos(theta), 0],
                                [0, 0, 1]])

    h, w = x.shape[row_index], x.shape[col_index]
    transform_matrix = transform_matrix_offset_center(rotation_matrix, h, w)
    x = apply_transform(x, transform_matrix, channel_index, fill_mode, cval)
    return x


def random_shift(x, wrg, hrg, row_index=1, col_index=2, channel_index=0,
                 fill_mode='nearest', cval=0.):
    h, w = x.shape[row_index], x.shape[col_index]
    tx = np.random.uniform(-hrg, hrg) * h
    ty = np.random.uniform(-wrg, wrg) * w
    translation_matrix = np.array([[1, 0, tx],
                                   [0, 1, ty],
                                   [0, 0, 1]])

    transform_matrix = translation_matrix  # no need to do offset
    x = apply_transform(x, transform_matrix, channel_index, fill_mode, cval)
    return x


def random_shear(x, intensity, row_index=1, col_index=2, channel_index=0,
                 fill_mode='nearest', cval=0.):
    shear = np.random.uniform(-intensity, intensity)
    shear_matrix = np.array([[1, -np.sin(shear), 0],
                             [0, np.cos(shear), 0],
                             [0, 0, 1]])

    h, w = x.shape[row_index], x.shape[col_index]
    transform_matrix = transform_matrix_offset_center(shear_matrix, h, w)
    x = apply_transform(x, transform_matrix, channel_index, fill_mode, cval)
    return x


def random_zoom(x, zoom_range, row_index=1, col_index=2, channel_index=0,
                fill_mode='nearest', cval=0.):
    if len(zoom_range) != 2:
        raise Exception('zoom_range should be a tuple or list of two floats. '
                        'Received arg: ', zoom_range)

    if zoom_range[0] == 1 and zoom_range[1] == 1:
        zx, zy = 1, 1
    else:
        zx, zy = np.random.uniform(zoom_range[0], zoom_range[1], 2)
    zoom_matrix = np.array([[zx, 0, 0],
                            [0, zy, 0],
                            [0, 0, 1]])

    h, w = x.shape[row_index], x.shape[col_index]
    transform_matrix = transform_matrix_offset_center(zoom_matrix, h, w)
    x = apply_transform(x, transform_matrix, channel_index, fill_mode, cval)
    return x


def random_barrel_transform(x, intensity):
    # TODO
    pass


def random_channel_shift(x, intensity, channel_index=0):
    x = np.rollaxis(x, channel_index, 0)
    min_x, max_x = np.min(x), np.max(x)
    channel_images = [np.clip(x_channel + np.random.uniform(-intensity, intensity), min_x, max_x)
                      for x_channel in x]
    x = np.stack(channel_images, axis=0)
    x = np.rollaxis(x, 0, channel_index+1)
    return x


def transform_matrix_offset_center(matrix, x, y):
    o_x = float(x) / 2 + 0.5
    o_y = float(y) / 2 + 0.5
    offset_matrix = np.array([[1, 0, o_x], [0, 1, o_y], [0, 0, 1]])
    reset_matrix = np.array([[1, 0, -o_x], [0, 1, -o_y], [0, 0, 1]])
    transform_matrix = np.dot(np.dot(offset_matrix, matrix), reset_matrix)
    return transform_matrix


def apply_transform(x, transform_matrix, channel_index=0, fill_mode='nearest', cval=0.):
    x = np.rollaxis(x, channel_index, 0)
    final_affine_matrix = transform_matrix[:2, :2]
    final_offset = transform_matrix[:2, 2]
    channel_images = [ndi.interpolation.affine_transform(x_channel, final_affine_matrix,
                      final_offset, order=0, mode=fill_mode, cval=cval) for x_channel in x]
    x = np.stack(channel_images, axis=0)
    x = np.rollaxis(x, 0, channel_index+1)
    return x


def flip_axis(x, axis):
    x = np.asarray(x).swapaxes(axis, 0)
    x = x[::-1, ...]
    x = x.swapaxes(0, axis)
    return x


def array_to_img(x, dim_ordering='th', scale=True):
    from PIL import Image
    if dim_ordering == 'th':
        x = x.transpose(1, 2, 0)
    if scale:
        x += max(-np.min(x), 0)
        x /= np.max(x)
        x *= 255
    if x.shape[2] == 3:
        # RGB
        return Image.fromarray(x.astype('uint8'), 'RGB')
    elif x.shape[2] == 1:
        # grayscale
        return Image.fromarray(x[:, :, 0].astype('uint8'), 'L')
    else:
        raise Exception('Unsupported channel number: ', x.shape[2])


# only used by tests/keras/preprocessing/test_image.py to convert PIL.Image to numpy array
def img_to_array(img, dim_ordering='th'):
    if dim_ordering not in ['th', 'tf']:
        raise Exception('Unknown dim_ordering: ', dim_ordering)
    # image has dim_ordering (height, width, channel)
    x = np.asarray(img, dtype='float32')
    if len(x.shape) == 3:
        if dim_ordering == 'th':
            x = x.transpose(2, 0, 1)
    elif len(x.shape) == 2:
        if dim_ordering == 'th':
            x = x.reshape((1, x.shape[0], x.shape[1]))
        else:
            x = x.reshape((x.shape[0], x.shape[1], 1))
    else:
        raise Exception('Unsupported image shape: ', x.shape)
    return x


def load_img(path, grayscale=False):
    from PIL import Image
    img = Image.open(path)
    if grayscale:
        img = img.convert('L')
    else:  # Ensure 3 channel even when loaded image is grayscale
        img = img.convert('RGB')
    return img


def list_pictures(directory, ext='jpg|jpeg|bmp|png'):
    return [os.path.join(directory, f) for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f)) and re.match('([\w]+\.(?:' + ext + '))', f)]


class ImageDataGenerator(object):
    '''Generate minibatches with
    real-time data augmentation.

    # Arguments
        featurewise_center: set input mean to 0 over the dataset.
        samplewise_center: set each sample mean to 0.
        featurewise_std_normalization: divide inputs by std of the dataset.
        samplewise_std_normalization: divide each input by its std.
        zca_whitening: apply ZCA whitening.
        rotation_range: degrees (0 to 180).
        width_shift_range: fraction of total width.
        height_shift_range: fraction of total height.
        shear_range: shear intensity (shear angle in radians).
        zoom_range: amount of zoom. if scalar z, zoom will be randomly picked
            in the range [1-z, 1+z]. A sequence of two can be passed instead
            to select this range.
        channel_shift_range: shift range for each channels.
        fill_mode: points outside the boundaries are filled according to the
            given mode ('constant', 'nearest', 'reflect' or 'wrap'). Default
            is 'nearest'.
        cval: value used for points outside the boundaries when fill_mode is
            'constant'. Default is 0.
        horizontal_flip: whether to randomly flip images horizontally.
        vertical_flip: whether to randomly flip images vertically.
        dim_ordering: 'th' or 'tf'. In 'th' mode, the channels dimension
            (the depth) is at index 1, in 'tf' mode it is at index 3.
    '''
    def __init__(self,
                 featurewise_center=False,
                 samplewise_center=False,
                 featurewise_std_normalization=False,
                 samplewise_std_normalization=False,
                 zca_whitening=False,
                 rotation_range=0.,
                 width_shift_range=0.,
                 height_shift_range=0.,
                 shear_range=0.,
                 zoom_range=0.,
                 channel_shift_range=0.,
                 fill_mode='nearest',
                 cval=0.,
                 horizontal_flip=False,
                 vertical_flip=False,
                 dim_ordering='th'):
        self.__dict__.update(locals())
        self.mean = None
        self.std = None
        self.principal_components = None
        self.lock = threading.Lock()

        if dim_ordering not in {'tf', 'th'}:
            raise Exception('dim_ordering should be "tf" (channel after row and '
                            'column) or "th" (channel before row and column). '
                            'Received arg: ', dim_ordering)
        self.dim_ordering = dim_ordering
        if dim_ordering == "th":
            self.channel_index = 1
            self.row_index = 2
            self.col_index = 3
        if dim_ordering == "tf":
            self.channel_index = 3
            self.row_index = 1
            self.col_index = 2

        if np.isscalar(zoom_range):
            self.zoom_range = [1 - zoom_range, 1 + zoom_range]
        elif len(zoom_range) == 2:
            self.zoom_range = [zoom_range[0], zoom_range[1]]
        else:
            raise Exception('zoom_range should be a float or '
                            'a tuple or list of two floats. '
                            'Received arg: ', zoom_range)

        self.batch_index = 0
        self.total_batches_seen = 0

    def reset(self):
        self.batch_index = 0

    def _flow_index(self, N, batch_size=32, shuffle=False, seed=None):
        while 1:
            index_array = np.arange(N)
            if self.batch_index == 0:
                if shuffle:
                    if seed is not None:
                        np.random.seed(seed + self.total_batches_seen)
                    index_array = np.random.permutation(N)

            current_index = (self.batch_index * batch_size) % N
            if N >= current_index + batch_size:
                current_batch_size = batch_size
                self.batch_index += 1
            else:
                current_batch_size = N - current_index
                self.batch_index = 0
            self.total_batches_seen += 1
            yield (index_array[current_index: current_index + current_batch_size],
                   current_index, current_batch_size)

    def flow(self, X, y, batch_size=32, shuffle=False, seed=None,
             save_to_dir=None, save_prefix='', save_format='jpeg'):
        assert len(X) == len(y)
        self.X = X
        self.y = y
        self.save_to_dir = save_to_dir
        self.save_prefix = save_prefix
        self.save_format = save_format
        self.reset()
        self.flow_generator = self._flow_index(X.shape[0], batch_size,
                                               shuffle, seed)
        return self

    def __iter__(self):
        # needed if we want to do something like:
        # for x, y in data_gen.flow(...):
        return self

    def next(self):
        # for python 2.x.
        # Keeps under lock only the mechanism which advances
        # the indexing of each batch
        # see # http://anandology.com/blog/using-iterators-and-generators/
        with self.lock:
            index_array, current_index, current_batch_size = next(self.flow_generator)
        # The transformation of images is not under thread lock so it can be done in parallel
        bX = np.zeros(tuple([current_batch_size] + list(self.X.shape)[1:]))
        for i, j in enumerate(index_array):
            x = self.X[j]
            x = self.random_transform(x.astype('float32'))
            x = self.standardize(x)
            bX[i] = x
        if self.save_to_dir:
            for i in range(current_batch_size):
                img = array_to_img(bX[i], self.dim_ordering, scale=True)
                fname = '{prefix}_{index}.{format}'.format(prefix=self.save_prefix,
                                                           index=current_index + i,
                                                           format=self.save_format)
                img.save(os.path.join(self.save_to_dir, fname))
        bY = self.y[index_array]
        return bX, bY

    def __next__(self):
        # for python 3.x.
        return self.next()

    def standardize(self, x):
        # x is a single image, so it doesn't have image number at index 0
        img_channel_index = self.channel_index - 1
        if self.samplewise_center:
            x -= np.mean(x, axis=img_channel_index, keepdims=True)
        if self.samplewise_std_normalization:
            x /= (np.std(x, axis=img_channel_index, keepdims=True) + 1e-7)

        if self.featurewise_center:
            x -= self.mean
        if self.featurewise_std_normalization:
            x /= (self.std + 1e-7)

        if self.zca_whitening:
            flatx = np.reshape(x, (x.size))
            whitex = np.dot(flatx, self.principal_components)
            x = np.reshape(whitex, (x.shape[0], x.shape[1], x.shape[2]))

        return x

    def random_transform(self, x):
        # x is a single image, so it doesn't have image number at index 0
        img_row_index = self.row_index - 1
        img_col_index = self.col_index - 1
        img_channel_index = self.channel_index - 1

        # use composition of homographies to generate final transform that needs to be applied
        if self.rotation_range:
            theta = np.pi / 180 * np.random.uniform(-self.rotation_range, self.rotation_range)
        else:
            theta = 0
        rotation_matrix = np.array([[np.cos(theta), -np.sin(theta), 0],
                                    [np.sin(theta), np.cos(theta), 0],
                                    [0, 0, 1]])
        if self.height_shift_range:
            tx = np.random.uniform(-self.height_shift_range, self.height_shift_range) * x.shape[img_row_index]
        else:
            tx = 0

        if self.width_shift_range:
            ty = np.random.uniform(-self.width_shift_range, self.width_shift_range) * x.shape[img_col_index]
        else:
            ty = 0

        translation_matrix = np.array([[1, 0, tx],
                                       [0, 1, ty],
                                       [0, 0, 1]])
        if self.shear_range:
            shear = np.random.uniform(-self.shear_range, self.shear_range)
        else:
            shear = 0
        shear_matrix = np.array([[1, -np.sin(shear), 0],
                                 [0, np.cos(shear), 0],
                                 [0, 0, 1]])

        if self.zoom_range[0] == 1 and self.zoom_range[1] == 1:
            zx, zy = 1, 1
        else:
            zx, zy = np.random.uniform(self.zoom_range[0], self.zoom_range[1], 2)
        zoom_matrix = np.array([[zx, 0, 0],
                                [0, zy, 0],
                                [0, 0, 1]])

        transform_matrix = np.dot(np.dot(np.dot(rotation_matrix, translation_matrix), shear_matrix), zoom_matrix)

        h, w = x.shape[img_row_index], x.shape[img_col_index]
        transform_matrix = transform_matrix_offset_center(transform_matrix, h, w)
        x = apply_transform(x, transform_matrix, img_channel_index,
                            fill_mode=self.fill_mode, cval=self.cval)
        if self.channel_shift_range != 0:
            x = random_channel_shift(x, self.channel_shift_range, img_channel_index)

        if self.horizontal_flip:
            if np.random.random() < 0.5:
                x = flip_axis(x, img_col_index)

        if self.vertical_flip:
            if np.random.random() < 0.5:
                x = flip_axis(x, img_row_index)

        # TODO:
        # channel-wise normalization
        # barrel/fisheye
        return x

    def fit(self, X,
            augment=False,
            rounds=1,
            seed=None):
        '''Required for featurewise_center, featurewise_std_normalization
        and zca_whitening.

        # Arguments
            X: Numpy array, the data to fit on.
            augment: whether to fit on randomly augmented samples
            rounds: if `augment`,
                how many augmentation passes to do over the data
            seed: random seed.
        '''
        X = np.copy(X)
        if augment:
            aX = np.zeros(tuple([rounds * X.shape[0]] + list(X.shape)[1:]))
            for r in range(rounds):
                for i in range(X.shape[0]):
                    aX[i + r * X.shape[0]] = self.random_transform(X[i])
            X = aX

        if self.featurewise_center:
            self.mean = np.mean(X, axis=0)
            X -= self.mean

        if self.featurewise_std_normalization:
            self.std = np.std(X, axis=0)
            X /= (self.std + 1e-7)

        if self.zca_whitening:
            flatX = np.reshape(X, (X.shape[0], X.shape[1] * X.shape[2] * X.shape[3]))
            sigma = np.dot(flatX.T, flatX) / flatX.shape[1]
            U, S, V = linalg.svd(sigma)
            self.principal_components = np.dot(np.dot(U, np.diag(1. / np.sqrt(S + 10e-7))), U.T)


class GraphImageDataGenerator(ImageDataGenerator):
    '''Example of how to build a generator for a Graph model
    '''
    def next(self):
        bX, bY = super(GraphImageDataGenerator, self).next()
        return {'input': bX, 'output': bY}

# note: topology.Node is an internal class,
# it isn't meant to be used by Keras users.
from .topology import InputSpec
from .topology import Input
from .topology import InputLayer
from .topology import Layer
from .topology import Merge
from .topology import merge
from .topology import get_source_inputs
from .training import Model

# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import numpy as np

import sys
import marshal
import types as python_types
import warnings
import copy
from six.moves import zip

from keras import backend as K


def to_list(x):
    '''This normalizes a list/tensor into a list.

    If a tensor is passed, we return
    a list of size 1 containing the tensor.
    '''
    if type(x) is list:
        return x
    return [x]


class InputSpec(object):
    '''This specifies the ndim, dtype and shape of every input to a layer.
    Every layer should expose (if appropriate) an `input_spec` attribute:
    a list of instances of InputSpec (one per input tensor).

    A None entry in a shape is compatible with any dimension,
    a None shape is compatible with any shape.
    '''
    def __init__(self, dtype=None, shape=None, ndim=None):
        if type(ndim) is str:
            assert '+' in ndim, 'When passing a str "ndim", it should have the form "2+", "3+", etc.'
            int_ndim = ndim[:ndim.find('+')]
            assert int_ndim.isdigit(), 'When passing a str "ndim", it should have the form "2+", "3+", etc.'
        if shape is not None:
            self.ndim = len(shape)
        else:
            self.ndim = ndim
        self.dtype = dtype
        self.shape = shape


class Node(object):
    '''A `Node` describes the connectivity between two layers.

    Each time a layer is connected to some new input,
    a node is added to `layer.inbound_nodes`.
    Each time the output of a layer is used by another layer,
    a node is added to `layer.outbound_nodes`.

    # Attributes
        outbound_layer: the layer that takes
            `input_tensors` and turns them into `output_tensors`.
        inbound_layers: a list of layers, the same length as `input_tensors`,
            the layers from where `input_tensors` originate.
        node_indices: a list of integers, the same length as `inbound_layers`.
            `node_indices[i]` is the origin node of `input_tensors[i]`
            (necessary since each inbound layer might have several nodes,
            e.g. if the layer is being shared with a different data stream).
        tensor_indices: a list of integers, the same length as `inbound_layers`.
            `tensor_indices[i]` is the index of `input_tensors[i]` within the
            output of the inbound layer (necessary since each inbound layer might
            have multiple tensor outputs, with each one being
            independently manipulable).
        input_tensors: list of input tensors.
        output_tensors: list of output tensors.
        input_masks: list of input masks (a mask can be a tensor, or None).
        output_masks: list of output masks (a mask can be a tensor, or None).
        input_shapes: list of input shape tuples.
        output_shapes: list of output shape tuples.

    `node_indices` and `tensor_indices` are basically fine-grained coordinates
    describing the origin of the `input_tensors`, verifying the following:

    `input_tensors[i] == inbound_layers[i].inbound_nodes[node_indices[i]].output_tensors[tensor_indices[i]]`

    A node from layer A to layer B is added to:
        A.outbound_nodes
        B.inbound_nodes
    '''
    def __init__(self, outbound_layer,
                 inbound_layers, node_indices, tensor_indices,
                 input_tensors, output_tensors,
                 input_masks, output_masks,
                 input_shapes, output_shapes):
        # layer instance (NOT a list).
        # this is the layer that takes a list of input tensors
        # and turns them into a list of output tensors.
        # the current node will be added to the inbound_nodes of outbound_layer
        self.outbound_layer = outbound_layer

        # the following 3 properties describe where
        # the input tensors come from: which layers,
        # and for each layer, which node and which
        # tensor output of each node.
        self.inbound_layers = inbound_layers  # list of layer instances
        self.node_indices = node_indices  # list of integers, 1:1 mapping with inbound_layers
        self.tensor_indices = tensor_indices  # list of integers, 1:1 mapping with inbound_layers

        # tensor inputs and outputs of outbound_layer
        self.input_tensors = input_tensors  # list of tensors. 1:1 mapping with inbound_layers
        self.output_tensors = output_tensors  # list of tensors, created by outbound_layer.call()

        # input and output masks
        self.input_masks = input_masks  # list of tensors, 1:1 mapping with input_tensor
        self.output_masks = output_masks  # list of tensors, created by outbound_layer.compute_mask()

        # input and output shapes
        self.input_shapes = input_shapes  # list of shape tuples, shapes of input_tensors
        self.output_shapes = output_shapes  # list of shape tuples, shapes of output_tensors

        # add nodes to all layers involved.
        for layer in inbound_layers:
            if layer is not None:
                layer.outbound_nodes.append(self)
        outbound_layer.inbound_nodes.append(self)

    @classmethod
    def create_node(cls, outbound_layer,
                    inbound_layers, node_indices=None, tensor_indices=None):
        if not node_indices:
            node_indices = [0 for _ in range(len(inbound_layers))]
        else:
            assert len(node_indices) == len(inbound_layers)
        if not tensor_indices:
            tensor_indices = [0 for _ in range(len(inbound_layers))]

        input_tensors = []
        input_masks = []
        input_shapes = []

        for inbound_layer, node_index, tensor_index in zip(inbound_layers, node_indices, tensor_indices):
            inbound_node = inbound_layer.inbound_nodes[node_index]
            input_tensors.append(inbound_node.output_tensors[tensor_index])
            input_masks.append(inbound_node.output_masks[tensor_index])
            input_shapes.append(inbound_node.output_shapes[tensor_index])

        assert len(input_shapes) == len(input_tensors) == len(input_masks)

        if len(input_tensors) == 1:
            output_tensors = to_list(outbound_layer.call(input_tensors[0], mask=input_masks[0]))
            output_masks = to_list(outbound_layer.compute_mask(input_tensors[0], input_masks[0]))
            # TODO: try to auto-infer shape if exception is raised by get_output_shape_for
            output_shapes = to_list(outbound_layer.get_output_shape_for(input_shapes[0]))
        else:
            output_tensors = to_list(outbound_layer.call(input_tensors, mask=input_masks))
            output_masks = to_list(outbound_layer.compute_mask(input_tensors, input_masks))
            output_shapes = to_list(outbound_layer.get_output_shape_for(input_shapes))

        if not output_tensors or output_tensors[0] is None:
            raise Exception('The `call` method of layer "' +
                            outbound_layer.name +
                            '" should return a tensor. Found: ' +
                            str(output_tensors[0]))
        if len(output_tensors) != len(output_shapes):
            raise Exception('The `get_output_shape_for` method of layer "' +
                            outbound_layer.name +
                            '"" should return one shape tuple per '
                            'output tensor of the layer. Found: ' +
                            str(output_shapes))
        if len(output_tensors) != len(output_masks):
            raise Exception('The `compute_mask` method of layer "' +
                            outbound_layer.name +
                            '" should return one mask tensor per '
                            'output tensor of the layer. Found: ' +
                            str(output_masks))

        for i in range(len(output_tensors)):
            output_tensors[i]._keras_shape = output_shapes[i]
            output_tensors[i]._uses_learning_phase = any([x._uses_learning_phase for x in input_tensors]) or outbound_layer.uses_learning_phase
            output_tensors[i]._keras_history = (outbound_layer, len(outbound_layer.inbound_nodes), i)

        return cls(outbound_layer,
                   inbound_layers, node_indices, tensor_indices,
                   input_tensors, output_tensors,
                   input_masks, output_masks,
                   input_shapes, output_shapes)

    def get_config(self):
        inbound_names = []
        for layer in self.inbound_layers:
            if layer:
                inbound_names.append(layer.name)
            else:
                inbound_names.append(None)
        return {'outbound_layer': self.outbound_layer.name if self.outbound_layer else None,
                'inbound_layers': inbound_names,
                'node_indices': self.node_indices,
                'tensor_indices': self.tensor_indices}


class Layer(object):
    '''Abstract base layer class.

    # Properties
        name: string, must be unique within a model.
        input_spec: list of InputSpec class instances
            each entry describes one required input:
                - ndim
                - dtype
            A layer with `n` input tensors must have
            an `input_spec` of length `n`.
        trainable: boolean, whether the layer weights
            will be updated during training.
        uses_learning_phase: whether any operation
            of the layer uses `K.in_training_phase()`
            or `K.in_test_phase()`.
        input_shape: shape tuple. Provided for convenience,
            but note that there may be cases in which this
            attribute is ill-defined (e.g. a shared layer
            with multiple input shapes), in which case
            requesting `input_shape` will raise an Exception.
            Prefer using `layer.get_input_shape_for(input_shape)`,
            or `layer.get_input_shape_at(node_index)`.
        output_shape: shape tuple. See above.
        inbound_nodes: list of nodes.
        outbound_nodes: list of nodes.
        supports_masking: boolean
        input, output: input/output tensor(s). Note that if the layer is used
            more than once (shared layer), this is ill-defined
            and will raise an exception. In such cases, use
            `layer.get_input_at(node_index)`.
        input_mask, output_mask: same as above, for masks.

        trainable_weights: list of variables.
        non_trainable_weights: list of variables.
        regularizers: list of regularizers.
        constraints: dict mapping weights to constraints.

    # Methods
        call(x, mask=None): where the layer's logic lives.
        __call__(x, mask=None): wrapper around the layer logic (`call`).
            if x is a Keras tensor:
                - connect current layer with last layer from tensor:
                    `self.add_inbound_node(last_layer)`
                - add layer to tensor history
            if layer is not built:
                - build from x._keras_shape
        get_weights()
        set_weights(weights)
        get_config()
        count_params()
        get_output_shape_for(input_shape)
        compute_mask(x, mask)
        get_input_at(node_index)
        get_output_at(node_index)
        get_input_shape_at(node_index)
        get_output_shape_at(node_index)
        get_input_mask_at(node_index)
        get_output_mask_at(node_index)

    # Class Methods
        from_config(config)

    # Internal methods:
        build(input_shape)
        add_inbound_node(layer, index=0)
        create_input_layer()
        assert_input_compatibility()
    '''
    def __init__(self, **kwargs):
        # these properties should have been set
        # by the child class, as appropriate.
        if not hasattr(self, 'input_spec'):
            self.input_spec = None
        if not hasattr(self, 'supports_masking'):
            self.supports_masking = False
        if not hasattr(self, 'uses_learning_phase'):
            self.uses_learning_phase = False

        # these lists will be filled via successive calls
        # to self.add_inbound_node()
        self.inbound_nodes = []
        self.outbound_nodes = []

        # these properties will be set upon call of self.build(),
        # which itself will be calld upon self.add_inbound_node if necessary.
        self.trainable_weights = []
        self.non_trainable_weights = []
        self.regularizers = []
        self.constraints = {}  # dict {tensor: constraint instance}
        self.built = False

        # these properties should be set by the user via keyword arguments.
        # note that 'input_dtype', 'input_shape' and 'batch_input_shape'
        # are only applicable to input layers: do not pass these keywords
        # to non-input layers.
        allowed_kwargs = {'input_shape',
                          'batch_input_shape',
                          'input_dtype',
                          'name',
                          'trainable',
                          'create_input_layer'}
        for kwarg in kwargs.keys():
            assert kwarg in allowed_kwargs, 'Keyword argument not understood: ' + kwarg

        name = kwargs.get('name')
        if not name:
            prefix = self.__class__.__name__.lower()
            name = prefix + '_' + str(K.get_uid(prefix))
        self.name = name

        self.trainable = kwargs.get('trainable', True)
        if 'batch_input_shape' in kwargs or 'input_shape' in kwargs:
            # in this case we will create an input layer
            # to insert before the current layer
            if 'batch_input_shape' in kwargs:
                batch_input_shape = tuple(kwargs['batch_input_shape'])
            elif 'input_shape' in kwargs:
                batch_input_shape = (None,) + tuple(kwargs['input_shape'])
            self.batch_input_shape = batch_input_shape
            input_dtype = kwargs.get('input_dtype', K.floatx())
            self.input_dtype = input_dtype
            if 'create_input_layer' in kwargs:
                self.create_input_layer(batch_input_shape, input_dtype)

    def create_input_layer(self, batch_input_shape,
                           input_dtype=None, name=None):
        if not name:
            prefix = self.__class__.__name__.lower() + '_input_'
            name = prefix + str(K.get_uid(prefix))
        if not input_dtype:
            input_dtype = K.floatx()

        self.batch_input_shape = batch_input_shape
        self.input_dtype = input_dtype

        # instantiate the input layer
        x = Input(batch_shape=batch_input_shape,
                  dtype=input_dtype, name=name)
        # this will build the current layer
        # and create the node connecting the current layer
        # to the input layer we just created.
        self(x)

    def assert_input_compatibility(self, input):
        '''This checks that the tensor(s) `input`
        verify the input assumptions of the layer
        (if any). If not, exceptions are raised.
        '''
        if not self.input_spec:
            return True
        assert type(self.input_spec) is list, ('input_spec must be a list of ' +
                                               'InputSpec instances. Found: ' +
                                               str(self.input_spec))
        inputs = to_list(input)
        if len(self.input_spec) > 1:
            if len(inputs) != len(self.input_spec):
                raise Exception('Layer ' + self.name + ' expects ' +
                                str(len(self.input_spec)) + ' inputs, '
                                'but it received ' + str(len(inputs)) +
                                ' input tensors. Input received: ' +
                                str(input))
        for input_index, (x, spec) in enumerate(zip(inputs, self.input_spec)):
            if spec is None:
                continue

            # check ndim
            if spec.ndim is not None:
                if type(spec.ndim) is str:
                    int_ndim = spec.ndim[:spec.ndim.find('+')]
                    ndim = int(int_ndim)
                    if K.ndim(x) < ndim:
                        raise Exception('Input ' + str(input_index) +
                                        ' is incompatible with layer ' +
                                        self.name + ': expected ndim >= ' +
                                        str(ndim) + ', found ndim=' +
                                        str(K.ndim(x)))
                else:
                    if K.ndim(x) != spec.ndim:
                        raise Exception('Input ' + str(input_index) +
                                        ' is incompatible with layer ' +
                                        self.name + ': expected ndim=' +
                                        str(spec.ndim) + ', found ndim=' +
                                        str(K.ndim(x)))
            if spec.dtype is not None:
                if K.dtype(x) != spec.dtype:
                    raise Exception('Input ' + str(input_index) +
                                    ' is incompatible with layer ' +
                                    self.name + ': expected dtype=' +
                                    str(spec.dtype) + ', found dtype=' +
                                    str(K.dtype(x)))
            if spec.shape is not None:
                if hasattr(x, '_keras_shape'):
                    x_shape = x._keras_shape
                elif hasattr(K, 'int_shape'):
                    # tensorflow shape inference
                    x_shape = K.int_shape(x)
                else:
                    continue
                for spec_dim, dim in zip(spec.shape, x_shape):
                    if spec_dim is not None:
                        if spec_dim != dim:
                            raise Exception('Input ' + str(input_index) +
                                            ' is incompatible with layer ' +
                                            self.name + ': expected shape=' +
                                            str(spec.shape) + ', found shape=' +
                                            str(x_shape))

    def call(self, x, mask=None):
        '''This is where the layer's logic lives.

        # Arguments
            x: input tensor, or list/tuple of input tensors.
            mask: a masking tensor (or list of tensors). Used mainly in RNNs.

        # Returns:
            A tensor or list/tuple of tensors.
        '''
        return x

    def __call__(self, x, mask=None):
        '''Wrapper around self.call(), for handling
        internal Keras references.

        If a Keras tensor is passed:
            - we call self.add_inbound_node()
            - if necessary, we `build` the layer to match
                the _keras_shape of the input(s)
            - we update the _keras_shape of every input tensor with
                its new shape (obtained via self.get_output_shape_for).
                This is done as part of add_inbound_node().
            - we update the _keras_history of the output tensor(s)
                with the current layer.
                This is done as part of add_inbound_node().

        # Arguments
            x: can be a tensor or list/tuple of tensors.
            mask: tensor or list/tuple of tensors.
        '''
        if not self.built:
            # raise exceptions in case the input is not compatible
            # with the input_spec specified in the layer constructor
            self.assert_input_compatibility(x)

            # collect input shapes to build layer
            input_shapes = []
            for x_elem in to_list(x):
                if hasattr(x_elem, '_keras_shape'):
                    input_shapes.append(x_elem._keras_shape)
                elif hasattr(K, 'int_shape'):
                    input_shapes.append(K.int_shape(x_elem))
                else:
                    raise Exception('You tried to call layer "' + self.name +
                                    '". This layer has no information'
                                    ' about its expected input shape, '
                                    'and thus cannot be built. '
                                    'You can build it manually via: '
                                    '`layer.build(batch_input_shape)`')
            if len(input_shapes) == 1:
                self.build(input_shapes[0])
            else:
                self.build(input_shapes)
            self.built = True

        # raise exceptions in case the input is not compatible
        # with the input_spec set at build time
        self.assert_input_compatibility(x)
        # build and connect layer
        input_added = False
        input_tensors = to_list(x)

        inbound_layers = []
        node_indices = []
        tensor_indices = []
        for input_tensor in input_tensors:
            if hasattr(input_tensor, '_keras_history') and input_tensor._keras_history:
                # this is a Keras tensor
                previous_layer, node_index, tensor_index = input_tensor._keras_history
                inbound_layers.append(previous_layer)
                node_indices.append(node_index)
                tensor_indices.append(tensor_index)
            else:
                inbound_layers = None
                break
        if inbound_layers:
            # this will call layer.build() if necessary
            self.add_inbound_node(inbound_layers, node_indices, tensor_indices)
            input_added = True

        # get the output tensor to be returned
        if input_added:
            # output was already computed when calling self.add_inbound_node
            outputs = self.inbound_nodes[-1].output_tensors
            # if single output tensor: return it,
            # else return a list (at least 2 elements)
            if len(outputs) == 1:
                return outputs[0]
            else:
                return outputs
        else:
            # this case appears if the input was not a Keras tensor
            return self.call(x, mask)

    def add_inbound_node(self, inbound_layers,
                         node_indices=None, tensor_indices=None):
        '''
        # Arguments:
            inbound_layers: can be a layer instance
                or a list/tuple of layer instances.
            node_indices: integer (or list of integers).
                The input layer might have a number of
                parallel output streams;
                this is the index of the stream (in the input layer)
                where to connect the current layer.
            tensor_indices: integer or list of integers.
                The output of the inbound node might be a list/tuple
                of tensor, and we might only be interested in one sepcific entry.
                This index allows you to specify the index of the entry in the output list
                (if applicable). "None" means that we take all outputs (as a list).
        '''
        inbound_layers = to_list(inbound_layers)
        if not node_indices:
            node_indices = [0 for _ in range(len(inbound_layers))]
        else:
            node_indices = to_list(node_indices)
            assert len(node_indices) == len(inbound_layers)
        if not tensor_indices:
            tensor_indices = [0 for _ in range(len(inbound_layers))]
        else:
            tensor_indices = to_list(tensor_indices)

        if not self.built:
            # collect input_shapes for call to build()
            input_shapes = []
            for layer, node_index, tensor_index in zip(inbound_layers, node_indices, tensor_indices):
                input_shapes.append(layer.inbound_nodes[node_index].output_shapes[tensor_index])
            # call build()
            if len(input_shapes) == 1:
                self.build(input_shape=input_shapes[0])
            else:
                self.build(input_shape=input_shapes)
            self.built = True
        # creating the node automatically updates self.inbound_nodes
        # as well as outbound_nodes on inbound layers.
        Node.create_node(self, inbound_layers, node_indices, tensor_indices)

    def get_output_shape_for(self, input_shape):
        '''Computes the output shape of the layer given
        an input shape (assumes that the layer will be built
        to match that input shape).

        # Arguments
            input_shape: shape tuple (tuple of integers)
                or list of shape tuples (one per output tensor of the layer).
                Shape tuples can include None for free dimensions,
                instead of an integer.
        '''
        return input_shape

    def compute_mask(self, input, input_mask=None):
        '''Computes an output masking tensor, given an input tensor
        (or list thereof) and an input mask (or list thereof).

        # Arguments
            input: tensor or list of tensors.
            input_mask: tensor or list of tensors.

        # Returns
            None or a tensor (or list of tensors,
                one per output tensor of the layer).
        '''
        if not hasattr(self, 'supports_masking') or not self.supports_masking:
            if input_mask is not None:
                if type(input_mask) is list:
                    if any(input_mask):
                        raise Exception('Layer ' + self.name + ' does not support masking, ' +
                                        'but was passed an input_mask: ' + str(input_mask))
                else:
                    raise Exception('Layer ' + self.name + ' does not support masking, ' +
                                    'but was passed an input_mask: ' + str(input_mask))
            # masking not explicitly supported: return None as mask
            return None
        # if masking is explictly supported, by default
        # carry over the input mask
        return input_mask

    def build(self, input_shape):
        '''Creates the layer weights.
        Must be implemented on all layers that have weights.

        # Arguments
            input_shape: Keras tensor (future input to layer)
                or list/tuple of Keras tensors to reference
                for weight shape computations.
        '''
        self.built = True

    def _get_node_attribute_at_index(self, node_index, attr, attr_name):
        '''Retrieves an attribute (e.g. input_tensors) from a node.

        # Arguments
            node_index: integer index of the node from which
                to retrieve the attribute
            attr: exact node attribute name
            attr_name: human-readable attribute name, for error messages
        '''
        if not self.inbound_nodes:
            raise Exception('The layer has never been called ' +
                            'and thus has no defined ' + attr_name + '.')
        if not len(self.inbound_nodes) > node_index:
            raise Exception('Asked to get ' + attr_name +
                            ' at node ' + str(node_index) +
                            ', but the layer has only ' +
                            str(len(self.inbound_nodes)) + ' inbound nodes.')
        values = getattr(self.inbound_nodes[node_index], attr)
        if len(values) == 1:
            return values[0]
        else:
            return values

    def get_input_shape_at(self, node_index):
        '''Retrieves the input shape(s) of a layer at a given node.
        '''
        return self._get_node_attribute_at_index(node_index,
                                                 'input_shapes',
                                                 'input shape')

    def get_output_shape_at(self, node_index):
        '''Retrieves the output shape(s) of a layer at a given node.
        '''
        return self._get_node_attribute_at_index(node_index,
                                                 'output_shapes',
                                                 'output shape')

    def get_input_at(self, node_index):
        '''Retrieves the input tensor(s) of a layer at a given node.
        '''
        return self._get_node_attribute_at_index(node_index,
                                                 'input_tensors',
                                                 'input')

    def get_output_at(self, node_index):
        '''Retrieves the output tensor(s) of a layer at a given node.
        '''
        return self._get_node_attribute_at_index(node_index,
                                                 'output_tensors',
                                                 'output')

    def get_input_mask_at(self, node_index):
        '''Retrieves the input mask tensor(s) of a layer at a given node.
        '''
        return self._get_node_attribute_at_index(node_index,
                                                 'input_masks',
                                                 'input mask')

    def get_output_mask_at(self, node_index):
        '''Retrieves the output mask tensor(s) of a layer at a given node.
        '''
        return self._get_node_attribute_at_index(node_index,
                                                 'output_masks',
                                                 'output mask')

    @property
    def input(self):
        '''Retrieves the input tensor(s) of a layer (only applicable if
        the layer has exactly one inbound node, i.e. if it is connected
        to one incoming layer).
        '''
        if len(self.inbound_nodes) > 1:
            raise Exception('Layer ' + self.name +
                            ' has multiple inbound nodes, ' +
                            'hence the notion of "layer input" '
                            'is ill-defined. '
                            'Use `get_input_at(node_index)` instead.')
        elif not self.inbound_nodes:
            raise Exception('Layer ' + self.name +
                            ' is not connected, no input to return.')
        return self._get_node_attribute_at_index(0, 'input_tensors',
                                                 'input')

    def set_input(self, input_tensor, shape=None):
        if len(self.inbound_nodes) > 1:
            raise Exception('Cannot `set_input` for layer ' + self.name +
                            ' because it has more than one inbound connection.')
        if len(self.inbound_nodes) == 1:
            # check that the inbound node is an Input node
            if self.inbound_nodes[0].inbound_layers:
                warnings.warn('You are manually setting the input for layer ' +
                              self.name + ' but it is not an Input layer. '
                              'This will cause part of your model '
                              'to be disconnected.')
        if self.outbound_nodes:
            warnings.warn('You are manually setting the input for layer ' +
                          self.name + ' but it has ' +
                          str(len(self.outbound_nodes)) +
                          ' outbound layers. '
                          'This will cause part of your model '
                          'to be disconnected.')
        if not shape:
            if hasattr(K, 'int_shape'):
                shape = K.int_shape(input_tensor)
            else:
                raise Exception('`set_input` needs to know the shape '
                                'of the `input_tensor` it receives, but '
                                'Keras was not able to infer it automatically.'
                                ' Specify it via: '
                                '`model.set_input(input_tensor, shape)`')
        # reset layer connections
        self.inbound_nodes = []
        self.outbound_nodes = []
        input_shape = tuple(shape)
        self.build(input_shape=input_shape)

        # set Keras tensor metadata
        input_tensor._uses_learning_phase = False
        input_tensor._keras_history = (None, 0, 0)
        input_tensor._keras_shape = input_shape

        output_tensors = to_list(self.call(input_tensor))
        output_shapes = to_list(self.get_output_shape_for(input_shape))
        output_masks = to_list(self.compute_mask(input_tensor, None))

        for i, output_tensor in enumerate(output_tensors):
            output_tensor._keras_history = (self, 0, i)
            output_tensor._keras_shape = output_shapes[i]
            output_tensor._uses_learning_phase = self.uses_learning_phase

        # create node
        Node(self,
             inbound_layers=[],
             node_indices=[],
             tensor_indices=[],
             input_tensors=[input_tensor],
             output_tensors=output_tensors,
             input_masks=[None],
             output_masks=output_masks,
             input_shapes=[input_shape],
             output_shapes=output_shapes)

    @property
    def output(self):
        '''Retrieves the output tensor(s) of a layer (only applicable if
        the layer has exactly one inbound node, i.e. if it is connected
        to one incoming layer).
        '''
        if len(self.inbound_nodes) != 1:
            raise Exception('Layer ' + self.name +
                            ' has multiple inbound nodes, ' +
                            'hence the notion of "layer output" '
                            'is ill-defined. '
                            'Use `get_output_at(node_index)` instead.')
        return self._get_node_attribute_at_index(0, 'output_tensors',
                                                 'output')

    @property
    def input_mask(self):
        '''Retrieves the input mask tensor(s) of a layer (only applicable if
        the layer has exactly one inbound node, i.e. if it is connected
        to one incoming layer).
        '''
        if len(self.inbound_nodes) != 1:
            raise Exception('Layer ' + self.name +
                            ' has multiple inbound nodes, ' +
                            'hence the notion of "layer input mask" '
                            'is ill-defined. '
                            'Use `get_input_mask_at(node_index)` instead.')
        return self._get_node_attribute_at_index(0, 'input_masks',
                                                 'input mask')

    @property
    def output_mask(self):
        '''Retrieves the output mask tensor(s) of a layer (only applicable if
        the layer has exactly one inbound node, i.e. if it is connected
        to one incoming layer).
        '''
        if len(self.inbound_nodes) != 1:
            raise Exception('Layer ' + self.name +
                            ' has multiple inbound nodes, ' +
                            'hence the notion of "layer output mask" '
                            'is ill-defined. '
                            'Use `get_output_mask_at(node_index)` instead.')
        return self._get_node_attribute_at_index(0, 'output_masks',
                                                 'output mask')

    @property
    def input_shape(self):
        '''Retrieves the input shape tuple(s) of a layer. Only applicable
        if the layer has one inbound node,
        or if all inbound nodes have the same input shape.
        '''
        if not self.inbound_nodes:
            raise Exception('The layer has never been called ' +
                            'and thus has no defined input shape.')
        all_input_shapes = set([str(node.input_shapes) for node in self.inbound_nodes])
        if len(all_input_shapes) == 1:
            input_shapes = self.inbound_nodes[0].input_shapes
            if len(input_shapes) == 1:
                return input_shapes[0]
            else:
                return input_shapes
        else:
            raise Exception('The layer "' + str(self.name) +
                            ' has multiple inbound nodes, ' +
                            'with different input shapes. Hence ' +
                            'the notion of "input shape" is ' +
                            'ill-defined for the layer. ' +
                            'Use `get_input_shape_at(node_index)` instead.')

    @property
    def output_shape(self):
        '''Retrieves the output shape tuple(s) of a layer. Only applicable
        if the layer has one inbound node,
        or if all inbound nodes have the same output shape.
        '''
        if not self.inbound_nodes:
            raise Exception('The layer has never been called ' +
                            'and thus has no defined output shape.')
        all_output_shapes = set([str(node.output_shapes) for node in self.inbound_nodes])
        if len(all_output_shapes) == 1:
            output_shapes = self.inbound_nodes[0].output_shapes
            if len(output_shapes) == 1:
                return output_shapes[0]
            else:
                return output_shapes
        else:
            raise Exception('The layer "' + str(self.name) +
                            ' has multiple inbound nodes, ' +
                            'with different output shapes. Hence ' +
                            'the notion of "output shape" is ' +
                            'ill-defined for the layer. ' +
                            'Use `get_output_shape_at(node_index)` instead.')

    def set_weights(self, weights):
        '''Sets the weights of the layer, from Numpy arrays.

        # Arguments
            weights: a list of Numpy arrays. The number
                of arrays and their shape must match
                number of the dimensions of the weights
                of the layer (i.e. it should match the
                output of `get_weights`).
        '''
        params = self.trainable_weights + self.non_trainable_weights
        if len(params) != len(weights):
            raise Exception('You called `set_weights(weights)` on layer "' + self.name +
                            '" with a  weight list of length ' + str(len(weights)) +
                            ', but the layer was expecting ' + str(len(params)) +
                            ' weights. Provided weights: ' + str(weights))
        if not params:
            return
        weight_value_tuples = []
        param_values = K.batch_get_value(params)
        for pv, p, w in zip(param_values, params, weights):
            if pv.shape != w.shape:
                raise Exception('Layer weight shape ' +
                                str(pv.shape) +
                                ' not compatible with '
                                'provided weight shape ' + str(w.shape))
            weight_value_tuples.append((p, w))
        K.batch_set_value(weight_value_tuples)

    def get_weights(self):
        '''Returns the current weights of the layer,
        as a list of numpy arrays.
        '''
        params = self.trainable_weights + self.non_trainable_weights
        return K.batch_get_value(params)

    def get_config(self):
        '''Returns a Python dictionary (serializable)
        containing the configuration of a layer.
        The same layer can be reinstantiated later
        (without its trained weights) from this configuration.

        The config of a layer does not include connectivity
        information, nor the layer class name. These are handled
        by Container (one layer of abstraction above).
        '''
        config = {'name': self.name,
                  'trainable': self.trainable}
        if hasattr(self, 'batch_input_shape'):
            config['batch_input_shape'] = self.batch_input_shape
        if hasattr(self, 'input_dtype'):
            config['input_dtype'] = self.input_dtype
        return config

    @classmethod
    def from_config(cls, config):
        '''This method is the reverse of get_config,
        capable of instantiating the same layer from the config
        dictionary. It does not handle layer connectivity
        (handled by Container), nor weights (handled by `set_weights`).

        # Arguments
            config: a Python dictionary, typically the
                output of get_config.
        '''
        return cls(**config)

    def count_params(self):
        '''Returns the total number of floats (or ints)
        composing the weights of the layer.
        '''
        if not self.built:
            if self.__class__.__name__ in {'Sequential', 'Graph'}:
                self.build()
            else:
                raise Exception('You tried to call `count_params` on ' +
                                self.name + ', but the layer isn\'t built. '
                                'You can build it manually via: `' +
                                self.name + '.build(batch_input_shape)`.')
        return sum([K.count_params(p) for p in self.trainable_weights])


class InputLayer(Layer):
    '''TODO: dosctring
    '''
    def __init__(self, input_shape=None, batch_input_shape=None,
                 input_dtype=None, name=None):
        self.input_spec = None
        self.supports_masking = False
        self.uses_learning_phase = False
        self.trainable = False
        self.built = True

        self.inbound_nodes = []
        self.outbound_nodes = []

        self.trainable_weights = []
        self.non_trainable_weights = []
        self.regularizers = []
        self.constraints = {}

        if not name:
            prefix = 'input'
            name = prefix + '_' + str(K.get_uid(prefix))
        self.name = name

        if not batch_input_shape:
            assert input_shape, 'An Input layer should be passed either a `batch_input_shape` or an `input_shape`.'
            batch_input_shape = (None,) + tuple(input_shape)
        else:
            batch_input_shape = tuple(batch_input_shape)
        if not input_dtype:
            input_dtype = K.floatx()

        self.batch_input_shape = batch_input_shape
        self.input_dtype = input_dtype

        input_tensor = K.placeholder(shape=batch_input_shape,
                                     dtype=input_dtype,
                                     name=self.name)
        # create an input node to add to self.outbound_node
        # and set output_tensors' _keras_history
        input_tensor._uses_learning_phase = False
        input_tensor._keras_history = (self, 0, 0)
        shape = input_tensor._keras_shape
        Node(self,
             inbound_layers=[],
             node_indices=[],
             tensor_indices=[],
             input_tensors=[input_tensor],
             output_tensors=[input_tensor],
             input_masks=[None],
             output_masks=[None],
             input_shapes=[shape],
             output_shapes=[shape])

    def get_config(self):
        config = {'batch_input_shape': self.batch_input_shape,
                  'input_dtype': self.input_dtype,
                  'name': self.name}
        return config


def Input(shape=None, batch_shape=None,
          name=None, dtype=K.floatx()):
    '''`Input()` is used to instantiate a Keras tensor.
    A Keras tensor is a tensor object from the underlying backend
    (Theano or TensorFlow), which we augment with certain
    attributes that allow us to build a Keras model
    just by knowing the inputs and outputs of the model.

    For instance, if a, b and c and Keras tensors,
    it becomes possible to do:
    `model = Model(input=[a, b], output=c)`

    The added Keras attributes are:
        ._keras_shape: integer shape tuple propagated
            via Keras-side shape inference.
        ._keras_history: last layer applied to the tensor.
            the entire layer graph is retrievable from that layer,
            recursively.

    # Arguments
        shape: a shape tuple (integer), not including the batch size.
            For instance, `shape=(32,)` indicates that the expected input
            will be batches of 32-dimensional vectors.
        batch_shape: a shape tuple (integer), including the batch size.
            For instance, `batch_shape=(10, 32)` indicates that
            the expected input will be batches of 10 32-dimensional vectors.
            `batch_shape=(None, 32)` indicates batches of an arbitrary number
            of 32-dimensional vectors.
        name: An optional name string for the layer.
            Should be unique in a model (do not reuse the same name twice).
            It will be autogenerated if it isn't provided.
        dtype: The data type expected by the input, as a string
            (`float32`, `flaot64`, `int32`...)

    # Example usage

        ```python
        # this is a logistic regression in Keras
        a = Input(shape=(32,))
        b = Dense(16, activation='softmax')(a)
        model = Model(input=a, output=b)
        ```
    '''
    if not batch_shape:
        assert shape, ('Please provide to Input either an `input_shape`' +
                       ' or `batch_input_shape` argument. Note that ' +
                       '`input_shape` does not include the batch '
                       'dimension.')
        batch_shape = (None,) + tuple(shape)
    input_layer = InputLayer(batch_input_shape=batch_shape,
                             name=name, input_dtype=dtype)
    # return tensor including _keras_shape and _keras_history
    # note that in this case train_output and test_output are the same pointer.
    outputs = input_layer.inbound_nodes[0].output_tensors
    if len(outputs) == 1:
        return outputs[0]
    else:
        return outputs


class Merge(Layer):
    '''A `Merge` layer can be used to merge a list of tensors
    into a single tensor, following some merge `mode`.

    # Example usage

    ```python
    model1 = Sequential()
    model1.add(Dense(32))

    model2 = Sequential()
    model2.add(Dense(32))

    merged_model = Sequential()
    merged_model.add(Merge([model1, model2], mode='concat', concat_axis=1)
    # TODO: would this actually work? it needs to.
    # achieve this with get_source_inputs in Sequential.
    ```

    # Arguments
        layers: can be a list of Keras tensors or
            a list of layer instances. Must be more
            than one layer/tensor.
        mode: string or lambda/function. If string, must be one
            of: 'sum', 'mul', 'concat', 'ave', 'cos', 'dot'.
            If lambda/function, it should take as input a list of tensors
            and return a single tensor.
        concat_axis: integer, axis to use in mode `concat`.
        dot_axes: integer or tuple of integers, axes to use in mode `dot`.
        output_shape: shape tuple (tuple of integers), or lambda/function
            to compute output_shape (only if merge mode is a lambda/function).
            If the latter case, it should take as input a list of shape tuples
            (1:1 mapping to input tensors) and return a single shape tuple.
        node_indices: optional list of integers containing
            the output node index for each input layer
            (in case some input layers have multiple output nodes).
            will default to an array of 0s if not provided.
        tensor_indices: optional list of indices of output tensors
            to consider for merging
            (in case some input layer node returns multiple tensors).
    '''
    def __init__(self, layers=None, mode='sum', concat_axis=-1,
                 dot_axes=-1, output_shape=None,
                 node_indices=None, tensor_indices=None, name=None):
        self.layers = layers
        self.mode = mode
        self.concat_axis = concat_axis
        self.dot_axes = dot_axes
        if type(self.dot_axes) == int:
            self.dot_axes = [self.dot_axes, ] * 2
        self._output_shape = output_shape
        self.node_indices = node_indices

        # layer parameters
        self.inbound_nodes = []
        self.outbound_nodes = []
        self.constraints = {}
        self.regularizers = []
        self.trainable_weights = []
        self.non_trainable_weights = []
        self.supports_masking = False
        self.uses_learning_phase = False
        self.input_spec = None  # compatible with whatever
        if not name:
            prefix = self.__class__.__name__.lower()
            name = prefix + '_' + str(K.get_uid(prefix))
        self.name = name

        if layers:
            # this exists for backwards compatibility.
            # equivalent to:
            # merge = Merge(layers=None)
            # output = merge([input_tensor_1, input_tensor_2])
            if not node_indices:
                # by default we connect to
                # the 1st output stream in the input layer
                node_indices = [0 for _ in range(len(layers))]
            self._arguments_validation(layers, mode,
                                       concat_axis, dot_axes,
                                       output_shape,
                                       node_indices, tensor_indices)
            self.built = True
            self.add_inbound_node(layers, node_indices, tensor_indices)
        else:
            self.built = False

    def _arguments_validation(self, layers, mode, concat_axis, dot_axes,
                              output_shape, node_indices, tensor_indices):
        '''Validates user-passed arguments and raises exceptions
        as appropriate.
        '''
        if not hasattr(mode, '__call__'):
            if mode not in {'sum', 'mul', 'concat', 'ave', 'cos', 'dot'}:
                raise Exception('Invalid merge mode: ' + str(mode))
        if type(layers) not in {list, tuple} or len(layers) < 2:
            raise Exception('A Merge should only be applied to a list of '
                            'layers with at least 2 elements. Found: ' + str(layers))

        if tensor_indices is None:
            tensor_indices = [None for _ in range(len(layers))]

        input_shapes = []
        for i, layer in enumerate(layers):
            layer_output_shape = layer.get_output_shape_at(node_indices[i])
            if type(layer_output_shape) is list:
                # case: the layer has multiple output tensors
                # and we only need a specific one
                layer_output_shape = layer_output_shape[tensor_indices[i]]
            input_shapes.append(layer_output_shape)

        if mode in {'sum', 'mul', 'ave', 'cos'}:
            input_shapes_set = set(input_shapes)
            if len(input_shapes_set) > 1:
                raise Exception('Only layers of same output shape can '
                                'be merged using ' + mode + ' mode. ' +
                                'Layer shapes: %s' % input_shapes)
        if mode in {'cos', 'dot'}:
            if len(layers) > 2:
                raise Exception(mode + ' merge takes exactly 2 layers')
            shape1 = input_shapes[0]
            shape2 = input_shapes[1]
            n1 = len(shape1)
            n2 = len(shape2)
            if mode == 'dot':
                if type(dot_axes) == int:
                    if dot_axes < 0:
                        dot_axes = [dot_axes % n1, dot_axes % n2]
                    else:
                        dot_axes = [n1 - dot_axes, n2-dot_axes]
                if type(dot_axes) not in [list, tuple]:
                    raise Exception('Invalid type for dot_axes - should be a list.')
                if len(dot_axes) != 2:
                    raise Exception('Invalid format for dot_axes - should contain two elements.')
                if type(dot_axes[0]) is not int or type(dot_axes[1]) is not int:
                    raise Exception('Invalid format for dot_axes - list elements should be "int".')
                if shape1[dot_axes[0]] != shape2[dot_axes[1]]:
                    raise Exception('Dimension incompatibility using dot mode: ' +
                                    '%s != %s. ' % (shape1[dot_axes[0]], shape2[dot_axes[1]]) +
                                    'Layer shapes: %s, %s' % (shape1, shape2))
        elif mode == 'concat':
            reduced_inputs_shapes = [list(shape) for shape in input_shapes]
            shape_set = set()
            for i in range(len(reduced_inputs_shapes)):
                del reduced_inputs_shapes[i][self.concat_axis]
                shape_set.add(tuple(reduced_inputs_shapes[i]))
            if len(shape_set) > 1:
                raise Exception('"concat" mode can only merge layers with matching ' +
                                'output shapes except for the concat axis. ' +
                                'Layer shapes: %s' % (input_shapes))

    def call(self, inputs, mask=None):
        if type(inputs) is not list or len(inputs) <= 1:
            raise Exception('Merge must be called on a list of tensors '
                            '(at least 2). Got: ' + str(inputs))
        # case: "mode" is a lambda or function.
        if hasattr(self.mode, '__call__'):
            # TODO: consider making it possible to
            # pass custom arguments to lambda.
            arguments = {}
            return self.mode(inputs, **arguments)

        if self.mode == 'sum' or self.mode == 'ave':
            s = inputs[0]
            for i in range(1, len(inputs)):
                s += inputs[i]
            if self.mode == 'ave':
                s /= len(inputs)
            return s

        elif self.mode == 'concat':
            return K.concatenate(inputs, axis=self.concat_axis)

        elif self.mode == 'mul':
            s = inputs[0]
            for i in range(1, len(inputs)):
                s *= inputs[i]
            return s

        elif self.mode == 'dot':
            l1 = inputs[0]
            l2 = inputs[1]
            output = K.batch_dot(l1, l2, self.dot_axes)
            return output

        elif self.mode == 'cos':
            l1 = inputs[0]
            l2 = inputs[1]
            denominator = K.sqrt(K.batch_dot(l1, l1, self.dot_axes) *
                                 K.batch_dot(l2, l2, self.dot_axes))
            output = K.batch_dot(l1, l2, self.dot_axes) / denominator
            output = K.expand_dims(output, 1)
            return output
        else:
            raise Exception('Unknown merge mode.')

    def __call__(self, inputs, mask=None):
        '''We disable successive calls to __call__ for Merge layers.
        Although there is no technical obstacle to
        making it possible to __call__ a Merge intance many times
        (it is just a layer), it would make for a rather unelegant API.
        '''
        if type(inputs) is not list:
            raise Exception('Merge can only be called on a list of tensors, '
                            'not a single tensor. Received: ' + str(inputs))
        if self.built:
            raise Exception('A Merge layer cannot be used more than once, '
                            'please use ' +
                            'the "merge" function instead: ' +
                            '`merged_tensor = merge([tensor_1, tensor2])`.')

        all_keras_tensors = True
        for x in inputs:
            if not hasattr(x, '_keras_history'):
                all_keras_tensors = False
                break

        if all_keras_tensors:
            layers = []
            node_indices = []
            tensor_indices = []
            for x in inputs:
                layer, node_index, tensor_index = x._keras_history
                layers.append(layer)
                node_indices.append(node_index)
                tensor_indices.append(tensor_index)
            self._arguments_validation(layers, self.mode,
                                       self.concat_axis, self.dot_axes,
                                       self._output_shape,
                                       node_indices, tensor_indices)
            self.built = True
            self.add_inbound_node(layers, node_indices, tensor_indices)

            outputs = self.inbound_nodes[-1].output_tensors
            return outputs[0] # merge only returns a single tensor
        else:
            return self.call(inputs, mask)

    def get_output_shape_for(self, input_shape):
        assert type(input_shape) is list  # must have mutiple input shape tuples
        # case: callable self._output_shape
        if hasattr(self.mode, '__call__'):
            if hasattr(self._output_shape, '__call__'):
                output_shape = self._output_shape(input_shape)
                return output_shape
            elif self._output_shape is not None:
                return self._output_shape
            else:
                # TODO: consider shape auto-inference with TF
                raise Exception('The Merge layer ' + self.name +
                                ' has a callable `mode` argument, ' +
                                'and we cannot infer its output shape because ' +
                                'no `output_shape` argument was provided.' +
                                'Make sure to pass a shape tuple (or a callable) ' +
                                '`output_shape` to Merge.')
        # pre-defined merge modes
        input_shapes = input_shape
        if self.mode in ['sum', 'mul', 'ave']:
            # all tuples in input_shapes should be the same
            return input_shapes[0]
        elif self.mode == 'concat':
            output_shape = list(input_shapes[0])
            for shape in input_shapes[1:]:
                if output_shape[self.concat_axis] is None or shape[self.concat_axis] is None:
                    output_shape[self.concat_axis] = None
                    break
                output_shape[self.concat_axis] += shape[self.concat_axis]
            return tuple(output_shape)
        elif self.mode == 'join':
            return None
        elif self.mode == 'dot':
            shape1 = list(input_shapes[0])
            shape2 = list(input_shapes[1])
            dot_axes = [a-1 for a in self.dot_axes]
            tensordot_output = np.tensordot(np.zeros(tuple(shape1[1:])),
                                            np.zeros(tuple(shape2[1:])),
                                            axes=dot_axes)
            if len(tensordot_output.shape) == 0:
                shape = (1,)
            else:
                shape = tensordot_output.shape
            return (shape1[0],) + shape
        elif self.mode == 'cos':
            return (input_shapes[0][0], 1)

    def compute_mask(self, input, mask=None):
        '''TODO: add mask merging support
        '''
        if mask is not None and any(mask):
            raise Exception('Merge does not support masking, ' +
                            'but was passed an input mask: ' + str(mask))
        return None

    def get_config(self):
        py3 = sys.version_info[0] == 3

        if isinstance(self.mode, python_types.LambdaType):
            if py3:
                mode = marshal.dumps(self.mode.__code__)
            else:
                mode = marshal.dumps(self.mode.func_code)
            mode_type = 'lambda'
        elif callable(self.mode):
            mode = self.mode.__name__
            mode_type = 'function'
        else:
            mode = self.mode
            mode_type = 'raw'

        if isinstance(self._output_shape, python_types.LambdaType):
            if py3:
                output_shape = marshal.dumps(self._output_shape.__code__)
            else:
                output_shape = marshal.dumps(self._output_shape.func_code)
            output_shape_type = 'lambda'
        elif callable(self._output_shape):
            output_shape = self._output_shape.__name__
            output_shape_type = 'function'
        else:
            output_shape = self._output_shape
            output_shape_type = 'raw'

        return {'name': self.name,
                'mode': mode,
                'mode_type': mode_type,
                'concat_axis': self.concat_axis,
                'dot_axes': self.dot_axes,
                'output_shape': output_shape,
                'output_shape_type': output_shape_type}

    @classmethod
    def from_config(cls, config):
        mode_type = config.pop('mode_type')
        if mode_type == 'function':
            mode = globals()[config['mode']]
        elif mode_type == 'lambda':
            mode = marshal.loads(config['mode'])
            mode = python_types.FunctionType(mode, globals())
        else:
            mode = config['mode']

        output_shape_type = config.pop('output_shape_type')
        if output_shape_type == 'function':
            output_shape = globals()[config['output_shape']]
        elif output_shape_type == 'lambda':
            output_shape = marshal.loads(config['output_shape'])
            output_shape = python_types.FunctionType(output_shape, globals())
        else:
            output_shape = config['output_shape']

        config['mode'] = mode
        config['output_shape'] = output_shape
        return super(Merge, cls).from_config(config)


def merge(inputs, mode='sum', concat_axis=-1,
          dot_axes=-1, output_shape=None, name=None):
    '''Functional merge, to apply to Keras tensors (NOT layers).
    Returns a Keras tensor.

    # Example usage:

    ```python
    tensor_a = Input(shape=(32,))
    tensor_b = Input(shape=(32,))
    merged_tensor = merge([tensor_a, tensor_b], mode='concat', concat_axis=1)
    ```

    # Arguments
        mode: string or lambda/function. If string, must be one
            of: 'sum', 'mul', 'concat', 'ave', 'join', 'cos', 'dot'.
            If lambda/function, it should take as input a list of tensors
            and return a single tensor.
        concat_axis: integer, axis to use in mode `concat`.
        dot_axes: integer or tuple of integers, axes to use in mode `dot`.
        output_shape: shape tuple (tuple of integers), or lambda/function
            to compute output_shape (only if merge mode is a lambda/function).
            If the latter case, it should take as input a list of shape tuples
            (1:1 mapping to input tensors) and return a single shape tuple.
        node_indices: optional list of integers containing
            the output node index for each input layer
            (in case some input layers have multiple output nodes).
            will default to an array of 0s if not provided.
        tensor_indices: optional list of indices of output tensors
            to consider for merging
            (in case some input layer node returns multiple tensors).
    '''
    all_keras_tensors = True
    for x in inputs:
        if not hasattr(x, '_keras_history'):
            all_keras_tensors = False
            break
    if all_keras_tensors:
        input_layers = []
        node_indices = []
        tensor_indices = []
        for x in inputs:
            input_layer, node_index, tensor_index = x._keras_history
            input_layers.append(input_layer)
            node_indices.append(node_index)
            tensor_indices.append(tensor_index)
        merge_layer = Merge(input_layers, mode=mode,
                            concat_axis=concat_axis,
                            dot_axes=dot_axes,
                            output_shape=output_shape,
                            node_indices=node_indices,
                            tensor_indices=tensor_indices,
                            name=name)
        return merge_layer.inbound_nodes[0].output_tensors[0]
    else:
        merge_layer = Merge(mode=mode,
                            concat_axis=concat_axis,
                            dot_axes=dot_axes,
                            output_shape=output_shape,
                            name=name)
        return merge_layer(inputs)


class Container(Layer):
    '''TODO: dosctring

    # Properties
        name
        inputs
        outputs
        input_layers
        output_layers

        input_spec (list of class instances)
            each entry describes one required input:
                - ndim
                - dtype
        trainable (boolean)
        input_shape
        output_shape
        inbound_nodes: list of nodes
        outbound_nodes: list of nodes

        (supports_masking (boolean))

        trainable_weights (list of variables)
        non_trainable_weights (list of variables)
        regularizers (list of regularizers)
        constraints (list of tuples (weight, constraint))

    # Methods
        summary
        get_layer
        get_weights
        set_weights
        get_config
        get_output_shape_for

    # Class Methods
        from_config
    '''
    def __init__(self, input, output, name=None):
        # handle name argument
        if not name:
            prefix = self.__class__.__name__.lower()
            name = prefix + '_' + str(K.get_uid(prefix))
        self.name = name

        # Container-specific properties
        if type(input) in {list, tuple}:
            self.inputs = list(input)  # tensor or list of tensors
        else:
            self.inputs = [input]
        if type(output) in {list, tuple}:
            self.outputs = list(output)
        else:
            self.outputs = [output]

        # check for redundancy in inputs:
        inputs_set = set(self.inputs)
        if len(inputs_set) != len(self.inputs):
            raise Exception('The list of inputs passed to the model '
                            'is redundant. All inputs should only appear once.'
                            ' Found: ' + str(self.inputs))

        # list of initial layers (1 to 1 mapping with self.inputs,
        # hence the same layer might appear twice)
        self.input_layers = []
        # TODO: probably useless because input layers must be Input layers (node_indices = [0], tensor_indices = [0])
        self.input_layers_node_indices = []
        self.input_layers_tensor_indices = []
        # list of layers (1 to 1 mapping with self.inputs,
        # hence the same layer might appear twice)
        self.output_layers = []
        # TODO: probably useless
        self.output_layers_node_indices = []
        self.output_layers_tensor_indices = []
        # all layers in order of horizontal graph traversal.
        # Entries are unique. Includes input and output layers.
        self.layers = []

        # this is for performance optimization
        # when calling the Container on new inputs.
        # every time the Container is called on a set on input tensors,
        # we compute the output tensors,
        # output masks and output shapes in one pass,
        # then cache them here. When of of these output is queried later,
        # we retrieve it from there instead of recomputing it.
        self._output_mask_cache = {}
        self._output_tensor_cache = {}
        self._output_shape_cache = {}

        # arguments validation
        for x in self.inputs:
            # check that x is a Keras tensor
            if not hasattr(x, '_keras_history'):
                cls_name = self.__class__.__name__
                raise Exception('Input tensors to a ' + cls_name + ' ' +
                                'must be Keras tensors. Found: ' + str(x) +
                                ' (missing Keras metadata).')
            # check that x is an input tensor
            layer, node_index, tensor_index = x._keras_history
            if len(layer.inbound_nodes) > 1 or (layer.inbound_nodes and layer.inbound_nodes[0].inbound_layers):
                cls_name = self.__class__.__name__
                warnings.warn(cls_name + ' inputs must come from '
                              'a Keras Input layer, '
                              'they cannot be the output of '
                              'a previous non-Input layer. '
                              'Here, a tensor specified as '
                              'input to "' + self.name +
                              '" was not an Input tensor, '
                              'it was generated by layer ' +
                              layer.name + '.\n'
                              'Note that input tensors are '
                              'instantiated via `tensor = Input(shape)`.\n'
                              'The tensor that caused the issue was: ' +
                              str(x.name))
        for x in self.outputs:
            if not hasattr(x, '_keras_history'):
                cls_name = self.__class__.__name__
                raise Exception('Output tensors to a ' + cls_name + ' must be '
                                'Keras tensors. Found: ' + str(x))
        # build self.output_layers:
        for x in self.outputs:
            layer, node_index, tensor_index = x._keras_history
            self.output_layers.append(layer)
            self.output_layers_node_indices.append(node_index)
            self.output_layers_tensor_indices.append(tensor_index)
        # build self.output_layers:
        for x in self.inputs:
            layer, node_index, tensor_index = x._keras_history
            # it's supposed to be an input layer, so only one node
            # and one tensor output
            assert node_index == 0
            assert tensor_index == 0
            self.input_layers.append(layer)
            self.input_layers_node_indices.append(node_index)
            self.input_layers_tensor_indices.append(tensor_index)

        # build self.input_names and self.output_names
        self.input_names = []
        self.output_names = []
        for layer in self.input_layers:
            self.input_names.append(layer.name)
        for layer in self.output_layers:
            self.output_names.append(layer.name)

        self.internal_input_shapes = [x._keras_shape for x in self.inputs]
        self.internal_output_shapes = [x._keras_shape for x in self.outputs]

        # container_nodes: set of nodes included in the graph
        # (not all nodes included in the layers are relevant to the current graph).
        container_nodes = set()  # ids of all nodes relevant to the Container
        nodes_depths = {}  # map {node: depth value}
        layers_depths = {}  # map {layer: depth value}

        def make_node_key(node, depth):
            return str(id(node)) + '-' + str(depth)

        def build_map_of_graph(tensor, seen_nodes=set(), depth=0,
                               layer=None, node_index=None, tensor_index=None):
            '''This recursively updates the maps nodes_depths,
            layers_depths and the set container_nodes.
            Does not try to detect cycles in graph (TODO?)

            # Arguments
                tensor: some tensor in a graph
                seen_nodes: set of node ids ("{layer.name}_ib-{node_index}")
                    of nodes seen so far. Useful to prevent infinite loops.
                depth: current depth in the graph (0 = last output).
                layer: layer from which `tensor` comes from. If not provided,
                    will be obtained from `tensor._keras_history`.
                node_index: node index from which `tensor` comes from.
                tensor_index: tensor_index from which `tensor` comes from.
            '''
            if not layer or node_index is None or tensor_index is None:
                layer, node_index, tensor_index = tensor._keras_history
            node = layer.inbound_nodes[node_index]

            # prevent cycles
            seen_nodes.add(make_node_key(node, depth))

            node_key = layer.name + '_ib-' + str(node_index)
            # update container_nodes
            container_nodes.add(node_key)
            # update nodes_depths
            node_depth = nodes_depths.get(node)
            if node_depth is None:
                nodes_depths[node] = depth
            else:
                nodes_depths[node] = max(depth, node_depth)
            # update layers_depths
            layer_depth = layers_depths.get(layer)
            if layer_depth is None:
                layers_depths[layer] = depth
            else:
                layers_depths[layer] = max(depth, layer_depth)

            # propagate to all previous tensors connected to this node
            for i in range(len(node.inbound_layers)):
                x = node.input_tensors[i]
                layer = node.inbound_layers[i]
                node_index = node.node_indices[i]
                tensor_index = node.tensor_indices[i]
                next_node = layer.inbound_nodes[node_index]
                node_key = make_node_key(next_node, depth + 1)
                if node_key not in seen_nodes:
                    build_map_of_graph(x, seen_nodes, depth + 1,
                                       layer, node_index, tensor_index)

        for x in self.outputs:
            seen_nodes = set()
            build_map_of_graph(x, seen_nodes, depth=0)

        # build a map {depth: list of nodes with this depth}
        nodes_by_depth = {}
        for node, depth in nodes_depths.items():
            if depth not in nodes_by_depth:
                nodes_by_depth[depth] = []
            nodes_by_depth[depth].append(node)

        # build a map {depth: list of layers with this depth}
        layers_by_depth = {}
        for layer, depth in layers_depths.items():
            if depth not in layers_by_depth:
                layers_by_depth[depth] = []
            layers_by_depth[depth].append(layer)

        # get sorted list of layer depths
        depth_keys = list(layers_by_depth.keys())
        depth_keys.sort(reverse=True)

        # set self.layers and self.layers_by_depth
        layers = []
        for depth in depth_keys:
            layers_for_depth = layers_by_depth[depth]
            # container.layers needs to have a deterministic order
            layers_for_depth.sort(key=lambda x: x.name)
            for layer in layers_for_depth:
                layers.append(layer)
        self.layers = layers
        self.layers_by_depth = layers_by_depth

        # get sorted list of node depths
        depth_keys = list(nodes_by_depth.keys())
        depth_keys.sort(reverse=True)

        # check that all tensors required are computable.
        # computable_tensors: all tensors in the graph
        # that can be computed from the inputs provided
        computable_tensors = []
        for x in self.inputs:
            computable_tensors.append(x)

        layers_with_complete_input = []  # to provide a better error msg
        for depth in depth_keys:
            for node in nodes_by_depth[depth]:
                layer = node.outbound_layer
                if layer:
                    for x in node.input_tensors:
                        if x not in computable_tensors:
                            raise Exception(
                                'Graph disconnected: '
                                'cannot obtain value for tensor ' +
                                str(x) + ' at layer "' + layer.name + '". '
                                'The following previous layers '
                                'were accessed without issue: ' +
                                str(layers_with_complete_input))
                    for x in node.output_tensors:
                        computable_tensors.append(x)
                    layers_with_complete_input.append(layer.name)

        # set self.nodes and self.nodes_by_depth
        self.container_nodes = container_nodes
        self.nodes_by_depth = nodes_by_depth

        # ensure name unicity, which will be crucial for serialization
        # (since serialized nodes refer to layers by their name).
        all_names = [layer.name for layer in self.layers]
        for name in all_names:
            if all_names.count(name) != 1:
                raise Exception('The name "' + name + '" is used ' +
                                str(all_names.count(name)) +
                                ' times in the model. ' +
                                'All layer names should be unique.')

        # layer parameters
        # the new container starts with a single inbound node
        # for its inputs, and no outbound nodes.
        self.outbound_nodes = []  # will be appended to by future calls to __call__
        self.inbound_nodes = []  # will be appended to below, and by future calls to __call__
        # create the node linking internal inputs to internal outputs
        Node(outbound_layer=self,
             inbound_layers=[],
             node_indices=[],
             tensor_indices=[],
             input_tensors=self.inputs,
             output_tensors=self.outputs,
             # no container-level masking for now
             input_masks=[None for _ in self.inputs],
             output_masks=[None for _ in self.outputs],
             input_shapes=[x._keras_shape for x in self.inputs],
             output_shapes=[x._keras_shape for x in self.outputs])
        self.built = True
        self.supports_masking = False
        # the following are implemented as property functions:
        # self.constraints
        # self.regularizers
        # self.trainable_weights
        # self.non_trainable_weights
        # self.input_spec

    def get_layer(self, name=None, index=None):
        '''Returns a layer based on either its name (unique)
        or its index in the graph. Indices are based on
        order of horizontal graph traversal (bottom-up).

        # Arguments
            name: string, name of layer.
            index: integer, index of layer.

        # Returns
            A layer instance.
        '''
        # it would be unreliable to build a dictionary
        # based on layer names, because names can potentially
        # be changed at any point by the user
        # without the container being notified of it
        if index:
            if len(self.layers) <= index:
                raise Exception('Was asked to retrieve layer at index ' +
                                str(index) + ' but model only has ' +
                                str(len(self.layers)) + ' layers.')
        else:
            assert name, 'Provide either a layer name or layer index.'
        layer = None
        for layer in self.layers:
            if layer.name == name:
                return layer
        if not layer:
            raise Exception('No such layer: ' + name)

    @property
    def updates(self):
        updates = []
        for layer in self.layers:
            if hasattr(layer, 'updates'):
                updates += layer.updates
        return updates

    @property
    def stateful(self):
        return any([(hasattr(layer, 'stateful') and layer.stateful) for layer in self.layers])

    def reset_states(self):
        for layer in self.layers:
            if hasattr(layer, 'reset_states') and getattr(layer, 'stateful', False):
                layer.reset_states()

    @property
    def state_updates(self):
        '''Returns the `updates` from all layers that are
        stateful.  This is useful for separating training updates and
        state updates, e.g. when we need to update a layer's internal state
        during prediction.
        '''
        state_updates = []
        for layer in self.layers:
            if getattr(layer, 'stateful', False):
                if hasattr(layer, 'updates'):
                    state_updates += layer.updates
        return state_updates

    @property
    def constraints(self):
        cons = {}
        for layer in self.layers:
            for key, value in layer.constraints.items():
                if key in cons:
                    raise Exception('Received multiple constraints '
                                    'for one weight tensor: ' + str(key))
                cons[key] = value
        return cons

    @property
    def regularizers(self):
        regs = []
        for layer in self.layers:
            regs += layer.regularizers
        return regs

    @property
    def trainable_weights(self):
        weights = []
        for layer in self.layers:
            weights += layer.trainable_weights
        return weights

    @property
    def non_trainable_weights(self):
        weights = []
        for layer in self.layers:
            weights += layer.non_trainable_weights
        return weights

    @property
    def input_spec(self):
        specs = []
        for layer in getattr(self, 'input_layers', []):
            if layer.input_spec is None:
                specs.append(None)
            else:
                if type(layer.input_spec) is not list:
                    raise Exception('Layer ' + layer.name +
                                    ' has an input_spec attribute that '
                                    'is not a list. We expect a list. '
                                    'Found input_spec = ' +
                                    str(layer.input_spec))
                specs += layer.input_spec
        return specs

    @property
    def uses_learning_phase(self):
        '''True if any layer in the graph uses it.
        '''
        layers_learning_phase = any([layer.uses_learning_phase for layer in self.layers])
        regs_learning_phase = any([reg.uses_learning_phase for reg in self.regularizers])
        return layers_learning_phase or regs_learning_phase

    def call(self, input, mask=None):
        '''`call` just reapplies all ops in the graph to the new inputs
        (e.g. build a new computational graph from the provided inputs).

        It is callable on non-Keras tensors.

        # Arguments
            input: a tensor or list of tensors.
            mask: a mask or list of masks. A mask can be
                either a tensor or None (no mask).

        # Returns
            A tensor if there is a single output, or
            a list of tensors if there are more than one outputs.
        '''
        inputs = to_list(input)
        if mask is None:
            masks = [None for _ in range(len(inputs))]
        else:
            masks = to_list(mask)
        cache_key = ','.join([str(id(x)) for x in inputs])
        cache_key += '_' + ','.join([str(id(x)) for x in masks])
        if cache_key in self._output_tensor_cache:
            return self._output_tensor_cache[cache_key]
        else:
            output_tensors, output_masks, output_shapes = self.run_internal_graph(inputs, masks)
            return output_tensors

    def compute_mask(self, input, mask):
        inputs = to_list(input)
        if mask is None:
            masks = [None for _ in range(len(inputs))]
        else:
            masks = to_list(mask)
        cache_key = ','.join([str(id(x)) for x in inputs])
        cache_key += '_' + ','.join([str(id(x)) for x in masks])
        if cache_key in self._output_mask_cache:
            return self._output_mask_cache[cache_key]
        else:
            output_tensors, output_masks, output_shapes = self.run_internal_graph(inputs, masks)
            return output_masks

    def get_output_shape_for(self, input_shape):
        input_shapes = to_list(input_shape)
        if len(input_shapes) != len(self.input_layers):
            raise Exception('Invalid input_shape argument ' +
                            str(input_shape) + ': model has ' +
                            str(len(self.input_layers)) + ' tensor inputs.')

        cache_key = ','.join([str(x) for x in input_shapes])
        if cache_key in self._output_shape_cache:
            output_shapes = self._output_shape_cache[cache_key]
            if type(output_shapes) is list and len(output_shapes) == 1:
                return output_shapes[0]
            return output_shapes
        else:
            # bad luck, have to run the graph manually
            layers_to_output_shapes = {}
            for i in range(len(input_shapes)):
                layer = self.input_layers[i]
                input_shape = input_shapes[i]
                # it's an input layer: get_output_shape_for is identity,
                # and there is only one node and one tensor output.
                shape_key = layer.name + '_0_0'
                layers_to_output_shapes[shape_key] = input_shape

            depth_keys = list(self.nodes_by_depth.keys())
            depth_keys.sort(reverse=True)
            # iterate over nodes, by depth level
            if len(depth_keys) > 1:
                for depth in depth_keys:
                    nodes = self.nodes_by_depth[depth]
                    for node in nodes:
                        # this is always a single layer, never a list
                        layer = node.outbound_layer
                        if layer in self.input_layers:
                            # we've already covered the input layers
                            # a few lines above
                            continue
                        # potentially redundant list,
                        # same size of node.input_tensors
                        input_shapes = []
                        for j in range(len(node.inbound_layers)):
                            inbound_layer = node.inbound_layers[j]
                            node_index = node.node_indices[j]
                            tensor_index = node.tensor_indices[j]
                            shape_key = inbound_layer.name + '_%s_%s' % (node_index, tensor_index)
                            input_shape = layers_to_output_shapes[shape_key]
                            input_shapes.append(input_shape)

                        if len(input_shapes) == 1:
                            output_shape = layer.get_output_shape_for(input_shapes[0])
                        else:
                            output_shape = layer.get_output_shape_for(input_shapes)

                        output_shapes = to_list(output_shape)
                        node_index = layer.inbound_nodes.index(node)
                        for j in range(len(output_shapes)):
                            shape_key = layer.name + '_%s_%s' % (node_index, j)
                            layers_to_output_shapes[shape_key] = output_shapes[j]

            # read final output shapes from layers_to_output_shapes
            output_shapes = []
            output_shape_keys = []
            for i in range(len(self.output_layers)):
                layer = self.output_layers[i]
                node_index = self.output_layers_node_indices[i]
                tensor_index = self.output_layers_tensor_indices[i]
                shape_key = layer.name + '_%s_%s' % (node_index, tensor_index)
                output_shape_keys.append(shape_key)

            for i, key in enumerate(output_shape_keys):
                assert key in layers_to_output_shapes
                output_shapes.append(layers_to_output_shapes[key])
            # store in cache
            self._output_shape_cache[cache_key] = output_shapes
            if type(output_shapes) is list and len(output_shapes) == 1:
                return output_shapes[0]
            return output_shapes

    def run_internal_graph(self, inputs, masks=None):
        '''Computes output tensors for new inputs.

        # Note:
            - expects `inputs` to be a list (potentially with 1 element).
            - can be run on non-Keras tensors.

        # Arguments
            inputs: list of tensors
            masks: list of masks (tensors or None).

        # Returns
            Three lists: output_tensors, output_masks, output_shapes
        '''
        assert type(inputs) is list
        if masks is None:
            masks = [None for _ in range(len(inputs))]
        assert type(masks) is list

        # dictionary mapping reference tensors to tuples (computed tensor, compute mask)
        # we assume a 1:1 mapping from tensor to mask
        # TODO: raise exception when a .compute_mask does not return a list the same size as call
        tensor_map = {}
        for x, y, mask in zip(self.inputs, inputs, masks):
            tensor_map[str(id(x))] = (y, mask)

        depth_keys = list(self.nodes_by_depth.keys())
        depth_keys.sort(reverse=True)
        for depth in depth_keys:
            nodes = self.nodes_by_depth[depth]
            for node in nodes:
                # this is always a single layer, never a list
                layer = node.outbound_layer

                reference_input_tensors = node.input_tensors
                reference_output_tensors = node.output_tensors

                # if all previous input tensors are available in tensor_map,
                # then call node.inbound_layer on them
                computed_data = []  # list of tuples (input, mask)
                for x in reference_input_tensors:
                    if str(id(x)) in tensor_map:
                        computed_data.append(tensor_map[str(id(x))])
                if len(computed_data) == len(reference_input_tensors):
                    # call layer
                    if len(computed_data) == 1:
                        computed_tensor, computed_mask = computed_data[0]
                        output_tensors = to_list(layer.call(computed_tensor, computed_mask))
                        output_masks = to_list(layer.compute_mask(computed_tensor, computed_mask))
                        computed_tensors = [computed_tensor]
                        computed_masks = [computed_mask]
                    else:
                        computed_tensors = [x[0] for x in computed_data]
                        computed_masks = [x[1] for x in computed_data]
                        output_tensors = to_list(layer.call(computed_tensors, computed_masks))
                        output_masks = to_list(layer.compute_mask(computed_tensors, computed_masks))

                    # update _keras_shape
                    if all([hasattr(x, '_keras_shape') for x in computed_tensors]):
                        if len(computed_tensors) == 1:
                            shapes = to_list(layer.get_output_shape_for(computed_tensors[0]._keras_shape))
                            uses_learning_phase = computed_tensors[0]._uses_learning_phase or layer.uses_learning_phase
                        else:
                            shapes = to_list(layer.get_output_shape_for([x._keras_shape for x in computed_tensors]))
                            uses_learning_phase = any([x._uses_learning_phase for x in computed_tensors]) or layer.uses_learning_phase
                        for x, s in zip(output_tensors, shapes):
                            x._keras_shape = s
                            x._uses_learning_phase = uses_learning_phase
                    for x, y, mask in zip(reference_output_tensors, output_tensors, output_masks):
                        tensor_map[str(id(x))] = (y, mask)

        output_tensors = []
        output_masks = []
        output_shapes = []
        for x in self.outputs:
            # todo: better error msg
            assert str(id(x)) in tensor_map, 'Could not compute output ' + str(x)
            tensor, mask = tensor_map[str(id(x))]
            if hasattr(tensor, '_keras_shape') and output_shapes is not None:
                shape = tensor._keras_shape
                output_shapes.append(shape)
            else:
                output_shapes = None
            output_tensors.append(tensor)
            output_masks.append(mask)

        # update cache; keys are based on ids on input tensors and inputs masks
        cache_key = ','.join([str(id(x)) for x in inputs])
        cache_key += '_' + ','.join([str(id(x)) for x in masks])

        if len(output_tensors) == 1:
            output_tensors = output_tensors[0]
            self._output_tensor_cache[cache_key] = output_tensors
        else:
            self._output_tensor_cache[cache_key] = output_tensors

        if len(output_masks) == 1:
            output_masks = output_masks[0]
            self._output_mask_cache[cache_key] = output_masks
        else:
            self._output_mask_cache[cache_key] = output_masks

        if output_shapes is not None:
            input_shapes = [x._keras_shape for x in inputs]
            cache_key = ','.join([str(x) for x in input_shapes])
            if len(output_shapes) == 1:
                output_shapes = output_shapes[0]
                self._output_shape_cache[cache_key] = output_shapes
            else:
                self._output_shape_cache[cache_key] = output_shapes
        return output_tensors, output_masks, output_shapes

    def get_config(self):
        '''TODO: add keras version information
        '''
        config = {
            'name': self.name,
        }
        node_conversion_map = {}
        for layer in self.layers:
            if issubclass(layer.__class__, Container):
                # containers start with a pre-existing node
                # linking their input to output
                kept_nodes = 1
            else:
                kept_nodes = 0
            for original_node_index, node in enumerate(layer.inbound_nodes):
                node_key = layer.name + '_ib-' + str(original_node_index)
                if node_key in self.container_nodes:
                    node_conversion_map[node_key] = kept_nodes
                    kept_nodes += 1
        layer_configs = []
        for layer in self.layers:  # from the earliest layers on
            layer_class_name = layer.__class__.__name__
            layer_config = layer.get_config()
            filtered_inbound_nodes = []
            for original_node_index, node in enumerate(layer.inbound_nodes):
                node_key = layer.name + '_ib-' + str(original_node_index)
                if node_key in self.container_nodes:
                    # the node is relevant to the model:
                    # add to filtered_inbound_nodes
                    if node.inbound_layers:
                        node_data = []
                        for i in range(len(node.inbound_layers)):
                            inbound_layer = node.inbound_layers[i]
                            node_index = node.node_indices[i]
                            tensor_index = node.tensor_indices[i]
                            node_key = inbound_layer.name + '_ib-' + str(node_index)
                            # assert node_key in node_conversion_map, 'Node never seen before: %s' % node_key
                            new_node_index = node_conversion_map.get(node_key, 0)
                            node_data.append([inbound_layer.name,
                                              new_node_index,
                                              tensor_index])
                        filtered_inbound_nodes.append(node_data)
            layer_configs.append({
                'name': layer.name,
                'class_name': layer_class_name,
                'config': layer_config,
                'inbound_nodes': filtered_inbound_nodes,
            })
        config['layers'] = layer_configs

        # gather info about inputs and outputs
        model_inputs = []
        for i in range(len(self.input_layers)):
            layer = self.input_layers[i]
            node_index = self.input_layers_node_indices[i]
            node_key = layer.name + '_ib-' + str(node_index)
            new_node_index = node_conversion_map[node_key]
            tensor_index = self.input_layers_tensor_indices[i]
            model_inputs.append([layer.name, new_node_index, tensor_index])
        config['input_layers'] = model_inputs
        model_outputs = []
        for i in range(len(self.output_layers)):
            layer = self.output_layers[i]
            node_index = self.output_layers_node_indices[i]
            node_key = layer.name + '_ib-' + str(node_index)
            new_node_index = node_conversion_map[node_key]
            tensor_index = self.output_layers_tensor_indices[i]
            model_outputs.append([layer.name, new_node_index, tensor_index])
        config['output_layers'] = model_outputs
        return copy.deepcopy(config)

    @classmethod
    def from_config(cls, config, custom_objects={}):
        '''Instantiates a Model from its config (output of `get_config()`).

        TODO: support for custom objects
        '''
        from keras.utils.layer_utils import layer_from_config

        # layer instances created during
        # the graph reconstruction process
        created_layers = {}

        # iterate over saved layers, instantiate them,
        # then call them on appropriate inputs to create graph nodes
        for layer_data in config['layers']:
            layer_name = layer_data['name']

            # instantiate layer
            layer = layer_from_config(layer_data,
                                      custom_objects=custom_objects)
            created_layers[layer_name] = layer

            # gather layer inputs
            inbound_nodes_data = layer_data['inbound_nodes']
            for node_data in inbound_nodes_data:
                input_tensors = []
                for input_data in node_data:
                    inbound_layer_name, inbound_node_index, inbound_tensor_index = input_data
                    assert inbound_layer_name in created_layers, 'Missing layer: %s' % inbound_layer_name
                    inbound_layer = created_layers[inbound_layer_name]
                    inbound_node = inbound_layer.inbound_nodes[inbound_node_index]
                    input_tensors.append(inbound_node.output_tensors[inbound_tensor_index])
                # call layer on its inputs, thus creating the node
                # and building the layer if needed
                if input_tensors:
                    if len(input_tensors) == 1:
                        layer(input_tensors[0])
                    else:
                        layer(input_tensors)
        name = config.get('name')
        input_tensors = []
        output_tensors = []
        for layer_data in config['input_layers']:
            layer_name, node_index, tensor_index = layer_data
            assert layer_name in created_layers
            layer = created_layers[layer_name]
            layer_output_tensors = layer.inbound_nodes[node_index].output_tensors
            input_tensors.append(layer_output_tensors[tensor_index])
        for layer_data in config['output_layers']:
            layer_name, node_index, tensor_index = layer_data
            assert layer_name in created_layers
            layer = created_layers[layer_name]
            layer_output_tensors = layer.inbound_nodes[node_index].output_tensors
            output_tensors.append(layer_output_tensors[tensor_index])
        return cls(input=input_tensors, output=output_tensors, name=name)

    def save_weights(self, filepath, overwrite=False):
        '''Dumps all layer weights to a HDF5 file.

        The weight file has:
            - `layer_names` (attribute), a list of strings
                (ordered names of model layers)
            - for every layer, a `group` named `layer.name`
                - for every such layer group, a group attribute `weight_names`,
                    a list of strings (ordered names of weights tensor of the layer)
                - for every weight in the layer, a dataset
                    storing the weight value, named after the weight tensor
        '''
        import h5py
        import os.path
        # if file exists and should not be overwritten
        if not overwrite and os.path.isfile(filepath):
            import sys
            get_input = input
            if sys.version_info[:2] <= (2, 7):
                get_input = raw_input
            overwrite = get_input('[WARNING] %s already exists - overwrite? '
                                  '[y/n]' % (filepath))
            while overwrite not in ['y', 'n']:
                overwrite = get_input('Enter "y" (overwrite) or "n" (cancel).')
            if overwrite == 'n':
                return
            print('[TIP] Next time specify overwrite=True in save_weights!')

        if hasattr(self, 'flattened_layers'):
            # support for legacy Sequential/Merge behavior
            flattened_layers = self.flattened_layers
        else:
            flattened_layers = self.layers

        f = h5py.File(filepath, 'w')
        f.attrs['layer_names'] = [layer.name.encode('utf8') for layer in flattened_layers]

        for layer in flattened_layers:
            g = f.create_group(layer.name)
            symbolic_weights = layer.trainable_weights + layer.non_trainable_weights
            weight_values = layer.get_weights()
            weight_names = []
            for i, (w, val) in enumerate(zip(symbolic_weights, weight_values)):
                if hasattr(w, 'name') and w.name:
                    name = str(w.name)
                else:
                    name = 'param_' + str(i)
                weight_names.append(name.encode('utf8'))
            g.attrs['weight_names'] = weight_names
            for name, val in zip(weight_names, weight_values):
                param_dset = g.create_dataset(name, val.shape,
                                              dtype=val.dtype)
                param_dset[:] = val
        f.flush()
        f.close()

    def load_weights(self, filepath):
        '''Load all layer weights from a HDF5 save file.
        '''
        import h5py
        f = h5py.File(filepath, mode='r')

        if hasattr(self, 'flattened_layers'):
            # support for legacy Sequential/Merge behavior
            flattened_layers = self.flattened_layers
        else:
            flattened_layers = self.layers

        if 'nb_layers' in f.attrs:
            # legacy format
            nb_layers = f.attrs['nb_layers']
            if nb_layers != len(flattened_layers):
                raise Exception('You are trying to load a weight file '
                                'containing ' + str(nb_layers) +
                                ' layers into a model with ' +
                                str(len(flattened_layers)) + '.')

            for k in range(nb_layers):
                g = f['layer_{}'.format(k)]
                weights = [g['param_{}'.format(p)] for p in range(g.attrs['nb_params'])]
                flattened_layers[k].set_weights(weights)
        else:
            # new file format
            layer_names = [n.decode('utf8') for n in f.attrs['layer_names']]
            if len(layer_names) != len(flattened_layers):
                raise Exception('You are trying to load a weight file '
                                'containing ' + str(len(layer_names)) +
                                ' layers into a model with ' +
                                str(len(flattened_layers)) + ' layers.')

            # we batch weight value assignments in a single backend call
            # which provides a speedup in TensorFlow.
            weight_value_tuples = []
            for k, name in enumerate(layer_names):
                g = f[name]
                weight_names = [n.decode('utf8') for n in g.attrs['weight_names']]
                if len(weight_names):
                    weight_values = [g[weight_name] for weight_name in weight_names]
                    layer = flattened_layers[k]
                    symbolic_weights = layer.trainable_weights + layer.non_trainable_weights
                    if len(weight_values) != len(symbolic_weights):
                        raise Exception('Layer #' + str(k) +
                                        ' (named "' + layer.name +
                                        '" in the current model) was found to '
                                        'correspond to layer ' + name +
                                        ' in the save file. '
                                        'However the new layer ' + layer.name +
                                        ' expects ' + str(len(symbolic_weights)) +
                                        ' weights, but the saved weights have ' +
                                        str(len(weight_values)) +
                                        ' elements.')
                    weight_value_tuples += zip(symbolic_weights, weight_values)
            K.batch_set_value(weight_value_tuples)
        f.close()

    def to_json(self, **kwargs):
        '''Returns a JSON string containing the network configuration.

        To load a network from a JSON save file, use
        `keras.models.model_from_json(json_string, custom_objects={})`.
        '''
        import json

        def get_json_type(obj):
            # if obj is any numpy type
            if type(obj).__module__ == np.__name__:
                return obj.item()

            # if obj is a python 'type'
            if type(obj).__name__ == type.__name__:
                return obj.__name__

            raise TypeError('Not JSON Serializable')

        config = self.get_config()
        model_config = {
            'class_name': self.__class__.__name__,
            'config': config,
        }
        return json.dumps(model_config, default=get_json_type, **kwargs)

    def to_yaml(self, **kwargs):
        '''Returns a yaml string containing the network configuration.

        To load a network from a yaml save file, use
        `keras.models.model_from_yaml(yaml_string, custom_objects={})`.

        `custom_objects` should be a dictionary mapping
        the names of custom losses / layers / etc to the corresponding
        functions / classes.
        '''
        import yaml
        config = self.get_config()
        model_config = {
            'class_name': self.__class__.__name__,
            'config': config,
        }
        return yaml.dump(model_config, **kwargs)

    def summary(self):
        from keras.utils.layer_utils import print_summary

        if hasattr(self, 'flattened_layers'):
            # support for legacy Sequential/Merge behavior
            flattened_layers = self.flattened_layers
        else:
            flattened_layers = self.layers

        print_summary(flattened_layers, getattr(self, 'container_nodes', None))


def get_source_inputs(tensor, layer=None, node_index=None):
    '''Returns the list of input tensors
    necessary to compute `tensor`.

    Output will always be a list of tensors
    (potentially with 1 element).

    # Arguments
        tensor: the tensor to start from.
        layer: origin layer of the tensor. Will be
            determined via tensor._keras_history if not provided.
        node_index: origin node index of the tensor.
    '''
    if not hasattr(tensor, '_keras_history'):
        raise Exception('Tensor must be a Keras tensor. Found: ' + str(tensor))

    if layer is None or node_index:
        layer, node_index, _ = tensor._keras_history
    if not layer.inbound_nodes:
        return [tensor]
    else:
        node = layer.inbound_nodes[node_index]
        if not node.inbound_layers:
            # reached an Input layer, stop recursion
            return node.input_tensors
        else:
            source_tensors = []
            for i in range(len(node.inbound_layers)):
                x = node.input_tensors[i]
                layer = node.inbound_layers[i]
                node_index = node.node_indices[i]
                previous_sources = get_source_inputs(x,
                                                     layer,
                                                     node_index)
                # avoid input redundancy
                for x in previous_sources:
                    if x not in source_tensors:
                        source_tensors.append(x)
            return source_tensors

from __future__ import print_function
from __future__ import absolute_import

import warnings
import copy
import time
import numpy as np
import threading
try:
    import queue
except ImportError:
    import Queue as queue

from .topology import Container
from .. import backend as K
from .. import optimizers
from .. import objectives
from .. import metrics as metrics_module
from ..utils.generic_utils import Progbar
from .. import callbacks as cbks


def standardize_input_data(data, names, shapes=None, check_batch_dim=True,
                           exception_prefix=''):
    '''Users may pass data as a list of arrays, dictionary of arrays,
    or as a single array. We normalize this to an ordered list of
    arrays (same order as `names`), while checking that the provided
    arrays have shapes that match the network's expectations.
    '''
    if type(data) is dict:
        arrays = []
        for name in names:
            if name not in data:
                raise Exception('No data provided for "' +
                                name + '". Need data for each key in: ' +
                                str(data.keys()))
            arrays.append(data[name])
    elif type(data) is list:
        if len(data) != len(names):
            if len(data) > 0 and hasattr(data[0], 'shape'):
                raise Exception('Error when checking ' + exception_prefix +
                                ': the list of Numpy arrays '
                                'that you are passing to your model '
                                'is not the size the model expected. '
                                'Expected to see ' + str(len(names)) +
                                ' arrays but instead got '
                                'the following list of ' + str(len(data)) +
                                ' arrays: ' + str(data)[:200] +
                                '...')
            else:
                if len(names) == 1:
                    data = [np.asarray(data)]
                else:
                    raise Exception('Error when checking ' + exception_prefix +
                                    ': you are passing a list as '
                                    'input to your model, '
                                    'but the model expects a '
                                    'a list of ' + str(len(names)) +
                                    ' Numpy arrays instead. '
                                    'The list you passed was: ' +
                                    str(data)[:200])
        arrays = data
    else:
        if not hasattr(data, 'shape'):
            raise Exception('Error when checking ' + exception_prefix +
                            ': data should be a Numpy array, '
                            'or list/dict of Numpy arrays. '
                            'Found: ' + str(data)[:200] + '...')
        if len(names) != 1:
            # case: model expects multiple inputs but only received
            # a single Numpy array
            raise Exception('The model expects ' + str(len(names)) +
                            ' input arrays, but only received one array. '
                            'Found: array with shape ' + str(data.shape))
        arrays = [data]

    # make arrays at least 2D
    for i in range(len(names)):
        array = arrays[i]
        if len(array.shape) == 1:
            array = np.expand_dims(array, 1)
            arrays[i] = array

    # check shapes compatibility
    if shapes:
        for i in range(len(names)):
            if not i and not check_batch_dim:
                # skip the first axis
                continue
            array = arrays[i]
            if len(array.shape) != len(shapes[i]):
                raise Exception('Error when checking ' + exception_prefix +
                                ': expected ' + names[i] +
                                ' to have ' + str(len(shapes[i])) +
                                ' dimensions, but got array with shape ' +
                                str(array.shape))
            for dim, ref_dim in zip(array.shape, shapes[i]):
                if ref_dim:
                    if ref_dim != dim:
                        raise Exception('Error when checking ' + exception_prefix +
                                        ': expected ' + names[i] +
                                        ' to have shape ' + str(shapes[i]) +
                                        ' but got array with shape ' +
                                        str(array.shape))
    return arrays


def standardize_sample_or_class_weights(x_weight, output_names, weight_type):
    if x_weight is None or len(x_weight) == 0:
        return [None for _ in output_names]
    if len(output_names) == 1:
        if type(x_weight) is list and len(x_weight) == 1:
            return x_weight
        if type(x_weight) is dict and output_names[0] in x_weight:
            return [x_weight[output_names[0]]]
        else:
            return [x_weight]
    if type(x_weight) is list:
        if len(x_weight) != len(output_names):
            raise Exception('Provided `' + weight_type + '` was a list of ' +
                            str(len(x_weight)) +
                            ' elements, but the model has ' +
                            str(len(output_names)) + ' outputs. '
                            'You should provide one `' + weight_type + '`'
                            'array per model output.')
        return x_weight
    if type(x_weight) is dict:
        x_weights = []
        for name in output_names:
            x_weights.append(x_weight.get(name))
        return x_weights
    else:
        raise Exception('The model has multiple outputs, so `' +
                        weight_type + '` '
                        'should be either a list of a dict. '
                        'Provided `' + weight_type +
                        '` type not understood: ' +
                        str(x_weight))


def standardize_class_weights(class_weight, output_names):
    return standardize_sample_or_class_weights(class_weight,
                                               output_names,
                                               'class_weight')


def standardize_sample_weights(sample_weight, output_names):
    return standardize_sample_or_class_weights(sample_weight,
                                               output_names,
                                               'sample_weight')


def check_array_lengths(X, Y, W):
    x_lengths = [x.shape[0] for x in X]
    y_lengths = [y.shape[0] for y in Y]
    w_lengths = [w.shape[0] for w in W]
    set_x = set(x_lengths)
    if len(set_x) != 1:
        raise Exception('All input arrays (x) should have '
                        'the same number of samples.')
    set_y = set(y_lengths)
    if len(set_y) != 1:
        raise Exception('All target arrays (y) should have '
                        'the same number of samples.')
    set_w = set(w_lengths)
    if len(set_w) != 1:
        raise Exception('All sample_weight arrays should have '
                        'the same number of samples.')
    if list(set_x)[0] != list(set_y)[0]:
        raise Exception('Input arrays should have '
                        'the same number of samples as target arrays. Found ' +
                        str(list(set_x)[0]) + ' input samples and ' +
                        str(list(set_y)[0]) + ' target samples.')
    if list(set_x)[0] != list(set_w)[0]:
        raise Exception('Sample_weight arrays should have '
                        'the same number of samples as input arrays. Found ' +
                        str(list(set_x)[0]) + ' input samples and ' +
                        str(list(set_w)[0]) + ' target samples.')


def check_loss_and_target_compatibility(targets, losses, output_shapes):
    assert len(targets) == len(losses) == len(output_shapes)
    key_losses = {'mean_square_error',
                  'binary_crossentropy',
                  'categorical_crossentropy'}
    for y, loss, shape in zip(targets, losses, output_shapes):
        if loss.__name__ == 'categorical_crossentropy':
            if y.shape[1] == 1:
                raise Exception('You are passing a target array of shape ' + str(y.shape) +
                                ' while using as loss `categorical_crossentropy`. '
                                '`categorical_crossentropy` expects '
                                'targets to be binary matrices (1s and 0s) '
                                'of shape (samples, classes). '
                                'If your targets are integer classes, '
                                'you can convert them to the expected format via:\n'
                                '```\n'
                                'from keras.utils.np_utils import to_categorical\n'
                                'y_binary = to_categorical(y_int)\n'
                                '```\n'
                                '\n'
                                'Alternatively, you can use the loss function '
                                '`sparse_categorical_crossentropy` instead, '
                                'which does expect integer targets.')
        if loss.__name__ in key_losses and shape[1] is not None and y.shape[1] != shape[1]:
                raise Exception('A target array with shape ' + str(y.shape) +
                                ' was passed for an output of shape ' + str(shape) +
                                ' while using as loss `' + loss.__name__ + '`. '
                                'This loss expects '
                                'targets to have the same shape '
                                'as the output.')


def collect_metrics(metrics, output_names):
    if not metrics:
        return [[] for _ in output_names]
    if type(metrics) is list:
        # we then apply all metrics to all outputs.
        return [copy.copy(metrics) for _ in output_names]
    elif type(metrics) is dict:
        nested_metrics = []
        for name in output_names:
            output_metrics = metrics.get(name, [])
            if type(output_metrics) is not list:
                output_metrics = [output_metrics]
            nested_metrics.append(output_metrics)
        return nested_metrics
    else:
        raise Exception('Type of `metrics` argument not understood. '
                        'Expected a list or dictionary, found: ' +
                        str(metrics))


def collect_trainable_weights(layer):
    trainable = getattr(layer, 'trainable', True)
    if not trainable:
        return []
    weights = []
    if layer.__class__.__name__ in ['Sequential', 'Model']:
        for sublayer in layer.layers:
            weights += collect_trainable_weights(sublayer)
    elif layer.__class__.__name__ == 'Graph':
        for sublayer in layer._graph_nodes.values():
            weights += collect_trainable_weights(sublayer)
    else:
        weights += layer.trainable_weights
    return weights


def batch_shuffle(index_array, batch_size):
    '''This shuffles an array in a batch-wise fashion.
    Useful for shuffling HDF5 arrays
    (where one cannot access arbitrary indices).
    '''
    batch_count = int(len(index_array) / batch_size)
    # to reshape we need to be cleanly divisible by batch size
    # we stash extra items and reappend them after shuffling
    last_batch = index_array[batch_count * batch_size:]
    index_array = index_array[:batch_count * batch_size]
    index_array = index_array.reshape((batch_count, batch_size))
    np.random.shuffle(index_array)
    index_array = index_array.flatten()
    return np.append(index_array, last_batch)


def make_batches(size, batch_size):
    '''Returns a list of batch indices (tuples of indices).
    '''
    nb_batch = int(np.ceil(size / float(batch_size)))
    return [(i * batch_size, min(size, (i + 1) * batch_size))
            for i in range(0, nb_batch)]


def slice_X(X, start=None, stop=None):
    '''This takes an array-like, or a list of
    array-likes, and outputs:
        - X[start:stop] if X is an array-like
        - [x[start:stop] for x in X] if X in a list

    Can also work on list/array of indices: `slice_X(x, indices)`

    # Arguments:
        start: can be an integer index (start index)
            or a list/array of indices
        stop: integer (stop index); should be None if
            `start` was a list.
    '''
    if type(X) == list:
        if hasattr(start, '__len__'):
            # hdf5 datasets only support list objects as indices
            if hasattr(start, 'shape'):
                start = start.tolist()
            return [x[start] for x in X]
        else:
            return [x[start:stop] for x in X]
    else:
        if hasattr(start, '__len__'):
            if hasattr(start, 'shape'):
                start = start.tolist()
            return X[start]
        else:
            return X[start:stop]


def weighted_objective(fn):
    '''Transforms an objective function `fn(y_true, y_pred)`
    into a sample-weighted, cost-masked objective function
    `fn(y_true, y_pred, weights, mask)`.
    '''
    def weighted(y_true, y_pred, weights, mask=None):
        # score_array has ndim >= 2
        score_array = fn(y_true, y_pred)
        if mask is not None:
            # Cast the mask to floatX to avoid float64 upcasting in theano
            mask = K.cast(mask, K.floatx())
            # mask should have the same shape as score_array
            score_array *= mask
            #  the loss per batch should be proportional
            #  to the number of unmasked samples.
            score_array /= K.mean(mask)

        # reduce score_array to same ndim as weight array
        ndim = K.ndim(score_array)
        weight_ndim = K.ndim(weights)
        score_array = K.mean(score_array, axis=list(range(weight_ndim, ndim)))

        # apply sample weighting
        if weights is not None:
            score_array *= weights
            score_array /= K.mean(K.cast(K.not_equal(weights, 0), K.floatx()))
        return K.mean(score_array)
    return weighted


def standardize_weights(y, sample_weight=None, class_weight=None,
                        sample_weight_mode=None):
    '''Performs weight input validation and standardization
    to a single sample-wise (or timestep-wise) weight array.
    '''
    if sample_weight_mode is not None:
        if sample_weight_mode != 'temporal':
            raise Exception('"sample_weight_mode '
                            'should be None or "temporal". '
                            'Found: ' + str(sample_weight_mode))
        if len(y.shape) < 3:
            raise Exception('Found a sample_weight array for '
                            'an input with shape ' +
                            str(y.shape) + '. '
                            'Timestep-wise sample weighting (use of '
                            'sample_weight_mode="temporal") is restricted to '
                            'outputs that are at least 3D, i.e. that have '
                            'a time dimension.')
        if sample_weight is not None and len(sample_weight.shape) != 2:
            raise Exception('Found a sample_weight array with shape ' +
                            str(sample_weight.shape) + '. '
                            'In order to use timestep-wise sample weighting, '
                            'you should pass a 2D sample_weight array.')
    else:
        if sample_weight is not None and len(sample_weight.shape) != 1:
            raise Exception('Found a sample_weight array with shape ' +
                            str(sample_weight.shape) + '. '
                            'In order to use timestep-wise sample weights, '
                            'you should specify sample_weight_mode="temporal" '
                            'in compile(). If you just mean to use '
                            'sample-wise weights, make sure your '
                            'sample_weight array is 1D.')

    if sample_weight is not None:
        assert len(sample_weight.shape) <= len(y.shape)
        # TODO: proper error message
        assert y.shape[:sample_weight.ndim] == sample_weight.shape
        return sample_weight
    elif isinstance(class_weight, dict):
        if len(y.shape) > 2:
            raise Exception('class_weight not supported for '
                            '3+ dimensional targets.')
        if y.shape[1] > 1:
            y_classes = y.argmax(axis=1)
        elif y.shape[1] == 1:
            y_classes = np.reshape(y, y.shape[0])
        else:
            y_classes = y
        weights = np.asarray([class_weight[cls] for cls in y_classes])
        return weights
    else:
        if sample_weight_mode is None:
            return np.ones((y.shape[0],))
        else:
            return np.ones((y.shape[0], y.shape[1]))


def generator_queue(generator, max_q_size=10,
                    wait_time=0.05, nb_worker=1):
    '''Builds a threading queue out of a data generator.
    Used in `fit_generator`, `evaluate_generator`, `predict_generator`.
    '''
    q = queue.Queue()
    _stop = threading.Event()

    def data_generator_task():
        while not _stop.is_set():
            try:
                if q.qsize() < max_q_size:
                    try:
                        generator_output = next(generator)
                    except ValueError:
                        continue
                    q.put(generator_output)
                else:
                    time.sleep(wait_time)
            except Exception:
                _stop.set()
                raise

    generator_threads = [threading.Thread(target=data_generator_task)
                         for _ in range(nb_worker)]

    for thread in generator_threads:
        thread.daemon = True
        thread.start()

    return q, _stop


class Model(Container):

    def compile(self, optimizer, loss, metrics=[], loss_weights=None,
                sample_weight_mode=None, **kwargs):
        '''Configures the model for training.

        # Arguments
            optimizer: str (name of optimizer) or optimizer object.
                See [optimizers](/optimizers).
            loss: str (name of objective function) or objective function.
                See [objectives](/objectives).
                If the model has multiple outputs, you can use a different loss
                on each output by passing a dictionary or a list of objectives.
            metrics: list of metrics to be evaluated by the model
                during training and testing.
                Typically you will use `metrics=['accuracy']`.
                To specify different metrics for different outputs of a
                multi-output model, you could also pass a dictionary,
                such as `metrics={'output_a': 'accuracy'}`.
            sample_weight_mode: if you need to do timestep-wise
                sample weighting (2D weights), set this to "temporal".
                "None" defaults to sample-wise weights (1D).
                If the model has multiple outputs, you can use a different
                `sample_weight_mode` on each output by passing a
                dictionary or a list of modes.
            kwargs: when using the Theano backend, these arguments
                are passed into K.function. Ignored for Tensorflow backend.
        '''
        self.optimizer = optimizers.get(optimizer)
        self.sample_weight_mode = sample_weight_mode
        self.loss = loss

        # prepare loss weights
        if loss_weights is None:
            loss_weights_list = [1. for _ in range(len(self.outputs))]
        elif type(loss_weights) is dict:
            for name in loss_weights:
                if name not in self.output_names:
                    raise Exception('Unknown entry in loss_weights '
                                    'dictionary: "' + name + '". '
                                    'Only expected the following keys: ' +
                                    str(self.output_names))
            loss_weights_list = []
            for name in self.output_names:
                loss_weights_list.append(loss_weights.get(name, 1.))
        elif type(loss_weights) is list:
            if len(loss_weights) != len(self.outputs):
                raise Exception('When passing a list as loss_weights, '
                                'it should have one entry per model outputs. '
                                'The model has ' + str(len(self.outputs)) +
                                ' outputs, but you passed loss_weights=' +
                                str(loss))
            loss_weights_list = loss_weights
        else:
            raise Exception('Could not interpret loss_weights argument: ' +
                            str(loss_weights))

        # prepare loss functions
        if type(loss) is dict:
            for name in loss:
                if name not in self.output_names:
                    raise Exception('Unknown entry in loss '
                                    'dictionary: "' + name + '". '
                                    'Only expected the following keys: ' +
                                    str(self.output_names))
            loss_functions = []
            for name in self.output_names:
                if name not in loss:
                    raise Exception('Output "' + name +
                                    '" missing from loss dictionary')
                loss_functions.append(objectives.get(loss[name]))
        elif type(loss) is list:
            if len(loss) != len(self.outputs):
                raise Exception('When passing a list as loss, '
                                'it should have one entry per model outputs. '
                                'The model has ' + str(len(self.outputs)) +
                                ' outputs, but you passed loss=' +
                                str(loss))
            loss_functions = [objectives.get(l) for l in loss]
        else:
            loss_function = objectives.get(loss)
            loss_functions = [loss_function for _ in range(len(self.outputs))]
        self.loss_functions = loss_functions
        weighted_losses = [weighted_objective(fn) for fn in loss_functions]

        # prepare output masks
        masks = self.compute_mask(self.inputs, mask=None)
        if masks is None:
            masks = [None for _ in self.outputs]
        if type(masks) is not list:
            masks = [masks]

        # prepare sample weights
        if type(sample_weight_mode) is dict:
            for name in sample_weight_mode:
                if name not in self.output_names:
                    raise Exception('Unknown entry in '
                                    'sample_weight_mode dictionary: "' +
                                    name + '". '
                                    'Only expected the following keys: ' +
                                    str(self.output_names))
            sample_weights = []
            sample_weight_modes = []
            for name in self.output_names:
                if name not in sample_weight_mode:
                    raise Exception('Output "' + name +
                                    '" missing from sample_weight_modes '
                                    'dictionary')
                if sample_weight_mode.get(name) == 'temporal':
                    weight = K.placeholder(ndim=2, name=name + '_sample_weights')
                    sample_weight_modes.append('temporal')
                else:
                    weight = K.placeholder(ndim=1, name=name + '_sample_weights')
                    sample_weight_modes.append(None)
                sample_weights.append(weight)
        elif type(sample_weight_mode) is list:
            if len(sample_weight_mode) != len(self.outputs):
                raise Exception('When passing a list as sample_weight_mode, ' +
                                'it should have one entry per model outputs. '
                                'The model has ' + str(len(self.outputs)) +
                                ' outputs, but you passed sample_weight_mode=' +
                                str(sample_weight_mode))
            sample_weights = []
            sample_weight_modes = []
            for mode, name in zip(sample_weight_mode, self.output_names):
                if mode == 'temporal':
                    weight = K.placeholder(ndim=2, name=name + '_sample_weights')
                    sample_weight_modes.append('temporal')
                else:
                    weight = K.placeholder(ndim=1, name=name + '_sample_weights')
                    sample_weight_modes.append(None)
                sample_weights.append(weight)
        else:
            if sample_weight_mode == 'temporal':
                sample_weights = [K.placeholder(ndim=2, name=name + '_sample_weights')
                                  for name in self.output_names]
                sample_weight_modes = ['temporal' for name in self.output_names]
            else:
                sample_weights = [K.placeholder(ndim=1, name=name + '_sample_weights')
                                  for name in self.output_names]
                sample_weight_modes = [None for name in self.output_names]
        self.sample_weight_modes = sample_weight_modes

        # prepare targets of model
        self.targets = []
        for i in range(len(self.outputs)):
            shape = self.internal_output_shapes[i]
            name = self.output_names[i]
            self.targets.append(K.placeholder(ndim=len(shape), name=name + '_target'))

        # prepare metrics
        self.metrics_names = ['loss']
        self.metrics = []

        # compute total loss
        total_loss = None
        for i in range(len(self.outputs)):
            y_true = self.targets[i]
            y_pred = self.outputs[i]
            weighted_loss = weighted_losses[i]
            sample_weight = sample_weights[i]
            mask = masks[i]
            loss_weight = loss_weights_list[i]
            output_loss = weighted_loss(y_true, y_pred,
                                        sample_weight, mask)
            if len(self.outputs) > 1:
                self.metrics.append(output_loss)
                self.metrics_names.append(self.output_names[i] + '_loss')
            if total_loss is None:
                total_loss = loss_weight * output_loss
            else:
                total_loss += loss_weight * output_loss

        # add regularization penalties to the loss
        for r in self.regularizers:
            total_loss = r(total_loss)

        # list of same size as output_names.
        # contains tuples (metrics for output, names of metrics)
        nested_metrics = collect_metrics(metrics, self.output_names)
        for i in range(len(self.outputs)):
            y_true = self.targets[i]
            y_pred = self.outputs[i]
            output_metrics = nested_metrics[i]

            for metric in output_metrics:
                if metric == 'accuracy' or metric == 'acc':
                    # custom handling of accuracy (because of class mode duality)
                    output_shape = self.internal_output_shapes[i]
                    if output_shape[-1] == 1:
                        # case: binary accuracy
                        self.metrics.append(metrics_module.binary_accuracy(y_true, y_pred))
                    elif self.loss_functions[i] == objectives.sparse_categorical_crossentropy:
                        # case: categorical accuracy with sparse targets
                        self.metrics.append(
                            metrics_module.sparse_categorical_accuracy(y_true, y_pred))
                    else:
                        # case: categorical accuracy with dense targets
                        self.metrics.append(metrics_module.categorical_accuracy(y_true, y_pred))
                    if len(self.output_names) == 1:
                        self.metrics_names.append('acc')
                    else:
                        self.metrics_names.append(self.output_layers[i].name + '_acc')
                else:
                    metric_fn = metrics_module.get(metric)
                    self.metrics.append(metric_fn(y_true, y_pred))
                    if len(self.output_names) == 1:
                        self.metrics_names.append(metric_fn.__name__)
                    else:
                        self.metrics_names.append(self.output_layers[i].name + '_' + metric_fn.__name__)

        # prepare gradient updates and state updates
        self.optimizer = optimizers.get(optimizer)
        self.total_loss = total_loss
        self.sample_weights = sample_weights

        # functions for train, test and predict will
        # be compiled lazily when required.
        # This saves time when the user is not using all functions.
        self._function_kwargs = kwargs

        self.train_function = None
        self.test_function = None
        self.predict_function = None

    def _make_train_function(self):
        if not hasattr(self, 'train_function'):
            raise Exception('You must compile your model before using it.')
        if self.train_function is None:
            if self.uses_learning_phase:
                inputs = self.inputs + self.targets + self.sample_weights + [K.learning_phase()]
            else:
                inputs = self.inputs + self.targets + self.sample_weights

            # get trainable weights
            trainable_weights = []
            for layer in self.layers:
                trainable_weights += collect_trainable_weights(layer)

            training_updates = self.optimizer.get_updates(trainable_weights, self.constraints, self.total_loss)
            updates = self.updates + training_updates

            # returns loss and metrics. Updates weights at each call.
            self.train_function = K.function(inputs,
                                             [self.total_loss] + self.metrics,
                                             updates=updates,
                                             **self._function_kwargs)

    def _make_test_function(self):
        if not hasattr(self, 'test_function'):
            raise Exception('You must compile your model before using it.')
        if self.test_function is None:
            if self.uses_learning_phase:
                inputs = self.inputs + self.targets + self.sample_weights + [K.learning_phase()]
            else:
                inputs = self.inputs + self.targets + self.sample_weights
            # return loss and metrics, no gradient updates.
            # Does update the network states.
            self.test_function = K.function(inputs,
                                            [self.total_loss] + self.metrics,
                                            updates=self.state_updates,
                                            **self._function_kwargs)

    def _make_predict_function(self):
        if not hasattr(self, 'predict_function'):
            self.predict_function = None
        if self.predict_function is None:
            if self.uses_learning_phase:
                inputs = self.inputs + [K.learning_phase()]
            else:
                inputs = self.inputs
            # returns network outputs. Does not update weights.
            # Does update the network states.
            kwargs = getattr(self, '_function_kwargs', {})
            self.predict_function = K.function(inputs,
                                               self.outputs,
                                               updates=self.state_updates,
                                               **kwargs)

    def _fit_loop(self, f, ins, out_labels=[], batch_size=32,
                  nb_epoch=100, verbose=1, callbacks=[],
                  val_f=None, val_ins=None, shuffle=True,
                  callback_metrics=[]):
        '''Abstract fit function for f(ins).
        Assume that f returns a list, labeled by out_labels.

        # Arguments
            f: Keras function returning a list of tensors
            ins: list of tensors to be fed to `f`
            out_labels: list of strings, display names of
                the outputs of `f`
            batch_size: integer batch size
            nb_epoch: number of times to iterate over the data
            verbose: verbosity mode, 0, 1 or 2
            callbacks: list of callbacks to be called during training
            val_f: Keras function to call for validation
            val_ins: list of tensors to be fed to `val_f`
            shuffle: whether to shuffle the data at the beginning of each epoch
            callback_metrics: list of strings, the display names of the metrics
                passed to the callbacks. They should be the
                concatenation of list the display names of the outputs of
                 `f` and the list of display names of the outputs of `f_val`.

        # Returns
            `History` object.
        '''
        do_validation = False
        if val_f and val_ins:
            do_validation = True
            if verbose:
                print('Train on %d samples, validate on %d samples' %
                      (len(ins[0]), len(val_ins[0])))

        nb_train_sample = len(ins[0])
        index_array = np.arange(nb_train_sample)

        self.history = cbks.History()
        callbacks = [cbks.BaseLogger()] + callbacks + [self.history]
        if verbose:
            callbacks += [cbks.ProgbarLogger()]
        callbacks = cbks.CallbackList(callbacks)

        # it's possible to callback a different model than self
        # (used by Sequential models)
        if hasattr(self, 'callback_model') and self.callback_model:
            callback_model = self.callback_model
        else:
            callback_model = self

        callbacks._set_model(callback_model)
        callbacks._set_params({
            'batch_size': batch_size,
            'nb_epoch': nb_epoch,
            'nb_sample': nb_train_sample,
            'verbose': verbose,
            'do_validation': do_validation,
            'metrics': callback_metrics,
        })
        callbacks.on_train_begin()
        callback_model.stop_training = False
        self.validation_data = val_ins

        for epoch in range(nb_epoch):
            callbacks.on_epoch_begin(epoch)
            if shuffle == 'batch':
                index_array = batch_shuffle(index_array, batch_size)
            elif shuffle:
                np.random.shuffle(index_array)

            batches = make_batches(nb_train_sample, batch_size)
            for batch_index, (batch_start, batch_end) in enumerate(batches):
                batch_ids = index_array[batch_start:batch_end]
                try:
                    if type(ins[-1]) is float:
                        # do not slice the training phase flag
                        ins_batch = slice_X(ins[:-1], batch_ids) + [ins[-1]]
                    else:
                        ins_batch = slice_X(ins, batch_ids)
                except TypeError:
                    raise Exception('TypeError while preparing batch. '
                                    'If using HDF5 input data, '
                                    'pass shuffle="batch".')
                batch_logs = {}
                batch_logs['batch'] = batch_index
                batch_logs['size'] = len(batch_ids)
                callbacks.on_batch_begin(batch_index, batch_logs)
                outs = f(ins_batch)
                if type(outs) != list:
                    outs = [outs]
                for l, o in zip(out_labels, outs):
                    batch_logs[l] = o

                callbacks.on_batch_end(batch_index, batch_logs)

                epoch_logs = {}
                if batch_index == len(batches) - 1:  # last batch
                    # validation
                    if do_validation:
                        # replace with self._evaluate
                        val_outs = self._test_loop(val_f, val_ins,
                                                   batch_size=batch_size,
                                                   verbose=0)
                        if type(val_outs) != list:
                            val_outs = [val_outs]
                        # same labels assumed
                        for l, o in zip(out_labels, val_outs):
                            epoch_logs['val_' + l] = o
            callbacks.on_epoch_end(epoch, epoch_logs)
            if callback_model.stop_training:
                break
        callbacks.on_train_end()
        return self.history

    def _predict_loop(self, f, ins, batch_size=32, verbose=0):
        '''Abstract method to loop over some data in batches.

        # Arguments
            f: Keras function returning a list of tensors.
            ins: list of tensors to be fed to `f`.
            batch_size: integer batch size.
            verbose: verbosity mode.

        # Returns
            Array of prections (if the model has a single output)
            or list of arrays of predictions
            (if the model has multiple outputs).
        '''
        nb_sample = len(ins[0])
        outs = []
        if verbose == 1:
            progbar = Progbar(target=nb_sample)
        batches = make_batches(nb_sample, batch_size)
        index_array = np.arange(nb_sample)
        for batch_index, (batch_start, batch_end) in enumerate(batches):
            batch_ids = index_array[batch_start:batch_end]
            if type(ins[-1]) is float:
                # do not slice the training phase flag
                ins_batch = slice_X(ins[:-1], batch_ids) + [ins[-1]]
            else:
                ins_batch = slice_X(ins, batch_ids)

            batch_outs = f(ins_batch)
            if type(batch_outs) != list:
                batch_outs = [batch_outs]
            if batch_index == 0:
                for batch_out in batch_outs:
                    shape = (nb_sample,) + batch_out.shape[1:]
                    outs.append(np.zeros(shape))

            for i, batch_out in enumerate(batch_outs):
                outs[i][batch_start:batch_end] = batch_out
            if verbose == 1:
                progbar.update(batch_end)
        if len(outs) == 1:
            return outs[0]
        return outs

    def _test_loop(self, f, ins, batch_size=32, verbose=0):
        '''Abstract method to loop over some data in batches.

        # Arguments
            f: Keras function returning a list of tensors.
            ins: list of tensors to be fed to `f`.
            batch_size: integer batch size.
            verbose: verbosity mode.

        # Returns
            Scalar loss (if the model has a single output and no metrics)
            or list of scalars (if the model has multiple outputs
            and/or metrics). The attribute `model.metrics_names` will give you
            the display labels for the scalar outputs.
        '''
        nb_sample = len(ins[0])
        outs = []
        if verbose == 1:
            progbar = Progbar(target=nb_sample)
        batches = make_batches(nb_sample, batch_size)
        index_array = np.arange(nb_sample)
        for batch_index, (batch_start, batch_end) in enumerate(batches):
            batch_ids = index_array[batch_start:batch_end]
            if type(ins[-1]) is float:
                # do not slice the training phase flag
                ins_batch = slice_X(ins[:-1], batch_ids) + [ins[-1]]
            else:
                ins_batch = slice_X(ins, batch_ids)

            batch_outs = f(ins_batch)
            if type(batch_outs) == list:
                if batch_index == 0:
                    for batch_out in enumerate(batch_outs):
                        outs.append(0.)
                for i, batch_out in enumerate(batch_outs):
                    outs[i] += batch_out * len(batch_ids)
            else:
                if batch_index == 0:
                    outs.append(0.)
                outs[0] += batch_outs * len(batch_ids)

            if verbose == 1:
                progbar.update(batch_end)
        for i, out in enumerate(outs):
            outs[i] /= nb_sample
        if len(outs) == 1:
            return outs[0]
        return outs

    def _standardize_user_data(self, x, y,
                               sample_weight=None, class_weight=None,
                               check_batch_dim=True, batch_size=None):
        if not hasattr(self, 'optimizer'):
            raise Exception('You must compile a model before training/testing.'
                            ' Use `model.compile(optimizer, loss)`.')

        x = standardize_input_data(x, self.input_names,
                                   self.internal_input_shapes,
                                   check_batch_dim=False,
                                   exception_prefix='model input')
        y = standardize_input_data(y, self.output_names,
                                   self.internal_output_shapes,
                                   check_batch_dim=False,
                                   exception_prefix='model target')
        sample_weights = standardize_sample_weights(sample_weight,
                                                    self.output_names)
        class_weights = standardize_class_weights(class_weight,
                                                  self.output_names)
        sample_weights = [standardize_weights(ref, sw, cw, mode)
                          for (ref, sw, cw, mode)
                          in zip(y, sample_weights, class_weights, self.sample_weight_modes)]
        check_array_lengths(x, y, sample_weights)
        check_loss_and_target_compatibility(y, self.loss_functions, self.internal_output_shapes)
        if self.stateful and batch_size:
            if x[0].shape[0] % batch_size != 0:
                raise Exception('In a stateful network, '
                                'you should only pass inputs with '
                                'a number of samples that can be '
                                'divided by the batch size. Found: ' +
                                str(x[0].shape[0]) + ' samples')
        return x, y, sample_weights

    def fit(self, x, y, batch_size=32, nb_epoch=10, verbose=1, callbacks=[],
            validation_split=0., validation_data=None, shuffle=True,
            class_weight=None, sample_weight=None):
        '''Trains the model for a fixed number of epochs (iterations on a dataset).

        # Arguments
            x: Numpy array of training data,
                or list of Numpy arrays if the model has multiple inputs.
                If all inputs in the model are named, you can also pass a dictionary
                mapping input names to Numpy arrays.
            y: Numpy array of target data,
                or list of Numpy arrays if the model has multiple outputs.
                If all outputs in the model are named, you can also pass a dictionary
                mapping output names to Numpy arrays.
            batch_size: integer. Number of samples per gradient update.
            nb_epoch: integer, the number of times to iterate over the training data arrays.
            verbose: 0, 1, or 2. Verbosity mode. 0 = silent, 1 = verbose, 2 = one log line per epoch.
            callbacks: list of callbacks to be called during training.
                See [callbacks](/callbacks).
            validation_split: float between 0 and 1:
                fraction of the training data to be used as validation data.
                The model will set apart this fraction of the training data,
                will not train on it, and will evaluate the loss and any model metrics
                on this data at the end of each epoch.
            validation_data: data on which to evaluate the loss and any model metrics
                at the end of each epoch. The model will not be trained on this data.
                This could be a tuple (x_val, y_val) or a tuple (val_x, val_y, val_sample_weights).
            shuffle: boolean, whether to shuffle the training data before each epoch.
            class_weight: optional dictionary mapping classe indices (integers) to
                a weight (float) to apply to the model's loss for the samples
                from this class during training.
                This can be useful to tell the model to "pay more attention" to
                samples from an under-represented class.
            sample_weight: optional array of the same length as x, containing
                weights to apply to the model's loss for each sample.
                In the case of temporal data, you can pass a 2D array
                with shape (samples, sequence_length),
                to apply a different weight to every timestep of every sample.
                In this case you should make sure to specify sample_weight_mode="temporal" in compile().


        # Returns
            A `History` instance. Its `history` attribute contains
            all information collected during training.
        '''
        # validate user data
        x, y, sample_weights = self._standardize_user_data(x, y,
                                                           sample_weight=sample_weight,
                                                           class_weight=class_weight,
                                                           check_batch_dim=False,
                                                           batch_size=batch_size)
        # prepare validation data
        if validation_data:
            do_validation = True
            if len(validation_data) == 2:
                val_x, val_y = validation_data
                val_sample_weight = None
            elif len(validation_data) == 3:
                val_x, val_y, val_sample_weight = validation_data
            else:
                raise
            val_x, val_y, val_sample_weights = self._standardize_user_data(val_x, val_y,
                                                                           sample_weight=val_sample_weight,
                                                                           check_batch_dim=False,
                                                                           batch_size=batch_size)
            self._make_test_function()
            val_f = self.test_function
            if self.uses_learning_phase:
                val_ins = val_x + val_y + val_sample_weights + [0.]
            else:
                val_ins = val_x + val_y + val_sample_weights

        elif validation_split and 0. < validation_split < 1.:
            do_validation = True
            split_at = int(len(x[0]) * (1. - validation_split))
            x, val_x = (slice_X(x, 0, split_at), slice_X(x, split_at))
            y, val_y = (slice_X(y, 0, split_at), slice_X(y, split_at))
            sample_weights, val_sample_weights = (slice_X(sample_weights, 0, split_at), slice_X(sample_weights, split_at))
            self._make_test_function()
            val_f = self.test_function
            if self.uses_learning_phase:
                val_ins = val_x + val_y + val_sample_weights + [0.]
            else:
                val_ins = val_x + val_y + val_sample_weights
        else:
            do_validation = False
            val_f = None
            val_ins = None

        # prepare input arrays and training function
        if self.uses_learning_phase:
            ins = x + y + sample_weights + [1.]
        else:
            ins = x + y + sample_weights
        self._make_train_function()
        f = self.train_function

        # prepare display labels
        out_labels = self.metrics_names
        if do_validation:
            callback_metrics = copy.copy(out_labels) + ['val_' + n for n in out_labels]
        else:
            callback_metrics = copy.copy(out_labels)

        # delegate logic to _fit_loop
        return self._fit_loop(f, ins, out_labels=out_labels,
                              batch_size=batch_size, nb_epoch=nb_epoch,
                              verbose=verbose, callbacks=callbacks,
                              val_f=val_f, val_ins=val_ins, shuffle=shuffle,
                              callback_metrics=callback_metrics)

    def evaluate(self, x, y, batch_size=32, verbose=1, sample_weight=None):
        '''Returns the loss value and metrics values for the model
        in test mode. Computation in done in batches.

        # Arguments
            x: Numpy array of test data,
                or list of Numpy arrays if the model has multiple inputs.
                If all inputs in the model are named, you can also pass a dictionary
                mapping input names to Numpy arrays.
            y: Numpy array of target data,
                or list of Numpy arrays if the model has multiple outputs.
                If all outputs in the model are named, you can also pass a dictionary
                mapping output names to Numpy arrays.
            batch_size: integer. Number of samples per gradient update.

        # Returns
            Scalar test loss (if the model has a single output and no metrics)
            or list of scalars (if the model has multiple outputs
            and/or metrics). The attribute `model.metrics_names` will give you
            the display labels for the scalar outputs.
        '''
        # validate user data
        x, y, sample_weights = self._standardize_user_data(x, y,
                                                           sample_weight=sample_weight,
                                                           check_batch_dim=False,
                                                           batch_size=batch_size)
        # prepare inputs, delegate logic to _test_loop
        if self.uses_learning_phase:
            ins = x + y + sample_weights + [0.]
        else:
            ins = x + y + sample_weights
        self._make_test_function()
        f = self.test_function
        return self._test_loop(f, ins,
                               batch_size=batch_size,
                               verbose=verbose)

    def predict(self, x, batch_size=32, verbose=0):
        '''Generates output predictions for the input samples,
        processing the samples in a batched way.

        # Arguments
            x: the input data, as a Numpy array
                (or list of Numpy arrays if the model has multiple outputs).
            batch_size: integer.
            verbose: verbosity mode, 0 or 1.

        # Returns
            A Numpy array of predictions.
        '''
        # validate user data
        x = standardize_input_data(x, self.input_names,
                                   self.internal_input_shapes,
                                   check_batch_dim=False)
        if self.stateful:
            if x[0].shape[0] > batch_size and x[0].shape[0] % batch_size != 0:
                raise Exception('In a stateful network, '
                                'you should only pass inputs with '
                                'a number of samples that can be '
                                'divided by the batch size. Found: ' +
                                str(x[0].shape[0]) + ' samples. '
                                'Batch size: ' + str(batch_size) + '.')

        # prepare inputs, delegate logic to _predict_loop
        if self.uses_learning_phase:
            ins = x + [0.]
        else:
            ins = x
        self._make_predict_function()
        f = self.predict_function
        return self._predict_loop(f, ins,
                                  batch_size=batch_size, verbose=verbose)

    def train_on_batch(self, x, y,
                       sample_weight=None, class_weight=None):
        '''Runs a single gradient update on a single batch of data.

        # Arguments
            x: Numpy array of training data,
                or list of Numpy arrays if the model has multiple inputs.
                If all inputs in the model are named, you can also pass a dictionary
                mapping input names to Numpy arrays.
            y: Numpy array of target data,
                or list of Numpy arrays if the model has multiple outputs.
                If all outputs in the model are named, you can also pass a dictionary
                mapping output names to Numpy arrays.
            sample_weight: optional array of the same length as x, containing
                weights to apply to the model's loss for each sample.
                In the case of temporal data, you can pass a 2D array
                with shape (samples, sequence_length),
                to apply a different weight to every timestep of every sample.
                In this case you should make sure to specify sample_weight_mode="temporal" in compile().
            class_weight: optional dictionary mapping classe indices (integers) to
                a weight (float) to apply to the model's loss for the samples
                from this class during training.
                This can be useful to tell the model to "pay more attention" to
                samples from an under-represented class.

        # Returns
            Scalar training loss (if the model has a single output and no metrics)
            or list of scalars (if the model has multiple outputs
            and/or metrics). The attribute `model.metrics_names` will give you
            the display labels for the scalar outputs.
        '''
        x, y, sample_weights = self._standardize_user_data(x, y,
                                                           sample_weight=sample_weight,
                                                           class_weight=class_weight,
                                                           check_batch_dim=True)
        if self.uses_learning_phase:
            ins = x + y + sample_weights + [1.]
        else:
            ins = x + y + sample_weights
        self._make_train_function()
        outputs = self.train_function(ins)
        if len(outputs) == 1:
            return outputs[0]
        return outputs

    def test_on_batch(self, x, y, sample_weight=None):
        '''Test the model on a single batch of samples.

        # Arguments
            x: Numpy array of test data,
                or list of Numpy arrays if the model has multiple inputs.
                If all inputs in the model are named, you can also pass a dictionary
                mapping input names to Numpy arrays.
            y: Numpy array of target data,
                or list of Numpy arrays if the model has multiple outputs.
                If all outputs in the model are named, you can also pass a dictionary
                mapping output names to Numpy arrays.
            sample_weight: optional array of the same length as x, containing
                weights to apply to the model's loss for each sample.
                In the case of temporal data, you can pass a 2D array
                with shape (samples, sequence_length),
                to apply a different weight to every timestep of every sample.
                In this case you should make sure to specify sample_weight_mode="temporal" in compile().

        # Returns
            Scalar test loss (if the model has a single output and no metrics)
            or list of scalars (if the model has multiple outputs
            and/or metrics). The attribute `model.metrics_names` will give you
            the display labels for the scalar outputs.
        '''
        x, y, sample_weights = self._standardize_user_data(x, y,
                                                           sample_weight=sample_weight,
                                                           check_batch_dim=True)
        if self.uses_learning_phase:
            ins = x + y + sample_weights + [0.]
        else:
            ins = x + y + sample_weights
        self._make_test_function()
        outputs = self.test_function(ins)
        if len(outputs) == 1:
            return outputs[0]
        return outputs

    def predict_on_batch(self, x):
        '''Returns predictions for a single batch of samples.
        '''
        x = standardize_input_data(x, self.input_names,
                                   self.internal_input_shapes)
        if self.uses_learning_phase:
            ins = x + [0.]
        else:
            ins = x
        self._make_predict_function()
        outputs = self.predict_function(ins)
        if len(outputs) == 1:
            return outputs[0]
        return outputs

    def fit_generator(self, generator, samples_per_epoch, nb_epoch,
                      verbose=1, callbacks=[],
                      validation_data=None, nb_val_samples=None,
                      class_weight={}, max_q_size=10):
        '''Fits the model on data generated batch-by-batch by
        a Python generator.
        The generator is run in parallel to the model, for efficiency.
        For instance, this allows you to do real-time data augmentation
        on images on CPU in parallel to training your model on GPU.

        # Arguments
            generator: a generator.
                The output of the generator must be either
                - a tuple (inputs, targets)
                - a tuple (inputs, targets, sample_weights).
                All arrays should contain the same number of samples.
                The generator is expected to loop over its data
                indefinitely. An epoch finishes when `samples_per_epoch`
                samples have been seen by the model.
            samples_per_epoch: integer, number of samples to process before
                going to the next epoch.
            nb_epoch: integer, total number of iterations on the data.
            verbose: verbosity mode, 0, 1, or 2.
            callbacks: list of callbacks to be called during training.
            validation_data: this can be either
                - a generator for the validation data
                - a tuple (inputs, targets)
                - a tuple (inputs, targets, sample_weights).
            nb_val_samples: only relevant if `validation_data` is a generator.
                number of samples to use from validation generator
                at the end of every epoch.
            class_weight: dictionary mapping class indices to a weight
                for the class.
            max_q_size: maximum size for the generator queue

        # Returns
            A `History` object.

        # Example

        ```python
            def generate_arrays_from_file(path):
                while 1:
                    f = open(path)
                    for line in f:
                        # create numpy arrays of input data
                        # and labels, from each line in the file
                        x1, x2, y = process_line(line)
                        yield ({'input_1': x1, 'input_2': x2}, {'output': y})
                    f.close()

            model.fit_generator(generate_arrays_from_file('/my_file.txt'),
                                samples_per_epoch=10000, nb_epoch=10)
        ```
        '''
        wait_time = 0.01  # in seconds
        epoch = 0

        do_validation = bool(validation_data)
        self._make_train_function()
        if do_validation:
            self._make_test_function()

        # python 2 has 'next', 3 has '__next__'
        # avoid any explicit version checks
        val_gen = (hasattr(validation_data, 'next') or
                   hasattr(validation_data, '__next__'))
        if val_gen and not nb_val_samples:
            raise Exception('When using a generator for validation data, '
                            'you must specify a value for "nb_val_samples".')

        out_labels = self.metrics_names
        callback_metrics = out_labels + ['val_' + n for n in out_labels]

        # prepare callbacks
        self.history = cbks.History()
        callbacks = [cbks.BaseLogger()] + callbacks + [self.history]
        if verbose:
            callbacks += [cbks.ProgbarLogger()]
        callbacks = cbks.CallbackList(callbacks)

        # it's possible to callback a different model than self:
        if hasattr(self, 'callback_model') and self.callback_model:
            callback_model = self.callback_model
        else:
            callback_model = self
        callbacks._set_model(callback_model)
        callbacks._set_params({
            'nb_epoch': nb_epoch,
            'nb_sample': samples_per_epoch,
            'verbose': verbose,
            'do_validation': do_validation,
            'metrics': callback_metrics,
        })
        callbacks.on_train_begin()

        if do_validation and not val_gen:
            if len(validation_data) == 2:
                val_x, val_y = validation_data
                val_sample_weight = None
            elif len(validation_data) == 3:
                val_x, val_y, val_sample_weight = validation_data
            else:
                raise Exception('validation_data should be a tuple '
                                '(val_x, val_y, val_sample_weight) '
                                'or (val_x, val_y). Found: ' + str(validation_data))
            val_x, val_y, val_sample_weights = self._standardize_user_data(val_x, val_y, val_sample_weight)
            self.validation_data = val_x + [val_y, val_sample_weights]
        else:
            self.validation_data = None

        # start generator thread storing batches into a queue
        data_gen_queue, _stop = generator_queue(generator, max_q_size=max_q_size)

        callback_model.stop_training = False
        while epoch < nb_epoch:
            callbacks.on_epoch_begin(epoch)
            samples_seen = 0
            batch_index = 0
            while samples_seen < samples_per_epoch:
                generator_output = None
                while not _stop.is_set():
                    if not data_gen_queue.empty():
                        generator_output = data_gen_queue.get()
                        break
                    else:
                        time.sleep(wait_time)

                if not hasattr(generator_output, '__len__'):
                    _stop.set()
                    raise Exception('output of generator should be a tuple '
                                    '(x, y, sample_weight) '
                                    'or (x, y). Found: ' + str(generator_output))
                if len(generator_output) == 2:
                    x, y = generator_output
                    sample_weight = None
                elif len(generator_output) == 3:
                    x, y, sample_weight = generator_output
                else:
                    _stop.set()
                    raise Exception('output of generator should be a tuple '
                                    '(x, y, sample_weight) '
                                    'or (x, y). Found: ' + str(generator_output))
                # build batch logs
                batch_logs = {}
                if type(x) is list:
                    batch_size = len(x[0])
                elif type(x) is dict:
                    batch_size = len(list(x.values())[0])
                else:
                    batch_size = len(x)
                batch_logs['batch'] = batch_index
                batch_logs['size'] = batch_size
                callbacks.on_batch_begin(batch_index, batch_logs)

                try:
                    outs = self.train_on_batch(x, y,
                                               sample_weight=sample_weight,
                                               class_weight=class_weight)
                except Exception as e:
                    _stop.set()
                    raise

                if type(outs) != list:
                    outs = [outs]
                for l, o in zip(out_labels, outs):
                    batch_logs[l] = o

                callbacks.on_batch_end(batch_index, batch_logs)

                # construct epoch logs
                epoch_logs = {}
                batch_index += 1
                samples_seen += batch_size

                # epoch finished
                if samples_seen > samples_per_epoch:
                    warnings.warn('Epoch comprised more than '
                                  '`samples_per_epoch` samples, '
                                  'which might affect learning results. '
                                  'Set `samples_per_epoch` correctly '
                                  'to avoid this warning.')
                if samples_seen >= samples_per_epoch and do_validation:
                    if val_gen:
                        val_outs = self.evaluate_generator(validation_data,
                                                           nb_val_samples,
                                                           max_q_size=max_q_size)
                    else:
                        # no need for try/except because
                        # data has already been validated
                        val_outs = self.evaluate(val_x, val_y,
                                                 sample_weight=val_sample_weights,
                                                 verbose=0)
                    if type(val_outs) is not list:
                        val_outs = [val_outs]
                    # same labels assumed
                    for l, o in zip(out_labels, val_outs):
                        epoch_logs['val_' + l] = o

            callbacks.on_epoch_end(epoch, epoch_logs)
            epoch += 1
            if callback_model.stop_training:
                break

        _stop.set()
        callbacks.on_train_end()
        return self.history

    def evaluate_generator(self, generator, val_samples, max_q_size=10):
        '''Evaluates the model on a data generator. The generator should
        return the same kind of data as accepted by `test_on_batch`.

        Arguments:
            generator:
                generator yielding tuples (inputs, targets)
                or (inputs, targets, sample_weights)
            val_samples:
                total number of samples to generate from `generator`
                before returning.
            max_q_size: maximum size for the generator queue

        # Returns
            Scalar test loss (if the model has a single output and no metrics)
            or list of scalars (if the model has multiple outputs
            and/or metrics). The attribute `model.metrics_names` will give you
            the display labels for the scalar outputs.
        '''
        self._make_test_function()

        processed_samples = 0
        wait_time = 0.01
        all_outs = []
        weights = []
        data_gen_queue, _stop = generator_queue(generator, max_q_size=max_q_size)

        while processed_samples < val_samples:
            generator_output = None
            while not _stop.is_set():
                if not data_gen_queue.empty():
                    generator_output = data_gen_queue.get()
                    break
                else:
                    time.sleep(wait_time)

            if not hasattr(generator_output, '__len__'):
                _stop.set()
                raise Exception('output of generator should be a tuple '
                                '(x, y, sample_weight) '
                                'or (x, y). Found: ' + str(generator_output))
            if len(generator_output) == 2:
                x, y = generator_output
                sample_weight = None
            elif len(generator_output) == 3:
                x, y, sample_weight = generator_output
            else:
                _stop.set()
                raise Exception('output of generator should be a tuple '
                                '(x, y, sample_weight) '
                                'or (x, y). Found: ' + str(generator_output))
            try:
                outs = self.test_on_batch(x, y, sample_weight=sample_weight)
            except Exception as e:
                _stop.set()
                raise

            if type(x) is list:
                nb_samples = len(x[0])
            elif type(x) is dict:
                nb_samples = len(list(x.values())[0])
            else:
                nb_samples = len(x)
            all_outs.append(outs)

            processed_samples += nb_samples
            weights.append(nb_samples)

        _stop.set()
        if type(outs) is not list:
            return np.average(np.asarray(all_outs),
                              weights=weights)
        else:
            averages = []
            for i in range(len(outs)):
                averages.append(np.average([out[i] for out in all_outs],
                                weights=weights))
            return averages

    def predict_generator(self, generator, val_samples, max_q_size=10):
        '''Generates predictions for the input samples from a data generator.
        The generator should return the same kind of data as accepted by
        `predict_on_batch`.

        # Arguments
            generator: generator yielding batches of input samples.
            val_samples: total number of samples to generate from `generator`
                before returning.
            max_q_size: maximum size for the generator queue

        # Returns
            Numpy array(s) of predictions.
        '''
        self._make_predict_function()

        processed_samples = 0
        wait_time = 0.01
        all_outs = []
        data_gen_queue, _stop = generator_queue(generator, max_q_size=max_q_size)

        while processed_samples < val_samples:
            generator_output = None
            while not _stop.is_set():
                if not data_gen_queue.empty():
                    generator_output = data_gen_queue.get()
                    break
                else:
                    time.sleep(wait_time)

            if isinstance(generator_output, tuple):
                if len(generator_output) == 2:
                    x, y = generator_output
                    sample_weight = None
                elif len(generator_output) == 3:
                    x, y, sample_weight = generator_output
                else:
                    _stop.set()
                    raise Exception('output of generator should be a tuple '
                                    '(x, y, sample_weight) '
                                    'or (x, y). Found: ' + str(generator_output))
            else:
                x = generator_output

            try:
                outs = self.predict_on_batch(x)
            except Exception as e:
                _stop.set()
                raise

            if type(x) is list:
                nb_samples = len(x[0])
            elif type(x) is dict:
                nb_samples = len(list(x.values())[0])
            else:
                nb_samples = len(x)

            if type(outs) != list:
                outs = [outs]

            if len(all_outs) == 0:
                for out in outs:
                    shape = (val_samples,) + out.shape[1:]
                    all_outs.append(np.zeros(shape))

            for i, out in enumerate(outs):
                all_outs[i][processed_samples:(processed_samples + nb_samples)] = out

            processed_samples += nb_samples

        _stop.set()
        if len(all_outs) == 1:
            return all_outs[0]
        return all_outs

# -*- coding: utf-8 -*-
'''
General documentation architecture:

Home
Index

- Getting started
    Getting started with the sequential model
    Getting started with the functional api
    Examples
    FAQ
    Installation guide

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
    Core layers
    Convolutional
    Recurrent
    Embeddings
    Normalization
    Advanced activations
    Noise

- Preprocessing
    Image preprocessing
    Text preprocessing
    Sequence preprocessing

Objectives
Optimizers
Activations
Callbacks
Datasets
Backend
Initializations
Regularizers
Constraints
Visualization
Scikit-learn API

'''
from __future__ import print_function
from __future__ import unicode_literals

import re
import inspect
import os
import shutil
import sys
if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding('utf8')

from keras.layers import convolutional
from keras.layers import recurrent
from keras.layers import core
from keras.layers import noise
from keras.layers import normalization
from keras.layers import advanced_activations
from keras.layers import embeddings
from keras.layers import wrappers
from keras import optimizers
from keras import callbacks
from keras import models
from keras.engine import topology
from keras import objectives
from keras import backend
from keras import constraints
from keras import activations
from keras import regularizers

EXCLUDE = {
    'Optimizer',
    'Wrapper',
    'get_session',
    'set_session',
}

PAGES = [
    {
        'page': 'models/sequential.md',
        'functions': [
            models.Sequential.compile,
            models.Sequential.fit,
            models.Sequential.evaluate,
            models.Sequential.predict,
            models.Sequential.predict_classes,
            models.Sequential.predict_proba,
            models.Sequential.train_on_batch,
            models.Sequential.test_on_batch,
            models.Sequential.predict_on_batch,
            models.Sequential.fit_generator,
            models.Sequential.evaluate_generator,
        ],
    },
    {
        'page': 'models/model.md',
        'functions': [
            models.Model.compile,
            models.Model.fit,
            models.Model.evaluate,
            models.Model.predict,
            models.Model.train_on_batch,
            models.Model.test_on_batch,
            models.Model.predict_on_batch,
            models.Model.fit_generator,
            models.Model.evaluate_generator,
            models.Model.get_layer,
        ]
    },
    {
        'page': 'layers/core.md',
        'classes': [
            core.Dense,
            core.Activation,
            core.Dropout,
            core.Flatten,
            core.Reshape,
            core.Permute,
            core.RepeatVector,
            topology.Merge,
            core.Lambda,
            core.ActivityRegularization,
            core.Masking,
            core.Highway,
            core.MaxoutDense,
            core.TimeDistributedDense,
        ],
    },
    {
        'page': 'layers/convolutional.md',
        'classes': [
            convolutional.Convolution1D,
            convolutional.Convolution2D,
            convolutional.Convolution3D,
            convolutional.MaxPooling1D,
            convolutional.MaxPooling2D,
            convolutional.MaxPooling3D,
            convolutional.AveragePooling1D,
            convolutional.AveragePooling2D,
            convolutional.AveragePooling3D,
            convolutional.UpSampling1D,
            convolutional.UpSampling2D,
            convolutional.UpSampling3D,
            convolutional.ZeroPadding1D,
            convolutional.ZeroPadding2D,
            convolutional.ZeroPadding3D,
        ],
    },
    {
        'page': 'layers/recurrent.md',
        'classes': [
            recurrent.Recurrent,
            recurrent.SimpleRNN,
            recurrent.GRU,
            recurrent.LSTM,
        ],
    },
    {
        'page': 'layers/embeddings.md',
        'classes': [
            embeddings.Embedding,
        ],
    },
    {
        'page': 'layers/normalization.md',
        'classes': [
            normalization.BatchNormalization,
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
        'page': 'layers/wrappers.md',
        'all_module_classes': [wrappers],
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
        'page': 'backend.md',
        'all_module_functions': [backend],
    },
]

ROOT = 'http://keras.io/'


def get_earliest_class_that_defined_member(member, cls):
    ancestors = get_classes_ancestors([cls])
    result = None
    for ancestor in ancestors:
        if member in dir(ancestor):
            result = ancestor
    if not result:
        return cls
    return result


def get_classes_ancestors(classes):
    ancestors = []
    for cls in classes:
        ancestors += cls.__bases__
    filtered_ancestors = []
    for ancestor in ancestors:
        if ancestor.__name__ in ['object']:
            continue
        filtered_ancestors.append(ancestor)
    if filtered_ancestors:
        return filtered_ancestors + get_classes_ancestors(filtered_ancestors)
    else:
        return filtered_ancestors


def get_function_signature(function, method=True):
    signature = inspect.getargspec(function)
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
    st = '%s.%s(' % (function.__module__, function.__name__)
    for a in args:
        st += str(a) + ', '
    for a, v in kwargs:
        if type(v) == str:
            v = '\'' + v + '\''
        st += str(a) + '=' + str(v) + ', '
    if kwargs or args:
        return st[:-2] + ')'
    else:
        return st + ')'


def get_class_signature(cls):
    try:
        class_signature = get_function_signature(cls.__init__)
        class_signature = class_signature.replace('__init__', cls.__name__)
    except:
        # in case the class inherits from object and does not
        # define __init__
        class_signature = cls.__module__ + '.' + cls.__name__ + '()'
    return class_signature


def class_to_docs_link(cls):
    module_name = cls.__module__
    assert module_name[:6] == 'keras.'
    module_name = module_name[6:]
    link = ROOT + module_name.replace('.', '/') + '#' + cls.__name__.lower()
    return link


def class_to_source_link(cls):
    module_name = cls.__module__
    assert module_name[:6] == 'keras.'
    path = module_name.replace('.', '/')
    path += '.py'
    line = inspect.getsourcelines(cls)[-1]
    link = 'https://github.com/fchollet/keras/blob/master/' + path + '#L' + str(line)
    return '[[source]](' + link + ')'


def code_snippet(snippet):
    result = '```python\n'
    result += snippet + '\n'
    result += '```\n'
    return result


def process_class_docstring(docstring):
    docstring = re.sub(r'\n    # (.*)\n',
                       r'\n    __\1__\n\n',
                       docstring)

    docstring = re.sub(r'    ([^\s\\]+):(.*)\n',
                       r'    - __\1__:\2\n',
                       docstring)

    docstring = docstring.replace('    ' * 5, '\t\t')
    docstring = docstring.replace('    ' * 3, '\t')
    docstring = docstring.replace('    ', '')
    return docstring


def process_function_docstring(docstring):
    docstring = re.sub(r'\n    # (.*)\n',
                       r'\n    __\1__\n\n',
                       docstring)
    docstring = re.sub(r'\n        # (.*)\n',
                       r'\n        __\1__\n\n',
                       docstring)

    docstring = re.sub(r'    ([^\s\\]+):(.*)\n',
                       r'    - __\1__:\2\n',
                       docstring)

    docstring = docstring.replace('    ' * 6, '\t\t')
    docstring = docstring.replace('    ' * 4, '\t')
    docstring = docstring.replace('    ', '')
    return docstring

print('Cleaning up existing sources directory.')
if os.path.exists('sources'):
    shutil.rmtree('sources')
print('Populating sources directory with templates.')
for subdir, dirs, fnames in os.walk('templates'):
    for fname in fnames:
        new_subdir = subdir.replace('templates', 'sources')
        if not os.path.exists(new_subdir):
            os.makedirs(new_subdir)
        if fname[-3:] == '.md':
            fpath = os.path.join(subdir, fname)
            new_fpath = fpath.replace('templates', 'sources')
            shutil.copy(fpath, new_fpath)

print('Starting autogeneration.')
for page_data in PAGES:
    blocks = []
    classes = page_data.get('classes', [])
    for module in page_data.get('all_module_classes', []):
        module_classes = []
        for name in dir(module):
            if name[0] == '_' or name in EXCLUDE:
                continue
            module_member = getattr(module, name)
            if inspect.isclass(module_member):
                cls = module_member
                if cls.__module__ == module.__name__:
                    if cls not in module_classes:
                        module_classes.append(cls)
        module_classes.sort(key=lambda x: id(x))
        classes += module_classes

    for cls in classes:
        subblocks = []
        signature = get_class_signature(cls)
        subblocks.append('<span style="float:right;">' + class_to_source_link(cls) + '</span>')
        subblocks.append('### ' + cls.__name__ + '\n')
        subblocks.append(code_snippet(signature))
        docstring = cls.__doc__
        if docstring:
            subblocks.append(process_class_docstring(docstring))
        blocks.append('\n'.join(subblocks))

    functions = page_data.get('functions', [])
    for module in page_data.get('all_module_functions', []):
        module_functions = []
        for name in dir(module):
            if name[0] == '_' or name in EXCLUDE:
                continue
            module_member = getattr(module, name)
            if inspect.isfunction(module_member):
                function = module_member
                if module.__name__ in function.__module__:
                    if function not in module_functions:
                        module_functions.append(function)
        module_functions.sort(key=lambda x: id(x))
        functions += module_functions

    for function in functions:
        subblocks = []
        signature = get_function_signature(function, method=False)
        signature = signature.replace(function.__module__ + '.', '')
        subblocks.append('### ' + function.__name__ + '\n')
        subblocks.append(code_snippet(signature))
        docstring = function.__doc__
        if docstring:
            subblocks.append(process_function_docstring(docstring))
            blocks.append('\n\n'.join(subblocks))

    mkdown = '\n----\n\n'.join(blocks)
    # save module page.
    # Either insert content into existing page,
    # or create page otherwise
    page_name = page_data['page']
    path = os.path.join('sources', page_name)
    if os.path.exists(path):
        template = open(path).read()
        assert '{{autogenerated}}' in template, ('Template found for ' + path +
                                                 ' but missing {{autogenerated}} tag.')
        mkdown = template.replace('{{autogenerated}}', mkdown)
        print('...inserting autogenerated content into template:', path)
    else:
        print('...creating new page with autogenerated content:', path)
    subdir = os.path.dirname(path)
    if not os.path.exists(subdir):
        os.makedirs(subdir)
    open(path, 'w').write(mkdown)


# covered_so_far = set()
# for module, module_name in MODULES:
#     class_pages = []
#     for name in dir(module):
#         if name in SKIP:
#             continue
#         if name[0] == '_':
#             continue
#         module_member = getattr(module, name)
#         if module_member in covered_so_far:
#             continue
#         if inspect.isclass(module_member):
#             cls = module_member
#             if cls.__module__ == module_name:

#                 try:
#                     class_signature = get_function_signature(cls.__init__)
#                     class_signature = class_signature.replace('__init__', cls.__name__)
#                 except:
#                     # in case the class inherits from object and does not
#                     # define __init__
#                     class_signature = module_name + '.' + cls.__name__ + '()'

#                 functions = []
#                 functions_not_defined_here = []
#                 for name in dir(cls):
#                     if name in SKIP:
#                         continue
#                     if name[0] == '_':
#                         continue
#                     cls_member = getattr(cls, name)
#                     if inspect.isfunction(cls_member):
#                         function = cls_member
#                         signature = inspect.getargspec(function)
#                         defaults = signature.defaults
#                         args = signature.args[1:]
#                         if defaults:
#                             kwargs = zip(args[-len(defaults):], defaults)
#                             args = args[:-len(defaults)]
#                         else:
#                             kwargs = []

#                         defined_by = get_earliest_class_that_defined_member(function.__name__, cls)
#                         if cls == defined_by:
#                             functions.append(function)
#                         else:
#                             functions_not_defined_here.append((function, defined_by))

#                 blocks = []
#                 blocks.append('<span style="float:right;">' + class_to_source_link(cls) + '</span>')
#                 blocks.append('# ' + cls.__name__ + '\n')
#                 blocks.append(code_snippet(class_signature))
#                 docstring = cls.__doc__
#                 if docstring:
#                     blocks.append(process_class_docstring(docstring))

#                 if cls.__name__ in INCLUDE_functionS_FOR:
#                     if functions or functions_not_defined_here:
#                         blocks.append('### functions\n')
#                         for function in functions:
#                             signature = get_function_signature(function)
#                             signature = signature.replace(module_name + '.', '')
#                             blocks.append(code_snippet(signature))
#                             docstring = function.__doc__
#                             if docstring:
#                                 blocks.append(process_function_docstring(docstring))
#                         for function, defined_by in functions_not_defined_here:
#                             signature = get_function_signature(function)
#                             function_module_name = function.__module__
#                             signature = signature.replace(function_module_name + '.', '')
#                             link = '[' + defined_by.__name__ + '](' + class_to_docs_link(defined_by) + ')'
#                             blocks.append(code_snippet(signature))
#                             blocks.append('Defined by ' + link + '.\n')

#                 mkdown = '\n'.join(blocks)
#                 class_pages.append((id(cls), mkdown))
#                 covered_so_far.add(module_member)

#     class_pages.sort(key=lambda x: x[0])
#     class_pages = [x[1] for x in class_pages]
#     module_page = '\n----\n\n'.join(class_pages)

#     # save module page.
#     # Either insert content into existing page,
#     # or create page otherwise
#     path = 'sources/' + module_name.replace('.', '/')[6:] + '.md'
#     if os.path.exists(path):
#         template = open(path).read()
#         assert '{{autogenerated}}' in template, ('Template found for ' + path +
#                                                  ' but missing {{autogenerated}} tag.')
#         module_page = template.replace('{{autogenerated}}', module_page)
#         print('...inserting autogenerated content into template:', path)
#     else:
#         print('...creating new page with autogenerated content:', path)
#     subdir = os.path.dirname(path)
#     if not os.path.exists(subdir):
#         os.makedirs(subdir)
#     open(path, 'w').write(module_page)

'''Trains a simple deep NN on the MNIST dataset.

Gets to 98.40% test accuracy after 20 epochs
(there is *a lot* of margin for parameter tuning).
2 seconds per epoch on a K520 GPU.
'''

from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.optimizers import SGD, Adam, RMSprop
from keras.utils import np_utils


batch_size = 128
nb_classes = 10
nb_epoch = 20

# the data, shuffled and split between train and test sets
(X_train, y_train), (X_test, y_test) = mnist.load_data()

X_train = X_train.reshape(60000, 784)
X_test = X_test.reshape(10000, 784)
X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
X_train /= 255
X_test /= 255
print(X_train.shape[0], 'train samples')
print(X_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)

model = Sequential()
model.add(Dense(512, input_shape=(784,)))
model.add(Activation('relu'))
model.add(Dropout(0.2))
model.add(Dense(512))
model.add(Activation('relu'))
model.add(Dropout(0.2))
model.add(Dense(10))
model.add(Activation('softmax'))

model.summary()

model.compile(loss='categorical_crossentropy',
              optimizer=RMSprop(),
              metrics=['accuracy'])

history = model.fit(X_train, Y_train,
                    batch_size=batch_size, nb_epoch=nb_epoch,
                    verbose=1, validation_data=(X_test, Y_test))
score = model.evaluate(X_test, Y_test, verbose=0)
print('Test score:', score[0])
print('Test accuracy:', score[1])

'''This is a reproduction of the IRNN experiment
with pixel-by-pixel sequential MNIST in
"A Simple Way to Initialize Recurrent Networks of Rectified Linear Units"
by Quoc V. Le, Navdeep Jaitly, Geoffrey E. Hinton

arXiv:1504.00941v2 [cs.NE] 7 Apr 201
http://arxiv.org/pdf/1504.00941v2.pdf

Optimizer is replaced with RMSprop which yields more stable and steady
improvement.

Reaches 0.93 train/test accuracy after 900 epochs
(which roughly corresponds to 1687500 steps in the original paper.)
'''

from __future__ import print_function

from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Activation
from keras.initializations import normal, identity
from keras.layers.recurrent import SimpleRNN
from keras.optimizers import RMSprop
from keras.utils import np_utils

batch_size = 32
nb_classes = 10
nb_epochs = 200
hidden_units = 100

learning_rate = 1e-6
clip_norm = 1.0

# the data, shuffled and split between train and test sets
(X_train, y_train), (X_test, y_test) = mnist.load_data()

X_train = X_train.reshape(X_train.shape[0], -1, 1)
X_test = X_test.reshape(X_test.shape[0], -1, 1)
X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
X_train /= 255
X_test /= 255
print('X_train shape:', X_train.shape)
print(X_train.shape[0], 'train samples')
print(X_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)

print('Evaluate IRNN...')
model = Sequential()
model.add(SimpleRNN(output_dim=hidden_units,
                    init=lambda shape, name: normal(shape, scale=0.001, name=name),
                    inner_init=lambda shape, name: identity(shape, scale=1.0, name=name),
                    activation='relu',
                    input_shape=X_train.shape[1:]))
model.add(Dense(nb_classes))
model.add(Activation('softmax'))
rmsprop = RMSprop(lr=learning_rate)
model.compile(loss='categorical_crossentropy',
              optimizer=rmsprop,
              metrics=['accuracy'])

model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epochs,
          verbose=1, validation_data=(X_test, Y_test))

scores = model.evaluate(X_test, Y_test, verbose=0)
print('IRNN test score:', scores[0])
print('IRNN test accuracy:', scores[1])

'''Trains a simple convnet on the MNIST dataset.

Gets to 99.25% test accuracy after 12 epochs
(there is still a lot of margin for parameter tuning).
16 seconds per epoch on a GRID K520 GPU.
'''

from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.utils import np_utils

batch_size = 128
nb_classes = 10
nb_epoch = 12

# input image dimensions
img_rows, img_cols = 28, 28
# number of convolutional filters to use
nb_filters = 32
# size of pooling area for max pooling
nb_pool = 2
# convolution kernel size
nb_conv = 3

# the data, shuffled and split between train and test sets
(X_train, y_train), (X_test, y_test) = mnist.load_data()

X_train = X_train.reshape(X_train.shape[0], 1, img_rows, img_cols)
X_test = X_test.reshape(X_test.shape[0], 1, img_rows, img_cols)
X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
X_train /= 255
X_test /= 255
print('X_train shape:', X_train.shape)
print(X_train.shape[0], 'train samples')
print(X_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)

model = Sequential()

model.add(Convolution2D(nb_filters, nb_conv, nb_conv,
                        border_mode='valid',
                        input_shape=(1, img_rows, img_cols)))
model.add(Activation('relu'))
model.add(Convolution2D(nb_filters, nb_conv, nb_conv))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(nb_pool, nb_pool)))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(128))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(nb_classes))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy',
              optimizer='adadelta',
              metrics=['accuracy'])

model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch,
          verbose=1, validation_data=(X_test, Y_test))
score = model.evaluate(X_test, Y_test, verbose=0)
print('Test score:', score[0])
print('Test accuracy:', score[1])

'''Example script to generate text from Nietzsche's writings.

At least 20 epochs are required before the generated text
starts sounding coherent.

It is recommended to run this script on GPU, as recurrent
networks are quite computationally intensive.

If you try this script on new data, make sure your corpus
has at least ~100k characters. ~1M is better.
'''

from __future__ import print_function
from keras.models import Sequential
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.utils.data_utils import get_file
import numpy as np
import random
import sys

path = get_file('nietzsche.txt', origin="https://s3.amazonaws.com/text-datasets/nietzsche.txt")
text = open(path).read().lower()
print('corpus length:', len(text))

chars = set(text)
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
X = np.zeros((len(sentences), maxlen, len(chars)), dtype=np.bool)
y = np.zeros((len(sentences), len(chars)), dtype=np.bool)
for i, sentence in enumerate(sentences):
    for t, char in enumerate(sentence):
        X[i, t, char_indices[char]] = 1
    y[i, char_indices[next_chars[i]]] = 1


# build the model: 2 stacked LSTM
print('Build model...')
model = Sequential()
model.add(LSTM(512, return_sequences=True, input_shape=(maxlen, len(chars))))
model.add(Dropout(0.2))
model.add(LSTM(512, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(len(chars)))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy', optimizer='rmsprop')


def sample(a, temperature=1.0):
    # helper function to sample an index from a probability array
    a = np.log(a) / temperature
    a = np.exp(a) / np.sum(np.exp(a))
    return np.argmax(np.random.multinomial(1, a, 1))

# train the model, output generated text after each iteration
for iteration in range(1, 60):
    print()
    print('-' * 50)
    print('Iteration', iteration)
    model.fit(X, y, batch_size=128, nb_epoch=1)

    start_index = random.randint(0, len(text) - maxlen - 1)

    for diversity in [0.2, 0.5, 1.0, 1.2]:
        print()
        print('----- diversity:', diversity)

        generated = ''
        sentence = text[start_index: start_index + maxlen]
        generated += sentence
        print('----- Generating with seed: "' + sentence + '"')
        sys.stdout.write(generated)

        for i in range(400):
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

'''This example demonstrates the use of Convolution1D for text classification.

Gets to 0.88 test accuracy after 2 epochs. 
90s/epoch on Intel i5 2.4Ghz CPU.
10s/epoch on Tesla K40 GPU.

'''

from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Lambda
from keras.layers.embeddings import Embedding
from keras.layers.convolutional import Convolution1D
from keras.datasets import imdb
from keras import backend as K


# set parameters:
max_features = 5000
maxlen = 400
batch_size = 32
embedding_dims = 50
nb_filter = 250
filter_length = 3
hidden_dims = 250
nb_epoch = 2

print('Loading data...')
(X_train, y_train), (X_test, y_test) = imdb.load_data(nb_words=max_features,
                                                      test_split=0.2)
print(len(X_train), 'train sequences')
print(len(X_test), 'test sequences')

print('Pad sequences (samples x time)')
X_train = sequence.pad_sequences(X_train, maxlen=maxlen)
X_test = sequence.pad_sequences(X_test, maxlen=maxlen)
print('X_train shape:', X_train.shape)
print('X_test shape:', X_test.shape)

print('Build model...')
model = Sequential()

# we start off with an efficient embedding layer which maps
# our vocab indices into embedding_dims dimensions
model.add(Embedding(max_features,
                    embedding_dims,
                    input_length=maxlen,
                    dropout=0.2))

# we add a Convolution1D, which will learn nb_filter
# word group filters of size filter_length:
model.add(Convolution1D(nb_filter=nb_filter,
                        filter_length=filter_length,
                        border_mode='valid',
                        activation='relu',
                        subsample_length=1))

# we use max over time pooling by defining a python function to use
# in a Lambda layer
def max_1d(X):
    return K.max(X, axis=1)

model.add(Lambda(max_1d, output_shape=(nb_filter,)))

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
model.fit(X_train, y_train,
          batch_size=batch_size,
          nb_epoch=nb_epoch,
          validation_data=(X_test, y_test))

'''Trains a LSTM on the IMDB sentiment classification task.

The dataset is actually too small for LSTM to be of any advantage
compared to simpler, much faster methods such as TF-IDF+LogReg.

Notes:

- RNNs are tricky. Choice of batch size is important,
choice of loss and optimizer is critical, etc.
Some configurations won't converge.

- LSTM loss decrease patterns during training can be quite different
from what you see with CNNs/MLPs/etc.
'''
from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.preprocessing import sequence
from keras.utils import np_utils
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM, SimpleRNN, GRU
from keras.datasets import imdb

max_features = 20000
maxlen = 80  # cut texts after this number of words (among top max_features most common words)
batch_size = 32

print('Loading data...')
(X_train, y_train), (X_test, y_test) = imdb.load_data(nb_words=max_features,
                                                      test_split=0.2)
print(len(X_train), 'train sequences')
print(len(X_test), 'test sequences')

print('Pad sequences (samples x time)')
X_train = sequence.pad_sequences(X_train, maxlen=maxlen)
X_test = sequence.pad_sequences(X_test, maxlen=maxlen)
print('X_train shape:', X_train.shape)
print('X_test shape:', X_test.shape)

print('Build model...')
model = Sequential()
model.add(Embedding(max_features, 128, input_length=maxlen, dropout=0.2))
model.add(LSTM(128, dropout_W=0.2, dropout_U=0.2))  # try using a GRU instead, for fun
model.add(Dense(1))
model.add(Activation('sigmoid'))

# try using different optimizers and different optimizer configs
model.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

print('Train...')
print(X_train.shape)
print(y_train.shape)
model.fit(X_train, y_train, batch_size=batch_size, nb_epoch=15,
          validation_data=(X_test, y_test))
score, acc = model.evaluate(X_test, y_test,
                            batch_size=batch_size)
print('Test score:', score)
print('Test accuracy:', acc)

'''Train a Bidirectional LSTM on the IMDB sentiment classification task.

Output after 4 epochs on CPU: ~0.8146
Time per epoch on CPU (Core i7): ~150s.
'''

from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.preprocessing import sequence
from keras.models import Model
from keras.layers import Dense, Dropout, Embedding, LSTM, Input, merge
from keras.datasets import imdb


max_features = 20000
maxlen = 100  # cut texts after this number of words (among top max_features most common words)
batch_size = 32

print('Loading data...')
(X_train, y_train), (X_test, y_test) = imdb.load_data(nb_words=max_features,
                                                      test_split=0.2)
print(len(X_train), 'train sequences')
print(len(X_test), 'test sequences')

print("Pad sequences (samples x time)")
X_train = sequence.pad_sequences(X_train, maxlen=maxlen)
X_test = sequence.pad_sequences(X_test, maxlen=maxlen)
print('X_train shape:', X_train.shape)
print('X_test shape:', X_test.shape)
y_train = np.array(y_train)
y_test = np.array(y_test)


# this is the placeholder tensor for the input sequences
sequence = Input(shape=(maxlen,), dtype='int32')
# this embedding layer will transform the sequences of integers
# into vectors of size 128
embedded = Embedding(max_features, 128, input_length=maxlen)(sequence)

# apply forwards LSTM
forwards = LSTM(64)(embedded)
# apply backwards LSTM
backwards = LSTM(64, go_backwards=True)(embedded)

# concatenate the outputs of the 2 LSTMs
merged = merge([forwards, backwards], mode='concat', concat_axis=-1)
after_dp = Dropout(0.5)(merged)
output = Dense(1, activation='sigmoid')(after_dp)

model = Model(input=sequence, output=output)

# try using different optimizers and different optimizer configs
model.compile('adam', 'binary_crossentropy', metrics=['accuracy'])

print('Train...')
model.fit(X_train, y_train,
          batch_size=batch_size,
          nb_epoch=4,
          validation_data=[X_test, y_test])

'''Example of how to use sklearn wrapper

Builds simple CNN models on MNIST and uses sklearn's GridSearchCV to find best model
'''

from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.utils import np_utils
from keras.wrappers.scikit_learn import KerasClassifier
from sklearn.grid_search import GridSearchCV


nb_classes = 10

# input image dimensions
img_rows, img_cols = 28, 28

# load training data and do basic data normalization
(X_train, y_train), (X_test, y_test) = mnist.load_data()
X_train = X_train.reshape(X_train.shape[0], 1, img_rows, img_cols)
X_test = X_test.reshape(X_test.shape[0], 1, img_rows, img_cols)
X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
X_train /= 255
X_test /= 255

# convert class vectors to binary class matrices
y_train = np_utils.to_categorical(y_train, nb_classes)
y_test = np_utils.to_categorical(y_test, nb_classes)

def make_model(dense_layer_sizes, nb_filters, nb_conv, nb_pool):
    '''Creates model comprised of 2 convolutional layers followed by dense layers

    dense_layer_sizes: List of layer sizes. This list has one number for each layer
    nb_filters: Number of convolutional filters in each convolutional layer
    nb_conv: Convolutional kernel size
    nb_pool: Size of pooling area for max pooling
    '''

    model = Sequential()

    model.add(Convolution2D(nb_filters, nb_conv, nb_conv,
                            border_mode='valid',
                            input_shape=(1, img_rows, img_cols)))
    model.add(Activation('relu'))
    model.add(Convolution2D(nb_filters, nb_conv, nb_conv))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size=(nb_pool, nb_pool)))
    model.add(Dropout(0.25))

    model.add(Flatten())
    for layer_size in dense_layer_sizes:
        model.add(Dense(layer_size))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))
    model.add(Dense(nb_classes))
    model.add(Activation('softmax'))

    model.compile(loss='categorical_crossentropy',
                  optimizer='adadelta',
                  metrics=['accuracy'])

    return model

dense_size_candidates = [[32], [64], [32, 32], [64, 64]]
my_classifier = KerasClassifier(make_model, batch_size=32)
validator = GridSearchCV(my_classifier,
                         param_grid={'dense_layer_sizes': dense_size_candidates,
                                     # nb_epoch is avail for tuning even when not
                                     # an argument to model building function
                                     'nb_epoch': [3, 6],
                                     'nb_filters': [8],
                                     'nb_conv': [3],
                                     'nb_pool': [2]},
                         scoring='log_loss',
                         n_jobs=1)
validator.fit(X_train, y_train)

print('The parameters of the best model are: ')
print(validator.best_params_)

# validator.best_estimator_ returns sklearn-wrapped version of best model.
# validator.best_estimator_.model returns the (unwrapped) keras model
best_model = validator.best_estimator_.model
metric_names = best_model.metrics_names
metric_values = best_model.evaluate(X_test, y_test)
for metric, value in zip(metric_names, metric_values):
    print(metric, ': ', value)

'''Trains two recurrent neural networks based upon a story and a question.
The resulting merged vector is then queried to answer a range of bAbI tasks.

The results are comparable to those for an LSTM model provided in Weston et al.:
"Towards AI-Complete Question Answering: A Set of Prerequisite Toy Tasks"
http://arxiv.org/abs/1502.05698

Task Number                  | FB LSTM Baseline | Keras QA
---                          | ---              | ---
QA1 - Single Supporting Fact | 50               | 100.0
QA2 - Two Supporting Facts   | 20               | 50.0
QA3 - Three Supporting Facts | 20               | 20.5
QA4 - Two Arg. Relations     | 61               | 62.9
QA5 - Three Arg. Relations   | 70               | 61.9
QA6 - Yes/No Questions       | 48               | 50.7
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

Notes:

- With default word, sentence, and query vector sizes, the GRU model achieves:
  - 100% test accuracy on QA1 in 20 epochs (2 seconds per epoch on CPU)
  - 50% test accuracy on QA2 in 20 epochs (16 seconds per epoch on CPU)
In comparison, the Facebook paper achieves 50% and 20% for the LSTM baseline.

- The task does not traditionally parse the question separately. This likely
improves accuracy and is a good example of merging two RNNs.

- The word vector embeddings are not shared between the story and question RNNs.

- See how the accuracy changes given 10,000 training samples (en-10k) instead
of only 1000. 1000 was used in order to be comparable to the original paper.

- Experiment with GRU, LSTM, and JZS1-3 as they give subtly different results.

- The length and noise (i.e. 'useless' story components) impact the ability for
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
np.random.seed(1337)  # for reproducibility

from keras.utils.data_utils import get_file
from keras.layers.embeddings import Embedding
from keras.layers.core import Dense, Merge, Dropout, RepeatVector
from keras.layers import recurrent
from keras.models import Sequential
from keras.preprocessing.sequence import pad_sequences


def tokenize(sent):
    '''Return the tokens of a sentence including punctuation.

    >>> tokenize('Bob dropped the apple. Where is the apple?')
    ['Bob', 'dropped', 'the', 'apple', '.', 'Where', 'is', 'the', 'apple', '?']
    '''
    return [x.strip() for x in re.split('(\W+)?', sent) if x.strip()]


def parse_stories(lines, only_supporting=False):
    '''Parse stories provided in the bAbi tasks format

    If only_supporting is true, only the sentences that support the answer are kept.
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
            substory = None
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
    '''Given a file name, read the file, retrieve the stories, and then convert the sentences into a single story.

    If max_length is supplied, any stories longer than max_length tokens will be discarded.
    '''
    data = parse_stories(f.readlines(), only_supporting=only_supporting)
    flatten = lambda data: reduce(lambda x, y: x + y, data)
    data = [(flatten(story), q, answer) for story, q, answer in data if not max_length or len(flatten(story)) < max_length]
    return data


def vectorize_stories(data, word_idx, story_maxlen, query_maxlen):
    X = []
    Xq = []
    Y = []
    for story, query, answer in data:
        x = [word_idx[w] for w in story]
        xq = [word_idx[w] for w in query]
        y = np.zeros(len(word_idx) + 1)  # let's not forget that index 0 is reserved
        y[word_idx[answer]] = 1
        X.append(x)
        Xq.append(xq)
        Y.append(y)
    return pad_sequences(X, maxlen=story_maxlen), pad_sequences(Xq, maxlen=query_maxlen), np.array(Y)

RNN = recurrent.LSTM
EMBED_HIDDEN_SIZE = 50
SENT_HIDDEN_SIZE = 100
QUERY_HIDDEN_SIZE = 100
BATCH_SIZE = 32
EPOCHS = 40
print('RNN / Embed / Sent / Query = {}, {}, {}, {}'.format(RNN, EMBED_HIDDEN_SIZE, SENT_HIDDEN_SIZE, QUERY_HIDDEN_SIZE))

path = get_file('babi-tasks-v1-2.tar.gz', origin='http://www.thespermwhale.com/jaseweston/babi/tasks_1-20_v1-2.tar.gz')
tar = tarfile.open(path)
# Default QA1 with 1000 samples
# challenge = 'tasks_1-20_v1-2/en/qa1_single-supporting-fact_{}.txt'
# QA1 with 10,000 samples
# challenge = 'tasks_1-20_v1-2/en-10k/qa1_single-supporting-fact_{}.txt'
# QA2 with 1000 samples
challenge = 'tasks_1-20_v1-2/en/qa2_two-supporting-facts_{}.txt'
# QA2 with 10,000 samples
# challenge = 'tasks_1-20_v1-2/en-10k/qa2_two-supporting-facts_{}.txt'
train = get_stories(tar.extractfile(challenge.format('train')))
test = get_stories(tar.extractfile(challenge.format('test')))

vocab = sorted(reduce(lambda x, y: x | y, (set(story + q + [answer]) for story, q, answer in train + test)))
# Reserve 0 for masking via pad_sequences
vocab_size = len(vocab) + 1
word_idx = dict((c, i + 1) for i, c in enumerate(vocab))
story_maxlen = max(map(len, (x for x, _, _ in train + test)))
query_maxlen = max(map(len, (x for _, x, _ in train + test)))

X, Xq, Y = vectorize_stories(train, word_idx, story_maxlen, query_maxlen)
tX, tXq, tY = vectorize_stories(test, word_idx, story_maxlen, query_maxlen)

print('vocab = {}'.format(vocab))
print('X.shape = {}'.format(X.shape))
print('Xq.shape = {}'.format(Xq.shape))
print('Y.shape = {}'.format(Y.shape))
print('story_maxlen, query_maxlen = {}, {}'.format(story_maxlen, query_maxlen))

print('Build model...')

sentrnn = Sequential()
sentrnn.add(Embedding(vocab_size, EMBED_HIDDEN_SIZE,
                      input_length=story_maxlen))
sentrnn.add(Dropout(0.3))

qrnn = Sequential()
qrnn.add(Embedding(vocab_size, EMBED_HIDDEN_SIZE,
                   input_length=query_maxlen))
qrnn.add(Dropout(0.3))
qrnn.add(RNN(EMBED_HIDDEN_SIZE, return_sequences=False))
qrnn.add(RepeatVector(story_maxlen))

model = Sequential()
model.add(Merge([sentrnn, qrnn], mode='sum'))
model.add(RNN(EMBED_HIDDEN_SIZE, return_sequences=False))
model.add(Dropout(0.3))
model.add(Dense(vocab_size, activation='softmax'))

model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

print('Training')
model.fit([X, Xq], Y, batch_size=BATCH_SIZE, nb_epoch=EPOCHS, validation_split=0.05)
loss, acc = model.evaluate([tX, tXq], tY, batch_size=BATCH_SIZE)
print('Test loss / test accuracy = {:.4f} / {:.4f}'.format(loss, acc))

'''The example demonstrates how to write custom layers for Keras.

We build a custom activation layer called 'Antirectifier',
which modifies the shape of the tensor that passes through it.
We need to specify two methods: `get_output_shape_for` and `call`.

Note that the same result can also be achieved via a Lambda layer.

Because our custom layer is written with primitives from the Keras
backend (`K`), our code can run both on TensorFlow and Theano.
'''

from __future__ import print_function
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Layer, Activation
from keras.datasets import mnist
from keras import backend as K
from keras.utils import np_utils


class Antirectifier(Layer):
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
    def get_output_shape_for(self, input_shape):
        shape = list(input_shape)
        assert len(shape) == 2  # only valid for 2D tensors
        shape[-1] *= 2
        return tuple(shape)

    def call(self, x, mask=None):
        x -= K.mean(x, axis=1, keepdims=True)
        x = K.l2_normalize(x, axis=1)
        pos = K.relu(x)
        neg = K.relu(-x)
        return K.concatenate([pos, neg], axis=1)

# global parameters
batch_size = 128
nb_classes = 10
nb_epoch = 40

# the data, shuffled and split between train and test sets
(X_train, y_train), (X_test, y_test) = mnist.load_data()

X_train = X_train.reshape(60000, 784)
X_test = X_test.reshape(10000, 784)
X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
X_train /= 255
X_test /= 255
print(X_train.shape[0], 'train samples')
print(X_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)

# build the model
model = Sequential()
model.add(Dense(256, input_shape=(784,)))
model.add(Antirectifier())
model.add(Dropout(0.1))
model.add(Dense(256))
model.add(Antirectifier())
model.add(Dropout(0.1))
model.add(Dense(10))
model.add(Activation('softmax'))

# compile the model
model.compile(loss='categorical_crossentropy',
              optimizer='rmsprop',
              metrics=['accuracy'])

# train the model
model.fit(X_train, Y_train,
          batch_size=batch_size, nb_epoch=nb_epoch,
          verbose=1, validation_data=(X_test, Y_test))

# next, compare with an equivalent network
# with2x bigger Dense layers and ReLU

'''This script demonstrates how to build the Inception v3 architecture
using the Keras functional API.
We are not actually training it here, for lack of appropriate data.

For more information about this architecture, see:

"Rethinking the Inception Architecture for Computer Vision"
Christian Szegedy, Vincent Vanhoucke, Sergey Ioffe, Jonathon Shlens, Zbigniew Wojna
http://arxiv.org/abs/1512.00567
'''
from keras.layers import Convolution2D, MaxPooling2D, AveragePooling2D
from keras.layers import BatchNormalization, Flatten, Dense, Dropout
from keras.layers import Input, merge
from keras.models import Model
from keras import regularizers


# global constants
NB_CLASS = 1000  # number of classes
DIM_ORDERING = 'th'  # 'th' (channels, width, height) or 'tf' (width, height, channels)
WEIGHT_DECAY = 0.  # L2 regularization factor
USE_BN = False  # whether to use batch normalization


def conv2D_bn(x, nb_filter, nb_row, nb_col,
              border_mode='same', subsample=(1, 1),
              activation='relu', batch_norm=USE_BN,
              weight_decay=WEIGHT_DECAY, dim_ordering=DIM_ORDERING):
    '''Utility function to apply to a tensor a module conv + BN
    with optional weight decay (L2 weight regularization).
    '''
    if weight_decay:
        W_regularizer = regularizers.l2(weight_decay)
        b_regularizer = regularizers.l2(weight_decay)
    else:
        W_regularizer = None
        b_regularizer = None
    x = Convolution2D(nb_filter, nb_row, nb_col,
                      subsample=subsample,
                      activation=activation,
                      border_mode=border_mode,
                      W_regularizer=W_regularizer,
                      b_regularizer=b_regularizer,
                      dim_ordering=dim_ordering)(x)
    if batch_norm:
        x = BatchNormalization()(x)
    return x

# Define image input layer

if DIM_ORDERING == 'th':
    img_input = Input(shape=(3, 299, 299))
    CONCAT_AXIS = 1
elif DIM_ORDERING == 'tf':
    img_input = Input(shape=(299, 299, 3))
    CONCAT_AXIS = 3
else:
    raise Exception('Invalid dim ordering: ' + str(DIM_ORDERING))

# Entry module

x = conv2D_bn(img_input, 32, 3, 3, subsample=(2, 2), border_mode='valid')
x = conv2D_bn(x, 32, 3, 3, border_mode='valid')
x = conv2D_bn(x, 64, 3, 3)
x = MaxPooling2D((3, 3), strides=(2, 2), dim_ordering=DIM_ORDERING)(x)

x = conv2D_bn(x, 80, 1, 1, border_mode='valid')
x = conv2D_bn(x, 192, 3, 3, border_mode='valid')
x = MaxPooling2D((3, 3), strides=(2, 2), dim_ordering=DIM_ORDERING)(x)

# mixed: 35 x 35 x 256

branch1x1 = conv2D_bn(x, 64, 1, 1)

branch5x5 = conv2D_bn(x, 48, 1, 1)
branch5x5 = conv2D_bn(branch5x5, 64, 5, 5)

branch3x3dbl = conv2D_bn(x, 64, 1, 1)
branch3x3dbl = conv2D_bn(branch3x3dbl, 96, 3, 3)
branch3x3dbl = conv2D_bn(branch3x3dbl, 96, 3, 3)

branch_pool = AveragePooling2D((3, 3), strides=(1, 1), border_mode='same', dim_ordering=DIM_ORDERING)(x)
branch_pool = conv2D_bn(branch_pool, 32, 1, 1)
x = merge([branch1x1, branch5x5, branch3x3dbl, branch_pool], mode='concat', concat_axis=CONCAT_AXIS)

# mixed_1: 35 x 35 x 288

branch1x1 = conv2D_bn(x, 64, 1, 1)

branch5x5 = conv2D_bn(x, 48, 1, 1)
branch5x5 = conv2D_bn(branch5x5, 64, 5, 5)

branch3x3dbl = conv2D_bn(x, 64, 1, 1)
branch3x3dbl = conv2D_bn(branch3x3dbl, 96, 3, 3)
branch3x3dbl = conv2D_bn(branch3x3dbl, 96, 3, 3)

branch_pool = AveragePooling2D((3, 3), strides=(1, 1), border_mode='same', dim_ordering=DIM_ORDERING)(x)
branch_pool = conv2D_bn(branch_pool, 64, 1, 1)
x = merge([branch1x1, branch5x5, branch3x3dbl, branch_pool], mode='concat', concat_axis=CONCAT_AXIS)

# mixed2: 35 x 35 x 288

branch1x1 = conv2D_bn(x, 64, 1, 1)

branch5x5 = conv2D_bn(x, 48, 1, 1)
branch5x5 = conv2D_bn(branch5x5, 64, 5, 5)

branch3x3dbl = conv2D_bn(x, 64, 1, 1)
branch3x3dbl = conv2D_bn(branch3x3dbl, 96, 3, 3)
branch3x3dbl = conv2D_bn(branch3x3dbl, 96, 3, 3)

branch_pool = AveragePooling2D((3, 3), strides=(1, 1), border_mode='same', dim_ordering=DIM_ORDERING)(x)
branch_pool = conv2D_bn(branch_pool, 64, 1, 1)
x = merge([branch1x1, branch5x5, branch3x3dbl, branch_pool], mode='concat', concat_axis=CONCAT_AXIS)

# mixed3: 17 x 17 x 768

branch3x3 = conv2D_bn(x, 384, 3, 3, subsample=(2, 2), border_mode='valid')

branch3x3dbl = conv2D_bn(x, 64, 1, 1)
branch3x3dbl = conv2D_bn(branch3x3dbl, 96, 3, 3)
branch3x3dbl = conv2D_bn(branch3x3dbl, 96, 3, 3, subsample=(2, 2), border_mode='valid')

branch_pool = MaxPooling2D((3, 3), strides=(2, 2), dim_ordering=DIM_ORDERING)(x)
x = merge([branch3x3, branch3x3dbl, branch_pool], mode='concat', concat_axis=CONCAT_AXIS)

# mixed4: 17 x 17 x 768

branch1x1 = conv2D_bn(x, 192, 1, 1)

branch7x7 = conv2D_bn(x, 128, 1, 1)
branch7x7 = conv2D_bn(branch7x7, 128, 1, 7)
branch7x7 = conv2D_bn(branch7x7, 192, 7, 1)

branch7x7dbl = conv2D_bn(x, 128, 1, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 128, 7, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 128, 1, 7)
branch7x7dbl = conv2D_bn(branch7x7dbl, 128, 7, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 192, 1, 7)

branch_pool = AveragePooling2D((3, 3), strides=(1, 1), border_mode='same', dim_ordering=DIM_ORDERING)(x)
branch_pool = conv2D_bn(branch_pool, 192, 1, 1)
x = merge([branch1x1, branch7x7, branch7x7dbl, branch_pool], mode='concat', concat_axis=CONCAT_AXIS)

# mixed5: 17 x 17 x 768

branch1x1 = conv2D_bn(x, 192, 1, 1)

branch7x7 = conv2D_bn(x, 160, 1, 1)
branch7x7 = conv2D_bn(branch7x7, 160, 1, 7)
branch7x7 = conv2D_bn(branch7x7, 192, 7, 1)

branch7x7dbl = conv2D_bn(x, 160, 1, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 160, 7, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 160, 1, 7)
branch7x7dbl = conv2D_bn(branch7x7dbl, 160, 7, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 192, 1, 7)

branch_pool = AveragePooling2D((3, 3), strides=(1, 1), border_mode='same', dim_ordering=DIM_ORDERING)(x)
branch_pool = conv2D_bn(branch_pool, 192, 1, 1)
x = merge([branch1x1, branch7x7, branch7x7dbl, branch_pool], mode='concat', concat_axis=CONCAT_AXIS)

# mixed5: 17 x 17 x 768

branch1x1 = conv2D_bn(x, 192, 1, 1)

branch7x7 = conv2D_bn(x, 160, 1, 1)
branch7x7 = conv2D_bn(branch7x7, 160, 1, 7)
branch7x7 = conv2D_bn(branch7x7, 192, 7, 1)

branch7x7dbl = conv2D_bn(x, 160, 1, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 160, 7, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 160, 1, 7)
branch7x7dbl = conv2D_bn(branch7x7dbl, 160, 7, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 192, 1, 7)

branch_pool = AveragePooling2D((3, 3), strides=(1, 1), border_mode='same', dim_ordering=DIM_ORDERING)(x)
branch_pool = conv2D_bn(branch_pool, 192, 1, 1)
x = merge([branch1x1, branch7x7, branch7x7dbl, branch_pool], mode='concat', concat_axis=CONCAT_AXIS)

# mixed6: 17 x 17 x 768

branch1x1 = conv2D_bn(x, 192, 1, 1)

branch7x7 = conv2D_bn(x, 160, 1, 1)
branch7x7 = conv2D_bn(branch7x7, 160, 1, 7)
branch7x7 = conv2D_bn(branch7x7, 192, 7, 1)

branch7x7dbl = conv2D_bn(x, 160, 1, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 160, 7, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 192, 1, 7)
branch7x7dbl = conv2D_bn(branch7x7dbl, 160, 7, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 192, 1, 7)

branch_pool = AveragePooling2D((3, 3), strides=(1, 1), border_mode='same', dim_ordering=DIM_ORDERING)(x)
branch_pool = conv2D_bn(branch_pool, 192, 1, 1)
x = merge([branch1x1, branch7x7, branch7x7dbl, branch_pool], mode='concat', concat_axis=CONCAT_AXIS)

# mixed7: 17 x 17 x 768

branch1x1 = conv2D_bn(x, 192, 1, 1)

branch7x7 = conv2D_bn(x, 192, 1, 1)
branch7x7 = conv2D_bn(branch7x7, 192, 1, 7)
branch7x7 = conv2D_bn(branch7x7, 192, 7, 1)

branch7x7dbl = conv2D_bn(x, 160, 1, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 192, 7, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 192, 1, 7)
branch7x7dbl = conv2D_bn(branch7x7dbl, 192, 7, 1)
branch7x7dbl = conv2D_bn(branch7x7dbl, 192, 1, 7)

branch_pool = AveragePooling2D((3, 3), strides=(1, 1), border_mode='same', dim_ordering=DIM_ORDERING)(x)
branch_pool = conv2D_bn(branch_pool, 192, 1, 1)
x = merge([branch1x1, branch7x7, branch7x7dbl, branch_pool], mode='concat', concat_axis=CONCAT_AXIS)

# Auxiliary head

aux_logits = AveragePooling2D((5, 5), strides=(3, 3), dim_ordering=DIM_ORDERING)(x)
aux_logits = conv2D_bn(aux_logits, 128, 1, 1)
aux_logits = conv2D_bn(aux_logits, 728, 5, 5, border_mode='valid')
aux_logits = Flatten()(aux_logits)
aux_preds = Dense(NB_CLASS, activation='softmax')(aux_logits)

# mixed8: 8 x 8 x 1280

branch3x3 = conv2D_bn(x, 192, 1, 1)
branch3x3 = conv2D_bn(branch3x3, 320, 3, 3, subsample=(2, 2), border_mode='valid')

branch7x7x3 = conv2D_bn(x, 192, 1, 1)
branch7x7x3 = conv2D_bn(branch7x7x3, 192, 1, 7)
branch7x7x3 = conv2D_bn(branch7x7x3, 192, 7, 1)
branch7x7x3 = conv2D_bn(branch7x7x3, 192, 3, 3, subsample=(2, 2), border_mode='valid')

branch_pool = AveragePooling2D((3, 3), strides=(2, 2), dim_ordering=DIM_ORDERING)(x)
x = merge([branch3x3, branch7x7x3, branch_pool], mode='concat', concat_axis=CONCAT_AXIS)

# mixed9: 8 x 8 x 2048

branch1x1 = conv2D_bn(x, 320, 1, 1)

branch3x3 = conv2D_bn(x, 384, 1, 1)
branch3x3_1 = conv2D_bn(branch3x3, 384, 1, 3)
branch3x3_2 = conv2D_bn(branch3x3, 384, 3, 1)
branch3x3 = merge([branch3x3_1, branch3x3_2], mode='concat', concat_axis=CONCAT_AXIS)

branch3x3dbl = conv2D_bn(x, 448, 1, 1)
branch3x3dbl = conv2D_bn(branch3x3dbl, 384, 3, 3)
branch3x3dbl_1 = conv2D_bn(branch3x3dbl, 384, 1, 3)
branch3x3dbl_2 = conv2D_bn(branch3x3dbl, 384, 3, 1)
branch3x3dbl = merge([branch3x3dbl_1, branch3x3dbl_2], mode='concat', concat_axis=CONCAT_AXIS)

branch_pool = AveragePooling2D((3, 3), strides=(1, 1), border_mode='same', dim_ordering=DIM_ORDERING)(x)
branch_pool = conv2D_bn(branch_pool, 192, 1, 1)
x = merge([branch1x1, branch3x3, branch3x3dbl, branch_pool], mode='concat', concat_axis=CONCAT_AXIS)

# mixed10: 8 x 8 x 2048

branch1x1 = conv2D_bn(x, 320, 1, 1)

branch3x3 = conv2D_bn(x, 384, 1, 1)
branch3x3_1 = conv2D_bn(branch3x3, 384, 1, 3)
branch3x3_2 = conv2D_bn(branch3x3, 384, 3, 1)
branch3x3 = merge([branch3x3_1, branch3x3_2], mode='concat', concat_axis=CONCAT_AXIS)

branch3x3dbl = conv2D_bn(x, 448, 1, 1)
branch3x3dbl = conv2D_bn(branch3x3dbl, 384, 3, 3)
branch3x3dbl_1 = conv2D_bn(branch3x3dbl, 384, 1, 3)
branch3x3dbl_2 = conv2D_bn(branch3x3dbl, 384, 3, 1)
branch3x3dbl = merge([branch3x3dbl_1, branch3x3dbl_2], mode='concat', concat_axis=CONCAT_AXIS)

branch_pool = AveragePooling2D((3, 3), strides=(1, 1), border_mode='same', dim_ordering=DIM_ORDERING)(x)
branch_pool = conv2D_bn(branch_pool, 192, 1, 1)
x = merge([branch1x1, branch3x3, branch3x3dbl, branch_pool], mode='concat', concat_axis=CONCAT_AXIS)

# Final pooling and prediction

x = AveragePooling2D((8, 8), strides=(1, 1), dim_ordering=DIM_ORDERING)(x)
x = Dropout(0.5)(x)
x = Flatten()(x)
preds = Dense(NB_CLASS, activation='softmax')(x)

# Define model

model = Model(input=img_input, output=[preds, aux_preds])
model.compile('rmsprop', 'categorical_crossentropy')

# train via e.g. `model.fit(x_train, [y_train] * 2, batch_size=32, nb_epoch=100)`
# Note that for a large dataset it would be preferable
# to train using `fit_generator` (see Keras docs).

'''Train a Siamese MLP on pairs of digits from the MNIST dataset.

It follows Hadsell-et-al.'06 [1] by computing the Euclidean distance on the
output of the shared network and by optimizing the contrastive loss (see paper
for mode details).

[1] "Dimensionality Reduction by Learning an Invariant Mapping"
    http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf

Gets to 99.5% test accuracy after 20 epochs.
3 seconds per epoch on a Titan X GPU
'''
from __future__ import absolute_import
from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

import random
from keras.datasets import mnist
from keras.models import Sequential, Model
from keras.layers import Dense, Dropout, Input, Lambda
from keras.optimizers import SGD, RMSprop
from keras import backend as K


def euclidean_distance(vects):
    x, y = vects
    return K.sqrt(K.sum(K.square(x - y), axis=1, keepdims=True))


def eucl_dist_output_shape(shapes):
    shape1, shape2 = shapes
    return shape1


def contrastive_loss(y_true, y_pred):
    '''Contrastive loss from Hadsell-et-al.'06
    http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf
    '''
    margin = 1
    return K.mean(y_true * K.square(y_pred) + (1 - y_true) * K.square(K.maximum(margin - y_pred, 0)))


def create_pairs(x, digit_indices):
    '''Positive and negative pair creation.
    Alternates between positive and negative pairs.
    '''
    pairs = []
    labels = []
    n = min([len(digit_indices[d]) for d in range(10)]) - 1
    for d in range(10):
        for i in range(n):
            z1, z2 = digit_indices[d][i], digit_indices[d][i+1]
            pairs += [[x[z1], x[z2]]]
            inc = random.randrange(1, 10)
            dn = (d + inc) % 10
            z1, z2 = digit_indices[d][i], digit_indices[dn][i]
            pairs += [[x[z1], x[z2]]]
            labels += [1, 0]
    return np.array(pairs), np.array(labels)


def create_base_network(input_dim):
    '''Base network to be shared (eq. to feature extraction).
    '''
    seq = Sequential()
    seq.add(Dense(128, input_shape=(input_dim,), activation='relu'))
    seq.add(Dropout(0.1))
    seq.add(Dense(128, activation='relu'))
    seq.add(Dropout(0.1))
    seq.add(Dense(128, activation='relu'))
    return seq


def compute_accuracy(predictions, labels):
    '''Compute classification accuracy with a fixed threshold on distances.
    '''
    return labels[predictions.ravel() < 0.5].mean()


# the data, shuffled and split between train and test sets
(X_train, y_train), (X_test, y_test) = mnist.load_data()
X_train = X_train.reshape(60000, 784)
X_test = X_test.reshape(10000, 784)
X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
X_train /= 255
X_test /= 255
input_dim = 784
nb_epoch = 20

# create training+test positive and negative pairs
digit_indices = [np.where(y_train == i)[0] for i in range(10)]
tr_pairs, tr_y = create_pairs(X_train, digit_indices)

digit_indices = [np.where(y_test == i)[0] for i in range(10)]
te_pairs, te_y = create_pairs(X_test, digit_indices)

# network definition
base_network = create_base_network(input_dim)

input_a = Input(shape=(input_dim,))
input_b = Input(shape=(input_dim,))

# because we re-use the same instance `base_network`,
# the weights of the network
# will be shared across the two branches
processed_a = base_network(input_a)
processed_b = base_network(input_b)

distance = Lambda(euclidean_distance, output_shape=eucl_dist_output_shape)([processed_a, processed_b])

model = Model(input=[input_a, input_b], output=distance)

# train
rms = RMSprop()
model.compile(loss=contrastive_loss, optimizer=rms)
model.fit([tr_pairs[:, 0], tr_pairs[:, 1]], tr_y,
          validation_data=([te_pairs[:, 0], te_pairs[:, 1]], te_y),
          batch_size=128,
          nb_epoch=nb_epoch)

# compute final accuracy on training and test sets
pred = model.predict([tr_pairs[:, 0], tr_pairs[:, 1]])
tr_acc = compute_accuracy(pred, tr_y)
pred = model.predict([te_pairs[:, 0], te_pairs[:, 1]])
te_acc = compute_accuracy(pred, te_y)

print('* Accuracy on training set: %0.2f%%' % (100 * tr_acc))
print('* Accuracy on test set: %0.2f%%' % (100 * te_acc))

'''Deep Dreaming in Keras.

Run the script with:
```
python deep_dream.py path_to_your_base_image.jpg prefix_for_results
```
e.g.:
```
python deep_dream.py img/mypic.jpg results/dream
```

It is preferrable to run this script on GPU, for speed.
If running on CPU, prefer the TensorFlow backend (much faster).

Example results: http://i.imgur.com/FX6ROg9.jpg
'''
from __future__ import print_function
from scipy.misc import imread, imresize, imsave
import numpy as np
from scipy.optimize import fmin_l_bfgs_b
import time
import argparse
import h5py
import os

from keras.models import Sequential
from keras.layers.convolutional import Convolution2D, ZeroPadding2D, MaxPooling2D
from keras import backend as K

parser = argparse.ArgumentParser(description='Deep Dreams with Keras.')
parser.add_argument('base_image_path', metavar='base', type=str,
                    help='Path to the image to transform.')
parser.add_argument('result_prefix', metavar='res_prefix', type=str,
                    help='Prefix for the saved results.')

args = parser.parse_args()
base_image_path = args.base_image_path
result_prefix = args.result_prefix

# dimensions of the generated picture.
img_width = 600
img_height = 600

# path to the model weights file.
weights_path = 'vgg16_weights.h5'

# some settings we found interesting
saved_settings = {
    'bad_trip': {'features': {'conv4_1': 0.05,
                              'conv4_2': 0.01,
                              'conv4_3': 0.01},
                 'continuity': 0.1,
                 'dream_l2': 0.8,
                 'jitter': 5},
    'dreamy': {'features': {'conv5_1': 0.05,
                            'conv5_2': 0.02},
               'continuity': 0.1,
               'dream_l2': 0.02,
               'jitter': 0},
}
# the settings we will use in this experiment
settings = saved_settings['dreamy']

# util function to open, resize and format pictures into appropriate tensors
def preprocess_image(image_path):
    img = imresize(imread(image_path), (img_width, img_height))
    img = img.transpose((2, 0, 1)).astype('float64')
    img = np.expand_dims(img, axis=0)
    return img

# util function to convert a tensor into a valid image
def deprocess_image(x):
    x = x.transpose((1, 2, 0))
    x = np.clip(x, 0, 255).astype('uint8')
    return x

# build the VGG16 network
model = Sequential()
model.add(ZeroPadding2D((1, 1), batch_input_shape=(1, 3, img_width, img_height)))
first_layer = model.layers[-1]
# this is a placeholder tensor that will contain our generated images
dream = first_layer.input

model.add(Convolution2D(64, 3, 3, activation='relu', name='conv1_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(64, 3, 3, activation='relu', name='conv1_2'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(128, 3, 3, activation='relu', name='conv2_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(128, 3, 3, activation='relu', name='conv2_2'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(256, 3, 3, activation='relu', name='conv3_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(256, 3, 3, activation='relu', name='conv3_2'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(256, 3, 3, activation='relu', name='conv3_3'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv4_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv4_2'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv4_3'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv5_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv5_2'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv5_3'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

# load the weights of the VGG16 networks
# (trained on ImageNet, won the ILSVRC competition in 2014)
# note: when there is a complete match between your model definition
# and your weight savefile, you can simply call model.load_weights(filename)
assert os.path.exists(weights_path), 'Model weights not found (see "weights_path" variable in script).'
f = h5py.File(weights_path)
for k in range(f.attrs['nb_layers']):
    if k >= len(model.layers):
        # we don't look at the last (fully-connected) layers in the savefile
        break
    g = f['layer_{}'.format(k)]
    weights = [g['param_{}'.format(p)] for p in range(g.attrs['nb_params'])]
    model.layers[k].set_weights(weights)
f.close()
print('Model loaded.')

# get the symbolic outputs of each "key" layer (we gave them unique names).
layer_dict = dict([(layer.name, layer) for layer in model.layers])

# continuity loss util function
def continuity_loss(x):
    assert K.ndim(x) == 4
    a = K.square(x[:, :, :img_width-1, :img_height-1] - x[:, :, 1:, :img_height-1])
    b = K.square(x[:, :, :img_width-1, :img_height-1] - x[:, :, :img_width-1, 1:])
    return K.sum(K.pow(a + b, 1.25))

# define the loss
loss = K.variable(0.)
for layer_name in settings['features']:
    # add the L2 norm of the features of a layer to the loss
    assert layer_name in layer_dict.keys(), 'Layer ' + layer_name + ' not found in model.'
    coeff = settings['features'][layer_name]
    x = layer_dict[layer_name].output
    shape = layer_dict[layer_name].output_shape
    # we avoid border artifacts by only involving non-border pixels in the loss
    loss -= coeff * K.sum(K.square(x[:, :, 2: shape[2]-2, 2: shape[3]-2])) / np.prod(shape[1:])

# add continuity loss (gives image local coherence, can result in an artful blur)
loss += settings['continuity'] * continuity_loss(dream) / (3 * img_width * img_height)
# add image L2 norm to loss (prevents pixels from taking very high values, makes image darker)
loss += settings['dream_l2'] * K.sum(K.square(dream)) / (3 * img_width * img_height)

# feel free to further modify the loss as you see fit, to achieve new effects...

# compute the gradients of the dream wrt the loss
grads = K.gradients(loss, dream)

outputs = [loss]
if type(grads) in {list, tuple}:
    outputs += grads
else:
    outputs.append(grads)

f_outputs = K.function([dream], outputs)
def eval_loss_and_grads(x):
    x = x.reshape((1, 3, img_width, img_height))
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
# so as to minimize the loss
x = preprocess_image(base_image_path)
for i in range(5):
    print('Start of iteration', i)
    start_time = time.time()

    # add a random jitter to the initial image. This will be reverted at decoding time
    random_jitter = (settings['jitter'] * 2) * (np.random.random((3, img_width, img_height)) - 0.5)
    x += random_jitter

    # run L-BFGS for 7 steps
    x, min_val, info = fmin_l_bfgs_b(evaluator.loss, x.flatten(),
                                     fprime=evaluator.grads, maxfun=7)
    print('Current loss value:', min_val)
    # decode the dream and save it
    x = x.reshape((3, img_width, img_height))
    x -= random_jitter
    img = deprocess_image(x)
    fname = result_prefix + '_at_iteration_%d.png' % i
    imsave(fname, img)
    end_time = time.time()
    print('Image saved as', fname)
    print('Iteration %d completed in %ds' % (i, end_time - start_time))

'''Trains and evaluate a simple MLP
on the Reuters newswire topic classification task.
'''

from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.datasets import reuters
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.normalization import BatchNormalization
from keras.utils import np_utils
from keras.preprocessing.text import Tokenizer

max_words = 1000
batch_size = 32
nb_epoch = 5

print('Loading data...')
(X_train, y_train), (X_test, y_test) = reuters.load_data(nb_words=max_words, test_split=0.2)
print(len(X_train), 'train sequences')
print(len(X_test), 'test sequences')

nb_classes = np.max(y_train)+1
print(nb_classes, 'classes')

print('Vectorizing sequence data...')
tokenizer = Tokenizer(nb_words=max_words)
X_train = tokenizer.sequences_to_matrix(X_train, mode='binary')
X_test = tokenizer.sequences_to_matrix(X_test, mode='binary')
print('X_train shape:', X_train.shape)
print('X_test shape:', X_test.shape)

print('Convert class vector to binary class matrix (for use with categorical_crossentropy)')
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)
print('Y_train shape:', Y_train.shape)
print('Y_test shape:', Y_test.shape)

print('Building model...')
model = Sequential()
model.add(Dense(512, input_shape=(max_words,)))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(nb_classes))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

history = model.fit(X_train, Y_train,
                    nb_epoch=nb_epoch, batch_size=batch_size,
                    verbose=1, validation_split=0.1)
score = model.evaluate(X_test, Y_test,
                       batch_size=batch_size, verbose=1)
print('Test score:', score[0])
print('Test accuracy:', score[1])

# -*- coding: utf-8 -*-
'''An implementation of sequence to sequence learning for performing addition
Input: "535+61"
Output: "596"
Padding is handled by using a repeated sentinel character (space)

Input may optionally be inverted, shown to increase performance in many tasks in:
"Learning to Execute"
http://arxiv.org/abs/1410.4615
and
"Sequence to Sequence Learning with Neural Networks"
http://papers.nips.cc/paper/5346-sequence-to-sequence-learning-with-neural-networks.pdf
Theoretically it introduces shorter term dependencies between source and target.

Two digits inverted:
+ One layer LSTM (128 HN), 5k training examples = 99% train/test accuracy in 55 epochs

Three digits inverted:
+ One layer LSTM (128 HN), 50k training examples = 99% train/test accuracy in 100 epochs

Four digits inverted:
+ One layer LSTM (128 HN), 400k training examples = 99% train/test accuracy in 20 epochs

Five digits inverted:
+ One layer LSTM (128 HN), 550k training examples = 99% train/test accuracy in 30 epochs

'''

from __future__ import print_function
from keras.models import Sequential
from keras.engine.training import slice_X
from keras.layers.core import Activation, TimeDistributedDense, RepeatVector
from keras.layers import recurrent
import numpy as np
from six.moves import range


class CharacterTable(object):
    '''
    Given a set of characters:
    + Encode them to a one hot integer representation
    + Decode the one hot integer representation to their character output
    + Decode a vector of probabilties to their character output
    '''
    def __init__(self, chars, maxlen):
        self.chars = sorted(set(chars))
        self.char_indices = dict((c, i) for i, c in enumerate(self.chars))
        self.indices_char = dict((i, c) for i, c in enumerate(self.chars))
        self.maxlen = maxlen

    def encode(self, C, maxlen=None):
        maxlen = maxlen if maxlen else self.maxlen
        X = np.zeros((maxlen, len(self.chars)))
        for i, c in enumerate(C):
            X[i, self.char_indices[c]] = 1
        return X

    def decode(self, X, calc_argmax=True):
        if calc_argmax:
            X = X.argmax(axis=-1)
        return ''.join(self.indices_char[x] for x in X)


class colors:
    ok = '\033[92m'
    fail = '\033[91m'
    close = '\033[0m'

# Parameters for the model and dataset
TRAINING_SIZE = 50000
DIGITS = 3
INVERT = True
# Try replacing GRU, or SimpleRNN
RNN = recurrent.LSTM
HIDDEN_SIZE = 128
BATCH_SIZE = 128
LAYERS = 1
MAXLEN = DIGITS + 1 + DIGITS

chars = '0123456789+ '
ctable = CharacterTable(chars, MAXLEN)

questions = []
expected = []
seen = set()
print('Generating data...')
while len(questions) < TRAINING_SIZE:
    f = lambda: int(''.join(np.random.choice(list('0123456789')) for i in range(np.random.randint(1, DIGITS + 1))))
    a, b = f(), f()
    # Skip any addition questions we've already seen
    # Also skip any such that X+Y == Y+X (hence the sorting)
    key = tuple(sorted((a, b)))
    if key in seen:
        continue
    seen.add(key)
    # Pad the data with spaces such that it is always MAXLEN
    q = '{}+{}'.format(a, b)
    query = q + ' ' * (MAXLEN - len(q))
    ans = str(a + b)
    # Answers can be of maximum size DIGITS + 1
    ans += ' ' * (DIGITS + 1 - len(ans))
    if INVERT:
        query = query[::-1]
    questions.append(query)
    expected.append(ans)
print('Total addition questions:', len(questions))

print('Vectorization...')
X = np.zeros((len(questions), MAXLEN, len(chars)), dtype=np.bool)
y = np.zeros((len(questions), DIGITS + 1, len(chars)), dtype=np.bool)
for i, sentence in enumerate(questions):
    X[i] = ctable.encode(sentence, maxlen=MAXLEN)
for i, sentence in enumerate(expected):
    y[i] = ctable.encode(sentence, maxlen=DIGITS + 1)

# Shuffle (X, y) in unison as the later parts of X will almost all be larger digits
indices = np.arange(len(y))
np.random.shuffle(indices)
X = X[indices]
y = y[indices]

# Explicitly set apart 10% for validation data that we never train over
split_at = len(X) - len(X) / 10
(X_train, X_val) = (slice_X(X, 0, split_at), slice_X(X, split_at))
(y_train, y_val) = (y[:split_at], y[split_at:])

print(X_train.shape)
print(y_train.shape)

print('Build model...')
model = Sequential()
# "Encode" the input sequence using an RNN, producing an output of HIDDEN_SIZE
# note: in a situation where your input sequences have a variable length,
# use input_shape=(None, nb_feature).
model.add(RNN(HIDDEN_SIZE, input_shape=(MAXLEN, len(chars))))
# For the decoder's input, we repeat the encoded input for each time step
model.add(RepeatVector(DIGITS + 1))
# The decoder RNN could be multiple layers stacked or a single layer
for _ in range(LAYERS):
    model.add(RNN(HIDDEN_SIZE, return_sequences=True))

# For each of step of the output sequence, decide which character should be chosen
model.add(TimeDistributedDense(len(chars)))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

# Train the model each generation and show predictions against the validation dataset
for iteration in range(1, 200):
    print()
    print('-' * 50)
    print('Iteration', iteration)
    model.fit(X_train, y_train, batch_size=BATCH_SIZE, nb_epoch=1,
              validation_data=(X_val, y_val))
    ###
    # Select 10 samples from the validation set at random so we can visualize errors
    for i in range(10):
        ind = np.random.randint(0, len(X_val))
        rowX, rowy = X_val[np.array([ind])], y_val[np.array([ind])]
        preds = model.predict_classes(rowX, verbose=0)
        q = ctable.decode(rowX[0])
        correct = ctable.decode(rowy[0])
        guess = ctable.decode(preds[0], calc_argmax=False)
        print('Q', q[::-1] if INVERT else q)
        print('T', correct)
        print(colors.ok + 'â˜‘' + colors.close if correct == guess else colors.fail + 'â˜’' + colors.close, guess)
        print('---')

'''Trains a memory network on the bAbI dataset.

References:
- Jason Weston, Antoine Bordes, Sumit Chopra, Tomas Mikolov, Alexander M. Rush,
  "Towards AI-Complete Question Answering: A Set of Prerequisite Toy Tasks",
  http://arxiv.org/abs/1502.05698

- Sainbayar Sukhbaatar, Arthur Szlam, Jason Weston, Rob Fergus,
  "End-To-End Memory Networks",
  http://arxiv.org/abs/1503.08895

Reaches 98.6% accuracy on task 'single_supporting_fact_10k' after 120 epochs.
Time per epoch: 3s on CPU (core i7).
'''

from __future__ import print_function
from keras.models import Sequential
from keras.layers.embeddings import Embedding
from keras.layers.core import Activation, Dense, Merge, Permute, Dropout
from keras.layers.recurrent import LSTM
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
    return [x.strip() for x in re.split('(\W+)?', sent) if x.strip()]


def parse_stories(lines, only_supporting=False):
    '''Parse stories provided in the bAbi tasks format

    If only_supporting is true, only the sentences that support the answer are kept.
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
            substory = None
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
    '''Given a file name, read the file, retrieve the stories, and then convert the sentences into a single story.

    If max_length is supplied, any stories longer than max_length tokens will be discarded.
    '''
    data = parse_stories(f.readlines(), only_supporting=only_supporting)
    flatten = lambda data: reduce(lambda x, y: x + y, data)
    data = [(flatten(story), q, answer) for story, q, answer in data if not max_length or len(flatten(story)) < max_length]
    return data


def vectorize_stories(data, word_idx, story_maxlen, query_maxlen):
    X = []
    Xq = []
    Y = []
    for story, query, answer in data:
        x = [word_idx[w] for w in story]
        xq = [word_idx[w] for w in query]
        y = np.zeros(len(word_idx) + 1)  # let's not forget that index 0 is reserved
        y[word_idx[answer]] = 1
        X.append(x)
        Xq.append(xq)
        Y.append(y)
    return (pad_sequences(X, maxlen=story_maxlen),
            pad_sequences(Xq, maxlen=query_maxlen), np.array(Y))


path = get_file('babi-tasks-v1-2.tar.gz',
                origin='http://www.thespermwhale.com/jaseweston/babi/tasks_1-20_v1-2.tar.gz')
tar = tarfile.open(path)

challenges = {
    # QA1 with 10,000 samples
    'single_supporting_fact_10k': 'tasks_1-20_v1-2/en-10k/qa1_single-supporting-fact_{}.txt',
    # QA2 with 10,000 samples
    'two_supporting_facts_10k': 'tasks_1-20_v1-2/en-10k/qa2_two-supporting-facts_{}.txt',
}
challenge_type = 'single_supporting_fact_10k'
challenge = challenges[challenge_type]

print('Extracting stories for the challenge:', challenge_type)
train_stories = get_stories(tar.extractfile(challenge.format('train')))
test_stories = get_stories(tar.extractfile(challenge.format('test')))

vocab = sorted(reduce(lambda x, y: x | y, (set(story + q + [answer]) for story, q, answer in train_stories + test_stories)))
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
inputs_train, queries_train, answers_train = vectorize_stories(train_stories, word_idx, story_maxlen, query_maxlen)
inputs_test, queries_test, answers_test = vectorize_stories(test_stories, word_idx, story_maxlen, query_maxlen)

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

# embed the input sequence into a sequence of vectors
input_encoder_m = Sequential()
input_encoder_m.add(Embedding(input_dim=vocab_size,
                              output_dim=64,
                              input_length=story_maxlen))
input_encoder_m.add(Dropout(0.3))
# output: (samples, story_maxlen, embedding_dim)
# embed the question into a sequence of vectors
question_encoder = Sequential()
question_encoder.add(Embedding(input_dim=vocab_size,
                               output_dim=64,
                               input_length=query_maxlen))
question_encoder.add(Dropout(0.3))
# output: (samples, query_maxlen, embedding_dim)
# compute a 'match' between input sequence elements (which are vectors)
# and the question vector sequence
match = Sequential()
match.add(Merge([input_encoder_m, question_encoder],
                mode='dot',
                dot_axes=[2, 2]))
# output: (samples, story_maxlen, query_maxlen)
# embed the input into a single vector with size = story_maxlen:
input_encoder_c = Sequential()
input_encoder_c.add(Embedding(input_dim=vocab_size,
                              output_dim=query_maxlen,
                              input_length=story_maxlen))
input_encoder_c.add(Dropout(0.3))
# output: (samples, story_maxlen, query_maxlen)
# sum the match vector with the input vector:
response = Sequential()
response.add(Merge([match, input_encoder_c], mode='sum'))
# output: (samples, story_maxlen, query_maxlen)
response.add(Permute((2, 1)))  # output: (samples, query_maxlen, story_maxlen)

# concatenate the match vector with the question vector,
# and do logistic regression on top
answer = Sequential()
answer.add(Merge([response, question_encoder], mode='concat', concat_axis=-1))
# the original paper uses a matrix multiplication for this reduction step.
# we choose to use a RNN instead.
answer.add(LSTM(32))
# one regularization layer -- more would probably be needed.
answer.add(Dropout(0.3))
answer.add(Dense(vocab_size))
# we output a probability distribution over the vocabulary
answer.add(Activation('softmax'))

answer.compile(optimizer='rmsprop', loss='categorical_crossentropy',
               metrics=['accuracy'])
# Note: you could use a Graph model to avoid repeat the input twice
answer.fit([inputs_train, queries_train, inputs_train], answers_train,
           batch_size=32,
           nb_epoch=120,
           validation_data=([inputs_test, queries_test, inputs_test], answers_test))

'''Compare LSTM implementations on the IMDB sentiment classification task.

consume_less='cpu' preprocesses input to the LSTM which typically results in
faster computations at the expense of increased peak memory usage as the
preprocessed input must be kept in memory.

consume_less='mem' does away with the preprocessing, meaning that it might take
a little longer, but should require less peak memory.

consume_less='gpu' concatenates the input, output and forget gate's weights
into one, large matrix, resulting in faster computation time as the GPU can
utilize more cores, at the expense of reduced regularization because the same
dropout is shared across the gates.

Note that the relative performance of the different `consume_less` modes
can vary depending on your device, your model and the size of your data.
'''

import time
import numpy as np
import matplotlib.pyplot as plt

from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import Embedding, Dense, LSTM
from keras.datasets import imdb

max_features = 20000
max_length = 80
embedding_dim = 256
batch_size = 128
epochs = 10
modes = ['cpu', 'mem', 'gpu']

print('Loading data...')
(X_train, y_train), (X_test, y_test) = imdb.load_data(nb_words=max_features)
X_train = sequence.pad_sequences(X_train, max_length)
X_test = sequence.pad_sequences(X_test, max_length)

# Compile and train different models while meauring performance.
results = []
for mode in modes:
    print('Testing mode: consume_less="{}"'.format(mode))

    model = Sequential()
    model.add(Embedding(max_features, embedding_dim, input_length=max_length, dropout=0.2))
    model.add(LSTM(embedding_dim, dropout_W=0.2, dropout_U=0.2, consume_less=mode))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(loss='binary_crossentropy',
                  optimizer='adam',
                  metrics=['accuracy'])

    start_time = time.time()
    history = model.fit(X_train, y_train,
                        batch_size=batch_size,
                        nb_epoch=epochs,
                        validation_data=(X_test, y_test))
    average_time_per_epoch = (time.time() - start_time) / epochs

    results.append((history, average_time_per_epoch))

# Compare models' accuracy, loss and elapsed time per epoch.
plt.style.use('ggplot')
ax1 = plt.subplot2grid((2, 2), (0, 0))
ax1.set_title('Accuracy')
ax1.set_ylabel('Validation Accuracy')
ax1.set_xlabel('Epochs')
ax2 = plt.subplot2grid((2, 2), (1, 0))
ax2.set_title('Loss')
ax2.set_ylabel('Validation Loss')
ax2.set_xlabel('Epochs')
ax3 = plt.subplot2grid((2, 2), (0, 1), rowspan=2)
ax3.set_title('Time')
ax3.set_ylabel('Seconds')
for mode, result in zip(modes, results):
    ax1.plot(result[0].epoch, result[0].history['val_acc'], label=mode)
    ax2.plot(result[0].epoch, result[0].history['val_loss'], label=mode)
ax1.legend()
ax2.legend()
ax3.bar(np.arange(len(results)), [x[1] for x in results],
        tick_label=modes, align='center')
plt.tight_layout()
plt.show()

'''Example script showing how to use stateful RNNs
to model long sequences efficiently.
'''
from __future__ import print_function
import numpy as np
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers.core import Dense
from keras.layers.recurrent import LSTM


# since we are using stateful rnn tsteps can be set to 1
tsteps = 1
batch_size = 25
epochs = 25
# number of elements ahead that are used to make the prediction
lahead = 1


def gen_cosine_amp(amp=100, period=25, x0=0, xn=50000, step=1, k=0.0001):
    """Generates an absolute cosine time series with the amplitude
    exponentially decreasing

    Arguments:
        amp: amplitude of the cosine function
        period: period of the cosine function
        x0: initial x of the time series
        xn: final x of the time series
        step: step of the time series discretization
        k: exponential rate
    """
    cos = np.zeros(((xn - x0) * step, 1, 1))
    for i in range(len(cos)):
        idx = x0 + i * step
        cos[i, 0, 0] = amp * np.cos(idx / (2 * np.pi * period))
        cos[i, 0, 0] = cos[i, 0, 0] * np.exp(-k * idx)
    return cos


print('Generating Data')
cos = gen_cosine_amp()
print('Input shape:', cos.shape)

expected_output = np.zeros((len(cos), 1))
for i in range(len(cos) - lahead):
    expected_output[i, 0] = np.mean(cos[i + 1:i + lahead + 1])

print('Output shape')
print(expected_output.shape)

print('Creating Model')
model = Sequential()
model.add(LSTM(50,
               batch_input_shape=(batch_size, tsteps, 1),
               return_sequences=True,
               stateful=True))
model.add(LSTM(50,
               batch_input_shape=(batch_size, tsteps, 1),
               return_sequences=False,
               stateful=True))
model.add(Dense(1))
model.compile(loss='mse', optimizer='rmsprop')

print('Training')
for i in range(epochs):
    print('Epoch', i, '/', epochs)
    model.fit(cos,
              expected_output,
              batch_size=batch_size,
              verbose=1,
              nb_epoch=1,
              shuffle=False)
    model.reset_states()

print('Predicting')
predicted_output = model.predict(cos, batch_size=batch_size)

print('Ploting Results')
plt.subplot(2, 1, 1)
plt.plot(expected_output)
plt.title('Expected')
plt.subplot(2, 1, 2)
plt.plot(predicted_output)
plt.title('Predicted')
plt.show()

'''Visualization of the filters of VGG16, via gradient ascent in input space.

This script can run on CPU in a few minutes (with the TensorFlow backend).

Results example: http://i.imgur.com/4nj4KjN.jpg

Before running this script, download the weights for the VGG16 model at:
https://drive.google.com/file/d/0Bz7KyqmuGsilT0J5dmRCM0ROVHc/view?usp=sharing
(source: https://gist.github.com/baraldilorenzo/07d7802847aaad0a35d3)
and make sure the variable `weights_path` in this script matches the location of the file.
'''
from __future__ import print_function
from scipy.misc import imsave
import numpy as np
import time
import os
import h5py

from keras.models import Sequential
from keras.layers import Convolution2D, ZeroPadding2D, MaxPooling2D
from keras import backend as K

# dimensions of the generated pictures for each filter.
img_width = 128
img_height = 128

# path to the model weights file.
weights_path = 'vgg16_weights.h5'

# the name of the layer we want to visualize (see model definition below)
layer_name = 'conv5_1'

# util function to convert a tensor into a valid image
def deprocess_image(x):
    # normalize tensor: center on 0., ensure std is 0.1
    x -= x.mean()
    x /= (x.std() + 1e-5)
    x *= 0.1

    # clip to [0, 1]
    x += 0.5
    x = np.clip(x, 0, 1)

    # convert to RGB array
    x *= 255
    x = x.transpose((1, 2, 0))
    x = np.clip(x, 0, 255).astype('uint8')
    return x

# build the VGG16 network
model = Sequential()
model.add(ZeroPadding2D((1, 1), batch_input_shape=(1, 3, img_width, img_height)))
first_layer = model.layers[-1]
# this is a placeholder tensor that will contain our generated images
input_img = first_layer.input

model.add(Convolution2D(64, 3, 3, activation='relu', name='conv1_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(64, 3, 3, activation='relu', name='conv1_2'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(128, 3, 3, activation='relu', name='conv2_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(128, 3, 3, activation='relu', name='conv2_2'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(256, 3, 3, activation='relu', name='conv3_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(256, 3, 3, activation='relu', name='conv3_2'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(256, 3, 3, activation='relu', name='conv3_3'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv4_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv4_2'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv4_3'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv5_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv5_2'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv5_3'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

# load the weights of the VGG16 networks
# (trained on ImageNet, won the ILSVRC competition in 2014)
# note: when there is a complete match between your model definition
# and your weight savefile, you can simply call model.load_weights(filename)
assert os.path.exists(weights_path), 'Model weights not found (see "weights_path" variable in script).'
f = h5py.File(weights_path)
for k in range(f.attrs['nb_layers']):
    if k >= len(model.layers):
        # we don't look at the last (fully-connected) layers in the savefile
        break
    g = f['layer_{}'.format(k)]
    weights = [g['param_{}'.format(p)] for p in range(g.attrs['nb_params'])]
    model.layers[k].set_weights(weights)
f.close()
print('Model loaded.')

# get the symbolic outputs of each "key" layer (we gave them unique names).
layer_dict = dict([(layer.name, layer) for layer in model.layers])


def normalize(x):
    # utility function to normalize a tensor by its L2 norm
    return x / (K.sqrt(K.mean(K.square(x))) + 1e-5)


kept_filters = []
for filter_index in range(0, 200):
    # we only scan through the first 200 filters,
    # but there are actually 512 of them
    print('Processing filter %d' % filter_index)
    start_time = time.time()

    # we build a loss function that maximizes the activation
    # of the nth filter of the layer considered
    layer_output = layer_dict[layer_name].output
    loss = K.mean(layer_output[:, filter_index, :, :])

    # we compute the gradient of the input picture wrt this loss
    grads = K.gradients(loss, input_img)[0]

    # normalization trick: we normalize the gradient
    grads = normalize(grads)

    # this function returns the loss and grads given the input picture
    iterate = K.function([input_img], [loss, grads])

    # step size for gradient ascent
    step = 1.

    # we start from a gray image with some random noise
    input_img_data = np.random.random((1, 3, img_width, img_height)) * 20 + 128.

    # we run gradient ascent for 20 steps
    for i in range(20):
        loss_value, grads_value = iterate([input_img_data])
        input_img_data += grads_value * step

        print('Current loss value:', loss_value)
        if loss_value <= 0.:
            # some filters get stuck to 0, we can skip them
            break

    # decode the resulting input image
    if loss_value > 0:
        img = deprocess_image(input_img_data[0])
        kept_filters.append((img, loss_value))
    end_time = time.time()
    print('Filter %d processed in %ds' % (filter_index, end_time - start_time))

# we will stich the best 64 filters on a 8 x 8 grid.
n = 8

# the filters that have the highest loss are assumed to be better-looking.
# we will only keep the top 64 filters.
kept_filters.sort(key=lambda x: x[1], reverse=True)
kept_filters = kept_filters[:n * n]

# build a black picture with enough space for
# our 8 x 8 filters of size 128 x 128, with a 5px margin in between
margin = 5
width = n * img_width + (n - 1) * margin
height = n * img_height + (n - 1) * margin
stitched_filters = np.zeros((width, height, 3))

# fill the picture with our saved filters
for i in range(n):
    for j in range(n):
        img, loss = kept_filters[i * n + j]
        stitched_filters[(img_width + margin) * i: (img_width + margin) * i + img_width,
                         (img_height + margin) * j: (img_height + margin) * j + img_height, :] = img

# save the result to disk
imsave('stitched_filters_%dx%d.png' % (n, n), stitched_filters)

'''Train a recurrent convolutional network on the IMDB sentiment
classification task.

Gets to 0.8498 test accuracy after 2 epochs. 41s/epoch on K520 GPU.
'''
from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM, GRU, SimpleRNN
from keras.layers.convolutional import Convolution1D, MaxPooling1D
from keras.datasets import imdb


# Embedding
max_features = 20000
maxlen = 100
embedding_size = 128

# Convolution
filter_length = 3
nb_filter = 64
pool_length = 2

# LSTM
lstm_output_size = 70

# Training
batch_size = 30
nb_epoch = 2

'''
Note:
batch_size is highly sensitive.
Only 2 epochs are needed as the dataset is very small.
'''

print('Loading data...')
(X_train, y_train), (X_test, y_test) = imdb.load_data(nb_words=max_features, test_split=0.2)
print(len(X_train), 'train sequences')
print(len(X_test), 'test sequences')

print('Pad sequences (samples x time)')
X_train = sequence.pad_sequences(X_train, maxlen=maxlen)
X_test = sequence.pad_sequences(X_test, maxlen=maxlen)
print('X_train shape:', X_train.shape)
print('X_test shape:', X_test.shape)

print('Build model...')

model = Sequential()
model.add(Embedding(max_features, embedding_size, input_length=maxlen))
model.add(Dropout(0.25))
model.add(Convolution1D(nb_filter=nb_filter,
                        filter_length=filter_length,
                        border_mode='valid',
                        activation='relu',
                        subsample_length=1))
model.add(MaxPooling1D(pool_length=pool_length))
model.add(LSTM(lstm_output_size))
model.add(Dense(1))
model.add(Activation('sigmoid'))

model.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

print('Train...')
model.fit(X_train, y_train, batch_size=batch_size, nb_epoch=nb_epoch,
          validation_data=(X_test, y_test))
score, acc = model.evaluate(X_test, y_test, batch_size=batch_size)
print('Test score:', score)
print('Test accuracy:', acc)

'''Transfer learning toy example:

1- Train a simple convnet on the MNIST dataset the first 5 digits [0..4].
2- Freeze convolutional layers and fine-tune dense layers
   for the classification of digits [5..9].

Run on GPU: THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python mnist_transfer_cnn.py

Get to 99.8% test accuracy after 5 epochs
for the first five digits classifier
and 99.2% for the last five digits after transfer + fine-tuning.
'''

from __future__ import print_function
import numpy as np
import datetime

np.random.seed(1337)  # for reproducibility

from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.utils import np_utils


now = datetime.datetime.now

batch_size = 128
nb_classes = 5
nb_epoch = 5

# input image dimensions
img_rows, img_cols = 28, 28
# number of convolutional filters to use
nb_filters = 32
# size of pooling area for max pooling
nb_pool = 2
# convolution kernel size
nb_conv = 3


def train_model(model, train, test, nb_classes):
    X_train = train[0].reshape(train[0].shape[0], 1, img_rows, img_cols)
    X_test = test[0].reshape(test[0].shape[0], 1, img_rows, img_cols)
    X_train = X_train.astype('float32')
    X_test = X_test.astype('float32')
    X_train /= 255
    X_test /= 255
    print('X_train shape:', X_train.shape)
    print(X_train.shape[0], 'train samples')
    print(X_test.shape[0], 'test samples')

    # convert class vectors to binary class matrices
    Y_train = np_utils.to_categorical(train[1], nb_classes)
    Y_test = np_utils.to_categorical(test[1], nb_classes)

    model.compile(loss='categorical_crossentropy',
                  optimizer='adadelta',
                  metrics=['accuracy'])

    t = now()
    model.fit(X_train, Y_train,
              batch_size=batch_size, nb_epoch=nb_epoch,
              verbose=1,
              validation_data=(X_test, Y_test))
    print('Training time: %s' % (now() - t))
    score = model.evaluate(X_test, Y_test, verbose=0)
    print('Test score:', score[0])
    print('Test accuracy:', score[1])


# the data, shuffled and split between train and test sets
(X_train, y_train), (X_test, y_test) = mnist.load_data()

# create two datasets one with digits below 5 and one with 5 and above
X_train_lt5 = X_train[y_train < 5]
y_train_lt5 = y_train[y_train < 5]
X_test_lt5 = X_test[y_test < 5]
y_test_lt5 = y_test[y_test < 5]

X_train_gte5 = X_train[y_train >= 5]
y_train_gte5 = y_train[y_train >= 5] - 5  # make classes start at 0 for
X_test_gte5 = X_test[y_test >= 5]         # np_utils.to_categorical
y_test_gte5 = y_test[y_test >= 5] - 5

# define two groups of layers: feature (convolutions) and classification (dense)
feature_layers = [
    Convolution2D(nb_filters, nb_conv, nb_conv,
                  border_mode='valid',
                  input_shape=(1, img_rows, img_cols)),
    Activation('relu'),
    Convolution2D(nb_filters, nb_conv, nb_conv),
    Activation('relu'),
    MaxPooling2D(pool_size=(nb_pool, nb_pool)),
    Dropout(0.25),
    Flatten(),
]
classification_layers = [
    Dense(128),
    Activation('relu'),
    Dropout(0.5),
    Dense(nb_classes),
    Activation('softmax')
]

# create complete model
model = Sequential()
for l in feature_layers + classification_layers:
    model.add(l)

# train model for 5-digit classification [0..4]
train_model(model,
            (X_train_lt5, y_train_lt5),
            (X_test_lt5, y_test_lt5), nb_classes)

# freeze feature layers and rebuild model
for l in feature_layers:
    l.trainable = False

# transfer: train dense layers for new classification task [5..9]
train_model(model,
            (X_train_gte5, y_train_gte5),
            (X_test_gte5, y_test_gte5), nb_classes)

'''Train a simple deep CNN on the CIFAR10 small images dataset.

GPU run command:
    THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python cifar10_cnn.py

It gets down to 0.65 test logloss in 25 epochs, and down to 0.55 after 50 epochs.
(it's still underfitting at that point, though).

Note: the data was pickled with Python 2, and some encoding issues might prevent you
from loading it in Python 3. You might have to load it in Python 2,
save it in a different format, load it in Python 3 and repickle it.
'''

from __future__ import print_function
from keras.datasets import cifar10
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import SGD
from keras.utils import np_utils

batch_size = 32
nb_classes = 10
nb_epoch = 200
data_augmentation = True

# input image dimensions
img_rows, img_cols = 32, 32
# the CIFAR10 images are RGB
img_channels = 3

# the data, shuffled and split between train and test sets
(X_train, y_train), (X_test, y_test) = cifar10.load_data()
print('X_train shape:', X_train.shape)
print(X_train.shape[0], 'train samples')
print(X_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)

model = Sequential()

model.add(Convolution2D(32, 3, 3, border_mode='same',
                        input_shape=(img_channels, img_rows, img_cols)))
model.add(Activation('relu'))
model.add(Convolution2D(32, 3, 3))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Convolution2D(64, 3, 3, border_mode='same'))
model.add(Activation('relu'))
model.add(Convolution2D(64, 3, 3))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(512))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(nb_classes))
model.add(Activation('softmax'))

# let's train the model using SGD + momentum (how original).
sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy',
              optimizer=sgd,
              metrics=['accuracy'])

X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
X_train /= 255
X_test /= 255

if not data_augmentation:
    print('Not using data augmentation.')
    model.fit(X_train, Y_train,
              batch_size=batch_size,
              nb_epoch=nb_epoch,
              validation_data=(X_test, Y_test),
              shuffle=True)
else:
    print('Using real-time data augmentation.')

    # this will do preprocessing and realtime data augmentation
    datagen = ImageDataGenerator(
        featurewise_center=False,  # set input mean to 0 over the dataset
        samplewise_center=False,  # set each sample mean to 0
        featurewise_std_normalization=False,  # divide inputs by std of the dataset
        samplewise_std_normalization=False,  # divide each input by its std
        zca_whitening=False,  # apply ZCA whitening
        rotation_range=0,  # randomly rotate images in the range (degrees, 0 to 180)
        width_shift_range=0.1,  # randomly shift images horizontally (fraction of total width)
        height_shift_range=0.1,  # randomly shift images vertically (fraction of total height)
        horizontal_flip=True,  # randomly flip images
        vertical_flip=False)  # randomly flip images

    # compute quantities required for featurewise normalization
    # (std, mean, and principal components if ZCA whitening is applied)
    datagen.fit(X_train)

    # fit the model on the batches generated by datagen.flow()
    model.fit_generator(datagen.flow(X_train, Y_train,
                        batch_size=batch_size),
                        samples_per_epoch=X_train.shape[0],
                        nb_epoch=nb_epoch,
                        validation_data=(X_test, Y_test))

'''Neural style transfer with Keras.

Before running this script, download the weights for the VGG16 model at:
https://drive.google.com/file/d/0Bz7KyqmuGsilT0J5dmRCM0ROVHc/view?usp=sharing
(source: https://gist.github.com/baraldilorenzo/07d7802847aaad0a35d3)
and make sure the variable `weights_path` in this script matches the location of the file.

Run the script with:
```
python neural_style_transfer.py path_to_your_base_image.jpg path_to_your_reference.jpg prefix_for_results
```
e.g.:
```
python neural_style_transfer.py img/tuebingen.jpg img/starry_night.jpg results/my_result
```

It is preferrable to run this script on GPU, for speed.
If running on CPU, prefer the TensorFlow backend (much faster).

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
L2 distances betwen the Gram matrices of the representations of
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
from scipy.misc import imread, imresize, imsave
import numpy as np
from scipy.optimize import fmin_l_bfgs_b
import time
import os
import argparse
import h5py

from keras.models import Sequential
from keras.layers.convolutional import Convolution2D, ZeroPadding2D, MaxPooling2D
from keras import backend as K

parser = argparse.ArgumentParser(description='Neural style transfer with Keras.')
parser.add_argument('base_image_path', metavar='base', type=str,
                    help='Path to the image to transform.')
parser.add_argument('style_reference_image_path', metavar='ref', type=str,
                    help='Path to the style reference image.')
parser.add_argument('result_prefix', metavar='res_prefix', type=str,
                    help='Prefix for the saved results.')

args = parser.parse_args()
base_image_path = args.base_image_path
style_reference_image_path = args.style_reference_image_path
result_prefix = args.result_prefix
weights_path = 'vgg16_weights.h5'

# these are the weights of the different loss components
total_variation_weight = 1.
style_weight = 1.
content_weight = 0.025

# dimensions of the generated picture.
img_width = 400
img_height = 400
assert img_height == img_width, 'Due to the use of the Gram matrix, width and height must match.'

# util function to open, resize and format pictures into appropriate tensors
def preprocess_image(image_path):
    img = imresize(imread(image_path), (img_width, img_height))
    img = img.transpose((2, 0, 1)).astype('float64')
    img = np.expand_dims(img, axis=0)
    return img

# util function to convert a tensor into a valid image
def deprocess_image(x):
    x = x.transpose((1, 2, 0))
    x = np.clip(x, 0, 255).astype('uint8')
    return x

# get tensor representations of our images
base_image = K.variable(preprocess_image(base_image_path))
style_reference_image = K.variable(preprocess_image(style_reference_image_path))

# this will contain our generated image
combination_image = K.placeholder((1, 3, img_width, img_height))

# combine the 3 images into a single Keras tensor
input_tensor = K.concatenate([base_image,
                              style_reference_image,
                              combination_image], axis=0)

# build the VGG16 network with our 3 images as input
first_layer = ZeroPadding2D((1, 1))
first_layer.set_input(input_tensor, shape=(3, 3, img_width, img_height))

model = Sequential()
model.add(first_layer)
model.add(Convolution2D(64, 3, 3, activation='relu', name='conv1_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(64, 3, 3, activation='relu'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(128, 3, 3, activation='relu', name='conv2_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(128, 3, 3, activation='relu'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(256, 3, 3, activation='relu', name='conv3_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(256, 3, 3, activation='relu'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(256, 3, 3, activation='relu'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv4_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv4_2'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu', name='conv5_1'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu'))
model.add(ZeroPadding2D((1, 1)))
model.add(Convolution2D(512, 3, 3, activation='relu'))
model.add(MaxPooling2D((2, 2), strides=(2, 2)))

# load the weights of the VGG16 networks
# (trained on ImageNet, won the ILSVRC competition in 2014)
# note: when there is a complete match between your model definition
# and your weight savefile, you can simply call model.load_weights(filename)
assert os.path.exists(weights_path), 'Model weights not found (see "weights_path" variable in script).'
f = h5py.File(weights_path)
for k in range(f.attrs['nb_layers']):
    if k >= len(model.layers):
        # we don't look at the last (fully-connected) layers in the savefile
        break
    g = f['layer_{}'.format(k)]
    weights = [g['param_{}'.format(p)] for p in range(g.attrs['nb_params'])]
    model.layers[k].set_weights(weights)
f.close()
print('Model loaded.')

# get the symbolic outputs of each "key" layer (we gave them unique names).
outputs_dict = dict([(layer.name, layer.output) for layer in model.layers])

# compute the neural style loss
# first we need to define 4 util functions

# the gram matrix of an image tensor (feature-wise outer product)
def gram_matrix(x):
    assert K.ndim(x) == 3
    features = K.batch_flatten(x)
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
    size = img_width * img_height
    return K.sum(K.square(S - C)) / (4. * (channels ** 2) * (size ** 2))

# an auxiliary loss function
# designed to maintain the "content" of the
# base image in the generated image
def content_loss(base, combination):
    return K.sum(K.square(combination - base))

# the 3rd loss function, total variation loss,
# designed to keep the generated image locally coherent
def total_variation_loss(x):
    assert K.ndim(x) == 4
    a = K.square(x[:, :, :img_width-1, :img_height-1] - x[:, :, 1:, :img_height-1])
    b = K.square(x[:, :, :img_width-1, :img_height-1] - x[:, :, :img_width-1, 1:])
    return K.sum(K.pow(a + b, 1.25))

# combine these loss functions into a single scalar
loss = K.variable(0.)
layer_features = outputs_dict['conv4_2']
base_image_features = layer_features[0, :, :, :]
combination_features = layer_features[2, :, :, :]
loss += content_weight * content_loss(base_image_features,
                                      combination_features)

feature_layers = ['conv1_1', 'conv2_1', 'conv3_1', 'conv4_1', 'conv5_1']
for layer_name in feature_layers:
    layer_features = outputs_dict[layer_name]
    style_reference_features = layer_features[1, :, :, :]
    combination_features = layer_features[2, :, :, :]
    sl = style_loss(style_reference_features, combination_features)
    loss += (style_weight / len(feature_layers)) * sl
loss += total_variation_weight * total_variation_loss(combination_image)

# get the gradients of the generated image wrt the loss
grads = K.gradients(loss, combination_image)

outputs = [loss]
if type(grads) in {list, tuple}:
    outputs += grads
else:
    outputs.append(grads)

f_outputs = K.function([combination_image], outputs)
def eval_loss_and_grads(x):
    x = x.reshape((1, 3, img_width, img_height))
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
x = np.random.uniform(0, 255, (1, 3, img_width, img_height))
for i in range(10):
    print('Start of iteration', i)
    start_time = time.time()
    x, min_val, info = fmin_l_bfgs_b(evaluator.loss, x.flatten(),
                                     fprime=evaluator.grads, maxfun=20)
    print('Current loss value:', min_val)
    # save current generated image
    img = deprocess_image(x.reshape((3, img_width, img_height)))
    fname = result_prefix + '_at_iteration_%d.png' % i
    imsave(fname, img)
    end_time = time.time()
    print('Image saved as', fname)
    print('Iteration %d completed in %ds' % (i, end_time - start_time))

