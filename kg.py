import numpy as np 
import random, math, os, time, csv

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
		self.gamma = np.random(self.prior_alpha, self.prior_beta) 
		self.thetas = np.array([np.random.beta(self.prior_alpha, self.prior_beta) for _ in range(n_arms)])
		self.q = np.array([np.random.beta(self.prior_alpha, self.prior_beta) for _ in range(n_arms)])

	def observe_reward(self, k, reward):
		self.t += 1

		if reward:
			self.successes[k] += 1
		else:
			self.failures[k] += 1
		
		# calculate posteriors
		self.thetas = np.random.beta(self.prior_alpha + self.successes, self.prior_beta + self.failures)

		# update belief state
		p_reward_given_theta = self.thetas**self.successes * (1-self.thetas)**self.failures
		p_prior = gamma * self.q + (1-gamma) * self.prior
		self.q = p_reward_given_theta * p_prior # TOASK: ~???
		self.q /= np.sum(self.q)
		return 

	def choose_arm(self):
		gradients = self.q * (self.successes / self.t) - self.thetas
		decisions = self.thetas + (self.T - self.t - 1) * gradients 
		return np.argmax(decisions)

		# TOASK: Or are we taking JUST the max (asymmetric w/ maxes of q vs. thetas?)
		gradient = np.amax(self.q) - np.amax(self.thetas)
		decision = np.argmax(self.thetas) + (self.T - self.t - 1) * gradient
		return decision



































