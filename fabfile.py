#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fabric.api import *
from fabric.context_managers import cd
from fabric.contrib.files import append, sed, exists
import os

def lab():
    env.hosts = ['10.20.61.148']
    env.user = 'si'
    env.password = 'si'
    env.virtualenv_home = '/opt/virtualenvs'
    env.venv_name = 'base'
    env.svtproxy = True
    env.python = '/usr/local/bin/python2.7'
    env.graphite_host = '10.20.61.145' # internal interface

def stage():
    env.hosts = ['ec2-46-51-158-60.eu-west-1.compute.amazonaws.com']
    env.user = 'ec2-user'
    env.key_filename = os.path.join(os.path.expanduser('~'), '.ssh', 'svti-frank.pem')
    env.virtualenv_home = '/opt/virtualenvs'
    env.venv_name = 'base'
    env.svtproxy = False
    env.python = '/usr/local/bin/python2.7'
    env.graphite_host = 'ec2-46-51-158-60.eu-west-1.compute.amazonaws.com'

def install_python27():
    """installs python 2.7.1 as /usr/local/bin/python2.7"""
    if exists('/usr/local/bin/python2.7'):
        return
    sudo('yum -y install bzip2-devel zlib-devel sqlite-devel')
    with cd('/tmp'):
        run('wget http://python.org/ftp/python/2.7.1/Python-2.7.1.tgz')
        with hide('running', 'stdout'):
            run('tar xfz  Python-2.7.1.tgz')
            with cd('Python-2.7.1'):
                run('./configure --enable-shared')
                sudo('make -i altinstall')
    append('/etc/ld.so.conf.d/python2.7.conf', '/usr/local/lib', use_sudo=True)
    sudo('/sbin/ldconfig')

def install_mod_wsgi():
    """installs mod_wsgi 3.3 using python 2.7"""
    if exists('/usr/lib64/httpd/modules/mod_wsgi.so') or exists('/usr/lib/httpd/modules/mod_wsgi.so'):
        return
    with cd('/tmp'):
        sudo('wget http://modwsgi.googlecode.com/files/mod_wsgi-3.3.tar.gz')
        sudo('tar -xzvf mod_wsgi-3.3.tar.gz')
        with cd('mod_wsgi-3.3'):
            sudo('./configure -with-python=%(python)s' % env)
            sudo('make')
            sudo('make install')
        sudo('rm -rf mod_wsgi-3.3.tar.gz mod_wsgi-3.3')

def install_virtualenv():
    """installs virtualenv and virtualenvwrapper"""
    if exists('/usr/local/bin/virtualenvwrapper.sh'):
        return
    with cd('/tmp'):
        run('wget http://python-distribute.org/distribute_setup.py')
        sudo('%(python)s distribute_setup.py' % env)
    with prefix('export VIRTUALENVWRAPPER_PYTHON=%(python)s && unset PIP_REQUIRE_VIRTUALENV' % env):
        sudo('/usr/local/bin/easy_install -U pip')
        sudo('/usr/local/bin/pip install -U virtualenv virtualenvwrapper')
        run('/usr/local/bin/virtualenvwrapper.sh')
    sudo('mkdir -p %(virtualenv_home)s' % env)
    sudo('chown -R %(user)s %(virtualenv_home)s' % env)

def configure_shell():
    """gets the latest configuration files in place"""
    run('wget https://bitbucket.org/svtidevelopers/statistik/get/tip.tar.gz')
    run('tar xfz tip.tar.gz')
    with cd('svtidevelopers-statistik-*'):
        sudo('rm -rf /opt/config; mv config /opt/')
        sudo('rm -rf /opt/statsd; mv statsd /opt/')
    run('rm -rf tip.tar* svtidevelopers-statistik-*')
    # convenience files
    run('rm ~/.screenrc; ln -s /opt/config/screenrc ~/.screenrc')
    run('rm ~/.bashrc; ln -s /opt/config/bashrc ~/.bashrc')
    if env.svtproxy:
        append('~/.bashrc', 'export http_proxy=http://proxy.svt.se:8080')
        append('~/.bashrc', 'export https_proxy=https://proxy.svt.se:8080')
    with cd('%(virtualenv_home)s' % env):
        run('mkvirtualenv --no-site-packages %(venv_name)s' % env)

