from flask import Flask

# Serve everything under the 'bot/static' directory at /static/...
app = Flask(__name__, static_folder="bot/static")

if __name__ == "__main__":
    # Listen on all interfaces, on port 25594
    app.run(host="0.0.0.0", port=25594, debug=True)
