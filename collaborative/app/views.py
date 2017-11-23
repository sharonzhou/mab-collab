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

def advance_next_game(max_trials, max_games, scores, score, completion_code, next_game_bool, trial, game, reward):
	completion_code = False
	if trial == max_trials:
		scores.append(score)
	if game >= max_games:
		completion_code = True
	else:
		next_game_bool = True
		score = 0
		trial = 1
		game += 1
		reward = None
	return reward, trial, game

@app.route('/_check_partner_move')
def check_partner_move():
	# print('check_partner_move', session)
	session['next_game_bool'] = False
	session['partner_moved'] = False

	# Check whose turn it is in the room
	room = Room.query.get(session['room_id'])
	turn = room.next_turn_uid
	session['next_turn_uid'] = turn

	# Partner moved (it's your turn now); update session vars
	# print(room)
	# print('check_partner_move, turn is: ', turn, 'my uid is', session['uid'])
	if turn == session['uid']:
		session['partner_moved'] = True
		session['game'] = room.game
		session['trial'] = room.trial
		session['reward'] = room.reward
		session['past_reward'] = room.reward #TODO: when new game happens, show past reward from past game (grayed out?), but then show new game w/o score I guess...
		session['chosen_arm'] = room.chosen_arm
		session['completion_code'] = False

		# TODO: partial observability: update session score appropriately

		# End or next game
		if session['trial'] >= MAX_TRIALS:
			advance_next_game(MAX_TRIALS, MAX_GAMES, session['scores'], session['score'], \
				session['completion_code'], session['next_game_bool'], session['trial'], \
				session['game'], session['reward'])
			room.reward = session['reward']
			room.game = session['game']
			room.trial = session['trial']
			db.session.commit()
	
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
	if 'scores' not in session:
		session['scores'] = []

	# Get reward r for arm k
	chosen_arm = request.args.get('k', type=int) - 1
	game = session['game']
	reward = 1 if random.random() < reward_rates[game - 1][chosen_arm] else 0
	session['reward'] = reward

	# Get current vars from session
	uid = session['uid']
	trial = session['trial']
	if 'score' not in session:
		session['score'] = 0
	score = session['score']

	# Record user's choice and reward to db, for trials within scope 
	# (don't record accidental requests from spamming keys)
	if trial <= MAX_TRIALS:
		# TODO: partial observability: update score in Move DB (have a observed flag nullable=T), but not in session var...
		score += reward
		move = Move(uid=uid, chosen_arm=chosen_arm, trial=trial, game=game, reward=reward, score=score)
		print('stored', move)
		db.session.add(move)
		db.session.commit()

	# Next trial
	session['trial'] = trial + 1

	# Set default session vars
	session['next_game_bool'] = False
	session['completion_code'] = False

	# If playing double, update room
	if 'room_id' in session and session['room_id'] != 0:
		session['partner_moved'] = False

		# End or next game
		if session['trial'] >= MAX_TRIALS:
			advance_next_game(MAX_TRIALS, MAX_GAMES, session['scores'], session['score'], \
				session['completion_code'], session['next_game_bool'], session['trial'], \
				session['game'], session['reward'])

		# Switch to partner's turn
		room = Room.query.get(session['room_id'])
		room.next_turn_uid = room.p1_uid if room.p2_uid == session['uid'] else room.p2_uid
		room.time_last_move = datetime.utcnow()
		room.chosen_arm = chosen_arm
		room.reward = reward
		room.trial = session['trial']
		room.game = session['game']
		db.session.commit()

		session['next_turn_uid'] = room.p1_uid if room.p2_uid == session['uid'] else room.p2_uid
	else:
		if trial >= MAX_TRIALS:
			session['next_game_bool'] = True

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

@app.route('/_completion_code')
def make_completion_code():
	print('make_completion_code', session)
	if 'amt_id' in session:
		x = session['amt_id'][-1]
		code = ''.join(random.sample(string.ascii_letters + string.digits, 3)) + str(x) + ''.join(random.sample(string.ascii_letters + string.digits, 3)) 	
		return jsonify(code=code)

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
				session['game'] = 1
				session['trial'] = 1
				session['score'] = 0
				session['reward'] = None

				room = Room(next_turn_uid=first_turn_uid, p1_uid=user.id, p2_uid=partner_uid, \
					time_last_move=timestamp, chosen_arm=-1, trial=1, game=1, reward=None)
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








































