from flask import Flask, jsonify, render_template, request, redirect, url_for, session, escape
from app import app, db
from app.models import *
from app.constant import *
import numpy as np
import random, string
from datetime import datetime, timedelta

@app.route('/logout')
def logout():
	print('logout', session)
	session.clear()
	return redirect(url_for('index'))

@app.route('/_next_game')
def next_game():
	print('next_game', session)
	session['score'] = 0
	session['trial'] = 1
	session['game'] += 1
	session['reward'] = None
	session['next_game_button'] = False
	return jsonify(uid=session['uid'], game=session['game'], trial=session['trial'], score=session['score'], scores=session['scores'], reward=session['reward'])

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
	k = request.args.get('k', type=int) - 1
	game = session['game']
	r = 1 if random.random() < reward_rates[game - 1][k] else 0
	session['reward'] = r

	# Get current vars from session
	uid = session['uid']
	trial = session['trial']

	# Record user's choice and reward to db, for trials within scope 
	# (don't record accidental requests from spamming keys)
	if trial <= 15:
		if 'score' not in session:
			session['score'] = 0
		session['score'] += r
		score = session['score']
		move = Move(uid=uid, chosen_arm=k, trial=trial, game=game, reward=r, score=score)
		print('stored', move)
		db.session.add(move)
		db.session.commit()

	# If playing double
	if 'room_id' in session and session['room_id'] != 0:
		# Set default session vars
		session['next_game_button'] = False
		session['completion_code'] = False

		# End or next game
		if trial >= 15:
			if trial == 15:
				session['scores'].append(session['score'])

			if game >= 20:
				session['completion_code'] = True
			else:
				session['next_game_button'] = True
	else:
		session['next_game_button'] = False
		if trial >= 15:
			session['next_game_button'] = True

	# Next trial
	session['trial'] = trial + 1

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
	if 'amt_id' in session and 'uid' in session:
		# Flag that user is waiting w/ defaults
		session['next_game_button'] = False
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

				room = Room(next_turn_uid=first_turn_uid, p1_uid=user.id, p2_uid=partner_uid, \
					time_last_move=timestamp, chosen_arm=-1, trial=1, game=1, score=0)
				db.session.add(room)
				db.session.commit()

				new_room_id = Room.query.filter_by(p1_uid=user.id, p2_uid=partner_uid).order_by(Room.id.desc()).first().id
				session['room_id'] = new_room_id
				print(new_room_id)

				user.room_id = new_room_id
				partner.room_id = new_room_id

				user.is_ready = False
				partner.is_ready = False

				session['is_ready'] = False
				db.session.commit()
		return jsonify(room_id=session['room_id'])

@app.route('/_drop_user')
def drop_user():
	print('drop_user', session)
	if 'amt_id' in session:
		if 'room_id' in session and session['room_id'] != 0:
			# Restore matched partner to waiting
			room = Room.query.get(session['room_id'])
			if room.p1_uid == session['uid']:
				partner_uid = room.p2_uid
			elif room.p2_uid == session['uid']:
				partner_uid = room.p1_uid
			else:
				print('Error, room does not match dropped user')
				return jsonify(response='Error, room does not match dropped user')
			partner = Worker.query.get(partner_uid)
			partner.room_id = 0
			partner.is_ready = True
			user.is_ready = False
			user.room_id = 0
			db.session.commit()
			return jsonify(response='Altered dropped user\'s partner')


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








