def install_nodejs():
    """installs node.js from trunk"""
    if exists('/usr/local/bin/node'):
        return
    sudo('yum install -y openssl-devel')
    with cd('/tmp/'):
        sudo('rm -rf node')
        run('curl -L https://github.com/joyent/node/tarball/master -o node_trunk.tar.gz')
        run('tar xfz node_trunk.tar.gz')
        with cd('joyent-node*'):
            run('./configure && make')
            sudo('make install')

def install_cairo():
    """installs cairo backend"""
    # http://graphite.readthedocs.org/en/latest/install.html
    # http://agiletesting.blogspot.com/2011_04_01_archive.html
    if exists('/usr/local/lib/libcairo.so'):
        return
    sudo('yum -y install pkgconfig valgrind-devel libpng-devel freetype-devel fontconfig-devel')
    with cd('/tmp'):
        # install pixman
        sudo('rm -rf pixman*')
        run('wget http://cairographics.org/releases/pixman-0.20.2.tar.gz')
        run('tar xfz pixman-0.20.2.tar.gz')
        with cd('pixman-0.20.2'):
            with prefix('export PKG_CONFIG_PATH=/usr/lib/pkgconfig:/usr/lib64/pkgconfig:/usr/local/lib/pkgconfig'):
                run('./configure && make')
            sudo('make install')
        # install cairo
        sudo('rm -rf cairo*')
        run('wget http://cairographics.org/releases/cairo-1.10.2.tar.gz')
        run('tar xfz cairo-1.10.2.tar.gz')
        with cd('cairo-1.10.2'):
            with prefix('export PKG_CONFIG_PATH=/usr/lib/pkgconfig:/usr/lib64/pkgconfig:/usr/local/lib/pkgconfig'):
                run('./configure --enable-xlib=no --disable-gobject && make')
            sudo('make install')

def install_py2cairo():
    """install py2cairo in virtualenv"""
    with prefix('workon %(venv_name)s' % env):
        with prefix('export PKG_CONFIG_PATH=/usr/lib/pkgconfig:/usr/lib64/pkgconfig:/usr/local/lib/pkgconfig'):
            # "pip install py2cairo" picks python3.0 version of py2cairo!
            run('pip install http://www.cairographics.org/releases/py2cairo-1.8.10.tar.gz')

def install_bzr():
    """installs bzr on redhat5"""
    if not exists('/usr/bin/bzr'):
        with cd('/tmp'):
            run('curl -O http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-4.noarch.rpm')
            run('sudo rpm -Uvh epel-release-5-4.noarch.rpm')
        sudo('yum -y install bzr')

def install_graphite():
    """installs graphite from trunk"""
    # create target dir with correct permissions
    sudo('test -e /opt/graphite || mkdir /opt/graphite')
    sudo('chown -R %(user)s /opt/graphite' % env)
    # hm I cannot branch with bzr through the proxy https://bugs.launchpad.net/bzr/+bug/198646
    # and I cannot download an arbitrary version as tarball from launchpad https://bugs.launchpad.net/loggerhead/+bug/240580
    # hence:
    if not exists('~/graphite_trunk.tar.gz'):
        put('graphite_trunk.tar.gz')
    run('tar xfz graphite_trunk.tar.gz')
    with prefix('workon %(venv_name)s' % env):
        run('pip install python-memcached simplejson')
        with prefix('export PKG_CONFIG_PATH=/usr/lib/pkgconfig:/usr/lib64/pkgconfig:/usr/local/lib/pkgconfig'):
            #run('pip install http://launchpad.net/graphite/1.0/0.9.8/+download/graphite-web-0.9.8.tar.gz')
            with cd('graphite_trunk'):
                run('pip install .')
            run('pip install http://launchpad.net/graphite/1.0/0.9.8/+download/carbon-0.9.8.tar.gz')
            run('pip install http://launchpad.net/graphite/1.0/0.9.8/+download/whisper-0.9.8.tar.gz')
            run('pip install django')
        run('cd /opt/graphite/webapp/graphite; python manage.py syncdb --noinput')
    sudo('test -e /opt/graphite/storage/log/webapp || mkdir -p /opt/graphite/storage/log/webapp')
    sudo('chown -R apache:apache /opt/graphite/storage')

