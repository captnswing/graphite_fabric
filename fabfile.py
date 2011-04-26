#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fabric.api import *
from fabric.context_managers import cd, hide, settings
from fabric.contrib.files import append, exists, sed
import os

import time

def stage():
    env.hosts = ['ec2-79-125-29-204.eu-west-1.compute.amazonaws.com']
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
    VIRTUALENV_BASHRC="""
    test -r /usr/bin/virtualenvwrapper.sh && . /usr/bin/virtualenvwrapper.sh
    export WORKON_HOME=%(virtualenv_home)s
    export PIP_VIRTUALENV_BASE=$WORKON_HOME
    # To tell pip to only run if there is a virtualenv currently activated, and to bail if not, use:
    export PIP_REQUIRE_VIRTUALENV=true""" % env
    bashrc_lines = [ l.strip() for l in VIRTUALENV_BASHRC.splitlines() if l.strip() ]
    append('~/.bashrc', bashrc_lines)
    with cd('%(virtualenv_home)s' % env):
        run('mkvirtualenv --no-site-packages %(venv_name)s' % env)
          
def install_cairo():
    """following instructions at:
        http://agiletesting.blogspot.com/2011_04_01_archive.html
        http://graphite.readthedocs.org/en/latest/install.html"""
    sudo('yum -y install pkgconfig libpng libpng-devel freetype freetype-devel')
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
        django_root = run("""python -c 'from pkg_resources import get_distribution; print get_distribution("django").location'""")
    with cd('/opt/graphite/conf'):
        run('cp graphite.wsgi.example graphite.wsgi')
        run('cp carbon.conf.example carbon.conf')
        run('cp storage-schemas.conf.example storage-schemas.conf')
    with cd('graphite-web-0.9.8'):
        sed('examples/example-graphite-vhost.conf', '@DJANGO_ROOT@', django_root)
        run("sed -i '1iLoadModule wsgi_module modules/mod_wsgi.so' examples/example-graphite-vhost.conf")
        sudo('cp examples/example-graphite-vhost.conf /etc/httpd/conf.d/graphite.conf')

def install_mod_wsgi():
    if not exists('/usr/lib64/httpd/modules/mod_wsgi.so'):
        with cd('/tmp'):
            sudo('wget http://modwsgi.googlecode.com/files/mod_wsgi-3.3.tar.gz')
            sudo('tar -xzvf mod_wsgi-3.3.tar.gz')
            with cd('mod_wsgi-3.3'):
                sudo('./configure -with-python=/usr/bin/python2.6')
                sudo('make')
                sudo('make install')
            sudo('rm -rf mod_wsgi-3.3.tar.gz mod_wsgi-3.3')
    else:
        run('echo "mod_wsgi already installed"')

def setup():
    """
    Setup a fresh virtualenv as well as a few useful directories, then run
    a full deployment
    """
    require('hosts', provided_by=[ stage ])
    # install required packages
    sudo('yum -y install screen mlocate make gcc python-devel')
    sudo('/usr/bin/updatedb')
    put(os.path.join(os.path.expanduser('~'), '.screenrc'))
#   install_mod_wsgi
#   install_virtualenv()
#   install_pycairo()
    install_graphite()