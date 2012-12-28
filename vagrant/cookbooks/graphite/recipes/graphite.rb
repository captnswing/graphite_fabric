include_recipe "graphite::cairo"

directory "/opt/graphite" do
  owner "vagrant"
  group "vagrant"
  mode 0775
end

directory "#{node[:graphite][:venv]}" do
  recursive true
  owner "vagrant"
  group "vagrant"
  mode 0775
end

python_virtualenv "#{node[:graphite][:venv]}" do
  # TODO
  interpreter "#{node[:python][:prefix_dir]}/bin/python"
  owner "vagrant"
  group "vagrant"
  action :create
end

%w{gunicorn python-memcached django django-tagging}.each do |pypkg|
  python_pip pypkg do
    virtualenv "#{node[:graphite][:venv]}"
    action :install
  end
end

# the tarballs composing the graphite application
graphite_tarballs = ["http://www.cairographics.org/releases/py2cairo-1.8.10.tar.gz",
                     "http://launchpadlibrarian.net/82112367/whisper-0.9.9.tar.gz",
                     "http://launchpadlibrarian.net/82112362/carbon-0.9.9.tar.gz",
                     "http://launchpadlibrarian.net/82112308/graphite-web-0.9.9.tar.gz"]

# install all the tarballs in the venv
graphite_tarballs.each do |remote_tball|
  local_tball = "#{node[:python][:srcdir]}/" + File.basename(remote_tball)
  remote_file local_tball do
    source remote_tball
    action :create_if_missing
    mode "0644"
  end
  python_pip local_tball do
    virtualenv "#{node[:graphite][:venv]}"
    action :install
    # TODO
    #not_if "[ `pip freeze | grep #{pkg} | cut -d'=' -f3` = '#{version}' ]"
  end
end

# 'import graphite' needs to work when in the virtualenv
execute "change_pythonpath" do
  cwd "#{node[:graphite][:venv]}/bin"
  user "vagrant"
  command "echo 'export PYTHONPATH=/opt/graphite/webapp:$PYTHONPATH' >>activate"
end

# change permissions so that vagrant user can write database
execute "change_permissions" do
  cwd "/opt/graphite/storage"
  user "root"
  command "chown -R vagrant:vagrant ."
end

# execute syncdb
execute "managepy_syncdb" do
  cwd "/opt/graphite/webapp/graphite"
  user "vagrant"
  command ". #{node[:graphite][:venv]}/bin/activate; python manage.py syncdb --noinput"
end

# install graphite.wsgi
template "graphite.wsgi" do
  path "/opt/graphite/conf/graphite.wsgi"
  source "graphite.wsgi.erb"
  owner "vagrant"
  group "vagrant"
  mode "0644"
  action :create
end

template "storage-schemas.conf" do
  path "/opt/graphite/conf/storage-schemas.conf"
  source "storage-schemas.conf.erb"
  owner "vagrant"
  group "vagrant"
  mode "0644"
  #notifies :restart, resources(:service => "redis")
end

template "dashboard.conf" do
  path "/opt/graphite/conf/dashboard.conf"
  source "dashboard.conf.erb"
  owner "vagrant"
  group "vagrant"
  mode "0644"
  #notifies :restart, resources(:service => "redis")
end

template "carbon.conf" do
  path "/opt/graphite/conf/carbon.conf"
  source "carbon.conf.erb"
  owner "vagrant"
  group "vagrant"
  mode "0644"
  #notifies :restart, resources(:service => "redis")
end

template "local_settings.py" do
  path "/opt/graphite/webapp/graphite/local_settings.py"
  source "local_settings.py.erb"
  owner "vagrant"
  group "vagrant"
  mode "0644"
  #notifies :restart, resources(:service => "redis")
end
