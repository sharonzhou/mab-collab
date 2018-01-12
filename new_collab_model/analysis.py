import csv, time
import pandas as pd
from collections import defaultdict

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
    print(stats[stats['chosen_arm']!=stats['arm']])
    stats = stats.assign(value=stats.apply(value, axis=1))
    best = stats.groupby(['room', 'game', 'move'])['value'].max().rename('best')
    stats = stats.join(best, on=['room', 'game', 'move'])
    stats = stats.assign(winner=stats.apply(lambda row: 1. if row['value']>=row['best']-1e-5 else 0., axis=1))
    winners = stats.groupby(['room', 'game', 'move'])['winner'].sum().rename('others')
    stats = stats.join(winners, on=['room', 'game', 'move'])
    stats = stats.assign(agreement=stats['winner']/stats['others'])
    # print(stats)
    stats = stats[stats['chosen_arm']==stats['arm']]
    # print(stats)
    # print(stats.groupby(['room', 'game', 'condition'])['agreement'].mean())
    # print(stats.groupby(['room', 'condition'])['agreement'].mean())
    # print(stats.groupby(['condition'])['agreement'].mean())

if __name__=='__main__':
    print("starting", time.time())
    condition_counts = defaultdict(int)
    with open('intermediate_stats.csv', 'r') as file:
        reader = csv.DictReader(file)
        rooms = []
        for row in reader:
            if row['room'] not in rooms and row['room'] != 'room':
                rooms.append(row['room'])
                condition_counts[row['condition']] += 1
    results = pd.read_csv('intermediate_stats.csv')
    analyze(results)

    # print(len(rooms), rooms)
    # print(condition_counts)

