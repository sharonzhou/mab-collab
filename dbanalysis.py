import os, random, csv
from urllib import parse
import psycopg2
import psycopg2.extras
import numpy as np
from kg import KnowledgeGradient
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
		for u in range(self.num_workers):
			for g in range(self.num_games):
				kg = KnowledgeGradient(self.num_arms, self.num_trials)
				for t in range(self.num_trials):
					k_human = int(self.human_actions[u, g, t])
					k_robot = kg.choose()
					self.kg_agreement[u, g, t] = k_human == k_robot
					self.kg_actions[u, g, t] = k_robot
					r = self.rewards[u, g, t]
					kg.observe(k, r)
