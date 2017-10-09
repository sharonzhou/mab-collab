from app import app

port = int(os.environ.get('PORT', 33507))
app.run(debug=True, port=port)