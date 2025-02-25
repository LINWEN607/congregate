from time import sleep
import subprocess
from flask import Response, Blueprint, stream_with_context
from congregate.helpers.utils import get_congregate_path
import fileinput

logger = Blueprint('logger', __name__)

import time
from typing import Iterator

def follow(file, sleep_sec=0.1) -> Iterator[str]:
    """ Yield each line from a file as they are written.
    `sleep_sec` is the time to sleep after empty reads. """
    line = ''
    file.seek(0, 2)
    while True:
        tmp = file.readline()
        if tmp is not None and tmp != "":
            line += tmp
            if line.endswith("\n"):
                yield line
                line = ''
        elif sleep_sec:
            time.sleep(sleep_sec)

@logger.route('/log/<log_file>')
def generate_stream(log_file):
    def generate():
        last_line = ""
        # while True:
        #     print("Tailing logs")
        #     output = subprocess.check_output(
        #         ['tail', '-n 1', f'{get_congregate_path()}/data/logs/congregate.log'])
        #     # if output == last_line:
        #     #     yield ""
        #     # else:
        #     #     last_line = output
        #     #     yield "<p>" + output.split("|")[-1] + "</p>"
        #     yield output
        #     sleep(1)
        with open(f'{get_congregate_path()}/data/logs/{log_file}', 'r') as file:
            for line in follow(file):
                yield line

    return Response(stream_with_context(generate()))

@logger.route('/logLine')
def return_last_line():
    output = subprocess.check_output(
        ['tail', '-n 1', f'{get_congregate_path()}/data/logs/congregate.log'])
    return output.split(":")[-1]
