from flask import Flask, jsonify, render_template, request, redirect, url_for, session, escape
from app import app, db
from app.models import *
from app.constant import *
import numpy as np
import random, string, json
from datetime import datetime, timedelta

num_trials = 40
num_games = 10

# Covnerts session variable to json-convertible dict
def session_to_dict(session):
	session_vars = {}
	for k, v in session.items():
		session_vars[k] = v
	return session_vars

# Creates completion codes for: completed, waiting, timeout
def create_completion_code(unique_string, code_type):
	x = unique_string[-1]
	code = ''.join(random.sample(string.ascii_letters + string.digits, 3)) + str(x) + ''.join(random.sample(string.ascii_letters + string.digits, 3)) 	
	if code_type == "completed":
		code += 's' if random.random() < .3 else 'z'
	elif code_type == "waiting":
		code = 't' + code
	elif code_type == "timeout":
		code = 'c' + code + 'p'
	return code

@app.route('/logout')
def logout():
	if session:
		print('logout', session)
		session.clear()
	return redirect(url_for('index'))

@app.route('/_check_partner_move')
def check_partner_move():
	# print('check_partner_move', session)

	# Check whose turn it is in the room
	room = Room.query.get(session['room_id'])
	session['timeout'] = False
	turn = room.next_turn_uid
	session['next_turn_uid'] = turn
	session['completion_code'] = room.completion_code
	session['scores'] = json.loads(room.scores_strs)
	session['next_game_bool'] = room.next_game_bool

	# Partner moved (it's your turn now); update session vars
	if turn == session['uid']:
		session['game'] = room.game
		session['trial'] = room.trial
		session['reward'] = room.reward
		session['chosen_arm'] = room.chosen_arm
		if room.p1_uid == session['uid']:
			session['score'] = room.p1_score
			session['is_observable'] = room.p1_is_observable
			session['partner_is_observable'] = room.p2_is_observable
		else:
			session['score'] = room.p2_score
			session['is_observable'] = room.p2_is_observable
			session['partner_is_observable'] = room.p1_is_observable
	else:
		# Partner's turn: check if they dropped out
		if room.time_last_move < datetime.utcnow() - timedelta(seconds=21):
			session['timeout'] = True
			
			# Set partner's timeout bool to true, so they can't return to game
			partner_uid = room.p1_uid if room.p2_uid == session['uid'] else room.p2_uid
			partner = Worker.query.get(partner_uid)
			partner.timeout = True
			room.dropout = partner_uid
			db.session.commit()

			# Give intermediate completion code
			session['timeout_code'] = create_completion_code(session['amt_id'], 'timeout')
	return jsonify(session_to_dict(session))

