import numpy as np 
import random, csv
from kg import KnowledgeGradient
from constant import *

num_arms = 4
num_games = 20
num_trials = 15
num_iters = 10000

probabilities = np.zeros((num_games, num_trials, num_arms))


for i in range(num_iters):
	for g in range(num_games):
		kg_ins = KnowledgeGradient(num_arms, num_trials)
		thetas = reward_rates[g]
		for t in range(num_trials):
			k = kg_ins.choose()
			probabilities[g, t, k] += 1
			r = 1 if random.random() < thetas[k] else 0
			kg_ins.observe(k, r)
	if i % 500 == 0:
		with open("kg_probs_{}.csv".format(str(i)), "w") as f:
			writer = csv.writer(f)
			writer.writerows(probabilities / (i + 1))
		print(i)
