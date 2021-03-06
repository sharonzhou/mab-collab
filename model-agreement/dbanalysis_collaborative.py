import os, random, csv, itertools
from urllib import parse
import psycopg2
import psycopg2.extras
import numpy as np
from collaborative_model import CollaborativeModel
from constant import *
import params_history

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

			# print("Room {}, All chosen arms: {}".format(room_id, chosen_arms))

			valid_room["chosen_arms"] = chosen_arms
			valid_room["rewards"] = rewards
			valid_rooms.append(valid_room)

		self.valid_rooms = valid_rooms
		self.num_valid_rooms = len(valid_rooms)
		self.room_id_mapping = { r["room_id"]: i for i, r in enumerate(self.valid_rooms) }
		self.id_room_mapping = { self.room_id_mapping[r]: r for r in self.room_id_mapping.keys() }

		# Rewards are Bernoulli
		self.num_rewards = 2 
		self.num_games = 20
		self.num_trials = 15
		self.num_arms = 4
		self.num_conditions = 3

		# Compute per trial model agreement
		self.model_agreement = np.zeros((self.num_valid_rooms, self.num_games, self.num_trials))
		self.model_actions = np.zeros((self.num_valid_rooms, self.num_games, self.num_trials))
		self.human_actions = np.zeros((self.num_valid_rooms, self.num_games, self.num_trials))
		self.rewards = np.zeros((self.num_valid_rooms, self.num_games, self.num_trials))
		self.experimental_conditions = ["" for _ in range(self.num_valid_rooms)]

	def get_model_agreement(self):
		self.average_model_agreement_by_condition = { "control": [], "partial": [], "partial_asymmetric": [] }
		for room in self.valid_rooms:
			room_id_original = room["room_id"]
			room_id = self.room_id_mapping[room_id_original]

			p1 = 0
			p2 = 1
			experimental_condition = room["experimental_condition"]
			p1_observability = observability_probabilities[experimental_condition][p1]
			p2_observability = observability_probabilities[experimental_condition][p2]
			next_turn = p1

			p1_alpha = .65
			p1_beta = 1.05
			p2_alpha = .65
			p2_beta = 1.05
			room_model_actions = np.zeros((self.num_games, self.num_trials))
			room_human_actions = np.zeros((self.num_games, self.num_trials))
			room_model_agreement = np.zeros((self.num_games, self.num_trials))
			room_rewards = np.zeros((self.num_games, self.num_trials))

			for g in range(self.num_games):
				p1_model = CollaborativeModel(n_arms=self.num_arms, T=self.num_trials, alpha=p1_alpha, beta=p1_beta, my_observability=p1_observability, partner_observability=p2_observability)
				p2_model = CollaborativeModel(n_arms=self.num_arms, T=self.num_trials, alpha=p2_alpha, beta=p2_beta, my_observability=p2_observability, partner_observability=p1_observability)
				for t in range(self.num_trials):
					# Chosen arms indexed at 0 for model, but 1 for human record in db
					k_human = int(room["chosen_arms"][g][t] - 1)

					if next_turn == p1:
						k_model = p1_model.choose()
					else:
						k_model = p2_model.choose()
					
					room_model_actions[g, t] = k_model
					room_human_actions[g, t] = k_human
					room_model_agreement[g, t] = k_human == k_model

					reward = room["rewards"][g][t]
					room_rewards[g][t] = reward

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
			# Model agreement (average) for this room w/ these params, while removing trial 1
			full_room_model_agreement = np.copy(room_model_agreement)
			room_model_agreement = np.delete(room_model_agreement, np.s_[0], axis=1)
			room_model_agreement = np.true_divide(np.sum(room_model_agreement), room_model_agreement.shape[0] * room_model_agreement.shape[1])
			
			self.model_actions[room_id] = room_model_actions
			self.human_actions[room_id] = room_human_actions
			self.model_agreement[room_id] = full_room_model_agreement
			self.rewards[room_id] = room_rewards
			self.experimental_conditions[room_id] = experimental_condition
			self.average_model_agreement_by_condition[experimental_condition].append(room_model_agreement)

		# Model agreement across rooms, removing trial 1 (trial=0)
		self.adjusted_model_agreement = np.delete(self.model_agreement, np.s_[0], axis=2)
		self.adjusted_model_agreement_per_room = np.true_divide(np.sum(self.adjusted_model_agreement, axis=(1,2)), self.adjusted_model_agreement.shape[1] * self.adjusted_model_agreement.shape[2])

		# Compute average model agreement
		self.average_model_agreement = np.true_divide(np.sum(self.adjusted_model_agreement), \
			self.adjusted_model_agreement.shape[0] * self.adjusted_model_agreement.shape[1] * self.adjusted_model_agreement.shape[2])
		print("Mapping of room ids:", self.room_id_mapping)
		print("AVERAGE AGREEMENT:", self.average_model_agreement, ", std dev:", np.std(self.adjusted_model_agreement_per_room), ", min:", np.amin(self.adjusted_model_agreement_per_room), ", max:", np.amax(self.adjusted_model_agreement_per_room))
		print("By room:", self.adjusted_model_agreement_per_room)

		# Compute average model agreement by condition
		# self.average_model_agreement_by_condition = { k: np.true_divide(v, 280) for k, v in self.average_model_agreement_by_condition.items() }
		print("AVERAGE AGREEMENT BY CONDITION:", \
			"control:", np.mean(self.average_model_agreement_by_condition["control"]), np.std(self.average_model_agreement_by_condition["control"]), \
			", partial:", np.mean(self.average_model_agreement_by_condition["partial"]), np.std(self.average_model_agreement_by_condition["partial"]), \
			", partial_asymmetric:", np.mean(self.average_model_agreement_by_condition["partial_asymmetric"]), np.std(self.average_model_agreement_by_condition["partial_asymmetric"]) \
			)

		return self.model_actions, self.model_agreement, self.average_model_agreement, self.adjusted_model_agreement

	def get_params_history(self):
		print("Evaluated {} params combinations of {} per param".format(len(list(params_history.params_evaluated)), params_history.vals_per_param))
		print("Average agreement {}, std dev {}, range from {} to {}".format(np.mean(params_history.best_agreement), \
			np.std(params_history.best_agreement), np.amin(params_history.best_agreement), np.amax(params_history.best_agreement)))
		print("Average params (greedy/1st found) {}, std dev {}, range from {} to {}".format(np.mean(params_history.best_params, axis=0), \
			np.std(params_history.best_params, axis=0), np.amin(params_history.best_params, axis=0), np.amax(params_history.best_params, axis=0)))
		all_best_params = []
		for room in params_history.all_best_params:
			all_best_params.append(np.mean(room, axis=0))
		print("Average params (all) {}, std dev {}, range from {} to {}".format(np.mean(all_best_params, axis=0), \
			np.std(all_best_params, axis=0), np.amin(all_best_params, axis=0), np.amax(all_best_params, axis=0)))
		return
		
	def compute_model_agreement(self):
		best_params = [ [] for _ in range(self.num_valid_rooms) ]
		best_agreement = [ None for _ in range(self.num_valid_rooms) ]
		history_agreement_to_params = [ {} for _ in range(self.num_valid_rooms) ]
		for room in self.valid_rooms:
			room_id_original = room["room_id"]
			room_id = self.room_id_mapping[room_id_original]
