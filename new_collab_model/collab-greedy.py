import os, random, csv, itertools
from greedy import Greedy
# from wsls import WSLS
import pandas as pd
import numpy as np
from dbnpgreedy import data, db_headers
from numpy.random import beta, shuffle
from scipy.misc import comb
from collections import defaultdict
import itertools, os, time
from multiprocessing import Pool

class GreedyGame(object):
	def __init__(self, turns, arms=[1, 2, 3, 4], i_turn=0, epsilon=0):
		self.i_turn = i_turn
		self.arms = arms
		self.turns = turns
		self.epsilon = epsilon # currently not used to find values of arms 
		self.chosen_arms = None
		self.rewards = None
		self.visibility = None
	def i_player(self):
		return self.turns[self.i_turn]
	def stats(self):
		i_player = self.i_player()
		# Hide rewards
		hidden_rewards = np.where(self.visibility["visibility_p{}".format(i_player)], self.rewards, -1)
		ret = np.zeros((1, len(self.arms)))
		self.chosen_arms = np.array(self.chosen_arms)
		for arm in self.arms:
			# Count pulls regardless of visibility (vs. Only count pulls that were observed)
			pulls = np.sum(np.where(self.chosen_arms == arm, 1, 0))
			successes = np.where(self.chosen_arms == arm, hidden_rewards, 0)
			# Hidden pulls
			hidden_pulls = np.sum(successes[successes == -1])
			# Only counting pulls that were observed
			pulls = pulls + hidden_pulls # hidden pulls are negative
			if successes.any():
				successes = np.sum(successes[successes != -1])
			else:
				successes = 0
			val = 0
			if pulls > 0:
				val = successes / pulls
			ret[:,arm-1] = val
		return ret

def compute_stats(data):
	turns = data[db_headers['player']]
	game = GreedyGame(turns)
	ret = []
	for i in range(len(turns)):
		game.i_turn = i
		game.chosen_arms = data[db_headers['chosen_arm']][:i]
		game.rewards = data[db_headers['reward']][:i]
		visibility_p0 = data[db_headers['visibility_p0']][:i]
		visibility_p1 = data[db_headers['visibility_p1']][:i]
		game.visibility = { "visibility_p0": visibility_p0, "visibility_p1": visibility_p1 }
		game_stats = game.stats()
		# stats_headers = ['room', 'game', 'condition', 'player', 'chosen_arm'] + ['arm{}']
		base_stats = [ data[db_headers['room']], data[db_headers['game']], i, data[db_headers['condition']], game.i_player(), data[db_headers['chosen_arm']][i] ]
		for i in range(len(game.arms)):
			stats = base_stats + [i, list(game_stats[0])[i]]
			ret.append(stats)
	print(data[db_headers['room']], data[db_headers['game']], time.time())
	return ret

def analyze(stats):
	best = stats.groupby(['room', 'game', 'move'])['value'].max().rename('best')
	stats = stats.join(best, on=['room', 'game', 'move'])
	stats = stats.assign(winner=stats.apply(lambda row: 1. if row['value']>=row['best']-1e-5 else 0., axis=1))
	winners = stats.groupby(['room', 'game', 'move'])['winner'].sum().rename('others')
	stats = stats.join(winners, on=['room', 'game', 'move'])
	stats = stats.assign(agreement=stats['winner']/stats['others'])
	print(stats)
	stats = stats[stats['chosen_arm']==stats['arm']]
	# print(stats.groupby(['room', 'game', 'condition'])['agreement'].mean())
	# print(stats.groupby(['room', 'condition'])['agreement'].mean())
	print(stats.groupby(['condition'])['agreement'].mean())

if __name__=='__main__':
	start_time = time.time()
	print("starting other", time.time())
	if not os.path.exists('stats_greedy.csv'):
		datas = data()
		print('finished getting data; took ', time.time() - start_time, 'seconds')
		pool = Pool(3)
		results = []
		for stats in pool.map(compute_stats, datas):
			results.append(stats)
		with open('stats_greedy.csv', 'w') as f:
			writer = csv.writer(f)
			writer.writerow(['room', 'game', 'move', 'condition', 'player', 'chosen_arm', 'arm', 'value'])
			for i, room in enumerate(results):
				for j, game in enumerate(room):
					writer.writerow(game)
	results = pd.read_csv('stats_greedy.csv')
	# with open('stats_greedy.csv', 'r') as f:
	# 	r = csv.DictReader(f)
	# 	for row in r:
	# 		print(row)
	# 		print("==================")
	analyze(results)
	# # print(results)
