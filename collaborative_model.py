import numpy as np 
import random, math

"""
Collaborative Trust Model
"""
class CollaborativeTrustModel:
	def __init__(self, n_arms=4, T=15, alpha=.65, beta=1.05, alpha_partner=.5, beta_partner=.5):
		# Time horizon and time step
		self.T = T
		self.t = 1
		
		# Arms and historical reward rate
		self.n_arms = n_arms
		self.chosen_count = np.zeros((n_arms))
		self.success_count = np.zeros((n_arms))

		# Observability counts
		self.seen_count = np.zeros((n_arms))
		self.seen_partner_count = np.zeros((n_arms))
		self.seen_both_count = np.zeros((n_arms))

		# My belief
		self.prior_alpha = alpha
		self.prior_beta = beta
		self.prior = [self._discretize_beta_pdf(self.prior_alpha, self.prior_beta) for _ in range(n_arms)]
		self.q = np.copy(self.prior)
	
		# Model of partner's belief
		self.prior_alpha_partner = alpha_partner
		self.prior_beta_partner = beta_partner
		self.prior_partner = [self._discretize_beta_pdf(self.prior_alpha_partner, self.prior_beta_partner) for _ in range(n_arms)]
		self.q_partner = np.copy(self.prior_partner)

	# Discretizes Beta dist into its pdf with support [0,1], normalized to integrate to 1
	def _discretize_beta_pdf(self, alpha, beta):
		x = [i / 100. for i in range(101)]
		pdf = [0 if i == 0. or i == 1. else i**(alpha - 1.) * (1. - i)**(beta - 1.) for i in x]
		pdf = [i / sum(pdf) for i in pdf]
		return pdf

	# Updates the belief (retains original copy for calculating hypothetical updates)
	def _update_belief(self, belief, k, r, prior):
		q = np.copy(belief)
		pr_observation = np.ones((self.n_arms, 101))
		pr_observation[k] = [i / 100. if r else 1 - i / 100. for i in range(101)]
		q = pr_observation * prior
		q = (q.T / np.sum(q, axis=1)).T
		return q

	# Estimate model of partner's belief
	def _estimate_partner_belief(self):
		thetas = np.zeros((self.n_arms))
		if 0 not in self.seen_count:
			thetas = np.true_divide(self.success_count, self.seen_count)
		alpha_bar = np.zeros((self.n_arms))
		beta_bar = np.zeros((self.n_arms))

		# Performs n choose x
		def n_choose_x(n, x):
			print("choose",n,x)
			f = math.factorial
			return f(n) / f(x) / f(n-x)

		for k in range(self.n_arms):
			pdf_binomial = n_choose_x(self.seen_partner_count[k], thetas[k]) \
							* thetas[k]**(thetas[k]*self.seen_partner_count[k]) \
							* (1 - thetas[k])**(self.seen_partner_count[k] - thetas[k]*self.seen_partner_count[k])
			alpha_bar[k] = sum([self.q[k, i] * i / 100. for i in range(101)]) * pdf_binomial
		beta_bar = self.seen_partner_count - alpha_bar
		
		alpha = alpha_bar + self.prior_alpha_partner
		beta = beta_bar + self.prior_beta_partner
		q_partner = self._discretize_beta_pdf(alpha, beta)
		return q_partner

	# Observe reward r on arm k, and update belief
	def observe(self, k, r, partner_observability):
		self.chosen_count[k] += 1
		if partner_observability:
			self.seen_partner_count[k] += 1

		# If you can observe reward
		if r is not None:
			self.seen_count[k] += 1
			if r == 1:
				self.success_count[k] += 1
			if partner_observability:
				self.seen_both_count[k] += 1
			self.q = self._update_belief(self.q, k, r, self.prior)

		self.t += 1

	def choose(self): 
		# Estimate/update model of partner's belief (could do this in observe(), but want to reduce computing this 2x -> 1x every 2 rounds)
		# Instead, updating the counts when observing so that this uses all historical data
		self.q_partner = self._estimate_partner_belief()

		# Information gain
		information_gain = np.zeros(self.n_arms)
		information_gain_partner = np.zeros(self.n_arms)
		for k in range(self.n_arms):
			# Expected reward rates
			expectation = sum([self.q[k, i] * i / 100. for i in range(101)])
			expectation_partner = sum([self.q_partner[k, i] * i / 100. for i in range(101)])

			# Hypothetical success
			q_success = self._update_belief(self.q, k, 1, self.priors)
			q_success_partner = self._update_belief(self.q_partner, k, 1, self.prior_partner)

			# Hypothetical failure
			q_failure = self._update_belief(self.q, k, 0, self.priors)
			q_failure_partner = self._update_belief(self.q_partner, k, 0, self.prior_partner)

			# Max exploitative value
			max_expected_success = np.max([sum([q_success[kk, i] * i / 100. for i in range(101)]) \
									for kk in range(self.n_arms)])
			max_expected_failure = np.max([sum([q_failure[kk, i] * i / 100. for i in range(101)]) \
									for kk in range(self.n_arms)])
			information_gain[k] = np.max(max_expected_success * expectation \
								+ max_expected_failure * (1 - expectation))

			max_expected_success_partner = np.max([sum([q_success_partner[kk, i] * i / 100. for i in range(101)]) \
									for kk in range(self.n_arms)])
			max_expected_failure_partner = np.max([sum([q_failure_partner[kk, i] * i / 100. for i in range(101)]) \
									for kk in range(self.n_arms)])
			information_gain_partner[k] = np.max(max_expected_success_partner * expectation_partner \
								+ max_expected_failure_partner * (1 - expectation_partner))
			# TODO/QUESTION FOR DORSA: multiply information_gain_partner[k] by the probability of bar alpha and bar beta for arm k
			# ^^ Should we do this? It might make sense to get the expected value of alpha_bar and beta_bar, as above, instead of sampling for them
			# ...and using their probabilities --- thus having w_2 (the "how much I care about partner/selflessness") actually be what affects that term)
		# Take max of expected value now + my info gain + partner's info gain over all arms
		decisions = np.array([sum([self.q[k, i] * i / 100. for i in range(101)]) for k in range(self.n_arms)]) \
						+ math.ceil((self.T - self.t - 1) / 2.) * information_gain \
						+ math.floor((self.T - self.t - 1) / 2.) * information_gain_partner
		
		# Choose next arm
		return np.argmax(decisions)

