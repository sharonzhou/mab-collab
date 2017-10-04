import numpy as np 
import random
from kg import KnowledgeGradient

# Real reward rates
reward_rates = [.4, .5, .8]

# KG parameters
n_arms = 3
T = 100

kg_ins = KnowledgeGradient(n_arms, T)

# First arm is random
k = random.choice(range(n_arms))
for t in range(T):
	print(k)
	reward = 1 if random.random() < reward_rates[k] else 0
	print("{}  Chose arm {}. Observed reward {}".format(t, k, reward))
	k = kg_ins.choose_and_observe(k, reward)
