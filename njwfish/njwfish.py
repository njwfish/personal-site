from flask import Flask
from core import core

app = Flask(__name__)
app.register_blueprint(core)

if __name__ == "__main__":
    app.run(debug=True)

