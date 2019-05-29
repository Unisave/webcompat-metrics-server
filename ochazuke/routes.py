#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Set of routes for Ochazuke app."""

import json

from flask import abort
from flask import current_app as app
from flask import request
from flask import Response

from ochazuke.helpers import get_json_slice
from ochazuke.helpers import get_timeline_data
from ochazuke.helpers import is_valid_args
from ochazuke.helpers import is_valid_category
from ochazuke.helpers import normalize_date_range
from tools.helpers import get_remote_data


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


@app.route('/data/triage-bugs')
def triage_bugs():
    """Returns the list of issues which are currently in triage."""
    url = 'https://api.github.com/repos/webcompat/web-bugs/issues?sort=created&per_page=100&direction=asc&milestone=2'  # noqa
    json_data = get_remote_data(url)
    response = Response(
        response=json_data,
        status=200,
        mimetype='application/json')
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Vary', 'Origin')
    return response
