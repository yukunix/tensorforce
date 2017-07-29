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
Multi-layer perceptron baseline value function.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from six.moves import xrange
import tensorflow as tf

from tensorforce import util
from tensorforce.core.networks import NeuralNetwork, layered_network_builder
from tensorforce.core.baselines import Baseline


class MLPBaseline(Baseline):

    def __init__(self, size, hidden_layers=2, repeat_update=100):
        """Multilayer-perceptron baseline value function.

        Args:
            size: Number of neurons per hidden layer
            hidden_layers: Number of hidden layers in the base line
            repeat_update: Epochs over the training data to fit the baseline
        """

        self.size = size
        self.hidden_layers = hidden_layers
        self.repeat_update = repeat_update
        self.session = None

    def create_tf_operations(self, config):
        if len(config.states) > 1:
            raise Exception()

        with tf.variable_scope('mlp_value_function'):
            self.state = tf.placeholder(dtype=tf.float32, shape=(None, util.prod(next(iter(config.states))[1].shape)))
            self.returns = tf.placeholder(dtype=tf.float32, shape=(None,))

            layers = []
            for _ in xrange(self.hidden_layers):
                layers.append({'type': 'dense', 'size': self.size})

            layers.append({'type': 'linear', 'size': 1})
            network = NeuralNetwork(network_builder=layered_network_builder(layers),
                                    inputs=dict(state=self.state))

            self.prediction = network.output
            loss = tf.nn.l2_loss(self.prediction - self.returns)

            optimizer = tf.train.AdamOptimizer(learning_rate=config.learning_rate)

            self.optimize = optimizer.minimize(loss)

    def predict(self, states):
        states = next(iter(states.values()))

        return self.session.run(self.prediction, {self.state: states})[0]

    def update(self, states, returns):
        #TODO could do sampling here
        states = next(iter(states.values()))

        for _ in range(self.repeat_update):
            self.session.run(self.optimize, {self.state: states, self.returns: returns})
