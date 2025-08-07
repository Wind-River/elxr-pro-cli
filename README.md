<h1>
  <a href="https://elxr.pro" target="_blank">
    <img src="https://elxr.org/images/eLxr_logo-06-new.png" width="33"/>
  </a>
  <br>
  eLxr Pro Client
</h1>

# Convenient and Consistent Interface for your eLxr Pro Systems
[![Latest Upstream Version]](https://gitlab.com/elxrpro/subscription_services/elxr-pro)
<br/>

The eLxr Pro Client (`elxr-pro`) is the official tool to enable eLxr Pro offerings on your system.


Try it out by running `elxr-pro help`!

Or [check out the docs](https://elxr.pro).

## Setup development environment

1. Clone the repository and start debian docker environment:

   ```sh
   git clone https://gitlab.com/elxrpro/subscription_services/elxr-pro.git
   export DISTRO=bookworm
   docker run -ti --privileged -v elxr-pro:/elxr-pro debian:$DISTRO /bin/bash
   apt update;apt install vim git git-buildpackage -y
   ```

1. Get the dependencies and build the deb package locally by manual:
   Given we have the pipeline build, it's not necessary to build deb package locally.
   ```sh
   cd /elxr-pro
   git config --global --add safe.directory /elxr-pro
   apt build-dep .
   dpkg-buildpackage
   ```
   You can find the deb package has been generated as elxr-pro*.deb at the parent path.

1. As the unit tests have been added in the debian/rule, the unit tests will be executed during the building process of the deb package. If you want to execute the unit tests by manual firstly, you can execute the following command:
   ```sh
   cd /elxr-pro
   pytest
   ```
or
   ```sh
   cd /elxr-pro
   python3 -m pytest
   ```
## Sub-commands for elxr-pro client

You can get the followingdetailed usage summary for each sub-commands:

   ```sh
   sudo elxr-pro -h

   Quick start commands:

     join             attach this machine to an eLxr Pro subscription

   Other commands:

     config           manage eLxr Pro configuration on this machine
     leave            remove this machine from an eLxr Pro subscription
     test             validate the connection to the API server
   ```

Test sub-command is used to validate if the connection to the API Server is reachable.

   ```sh
   sudo elxr-pro test <token>
   ```
or
   ```sh
   sudo elxr-pro test
   ```

For join command, you can get a token from the subscription dashboard page.
Then execute the join command with the token to activate the pro entitlements.

   ```sh
   sudo elxr-pro join <token>
   ```

Use the --pro-only option to just keep pro resources:
   ```sh
   sudo elxr-pro join --pro-only <token>
   ```

You can return back elxr resource with leave sub command:

   ```sh
   sudo elxr-pro leave
   ```
This will restore the elxr apt repository resource.

The config subcommand is to support the apt proxy feature:
If there is an apt proxy candidate, it can be enable with the config command:

   ```sh
   sudo elxr-pro config show
   sudo elxr-pro config set ea_apt_http_proxy=${proxy_url}
   sudo elxr-pro config set ea_apt_https_proxy=${proxy_url}
   ```
or
   ```sh
   sudo elxr-pro config set global_apt_http_proxy=${proxy_url}
   sudo elxr-pro config set global_apt_https_proxy=${proxy_url}
   ```
The apt proxy setting can be shown in the file
/etc/apt/apt.conf.d/90elxr-advantage-aptproxy

## Setup configuration for the verification in the development environment

1. install the elxr-pro deb package:

   ```sh
   dpkg -i elxr-pro-*.deb
   which elxr-pro
   ```

1. Edit and customize the configuration file:

   ```sh
   vim /etc/elxr-advantage/eaclient.conf
   ```

Set the contract_url and log_level to the appropriate values for the development environment. The contract_url should point to the API Server(https://gitlab.com/elxrpro/subscription_services/api-server) where your implementation is hosted.

1. Verify the connection to API Server:

   ```sh
   elxr-pro test <token>
   ```

1. Execute the join/leave sub-commands to activate/deactivate elxr-pro mirros:

   ```sh
   elxr-pro join <token>
   elxr-pro leave
   ```

## Common issues and solutions

### end user quick start

1. Download the elxr-pro deb package from Gallery(Please refer to https://confluence.wrs.com/display/OS2/ELxr+Pro+Gallery+Release+Process)

1. Install the deb pacakge in the target system

   ```sh
   sudo dpkg -i elxr-pro*.deb
   ```

### developer quick start

Build the elxr-pro deb pacakge or download it from the elxrpro gitlab artifacts page, then install it with the following command:

   ```sh
   sudo dpkg -i elxr-pro*.deb
   ```
The full python libaries will be imported at /usr/lib/python3/dist-packages/eaclient, you can combine the '--debug' option fur debugging.

Please refer to https://gitlab.com/groups/elxrpro/-/issues and new a page to track the issue.


## Project License

The license for this project is the Apache 2.0 license. Text of the Apache 2.0
license and other applicable license notices can be found in the LICENSE file
in the top level directory. Each source file should include a license notice
that designates the licensing terms for the respective file.


## Legal Notices

All product names, logos, and brands are property of their respective owners. All company,
product and service names used in this software are for identification purposes only. Wind
River and VxWorks are a registered trademarks of Wind River Systems. Amazon and AWS
are registered trademarks of the Amazon Corporation.

Disclaimer of Warranty / No Support: Wind River does not provide support and
maintenance services for this software, under Wind River’s standard Software Support and
Maintenance Agreement or otherwise. Unless required by applicable law, Wind River
provides the software (and each contributor provides its contribution) on an “AS IS” BASIS,
WITHOUT WARRANTIES OF ANY KIND, either express or implied, including, without
limitation, any warranties of TITLE, NONINFRINGEMENT, MERCHANTABILITY, or FITNESS
FOR A PARTICULAR PURPOSE. You are solely responsible for determining the
appropriateness of using or redistributing the software and assume ay risks associated
with your exercise of permissions under the license.