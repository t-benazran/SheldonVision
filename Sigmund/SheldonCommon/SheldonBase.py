import dash
from flask import Request

SHELDON_DASH_COMMON_NAME = "SheldonDashCommonName"
app = dash.Dash(SHELDON_DASH_COMMON_NAME)


def shutdown_server():
    func = Request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.server.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'