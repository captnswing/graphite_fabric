# some sane defaults for the virtual machine
include_recipe "graphite::hostdefaults"

# installing python, pip and virtualenv
include_recipe "python::source"
include_recipe "python::pip"
include_recipe "python::virtualenv"

# installing graphite
include_recipe "graphite::cairo"
include_recipe "graphite::graphite"

# installing statsd
include_recipe "nodejs"
include_recipe "graphite::statsd"

# install and run supervisor
include_recipe "graphite::supervisor"
