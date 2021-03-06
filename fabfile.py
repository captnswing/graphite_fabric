#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author:     Frank Hoffsümmer
Purpose:    Install graphite & statsd from trunk on a remote Amazon EC2 linux instance
Disclaimer: this code works on my machines (tm)
Usage:
            # setup the Amazon EC2 machine with graphite and statsd
            fab -i <path to EC2 .pem> -H <EC2 hostname> setup

            # start / stop / check the statsd and graphite services
            fab -i <path to EC2 .pem> -H <EC2 hostname> graphite:start
            fab -i <path to EC2 .pem> -H <EC2 hostname> graphite:stop
            fab -i <path to EC2 .pem> -H <EC2 hostname> graphite:status

"""
from fabric.api import *
from fabric.context_managers import cd
from fabric.contrib.files import sed, exists, append
import urllib2
import sys
import os

# default user on an Amazon EC2 linux instance
env.user = 'ec2-user'
# root dir for virtualenvs on the remote machine
env.virtualenv_home = '/opt/virtualenvs'
# name of the virtualenv we're using here
env.venv_name = 'base'
# python 2.6 that follows with the standard amazon linux ami is fine
env.python = '/usr/bin/python'

@task
def labmanager():
    env.hosts = ['10.20.61.127']
    env.user = 'si'
    env.password = 'si'
    # root dir for virtualenvs on the remote machine
    env.virtualenv_home = '/opt/virtualenvs'
    # name of the virtualenv we're using here
    env.venv_name = 'base'
    # link to python 2.6
    env.python = '/usr/bin/python26'


def install_mod_wsgi():
    """
    installs mod_wsgi 3.3
    """
    if exists('/usr/lib64/httpd/modules/mod_wsgi.so') or exists('/usr/lib/httpd/modules/mod_wsgi.so'):
        return
    with cd('/tmp'):
        run('wget http://modwsgi.googlecode.com/files/mod_wsgi-3.3.tar.gz')
        run('tar -xzvf mod_wsgi-3.3.tar.gz')
        with cd('mod_wsgi-3.3'):
            run('./configure -with-python={0.python:>s}'.format(env))
            sudo('make install')
        sudo('rm -rf mod_wsgi-3.3.tar.gz mod_wsgi-3.3')


def install_virtualenv():
    """
    installs virtualenv and virtualenvwrapper
    """
    sudo('yum -y -q install python26-distribute')
    sudo('mkdir -p {0.virtualenv_home:>s}'.format(env))
    if exists('/usr/local/bin/virtualenvwrapper.sh') or exists('/usr/bin/virtualenvwrapper.sh'):
        return
    with prefix('export VIRTUALENVWRAPPER_PYTHON={0.python:>s} && unset PIP_REQUIRE_VIRTUALENV'.format(env)):
        with cd('/tmp'):
            sudo('curl -o - https://raw.github.com/pypa/pip/master/contrib/get-pip.py | {0.python:>s}'.format(env))
            sudo('/usr/bin/pip install -U virtualenv virtualenvwrapper')
            run('/usr/bin/virtualenvwrapper.sh')
        sudo('chown -R {0.user:>s} {0.virtualenv_home:>s}'.format(env))
        # create virtualenv env.venv_name
        with cd('{0.virtualenv_home:>s}'.format(env)):
            run('mkvirtualenv --no-site-packages {0.venv_name:>s}'.format(env))


def install_dtach():
    """
    installs dtach, to speed things up
    """
    if exists('/usr/local/bin/dtach'):
        return
    with cd('/tmp/'):
        run('curl -L http://sourceforge.net/projects/dtach/files/dtach/0.8/dtach-0.8.tar.gz/download -o dtach-0.8.tar.gz')
        run('tar xfz dtach-0.8.tar.gz')
        with cd('dtach-0.8'):
            run('./configure')
            sudo('make')
            sudo('mv dtach /usr/local/bin/')


def install_nodejs():
    """
    installs node.js from trunk
    """
    if exists('/usr/local/bin/node'):
        return
    sudo('yum install -y -q openssl-devel')
    with cd('/tmp/'):
        # from https://gist.github.com/579814
        sudo('rm -rf node-latest-install')
        run('mkdir node-latest-install')
        with cd('node-latest-install'):
            run('curl http://nodejs.org/dist/node-latest.tar.gz | tar xz --strip-components=1')
            run('./configure')
            # 'sudo make install' takes quite a while to complete
            # I want to have this running in the background so the fabric script can continue with other things
            # see http://docs.fabfile.org/en/1.0.1/faq.html#why-can-t-i-run-programs-in-the-background-with-it-makes-fabric-hang
            # on different methods how to detach long running processes on the target host with fabric
            # I couldn't get screen -d -m to work though. hence 'dtach', which works fine
            sudo('/usr/local/bin/dtach -n /tmp/node make install')


def install_statsd():
    sudo('mkdir -p /opt/statsd')
    with cd('/tmp/'):
        sudo('rm -rf statsd')
        run('env GIT_SSL_NO_VERIFY=true git clone https://github.com/etsy/statsd.git')
        get_configfile('/opt/statsd/stats.js')
        get_configfile('/opt/statsd/config.js')


def install_cairo():
    """
    installs latest version of pixman and cairo backend
    """
    # graphite is not satisfied with versions available through "yum install"
    if exists('/usr/local/lib/libcairo.so'):
        return
    sudo('yum -y -q install pkgconfig valgrind-devel libpng-devel freetype-devel fontconfig-devel')
    with cd('/tmp'):
        # install pixman
        sudo('rm -rf pixman*')
        run('wget http://cairographics.org/releases/pixman-0.20.2.tar.gz')
        run('tar xfz pixman-0.20.2.tar.gz')
        with cd('pixman-0.20.2'):
            with prefix('export PKG_CONFIG_PATH=/usr/lib/pkgconfig:/usr/lib64/pkgconfig:/usr/local/lib/pkgconfig'):
                run('./configure')
            sudo('make install')
            # install cairo
        sudo('rm -rf cairo*')
        run('wget http://cairographics.org/releases/cairo-1.10.2.tar.gz')
        run('tar xfz cairo-1.10.2.tar.gz')
        with cd('cairo-1.10.2'):
            with prefix('export PKG_CONFIG_PATH=/usr/lib/pkgconfig:/usr/lib64/pkgconfig:/usr/local/lib/pkgconfig'):
                run('./configure --enable-xlib=no --disable-gobject')
            sudo('make install')


def install_graphite():
    """
    installs graphite from trunk. because 0.9.8 has some bugs
    """
    # create target dir with correct permissions
    sudo('test -e /opt/graphite || mkdir /opt/graphite')
    sudo('chown -R {0.user:>s} /opt/graphite'.format(env))
    # cannot download an arbitrary version as tarball from launchpad https://bugs.launchpad.net/loggerhead/+bug/240580
    sudo('rm -rf graphite')
    run('bzr branch lp:graphite')
    with prefix('workon {0.venv_name:>s}'.format(env)):
        # install some dependencies
        run('pip install python-memcached django django-tagging')
        with prefix('export PKG_CONFIG_PATH=/usr/lib/pkgconfig:/usr/lib64/pkgconfig:/usr/local/lib/pkgconfig'):
            # install graphite from trunk - less bugs
            with cd('graphite'):
                run('pip install .')
            # install latest release of carbon
            run('pip install http://launchpadlibrarian.net/82112362/carbon-0.9.9.tar.gz')
            # install latest release of whisper
            run('pip install http://launchpadlibrarian.net/82112367/whisper-0.9.9.tar.gz')
            # "pip install py2cairo" picks python3.0 version of py2cairo, hence explicit link
            run('pip install http://www.cairographics.org/releases/py2cairo-1.8.10.tar.gz')
            # run the django webapp syncdb command
        run('cd /opt/graphite/webapp/graphite; python manage.py syncdb --noinput')
    # create required directories
    sudo('test -e /opt/graphite/storage/log/webapp || mkdir -p /opt/graphite/storage/log/webapp')
    # set permissions for the apache process
    sudo('chown -R apache:apache /opt/graphite/storage')


def get_configfile(filepath):
    """
    fetches config files from /opt/config/ tree on bitbucket and puts them into place on the remote machine
    """
    directory = os.path.dirname(filepath)
    if directory == '~':
        # get the home directory of the remote user
        directory = run('pwd')
        # all config files are saved under the /config/ tree hierarchy in the bitbucket source repository
    config_root = "https://bitbucket.org/captnswing/graphite_fabfile/raw/default/config/"
    # convention: config files directly under the /config/ dir are copied to the remote users home dir
    bitbucket_source = config_root + filepath.lstrip('~').lstrip('/')
    sudo('cd %s; curl -s -O %s' % (directory, bitbucket_source))


def configure_shell():
    """
    fetches shell config files from bitbucket, and puts them in the ec2-user's home directory
    """
    # fetch shell config files
    get_configfile('~/.screenrc')
    get_configfile('~/.bashrc')
    # change placeholder variable
    sed('~/.bashrc', '@PYTHON@', env.python, use_sudo=True)


def configure_services():
    """
    downloads & puts in place config files from bitbucket
    changes placeholder variables in them to correct values
    """
    # find out pathes
    with prefix('workon {0.venv_name:>s}'.format(env)):
        python_root = run("""python -c 'from pkg_resources import get_distribution; print get_distribution("django").location'""")
        django_root = run("""cd /; python -c 'print __import__("django").__path__[0]'""")
    # graphite config
    get_configfile('/opt/graphite/conf/graphite.wsgi')
    get_configfile('/opt/graphite/conf/storage-schemas.conf')
    get_configfile('/opt/graphite/conf/dashboard.conf')
    get_configfile('/opt/graphite/conf/carbon.conf')
    get_configfile('/opt/graphite/webapp/graphite/local_settings.py')
    # apache2 config
    get_configfile('/etc/httpd/conf/httpd.conf')
    get_configfile('/etc/httpd/conf.d/graphite.conf')
    sed('/etc/httpd/conf.d/graphite.conf', '@DJANGO_ROOT@', django_root, use_sudo=True)
    sed('/etc/httpd/conf.d/graphite.conf', '@PYTHON_ROOT@', python_root, use_sudo=True)
    # supervisord config
    get_configfile('/etc/supervisord.conf')
    # statsd config
    get_configfile('/etc/statsd.js')
    sed('/etc/statsd.js', '@GRAPHITE_HOST@', env.hosts[0], use_sudo=True)
    # fix permissions
    if exists('~/.virtualenvs'):
        sudo('chown -R {0.user:>s} /home/{user:>s}/.virtualenvs'.format(env))

@task
def start_supervisord():
    """
    starts supervisord (installs it first, if not present)
    this starts all the configured services as well
    """
    if not exists('/usr/bin/supervisord'):
        with prefix('PIP_REQUIRE_VIRTUALENV=false'):
            sudo('pip install supervisor')
    sudo('/usr/bin/supervisord')


def check_graphite():
    """
    see if the graphite is responding to a basic request
    """
    # derive url of an graphite image
    with hide('running', 'stdout'):
        hostname = run('uname -n')
    image_url = 'http://%s/render/?target=carbon.agents.%s.pointsPerUpdate' % (env.hosts[0], hostname)
    print image_url
    # open the image
    try:
        response = urllib2.urlopen(image_url)
        # check the response code
        # tell it like it is
        if response.getcode() == 200:
            print "graphite seems to be running"
        else:
            print "something wrong with graphite installation"
    except urllib2.URLError, e:
        print "could not fetch graphite image: %s" % e.reason


@task
def graphite(command=""):
    """
    starts & stops the graphite services and displays their status
    """
    if command.lower() not in ['start', 'stop', 'status']:
        print "use graphite:start, graphite:stop or graphite:status"
        sys.exit(-1)
    if command.lower() == "status":
        sudo('/usr/bin/supervisorctl status')
    else:
        sudo('/usr/bin/supervisorctl %s graphite:*' % command.lower())
    if command.lower() != "stop":
        check_graphite()
    if command.lower() == "stop":
        with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
            # take down any apache
            sudo('killall httpd')
            sudo('killall carbon-cache.py')
            sudo('killall node')


@task
def setup():
    """
    installs graphite and statsd on the remote EC2 host
    """
#    if env['host'][:6] == '10.20.':
#        # we're in SVT's network
#        append('/home/si/.bashrc', ['export http_proxy=http://proxy.svt.se:8080', 'export https_proxy=https://proxy.svt.se:8080'])
#        append('/etc/sudoers', 'Defaults env_keep = *', use_sudo=True)
#        run('wget http://download.fedora.redhat.com/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm')
#        sudo('rpm -Uvh /home/si/epel-release-5-4.noarch.rpm')
#    sudo('yum -y -q update')
    sudo('yum -y -q install bzr screen mlocate make gcc gcc-c++ python26-devel httpd-devel git-core')
    install_dtach()
    install_nodejs()
    install_cairo()
    install_mod_wsgi()
    configure_shell()
    if env['host'][:6] == '10.20.':
        # we're in SVT's network
        # reappend proxy settings
        append('/home/si/.bashrc', ['export http_proxy=http://proxy.svt.se:8080', 'export https_proxy=https://proxy.svt.se:8080'])
    install_virtualenv()
    install_graphite()
    install_statsd()
    configure_services()
    start_supervisord()
    graphite("start")
