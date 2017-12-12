import numpy as np 
import random
from collaborative_model import CollaborativeModel
from constant import *

# experimental_condition = "control"
experimental_condition = "partial"
# experimental_condition = "partial_asymmetric"
p1 = 0 
p2 = 1
num_games = 1 #20
T = 15
thetas = reward_rates
n_arms = 4

p1_observability = observability_probabilities[experimental_condition][p1]
p2_observability = observability_probabilities[experimental_condition][p2]

next_turn = p1
for g in range(num_games):
	p1_model = CollaborativeModel(n_arms=n_arms, T=T, my_observability=p1_observability, partner_observability=p2_observability)
	p2_model = CollaborativeModel(n_arms=n_arms, T=T, my_observability=p2_observability, partner_observability=p1_observability)
	for t in range(T):
		if next_turn == p1:
			k = p1_model.choose()
		else:
			k = p2_model.choose()
		reward = 1 if random.random() < thetas[g][k] else 0
		
		p1_observed = experimental_conditions[experimental_condition][p1][g][t]
		p2_observed = experimental_conditions[experimental_condition][p2][g][t]
		
		if p1_observed == False:
			p1_model.observe(k, None, p2_observed)
		elif p1_observed == True:
			p1_model.observe(k, reward, p2_observed)
		
		if p2_observed == False:
			p2_model.observe(k, None, p1_observed)
		elif p2_observed == True:
			p2_model.observe(k, reward, p1_observed)
		
		if next_turn == 0:
			print("p1 decision {}, exploit {}, my info gain {}, partner info gain {}, decisions {}".format(p1_model.decision, p1_model.decision_exploit, p1_model.decision_information_gain, p1_model.decision_information_gain_partner, p1_model.decisions))
		elif next_turn == 1:
			print("p2 decision {}, exploit {}, my info gain {}, partner info gain {}, decisions {}".format(p2_model.decision, p2_model.decision_exploit, p2_model.decision_information_gain, p2_model.decision_information_gain_partner, p2_model.decisions))
		print("{}  p{} chose arm {}: reward {}. p1 observed? {}. p2 observed? {}".format(t, next_turn + 1, k, reward, "yes" if p1_observed == 1 else "no", "yes" if p2_observed == 1 else "no"))
		next_turn = p1 if next_turn == p2 else p2
