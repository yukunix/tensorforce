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
A policy gradient agent provides generic methods used of pg algorithms, e.g.
GAE-computation or merging of episode data.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import numpy as np
import tensorflow as tf

from tensorforce import util
from tensorforce.core.distributions.beta import Beta
from tensorforce.models import Model
from tensorforce.core.networks import NeuralNetwork
from tensorforce.core.baselines import Baseline
from tensorforce.core.distributions import Distribution, Categorical, Gaussian


class PolicyGradientModel(Model):
    """
    Policy Gradient Model base class.


    A Policy Gradient Model expects the following additional configuration parameters:

    * `baseline`: string indicating the baseline value function (currently 'linear' or 'mlp').
    * `baseline_args`: list of arguments for the baseline value function.
    * `baseline_kwargs`: dict of keyword arguments for the baseline value function.
    * `gae_rewards`: boolean indicating whether to use GAE reward estimation.
    * `gae_lambda`: GAE lambda.
    * `normalize_rewards`: boolean indicating whether to normalize rewards.

    """
    default_config = dict(
        baseline=None,
        gae_rewards=False,
        gae_lambda=0.97,
        normalize_rewards=False
    )

    def __init__(self, config):
        config.default(PolicyGradientModel.default_config)

        # distribution
        self.distribution = dict()
        for name, action in config.actions:
            if 'distribution' in action:
                kwargs = dict(action)
                self.distribution[name] = Distribution.from_config(config=action.distribution, kwargs=kwargs)
            elif action.continuous:
                if action.min_value is None:
                    assert action.max_value is None
                    self.distribution[name] = Gaussian(shape=action.shape)
                else:
                    assert action.max_value is not None
                    self.distribution[name] = Beta(min_value=action.min_value, max_value=action.max_value, shape=action.shape)
            else:
                self.distribution[name] = Categorical(shape=action.shape, num_actions=action.num_actions)

        # baseline
        if config.baseline is None:
            self.baseline = None
        else:
            self.baseline = dict()
            for name, state in config.states:
                self.baseline[name] = Baseline.from_config(config=config.baseline)

        # advantage estimation
        self.gae_rewards = config.gae_rewards
        self.gae_lambda = config.gae_lambda
        self.normalize_rewards = config.normalize_rewards

        super(PolicyGradientModel, self).__init__(config)

    def create_tf_operations(self, config):
        super(PolicyGradientModel, self).create_tf_operations(config)

        with tf.variable_scope('value_function'):
            network_builder = util.get_function(fct=config.network)
            self.network = NeuralNetwork(network_builder=network_builder, inputs=self.state)
            self.internal_inputs.extend(self.network.internal_inputs)
            self.internal_outputs.extend(self.network.internal_outputs)
            self.internal_inits.extend(self.network.internal_inits)

        with tf.variable_scope('distribution'):
            for action, distribution in self.distribution.items():
                with tf.variable_scope(action):
                    distribution.create_tf_operations(x=self.network.output, deterministic=self.deterministic)
                self.action_taken[action] = distribution.sample()

        if self.baseline:
            with tf.variable_scope('baseline'):
                # Generate one baseline per state input, later average their predictions
                for name, state in config.states:
                    self.baseline[name].create_tf_operations(state, scope='baseline_' + name)

    def set_session(self, session):
        super(PolicyGradientModel, self).set_session(session)

        if self.baseline is not None:
            for baseline in self.baseline.values():
                baseline.session = session

    def update(self, batch):
        """Generic policy gradient update on a batch of experiences. Each model needs to update its specific
        logic.
        
        Args:
            batch: 

        Returns:

        """
        batch['rewards'], discounted_rewards = self.reward_estimation(
            states=batch['states'],
            rewards=batch['rewards'],
            terminals=batch['terminals']
        )
        if self.baseline:
            for name, state in batch['states'].items():
                self.baseline[name].update(
                    states=state,
                    returns=discounted_rewards
                )

        super(PolicyGradientModel, self).update(batch)

    def reward_estimation(self, states, rewards, terminals):
        """Process rewards according to the configuration.

        Args:
            states:
            rewards:
            terminals:

        Returns:

        """
        discounted_rewards = util.cumulative_discount(
            values=rewards,
            terminals=terminals,
            discount=self.discount
        )

        if self.baseline:
            state_values = list()
            for name, state in states.items():
                state_value = self.baseline[name].predict(states=state)
                state_values.append(state_value)

            state_values = np.mean(state_values, axis=0)

            if self.gae_rewards:
                td_residuals = rewards + np.array(
                    [self.discount * state_values[n + 1] - state_values[n] if (n < len(state_values) - 1 and not terminal) else 0.0 for n, terminal in enumerate(terminals)])
                rewards = util.cumulative_discount(
                    values=td_residuals,
                    terminals=terminals,
                    discount=(self.discount * self.gae_lambda)
                )
            else:
                rewards = discounted_rewards - state_values
        else:
            rewards = discounted_rewards

        mean = rewards.mean()
        stddev = rewards.std()
        self.logger.debug('Reward mean {} and variance {}.'.format(mean, stddev * stddev))

        if self.normalize_rewards:
            rewards = (rewards - mean) / max(stddev, util.epsilon)

        self.logger.debug('First ten rewards: {}.'.format(rewards[:10]))

        return rewards, discounted_rewards
