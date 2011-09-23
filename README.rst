Overview
========

fabric script that installs graphite-trunk and Etsy's statsd on an Amazon EC2 linux instance.

On the way, it installs all of graphite's dependencies: http://graphite.readthedocs.org/en/latest/install.html

taking some clues from: http://agiletesting.blogspot.com/2011/04/installing-and-configuring-graphite.html

Prerequisits
============

Amazon EC2
----------

Suitable Amazon EC2 linux instance (I use ``Basic 64-bit Amazon Linux AMI 2011.02.1 Beta``)

.. image:: https://bitbucket.org/captnswing/graphite_fabfile/raw/860484efac99/ec2instance.png

The instance need to be configured with a security group that has the necessary UDP / TCP ports opened.

.. image:: https://bitbucket.org/captnswing/graphite_fabfile/raw/860484efac99/ec2firewall.png


Local machine
-------------

On your local machine, you need python2 >= 2.6 and python-fabric http://docs.fabfile.org

::

    pip install fabric

Running the script
==================

once fabric is installed, and the ec2 instance is running, just paste the hostname of the
instance into the ec2 function's ``env.hosts`` variable.

Also, change the name of the keypair used to create the instance in the ec2 function's ``env.key_filename`` variable.
The keypair need to be available in your local ``.ssh`` directory, you should be able to ssh into your instance before proceeding.

Then just invoke

::

    $ fab ec2 setup

in the directory that contains this file.
