#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Create Ochazuke: the webcompat-metrics-server Flask application."""

import os
import logging
import json

from flask import abort
from flask import Flask
from flask import request
from flask import Response

from ochazuke.helpers import get_json_slice
from ochazuke.helpers import get_timeline_data
from ochazuke.helpers import is_valid_args
from ochazuke.helpers import is_valid_category
from ochazuke.helpers import normalize_date_range
from tools.helpers import get_remote_data
from ochazuke.models import db


def create_app(test_config=None):
    """Create the main webcompat metrics server app."""
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # configure the postgresql database
    if test_config is None:
        # fetch the environment variables for the database and hook secret
        database_url = os.environ.get('DATABASE_URL')
    else:
        # use the local database for testing and a dummy secret
        database_url = 'postgresql://localhost/metrics'
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # A route for starting
    @app.route('/')
    def index():
        """Home page of the site"""
        return 'Welcome to ochazuke'

    @app.route('/data/weekly-counts')
    def weekly_reports_data():
        """Secondhand pipeline for returning weekly JSON data."""
        json_weekly_data = get_remote_data(
            'http://laghee.pythonanywhere.com/tmp/weekly_issues')
        if is_valid_args(request.args):
            json_weekly_data = get_json_slice(
                json_weekly_data,
                request.args.get('from'),
                request.args.get('to')
            )
        response = Response(
            response=json_weekly_data,
            status=200,
            mimetype='application/json')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Vary', 'Origin')
        return response

    @app.route('/data/<category>-timeline')
    def issues_count_data(category):
        """Route for issues count."""
        if not is_valid_category(category):
            abort(404)
        if not request.args:
            abort(404)
        if not is_valid_args(request.args):
            abort(404)
        # Extract the dates
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        start, end = normalize_date_range(from_date, to_date)
        # Grab the data
        timeline = get_timeline_data(category, start, end)
        # Prepare the response
        about = 'Hourly {category} issues count'.format(category=category)
        response_object = {
            'about': about,
            'date_format': 'w3c',
            'timeline': timeline
        }
        response = Response(
            response=json.dumps(response_object),
            status=200,
            mimetype='application/json')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Vary', 'Origin')
        return response

    return app


# Logging Capabilities
# To benefit from the logging, you may want to add:
#   app.logger.info(Thing_To_Log)
# it will create a line with the following format
# (2015-09-14 20:50:19) INFO: Thing_To_Log
logging.basicConfig(format='(%(asctime)s) %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d  %H:%M:%S %z', level=logging.INFO)

app = create_app()