#
			# # Easy way to skip to a certain room
			# if room_id < 9:
			# 	continue
#

			p1 = 0
			p2 = 1
			experimental_condition = room["experimental_condition"]
			p1_observability = observability_probabilities[experimental_condition][p1]
			p2_observability = observability_probabilities[experimental_condition][p2]
			next_turn = p1

			p1_alphas = [0., .3, .6, .9, 1.2, 1.5, 1.8, 2.1]
			p1_betas = [0., .3, .6, .9, 1.2, 1.5, 1.8, 2.1]
			p2_alphas = [0., .3, .6, .9, 1.2, 1.5, 1.8, 2.1]
			p2_betas = [0., .3, .6, .9, 1.2, 1.5, 1.8, 2.1]

			for p1_alpha, p1_beta, p2_alpha, p2_beta in itertools.product(p1_alphas, p1_betas, p2_alphas, p2_betas):
				params = [p1_alpha, p1_beta, p2_alpha, p2_beta]
				if params in list(params_history.best_params_evaluated):
					best_agreement = params_history.best_agreement[room_id]
					best_params = params_history.best_params[room_id]
				room_model_actions = np.zeros((self.num_games, self.num_trials))
				room_human_actions = np.zeros((self.num_games, self.num_trials))
				room_model_agreement = np.zeros((self.num_games, self.num_trials))

				for g in range(self.num_games):
					p1_model = CollaborativeModel(n_arms=self.num_arms, T=self.num_trials, alpha=p1_alpha, beta=p1_beta, my_observability=p1_observability, partner_observability=p2_observability)
					p2_model = CollaborativeModel(n_arms=self.num_arms, T=self.num_trials, alpha=p2_alpha, beta=p2_beta, my_observability=p2_observability, partner_observability=p1_observability)
					for t in range(self.num_trials):
						# Chosen arms indexed at 0 for model, but 1 for human record in db
						k_human = int(room["chosen_arms"][g][t] - 1)

						if next_turn == p1:
							k_model = p1_model.choose()
						else:
							k_model = p2_model.choose()
						
						room_model_actions[g, t] = k_model
						room_human_actions[g, t] = k_human
						room_model_agreement[g, t] = k_human == k_model
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
				
				# Model agreement (average) for this room w/ these params, while removing trial 1
				full_room_model_agreement = np.copy(room_model_agreement)
				room_model_agreement = np.delete(room_model_agreement, np.s_[0], axis=1)
				room_model_agreement = np.true_divide(np.sum(room_model_agreement), room_model_agreement.shape[0] * room_model_agreement.shape[1])
				if room_model_agreement not in list(history_agreement_to_params[room_id].keys()):
					history_agreement_to_params[room_id][room_model_agreement] = []
				history_agreement_to_params[room_id][room_model_agreement].append(params)
				
				# Write to db room_id_original, room_model_agreement, params to csv of history; use vals above for lookup
				
				print(room_id, room_id_original, "Found agreement as: ", room_model_agreement, " with params p1_a, p1_b, p2_a, p2_b as ", params)
				if best_agreement[room_id] is None or room_model_agreement > best_agreement[room_id]:
					print(room_id, room_id_original, "Found new best agreement as: ", room_model_agreement, " with params p1_a, p1_b, p2_a, p2_b as ", params)
					best_agreement[room_id] = room_model_agreement
					best_params[room_id] = params
					self.model_actions[room_id] = room_model_actions
					self.human_actions[room_id] = room_human_actions
					self.model_agreement[room_id] = full_room_model_agreement

			print("History so far ", history_agreement_to_params)
			print("All best params for rooms so far: {}".format(best_params))
			print("Best params found for room {} is {}".format(room_id, best_params[room_id]))

		# Model agreement across rooms
		print("Final history of agreement to params ", history_agreement_to_params)
		print("Final best agreement values for all rooms ", best_agreement)
		print("Final best params for all rooms ", best_params)
		
		# Remove trial 1 (t=0)
		self.adjusted_model_agreement = np.delete(self.model_agreement, np.s_[0], axis=2)

		# Compute average model agreement
		self.average_model_agreement = np.true_divide(np.sum(self.adjusted_model_agreement), \
			self.adjusted_model_agreement.shape[0] * self.adjusted_model_agreement.shape[1] * self.adjusted_model_agreement.shape[2])
		print("Mapping of room ids:", self.room_id_mapping)
		print("AVERAGE AGREEMENT:", self.average_model_agreement, ", std dev:", np.std(self.adjusted_model_agreement), ", min:", np.minimum(self.adjusted_model_agreement), ", max:", np.maximum(self.adjusted_model_agreement))

		return self.model_actions, self.model_agreement, self.average_model_agreement, self.adjusted_model_agreement

# Test
url = parse.urlparse(os.environ["DATABASE_URL"])
analysis = Analysis(url)
analysis.get_params_history()
# analysis.compute_model_agreement()