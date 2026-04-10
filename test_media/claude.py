"""
AIAgentShort.py
YouTube Short: "AI Agents That Control Your Computer"
Channel: AI with Haseeb
Format: 1080x1920 (9:16 vertical)
Duration: ~45 seconds
"""

from manim import *
import numpy as np
import os

# ─── Palette ────────────────────────────────────────────────────────────────
NEON_BLUE   = "#00D4FF"
DEEP_PURPLE = "#7B2FBE"
SOFT_PURPLE = "#C084FC"
ACCENT_CYAN = "#06FFA5"
DARK_BG     = "#0A0A1A"
PANEL_BG    = "#111133"
WHITE_TEXT  = "#F0F0FF"
WARN_ORANGE = "#FF6B35"
DIM_GRAY    = "#3A3A5C"

# ─── Config ─────────────────────────────────────────────────────────────────
config.pixel_width  = 1080
config.pixel_height = 1920
config.frame_rate   = 30
config.background_color = DARK_BG


# ════════════════════════════════════════════════════════════════════════════
#  HELPER BUILDERS
# ════════════════════════════════════════════════════════════════════════════

def make_glow_circle(radius=0.35, color=NEON_BLUE, opacity=0.18):
    """Concentric translucent rings that simulate a glow halo."""
    rings = VGroup()
    for i in range(4):
        r = Circle(radius=radius + i * 0.18, color=color,
                   stroke_width=max(1, 5 - i * 1.2),
                   stroke_opacity=opacity - i * 0.03,
                   fill_opacity=0)
        rings.add(r)
    return rings


def make_brain(scale=1.0, color=NEON_BLUE):
    """Simple stylised brain from ellipses + arcs."""
    body = Ellipse(width=1.4, height=1.1, color=color,
                   stroke_width=3, fill_opacity=0)
    # Left hemisphere divider
    divider = ArcBetweenPoints(body.get_top(), body.get_bottom(),
                               angle=PI / 4, color=color,
                               stroke_width=2)
    # Wrinkle arcs
    w1 = Arc(radius=0.28, angle=PI, start_angle=PI / 6,
             color=color, stroke_width=2).shift(LEFT * 0.3 + UP * 0.1)
    w2 = Arc(radius=0.28, angle=PI, start_angle=PI * 5 / 6,
             color=color, stroke_width=2).shift(RIGHT * 0.3 + UP * 0.1)
    w3 = Arc(radius=0.18, angle=PI * 0.8, start_angle=PI / 4,
             color=color, stroke_width=1.5).shift(LEFT * 0.32 + DOWN * 0.18)
    brain = VGroup(body, divider, w1, w2, w3).scale(scale)
    return brain

class Trapezoid(Polygon):
    def __init__(self, **kwargs):
        """Custom Trapezoid for the laptop base."""
        # Top width ~5.8, Bottom width ~7.0, Height 1.0
        # Centered at ORIGIN
        points = [
            [-3.5, -0.5, 0], # Bottom Left
            [ 3.5, -0.5, 0], # Bottom Right
            [ 2.9,  0.5, 0], # Top Right
            [-2.9,  0.5, 0], # Top Left
        ]
        super().__init__(*points, **kwargs)


def make_laptop(scale=1.0):
    """Simple flat-design laptop."""
    screen = RoundedRectangle(corner_radius=0.08, width=2.2, height=1.5,
                               color=NEON_BLUE, fill_color=PANEL_BG,
                               fill_opacity=1, stroke_width=3)
    # Screen content lines
    for i in range(4):
        line = Line(
            screen.get_left() + RIGHT * 0.25 + UP * (0.4 - i * 0.22),
            screen.get_right() + LEFT  * 0.25 + UP * (0.4 - i * 0.22),
            stroke_width=1.5,
            color=NEON_BLUE if i == 0 else DIM_GRAY,
            stroke_opacity=0.7 if i > 0 else 1,
        )
        screen.add(line)
    # Base
    base = Trapezoid(color=NEON_BLUE, fill_color=PANEL_BG, fill_opacity=1,
                     stroke_width=2).scale(0.38)
    base.stretch(0.28, 1)
    base.next_to(screen, DOWN, buff=0)
    return VGroup(screen, base).scale(scale)


