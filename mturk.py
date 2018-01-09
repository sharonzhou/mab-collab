from boto.mturk.connection import MTurkConnection
from boto.mturk.price import Price
import os, csv, sys, boto3, math
from urllib import parse
import psycopg2
import psycopg2.extras
import numpy as np
from datetime import datetime
from collections import defaultdict

HIT_IDS = [
	"3KTCJ4SCVGL8ENH4PJZ4H80VVN71MI",
	"3IZPORCT1FTAFEFAWGY6VUACI0NRHI",
	"32W3UF2EZO5CX02WZCOSCA2MDU1C4E",
	"3X2LT8FDHW2MUZV3S6E65GPU7WL8WW"
]

QUAL_ID = "3UZ6VZ89OUG2MYQI7QCGNQE7UQOBGC"
QUAL_NAME = "doubletrouble"

HIT_COST = 0.5

WAIT_BONUS = 0.5
DROPOUT_BONUS = 1

BASE_BONUS = 1.5
WIN_MOST = 0
WIN_AVG = 3
WIN_TOP = 2

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

completion_code_to_cumulative_score = {}
all_cumulative_scores = []
for room in rooms:
	p1_uid = room[2]
	p2_uid = room[3]
	experimental_condition = room[19]
	scores = room[18].strip("\[\]").split(", ")
	scores = [int(s) for s in scores if s != ""]

	if len(scores) < 10:
		print("Dropping out Room", room[0], "with users", p1_uid, p2_uid, "and condition", experimental_condition)
		continue

	print("Room", room[0], "with users", p1_uid, p2_uid, "and condition", experimental_condition)

	completion_code = room[10]
	cumulative_score = np.sum(scores)
	completion_code_to_cumulative_score[completion_code] = cumulative_score
	all_cumulative_scores.append(cumulative_score)
print("Completion code to cumulative score", completion_code_to_cumulative_score)

# Calculate relevant score cutoffs for bonuses
most_score = np.percentile(all_cumulative_scores, 25)
average_score = np.percentile(all_cumulative_scores, 50)
top_score = np.percentile(all_cumulative_scores, 90)
print("Score cutoffs", most_score, average_score, top_score)

completion_code_to_bonus = {}
for code, score in completion_code_to_cumulative_score.items():
	if not code:
		continue
	bonus = BASE_BONUS
	if score >= most_score:
		bonus += WIN_MOST
	if score >= average_score:
		bonus += WIN_AVG
	if score >= top_score:
		bonus += WIN_TOP
	completion_code_to_bonus[code.upper()] = bonus
print("Completion code to bonus", completion_code_to_bonus)

MAX_ASSIGNMENTS_PER_HIT = 300

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

HOST = 'mechanicalturk.amazonaws.com'

mturk = MTurkConnection(aws_access_key_id=AWS_ACCESS_KEY_ID,
						aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
						host=HOST)
client = boto3.client(
    'mturk',
    region_name='us-east-1',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

current_balance = float(client.get_account_balance()['AvailableBalance'])
print(current_balance)

print(mturk.get_account_balance()[0])

assignments = []
for hit_id in HIT_IDS:
	pages = math.ceil(MAX_ASSIGNMENTS_PER_HIT / 100)
	for x in range(pages):
		page_number = x + 1
		hit_assignments = mturk.get_assignments(hit_id, status=None, page_size=100, page_number=page_number)
		print("{} assignments found for HIT {}".format(len(hit_assignments), hit_id))
		assignments += hit_assignments
print(assignments)

workers = []
total_bonuses = 0
completion_codes = defaultdict(int)
worker_ids = defaultdict(int)
spammers = []
for assignment in assignments:
	assignment_id = assignment.AssignmentId
	worker_id = assignment.WorkerId
	worker_ids[worker_id] += 1
	answers = assignment.answers[0]
	completion_code = None
	for answer in answers:
		if answer.qid == "code":
			completion_code = answer.fields[0].strip().upper()
			completion_codes[completion_code] += 1
			if completion_code and completion_code[0] == "T":
				bonus = WAIT_BONUS
				total_bonuses += bonus + HIT_COST
				workers.append({"worker_id": worker_id, "assignment_id": assignment_id, "bonus": bonus})
				print("Worker (waiting) {0}: Completion code {1}, with bonus {2} ".format(worker_id, completion_code, bonus))
			elif completion_code and completion_code[0] == "C" and completion_code[-1] == "P":
				bonus = DROPOUT_BONUS
				total_bonuses += bonus + HIT_COST
				workers.append({"worker_id": worker_id, "assignment_id": assignment_id, "bonus": bonus})
				print("Worker (partner dropped out) {0}: Completion code {1}, with bonus {2} ".format(worker_id, completion_code, bonus))
			elif completion_code in completion_code_to_bonus:
				bonus = completion_code_to_bonus[completion_code]
				total_bonuses += bonus + HIT_COST
				workers.append({"worker_id": worker_id, "assignment_id": assignment_id, "bonus": bonus})
				print("Worker {0}: Completion code {1}, with bonus {2} ".format(worker_id, completion_code, bonus))
			else:
				print("Worker {0} has no identifiable Completion code {1}".format(worker_id, completion_code))
				spammers.append({"worker_id": worker_id, "assignment_id": assignment_id, "completion_code": completion_code})
print("Redundant completion codes:", [c for c, v in completion_codes.items() if v > 2])
print("Redundant workers codes:", [w for w, v in worker_ids.items() if v > 1])
# print("All workers:", workers)
print("Total number of workers: {}".format(len(workers)))
print("Total bonuses:", total_bonuses)
print("Do we have enough money in the account?", current_balance, total_bonuses, current_balance >= total_bonuses)
if current_balance < total_bonuses:
	print("We need to add", total_bonuses - current_balance, ", rounded up", math.ceil(total_bonuses - current_balance))

try:
	qual_response = mturk.create_qualification_type(QUAL_NAME, QUAL_DESC, "Active")
except:
	qual_response = mturk.search_qualification_types(QUAL_NAME)

qual_id = qual_response[0].QualificationTypeId

print("Qual ID: {0}".format(qual_id))

message = "Thanks for participating and for your feedback. Hope you enjoyed it!"

errored_workers = []

for worker in workers:
	print(worker["worker_id"])
	# Assign qualifications
	# try:
	# 	mturk.assign_qualification(qual_id, worker["worker_id"], value=1, send_notification=False)
	# except:
	# 	try:
	# 		mturk.assign_qualification(qual_id, worker["worker_id"], value=1)
	# 	except:
	# 		print("There was an error giving qual {0} with qual id {1} to worker {2} for HIT {3}".format(QUAL_NAME, qual_id, worker["worker_id"], worker["assignment_id"]))
	# 	else:
	# 		print("Gave qualification to {}".format(worker["worker_id"]))
	# else:
	# 	print("Gave qualification to {}".format(worker["worker_id"]))   
	
	# Pay workers
	if current_balance < total_bonuses:
		print("Before paying workers, we need to add to our account $", total_bonuses - current_balance, ", rounded up that's $", math.ceil(total_bonuses - current_balance))
	else:
		try:
			# Pay bonuses
			mturk.grant_bonus(worker["worker_id"], worker["assignment_id"], Price(worker["bonus"]), message)
		except:
			errored_workers.append(worker)
		else:
			print("Paid worker", worker)

print(mturk.get_account_balance()[0])

print("Errored:", errored_workers)
print("Spammers:", spammers)








