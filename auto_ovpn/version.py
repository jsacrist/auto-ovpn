import os
import git  # Installed with `pip3 install --user gitpython`
import json


def get_version(save_json=False):
    ver_git = _from_git()
    ret_ver = ver_git

    if save_json:
        _save_json(ver_git)

    ver_json = _from_json()
    if ret_ver["version"] == "unknown":
        ret_ver = ver_json
    return ret_ver


def _save_json(dict_to_save):
    filename = "{}/version.json".format(os.path.dirname(os.path.realpath(__file__)))
    print("Creating version file in {}".format(filename))
    with open(filename, "w") as fp:
        json.dump(dict_to_save, fp)


def _from_json():
    filename = "{}/version.json".format(os.path.dirname(os.path.realpath(__file__)))
    try:
        with open(filename, "r") as fp:
            ver_json = json.load(fp)
    except:
        ver_json = dict(version="unknown", is_dirty="True", hash=None, version_long="unknown")
    return ver_json


def _from_git():
    v_compact = "unknown"
    v_long = "unknown"
    v_hash = None
    try:
        with git.Repo(os.path.realpath(__file__), search_parent_directories=True) as g_repo:
            v_raw = g_repo.git.describe(long=True, dirty=True, broken=True)
            v_compact = g_repo.git.describe(long=False, dirty=False, broken=False)
            v_long = v_raw.replace("-", "+", 1).replace("-", ".", 2)
            v_hash = g_repo.head.object.hexsha
    except (git.exc.InvalidGitRepositoryError, git.exc.GitCommandError):
        pass

    version = v_long
    is_dirty = "dirty" in version

    if not is_dirty and version.replace(v_compact, "", ).startswith("+0"):
        version = v_compact

    ret_dict = dict(
        version=version,
        is_dirty=is_dirty,
        hash=v_hash,
        version_long=v_long,
    )
    return ret_dict