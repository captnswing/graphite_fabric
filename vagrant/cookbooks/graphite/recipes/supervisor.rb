directory "#{node[:venv]}/run" do
    recursive true
    owner "vagrant"
    group "vagrant"
    mode 0775
end

python_pip "supervisor" do
    virtualenv "#{node[:venv]}"
    action :install
end

template "/etc/supervisor.conf" do
    source "supervisor.conf.erb"
    owner "root"
    group "root"
    mode 0644
end
