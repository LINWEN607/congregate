###
### If this file is changed due to autopep8, revert the change or else the UI won't load
###
import os
import sys
import logging


sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)))))

from gitlab_ps_utils.logger import myLogger


log = myLogger('werkzeug', app_path=os.getenv('CONGREGATE_PATH'), log_name='congregate')

log.setLevel(logging.ERROR)
