from helpers import conf

import argparse
import json
from helpers import api
import time

conf = conf.ig()
# parser = argparse.ArgumentParser(description='Analyze GitLab repositories.')
# parser.add_argument('--test', type=str, default=None, dest='quiet',
#                     help='Silent output of script')

# args = parser.parse_args()

# print args.quiet
id = 19
req = api.generate_post_request(conf.child_host, conf.child_token, "projects/%d/export" % id, "")
print json.load(req)
req = api.generate_get_request(conf.child_host, conf.child_token, "projects/%d/import" % id)
print json.load(req)
time.sleep(0.5)
download = api.generate_get_request(conf.child_host, conf.child_token, "projects/%d/export/download" % id)
print download.info().getheader("Content-Disposition").split("=")[1]