"""Manim (3Blue1Brown's engine, MIT) scenes for calculation lessons, rendered as transparent
clips and laid over the lesson video. Templates: recovery (loss -> gain needed), rr (risk/reward)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT = r'''
import json, os
from manim import *
P = json.loads(os.environ["TI_PARAMS"])
config.background_opacity = 0.0
config.pixel_width, config.pixel_height, config.frame_rate = 1000, 900, P["fps"]
config.frame_width = 10; config.frame_height = 9
A, A2, TXT = P["a"], P["a2"], P["txt"]
RED, GREEN = "#FF6B6B", "#3DDC97"
F = "Noto Sans Armenian"

class Recovery(Scene):
    def construct(self):
        title = Text(P.get("title", "Կորուստ → անհրաժեշտ աճ"), font=F, weight=BOLD, color=A2).scale(0.62).to_edge(UP, buff=0.5)
        self.play(FadeIn(title, shift=DOWN * 0.3), run_time=0.5)
        rows = [(10, 11), (25, 33), (50, 100)]
        grp = VGroup()
        for i, (loss, gain) in enumerate(rows):
            y = 1.3 - i * 2.0
            lb = Rectangle(width=0.001, height=0.9, fill_color=RED, fill_opacity=1, stroke_width=0).move_to([-0.8, y, 0], aligned_edge=RIGHT)
            gb = Rectangle(width=0.001, height=0.9, fill_color=GREEN, fill_opacity=1, stroke_width=0).move_to([-0.2, y, 0], aligned_edge=LEFT)
            lt = Text(f"−{loss}%", font=F, weight=BOLD, color=TXT).scale(0.7)
            gt = Text(f"+{gain}%", font=F, weight=BOLD, color=TXT).scale(0.7)
            self.play(lb.animate.stretch_to_fit_width(loss / 30).move_to([-0.8, y, 0], aligned_edge=RIGHT),
                      run_time=0.45)
            lt.next_to(lb, LEFT, buff=0.2)
            self.add(lt)
            self.play(gb.animate.stretch_to_fit_width(gain / 42).move_to([-0.2, y, 0], aligned_edge=LEFT), run_time=0.55)
            gt.next_to(gb, RIGHT, buff=0.2)
            self.add(gt)
        self.wait(P["hold"])

class RR(Scene):
    def construct(self):
        entry = Line([-3.2, -0.6, 0], [3.2, -0.6, 0], color=TXT, stroke_width=4)
        et = Text("Entry", font=F, color=TXT).scale(0.55).next_to(entry, LEFT, buff=0.2)
        self.play(Create(entry), FadeIn(et), run_time=0.5)
        risk = Rectangle(width=6.4, height=0.001, fill_color=RED, fill_opacity=0.55, stroke_width=0).move_to([0, -0.6, 0], aligned_edge=UP)
        self.play(risk.animate.stretch_to_fit_height(1.4).move_to([0, -0.6, 0], aligned_edge=UP), run_time=0.6)
        rt = Text("Risk · 1R", font=F, weight=BOLD, color=TXT).scale(0.6).move_to(risk)
        self.play(FadeIn(rt), run_time=0.3)
        rew = Rectangle(width=6.4, height=0.001, fill_color=GREEN, fill_opacity=0.55, stroke_width=0).move_to([0, -0.6, 0], aligned_edge=DOWN)
        self.play(rew.animate.stretch_to_fit_height(2.8).move_to([0, -0.6, 0], aligned_edge=DOWN), run_time=0.8)
        wt = Text("Reward · 2R", font=F, weight=BOLD, color=TXT).scale(0.6).move_to(rew)
        self.play(FadeIn(wt), run_time=0.3)
        ratio = Text("1 : 2", font=F, weight=BOLD, color=A2).scale(1.2).to_edge(UP, buff=0.3)
        self.play(GrowFromCenter(ratio), run_time=0.5)
        self.wait(P["hold"])
'''
TEMPLATES = {"recovery": ("Recovery", 2.5), "rr": ("RR", 3.0)}


def available():
    try:
        import manim  # noqa: F401
        return True
    except ImportError:
        return False


def render(template, palette, duration, fps, out_mov, title=None):
    cls, anim = TEMPLATES[template]
    work = tempfile.mkdtemp(prefix="manim_")
    script = os.path.join(work, "scene.py")
    open(script, "w").write(SCRIPT)
    params = {"fps": fps, "a": palette["a"], "a2": palette["a2"], "txt": palette["txt"],
              "hold": max(0.5, duration - anim), "title": title}
    env = dict(os.environ, TI_PARAMS=json.dumps(params, ensure_ascii=False))
    r = subprocess.run([sys.executable, "-m", "manim", "render", "-q", "h", "--transparent", "--format", "mov",
                        "--media_dir", work, "--disable_caching", "-o", "out", script, cls],
                       env=env, capture_output=True, text=True, cwd=work)
    found = [os.path.join(dp, f) for dp, _, fs in os.walk(work) for f in fs if f.startswith("out") and f.endswith(".mov")]
    if r.returncode != 0 or not found:
        raise RuntimeError("manim failed: " + (r.stderr or r.stdout)[-400:])
    shutil.move(found[0], out_mov)
    shutil.rmtree(work, ignore_errors=True)
    return out_mov
