import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import gym
import matplotlib.pyplot as plt
import copy
from dqn import DQN

# hyper-parameters
BATCH_SIZE = 128
LR = 0.01
GAMMA = 0.90
EPISILO = 0.9
MEMORY_CAPACITY = 2000
Q_NETWORK_ITERATION = 100

env = gym.make("CartPole-v0")
env = env.unwrapped
NUM_ACTIONS = env.action_space.n
NUM_STATES = env.observation_space.shape[0]
ENV_A_SHAPE = (
    0 if isinstance(env.action_space.sample(), int) else env.action_space.sample.shape
)


def reward_func(env, x, x_dot, theta, theta_dot):
    r1 = (env.x_threshold - abs(x)) / env.x_threshold - 0.5
    r2 = (env.theta_threshold_radians - abs(theta)) / env.theta_threshold_radians - 0.5
    reward = r1 + r2
    return reward


def main():
    dqn = DQN(NUM_STATES, ENV_A_SHAPE, NUM_ACTIONS)
    episodes = 400
    print("Collecting Experience....")
    reward_list = []
    plt.ion()
    fig, ax = plt.subplots()
    for i in range(episodes):
        state = env.reset()
        ep_reward = 0
        while True:
            env.render()
            action = dqn.choose_action(state)
            next_state, _, done, info = env.step(action)
            x, x_dot, theta, theta_dot = next_state
            reward = reward_func(env, x, x_dot, theta, theta_dot)

            dqn.store_transition(state, action, reward, next_state)
            ep_reward += reward

            if dqn.memory_counter >= MEMORY_CAPACITY:
                dqn.learn()
                if done:
                    print(
                        "episode: {} , the episode reward is {}".format(
                            i, round(ep_reward, 3)
                        )
                    )
            if done:
                break
            state = next_state
        r = copy.copy(reward)
        reward_list.append(r)
        ax.set_xlim(0, 300)
        # ax.cla()
        ax.plot(reward_list, "g-", label="total_loss")
        plt.pause(0.001)


if __name__ == "__main__":
    main()
