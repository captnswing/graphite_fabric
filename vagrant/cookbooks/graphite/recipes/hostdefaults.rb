case node[:platform]
when "ubuntu","debian"
    execute "apt-get update" do
        action :run
    end
end

packages = value_for_platform(
    ["centos","redhat","fedora","amazon"] =>
        {"default" => ["screen", "bash-completion"]},
    ["ubuntu","debian"] =>
        {"default" => ["screen", "bash-completion"]}
)

packages.each do |dev_pkg|
  package dev_pkg
end

execute "update_locale" do
    user "root"
    command "locale-gen sv_SE.UTF-8; update-locale LANG=sv_SE.UTF-8"
end

cookbook_file "/home/vagrant/.bashrc" do
    source ".bashrc"
    owner "vagrant"
    group "vagrant"
    mode 0755
end

cookbook_file "/home/vagrant/.screenrc" do
    source ".screenrc"
    owner "vagrant"
    group "vagrant"
    mode 0644
end
