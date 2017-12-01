import os, random, csv
from urllib import parse
import psycopg2
import psycopg2.extras
import numpy as np
from kg import KnowledgeGradient
from constant import *

parse.uses_netloc.append("postgres")
url = parse.urlparse(os.environ["DATABASE_URL"])

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

query = "select * from move;"
cursor.execute(query)
moves = cursor.fetchall()

query = "select * from worker;"
cursor.execute(query)
workers = cursor.fetchall()

valid_worker_ids = [w[0] for w in workers if w[1] and w[1] != "testing"]
num_workers = len(valid_worker_ids)
worker_id_mapping = { w: i for i, w in enumerate(valid_worker_ids)}

num_games = 20
num_trials = 15
num_arms = 4
num_rewards = 2
arm_data = np.zeros((num_workers, num_games, num_trials))
reward_data = np.zeros((num_workers, num_games, num_trials))

# Get valid moves
history = []
for m in moves:
	u = m[1]
	if u not in valid_worker_ids:
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
	w = worker_id_mapping[u]
	arm_data[w, g, t] = k
	reward_data[w, g, t] = r

# Compute per trial model agreement
agreement = np.zeros((num_workers, num_games, num_trials))
for u in range(num_workers):
	for g in range(num_games):
		kg = KnowledgeGradient(num_arms, num_trials)
		for t in range(num_trials):
			k_human = int(arm_data[u, g, t])
			k_robot = kg.choose()
			agreement[u, g, t] = k_human == k_robot
			r = reward_data[u, g, t]
			kg.observe(k, r)

with open("model_agreement.csv", "w+") as f:
	writer = csv.writer(f)
	for u in range(num_workers):
		for g in range(num_games):
			writer.writerow(np.insert(agreement[u, g], 0, u, axis=0))

"""
# Aggregate data across workers by game, trial, arm chosen, reward received
num_games = 20
num_trials = 15
num_arms = 4
num_rewards = 2
aggregate = np.zeros((num_games, num_trials, num_arms, num_rewards))
history = []
for m in moves:
	uid = m[1]
	if uid not in valid_worker_ids:
		continue
	k = m[2]
	trial = m[3] - 1
	game = m[4] - 1
	r = m[5]

	# Remove duplicates	
	h = [uid, trial, game]
	if history and h in history:
		continue
	history.append(h)

	# Counter
	aggregate[game][trial][k][r] += 1

# Get probabilities of choosing each arm at every trial, per game
probabilities = np.zeros((num_games, num_trials, num_arms))
for i in range(num_games):
	for j in range(num_trials):
		probabilities[i,j] = np.sum(aggregate[i][j], axis=1) / np.sum(aggregate[i][j])
print("E.g. Game 20, Trial 15: ", probabilities[19][14])
"""



