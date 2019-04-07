# -*- coding: utf-8 -*-
import os
import glob
import yaml
from ._version import get_versions


#%% "Global" variables
REQUIRED_VARS = ['VPN_NAME', 'SERVER_ALIASES', 'NET_ADDRESS', 'NET_MASK',
                 'DNS_ADDRESS', 'KEY_DIR', 'OUTPUT_DIR']

DEFAULT_VALUES = dict(
    CLIENT_LIST=None,
    SERVER_PROTO='tcp',
    SERVER_PORT_OUT=1194,
    SERVER_PORT_IN=1194,
    CIPHER='AES-256-CBC',
    CONFIG_PATH='/etc/openvpn',
    SLEEP_TIME=10
)


#%% "Internal" functions
def _get_ip_prefix(server_network, net_mask):
    ip_prefix = ''.join(["{}.".format(x) for (x, y) in zip(server_network.split('.'), net_mask.split('.')) if y != "0"])
    num_octets = len(ip_prefix.split('.'))
    ip_prefix = ip_prefix if num_octets == 4 else "{}0.".format(ip_prefix)
    return ip_prefix


def _log_clients(vpn_name, message, client_list, num_tabs=2):
    print("[{}] {}:".format(vpn_name, message))
    for line in _list_to_multiline_str(sorted(client_list), 100).split('\n'):
        print("\t" * num_tabs + line)


def _list_to_multiline_str(a_list, num_char=80):
    str_out = ""
    for idx, element in enumerate(a_list):

        if idx > 0:
            str_out = str_out + ","

        if len(str_out.split('\n')[-1]) + len(element) > num_char:
            str_out = str_out + "\n"
        elif idx > 0:
            str_out = str_out + " "

        str_out = str_out + element
    return str_out


def _verify_or_make_dir(some_dir):
    if not os.path.exists(some_dir):
        os.makedirs(some_dir)


#%% Parser Functions
def parse_options_from_yaml(yaml_file):
    with open(yaml_file, 'r') as myfile:
        cfg = yaml.load(myfile.read())

    # Validate that the required variables were provided
    for x in REQUIRED_VARS:
        assert x in cfg, "The provided YAML file does not contain the required value for[{}]".format(x)

    # TODO: Ensure the provided values in the YAML file are valid

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
    elif os.path.exists("{}/{}".format(dir_name, yaml_file)):
        found_file = "{}/{}".format(dir_name, yaml_file)
    else:
        raise Exception("The specified client file [{}] was not found".format(yaml_file))

    with open(found_file, 'r') as myfile:
        clients = yaml.load(myfile.read())
    return clients


#%% Template-filling functions
def fill_server_values(key_dir, server_network, server_port_in, config_path,
                       server_proto, server_mask, cipher):

    # Open the files containing keys, certificates, etc.
    with open("{}/ca.crt".format(key_dir), 'r') as myfile:
        contents_ca_crt = myfile.read()

    with open("{}/server.crt".format(key_dir), 'r') as myfile:
        contents_server_crt = myfile.read()

    with open("{}/server.key".format(key_dir), 'r') as myfile:
        contents_server_key = myfile.read()

    with open("{}/dh2048.pem".format(key_dir), 'r') as myfile:
        contents_dh2048 = myfile.read()

    with open("{}/ta.key".format(key_dir), 'r') as myfile:
        contents_ta_key = myfile.read()

    # Fill-in the 'template' with the contents of keys, certificates, etc...
    server_file_contents = (
            "# {} will be a new VPN, must not conflict with existing nets\n".format(server_network) +
            "server {} {}\n".format(server_network, server_mask) +
            "cipher {}\n".format(cipher) +
            "proto {}\n".format(server_proto) +
            "port {}\n".format(server_port_in) +
            "dev tun\n" +
            "mute 10\n" +
            "ifconfig-pool-persist {}/ipp.txt 0\n\n".format(config_path) +
            "persist-key\n" +
            "persist-tun\n" +
            "keepalive 10 60\n" +
            "topology subnet\n" +
            "comp-lzo adaptive\n" +
            "client-to-client\n" +
            "script-security 2\n" +
            "daemon\n" +
            "verb 5\n\n" +
            "<ca>\n{}</ca>\n\n".format(contents_ca_crt) +
            "<cert>\n{}</cert>\n\n".format(contents_server_crt) +
            "<key>\n{}</key>\n\n".format(contents_server_key) +
            "<dh>\n{}</dh>\n\n".format(contents_dh2048) +
            "key-direction 0\n" +
            "<tls-auth>\n{}</tls-auth>\n\n".format(contents_ta_key)
    )

    return server_file_contents


