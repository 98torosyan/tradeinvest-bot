"""Small persistent control files on main (pause flag, Telegram offset, watchdog memory)
and a safe commit helper that retries on concurrent pushes."""
import json
import os
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "control")


def _p(name):
    os.makedirs(DIR, exist_ok=True)
    return os.path.join(DIR, name)


def paused():
    return os.path.exists(_p("paused"))


def set_paused(flag):
    if flag:
        open(_p("paused"), "w").write("paused\n")
    elif os.path.exists(_p("paused")):
        os.remove(_p("paused"))


def get(name, default=None):
    try:
        return json.load(open(_p(name + ".json"), encoding="utf-8"))
    except (OSError, ValueError):
        return default


def put(name, value):
    json.dump(value, open(_p(name + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def commit(paths, message, tries=4):
    """git add/commit/push with rebase-retry (other workflows may push at the same time)."""
    run = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    run("config", "user.name", "tradeinvest-bot"); run("config", "user.email", "actions@users.noreply.github.com")
    run("add", "-A", *paths)
    if run("diff", "--cached", "--quiet").returncode == 0:
        return True
    run("commit", "-q", "-m", message)
    for i in range(tries):
        if run("pull", "-q", "--rebase", "-X", "theirs").returncode == 0 and run("push", "-q").returncode == 0:
            return True
        run("rebase", "--abort"); time.sleep(3 + i * 4)
    return False
