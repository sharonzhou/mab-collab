from app import db

class Worker(db.Model):
	id = db.Column(db.Integer(), primary_key=True)
	amt_id = db.Column(db.String(512))

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
		return "<Move {}>".format(self.id)

db.create_all()