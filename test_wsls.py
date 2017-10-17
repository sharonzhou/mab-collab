import numpy as np 
import random
from wsls import WSLS

n_arms = 3
wsls = WSLS(n_arms)

thetas = [np.random.beta(2,2) for _ in range(n_arms)]
T = 100
for t in range(T):
	k = wsls.choose()
	reward = 1 if random.random() < thetas[k] else 0
	print("{}  Chose arm {}. Observed reward {}".format(t, k, reward))
	wsls.observe(k, reward)
