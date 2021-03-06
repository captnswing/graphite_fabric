# Introduction

Inspired by Etsy's seminal blogpost [Measure anything, measure everything](http://codeascraft.etsy.com/2011/02/15/measure-anything-measure-everything),
w
It turned out to be quite a bit more involved than

    sudo yum -y install graphite statsd     # yeah I wish...

This fabric script is the result of my effort to trace my steps while trying to get everything
work together and up and running (I took some clues from [Grig Gheorghiu](http://agiletesting.blogspot.com/2011/04/installing-and-configuring-graphite.html)).

I use the script to automatically install statsd and Graphite (and its [dependencies](http://graphite.readthedocs.org/en/latest/install.html)) from trunk on any standard Amazon EC2 linux instance.

On an `m1.large` EC2 instance, this script is finished within 8minutes.

Works on my machines, YMMV!

# Prerequisits

## Amazon EC2

Suitable Amazon EC2 linux instance (I often use `Basic 64-bit Amazon Linux AMI 2011.02.1 Beta`
on an `m1.large` machine)

![image](https://raw.github.com/captnswing/graphite_fabric/master/ec2instance.png)

The instance need to be configured with a security group that has the necessary UDP / TCP ports opened.

![image](https://raw.github.com/captnswing/graphite_fabric/master/ec2firewall.png)

## Local machine

On your local machine, you need mercurial, python2 >= 2.6 and [python-fabric](http://docs.fabfile.org)

    pip install fabric

# Installing graphite with this fabfile

Once fabric is installed, and the EC2 instance is running,
test that you are able to ssh into your EC2 instance, using something like

    ssh -i ~/.ssh/myec2key.pem ec2-user@ec2-xxx-xxx-xxx-xxx.eu-west-1.compute.amazonaws.com

Then just invoke

    curl -O https://bitbucket.org/captnswing/graphite_fabfile/raw/default/fabfile.py
    fab -i <path to EC2 .pem> -H <EC2 hostname> setup

## Starting & stopping graphite

On the EC2 host, `supervisord` takes care of running apache httpd, graphite carbon and node.js statsd services.

You can check the status of these services by invoking

    fab -i <path to EC2 .pem> -H <EC2 hostname> graphite:status

Also

    fab -i <path to EC2 .pem> -H <EC2 hostname> graphite:stop
    fab -i <path to EC2 .pem> -H <EC2 hostname> graphite:start

does what you think it does.

## Getting data into your graphite

Check out the graphite / statsd clients here

* [https://github.com/etsy/statsd](https://github.com/etsy/statsd)
* [https://github.com/sivy/statsd-client](https://github.com/sivy/statsd-client)
* [https://github.com/dawanda/statsd-client](https://github.com/dawanda/statsd-client)
* [https://github.com/bvandenbos/statsd-client](https://github.com/bvandenbos/statsd-client)
* many more...



