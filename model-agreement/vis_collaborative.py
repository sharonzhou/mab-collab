from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import numpy as np
import os, json
from urllib import parse
from dbanalysis_collaborative import Analysis

app = Flask(__name__)

@app.route("/human_actions/<rid>")
def human_actions(rid):
	url = parse.urlparse(os.environ["DATABASE_URL"])
	analysis = Analysis(url)
	room_id = int(rid) - 1
	original_room_id = analysis.id_room_mapping[room_id]

	human_actions = analysis.human_actions
	rewards = analysis.rewards
	model_actions, model_agreement, avg_agreement, adjusted_model_agreement = analysis.get_model_agreement()
	experimental_condition = analysis.experimental_conditions[room_id]

	# Rows for room actions
	human_actions = human_actions[room_id]
	rows = [[] for _ in range(len(human_actions))]
	for g, game in enumerate(human_actions):
		rows[g] = [[] for _ in range(len(game))]
		for t, _ in enumerate(game):
			style = "fill-color: rgb(211,94,96);"
			if rewards[room_id][g][t]:
				style = "fill-color: rgb(132,186,91);"

			annotation = "{}".format(str(int(model_actions[room_id][g][t] + 1)))
			tooltip = "t={}\nH {}\nR {}".format(str(t), str(int(human_actions[g][t] + 1)), str(int(model_actions[room_id][g][t] + 1)))

			if model_agreement[room_id][g][t]:
				style += "fill-opacity: 1;"
			else:
				style += "fill-opacity: .2;"

			rows[g][t] = ["Trial {}".format(str(t)), human_actions[g][t] + 1, style, annotation, tooltip]
		print("rows[g] is:", rows[g])
	return render_template("human_actions_collaborative.html", rows=json.dumps(rows), room_id=room_id, original_room_id=original_room_id, experimental_condition=experimental_condition)

@app.route("/")
@app.route("/<model>")
def model(model="model"):
	parse.uses_netloc.append("postgres")
	url = parse.urlparse(os.environ["DATABASE_URL"])
	analysis = Analysis(url)
	
	# Get average model agreement
	model_actions, model_agreement, avg_agreement, adjusted_model_agreement = analysis.get_model_agreement()

	# Average agreement for a room
	room_avg_agreement = np.true_divide(np.sum(model_agreement, axis=(1,2)), model_agreement.shape[1] * model_agreement.shape[2])

	# Average agreement for a game
	game_avg_agreement = np.true_divide(np.sum(model_agreement, axis=(0,2)), model_agreement.shape[0] * model_agreement.shape[2])
	
	data = {}
	data["room_avg_agreement"] = room_avg_agreement.tolist()
	data["game_avg_agreement"] = game_avg_agreement.tolist()
	data["avg_agreement"] = avg_agreement.tolist()

	return render_template("vis_collaborative.html", **data, model=model)


if __name__ == "__main__":
	port = int(os.environ.get("PORT", 5000))
	app.run(debug=True, host="0.0.0.0", port=port)