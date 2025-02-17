![stargaze](/stargaze/static/stargaze.jpg)

**stargaze** is an application which helps you find the best spot for
astronomical
observations in your area, taking numerous factors into account, such as:

- Accessibility by road
- Remoteness from large populated areas, lit roads and major highways
- Relief (view should not be obstructed)
- Physical and legal access to the observation spot
- and others

Features
--------

stargaze accepts multiple search parameters, which are `whereabouts`, `radius`,
and `direction`.

- `whereabouts` are supplied as a string and can be either coordinates or
  toponym. E.g. "Krakow";
- `radius` defines the search area as a circle centered at `whereabouts`. This
  parameter is a string that represents distance, the default unit of
  measurement is meters. E.g. "1000", "3km";
- `direction` is identical to the azimuth of the observed object, this parameter
  is a string with degrees in decimal form or cardinal direction. E.g. "115", "
  south".

The result of the search is a set of points that the application has found to be
the fittest according to our set of criteria. These points are displayed on the
map with pins.

Installation
------------

The installation requirements for the application are: `postgresql` instance
with `postgis` and `python3`.
It is recommended to install python dependencies inside a virtual environment:

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

Usage
-----

One can run the application in two ways: with the web interface and the command
line.

To use the web front-end:

```bash
flask --app app run
```

To use the CLI:

```bash
python -m stargaze --near <whereabouts> --within <radius> --head <direction>
```

Examples
--------

Search for the stargazing spots around Krakow within 3 kilometers heading south:
```bash
$ python -m stargaze.cli --near Krakow --within 3km --head south
there are 0 missing tiles
nothing to be imported
(50.05053733031539, 20.010839617924916)
(50.03128092447786, 20.00882052954042)
(50.05799339667003, 20.024505761093792)
(50.04575396825263, 20.02780386539977)
```