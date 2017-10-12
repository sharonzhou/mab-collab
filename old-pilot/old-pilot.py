import csv
from scipy import stats as stats
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl 

practice = []
actual = []

practice.append({'active_player': ['1', '2', '1', '2', '1', '2', '1', '2', '1', '2'], 'human_decision': ['0', '0', '2', '0', '0', '0', '1', '1', '0', '0'], 'agent_decision': [0, 1, 0, 0, 1, 0, 0, 0, 1, 0], 'reward': [26.48, 46.45, -15.04, 59.28, 35.45, 54.87, 24.88, 36.18, 53.87, 33.43], 'reasons': [[(1, "it's the best"), (2, 'I want to test it')], [(2, 'It worked last time'), (1, "haven't tried this one")], [(1, "haven't tried this one"), (2, 'We should test it')], [(2, 'It works every time'), (1, 'I chose this because it did well before')], [(1, 'it was random'), (2, 'it works')], [(2, 'it works every time!'), (1, 'i chose this before and it did well')], [(1, 'never played this one'), (2, 'Want to try it')], [(2, 'It seems to be the best'), (1, 'it did well before ')], [(1, 'it was random'), (2, 'best')], [(2, 'best'), (1, 'this is the best, sharon is the best')]], 'human_cumulative_reward': 0, 'cumulative_reward': 355.85, 'agent_cumulative_reward': 440.76, 'suggestions': [[(1, 0), (2, 0)], [(2, 0), (1, 2)], [(1, 2), (2, 2)], [(2, 0), (1, 0)], [(1, 2), (2, 0)], [(2, 0), (1, 0)], [(1, 1), (2, 1)], [(2, 0), (1, 1)], [(1, 2), (2, 0)], [(2, 0), (1, 0)]], 'confidences': [[(1, 5), (2, 1)], [(2, 4), (1, 1)], [(1, 3), (2, 1)], [(2, 5), (1, 5)], [(1, 5), (2, 5)], [(2, 5), (1, 5)], [(1, 3), (2, 3)], [(2, 5), (1, 5)], [(1, 4), (2, 5)], [(2, 5), (1, 5)]]})
actual.append({'active_player': ['1', '2', '1', '2', '1', '2', '1', '2', '1', '2'], 'agent_decision': [0, 0, 1, 0, 0, 0, 0, 0, 0, 1], 'confidences': [[(1, 1), (2, 5)], [(2, 4), (1, 1)], [(1, 1), (2, 4)], [(2, 5), (1, 5)], [(1, 5), (2, 5)], [(2, 3), (1, 4)], [(1, 4), (2, 4)], [(2, 5), (1, 4)], [(1, 4), (2, 5)], [(2, 4), (1, 4)]], 'reward': [0.55, 0.35, 0.83, 0.47, 0.63, 0.56, 0.55, 0.53, 0.79, 0.67], 'cumulative_reward': 5.930000000000001, 'agent_cumulative_reward': 5.670000000000001, 'human_decision': ['0', '1', '0', '2', '2', '2', '2', '2', '1', '1'], 'reasons': [[(1, 'testing'), (2, 'havent tried this one')], [(2, 'it was random'), (1, 'testing')], [(1, 'testing'), (2, 'i chose this before and it did well')], [(2, 'same as before'), (1, 'to try it')], [(1, 'its the highest'), (2, 'it did well before and im not changing it ')], [(2, 'havent tried this one yet'), (1, 'largest so far')], [(1, 'seems largest'), (2, 'it did well before ')], [(2, 'it did well before i guess'), (1, 'largest')], [(1, 'largest'), (2, 'it was random ')], [(2, 'same as before'), (1, 'seems better')]], 'suggestions': [[(1, 0), (2, 0)], [(2, 1), (1, 1)], [(1, 2), (2, 1)], [(2, 1), (1, 2)], [(1, 0), (2, 1)], [(2, 2), (1, 2)], [(1, 2), (2, 1)], [(2, 0), (1, 2)], [(1, 2), (2, 1)], [(2, 1), (1, 1)]], 'human_cumulative_reward': 0})

