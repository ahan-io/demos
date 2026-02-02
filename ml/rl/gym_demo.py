import time
import numpy as np
from itertools import count
from collections import namedtuple

import gym

# Importing PyTorch here
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions import Categorical

SavedAction = namedtuple("SavedAction", ["log_prob", "value"])
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
env = gym.make(
    "CartPole-v1", render_mode="human"
)  # We make the Cartpole environment here
state_size = env.observation_space.shape[0]
action_size = env.action_space.n
print(f"Action space: {env.action_space}")
print(f"Observation space: {env.observation_space}")
print(f"There are {action_size} actions")


class Actor(torch.nn.Module):
    def __init__(self, state_size, action_size):
        super(Actor, self).__init__()
        self.state_size = state_size
        self.action_size = action_size
        self.linear1 = torch.nn.Linear(self.state_size, 128)
        self.linear2 = torch.nn.Linear(128, 256)
        self.linear3 = torch.nn.Linear(256, self.action_size)

    def forward(self, state):
        output = F.relu(self.linear1(state))
        output = F.relu(self.linear2(output))
        output = self.linear3(output)
        distribution = torch.distributions.Categorical(F.softmax(output, dim=-1))
        return distribution


class Critic(torch.nn.Module):
    def __init__(self, state_size, action_size):
        super(Critic, self).__init__()
        self.state_size = state_size
        self.action_size = action_size
        self.linear1 = torch.nn.Linear(self.state_size, 128)
        self.linear2 = torch.nn.Linear(128, 256)
        self.linear3 = torch.nn.Linear(256, 1)

    def forward(self, state):
        output = F.relu(self.linear1(state))
        output = F.relu(self.linear2(output))
        value = self.linear3(output)
        return value


def discounted_rewards(next_value, rewards, masks, gamma=0.99):
    """计算折扣奖励"""

    R = next_value
    returns = []
    for step in reversed(range(len(rewards))):
        R = rewards[step] + gamma * R * masks[step]
        returns.insert(0, R)
    return returns


def run_episode(actor:Actor, critic:Critic, n_iters:int):
    optimizerA = torch.optim.Adam(actor.parameters())
    optimizerC = torch.optim.Adam(critic.parameters())
    for iter in range(n_iters):
        # 重置环境，开始新一轮的游戏
        state, _ = env.reset()

        log_probs = [] # 保存这一轮游戏中，每个 action 的对数概率

        values = []# 保存这一轮游戏中，各个 state 下的回报估值

        rewards = []# 保存这一轮游戏中，各个 state 下奖励
        masks = []
        entropy = 0 # 好像没用

        for i in count():
            # 在每个游戏步骤中，渲染当前状态
            env.render()
            # 将状态转换为张量
            state = torch.FloatTensor(state).to(device)
            # 通过 Actor 和 Critic 模型获取动作的概率分布和状态的回报估值。
            dist, value = actor(state), critic(state)
            # 随机选择一个 action
            action = dist.sample()
            # 从概率分布中采样一个动作，执行该动作，并获得下一个状态、奖励等信息。
            next_state, reward, done, _, _ = env.step(action.cpu().numpy())

            # 计算 action 的对数概率
            log_prob = dist.log_prob(action).unsqueeze(0)
            entropy += dist.entropy().mean() # 这个熵实际并未使用

            log_probs.append(log_prob)
            values.append(value)
            rewards.append(torch.tensor([reward], dtype=torch.float, device=device))
            masks.append(torch.tensor([1 - done], dtype=torch.float, device=device))

            state = next_state

            if done:
                print("Iteration: {}, Score: {}".format(iter, i))
                break

        next_state = torch.FloatTensor(next_state).to(device)
        next_value = critic(next_state)
        # 使用折扣回报函数计算每个状态的折扣奖励。
        returns = discounted_rewards(next_value, rewards, masks)

        log_probs = torch.cat(log_probs)
        returns = torch.cat(returns).detach()
        values = torch.cat(values)

        # 计算优势函数（advantage）和策略梯度损失（actor_loss）
        advantage = returns - values
        actor_loss = -(log_probs * advantage.detach()).mean()
        # 计算值函数损失（critic_loss）
        critic_loss = advantage.pow(2).mean()

        # 清零优化器的梯度，计算并更新 Actor 和 Critic 的参数。
        optimizerA.zero_grad()
        optimizerC.zero_grad()
        actor_loss.backward()
        critic_loss.backward()
        optimizerA.step()
        optimizerC.step()

# 构建一个神经网络 model 作为actor
actor = Actor(state_size, action_size).to(device)
# 构建一个神经网络 model 作为 critic
critic = Critic(state_size, action_size).to(device)
run_episode(actor, critic, n_iters=1000)

env.close()
