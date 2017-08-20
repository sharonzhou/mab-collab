import numpy as np 
import random, math

class Bandit:
	def __init__(self, n_arms, mus=None, sigmas=None):
		self.t = 1
		self.n_arms = n_arms

		# Create random dists per arm
		self.mus = [random.random() for _ in range(n_arms)] if mus is None else mus
		self.sigmas = [random.random() for _ in range(n_arms)] if sigmas is None else sigmas

		# For the agent
		self.alphas = [1] * n_arms
		self.betas = [1] * n_arms
		uniform_prior = 1.0 / n_arms
		self.thetas = [uniform_prior] * n_arms
		self.reward_history = []

	# Human pulls an arm and observes a reward (+ agent updates posterior)
	def pull_arm(self, arm):
		self.t += 1
		reward = np.random.normal(self.mus[arm], self.sigmas[arm])
		reward = int(reward * 100) / 100.0
		print(reward)

		# Update agent's Bayesian posterior (normalized)
		self.reward_history.append(reward)
		# Normalize reward to nonneg vals [0, 1] for binomial p 
		reward_range = max(self.reward_history) - min(self.reward_history)
		if reward_range != 0:
			normalized_reward = (reward - min(self.reward_history)) / reward_range 
		else:
			normalized_reward = 0.5
		reward_update = np.random.binomial(1, normalized_reward)
		self.alphas[arm] += reward_update
		self.betas[arm] += 1 - reward_update
		self.thetas = [random.betavariate(self.alphas[i] + 1, self.betas[i] + 1) for i in range(len(self.alphas))]
		self.thetas = [i / sum(self.thetas) for i in self.thetas]		

		return reward

	# Agent's estimate
	def estimate(self):
		return self.thetas

def test_bandit():
	n_arms = 3
	bandit = Bandit(n_arms)

	num_rounds = 16
	history = { "human": [], "agent": [], "reasons": [], "rewards": [], "cumulative_reward": 0, "agent_cumulative_reward": 0 }
	cumulative_reward = 0

	# Instructions
	print("There are {} arms to pull, each with a different distribution of rewards. You want to maximize your rewards.".format(n_arms))

	for _ in range(num_rounds):
		print("Round {}...".format(bandit.t))

		# Agent's estimate
		thetas = bandit.estimate()
		agent_arm = np.argmax(thetas)

		player = "1" if bandit.t % 2 == 1 else "2"
		# Ask player 1 to pull an arm (+ give reason) 
		arm = input("Player {}: Which arm do you pull (type one of the following numbers): {}?  ".format(player, [i for i in range(n_arms)]))
		while arm not in [str(i) for i in range(n_arms)]:
			arm = input("Player {}: That's not one of the options. Which arm do you pull (type one of the following numbers): {}?  ".format(player, [i for i in range(n_arms)]))
		reason = input("Player {}: Why did you pull that arm?  ".format(player))
		reward = bandit.pull_arm(int(arm))
		cumulative_reward += reward
		print("You got this reward: {}. Your total reward: {}".format(int(reward * 100), int(cumulative_reward * 100)))
		
		# Update history
		history["agent"].append(agent_arm)
		history["human"].append(arm)
		history["reasons"].append(reason)
		history["rewards"].append(reward)
	
	history["cumulative_reward"] = cumulative_reward

	# Agent alone
	bandit_resim = Bandit(n_arms, mus=bandit.mus, sigmas=bandit.sigmas)
	agent_cumulative_reward = 0
	for _ in range(num_rounds):
		thetas = bandit_resim.estimate()
		agent_arm = np.argmax(thetas)
		reward = bandit_resim.pull_arm(agent_arm)
		agent_cumulative_reward += reward

	print("That's it! Your joint total {} and how that compares to an agent alone {}".format(int(cumulative_reward * 100), int(agent_cumulative_reward * 100)))
	
	print("\n\nHistory: {}".format(history))

test_bandit()









