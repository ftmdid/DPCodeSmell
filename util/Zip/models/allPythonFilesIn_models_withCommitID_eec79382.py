import numpy as np

import sklearn.preprocessing as prep
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data

from autoencoder.autoencoder_models.Autoencoder import Autoencoder

mnist = input_data.read_data_sets('MNIST_data', one_hot = True)

def standard_scale(X_train, X_test):
    preprocessor = prep.StandardScaler().fit(X_train)
    X_train = preprocessor.transform(X_train)
    X_test = preprocessor.transform(X_test)
    return X_train, X_test

def get_random_block_from_data(data, batch_size):
    start_index = np.random.randint(0, len(data) - batch_size)
    return data[start_index:(start_index + batch_size)]

X_train, X_test = standard_scale(mnist.train.images, mnist.test.images)

n_samples = int(mnist.train.num_examples)
training_epochs = 20
batch_size = 128
display_step = 1

autoencoder = Autoencoder(n_input = 784,
                          n_hidden = 200,
                          transfer_function = tf.nn.softplus,
                          optimizer = tf.train.AdamOptimizer(learning_rate = 0.001))

for epoch in range(training_epochs):
    avg_cost = 0.
    total_batch = int(n_samples / batch_size)
    # Loop over all batches
    for i in range(total_batch):
        batch_xs = get_random_block_from_data(X_train, batch_size)

        # Fit training using batch data
        cost = autoencoder.partial_fit(batch_xs)
        # Compute average loss
        avg_cost += cost / n_samples * batch_size

    # Display logs per epoch step
    if epoch % display_step == 0:
        print "Epoch:", '%04d' % (epoch + 1), \
            "cost=", "{:.9f}".format(avg_cost)

print "Total cost: " + str(autoencoder.calc_total_cost(X_test))


import numpy as np
import tensorflow as tf

def xavier_init(fan_in, fan_out, constant = 1):
    low = -constant * np.sqrt(6.0 / (fan_in + fan_out))
    high = constant * np.sqrt(6.0 / (fan_in + fan_out))
    return tf.random_uniform((fan_in, fan_out),
                             minval = low, maxval = high,
                             dtype = tf.float32)

import numpy as np

import sklearn.preprocessing as prep
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data

from autoencoder.autoencoder_models.DenoisingAutoencoder import AdditiveGaussianNoiseAutoencoder

mnist = input_data.read_data_sets('MNIST_data', one_hot = True)

def standard_scale(X_train, X_test):
    preprocessor = prep.StandardScaler().fit(X_train)
    X_train = preprocessor.transform(X_train)
    X_test = preprocessor.transform(X_test)
    return X_train, X_test

def get_random_block_from_data(data, batch_size):
    start_index = np.random.randint(0, len(data) - batch_size)
    return data[start_index:(start_index + batch_size)]

X_train, X_test = standard_scale(mnist.train.images, mnist.test.images)

n_samples = int(mnist.train.num_examples)
training_epochs = 20
batch_size = 128
display_step = 1

autoencoder = AdditiveGaussianNoiseAutoencoder(n_input = 784,
                                               n_hidden = 200,
                                               transfer_function = tf.nn.softplus,
                                               optimizer = tf.train.AdamOptimizer(learning_rate = 0.001),
                                               scale = 0.01)

for epoch in range(training_epochs):
    avg_cost = 0.
    total_batch = int(n_samples / batch_size)
    # Loop over all batches
    for i in range(total_batch):
        batch_xs = get_random_block_from_data(X_train, batch_size)

        # Fit training using batch data
        cost = autoencoder.partial_fit(batch_xs)
        # Compute average loss
        avg_cost += cost / n_samples * batch_size

    # Display logs per epoch step
    if epoch % display_step == 0:
        print "Epoch:", '%04d' % (epoch + 1), \
            "cost=", "{:.9f}".format(avg_cost)

print "Total cost: " + str(autoencoder.calc_total_cost(X_test))

import numpy as np

import sklearn.preprocessing as prep
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data

from autoencoder.autoencoder_models.VariationalAutoencoder import VariationalAutoencoder

mnist = input_data.read_data_sets('MNIST_data', one_hot = True)



def min_max_scale(X_train, X_test):
    preprocessor = prep.MinMaxScaler().fit(X_train)
    X_train = preprocessor.transform(X_train)
    X_test = preprocessor.transform(X_test)
    return X_train, X_test


def get_random_block_from_data(data, batch_size):
    start_index = np.random.randint(0, len(data) - batch_size)
    return data[start_index:(start_index + batch_size)]


X_train, X_test = min_max_scale(mnist.train.images, mnist.test.images)

n_samples = int(mnist.train.num_examples)
training_epochs = 20
batch_size = 128
display_step = 1

autoencoder = VariationalAutoencoder(n_input = 784,
                                     n_hidden = 200,
                                     optimizer = tf.train.AdamOptimizer(learning_rate = 0.001))

for epoch in range(training_epochs):
    avg_cost = 0.
    total_batch = int(n_samples / batch_size)
    # Loop over all batches
    for i in range(total_batch):
        batch_xs = get_random_block_from_data(X_train, batch_size)

        # Fit training using batch data
        cost = autoencoder.partial_fit(batch_xs)
        # Compute average loss
        avg_cost += cost / n_samples * batch_size

    # Display logs per epoch step
    if epoch % display_step == 0:
        print "Epoch:", '%04d' % (epoch + 1), \
            "cost=", "{:.9f}".format(avg_cost)

print "Total cost: " + str(autoencoder.calc_total_cost(X_test))

import numpy as np

import sklearn.preprocessing as prep
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data

from autoencoder.autoencoder_models.DenoisingAutoencoder import MaskingNoiseAutoencoder

mnist = input_data.read_data_sets('MNIST_data', one_hot = True)

def standard_scale(X_train, X_test):
    preprocessor = prep.StandardScaler().fit(X_train)
    X_train = preprocessor.transform(X_train)
    X_test = preprocessor.transform(X_test)
    return X_train, X_test

def get_random_block_from_data(data, batch_size):
    start_index = np.random.randint(0, len(data) - batch_size)
    return data[start_index:(start_index + batch_size)]

X_train, X_test = standard_scale(mnist.train.images, mnist.test.images)


n_samples = int(mnist.train.num_examples)
training_epochs = 100
batch_size = 128
display_step = 1

autoencoder = MaskingNoiseAutoencoder(n_input = 784,
                                      n_hidden = 200,
                                      transfer_function = tf.nn.softplus,
                                      optimizer = tf.train.AdamOptimizer(learning_rate = 0.001),
                                      dropout_probability = 0.95)

for epoch in range(training_epochs):
    avg_cost = 0.
    total_batch = int(n_samples / batch_size)
    for i in range(total_batch):
        batch_xs = get_random_block_from_data(X_train, batch_size)

        cost = autoencoder.partial_fit(batch_xs)

        avg_cost += cost / n_samples * batch_size

    if epoch % display_step == 0:
        print "Epoch:", '%04d' % (epoch + 1), \
            "cost=", "{:.9f}".format(avg_cost)

print "Total cost: " + str(autoencoder.calc_total_cost(X_test))

import tensorflow as tf
import numpy as np
import autoencoder.Utils

class VariationalAutoencoder(object):

    def __init__(self, n_input, n_hidden, optimizer = tf.train.AdamOptimizer()):
        self.n_input = n_input
        self.n_hidden = n_hidden

        network_weights = self._initialize_weights()
        self.weights = network_weights

        # model
        self.x = tf.placeholder(tf.float32, [None, self.n_input])
        self.z_mean = tf.add(tf.matmul(self.x, self.weights['w1']), self.weights['b1'])
        self.z_log_sigma_sq = tf.add(tf.matmul(self.x, self.weights['log_sigma_w1']), self.weights['log_sigma_b1'])

        # sample from gaussian distribution
        eps = tf.random_normal(tf.pack([tf.shape(self.x)[0], self.n_hidden]), 0, 1, dtype = tf.float32)
        self.z = tf.add(self.z_mean, tf.mul(tf.sqrt(tf.exp(self.z_log_sigma_sq)), eps))

        self.reconstruction = tf.add(tf.matmul(self.z, self.weights['w2']), self.weights['b2'])

        # cost
        reconstr_loss = 0.5 * tf.reduce_sum(tf.pow(tf.sub(self.reconstruction, self.x), 2.0))
        latent_loss = -0.5 * tf.reduce_sum(1 + self.z_log_sigma_sq
                                           - tf.square(self.z_mean)
                                           - tf.exp(self.z_log_sigma_sq), 1)
        self.cost = tf.reduce_mean(reconstr_loss + latent_loss)
        self.optimizer = optimizer.minimize(self.cost)

        init = tf.initialize_all_variables()
        self.sess = tf.Session()
        self.sess.run(init)

    def _initialize_weights(self):
        all_weights = dict()
        all_weights['w1'] = tf.Variable(autoencoder.Utils.xavier_init(self.n_input, self.n_hidden))
        all_weights['log_sigma_w1'] = tf.Variable(autoencoder.Utils.xavier_init(self.n_input, self.n_hidden))
        all_weights['b1'] = tf.Variable(tf.zeros([self.n_hidden], dtype=tf.float32))
        all_weights['log_sigma_b1'] = tf.Variable(tf.zeros([self.n_hidden], dtype=tf.float32))
        all_weights['w2'] = tf.Variable(tf.zeros([self.n_hidden, self.n_input], dtype=tf.float32))
        all_weights['b2'] = tf.Variable(tf.zeros([self.n_input], dtype=tf.float32))
        return all_weights

    def partial_fit(self, X):
        cost, opt = self.sess.run((self.cost, self.optimizer), feed_dict={self.x: X})
        return cost

    def calc_total_cost(self, X):
        return self.sess.run(self.cost, feed_dict = {self.x: X})

    def transform(self, X):
        return self.sess.run(self.z_mean, feed_dict={self.x: X})

    def generate(self, hidden = None):
        if hidden is None:
            hidden = np.random.normal(size=self.weights["b1"])
        return self.sess.run(self.reconstruction, feed_dict={self.z_mean: hidden})

    def reconstruct(self, X):
        return self.sess.run(self.reconstruction, feed_dict={self.x: X})

    def getWeights(self):
        return self.sess.run(self.weights['w1'])

    def getBiases(self):
        return self.sess.run(self.weights['b1'])



import tensorflow as tf
import numpy as np
import autoencoder.Utils

class Autoencoder(object):

    def __init__(self, n_input, n_hidden, transfer_function=tf.nn.softplus, optimizer = tf.train.AdamOptimizer()):
        self.n_input = n_input
        self.n_hidden = n_hidden
        self.transfer = transfer_function

        network_weights = self._initialize_weights()
        self.weights = network_weights

        # model
        self.x = tf.placeholder(tf.float32, [None, self.n_input])
        self.hidden = self.transfer(tf.add(tf.matmul(self.x, self.weights['w1']), self.weights['b1']))
        self.reconstruction = tf.add(tf.matmul(self.hidden, self.weights['w2']), self.weights['b2'])

        # cost
        self.cost = 0.5 * tf.reduce_sum(tf.pow(tf.sub(self.reconstruction, self.x), 2.0))
        self.optimizer = optimizer.minimize(self.cost)

        init = tf.initialize_all_variables()
        self.sess = tf.Session()
        self.sess.run(init)


    def _initialize_weights(self):
        all_weights = dict()
        all_weights['w1'] = tf.Variable(autoencoder.Utils.xavier_init(self.n_input, self.n_hidden))
        all_weights['b1'] = tf.Variable(tf.zeros([self.n_hidden], dtype=tf.float32))
        all_weights['w2'] = tf.Variable(tf.zeros([self.n_hidden, self.n_input], dtype=tf.float32))
        all_weights['b2'] = tf.Variable(tf.zeros([self.n_input], dtype=tf.float32))
        return all_weights

    def partial_fit(self, X):
        cost, opt = self.sess.run((self.cost, self.optimizer), feed_dict={self.x: X})
        return cost

    def calc_total_cost(self, X):
        return self.sess.run(self.cost, feed_dict = {self.x: X})

    def transform(self, X):
        return self.sess.run(self.hidden, feed_dict={self.x: X})

    def generate(self, hidden = None):
        if hidden is None:
            hidden = np.random.normal(size=self.weights["b1"])
        return self.sess.run(self.reconstruction, feed_dict={self.hidden: hidden})

    def reconstruct(self, X):
        return self.sess.run(self.reconstruction, feed_dict={self.x: X})

    def getWeights(self):
        return self.sess.run(self.weights['w1'])

    def getBiases(self):
        return self.sess.run(self.weights['b1'])


import tensorflow as tf
import numpy as np
import autoencoder.Utils


class AdditiveGaussianNoiseAutoencoder(object):
    def __init__(self, n_input, n_hidden, transfer_function = tf.nn.softplus, optimizer = tf.train.AdamOptimizer(),
                 scale = 0.1):
        self.n_input = n_input
        self.n_hidden = n_hidden
        self.transfer = transfer_function
        self.scale = tf.placeholder(tf.float32)
        self.training_scale = scale
        network_weights = self._initialize_weights()
        self.weights = network_weights

        # model
        self.x = tf.placeholder(tf.float32, [None, self.n_input])
        self.hidden = self.transfer(tf.add(tf.matmul(self.x + scale * tf.random_normal((n_input,)),
                self.weights['w1']),
                self.weights['b1']))
        self.reconstruction = tf.add(tf.matmul(self.hidden, self.weights['w2']), self.weights['b2'])

        # cost
        self.cost = 0.5 * tf.reduce_sum(tf.pow(tf.sub(self.reconstruction, self.x), 2.0))
        self.optimizer = optimizer.minimize(self.cost)

        init = tf.initialize_all_variables()
        self.sess = tf.Session()
        self.sess.run(init)

    def _initialize_weights(self):
        all_weights = dict()
        all_weights['w1'] = tf.Variable(autoencoder.Utils.xavier_init(self.n_input, self.n_hidden))
        all_weights['b1'] = tf.Variable(tf.zeros([self.n_hidden], dtype = tf.float32))
        all_weights['w2'] = tf.Variable(tf.zeros([self.n_hidden, self.n_input], dtype = tf.float32))
        all_weights['b2'] = tf.Variable(tf.zeros([self.n_input], dtype = tf.float32))
        return all_weights

    def partial_fit(self, X):
        cost, opt = self.sess.run((self.cost, self.optimizer), feed_dict = {self.x: X,
                                                                            self.scale: self.training_scale
                                                                            })
        return cost

    def calc_total_cost(self, X):
        return self.sess.run(self.cost, feed_dict = {self.x: X,
                                                     self.scale: self.training_scale
                                                     })

    def transform(self, X):
        return self.sess.run(self.hidden, feed_dict = {self.x: X,
                                                       self.scale: self.training_scale
                                                       })

    def generate(self, hidden = None):
        if hidden is None:
            hidden = np.random.normal(size = self.weights["b1"])
        return self.sess.run(self.reconstruction, feed_dict = {self.hidden: hidden})

    def reconstruct(self, X):
        return self.sess.run(self.reconstruction, feed_dict = {self.x: X,
                                                               self.scale: self.training_scale
                                                               })

    def getWeights(self):
        return self.sess.run(self.weights['w1'])

    def getBiases(self):
        return self.sess.run(self.weights['b1'])


class MaskingNoiseAutoencoder(object):
    def __init__(self, n_input, n_hidden, transfer_function = tf.nn.softplus, optimizer = tf.train.AdamOptimizer(),
                 dropout_probability = 0.95):
        self.n_input = n_input
        self.n_hidden = n_hidden
        self.transfer = transfer_function
        self.dropout_probability = dropout_probability
        self.keep_prob = tf.placeholder(tf.float32)

        network_weights = self._initialize_weights()
        self.weights = network_weights

        # model
        self.x = tf.placeholder(tf.float32, [None, self.n_input])
        self.hidden = self.transfer(tf.add(tf.matmul(tf.nn.dropout(self.x, self.keep_prob), self.weights['w1']),
                                           self.weights['b1']))
        self.reconstruction = tf.add(tf.matmul(self.hidden, self.weights['w2']), self.weights['b2'])

        # cost
        self.cost = 0.5 * tf.reduce_sum(tf.pow(tf.sub(self.reconstruction, self.x), 2.0))
        self.optimizer = optimizer.minimize(self.cost)

        init = tf.initialize_all_variables()
        self.sess = tf.Session()
        self.sess.run(init)

    def _initialize_weights(self):
        all_weights = dict()
        all_weights['w1'] = tf.Variable(autoencoder.Utils.xavier_init(self.n_input, self.n_hidden))
        all_weights['b1'] = tf.Variable(tf.zeros([self.n_hidden], dtype = tf.float32))
        all_weights['w2'] = tf.Variable(tf.zeros([self.n_hidden, self.n_input], dtype = tf.float32))
        all_weights['b2'] = tf.Variable(tf.zeros([self.n_input], dtype = tf.float32))
        return all_weights

    def partial_fit(self, X):
        cost, opt = self.sess.run((self.cost, self.optimizer),
                                  feed_dict = {self.x: X, self.keep_prob: self.dropout_probability})
        return cost

    def calc_total_cost(self, X):
        return self.sess.run(self.cost, feed_dict = {self.x: X, self.keep_prob: 1.0})

    def transform(self, X):
        return self.sess.run(self.hidden, feed_dict = {self.x: X, self.keep_prob: 1.0})

    def generate(self, hidden = None):
        if hidden is None:
            hidden = np.random.normal(size = self.weights["b1"])
        return self.sess.run(self.reconstruction, feed_dict = {self.hidden: hidden})

    def reconstruct(self, X):
        return self.sess.run(self.reconstruction, feed_dict = {self.x: X, self.keep_prob: 1.0})

    def getWeights(self):
        return self.sess.run(self.weights['w1'])

    def getBiases(self):
        return self.sess.run(self.weights['b1'])

#!/usr/bin/env python
#
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Submatrix-wise Vector Embedding Learner.

Implementation of SwiVel algorithm described at:
http://arxiv.org/abs/1602.02215

This program expects an input directory that contains the following files.

  row_vocab.txt, col_vocab.txt

    The row an column vocabulary files.  Each file should contain one token per
    line; these will be used to generate a tab-separate file containing the
    trained embeddings.

  row_sums.txt, col_sum.txt

    The matrix row and column marginal sums.  Each file should contain one
    decimal floating point number per line which corresponds to the marginal
    count of the matrix for that row or column.

  shards.recs

    A file containing the sub-matrix shards, stored as TFRecords.  Each shard is
    expected to be a serialzed tf.Example protocol buffer with the following
    properties:

      global_row: the global row indicies contained in the shard
      global_col: the global column indicies contained in the shard
      sparse_local_row, sparse_local_col, sparse_value: three parallel arrays
      that are a sparse representation of the submatrix counts.

It will generate embeddings, training from the input directory for the specified
number of epochs.  When complete, it will output the trained vectors to a
tab-separated file that contains one line per embedding.  Row and column
embeddings are stored in separate files.

"""

import argparse
import glob
import math
import os
import sys
import time
import threading

import numpy as np
import tensorflow as tf

flags = tf.app.flags

flags.DEFINE_string('input_base_path', '/tmp/swivel_data',
                    'Directory containing input shards, vocabularies, '
                    'and marginals.')
flags.DEFINE_string('output_base_path', '/tmp/swivel_data',
                    'Path where to write the trained embeddings.')
flags.DEFINE_integer('embedding_size', 300, 'Size of the embeddings')
flags.DEFINE_boolean('trainable_bias', False, 'Biases are trainable')
flags.DEFINE_integer('submatrix_rows', 4096, 'Rows in each training submatrix. '
                     'This must match the training data.')
flags.DEFINE_integer('submatrix_cols', 4096, 'Rows in each training submatrix. '
                     'This must match the training data.')
flags.DEFINE_float('loss_multiplier', 1.0 / 4096,
                   'constant multiplier on loss.')
flags.DEFINE_float('confidence_exponent', 0.5,
                   'Exponent for l2 confidence function')
flags.DEFINE_float('confidence_scale', 0.25, 'Scale for l2 confidence function')
flags.DEFINE_float('confidence_base', 0.1, 'Base for l2 confidence function')
flags.DEFINE_float('learning_rate', 1.0, 'Initial learning rate')
flags.DEFINE_integer('num_concurrent_steps', 2,
                     'Number of threads to train with')
flags.DEFINE_float('num_epochs', 40, 'Number epochs to train for')
flags.DEFINE_float('per_process_gpu_memory_fraction', 0.25,
                   'Fraction of GPU memory to use')

FLAGS = flags.FLAGS


def embeddings_with_init(vocab_size, embedding_dim, name):
  """Creates and initializes the embedding tensors."""
  return tf.get_variable(name=name,
                         shape=[vocab_size, embedding_dim],
                         initializer=tf.random_normal_initializer(
                             stddev=math.sqrt(1.0 / embedding_dim)))


def count_matrix_input(filenames, submatrix_rows, submatrix_cols):
  """Reads submatrix shards from disk."""
  filename_queue = tf.train.string_input_producer(filenames)
  reader = tf.WholeFileReader()
  _, serialized_example = reader.read(filename_queue)
  features = tf.parse_single_example(
      serialized_example,
      features={
          'global_row': tf.FixedLenFeature([submatrix_rows], dtype=tf.int64),
          'global_col': tf.FixedLenFeature([submatrix_cols], dtype=tf.int64),
          'sparse_local_row': tf.VarLenFeature(dtype=tf.int64),
          'sparse_local_col': tf.VarLenFeature(dtype=tf.int64),
          'sparse_value': tf.VarLenFeature(dtype=tf.float32)
      })

  global_row = features['global_row']
  global_col = features['global_col']

  sparse_local_row = features['sparse_local_row'].values
  sparse_local_col = features['sparse_local_col'].values
  sparse_count = features['sparse_value'].values

  sparse_indices = tf.concat(1, [tf.expand_dims(sparse_local_row, 1),
                                 tf.expand_dims(sparse_local_col, 1)])
  count = tf.sparse_to_dense(sparse_indices, [submatrix_rows, submatrix_cols],
                             sparse_count)

  queued_global_row, queued_global_col, queued_count = tf.train.batch(
      [global_row, global_col, count],
      batch_size=1,
      num_threads=4,
      capacity=32)

  queued_global_row = tf.reshape(queued_global_row, [submatrix_rows])
  queued_global_col = tf.reshape(queued_global_col, [submatrix_cols])
  queued_count = tf.reshape(queued_count, [submatrix_rows, submatrix_cols])

  return queued_global_row, queued_global_col, queued_count


def read_marginals_file(filename):
  """Reads text file with one number per line to an array."""
  with open(filename) as lines:
    return [float(line) for line in lines]


def write_embedding_tensor_to_disk(vocab_path, output_path, sess, embedding):
  """Writes tensor to output_path as tsv"""
  # Fetch the embedding values from the model
  embeddings = sess.run(embedding)

  with open(output_path, 'w') as out_f:
    with open(vocab_path) as vocab_f:
      for index, word in enumerate(vocab_f):
        word = word.strip()
        embedding = embeddings[index]
        out_f.write(word + '\t' + '\t'.join([str(x) for x in embedding]) + '\n')


def write_embeddings_to_disk(config, model, sess):
  """Writes row and column embeddings disk"""
  # Row Embedding
  row_vocab_path = config.input_base_path + '/row_vocab.txt'
  row_embedding_output_path = config.output_base_path + '/row_embedding.tsv'
  print 'Writing row embeddings to:', row_embedding_output_path
  write_embedding_tensor_to_disk(row_vocab_path, row_embedding_output_path,
                                 sess, model.row_embedding)

  # Column Embedding
  col_vocab_path = config.input_base_path + '/col_vocab.txt'
  col_embedding_output_path = config.output_base_path + '/col_embedding.tsv'
  print 'Writing column embeddings to:', col_embedding_output_path
  write_embedding_tensor_to_disk(col_vocab_path, col_embedding_output_path,
                                 sess, model.col_embedding)


class SwivelModel(object):
  """Small class to gather needed pieces from a Graph being built."""

  def __init__(self, config):
    """Construct graph for dmc."""
    self._config = config

    # Create paths to input data files
    print 'Reading model from:', config.input_base_path
    count_matrix_files = glob.glob(config.input_base_path + '/shard-*.pb')
    row_sums_path = config.input_base_path + '/row_sums.txt'
    col_sums_path = config.input_base_path + '/col_sums.txt'

    # Read marginals
    row_sums = read_marginals_file(row_sums_path)
    col_sums = read_marginals_file(col_sums_path)

    self.n_rows = len(row_sums)
    self.n_cols = len(col_sums)
    print 'Matrix dim: (%d,%d) SubMatrix dim: (%d,%d) ' % (
        self.n_rows, self.n_cols, config.submatrix_rows, config.submatrix_cols)
    self.n_submatrices = (self.n_rows * self.n_cols /
                          (config.submatrix_rows * config.submatrix_cols))
    print 'n_submatrices: %d' % (self.n_submatrices)

    # ===== CREATE VARIABLES ======

    with tf.device('/cpu:0'):
      # embeddings
      self.row_embedding = embeddings_with_init(
          embedding_dim=config.embedding_size,
          vocab_size=self.n_rows,
          name='row_embedding')
      self.col_embedding = embeddings_with_init(
          embedding_dim=config.embedding_size,
          vocab_size=self.n_cols,
          name='col_embedding')
      tf.histogram_summary('row_emb', self.row_embedding)
      tf.histogram_summary('col_emb', self.col_embedding)

      matrix_log_sum = math.log(np.sum(row_sums) + 1)
      row_bias_init = [math.log(x + 1) for x in row_sums]
      col_bias_init = [math.log(x + 1) for x in col_sums]
      self.row_bias = tf.Variable(row_bias_init,
                                  trainable=config.trainable_bias)
      self.col_bias = tf.Variable(col_bias_init,
                                  trainable=config.trainable_bias)
      tf.histogram_summary('row_bias', self.row_bias)
      tf.histogram_summary('col_bias', self.col_bias)

    # ===== CREATE GRAPH =====

    # Get input
    with tf.device('/cpu:0'):
      global_row, global_col, count = count_matrix_input(
          count_matrix_files, config.submatrix_rows, config.submatrix_cols)

      # Fetch embeddings.
      selected_row_embedding = tf.nn.embedding_lookup(self.row_embedding,
                                                      global_row)
      selected_col_embedding = tf.nn.embedding_lookup(self.col_embedding,
                                                      global_col)

      # Fetch biases.
      selected_row_bias = tf.nn.embedding_lookup([self.row_bias], global_row)
      selected_col_bias = tf.nn.embedding_lookup([self.col_bias], global_col)

    # Multiply the row and column embeddings to generate predictions.
    predictions = tf.matmul(
        selected_row_embedding, selected_col_embedding, transpose_b=True)

    # These binary masks separate zero from non-zero values.
    count_is_nonzero = tf.to_float(tf.cast(count, tf.bool))
    count_is_zero = 1 - tf.to_float(tf.cast(count, tf.bool))

    objectives = count_is_nonzero * tf.log(count + 1e-30)
    objectives -= tf.reshape(selected_row_bias, [config.submatrix_rows, 1])
    objectives -= selected_col_bias
    objectives += matrix_log_sum

    err = predictions - objectives

    # The confidence function scales the L2 loss based on the raw co-occurrence
    # count.
    l2_confidence = (config.confidence_base + config.confidence_scale * tf.pow(
        count, config.confidence_exponent))

    l2_loss = config.loss_multiplier * tf.reduce_sum(
        0.5 * l2_confidence * err * err * count_is_nonzero)

    sigmoid_loss = config.loss_multiplier * tf.reduce_sum(
        tf.nn.softplus(err) * count_is_zero)

    self.loss = l2_loss + sigmoid_loss

    tf.scalar_summary("l2_loss", l2_loss)
    tf.scalar_summary("sigmoid_loss", sigmoid_loss)
    tf.scalar_summary("loss", self.loss)

    # Add optimizer.
    self.global_step = tf.Variable(0, name='global_step')
    opt = tf.train.AdagradOptimizer(config.learning_rate)
    self.train_op = opt.minimize(self.loss, global_step=self.global_step)
    self.saver = tf.train.Saver(sharded=True)


def main(_):
  # Create the output path.  If this fails, it really ought to fail
  # now. :)
  if not os.path.isdir(FLAGS.output_base_path):
    os.makedirs(FLAGS.output_base_path)

  # Create and run model
  with tf.Graph().as_default():
    model = SwivelModel(FLAGS)

    # Create a session for running Ops on the Graph.
    gpu_options = tf.GPUOptions(
        per_process_gpu_memory_fraction=FLAGS.per_process_gpu_memory_fraction)
    sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))

    # Run the Op to initialize the variables.
    sess.run(tf.initialize_all_variables())

    # Start feeding input
    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=sess, coord=coord)

    # Calculate how many steps each thread should run
    n_total_steps = int(FLAGS.num_epochs * model.n_rows * model.n_cols) / (
        FLAGS.submatrix_rows * FLAGS.submatrix_cols)
    n_steps_per_thread = n_total_steps / FLAGS.num_concurrent_steps
    n_submatrices_to_train = model.n_submatrices * FLAGS.num_epochs
    t0 = [time.time()]

    def TrainingFn():
      for _ in range(n_steps_per_thread):
        _, global_step = sess.run([model.train_op, model.global_step])
        n_steps_between_status_updates = 100
        if (global_step % n_steps_between_status_updates) == 0:
          elapsed = float(time.time() - t0[0])
          print '%d/%d submatrices trained (%.1f%%), %.1f submatrices/sec' % (
              global_step, n_submatrices_to_train,
              100.0 * global_step / n_submatrices_to_train,
              n_steps_between_status_updates / elapsed)
          t0[0] = time.time()

    # Start training threads
    train_threads = []
    for _ in range(FLAGS.num_concurrent_steps):
      t = threading.Thread(target=TrainingFn)
      train_threads.append(t)
      t.start()

    # Wait for threads to finish.
    for t in train_threads:
      t.join()

    coord.request_stop()
    coord.join(threads)

    # Write out vectors
    write_embeddings_to_disk(FLAGS, model, sess)

    #Shutdown
    sess.close()


if __name__ == '__main__':
  tf.app.run()

#!/usr/bin/env python
#
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Prepare a corpus for processing by swivel.

Creates a sharded word co-occurrence matrix from a text file input corpus.

Usage:

  prep.py --output_dir <output-dir> --input <text-file>

Options:

  --input <filename>
      The input text.

  --output_dir <directory>
      Specifies the output directory where the various Swivel data
      files should be placed.

  --shard_size <int>
      Specifies the shard size; default 4096.

  --min_count <int>
      Specifies the minimum number of times a word should appear
      to be included in the vocabulary; default 5.

  --max_vocab <int>
      Specifies the maximum vocabulary size; default shard size
      times 1024.

  --vocab <filename>
      Use the specified unigram vocabulary instead of generating
      it from the corpus.

  --window_size <int>
      Specifies the window size for computing co-occurrence stats;
      default 10.

  --bufsz <int>
      The number of co-occurrences that are buffered; default 16M.

"""

import itertools
import math
import os
import struct
import sys

import tensorflow as tf

flags = tf.app.flags

flags.DEFINE_string('input', '', 'The input text.')
flags.DEFINE_string('output_dir', '/tmp/swivel_data',
                    'Output directory for Swivel data')
flags.DEFINE_integer('shard_size', 4096, 'The size for each shard')
flags.DEFINE_integer('min_count', 5,
                     'The minimum number of times a word should occur to be '
                     'included in the vocabulary')
flags.DEFINE_integer('max_vocab', 4096 * 64, 'The maximum vocabulary size')
flags.DEFINE_string('vocab', '', 'Vocabulary to use instead of generating one')
flags.DEFINE_integer('window_size', 10, 'The window size')
flags.DEFINE_integer('bufsz', 16 * 1024 * 1024,
                     'The number of co-occurrences to buffer')

FLAGS = flags.FLAGS

shard_cooc_fmt = struct.Struct('iif')


def words(line):
  """Splits a line of text into tokens."""
  return line.strip().split()


def create_vocabulary(lines):
  """Reads text lines and generates a vocabulary."""
  lines.seek(0, os.SEEK_END)
  nbytes = lines.tell()
  lines.seek(0, os.SEEK_SET)

  vocab = {}
  for lineno, line in enumerate(lines, start=1):
    for word in words(line):
      vocab.setdefault(word, 0)
      vocab[word] += 1

    if lineno % 100000 == 0:
      pos = lines.tell()
      sys.stdout.write('\rComputing vocabulary: %0.1f%% (%d/%d)...' % (
          100.0 * pos / nbytes, pos, nbytes))
      sys.stdout.flush()

  sys.stdout.write('\n')

  vocab = [(tok, n) for tok, n in vocab.iteritems() if n >= FLAGS.min_count]
  vocab.sort(key=lambda kv: (-kv[1], kv[0]))

  num_words = max(len(vocab), FLAGS.shard_size)
  num_words = min(len(vocab), FLAGS.max_vocab)
  if num_words % FLAGS.shard_size != 0:
    num_words -= num_words % FLAGS.shard_size

  if not num_words:
    raise Exception('empty vocabulary')

  print 'vocabulary contains %d tokens' % num_words

  vocab = vocab[:num_words]
  return [tok for tok, n in vocab]


def write_vocab_and_sums(vocab, sums, vocab_filename, sums_filename):
  """Writes vocabulary and marginal sum files."""
  with open(os.path.join(FLAGS.output_dir, vocab_filename), 'w') as vocab_out:
    with open(os.path.join(FLAGS.output_dir, sums_filename), 'w') as sums_out:
      for tok, cnt in itertools.izip(vocab, sums):
        print >> vocab_out, tok
        print >> sums_out, cnt


def compute_coocs(lines, vocab):
  """Compute the co-occurrence statistics from the text.

  This generates a temporary file for each shard that contains the intermediate
  counts from the shard: these counts must be subsequently sorted and collated.

  """
  word_to_id = {tok: idx for idx, tok in enumerate(vocab)}

  lines.seek(0, os.SEEK_END)
  nbytes = lines.tell()
  lines.seek(0, os.SEEK_SET)

  num_shards = len(vocab) / FLAGS.shard_size

  shardfiles = {}
  for row in range(num_shards):
    for col in range(num_shards):
      filename = os.path.join(
          FLAGS.output_dir, 'shard-%03d-%03d.tmp' % (row, col))

      shardfiles[(row, col)] = open(filename, 'w+')

  def flush_coocs():
    for (row_id, col_id), cnt in coocs.iteritems():
      row_shard = row_id % num_shards
      row_off = row_id / num_shards
      col_shard = col_id % num_shards
      col_off = col_id / num_shards

      # Since we only stored (a, b), we emit both (a, b) and (b, a).
      shardfiles[(row_shard, col_shard)].write(
          shard_cooc_fmt.pack(row_off, col_off, cnt))

      shardfiles[(col_shard, row_shard)].write(
          shard_cooc_fmt.pack(col_off, row_off, cnt))

  coocs = {}
  sums = [0.0] * len(vocab)

  for lineno, line in enumerate(lines, start=1):
    # Computes the word IDs for each word in the sentence.  This has the effect
    # of "stretching" the window past OOV tokens.
    wids = filter(
        lambda wid: wid is not None,
        (word_to_id.get(w) for w in words(line)))

    for pos in xrange(len(wids)):
      lid = wids[pos]
      window_extent = min(FLAGS.window_size + 1, len(wids) - pos)
      for off in xrange(1, window_extent):
        rid = wids[pos + off]
        pair = (min(lid, rid), max(lid, rid))
        count = 1.0 / off
        sums[lid] += count
        sums[rid] += count
        coocs.setdefault(pair, 0.0)
        coocs[pair] += count

      sums[lid] += 1.0
      pair = (lid, lid)
      coocs.setdefault(pair, 0.0)
      coocs[pair] += 0.5  # Only add 1/2 since we output (a, b) and (b, a)

    if lineno % 10000 == 0:
      pos = lines.tell()
      sys.stdout.write('\rComputing co-occurrences: %0.1f%% (%d/%d)...' % (
          100.0 * pos / nbytes, pos, nbytes))
      sys.stdout.flush()

      if len(coocs) > FLAGS.bufsz:
        flush_coocs()
        coocs = {}

  flush_coocs()
  sys.stdout.write('\n')

  return shardfiles, sums


def write_shards(vocab, shardfiles):
  """Processes the temporary files to generate the final shard data.

  The shard data is stored as a tf.Example protos using a TFRecordWriter. The
  temporary files are removed from the filesystem once they've been processed.

  """
  num_shards = len(vocab) / FLAGS.shard_size

  ix = 0
  for (row, col), fh in shardfiles.iteritems():
    ix += 1
    sys.stdout.write('\rwriting shard %d/%d' % (ix, len(shardfiles)))
    sys.stdout.flush()

    # Read the entire binary co-occurrence and unpack it into an array.
    fh.seek(0)
    buf = fh.read()
    os.unlink(fh.name)
    fh.close()

    coocs = [
        shard_cooc_fmt.unpack_from(buf, off)
        for off in range(0, len(buf), shard_cooc_fmt.size)]

    # Sort and merge co-occurrences for the same pairs.
    coocs.sort()

    if coocs:
      current_pos = 0
      current_row_col = (coocs[current_pos][0], coocs[current_pos][1])
      for next_pos in range(1, len(coocs)):
        next_row_col = (coocs[next_pos][0], coocs[next_pos][1])
        if current_row_col == next_row_col:
          coocs[current_pos] = (
              coocs[current_pos][0],
              coocs[current_pos][1],
              coocs[current_pos][2] + coocs[next_pos][2])
        else:
          current_pos += 1
          if current_pos < next_pos:
            coocs[current_pos] = coocs[next_pos]

          current_row_col = (coocs[current_pos][0], coocs[current_pos][1])

      coocs = coocs[:(1 + current_pos)]

    # Convert to a TF Example proto.
    def _int64s(xs):
      return tf.train.Feature(int64_list=tf.train.Int64List(value=list(xs)))

    def _floats(xs):
      return tf.train.Feature(float_list=tf.train.FloatList(value=list(xs)))

    example = tf.train.Example(features=tf.train.Features(feature={
        'global_row': _int64s(
            row + num_shards * i for i in range(FLAGS.shard_size)),
        'global_col': _int64s(
            col + num_shards * i for i in range(FLAGS.shard_size)),

        'sparse_local_row': _int64s(cooc[0] for cooc in coocs),
        'sparse_local_col': _int64s(cooc[1] for cooc in coocs),
        'sparse_value': _floats(cooc[2] for cooc in coocs),
    }))

    filename = os.path.join(FLAGS.output_dir, 'shard-%03d-%03d.pb' % (row, col))
    with open(filename, 'w') as out:
      out.write(example.SerializeToString())

  sys.stdout.write('\n')


def main(_):
  # Create the output directory, if necessary
  if FLAGS.output_dir and not os.path.isdir(FLAGS.output_dir):
    os.makedirs(FLAGS.output_dir)

  # Read the file onces to create the vocabulary.
  if FLAGS.vocab:
    with open(FLAGS.vocab, 'r') as lines:
      vocab = [line.strip() for line in lines]
  else:
    with open(FLAGS.input, 'r') as lines:
      vocab = create_vocabulary(lines)

  # Now read the file again to determine the co-occurrence stats.
  with open(FLAGS.input, 'r') as lines:
    shardfiles, sums = compute_coocs(lines, vocab)

  # Collect individual shards into the shards.recs file.
  write_shards(vocab, shardfiles)

  # Now write the marginals.  They're symmetric for this application.
  write_vocab_and_sums(vocab, sums, 'row_vocab.txt', 'row_sums.txt')
  write_vocab_and_sums(vocab, sums, 'col_vocab.txt', 'col_sums.txt')

  print 'done!'


if __name__ == '__main__':
  tf.app.run()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mmap
import numpy as np
import os
import struct

class Vecs(object):
  def __init__(self, vocab_filename, rows_filename, cols_filename=None):
    """Initializes the vectors from a text vocabulary and binary data."""
    with open(vocab_filename, 'r') as lines:
      self.vocab = [line.split()[0] for line in lines]
      self.word_to_idx = {word: idx for idx, word in enumerate(self.vocab)}

    n = len(self.vocab)

    with open(rows_filename, 'r') as rows_fh:
      rows_fh.seek(0, os.SEEK_END)
      size = rows_fh.tell()

      # Make sure that the file size seems reasonable.
      if size % (4 * n) != 0:
        raise IOError(
            'unexpected file size for binary vector file %s' % rows_filename)

      # Memory map the rows.
      dim = size / (4 * n)
      rows_mm = mmap.mmap(rows_fh.fileno(), 0, prot=mmap.PROT_READ)
      rows = np.matrix(
          np.frombuffer(rows_mm, dtype=np.float32).reshape(n, dim))

      # If column vectors were specified, then open them and add them to the row
      # vectors.
      if cols_filename:
        with open(cols_filename, 'r') as cols_fh:
          cols_mm = mmap.mmap(cols_fh.fileno(), 0, prot=mmap.PROT_READ)
          cols_fh.seek(0, os.SEEK_END)
          if cols_fh.tell() != size:
            raise IOError('row and column vector files have different sizes')

          cols = np.matrix(
              np.frombuffer(cols_mm, dtype=np.float32).reshape(n, dim))

          rows += cols
          cols_mm.close()

      # Normalize so that dot products are just cosine similarity.
      self.vecs = rows / np.linalg.norm(rows, axis=1).reshape(n, 1)
      rows_mm.close()

  def similarity(self, word1, word2):
    """Computes the similarity of two tokens."""
    idx1 = self.word_to_idx.get(word1)
    idx2 = self.word_to_idx.get(word2)
    if not idx1 or not idx2:
      return None

    return float(self.vecs[idx1] * self.vecs[idx2].transpose())

  def neighbors(self, query):
    """Returns the nearest neighbors to the query (a word or vector)."""
    if isinstance(query, basestring):
      idx = self.word_to_idx.get(query)
      if idx is None:
        return None

      query = self.vecs[idx]

    neighbors = self.vecs * query.transpose()

    return sorted(
      zip(self.vocab, neighbors.flat),
      key=lambda kv: kv[1], reverse=True)

  def lookup(self, word):
    """Returns the embedding for a token, or None if no embedding exists."""
    idx = self.word_to_idx.get(word)
    return None if idx is None else self.vecs[idx]

#!/usr/bin/env python
#
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Computes Spearman's rho with respect to human judgements.

Given a set of row (and potentially column) embeddings, this computes Spearman's
rho between the rank ordering of predicted word similarity and human judgements.

Usage:

  wordim.py --embeddings=<binvecs> --vocab=<vocab> eval1.tab eval2.tab ...

Options:

  --embeddings=<filename>: the vectors to test
  --vocab=<filename>: the vocabulary file

Evaluation files are assumed to be tab-separated files with exactly three
columns.  The first two columns contain the words, and the third column contains
the scored human judgement.

"""

import scipy.stats
import sys
from getopt import GetoptError, getopt

from vecs import Vecs

try:
  opts, args = getopt(sys.argv[1:], '', ['embeddings=', 'vocab='])
except GetoptError, e:
  print >> sys.stderr, e
  sys.exit(2)

opt_embeddings = None
opt_vocab = None

for o, a in opts:
  if o == '--embeddings':
    opt_embeddings = a
  if o == '--vocab':
    opt_vocab = a

if not opt_vocab:
  print >> sys.stderr, 'please specify a vocabulary file with "--vocab"'
  sys.exit(2)

if not opt_embeddings:
  print >> sys.stderr, 'please specify the embeddings with "--embeddings"'
  sys.exit(2)

try:
  vecs = Vecs(opt_vocab, opt_embeddings)
except IOError, e:
  print >> sys.stderr, e
  sys.exit(1)

def evaluate(lines):
  acts, preds = [], []

  with open(filename, 'r') as lines:
    for line in lines:
      w1, w2, act = line.strip().split('\t')
      pred = vecs.similarity(w1, w2)
      if pred is None:
        continue

      acts.append(float(act))
      preds.append(pred)

  rho, _ = scipy.stats.spearmanr(acts, preds)
  return rho

for filename in args:
  with open(filename, 'r') as lines:
    print '%0.3f %s' % (evaluate(lines), filename)

#!/usr/bin/env python
#
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Converts vectors from text to a binary format for quicker manipulation.

Usage:

  text2bin.py -o <out> -v <vocab> vec1.txt [vec2.txt ...]

Optiona:

  -o <filename>, --output <filename>
    The name of the file into which the binary vectors are written.

  -v <filename>, --vocab <filename>
    The name of the file into which the vocabulary is written.

Description

This program merges one or more whitespace separated vector files into a single
binary vector file that can be used by downstream evaluation tools in this
directory ("wordsim.py" and "analogy").

If more than one vector file is specified, then the files must be aligned
row-wise (i.e., each line must correspond to the same embedding), and they must
have the same number of columns (i.e., be the same dimension).

"""

from itertools import izip
from getopt import GetoptError, getopt
import os
import struct
import sys

try:
  opts, args = getopt(
      sys.argv[1:], 'o:v:', ['output=', 'vocab='])
except GetoptError, e:
  print >> sys.stderr, e
  sys.exit(2)

opt_output = 'vecs.bin'
opt_vocab = 'vocab.txt'
for o, a in opts:
  if o in ('-o', '--output'):
    opt_output = a
  if o in ('-v', '--vocab'):
    opt_vocab = a

def go(fhs):
  fmt = None
  with open(opt_vocab, 'w') as vocab_out:
    with open(opt_output, 'w') as vecs_out:
      for lines in izip(*fhs):
        parts = [line.split() for line in lines]
        token = parts[0][0]
        if any(part[0] != token for part in parts[1:]):
          raise IOError('vector files must be aligned')

        print >> vocab_out, token

        vec = [sum(float(x) for x in xs) for xs in zip(*parts)[1:]]
        if not fmt:
          fmt = struct.Struct('%df' % len(vec))

        vecs_out.write(fmt.pack(*vec))

if args:
  fhs = [open(filename) for filename in args]
  go(fhs)
  for fh in fhs:
    fh.close()
else:
  go([sys.stdin])

#!/usr/bin/env python
#
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Simple tool for inspecting nearest neighbors and analogies."""

import re
import sys
from getopt import GetoptError, getopt

from vecs import Vecs

try:
  opts, args = getopt(sys.argv[1:], 'v:e:', ['vocab=', 'embeddings='])
except GetoptError, e:
  print >> sys.stderr, e
  sys.exit(2)

opt_vocab = 'vocab.txt'
opt_embeddings = None

for o, a in opts:
  if o in ('-v', '--vocab'):
    opt_vocab = a
  if o in ('-e', '--embeddings'):
    opt_embeddings = a

vecs = Vecs(opt_vocab, opt_embeddings)

while True:
  sys.stdout.write('query> ')
  sys.stdout.flush()

  query = sys.stdin.readline().strip()
  if not query:
    break

  parts = re.split(r'\s+', query)

  if len(parts) == 1:
    res = vecs.neighbors(parts[0])

  elif len(parts) == 3:
    vs = [vecs.lookup(w) for w in parts]
    if any(v is None for v in vs):
      print 'not in vocabulary: %s' % (
          ', '.join(tok for tok, v in zip(parts, vs) if v is None))

      continue

    res = vecs.neighbors(vs[2] - vs[0] + vs[1])

  else:
    print 'use a single word to query neighbors, or three words for analogy'
    continue

  if not res:
    continue

  for word, sim in res[:20]:
    print '%0.4f: %s' % (sim, word)

  print

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
# pylint: disable=line-too-long
"""A binary to train Inception in a distributed manner using multiple systems.

Please see accompanying README.md for details and instructions.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

from inception import inception_distributed_train
from inception.imagenet_data import ImagenetData

FLAGS = tf.app.flags.FLAGS


def main(unused_args):
  assert FLAGS.job_name in ['ps', 'worker'], 'job_name must be ps or worker'

  # Extract all the hostnames for the ps and worker jobs to construct the
  # cluster spec.
  ps_hosts = FLAGS.ps_hosts.split(',')
  worker_hosts = FLAGS.worker_hosts.split(',')
  tf.logging.info('PS hosts are: %s' % ps_hosts)
  tf.logging.info('Worker hosts are: %s' % worker_hosts)

  cluster_spec = tf.train.ClusterSpec({'ps': ps_hosts,
                                       'worker': worker_hosts})
  server = tf.train.Server(
      {'ps': ps_hosts,
       'worker': worker_hosts},
      job_name=FLAGS.job_name,
      task_index=FLAGS.task_id)

  if FLAGS.job_name == 'ps':
    # `ps` jobs wait for incoming connections from the workers.
    server.join()
  else:
    # `worker` jobs will actually do the work.
    dataset = ImagenetData(subset=FLAGS.subset)
    assert dataset.data_files()
    # Only the chief checks for or creates train_dir.
    if FLAGS.task_id == 0:
      if not tf.gfile.Exists(FLAGS.train_dir):
        tf.gfile.MakeDirs(FLAGS.train_dir)
    inception_distributed_train.train(server.target, dataset, cluster_spec)

if __name__ == '__main__':
  tf.logging.set_verbosity(tf.logging.INFO)
  tf.app.run()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""A binary to evaluate Inception on the flowers data set.

Note that using the supplied pre-trained inception checkpoint, the eval should
achieve:
  precision @ 1 = 0.7874 recall @ 5 = 0.9436 [50000 examples]

See the README.md for more details.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import tensorflow as tf

from inception import inception_eval
from inception.imagenet_data import ImagenetData

FLAGS = tf.app.flags.FLAGS


def main(unused_argv=None):
  dataset = ImagenetData(subset=FLAGS.subset)
  assert dataset.data_files()
  if tf.gfile.Exists(FLAGS.eval_dir):
    tf.gfile.DeleteRecursively(FLAGS.eval_dir)
  tf.gfile.MakeDirs(FLAGS.eval_dir)
  inception_eval.evaluate(dataset)


if __name__ == '__main__':
  tf.app.run()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Small library that points to the ImageNet data set.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function



from inception.dataset import Dataset


class ImagenetData(Dataset):
  """ImageNet data set."""

  def __init__(self, subset):
    super(ImagenetData, self).__init__('ImageNet', subset)

  def num_classes(self):
    """Returns the number of classes in the data set."""
    return 1000

  def num_examples_per_epoch(self):
    """Returns the number of examples in the data set."""
    # Bounding box data consists of 615299 bounding boxes for 544546 images.
    if self.subset == 'train':
      return 1281167
    if self.subset == 'validation':
      return 50000

  def download_message(self):
    """Instruction to download and extract the tarball from Flowers website."""

    print('Failed to find any ImageNet %s files'% self.subset)
    print('')
    print('If you have already downloaded and processed the data, then make '
          'sure to set --data_dir to point to the directory containing the '
          'location of the sharded TFRecords.\n')
    print('If you have not downloaded and prepared the ImageNet data in the '
          'TFRecord format, you will need to do this at least once. This '
          'process could take several hours depending on the speed of your '
          'computer and network connection\n')
    print('Please see README.md for instructions on how to build '
          'the ImageNet dataset using download_and_preprocess_imagenet.\n')
    print('Note that the raw data size is 300 GB and the processed data size '
          'is 150 GB. Please ensure you have at least 500GB disk space.')

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""A library to train Inception using multiple replicas with synchronous update.

Please see accompanying README.md for details and instructions.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
import os.path
import time

import numpy as np
import tensorflow as tf

from inception import image_processing
from inception import inception_model as inception
from inception.slim import slim

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_string('job_name', '', 'One of "ps", "worker"')
tf.app.flags.DEFINE_string('ps_hosts', '',
                           """Comma-separated list of hostname:port for the """
                           """parameter server jobs. e.g. """
                           """'machine1:2222,machine2:1111,machine2:2222'""")
tf.app.flags.DEFINE_string('worker_hosts', '',
                           """Comma-separated list of hostname:port for the """
                           """worker jobs. e.g. """
                           """'machine1:2222,machine2:1111,machine2:2222'""")

tf.app.flags.DEFINE_string('train_dir', '/tmp/imagenet_train',
                           """Directory where to write event logs """
                           """and checkpoint.""")
tf.app.flags.DEFINE_integer('max_steps', 1000000, 'Number of batches to run.')
tf.app.flags.DEFINE_string('subset', 'train', 'Either "train" or "validation".')
tf.app.flags.DEFINE_boolean('log_device_placement', False,
                            'Whether to log device placement.')

# Task ID is used to select the chief and also to access the local_step for
# each replica to check staleness of the gradients in sync_replicas_optimizer.
tf.app.flags.DEFINE_integer(
    'task_id', 0, 'Task ID of the worker/replica running the training.')

# More details can be found in the sync_replicas_optimizer class:
# tensorflow/python/training/sync_replicas_optimizer.py
tf.app.flags.DEFINE_integer('num_replicas_to_aggregate', -1,
                            """Number of gradients to collect before """
                            """updating the parameters.""")
tf.app.flags.DEFINE_integer('save_interval_secs', 10 * 60,
                            'Save interval seconds.')
tf.app.flags.DEFINE_integer('save_summaries_secs', 180,
                            'Save summaries interval seconds.')

# **IMPORTANT**
# Please note that this learning rate schedule is heavily dependent on the
# hardware architecture, batch size and any changes to the model architecture
# specification. Selecting a finely tuned learning rate schedule is an
# empirical process that requires some experimentation. Please see README.md
# more guidance and discussion.
#
# Learning rate decay factor selected from https://arxiv.org/abs/1604.00981
tf.app.flags.DEFINE_float('initial_learning_rate', 0.045,
                          'Initial learning rate.')
tf.app.flags.DEFINE_float('num_epochs_per_decay', 2.0,
                          'Epochs after which learning rate decays.')
tf.app.flags.DEFINE_float('learning_rate_decay_factor', 0.94,
                          'Learning rate decay factor.')

# Constants dictating the learning rate schedule.
RMSPROP_DECAY = 0.9                # Decay term for RMSProp.
RMSPROP_MOMENTUM = 0.9             # Momentum in RMSProp.
RMSPROP_EPSILON = 1.0              # Epsilon term for RMSProp.


def train(target, dataset, cluster_spec):
  """Train Inception on a dataset for a number of steps."""
  # Number of workers and parameter servers are infered from the workers and ps
  # hosts string.
  num_workers = len(cluster_spec.as_dict()['worker'])
  num_parameter_servers = len(cluster_spec.as_dict()['ps'])
  # If no value is given, num_replicas_to_aggregate defaults to be the number of
  # workers.
  if FLAGS.num_replicas_to_aggregate == -1:
    num_replicas_to_aggregate = num_workers
  else:
    num_replicas_to_aggregate = FLAGS.num_replicas_to_aggregate

  # Both should be greater than 0 in a distributed training.
  assert num_workers > 0 and num_parameter_servers > 0, (' num_workers and '
                                                         'num_parameter_servers'
                                                         ' must be > 0.')

  # Choose worker 0 as the chief. Note that any worker could be the chief
  # but there should be only one chief.
  is_chief = (FLAGS.task_id == 0)

  # Ops are assigned to worker by default.
  with tf.device('/job:worker/task:%d' % FLAGS.task_id):
    # Variables and its related init/assign ops are assigned to ps.
    with slim.scopes.arg_scope(
        [slim.variables.variable, slim.variables.global_step],
        device=slim.variables.VariableDeviceChooser(num_parameter_servers)):
      # Create a variable to count the number of train() calls. This equals the
      # number of updates applied to the variables.
      global_step = slim.variables.global_step()

      # Calculate the learning rate schedule.
      num_batches_per_epoch = (dataset.num_examples_per_epoch() /
                               FLAGS.batch_size)
      # Decay steps need to be divided by the number of replicas to aggregate.
      decay_steps = int(num_batches_per_epoch * FLAGS.num_epochs_per_decay /
                        num_replicas_to_aggregate)

      # Decay the learning rate exponentially based on the number of steps.
      lr = tf.train.exponential_decay(FLAGS.initial_learning_rate,
                                      global_step,
                                      decay_steps,
                                      FLAGS.learning_rate_decay_factor,
                                      staircase=True)
      # Add a summary to track the learning rate.
      tf.scalar_summary('learning_rate', lr)

      # Create an optimizer that performs gradient descent.
      opt = tf.train.RMSPropOptimizer(lr,
                                      RMSPROP_DECAY,
                                      momentum=RMSPROP_MOMENTUM,
                                      epsilon=RMSPROP_EPSILON)

      images, labels = image_processing.distorted_inputs(
          dataset,
          batch_size=FLAGS.batch_size,
          num_preprocess_threads=FLAGS.num_preprocess_threads)

      # Number of classes in the Dataset label set plus 1.
      # Label 0 is reserved for an (unused) background class.
      num_classes = dataset.num_classes() + 1
      logits = inception.inference(images, num_classes, for_training=True)
      # Add classification loss.
      inception.loss(logits, labels)

      # Gather all of the losses including regularization losses.
      losses = tf.get_collection(slim.losses.LOSSES_COLLECTION)
      losses += tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)

      total_loss = tf.add_n(losses, name='total_loss')

      if is_chief:
        # Compute the moving average of all individual losses and the
        # total loss.
        loss_averages = tf.train.ExponentialMovingAverage(0.9, name='avg')
        loss_averages_op = loss_averages.apply(losses + [total_loss])

        # Attach a scalar summmary to all individual losses and the total loss;
        # do the same for the averaged version of the losses.
        for l in losses + [total_loss]:
          loss_name = l.op.name
          # Name each loss as '(raw)' and name the moving average version of the
          # loss as the original loss name.
          tf.scalar_summary(loss_name + ' (raw)', l)
          tf.scalar_summary(loss_name, loss_averages.average(l))

        # Add dependency to compute loss_averages.
        with tf.control_dependencies([loss_averages_op]):
          total_loss = tf.identity(total_loss)

      # Track the moving averages of all trainable variables.
      # Note that we maintain a 'double-average' of the BatchNormalization
      # global statistics.
      # This is not needed when the number of replicas are small but important
      # for synchronous distributed training with tens of workers/replicas.
      exp_moving_averager = tf.train.ExponentialMovingAverage(
          inception.MOVING_AVERAGE_DECAY, global_step)

      variables_to_average = (
          tf.trainable_variables() + tf.moving_average_variables())

      # Add histograms for model variables.
      for var in variables_to_average:
        tf.histogram_summary(var.op.name, var)

      # Create synchronous replica optimizer.
      opt = tf.train.SyncReplicasOptimizer(
          opt,
          replicas_to_aggregate=num_replicas_to_aggregate,
          replica_id=FLAGS.task_id,
          total_num_replicas=num_workers,
          variable_averages=exp_moving_averager,
          variables_to_average=variables_to_average)

      batchnorm_updates = tf.get_collection(slim.ops.UPDATE_OPS_COLLECTION)
      assert batchnorm_updates, 'Batchnorm updates are missing'
      batchnorm_updates_op = tf.group(*batchnorm_updates)
      # Add dependency to compute batchnorm_updates.
      with tf.control_dependencies([batchnorm_updates_op]):
        total_loss = tf.identity(total_loss)

      # Compute gradients with respect to the loss.
      grads = opt.compute_gradients(total_loss)

      # Add histograms for gradients.
      for grad, var in grads:
        if grad is not None:
          tf.histogram_summary(var.op.name + '/gradients', grad)

      apply_gradients_op = opt.apply_gradients(grads, global_step=global_step)

      with tf.control_dependencies([apply_gradients_op]):
        train_op = tf.identity(total_loss, name='train_op')

      # Get chief queue_runners, init_tokens and clean_up_op, which is used to
      # synchronize replicas.
      # More details can be found in sync_replicas_optimizer.
      chief_queue_runners = [opt.get_chief_queue_runner()]
      init_tokens_op = opt.get_init_tokens_op()
      clean_up_op = opt.get_clean_up_op()

      # Create a saver.
      saver = tf.train.Saver()

      # Build the summary operation based on the TF collection of Summaries.
      summary_op = tf.merge_all_summaries()

      # Build an initialization operation to run below.
      init_op = tf.initialize_all_variables()

      # We run the summaries in the same thread as the training operations by
      # passing in None for summary_op to avoid a summary_thread being started.
      # Running summaries and training operations in parallel could run out of
      # GPU memory.
      sv = tf.train.Supervisor(is_chief=is_chief,
                               logdir=FLAGS.train_dir,
                               init_op=init_op,
                               summary_op=None,
                               global_step=global_step,
                               saver=saver,
                               save_model_secs=FLAGS.save_interval_secs)

      tf.logging.info('%s Supervisor' % datetime.now())

      sess_config = tf.ConfigProto(
          allow_soft_placement=True,
          log_device_placement=FLAGS.log_device_placement)

      # Get a session.
      sess = sv.prepare_or_wait_for_session(target, config=sess_config)

      # Start the queue runners.
      queue_runners = tf.get_collection(tf.GraphKeys.QUEUE_RUNNERS)
      sv.start_queue_runners(sess, queue_runners)
      tf.logging.info('Started %d queues for processing input data.',
                      len(queue_runners))

      if is_chief:
        sv.start_queue_runners(sess, chief_queue_runners)
        sess.run(init_tokens_op)

      # Train, checking for Nans. Concurrently run the summary operation at a
      # specified interval. Note that the summary_op and train_op never run
      # simultaneously in order to prevent running out of GPU memory.
      next_summary_time = time.time() + FLAGS.save_summaries_secs
      while not sv.should_stop():
        try:
          start_time = time.time()
          loss_value, step = sess.run([train_op, global_step])
          assert not np.isnan(loss_value), 'Model diverged with loss = NaN'
          if step > FLAGS.max_steps:
            break
          duration = time.time() - start_time

          if step % 30 == 0:
            examples_per_sec = FLAGS.batch_size / float(duration)
            format_str = ('Worker %d: %s: step %d, loss = %.2f'
                          '(%.1f examples/sec; %.3f  sec/batch)')
            tf.logging.info(format_str %
                            (FLAGS.task_id, datetime.now(), step, loss_value,
                             examples_per_sec, duration))

          # Determine if the summary_op should be run on the chief worker.
          if is_chief and next_summary_time < time.time():
            tf.logging.info('Running Summary operation on the chief.')
            summary_str = sess.run(summary_op)
            sv.summary_computed(sess, summary_str)
            tf.logging.info('Finished running Summary operation.')

            # Determine the next time for running the summary.
            next_summary_time += FLAGS.save_summaries_secs
        except:
          if is_chief:
            tf.logging.info('About to execute sync_clean_up_op!')
            sess.run(clean_up_op)
          raise

      # Stop the supervisor.  This also waits for service threads to finish.
      sv.stop()

      # Save after the training ends.
      if is_chief:
        saver.save(sess,
                   os.path.join(FLAGS.train_dir, 'model.ckpt'),
                   global_step=global_step)

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""A binary to train Inception on the flowers data set.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function



import tensorflow as tf

from inception import inception_train
from inception.flowers_data import FlowersData

FLAGS = tf.app.flags.FLAGS


def main(_):
  dataset = FlowersData(subset=FLAGS.subset)
  assert dataset.data_files()
  if tf.gfile.Exists(FLAGS.train_dir):
    tf.gfile.DeleteRecursively(FLAGS.train_dir)
  tf.gfile.MakeDirs(FLAGS.train_dir)
  inception_train.train(dataset)


if __name__ == '__main__':
  tf.app.run()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""A binary to train Inception on the ImageNet data set.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function



import tensorflow as tf

from inception import inception_train
from inception.imagenet_data import ImagenetData

FLAGS = tf.app.flags.FLAGS


def main(_):
  dataset = ImagenetData(subset=FLAGS.subset)
  assert dataset.data_files()
  if tf.gfile.Exists(FLAGS.train_dir):
    tf.gfile.DeleteRecursively(FLAGS.train_dir)
  tf.gfile.MakeDirs(FLAGS.train_dir)
  inception_train.train(dataset)


if __name__ == '__main__':
  tf.app.run()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""A library to train Inception using multiple GPU's with synchronous updates.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy
from datetime import datetime
import os.path
import re
import time

import numpy as np
import tensorflow as tf

from inception import image_processing
from inception import inception_model as inception
from inception.slim import slim

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_string('train_dir', '/tmp/imagenet_train',
                           """Directory where to write event logs """
                           """and checkpoint.""")
tf.app.flags.DEFINE_integer('max_steps', 10000000,
                            """Number of batches to run.""")
tf.app.flags.DEFINE_string('subset', 'train',
                           """Either 'train' or 'validation'.""")

# Flags governing the hardware employed for running TensorFlow.
tf.app.flags.DEFINE_integer('num_gpus', 1,
                            """How many GPUs to use.""")
tf.app.flags.DEFINE_boolean('log_device_placement', False,
                            """Whether to log device placement.""")

# Flags governing the type of training.
tf.app.flags.DEFINE_boolean('fine_tune', False,
                            """If set, randomly initialize the final layer """
                            """of weights in order to train the network on a """
                            """new task.""")
tf.app.flags.DEFINE_string('pretrained_model_checkpoint_path', '',
                           """If specified, restore this pretrained model """
                           """before beginning any training.""")

# **IMPORTANT**
# Please note that this learning rate schedule is heavily dependent on the
# hardware architecture, batch size and any changes to the model architecture
# specification. Selecting a finely tuned learning rate schedule is an
# empirical process that requires some experimentation. Please see README.md
# more guidance and discussion.
#
# With 8 Tesla K40's and a batch size = 256, the following setup achieves
# precision@1 = 73.5% after 100 hours and 100K steps (20 epochs).
# Learning rate decay factor selected from http://arxiv.org/abs/1404.5997.
tf.app.flags.DEFINE_float('initial_learning_rate', 0.1,
                          """Initial learning rate.""")
tf.app.flags.DEFINE_float('num_epochs_per_decay', 30.0,
                          """Epochs after which learning rate decays.""")
tf.app.flags.DEFINE_float('learning_rate_decay_factor', 0.16,
                          """Learning rate decay factor.""")

# Constants dictating the learning rate schedule.
RMSPROP_DECAY = 0.9                # Decay term for RMSProp.
RMSPROP_MOMENTUM = 0.9             # Momentum in RMSProp.
RMSPROP_EPSILON = 1.0              # Epsilon term for RMSProp.


def _tower_loss(images, labels, num_classes, scope):
  """Calculate the total loss on a single tower running the ImageNet model.

  We perform 'batch splitting'. This means that we cut up a batch across
  multiple GPU's. For instance, if the batch size = 32 and num_gpus = 2,
  then each tower will operate on an batch of 16 images.

  Args:
    images: Images. 4D tensor of size [batch_size, FLAGS.image_size,
                                       FLAGS.image_size, 3].
    labels: 1-D integer Tensor of [batch_size].
    num_classes: number of classes
    scope: unique prefix string identifying the ImageNet tower, e.g.
      'tower_0'.

  Returns:
     Tensor of shape [] containing the total loss for a batch of data
  """
  # When fine-tuning a model, we do not restore the logits but instead we
  # randomly initialize the logits. The number of classes in the output of the
  # logit is the number of classes in specified Dataset.
  restore_logits = not FLAGS.fine_tune

  # Build inference Graph.
  logits = inception.inference(images, num_classes, for_training=True,
                               restore_logits=restore_logits,
                               scope=scope)

  # Build the portion of the Graph calculating the losses. Note that we will
  # assemble the total_loss using a custom function below.
  split_batch_size = images.get_shape().as_list()[0]
  inception.loss(logits, labels, batch_size=split_batch_size)

  # Assemble all of the losses for the current tower only.
  losses = tf.get_collection(slim.losses.LOSSES_COLLECTION, scope)

  # Calculate the total loss for the current tower.
  regularization_losses = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)
  total_loss = tf.add_n(losses + regularization_losses, name='total_loss')

  # Compute the moving average of all individual losses and the total loss.
  loss_averages = tf.train.ExponentialMovingAverage(0.9, name='avg')
  loss_averages_op = loss_averages.apply(losses + [total_loss])

  # Attach a scalar summmary to all individual losses and the total loss; do the
  # same for the averaged version of the losses.
  for l in losses + [total_loss]:
    # Remove 'tower_[0-9]/' from the name in case this is a multi-GPU training
    # session. This helps the clarity of presentation on TensorBoard.
    loss_name = re.sub('%s_[0-9]*/' % inception.TOWER_NAME, '', l.op.name)
    # Name each loss as '(raw)' and name the moving average version of the loss
    # as the original loss name.
    tf.scalar_summary(loss_name +' (raw)', l)
    tf.scalar_summary(loss_name, loss_averages.average(l))

  with tf.control_dependencies([loss_averages_op]):
    total_loss = tf.identity(total_loss)
  return total_loss


def _average_gradients(tower_grads):
  """Calculate the average gradient for each shared variable across all towers.

  Note that this function provides a synchronization point across all towers.

  Args:
    tower_grads: List of lists of (gradient, variable) tuples. The outer list
      is over individual gradients. The inner list is over the gradient
      calculation for each tower.
  Returns:
     List of pairs of (gradient, variable) where the gradient has been averaged
     across all towers.
  """
  average_grads = []
  for grad_and_vars in zip(*tower_grads):
    # Note that each grad_and_vars looks like the following:
    #   ((grad0_gpu0, var0_gpu0), ... , (grad0_gpuN, var0_gpuN))
    grads = []
    for g, _ in grad_and_vars:
      # Add 0 dimension to the gradients to represent the tower.
      expanded_g = tf.expand_dims(g, 0)

      # Append on a 'tower' dimension which we will average over below.
      grads.append(expanded_g)

    # Average over the 'tower' dimension.
    grad = tf.concat(0, grads)
    grad = tf.reduce_mean(grad, 0)

    # Keep in mind that the Variables are redundant because they are shared
    # across towers. So .. we will just return the first tower's pointer to
    # the Variable.
    v = grad_and_vars[0][1]
    grad_and_var = (grad, v)
    average_grads.append(grad_and_var)
  return average_grads


def train(dataset):
  """Train on dataset for a number of steps."""
  with tf.Graph().as_default(), tf.device('/cpu:0'):
    # Create a variable to count the number of train() calls. This equals the
    # number of batches processed * FLAGS.num_gpus.
    global_step = tf.get_variable(
        'global_step', [],
        initializer=tf.constant_initializer(0), trainable=False)

    # Calculate the learning rate schedule.
    num_batches_per_epoch = (dataset.num_examples_per_epoch() /
                             FLAGS.batch_size)
    decay_steps = int(num_batches_per_epoch * FLAGS.num_epochs_per_decay)

    # Decay the learning rate exponentially based on the number of steps.
    lr = tf.train.exponential_decay(FLAGS.initial_learning_rate,
                                    global_step,
                                    decay_steps,
                                    FLAGS.learning_rate_decay_factor,
                                    staircase=True)

    # Create an optimizer that performs gradient descent.
    opt = tf.train.RMSPropOptimizer(lr, RMSPROP_DECAY,
                                    momentum=RMSPROP_MOMENTUM,
                                    epsilon=RMSPROP_EPSILON)

    # Get images and labels for ImageNet and split the batch across GPUs.
    assert FLAGS.batch_size % FLAGS.num_gpus == 0, (
        'Batch size must be divisible by number of GPUs')
    split_batch_size = int(FLAGS.batch_size / FLAGS.num_gpus)

    # Override the number of preprocessing threads to account for the increased
    # number of GPU towers.
    num_preprocess_threads = FLAGS.num_preprocess_threads * FLAGS.num_gpus
    images, labels = image_processing.distorted_inputs(
        dataset,
        num_preprocess_threads=num_preprocess_threads)

    input_summaries = copy.copy(tf.get_collection(tf.GraphKeys.SUMMARIES))

    # Number of classes in the Dataset label set plus 1.
    # Label 0 is reserved for an (unused) background class.
    num_classes = dataset.num_classes() + 1
    
     # Split the batch of images and labels for towers.
    images_splits = tf.split(0, FLAGS.num_gpus, images)
    labels_splits = tf.split(0, FLAGS.num_gpus, labels)

    # Calculate the gradients for each model tower.
    tower_grads = []
    for i in xrange(FLAGS.num_gpus):
      with tf.device('/gpu:%d' % i):
        with tf.name_scope('%s_%d' % (inception.TOWER_NAME, i)) as scope:
          # Force all Variables to reside on the CPU.
          with slim.arg_scope([slim.variables.variable], device='/cpu:0'):
            # Calculate the loss for one tower of the ImageNet model. This
            # function constructs the entire ImageNet model but shares the
            # variables across all towers.
            loss = _tower_loss(images_splits[i], labels_splits[i], num_classes,
                               scope)

          # Reuse variables for the next tower.
          tf.get_variable_scope().reuse_variables()

          # Retain the summaries from the final tower.
          summaries = tf.get_collection(tf.GraphKeys.SUMMARIES, scope)

          # Retain the Batch Normalization updates operations only from the
          # final tower. Ideally, we should grab the updates from all towers
          # but these stats accumulate extremely fast so we can ignore the
          # other stats from the other towers without significant detriment.
          batchnorm_updates = tf.get_collection(slim.ops.UPDATE_OPS_COLLECTION,
                                                scope)

          # Calculate the gradients for the batch of data on this ImageNet
          # tower.
          grads = opt.compute_gradients(loss)

          # Keep track of the gradients across all towers.
          tower_grads.append(grads)

    # We must calculate the mean of each gradient. Note that this is the
    # synchronization point across all towers.
    grads = _average_gradients(tower_grads)

    # Add a summaries for the input processing and global_step.
    summaries.extend(input_summaries)

    # Add a summary to track the learning rate.
    summaries.append(tf.scalar_summary('learning_rate', lr))

    # Add histograms for gradients.
    for grad, var in grads:
      if grad is not None:
        summaries.append(
            tf.histogram_summary(var.op.name + '/gradients', grad))

    # Apply the gradients to adjust the shared variables.
    apply_gradient_op = opt.apply_gradients(grads, global_step=global_step)

    # Add histograms for trainable variables.
    for var in tf.trainable_variables():
      summaries.append(tf.histogram_summary(var.op.name, var))

    # Track the moving averages of all trainable variables.
    # Note that we maintain a "double-average" of the BatchNormalization
    # global statistics. This is more complicated then need be but we employ
    # this for backward-compatibility with our previous models.
    variable_averages = tf.train.ExponentialMovingAverage(
        inception.MOVING_AVERAGE_DECAY, global_step)

    # Another possiblility is to use tf.slim.get_variables().
    variables_to_average = (tf.trainable_variables() +
                            tf.moving_average_variables())
    variables_averages_op = variable_averages.apply(variables_to_average)

    # Group all updates to into a single train op.
    batchnorm_updates_op = tf.group(*batchnorm_updates)
    train_op = tf.group(apply_gradient_op, variables_averages_op,
                        batchnorm_updates_op)

    # Create a saver.
    saver = tf.train.Saver(tf.all_variables())

    # Build the summary operation from the last tower summaries.
    summary_op = tf.merge_summary(summaries)

    # Build an initialization operation to run below.
    init = tf.initialize_all_variables()

    # Start running operations on the Graph. allow_soft_placement must be set to
    # True to build towers on GPU, as some of the ops do not have GPU
    # implementations.
    sess = tf.Session(config=tf.ConfigProto(
        allow_soft_placement=True,
        log_device_placement=FLAGS.log_device_placement))
    sess.run(init)

    if FLAGS.pretrained_model_checkpoint_path:
      assert tf.gfile.Exists(FLAGS.pretrained_model_checkpoint_path)
      variables_to_restore = tf.get_collection(
          slim.variables.VARIABLES_TO_RESTORE)
      restorer = tf.train.Saver(variables_to_restore)
      restorer.restore(sess, FLAGS.pretrained_model_checkpoint_path)
      print('%s: Pre-trained model restored from %s' %
            (datetime.now(), FLAGS.pretrained_model_checkpoint_path))

    # Start the queue runners.
    tf.train.start_queue_runners(sess=sess)

    summary_writer = tf.train.SummaryWriter(
        FLAGS.train_dir,
        graph_def=sess.graph.as_graph_def(add_shapes=True))

    for step in xrange(FLAGS.max_steps):
      start_time = time.time()
      _, loss_value = sess.run([train_op, loss])
      duration = time.time() - start_time

      assert not np.isnan(loss_value), 'Model diverged with loss = NaN'

      if step % 10 == 0:
        examples_per_sec = FLAGS.batch_size / float(duration)
        format_str = ('%s: step %d, loss = %.2f (%.1f examples/sec; %.3f '
                      'sec/batch)')
        print(format_str % (datetime.now(), step, loss_value,
                            examples_per_sec, duration))

      if step % 100 == 0:
        summary_str = sess.run(summary_op)
        summary_writer.add_summary(summary_str, step)

      # Save the model checkpoint periodically.
      if step % 5000 == 0 or (step + 1) == FLAGS.max_steps:
        checkpoint_path = os.path.join(FLAGS.train_dir, 'model.ckpt')
        saver.save(sess, checkpoint_path, global_step=step)

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Small library that points to a data set.

Methods of Data class:
  data_files: Returns a python list of all (sharded) data set files.
  num_examples_per_epoch: Returns the number of examples in the data set.
  num_classes: Returns the number of classes in the data set.
  reader: Return a reader for a single entry from the data set.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from abc import ABCMeta
from abc import abstractmethod
import os


import tensorflow as tf

FLAGS = tf.app.flags.FLAGS

# Basic model parameters.
tf.app.flags.DEFINE_string('data_dir', '/tmp/mydata',
                           """Path to the processed data, i.e. """
                           """TFRecord of Example protos.""")


class Dataset(object):
  """A simple class for handling data sets."""
  __metaclass__ = ABCMeta

  def __init__(self, name, subset):
    """Initialize dataset using a subset and the path to the data."""
    assert subset in self.available_subsets(), self.available_subsets()
    self.name = name
    self.subset = subset

  @abstractmethod
  def num_classes(self):
    """Returns the number of classes in the data set."""
    pass
    # return 10

  @abstractmethod
  def num_examples_per_epoch(self):
    """Returns the number of examples in the data subset."""
    pass
    # if self.subset == 'train':
    #   return 10000
    # if self.subset == 'validation':
    #   return 1000

  @abstractmethod
  def download_message(self):
    """Prints a download message for the Dataset."""
    pass

  def available_subsets(self):
    """Returns the list of available subsets."""
    return ['train', 'validation']

  def data_files(self):
    """Returns a python list of all (sharded) data subset files.

    Returns:
      python list of all (sharded) data set files.
    Raises:
      ValueError: if there are not data_files matching the subset.
    """
    tf_record_pattern = os.path.join(FLAGS.data_dir, '%s-*' % self.subset)
    data_files = tf.gfile.Glob(tf_record_pattern)
    if not data_files:
      print('No files found for dataset %s/%s at %s' % (self.name,
                                                        self.subset,
                                                        FLAGS.data_dir))

      self.download_message()
      exit(-1)
    return data_files

  def reader(self):
    """Return a reader for a single entry from the data set.

    See io_ops.py for details of Reader class.

    Returns:
      Reader object that reads the data set.
    """
    return tf.TFRecordReader()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Build the Inception v3 network on ImageNet data set.

The Inception v3 architecture is described in http://arxiv.org/abs/1512.00567

Summary of available functions:
 inference: Compute inference on the model inputs to make a prediction
 loss: Compute the loss of the prediction with respect to the labels
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re

import tensorflow as tf

from inception.slim import slim

FLAGS = tf.app.flags.FLAGS

# If a model is trained using multiple GPUs, prefix all Op names with tower_name
# to differentiate the operations. Note that this prefix is removed from the
# names of the summaries when visualizing a model.
TOWER_NAME = 'tower'

# Batch normalization. Constant governing the exponential moving average of
# the 'global' mean and variance for all activations.
BATCHNORM_MOVING_AVERAGE_DECAY = 0.9997

# The decay to use for the moving average.
MOVING_AVERAGE_DECAY = 0.9999


def inference(images, num_classes, for_training=False, restore_logits=True,
              scope=None):
  """Build Inception v3 model architecture.

  See here for reference: http://arxiv.org/abs/1512.00567

  Args:
    images: Images returned from inputs() or distorted_inputs().
    num_classes: number of classes
    for_training: If set to `True`, build the inference model for training.
      Kernels that operate differently for inference during training
      e.g. dropout, are appropriately configured.
    restore_logits: whether or not the logits layers should be restored.
      Useful for fine-tuning a model with different num_classes.
    scope: optional prefix string identifying the ImageNet tower.

  Returns:
    Logits. 2-D float Tensor.
    Auxiliary Logits. 2-D float Tensor of side-head. Used for training only.
  """
  # Parameters for BatchNorm.
  batch_norm_params = {
      # Decay for the moving averages.
      'decay': BATCHNORM_MOVING_AVERAGE_DECAY,
      # epsilon to prevent 0s in variance.
      'epsilon': 0.001,
  }
  # Set weight_decay for weights in Conv and FC layers.
  with slim.arg_scope([slim.ops.conv2d, slim.ops.fc], weight_decay=0.00004):
    with slim.arg_scope([slim.ops.conv2d],
                        stddev=0.1,
                        activation=tf.nn.relu,
                        batch_norm_params=batch_norm_params):
      logits, endpoints = slim.inception.inception_v3(
          images,
          dropout_keep_prob=0.8,
          num_classes=num_classes,
          is_training=for_training,
          restore_logits=restore_logits,
          scope=scope)

  # Add summaries for viewing model statistics on TensorBoard.
  _activation_summaries(endpoints)

  # Grab the logits associated with the side head. Employed during training.
  auxiliary_logits = endpoints['aux_logits']

  return logits, auxiliary_logits


def loss(logits, labels, batch_size=None):
  """Adds all losses for the model.

  Note the final loss is not returned. Instead, the list of losses are collected
  by slim.losses. The losses are accumulated in tower_loss() and summed to
  calculate the total loss.

  Args:
    logits: List of logits from inference(). Each entry is a 2-D float Tensor.
    labels: Labels from distorted_inputs or inputs(). 1-D tensor
            of shape [batch_size]
    batch_size: integer
  """
  if not batch_size:
    batch_size = FLAGS.batch_size

  # Reshape the labels into a dense Tensor of
  # shape [FLAGS.batch_size, num_classes].
  sparse_labels = tf.reshape(labels, [batch_size, 1])
  indices = tf.reshape(tf.range(batch_size), [batch_size, 1])
  concated = tf.concat(1, [indices, sparse_labels])
  num_classes = logits[0].get_shape()[-1].value
  dense_labels = tf.sparse_to_dense(concated,
                                    [batch_size, num_classes],
                                    1.0, 0.0)

  # Cross entropy loss for the main softmax prediction.
  slim.losses.cross_entropy_loss(logits[0],
                                 dense_labels,
                                 label_smoothing=0.1,
                                 weight=1.0)

  # Cross entropy loss for the auxiliary softmax head.
  slim.losses.cross_entropy_loss(logits[1],
                                 dense_labels,
                                 label_smoothing=0.1,
                                 weight=0.4,
                                 scope='aux_loss')


def _activation_summary(x):
  """Helper to create summaries for activations.

  Creates a summary that provides a histogram of activations.
  Creates a summary that measure the sparsity of activations.

  Args:
    x: Tensor
  """
  # Remove 'tower_[0-9]/' from the name in case this is a multi-GPU training
  # session. This helps the clarity of presentation on tensorboard.
  tensor_name = re.sub('%s_[0-9]*/' % TOWER_NAME, '', x.op.name)
  tf.histogram_summary(tensor_name + '/activations', x)
  tf.scalar_summary(tensor_name + '/sparsity', tf.nn.zero_fraction(x))


def _activation_summaries(endpoints):
  with tf.name_scope('summaries'):
    for act in endpoints.values():
      _activation_summary(act)

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Small library that points to the flowers data set.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function



from inception.dataset import Dataset


class FlowersData(Dataset):
  """Flowers data set."""

  def __init__(self, subset):
    super(FlowersData, self).__init__('Flowers', subset)

  def num_classes(self):
    """Returns the number of classes in the data set."""
    return 5

  def num_examples_per_epoch(self):
    """Returns the number of examples in the data subset."""
    if self.subset == 'train':
      return 3170
    if self.subset == 'validation':
      return 500

  def download_message(self):
    """Instruction to download and extract the tarball from Flowers website."""

    print('Failed to find any Flowers %s files'% self.subset)
    print('')
    print('If you have already downloaded and processed the data, then make '
          'sure to set --data_dir to point to the directory containing the '
          'location of the sharded TFRecords.\n')
    print('Please see README.md for instructions on how to build '
          'the flowers dataset using download_and_preprocess_flowers.\n')

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""A library to evaluate Inception on a single GPU.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
import math
import os.path
import time


import numpy as np
import tensorflow as tf

from inception import image_processing
from inception import inception_model as inception


FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_string('eval_dir', '/tmp/imagenet_eval',
                           """Directory where to write event logs.""")
tf.app.flags.DEFINE_string('checkpoint_dir', '/tmp/imagenet_train',
                           """Directory where to read model checkpoints.""")

# Flags governing the frequency of the eval.
tf.app.flags.DEFINE_integer('eval_interval_secs', 60 * 5,
                            """How often to run the eval.""")
tf.app.flags.DEFINE_boolean('run_once', False,
                            """Whether to run eval only once.""")

# Flags governing the data used for the eval.
tf.app.flags.DEFINE_integer('num_examples', 50000,
                            """Number of examples to run. Note that the eval """
                            """ImageNet dataset contains 50000 examples.""")
tf.app.flags.DEFINE_string('subset', 'validation',
                           """Either 'validation' or 'train'.""")


def _eval_once(saver, summary_writer, top_1_op, top_5_op, summary_op):
  """Runs Eval once.

  Args:
    saver: Saver.
    summary_writer: Summary writer.
    top_1_op: Top 1 op.
    top_5_op: Top 5 op.
    summary_op: Summary op.
  """
  with tf.Session() as sess:
    ckpt = tf.train.get_checkpoint_state(FLAGS.checkpoint_dir)
    if ckpt and ckpt.model_checkpoint_path:
      if os.path.isabs(ckpt.model_checkpoint_path):
        # Restores from checkpoint with absolute path.
        saver.restore(sess, ckpt.model_checkpoint_path)
      else:
        # Restores from checkpoint with relative path.
        saver.restore(sess, os.path.join(FLAGS.checkpoint_dir,
                                         ckpt.model_checkpoint_path))

      # Assuming model_checkpoint_path looks something like:
      #   /my-favorite-path/imagenet_train/model.ckpt-0,
      # extract global_step from it.
      global_step = ckpt.model_checkpoint_path.split('/')[-1].split('-')[-1]
      print('Succesfully loaded model from %s at step=%s.' %
            (ckpt.model_checkpoint_path, global_step))
    else:
      print('No checkpoint file found')
      return

    # Start the queue runners.
    coord = tf.train.Coordinator()
    try:
      threads = []
      for qr in tf.get_collection(tf.GraphKeys.QUEUE_RUNNERS):
        threads.extend(qr.create_threads(sess, coord=coord, daemon=True,
                                         start=True))

      num_iter = int(math.ceil(FLAGS.num_examples / FLAGS.batch_size))
      # Counts the number of correct predictions.
      count_top_1 = 0.0
      count_top_5 = 0.0
      total_sample_count = num_iter * FLAGS.batch_size
      step = 0

      print('%s: starting evaluation on (%s).' % (datetime.now(), FLAGS.subset))
      start_time = time.time()
      while step < num_iter and not coord.should_stop():
        top_1, top_5 = sess.run([top_1_op, top_5_op])
        count_top_1 += np.sum(top_1)
        count_top_5 += np.sum(top_5)
        step += 1
        if step % 20 == 0:
          duration = time.time() - start_time
          sec_per_batch = duration / 20.0
          examples_per_sec = FLAGS.batch_size / sec_per_batch
          print('%s: [%d batches out of %d] (%.1f examples/sec; %.3f'
                'sec/batch)' % (datetime.now(), step, num_iter,
                                examples_per_sec, sec_per_batch))
          start_time = time.time()

      # Compute precision @ 1.
      precision_at_1 = count_top_1 / total_sample_count
      recall_at_5 = count_top_5 / total_sample_count
      print('%s: precision @ 1 = %.4f recall @ 5 = %.4f [%d examples]' %
            (datetime.now(), precision_at_1, recall_at_5, total_sample_count))

      summary = tf.Summary()
      summary.ParseFromString(sess.run(summary_op))
      summary.value.add(tag='Precision @ 1', simple_value=precision_at_1)
      summary.value.add(tag='Recall @ 5', simple_value=recall_at_5)
      summary_writer.add_summary(summary, global_step)

    except Exception as e:  # pylint: disable=broad-except
      coord.request_stop(e)

    coord.request_stop()
    coord.join(threads, stop_grace_period_secs=10)


def evaluate(dataset):
  """Evaluate model on Dataset for a number of steps."""
  with tf.Graph().as_default():
    # Get images and labels from the dataset.
    images, labels = image_processing.inputs(dataset)

    # Number of classes in the Dataset label set plus 1.
    # Label 0 is reserved for an (unused) background class.
    num_classes = dataset.num_classes() + 1

    # Build a Graph that computes the logits predictions from the
    # inference model.
    logits, _ = inception.inference(images, num_classes)

    # Calculate predictions.
    top_1_op = tf.nn.in_top_k(logits, labels, 1)
    top_5_op = tf.nn.in_top_k(logits, labels, 5)

    # Restore the moving average version of the learned variables for eval.
    variable_averages = tf.train.ExponentialMovingAverage(
        inception.MOVING_AVERAGE_DECAY)
    variables_to_restore = variable_averages.variables_to_restore()
    saver = tf.train.Saver(variables_to_restore)

    # Build the summary operation based on the TF collection of Summaries.
    summary_op = tf.merge_all_summaries()

    graph_def = tf.get_default_graph().as_graph_def()
    summary_writer = tf.train.SummaryWriter(FLAGS.eval_dir,
                                            graph_def=graph_def)

    while True:
      _eval_once(saver, summary_writer, top_1_op, top_5_op, summary_op)
      if FLAGS.run_once:
        break
      time.sleep(FLAGS.eval_interval_secs)

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Read and preprocess image data.

 Image processing occurs on a single image at a time. Image are read and
 preprocessed in parallel across multiple threads. The resulting images
 are concatenated together to form a single batch for training or evaluation.

 -- Provide processed image data for a network:
 inputs: Construct batches of evaluation examples of images.
 distorted_inputs: Construct batches of training examples of images.
 batch_inputs: Construct batches of training or evaluation examples of images.

 -- Data processing:
 parse_example_proto: Parses an Example proto containing a training example
   of an image.

 -- Image decoding:
 decode_jpeg: Decode a JPEG encoded string into a 3-D float32 Tensor.

 -- Image preprocessing:
 image_preprocessing: Decode and preprocess one image for evaluation or training
 distort_image: Distort one image for training a network.
 eval_image: Prepare one image for evaluation.
 distort_color: Distort the color in one image for training.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_integer('batch_size', 32,
                            """Number of images to process in a batch.""")
tf.app.flags.DEFINE_integer('image_size', 299,
                            """Provide square images of this size.""")
tf.app.flags.DEFINE_integer('num_preprocess_threads', 4,
                            """Number of preprocessing threads per tower. """
                            """Please make this a multiple of 4.""")
tf.app.flags.DEFINE_integer('num_readers', 4,
                            """Number of parallel readers during train.""")

# Images are preprocessed asynchronously using multiple threads specified by
# --num_preprocss_threads and the resulting processed images are stored in a
# random shuffling queue. The shuffling queue dequeues --batch_size images
# for processing on a given Inception tower. A larger shuffling queue guarantees
# better mixing across examples within a batch and results in slightly higher
# predictive performance in a trained model. Empirically,
# --input_queue_memory_factor=16 works well. A value of 16 implies a queue size
# of 1024*16 images. Assuming RGB 299x299 images, this implies a queue size of
# 16GB. If the machine is memory limited, then decrease this factor to
# decrease the CPU memory footprint, accordingly.
tf.app.flags.DEFINE_integer('input_queue_memory_factor', 16,
                            """Size of the queue of preprocessed images. """
                            """Default is ideal but try smaller values, e.g. """
                            """4, 2 or 1, if host memory is constrained. See """
                            """comments in code for more details.""")


def inputs(dataset, batch_size=None, num_preprocess_threads=None):
  """Generate batches of ImageNet images for evaluation.

  Use this function as the inputs for evaluating a network.

  Note that some (minimal) image preprocessing occurs during evaluation
  including central cropping and resizing of the image to fit the network.

  Args:
    dataset: instance of Dataset class specifying the dataset.
    batch_size: integer, number of examples in batch
    num_preprocess_threads: integer, total number of preprocessing threads but
      None defaults to FLAGS.num_preprocess_threads.

  Returns:
    images: Images. 4D tensor of size [batch_size, FLAGS.image_size,
                                       image_size, 3].
    labels: 1-D integer Tensor of [FLAGS.batch_size].
  """
  if not batch_size:
    batch_size = FLAGS.batch_size

  # Force all input processing onto CPU in order to reserve the GPU for
  # the forward inference and back-propagation.
  with tf.device('/cpu:0'):
    images, labels = batch_inputs(
        dataset, batch_size, train=False,
        num_preprocess_threads=num_preprocess_threads,
        num_readers=1)

  return images, labels


def distorted_inputs(dataset, batch_size=None, num_preprocess_threads=None):
  """Generate batches of distorted versions of ImageNet images.

  Use this function as the inputs for training a network.

  Distorting images provides a useful technique for augmenting the data
  set during training in order to make the network invariant to aspects
  of the image that do not effect the label.

  Args:
    dataset: instance of Dataset class specifying the dataset.
    batch_size: integer, number of examples in batch
    num_preprocess_threads: integer, total number of preprocessing threads but
      None defaults to FLAGS.num_preprocess_threads.

  Returns:
    images: Images. 4D tensor of size [batch_size, FLAGS.image_size,
                                       FLAGS.image_size, 3].
    labels: 1-D integer Tensor of [batch_size].
  """
  if not batch_size:
    batch_size = FLAGS.batch_size

  # Force all input processing onto CPU in order to reserve the GPU for
  # the forward inference and back-propagation.
  with tf.device('/cpu:0'):
    images, labels = batch_inputs(
        dataset, batch_size, train=True,
        num_preprocess_threads=num_preprocess_threads,
        num_readers=FLAGS.num_readers)
  return images, labels


def decode_jpeg(image_buffer, scope=None):
  """Decode a JPEG string into one 3-D float image Tensor.

  Args:
    image_buffer: scalar string Tensor.
    scope: Optional scope for op_scope.
  Returns:
    3-D float Tensor with values ranging from [0, 1).
  """
  with tf.op_scope([image_buffer], scope, 'decode_jpeg'):
    # Decode the string as an RGB JPEG.
    # Note that the resulting image contains an unknown height and width
    # that is set dynamically by decode_jpeg. In other words, the height
    # and width of image is unknown at compile-time.
    image = tf.image.decode_jpeg(image_buffer, channels=3)

    # After this point, all image pixels reside in [0,1)
    # until the very end, when they're rescaled to (-1, 1).  The various
    # adjust_* ops all require this range for dtype float.
    image = tf.image.convert_image_dtype(image, dtype=tf.float32)
    return image


def distort_color(image, thread_id=0, scope=None):
  """Distort the color of the image.

  Each color distortion is non-commutative and thus ordering of the color ops
  matters. Ideally we would randomly permute the ordering of the color ops.
  Rather then adding that level of complication, we select a distinct ordering
  of color ops for each preprocessing thread.

  Args:
    image: Tensor containing single image.
    thread_id: preprocessing thread ID.
    scope: Optional scope for op_scope.
  Returns:
    color-distorted image
  """
  with tf.op_scope([image], scope, 'distort_color'):
    color_ordering = thread_id % 2

    if color_ordering == 0:
      image = tf.image.random_brightness(image, max_delta=32. / 255.)
      image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
      image = tf.image.random_hue(image, max_delta=0.2)
      image = tf.image.random_contrast(image, lower=0.5, upper=1.5)
    elif color_ordering == 1:
      image = tf.image.random_brightness(image, max_delta=32. / 255.)
      image = tf.image.random_contrast(image, lower=0.5, upper=1.5)
      image = tf.image.random_saturation(image, lower=0.5, upper=1.5)
      image = tf.image.random_hue(image, max_delta=0.2)

    # The random_* ops do not necessarily clamp.
    image = tf.clip_by_value(image, 0.0, 1.0)
    return image


def distort_image(image, height, width, bbox, thread_id=0, scope=None):
  """Distort one image for training a network.

  Distorting images provides a useful technique for augmenting the data
  set during training in order to make the network invariant to aspects
  of the image that do not effect the label.

  Args:
    image: 3-D float Tensor of image
    height: integer
    width: integer
    bbox: 3-D float Tensor of bounding boxes arranged [1, num_boxes, coords]
      where each coordinate is [0, 1) and the coordinates are arranged
      as [ymin, xmin, ymax, xmax].
    thread_id: integer indicating the preprocessing thread.
    scope: Optional scope for op_scope.
  Returns:
    3-D float Tensor of distorted image used for training.
  """
  with tf.op_scope([image, height, width, bbox], scope, 'distort_image'):
    # Each bounding box has shape [1, num_boxes, box coords] and
    # the coordinates are ordered [ymin, xmin, ymax, xmax].

    # Display the bounding box in the first thread only.
    if not thread_id:
      image_with_box = tf.image.draw_bounding_boxes(tf.expand_dims(image, 0),
                                                    bbox)
      tf.image_summary('image_with_bounding_boxes', image_with_box)

  # A large fraction of image datasets contain a human-annotated bounding
  # box delineating the region of the image containing the object of interest.
  # We choose to create a new bounding box for the object which is a randomly
  # distorted version of the human-annotated bounding box that obeys an allowed
  # range of aspect ratios, sizes and overlap with the human-annotated
  # bounding box. If no box is supplied, then we assume the bounding box is
  # the entire image.
    sample_distorted_bounding_box = tf.image.sample_distorted_bounding_box(
        tf.shape(image),
        bounding_boxes=bbox,
        min_object_covered=0.1,
        aspect_ratio_range=[0.75, 1.33],
        area_range=[0.05, 1.0],
        max_attempts=100,
        use_image_if_no_bounding_boxes=True)
    bbox_begin, bbox_size, distort_bbox = sample_distorted_bounding_box
    if not thread_id:
      image_with_distorted_box = tf.image.draw_bounding_boxes(
          tf.expand_dims(image, 0), distort_bbox)
      tf.image_summary('images_with_distorted_bounding_box',
                       image_with_distorted_box)

    # Crop the image to the specified bounding box.
    distorted_image = tf.slice(image, bbox_begin, bbox_size)

    # This resizing operation may distort the images because the aspect
    # ratio is not respected. We select a resize method in a round robin
    # fashion based on the thread number.
    # Note that ResizeMethod contains 4 enumerated resizing methods.
    resize_method = thread_id % 4
    distorted_image = tf.image.resize_images(distorted_image, height, width,
                                             resize_method)
    # Restore the shape since the dynamic slice based upon the bbox_size loses
    # the third dimension.
    distorted_image.set_shape([height, width, 3])
    if not thread_id:
      tf.image_summary('cropped_resized_image',
                       tf.expand_dims(distorted_image, 0))

    # Randomly flip the image horizontally.
    distorted_image = tf.image.random_flip_left_right(distorted_image)

    # Randomly distort the colors.
    distorted_image = distort_color(distorted_image, thread_id)

    if not thread_id:
      tf.image_summary('final_distorted_image',
                       tf.expand_dims(distorted_image, 0))
    return distorted_image


def eval_image(image, height, width, scope=None):
  """Prepare one image for evaluation.

  Args:
    image: 3-D float Tensor
    height: integer
    width: integer
    scope: Optional scope for op_scope.
  Returns:
    3-D float Tensor of prepared image.
  """
  with tf.op_scope([image, height, width], scope, 'eval_image'):
    # Crop the central region of the image with an area containing 87.5% of
    # the original image.
    image = tf.image.central_crop(image, central_fraction=0.875)

    # Resize the image to the original height and width.
    image = tf.expand_dims(image, 0)
    image = tf.image.resize_bilinear(image, [height, width],
                                     align_corners=False)
    image = tf.squeeze(image, [0])
    return image


def image_preprocessing(image_buffer, bbox, train, thread_id=0):
  """Decode and preprocess one image for evaluation or training.

  Args:
    image_buffer: JPEG encoded string Tensor
    bbox: 3-D float Tensor of bounding boxes arranged [1, num_boxes, coords]
      where each coordinate is [0, 1) and the coordinates are arranged as
      [ymin, xmin, ymax, xmax].
    train: boolean
    thread_id: integer indicating preprocessing thread

  Returns:
    3-D float Tensor containing an appropriately scaled image

  Raises:
    ValueError: if user does not provide bounding box
  """
  if bbox is None:
    raise ValueError('Please supply a bounding box.')

  image = decode_jpeg(image_buffer)
  height = FLAGS.image_size
  width = FLAGS.image_size

  if train:
    image = distort_image(image, height, width, bbox, thread_id)
  else:
    image = eval_image(image, height, width)

  # Finally, rescale to [-1,1] instead of [0, 1)
  image = tf.sub(image, 0.5)
  image = tf.mul(image, 2.0)
  return image


def parse_example_proto(example_serialized):
  """Parses an Example proto containing a training example of an image.

  The output of the build_image_data.py image preprocessing script is a dataset
  containing serialized Example protocol buffers. Each Example proto contains
  the following fields:

    image/height: 462
    image/width: 581
    image/colorspace: 'RGB'
    image/channels: 3
    image/class/label: 615
    image/class/synset: 'n03623198'
    image/class/text: 'knee pad'
    image/object/bbox/xmin: 0.1
    image/object/bbox/xmax: 0.9
    image/object/bbox/ymin: 0.2
    image/object/bbox/ymax: 0.6
    image/object/bbox/label: 615
    image/format: 'JPEG'
    image/filename: 'ILSVRC2012_val_00041207.JPEG'
    image/encoded: <JPEG encoded string>

  Args:
    example_serialized: scalar Tensor tf.string containing a serialized
      Example protocol buffer.

  Returns:
    image_buffer: Tensor tf.string containing the contents of a JPEG file.
    label: Tensor tf.int32 containing the label.
    bbox: 3-D float Tensor of bounding boxes arranged [1, num_boxes, coords]
      where each coordinate is [0, 1) and the coordinates are arranged as
      [ymin, xmin, ymax, xmax].
    text: Tensor tf.string containing the human-readable label.
  """
  # Dense features in Example proto.
  feature_map = {
      'image/encoded': tf.FixedLenFeature([], dtype=tf.string,
                                          default_value=''),
      'image/class/label': tf.FixedLenFeature([1], dtype=tf.int64,
                                              default_value=-1),
      'image/class/text': tf.FixedLenFeature([], dtype=tf.string,
                                             default_value=''),
  }
  sparse_float32 = tf.VarLenFeature(dtype=tf.float32)
  # Sparse features in Example proto.
  feature_map.update(
      {k: sparse_float32 for k in ['image/object/bbox/xmin',
                                   'image/object/bbox/ymin',
                                   'image/object/bbox/xmax',
                                   'image/object/bbox/ymax']})

  features = tf.parse_single_example(example_serialized, feature_map)
  label = tf.cast(features['image/class/label'], dtype=tf.int32)

  xmin = tf.expand_dims(features['image/object/bbox/xmin'].values, 0)
  ymin = tf.expand_dims(features['image/object/bbox/ymin'].values, 0)
  xmax = tf.expand_dims(features['image/object/bbox/xmax'].values, 0)
  ymax = tf.expand_dims(features['image/object/bbox/ymax'].values, 0)

  # Note that we impose an ordering of (y, x) just to make life difficult.
  bbox = tf.concat(0, [ymin, xmin, ymax, xmax])

  # Force the variable number of bounding boxes into the shape
  # [1, num_boxes, coords].
  bbox = tf.expand_dims(bbox, 0)
  bbox = tf.transpose(bbox, [0, 2, 1])

  return features['image/encoded'], label, bbox, features['image/class/text']


def batch_inputs(dataset, batch_size, train, num_preprocess_threads=None,
                 num_readers=1):
  """Contruct batches of training or evaluation examples from the image dataset.

  Args:
    dataset: instance of Dataset class specifying the dataset.
      See dataset.py for details.
    batch_size: integer
    train: boolean
    num_preprocess_threads: integer, total number of preprocessing threads
    num_readers: integer, number of parallel readers

  Returns:
    images: 4-D float Tensor of a batch of images
    labels: 1-D integer Tensor of [batch_size].

  Raises:
    ValueError: if data is not found
  """
  with tf.name_scope('batch_processing'):
    data_files = dataset.data_files()
    if data_files is None:
      raise ValueError('No data files found for this dataset')

    # Create filename_queue
    if train:
      filename_queue = tf.train.string_input_producer(data_files,
                                                      shuffle=True,
                                                      capacity=16)
    else:
      filename_queue = tf.train.string_input_producer(data_files,
                                                      shuffle=False,
                                                      capacity=1)
    if num_preprocess_threads is None:
      num_preprocess_threads = FLAGS.num_preprocess_threads

    if num_preprocess_threads % 4:
      raise ValueError('Please make num_preprocess_threads a multiple '
                       'of 4 (%d % 4 != 0).', num_preprocess_threads)

    if num_readers is None:
      num_readers = FLAGS.num_readers

    if num_readers < 1:
      raise ValueError('Please make num_readers at least 1')

    # Approximate number of examples per shard.
    examples_per_shard = 1024
    # Size the random shuffle queue to balance between good global
    # mixing (more examples) and memory use (fewer examples).
    # 1 image uses 299*299*3*4 bytes = 1MB
    # The default input_queue_memory_factor is 16 implying a shuffling queue
    # size: examples_per_shard * 16 * 1MB = 17.6GB
    min_queue_examples = examples_per_shard * FLAGS.input_queue_memory_factor
    if train:
      examples_queue = tf.RandomShuffleQueue(
          capacity=min_queue_examples + 3 * batch_size,
          min_after_dequeue=min_queue_examples,
          dtypes=[tf.string])
    else:
      examples_queue = tf.FIFOQueue(
          capacity=examples_per_shard + 3 * batch_size,
          dtypes=[tf.string])

    # Create multiple readers to populate the queue of examples.
    if num_readers > 1:
      enqueue_ops = []
      for _ in range(num_readers):
        reader = dataset.reader()
        _, value = reader.read(filename_queue)
        enqueue_ops.append(examples_queue.enqueue([value]))

      tf.train.queue_runner.add_queue_runner(
          tf.train.queue_runner.QueueRunner(examples_queue, enqueue_ops))
      example_serialized = examples_queue.dequeue()
    else:
      reader = dataset.reader()
      _, example_serialized = reader.read(filename_queue)

    images_and_labels = []
    for thread_id in range(num_preprocess_threads):
      # Parse a serialized Example proto to extract the image and metadata.
      image_buffer, label_index, bbox, _ = parse_example_proto(
          example_serialized)
      image = image_preprocessing(image_buffer, bbox, train, thread_id)
      images_and_labels.append([image, label_index])

    images, label_index_batch = tf.train.batch_join(
        images_and_labels,
        batch_size=batch_size,
        capacity=2 * num_preprocess_threads * batch_size)

    # Reshape images into these desired dimensions.
    height = FLAGS.image_size
    width = FLAGS.image_size
    depth = 3

    images = tf.cast(images, tf.float32)
    images = tf.reshape(images, shape=[batch_size, height, width, depth])

    # Display the training images in the visualizer.
    tf.image_summary('images', images)

    return images, tf.reshape(label_index_batch, [batch_size])

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""A binary to evaluate Inception on the flowers data set.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import tensorflow as tf

from inception import inception_eval
from inception.flowers_data import FlowersData

FLAGS = tf.app.flags.FLAGS


def main(unused_argv=None):
  dataset = FlowersData(subset=FLAGS.subset)
  assert dataset.data_files()
  if tf.gfile.Exists(FLAGS.eval_dir):
    tf.gfile.DeleteRecursively(FLAGS.eval_dir)
  tf.gfile.MakeDirs(FLAGS.eval_dir)
  inception_eval.evaluate(dataset)


if __name__ == '__main__':
  tf.app.run()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Contains the new arg_scope used for TF-Slim ops.

  Allows one to define models much more compactly by eliminating boilerplate
  code. This is accomplished through the use of argument scoping (arg_scope).

  Example of how to use scopes.arg_scope:

  with scopes.arg_scope(ops.conv2d, padding='SAME',
                      stddev=0.01, weight_decay=0.0005):
    net = ops.conv2d(inputs, 64, [11, 11], 4, padding='VALID', scope='conv1')
    net = ops.conv2d(net, 256, [5, 5], scope='conv2')

  The first call to conv2d will use predefined args:
    ops.conv2d(inputs, 64, [11, 11], 4, padding='VALID',
              stddev=0.01, weight_decay=0.0005, scope='conv1')

  The second call to Conv will overwrite padding:
    ops.conv2d(inputs, 256, [5, 5], padding='SAME',
               stddev=0.01, weight_decay=0.0005, scope='conv2')

  Example of how to reuse an arg_scope:
  with scopes.arg_scope(ops.conv2d, padding='SAME',
                      stddev=0.01, weight_decay=0.0005) as conv2d_arg_scope:
    net = ops.conv2d(net, 256, [5, 5], scope='conv1')
    ....

  with scopes.arg_scope(conv2d_arg_scope):
    net = ops.conv2d(net, 256, [5, 5], scope='conv2')

  Example of how to use scopes.add_arg_scope:

  @scopes.add_arg_scope
  def conv2d(*args, **kwargs)
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import contextlib
import functools

from tensorflow.python.framework import ops

_ARGSTACK_KEY = ("__arg_stack",)

_DECORATED_OPS = set()


def _get_arg_stack():
  stack = ops.get_collection(_ARGSTACK_KEY)
  if stack:
    return stack[0]
  else:
    stack = [{}]
    ops.add_to_collection(_ARGSTACK_KEY, stack)
    return stack


def _current_arg_scope():
  stack = _get_arg_stack()
  return stack[-1]


def _add_op(op):
  key_op = (op.__module__, op.__name__)
  if key_op not in _DECORATED_OPS:
    _DECORATED_OPS.add(key_op)


@contextlib.contextmanager
def arg_scope(list_ops_or_scope, **kwargs):
  """Stores the default arguments for the given set of list_ops.

  For usage, please see examples at top of the file.

  Args:
    list_ops_or_scope: List or tuple of operations to set argument scope for or
      a dictionary containg the current scope. When list_ops_or_scope is a dict,
      kwargs must be empty. When list_ops_or_scope is a list or tuple, then
      every op in it need to be decorated with @add_arg_scope to work.
    **kwargs: keyword=value that will define the defaults for each op in
              list_ops. All the ops need to accept the given set of arguments.

  Yields:
    the current_scope, which is a dictionary of {op: {arg: value}}
  Raises:
    TypeError: if list_ops is not a list or a tuple.
    ValueError: if any op in list_ops has not be decorated with @add_arg_scope.
  """
  if isinstance(list_ops_or_scope, dict):
    # Assumes that list_ops_or_scope is a scope that is being reused.
    if kwargs:
      raise ValueError("When attempting to re-use a scope by suppling a"
                       "dictionary, kwargs must be empty.")
    current_scope = list_ops_or_scope.copy()
    try:
      _get_arg_stack().append(current_scope)
      yield current_scope
    finally:
      _get_arg_stack().pop()
  else:
    # Assumes that list_ops_or_scope is a list/tuple of ops with kwargs.
    if not isinstance(list_ops_or_scope, (list, tuple)):
      raise TypeError("list_ops_or_scope must either be a list/tuple or reused"
                      "scope (i.e. dict)")
    try:
      current_scope = _current_arg_scope().copy()
      for op in list_ops_or_scope:
        key_op = (op.__module__, op.__name__)
        if not has_arg_scope(op):
          raise ValueError("%s is not decorated with @add_arg_scope", key_op)
        if key_op in current_scope:
          current_kwargs = current_scope[key_op].copy()
          current_kwargs.update(kwargs)
          current_scope[key_op] = current_kwargs
        else:
          current_scope[key_op] = kwargs.copy()
      _get_arg_stack().append(current_scope)
      yield current_scope
    finally:
      _get_arg_stack().pop()


def add_arg_scope(func):
  """Decorates a function with args so it can be used within an arg_scope.

  Args:
    func: function to decorate.

  Returns:
    A tuple with the decorated function func_with_args().
  """
  @functools.wraps(func)
  def func_with_args(*args, **kwargs):
    current_scope = _current_arg_scope()
    current_args = kwargs
    key_func = (func.__module__, func.__name__)
    if key_func in current_scope:
      current_args = current_scope[key_func].copy()
      current_args.update(kwargs)
    return func(*args, **current_args)
  _add_op(func)
  return func_with_args


def has_arg_scope(func):
  """Checks whether a func has been decorated with @add_arg_scope or not.

  Args:
    func: function to check.

  Returns:
    a boolean.
  """
  key_op = (func.__module__, func.__name__)
  return key_op in _DECORATED_OPS

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for inception."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

from inception.slim import slim


def get_variables(scope=None):
  return slim.variables.get_variables(scope)


def get_variables_by_name(name):
  return slim.variables.get_variables_by_name(name)


class CollectionsTest(tf.test.TestCase):

  def testVariables(self):
    batch_size = 5
    height, width = 299, 299
    with self.test_session():
      inputs = tf.random_uniform((batch_size, height, width, 3))
      with slim.arg_scope([slim.ops.conv2d],
                          batch_norm_params={'decay': 0.9997}):
        slim.inception.inception_v3(inputs)
      self.assertEqual(len(get_variables()), 388)
      self.assertEqual(len(get_variables_by_name('weights')), 98)
      self.assertEqual(len(get_variables_by_name('biases')), 2)
      self.assertEqual(len(get_variables_by_name('beta')), 96)
      self.assertEqual(len(get_variables_by_name('gamma')), 0)
      self.assertEqual(len(get_variables_by_name('moving_mean')), 96)
      self.assertEqual(len(get_variables_by_name('moving_variance')), 96)

  def testVariablesWithoutBatchNorm(self):
    batch_size = 5
    height, width = 299, 299
    with self.test_session():
      inputs = tf.random_uniform((batch_size, height, width, 3))
      with slim.arg_scope([slim.ops.conv2d],
                          batch_norm_params=None):
        slim.inception.inception_v3(inputs)
      self.assertEqual(len(get_variables()), 196)
      self.assertEqual(len(get_variables_by_name('weights')), 98)
      self.assertEqual(len(get_variables_by_name('biases')), 98)
      self.assertEqual(len(get_variables_by_name('beta')), 0)
      self.assertEqual(len(get_variables_by_name('gamma')), 0)
      self.assertEqual(len(get_variables_by_name('moving_mean')), 0)
      self.assertEqual(len(get_variables_by_name('moving_variance')), 0)

  def testVariablesByLayer(self):
    batch_size = 5
    height, width = 299, 299
    with self.test_session():
      inputs = tf.random_uniform((batch_size, height, width, 3))
      with slim.arg_scope([slim.ops.conv2d],
                          batch_norm_params={'decay': 0.9997}):
        slim.inception.inception_v3(inputs)
      self.assertEqual(len(get_variables()), 388)
      self.assertEqual(len(get_variables('conv0')), 4)
      self.assertEqual(len(get_variables('conv1')), 4)
      self.assertEqual(len(get_variables('conv2')), 4)
      self.assertEqual(len(get_variables('conv3')), 4)
      self.assertEqual(len(get_variables('conv4')), 4)
      self.assertEqual(len(get_variables('mixed_35x35x256a')), 28)
      self.assertEqual(len(get_variables('mixed_35x35x288a')), 28)
      self.assertEqual(len(get_variables('mixed_35x35x288b')), 28)
      self.assertEqual(len(get_variables('mixed_17x17x768a')), 16)
      self.assertEqual(len(get_variables('mixed_17x17x768b')), 40)
      self.assertEqual(len(get_variables('mixed_17x17x768c')), 40)
      self.assertEqual(len(get_variables('mixed_17x17x768d')), 40)
      self.assertEqual(len(get_variables('mixed_17x17x768e')), 40)
      self.assertEqual(len(get_variables('mixed_8x8x2048a')), 36)
      self.assertEqual(len(get_variables('mixed_8x8x2048b')), 36)
      self.assertEqual(len(get_variables('logits')), 2)
      self.assertEqual(len(get_variables('aux_logits')), 10)

  def testVariablesToRestore(self):
    batch_size = 5
    height, width = 299, 299
    with self.test_session():
      inputs = tf.random_uniform((batch_size, height, width, 3))
      with slim.arg_scope([slim.ops.conv2d],
                          batch_norm_params={'decay': 0.9997}):
        slim.inception.inception_v3(inputs)
      variables_to_restore = tf.get_collection(
          slim.variables.VARIABLES_TO_RESTORE)
      self.assertEqual(len(variables_to_restore), 388)
      self.assertListEqual(variables_to_restore, get_variables())

  def testVariablesToRestoreWithoutLogits(self):
    batch_size = 5
    height, width = 299, 299
    with self.test_session():
      inputs = tf.random_uniform((batch_size, height, width, 3))
      with slim.arg_scope([slim.ops.conv2d],
                          batch_norm_params={'decay': 0.9997}):
        slim.inception.inception_v3(inputs, restore_logits=False)
      variables_to_restore = tf.get_collection(
          slim.variables.VARIABLES_TO_RESTORE)
      self.assertEqual(len(variables_to_restore), 384)

  def testRegularizationLosses(self):
    batch_size = 5
    height, width = 299, 299
    with self.test_session():
      inputs = tf.random_uniform((batch_size, height, width, 3))
      with slim.arg_scope([slim.ops.conv2d, slim.ops.fc], weight_decay=0.00004):
        slim.inception.inception_v3(inputs)
      losses = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)
      self.assertEqual(len(losses), len(get_variables_by_name('weights')))

  def testTotalLossWithoutRegularization(self):
    batch_size = 5
    height, width = 299, 299
    num_classes = 1001
    with self.test_session():
      inputs = tf.random_uniform((batch_size, height, width, 3))
      dense_labels = tf.random_uniform((batch_size, num_classes))
      with slim.arg_scope([slim.ops.conv2d, slim.ops.fc], weight_decay=0):
        logits, end_points = slim.inception.inception_v3(
            inputs,
            num_classes=num_classes)
        # Cross entropy loss for the main softmax prediction.
        slim.losses.cross_entropy_loss(logits,
                                       dense_labels,
                                       label_smoothing=0.1,
                                       weight=1.0)
        # Cross entropy loss for the auxiliary softmax head.
        slim.losses.cross_entropy_loss(end_points['aux_logits'],
                                       dense_labels,
                                       label_smoothing=0.1,
                                       weight=0.4,
                                       scope='aux_loss')
      losses = tf.get_collection(slim.losses.LOSSES_COLLECTION)
      self.assertEqual(len(losses), 2)

  def testTotalLossWithRegularization(self):
    batch_size = 5
    height, width = 299, 299
    num_classes = 1000
    with self.test_session():
      inputs = tf.random_uniform((batch_size, height, width, 3))
      dense_labels = tf.random_uniform((batch_size, num_classes))
      with slim.arg_scope([slim.ops.conv2d, slim.ops.fc], weight_decay=0.00004):
        logits, end_points = slim.inception.inception_v3(inputs, num_classes)
        # Cross entropy loss for the main softmax prediction.
        slim.losses.cross_entropy_loss(logits,
                                       dense_labels,
                                       label_smoothing=0.1,
                                       weight=1.0)
        # Cross entropy loss for the auxiliary softmax head.
        slim.losses.cross_entropy_loss(end_points['aux_logits'],
                                       dense_labels,
                                       label_smoothing=0.1,
                                       weight=0.4,
                                       scope='aux_loss')
      losses = tf.get_collection(slim.losses.LOSSES_COLLECTION)
      self.assertEqual(len(losses), 2)
      reg_losses = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)
      self.assertEqual(len(reg_losses), 98)


if __name__ == '__main__':
  tf.test.main()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Contains convenience wrappers for creating variables in TF-Slim.

The variables module is typically used for defining model variables from the
ops routines (see slim.ops). Such variables are used for training, evaluation
and inference of models.

All the variables created through this module would be added to the
MODEL_VARIABLES collection, if you create a model variable outside slim, it can
be added with slim.variables.add_variable(external_variable, reuse).

Usage:
  weights_initializer = tf.truncated_normal_initializer(stddev=0.01)
  l2_regularizer = lambda t: losses.l2_loss(t, weight=0.0005)
  weights = variables.variable('weights',
                               shape=[100, 100],
                               initializer=weights_initializer,
                               regularizer=l2_regularizer,
                               device='/cpu:0')

  biases = variables.variable('biases',
                              shape=[100],
                              initializer=tf.zeros_initializer,
                              device='/cpu:0')

  # More complex example.

  net = slim.ops.conv2d(input, 32, [3, 3], scope='conv1')
  net = slim.ops.conv2d(net, 64, [3, 3], scope='conv2')
  with slim.arg_scope([variables.variable], restore=False):
    net = slim.ops.conv2d(net, 64, [3, 3], scope='conv3')

  # Get all model variables from all the layers.
  model_variables = slim.variables.get_variables()

  # Get all model variables from a specific the layer, i.e 'conv1'.
  conv1_variables = slim.variables.get_variables('conv1')

  # Get all weights from all the layers.
  weights = slim.variables.get_variables_by_name('weights')

  # Get all bias from all the layers.
  biases = slim.variables.get_variables_by_name('biases')

  # Get all variables to restore.
  # (i.e. only those created by 'conv1' and 'conv2')
  variables_to_restore = slim.variables.get_variables_to_restore()

************************************************
* Initializing model variables from a checkpoint
************************************************

# Create some variables.
v1 = slim.variables.variable(name="v1", ..., restore=False)
v2 = slim.variables.variable(name="v2", ...) # By default restore=True
...
# The list of variables to restore should only contain 'v2'.
variables_to_restore = slim.variables.get_variables_to_restore()
restorer = tf.train.Saver(variables_to_restore)
with tf.Session() as sess:
  # Restore variables from disk.
  restorer.restore(sess, "/tmp/model.ckpt")
  print("Model restored.")
  # Do some work with the model
  ...

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

from tensorflow.core.framework import graph_pb2
from inception.slim import scopes

# Collection containing all the variables created using slim.variables
MODEL_VARIABLES = '_model_variables_'

# Collection containing the slim.variables that are created with restore=True.
VARIABLES_TO_RESTORE = '_variables_to_restore_'


def add_variable(var, restore=True):
  """Adds a variable to the MODEL_VARIABLES collection.

    Optionally it will add the variable to  the VARIABLES_TO_RESTORE collection.
  Args:
    var: a variable.
    restore: whether the variable should be added to the
      VARIABLES_TO_RESTORE collection.

  """
  collections = [MODEL_VARIABLES]
  if restore:
    collections.append(VARIABLES_TO_RESTORE)
  for collection in collections:
    if var not in tf.get_collection(collection):
      tf.add_to_collection(collection, var)


def get_variables(scope=None, suffix=None):
  """Gets the list of variables, filtered by scope and/or suffix.

  Args:
    scope: an optional scope for filtering the variables to return.
    suffix: an optional suffix for filtering the variables to return.

  Returns:
    a copied list of variables with scope and suffix.
  """
  candidates = tf.get_collection(MODEL_VARIABLES, scope)[:]
  if suffix is not None:
    candidates = [var for var in candidates if var.op.name.endswith(suffix)]
  return candidates


def get_variables_to_restore():
  """Gets the list of variables to restore.

  Returns:
    a copied list of variables.
  """
  return tf.get_collection(VARIABLES_TO_RESTORE)[:]


def get_variables_by_name(given_name, scope=None):
  """Gets the list of variables that were given that name.

  Args:
    given_name: name given to the variable without scope.
    scope: an optional scope for filtering the variables to return.

  Returns:
    a copied list of variables with the given name and prefix.
  """
  return get_variables(scope=scope, suffix=given_name)


def get_unique_variable(name):
  """Gets the variable uniquely identified by that name.

  Args:
    name: a name that uniquely identifies the variable.

  Returns:
    a tensorflow variable.

  Raises:
    ValueError: if no variable uniquely identified by the name exists.
  """
  candidates = tf.get_collection(tf.GraphKeys.VARIABLES, name)
  if not candidates:
    raise ValueError('Couldnt find variable %s' % name)

  for candidate in candidates:
    if candidate.op.name == name:
      return candidate
  raise ValueError('Variable %s does not uniquely identify a variable', name)


class VariableDeviceChooser(object):
  """Slim device chooser for variables.

  When using a parameter server it will assign them in a round-robin fashion.
  When not using a parameter server it allows GPU:0 placement otherwise CPU:0.
  """

  def __init__(self,
               num_parameter_servers=0,
               ps_device='/job:ps',
               placement='CPU:0'):
    """Initialize VariableDeviceChooser.

    Args:
      num_parameter_servers: number of parameter servers.
      ps_device: string representing the parameter server device.
      placement: string representing the placement of the variable either CPU:0
        or GPU:0. When using parameter servers forced to CPU:0.
    """
    self._num_ps = num_parameter_servers
    self._ps_device = ps_device
    self._placement = placement if num_parameter_servers == 0 else 'CPU:0'
    self._next_task_id = 0

  def __call__(self, op):
    device_string = ''
    if self._num_ps > 0:
      task_id = self._next_task_id
      self._next_task_id = (self._next_task_id + 1) % self._num_ps
      device_string = '%s/task:%d' % (self._ps_device, task_id)
    device_string += '/%s' % self._placement
    return device_string


# TODO(sguada) Remove once get_variable is able to colocate op.devices.
def variable_device(device, name):
  """Fix the variable device to colocate its ops."""
  if callable(device):
    var_name = tf.get_variable_scope().name + '/' + name
    var_def = graph_pb2.NodeDef(name=var_name, op='Variable')
    device = device(var_def)
  if device is None:
    device = ''
  return device


@scopes.add_arg_scope
def global_step(device=''):
  """Returns the global step variable.

  Args:
    device: Optional device to place the variable. It can be an string or a
      function that is called to get the device for the variable.

  Returns:
    the tensor representing the global step variable.
  """
  global_step_ref = tf.get_collection(tf.GraphKeys.GLOBAL_STEP)
  if global_step_ref:
    return global_step_ref[0]
  else:
    collections = [
        VARIABLES_TO_RESTORE,
        tf.GraphKeys.VARIABLES,
        tf.GraphKeys.GLOBAL_STEP,
    ]
    # Get the device for the variable.
    with tf.device(variable_device(device, 'global_step')):
      return tf.get_variable('global_step', shape=[], dtype=tf.int64,
                             initializer=tf.zeros_initializer,
                             trainable=False, collections=collections)


@scopes.add_arg_scope
def variable(name, shape=None, dtype=tf.float32, initializer=None,
             regularizer=None, trainable=True, collections=None, device='',
             restore=True):
  """Gets an existing variable with these parameters or creates a new one.

    It also add itself to a group with its name.

  Args:
    name: the name of the new or existing variable.
    shape: shape of the new or existing variable.
    dtype: type of the new or existing variable (defaults to `DT_FLOAT`).
    initializer: initializer for the variable if one is created.
    regularizer: a (Tensor -> Tensor or None) function; the result of
        applying it on a newly created variable will be added to the collection
        GraphKeys.REGULARIZATION_LOSSES and can be used for regularization.
    trainable: If `True` also add the variable to the graph collection
      `GraphKeys.TRAINABLE_VARIABLES` (see tf.Variable).
    collections: A list of collection names to which the Variable will be added.
      Note that the variable is always also added to the tf.GraphKeys.VARIABLES
      and MODEL_VARIABLES collections.
    device: Optional device to place the variable. It can be an string or a
      function that is called to get the device for the variable.
    restore: whether the variable should be added to the
      VARIABLES_TO_RESTORE collection.

  Returns:
    The created or existing variable.
  """
  collections = list(collections or [])

  # Make sure variables are added to tf.GraphKeys.VARIABLES and MODEL_VARIABLES
  collections += [tf.GraphKeys.VARIABLES, MODEL_VARIABLES]
  # Add to VARIABLES_TO_RESTORE if necessary
  if restore:
    collections.append(VARIABLES_TO_RESTORE)
  # Remove duplicates
  collections = set(collections)
  # Get the device for the variable.
  with tf.device(variable_device(device, name)):
    return tf.get_variable(name, shape=shape, dtype=dtype,
                           initializer=initializer, regularizer=regularizer,
                           trainable=trainable, collections=collections)

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for slim.inception."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

from inception.slim import inception_model as inception


class InceptionTest(tf.test.TestCase):

  def testBuildLogits(self):
    batch_size = 5
    height, width = 299, 299
    num_classes = 1000
    with self.test_session():
      inputs = tf.random_uniform((batch_size, height, width, 3))
      logits, _ = inception.inception_v3(inputs, num_classes)
      self.assertTrue(logits.op.name.startswith('logits'))
      self.assertListEqual(logits.get_shape().as_list(),
                           [batch_size, num_classes])

  def testBuildEndPoints(self):
    batch_size = 5
    height, width = 299, 299
    num_classes = 1000
    with self.test_session():
      inputs = tf.random_uniform((batch_size, height, width, 3))
      _, end_points = inception.inception_v3(inputs, num_classes)
      self.assertTrue('logits' in end_points)
      logits = end_points['logits']
      self.assertListEqual(logits.get_shape().as_list(),
                           [batch_size, num_classes])
      self.assertTrue('aux_logits' in end_points)
      aux_logits = end_points['aux_logits']
      self.assertListEqual(aux_logits.get_shape().as_list(),
                           [batch_size, num_classes])
      pre_pool = end_points['mixed_8x8x2048b']
      self.assertListEqual(pre_pool.get_shape().as_list(),
                           [batch_size, 8, 8, 2048])

  def testVariablesSetDevice(self):
    batch_size = 5
    height, width = 299, 299
    num_classes = 1000
    with self.test_session():
      inputs = tf.random_uniform((batch_size, height, width, 3))
      # Force all Variables to reside on the device.
      with tf.variable_scope('on_cpu'), tf.device('/cpu:0'):
        inception.inception_v3(inputs, num_classes)
      with tf.variable_scope('on_gpu'), tf.device('/gpu:0'):
        inception.inception_v3(inputs, num_classes)
      for v in tf.get_collection(tf.GraphKeys.VARIABLES, scope='on_cpu'):
        self.assertDeviceEqual(v.device, '/cpu:0')
      for v in tf.get_collection(tf.GraphKeys.VARIABLES, scope='on_gpu'):
        self.assertDeviceEqual(v.device, '/gpu:0')

  def testHalfSizeImages(self):
    batch_size = 5
    height, width = 150, 150
    num_classes = 1000
    with self.test_session():
      inputs = tf.random_uniform((batch_size, height, width, 3))
      logits, end_points = inception.inception_v3(inputs, num_classes)
      self.assertTrue(logits.op.name.startswith('logits'))
      self.assertListEqual(logits.get_shape().as_list(),
                           [batch_size, num_classes])
      pre_pool = end_points['mixed_8x8x2048b']
      self.assertListEqual(pre_pool.get_shape().as_list(),
                           [batch_size, 3, 3, 2048])

  def testUnknowBatchSize(self):
    batch_size = 1
    height, width = 299, 299
    num_classes = 1000
    with self.test_session() as sess:
      inputs = tf.placeholder(tf.float32, (None, height, width, 3))
      logits, _ = inception.inception_v3(inputs, num_classes)
      self.assertTrue(logits.op.name.startswith('logits'))
      self.assertListEqual(logits.get_shape().as_list(),
                           [None, num_classes])
      images = tf.random_uniform((batch_size, height, width, 3))
      sess.run(tf.initialize_all_variables())
      output = sess.run(logits, {inputs: images.eval()})
      self.assertEquals(output.shape, (batch_size, num_classes))

  def testEvaluation(self):
    batch_size = 2
    height, width = 299, 299
    num_classes = 1000
    with self.test_session() as sess:
      eval_inputs = tf.random_uniform((batch_size, height, width, 3))
      logits, _ = inception.inception_v3(eval_inputs, num_classes,
                                         is_training=False)
      predictions = tf.argmax(logits, 1)
      sess.run(tf.initialize_all_variables())
      output = sess.run(predictions)
      self.assertEquals(output.shape, (batch_size,))

  def testTrainEvalWithReuse(self):
    train_batch_size = 5
    eval_batch_size = 2
    height, width = 150, 150
    num_classes = 1000
    with self.test_session() as sess:
      train_inputs = tf.random_uniform((train_batch_size, height, width, 3))
      inception.inception_v3(train_inputs, num_classes)
      tf.get_variable_scope().reuse_variables()
      eval_inputs = tf.random_uniform((eval_batch_size, height, width, 3))
      logits, _ = inception.inception_v3(eval_inputs, num_classes,
                                         is_training=False)
      predictions = tf.argmax(logits, 1)
      sess.run(tf.initialize_all_variables())
      output = sess.run(predictions)
      self.assertEquals(output.shape, (eval_batch_size,))


if __name__ == '__main__':
  tf.test.main()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests slim.scopes."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import tensorflow as tf
from inception.slim import scopes


@scopes.add_arg_scope
def func1(*args, **kwargs):
  return (args, kwargs)


@scopes.add_arg_scope
def func2(*args, **kwargs):
  return (args, kwargs)


class ArgScopeTest(tf.test.TestCase):

  def testEmptyArgScope(self):
    with self.test_session():
      self.assertEqual(scopes._current_arg_scope(), {})

  def testCurrentArgScope(self):
    func1_kwargs = {'a': 1, 'b': None, 'c': [1]}
    key_op = (func1.__module__, func1.__name__)
    current_scope = {key_op: func1_kwargs.copy()}
    with self.test_session():
      with scopes.arg_scope([func1], a=1, b=None, c=[1]) as scope:
        self.assertDictEqual(scope, current_scope)

  def testCurrentArgScopeNested(self):
    func1_kwargs = {'a': 1, 'b': None, 'c': [1]}
    func2_kwargs = {'b': 2, 'd': [2]}
    key = lambda f: (f.__module__, f.__name__)
    current_scope = {key(func1): func1_kwargs.copy(),
                     key(func2): func2_kwargs.copy()}
    with self.test_session():
      with scopes.arg_scope([func1], a=1, b=None, c=[1]):
        with scopes.arg_scope([func2], b=2, d=[2]) as scope:
          self.assertDictEqual(scope, current_scope)

  def testReuseArgScope(self):
    func1_kwargs = {'a': 1, 'b': None, 'c': [1]}
    key_op = (func1.__module__, func1.__name__)
    current_scope = {key_op: func1_kwargs.copy()}
    with self.test_session():
      with scopes.arg_scope([func1], a=1, b=None, c=[1]) as scope1:
        pass
      with scopes.arg_scope(scope1) as scope:
        self.assertDictEqual(scope, current_scope)

  def testReuseArgScopeNested(self):
    func1_kwargs = {'a': 1, 'b': None, 'c': [1]}
    func2_kwargs = {'b': 2, 'd': [2]}
    key = lambda f: (f.__module__, f.__name__)
    current_scope1 = {key(func1): func1_kwargs.copy()}
    current_scope2 = {key(func1): func1_kwargs.copy(),
                      key(func2): func2_kwargs.copy()}
    with self.test_session():
      with scopes.arg_scope([func1], a=1, b=None, c=[1]) as scope1:
        with scopes.arg_scope([func2], b=2, d=[2]) as scope2:
          pass
      with scopes.arg_scope(scope1):
        self.assertDictEqual(scopes._current_arg_scope(), current_scope1)
      with scopes.arg_scope(scope2):
        self.assertDictEqual(scopes._current_arg_scope(), current_scope2)

  def testSimpleArgScope(self):
    func1_args = (0,)
    func1_kwargs = {'a': 1, 'b': None, 'c': [1]}
    with self.test_session():
      with scopes.arg_scope([func1], a=1, b=None, c=[1]):
        args, kwargs = func1(0)
        self.assertTupleEqual(args, func1_args)
        self.assertDictEqual(kwargs, func1_kwargs)

  def testSimpleArgScopeWithTuple(self):
    func1_args = (0,)
    func1_kwargs = {'a': 1, 'b': None, 'c': [1]}
    with self.test_session():
      with scopes.arg_scope((func1,), a=1, b=None, c=[1]):
        args, kwargs = func1(0)
        self.assertTupleEqual(args, func1_args)
        self.assertDictEqual(kwargs, func1_kwargs)

  def testOverwriteArgScope(self):
    func1_args = (0,)
    func1_kwargs = {'a': 1, 'b': 2, 'c': [1]}
    with scopes.arg_scope([func1], a=1, b=None, c=[1]):
      args, kwargs = func1(0, b=2)
      self.assertTupleEqual(args, func1_args)
      self.assertDictEqual(kwargs, func1_kwargs)

  def testNestedArgScope(self):
    func1_args = (0,)
    func1_kwargs = {'a': 1, 'b': None, 'c': [1]}
    with scopes.arg_scope([func1], a=1, b=None, c=[1]):
      args, kwargs = func1(0)
      self.assertTupleEqual(args, func1_args)
      self.assertDictEqual(kwargs, func1_kwargs)
      func1_kwargs['b'] = 2
      with scopes.arg_scope([func1], b=2):
        args, kwargs = func1(0)
        self.assertTupleEqual(args, func1_args)
        self.assertDictEqual(kwargs, func1_kwargs)

  def testSharedArgScope(self):
    func1_args = (0,)
    func1_kwargs = {'a': 1, 'b': None, 'c': [1]}
    with scopes.arg_scope([func1, func2], a=1, b=None, c=[1]):
      args, kwargs = func1(0)
      self.assertTupleEqual(args, func1_args)
      self.assertDictEqual(kwargs, func1_kwargs)
      args, kwargs = func2(0)
      self.assertTupleEqual(args, func1_args)
      self.assertDictEqual(kwargs, func1_kwargs)

  def testSharedArgScopeTuple(self):
    func1_args = (0,)
    func1_kwargs = {'a': 1, 'b': None, 'c': [1]}
    with scopes.arg_scope((func1, func2), a=1, b=None, c=[1]):
      args, kwargs = func1(0)
      self.assertTupleEqual(args, func1_args)
      self.assertDictEqual(kwargs, func1_kwargs)
      args, kwargs = func2(0)
      self.assertTupleEqual(args, func1_args)
      self.assertDictEqual(kwargs, func1_kwargs)

  def testPartiallySharedArgScope(self):
    func1_args = (0,)
    func1_kwargs = {'a': 1, 'b': None, 'c': [1]}
    func2_args = (1,)
    func2_kwargs = {'a': 1, 'b': None, 'd': [2]}
    with scopes.arg_scope([func1, func2], a=1, b=None):
      with scopes.arg_scope([func1], c=[1]), scopes.arg_scope([func2], d=[2]):
        args, kwargs = func1(0)
        self.assertTupleEqual(args, func1_args)
        self.assertDictEqual(kwargs, func1_kwargs)
        args, kwargs = func2(1)
        self.assertTupleEqual(args, func2_args)
        self.assertDictEqual(kwargs, func2_kwargs)

if __name__ == '__main__':
  tf.test.main()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""TF-Slim grouped API. Please see README.md for details and usage."""
# pylint: disable=unused-import

# Collapse tf-slim into a single namespace.
from inception.slim import inception_model as inception
from inception.slim import losses
from inception.slim import ops
from inception.slim import scopes
from inception.slim import variables
from inception.slim.scopes import arg_scope

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Contains convenience wrappers for typical Neural Network TensorFlow layers.

   Additionally it maintains a collection with update_ops that need to be
   updated after the ops have been computed, for exmaple to update moving means
   and moving variances of batch_norm.

   Ops that have different behavior during training or eval have an is_training
   parameter. Additionally Ops that contain variables.variable have a trainable
   parameter, which control if the ops variables are trainable or not.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import tensorflow as tf

from tensorflow.python.training import moving_averages

from inception.slim import losses
from inception.slim import scopes
from inception.slim import variables

# Used to keep the update ops done by batch_norm.
UPDATE_OPS_COLLECTION = '_update_ops_'


@scopes.add_arg_scope
def batch_norm(inputs,
               decay=0.999,
               center=True,
               scale=False,
               epsilon=0.001,
               moving_vars='moving_vars',
               activation=None,
               is_training=True,
               trainable=True,
               restore=True,
               scope=None,
               reuse=None):
  """Adds a Batch Normalization layer.

  Args:
    inputs: a tensor of size [batch_size, height, width, channels]
            or [batch_size, channels].
    decay: decay for the moving average.
    center: If True, subtract beta. If False, beta is not created and ignored.
    scale: If True, multiply by gamma. If False, gamma is
      not used. When the next layer is linear (also e.g. ReLU), this can be
      disabled since the scaling can be done by the next layer.
    epsilon: small float added to variance to avoid dividing by zero.
    moving_vars: collection to store the moving_mean and moving_variance.
    activation: activation function.
    is_training: whether or not the model is in training mode.
    trainable: whether or not the variables should be trainable or not.
    restore: whether or not the variables should be marked for restore.
    scope: Optional scope for variable_op_scope.
    reuse: whether or not the layer and its variables should be reused. To be
      able to reuse the layer scope must be given.

  Returns:
    a tensor representing the output of the operation.

  """
  inputs_shape = inputs.get_shape()
  with tf.variable_op_scope([inputs], scope, 'BatchNorm', reuse=reuse):
    axis = list(range(len(inputs_shape) - 1))
    params_shape = inputs_shape[-1:]
    # Allocate parameters for the beta and gamma of the normalization.
    beta, gamma = None, None
    if center:
      beta = variables.variable('beta',
                                params_shape,
                                initializer=tf.zeros_initializer,
                                trainable=trainable,
                                restore=restore)
    if scale:
      gamma = variables.variable('gamma',
                                 params_shape,
                                 initializer=tf.ones_initializer,
                                 trainable=trainable,
                                 restore=restore)
    # Create moving_mean and moving_variance add them to
    # GraphKeys.MOVING_AVERAGE_VARIABLES collections.
    moving_collections = [moving_vars, tf.GraphKeys.MOVING_AVERAGE_VARIABLES]
    moving_mean = variables.variable('moving_mean',
                                     params_shape,
                                     initializer=tf.zeros_initializer,
                                     trainable=False,
                                     restore=restore,
                                     collections=moving_collections)
    moving_variance = variables.variable('moving_variance',
                                         params_shape,
                                         initializer=tf.ones_initializer,
                                         trainable=False,
                                         restore=restore,
                                         collections=moving_collections)
    if is_training:
      # Calculate the moments based on the individual batch.
      mean, variance = tf.nn.moments(inputs, axis)

      update_moving_mean = moving_averages.assign_moving_average(
          moving_mean, mean, decay)
      tf.add_to_collection(UPDATE_OPS_COLLECTION, update_moving_mean)
      update_moving_variance = moving_averages.assign_moving_average(
          moving_variance, variance, decay)
      tf.add_to_collection(UPDATE_OPS_COLLECTION, update_moving_variance)
    else:
      # Just use the moving_mean and moving_variance.
      mean = moving_mean
      variance = moving_variance
    # Normalize the activations.
    outputs = tf.nn.batch_normalization(
        inputs, mean, variance, beta, gamma, epsilon)
    outputs.set_shape(inputs.get_shape())
    if activation:
      outputs = activation(outputs)
    return outputs


def _two_element_tuple(int_or_tuple):
  """Converts `int_or_tuple` to height, width.

  Several of the functions that follow accept arguments as either
  a tuple of 2 integers or a single integer.  A single integer
  indicates that the 2 values of the tuple are the same.

  This functions normalizes the input value by always returning a tuple.

  Args:
    int_or_tuple: A list of 2 ints, a single int or a tf.TensorShape.

  Returns:
    A tuple with 2 values.

  Raises:
    ValueError: If `int_or_tuple` it not well formed.
  """
  if isinstance(int_or_tuple, (list, tuple)):
    if len(int_or_tuple) != 2:
      raise ValueError('Must be a list with 2 elements: %s' % int_or_tuple)
    return int(int_or_tuple[0]), int(int_or_tuple[1])
  if isinstance(int_or_tuple, int):
    return int(int_or_tuple), int(int_or_tuple)
  if isinstance(int_or_tuple, tf.TensorShape):
    if len(int_or_tuple) == 2:
      return int_or_tuple[0], int_or_tuple[1]
  raise ValueError('Must be an int, a list with 2 elements or a TensorShape of '
                   'length 2')


@scopes.add_arg_scope
def conv2d(inputs,
           num_filters_out,
           kernel_size,
           stride=1,
           padding='SAME',
           activation=tf.nn.relu,
           stddev=0.01,
           bias=0.0,
           weight_decay=0,
           batch_norm_params=None,
           is_training=True,
           trainable=True,
           restore=True,
           scope=None,
           reuse=None):
  """Adds a 2D convolution followed by an optional batch_norm layer.

  conv2d creates a variable called 'weights', representing the convolutional
  kernel, that is convolved with the input. If `batch_norm_params` is None, a
  second variable called 'biases' is added to the result of the convolution
  operation.

  Args:
    inputs: a tensor of size [batch_size, height, width, channels].
    num_filters_out: the number of output filters.
    kernel_size: a list of length 2: [kernel_height, kernel_width] of
      of the filters. Can be an int if both values are the same.
    stride: a list of length 2: [stride_height, stride_width].
      Can be an int if both strides are the same.  Note that presently
      both strides must have the same value.
    padding: one of 'VALID' or 'SAME'.
    activation: activation function.
    stddev: standard deviation of the truncated guassian weight distribution.
    bias: the initial value of the biases.
    weight_decay: the weight decay.
    batch_norm_params: parameters for the batch_norm. If is None don't use it.
    is_training: whether or not the model is in training mode.
    trainable: whether or not the variables should be trainable or not.
    restore: whether or not the variables should be marked for restore.
    scope: Optional scope for variable_op_scope.
    reuse: whether or not the layer and its variables should be reused. To be
      able to reuse the layer scope must be given.
  Returns:
    a tensor representing the output of the operation.

  """
  with tf.variable_op_scope([inputs], scope, 'Conv', reuse=reuse):
    kernel_h, kernel_w = _two_element_tuple(kernel_size)
    stride_h, stride_w = _two_element_tuple(stride)
    num_filters_in = inputs.get_shape()[-1]
    weights_shape = [kernel_h, kernel_w,
                     num_filters_in, num_filters_out]
    weights_initializer = tf.truncated_normal_initializer(stddev=stddev)
    l2_regularizer = None
    if weight_decay and weight_decay > 0:
      l2_regularizer = losses.l2_regularizer(weight_decay)
    weights = variables.variable('weights',
                                 shape=weights_shape,
                                 initializer=weights_initializer,
                                 regularizer=l2_regularizer,
                                 trainable=trainable,
                                 restore=restore)
    conv = tf.nn.conv2d(inputs, weights, [1, stride_h, stride_w, 1],
                        padding=padding)
    if batch_norm_params is not None:
      with scopes.arg_scope([batch_norm], is_training=is_training,
                            trainable=trainable, restore=restore):
        outputs = batch_norm(conv, **batch_norm_params)
    else:
      bias_shape = [num_filters_out,]
      bias_initializer = tf.constant_initializer(bias)
      biases = variables.variable('biases',
                                  shape=bias_shape,
                                  initializer=bias_initializer,
                                  trainable=trainable,
                                  restore=restore)
      outputs = tf.nn.bias_add(conv, biases)
    if activation:
      outputs = activation(outputs)
    return outputs


@scopes.add_arg_scope
def fc(inputs,
       num_units_out,
       activation=tf.nn.relu,
       stddev=0.01,
       bias=0.0,
       weight_decay=0,
       batch_norm_params=None,
       is_training=True,
       trainable=True,
       restore=True,
       scope=None,
       reuse=None):
  """Adds a fully connected layer followed by an optional batch_norm layer.

  FC creates a variable called 'weights', representing the fully connected
  weight matrix, that is multiplied by the input. If `batch_norm` is None, a
  second variable called 'biases' is added to the result of the initial
  vector-matrix multiplication.

  Args:
    inputs: a [B x N] tensor where B is the batch size and N is the number of
            input units in the layer.
    num_units_out: the number of output units in the layer.
    activation: activation function.
    stddev: the standard deviation for the weights.
    bias: the initial value of the biases.
    weight_decay: the weight decay.
    batch_norm_params: parameters for the batch_norm. If is None don't use it.
    is_training: whether or not the model is in training mode.
    trainable: whether or not the variables should be trainable or not.
    restore: whether or not the variables should be marked for restore.
    scope: Optional scope for variable_op_scope.
    reuse: whether or not the layer and its variables should be reused. To be
      able to reuse the layer scope must be given.

  Returns:
     the tensor variable representing the result of the series of operations.
  """
  with tf.variable_op_scope([inputs], scope, 'FC', reuse=reuse):
    num_units_in = inputs.get_shape()[1]
    weights_shape = [num_units_in, num_units_out]
    weights_initializer = tf.truncated_normal_initializer(stddev=stddev)
    l2_regularizer = None
    if weight_decay and weight_decay > 0:
      l2_regularizer = losses.l2_regularizer(weight_decay)
    weights = variables.variable('weights',
                                 shape=weights_shape,
                                 initializer=weights_initializer,
                                 regularizer=l2_regularizer,
                                 trainable=trainable,
                                 restore=restore)
    if batch_norm_params is not None:
      outputs = tf.matmul(inputs, weights)
      with scopes.arg_scope([batch_norm], is_training=is_training,
                            trainable=trainable, restore=restore):
        outputs = batch_norm(outputs, **batch_norm_params)
    else:
      bias_shape = [num_units_out,]
      bias_initializer = tf.constant_initializer(bias)
      biases = variables.variable('biases',
                                  shape=bias_shape,
                                  initializer=bias_initializer,
                                  trainable=trainable,
                                  restore=restore)
      outputs = tf.nn.xw_plus_b(inputs, weights, biases)
    if activation:
      outputs = activation(outputs)
    return outputs


def one_hot_encoding(labels, num_classes, scope=None):
  """Transform numeric labels into onehot_labels.

  Args:
    labels: [batch_size] target labels.
    num_classes: total number of classes.
    scope: Optional scope for op_scope.
  Returns:
    one hot encoding of the labels.
  """
  with tf.op_scope([labels], scope, 'OneHotEncoding'):
    batch_size = labels.get_shape()[0]
    indices = tf.expand_dims(tf.range(0, batch_size), 1)
    labels = tf.cast(tf.expand_dims(labels, 1), indices.dtype)
    concated = tf.concat(1, [indices, labels])
    onehot_labels = tf.sparse_to_dense(
        concated, tf.pack([batch_size, num_classes]), 1.0, 0.0)
    onehot_labels.set_shape([batch_size, num_classes])
    return onehot_labels


@scopes.add_arg_scope
def max_pool(inputs, kernel_size, stride=2, padding='VALID', scope=None):
  """Adds a Max Pooling layer.

  It is assumed by the wrapper that the pooling is only done per image and not
  in depth or batch.

  Args:
    inputs: a tensor of size [batch_size, height, width, depth].
    kernel_size: a list of length 2: [kernel_height, kernel_width] of the
      pooling kernel over which the op is computed. Can be an int if both
      values are the same.
    stride: a list of length 2: [stride_height, stride_width].
      Can be an int if both strides are the same.  Note that presently
      both strides must have the same value.
    padding: the padding method, either 'VALID' or 'SAME'.
    scope: Optional scope for op_scope.

  Returns:
    a tensor representing the results of the pooling operation.
  Raises:
    ValueError: if 'kernel_size' is not a 2-D list
  """
  with tf.op_scope([inputs], scope, 'MaxPool'):
    kernel_h, kernel_w = _two_element_tuple(kernel_size)
    stride_h, stride_w = _two_element_tuple(stride)
    return tf.nn.max_pool(inputs,
                          ksize=[1, kernel_h, kernel_w, 1],
                          strides=[1, stride_h, stride_w, 1],
                          padding=padding)


@scopes.add_arg_scope
def avg_pool(inputs, kernel_size, stride=2, padding='VALID', scope=None):
  """Adds a Avg Pooling layer.

  It is assumed by the wrapper that the pooling is only done per image and not
  in depth or batch.

  Args:
    inputs: a tensor of size [batch_size, height, width, depth].
    kernel_size: a list of length 2: [kernel_height, kernel_width] of the
      pooling kernel over which the op is computed. Can be an int if both
      values are the same.
    stride: a list of length 2: [stride_height, stride_width].
      Can be an int if both strides are the same.  Note that presently
      both strides must have the same value.
    padding: the padding method, either 'VALID' or 'SAME'.
    scope: Optional scope for op_scope.

  Returns:
    a tensor representing the results of the pooling operation.
  """
  with tf.op_scope([inputs], scope, 'AvgPool'):
    kernel_h, kernel_w = _two_element_tuple(kernel_size)
    stride_h, stride_w = _two_element_tuple(stride)
    return tf.nn.avg_pool(inputs,
                          ksize=[1, kernel_h, kernel_w, 1],
                          strides=[1, stride_h, stride_w, 1],
                          padding=padding)


@scopes.add_arg_scope
def dropout(inputs, keep_prob=0.5, is_training=True, scope=None):
  """Returns a dropout layer applied to the input.

  Args:
    inputs: the tensor to pass to the Dropout layer.
    keep_prob: the probability of keeping each input unit.
    is_training: whether or not the model is in training mode. If so, dropout is
    applied and values scaled. Otherwise, inputs is returned.
    scope: Optional scope for op_scope.

  Returns:
    a tensor representing the output of the operation.
  """
  if is_training and keep_prob > 0:
    with tf.op_scope([inputs], scope, 'Dropout'):
      return tf.nn.dropout(inputs, keep_prob)
  else:
    return inputs


def flatten(inputs, scope=None):
  """Flattens the input while maintaining the batch_size.

    Assumes that the first dimension represents the batch.

  Args:
    inputs: a tensor of size [batch_size, ...].
    scope: Optional scope for op_scope.

  Returns:
    a flattened tensor with shape [batch_size, k].
  Raises:
    ValueError: if inputs.shape is wrong.
  """
  if len(inputs.get_shape()) < 2:
    raise ValueError('Inputs must be have a least 2 dimensions')
  dims = inputs.get_shape()[1:]
  k = dims.num_elements()
  with tf.op_scope([inputs], scope, 'Flatten'):
    return tf.reshape(inputs, [-1, k])


def repeat_op(repetitions, inputs, op, *args, **kwargs):
  """Build a sequential Tower starting from inputs by using an op repeatedly.

  It creates new scopes for each operation by increasing the counter.
  Example: given repeat_op(3, _, ops.conv2d, 64, [3, 3], scope='conv1')
    it will repeat the given op under the following variable_scopes:
      conv1/Conv
      conv1/Conv_1
      conv1/Conv_2

  Args:
    repetitions: number or repetitions.
    inputs: a tensor of size [batch_size, height, width, channels].
    op: an operation.
    *args: args for the op.
    **kwargs: kwargs for the op.

  Returns:
    a tensor result of applying the operation op, num times.
  Raises:
    ValueError: if the op is unknown or wrong.
  """
  scope = kwargs.pop('scope', None)
  with tf.variable_op_scope([inputs], scope, 'RepeatOp'):
    tower = inputs
    for _ in range(repetitions):
      tower = op(tower, *args, **kwargs)
    return tower

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Inception-v3 expressed in TensorFlow-Slim.

  Usage:

  # Parameters for BatchNorm.
  batch_norm_params = {
      # Decay for the batch_norm moving averages.
      'decay': BATCHNORM_MOVING_AVERAGE_DECAY,
      # epsilon to prevent 0s in variance.
      'epsilon': 0.001,
  }
  # Set weight_decay for weights in Conv and FC layers.
  with slim.arg_scope([slim.ops.conv2d, slim.ops.fc], weight_decay=0.00004):
    with slim.arg_scope([slim.ops.conv2d],
                        stddev=0.1,
                        activation=tf.nn.relu,
                        batch_norm_params=batch_norm_params):
      # Force all Variables to reside on the CPU.
      with slim.arg_scope([slim.variables.variable], device='/cpu:0'):
        logits, endpoints = slim.inception.inception_v3(
            images,
            dropout_keep_prob=0.8,
            num_classes=num_classes,
            is_training=for_training,
            restore_logits=restore_logits,
            scope=scope)
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

from inception.slim import ops
from inception.slim import scopes


def inception_v3(inputs,
                 dropout_keep_prob=0.8,
                 num_classes=1000,
                 is_training=True,
                 restore_logits=True,
                 scope=''):
  """Latest Inception from http://arxiv.org/abs/1512.00567.

    "Rethinking the Inception Architecture for Computer Vision"

    Christian Szegedy, Vincent Vanhoucke, Sergey Ioffe, Jonathon Shlens,
    Zbigniew Wojna

  Args:
    inputs: a tensor of size [batch_size, height, width, channels].
    dropout_keep_prob: dropout keep_prob.
    num_classes: number of predicted classes.
    is_training: whether is training or not.
    restore_logits: whether or not the logits layers should be restored.
      Useful for fine-tuning a model with different num_classes.
    scope: Optional scope for op_scope.

  Returns:
    a list containing 'logits', 'aux_logits' Tensors.
  """
  # end_points will collect relevant activations for external use, for example
  # summaries or losses.
  end_points = {}
  with tf.op_scope([inputs], scope, 'inception_v3'):
    with scopes.arg_scope([ops.conv2d, ops.fc, ops.batch_norm, ops.dropout],
                          is_training=is_training):
      with scopes.arg_scope([ops.conv2d, ops.max_pool, ops.avg_pool],
                            stride=1, padding='VALID'):
        # 299 x 299 x 3
        end_points['conv0'] = ops.conv2d(inputs, 32, [3, 3], stride=2,
                                         scope='conv0')
        # 149 x 149 x 32
        end_points['conv1'] = ops.conv2d(end_points['conv0'], 32, [3, 3],
                                         scope='conv1')
        # 147 x 147 x 32
        end_points['conv2'] = ops.conv2d(end_points['conv1'], 64, [3, 3],
                                         padding='SAME', scope='conv2')
        # 147 x 147 x 64
        end_points['pool1'] = ops.max_pool(end_points['conv2'], [3, 3],
                                           stride=2, scope='pool1')
        # 73 x 73 x 64
        end_points['conv3'] = ops.conv2d(end_points['pool1'], 80, [1, 1],
                                         scope='conv3')
        # 73 x 73 x 80.
        end_points['conv4'] = ops.conv2d(end_points['conv3'], 192, [3, 3],
                                         scope='conv4')
        # 71 x 71 x 192.
        end_points['pool2'] = ops.max_pool(end_points['conv4'], [3, 3],
                                           stride=2, scope='pool2')
        # 35 x 35 x 192.
        net = end_points['pool2']
      # Inception blocks
      with scopes.arg_scope([ops.conv2d, ops.max_pool, ops.avg_pool],
                            stride=1, padding='SAME'):
        # mixed: 35 x 35 x 256.
        with tf.variable_scope('mixed_35x35x256a'):
          with tf.variable_scope('branch1x1'):
            branch1x1 = ops.conv2d(net, 64, [1, 1])
          with tf.variable_scope('branch5x5'):
            branch5x5 = ops.conv2d(net, 48, [1, 1])
            branch5x5 = ops.conv2d(branch5x5, 64, [5, 5])
          with tf.variable_scope('branch3x3dbl'):
            branch3x3dbl = ops.conv2d(net, 64, [1, 1])
            branch3x3dbl = ops.conv2d(branch3x3dbl, 96, [3, 3])
            branch3x3dbl = ops.conv2d(branch3x3dbl, 96, [3, 3])
          with tf.variable_scope('branch_pool'):
            branch_pool = ops.avg_pool(net, [3, 3])
            branch_pool = ops.conv2d(branch_pool, 32, [1, 1])
          net = tf.concat(3, [branch1x1, branch5x5, branch3x3dbl, branch_pool])
          end_points['mixed_35x35x256a'] = net
        # mixed_1: 35 x 35 x 288.
        with tf.variable_scope('mixed_35x35x288a'):
          with tf.variable_scope('branch1x1'):
            branch1x1 = ops.conv2d(net, 64, [1, 1])
          with tf.variable_scope('branch5x5'):
            branch5x5 = ops.conv2d(net, 48, [1, 1])
            branch5x5 = ops.conv2d(branch5x5, 64, [5, 5])
          with tf.variable_scope('branch3x3dbl'):
            branch3x3dbl = ops.conv2d(net, 64, [1, 1])
            branch3x3dbl = ops.conv2d(branch3x3dbl, 96, [3, 3])
            branch3x3dbl = ops.conv2d(branch3x3dbl, 96, [3, 3])
          with tf.variable_scope('branch_pool'):
            branch_pool = ops.avg_pool(net, [3, 3])
            branch_pool = ops.conv2d(branch_pool, 64, [1, 1])
          net = tf.concat(3, [branch1x1, branch5x5, branch3x3dbl, branch_pool])
          end_points['mixed_35x35x288a'] = net
        # mixed_2: 35 x 35 x 288.
        with tf.variable_scope('mixed_35x35x288b'):
          with tf.variable_scope('branch1x1'):
            branch1x1 = ops.conv2d(net, 64, [1, 1])
          with tf.variable_scope('branch5x5'):
            branch5x5 = ops.conv2d(net, 48, [1, 1])
            branch5x5 = ops.conv2d(branch5x5, 64, [5, 5])
          with tf.variable_scope('branch3x3dbl'):
            branch3x3dbl = ops.conv2d(net, 64, [1, 1])
            branch3x3dbl = ops.conv2d(branch3x3dbl, 96, [3, 3])
            branch3x3dbl = ops.conv2d(branch3x3dbl, 96, [3, 3])
          with tf.variable_scope('branch_pool'):
            branch_pool = ops.avg_pool(net, [3, 3])
            branch_pool = ops.conv2d(branch_pool, 64, [1, 1])
          net = tf.concat(3, [branch1x1, branch5x5, branch3x3dbl, branch_pool])
          end_points['mixed_35x35x288b'] = net
        # mixed_3: 17 x 17 x 768.
        with tf.variable_scope('mixed_17x17x768a'):
          with tf.variable_scope('branch3x3'):
            branch3x3 = ops.conv2d(net, 384, [3, 3], stride=2, padding='VALID')
          with tf.variable_scope('branch3x3dbl'):
            branch3x3dbl = ops.conv2d(net, 64, [1, 1])
            branch3x3dbl = ops.conv2d(branch3x3dbl, 96, [3, 3])
            branch3x3dbl = ops.conv2d(branch3x3dbl, 96, [3, 3],
                                      stride=2, padding='VALID')
          with tf.variable_scope('branch_pool'):
            branch_pool = ops.max_pool(net, [3, 3], stride=2, padding='VALID')
          net = tf.concat(3, [branch3x3, branch3x3dbl, branch_pool])
          end_points['mixed_17x17x768a'] = net
        # mixed4: 17 x 17 x 768.
        with tf.variable_scope('mixed_17x17x768b'):
          with tf.variable_scope('branch1x1'):
            branch1x1 = ops.conv2d(net, 192, [1, 1])
          with tf.variable_scope('branch7x7'):
            branch7x7 = ops.conv2d(net, 128, [1, 1])
            branch7x7 = ops.conv2d(branch7x7, 128, [1, 7])
            branch7x7 = ops.conv2d(branch7x7, 192, [7, 1])
          with tf.variable_scope('branch7x7dbl'):
            branch7x7dbl = ops.conv2d(net, 128, [1, 1])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 128, [7, 1])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 128, [1, 7])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 128, [7, 1])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 192, [1, 7])
          with tf.variable_scope('branch_pool'):
            branch_pool = ops.avg_pool(net, [3, 3])
            branch_pool = ops.conv2d(branch_pool, 192, [1, 1])
          net = tf.concat(3, [branch1x1, branch7x7, branch7x7dbl, branch_pool])
          end_points['mixed_17x17x768b'] = net
        # mixed_5: 17 x 17 x 768.
        with tf.variable_scope('mixed_17x17x768c'):
          with tf.variable_scope('branch1x1'):
            branch1x1 = ops.conv2d(net, 192, [1, 1])
          with tf.variable_scope('branch7x7'):
            branch7x7 = ops.conv2d(net, 160, [1, 1])
            branch7x7 = ops.conv2d(branch7x7, 160, [1, 7])
            branch7x7 = ops.conv2d(branch7x7, 192, [7, 1])
          with tf.variable_scope('branch7x7dbl'):
            branch7x7dbl = ops.conv2d(net, 160, [1, 1])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 160, [7, 1])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 160, [1, 7])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 160, [7, 1])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 192, [1, 7])
          with tf.variable_scope('branch_pool'):
            branch_pool = ops.avg_pool(net, [3, 3])
            branch_pool = ops.conv2d(branch_pool, 192, [1, 1])
          net = tf.concat(3, [branch1x1, branch7x7, branch7x7dbl, branch_pool])
          end_points['mixed_17x17x768c'] = net
        # mixed_6: 17 x 17 x 768.
        with tf.variable_scope('mixed_17x17x768d'):
          with tf.variable_scope('branch1x1'):
            branch1x1 = ops.conv2d(net, 192, [1, 1])
          with tf.variable_scope('branch7x7'):
            branch7x7 = ops.conv2d(net, 160, [1, 1])
            branch7x7 = ops.conv2d(branch7x7, 160, [1, 7])
            branch7x7 = ops.conv2d(branch7x7, 192, [7, 1])
          with tf.variable_scope('branch7x7dbl'):
            branch7x7dbl = ops.conv2d(net, 160, [1, 1])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 160, [7, 1])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 160, [1, 7])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 160, [7, 1])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 192, [1, 7])
          with tf.variable_scope('branch_pool'):
            branch_pool = ops.avg_pool(net, [3, 3])
            branch_pool = ops.conv2d(branch_pool, 192, [1, 1])
          net = tf.concat(3, [branch1x1, branch7x7, branch7x7dbl, branch_pool])
          end_points['mixed_17x17x768d'] = net
        # mixed_7: 17 x 17 x 768.
        with tf.variable_scope('mixed_17x17x768e'):
          with tf.variable_scope('branch1x1'):
            branch1x1 = ops.conv2d(net, 192, [1, 1])
          with tf.variable_scope('branch7x7'):
            branch7x7 = ops.conv2d(net, 192, [1, 1])
            branch7x7 = ops.conv2d(branch7x7, 192, [1, 7])
            branch7x7 = ops.conv2d(branch7x7, 192, [7, 1])
          with tf.variable_scope('branch7x7dbl'):
            branch7x7dbl = ops.conv2d(net, 192, [1, 1])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 192, [7, 1])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 192, [1, 7])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 192, [7, 1])
            branch7x7dbl = ops.conv2d(branch7x7dbl, 192, [1, 7])
          with tf.variable_scope('branch_pool'):
            branch_pool = ops.avg_pool(net, [3, 3])
            branch_pool = ops.conv2d(branch_pool, 192, [1, 1])
          net = tf.concat(3, [branch1x1, branch7x7, branch7x7dbl, branch_pool])
          end_points['mixed_17x17x768e'] = net
        # Auxiliary Head logits
        aux_logits = tf.identity(end_points['mixed_17x17x768e'])
        with tf.variable_scope('aux_logits'):
          aux_logits = ops.avg_pool(aux_logits, [5, 5], stride=3,
                                    padding='VALID')
          aux_logits = ops.conv2d(aux_logits, 128, [1, 1], scope='proj')
          # Shape of feature map before the final layer.
          shape = aux_logits.get_shape()
          aux_logits = ops.conv2d(aux_logits, 768, shape[1:3], stddev=0.01,
                                  padding='VALID')
          aux_logits = ops.flatten(aux_logits)
          aux_logits = ops.fc(aux_logits, num_classes, activation=None,
                              stddev=0.001, restore=restore_logits)
          end_points['aux_logits'] = aux_logits
        # mixed_8: 8 x 8 x 1280.
        # Note that the scope below is not changed to not void previous
        # checkpoints.
        # (TODO) Fix the scope when appropriate.
        with tf.variable_scope('mixed_17x17x1280a'):
          with tf.variable_scope('branch3x3'):
            branch3x3 = ops.conv2d(net, 192, [1, 1])
            branch3x3 = ops.conv2d(branch3x3, 320, [3, 3], stride=2,
                                   padding='VALID')
          with tf.variable_scope('branch7x7x3'):
            branch7x7x3 = ops.conv2d(net, 192, [1, 1])
            branch7x7x3 = ops.conv2d(branch7x7x3, 192, [1, 7])
            branch7x7x3 = ops.conv2d(branch7x7x3, 192, [7, 1])
            branch7x7x3 = ops.conv2d(branch7x7x3, 192, [3, 3],
                                     stride=2, padding='VALID')
          with tf.variable_scope('branch_pool'):
            branch_pool = ops.max_pool(net, [3, 3], stride=2, padding='VALID')
          net = tf.concat(3, [branch3x3, branch7x7x3, branch_pool])
          end_points['mixed_17x17x1280a'] = net
        # mixed_9: 8 x 8 x 2048.
        with tf.variable_scope('mixed_8x8x2048a'):
          with tf.variable_scope('branch1x1'):
            branch1x1 = ops.conv2d(net, 320, [1, 1])
          with tf.variable_scope('branch3x3'):
            branch3x3 = ops.conv2d(net, 384, [1, 1])
            branch3x3 = tf.concat(3, [ops.conv2d(branch3x3, 384, [1, 3]),
                                      ops.conv2d(branch3x3, 384, [3, 1])])
          with tf.variable_scope('branch3x3dbl'):
            branch3x3dbl = ops.conv2d(net, 448, [1, 1])
            branch3x3dbl = ops.conv2d(branch3x3dbl, 384, [3, 3])
            branch3x3dbl = tf.concat(3, [ops.conv2d(branch3x3dbl, 384, [1, 3]),
                                         ops.conv2d(branch3x3dbl, 384, [3, 1])])
          with tf.variable_scope('branch_pool'):
            branch_pool = ops.avg_pool(net, [3, 3])
            branch_pool = ops.conv2d(branch_pool, 192, [1, 1])
          net = tf.concat(3, [branch1x1, branch3x3, branch3x3dbl, branch_pool])
          end_points['mixed_8x8x2048a'] = net
        # mixed_10: 8 x 8 x 2048.
        with tf.variable_scope('mixed_8x8x2048b'):
          with tf.variable_scope('branch1x1'):
            branch1x1 = ops.conv2d(net, 320, [1, 1])
          with tf.variable_scope('branch3x3'):
            branch3x3 = ops.conv2d(net, 384, [1, 1])
            branch3x3 = tf.concat(3, [ops.conv2d(branch3x3, 384, [1, 3]),
                                      ops.conv2d(branch3x3, 384, [3, 1])])
          with tf.variable_scope('branch3x3dbl'):
            branch3x3dbl = ops.conv2d(net, 448, [1, 1])
            branch3x3dbl = ops.conv2d(branch3x3dbl, 384, [3, 3])
            branch3x3dbl = tf.concat(3, [ops.conv2d(branch3x3dbl, 384, [1, 3]),
                                         ops.conv2d(branch3x3dbl, 384, [3, 1])])
          with tf.variable_scope('branch_pool'):
            branch_pool = ops.avg_pool(net, [3, 3])
            branch_pool = ops.conv2d(branch_pool, 192, [1, 1])
          net = tf.concat(3, [branch1x1, branch3x3, branch3x3dbl, branch_pool])
          end_points['mixed_8x8x2048b'] = net
        # Final pooling and prediction
        with tf.variable_scope('logits'):
          shape = net.get_shape()
          net = ops.avg_pool(net, shape[1:3], padding='VALID', scope='pool')
          # 1 x 1 x 2048
          net = ops.dropout(net, dropout_keep_prob, scope='dropout')
          net = ops.flatten(net, scope='flatten')
          # 2048
          logits = ops.fc(net, num_classes, activation=None, scope='logits',
                          restore=restore_logits)
          # 1000
          end_points['logits'] = logits
          end_points['predictions'] = tf.nn.softmax(logits, name='predictions')
      return logits, end_points


def inception_v3_parameters(weight_decay=0.00004, stddev=0.1,
                            batch_norm_decay=0.9997, batch_norm_epsilon=0.001):
  """Yields the scope with the default parameters for inception_v3.

  Args:
    weight_decay: the weight decay for weights variables.
    stddev: standard deviation of the truncated guassian weight distribution.
    batch_norm_decay: decay for the moving average of batch_norm momentums.
    batch_norm_epsilon: small float added to variance to avoid dividing by zero.

  Yields:
    a arg_scope with the parameters needed for inception_v3.
  """
  # Set weight_decay for weights in Conv and FC layers.
  with scopes.arg_scope([ops.conv2d, ops.fc],
                        weight_decay=weight_decay):
    # Set stddev, activation and parameters for batch_norm.
    with scopes.arg_scope([ops.conv2d],
                          stddev=stddev,
                          activation=tf.nn.relu,
                          batch_norm_params={
                              'decay': batch_norm_decay,
                              'epsilon': batch_norm_epsilon}) as arg_scope:
      yield arg_scope

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for slim.ops."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import numpy as np
import tensorflow as tf

from tensorflow.python.ops import control_flow_ops

from inception.slim import ops
from inception.slim import scopes
from inception.slim import variables


class ConvTest(tf.test.TestCase):

  def testCreateConv(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.conv2d(images, 32, [3, 3])
      self.assertEquals(output.op.name, 'Conv/Relu')
      self.assertListEqual(output.get_shape().as_list(), [5, height, width, 32])

  def testCreateSquareConv(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.conv2d(images, 32, 3)
      self.assertEquals(output.op.name, 'Conv/Relu')
      self.assertListEqual(output.get_shape().as_list(), [5, height, width, 32])

  def testCreateConvWithTensorShape(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.conv2d(images, 32, images.get_shape()[1:3])
      self.assertEquals(output.op.name, 'Conv/Relu')
      self.assertListEqual(output.get_shape().as_list(), [5, height, width, 32])

  def testCreateFullyConv(self):
    height, width = 6, 6
    with self.test_session():
      images = tf.random_uniform((5, height, width, 32), seed=1)
      output = ops.conv2d(images, 64, images.get_shape()[1:3], padding='VALID')
      self.assertEquals(output.op.name, 'Conv/Relu')
      self.assertListEqual(output.get_shape().as_list(), [5, 1, 1, 64])

  def testCreateVerticalConv(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.conv2d(images, 32, [3, 1])
      self.assertEquals(output.op.name, 'Conv/Relu')
      self.assertListEqual(output.get_shape().as_list(),
                           [5, height, width, 32])

  def testCreateHorizontalConv(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.conv2d(images, 32, [1, 3])
      self.assertEquals(output.op.name, 'Conv/Relu')
      self.assertListEqual(output.get_shape().as_list(),
                           [5, height, width, 32])

  def testCreateConvWithStride(self):
    height, width = 6, 6
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.conv2d(images, 32, [3, 3], stride=2)
      self.assertEquals(output.op.name, 'Conv/Relu')
      self.assertListEqual(output.get_shape().as_list(),
                           [5, height/2, width/2, 32])

  def testCreateConvCreatesWeightsAndBiasesVars(self):
    height, width = 3, 3
    images = tf.random_uniform((5, height, width, 3), seed=1)
    with self.test_session():
      self.assertFalse(variables.get_variables('conv1/weights'))
      self.assertFalse(variables.get_variables('conv1/biases'))
      ops.conv2d(images, 32, [3, 3], scope='conv1')
      self.assertTrue(variables.get_variables('conv1/weights'))
      self.assertTrue(variables.get_variables('conv1/biases'))

  def testCreateConvWithScope(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.conv2d(images, 32, [3, 3], scope='conv1')
      self.assertEquals(output.op.name, 'conv1/Relu')

  def testCreateConvWithoutActivation(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.conv2d(images, 32, [3, 3], activation=None)
      self.assertEquals(output.op.name, 'Conv/BiasAdd')

  def testCreateConvValid(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.conv2d(images, 32, [3, 3], padding='VALID')
      self.assertListEqual(output.get_shape().as_list(), [5, 1, 1, 32])

  def testCreateConvWithWD(self):
    height, width = 3, 3
    with self.test_session() as sess:
      images = tf.random_uniform((5, height, width, 3), seed=1)
      ops.conv2d(images, 32, [3, 3], weight_decay=0.01)
      wd = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)[0]
      self.assertEquals(wd.op.name,
                        'Conv/weights/Regularizer/L2Regularizer/value')
      sess.run(tf.initialize_all_variables())
      self.assertTrue(sess.run(wd) <= 0.01)

  def testCreateConvWithoutWD(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      ops.conv2d(images, 32, [3, 3], weight_decay=0)
      self.assertEquals(
          tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES), [])

  def testReuseVars(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      ops.conv2d(images, 32, [3, 3], scope='conv1')
      self.assertEquals(len(variables.get_variables()), 2)
      ops.conv2d(images, 32, [3, 3], scope='conv1', reuse=True)
      self.assertEquals(len(variables.get_variables()), 2)

  def testNonReuseVars(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      ops.conv2d(images, 32, [3, 3])
      self.assertEquals(len(variables.get_variables()), 2)
      ops.conv2d(images, 32, [3, 3])
      self.assertEquals(len(variables.get_variables()), 4)

  def testReuseConvWithWD(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      ops.conv2d(images, 32, [3, 3], weight_decay=0.01, scope='conv1')
      self.assertEquals(len(variables.get_variables()), 2)
      self.assertEquals(
          len(tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)), 1)
      ops.conv2d(images, 32, [3, 3], weight_decay=0.01, scope='conv1',
                 reuse=True)
      self.assertEquals(len(variables.get_variables()), 2)
      self.assertEquals(
          len(tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)), 1)

  def testConvWithBatchNorm(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 32), seed=1)
      with scopes.arg_scope([ops.conv2d], batch_norm_params={'decay': 0.9}):
        net = ops.conv2d(images, 32, [3, 3])
        net = ops.conv2d(net, 32, [3, 3])
      self.assertEquals(len(variables.get_variables()), 8)
      self.assertEquals(len(variables.get_variables('Conv/BatchNorm')), 3)
      self.assertEquals(len(variables.get_variables('Conv_1/BatchNorm')), 3)

  def testReuseConvWithBatchNorm(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 32), seed=1)
      with scopes.arg_scope([ops.conv2d], batch_norm_params={'decay': 0.9}):
        net = ops.conv2d(images, 32, [3, 3], scope='Conv')
        net = ops.conv2d(net, 32, [3, 3], scope='Conv', reuse=True)
      self.assertEquals(len(variables.get_variables()), 4)
      self.assertEquals(len(variables.get_variables('Conv/BatchNorm')), 3)
      self.assertEquals(len(variables.get_variables('Conv_1/BatchNorm')), 0)


class FCTest(tf.test.TestCase):

  def testCreateFC(self):
    height, width = 3, 3
    with self.test_session():
      inputs = tf.random_uniform((5, height * width * 3), seed=1)
      output = ops.fc(inputs, 32)
      self.assertEquals(output.op.name, 'FC/Relu')
      self.assertListEqual(output.get_shape().as_list(), [5, 32])

  def testCreateFCWithScope(self):
    height, width = 3, 3
    with self.test_session():
      inputs = tf.random_uniform((5, height * width * 3), seed=1)
      output = ops.fc(inputs, 32, scope='fc1')
      self.assertEquals(output.op.name, 'fc1/Relu')

  def testCreateFcCreatesWeightsAndBiasesVars(self):
    height, width = 3, 3
    inputs = tf.random_uniform((5, height * width * 3), seed=1)
    with self.test_session():
      self.assertFalse(variables.get_variables('fc1/weights'))
      self.assertFalse(variables.get_variables('fc1/biases'))
      ops.fc(inputs, 32, scope='fc1')
      self.assertTrue(variables.get_variables('fc1/weights'))
      self.assertTrue(variables.get_variables('fc1/biases'))

  def testReuseVars(self):
    height, width = 3, 3
    inputs = tf.random_uniform((5, height * width * 3), seed=1)
    with self.test_session():
      ops.fc(inputs, 32, scope='fc1')
      self.assertEquals(len(variables.get_variables('fc1')), 2)
      ops.fc(inputs, 32, scope='fc1', reuse=True)
      self.assertEquals(len(variables.get_variables('fc1')), 2)

  def testNonReuseVars(self):
    height, width = 3, 3
    inputs = tf.random_uniform((5, height * width * 3), seed=1)
    with self.test_session():
      ops.fc(inputs, 32)
      self.assertEquals(len(variables.get_variables('FC')), 2)
      ops.fc(inputs, 32)
      self.assertEquals(len(variables.get_variables('FC')), 4)

  def testCreateFCWithoutActivation(self):
    height, width = 3, 3
    with self.test_session():
      inputs = tf.random_uniform((5, height * width * 3), seed=1)
      output = ops.fc(inputs, 32, activation=None)
      self.assertEquals(output.op.name, 'FC/xw_plus_b')

  def testCreateFCWithWD(self):
    height, width = 3, 3
    with self.test_session() as sess:
      inputs = tf.random_uniform((5, height * width * 3), seed=1)
      ops.fc(inputs, 32, weight_decay=0.01)
      wd = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)[0]
      self.assertEquals(wd.op.name,
                        'FC/weights/Regularizer/L2Regularizer/value')
      sess.run(tf.initialize_all_variables())
      self.assertTrue(sess.run(wd) <= 0.01)

  def testCreateFCWithoutWD(self):
    height, width = 3, 3
    with self.test_session():
      inputs = tf.random_uniform((5, height * width * 3), seed=1)
      ops.fc(inputs, 32, weight_decay=0)
      self.assertEquals(
          tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES), [])

  def testReuseFCWithWD(self):
    height, width = 3, 3
    with self.test_session():
      inputs = tf.random_uniform((5, height * width * 3), seed=1)
      ops.fc(inputs, 32, weight_decay=0.01, scope='fc')
      self.assertEquals(len(variables.get_variables()), 2)
      self.assertEquals(
          len(tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)), 1)
      ops.fc(inputs, 32, weight_decay=0.01, scope='fc', reuse=True)
      self.assertEquals(len(variables.get_variables()), 2)
      self.assertEquals(
          len(tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)), 1)

  def testFCWithBatchNorm(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height * width * 3), seed=1)
      with scopes.arg_scope([ops.fc], batch_norm_params={}):
        net = ops.fc(images, 27)
        net = ops.fc(net, 27)
      self.assertEquals(len(variables.get_variables()), 8)
      self.assertEquals(len(variables.get_variables('FC/BatchNorm')), 3)
      self.assertEquals(len(variables.get_variables('FC_1/BatchNorm')), 3)

  def testReuseFCWithBatchNorm(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height * width * 3), seed=1)
      with scopes.arg_scope([ops.fc], batch_norm_params={'decay': 0.9}):
        net = ops.fc(images, 27, scope='fc1')
        net = ops.fc(net, 27, scope='fc1', reuse=True)
      self.assertEquals(len(variables.get_variables()), 4)
      self.assertEquals(len(variables.get_variables('fc1/BatchNorm')), 3)


class MaxPoolTest(tf.test.TestCase):

  def testCreateMaxPool(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.max_pool(images, [3, 3])
      self.assertEquals(output.op.name, 'MaxPool/MaxPool')
      self.assertListEqual(output.get_shape().as_list(), [5, 1, 1, 3])

  def testCreateSquareMaxPool(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.max_pool(images, 3)
      self.assertEquals(output.op.name, 'MaxPool/MaxPool')
      self.assertListEqual(output.get_shape().as_list(), [5, 1, 1, 3])

  def testCreateMaxPoolWithScope(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.max_pool(images, [3, 3], scope='pool1')
      self.assertEquals(output.op.name, 'pool1/MaxPool')

  def testCreateMaxPoolSAME(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.max_pool(images, [3, 3], padding='SAME')
      self.assertListEqual(output.get_shape().as_list(), [5, 2, 2, 3])

  def testCreateMaxPoolStrideSAME(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.max_pool(images, [3, 3], stride=1, padding='SAME')
      self.assertListEqual(output.get_shape().as_list(), [5, height, width, 3])

  def testGlobalMaxPool(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.max_pool(images, images.get_shape()[1:3], stride=1)
      self.assertListEqual(output.get_shape().as_list(), [5, 1, 1, 3])


class AvgPoolTest(tf.test.TestCase):

  def testCreateAvgPool(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.avg_pool(images, [3, 3])
      self.assertEquals(output.op.name, 'AvgPool/AvgPool')
      self.assertListEqual(output.get_shape().as_list(), [5, 1, 1, 3])

  def testCreateSquareAvgPool(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.avg_pool(images, 3)
      self.assertEquals(output.op.name, 'AvgPool/AvgPool')
      self.assertListEqual(output.get_shape().as_list(), [5, 1, 1, 3])

  def testCreateAvgPoolWithScope(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.avg_pool(images, [3, 3], scope='pool1')
      self.assertEquals(output.op.name, 'pool1/AvgPool')

  def testCreateAvgPoolSAME(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.avg_pool(images, [3, 3], padding='SAME')
      self.assertListEqual(output.get_shape().as_list(), [5, 2, 2, 3])

  def testCreateAvgPoolStrideSAME(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.avg_pool(images, [3, 3], stride=1, padding='SAME')
      self.assertListEqual(output.get_shape().as_list(), [5, height, width, 3])

  def testGlobalAvgPool(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.avg_pool(images, images.get_shape()[1:3], stride=1)
      self.assertListEqual(output.get_shape().as_list(), [5, 1, 1, 3])


class OneHotEncodingTest(tf.test.TestCase):

  def testOneHotEncodingCreate(self):
    with self.test_session():
      labels = tf.constant([0, 1, 2])
      output = ops.one_hot_encoding(labels, num_classes=3)
      self.assertEquals(output.op.name, 'OneHotEncoding/SparseToDense')
      self.assertListEqual(output.get_shape().as_list(), [3, 3])

  def testOneHotEncoding(self):
    with self.test_session():
      labels = tf.constant([0, 1, 2])
      one_hot_labels = tf.constant([[1, 0, 0],
                                    [0, 1, 0],
                                    [0, 0, 1]])
      output = ops.one_hot_encoding(labels, num_classes=3)
      self.assertAllClose(output.eval(), one_hot_labels.eval())


class DropoutTest(tf.test.TestCase):

  def testCreateDropout(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.dropout(images)
      self.assertEquals(output.op.name, 'Dropout/dropout/mul_1')
      output.get_shape().assert_is_compatible_with(images.get_shape())

  def testCreateDropoutNoTraining(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1, name='images')
      output = ops.dropout(images, is_training=False)
      self.assertEquals(output, images)


class FlattenTest(tf.test.TestCase):

  def testFlatten4D(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1, name='images')
      output = ops.flatten(images)
      self.assertEquals(output.get_shape().num_elements(),
                        images.get_shape().num_elements())
      self.assertEqual(output.get_shape()[0], images.get_shape()[0])

  def testFlatten3D(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width), seed=1, name='images')
      output = ops.flatten(images)
      self.assertEquals(output.get_shape().num_elements(),
                        images.get_shape().num_elements())
      self.assertEqual(output.get_shape()[0], images.get_shape()[0])

  def testFlattenBatchSize(self):
    height, width = 3, 3
    with self.test_session() as sess:
      images = tf.random_uniform((5, height, width, 3), seed=1, name='images')
      inputs = tf.placeholder(tf.int32, (None, height, width, 3))
      output = ops.flatten(inputs)
      self.assertEquals(output.get_shape().as_list(),
                        [None, height * width * 3])
      output = sess.run(output, {inputs: images.eval()})
      self.assertEquals(output.size,
                        images.get_shape().num_elements())
      self.assertEqual(output.shape[0], images.get_shape()[0])


class BatchNormTest(tf.test.TestCase):

  def testCreateOp(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      output = ops.batch_norm(images)
      self.assertTrue(output.op.name.startswith('BatchNorm/batchnorm'))
      self.assertListEqual(output.get_shape().as_list(), [5, height, width, 3])

  def testCreateVariables(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      ops.batch_norm(images)
      beta = variables.get_variables_by_name('beta')[0]
      self.assertEquals(beta.op.name, 'BatchNorm/beta')
      gamma = variables.get_variables_by_name('gamma')
      self.assertEquals(gamma, [])
      moving_mean = tf.moving_average_variables()[0]
      moving_variance = tf.moving_average_variables()[1]
      self.assertEquals(moving_mean.op.name, 'BatchNorm/moving_mean')
      self.assertEquals(moving_variance.op.name, 'BatchNorm/moving_variance')

  def testCreateVariablesWithScale(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      ops.batch_norm(images, scale=True)
      beta = variables.get_variables_by_name('beta')[0]
      gamma = variables.get_variables_by_name('gamma')[0]
      self.assertEquals(beta.op.name, 'BatchNorm/beta')
      self.assertEquals(gamma.op.name, 'BatchNorm/gamma')
      moving_mean = tf.moving_average_variables()[0]
      moving_variance = tf.moving_average_variables()[1]
      self.assertEquals(moving_mean.op.name, 'BatchNorm/moving_mean')
      self.assertEquals(moving_variance.op.name, 'BatchNorm/moving_variance')

  def testCreateVariablesWithoutCenterWithScale(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      ops.batch_norm(images, center=False, scale=True)
      beta = variables.get_variables_by_name('beta')
      self.assertEquals(beta, [])
      gamma = variables.get_variables_by_name('gamma')[0]
      self.assertEquals(gamma.op.name, 'BatchNorm/gamma')
      moving_mean = tf.moving_average_variables()[0]
      moving_variance = tf.moving_average_variables()[1]
      self.assertEquals(moving_mean.op.name, 'BatchNorm/moving_mean')
      self.assertEquals(moving_variance.op.name, 'BatchNorm/moving_variance')

  def testCreateVariablesWithoutCenterWithoutScale(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      ops.batch_norm(images, center=False, scale=False)
      beta = variables.get_variables_by_name('beta')
      self.assertEquals(beta, [])
      gamma = variables.get_variables_by_name('gamma')
      self.assertEquals(gamma, [])
      moving_mean = tf.moving_average_variables()[0]
      moving_variance = tf.moving_average_variables()[1]
      self.assertEquals(moving_mean.op.name, 'BatchNorm/moving_mean')
      self.assertEquals(moving_variance.op.name, 'BatchNorm/moving_variance')

  def testMovingAverageVariables(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      ops.batch_norm(images, scale=True)
      moving_mean = tf.moving_average_variables()[0]
      moving_variance = tf.moving_average_variables()[1]
      self.assertEquals(moving_mean.op.name, 'BatchNorm/moving_mean')
      self.assertEquals(moving_variance.op.name, 'BatchNorm/moving_variance')

  def testUpdateOps(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      ops.batch_norm(images)
      update_ops = tf.get_collection(ops.UPDATE_OPS_COLLECTION)
      update_moving_mean = update_ops[0]
      update_moving_variance = update_ops[1]
      self.assertEquals(update_moving_mean.op.name,
                        'BatchNorm/AssignMovingAvg')
      self.assertEquals(update_moving_variance.op.name,
                        'BatchNorm/AssignMovingAvg_1')

  def testReuseVariables(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      ops.batch_norm(images, scale=True, scope='bn')
      ops.batch_norm(images, scale=True, scope='bn', reuse=True)
      beta = variables.get_variables_by_name('beta')
      gamma = variables.get_variables_by_name('gamma')
      self.assertEquals(len(beta), 1)
      self.assertEquals(len(gamma), 1)
      moving_vars = tf.get_collection('moving_vars')
      self.assertEquals(len(moving_vars), 2)

  def testReuseUpdateOps(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      ops.batch_norm(images, scope='bn')
      self.assertEquals(len(tf.get_collection(ops.UPDATE_OPS_COLLECTION)), 2)
      ops.batch_norm(images, scope='bn', reuse=True)
      self.assertEquals(len(tf.get_collection(ops.UPDATE_OPS_COLLECTION)), 4)

  def testCreateMovingVars(self):
    height, width = 3, 3
    with self.test_session():
      images = tf.random_uniform((5, height, width, 3), seed=1)
      _ = ops.batch_norm(images, moving_vars='moving_vars')
      moving_mean = tf.get_collection('moving_vars',
                                      'BatchNorm/moving_mean')
      self.assertEquals(len(moving_mean), 1)
      self.assertEquals(moving_mean[0].op.name, 'BatchNorm/moving_mean')
      moving_variance = tf.get_collection('moving_vars',
                                          'BatchNorm/moving_variance')
      self.assertEquals(len(moving_variance), 1)
      self.assertEquals(moving_variance[0].op.name, 'BatchNorm/moving_variance')

  def testComputeMovingVars(self):
    height, width = 3, 3
    with self.test_session() as sess:
      image_shape = (10, height, width, 3)
      image_values = np.random.rand(*image_shape)
      expected_mean = np.mean(image_values, axis=(0, 1, 2))
      expected_var = np.var(image_values, axis=(0, 1, 2))
      images = tf.constant(image_values, shape=image_shape, dtype=tf.float32)
      output = ops.batch_norm(images, decay=0.1)
      update_ops = tf.get_collection(ops.UPDATE_OPS_COLLECTION)
      with tf.control_dependencies(update_ops):
        barrier = tf.no_op(name='gradient_barrier')
        output = control_flow_ops.with_dependencies([barrier], output)
      # Initialize all variables
      sess.run(tf.initialize_all_variables())
      moving_mean = variables.get_variables('BatchNorm/moving_mean')[0]
      moving_variance = variables.get_variables('BatchNorm/moving_variance')[0]
      mean, variance = sess.run([moving_mean, moving_variance])
      # After initialization moving_mean == 0 and moving_variance == 1.
      self.assertAllClose(mean, [0] * 3)
      self.assertAllClose(variance, [1] * 3)
      for _ in range(10):
        sess.run([output])
      mean = moving_mean.eval()
      variance = moving_variance.eval()
      # After 10 updates with decay 0.1 moving_mean == expected_mean and
      # moving_variance == expected_var.
      self.assertAllClose(mean, expected_mean)
      self.assertAllClose(variance, expected_var)

  def testEvalMovingVars(self):
    height, width = 3, 3
    with self.test_session() as sess:
      image_shape = (10, height, width, 3)
      image_values = np.random.rand(*image_shape)
      expected_mean = np.mean(image_values, axis=(0, 1, 2))
      expected_var = np.var(image_values, axis=(0, 1, 2))
      images = tf.constant(image_values, shape=image_shape, dtype=tf.float32)
      output = ops.batch_norm(images, decay=0.1, is_training=False)
      update_ops = tf.get_collection(ops.UPDATE_OPS_COLLECTION)
      with tf.control_dependencies(update_ops):
        barrier = tf.no_op(name='gradient_barrier')
        output = control_flow_ops.with_dependencies([barrier], output)
      # Initialize all variables
      sess.run(tf.initialize_all_variables())
      moving_mean = variables.get_variables('BatchNorm/moving_mean')[0]
      moving_variance = variables.get_variables('BatchNorm/moving_variance')[0]
      mean, variance = sess.run([moving_mean, moving_variance])
      # After initialization moving_mean == 0 and moving_variance == 1.
      self.assertAllClose(mean, [0] * 3)
      self.assertAllClose(variance, [1] * 3)
      # Simulate assigment from saver restore.
      init_assigns = [tf.assign(moving_mean, expected_mean),
                      tf.assign(moving_variance, expected_var)]
      sess.run(init_assigns)
      for _ in range(10):
        sess.run([output], {images: np.random.rand(*image_shape)})
      mean = moving_mean.eval()
      variance = moving_variance.eval()
      # Although we feed different images, the moving_mean and moving_variance
      # shouldn't change.
      self.assertAllClose(mean, expected_mean)
      self.assertAllClose(variance, expected_var)

  def testReuseVars(self):
    height, width = 3, 3
    with self.test_session() as sess:
      image_shape = (10, height, width, 3)
      image_values = np.random.rand(*image_shape)
      expected_mean = np.mean(image_values, axis=(0, 1, 2))
      expected_var = np.var(image_values, axis=(0, 1, 2))
      images = tf.constant(image_values, shape=image_shape, dtype=tf.float32)
      output = ops.batch_norm(images, decay=0.1, is_training=False)
      update_ops = tf.get_collection(ops.UPDATE_OPS_COLLECTION)
      with tf.control_dependencies(update_ops):
        barrier = tf.no_op(name='gradient_barrier')
        output = control_flow_ops.with_dependencies([barrier], output)
      # Initialize all variables
      sess.run(tf.initialize_all_variables())
      moving_mean = variables.get_variables('BatchNorm/moving_mean')[0]
      moving_variance = variables.get_variables('BatchNorm/moving_variance')[0]
      mean, variance = sess.run([moving_mean, moving_variance])
      # After initialization moving_mean == 0 and moving_variance == 1.
      self.assertAllClose(mean, [0] * 3)
      self.assertAllClose(variance, [1] * 3)
      # Simulate assigment from saver restore.
      init_assigns = [tf.assign(moving_mean, expected_mean),
                      tf.assign(moving_variance, expected_var)]
      sess.run(init_assigns)
      for _ in range(10):
        sess.run([output], {images: np.random.rand(*image_shape)})
      mean = moving_mean.eval()
      variance = moving_variance.eval()
      # Although we feed different images, the moving_mean and moving_variance
      # shouldn't change.
      self.assertAllClose(mean, expected_mean)
      self.assertAllClose(variance, expected_var)

if __name__ == '__main__':
  tf.test.main()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Contains convenience wrappers for various Neural Network TensorFlow losses.

  All the losses defined here add themselves to the LOSSES_COLLECTION
  collection.

  l1_loss: Define a L1 Loss, useful for regularization, i.e. lasso.
  l2_loss: Define a L2 Loss, useful for regularization, i.e. weight decay.
  cross_entropy_loss: Define a cross entropy loss using
    softmax_cross_entropy_with_logits. Useful for classification.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

# In order to gather all losses in a network, the user should use this
# key for get_collection, i.e:
#   losses = tf.get_collection(slim.losses.LOSSES_COLLECTION)
LOSSES_COLLECTION = '_losses'


def l1_regularizer(weight=1.0, scope=None):
  """Define a L1 regularizer.

  Args:
    weight: scale the loss by this factor.
    scope: Optional scope for op_scope.

  Returns:
    a regularizer function.
  """
  def regularizer(tensor):
    with tf.op_scope([tensor], scope, 'L1Regularizer'):
      l1_weight = tf.convert_to_tensor(weight,
                                       dtype=tensor.dtype.base_dtype,
                                       name='weight')
      return tf.mul(l1_weight, tf.reduce_sum(tf.abs(tensor)), name='value')
  return regularizer


def l2_regularizer(weight=1.0, scope=None):
  """Define a L2 regularizer.

  Args:
    weight: scale the loss by this factor.
    scope: Optional scope for op_scope.

  Returns:
    a regularizer function.
  """
  def regularizer(tensor):
    with tf.op_scope([tensor], scope, 'L2Regularizer'):
      l2_weight = tf.convert_to_tensor(weight,
                                       dtype=tensor.dtype.base_dtype,
                                       name='weight')
      return tf.mul(l2_weight, tf.nn.l2_loss(tensor), name='value')
  return regularizer


def l1_l2_regularizer(weight_l1=1.0, weight_l2=1.0, scope=None):
  """Define a L1L2 regularizer.

  Args:
    weight_l1: scale the L1 loss by this factor.
    weight_l2: scale the L2 loss by this factor.
    scope: Optional scope for op_scope.

  Returns:
    a regularizer function.
  """
  def regularizer(tensor):
    with tf.op_scope([tensor], scope, 'L1L2Regularizer'):
      weight_l1_t = tf.convert_to_tensor(weight_l1,
                                         dtype=tensor.dtype.base_dtype,
                                         name='weight_l1')
      weight_l2_t = tf.convert_to_tensor(weight_l2,
                                         dtype=tensor.dtype.base_dtype,
                                         name='weight_l2')
      reg_l1 = tf.mul(weight_l1_t, tf.reduce_sum(tf.abs(tensor)),
                      name='value_l1')
      reg_l2 = tf.mul(weight_l2_t, tf.nn.l2_loss(tensor),
                      name='value_l2')
      return tf.add(reg_l1, reg_l2, name='value')
  return regularizer


def l1_loss(tensor, weight=1.0, scope=None):
  """Define a L1Loss, useful for regularize, i.e. lasso.

  Args:
    tensor: tensor to regularize.
    weight: scale the loss by this factor.
    scope: Optional scope for op_scope.

  Returns:
    the L1 loss op.
  """
  with tf.op_scope([tensor], scope, 'L1Loss'):
    weight = tf.convert_to_tensor(weight,
                                  dtype=tensor.dtype.base_dtype,
                                  name='loss_weight')
    loss = tf.mul(weight, tf.reduce_sum(tf.abs(tensor)), name='value')
    tf.add_to_collection(LOSSES_COLLECTION, loss)
    return loss


def l2_loss(tensor, weight=1.0, scope=None):
  """Define a L2Loss, useful for regularize, i.e. weight decay.

  Args:
    tensor: tensor to regularize.
    weight: an optional weight to modulate the loss.
    scope: Optional scope for op_scope.

  Returns:
    the L2 loss op.
  """
  with tf.op_scope([tensor], scope, 'L2Loss'):
    weight = tf.convert_to_tensor(weight,
                                  dtype=tensor.dtype.base_dtype,
                                  name='loss_weight')
    loss = tf.mul(weight, tf.nn.l2_loss(tensor), name='value')
    tf.add_to_collection(LOSSES_COLLECTION, loss)
    return loss


def cross_entropy_loss(logits, one_hot_labels, label_smoothing=0,
                       weight=1.0, scope=None):
  """Define a Cross Entropy loss using softmax_cross_entropy_with_logits.

  It can scale the loss by weight factor, and smooth the labels.

  Args:
    logits: [batch_size, num_classes] logits outputs of the network .
    one_hot_labels: [batch_size, num_classes] target one_hot_encoded labels.
    label_smoothing: if greater than 0 then smooth the labels.
    weight: scale the loss by this factor.
    scope: Optional scope for op_scope.

  Returns:
    A tensor with the softmax_cross_entropy loss.
  """
  logits.get_shape().assert_is_compatible_with(one_hot_labels.get_shape())
  with tf.op_scope([logits, one_hot_labels], scope, 'CrossEntropyLoss'):
    num_classes = one_hot_labels.get_shape()[-1].value
    one_hot_labels = tf.cast(one_hot_labels, logits.dtype)
    if label_smoothing > 0:
      smooth_positives = 1.0 - label_smoothing
      smooth_negatives = label_smoothing / num_classes
      one_hot_labels = one_hot_labels * smooth_positives + smooth_negatives
    cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits,
                                                            one_hot_labels,
                                                            name='xentropy')
    weight = tf.convert_to_tensor(weight,
                                  dtype=logits.dtype.base_dtype,
                                  name='loss_weight')
    loss = tf.mul(weight, tf.reduce_mean(cross_entropy), name='value')
    tf.add_to_collection(LOSSES_COLLECTION, loss)
    return loss

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for slim.losses."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import tensorflow as tf

from inception.slim import losses


class LossesTest(tf.test.TestCase):

  def testL1Loss(self):
    with self.test_session():
      shape = [5, 5, 5]
      num_elem = 5 * 5 * 5
      weights = tf.constant(1.0, shape=shape)
      wd = 0.01
      loss = losses.l1_loss(weights, wd)
      self.assertEquals(loss.op.name, 'L1Loss/value')
      self.assertAlmostEqual(loss.eval(), num_elem * wd, 5)

  def testL2Loss(self):
    with self.test_session():
      shape = [5, 5, 5]
      num_elem = 5 * 5 * 5
      weights = tf.constant(1.0, shape=shape)
      wd = 0.01
      loss = losses.l2_loss(weights, wd)
      self.assertEquals(loss.op.name, 'L2Loss/value')
      self.assertAlmostEqual(loss.eval(), num_elem * wd / 2, 5)


class RegularizersTest(tf.test.TestCase):

  def testL1Regularizer(self):
    with self.test_session():
      shape = [5, 5, 5]
      num_elem = 5 * 5 * 5
      tensor = tf.constant(1.0, shape=shape)
      loss = losses.l1_regularizer()(tensor)
      self.assertEquals(loss.op.name, 'L1Regularizer/value')
      self.assertAlmostEqual(loss.eval(), num_elem, 5)

  def testL1RegularizerWithScope(self):
    with self.test_session():
      shape = [5, 5, 5]
      num_elem = 5 * 5 * 5
      tensor = tf.constant(1.0, shape=shape)
      loss = losses.l1_regularizer(scope='L1')(tensor)
      self.assertEquals(loss.op.name, 'L1/value')
      self.assertAlmostEqual(loss.eval(), num_elem, 5)

  def testL1RegularizerWithWeight(self):
    with self.test_session():
      shape = [5, 5, 5]
      num_elem = 5 * 5 * 5
      tensor = tf.constant(1.0, shape=shape)
      weight = 0.01
      loss = losses.l1_regularizer(weight)(tensor)
      self.assertEquals(loss.op.name, 'L1Regularizer/value')
      self.assertAlmostEqual(loss.eval(), num_elem * weight, 5)

  def testL2Regularizer(self):
    with self.test_session():
      shape = [5, 5, 5]
      num_elem = 5 * 5 * 5
      tensor = tf.constant(1.0, shape=shape)
      loss = losses.l2_regularizer()(tensor)
      self.assertEquals(loss.op.name, 'L2Regularizer/value')
      self.assertAlmostEqual(loss.eval(), num_elem / 2, 5)

  def testL2RegularizerWithScope(self):
    with self.test_session():
      shape = [5, 5, 5]
      num_elem = 5 * 5 * 5
      tensor = tf.constant(1.0, shape=shape)
      loss = losses.l2_regularizer(scope='L2')(tensor)
      self.assertEquals(loss.op.name, 'L2/value')
      self.assertAlmostEqual(loss.eval(), num_elem / 2, 5)

  def testL2RegularizerWithWeight(self):
    with self.test_session():
      shape = [5, 5, 5]
      num_elem = 5 * 5 * 5
      tensor = tf.constant(1.0, shape=shape)
      weight = 0.01
      loss = losses.l2_regularizer(weight)(tensor)
      self.assertEquals(loss.op.name, 'L2Regularizer/value')
      self.assertAlmostEqual(loss.eval(), num_elem * weight / 2, 5)

  def testL1L2Regularizer(self):
    with self.test_session():
      shape = [5, 5, 5]
      num_elem = 5 * 5 * 5
      tensor = tf.constant(1.0, shape=shape)
      loss = losses.l1_l2_regularizer()(tensor)
      self.assertEquals(loss.op.name, 'L1L2Regularizer/value')
      self.assertAlmostEqual(loss.eval(), num_elem + num_elem / 2, 5)

  def testL1L2RegularizerWithScope(self):
    with self.test_session():
      shape = [5, 5, 5]
      num_elem = 5 * 5 * 5
      tensor = tf.constant(1.0, shape=shape)
      loss = losses.l1_l2_regularizer(scope='L1L2')(tensor)
      self.assertEquals(loss.op.name, 'L1L2/value')
      self.assertAlmostEqual(loss.eval(), num_elem + num_elem / 2, 5)

  def testL1L2RegularizerWithWeights(self):
    with self.test_session():
      shape = [5, 5, 5]
      num_elem = 5 * 5 * 5
      tensor = tf.constant(1.0, shape=shape)
      weight_l1 = 0.01
      weight_l2 = 0.05
      loss = losses.l1_l2_regularizer(weight_l1, weight_l2)(tensor)
      self.assertEquals(loss.op.name, 'L1L2Regularizer/value')
      self.assertAlmostEqual(loss.eval(),
                             num_elem * weight_l1 + num_elem * weight_l2 / 2, 5)


class CrossEntropyLossTest(tf.test.TestCase):

  def testCrossEntropyLossAllCorrect(self):
    with self.test_session():
      logits = tf.constant([[10.0, 0.0, 0.0],
                            [0.0, 10.0, 0.0],
                            [0.0, 0.0, 10.0]])
      labels = tf.constant([[1, 0, 0],
                            [0, 1, 0],
                            [0, 0, 1]])
      loss = losses.cross_entropy_loss(logits, labels)
      self.assertEquals(loss.op.name, 'CrossEntropyLoss/value')
      self.assertAlmostEqual(loss.eval(), 0.0, 3)

  def testCrossEntropyLossAllWrong(self):
    with self.test_session():
      logits = tf.constant([[10.0, 0.0, 0.0],
                            [0.0, 10.0, 0.0],
                            [0.0, 0.0, 10.0]])
      labels = tf.constant([[0, 0, 1],
                            [1, 0, 0],
                            [0, 1, 0]])
      loss = losses.cross_entropy_loss(logits, labels)
      self.assertEquals(loss.op.name, 'CrossEntropyLoss/value')
      self.assertAlmostEqual(loss.eval(), 10.0, 3)

  def testCrossEntropyLossAllWrongWithWeight(self):
    with self.test_session():
      logits = tf.constant([[10.0, 0.0, 0.0],
                            [0.0, 10.0, 0.0],
                            [0.0, 0.0, 10.0]])
      labels = tf.constant([[0, 0, 1],
                            [1, 0, 0],
                            [0, 1, 0]])
      loss = losses.cross_entropy_loss(logits, labels, weight=0.5)
      self.assertEquals(loss.op.name, 'CrossEntropyLoss/value')
      self.assertAlmostEqual(loss.eval(), 5.0, 3)

if __name__ == '__main__':
  tf.test.main()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for slim.variables."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

from inception.slim import scopes
from inception.slim import variables


class VariablesTest(tf.test.TestCase):

  def testCreateVariable(self):
    with self.test_session():
      with tf.variable_scope('A'):
        a = variables.variable('a', [5])
        self.assertEquals(a.op.name, 'A/a')
        self.assertListEqual(a.get_shape().as_list(), [5])

  def testGetVariables(self):
    with self.test_session():
      with tf.variable_scope('A'):
        a = variables.variable('a', [5])
      with tf.variable_scope('B'):
        b = variables.variable('a', [5])
      self.assertEquals([a, b], variables.get_variables())
      self.assertEquals([a], variables.get_variables('A'))
      self.assertEquals([b], variables.get_variables('B'))

  def testGetVariablesSuffix(self):
    with self.test_session():
      with tf.variable_scope('A'):
        a = variables.variable('a', [5])
      with tf.variable_scope('A'):
        b = variables.variable('b', [5])
      self.assertEquals([a], variables.get_variables(suffix='a'))
      self.assertEquals([b], variables.get_variables(suffix='b'))

  def testGetVariableWithSingleVar(self):
    with self.test_session():
      with tf.variable_scope('parent'):
        a = variables.variable('child', [5])
      self.assertEquals(a, variables.get_unique_variable('parent/child'))

  def testGetVariableWithDistractors(self):
    with self.test_session():
      with tf.variable_scope('parent'):
        a = variables.variable('child', [5])
        with tf.variable_scope('child'):
          variables.variable('grandchild1', [7])
          variables.variable('grandchild2', [9])
      self.assertEquals(a, variables.get_unique_variable('parent/child'))

  def testGetVariableThrowsExceptionWithNoMatch(self):
    var_name = 'cant_find_me'
    with self.test_session():
      with self.assertRaises(ValueError):
        variables.get_unique_variable(var_name)

  def testGetThrowsExceptionWithChildrenButNoMatch(self):
    var_name = 'parent/child'
    with self.test_session():
      with tf.variable_scope(var_name):
        variables.variable('grandchild1', [7])
        variables.variable('grandchild2', [9])
      with self.assertRaises(ValueError):
        variables.get_unique_variable(var_name)

  def testGetVariablesToRestore(self):
    with self.test_session():
      with tf.variable_scope('A'):
        a = variables.variable('a', [5])
      with tf.variable_scope('B'):
        b = variables.variable('a', [5])
      self.assertEquals([a, b], variables.get_variables_to_restore())

  def testNoneGetVariablesToRestore(self):
    with self.test_session():
      with tf.variable_scope('A'):
        a = variables.variable('a', [5], restore=False)
      with tf.variable_scope('B'):
        b = variables.variable('a', [5], restore=False)
      self.assertEquals([], variables.get_variables_to_restore())
      self.assertEquals([a, b], variables.get_variables())

  def testGetMixedVariablesToRestore(self):
    with self.test_session():
      with tf.variable_scope('A'):
        a = variables.variable('a', [5])
        b = variables.variable('b', [5], restore=False)
      with tf.variable_scope('B'):
        c = variables.variable('c', [5])
        d = variables.variable('d', [5], restore=False)
      self.assertEquals([a, b, c, d], variables.get_variables())
      self.assertEquals([a, c], variables.get_variables_to_restore())

  def testReuseVariable(self):
    with self.test_session():
      with tf.variable_scope('A'):
        a = variables.variable('a', [])
      with tf.variable_scope('A', reuse=True):
        b = variables.variable('a', [])
      self.assertEquals(a, b)
      self.assertListEqual([a], variables.get_variables())

  def testVariableWithDevice(self):
    with self.test_session():
      with tf.variable_scope('A'):
        a = variables.variable('a', [], device='cpu:0')
        b = variables.variable('b', [], device='cpu:1')
      self.assertDeviceEqual(a.device, 'cpu:0')
      self.assertDeviceEqual(b.device, 'cpu:1')

  def testVariableWithDeviceFromScope(self):
    with self.test_session():
      with tf.device('/cpu:0'):
        a = variables.variable('a', [])
        b = variables.variable('b', [], device='cpu:1')
      self.assertDeviceEqual(a.device, 'cpu:0')
      self.assertDeviceEqual(b.device, 'cpu:1')

  def testVariableWithDeviceFunction(self):
    class DevFn(object):

      def __init__(self):
        self.counter = -1

      def __call__(self, op):
        self.counter += 1
        return 'cpu:%d' % self.counter

    with self.test_session():
      with scopes.arg_scope([variables.variable], device=DevFn()):
        a = variables.variable('a', [])
        b = variables.variable('b', [])
        c = variables.variable('c', [], device='cpu:12')
        d = variables.variable('d', [])
        with tf.device('cpu:99'):
          e_init = tf.constant(12)
        e = variables.variable('e', initializer=e_init)
      self.assertDeviceEqual(a.device, 'cpu:0')
      self.assertDeviceEqual(a.initial_value.device, 'cpu:0')
      self.assertDeviceEqual(b.device, 'cpu:1')
      self.assertDeviceEqual(b.initial_value.device, 'cpu:1')
      self.assertDeviceEqual(c.device, 'cpu:12')
      self.assertDeviceEqual(c.initial_value.device, 'cpu:12')
      self.assertDeviceEqual(d.device, 'cpu:2')
      self.assertDeviceEqual(d.initial_value.device, 'cpu:2')
      self.assertDeviceEqual(e.device, 'cpu:3')
      self.assertDeviceEqual(e.initial_value.device, 'cpu:99')

  def testVariableWithReplicaDeviceSetter(self):
    with self.test_session():
      with tf.device(tf.train.replica_device_setter(ps_tasks=2)):
        a = variables.variable('a', [])
        b = variables.variable('b', [])
        c = variables.variable('c', [], device='cpu:12')
        d = variables.variable('d', [])
        with tf.device('cpu:99'):
          e_init = tf.constant(12)
        e = variables.variable('e', initializer=e_init)
      # The values below highlight how the replica_device_setter puts initial
      # values on the worker job, and how it merges explicit devices.
      self.assertDeviceEqual(a.device, '/job:ps/task:0/cpu:0')
      self.assertDeviceEqual(a.initial_value.device, '/job:worker/cpu:0')
      self.assertDeviceEqual(b.device, '/job:ps/task:1/cpu:0')
      self.assertDeviceEqual(b.initial_value.device, '/job:worker/cpu:0')
      self.assertDeviceEqual(c.device, '/job:ps/task:0/cpu:12')
      self.assertDeviceEqual(c.initial_value.device, '/job:worker/cpu:12')
      self.assertDeviceEqual(d.device, '/job:ps/task:1/cpu:0')
      self.assertDeviceEqual(d.initial_value.device, '/job:worker/cpu:0')
      self.assertDeviceEqual(e.device, '/job:ps/task:0/cpu:0')
      self.assertDeviceEqual(e.initial_value.device, '/job:worker/cpu:99')

  def testVariableWithVariableDeviceChooser(self):

    with tf.Graph().as_default():
      device_fn = variables.VariableDeviceChooser(num_parameter_servers=2)
      with scopes.arg_scope([variables.variable], device=device_fn):
        a = variables.variable('a', [])
        b = variables.variable('b', [])
        c = variables.variable('c', [], device='cpu:12')
        d = variables.variable('d', [])
        with tf.device('cpu:99'):
          e_init = tf.constant(12)
        e = variables.variable('e', initializer=e_init)
      # The values below highlight how the VariableDeviceChooser puts initial
      # values on the same device as the variable job.
      self.assertDeviceEqual(a.device, '/job:ps/task:0/cpu:0')
      self.assertDeviceEqual(a.initial_value.device, a.device)
      self.assertDeviceEqual(b.device, '/job:ps/task:1/cpu:0')
      self.assertDeviceEqual(b.initial_value.device, b.device)
      self.assertDeviceEqual(c.device, '/cpu:12')
      self.assertDeviceEqual(c.initial_value.device, c.device)
      self.assertDeviceEqual(d.device, '/job:ps/task:0/cpu:0')
      self.assertDeviceEqual(d.initial_value.device, d.device)
      self.assertDeviceEqual(e.device, '/job:ps/task:1/cpu:0')
      self.assertDeviceEqual(e.initial_value.device, '/cpu:99')

  def testVariableGPUPlacement(self):

    with tf.Graph().as_default():
      device_fn = variables.VariableDeviceChooser(placement='gpu:0')
      with scopes.arg_scope([variables.variable], device=device_fn):
        a = variables.variable('a', [])
        b = variables.variable('b', [])
        c = variables.variable('c', [], device='cpu:12')
        d = variables.variable('d', [])
        with tf.device('cpu:99'):
          e_init = tf.constant(12)
        e = variables.variable('e', initializer=e_init)
      # The values below highlight how the VariableDeviceChooser puts initial
      # values on the same device as the variable job.
      self.assertDeviceEqual(a.device, '/gpu:0')
      self.assertDeviceEqual(a.initial_value.device, a.device)
      self.assertDeviceEqual(b.device, '/gpu:0')
      self.assertDeviceEqual(b.initial_value.device, b.device)
      self.assertDeviceEqual(c.device, '/cpu:12')
      self.assertDeviceEqual(c.initial_value.device, c.device)
      self.assertDeviceEqual(d.device, '/gpu:0')
      self.assertDeviceEqual(d.initial_value.device, d.device)
      self.assertDeviceEqual(e.device, '/gpu:0')
      self.assertDeviceEqual(e.initial_value.device, '/cpu:99')

  def testVariableCollection(self):
    with self.test_session():
      a = variables.variable('a', [], collections='A')
      b = variables.variable('b', [], collections='B')
      self.assertEquals(a, tf.get_collection('A')[0])
      self.assertEquals(b, tf.get_collection('B')[0])

  def testVariableCollections(self):
    with self.test_session():
      a = variables.variable('a', [], collections=['A', 'C'])
      b = variables.variable('b', [], collections=['B', 'C'])
      self.assertEquals(a, tf.get_collection('A')[0])
      self.assertEquals(b, tf.get_collection('B')[0])

  def testVariableCollectionsWithArgScope(self):
    with self.test_session():
      with scopes.arg_scope([variables.variable], collections='A'):
        a = variables.variable('a', [])
        b = variables.variable('b', [])
      self.assertListEqual([a, b], tf.get_collection('A'))

  def testVariableCollectionsWithArgScopeNested(self):
    with self.test_session():
      with scopes.arg_scope([variables.variable], collections='A'):
        a = variables.variable('a', [])
        with scopes.arg_scope([variables.variable], collections='B'):
          b = variables.variable('b', [])
      self.assertEquals(a, tf.get_collection('A')[0])
      self.assertEquals(b, tf.get_collection('B')[0])

  def testVariableCollectionsWithArgScopeNonNested(self):
    with self.test_session():
      with scopes.arg_scope([variables.variable], collections='A'):
        a = variables.variable('a', [])
      with scopes.arg_scope([variables.variable], collections='B'):
        b = variables.variable('b', [])
      variables.variable('c', [])
      self.assertListEqual([a], tf.get_collection('A'))
      self.assertListEqual([b], tf.get_collection('B'))

  def testVariableRestoreWithArgScopeNested(self):
    with self.test_session():
      with scopes.arg_scope([variables.variable], restore=True):
        a = variables.variable('a', [])
        with scopes.arg_scope([variables.variable],
                              trainable=False,
                              collections=['A', 'B']):
          b = variables.variable('b', [])
        c = variables.variable('c', [])
      self.assertListEqual([a, b, c], variables.get_variables_to_restore())
      self.assertListEqual([a, c], tf.trainable_variables())
      self.assertListEqual([b], tf.get_collection('A'))
      self.assertListEqual([b], tf.get_collection('B'))


class GetVariablesByNameTest(tf.test.TestCase):

  def testGetVariableGivenNameScoped(self):
    with self.test_session():
      with tf.variable_scope('A'):
        a = variables.variable('a', [5])
        b = variables.variable('b', [5])
        self.assertEquals([a], variables.get_variables_by_name('a'))
        self.assertEquals([b], variables.get_variables_by_name('b'))

  def testGetVariablesByNameReturnsByValueWithScope(self):
    with self.test_session():
      with tf.variable_scope('A'):
        a = variables.variable('a', [5])
        matched_variables = variables.get_variables_by_name('a')

        # If variables.get_variables_by_name returns the list by reference, the
        # following append should persist, and be returned, in subsequent calls
        # to variables.get_variables_by_name('a').
        matched_variables.append(4)

        matched_variables = variables.get_variables_by_name('a')
        self.assertEquals([a], matched_variables)

  def testGetVariablesByNameReturnsByValueWithoutScope(self):
    with self.test_session():
      a = variables.variable('a', [5])
      matched_variables = variables.get_variables_by_name('a')

      # If variables.get_variables_by_name returns the list by reference, the
      # following append should persist, and be returned, in subsequent calls
      # to variables.get_variables_by_name('a').
      matched_variables.append(4)

      matched_variables = variables.get_variables_by_name('a')
      self.assertEquals([a], matched_variables)


class GlobalStepTest(tf.test.TestCase):

  def testStable(self):
    with tf.Graph().as_default():
      gs = variables.global_step()
      gs2 = variables.global_step()
      self.assertTrue(gs is gs2)

  def testDevice(self):
    with tf.Graph().as_default():
      with scopes.arg_scope([variables.global_step], device='/gpu:0'):
        gs = variables.global_step()
      self.assertDeviceEqual(gs.device, '/gpu:0')

  def testDeviceFn(self):
    class DevFn(object):

      def __init__(self):
        self.counter = -1

      def __call__(self, op):
        self.counter += 1
        return '/cpu:%d' % self.counter

    with tf.Graph().as_default():
      with scopes.arg_scope([variables.global_step], device=DevFn()):
        gs = variables.global_step()
        gs2 = variables.global_step()
      self.assertDeviceEqual(gs.device, '/cpu:0')
      self.assertEquals(gs, gs2)
      self.assertDeviceEqual(gs2.device, '/cpu:0')

  def testReplicaDeviceSetter(self):
    device_fn = tf.train.replica_device_setter(2)
    with tf.Graph().as_default():
      with scopes.arg_scope([variables.global_step], device=device_fn):
        gs = variables.global_step()
        gs2 = variables.global_step()
        self.assertEquals(gs, gs2)
        self.assertDeviceEqual(gs.device, '/job:ps/task:0')
        self.assertDeviceEqual(gs.initial_value.device, '/job:ps/task:0')
        self.assertDeviceEqual(gs2.device, '/job:ps/task:0')
        self.assertDeviceEqual(gs2.initial_value.device, '/job:ps/task:0')

  def testVariableWithVariableDeviceChooser(self):

    with tf.Graph().as_default():
      device_fn = variables.VariableDeviceChooser()
      with scopes.arg_scope([variables.global_step], device=device_fn):
        gs = variables.global_step()
        gs2 = variables.global_step()
        self.assertEquals(gs, gs2)
        self.assertDeviceEqual(gs.device, 'cpu:0')
        self.assertDeviceEqual(gs.initial_value.device, gs.device)
        self.assertDeviceEqual(gs2.device, 'cpu:0')
        self.assertDeviceEqual(gs2.initial_value.device, gs2.device)


if __name__ == '__main__':
  tf.test.main()

#!/usr/bin/python
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Process the ImageNet Challenge bounding boxes for TensorFlow model training.

Associate the ImageNet 2012 Challenge validation data set with labels.

The raw ImageNet validation data set is expected to reside in JPEG files
located in the following directory structure.

 data_dir/ILSVRC2012_val_00000001.JPEG
 data_dir/ILSVRC2012_val_00000002.JPEG
 ...
 data_dir/ILSVRC2012_val_00050000.JPEG

This script moves the files into a directory structure like such:
 data_dir/n01440764/ILSVRC2012_val_00000293.JPEG
 data_dir/n01440764/ILSVRC2012_val_00000543.JPEG
 ...
where 'n01440764' is the unique synset label associated with
these images.

This directory reorganization requires a mapping from validation image
number (i.e. suffix of the original file) to the associated label. This
is provided in the ImageNet development kit via a Matlab file.

In order to make life easier and divorce ourselves from Matlab, we instead
supply a custom text file that provides this mapping for us.

Sample usage:
  ./preprocess_imagenet_validation_data.py ILSVRC2012_img_val \
  imagenet_2012_validation_synset_labels.txt
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import os.path
import sys


if __name__ == '__main__':
  if len(sys.argv) < 3:
    print('Invalid usage\n'
          'usage: preprocess_imagenet_validation_data.py '
          '<validation data dir> <validation labels file>')
    sys.exit(-1)
  data_dir = sys.argv[1]
  validation_labels_file = sys.argv[2]

  # Read in the 50000 synsets associated with the validation data set.
  labels = [l.strip() for l in open(validation_labels_file).readlines()]
  unique_labels = set(labels)

  # Make all sub-directories in the validation data dir.
  for label in unique_labels:
    labeled_data_dir = os.path.join(data_dir, label)
    os.makedirs(labeled_data_dir)

  # Move all of the image to the appropriate sub-directory.
  for i in xrange(len(labels)):
    basename = 'ILSVRC2012_val_000%.5d.JPEG' % (i + 1)
    original_filename = os.path.join(data_dir, basename)
    if not os.path.exists(original_filename):
      print('Failed to find: ' % original_filename)
      sys.exit(-1)
    new_filename = os.path.join(data_dir, labels[i], basename)
    os.rename(original_filename, new_filename)

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Converts ImageNet data to TFRecords file format with Example protos.

The raw ImageNet data set is expected to reside in JPEG files located in the
following directory structure.

  data_dir/n01440764/ILSVRC2012_val_00000293.JPEG
  data_dir/n01440764/ILSVRC2012_val_00000543.JPEG
  ...

where 'n01440764' is the unique synset label associated with
these images.

The training data set consists of 1000 sub-directories (i.e. labels)
each containing 1200 JPEG images for a total of 1.2M JPEG images.

The evaluation data set consists of 1000 sub-directories (i.e. labels)
each containing 50 JPEG images for a total of 50K JPEG images.

This TensorFlow script converts the training and evaluation data into
a sharded data set consisting of 1024 and 128 TFRecord files, respectively.

  train_directory/train-00000-of-01024
  train_directory/train-00001-of-01024
  ...
  train_directory/train-00127-of-01024

and

  validation_directory/validation-00000-of-00128
  validation_directory/validation-00001-of-00128
  ...
  validation_directory/validation-00127-of-00128

Each validation TFRecord file contains ~390 records. Each training TFREcord
file contains ~1250 records. Each record within the TFRecord file is a
serialized Example proto. The Example proto contains the following fields:

  image/encoded: string containing JPEG encoded image in RGB colorspace
  image/height: integer, image height in pixels
  image/width: integer, image width in pixels
  image/colorspace: string, specifying the colorspace, always 'RGB'
  image/channels: integer, specifying the number of channels, always 3
  image/format: string, specifying the format, always'JPEG'

  image/filename: string containing the basename of the image file
            e.g. 'n01440764_10026.JPEG' or 'ILSVRC2012_val_00000293.JPEG'
  image/class/label: integer specifying the index in a classification layer.
    The label ranges from [1, 1000] where 0 is not used.
  image/class/synset: string specifying the unique ID of the label,
    e.g. 'n01440764'
  image/class/text: string specifying the human-readable version of the label
    e.g. 'red fox, Vulpes vulpes'

  image/object/bbox/xmin: list of integers specifying the 0+ human annotated
    bounding boxes
  image/object/bbox/xmax: list of integers specifying the 0+ human annotated
    bounding boxes
  image/object/bbox/ymin: list of integers specifying the 0+ human annotated
    bounding boxes
  image/object/bbox/ymax: list of integers specifying the 0+ human annotated
    bounding boxes
  image/object/bbox/label: integer specifying the index in a classification
    layer. The label ranges from [1, 1000] where 0 is not used. Note this is
    always identical to the image label.

Note that the length of xmin is identical to the length of xmax, ymin and ymax
for each example.

Running this script using 16 threads may take around ~2.5 hours on a HP Z420.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
import os
import random
import sys
import threading


import numpy as np
import tensorflow as tf

tf.app.flags.DEFINE_string('train_directory', '/tmp/',
                           'Training data directory')
tf.app.flags.DEFINE_string('validation_directory', '/tmp/',
                           'Validation data directory')
tf.app.flags.DEFINE_string('output_directory', '/tmp/',
                           'Output data directory')

tf.app.flags.DEFINE_integer('train_shards', 1024,
                            'Number of shards in training TFRecord files.')
tf.app.flags.DEFINE_integer('validation_shards', 128,
                            'Number of shards in validation TFRecord files.')

tf.app.flags.DEFINE_integer('num_threads', 8,
                            'Number of threads to preprocess the images.')

# The labels file contains a list of valid labels are held in this file.
# Assumes that the file contains entries as such:
#   n01440764
#   n01443537
#   n01484850
# where each line corresponds to a label expressed as a synset. We map
# each synset contained in the file to an integer (based on the alphabetical
# ordering). See below for details.
tf.app.flags.DEFINE_string('labels_file',
                           'imagenet_lsvrc_2015_synsets.txt',
                           'Labels file')

# This file containing mapping from synset to human-readable label.
# Assumes each line of the file looks like:
#
#   n02119247    black fox
#   n02119359    silver fox
#   n02119477    red fox, Vulpes fulva
#
# where each line corresponds to a unique mapping. Note that each line is
# formatted as <synset>\t<human readable label>.
tf.app.flags.DEFINE_string('imagenet_metadata_file',
                           'imagenet_metadata.txt',
                           'ImageNet metadata file')

# This file is the output of process_bounding_box.py
# Assumes each line of the file looks like:
#
#   n00007846_64193.JPEG,0.0060,0.2620,0.7545,0.9940
#
# where each line corresponds to one bounding box annotation associated
# with an image. Each line can be parsed as:
#
#   <JPEG file name>, <xmin>, <ymin>, <xmax>, <ymax>
#
# Note that there might exist mulitple bounding box annotations associated
# with an image file.
tf.app.flags.DEFINE_string('bounding_box_file',
                           './imagenet_2012_bounding_boxes.csv',
                           'Bounding box file')

FLAGS = tf.app.flags.FLAGS


def _int64_feature(value):
  """Wrapper for inserting int64 features into Example proto."""
  if not isinstance(value, list):
    value = [value]
  return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def _float_feature(value):
  """Wrapper for inserting float features into Example proto."""
  if not isinstance(value, list):
    value = [value]
  return tf.train.Feature(float_list=tf.train.FloatList(value=value))


def _bytes_feature(value):
  """Wrapper for inserting bytes features into Example proto."""
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def _convert_to_example(filename, image_buffer, label, synset, human, bbox,
                        height, width):
  """Build an Example proto for an example.

  Args:
    filename: string, path to an image file, e.g., '/path/to/example.JPG'
    image_buffer: string, JPEG encoding of RGB image
    label: integer, identifier for the ground truth for the network
    synset: string, unique WordNet ID specifying the label, e.g., 'n02323233'
    human: string, human-readable label, e.g., 'red fox, Vulpes vulpes'
    bbox: list of bounding boxes; each box is a list of integers
      specifying [xmin, ymin, xmax, ymax]. All boxes are assumed to belong to
      the same label as the image label.
    height: integer, image height in pixels
    width: integer, image width in pixels
  Returns:
    Example proto
  """
  xmin = []
  ymin = []
  xmax = []
  ymax = []
  for b in bbox:
    assert len(b) == 4
    # pylint: disable=expression-not-assigned
    [l.append(point) for l, point in zip([xmin, ymin, xmax, ymax], b)]
    # pylint: enable=expression-not-assigned

  colorspace = 'RGB'
  channels = 3
  image_format = 'JPEG'

  example = tf.train.Example(features=tf.train.Features(feature={
      'image/height': _int64_feature(height),
      'image/width': _int64_feature(width),
      'image/colorspace': _bytes_feature(colorspace),
      'image/channels': _int64_feature(channels),
      'image/class/label': _int64_feature(label),
      'image/class/synset': _bytes_feature(synset),
      'image/class/text': _bytes_feature(human),
      'image/object/bbox/xmin': _float_feature(xmin),
      'image/object/bbox/xmax': _float_feature(xmax),
      'image/object/bbox/ymin': _float_feature(ymin),
      'image/object/bbox/ymax': _float_feature(ymax),
      'image/object/bbox/label': _int64_feature([label] * len(xmin)),
      'image/format': _bytes_feature(image_format),
      'image/filename': _bytes_feature(os.path.basename(filename)),
      'image/encoded': _bytes_feature(image_buffer)}))
  return example


class ImageCoder(object):
  """Helper class that provides TensorFlow image coding utilities."""

  def __init__(self):
    # Create a single Session to run all image coding calls.
    self._sess = tf.Session()

    # Initializes function that converts PNG to JPEG data.
    self._png_data = tf.placeholder(dtype=tf.string)
    image = tf.image.decode_png(self._png_data, channels=3)
    self._png_to_jpeg = tf.image.encode_jpeg(image, format='rgb', quality=100)

    # Initializes function that converts CMYK JPEG data to RGB JPEG data.
    self._cmyk_data = tf.placeholder(dtype=tf.string)
    image = tf.image.decode_jpeg(self._cmyk_data, channels=0)
    self._cmyk_to_rgb = tf.image.encode_jpeg(image, format='rgb', quality=100)

    # Initializes function that decodes RGB JPEG data.
    self._decode_jpeg_data = tf.placeholder(dtype=tf.string)
    self._decode_jpeg = tf.image.decode_jpeg(self._decode_jpeg_data, channels=3)

  def png_to_jpeg(self, image_data):
    return self._sess.run(self._png_to_jpeg,
                          feed_dict={self._png_data: image_data})

  def cmyk_to_rgb(self, image_data):
    return self._sess.run(self._cmyk_to_rgb,
                          feed_dict={self._cmyk_data: image_data})

  def decode_jpeg(self, image_data):
    image = self._sess.run(self._decode_jpeg,
                           feed_dict={self._decode_jpeg_data: image_data})
    assert len(image.shape) == 3
    assert image.shape[2] == 3
    return image


def _is_png(filename):
  """Determine if a file contains a PNG format image.

  Args:
    filename: string, path of the image file.

  Returns:
    boolean indicating if the image is a PNG.
  """
  # File list from:
  # https://groups.google.com/forum/embed/?place=forum/torch7#!topic/torch7/fOSTXHIESSU
  return 'n02105855_2933.JPEG' in filename


def _is_cmyk(filename):
  """Determine if file contains a CMYK JPEG format image.

  Args:
    filename: string, path of the image file.

  Returns:
    boolean indicating if the image is a JPEG encoded with CMYK color space.
  """
  # File list from:
  # https://github.com/cytsai/ilsvrc-cmyk-image-list
  blacklist = ['n01739381_1309.JPEG', 'n02077923_14822.JPEG',
               'n02447366_23489.JPEG', 'n02492035_15739.JPEG',
               'n02747177_10752.JPEG', 'n03018349_4028.JPEG',
               'n03062245_4620.JPEG', 'n03347037_9675.JPEG',
               'n03467068_12171.JPEG', 'n03529860_11437.JPEG',
               'n03544143_17228.JPEG', 'n03633091_5218.JPEG',
               'n03710637_5125.JPEG', 'n03961711_5286.JPEG',
               'n04033995_2932.JPEG', 'n04258138_17003.JPEG',
               'n04264628_27969.JPEG', 'n04336792_7448.JPEG',
               'n04371774_5854.JPEG', 'n04596742_4225.JPEG',
               'n07583066_647.JPEG', 'n13037406_4650.JPEG']
  return filename.split('/')[-1] in blacklist


def _process_image(filename, coder):
  """Process a single image file.

  Args:
    filename: string, path to an image file e.g., '/path/to/example.JPG'.
    coder: instance of ImageCoder to provide TensorFlow image coding utils.
  Returns:
    image_buffer: string, JPEG encoding of RGB image.
    height: integer, image height in pixels.
    width: integer, image width in pixels.
  """
  # Read the image file.
  image_data = tf.gfile.FastGFile(filename, 'r').read()

  # Clean the dirty data.
  if _is_png(filename):
    # 1 image is a PNG.
    print('Converting PNG to JPEG for %s' % filename)
    image_data = coder.png_to_jpeg(image_data)
  elif _is_cmyk(filename):
    # 22 JPEG images are in CMYK colorspace.
    print('Converting CMYK to RGB for %s' % filename)
    image_data = coder.cmyk_to_rgb(image_data)

  # Decode the RGB JPEG.
  image = coder.decode_jpeg(image_data)

  # Check that image converted to RGB
  assert len(image.shape) == 3
  height = image.shape[0]
  width = image.shape[1]
  assert image.shape[2] == 3

  return image_data, height, width


def _process_image_files_batch(coder, thread_index, ranges, name, filenames,
                               synsets, labels, humans, bboxes, num_shards):
  """Processes and saves list of images as TFRecord in 1 thread.

  Args:
    coder: instance of ImageCoder to provide TensorFlow image coding utils.
    thread_index: integer, unique batch to run index is within [0, len(ranges)).
    ranges: list of pairs of integers specifying ranges of each batches to
      analyze in parallel.
    name: string, unique identifier specifying the data set
    filenames: list of strings; each string is a path to an image file
    synsets: list of strings; each string is a unique WordNet ID
    labels: list of integer; each integer identifies the ground truth
    humans: list of strings; each string is a human-readable label
    bboxes: list of bounding boxes for each image. Note that each entry in this
      list might contain from 0+ entries corresponding to the number of bounding
      box annotations for the image.
    num_shards: integer number of shards for this data set.
  """
  # Each thread produces N shards where N = int(num_shards / num_threads).
  # For instance, if num_shards = 128, and the num_threads = 2, then the first
  # thread would produce shards [0, 64).
  num_threads = len(ranges)
  assert not num_shards % num_threads
  num_shards_per_batch = int(num_shards / num_threads)

  shard_ranges = np.linspace(ranges[thread_index][0],
                             ranges[thread_index][1],
                             num_shards_per_batch + 1).astype(int)
  num_files_in_thread = ranges[thread_index][1] - ranges[thread_index][0]

  counter = 0
  for s in xrange(num_shards_per_batch):
    # Generate a sharded version of the file name, e.g. 'train-00002-of-00010'
    shard = thread_index * num_shards_per_batch + s
    output_filename = '%s-%.5d-of-%.5d' % (name, shard, num_shards)
    output_file = os.path.join(FLAGS.output_directory, output_filename)
    writer = tf.python_io.TFRecordWriter(output_file)

    shard_counter = 0
    files_in_shard = np.arange(shard_ranges[s], shard_ranges[s + 1], dtype=int)
    for i in files_in_shard:
      filename = filenames[i]
      label = labels[i]
      synset = synsets[i]
      human = humans[i]
      bbox = bboxes[i]

      image_buffer, height, width = _process_image(filename, coder)

      example = _convert_to_example(filename, image_buffer, label,
                                    synset, human, bbox,
                                    height, width)
      writer.write(example.SerializeToString())
      shard_counter += 1
      counter += 1

      if not counter % 1000:
        print('%s [thread %d]: Processed %d of %d images in thread batch.' %
              (datetime.now(), thread_index, counter, num_files_in_thread))
        sys.stdout.flush()

    print('%s [thread %d]: Wrote %d images to %s' %
          (datetime.now(), thread_index, shard_counter, output_file))
    sys.stdout.flush()
    shard_counter = 0
  print('%s [thread %d]: Wrote %d images to %d shards.' %
        (datetime.now(), thread_index, counter, num_files_in_thread))
  sys.stdout.flush()


def _process_image_files(name, filenames, synsets, labels, humans,
                         bboxes, num_shards):
  """Process and save list of images as TFRecord of Example protos.

  Args:
    name: string, unique identifier specifying the data set
    filenames: list of strings; each string is a path to an image file
    synsets: list of strings; each string is a unique WordNet ID
    labels: list of integer; each integer identifies the ground truth
    humans: list of strings; each string is a human-readable label
    bboxes: list of bounding boxes for each image. Note that each entry in this
      list might contain from 0+ entries corresponding to the number of bounding
      box annotations for the image.
    num_shards: integer number of shards for this data set.
  """
  assert len(filenames) == len(synsets)
  assert len(filenames) == len(labels)
  assert len(filenames) == len(humans)
  assert len(filenames) == len(bboxes)

  # Break all images into batches with a [ranges[i][0], ranges[i][1]].
  spacing = np.linspace(0, len(filenames), FLAGS.num_threads + 1).astype(np.int)
  ranges = []
  threads = []
  for i in xrange(len(spacing) - 1):
    ranges.append([spacing[i], spacing[i+1]])

  # Launch a thread for each batch.
  print('Launching %d threads for spacings: %s' % (FLAGS.num_threads, ranges))
  sys.stdout.flush()

  # Create a mechanism for monitoring when all threads are finished.
  coord = tf.train.Coordinator()

  # Create a generic TensorFlow-based utility for converting all image codings.
  coder = ImageCoder()

  threads = []
  for thread_index in xrange(len(ranges)):
    args = (coder, thread_index, ranges, name, filenames,
            synsets, labels, humans, bboxes, num_shards)
    t = threading.Thread(target=_process_image_files_batch, args=args)
    t.start()
    threads.append(t)

  # Wait for all the threads to terminate.
  coord.join(threads)
  print('%s: Finished writing all %d images in data set.' %
        (datetime.now(), len(filenames)))
  sys.stdout.flush()


def _find_image_files(data_dir, labels_file):
  """Build a list of all images files and labels in the data set.

  Args:
    data_dir: string, path to the root directory of images.

      Assumes that the ImageNet data set resides in JPEG files located in
      the following directory structure.

        data_dir/n01440764/ILSVRC2012_val_00000293.JPEG
        data_dir/n01440764/ILSVRC2012_val_00000543.JPEG

      where 'n01440764' is the unique synset label associated with these images.

    labels_file: string, path to the labels file.

      The list of valid labels are held in this file. Assumes that the file
      contains entries as such:
        n01440764
        n01443537
        n01484850
      where each line corresponds to a label expressed as a synset. We map
      each synset contained in the file to an integer (based on the alphabetical
      ordering) starting with the integer 1 corresponding to the synset
      contained in the first line.

      The reason we start the integer labels at 1 is to reserve label 0 as an
      unused background class.

  Returns:
    filenames: list of strings; each string is a path to an image file.
    synsets: list of strings; each string is a unique WordNet ID.
    labels: list of integer; each integer identifies the ground truth.
  """
  print('Determining list of input files and labels from %s.' % data_dir)
  challenge_synsets = [l.strip() for l in
                       tf.gfile.FastGFile(labels_file, 'r').readlines()]

  labels = []
  filenames = []
  synsets = []

  # Leave label index 0 empty as a background class.
  label_index = 1

  # Construct the list of JPEG files and labels.
  for synset in challenge_synsets:
    jpeg_file_path = '%s/%s/*.JPEG' % (data_dir, synset)
    matching_files = tf.gfile.Glob(jpeg_file_path)

    labels.extend([label_index] * len(matching_files))
    synsets.extend([synset] * len(matching_files))
    filenames.extend(matching_files)

    if not label_index % 100:
      print('Finished finding files in %d of %d classes.' % (
          label_index, len(challenge_synsets)))
    label_index += 1

  # Shuffle the ordering of all image files in order to guarantee
  # random ordering of the images with respect to label in the
  # saved TFRecord files. Make the randomization repeatable.
  shuffled_index = range(len(filenames))
  random.seed(12345)
  random.shuffle(shuffled_index)

  filenames = [filenames[i] for i in shuffled_index]
  synsets = [synsets[i] for i in shuffled_index]
  labels = [labels[i] for i in shuffled_index]

  print('Found %d JPEG files across %d labels inside %s.' %
        (len(filenames), len(challenge_synsets), data_dir))
  return filenames, synsets, labels


def _find_human_readable_labels(synsets, synset_to_human):
  """Build a list of human-readable labels.

  Args:
    synsets: list of strings; each string is a unique WordNet ID.
    synset_to_human: dict of synset to human labels, e.g.,
      'n02119022' --> 'red fox, Vulpes vulpes'

  Returns:
    List of human-readable strings corresponding to each synset.
  """
  humans = []
  for s in synsets:
    assert s in synset_to_human, ('Failed to find: %s' % s)
    humans.append(synset_to_human[s])
  return humans


def _find_image_bounding_boxes(filenames, image_to_bboxes):
  """Find the bounding boxes for a given image file.

  Args:
    filenames: list of strings; each string is a path to an image file.
    image_to_bboxes: dictionary mapping image file names to a list of
      bounding boxes. This list contains 0+ bounding boxes.
  Returns:
    List of bounding boxes for each image. Note that each entry in this
    list might contain from 0+ entries corresponding to the number of bounding
    box annotations for the image.
  """
  num_image_bbox = 0
  bboxes = []
  for f in filenames:
    basename = os.path.basename(f)
    if basename in image_to_bboxes:
      bboxes.append(image_to_bboxes[basename])
      num_image_bbox += 1
    else:
      bboxes.append([])
  print('Found %d images with bboxes out of %d images' % (
      num_image_bbox, len(filenames)))
  return bboxes


def _process_dataset(name, directory, num_shards, synset_to_human,
                     image_to_bboxes):
  """Process a complete data set and save it as a TFRecord.

  Args:
    name: string, unique identifier specifying the data set.
    directory: string, root path to the data set.
    num_shards: integer number of shards for this data set.
    synset_to_human: dict of synset to human labels, e.g.,
      'n02119022' --> 'red fox, Vulpes vulpes'
    image_to_bboxes: dictionary mapping image file names to a list of
      bounding boxes. This list contains 0+ bounding boxes.
  """
  filenames, synsets, labels = _find_image_files(directory, FLAGS.labels_file)
  humans = _find_human_readable_labels(synsets, synset_to_human)
  bboxes = _find_image_bounding_boxes(filenames, image_to_bboxes)
  _process_image_files(name, filenames, synsets, labels,
                       humans, bboxes, num_shards)


def _build_synset_lookup(imagenet_metadata_file):
  """Build lookup for synset to human-readable label.

  Args:
    imagenet_metadata_file: string, path to file containing mapping from
      synset to human-readable label.

      Assumes each line of the file looks like:

        n02119247    black fox
        n02119359    silver fox
        n02119477    red fox, Vulpes fulva

      where each line corresponds to a unique mapping. Note that each line is
      formatted as <synset>\t<human readable label>.

  Returns:
    Dictionary of synset to human labels, such as:
      'n02119022' --> 'red fox, Vulpes vulpes'
  """
  lines = tf.gfile.FastGFile(imagenet_metadata_file, 'r').readlines()
  synset_to_human = {}
  for l in lines:
    if l:
      parts = l.strip().split('\t')
      assert len(parts) == 2
      synset = parts[0]
      human = parts[1]
      synset_to_human[synset] = human
  return synset_to_human


def _build_bounding_box_lookup(bounding_box_file):
  """Build a lookup from image file to bounding boxes.

  Args:
    bounding_box_file: string, path to file with bounding boxes annotations.

      Assumes each line of the file looks like:

        n00007846_64193.JPEG,0.0060,0.2620,0.7545,0.9940

      where each line corresponds to one bounding box annotation associated
      with an image. Each line can be parsed as:

        <JPEG file name>, <xmin>, <ymin>, <xmax>, <ymax>

      Note that there might exist mulitple bounding box annotations associated
      with an image file. This file is the output of process_bounding_boxes.py.

  Returns:
    Dictionary mapping image file names to a list of bounding boxes. This list
    contains 0+ bounding boxes.
  """
  lines = tf.gfile.FastGFile(bounding_box_file, 'r').readlines()
  images_to_bboxes = {}
  num_bbox = 0
  num_image = 0
  for l in lines:
    if l:
      parts = l.split(',')
      assert len(parts) == 5, ('Failed to parse: %s' % l)
      filename = parts[0]
      xmin = float(parts[1])
      ymin = float(parts[2])
      xmax = float(parts[3])
      ymax = float(parts[4])
      box = [xmin, ymin, xmax, ymax]

      if filename not in images_to_bboxes:
        images_to_bboxes[filename] = []
        num_image += 1
      images_to_bboxes[filename].append(box)
      num_bbox += 1

  print('Successfully read %d bounding boxes '
        'across %d images.' % (num_bbox, num_image))
  return images_to_bboxes


def main(unused_argv):
  assert not FLAGS.train_shards % FLAGS.num_threads, (
      'Please make the FLAGS.num_threads commensurate with FLAGS.train_shards')
  assert not FLAGS.validation_shards % FLAGS.num_threads, (
      'Please make the FLAGS.num_threads commensurate with '
      'FLAGS.validation_shards')
  print('Saving results to %s' % FLAGS.output_directory)

  # Build a map from synset to human-readable label.
  synset_to_human = _build_synset_lookup(FLAGS.imagenet_metadata_file)
  image_to_bboxes = _build_bounding_box_lookup(FLAGS.bounding_box_file)

  # Run it!
  _process_dataset('validation', FLAGS.validation_directory,
                   FLAGS.validation_shards, synset_to_human, image_to_bboxes)
  _process_dataset('train', FLAGS.train_directory, FLAGS.train_shards,
                   synset_to_human, image_to_bboxes)


if __name__ == '__main__':
  tf.app.run()

#!/usr/bin/python
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Process the ImageNet Challenge bounding boxes for TensorFlow model training.

This script is called as

process_bounding_boxes.py <dir> [synsets-file]

Where <dir> is a directory containing the downloaded and unpacked bounding box
data. If [synsets-file] is supplied, then only the bounding boxes whose
synstes are contained within this file are returned. Note that the
[synsets-file] file contains synset ids, one per line.

The script dumps out a CSV text file in which each line contains an entry.
  n00007846_64193.JPEG,0.0060,0.2620,0.7545,0.9940

The entry can be read as:
  <JPEG file name>, <xmin>, <ymin>, <xmax>, <ymax>

The bounding box for <JPEG file name> contains two points (xmin, ymin) and
(xmax, ymax) specifying the lower-left corner and upper-right corner of a
bounding box in *relative* coordinates.

The user supplies a directory where the XML files reside. The directory
structure in the directory <dir> is assumed to look like this:

<dir>/nXXXXXXXX/nXXXXXXXX_YYYY.xml

Each XML file contains a bounding box annotation. The script:

 (1) Parses the XML file and extracts the filename, label and bounding box info.

 (2) The bounding box is specified in the XML files as integer (xmin, ymin) and
    (xmax, ymax) *relative* to image size displayed to the human annotator. The
    size of the image displayed to the human annotator is stored in the XML file
    as integer (height, width).

    Note that the displayed size will differ from the actual size of the image
    downloaded from image-net.org. To make the bounding box annotation useable,
    we convert bounding box to floating point numbers relative to displayed
    height and width of the image.

    Note that each XML file might contain N bounding box annotations.

    Note that the points are all clamped at a range of [0.0, 1.0] because some
    human annotations extend outside the range of the supplied image.

    See details here: http://image-net.org/download-bboxes

(3) By default, the script outputs all valid bounding boxes. If a
    [synsets-file] is supplied, only the subset of bounding boxes associated
    with those synsets are outputted. Importantly, one can supply a list of
    synsets in the ImageNet Challenge and output the list of bounding boxes
    associated with the training images of the ILSVRC.

    We use these bounding boxes to inform the random distortion of images
    supplied to the network.

If you run this script successfully, you will see the following output
to stderr:
> Finished processing 544546 XML files.
> Skipped 0 XML files not in ImageNet Challenge.
> Skipped 0 bounding boxes not in ImageNet Challenge.
> Wrote 615299 bounding boxes from 544546 annotated images.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import glob
import os.path
import sys
import xml.etree.ElementTree as ET


class BoundingBox(object):
  pass


def GetItem(name, root, index=0):
  count = 0
  for item in root.iter(name):
    if count == index:
      return item.text
    count += 1
  # Failed to find "index" occurrence of item.
  return -1


def GetInt(name, root, index=0):
  return int(GetItem(name, root, index))


def FindNumberBoundingBoxes(root):
  index = 0
  while True:
    if GetInt('xmin', root, index) == -1:
      break
    index += 1
  return index


def ProcessXMLAnnotation(xml_file):
  """Process a single XML file containing a bounding box."""
  # pylint: disable=broad-except
  try:
    tree = ET.parse(xml_file)
  except Exception:
    print('Failed to parse: ' + xml_file, file=sys.stderr)
    return None
  # pylint: enable=broad-except
  root = tree.getroot()

  num_boxes = FindNumberBoundingBoxes(root)
  boxes = []

  for index in xrange(num_boxes):
    box = BoundingBox()
    # Grab the 'index' annotation.
    box.xmin = GetInt('xmin', root, index)
    box.ymin = GetInt('ymin', root, index)
    box.xmax = GetInt('xmax', root, index)
    box.ymax = GetInt('ymax', root, index)

    box.width = GetInt('width', root)
    box.height = GetInt('height', root)
    box.filename = GetItem('filename', root) + '.JPEG'
    box.label = GetItem('name', root)

    xmin = float(box.xmin) / float(box.width)
    xmax = float(box.xmax) / float(box.width)
    ymin = float(box.ymin) / float(box.height)
    ymax = float(box.ymax) / float(box.height)

    # Some images contain bounding box annotations that
    # extend outside of the supplied image. See, e.g.
    # n03127925/n03127925_147.xml
    # Additionally, for some bounding boxes, the min > max
    # or the box is entirely outside of the image.
    min_x = min(xmin, xmax)
    max_x = max(xmin, xmax)
    box.xmin_scaled = min(max(min_x, 0.0), 1.0)
    box.xmax_scaled = min(max(max_x, 0.0), 1.0)

    min_y = min(ymin, ymax)
    max_y = max(ymin, ymax)
    box.ymin_scaled = min(max(min_y, 0.0), 1.0)
    box.ymax_scaled = min(max(max_y, 0.0), 1.0)

    boxes.append(box)

  return boxes

if __name__ == '__main__':
  if len(sys.argv) < 2 or len(sys.argv) > 3:
    print('Invalid usage\n'
          'usage: process_bounding_boxes.py <dir> [synsets-file]',
          file=sys.stderr)
    sys.exit(-1)

  xml_files = glob.glob(sys.argv[1] + '/*/*.xml')
  print('Identified %d XML files in %s' % (len(xml_files), sys.argv[1]),
        file=sys.stderr)

  if len(sys.argv) == 3:
    labels = set([l.strip() for l in open(sys.argv[2]).readlines()])
    print('Identified %d synset IDs in %s' % (len(labels), sys.argv[2]),
          file=sys.stderr)
  else:
    labels = None

  skipped_boxes = 0
  skipped_files = 0
  saved_boxes = 0
  saved_files = 0
  for file_index, one_file in enumerate(xml_files):
    # Example: <...>/n06470073/n00141669_6790.xml
    label = os.path.basename(os.path.dirname(one_file))

    # Determine if the annotation is from an ImageNet Challenge label.
    if labels is not None and label not in labels:
      skipped_files += 1
      continue

    bboxes = ProcessXMLAnnotation(one_file)
    assert bboxes is not None, 'No bounding boxes found in ' + one_file

    found_box = False
    for bbox in bboxes:
      if labels is not None:
        if bbox.label != label:
          # Note: There is a slight bug in the bounding box annotation data.
          # Many of the dog labels have the human label 'Scottish_deerhound'
          # instead of the synset ID 'n02092002' in the bbox.label field. As a
          # simple hack to overcome this issue, we only exclude bbox labels
          # *which are synset ID's* that do not match original synset label for
          # the XML file.
          if bbox.label in labels:
            skipped_boxes += 1
            continue

      # Guard against improperly specified boxes.
      if (bbox.xmin_scaled >= bbox.xmax_scaled or
          bbox.ymin_scaled >= bbox.ymax_scaled):
        skipped_boxes += 1
        continue

      # Note bbox.filename occasionally contains '%s' in the name. This is
      # data set noise that is fixed by just using the basename of the XML file.
      image_filename = os.path.splitext(os.path.basename(one_file))[0]
      print('%s.JPEG,%.4f,%.4f,%.4f,%.4f' %
            (image_filename,
             bbox.xmin_scaled, bbox.ymin_scaled,
             bbox.xmax_scaled, bbox.ymax_scaled))

      saved_boxes += 1
      found_box = True
    if found_box:
      saved_files += 1
    else:
      skipped_files += 1

    if not file_index % 5000:
      print('--> processed %d of %d XML files.' %
            (file_index + 1, len(xml_files)),
            file=sys.stderr)
      print('--> skipped %d boxes and %d XML files.' %
            (skipped_boxes, skipped_files), file=sys.stderr)

  print('Finished processing %d XML files.' % len(xml_files), file=sys.stderr)
  print('Skipped %d XML files not in ImageNet Challenge.' % skipped_files,
        file=sys.stderr)
  print('Skipped %d bounding boxes not in ImageNet Challenge.' % skipped_boxes,
        file=sys.stderr)
  print('Wrote %d bounding boxes from %d annotated images.' %
        (saved_boxes, saved_files),
        file=sys.stderr)
  print('Finished.', file=sys.stderr)

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Converts image data to TFRecords file format with Example protos.

The image data set is expected to reside in JPEG files located in the
following directory structure.

  data_dir/label_0/image0.jpeg
  data_dir/label_0/image1.jpg
  ...
  data_dir/label_1/weird-image.jpeg
  data_dir/label_1/my-image.jpeg
  ...

where the sub-directory is the unique label associated with these images.

This TensorFlow script converts the training and evaluation data into
a sharded data set consisting of TFRecord files

  train_directory/train-00000-of-01024
  train_directory/train-00001-of-01024
  ...
  train_directory/train-00127-of-01024

and

  validation_directory/validation-00000-of-00128
  validation_directory/validation-00001-of-00128
  ...
  validation_directory/validation-00127-of-00128

where we have selected 1024 and 128 shards for each data set. Each record
within the TFRecord file is a serialized Example proto. The Example proto
contains the following fields:

  image/encoded: string containing JPEG encoded image in RGB colorspace
  image/height: integer, image height in pixels
  image/width: integer, image width in pixels
  image/colorspace: string, specifying the colorspace, always 'RGB'
  image/channels: integer, specifying the number of channels, always 3
  image/format: string, specifying the format, always'JPEG'

  image/filename: string containing the basename of the image file
            e.g. 'n01440764_10026.JPEG' or 'ILSVRC2012_val_00000293.JPEG'
  image/class/label: integer specifying the index in a classification layer.
    The label ranges from [0, num_labels] where 0 is unused and left as
    the background class.
  image/class/text: string specifying the human-readable version of the label
    e.g. 'dog'

If you data set involves bounding boxes, please look at build_imagenet_data.py.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
import os
import random
import sys
import threading


import numpy as np
import tensorflow as tf

tf.app.flags.DEFINE_string('train_directory', '/tmp/',
                           'Training data directory')
tf.app.flags.DEFINE_string('validation_directory', '/tmp/',
                           'Validation data directory')
tf.app.flags.DEFINE_string('output_directory', '/tmp/',
                           'Output data directory')

tf.app.flags.DEFINE_integer('train_shards', 2,
                            'Number of shards in training TFRecord files.')
tf.app.flags.DEFINE_integer('validation_shards', 2,
                            'Number of shards in validation TFRecord files.')

tf.app.flags.DEFINE_integer('num_threads', 2,
                            'Number of threads to preprocess the images.')

# The labels file contains a list of valid labels are held in this file.
# Assumes that the file contains entries as such:
#   dog
#   cat
#   flower
# where each line corresponds to a label. We map each label contained in
# the file to an integer corresponding to the line number starting from 0.
tf.app.flags.DEFINE_string('labels_file', '', 'Labels file')


FLAGS = tf.app.flags.FLAGS


def _int64_feature(value):
  """Wrapper for inserting int64 features into Example proto."""
  if not isinstance(value, list):
    value = [value]
  return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def _bytes_feature(value):
  """Wrapper for inserting bytes features into Example proto."""
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def _convert_to_example(filename, image_buffer, label, text, height, width):
  """Build an Example proto for an example.

  Args:
    filename: string, path to an image file, e.g., '/path/to/example.JPG'
    image_buffer: string, JPEG encoding of RGB image
    label: integer, identifier for the ground truth for the network
    text: string, unique human-readable, e.g. 'dog'
    height: integer, image height in pixels
    width: integer, image width in pixels
  Returns:
    Example proto
  """

  colorspace = 'RGB'
  channels = 3
  image_format = 'JPEG'

  example = tf.train.Example(features=tf.train.Features(feature={
      'image/height': _int64_feature(height),
      'image/width': _int64_feature(width),
      'image/colorspace': _bytes_feature(colorspace),
      'image/channels': _int64_feature(channels),
      'image/class/label': _int64_feature(label),
      'image/class/text': _bytes_feature(text),
      'image/format': _bytes_feature(image_format),
      'image/filename': _bytes_feature(os.path.basename(filename)),
      'image/encoded': _bytes_feature(image_buffer)}))
  return example


class ImageCoder(object):
  """Helper class that provides TensorFlow image coding utilities."""

  def __init__(self):
    # Create a single Session to run all image coding calls.
    self._sess = tf.Session()

    # Initializes function that converts PNG to JPEG data.
    self._png_data = tf.placeholder(dtype=tf.string)
    image = tf.image.decode_png(self._png_data, channels=3)
    self._png_to_jpeg = tf.image.encode_jpeg(image, format='rgb', quality=100)

    # Initializes function that decodes RGB JPEG data.
    self._decode_jpeg_data = tf.placeholder(dtype=tf.string)
    self._decode_jpeg = tf.image.decode_jpeg(self._decode_jpeg_data, channels=3)

  def png_to_jpeg(self, image_data):
    return self._sess.run(self._png_to_jpeg,
                          feed_dict={self._png_data: image_data})

  def decode_jpeg(self, image_data):
    image = self._sess.run(self._decode_jpeg,
                           feed_dict={self._decode_jpeg_data: image_data})
    assert len(image.shape) == 3
    assert image.shape[2] == 3
    return image


def _is_png(filename):
  """Determine if a file contains a PNG format image.

  Args:
    filename: string, path of the image file.

  Returns:
    boolean indicating if the image is a PNG.
  """
  return '.png' in filename


def _process_image(filename, coder):
  """Process a single image file.

  Args:
    filename: string, path to an image file e.g., '/path/to/example.JPG'.
    coder: instance of ImageCoder to provide TensorFlow image coding utils.
  Returns:
    image_buffer: string, JPEG encoding of RGB image.
    height: integer, image height in pixels.
    width: integer, image width in pixels.
  """
  # Read the image file.
  image_data = tf.gfile.FastGFile(filename, 'r').read()

  # Convert any PNG to JPEG's for consistency.
  if _is_png(filename):
    print('Converting PNG to JPEG for %s' % filename)
    image_data = coder.png_to_jpeg(image_data)

  # Decode the RGB JPEG.
  image = coder.decode_jpeg(image_data)

  # Check that image converted to RGB
  assert len(image.shape) == 3
  height = image.shape[0]
  width = image.shape[1]
  assert image.shape[2] == 3

  return image_data, height, width


def _process_image_files_batch(coder, thread_index, ranges, name, filenames,
                               texts, labels, num_shards):
  """Processes and saves list of images as TFRecord in 1 thread.

  Args:
    coder: instance of ImageCoder to provide TensorFlow image coding utils.
    thread_index: integer, unique batch to run index is within [0, len(ranges)).
    ranges: list of pairs of integers specifying ranges of each batches to
      analyze in parallel.
    name: string, unique identifier specifying the data set
    filenames: list of strings; each string is a path to an image file
    texts: list of strings; each string is human readable, e.g. 'dog'
    labels: list of integer; each integer identifies the ground truth
    num_shards: integer number of shards for this data set.
  """
  # Each thread produces N shards where N = int(num_shards / num_threads).
  # For instance, if num_shards = 128, and the num_threads = 2, then the first
  # thread would produce shards [0, 64).
  num_threads = len(ranges)
  assert not num_shards % num_threads
  num_shards_per_batch = int(num_shards / num_threads)

  shard_ranges = np.linspace(ranges[thread_index][0],
                             ranges[thread_index][1],
                             num_shards_per_batch + 1).astype(int)
  num_files_in_thread = ranges[thread_index][1] - ranges[thread_index][0]

  counter = 0
  for s in xrange(num_shards_per_batch):
    # Generate a sharded version of the file name, e.g. 'train-00002-of-00010'
    shard = thread_index * num_shards_per_batch + s
    output_filename = '%s-%.5d-of-%.5d' % (name, shard, num_shards)
    output_file = os.path.join(FLAGS.output_directory, output_filename)
    writer = tf.python_io.TFRecordWriter(output_file)

    shard_counter = 0
    files_in_shard = np.arange(shard_ranges[s], shard_ranges[s + 1], dtype=int)
    for i in files_in_shard:
      filename = filenames[i]
      label = labels[i]
      text = texts[i]

      image_buffer, height, width = _process_image(filename, coder)

      example = _convert_to_example(filename, image_buffer, label,
                                    text, height, width)
      writer.write(example.SerializeToString())
      shard_counter += 1
      counter += 1

      if not counter % 1000:
        print('%s [thread %d]: Processed %d of %d images in thread batch.' %
              (datetime.now(), thread_index, counter, num_files_in_thread))
        sys.stdout.flush()

    print('%s [thread %d]: Wrote %d images to %s' %
          (datetime.now(), thread_index, shard_counter, output_file))
    sys.stdout.flush()
    shard_counter = 0
  print('%s [thread %d]: Wrote %d images to %d shards.' %
        (datetime.now(), thread_index, counter, num_files_in_thread))
  sys.stdout.flush()


def _process_image_files(name, filenames, texts, labels, num_shards):
  """Process and save list of images as TFRecord of Example protos.

  Args:
    name: string, unique identifier specifying the data set
    filenames: list of strings; each string is a path to an image file
    texts: list of strings; each string is human readable, e.g. 'dog'
    labels: list of integer; each integer identifies the ground truth
    num_shards: integer number of shards for this data set.
  """
  assert len(filenames) == len(texts)
  assert len(filenames) == len(labels)

  # Break all images into batches with a [ranges[i][0], ranges[i][1]].
  spacing = np.linspace(0, len(filenames), FLAGS.num_threads + 1).astype(np.int)
  ranges = []
  threads = []
  for i in xrange(len(spacing) - 1):
    ranges.append([spacing[i], spacing[i+1]])

  # Launch a thread for each batch.
  print('Launching %d threads for spacings: %s' % (FLAGS.num_threads, ranges))
  sys.stdout.flush()

  # Create a mechanism for monitoring when all threads are finished.
  coord = tf.train.Coordinator()

  # Create a generic TensorFlow-based utility for converting all image codings.
  coder = ImageCoder()

  threads = []
  for thread_index in xrange(len(ranges)):
    args = (coder, thread_index, ranges, name, filenames,
            texts, labels, num_shards)
    t = threading.Thread(target=_process_image_files_batch, args=args)
    t.start()
    threads.append(t)

  # Wait for all the threads to terminate.
  coord.join(threads)
  print('%s: Finished writing all %d images in data set.' %
        (datetime.now(), len(filenames)))
  sys.stdout.flush()


def _find_image_files(data_dir, labels_file):
  """Build a list of all images files and labels in the data set.

  Args:
    data_dir: string, path to the root directory of images.

      Assumes that the image data set resides in JPEG files located in
      the following directory structure.

        data_dir/dog/another-image.JPEG
        data_dir/dog/my-image.jpg

      where 'dog' is the label associated with these images.

    labels_file: string, path to the labels file.

      The list of valid labels are held in this file. Assumes that the file
      contains entries as such:
        dog
        cat
        flower
      where each line corresponds to a label. We map each label contained in
      the file to an integer starting with the integer 0 corresponding to the
      label contained in the first line.

  Returns:
    filenames: list of strings; each string is a path to an image file.
    texts: list of strings; each string is the class, e.g. 'dog'
    labels: list of integer; each integer identifies the ground truth.
  """
  print('Determining list of input files and labels from %s.' % data_dir)
  unique_labels = [l.strip() for l in tf.gfile.FastGFile(
      labels_file, 'r').readlines()]

  labels = []
  filenames = []
  texts = []

  # Leave label index 0 empty as a background class.
  label_index = 1

  # Construct the list of JPEG files and labels.
  for text in unique_labels:
    jpeg_file_path = '%s/%s/*' % (data_dir, text)
    matching_files = tf.gfile.Glob(jpeg_file_path)

    labels.extend([label_index] * len(matching_files))
    texts.extend([text] * len(matching_files))
    filenames.extend(matching_files)

    if not label_index % 100:
      print('Finished finding files in %d of %d classes.' % (
          label_index, len(labels)))
    label_index += 1

  # Shuffle the ordering of all image files in order to guarantee
  # random ordering of the images with respect to label in the
  # saved TFRecord files. Make the randomization repeatable.
  shuffled_index = range(len(filenames))
  random.seed(12345)
  random.shuffle(shuffled_index)

  filenames = [filenames[i] for i in shuffled_index]
  texts = [texts[i] for i in shuffled_index]
  labels = [labels[i] for i in shuffled_index]

  print('Found %d JPEG files across %d labels inside %s.' %
        (len(filenames), len(unique_labels), data_dir))
  return filenames, texts, labels


def _process_dataset(name, directory, num_shards, labels_file):
  """Process a complete data set and save it as a TFRecord.

  Args:
    name: string, unique identifier specifying the data set.
    directory: string, root path to the data set.
    num_shards: integer number of shards for this data set.
    labels_file: string, path to the labels file.
  """
  filenames, texts, labels = _find_image_files(directory, labels_file)
  _process_image_files(name, filenames, texts, labels, num_shards)


def main(unused_argv):
  assert not FLAGS.train_shards % FLAGS.num_threads, (
      'Please make the FLAGS.num_threads commensurate with FLAGS.train_shards')
  assert not FLAGS.validation_shards % FLAGS.num_threads, (
      'Please make the FLAGS.num_threads commensurate with '
      'FLAGS.validation_shards')
  print('Saving results to %s' % FLAGS.output_directory)

  # Run it!
  _process_dataset('validation', FLAGS.validation_directory,
                   FLAGS.validation_shards, FLAGS.labels_file)
  _process_dataset('train', FLAGS.train_directory,
                   FLAGS.train_shards, FLAGS.labels_file)


if __name__ == '__main__':
  tf.app.run()

# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import tensorflow as tf
from spatial_transformer import transformer
from scipy import ndimage
import numpy as np
import matplotlib.pyplot as plt

# %% Create a batch of three images (1600 x 1200)
# %% Image retrieved from:
# %% https://raw.githubusercontent.com/skaae/transformer_network/master/cat.jpg
im = ndimage.imread('cat.jpg')
im = im / 255.
im = im.reshape(1, 1200, 1600, 3)
im = im.astype('float32')

# %% Let the output size of the transformer be half the image size.
out_size = (600, 800)

# %% Simulate batch
batch = np.append(im, im, axis=0)
batch = np.append(batch, im, axis=0)
num_batch = 3

x = tf.placeholder(tf.float32, [None, 1200, 1600, 3])
x = tf.cast(batch, 'float32')

# %% Create localisation network and convolutional layer
with tf.variable_scope('spatial_transformer_0'):

    # %% Create a fully-connected layer with 6 output nodes
    n_fc = 6
    W_fc1 = tf.Variable(tf.zeros([1200 * 1600 * 3, n_fc]), name='W_fc1')

    # %% Zoom into the image
    initial = np.array([[0.5, 0, 0], [0, 0.5, 0]])
    initial = initial.astype('float32')
    initial = initial.flatten()

    b_fc1 = tf.Variable(initial_value=initial, name='b_fc1')
    h_fc1 = tf.matmul(tf.zeros([num_batch, 1200 * 1600 * 3]), W_fc1) + b_fc1
    h_trans = transformer(x, h_fc1, out_size)

# %% Run session
sess = tf.Session()
sess.run(tf.initialize_all_variables())
y = sess.run(h_trans, feed_dict={x: batch})

# plt.imshow(y[0])

# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================
import tensorflow as tf
from spatial_transformer import transformer
import numpy as np
from tf_utils import weight_variable, bias_variable, dense_to_one_hot

# %% Load data
mnist_cluttered = np.load('./data/mnist_sequence1_sample_5distortions5x5.npz')

X_train = mnist_cluttered['X_train']
y_train = mnist_cluttered['y_train']
X_valid = mnist_cluttered['X_valid']
y_valid = mnist_cluttered['y_valid']
X_test = mnist_cluttered['X_test']
y_test = mnist_cluttered['y_test']

# % turn from dense to one hot representation
Y_train = dense_to_one_hot(y_train, n_classes=10)
Y_valid = dense_to_one_hot(y_valid, n_classes=10)
Y_test = dense_to_one_hot(y_test, n_classes=10)

# %% Graph representation of our network

# %% Placeholders for 40x40 resolution
x = tf.placeholder(tf.float32, [None, 1600])
y = tf.placeholder(tf.float32, [None, 10])

# %% Since x is currently [batch, height*width], we need to reshape to a
# 4-D tensor to use it in a convolutional graph.  If one component of
# `shape` is the special value -1, the size of that dimension is
# computed so that the total size remains constant.  Since we haven't
# defined the batch dimension's shape yet, we use -1 to denote this
# dimension should not change size.
x_tensor = tf.reshape(x, [-1, 40, 40, 1])

# %% We'll setup the two-layer localisation network to figure out the
# %% parameters for an affine transformation of the input
# %% Create variables for fully connected layer
W_fc_loc1 = weight_variable([1600, 20])
b_fc_loc1 = bias_variable([20])

W_fc_loc2 = weight_variable([20, 6])
# Use identity transformation as starting point
initial = np.array([[1., 0, 0], [0, 1., 0]])
initial = initial.astype('float32')
initial = initial.flatten()
b_fc_loc2 = tf.Variable(initial_value=initial, name='b_fc_loc2')

# %% Define the two layer localisation network
h_fc_loc1 = tf.nn.tanh(tf.matmul(x, W_fc_loc1) + b_fc_loc1)
# %% We can add dropout for regularizing and to reduce overfitting like so:
keep_prob = tf.placeholder(tf.float32)
h_fc_loc1_drop = tf.nn.dropout(h_fc_loc1, keep_prob)
# %% Second layer
h_fc_loc2 = tf.nn.tanh(tf.matmul(h_fc_loc1_drop, W_fc_loc2) + b_fc_loc2)

# %% We'll create a spatial transformer module to identify discriminative
# %% patches
out_size = (40, 40)
h_trans = transformer(x_tensor, h_fc_loc2, out_size)

# %% We'll setup the first convolutional layer
# Weight matrix is [height x width x input_channels x output_channels]
filter_size = 3
n_filters_1 = 16
W_conv1 = weight_variable([filter_size, filter_size, 1, n_filters_1])

# %% Bias is [output_channels]
b_conv1 = bias_variable([n_filters_1])

# %% Now we can build a graph which does the first layer of convolution:
# we define our stride as batch x height x width x channels
# instead of pooling, we use strides of 2 and more layers
# with smaller filters.

h_conv1 = tf.nn.relu(
    tf.nn.conv2d(input=h_trans,
                 filter=W_conv1,
                 strides=[1, 2, 2, 1],
                 padding='SAME') +
    b_conv1)

# %% And just like the first layer, add additional layers to create
# a deep net
n_filters_2 = 16
W_conv2 = weight_variable([filter_size, filter_size, n_filters_1, n_filters_2])
b_conv2 = bias_variable([n_filters_2])
h_conv2 = tf.nn.relu(
    tf.nn.conv2d(input=h_conv1,
                 filter=W_conv2,
                 strides=[1, 2, 2, 1],
                 padding='SAME') +
    b_conv2)

# %% We'll now reshape so we can connect to a fully-connected layer:
h_conv2_flat = tf.reshape(h_conv2, [-1, 10 * 10 * n_filters_2])

# %% Create a fully-connected layer:
n_fc = 1024
W_fc1 = weight_variable([10 * 10 * n_filters_2, n_fc])
b_fc1 = bias_variable([n_fc])
h_fc1 = tf.nn.relu(tf.matmul(h_conv2_flat, W_fc1) + b_fc1)

h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

# %% And finally our softmax layer:
W_fc2 = weight_variable([n_fc, 10])
b_fc2 = bias_variable([10])
y_pred = tf.nn.softmax(tf.matmul(h_fc1_drop, W_fc2) + b_fc2)

# %% Define loss/eval/training functions
cross_entropy = -tf.reduce_sum(y * tf.log(y_pred))
opt = tf.train.AdamOptimizer()
optimizer = opt.minimize(cross_entropy)
grads = opt.compute_gradients(cross_entropy, [b_fc_loc2])

# %% Monitor accuracy
correct_prediction = tf.equal(tf.argmax(y_pred, 1), tf.argmax(y, 1))
accuracy = tf.reduce_mean(tf.cast(correct_prediction, 'float'))

# %% We now create a new session to actually perform the initialization the
# variables:
sess = tf.Session()
sess.run(tf.initialize_all_variables())


# %% We'll now train in minibatches and report accuracy, loss:
iter_per_epoch = 100
n_epochs = 500
train_size = 10000

indices = np.linspace(0, 10000 - 1, iter_per_epoch)
indices = indices.astype('int')

for epoch_i in range(n_epochs):
    for iter_i in range(iter_per_epoch - 1):
        batch_xs = X_train[indices[iter_i]:indices[iter_i+1]]
        batch_ys = Y_train[indices[iter_i]:indices[iter_i+1]]

        if iter_i % 10 == 0:
            loss = sess.run(cross_entropy,
                            feed_dict={
                                x: batch_xs,
                                y: batch_ys,
                                keep_prob: 1.0
                            })
            print('Iteration: ' + str(iter_i) + ' Loss: ' + str(loss))

        sess.run(optimizer, feed_dict={
            x: batch_xs, y: batch_ys, keep_prob: 0.8})

    print('Accuracy (%d): ' % epoch_i + str(sess.run(accuracy,
                                                     feed_dict={
                                                         x: X_valid,
                                                         y: Y_valid,
                                                         keep_prob: 1.0
                                                     })))
    # theta = sess.run(h_fc_loc2, feed_dict={
    #        x: batch_xs, keep_prob: 1.0})
    # print(theta[0])

# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

# %% Borrowed utils from here: https://github.com/pkmital/tensorflow_tutorials/
import tensorflow as tf
import numpy as np

def conv2d(x, n_filters,
           k_h=5, k_w=5,
           stride_h=2, stride_w=2,
           stddev=0.02,
           activation=lambda x: x,
           bias=True,
           padding='SAME',
           name="Conv2D"):
    """2D Convolution with options for kernel size, stride, and init deviation.
    Parameters
    ----------
    x : Tensor
        Input tensor to convolve.
    n_filters : int
        Number of filters to apply.
    k_h : int, optional
        Kernel height.
    k_w : int, optional
        Kernel width.
    stride_h : int, optional
        Stride in rows.
    stride_w : int, optional
        Stride in cols.
    stddev : float, optional
        Initialization's standard deviation.
    activation : arguments, optional
        Function which applies a nonlinearity
    padding : str, optional
        'SAME' or 'VALID'
    name : str, optional
        Variable scope to use.
    Returns
    -------
    x : Tensor
        Convolved input.
    """
    with tf.variable_scope(name):
        w = tf.get_variable(
            'w', [k_h, k_w, x.get_shape()[-1], n_filters],
            initializer=tf.truncated_normal_initializer(stddev=stddev))
        conv = tf.nn.conv2d(
            x, w, strides=[1, stride_h, stride_w, 1], padding=padding)
        if bias:
            b = tf.get_variable(
                'b', [n_filters],
                initializer=tf.truncated_normal_initializer(stddev=stddev))
            conv = conv + b
        return conv
    
def linear(x, n_units, scope=None, stddev=0.02,
           activation=lambda x: x):
    """Fully-connected network.
    Parameters
    ----------
    x : Tensor
        Input tensor to the network.
    n_units : int
        Number of units to connect to.
    scope : str, optional
        Variable scope to use.
    stddev : float, optional
        Initialization's standard deviation.
    activation : arguments, optional
        Function which applies a nonlinearity
    Returns
    -------
    x : Tensor
        Fully-connected output.
    """
    shape = x.get_shape().as_list()

    with tf.variable_scope(scope or "Linear"):
        matrix = tf.get_variable("Matrix", [shape[1], n_units], tf.float32,
                                 tf.random_normal_initializer(stddev=stddev))
        return activation(tf.matmul(x, matrix))
    
# %%
def weight_variable(shape):
    '''Helper function to create a weight variable initialized with
    a normal distribution
    Parameters
    ----------
    shape : list
        Size of weight variable
    '''
    #initial = tf.random_normal(shape, mean=0.0, stddev=0.01)
    initial = tf.zeros(shape)
    return tf.Variable(initial)

# %%
def bias_variable(shape):
    '''Helper function to create a bias variable initialized with
    a constant value.
    Parameters
    ----------
    shape : list
        Size of weight variable
    '''
    initial = tf.random_normal(shape, mean=0.0, stddev=0.01)
    return tf.Variable(initial)

# %% 
def dense_to_one_hot(labels, n_classes=2):
    """Convert class labels from scalars to one-hot vectors."""
    labels = np.array(labels)
    n_labels = labels.shape[0]
    index_offset = np.arange(n_labels) * n_classes
    labels_one_hot = np.zeros((n_labels, n_classes), dtype=np.float32)
    labels_one_hot.flat[index_offset + labels.ravel()] = 1
    return labels_one_hot

# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import tensorflow as tf


def transformer(U, theta, out_size, name='SpatialTransformer', **kwargs):
    """Spatial Transformer Layer

    Implements a spatial transformer layer as described in [1]_.
    Based on [2]_ and edited by David Dao for Tensorflow.

    Parameters
    ----------
    U : float
        The output of a convolutional net should have the
        shape [num_batch, height, width, num_channels].
    theta: float
        The output of the
        localisation network should be [num_batch, 6].
    out_size: tuple of two ints
        The size of the output of the network (height, width)

    References
    ----------
    .. [1]  Spatial Transformer Networks
            Max Jaderberg, Karen Simonyan, Andrew Zisserman, Koray Kavukcuoglu
            Submitted on 5 Jun 2015
    .. [2]  https://github.com/skaae/transformer_network/blob/master/transformerlayer.py

    Notes
    -----
    To initialize the network to the identity transform init
    ``theta`` to :
        identity = np.array([[1., 0., 0.],
                             [0., 1., 0.]])
        identity = identity.flatten()
        theta = tf.Variable(initial_value=identity)

    """

    def _repeat(x, n_repeats):
        with tf.variable_scope('_repeat'):
            rep = tf.transpose(
                tf.expand_dims(tf.ones(shape=tf.pack([n_repeats, ])), 1), [1, 0])
            rep = tf.cast(rep, 'int32')
            x = tf.matmul(tf.reshape(x, (-1, 1)), rep)
            return tf.reshape(x, [-1])

    def _interpolate(im, x, y, out_size):
        with tf.variable_scope('_interpolate'):
            # constants
            num_batch = tf.shape(im)[0]
            height = tf.shape(im)[1]
            width = tf.shape(im)[2]
            channels = tf.shape(im)[3]

            x = tf.cast(x, 'float32')
            y = tf.cast(y, 'float32')
            height_f = tf.cast(height, 'float32')
            width_f = tf.cast(width, 'float32')
            out_height = out_size[0]
            out_width = out_size[1]
            zero = tf.zeros([], dtype='int32')
            max_y = tf.cast(tf.shape(im)[1] - 1, 'int32')
            max_x = tf.cast(tf.shape(im)[2] - 1, 'int32')

            # scale indices from [-1, 1] to [0, width/height]
            x = (x + 1.0)*(width_f) / 2.0
            y = (y + 1.0)*(height_f) / 2.0

            # do sampling
            x0 = tf.cast(tf.floor(x), 'int32')
            x1 = x0 + 1
            y0 = tf.cast(tf.floor(y), 'int32')
            y1 = y0 + 1

            x0 = tf.clip_by_value(x0, zero, max_x)
            x1 = tf.clip_by_value(x1, zero, max_x)
            y0 = tf.clip_by_value(y0, zero, max_y)
            y1 = tf.clip_by_value(y1, zero, max_y)
            dim2 = width
            dim1 = width*height
            base = _repeat(tf.range(num_batch)*dim1, out_height*out_width)
            base_y0 = base + y0*dim2
            base_y1 = base + y1*dim2
            idx_a = base_y0 + x0
            idx_b = base_y1 + x0
            idx_c = base_y0 + x1
            idx_d = base_y1 + x1

            # use indices to lookup pixels in the flat image and restore
            # channels dim
            im_flat = tf.reshape(im, tf.pack([-1, channels]))
            im_flat = tf.cast(im_flat, 'float32')
            Ia = tf.gather(im_flat, idx_a)
            Ib = tf.gather(im_flat, idx_b)
            Ic = tf.gather(im_flat, idx_c)
            Id = tf.gather(im_flat, idx_d)

            # and finally calculate interpolated values
            x0_f = tf.cast(x0, 'float32')
            x1_f = tf.cast(x1, 'float32')
            y0_f = tf.cast(y0, 'float32')
            y1_f = tf.cast(y1, 'float32')
            wa = tf.expand_dims(((x1_f-x) * (y1_f-y)), 1)
            wb = tf.expand_dims(((x1_f-x) * (y-y0_f)), 1)
            wc = tf.expand_dims(((x-x0_f) * (y1_f-y)), 1)
            wd = tf.expand_dims(((x-x0_f) * (y-y0_f)), 1)
            output = tf.add_n([wa*Ia, wb*Ib, wc*Ic, wd*Id])
            return output

    def _meshgrid(height, width):
        with tf.variable_scope('_meshgrid'):
            # This should be equivalent to:
            #  x_t, y_t = np.meshgrid(np.linspace(-1, 1, width),
            #                         np.linspace(-1, 1, height))
            #  ones = np.ones(np.prod(x_t.shape))
            #  grid = np.vstack([x_t.flatten(), y_t.flatten(), ones])
            x_t = tf.matmul(tf.ones(shape=tf.pack([height, 1])),
                            tf.transpose(tf.expand_dims(tf.linspace(-1.0, 1.0, width), 1), [1, 0]))
            y_t = tf.matmul(tf.expand_dims(tf.linspace(-1.0, 1.0, height), 1),
                            tf.ones(shape=tf.pack([1, width])))

            x_t_flat = tf.reshape(x_t, (1, -1))
            y_t_flat = tf.reshape(y_t, (1, -1))

            ones = tf.ones_like(x_t_flat)
            grid = tf.concat(0, [x_t_flat, y_t_flat, ones])
            return grid

    def _transform(theta, input_dim, out_size):
        with tf.variable_scope('_transform'):
            num_batch = tf.shape(input_dim)[0]
            height = tf.shape(input_dim)[1]
            width = tf.shape(input_dim)[2]
            num_channels = tf.shape(input_dim)[3]
            theta = tf.reshape(theta, (-1, 2, 3))
            theta = tf.cast(theta, 'float32')

            # grid of (x_t, y_t, 1), eq (1) in ref [1]
            height_f = tf.cast(height, 'float32')
            width_f = tf.cast(width, 'float32')
            out_height = out_size[0]
            out_width = out_size[1]
            grid = _meshgrid(out_height, out_width)
            grid = tf.expand_dims(grid, 0)
            grid = tf.reshape(grid, [-1])
            grid = tf.tile(grid, tf.pack([num_batch]))
            grid = tf.reshape(grid, tf.pack([num_batch, 3, -1]))

            # Transform A x (x_t, y_t, 1)^T -> (x_s, y_s)
            T_g = tf.batch_matmul(theta, grid)
            x_s = tf.slice(T_g, [0, 0, 0], [-1, 1, -1])
            y_s = tf.slice(T_g, [0, 1, 0], [-1, 1, -1])
            x_s_flat = tf.reshape(x_s, [-1])
            y_s_flat = tf.reshape(y_s, [-1])

            input_transformed = _interpolate(
                input_dim, x_s_flat, y_s_flat,
                out_size)

            output = tf.reshape(
                input_transformed, tf.pack([num_batch, out_height, out_width, num_channels]))
            return output

    with tf.variable_scope(name):
        output = _transform(theta, U, out_size)
        return output


def batch_transformer(U, thetas, out_size, name='BatchSpatialTransformer'):
    """Batch Spatial Transformer Layer

    Parameters
    ----------

    U : float
        tensor of inputs [num_batch,height,width,num_channels]
    thetas : float
        a set of transformations for each input [num_batch,num_transforms,6]
    out_size : int
        the size of the output [out_height,out_width]

    Returns: float
        Tensor of size [num_batch*num_transforms,out_height,out_width,num_channels]
    """
    with tf.variable_scope(name):
        num_batch, num_transforms = map(int, thetas.get_shape().as_list()[:2])
        indices = [[i]*num_transforms for i in xrange(num_batch)]
        input_repeated = tf.gather(U, tf.reshape(indices, [-1]))
        return transformer(input_repeated, thetas, out_size)

# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""The Neural GPU Model."""

import time

import tensorflow as tf

import data_utils


def conv_linear(args, kw, kh, nin, nout, do_bias, bias_start, prefix):
  """Convolutional linear map."""
  assert args is not None
  if not isinstance(args, (list, tuple)):
    args = [args]
  with tf.variable_scope(prefix):
    k = tf.get_variable("CvK", [kw, kh, nin, nout])
    if len(args) == 1:
      res = tf.nn.conv2d(args[0], k, [1, 1, 1, 1], "SAME")
    else:
      res = tf.nn.conv2d(tf.concat(3, args), k, [1, 1, 1, 1], "SAME")
    if not do_bias: return res
    bias_term = tf.get_variable("CvB", [nout],
                                initializer=tf.constant_initializer(0.0))
    return res + bias_term + bias_start


def sigmoid_cutoff(x, cutoff):
  """Sigmoid with cutoff, e.g., 1.2sigmoid(x) - 0.1."""
  y = tf.sigmoid(x)
  if cutoff < 1.01: return y
  d = (cutoff - 1.0) / 2.0
  return tf.minimum(1.0, tf.maximum(0.0, cutoff * y - d))


def tanh_cutoff(x, cutoff):
  """Tanh with cutoff, e.g., 1.1tanh(x) cut to [-1. 1]."""
  y = tf.tanh(x)
  if cutoff < 1.01: return y
  d = (cutoff - 1.0) / 2.0
  return tf.minimum(1.0, tf.maximum(-1.0, (1.0 + d) * y))


def conv_gru(inpts, mem, kw, kh, nmaps, cutoff, prefix):
  """Convolutional GRU."""
  def conv_lin(args, suffix, bias_start):
    return conv_linear(args, kw, kh, len(args) * nmaps, nmaps, True, bias_start,
                       prefix + "/" + suffix)
  reset = sigmoid_cutoff(conv_lin(inpts + [mem], "r", 1.0), cutoff)
  # candidate = tanh_cutoff(conv_lin(inpts + [reset * mem], "c", 0.0), cutoff)
  candidate = tf.tanh(conv_lin(inpts + [reset * mem], "c", 0.0))
  gate = sigmoid_cutoff(conv_lin(inpts + [mem], "g", 1.0), cutoff)
  return gate * mem + (1 - gate) * candidate


@tf.RegisterGradient("CustomIdG")
def _custom_id_grad(_, grads):
  return grads


def quantize(t, quant_scale, max_value=1.0):
  """Quantize a tensor t with each element in [-max_value, max_value]."""
  t = tf.minimum(max_value, tf.maximum(t, -max_value))
  big = quant_scale * (t + max_value) + 0.5
  with tf.get_default_graph().gradient_override_map({"Floor": "CustomIdG"}):
    res = (tf.floor(big) / quant_scale) - max_value
  return res


def quantize_weights_op(quant_scale, max_value):
  ops = [v.assign(quantize(v, quant_scale, float(max_value)))
         for v in tf.trainable_variables()]
  return tf.group(*ops)


def relaxed_average(var_name_suffix, rx_step):
  """Calculate the average of relaxed variables having var_name_suffix."""
  relaxed_vars = []
  for l in xrange(rx_step):
    with tf.variable_scope("RX%d" % l, reuse=True):
      try:
        relaxed_vars.append(tf.get_variable(var_name_suffix))
      except ValueError:
        pass
  dsum = tf.add_n(relaxed_vars)
  avg = dsum / len(relaxed_vars)
  diff = [v - avg for v in relaxed_vars]
  davg = tf.add_n([d*d for d in diff])
  return avg, tf.reduce_sum(davg)


def relaxed_distance(rx_step):
  """Distance between relaxed variables and their average."""
  res, ops, rx_done = [], [], {}
  for v in tf.trainable_variables():
    if v.name[0:2] == "RX":
      rx_name = v.op.name[v.name.find("/") + 1:]
      if rx_name not in rx_done:
        avg, dist_loss = relaxed_average(rx_name, rx_step)
        res.append(dist_loss)
        rx_done[rx_name] = avg
      ops.append(v.assign(rx_done[rx_name]))
  return tf.add_n(res), tf.group(*ops)


def make_dense(targets, noclass):
  """Move a batch of targets to a dense 1-hot representation."""
  with tf.device("/cpu:0"):
    shape = tf.shape(targets)
    batch_size = shape[0]
    indices = targets + noclass * tf.range(0, batch_size)
    length = tf.expand_dims(batch_size * noclass, 0)
    dense = tf.sparse_to_dense(indices, length, 1.0, 0.0)
  return tf.reshape(dense, [-1, noclass])


def check_for_zero(sparse):
  """In a sparse batch of ints, make 1.0 if it's 0 and 0.0 else."""
  with tf.device("/cpu:0"):
    shape = tf.shape(sparse)
    batch_size = shape[0]
    sparse = tf.minimum(sparse, 1)
    indices = sparse + 2 * tf.range(0, batch_size)
    dense = tf.sparse_to_dense(indices, tf.expand_dims(2 * batch_size, 0),
                               1.0, 0.0)
    reshaped = tf.reshape(dense, [-1, 2])
  return tf.reshape(tf.slice(reshaped, [0, 0], [-1, 1]), [-1])


class NeuralGPU(object):
  """Neural GPU Model."""

  def __init__(self, nmaps, vec_size, niclass, noclass, dropout, rx_step,
               max_grad_norm, cutoff, nconvs, kw, kh, height, mode,
               learning_rate, pull, pull_incr, min_length, act_noise=0.0):
    # Feeds for parameters and ops to update them.
    self.global_step = tf.Variable(0, trainable=False)
    self.cur_length = tf.Variable(min_length, trainable=False)
    self.cur_length_incr_op = self.cur_length.assign_add(1)
    self.lr = tf.Variable(float(learning_rate), trainable=False)
    self.lr_decay_op = self.lr.assign(self.lr * 0.98)
    self.pull = tf.Variable(float(pull), trainable=False)
    self.pull_incr_op = self.pull.assign(self.pull * pull_incr)
    self.do_training = tf.placeholder(tf.float32, name="do_training")
    self.noise_param = tf.placeholder(tf.float32, name="noise_param")

    # Feeds for inputs, targets, outputs, losses, etc.
    self.input = []
    self.target = []
    for l in xrange(data_utils.forward_max + 1):
      self.input.append(tf.placeholder(tf.int32, name="inp{0}".format(l)))
      self.target.append(tf.placeholder(tf.int32, name="tgt{0}".format(l)))
    self.outputs = []
    self.losses = []
    self.grad_norms = []
    self.updates = []

    # Computation.
    inp0_shape = tf.shape(self.input[0])
    batch_size = inp0_shape[0]
    with tf.device("/cpu:0"):
      emb_weights = tf.get_variable(
          "embedding", [niclass, vec_size],
          initializer=tf.random_uniform_initializer(-1.7, 1.7))
      e0 = tf.scatter_update(emb_weights,
                             tf.constant(0, dtype=tf.int32, shape=[1]),
                             tf.zeros([1, vec_size]))

    adam = tf.train.AdamOptimizer(self.lr, epsilon=1e-4)

    # Main graph creation loop, for every bin in data_utils.
    self.steps = []
    for length in sorted(list(set(data_utils.bins + [data_utils.forward_max]))):
      data_utils.print_out("Creating model for bin of length %d." % length)
      start_time = time.time()
      if length > data_utils.bins[0]:
        tf.get_variable_scope().reuse_variables()

      # Embed inputs and calculate mask.
      with tf.device("/cpu:0"):
        with tf.control_dependencies([e0]):
          embedded = [tf.nn.embedding_lookup(emb_weights, self.input[l])
                      for l in xrange(length)]
        # Mask to 0-out padding space in each step.
        imask = [check_for_zero(self.input[l]) for l in xrange(length)]
        omask = [check_for_zero(self.target[l]) for l in xrange(length)]
        mask = [1.0 - (imask[i] * omask[i]) for i in xrange(length)]
        mask = [tf.reshape(m, [-1, 1]) for m in mask]
        # Use a shifted mask for step scaling and concatenated for weights.
        shifted_mask = mask + [tf.zeros_like(mask[0])]
        scales = [shifted_mask[i] * (1.0 - shifted_mask[i+1])
                  for i in xrange(length)]
        scales = [tf.reshape(s, [-1, 1, 1, 1]) for s in scales]
        mask = tf.concat(1, mask[0:length])  # batch x length
        weights = mask
        # Add a height dimension to mask to use later for masking.
        mask = tf.reshape(mask, [-1, length, 1, 1])
        mask = tf.concat(2, [mask for _ in xrange(height)]) + tf.zeros(
            tf.pack([batch_size, length, height, nmaps]), dtype=tf.float32)

      # Start is a length-list of batch-by-nmaps tensors, reshape and concat.
      start = [tf.tanh(embedded[l]) for l in xrange(length)]
      start = [tf.reshape(start[l], [-1, 1, nmaps]) for l in xrange(length)]
      start = tf.reshape(tf.concat(1, start), [-1, length, 1, nmaps])

      # First image comes from start by applying one convolution and adding 0s.
      first = conv_linear(start, 1, 1, vec_size, nmaps, True, 0.0, "input")
      first = [first] + [tf.zeros(tf.pack([batch_size, length, 1, nmaps]),
                                  dtype=tf.float32) for _ in xrange(height - 1)]
      first = tf.concat(2, first)

      # Computation steps.
      keep_prob = 1.0 - self.do_training * (dropout * 8.0 / float(length))
      step = [tf.nn.dropout(first, keep_prob) * mask]
      act_noise_scale = act_noise * self.do_training * self.pull
      outputs = []
      for it in xrange(length):
        with tf.variable_scope("RX%d" % (it % rx_step)) as vs:
          if it >= rx_step:
            vs.reuse_variables()
          cur = step[it]
          # Do nconvs-many CGRU steps.
          for layer in xrange(nconvs):
            cur = conv_gru([], cur, kw, kh, nmaps, cutoff, "cgru_%d" % layer)
            cur *= mask
          outputs.append(tf.slice(cur, [0, 0, 0, 0], [-1, -1, 1, -1]))
          cur = tf.nn.dropout(cur, keep_prob)
          if act_noise > 0.00001:
            cur += tf.truncated_normal(tf.shape(cur)) * act_noise_scale
          step.append(cur * mask)

      self.steps.append([tf.reshape(s, [-1, length, height * nmaps])
                         for s in step])
      # Output is the n-th step output; n = current length, as in scales.
      output = tf.add_n([outputs[i] * scales[i] for i in xrange(length)])
      # Final convolution to get logits, list outputs.
      output = conv_linear(output, 1, 1, nmaps, noclass, True, 0.0, "output")
      output = tf.reshape(output, [-1, length, noclass])
      external_output = [tf.reshape(o, [-1, noclass])
                         for o in list(tf.split(1, length, output))]
      external_output = [tf.nn.softmax(o) for o in external_output]
      self.outputs.append(external_output)

      # Calculate cross-entropy loss and normalize it.
      targets = tf.concat(1, [make_dense(self.target[l], noclass)
                              for l in xrange(length)])
      targets = tf.reshape(targets, [-1, noclass])
      xent = tf.reshape(tf.nn.softmax_cross_entropy_with_logits(
          tf.reshape(output, [-1, noclass]), targets), [-1, length])
      perp_loss = tf.reduce_sum(xent * weights)
      perp_loss /= tf.cast(batch_size, dtype=tf.float32)
      perp_loss /= length

      # Final loss: cross-entropy + shared parameter relaxation part.
      relax_dist, self.avg_op = relaxed_distance(rx_step)
      total_loss = perp_loss + relax_dist * self.pull
      self.losses.append(perp_loss)

      # Gradients and Adam update operation.
      if length == data_utils.bins[0] or (mode == 0 and
                                          length < data_utils.bins[-1] + 1):
        data_utils.print_out("Creating backward for bin of length %d." % length)
        params = tf.trainable_variables()
        grads = tf.gradients(total_loss, params)
        grads, norm = tf.clip_by_global_norm(grads, max_grad_norm)
        self.grad_norms.append(norm)
        for grad in grads:
          if isinstance(grad, tf.Tensor):
            grad += tf.truncated_normal(tf.shape(grad)) * self.noise_param
        update = adam.apply_gradients(zip(grads, params),
                                      global_step=self.global_step)
        self.updates.append(update)
      data_utils.print_out("Created model for bin of length %d in"
                           " %.2f s." % (length, time.time() - start_time))
    self.saver = tf.train.Saver(tf.all_variables())

  def step(self, sess, inp, target, do_backward, noise_param=None,
           get_steps=False):
    """Run a step of the network."""
    assert len(inp) == len(target)
    length = len(target)
    feed_in = {}
    feed_in[self.noise_param.name] = noise_param if noise_param else 0.0
    feed_in[self.do_training.name] = 1.0 if do_backward else 0.0
    feed_out = []
    index = len(data_utils.bins)
    if length < data_utils.bins[-1] + 1:
      index = data_utils.bins.index(length)
    if do_backward:
      feed_out.append(self.updates[index])
      feed_out.append(self.grad_norms[index])
    feed_out.append(self.losses[index])
    for l in xrange(length):
      feed_in[self.input[l].name] = inp[l]
    for l in xrange(length):
      feed_in[self.target[l].name] = target[l]
      feed_out.append(self.outputs[index][l])
    if get_steps:
      for l in xrange(length+1):
        feed_out.append(self.steps[index][l])
    res = sess.run(feed_out, feed_in)
    offset = 0
    norm = None
    if do_backward:
      offset = 2
      norm = res[1]
    outputs = res[offset + 1:offset + 1 + length]
    steps = res[offset + 1 + length:] if get_steps else None
    return res[offset], outputs, norm, steps

# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Convolutional Gated Recurrent Networks for Algorithm Learning."""

import math
import random
import sys
import time

import numpy as np
import tensorflow as tf

from tensorflow.python.platform import gfile

FLAGS = tf.app.flags.FLAGS

bins = [8, 12, 16, 20, 24, 28, 32, 36, 40, 48, 64, 128]
all_tasks = ["sort", "kvsort", "id", "rev", "rev2", "incr", "add", "left",
             "right", "left-shift", "right-shift", "bmul", "mul", "dup",
             "badd", "qadd", "search"]
forward_max = 128
log_filename = ""


def pad(l):
  for b in bins:
    if b >= l: return b
  return forward_max


train_set = {}
test_set = {}
for some_task in all_tasks:
  train_set[some_task] = []
  test_set[some_task] = []
  for all_max_len in xrange(10000):
    train_set[some_task].append([])
    test_set[some_task].append([])


def add(n1, n2, base=10):
  """Add two numbers represented as lower-endian digit lists."""
  k = max(len(n1), len(n2)) + 1
  d1 = n1 + [0 for _ in xrange(k - len(n1))]
  d2 = n2 + [0 for _ in xrange(k - len(n2))]
  res = []
  carry = 0
  for i in xrange(k):
    if d1[i] + d2[i] + carry < base:
      res.append(d1[i] + d2[i] + carry)
      carry = 0
    else:
      res.append(d1[i] + d2[i] + carry - base)
      carry = 1
  while res and res[-1] == 0:
    res = res[:-1]
  if res: return res
  return [0]


def init_data(task, length, nbr_cases, nclass):
  """Data initialization."""
  def rand_pair(l, task):
    """Random data pair for a task. Total length should be <= l."""
    k = (l-1)/2
    base = 10
    if task[0] == "b": base = 2
    if task[0] == "q": base = 4
    d1 = [np.random.randint(base) for _ in xrange(k)]
    d2 = [np.random.randint(base) for _ in xrange(k)]
    if task in ["add", "badd", "qadd"]:
      res = add(d1, d2, base)
    elif task in ["mul", "bmul"]:
      d1n = sum([d * (base ** i) for i, d in enumerate(d1)])
      d2n = sum([d * (base ** i) for i, d in enumerate(d2)])
      if task == "bmul":
        res = [int(x) for x in list(reversed(str(bin(d1n * d2n))))[:-2]]
      else:
        res = [int(x) for x in list(reversed(str(d1n * d2n)))]
    else:
      sys.exit()
    sep = [12]
    if task in ["add", "badd", "qadd"]: sep = [11]
    inp = [d + 1 for d in d1] + sep + [d + 1 for d in d2]
    return inp, [r + 1 for r in res]

  def rand_dup_pair(l):
    """Random data pair for duplication task. Total length should be <= l."""
    k = l/2
    x = [np.random.randint(nclass - 1) + 1 for _ in xrange(k)]
    inp = x + [0 for _ in xrange(l - k)]
    res = x + x + [0 for _ in xrange(l - 2*k)]
    return inp, res

  def rand_rev2_pair(l):
    """Random data pair for reverse2 task. Total length should be <= l."""
    inp = [(np.random.randint(nclass - 1) + 1,
            np.random.randint(nclass - 1) + 1) for _ in xrange(l/2)]
    res = [i for i in reversed(inp)]
    return [x for p in inp for x in p], [x for p in res for x in p]

  def rand_search_pair(l):
    """Random data pair for search task. Total length should be <= l."""
    inp = [(np.random.randint(nclass - 1) + 1,
            np.random.randint(nclass - 1) + 1) for _ in xrange(l-1/2)]
    q = np.random.randint(nclass - 1) + 1
    res = 0
    for (k, v) in reversed(inp):
      if k == q:
        res = v
    return [x for p in inp for x in p] + [q], [res]

  def rand_kvsort_pair(l):
    """Random data pair for key-value sort. Total length should be <= l."""
    keys = [(np.random.randint(nclass - 1) + 1, i) for i in xrange(l/2)]
    vals = [np.random.randint(nclass - 1) + 1 for _ in xrange(l/2)]
    kv = [(k, vals[i]) for (k, i) in keys]
    sorted_kv = [(k, vals[i]) for (k, i) in sorted(keys)]
    return [x for p in kv for x in p], [x for p in sorted_kv for x in p]

  def spec(inp):
    """Return the target given the input for some tasks."""
    if task == "sort":
      return sorted(inp)
    elif task == "id":
      return inp
    elif task == "rev":
      return [i for i in reversed(inp)]
    elif task == "incr":
      carry = 1
      res = []
      for i in xrange(len(inp)):
        if inp[i] + carry < nclass:
          res.append(inp[i] + carry)
          carry = 0
        else:
          res.append(1)
          carry = 1
      return res
    elif task == "left":
      return [inp[0]]
    elif task == "right":
      return [inp[-1]]
    elif task == "left-shift":
      return [inp[l-1] for l in xrange(len(inp))]
    elif task == "right-shift":
      return [inp[l+1] for l in xrange(len(inp))]
    else:
      print_out("Unknown spec for task " + str(task))
      sys.exit()

  l = length
  cur_time = time.time()
  total_time = 0.0
  for case in xrange(nbr_cases):
    total_time += time.time() - cur_time
    cur_time = time.time()
    if l > 10000 and case % 100 == 1:
      print_out("  avg gen time %.4f s" % (total_time / float(case)))
    if task in ["add", "badd", "qadd", "bmul", "mul"]:
      i, t = rand_pair(l, task)
      train_set[task][len(i)].append([i, t])
      i, t = rand_pair(l, task)
      test_set[task][len(i)].append([i, t])
    elif task == "dup":
      i, t = rand_dup_pair(l)
      train_set[task][len(i)].append([i, t])
      i, t = rand_dup_pair(l)
      test_set[task][len(i)].append([i, t])
    elif task == "rev2":
      i, t = rand_rev2_pair(l)
      train_set[task][len(i)].append([i, t])
      i, t = rand_rev2_pair(l)
      test_set[task][len(i)].append([i, t])
    elif task == "search":
      i, t = rand_search_pair(l)
      train_set[task][len(i)].append([i, t])
      i, t = rand_search_pair(l)
      test_set[task][len(i)].append([i, t])
    elif task == "kvsort":
      i, t = rand_kvsort_pair(l)
      train_set[task][len(i)].append([i, t])
      i, t = rand_kvsort_pair(l)
      test_set[task][len(i)].append([i, t])
    else:
      inp = [np.random.randint(nclass - 1) + 1 for i in xrange(l)]
      target = spec(inp)
      train_set[task][l].append([inp, target])
      inp = [np.random.randint(nclass - 1) + 1 for i in xrange(l)]
      target = spec(inp)
      test_set[task][l].append([inp, target])


def to_symbol(i):
  """Covert ids to text."""
  if i == 0: return ""
  if i == 11: return "+"
  if i == 12: return "*"
  return str(i-1)


def to_id(s):
  """Covert text to ids."""
  if s == "+": return 11
  if s == "*": return 12
  return int(s) + 1


def get_batch(max_length, batch_size, do_train, task, offset=None, preset=None):
  """Get a batch of data, training or testing."""
  inputs = []
  targets = []
  length = max_length
  if preset is None:
    cur_set = test_set[task]
    if do_train: cur_set = train_set[task]
    while not cur_set[length]:
      length -= 1
  pad_length = pad(length)
  for b in xrange(batch_size):
    if preset is None:
      elem = random.choice(cur_set[length])
      if offset is not None and offset + b < len(cur_set[length]):
        elem = cur_set[length][offset + b]
    else:
      elem = preset
    inp, target = elem[0], elem[1]
    assert len(inp) == length
    inputs.append(inp + [0 for l in xrange(pad_length - len(inp))])
    targets.append(target + [0 for l in xrange(pad_length - len(target))])
  res_input = []
  res_target = []
  for l in xrange(pad_length):
    new_input = np.array([inputs[b][l] for b in xrange(batch_size)],
                         dtype=np.int32)
    new_target = np.array([targets[b][l] for b in xrange(batch_size)],
                          dtype=np.int32)
    res_input.append(new_input)
    res_target.append(new_target)
  return res_input, res_target


def print_out(s, newline=True):
  """Print a message out and log it to file."""
  if log_filename:
    try:
      with gfile.GFile(log_filename, mode="a") as f:
        f.write(s + ("\n" if newline else ""))
    # pylint: disable=bare-except
    except:
      sys.stdout.write("Error appending to %s\n" % log_filename)
  sys.stdout.write(s + ("\n" if newline else ""))
  sys.stdout.flush()


def decode(output):
  return [np.argmax(o, axis=1) for o in output]


def accuracy(inpt, output, target, batch_size, nprint):
  """Calculate output accuracy given target."""
  assert nprint < batch_size + 1
  def task_print(inp, output, target):
    stop_bound = 0
    print_len = 0
    while print_len < len(target) and target[print_len] > stop_bound:
      print_len += 1
    print_out("    i: " + " ".join([str(i - 1) for i in inp if i > 0]))
    print_out("    o: " +
              " ".join([str(output[l] - 1) for l in xrange(print_len)]))
    print_out("    t: " +
              " ".join([str(target[l] - 1) for l in xrange(print_len)]))
  decoded_target = target
  decoded_output = decode(output)
  total = 0
  errors = 0
  seq = [0 for b in xrange(batch_size)]
  for l in xrange(len(decoded_output)):
    for b in xrange(batch_size):
      if decoded_target[l][b] > 0:
        total += 1
        if decoded_output[l][b] != decoded_target[l][b]:
          seq[b] = 1
          errors += 1
  e = 0  # Previous error index
  for _ in xrange(min(nprint, sum(seq))):
    while seq[e] == 0:
      e += 1
    task_print([inpt[l][e] for l in xrange(len(inpt))],
               [decoded_output[l][e] for l in xrange(len(decoded_target))],
               [decoded_target[l][e] for l in xrange(len(decoded_target))])
    e += 1
  for b in xrange(nprint - errors):
    task_print([inpt[l][b] for l in xrange(len(inpt))],
               [decoded_output[l][b] for l in xrange(len(decoded_target))],
               [decoded_target[l][b] for l in xrange(len(decoded_target))])
  return errors, total, sum(seq)


def safe_exp(x):
  perp = 10000
  if x < 100: perp = math.exp(x)
  if perp > 10000: return 10000
  return perp

# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Neural GPU for Learning Algorithms."""

import math
import os
import random
import sys
import time

import matplotlib.animation as anim
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf

from tensorflow.python.platform import gfile

import data_utils as data
import neural_gpu

tf.app.flags.DEFINE_float("lr", 0.001, "Learning rate.")
tf.app.flags.DEFINE_float("init_weight", 1.0, "Initial weights deviation.")
tf.app.flags.DEFINE_float("max_grad_norm", 1.0, "Clip gradients to this norm.")
tf.app.flags.DEFINE_float("cutoff", 1.2, "Cutoff at the gates.")
tf.app.flags.DEFINE_float("pull", 0.0005, "Starting pull of the relaxations.")
tf.app.flags.DEFINE_float("pull_incr", 1.2, "Increase pull by that much.")
tf.app.flags.DEFINE_float("curriculum_bound", 0.15, "Move curriculum < this.")
tf.app.flags.DEFINE_float("dropout", 0.15, "Dropout that much.")
tf.app.flags.DEFINE_float("grad_noise_scale", 0.0, "Gradient noise scale.")
tf.app.flags.DEFINE_integer("batch_size", 32, "Batch size.")
tf.app.flags.DEFINE_integer("low_batch_size", 16, "Low batch size.")
tf.app.flags.DEFINE_integer("steps_per_checkpoint", 200, "Steps per epoch.")
tf.app.flags.DEFINE_integer("nmaps", 128, "Number of floats in each cell.")
tf.app.flags.DEFINE_integer("niclass", 33, "Number of classes (0 is padding).")
tf.app.flags.DEFINE_integer("noclass", 33, "Number of classes (0 is padding).")
tf.app.flags.DEFINE_integer("train_data_size", 5000, "Training examples/len.")
tf.app.flags.DEFINE_integer("max_length", 41, "Maximum length.")
tf.app.flags.DEFINE_integer("rx_step", 6, "Relax that many recursive steps.")
tf.app.flags.DEFINE_integer("random_seed", 125459, "Random seed.")
tf.app.flags.DEFINE_integer("nconvs", 2, "How many convolutions / 1 step.")
tf.app.flags.DEFINE_integer("kw", 3, "Kernel width.")
tf.app.flags.DEFINE_integer("kh", 3, "Kernel height.")
tf.app.flags.DEFINE_integer("height", 4, "Height.")
tf.app.flags.DEFINE_integer("forward_max", 401, "Maximum forward length.")
tf.app.flags.DEFINE_integer("jobid", -1, "Task id when running on borg.")
tf.app.flags.DEFINE_integer("nprint", 0, "How many test examples to print out.")
tf.app.flags.DEFINE_integer("mode", 0, "Mode: 0-train other-decode.")
tf.app.flags.DEFINE_bool("animate", False, "Whether to produce an animation.")
tf.app.flags.DEFINE_bool("quantize", False, "Whether to quantize variables.")
tf.app.flags.DEFINE_string("task", "rev", "Which task are we learning?")
tf.app.flags.DEFINE_string("train_dir", "/tmp/", "Directory to store models.")
tf.app.flags.DEFINE_string("ensemble", "", "Model paths for ensemble.")

FLAGS = tf.app.flags.FLAGS
EXTRA_EVAL = 12


def initialize(sess):
  """Initialize data and model."""
  if FLAGS.jobid >= 0:
    data.log_filename = os.path.join(FLAGS.train_dir, "log%d" % FLAGS.jobid)
  data.print_out("NN ", newline=False)

  # Set random seed.
  seed = FLAGS.random_seed + max(0, FLAGS.jobid)
  tf.set_random_seed(seed)
  random.seed(seed)
  np.random.seed(seed)

  # Check data sizes.
  assert data.bins
  min_length = 3
  max_length = min(FLAGS.max_length, data.bins[-1])
  assert max_length + 1 > min_length
  while len(data.bins) > 1 and data.bins[-2] > max_length + EXTRA_EVAL:
    data.bins = data.bins[:-1]
  assert data.bins[0] > FLAGS.rx_step
  data.forward_max = max(FLAGS.forward_max, data.bins[-1])
  nclass = min(FLAGS.niclass, FLAGS.noclass)
  data_size = FLAGS.train_data_size if FLAGS.mode == 0 else 1000

  # Initialize data for each task.
  tasks = FLAGS.task.split("-")
  for t in tasks:
    for l in xrange(max_length + EXTRA_EVAL - 1):
      data.init_data(t, l, data_size, nclass)
    data.init_data(t, data.bins[-2], data_size, nclass)
    data.init_data(t, data.bins[-1], data_size, nclass)
    end_size = 4 * 1024 if FLAGS.mode > 0 else 1024
    data.init_data(t, data.forward_max, end_size, nclass)

  # Print out parameters.
  curriculum = FLAGS.curriculum_bound
  msg1 = ("layers %d kw %d h %d kh %d relax %d batch %d noise %.2f task %s"
          % (FLAGS.nconvs, FLAGS.kw, FLAGS.height, FLAGS.kh, FLAGS.rx_step,
             FLAGS.batch_size, FLAGS.grad_noise_scale, FLAGS.task))
  msg2 = "data %d %s" % (FLAGS.train_data_size, msg1)
  msg3 = ("cut %.2f pull %.3f lr %.2f iw %.2f cr %.2f nm %d d%.4f gn %.2f %s" %
          (FLAGS.cutoff, FLAGS.pull_incr, FLAGS.lr, FLAGS.init_weight,
           curriculum, FLAGS.nmaps, FLAGS.dropout, FLAGS.max_grad_norm, msg2))
  data.print_out(msg3)

  # Create checkpoint directory if it does not exist.
  checkpoint_dir = os.path.join(FLAGS.train_dir, "neural_gpu%s"
                                % ("" if FLAGS.jobid < 0 else str(FLAGS.jobid)))
  if not gfile.IsDirectory(checkpoint_dir):
    data.print_out("Creating checkpoint directory %s." % checkpoint_dir)
    gfile.MkDir(checkpoint_dir)

  # Create model and initialize it.
  tf.get_variable_scope().set_initializer(
      tf.uniform_unit_scaling_initializer(factor=1.8 * FLAGS.init_weight))
  model = neural_gpu.NeuralGPU(
      FLAGS.nmaps, FLAGS.nmaps, FLAGS.niclass, FLAGS.noclass, FLAGS.dropout,
      FLAGS.rx_step, FLAGS.max_grad_norm, FLAGS.cutoff, FLAGS.nconvs,
      FLAGS.kw, FLAGS.kh, FLAGS.height, FLAGS.mode, FLAGS.lr,
      FLAGS.pull, FLAGS.pull_incr, min_length + 3)
  data.print_out("Created model.")
  sess.run(tf.initialize_all_variables())
  data.print_out("Initialized variables.")

  # Load model from parameters if a checkpoint exists.
  ckpt = tf.train.get_checkpoint_state(checkpoint_dir)
  if ckpt and gfile.Exists(ckpt.model_checkpoint_path):
    data.print_out("Reading model parameters from %s"
                   % ckpt.model_checkpoint_path)
    model.saver.restore(sess, ckpt.model_checkpoint_path)

  # Check if there are ensemble models and get their checkpoints.
  ensemble = []
  ensemble_dir_list = [d for d in FLAGS.ensemble.split(",") if d]
  for ensemble_dir in ensemble_dir_list:
    ckpt = tf.train.get_checkpoint_state(ensemble_dir)
    if ckpt and gfile.Exists(ckpt.model_checkpoint_path):
      data.print_out("Found ensemble model %s" % ckpt.model_checkpoint_path)
      ensemble.append(ckpt.model_checkpoint_path)

  # Return the model and needed variables.
  return (model, min_length, max_length, checkpoint_dir, curriculum, ensemble)


def single_test(l, model, sess, task, nprint, batch_size, print_out=True,
                offset=None, ensemble=None, get_steps=False):
  """Test model on test data of length l using the given session."""
  inpt, target = data.get_batch(l, batch_size, False, task, offset)
  _, res, _, steps = model.step(sess, inpt, target, False, get_steps=get_steps)
  errors, total, seq_err = data.accuracy(inpt, res, target, batch_size, nprint)
  seq_err = float(seq_err) / batch_size
  if total > 0:
    errors = float(errors) / total
  if print_out:
    data.print_out("  %s len %d errors %.2f sequence-errors %.2f"
                   % (task, l, 100*errors, 100*seq_err))
  # Ensemble eval.
  if ensemble:
    results = []
    for m in ensemble:
      model.saver.restore(sess, m)
      _, result, _, _ = model.step(sess, inpt, target, False)
      m_errors, m_total, m_seq_err = data.accuracy(inpt, result, target,
                                                   batch_size, nprint)
      m_seq_err = float(m_seq_err) / batch_size
      if total > 0:
        m_errors = float(m_errors) / m_total
      data.print_out("     %s len %d m-errors %.2f m-sequence-errors %.2f"
                     % (task, l, 100*m_errors, 100*m_seq_err))
      results.append(result)
    ens = [sum(o) for o in zip(*results)]
    errors, total, seq_err = data.accuracy(inpt, ens, target,
                                           batch_size, nprint)
    seq_err = float(seq_err) / batch_size
    if total > 0:
      errors = float(errors) / total
    if print_out:
      data.print_out("  %s len %d ens-errors %.2f ens-sequence-errors %.2f"
                     % (task, l, 100*errors, 100*seq_err))
  return errors, seq_err, (steps, inpt, [np.argmax(o, axis=1) for o in res])


def multi_test(l, model, sess, task, nprint, batch_size, offset=None,
               ensemble=None):
  """Run multiple tests at lower batch size to save memory."""
  errors, seq_err = 0.0, 0.0
  to_print = nprint
  low_batch = FLAGS.low_batch_size
  low_batch = min(low_batch, batch_size)
  for mstep in xrange(batch_size / low_batch):
    cur_offset = None if offset is None else offset + mstep * low_batch
    err, sq_err, _ = single_test(l, model, sess, task, to_print, low_batch,
                                 False, cur_offset, ensemble=ensemble)
    to_print = max(0, to_print - low_batch)
    errors += err
    seq_err += sq_err
    if FLAGS.mode > 0:
      cur_errors = float(low_batch * errors) / ((mstep+1) * low_batch)
      cur_seq_err = float(low_batch * seq_err) / ((mstep+1) * low_batch)
      data.print_out("    %s multitest current errors %.2f sequence-errors %.2f"
                     % (task, 100*cur_errors, 100*cur_seq_err))
  errors = float(low_batch) * float(errors) / batch_size
  seq_err = float(low_batch) * float(seq_err) / batch_size
  data.print_out("  %s len %d errors %.2f sequence-errors %.2f"
                 % (task, l, 100*errors, 100*seq_err))
  return errors, seq_err


def train():
  """Train the model."""
  batch_size = FLAGS.batch_size
  tasks = FLAGS.task.split("-")
  with tf.Session() as sess:
    (model, min_length, max_length, checkpoint_dir,
     curriculum, _) = initialize(sess)
    quant_op = neural_gpu.quantize_weights_op(512, 8)
    max_cur_length = min(min_length + 3, max_length)
    prev_acc_perp = [1000000 for _ in xrange(3)]
    prev_seq_err = 1.0

    # Main traning loop.
    while True:
      global_step, pull, max_cur_length, learning_rate = sess.run(
          [model.global_step, model.pull, model.cur_length, model.lr])
      acc_loss, acc_total, acc_errors, acc_seq_err = 0.0, 0, 0, 0
      acc_grad_norm, step_count, step_time = 0.0, 0, 0.0
      for _ in xrange(FLAGS.steps_per_checkpoint):
        global_step += 1
        task = random.choice(tasks)

        # Select the length for curriculum learning.
        l = np.random.randint(max_cur_length - min_length + 1) + min_length
        # Prefer longer stuff 60% of time.
        if np.random.randint(100) < 60:
          l1 = np.random.randint(max_cur_length - min_length+1) + min_length
          l = max(l, l1)
        # Mixed curriculum learning: in 25% of cases go to any larger length.
        if np.random.randint(100) < 25:
          l1 = np.random.randint(max_length - min_length + 1) + min_length
          l = max(l, l1)

        # Run a step and time it.
        start_time = time.time()
        inp, target = data.get_batch(l, batch_size, True, task)
        noise_param = math.sqrt(math.pow(global_step, -0.55) *
                                prev_seq_err) * FLAGS.grad_noise_scale
        loss, res, gnorm, _ = model.step(sess, inp, target, True, noise_param)
        step_time += time.time() - start_time
        acc_grad_norm += float(gnorm)

        # Accumulate statistics only if we did not exceed curriculum length.
        if l < max_cur_length + 1:
          step_count += 1
          acc_loss += loss
          errors, total, seq_err = data.accuracy(inp, res, target,
                                                 batch_size, 0)
          acc_total += total
          acc_errors += errors
          acc_seq_err += seq_err

      # Normalize and print out accumulated statistics.
      acc_loss /= step_count
      step_time /= FLAGS.steps_per_checkpoint
      acc_seq_err = float(acc_seq_err) / (step_count * batch_size)
      prev_seq_err = max(0.0, acc_seq_err - 0.02)  # No noise at error < 2%.
      acc_errors = float(acc_errors) / acc_total if acc_total > 0 else 1.0
      msg1 = "step %d step-time %.2f" % (global_step, step_time)
      msg2 = "lr %.8f pull %.3f" % (learning_rate, pull)
      msg3 = ("%s %s grad-norm %.8f"
              % (msg1, msg2, acc_grad_norm / FLAGS.steps_per_checkpoint))
      data.print_out("%s len %d ppx %.8f errors %.2f sequence-errors %.2f" %
                     (msg3, max_cur_length, data.safe_exp(acc_loss),
                      100*acc_errors, 100*acc_seq_err))

      # If errors are below the curriculum threshold, move curriculum forward.
      if curriculum > acc_seq_err:
        if FLAGS.quantize:
          # Quantize weights.
          data.print_out("  Quantizing parameters.")
          sess.run([quant_op])
        # Increase current length (until the next with training data).
        do_incr = True
        while do_incr and max_cur_length < max_length:
          sess.run(model.cur_length_incr_op)
          for t in tasks:
            if data.train_set[t]: do_incr = False
        # Forget last perplexities if we're not yet at the end.
        if max_cur_length < max_length:
          prev_acc_perp.append(1000000)
        # Either increase pull or, if it's large, average parameters.
        if pull < 0.1:
          sess.run(model.pull_incr_op)
        else:
          data.print_out("  Averaging parameters.")
          sess.run(model.avg_op)
          if acc_seq_err < (curriculum / 3.0):
            sess.run(model.lr_decay_op)

      # Lower learning rate if we're worse than the last 3 checkpoints.
      acc_perp = data.safe_exp(acc_loss)
      if acc_perp > max(prev_acc_perp[-3:]):
        sess.run(model.lr_decay_op)
      prev_acc_perp.append(acc_perp)

      # Save checkpoint.
      checkpoint_path = os.path.join(checkpoint_dir, "neural_gpu.ckpt")
      model.saver.save(sess, checkpoint_path,
                       global_step=model.global_step)

      # Run evaluation.
      bound = data.bins[-1] + 1
      for t in tasks:
        l = min_length
        while l < max_length + EXTRA_EVAL and l < bound:
          _, seq_err, _ = single_test(l, model, sess, t,
                                      FLAGS.nprint, batch_size)
          l += 1
          while l < bound + 1 and not data.test_set[t][l]:
            l += 1
        if seq_err < 0.05:  # Run larger test if we're good enough.
          _, seq_err = multi_test(data.forward_max, model, sess, t,
                                  FLAGS.nprint, batch_size * 4)
      if seq_err < 0.01:  # Super-large test on 1-task large-forward models.
        if data.forward_max > 4000 and len(tasks) == 1:
          multi_test(data.forward_max, model, sess, tasks[0], FLAGS.nprint,
                     batch_size * 16, 0)


def animate(l, test_data, anim_size):
  """Create animation for the given data (hacky matplotlib use)."""
  xf = 12  # Extra frames to slow down at start and end.
  fps = 2  # Frames per step.

  # Make the figure.
  fig = plt.figure(figsize=(16, 9), facecolor="white")
  ax = fig.add_axes([0, 0, 1, 1], frameon=False, zorder=2)
  ax.set_xticks([i * 24-0.5 for i in xrange(4)])
  ax.set_xticklabels([])
  ax.set_yticks([i - 0.5 for i in xrange(l+1)])
  ax.grid(which="major", axis="both", linestyle="-", color="black")
  # We need text fields.
  text_fields = []
  text_size = 24*32/l
  for y in xrange(l):
    text_fields.append(ax.text(
        11.25, y + 0.15, "", color="g", ha="center", va="center",
        bbox={"facecolor": "b", "alpha": 0.01, "pad": 24 * text_size},
        size=text_size - (4 * 32 / l), animated=True))
  im = ax.imshow(np.zeros_like(test_data[0][0][0]), vmin=-1.0,
                 vmax=1.0, cmap="gray", aspect="auto", origin="upper",
                 interpolation="none", animated=True)
  im.set_zorder(1)

  # Main animation step.
  def animation_update(frame_no, test_data, xf, im, text_fields):
    """Update an animation frame."""
    steps, inpt, out_raw = test_data
    length = len(steps)
    batch = frame_no / (fps * (l+4*xf))
    index = int((frame_no % (fps * (l+4*xf))) / fps)
    # Cut output after first padding.
    out = [out_raw[i][batch] for i in xrange(len(text_fields))]
    if 0 in out:
      i = out.index(0)
      out = out[0:i] + [0 for _ in xrange(len(out) - i)]
    # Show the state after the first frames.
    if index >= 2*xf:
      im.set_array(steps[min(length - 1, index - 2*xf)][batch])
      for i, t in enumerate(text_fields):
        if index - 2*xf < length:
          t.set_text("")
        else:
          t.set_text(data.to_symbol(out[i]))
    else:
      for i, t in enumerate(text_fields):
        t.set_text(data.to_symbol(inpt[i][batch]) if index < xf else "")
      if index < xf:
        im.set_array(np.zeros_like(steps[0][0]))
      else:
        im.set_array(steps[0][batch])
    return im,

  # Create the animation and save to mp4.
  animation = anim.FuncAnimation(
      fig, animation_update, blit=True, frames=(l+4*xf)*anim_size*fps,
      interval=500/fps, fargs=(test_data, xf, im, text_fields))
  animation.save("/tmp/neural_gpu.mp4", writer="mencoder", fps=4*fps, dpi=3*80)


def evaluate():
  """Evaluate an existing model."""
  batch_size = FLAGS.batch_size
  tasks = FLAGS.task.split("-")
  with tf.Session() as sess:
    model, min_length, max_length, _, _, ensemble = initialize(sess)
    bound = data.bins[-1] + 1
    for t in tasks:
      l = min_length
      while l < max_length + EXTRA_EVAL and l < bound:
        _, seq_err, _ = single_test(l, model, sess, t, FLAGS.nprint,
                                    batch_size, ensemble=ensemble)
        l += 1
        while l < bound + 1 and not data.test_set[t][l]:
          l += 1
      # Animate.
      if FLAGS.animate:
        anim_size = 2
        _, _, test_data = single_test(l, model, sess, t, 0, anim_size,
                                      get_steps=True)
        animate(l, test_data, anim_size)
      # More tests.
      _, seq_err = multi_test(data.forward_max, model, sess, t, FLAGS.nprint,
                              batch_size * 4, ensemble=ensemble)
    if seq_err < 0.01:  # Super-test if we're very good and in large-test mode.
      if data.forward_max > 4000 and len(tasks) == 1:
        multi_test(data.forward_max, model, sess, tasks[0], FLAGS.nprint,
                   batch_size * 64, 0, ensemble=ensemble)


def interactive():
  """Interactively probe an existing model."""
  with tf.Session() as sess:
    model, _, _, _, _, _ = initialize(sess)
    sys.stdout.write("Input to Neural GPU, e.g., 0 1. Use -1 for PAD.\n")
    sys.stdout.write("> ")
    sys.stdout.flush()
    inpt = sys.stdin.readline()
    while inpt:
      ids = [data.to_id(s) for s in inpt.strip().split()]
      inpt, target = data.get_batch(len(ids), 1, False, "",
                                    preset=(ids, [0 for _ in ids]))
      _, res, _, _ = model.step(sess, inpt, target, False)
      res = [np.argmax(o, axis=1) for o in res]
      res = [o for o in res[:len(ids)] if o > 0]
      print "  " + " ".join([data.to_symbol(output[0]) for output in res])
      sys.stdout.write("> ")
      sys.stdout.flush()
      inpt = sys.stdin.readline()


def main(_):
  if FLAGS.mode == 0:
    train()
  elif FLAGS.mode == 1:
    evaluate()
  else:
    interactive()

if __name__ == "__main__":
  tf.app.run()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A library showing off sequence recognition and generation with the simple
example of names.

We use recurrent neural nets to learn complex functions able to recogize and
generate sequences of a given form. This can be used for natural language
syntax recognition, dynamically generating maps or puzzles and of course
baby name generation.

Before using this module, it is recommended to read the Tensorflow tutorial on
recurrent neural nets, as it explains the basic concepts of this model, and
will show off another module, the PTB module on which this model bases itself.

Here is an overview of the functions available in this module:

* RNN Module for sequence functions based on PTB

* Name recognition specifically for recognizing names, but can be adapted to
    recognizing sequence patterns

* Name generations specifically for generating names, but can be adapted to
    generating arbitrary sequence patterns
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import time

import tensorflow as tf
import numpy as np

from model import NamignizerModel
import data_utils


class SmallConfig(object):
    """Small config."""
    init_scale = 0.1
    learning_rate = 1.0
    max_grad_norm = 5
    num_layers = 2
    num_steps = 20
    hidden_size = 200
    max_epoch = 4
    max_max_epoch = 13
    keep_prob = 1.0
    lr_decay = 0.5
    batch_size = 20
    vocab_size = 27
    epoch_size = 100


class LargeConfig(object):
    """Medium config."""
    init_scale = 0.05
    learning_rate = 1.0
    max_grad_norm = 5
    num_layers = 2
    num_steps = 35
    hidden_size = 650
    max_epoch = 6
    max_max_epoch = 39
    keep_prob = 0.5
    lr_decay = 0.8
    batch_size = 20
    vocab_size = 27
    epoch_size = 100


class TestConfig(object):
    """Tiny config, for testing."""
    init_scale = 0.1
    learning_rate = 1.0
    max_grad_norm = 1
    num_layers = 1
    num_steps = 2
    hidden_size = 2
    max_epoch = 1
    max_max_epoch = 1
    keep_prob = 1.0
    lr_decay = 0.5
    batch_size = 20
    vocab_size = 27
    epoch_size = 100


def run_epoch(session, m, names, counts, epoch_size, eval_op, verbose=False):
    """Runs the model on the given data for one epoch

    Args:
        session: the tf session holding the model graph
        m: an instance of the NamignizerModel
        names: a set of lowercase names of 26 characters
        counts: a list of the frequency of the above names
        epoch_size: the number of batches to run
        eval_op: whether to change the params or not, and how to do it
    Kwargs:
        verbose: whether to print out state of training during the epoch
    Returns:
        cost: the average cost during the last stage of the epoch
    """
    start_time = time.time()
    costs = 0.0
    iters = 0
    for step, (x, y) in enumerate(data_utils.namignizer_iterator(names, counts,
                                                                 m.batch_size, m.num_steps, epoch_size)):

        cost, _ = session.run([m.cost, eval_op],
                              {m.input_data: x,
                               m.targets: y,
                               m.initial_state: m.initial_state.eval(),
                               m.weights: np.ones(m.batch_size * m.num_steps)})
        costs += cost
        iters += m.num_steps

        if verbose and step % (epoch_size // 10) == 9:
            print("%.3f perplexity: %.3f speed: %.0f lps" %
                  (step * 1.0 / epoch_size, np.exp(costs / iters),
                   iters * m.batch_size / (time.time() - start_time)))

        if step >= epoch_size:
            break

    return np.exp(costs / iters)


def train(data_dir, checkpoint_path, config):
    """Trains the model with the given data

    Args:
        data_dir: path to the data for the model (see data_utils for data
            format)
        checkpoint_path: the path to save the trained model checkpoints
        config: one of the above configs that specify the model and how it
            should be run and trained
    Returns:
        None
    """
    # Prepare Name data.
    print("Reading Name data in %s" % data_dir)
    names, counts = data_utils.read_names(data_dir)

    with tf.Graph().as_default(), tf.Session() as session:
        initializer = tf.random_uniform_initializer(-config.init_scale,
                                                    config.init_scale)
        with tf.variable_scope("model", reuse=None, initializer=initializer):
            m = NamignizerModel(is_training=True, config=config)

        tf.initialize_all_variables().run()

        for i in range(config.max_max_epoch):
            lr_decay = config.lr_decay ** max(i - config.max_epoch, 0.0)
            m.assign_lr(session, config.learning_rate * lr_decay)

            print("Epoch: %d Learning rate: %.3f" % (i + 1, session.run(m.lr)))
            train_perplexity = run_epoch(session, m, names, counts, config.epoch_size, m.train_op,
                                         verbose=True)
            print("Epoch: %d Train Perplexity: %.3f" %
                  (i + 1, train_perplexity))

            m.saver.save(session, checkpoint_path, global_step=i)


def namignize(names, checkpoint_path, config):
    """Recognizes names and prints the Perplexity of the model for each names
    in the list

    Args:
        names: a list of names in the model format
        checkpoint_path: the path to restore the trained model from, should not
            include the model name, just the path to
        config: one of the above configs that specify the model and how it
            should be run and trained
    Returns:
        None
    """
    with tf.Graph().as_default(), tf.Session() as session:

        with tf.variable_scope("model"):
            m = NamignizerModel(is_training=False, config=config)

        m.saver.restore(session, checkpoint_path)

        for name in names:
            x, y = data_utils.name_to_batch(name, m.batch_size, m.num_steps)

            cost, loss, _ = session.run([m.cost, m.loss, tf.no_op()],
                                  {m.input_data: x,
                                   m.targets: y,
                                   m.initial_state: m.initial_state.eval(),
                                   m.weights: np.concatenate((
                                       np.ones(len(name)), np.zeros(m.batch_size * m.num_steps - len(name))))})

            print("Name {} gives us a perplexity of {}".format(
                name, np.exp(cost)))


def namignator(checkpoint_path, config):
    """Generates names randomly according to a given model

    Args:
        checkpoint_path: the path to restore the trained model from, should not
            include the model name, just the path to
        config: one of the above configs that specify the model and how it
            should be run and trained
    Returns:
        None
    """
    # mutate the config to become a name generator config
    config.num_steps = 1
    config.batch_size = 1

    with tf.Graph().as_default(), tf.Session() as session:

        with tf.variable_scope("model"):
            m = NamignizerModel(is_training=False, config=config)

        m.saver.restore(session, checkpoint_path)

        activations, final_state, _ = session.run([m.activations, m.final_state, tf.no_op()],
                                                  {m.input_data: np.zeros((1, 1)),
                                                   m.targets: np.zeros((1, 1)),
                                                   m.initial_state: m.initial_state.eval(),
                                                   m.weights: np.ones(1)})

        # sample from our softmax activations
        next_letter = np.random.choice(27, p=activations[0])
        name = [next_letter]
        while next_letter != 0:
            activations, final_state, _ = session.run([m.activations, m.final_state, tf.no_op()],
                                                      {m.input_data: [[next_letter]],
                                                       m.targets: np.zeros((1, 1)),
                                                       m.initial_state: final_state,
                                                       m.weights: np.ones(1)})

            next_letter = np.random.choice(27, p=activations[0])
            name += [next_letter]

        print(map(lambda x: chr(x + 96), name))


if __name__ == "__main__":
    # train("data/SmallNames.txt", "model/namignizer", SmallConfig)

    # namignize(["mary", "ida", "gazorbazorb", "mmmhmm", "bob"],
    #     tf.train.latest_checkpoint("model"), SmallConfig)

    # namignator(tf.train.latest_checkpoint("model"), SmallConfig)

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""RNN model with embeddings"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf


class NamignizerModel(object):
    """The Namignizer model ~ strongly based on PTB"""

    def __init__(self, is_training, config):
        self.batch_size = batch_size = config.batch_size
        self.num_steps = num_steps = config.num_steps
        size = config.hidden_size
        # will always be 27
        vocab_size = config.vocab_size

        # placeholders for inputs
        self._input_data = tf.placeholder(tf.int32, [batch_size, num_steps])
        self._targets = tf.placeholder(tf.int32, [batch_size, num_steps])
        # weights for the loss function
        self._weights = tf.placeholder(tf.float32, [batch_size * num_steps])

        # lstm for our RNN cell (GRU supported too)
        lstm_cell = tf.nn.rnn_cell.BasicLSTMCell(size, forget_bias=0.0)
        if is_training and config.keep_prob < 1:
            lstm_cell = tf.nn.rnn_cell.DropoutWrapper(
                lstm_cell, output_keep_prob=config.keep_prob)
        cell = tf.nn.rnn_cell.MultiRNNCell([lstm_cell] * config.num_layers)

        self._initial_state = cell.zero_state(batch_size, tf.float32)

        with tf.device("/cpu:0"):
            embedding = tf.get_variable("embedding", [vocab_size, size])
            inputs = tf.nn.embedding_lookup(embedding, self._input_data)

        if is_training and config.keep_prob < 1:
            inputs = tf.nn.dropout(inputs, config.keep_prob)

        outputs = []
        state = self._initial_state
        with tf.variable_scope("RNN"):
            for time_step in range(num_steps):
                if time_step > 0:
                    tf.get_variable_scope().reuse_variables()
                (cell_output, state) = cell(inputs[:, time_step, :], state)
                outputs.append(cell_output)

        output = tf.reshape(tf.concat(1, outputs), [-1, size])
        softmax_w = tf.get_variable("softmax_w", [size, vocab_size])
        softmax_b = tf.get_variable("softmax_b", [vocab_size])
        logits = tf.matmul(output, softmax_w) + softmax_b
        loss = tf.nn.seq2seq.sequence_loss_by_example(
            [logits],
            [tf.reshape(self._targets, [-1])],
            [self._weights])
        self._loss = loss
        self._cost = cost = tf.reduce_sum(loss) / batch_size
        self._final_state = state

        # probabilities of each letter
        self._activations = tf.nn.softmax(logits)

        # ability to save the model
        self.saver = tf.train.Saver(tf.all_variables())

        if not is_training:
            return

        self._lr = tf.Variable(0.0, trainable=False)
        tvars = tf.trainable_variables()
        grads, _ = tf.clip_by_global_norm(tf.gradients(cost, tvars),
                                          config.max_grad_norm)
        optimizer = tf.train.GradientDescentOptimizer(self.lr)
        self._train_op = optimizer.apply_gradients(zip(grads, tvars))

    def assign_lr(self, session, lr_value):
        session.run(tf.assign(self.lr, lr_value))

    @property
    def input_data(self):
        return self._input_data

    @property
    def targets(self):
        return self._targets

    @property
    def activations(self):
        return self._activations

    @property
    def weights(self):
        return self._weights

    @property
    def initial_state(self):
        return self._initial_state

    @property
    def cost(self):
        return self._cost

    @property
    def loss(self):
        return self._loss

    @property
    def final_state(self):
        return self._final_state

    @property
    def lr(self):
        return self._lr

    @property
    def train_op(self):
        return self._train_op

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for parsing Kaggle baby names files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import os

import numpy as np
import tensorflow as tf
import pandas as pd

# the default end of name rep will be zero
_EON = 0


def read_names(names_path):
    """read data from downloaded file. See SmallNames.txt for example format
    or go to https://www.kaggle.com/kaggle/us-baby-names for full lists

    Args:
        names_path: path to the csv file similar to the example type
    Returns:
        Dataset: a namedtuple of two elements: deduped names and their associated
            counts. The names contain only 26 chars and are all lower case
    """
    names_data = pd.read_csv(names_path)
    names_data.Name = names_data.Name.str.lower()

    name_data = names_data.groupby(by=["Name"])["Count"].sum()
    name_counts = np.array(name_data.tolist())
    names_deduped = np.array(name_data.index.tolist())

    Dataset = collections.namedtuple('Dataset', ['Name', 'Count'])
    return Dataset(names_deduped, name_counts)


def _letter_to_number(letter):
    """converts letters to numbers between 1 and 27"""
    # ord of lower case 'a' is 97
    return ord(letter) - 96


def namignizer_iterator(names, counts, batch_size, num_steps, epoch_size):
    """Takes a list of names and counts like those output from read_names, and
    makes an iterator yielding a batch_size by num_steps array of random names
    separated by an end of name token. The names are choosen randomly according
    to their counts. The batch may end mid-name

    Args:
        names: a set of lowercase names composed of 26 characters
        counts: a list of the frequency of those names
        batch_size: int
        num_steps: int
        epoch_size: number of batches to yield
    Yields:
        (x, y): a batch_size by num_steps array of ints representing letters, where
            x will be the input and y will be the target
    """
    name_distribution = counts / counts.sum()

    for i in range(epoch_size):
        data = np.zeros(batch_size * num_steps + 1)
        samples = np.random.choice(names, size=batch_size * num_steps // 2,
                                   replace=True, p=name_distribution)

        data_index = 0
        for sample in samples:
            if data_index >= batch_size * num_steps:
                break
            for letter in map(_letter_to_number, sample) + [_EON]:
                if data_index >= batch_size * num_steps:
                    break
                data[data_index] = letter
                data_index += 1

        x = data[:batch_size * num_steps].reshape((batch_size, num_steps))
        y = data[1:batch_size * num_steps + 1].reshape((batch_size, num_steps))

        yield (x, y)


def name_to_batch(name, batch_size, num_steps):
    """ Takes a single name and fills a batch with it

    Args:
        name: lowercase composed of 26 characters
        batch_size: int
        num_steps: int
    Returns:
        x, y: a batch_size by num_steps array of ints representing letters, where
            x will be the input and y will be the target. The array is filled up
            to the length of the string, the rest is filled with zeros
    """
    data = np.zeros(batch_size * num_steps + 1)

    data_index = 0
    for letter in map(_letter_to_number, name) + [_EON]:
        data[data_index] = letter
        data_index += 1

    x = data[:batch_size * num_steps].reshape((batch_size, num_steps))
    y = data[1:batch_size * num_steps + 1].reshape((batch_size, num_steps))

    return x, y

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Tests for graph_builder."""


# disable=no-name-in-module,unused-import,g-bad-import-order,maybe-no-member
import os.path

import tensorflow as tf

from tensorflow.python.framework import test_util
from tensorflow.python.ops import variables
from tensorflow.python.platform import googletest

from syntaxnet import graph_builder
from syntaxnet import sparse_pb2
from syntaxnet.ops import gen_parser_ops

FLAGS = tf.app.flags.FLAGS
if not hasattr(FLAGS, 'test_srcdir'):
  FLAGS.test_srcdir = ''
if not hasattr(FLAGS, 'test_tmpdir'):
  FLAGS.test_tmpdir = tf.test.get_temp_dir()


class GraphBuilderTest(test_util.TensorFlowTestCase):

  def setUp(self):
    # Creates a task context with the correct testing paths.
    initial_task_context = os.path.join(
        FLAGS.test_srcdir,
        'syntaxnet/'
        'testdata/context.pbtxt')
    self._task_context = os.path.join(FLAGS.test_tmpdir, 'context.pbtxt')
    with open(initial_task_context, 'r') as fin:
      with open(self._task_context, 'w') as fout:
        fout.write(fin.read().replace('SRCDIR', FLAGS.test_srcdir)
                   .replace('OUTPATH', FLAGS.test_tmpdir))

    # Creates necessary term maps.
    with self.test_session() as sess:
      gen_parser_ops.lexicon_builder(task_context=self._task_context,
                                     corpus_name='training-corpus').run()
      self._num_features, self._num_feature_ids, _, self._num_actions = (
          sess.run(gen_parser_ops.feature_size(task_context=self._task_context,
                                               arg_prefix='brain_parser')))

  def MakeBuilder(self, use_averaging=True, **kw_args):
    # Set the seed and gate_gradients to ensure reproducibility.
    return graph_builder.GreedyParser(
        self._num_actions, self._num_features, self._num_feature_ids,
        embedding_sizes=[8, 8, 8], hidden_layer_sizes=[32, 32], seed=42,
        gate_gradients=True, use_averaging=use_averaging, **kw_args)

  def FindNode(self, name):
    for node in tf.get_default_graph().as_graph_def().node:
      if node.name == name:
        return node
    return None

  def NodeFound(self, name):
    return self.FindNode(name) is not None

  def testScope(self):
    # Set up the network topology
    graph = tf.Graph()
    with graph.as_default():
      parser = self.MakeBuilder()
      parser.AddTraining(self._task_context,
                         batch_size=10,
                         corpus_name='training-corpus')
      parser.AddEvaluation(self._task_context,
                           batch_size=2,
                           corpus_name='tuning-corpus')
      parser.AddSaver()

      # Check that the node ids we may rely on are there with the expected
      # names.
      self.assertEqual(parser.training['logits'].name, 'training/logits:0')
      self.assertTrue(self.NodeFound('training/logits'))
      self.assertTrue(self.NodeFound('training/feature_0'))
      self.assertTrue(self.NodeFound('training/feature_1'))
      self.assertTrue(self.NodeFound('training/feature_2'))
      self.assertFalse(self.NodeFound('training/feature_3'))

      self.assertEqual(parser.evaluation['logits'].name, 'evaluation/logits:0')
      self.assertTrue(self.NodeFound('evaluation/logits'))

      # The saver node is expected to be in the root scope.
      self.assertTrue(self.NodeFound('save/restore_all'))

      # Also check that the parameters have the scope we expect.
      self.assertTrue(self.NodeFound('embedding_matrix_0'))
      self.assertTrue(self.NodeFound('embedding_matrix_1'))
      self.assertTrue(self.NodeFound('embedding_matrix_2'))
      self.assertFalse(self.NodeFound('embedding_matrix_3'))

  def testNestedScope(self):
    # It's OK to put the whole graph in a scope of its own.
    graph = tf.Graph()
    with graph.as_default():
      with graph.name_scope('top'):
        parser = self.MakeBuilder()
        parser.AddTraining(self._task_context,
                           batch_size=10,
                           corpus_name='training-corpus')
        parser.AddSaver()

      self.assertTrue(self.NodeFound('top/training/logits'))
      self.assertTrue(self.NodeFound('top/training/feature_0'))

      # The saver node is expected to be in the root scope no matter what.
      self.assertFalse(self.NodeFound('top/save/restore_all'))
      self.assertTrue(self.NodeFound('save/restore_all'))

  def testUseCustomGraphs(self):
    batch_size = 10

    # Use separate custom graphs.
    custom_train_graph = tf.Graph()
    with custom_train_graph.as_default():
      train_parser = self.MakeBuilder()
      train_parser.AddTraining(self._task_context,
                               batch_size,
                               corpus_name='training-corpus')

    custom_eval_graph = tf.Graph()
    with custom_eval_graph.as_default():
      eval_parser = self.MakeBuilder()
      eval_parser.AddEvaluation(self._task_context,
                                batch_size,
                                corpus_name='tuning-corpus')

    # The following session runs should not fail.
    with self.test_session(graph=custom_train_graph) as sess:
      self.assertTrue(self.NodeFound('training/logits'))
      sess.run(train_parser.inits.values())
      sess.run(['training/logits:0'])

    with self.test_session(graph=custom_eval_graph) as sess:
      self.assertFalse(self.NodeFound('training/logits'))
      self.assertTrue(self.NodeFound('evaluation/logits'))
      sess.run(eval_parser.inits.values())
      sess.run(['evaluation/logits:0'])

  def testTrainingAndEvalAreIndependent(self):
    batch_size = 10
    graph = tf.Graph()
    with graph.as_default():
      parser = self.MakeBuilder(use_averaging=False)
      parser.AddTraining(self._task_context,
                         batch_size,
                         corpus_name='training-corpus')
      parser.AddEvaluation(self._task_context,
                           batch_size,
                           corpus_name='tuning-corpus')
    with self.test_session(graph=graph) as sess:
      sess.run(parser.inits.values())
      # Before any training updates are performed, both training and eval nets
      # should return the same computations.
      eval_logits, = sess.run([parser.evaluation['logits']])
      training_logits, = sess.run([parser.training['logits']])
      self.assertNear(abs((eval_logits - training_logits).sum()), 0, 1e-6)

      # After training, activations should differ.
      for _ in range(5):
        eval_logits = parser.evaluation['logits'].eval()
      for _ in range(5):
        training_logits, _ = sess.run([parser.training['logits'],
                                       parser.training['train_op']])
      self.assertGreater(abs((eval_logits - training_logits).sum()), 0, 1e-3)

  def testReproducibility(self):
    batch_size = 10

    def ComputeACost(graph):
      with graph.as_default():
        parser = self.MakeBuilder(use_averaging=False)
        parser.AddTraining(self._task_context,
                           batch_size,
                           corpus_name='training-corpus')
        parser.AddEvaluation(self._task_context,
                             batch_size,
                             corpus_name='tuning-corpus')
      with self.test_session(graph=graph) as sess:
        sess.run(parser.inits.values())
        for _ in range(5):
          cost, _ = sess.run([parser.training['cost'],
                              parser.training['train_op']])
      return cost

    cost1 = ComputeACost(tf.Graph())
    cost2 = ComputeACost(tf.Graph())
    self.assertNear(cost1, cost2, 1e-8)

  def testAddTrainingAndEvalOrderIndependent(self):
    batch_size = 10

    graph1 = tf.Graph()
    with graph1.as_default():
      parser = self.MakeBuilder(use_averaging=False)
      parser.AddTraining(self._task_context,
                         batch_size,
                         corpus_name='training-corpus')
      parser.AddEvaluation(self._task_context,
                           batch_size,
                           corpus_name='tuning-corpus')
    with self.test_session(graph=graph1) as sess:
      sess.run(parser.inits.values())
      metrics1 = None
      for _ in range(500):
        cost1, _ = sess.run([parser.training['cost'],
                             parser.training['train_op']])
        em1 = parser.evaluation['eval_metrics'].eval()
        metrics1 = metrics1 + em1 if metrics1 is not None else em1

    # Reverse the order in which Training and Eval stacks are added.
    graph2 = tf.Graph()
    with graph2.as_default():
      parser = self.MakeBuilder(use_averaging=False)
      parser.AddEvaluation(self._task_context,
                           batch_size,
                           corpus_name='tuning-corpus')
      parser.AddTraining(self._task_context,
                         batch_size,
                         corpus_name='training-corpus')
    with self.test_session(graph=graph2) as sess:
      sess.run(parser.inits.values())
      metrics2 = None
      for _ in range(500):
        cost2, _ = sess.run([parser.training['cost'],
                             parser.training['train_op']])
        em2 = parser.evaluation['eval_metrics'].eval()
        metrics2 = metrics2 + em2 if metrics2 is not None else em2

    self.assertNear(cost1, cost2, 1e-8)
    self.assertEqual(abs(metrics1 - metrics2).sum(), 0)

  def testEvalMetrics(self):
    batch_size = 10
    graph = tf.Graph()
    with graph.as_default():
      parser = self.MakeBuilder()
      parser.AddEvaluation(self._task_context,
                           batch_size,
                           corpus_name='tuning-corpus')
    with self.test_session(graph=graph) as sess:
      sess.run(parser.inits.values())
      tokens = 0
      correct_heads = 0
      for _ in range(100):
        eval_metrics = sess.run(parser.evaluation['eval_metrics'])
        tokens += eval_metrics[0]
        correct_heads += eval_metrics[1]
      self.assertGreater(tokens, 0)
      self.assertGreaterEqual(tokens, correct_heads)
      self.assertGreaterEqual(correct_heads, 0)

  def MakeSparseFeatures(self, ids, weights):
    f = sparse_pb2.SparseFeatures()
    for i, w in zip(ids, weights):
      f.id.append(i)
      f.weight.append(w)
    return f.SerializeToString()

  def testEmbeddingOp(self):
    graph = tf.Graph()
    with self.test_session(graph=graph):
      params = tf.constant([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]],
                           tf.float32)

      var = variables.Variable([self.MakeSparseFeatures([1, 2], [1.0, 1.0]),
                                self.MakeSparseFeatures([], [])])
      var.initializer.run()
      embeddings = graph_builder.EmbeddingLookupFeatures(params, var,
                                                         True).eval()
      self.assertAllClose([[8.0, 10.0], [0.0, 0.0]], embeddings)

      var = variables.Variable([self.MakeSparseFeatures([], []),
                                self.MakeSparseFeatures([0, 2],
                                                        [0.5, 2.0])])
      var.initializer.run()
      embeddings = graph_builder.EmbeddingLookupFeatures(params, var,
                                                         True).eval()
      self.assertAllClose([[0.0, 0.0], [10.5, 13.0]], embeddings)

  def testOnlyTrainSomeParameters(self):
    batch_size = 10
    graph = tf.Graph()
    with graph.as_default():
      parser = self.MakeBuilder(use_averaging=False, only_train='softmax_bias')
      parser.AddTraining(self._task_context,
                         batch_size,
                         corpus_name='training-corpus')
    with self.test_session(graph=graph) as sess:
      sess.run(parser.inits.values())
      # Before training, save the state of two of the parameters.
      bias0, weight0 = sess.run([parser.params['softmax_bias'],
                                 parser.params['softmax_weight']])

      for _ in range(5):
        bias, weight, _ = sess.run([parser.params['softmax_bias'],
                                    parser.params['softmax_weight'],
                                    parser.training['train_op']])

      # After training, only one of the parameters should have changed.
      self.assertAllEqual(weight, weight0)
      self.assertGreater(abs(bias - bias0).sum(), 0, 1e-5)


if __name__ == '__main__':
  googletest.main()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Build structured parser models."""

import tensorflow as tf

from tensorflow.python.ops import control_flow_ops as cf
from tensorflow.python.ops import state_ops
from tensorflow.python.ops import tensor_array_ops

from syntaxnet import graph_builder
from syntaxnet.ops import gen_parser_ops

tf.NoGradient('BeamParseReader')
tf.NoGradient('BeamParser')
tf.NoGradient('BeamParserOutput')


def AddCrossEntropy(batch_size, n):
  """Adds a cross entropy cost function."""
  cross_entropies = []
  def _Pass():
    return tf.constant(0, dtype=tf.float32, shape=[1])

  for beam_id in range(batch_size):
    beam_gold_slot = tf.reshape(tf.slice(n['gold_slot'], [beam_id], [1]), [1])
    def _ComputeCrossEntropy():
      """Adds ops to compute cross entropy of the gold path in a beam."""
      # Requires a cast so that UnsortedSegmentSum, in the gradient,
      # is happy with the type of its input 'segment_ids', which
      # must be int32.
      idx = tf.cast(
          tf.reshape(
              tf.where(tf.equal(n['beam_ids'], beam_id)), [-1]), tf.int32)
      beam_scores = tf.reshape(tf.gather(n['all_path_scores'], idx), [1, -1])
      num = tf.shape(idx)
      return tf.nn.softmax_cross_entropy_with_logits(
          beam_scores, tf.expand_dims(
              tf.sparse_to_dense(beam_gold_slot, num, [1.], 0.), 0))
    # The conditional here is needed to deal with the last few batches of the
    # corpus which can contain -1 in beam_gold_slot for empty batch slots.
    cross_entropies.append(cf.cond(
        beam_gold_slot[0] >= 0, _ComputeCrossEntropy, _Pass))
  return {'cross_entropy': tf.div(tf.add_n(cross_entropies), batch_size)}


class StructuredGraphBuilder(graph_builder.GreedyParser):
  """Extends the standard GreedyParser with a CRF objective using a beam.

  The constructor takes two additional keyword arguments.
  beam_size: the maximum size the beam can grow to.
  max_steps: the maximum number of steps in any particular beam.

  The model supports batch training with the batch_size argument to the
  AddTraining method.
  """

  def __init__(self, *args, **kwargs):
    self._beam_size = kwargs.pop('beam_size', 10)
    self._max_steps = kwargs.pop('max_steps', 25)
    super(StructuredGraphBuilder, self).__init__(*args, **kwargs)

  def _AddBeamReader(self,
                     task_context,
                     batch_size,
                     corpus_name,
                     until_all_final=False,
                     always_start_new_sentences=False):
    """Adds an op capable of reading sentences and parsing them with a beam."""
    features, state, epochs = gen_parser_ops.beam_parse_reader(
        task_context=task_context,
        feature_size=self._feature_size,
        beam_size=self._beam_size,
        batch_size=batch_size,
        corpus_name=corpus_name,
        allow_feature_weights=self._allow_feature_weights,
        arg_prefix=self._arg_prefix,
        continue_until_all_final=until_all_final,
        always_start_new_sentences=always_start_new_sentences)
    return {'state': state, 'features': features, 'epochs': epochs}

  def _BuildSequence(self,
                     batch_size,
                     max_steps,
                     features,
                     state,
                     use_average=False):
    """Adds a sequence of beam parsing steps."""
    def Advance(state, step, scores_array, alive, alive_steps, *features):
      scores = self._BuildNetwork(features,
                                  return_average=use_average)['logits']
      scores_array = scores_array.write(step, scores)
      features, state, alive = (
          gen_parser_ops.beam_parser(state, scores, self._feature_size))
      return [state, step + 1, scores_array, alive, alive_steps + tf.cast(
          alive, tf.int32)] + list(features)

    # args: (state, step, scores_array, alive, alive_steps, *features)
    def KeepGoing(*args):
      return tf.logical_and(args[1] < max_steps, tf.reduce_any(args[3]))

    step = tf.constant(0, tf.int32, [])
    scores_array = tensor_array_ops.TensorArray(dtype=tf.float32,
                                                size=0,
                                                dynamic_size=True)
    alive = tf.constant(True, tf.bool, [batch_size])
    alive_steps = tf.constant(0, tf.int32, [batch_size])
    t = tf.while_loop(
        KeepGoing,
        Advance,
        [state, step, scores_array, alive, alive_steps] + list(features),
        parallel_iterations=100)

    # Link to the final nodes/values of ops that have passed through While:
    return {'state': t[0],
            'concat_scores': t[2].concat(),
            'alive': t[3],
            'alive_steps': t[4]}

  def AddTraining(self,
                  task_context,
                  batch_size,
                  learning_rate=0.1,
                  decay_steps=4000,
                  momentum=None,
                  corpus_name='documents'):
    with tf.name_scope('training'):
      n = self.training
      n['accumulated_alive_steps'] = self._AddVariable(
          [batch_size], tf.int32, 'accumulated_alive_steps',
          tf.zeros_initializer)
      n.update(self._AddBeamReader(task_context, batch_size, corpus_name))
      # This adds a required 'step' node too:
      learning_rate = tf.constant(learning_rate, dtype=tf.float32)
      n['learning_rate'] = self._AddLearningRate(learning_rate, decay_steps)
      # Call BuildNetwork *only* to set up the params outside of the main loop.
      self._BuildNetwork(list(n['features']))

      n.update(self._BuildSequence(batch_size, self._max_steps, n['features'],
                                   n['state']))

      flat_concat_scores = tf.reshape(n['concat_scores'], [-1])
      (indices_and_paths, beams_and_slots, n['gold_slot'], n[
          'beam_path_scores']) = gen_parser_ops.beam_parser_output(n[
              'state'])
      n['indices'] = tf.reshape(tf.gather(indices_and_paths, [0]), [-1])
      n['path_ids'] = tf.reshape(tf.gather(indices_and_paths, [1]), [-1])
      n['all_path_scores'] = tf.sparse_segment_sum(
          flat_concat_scores, n['indices'], n['path_ids'])
      n['beam_ids'] = tf.reshape(tf.gather(beams_and_slots, [0]), [-1])
      n.update(AddCrossEntropy(batch_size, n))

      if self._only_train:
        trainable_params = {k: v for k, v in self.params.iteritems()
                            if k in self._only_train}
      else:
        trainable_params = self.params
      for p in trainable_params:
        tf.logging.info('trainable_param: %s', p)

      regularized_params = [
          tf.nn.l2_loss(p) for k, p in trainable_params.iteritems()
          if k.startswith('weights') or k.startswith('bias')]
      l2_loss = 1e-4 * tf.add_n(regularized_params) if regularized_params else 0

      n['cost'] = tf.add(n['cross_entropy'], l2_loss, name='cost')

      n['gradients'] = tf.gradients(n['cost'], trainable_params.values())

      with tf.control_dependencies([n['alive_steps']]):
        update_accumulators = tf.group(
            tf.assign_add(n['accumulated_alive_steps'], n['alive_steps']))

      def ResetAccumulators():
        return tf.assign(
            n['accumulated_alive_steps'], tf.zeros([batch_size], tf.int32))
      n['reset_accumulators_func'] = ResetAccumulators

      optimizer = tf.train.MomentumOptimizer(n['learning_rate'],
                                             momentum,
                                             use_locking=self._use_locking)
      train_op = optimizer.minimize(n['cost'],
                                    var_list=trainable_params.values())
      for param in trainable_params.values():
        slot = optimizer.get_slot(param, 'momentum')
        self.inits[slot.name] = state_ops.init_variable(slot,
                                                        tf.zeros_initializer)
        self.variables[slot.name] = slot

      def NumericalChecks():
        return tf.group(*[
            tf.check_numerics(param, message='Parameter is not finite.')
            for param in trainable_params.values()
            if param.dtype.base_dtype in [tf.float32, tf.float64]])
      check_op = cf.cond(tf.equal(tf.mod(self.GetStep(), self._check_every), 0),
                         NumericalChecks, tf.no_op)
      avg_update_op = tf.group(*self._averaging.values())
      train_ops = [train_op]
      if self._check_parameters:
        train_ops.append(check_op)
      if self._use_averaging:
        train_ops.append(avg_update_op)
      with tf.control_dependencies([update_accumulators]):
        n['train_op'] = tf.group(*train_ops, name='train_op')
      n['alive_steps'] = tf.identity(n['alive_steps'], name='alive_steps')
    return n

  def AddEvaluation(self,
                    task_context,
                    batch_size,
                    evaluation_max_steps=300,
                    corpus_name=None):
    with tf.name_scope('evaluation'):
      n = self.evaluation
      n.update(self._AddBeamReader(task_context,
                                   batch_size,
                                   corpus_name,
                                   until_all_final=True,
                                   always_start_new_sentences=True))
      self._BuildNetwork(
          list(n['features']),
          return_average=self._use_averaging)
      n.update(self._BuildSequence(batch_size, evaluation_max_steps, n[
          'features'], n['state'], use_average=self._use_averaging))
      n['eval_metrics'], n['documents'] = (
          gen_parser_ops.beam_eval_output(n['state']))
    return n

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Loads parser_ops shared library."""

import os.path
import tensorflow as tf

tf.load_op_library(
    os.path.join(tf.resource_loader.get_data_files_path(),
                 'parser_ops.so'))

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Tests for beam_reader_ops."""


import os.path
import time

import tensorflow as tf

from tensorflow.python.framework import test_util
from tensorflow.python.platform import googletest
from tensorflow.python.platform import tf_logging as logging

from syntaxnet import structured_graph_builder
from syntaxnet.ops import gen_parser_ops

FLAGS = tf.app.flags.FLAGS
if not hasattr(FLAGS, 'test_srcdir'):
  FLAGS.test_srcdir = ''
if not hasattr(FLAGS, 'test_tmpdir'):
  FLAGS.test_tmpdir = tf.test.get_temp_dir()


class ParsingReaderOpsTest(test_util.TensorFlowTestCase):

  def setUp(self):
    # Creates a task context with the correct testing paths.
    initial_task_context = os.path.join(
        FLAGS.test_srcdir,
        'syntaxnet/'
        'testdata/context.pbtxt')
    self._task_context = os.path.join(FLAGS.test_tmpdir, 'context.pbtxt')
    with open(initial_task_context, 'r') as fin:
      with open(self._task_context, 'w') as fout:
        fout.write(fin.read().replace('SRCDIR', FLAGS.test_srcdir)
                   .replace('OUTPATH', FLAGS.test_tmpdir))

    # Creates necessary term maps.
    with self.test_session() as sess:
      gen_parser_ops.lexicon_builder(task_context=self._task_context,
                                     corpus_name='training-corpus').run()
      self._num_features, self._num_feature_ids, _, self._num_actions = (
          sess.run(gen_parser_ops.feature_size(task_context=self._task_context,
                                               arg_prefix='brain_parser')))

  def MakeGraph(self,
                max_steps=10,
                beam_size=2,
                batch_size=1,
                **kwargs):
    """Constructs a structured learning graph."""
    assert max_steps > 0, 'Empty network not supported.'

    logging.info('MakeGraph + %s', kwargs)

    with self.test_session(graph=tf.Graph()) as sess:
      feature_sizes, domain_sizes, embedding_dims, num_actions = sess.run(
          gen_parser_ops.feature_size(task_context=self._task_context))
    embedding_dims = [8, 8, 8]
    hidden_layer_sizes = []
    learning_rate = 0.01
    builder = structured_graph_builder.StructuredGraphBuilder(
        num_actions,
        feature_sizes,
        domain_sizes,
        embedding_dims,
        hidden_layer_sizes,
        seed=1,
        max_steps=max_steps,
        beam_size=beam_size,
        gate_gradients=True,
        use_locking=True,
        use_averaging=False,
        check_parameters=False,
        **kwargs)
    builder.AddTraining(self._task_context,
                        batch_size,
                        learning_rate=learning_rate,
                        decay_steps=1000,
                        momentum=0.9,
                        corpus_name='training-corpus')
    builder.AddEvaluation(self._task_context,
                          batch_size,
                          evaluation_max_steps=25,
                          corpus_name=None)
    builder.training['inits'] = tf.group(*builder.inits.values(), name='inits')
    return builder

  def Train(self, **kwargs):
    with self.test_session(graph=tf.Graph()) as sess:
      max_steps = 3
      batch_size = 3
      beam_size = 3
      builder = (
          self.MakeGraph(
              max_steps=max_steps, beam_size=beam_size,
              batch_size=batch_size, **kwargs))
      logging.info('params: %s', builder.params.keys())
      logging.info('variables: %s', builder.variables.keys())

      t = builder.training
      sess.run(t['inits'])
      costs = []
      gold_slots = []
      alive_steps_vector = []
      every_n = 5
      walltime = time.time()
      for step in range(10):
        if step > 0 and step % every_n == 0:
          new_walltime = time.time()
          logging.info(
              'Step: %d <cost>: %f <gold_slot>: %f <alive_steps>: %f <iter '
              'time>: %f ms',
              step, sum(costs[-every_n:]) / float(every_n),
              sum(gold_slots[-every_n:]) / float(every_n),
              sum(alive_steps_vector[-every_n:]) / float(every_n),
              1000 * (new_walltime - walltime) / float(every_n))
          walltime = new_walltime

        cost, gold_slot, alive_steps, _ = sess.run(
            [t['cost'], t['gold_slot'], t['alive_steps'], t['train_op']])
        costs.append(cost)
        gold_slots.append(gold_slot.mean())
        alive_steps_vector.append(alive_steps.mean())

      if builder._only_train:
        trainable_param_names = [
            k for k in builder.params if k in builder._only_train]
      else:
        trainable_param_names = builder.params.keys()
      if builder._use_averaging:
        for v in trainable_param_names:
          avg = builder.variables['%s_avg_var' % v].eval()
          tf.assign(builder.params[v], avg).eval()

      # Reset for pseudo eval.
      costs = []
      gold_slots = []
      alive_stepss = []
      for step in range(10):
        cost, gold_slot, alive_steps = sess.run(
            [t['cost'], t['gold_slot'], t['alive_steps']])
        costs.append(cost)
        gold_slots.append(gold_slot.mean())
        alive_stepss.append(alive_steps.mean())

      logging.info(
          'Pseudo eval: <cost>: %f <gold_slot>: %f <alive_steps>: %f',
          sum(costs[-every_n:]) / float(every_n),
          sum(gold_slots[-every_n:]) / float(every_n),
          sum(alive_stepss[-every_n:]) / float(every_n))

  def PathScores(self, iterations, beam_size, max_steps, batch_size):
    with self.test_session(graph=tf.Graph()) as sess:
      t = self.MakeGraph(beam_size=beam_size, max_steps=max_steps,
                         batch_size=batch_size).training
      sess.run(t['inits'])
      all_path_scores = []
      beam_path_scores = []
      for i in range(iterations):
        logging.info('run %d', i)
        tensors = (
            sess.run(
                [t['alive_steps'], t['concat_scores'],
                 t['all_path_scores'], t['beam_path_scores'],
                 t['indices'], t['path_ids']]))

        logging.info('alive for %s, all_path_scores and beam_path_scores, '
                     'indices and path_ids:'
                     '\n%s\n%s\n%s\n%s',
                     tensors[0], tensors[2], tensors[3], tensors[4], tensors[5])
        logging.info('diff:\n%s', tensors[2] - tensors[3])

        all_path_scores.append(tensors[2])
        beam_path_scores.append(tensors[3])
      return all_path_scores, beam_path_scores

  def testParseUntilNotAlive(self):
    """Ensures that the 'alive' condition works in the Cond ops."""
    with self.test_session(graph=tf.Graph()) as sess:
      t = self.MakeGraph(batch_size=3, beam_size=2, max_steps=5).training
      sess.run(t['inits'])
      for i in range(5):
        logging.info('run %d', i)
        tf_alive = t['alive'].eval()
        self.assertFalse(any(tf_alive))

  def testParseMomentum(self):
    """Ensures that Momentum training can be done using the gradients."""
    self.Train()
    self.Train(model_cost='perceptron_loss')
    self.Train(model_cost='perceptron_loss',
               only_train='softmax_weight,softmax_bias', softmax_init=0)
    self.Train(only_train='softmax_weight,softmax_bias', softmax_init=0)

  def testPathScoresAgree(self):
    """Ensures that path scores computed in the beam are same in the net."""
    all_path_scores, beam_path_scores = self.PathScores(
        iterations=1, beam_size=130, max_steps=5, batch_size=1)
    self.assertArrayNear(all_path_scores[0], beam_path_scores[0], 1e-6)

  def testBatchPathScoresAgree(self):
    """Ensures that path scores computed in the beam are same in the net."""
    all_path_scores, beam_path_scores = self.PathScores(
        iterations=1, beam_size=130, max_steps=5, batch_size=22)
    self.assertArrayNear(all_path_scores[0], beam_path_scores[0], 1e-6)

  def testBatchOneStepPathScoresAgree(self):
    """Ensures that path scores computed in the beam are same in the net."""
    all_path_scores, beam_path_scores = self.PathScores(
        iterations=1, beam_size=130, max_steps=1, batch_size=22)
    self.assertArrayNear(all_path_scores[0], beam_path_scores[0], 1e-6)


if __name__ == '__main__':
  googletest.main()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""A program to train a tensorflow neural net parser from a a conll file."""



import os
import os.path
import time

import tensorflow as tf

from tensorflow.python.platform import gfile
from tensorflow.python.platform import tf_logging as logging

from google.protobuf import text_format

from syntaxnet import graph_builder
from syntaxnet import structured_graph_builder
from syntaxnet.ops import gen_parser_ops
from syntaxnet import task_spec_pb2

flags = tf.app.flags
FLAGS = flags.FLAGS

flags.DEFINE_string('tf_master', '',
                    'TensorFlow execution engine to connect to.')
flags.DEFINE_string('output_path', '', 'Top level for output.')
flags.DEFINE_string('task_context', '',
                    'Path to a task context with resource locations and '
                    'parameters.')
flags.DEFINE_string('arg_prefix', None, 'Prefix for context parameters.')
flags.DEFINE_string('params', '0', 'Unique identifier of parameter grid point.')
flags.DEFINE_string('training_corpus', 'training-corpus',
                    'Name of the context input to read training data from.')
flags.DEFINE_string('tuning_corpus', 'tuning-corpus',
                    'Name of the context input to read tuning data from.')
flags.DEFINE_string('word_embeddings', None,
                    'Recordio containing pretrained word embeddings, will be '
                    'loaded as the first embedding matrix.')
flags.DEFINE_bool('compute_lexicon', False, '')
flags.DEFINE_bool('projectivize_training_set', False, '')
flags.DEFINE_string('hidden_layer_sizes', '200,200',
                    'Comma separated list of hidden layer sizes.')
flags.DEFINE_string('graph_builder', 'greedy',
                    'Graph builder to use, either "greedy" or "structured".')
flags.DEFINE_integer('batch_size', 32,
                     'Number of sentences to process in parallel.')
flags.DEFINE_integer('beam_size', 10, 'Number of slots for beam parsing.')
flags.DEFINE_integer('num_epochs', 10, 'Number of epochs to train for.')
flags.DEFINE_integer('max_steps', 50,
                     'Max number of parser steps during a training step.')
flags.DEFINE_integer('report_every', 100,
                     'Report cost and training accuracy every this many steps.')
flags.DEFINE_integer('checkpoint_every', 5000,
                     'Measure tuning UAS and checkpoint every this many steps.')
flags.DEFINE_bool('slim_model', False,
                  'Whether to remove non-averaged variables, for compactness.')
flags.DEFINE_float('learning_rate', 0.1, 'Initial learning rate parameter.')
flags.DEFINE_integer('decay_steps', 4000,
                     'Decay learning rate by 0.96 every this many steps.')
flags.DEFINE_float('momentum', 0.9,
                   'Momentum parameter for momentum optimizer.')
flags.DEFINE_string('seed', '0', 'Initialization seed for TF variables.')
flags.DEFINE_string('pretrained_params', None,
                    'Path to model from which to load params.')
flags.DEFINE_string('pretrained_params_names', None,
                    'List of names of tensors to load from pretrained model.')
flags.DEFINE_float('averaging_decay', 0.9999,
                   'Decay for exponential moving average when computing'
                   'averaged parameters, set to 1 to do vanilla averaging.')


def StageName():
  return os.path.join(FLAGS.arg_prefix, FLAGS.graph_builder)


def OutputPath(path):
  return os.path.join(FLAGS.output_path, StageName(), FLAGS.params, path)


def RewriteContext():
  context = task_spec_pb2.TaskSpec()
  with gfile.FastGFile(FLAGS.task_context) as fin:
    text_format.Merge(fin.read(), context)
  for resource in context.input:
    if resource.creator == StageName():
      del resource.part[:]
      part = resource.part.add()
      part.file_pattern = os.path.join(OutputPath(resource.name))
  with gfile.FastGFile(OutputPath('context'), 'w') as fout:
    fout.write(str(context))


def WriteStatus(num_steps, eval_metric, best_eval_metric):
  status = os.path.join(os.getenv('GOOGLE_STATUS_DIR') or '/tmp', 'STATUS')
  message = ('Parameters: %s | Steps: %d | Tuning score: %.2f%% | '
             'Best tuning score: %.2f%%' % (FLAGS.params, num_steps,
                                            eval_metric, best_eval_metric))
  with gfile.FastGFile(status, 'w') as fout:
    fout.write(message)
  with gfile.FastGFile(OutputPath('status'), 'a') as fout:
    fout.write(message + '\n')


def Eval(sess, parser, num_steps, best_eval_metric):
  """Evaluates a network and checkpoints it to disk.

  Args:
    sess: tensorflow session to use
    parser: graph builder containing all ops references
    num_steps: number of training steps taken, for logging
    best_eval_metric: current best eval metric, to decide whether this model is
        the best so far

  Returns:
    new best eval metric
  """
  logging.info('Evaluating training network.')
  t = time.time()
  num_epochs = None
  num_tokens = 0
  num_correct = 0
  while True:
    tf_eval_epochs, tf_eval_metrics = sess.run([
        parser.evaluation['epochs'], parser.evaluation['eval_metrics']
    ])
    num_tokens += tf_eval_metrics[0]
    num_correct += tf_eval_metrics[1]
    if num_epochs is None:
      num_epochs = tf_eval_epochs
    elif num_epochs < tf_eval_epochs:
      break
  eval_metric = 0 if num_tokens == 0 else (100.0 * num_correct / num_tokens)
  logging.info('Seconds elapsed in evaluation: %.2f, '
               'eval metric: %.2f%%', time.time() - t, eval_metric)
  WriteStatus(num_steps, eval_metric, max(eval_metric, best_eval_metric))

  # Save parameters.
  if FLAGS.output_path:
    logging.info('Writing out trained parameters.')
    parser.saver.save(sess, OutputPath('latest-model'))
    if eval_metric > best_eval_metric:
      parser.saver.save(sess, OutputPath('model'))

  return max(eval_metric, best_eval_metric)


def Train(sess, num_actions, feature_sizes, domain_sizes, embedding_dims):
  """Builds and trains the network.

  Args:
    sess: tensorflow session to use.
    num_actions: number of possible golden actions.
    feature_sizes: size of each feature vector.
    domain_sizes: number of possible feature ids in each feature vector.
    embedding_dims: embedding dimension to use for each feature group.
  """
  t = time.time()
  hidden_layer_sizes = map(int, FLAGS.hidden_layer_sizes.split(','))
  logging.info('Building training network with parameters: feature_sizes: %s '
               'domain_sizes: %s', feature_sizes, domain_sizes)

  if FLAGS.graph_builder == 'greedy':
    parser = graph_builder.GreedyParser(num_actions,
                                        feature_sizes,
                                        domain_sizes,
                                        embedding_dims,
                                        hidden_layer_sizes,
                                        seed=int(FLAGS.seed),
                                        gate_gradients=True,
                                        averaging_decay=FLAGS.averaging_decay,
                                        arg_prefix=FLAGS.arg_prefix)
  else:
    parser = structured_graph_builder.StructuredGraphBuilder(
        num_actions,
        feature_sizes,
        domain_sizes,
        embedding_dims,
        hidden_layer_sizes,
        seed=int(FLAGS.seed),
        gate_gradients=True,
        averaging_decay=FLAGS.averaging_decay,
        arg_prefix=FLAGS.arg_prefix,
        beam_size=FLAGS.beam_size,
        max_steps=FLAGS.max_steps)

  task_context = OutputPath('context')
  if FLAGS.word_embeddings is not None:
    parser.AddPretrainedEmbeddings(0, FLAGS.word_embeddings, task_context)

  corpus_name = ('projectivized-training-corpus' if
                 FLAGS.projectivize_training_set else FLAGS.training_corpus)
  parser.AddTraining(task_context,
                     FLAGS.batch_size,
                     learning_rate=FLAGS.learning_rate,
                     momentum=FLAGS.momentum,
                     decay_steps=FLAGS.decay_steps,
                     corpus_name=corpus_name)
  parser.AddEvaluation(task_context,
                       FLAGS.batch_size,
                       corpus_name=FLAGS.tuning_corpus)
  parser.AddSaver(FLAGS.slim_model)

  # Save graph.
  if FLAGS.output_path:
    with gfile.FastGFile(OutputPath('graph'), 'w') as f:
      f.write(sess.graph_def.SerializeToString())

  logging.info('Initializing...')
  num_epochs = 0
  cost_sum = 0.0
  num_steps = 0
  best_eval_metric = 0.0
  sess.run(parser.inits.values())

  if FLAGS.pretrained_params is not None:
    logging.info('Loading pretrained params from %s', FLAGS.pretrained_params)
    feed_dict = {'save/Const:0': FLAGS.pretrained_params}
    targets = []
    for node in sess.graph_def.node:
      if (node.name.startswith('save/Assign') and
          node.input[0] in FLAGS.pretrained_params_names.split(',')):
        logging.info('Loading %s with op %s', node.input[0], node.name)
        targets.append(node.name)
    sess.run(targets, feed_dict=feed_dict)

  logging.info('Training...')
  while num_epochs < FLAGS.num_epochs:
    tf_epochs, tf_cost, _ = sess.run([parser.training[
        'epochs'], parser.training['cost'], parser.training['train_op']])
    num_epochs = tf_epochs
    num_steps += 1
    cost_sum += tf_cost
    if num_steps % FLAGS.report_every == 0:
      logging.info('Epochs: %d, num steps: %d, '
                   'seconds elapsed: %.2f, avg cost: %.2f, ', num_epochs,
                   num_steps, time.time() - t, cost_sum / FLAGS.report_every)
      cost_sum = 0.0
    if num_steps % FLAGS.checkpoint_every == 0:
      best_eval_metric = Eval(sess, parser, num_steps, best_eval_metric)


def main(unused_argv):
  logging.set_verbosity(logging.INFO)
  if not gfile.IsDirectory(OutputPath('')):
    gfile.MakeDirs(OutputPath(''))

  # Rewrite context.
  RewriteContext()

  # Creates necessary term maps.
  if FLAGS.compute_lexicon:
    logging.info('Computing lexicon...')
    with tf.Session(FLAGS.tf_master) as sess:
      gen_parser_ops.lexicon_builder(task_context=OutputPath('context'),
                                     corpus_name=FLAGS.training_corpus).run()
  with tf.Session(FLAGS.tf_master) as sess:
    feature_sizes, domain_sizes, embedding_dims, num_actions = sess.run(
        gen_parser_ops.feature_size(task_context=OutputPath('context'),
                                    arg_prefix=FLAGS.arg_prefix))

  # Well formed and projectivize.
  if FLAGS.projectivize_training_set:
    logging.info('Preprocessing...')
    with tf.Session(FLAGS.tf_master) as sess:
      source, last = gen_parser_ops.document_source(
          task_context=OutputPath('context'),
          batch_size=FLAGS.batch_size,
          corpus_name=FLAGS.training_corpus)
      sink = gen_parser_ops.document_sink(
          task_context=OutputPath('context'),
          corpus_name='projectivized-training-corpus',
          documents=gen_parser_ops.projectivize_filter(
              gen_parser_ops.well_formed_filter(source,
                                                task_context=OutputPath(
                                                    'context')),
              task_context=OutputPath('context')))
      while True:
        tf_last, _ = sess.run([last, sink])
        if tf_last:
          break

  logging.info('Training...')
  with tf.Session(FLAGS.tf_master) as sess:
    Train(sess, num_actions, feature_sizes, domain_sizes, embedding_dims)


if __name__ == '__main__':
  tf.app.run()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""A program to annotate a conll file with a tensorflow neural net parser."""


import os
import os.path
import time

import tensorflow as tf

from tensorflow.python.platform import gfile
from tensorflow.python.platform import tf_logging as logging
from syntaxnet import sentence_pb2
from syntaxnet import graph_builder
from syntaxnet import structured_graph_builder
from syntaxnet.ops import gen_parser_ops

flags = tf.app.flags
FLAGS = flags.FLAGS


flags.DEFINE_string('task_context', '',
                    'Path to a task context with inputs and parameters for '
                    'feature extractors.')
flags.DEFINE_string('model_path', '', 'Path to model parameters.')
flags.DEFINE_string('arg_prefix', None, 'Prefix for context parameters.')
flags.DEFINE_string('graph_builder', 'greedy',
                    'Which graph builder to use, either greedy or structured.')
flags.DEFINE_string('input', 'stdin',
                    'Name of the context input to read data from.')
flags.DEFINE_string('output', 'stdout',
                    'Name of the context input to write data to.')
flags.DEFINE_string('hidden_layer_sizes', '200,200',
                    'Comma separated list of hidden layer sizes.')
flags.DEFINE_integer('batch_size', 32,
                     'Number of sentences to process in parallel.')
flags.DEFINE_integer('beam_size', 8, 'Number of slots for beam parsing.')
flags.DEFINE_integer('max_steps', 1000, 'Max number of steps to take.')
flags.DEFINE_bool('slim_model', False,
                  'Whether to expect only averaged variables.')


def Eval(sess, num_actions, feature_sizes, domain_sizes, embedding_dims):
  """Builds and evaluates a network.

  Args:
    sess: tensorflow session to use
    num_actions: number of possible golden actions
    feature_sizes: size of each feature vector
    domain_sizes: number of possible feature ids in each feature vector
    embedding_dims: embedding dimension for each feature group
  """
  t = time.time()
  hidden_layer_sizes = map(int, FLAGS.hidden_layer_sizes.split(','))
  logging.info('Building training network with parameters: feature_sizes: %s '
               'domain_sizes: %s', feature_sizes, domain_sizes)
  if FLAGS.graph_builder == 'greedy':
    parser = graph_builder.GreedyParser(num_actions,
                                        feature_sizes,
                                        domain_sizes,
                                        embedding_dims,
                                        hidden_layer_sizes,
                                        gate_gradients=True,
                                        arg_prefix=FLAGS.arg_prefix)
  else:
    parser = structured_graph_builder.StructuredGraphBuilder(
        num_actions,
        feature_sizes,
        domain_sizes,
        embedding_dims,
        hidden_layer_sizes,
        gate_gradients=True,
        arg_prefix=FLAGS.arg_prefix,
        beam_size=FLAGS.beam_size,
        max_steps=FLAGS.max_steps)
  task_context = FLAGS.task_context
  parser.AddEvaluation(task_context,
                       FLAGS.batch_size,
                       corpus_name=FLAGS.input,
                       evaluation_max_steps=FLAGS.max_steps)

  parser.AddSaver(FLAGS.slim_model)
  sess.run(parser.inits.values())
  parser.saver.restore(sess, FLAGS.model_path)

  sink_documents = tf.placeholder(tf.string)
  sink = gen_parser_ops.document_sink(sink_documents,
                                      task_context=FLAGS.task_context,
                                      corpus_name=FLAGS.output)
  t = time.time()
  num_epochs = None
  num_tokens = 0
  num_correct = 0
  num_documents = 0
  while True:
    tf_eval_epochs, tf_eval_metrics, tf_documents = sess.run([
        parser.evaluation['epochs'],
        parser.evaluation['eval_metrics'],
        parser.evaluation['documents'],
    ])

    if len(tf_documents):
      logging.info('Processed %d documents', len(tf_documents))
      num_documents += len(tf_documents)
      sess.run(sink, feed_dict={sink_documents: tf_documents})

    num_tokens += tf_eval_metrics[0]
    num_correct += tf_eval_metrics[1]
    if num_epochs is None:
      num_epochs = tf_eval_epochs
    elif num_epochs < tf_eval_epochs:
      break

  logging.info('Total processed documents: %d', num_documents)
  if num_tokens > 0:
    eval_metric = 100.0 * num_correct / num_tokens
    logging.info('num correct tokens: %d', num_correct)
    logging.info('total tokens: %d', num_tokens)
    logging.info('Seconds elapsed in evaluation: %.2f, '
                 'eval metric: %.2f%%', time.time() - t, eval_metric)


def main(unused_argv):
  logging.set_verbosity(logging.INFO)
  with tf.Session() as sess:
    feature_sizes, domain_sizes, embedding_dims, num_actions = sess.run(
        gen_parser_ops.feature_size(task_context=FLAGS.task_context,
                                    arg_prefix=FLAGS.arg_prefix))

  with tf.Session() as sess:
    Eval(sess, num_actions, feature_sizes, domain_sizes, embedding_dims)


if __name__ == '__main__':
  tf.app.run()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Builds parser models."""

import tensorflow as tf

import syntaxnet.load_parser_ops

from tensorflow.python.ops import control_flow_ops as cf
from tensorflow.python.ops import state_ops
from tensorflow.python.platform import tf_logging as logging

from syntaxnet.ops import gen_parser_ops


def BatchedSparseToDense(sparse_indices, output_size):
  """Batch compatible sparse to dense conversion.

  This is useful for one-hot coded target labels.

  Args:
    sparse_indices: [batch_size] tensor containing one index per batch
    output_size: needed in order to generate the correct dense output

  Returns:
    A [batch_size, output_size] dense tensor.
  """
  eye = tf.diag(tf.fill([output_size], tf.constant(1, tf.float32)))
  return tf.nn.embedding_lookup(eye, sparse_indices)


def EmbeddingLookupFeatures(params, sparse_features, allow_weights):
  """Computes embeddings for each entry of sparse features sparse_features.

  Args:
    params: list of 2D tensors containing vector embeddings
    sparse_features: 1D tensor of strings. Each entry is a string encoding of
      dist_belief.SparseFeatures, and represents a variable length list of
      feature ids, and optionally, corresponding weights values.
    allow_weights: boolean to control whether the weights returned from the
      SparseFeatures are used to multiply the embeddings.

  Returns:
    A tensor representing the combined embeddings for the sparse features.
    For each entry s in sparse_features, the function looks up the embeddings
    for each id and sums them into a single tensor weighing them by the
    weight of each id. It returns a tensor with each entry of sparse_features
    replaced by this combined embedding.
  """
  if not isinstance(params, list):
    params = [params]
  # Lookup embeddings.
  sparse_features = tf.convert_to_tensor(sparse_features)
  indices, ids, weights = gen_parser_ops.unpack_sparse_features(sparse_features)
  embeddings = tf.nn.embedding_lookup(params, ids)

  if allow_weights:
    # Multiply by weights, reshaping to allow broadcast.
    broadcast_weights_shape = tf.concat(0, [tf.shape(weights), [1]])
    embeddings *= tf.reshape(weights, broadcast_weights_shape)

  # Sum embeddings by index.
  return tf.unsorted_segment_sum(embeddings, indices, tf.size(sparse_features))


class GreedyParser(object):
  """Builds a Chen & Manning style greedy neural net parser.

  Builds a graph with an optional reader op connected at one end and
  operations needed to train the network on the other. Supports multiple
  network instantiations sharing the same parameters and network topology.

  The following named nodes are added to the training and eval networks:
    epochs: a tensor containing the current epoch number
    cost: a tensor containing the current training step cost
    gold_actions: a tensor containing actions from gold decoding
    feature_endpoints: a list of sparse feature vectors
    logits: output of the final layer before computing softmax
  The training network also contains:
    train_op: an op that executes a single training step

  Typical usage:

  parser = graph_builder.GreedyParser(num_actions, num_features,
                                      num_feature_ids, embedding_sizes,
                                      hidden_layer_sizes)
  parser.AddTraining(task_context, batch_size=5)
  with tf.Session('local') as sess:
    # This works because the session uses the same default graph as the
    # GraphBuilder did.
    sess.run(parser.inits.values())
    while True:
      tf_epoch, _ = sess.run([parser.training['epoch'],
                              parser.training['train_op']])
      if tf_epoch[0] > 0:
        break
  """

  def __init__(self,
               num_actions,
               num_features,
               num_feature_ids,
               embedding_sizes,
               hidden_layer_sizes,
               seed=None,
               gate_gradients=False,
               use_locking=False,
               embedding_init=1.0,
               relu_init=1e-4,
               bias_init=0.2,
               softmax_init=1e-4,
               averaging_decay=0.9999,
               use_averaging=True,
               check_parameters=True,
               check_every=1,
               allow_feature_weights=False,
               only_train='',
               arg_prefix=None,
               **unused_kwargs):
    """Initialize the graph builder with parameters defining the network.

    Args:
      num_actions: int size of the set of parser actions
      num_features: int list of dimensions of the feature vectors
      num_feature_ids: int list of same length as num_features corresponding to
        the sizes of the input feature spaces
      embedding_sizes: int list of same length as num_features of the desired
        embedding layer sizes
      hidden_layer_sizes: int list of desired relu layer sizes; may be empty
      seed: optional random initializer seed to enable reproducibility
      gate_gradients: if True, gradient updates are computed synchronously,
        ensuring consistency and reproducibility
      use_locking: if True, use locking to avoid read-write contention when
        updating Variables
      embedding_init: sets the std dev of normal initializer of embeddings to
        embedding_init / embedding_size ** .5
      relu_init: sets the std dev of normal initializer of relu weights
        to relu_init
      bias_init: sets constant initializer of relu bias to bias_init
      softmax_init: sets the std dev of normal initializer of softmax init
        to softmax_init
      averaging_decay: decay for exponential moving average when computing
        averaged parameters, set to 1 to do vanilla averaging
      use_averaging: whether to use moving averages of parameters during evals
      check_parameters: whether to check for NaN/Inf parameters during
        training
      check_every: checks numerics every check_every steps.
      allow_feature_weights: whether feature weights are allowed.
      only_train: the comma separated set of parameter names to train. If empty,
        all model parameters will be trained.
      arg_prefix: prefix for context parameters.
    """
    self._num_actions = num_actions
    self._num_features = num_features
    self._num_feature_ids = num_feature_ids
    self._embedding_sizes = embedding_sizes
    self._hidden_layer_sizes = hidden_layer_sizes
    self._seed = seed
    self._gate_gradients = gate_gradients
    self._use_locking = use_locking
    self._use_averaging = use_averaging
    self._check_parameters = check_parameters
    self._check_every = check_every
    self._allow_feature_weights = allow_feature_weights
    self._only_train = set(only_train.split(',')) if only_train else None
    self._feature_size = len(embedding_sizes)
    self._embedding_init = embedding_init
    self._relu_init = relu_init
    self._softmax_init = softmax_init
    self._arg_prefix = arg_prefix
    # Parameters of the network with respect to which training is done.
    self.params = {}
    # Other variables, with respect to which no training is done, but which we
    # nonetheless need to save in order to capture the state of the graph.
    self.variables = {}
    # Operations to initialize any nodes that require initialization.
    self.inits = {}
    # Training- and eval-related nodes.
    self.training = {}
    self.evaluation = {}
    self.saver = None
    # Nodes to compute moving averages of parameters, called every train step.
    self._averaging = {}
    self._averaging_decay = averaging_decay
    # Pretrained embeddings that can be used instead of constant initializers.
    self._pretrained_embeddings = {}
    # After the following 'with' statement, we'll be able to re-enter the
    # 'params' scope by re-using the self._param_scope member variable. See for
    # instance _AddParam.
    with tf.name_scope('params') as self._param_scope:
      self._relu_bias_init = tf.constant_initializer(bias_init)

  @property
  def embedding_size(self):
    size = 0
    for i in range(self._feature_size):
      size += self._num_features[i] * self._embedding_sizes[i]
    return size

  def _AddParam(self,
                shape,
                dtype,
                name,
                initializer=None,
                return_average=False):
    """Add a model parameter w.r.t. we expect to compute gradients.

    _AddParam creates both regular parameters (usually for training) and
    averaged nodes (usually for inference). It returns one or the other based
    on the 'return_average' arg.

    Args:
      shape: int list, tensor shape of the parameter to create
      dtype: tf.DataType, data type of the parameter
      name: string, name of the parameter in the TF graph
      initializer: optional initializer for the paramter
      return_average: if False, return parameter otherwise return moving average

    Returns:
      parameter or averaged parameter
    """
    if name not in self.params:
      step = tf.cast(self.GetStep(), tf.float32)
      # Put all parameters and their initializing ops in their own scope
      # irrespective of the current scope (training or eval).
      with tf.name_scope(self._param_scope):
        self.params[name] = tf.get_variable(name, shape, dtype, initializer)
        param = self.params[name]
        if initializer is not None:
          self.inits[name] = state_ops.init_variable(param, initializer)
        if self._averaging_decay == 1:
          logging.info('Using vanilla averaging of parameters.')
          ema = tf.train.ExponentialMovingAverage(decay=(step / (step + 1.0)),
                                                  num_updates=None)
        else:
          ema = tf.train.ExponentialMovingAverage(decay=self._averaging_decay,
                                                  num_updates=step)
        self._averaging[name + '_avg_update'] = ema.apply([param])
        self.variables[name + '_avg_var'] = ema.average(param)
        self.inits[name + '_avg_init'] = state_ops.init_variable(
            ema.average(param), tf.zeros_initializer)
    return (self.variables[name + '_avg_var'] if return_average else
            self.params[name])

  def GetStep(self):
    def OnesInitializer(shape, dtype=tf.float32):
      return tf.ones(shape, dtype)
    return self._AddVariable([], tf.int32, 'step', OnesInitializer)

  def _AddVariable(self, shape, dtype, name, initializer=None):
    if name in self.variables:
      return self.variables[name]
    self.variables[name] = tf.get_variable(name, shape, dtype, initializer)
    if initializer is not None:
      self.inits[name] = state_ops.init_variable(self.variables[name],
                                                 initializer)
    return self.variables[name]

  def _ReluWeightInitializer(self):
    with tf.name_scope(self._param_scope):
      return tf.random_normal_initializer(stddev=self._relu_init,
                                          seed=self._seed)

  def _EmbeddingMatrixInitializer(self, index, embedding_size):
    if index in self._pretrained_embeddings:
      return self._pretrained_embeddings[index]
    else:
      return tf.random_normal_initializer(
          stddev=self._embedding_init / embedding_size**.5,
          seed=self._seed)

  def _AddEmbedding(self,
                    features,
                    num_features,
                    num_ids,
                    embedding_size,
                    index,
                    return_average=False):
    """Adds an embedding matrix and passes the `features` vector through it."""
    embedding_matrix = self._AddParam(
        [num_ids, embedding_size],
        tf.float32,
        'embedding_matrix_%d' % index,
        self._EmbeddingMatrixInitializer(index, embedding_size),
        return_average=return_average)
    embedding = EmbeddingLookupFeatures(embedding_matrix,
                                        tf.reshape(features,
                                                   [-1],
                                                   name='feature_%d' % index),
                                        self._allow_feature_weights)
    return tf.reshape(embedding, [-1, num_features * embedding_size])

  def _BuildNetwork(self, feature_endpoints, return_average=False):
    """Builds a feed-forward part of the net given features as input.

    The network topology is already defined in the constructor, so multiple
    calls to BuildForward build multiple networks whose parameters are all
    shared. It is the source of the input features and the use of the output
    that distinguishes each network.

    Args:
      feature_endpoints: tensors with input features to the network
      return_average: whether to use moving averages as model parameters

    Returns:
      logits: output of the final layer before computing softmax
    """
    assert len(feature_endpoints) == self._feature_size

    # Create embedding layer.
    embeddings = []
    for i in range(self._feature_size):
      embeddings.append(self._AddEmbedding(feature_endpoints[i],
                                           self._num_features[i],
                                           self._num_feature_ids[i],
                                           self._embedding_sizes[i],
                                           i,
                                           return_average=return_average))

    last_layer = tf.concat(1, embeddings)
    last_layer_size = self.embedding_size

    # Create ReLU layers.
    for i, hidden_layer_size in enumerate(self._hidden_layer_sizes):
      weights = self._AddParam(
          [last_layer_size, hidden_layer_size],
          tf.float32,
          'weights_%d' % i,
          self._ReluWeightInitializer(),
          return_average=return_average)
      bias = self._AddParam([hidden_layer_size],
                            tf.float32,
                            'bias_%d' % i,
                            self._relu_bias_init,
                            return_average=return_average)
      last_layer = tf.nn.relu_layer(last_layer,
                                    weights,
                                    bias,
                                    name='layer_%d' % i)
      last_layer_size = hidden_layer_size

    # Create softmax layer.
    softmax_weight = self._AddParam(
        [last_layer_size, self._num_actions],
        tf.float32,
        'softmax_weight',
        tf.random_normal_initializer(stddev=self._softmax_init,
                                     seed=self._seed),
        return_average=return_average)
    softmax_bias = self._AddParam(
        [self._num_actions],
        tf.float32,
        'softmax_bias',
        tf.zeros_initializer,
        return_average=return_average)
    logits = tf.nn.xw_plus_b(last_layer,
                             softmax_weight,
                             softmax_bias,
                             name='logits')
    return {'logits': logits}

  def _AddGoldReader(self, task_context, batch_size, corpus_name):
    features, epochs, gold_actions = (
        gen_parser_ops.gold_parse_reader(task_context,
                                         self._feature_size,
                                         batch_size,
                                         corpus_name=corpus_name,
                                         arg_prefix=self._arg_prefix))
    return {'gold_actions': tf.identity(gold_actions,
                                        name='gold_actions'),
            'epochs': tf.identity(epochs,
                                  name='epochs'),
            'feature_endpoints': features}

  def _AddDecodedReader(self, task_context, batch_size, transition_scores,
                        corpus_name):
    features, epochs, eval_metrics, documents = (
        gen_parser_ops.decoded_parse_reader(transition_scores,
                                            task_context,
                                            self._feature_size,
                                            batch_size,
                                            corpus_name=corpus_name,
                                            arg_prefix=self._arg_prefix))
    return {'eval_metrics': eval_metrics,
            'epochs': tf.identity(epochs,
                                  name='epochs'),
            'feature_endpoints': features,
            'documents': documents}

  def _AddCostFunction(self, batch_size, gold_actions, logits):
    """Cross entropy plus L2 loss on weights and biases of the hidden layers."""
    dense_golden = BatchedSparseToDense(gold_actions, self._num_actions)
    cross_entropy = tf.div(
        tf.reduce_sum(tf.nn.softmax_cross_entropy_with_logits(
            logits, dense_golden)), batch_size)
    regularized_params = [tf.nn.l2_loss(p)
                          for k, p in self.params.items()
                          if k.startswith('weights') or k.startswith('bias')]
    l2_loss = 1e-4 * tf.add_n(regularized_params) if regularized_params else 0
    return {'cost': tf.add(cross_entropy, l2_loss, name='cost')}

  def AddEvaluation(self,
                    task_context,
                    batch_size,
                    evaluation_max_steps=300,
                    corpus_name='documents'):
    """Builds the forward network only without the training operation.

    Args:
      task_context: file path from which to read the task context.
      batch_size: batch size to request from reader op.
      evaluation_max_steps: max number of parsing actions during evaluation,
          only used in beam parsing.
      corpus_name: name of the task input to read parses from.

    Returns:
      Dictionary of named eval nodes.
    """
    def _AssignTransitionScores():
      return tf.assign(nodes['transition_scores'],
                       nodes['logits'], validate_shape=False)
    def _Pass():
      return tf.constant(-1.0)
    unused_evaluation_max_steps = evaluation_max_steps
    with tf.name_scope('evaluation'):
      nodes = self.evaluation
      nodes['transition_scores'] = self._AddVariable(
          [batch_size, self._num_actions], tf.float32, 'transition_scores',
          tf.constant_initializer(-1.0))
      nodes.update(self._AddDecodedReader(task_context, batch_size, nodes[
          'transition_scores'], corpus_name))
      nodes.update(self._BuildNetwork(nodes['feature_endpoints'],
                                      return_average=self._use_averaging))
      nodes['eval_metrics'] = cf.with_dependencies(
          [tf.cond(tf.greater(tf.size(nodes['logits']), 0),
                   _AssignTransitionScores, _Pass)],
          nodes['eval_metrics'], name='eval_metrics')
    return nodes

  def _IncrementCounter(self, counter):
    return state_ops.assign_add(counter, 1, use_locking=True)

  def _AddLearningRate(self, initial_learning_rate, decay_steps):
    """Returns a learning rate that decays by 0.96 every decay_steps.

    Args:
      initial_learning_rate: initial value of the learning rate
      decay_steps: decay by 0.96 every this many steps

    Returns:
      learning rate variable.
    """
    step = self.GetStep()
    return cf.with_dependencies(
        [self._IncrementCounter(step)],
        tf.train.exponential_decay(initial_learning_rate,
                                   step,
                                   decay_steps,
                                   0.96,
                                   staircase=True))

  def AddPretrainedEmbeddings(self, index, embeddings_path, task_context):
    """Embeddings at the given index will be set to pretrained values."""

    def _Initializer(shape, dtype=tf.float32):
      unused_dtype = dtype
      t = gen_parser_ops.word_embedding_initializer(
          vectors=embeddings_path,
          task_context=task_context,
          embedding_init=self._embedding_init)

      t.set_shape(shape)
      return t

    self._pretrained_embeddings[index] = _Initializer

  def AddTraining(self,
                  task_context,
                  batch_size,
                  learning_rate=0.1,
                  decay_steps=4000,
                  momentum=0.9,
                  corpus_name='documents'):
    """Builds a trainer to minimize the cross entropy cost function.

    Args:
      task_context: file path from which to read the task context
      batch_size: batch size to request from reader op
      learning_rate: initial value of the learning rate
      decay_steps: decay learning rate by 0.96 every this many steps
      momentum: momentum parameter used when training with momentum
      corpus_name: name of the task input to read parses from

    Returns:
      Dictionary of named training nodes.
    """
    with tf.name_scope('training'):
      nodes = self.training
      nodes.update(self._AddGoldReader(task_context, batch_size, corpus_name))
      nodes.update(self._BuildNetwork(nodes['feature_endpoints'],
                                      return_average=False))
      nodes.update(self._AddCostFunction(batch_size, nodes['gold_actions'],
                                         nodes['logits']))
      # Add the optimizer
      if self._only_train:
        trainable_params = [v
                            for k, v in self.params.iteritems()
                            if k in self._only_train]
      else:
        trainable_params = self.params.values()
      lr = self._AddLearningRate(learning_rate, decay_steps)
      optimizer = tf.train.MomentumOptimizer(lr,
                                             momentum,
                                             use_locking=self._use_locking)
      train_op = optimizer.minimize(nodes['cost'], var_list=trainable_params)
      for param in trainable_params:
        slot = optimizer.get_slot(param, 'momentum')
        self.inits[slot.name] = state_ops.init_variable(slot,
                                                        tf.zeros_initializer)
        self.variables[slot.name] = slot
      numerical_checks = [
          tf.check_numerics(param,
                            message='Parameter is not finite.')
          for param in trainable_params
          if param.dtype.base_dtype in [tf.float32, tf.float64]
      ]
      check_op = tf.group(*numerical_checks)
      avg_update_op = tf.group(*self._averaging.values())
      train_ops = [train_op]
      if self._check_parameters:
        train_ops.append(check_op)
      if self._use_averaging:
        train_ops.append(avg_update_op)
      nodes['train_op'] = tf.group(*train_ops, name='train_op')
    return nodes

  def AddSaver(self, slim_model=False):
    """Adds ops to save and restore model parameters.

    Args:
      slim_model: whether only averaged variables are saved.

    Returns:
      the saver object.
    """
    # We have to put the save op in the root scope otherwise running
    # "save/restore_all" won't find the "save/Const" node it expects.
    with tf.name_scope(None):
      variables_to_save = self.params.copy()
      variables_to_save.update(self.variables)
      if slim_model:
        for key in variables_to_save.keys():
          if not key.endswith('avg_var'):
            del variables_to_save[key]
      self.saver = tf.train.Saver(variables_to_save)
    return self.saver

# coding=utf-8
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Tests for lexicon_builder."""


# disable=no-name-in-module,unused-import,g-bad-import-order,maybe-no-member
import os.path

import tensorflow as tf

import syntaxnet.load_parser_ops

from tensorflow.python.framework import test_util
from tensorflow.python.platform import googletest
from tensorflow.python.platform import tf_logging as logging

from syntaxnet import sentence_pb2
from syntaxnet import task_spec_pb2
from syntaxnet.ops import gen_parser_ops

FLAGS = tf.app.flags.FLAGS

CONLL_DOC1 = u'''1 à¤¬à¤¾à¤¤ _ n NN _ _ _ _ _
2 à¤—à¤²à¤¤ _ adj JJ _ _ _ _ _
3 à¤¹à¥‹ _ v VM _ _ _ _ _
4 à¤¤à¥‹ _ avy CC _ _ _ _ _
5 à¤—à¥à¤¸à¥à¤¸à¤¾ _ n NN _ _ _ _ _
6 à¤¸à¥‡à¤²à¥‡à¤¬à¥à¤°à¤¿à¤Ÿà¤¿à¤œ _ n NN _ _ _ _ _
7 à¤•à¥‹ _ psp PSP _ _ _ _ _
8 à¤­à¥€ _ avy RP _ _ _ _ _
9 à¤†à¤¨à¤¾ _ v VM _ _ _ _ _
10 à¤²à¤¾à¤œà¤®à¥€ _ adj JJ _ _ _ _ _
11 à¤¹à¥ˆ _ v VM _ _ _ _ _
12 à¥¤ _ punc SYM _ _ _ _ _'''

CONLL_DOC2 = u'''1 à¤²à¥‡à¤•à¤¿à¤¨ _ avy CC _ _ _ _ _
2 à¤…à¤­à¤¿à¤¨à¥‡à¤¤à¥à¤°à¥€ _ n NN _ _ _ _ _
3 à¤•à¥‡ _ psp PSP _ _ _ _ _
4 à¤‡à¤¸ _ pn DEM _ _ _ _ _
5 à¤•à¤¦à¤® _ n NN _ _ _ _ _
6 à¤¸à¥‡ _ psp PSP _ _ _ _ _
7 à¤µà¤¹à¤¾à¤‚ _ pn PRP _ _ _ _ _
8 à¤°à¤‚à¤— _ n NN _ _ _ _ _
9 à¤®à¥‡à¤‚ _ psp PSP _ _ _ _ _
10 à¤­à¤‚à¤— _ adj JJ _ _ _ _ _
11 à¤ªà¥œ _ v VM _ _ _ _ _
12 à¤—à¤¯à¤¾ _ v VAUX _ _ _ _ _
13 à¥¤ _ punc SYM _ _ _ _ _'''

TAGS = ['NN', 'JJ', 'VM', 'CC', 'PSP', 'RP', 'JJ', 'SYM', 'DEM', 'PRP', 'VAUX']

CATEGORIES = ['n', 'adj', 'v', 'avy', 'n', 'psp', 'punc', 'pn']

TOKENIZED_DOCS = u'''à¤¬à¤¾à¤¤ à¤—à¤²à¤¤ à¤¹à¥‹ à¤¤à¥‹ à¤—à¥à¤¸à¥à¤¸à¤¾ à¤¸à¥‡à¤²à¥‡à¤¬à¥à¤°à¤¿à¤Ÿà¤¿à¤œ à¤•à¥‹ à¤­à¥€ à¤†à¤¨à¤¾ à¤²à¤¾à¤œà¤®à¥€ à¤¹à¥ˆ à¥¤
à¤²à¥‡à¤•à¤¿à¤¨ à¤…à¤­à¤¿à¤¨à¥‡à¤¤à¥à¤°à¥€ à¤•à¥‡ à¤‡à¤¸ à¤•à¤¦à¤® à¤¸à¥‡ à¤µà¤¹à¤¾à¤‚ à¤°à¤‚à¤— à¤®à¥‡à¤‚ à¤­à¤‚à¤— à¤ªà¥œ à¤—à¤¯à¤¾ à¥¤
'''

COMMENTS = u'# Line with fake comments.'


class LexiconBuilderTest(test_util.TensorFlowTestCase):

  def setUp(self):
    if not hasattr(FLAGS, 'test_srcdir'):
      FLAGS.test_srcdir = ''
    if not hasattr(FLAGS, 'test_tmpdir'):
      FLAGS.test_tmpdir = tf.test.get_temp_dir()
    self.corpus_file = os.path.join(FLAGS.test_tmpdir, 'documents.conll')
    self.context_file = os.path.join(FLAGS.test_tmpdir, 'context.pbtxt')

  def AddInput(self, name, file_pattern, record_format, context):
    inp = context.input.add()
    inp.name = name
    inp.record_format.append(record_format)
    inp.part.add().file_pattern = file_pattern

  def WriteContext(self, corpus_format):
    context = task_spec_pb2.TaskSpec()
    self.AddInput('documents', self.corpus_file, corpus_format, context)
    for name in ('word-map', 'lcword-map', 'tag-map',
                 'category-map', 'label-map', 'prefix-table',
                 'suffix-table', 'tag-to-category'):
      self.AddInput(name, os.path.join(FLAGS.test_tmpdir, name), '', context)
    logging.info('Writing context to: %s', self.context_file)
    with open(self.context_file, 'w') as f:
      f.write(str(context))

  def ReadNextDocument(self, sess, doc_source):
    doc_str, last = sess.run(doc_source)
    if doc_str:
      doc = sentence_pb2.Sentence()
      doc.ParseFromString(doc_str[0])
    else:
      doc = None
    return doc, last

  def ValidateDocuments(self):
    doc_source = gen_parser_ops.document_source(self.context_file, batch_size=1)
    with self.test_session() as sess:
      logging.info('Reading document1')
      doc, last = self.ReadNextDocument(sess, doc_source)
      self.assertEqual(len(doc.token), 12)
      self.assertEqual(u'à¤²à¤¾à¤œà¤®à¥€', doc.token[9].word)
      self.assertFalse(last)
      logging.info('Reading document2')
      doc, last = self.ReadNextDocument(sess, doc_source)
      self.assertEqual(len(doc.token), 13)
      self.assertEqual(u'à¤­à¤‚à¤—', doc.token[9].word)
      self.assertFalse(last)
      logging.info('Hitting end of the dataset')
      doc, last = self.ReadNextDocument(sess, doc_source)
      self.assertTrue(doc is None)
      self.assertTrue(last)

  def ValidateTagToCategoryMap(self):
    with file(os.path.join(FLAGS.test_tmpdir, 'tag-to-category'), 'r') as f:
      entries = [line.strip().split('\t') for line in f.readlines()]
    for tag, category in entries:
      self.assertIn(tag, TAGS)
      self.assertIn(category, CATEGORIES)

  def BuildLexicon(self):
    with self.test_session():
      gen_parser_ops.lexicon_builder(task_context=self.context_file).run()

  def testCoNLLFormat(self):
    self.WriteContext('conll-sentence')
    logging.info('Writing conll file to: %s', self.corpus_file)
    with open(self.corpus_file, 'w') as f:
      f.write((CONLL_DOC1 + u'\n\n' + CONLL_DOC2 + u'\n')
              .replace(' ', '\t').encode('utf-8'))
    self.ValidateDocuments()
    self.BuildLexicon()
    self.ValidateTagToCategoryMap()

  def testCoNLLFormatExtraNewlinesAndComments(self):
    self.WriteContext('conll-sentence')
    with open(self.corpus_file, 'w') as f:
      f.write((u'\n\n\n' + CONLL_DOC1 + u'\n\n\n' + COMMENTS +
               u'\n\n' + CONLL_DOC2).replace(' ', '\t').encode('utf-8'))
    self.ValidateDocuments()
    self.BuildLexicon()
    self.ValidateTagToCategoryMap()

  def testTokenizedTextFormat(self):
    self.WriteContext('tokenized-text')
    with open(self.corpus_file, 'w') as f:
      f.write(TOKENIZED_DOCS.encode('utf-8'))
    self.ValidateDocuments()
    self.BuildLexicon()

  def testTokenizedTextFormatExtraNewlines(self):
    self.WriteContext('tokenized-text')
    with open(self.corpus_file, 'w') as f:
      f.write((u'\n\n\n' + TOKENIZED_DOCS + u'\n\n\n').encode('utf-8'))
    self.ValidateDocuments()
    self.BuildLexicon()

if __name__ == '__main__':
  googletest.main()

# coding=utf-8
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Tests for english_tokenizer."""


# disable=no-name-in-module,unused-import,g-bad-import-order,maybe-no-member
import os.path

import tensorflow as tf

import syntaxnet.load_parser_ops

from tensorflow.python.framework import test_util
from tensorflow.python.platform import googletest
from tensorflow.python.platform import tf_logging as logging

from syntaxnet import sentence_pb2
from syntaxnet import task_spec_pb2
from syntaxnet.ops import gen_parser_ops

FLAGS = tf.app.flags.FLAGS


class TextFormatsTest(test_util.TensorFlowTestCase):

  def setUp(self):
    if not hasattr(FLAGS, 'test_srcdir'):
      FLAGS.test_srcdir = ''
    if not hasattr(FLAGS, 'test_tmpdir'):
      FLAGS.test_tmpdir = tf.test.get_temp_dir()
    self.corpus_file = os.path.join(FLAGS.test_tmpdir, 'documents.conll')
    self.context_file = os.path.join(FLAGS.test_tmpdir, 'context.pbtxt')

  def AddInput(self, name, file_pattern, record_format, context):
    inp = context.input.add()
    inp.name = name
    inp.record_format.append(record_format)
    inp.part.add().file_pattern = file_pattern

  def WriteContext(self, corpus_format):
    context = task_spec_pb2.TaskSpec()
    self.AddInput('documents', self.corpus_file, corpus_format, context)
    for name in ('word-map', 'lcword-map', 'tag-map',
                 'category-map', 'label-map', 'prefix-table',
                 'suffix-table', 'tag-to-category'):
      self.AddInput(name, os.path.join(FLAGS.test_tmpdir, name), '', context)
    logging.info('Writing context to: %s', self.context_file)
    with open(self.context_file, 'w') as f:
      f.write(str(context))

  def ReadNextDocument(self, sess, sentence):
    sentence_str, = sess.run([sentence])
    if sentence_str:
      sentence_doc = sentence_pb2.Sentence()
      sentence_doc.ParseFromString(sentence_str[0])
    else:
      sentence_doc = None
    return sentence_doc

  def CheckTokenization(self, sentence, tokenization):
    self.WriteContext('english-text')
    logging.info('Writing text file to: %s', self.corpus_file)
    with open(self.corpus_file, 'w') as f:
      f.write(sentence)
    sentence, _ = gen_parser_ops.document_source(
        self.context_file, batch_size=1)
    with self.test_session() as sess:
      sentence_doc = self.ReadNextDocument(sess, sentence)
      self.assertEqual(' '.join([t.word for t in sentence_doc.token]),
                       tokenization)

  def testSimple(self):
    self.CheckTokenization('Hello, world!', 'Hello , world !')
    self.CheckTokenization('"Hello"', "`` Hello ''")
    self.CheckTokenization('{"Hello@#$', '-LRB- `` Hello @ # $')
    self.CheckTokenization('"Hello..."', "`` Hello ... ''")
    self.CheckTokenization('()[]{}<>',
                           '-LRB- -RRB- -LRB- -RRB- -LRB- -RRB- < >')
    self.CheckTokenization('Hello--world', 'Hello -- world')
    self.CheckTokenization("Isn't", "Is n't")
    self.CheckTokenization("n't", "n't")
    self.CheckTokenization('Hello Mr. Smith.', 'Hello Mr. Smith .')
    self.CheckTokenization("It's Mr. Smith's.", "It 's Mr. Smith 's .")
    self.CheckTokenization("It's the Smiths'.", "It 's the Smiths ' .")
    self.CheckTokenization('Gotta go', 'Got ta go')
    self.CheckTokenization('50-year-old', '50-year-old')

  def testUrl(self):
    self.CheckTokenization('http://www.google.com/news is down',
                           'http : //www.google.com/news is down')


if __name__ == '__main__':
  googletest.main()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Tests for reader_ops."""


import os.path

import numpy as np
import tensorflow as tf

from tensorflow.python.framework import test_util
from tensorflow.python.ops import control_flow_ops as cf
from tensorflow.python.platform import googletest
from tensorflow.python.platform import tf_logging as logging

from syntaxnet import dictionary_pb2
from syntaxnet import graph_builder
from syntaxnet import sparse_pb2
from syntaxnet.ops import gen_parser_ops


FLAGS = tf.app.flags.FLAGS
if not hasattr(FLAGS, 'test_srcdir'):
  FLAGS.test_srcdir = ''
if not hasattr(FLAGS, 'test_tmpdir'):
  FLAGS.test_tmpdir = tf.test.get_temp_dir()


class ParsingReaderOpsTest(test_util.TensorFlowTestCase):

  def setUp(self):
    # Creates a task context with the correct testing paths.
    initial_task_context = os.path.join(
        FLAGS.test_srcdir,
        'syntaxnet/'
        'testdata/context.pbtxt')
    self._task_context = os.path.join(FLAGS.test_tmpdir, 'context.pbtxt')
    with open(initial_task_context, 'r') as fin:
      with open(self._task_context, 'w') as fout:
        fout.write(fin.read().replace('SRCDIR', FLAGS.test_srcdir)
                   .replace('OUTPATH', FLAGS.test_tmpdir))

    # Creates necessary term maps.
    with self.test_session() as sess:
      gen_parser_ops.lexicon_builder(task_context=self._task_context,
                                     corpus_name='training-corpus').run()
      self._num_features, self._num_feature_ids, _, self._num_actions = (
          sess.run(gen_parser_ops.feature_size(task_context=self._task_context,
                                               arg_prefix='brain_parser')))

  def GetMaxId(self, sparse_features):
    max_id = 0
    for x in sparse_features:
      for y in x:
        f = sparse_pb2.SparseFeatures()
        f.ParseFromString(y)
        for i in f.id:
          max_id = max(i, max_id)
    return max_id

  def testParsingReaderOp(self):
    # Runs the reader over the test input for two epochs.
    num_steps_a = 0
    num_actions = 0
    num_word_ids = 0
    num_tag_ids = 0
    num_label_ids = 0
    batch_size = 10
    with self.test_session() as sess:
      (words, tags, labels), epochs, gold_actions = (
          gen_parser_ops.gold_parse_reader(self._task_context,
                                           3,
                                           batch_size,
                                           corpus_name='training-corpus'))
      while True:
        tf_gold_actions, tf_epochs, tf_words, tf_tags, tf_labels = (
            sess.run([gold_actions, epochs, words, tags, labels]))
        num_steps_a += 1
        num_actions = max(num_actions, max(tf_gold_actions) + 1)
        num_word_ids = max(num_word_ids, self.GetMaxId(tf_words) + 1)
        num_tag_ids = max(num_tag_ids, self.GetMaxId(tf_tags) + 1)
        num_label_ids = max(num_label_ids, self.GetMaxId(tf_labels) + 1)
        self.assertIn(tf_epochs, [0, 1, 2])
        if tf_epochs > 1:
          break

    # Runs the reader again, this time with a lot of added graph nodes.
    num_steps_b = 0
    with self.test_session() as sess:
      num_features = [6, 6, 4]
      num_feature_ids = [num_word_ids, num_tag_ids, num_label_ids]
      embedding_sizes = [8, 8, 8]
      hidden_layer_sizes = [32, 32]
      # Here we aim to test the iteration of the reader op in a complex network,
      # not the GraphBuilder.
      parser = graph_builder.GreedyParser(
          num_actions, num_features, num_feature_ids, embedding_sizes,
          hidden_layer_sizes)
      parser.AddTraining(self._task_context,
                         batch_size,
                         corpus_name='training-corpus')
      sess.run(parser.inits.values())
      while True:
        tf_epochs, tf_cost, _ = sess.run(
            [parser.training['epochs'], parser.training['cost'],
             parser.training['train_op']])
        num_steps_b += 1
        self.assertGreaterEqual(tf_cost, 0)
        self.assertIn(tf_epochs, [0, 1, 2])
        if tf_epochs > 1:
          break

    # Assert that the two runs made the exact same number of steps.
    logging.info('Number of steps in the two runs: %d, %d',
                 num_steps_a, num_steps_b)
    self.assertEqual(num_steps_a, num_steps_b)

  def testParsingReaderOpWhileLoop(self):
    feature_size = 3
    batch_size = 5

    def ParserEndpoints():
      return gen_parser_ops.gold_parse_reader(self._task_context,
                                              feature_size,
                                              batch_size,
                                              corpus_name='training-corpus')

    with self.test_session() as sess:
      # The 'condition' and 'body' functions expect as many arguments as there
      # are loop variables. 'condition' depends on the 'epoch' loop variable
      # only, so we disregard the remaining unused function arguments. 'body'
      # returns a list of updated loop variables.
      def Condition(epoch, *unused_args):
        return tf.less(epoch, 2)

      def Body(epoch, num_actions, *feature_args):
        # By adding one of the outputs of the reader op ('epoch') as a control
        # dependency to the reader op we force the repeated evaluation of the
        # reader op.
        with epoch.graph.control_dependencies([epoch]):
          features, epoch, gold_actions = ParserEndpoints()
        num_actions = tf.maximum(num_actions,
                                 tf.reduce_max(gold_actions, [0], False) + 1)
        feature_ids = []
        for i in range(len(feature_args)):
          feature_ids.append(features[i])
        return [epoch, num_actions] + feature_ids

      epoch = ParserEndpoints()[-2]
      num_actions = tf.constant(0)
      loop_vars = [epoch, num_actions]

      res = sess.run(
          cf.While(Condition, Body, loop_vars, parallel_iterations=1))
      logging.info('Result: %s', res)
      self.assertEqual(res[0], 2)

  def testWordEmbeddingInitializer(self):
    def _TokenEmbedding(token, embedding):
      e = dictionary_pb2.TokenEmbedding()
      e.token = token
      e.vector.values.extend(embedding)
      return e.SerializeToString()

    # Provide embeddings for the first three words in the word map.
    records_path = os.path.join(FLAGS.test_tmpdir, 'sstable-00000-of-00001')
    writer = tf.python_io.TFRecordWriter(records_path)
    writer.write(_TokenEmbedding('.', [1, 2]))
    writer.write(_TokenEmbedding(',', [3, 4]))
    writer.write(_TokenEmbedding('the', [5, 6]))
    del writer

    with self.test_session():
      embeddings = gen_parser_ops.word_embedding_initializer(
          vectors=records_path,
          task_context=self._task_context).eval()
    self.assertAllClose(
        np.array([[1. / (1 + 4) ** .5, 2. / (1 + 4) ** .5],
                  [3. / (9 + 16) ** .5, 4. / (9 + 16) ** .5],
                  [5. / (25 + 36) ** .5, 6. / (25 + 36) ** .5]]),
        embeddings[:3,])


if __name__ == '__main__':
  googletest.main()

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""A program to generate ASCII trees from conll files."""

import collections

import asciitree
import tensorflow as tf

import syntaxnet.load_parser_ops

from tensorflow.python.platform import tf_logging as logging
from syntaxnet import sentence_pb2
from syntaxnet.ops import gen_parser_ops

flags = tf.app.flags
FLAGS = flags.FLAGS

flags.DEFINE_string('task_context',
                    'syntaxnet/models/parsey_mcparseface/context.pbtxt',
                    'Path to a task context with inputs and parameters for '
                    'feature extractors.')
flags.DEFINE_string('corpus_name', 'stdin-conll',
                    'Path to a task context with inputs and parameters for '
                    'feature extractors.')


def to_dict(sentence):
  """Builds a dictionary representing the parse tree of a sentence.

  Args:
    sentence: Sentence protocol buffer to represent.
  Returns:
    Dictionary mapping tokens to children.
  """
  token_str = ['%s %s %s' % (token.word, token.tag, token.label)
               for token in sentence.token]
  children = [[] for token in sentence.token]
  root = -1
  for i in range(0, len(sentence.token)):
    token = sentence.token[i]
    if token.head == -1:
      root = i
    else:
      children[token.head].append(i)

  def _get_dict(i):
    d = collections.OrderedDict()
    for c in children[i]:
      d[token_str[c]] = _get_dict(c)
    return d

  tree = collections.OrderedDict()
  tree[token_str[root]] = _get_dict(root)
  return tree


def main(unused_argv):
  logging.set_verbosity(logging.INFO)
  with tf.Session() as sess:
    src = gen_parser_ops.document_source(batch_size=32,
                                         corpus_name=FLAGS.corpus_name,
                                         task_context=FLAGS.task_context)
    sentence = sentence_pb2.Sentence()
    while True:
      documents, finished = sess.run(src)
      logging.info('Read %d documents', len(documents))
      for d in documents:
        sentence.ParseFromString(d)
        tr = asciitree.LeftAligned()
        d = to_dict(sentence)
        print 'Input: %s' % sentence.text
        print 'Parse:'
        print tr(d)

      if finished:
        break


if __name__ == '__main__':
  tf.app.run()