practice.append({'active_player': ['1', '2', '1', '2'], 'agent_decision': [0, 0, 0, 0], 'confidences': [[(1, 1), (2, 2)], [(2, 1), (1, 5)], [(1, 4), (2, 1)], [(2, 1), (1, 5)]], 'reward': [0.25, 0.08, 0.44, 0.17], 'human_cumulative_reward': 0.9400000000000001, 'reasons': [[(1, 'sdklfjakl'), (2, 'random')], [(2, 'klsajfgklfs'), (1, "i don't know")], [(1, 'why should i tell you'), (2, 'ti')], [(2, 'uyg'), (1, 'opposite of geza')]], 'human_decision': ['1', '2', '0', '2'], 'agent_cumulative_reward': 1.52, 'suggestions': [[(1, 2), (2, 0)], [(2, 1), (1, 0)], [(1, 1), (2, 0)], [(2, 0), (1, 2)]]})
actual.append({'active_player': ['1', '2', '1', '2', '1', '2', '1', '2', '1', '2'], 'agent_decision': [0, 0, 2, 2, 1, 0, 2, 0, 0, 0], 'confidences': [[(1, 1), (2, 3)], [(2, 3), (1, 1)], [(1, 4), (2, 1)], [(2, 1), (1, 3)], [(1, 3), (2, 1)], [(2, 1), (1, 4)], [(1, 1), (2, 1)], [(2, 1), (1, 3)], [(1, 3), (2, 1)], [(2, 1), (1, 4)]], 'reward': [0.46, 0.9, 0.6, 0.66, 0.98, 1.37, 0.78, 0.32, 0.41, 0.67], 'human_cumulative_reward': 7.150000000000001, 'reasons': [[(1, ''), (2, 'eandom')], [(2, 'random'), (1, '0')], [(1, 'sounds good'), (2, 'hi sharon/1!!!!!111')], [(2, 'fdhsdf'), (1, 'hggf')], [(1, 'random'), (2, '')], [(2, ''), (1, '!')], [(1, 'hfjgy'), (2, '')], [(2, ''), (1, 'jhg')], [(1, 'random'), (2, '')], [(2, ''), (1, 'sdfg')]], 'human_decision': ['2', '0', '0', '0', '0', '0', '0', '0', '0', '1'], 'agent_cumulative_reward': 5.48, 'suggestions': [[(1, 0), (2, 2)], [(2, 1), (1, 0)], [(1, 0), (2, 0)], [(2, 0), (1, 0)], [(1, 1), (2, 1)], [(2, 0), (1, 0)], [(1, 0), (2, 0)], [(2, 0), (1, 1)], [(1, 2), (2, 0)], [(2, 2), (1, 1)]]})