@app.route('/_choose_arm')
def give_reward():
	if 'room_id' in session and 'uid' in session:
		print('give_reward', session)

		# Default values
		room = Room.query.get(session['room_id'])
		if 'game' not in session:
			session['game'] = room.game
		if 'trial' not in session:
			session['trial'] = room.trial
		if 'scores' not in session or not session['scores']:
			session['scores'] = json.loads(room.scores_strs)
		if 'score' not in session or not session['score']:
			session['score'] = room.score
		session['next_game_bool'] = False

		uid = session['uid']
		game = room.game
		trial = room.trial

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

			# Collaborative setting: update room
			if "experimental_condition" not in session:
				session['experimental_condition'] = room.experimental_condition
			p1_observability, p2_observability = experimental_conditions[session['experimental_condition']]

			is_p1 = True
			if session['uid'] == room.p2_uid:
				is_p1 = False
			if is_p1:
				room.next_turn_uid = room.p2_uid
				session['next_turn_uid'] = room.p2_uid
			else:				
				room.next_turn_uid = room.p1_uid
				session['next_turn_uid'] = room.p1_uid

			# Record user's choice and reward to db, for trials within scope (don't record accidental requests from spamming keys)
			if trial <= num_trials:
				# Observability for this past trial
				if is_p1:
					is_observable = bool(p1_observability[game - 1][trial - 1])
					partner_is_observable = bool(p2_observability[game - 1][trial - 1])
				else:
					is_observable = bool(p2_observability[game - 1][trial - 1])
					partner_is_observable = bool(p1_observability[game - 1][trial - 1])

				p1_is_observable = bool(p1_observability[game - 1][trial - 1])
				p2_is_observable = bool(p2_observability[game - 1][trial - 1])
				room.p1_is_observable = p1_is_observable
				room.p2_is_observable = p2_is_observable
				p1_score = room.p1_score
				p2_score = room.p2_score
				p1_score = p1_score + reward if p1_is_observable else p1_score
				p2_score = p2_score + reward if p2_is_observable else p2_score
				room.p1_score = p1_score
				room.p2_score = p2_score

				if is_p1:
					session['is_observable'] = p1_is_observable
					session['partner_is_observable'] = p2_is_observable
					session['score'] = p1_score
				else:
					session['is_observable'] = p2_is_observable
					session['partner_is_observable'] = p1_is_observable
					session['score'] = p2_score

				move = Move(uid=uid, chosen_arm=chosen_arm, trial=trial, game=game, reward=reward, score=session['score'], is_observable=session['is_observable'])
				print('stored', move)
				db.session.add(move)
				db.session.commit()
				
				# Update true score
				true_score = room.score + reward
				room.score = true_score
				print('true scores are', json.loads(room.scores_strs), 'true score is', true_score, '// p1 sees', p1_score, '// p2', p2_score)
				print("choose arm - scores", session['scores'], json.loads(room.scores_strs))
				print('p1 and p2 scores....', json.loads(room.p1_scores_strs), json.loads(room.p2_scores_strs))

				# Finished game; record score under scores 
				if trial == num_trials:
					true_scores = json.loads(room.scores_strs)
					true_scores.append(true_score)
					session['scores'] = true_scores
					room.scores_strs = json.dumps(true_scores)
					
					# Saving this to db for quick glance qualitative analysis, but display true scores to p1 & p2
					p1_scores = json.loads(room.p1_scores_strs)
					p1_scores.append(p1_score)
					room.p1_scores_strs = json.dumps(p1_scores)
					
					p2_scores = json.loads(room.p2_scores_strs)
					p2_scores.append(p2_score)
					room.p2_scores_strs = json.dumps(p2_scores)

					print('updated true scores, p1 and p2 scores....', json.loads(room.scores_strs), json.loads(room.p1_scores_strs), json.loads(room.p2_scores_strs))
					db.session.commit()

			# Finished game (or over)
			if trial >= num_trials:
				if game >= num_games:
					# Give completion code, storing value in room for partner to query
					if not room.completion_code:
						code = create_completion_code(session['amt_id'], 'completed')
						room.completion_code = code
						db.session.commit()
					else:
						code = room.completion_code 
					session['completion_code'] = code
				else:
					session['next_game_bool'] = True
			room.time_last_move = datetime.utcnow()
			room.chosen_arm = session['chosen_arm']
			room.reward = session['reward']
			room.trial = session['trial']
			room.game = session['game']
			room.next_game_bool = session['next_game_bool']
			db.session.commit()

		# Requery state b/c of repeated requests (collaborative setting only) 
		else:
			print('avoided duplicating', session)
			room = Room.query.get(session['room_id'])
			if room.p1_uid == session['uid']:
				session['score'] = room.p1_score
			else:
				session['score'] = room.p2_score
			session['scores'] = json.loads(room.scores_strs)
			session['game'] = room.game
			session['trial'] = room.trial
			session['reward'] = room.reward
			session['chosen_arm'] = room.chosen_arm
			session['completion_code'] = room.completion_code
			session['next_game_bool'] = room.next_game_bool
		return jsonify(session_to_dict(session))

@app.route('/_get_true_score')
def get_true_score():
	if 'trial' in session and 'room_id' in session:
		print('get_true_score', session)

		# Return true score if trial is num_trials
		if session['trial'] >= num_trials:
			room = Room.query.get(session['room_id'])
			return jsonify(true_score=room.score)

@app.route('/_choose_arm_single')
def give_reward_single():
	if 'uid' in session:
		print('give_reward_single', session)

		# Default values
		if 'game' not in session:
			session['game'] = 1
		if 'trial' not in session:
			session['trial'] = 1
		if 'score' not in session or not session['score']:
			session['score'] = 0
		uid = session['uid']
		game = session['game']
		trial = session['trial']
		score = session['score']

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
		if trial <= num_trials:
			score += reward
			session['score'] = score
			move = Move(uid=uid, chosen_arm=chosen_arm, trial=trial, game=game, reward=reward, score=score)
			db.session.add(move)
			db.session.commit()
		session['next_game_bool'] = False
		if trial >= num_trials:
			session['next_game_bool'] = True

		return jsonify(session_to_dict(session))

@app.route('/_create_user')
def insert_user():
	print('insert_user', session)
	amt_id = request.args.get('amt_id')

	# Create user in db
	user = Worker(amt_id=amt_id, room_id=0, is_ready=False, timeout=False)
	db.session.add(user)
	db.session.commit()

	uhash = hash(user)
	session['amt_id'] = amt_id
	session['uhash'] = uhash

	# Return vars for debugging on client side
	return jsonify(session_to_dict(session))

@app.route('/_waiting_completion_code')
def make_waiting_completion_code():
	if 'amt_id' in session:
		print('make_waiting_completion_code', session)
		session['waiting_code'] = create_completion_code(session['amt_id'], 'waiting')
		return jsonify(session_to_dict(session))

@app.route('/_timeout_completion_code')
def make_timeout_completion_code():
	if 'amt_id' in session:
		print('make_timeout_completion_code', session)
		session['timeout_code'] = create_completion_code(session['amt_id'], 'timeout')
		return jsonify(session_to_dict(session))


