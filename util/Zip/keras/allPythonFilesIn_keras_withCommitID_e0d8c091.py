from setuptools import setup
from setuptools import find_packages


setup(name='Keras',
      version='0.3.0',
      description='Theano-based Deep Learning library',
      author='Francois Chollet',
      author_email='francois.chollet@gmail.com',
      url='https://github.com/fchollet/keras',
      download_url='https://github.com/fchollet/keras/tarball/0.3.0',
      license='MIT',
      install_requires=['theano', 'pyyaml', 'six'],
      extras_require={
          'h5py': ['h5py'],
      },
      packages=find_packages())

from __future__ import absolute_import
from __future__ import print_function
import numpy as np
import warnings
import pprint
from six.moves import range
import six

from . import backend as K
from . import optimizers
from . import objectives
from . import callbacks as cbks
from .utils.layer_utils import container_from_config
from .utils.layer_utils import model_summary
from .utils.generic_utils import Progbar
from .layers import containers


def standardize_y(y):
    if not hasattr(y, 'shape'):
        y = np.asarray(y)
    if len(y.shape) == 1:
        y = np.expand_dims(y, 1)
    return y


def batch_shuffle(index_array, batch_size):
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
    nb_batch = int(np.ceil(size / float(batch_size)))
    return [(i * batch_size, min(size, (i + 1) * batch_size)) for i in range(0, nb_batch)]


def standardize_X(X):
    if type(X) == list:
        return X
    else:
        return [X]


def slice_X(X, start=None, stop=None):
    '''
    '''
    if type(X) == list:
        if hasattr(start, '__len__'):
            # hdf5 dataset only support list object as indices
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
    def weighted(y_true, y_pred, weights, mask=None):
        '''
        '''
        # score_array has ndim >= 2
        score_array = fn(y_true, y_pred)
        if mask is not None:
            # mask should have the same shape as score_array
            score_array *= mask
            #  the loss per batch should be proportional
            #  to the number of unmasked sampled.
            score_array /= K.mean(mask)

        # reduce score_array to 1D
        ndim = K.ndim(score_array)
        for d in range(ndim-1):
            score_array = K.mean(score_array, axis=-1)

        if weights is not None:
            score_array *= weights
        return K.mean(score_array)
    return weighted


def standardize_weights(y, sample_weight=None, class_weight=None):
    '''
    '''
    if sample_weight is not None:
        assert len(sample_weight) == len(y)
        return sample_weight.flatten()
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
        return np.ones((y.shape[0],))


def model_from_yaml(yaml_string, custom_objects={}):
    '''
        Returns a model generated from a local yaml file,
        which is either created by hand or from to_yaml method
        of Sequential or Graph
    '''
    import yaml
    config = yaml.load(yaml_string)
    return model_from_config(config, custom_objects=custom_objects)


def model_from_json(json_string, custom_objects={}):
    import json
    config = json.loads(json_string)
    return model_from_config(config, custom_objects=custom_objects)


def model_from_config(config, custom_objects={}):
    '''
    '''
    model_name = config.get('name')
    if model_name not in {'Graph', 'Sequential'}:
        raise Exception('Unrecognized model:', model_name)

    # Create a container then set class to appropriate model
    model = container_from_config(config, custom_objects=custom_objects)
    if model_name == 'Graph':
        model.__class__ = Graph
    elif model_name == 'Sequential':
        model.__class__ = Sequential

    if 'optimizer' in config:
        # if it has an optimizer, the model is assumed to be compiled
        loss = config.get('loss')
        class_mode = config.get('class_mode')

        optimizer_params = dict([(k, v) for k, v in config.get('optimizer').items()])
        optimizer_name = optimizer_params.pop('name')
        optimizer = optimizers.get(optimizer_name, optimizer_params)

        if model_name == 'Sequential':
            model.compile(loss=loss, optimizer=optimizer,
                          class_mode=class_mode)
        elif model_name == 'Graph':
            model.compile(loss=loss, optimizer=optimizer)
    return model


def get_function_name(o):
    if isinstance(o, six.string_types):
        return o
    else:
        return o.__name__


class Model(object):
    '''Abstract base model class.
    '''
    def _fit(self, f, ins, out_labels=[], batch_size=128,
             nb_epoch=100, verbose=1, callbacks=[],
             val_f=None, val_ins=None, shuffle=True, metrics=[]):
        '''
            Abstract fit function for f(ins).
            Assume that f returns a list, labelled by out_labels.
        '''
        do_validation = False
        if val_f and val_ins:
            do_validation = True
            if verbose:
                print('Train on %d samples, validate on %d samples' %
                      (len(ins[0]), len(val_ins[0])))

        nb_train_sample = len(ins[0])
        index_array = np.arange(nb_train_sample)

        history = cbks.History()
        if verbose:
            callbacks = [history, cbks.BaseLogger()] + callbacks
        else:
            callbacks = [history] + callbacks
        callbacks = cbks.CallbackList(callbacks)

        callbacks._set_model(self)
        callbacks._set_params({
            'batch_size': batch_size,
            'nb_epoch': nb_epoch,
            'nb_sample': nb_train_sample,
            'verbose': verbose,
            'do_validation': do_validation,
            'metrics': metrics,
        })
        callbacks.on_train_begin()

        self.stop_training = False
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
            if self.stop_training:
                break

        callbacks.on_train_end()
        return history

    def _predict_loop(self, f, ins, batch_size=128, verbose=0):
        '''Abstract method to loop over some data in batches.
        '''
        nb_sample = len(ins[0])
        outs = []
        if verbose == 1:
            progbar = Progbar(target=nb_sample)
        batches = make_batches(nb_sample, batch_size)
        index_array = np.arange(nb_sample)
        for batch_index, (batch_start, batch_end) in enumerate(batches):
            batch_ids = index_array[batch_start:batch_end]
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
        return outs

    def _test_loop(self, f, ins, batch_size=128, verbose=0):
        '''Abstract method to loop over some data in batches.
        '''
        nb_sample = len(ins[0])
        outs = []
        if verbose == 1:
            progbar = Progbar(target=nb_sample)
        batches = make_batches(nb_sample, batch_size)
        index_array = np.arange(nb_sample)
        for batch_index, (batch_start, batch_end) in enumerate(batches):
            batch_ids = index_array[batch_start:batch_end]
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
        return outs

    def get_config(self, verbose=0):
        '''Return the configuration of the model
        as a dictionary.

        To load a model from its configuration, use
        `keras.models.model_from_config(config, custom_objects={})`.
        '''
        config = super(Model, self).get_config()
        for p in ['class_mode']:
            if hasattr(self, p):
                config[p] = getattr(self, p)
        if hasattr(self, 'optimizer'):
            config['optimizer'] = self.optimizer.get_config()
        if hasattr(self, 'loss'):
            if type(self.loss) == dict:
                config['loss'] = dict([(k, get_function_name(v)) for k, v in self.loss.items()])
            else:
                config['loss'] = get_function_name(self.loss)

        if verbose:
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(config)
        return config

    def to_yaml(self, **kwargs):
        '''Return a yaml string containing the model configuration.

        To load a model from a yaml save file, use
        `keras.models.from_yaml(yaml_string, custom_objects={})`.

        `custom_objects` should be a dictionary mapping
        the names of custom losses / layers / etc to the corresponding
        functions / classes.
        '''
        import yaml
        config = self.get_config()
        return yaml.dump(config, **kwargs)

    def to_json(self, **kwargs):
        '''Return a JSON string containing the model configuration.

        To load a model from a JSON save file, use
        `keras.models.from_json(json_string, custom_objects={})`.
        '''
        import json
        config = self.get_config()
        return json.dumps(config, **kwargs)

    def summary(self):
        '''Print out a summary of the model architecture,
        include parameter count information.
        '''
        model_summary(self)


class Sequential(Model, containers.Sequential):
    '''Linear stack of layers.

    Inherits from containers.Sequential.
    '''
    def compile(self, optimizer, loss,
                class_mode="categorical"):
        '''Configure the learning process.

        # Arguments
            optimizer: str (name of optimizer) or optimizer object.
                See [optimizers](optimizers.md).
            loss: str (name of objective function) or objective function.
                See [objectives](objectives.md).
            class_mode: one of "categorical", "binary".
                This is only used for computing classification accuracy or
                using the predict_classes method.
        '''
        self.optimizer = optimizers.get(optimizer)

        self.loss = objectives.get(loss)
        weighted_loss = weighted_objective(objectives.get(loss))

        # input of model
        self.X_train = self.get_input(train=True)
        self.X_test = self.get_input(train=False)

        self.y_train = self.get_output(train=True)
        self.y_test = self.get_output(train=False)

        # target of model
        self.y = K.placeholder(ndim=K.ndim(self.y_train))
        # weights: one scalar per sample
        self.weights = K.placeholder(ndim=1)

        if hasattr(self.layers[-1], "get_output_mask"):
            mask = self.layers[-1].get_output_mask()
        else:
            mask = None
        train_loss = weighted_loss(self.y, self.y_train, self.weights, mask)
        test_loss = weighted_loss(self.y, self.y_test, self.weights, mask)

        if class_mode == "categorical":
            train_accuracy = K.mean(K.equal(K.argmax(self.y, axis=-1),
                                            K.argmax(self.y_train, axis=-1)))
            test_accuracy = K.mean(K.equal(K.argmax(self.y, axis=-1),
                                           K.argmax(self.y_test, axis=-1)))

        elif class_mode == "binary":
            train_accuracy = K.mean(K.equal(self.y, K.round(self.y_train)))
            test_accuracy = K.mean(K.equal(self.y, K.round(self.y_test)))
        else:
            raise Exception("Invalid class mode:" + str(class_mode))
        self.class_mode = class_mode

        for r in self.regularizers:
            train_loss = r(train_loss)
        updates = self.optimizer.get_updates(self.params,
                                             self.constraints,
                                             train_loss)
        updates += self.updates

        if type(self.X_train) == list:
            train_ins = self.X_train + [self.y, self.weights]
            test_ins = self.X_test + [self.y, self.weights]
            assert type(self.X_test) == list
            predict_ins = self.X_test
        else:
            train_ins = [self.X_train, self.y, self.weights]
            test_ins = [self.X_test, self.y, self.weights]
            predict_ins = [self.X_test]

        self._train = K.function(train_ins, [train_loss], updates=updates)
        self._train_with_acc = K.function(train_ins, [train_loss, train_accuracy], updates=updates)
        self._predict = K.function(predict_ins, [self.y_test], updates=self.state_updates)
        self._test = K.function(test_ins, [test_loss])
        self._test_with_acc = K.function(test_ins, [test_loss, test_accuracy])

    def fit(self, X, y, batch_size=128, nb_epoch=100, verbose=1, callbacks=[],
            validation_split=0., validation_data=None, shuffle=True,
            show_accuracy=False, class_weight=None, sample_weight=None):
        '''Train the model for a fixed number of epochs.

        Returns a history object. It `history` attribute is a record of
        training loss values at successive epochs,
        as well as validation loss values (if applicable).

        # Arguments
            X: data, as a numpy array.
            y: labels, as a numpy array.
            batch_size: int. Number of samples per gradient update.
            nb_epoch: int.
            verbose: 0 for no logging to stdout,
                1 for progress bar logging, 2 for one log line per epoch.
            callbacks: `keras.callbacks.Callback` list.
                List of callbacks to apply during training.
                See [callbacks](callbacks.md).
            validation_split: float (0. < x < 1).
                Fraction of the data to use as held-out validation data.
            validation_data: tuple (X, y) to be used as held-out
                validation data. Will override validation_split.
            shuffle: boolean or str (for 'batch').
                Whether to shuffle the samples at each epoch.
                'batch' is a special option for dealing with the
                limitations of HDF5 data; it shuffles in batch-sized chunks.
            show_accuracy: boolean. Whether to display
                class accuracy in the logs to stdout at each epoch.
            class_weight: dictionary mapping classes to a weight value,
                used for scaling the loss function (during training only).
            sample_weight: list or numpy array with 1:1 mapping to
                the training samples, used for scaling the loss function
                (during training only). For time-distributed data,
                there is one weight per sample *per timestep*,
                i.e. if your output data is shaped
                `(nb_samples, timesteps, output_dim)`,
                your mask should be of shape `(nb_samples, timesteps, 1)`.
                This allows you to mask out or reweight individual
                output timesteps, which is useful
                in sequence to sequence learning.
        '''
        X = standardize_X(X)
        y = standardize_y(y)

        val_f = None
        val_ins = None
        if validation_data or validation_split:
            if show_accuracy:
                val_f = self._test_with_acc
            else:
                val_f = self._test
        if validation_data:
            if len(validation_data) == 2:
                X_val, y_val = validation_data
                X_val = standardize_X(X_val)
                y_val = standardize_y(y_val)
                sample_weight_val = standardize_weights(y_val)
            elif len(validation_data) == 3:
                X_val, y_val, sample_weight_val = validation_data
                X_val = standardize_X(X_val)
                y_val = standardize_y(y_val)
                sample_weight_val = standardize_weights(y_val,
                                                        sample_weight=sample_weight_val)
            else:
                raise Exception('Invalid format for validation data; '
                                'provide a tuple (X_val, y_val) or '
                                '(X_val, y_val, sample_weight). '
                                'X_val may be a numpy array or a list of '
                                'numpy arrays depending on your model input.')
            val_ins = X_val + [y_val, sample_weight_val]

        elif 0 < validation_split < 1:
            split_at = int(len(X[0]) * (1 - validation_split))
            X, X_val = (slice_X(X, 0, split_at), slice_X(X, split_at))
            y, y_val = (slice_X(y, 0, split_at), slice_X(y, split_at))
            if sample_weight is not None:
                sample_weight, sample_weight_val = (slice_X(sample_weight, 0, split_at), slice_X(sample_weight, split_at))
                sample_weight_val = standardize_weights(y_val,
                                                        sample_weight=sample_weight_val)
            else:
                sample_weight_val = standardize_weights(y_val)
            val_ins = X_val + [y_val, sample_weight_val]

        if show_accuracy:
            f = self._train_with_acc
            out_labels = ['loss', 'acc']
        else:
            f = self._train
            out_labels = ['loss']

        sample_weight = standardize_weights(y, class_weight=class_weight,
                                            sample_weight=sample_weight)
        ins = X + [y, sample_weight]
        metrics = ['loss', 'acc', 'val_loss', 'val_acc']
        return self._fit(f, ins, out_labels=out_labels,
                         batch_size=batch_size, nb_epoch=nb_epoch,
                         verbose=verbose, callbacks=callbacks,
                         val_f=val_f, val_ins=val_ins,
                         shuffle=shuffle, metrics=metrics)

    def predict(self, X, batch_size=128, verbose=0):
        '''Generate output predictions for the input samples
        batch by batch.

        # Arguments
            X: the input data, as a numpy array.
            batch_size: integer.
            verbose: verbosity mode, 0 or 1.

        # Returns
            A numpy array of predictions.
        '''
        X = standardize_X(X)
        return self._predict_loop(self._predict, X, batch_size, verbose)[0]

    def predict_proba(self, X, batch_size=128, verbose=1):
        '''Generate class probability predictions for the input samples
        batch by batch.

        # Arguments
            X: the input data, as a numpy array.
            batch_size: integer.
            verbose: verbosity mode, 0 or 1.

        # Returns
            A numpy array of probability predictions.
        '''
        preds = self.predict(X, batch_size, verbose)
        if preds.min() < 0 or preds.max() > 1:
            warnings.warn('Network returning invalid probability values.')
        return preds

    def predict_classes(self, X, batch_size=128, verbose=1):
        '''Generate class predictions for the input samples
        batch by batch.

        # Arguments
            X: the input data, as a numpy array.
            batch_size: integer.
            verbose: verbosity mode, 0 or 1.

        # Returns
            A numpy array of class predictions.
        '''
        proba = self.predict(X, batch_size=batch_size, verbose=verbose)
        if self.class_mode == 'categorical':
            return proba.argmax(axis=-1)
        else:
            return (proba > 0.5).astype('int32')

    def evaluate(self, X, y, batch_size=128, show_accuracy=False,
                 verbose=1, sample_weight=None):
        '''Compute the loss on some input data, batch by batch.

        # Arguments
            X: input data, as a numpy array.
            y: labels, as a numpy array.
            batch_size: integer.
            show_accuracy: boolean.
            verbose: verbosity mode, 0 or 1.
            sample_weight: sample weights, as a numpy array.
        '''
        X = standardize_X(X)
        y = standardize_y(y)
        sample_weight = standardize_weights(y, sample_weight=sample_weight)

        ins = X + [y, sample_weight]
        if show_accuracy:
            f = self._test_with_acc
        else:
            f = self._test
        outs = self._test_loop(f, ins, batch_size, verbose)
        if show_accuracy:
            return outs
        else:
            return outs[0]

    def train_on_batch(self, X, y, accuracy=False,
                       class_weight=None, sample_weight=None):
        '''Single gradient update over one batch of samples.

        Returns the loss over the data,
        or a tuple `(loss, accuracy)` if `accuracy=True`.

        Arguments: see `fit` method.
        '''
        X = standardize_X(X)
        y = standardize_y(y)
        sample_weight = standardize_weights(y, class_weight=class_weight,
                                            sample_weight=sample_weight)
        ins = X + [y, sample_weight]
        if accuracy:
            return self._train_with_acc(ins)
        else:
            return self._train(ins)

    def test_on_batch(self, X, y, accuracy=False, sample_weight=None):
        '''Returns the loss over a single batch of samples,
        or a tuple `(loss, accuracy)` if `accuracy=True`.

        Arguments: see `fit` method.
        '''
        X = standardize_X(X)
        y = standardize_y(y)
        sample_weight = standardize_weights(y, sample_weight=sample_weight)

        ins = X + [y, sample_weight]
        if accuracy:
            return self._test_with_acc(ins)
        else:
            return self._test(ins)

    def predict_on_batch(self, X):
        '''Returns predictions for a single batch of samples.
        '''
        ins = standardize_X(X)
        return self._predict(ins)

    def save_weights(self, filepath, overwrite=False):
        '''Dump all layer weights to a HDF5 file.
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

        f = h5py.File(filepath, 'w')
        f.attrs['nb_layers'] = len(self.layers)
        for k, l in enumerate(self.layers):
            g = f.create_group('layer_{}'.format(k))
            weights = l.get_weights()
            g.attrs['nb_params'] = len(weights)
            for n, param in enumerate(weights):
                param_name = 'param_{}'.format(n)
                param_dset = g.create_dataset(param_name, param.shape,
                                              dtype=param.dtype)
                param_dset[:] = param
        f.flush()
        f.close()

    def load_weights(self, filepath):
        '''Load all layer weights from a HDF5 save file.
        '''
        import h5py
        f = h5py.File(filepath)
        for k in range(f.attrs['nb_layers']):
            # This method does not make use of Sequential.set_weights()
            # for backwards compatibility.
            g = f['layer_{}'.format(k)]
            weights = [g['param_{}'.format(p)] for p in range(g.attrs['nb_params'])]
            self.layers[k].set_weights(weights)
        f.close()


class Graph(Model, containers.Graph):
    '''Arbitrary connection graph.
    It can have any number of inputs and outputs,
    with each output trained with its own loss function.
    The quantity being optimized by a Graph model is
    the sum of all loss functions over the different outputs.

    Inherits from `containers.Graph`.
    '''
    def compile(self, optimizer, loss):
        '''Configure the learning process.

        # Arguments
            optimizer: str (name of optimizer) or optimizer object.
                See [optimizers](optimizers.md).
            loss: dictionary mapping the name(s) of the output(s) to
                a loss function (string name of objective function or
                objective function. See [objectives](objectives.md)).
        '''
        ys = []
        ys_train = []
        ys_test = []
        weights = []
        train_loss = 0.
        test_loss = 0.
        for output_name in self.output_order:
            loss_fn = loss[output_name]
            output = self.outputs[output_name]
            y_train = output.get_output(True)
            y_test = output.get_output(False)
            y = K.placeholder(ndim=K.ndim(y_train))
            ys.append(y)
            ys_train.append(y_train)
            ys_test.append(y_test)

            if hasattr(output, "get_output_mask"):
                mask = output.get_output_mask()
            else:
                mask = None

            weight = K.placeholder(ndim=1)
            weights.append(weight)
            weighted_loss = weighted_objective(objectives.get(loss_fn))
            train_loss += weighted_loss(y, y_train, weight, mask)
            test_loss += weighted_loss(y, y_test, weight, mask)

        ins = [self.inputs[name].input for name in self.input_order]
        train_ins = ins + ys + weights
        test_ins = ins + ys + weights

        for r in self.regularizers:
            train_loss = r(train_loss)
        self.optimizer = optimizers.get(optimizer)
        updates = self.optimizer.get_updates(self.params,
                                             self.constraints,
                                             train_loss)
        updates += self.updates
        self.loss = loss

        self._train = K.function(train_ins, [train_loss], updates=updates)
        self._test = K.function(test_ins, [test_loss])
        self._predict = K.function(inputs=ins, outputs=ys_test,
                                   updates=self.state_updates)

    def fit(self, data, batch_size=128, nb_epoch=100, verbose=1, callbacks=[],
            validation_split=0., validation_data=None, shuffle=True,
            class_weight={}, sample_weight={}):
        '''Train the model for a fixed number of epochs.

        Returns a history object. It `history` attribute is a record of
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
        X = [data[name] for name in self.input_order]
        y = [standardize_y(data[name]) for name in self.output_order]

        sample_weight_list = [standardize_weights(y[i],
                                                  sample_weight=sample_weight.get(self.output_order[i])) for i in range(len(self.output_order))]
        class_weight_list = [class_weight.get(name) for name in self.output_order]

        val_f = None
        val_ins = None
        if validation_data or validation_split:
            val_f = self._test
        if validation_data:
            # can't use sample weights with validation data at this point
            y_val = [standardize_y(validation_data[name]) for name in self.output_order]
            sample_weight = [standardize_weights(y_val[i]) for i in range(len(y_val))]
            val_ins = [validation_data[name] for name in self.input_order] + [standardize_y(validation_data[name]) for name in self.output_order] + sample_weight

        elif 0 < validation_split < 1:
            split_at = int(len(X[0]) * (1 - validation_split))
            X, X_val = (slice_X(X, 0, split_at), slice_X(X, split_at))
            y, y_val = (slice_X(y, 0, split_at), slice_X(y, split_at))
            sample_weight_list, sample_weight_list_val = (slice_X(sample_weight_list, 0, split_at), slice_X(sample_weight_list, split_at))
            val_ins = X_val + y_val + sample_weight_list_val

        f = self._train
        out_labels = ['loss']
        metrics = ['loss', 'val_loss']

        sample_weight_list = [standardize_weights(y[i],
                                                  sample_weight=sample_weight_list[i],
                                                  class_weight=class_weight_list[i]) for i in range(len(self.output_order))]
        ins = X + y + sample_weight_list
        history = self._fit(f, ins, out_labels=out_labels,
                            batch_size=batch_size, nb_epoch=nb_epoch,
                            verbose=verbose, callbacks=callbacks,
                            val_f=val_f, val_ins=val_ins,
                            shuffle=shuffle, metrics=metrics)
        return history

    def evaluate(self, data, batch_size=128, verbose=0, sample_weight={}):
        '''Compute the loss on some input data, batch by batch.

        Arguments: see `fit` method.
        '''
        sample_weight = [standardize_weights(data[name],
                                             sample_weight=sample_weight.get(name)) for name in self.output_order]

        ins = [data[name] for name in self.input_order] + [standardize_y(data[name]) for name in self.output_order] + sample_weight
        outs = self._test_loop(self._test, ins, batch_size, verbose)
        return outs[0]

    def predict(self, data, batch_size=128, verbose=0):
        '''Generate output predictions for the input samples
        batch by batch.

        Arguments: see `fit` method.
        '''
        ins = [data[name] for name in self.input_order]
        outs = self._predict_loop(self._predict, ins, batch_size, verbose)
        return dict(zip(self.output_order, outs))

    def train_on_batch(self, data, class_weight={}, sample_weight={}):
        '''Single gradient update on a batch of samples.

        Arguments: see `fit` method.
        '''
        sample_weight = [standardize_weights(data[name],
                                             sample_weight=sample_weight.get(name),
                                             class_weight=class_weight.get(name)) for name in self.output_order]
        ins = [data[name] for name in self.input_order] + [standardize_y(data[name]) for name in self.output_order] + sample_weight
        return self._train(ins)

    def test_on_batch(self, data, sample_weight={}):
        '''Compute the loss on a single batch of samples.

        Arguments: see `fit` method.
        '''
        sample_weight = [standardize_weights(data[name],
                                             sample_weight=sample_weight.get(name)) for name in self.output_order]
        ins = [data[name] for name in self.input_order] + [standardize_y(data[name]) for name in self.output_order] + sample_weight
        return self._test(ins)

    def predict_on_batch(self, data):
        '''Generate predictions for a single batch of samples.
        '''
        ins = [data[name] for name in self.input_order]
        return self._predict(ins)

    def save_weights(self, filepath, overwrite=False):
        '''Save weights from all layers to a HDF5 files.
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

        f = h5py.File(filepath, 'w')
        g = f.create_group('graph')
        weights = self.get_weights()
        g.attrs['nb_params'] = len(weights)
        for n, param in enumerate(weights):
            param_name = 'param_{}'.format(n)
            param_dset = g.create_dataset(param_name, param.shape,
                                          dtype=param.dtype)
            param_dset[:] = param
        f.flush()
        f.close()

    def load_weights(self, filepath):
        '''Load weights from a HDF5 file.
        '''
        import h5py
        f = h5py.File(filepath)
        g = f['graph']
        weights = [g['param_{}'.format(p)] for p in range(g.attrs['nb_params'])]
        self.set_weights(weights)
        f.close()

from __future__ import absolute_import
from . import backend as K


def softmax(x):
    ndim = K.ndim(x)
    if ndim == 2:
        return K.softmax(x)
    elif ndim == 3:
        # apply softmax to each timestep
        def step(x, states):
            return K.softmax(x), []
        last_output, outputs, states = K.rnn(step, x, [], masking=False)
        return outputs
    else:
        raise Exception('Cannot apply softmax to a tensor that is not 2D or 3D. ' +
                        'Here, ndim=' + str(ndim))


def softplus(x):
    return K.softplus(x)


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
    The function returns the variable that is passed in, so all types work
    '''
    return x


