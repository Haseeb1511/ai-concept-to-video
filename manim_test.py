# from manim import *
# import json
# import os
# import random
# import math
# import numpy as np
# import textwrap
# from pathlib import Path

# from dotenv import load_dotenv
# load_dotenv()



# class RenderScene(Scene):
#     def construct(self):
#         # Fallback for manual testing if SCENE_DATA is not set in environment
#         if "SCENE_DATA" not in os.environ:
#             os.environ["SCENE_DATA"] = json.dumps({
#                 "text": "Fallback scene for manual testing",
#                 "duration": 5.0,
#                 "scene_id": 1
#             })
            
#         data = json.loads(os.environ["SCENE_DATA"])
#         # ... rest of the logic














from manim import *
import json
import os
import random
import math
import numpy as np
import textwrap
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()


class RenderScene(Scene):
    def construct(self):
        # Fallback for manual testing if SCENE_DATA is not set in environment
        if "SCENE_DATA" not in os.environ:
            os.environ["SCENE_DATA"] = json.dumps({
                "text": "Fallback scene for manual testing",
                "duration": 5.0,
                "scene_id": 1
            })
            
        data = json.loads(os.environ["SCENE_DATA"])
        text = data["text"]
        duration = data["duration"]
        scene_id = data["scene_id"]

        if scene_id == 1:
            self.scene_1(duration)
        elif scene_id == 2:
            self.scene_2(duration)
        elif scene_id == 3:
            self.scene_3(duration)
        elif scene_id == 4:
            self.scene_4(duration)
        elif scene_id == 5:
            self.scene_5(duration)
        elif scene_id == 6:
            self.scene_6(duration)
        elif scene_id == 7:
            self.scene_7(duration)
        elif scene_id == 8:
            self.scene_8(duration)

    # ─────────────────────────────────────────────
    # Scene 1 — HOOK (0–3s)
    # ─────────────────────────────────────────────
    def scene_1(self, duration):
        self.camera.background_color = "#0a0a1e"

        hook = Text("Wait…", font_size=72, color=YELLOW, weight=BOLD)
        hook.shift(UP * 1.8)

        question = Text("This is ALL AI does?", font_size=40, color=WHITE)
        question.next_to(hook, DOWN, buff=0.5)

        sub = Text("It's insanely simple.", font_size=34, color=GREEN, weight=BOLD)
        sub.next_to(question, DOWN, buff=0.5)

        self.play(Write(hook), run_time=0.6)
        self.play(FadeIn(question, shift=UP * 0.2), run_time=0.6)
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=0.5)
        self.wait(max(0.1, duration - 1.7))

    # ─────────────────────────────────────────────
    # Scene 2 — Dog + AI Brain + Dials (3–10s)
    # ─────────────────────────────────────────────
    def scene_2(self, duration):
        self.camera.background_color = "#0a0a1e"

        # Dog image placeholder (top)
        dog_box = RoundedRectangle(
            corner_radius=0.3, width=2.4, height=1.8,
            color=ORANGE, fill_color=ORANGE, fill_opacity=0.12
        )
        dog_box.shift(UP * 2.8)

        dog_text = Text("Dog Photo", font_size=28, color=ORANGE)
        dog_text.move_to(dog_box.get_center())

        label_dog = Text('"dog"', font_size=22, color=WHITE)
        label_dog.next_to(dog_box, DOWN, buff=0.12)

        # Arrow from dog to brain
        arr = Arrow(
            dog_box.get_bottom() + DOWN * 0.05,
            dog_box.get_bottom() + DOWN * 0.85,
            color=WHITE, buff=0, stroke_width=3
        )

        # AI Brain box (middle)
        brain_box = RoundedRectangle(
            corner_radius=0.3, width=3.2, height=2.5,
            color=BLUE, fill_color=BLUE, fill_opacity=0.08
        )
        brain_box.shift(DOWN * 0.9)

        brain_title = Text("AI Brain", font_size=32, color=BLUE_B, weight=BOLD)
        brain_title.next_to(brain_box, UP, buff=0.14)

        # Dials (5 × 3 grid of circles inside brain)
        dials = VGroup()
        cx = brain_box.get_center()
        for i in range(5):
            for j in range(3):
                d = Circle(radius=0.14, color=TEAL, fill_opacity=0.85)
                d.move_to(cx + RIGHT * (i * 0.52 - 1.04) + UP * (j * 0.55 - 0.55))
                dials.add(d)

        dial_label = Text("Millions of weights (dials)", font_size=20, color=TEAL)
        dial_label.next_to(brain_box, DOWN, buff=0.2)

        # Animate
        self.play(FadeIn(dog_box), Write(dog_text), run_time=0.6)
        self.play(FadeIn(label_dog), run_time=0.3)
        self.play(GrowArrow(arr), run_time=0.5)
        self.play(Create(brain_box), Write(brain_title), run_time=0.7)
        self.play(
            LaggedStart(*[FadeIn(d) for d in dials], lag_ratio=0.04),
            run_time=1.5
        )
        self.play(FadeIn(dial_label), run_time=0.4)
        self.wait(max(0.1, duration - 4.0))

    # ─────────────────────────────────────────────
    # Scene 3 — Wrong Guess + Error Bar (10–18s)
    # ─────────────────────────────────────────────
    def scene_3(self, duration):
        self.camera.background_color = "#0a0a1e"

        title = Text("AI's First Guess:", font_size=36, color=WHITE, weight=BOLD)
        title.shift(UP * 3.0)

        # Prediction row
        pred_label = Text("Prediction:", font_size=26, color=GRAY)
        pred_label.shift(UP * 1.8 + LEFT * 0.4)
        pred_val = Text("CAT", font_size=50, color=RED, weight=BOLD)
        pred_val.next_to(pred_label, RIGHT, buff=0.3)

        # Reality row
        real_label = Text("Reality:", font_size=26, color=GRAY)
        real_label.shift(UP * 0.6 + LEFT * 0.4)
        real_val = Text("DOG", font_size=50, color=GREEN, weight=BOLD)
        real_val.next_to(real_label, RIGHT, buff=0.3)

        # WRONG banner
        wrong = Text("WRONG!", font_size=58, color=RED, weight=BOLD)
        wrong.shift(DOWN * 0.7)

        # Error bar
        err_lbl = Text("Error Gap", font_size=24, color=RED)
        err_lbl.shift(DOWN * 1.85)

        bar_bg = Rectangle(
            width=3.8, height=0.45,
            fill_color="#222222", fill_opacity=0.8,
            stroke_color=GRAY, stroke_width=1
        )
        bar_bg.shift(DOWN * 2.55)

        bar_fill = Rectangle(
            width=3.6, height=0.41,
            fill_color=RED, fill_opacity=1.0, stroke_width=0
        )
        bar_fill.align_to(bar_bg, LEFT).shift(RIGHT * 0.1)
        bar_fill.shift(DOWN * 2.55)

        self.play(FadeIn(title), run_time=0.4)
        self.play(FadeIn(pred_label), FadeIn(pred_val), run_time=0.6)
        self.play(FadeIn(real_label), FadeIn(real_val), run_time=0.6)
        self.play(Write(wrong), run_time=0.6)
        self.play(FadeIn(err_lbl), Create(bar_bg), run_time=0.4)
        self.play(GrowFromEdge(bar_fill, LEFT), run_time=0.9)
        self.play(Indicate(wrong, color=RED, scale_factor=1.1), run_time=0.6)
        self.wait(max(0.1, duration - 4.1))

    # ─────────────────────────────────────────────
    # Scene 4 — Backpropagation (18–26s)
    # ─────────────────────────────────────────────
    def scene_4(self, duration):
        self.camera.background_color = "#0a0a1e"

        title = Text("Backpropagation", font_size=40, color=YELLOW, weight=BOLD)
        title.shift(UP * 3.4)

        subtitle = Text("Error signal flows BACKWARD", font_size=24, color=WHITE)
        subtitle.next_to(title, DOWN, buff=0.22)

        # 3-layer network — fits within ±1.5 x-range
        layer_x = [-1.5, 0.0, 1.5]
        node_colors = [GREEN_C, BLUE_C, RED_C]
        node_groups = []

        for li in range(3):
            grp = VGroup()
            for ni in range(3):
                n = Circle(radius=0.22, color=node_colors[li], fill_opacity=0.85)
                n.move_to(RIGHT * layer_x[li] + UP * (ni * 1.0 - 1.0))
                grp.add(n)
            node_groups.append(grp)

        # Forward connections (thin gray)
        conns = VGroup()
        for l in range(2):
            for i in range(3):
                for j in range(3):
                    ln = Line(
                        node_groups[l][i].get_center(),
                        node_groups[l + 1][j].get_center(),
                        stroke_width=0.8, color=GRAY, stroke_opacity=0.45
                    )
                    conns.add(ln)

        # Backward arrows (red, below network)
        back_arr1 = Arrow(
            RIGHT * layer_x[2] + DOWN * 1.85,
            RIGHT * layer_x[1] + DOWN * 1.85,
            color=RED_A, stroke_width=5, buff=0.28
        )
        back_arr2 = Arrow(
            RIGHT * layer_x[1] + DOWN * 1.85,
            RIGHT * layer_x[0] + DOWN * 1.85,
            color=RED_A, stroke_width=5, buff=0.28
        )

        nudge = Text("Each dial gets a tiny nudge!", font_size=24, color=TEAL)
        nudge.shift(DOWN * 3.1)

        self.play(FadeIn(title), FadeIn(subtitle), run_time=0.6)
        self.play(Create(conns), run_time=0.7)
        self.play(
            LaggedStart(*[Create(ng) for ng in node_groups], lag_ratio=0.2),
            run_time=0.9
        )
        self.play(GrowArrow(back_arr1), run_time=0.55)
        self.play(GrowArrow(back_arr2), run_time=0.55)
        self.play(
            *[Indicate(n, color=RED, scale_factor=1.18)
              for grp in node_groups[:2] for n in grp],
            run_time=1.0
        )
        self.play(FadeIn(nudge), run_time=0.5)
        self.wait(max(0.1, duration - 4.8))

    # ─────────────────────────────────────────────
    # Scene 5 — Dials Adjust + Shrinking Error (26–34s)
    # ─────────────────────────────────────────────
    def scene_5(self, duration):
        self.camera.background_color = "#0a0a1e"

        title = Text("Adjusting the Dials…", font_size=36, color=WHITE, weight=BOLD)
        title.shift(UP * 3.3)

        # Dials grid (6 × 3)
        dials = VGroup()
        for i in range(6):
            for j in range(3):
                d = Circle(radius=0.16, color=TEAL, fill_opacity=0.75)
                d.move_to(UP * 1.85 + RIGHT * (i * 0.50 - 1.25) + UP * (j * 0.50 - 0.50))
                dials.add(d)

        # New guess
        guess_row = VGroup(
            Text("New Guess:", font_size=28, color=WHITE),
            Text('"dog"', font_size=40, color=YELLOW, weight=BOLD)
        ).arrange(RIGHT, buff=0.3)
        guess_row.shift(DOWN * 0.3)

        closer = Text("Getting closer!", font_size=28, color=GREEN, weight=BOLD)
        closer.next_to(guess_row, DOWN, buff=0.3)

        # Error bar shrinking
        err_lbl = Text("Error", font_size=24, color=RED)
        err_lbl.shift(DOWN * 1.85)

        bar_bg = Rectangle(
            width=3.8, height=0.42,
            fill_color="#222222", fill_opacity=0.8,
            stroke_color=GRAY, stroke_width=1
        )
        bar_bg.shift(DOWN * 2.55)

        bar_full = Rectangle(
            width=3.6, height=0.38,
            fill_color=RED, fill_opacity=1.0, stroke_width=0
        )
        bar_full.align_to(bar_bg, LEFT).shift(RIGHT * 0.1).shift(DOWN * 2.55)

        bar_half = Rectangle(
            width=1.8, height=0.38,
            fill_color=ORANGE, fill_opacity=1.0, stroke_width=0
        )
        bar_half.align_to(bar_bg, LEFT).shift(RIGHT * 0.1).shift(DOWN * 2.55)

        self.play(FadeIn(title), run_time=0.4)
        self.play(
            LaggedStart(*[FadeIn(d) for d in dials], lag_ratio=0.04),
            run_time=0.9
        )
        self.play(
            *[d.animate.set_fill(GREEN, opacity=0.9) for d in dials[::3]],
            *[d.animate.set_fill(BLUE_C, opacity=0.9) for d in dials[1::3]],
            run_time=0.7
        )
        self.play(FadeIn(guess_row), run_time=0.5)
        self.play(FadeIn(closer), run_time=0.4)
        self.play(Create(bar_bg), Create(bar_full), run_time=0.4)
        self.play(Transform(bar_full, bar_half), run_time=1.1)
        self.wait(max(0.1, duration - 4.4))

    # ─────────────────────────────────────────────
    # Scene 6 — 10,000 Images / Error Vanished (34–42s)
    # ─────────────────────────────────────────────
    def scene_6(self, duration):
        self.camera.background_color = "#0a0a1e"

        title = Text("10,000 Images Later…", font_size=38, color=WHITE, weight=BOLD)
        title.shift(UP * 3.3)

        counter_label = Text("Trained on:", font_size=26, color=GRAY)
        counter_label.shift(UP * 2.2)

        def make_ctr(val_str):
            t = Text(val_str, font_size=40, color=YELLOW, weight=BOLD)
            t.next_to(counter_label, DOWN, buff=0.15)
            return t

        c0 = make_ctr("0 images")
        c1 = make_ctr("1,000 images")
        c2 = make_ctr("5,000 images")
        c3 = make_ctr("10,000 images")

        # Error bar (starts full red → shrinks to tiny green)
        err_lbl = Text("Error", font_size=26, color=WHITE)
        err_lbl.shift(UP * 0.6)

        bar_bg = Rectangle(
            width=3.8, height=0.46,
            fill_color="#222222", fill_opacity=0.8,
            stroke_color=GRAY, stroke_width=1
        )
        bar_bg.shift(UP * 0.0)

        bar_init = Rectangle(
            width=3.6, height=0.42,
            fill_color=RED, fill_opacity=1.0, stroke_width=0
        )
        bar_init.align_to(bar_bg, LEFT).shift(RIGHT * 0.1)

        bar_final = Rectangle(
            width=0.22, height=0.42,
            fill_color=GREEN, fill_opacity=1.0, stroke_width=0
        )
        bar_final.align_to(bar_bg, LEFT).shift(RIGHT * 0.1)

        # Prediction
        pred_row = VGroup(
            Text("Prediction:", font_size=26, color=GRAY),
            Text('"dog"  ✓', font_size=38, color=GREEN, weight=BOLD)
        ).arrange(RIGHT, buff=0.3)
        pred_row.shift(DOWN * 1.3)

        every = Text("Every. Single. Time.", font_size=30, color=YELLOW, weight=BOLD)
        every.shift(DOWN * 2.25)

        self.play(FadeIn(title), run_time=0.4)
        self.play(FadeIn(counter_label), FadeIn(c0), run_time=0.4)
        self.play(Transform(c0, c1), run_time=0.25)
        self.play(Transform(c0, c2), run_time=0.25)
        self.play(Transform(c0, c3), run_time=0.35)
        self.play(FadeIn(err_lbl), Create(bar_bg), Create(bar_init), run_time=0.5)
        self.play(Transform(bar_init, bar_final), run_time=1.4)
        self.play(FadeIn(pred_row), run_time=0.6)
        self.play(FadeIn(every), run_time=0.5)
        self.wait(max(0.1, duration - 4.6))

    # ─────────────────────────────────────────────
    # Scene 7 — WOW MOMENT (42–52s)
    # ─────────────────────────────────────────────
    def scene_7(self, duration):
        self.camera.background_color = "#0a0a1e"

        lines = VGroup(
            Text("AI is just a machine", font_size=34, color=WHITE),
            Text("that adjusts", font_size=34, color=WHITE),
            Text("millions of dials", font_size=42, color=YELLOW, weight=BOLD),
            Text("until it stops", font_size=34, color=WHITE),
            Text("being wrong.", font_size=42, color=RED, weight=BOLD),
        ).arrange(DOWN, buff=0.32)
        lines.shift(UP * 0.6)

        secret = Text("That's the ENTIRE secret.", font_size=32, color=GREEN, weight=BOLD)
        secret.next_to(lines, DOWN, buff=0.45)

        mind_blown = Text("Mind = Blown", font_size=28, color=TEAL)
        mind_blown.next_to(secret, DOWN, buff=0.28)

        for i, line in enumerate(lines):
            self.play(FadeIn(line, shift=UP * 0.15), run_time=0.45)

        self.play(Write(secret), run_time=0.8)
        self.play(FadeIn(mind_blown), run_time=0.4)
        self.play(Indicate(lines[2], scale_factor=1.08, color=YELLOW), run_time=0.7)
        self.wait(max(0.1, duration - 5.4))

    # ─────────────────────────────────────────────
    # Scene 8 — OUTRO (52–60s)
    # ─────────────────────────────────────────────
    def scene_8(self, duration):
        self.camera.background_color = "#0a0a1e"

        thanks = Text("Thanks for watching!", font_size=40, color=WHITE, weight=BOLD)
        thanks.shift(UP * 3.0)

        # Channel name with glowing box
        ch_bg = RoundedRectangle(
            corner_radius=0.4, width=4.0, height=1.1,
            fill_color="#1a2a4a", fill_opacity=0.9,
            stroke_color=BLUE_B, stroke_width=2.5
        )
        ch_bg.shift(UP * 1.5)

        channel = Text("Applie AI Lab", font_size=44, color=YELLOW, weight=BOLD)
        channel.move_to(ch_bg.get_center())

        sub_text = Text("Like & Subscribe", font_size=34, color=GREEN, weight=BOLD)
        sub_text.shift(DOWN * 0.2)

        desc = Text("for AI concepts explained simply!", font_size=22, color=WHITE)
        desc.next_to(sub_text, DOWN, buff=0.32)

        cta_row = VGroup(
            Text("LIKE", font_size=26, color=BLUE_B, weight=BOLD),
            Text("SUBSCRIBE", font_size=26, color=RED_B, weight=BOLD),
            Text("NOTIFY", font_size=26, color=YELLOW, weight=BOLD),
        ).arrange(RIGHT, buff=0.45)
        cta_row.shift(DOWN * 2.0)

        self.play(FadeIn(thanks, shift=DOWN * 0.2), run_time=0.55)
        self.play(Create(ch_bg), run_time=0.45)
        self.play(Write(channel), run_time=0.8)
        self.play(FadeIn(sub_text), run_time=0.45)
        self.play(FadeIn(desc), run_time=0.4)
        self.play(
            LaggedStart(*[FadeIn(c) for c in cta_row], lag_ratio=0.3),
            run_time=0.7
        )
        self.play(Indicate(channel, scale_factor=1.06, color=YELLOW), run_time=0.7)
        self.wait(max(0.1, duration - 4.1))