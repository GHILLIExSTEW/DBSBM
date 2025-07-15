import os
from flask import Flask

# Serve everything under the 'static' directory at /static/...
app = Flask(__name__, static_folder="static")

if __name__ == "__main__":
    # Listen on all interfaces, on port 25594
    app.run(host="0.0.0.0", port=25594, debug=True)
