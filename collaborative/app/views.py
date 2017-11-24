from flask import Flask, jsonify, render_template, request, redirect, url_for, session, escape
from app import app, db
from app.models import *
from app.constant import *
import numpy as np
import random, string
from datetime import datetime, timedelta

MAX_TRIALS = 15
MAX_GAMES = 20

@app.route('/logout')
def logout():
	print('logout', session)
	session.clear()
	return redirect(url_for('index'))

@app.route('/_check_partner_move')
def check_partner_move():
	# print('check_partner_move', session)

	# Check whose turn it is in the room
	room = Room.query.get(session['room_id'])
	turn = room.next_turn_uid
	session['next_turn_uid'] = turn

	# Partner moved (it's your turn now); update session vars
	if turn == session['uid']:
		session['game'] = room.game
		session['trial'] = room.trial
		session['reward'] = room.reward
		session['chosen_arm'] = room.chosen_arm
		session['completion_code'] = room.completion_code
		if room.p1_uid == session['uid']:
			session['scores'] = room.p1_scores
			session['score'] = room.p1_score
		else:
			session['scores'] = room.p2_scores
			session['score'] = room.p2_score

		# TODO: partial observability: update session score appropriately
	
	session_vars = {}
	for k, v in session.items():
		session_vars[k] = v	
	return jsonify(session_vars)

@app.route('/_choose_arm')
def give_reward():
	print('give_reward', session)

	# Default values
	if 'game' not in session:
		session['game'] = 1
	if 'trial' not in session:
		session['trial'] = 1
	if 'scores' not in session or not session['scores']:
		session['scores'] = []
	if 'score' not in session or not session['score']:
		session['score'] = 0
	uid = session['uid']
	game = session['game']
	trial = session['trial']
	scores = session['scores']
	score = session['score']

	last_move = Move.query.filter_by(uid=uid).order_by(Move.id.desc()).first()
	if not last_move or trial != last_move.trial:
		# Get reward r for arm k
		chosen_arm = request.args.get('k', type=int)
		reward = 1 if random.random() < reward_rates[game - 1][chosen_arm - 1] else 0
		session['chosen_arm'] = chosen_arm
		session['reward'] = reward

		# Next trial
		session['trial'] = trial + 1

		# Set default session vars
		session['completion_code'] = None

		# Record user's choice and reward to db, for trials within scope (don't record accidental requests from spamming keys)
		if trial <= MAX_TRIALS:
			# TODO: partial observability: update score in Move DB (have a observed flag nullable=T), but not in session var...
			score += reward
			session['score'] = score
			print('my score updated to be', score, reward)
			# TODO: this score is updating weird
			move = Move(uid=uid, chosen_arm=chosen_arm, trial=trial, game=game, reward=reward, score=score)
			print('stored', move)
			db.session.add(move)
			db.session.commit()

		# If playing double, update room
		if 'room_id' in session and session['room_id'] != 0:
			# End or next game
			reset = False
			if session['trial'] >= MAX_TRIALS:
				if trial == MAX_TRIALS:
					session['scores'].append(score)
				if game >= MAX_GAMES:
					# Give completion code
					x = session['amt_id'][-1]
					code = ''.join(random.sample(string.ascii_letters + string.digits, 3)) + str(x) + ''.join(random.sample(string.ascii_letters + string.digits, 3)) 	
					session['completion_code'] = code

					# Store value in room for partner to query
					room = Room.query.get(session['room_id'])
					room.completion_code = code
					db.session.commit()
				else:
					reset = True
					session['score'] = 0
					session['trial'] = 1
					session['game'] += 1
					session['reward'] = None
					session['chosen_arm'] = None

			# Switch to partner's turn; update scores
			room = Room.query.get(session['room_id'])
			if room.p1_uid == session['uid']:
				room.next_turn_uid = room.p2_uid
				session['next_turn_uid'] = room.p2_uid

				room.p1_scores = session['scores']
				room.p1_score = session['score']

				# Partner's score update
				# TODO: partial observability
				if trial <= MAX_TRIALS:
					room.p2_score += reward
					print('i am p1: partner p2 score updated to be', room.p2_score, reward, session['uid'])
					if trial == MAX_TRIALS:
						partner_scores = room.p2_scores
						partner_scores.append(room.p2_score)
						room.p2_scores = partner_scores
			else:
				room.next_turn_uid = room.p1_uid
				session['next_turn_uid'] = room.p1_uid

				room.p2_scores = session['scores']
				room.p2_score = session['score']

				# Partner's score update
				# TODO: partial observability
				if trial <= MAX_TRIALS:
					room.p1_score += reward
					print('i am p2: partner p1 score updated to be', room.p1_score, reward, session['uid'])
					if trial == MAX_TRIALS:
						partner_scores = room.p1_scores
						partner_scores.append(room.p1_score)
						room.p1_scores = partner_scores
			# TODO: partial observability
			if reset:
				room.p1_score = session['score']
				room.p2_score = session['score']
			room.time_last_move = datetime.utcnow()
			room.chosen_arm = session['chosen_arm']
			room.reward = session['reward']
			room.trial = session['trial']
			room.game = session['game']
			room.completion_code = session['completion_code']
			db.session.commit()
		else:
			session['next_game_bool'] = False
			if trial >= MAX_TRIALS:
				session['next_game_bool'] = True
	else:
		# Requery state b/c of repeated requests
		print('avoided duplicating', session)
		room = Room.query.get(session['room_id'])
		if room.p1_uid == session['uid']:
			session['score'] = room.p1_score
			session['scores'] = room.p1_scores
		else:
			session['score'] = room.p2_score
			session['scores'] = room.p2_scores
		session['game'] = room.game
		session['trial'] = room.trial
		session['reward'] = room.reward
		session['chosen_arm'] = room.chosen_arm
		session['completion_code'] = room.completion_code

	session_vars = {}
	for k, v in session.items():
		session_vars[k] = v
	return jsonify(session_vars)

