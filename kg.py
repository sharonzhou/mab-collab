import numpy as np 
import random
from beta import Beta

"""
Knowledge Gradient: from forgetful Bayes and myopic planning
		parameterized by int: n_arms, the number of arms; int: T, finite time horizon
"""
class KnowledgeGradient:
	def __init__(self, n_arms, T):
		self.T = T
		self.t = 1
		self.n_arms = n_arms
		self.n_pulls = np.zeros(n_arms)
		self.successes = np.zeros(n_arms)
		self.failures = np.zeros(n_arms)

		# from eval (pg 5) of paper
		self.prior_alpha = 2
		self.prior_beta = 2
		self.priors = np.array([Beta(self.prior_alpha, self.prior_beta) for _ in range(n_arms)])
		self.gamma = Beta(self.prior_alpha, self.prior_beta).compute()
		self.thetas = np.array([prior.compute() for prior in self.priors])
		self.q = self.prior
		# self.states = [[s] for s in self.q]

	def observe_reward(self, k, reward):
		self.t += 1
		self.n_pulls += 1
		self.successes[k] += reward
		self.failures[k] += 1 - reward
		
		# Update estimated reward rate for arm k
		self.thetas[k] = self.thetas[k] + (1. / self.n_pulls[k]) * (reward - self.thetas[k])
		# Represent as Beta dist, from which to be generated iid
		# self.thetas[k] = Beta(self.prior_alpha + self.successes[k], self.prior_beta + self.failures[k])

		# Update posteriors
		# pr_observation = self.thetas**self.successes * (1-self.thetas)**self.failures
		pr_observation = Beta(self.successes + 1, self.failures + 1)
		pr_prior = gamma * self.q + (1 - gamma) * self.priors
		self.q = pr_observation * pr_prior
		self.q /= np.sum(self.q)
		return 

	def choose_arm(self):
		n = self.successes + self.failures
		p = np.true_divide(self.successes, n)
		variance = n * p * (1 - p)
		gradients = p + variance - np.amax(self.thetas)
		decisions = self.thetas + (self.T - self.t - 1) * gradients 
		return np.argmax(decisions)


































