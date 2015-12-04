# Copyright (c) 2015. Librato, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Librato, Inc. nor the names of project contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL LIBRATO, INC. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# Utility library for working with Librato Spaces
# Their python bindings don't include support for these APIs
import json
import requests
from requests.auth import HTTPBasicAuth
from six.moves.urllib.parse import urlencode

SPACES_API_URL = "https://metrics-api.librato.com/v1/spaces"


class Api(object):
    def __init__(self, user, password):
        super(Api, self).__init__()

        self.user = user
        self.password = password
        self.auth = HTTPBasicAuth(user, password)
        # user, pwd = get_master_credentials()
        # self.auth = HTTPBasicAuth(user, pwd)

    def get_spaces(self):
        spaces = []
        found = 0
        while True:
            params = {"offset": found}
            resp = requests.get(SPACES_API_URL, params=params, auth=self.auth)
            resp.raise_for_status()

            data = resp.json()
            query = data.get('query')

            spaces.extend(data.get('spaces'))

            found += query.get('length')
            if query.get('found') == found:
                break
        return spaces

    def add_space(self, name):
        spaces = self.get_spaces()
        if name in [s.get('name') for s in spaces]:
            raise Exception('Space {} already exists'.format(name))
        params = {
            "name": name,
        }
        data = urlencode(params)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = requests.post(SPACES_API_URL, data=data, headers=headers, auth=self.auth)
        resp.raise_for_status()
        return resp.json()

    def get_charts(self, space_id):
        url = "{}/{}/charts".format(SPACES_API_URL, space_id)
        resp = requests.get(url, auth=self.auth)
        resp.raise_for_status()

        return resp.json()

    def get_chart(self, space_id, chart_id):
        url = "{}/{}/charts/{}".format(SPACES_API_URL, space_id, chart_id)
        resp = requests.get(url, auth=self.auth)
        resp.raise_for_status()
        return resp.json()

    def add_chart(self, space_id, name, y_label, chart_type="line", metrics=[], min_=None, max_=None):
        params = {
            "name": name,
            "type": chart_type,
            "label": y_label,
        }
        if metrics:
            params['streams'] = []
            for m in metrics:
                params['streams'].append(m)
        if min_:
            params['min'] = min_
        if max_:
            params['max'] = max_

        url = "{}/{}/charts".format(SPACES_API_URL, space_id)
        # data = urlencode(params)
        # headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = json.dumps(params)
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, data=data, headers=headers, auth=self.auth)
        resp.raise_for_status()

        return resp.json()

    def add_metric(self, space_id, chart_id, metric):
        chart = self.get_chart(space_id, chart_id)
        del chart['id']
        metrics = chart.get('streams') or []
        metrics.append(metric)

        chart['streams'] = metrics
        url = "{}/{}/charts/{}".format(SPACES_API_URL, space_id, chart_id)

        # JSON content type appears to be required for some reason
        # data = urlencode(chart)
        # headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = json.dumps(chart)
        headers = {"Content-Type": "application/json"}
        resp = requests.put(url, data=data, headers=headers, auth=self.auth)
        resp.raise_for_status()
