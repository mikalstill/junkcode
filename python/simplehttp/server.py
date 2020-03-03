#!/usr/bin/python3

import datetime
import flask
import flask_restful
import jinja2
import math
import sys

from flask import request

app = flask.Flask(__name__)
api = flask_restful.Api(app)


LOCATIONS = {
    'CBR': (-35.3075, 149.1244),
    'LAX': (33.9416, 118.4085),
    'LON': (51.4700, 0.4543)
}


class Root(flask_restful.Resource):
    def get(self):
        # Read template and data
        with open('template.html') as f:
            t = jinja2.Template(f.read())

        # Extract location header
        latlon = request.headers.get('X-Lat-Lon')
        if latlon:
            lat, lon = latlon.split(',')
            lat = float(lat)
            lon = float(lon)

            region = 'CBR'
            min_distance = 1000000

            for location in LOCATIONS:
                distance = math.sqrt(math.pow(LOCATIONS[location][0] - lat, 2) +
                                     math.pow(LOCATIONS[location][1] - lon, 2))
                if distance < min_distance:
                    min_distance = distance
                    region = location

        else:
            region = 'CBR'
            min_distance = -1

        resp = flask.Response(
            t.render(
                timestamp=str(datetime.datetime.now()),
                headers=dict(request.headers),
                min_distance=min_distance,
                region=region,
            ),
            mimetype='text/html')

        resp.status_code = 200
        return resp


class Health(flask_restful.Resource):
    def get(self):
        resp = flask.Response('OK', mimetype='text/plain')
        resp.status_code = 200
        return resp


api.add_resource(Root, '/')
api.add_resource(Health, '/healthz')

if __name__ == '__main__':
    # Note this is not run with the flask task runner...
    app.run(host='0.0.0.0', port=int(sys.argv[1]), debug=True)
