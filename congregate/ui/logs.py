import subprocess
from flask import Response, Blueprint, stream_with_context
from congregate.helpers.utils import get_congregate_path

logger = Blueprint('logger', __name__)


@logger.route('/log')
def generate_stream():
    def generate():
        last_line = ""
        while True:
            output = subprocess.check_output(
                ['tail', '-n 1', f'{get_congregate_path()}/data/logs/congregate.log'])
            if output == last_line:
                yield ""
            else:
                last_line = output
                yield "<p>" + output.split("|")[-1] + "</p>"
            subprocess.call(['sleep', '1'])

    return Response(stream_with_context(generate()))

@logger.route('/logLine')
def return_last_line():
    output = subprocess.check_output(
        ['tail', '-n 1', f'{get_congregate_path()}/data/logs/congregate.log'])
    return output.split(":")[-1]
