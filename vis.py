from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import numpy as np
import os
from urllib import parse
from agreement import Agreement

app = Flask(__name__)

@app.route("/")
def main():
	parse.uses_netloc.append("postgres")
	url = parse.urlparse(os.environ["DATABASE_URL"])
	a = Agreement(url)
	return render_template("vis.html", agreement=a.agreement.swapaxes(0,1).swapaxes(1,2).tolist())

if __name__ == "__main__":
	port = int(os.environ.get("PORT", 5000))
	app.run(debug=True, host="0.0.0.0", port=port)