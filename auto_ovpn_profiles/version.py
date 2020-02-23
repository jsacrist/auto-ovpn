import os
import git  # Installed with `pip3 install --user gitpython`


def get_version():
    ret_dict = dict()
    ret_dict["version_raw"] = "unknown"
    ret_dict["hash"] = None
    try:
        with git.Repo(os.path.realpath(__file__), search_parent_directories=True) as g_repo:
            ret_dict["version_raw"] = g_repo.git.describe(long=True, dirty=True, broken=True)
            ret_dict["hash"] = g_repo.head.object.hexsha
    except (git.exc.InvalidGitRepositoryError, git.exc.GitCommandError):
        pass
    ret_dict["version"] = ret_dict["version_raw"].replace("-", "+", 1).replace("-", ".", 1)
    ret_dict["is_dirty"] = "dirty" in ret_dict["version"]
    return ret_dict
