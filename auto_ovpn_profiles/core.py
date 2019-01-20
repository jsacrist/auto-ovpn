#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import yaml


#%% "Global" variables
REQUIRED_VARS = ['VPN_NAME', 'SERVER_ALIASES', 'NET_ADDRESS', 'NET_MASK', 'SERVER_ADDRESS',
                 'DNS_ADDRESS', 'KEY_DIR', 'OUTPUT_DIR']

DEFAULT_VALUES = dict(CLIENT_LIST=None,
                      SERVER_PROTO='tcp',
                      SERVER_PORT_OUT=1194,
                      SERVER_PORT_IN=1194,
                      IFACE='eth0',
                      CIPHER='AES-256-CBC',
                      CONFIG_PATH='/etc/openvpn',
                      SLEEP_TIME=10)


#%% Misc. Functions
def parse_options_from_yaml(yaml_file):
    with open(yaml_file, 'r') as myfile:
        cfg = yaml.load(myfile.read())

    # Validate that the required variables were provided
    for x in REQUIRED_VARS:
        assert x in cfg, f"The provided YAML file does not contain the required value for[{x}]"

    # Use default values for the variables that no value was provided, if one was provided use that instead.
    for x in DEFAULT_VALUES:
        if x not in cfg:
            cfg[x] = DEFAULT_VALUES[x]

    # Add config file's dir name:
    cfg['DIR_NAME'] = os.path.dirname(os.path.abspath(yaml_file))
    return cfg


def parse_client_yaml_file(yaml_file, dir_name):
    if os.path.exists(yaml_file):
        found_file = yaml_file
    elif os.path.exists(f"{dir_name}/{yaml_file}"):
        found_file = f"{dir_name}/{yaml_file}"
    else:
        raise Exception(f"The specified client file [{yaml_file}] was not found")

    with open(found_file, 'r') as myfile:
        clients = yaml.load(myfile.read())
    return clients


def verify_or_make_dir(some_dir):
    if not os.path.exists(some_dir):
        os.makedirs(some_dir)


#%% Template-filling functions
def fill_server_values(key_dir, server_address, server_port_in, config_path="/etc/openvpn",
                       server_proto="tcp", server_mask="255.255.255.0", cipher="AES-256-CBC", ):

    # Open the files containing keys, certificates, etc.
    with open(f"{key_dir}/ca.crt", 'r') as myfile:
        contents_ca_crt = myfile.read()

    with open(f"{key_dir}/server.crt", 'r') as myfile:
        contents_server_crt = myfile.read()

    with open(f"{key_dir}/server.key", 'r') as myfile:
        contents_server_key = myfile.read()

    with open(f"{key_dir}/dh2048.pem", 'r') as myfile:
        contents_dh2048 = myfile.read()

    with open(f"{key_dir}/ta.key", 'r') as myfile:
        contents_ta_key = myfile.read()

    # Fill-in the 'template' with the contents of keys, certificates, etc...
    server_file_contents = \
        f"# {server_address} will be a new VPN, must not conflict with existing nets\n" + \
        f"server {server_address} {server_mask}\n" + \
        f"cipher {cipher}\n" + \
        f"proto {server_proto}\n" + \
        f"port {server_port_in}\n" + \
        "dev tun\n" + \
        "mute 10\n" + \
        f"ifconfig-pool-persist {config_path}/ipp.txt 0\n\n" + \
        "persist-key\n" + \
        "persist-tun\n" + \
        "keepalive 10 60\n" + \
        "topology subnet\n" + \
        "comp-lzo adaptive\n" + \
        "client-to-client\n" + \
        "script-security 2\n" + \
        "daemon\n" + \
        "verb 5\n\n" + \
        f"<ca>\n{contents_ca_crt}</ca>\n\n" + \
        f"<cert>\n{contents_server_crt}</cert>\n\n" + \
        f"<key>\n{contents_server_key}</key>\n\n" + \
        f"<dh>\n{contents_dh2048}</dh>\n\n" + \
        "key-direction 0\n" + \
        f"<tls-auth>\n{contents_ta_key}</tls-auth>\n\n"

    return server_file_contents


