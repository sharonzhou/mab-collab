import psycopg2
import psycopg2.extras
import constant
import pandas as pd

COLUMNS = ['player', 'arm', 'reward', 'visibility', 'real']

def data():
    connection = psycopg2.connect(
        database='collab',
        user='dsadigh',
        password='',
        host='localhost',
        port=''
    )

    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('select * from move;')
    moves = cursor.fetchall()
    cursor.execute('select * from worker;')
    workers = cursor.fetchall()
    cursor.execute('select * from room;')
    rooms = cursor.fetchall()

    connection.close()

    for room in rooms:
        room_id = room[0]
        p1_uid = room[2]
        p2_uid = room[3]
        condition = room[19]
        scores = room[18].strip('/[/]').split(', ')
        if not scores or len(scores) != 20:
            continue
        plays = dict()
        for m in moves:
            if m[7] is None:
                continue
            uid = m[1]
            trial = m[3]-1
            game = m[4]-1
            chosen_arm = m[2]
            reward = m[5]
            if uid == p1_uid or uid == p2_uid:
                if (game, trial) in plays:
                    continue
                v1 = constant.experimental_conditions[condition][0][game][trial]
                v2 = constant.experimental_conditions[condition][1][game][trial]
                player = 0 if uid==p1_uid else 1
                plays[(game, trial)] = (player, chosen_arm, reward, v1==1, v2==1)
        for i in range(20):
            result = pd.DataFrame({
                'player': [plays[i, j][0] for j in range(15)],
                'arm': [plays[i, j][1] for j in range(15)],
                'reward': [float(plays[i, j][2]) for j in range(15)],
                'visibility': [(plays[i, j][3], plays[i, j][4]) for j in range(15)],
                'real': [True for j in range(15)]
            }, columns=COLUMNS)
            yield {
                'condition': condition,
                'room': room_id,
                'game': i,
                'p0_uid': p1_uid,
                'p1_uid': p2_uid,
                'moves': result
            }

if __name__=='__main__':
    for x in data():
        print(x)
