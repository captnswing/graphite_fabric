#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fabric.api import *
from fabric.context_managers import cd
from fabric.contrib.files import append, sed, exists
import os

def ec2():
    env.hosts = ['ec2-46-51-158-241.eu-west-1.compute.amazonaws.com']
    env.user = 'ec2-user'
    env.key_filename = os.path.join(os.path.expanduser('~'), '.ssh', 'svti-frank.pem')
    env.virtualenv_home = '/opt/virtualenvs'
    env.venv_name = 'base'
    env.svtproxy = False
    env.python = '/usr/bin/python'
    env.graphite_host = env.hosts[0]

def install_mod_wsgi():
    """installs mod_wsgi 3.3"""
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
    run('wget https://bitbucket.org/svtidevelopers/statistik/get/tip.tar.gz')
    run('tar xfz tip.tar.gz')
    with cd('svtidevelopers-statistik-*'):
        sudo('rm -rf /opt/config; mv config /opt/')
        sudo('rm -rf /opt/statsd; mv statsd /opt/')
    run('rm -rf tip.tar* svtidevelopers-statistik-*')
    # shell config
    run('rm ~/.screenrc; ln -s /opt/config/screenrc ~/.screenrc')
    run('rm ~/.bashrc; ln -s /opt/config/bashrc ~/.bashrc')
    sed('~/.bashrc', '@PYTHON@', env.python)
    # proxy config
    if env.svtproxy:
        append('~/.bashrc', 'export http_proxy=http://proxy.svt.se:8080')
        append('~/.bashrc', 'export https_proxy=https://proxy.svt.se:8080')

def install_virtualenv():
    """installs virtualenv and virtualenvwrapper"""
    if exists('/usr/local/bin/virtualenvwrapper.sh'):
        return
    with cd('/tmp'):
        run('wget http://python-distribute.org/distribute_setup.py')
        sudo('%(python)s distribute_setup.py' % env)
    with prefix('export VIRTUALENVWRAPPER_PYTHON=%(python)s && unset PIP_REQUIRE_VIRTUALENV' % env):
        sudo('/usr/bin/easy_install -U pip')
        sudo('/usr/bin/pip install -U virtualenv virtualenvwrapper')
        run('/usr/bin/virtualenvwrapper.sh')
    sudo('chown -R %(user)s %(virtualenv_home)s' % env)
    # create virtualenv
    with cd('%(virtualenv_home)s' % env):
        run('mkvirtualenv --no-site-packages %(venv_name)s' % env)

def install_dtach():
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
    """installs node.js from trunk"""
    if exists('/usr/local/bin/node'):
        return
    sudo('yum install -y -q openssl-devel')
    with cd('/tmp/'):
        sudo('rm -rf node joyent-node*')
        run('curl -L https://github.com/joyent/node/tarball/master -o node_trunk.tar.gz')
        run('tar xfz node_trunk.tar.gz')
        with cd('joyent-node*'):
            run('./configure')
            # see http://docs.fabfile.org/en/1.0.1/faq.html#why-can-t-i-run-programs-in-the-background-with-it-makes-fabric-hang
            sudo('/usr/local/bin/dtach -n /tmp/node make install')

def install_cairo():
    """installs cairo backend"""
    # http://graphite.readthedocs.org/en/latest/install.html
    # http://agiletesting.blogspot.com/2011_04_01_archive.html
    if exists('/usr/local/lib/libcairo.so'):
        return
    sudo('yum -y -q install pkgconfig valgrind-devel libpng-devel freetype-devel fontconfig-devel')
    with cd('/tmp'):
        # install pixman
        sudo('rm -rf pixman*')
        #run('wget http://cairographics.org/releases/pixman-0.20.2.tar.gz')
        run('wget http://svti-packages.s3.amazonaws.com/pixman-0.20.2.tar.gz')
        run('tar xfz pixman-0.20.2.tar.gz')
        with cd('pixman-0.20.2'):
            with prefix('export PKG_CONFIG_PATH=/usr/lib/pkgconfig:/usr/lib64/pkgconfig:/usr/local/lib/pkgconfig'):
                run('./configure')
            sudo('make install')
        # install cairo
        sudo('rm -rf cairo*')
        #run('wget http://cairographics.org/releases/cairo-1.10.2.tar.gz')
        run('wget http://svti-packages.s3.amazonaws.com/cairo-1.10.2.tar.gz')
        run('tar xfz cairo-1.10.2.tar.gz')
        with cd('cairo-1.10.2'):
            with prefix('export PKG_CONFIG_PATH=/usr/lib/pkgconfig:/usr/lib64/pkgconfig:/usr/local/lib/pkgconfig'):
                run('./configure --enable-xlib=no --disable-gobject')
            sudo('make install')

