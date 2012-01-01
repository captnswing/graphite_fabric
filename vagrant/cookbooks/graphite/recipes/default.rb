case node[:platform]
when "ubuntu","debian"
    execute "apt-get update" do
        action :run
    end
end

execute "update_locale" do
    user "root"
    command "locale-gen sv_SE.UTF-8; update-locale LANG=sv_SE.UTF-8"
end

#include_recipe "nodejs"
include_recipe "python::source"
include_recipe "python::pip"
include_recipe "python::virtualenv"
include_recipe "graphite::cairo"
include_recipe "graphite::graphite"
include_recipe "graphite::statsd"
