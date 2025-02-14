from flask import Flask, render_template, request
from stargaze.geocoding import find_coordinates

app = Flask(__name__)


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        whereabouts = request.form.get('whereabouts')
        if whereabouts:
            coordinates = find_coordinates(whereabouts)
            return render_template('index.html', coordinates=coordinates)
    return render_template('index.html', coordinates=None)
