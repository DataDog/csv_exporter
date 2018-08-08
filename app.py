import datetime
import time

import dateutil
import pandas
import requests

from flask import Flask, render_template, request, send_from_directory

app = Flask(__name__)

def get_csv(api_response):
    data = {'metric': []}
    entry_list = []
    api_json = api_response.json()
    for entry in api_json['series']:
        aggr = entry['aggr']
        display_name = entry['display_name']
        scope = entry['scope']

        data[scope] = []
        data['metric'] = '{} ({})'.format(display_name, aggr)
        entry_list.append(scope)

        for _, data_point in entry['pointlist']:
            if not data_point:
                this_data_point = ''
            else:
                this_data_point = float(data_point)

            data[scope].append(this_data_point)

        pandas.to_numeric(data[scope])
        if 'date' not in data:
            data['date'] = [
                str(datetime.datetime.fromtimestamp(epoch_timestamp/1000))
                for epoch_timestamp, _ in entry['pointlist']
            ]

    column_list = ['date', 'metric'] + entry_list
    dataframe = pandas.DataFrame(data, columns=column_list)
    filename = (
        'Metrics-CSV' +
        str(datetime.datetime.now()).split('.')[0].replace(' ', '-') +
        '.csv'
    )

    dataframe.to_csv(filename, encoding='utf-8')
    return filename

@app.route('/files/<path:path>')
def send_file(path):
    return send_from_directory('/', path)

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'metric_query' in request.form and request.form['metric_query'] != '':
        api_key = request.form.get('api_key')
        app_key = request.form.get('app_key')
        start_time_dt = dateutil.parser.parse(request.form.get('start_time'))
        end_time_dt = dateutil.parser.parse(request.form.get('end_time'))
        start_time = int(time.mktime(start_time_dt.timetuple()))
        end_time = int(time.mktime(end_time_dt.timetuple()))
        metric_query = request.form.get('metric_query')

        metrics_url = (
            'https://api.datadoghq.com/api/v1/query?'
            'api_key={api_key}&application_key={app_key}&query={query}'
            '&from={start_time}&to={end_time}'
        ).format(
            api_key=api_key,
            app_key=app_key,
            query=metric_query,
            start_time=start_time,
            end_time=end_time
        )

        metrics_api_response = requests.get(metrics_url)
        filename = get_csv(metrics_api_response)
        filepath = '/files/' + filename

        graph_url = (
            'https://api.datadoghq.com/api/v1/graph/snapshot?'
            'api_key={api_key}&application_key={app_key}&metric_query={query}'
            '&start={start_time}&end={end_time}'
        ).format(
            api_key=api_key,
            app_key=app_key,
            query=metric_query,
            start_time=start_time,
            end_time=end_time
        )

        graph_api_response = requests.get(graph_url)
        graph_url = graph_api_response.json()['snapshot_url'].replace('https',
                                                                      'http')

        time.sleep(6)
    elif 'api_key' in request.args and request.args['api_key']:
        api_key = request.args.get('api_key')
        app_key = request.args.get('app_key')
        filename = ''
        filepath = ''
        graph_url = ''
    else:
        api_key = ''
        app_key = ''
        filename = ''
        filepath = ''
        graph_url = ''

    return render_template('index.html',
                           filename=filename,
                           filepath=filepath,
                           graph_url=graph_url,
                           api_key=api_key,
                           app_key=app_key)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=80, ssl_context='adhoc')
