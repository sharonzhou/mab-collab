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
		self.thetas = np.array([np.random.beta(self.prior_alpha, self.prior_beta) for _ in range(n_arms)])
		self.q = np.array([self._discretize_beta_pdf(self.prior_alpha + 1, self.prior_beta + 1) for _ in range(n_arms)])
	
	# Discretizes Beta dist into its pdf with support [0,1], normalized to integrate to 1
	def _discretize_beta_pdf(self, alpha, beta):
		x = [i / 100. for i in range(101)]
		pdf = [i**(alpha - 1.) * (1. - i)**(beta - 1.) for i in x]
		pdf /= np.sum(pdf)
		return pdf

	# Estimates updated reward rates + posterior probability distributions, after arm k is pulled with reward r
	def _estimate(self, q, thetas, k, r, priors, gamma):
		# Reset thetas randomly
		if random.random() < 1 - gamma:
			thetas = np.array([np.random.beta(self.prior_alpha, self.prior_beta) for _ in range(self.n_arms)])

		pr_observation = np.ones((self.n_arms, 101))
		pr_observation[k] = [i / 100. if r else 1 - i / 100. for i in range(101)]
		pr_prior = gamma * q + (1. - gamma) * priors
		q = pr_observation * pr_prior
		q /= np.sum(q)

		return thetas, q

	def observe_and_choose(self, k, reward):
		self.t += 1		

		# Observe reward
		self.thetas, self.q = self._estimate(self.q, self.thetas, \
			k, reward, self.priors, self.gamma)

		# Choose next arm
		expectations = np.zeros(self.n_arms)
		for k in range(self.n_arms):
			# Hypothetical success
			thetas_success, q_success = self._estimate(self.q, self.thetas, \
				k, 1, self.priors, self.gamma)
			
			# Hypothetical failure
			thetas_failure, q_failure = self._estimate(self.q, self.thetas, \
				k, 0, self.priors, self.gamma)

			# Expectation of success + failure
			expectations[k] = np.sum(q_success) + np.sum(q_failure)

		# Take max over all arms (removed independent term in gradient)
		decisions = np.sum(self.q, axis=1) + (self.T - self.t - 1) * np.amax(expectations)
		return np.argmax(decisions)



