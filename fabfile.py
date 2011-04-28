#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fabric.api import *
from fabric.context_managers import cd
from fabric.contrib.files import append, sed
import os

def stage():
    env.hosts = ['ec2-46-51-165-44.eu-west-1.compute.amazonaws.com']
    env.host_family = 'stage'
    env.user = 'ec2-user'
    env.key_filename = os.path.join(os.path.expanduser('~'), '.ssh', 'svti-frank.pem')
    env.virtualenv_home = '/opt/virtualenvs'
    env.venv_name = 'test'

def install_virtualenv():
    sudo('easy_install pip')
    sudo('pip install virtualenv virtualenvwrapper')
    sudo('mkdir -p %(virtualenv_home)s' % env)
    sudo('chown -R %(user)s %(virtualenv_home)s' % env)
    with cd('%(virtualenv_home)s' % env):
        run('mkvirtualenv --no-site-packages %(venv_name)s' % env)

def install_nodejs():
    sudo('yum install -y gcc-c++ openssl-devel curl libssl-dev apache2-utils git-core')
    with cd('/tmp/'):
        sudo('rm -rf node')
        run('git clone https://github.com/joyent/node.git')
        with cd('node'):
            run('./configure && make')
            sudo('make install')
        sudo('rm -rf npm')
        run('git clone git://github.com/isaacs/npm.git')
        with cd('node'):
            sudo('env PATH=/usr/local/bin/:$PATH make install')

def install_py2cairo():
    """following instructions at:
        http://agiletesting.blogspot.com/2011_04_01_archive.html
        http://graphite.readthedocs.org/en/latest/install.html"""
    sudo('yum -y install pkgconfig libpng-devel freetype-devel')
    with cd('/tmp'):
        # install pixman
        run('wget http://cairographics.org/releases/pixman-0.20.2.tar.gz')
        run('tar xfz pixman-0.20.2.tar.gz')
        with cd('pixman-0.20.2'):
            with prefix('export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig'):
                run('./configure && make')
            sudo('make install')
        # install cairo
        run('wget http://cairographics.org/releases/cairo-1.10.2.tar.gz')
        run('tar xfz cairo-1.10.2.tar.gz')
        with cd('cairo-1.10.2'):
            with prefix('export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig'):
                run('./configure --enable-xml && make')
            sudo('make install')
    # install py2cairo
    with prefix('workon %(venv_name)s' % env):
        with prefix('export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig'):
            # "pip install py2cairo" picks python3.0 version of py2cairo!
            run('pip install http://www.cairographics.org/releases/py2cairo-1.8.10.tar.gz')

def install_graphite():
    sudo('test -e /opt/graphite || mkdir /opt/graphite')
    sudo('chown -R %(user)s /opt/graphite' % env)
    with prefix('workon %(venv_name)s' % env):
        run('pip install http://launchpad.net/graphite/0.9/0.9.8/+download/carbon-0.9.8.tar.gz')
        run('pip install http://launchpad.net/graphite/0.9/0.9.8/+download/whisper-0.9.8.tar.gz')
        run('pip install http://launchpad.net/graphite/0.9/0.9.8/+download/graphite-web-0.9.8.tar.gz')
    sudo('chown -R %(user)s /opt/graphite/storage/log/' % env)
    with prefix('workon %(venv_name)s' % env):
        run('pip install django')
        run('cd /opt/graphite/webapp/graphite; python manage.py syncdb --noinput')
        sudo('test -e /opt/graphite/storage/log/webapp || mkdir -p /opt/graphite/storage/log/webapp')
        sudo('chown -R apache:apache /opt/graphite/storage/log/webapp')

def install_mod_wsgi():
    with cd('/tmp'):
        sudo('wget http://modwsgi.googlecode.com/files/mod_wsgi-3.3.tar.gz')
        sudo('tar -xzvf mod_wsgi-3.3.tar.gz')
        with cd('mod_wsgi-3.3'):
            sudo('./configure -with-python=/usr/bin/python2.6')
            sudo('make')
            sudo('make install')
        sudo('rm -rf mod_wsgi-3.3.tar.gz mod_wsgi-3.3')

def configure():
    # get latest config in place
    run('wget https://bitbucket.org/svtidevelopers/statistik/get/tip.tar.gz')
    run('tar xfz tip.tar.gz')
    with cd('svtidevelopers-statistik-*'):
        sudo('rm -rf /opt/config; mv config /opt/')
        sudo('rm -rf /opt/statsd; mv statsd /opt/')
    run('rm -rf tip.tar* svtidevelopers-statistik-*')
    # convenience files
    run('rm ~/.screenrc; ln -s /opt/config/screenrc ~/.screenrc')
    run('rm ~/.bashrc; ln -s /opt/config/bashrc ~/.bashrc')
    run('rm ~/.hgrc; ln -s /opt/config/hgrc ~/.hgrc')
    # graphite config files
    sudo('rm /opt/graphite/conf/graphite.wsgi; ln -s /opt/config/opt/graphite/conf/graphite.wsgi /opt/graphite/conf/graphite.wsgi')
    sudo('rm /opt/graphite/conf/carbon.conf; ln -s /opt/config/opt/graphite/conf/carbon.conf /opt/graphite/conf/carbon.conf')
    sudo('rm /opt/graphite/conf/storage-schemas.conf; ln -s /opt/config/opt/graphite/conf/storage-schemas.conf /opt/graphite/conf/storage-schemas.conf')
    sudo('rm /opt/graphite/conf/dashboard.conf; ln -s /opt/config/opt/graphite/conf/dashboard.conf /opt/graphite/conf/dashboard.conf')
    # apache2 config files
    sudo('rm /etc/httpd/conf/httpd.conf; ln -s /opt/config/etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf')
    sudo('rm /etc/httpd/conf.d/graphite.conf; ln -s /opt/config/etc/httpd/conf.d/graphite.conf /etc/httpd/conf.d/graphite.conf')
    with prefix('workon %(venv_name)s' % env):
        python_root = run("""python -c 'from pkg_resources import get_distribution; print get_distribution("django").location'""")
        django_root = run("""cd /; python -c 'print __import__("django").__path__[0]'""")
    sed('/etc/httpd/conf.d/graphite.conf', '@DJANGO_ROOT@', django_root, use_sudo=True)
    sed('/etc/httpd/conf.d/graphite.conf', '@PYTHON_ROOT@', python_root, use_sudo=True)
    # statsd config
    sudo('rm /etc/statsd.js; ln -s /opt/config/etc/statsd.js /etc/statsd.js')
    sed('/etc/statsd.js', '@GRAPHITE_HOST@', env.hosts[0], use_sudo=True)

def start_services():
    require('hosts', provided_by=[ stage ])
    with prefix('workon %(venv_name)s' % env):
        venv_python = run('which python')
    with settings(warn_only=True):
        sudo('/usr/sbin/apachectl restart', pty=True)
        sudo('%s /opt/graphite/bin/carbon-cache.py start' % venv_python)
    sudo('nohup /usr/local/bin/node /opt/statsd/stats.js /etc/statsd.js &')

def setup():
    require('hosts', provided_by=[ stage ])
    sudo('yum -y install screen mlocate make gcc python-devel mercurial httpd-devel')
    install_mod_wsgi()
    install_virtualenv()
    install_py2cairo()
    install_graphite()
    configure()
    sudo('/usr/bin/updatedb')
    start_services()
