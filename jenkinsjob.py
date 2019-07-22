"""Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab

Usage:
    jenkinsjob verify <project_url>
    jenkinsjob ondemand <option> <params>...
    jenkinsjob disable_all_mirrors

Options:
    -h --help     Show this screen.

Commands:
    jenkins mirror disable_all_mirrors
    jenkins verify http://url.com/repo.git
"""

# from congregate.migration.mirror import MirrorClient as m
from congregate.migration.verify import Verification as v
from congregate.migration.ondemand import OnDemand as o
from docopt import docopt

if __name__ == '__main__':
    arguments = docopt(__doc__)
    if arguments["verify"]:
        verification = v()
        if arguments["<project_url>"]:
            function = getattr(v, arguments["<project_url>"])
            function(verification, arguments['<option>'])
    elif arguments["ondemand"]:
        ondemand = o()
        if arguments["<option>"]:
            function = getattr(ondemand, arguments["<option>"])
            function(*arguments["<params>"])
    # elif arguments["disable_all_mirrors"]:
    #     mirror = m()
    #     mirror.disable_all_mirrors()