def fill_firewall_values(server_network, server_port_in, server_proto):
    firewall_file_contents = (
        "################################################################################\n" +
        "## FIREWALL START\n" +
        "# NOTE: The following iptables lines should be placed either:\n" +
        "#   a) In the startup script of a dd-wrt router.\n" +
        "# Or\n" +
        "#   b) in the /etc/rc.local file of a Debian-based distro.\n" +
        "################################################################################\n#\n" +
        "iptables -A OUTPUT -o tun+ -j ACCEPT\n\n" +
        "# Accept data coming from {} port {}\n".format(server_proto, server_port_in) +
        "iptables --insert INPUT 1 --protocol {} --dport {} --jump ACCEPT\n\n".format(server_proto, server_port_in) +
        "# Re-route traffic from VPN clients to the internet\n" +
        "iptables -I FORWARD 1 --source {}/24 -j ACCEPT\n".format(server_network) +
        "iptables -t nat -A POSTROUTING -s {}/24 ! -d {}/24 -j MASQUERADE\n\n".format(server_network, server_network) +
        "## FIREWALL END\n" +
        "################################################################################\n"
    )
    return firewall_file_contents


def fill_base_client_values(key_dir, client_name, server_port_out, server_aliases,
                            server_proto, cipher):
    """
    """

    # Open the files containing keys, certificates, etc.
    with open("{}/ca.crt".format(key_dir), 'r') as myfile:
        contents_ca_crt = myfile.read()

    with open("{}/{}.crt".format(key_dir, client_name), 'r') as myfile:
        contents_client_crt = myfile.read()

    with open("{}/{}.key".format(key_dir, client_name), 'r') as myfile:
        contents_client_key = myfile.read()

    with open("{}/ta.key".format(key_dir), 'r') as myfile:
        contents_ta_key = myfile.read()

    aliases_str = "remote {}".format(server_aliases)
    if isinstance(server_aliases, list) or isinstance(server_aliases, tuple):
        aliases_str = '\n'.join(["remote {}".format(x) for x in server_aliases])

    client_file_contents = (
            "{}\n".format(aliases_str) +
            "client\n" +
            "cipher {}\n".format(cipher) +
            "proto {}\n".format(server_proto) +
            "port {}\n".format(server_port_out) +
            "dev tun\n" +
            "float\n" +
            "verb 5\n" +
            "comp-lzo\n" +
            "remote-cert-tls server\n" +
            "auth-nocache\n\n" +
            "<ca>\n{}</ca>\n\n".format(contents_ca_crt) +
            "<cert>\n{}</cert>\n\n".format(contents_client_crt) +
            "<key>\n{}</key>\n\n".format(contents_client_key) +
            "key-direction 1\n" +
            "<tls-auth>\n{}</tls-auth>\n\n".format(contents_ta_key)
        )

    return client_file_contents


