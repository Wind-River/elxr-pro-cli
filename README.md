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

## Setup configuration for the verification in the dev env

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
