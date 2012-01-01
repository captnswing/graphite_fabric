directory "/opt/statsd" do
    owner "vagrant"
    group "vagrant"
    mode 0775
end

packages = value_for_platform(
    ["centos","redhat","fedora","amazon"] =>
        {"default" => ["git"]},
    ["ubuntu","debian"] =>
        {"default" => ["git-core"]}
  )

packages.each do |dev_pkg|
  package dev_pkg
end

git "/opt/statsd" do
    repository "https://github.com/etsy/statsd.git"
    action :export
    user "vagrant"
    group "vagrant"
end
