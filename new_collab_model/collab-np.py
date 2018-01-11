import pandas as pd
import numpy as np
from db import data, COLUMNS
from numpy.random import beta, shuffle
from scipy.misc import comb
from collections import defaultdict
import itertools, os, time
from multiprocessing import Pool

# Moves are stored as numpy matrices

def filter_for_player(moves, i_player): # Returns sublist of moves visible to i_player
    return moves[moves['visibility_p{}'.format(i_player)]]

def hide_for_player(moves, i_player): # Replaces the rewards not visible to i_player by NaN
    moves = np.copy(moves)
    moves['reward'] = moves['reward'] if moves['visibility'][i_player] else None
    return moves

def possibilities(moves, belief): # Generates all possible values for hidden rewards according to belief
    unknown_moves = moves[moves['reward'] == None]
    array([[x] for x in [ list(a[a[:,0]==i,1]) for i in n]])
    n = unique(unknown_moves[:,0])
    groups = np.array([x] for x in [list(unknown_moves[unknown_moves[:,0] == i, 1])] for i in n)
    unknown_moves.groupby(['arm', 'visibility', 'real']) #In each group only the number of success/failures matter (not the order of them), so we can generate all possibilities based on number of successes in each group. 'real' makes sure the hypothetical moves are not grouped with the historical real moves since we need to consider all possibilities for the hypothetical move.
    for ns_heads in itertools.product(*[range(s+1) for s in groups.size()]):
        # Sharon: we start with our known rewards
        rewards = moves['reward'].dropna()
        combs = 1.
        # Sharon: looking at one group and one n_heads val at a time
        for n_heads, (_, group) in zip(ns_heads, groups):
            # Sharon: we will in hypothetical rewards based on n_heads across an unknown group
            # Sharon: the resulting variable rewards will be all known values, followed by hypoth. heads, hypoth. tails for first group, then hypoth. heads, hypoth. tails for next group, etc.
            # Sharon: e.g. rewards = [ known_1 known_0 ... unknown_1 unknown_1 unknown_0 ... unknown_1 unknown_1 unknown_0]
            rewards = rewards.append(group.iloc[:n_heads]['reward'].fillna(1.))
            rewards = rewards.append(group.iloc[n_heads:]['reward'].fillna(0.))
            # Sharon: here (after outer for-loop is over) we consider all the combs from partitions of heads/tails in this group
            # Sharon: incl. overlapping n_heads vals among groups (this differs from previous code, which only looks at vals of n_heads once across all groups)
            combs *= comb(len(group), n_heads)
        possible_moves = moves.copy()
        possible_moves['reward'] = rewards
        assumed = unknown_moves.copy()
        # Sharon: rewards variable accumulates all possible hypoth. combos and these map onto the groups
        assumed['reward'] = rewards
        # Sharon: count zeros and ones per arm? print here
        zeros = assumed[assumed['reward']==0.].groupby('arm').size().rename('zero')
        ones = assumed[assumed['reward']==1.].groupby('arm').size().rename('one')
        # Sharon: ? print here
        stats = pd.concat([zeros, ones], axis=1).fillna(0).astype(int)
        yield combs*belief.probability(stats), possible_moves # Pair of the form (probability, moves)

