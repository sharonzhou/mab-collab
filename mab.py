import numpy as np 
import random, math, os, time, csv

"""
Bandit: creates an n-armed bandit with either random or specified normal distributions,
		parameterized by mu, sigma
"""
class Bandit:
	def __init__(self, n_arms, mus=None, sigmas=None):
		self.t = 1
		self.n_arms = n_arms

		# Create random dists per arm
		self.mus = [random.random() for _ in range(n_arms)] if mus is None else mus
		self.sigmas = [random.random() for _ in range(n_arms)] if sigmas is None else sigmas

		# For the agent
		self.alphas = [1] * n_arms
		self.betas = [1] * n_arms
		uniform_prior = 1.0 / n_arms
		self.thetas = [uniform_prior] * n_arms
		self.reward_history = []

	def reset_dists(self, mus, sigmas):
		self.mus = mus
		self.sigmas = sigmas

	# Human pulls an arm and observes a reward (+ agent updates posterior)
	def pull_arm(self, arm):
		self.t += 1
		reward = np.random.normal(self.mus[arm], self.sigmas[arm])
		reward = int(reward * 100) / 100.0

		# Update agent's Bayesian posterior (normalized)
		self.reward_history.append(reward)
		# Normalize reward to nonneg vals [0, 1] for binomial p 
		reward_range = max(self.reward_history) - min(self.reward_history)
		if reward_range != 0:
			normalized_reward = (reward - min(self.reward_history)) / reward_range 
		else:
			normalized_reward = 0.5
		reward_update = np.random.binomial(1, normalized_reward)
		self.alphas[arm] += reward_update
		self.betas[arm] += 1 - reward_update
		self.thetas = [random.betavariate(self.alphas[i] + 1, self.betas[i] + 1) for i in range(len(self.alphas))]
		self.thetas = [i / sum(self.thetas) for i in self.thetas]		

		return reward

	# Agent's estimate
	def estimate(self):
		return self.thetas

