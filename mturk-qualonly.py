from boto.mturk.connection import MTurkConnection
import os, csv, sys, math
from urllib import parse
import psycopg2
import psycopg2.extras
import numpy as np
from datetime import datetime

HIT_IDS = [
	"3KTCJ4SCVGL8ENH4PJZ4H80VVN71MI",
	"3IZPORCT1FTAFEFAWGY6VUACI0NRHI",
	"32W3UF2EZO5CX02WZCOSCA2MDU1C4E",
	"3X2LT8FDHW2MUZV3S6E65GPU7WL8WW"
]

QUAL_ID = "3UZ6VZ89OUG2MYQI7QCGNQE7UQOBGC"
QUAL_NAME = "doubletrouble"

MAX_ASSIGNMENTS_PER_HIT = 300

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

HOST = 'mechanicalturk.amazonaws.com'

mturk = MTurkConnection(aws_access_key_id=AWS_ACCESS_KEY_ID,
						aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
						host=HOST)

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

try:
	qual_response = mturk.create_qualification_type(QUAL_NAME, QUAL_DESC, "Active")
except:
	qual_response = mturk.search_qualification_types(QUAL_NAME)

qual_id = qual_response[0].QualificationTypeId

print("Qual ID: {0}".format(qual_id))

workers = []
for assignment in assignments:
	assignment_id = assignment.AssignmentId
	worker_id = assignment.WorkerId
	answers = assignment.answers[0]
	workers.append({"worker_id": worker_id, "assignment_id": assignment_id})
	print("Worker {0}".format(worker_id))

for worker in workers:
	print(worker["worker_id"])
	# Assign qualifications
	try:
		mturk.assign_qualification(qual_id, worker["worker_id"], value=1, send_notification=False)
	except:
		try:
			mturk.assign_qualification(qual_id, worker["worker_id"], value=1)
		except:
			print("There was an error giving qual {0} with qual id {1} to worker {2} for HIT {3}".format(QUAL_NAME, qual_id, worker["worker_id"], worker["assignment_id"]))
		else:
			print("Gave qualification to {}".format(worker["worker_id"]))
	else:
		print("Gave qualification to {}".format(worker["worker_id"]))   

print(mturk.get_account_balance()[0])








