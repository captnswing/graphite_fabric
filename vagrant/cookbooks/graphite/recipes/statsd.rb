include_recipe "nodejs"

directory "/opt/statsd" do
    owner "vagrant"
    group "vagrant"
    mode 0775
end

gitpkg = value_for_platform(
    ["centos","redhat","fedora","amazon"] =>
        {"default" => ["git"]},
    ["ubuntu","debian"] =>
        {"default" => ["git-core"]}
  )

gitpkg.each do |pkg|
  package pkg
end

git "/opt/statsd" do
    repository "https://github.com/etsy/statsd.git"
    action :export
    user "vagrant"
    group "vagrant"
end

template "statsd.js" do
  path "/etc/statsd.js"
  source "statsd.js.erb"
  owner "vagrant"
  group "vagrant"
  mode "0644"
end
