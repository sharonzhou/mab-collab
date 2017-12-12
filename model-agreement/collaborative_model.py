import numpy as np 
import random, math

"""
Collaborative Model
"""
class CollaborativeModel:
	def __init__(self, n_arms=4, T=15, alpha=.65, beta=1.05, my_observability=1, partner_observability=1):
		# Time horizon and time step
		self.T = T
		self.t = 1
		
		# Arms and historical reward rate
		self.n_arms = n_arms
		self.chosen_count = np.zeros((n_arms))
		self.success_count = np.zeros((n_arms))

		# Observability and observability counts
		self.my_observability = my_observability
		self.partner_observability = partner_observability
		self.reward_observability_count = np.zeros((n_arms))
		self.reward_observability_partner_count = np.zeros((n_arms))
		self.reward_observability_both_count = np.zeros((n_arms))

		# My belief
		self.prior_alpha = alpha
		self.prior_beta = beta
		self.prior = np.array([self._discretize_beta_pdf(self.prior_alpha, self.prior_beta) for _ in range(n_arms)])
		self.q = np.copy(self.prior)

		# Model of partner's belief
		self.A_partner = np.zeros((n_arms, T + 1))

		# Real decision and hypothetical decisions made if purely exploiting, 
		# 	purely exploring for own info gain, purely exploring for partner's info gain (for analysis)
		self.decisions = None
		self.decision = None
		self.decision_exploit = None
		self.decision_information_gain = None
		self.decision_information_gain_partner = None

	# Discretizes Beta dist into its pdf with support [0,1], normalized to integrate to 1
	def _discretize_beta_pdf(self, alpha, beta):
		x = [i / 100. for i in range(101)]
		pdf = [0 if i == 0. or i == 1. else i**(alpha - 1.) * (1. - i)**(beta - 1.) for i in x]
		pdf = [i / sum(pdf) for i in pdf]
		return pdf

	# Performs n choose x
	def _n_choose_x(self, n, x):
		f = math.factorial
		return f(n) / f(x) / f(n-x)

	# Updates my belief (retains original copy for calculating hypothetical updates)
	# 		my_hypothetical_observability: value of observability, varying for hypothetical updates on non-control conditions only 
	def _update_my_belief(self, belief, k, r, prior, my_hypothetical_observability=1):
		q = np.copy(belief)
		pr_observation = np.ones((self.n_arms, 101))
		pr_observation[k] = [i / 100. if r else 1 - i / 100. for i in range(101)]
		q = pr_observation * prior * my_hypothetical_observability
		q = (q.T / np.sum(q, axis=1)).T
		return q

	# Updates an estimated model of partner's belief (retains original copy for calculating hypothetical updates)
	def _update_partner_belief(self, A_partner, success_count, reward_observability_count, reward_observability_partner_count):
		# Copy of matrix of partner's belief
		A_partner = np.copy(A_partner)
		thetas = np.zeros((self.n_arms))
		if 0 not in reward_observability_count:
			thetas = np.true_divide(success_count, reward_observability_count)

		for k in range(self.n_arms):
			for i in range(int(reward_observability_partner_count[k])):
				pdf_binomial = self._n_choose_x(reward_observability_partner_count[k], i) * thetas[k]**i \
								* (1 - thetas[k])**(reward_observability_partner_count[k] - i)
				A_partner[k, i] = sum(self.q[k] * pdf_binomial)
		return A_partner

	# Estimates hypothetical future model of partner's belief 
	def _update_hypothetical_partner_belief(self, k, A_partner_k, success_count_k, reward_observability_count_k, reward_observability_partner_count_k, partner_hypothetical_observability):
		A_partner_k = np.copy(A_partner_k)
		theta_k = 0
		if reward_observability_count_k != 0:
			theta_k = float(success_count_k) / float(reward_observability_count_k)

		for i in range(int(reward_observability_partner_count_k)):
			pdf_binomial = self._n_choose_x(reward_observability_partner_count_k, i) * theta_k**i \
							* (1 - theta_k)**(reward_observability_partner_count_k - i)
			A_partner_k[i] = sum(self.q[k] * pdf_binomial)
		return A_partner_k * partner_hypothetical_observability

	# Observe reward r on arm k, and update belief
	def observe(self, k, r, partner_observed):
		self.chosen_count[k] += 1
		if partner_observed:
			self.reward_observability_partner_count[k] += 1

		# If you can observe reward
		if r is not None:
			self.reward_observability_count[k] += 1
			if r == 1:
				self.success_count[k] += 1
			if partner_observed:
				self.reward_observability_both_count[k] += 1
			self.q = self._update_my_belief(self.q, k, r, self.prior)

		self.t += 1

	def choose(self): 
		# Update model of partner's belief (could do this in observe(), but want to reduce computing this 2x -> 1x every 2 rounds)
		self.A_partner = self._update_partner_belief(self.A_partner, self.success_count, self.reward_observability_count, self.reward_observability_partner_count)

		# Information gain
		information_gain = np.zeros((self.n_arms))
		information_gain_partner = np.zeros((self.n_arms))
		for k in range(self.n_arms):
			# Expected reward rates
			expectation = sum([self.q[k, i] * i / 100. for i in range(101)])
			expectation_partner = sum(self.A_partner[k]) / len(self.A_partner[k]) 

			# Hypothetical success
			q_success = self._update_my_belief(self.q, k, 1, self.prior, my_hypothetical_observability=self.my_observability)
			# Both agents have a probability of observability, here added to the hypothetical counts as probabilities
			A_success_partner = self._update_hypothetical_partner_belief(k, self.A_partner[k], self.success_count[k] + 1, self.reward_observability_count[k] + 1, self.reward_observability_partner_count[k] + 1, self.partner_observability)

			# Hypothetical failure
			q_failure = self._update_my_belief(self.q, k, 0, self.prior, my_hypothetical_observability=self.my_observability)
			# Again: Both agents have a probability of observability, here added to the hypothetical counts as probabilities
			A_failure_partner = self._update_hypothetical_partner_belief(k, self.A_partner[k], self.success_count[k], self.reward_observability_count[k] + 1, self.reward_observability_partner_count[k] + 1, self.partner_observability)

			# Max exploitative value
			max_expected_success = np.max([sum([q_success[kk, i] * i / 100. for i in range(101)]) \
									for kk in range(self.n_arms)])
			max_expected_failure = np.max([sum([q_failure[kk, i] * i / 100. for i in range(101)]) \
									for kk in range(self.n_arms)])
			information_gain[k] = np.max(max_expected_success * expectation + max_expected_failure * (1 - expectation))

			max_expected_success_partner = np.array(list(np.max(A_success_partner[kk] for kk in range(self.n_arms))))
			max_expected_failure_partner = np.array(list(np.max(A_failure_partner[kk] for kk in range(self.n_arms))))
			information_gain_partner[k] = np.max(max_expected_success_partner * expectation_partner \
								+ max_expected_failure_partner * (1 - expectation_partner))
		# Take max of expected value now + my info gain + partner's info gain over all arms
		decisions = np.array([sum([self.q[k, i] * i / 100. for i in range(101)]) for k in range(self.n_arms)]) \
						+ math.ceil((self.T - self.t - 1) / 2.) * information_gain \
						+ math.floor((self.T - self.t - 1) / 2.) * information_gain_partner
		self.decisions = decisions
		self.decision = np.argmax(decisions)

		# Decisions if exploiting, purely gaining info for self, and purely gaining info for partner (for analysis)
		self.decision_exploit = np.argmax(np.array([sum([self.q[k, i] * i / 100. for i in range(101)]) for k in range(self.n_arms)]))
		self.decision_information_gain = np.argmax(information_gain)
		self.decision_information_gain_partner = np.argmax(information_gain_partner)

		# Choose next arm
		return self.decision