def fill_firewall_values(server_network, server_port_in, server_iface, server_proto="tcp"):
    firewall_file_contents = \
        "################################################################################\n" +\
        "## FIREWALL START\n" +\
        "# NOTE: The following iptables lines should be placed either:\n" +\
        "#   a) In the startup script of a dd-wrt router.\n" +\
        "# Or\n" +\
        "#   b) in the /etc/rc.local file of a Debian-based distro.\n" +\
        "################################################################################\n#\n" +\
        "iptables -A OUTPUT -o tun+ -j ACCEPT\n\n" +\
        f"# Accept data coming from {server_proto} port {server_port_in}\n" +\
        f"iptables --insert INPUT 1 --protocol {server_proto} --dport {server_port_in} --jump ACCEPT\n\n" +\
        "# Re-route traffic from VPN clients to the internet\n" +\
        f"iptables -I FORWARD 1 --source {server_network}/24 -j ACCEPT\n" +\
        f"iptables -t nat -A POSTROUTING -s {server_network}/24 -o {server_iface} -j MASQUERADE\n\n" +\
        "## FIREWALL END\n" +\
        "################################################################################\n"
    return firewall_file_contents


def fill_base_client_values(key_dir, client_name, server_port_out, server_aliases,
                            server_proto="tcp", cipher="AES-256-CBC"):
    """
    """

    # Open the files containing keys, certificates, etc.
    with open(f"{key_dir}/ca.crt", 'r') as myfile:
        contents_ca_crt = myfile.read()

    with open(f"{key_dir}/{client_name}.crt", 'r') as myfile:
        contents_client_crt = myfile.read()

    with open(f"{key_dir}/{client_name}.key", 'r') as myfile:
        contents_client_key = myfile.read()

    with open(f"{key_dir}/ta.key", 'r') as myfile:
        contents_ta_key = myfile.read()

    aliases_str = f"remote {server_aliases}"
    if isinstance(server_aliases, list) or isinstance(server_aliases, tuple):
        aliases_str = '\n'.join([f"remote {x}" for x in server_aliases])

    client_file_contents = \
        f"{aliases_str}\n" +\
        "client\n" +\
        f"cipher {cipher}\n" + \
        f"proto {server_proto}\n" + \
        f"port {server_port_out}\n" + \
        "dev tun\n" + \
        "float\n" + \
        "verb 5\n" + \
        "comp-lzo\n" + \
        "remote-cert-tls server\n" + \
        "auth-nocache\n\n" + \
        f"<ca>\n{contents_ca_crt}</ca>\n\n" + \
        f"<cert>\n{contents_client_crt}</cert>\n\n" + \
        f"<key>\n{contents_client_key}</key>\n\n" + \
        "key-direction 1\n" + \
        f"<tls-auth>\n{contents_ta_key}</tls-auth>\n\n"

    return client_file_contents


def fill_client_values(dns_address, key_dir, client_name, server_port_out, server_aliases,
                       server_proto="tcp", cipher="AES-256-CBC"):
    """

    Args:
        dns_address:
        key_dir:
        client_name:
        server_port_out:
        server_aliases:
        server_proto:
        cipher:

    Returns: A tuple with four distinct strings corresponding to client profles: linux, linux-redirect,
             windows, windows-redirect.

    """
    # fill out the variables for a 'base' client.
    client_std = fill_base_client_values(key_dir, client_name, server_port_out, server_aliases,
                                         server_proto, cipher)

    # Define some strings needed for windows and linux profiles
    redir_string = "redirect-gateway def1 bypass-dhcp\n"
    resolv_file = "/etc/openvpn/update-resolv-conf"
    resolv_line = f"{resolv_file} foreign_option_1='dhcp-option DNS {dns_address}'"
    dns_line = f"dhcp-option DNS {dns_address}\n"

    file_header = f"# Client configuration for [{client_name}]\n"

    # Put together the strings for linux profiles
    client_linux = file_header + "# LINUX profile\n" + client_std
    client_linux_redir = (file_header + "# LINUX profile (redirect)\n" + client_std +
                          redir_string +
                          "script-security 2\n" +
                          f"up \"{resolv_line}\"\n" +
                          f"down \"{resolv_line}\"\n" +
                          dns_line)

    # Put together the strings for windows profiles
    client_windows = file_header + "# WINDOWS/ANDROID profile\n" + client_std
    client_windows_redir = (file_header + "# WINDOWS/ANDROID profile (redirect)\n" + client_std +
                            redir_string +
                            "block-outside-dns\n" +
                            dns_line)

    return client_linux, client_linux_redir, client_windows, client_windows_redir


