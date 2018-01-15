import pandas as pd
from db import data, COLUMNS
from numpy.random import beta, shuffle
from scipy.misc import comb
from collections import defaultdict
import itertools, os, time
from multiprocessing import Pool

# Moves are stored as Pandas dataframe

def filter_for_player(moves, i_player): # Returns sublist of moves visible to i_player
    return moves[moves['visibility'].apply(lambda v: v[i_player])]

def hide_for_player(moves, i_player): # Replaces the rewards not visible to i_player by NaN
    moves = moves.copy()
    moves['reward'] = moves.apply(lambda row: row['reward'] if row['visibility'][i_player] else None, axis=1)
    return moves

def possibilities(moves, belief): # Generates all possible values for hidden rewards according to belief
    unknown_moves = moves[moves['reward'].isna()]
    groups = unknown_moves.groupby(['arm', 'visibility', 'real']) #In each group only the number of success/failures matter (not the order of them), so we can generate all possibilities based on number of successes in each group. 'real' makes sure the hypothetical moves are not grouped with the historical real moves since we need to consider all possibilities for the hypothetical move.
    for ns_heads in itertools.product(*[range(s+1) for s in groups.size()]):
        rewards = moves['reward'].dropna()
        combs = 1.
        for n_heads, (_, group) in zip(ns_heads, groups):
            rewards = rewards.append(group.iloc[:n_heads]['reward'].fillna(1.))
            rewards = rewards.append(group.iloc[n_heads:]['reward'].fillna(0.))
            combs *= comb(len(group), n_heads)
        possible_moves = moves.copy()
        possible_moves['reward'] = rewards
        assumed = unknown_moves.copy()
        assumed['reward'] = rewards
        zeros = assumed[assumed['reward']==0.].groupby('arm').size().rename('zero')
        ones = assumed[assumed['reward']==1.].groupby('arm').size().rename('one')
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
    def probability(self, one, zero): # This is computing the following probability: sample theta from this beta(a,b), and then sample a bunch of Bernoulli(theta). This is the probability of the first one samples being 1, and the next zero samples being 0.
        ret = 1.
        for i in range(one):
            ret *= (self.a+i)/(self.a+self.b+i)
        for i in range(zero):
            ret *= (self.b+i)/(self.a+self.b+one+i)
        return ret

class Belief(defaultdict):
    def __init__(self, moves=None):
        defaultdict.__init__(self, lambda: Beta(1, 1))
        if moves is not None:
            self.append(moves)
    def append(self, moves):
        for arm, cnt in moves[moves['reward']==1.0].groupby('arm').size().items():
            self[arm]*=Beta(cnt, 0)
        for arm, cnt in moves[moves['reward']==0.0].groupby('arm').size().items():
            self[arm]*=Beta(0, cnt)
    def probability(self, stats): # Probability of observing specified sequences of zeros and ones
        ret = 1.
        for arm, row in stats.iterrows():
            ret *= self[arm].probability(row['one'], row['zero'])
        return ret
    def exploit_value(self, arms):
        return max([self[arm].mean() for arm in arms])

class Visibility(object):
    def __init__(self, condition):
        self.condition = condition
        if condition not in ['control', 'partial', 'partial_asymmetric']:
            raise Exception('Game condition not recognized')
    def possibilities(self): # Generate possible visibilities
        if self.condition=='control':
            yield 1., (True, True)
        elif self.condition=='partial':
            yield 2./3., (True, False)
            yield 1./3., (True, True)
            # yield 2./9., (True, True)
            # yield 2./9., (False, False)
            # yield 1./9., (True, False)
            # yield 4./9., (False, True)
        elif self.condition=='partial_asymmetric':
            yield 2./9., (True, True)
            yield 2./9., (False, False)
            yield 1./9., (True, False)
            yield 4./9., (False, True)
            # yield 2./3., (True, False)
            # yield 1./3., (False, True)

class Game(object):
    def __init__(self, turns, visibility=Visibility('control'), arms=[1, 2, 3, 4]):
        self.turns = turns
        self.arms = arms
        self.n_players = max(turns)+1
        self.visibility = visibility
        self.moves = pd.DataFrame(columns=COLUMNS)
    def i_player(self):
        return self.turns[len(self.moves)]
    def hypothetical(self, arm): # Generate possible next moves if arm is pulled
        i_player = self.i_player()
        for p, visibilities in self.visibility.possibilities():
            move = pd.DataFrame({'player': [i_player], 'arm': [arm], 'reward': [None], 'visibility': [visibilities], 'real': [False]}, index=[len(self.moves)], columns=COLUMNS)
            yield p, move
    def stats(self):
        ret = pd.DataFrame(columns=['arm', 'p', 'reward']+['exploit{}'.format(i) for i in range(self.n_players)])
        i_player = self.i_player()
        for arm in self.arms:
            for p1, move in self.hypothetical(arm):
                moves = self.moves.append(move)
                player_view = hide_for_player(moves, i_player)
                for p2, possible in possibilities(player_view, Belief(player_view)):
                    ret.loc[len(ret)]=[arm, p1*p2, possible.iloc[-1]['reward']]+[Belief(filter_for_player(possible, i)).exploit_value(self.arms) for i in range(self.n_players)]
        for key in ret:
            if key not in ['arm', 'p']:
                ret[key] *= ret['p']
        ret = ret.groupby('arm', group_keys=False).sum()
        ret = ret.reset_index()
        return ret
    # def value(self):
    #     stats = self.stats()
    #     value = stats['reward'].copy()
    #     for i in range(self.n_players):
    #         value += stats['exploit{}'.format(i)]*discounted_sum(self.turns[len(self.moves)+1:], i)
    #     return value

def compute_stats(data):
    print("compute_stats", time.time())
    first_player = data['moves'].iloc[0]['player']
    turns = [first_player if i%2==0 else 1-first_player for i in range(len(data['moves']))]
    game = Game(turns, visibility=Visibility(data['condition']))
    ret = pd.DataFrame()
    for i in range(len(data['moves'])):
        game.moves = data['moves'].iloc[:i]
        stats = game.stats()
        stats = stats.assign(room=data['room'], game=data['game'], move=i, condition=data['condition'], player=game.i_player(), chosen_arm=data['moves'].iloc[i]['arm'])
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
    start_time = time.time()
    print("starting")
    if not os.path.exists('stats.csv'):
        datas = [d for d in data()]
        print('finished getting data; took ', time.time() - start_time, 'seconds')
        pool = Pool(3)
        results = pd.DataFrame()
        for stats in pool.map(compute_stats, datas):
            stats.to_csv('running_stats.csv', mode='a')
            results = results.append(stats)
        results.to_csv('stats.csv')
    results = pd.read_csv('stats.csv')
    analyze(results)
    #print(results)
