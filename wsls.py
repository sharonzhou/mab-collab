import random

class WSLS:
	def __init__(self, n_arms):
		self.n_arms = n_arms
		self.next_arm = random.choice(range(n_arms))

	def observe(self, k, r):
		if r == 1:
			self.next_arm = k
		else:
			while self.next_arm == k:
				self.next_arm = random.choice(range(self.n_arms))

	def choose(self): 
		return self.next_arm
