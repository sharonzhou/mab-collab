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
@app.route("/human_actions/<db>/<uid>/<model>")
def human_actions(db, uid, model="kg"):
	analysis = get_interface_analysis_instance(db)

	human_actions = analysis.human_actions
	rewards = analysis.rewards

	kg_actions, kg_agreement = analysis.compute_kg(db)
	greedy_actions, greedy_agreement = analysis.compute_greedy()
	wsls_actions, wsls_agreement = analysis.compute_wsls()

	# Rows for user's actions
	actions = human_actions[int(uid)]
	rows = [[] for _ in range(len(actions))]
	for g, game in enumerate(actions):
		rows[g] = [[] for _ in range(len(game))]
		for t, _ in enumerate(game):
			style = "fill-color: red"
			if rewards[int(uid)][g][t]:
				style = "fill-color: green"

			if model == "greedy":
				model_agreement = greedy_agreement
				annotation = "eG: {}".format(str(int(greedy_actions[int(uid)][g][t] + 1)))
			elif model == "wsls":
				model_agreement = wsls_agreement
				annotation = "WSLS: {}".format(str(int(wsls_actions[int(uid)][g][t] + 1)))
			else:
				model_agreement = kg_agreement
				annotation = "KG: {}".format(str(int(kg_actions[int(uid)][g][t] + 1)))

			tooltip = "KG: {}\n".format(str(int(kg_actions[int(uid)][g][t] + 1))) + \
						" eG: {}\n".format(str(int(greedy_actions[int(uid)][g][t] + 1))) + \
						" WSLS: {}".format(str(int(wsls_actions[int(uid)][g][t] + 1)))

			if model_agreement[int(uid)][g][t]:
				style += "; stroke-color: gray; stroke-width: 1; fill-opacity: 1"
			else:
				style += "; fill-opacity: .2"

			rows[g][t] = ["Trial {}".format(str(t + 1)), actions[g][t] + 1, style, annotation, tooltip]
	return render_template("human_actions.html", rows=json.dumps(rows), user=uid, interface=db)


@app.route("/")
def main():
	return render_template("index.html")

@app.route("/<model>")
def model(model="kg"):
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
		if model == "greedy":
			_, model_agreement = analysis.compute_greedy()
		elif model == "wsls":
			_, model_agreement = analysis.compute_wsls()
		else:
			_, model_agreement = analysis.compute_kg(interface)

		print("Original shape (u, g, t): ", model_agreement.shape)
		# Remove user 4 (u=3)
		# model_agreement = np.delete(model_agreement, np.s_[3], axis=0)
		# Remove trial 1 (t=0)
		model_agreement = np.delete(model_agreement, np.s_[0], axis=2)
		print("New shape (u, g, t): ", model_agreement.shape)
		avg_agreement = np.true_divide(np.sum(model_agreement), \
			model_agreement.shape[0] * model_agreement.shape[1] * model_agreement.shape[2])

		# Average agreement for a user.
		user_avg_agreement = np.true_divide(np.sum(model_agreement, axis=1), 20)
		data[interface + "_user_avg_agreement"] = user_avg_agreement.tolist()
		data[interface + "_avg_agreement"] = avg_agreement.tolist()

	return render_template("vis.html", **data, model=model)


if __name__ == "__main__":
	port = int(os.environ.get("PORT", 5000))
	app.run(debug=True, host="0.0.0.0", port=port)