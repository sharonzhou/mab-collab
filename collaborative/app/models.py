from app import db
from sqlalchemy_utils import ScalarListType

class Worker(db.Model):
	id = db.Column(db.Integer(), primary_key=True)
	amt_id = db.Column(db.String(512))
	room_id = db.Column(db.Integer(), nullable=True)
	is_ready = db.Column(db.Boolean())
	last_active = db.Column(db.DateTime())
	timeout = db.Column(db.Boolean())

	def __repr__(self):
		return "<User {}: {}>".format(self.id, self.amt_id)

class Move(db.Model):
	id = db.Column(db.Integer(), primary_key=True)
	uid = db.Column(db.Integer(), db.ForeignKey("worker.id"),
        nullable=False)
	chosen_arm = db.Column(db.Integer())
	trial = db.Column(db.Integer())
	game = db.Column(db.Integer())
	reward = db.Column(db.Integer())
	score = db.Column(db.Integer())
	is_observable = db.Column(db.Boolean())

	def __repr__(self):
		return "<Move {} by {} on arm {} for game {} trial {} with reward {} and score {}>"\
			.format(self.id, self.uid, self.chosen_arm, self.game, self.trial, self.reward, self.score)

class Room(db.Model):
	id = db.Column(db.Integer(), primary_key=True)
	next_turn_uid = db.Column(db.Integer(), db.ForeignKey("worker.id"))
	p1_uid = db.Column(db.Integer(), db.ForeignKey("worker.id"),
        nullable=False)
	p2_uid = db.Column(db.Integer(), db.ForeignKey("worker.id"),
        nullable=False)

	time_last_move = db.Column(db.DateTime())
	chosen_arm = db.Column(db.Integer())
	trial = db.Column(db.Integer())
	game = db.Column(db.Integer())
	reward = db.Column(db.Integer())
	next_game_bool = db.Column(db.Boolean())
	completion_code = db.Column(db.String(1024))

	p1_score = db.Column(db.Integer())
	p1_is_observable = db.Column(db.Boolean())
	p1_scores_strs = db.Column(db.String(1024))

	p2_score = db.Column(db.Integer())
	p2_is_observable = db.Column(db.Boolean())
	p2_scores_strs = db.Column(db.String(1024))

	# True scores for each game w/ full observability
	score = db.Column(db.Integer())
	scores_strs = db.Column(db.String(1024))
	experimental_condition = db.Column(db.String(512))
	def __repr__(self):
		return "<Room {} with {} and {}, next turn is player {}, \
			last move at time {}, chosen arm {}, on game {}, trial {}, reward {},\
			next game bool {}, completion code {}>"\
			.format(self.id, self.p1_uid, self.p2_uid, self.next_turn_uid, 
				self.time_last_move, self.chosen_arm, self.game, self.trial, self.reward,
				self.next_game_bool, self.completion_code)


db.create_all()
db.session.commit()