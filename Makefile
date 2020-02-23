#
PKG = auto_ovpn_profiles
PY  = python3
PIP = pip3

#$(eval WHL=$(shell find dist/ -name "auto_ovpn_profiles*" -print0 | xargs -r -0 ls -1 -t | head -1) )
#@echo "$(WHL)"

build :
	@echo "Building..."
	$(PY) setup.py bdist_wheel

install-dev :
	@echo -n "Installing in developer mode "
	$(PIP) install --editable .

uninstall :
	@echo "Uninstalling..."
	$(PIP) uninstall -y $(PKG)

clean :
	@echo "Cleaning..."
	rm -rf build/ dist/ *.egg-info/
	find . -type f -path "*.pyc" -delete
	find . -type d -path "*/__pycache__" -delete
