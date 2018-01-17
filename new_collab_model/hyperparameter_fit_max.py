import csv, time, random, os
import pandas as pd
from collections import defaultdict
import numpy as np
import pprint

if __name__=='__main__':
    print("starting", time.time())

    condition_counts = defaultdict(int)
    condition_rooms = defaultdict(list)
    with open('intermediate_stats.csv', 'r') as file:
        reader = csv.DictReader(file)
        rooms = []
        for row in reader:
            if row['room'] not in rooms and row['room'] != 'room':
                rooms.append(row['room'])
                condition_counts[row['condition']] += 1
                condition_rooms[row['condition']].append(row['room'])
    print(len(rooms), condition_rooms)
    print(condition_counts)

    stats = pd.read_csv('all_agreements.csv')
    print(stats.count()[0], "iterations of parameter sets")

    max_stats = stats.max(axis=0)

    # Get best params for first game
    first_game_indices = stats.filter(regex='game_room_agreement_\(.*,\s0\)').idxmax(axis=0)
    rooms_to_indices = pd.DataFrame(data=first_game_indices, columns=['stats_index'])
    rooms_to_indices = rooms_to_indices.rename(index=lambda x: x.strip('game_room_agreement_(').strip(', 0)'))
    rooms_to_indices = rooms_to_indices.assign(room_id=rooms_to_indices.index.values)

    first_game_params = stats.ix[first_game_indices].filter(regex='param_')
    rooms_to_params = pd.merge(rooms_to_indices, first_game_params, left_on='stats_index', right_on=first_game_params.index.values)
    rooms_to_params = rooms_to_params.drop_duplicates(subset=['stats_index', 'room_id'])
    rooms_to_params = rooms_to_params.rename(index=rooms_to_params['room_id'])

    # Compute params on later games, and get average agreement per room and overall
    room_agreements = defaultdict(int)
    rooms_to_params_np = rooms_to_params.values

    for row in rooms_to_params_np:
        stats_index = row[0]
        room = row[1]
        param_discount_factor = row[2]
        param_exploit_weight = row[3]
        param_w1 = row[4]
        param_w2 = row[5]
        stats_with_params = stats[(stats['param_discount_factor']==param_discount_factor) & \
                            (stats['param_exploit_weight']==param_exploit_weight) & \
                            (stats['param_w1']==param_w1) & \
                            (stats['param_w2']==param_w2)]
        # print('game_room_agreement_\(' + room + ',\s[^0]\)')
        game_room_agreements = stats_with_params.filter(regex='game_room_agreement_\(' + room + ',\s[^0]\)')
        if game_room_agreements.shape[1] != 9:
            print("Incomplete analysis in intermediate_stats.csv for room {}. Only {} games analyzed.".format(room, game_room_agreements.shape[1] + 1))
            if room in condition_rooms['control']:
                print("in condition control")
            if room in condition_rooms['partial']:
                print("in condition partial")
            if room in condition_rooms['partial_asymmetric']:
                print("in condition asymmetric")
            continue
        room_agreements[room] = game_room_agreements.mean(axis=1).values[0]
    
    mean_agreement = float(sum(room_agreements.values())) / len(room_agreements)

    print("Average agreement per room:")
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(room_agreements)
    print("Average agreement overall: {}".format(mean_agreement))

    # Compute agreement on fitting params to all computed stats (vs. just on 1st game)
    # agreements = {}
    # agreements['agreement_by_condition'] = max_stats.filter(regex='condition_agreement').mean()
    # agreements['agreement_by_room'] = max_stats.filter(regex='room_agreement').mean()
    # agreements['agreement_by_game_room'] = max_stats.filter(regex='game_room_agreement').mean()
    # agreements['agreement_by_game'] = max_stats.filter(regex='game_agreement').mean()

    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(agreements)



