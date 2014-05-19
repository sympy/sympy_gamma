#!/usr/bin/env python

import os
import sys
import argparse
import subprocess

TAG_COMMAND = 'git describe --exact-match HEAD --tags'
DEPLOY_COMMAND = ('python2 $SDK_LOCATION/appcfg.py '
                  '--oauth2_refresh_token=$OAUTH_REFRESH_TOKEN update .')
ROLLBACK_COMMAND = ('python2 $SDK_LOCATION/appcfg.py '
                  '--oauth2_refresh_token=$OAUTH_REFRESH_TOKEN rollback .')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate an App Engine app.yaml and optionally deploy this application.')
    parser.add_argument('--generate-only',
                        help="Only generate app.yaml. Do not deploy.",
                        action='store_true')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--generate-test',
                       help='Generate app.yaml for the test application.',
                       nargs='?',
                       type=int,
                       default=-1,
                       const=-1)
    group.add_argument('--generate-production',
                       help='Generate app.yaml for the production application.',
                       nargs='?',
                       type=int,
                       default=-1,
                       const=-1)
    args = parser.parse_args()

    deploy_app = not args.generate_only

    config_type = 'test'
    if (args.generate_production > 0 or
        (os.environ.get('TRAVIS_PULL_REQUEST') == 'false' and
         args.generate_test < 0)):
        config_type = 'production'

    application = version = None
    if config_type == 'production':
        print "Generating production configuration."
        application = 'sympy-gamma-li'
        # On main branch. Get the tag corresponding to the current commit;
        # if the tag does not exist, do not deploy.
        git_process = subprocess.Popen(TAG_COMMAND,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        stdin, stdout = git_process.communicate()
        if not stdin and args.generate_production <= 0:
            print "ERROR: Could not determine version to deploy."
            print "Either tag the current commit as 'version-VERSION' or provide" + \
                "--generate-production VERSION."
            sys.exit(1)

        if args.generate_production > 0:
            version = args.generate_production
        else:
            try:
                version = int(stdin[8:])
            except ValueError:
                print "ERROR: Could not determine version number from tag", stdin
                sys.exit(1)
    else:
        print "Generating test configuration."
        application = 'sympy-gamma-li'
        if args.generate_test > 0:
            # User provided test version
            version = args.generate_test
        elif 'TRAVIS_PULL_REQUEST' in os.environ:
            # Get PR number from Travis
            version = int(os.environ.get('TRAVIS_PULL_REQUEST'))
        else:
            print "ERROR: Must provide --generate-test VERSION if not running under Travis."
            sys.exit(1)

    print "Generating configuration for version", version

    with open('app.yaml.template') as f:
        template = f.read()
        configuration = template.format(application=application, version=version)

    with open('app.yaml', 'w') as f:
        f.write(configuration)

    print "Generated configuration."
    if deploy_app:
        print "Deploying..."
        return_code = subprocess.call(DEPLOY_COMMAND, shell=True)
        if return_code == 0:
            print "Deployed application."
        else:
            print "Could not deploy application. Running appcfg rollback..."
            subprocess.call(ROLLBACK_COMMAND, shell=True)
