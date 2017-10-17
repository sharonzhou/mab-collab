from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import numpy as np
import os, json
from urllib import parse
from dbanalysis import Analysis

app = Flask(__name__)
def get_interface_analysis_instance(db):
	if db == "single":
		url = parse.urlparse(os.environ["DATABASE_URL_SINGLE"])
	elif db == "single_bars":
		url = parse.urlparse(os.environ["DATABASE_URL_SINGLE_BARS"])
	else:
		# Error
		print("Please provide a valid db url")
		return None
	return Analysis(url)

@app.route("/human_actions/<db>/<uid>")
def human_actions(db, uid):
	analysis = get_interface_analysis_instance(db)

	human_actions = analysis.human_actions
	rewards = analysis.rewards
	kg_agreement = analysis.kg_agreement
	kg_actions = analysis.kg_actions

	# Rows for user's actions
	actions = human_actions[int(uid)]
	rows = [[] for _ in range(len(actions))]
	for g, game in enumerate(actions):
		rows[g] = [[] for _ in range(len(game))]
		for t, _ in enumerate(game):
			style = "fill-color: red"
			if rewards[int(uid)][g][t]:
				style = "fill-color: green"
			annotation = "KG: {}".format(str(int(kg_actions[int(uid)][g][t] + 1)))
			if kg_agreement[int(uid)][g][t]:
				style += "; stroke-color: gray; stroke-width: 1; fill-opacity: 1"
			else:
				style += "; fill-opacity: .2"
			rows[g][t] = ["Trial {}".format(str(t + 1)), actions[g][t] + 1, style, annotation]
	return render_template("human_actions.html", rows=json.dumps(rows), user=uid, interface=db)


@app.route("/")
def main():
	parse.uses_netloc.append("postgres")
	urls = {
		"single": parse.urlparse(os.environ["DATABASE_URL_SINGLE"]),
		"single_bars": parse.urlparse(os.environ["DATABASE_URL_SINGLE_BARS"])
	}
	
	data = {}
	for interface, url in urls.items():
		data[interface] = {}

		analysis = Analysis(url)

		# Shapes: (uid, game, trial)
		human_actions = analysis.human_actions
		rewards = analysis.rewards
		kg_agreement = analysis.kg_agreement
		kg_actions = analysis.kg_actions

		# Average KG agreement for a user.
		user_avg_kg_agreement = np.true_divide(np.sum(kg_agreement, axis=1), 20)

		# Average per trial. Shape: (game, trial)
		avg_kg_agreement = np.true_divide(np.sum(kg_agreement.swapaxes(0,1).swapaxes(1,2), axis=2), kg_agreement.size)

		data[interface + "_human_actions"] = human_actions.tolist()
		data[interface + "_rewards"] = rewards.tolist()
		data[interface + "_kg_agreement"] = kg_agreement.tolist()
		data[interface + "_kg_actions"] = kg_actions.tolist()
		data[interface + "_avg_kg_agreement"] = avg_kg_agreement.tolist()
		data[interface + "_user_avg_kg_agreement"] = user_avg_kg_agreement.tolist()
	return render_template("vis.html", **data)


if __name__ == "__main__":
	port = int(os.environ.get("PORT", 5000))
	app.run(debug=True, host="0.0.0.0", port=port)