"""Media hosting on a history-less `media` branch served by GitHub Pages.
Every publish rebuilds the branch as ONE orphan commit (recent files only),
so the repository never grows, no matter how many videos are published."""
import datetime as dt
import os
import shutil
import subprocess
import tempfile
import uuid
from zoneinfo import ZoneInfo

from . import settings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _git(*args, cwd=ROOT, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)


def base_url():
    import sys
    sys.path.insert(0, ROOT)
    from config import PAGES_BASE_URL
    return PAGES_BASE_URL.rstrip("/")


def publish(files, site_dir=None, dry_run=False):
    """files: [(local_path, 'reels/<name>')]. Returns {rel: public_url}."""
    br = settings.MEDIA_BRANCH
    tmp = tempfile.mkdtemp(prefix="media_")
    have_remote = _git("fetch", "-q", "origin", br, check=False).returncode == 0
    if have_remote:
        _git("worktree", "add", "-f", "--detach", tmp, f"origin/{br}")
    else:
        _git("worktree", "add", "-f", "--detach", tmp)
        for name in os.listdir(tmp):
            if name != ".git":
                p = os.path.join(tmp, name)
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    try:
        cutoff = (dt.datetime.now(ZoneInfo(settings.TZ)) - dt.timedelta(days=settings.KEEP_DAYS)).strftime("%Y%m%d")
        rdir = os.path.join(tmp, "reels")
        os.makedirs(rdir, exist_ok=True)
        for f in os.listdir(rdir):
            if f[:8].isdigit() and f[:8] < cutoff:
                os.remove(os.path.join(rdir, f))
        for src, rel in files:
            dst = os.path.join(tmp, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy(src, dst)
        if site_dir:
            for name in os.listdir(site_dir):
                s = os.path.join(site_dir, name); d = os.path.join(tmp, name)
                if os.path.isdir(s):
                    shutil.rmtree(d, ignore_errors=True); shutil.copytree(s, d)
                else:
                    shutil.copy(s, d)
        open(os.path.join(tmp, ".nojekyll"), "a").close()
        if not dry_run:
            tmpbr = "media-" + uuid.uuid4().hex[:8]
            _git("checkout", "-q", "--orphan", tmpbr, cwd=tmp)
            _git("add", "-A", cwd=tmp)
            _git("-c", "user.name=tradeinvest-bot", "-c", "user.email=actions@users.noreply.github.com",
                 "commit", "-q", "-m", "media", cwd=tmp)
            _git("push", "-q", "-f", "origin", f"HEAD:{br}", cwd=tmp)
    finally:
        _git("worktree", "remove", "-f", tmp, check=False)
        shutil.rmtree(tmp, ignore_errors=True)
    b = base_url()
    return {rel: f"{b}/{rel}" for _, rel in files}