class Beta(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def mean(self):
        return self.a/(self.a+self.b)
    def __mul__(self, o):
        return Beta(self.a+o.a, self.b+o.b)
    def sample(self):
        return beta(self.a, self.b)
    # Sharon: beta pdf
    def probability(self, one, zero): # This is computing the following probability: sample theta from this beta(a,b), and then sample a bunch of Bernoulli(theta). This is the probability of the first one samples being 1, and the next zero samples being 0.
        ret = 1.
        for i in range(one):
            ret *= (self.a+i)/(self.a+self.b+i)
        # Sharon [question]: shouldn't this look at the next zero samples like this? for i in range(one, one+zero):
        for i in range(zero):
            ret *= (self.b+i)/(self.a+self.b+one+i)
        return ret

class Belief(defaultdict):
    # Sharon: initialize belief per arm w/ Beta(1,1) * P(moves)
    def __init__(self, moves=None):
        # Sharon: init new defaultdicts with Beta(1,1), used when init self[arm] in append()
        defaultdict.__init__(self, lambda: Beta(1, 1))
        if moves is not None:
            # Sharon: using function append() defined below (not built-in function)
            self.append(moves)
    def append(self, moves):
        for arm, cnt in moves[moves['reward']==1.0].groupby('arm').size().items():
            # Sharon: adds cnt to alpha (a) value for ea arm
            self[arm]*=Beta(cnt, 0)
        for arm, cnt in moves[moves['reward']==0.0].groupby('arm').size().items():
            # Sharon: adds cnt to beta (b) value for ea arm
            self[arm]*=Beta(0, cnt)
    def probability(self, stats): # Probability of observing specified sequences of zeros and ones
        ret = 1.
        for arm, row in stats.iterrows():
            # Sharon: not recursive - this probability fcn is for Beta object self[arm]
            ret *= self[arm].probability(row['one'], row['zero'])
        return ret
    def exploit_value(self, arms):
        return max([self[arm].mean() for arm in arms])

class Visibility(object):
    def __init__(self, condition):
        if condition not in ['control', 'partial', 'partial_asymmetric']:
            raise Exception('Game condition not recognized')
        self.condition = condition
        if self.condition=='control':
            self.visibilities = [[1., True, True]]
        elif self.condition=='partial':
            self.visibilities = [[2./3., True, False], [1./3., True, True]]
        elif self.condition=='partial_asymmetric':
            self.visibilities = [[2./9., True, True], [2./9., False, False], [1./9., True, False], [4./9., False, True]]

class Game(object):
    def __init__(self, turns, visibility=Visibility('control'), arms=[1, 2, 3, 4]):
        self.turns = turns
        self.arms = arms
        self.n_players = max(turns)+1
        self.visibility = visibility
        # COLUMNS = ['player', 'arm', 'reward', 'visibility', 'real']
        self.columns = {}
        for i, col in enumerate(COLUMNS):
            self.columns[col] = i
        self.moves = np.zeros((1, len(COLUMNS)))
        self.move_num = 0
        print("self.moves shape", self.moves.shape)
    def players(self):
        print("should be self.turns for players, just # of moves ({}) {}".format(self.moves.shape[0], np.array(self.turns[:self.move_num + 1])))
        return np.array(self.turns[:self.move_num + 1])
    def hypothetical(self, arm): # Generate possible next moves if arm is pulled
        players = self.players()
        moves = [self.visibility.visibilities[0], players, arm, self.visibility.visibilities[1], self.visibility.visibilities[2], 0]
        return moves
    def stats(self, room, game, i_move, condition, i_player, chosen_arm):
        ret_col_headers = ['arm', 'p', 'reward']+['exploit{}'.format(i) for i in range(self.n_players)]
        ret_cols = {}
        for i, header in enumerate(ret_col_headers):
            ret_cols[header] = i
        players = self.players()
        ret = np.zeros((1, len(ret_col_headers)))
        for arm in self.arms:
            # For each hypoth. outcome of an arm, we take the current player's belief to get the predicted reward
            moves = hypothetical(arm)
            player_view = hide_for_player(moves, players[-1])
            poss = possibilities(player_view, Belief(player_view))
            ret = np.array([room, game, i_move, condition, i_player, chosen_arm] + [arm, moves[0]*poss[0], poss[1]] + [Belief(filter_for_player(poss[1], i)).exploit_value(self.arms) for i in range(self.n_players)])
        ret[2:] *= ret[1]
        return ret
    # def value(self):
    #     stats = self.stats()
    #     value = stats['reward'].copy()
    #     for i in range(self.n_players):
    #         value += stats['exploit{}'.format(i)]*discounted_sum(self.turns[len(self.moves)+1:], i)
    #     return value

def compute_stats(data):
    print("compute_stats", time.time())
    first_player = data[db_headers['player'][0]]
    turns = [first_player if i%2==0 else 1-first_player for i in range(len(data[db_headers['player']]))]
    game = Game(turns, visibility=Visibility(data[db_headers['condition']]))
    ret = pd.DataFrame()
    for i in range(len(data[db_headers['player']])):
        # Conversion to np: not really this for game.visibility.visibilities[0]....
        game.moves = np.array([game.visibility.visibilities[0], data[db_headers['player']][:i], data[db_headers['chosen_arm']][:i], data[db_headers['visibility_p0']],[:i] data[db_headers['visibility_p1']][:i], data[db_headers['real']][:i]])
        stats = game.stats(data[db_headers['room']], data[db_headers['game']], i, data[db_headers['condition']], data[db_headers['player'][i]], data[db_headers['chosen_arm'][i]])
        ret = ret.append(stats)
    print(data['room'], data['game'], time.time())
    return ret

def analyze(stats):
    def value(row):
        ret = row['reward']*1. # Next step's reward, 1 could be a parameter we'd need to fit/change
        discount = 1.
        player = row['player']
        for i in range(int(row['move'])+1, 15):
            discount *= .9 # Discount factor, need to fit/change
            player = 1-player
            ret += discount*row['exploit{}'.format(int(player))]*(1. if player==row['player'] else 1.) #weights of partner and me can be fit/changed
        return ret
    stats = stats.assign(value=stats.apply(value, axis=1))
    best = stats.groupby(['room', 'game', 'move'])['value'].max().rename('best')
    stats = stats.join(best, on=['room', 'game', 'move'])
    stats = stats.assign(winner=stats.apply(lambda row: 1. if row['value']>=row['best']-1e-5 else 0., axis=1))
    winners = stats.groupby(['room', 'game', 'move'])['winner'].sum().rename('others')
    stats = stats.join(winners, on=['room', 'game', 'move'])
    stats = stats.assign(agreement=stats['winner']/stats['others'])
    stats = stats[stats['chosen_arm']==stats['arm']]
    print(stats.groupby(['room', 'game', 'condition'])['agreement'].mean())
    print(stats.groupby(['room', 'condition'])['agreement'].mean())
    print(stats.groupby(['condition'])['agreement'].mean())

if __name__=='__main__':
    print("starting", time.time())
    if not os.path.exists('stats.csv'):
        datas = [d for d in data()]
        pool = Pool(3)
        results = pd.DataFrame()
        for stats in pool.map(compute_stats, datas):
            stats.to_csv('running_stats.csv', mode='a')
            results = results.append(stats)
        results.to_csv('stats.csv')
    results = pd.read_csv('stats.csv')
    analyze(results)
    #print(results)