@app.route('/_advance_next_game')
def advance_next_game():
	if 'uid' in session and 'room_id' in session and 'game' in session:
		room = Room.query.get(session['room_id'])
		last_move = Move.query.filter_by(uid=session['uid']).order_by(Move.id.desc()).first()
		last_game = last_move.game 
		next_game = last_game + 1

		# Reset observability
		p1_observability, p2_observability = experimental_conditions[session['experimental_condition']]
		if session['uid'] == room.p1_uid:
			is_observable = bool(p1_observability[session['game'] - 1][0]) 
			room.p1_is_observable = is_observable
		else:
			is_observable = bool(p2_observability[session['game'] - 1][0])
			room.p2_is_observable = is_observable
		session['is_observable'] = is_observable

		# You advanced first
		if room.game != next_game:
			room.score = 0
			room.p1_score = 0
			room.p2_score = 0
			room.time_last_move = datetime.utcnow()
			room.chosen_arm = None
			room.reward = None
			room.trial = 1
			room.game = last_game + 1
			room.next_game_bool = False
			db.session.commit()

			session['next_game_bool'] = False
			session['trial'] = 1
			session['game'] = next_game
			session['reward'] = None
			session['chosen_arm'] = None
			session['score'] = 0
		# Partner advanced first and already started/chose an arm
		else:
			room.time_last_move = datetime.utcnow()
			db.session.commit()

			session['next_game_bool'] = room.next_game_bool
			session['trial'] = room.trial
			session['game'] = room.game
			session['reward'] = room.reward
			session['chosen_arm'] = room.chosen_arm
			session['score'] = room.p1_score if session['uid'] == room.p1_uid else room.p2_score

		return jsonify(session_to_dict(session))


@app.route('/_enter_waiting')
def enter_waiting_room():
	# Flag that user is waiting w/ defaults
	if 'uid' in session:
		print('enter_waiting_room', session)
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
		return jsonify(session_to_dict(session))

@app.route('/_waiting_ping')
def check_waiting_room():
	if 'uid' in session:
		print('check_waiting_room', session)

		# Record activity timestamp
		session['last_active'] = datetime.utcnow()
		user = Worker.query.get(session['uid'])
		user.last_active = session['last_active']
		db.session.commit()

		# Check if user already has room id and already matched
		room_id = user.room_id
		if room_id != 0:
			session['is_ready'] = False
			user.is_ready = False
			db.session.commit()

			session['room_id'] = room_id
			room = Room.query.get(room_id)
			session['next_turn_uid'] = room.next_turn_uid
			session['experimental_condition'] = room.experimental_condition
		# Check waiting room for a partner
		else:
			partner = Worker.query.filter(Worker.id != session['uid']).filter(Worker.last_active >= session['last_active'] - timedelta(seconds=20)).filter_by(room_id=0, is_ready=True).first()
			if partner is not None:
				print(user, "partnered up with ", partner)

				# Create next room
				partner_uid = partner.id
				timestamp = datetime.utcnow()
				
				# Don't randomize as this changes controlling observability across pairs
				session['next_turn_uid'] = user.id
				
				# Set experimental condition randomly
				# experimental_condition = random.choice(list(experimental_conditions.keys()))
				# Fix experimental condition
				# experimental_condition = "control"
				# experimental_condition = "partial"
				experimental_condition = "partial_asymmetric"
				session['experimental_condition'] = experimental_condition

				room = Room(next_turn_uid=user.id, p1_uid=user.id, p2_uid=partner_uid, \
					time_last_move=timestamp, chosen_arm=-1, trial=1, game=1, reward=None, \
					completion_code=None, p1_score=0, p2_score=0, p1_scores_strs=json.dumps([]), p2_scores_strs=json.dumps([]), \
					experimental_condition=experimental_condition, score=0, scores_strs=json.dumps([]))
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
		return jsonify(session_to_dict(session))

@app.route('/')
def index():
	print('index', session)
	if 'amt_id' in session:
		uhash = hash(session['amt_id'])
		session['num_games'] = num_games
		session['num_trials'] = num_trials		
		if 'uid' in session:
			user = Worker.query.get(session['uid'])
		else:
			user = Worker.query.filter_by(amt_id=session['amt_id']).order_by(Worker.id.desc()).first()
			session['uid'] = user.id
		if user.timeout:
			session.clear()
			info_vars = { 'num_games': num_games, 'num_trials': num_trials }
			return render_template('index.html', vars=info_vars)
		session_vars = session_to_dict(session)
		if 'timeout' in session and session['timeout']:
			# Partner timed out
			return render_template('timeout.html', vars=session_vars)
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
			info_vars = { 'num_games': num_games, 'num_trials': num_trials }
			return render_template('index.html', vars=info_vars)
	else:
		info_vars = { 'num_games': num_games, 'num_trials': num_trials }
		return render_template('index.html', vars=info_vars)

app.secret_key = '\x96\xca\xd6\xe5\xa9\\\x08\xa2\x08\xdf\x82\xc2\xcc\xfe'








































