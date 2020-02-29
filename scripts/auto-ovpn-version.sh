#!/usr/bin/env bash

PY="python3"

echo "Checking Location and __version__ from installed package"
$PY -c "import auto_ovpn; print(auto_ovpn.__file__); print(auto_ovpn.__version__)"

echo "Checking version returned from CLI"
auto-ovpn --version
