"""Executes Keras benchmarks and accuracy tests."""
from __future__ import print_function

import os

from absl import flags
from absl.testing import flagsaver
import tensorflow as tf  # pylint: disable=g-bad-import-order

from official.resnet import cifar10_main as cifar_main
import official.resnet.keras.keras_cifar_main as keras_cifar_main
import official.resnet.keras.keras_common as keras_common

DATA_DIR = '/data/cifar10_data/'


class KerasCifar10BenchmarkTests(object):
  """Benchmarks and accuracy tests for KerasCifar10."""

  local_flags = None

  def __init__(self, output_dir=None):
    self.oss_report_object = None
    self.output_dir = output_dir

  def keras_resnet56_1_gpu(self):
    """Test keras based model with Keras fit and distribution strategies."""
    self._setup()
    flags.FLAGS.num_gpus = 1
    flags.FLAGS.data_dir = DATA_DIR
    flags.FLAGS.batch_size = 128
    flags.FLAGS.train_epochs = 182
    flags.FLAGS.model_dir = self._get_model_dir('keras_resnet56_1_gpu')
    flags.FLAGS.resnet_size = 56
    flags.FLAGS.dtype = 'fp32'
    stats = keras_cifar_main.run(flags.FLAGS)
    self._fill_report_object(stats)

  def keras_resnet56_4_gpu(self):
    """Test keras based model with Keras fit and distribution strategies."""
    self._setup()
    flags.FLAGS.num_gpus = 4
    flags.FLAGS.data_dir = self._get_model_dir('keras_resnet56_4_gpu')
    flags.FLAGS.batch_size = 128
    flags.FLAGS.train_epochs = 182
    flags.FLAGS.model_dir = ''
    flags.FLAGS.resnet_size = 56
    flags.FLAGS.dtype = 'fp32'
    stats = keras_cifar_main.run(flags.FLAGS)
    self._fill_report_object(stats)

  def keras_resnet56_no_dist_strat_1_gpu(self):
    """Test keras based model with Keras fit but not distribution strategies."""
    self._setup()
    flags.FLAGS.dist_strat_off = True
    flags.FLAGS.num_gpus = 1
    flags.FLAGS.data_dir = DATA_DIR
    flags.FLAGS.batch_size = 128
    flags.FLAGS.train_epochs = 182
    flags.FLAGS.model_dir = self._get_model_dir(
        'keras_resnet56_no_dist_strat_1_gpu')
    flags.FLAGS.resnet_size = 56
    flags.FLAGS.dtype = 'fp32'
    stats = keras_cifar_main.run(flags.FLAGS)
    self._fill_report_object(stats)

  def _fill_report_object(self, stats):
    if self.oss_report_object:
      self.oss_report_object.top_1 = stats['accuracy_top_1'].item()
      self.oss_report_object.add_other_quality(stats['training_accuracy_top_1']
                                               .item(),
                                               'top_1_train_accuracy')
    else:
      raise ValueError('oss_report_object has not been set.')

  def _get_model_dir(self, folder_name):
    return os.path.join(self.output_dir, folder_name)

  def _setup(self):
    """Setups up and resets flags before each test."""
    tf.logging.set_verbosity(tf.logging.DEBUG)
    if KerasCifar10BenchmarkTests.local_flags is None:
      keras_common.define_keras_flags()
      cifar_main.define_cifar_flags()
      # Loads flags to get defaults to then override.
      flags.FLAGS(['foo'])
      saved_flag_values = flagsaver.save_flag_values()
      KerasCifar10BenchmarkTests.local_flags = saved_flag_values
      return
    flagsaver.restore_flag_values(KerasCifar10BenchmarkTests.local_flags)