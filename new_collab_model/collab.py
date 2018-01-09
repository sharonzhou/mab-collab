import pandas as pd
from db import data, COLUMNS
from numpy.random import beta, shuffle
from scipy.misc import comb
from collections import defaultdict
import itertools
from multiprocessing import Pool
import os

# Moves are stored as Pandas dataframe

def filter_for_player(moves, i_player): # Returns sublist of moves visible to i_player
    return moves[moves['visibility'].apply(lambda v: v[i_player])]

def hide_for_player(moves, i_player): # Replaces the rewards not visible to i_player by NaN
    moves = moves.copy()
    # Sharon: [question]: why is there axis=1? print here
    moves['reward'] = moves.apply(lambda row: row['reward'] if row['visibility'][i_player] else None, axis=1)
    return moves

def possibilities(moves, belief): # Generates all possible values for hidden rewards according to belief
    # Sharon [reiterating]: so these are the moves with unseen rewards? then we want to hypothetically consider all partitions of S/F with them
    unknown_moves = moves[moves['reward'].isna()]
    # Sharon: this means that for a given arm, there will be at least one group. for 'control' there should be 1 group per arm (since visibility is all true)
    # Sharon: 'real' is a boolean value of whether this df is historical real data or hypothetical.
    # Sharon: grouping by visibility means that we have separate groups for what's seen and unseen
    groups = unknown_moves.groupby(['arm', 'visibility', 'real']) #In each group only the number of success/failures matter (not the order of them), so we can generate all possibilities based on number of successes in each group. 'real' makes sure the hypothetical moves are not grouped with the historical real moves since we need to consider all possibilities for the hypothetical move.
    # Sharon: this is for all permutations of n_heads across the groups
    # Sharon [question]: why are we including the 'real'=True groups with the hypothetical ones ('real'=False) here? or are they never passed together to this function?
    # Sharon: there is a +1 because we can have n_heads = size of group (in which case there are 0 tails)
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
    # Sharon [question]: initialize belief per arm w/ Beta(1,1) * P(moves)
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
        self.condition = condition
        if condition not in ['control', 'partial', 'partial_asymmetric']:
            raise Exception('Game condition not recognized')
    # Sharon: using a generator instead of just returning a list b/c hypothetical function, defined below, yields a move
    def possibilities(self): # Generate possible visibilities
        if self.condition=='control':
            yield 1., (True, True)
        elif self.condition=='partial':
            yield 2./3., (True, False)
            yield 1./3., (True, True)
        # Sharon: in our new experiment with independent p's, this should be:
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
        # Sharon: turns is [0,1,0,1,...]
        self.turns = turns
        self.arms = arms
        self.n_players = max(turns)+1
        self.visibility = visibility
        # Sharon: COLUMNS is from db
        self.moves = pd.DataFrame(columns=COLUMNS)
    def i_player(self):
        # Sharon: is it len(self.moves) and not len(self.moves) - 1 because initially len(moves) = 0; moves are added on after i_player() is called
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
            # Sharon: for each hypoth. outcome of an arm, we take the current player's belief to get the predicted reward
            for p1, move in self.hypothetical(arm):
                moves = self.moves.append(move)
                player_view = hide_for_player(moves, i_player)
                for p2, possible in possibilities(player_view, Belief(player_view)):
                    # Sharon: extend return object 
                    # Sharon: add what each player would exploit based on this hypothetical move (previous code did not consider exploit val of _both_ players, but only the next player's turn (in our case, that's always the partner))
                    ret.loc[len(ret)]=[arm, p1*p2, possible.iloc[-1]['reward']]+[Belief(filter_for_player(possible, i)).exploit_value(self.arms) for i in range(self.n_players)]
        for key in ret:
            # Sharon: for the reward and player's exploit values, multiply by join probabilities
            if key not in ['arm', 'p']:
                # Sharon [question]: previous code did not multiply the exploitative value by 'p' - should we be still be doing this here? 
                # Sharon [question cont'd]: On the one hand, I get it that they're dependent on these possible next moves, but on the other hand, in our original formalism/model, we had this exploitative value separate and outside of the hypoth. probability
                # Sharon [remark]: pandas df's are so coool! love how you can not only extract but also do ops on everything in col 'p' like this
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
    first_player = data['moves'].iloc[0]['player']
    turns = [first_player if i%2==0 else 1-first_player for i in range(len(data['moves']))]
    game = Game(turns, visibility=Visibility(data['condition']))
    ret = pd.DataFrame()
    for i in range(len(data['moves'])):
        game.moves = data['moves'].iloc[:i]
        stats = game.stats()
        stats = stats.assign(room=data['room'], game=data['game'], move=i, condition=data['condition'], player=game.i_player(), chosen_arm=data['moves'].iloc[i]['arm'])
        ret = ret.append(stats)
    print(data['room'], data['game'])
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
    if not os.path.exists('stats.csv'):
        datas = [d for d in data()]
        pool = Pool(3)
        results = pd.DataFrame()
        for stats in pool.map(compute_stats, datas):
            results = results.append(stats)
        results.to_csv('stats.csv')
    results = pd.read_csv('stats.csv')
    analyze(results)
    #print(results)
