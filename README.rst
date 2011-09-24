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
    :width: 800 px

The instance need to be configured with a security group that has the necessary UDP / TCP ports opened.

.. image:: https://bitbucket.org/captnswing/graphite_fabfile/raw/default/ec2firewall.png
    :width: 500 px


Local machine
-------------

On your local machine, you need python2 >= 2.6 and python-fabric_

::

    pip install fabric

Installing graphite with this fabfile
=====================================

Once fabric is installed, and the ec2 instance is running,
test that you are able to ssh into your EC2 instance, using something like

::

    ssh -i ~/.ssh/myec2key.pem ec2-user@ec2-xxx-xxx-xxx-xxx.eu-west-1.compute.amazonaws.com

Then just invoke

::

    fab -i <path to EC2 .pem> -H <EC2 hostname> setup

in the directory that contains this file.

Starting & stopping graphite
----------------------------

On the EC2 host, ``supervisord`` takes care of running apache httpd, graphite carbon and node.js statsd services.

You can check the status of these services by invoking

::

    fab -i <path to EC2 .pem> -H <EC2 hostname> graphite:status

Also

::

    fab -i <path to EC2 .pem> -H <EC2 hostname> graphite:stop
    fab -i <path to EC2 .pem> -H <EC2 hostname> graphite:start

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

