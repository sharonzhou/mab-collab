from app import db

class Worker(db.Model):
	id = db.Column(db.Integer(), primary_key=True)
	amt_id = db.Column(db.String(512))
	room_id = db.Column(db.Integer())
	is_ready = db.Column(db.Boolean())

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

	def __repr__(self):
		return "<Move {} by {} on arm {} for game {} trial {} with reward {}>"\
			.format(self.id, self.uid, self.chosen_arm, self.game, self.trial, self.reward)

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
	score = db.Column(db.Integer())

	def __repr__(self):
		return "<Room {} with {} and {}, next turn is player {}, \
			last move at time {}, chosen arm {}, on game {}, trial {}, reward {}>"\
			.format(self.id, self.p1_uid, self.p2_uid, self.next_turn_uid, 
				self.time_last_move, self.chosen_arm, self.game, self.trial, self.cumulative_reward)


db.create_all()