def run_experiment(n_arms=3):
	# Codes for fixed parameters on practice and experiment rounds
	codes = {
		"practice": { "mus": [50, 30, 10], "sigmas": [10, 10, 30]},
		"realdeal": { "mus": [40, 70, 50], "sigmas": [35, 25, 5]}
	}

	code = input("[Optional] Please enter valid code:  ")
	if code in codes:
		bandit = Bandit(n_arms, mus=codes[code]["mus"], sigmas=codes[code]["sigmas"])
		print("Loading game with code {}...".format(code), end="\r")
	else:
		bandit = Bandit(n_arms)
		print("Loading game...", end="\r")
	time.sleep(1)

	# Get ranges within 2 std dev
	num_sigmas = 2
	ranges = []
	for (m,s) in list((zip(bandit.mus,bandit.sigmas))):
		ranges.append(m + num_sigmas * s)
		ranges.append(m - num_sigmas * s)

	num_rounds = 10
	history = { 
		"agent_decision": [], 
		"human_decision": [], 
		"active_player": [],
		"suggestions": [],
		"confidences": [],
		"reasons": [],
		"reward": [], 
		"human_cumulative_reward": 0, 
		"agent_cumulative_reward": 0 
	}
	cumulative_reward = 0

	# Instructions
	print("There are {} arms to pull, each with a different distribution of rewards ($), most (95%) of which range from {} to {}. You want to maximize your rewards as a team. You will be prompted to take turns playing arms, but you will both reveal suggestions to your partner in all rounds. \n When asked for a reason for your choice in arms, here are a few examples you could use: \n\
		 \"I chose this because it did well before\", \"it's the best\", \"haven't tried this one\", \"it was random\"".format(n_arms, min(ranges), max(ranges)))
	ready = input("Ready to begin (y/[n])?  ")
	while ready.lower() not in ["yes", "y"]:
		ready = input("Ready to begin? ")

	for _ in range(num_rounds):
		print("Round {} / {}...".format(bandit.t, num_rounds))

		# Agent's estimate
		thetas = bandit.estimate()
		agent_arm = np.argmax(thetas)

		# 1st player is active (makes the play), 2nd passive
		players = ["1", "2"]
		if bandit.t % 2 == 0:
			players.reverse()

		# Ask players to identify an arm, give confidence score, and privately give reason
		suggestions, confidences, reasons = [], [], []
		for player in players:
			suggestion = input("Player {} Suggestion: What arm do SUGGEST playing next (type one of the following numbers): {}?  ".format(player, [i for i in range(n_arms)]))
			while suggestion not in [str(i) for i in range(n_arms)]:
				suggestion = input("Player {} Suggestion: That's not one of the options. What arm do SUGGEST playing next (type one of the following numbers): {}?  ".format(player, [i for i in range(n_arms)]))
			confidence = input("Player {} Confidence: On a scale of 1 to 5, how CONFIDENT are you in this decision, with 5 being the most confident?  ".format(player))
			while confidence not in [str(i) for i in range(1,6)]:
				confidence = input("Player {} Confidence: That's not one of the options. On a scale of 1 to 5, how CONFIDENT are you in this decision?  ".format(player))
			reason_prompt = "[Private] Player {} Reason: What REASON do you suggest playing that arm? ".format(player)
			reason = input(reason_prompt)
			print("\033[A{}\033A".format("*"*(len(reason)+len(reason_prompt))))
			time.sleep(0.1)
			suggestions.append((int(player), int(suggestion)))
			confidences.append((int(player), int(confidence)))
			reasons.append((int(player), reason))

		# Ask active player to pull arm
		arm = input("Player {} Decision: It's your turn. Based on this information, what arm do decide to play (type one of the following numbers): {}?  ".format(player, [i for i in range(n_arms)]))
		while arm not in [str(i) for i in range(n_arms)]:
			arm = input("Player {} Decision: That's not one of the options. Which arm do you decide to play (type one of the following numbers): {}?  ".format(player, [i for i in range(n_arms)]))
		reward = bandit.pull_arm(int(arm))
		cumulative_reward += reward
		print("Your team got this reward: {}. Total reward: {}".format(int(reward * 100), int(cumulative_reward * 100)))
		
		# Update history
		history["agent_decision"].append(agent_arm)
		history["human_decision"].append(arm)
		history["active_player"].append(players[0])
		history["suggestions"].append(suggestions)
		history["confidences"].append(confidences)
		history["reasons"].append(reasons)
		history["reward"].append(reward)
	
	history["cumulative_reward"] = cumulative_reward

	# Agent alone
	bandit_resim = Bandit(n_arms, mus=bandit.mus, sigmas=bandit.sigmas)
	agent_cumulative_reward = 0
	for _ in range(num_rounds):
		thetas = bandit_resim.estimate()
		agent_arm = np.argmax(thetas)
		reward = bandit_resim.pull_arm(agent_arm)
		agent_cumulative_reward += reward
	history["agent_cumulative_reward"] = agent_cumulative_reward

	print("\n\nHistory: {}".format(history))
	with open("pilot_data.csv", "a") as f:
		w = csv.writer(f)
		i = 1
		for k, v in history.items():
			if "cumulative_reward" not in k:
				w.writerow([i] + [k] + v)
			i += 1
		w.writerow(["human_cumulative_reward", history["human_cumulative_reward"]])
		w.writerow(["agent_cumulative_reward", history["agent_cumulative_reward"]])

	print("That's it! Your joint total {} and how that compares to an agent alone {}".format(int(cumulative_reward * 100), int(agent_cumulative_reward * 100)))

	# @Dorsa, if you want to view the parameters, uncomment this print statement 
	# print("The distributions (mean, sd) of each arm were, from arm 0 to 2: {}".format(zip(bandit.mus, bandit.sigmas)))
	
	play_again = input("Would you like to play again (y/[n])?  ")
	if play_again in ["yes", "y"]:
		run_experiment()
	return
	
run_experiment()









