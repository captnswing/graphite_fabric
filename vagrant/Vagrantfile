# -*- mode: ruby -*-

Vagrant::Config.run do |config|
  config.vm.box = "lucid32"
  # config.vm.box_url = "http://files.vagrantup.com/lucid32.box"
  # config.vm.box = "lucid64"
  # config.vm.box_url = "http://files.vagrantup.com/lucid64.box"

  # Boot with a GUI so you can see the screen. (Default is headless)
  config.vm.boot_mode = :gui

  # Assign this VM to a host only network IP, allowing you to access it
  # via the IP.
  config.vm.network "33.33.33.10"

  # http://superuser.com/questions/342473/vagrant-ssh-fails-with-virtualbox
  # https://github.com/mitchellh/vagrant/issues/455
  config.ssh.max_tries = 150

  # Forward a port from the guest to the host, which allows for outside
  # computers to access the VM, whereas host only networking does not.
  config.vm.forward_port "gunicorn", 8000, 8787
  config.vm.forward_port "graphite-dev", 8080, 8888

  # Share an additional folder to the guest VM. The first argument is
  # an identifier, the second is the path on the guest to mount the
  # folder, and the third is the path on the host to the actual folder.
  # config.vm.share_folder "v-data", "/vagrant_data", "../data"

  # Boost CPU & RAM slightly and give it a reasonable name
  config.vm.customize do |vm|
    vm.memory_size = 512
    vm.cpu_count = 2
    vm.name = "graphite"
  end

  # Enable provisioning with chef solo, specifying a cookbooks path (relative
  # to this Vagrantfile), and adding some recipes and/or roles.
  config.vm.provision :chef_solo do |chef|
    # TODO: add site-cookbooks
    chef.cookbooks_path = "cookbooks"
    chef.add_recipe "graphite"

    #chef.log_level = :debug
    #chef.add_role "web"

    # TODO: figure out proxy
    # chef.http_proxy = "http://proxy.svt.se:8080"
    # chef.https_proxy = "https://proxy.svt.se:8080"

    # override attributes/default.rb
    chef.json.merge!(
        {
            # override node cookbook attributes
            :nodejs => {:version => "0.6.6"},
            # override python cookbook attributes
            :python => {:install_method => 'source',
                        :version => '2.7.2',
                        :checksum => '5057eb067eb5b5a6040dbd0e889e06550bde9ec041dadaa855ee9490034cbdab'
            }
        }
    )
  end

end