def configure_services():
    # graphite config files
    sudo('rm /opt/graphite/conf/graphite.wsgi; ln -s /opt/config/opt/graphite/conf/graphite.wsgi /opt/graphite/conf/graphite.wsgi')
    sudo('rm /opt/graphite/conf/storage-schemas.conf; ln -s /opt/config/opt/graphite/conf/storage-schemas.conf /opt/graphite/conf/storage-schemas.conf')
    sudo('rm /opt/graphite/conf/dashboard.conf; ln -s /opt/config/opt/graphite/conf/dashboard.conf /opt/graphite/conf/dashboard.conf')
    sudo('rm /opt/graphite/conf/carbon.conf; ln -s /opt/config/opt/graphite/conf/carbon.conf /opt/graphite/conf/carbon.conf')
    sudo('rm /opt/graphite/webapp/graphite/local_settings.py; ln -s /opt/config/opt/graphite/webapp/graphite/local_settings.py /opt/graphite/webapp/graphite/local_settings.py')
    # apache2 config files
    sudo('rm /etc/httpd/conf/httpd.conf; ln -s /opt/config/etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf')
    sudo('rm /etc/httpd/conf.d/graphite.conf; ln -s /opt/config/etc/httpd/conf.d/graphite.conf /etc/httpd/conf.d/graphite.conf')
    # fix permissions
    if exists('~/.virtualenvs'):
        sudo('chown -R %(user)s /home/%(user)s/.virtualenvs' % env)
    with prefix('workon %(venv_name)s' % env):
        python_root = run("""python -c 'from pkg_resources import get_distribution; print get_distribution("django").location'""")
        django_root = run("""cd /; python -c 'print __import__("django").__path__[0]'""")
    sed('/etc/httpd/conf.d/graphite.conf', '@DJANGO_ROOT@', django_root, use_sudo=True)
    sed('/etc/httpd/conf.d/graphite.conf', '@PYTHON_ROOT@', python_root, use_sudo=True)
    # statsd config
    sudo('rm /etc/statsd.js; ln -s /opt/config/etc/statsd.js /etc/statsd.js')
    sed('/etc/statsd.js', '@GRAPHITE_HOST@', env.graphite_host, use_sudo=True)

def start_services():
    require('hosts', provided_by=[ stage, lab ])
    with prefix('workon %(venv_name)s' % env):
        venv_python = run('which python')
    with settings(warn_only=True):
        sudo('/usr/sbin/apachectl start')
        sudo('%s /opt/graphite/bin/carbon-cache.py start' % venv_python)
    sudo('nohup /usr/local/bin/node /opt/statsd/stats.js /etc/statsd.js &')
    check_services()

def check_services():
    # psa is a macro in .bashrc
    with settings(warn_only=True):
        run('psa statsd')
        run('psa carbon')
        run('psa httpd')
    # derive url of an graphite image
    with hide('running', 'stdout'):
        hostname = run('uname -n')
    image_url = 'http://%s/render/?target=carbon.agents.%s.pointsssPerUpdate' % (env.hosts[0], hostname)
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
    require('hosts', provided_by=[ stage, lab ])
    with prefix('workon %(venv_name)s' % env):
        venv_python = run('which python')
    with settings(warn_only=True):
        sudo('/usr/sbin/apachectl stop')
        sudo('%s /opt/graphite/bin/carbon-cache.py stop' % venv_python)
        sudo('killall node')
    check_services()

def setup():
    require('hosts', provided_by=[ stage, lab ])
    if env.svtproxy:
        append('/etc/profile.d/proxy.sh', 'export http_proxy=http://proxy.svt.se:8080', use_sudo=True)
        append('/etc/profile.d/proxy.sh', 'export https_proxy=https://proxy.svt.se:8080', use_sudo=True)
        append('~/.bashrc', 'export http_proxy=http://proxy.svt.se:8080')
        append('~/.bashrc', 'export https_proxy=https://proxy.svt.se:8080')
    sudo('yum -y install screen mlocate mercurial')
    sudo('yum -y install make gcc gcc-c++ httpd-devel')
    install_python27()
    install_mod_wsgi()
    install_virtualenv()
    configure_shell()
    install_cairo()
    install_py2cairo()
    install_graphite()
    install_nodejs()
    configure_services()
    sudo('/usr/bin/updatedb')
    start_services()
