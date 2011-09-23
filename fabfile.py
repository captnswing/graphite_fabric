#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author:     Frank Hoffsümmer
Disclaimer: this code works on my machine (tm)

fabric script that installs graphite-trunk and statsd on an Amazon EC2 linux instance.

On the way, it installs all of graphites dependencies:
http://graphite.readthedocs.org/en/latest/install.html

taking some clues from:
http://agiletesting.blogspot.com/2011/04/installing-and-configuring-graphite.html

once fabric is installed, and the ec2 instance is running, just paste the hostname of the
instance into the ec2 function's "env.hosts" variable, and then invoke

$ fab ec2 setup

in the directory that contains this file. For more on fabric, see http://docs.fabfile.org
"""
from fabric.api import *
from fabric.context_managers import cd
from fabric.contrib.files import sed, exists
import os

def ec2():
    """
    configuration parameters for an Amazon EC2 standard Linux instance.
    """
    # the ec2 instance needs to be configured with an ec2 security group
    # that allows for tcp/ip traffic on ports
    # 22 (ssh), 80 (http), 443 (https), 2003 (graphite-carbon)
    # and udp traffic on port
    # 8125 (statsd)
    #
    # put the ec2 hostname in here
    env.hosts = ['ec2-46-137-57-226.eu-west-1.compute.amazonaws.com']
    # this is the username on any standard amazon linux ami instance
    env.user = 'ec2-user'
    # local path to the keypair the ec2 instance was configured with
    env.key_filename = os.path.join(os.path.expanduser('~'), '.ssh', 'svti-frank.pem')
    # location of the virtualenvs
    env.virtualenv_home = '/opt/virtualenvs'
    # name of the virtualenv we're using here
    env.venv_name = 'base'
    # python 2.6 that follows with the standard amazon linux ami is fine
    env.python = '/usr/bin/python'
    env.graphite_host = env.hosts[0]

def install_mod_wsgi():
    """
    installs mod_wsgi 3.3.
    """
    if exists('/usr/lib64/httpd/modules/mod_wsgi.so') or exists('/usr/lib/httpd/modules/mod_wsgi.so'):
        return
    with cd('/tmp'):
        run('wget http://modwsgi.googlecode.com/files/mod_wsgi-3.3.tar.gz')
        run('tar -xzvf mod_wsgi-3.3.tar.gz')
        with cd('mod_wsgi-3.3'):
            run('./configure -with-python=%(python)s' % env)
            sudo('make install')
        sudo('rm -rf mod_wsgi-3.3.tar.gz mod_wsgi-3.3')

def configure_shell():
    """
    fetches all config files from bitbucket,
    and links the shell related config files into place.
    """
    run('wget https://bitbucket.org/captnswing/graphite_fabfile/get/tip.tar.gz')
    run('tar xfz tip.tar.gz')
    with cd('captnswing-graphite_fabfile-*'):
        # move config directory tree into /opt
        sudo('rm -rf /opt/config; mv config /opt/')
    run('rm -rf tip.tar* captnswing-graphite_fabfile-*')
    # link shell config files into place
    run('rm ~/.screenrc; ln -s /opt/config/screenrc ~/.screenrc')
    run('rm ~/.bashrc; ln -s /opt/config/bashrc ~/.bashrc')
    sed('~/.bashrc', '@PYTHON@', env.python)

def install_virtualenv():
    """
    installs virtualenv and virtualenvwrapper.
    """
    sudo('mkdir -p %(virtualenv_home)s' % env)
    if exists('/usr/local/bin/virtualenvwrapper.sh') or exists('/usr/bin/virtualenvwrapper.sh'):
        return
    with cd('/tmp'):
        run('wget http://python-distribute.org/distribute_setup.py')
        sudo('%(python)s distribute_setup.py' % env)
    with prefix('export VIRTUALENVWRAPPER_PYTHON=%(python)s && unset PIP_REQUIRE_VIRTUALENV' % env):
        sudo('/usr/bin/easy_install -U pip')
        sudo('/usr/bin/pip install -U virtualenv virtualenvwrapper')
        run('/usr/bin/virtualenvwrapper.sh')
    sudo('chown -R %(user)s %(virtualenv_home)s' % env)
    # create virtualenv env.venv_name
    with cd('%(virtualenv_home)s' % env):
        run('mkvirtualenv --no-site-packages %(venv_name)s' % env)

def install_dtach():
    """
    installs dtach, to speed things up.
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
    installs node.js from latest trunk.
    """
    if exists('/usr/local/bin/node'):
        return
    sudo('yum install -y -q openssl-devel')
    with cd('/tmp/'):
        sudo('rm -rf node joyent-node*')
        run('curl -L https://github.com/joyent/node/tarball/master -o node_trunk.tar.gz')
        run('tar xfz node_trunk.tar.gz')
        with cd('joyent-node*'):
            run('./configure')
            # 'sudo make install' takes quite a while to complete
            # I want to have this running in the background so the fabric script can continue with other things
            # see http://docs.fabfile.org/en/1.0.1/faq.html#why-can-t-i-run-programs-in-the-background-with-it-makes-fabric-hang
            # on different methods how to detach long running processes on the target host with fabric
            # I couldn't get screen -d -m to work though. hence 'dtach', which works fine
            sudo('/usr/local/bin/dtach -n /tmp/node make install')

def install_cairo():
    """
    installs latest version of pixman and cairo backend.
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
    installs graphite from trunk. because 0.9.8 has some bugs.
    """
    # create target dir with correct permissions
    sudo('test -e /opt/graphite || mkdir /opt/graphite')
    sudo('chown -R %(user)s /opt/graphite' % env)
    # cannot download an arbitrary version as tarball from launchpad https://bugs.launchpad.net/loggerhead/+bug/240580
    sudo('rm -rf graphite')
    run('bzr branch lp:graphite')
    with prefix('workon %(venv_name)s' % env):
        # install some dependencies
        run('pip install python-memcached simplejson django django-tagging')
        with prefix('export PKG_CONFIG_PATH=/usr/lib/pkgconfig:/usr/lib64/pkgconfig:/usr/local/lib/pkgconfig'):
            # install graphite from trunk - less bugs
            with cd('graphite'):
                run('pip install .')
            # install latest release of carbon
            run('pip install http://launchpad.net/graphite/1.0/0.9.8/+download/carbon-0.9.8.tar.gz')
            # install latest release of whisper
            run('pip install http://launchpad.net/graphite/1.0/0.9.8/+download/whisper-0.9.8.tar.gz')
            # "pip install py2cairo" picks python3.0 version of py2cairo, hence explicit link
            run('pip install http://www.cairographics.org/releases/py2cairo-1.8.10.tar.gz')
        # run the django webapp syncdb command
        run('cd /opt/graphite/webapp/graphite; python manage.py syncdb --noinput')
    # create required directories
    sudo('test -e /opt/graphite/storage/log/webapp || mkdir -p /opt/graphite/storage/log/webapp')
    # set permissions for the apache process
    sudo('chown -R apache:apache /opt/graphite/storage')

def configure_services():
    """
    symlinks configfiles under /opt/config tree into place.
    changes placeholder variables in them to correct values.
    """
    # find out pathes
    with prefix('workon %(venv_name)s' % env):
        python_root = run("""python -c 'from pkg_resources import get_distribution; print get_distribution("django").location'""")
        django_root = run("""cd /; python -c 'print __import__("django").__path__[0]'""")
        python = run("which python")
    # graphite config
    sudo('rm /opt/graphite/conf/graphite.wsgi; ln -s /opt/config/opt/graphite/conf/graphite.wsgi /opt/graphite/conf/graphite.wsgi')
    sudo('rm /opt/graphite/conf/storage-schemas.conf; ln -s /opt/config/opt/graphite/conf/storage-schemas.conf /opt/graphite/conf/storage-schemas.conf')
    sudo('rm /opt/graphite/conf/dashboard.conf; ln -s /opt/config/opt/graphite/conf/dashboard.conf /opt/graphite/conf/dashboard.conf')
    sudo('rm /opt/graphite/conf/carbon.conf; ln -s /opt/config/opt/graphite/conf/carbon.conf /opt/graphite/conf/carbon.conf')
    sudo('rm /opt/graphite/webapp/graphite/local_settings.py; ln -s /opt/config/opt/graphite/webapp/graphite/local_settings.py /opt/graphite/webapp/graphite/local_settings.py')
    # apache2 config
    sudo('rm /etc/httpd/conf/httpd.conf; ln -s /opt/config/etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf')
    sudo('rm /etc/httpd/conf.d/graphite.conf; ln -s /opt/config/etc/httpd/conf.d/graphite.conf /etc/httpd/conf.d/graphite.conf')
    sed('/etc/httpd/conf.d/graphite.conf', '@DJANGO_ROOT@', django_root, use_sudo=True)
    sed('/etc/httpd/conf.d/graphite.conf', '@PYTHON_ROOT@', python_root, use_sudo=True)
    # supervisord config
    sudo('rm /etc/supervisord.conf; ln -s /opt/config/etc/supervisord.conf /etc/supervisord.conf')
    sed('/etc/supervisord.conf', '@PYTHON@', python, use_sudo=True)
    # statsd config
    sudo('rm /etc/statsd.js; ln -s /opt/config/etc/statsd.js /etc/statsd.js')
    sed('/etc/statsd.js', '@GRAPHITE_HOST@', env.graphite_host, use_sudo=True)
    # fix permissions
    if exists('~/.virtualenvs'):
        sudo('chown -R %(user)s /home/%(user)s/.virtualenvs' % env)

def start_supervisord():
    """
    starts supervisord (installs it first, if not present).
    this starts all the configured services as well.
    """
    if not exists('/opt/virtualenvs/%(venv_name)s/bin/supervisord' % env):
        with prefix('workon %(venv_name)s' % env):
            run('pip install supervisor')
    sudo('/opt/virtualenvs/%(venv_name)s/bin/supervisord' % env)

def start_services():
    """
    starts the configured services and keeps them running.
    """
    sudo('/opt/virtualenvs/%(venv_name)s/bin/supervisorctl start apache' % env)
    sudo('/opt/virtualenvs/%(venv_name)s/bin/supervisorctl start carbon' % env)
    sudo('/opt/virtualenvs/%(venv_name)s/bin/supervisorctl start node' % env)
    check_services()

def check_services():
    """
    see if the configured services are running.
    """
    sudo('/opt/virtualenvs/%(venv_name)s/bin/supervisorctl status' % env)
    # derive url of an graphite image
    with hide('running', 'stdout'):
        hostname = run('uname -n')
    image_url = 'http://%s/render/?target=carbon.agents.%s.pointsPerUpdate' % (env.graphite_host, hostname)
    print image_url
    # open the image
    import urllib2
    req = urllib2.Request(image_url)
    # check the response code
    response = urllib2.urlopen(req)
    # tell it like it is
    if response.getcode() == 200:
        print "graphite seems to be running"
    else:
        print "something wrong with graphite installation"

def stop_services():
    """
    takes the configured services down nicely.
    """
    sudo('/opt/virtualenvs/%(venv_name)s/bin/supervisorctl stop apache' % env)
    sudo('/opt/virtualenvs/%(venv_name)s/bin/supervisorctl stop carbon' % env)
    sudo('/opt/virtualenvs/%(venv_name)s/bin/supervisorctl stop node' % env)
    check_services()

def setup():
    """
    performs the required steps to install statsd and graphite.
    """
    require('hosts', provided_by=[ ec2 ])
    sudo('yum -y -q install bzr screen mlocate make gcc gcc-c++ python26-devel httpd-devel')
    install_dtach()
    install_nodejs()
    install_cairo()
    install_mod_wsgi()
    configure_shell()
    install_virtualenv()
    install_graphite()
    configure_services()
    start_supervisord()
    check_services()
