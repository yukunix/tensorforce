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
Deep Q-learning from demonstration. This agent pre-trains from demonstration data.

Original paper: 'Learning from Demonstrations for Real World Reinforcement Learning'

https://arxiv.org/abs/1704.03732
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from six.moves import xrange

from tensorforce.agents import MemoryAgent
from tensorforce.core.memories import Replay
from tensorforce.models import DQFDModel


class DQFDAgent(MemoryAgent):
    """
    Deep Q-learning from demonstration (DQFD) agent ([Hester et al., 2017](https://arxiv.org/abs/1704.03732)).
    This agent uses DQN to pre-train from demonstration data.

    Configuration:

    Each agent requires the following configuration parameters:

    * `states`: dict containing one or more state definitions.
    * `actions`: dict containing one or more action definitions.
    * `preprocessing`: dict or list containing state preprocessing configuration.
    * `exploration`: dict containing action exploration configuration.

    Each model requires the following configuration parameters:

    * `discount`: float of discount factor (gamma).
    * `learning_rate`: float of learning rate (alpha).
    * `optimizer`: string of optimizer to use (e.g. 'adam').
    * `device`: string of tensorflow device name.
    * `tf_summary`: string directory to write tensorflow summaries. Default None
    * `tf_summary_level`: int indicating which tensorflow summaries to create.
    * `tf_summary_interval`: int number of calls to get_action until writing tensorflow summaries on update.
    * `log_level`: string containing logleve (e.g. 'info').
    * `distributed`: boolean indicating whether to use distributed tensorflow.
    * `global_model`: global model.
    * `session`: session to use.


    The `DQFDAgent` class additionally requires the following parameters:


    * `batch_size`: integer of the batch size.
    * `memory_capacity`: integer of maximum experiences to store.
    * `memory`: string indicating memory type ('replay' or 'prioritized_replay').
    * `min_replay_size`: integer of minimum replay size before the first update.
    * `update_rate`: float of the update rate (e.g. 0.25 = every 4 steps).
    * `target_network_update_rate`: float of target network update rate (e.g. 0.01 = every 100 steps).
    * `use_target_network`: boolean indicating whether to use a target network.
    * `update_repeat`: integer of how many times to repeat an update.
    * `update_target_weight`: float of update target weight (tau parameter).
    * `demo_sampling_ratio`: float, ratio of expert data used at runtime to train from.
    * `supervised_weight`: float, weight of large margin classifier loss.
    * `expert_margin`: float of difference in Q-values between expert action and other actions enforced by the large margin function.
    * `clip_loss`: float if not 0, uses the huber loss with clip_loss as the linear bound


    """

    name = 'DQFDAgent'
    model = DQFDModel

    default_config = dict(
        target_update_frequency=10000,
        demo_memory_capacity=1000000,
        demo_sampling_ratio=0.01,
    )

    def __init__(self, config, model=None):
        config.default(DQFDAgent.default_config)
        super(DQFDAgent, self).__init__(config, model)
        self.target_update_frequency = config.target_update_frequency

        # This is the demonstration memory that we will fill with observations before starting
        # the main training loop
        self.demo_memory = Replay(config.demo_memory_capacity, config.states, config.actions)

        # The demo_sampling_ratio, called p in paper, controls ratio of expert vs online training samples
        # p = n_demo / (n_demo + n_replay) => n_demo  = p * n_replay / (1 - p)
        self.demo_batch_size = int(config.demo_sampling_ratio * config.batch_size / (1.0 - config.demo_sampling_ratio))
        assert self.demo_batch_size > 0, 'Check DQFD sampling parameters to make sure demo_batch_size is positive. (Calculated {} based on current parameters)'.format(self.demo_batch_size)

    def observe(self, reward, terminal):
        """Adds observations, updates via sampling from memories according to update rate.
        DQFD samples from the online replay memory and the demo memory with
        the fractions controlled by a hyper parameter p called 'expert sampling ratio.

        Args:
            reward:
            terminal:

        Returns:

        """
        super(DQFDAgent, self).observe(reward=reward, terminal=terminal)

        if self.timestep >= self.first_update and self.timestep % self.update_frequency == 0:
            for _ in xrange(self.repeat_update):
                batch = self.demo_memory.get_batch(self.demo_batch_size)
                self.model.demonstration_update(batch=batch)

    def import_demonstrations(self, demonstrations):
        """Imports demonstrations, i.e. expert observations. Note that for large numbers of observations,
        set_demonstrations is more appropriate, which directly sets memory contents to an array an expects
        a different layout.

        Args:
            demonstrations: List of observation dicts

        Returns:

        """
        for observation in demonstrations:
            if self.unique_state:
                state = dict(state=observation['state'])
            else:
                state = observation['state']
            if self.unique_action:
                action = dict(action=observation['action'])
            else:
                action = observation['action']
            self.demo_memory.add_observation(
                state=state,
                action=action,
                reward=observation['reward'],
                terminal=observation['terminal'],
                internal=observation['internal']
            )

    def set_demonstrations(self, batch):
        """
        Set all demonstrations from batch data. Expects a dict wherein each value contains an array
        containing all states, actions, rewards, terminals and internals respectively.
        of
        Args:
            batch:

        Returns:

        """
        self.demo_memory.set_memory(
            states=batch['states'],
            actions=batch['actions'],
            rewards=batch['rewards'],
            terminals=batch['terminals'],
            internals=batch['internals']
        )

    def pretrain(self, steps):
        """Computes pretrain updates.

        Args:
            steps: Number of updates to execute.

        Returns:

        """
        for _ in xrange(steps):
            # Sample from demo memory
            batch = self.demo_memory.get_batch(batch_size=self.batch_size, next_states=True)

            # Update using both double Q-learning and supervised double_q_loss
            self.model.demonstration_update(batch)
