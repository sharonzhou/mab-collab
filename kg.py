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
		self.successes = np.zeros(n_arms)
		self.failures = np.zeros(n_arms)

		# from eval (pg 5) of paper
		self.prior_alpha = 2
		self.prior_beta = 2
		self.priors = np.array([self._beta(self.prior_alpha, self.prior_beta) for _ in range(n_arms)])
		self.gamma = self._beta(self.prior_alpha, self.prior_beta)
		self.thetas = self.priors
		self.q = self._beta(1, 1) * self.priors
	
	# Estimates updated reward rates + posterior probability distributions, after arm k is pulled with reward r
	def _estimate(self, q, thetas, successes, failures, k, r, priors, gamma):
		successes[k] += r
		failures[k] += 1 - r
		thetas[k] = thetas[k] + (1. / (successes[k] + failures[k])) * (r - thetas[k])

		pr_observation = self._beta(successes + 1, failures + 1)
		pr_prior = gamma * q + (1. - gamma) * priors
		q = pr_observation * pr_prior
		q /= np.sum(q)

		return thetas, np.array(q)

	def _beta(self, alpha, beta):
		return np.true_divide(alpha, alpha + beta)

	def observe_and_choose(self, k, reward):
		self.t += 1		

		# Observe reward
		self.thetas, self.q = self._estimate(self.q, self.thetas, \
			self.successes, self.failures, k, reward, self.priors, self.gamma)

		# Choose next arm
		expectations = np.zeros(self.n_arms)
		for k in range(self.n_arms):
			# Hypothetical success
			thetas_success, q_success = self._estimate(self.q, self.thetas, \
				self.successes, self.failures, k, 1, self.priors, self.gamma)
			
			# Hypothetical failure
			thetas_failure, q_failure = self._estimate(self.q, self.thetas, \
				self.successes, self.failures, k, 0, self.priors, self.gamma)

			# Expectation of success + failure
			expectations[k] = np.sum(q_success * thetas_success + q_failure * thetas_failure)

		# Take max over all arms (removed independent term in gradient)
		decisions = self.thetas + (self.T - self.t - 1) * np.amax(expectations)
		return np.argmax(decisions)


