#%% File-writing functions
def write_server_config(output_dir, key_dir, server_address, server_port_in, config_path="/etc/openvpn",
                        server_proto="tcp", server_mask="255.255.255.0", cipher="AES-256-CBC",):
    # TODO: should server_mask be called net_mask?
    """
    """
    # Read the files found in key_dir and create a string variable with the config. file contents
    config_file_contents = fill_server_values(key_dir, server_address, server_port_in,
                                              config_path, server_proto, server_mask, cipher)

    # Write config to file
    verify_or_make_dir(output_dir)
    with open(f"{output_dir}/server.conf", "w") as my_file:
        my_file.write(config_file_contents)


def _get_ip_prefix(server_network, net_mask):
    ip_prefix = ''.join([f"{x}." for (x, y) in zip(server_network.split('.'), net_mask.split('.')) if y != "0"])
    num_octets = len(ip_prefix.split('.'))
    ip_prefix = ip_prefix if num_octets == 4 else f"{ip_prefix}0."
    return ip_prefix


def _log_clients(vpn_name, message, client_list):
    print(f"[{vpn_name}] {message}:")
    print(f'\t{", ".join(client_list)}\n')


def write_server_ipp_file(client_file, dir_name, output_dir, key_dir, vpn_name, server_network, net_mask):
    if client_file is None:
        print(f"No client-file provided for {vpn_name}, won't write ipp.txt...")
        return

    client_ip_dict = parse_client_yaml_file(client_file, dir_name)
    clients_existing = get_all_clients_by_keyfiles(key_dir)
    clients_inner_join = {x: client_ip_dict[x] for x in client_ip_dict if x in clients_existing}

    clients_existing_but_no_addr = [x for x in clients_existing if x not in client_ip_dict]
    clients_addr_but_not_existing = {x: client_ip_dict[x] for x in client_ip_dict if x not in clients_existing}

    ip_prefix = _get_ip_prefix(server_network, net_mask)
    static_ips = f"## ipp.txt for {vpn_name} ({server_network})\n## certificate_client_name,ip_address\n"

    for a_client in clients_inner_join:
        ip_ending = clients_inner_join[a_client]
        static_ips += f"{a_client},{ip_prefix}{ip_ending}\n"

    with open(f"{output_dir}/ipp.txt", "w") as my_file:
        my_file.write(static_ips)

    msg_written = "The following clients had their profiles written:"
    _log_clients(vpn_name, msg_written, clients_inner_join)

    msg_not_in_client_file = ("The following clients have a key-pair, but were " +
                              f"not written to ipp.txt because they were not found in {client_file}:")
    _log_clients(vpn_name, msg_not_in_client_file, clients_existing_but_no_addr)

    msg_no_key = (f"The following clients were found in {client_file}, but had no " +
                  f"key-pair and were not written")
    _log_clients(vpn_name, msg_no_key, clients_addr_but_not_existing)


