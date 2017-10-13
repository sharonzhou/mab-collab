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

		self.prior_alpha = 2
		self.prior_beta = 2
		self.priors = np.array([self._discretize_beta_pdf(self.prior_alpha, self.prior_beta) for _ in range(n_arms)])
		
		# NB: gamma taken empirically from paper
		self.gamma = .81 
		self.q = np.array([self._discretize_beta_pdf(self.prior_alpha, self.prior_beta) for _ in range(n_arms)])
	
	# Discretizes Beta dist into its pdf with support [0,1], normalized to integrate to 1
	def _discretize_beta_pdf(self, alpha, beta):
		x = [i / 100. for i in range(101)]
		pdf = [i**(alpha - 1.) * (1. - i)**(beta - 1.) for i in x]
		pdf /= np.sum(pdf)
		return pdf

	def _estimate(self, q_original, k, r):
		q = np.copy(q_original)
		pr_observation = np.ones((self.n_arms, 101))
		pr_observation[k] = [i / 100. if r else 1 - i / 100. for i in range(101)]
		pr_prior = self.gamma * q + (1. - self.gamma) * self.priors
		q = pr_observation * pr_prior
		q = (q.T / np.sum(q, axis=1)).T
		return q

	# Observe reward r on arm k, and update internal state
	def observe(self, k, r):
		self.q = self._estimate(self.q, k, r)
		self.t += 1

	def choose(self): 
		# Hypothetical expectations
		expectations = np.zeros(self.n_arms)
		for k in range(self.n_arms):
			# Original expected reward
			original_expectation = np.array([sum([self.q[k, i] * i / 100. for i in range(101)]) \
									for k in range(self.n_arms)])

			# Hypothetical success
			q_success = self._estimate(self.q, k, 1)
			
			# Hypothetical failure
			q_failure = self._estimate(self.q, k, 0)

			# Expectation of success + failure
			max_expected_success = np.max([sum([q_success[kk, i] * i / 100. for i in range(101)]) \
									for kk in range(self.n_arms)])
			max_expected_failure = np.max([sum([q_failure[kk, i] * i / 100. for i in range(101)]) \
									for kk in range(self.n_arms)])
			expectations[k] = np.max(max_expected_success * original_expectation \
								+ max_expected_failure * (1 - original_expectation))

		# Take max over all arms (removed independent term in gradient)
		decisions = np.array([sum([self.q[k, i] * i / 100. for i in range(101)]) \
						for k in range(self.n_arms)]) + (self.T - self.t - 1) * expectations
		
		# Choose next arm
		return np.argmax(decisions)

