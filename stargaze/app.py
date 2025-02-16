from flask import Flask, render_template, request
from stargaze.geocoding import find_coordinates

app = Flask(__name__)


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        try:
            whereabouts = request.form.get('whereabouts')
            if whereabouts:
                coordinates = find_coordinates(whereabouts)
                return render_template('index.html', coordinates=coordinates, whereabouts=whereabouts)
        except IndexError:
            return render_template('index.html', coordinates=None)
    return render_template('index.html', coordinates=None)

@app.route('/about')
def about():
    return render_template('about.html')