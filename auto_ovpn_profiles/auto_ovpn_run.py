#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import glob
from distutils.dir_util import copy_tree
from auto_ovpn_profiles import parse_options_from_yaml, write_complete_config, get_all_clients_by_keyfiles

#%%
output_dir = "C:/Users/jsacr/Desktop/vpns/all_clients"
cfg_files = [
    "../personal_networks_cfg/vpnmx.yml",
    "../personal_networks_cfg/vpnca.yml",
    ]

#%%
client_dirs = []
for cfg_file in cfg_files:
    cfg = parse_options_from_yaml(cfg_file)
    write_complete_config(cfg)
    existing_clients = get_all_clients_by_keyfiles(cfg['KEY_DIR'])
    client_dirs.append(glob.glob(f"{cfg['OUTPUT_DIR']}/clients/")[0])

#%%
for a_dir in client_dirs:
    copy_tree(a_dir, output_dir)