@app.route('/_create_user')
def insert_user():
	print('insert_user', session)
	amt_id = request.args.get('amt_id')

	# Create user in db
	user = Worker(amt_id=amt_id, room_id=0, is_ready=False)
	db.session.add(user)
	db.session.commit()

	uhash = hash(user)
	session['amt_id'] = amt_id
	session['uhash'] = uhash

	# Return vars for debugging on client side
	return jsonify(amt_id=amt_id, uhash=uhash)

@app.route('/_waiting_completion_code')
def make_waiting_completion_code():
	print('waiting_completion_code', session)
	if 'amt_id' in session:
		x = session['amt_id'][0]
		code = 't' + ''.join(random.sample(string.ascii_letters + string.digits, 3)) + str(x) + ''.join(random.sample(string.ascii_letters + string.digits, 3)) 	
		return jsonify(code=code)

@app.route('/_enter_waiting')
def enter_waiting_room():
	print('enter_waiting_room', session)

	# Flag that user is waiting w/ defaults
	if 'amt_id' in session and 'uid' in session:
		session['next_game_bool'] = False
		session['last_active'] = datetime.utcnow()
		session['is_ready'] = True
		session['room_id'] = 0

		session['game'] = 1
		session['trial'] = 1
		session['score'] = 0
		session['reward'] = None

		user = Worker.query.get(session['uid'])
		user.last_active = session['last_active']
		user.is_ready = session['is_ready']
		user.room_id = session['room_id']
		db.session.commit()
		return jsonify(uid=user.id, is_ready=session['is_ready'], room_id=session['room_id'])

@app.route('/_waiting_ping')
def check_waiting_room():
	print('check_waiting_room', session)
	if 'amt_id' in session and 'uid' in session:
		# Record activity timestamp
		session['last_active'] = datetime.utcnow()
		user = Worker.query.get(session['uid'])
		user.last_active = session['last_active']
		db.session.commit()

		# Check if user already has room id and already matched
		room_id = user.room_id
		if room_id != 0:
			session['is_ready'] = False
			session['room_id'] = room_id
		# Check waiting room for a partner
		else:
			partner = Worker.query.filter(Worker.id != session['uid']).filter(Worker.last_active >= session['last_active'] - timedelta(seconds=20)).filter_by(room_id=0, is_ready=True).first()
			if partner is not None:
				print(user, "partnered up with ", partner)

				# Create next room
				partner_uid = partner.id
				timestamp = datetime.utcnow()
				first_turn_uid = user.id if random.random() < .5 else partner_uid
				session['next_turn_uid'] = first_turn_uid

				room = Room(next_turn_uid=first_turn_uid, p1_uid=user.id, p2_uid=partner_uid, \
					time_last_move=timestamp, chosen_arm=-1, trial=1, game=1, reward=None, \
					completion_code=None, p1_score=0, p2_score=0, p1_scores=[], p2_scores=[])
				db.session.add(room)
				db.session.commit()

				new_room_id = Room.query.filter_by(p1_uid=user.id, p2_uid=partner_uid).order_by(Room.id.desc()).first().id
				session['room_id'] = new_room_id

				user.room_id = new_room_id
				partner.room_id = new_room_id

				user.is_ready = False
				partner.is_ready = False
				session['is_ready'] = False

				db.session.commit()
		return jsonify(room_id=session['room_id'])

@app.route('/')
def index():
	print('index', session)
	if 'amt_id' in session:
		uhash = hash(session['amt_id'])
		if 'uid' not in session:
			uid = Worker.query.filter_by(amt_id=session['amt_id']).order_by(Worker.id.desc()).first().id
			session['uid'] = uid
		session_vars = {}
		for k, v in session.items():
			session_vars[k] = v
		if 'is_ready' not in session:
			# Play single
			return render_template('play_single.html', vars=session_vars)			
		elif 'is_ready' in session and session['is_ready']:
			# Put in waiting room and wait on client side
			return render_template('wait.html', vars=session_vars)
		elif 'room_id' in session and session['room_id'] != 0:
			# Play double
			return render_template('play_double.html', vars=session_vars)
		else:
			print('Error, erase session')
			session.clear()
			return render_template('index.html')
	else:
		return render_template('index.html')

app.secret_key = '\x96\xca\xd6\xe5\xa9\\\x08\xa2\x08\xdf\x82\xc2\xcc\xfe'








































