import os
from urllib import parse
import psycopg2
import psycopg2.extras
import numpy as np
from datetime import datetime

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

query = "select * from room;"
cursor.execute(query)
rooms = cursor.fetchall()

valid_worker_ids = [w[0] for w in workers if w[1] and w[1] != "testing"]
dropouts = [w[0] for w in workers if w[5]]
print(valid_worker_ids, dropouts)

avg_time = []
for room in rooms:
	p1_uid = room[2]
	p2_uid = room[3]
	experimental_condition = room[19]
	scores = room[18]
	if len(scores) < 20:
		print("Dropping out Room", room[0], "with users", p1_uid, p2_uid, "and condition", experimental_condition)
		continue

	print("Room", room[0], "with users", p1_uid, p2_uid, "and condition", experimental_condition)
	time_last_move = room[4]

	query = "select last_active from worker where id =" + str(p1_uid) + ";"
	cursor.execute(query)
	last_active_p1 = cursor.fetchone()[0]
	avg_time.append((time_last_move - last_active_p1).total_seconds())

	query = "select last_active from worker where id =" + str(p2_uid) + ";"
	cursor.execute(query)
	last_active_p2 = cursor.fetchone()[0]
	avg_time.append((time_last_move - last_active_p2).total_seconds())

print("Average time on task: ", np.sum(avg_time) / len(avg_time) / 60.)
# 10.5min task on average

chosen_arms_p1 = [[] for _ in range(20)]
chosen_arms_p2 = [[] for _ in range(20)]
for m in moves:
	if m[7] is None:
		continue
	game = m[4]
	if m[1] == 35:
		chosen_arms_p1[game - 1].append(m[2])
	if m[1] == 34:
		chosen_arms_p2[game - 1].append(m[2])
print("P1", chosen_arms_p1)
print("P2", chosen_arms_p2)

