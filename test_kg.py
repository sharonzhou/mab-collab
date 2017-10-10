import numpy as np 
import random
from kg import KnowledgeGradient

n_arms = 3
thetas = [np.random.beta(2,2) for _ in range(n_arms)]
gamma = .1
T = 100

kg_ins = KnowledgeGradient(n_arms, T)

for t in range(T):
	if random.random() < gamma:
		thetas = [np.random.beta(2,2) for _ in range(n_arms)]
	k = kg_ins.choose()
	reward = 1 if random.random() < thetas[k] else 0
	print("{}  Chose arm {}. Observed reward {}".format(t, k, reward))
	kg_ins.observe(k, reward)
