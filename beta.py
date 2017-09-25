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

	def __str__(self):
		return "Beta(" + str(self.alpha) + ", " + str(self.beta)

	def __mul__(self, other):
		return self.compute() * other

	def __add__(self, other):
		return self.compute() + other

	def __truediv__(self, other):
		return self.compute() / float(other)

	def update(self, alpha=None, beta=None):
		if alpha:
			self.alpha = alpha
		if beta:
			self.beta = beta
		return
	
	def compute(self):
		# approximation
		n = 1000000000.
		p = self.alpha / self.alpha + self.beta
		return np.random.binomial(n, p) / n

class Mul:
	def __init__(self, x, y):
		self.x = x
		self.y = y

	def compute(self):
		return x * y

class Add:
	def __init__(self, x, y):
		self.x = x
		self.y = y

	def compute(self):
		return x + y

class Div:
	def __init__(self, x, y):
		self.x = x
		self.y = y

	def compute(self):
		return x / y	
