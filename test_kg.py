import numpy as np 
import random
from kg import KnowledgeGradient

# Hidden Bernoulli dists per arm
dists = [.4, .5, .8]

# KG parameters
n_arms = 3
T = 100

kg_ins = KnowledgeGradient(n_arms, T)

# First arm is random
k = random.choice(range(n_arms))
for t in range(T):
	reward = 1 if random.random() < dists[k] else 0
	print("{}  Chose arm {}. Observed reward {}".format(t, k, reward))
	k = kg_ins.observe_and_choose(k, reward)
