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
		print("this is a max ", argmaxes)

		if random.random() < self.e:
			print("returning a random one!")
			all_arms = [i for i in range(self.n_arms)]
			argmaxes.reverse()
			valid_arms = [all_arms.pop(i) for i in argmaxes]
			if not valid_arms:
				k = random.choice(range(self.n_arms))
			else:
				k = random.choice(valid_arms)
			print(k)
			return k
		else:
			k = random.choice(argmaxes)
			print("not random ", k)
			return k


