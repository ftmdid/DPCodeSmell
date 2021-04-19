from setuptools import setup
from setuptools import find_packages


setup(name='Keras',
      version='0.2.0',
      description='Theano-based Deep Learning library',
      author='Francois Chollet',
      author_email='francois.chollet@gmail.com',
      url='https://github.com/fchollet/keras',
      download_url='https://github.com/fchollet/keras/tarball/0.2.0',
      license='MIT',
      install_requires=['theano', 'pyyaml', 'six'],
      extras_require={
          'h5py': ['h5py'],
      },
      packages=find_packages())

from __future__ import absolute_import
from __future__ import print_function
import theano
import theano.tensor as T
import numpy as np
import warnings, time, copy, pprint
from six.moves import range
import six

from . import optimizers
from . import objectives
from . import regularizers
from . import constraints
from . import callbacks as cbks
from .utils.layer_utils import container_from_config
from .utils.generic_utils import Progbar, printv
from .layers import containers


def standardize_y(y):
    if not hasattr(y, 'shape'):
        y = np.asarray(y)
    if len(y.shape) == 1:
        y = np.expand_dims(y, 1)
    return y


def batch_shuffle(index_array, batch_size):
    batch_count = int(len(index_array)/batch_size)
    # to reshape we need to be cleanly divisible by batch size
    # we stash extra items and reappend them after shuffling
    last_batch = index_array[batch_count*batch_size:]
    index_array = index_array[:batch_count*batch_size]
    index_array = index_array.reshape((batch_count, batch_size))
    np.random.shuffle(index_array)
    index_array = index_array.flatten()
    return np.append(index_array, last_batch)


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
        # it's important that 0 * Inf == 0, not NaN, so we need to filter
        # those out first
        filtered_y_true = y_true[weights.nonzero()[:-1]]
        filtered_y_pred = y_pred[weights.nonzero()[:-1]]
        filtered_weights = weights[weights.nonzero()]
        obj_output = fn(filtered_y_true, filtered_y_pred)
        weighted = filtered_weights * obj_output
        if mask is None:
            # Instead of calling mean() here, we divide by the sum of filtered_weights.
            return weighted.sum() / filtered_weights.sum()
        else:
            filtered_mask = mask[weights.nonzero()[:-1]]
            return weighted.sum() / (filtered_mask * filtered_weights).sum()
    return weighted


def standardize_weights(y, sample_weight=None, class_weight=None):
    if sample_weight is not None:
        return standardize_y(sample_weight)
    elif isinstance(class_weight, dict):
        if len(y.shape) > 3:
            raise Exception('class_weight not supported for 4+ dimensional targets.')
        yshape = y.shape
        y = np.reshape(y, (-1, yshape[-1]))  # for time-distributed data, collapse time and sample
        if y.shape[1] > 1:
            y_classes = y.argmax(axis=1)
        elif y.shape[1] == 1:
            y_classes = np.reshape(y, y.shape[0])
        else:
            y_classes = y
        class_weights = np.asarray([class_weight[cls] for cls in y_classes])
        return np.reshape(class_weights, yshape[:-1] + (1,))  # uncollapse initial dimensions
    else:
        return np.ones(y.shape[:-1] + (1,))


def model_from_yaml(yaml_string, custom_objects={}):
    '''
        Returns a model generated from a local yaml file,
        which is either created by hand or from to_yaml method of Sequential or Graph
    '''
    import yaml
    config = yaml.load(yaml_string)
    return model_from_config(config, custom_objects=custom_objects)


def model_from_json(json_string, custom_objects={}):
    import json
    config = json.loads(json_string)
    return model_from_config(config, custom_objects=custom_objects)


def model_from_config(config, custom_objects={}):
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
        theano_mode = config.get('theano_mode')

        optimizer_params = dict([(k, v) for k, v in config.get('optimizer').items()])
        optimizer_name = optimizer_params.pop('name')
        optimizer = optimizers.get(optimizer_name, optimizer_params)

        if model_name == 'Sequential':
            model.compile(loss=loss, optimizer=optimizer, class_mode=class_mode, theano_mode=theano_mode)
        elif model_name == 'Graph':
            model.compile(loss=loss, optimizer=optimizer, theano_mode=theano_mode)

    return model


def get_function_name(o):
    if isinstance(o, six.string_types):
        return o
    else:
        return o.__name__


class Model(object):
    def _fit(self, f, ins, out_labels=[], batch_size=128, nb_epoch=100, verbose=1, callbacks=[],
             val_f=None, val_ins=None, shuffle=True, metrics=[]):
        '''
            Abstract fit function for f(*ins). Assume that f returns a list, labelled by out_labels.
        '''
        do_validation = False
        if val_f and val_ins:
            do_validation = True
            if verbose:
                print("Train on %d samples, validate on %d samples" % (len(ins[0]), len(val_ins[0])))

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
                except TypeError as err:
                    raise Exception('TypeError while preparing batch. \
                        If using HDF5 input data, pass shuffle="batch".\n')

                batch_logs = {}
                batch_logs['batch'] = batch_index
                batch_logs['size'] = len(batch_ids)
                callbacks.on_batch_begin(batch_index, batch_logs)
                outs = f(*ins_batch)
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
                        val_outs = self._test_loop(val_f, val_ins, batch_size=batch_size, verbose=0)
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
        '''
            Abstract method to loop over some data in batches.
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

            batch_outs = f(*ins_batch)
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
        '''
            Abstract method to loop over some data in batches.
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

            batch_outs = f(*ins_batch)
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
        config = super(Model, self).get_config()
        for p in ['class_mode', 'theano_mode']:
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
        # dump model configuration to yaml string
        import yaml
        config = self.get_config()
        return yaml.dump(config, **kwargs)

    def to_json(self, **kwargs):
        # dump model configuration to json string
        import json
        config = self.get_config()
        return json.dumps(config, **kwargs)


class Sequential(Model, containers.Sequential):
    '''
        Inherits from Model the following methods:
            - _fit
            - _predict
            - _evaluate
        Inherits from containers.Sequential the following methods:
            - __init__
            - add
            - get_output
            - get_input
            - get_weights
            - set_weights
    '''

    def compile(self, optimizer, loss, class_mode="categorical", theano_mode=None):
        self.optimizer = optimizers.get(optimizer)

        self.loss = objectives.get(loss)
        weighted_loss = weighted_objective(objectives.get(loss))

        # input of model
        self.X_train = self.get_input(train=True)
        self.X_test = self.get_input(train=False)

        self.y_train = self.get_output(train=True)
        self.y_test = self.get_output(train=False)

        # target of model
        self.y = T.zeros_like(self.y_train)

        self.weights = T.ones_like(self.y_train)

        if hasattr(self.layers[-1], "get_output_mask"):
            mask = self.layers[-1].get_output_mask()
        else:
            mask = None
        train_loss = weighted_loss(self.y, self.y_train, self.weights, mask)
        test_loss = weighted_loss(self.y, self.y_test, self.weights, mask)

        train_loss.name = 'train_loss'
        test_loss.name = 'test_loss'
        self.y.name = 'y'

        if class_mode == "categorical":
            train_accuracy = T.mean(T.eq(T.argmax(self.y, axis=-1), T.argmax(self.y_train, axis=-1)))
            test_accuracy = T.mean(T.eq(T.argmax(self.y, axis=-1), T.argmax(self.y_test, axis=-1)))

        elif class_mode == "binary":
            train_accuracy = T.mean(T.eq(self.y, T.round(self.y_train)))
            test_accuracy = T.mean(T.eq(self.y, T.round(self.y_test)))
        else:
            raise Exception("Invalid class mode:" + str(class_mode))
        self.class_mode = class_mode
        self.theano_mode = theano_mode

        for r in self.regularizers:
            train_loss = r(train_loss)
        updates = self.optimizer.get_updates(self.params, self.constraints, train_loss)
        updates += self.updates

        if type(self.X_train) == list:
            train_ins = self.X_train + [self.y, self.weights]
            test_ins = self.X_test + [self.y, self.weights]
            predict_ins = self.X_test
        else:
            train_ins = [self.X_train, self.y, self.weights]
            test_ins = [self.X_test, self.y, self.weights]
            predict_ins = [self.X_test]

        self._train = theano.function(train_ins, train_loss, updates=updates,
                                      allow_input_downcast=True, mode=theano_mode)
        self._train_with_acc = theano.function(train_ins, [train_loss, train_accuracy], updates=updates,
                                               allow_input_downcast=True, mode=theano_mode)
        self._predict = theano.function(predict_ins, self.y_test,
                                        allow_input_downcast=True, mode=theano_mode)
        self._test = theano.function(test_ins, test_loss,
                                     allow_input_downcast=True, mode=theano_mode)
        self._test_with_acc = theano.function(test_ins, [test_loss, test_accuracy],
                                              allow_input_downcast=True, mode=theano_mode)

    def train_on_batch(self, X, y, accuracy=False, class_weight=None, sample_weight=None):
        X = standardize_X(X)
        y = standardize_y(y)
        sample_weight = standardize_weights(y, class_weight=class_weight, sample_weight=sample_weight)

        ins = X + [y, sample_weight]
        if accuracy:
            return self._train_with_acc(*ins)
        else:
            return self._train(*ins)

    def test_on_batch(self, X, y, accuracy=False, sample_weight=None):
        X = standardize_X(X)
        y = standardize_y(y)
        sample_weight = standardize_weights(y, sample_weight=sample_weight)

        ins = X + [y, sample_weight]
        if accuracy:
            return self._test_with_acc(*ins)
        else:
            return self._test(*ins)

    def predict_on_batch(self, X):
        ins = standardize_X(X)
        return self._predict(*ins)

    def fit(self, X, y, batch_size=128, nb_epoch=100, verbose=1, callbacks=[],
            validation_split=0., validation_data=None, shuffle=True, show_accuracy=False,
            class_weight=None, sample_weight=None):

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
                sample_weight_val = np.ones(y_val.shape[:-1] + (1,))
            elif len(validation_data) == 3:
                X_val, y_val, sample_weight_val = validation_data
                X_val = standardize_X(X_val)
                y_val = standardize_y(y_val)
                sample_weight_val = standardize_weights(y_val, sample_weight=sample_weight_val)
            else:
                raise Exception("Invalid format for validation data; provide a tuple (X_val, y_val) or (X_val, y_val, sample_weight). \
                    X_val may be a numpy array or a list of numpy arrays depending on your model input.")
            val_ins = X_val + [y_val, sample_weight_val]

        elif 0 < validation_split < 1:
            split_at = int(len(X[0]) * (1 - validation_split))
            X, X_val = (slice_X(X, 0, split_at), slice_X(X, split_at))
            y, y_val = (slice_X(y, 0, split_at), slice_X(y, split_at))
            if sample_weight is not None:
                sample_weight, sample_weight_val = (slice_X(sample_weight, 0, split_at), slice_X(sample_weight, split_at))
                sample_weight_val = standardize_weights(y_val, sample_weight=sample_weight_val)
            else:
                sample_weight_val = np.ones(y_val.shape[:-1] + (1,))
            val_ins = X_val + [y_val, sample_weight_val]

        if show_accuracy:
            f = self._train_with_acc
            out_labels = ['loss', 'acc']
        else:
            f = self._train
            out_labels = ['loss']

        sample_weight = standardize_weights(y, class_weight=class_weight, sample_weight=sample_weight)
        ins = X + [y, sample_weight]
        metrics = ['loss', 'acc', 'val_loss', 'val_acc']
        return self._fit(f, ins, out_labels=out_labels, batch_size=batch_size, nb_epoch=nb_epoch,
                         verbose=verbose, callbacks=callbacks,
                         val_f=val_f, val_ins=val_ins,
                         shuffle=shuffle, metrics=metrics)

    def predict(self, X, batch_size=128, verbose=0):
        X = standardize_X(X)
        return self._predict_loop(self._predict, X, batch_size, verbose)[0]

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

    def evaluate(self, X, y, batch_size=128, show_accuracy=False, verbose=1, sample_weight=None):
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
        '''
            This method does not make use of Sequential.set_weights()
            for backwards compatibility.
        '''
        # Loads weights from HDF5 file
        import h5py
        f = h5py.File(filepath)
        for k in range(f.attrs['nb_layers']):
            g = f['layer_{}'.format(k)]
            weights = [g['param_{}'.format(p)] for p in range(g.attrs['nb_params'])]
            self.layers[k].set_weights(weights)
        f.close()


class Graph(Model, containers.Graph):
    def compile(self, optimizer, loss, theano_mode=None):
        # loss is a dictionary mapping output name to loss functions
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
            y = T.zeros_like(y_test)
            ys.append(y)
            ys_train.append(y_train)
            ys_test.append(y_test)

            if hasattr(output, "get_output_mask"):
                mask = output.get_output_mask()
            else:
                mask = None

            weight = T.ones_like(y_test)
            weights.append(weight)
            weighted_loss = weighted_objective(objectives.get(loss_fn))
            train_loss += weighted_loss(y, y_train, weight, mask)
            test_loss += weighted_loss(y, y_test, weight, mask)

        train_loss.name = 'train_loss'
        test_loss.name = 'test_loss'

        ins = [self.inputs[name].input for name in self.input_order]
        train_ins = ins + ys + weights
        test_ins = ins + ys + weights

        for r in self.regularizers:
            train_loss = r(train_loss)
        self.optimizer = optimizers.get(optimizer)
        updates = self.optimizer.get_updates(self.params, self.constraints, train_loss)
        updates += self.updates
        self.theano_mode = theano_mode
        self.loss = loss

        self._train = theano.function(train_ins, train_loss, updates=updates,
                                      allow_input_downcast=True, mode=theano_mode)
        self._test = theano.function(test_ins, test_loss,
                                     allow_input_downcast=True, mode=theano_mode)
        self._predict = theano.function(inputs=ins, outputs=ys_test,
                                        allow_input_downcast=True, mode=theano_mode)

    def train_on_batch(self, data, class_weight={}, sample_weight={}):
        # data is a dictionary mapping output and input names to arrays
        sample_weight = [standardize_weights(data[name],
                                             sample_weight=sample_weight.get(name),
                                             class_weight=class_weight.get(name)) for name in self.output_order]
        ins = [data[name] for name in self.input_order] + [standardize_y(data[name]) for name in self.output_order] + sample_weight
        return self._train(*ins)

    def test_on_batch(self, data, sample_weight={}):
        # data is a dictionary mapping input names to arrays
        sample_weight = [standardize_weights(data[name],
                                             sample_weight=sample_weight.get(name)) for name in self.output_order]
        ins = [data[name] for name in self.input_order] + [standardize_y(data[name]) for name in self.output_order] + sample_weight
        return self._test(*ins)

    def predict_on_batch(self, data):
        # data is a dictionary mapping input names to arrays
        ins = [data[name] for name in self.input_order]
        return self._predict(*ins)

    def fit(self, data, batch_size=128, nb_epoch=100, verbose=1, callbacks=[],
            validation_split=0., validation_data=None, shuffle=True, class_weight={}, sample_weight={}):
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
            sample_weight = [standardize_weights(validation_data[name]) for name in self.output_order]
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
        history = self._fit(f, ins, out_labels=out_labels, batch_size=batch_size, nb_epoch=nb_epoch,
                            verbose=verbose, callbacks=callbacks,
                            val_f=val_f, val_ins=val_ins,
                            shuffle=shuffle, metrics=metrics)
        return history

    def evaluate(self, data, batch_size=128, verbose=0, sample_weight={}):
        sample_weight = [standardize_weights(data[name],
                                             sample_weight=sample_weight.get(name)) for name in self.output_order]

        ins = [data[name] for name in self.input_order] + [standardize_y(data[name]) for name in self.output_order] + sample_weight
        outs = self._test_loop(self._test, ins, batch_size, verbose)
        return outs[0]

    def predict(self, data, batch_size=128, verbose=0):
        ins = [data[name] for name in self.input_order]
        outs = self._predict_loop(self._predict, ins, batch_size, verbose)
        return dict(zip(self.output_order, outs))

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
        g = f.create_group('graph')
        weights = self.get_weights()
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
        g = f['graph']
        weights = [g['param_{}'.format(p)] for p in range(g.attrs['nb_params'])]
        self.set_weights(weights)
        f.close()

from __future__ import absolute_import
import theano.tensor as T


def softmax(x):
    return T.nnet.softmax(x.reshape((-1, x.shape[-1]))).reshape(x.shape)


def time_distributed_softmax(x):
    import warnings
    warnings.warn("time_distributed_softmax is deprecated. Just use softmax!", DeprecationWarning)
    return softmax(x)


def softplus(x):
    return T.nnet.softplus(x)


def relu(x):
    return T.nnet.relu(x)


def tanh(x):
    return T.tanh(x)


def sigmoid(x):
    return T.nnet.sigmoid(x)


def hard_sigmoid(x):
    return T.nnet.hard_sigmoid(x)


def linear(x):
    '''
    The function returns the variable that is passed in, so all types work
    '''
    return x


from .utils.generic_utils import get_from_module
def get(identifier):
    return get_from_module(identifier, globals(), 'activation function')


"""
Keras: Theano-based Deep Learning library
==================================
Keras is a minimalist, highly modular neural network library in 
the spirit of Torch, written in Python / Theano so as not to have 
to deal with the dearth of ecosystem in Lua. It was developed with 
a focus on enabling fast experimentation. Being able to go from 
idea to result with the least possible delay is key to doing 
good research.

See http://keras.io/
"""

__version__ = '0.2.0'

from __future__ import absolute_import
import theano.tensor as T


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
        loss += T.sum(abs(self.p)) * self.l1
        loss += T.sum(self.p ** 2) * self.l2
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
        loss += self.l1 * T.sum(T.mean(abs(self.layer.get_output(True)), axis=0))
        loss += self.l2 * T.sum(T.mean(self.layer.get_output(True) ** 2, axis=0))
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
    return get_from_module(identifier, globals(), 'regularizer', instantiate=True, kwargs=kwargs)

from __future__ import absolute_import
import theano
import theano.tensor as T

from .utils.theano_utils import shared_zeros, shared_scalar, floatX
from .utils.generic_utils import get_from_module
from six.moves import zip


def clip_norm(g, c, n):
    if c > 0:
        g = T.switch(T.ge(n, c), g * c / n, g)
    return g


def kl_divergence(p, p_hat):
    return p_hat - p + p * T.log(p / p_hat)