def write_firewall_config(output_dir, server_network, server_port_in, server_iface, server_proto="tcp"):
    """
    """
    # Fill out the specific values for the firewall.
    firewall_contents = fill_firewall_values(server_network, server_port_in, server_iface, server_proto)

    # Write config to file
    verify_or_make_dir(output_dir)

    with open(f"{output_dir}/firewall.sh", "w") as my_file:
        my_file.write(firewall_contents)


def write_client_profiles(output_dir, vpn_name, dns_address, key_dir, client_name, server_port_out, server_aliases,
                          server_proto="tcp", cipher="AES-256-CBC"):

    # Fill-in the values for this client
    client_l, client_lr, client_w, client_wr = fill_client_values(dns_address, key_dir, client_name, server_port_out,
                                                                  server_aliases, server_proto, cipher)

    dir_linux = f"{output_dir}/clients/{client_name}/linux/"
    dir_windows = f"{output_dir}/clients/{client_name}/windows/"
    verify_or_make_dir(dir_linux)
    verify_or_make_dir(dir_windows)

    # Save the linux profiles
    with open(f"{dir_linux}/{vpn_name}.conf", "w", newline='\n') as myfile:
        myfile.write(client_l)

    with open(f"{dir_linux}/{vpn_name}-redirect.conf", "w", newline='\n') as myfile:
        myfile.write(client_lr)

    # Save the windows profiles
    with open(f"{dir_windows}/{vpn_name}.ovpn", "w", newline='\r\n') as myfile:
        myfile.write(client_w)

    with open(f"{dir_windows}/{vpn_name}-redirect.ovpn", "w", newline='\r\n') as myfile:
        myfile.write(client_wr)


def get_all_clients_by_keyfiles(key_dir):
    ignore_files = ['ta.key', 'ca.key', 'server.key']
    key_files = glob.glob(f"{key_dir}/*.key")
    existing_clients = [y.split('.')[0] for y in [os.path.basename(x) for x in key_files] if y not in ignore_files]
    return existing_clients


def write_all_client_profiles(output_dir, vpn_name, dns_address, key_dir, server_port_out, server_aliases,
                              server_proto="tcp", cipher="AES-256-CBC"):
    existing_clients = get_all_clients_by_keyfiles(key_dir)
    for client_name in existing_clients:
        write_client_profiles(output_dir, vpn_name, dns_address, key_dir, client_name,
                              server_port_out, server_aliases, server_proto, cipher)


def write_complete_config(cfg):
    write_server_config(output_dir=cfg['OUTPUT_DIR'],
                        key_dir=cfg['KEY_DIR'],
                        server_address=cfg['SERVER_ADDRESS'],
                        server_port_in=cfg['SERVER_PORT_IN'],
                        config_path=cfg['CONFIG_PATH'],
                        server_proto=cfg['SERVER_PROTO'],
                        server_mask=cfg['NET_MASK'],
                        cipher=cfg['CIPHER'])

    write_server_ipp_file(client_file=cfg['CLIENT_LIST'],
                          dir_name=cfg['DIR_NAME'],
                          output_dir=cfg['OUTPUT_DIR'],
                          key_dir=cfg['KEY_DIR'],
                          vpn_name=cfg['VPN_NAME'],
                          server_network=cfg['NET_ADDRESS'],
                          net_mask=cfg['NET_MASK'])

    write_firewall_config(output_dir=cfg['OUTPUT_DIR'],
                          server_network=cfg['NET_ADDRESS'],
                          server_port_in=cfg['SERVER_PORT_IN'],
                          server_iface=cfg['IFACE'],
                          server_proto=cfg['SERVER_PROTO'])

    write_all_client_profiles(output_dir=cfg['OUTPUT_DIR'],
                              vpn_name=cfg['VPN_NAME'],
                              dns_address=cfg['DNS_ADDRESS'],
                              key_dir=cfg['KEY_DIR'],
                              server_port_out=cfg['SERVER_PORT_OUT'],
                              server_aliases=cfg['SERVER_ALIASES'],
                              server_proto=cfg['SERVER_PROTO'],
                              cipher=cfg['CIPHER'])