def make_terminal_window(lines, width=3.4, height=2.0):
    """Dark terminal panel with coloured text lines."""
    panel = RoundedRectangle(corner_radius=0.12, width=width, height=height,
                              fill_color=PANEL_BG, fill_opacity=0.97,
                              stroke_color=NEON_BLUE, stroke_width=2)
    # Title bar dots
    dot_colors = ["#FF5F57", "#FFBD2E", "#28CA42"]
    dots = VGroup(*[
        Dot(radius=0.07, color=c).shift(LEFT * (0.5 - i * 0.22))
        for i, c in enumerate(dot_colors)
    ]).next_to(panel.get_top(), DOWN, buff=0.18)

    text_group = VGroup()
    for i, (txt, col) in enumerate(lines):
        t = Text(txt, font="Courier New", font_size=18, color=col)
        text_group.add(t)
    text_group.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    text_group.next_to(dots, DOWN, buff=0.18).align_to(panel, LEFT).shift(RIGHT * 0.2)

    return VGroup(panel, dots, text_group)


def make_icon_box(symbol, label, icon_color=NEON_BLUE, size=0.85):
    """Rounded box with a symbol + small label underneath."""
    box = RoundedRectangle(corner_radius=0.12, width=size, height=size,
                            fill_color=PANEL_BG, fill_opacity=1,
                            stroke_color=icon_color, stroke_width=2)
    sym = Text(symbol, font_size=int(26 * size), color=icon_color).move_to(box)
    lbl = Text(label, font_size=int(13 * size), color=WHITE_TEXT).next_to(box, DOWN, buff=0.08)
    return VGroup(box, sym, lbl)


def make_arrow(start, end, color=NEON_BLUE, width=4):
    return Arrow(start, end, buff=0.15, color=color,
                 stroke_width=width, max_tip_length_to_length_ratio=0.18)


def pulse_animation(mob, scale=1.08, duration=0.4):
    return Succession(
        mob.animate(rate_func=there_and_back, run_time=duration).scale(scale)
    )


def starfield(n=60, spread_x=5.5, spread_y=10.0):
    """Background particle stars."""
    dots = VGroup()
    rng = np.random.default_rng(42)
    for _ in range(n):
        x = rng.uniform(-spread_x, spread_x)
        y = rng.uniform(-spread_y, spread_y)
        r = rng.uniform(0.012, 0.045)
        op = rng.uniform(0.15, 0.55)
        d = Dot(radius=r, color=WHITE, fill_opacity=op).move_to([x, y, 0])
        dots.add(d)
    return dots


# ════════════════════════════════════════════════════════════════════════════
#  SCENE DISPATCH
# ════════════════════════════════════════════════════════════════════════════

SCENE_DATA = {
    "AIAgentShort": "all",
}


