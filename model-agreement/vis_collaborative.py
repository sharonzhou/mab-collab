from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import numpy as np
import os, json
from urllib import parse
from dbanalysis_collaborative import Analysis

app = Flask(__name__)

@app.route("/human_actions/<room_id>")
def human_actions(room_id):
	url = parse.urlparse(os.environ["DATABASE_URL"])
	analysis = Analysis(url)
	original_room_id = analysis.id_room_mapping[int(room_id)]

	human_actions = analysis.human_actions
	rewards = analysis.rewards
	model_actions, model_agreement, _ = analysis.get_model_agreement()

	# Rows for room actions
	actions = human_actions[int(room_id) - 1]
	rows = [[] for _ in range(len(actions))]
	for g, game in enumerate(actions):
		rows[g] = [[] for _ in range(len(game) - 1)]
		for t, _ in enumerate(game):
			if t == len(game) - 1:
				continue
			style = "fill-color: rgb(211,94,96);"
			if rewards[int(room_id)][g][t]:
				style = "fill-color: rgb(132,186,91);"

			annotation = "{}".format(str(int(model_actions[int(room_id) - 1][g][t] + 1)))
			tooltip = "{}\n".format(str(int(model_actions[int(room_id) - 1][g][t] + 1)))

			if model_agreement[int(room_id) - 1][g][t]:
				style += "fill-opacity: 1;"
			else:
				style += "fill-opacity: .2;"

			rows[g][t] = ["Trial {}".format(str(t + 1)), actions[g][t] + 1, style, annotation, tooltip]
		print("rows[g] is:",rows[g])
	return render_template("human_actions_collaborative.html", rows=json.dumps(rows), room_id=original_room_id)

@app.route("/")
@app.route("/<model>")
def model(model="model"):
	parse.uses_netloc.append("postgres")
	url = parse.urlparse(os.environ["DATABASE_URL"])
	analysis = Analysis(url)
	
	# Get average model agreement
	_, model_agreement, avg_agreement = analysis.get_model_agreement()

	# Average agreement for a user
	user_avg_agreement = np.true_divide(np.sum(model_agreement, axis=1), 20)
	
	data = {}
	data["user_avg_agreement"] = user_avg_agreement.tolist()
	data["avg_agreement"] = avg_agreement.tolist()

	return render_template("vis_collaborative.html", **data, model=model)


if __name__ == "__main__":
	port = int(os.environ.get("PORT", 5000))
	app.run(debug=True, host="0.0.0.0", port=port)