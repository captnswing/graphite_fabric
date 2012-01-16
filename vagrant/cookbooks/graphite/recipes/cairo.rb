packages = value_for_platform(
  ["ubuntu", "debian"] =>
    {"default" => ["pkg-config", "libpixman-1-dev", "libcairo2-dev", "valgrind", "libpng12-dev", "libfreetype6-dev", "libfontconfig1-dev"]},
  ["centos", "redhat", "fedora", "amazon"] =>
    {"default" => ["pkgconfig", "valgrind-devel", "libpng-devel", "freetype-devel", "fontconfig-devel"]}
)

packages.each do |dev_pkg|
  package dev_pkg
end

case node.platform
when "debian", "ubuntu"
  include_recipe "apt"

when "redhat", "centos"
  include_recipe "yum"

  libpixman = "/usr/local/lib/libpixman-1.so.#{node[:graphite][:pixmanversion]}"
  libcairo = "/usr/local/lib/libcairo.a"

  remote_file "#{node[:python][:srcdir]}/pixman-#{node[:graphite][:pixmanversion]}.tar.gz" do
    source "http://cairographics.org/releases/pixman-#{node[:graphite][:pixmanversion]}.tar.gz"
    action :create_if_missing
    # TODO
    # checksum node[:graphite][:pixmanchecksum]
    mode "0644"
    notifies :run, "bash[install_pixman]", :immediately
  end

  bash "install_pixman" do
    cwd "#{node[:python][:srcdir]}"
    user "root"
    code <<-EOH
      tar zxf pixman-#{node[:graphite][:pixmanversion]}.tar.gz && \
      cd pixman-#{node[:graphite][:pixmanversion]} && \
      ./configure && \
      make install
    EOH
    not_if "test -e #{libpixman}"
    action :nothing
  end

  remote_file "#{node[:python][:srcdir]}/cairo-#{node[:graphite][:cairoversion]}.tar.gz" do
    source "http://cairographics.org/releases/cairo-#{node[:graphite][:cairoversion]}.tar.gz"
    # TODO
    # checksum node[:graphite][:cairochecksum]
    action :create_if_missing
    mode "0644"
    notifies :run, "bash[install_cairo]", :immediately
  end

  bash "install_cairo" do
    cwd "#{node[:python][:srcdir]}"
    user "root"
    code <<-EOH
      tar zxf cairo-#{node[:graphite][:cairoversion]}.tar.gz && \
      cd cairo-#{node[:graphite][:cairoversion]} && \
      ./configure --enable-xlib=no --disable-gobject && \
      make install
    EOH
    not_if "test -e #{libcairo}"
    action :nothing
  end

end