class AIAgentShort(Scene):
    """
    Full ~45s YouTube Short — all 6 scenes in one continuous render.
    Run with:
        manim -pqh AIAgentShort.py AIAgentShort
    """

    def construct(self):
        # Persistent starfield background
        stars = starfield()
        self.add(stars)

        self.scene1_hook()
        self.scene2_chatbot()
        self.scene3_agent_actions()
        self.scene4_pipeline()
        self.scene5_loop()
        self.scene6_finale()

    # ─────────────────────────────────────────────────────────────────────
    # SCENE 1 — HOOK  (0–4 s)
    # ─────────────────────────────────────────────────────────────────────
    def scene1_hook(self):
        # ── Headline ──
        headline = Text("AI That Can Control\nYour Computer",
                        font_size=52, color=WHITE_TEXT,
                        weight=BOLD, line_spacing=0.9)
        headline.to_edge(UP, buff=1.1)

        # Gradient-ish underline
        uline = Line(headline.get_left() + DOWN * 0.05,
                     headline.get_right() + DOWN * 0.05,
                     color=NEON_BLUE, stroke_width=3)
        uline.next_to(headline, DOWN, buff=0.12)

        # ── Laptop ──
        laptop = make_laptop(scale=1.1)
        laptop.move_to(ORIGIN + DOWN * 0.6)

        # ── Brain ──
        brain = make_brain(scale=1.0, color=SOFT_PURPLE)
        glow  = make_glow_circle(radius=0.72, color=SOFT_PURPLE, opacity=0.15)
        brain_group = VGroup(glow, brain)
        brain_group.next_to(laptop, RIGHT, buff=0.7).shift(UP * 0.1)

        # Pulse ring on brain
        ring = Circle(radius=0.9, color=SOFT_PURPLE, stroke_width=1.5,
                      stroke_opacity=0).move_to(brain_group)

        # ── Peripheral icons ──
        icons = VGroup(
            make_icon_box("⌨", "Terminal", NEON_BLUE,  0.72),
            make_icon_box("📄", "Code",    ACCENT_CYAN, 0.72),
            make_icon_box("🌐", "Browser", SOFT_PURPLE, 0.72),
            make_icon_box("📁", "Files",   WARN_ORANGE, 0.72),
        )
        icons.arrange(RIGHT, buff=0.35)
        icons.next_to(laptop, DOWN, buff=0.6)

        # Arrows from brain to each icon
        arrows = VGroup()
        for icon in icons:
            a = CurvedArrow(brain_group.get_bottom(),
                            icon.get_top(),
                            angle=-PI / 5,
                            color=NEON_BLUE,
                            stroke_width=2.5,
                            tip_length=0.15)
            arrows.add(a)

        # ── Animate ──
        self.play(Write(headline), run_time=0.7)
        self.play(Create(uline), run_time=0.3)
        self.play(FadeIn(laptop, scale=0.6), run_time=0.5)
        self.play(FadeIn(brain_group, scale=0.5), run_time=0.4)
        # Pulse ring
        self.play(
            ring.animate(rate_func=linear).scale(2).set_stroke(opacity=0),
            run_time=0.6
        )
        self.play(LaggedStart(*[FadeIn(ic, shift=UP * 0.3) for ic in icons],
                              lag_ratio=0.15, run_time=0.6))
        self.play(LaggedStart(*[Create(a) for a in arrows],
                              lag_ratio=0.12, run_time=0.7))
        self.wait(0.4)

        # ── Transition: keep stars, wipe scene ──
        self.play(
            FadeOut(VGroup(headline, uline, laptop, brain_group,
                           ring, icons, arrows)),
            run_time=0.45
        )

    # ─────────────────────────────────────────────────────────────────────
    # SCENE 2 — TRADITIONAL CHATBOT  (4–10 s)
    # ─────────────────────────────────────────────────────────────────────
    def scene2_chatbot(self):
        # ── Label ──
        label = Text("Traditional AI Chatbot",
                     font_size=38, color=WARN_ORANGE, weight=BOLD)
        label.to_edge(UP, buff=1.0)

        # ── Chat panel ──
        panel = RoundedRectangle(corner_radius=0.18, width=4.0, height=5.2,
                                  fill_color=PANEL_BG, fill_opacity=1,
                                  stroke_color=DIM_GRAY, stroke_width=2)
        panel.shift(DOWN * 0.2)

        # Title bar
        bar = RoundedRectangle(corner_radius=0.18, width=4.0, height=0.55,
                                fill_color="#1A1A3E", fill_opacity=1,
                                stroke_color=DIM_GRAY, stroke_width=0)
        bar.align_to(panel, UP).align_to(panel, LEFT)
        bar_label = Text("ChatAI", font_size=18, color=DIM_GRAY).move_to(bar)

        # User bubble
        user_txt = Text("Write Python code\nto sort a list",
                        font_size=20, color=WHITE_TEXT, line_spacing=0.85)
        user_bubble = RoundedRectangle(corner_radius=0.14, width=2.8, height=0.9,
                                        fill_color="#1E3A5F", fill_opacity=1,
                                        stroke_color=NEON_BLUE, stroke_width=1.5)
        user_bubble.next_to(bar, DOWN, buff=0.35).align_to(panel, RIGHT).shift(LEFT * 0.2)
        user_txt.move_to(user_bubble)

        # User tag
        user_tag = Text("You", font_size=15, color=NEON_BLUE)
        user_tag.next_to(user_bubble, UP, buff=0.06).align_to(user_bubble, RIGHT)

        # Response bubble
        code_lines = [
            ("def sort_list(lst):", ACCENT_CYAN),
            ("    return sorted(lst)", WHITE_TEXT),
            ("", WHITE_TEXT),
            ("# Returns sorted list", DIM_GRAY),
        ]
        code_group = VGroup()
        for line, col in code_lines:
            code_group.add(Text(line, font="Courier New", font_size=17, color=col))
        code_group.arrange(DOWN, aligned_edge=LEFT, buff=0.1)

        ai_bubble = RoundedRectangle(corner_radius=0.14, width=3.2, height=1.7,
                                      fill_color="#1A2E1A", fill_opacity=1,
                                      stroke_color=ACCENT_CYAN, stroke_width=1.5)
        ai_bubble.next_to(user_bubble, DOWN, buff=0.4).align_to(panel, LEFT).shift(RIGHT * 0.2)
        code_group.move_to(ai_bubble).shift(LEFT * 0.1)

        ai_tag = Text("AI", font_size=15, color=ACCENT_CYAN)
        ai_tag.next_to(ai_bubble, UP, buff=0.06).align_to(ai_bubble, LEFT)

        # ── "But it can't DO anything" X mark ──
        x_mark = Text("✗ Only Text. No Action.",
                       font_size=28, color=WARN_ORANGE, weight=BOLD)
        x_mark.next_to(panel, DOWN, buff=0.55)

        # ── Animate ──
        self.play(Write(label), run_time=0.5)
        self.play(FadeIn(panel), FadeIn(bar), FadeIn(bar_label), run_time=0.4)
        self.play(FadeIn(user_bubble, shift=LEFT * 0.3),
                  FadeIn(user_tag), run_time=0.4)
        self.play(FadeIn(ai_bubble, shift=RIGHT * 0.3),
                  FadeIn(ai_tag), run_time=0.4)
        self.play(LaggedStart(
            *[FadeIn(t, shift=UP * 0.15) for t in code_group],
            lag_ratio=0.2, run_time=0.8
        ))
        self.wait(0.3)
        self.play(FadeIn(x_mark, scale=0.8), run_time=0.4)
        self.wait(0.5)

        self.play(FadeOut(VGroup(label, panel, bar, bar_label,
                                 user_bubble, user_tag, user_txt,
                                 ai_bubble, ai_tag, code_group, x_mark)),
                  run_time=0.4)

    # ─────────────────────────────────────────────────────────────────────
    # SCENE 3 — AI AGENT ACTIONS  (10–20 s)
    # ─────────────────────────────────────────────────────────────────────
    def scene3_agent_actions(self):
        # ── Title ──
        title = Text("AI Agent in Action",
                     font_size=42, color=NEON_BLUE, weight=BOLD)
        title.to_edge(UP, buff=1.0)

        # ── Brain (centre-left) ──
        brain = make_brain(scale=1.05, color=SOFT_PURPLE)
        glow  = make_glow_circle(radius=0.75, color=SOFT_PURPLE)
        bg = VGroup(glow, brain)
        bg.move_to(LEFT * 1.6 + UP * 0.5)

        brain_label = Text("AI Agent", font_size=22, color=SOFT_PURPLE)
        brain_label.next_to(bg, DOWN, buff=0.15)

        # ── Terminal window ──
        terminal = make_terminal_window([
            ("$ pip install numpy",    ACCENT_CYAN),
            ("Collecting numpy ...",   DIM_GRAY),
            ("Successfully installed", ACCENT_CYAN),
            ("$ python main.py",       NEON_BLUE),
            ("[✓] Tests passed: 5/5",  ACCENT_CYAN),
        ], width=3.5, height=2.8)
        terminal.move_to(RIGHT * 1.4 + UP * 0.3)

        # Connector arrow
        arrow_t = make_arrow(bg.get_right(), terminal.get_left())

        # ── Code file ──
        code_lines_raw = [
            ("import numpy as np",        SOFT_PURPLE),
            ("def process(data):",        NEON_BLUE),
            ("    arr = np.array(data)",  WHITE_TEXT),
            ("    return arr.mean()",     WHITE_TEXT),
        ]
        code_panel = make_terminal_window(code_lines_raw, width=3.5, height=2.0)
        code_panel.move_to(RIGHT * 1.4 + DOWN * 2.5)

        arrow_c = make_arrow(bg.get_right() + DOWN * 0.3,
                             code_panel.get_left() + UP * 0.2,
                             color=ACCENT_CYAN)

        # Action badge
        def action_badge(text, color=NEON_BLUE):
            b = RoundedRectangle(corner_radius=0.1, width=2.6, height=0.45,
                                  fill_color=PANEL_BG, fill_opacity=1,
                                  stroke_color=color, stroke_width=1.8)
            t = Text(text, font_size=19, color=color).move_to(b)
            return VGroup(b, t)

        actions = VGroup(
            action_badge("① Open file",          NEON_BLUE),
            action_badge("② Write code",         ACCENT_CYAN),
            action_badge("③ pip install numpy",  SOFT_PURPLE),
            action_badge("④ Run & test",         WARN_ORANGE),
        )
        actions.arrange(DOWN, buff=0.22)
        actions.to_edge(LEFT, buff=0.3).shift(DOWN * 2.8)

        # ── Animate ──
        self.play(Write(title), run_time=0.5)
        self.play(FadeIn(bg, scale=0.6), FadeIn(brain_label), run_time=0.5)
        self.play(FadeIn(terminal, shift=RIGHT * 0.4), GrowArrow(arrow_t), run_time=0.6)
        # Reveal terminal lines one by one
        lines_vg = terminal[-1]  # text_group is last child
        for line in lines_vg:
            self.play(FadeIn(line, shift=UP * 0.1), run_time=0.22)
        self.play(FadeIn(code_panel, shift=DOWN * 0.3), GrowArrow(arrow_c), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(a, shift=RIGHT * 0.2) for a in actions],
                              lag_ratio=0.18, run_time=0.9))
        self.wait(0.4)

        self.play(FadeOut(VGroup(title, bg, brain_label, terminal, arrow_t,
                                  code_panel, arrow_c, actions)),
                  run_time=0.4)

    # ─────────────────────────────────────────────────────────────────────
    # SCENE 4 — PIPELINE  (20–30 s)
    # ─────────────────────────────────────────────────────────────────────
    def scene4_pipeline(self):
        title = Text("How It Works",
                     font_size=44, color=WHITE_TEXT, weight=BOLD)
        title.to_edge(UP, buff=1.0)

        # Pipeline nodes
        node_data = [
            ("💡", "Your\nIdea",    WARN_ORANGE),
            ("🧠", "AI\nBrain",    SOFT_PURPLE),
            ("🛠", "Tools",        NEON_BLUE),
            ("✅", "Result",       ACCENT_CYAN),
        ]
        nodes = VGroup()
        for sym, lbl, col in node_data:
            circle = Circle(radius=0.58, color=col,
                            fill_color=PANEL_BG, fill_opacity=1,
                            stroke_width=3)
            glow = make_glow_circle(radius=0.58, color=col)
            icon = Text(sym, font_size=30).move_to(circle)
            label = Text(lbl, font_size=18, color=col,
                         line_spacing=0.8).next_to(circle, DOWN, buff=0.12)
            nodes.add(VGroup(glow, circle, icon, label))

        nodes.arrange(DOWN, buff=0.75)
        nodes.move_to(LEFT * 1.6 + UP * 0.0)

        # Arrows between nodes
        pipe_arrows = VGroup()
        for i in range(len(nodes) - 1):
            a = make_arrow(nodes[i].get_bottom(),
                           nodes[i + 1].get_top(),
                           color=DIM_GRAY, width=3)
            pipe_arrows.add(a)

        # Tool icons on the right
        tool_icons = VGroup(
            make_icon_box("⌨", "Terminal", NEON_BLUE,  0.78),
            make_icon_box("📝", "Editor",  ACCENT_CYAN, 0.78),
            make_icon_box("🌐", "Browser", SOFT_PURPLE, 0.78),
            make_icon_box("📁", "Files",   WARN_ORANGE, 0.78),
        )
        tool_icons.arrange(DOWN, buff=0.35)
        tool_icons.move_to(RIGHT * 1.8)

        # Bracket connecting Tools node to tool list
        brace = Brace(tool_icons, direction=LEFT, color=NEON_BLUE, buff=0.1)
        brace_label = Text("picks\nthe right\ntool",
                           font_size=17, color=NEON_BLUE,
                           line_spacing=0.8).next_to(brace, LEFT, buff=0.1)

        # ── Animate ──
        self.play(Write(title), run_time=0.5)
        for i, (node, pa) in enumerate(zip(nodes,
                                            [*pipe_arrows, None])):
            self.play(FadeIn(node, scale=0.7), run_time=0.32)
            if pa:
                self.play(GrowArrow(pa), run_time=0.22)

        self.play(LaggedStart(*[FadeIn(t, shift=LEFT * 0.2) for t in tool_icons],
                              lag_ratio=0.15, run_time=0.7))
        self.play(FadeIn(brace), Write(brace_label), run_time=0.5)

        # Highlight arrows flowing top-to-bottom
        for a in pipe_arrows:
            self.play(a.animate.set_color(NEON_BLUE), run_time=0.15)
        self.wait(0.4)

        self.play(FadeOut(VGroup(title, nodes, pipe_arrows,
                                  tool_icons, brace, brace_label)),
                  run_time=0.4)

    # ─────────────────────────────────────────────────────────────────────
    # SCENE 5 — AUTONOMOUS LOOP  (30–40 s)
    # ─────────────────────────────────────────────────────────────────────
    def scene5_loop(self):
        title = Text("Autonomous Loop",
                     font_size=42, color=NEON_BLUE, weight=BOLD)
        title.to_edge(UP, buff=1.0)

        # ── Four nodes in a circular loop ──
        loop_labels = [
            ("🤔 Think",   SOFT_PURPLE, UL),
            ("⚡ Act",    WARN_ORANGE, UR),
            ("👁 Observe", ACCENT_CYAN, DR),
            ("📈 Improve", NEON_BLUE,   DL),
        ]
        radius = 1.55
        loop_nodes = VGroup()
        positions = [
            UP    * radius,
            RIGHT * radius,
            DOWN  * radius,
            LEFT  * radius,
        ]
        for (lbl, col, _), pos in zip(loop_labels, positions):
            box = RoundedRectangle(corner_radius=0.18, width=1.8, height=0.62,
                                    fill_color=PANEL_BG, fill_opacity=1,
                                    stroke_color=col, stroke_width=2.5)
            txt = Text(lbl, font_size=22, color=col).move_to(box)
            node = VGroup(box, txt)
            node.move_to(pos)
            loop_nodes.add(node)

        loop_nodes.shift(DOWN * 0.3)

        # Curved arrows connecting nodes in a cycle
        loop_arrows = VGroup()
        for i in range(4):
            src = loop_nodes[i].get_center()
            dst = loop_nodes[(i + 1) % 4].get_center()
            a = CurvedArrow(src, dst, angle=PI / 3.5,
                            color=DIM_GRAY, stroke_width=2.8,
                            tip_length=0.18)
            loop_arrows.add(a)

        # Progress bar
        bar_bg = RoundedRectangle(corner_radius=0.1, width=4.2, height=0.38,
                                   fill_color=DIM_GRAY, fill_opacity=1,
                                   stroke_color=NEON_BLUE, stroke_width=1.5)
        bar_fill = RoundedRectangle(corner_radius=0.1, width=0.01, height=0.38,
                                     fill_color=NEON_BLUE, fill_opacity=1,
                                     stroke_width=0)
        bar_bg.next_to(loop_nodes, DOWN, buff=0.75)
        bar_fill.align_to(bar_bg, LEFT).align_to(bar_bg, UP)
        bar_lbl = Text("Code Quality", font_size=18, color=DIM_GRAY)
        bar_lbl.next_to(bar_bg, UP, buff=0.12)
        bar_pct = Text("0%", font_size=20, color=NEON_BLUE)
        bar_pct.next_to(bar_bg, RIGHT, buff=0.15)

        # ── Animate ──
        self.play(Write(title), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(n, scale=0.7) for n in loop_nodes],
                              lag_ratio=0.18, run_time=0.7))
        self.play(LaggedStart(*[Create(a) for a in loop_arrows],
                              lag_ratio=0.15, run_time=0.8))
        self.play(FadeIn(bar_bg), FadeIn(bar_lbl), FadeIn(bar_fill),
                  FadeIn(bar_pct), run_time=0.4)

        # Three loop iterations with progress
        for iteration in range(3):
            for i, (arrow, node) in enumerate(zip(loop_arrows, loop_nodes)):
                col = loop_labels[i][1]
                self.play(
                    arrow.animate.set_color(col),
                    node[0].animate.set_stroke(color=col, width=3.5),
                    run_time=0.18
                )
                self.play(
                    arrow.animate.set_color(DIM_GRAY),
                    node[0].animate.set_stroke(color=loop_labels[i][1], width=2.5),
                    run_time=0.1
                )

            # Progress bar grows
            target_width = 1.4 + iteration * 1.4
            pct_val = int(((iteration + 1) / 3) * 100)
            new_fill = bar_fill.copy().set_width(target_width).align_to(bar_bg, LEFT)
            self.play(
                Transform(bar_fill, new_fill),
                ChangeDecimalToValue(
                    DecimalNumber(0, font_size=20, color=NEON_BLUE,
                                  num_decimal_places=0).next_to(bar_bg, RIGHT, buff=0.15),
                    pct_val,
                ) if False else
                bar_pct.animate.become(
                    Text(f"{pct_val}%", font_size=20, color=NEON_BLUE)
                    .next_to(bar_bg, RIGHT, buff=0.15)
                ),
                run_time=0.3
            )

        self.wait(0.4)
        self.play(FadeOut(VGroup(title, loop_nodes, loop_arrows,
                                  bar_bg, bar_fill, bar_lbl, bar_pct)),
                  run_time=0.4)

    # ─────────────────────────────────────────────────────────────────────
    # SCENE 6 — FINALE  (40–50 s)
    # ─────────────────────────────────────────────────────────────────────
    def scene6_finale(self):
        # ── Burst of particles ──
        particles = VGroup()
        rng = np.random.default_rng(7)
        for _ in range(40):
            angle  = rng.uniform(0, TAU)
            dist   = rng.uniform(0.4, 2.8)
            col    = rng.choice([NEON_BLUE, SOFT_PURPLE, ACCENT_CYAN, WARN_ORANGE])
            d = Dot(radius=rng.uniform(0.04, 0.12), color=col, fill_opacity=0.8)
            d.move_to(ORIGIN + np.array([np.cos(angle), np.sin(angle), 0]) * dist)
            particles.add(d)

        self.play(LaggedStart(*[GrowFromCenter(p) for p in particles],
                              lag_ratio=0.02, run_time=0.7))

        # ── Central brain (large) ──
        brain = make_brain(scale=1.5, color=NEON_BLUE)
        glow  = make_glow_circle(radius=1.1, color=NEON_BLUE, opacity=0.12)
        brain_group = VGroup(glow, brain)
        brain_group.move_to(UP * 0.5)

        self.play(FadeIn(brain_group, scale=0.4), run_time=0.5)

        # ── Task orbits ──
        task_data = [
            ("⌨ Coding",     NEON_BLUE,   1.9, 0),
            ("🐛 Debugging", WARN_ORANGE, 2.2, PI / 2),
            ("📦 Installing", SOFT_PURPLE, 2.0, PI),
            ("🧪 Testing",   ACCENT_CYAN, 2.3, PI * 3 / 2),
        ]
        task_group = VGroup()
        orbit_arrows = VGroup()
        for lbl, col, r, angle in task_data:
            pos = brain_group.get_center() + r * np.array(
                [np.cos(angle), np.sin(angle), 0])
            box = make_icon_box(lbl.split()[0], lbl.split()[1], col, 0.82)
            box.move_to(pos)
            task_group.add(box)
            a = make_arrow(brain_group.get_center(), pos, color=col, width=2.5)
            orbit_arrows.add(a)

        self.play(LaggedStart(*[FadeIn(t, scale=0.5) for t in task_group],
                              lag_ratio=0.15, run_time=0.7))
        self.play(LaggedStart(*[GrowArrow(a) for a in orbit_arrows],
                              lag_ratio=0.12, run_time=0.6))

        # ── Rotate tasks around the brain ──
        self.play(
            Rotate(task_group, angle=PI / 5,
                   about_point=brain_group.get_center(),
                   run_time=1.0, rate_func=smooth),
        )

        # ── Final text ──
        final_text = Text("AI Agents:\nThe Future of Programming",
                          font_size=44, color=WHITE_TEXT,
                          weight=BOLD, line_spacing=0.88)
        final_text.to_edge(DOWN, buff=1.8)

        # Gradient underline
        f_uline = Line(final_text.get_left(), final_text.get_right(),
                       color=NEON_BLUE, stroke_width=3)
        f_uline.next_to(final_text, DOWN, buff=0.1)

        # Channel branding
        channel = Text("AI with Haseeb",
                       font_size=30, color=SOFT_PURPLE, weight=BOLD)
        channel.next_to(f_uline, DOWN, buff=0.28)

        self.play(
            Write(final_text), run_time=0.7
        )
        self.play(Create(f_uline), run_time=0.3)
        self.play(FadeIn(channel, scale=0.8), run_time=0.4)

        # Pulse rings on brain
        for _ in range(2):
            ring = Circle(radius=1.2, color=NEON_BLUE, stroke_width=2,
                          stroke_opacity=0.9).move_to(brain_group)
            self.play(ring.animate(rate_func=linear)
                       .scale(2.4)
                       .set_stroke(opacity=0),
                      run_time=0.6)

        self.wait(0.8)

        # ── Fade to black ──
        black = Rectangle(width=9, height=16, fill_color=BLACK,
                           fill_opacity=0, stroke_width=0)
        self.play(
            black.animate.set_fill(opacity=1),
            run_time=0.8
        )
        self.wait(0.2)