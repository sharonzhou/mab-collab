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
print(valid_worker_ids)

avg_time = []
for room in rooms:
	print("Room", room[0])
	p1_uid = room[2]
	p2_uid = room[3]
	time_last_move = room[4]

	query = "select last_active from worker where id =" + str(p1_uid) + ";"
	cursor.execute(query)
	last_active_p1 = cursor.fetchone()[0]
	avg_time.append((time_last_move - last_active_p1).total_seconds())

	query = "select last_active from worker where id =" + str(p2_uid) + ";"
	cursor.execute(query)
	last_active_p2 = cursor.fetchone()[0]
	avg_time.append((time_last_move - last_active_p2).total_seconds())

print(np.sum(avg_time) / len(avg_time) / 60.)
# 9min task on average
