directory "#{node[:graphite][:venv]}/run" do
    recursive true
    owner "vagrant"
    group "vagrant"
    mode 0775
end

python_pip "supervisor" do
    virtualenv "#{node[:graphite][:venv]}"
    action :install
end

# configuration file for supervisord
template "/etc/supervisord.conf" do
    source "supervisord.conf.erb"
    owner "root"
    group "root"
    mode 0644
end

# init file for ubuntu upstart
template "/etc/init/supervisor.conf" do
    source "supervisor.conf.erb"
    owner "root"
    group "root"
    mode 0644
end

service "supervisor" do
    provider Chef::Provider::Service::Upstart
    enabled true
    running true
    supports :status => true, :start => true, :stop => true
    action [:enable, :start]
end