practice.append({'human_decision': ['2', '0', '0', '1'], 'human_cumulative_reward': 1.26, 'agent_cumulative_reward': 1.49, 'reasons': [[(1, 'randomness. plus CS people start counting at zero'), (2, 'Even if we can only pull one arm, it makes more sense for us to diversify, even with our thoughts, to lower risk.')], [(2, 'To test to see if it can do better'), (1, 'bc i said so')], [(1, "because i didn't pick this yet"), (2, "It's clearly the better arm.")], [(2, 'It appears to be the better arm'), (1, 'it is a compromise')]], 'suggestions': [[(1, 0), (2, 2)], [(2, 2), (1, 0)], [(1, 2), (2, 0)], [(2, 0), (1, 1)]], 'active_player': ['1', '2', '1', '2'], 'agent_decision': [0, 0, 0, 0], 'reward': [-0.03, 0.52, 0.44, 0.33], 'confidences': [[(1, 5), (2, 4)], [(2, 3), (1, 5)], [(1, 5), (2, 5)], [(2, 5), (1, 5)]]})
actual.append({'human_decision': ['2', '1', '1', '1', '0', '1', '1', '1', '1', '2'], 'human_cumulative_reward': 7.38, 'agent_cumulative_reward': 3.51, 'reasons': [[(1, 'because CS people start counting at 0'), (2, 'Diversification')], [(2, '53 is middle of range so arm 1 could be slightly better and we have 10 rounds total to find this arm'), (1, 'because teamwork rocks')], [(1, 'because 1 won last time so I should pick a different number'), (2, '1 is likely to have a good distribution')], [(2, 'To test out another arm'), (1, 'because 1 won last time')], [(1, "that's what my teammate said last time"), (2, 'to test it out!')], [(2, "It's a good arm!"), (1, 'he said it would be good')], [(1, 'i am tired of this game'), (2, "It's a good arm!")], [(2, "it's a good arm"), (1, 'because we do medium good when we do this')], [(1, 'to be different'), (2, "It's a good arm!")], [(2, "It's a good arm, although not sure if there's a better one"), (1, 'i am tired of hitting 1')]], 'suggestions': [[(1, 0), (2, 2)], [(2, 1), (1, 1)], [(1, 0), (2, 1)], [(2, 0), (1, 1)], [(1, 0), (2, 0)], [(2, 1), (1, 1)], [(1, 1), (2, 1)], [(2, 1), (1, 1)], [(1, 2), (2, 1)], [(2, 1), (1, 2)]], 'active_player': ['1', '2', '1', '2', '1', '2', '1', '2', '1', '2'], 'agent_decision': [0, 0, 2, 1, 1, 1, 2, 1, 1, 2], 'reward': [0.53, 1.23, 0.81, 0.56, 0.55, 0.79, 1.0, 0.76, 0.6, 0.55], 'confidences': [[(1, 5), (2, 5)], [(2, 2), (1, 5)], [(1, 5), (2, 5)], [(2, 2), (1, 5)], [(1, 3), (2, 2)], [(2, 5), (1, 5)], [(1, 5), (2, 5)], [(2, 5), (1, 5)], [(1, 5), (2, 5)], [(2, 4), (1, 5)]]})

# Cleaning errors and missing vals in data
practice[0]['agent_cumulative_reward'] /= 100.0
practice[0]['cumulative_reward'] /= 100.0
for i, team in enumerate(practice):
	if 'cumulative_reward' in team:
		team['human_cumulative_reward'] = team['cumulative_reward']
for i, team in enumerate(actual):
	if 'cumulative_reward' in team:
		team['human_cumulative_reward'] = team['cumulative_reward']

# Adding demographics information
durim = {
			'male': 1,
			'age': '20s',
			'ethnicity': 'caucasian',
			'education': 'bachelors'
		}
practice[0]['player_1_demographics'] = durim
actual[0]['player_2_demographics'] = durim

mark = {
			'male': 1,
			'age': '30s',
			'ethnicity': 'caucasian',
			'education': 'phd'
		}
practice[0]['player_2_demographics'] = mark
actual[0]['player_1_demographics'] = mark

geza = {
			'male': 1,
			'age': '20s',
			'ethnicity': 'mixed caucasian/asian',
			'education': 'masters'
		}
practice[1]['player_2_demographics'] = geza
actual[1]['player_2_demographics'] = geza

girl = {
			'male': 0,
			'age': '20s',
			'ethnicity': 'asian',
			'education': 'undergrad'
		}
practice[1]['player_1_demographics'] = girl
actual[1]['player_1_demographics'] = girl

naomi = {
			'male': 0,
			'age': '20s',
			'ethnicity': 'caucasian',
			'education': 'undergrad'
		}
practice[2]['player_1_demographics'] = naomi
actual[2]['player_1_demographics'] = naomi

ante = {
			'male': 1,
			'age': '20s',
			'ethnicity': 'asian',
			'education': 'masters'
		}
practice[2]['player_2_demographics'] = ante
actual[2]['player_2_demographics'] = ante


# Plot all moves by game play
# for team in actual:
team = actual[0]

ind = np.arange(len(team['human_decision']))
width = 0.35
data_title = "Decisions vs. Rewards over time"
plt.scatter(ind, team['human_decision'])
# plt.scatter(team['human_decision'], team['reward'])
plt.ylabel("Reward")
plt.title(data_title)
# plt.xticks(ind + width / 2, conditions)
plt.show()