from .utils.generic_utils import get_from_module
def get(identifier):
    return get_from_module(identifier, globals(), 'activation function')

__version__ = '0.3.0'

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
        return {"name": self.__class__.__name__}


class WeightRegularizer(Regularizer):
    def __init__(self, l1=0., l2=0.):
        self.l1 = l1
        self.l2 = l2

    def set_param(self, p):
        self.p = p

    def __call__(self, loss):
        loss += K.sum(K.abs(self.p)) * self.l1
        loss += K.sum(K.square(self.p)) * self.l2
        return loss

    def get_config(self):
        return {"name": self.__class__.__name__,
                "l1": self.l1,
                "l2": self.l2}


class ActivityRegularizer(Regularizer):
    def __init__(self, l1=0., l2=0.):
        self.l1 = l1
        self.l2 = l2

    def set_layer(self, layer):
        self.layer = layer

    def __call__(self, loss):
        output = self.layer.get_output(True)
        loss += self.l1 * K.sum(K.mean(K.abs(output), axis=0))
        loss += self.l2 * K.sum(K.mean(K.square(output), axis=0))
        return loss

    def get_config(self):
        return {"name": self.__class__.__name__,
                "l1": self.l1,
                "l2": self.l2}


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

identity = Regularizer

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
        self.__dict__.update(kwargs)
        self.updates = []

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

    def get_config(self):
        return {"name": self.__class__.__name__}


class SGD(Optimizer):
    '''Stochastic gradient descent, with support for momentum,
    decay, and Nesterov momentum.

    # Arguments
        lr: float >= 0. Learning rate.
        momentum: float >= 0. Parameter updates momentum.
        decay: float >= 0. Learning rate decay over each update.
        nesterov: boolean. Whether to apply Nesterov momentum.
    '''
    def __init__(self, lr=0.01, momentum=0., decay=0., nesterov=False,
                 *args, **kwargs):
        super(SGD, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.iterations = K.variable(0.)
        self.lr = K.variable(lr)
        self.momentum = K.variable(momentum)
        self.decay = K.variable(decay)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        lr = self.lr * (1.0 / (1.0 + self.decay * self.iterations))
        self.updates = [(self.iterations, self.iterations + 1.)]

        for p, g, c in zip(params, grads, constraints):
            m = K.variable(np.zeros(K.get_value(p).shape))  # momentum
            v = self.momentum * m - lr * g  # velocity
            self.updates.append((m, v))

            if self.nesterov:
                new_p = p + self.momentum * v - lr * g
            else:
                new_p = p + v

            self.updates.append((p, c(new_p)))  # apply constraints
        return self.updates

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(K.get_value(self.lr)),
                "momentum": float(K.get_value(self.momentum)),
                "decay": float(K.get_value(self.decay)),
                "nesterov": self.nesterov}


class RMSprop(Optimizer):
    '''RMSProp optimizer.

    It is recommended to leave the parameters of this optimizer
    at their default values.

    This optimizer is usually a good choice for recurrent
    neural networks.

    # Arguments
        lr: float >= 0. Learning rate.
        rho: float >= 0.
        epsilon: float >= 0. Fuzz factor.
    '''
    def __init__(self, lr=0.001, rho=0.9, epsilon=1e-6, *args, **kwargs):
        super(RMSprop, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.lr = K.variable(lr)
        self.rho = K.variable(rho)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        accumulators = [K.variable(np.zeros(K.get_value(p).shape)) for p in params]
        self.updates = []

        for p, g, a, c in zip(params, grads, accumulators, constraints):
            # update accumulator
            new_a = self.rho * a + (1 - self.rho) * K.square(g)
            self.updates.append((a, new_a))

            new_p = p - self.lr * g / K.sqrt(new_a + self.epsilon)
            self.updates.append((p, c(new_p)))  # apply constraints
        return self.updates

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(K.get_value(self.lr)),
                "rho": float(K.get_value(self.rho)),
                "epsilon": self.epsilon}


class Adagrad(Optimizer):
    '''Adagrad optimizer.

    It is recommended to leave the parameters of this optimizer
    at their default values.

    # Arguments
        lr: float >= 0. Learning rate.
        epsilon: float >= 0.
    '''
    def __init__(self, lr=0.01, epsilon=1e-6, *args, **kwargs):
        super(Adagrad, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.lr = K.variable(lr)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        accumulators = [K.variable(np.zeros(K.get_value(p).shape)) for p in params]
        self.updates = []

        for p, g, a, c in zip(params, grads, accumulators, constraints):
            new_a = a + K.square(g)  # update accumulator
            self.updates.append((a, new_a))
            new_p = p - self.lr * g / K.sqrt(new_a + self.epsilon)
            self.updates.append((p, c(new_p)))  # apply constraints
        return self.updates

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(K.get_value(self.lr)),
                "epsilon": self.epsilon}


class Adadelta(Optimizer):
    '''Adadelta optimizer.

    It is recommended to leave the parameters of this optimizer
    at their default values.

    # Arguments
        lr: float >= 0. Learning rate. It is recommended to leave it at the default value.
        rho: float >= 0.
        epsilon: float >= 0. Fuzz factor.

    # References
        - [Adadelta - an adaptive learning rate method](http://arxiv.org/abs/1212.5701)
    '''
    def __init__(self, lr=1.0, rho=0.95, epsilon=1e-6, *args, **kwargs):
        super(Adadelta, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.lr = K.variable(lr)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        accumulators = [K.variable(np.zeros(K.get_value(p).shape)) for p in params]
        delta_accumulators = [K.variable(np.zeros(K.get_value(p).shape)) for p in params]
        self.updates = []

        for p, g, a, d_a, c in zip(params, grads, accumulators,
                                   delta_accumulators, constraints):
            # update accumulator
            new_a = self.rho * a + (1 - self.rho) * K.square(g)
            self.updates.append((a, new_a))

            # use the new accumulator and the *old* delta_accumulator
            update = g * K.sqrt(d_a + self.epsilon) / K.sqrt(new_a + self.epsilon)

            new_p = p - self.lr * update
            self.updates.append((p, c(new_p)))  # apply constraints

            # update delta_accumulator
            new_d_a = self.rho * d_a + (1 - self.rho) * K.square(update)
            self.updates.append((d_a, new_d_a))
        return self.updates

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(K.get_value(self.lr)),
                "rho": self.rho,
                "epsilon": self.epsilon}


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
    def __init__(self, lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-8,
                 *args, **kwargs):
        super(Adam, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.iterations = K.variable(0)
        self.lr = K.variable(lr)
        self.beta_1 = K.variable(beta_1)
        self.beta_2 = K.variable(beta_2)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        self.updates = [(self.iterations, self.iterations+1.)]

        t = self.iterations + 1
        lr_t = self.lr * K.sqrt(1 - K.pow(self.beta_2, t)) / (1 - K.pow(self.beta_1, t))

        for p, g, c in zip(params, grads, constraints):
            # zero init of moment
            m = K.variable(np.zeros(K.get_value(p).shape))
            # zero init of velocity
            v = K.variable(np.zeros(K.get_value(p).shape))

            m_t = (self.beta_1 * m) + (1 - self.beta_1) * g
            v_t = (self.beta_2 * v) + (1 - self.beta_2) * K.square(g)
            p_t = p - lr_t * m_t / (K.sqrt(v_t) + self.epsilon)

            self.updates.append((m, m_t))
            self.updates.append((v, v_t))
            self.updates.append((p, c(p_t)))  # apply constraints
        return self.updates

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(K.get_value(self.lr)),
                "beta_1": float(K.get_value(self.beta_1)),
                "beta_2": float(K.get_value(self.beta_2)),
                "epsilon": self.epsilon}

# aliases
sgd = SGD
rmsprop = RMSprop
adagrad = Adagrad
adadelta = Adadelta
adam = Adam


def get(identifier, kwargs=None):
    return get_from_module(identifier, globals(), 'optimizer',
                           instantiate=True, kwargs=kwargs)

from __future__ import absolute_import
import numpy as np
from . import backend as K


def mean_squared_error(y_true, y_pred):
    return K.mean(K.square(y_pred - y_true), axis=-1)


def root_mean_squared_error(y_true, y_pred):
    return K.sqrt(K.mean(K.square(y_pred - y_true), axis=-1))


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
    '''Expects a binary class matrix instead of a vector of scalar classes
    '''
    return K.mean(K.categorical_crossentropy(y_pred, y_true), axis=-1)


def binary_crossentropy(y_true, y_pred):
    return K.mean(K.binary_crossentropy(y_pred, y_true), axis=-1)


def poisson_loss(y_true, y_pred):
    return K.mean(y_pred - y_true * K.log(y_pred + K.epsilon()), axis=-1)

# aliases
mse = MSE = mean_squared_error
rmse = RMSE = root_mean_squared_error
mae = MAE = mean_absolute_error
mape = MAPE = mean_absolute_percentage_error
msle = MSLE = mean_squared_logarithmic_error

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
        if self._delta_t_batch > 0. and delta_t_median > 0.95 * self._delta_t_batch and delta_t_median > 0.1:
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
        if self._delta_t_batch > 0. and delta_t_median > 0.95 * self._delta_t_batch and delta_t_median > 0.1:
            warnings.warn('Method on_batch_end() is slow compared '
                          'to the batch update (%f). Check your callbacks.' % delta_t_median)

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

        on_epoch_end: logs optionally include `val_loss`
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
    '''Callback that prints events to the standard output.

    This callback is automatically applied to
    every Keras model (it is the basis of the verbosity modes
    in models).
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
        self.totals = {}

    def on_batch_begin(self, batch, logs={}):
        if self.seen < self.params['nb_sample']:
            self.log_values = []

    def on_batch_end(self, batch, logs={}):
        batch_size = logs.get('size', 0)
        self.seen += batch_size

        for k, v in logs.items():
            if k in self.totals:
                self.totals[k] += v * batch_size
            else:
                self.totals[k] = v * batch_size
        for k in self.params['metrics']:
            if k in logs:
                self.log_values.append((k, logs[k]))

        # skip progbar update for the last batch;
        # will be handled by on_epoch_end
        if self.verbose and self.seen < self.params['nb_sample']:
            self.progbar.update(self.seen, self.log_values)

    def on_epoch_end(self, epoch, logs={}):
        for k in self.params['metrics']:
            if k in self.totals:
                self.log_values.append((k, self.totals[k] / self.seen))
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
        self.epoch.append(epoch)
        for k, v in self.totals.items():
            if k not in self.history:
                self.history[k] = []
            self.history[k].append(v / self.seen)

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
                          'fallback to auto mode' % (self.mode), RuntimeWarning)
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
                        print('Epoch %05d: %s improved from %0.5f to %0.5f, saving model to %s'
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
    '''
    def __init__(self, monitor='val_loss', patience=0, verbose=0):
        super(Callback, self).__init__()

        self.monitor = monitor
        self.patience = patience
        self.verbose = verbose
        self.best = np.Inf
        self.wait = 0

    def on_epoch_end(self, epoch, logs={}):
        current = logs.get(self.monitor)
        if current is None:
            warnings.warn('Early stopping requires %s available!' %
                          (self.monitor), RuntimeWarning)

        if current < self.best:
            self.best = current
            self.wait = 0
        else:
            if self.wait >= self.patience:
                if self.verbose > 0:
                    print('Epoch %05d: early stopping' % (epoch))
                self.model.stop_training = True
            self.wait += 1


