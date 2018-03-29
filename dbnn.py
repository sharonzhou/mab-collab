import psycopg2
import psycopg2.extras
import constant
import numpy as np
from urllib import parse
import os

COLUMNS = ['player', 'arm', 'reward', 'visibility', 'real']

db_header_names = ['condition', 'room', 'game', 'player', 'chosen_arm', 'reward', 'visibility_p0', 'visibility_p1', 'real']
db_headers = {}
for i, header in enumerate(db_header_names):
    db_headers[header] = i

def data():
    db_url = parse.urlparse(os.environ["DATABASE_URL"])

    connection = psycopg2.connect(
        database=db_url.path[1:],
        user=db_url.username,
        password=db_url.password,
        host=db_url.hostname,
        port=db_url.port
    )

    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('select * from move;')
    moves = cursor.fetchall()
    cursor.execute('select * from worker;')
    workers = cursor.fetchall()
    cursor.execute('select * from room;')
    rooms = cursor.fetchall()

    connection.close()

    X = []
    y = []
    num_games = 10
    num_trials = 40
    results = []
    for room in rooms:
        room_id = room[0]
        p1_uid = room[2]
        p2_uid = room[3]
        condition = room[19]
        scores = room[18].strip('/[/]').split(', ')
        if not scores or len(scores) != num_games:
            continue

        plays = dict()
        for m in moves:
            if m[7] is None:
                continue
            uid = m[1]
            trial = m[3]-1
            game = m[4]-1
            if (game, trial) in plays:
                # print("duplicate play")
                continue
            if not(uid == p1_uid or uid == p2_uid):
                continue
            chosen_arm = m[2]
            reward = m[5]
            plays[(game, trial)] = (reward, chosen_arm, uid)

        prev_game = None
        for (game, trial), (reward, chosen_arm, uid) in sorted(plays.items()):
            game_x = np.full((1, 2*num_trials), -1.)
            if game != prev_game:
                # Reset vals and add empty game to predict chosen arm y
                prev_game = game
                X.append(game_x.tolist()[0])
                game_x_p1 = []
                game_x_p2 = []

            if uid == p1_uid:
                visibility = constant.experimental_conditions[condition][0][game][trial]
                partner_visibility = constant.experimental_conditions[condition][1][game][trial]
                reward_partner = reward
                if not visibility:
                    reward = .5
                elif not partner_visibility:
                    reward_partner = .5
                game_x_p1.append(chosen_arm)
                game_x_p1.append(reward)
                game_x_p2.append(chosen_arm)
                game_x_p2.append(reward_partner)

                game_x_p1_np = np.array(game_x_p1)
                game_x[:,:game_x_p1_np.shape[0]] = game_x_p1_np
                # print('p1', game_x_p1_np, game_x_p1_np.shape[0])

            elif uid == p2_uid:
                visibility = constant.experimental_conditions[condition][1][game][trial]
                partner_visibility = constant.experimental_conditions[condition][0][game][trial]
                reward_partner = reward
                if not visibility:
                    reward = .5
                elif not partner_visibility:
                    reward_partner = .5
                game_x_p2.append(chosen_arm)
                game_x_p2.append(reward)
                game_x_p1.append(chosen_arm)
                game_x_p1.append(reward_partner)

                game_x_p2_np = np.array(game_x_p2)
                game_x[:,:game_x_p2_np.shape[0]] = game_x_p2_np
                # print('p2', game_x_p2_np, game_x_p2_np.shape[0])
            
            # Don't put last round stuff in X
            if trial != num_trials - 1:
                X.append(game_x.tolist()[0])
            y.append(chosen_arm)

    return X, y

if __name__=='__main__':
    X, y = data()
    data = np.array([X, y])
    np.save('datann.npy', data)

