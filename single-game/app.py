from flask import Flask, jsonify, render_template, request
import numpy as np
import constants
import random

app = Flask(__name__)

@app.route('/_choose_arm')
def give_reward():
	k = request.args.get('k', 0, type=int) - 1

	# Sample from arm's distribution? Or have real reward rates
	# reward = np.random.beta(alpha, beta)
	r = 1 if random.random() < constants.reward_rates[k] else 0
	return jsonify(reward=r)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()