import os
import git  # Installed with `pip3 install --user gitpython`


def get_version():
    v_raw = "unknown"
    v_compact = "unknown"
    v_long = "unknown"
    v_hash = None
    try:
        with git.Repo(os.path.realpath(__file__), search_parent_directories=True) as g_repo:
            v_raw = g_repo.git.describe(long=True, dirty=True, broken=True)
            v_compact = g_repo.git.describe(long=False, dirty=False, broken=False)
            v_long = v_raw.replace("-", "+", 1).replace("-", ".", 1)
            v_hash = g_repo.head.object.hexsha
    except (git.exc.InvalidGitRepositoryError, git.exc.GitCommandError):
        pass

    version = v_long
    is_dirty = "dirty" in version

    if not is_dirty and version.replace(v_compact, "",).startswith("+0"):
        version = v_compact

    ret_dict = dict(
        version=version,
        is_dirty=is_dirty,
        hash=v_hash,
        version_long=v_long,
    )
    return ret_dict