class Optimizer(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.updates = []

    def get_state(self):
        return [u[0].get_value() for u in self.updates]

    def set_state(self, value_list):
        assert len(self.updates) == len(value_list)
        for u, v in zip(self.updates, value_list):
            u[0].set_value(floatX(v))

    def get_updates(self, params, constraints, loss):
        raise NotImplementedError

    def get_gradients(self, loss, params):

        grads = T.grad(loss, params)

        if hasattr(self, 'clipnorm') and self.clipnorm > 0:
            norm = T.sqrt(sum([T.sum(g ** 2) for g in grads]))
            grads = [clip_norm(g, self.clipnorm, norm) for g in grads]

        if hasattr(self, 'clipvalue') and self.clipvalue > 0:
            grads = [T.clip(g, -self.clipvalue, self.clipvalue) for g in grads]

        return grads

    def get_config(self):
        return {"name": self.__class__.__name__}


class SGD(Optimizer):

    def __init__(self, lr=0.01, momentum=0., decay=0., nesterov=False, *args, **kwargs):
        super(SGD, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.iterations = shared_scalar(0)
        self.lr = shared_scalar(lr)
        self.momentum = shared_scalar(momentum)
        self.decay = shared_scalar(decay)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        lr = self.lr * (1.0 / (1.0 + self.decay * self.iterations))
        self.updates = [(self.iterations, self.iterations + 1.)]

        for p, g, c in zip(params, grads, constraints):
            m = shared_zeros(p.get_value().shape)  # momentum
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
                "lr": float(self.lr.get_value()),
                "momentum": float(self.momentum.get_value()),
                "decay": float(self.decay.get_value()),
                "nesterov": self.nesterov}


class RMSprop(Optimizer):
    def __init__(self, lr=0.001, rho=0.9, epsilon=1e-6, *args, **kwargs):
        super(RMSprop, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.lr = shared_scalar(lr)
        self.rho = shared_scalar(rho)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        accumulators = [shared_zeros(p.get_value().shape) for p in params]
        self.updates = []

        for p, g, a, c in zip(params, grads, accumulators, constraints):
            new_a = self.rho * a + (1 - self.rho) * g ** 2  # update accumulator
            self.updates.append((a, new_a))

            new_p = p - self.lr * g / T.sqrt(new_a + self.epsilon)
            self.updates.append((p, c(new_p)))  # apply constraints
        return self.updates

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(self.lr.get_value()),
                "rho": float(self.rho.get_value()),
                "epsilon": self.epsilon}


class Adagrad(Optimizer):
    def __init__(self, lr=0.01, epsilon=1e-6, *args, **kwargs):
        super(Adagrad, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.lr = shared_scalar(lr)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        accumulators = [shared_zeros(p.get_value().shape) for p in params]
        self.updates = []

        for p, g, a, c in zip(params, grads, accumulators, constraints):
            new_a = a + g ** 2  # update accumulator
            self.updates.append((a, new_a))
            new_p = p - self.lr * g / T.sqrt(new_a + self.epsilon)
            self.updates.append((p, c(new_p)))  # apply constraints
        return self.updates

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(self.lr.get_value()),
                "epsilon": self.epsilon}


class Adadelta(Optimizer):
    '''
        Reference: http://arxiv.org/abs/1212.5701
    '''
    def __init__(self, lr=1.0, rho=0.95, epsilon=1e-6, *args, **kwargs):
        super(Adadelta, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.lr = shared_scalar(lr)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        accumulators = [shared_zeros(p.get_value().shape) for p in params]
        delta_accumulators = [shared_zeros(p.get_value().shape) for p in params]
        self.updates = []

        for p, g, a, d_a, c in zip(params, grads, accumulators,
                                   delta_accumulators, constraints):
            new_a = self.rho * a + (1 - self.rho) * g ** 2  # update accumulator
            self.updates.append((a, new_a))

            # use the new accumulator and the *old* delta_accumulator
            update = g * T.sqrt(d_a + self.epsilon) / T.sqrt(new_a +
                                                             self.epsilon)

            new_p = p - self.lr * update
            self.updates.append((p, c(new_p)))  # apply constraints

            # update delta_accumulator
            new_d_a = self.rho * d_a + (1 - self.rho) * update ** 2
            self.updates.append((d_a, new_d_a))
        return self.updates

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(self.lr.get_value()),
                "rho": self.rho,
                "epsilon": self.epsilon}


class Adam(Optimizer):
    '''
        Reference: http://arxiv.org/abs/1412.6980v8

        Default parameters follow those provided in the original paper.
    '''
    def __init__(self, lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-8, *args, **kwargs):
        super(Adam, self).__init__(**kwargs)
        self.__dict__.update(locals())
        self.iterations = shared_scalar(0)
        self.lr = shared_scalar(lr)

    def get_updates(self, params, constraints, loss):
        grads = self.get_gradients(loss, params)
        self.updates = [(self.iterations, self.iterations+1.)]

        t = self.iterations + 1
        lr_t = self.lr * T.sqrt(1-self.beta_2**t)/(1-self.beta_1**t)

        for p, g, c in zip(params, grads, constraints):
            m = theano.shared(p.get_value() * 0.)  # zero init of moment
            v = theano.shared(p.get_value() * 0.)  # zero init of velocity

            m_t = (self.beta_1 * m) + (1 - self.beta_1) * g
            v_t = (self.beta_2 * v) + (1 - self.beta_2) * (g**2)
            p_t = p - lr_t * m_t / (T.sqrt(v_t) + self.epsilon)

            self.updates.append((m, m_t))
            self.updates.append((v, v_t))
            self.updates.append((p, c(p_t)))  # apply constraints
        return self.updates

    def get_config(self):
        return {"name": self.__class__.__name__,
                "lr": float(self.lr.get_value()),
                "beta_1": self.beta_1,
                "beta_2": self.beta_2,
                "epsilon": self.epsilon}

# aliases
sgd = SGD
rmsprop = RMSprop
adagrad = Adagrad
adadelta = Adadelta
adam = Adam


def get(identifier, kwargs=None):
    return get_from_module(identifier, globals(), 'optimizer', instantiate=True,
                           kwargs=kwargs)

from __future__ import absolute_import
import theano
import theano.tensor as T
import numpy as np
from six.moves import range

if theano.config.floatX == 'float64':
    epsilon = 1.0e-9
else:
    epsilon = 1.0e-7


def mean_squared_error(y_true, y_pred):
    return T.sqr(y_pred - y_true).mean(axis=-1)
    
def root_mean_squared_error(y_true, y_pred):
    return T.sqrt(T.sqr(y_pred - y_true).mean(axis=-1))

def mean_absolute_error(y_true, y_pred):
    return T.abs_(y_pred - y_true).mean(axis=-1)


def mean_absolute_percentage_error(y_true, y_pred):
    return T.abs_((y_true - y_pred) / T.clip(T.abs_(y_true), epsilon, np.inf)).mean(axis=-1) * 100.


def mean_squared_logarithmic_error(y_true, y_pred):
    return T.sqr(T.log(T.clip(y_pred, epsilon, np.inf) + 1.) - T.log(T.clip(y_true, epsilon, np.inf) + 1.)).mean(axis=-1)


def squared_hinge(y_true, y_pred):
    return T.sqr(T.maximum(1. - y_true * y_pred, 0.)).mean(axis=-1)


def hinge(y_true, y_pred):
    return T.maximum(1. - y_true * y_pred, 0.).mean(axis=-1)


def categorical_crossentropy(y_true, y_pred):
    '''Expects a binary class matrix instead of a vector of scalar classes
    '''
    y_pred = T.clip(y_pred, epsilon, 1.0 - epsilon)
    # scale preds so that the class probas of each sample sum to 1
    y_pred /= y_pred.sum(axis=-1, keepdims=True)
    cce = T.nnet.categorical_crossentropy(y_pred, y_true)
    return cce


def binary_crossentropy(y_true, y_pred):
    y_pred = T.clip(y_pred, epsilon, 1.0 - epsilon)
    bce = T.nnet.binary_crossentropy(y_pred, y_true).mean(axis=-1)
    return bce


def poisson_loss(y_true, y_pred):
    return T.mean(y_pred - y_true * T.log(y_pred + epsilon), axis=-1)

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
import time, json, warnings

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

        # skip progbar update for the last batch; will be handled by on_epoch_end
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
    def __init__(self, filepath, monitor='val_loss', verbose=0, save_best_only=False, mode='auto'):

        super(Callback, self).__init__()
        self.monitor = monitor
        self.verbose = verbose
        self.filepath = filepath
        self.save_best_only = save_best_only
        
        if mode not in ['auto', 'min', 'max']:
            warnings.warn("ModelCheckpoint mode %s is unknown, fallback to auto mode" % (self.mode), RuntimeWarning)
            mode = 'auto'
            
        if mode == "min":
            self.monitor_op = np.less
            self.best = np.Inf
        elif mode == "max":
            self.monitor_op = np.greater
            self.best = -np.Inf
        else:
            if "acc" in self.monitor:
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
                warnings.warn("Can save best model only with %s available, skipping." % (self.monitor), RuntimeWarning)
            else:
                if self.monitor_op(current, self.best):
                    if self.verbose > 0:
                        print("Epoch %05d: %s improved from %0.5f to %0.5f, saving model to %s"
                              % (epoch, self.monitor, self.best, current, filepath))
                    self.best = current
                    self.model.save_weights(filepath, overwrite=True)
                else:
                    if self.verbose > 0:
                        print("Epoch %05d: %s did not improve" % (epoch, self.monitor))
        else:
            if self.verbose > 0:
                print("Epoch %05d: saving model to %s" % (epoch, filepath))
            self.model.save_weights(filepath, overwrite=True)


class EarlyStopping(Callback):
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
            warnings.warn("Early stopping requires %s available!" % (self.monitor), RuntimeWarning)

        if current < self.best:
            self.best = current
            self.wait = 0
        else:
            if self.wait >= self.patience:
                if self.verbose > 0:
                    print("Epoch %05d: early stopping" % (epoch))
                self.model.stop_training = True
            self.wait += 1


class RemoteMonitor(Callback):
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
            r = requests.post(self.root + '/publish/epoch/end/', {'data': json.dumps(send)})
        except:
            print('Warning: could not reach RemoteMonitor root server at ' + str(self.root))


class LearningRateScheduler(Callback):
    '''LearningRateScheduler
    schedule is a function that gets an epoch number as input and returns a new
    learning rate as output.
    '''
    def __init__(self, schedule):
        super(LearningRateScheduler, self).__init__()
        self.schedule = schedule

    def on_epoch_begin(self, epoch, logs={}):
        self.model.optimizer.lr.set_value(self.schedule(epoch))

from __future__ import absolute_import
import theano
import theano.tensor as T
import numpy as np


class Constraint(object):
    def __call__(self, p):
        return p

    def get_config(self):
        return {"name": self.__class__.__name__}


class MaxNorm(Constraint):
    def __init__(self, m=2):
        self.m = m

    def __call__(self, p):
        norms = T.sqrt(T.sum(T.sqr(p), axis=0))
        desired = T.clip(norms, 0, self.m)
        p = p * (desired / (1e-7 + norms))
        return p

    def get_config(self):
        return {"name": self.__class__.__name__,
                "m": self.m}


class NonNeg(Constraint):
    def __call__(self, p):
        p = theano.shared(p)
        p *= T.ge(p, 0.)
        return p


class UnitNorm(Constraint):
    def __call__(self, p):
        return p / T.sqrt(T.sum(p**2, axis=-1, keepdims=True))

identity = Constraint
maxnorm = MaxNorm
nonneg = NonNeg
unitnorm = UnitNorm

from .utils.generic_utils import get_from_module
def get(identifier, kwargs=None):
    return get_from_module(identifier, globals(), 'constraint', instantiate=True, kwargs=kwargs)

from __future__ import absolute_import
import theano
import theano.tensor as T
import numpy as np

from .utils.theano_utils import sharedX, shared_zeros, shared_ones


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
    return sharedX(scale * q[:shape[0], :shape[1]])


def identity(shape, scale=1):
    if len(shape) != 2 or shape[0] != shape[1]:
        raise Exception("Identity matrix initialization can only be used for 2D square matrices")
    else:
        return sharedX(scale * np.identity(shape[0]))


def zero(shape):
    return shared_zeros(shape)


def one(shape):
    return shared_ones(shape)


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

import theano
import theano.tensor as T
from theano.tensor.signal import downsample

from .. import activations, initializations, regularizers, constraints
from ..utils.theano_utils import shared_zeros, on_gpu
from ..layers.core import Layer

if on_gpu():
    from theano.sandbox.cuda import dnn


def conv_output_length(input_length, filter_size, border_mode, stride):
    if input_length is None:
        return None
    assert border_mode in {'same', 'full', 'valid'}
    if border_mode == 'same':
        output_length = input_length
    elif border_mode == 'full':
        output_length = input_length + filter_size - 1
    elif border_mode == 'valid':
        output_length = input_length - filter_size + 1
    return (output_length + stride - 1) // stride


def pool_output_length(input_length, pool_size, ignore_border, stride):
    if input_length is None:
        return None
    if ignore_border:
        output_length = input_length - pool_size + 1
        output_length = (output_length + stride - 1) // stride
    else:
        if pool_size == input_length:
            output_length = min(input_length, stride - stride % 2)
            if output_length <= 0:
                output_length = 1
        elif stride >= pool_size:
            output_length = (input_length + stride - 1) // stride
        else:
            output_length = (input_length - pool_size + stride - 1) // stride
            if output_length <= 0:
                output_length = 1
            else:
                output_length += 1
    return output_length


class Convolution1D(Layer):
    input_ndim = 3

    def __init__(self, nb_filter, filter_length,
                 init='uniform', activation='linear', weights=None,
                 border_mode='valid', subsample_length=1,
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None, input_dim=None, input_length=None, **kwargs):

        if border_mode not in {'valid', 'full', 'same'}:
            raise Exception('Invalid border mode for Convolution1D:', border_mode)
        self.nb_filter = nb_filter
        self.filter_length = filter_length
        self.init = initializations.get(init)
        self.activation = activations.get(activation)
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
        super(Convolution1D, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[2]
        self.input = T.tensor3()
        self.W_shape = (self.nb_filter, input_dim, self.filter_length, 1)
        self.W = self.init(self.W_shape)
        self.b = shared_zeros((self.nb_filter,))
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
        length = conv_output_length(self.input_shape[1], self.filter_length, self.border_mode, self.subsample[0])
        return (self.input_shape[0], length, self.nb_filter)

    def get_output(self, train=False):
        X = self.get_input(train)
        X = T.reshape(X, (X.shape[0], X.shape[1], X.shape[2], 1)).dimshuffle(0, 2, 1, 3)

        border_mode = self.border_mode
        if on_gpu() and dnn.dnn_available():
            if border_mode == 'same':
                assert(self.subsample_length == 1)
                pad_x = (self.filter_length - self.subsample_length) // 2
                conv_out = dnn.dnn_conv(img=X,
                                        kerns=self.W,
                                        border_mode=(pad_x, 0))
            else:
                conv_out = dnn.dnn_conv(img=X,
                                        kerns=self.W,
                                        border_mode=border_mode,
                                        subsample=self.subsample)
        else:
            if border_mode == 'same':
                assert(self.subsample_length == 1)
                border_mode = 'full'

            input_shape = self.input_shape
            image_shape = (input_shape[0], input_shape[2], input_shape[1], 1)
            conv_out = T.nnet.conv.conv2d(X, self.W,
                                          border_mode=border_mode,
                                          subsample=self.subsample,
                                          image_shape=image_shape,
                                          filter_shape=self.W_shape)
            if self.border_mode == 'same':
                shift_x = (self.filter_length - 1) // 2
                conv_out = conv_out[:, :, shift_x:X.shape[2] + shift_x, :]

        output = self.activation(conv_out + self.b.dimshuffle('x', 0, 'x', 'x'))
        output = T.reshape(output, (output.shape[0], output.shape[1], output.shape[2])).dimshuffle(0, 2, 1)
        return output

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "nb_filter": self.nb_filter,
                  "filter_length": self.filter_length,
                  "init": self.init.__name__,
                  "activation": self.activation.__name__,
                  "border_mode": self.border_mode,
                  "subsample_length": self.subsample_length,
                  "W_regularizer": self.W_regularizer.get_config() if self.W_regularizer else None,
                  "b_regularizer": self.b_regularizer.get_config() if self.b_regularizer else None,
                  "activity_regularizer": self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  "W_constraint": self.W_constraint.get_config() if self.W_constraint else None,
                  "b_constraint": self.b_constraint.get_config() if self.b_constraint else None,
                  "input_dim": self.input_dim,
                  "input_length": self.input_length}
        base_config = super(Convolution1D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Convolution2D(Layer):
    input_ndim = 4

    def __init__(self, nb_filter, nb_row, nb_col,
                 init='glorot_uniform', activation='linear', weights=None,
                 border_mode='valid', subsample=(1, 1),
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None, **kwargs):

        if border_mode not in {'valid', 'full', 'same'}:
            raise Exception('Invalid border mode for Convolution2D:', border_mode)
        self.nb_filter = nb_filter
        self.nb_row = nb_row
        self.nb_col = nb_col
        self.init = initializations.get(init)
        self.activation = activations.get(activation)
        self.border_mode = border_mode
        self.subsample = tuple(subsample)

        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.activity_regularizer = regularizers.get(activity_regularizer)

        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)
        self.constraints = [self.W_constraint, self.b_constraint]

        self.initial_weights = weights
        super(Convolution2D, self).__init__(**kwargs)

    def build(self):
        stack_size = self.input_shape[1]
        self.input = T.tensor4()
        self.W_shape = (self.nb_filter, stack_size, self.nb_row, self.nb_col)
        self.W = self.init(self.W_shape)
        self.b = shared_zeros((self.nb_filter,))
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
        rows = input_shape[2]
        cols = input_shape[3]
        rows = conv_output_length(rows, self.nb_row, self.border_mode, self.subsample[0])
        cols = conv_output_length(cols, self.nb_col, self.border_mode, self.subsample[1])
        return (input_shape[0], self.nb_filter, rows, cols)

    def get_output(self, train=False):
        X = self.get_input(train)
        border_mode = self.border_mode
        if on_gpu() and dnn.dnn_available():
            if border_mode == 'same':
                assert(self.subsample == (1, 1))
                pad_x = (self.nb_row - self.subsample[0]) // 2
                pad_y = (self.nb_col - self.subsample[1]) // 2
                conv_out = dnn.dnn_conv(img=X,
                                        kerns=self.W,
                                        border_mode=(pad_x, pad_y))
            else:
                conv_out = dnn.dnn_conv(img=X,
                                        kerns=self.W,
                                        border_mode=border_mode,
                                        subsample=self.subsample)
        else:
            if border_mode == 'same':
                border_mode = 'full'
                assert(self.subsample == (1, 1))

            conv_out = T.nnet.conv.conv2d(X, self.W,
                                          border_mode=border_mode,
                                          subsample=self.subsample,
                                          image_shape=self.input_shape,
                                          filter_shape=self.W_shape)
            if self.border_mode == 'same':
                shift_x = (self.nb_row - 1) // 2
                shift_y = (self.nb_col - 1) // 2
                conv_out = conv_out[:, :, shift_x:X.shape[2] + shift_x, shift_y:X.shape[3] + shift_y]

        return self.activation(conv_out + self.b.dimshuffle('x', 0, 'x', 'x'))

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "nb_filter": self.nb_filter,
                  "nb_row": self.nb_row,
                  "nb_col": self.nb_col,
                  "init": self.init.__name__,
                  "activation": self.activation.__name__,
                  "border_mode": self.border_mode,
                  "subsample": self.subsample,
                  "W_regularizer": self.W_regularizer.get_config() if self.W_regularizer else None,
                  "b_regularizer": self.b_regularizer.get_config() if self.b_regularizer else None,
                  "activity_regularizer": self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  "W_constraint": self.W_constraint.get_config() if self.W_constraint else None,
                  "b_constraint": self.b_constraint.get_config() if self.b_constraint else None}
        base_config = super(Convolution2D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class MaxPooling1D(Layer):
    input_ndim = 3

    def __init__(self, pool_length=2, stride=None, ignore_border=True, **kwargs):
        super(MaxPooling1D, self).__init__(**kwargs)
        if stride is None:
            stride = pool_length
        self.pool_length = pool_length
        self.stride = stride
        self.st = (self.stride, 1)

        self.input = T.tensor3()
        self.pool_size = (pool_length, 1)
        self.ignore_border = ignore_border

    @property
    def output_shape(self):
        input_shape = self.input_shape
        length = pool_output_length(input_shape[1], self.pool_length, self.ignore_border, self.stride)
        return (input_shape[0], length, input_shape[2])

    def get_output(self, train=False):
        X = self.get_input(train)
        X = T.reshape(X, (X.shape[0], X.shape[1], X.shape[2], 1)).dimshuffle(0, 2, 1, 3)
        output = downsample.max_pool_2d(X, ds=self.pool_size, st=self.st, ignore_border=self.ignore_border)
        output = output.dimshuffle(0, 2, 1, 3)
        return T.reshape(output, (output.shape[0], output.shape[1], output.shape[2]))

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "stride": self.stride,
                  "pool_length": self.pool_length,
                  "ignore_border": self.ignore_border}
        base_config = super(MaxPooling1D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class MaxPooling2D(Layer):
    input_ndim = 4

    def __init__(self, pool_size=(2, 2), stride=None, ignore_border=True, **kwargs):
        super(MaxPooling2D, self).__init__(**kwargs)
        self.input = T.tensor4()
        self.pool_size = tuple(pool_size)
        if stride is None:
            stride = self.pool_size
        self.stride = tuple(stride)
        self.ignore_border = ignore_border

    @property
    def output_shape(self):
        input_shape = self.input_shape
        rows = pool_output_length(input_shape[2], self.pool_size[0], self.ignore_border, self.stride[0])
        cols = pool_output_length(input_shape[3], self.pool_size[1], self.ignore_border, self.stride[1])
        return (input_shape[0], input_shape[1], rows, cols)

    def get_output(self, train=False):
        X = self.get_input(train)
        output = downsample.max_pool_2d(X, ds=self.pool_size, st=self.stride, ignore_border=self.ignore_border)
        return output

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "pool_size": self.pool_size,
                  "ignore_border": self.ignore_border,
                  "stride": self.stride}
        base_config = super(MaxPooling2D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class UpSample1D(Layer):
    input_ndim = 3

    def __init__(self, length=2, **kwargs):
        super(UpSample1D, self).__init__(**kwargs)
        self.length = length
        self.input = T.tensor3()

    @property
    def output_shape(self):
        input_shape = self.input_shape
        return (input_shape[0], self.length * input_shape[1], input_shape[2])

    def get_output(self, train=False):
        X = self.get_input(train)
        output = theano.tensor.extra_ops.repeat(X, self.length, axis=1)
        return output

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "length": self.length}
        base_config = super(UpSample1D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class UpSample2D(Layer):
    input_ndim = 4

    def __init__(self, size=(2, 2), **kwargs):
        super(UpSample2D, self).__init__(**kwargs)
        self.input = T.tensor4()
        self.size = tuple(size)

    @property
    def output_shape(self):
        input_shape = self.input_shape
        return (input_shape[0], input_shape[1], self.size[0] * input_shape[2], self.size[1] * input_shape[3])

    def get_output(self, train=False):
        X = self.get_input(train)
        Y = theano.tensor.extra_ops.repeat(X, self.size[0], axis=2)
        output = theano.tensor.extra_ops.repeat(Y, self.size[1], axis=3)
        return output

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "size": self.size}
        base_config = super(UpSample2D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ZeroPadding1D(Layer):
    """Zero-padding layer for 1D input (e.g. temporal sequence).

    Input shape
    -----------
    3D tensor with shape (samples, axis_to_pad, features)

    Output shape
    ------------
    3D tensor with shape (samples, padded_axis, features)

    Arguments
    ---------
    padding: int
        How many zeros to add at the beginning and end of
        the padding dimension (axis 1).
    """
    input_ndim = 3

    def __init__(self, padding=1, **kwargs):
        super(ZeroPadding1D, self).__init__(**kwargs)
        self.padding = padding
        self.input = T.tensor3()

    @property
    def output_shape(self):
        input_shape = self.input_shape
        return (input_shape[0], input_shape[1] + self.padding * 2, input_shape[2])

    def get_output(self, train=False):
        X = self.get_input(train)
        input_shape = X.shape
        output_shape = (input_shape[0],
                        input_shape[1] + 2 * self.padding,
                        input_shape[2])
        output = T.zeros(output_shape)
        return T.set_subtensor(output[:, self.padding:X.shape[1] + self.padding, :], X)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "padding": self.padding}
        base_config = super(ZeroPadding1D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ZeroPadding2D(Layer):
    """Zero-padding layer for 1D input (e.g. temporal sequence).

    Input shape
    -----------
    4D tensor with shape (samples, depth, first_axis_to_pad, second_axis_to_pad)

    Output shape
    ------------
    4D tensor with shape (samples, depth, first_padded_axis, second_padded_axis)

    Arguments
    ---------
    padding: tuple of int (length 2)
        How many zeros to add at the beginning and end of
        the 2 padding dimensions (axis 3 and 4).
    """
    input_ndim = 4

    def __init__(self, padding=(1, 1), **kwargs):
        super(ZeroPadding2D, self).__init__(**kwargs)
        self.padding = tuple(padding)
        self.input = T.tensor4()

    @property
    def output_shape(self):
        input_shape = self.input_shape
        return (input_shape[0],
                input_shape[1],
                input_shape[2] + 2 * self.padding[0],
                input_shape[3] + 2 * self.padding[1])

    def get_output(self, train=False):
        X = self.get_input(train)
        input_shape = X.shape
        output_shape = (input_shape[0],
                        input_shape[1],
                        input_shape[2] + 2 * self.padding[0],
                        input_shape[3] + 2 * self.padding[1])
        output = T.zeros(output_shape)
        indices = (slice(None),
                   slice(None),
                   slice(self.padding[0], input_shape[2] + self.padding[0]),
                   slice(self.padding[1], input_shape[3] + self.padding[1]))
        return T.set_subtensor(output[indices], X)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "padding": self.padding}
        base_config = super(ZeroPadding2D, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

# -*- coding: utf-8 -*-
from __future__ import absolute_import
import theano
import theano.tensor as T
import numpy as np

from .. import activations, initializations
from ..utils.theano_utils import shared_scalar, shared_zeros, alloc_zeros_matrix
from ..layers.core import Layer, MaskedLayer
from six.moves import range


class Recurrent(MaskedLayer):
    input_ndim = 3

    def get_output_mask(self, train=None):
        if self.return_sequences:
            return super(Recurrent, self).get_output_mask(train)
        else:
            return None

    def get_padded_shuffled_mask(self, train, X, pad=0):
        mask = self.get_input_mask(train)
        if mask is None:
            mask = T.ones_like(X.sum(axis=-1))  # is there a better way to do this without a sum?

        # mask is (nb_samples, time)
        mask = T.shape_padright(mask)  # (nb_samples, time, 1)
        mask = T.addbroadcast(mask, -1)  # the new dimension (the '1') is made broadcastable
        # see http://deeplearning.net/software/theano/library/tensor/basic.html#broadcasting-in-theano-vs-numpy
        mask = mask.dimshuffle(1, 0, 2)  # (time, nb_samples, 1)

        if pad > 0:
            # left-pad in time with 0
            padding = alloc_zeros_matrix(pad, mask.shape[1], 1)
            mask = T.concatenate([padding, mask], axis=0)
        return mask.astype('int8')

    @property
    def output_shape(self):
        input_shape = self.input_shape
        if self.return_sequences:
            return (input_shape[0], input_shape[1], self.output_dim)
        else:
            return (input_shape[0], self.output_dim)


class SimpleRNN(Recurrent):
    '''
        Fully connected RNN where output is to fed back to input.

        Not a particularly useful model,
        included for demonstration purposes
        (demonstrates how to use theano.scan to build a basic RNN).
    '''
    def __init__(self, output_dim,
                 init='glorot_uniform', inner_init='orthogonal', activation='sigmoid', weights=None,
                 truncate_gradient=-1, return_sequences=False, input_dim=None, input_length=None, **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.truncate_gradient = truncate_gradient
        self.activation = activations.get(activation)
        self.return_sequences = return_sequences
        self.initial_weights = weights

        self.input_dim = input_dim
        self.input_length = input_length
        if self.input_dim:
            kwargs['input_shape'] = (self.input_length, self.input_dim)
        super(SimpleRNN, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[2]
        self.input = T.tensor3()

        self.W = self.init((input_dim, self.output_dim))
        self.U = self.inner_init((self.output_dim, self.output_dim))
        self.b = shared_zeros((self.output_dim))
        self.params = [self.W, self.U, self.b]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def _step(self, x_t, mask_tm1, h_tm1, u):
        '''
            Variable names follow the conventions from:
            http://deeplearning.net/software/theano/library/scan.html

        '''
        return self.activation(x_t + mask_tm1 * T.dot(h_tm1, u))

    def get_output(self, train=False):
        X = self.get_input(train)  # shape: (nb_samples, time (padded with zeros), input_dim)
        # new shape: (time, nb_samples, input_dim) -> because theano.scan iterates over main dimension
        padded_mask = self.get_padded_shuffled_mask(train, X, pad=1)
        X = X.dimshuffle((1, 0, 2))
        x = T.dot(X, self.W) + self.b

        # scan = theano symbolic loop.
        # See: http://deeplearning.net/software/theano/library/scan.html
        # Iterate over the first dimension of the x array (=time).
        outputs, updates = theano.scan(
            self._step,  # this will be called with arguments (sequences[i], outputs[i-1], non_sequences[i])
            sequences=[x, dict(input=padded_mask, taps=[-1])],  # tensors to iterate over, inputs to _step
            # initialization of the output. Input to _step with default tap=-1.
            outputs_info=T.unbroadcast(alloc_zeros_matrix(X.shape[1], self.output_dim), 1),
            non_sequences=self.U,  # static inputs to _step
            truncate_gradient=self.truncate_gradient)

        if self.return_sequences:
            return outputs.dimshuffle((1, 0, 2))
        return outputs[-1]

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "output_dim": self.output_dim,
                  "init": self.init.__name__,
                  "inner_init": self.inner_init.__name__,
                  "activation": self.activation.__name__,
                  "truncate_gradient": self.truncate_gradient,
                  "return_sequences": self.return_sequences,
                  "input_dim": self.input_dim,
                  "input_length": self.input_length}
        base_config = super(SimpleRNN, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class SimpleDeepRNN(Recurrent):
    '''
        Fully connected RNN where the output of multiple timesteps
        (up to "depth" steps in the past) is fed back to the input:

        output = activation( W.x_t + b + inner_activation(U_1.h_tm1) + inner_activation(U_2.h_tm2) + ... )

        This demonstrates how to build RNNs with arbitrary lookback.
        Also (probably) not a super useful model.
    '''
    def __init__(self, output_dim, depth=3,
                 init='glorot_uniform', inner_init='orthogonal',
                 activation='sigmoid', inner_activation='hard_sigmoid',
                 weights=None, truncate_gradient=-1, return_sequences=False,
                 input_dim=None, input_length=None, **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.truncate_gradient = truncate_gradient
        self.activation = activations.get(activation)
        self.inner_activation = activations.get(inner_activation)
        self.depth = depth
        self.return_sequences = return_sequences
        self.initial_weights = weights

        self.input_dim = input_dim
        self.input_length = input_length
        if self.input_dim:
            kwargs['input_shape'] = (self.input_length, self.input_dim)
        super(SimpleDeepRNN, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[2]
        self.input = T.tensor3()
        self.W = self.init((input_dim, self.output_dim))
        self.Us = [self.inner_init((self.output_dim, self.output_dim)) for _ in range(self.depth)]
        self.b = shared_zeros((self.output_dim))
        self.params = [self.W] + self.Us + [self.b]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def _step(self, x_t, *args):
        o = x_t
        for i in range(self.depth):
            mask_tmi = args[i]
            h_tmi = args[i + self.depth]
            U_tmi = args[i + 2*self.depth]
            o += mask_tmi*self.inner_activation(T.dot(h_tmi, U_tmi))
        return self.activation(o)

    def get_output(self, train=False):
        X = self.get_input(train)
        padded_mask = self.get_padded_shuffled_mask(train, X, pad=self.depth)
        X = X.dimshuffle((1, 0, 2))

        x = T.dot(X, self.W) + self.b

        if self.depth == 1:
            initial = T.unbroadcast(alloc_zeros_matrix(X.shape[1], self.output_dim), 1)
        else:
            initial = T.unbroadcast(T.unbroadcast(alloc_zeros_matrix(self.depth, X.shape[1], self.output_dim), 0), 2)

        outputs, updates = theano.scan(
            self._step,
            sequences=[x, dict(
                input=padded_mask,
                taps=[(-i) for i in range(self.depth)]
            )],
            outputs_info=[dict(
                initial=initial,
                taps=[(-i-1) for i in range(self.depth)]
            )],
            non_sequences=self.Us,
            truncate_gradient=self.truncate_gradient
        )

        if self.return_sequences:
            return outputs.dimshuffle((1, 0, 2))
        return outputs[-1]

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "output_dim": self.output_dim,
                  "depth": self.depth,
                  "init": self.init.__name__,
                  "inner_init": self.inner_init.__name__,
                  "activation": self.activation.__name__,
                  "inner_activation": self.inner_activation.__name__,
                  "truncate_gradient": self.truncate_gradient,
                  "return_sequences": self.return_sequences,
                  "input_dim": self.input_dim,
                  "input_length": self.input_length}
        base_config = super(SimpleDeepRNN, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class GRU(Recurrent):
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
    def __init__(self, output_dim,
                 init='glorot_uniform', inner_init='orthogonal',
                 activation='sigmoid', inner_activation='hard_sigmoid',
                 weights=None, truncate_gradient=-1, return_sequences=False,
                 input_dim=None, input_length=None, **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.activation = activations.get(activation)
        self.inner_activation = activations.get(inner_activation)
        self.truncate_gradient = truncate_gradient
        self.return_sequences = return_sequences
        self.initial_weights = weights

        self.input_dim = input_dim
        self.input_length = input_length
        if self.input_dim:
            kwargs['input_shape'] = (self.input_length, self.input_dim)
        super(GRU, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[2]
        self.input = T.tensor3()

        self.W_z = self.init((input_dim, self.output_dim))
        self.U_z = self.inner_init((self.output_dim, self.output_dim))
        self.b_z = shared_zeros((self.output_dim))

        self.W_r = self.init((input_dim, self.output_dim))
        self.U_r = self.inner_init((self.output_dim, self.output_dim))
        self.b_r = shared_zeros((self.output_dim))

        self.W_h = self.init((input_dim, self.output_dim))
        self.U_h = self.inner_init((self.output_dim, self.output_dim))
        self.b_h = shared_zeros((self.output_dim))

        self.params = [
            self.W_z, self.U_z, self.b_z,
            self.W_r, self.U_r, self.b_r,
            self.W_h, self.U_h, self.b_h,
        ]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def _step(self,
              xz_t, xr_t, xh_t, mask_tm1,
              h_tm1,
              u_z, u_r, u_h):
        h_mask_tm1 = mask_tm1 * h_tm1
        z = self.inner_activation(xz_t + T.dot(h_mask_tm1, u_z))
        r = self.inner_activation(xr_t + T.dot(h_mask_tm1, u_r))
        hh_t = self.activation(xh_t + T.dot(r * h_mask_tm1, u_h))
        h_t = z * h_mask_tm1 + (1 - z) * hh_t
        return h_t

    def get_output(self, train=False):
        X = self.get_input(train)
        padded_mask = self.get_padded_shuffled_mask(train, X, pad=1)
        X = X.dimshuffle((1, 0, 2))

        x_z = T.dot(X, self.W_z) + self.b_z
        x_r = T.dot(X, self.W_r) + self.b_r
        x_h = T.dot(X, self.W_h) + self.b_h
        outputs, updates = theano.scan(
            self._step,
            sequences=[x_z, x_r, x_h, padded_mask],
            outputs_info=T.unbroadcast(alloc_zeros_matrix(X.shape[1], self.output_dim), 1),
            non_sequences=[self.U_z, self.U_r, self.U_h],
            truncate_gradient=self.truncate_gradient)

        if self.return_sequences:
            return outputs.dimshuffle((1, 0, 2))
        return outputs[-1]

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "output_dim": self.output_dim,
                  "init": self.init.__name__,
                  "inner_init": self.inner_init.__name__,
                  "activation": self.activation.__name__,
                  "inner_activation": self.inner_activation.__name__,
                  "truncate_gradient": self.truncate_gradient,
                  "return_sequences": self.return_sequences,
                  "input_dim": self.input_dim,
                  "input_length": self.input_length}
        base_config = super(GRU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class LSTM(Recurrent):
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
    def __init__(self, output_dim,
                 init='glorot_uniform', inner_init='orthogonal', forget_bias_init='one',
                 activation='tanh', inner_activation='hard_sigmoid',
                 weights=None, truncate_gradient=-1, return_sequences=False,
                 input_dim=None, input_length=None, **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.forget_bias_init = initializations.get(forget_bias_init)
        self.activation = activations.get(activation)
        self.inner_activation = activations.get(inner_activation)
        self.truncate_gradient = truncate_gradient
        self.return_sequences = return_sequences
        self.initial_weights = weights

        self.input_dim = input_dim
        self.input_length = input_length
        if self.input_dim:
            kwargs['input_shape'] = (self.input_length, self.input_dim)
        super(LSTM, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[2]
        self.input = T.tensor3()

        self.W_i = self.init((input_dim, self.output_dim))
        self.U_i = self.inner_init((self.output_dim, self.output_dim))
        self.b_i = shared_zeros((self.output_dim))

        self.W_f = self.init((input_dim, self.output_dim))
        self.U_f = self.inner_init((self.output_dim, self.output_dim))
        self.b_f = self.forget_bias_init((self.output_dim))

        self.W_c = self.init((input_dim, self.output_dim))
        self.U_c = self.inner_init((self.output_dim, self.output_dim))
        self.b_c = shared_zeros((self.output_dim))

        self.W_o = self.init((input_dim, self.output_dim))
        self.U_o = self.inner_init((self.output_dim, self.output_dim))
        self.b_o = shared_zeros((self.output_dim))

        self.params = [
            self.W_i, self.U_i, self.b_i,
            self.W_c, self.U_c, self.b_c,
            self.W_f, self.U_f, self.b_f,
            self.W_o, self.U_o, self.b_o,
        ]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def _step(self,
              xi_t, xf_t, xo_t, xc_t, mask_tm1,
              h_tm1, c_tm1,
              u_i, u_f, u_o, u_c):
        h_mask_tm1 = mask_tm1 * h_tm1
        c_mask_tm1 = mask_tm1 * c_tm1

        i_t = self.inner_activation(xi_t + T.dot(h_mask_tm1, u_i))
        f_t = self.inner_activation(xf_t + T.dot(h_mask_tm1, u_f))
        c_t = f_t * c_mask_tm1 + i_t * self.activation(xc_t + T.dot(h_mask_tm1, u_c))
        o_t = self.inner_activation(xo_t + T.dot(h_mask_tm1, u_o))
        h_t = o_t * self.activation(c_t)
        return h_t, c_t

    def get_output(self, train=False):
        X = self.get_input(train)
        padded_mask = self.get_padded_shuffled_mask(train, X, pad=1)
        X = X.dimshuffle((1, 0, 2))

        xi = T.dot(X, self.W_i) + self.b_i
        xf = T.dot(X, self.W_f) + self.b_f
        xc = T.dot(X, self.W_c) + self.b_c
        xo = T.dot(X, self.W_o) + self.b_o

        [outputs, memories], updates = theano.scan(
            self._step,
            sequences=[xi, xf, xo, xc, padded_mask],
            outputs_info=[
                T.unbroadcast(alloc_zeros_matrix(X.shape[1], self.output_dim), 1),
                T.unbroadcast(alloc_zeros_matrix(X.shape[1], self.output_dim), 1)
            ],
            non_sequences=[self.U_i, self.U_f, self.U_o, self.U_c],
            truncate_gradient=self.truncate_gradient)

        if self.return_sequences:
            return outputs.dimshuffle((1, 0, 2))
        return outputs[-1]

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "output_dim": self.output_dim,
                  "init": self.init.__name__,
                  "inner_init": self.inner_init.__name__,
                  "forget_bias_init": self.forget_bias_init.__name__,
                  "activation": self.activation.__name__,
                  "inner_activation": self.inner_activation.__name__,
                  "truncate_gradient": self.truncate_gradient,
                  "return_sequences": self.return_sequences,
                  "input_dim": self.input_dim,
                  "input_length": self.input_length}
        base_config = super(LSTM, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class JZS1(Recurrent):
    '''
        Evolved recurrent neural network architectures from the evaluation of thousands
        of models, serving as alternatives to LSTMs and GRUs. See Jozefowicz et al. 2015.

        This corresponds to the `MUT1` architecture described in the paper.

        Takes inputs with shape:
        (nb_samples, max_sample_length (samples shorter than this are padded with zeros at the end), input_dim)

        and returns outputs with shape:
        if not return_sequences:
            (nb_samples, output_dim)
        if return_sequences:
            (nb_samples, max_sample_length, output_dim)

        References:
            An Empirical Exploration of Recurrent Network Architectures
                http://www.jmlr.org/proceedings/papers/v37/jozefowicz15.pdf
    '''
    def __init__(self, output_dim,
                 init='glorot_uniform', inner_init='orthogonal',
                 activation='tanh', inner_activation='sigmoid',
                 weights=None, truncate_gradient=-1, return_sequences=False,
                 input_dim=None, input_length=None, **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.activation = activations.get(activation)
        self.inner_activation = activations.get(inner_activation)
        self.truncate_gradient = truncate_gradient
        self.return_sequences = return_sequences
        self.initial_weights = weights

        self.input_dim = input_dim
        self.input_length = input_length
        if self.input_dim:
            kwargs['input_shape'] = (self.input_length, self.input_dim)
        super(JZS1, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[2]
        self.input = T.tensor3()

        self.W_z = self.init((input_dim, self.output_dim))
        self.b_z = shared_zeros((self.output_dim))

        self.W_r = self.init((input_dim, self.output_dim))
        self.U_r = self.inner_init((self.output_dim, self.output_dim))
        self.b_r = shared_zeros((self.output_dim))

        self.U_h = self.inner_init((self.output_dim, self.output_dim))
        self.b_h = shared_zeros((self.output_dim))

        # P_h used to project X onto different dimension, using sparse random projections
        if input_dim == self.output_dim:
            self.Pmat = theano.shared(np.identity(self.output_dim, dtype=theano.config.floatX), name=None)
        else:
            P = np.random.binomial(1, 0.5, size=(input_dim, self.output_dim)).astype(theano.config.floatX) * 2 - 1
            P = 1 / np.sqrt(input_dim) * P
            self.Pmat = theano.shared(P, name=None)

        self.params = [
            self.W_z, self.b_z,
            self.W_r, self.U_r, self.b_r,
            self.U_h, self.b_h,
            self.Pmat
        ]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def _step(self,
              xz_t, xr_t, xh_t, mask_tm1,
              h_tm1,
              u_r, u_h):
        h_mask_tm1 = mask_tm1 * h_tm1
        z = self.inner_activation(xz_t)
        r = self.inner_activation(xr_t + T.dot(h_mask_tm1, u_r))
        hh_t = self.activation(xh_t + T.dot(r * h_mask_tm1, u_h))
        h_t = hh_t * z + h_mask_tm1 * (1 - z)
        return h_t

    def get_output(self, train=False):
        X = self.get_input(train)
        padded_mask = self.get_padded_shuffled_mask(train, X, pad=1)
        X = X.dimshuffle((1, 0, 2))

        x_z = T.dot(X, self.W_z) + self.b_z
        x_r = T.dot(X, self.W_r) + self.b_r
        x_h = T.tanh(T.dot(X, self.Pmat)) + self.b_h
        outputs, updates = theano.scan(
            self._step,
            sequences=[x_z, x_r, x_h, padded_mask],
            outputs_info=T.unbroadcast(alloc_zeros_matrix(X.shape[1], self.output_dim), 1),
            non_sequences=[self.U_r, self.U_h],
            truncate_gradient=self.truncate_gradient)
        if self.return_sequences:
            return outputs.dimshuffle((1, 0, 2))
        return outputs[-1]

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "output_dim": self.output_dim,
                  "init": self.init.__name__,
                  "inner_init": self.inner_init.__name__,
                  "activation": self.activation.__name__,
                  "inner_activation": self.inner_activation.__name__,
                  "truncate_gradient": self.truncate_gradient,
                  "return_sequences": self.return_sequences,
                  "input_dim": self.input_dim,
                  "input_length": self.input_length}
        base_config = super(JZS1, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class JZS2(Recurrent):
    '''
        Evolved recurrent neural network architectures from the evaluation of thousands
        of models, serving as alternatives to LSTMs and GRUs. See Jozefowicz et al. 2015.

        This corresponds to the `MUT2` architecture described in the paper.

        Takes inputs with shape:
        (nb_samples, max_sample_length (samples shorter than this are padded with zeros at the end), input_dim)

        and returns outputs with shape:
        if not return_sequences:
            (nb_samples, output_dim)
        if return_sequences:
            (nb_samples, max_sample_length, output_dim)

        References:
            An Empirical Exploration of Recurrent Network Architectures
                http://www.jmlr.org/proceedings/papers/v37/jozefowicz15.pdf
    '''
    def __init__(self, output_dim,
                 init='glorot_uniform', inner_init='orthogonal',
                 activation='tanh', inner_activation='sigmoid',
                 weights=None, truncate_gradient=-1, return_sequences=False,
                 input_dim=None, input_length=None, **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.activation = activations.get(activation)
        self.inner_activation = activations.get(inner_activation)
        self.truncate_gradient = truncate_gradient
        self.return_sequences = return_sequences
        self.initial_weights = weights

        self.input_dim = input_dim
        self.input_length = input_length
        if self.input_dim:
            kwargs['input_shape'] = (self.input_length, self.input_dim)
        super(JZS2, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[2]
        self.input = T.tensor3()

        self.W_z = self.init((input_dim, self.output_dim))
        self.U_z = self.inner_init((self.output_dim, self.output_dim))
        self.b_z = shared_zeros((self.output_dim))

        self.U_r = self.inner_init((self.output_dim, self.output_dim))
        self.b_r = shared_zeros((self.output_dim))

        self.W_h = self.init((input_dim, self.output_dim))
        self.U_h = self.inner_init((self.output_dim, self.output_dim))
        self.b_h = shared_zeros((self.output_dim))

        # P_h used to project X onto different dimension, using sparse random projections
        if input_dim == self.output_dim:
            self.Pmat = theano.shared(np.identity(self.output_dim, dtype=theano.config.floatX), name=None)
        else:
            P = np.random.binomial(1, 0.5, size=(input_dim, self.output_dim)).astype(theano.config.floatX) * 2 - 1
            P = 1 / np.sqrt(input_dim) * P
            self.Pmat = theano.shared(P, name=None)

        self.params = [
            self.W_z, self.U_z, self.b_z,
            self.U_r, self.b_r,
            self.W_h, self.U_h, self.b_h,
            self.Pmat
        ]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def _step(self,
              xz_t, xr_t, xh_t, mask_tm1,
              h_tm1,
              u_z, u_r, u_h):
        h_mask_tm1 = mask_tm1 * h_tm1
        z = self.inner_activation(xz_t + T.dot(h_mask_tm1, u_z))
        r = self.inner_activation(xr_t + T.dot(h_mask_tm1, u_r))
        hh_t = self.activation(xh_t + T.dot(r * h_mask_tm1, u_h))
        h_t = hh_t * z + h_mask_tm1 * (1 - z)
        return h_t

    def get_output(self, train=False):
        X = self.get_input(train)
        padded_mask = self.get_padded_shuffled_mask(train, X, pad=1)
        X = X.dimshuffle((1, 0, 2))

        x_z = T.dot(X, self.W_z) + self.b_z
        x_r = T.dot(X, self.Pmat) + self.b_r
        x_h = T.dot(X, self.W_h) + self.b_h
        outputs, updates = theano.scan(
            self._step,
            sequences=[x_z, x_r, x_h, padded_mask],
            outputs_info=T.unbroadcast(alloc_zeros_matrix(X.shape[1], self.output_dim), 1),
            non_sequences=[self.U_z, self.U_r, self.U_h],
            truncate_gradient=self.truncate_gradient)
        if self.return_sequences:
            return outputs.dimshuffle((1, 0, 2))
        return outputs[-1]

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "output_dim": self.output_dim,
                  "init": self.init.__name__,
                  "inner_init": self.inner_init.__name__,
                  "activation": self.activation.__name__,
                  "inner_activation": self.inner_activation.__name__,
                  "truncate_gradient": self.truncate_gradient,
                  "return_sequences": self.return_sequences,
                  "input_dim": self.input_dim,
                  "input_length": self.input_length}
        base_config = super(JZS2, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class JZS3(Recurrent):
    '''
        Evolved recurrent neural network architectures from the evaluation of thousands
        of models, serving as alternatives to LSTMs and GRUs. See Jozefowicz et al. 2015.

        This corresponds to the `MUT3` architecture described in the paper.

        Takes inputs with shape:
        (nb_samples, max_sample_length (samples shorter than this are padded with zeros at the end), input_dim)

        and returns outputs with shape:
        if not return_sequences:
            (nb_samples, output_dim)
        if return_sequences:
            (nb_samples, max_sample_length, output_dim)

        References:
            An Empirical Exploration of Recurrent Network Architectures
                http://www.jmlr.org/proceedings/papers/v37/jozefowicz15.pdf
    '''
    def __init__(self, output_dim,
                 init='glorot_uniform', inner_init='orthogonal',
                 activation='tanh', inner_activation='sigmoid',
                 weights=None, truncate_gradient=-1, return_sequences=False,
                 input_dim=None, input_length=None, **kwargs):
        self.output_dim = output_dim
        self.init = initializations.get(init)
        self.inner_init = initializations.get(inner_init)
        self.activation = activations.get(activation)
        self.inner_activation = activations.get(inner_activation)
        self.truncate_gradient = truncate_gradient
        self.return_sequences = return_sequences
        self.initial_weights = weights

        self.input_dim = input_dim
        self.input_length = input_length
        if self.input_dim:
            kwargs['input_shape'] = (self.input_length, self.input_dim)
        super(JZS3, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[2]
        self.input = T.tensor3()

        self.W_z = self.init((input_dim, self.output_dim))
        self.U_z = self.inner_init((self.output_dim, self.output_dim))
        self.b_z = shared_zeros((self.output_dim))

        self.W_r = self.init((input_dim, self.output_dim))
        self.U_r = self.inner_init((self.output_dim, self.output_dim))
        self.b_r = shared_zeros((self.output_dim))

        self.W_h = self.init((input_dim, self.output_dim))
        self.U_h = self.inner_init((self.output_dim, self.output_dim))
        self.b_h = shared_zeros((self.output_dim))

        self.params = [
            self.W_z, self.U_z, self.b_z,
            self.W_r, self.U_r, self.b_r,
            self.W_h, self.U_h, self.b_h,
        ]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def _step(self,
              xz_t, xr_t, xh_t, mask_tm1,
              h_tm1,
              u_z, u_r, u_h):
        h_mask_tm1 = mask_tm1 * h_tm1
        z = self.inner_activation(xz_t + T.dot(T.tanh(h_mask_tm1), u_z))
        r = self.inner_activation(xr_t + T.dot(h_mask_tm1, u_r))
        hh_t = self.activation(xh_t + T.dot(r * h_mask_tm1, u_h))
        h_t = hh_t * z + h_mask_tm1 * (1 - z)
        return h_t

    def get_output(self, train=False):
        X = self.get_input(train)
        padded_mask = self.get_padded_shuffled_mask(train, X, pad=1)
        X = X.dimshuffle((1, 0, 2))

        x_z = T.dot(X, self.W_z) + self.b_z
        x_r = T.dot(X, self.W_r) + self.b_r
        x_h = T.dot(X, self.W_h) + self.b_h
        outputs, updates = theano.scan(
            self._step,
            sequences=[x_z, x_r, x_h, padded_mask],
            outputs_info=T.unbroadcast(alloc_zeros_matrix(X.shape[1], self.output_dim), 1),
            non_sequences=[self.U_z, self.U_r, self.U_h],
            truncate_gradient=self.truncate_gradient
        )
        if self.return_sequences:
            return outputs.dimshuffle((1, 0, 2))
        return outputs[-1]

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "output_dim": self.output_dim,
                  "init": self.init.__name__,
                  "inner_init": self.inner_init.__name__,
                  "activation": self.activation.__name__,
                  "inner_activation": self.inner_activation.__name__,
                  "truncate_gradient": self.truncate_gradient,
                  "return_sequences": self.return_sequences,
                  "input_dim": self.input_dim,
                  "input_length": self.input_length}
        base_config = super(JZS3, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from collections import OrderedDict
import theano.tensor as T
from ..layers.core import Layer, Merge
from ..utils.theano_utils import ndim_tensor
from six.moves import range


class Sequential(Layer):
    '''
        Simple linear stack of layers.

        inherited from Layer:
        - get_params
        - get_output_mask
        - supports_masked_input
    '''

    def __init__(self, layers=[]):
        self.layers = []
        for layer in layers:
            self.add(layer)

    def set_previous(self, layer):
        self.layers[0].previous = layer

    def add(self, layer):
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
    def output_shape(self):
        return self.layers[-1].output_shape

    def get_output(self, train=False):
        return self.layers[-1].get_output(train)

    def set_input(self):
        for l in self.layers:
            if hasattr(l, 'input'):
                ndim = l.input.ndim
                self.layers[0].input = ndim_tensor(ndim)
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
        return {"name": self.__class__.__name__,
                "layers": [layer.get_config() for layer in self.layers]}

    def count_params(self):
        return sum([layer.count_params() for layer in self.layers])


class Graph(Layer):
    '''
        Implement a NN graph with arbitrary layer connections,
        arbitrary number of inputs and arbitrary number of outputs.

        Note: Graph can only be used as a layer
        (connect, input, get_input, get_output)
        when it has exactly one input and one output.

        inherited from Layer:
            - get_output_mask
            - supports_masked_input
            - get_weights
            - set_weights
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

    def set_previous(self, layer, connection_map={}):
        if self.nb_input != layer.nb_output:
            raise Exception('Cannot connect layers: input count does not match output count.')
        if self.nb_input == 1:
            self.inputs[self.input_order[0]].set_previous(layer)
        else:
            if not connection_map:
                raise Exception('Cannot attach multi-input layer: no connection_map provided.')
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

    def add_input(self, name, input_shape, dtype='float'):
        if name in self.namespace:
            raise Exception('Duplicate node identifier: ' + name)
        self.namespace.add(name)
        self.input_order.append(name)
        layer = Layer()  # empty layer
        layer.set_input_shape(input_shape)
        ndim = len(input_shape) + 1
        if dtype == 'float':
            layer.input = ndim_tensor(ndim)
        else:
            if ndim == 2:
                layer.input = T.imatrix()
            else:
                raise Exception('Type "int" can only be used with ndim==2 (Embedding).')
        layer.input.name = name
        self.inputs[name] = layer
        self.input_config.append({'name': name,
                                  'input_shape': input_shape,
                                  'dtype': dtype})

    def add_node(self, layer, name, input=None, inputs=[],
                 merge_mode='concat', concat_axis=-1, dot_axes=-1, create_output=False):
        if hasattr(layer, 'set_name'):
            layer.set_name(name)
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
            merge = Merge(to_merge, mode=merge_mode, concat_axis=concat_axis, dot_axes=dot_axes)
            layer.set_previous(merge)

        self.namespace.add(name)
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

    def add_output(self, name, input=None, inputs=[],
                   merge_mode='concat', concat_axis=-1, dot_axes=-1):
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
            merge = Merge(to_merge, mode=merge_mode, concat_axis=concat_axis, dot_axes=dot_axes)
            self.outputs[name] = merge

        self.output_order.append(name)
        self.output_config.append({'name': name,
                                   'input': input,
                                   'inputs': inputs,
                                   'merge_mode': merge_mode,
                                   'concat_axis': concat_axis,
                                   'dot_axes': dot_axes})

    def get_config(self):
        return {"name": self.__class__.__name__,
                "input_config": self.input_config,
                "node_config": self.node_config,
                "output_config": self.output_config,
                "input_order": self.input_order,
                "output_order": self.output_order,
                "nodes": dict([(c["name"], self.nodes[c["name"]].get_config()) for c in self.node_config])}

    def count_params(self):
        return sum([layer.count_params() for layer in self.nodes.values()])


# -*- coding: utf-8 -*-
from __future__ import absolute_import, division

import theano
import theano.tensor as T
import numpy as np

from collections import OrderedDict
import copy

from .. import activations, initializations, regularizers, constraints
from ..utils.theano_utils import shared_zeros, floatX, ndim_tensor
from ..utils.generic_utils import make_tuple
from ..regularizers import ActivityRegularizer, Regularizer

from theano.sandbox.rng_mrg import MRG_RandomStreams as RandomStreams
from six.moves import zip


class Layer(object):
    def __init__(self, **kwargs):
        for kwarg in kwargs:
            assert kwarg in {'input_shape', 'trainable'}, "Keyword argument not understood: " + kwarg
        if 'input_shape' in kwargs:
            self.set_input_shape(kwargs['input_shape'])
        if 'trainable' in kwargs:
            self._trainable = kwargs['trainable']
        if not hasattr(self, 'params'):
            self.params = []

    def set_previous(self, layer, connection_map={}):
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
        input_shape = (None,) + tuple(input_shape)
        if hasattr(self, 'input_ndim') and self.input_ndim:
            if self.input_ndim != len(input_shape):
                raise Exception('Invalid input shape - Layer expects input ndim=' +
                                str(self.input_ndim) + ', was provided with input shape ' + str(input_shape))
        self._input_shape = input_shape
        self.input = ndim_tensor(len(self._input_shape))
        self.build()

    @property
    def output_shape(self):
        # default assumption: tensor shape unchanged.
        return self.input_shape

    def get_output(self, train=False):
        return self.get_input(train)

    def get_input(self, train=False):
        if hasattr(self, 'previous'):
            return self.previous.get_output(train=train)
        elif hasattr(self, 'input'):
            return self.input
        else:
            raise Exception('Layer is not connected\
                and is not an input layer.')

    def supports_masked_input(self):
        ''' Whether or not this layer respects the output mask of its previous layer in its calculations. If you try
        to attach a layer that does *not* support masked_input to a layer that gives a non-None output_mask() that is
        an error'''
        return False

    def get_output_mask(self, train=None):
        '''
        For some models (such as RNNs) you want a way of being able to mark some output data-points as
        "masked", so they are not used in future calculations. In such a model, get_output_mask() should return a mask
        of one less dimension than get_output() (so if get_output is (nb_samples, nb_timesteps, nb_dimensions), then the mask
        is (nb_samples, nb_timesteps), with a one for every unmasked datapoint, and a zero for every masked one.

        If there is *no* masking then it shall return None. For instance if you attach an Activation layer (they support masking)
        to a layer with an output_mask, then that Activation shall also have an output_mask. If you attach it to a layer with no
        such mask, then the Activation's get_output_mask shall return None.

        Some layers have an output_mask even if their input is unmasked, notably Embedding which can turn the entry "0" into
        a mask.
        '''
        return None

    def set_weights(self, weights):
        assert len(self.params) == len(weights), 'Provided weight array does not match layer weights (' + \
            str(len(self.params)) + ' layer params vs. ' + str(len(weights)) + ' provided weights)'
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
        config = {"name": self.__class__.__name__}
        if hasattr(self, '_input_shape'):
            config['input_shape'] = self._input_shape[1:]
        if hasattr(self, '_trainable'):
            config['trainable'] = self._trainable
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

    def set_name(self, name):
        for i in range(len(self.params)):
            self.params[i].name = '%s_p%d' % (name, i)

    def count_params(self):
        return sum([np.prod(p.shape.eval()) for p in self.params])


class MaskedLayer(Layer):
    '''
    If your layer trivially supports masking (by simply copying the input mask to the output), then subclass MaskedLayer
    instead of Layer, and make sure that you incorporate the input mask into your calculation of get_output()
    '''
    def supports_masked_input(self):
        return True

    def get_input_mask(self, train=False):
        if hasattr(self, 'previous'):
            return self.previous.get_output_mask(train)
        else:
            return None

    def get_output_mask(self, train=False):
        ''' The default output mask is just the input mask unchanged. Override this in your own
        implementations if, for instance, you are reshaping the input'''
        return self.get_input_mask(train)


class Masking(MaskedLayer):
    """Mask an input sequence by using a mask value to identify padding.

    This layer copies the input to the output layer with identified padding
    replaced with 0s and creates an output mask in the process.

    At each timestep, if the values all equal `mask_value`,
    then the corresponding mask value for the timestep is 0 (skipped),
    otherwise it is 1.

    """
    def __init__(self, mask_value=0., **kwargs):
        super(Masking, self).__init__(**kwargs)
        self.mask_value = mask_value
        self.input = T.tensor3()

    def get_output_mask(self, train=False):
        X = self.get_input(train)
        return T.any(T.ones_like(X) * (1. - T.eq(X, self.mask_value)), axis=-1)

    def get_output(self, train=False):
        X = self.get_input(train)
        return X * T.shape_padright(T.any((1. - T.eq(X, self.mask_value)), axis=-1))

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "mask_value": self.mask_value}
        base_config = super(Masking, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class TimeDistributedMerge(Layer):
    '''Sum/multiply/average over the outputs of a TimeDistributed layer.

    mode: {'sum', 'mul', 'ave'}
    Tensor input dimensions:   (nb_sample, time, features)
    Tensor output dimensions:  (nb_sample, features)
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
        if self.mode == 'sum' or self.mode == 'ave':
            s = theano.tensor.sum(X, axis=1)
            if self.mode == 'ave':
                s /= X.shape[1]
            return s
        elif self.mode == 'mul':
            s = theano.tensor.mul(X, axis=1)
            return s
        else:
            raise Exception('Unknown merge mode')

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "mode": self.mode}
        base_config = super(TimeDistributedMerge, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Merge(Layer):
    def __init__(self, layers, mode='sum', concat_axis=-1, dot_axes=-1):
        ''' Merge the output of a list of layers or containers into a single tensor.
            mode: {'sum', 'mul', 'concat', 'ave', 'join'}
        '''
        if len(layers) < 2:
            raise Exception("Please specify two or more input layers (or containers) to merge")

        if mode not in {'sum', 'mul', 'concat', 'ave', 'join', 'cos', 'dot'}:
            raise Exception("Invalid merge mode: " + str(mode))

        if mode in {'sum', 'mul', 'ave', 'cos'}:
            input_shapes = set([l.output_shape for l in layers])
            if len(input_shapes) > 1:
                raise Exception("Only layers of same output shape can be merged using " + mode + " mode")
        if mode in {'cos', 'dot'}:
            if len(layers) > 2:
                raise Exception(mode + " merge takes exactly 2 layers")
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
                for i in range(len(dot_axes[0])):
                    if shape1[dot_axes[0][i]] != shape2[dot_axes[1][i]]:
                        raise Exception(" Dot incompatible layers can not be merged using dot mode")
        elif mode == 'concat':
            input_shapes = set([list(l.output_shape).pop(concat_axis) for l in layers])
            if len(input_shapes) > 1:
                raise Exception("'concat' mode can only merge layers with matching output shapes except for the concat axis")

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
            for i in self.dot_axes[0]:
                shape1.pop(i)
            for i in self.dot_axes[1]:
                shape2.pop(i)
            shape = shape1 + shape2[1:]
            if len(shape) == 1:
                shape.append(1)
            return tuple(shape)
        elif self.mode == 'cos':
            return tuple(input_shapes[0][0], 1)

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
            return T.concatenate(inputs, axis=self.concat_axis)
        elif self.mode == 'join':
            inputs = OrderedDict()
            for i in range(len(self.layers)):
                X = self.layers[i].get_output(train)
                if X.name is None:
                    raise ValueError("merge_mode='join' only works with named inputs")
                else:
                    inputs[X.name] = X
            return inputs
        elif self.mode == 'mul':
            s = self.layers[0].get_output(train)
            for i in range(1, len(self.layers)):
                s *= self.layers[i].get_output(train)
            return s
        elif self.mode == 'dot':
            l1 = self.layers[0].get_output(train)
            l2 = self.layers[1].get_output(train)
            output = T.batched_tensordot(l1, l2, self.dot_axes)
            output = output.dimshuffle((0, 'x'))
            return output
        elif self.mode == 'cos':
            l1 = self.layers[0].get_output(train)
            l2 = self.layers[1].get_output(train)
            output, _ = theano.scan(lambda v1, v2: T.dot(v1, v2)/T.sqrt(T.dot(v1, v1) * T.dot(v2, v2)), sequences=[l1, l2], outputs_info=None)
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
        config = {"name": self.__class__.__name__,
                  "layers": [l.get_config() for l in self.layers],
                  "mode": self.mode,
                  "concat_axis": self.concat_axis,
                  "dot_axes": self.dot_axes}
        base_config = super(Merge, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))



class Dropout(MaskedLayer):
    '''
        Hinton's dropout.
    '''
    def __init__(self, p, **kwargs):
        super(Dropout, self).__init__(**kwargs)
        self.p = p
        self.srng = RandomStreams(seed=np.random.randint(10e6))

    def get_output(self, train=False):
        X = self.get_input(train)
        if self.p > 0.:
            retain_prob = 1. - self.p
            if train:
                X *= self.srng.binomial(X.shape, p=retain_prob, dtype=theano.config.floatX) / retain_prob
        return X

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "p": self.p}
        base_config = super(Dropout, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Activation(MaskedLayer):
    '''
        Apply an activation function to an output.
    '''
    def __init__(self, activation, target=0, beta=0.1, **kwargs):
        super(Activation, self).__init__(**kwargs)
        self.activation = activations.get(activation)
        self.target = target
        self.beta = beta

    def get_output(self, train=False):
        X = self.get_input(train)
        return self.activation(X)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "activation": self.activation.__name__,
                  "target": self.target,
                  "beta": self.beta}
        base_config = super(Activation, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Reshape(Layer):
    '''
        Reshape an output to a certain shape.
        Can't be used as first layer in a model (no fixed input!)
        First dimension is assumed to be nb_samples.
    '''
    def __init__(self, dims, **kwargs):
        super(Reshape, self).__init__(**kwargs)
        self.dims = tuple(dims)

    @property
    def output_shape(self):
        return (self.input_shape[0],) + self.dims

    def get_output(self, train=False):
        X = self.get_input(train)
        new_shape = (X.shape[0],) + self.dims
        return theano.tensor.reshape(X, new_shape)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "dims": self.dims}
        base_config = super(Reshape, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Permute(Layer):
    '''
        Permute the dimensions of the input according to the given tuple.
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
        return X.dimshuffle((0,) + self.dims)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "dims": self.dims}
        base_config = super(Permute, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Flatten(Layer):
    '''
        Reshape input to flat shape.
        First dimension is assumed to be nb_samples.
    '''
    def __init__(self, **kwargs):
        super(Flatten, self).__init__(**kwargs)

    @property
    def output_shape(self):
        input_shape = self.input_shape
        return (input_shape[0], np.prod(input_shape[1:]))

    def get_output(self, train=False):
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
    def __init__(self, n, **kwargs):
        super(RepeatVector, self).__init__(**kwargs)
        self.n = n

    @property
    def output_shape(self):
        input_shape = self.input_shape
        return (input_shape[0], self.n, input_shape[1])

    def get_output(self, train=False):
        X = self.get_input(train)
        tensors = [X]*self.n
        stacked = theano.tensor.stack(*tensors)
        return stacked.dimshuffle((1, 0, 2))

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "n": self.n}
        base_config = super(RepeatVector, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class Dense(Layer):
    '''
        Just your regular fully connected NN layer.
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
        super(Dense, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[1]

        self.input = T.matrix()
        self.W = self.init((input_dim, self.output_dim))
        self.b = shared_zeros((self.output_dim,))

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
        output = self.activation(T.dot(X, self.W) + self.b)
        return output

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
                  "input_dim": self.input_dim}
        base_config = super(Dense, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ActivityRegularization(Layer):
    '''
        Layer that passes through its input unchanged, but applies an update
        to the cost function based on the activity.
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
    '''
       Apply a same Dense layer for each dimension[1] (time_dimension) input.
       Especially useful after a recurrent network with 'return_sequence=True'.
       Tensor input dimensions:   (nb_sample, time_dimension, input_dim)
       Tensor output dimensions:  (nb_sample, time_dimension, output_dim)

    '''
    input_ndim = 3

    def __init__(self, output_dim, init='glorot_uniform', activation='linear', weights=None,
                 W_regularizer=None, b_regularizer=None, activity_regularizer=None,
                 W_constraint=None, b_constraint=None, input_dim=None, input_length=None, **kwargs):
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
        super(TimeDistributedDense, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[2]

        self.input = T.tensor3()
        self.W = self.init((input_dim, self.output_dim))
        self.b = shared_zeros((self.output_dim))

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
        output = self.activation(T.dot(X.dimshuffle(1, 0, 2), self.W) + self.b)
        return output.dimshuffle(1, 0, 2)

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

    Tensor input dimensions: same as encoder input
    Tensor output dimensions:
        if output_reconstruction:
            same as encoder output
        else:
            same as decoder output
    '''
    def __init__(self, encoder, decoder, output_reconstruction=True, weights=None, **kwargs):
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
        self.encoder.previous.output_shape

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
    '''
        Max-out layer, nb_feature is the number of pieces in the piecewise linear approx.
        Refer to http://arxiv.org/pdf/1302.4389.pdf
    '''
    input_ndim = 2

    def __init__(self, output_dim, nb_feature=4, init='glorot_uniform', weights=None,
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
        super(MaxoutDense, self).__init__(**kwargs)

    def build(self):
        input_dim = self.input_shape[1]

        self.input = T.matrix()
        self.W = self.init((self.nb_feature, input_dim, self.output_dim))
        self.b = shared_zeros((self.nb_feature, self.output_dim))

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
        output = T.max(T.dot(X, self.W) + self.b, axis=1)
        return output

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "output_dim": self.output_dim,
                  "init": self.init.__name__,
                  "nb_feature": self.nb_feature,
                  "W_regularizer": self.W_regularizer.get_config() if self.W_regularizer else None,
                  "b_regularizer": self.b_regularizer.get_config() if self.b_regularizer else None,
                  "activity_regularizer": self.activity_regularizer.get_config() if self.activity_regularizer else None,
                  "W_constraint": self.W_constraint.get_config() if self.W_constraint else None,
                  "b_constraint": self.b_constraint.get_config() if self.b_constraint else None,
                  "input_dim": self.input_dim}
        base_config = super(MaxoutDense, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

from __future__ import absolute_import
import theano
import theano.tensor as T

from .. import activations, initializations, regularizers, constraints
from ..layers.core import Layer, MaskedLayer
from ..utils.theano_utils import sharedX

from ..constraints import unitnorm


class Embedding(Layer):
    '''
        Turn positive integers (indexes) into denses vectors of fixed size.
        eg. [[4], [20]] -> [[0.25, 0.1], [0.6, -0.2]]

        @input_dim: size of vocabulary (highest input integer + 1)
        @out_dim: size of dense representation
    '''
    input_ndim = 2

    def __init__(self, input_dim, output_dim, init='uniform', input_length=None,
                 W_regularizer=None, activity_regularizer=None, W_constraint=None,
                 mask_zero=False, weights=None, **kwargs):
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
        self.input = T.imatrix()
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
            return T.ones_like(X) * (1 - T.eq(X, 0))

    @property
    def output_shape(self):
        return (self.input_shape[0], self.input_length, self.output_dim)

    def get_output(self, train=False):
        X = self.get_input(train)
        out = self.W[X]
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


class WordContextProduct(Layer):
    '''
        This layer turns a pair of words (a pivot word + a context word,
        ie. a word from the same context, or a random, out-of-context word),
        identified by their index in a vocabulary, into two dense representations
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
            Efficient Estimation of Word representations in Vector Space
            http://arxiv.org/pdf/1301.3781v3.pdf
    '''
    input_ndim = 2

    def __init__(self, input_dim, proj_dim=128,
                 init='uniform', activation='sigmoid', weights=None, **kwargs):

        super(WordContextProduct, self).__init__(**kwargs)
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

    @property
    def output_shape(self):
        return (self.input_shape[0], 1)

    def get_output(self, train=False):
        X = self.get_input(train)
        w = self.W_w[X[:, 0]]  # nb_samples, proj_dim
        c = self.W_c[X[:, 1]]  # nb_samples, proj_dim

        dot = T.sum(w * c, axis=1)
        dot = theano.tensor.reshape(dot, (X.shape[0], 1))
        return self.activation(dot)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "input_dim": self.input_dim,
                  "proj_dim": self.proj_dim,
                  "init": self.init.__name__,
                  "activation": self.activation.__name__}
        base_config = super(WordContextProduct, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

from __future__ import absolute_import
import numpy as np
from .core import MaskedLayer
import theano
import theano.tensor as T
from theano.sandbox.rng_mrg import MRG_RandomStreams as RandomStreams


class GaussianNoise(MaskedLayer):
    '''
        Corruption process with GaussianNoise
    '''
    def __init__(self, sigma, **kwargs):
        super(GaussianNoise, self).__init__(**kwargs)
        self.sigma = sigma
        self.srng = RandomStreams(seed=np.random.randint(10e6))

    def get_output(self, train=False):
        X = self.get_input(train)
        if not train or self.sigma == 0:
            return X
        else:
            return X + self.srng.normal(size=X.shape, avg=0.0, std=self.sigma,
                                        dtype=theano.config.floatX)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "sigma": self.sigma}
        base_config = super(GaussianNoise, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class GaussianDropout(MaskedLayer):
    '''
        Multiplicative Gaussian Noise
        Reference:
            Dropout: A Simple Way to Prevent Neural Networks from Overfitting
            Srivastava, Hinton, et al. 2014
            http://www.cs.toronto.edu/~rsalakhu/papers/srivastava14a.pdf
    '''
    def __init__(self, p, **kwargs):
        super(GaussianDropout, self).__init__(**kwargs)
        self.p = p
        self.srng = RandomStreams(seed=np.random.randint(10e6))

    def get_output(self, train):
        X = self.get_input(train)
        if train:
            # self.p refers to drop probability rather than retain probability (as in paper) to match Dropout layer syntax
            X *= self.srng.normal(size=X.shape, avg=1.0, std=T.sqrt(self.p / (1.0 - self.p)), dtype=theano.config.floatX)
        return X

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "p": self.p}
        base_config = super(GaussianDropout, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

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
        config = {"name": self.__class__.__name__,
                  "alpha": self.alpha}
        base_config = super(LeakyReLU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class PReLU(MaskedLayer):
    '''
        Reference:
            Delving Deep into Rectifiers: Surpassing Human-Level Performance on ImageNet Classification
                http://arxiv.org/pdf/1502.01852v1.pdf
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
        pos = T.nnet.relu(X)
        neg = self.alphas * (X - abs(X)) * 0.5
        return pos + neg

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "init": self.init.__name__}
        base_config = super(PReLU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ParametricSoftplus(MaskedLayer):
    '''
        Parametric Softplus of the form: alpha * log(1 + exp(beta * X))

        Reference:
            Inferring Nonlinear Neuronal Computation Based on Physiologically Plausible Inputs
            http://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003143
    '''
    def __init__(self, alpha_init=0.2, beta_init=5.0,
                 weights=None, **kwargs):
        self.alpha_init = alpha_init
        self.beta_init = beta_init
        self.initial_weights = weights
        super(ParametricSoftplus, self).__init__(**kwargs)

    def build(self):
        input_shape = self.input_shape[1:]
        self.alphas = sharedX(self.alpha_init * np.ones(input_shape))
        self.betas = sharedX(self.beta_init * np.ones(input_shape))
        self.params = [self.alphas, self.betas]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def get_output(self, train):
        X = self.get_input(train)
        return T.nnet.softplus(self.betas * X) * self.alphas

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "alpha_init": self.alpha_init,
                  "beta_init": self.beta_init}
        base_config = super(ParametricSoftplus, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


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
        config = {"name": self.__class__.__name__,
                  "theta": self.theta}
        base_config = super(ThresholdedLinear, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class ThresholdedReLU(MaskedLayer):
    '''
        Thresholded Rectified Activation

        Reference:
            Zero-Bias Autoencoders and the Benefits of Co-Adapting Features
            http://arxiv.org/pdf/1402.3337.pdf
    '''
    def __init__(self, theta=1.0, **kwargs):
        super(ThresholdedReLU, self).__init__(**kwargs)
        self.theta = theta

    def get_output(self, train):
        X = self.get_input(train)
        return T.switch(X > self.theta, X, 0)

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "theta": self.theta}
        base_config = super(ThresholdedReLU, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

from ..layers.core import Layer
from ..utils.theano_utils import shared_zeros, shared_ones, ndim_tensor, floatX
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
    def __init__(self, epsilon=1e-6, mode=0, momentum=0.9, weights=None, **kwargs):
        self.init = initializations.get("uniform")
        self.epsilon = epsilon
        self.mode = mode
        self.momentum = momentum
        self.initial_weights = weights
        super(BatchNormalization, self).__init__(**kwargs)

    def build(self):
        input_shape = self.input_shape  # starts with samples axis
        input_shape = input_shape[1:]
        self.input = ndim_tensor(len(input_shape) + 1)

        self.gamma = self.init((input_shape))
        self.beta = shared_zeros(input_shape)

        self.params = [self.gamma, self.beta]
        self.running_mean = shared_zeros(input_shape)
        self.running_std = shared_ones((input_shape))

        # initialize self.updates: batch mean/std computation
        X = self.get_input(train=True)
        m = X.mean(axis=0)
        std = T.mean((X - m) ** 2 + self.epsilon, axis=0) ** 0.5
        mean_update = self.momentum * self.running_mean + (1-self.momentum) * m
        std_update = self.momentum * self.running_std + (1-self.momentum) * std
        self.updates = [(self.running_mean, mean_update), (self.running_std, std_update)]

        if self.initial_weights is not None:
            self.set_weights(self.initial_weights)
            del self.initial_weights

    def get_weights(self):
        return super(BatchNormalization, self).get_weights() + [self.running_mean.get_value(), self.running_std.get_value()]

    def set_weights(self, weights):
        self.running_mean.set_value(floatX(weights[-2]))
        self.running_std.set_value(floatX(weights[-1]))
        super(BatchNormalization, self).set_weights(weights[:-2])

    def get_output(self, train):
        X = self.get_input(train)

        if self.mode == 0:
            X_normed = (X - self.running_mean) / (self.running_std + self.epsilon)

        elif self.mode == 1:
            m = X.mean(axis=-1, keepdims=True)
            std = X.std(axis=-1, keepdims=True)
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


class LRN2D(Layer):
    """
    This code is adapted from pylearn2.
    License at: https://github.com/lisa-lab/pylearn2/blob/master/LICENSE.txt
    """

    def __init__(self, alpha=1e-4, k=2, beta=0.75, n=5, **kwargs):
        if n % 2 == 0:
            raise NotImplementedError("LRN2D only works with odd n. n provided: " + str(n))
        super(LRN2D, self).__init__(**kwargs)
        self.alpha = alpha
        self.k = k
        self.beta = beta
        self.n = n

    def get_output(self, train):
        X = self.get_input(train)
        b, ch, r, c = X.shape
        half_n = self.n // 2
        input_sqr = T.sqr(X)
        extra_channels = T.alloc(0., b, ch + 2*half_n, r, c)
        input_sqr = T.set_subtensor(extra_channels[:, half_n:half_n+ch, :, :], input_sqr)
        scale = self.k
        for i in range(self.n):
            scale += self.alpha * input_sqr[:, i:i+ch, :, :]
        scale = scale ** self.beta
        return X / scale

    def get_config(self):
        config = {"name": self.__class__.__name__,
                  "alpha": self.alpha,
                  "k": self.k,
                  "beta": self.beta,
                  "n": self.n}
        base_config = super(LRN2D, self).get_config()
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

import tarfile, inspect, os
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
from __future__ import print_function
from .data_utils import get_file
import string
import random
import os
from six.moves import cPickle
from six.moves import zip
import numpy as np


def make_reuters_dataset(path=os.path.join('datasets', 'temp', 'reuters21578'), min_samples_per_topic=15):
    import re
    from ..preprocessing.text import Tokenizer

    wire_topics = []
    topic_counts = {}
    wire_bodies = []

    for fname in os.listdir(path):
        if 'sgm' in fname:
            s = open(os.path.join(path, fname)).read()
            tag = '<TOPICS>'
            while tag in s:
                s = s[s.find(tag)+len(tag):]
                topics = s[:s.find('</')]
                if topics and '</D><D>' not in topics:
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
    items.sort(key=lambda x: x[1])
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
    print('text reconstruction:')
    reverse_word_index = dict([(v, k) for k, v in tokenizer.word_index.items()])
    print(' '.join(reverse_word_index[i] for i in X[10]))

    dataset = (X, labels)
    print('-')
    print('Saving...')
    cPickle.dump(dataset, open(os.path.join('datasets', 'data', 'reuters.pkl'), 'w'))
    cPickle.dump(tokenizer.word_index, open(os.path.join('datasets', 'data', 'reuters_word_index.pkl'), 'w'))


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
import theano
import copy

from ..layers.advanced_activations import LeakyReLU, PReLU
from ..layers.core import Dense, Merge, Dropout, Activation, Reshape, Flatten, RepeatVector, Layer, AutoEncoder, Masking, Permute
from ..layers.core import ActivityRegularization, TimeDistributedDense, AutoEncoder, MaxoutDense
from ..layers.convolutional import Convolution1D, Convolution2D, MaxPooling1D, MaxPooling2D, ZeroPadding2D
from ..layers.embeddings import Embedding, WordContextProduct
from ..layers.noise import GaussianNoise, GaussianDropout
from ..layers.normalization import BatchNormalization, LRN2D
from ..layers.recurrent import SimpleRNN, SimpleDeepRNN, GRU, LSTM, JZS1, JZS2, JZS3
from ..layers import containers
from .. import regularizers
from .. import constraints


def container_from_config(original_layer_dict, custom_objects={}):
    layer_dict = copy.deepcopy(original_layer_dict)
    name = layer_dict.get('name')

    # Insert custom layers into globals so they can be accessed by `get_from_module`.
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
                else: # not a regularizer of constraint, don't touch it
                    v['name'] = vname

        base_layer = get_layer(name, layer_dict)
        return base_layer


def print_layer_shapes(model, input_shapes):
    """
    Utility function to print the shape of the output at each layer of a Model

    Arguments:
        model: instance of Model / Merge
        input_shapes: dict (Graph), list of tuples (Merge) or tuple (Sequential)
    """
    if model.__class__.__name__ in ['Sequential', 'Merge']:
        # in this case input_shapes is a tuple, or a list [shape1, shape2]
        if not isinstance(input_shapes[0], tuple):
            input_shapes = [input_shapes]

        inputs = model.get_input(train=False)
        if not isinstance(inputs, list):
            inputs = [inputs]
        input_dummy = [np.zeros(shape, dtype=np.float32)
                       for shape in input_shapes]
        layers = model.layers

    elif model.__class__.__name__ == 'Graph':
        # in this case input_shapes is a dictionary
        inputs = [model.inputs[name].input
                  for name in model.input_order]
        input_dummy = [np.zeros(input_shapes[name], dtype=np.float32)
                       for name in model.input_order]
        layers = [model.nodes[c['name']] for c in model.node_config]

    print("input shapes : ", input_shapes)
    for l in layers:
        shape_f = theano.function(inputs, l.get_output(train=False).shape,
                                  on_unused_input='ignore')
        out_shape = tuple(shape_f(*input_dummy))
        config = l.get_config()
        print('shape after %s: %s' % (config['name'], out_shape))


from .generic_utils import get_from_module
def get_layer(identifier, kwargs=None):
    return get_from_module(identifier, globals(), 'layer', instantiate=True, kwargs=kwargs)

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
                if type(self.sum_values[k]) is list:
                    info += ' - %s: %.4f' % (k, self.sum_values[k][0] / max(1, self.sum_values[k][1]))
                else:
                    info += ' - %s: %s' % (k, self.sum_values[k])

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
                    info += ' - %s: %.4f' % (k, self.sum_values[k][0] / max(1, self.sum_values[k][1]))
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


def ndim_tensor(ndim):
    if ndim == 1:
        return T.vector()
    elif ndim == 2:
        return T.matrix()
    elif ndim == 3:
        return T.tensor3()
    elif ndim == 4:
        return T.tensor4()
    return T.matrix()


def on_gpu():
    return theano.config.device[:3] == 'gpu'


import pydot
# old pydot will not work with python3, must use one
# that works with python3 such as pydot2 or pydot


def plot(model, to_file='model.png'):

    graph = pydot.Dot(graph_type='digraph')
    if type(model) == Sequential:
        previous_node = None
        written_nodes = []
        n = 1
        for node in model.get_config()['layers']:
            # append number in case layers have same name to differentiate
            if (node['name'] + str(n)) in written_nodes:
                n += 1
            current_node = pydot.Node(node['name'] + str(n))
            written_nodes.append(node['name'] + str(n))
            graph.add_node(current_node)
            if previous_node:
                graph.add_edge(pydot.Edge(previous_node, current_node))
            previous_node = current_node
        graph.write_png(to_file)

    elif type(model) == Graph:
        # don't need to append number for names since all nodes labeled
        for input_node in model.input_config:
            graph.add_node(pydot.Node(input_node['name']))

        # intermediate and output nodes have input defined
        for layer_config in [model.node_config, model.output_config]:
            for node in layer_config:
                graph.add_node(pydot.Node(node['name']))
                # possible to have multiple 'inputs' vs 1 'input'
                if node['inputs']:
                    for e in node['inputs']:
                        graph.add_edge(pydot.Edge(e, node['name']))
                else:
                    graph.add_edge(pydot.Edge(node['input'], node['name']))

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




from __future__ import absolute_import
from __future__ import print_function
import keras
from keras.datasets import mnist
import keras.models
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.regularizers import l2, l1
from keras.constraints import maxnorm, nonneg
from keras.optimizers import SGD, Adam, RMSprop
from keras.utils import np_utils, generic_utils
import theano
import theano.tensor as T
import numpy as np
import scipy

batch_size = 100
nb_classes = 10
nb_epoch = 10

# the data, shuffled and split between tran and test sets
(X_train, y_train), (X_test, y_test) = mnist.load_data()
X_train=X_train.reshape(60000,784)
X_test=X_test.reshape(10000,784)
X_train = X_train.astype("float32")
X_test = X_test.astype("float32")
X_train /= 255
X_test /= 255

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)

model = Sequential()
model.add(Dense(784, 20, W_constraint=maxnorm(1)))
model.add(Activation('relu'))
model.add(Dropout(0.1))
model.add(Dense(20, 20, W_constraint=nonneg()))
model.add(Activation('relu'))
model.add(Dropout(0.1))
model.add(Dense(20, 10, W_constraint=maxnorm(1)))
model.add(Activation('softmax'))


rms = RMSprop()
model.compile(loss='categorical_crossentropy', optimizer=rms)

model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch, show_accuracy=True, verbose=0)

a=model.params[0].eval()
if np.isclose(np.max(np.sqrt(np.sum(a**2, axis=0))),1):
	print('Maxnorm test passed')
else:
	raise ValueError('Maxnorm test failed!')
		
b=model.params[2].eval()
if np.min(b)==0 and np.min(a)!=0:
	print('Nonneg test passed')
else:
	raise ValueError('Nonneg test failed!')
	

model = Sequential()
model.add(Dense(784, 20))
model.add(Activation('relu'))
model.add(Dense(20, 20, W_regularizer=l1(.01)))
model.add(Activation('relu'))
model.add(Dense(20, 10))
model.add(Activation('softmax'))


rms = RMSprop()
model.compile(loss='categorical_crossentropy', optimizer=rms)

model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=20, show_accuracy=True, verbose=0)

a=model.params[2].eval().reshape(400)
(D, p1) = scipy.stats.kurtosistest(a)

model = Sequential()
model.add(Dense(784, 20))
model.add(Activation('relu'))
model.add(Dense(20, 20, W_regularizer=l2(.01)))
model.add(Activation('relu'))
model.add(Dense(20, 10))
model.add(Activation('softmax'))


rms = RMSprop()
model.compile(loss='categorical_crossentropy', optimizer=rms)

model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=20, show_accuracy=True, verbose=0)

a=model.params[2].eval().reshape(400)
(D, p2) = scipy.stats.kurtosistest(a)

if p1<.01 and p2>.01:
	print('L1 and L2 regularization tests passed')
else:
	raise ValueError('L1 and L2 regularization tests failed!')
from __future__ import absolute_import
from __future__ import print_function
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Activation
from keras.utils import np_utils
from keras.wrappers.scikit_learn import *
import numpy as np

batch_size = 128
nb_epoch = 1

nb_classes = 10
max_train_samples = 5000
max_test_samples = 1000

np.random.seed(1337) # for reproducibility

############################################
# scikit-learn classification wrapper test #
############################################
print('Beginning scikit-learn classification wrapper test')

print('Loading data')
(X_train, y_train), (X_test, y_test) = mnist.load_data()

X_train = X_train.reshape(60000, 784)[:max_train_samples]
X_test = X_test.reshape(10000, 784)[:max_test_samples]
X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
X_train /= 255
X_test /= 255

Y_train = np_utils.to_categorical(y_train, nb_classes)[:max_train_samples]
Y_test = np_utils.to_categorical(y_test, nb_classes)[:max_test_samples]

print('Defining model')
model = Sequential()
model.add(Dense(784, 50))
model.add(Activation('relu'))
model.add(Dense(50, 10))
model.add(Activation('softmax'))

print('Creating wrapper')
classifier = KerasClassifier(model, train_batch_size=batch_size, nb_epoch=nb_epoch)

print('Fitting model')
classifier.fit(X_train, Y_train)

print('Testing score function')
score = classifier.score(X_train, Y_train)
print('Score: ', score)

print('Testing predict function')
preds = classifier.predict(X_test)
print('Preds.shape: ', preds.shape)

print('Testing predict proba function')
proba = classifier.predict_proba(X_test)
print('Proba.shape: ', proba.shape)

print('Testing get params')
print(classifier.get_params())

print('Testing set params')
classifier.set_params(optimizer='sgd', loss='binary_crossentropy')
print(classifier.get_params())

print('Testing attributes')
print('Classes')
print(classifier.classes_)
print('Config')
print(classifier.config_)
print('Weights')
print(classifier.weights_)
print('Compiled model')
print(classifier.compiled_model_)

########################################
# scikit-learn regression wrapper test #
########################################
print('Beginning scikit-learn regression wrapper test')

print('Generating data')
X_train = np.random.random((5000, 100))
X_test = np.random.random((1000, 100))
y_train = np.random.random(5000)
y_test = np.random.random(1000)

print('Defining model')
model = Sequential()
model.add(Dense(100, 50))
model.add(Activation('relu'))
model.add(Dense(50, 1))
model.add(Activation('linear'))

print('Creating wrapper')
regressor = KerasRegressor(model, train_batch_size=batch_size, nb_epoch=nb_epoch)

print('Fitting model')
regressor.fit(X_train, y_train)

print('Testing score function')
score = regressor.score(X_train, y_train)
print('Score: ', score)

print('Testing predict function')
preds = regressor.predict(X_test)
print('Preds.shape: ', preds.shape)

print('Testing get params')
print(regressor.get_params())

print('Testing set params')
regressor.set_params(optimizer='sgd', loss='mean_absolute_error')
print(regressor.get_params())

print('Testing attributes')
print('Config')
print(regressor.config_)
print('Weights')
print(regressor.weights_)
print('Compiled model')
print(regressor.compiled_model_)

print('Test script complete.')

# Dummy test data as input to RNN. This input is 3 timesteps long where the third timestep always matches the
# first. Without masking it should be able to learn it, with masking it should fail.

import numpy as np
from keras.utils.theano_utils import sharedX
from keras.models import Sequential
from keras.layers.core import Dense, Activation, Merge, Dropout, TimeDistributedDense
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import SimpleRNN, SimpleDeepRNN, LSTM, GRU
import theano

theano.config.exception_verbosity = 'high' 

# (nb_samples, timesteps, dimensions)
X = np.random.random_integers(1, 4, size=(500000, 15))

print("About to compile the first model")
model = Sequential()
model.add(Embedding(5, 4, mask_zero=True))
model.add(TimeDistributedDense(4, 4)) # obviously this is redundant. Just testing.
model.add(SimpleRNN(4, 4, activation='relu', return_sequences=True))
model.add(Dropout(0.5))
model.add(SimpleDeepRNN(4, 4, depth=2, activation='relu')) 
model.add(Dropout(0.5))
model.add(Dense(4, 4, activation='softmax'))
model.compile(loss='categorical_crossentropy',
        optimizer='rmsprop', theano_mode=theano.compile.mode.FAST_RUN)
print("Compiled model")

W = model.get_weights() # We'll save these so we can reset it later

X[:, : 10] = 0
Xmask0 = X.copy()
Xmask0[:, 10] = 0

Xmask12 = X.copy()
Xmask12[:, 11] = 0
Xmask12[:, 12] = 0

X0_onehot = np.zeros((X.shape[0], 4))
X1_onehot = np.zeros((X.shape[0], 4))
for i, row in enumerate(X):
    X0_onehot[i, row[10] - 1] = 1
    X1_onehot[i, row[11] - 1] = 1

# Uniform score: 4 options = ln(4) nats (2 bits)
# we should not do better than this when we mask out the part of the input
# that gives us the correct answer
uniform_score = np.log(4)
batch_size=512

# Train it to guess 0th dim
model.fit(X, X0_onehot, nb_epoch=1, batch_size=batch_size)
score = model.evaluate(X, X0_onehot, batch_size=batch_size)
if score > uniform_score * 0.9:
    raise Exception('Failed to learn to copy timestep 0, score %f' % score)
    

model.set_weights(W)

# Train without showing it the 0th dim to learn 1st dim
model.fit(X[: , 1:], X1_onehot, nb_epoch=1, batch_size=batch_size)
score = model.evaluate(X[:, 1:], X1_onehot, batch_size=batch_size)
if score > uniform_score * 0.9:
    raise Exception('Failed to learn to copy timestep 1, score %f' % score)

model.set_weights(W)

# Train to guess 0th dim when 0th dim has been masked (should fail)
model.fit(Xmask0, X0_onehot, nb_epoch=1, batch_size=batch_size)
score = model.evaluate(Xmask0, X0_onehot, batch_size=batch_size)
if score < uniform_score * 0.9:
   raise Exception('Somehow learned to copy timestep 0 despite mask, score %f' % score)

model.set_weights(W)

# Train to guess 1st dim when 0th dim has been masked (should succeed)
model.fit(Xmask0, X1_onehot, nb_epoch=1, batch_size=batch_size)
score = model.evaluate(Xmask0, X1_onehot, batch_size=batch_size)
if score > uniform_score * 0.9:
    raise Exception('Failed to learn to copy timestep 1 in masked model, score %f' % score)

model.set_weights(W)

# Finally, make sure the mask is actually blocking input, mask out timesteps 1 and 2, and see if
# it can learn timestep 0 (should fail)
model.fit(Xmask12, X0_onehot, nb_epoch=1, batch_size=batch_size)

score = model.evaluate(Xmask12, X0_onehot, batch_size=batch_size)
if score < uniform_score * 0.9:
    raise Exception('Somehow learned to copy timestep 0 despite masking 1, score %f' % score)

# Another testing approach, just initialize models and make sure that prepending zeros doesn't affect
# their output
print("About to compile the second model")
model2 = Sequential()
model2.add(Embedding(5, 4, mask_zero=True))
model2.add(TimeDistributedDense(4, 4))
model2.add(Activation('time_distributed_softmax'))
model2.add(LSTM(4, 4, return_sequences=True))
model2.add(Activation('tanh'))
model2.add(GRU(4, 4, activation='softmax', return_sequences=True))
model2.add(SimpleDeepRNN(4, 4, depth=2, activation='relu', return_sequences=True)) 
model2.add(SimpleRNN(4, 4, activation='relu', return_sequences=True))
model2.compile(loss='categorical_crossentropy',
        optimizer='rmsprop', theano_mode=theano.compile.mode.FAST_RUN)
print("Compiled model2")

X2 = np.random.random_integers(1, 4, size=(2, 5))
y2 = np.random.random((X2.shape[0], X2.shape[1], 4))

ref = model2.predict(X2)
ref_eval = model2.evaluate(X2, y2)
mask = np.ones((y2.shape[0], y2.shape[1], 1))

for pre_zeros in range(1, 10):
    padded_X2 = np.concatenate((np.zeros((X2.shape[0], pre_zeros)), X2), axis=1)
    padded_mask = np.concatenate((np.zeros((mask.shape[0], pre_zeros, mask.shape[2])), mask), axis=1)
    padded_y2 = np.concatenate((np.zeros((y2.shape[0], pre_zeros, y2.shape[2])), y2), axis=1)

    pred = model2.predict(padded_X2)
    if not np.allclose(ref[:, -1, :], pred[:, -1, :]):
        raise Exception("Different result after left-padding %d zeros. Ref: %s, Pred: %s" % (pre_zeros, ref, pred))

    pad_eval = model2.evaluate(padded_X2, padded_y2, weights=padded_mask)
    if not np.allclose([pad_eval], [ref_eval]):
        raise Exception("Got dissimilar categorical_crossentropy after left-padding %d zeros. Ref: %f, Pred %f" %\
                (pref_eval, pred_val))

        


from __future__ import absolute_import
from __future__ import print_function
from keras.datasets import mnist
from keras.models import Sequential, model_from_config
from keras.layers.core import AutoEncoder, Dense, Activation, TimeDistributedDense, Flatten
from keras.layers.recurrent import LSTM
from keras.layers.embeddings import Embedding
from keras.layers.core import Layer
from keras.layers import containers
from keras.utils import np_utils
import numpy as np

nb_classes = 10
batch_size = 128
nb_epoch = 5
activation = 'linear'

input_dim = 784
hidden_dim = 392

max_train_samples = 5000
max_test_samples = 1000

# the data, shuffled and split between tran and test sets
(X_train, y_train), (X_test, y_test) = mnist.load_data()

X_train = X_train.reshape(60000, input_dim)[:max_train_samples]
X_test = X_test.reshape(10000, input_dim)[:max_test_samples]
X_train = X_train.astype("float32")
X_test = X_test.astype("float32")
X_train /= 255
X_test /= 255

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)[:max_train_samples]
Y_test = np_utils.to_categorical(y_test, nb_classes)[:max_test_samples]

print("X_train: ", X_train.shape)
print("X_test: ", X_test.shape)


##########################
# dense model test       #
##########################

print("Training classical fully connected layer for classification")
model_classical = Sequential()
model_classical.add(Dense(input_dim, 10, activation=activation))
model_classical.add(Activation('softmax'))
model_classical.get_config(verbose=1)
model_classical.compile(loss='categorical_crossentropy', optimizer='adam')
model_classical.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch, show_accuracy=False, verbose=0, validation_data=(X_test, Y_test))
classical_score = model_classical.evaluate(X_test, Y_test, verbose=0, show_accuracy=True)
print('\nclassical_score:', classical_score)

##########################
# autoencoder model test #
##########################


def build_lstm_autoencoder(autoencoder, X_train, X_test):
    X_train = X_train[:, np.newaxis, :]
    X_test = X_test[:, np.newaxis, :]
    print("Modified X_train: ", X_train.shape)
    print("Modified X_test: ", X_test.shape)

    # The TimeDistributedDense isn't really necessary, however you need a lot of GPU memory to do 784x394-394x784
    autoencoder.add(TimeDistributedDense(input_dim, 16))
    autoencoder.add(AutoEncoder(encoder=LSTM(16, 8, activation=activation, return_sequences=True),
                                decoder=LSTM(8, input_dim, activation=activation, return_sequences=True),
                                output_reconstruction=False))
    return autoencoder, X_train, X_test


def build_deep_classical_autoencoder(autoencoder):
    encoder = containers.Sequential([Dense(input_dim, hidden_dim, activation=activation), Dense(hidden_dim, hidden_dim/2, activation=activation)])
    decoder = containers.Sequential([Dense(hidden_dim/2, hidden_dim, activation=activation), Dense(hidden_dim, input_dim, activation=activation)])
    autoencoder.add(AutoEncoder(encoder=encoder, decoder=decoder, output_reconstruction=False))
    return autoencoder

# Try different things here: 'lstm' or 'classical' or 'denoising'
# or 'deep_denoising'

for autoencoder_type in ['classical', 'lstm']:
    print(autoencoder_type)
    print('-'*40)
    # Build our autoencoder model
    autoencoder = Sequential()
    if autoencoder_type == 'lstm':
        print("Training LSTM AutoEncoder")
        autoencoder, X_train, X_test = build_lstm_autoencoder(autoencoder, X_train, X_test)
    elif autoencoder_type == 'classical':
        print("Training Classical AutoEncoder")
        autoencoder = build_deep_classical_autoencoder(autoencoder)
    else:
        print("Error: unknown autoencoder type!")
        exit(-1)

    autoencoder.compile(loss='mean_squared_error', optimizer='adam')
    # Do NOT use validation data with return output_reconstruction=True
    autoencoder.fit(X_train, X_train, batch_size=batch_size, nb_epoch=nb_epoch, show_accuracy=False, verbose=1)

    # Do an inference pass
    prefilter_train = autoencoder.predict(X_train, verbose=0)
    prefilter_test = autoencoder.predict(X_test, verbose=0)
    print("prefilter_train: ", prefilter_train.shape)
    print("prefilter_test: ", prefilter_test.shape)

    # Classify results from Autoencoder
    print("Building classical fully connected layer for classification")
    model = Sequential()
    if autoencoder_type == 'lstm':
        model.add(TimeDistributedDense(8, nb_classes, activation=activation))
        model.add(Flatten())
    elif autoencoder_type == 'classical':
        model.add(Dense(prefilter_train.shape[1], nb_classes, activation=activation))
    else:
        model.add(Dense(prefilter_train.shape[1], nb_classes, activation=activation))

    model.add(Activation('softmax'))

    model.get_config(verbose=1)
    model.compile(loss='categorical_crossentropy', optimizer='adam')
    model.fit(prefilter_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch, show_accuracy=False, verbose=0, validation_data=(prefilter_test, Y_test))

    score = model.evaluate(prefilter_test, Y_test, verbose=0, show_accuracy=True)
    print('\nscore:', score)

    print('Loss change:', (score[0] - classical_score[0])/classical_score[0], '%')
    print('Accuracy change:', (score[1] - classical_score[1])/classical_score[1], '%')

    # check serialization
    config = autoencoder.get_config(verbose=1)
    autoencoder = model_from_config(config)

import numpy as np
import random
import theano

from keras.models import Sequential
from keras.callbacks import Callback
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.regularizers import l2
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.utils import np_utils
from keras.datasets import mnist
import keras.callbacks as cbks

from matplotlib import pyplot as plt
from matplotlib import animation

##############################
# model DrawActivations test #
##############################

print('Running DrawActivations test')

nb_classes = 10
batch_size = 128
nb_epoch = 10

max_train_samples = 512
max_test_samples = 1

np.random.seed(1337)

# the data, shuffled and split between tran and test sets
(X_train, y_train), (X_test, y_test) = mnist.load_data()

X_train = X_train.reshape(-1,1,28,28)[:max_train_samples]
X_train = X_train.astype("float32")
X_train /= 255

X_test = X_test.reshape(-1,1,28,28)[:max_test_samples]
X_test = X_test.astype("float32")
X_test /= 255

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)[:max_train_samples]

class Frames(object):
    def __init__(self, n_plots=16):
        self._n_frames = 0
        self._framedata = []
        self._titles = []
        for i in range(n_plots):
            self._framedata.append([])

    def add_frame(self, i, frame):
        self._framedata[i].append(frame)

    def set_title(self, title):
        self._titles.append(title)

class SubplotTimedAnimation(animation.TimedAnimation):

    def __init__(self, fig, frames, grid=(4, 4), interval=10, blit=False, **kwargs):
        self.n_plots = grid[0] * grid[1]
        self.axes = [fig.add_subplot(grid[0], grid[1], i + 1) for i in range(self.n_plots)]
        for axis in self.axes:
            axis.get_xaxis().set_ticks([])
            axis.get_yaxis().set_ticks([])
        self.frames = frames
        self.imgs = [self.axes[i].imshow(frames._framedata[i][0], interpolation='nearest', cmap='bone') for i in range(self.n_plots)]
        self.title = fig.suptitle('')
        super(SubplotTimedAnimation, self).__init__(fig, interval=interval, blit=blit, **kwargs)

    def _draw_frame(self, j):
        for i in range(self.n_plots):
            self.imgs[i].set_data(self.frames._framedata[i][j])
        if len(self.frames._titles) > j:
            self.title.set_text(self.frames._titles[j])
        self._drawn_artists = self.imgs

    def new_frame_seq(self):
        return iter(range(len(self.frames._framedata[0])))

    def _init_draw(self):
        for img in self.imgs:
            img.set_data([[]])

def combine_imgs(imgs, grid=(1,1)):
    n_imgs, img_h, img_w = imgs.shape
    if n_imgs != grid[0] * grid[1]:
        raise ValueError()
    combined = np.zeros((grid[0] * img_h, grid[1] * img_w))
    for i in range(grid[0]):
        for j in range(grid[1]):
            combined[img_h*i:img_h*(i+1),img_w*j:img_w*(j+1)] = imgs[grid[0] * i + j]
    return combined

class DrawActivations(Callback):
    def __init__(self, figsize):
        self.fig = plt.figure(figsize=figsize)

    def on_train_begin(self, logs={}):
        self.imgs = Frames(n_plots=5)

        layers_0_ids = np.random.choice(32, 16, replace=False)
        self.test_layer0 = theano.function([self.model.get_input()], self.model.layers[1].get_output(train=False)[0, layers_0_ids])

        layers_1_ids = np.random.choice(64, 36, replace=False)
        self.test_layer1 = theano.function([self.model.get_input()], self.model.layers[5].get_output(train=False)[0, layers_1_ids])

        self.test_layer2 = theano.function([self.model.get_input()], self.model.layers[10].get_output(train=False)[0])

    def on_epoch_begin(self, epoch, logs={}):
        self.epoch = epoch

    def on_batch_end(self, batch, logs={}):
        if batch % 5 == 0:
            self.imgs.add_frame(0, X_test[0,0])
            self.imgs.add_frame(1, combine_imgs(self.test_layer0(X_test), grid=(4, 4)))
            self.imgs.add_frame(2, combine_imgs(self.test_layer1(X_test), grid=(6, 6)))
            self.imgs.add_frame(3, self.test_layer2(X_test).reshape((16,16)))
            self.imgs.add_frame(4, self.model._predict(X_test)[0].reshape((1,10)))
            self.imgs.set_title('Epoch #%d - Batch #%d' % (self.epoch, batch))

    def on_train_end(self, logs={}):
        anim = SubplotTimedAnimation(self.fig, self.imgs, grid=(1,5), interval=10, blit=False, repeat_delay=1000)
        # anim.save('test_gif.gif', fps=15, writer='imagemagick')
        plt.show()

# model = Sequential()
# model.add(Dense(784, 50))
# model.add(Activation('relu'))
# model.add(Dense(50, 10))
# model.add(Activation('softmax'))

model = Sequential()
model.add(Convolution2D(32, 1, 3, 3, border_mode='full'))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Convolution2D(64, 32, 3, 3, border_mode='full'))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(64*8*8, 256))
model.add(Activation('relu'))
model.add(Dropout(0.5))

model.add(Dense(256, 10, W_regularizer = l2(0.1)))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

# Fit the model
draw_weights = DrawActivations(figsize=(5.4, 1.35))
model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch, verbose=1, callbacks=[draw_weights])


##########################
# model checkpoint tests #
##########################

print('Running ModelCheckpoint test')

nb_classes = 10
batch_size = 128
nb_epoch = 20

# small sample size to overfit on training data
max_train_samples = 50
max_test_samples = 1000

np.random.seed(1337) # for reproducibility

# the data, shuffled and split between tran and test sets
(X_train, y_train), (X_test, y_test) = mnist.load_data()

X_train = X_train.reshape(60000,784)[:max_train_samples]
X_test = X_test.reshape(10000,784)[:max_test_samples]
X_train = X_train.astype("float32")
X_test = X_test.astype("float32")
X_train /= 255
X_test /= 255

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)[:max_train_samples]
Y_test = np_utils.to_categorical(y_test, nb_classes)[:max_test_samples]


# Create a slightly larger network than required to test best validation save only
model = Sequential()
model.add(Dense(784, 500))
model.add(Activation('relu'))
model.add(Dense(500, 10))
model.add(Activation('softmax'))
model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

# test file location
path = "/tmp"
filename = "model_weights.hdf5"
import os
f = os.path.join(path, filename)

print("Test model checkpointer")
# only store best validation model in checkpointer
checkpointer = cbks.ModelCheckpoint(filepath=f, verbose=1, save_best_only=True)
model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch, show_accuracy=True, verbose=0, validation_data=(X_test, Y_test), callbacks =[checkpointer])

if not os.path.isfile(f):
    raise Exception("Model weights were not saved to %s" % (f))

print("Test model checkpointer without validation data")
import warnings
warnings.filterwarnings('error')
try:
    passed = False
    # this should issue a warning
    model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch, show_accuracy=True, verbose=0, callbacks =[checkpointer])
except:
    passed = True
if not passed:
    raise Exception("Modelcheckpoint tests did not pass")

print("Test model checkpointer with pattern")
filename = "model_weights.{epoch:04d}.hdf5"
f = os.path.join(path, filename)
nb_epoch = 3
checkpointer = cbks.ModelCheckpoint(f)
model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch, verbose=0, callbacks=[checkpointer])
for i in range(nb_epoch):
    if not os.path.isfile(f.format(epoch=i)):
        raise Exception("Model weights were not saved separately for each epoch")

print("Tests passed")

from __future__ import absolute_import
from __future__ import print_function
import numpy as np

from keras.utils.test_utils import get_test_data
from keras.preprocessing import sequence
from keras.optimizers import SGD, RMSprop, Adagrad
from keras.utils import np_utils
from keras.models import Sequential, Graph
from keras.layers.core import Dense, Dropout, Activation, Merge
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM, GRU
from keras.datasets import imdb
from keras.models import model_from_yaml

'''
This is essentially the IMDB test. Deserialized models should yield
the same config as the original one.
'''

max_features = 10000
maxlen = 100
batch_size = 32

(X_train, y_train), (X_test, y_test) = imdb.load_data(nb_words=max_features, test_split=0.2)

X_train = sequence.pad_sequences(X_train, maxlen=maxlen)
X_test = sequence.pad_sequences(X_test, maxlen=maxlen)

model = Sequential()
model.add(Embedding(max_features, 128))
model.add(LSTM(128, 128))
model.add(Dropout(0.5))
model.add(Dense(128, 1, W_regularizer='identity', b_constraint='maxnorm'))
model.add(Activation('sigmoid'))

model.get_config(verbose=1)

#####################################
# save model w/o parameters to yaml #
#####################################

yaml_no_params = model.to_yaml()

no_param_model = model_from_yaml(yaml_no_params)
no_param_model.get_config(verbose=1)

######################################
# save multi-branch sequential model #
######################################

seq = Sequential()
seq.add(Merge([model, model], mode='sum'))
seq.get_config(verbose=1)
merge_yaml = seq.to_yaml()
merge_model = model_from_yaml(merge_yaml)

large_model = Sequential()
large_model.add(Merge([seq,model], mode='concat'))
large_model.get_config(verbose=1)
large_model.to_yaml()

####################
# save graph model #
####################

X = np.random.random((100, 32))
X2 = np.random.random((100, 32))
y = np.random.random((100, 4))
y2 = np.random.random((100,))

(X_train, y_train), (X_test, y_test) = get_test_data(nb_train=1000, nb_test=200, input_shape=(32,),
                                                     classification=False, output_shape=(4,))

graph = Graph()

graph.add_input(name='input1', ndim=2)

graph.add_node(Dense(32, 16), name='dense1', input='input1')
graph.add_node(Dense(32, 4), name='dense2', input='input1')
graph.add_node(Dense(16, 4), name='dense3', input='dense1')

graph.add_output(name='output1', inputs=['dense2', 'dense3'], merge_mode='sum')
graph.compile('rmsprop', {'output1': 'mse'})

graph.get_config(verbose=1)

history = graph.fit({'input1': X_train, 'output1': y_train}, nb_epoch=10)
original_pred = graph.predict({'input1': X_test})

graph_yaml = graph.to_yaml()
graph.save_weights('temp.h5', overwrite=True)

reloaded_graph = model_from_yaml(graph_yaml)
reloaded_graph.load_weights('temp.h5')
reloaded_graph.get_config(verbose=1)

reloaded_graph.compile('rmsprop', {'output1': 'mse'})
new_pred = reloaded_graph.predict({'input1': X_test})

assert(np.sum(new_pred['output1'] - original_pred['output1']) == 0)

from __future__ import absolute_import
from __future__ import print_function
from keras.models import Sequential, Graph
from keras.layers.core import Layer, Activation, Dense, Flatten, Reshape, Merge
from keras.layers.convolutional import Convolution2D, MaxPooling2D
import keras.utils.layer_utils as layer_utils

print('-- Sequential model')
left = Sequential()
left.add(Convolution2D(32, 1, 3, 3, border_mode='valid'))
left.add(MaxPooling2D(pool_size=(2, 2)))
left.add(Flatten())
left.add(Dense(32 * 13 * 13, 50))
left.add(Activation('relu'))

right = Sequential()
right.add(Dense(784, 30))
right.add(Activation('relu'))

model = Sequential()
model.add(Merge([left, right], mode='concat'))

model.add(Dense(80, 10))
model.add(Activation('softmax'))

layer_utils.print_layer_shapes(model, [(1, 1, 28, 28), (1, 784)])

print('-- Graph model')
graph = Graph()
graph.add_input(name='input1', ndim=2)
graph.add_input(name='input2', ndim=4)
graph.add_node(Dense(32, 16), name='dense1', input='input1')
graph.add_node(Dense(16, 4), name='dense3', input='dense1')

graph.add_node(Convolution2D(32, 1, 3, 3), name='conv1', input='input2')
graph.add_node(Flatten(), name='flatten1', input='conv1')
graph.add_node(Dense(32 * 13 * 13, 10), name='dense4', input='flatten1')

graph.add_output(name='output1', inputs=['dense1', 'dense3'], merge_mode='sum')
graph.add_output(name='output2', inputs=['dense1', 'dense4'], merge_mode='concat')

layer_utils.print_layer_shapes(graph, {'input1': (1, 32), 'input2': (1, 1, 28, 28)})

print('Test script complete')

from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.optimizers import SGD

import sys
sys.setrecursionlimit(10000) # to be able to pickle Theano compiled functions

import pickle, numpy

def create_model():
    model = Sequential()
    model.add(Dense(256, 2048, init='uniform', activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(2048, 2048, init='uniform', activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(2048, 2048, init='uniform', activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(2048, 2048, init='uniform', activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(2048, 256, init='uniform', activation='linear'))
    return model

model = create_model()
sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='mse', optimizer=sgd)

pickle.dump(model, open('/tmp/model.pkl', 'wb'))
model.save_weights('/tmp/model_weights.hdf5')

model_loaded = create_model()
model_loaded.load_weights('/tmp/model_weights.hdf5')

for k in range(len(model.layers)):
    weights_orig = model.layers[k].get_weights()
    weights_loaded = model_loaded.layers[k].get_weights()
    for x, y in zip(weights_orig, weights_loaded):
        if numpy.any(x != y):
            raise ValueError('Loaded weights are different from pickled weights!')



from __future__ import absolute_import
from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.optimizers import SGD, Adam, RMSprop
from keras.utils import np_utils

'''
    Train a simple deep NN on the MNIST dataset.

    Get to 98.30% test accuracy after 20 epochs (there is *a lot* of margin for parameter tuning).
    2 seconds per epoch on a GRID K520 GPU.
'''

batch_size = 128
nb_classes = 10
nb_epoch = 20

# the data, shuffled and split between tran and test sets
(X_train, y_train), (X_test, y_test) = mnist.load_data()

X_train = X_train.reshape(60000, 784)
X_test = X_test.reshape(10000, 784)
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
model.add(Dense(128, input_shape=(784,)))
model.add(Activation('relu'))
model.add(Dropout(0.2))
model.add(Dense(128))
model.add(Activation('relu'))
model.add(Dropout(0.2))
model.add(Dense(10))
model.add(Activation('softmax'))

rms = RMSprop()
model.compile(loss='categorical_crossentropy', optimizer=rms)

model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch, show_accuracy=True, verbose=2, validation_data=(X_test, Y_test))
score = model.evaluate(X_test, Y_test, show_accuracy=True, verbose=0)
print('Test score:', score[0])
print('Test accuracy:', score[1])

from __future__ import absolute_import
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

'''
    This is a reproduction of the IRNN experiment
    with pixel-by-pixel sequential MNIST in
    "A Simple Way to Initialize Recurrent Networks of Rectified Linear Units "
    by Quoc V. Le, Navdeep Jaitly, Geoffrey E. Hinton

    arXiv:1504.00941v2 [cs.NE] 7 Apr 201
    http://arxiv.org/pdf/1504.00941v2.pdf

    Optimizer is replaced with RMSprop which yields more stable and steady
    improvement.

    Reaches 0.93 train/test accuracy after 900 epochs (which roughly corresponds
    to 1687500 steps in the original paper.)
'''

batch_size = 32
nb_classes = 10
nb_epochs = 200
hidden_units = 100

learning_rate = 1e-6
clip_norm = 1.0
BPTT_truncate = 28*28

# the data, shuffled and split between train and test sets
(X_train, y_train), (X_test, y_test) = mnist.load_data()

X_train = X_train.reshape(X_train.shape[0], -1, 1)
X_test = X_test.reshape(X_test.shape[0], -1, 1)
X_train = X_train.astype("float32")
X_test = X_test.astype("float32")
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
                    activation='relu', truncate_gradient=BPTT_truncate,
                    input_shape=(None, 1)))
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
model.add(LSTM(hidden_units, input_shape=(None, 1)))
model.add(Dense(nb_classes))
model.add(Activation('softmax'))
rmsprop = RMSprop(lr=learning_rate)
model.compile(loss='categorical_crossentropy', optimizer=rmsprop)

model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epochs,
          show_accuracy=True, verbose=1, validation_data=(X_test, Y_test))

scores = model.evaluate(X_test, Y_test, show_accuracy=True, verbose=0)
print('LSTM test score:', scores[0])
print('LSTM test accuracy:', scores[1])

from __future__ import absolute_import
from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.utils import np_utils

'''
    Train a simple convnet on the MNIST dataset.

    Run on GPU: THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python mnist_cnn.py

    Get to 99.25% test accuracy after 12 epochs (there is still a lot of margin for parameter tuning).
    16 seconds per epoch on a GRID K520 GPU.
'''

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
X_train = X_train.astype("float32")
X_test = X_test.astype("float32")
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
                        border_mode='full',
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

model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch, show_accuracy=True, verbose=1, validation_data=(X_test, Y_test))
score = model.evaluate(X_test, Y_test, show_accuracy=True, verbose=0)
print('Test score:', score[0])
print('Test accuracy:', score[1])

from __future__ import print_function
from keras.models import Sequential
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.datasets.data_utils import get_file
import numpy as np
import random
import sys

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

from __future__ import absolute_import
from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.preprocessing import sequence
from keras.optimizers import RMSprop
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.embeddings import Embedding
from keras.layers.convolutional import Convolution1D, MaxPooling1D
from keras.datasets import imdb

'''
    This example demonstrates the use of Convolution1D
    for text classification.

    Run on GPU: THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python imdb_cnn.py

    Get to 0.8330 test accuracy after 3 epochs. 100s/epoch on K520 GPU.
'''

# set parameters:
max_features = 5000
maxlen = 100
batch_size = 32
embedding_dims = 100
nb_filter = 250
filter_length = 3
hidden_dims = 250
nb_epoch = 3

print("Loading data...")
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

# we start off with an efficient embedding layer which maps
# our vocab indices into embedding_dims dimensions
model.add(Embedding(max_features, embedding_dims, input_length=maxlen))
model.add(Dropout(0.25))

# we add a Convolution1D, which will learn nb_filter
# word group filters of size filter_length:
model.add(Convolution1D(nb_filter=nb_filter,
                        filter_length=filter_length,
                        border_mode="valid",
                        activation="relu",
                        subsample_length=1))
# we use standard max pooling (halving the output of the previous layer):
model.add(MaxPooling1D(pool_length=2))

# We flatten the output of the conv layer, so that we can add a vanilla dense layer:
model.add(Flatten())

# We add a vanilla hidden layer:
model.add(Dense(hidden_dims))
model.add(Dropout(0.25))
model.add(Activation('relu'))

# We project onto a single unit output layer, and squash it with a sigmoid:
model.add(Dense(1))
model.add(Activation('sigmoid'))

model.compile(loss='binary_crossentropy', optimizer='rmsprop', class_mode="binary")
model.fit(X_train, y_train, batch_size=batch_size, nb_epoch=nb_epoch, show_accuracy=True, validation_data=(X_test, y_test))

from __future__ import absolute_import
from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

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
    Some configurations won't converge.

    - LSTM loss decrease patterns during training can be quite different
    from what you see with CNNs/MLPs/etc.

    GPU command:
        THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python imdb_lstm.py
'''

max_features = 20000
maxlen = 100  # cut texts after this number of words (among top max_features most common words)
batch_size = 32

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
model.add(Embedding(max_features, 128, input_length=maxlen))
model.add(LSTM(128))  # try using a GRU instead, for fun
model.add(Dropout(0.5))
model.add(Dense(1))
model.add(Activation('sigmoid'))

# try using different optimizers and different optimizer configs
model.compile(loss='binary_crossentropy', optimizer='adam', class_mode="binary")

print("Train...")
model.fit(X_train, y_train, batch_size=batch_size, nb_epoch=4, validation_data=(X_test, y_test), show_accuracy=True)
score, acc = model.evaluate(X_test, y_test, batch_size=batch_size, show_accuracy=True)
print('Test score:', score)
print('Test accuracy:', acc)

from __future__ import absolute_import
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

'''
    This demonstrates how to reach a score of 0.4890 (local validation)
    on the Kaggle Otto challenge, with a deep net using Keras.

    Compatible Python 2.7-3.4. Requires Scikit-Learn and Pandas.

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
from six.moves import cPickle
import os, re, json

from keras.preprocessing import sequence, text
from keras.optimizers import SGD, RMSprop, Adagrad
from keras.utils import np_utils, generic_utils
from keras.models import Sequential
from keras.layers.embeddings import WordContextProduct, Embedding
from six.moves import range
from six.moves import zip

max_features = 50000  # vocabulary size: top 50,000 most common words in data
skip_top = 100  # ignore top 100 most common words
nb_epoch = 1
dim_proj = 256  # embedding space dimension

save = True
load_model = False
load_tokenizer = False
train_model = True
save_dir = os.path.expanduser("~/.keras/models")
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
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
    tokenizer = cPickle.load(open(os.path.join(save_dir, tokenizer_fname), 'rb'))
else:
    print("Fit tokenizer...")
    tokenizer = text.Tokenizer(nb_words=max_features)
    tokenizer.fit_on_texts(text_generator())
    if save:
        print("Save tokenizer...")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        cPickle.dump(tokenizer, open(os.path.join(save_dir, tokenizer_fname), "wb"))

# training process
if train_model:
    if load_model:
        print('Load model...')
        model = cPickle.load(open(os.path.join(save_dir, model_load_fname), 'rb'))
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
                loss = model.train_on_batch(X, labels)
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
        cPickle.dump(model, open(os.path.join(save_dir, model_save_fname), "wb"))


print("It's test time!")

# recover the embedding weights trained with skipgram:
weights = model.layers[0].get_weights()[0]

# we no longer need this
del model

weights[:skip_top] = np.zeros((skip_top, dim_proj))
norm_weights = np_utils.normalize(weights)

word_index = tokenizer.word_index
reverse_word_index = dict([(v, k) for k, v in list(word_index.items())])


def embed_word(w):
    i = word_index.get(w)
    if (not i) or (i < skip_top) or (i >= max_features):
        return None
    return norm_weights[i]


def closest_to_point(point, nb_closest=10):
    proximities = np.dot(norm_weights, point)
    tups = list(zip(list(range(len(proximities))), proximities))
    tups.sort(key=lambda x: x[1], reverse=True)
    return [(reverse_word_index.get(t[0]), t[1]) for t in tups[:nb_closest]]


def closest_to_word(w, nb_closest=10):
    i = word_index.get(w)
    if (not i) or (i < skip_top) or (i >= max_features):
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

words = [
    "article",  # post, story, hn, read, comments
    "3",  # 6, 4, 5, 2
    "two",  # three, few, several, each
    "great",  # love, nice, working, looking
    "data",  # information, memory, database
    "money",  # company, pay, customers, spend
    "years",  # ago, year, months, hours, week, days
    "android",  # ios, release, os, mobile, beta
    "javascript",  # js, css, compiler, library, jquery, ruby
    "look",  # looks, looking
    "business",  # industry, professional, customers
    "company",  # companies, startup, founders, startups
    "after",  # before, once, until
    "own",  # personal, our, having
    "us",  # united, country, american, tech, diversity, usa, china, sv
    "using",  # javascript, js, tools (lol)
    "here",  # hn, post, comments
]

for w in words:
    res = closest_to_word(w)
    print('====', w)
    for r in res:
        print(r)

from __future__ import absolute_import
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

'''
Trains two recurrent neural networks based upon a story and a question.
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


def vectorize_stories(data):
    X = []
    Xq = []
    Y = []
    for story, query, answer in data:
        x = [word_idx[w] for w in story]
        xq = [word_idx[w] for w in query]
        y = np.zeros(vocab_size)
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

X, Xq, Y = vectorize_stories(train)
tX, tXq, tY = vectorize_stories(test)

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

from __future__ import absolute_import
from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

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
nb_epoch = 5

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
from __future__ import print_function
from keras.models import Sequential, slice_X
from keras.layers.core import Activation, TimeDistributedDense, RepeatVector
from keras.layers import recurrent
import numpy as np
from six.moves import range

"""
An implementation of sequence to sequence learning for performing addition
Input: "535+61"
Output: "596"
Padding is handled by using a repeated sentinel character (space)

By default, the JZS1 recurrent neural network is used
JZS1 was an "evolved" recurrent neural network performing well on arithmetic benchmark in:
"An Empirical Exploration of Recurrent Network Architectures"
http://jmlr.org/proceedings/papers/v37/jozefowicz15.pdf

Input may optionally be inverted, shown to increase performance in many tasks in:
"Learning to Execute"
http://arxiv.org/abs/1410.4615
and
"Sequence to Sequence Learning with Neural Networks"
http://papers.nips.cc/paper/5346-sequence-to-sequence-learning-with-neural-networks.pdf
Theoretically it introduces shorter term dependencies between source and target.

Two digits inverted:
+ One layer JZS1 (128 HN), 5k training examples = 99% train/test accuracy in 55 epochs

Three digits inverted:
+ One layer JZS1 (128 HN), 50k training examples = 99% train/test accuracy in 100 epochs

Four digits inverted:
+ One layer JZS1 (128 HN), 400k training examples = 99% train/test accuracy in 20 epochs

Five digits inverted:
+ One layer JZS1 (128 HN), 550k training examples = 99% train/test accuracy in 30 epochs

"""


class CharacterTable(object):
    """
    Given a set of characters:
    + Encode them to a one hot integer representation
    + Decode the one hot integer representation to their character output
    + Decode a vector of probabilties to their character output
    """
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
# Try replacing JZS1 with LSTM, GRU, or SimpleRNN
RNN = recurrent.JZS1
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
model.add(RNN(HIDDEN_SIZE, input_shape=(None, len(chars))))
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
    model.fit(X_train, y_train, batch_size=BATCH_SIZE, nb_epoch=1, validation_data=(X_val, y_val), show_accuracy=True)
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

from __future__ import absolute_import
from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.preprocessing import sequence
from keras.optimizers import SGD, RMSprop, Adagrad
from keras.utils import np_utils
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM, GRU, SimpleRNN
from keras.layers.convolutional import Convolution1D, MaxPooling1D
from keras.datasets import imdb

'''
    Train a recurrent convolutional network on the IMDB sentiment classification task.

    GPU command:
        THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python imdb_lstm.py

    Get to 0.8498 test accuracy after 2 epochs. 41s/epoch on K520 GPU.
'''

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
model.add(Embedding(max_features, embedding_size, input_length=maxlen))
model.add(Dropout(0.25))
model.add(Convolution1D(nb_filter=nb_filter,
                        filter_length=filter_length,
                        border_mode="valid",
                        activation="relu",
                        subsample_length=1))
model.add(MaxPooling1D(pool_length=pool_length))
model.add(LSTM(lstm_output_size))
model.add(Dense(1))
model.add(Activation('sigmoid'))

model.compile(loss='binary_crossentropy',
              optimizer='adam',
              class_mode="binary")

print("Train...")
model.fit(X_train, y_train, batch_size=batch_size, nb_epoch=nb_epoch,
          validation_data=(X_test, y_test), show_accuracy=True)
score, acc = model.evaluate(X_test, y_test, batch_size=batch_size,
                            show_accuracy=True)
print('Test score:', score)
print('Test accuracy:', acc)

from __future__ import absolute_import
from __future__ import print_function
import numpy as np
import datetime

np.random.seed(1337)  # for reproducibility

from keras.datasets import mnist
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.utils import np_utils

'''
    Transfer learning toy example:
        1- Train a simple convnet on the MNIST dataset the first 5 digits [0..4].
        2- Freeze convolutional layers and fine-tune dense layers for the classification of digits [5..9].

    Run on GPU: THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python mnist_cnn.py

    Get to 99.8% test accuracy after 5 epochs for the first five digits classifier
    and 99.2% for the last five digits after transfer + fine-tuning.
'''

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
    X_train = X_train.astype("float32")
    X_test = X_test.astype("float32")
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
    model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch, show_accuracy=True, verbose=1,
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
                  border_mode='full',
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
train_model(model, (X_train_lt5, y_train_lt5), (X_test_lt5, y_test_lt5), nb_classes)

# freeze feature layers and rebuild model
for l in feature_layers:
    l.trainable = False

# transfer: train dense layers for new classification task [5..9]
train_model(model, (X_train_gte5, y_train_gte5), (X_test_gte5, y_test_gte5), nb_classes)

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

# input image dimensions
img_rows, img_cols = 32, 32
# the CIFAR10 images are RGB
img_channels = 3

# the data, shuffled and split between tran and test sets
(X_train, y_train), (X_test, y_test) = cifar10.load_data()
print('X_train shape:', X_train.shape)
print(X_train.shape[0], 'train samples')
print(X_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)

model = Sequential()

model.add(Convolution2D(32, 3, 3, border_mode='full',
                        input_shape=(img_channels, img_rows, img_cols)))
model.add(Activation('relu'))
model.add(Convolution2D(32, 3, 3))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Convolution2D(64, 3, 3, border_mode='full'))
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

X_train = X_train.astype("float32")
X_test = X_test.astype("float32")
X_train /= 255
X_test /= 255

if not data_augmentation:
    print("Not using data augmentation or normalization")
    model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch)
    score = model.evaluate(X_test, Y_test, batch_size=batch_size)
    print('Test score:', score)

else:
    print("Using real time data augmentation")

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
        print("Training...")
        # batch train with realtime data augmentation
        progbar = generic_utils.Progbar(X_train.shape[0])
        for X_batch, Y_batch in datagen.flow(X_train, Y_train):
            loss = model.train_on_batch(X_batch, Y_batch)
            progbar.add(X_batch.shape[0], values=[("train loss", loss)])

        print("Testing...")
        # test time!
        progbar = generic_utils.Progbar(X_test.shape[0])
        for X_batch, Y_batch in datagen.flow(X_test, Y_test):
            score = model.test_on_batch(X_batch, Y_batch)
            progbar.add(X_batch.shape[0], values=[("test loss", score)])

