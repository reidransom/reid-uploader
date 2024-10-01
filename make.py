#!/usr/bin/env python

import sys
import subprocess

cmds = ['stage', 'serve', 'test']

def usage():
    return 'python make.py [%s]\n' % '|'.join(cmds)

def bash(cmd):
    subprocess.call(cmd, shell=True)

def rsync(src, dest, exclude=['*.pyc'], args=['--checksum', '--archive', '--verbose', '--delete', '--delete-excluded']):
    exclude.append('.DS_Store')
    args.extend(map(lambda s: '--exclude ' + s, exclude))
    args = ' '.join(args)
    cmd = 'rsync %(args)s %(src)s %(dest)s' % locals()
    bash(cmd)

def stage():
    rsync(
        'reiduploader/',
        'reidransom@reidransom.com:webapps/upload_wsgi/reiduploader/'
    )
    rsync(
        'webfaction/',
        'reidransom@reidransom.com:webapps/upload_wsgi/',
        args=['--archive', '--checksum', '--verbose']
    )
    bash('ssh reidransom@reidransom.com ./webapps/upload_wsgi/apache2/bin/restart')

def serve():
    from reiduploader.views import app
    from reiduploader.settings import PORT
    app.run(host='0.0.0.0', port=PORT)

def test():
    bash('python -m unittest discover')

if __name__ == '__main__':

    if len(sys.argv) < 2:
        sys.stderr.write(usage())
        sys.exit(1)
    elif not sys.argv[1] in cmds:
        sys.stderr.write(usage())
        sys.exit(1)

    locals()[sys.argv[1]]()
    sys.exit()
