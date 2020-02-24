# auto-ovpn
`auto-ovpn` is a Python package to automatically generate OpenVPN profiles based on an existing keys.
These keys are issued by your own Certificate Authority (CA) or a third-party.

## Installation

### Cloning the repository

Installing from source can be done by running the following lines: 
 
```bash
git clone https://github.com/jsacrist/auto-ovpn.git
cd auto-ovpn
make
make install
```

Uninstalling can be done via:

```bash
cd auto-ovpn
make uninstall
```

## Usage

running `auto-ovpn` with no arguments will show the required and optional arguments. 

### Creating an example config file:

In order to create the `*.ovpn` files corresponding to keys, you must first create a configuration Yaml file.
The following line shows an example of a configuration yaml file:  

```bash
auto-ovpn -e
```

    usage: auto-ovpn [-h] [-e] [-F FILE] [-o OUTPUT_DIR] [-v]
    
    optional arguments:
      -h, --help            show this help message and exit
      -e, --example         Print out an example of a configuration yaml file and
                            exit.
      -F FILE, --file FILE  Path to a yaml file containing the configuration
                            values.
      -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            (optional) Path to an output directory where all the
                            vpn profiles should be placed.
      -v, --version         Print the version of this package and exit.

You can use this output to start customizing your own file

```bash
auto-ovpn -e > my_vpn_config_1.yml
# <Edit your configuration>
```

Normally, you would want one config file for each VPN server you're maintaining.
If you you have 3 config files, then you can create the `*.ovpn` profiles for all 3 servers like so:

```bash
auto-ovpn -F vpn1.yml -F vpn2.yml -F vpn3.yml -o ~/vpns/all_configs/
```
