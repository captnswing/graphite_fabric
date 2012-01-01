directory "/opt/graphite" do
    owner "vagrant"
    group "vagrant"
    mode 0775
end

directory "#{node[:venv]}" do
    recursive true
    owner "vagrant"
    group "vagrant"
    mode 0775
end

python_virtualenv "#{node[:venv]}" do
    # TODO
    interpreter "#{node[:python][:prefix_dir]}/bin/python"
    owner "vagrant"
    group "vagrant"
    action :create
end

%w{gunicorn python-memcached django django-tagging}.each do |pypkg|
    python_pip pypkg do
        virtualenv "#{node[:venv]}"
        action :install
    end
end

graphite_tarballs = ["http://www.cairographics.org/releases/py2cairo-1.8.10.tar.gz",
                     "http://launchpadlibrarian.net/82112367/whisper-0.9.9.tar.gz",
                     "http://launchpadlibrarian.net/82112362/carbon-0.9.9.tar.gz",
                     "http://launchpadlibrarian.net/82112308/graphite-web-0.9.9.tar.gz"]

graphite_tarballs.each do |remote_tball|
    # TODO
    local_tball = "#{node[:srcdir]}/" + File.basename(remote_tball)
    remote_file local_tball do
        source remote_tball
        action :create_if_missing
        mode "0644"
    end
    python_pip local_tball do
        virtualenv "#{node[:venv]}"
        action :install
        # TODO
        #not_if "[ `pip freeze | grep #{pkg} | cut -d'=' -f3` = '#{version}' ]"
    end
end

execute "change_permissions" do
    cwd "/opt/graphite/storage"
    user "root"
    command "chown -R vagrant:vagrant ."
end

execute "managepy_syncdb" do
    cwd "/opt/graphite/webapp/graphite"
    user "vagrant"
    command ". #{node[:venv]}/bin/activate; python manage.py syncdb --noinput"
end
