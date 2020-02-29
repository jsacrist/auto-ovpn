#
PKG = auto_ovpn
PY  = python3
PIP = $(PY) -m pip

build :
	@echo "Building..."
	$(PY) setup.py bdist_wheel

install-dev : build
	@echo "Installing in `developer mode`"
	$(PIP) install --user --editable .

install : build
	@echo -n "Installing "
	@$(eval DIST_WHL=$(shell find dist/ -name "$(PKG)*" -print0 | xargs -r -0 ls -1 -t | head -1) )
	@$(eval WHL=$(shell basename $(DIST_WHL)))
	@echo "$(WHL)"
	cd dist && $(PIP) install --user $(WHL)

uninstall :
	@echo "Uninstalling..."
	$(PIP) uninstall -y $(PKG)
	pip3 uninstall -y $(PKG)

clean :
	@echo "Cleaning..."
	rm -rf build/ dist/ *.egg-info/
	find . -type f -path "*.pyc" -delete
	find . -type d -path "*/__pycache__" -delete

version :
	which $(PY)
	$(PY) --version
	$(PIP) --version
