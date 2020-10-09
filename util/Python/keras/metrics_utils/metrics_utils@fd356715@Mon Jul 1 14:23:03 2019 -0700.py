"""Utilities related to metrics."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


class Reduction(object):
    """Types of metrics reduction.

    Contains the following values:
    * `SUM`: Scalar sum of weighted values.
    * `SUM_OVER_BATCH_SIZE`: Scalar `SUM` of weighted values divided by
        number of elements in values.
    * `WEIGHTED_MEAN`: Scalar sum of weighted values divided by sum of weights.
    """

    SUM = 'sum'
    SUM_OVER_BATCH_SIZE = 'sum_over_batch_size'
    WEIGHTED_MEAN = 'weighted_mean'


def update_state_wrapper(update_state_fn):
    """Decorator to wrap metric `update_state()` with `add_update()`.

    # Arguments
        update_state_fn: function that accumulates metric statistics.

    # Returns
        Decorated function that wraps `update_state_fn()` with `add_update()`.
    """
    def decorated(metric_obj, *args, **kwargs):
        """Decorated function with `add_update()`."""

        update_op = update_state_fn(*args, **kwargs)
        metric_obj.add_update(update_op)
        return update_op

    return decorated