class RemoteMonitor(Callback):
    '''Experimental callback used to stream events to a server.

    Requires the `requests` library.
    '''
    def __init__(self, root='http://localhost:9000'):
        self.root = root

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
        import requests
        send = {}
        send['epoch'] = epoch

        for k, v in self.totals.items():
            send[k] = v / self.seen
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
        schedule: a function that gets an epoch index as input
            (integer, indexed from 0) and returns a new
            learning rate as output.
    '''
    def __init__(self, schedule):
        super(LearningRateScheduler, self).__init__()
        self.schedule = schedule

    def on_epoch_begin(self, epoch, logs={}):
        self.model.optimizer.lr.set_value(self.schedule(epoch))

from __future__ import absolute_import
from . import backend as K


class Constraint(object):
    def __call__(self, p):
        return p

    def get_config(self):
        return {"name": self.__class__.__name__}


class MaxNorm(Constraint):
    def __init__(self, m=2):
        self.m = m

    def __call__(self, p):
        norms = K.sqrt(K.sum(K.square(p), axis=0))
        desired = K.clip(norms, 0, self.m)
        p = p * (desired / (1e-7 + norms))
        return p

    def get_config(self):
        return {"name": self.__class__.__name__,
                "m": self.m}


class NonNeg(Constraint):
    def __call__(self, p):
        p *= K.cast(p >= 0., K.floatx())
        return p


class UnitNorm(Constraint):
    def __call__(self, p):
        return p / K.sqrt(K.sum(K.square(p), axis=-1, keepdims=True))

identity = Constraint
maxnorm = MaxNorm
nonneg = NonNeg
unitnorm = UnitNorm

from .utils.generic_utils import get_from_module
def get(identifier, kwargs=None):
    return get_from_module(identifier, globals(), 'constraint', instantiate=True, kwargs=kwargs)

from __future__ import absolute_import
import numpy as np
from . import backend as K


def get_fans(shape):
    fan_in = shape[0] if len(shape) == 2 else np.prod(shape[1:])
    fan_out = shape[1] if len(shape) == 2 else shape[0]
    return fan_in, fan_out


def uniform(shape, scale=0.05):
    return K.variable(np.random.uniform(low=-scale, high=scale, size=shape))


def normal(shape, scale=0.05):
    return K.variable(np.random.randn(*shape) * scale)


def lecun_uniform(shape):
    ''' Reference: LeCun 98, Efficient Backprop
        http://yann.lecun.com/exdb/publis/pdf/lecun-98b.pdf
    '''
    fan_in, fan_out = get_fans(shape)
    scale = np.sqrt(3. / fan_in)
    return uniform(shape, scale)


def glorot_normal(shape):
    ''' Reference: Glorot & Bengio, AISTATS 2010
    '''
    fan_in, fan_out = get_fans(shape)
    s = np.sqrt(2. / (fan_in + fan_out))
    return normal(shape, s)


def glorot_uniform(shape):
    fan_in, fan_out = get_fans(shape)
    s = np.sqrt(6. / (fan_in + fan_out))
    return uniform(shape, s)


def he_normal(shape):
    ''' Reference:  He et al., http://arxiv.org/abs/1502.01852
    '''
    fan_in, fan_out = get_fans(shape)
    s = np.sqrt(2. / fan_in)
    return normal(shape, s)


def he_uniform(shape):
    fan_in, fan_out = get_fans(shape)
    s = np.sqrt(6. / fan_in)
    return uniform(shape, s)


def orthogonal(shape, scale=1.1):
    ''' From Lasagne. Reference: Saxe et al., http://arxiv.org/abs/1312.6120
    '''
    flat_shape = (shape[0], np.prod(shape[1:]))
    a = np.random.normal(0.0, 1.0, flat_shape)
    u, _, v = np.linalg.svd(a, full_matrices=False)
    # pick the one with the correct shape
    q = u if u.shape == flat_shape else v
    q = q.reshape(shape)
    return K.variable(scale * q[:shape[0], :shape[1]])


def identity(shape, scale=1):
    if len(shape) != 2 or shape[0] != shape[1]:
        raise Exception("Identity matrix initialization can only be used for 2D square matrices")
    else:
        return K.variable(scale * np.identity(shape[0]))


def zero(shape):
    return K.zeros(shape)


def one(shape):
    return K.ones(shape)


from .utils.generic_utils import get_from_module
def get(identifier):
    return get_from_module(identifier, globals(), 'initialization')


from __future__ import absolute_import
import abc
import copy
import numpy as np

from ..utils.np_utils import to_categorical


class BaseWrapper(object):
    """
    Base class for the Keras scikit-learn wrapper.

    Warning: This class should not be used directly. Use derived classes instead.

    Parameters
    ----------
    train_batch_size : int, optional
        Number of training samples evaluated at a time.
    test_batch_size : int, optional
        Number of test samples evaluated at a time.
    nb_epochs : int, optional
        Number of training epochs.
    shuffle : boolean, optional
        Whether to shuffle the samples at each epoch.
    show_accuracy : boolean, optional
        Whether to display class accuracy in the logs at each epoch.
    validation_split : float [0, 1], optional
        Fraction of the data to use as held-out validation data.
    validation_data : tuple (X, y), optional
        Data to be used as held-out validation data. Will override validation_split.
    callbacks : list, optional
        List of callbacks to apply during training.
    verbose : int, optional
        Verbosity level.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, model, optimizer, loss,
                 train_batch_size=128, test_batch_size=128,
                 nb_epoch=100, shuffle=True, show_accuracy=False,
                 validation_split=0, validation_data=None, callbacks=None,
                 verbose=0,):
        self.model = model
        self.optimizer = optimizer
        self.loss = loss
        self.compiled_model_ = None
        self.classes_ = []
        self.config_ = []
        self.weights_ = []

        self.train_batch_size = train_batch_size
        self.test_batch_size = test_batch_size
        self.nb_epoch = nb_epoch
        self.shuffle = shuffle
        self.show_accuracy = show_accuracy
        self.validation_split = validation_split
        self.validation_data = validation_data
        self.callbacks = [] if callbacks is None else callbacks

        self.verbose = verbose

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

    def fit(self, X, y):
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

        Returns
        -------
        history : object
            Returns details about the training history at each epoch.
        """
        if len(y.shape) == 1:
            self.classes_ = list(np.unique(y))
            if self.loss == 'categorical_crossentropy':
                y = to_categorical(y)
        else:
            self.classes_ = np.arange(0, y.shape[1])

        self.compiled_model_ = copy.deepcopy(self.model)
        self.compiled_model_.compile(optimizer=self.optimizer, loss=self.loss)
        history = self.compiled_model_.fit(
            X, y, batch_size=self.train_batch_size, nb_epoch=self.nb_epoch, verbose=self.verbose,
            shuffle=self.shuffle, show_accuracy=self.show_accuracy,
            validation_split=self.validation_split, validation_data=self.validation_data,
            callbacks=self.callbacks)

        self.config_ = self.model.get_config()
        self.weights_ = self.model.get_weights()

        return history


class KerasClassifier(BaseWrapper):
    """
    Implementation of the scikit-learn classifier API for Keras.

    Parameters
    ----------
    model : object
        An un-compiled Keras model object is required to use the scikit-learn wrapper.
    optimizer : string
        Optimization method used by the model during compilation/training.
    loss : string
        Loss function used by the model during compilation/training.
    """
    def __init__(self, model, optimizer='adam', loss='categorical_crossentropy', **kwargs):
        super(KerasClassifier, self).__init__(model, optimizer, loss, **kwargs)

    def predict(self, X):
        """
        Returns the class predictions for the given test data.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Test samples where n_samples in the number of samples
            and n_features is the number of features.

        Returns
        -------
        preds : array-like, shape = (n_samples)
            Class predictions.
        """
        return self.compiled_model_.predict_classes(
            X, batch_size=self.test_batch_size, verbose=self.verbose)

    def predict_proba(self, X):
        """
        Returns class probability estimates for the given test data.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Test samples where n_samples in the number of samples
            and n_features is the number of features.

        Returns
        -------
        proba : array-like, shape = (n_samples, n_outputs)
            Class probability estimates.
        """
        return self.compiled_model_.predict_proba(
            X, batch_size=self.test_batch_size, verbose=self.verbose)

    def score(self, X, y):
        """
        Returns the mean accuracy on the given test data and labels.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Test samples where n_samples in the number of samples
            and n_features is the number of features.
        y : array-like, shape = (n_samples) or (n_samples, n_outputs)
            True labels for X.

        Returns
        -------
        score : float
            Mean accuracy of predictions on X wrt. y.
        """
        loss, accuracy = self.compiled_model_.evaluate(
            X, y, batch_size=self.test_batch_size, show_accuracy=True, verbose=self.verbose)
        return accuracy


class KerasRegressor(BaseWrapper):
    """
    Implementation of the scikit-learn regressor API for Keras.

    Parameters
    ----------
    model : object
        An un-compiled Keras model object is required to use the scikit-learn wrapper.
    optimizer : string
        Optimization method used by the model during compilation/training.
    loss : string
        Loss function used by the model during compilation/training.
    """
    def __init__(self, model, optimizer='adam', loss='mean_squared_error', **kwargs):
        super(KerasRegressor, self).__init__(model, optimizer, loss, **kwargs)

    def predict(self, X):
        """
        Returns predictions for the given test data.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Test samples where n_samples in the number of samples
            and n_features is the number of features.

        Returns
        -------
        preds : array-like, shape = (n_samples)
            Predictions.
        """
        return self.compiled_model_.predict(
            X, batch_size=self.test_batch_size, verbose=self.verbose).ravel()

    def score(self, X, y):
        """
        Returns the mean accuracy on the given test data and labels.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Test samples where n_samples in the number of samples
            and n_features is the number of features.
        y : array-like, shape = (n_samples)
            True labels for X.

        Returns
        -------
        score : float
            Loss from predictions on X wrt. y.
        """
        loss = self.compiled_model_.evaluate(
            X, y, batch_size=self.test_batch_size, show_accuracy=False, verbose=self.verbose)
        return loss

# -*- coding: utf-8 -*-
from __future__ import absolute_import

from .. import backend as K
from .. import activations, initializations, regularizers, constraints
from ..layers.core import Layer


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

    # Input shape
        3D tensor with shape: `(samples, steps, input_dim)`.

    # Output shape
        3D tensor with shape: `(samples, new_steps, nb_filter)`.
        `steps` value might have changed due to padding.

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
        input_dim: Number of channels/dimensions in the input.
            Either this argument or the keyword argument `input_shape`must be
            provided when using this layer as the first layer in a model.
        input_length: Length of input sequences, when it is constant.
            This argument is required if you are going to connect
            `Flatten` then `Dense` layers upstream
            (without it, the shape of the dense outputs cannot be computed).
    '''
    input_ndim = 3

    def __init__(self, nb_filter, filter_length,
                 init='uniform', activation='linear', weights=None,
                 border_mode='valid', subsample_length=1,
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None,
                 input_dim=None, input_length=None, **kwargs):

        if border_mode not in {'valid', 'same'}:
            raise Exception('Invalid border mode for Convolution1D:', border_mode)
        self.nb_filter = nb_filter
        self.filter_length = filter_length
        self.init = initializations.get(init)
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
        self.constraints = [self.W_constraint, self.b_constraint]

        self.initial_weights = weights

        self.input_dim = input_dim
        self.input_length = input_length
        if self.input_dim:
            kwargs['input_shape'] = (self.input_length, self.input_dim)
        self.input = K.placeholder(ndim=3)
        super(Convolution1D, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[2]
        self.W_shape = (self.nb_filter, input_dim, self.filter_length, 1)
        self.W = self.init(self.W_shape)
        self.b = K.zeros((self.nb_filter,))
        self.params = [self.W, self.b]
        self.regularizers = []

        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    @property
    def output_shape(self):
        length = conv_output_length(self.input_shape[1],
                                    self.filter_length,
                                    self.border_mode,
                                    self.subsample[0])
        return (self.input_shape[0], length, self.nb_filter)

    def get_output(self, train=False):
        X = self.get_input(train)
        X = K.expand_dims(X, -1)  # add a dimension of the right
        X = K.permute_dimensions(X, (0, 2, 1, 3))
        conv_out = K.conv2d(X, self.W, strides=self.subsample,
                            border_mode=self.border_mode,
                            dim_ordering='th')

        output = conv_out + K.reshape(self.b, (1, self.nb_filter, 1, 1))
        output = self.activation(output)
        output = K.squeeze(output, 3)  # remove the dummy 3rd dimension
        output = K.permute_dimensions(output, (0, 2, 1))
        return output

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'nb_filter': self.nb_filter,
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

    # Input shape
        4D tensor with shape:
        `(samples, channels, rows, cols)` if dim_ordering='th'
        or 4D tensor with shape:
        `(samples, rows, cols, channels)` if dim_ordering='tf'.

    # Output shape
        4D tensor with shape:
        `(samples, nb_filter, nb_row, nb_col)` if dim_ordering='th'
        or 4D tensor with shape:
        `(samples, nb_row, nb_col, nb_filter)` if dim_ordering='tf'.


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
    '''
    input_ndim = 4

    def __init__(self, nb_filter, nb_row, nb_col,
                 init='glorot_uniform', activation='linear', weights=None,
                 border_mode='valid', subsample=(1, 1), dim_ordering='th',
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None, **kwargs):

        if border_mode not in {'valid', 'same'}:
            raise Exception('Invalid border mode for Convolution2D:', border_mode)
        self.nb_filter = nb_filter
        self.nb_row = nb_row
        self.nb_col = nb_col
        self.init = initializations.get(init)
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
        self.constraints = [self.W_constraint, self.b_constraint]

        self.initial_weights = weights
        self.input = K.placeholder(ndim=4)
        super(Convolution2D, self).__init__(**kwargs)

    def build(self):
        if self.dim_ordering == 'th':
            stack_size = self.input_shape[1]
            self.W_shape = (self.nb_filter, stack_size, self.nb_row, self.nb_col)
        elif self.dim_ordering == 'tf':
            stack_size = self.input_shape[3]
            self.W_shape = (self.nb_row, self.nb_col, stack_size, self.nb_filter)
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)
        self.W = self.init(self.W_shape)
        self.b = K.zeros((self.nb_filter,))
        self.params = [self.W, self.b]
        self.regularizers = []

        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    @property
    def output_shape(self):
        input_shape = self.input_shape
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

    def get_output(self, train=False):
        X = self.get_input(train)
        conv_out = K.conv2d(X, self.W, strides=self.subsample,
                            border_mode=self.border_mode,
                            dim_ordering=self.dim_ordering,
                            image_shape=self.input_shape,
                            filter_shape=self.W_shape)
        if self.dim_ordering == 'th':
            output = conv_out + K.reshape(self.b, (1, self.nb_filter, 1, 1))
        elif self.dim_ordering == 'tf':
            output = conv_out + K.reshape(self.b, (1, 1, 1, self.nb_filter))
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)
        output = self.activation(output)
        return output

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'nb_filter': self.nb_filter,
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
                  'b_constraint': self.b_constraint.get_config() if self.b_constraint else None}
        base_config = super(Convolution2D, self).get_config()
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
        self.input = K.placeholder(ndim=3)
        self.pool_size = (pool_length, 1)
        assert border_mode in {'valid', 'same'}, 'border_mode must be in {valid, same}'
        self.border_mode = border_mode

    @property
    def output_shape(self):
        input_shape = self.input_shape
        length = conv_output_length(input_shape[1], self.pool_length,
                                    self.border_mode, self.stride)
        return (input_shape[0], length, input_shape[2])

    def _pooling_function(self, back_end, inputs, pool_size, strides,
                          border_mode, dim_ordering):
        raise NotImplementedError

    def get_output(self, train=False):
        X = self.get_input(train)
        X = K.expand_dims(X, -1)   # add dummy last dimension
        X = K.permute_dimensions(X, (0, 2, 1, 3))
        output = self._pooling_function(inputs=X, pool_size=self.pool_size,
                                        strides=self.st,
                                        border_mode=self.border_mode,
                                        dim_ordering='th')
        output = K.permute_dimensions(output, (0, 2, 1, 3))
        return K.squeeze(output, 3)  # remove dummy last dimension

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'stride': self.stride,
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
    input_ndim = 4

    def __init__(self, pool_size=(2, 2), strides=None, border_mode='valid',
                 dim_ordering='th', **kwargs):
        super(_Pooling2D, self).__init__(**kwargs)
        self.input = K.placeholder(ndim=4)
        self.pool_size = tuple(pool_size)
        if strides is None:
            strides = self.pool_size
        self.strides = tuple(strides)
        assert border_mode in {'valid', 'same'}, 'border_mode must be in {valid, same}'
        self.border_mode = border_mode
        assert dim_ordering in {'tf', 'th'}, 'dim_ordering must be in {tf, th}'
        self.dim_ordering = dim_ordering

    @property
    def output_shape(self):
        input_shape = self.input_shape
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

    def get_output(self, train=False):
        X = self.get_input(train)
        output = self._pooling_function(inputs=X, pool_size=self.pool_size,
                                        strides=self.strides,
                                        border_mode=self.border_mode,
                                        dim_ordering=self.dim_ordering)
        return output

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'pool_size': self.pool_size,
                  'border_mode': self.border_mode,
                  'strides': self.strides,
                  'dim_ordering': self.dim_ordering}
        base_config = super(_Pooling2D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class MaxPooling2D(_Pooling2D):
    '''Max pooling operation for spatial data.

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

    # Arguments
        pool_size: tuple of 2 integers,
            factors by which to downscale (vertical, horizontal).
            (2, 2) will halve the image in each dimension.
        strides: tuple of 2 integers, or None. Strides values.
        border_mode: 'valid' or 'same'.
            Note: 'same' will only work with TensorFlow for the time being.
        dim_ordering: 'th' or 'tf'. In 'th' mode, the channels dimension
            (the depth) is at index 1, in 'tf' mode is it at index 3.
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

    # Arguments
        pool_size: tuple of 2 integers,
            factors by which to downscale (vertical, horizontal).
            (2, 2) will halve the image in each dimension.
        strides: tuple of 2 integers, or None. Strides values.
        border_mode: 'valid' or 'same'.
            Note: 'same' will only work with TensorFlow for the time being.
        dim_ordering: 'th' or 'tf'. In 'th' mode, the channels dimension
            (the depth) is at index 1, in 'tf' mode is it at index 3.
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


class UpSampling1D(Layer):
    '''Repeats each temporal step `length` times along the time axis.

    # Input shape
        3D tensor with shape: `(samples, steps, features)`.

    # Output shape
        3D tensor with shape: `(samples, upsampled_steps, features)`.

    # Arguments:
        length: integer. Upsampling factor.
    '''
    input_ndim = 3

    def __init__(self, length=2, **kwargs):
        super(UpSampling1D, self).__init__(**kwargs)
        self.length = length
        self.input = K.placeholder(ndim=3)

    @property
    def output_shape(self):
        input_shape = self.input_shape
        return (input_shape[0], self.length * input_shape[1], input_shape[2])

    def get_output(self, train=False):
        X = self.get_input(train)
        output = K.concatenate([X] * self.length, axis=1)
        return output

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'length': self.length}
        base_config = super(UpSampling1D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class UpSampling2D(Layer):
    '''Repeats the rows and columns of the data
    by size[0] and size[1] respectively.

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

    # Arguments
        size: tuple of 2 integers. The upsampling factors for rows and columns.
        dim_ordering: 'th' or 'tf'.
            In 'th' mode, the channels dimension (the depth)
            is at index 1, in 'tf' mode is it at index 3.
    '''
    input_ndim = 4

    def __init__(self, size=(2, 2), dim_ordering='th', **kwargs):
        super(UpSampling2D, self).__init__(**kwargs)
        self.input = K.placeholder(ndim=4)
        self.size = tuple(size)
        assert dim_ordering in {'tf', 'th'}, 'dim_ordering must be in {tf, th}'
        self.dim_ordering = dim_ordering

    @property
    def output_shape(self):
        input_shape = self.input_shape
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

    def get_output(self, train=False):
        X = self.get_input(train)
        if self.dim_ordering == 'th':
            output = K.concatenate([X] * self.size[0], axis=2)
            output = K.concatenate([output] * self.size[1], axis=3)
        elif self.dim_ordering == 'tf':
            output = K.concatenate([X] * self.size[0], axis=1)
            output = K.concatenate([output] * self.size[1], axis=2)
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)
        return output

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'size': self.size}
        base_config = super(UpSampling2D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ZeroPadding1D(Layer):
    '''Zero-padding layer for 1D input (e.g. temporal sequence).

    # Input shape
        3D tensor with shape (samples, axis_to_pad, features)

    # Output shape
        3D tensor with shape (samples, padded_axis, features)

    # Arguments
        padding: int
            How many zeros to add at the beginning and end of
            the padding dimension (axis 1).
    '''
    input_ndim = 3

    def __init__(self, padding=1, **kwargs):
        super(ZeroPadding1D, self).__init__(**kwargs)
        self.padding = padding
        self.input = K.placeholder(ndim=3)

    @property
    def output_shape(self):
        input_shape = self.input_shape
        return (input_shape[0],
                input_shape[1] + self.padding * 2,
                input_shape[2])

    def get_output(self, train=False):
        X = self.get_input(train)
        return K.temporal_padding(X, padding=self.padding)

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'padding': self.padding}
        base_config = super(ZeroPadding1D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ZeroPadding2D(Layer):
    '''Zero-padding layer for 2D input (e.g. picture).

    # Input shape
        4D tensor with shape:
        (samples, depth, first_axis_to_pad, second_axis_to_pad)

    # Output shape
        4D tensor with shape:
        (samples, depth, first_padded_axis, second_padded_axis)

    # Arguments
        padding: tuple of int (length 2)
            How many zeros to add at the beginning and end of
            the 2 padding dimensions (axis 3 and 4).
    '''
    input_ndim = 4

    def __init__(self, padding=(1, 1), dim_ordering='th', **kwargs):
        super(ZeroPadding2D, self).__init__(**kwargs)
        self.padding = tuple(padding)
        self.input = K.placeholder(ndim=4)
        assert dim_ordering in {'tf', 'th'}, 'dim_ordering must be in {tf, th}'
        self.dim_ordering = dim_ordering

    @property
    def output_shape(self):
        input_shape = self.input_shape
        if self.dim_ordering == 'th':
            return (input_shape[0],
                    input_shape[1],
                    input_shape[2] + 2 * self.padding[0],
                    input_shape[3] + 2 * self.padding[1])
        elif self.dim_ordering == 'tf':
            return (input_shape[0],
                    input_shape[1] + 2 * self.padding[0],
                    input_shape[2] + 2 * self.padding[1],
                    input_shape[3])
        else:
            raise Exception('Invalid dim_ordering: ' + self.dim_ordering)

    def get_output(self, train=False):
        X = self.get_input(train)
        return K.spatial_2d_padding(X, padding=self.padding,
                                    dim_ordering=self.dim_ordering)

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'padding': self.padding}
        base_config = super(ZeroPadding2D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

# -*- coding: utf-8 -*-
from __future__ import absolute_import
import numpy as np

from .. import backend as K
from .. import activations, initializations
from ..layers.core import MaskedLayer


class Recurrent(MaskedLayer):
    '''Abstract base class for recurrent layers.
    Do not use in a model -- it's not a functional layer!

    All recurrent layers (GRU, LSTM, SimpleRNN) also
    follow the specifications of this class and accept
    the keyword arguments listed below.

    # Input shape
        3D tensor with shape `(nb_samples, timesteps, input_dim)`.

    # Output shape
        - if `return_sequences`: 3D tensor with shape
            `(nb_samples, timesteps, output_dim)`.
        - else, 2D tensor with shape `(nb_samples, output_dim)`.

    # Arguments
        weights: list of numpy arrays to set as initial weights.
            The list should have 3 elements, of shapes:
            `[(input_dim, output_dim), (output_dim, output_dim), (output_dim,)]`.
        return_sequences: Boolean. Whether to return the last output
            in the output sequence, or the full sequence.
        go_backwards: Boolean (default False).
            If True, rocess the input sequence backwards.
        stateful: Boolean (default False). If True, the last state
            for each sample at index i in a batch will be used as initial
            state for the sample of index i in the following batch.
        input_dim: dimensionality of the input (integer).
            This argument (or alternatively, the keyword argument `input_shape`)
            is required when using this layer as the first layer in a model.
        input_length: Length of input sequences, to be specified
            when it is constant.
            This argument is required if you are going to connect
            `Flatten` then `Dense` layers upstream
            (without it, the shape of the dense outputs cannot be computed).
            Note that if the recurrent layer is not the first layer
            in your model, you would need to specify the input Length
            at the level of the first layer
            (e.g. via the `input_shape` argument)

    # Masking
        This layer supports masking for input data with a variable number
        of timesteps. To introduce masks to your data,
        use an [Embedding](embeddings.md) layer with the `mask_zero` parameter
        set to `True`.
        **Note:** for the time being, masking is only supported with Theano.

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
                a `batch_input_size=(...)` to the first layer in your model.
                This is the expected shape of your inputs *including the batch size*.
                It should be a tuple of integers, e.g. `(32, 10, 100)`.

        To reset the states of your model, call `.reset_states()` on either
        a specific layer, or on your entire model.
    '''
    input_ndim = 3

    def __init__(self, weights=None,
                 return_sequences=False, go_backwards=False, stateful=False,
                 input_dim=None, input_length=None, **kwargs):
        self.return_sequences = return_sequences
        self.initial_weights = weights
        self.go_backwards = go_backwards
        self.stateful = stateful

        self.input_dim = input_dim
        self.input_length = input_length
        if self.input_dim:
            kwargs['input_shape'] = (self.input_length, self.input_dim)
        super(Recurrent, self).__init__(**kwargs)

    def get_output_mask(self, train=False):
        if self.return_sequences:
            return super(Recurrent, self).get_output_mask(train)
        else:
            return None

    @property
    def output_shape(self):
        input_shape = self.input_shape
        if self.return_sequences:
            return (input_shape[0], input_shape[1], self.output_dim)
        else:
            return (input_shape[0], self.output_dim)

    def step(self, x, states):
        raise NotImplementedError

    def get_initial_states(self, X):
        # build an all-zero tensor of shape (samples, output_dim)
        initial_state = K.zeros_like(X)  # (samples, timesteps, input_dim)
        initial_state = K.sum(initial_state, axis=1)  # (samples, input_dim)
        reducer = K.zeros((self.input_dim, self.output_dim))
        initial_state = K.dot(initial_state, reducer)  # (samples, output_dim)
        initial_states = [initial_state for _ in range(len(self.states))]
        return initial_states

    def get_output(self, train=False):
        # input shape: (nb_samples, time (padded with zeros), input_dim)
        X = self.get_input(train)
        assert K.ndim(X) == 3
        if K._BACKEND == 'tensorflow':
            if not self.input_shape[1]:
                raise Exception('When using TensorFlow, you should define ' +
                                'explicitely the number of timesteps of ' +
                                'your sequences. Make sure the first layer ' +
                                'has a "batch_input_shape" argument ' +
                                'including the samples axis.')

        mask = self.get_output_mask(train)
        if mask:
            # apply mask
            X *= K.cast(K.expand_dims(mask), X.dtype)
            masking = True
        else:
            masking = False

        if self.stateful:
            initial_states = self.states
        else:
            initial_states = self.get_initial_states(X)

        last_output, outputs, states = K.rnn(self.step, X, initial_states,
                                             go_backwards=self.go_backwards,
                                             masking=masking)
        if self.stateful:
            self.updates = []
            for i in range(len(states)):
                self.updates.append((self.states[i], states[i]))

        if self.return_sequences:
            return outputs
        else:
            return last_output

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "return_sequences": self.return_sequences,
                  "input_dim": self.input_dim,
                  "input_length": self.input_length,
                  "go_backwards": self.go_backwards,
                  "stateful": self.stateful}
        base_config = super(Recurrent, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class SimpleRNN(Recurrent):
    '''Fully-connected RNN where the output is to fed back to input.

    # Arguments
        output_dim: dimension of the internal projections and the final output.
        init: weight initialization function.
            Can be the name of an existing function (str),
            or a Theano function (see: [initializations](../initializations.md)).
        inner_init: initialization function of the inner cells.
        activation: activation function.
            Can be the name of an existing function (str),
            or a Theano function (see: [activations](../activations.md)).
    '''
    def __init__(self, output_dim,
                 init='glorot_uniform', inner_init='orthogonal',
                 activation='sigmoid', **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.activation = activations.get(activation)
        super(SimpleRNN, self).__init__(**kwargs)

    def build(self):
        input_shape = self.input_shape
        if self.stateful:
            self.reset_states()
        else:
            # initial states: all-zero tensor of shape (output_dim)
            self.states = [None]
        input_dim = input_shape[2]
        self.input_dim = input_dim

        self.W = self.init((input_dim, self.output_dim))
        self.U = self.inner_init((self.output_dim, self.output_dim))
        self.b = K.zeros((self.output_dim))
        self.params = [self.W, self.U, self.b]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def reset_states(self):
        assert self.stateful, 'Layer must be stateful.'
        input_shape = self.input_shape
        if not input_shape[0]:
            raise Exception('If a RNN is stateful, a complete ' +
                            'input_shape must be provided ' +
                            '(including batch size).')
        if hasattr(self, 'states'):
            K.set_value(self.states[0],
                        np.zeros((input_shape[0], self.output_dim)))
        else:
            self.states = [K.zeros((input_shape[0], self.output_dim))]

    def step(self, x, states):
        # states only contains the previous output.
        assert len(states) == 1
        prev_output = states[0]
        h = K.dot(x, self.W) + self.b
        output = self.activation(h + K.dot(prev_output, self.U))
        return output, [output]

    def get_config(self):
        config = {"output_dim": self.output_dim,
                  "init": self.init.__name__,
                  "inner_init": self.inner_init.__name__,
                  "activation": self.activation.__name__}
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

    # References
        - [On the Properties of Neural Machine Translation: Encoderâ€“Decoder Approaches](http://www.aclweb.org/anthology/W14-4012)
        - [Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling](http://arxiv.org/pdf/1412.3555v1.pdf)
    '''
    def __init__(self, output_dim,
                 init='glorot_uniform', inner_init='orthogonal',
                 activation='sigmoid', inner_activation='hard_sigmoid',
                 **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.activation = activations.get(activation)
        self.inner_activation = activations.get(inner_activation)
        super(GRU, self).__init__(**kwargs)

    def build(self):
        input_shape = self.input_shape
        input_dim = input_shape[2]
        self.input_dim = input_dim
        self.input = K.placeholder(input_shape)

        self.W_z = self.init((input_dim, self.output_dim))
        self.U_z = self.inner_init((self.output_dim, self.output_dim))
        self.b_z = K.zeros((self.output_dim,))

        self.W_r = self.init((input_dim, self.output_dim))
        self.U_r = self.inner_init((self.output_dim, self.output_dim))
        self.b_r = K.zeros((self.output_dim,))

        self.W_h = self.init((input_dim, self.output_dim))
        self.U_h = self.inner_init((self.output_dim, self.output_dim))
        self.b_h = K.zeros((self.output_dim,))

        self.params = [self.W_z, self.U_z, self.b_z,
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
        input_shape = self.input_shape
        if not input_shape[0]:
            raise Exception('If a RNN is stateful, a complete ' +
                            'input_shape must be provided ' +
                            '(including batch size).')
        if hasattr(self, 'states'):
            K.set_value(self.states[0],
                        np.zeros((input_shape[0], self.output_dim)))
        else:
            self.states = [K.zeros((input_shape[0], self.output_dim))]

    def step(self, x, states):
        assert len(states) == 1
        x_z = K.dot(x, self.W_z) + self.b_z
        x_r = K.dot(x, self.W_r) + self.b_r
        x_h = K.dot(x, self.W_h) + self.b_h

        h_tm1 = states[0]
        z = self.inner_activation(x_z + K.dot(h_tm1, self.U_z))
        r = self.inner_activation(x_r + K.dot(h_tm1, self.U_r))

        hh = self.inner_activation(x_h + K.dot(r * h_tm1, self.U_h))
        h = z * h_tm1 + (1 - z) * hh
        return h, [h]

    def get_config(self):
        config = {"output_dim": self.output_dim,
                  "init": self.init.__name__,
                  "inner_init": self.inner_init.__name__,
                  "activation": self.activation.__name__,
                  "inner_activation": self.inner_activation.__name__}
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

    # References
        - [Long short-term memory](http://deeplearning.cs.cmu.edu/pdfs/Hochreiter97_lstm.pdf) (original 1997 paper)
        - [Learning to forget: Continual prediction with LSTM](http://www.mitpressjournals.org/doi/pdf/10.1162/089976600300015015)
        - [Supervised sequence labelling with recurrent neural networks](http://www.cs.toronto.edu/~graves/preprint.pdf)
    '''
    def __init__(self, output_dim,
                 init='glorot_uniform', inner_init='orthogonal',
                 forget_bias_init='one', activation='tanh',
                 inner_activation='hard_sigmoid', **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.forget_bias_init = initializations.get(forget_bias_init)
        self.activation = activations.get(activation)
        self.inner_activation = activations.get(inner_activation)
        super(LSTM, self).__init__(**kwargs)

    def build(self):
        input_shape = self.input_shape
        input_dim = input_shape[2]
        self.input_dim = input_dim
        self.input = K.placeholder(input_shape)

        if self.stateful:
            self.reset_states()
        else:
            # initial states: 2 all-zero tensor of shape (output_dim)
            self.states = [None, None]

        self.W_i = self.init((input_dim, self.output_dim))
        self.U_i = self.inner_init((self.output_dim, self.output_dim))
        self.b_i = K.zeros((self.output_dim))

        self.W_f = self.init((input_dim, self.output_dim))
        self.U_f = self.inner_init((self.output_dim, self.output_dim))
        self.b_f = self.forget_bias_init((self.output_dim))

        self.W_c = self.init((input_dim, self.output_dim))
        self.U_c = self.inner_init((self.output_dim, self.output_dim))
        self.b_c = K.zeros((self.output_dim))

        self.W_o = self.init((input_dim, self.output_dim))
        self.U_o = self.inner_init((self.output_dim, self.output_dim))
        self.b_o = K.zeros((self.output_dim))

        self.params = [self.W_i, self.U_i, self.b_i,
                       self.W_c, self.U_c, self.b_c,
                       self.W_f, self.U_f, self.b_f,
                       self.W_o, self.U_o, self.b_o]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def reset_states(self):
        assert self.stateful, 'Layer must be stateful.'
        input_shape = self.input_shape
        if not input_shape[0]:
            raise Exception('If a RNN is stateful, a complete ' +
                            'input_shape must be provided ' +
                            '(including batch size).')
        if hasattr(self, 'states'):
            K.set_value(self.states[0],
                        np.zeros((input_shape[0], self.output_dim)))
            K.set_value(self.states[1],
                        np.zeros((input_shape[0], self.output_dim)))
        else:
            self.states = [K.zeros((input_shape[0], self.output_dim)),
                           K.zeros((input_shape[0], self.output_dim))]

    def step(self, x, states):
        assert len(states) == 2
        h_tm1 = states[0]
        c_tm1 = states[1]

        x_i = K.dot(x, self.W_i) + self.b_i
        x_f = K.dot(x, self.W_f) + self.b_f
        x_c = K.dot(x, self.W_c) + self.b_c
        x_o = K.dot(x, self.W_o) + self.b_o

        i = self.inner_activation(x_i + K.dot(h_tm1, self.U_i))
        f = self.inner_activation(x_f + K.dot(h_tm1, self.U_f))
        c = f * c_tm1 + i * self.activation(x_c + K.dot(h_tm1, self.U_c))
        o = self.inner_activation(x_o + K.dot(h_tm1, self.U_o))
        h = o * self.activation(c)
        return h, [h, c]

    def get_config(self):
        config = {"output_dim": self.output_dim,
                  "init": self.init.__name__,
                  "inner_init": self.inner_init.__name__,
                  "forget_bias_init": self.forget_bias_init.__name__,
                  "activation": self.activation.__name__,
                  "inner_activation": self.inner_activation.__name__}
        base_config = super(LSTM, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from collections import OrderedDict
from .. import backend as K
from ..layers.core import Layer, Merge, Siamese, SiameseHead
from six.moves import range


class Sequential(Layer):
    '''The Sequential container is a linear stack of layers.
    Apart from the `add` methods and the `layers` constructor argument,
    the API is identical to that of the `Layer` class.

    This class is also the basis for the `keras.models.Sequential` model.

    # Arguments
        layers: list of layers to be added to the container.
    '''
    def __init__(self, layers=[]):
        self.layers = []
        self.layer_cache = {}
        for layer in layers:
            self.add(layer)

    def __call__(self, X, mask=None, train=False):
        #turn off layer cache temporarily
        tmp_cache_enabled = self.cache_enabled
        self.cache_enabled = False
        #recursively search for a layer which is not a Sequential model
        layer = self
        while issubclass(layer.__class__, Sequential):
            layer = layer.layers[0]
        # set temporary input to first layer
        tmp_input = layer.get_input
        tmp_mask = None
        layer.get_input = lambda _: X
        if hasattr(layer, 'get_input_mask'):
            tmp_mask = layer.get_input_mask
            layer.get_input_mask = lambda _: mask
        Y = self.get_output(train=train)
        # return input from first layer to what it was
        layer.get_input = tmp_input
        if hasattr(layer, 'get_input_mask'):
            layer.get_input_mask = tmp_mask
        self.cache_enabled = tmp_cache_enabled
        return Y

    @property
    def cache_enabled(self):
        return  self._cache_enabled

    @cache_enabled.setter
    def cache_enabled(self, value):
        self._cache_enabled = value
        for l in self.layers:
            l.cache_enabled = value

    def set_previous(self, layer):
        self.layers[0].previous = layer

    def add(self, layer):
        layer.layer_cache = self.layer_cache
        self.layers.append(layer)
        if len(self.layers) > 1:
            self.layers[-1].set_previous(self.layers[-2])
            if not hasattr(self.layers[0], 'input'):
                self.set_input()

    @property
    def params(self):
        params = []
        for l in self.layers:
            if l.trainable:
                params += l.get_params()[0]
        return params

    @property
    def regularizers(self):
        regularizers = []
        for l in self.layers:
            if l.trainable:
                regularizers += l.get_params()[1]
        return regularizers

    @property
    def constraints(self):
        constraints = []
        for l in self.layers:
            if l.trainable:
                constraints += l.get_params()[2]
        return constraints

    @property
    def updates(self):
        updates = []
        for l in self.layers:
            if l.trainable:
                updates += l.get_params()[3]
        return updates

    @property
    def state_updates(self):
        """
        Returns the `updates` from all layers in the sequence that are
        stateful.  This is useful for separating _training_ updates and
        _prediction_ updates for when we need to update a layers internal state
        during a stateful prediction.
        """
        state_updates = []
        for l in self.layers:
            if getattr(l, 'stateful', False):
                state_updates += l.get_params()[3]
        return state_updates

    def reset_states(self):
        for l in self.layers:
            if hasattr(l, 'reset_states') and getattr(l, 'stateful', False):
                l.reset_states()

    @property
    def output_shape(self):
        return self.layers[-1].output_shape

    def get_output(self, train=False):
        return self.layers[-1].get_output(train)

    def set_input(self):
        for l in self.layers:
            if hasattr(l, 'input'):
                ndim = K.ndim(l.input)
                self.layers[0].input = K.placeholder(ndim=ndim)
                break

    def get_input(self, train=False):
        if not hasattr(self.layers[0], 'input'):
            self.set_input()
        return self.layers[0].get_input(train)

    @property
    def input_shape(self):
        return self.layers[0].input_shape

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
        return {'name': self.__class__.__name__,
                'layers': [layer.get_config() for layer in self.layers]}

    def count_params(self):
        return sum([layer.count_params() for layer in self.layers])


class Graph(Layer):
    '''Implement a NN graph with arbitrary layer connections,
    arbitrary number of inputs and arbitrary number of outputs.

    This class is also the basis for the `keras.models.Graph` model.

    Note: `Graph` can only be used as a layer
    (connect, input, get_input, get_output)
    when it has exactly one input and one output.
    '''
    def __init__(self):
        self.namespace = set()  # strings
        self.nodes = OrderedDict()  # layer-like
        self.inputs = {}  # layer-like
        self.input_order = []  # strings
        self.outputs = {}  # layer-like
        self.output_order = []  # strings
        self.input_config = []  # dicts
        self.output_config = []  # dicts
        self.node_config = []  # dicts
        self.layer_cache = {}

    @property
    def nb_input(self):
        return len(self.inputs)

    @property
    def nb_output(self):
        return len(self.outputs)

    @property
    def params(self):
        params = []
        for l in self.nodes.values():
            if l.trainable:
                params += l.get_params()[0]
        return params

    @property
    def regularizers(self):
        regularizers = []
        for l in self.nodes.values():
            if l.trainable:
                regularizers += l.get_params()[1]
        return regularizers

    @property
    def constraints(self):
        constraints = []
        for l in self.nodes.values():
            if l.trainable:
                constraints += l.get_params()[2]
        return constraints

    @property
    def updates(self):
        updates = []
        for l in self.nodes.values():
            if l.trainable:
                updates += l.get_params()[3]
        return updates

    @property
    def state_updates(self):
        """
        Returns the `updates` from all nodes in that graph for nodes that are
        stateful.  This is useful for separating _training_ updates and
        _prediction_ updates for when we need to update a layers internal state
        during a stateful prediction.
        """
        state_updates = []
        for l in self.nodes.values():
            if getattr(l, 'stateful', False):
                state_updates += l.get_params()[3]
        return state_updates

    def reset_states(self):
        for l in self.nodes.values():
            if hasattr(l, 'reset_states') and getattr(l, 'stateful', False):
                l.reset_states()

    def set_previous(self, layer, connection_map={}):
        if self.nb_input != layer.nb_output:
            raise Exception('Cannot connect layers: '
                            'input count does not match output count.')
        if self.nb_input == 1:
            self.inputs[self.input_order[0]].set_previous(layer)
        else:
            if not connection_map:
                raise Exception('Cannot attach multi-input layer: '
                                'no connection_map provided.')
            for k, v in connection_map.items():
                if k in self.inputs and v in layer.outputs:
                    self.inputs[k].set_previous(layer.outputs[v])
                else:
                    raise Exception('Invalid connection map.')

    def get_input(self, train=False):
        if len(self.inputs) == len(self.outputs) == 1:
            return self.inputs[self.input_order[0]].get_input(train)
        else:
            return dict([(k, v.get_input(train)) for k, v in self.inputs.items()])

    @property
    def input(self):
        return self.get_input()

    @property
    def output_shape(self):
        if self.nb_output == 1:
            # return tuple
            return self.outputs[self.output_order[0]].output_shape
        else:
            # return dictionary mapping output names to shape tuples
            return dict([(k, v.output_shape) for k, v in self.outputs.items()])

    def get_output(self, train=False):
        if len(self.inputs) == len(self.outputs) == 1:
            return self.outputs[self.output_order[0]].get_output(train)
        else:
            return dict([(k, v.get_output(train)) for k, v in self.outputs.items()])

    def add_input(self, name, input_shape=None,
                  batch_input_shape=None, dtype='float'):
        '''Add an input to the graph.

        # Arguments:
            name: string. The name of the new input. Must be unique in the graph.
            input_shape: a tuple of integers, the expected shape of the input samples.
                Does not include the batch size.
            batch_input_shape: a tuple of integers, the expected shape of the
                whole input batch, including the batch size.
            dtype: 'float' or 'int'.
        '''
        if name in self.namespace:
            raise Exception('Duplicate node identifier: ' + name)
        self.namespace.add(name)
        self.input_order.append(name)
        layer = Layer()  # empty layer
        if input_shape:
            layer.set_input_shape((None,) + tuple(input_shape))
        elif batch_input_shape:
            layer.set_input_shape(batch_input_shape)
        if dtype == 'float':
            layer.input = K.placeholder(shape=layer.input_shape, name=name)
        else:
            if len(input_shape) == 1:
                layer.input = K.placeholder(shape=layer.input_shape,
                                            dtype='int32',
                                            name=name)
            else:
                raise Exception('Type "int" can only be used with ndim==2 (Embedding).')
        self.inputs[name] = layer
        self.input_config.append({'name': name,
                                  'input_shape': input_shape,
                                  'dtype': dtype})

    def add_node(self, layer, name, input=None, inputs=[],
                 merge_mode='concat', concat_axis=-1, dot_axes=-1,
                 create_output=False):
        '''Add a node in the graph. It can be connected to multiple
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
            dot_axes: when `merge_mode='dot'`, this is the contraction axes
                specification; see the `Merge layer for details.
            create_output: boolean. Set this to `True` if you want the output
                of your node to be an output of the graph.
        '''
        if name in self.namespace:
            raise Exception('Duplicate node identifier: ' + name)
        if input:
            if input not in self.namespace:
                raise Exception('Unknown node/input identifier: ' + input)
            if input in self.nodes:
                layer.set_previous(self.nodes[input])
            elif input in self.inputs:
                layer.set_previous(self.inputs[input])
        if inputs:
            to_merge = []
            for n in inputs:
                if n in self.nodes:
                    to_merge.append(self.nodes[n])
                elif n in self.inputs:
                    to_merge.append(self.inputs[n])
                else:
                    raise Exception('Unknown identifier: ' + n)
            merge = Merge(to_merge, mode=merge_mode,
                          concat_axis=concat_axis, dot_axes=dot_axes)
            layer.set_previous(merge)

        self.namespace.add(name)
        layer.layer_cache = self.layer_cache
        self.nodes[name] = layer
        self.node_config.append({'name': name,
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

        Supposed, for instance, that you want to apply one same `Dense`
        layer after to the output of two different nodes.
        You can then add the `Dense` layer as a shared node.

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
        if name in self.namespace:
            raise Exception('Duplicate node identifier: ' + name)
        for o in outputs:
            if o in self.namespace:
                raise Exception('Duplicate node identifier: ' + o)
        if merge_mode:
            if merge_mode not in {'sum', 'ave', 'mul', 'dot', 'cos', 'concat', 'join'}:
                raise Exception('Invalid merge mode')
        layers = []
        for i in range(len(inputs)):
            input = inputs[i]
            if input in self.nodes:
                n = self.nodes[input]
                if n.__class__.__name__ == 'Siamese':
                    if n.merge_mode is None:
                        for j in range(len(n.inputs)):
                            sh = SiameseHead(j)
                            sh.previous = n
                            layers.append(sh)
                    else:
                        layers.append(n)
                else:
                    layers.append(n)
            elif input in self.inputs:
                n = self.inputs[input]
                layers.append(n)
            else:
                raise Exception('Unknown identifier: ' + input)
        s = Siamese(layer, layers, merge_mode,
                    concat_axis=concat_axis,
                    dot_axes=dot_axes,
                    is_graph=True)
        self.namespace.add(name)
        self.nodes[name] = s
        self.node_config.append({'name': name,
                                 'inputs': inputs,
                                 'merge_mode': merge_mode,
                                 'concat_axis': concat_axis,
                                 'dot_axes': dot_axes,
                                 'create_output': create_output if merge_mode else False})
        if not merge_mode:
            for i in range(len(outputs)):
                sh = SiameseHead(i)
                sh.previous = s
                sh_name = outputs[i]
                self.namespace.add(sh_name)
                self.nodes[sh_name] = sh
                self.node_config.append({'name': sh_name,
                                         'inputs': [s],
                                         'create_output': create_output})
                if create_output:
                    self.add_output(sh_name, input=sh_name)

        if create_output and merge_mode:
            if merge_mode == 'join':
                raise Exception('Output can not be of type OrderedDict')
            self.add_output(name, input=name)

    def add_output(self, name, input=None, inputs=[],
                   merge_mode='concat', concat_axis=-1, dot_axes=-1):
        '''Add an output to the graph.

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
            dot_axes: when `merge_mode='dot'`, this is the contraction axes
                specification; see the `Merge layer for details.
        '''
        if name in self.output_order:
            raise Exception('Duplicate output identifier: ' + name)
        if input:
            if input not in self.namespace:
                raise Exception('Unknown node/input identifier: ' + input)
            if input in self.nodes:
                self.outputs[name] = self.nodes[input]
            elif input in self.inputs:
                self.outputs[name] = self.inputs[input]
        if inputs:
            to_merge = []
            for n in inputs:
                if n not in self.nodes:
                    raise Exception('Unknown identifier: ' + n)
                to_merge.append(self.nodes[n])
            merge = Merge(to_merge, mode=merge_mode,
                          concat_axis=concat_axis, dot_axes=dot_axes)
            self.outputs[name] = merge

        self.output_order.append(name)
        self.output_config.append({'name': name,
                                   'input': input,
                                   'inputs': inputs,
                                   'merge_mode': merge_mode,
                                   'concat_axis': concat_axis,
                                   'dot_axes': dot_axes})

    def get_config(self):
        return {'name': self.__class__.__name__,
                'input_config': self.input_config,
                'node_config': self.node_config,
                'output_config': self.output_config,
                'input_order': self.input_order,
                'output_order': self.output_order,
                'nodes': dict([(c['name'], self.nodes[c['name']].get_config()) for c in self.node_config])}

    def count_params(self):
        return sum([layer.count_params() for layer in self.nodes.values()])

    def get_weights(self):
        weights = []
        for layer in self.nodes.values():
            weights += layer.get_weights()
        return weights

    def set_weights(self, weights):
        for layer in self.nodes.values():
            nb_param = len(layer.get_weights())
            layer.set_weights(weights[:nb_param])
            weights = weights[nb_param:]


# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division

import numpy as np

from collections import OrderedDict
import copy
from six.moves import zip

from .. import backend as K
from .. import activations, initializations, regularizers, constraints
from ..regularizers import ActivityRegularizer

import marshal
import types
import sys


class Layer(object):
    '''Abstract base layer class.

    All Keras layers accept certain keyword arguments:

        trainable: boolean. Set to "False" before model compilation
            to freeze layer weights (they won't be updated further
            during training).
        input_shape: a tuple of integers specifying the expected shape
            of the input samples. Does not includes the batch size.
            (e.g. `(100,)` for 100-dimensional inputs).
        batch_input_shape: a tuple of integers specifying the expected
            shape of a batch of input samples. Includes the batch size
            (e.g. `(32, 100)` for a batch of 32 100-dimensional inputs).
    '''
    def __init__(self, **kwargs):
        allowed_kwargs = {'input_shape',
                          'trainable',
                          'batch_input_shape',
                          'cache_enabled'}
        for kwarg in kwargs:
            assert kwarg in allowed_kwargs, "Keyword argument not understood: " + kwarg
        if 'input_shape' in kwargs:
            self.set_input_shape((None,) + tuple(kwargs['input_shape']))
        if 'batch_input_shape' in kwargs:
            self.set_input_shape(tuple(kwargs['batch_input_shape']))
        if 'trainable' in kwargs:
            self._trainable = kwargs['trainable']
        if not hasattr(self, 'params'):
            self.params = []
        self.cache_enabled = True
        if 'cache_enabled' in kwargs:
            self._cache_enabled = kwargs['cache_enabled']

    @property
    def cache_enabled(self):
        return self._cache_enabled

    @cache_enabled.setter
    def cache_enabled(self, value):
        self._cache_enabled = value

    def __call__(self, X, mask=None, train=False):
        # set temporary input
        tmp_input = self.get_input
        tmp_mask = None
        if hasattr(self, 'get_input_mask'):
            tmp_mask = self.get_input_mask
            self.get_input_mask = lambda _: mask
        self.get_input = lambda _: X
        Y = self.get_output(train=train)
        # return input to what it was
        if hasattr(self, 'get_input_mask'):
            self.get_input_mask = tmp_mask
        self.get_input = tmp_input
        return Y

    def set_previous(self, layer, connection_map={}):
        '''Connect a layer to its parent in the computational graph.
        '''
        assert self.nb_input == layer.nb_output == 1, "Cannot connect layers: input count and output count should be 1."
        if hasattr(self, 'input_ndim'):
            assert self.input_ndim == len(layer.output_shape), "Incompatible shapes: layer expected input with ndim=" +\
                str(self.input_ndim) + " but previous layer has output_shape " + str(layer.output_shape)
        if layer.get_output_mask() is not None:
            assert self.supports_masked_input(), "Cannot connect non-masking layer to layer with masked output"
        self.previous = layer
        self.build()

    def build(self):
        '''Instantiation of layer weights.

        Called after `set_previous`, or after `set_input_shape`,
        once the layer has a defined input shape.
        Must be implemented on all layers that have weights.
        '''
        pass

    @property
    def trainable(self):
        if hasattr(self, '_trainable'):
            return self._trainable
        else:
            return True

    @trainable.setter
    def trainable(self, value):
        self._trainable = value

    @property
    def nb_input(self):
        return 1

    @property
    def nb_output(self):
        return 1

    @property
    def input_shape(self):
        # if layer is not connected (e.g. input layer),
        # input shape can be set manually via _input_shape attribute.
        if hasattr(self, 'previous'):
            return self.previous.output_shape
        elif hasattr(self, '_input_shape'):
            return self._input_shape
        else:
            raise Exception('Layer is not connected. Did you forget to set "input_shape"?')

    def set_input_shape(self, input_shape):
        if type(input_shape) not in [tuple, list]:
            raise Exception('Invalid input shape - input_shape should be a tuple of int.')
        input_shape = tuple(input_shape)
        if hasattr(self, 'input_ndim') and self.input_ndim:
            if self.input_ndim != len(input_shape):
                raise Exception('Invalid input shape - Layer expects input ndim=' +
                                str(self.input_ndim) +
                                ', was provided with input shape ' + str(input_shape))
        self._input_shape = input_shape
        self.input = K.placeholder(shape=self._input_shape)
        self.build()

    @property
    def output_shape(self):
        # default assumption: tensor shape unchanged.
        return self.input_shape

    def get_output(self, train=False):
        return self.get_input(train)

    def get_input(self, train=False):
        if hasattr(self, 'previous'):
            # to avoid redundant computations,
            # layer outputs are cached when possible.
            if hasattr(self, 'layer_cache') and self.cache_enabled:
                previous_layer_id = '%s_%s' % (id(self.previous), train)
                if previous_layer_id in self.layer_cache:
                    return self.layer_cache[previous_layer_id]
            previous_output = self.previous.get_output(train=train)
            if hasattr(self, 'layer_cache') and self.cache_enabled:
                previous_layer_id = '%s_%s' % (id(self.previous), train)
                self.layer_cache[previous_layer_id] = previous_output
            return previous_output
        elif hasattr(self, 'input'):
            return self.input
        else:
            raise Exception('Layer is not connected' +
                            'and is not an input layer.')

    def supports_masked_input(self):
        '''Whether or not this layer respects the output mask of its previous
        layer in its calculations.
        If you try to attach a layer that does *not* support masked_input to
        a layer that gives a non-None output_mask(), an error will be raised.
        '''
        return False

    def get_output_mask(self, train=None):
        '''For some models (such as RNNs) you want a way of being able to mark
        some output data-points as "masked",
        so they are not used in future calculations.
        In such a model, get_output_mask() should return a mask
        of one less dimension than get_output()
        (so if get_output is (nb_samples, nb_timesteps, nb_dimensions),
        then the mask is (nb_samples, nb_timesteps),
        with a one for every unmasked datapoint,
        and a zero for every masked one.

        If there is *no* masking then it shall return None.
        For instance if you attach an Activation layer (they support masking)
        to a layer with an output_mask, then that Activation shall
        also have an output_mask.
        If you attach it to a layer with no such mask,
        then the Activation's get_output_mask shall return None.

        Some layers have an output_mask even if their input is unmasked,
        notably Embedding which can turn the entry "0" into
        a mask.
        '''
        return None

    def set_weights(self, weights):
        '''Set the weights of the layer.

        weights: a list of numpy arrays. The number
            of arrays and their shape must match
            number of the dimensions of the weights
            of the layer (i.e. it should match the
            output of `get_weights`).
        '''
        assert len(self.params) == len(weights), 'Provided weight array does not match layer weights (' + \
            str(len(self.params)) + ' layer params vs. ' + str(len(weights)) + ' provided weights)'
        for p, w in zip(self.params, weights):
            if K.get_value(p).shape != w.shape:
                raise Exception("Layer shape %s not compatible with weight shape %s." % (K.get_value(p).shape, w.shape))
            K.set_value(p, w)

    def get_weights(self):
        '''Return the weights of the layer,
        as a list of numpy arrays.
        '''
        weights = []
        for p in self.params:
            weights.append(K.get_value(p))
        return weights

    def get_config(self):
        '''Return the parameters of the layer, as a dictionary.
        '''
        config = {"name": self.__class__.__name__}
        if hasattr(self, '_input_shape'):
            config['input_shape'] = self._input_shape[1:]
        if hasattr(self, '_trainable'):
            config['trainable'] = self._trainable
        config['cache_enabled'] =  self.cache_enabled
        return config

    def get_params(self):
        consts = []
        updates = []

        if hasattr(self, 'regularizers'):
            regularizers = self.regularizers
        else:
            regularizers = []

        if hasattr(self, 'constraints') and len(self.constraints) == len(self.params):
            for c in self.constraints:
                if c:
                    consts.append(c)
                else:
                    consts.append(constraints.identity())
        elif hasattr(self, 'constraint') and self.constraint:
            consts += [self.constraint for _ in range(len(self.params))]
        else:
            consts += [constraints.identity() for _ in range(len(self.params))]

        if hasattr(self, 'updates') and self.updates:
            updates += self.updates

        return self.params, regularizers, consts, updates

    def count_params(self):
        '''Return the total number of floats (or ints)
        composing the weights of the layer.
        '''
        return sum([K.count_params(p) for p in self.params])

class MaskedLayer(Layer):
    '''If your layer trivially supports masking
    (by simply copying the input mask to the output),
    then subclass MaskedLayer instead of Layer,
    and make sure that you incorporate the input mask
    into your calculation of get_output().
    '''
    def supports_masked_input(self):
        return True

    def get_input_mask(self, train=False):
        if hasattr(self, 'previous'):
            return self.previous.get_output_mask(train)
        else:
            return None

    def get_output_mask(self, train=False):
        ''' The default output mask is just the input mask unchanged.
        Override this in your own implementations if,
        for instance, you are reshaping the input'''
        return self.get_input_mask(train)


class Masking(MaskedLayer):
    '''Mask an input sequence by using a mask value to identify padding.

    This layer copies the input to the output layer with identified padding
    replaced with 0s and creates an output mask in the process.

    At each timestep, if the values all equal `mask_value`,
    then the corresponding mask value for the timestep is 0 (skipped),
    otherwise it is 1.
    '''
    def __init__(self, mask_value=0., **kwargs):
        super(Masking, self).__init__(**kwargs)
        self.mask_value = mask_value
        self.input = K.placeholder(ndim=3)

    def get_output_mask(self, train=False):
        if K._BACKEND == "tensorflow":
            raise Exception("Masking is Theano-only for the time being.")
        X = self.get_input(train)
        return K.any(K.ones_like(X) * (1. - K.equal(X, self.mask_value)),
                     axis=-1)

    def get_output(self, train=False):
        X = self.get_input(train)
        return X * K.any((1. - K.equal(X, self.mask_value)),
                         axis=-1, keepdims=True)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "mask_value": self.mask_value}
        base_config = super(Masking, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class TimeDistributedMerge(Layer):
    '''Sum/multiply/average over the outputs of a TimeDistributed layer.

    # Input shape
        3D tensor with shape: `(samples, steps, features)`.

    # Output shape
        2D tensor with shape: `(samples, features)`.

    # Arguments
        mode: one of {'sum', 'mul', 'ave'}
    '''
    input_ndim = 3

    def __init__(self, mode='sum', **kwargs):
        super(TimeDistributedMerge, self).__init__(**kwargs)
        self.mode = mode
        self.params = []
        self.regularizers = []
        self.constraints = []
        self.updates = []

    @property
    def output_shape(self):
        return (None, self.input_shape[2])

    def get_output(self, train=False):
        X = self.get_input(train)
        if self.mode == 'ave':
            s = K.mean(X, axis=1)
            return s
        if self.mode == 'sum':
            s = K.sum(X, axis=1)
            return s
        elif self.mode == 'mul':
            s = K.prod(X, axis=1)
            return s
        else:
            raise Exception('Unknown merge mode')

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "mode": self.mode}
        base_config = super(TimeDistributedMerge, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Merge(Layer):
    '''Merge the output of a list of layers or containers into a single tensor.

    # Arguments
        mode: one of {sum, mul, concat, ave, dot}.
            sum: sum the outputs (shapes must match)
            mul: multiply the outputs element-wise (shapes must match)
            concat: concatenate the outputs along the axis specified by `concat_axis`
            ave: average the outputs (shapes must match)
        concat_axis: axis to use in `concat` mode.
        dot_axes: axis or axes to use in `dot` mode
            (see [the Numpy documentation](http://docs.scipy.org/doc/numpy-1.10.1/reference/generated/numpy.tensordot.html) for more details).

    # TensorFlow warning
        `dot` mode only works with Theano for the time being.

    # Examples

    ```python
    left = Sequential()
    left.add(Dense(50, input_shape=(784,)))
    left.add(Activation('relu'))

    right = Sequential()
    right.add(Dense(50, input_shape=(784,)))
    right.add(Activation('relu'))

    model = Sequential()
    model.add(Merge([left, right], mode='sum'))

    model.add(Dense(10))
    model.add(Activation('softmax'))

    model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

    model.fit([X_train, X_train], Y_train, batch_size=128, nb_epoch=20,
              validation_data=([X_test, X_test], Y_test))
    ```
    '''
    def __init__(self, layers, mode='sum', concat_axis=-1, dot_axes=-1):
        if len(layers) < 2:
            raise Exception('Please specify two or more input layers '
                            '(or containers) to merge')

        if mode not in {'sum', 'mul', 'concat', 'ave', 'join', 'cos', 'dot'}:
            raise Exception('Invalid merge mode: ' + str(mode))

        if mode in {'sum', 'mul', 'ave', 'cos'}:
            input_shapes = set([l.output_shape for l in layers])
            if len(input_shapes) > 1:
                raise Exception('Only layers of same output shape can '
                                'be merged using ' + mode + ' mode. ' +
                                'Layer shapes: %s' % ([l.output_shape for l in layers]))
        if mode in {'cos', 'dot'}:
            if K._BACKEND != 'theano':
                raise Exception('"' + mode + '" merge mode will only work with Theano.')

            if len(layers) > 2:
                raise Exception(mode + ' merge takes exactly 2 layers')
            shape1 = layers[0].output_shape
            shape2 = layers[1].output_shape
            n1 = len(shape1)
            n2 = len(shape2)
            if mode == 'dot':
                if type(dot_axes) == int:
                    if dot_axes < 0:
                        dot_axes = [range(dot_axes % n1, n1), range(dot_axes % n2, n2)]
                    else:
                        dot_axes = [range(n1 - dot_axes, n2), range(1, dot_axes + 1)]
                if type(dot_axes) not in [list, tuple]:
                    raise Exception('Invalid type for dot_axes - should be a list.')
                if len(dot_axes) != 2:
                    raise Exception('Invalid format for dot_axes - should contain two elements.')
                if type(dot_axes[0]) not in [list, tuple, range] or type(dot_axes[1]) not in [list, tuple, range]:
                    raise Exception('Invalid format for dot_axes - list elements should have type "list" or "tuple".')
                for i in range(len(dot_axes[0])):
                    if shape1[dot_axes[0][i]] != shape2[dot_axes[1][i]]:
                        raise Exception('Dimension incompatibility using dot mode: ' +
                                        '%s != %s. ' % (shape1[dot_axes[0][i]], shape2[dot_axes[1][i]]) +
                                        'Layer shapes: %s, %s' % (shape1, shape2))
        elif mode == 'concat':
            input_shapes = set()
            for l in layers:
                oshape = list(l.output_shape)
                oshape.pop(concat_axis)
                oshape = tuple(oshape)
                input_shapes.add(oshape)
            if len(input_shapes) > 1:
                raise Exception('"concat" mode can only merge layers with matching ' +
                                'output shapes except for the concat axis. ' +
                                'Layer shapes: %s' % ([l.output_shape for l in layers]))
        self.mode = mode
        self.concat_axis = concat_axis
        self.dot_axes = dot_axes
        self.layers = layers
        self.params = []
        self.regularizers = []
        self.constraints = []
        self.updates = []
        for l in self.layers:
            params, regs, consts, updates = l.get_params()
            self.regularizers += regs
            self.updates += updates
            # params and constraints have the same size
            for p, c in zip(params, consts):
                if p not in self.params:
                    self.params.append(p)
                    self.constraints.append(c)

    @property
    def output_shape(self):
        input_shapes = [layer.output_shape for layer in self.layers]
        if self.mode in ['sum', 'mul', 'ave']:
            return input_shapes[0]
        elif self.mode == 'concat':
            output_shape = list(input_shapes[0])
            for shape in input_shapes[1:]:
                output_shape[self.concat_axis] += shape[self.concat_axis]
            return tuple(output_shape)
        elif self.mode == 'join':
            return None
        elif self.mode == 'dot':
            shape1 = list(input_shapes[0])
            shape2 = list(input_shapes[1])
            dot_axes = []
            for axes in self.dot_axes:
                dot_axes.append([index-1 for index in axes])
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

    def get_params(self):
        return self.params, self.regularizers, self.constraints, self.updates

    def get_output(self, train=False):
        if self.mode == 'sum' or self.mode == 'ave':
            s = self.layers[0].get_output(train)
            for i in range(1, len(self.layers)):
                s += self.layers[i].get_output(train)
            if self.mode == 'ave':
                s /= len(self.layers)
            return s
        elif self.mode == 'concat':
            inputs = [self.layers[i].get_output(train) for i in range(len(self.layers))]
            return K.concatenate(inputs, axis=self.concat_axis)
        elif self.mode == 'join':
            inputs = OrderedDict()
            for i in range(len(self.layers)):
                X = self.layers[i].get_output(train)
                if X.name is None:
                    raise ValueError('merge_mode="join" only works with named inputs')
                else:
                    inputs[X.name] = X
            return inputs
        elif self.mode == 'mul':
            s = self.layers[0].get_output(train)
            for i in range(1, len(self.layers)):
                s *= self.layers[i].get_output(train)
            return s
        elif self.mode == 'dot':
            if K._BACKEND != 'theano':
                raise Exception('"dot" merge mode will only work with Theano.')
            from theano import tensor as T
            l1 = self.layers[0].get_output(train)
            l2 = self.layers[1].get_output(train)
            output = T.batched_tensordot(l1, l2, self.dot_axes)
            output_shape = list(self.output_shape)
            output_shape[0] = l1.shape[0]
            output = output.reshape(tuple(output_shape))
            return output
        elif self.mode == 'cos':
            if K._BACKEND != 'theano':
                raise Exception('"dot" merge mode will only work with Theano.')
            import theano
            l1 = self.layers[0].get_output(train)
            l2 = self.layers[1].get_output(train)
            output = T.batched_tensordot(l1, l2, self.dot_axes) / T.sqrt(T.batched_tensordot(l1, l1, self.dot_axes) * T.batched_tensordot(l2, l2, self.dot_axes))
            output = output.dimshuffle((0, 'x'))
            return output
        else:
            raise Exception('Unknown merge mode')

    def get_input(self, train=False):
        res = []
        for i in range(len(self.layers)):
            o = self.layers[i].get_input(train)
            if not type(o) == list:
                o = [o]
            for output in o:
                if output not in res:
                    res.append(output)
        return res

    @property
    def input(self):
        return self.get_input()

    def supports_masked_input(self):
        return False

    def get_output_mask(self, train=None):
        return None

    def get_weights(self):
        weights = []
        for l in self.layers:
            weights += l.get_weights()
        return weights

    def set_weights(self, weights):
        for i in range(len(self.layers)):
            nb_param = len(self.layers[i].params)
            self.layers[i].set_weights(weights[:nb_param])
            weights = weights[nb_param:]

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'layers': [l.get_config() for l in self.layers],
                  'mode': self.mode,
                  'concat_axis': self.concat_axis,
                  'dot_axes': self.dot_axes}
        base_config = super(Merge, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Dropout(MaskedLayer):
    '''Apply Dropout to the input. Dropout consists in randomly setting
    a fraction `p` of input units to 0 at each update during training time,
    which helps prevent overfitting.

    # Arguments
        p: float between 0 and 1. Fraction of the input units to drop.

    # References
        - [Dropout: A Simple Way to Prevent Neural Networks from Overfitting](http://www.cs.toronto.edu/~rsalakhu/papers/srivastava14a.pdf)
    '''
    def __init__(self, p, **kwargs):
        super(Dropout, self).__init__(**kwargs)
        self.p = p

    def get_output(self, train=False):
        X = self.get_input(train)
        if self.p > 0.:
            if train:
                X = K.dropout(X, level=self.p)
        return X

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'p': self.p}
        base_config = super(Dropout, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Activation(MaskedLayer):
    '''Apply an activation function to an output.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as input.

    # Arguments:
        activation: name of activation function to use
            (see: [activations](../activations.md)),
            or alternatively, a Theano or TensorFlow operation.
    '''
    def __init__(self, activation, **kwargs):
        super(Activation, self).__init__(**kwargs)
        self.activation = activations.get(activation)

    def get_output(self, train=False):
        X = self.get_input(train)
        return self.activation(X)

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'activation': self.activation.__name__}
        base_config = super(Activation, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Reshape(Layer):
    '''Reshape an output to a certain shape.

    # Input shape
        Arbitrary, although all dimensions in the input shaped must be fixed.
        Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        `(batch_size,) + dims`

    # Arguments
        dims: target shape. Tuple of integers,
            does not include the samples dimension (batch size).
    '''
    def __init__(self, dims, **kwargs):
        super(Reshape, self).__init__(**kwargs)
        self.dims = tuple(dims)

    @property
    def output_shape(self):
        return (self.input_shape[0],) + self.dims

    def get_output(self, train=False):
        X = self.get_input(train)
        return K.reshape(X, (-1,) + self.dims)

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'dims': self.dims}
        base_config = super(Reshape, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Permute(Layer):
    '''Permute the dimensions of the input according to a given pattern.

    Useful for e.g. connecting RNNs and convnets together.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same as the input shape, but with the dimensions re-ordered according
        to the specified pattern.

    # Arguments
        dims: Tuple of integers. Permutation pattern, does not include the
            samples dimension. Indexing starts at 1.
            For instance, `(2, 1)` permutes the first and second dimension
            of the input.
    '''
    def __init__(self, dims, **kwargs):
        super(Permute, self).__init__(**kwargs)
        self.dims = tuple(dims)

    @property
    def output_shape(self):
        input_shape = list(self.input_shape)
        output_shape = copy.copy(input_shape)
        for i, dim in enumerate(self.dims):
            target_dim = input_shape[dim]
            output_shape[i+1] = target_dim
        return tuple(output_shape)

    def get_output(self, train=False):
        X = self.get_input(train)
        return K.permute_dimensions(X, (0,) + self.dims)

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'dims': self.dims}
        base_config = super(Permute, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Flatten(Layer):
    '''Flatten the input. Does not affect the batch size.

    # Input shape
        Arbitrary, although all dimensions in the input shaped must be fixed.
        Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        `(batch_size,)`
    '''
    def __init__(self, **kwargs):
        super(Flatten, self).__init__(**kwargs)

    @property
    def output_shape(self):
        input_shape = self.input_shape
        return (input_shape[0], np.prod(input_shape[1:]))

    def get_output(self, train=False):
        X = self.get_input(train)
        return K.flatten(X)


class RepeatVector(Layer):
    '''Repeat the input n times.

    # Input shape
        2D tensor of shape `(nb_samples, features)`.

    # Output shape
        3D tensor of shape `(nb_samples, n, features)`.

    # Arguments
        n: integer, repetition factor.
    '''
    def __init__(self, n, **kwargs):
        super(RepeatVector, self).__init__(**kwargs)
        self.n = n

    @property
    def output_shape(self):
        input_shape = self.input_shape
        return (input_shape[0], self.n, input_shape[1])

    def get_output(self, train=False):
        X = self.get_input(train)
        return K.repeat(X, self.n)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "n": self.n}
        base_config = super(RepeatVector, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Dense(Layer):
    '''Just your regular fully connected NN layer.

    # Input shape
        2D tensor with shape: `(nb_samples, input_dim)`.

    # Output shape
        2D tensor with shape: `(nb_samples, output_dim)`.

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
            The list should have 1 element, of shape `(input_dim, output_dim)`.
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
        input_dim: dimensionality of the input (integer).
            This argument (or alternatively, the keyword argument `input_shape`)
            is required when using this layer as the first layer in a model.
    '''
    input_ndim = 2

    def __init__(self, output_dim, init='glorot_uniform', activation='linear', weights=None,
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None, input_dim=None, **kwargs):
        self.init = initializations.get(init)
        self.activation = activations.get(activation)
        self.output_dim = output_dim

        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)
        self.constraints = [self.W_constraint, self.b_constraint]

        self.initial_weights = weights

        self.input_dim = input_dim
        if self.input_dim:
            kwargs['input_shape'] = (self.input_dim,)
        self.input = K.placeholder(ndim=2)
        super(Dense, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[1]

        self.W = self.init((input_dim, self.output_dim))
        self.b = K.zeros((self.output_dim,))

        self.params = [self.W, self.b]

        self.regularizers = []
        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    @property
    def output_shape(self):
        return (self.input_shape[0], self.output_dim)

    def get_output(self, train=False):
        X = self.get_input(train)
        output = self.activation(K.dot(X, self.W) + self.b)
        return output

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'output_dim': self.output_dim,
                  'init': self.init.__name__,
                  'activation': self.activation.__name__,
                  'W_regularizer': self.W_regularizer.get_config() if self.W_regularizer else None,
                  'b_regularizer': self.b_regularizer.get_config() if self.b_regularizer else None,
                  'activity_regularizer': self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  'W_constraint': self.W_constraint.get_config() if self.W_constraint else None,
                  'b_constraint': self.b_constraint.get_config() if self.b_constraint else None,
                  'input_dim': self.input_dim}
        base_config = super(Dense, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ActivityRegularization(Layer):
    '''Layer that passes through its input unchanged, but applies an update
    to the cost function based on the activity.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as input.

    # Arguments
        l1: L1 regularization factor.
        l2: L2 regularization factor.
    '''
    def __init__(self, l1=0., l2=0., **kwargs):
        super(ActivityRegularization, self).__init__(**kwargs)
        self.l1 = l1
        self.l2 = l2

        activity_regularizer = ActivityRegularizer(l1=l1, l2=l2)
        activity_regularizer.set_layer(self)
        self.regularizers = [activity_regularizer]

    def get_output(self, train=False):
        return self.get_input(train)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "l1": self.l1,
                  "l2": self.l2}
        base_config = super(ActivityRegularization, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class TimeDistributedDense(MaskedLayer):
    '''Apply a same Dense layer for each dimension[1] (time_dimension) input.
    Especially useful after a recurrent network with 'return_sequence=True'.

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
            The list should have 1 element, of shape `(input_dim, output_dim)`.
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
        input_dim: dimensionality of the input (integer).
            This argument (or alternatively, the keyword argument `input_shape`)
            is required when using this layer as the first layer in a model.
    '''
    input_ndim = 3

    def __init__(self, output_dim,
                 init='glorot_uniform', activation='linear', weights=None,
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None,
                 input_dim=None, input_length=None, **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.activation = activations.get(activation)

        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)
        self.constraints = [self.W_constraint, self.b_constraint]

        self.initial_weights = weights

        self.input_dim = input_dim
        self.input_length = input_length
        if self.input_dim:
            kwargs['input_shape'] = (self.input_length, self.input_dim)
        self.input = K.placeholder(ndim=3)
        super(TimeDistributedDense, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[2]

        self.W = self.init((input_dim, self.output_dim))
        self.b = K.zeros((self.output_dim))

        self.params = [self.W, self.b]
        self.regularizers = []

        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    @property
    def output_shape(self):
        input_shape = self.input_shape
        return (input_shape[0], input_shape[1], self.output_dim)

    def get_output(self, train=False):
        X = self.get_input(train)

        def step(x, states):
            output = K.dot(x, self.W) + self.b
            return output, []

        last_output, outputs, states = K.rnn(step, X, [], masking=False)
        outputs = self.activation(outputs)
        return outputs

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "output_dim": self.output_dim,
                  "init": self.init.__name__,
                  "activation": self.activation.__name__,
                  "W_regularizer": self.W_regularizer.get_config() if self.W_regularizer else None,
                  "b_regularizer": self.b_regularizer.get_config() if self.b_regularizer else None,
                  "activity_regularizer": self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  "W_constraint": self.W_constraint.get_config() if self.W_constraint else None,
                  "b_constraint": self.b_constraint.get_config() if self.b_constraint else None,
                  "input_dim": self.input_dim,
                  "input_length": self.input_length}
        base_config = super(TimeDistributedDense, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class AutoEncoder(Layer):
    '''A customizable autoencoder model.

    # Input shape
        Same as encoder input.

    # Output shape
        If `output_reconstruction = True` then dim(input) = dim(output)
        else dim(output) = dim(hidden).

    # Arguments
        encoder: A [layer](./) or [layer container](./containers.md).
        decoder: A [layer](./) or [layer container](./containers.md).
        output_reconstruction: If this is `False`,
            the output of the autoencoder is the output of
            the deepest hidden layer.
            Otherwise, the output of the final decoder layer is returned.
        weights: list of numpy arrays to set as initial weights.

    # Examples
    ```python
    from keras.layers import containers

    # input shape: (nb_samples, 32)
    encoder = containers.Sequential([Dense(16, input_dim=32), Dense(8)])
    decoder = containers.Sequential([Dense(16, input_dim=8), Dense(32)])

    autoencoder = Sequential()
    autoencoder.add(AutoEncoder(encoder=encoder, decoder=decoder,
                                output_reconstruction=False))
    ```
    '''
    def __init__(self, encoder, decoder, output_reconstruction=True,
                 weights=None, **kwargs):
        super(AutoEncoder, self).__init__(**kwargs)

        self.output_reconstruction = output_reconstruction
        self.encoder = encoder
        self.decoder = decoder

        self.decoder.set_previous(self.encoder)

        self.params = []
        self.regularizers = []
        self.constraints = []
        self.updates = []
        for layer in [self.encoder, self.decoder]:
            params, regularizers, constraints, updates = layer.get_params()
            self.regularizers += regularizers
            self.updates += updates
            for p, c in zip(params, constraints):
                if p not in self.params:
                    self.params.append(p)
                    self.constraints.append(c)

        if weights is not None:
            self.set_weights(weights)

    def set_previous(self, node):
        self.encoder.set_previous(node)

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

    def _get_hidden(self, train=False):
        return self.encoder.get_output(train)

    @property
    def input_shape(self):
        return self.encoder.input_shape

    @property
    def output_shape(self):
        if self.output_reconstruction:
            return self.encoder.previous.output_shape
        else:
            return self.decoder.previous.output_shape

    def get_output(self, train=False):
        if not train and not self.output_reconstruction:
            return self.encoder.get_output(train)

        return self.decoder.get_output(train)

    def get_config(self):
        return {"name": self.__class__.__name__,
                "encoder_config": self.encoder.get_config(),
                "decoder_config": self.decoder.get_config(),
                "output_reconstruction": self.output_reconstruction}


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

    # Input shape
        2D tensor with shape: `(nb_samples, input_dim)`.

    # Output shape
        2D tensor with shape: `(nb_samples, output_dim)`.

    # References
        - [Maxout Networks](http://arxiv.org/pdf/1302.4389.pdf)
    '''
    input_ndim = 2

    def __init__(self, output_dim, nb_feature=4,
                 init='glorot_uniform', weights=None,
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None, input_dim=None, **kwargs):
        self.output_dim = output_dim
        self.nb_feature = nb_feature
        self.init = initializations.get(init)

        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)
        self.constraints = [self.W_constraint, self.b_constraint]

        self.initial_weights = weights
        self.input_dim = input_dim
        if self.input_dim:
            kwargs['input_shape'] = (self.input_dim,)
        self.input = K.placeholder(ndim=2)
        super(MaxoutDense, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[1]

        self.W = self.init((self.nb_feature, input_dim, self.output_dim))
        self.b = K.zeros((self.nb_feature, self.output_dim))

        self.params = [self.W, self.b]
        self.regularizers = []

        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.b_regularizer:
            self.b_regularizer.set_param(self.b)
            self.regularizers.append(self.b_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    @property
    def output_shape(self):
        return (self.input_shape[0], self.output_dim)

    def get_output(self, train=False):
        X = self.get_input(train)
        # -- don't need activation since it's just linear.
        output = K.max(K.dot(X, self.W) + self.b, axis=1)
        return output

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'output_dim': self.output_dim,
                  'init': self.init.__name__,
                  'nb_feature': self.nb_feature,
                  'W_regularizer': self.W_regularizer.get_config() if self.W_regularizer else None,
                  'b_regularizer': self.b_regularizer.get_config() if self.b_regularizer else None,
                  'activity_regularizer': self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  'W_constraint': self.W_constraint.get_config() if self.W_constraint else None,
                  'b_constraint': self.b_constraint.get_config() if self.b_constraint else None,
                  'input_dim': self.input_dim}
        base_config = super(MaxoutDense, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Lambda(Layer):
    '''Used for evaluating an arbitrary Theano / TensorFlow expression
    on the output of the previous layer.

    # Input shape
        Arbitrary. Use the keyword argument input_shape
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Specified by `output_shape` argument.

    # Arguments
        function: The function to be evaluated.
            Takes one argument: the output of previous layer
        output_shape: Expected output shape from function.
            Could be a tuple or a function of the shape of the input
    '''
    def __init__(self, function, output_shape=None, **kwargs):
        super(Lambda, self).__init__(**kwargs)
        py3 = sys.version_info[0] == 3
        if py3:
            self.function = marshal.dumps(function.__code__)
        else:
            self.function = marshal.dumps(function.func_code)
        if output_shape is None:
            self._output_shape = None
        elif type(output_shape) in {tuple, list}:
            self._output_shape = tuple(output_shape)
        else:
            if py3:
                self._output_shape = marshal.dumps(output_shape.__code__)
            else:
                self._output_shape = marshal.dumps(output_shape.func_code)

    @property
    def output_shape(self):
        if self._output_shape is None:
            return self.input_shape
        elif type(self._output_shape) == tuple:
            return (self.input_shape[0], ) + self._output_shape
        else:
            output_shape_func = marshal.loads(self._output_shape)
            output_shape_func = types.FunctionType(output_shape_func, globals())
            shape = output_shape_func(self.previous.output_shape)
            if type(shape) not in {list, tuple}:
                raise Exception("output_shape function must return a tuple")
            return tuple(shape)

    def get_output(self, train=False):
        func = marshal.loads(self.function)
        func = types.FunctionType(func, globals())
        if hasattr(self, 'previous'):
            return func(self.previous.get_output(train))
        else:
            return func(self.input)


class MaskedLambda(MaskedLayer, Lambda):
    pass


class LambdaMerge(Lambda):
    '''LambdaMerge layer for evaluating an arbitrary Theano / TensorFlow
    function over multiple inputs.

    # Output shape
        Specified by output_shape argument

    # Arguments
        layers - Input layers. Similar to layers argument of Merge
        function - The function to be evaluated. Takes one argument:
            list of outputs from input layers
        output_shape - Expected output shape from function.
            Could be a tuple or a function of list of input shapes
    '''
    def __init__(self, layers, function, output_shape=None):
        if len(layers) < 2:
            raise Exception('Please specify two or more input layers '
                            '(or containers) to merge')
        self.layers = layers
        self.params = []
        self.regularizers = []
        self.constraints = []
        self.updates = []
        for l in self.layers:
            params, regs, consts, updates = l.get_params()
            self.regularizers += regs
            self.updates += updates
            # params and constraints have the same size
            for p, c in zip(params, consts):
                if p not in self.params:
                    self.params.append(p)
                    self.constraints.append(c)
        py3 = sys.version_info[0] == 3
        if py3:
            self.function = marshal.dumps(function.__code__)
        else:
            self.function = marshal.dumps(function.func_code)
        if output_shape is None:
            self._output_shape = None
        elif type(output_shape) in {tuple, list}:
            self._output_shape = tuple(output_shape)
        else:
            if py3:
                self._output_shape = marshal.dumps(output_shape.__code__)
            else:
                self._output_shape = marshal.dumps(output_shape.func_code)

    @property
    def output_shape(self):
        input_shapes = [layer.output_shape for layer in self.layers]
        if self._output_shape is None:
            return input_shapes[0]
        elif type(self._output_shape) == tuple:
            return (input_shapes[0][0], ) + self._output_shape
        else:
            output_shape_func = marshal.loads(self._output_shape)
            output_shape_func = types.FunctionType(output_shape_func, globals())
            shape = output_shape_func(input_shapes)
            if type(shape) not in {list, tuple}:
                raise Exception('output_shape function must return a tuple')
            return tuple(shape)

    def get_params(self):
        return self.params, self.regularizers, self.constraints, self.updates

    def get_output(self, train=False):
        func = marshal.loads(self.function)
        func = types.FunctionType(func, globals())
        inputs = [layer.get_output(train) for layer in self.layers]
        return func(inputs)

    def get_input(self, train=False):
        res = []
        for i in range(len(self.layers)):
            o = self.layers[i].get_input(train)
            if not type(o) == list:
                o = [o]
            for output in o:
                if output not in res:
                    res.append(output)
        return res

    @property
    def input(self):
        return self.get_input()

    def supports_masked_input(self):
        return False

    def get_output_mask(self, train=None):
        return None

    def get_weights(self):
        weights = []
        for l in self.layers:
            weights += l.get_weights()
        return weights

    def set_weights(self, weights):
        for i in range(len(self.layers)):
            nb_param = len(self.layers[i].params)
            self.layers[i].set_weights(weights[:nb_param])
            weights = weights[nb_param:]

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'layers': [l.get_config() for l in self.layers],
                  'function': self.function,
                  'output_shape': self._output_shape}
        base_config = super(LambdaMerge, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Siamese(Layer):
    '''Share a layer accross multiple inputs.

    For instance, this allows you to applied e.g.
    a same `Dense` layer to the output of two
    different layers in a graph.

    # Output shape
        Depends on merge_mode argument

    # Arguments
        layer: The layer to be shared across multiple inputs
        inputs: Inputs to the shared layer
        merge_mode: Same meaning as `mode` argument of Merge layer
        concat_axis: Same meaning as `concat_axis` argument of Merge layer
        dot_axes: Same meaning as `dot_axes` argument of Merge layer
    '''
    def __init__(self, layer, inputs, merge_mode='concat',
                 concat_axis=1, dot_axes=-1, is_graph=False):
        if merge_mode not in ['sum', 'mul', 'concat', 'ave',
                              'join', 'cos', 'dot', None]:
            raise Exception('Invalid merge mode: ' + str(merge_mode))

        if merge_mode in {'cos', 'dot'}:
            if len(inputs) > 2:
                raise Exception(merge_mode + ' merge takes exactly 2 layers')

        self.layer = layer
        self.trainable = layer.trainable
        self.is_graph = is_graph
        self.inputs = inputs
        self.layer.set_previous(inputs[0])
        self.merge_mode = merge_mode
        self.concat_axis = concat_axis
        self.dot_axes = dot_axes
        self.params = []
        self.regularizers = []
        self.constraints = []
        self.updates = []
        layers = [layer]
        if merge_mode and not is_graph:
            layers += inputs
        for l in layers:
            params, regs, consts, updates = l.get_params()
            self.regularizers += regs
            self.updates += updates
            # params and constraints have the same size
            for p, c in zip(params, consts):
                if p not in self.params:
                    self.params.append(p)
                    self.constraints.append(c)

    @property
    def output_shape(self):
        if self.merge_mode is None:
            return self.layer.output_shape
        input_shapes = [self.get_output_shape(i) for i in range(len(self.inputs))]

        if self.merge_mode in ['sum', 'mul', 'ave']:
            return input_shapes[0]

        elif self.merge_mode == 'concat':
            output_shape = list(input_shapes[0])
            for shape in input_shapes[1:]:
                output_shape[self.concat_axis] += shape[self.concat_axis]
            return tuple(output_shape)

        elif self.merge_mode == 'join':
            return None

        elif self.merge_mode == 'dot':
            shape1 = list(input_shapes[0])
            shape2 = list(input_shapes[1])
            for i in self.dot_axes[0]:
                shape1.pop(i)
            for i in self.dot_axes[1]:
                shape2.pop(i)
            shape = shape1 + shape2[1:]
            if len(shape) == 1:
                shape.append(1)
            return tuple(shape)

        elif self.merge_mode == 'cos':
            return (input_shapes[0][0], 1)

    def get_params(self):
        return self.params, self.regularizers, self.constraints, self.updates

    def set_layer_input(self, head):
        layer = self.layer
        from ..layers.containers import Sequential
        while issubclass(layer.__class__, Sequential):
            layer = layer.layers[0]
        layer.previous = self.inputs[head]

    def get_output_at(self, head, train=False):
        X = self.inputs[head].get_output(train)
        mask = self.inputs[head].get_output_mask(train)
        Y = self.layer(X, mask)
        return Y

    def get_output_shape(self, head, train=False):
        self.set_layer_input(head)
        return self.layer.output_shape

    def get_output_join(self, train=False):
        o = OrderedDict()
        for i in range(len(self.inputs)):
            X = self.get_output_at(i, train)
            if X.name is None:
                raise ValueError('merge_mode="join" '
                                 'only works with named inputs')
            o[X.name] = X
        return o

    def get_output_sum(self, train=False):
        s = self.get_output_at(0, train)
        for i in range(1, len(self.inputs)):
            s += self.get_output_at(i, train)
        return s

    def get_output_ave(self, train=False):
        n = len(self.inputs)
        s = self.get_output_at(0, train)
        for i in range(1, n):
            s += self.get_output_at(i, train)
        s /= n
        return s

    def get_output_concat(self, train=False):
        inputs = [self.get_output_at(i, train) for i in range(len(self.inputs))]
        return K.concatenate(inputs, axis=self.concat_axis)

    def get_output_mul(self, train=False):
        s = self.get_output_at(0, train)
        for i in range(1, len(self.inputs)):
            s *= self.get_output_at(i, train)
        return s

    def get_output_dot(self, train=False):
        if K._BACKEND != 'theano':
            raise Exception('"dot" merge mode will only work with Theano.')
        from theano import tensor as T
        l1 = self.get_output_at(0, train)
        l2 = self.get_output_at(1, train)
        output = T.batched_tensordot(l1, l2, self.dot_axes)
        output = output.dimshuffle((0, 'x'))
        return output

    def get_output_cos(self, train=False):
        if K._BACKEND != 'theano':
            raise Exception('"cos" merge mode will only work with Theano.')
        import theano
        from theano import tensor as T
        l1 = self.get_output_at(0, train)
        l2 = self.get_output_at(1, train)
        output = T.batched_tensordot(l1, l2, self.dot_axes) / T.sqrt(T.batched_tensordot(l1, l1, self.dot_axes) * T.batched_tensordot(l2, l2, self.dot_axes))
        output = output.dimshuffle((0, 'x'))
        return output

    def get_output(self, train=False):
        mode = self.merge_mode
        if mode == 'join':
            return self.get_output_join(train)
        elif mode == 'concat':
            return self.get_output_concat(train)
        elif mode == 'sum':
            return self.get_output_sum(train)
        elif mode == 'ave':
            return self.get_output_ave(train)
        elif mode == 'mul':
            return self.get_output_mul(train)
        elif mode == 'dot':
            return self.get_output_dot(train)
        elif mode == 'cos':
            return self.get_output_cos(train)

    def get_input(self, train=False):
        res = []
        for i in range(len(self.inputs)):
            o = self.inputs[i].get_input(train)
            if type(o) != list:
                o = [o]
            for output in o:
                if output not in res:
                    res.append(output)
        return res

    @property
    def input(self):
        return self.get_input()

    def supports_masked_input(self):
        return False

    def get_output_mask(self, train=None):
        return None

    def get_weights(self):
        weights = self.layer.get_weights()
        if self.merge_mode and not self.is_graph:
            for m in self.inputs:
                weights += m.get_weights()
        return weights

    def set_weights(self, weights):
        nb_param = len(self.layer.params)
        self.layer.set_weights(weights[:nb_param])
        weights = weights[nb_param:]
        if self.merge_mode and not self.is_graph:
            for i in range(len(self.inputs)):
                nb_param = len(self.inputs[i].params)
                self.inputs[i].set_weights(weights[:nb_param])
                weights = weights[nb_param:]

    def get_config(self):
        config = {'name': self.__class__.__name__,
                  'layer': self.layer.get_config(),
                  'inputs': [m.get_config() for m in self.inputs],
                  'merge_mode': self.merge_mode,
                  'concat_axis': self.concat_axis,
                  'dot_axes': self.dot_axes,
                  'is_graph': self.is_graph}
        base_config = super(Siamese, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class SiameseHead(Layer):
    '''This layer should be added only on top of a Siamese layer
    with merge_mode = None

    Outputs the output of the Siamese layer at a given index,
    specified by the head argument

    # Arguments
        head: The index at which the output of the Siamese layer
            should be obtained
    '''
    def __init__(self, head):
        self.head = head
        self.params = []

    def get_output(self, train=False):
        return self.get_input(train)

    @property
    def input_shape(self):
        return self.previous.get_output_shape(self.head)

    def get_input(self, train=False):
        return self.previous.get_output_at(self.head, train)

    def get_config(self):

        config = {'name': self.__class__.__name__,
                  'head': self.head}

        base_config = super(SiameseHead, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

    def set_previous(self, layer):
        self.previous = layer


def add_shared_layer(layer, inputs):
    '''Use this function to add a shared layer across
    multiple Sequential models without merging the outputs
    '''
    input_layers = [l.layers[-1] for l in inputs]
    s = Siamese(layer, input_layers, merge_mode=None)
    for i in range(len(inputs)):
        sh = SiameseHead(i)
        inputs[i].add(s)
        inputs[i].add(sh)

from __future__ import absolute_import
from .. import backend as K

from .. import activations, initializations, regularizers, constraints
from ..layers.core import Layer, MaskedLayer

from ..constraints import unitnorm


class Embedding(Layer):
    '''Turn positive integers (indexes) into denses vectors of fixed size.
    eg. [[4], [20]] -> [[0.25, 0.1], [0.6, -0.2]]

    This layer can only be used as the first layer in  a model.

    # Input shape
        2D tensor with shape: `(nb_samples, sequence_length)`.

    # Output shape
        3D tensor with shape: `(nb_samples, sequence_length, output_dim)`.

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
      input_length: Length of input sequences, when it is constantself.
          This argument is required if you are going to connect
          `Flatten` then `Dense` layers upstream
          (without it, the shape of the dense outputs cannot be computed).
    '''
    input_ndim = 2

    def __init__(self, input_dim, output_dim,
                 init='uniform', input_length=None,
                 W_regularizer=None, activity_regularizer=None,
                 W_constraint=None,
                 mask_zero=False,
                 weights=None, **kwargs):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.input_length = input_length
        self.mask_zero = mask_zero

        self.W_constraint = constraints.get(W_constraint)
        self.constraints = [self.W_constraint]

        self.W_regularizer = regularizers.get(W_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        self.initial_weights = weights
        kwargs['input_shape'] = (self.input_dim,)
        super(Embedding, self).__init__(**kwargs)

    def build(self):
        self.input = K.placeholder(shape=(self.input_shape[0], self.input_length),
                                   dtype='int32')
        self.W = self.init((self.input_dim, self.output_dim))
        self.params = [self.W]
        self.regularizers = []
        if self.W_regularizer:
            self.W_regularizer.set_param(self.W)
            self.regularizers.append(self.W_regularizer)

        if self.activity_regularizer:
            self.activity_regularizer.set_layer(self)
            self.regularizers.append(self.activity_regularizer)

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)

    def get_output_mask(self, train=None):
        X = self.get_input(train)
        if not self.mask_zero:
            return None
        else:
            if K._BACKEND == "tensorflow":
                raise Exception("Masking is Theano-only for the time being.")
            return K.ones_like(X) * (1 - K.equal(X, 0))

    @property
    def output_shape(self):
        return (self.input_shape[0], self.input_length, self.output_dim)

    def get_output(self, train=False):
        X = self.get_input(train)
        out = K.gather(self.W, X)
        return out

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "input_dim": self.input_dim,
                  "output_dim": self.output_dim,
                  "init": self.init.__name__,
                  "input_length": self.input_length,
                  "mask_zero": self.mask_zero,
                  "activity_regularizer": self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  "W_regularizer": self.W_regularizer.get_config() if self.W_regularizer else None,
                  "W_constraint": self.W_constraint.get_config() if self.W_constraint else None}
        base_config = super(Embedding, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

from __future__ import absolute_import
from .core import MaskedLayer
from .. import backend as K


class GaussianNoise(MaskedLayer):
    '''Apply to the input an additive zero-centred gaussian noise with
    standard deviation `sigma`. This is useful to mitigate overfitting
    (you could see it as a kind of random data augmentation).
    Gaussian Noise (GS) is a natural choice as corruption process
    for real valued inputs.

    As it is a regularization layer, it is only active at training time.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as input.

    # Arguments
        sigma: float, standard deviation of the noise distribution.
    '''
    def __init__(self, sigma, **kwargs):
        super(GaussianNoise, self).__init__(**kwargs)
        self.sigma = sigma

    def get_output(self, train=False):
        X = self.get_input(train)
        if not train or self.sigma == 0:
            return X
        else:
            return X + K.random_normal(shape=K.shape(X),
                                       mean=0.,
                                       std=self.sigma)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "sigma": self.sigma}
        base_config = super(GaussianNoise, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class GaussianDropout(MaskedLayer):
    '''Apply to the input an multiplicative one-centred gaussian noise
    with standard deviation `sqrt(p/(1-p))`.

    As it is a regularization layer, it is only active at training time.

    # Arguments
        p: float, drop probability (as with `Dropout`).

    # References:
        [Dropout: A Simple Way to Prevent Neural Networks from Overfitting Srivastava, Hinton, et al. 2014](http://www.cs.toronto.edu/~rsalakhu/papers/srivastava14a.pdf)
    '''
    def __init__(self, p, **kwargs):
        super(GaussianDropout, self).__init__(**kwargs)
        self.p = p

    def get_output(self, train):
        X = self.get_input(train)
        if train:
            # self.p refers to drop probability rather than
            # retain probability (as in paper), for consistency
            X *= K.random_normal(shape=K.shape(X), mean=1.0,
                                 std=self.p / (1.0 - self.p))
        return X

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "p": self.p}
        base_config = super(GaussianDropout, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

from .. import initializations
from ..layers.core import MaskedLayer
from .. import backend as K
import numpy as np


class LeakyReLU(MaskedLayer):
    '''Special version of a Rectified Linear Unit
    that allows a small gradient when the unit is not active
    (`f(x) = alpha*x for x < 0`).

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
        super(LeakyReLU, self).__init__(**kwargs)
        self.alpha = alpha

    def get_output(self, train):
        X = self.get_input(train)
        return K.relu(X, alpha=self.alpha)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "alpha": self.alpha}
        base_config = super(LeakyReLU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class PReLU(MaskedLayer):
    '''
    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as the input.

    # Arguments:
        init: initialization function for the weights.
        weights: initial weights, as a list of a single numpy array.

    # References:
        - [Delving Deep into Rectifiers: Surpassing Human-Level Performance on ImageNet Classification](http://arxiv.org/pdf/1502.01852v1.pdf)
    '''
    def __init__(self, init='zero', weights=None, **kwargs):
        self.init = initializations.get(init)
        self.initial_weights = weights
        super(PReLU, self).__init__(**kwargs)

    def build(self):
        input_shape = self.input_shape[1:]
        self.alphas = self.init(input_shape)
        self.params = [self.alphas]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def get_output(self, train):
        X = self.get_input(train)
        pos = K.relu(X)
        neg = self.alphas * (X - abs(X)) * 0.5
        return pos + neg

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "init": self.init.__name__}
        base_config = super(PReLU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ELU(MaskedLayer):
    '''
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
        super(ELU, self).__init__(**kwargs)
        self.alpha = alpha

    def get_output(self, train):
        X = self.get_input(train)
        pos = K.relu(X)
        neg = (X - abs(X)) * 0.5
        return pos + self.alpha * (K.exp(neg) - 1.)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "alpha": self.alpha}
        base_config = super(ELU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ParametricSoftplus(MaskedLayer):
    '''Parametric Softplus of the form: alpha * log(1 + exp(beta * X))

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

    # References:
        - [Inferring Nonlinear Neuronal Computation Based on Physiologically Plausible Inputs](http://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003143)
    '''
    def __init__(self, alpha_init=0.2, beta_init=5.0,
                 weights=None, **kwargs):
        self.alpha_init = alpha_init
        self.beta_init = beta_init
        self.initial_weights = weights
        super(ParametricSoftplus, self).__init__(**kwargs)

    def build(self):
        input_shape = self.input_shape[1:]
        self.alphas = K.variable(self.alpha_init * np.ones(input_shape))
        self.betas = K.variable(self.beta_init * np.ones(input_shape))
        self.params = [self.alphas, self.betas]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def get_output(self, train):
        X = self.get_input(train)
        return K.softplus(self.betas * X) * self.alphas

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "alpha_init": self.alpha_init,
                  "beta_init": self.beta_init}
        base_config = super(ParametricSoftplus, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ThresholdedLinear(MaskedLayer):
    '''Thresholded Linear Activation.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as the input.

    # Arguments
        theta: float >= 0. Threshold location of activation.

    # References
        [Zero-Bias Autoencoders and the Benefits of Co-Adapting Features](http://arxiv.org/pdf/1402.3337.pdf)
    '''
    def __init__(self, theta=1.0, **kwargs):
        super(ThresholdedLinear, self).__init__(**kwargs)
        self.theta = theta

    def get_output(self, train):
        X = self.get_input(train)
        return K.switch(K.abs(X) < self.theta, 0, X)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "theta": self.theta}
        base_config = super(ThresholdedLinear, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ThresholdedReLU(MaskedLayer):
    '''Thresholded Rectified Activation.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as the input.

    # Arguments
        theta: float >= 0. Threshold location of activation.

    # References
        [Zero-Bias Autoencoders and the Benefits of Co-Adapting Features](http://arxiv.org/pdf/1402.3337.pdf)
    '''
    def __init__(self, theta=1.0, **kwargs):
        super(ThresholdedReLU, self).__init__(**kwargs)
        self.theta = theta

    def get_output(self, train):
        X = self.get_input(train)
        return K.switch(X > self.theta, X, 0)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "theta": self.theta}
        base_config = super(ThresholdedReLU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

from ..layers.core import Layer
from .. import initializations
from .. import backend as K


class BatchNormalization(Layer):
    '''Normalize the activations of the previous layer at each batch.

    # Input shape
        Arbitrary. Use the keyword argument `input_shape`
        (tuple of integers, does not include the samples axis)
        when using this layer as the first layer in a model.

    # Output shape
        Same shape as input.

    # Arguments
        epsilon: small float > 0. Fuzz parameter.
        mode: integer, 0 or 1.
            - 0: feature-wise normalization.
            - 1: sample-wise normalization.
        momentum: momentum in the computation of the
            exponential average of the mean and standard deviation
            of the data, for feature-wise normalization.
        weights: Initialization weights.
            List of 2 numpy arrays, with shapes:
            `[(input_shape,), (input_shape,)]`

    # References
        - [Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift](http://arxiv.org/pdf/1502.03167v3.pdf)
    '''
    def __init__(self, epsilon=1e-6, mode=0, momentum=0.9,
                 weights=None, **kwargs):
        self.init = initializations.get("uniform")
        self.epsilon = epsilon
        self.mode = mode
        self.momentum = momentum
        self.initial_weights = weights
        super(BatchNormalization, self).__init__(**kwargs)

    def build(self):
        input_shape = self.input_shape  # starts with samples axis
        input_shape = input_shape[1:]

        self.gamma = self.init((input_shape))
        self.beta = K.zeros(input_shape)

        self.params = [self.gamma, self.beta]
        self.running_mean = K.zeros(input_shape)
        self.running_std = K.ones((input_shape))

        # initialize self.updates: batch mean/std computation
        X = self.get_input(train=True)
        m = K.mean(X, axis=0)
        std = K.mean(K.square(X - m) + self.epsilon, axis=0)
        std = K.sqrt(std)
        mean_update = self.momentum * self.running_mean + (1-self.momentum) * m
        std_update = self.momentum * self.running_std + (1-self.momentum) * std
        self.updates = [(self.running_mean, mean_update),
                        (self.running_std, std_update)]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def get_weights(self):
        super_weights = super(BatchNormalization, self).get_weights()
        return super_weights + [K.get_value(self.running_mean),
                                K.get_value(self.running_std)]

    def set_weights(self, weights):
        K.set_value(self.running_mean, weights[-2])
        K.set_value(self.running_std, weights[-1])
        super(BatchNormalization, self).set_weights(weights[:-2])

    def get_output(self, train):
        X = self.get_input(train)
        if self.mode == 0:
            X_normed = ((X - self.running_mean) /
                        (self.running_std + self.epsilon))
        elif self.mode == 1:
            m = K.mean(X, axis=-1, keepdims=True)
            std = K.std(X, axis=-1, keepdims=True)
            X_normed = (X - m) / (std + self.epsilon)
        out = self.gamma * X_normed + self.beta
        return out

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "epsilon": self.epsilon,
                  "mode": self.mode,
                  "momentum": self.momentum}
        base_config = super(BatchNormalization, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

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
from six.moves import cPickle
import gzip
from .data_utils import get_file
import random
from six.moves import zip
import numpy as np


def load_data(path="imdb.pkl", nb_words=None, skip_top=0, maxlen=None, test_split=0.2, seed=113,
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

    X_train = X[:int(len(X)*(1-test_split))]
    y_train = labels[:int(len(X)*(1-test_split))]

    X_test = X[int(len(X)*(1-test_split)):]
    y_test = labels[int(len(X)*(1-test_split)):]

    return (X_train, y_train), (X_test, y_test)

from __future__ import absolute_import
from __future__ import print_function

import tarfile
import os
from six.moves.urllib.request import FancyURLopener

from ..utils.generic_utils import Progbar


class ParanoidURLopener(FancyURLopener):
    def http_error_default(self, url, fp, errcode, errmsg, headers):
        raise Exception('URL fetch failure on {}: {} -- {}'.format(url, errcode, errmsg))


def get_file(fname, origin, untar=False):
    datadir = os.path.expanduser(os.path.join('~', '.keras', 'datasets'))
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

        ParanoidURLopener().retrieve(origin, fpath, dl_progress)
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
from .data_utils import get_file
import random
from six.moves import cPickle
from six.moves import zip
import numpy as np


def load_data(path="reuters.pkl", nb_words=None, skip_top=0, maxlen=None, test_split=0.2, seed=113,
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

    X_train = X[:int(len(X)*(1-test_split))]
    y_train = labels[:int(len(X)*(1-test_split))]

    X_test = X[int(len(X)*(1-test_split)):]
    y_test = labels[int(len(X)*(1-test_split)):]

    return (X_train, y_train), (X_test, y_test)


def get_word_index(path="reuters_word_index.pkl"):
    path = get_file(path, origin="https://s3.amazonaws.com/text-datasets/reuters_word_index.pkl")
    f = open(path, 'rb')
    return cPickle.load(f)


if __name__ == "__main__":
    make_reuters_dataset()
    (X_train, y_train), (X_test, y_test) = load_data()

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

from __future__ import print_function
import inspect
import numpy as np
import copy

from ..layers.advanced_activations import *
from ..layers.core import *
from ..layers.convolutional import *
from ..layers.embeddings import *
from ..layers.noise import *
from ..layers.normalization import *
from ..layers.recurrent import *
from ..layers import containers
from .. import regularizers
from .. import constraints


def container_from_config(original_layer_dict, custom_objects={}):
    layer_dict = copy.deepcopy(original_layer_dict)
    name = layer_dict.get('name')

    # Insert custom layers into globals so they can
    # be accessed by `get_from_module`.
    for cls_key in custom_objects:
        globals()[cls_key] = custom_objects[cls_key]

    if name == 'Merge':
        mode = layer_dict.get('mode')
        layers = layer_dict.get('layers')
        layer_list = []
        for layer in layers:
            init_layer = container_from_config(layer)
            layer_list.append(init_layer)
        merge_layer = Merge(layer_list, mode)
        return merge_layer

    elif name == 'Sequential':
        layers = layer_dict.get('layers')
        layer_list = []
        for layer in layers:
            init_layer = container_from_config(layer)
            layer_list.append(init_layer)
        seq_layer = containers.Sequential(layer_list)
        return seq_layer

    elif name == 'Graph':
        graph_layer = containers.Graph()
        inputs = layer_dict.get('input_config')

        for input in inputs:
            graph_layer.add_input(**input)

        nodes = layer_dict.get('node_config')
        for node in nodes:
            layer = container_from_config(layer_dict['nodes'].get(node['name']))
            node['layer'] = layer
            graph_layer.add_node(**node)

        outputs = layer_dict.get('output_config')
        for output in outputs:
            graph_layer.add_output(**output)
        return graph_layer

    elif name == 'AutoEncoder':
        kwargs = {'encoder': container_from_config(layer_dict.get('encoder_config')),
                  'decoder': container_from_config(layer_dict.get('decoder_config'))}
        for kwarg in ['output_reconstruction', 'weights']:
            if kwarg in layer_dict:
                kwargs[kwarg] = layer_dict[kwarg]
        return AutoEncoder(**kwargs)

    else:
        layer_dict.pop('name')

        for k, v in layer_dict.items():
            if isinstance(v, dict):
                vname = v.pop('name')
                if vname in [x for x, y in inspect.getmembers(constraints, predicate=inspect.isclass)]:
                    layer_dict[k] = constraints.get(vname, v)
                elif vname in [x for x, y in inspect.getmembers(regularizers, predicate=inspect.isclass)]:
                    layer_dict[k] = regularizers.get(vname, v)
                else:
                    # not a regularizer of constraint, don't touch it
                    v['name'] = vname

        base_layer = get_layer(name, layer_dict)
        return base_layer


def model_summary(model):
    param_count = 0  # param count in the model

    def display(objects, positions):
        line = ''
        for i in range(len(objects)):
            line += str(objects[i])
            line = line[:positions[i]]
            line += ' ' * (positions[i] - len(line))
        print(line)

    def display_layer_info(layer, name, positions):
        layer_type = layer.__class__.__name__
        output_shape = layer.output_shape
        params = layer.count_params()
        to_display = ['%s (%s)' % (layer_type, name), output_shape, params]
        display(to_display, positions)

    line_length = 80  # total length of printed lines
    positions = [30, 60, 80]  # absolute positions of log elements in each line
    # header names for the different log elements
    to_display = ['Layer (name)', 'Output Shape', 'Param #']

    # for sequential models, we start by printing
    # the expect input shape
    if model.__class__.__name__ == 'Sequential':
        print('-' * line_length)
        print('Initial input shape: ' + str(model.input_shape))

    # print header
    print('-' * line_length)
    display(to_display, positions)
    print('-' * line_length)

    if model.__class__.__name__ == 'Sequential':
        for layer in model.layers:
            name = getattr(layer, 'name', 'Unnamed')
            display_layer_info(layer, name, positions)
            param_count += layer.count_params()

    elif model.__class__.__name__ == 'Graph':
        for name in model.input_order:
            layer = model.inputs[name]
            display_layer_info(layer, name, positions)

        for name in model.nodes:
            layer = model.nodes[name]
            display_layer_info(layer, name, positions)
            param_count += layer.count_params()

        for name in model.output_order:
            layer = model.outputs[name]
            display_layer_info(layer, name, positions)

    print('-' * line_length)
    print('Total params: %s' % param_count)
    print('-' * line_length)


from .generic_utils import get_from_module
def get_layer(identifier, kwargs=None):
    return get_from_module(identifier, globals(), 'layer',
                           instantiate=True, kwargs=kwargs)

from __future__ import absolute_import
import numpy as np
import time
import sys
import six


def get_from_module(identifier, module_params, module_name, instantiate=False, kwargs=None):
    if isinstance(identifier, six.string_types):
        res = module_params.get(identifier)
        if not res:
            raise Exception('Invalid ' + str(module_name) + ': ' + str(identifier))
        if instantiate and not kwargs:
            return res()
        elif instantiate and kwargs:
            return res(**kwargs)
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
                info += ' - %s:' % k
                if type(self.sum_values[k]) is list:
                    avg = self.sum_values[k][0] / max(1, self.sum_values[k][1])
                    if avg > 1e-3:
                        info += ' %.4f' % avg
                    else:
                        info += ' %.4e' % avg
                else:
                    info += ' %s' % self.sum_values[k]

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
                    info += ' - %s:' % k
                    avg = self.sum_values[k][0] / max(1, self.sum_values[k][1])
                    if avg > 1e-3:
                        info += ' %.4f' % avg
                    else:
                        info += ' %.4e' % avg
                sys.stdout.write(info + "\n")

    def add(self, n, values=[]):
        self.update(self.seen_so_far+n, values)


import pydot
# old pydot will not work with python3, must use one
# that works with python3 such as pydot2 or pydot
import itertools
from keras.layers.containers import Graph, Sequential
from keras.layers.core import Merge


def layer_typename(layer):
    return type(layer).__module__ + "." + type(layer).__name__


def get_layer_to_name(model):
    """Returns a dict mapping layer to their name in the model"""
    if not isinstance(model, Graph):
        return {}
    else:
        node_to_name = itertools.chain(
            model.nodes.items(), model.inputs.items(), model.outputs.items()
        )
        return {v: k for k, v in node_to_name}


class ModelToDot(object):
    """
    This is a helper class which visits a keras model (Sequential or Graph) and
    returns a pydot.Graph representation.

    This is implemented as a class because we need to maintain various states.

    Use it as ```ModelToDot()(model)```

    Keras models can have an arbitrary number of inputs and outputs. A given
    layer can have multiple inputs but has a single output. We therefore
    explore the model by starting at its output and crawling "up" the tree.
    """
    def _pydot_node_for_layer(self, layer, label):
        """
        Returns the pydot.Node corresponding to the given layer.
        `label` specify the name of the layer (only used if the layer isn't yet
            associated with a pydot.Node)
        """
        # Check if this already exists (will be the case for nodes that
        # serve as input to more than one layer)
        if layer in self.layer_to_pydotnode:
            node = self.layer_to_pydotnode[layer]
        else:
            layer_id = 'layer%d' % self.idgen
            self.idgen += 1

            label = label + " (" + layer_typename(layer) + ")"

            if self.show_shape:
                # Build the label that will actually contain a table with the
                # input/output
                outputlabels = str(layer.output_shape)
                if hasattr(layer, 'input_shape'):
                    inputlabels = str(layer.input_shape)
                elif hasattr(layer, 'input_shapes'):
                    inputlabels = ', '.join(
                        [str(ishape) for ishape in layer.input_shapes])
                else:
                    inputlabels = ''
                label = "%s\n|{input:|output:}|{{%s}|{%s}}" % (
                        label, inputlabels, outputlabels)

            node = pydot.Node(layer_id, label=label)
            self.g.add_node(node)
            self.layer_to_pydotnode[layer] = node
        return node

    def _process_layer(self, layer, layer_to_name=None, connect_to=None):
        """
        Process a layer, adding its node to the graph and creating edges to its
        outputs.

        `connect_to` specify where the output of the current layer will be
            connected
        `layer_to_name` is a dict mapping layer to their name in the Graph
            model. Should be {} when processing a Sequential model
        """
        # The layer can be a container layer, in which case we can recurse
        is_graph = isinstance(layer, Graph)
        is_seq = isinstance(layer, Sequential)
        if self.recursive and (is_graph or is_seq):
            # We got a container layer, recursively transform it
            if is_graph:
                child_layers = layer.outputs.values()
            else:
                child_layers = [layer.layers[-1]]
            for l in child_layers:
                self._process_layer(l, layer_to_name=get_layer_to_name(layer),
                                    connect_to=connect_to)
        else:
            # This is a simple layer.
            label = layer_to_name.get(layer, '')
            layer_node = self._pydot_node_for_layer(layer, label=label)

            if connect_to is not None:
                self.g.add_edge(pydot.Edge(layer_node, connect_to))

            # Proceed upwards to the parent(s). Only Merge layers have more
            # than one parent
            if isinstance(layer, Merge):  # Merge layer
                for l in layer.layers:
                    self._process_layer(l, layer_to_name,
                                        connect_to=layer_node)
            elif hasattr(layer, 'previous') and layer.previous is not None:
                self._process_layer(layer.previous, layer_to_name,
                                    connect_to=layer_node)

    def __call__(self, model, recursive=True, show_shape=False,
                 connect_to=None):
        self.idgen = 0
        # Maps keras layer to the pydot.Node representing them
        self.layer_to_pydotnode = {}
        self.recursive = recursive
        self.show_shape = show_shape

        self.g = pydot.Dot()
        self.g.set('rankdir', 'TB')
        self.g.set('concentrate', True)
        self.g.set_node_defaults(shape='record', fontname="Fira Mono")

        if hasattr(model, 'outputs'):
            # Graph
            for name, l in model.outputs.items():
                self._process_layer(l, get_layer_to_name(model),
                                    connect_to=connect_to)
        else:
            # Sequential container
            self._process_layer(model.layers[-1], {}, connect_to=connect_to)

        return self.g


def to_graph(model, **kwargs):
    """
    `recursive` controls wether we recursively explore container layers
    `show_shape` controls wether the shape is shown in the graph
    """
    return ModelToDot()(model, **kwargs)


def plot(model, to_file='model.png'):
    graph = to_graph(model)
    graph.write_png(to_file)

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

from __future__ import absolute_import
from __future__ import print_function
import os
import json
from .common import epsilon, floatx, set_epsilon, set_floatx

_keras_dir = os.path.expanduser(os.path.join('~', '.keras'))
if not os.path.exists(_keras_dir):
    os.makedirs(_keras_dir)

_BACKEND = 'theano'
_config_path = os.path.expanduser(os.path.join('~', '.keras', 'keras.json'))
if os.path.exists(_config_path):
    _config = json.load(open(_config_path))
    _floatx = _config.get('floatx', floatx())
    assert _floatx in {'float32', 'float64'}
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

if _BACKEND == 'theano':
    print('Using Theano backend.')
    from .theano_backend import *
elif _BACKEND == 'tensorflow':
    print('Using TensorFlow backend.')
    from .tensorflow_backend import *
else:
    raise Exception('Unknown backend: ' + str(_BACKEND))

import theano
from theano import tensor as T
from theano.sandbox.rng_mrg import MRG_RandomStreams as RandomStreams
from theano.tensor.signal import downsample
import numpy as np
from .common import _FLOATX, _EPSILON


# INTERNAL UTILS
theano.config.floatX = _FLOATX


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


def ndim(x):
    return x.ndim


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
    return T.mean(x, axis=axis, keepdims=keepdims)


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


def pow(x, a):
    return T.pow(x, a)


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


def repeat(x, n):
    '''Repeat a 2D tensor:

    if x has shape (samples, dim) and n=2,
    the output will have shape (samples, 2, dim)
    '''
    tensors = [x] * n
    stacked = T.stack(*tensors)
    return stacked.dimshuffle((1, 0, 2))


def tile(x, n):
    return T.tile(x, n)


def flatten(x):
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
        return self.function(*inputs)


def function(inputs, outputs, updates=[]):
    return Function(inputs, outputs, updates=updates)


def gradients(loss, variables):
    return T.grad(loss, variables)


# CONTROL FLOW

def rnn(step_function, inputs, initial_states,
        go_backwards=False, masking=True):
    '''Iterates over the time dimension of a tensor.

    Parameters
    ----------
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
    masking: boolean. If true, any input timestep inputs[s, i]
        that is all-zeros will be skipped (states will be passed to
        the next step unchanged) and the corresponding output will
        be all zeros.

    Returns
    -------
    A tuple (last_output, outputs, new_states).
        last_output: the latest output of the rnn, of shape (samples, ...)
        outputs: tensor with shape (samples, time, ...) where each
            entry outputs[s, t] is the output of the step function
            at time t for sample s.
        new_states: list of tensors, latest states returned by
            the step function, of shape (samples, ...).
    '''
    inputs = inputs.dimshuffle((1, 0, 2))

    def _step(input, *states):
        output, new_states = step_function(input, states)
        if masking:
            # if all-zero input timestep, return
            # all-zero output and unchanged states
            switch = T.any(input)
            output = T.switch(switch, output, 0. * output)
            return_states = []
            for state, new_state in zip(states, new_states):
                return_states.append(T.switch(switch, new_state, state))
            return [output] + return_states
        else:
            return [output] + new_states

    results, _ = theano.scan(
        _step,
        sequences=inputs,
        outputs_info=[None] + initial_states,
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

    outputs = outputs.dimshuffle((1, 0, 2))
    states = [T.squeeze(state[-1]) for state in states]
    return last_output, outputs, states


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


def conv2d(x, kernel, strides=(1, 1), border_mode='valid', dim_ordering='th',
           image_shape=None, filter_shape=None):
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
        if image_shape:
            image_shape = (image_shape[0], image_shape[3],
                           image_shape[1], image_shape[2])
        if filter_shape:
            filter_shape = (filter_shape[3], filter_shape[2],
                            filter_shape[0], filter_shape[1])

    if _on_gpu() and dnn.dnn_available():
        if border_mode == 'same':
            assert(strides == (1, 1))
            np_kernel = kernel.eval()
            pad_x = (np_kernel.shape[2] - strides[0]) // 2
            pad_y = (np_kernel.shape[3] - strides[1]) // 2
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
                                      subsample=strides,
                                      image_shape=image_shape,
                                      filter_shape=filter_shape)
        if border_mode == 'same':
            shift_x = (kernel.shape[2] - 1) // 2
            shift_y = (kernel.shape[3] - 1) // 2
            conv_out = conv_out[:, :,
                                shift_x:x.shape[2] + shift_x,
                                shift_y:x.shape[3] + shift_y]
    if dim_ordering == 'tf':
        conv_out = conv_out.dimshuffle((0, 2, 3, 1))
    return conv_out


def pool2d(x, pool_size, strides=(1, 1), border_mode='valid',
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
        x = x.dimshuffle((0, 3, 1, 2))

    if pool_mode == 'max':
        pool_out = downsample.max_pool_2d(x, ds=pool_size, st=strides,
                                          ignore_border=ignore_border,
                                          padding=padding,
                                          mode='max')
    elif pool_mode == 'avg':
        pool_out = downsample.max_pool_2d(x, ds=pool_size, st=strides,
                                          ignore_border=ignore_border,
                                          padding=padding,
                                          mode='average_exc_pad')
    else:
        raise Exception('Invalid pooling mode: ' + str(pool_mode))

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

tensordot -> soon to be introduced in TF
batched_tensordot -> reimplement
'''

import tensorflow as tf
import numpy as np
from .common import _FLOATX, _EPSILON

# INTERNAL UTILS

_SESSION = None


def _get_session():
    global _SESSION
    if _SESSION is None:
        _SESSION = tf.Session('')
    return _SESSION


def _set_session(session):
    global _SESSION
    _SESSION = session


# VARIABLE MANIPULATION

def variable(value, dtype=_FLOATX, name=None):
    v = tf.Variable(np.asarray(value, dtype=dtype), name=name)
    _get_session().run(v.initializer)
    return v


def placeholder(shape=None, ndim=None, dtype=_FLOATX, name=None):
    if not shape:
        if ndim:
            shape = [None for _ in range(ndim)]
    return tf.placeholder(dtype, shape=shape, name=name)


def shape(x):
    return x.get_shape()


def ndim(x):
    return len(x.get_shape())


def eval(x):
    '''Run a graph.
    '''
    return x.eval(session=_get_session())


def zeros(shape, dtype=_FLOATX, name=None):
    return variable(np.zeros(shape), dtype, name)


def ones(shape, dtype=_FLOATX, name=None):
    return variable(np.ones(shape), dtype, name)


def ones_like(x, name=None):
    return tf.ones_like(x)


def zeros_like(x, name=None):
    return tf.zeros_like(x)


def count_params(x):
    '''Return number of scalars in a tensor.
    '''
    shape = x.get_shape()
    return np.prod([shape[i]._value for i in range(len(shape))])


def cast(x, dtype):
    return tf.cast(x, dtype)


# LINEAR ALGEBRA

def dot(x, y):
    return tf.matmul(x, y)


def transpose(x):
    return tf.transpose(x)


def gather(reference, indices):
    '''reference: a tensor.
    indices: an int tensor of indices.

    Return: a tensor of same type as reference.
    '''
    return tf.gather(reference, indices)


# ELEMENT-WISE OPERATIONS

def max(x, axis=None, keepdims=False):
    if axis is not None and axis < 0:
        axis = axis % len(x.get_shape())
    return tf.reduce_max(x, reduction_indices=axis, keep_dims=keepdims)


def min(x, axis=None, keepdims=False):
    if axis is not None and axis < 0:
        axis = axis % len(x.get_shape())
    return tf.reduce_min(x, reduction_indices=axis, keep_dims=keepdims)


def sum(x, axis=None, keepdims=False):
    '''Sum of the values in a tensor, alongside the specified axis.
    '''
    if axis is not None and axis < 0:
        axis = axis % len(x.get_shape())
    return tf.reduce_sum(x, reduction_indices=axis, keep_dims=keepdims)


def prod(x, axis=None, keepdims=False):
    '''Multiply the values in a tensor, alongside the specified axis.
    '''
    return tf.reduce_prod(x, reduction_indices=axis, keep_dims=keepdims)


def std(x, axis=None, keepdims=False):
    if axis is not None and axis < 0:
        axis = axis % len(x.get_shape())
    if x.dtype.base_dtype == tf.bool:
        x = tf.cast(x, _FLOATX)
    m = tf.reduce_mean(x, reduction_indices=axis, keep_dims=keepdims)
    devs_squared = tf.square(x - m)
    return tf.sqrt(tf.reduce_mean(devs_squared,
                                  reduction_indices=axis,
                                  keep_dims=keepdims))


def mean(x, axis=None, keepdims=False):
    if axis is not None and axis < 0:
        axis = axis % len(x.get_shape())
    if x.dtype.base_dtype == tf.bool:
        x = tf.cast(x, _FLOATX)
    return tf.reduce_mean(x, reduction_indices=axis, keep_dims=keepdims)


def any(x, axis=None, keepdims=False):
    '''Bitwise reduction (logical OR).

    Return array of int8 (0s and 1s).
    '''
    if axis is not None and axis < 0:
        axis = axis % len(x.get_shape())
    x = tf.cast(x, tf.bool)
    x = tf.reduce_any(x, reduction_indices=axis, keep_dims=keepdims)
    return tf.cast(x, tf.int8)


def argmax(x, axis=-1):
    if axis < 0:
        axis = axis % len(x.get_shape())
    return tf.argmax(x, axis)


def argmin(x, axis=-1):
    if axis < 0:
        axis = axis % len(x.get_shape())
    return tf.argmin(x, axis)


def square(x):
    return tf.square(x)


def abs(x):
    return tf.abs(x)


def sqrt(x):
    x = tf.clip_by_value(x, tf.cast(0., dtype=_FLOATX),
                         tf.cast(np.inf, dtype=_FLOATX))
    return tf.sqrt(x)


def exp(x):
    return tf.exp(x)


def log(x):
    return tf.log(x)


def round(x):
    return tf.round(x)


def pow(x, a):
    return tf.pow(x, a)


def clip(x, min_value, max_value):
    if max_value < min_value:
        max_value = min_value
    return tf.clip_by_value(x, tf.cast(min_value, dtype=_FLOATX),
                            tf.cast(max_value, dtype=_FLOATX))


def equal(x, y):
    return tf.equal(x, y)


def maximum(x, y):
    return tf.maximum(x, y)


def minimum(x, y):
    return tf.minimum(x, y)


# SHAPE OPERATIONS

def concatenate(tensors, axis=-1):
    if axis < 0:
        axis = axis % len(tensors[0].get_shape())
    return tf.concat(axis, tensors)


def reshape(x, shape):
    return tf.reshape(x, shape)


def permute_dimensions(x, pattern):
    '''Transpose dimensions.

    pattern should be a tuple or list of
    dimension indices, e.g. [0, 2, 1].
    '''
    return tf.transpose(x, perm=pattern)


def repeat(x, n):
    '''Repeat a 2D tensor:

    if x has shape (samples, dim) and n=2,
    the output will have shape (samples, 2, dim)
    '''
    tensors = [x] * n
    stacked = tf.pack(tensors)
    return tf.transpose(stacked, (1, 0, 2))


def tile(x, n):
    return tf.tile(x, n)


def flatten(x):
    '''Turn a n-D tensor into a 2D tensor where
    the first dimension is conserved.
    '''
    x = tf.reshape(x, [-1, np.prod(x.get_shape()[1:].as_list())])
    return x


def expand_dims(x, dim=-1):
    '''Add a 1-sized dimension at index "dim".
    '''
    return tf.expand_dims(x, dim)


def squeeze(x, axis):
    '''Remove a 1-dimension from the tensor at index "axis".
    '''
    return tf.squeeze(x, [axis])


def temporal_padding(x, padding=1):
    '''Pad the middle dimension of a 3D tensor
    with "padding" zeros left and right.

    Appologies for the inane API, but Theano makes this
    really hard.
    '''
    pattern = [[0, 0], [padding, padding], [0, 0]]
    return tf.pad(x, pattern)


def spatial_2d_padding(x, padding=(1, 1), dim_ordering='th'):
    '''Pad the 2nd and 3rd dimensions of a 4D tensor
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


# VALUE MANIPULATION

def get_value(x):
    '''Technically the same as eval() for TF.
    '''
    return x.eval(session=_get_session())


def set_value(x, value):
    tf.assign(x, np.asarray(value)).op.run(session=_get_session())


# GRAPH MANIPULATION

class Function(object):

    def __init__(self, inputs, outputs, updates=[]):
        self.inputs = list(inputs)
        self.outputs = list(outputs)
        with tf.control_dependencies(self.outputs):
            self.updates = [tf.assign(p, new_p) for (p, new_p) in updates]

    def __call__(self, inputs):
        names = [v.name for v in self.inputs]
        feed_dict = dict(zip(names, inputs))
        session = _get_session()
        updated = session.run(self.outputs + self.updates, feed_dict=feed_dict)
        return updated[:len(self.outputs)]


def function(inputs, outputs, updates=[]):
    return Function(inputs, outputs, updates=updates)


def gradients(loss, variables):
    return tf.gradients(loss, variables)


# CONTROL FLOW

def rnn(step_function, inputs, initial_states,
        go_backwards=False, masking=True):
    '''Iterates over the time dimension of a tensor.

    Parameters
    ----------
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
    masking: boolean. If true, any input timestep inputs[s, i]
        that is all-zeros will be skipped (states will be passed to
        the next step unchanged) and the corresponding output will
        be all zeros.

    Returns
    -------
    A tuple (last_output, outputs, new_states).
        last_output: the latest output of the rnn, of shape (samples, ...)
        outputs: tensor with shape (samples, time, ...) where each
            entry outputs[s, t] is the output of the step function
            at time t for sample s.
        new_states: list of tensors, latest states returned by
            the step function, of shape (samples, ...).
    '''
    inputs = tf.transpose(inputs, (1, 0, 2))
    input_list = tf.unpack(inputs)

    states = initial_states
    successive_states = []
    successive_outputs = []
    if go_backwards:
        input_list.reverse()
    for input in input_list:
        output, new_states = step_function(input, states)
        if masking:
            # for now we raise an exception because tf.reduce_any will not work
            raise Exception("Masking is Theano-only for the time being.")

            # if all-zero input timestep, return
            # all-zero output and unchanged states
            switch = tf.reduce_any(input)
            output = tf.python.control_flow_ops.cond(switch,
                                                     lambda: output,
                                                     lambda: 0. * output)
            return_states = []
            for state, new_state in zip(states, new_states):
                return_states.append(tf.python.control_flow_ops.cond(switch,
                                                                     lambda: new_state,
                                                                     lambda: state))
            states = return_states
        else:
            states = new_states
        successive_outputs.append(output)
        successive_states.append(states)

    last_output = successive_outputs[-1]
    outputs = tf.pack(successive_outputs)
    new_states = successive_states[-1]

    outputs = tf.transpose(outputs, (1, 0, 2))
    return last_output, outputs, states


def switch(condition, then_expression, else_expression):
    '''condition: scalar tensor.
    '''
    return tf.python.control_flow_ops.cond(condition,
                                           lambda: then_expression,
                                           lambda: else_expression)


# NN OPERATIONS

def relu(x, alpha=0., max_value=None):
    '''ReLU.

    alpha: slope of negative section.
    '''
    negative_part = tf.nn.relu(-x)
    x = tf.nn.relu(x)
    if max_value is not None:
        x = tf.clip_by_value(x, tf.cast(0., dtype=_FLOATX),
                             tf.cast(max_value, dtype=_FLOATX))
    x -= tf.constant(alpha, dtype=_FLOATX) * negative_part
    return x


def softmax(x):
    return tf.nn.softmax(x)


def softplus(x):
    return tf.nn.softplus(x)


def categorical_crossentropy(output, target, from_logits=False):
    '''Note: tf.nn.softmax_cross_entropy_with_logits
    expects logits, Keras expects probabilities.
    '''
    if not from_logits:
        # scale preds so that the class probas of each sample sum to 1
        output /= tf.reduce_sum(output,
                                reduction_indices=len(output.get_shape())-1,
                                keep_dims=True)
        # manual computation of crossentropy
        output = tf.clip_by_value(output, tf.cast(_EPSILON, dtype=_FLOATX),
                                  tf.cast(1.-_EPSILON, dtype=_FLOATX))
        return - tf.reduce_sum(target * tf.log(output),
                               reduction_indices=len(output.get_shape())-1)
    else:
        return tf.nn.softmax_cross_entropy_with_logits(output, target)


def binary_crossentropy(output, target, from_logits=False):
    '''Note: tf.nn.sigmoid_cross_entropy_with_logits
    expects logits, Keras expects probabilities.
    '''
    if not from_logits:
        # transform back to logits
        output = tf.clip_by_value(output, tf.cast(_EPSILON, dtype=_FLOATX),
                                  tf.cast(1.-_EPSILON, dtype=_FLOATX))
        output = tf.log(output / (1 - output))
    return tf.nn.sigmoid_cross_entropy_with_logits(output, target)


def sigmoid(x):
    return tf.nn.sigmoid(x)


def hard_sigmoid(x):
    x = (0.2 * x) + 0.5
    x = tf.clip_by_value(x, tf.cast(0., dtype=_FLOATX),
                         tf.cast(1., dtype=_FLOATX))
    return x


def tanh(x):
    return tf.nn.tanh(x)


def dropout(x, level, seed=None):
    retain_prob = 1. - level
    if seed is None:
        seed = np.random.randint(10e6)
    # the dummy 1. works around a TF bug
    # (float32_ref vs. float32 incomptability)
    return tf.nn.dropout(x * 1., retain_prob, seed=seed)


# CONVOLUTIONS


def conv2d(x, kernel, strides=(1, 1), border_mode='valid', dim_ordering='th',
           image_shape=None, filter_shape=None):
    '''
    Run on cuDNN if available.
    border_mode: string, "same" or "valid".
    dim_ordering: whether to use Theano or TensorFlow dimension ordering
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
    '''
    pool_size: tuple of 2 integers.
    strides: tuple of 2 integers.
    border_mode: one of "valid", "same".
    dim_ordering: one of "th", "tf".
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

import numpy as np

# the type of float to use throughout the session.
_FLOATX = 'float32'
_EPSILON = 10e-8


def epsilon():
    return _EPSILON


def set_epsilon(e):
    global _EPSILON
    _EPSILON = e


def floatx():
    return _FLOATX


def set_floatx(floatx):
    global _FLOATX
    if floatx not in {'float32', 'float64'}:
        raise Exception('Unknown floatx type: ' + str(floatx))
    floatx = str(floatx)
    _FLOATX = floatx


def cast_to_floatx(x):
    '''Cast a Numpy array to floatx.
    '''
    return np.asarray(x, dtype=_FLOATX)

from __future__ import absolute_import
# -*- coding: utf-8 -*-
import numpy as np
import random
from six.moves import range

def pad_sequences(sequences, maxlen=None, dtype='int32', padding='pre', truncating='pre', value=0.):
    """
        Pad each sequence to the same length: 
        the length of the longest sequence.

        If maxlen is provided, any sequence longer
        than maxlen is truncated to maxlen. Truncation happens off either the beginning (default) or
        the end of the sequence.

        Supports post-padding and pre-padding (default).

    """
    lengths = [len(s) for s in sequences]

    nb_samples = len(sequences)
    if maxlen is None:
        maxlen = np.max(lengths)

    x = (np.ones((nb_samples, maxlen)) * value).astype(dtype)
    for idx, s in enumerate(sequences):
        if len(s) == 0:
            continue # empty list was found
        if truncating == 'pre':
            trunc = s[-maxlen:]
        elif truncating == 'post':
            trunc = s[:maxlen]
        else:
            raise ValueError("Truncating type '%s' not understood" % padding)

        if padding == 'post':
            x[idx, :len(trunc)] = trunc
        elif padding == 'pre':
            x[idx, -len(trunc):] = trunc
        else:
            raise ValueError("Padding type '%s' not understood" % padding)
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
    seq = text_to_word_sequence(text, filters=filters, lower=lower, split=split)
    return [(abs(hash(w)) % (n - 1) + 1) for w in seq]


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
        wcounts.sort(key=lambda x: x[1], reverse=True)
        sorted_voc = [wc[0] for wc in wcounts]
        self.word_index = dict(list(zip(sorted_voc, list(range(1, len(sorted_voc) + 1)))))

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
                nb_words = len(self.word_index) + 1
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
                    X[i][j] = c / len(seq)
                elif mode == "binary":
                    X[i][j] = 1
                elif mode == "tfidf":
                    tf = np.log(c / len(seq))
                    df = (1 + np.log(1 + self.index_docs.get(j, 0) / (1 + self.document_count)))
                    X[i][j] = tf / df
                else:
                    raise Exception("Unknown vectorization mode: " + str(mode))
        return X

from __future__ import absolute_import

import numpy as np
import re
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
    img = Image.open(path)
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
            augment=False,  # fit on randomly augmented samples
            rounds=1,  # if augment, how many augmentation passes over the data do we use
            seed=None):
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

# -*- coding: utf-8 -*-
from __future__ import print_function
import re
import inspect
import os
import shutil

from keras.layers import convolutional
from keras.layers import recurrent
from keras.layers import core
from keras.layers import noise
from keras.layers import normalization
from keras.layers import advanced_activations
from keras.layers import containers
from keras.layers import embeddings
from keras import optimizers
from keras import callbacks
from keras import models

MODULES = [(convolutional, 'keras.layers.convolutional'),
           (recurrent, 'keras.layers.recurrent'),
           (noise, 'keras.layers.noise'),
           (normalization, 'keras.layers.normalization'),
           (advanced_activations, 'keras.layers.advanced_activations'),
           (containers, 'keras.layers.containers'),
           (core, 'keras.layers.core'),
           (embeddings, 'keras.layers.embeddings'),
           (optimizers, 'keras.optimizers'),
           (callbacks, 'keras.callbacks'),
           (models, 'keras.models')]

SKIP = ['build', 'get_params', 'MaskedLayer',
        'SiameseHead', 'MaskedLambda',
        'CallbackList']
ROOT = 'http://keras.io/'
INCLUDE_METHODS_FOR = [
    'Layer',
    'Graph',
    'Sequential',
    'Callback',
]


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


def get_method_signature(method):
    signature = inspect.getargspec(method)
    defaults = signature.defaults
    args = signature.args[1:]
    if defaults:
        kwargs = zip(args[-len(defaults):], defaults)
        args = args[:-len(defaults)]
    else:
        kwargs = []
    st = '%s.%s(' % (method.__module__, method.__name__)
    for a in args:
        st += str(a) + ', '
    for a, v in kwargs:
        st += str(a) + '=' + str(v) + ', '
    if kwargs or args:
        return st[:-2] + ')'
    else:
        return st + ')'


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
    docstring = re.sub(r'    # (.*)\n',
                       r'    __\1__\n\n',
                       docstring)

    docstring = re.sub(r'    ([^\s\\]+):(.*)\n',
                       r'    - __\1__:\2\n',
                       docstring)
    docstring = docstring.replace('    ' * 3, '\t')
    docstring = docstring.replace('    ', '')
    return docstring


def process_method_docstring(docstring):
    docstring = re.sub(r'    # (.*)\n',
                       r'    __\1__\n\n',
                       docstring)

    docstring = re.sub(r'    ([^\s\\]+):(.*)\n',
                       r'    - __\1__:\2\n',
                       docstring)
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
covered_so_far = set()
for module, module_name in MODULES:
    class_pages = []
    for name in dir(module):
        if name in SKIP:
            continue
        if name[0] == '_':
            continue
        module_member = getattr(module, name)
        if module_member in covered_so_far:
            continue
        if inspect.isclass(module_member):
            cls = module_member
            if cls.__module__ == module_name:

                try:
                    class_signature = get_method_signature(cls.__init__)
                    class_signature = class_signature.replace('__init__', cls.__name__)
                except:
                    # in case the class inherits from object and does not
                    # define __init__
                    class_signature = module_name + '.' + cls.__name__ + '()'

                methods = []
                methods_not_defined_here = []
                for name in dir(cls):
                    if name in SKIP:
                        continue
                    if name[0] == '_':
                        continue
                    cls_member = getattr(cls, name)
                    if inspect.ismethod(cls_member):
                        method = cls_member
                        signature = inspect.getargspec(method)
                        defaults = signature.defaults
                        args = signature.args[1:]
                        if defaults:
                            kwargs = zip(args[-len(defaults):], defaults)
                            args = args[:-len(defaults)]
                        else:
                            kwargs = []

                        defined_by = get_earliest_class_that_defined_member(method.__name__, cls)
                        if cls == defined_by:
                            methods.append(method)
                        else:
                            methods_not_defined_here.append((method, defined_by))

                blocks = []
                blocks.append('<span style="float:right;">' + class_to_source_link(cls) + '</span>')
                blocks.append('# ' + cls.__name__ + '\n')
                blocks.append(code_snippet(class_signature))
                docstring = cls.__doc__
                if docstring:
                    blocks.append(process_class_docstring(docstring))

                if cls.__name__ in INCLUDE_METHODS_FOR:
                    if methods or methods_not_defined_here:
                        blocks.append('### Methods\n')
                        for method in methods:
                            signature = get_method_signature(method)
                            signature = signature.replace(module_name + '.', '')
                            blocks.append(code_snippet(signature))
                            docstring = method.__doc__
                            if docstring:
                                blocks.append(process_method_docstring(docstring))
                        for method, defined_by in methods_not_defined_here:
                            signature = get_method_signature(method)
                            method_module_name = method.__module__
                            signature = signature.replace(method_module_name + '.', '')
                            link = '[' + defined_by.__name__ + '](' + class_to_docs_link(defined_by) + ')'
                            blocks.append(code_snippet(signature))
                            blocks.append('Defined by ' + link + '.\n')

                mkdown = '\n'.join(blocks)
                class_pages.append((id(cls), mkdown))
                covered_so_far.add(module_member)

    class_pages.sort(key=lambda x: x[0])
    class_pages = [x[1] for x in class_pages]
    module_page = '\n----\n\n'.join(class_pages)

    # save module page.
    # Either insert content into existing page,
    # or create page otherwise
    path = 'sources/' + module_name.replace('.', '/')[6:] + '.md'
    if os.path.exists(path):
        template = open(path).read()
        assert '{{autogenerated}}' in template, ('Template found for ' + path +
                                                 ' but missing {{autogenerated}} tag.')
        module_page = template.replace('{{autogenerated}}', module_page)
        print('...inserting autogenerated content into template:', path)
    else:
        print('...creating new page with autogenerated content:', path)
    open(path, 'w').write(module_page)

'''Train a simple deep NN on the MNIST dataset.

Get to 98.40% test accuracy after 20 epochs
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

# the data, shuffled and split between tran and test sets
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

rms = RMSprop()
model.compile(loss='categorical_crossentropy', optimizer=rms)

model.fit(X_train, Y_train,
          batch_size=batch_size, nb_epoch=nb_epoch,
          show_accuracy=True, verbose=2,
          validation_data=(X_test, Y_test))
score = model.evaluate(X_test, Y_test,
                       show_accuracy=True, verbose=0)
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
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Activation
from keras.initializations import normal, identity
from keras.layers.recurrent import SimpleRNN, LSTM
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
                    init=lambda shape: normal(shape, scale=0.001),
                    inner_init=lambda shape: identity(shape, scale=1.0),
                    activation='relu', input_shape=X_train.shape[1:]))
model.add(Dense(nb_classes))
model.add(Activation('softmax'))
rmsprop = RMSprop(lr=learning_rate)
model.compile(loss='categorical_crossentropy', optimizer=rmsprop)

model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epochs,
          show_accuracy=True, verbose=1, validation_data=(X_test, Y_test))

scores = model.evaluate(X_test, Y_test, show_accuracy=True, verbose=0)
print('IRNN test score:', scores[0])
print('IRNN test accuracy:', scores[1])

print('Compare to LSTM...')
model = Sequential()
model.add(LSTM(hidden_units, input_shape=X_train.shape[1:]))
model.add(Dense(nb_classes))
model.add(Activation('softmax'))
rmsprop = RMSprop(lr=learning_rate)
model.compile(loss='categorical_crossentropy', optimizer=rmsprop)

model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epochs,
          show_accuracy=True, verbose=1, validation_data=(X_test, Y_test))

scores = model.evaluate(X_test, Y_test, show_accuracy=True, verbose=0)
print('LSTM test score:', scores[0])
print('LSTM test accuracy:', scores[1])

'''Train a simple convnet on the MNIST dataset.

Run on GPU: THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python mnist_cnn.py

Get to 99.25% test accuracy after 12 epochs (there is still a lot of margin for parameter tuning).
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

# the data, shuffled and split between tran and test sets
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

model.compile(loss='categorical_crossentropy', optimizer='adadelta')

model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch,
          show_accuracy=True, verbose=1, validation_data=(X_test, Y_test))
score = model.evaluate(X_test, Y_test, show_accuracy=True, verbose=0)
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
from keras.datasets.data_utils import get_file
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
maxlen = 20
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

'''This example demonstrates the use of Convolution1D for text classification.

Run on GPU: THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python imdb_cnn.py

Get to 0.835 test accuracy after 2 epochs. 100s/epoch on K520 GPU.
'''

from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.embeddings import Embedding
from keras.layers.convolutional import Convolution1D, MaxPooling1D
from keras.datasets import imdb


# set parameters:
max_features = 5000
maxlen = 100
batch_size = 32
embedding_dims = 100
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
model.add(Embedding(max_features, embedding_dims, input_length=maxlen))
model.add(Dropout(0.25))

# we add a Convolution1D, which will learn nb_filter
# word group filters of size filter_length:
model.add(Convolution1D(nb_filter=nb_filter,
                        filter_length=filter_length,
                        border_mode='valid',
                        activation='relu',
                        subsample_length=1))
# we use standard max pooling (halving the output of the previous layer):
model.add(MaxPooling1D(pool_length=2))

# We flatten the output of the conv layer,
# so that we can add a vanilla dense layer:
model.add(Flatten())

# We add a vanilla hidden layer:
model.add(Dense(hidden_dims))
model.add(Dropout(0.25))
model.add(Activation('relu'))

# We project onto a single unit output layer, and squash it with a sigmoid:
model.add(Dense(1))
model.add(Activation('sigmoid'))

model.compile(loss='binary_crossentropy',
              optimizer='rmsprop',
              class_mode='binary')
model.fit(X_train, y_train, batch_size=batch_size,
          nb_epoch=nb_epoch, show_accuracy=True,
          validation_data=(X_test, y_test))

'''Train a LSTM on the IMDB sentiment classification task.

The dataset is actually too small for LSTM to be of any advantage
compared to simpler, much faster methods such as TF-IDF+LogReg.

Notes:

- RNNs are tricky. Choice of batch size is important,
choice of loss and optimizer is critical, etc.
Some configurations won't converge.

- LSTM loss decrease patterns during training can be quite different
from what you see with CNNs/MLPs/etc.

GPU command:
    THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python imdb_lstm.py
'''

from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.preprocessing import sequence
from keras.utils import np_utils
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM
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

print('Build model...')
model = Sequential()
model.add(Embedding(max_features, 128, input_length=maxlen))
model.add(LSTM(128))  # try using a GRU instead, for fun
model.add(Dropout(0.5))
model.add(Dense(1))
model.add(Activation('sigmoid'))

# try using different optimizers and different optimizer configs
model.compile(loss='binary_crossentropy',
              optimizer='adam',
              class_mode="binary")

print("Train...")
model.fit(X_train, y_train, batch_size=batch_size, nb_epoch=3,
          validation_data=(X_test, y_test), show_accuracy=True)
score, acc = model.evaluate(X_test, y_test,
                            batch_size=batch_size,
                            show_accuracy=True)
print('Test score:', score)
print('Test accuracy:', acc)

'''Train a Bidirectional LSTM on the IMDB sentiment classification task.

GPU command:
    THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python imdb_bidirectional_lstm.py

Output after 4 epochs on CPU: ~0.8146
Time per epoch on CPU (Core i7): ~150s.
'''

from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.preprocessing import sequence
from keras.utils.np_utils import accuracy
from keras.models import Graph
from keras.layers.core import Dense, Dropout
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM
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

print('Build model...')
model = Graph()
model.add_input(name='input', input_shape=(maxlen,), dtype=int)
model.add_node(Embedding(max_features, 128, input_length=maxlen),
               name='embedding', input='input')
model.add_node(LSTM(64), name='forward', input='embedding')
model.add_node(LSTM(64, go_backwards=True), name='backward', input='embedding')
model.add_node(Dropout(0.5), name='dropout', inputs=['forward', 'backward'])
model.add_node(Dense(1, activation='sigmoid'), name='sigmoid', input='dropout')
model.add_output(name='output', input='sigmoid')

# try using different optimizers and different optimizer configs
model.compile('adam', {'output': 'binary_crossentropy'})

print('Train...')
model.fit({'input': X_train, 'output': y_train},
          batch_size=batch_size,
          nb_epoch=4)
acc = accuracy(y_test,
               np.round(np.array(model.predict({'input': X_test},
                                               batch_size=batch_size)['output'])))
print('Test accuracy:', acc)

'''This demonstrates how to reach a score of 0.4890 (local validation)
on the Kaggle Otto challenge, with a deep net using Keras.

Requires Scikit-Learn and Pandas.

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

Get the data from Kaggle:
https://www.kaggle.com/c/otto-group-product-classification-challenge/data
'''

from __future__ import print_function
import numpy as np
import pandas as pd
np.random.seed(1337)  # for reproducibility

from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.normalization import BatchNormalization
from keras.layers.advanced_activations import PReLU
from keras.utils import np_utils, generic_utils

from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler


def load_data(path, train=True):
    df = pd.read_csv(path)
    X = df.values.copy()
    if train:
        np.random.shuffle(X)  # https://youtu.be/uyUXoap67N8
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
    print('Wrote submission to file {}.'.format(fname))

print('Loading data...')
X, labels = load_data('train.csv', train=True)
X, scaler = preprocess_data(X)
y, encoder = preprocess_labels(labels)

X_test, ids = load_data('test.csv', train=False)
X_test, _ = preprocess_data(X_test, scaler)

nb_classes = y.shape[1]
print(nb_classes, 'classes')

dims = X.shape[1]
print(dims, 'dims')

print('Building model...')

model = Sequential()
model.add(Dense(512, input_shape=(dims,)))
model.add(PReLU())
model.add(BatchNormalization())
model.add(Dropout(0.5))

model.add(Dense(512))
model.add(PReLU())
model.add(BatchNormalization())
model.add(Dropout(0.5))

model.add(Dense(512))
model.add(PReLU())
model.add(BatchNormalization())
model.add(Dropout(0.5))

model.add(Dense(nb_classes))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy', optimizer='adam')

print('Training model...')
model.fit(X, y, nb_epoch=20, batch_size=128, validation_split=0.15)

print('Generating submission...')
proba = model.predict_proba(X_test)
make_submission(proba, ids, encoder, fname='keras-otto.csv')

'''Trains two recurrent neural networks based upon a story and a question.
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
  - 52.1% test accuracy on QA1 in 20 epochs (2 seconds per epoch on CPU)
  - 37.0% test accuracy on QA2 in 20 epochs (16 seconds per epoch on CPU)
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

from keras.datasets.data_utils import get_file
from keras.layers.embeddings import Embedding
from keras.layers.core import Dense, Merge
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

RNN = recurrent.GRU
EMBED_HIDDEN_SIZE = 50
SENT_HIDDEN_SIZE = 100
QUERY_HIDDEN_SIZE = 100
BATCH_SIZE = 32
EPOCHS = 20
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
sentrnn.add(Embedding(vocab_size, EMBED_HIDDEN_SIZE, mask_zero=True))
sentrnn.add(RNN(SENT_HIDDEN_SIZE, return_sequences=False))

qrnn = Sequential()
qrnn.add(Embedding(vocab_size, EMBED_HIDDEN_SIZE))
qrnn.add(RNN(QUERY_HIDDEN_SIZE, return_sequences=False))

model = Sequential()
model.add(Merge([sentrnn, qrnn], mode='concat'))
model.add(Dense(vocab_size, activation='softmax'))

model.compile(optimizer='adam', loss='categorical_crossentropy', class_mode='categorical')

print('Training')
model.fit([X, Xq], Y, batch_size=BATCH_SIZE, nb_epoch=EPOCHS, validation_split=0.05, show_accuracy=True)
loss, acc = model.evaluate([tX, tXq], tY, batch_size=BATCH_SIZE, show_accuracy=True)
print('Test loss / test accuracy = {:.4f} / {:.4f}'.format(loss, acc))

'''Train and evaluate a simple MLP on the Reuters newswire topic classification task.
GPU run command:
    THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python examples/reuters_mlp.py
CPU run command:
    python examples/reuters_mlp.py
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

model.compile(loss='categorical_crossentropy', optimizer='adam')

history = model.fit(X_train, Y_train, nb_epoch=nb_epoch, batch_size=batch_size, verbose=1, show_accuracy=True, validation_split=0.1)
score = model.evaluate(X_test, Y_test, batch_size=batch_size, verbose=1, show_accuracy=True)
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
from keras.models import Sequential, slice_X
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

model.compile(loss='categorical_crossentropy', optimizer='adam')

# Train the model each generation and show predictions against the validation dataset
for iteration in range(1, 200):
    print()
    print('-' * 50)
    print('Iteration', iteration)
    model.fit(X_train, y_train, batch_size=BATCH_SIZE, nb_epoch=1,
              validation_data=(X_val, y_val), show_accuracy=True)
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

'''Train a memory network on the bAbI dataset.

References:
- Jason Weston, Antoine Bordes, Sumit Chopra, Tomas Mikolov, Alexander M. Rush,
  "Towards AI-Complete Question Answering: A Set of Prerequisite Toy Tasks",
  http://arxiv.org/abs/1503.08895

- Sainbayar Sukhbaatar, Arthur Szlam, Jason Weston, Rob Fergus,
  "End-To-End Memory Networks",
  http://arxiv.org/abs/1503.08895

Reaches 93% accuracy on task 'single_supporting_fact_10k' after 70 epochs.
Time per epoch: 3s on CPU (core i7).
'''

from __future__ import print_function
from keras.models import Sequential
from keras.layers.embeddings import Embedding
from keras.layers.core import Activation, Dense, Merge, Permute, Dropout
from keras.layers.recurrent import LSTM
from keras.datasets.data_utils import get_file
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
# output: (samples, story_maxlen, embedding_dim)
# embed the question into a sequence of vectors
question_encoder = Sequential()
question_encoder.add(Embedding(input_dim=vocab_size,
                               output_dim=64,
                               input_length=query_maxlen))
# output: (samples, query_maxlen, embedding_dim)
# compute a 'match' between input sequence elements (which are vectors)
# and the question vector sequence
match = Sequential()
match.add(Merge([input_encoder_m, question_encoder],
                mode='dot',
                dot_axes=[(2,), (2,)]))
# output: (samples, story_maxlen, query_maxlen)
# embed the input into a single vector with size = story_maxlen:
input_encoder_c = Sequential()
input_encoder_c.add(Embedding(input_dim=vocab_size,
                              output_dim=query_maxlen,
                              input_length=story_maxlen))
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
answer.add(LSTM(64))
# one regularization layer -- more would probably be needed.
answer.add(Dropout(0.25))
answer.add(Dense(vocab_size))
# we output a probability distribution over the vocabulary
answer.add(Activation('softmax'))

answer.compile(optimizer='rmsprop', loss='categorical_crossentropy')
# Note: you could use a Graph model to avoid repeat the input twice
answer.fit([inputs_train, queries_train, inputs_train], answers_train,
           batch_size=32,
           nb_epoch=70,
           show_accuracy=True,
           validation_data=([inputs_test, queries_test, inputs_test], answers_test))

'''Train a recurrent convolutional network on the IMDB sentiment
classification task.

GPU command:
    THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python imdb_lstm.py

Get to 0.8498 test accuracy after 2 epochs. 41s/epoch on K520 GPU.
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
              class_mode='binary')

print('Train...')
model.fit(X_train, y_train, batch_size=batch_size, nb_epoch=nb_epoch,
          validation_data=(X_test, y_test), show_accuracy=True)
score, acc = model.evaluate(X_test, y_test, batch_size=batch_size,
                            show_accuracy=True)
print('Test score:', score)
print('Test accuracy:', acc)

'''Transfer learning toy example:

1- Train a simple convnet on the MNIST dataset the first 5 digits [0..4].
2- Freeze convolutional layers and fine-tune dense layers
   for the classification of digits [5..9].

Run on GPU: THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python mnist_cnn.py

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

    model.compile(loss='categorical_crossentropy', optimizer='adadelta')

    t = now()
    model.fit(X_train, Y_train,
              batch_size=batch_size, nb_epoch=nb_epoch,
              show_accuracy=True, verbose=1,
              validation_data=(X_test, Y_test))
    print('Training time: %s' % (now() - t))
    score = model.evaluate(X_test, Y_test, show_accuracy=True, verbose=0)
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
from keras.optimizers import SGD, Adadelta, Adagrad
from keras.utils import np_utils, generic_utils
from six.moves import range

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
model.compile(loss='categorical_crossentropy', optimizer=sgd)

X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
X_train /= 255
X_test /= 255

if not data_augmentation:
    print('Not using data augmentation or normalization')
    model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch)
    score = model.evaluate(X_test, Y_test, batch_size=batch_size)
    print('Test score:', score)

else:
    print('Using real time data augmentation')

    # this will do preprocessing and realtime data augmentation
    datagen = ImageDataGenerator(
        featurewise_center=True,  # set input mean to 0 over the dataset
        samplewise_center=False,  # set each sample mean to 0
        featurewise_std_normalization=True,  # divide inputs by std of the dataset
        samplewise_std_normalization=False,  # divide each input by its std
        zca_whitening=False,  # apply ZCA whitening
        rotation_range=20,  # randomly rotate images in the range (degrees, 0 to 180)
        width_shift_range=0.2,  # randomly shift images horizontally (fraction of total width)
        height_shift_range=0.2,  # randomly shift images vertically (fraction of total height)
        horizontal_flip=True,  # randomly flip images
        vertical_flip=False)  # randomly flip images

    # compute quantities required for featurewise normalization
    # (std, mean, and principal components if ZCA whitening is applied)
    datagen.fit(X_train)

    for e in range(nb_epoch):
        print('-'*40)
        print('Epoch', e)
        print('-'*40)
        print('Training...')
        # batch train with realtime data augmentation
        progbar = generic_utils.Progbar(X_train.shape[0])
        for X_batch, Y_batch in datagen.flow(X_train, Y_train):
            loss = model.train_on_batch(X_batch, Y_batch)
            progbar.add(X_batch.shape[0], values=[('train loss', loss[0])])

        print('Testing...')
        # test time!
        progbar = generic_utils.Progbar(X_test.shape[0])
        for X_batch, Y_batch in datagen.flow(X_test, Y_test):
            score = model.test_on_batch(X_batch, Y_batch)
            progbar.add(X_batch.shape[0], values=[('test loss', score[0])])

