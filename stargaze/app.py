from flask import Flask, render_template, request, g
from stargaze.geocoding import find_coordinates
from stargaze.cli import parse_length, parse_direction
from stargaze.core import stargaze
from stargaze.sessions import SessionFactory

app = Flask(__name__)


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        try:
            call_function = True
            input_whereabouts = request.form.get('whereabouts')

            if input_whereabouts:
                coordinates = find_coordinates(input_whereabouts)
                input_radius = request.form.get('radius')
                input_direction = request.form.get('direction', '0.0')
                direction = parse_direction(input_direction)
                if input_radius:
                    radius = parse_length(input_radius)
                    spots = stargaze(coordinates, radius, direction)
                    return render_template('index.html', whereabouts=input_whereabouts, radius=input_radius,
                                           spots=spots, direction=direction, call_function=call_function)
                radius = 3000
                spots = stargaze(coordinates, radius, direction)
                return render_template('index.html', whereabouts=input_whereabouts, radius=radius,
                                       spots=spots, direction=direction, call_function=call_function)
        except IndexError:
            return render_template('index.html', coordinates=None)
    return render_template('index.html', coordinates=None)


@app.route('/about')
def about():
    return render_template('about.html')


def get_db():
    if 'db' not in g:
        g.db = SessionFactory.get_session()
    return g.db


@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)
    if db is not None:
        SessionFactory.get_instance().close()