def fill_client_values(dns_address, key_dir, client_name, server_port_out,
                       server_aliases, server_proto, cipher):
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
    resolv_line = "{} foreign_option_1='dhcp-option DNS {}'".format(resolv_file, dns_address)
    dns_line = "dhcp-option DNS {}\n".format(dns_address)

    file_header = "# Client configuration for [{}]\n".format(client_name)

    # Put together the strings for linux profiles
    client_linux = file_header + "# LINUX profile\n" + client_std
    client_linux_redir = (
            file_header + "# LINUX profile (redirect)\n" + client_std +
            redir_string +
            "script-security 2\n" +
            "up \"{}\"\n".format(resolv_line) +
            "down \"{}\"\n".format(resolv_line) +
            dns_line
    )

    # Put together the strings for windows profiles
    client_windows = file_header + "# WINDOWS/ANDROID profile\n" + client_std
    client_windows_redir = (file_header + "# WINDOWS/ANDROID profile (redirect)\n" + client_std +
                            redir_string +
                            "block-outside-dns\n" +
                            dns_line)

    return client_linux, client_linux_redir, client_windows, client_windows_redir


#%% File-writing functions
def write_server_config(vpn_name, output_dir, key_dir, server_network, server_port_in, config_path,
                        server_proto, server_mask, cipher):
    # TODO: should server_mask be called net_mask?
    """
    """
    # Read the files found in key_dir and create a string variable with the config. file contents
    config_file_contents = fill_server_values(key_dir, server_network, server_port_in,
                                              config_path, server_proto, server_mask, cipher)

    # Write config to file
    _verify_or_make_dir(output_dir)
    with open("{}/server.conf".format(output_dir), "w") as my_file:
        my_file.write(config_file_contents)
    print("[{}] OpenVPN configuration file written to: {}/server.conf".format(vpn_name, output_dir))


def write_server_ipp_file(vpn_name, client_file, dir_name, output_dir, key_dir, server_network, net_mask):
    if client_file is None:
        print("[{}] No value for 'CLIENT_LIST' was specified.  Won't write ipp.txt...".format(vpn_name))
        return

    client_ip_dict = parse_client_yaml_file(client_file, dir_name)
    clients_existing = get_all_clients_by_keyfiles(key_dir)
    clients_inner_join = {x: client_ip_dict[x] for x in client_ip_dict if x in clients_existing}

    clients_existing_but_no_addr = [x for x in clients_existing if x not in client_ip_dict]
    clients_addr_but_not_existing = {x: client_ip_dict[x] for x in client_ip_dict if x not in clients_existing}

    ip_prefix = _get_ip_prefix(server_network, net_mask)
    static_ips = "## ipp.txt for {} ({})\n## certificate_client_name,ip_address\n".format(vpn_name, server_network)

    for a_client in clients_inner_join:
        ip_ending = clients_inner_join[a_client]
        static_ips += "{},{}{}\n".format(a_client, ip_prefix, ip_ending)

    with open("{}/ipp.txt".format(output_dir), "w") as my_file:
        my_file.write(static_ips)

    # Log everything that was done
    # if len(clients_inner_join) > 0:
    #     msg_written = "Profiles written"
    #     _log_clients(vpn_name, msg_written, clients_inner_join)

    if len(clients_existing_but_no_addr) > 0:
        # msg_not_in_client_file = ("Profiles written, but no entry added to ipp.txt " +
        #                           "(no matching entry in {})".format(client_file))
        msg_not_in_client_file = ("Profiles NOT added to ipp.txt " +
                                  "(no matching entry in {})".format(client_file))
        _log_clients(vpn_name, msg_not_in_client_file, clients_existing_but_no_addr, 3)

    if len(clients_addr_but_not_existing) > 0:
        msg_no_key = "Profiles NOT written (entries found in {}, but no key-pair found)".format(client_file)
        _log_clients(vpn_name, msg_no_key, clients_addr_but_not_existing, 3)


def write_firewall_config(vpn_name, output_dir, server_network, server_port_in, server_proto):
    """
    """
    # Fill out the specific values for the firewall.
    firewall_contents = fill_firewall_values(server_network, server_port_in, server_proto)

    # Write config to file
    _verify_or_make_dir(output_dir)

    with open("{}/firewall.sh".format(output_dir), "w") as my_file:
        my_file.write(firewall_contents)
    print("[{}] Firewall rules written to: {}/firewall.sh".format(vpn_name, output_dir))


