import csv, time, random, os
import pandas as pd
from collections import defaultdict
import numpy as np
import pprint

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
    print(len(rooms), rooms)
    print(condition_counts)

    results = pd.read_csv('intermediate_stats.csv')
    stats = pd.read_csv('all_agreements.csv')
    print(stats.count()[0], "iterations of parameter sets")

    max_stats = stats.max(axis=0)

    agreements = {}
    agreements['agreement_by_condition'] = max_stats.filter(regex='condition_agreement').mean()
    agreements['agreement_by_room'] = max_stats.filter(regex='room_agreement').mean()
    agreements['agreement_by_game_room'] = max_stats.filter(regex='game_room_agreement').mean()
    agreements['agreement_by_game'] = max_stats.filter(regex='game_agreement').mean()

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(agreements)



