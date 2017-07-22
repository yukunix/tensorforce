# Copyright 2017 reinforce.io. All Rights Reserved.
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
"""
A policy gradient agent provides generic methods used in pg algorithms, e.g.
GAE-computation or merging of episode data.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import numpy as np
import tensorflow as tf

from tensorforce import TensorForceError, util
from tensorforce.models import Model
from tensorforce.core.networks import NeuralNetwork
from tensorforce.core.value_functions import value_functions
from tensorforce.core.distributions import distributions, Distribution, Gaussian, Categorical


def _get_distribution(action):
    """Return the distribution associated with the action.

    The distribution in `action.distribution` can be either provided as a string
    or as an instance of Distribution. Defaults to `Gaussian` and `Categorical`.

    Args:
        action: dict

    Returns:
        distribution: instance of `Distribution`

    """
    if 'distribution' not in action:
        if action.continuous:
            return Gaussian()
        else:
            return Categorical(num_actions=action.num_actions)

    distribution = action.distribution

    if isinstance(distribution, Distribution):
        return distribution

    if distribution not in distributions:
        raise TensorForceError('Unknown distribution: {}'.format(distribution))

    distribution = distributions[distribution]
    if action.continuous:
        return distribution()
    else:
        return distribution(num_actions=action.num_actions)


class PolicyGradientModel(Model):
    """
    Policy Gradient Model base class.


    A Policy Gradient Model expects the following additional configuration parameters:

    * `baseline`: string indicating the baseline value function (currently 'linear' or 'mlp').
    * `baseline_args`: list of arguments for the baseline value function.
    * `baseline_kwargs`: dict of keyword arguments for the baseline value function.
    * `generalized_advantage_estimation`: boolean indicating whether to use GAE estimation.
    * `gae_lambda`: float of the Generalized Advantage Estimation lambda.
    * `normalize_advantage`: boolean indicating whether to normalize the advantage or not.

    """
    default_config = dict(
        baseline=None,
        baseline_args=None,
        baseline_kwargs=None,
        generalized_advantage_estimation=False,
        gae_lambda=0.97,
        normalize_advantage=False
    )

    def __init__(self, config):
        config.default(PolicyGradientModel.default_config)

        # distribution
        self.distribution = dict()
        for name, action in config.actions:
            self.distribution[name] = _get_distribution(action)

        # baseline
        if config.baseline is None:
            self.baseline = None
        else:
            baseline = util.function(f=config.baseline, predefined=value_functions)
            args = config.baseline_args or ()
            kwargs = config.baseline_kwargs or {}
            self.baseline = baseline(*args, **kwargs)

        super(PolicyGradientModel, self).__init__(config)

        # advantage estimation
        self.generalized_advantage_estimation = config.generalized_advantage_estimation
        if self.generalized_advantage_estimation:
            self.gae_lambda = config.gae_lambda
        self.normalize_advantage = config.normalize_advantage

    def create_tf_operations(self, config):
        super(PolicyGradientModel, self).create_tf_operations(config)

        with tf.variable_scope('value_function'):
            self.network = NeuralNetwork(config.network, inputs=self.state)
            self.internal_inputs.extend(self.network.internal_inputs)
            self.internal_outputs.extend(self.network.internal_outputs)
            self.internal_inits.extend(self.network.internal_inits)

        with tf.variable_scope('distribution'):
            for action, distribution in self.distribution.items():
                distribution.create_tf_operations(x=self.network.output, deterministic=self.deterministic, **config.actions[action])
                self.action_taken[action] = distribution.value

        if self.baseline:
            with tf.variable_scope('baseline'):
                self.baseline.create_tf_operations(config)

    def set_session(self, session):
        super(PolicyGradientModel, self).set_session(session)
        if self.baseline is not None:
            self.baseline.session = session

    def update(self, batch):
        """Generic policy gradient update on a batch of experiences. Each model needs to update its specific
        logic.
        
        Args:
            batch: 

        Returns:

        """
        batch['returns'] = util.cumulative_discount(rewards=batch['rewards'], terminals=batch['terminals'],
                                                    discount=self.discount)
        # assert utils.discount(batch['rewards'], batch['terminals'], self.discount) == discount
        batch['rewards'] = self.advantage_estimation(batch)
        if self.baseline:
            self.baseline.update(states=batch['states'], returns=batch['returns'])
        super(PolicyGradientModel, self).update(batch)

    def advantage_estimation(self, batch):
        """Expects a batch, returns advantages according to config.

        Args:
            batch: 

        Returns:

        """
        if not self.baseline:
            return batch['returns']

        estimates = self.baseline.predict(states=batch['states'])
        if self.generalized_advantage_estimation:
            deltas = np.array(
                [self.discount * estimates[n + 1] - estimates[n] if (n < len(estimates) - 1 and not terminal) else 0.0
                 for n, terminal in enumerate(batch['terminals'])])
            deltas += batch['rewards']
            advantage = util.cumulative_discount(rewards=deltas, terminals=batch['terminals'],
                                                 discount=(self.discount * self.gae_lambda))
        else:
            advantage = np.array(batch['returns']) - estimates

        if self.normalize_advantage:
            advantage -= advantage.mean()
            advantage /= advantage.std() + 1e-8

        return advantage
