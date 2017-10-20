import os, random, csv, itertools
from urllib import parse
import psycopg2
import psycopg2.extras
import numpy as np
from kg import KnowledgeGradient
from greedy import Greedy
from wsls import WSLS
from constant import *

class Analysis:
	def __init__(self, db_url):
		self.db_url = db_url

		conn = psycopg2.connect(
		    database=db_url.path[1:],
		    user=db_url.username,
		    password=db_url.password,
		    host=db_url.hostname,
		    port=db_url.port
		)

		cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

		query = "select * from move;"
		cursor.execute(query)
		moves = cursor.fetchall()

		query = "select * from worker;"
		cursor.execute(query)
		workers = cursor.fetchall()

		self.valid_worker_ids = [w[0] for w in workers if w[1] and w[1] != "testing"]
		self.num_workers = len(self.valid_worker_ids)
		self.worker_id_mapping = { w: i for i, w in enumerate(self.valid_worker_ids)}

		self.num_games = 20
		self.num_trials = 15
		self.num_arms = 4
		self.num_rewards = 2
		self.human_actions = np.zeros((self.num_workers, self.num_games, self.num_trials))
		self.rewards = np.zeros((self.num_workers, self.num_games, self.num_trials))

		# Get valid moves
		history = []
		for m in moves:
			u = m[1]
			if u not in self.valid_worker_ids:
				continue
			k = m[2]
			t = m[3] - 1
			g = m[4] - 1
			r = m[5]

			# Remove duplicates	
			h = [u, t, g]
			if history and h in history:
				continue
			history.append(h)

			# Counter
			w = self.worker_id_mapping[u]
			self.human_actions[w, g, t] = k
			self.rewards[w, g, t] = r

		# Compute per trial model agreement
		# TODO: optimization / hyperparam tuning
		self.kg_agreement = np.zeros((self.num_workers, self.num_games, self.num_trials))
		self.kg_actions = np.zeros((self.num_workers, self.num_games, self.num_trials))

		self.greedy_agreement = np.zeros((self.num_workers, self.num_games, self.num_trials))
		self.greedy_actions = np.zeros((self.num_workers, self.num_games, self.num_trials))
		self.e = .1

		self.wsls_agreement = np.zeros((self.num_workers, self.num_games, self.num_trials))
		self.wsls_actions = np.zeros((self.num_workers, self.num_games, self.num_trials))

	def compute_kg(self, interface=None):
		alphas = [.25, .5, .75, 1., 1.25, 1.5, 1.75, 2.]
		betas = [.25, .5, .75, 1., 1.25, 1.5, 1.75, 2.]
		gammas = [.1, .2, .3, .4, .5, .6, .7, .8, .9, 1.]
		best_params = [[] for _ in range(self.num_workers)]
		history = [{} for _ in range(self.num_workers)]
		print("interface is ", interface)
		if interface == "single":
			best_params = [[0.25, 2.0, 1.0], [0.25, 2.0, 0.9], [0.25, 1.25, 1.0], \
			[0.25, 1.25, 1.0], [0.25, 2.0, 1.0], [0.25, 1.75, 0.4], [0.5, 1.75, 1.0]]
		elif interface == "single_bars":
			best_params = [[0.25, 2.0, 1.0], [0.25, 2.0, 0.4], [0.25, 1.5, 1.0], \
			[0.25, 1.0, 1.0], [0.25, 0.5, 1.0], [0.25, 2.0, 1.0]]
		for u in range(self.num_workers):
			if best_params[u]:
				alpha, beta, gamma = best_params[u]
				for g in range(self.num_games):
					kg = KnowledgeGradient(self.num_arms, self.num_trials, \
						alpha=alpha, beta=beta, gamma=gamma)
					for t in range(self.num_trials):
						k_human = int(self.human_actions[u, g, t])

						k_kg = kg.choose()
						self.kg_agreement[u, g, t] = k_human == k_kg
						self.kg_actions[u, g, t] = k_kg

						r = self.rewards[u, g, t]
						kg.observe(k_human, r)
				print("Best param retrieved for user {} is {}".format(u, best_params[u]))
				continue
			best_aggregate_agreement = None
			for alpha, beta, gamma in itertools.product(alphas, betas, gammas):
				tmp_params = [alpha, beta, gamma]
				tmp_agreement = np.zeros((self.num_games, self.num_trials))
				tmp_actions = np.zeros((self.num_games, self.num_trials))
				for g in range(self.num_games):
					kg = KnowledgeGradient(self.num_arms, self.num_trials, \
						alpha=alpha, beta=beta, gamma=gamma)
					for t in range(self.num_trials):
						k_human = int(self.human_actions[u, g, t])

						k_kg = kg.choose()
						tmp_agreement[g, t] = k_human == k_kg
						tmp_actions[g, t] = k_kg

						r = self.rewards[u, g, t]
						kg.observe(k_human, r)
				# Check best
				aggregate_agreement = np.sum(tmp_agreement)
				if aggregate_agreement not in history[u]:
					history[u][aggregate_agreement] = []
				history[u][aggregate_agreement].append(tmp_params)
				print(u, "Found aggregate_agreement as: ", aggregate_agreement, " with params a b g as ", tmp_params)
				if best_aggregate_agreement is None or aggregate_agreement > best_aggregate_agreement:
					print(u, "Found new BEST aggregate_agreement: ", aggregate_agreement, " with params a b g as ", tmp_params)
					best_aggregate_agreement = aggregate_agreement
					best_params[u] = tmp_params
					self.kg_agreement[u] = tmp_agreement
					self.kg_actions[u] = tmp_actions
			print("history so far ", history)
			print("all best params for users so far: {}".format(best_params))
			print("best params found for user {} is {}".format(u, best_params[u]))
		print("final history of params ", history)
		print("final best params for users ", best_params)
		return self.kg_actions, self.kg_agreement

	def compute_greedy(self):
		epsilons = [.01, .025, .05, .1, .25, .5]
		best_params = [None for _ in range(self.num_workers)]
		history = [{} for _ in range(self.num_workers)]
		for u in range(self.num_workers):
			best_aggregate_agreement = None
			for e in epsilons:
				tmp_agreement = np.zeros((self.num_games, self.num_trials))
				tmp_actions = np.zeros((self.num_games, self.num_trials))
				for g in range(self.num_games):
					greedy = Greedy(self.num_arms, e)
					for t in range(self.num_trials):
						k_human = int(self.human_actions[u, g, t])

						k_greedy = greedy.choose()
						tmp_agreement[g, t] = k_human == k_greedy
						tmp_actions[g, t] = k_greedy

						r = self.rewards[u, g, t]
						greedy.observe(k_human, r)
				aggregate_agreement = np.sum(tmp_agreement)
				if aggregate_agreement not in history[u]:
					history[u][aggregate_agreement] = []
				history[u][aggregate_agreement].append(e)
				print(u, "Found aggregate_agreement as (greedy): ", aggregate_agreement, " with e as ", e)
				if best_aggregate_agreement is None or aggregate_agreement > best_aggregate_agreement:
					print(u, "Found new BEST aggregate_agreement (greedy): ", aggregate_agreement, " with e as ", e)
					best_aggregate_agreement = aggregate_agreement
					best_params[u] = e
					self.greedy_agreement[u] = tmp_agreement
					self.greedy_actions[u] = tmp_actions
			print("greedy: history so far ", history)
			print("greedy: all best e for users so far: {}".format(best_params))
			print("greedy: best e found for user {} is {}".format(u, best_params[u]))
		print("greedy: final history of e ", history)
		print("greedy: final best e for users ", best_params)				
		return self.greedy_actions, self.greedy_agreement
	
	def compute_wsls(self):
		for u in range(self.num_workers):
			for g in range(self.num_games):
				wsls = WSLS(self.num_arms)
				for t in range(self.num_trials):
					k_human = int(self.human_actions[u, g, t])

					k_wsls = wsls.choose()
					self.wsls_agreement[u, g, t] = k_human == k_wsls
					self.wsls_actions[u, g, t] = k_wsls

					r = self.rewards[u, g, t]
					wsls.observe(k_human, r)
		return self.wsls_actions, self.wsls_agreement
