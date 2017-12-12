import os, random, csv, itertools
from urllib import parse
import psycopg2
import psycopg2.extras
import numpy as np
from collaborative_model import CollaborativeModel
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

		query = "select * from room;"
		cursor.execute(query)
		rooms = cursor.fetchall()

		# Valid rooms (did not dropout)
		valid_rooms = []
		for room in rooms:
			room_id = room[0]
			p1_uid = room[2]
			p2_uid = room[3]
			experimental_condition = room[19]
			scores = room[18].strip("/[/]").split(", ")
			scores = [float(score) for score in scores if score != ""]
			if not scores or len(scores) != 20:
				continue
			valid_room = { 
							"room_id": room_id, 
							"p1_uid": p1_uid, 
							"p2_uid": p2_uid,
							"experimental_condition": experimental_condition,
							"scores": scores 
						}

			# Get moves for p1 and p2
			chosen_arms = [[None for _ in range(15)] for _ in range(20)]
			rewards = [[None for _ in range(15)] for _ in range(20)]
			for m in moves:
				if m[7] is None:
					continue
				uid = m[1]
				trial = m[3]
				game = m[4]

				chosen_arm = m[2]
				reward = m[5]
				if uid == p1_uid or uid == p2_uid:
					# Skip duplicates
					if chosen_arms[game - 1][trial - 1]:
						continue
					chosen_arms[game - 1][trial - 1] = chosen_arm
					rewards[game - 1][trial - 1] = reward

			print("Room {}, All chosen arms: {}".format(room_id, chosen_arms))

			valid_room["chosen_arms"] = chosen_arms
			valid_room["rewards"] = rewards
			valid_rooms.append(valid_room)

		self.valid_rooms = valid_rooms
		self.num_valid_rooms = len(valid_rooms)
		self.room_id_mapping = { r["room_id"]: i for i, r in enumerate(self.valid_rooms) }

		# Rewards are Bernoulli
		self.num_rewards = 2 
		self.num_games = 20
		self.num_trials = 15
		self.num_arms = 4

		# Compute per trial model agreement
		self.model_agreement = np.zeros((self.num_valid_rooms, self.num_games, self.num_trials))
		self.model_actions = np.zeros((self.num_valid_rooms, self.num_games, self.num_trials))
		self.human_actions = np.zeros((self.num_valid_rooms, self.num_games, self.num_trials))
		self.rewards = np.zeros((self.num_valid_rooms, self.num_games, self.num_trials))

	def compute_model_agreement(self):
		self.average_model_agreement_by_condition = { "control": 0, "partial": 0, "partial_asymmetric": 0 }
		self.num_rooms_by_condition = { "control": 0, "partial": 0, "partial_asymmetric": 0 }
		for room in self.valid_rooms:
			room_id_original = room["room_id"]
			room_id = self.room_id_mapping[room_id_original]
			p1 = 0
			p2 = 1
			experimental_condition = room["experimental_condition"]
			p1_observability = observability_probabilities[experimental_condition][p1]
			p2_observability = observability_probabilities[experimental_condition][p2]
			next_turn = p1

			self.num_rooms_by_condition[experimental_condition] += 1
			for g in range(self.num_games):
				p1_model = CollaborativeModel(n_arms=self.num_arms, T=self.num_trials, my_observability=p1_observability, partner_observability=p2_observability)
				p2_model = CollaborativeModel(n_arms=self.num_arms, T=self.num_trials, my_observability=p2_observability, partner_observability=p1_observability)
				for t in range(self.num_trials):
						# Chosen arms indexed at 0 for model, but 1 for human record in db
						k_human = int(room["chosen_arms"][g][t] - 1)

						if next_turn == p1:
							k_model = p1_model.choose()
						else:
							k_model = p2_model.choose()
						
						self.model_actions[room_id, g, t] = k_model
						self.human_actions[room_id, g, t] = k_human
						self.model_agreement[room_id, g, t] = k_human == k_model
						if t != 0 and k_human == k_model:
							self.average_model_agreement_by_condition[experimental_condition] += 1

						reward = room["rewards"][g][t]
						
						# Update models based on observability
						p1_observed = experimental_conditions[experimental_condition][p1][g][t]
						p2_observed = experimental_conditions[experimental_condition][p2][g][t]

						if p1_observed == False:
							p1_model.observe(k_human, None, p2_observed)
						elif p1_observed == True:
							p1_model.observe(k_human, reward, p2_observed)
						
						if p2_observed == False:
							p2_model.observe(k_human, None, p1_observed)
						elif p2_observed == True:
							p2_model.observe(k_human, reward, p1_observed)
						
						next_turn = p1 if next_turn == p2 else p2
		# Remove trial 1 (t=0)
		print("Original shape (room, g, t): ", self.model_agreement.shape)
		self.model_agreement = np.delete(self.model_agreement, np.s_[0], axis=2)
		print("New shape (room, g, t): ", self.model_agreement.shape)

		# Compute average model agreement
		print("Sum model agreement:", np.sum(self.model_agreement))
		self.average_model_agreement = np.true_divide(np.sum(self.model_agreement), \
			self.model_agreement.shape[0] * self.model_agreement.shape[1] * self.model_agreement.shape[2])

		# Compute average model agreement by condition
		print("AVERAGE AGREEMENT BY CONDITION:", self.average_model_agreement_by_condition)
		self.average_model_agreement_by_condition["control"] /= 280. * self.num_rooms_by_condition["control"]
		self.average_model_agreement_by_condition["partial"] /= 280. * self.num_rooms_by_condition["partial"]
		self.average_model_agreement_by_condition["partial_asymmetric"] /= 280. * self.num_rooms_by_condition["partial_asymmetric"]

		print("Mapping of room ids:", self.room_id_mapping)
		print("AVERAGE AGREEMENT:", self.average_model_agreement)
		print("AVERAGE AGREEMENT BY CONDITION:", self.average_model_agreement_by_condition)

		return self.human_actions, self.model_actions, self.model_agreement 
url = parse.urlparse(os.environ["DATABASE_URL"])
analysis = Analysis(url)
analysis.compute_model_agreement()