import random

class Greedy:
	def __init__(self, n_arms, e):
		self.e = e
		self.n_arms = n_arms
		self.t = 1
		self.successes = [0 for _ in range(n_arms)]

	def observe(self, k, r):
		if r:
			self.successes[k] += 1
		self.t += 1

	def choose(self):
		thetas = [s / self.t for s in self.successes]
		if sum(thetas) != 0:
			thetas = [th / sum(thetas) for th in thetas]
		else:
			thetas = [1. / self.n_arms for _ in range(self.n_arms)]
		
		argmaxes = [i for i, x in enumerate(thetas) if x == max(thetas)]

		if random.random() < self.e:
			k = random.choice(range(self.n_arms))
			while k in argmaxes:
				k = random.choice(range(self.n_arms))
			return k
		else:
			return random.choice(argmaxes)


