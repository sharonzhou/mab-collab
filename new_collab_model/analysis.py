import csv, time, random, os
import pandas as pd
from collections import defaultdict
from multiprocessing import Pool
import multiprocessing 

num_trials = 40

def compute_value(row, discount_factor, exploit_weight, w1, w2):
    """
    computes value of the row (move up until this time) based on parameters

    parameters to fit:
        discount_factor: discount factor on partner's info gain and my info gain. discount = 0 is greedy
        exploit_weight: how much exploit value matters
        w1: how much I care about my own info gain
        w2: how much I care about my partner's info gain
    """

    # exploit_value is the exploitative value of the arm
    exploit_value = row['reward']
    ret = exploit_value * exploit_weight

    # discount is the cumulative discount on prior moves
    discount = 1.
    player = row['player']   

    for i in range(int(row['move'])+1, num_trials):
        discount *= discount_factor
        player = 1-player
        ret += discount*row['exploit{}'.format(int(player))]*(w1 if player==row['player'] else w2) #weights of partner and me can be fit/changed
    return ret

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

    stats = pd.read_csv('intermediate_stats.csv')

    def fit_hyperparameters(pool, best_agreement=None, best_params=None):
        """ 
        sweeps hyperparameter values by random selection of param vals in range. all param ranges have range of [0, 1] support.
        """
        print("Starting pool", pool)
        iteration = 0
        best_agreement = best_agreement
        best_params = best_params

        if best_agreement is not None:
            print("Best agreement before this batch is {} with params {}".format(best_agreement, best_params))
        
        while True:
        # while iteration < 5:
            print("======================== Pool {}, iteration {} ========================".format(pool, iteration))

            # Select random param vals 
            discount_factor = random.random()
            exploit_weight = random.random()
            w1 = random.random()
            w2 = random.random()        

            # Compute agreement
            compute_stats = stats.copy()
            compute_stats = compute_stats.assign(value=compute_stats.apply(compute_value, args=(discount_factor, exploit_weight, w1, w2), axis=1))
            best = compute_stats.groupby(['room', 'game', 'move'])['value'].max().rename('best')
            compute_stats = compute_stats.join(best, on=['room', 'game', 'move'])
            compute_stats = compute_stats.assign(winner=compute_stats.apply(lambda row: 1. if row['value']>=row['best']-1e-5 else 0., axis=1))
            winners = compute_stats.groupby(['room', 'game', 'move'])['winner'].sum().rename('others')
            compute_stats = compute_stats.join(winners, on=['room', 'game', 'move'])
            compute_stats = compute_stats.assign(agreement=compute_stats['winner']/compute_stats['others'])
            compute_stats = compute_stats[compute_stats['chosen_arm']==compute_stats['arm']]

            agreement = compute_stats['agreement'].mean()
            condition_agreement = compute_stats.groupby(['condition'])['agreement'].mean()
            room_agreement = compute_stats.groupby(['room'])['agreement'].mean()
            game_room_agreement = compute_stats.groupby(['room', 'game'])['agreement'].mean()
            game_agreement = compute_stats.groupby(['game'])['agreement'].mean()

            data = {}
            data['agreement'] = [agreement]
            for key in condition_agreement.keys():
                data['condition_agreement_' + str(key)] = condition_agreement[key]
            for key in room_agreement.keys():
                data['room_agreement_' + str(key)] = room_agreement[key]
            for key in game_room_agreement.keys():
                data['game_room_agreement_' + str(key)] = game_room_agreement[key]
            for key in game_agreement.keys():
                data['game_agreement_' + str(key)] = game_agreement[key]

            data['param_discount_factor'] = [discount_factor]
            data['param_exploit_weight'] = [exploit_weight]
            data['param_w1'] = [w1]
            data['param_w2'] = [w2]

            recorded_stats = pd.DataFrame(data=data)
            if os.path.exists('all_agreements.csv'):
                recorded_stats.to_csv('all_agreements.csv', mode='a', header=False)
            else:
                recorded_stats.to_csv('all_agreements.csv')

            print("Agreement {} with parameters {}".format(data['agreement'], { "discount_factor": discount_factor, "exploit_weight": exploit_weight, "w1": w1, "w2": w2 }))

            # Save best agreement and its params
            if best_agreement is None or data['agreement'] > best_agreement:
                best_agreement = data['agreement']
                best_params = { "discount_factor": discount_factor, "exploit_weight": exploit_weight, "w1": w1, "w2": w2 }
                print("Found new best agreement {} with parameters {}".format(best_agreement, best_params))

            iteration += 1

    cpu_count = multiprocessing.cpu_count()
    pool = Pool(cpu_count)
    res = pool.map(fit_hyperparameters, range(cpu_count))


