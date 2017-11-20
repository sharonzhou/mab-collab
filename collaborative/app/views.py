from flask import Flask, jsonify, render_template, request, redirect, url_for, session, escape
from app import app, db
from app.models import *
from app.constant import *
import numpy as np
import random, string

@app.route('/logout')
def logout():
	session.pop('amt_id', None)
	return redirect(url_for('index'))

@app.route('/_next_game')
def next_game():
	session['score'] = 0
	session['trial'] = 1
	session['game'] += 1
	session['reward'] = None
	session['next_game_button'] = False
	return jsonify(uid=session['uid'], game=session['game'], trial=session['trial'], score=session['score'], scores=session['scores'], reward=session['reward'])

@app.route('/_choose_arm')
def give_reward():
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

	# Set default session vars
	session['next_game_button'] = False
	session['completion_code'] = False

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

	# End or next game
	if trial >= 15:
		if trial == 15:
			session['scores'].append(session['score'])

		if game >= 20:
			session['completion_code'] = True
		else:
			session['next_game_button'] = True

	# Next trial
	session['trial'] = trial + 1

	return jsonify(reward=r, uid=uid, trial=session['trial'], game=session['game'], 
		next_game_button=session['next_game_button'], score=session['score'],
		completion_code=session['completion_code'], scores=session['scores'])

@app.route('/_create_user')
def insert_user():
	amt_id = request.args.get('amt_id')

	# Create user in db
	user = Worker(amt_id=amt_id)
	db.session.add(user)
	db.session.commit()

	uhash = hash(user)
	session['amt_id'] = amt_id
	session['uhash'] = uhash

	# Hack: doesn't matter what you pass back, just need to pass back some json
	return jsonify(amt_id=amt_id)

@app.route('/_completion_code')
def make_completion_code():
	if 'amt_id' in session:
		x = session['amt_id'][-1]
		code = ''.join(random.sample(string.ascii_letters + string.digits, 3)) + str(x) + ''.join(random.sample(string.ascii_letters + string.digits, 3)) 	
		return jsonify(code=code)

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
		return render_template('play.html', vars=session_vars)
	else:
		return render_template('index.html')

app.secret_key = '\x96\xca\xd6\xe5\xa9\\\x08\xa2\x08\xdf\x82\xc2\xcc\xfe'








































