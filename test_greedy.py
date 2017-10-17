import numpy as np 
import random
from greedy import Greedy

n_arms = 3
e = .1
greedy = Greedy(n_arms, e)

thetas = [np.random.beta(2,2) for _ in range(n_arms)]
T = 100
for t in range(T):
	k = greedy.choose()
	reward = 1 if random.random() < thetas[k] else 0
	print("{}  Chose arm {}. Observed reward {}".format(t, k, reward))
	greedy.observe(k, reward)
