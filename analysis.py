import os
from urllib import parse
import psycopg2
import psycopg2.extras
import numpy as np

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
print(valid_worker_ids)

# Aggregate data across workers by game, trial, arm chosen, reward received
num_games = 20
num_trials = 15
num_arms = 4
num_rewards = 2
aggregate = np.zeros((num_games, num_trials, num_arms, num_rewards))
history = []
for m in moves:
	uid = m[1]
	k = m[2]
	trial = m[3] - 1
	game = m[4] - 1
	r = m[5]

	# Remove duplicates - meaning uid, trial, game are all same - keep first one	
	h = [uid, trial, game]
	if history and h in history:
		print("repeated uid game trial: ", uid, game, trial)
		continue
	history.append(h)

	# Counter
	aggregate[game][trial][k][r] += 1

print(aggregate[-1][-1])




