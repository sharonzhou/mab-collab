from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from app import app, db
from app.models import *
from app.constant import *
import numpy as np
import random, string

@app.route('/_choose_arm')
def give_reward():
	k = request.args.get('k', type=int) - 1
	game = request.args.get('game', type=int)
	r = 1 if random.random() < reward_rates[game - 1][k] else 0
	
	# Record user's choice and reward to db
	uid = request.args.get('uid', type=int)
	trial = request.args.get('trial', type=int)
	move = Move(uid=uid, chosen_arm=k, trial=trial, game=game, reward=r)
	db.session.add(move)
	db.session.commit()
	
	return jsonify(reward=r, uid=uid)

@app.route('/_create_user')
def insert_user():
	amt_id = request.args.get('amt_id')

	# Create user in db
	user = Worker(amt_id=amt_id)
	db.session.add(user)
	db.session.commit()
	uid = Worker.query.order_by(Worker.id.desc()).first().id

	return jsonify(uid=uid)

@app.route('/_completion_code')
def make_completion_code():
	uid = request.args.get('uid')
	code = ''.join(random.sample(string.ascii_letters + string.digits, 3)) + str(uid) + ''.join(random.sample(string.ascii_letters + string.digits, 3)) 	
	return jsonify(code=code)

@app.route('/play/<uid>')
def play(uid):
	return render_template('play.html', uid=uid)

@app.route('/')
def index():
	return render_template('index.html')
