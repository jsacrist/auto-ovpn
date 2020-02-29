import nox
import glob


pkg_name = "auto_ovpn"
# python_versions = ["2.7", "3.5", "3.6", "3.7"]
python_versions = ["3.6", "3.7"]


@nox.session(python=python_versions)
def lint(session):
    session.install("black")
    session.install("flake8")
    for py_file in glob.glob("{}/*.py".format(pkg_name)):
        session.run("black", "-l 100", py_file)
        session.run("flake8", py_file)


@nox.session(python=python_versions)
def installable(session):
    # same as pip install .
    session.install("-r", "install_requires.txt")
    session.install(".")
    session.run(
        "python3",
        "-c",
        "import {} as pkg; print(pkg.__version__); print(pkg.__file__)".format(pkg_name)
    )
    session.run("auto-ovpn")
