Introduction
============

fabric script that installs graphite-trunk and Etsy's statsd on an Amazon EC2 linux instance.

On the way, it installs all of graphite's dependencies_ (taking some clues from `Grig Gheorghiu`_)

Prerequisits
============

Amazon EC2
----------

Suitable Amazon EC2 linux instance (I use ``Basic 64-bit Amazon Linux AMI 2011.02.1 Beta``)

.. image:: https://bitbucket.org/captnswing/graphite_fabfile/raw/default/ec2instance.png
    :width: 600 px

The instance need to be configured with a security group that has the necessary UDP / TCP ports opened.

.. image:: https://bitbucket.org/captnswing/graphite_fabfile/raw/default/ec2firewall.png
    :width: 400 px


Local machine
-------------

On your local machine, you need python2 >= 2.6 and python-fabric_

::

    pip install fabric

Installing graphite with this fabfile
=====================================

Once fabric is installed, and the ec2 instance is running, just paste the hostname of the
instance into the ``EC2_HOSTNAME`` variable at the top of the script.

Also, change the name of the keypair used to create the instance in the ``EC2_KEYPAIR`` variable.
The keypair need to be available in your local ``.ssh`` directory, you should be able to ssh into your instance before proceeding.

Then just invoke

::

    fab ec2 setup

in the directory that contains this file.

Starting & stopping graphite
----------------------------

On the EC2 host, ``supervisord`` takes care of running apache httpd, graphite carbon and node.js statsd services.

You can check the status of these services by invoking

::

    fab ec2 check_services

Also

::

    fab ec2 stop_services
    fab ec2 start_services

does what you think it does.

Getting data into your graphite
-------------------------------

Check out the graphite / statsd clients here

* https://github.com/etsy/statsd
* https://github.com/sivy/statsd-client
* https://github.com/dawanda/statsd-client
* https://github.com/bvandenbos/statsd-client
* many more...

.. _python-fabric:  http://docs.fabfile.org
.. _dependencies: http://graphite.readthedocs.org/en/latest/install.html
.. _Grig Gheorghiu: http://agiletesting.blogspot.com/2011/04/installing-and-configuring-graphite.html