def install_py2cairo():
    """install py2cairo in virtualenv"""
    with prefix('workon %(venv_name)s' % env):
        with prefix('export PKG_CONFIG_PATH=/usr/lib/pkgconfig:/usr/lib64/pkgconfig:/usr/local/lib/pkgconfig'):
            # "pip install py2cairo" picks python3.0 version of py2cairo!
            run('pip install http://www.cairographics.org/releases/py2cairo-1.8.10.tar.gz')

def install_graphite():
    """installs graphite from trunk"""
    # create target dir with correct permissions
    sudo('test -e /opt/graphite || mkdir /opt/graphite')
    sudo('chown -R %(user)s /opt/graphite' % env)
    # hm I cannot branch with bzr through the SVT proxy https://bugs.launchpad.net/bzr/+bug/198646
    # and I cannot download an arbitrary version as tarball from launchpad https://bugs.launchpad.net/loggerhead/+bug/240580
    # hence:
    run('wget http://svti-packages.s3.amazonaws.com/graphite_trunk.tar.gz')
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
    """
    extracts a tar archive of all config files into /opt/config tree and symlinks all files into place
    """
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
    if not exists('/opt/virtualenvs/base/bin/supervisord'):
        with prefix('workon %(venv_name)s' % env):
            run('pip install supervisor')
    sudo('/opt/virtualenvs/base/bin/supervisord')

def start_services():
    sudo('/opt/virtualenvs/base/bin/supervisorctl start apache')
    sudo('/opt/virtualenvs/base/bin/supervisorctl start carbon')
    sudo('/opt/virtualenvs/base/bin/supervisorctl start node')
    check_services()

def check_services():
    sudo('/opt/virtualenvs/base/bin/supervisorctl status')
    # derive url of an graphite image
    with hide('running', 'stdout'):
        hostname = run('uname -n')
    image_url = 'http://%s/render/?target=carbon.agents.%s.pointsPerUpdate' % (env.hosts[0], hostname)
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
    sudo('/opt/virtualenvs/base/bin/supervisorctl stop apache')
    sudo('/opt/virtualenvs/base/bin/supervisorctl stop carbon')
    sudo('/opt/virtualenvs/base/bin/supervisorctl stop node')
    check_services()

def setup():
    require('hosts', provided_by=[ ec2 ])
    sudo('mkdir -p %(virtualenv_home)s' % env)
    if env.svtproxy:
        append('/etc/profile.d/proxy.sh', 'export http_proxy=http://proxy.svt.se:8080', use_sudo=True)
        append('/etc/profile.d/proxy.sh', 'export https_proxy=https://proxy.svt.se:8080', use_sudo=True)
        append('~/.bashrc', 'export http_proxy=http://proxy.svt.se:8080')
        append('~/.bashrc', 'export https_proxy=https://proxy.svt.se:8080')
    sudo('yum -y -q install screen mlocate make gcc gcc-c++ python26-devel httpd-devel')
    # couldn't get 'screen -d -m' to work. hence dtach
    install_dtach()
    install_nodejs()
    install_cairo()
    install_mod_wsgi()
    configure_shell()
    install_virtualenv()
    install_py2cairo()
    install_graphite()
    configure_services()
    start_supervisord()
    check_services()