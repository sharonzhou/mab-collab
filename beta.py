import numpy as np 
import random

"""
Beta: stores a beta coefficient as an object
	parameterized by int: alpha, int: beta
"""
class Beta:
	def __init__(self, alpha, beta):
		self.alpha = alpha
		self.beta = beta

	def update(self, alpha=None, beta=None):
		if alpha:
			self.alpha = alpha
		if beta:
			self.beta = beta
		return

	def function(self, function, other):
		# TODO: allow functions to interact with this object (necessary?)
		return function(self)
	
	def compute(self):
		return np.random.beta(alpha, beta)