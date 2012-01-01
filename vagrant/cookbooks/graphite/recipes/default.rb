# some sane defaults for the host
include_recipe "graphite::hostdefaults"

# installing python, pip and virtualenv
include_recipe "python::source"
include_recipe "python::pip"
include_recipe "python::virtualenv"

# installing graphite
include_recipe "graphite::cairo"
include_recipe "graphite::graphite"

directory "#{node[:venv]}/run" do
    recursive true
    owner "vagrant"
    group "vagrant"
    mode 0775
end

template "/etc/init/gunicorn.conf" do
    source "gunicorn.conf.erb"
    owner "root"
    group "root"
    mode 0644
end

service "gunicorn" do
    provider Chef::Provider::Service::Upstart
    enabled true
    running true
    supports :restart => true, :reload => true, :status => true
    action [:enable, :start]
end

# installing statsd
include_recipe "nodejs"
include_recipe "graphite::statsd"

#service "statsd" do
#  provider Chef::Provider::Service::Upstart
#  #subscribes :restart, resources(:git => "/opt/statsd")
#  start_command '/usr/local/bin/node /opt/statsd/stats.js /etc/statsd.js'
##  supports :restart => true, :start => true, :stop => true
#end
