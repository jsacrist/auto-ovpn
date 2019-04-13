#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import sys
import os
import glob
from distutils.dir_util import copy_tree
from auto_ovpn_profiles import parse_options_from_yaml, write_complete_config, get_all_clients_by_keyfiles


def parse_cl_args(arguments):
    a_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)

    a_parser.add_argument(
        "-e", "--example",
        action='store_true',
        help="Print out an example of a configuration yaml file and exit."
    )

    a_parser.add_argument(
        "-F", "--file",
        type=str,
        action='append',
        help="Path to a yaml file containing the configuration values."
    )

    a_parser.add_argument(
        "-o", "--output-dir",
        type=str,
        help="(optional) Path to an output directory where all the vpn profiles should be placed."
    )

    some_args = a_parser.parse_args(arguments)
    return some_args, a_parser


if __name__ == "__main__":
    args, parser = parse_cl_args(sys.argv[1:])

    # If the `example` flag was passed, print out the example yaml and quit
    if args.example:
        pkg_dir = os.path.dirname(__file__)
        with open("{}/vpn_example.yml".format(pkg_dir), 'r') as myfile:
            example_yaml = myfile.read()
            print(example_yaml)
        exit()

    # If no files were given, display the help text and quit
    if args.file is None:
        parser.print_help()
        exit()

    # If we make it to this point, at least a file was given.
    client_dirs = []
    for cfg in [parse_options_from_yaml(x) for x in set(args.file)]:
        write_complete_config(cfg)  # Process each config file
        existing_clients = get_all_clients_by_keyfiles(cfg['KEY_DIR'])
        client_dirs.append(glob.glob("{}/clients/".format(cfg['OUTPUT_DIR']))[0])

    if args.output_dir is not None:
        for a_dir in client_dirs:
            copy_tree(a_dir, args.output_dir)
