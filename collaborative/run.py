from app import app
import os
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

port = int(os.environ.get("PORT", 5000))
app.run(debug=True, host="0.0.0.0", port=port)
