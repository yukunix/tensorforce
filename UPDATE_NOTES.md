Update notes
------------

This file tracks all major updates and new features. As TensorForce is still in alpha, 
we are continuously implementing small updates and bug fixes, which will not
be tracked here in detail but through github issues.

2nd September 2017

- Added multi-LSTM support
- Fixed various bugs around reporting and logging
- Introduced CNN baseline
- Added baseline support for multiple states (experimental). Every state gets its own baseline
  and predictions are averaged

13th August 2017

- Fixed PPO performance issues, which we now recommend as the default
- Implemented Beta distribution for bounded actions
- Added n-step DQN and multithreaded runner
- Fixed wrong internal calculation of `prob_ratio` and `kl_divergence` in TRPO/PPO
- Added `next_internals` functionality to memories and QModel
- Changed config value names related to advantage estimation to `gae_rewards` and `normalize_rewards`


3rd August 2017

- Added `ls_accept_ratio=0.01` and adapted names of other TRPO config parameters related to line search
- Various bugs in Categorical DQN and Q-model target network scope fixed by @Islandman93
- Refactored distributions, categorical now using Gumbel-softmax

29th July 2017

- Added `QModel` as base class for DQN (hence DQFD) and NAF
- Added `next_state` placeholder to `QModel`, and boolean flag to `Memory.get_batch` to include next states
- `Configuration` now keeps track of which values were accessed, and `Agent` reports warning if not all were accessed


28th July 2017

- Moved external environments to tensorforce/contrib. The environment module just contains the base environment  class and our test environment going forward
- Merged environments ALE and Maze explorer, thanks to Islandman93 and mryellow


25th July 2017

- New optional argument `shape` for action specification, if an array of actions sharing the same specification is required
- Complete and correct mapping of OpenAIGym state/action spaces to corresponding TensorForce state/action specifications
- `MinimalTest` environment extension for multiple actions, plus an additional multi-state/action test for each agent


23th July 2017

- Implemented prototype of Proximal Policy Optimisation (PPO)
- Configuration argument network can now take module paths, not just functions
- Fixed prioritized experience replay sampling bug
- Enabling default values for distributions, see https://github.com/reinforceio/tensorforce/issues/34


8th July 2017

- BREAKING CHANGE: We modified the act and observe API once more because we think there was
a lack of clarity with regard to which state is observed (current vs next). The agent now internally
manages states and actions in the correct sequence so observe only needs reward and terminal.
- We further introduced a method ```import_observations``` so memory-based agents can preload
data into memory (e.g. if historic data is available). We also added a method ```last_observation```
on the generic agent which gives the current state, action, reward, terminal and internal state
- Fixed distributed agent mode, should run as intended now
- Fixed target network usage in NAF. Tests now run smoothl
- DQFDAgent now inherits from MemoryAgent


2nd July 2017

- Fixed lab integration: updated bazel BUILD file with command line options
- Adjusted environment integration to correctly select state and action interfaces
- Changed default agent to VPG since lab mixes continuous and discrete actions


25h June 2017

-   Added prioritised experience replay
-   Added RandomAgent for discrete/continuous random baselines
-   Moved pre-processing from runner to agent, analogue to exploration


11th June 2017

-   Fixed bug in DQFD test where demo data was not always the
    correct action. Also fixed small bug in DQFD loss (mean over
    supervised loss)
-   Network entry added to configuration so no separate network builder
    has to be passed to the agent constructor (see example)
-   The async mode using distributed tensorflow has been merged into the
    main model class. See the openai\_gym\_async.py example. In
    particular, this means multiple agents are now available in
    async mode. N.b. we are still working on making async/distributed
    things more convenient to use.
-   Fixed bug in NAF where target value (V) was connected to
    training output. Also added gradient clipping to NAF because we
    observed occasional numerical instability in testing.
-   For the same reason, we have altered the tests to always run
    multiple times and allow for an occasional failure on travis so our
    builds don't get broken by a random initialisation leading to
    an under/overflow.
-   Updated OpenAI Universe integration to work with our state/action
    interface, see an example in examples/openai\_universe.py
-   Added convenience method to create Network directly from json
    without needing to create a network builder, see examples for usage