def write_client_profiles(output_dir, vpn_name, dns_address, key_dir, client_name, server_port_out,
                          server_aliases, server_proto, cipher):

    # Fill-in the values for this client
    client_l, client_lr, client_w, client_wr = fill_client_values(dns_address, key_dir, client_name, server_port_out,
                                                                  server_aliases, server_proto, cipher)

    dir_linux = "{}/clients/{}/linux/".format(output_dir, client_name)
    dir_windows = "{}/clients/{}/windows/".format(output_dir, client_name)
    _verify_or_make_dir(dir_linux)
    _verify_or_make_dir(dir_windows)

    # Save the linux profiles
    with open("{}/{}.conf".format(dir_linux, vpn_name), "w", newline='\n') as myfile:
        myfile.write(client_l)

    with open("{}/{}-redirect.conf".format(dir_linux, vpn_name), "w", newline='\n') as myfile:
        myfile.write(client_lr)

    # Save the windows profiles
    with open("{}/{}.ovpn".format(dir_linux, vpn_name), "w", newline='\r\n') as myfile:
        myfile.write(client_w)

    with open("{}/{}-redirect.ovpn".format(dir_linux, vpn_name), "w", newline='\r\n') as myfile:
        myfile.write(client_wr)


def get_all_clients_by_keyfiles(key_dir):
    ignore_files = ['ta.key', 'ca.key', 'server.key']
    key_files = glob.glob("{}/*.key".format(key_dir))
    existing_clients = [y.split('.')[0] for y in [os.path.basename(x) for x in key_files] if y not in ignore_files]
    return existing_clients


def write_all_client_profiles(output_dir, vpn_name, dns_address, key_dir, server_port_out,
                              server_aliases, server_proto, cipher):
    existing_clients = get_all_clients_by_keyfiles(key_dir)
    for client_name in existing_clients:
        write_client_profiles(output_dir, vpn_name, dns_address, key_dir, client_name,
                              server_port_out, server_aliases, server_proto, cipher)
    _log_clients(vpn_name, "Profiles written to {}".format(output_dir), existing_clients)


def write_complete_config(cfg):
    write_server_config(
        vpn_name=cfg['VPN_NAME'],
        output_dir=cfg['OUTPUT_DIR'],
        key_dir=cfg['KEY_DIR'],
        server_network=cfg['NET_ADDRESS'],
        server_port_in=cfg['SERVER_PORT_IN'],
        config_path=cfg['CONFIG_PATH'],
        server_proto=cfg['SERVER_PROTO'],
        server_mask=cfg['NET_MASK'],
        cipher=cfg['CIPHER']
    )

    write_firewall_config(
        vpn_name=cfg['VPN_NAME'],
        output_dir=cfg['OUTPUT_DIR'],
        server_network=cfg['NET_ADDRESS'],
        server_port_in=cfg['SERVER_PORT_IN'],
        server_proto=cfg['SERVER_PROTO']
    )

    write_all_client_profiles(
        output_dir=cfg['OUTPUT_DIR'],
        vpn_name=cfg['VPN_NAME'],
        dns_address=cfg['DNS_ADDRESS'],
        key_dir=cfg['KEY_DIR'],
        server_port_out=cfg['SERVER_PORT_OUT'],
        server_aliases=cfg['SERVER_ALIASES'],
        server_proto=cfg['SERVER_PROTO'],
        cipher=cfg['CIPHER']
    )

    write_server_ipp_file(
        vpn_name=cfg['VPN_NAME'],
        client_file=cfg['CLIENT_LIST'],
        dir_name=cfg['DIR_NAME'],
        output_dir=cfg['OUTPUT_DIR'],
        key_dir=cfg['KEY_DIR'],
        server_network=cfg['NET_ADDRESS'],
        net_mask=cfg['NET_MASK']
    )

    print("")
