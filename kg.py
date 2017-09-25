import numpy as np 
import random
from beta import Beta, Mul

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
		self.priors = np.array([approx_beta(self.prior_alpha, self.prior_beta) for _ in range(n_arms)])
		self.gamma = approx_beta(self.prior_alpha, self.prior_beta)
		self.thetas = self.priors
		self.q = None

	def approx_beta(self, alpha, beta):
		n = 1000000000.
		p = float(alpha) / float(alpha + beta)
		return np.random.binomial(n, p) / n

	def observe_reward(self, k, reward):
		self.t += 1
		self.n_pulls += 1
		self.successes[k] += reward
		self.failures[k] += 1 - reward
		
		# Update estimated reward rate for arm k
		self.thetas[k] = self.thetas[k] + (1. / self.n_pulls[k]) * (reward - self.thetas[k])

		# Update posteriors
		pr_observation = approx_beta(self.successes + 1, self.failures + 1)
		pr_prior = gamma * self.q + (1. - gamma) * self.priors
		self.q = pr_observation * pr_prior
		self.q /= np.sum(self.q)
		return 

	def choose_arm(self):
		# TODO: expectation over hypothetical t+1 (0 or 1) for each arm, how each affects all qs (or E(\theta_k^t))
		# take mean of random var qs w/ integral
		# take max of these means over all arms
		# Q: can't you just take the theta with the highest E(theta^t)? as exploit
		n = self.successes + self.failures
		p = np.true_divide(self.successes, n)
		variance = n * p * (1 - p)
		gradients = p + variance - np.amax(self.thetas)
		decisions = self.thetas + (self.T - self.t - 1) * gradients 
		return np.argmax(decisions)


































