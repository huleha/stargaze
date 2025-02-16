from flask import Flask, render_template, request
from stargaze.geocoding import find_coordinates
from stargaze.cli import parse_length, parse_direction
from stargaze.core import stargaze

app = Flask(__name__)


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        try:
            input_whereabouts = request.form.get('whereabouts')
            if input_whereabouts:
                coordinates = find_coordinates(input_whereabouts)
                input_radius = request.form.get('radius')
                input_direction = request.form.get('direction', '0.0')
                direction = parse_direction(input_direction)
                print("AAAAAAAAAAAAA", direction)
                if input_radius:
                    print("bbb", direction)
                    radius = parse_length(input_radius)
                    spots = stargaze(coordinates, radius, direction)

                    return render_template('index.html', whereabouts=input_whereabouts, radius=input_radius,
                                           spots=spots, direction=direction)
                print("ccc", direction)
                radius = 3000
                spots = stargaze(coordinates, radius, direction)
                return render_template('index.html', whereabouts=input_whereabouts, radius=radius,
                                       spots=spots, direction=direction)

        except IndexError:
            return render_template('index.html', coordinates=None)
    return render_template('index.html', coordinates=None)


@app.route('/about')
def about():
    return render_template('about.html')
