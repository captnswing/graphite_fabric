libpixman = "/usr/local/lib/libpixman-1.so.#{node[:pixman][:version]}"
libcairo = "/usr/local/lib/libcairo.a"

remote_file "#{node[:srcdir]}/pixman-#{node[:pixman][:version]}.tar.gz" do
    source "http://cairographics.org/releases/pixman-#{node[:pixman][:version]}.tar.gz"
    action :create_if_missing
    mode "0644"
end

bash "install pixman from source" do
	cwd "#{node[:srcdir]}"
	user "root"
	code <<-EOH
		tar zxf pixman-#{node[:pixman][:version]}.tar.gz && \
		cd pixman-#{node[:pixman][:version]} && \
		./configure && \
		make && \
		make install
	EOH
	not_if "test -e #{libpixman}"
end

packages = value_for_platform(
    ["centos","redhat","fedora","amazon"] =>
        {"default" => ["pkgconfig", "valgrind-devel", "libpng-devel", "freetype-devel", "fontconfig-devel"]},
    ["ubuntu","debian"] =>
        {"default" => ["pkg-config", "valgrind", "libpng12-dev", "libfreetype6-dev", "libfontconfig1-dev"]}
  )

packages.each do |dev_pkg|
  package dev_pkg
end

remote_file "#{node[:srcdir]}/cairo-#{node[:cairo][:version]}.tar.gz" do
    source "http://cairographics.org/releases/cairo-#{node[:cairo][:version]}.tar.gz"
    action :create_if_missing
    mode "0644"
end

bash "install cairo from source" do
	cwd "#{node[:srcdir]}"
	user "root"
	code <<-EOH
		tar zxf cairo-#{node[:cairo][:version]}.tar.gz && \
		cd cairo-#{node[:cairo][:version]} && \
		./configure --enable-xlib=no --disable-gobject && \
		make && \
		make install
	EOH
	not_if "test -e #{libcairo}"
end
