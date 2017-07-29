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

from tensorforce.models.model import Model
from tensorforce.models.policy_gradient_model import PolicyGradientModel
from tensorforce.models.q_model import QModel
from tensorforce.models.vpg_model import VPGModel
from tensorforce.models.trpo_model import TRPOModel
from tensorforce.models.dqn_model import DQNModel
from tensorforce.models.naf_model import NAFModel
from tensorforce.models.dqfd_model import DQFDModel


models = dict(
    VPGModel=VPGModel,
    TRPOModel=TRPOModel,
    DQNModel=DQNModel,
    NAFModel=NAFModel,
    DQFDModel=DQFDModel
)


__all__ = ['Model', 'PolicyGradientModel', 'QModel', 'VPGModel', 'TRPOModel', 'DQNModel', 'NAFModel', 'DQFDModel', 'models']
