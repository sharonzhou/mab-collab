import numpy as np 
import random

"""
Collaborative Trust Model
"""
class CollaborativeTrustModel:
	def __init__(self, n_arms, T, alpha=.65, beta=1.05, gamma=.81, alpha_partner=.5, beta_partner=.5, gamma_partner=.5):
		self.T = T
		self.t = 1
		
		self.n_arms = n_arms

		self.prior_alpha = alpha
		self.prior_beta = beta
		self.priors = np.array([self._discretize_beta_pdf(self.prior_alpha, self.prior_beta) for _ in range(n_arms)])
		
		self.gamma = gamma
		self.q = np.array([self._discretize_beta_pdf(self.prior_alpha, self.prior_beta) for _ in range(n_arms)])
	
		""" PARTNER """
		self.prior_alpha_partner = alpha_partner
		self.prior_beta_partner = beta_partner
		self.priors_partner = np.array([self._discretize_beta_pdf(self.prior_alpha_partner, self.prior_beta_partner) for _ in range(n_arms)])
		
		self.gamma_partner = gamma_partner
		self.nu = np.array([self._discretize_beta_pdf(self.prior_alpha_partner, self.prior_beta_partner) for _ in range(n_arms)])

		# TODO: Initialize eta and tau to 0 and update them, or have them as fixed params to fit the model? Try both? 
		self.eta = 0
		self.tau = 0

	# Discretizes Beta dist into its pdf with support [0,1], normalized to integrate to 1
	def _discretize_beta_pdf(self, alpha, beta):
		x = [i / 100. for i in range(101)]
		pdf = [i**(alpha - 1.) * (1. - i)**(beta - 1.) if i != 0 and 1. - i != 0 else 0. for i in x]
		pdf /= np.sum(pdf)
		return pdf

	def _estimate(self, q_original, k, r, priors, gamma):
		q = np.copy(q_original)
		pr_observation = np.ones((self.n_arms, 101))
		pr_observation[k] = [i / 100. if r else 1 - i / 100. for i in range(101)]
		pr_prior = gamma * q + (1. - gamma) * priors
		q = pr_observation * pr_prior
		q = (q.T / np.sum(q, axis=1)).T
		return q

	# Observe reward r on arm k, and update internal state; Used for both partner and own turns
	def observe(self, k, r, partner_observability):
		# If you can observe reward
		if r is not None:
			self.q = self._estimate(self.q, k, r, self.priors, self.gamma)
			# TODO: Increase confidence in model if you can see reward
			self.eta *= (self.t + 1) / self.t
			if partner_observability:
				self.nu = self._estimate(self.nu, k, r, self.priors_partner, self.gamma_partner)
				# TODO: Increase trust somehow as partner is perceived as more competent
				self.tau *= (self.t + 1) / self.t
			else:
				# TODO: Lower trust if partner cannot see reward (partner perceived as less competent)
				self.tau *= (self.t - 1) / self.t
		# If you cannot observe reward
		else:
			# TODO: Lower confidence in model of partner if you cannot see reward
			self.eta *= (self.t - 1) / self.t
			if partner_observability:
				# TODO: Increase trust somehow as partner is perceived as more competent
				self.tau *= (self.t + 1) / self.t
			else:
				# TODO: Lower trust if partner cannot see reward (partner perceived as less competent)
				self.tau *= (self.t - 1) / self.t
		self.t += 1

	def choose(self): 
		# Hypothetical expectations
		expectations = np.zeros(self.n_arms)
		for k in range(self.n_arms):
			# Original expected reward
			original_expectation = sum([self.q[k, i] * i / 100. for i in range(101)])

			# Hypothetical success
			nu_success = self._estimate(self.nu, k, 1, self.priors_partner, self.gamma_partner)

			# Hypothetical failure
			nu_failure = self._estimate(self.nu, k, 0, self.priors_partner, self.gamma_partner)

			# Partner's expected arm
			# TODO: Question: shouldn't the kk for max_expected_success and max_expected_failure be the same?
			max_expected_success = np.max([sum([nu_success[kk, i] * i / 100. for i in range(101)]) \
									for kk in range(self.n_arms)])
			max_expected_failure = np.max([sum([nu_failure[kk, i] * i / 100. for i in range(101)]) \
									for kk in range(self.n_arms)])
			expectations[k] = np.max(max_expected_success * original_expectation \
								+ max_expected_failure * (1 - original_expectation))

		# Take max over all arms (removed independent term in gradient)
		# decisions = np.array([sum([self.q[k, i] * i / 100. for i in range(101)]) \
		# 				for k in range(self.n_arms)]) + (self.T - self.t - 1) * expectations
		# TODO: Do we want to include time component? e.g. (self.T - self.t - 1) from KG?
		decisions = np.array([sum([self.q[k, i] * i / 100. for i in range(101)]) \
						for k in range(self.n_arms)]) + self.tau * expectations
		
		# Choose next arm
		return np.argmax(decisions)

