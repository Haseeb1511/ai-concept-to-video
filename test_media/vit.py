from manim import *
import numpy as np
import os

# ─────────────────────────────────────────────
# VERTICAL SHORT CONFIGURATION (9:16 Full HD)
# ─────────────────────────────────────────────
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_height = 14.22222
config.frame_width = config.frame_height * (1080 / 1920) # 8.0

# ─────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────
BG        = ManimColor("#0D0D1A")
ACCENT1   = ManimColor("#7B2FFF")   # vivid purple   (Transformer Encoder)
ACCENT2   = ManimColor("#FF2D78")   # hot pink       (MLP head)
TEAL      = ManimColor("#00F5D4")   # cyan-teal      (patch embeddings)
AMBER     = ManimColor("#FFB703")   # warm amber     (positional embeddings)
CORAL     = ManimColor("#FF6B6B")   # coral          (attention)
WHITE_    = ManimColor("#E8E8F0")
GRID_CLR  = ManimColor("#FFFFFF")
DIM       = ManimColor("#3A3A5C")

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def make_input_image(scale=1.0):
    img_path = r"C:\Users\hasee\Desktop\Youtube Project\yt-short-generator\images\cat.png"
    if os.path.exists(img_path):
        img = ImageMobject(img_path)
        img.scale_to_fit_width(4.5 * scale)
        return img
    else:
        # Fallback if image is missing
        return Square(side_length=4.5*scale, fill_color=TEAL, fill_opacity=0.5)

def make_patch_grid(width=4.5, height=4.5, rows=4, cols=4, color=TEAL):
    lines = VGroup()
    step_x = width / cols
    step_y = height / rows
    for i in range(1, cols):
        offset = -width/2 + i*step_x
        lines.add(Line([offset, -height/2, 0],[offset, height/2, 0], stroke_color=color, stroke_width=2.5))
    for i in range(1, rows):
        offset = -height/2 + i*step_y
        lines.add(Line([-width/2, offset, 0],[ width/2, offset, 0], stroke_color=color, stroke_width=2.5))
    border = Rectangle(width=width, height=height, stroke_color=color, stroke_width=3, fill_opacity=0)
    lines.add(border)
    return lines

def make_patch(color=TEAL, size=0.6, num=None):
    sq = RoundedRectangle(corner_radius=0.08, width=size, height=size,
                          fill_color=color, fill_opacity=0.9,
                          stroke_color=WHITE_, stroke_width=1.5)
    g  = VGroup(sq)
    if num is not None:
        t = Text(str(num), font_size=18, color=WHITE_).move_to(sq)
        g.add(t)
    return g

def make_token_col(height=1.8, width=0.35, color=TEAL, label="", n_cells=5):
    cells = VGroup(*[
        Rectangle(width=width, height=height/n_cells,
                  fill_color=color, fill_opacity=0.2 + 0.15*i,
                  stroke_color=color, stroke_width=1)
        for i in range(n_cells)
    ]).arrange(DOWN, buff=0)
    g = VGroup(cells)
    if label:
        lbl = Text(label, font_size=15, color=color)
        lbl.next_to(cells, DOWN, buff=0.15)
        g.add(lbl)
    return g

def attention_arc(start, end, color=CORAL, opacity=0.8):
    return CubicBezier(start, start+DOWN*0.4, end+DOWN*0.4, end,
                       stroke_color=color, stroke_width=2.5,
                       stroke_opacity=opacity)


###############################################################
#                        MAIN SCENE                           #
###############################################################
class VisionTransformerShort(Scene):
    def construct(self):
        self.camera.background_color = BG

        self.scene_title()
        self.scene_input_image()
        self.scene_patch_creation()
        self.scene_linear_projection()
        self.scene_pos_embedding()
        self.scene_transformer_encoder()
        self.scene_mlp_output()
        self.scene_end()

    # ══════════════════════════════════════════
    # 1. TITLE
    # ══════════════════════════════════════════
    def scene_title(self):
        title = Text("Vision\nTransformer", font_size=64,
                     gradient=(ACCENT1, TEAL), weight=BOLD).arrange(DOWN)
        sub   = Text("How AI Sees Images", font_size=32, color=DIM)
        sub.next_to(title, DOWN, buff=0.6)

        dots = VGroup(*[
            Dot(radius=np.random.uniform(0.04,0.1),
                color=random_bright_color(),
                fill_opacity=np.random.uniform(0.3,0.8))
            .move_to([np.random.uniform(-3.5,3.5), np.random.uniform(-6,6), 0])
            for _ in range(50)
        ])

        self.play(FadeIn(dots, lag_ratio=0.05), run_time=0.8)
        self.play(Write(title), run_time=1.4)
        self.play(FadeIn(sub, shift=UP*0.3), run_time=0.7)
        self.wait(1.2)
        self.play(FadeOut(VGroup(title, sub, dots)), run_time=0.6)

    # ══════════════════════════════════════════
    # 2. INPUT IMAGE
    # ══════════════════════════════════════════
    def scene_input_image(self):
        label = Text("INPUT IMAGE", font_size=28, color=DIM)
        label.to_edge(UP, buff=1.0)

        self.img = make_input_image()
        self.img.move_to(UP*1.5)

        arrow_lbl = Text("Your Image", font_size=28, color=WHITE_)
        arrow_lbl.next_to(self.img, DOWN, buff=1.5)
        arr = Arrow(arrow_lbl.get_top(), self.img.get_bottom()+DOWN*0.1,
                    buff=0.1, color=TEAL, stroke_width=4)

        self.play(FadeIn(label, shift=DOWN*0.2))
        self.play(FadeIn(self.img, scale=0.8), run_time=1.0)
        self.play(FadeIn(arrow_lbl), GrowArrow(arr), run_time=0.7)
        self.wait(0.9)
        self.play(FadeOut(VGroup(label, arrow_lbl, arr)))

    # ══════════════════════════════════════════
    # 3. PATCH CREATION
    # ══════════════════════════════════════════
    def scene_patch_creation(self):
        self.play(self.img.animate.move_to(UP*3.0), run_time=0.6)

        lbl = Text("Step 1 – Split into Patches", font_size=32, color=TEAL)
        lbl.to_edge(UP, buff=0.6)
        self.play(FadeIn(lbl))

        img_w = self.img.width
        img_h = self.img.height

        grid = make_patch_grid(width=img_w, height=img_h, rows=4, cols=4, color=TEAL)
        grid.move_to(self.img.get_center())
        self.play(Create(grid), run_time=1.2)
        self.wait(0.4)

        step_x = img_w / 4
        step_y = img_h / 4
        origin = self.img.get_center() + LEFT*(img_w/2 - step_x/2) + UP*(img_h/2 - step_y/2)
        
        flashes = VGroup()
        for r in range(4):
            for c in range(4):
                pos = origin + RIGHT*c*step_x + DOWN*r*step_y
                flash = Rectangle(width=step_x*0.9, height=step_y*0.9,
                                  fill_color=TEAL, fill_opacity=0.35, stroke_width=0).move_to(pos)
                flashes.add(flash)

        self.play(LaggedStart(*[FadeIn(f) for f in flashes], lag_ratio=0.04), run_time=1.1)
        self.wait(0.3)

        patch_label = Text("16 Patch Tokens", font_size=26, color=AMBER)
        patch_label.move_to(DOWN*1.2)

        patches = VGroup(*[
            make_patch(color=interpolate_color(TEAL, ACCENT1, i/16), size=0.6, num=i+1)
            for i in range(16)
        ]).arrange_in_grid(rows=4, cols=4, buff=0.15)
        # Using 4x4 grid for patches visually below the image makes more sense for Vertical video
        patches.next_to(patch_label, DOWN, buff=0.5)

        self.play(FadeIn(patch_label))
        self.play(
            LaggedStart(*[
                TransformFromCopy(flashes[i], patches[i])
                for i in range(16)
            ], lag_ratio=0.05),
            run_time=1.6
        )
        self.wait(0.5)

        # Clear upper half, move patches up
        self.play(FadeOut(Group(self.img, grid, flashes, lbl, patch_label)),
                  patches.animate.arrange_in_grid(rows=2, cols=8, buff=0.1).to_edge(UP, buff=1.5),
                  run_time=1.0)

        self.patches = patches

    # ══════════════════════════════════════════
    # 4. LINEAR PROJECTION  →  patch embeddings
    # ══════════════════════════════════════════
    def scene_linear_projection(self):
        lbl = Text("Step 2 – Linear Embedding", font_size=32, color=TEAL)
        lbl.to_edge(UP, buff=0.3)
        self.play(FadeIn(lbl))

        lin_box = RoundedRectangle(corner_radius=0.2, width=4.5, height=1.2,
                                   fill_color=ACCENT1, fill_opacity=0.85,
                                   stroke_color=WHITE_, stroke_width=2.5)
        lin_txt = Text("Linear Projection", font_size=24, color=WHITE_).move_to(lin_box)
        lin_grp = VGroup(lin_box, lin_txt).next_to(self.patches, DOWN, buff=1.2)

        self.play(GrowFromCenter(lin_grp))

        token_cols = VGroup()
        colors_seq = [ACCENT2] + [interpolate_color(TEAL, ACCENT1, i/16) for i in range(16)]
        labels_seq = ["CLS"] + [str(i+1) for i in range(16)]

        for col, lbl2 in zip(colors_seq, labels_seq):
            tc = make_token_col(height=1.6, width=0.35, color=col, label=lbl2, n_cells=5)
            token_cols.add(tc)

        token_cols.arrange(RIGHT, buff=0.08)
        token_cols.width = min(token_cols.width, config.frame_width - 0.6)
        token_cols.next_to(lin_grp, DOWN, buff=1.4)

        arrow_in  = Arrow(self.patches.get_bottom(), lin_box.get_top(), buff=0.1, color=TEAL, stroke_width=4)
        arrow_out = Arrow(lin_box.get_bottom(), token_cols.get_top(), buff=0.1, color=TEAL, stroke_width=4)

        self.play(GrowArrow(arrow_in))
        self.play(GrowArrow(arrow_out))
        self.play(LaggedStart(*[FadeIn(tc, shift=DOWN*0.2) for tc in token_cols], lag_ratio=0.04), run_time=1.2)
        self.wait(0.6)

        self.play(FadeOut(VGroup(lbl, self.patches, lin_grp, arrow_in, arrow_out)))
        self.token_cols = token_cols

    # ══════════════════════════════════════════
    # 5. POSITIONAL EMBEDDINGS
    # ══════════════════════════════════════════
    def scene_pos_embedding(self):
        lbl = Text("Step 3 – Add Position Info", font_size=32, color=AMBER)
        lbl.to_edge(UP, buff=0.3)
        self.play(FadeIn(lbl))

        # Move token cols up slightly to make room
        self.play(self.token_cols.animate.move_to(UP*2.0))

        pos_cols = VGroup()
        for i in range(17):
            pc = make_token_col(height=1.6, width=0.35, color=AMBER, label=f"P{i}", n_cells=5)
            pos_cols.add(pc)
            
        pos_cols.arrange(RIGHT, buff=0.08)
        pos_cols.width = self.token_cols.width
        pos_cols.next_to(self.token_cols, DOWN, buff=2.0)

        plus_signs = VGroup(*[
            Text("+", font_size=28, color=WHITE_).move_to(
                (self.token_cols[i].get_bottom() + pos_cols[i].get_top())/2
            )
            for i in range(17)
        ])

        self.play(LaggedStart(*[FadeIn(pc, shift=UP*0.2) for pc in pos_cols], lag_ratio=0.04), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(p) for p in plus_signs], lag_ratio=0.03), run_time=0.5)
        self.wait(0.5)

        combined = VGroup()
        for i in range(17):
            base_color = AMBER if i == 0 else interpolate_color(TEAL, ACCENT1, i/17)
            merged_color = interpolate_color(base_color, AMBER, 0.4)
            tc = make_token_col(height=1.6, width=0.35, color=merged_color,
                                label=("CLS" if i==0 else str(i)), n_cells=5)
            tc.width = self.token_cols[i].width
            tc.move_to(self.token_cols[i].get_center())
            combined.add(tc)

        self.play(
            LaggedStart(*[
                AnimationGroup(
                    ReplacementTransform(pos_cols[i], combined[i]),
                    FadeOut(self.token_cols[i]),
                    FadeOut(plus_signs[i])
                )
                for i in range(17)
            ], lag_ratio=0.03),
            run_time=1.2
        )
        self.wait(0.5)

        note = Text("Tokens now know their exact location! ✓", font_size=24, color=WHITE_)
        note.next_to(combined, DOWN, buff=1.5)
        self.play(FadeIn(note, shift=UP*0.2))
        self.wait(0.8)
        self.play(FadeOut(VGroup(lbl, note)))

        # Position precisely at top for Transformer to be below
        self.play(combined.animate.move_to(UP*4.5), run_time=0.6)
        self.token_seq = combined

    # ══════════════════════════════════════════
    # 6. TRANSFORMER ENCODER (Pre-LN ViT correctly ordered)
    # ══════════════════════════════════════════
    def scene_transformer_encoder(self):
        lbl = Text("Step 4 – Transformer Encoder", font_size=32, color=ACCENT1)
        lbl.to_edge(UP, buff=0.3)
        self.play(FadeIn(lbl))

        enc_box = RoundedRectangle(corner_radius=0.4, width=6.5, height=8.5,
                                   fill_color="#1A0D33", fill_opacity=0.95,
                                   stroke_color=ACCENT1, stroke_width=3)
        enc_box.next_to(self.token_seq, DOWN, buff=0.8)
        
        enc_lbl = Text("Transformer Encoder ×12", font_size=24, color=ACCENT1, weight=BOLD)
        enc_lbl.next_to(enc_box, UP, buff=0.2)

        self.play(DrawBorderThenFill(enc_box), FadeIn(enc_lbl))

        # ViT Pre-LN Pipeline: 
        # LayerNorm -> Multi-Head Attention -> [+] -> LayerNorm -> MLP -> [+]
        ln1 = RoundedRectangle(corner_radius=0.15, width=4.5, height=0.7, fill_color=DIM, fill_opacity=1, stroke_color=TEAL)
        ln1_txt = Text("LayerNorm", font_size=18, color=TEAL).move_to(ln1)

        mha = RoundedRectangle(corner_radius=0.2, width=4.5, height=1.0, fill_color="#2D1050", fill_opacity=1, stroke_color=ACCENT1)
        mha_txt = Text("Multi-Head Attention", font_size=18, color=ACCENT1).move_to(mha)

        plus1 = Circle(radius=0.25, fill_color=BG, fill_opacity=1, stroke_color=WHITE_).add(Text("+", font_size=20, color=WHITE_))

        ln2 = RoundedRectangle(corner_radius=0.15, width=4.5, height=0.7, fill_color=DIM, fill_opacity=1, stroke_color=TEAL)
        ln2_txt = Text("LayerNorm", font_size=18, color=TEAL).move_to(ln2)

        mlp = RoundedRectangle(corner_radius=0.2, width=4.5, height=1.0, fill_color="#1A0A33", fill_opacity=1, stroke_color=AMBER)
        mlp_txt = Text("MLP (Feed-Forward)", font_size=18, color=AMBER).move_to(mlp)

        plus2 = Circle(radius=0.25, fill_color=BG, fill_opacity=1, stroke_color=WHITE_).add(Text("+", font_size=20, color=WHITE_))

        pipeline = VGroup(VGroup(ln1, ln1_txt), VGroup(mha, mha_txt), plus1, VGroup(ln2, ln2_txt), VGroup(mlp, mlp_txt), plus2)
        pipeline.arrange(DOWN, buff=0.45)
        pipeline.move_to(enc_box.get_center())

        # Arrows connecting blocks with spaces
        a1 = Arrow(ln1.get_bottom(), mha.get_top(), buff=0.08, stroke_width=3)
        a2 = Arrow(mha.get_bottom(), plus1.get_top(), buff=0.08, stroke_width=3)
        a3 = Arrow(plus1.get_bottom(), ln2.get_top(), buff=0.08, stroke_width=3)
        a4 = Arrow(ln2.get_bottom(), mlp.get_top(), buff=0.08, stroke_width=3)
        a5 = Arrow(mlp.get_bottom(), plus2.get_top(), buff=0.08, stroke_width=3)
        main_arrows = VGroup(a1, a2, a3, a4, a5)

        self.play(
            LaggedStart(FadeIn(pipeline, shift=UP*0.2), FadeIn(main_arrows), lag_ratio=0.2),
            run_time=1.5
        )

        # Residual Path 1
        start1 = pipeline[0].get_top() + UP*0.2
        res1 = VGroup(
            Line(start1, start1 + RIGHT*3.0, stroke_color=TEAL, stroke_width=3),
            Line(start1 + RIGHT*3.0, plus1.get_right() + RIGHT*3.0, stroke_color=TEAL, stroke_width=3),
            Arrow(plus1.get_right() + RIGHT*3.0, plus1.get_right(), stroke_color=TEAL, stroke_width=3, buff=0.05)
        )
        
        # Residual Path 2
        start2 = pipeline[3].get_top() + UP*0.2
        res2 = VGroup(
            Line(start2, start2 + RIGHT*3.0, stroke_color=TEAL, stroke_width=3),
            Line(start2 + RIGHT*3.0, plus2.get_right() + RIGHT*3.0, stroke_color=TEAL, stroke_width=3),
            Arrow(plus2.get_right() + RIGHT*3.0, plus2.get_right(), stroke_color=TEAL, stroke_width=3, buff=0.05)
        )

        res_lbl = Text("Residual Connections", font_size=18, color=TEAL).next_to(res1, RIGHT, buff=0.2)
        res_lbl.rotate(-90*DEGREES).shift(LEFT*0.3 + DOWN*1.5)

        self.play(Create(res1), Create(res2), FadeIn(res_lbl), run_time=1.2)

        # Main Flow entering Encoder
        flow_in = Arrow(self.token_seq.get_bottom(), enc_box.get_top(), color=TEAL, buff=0.08, stroke_width=5)
        self.play(GrowArrow(flow_in))

        # Show attention happening natively
        # Draw small internal arcs in MHA to symbolize the mechanism
        arc_start = mha.get_left() + RIGHT*0.4 + DOWN*0.2
        arcs = VGroup(*[attention_arc(arc_start, arc_start + RIGHT*(0.8 + 0.6*j), color=CORAL) for j in range(5)])
        att_lbl = Text("Tokens attend to each other", font_size=16, color=CORAL).next_to(arcs, DOWN, buff=0.1)
        
        self.play(Create(arcs), FadeIn(att_lbl))
        self.wait(0.5)

        # Pulse the encoder
        for _ in range(2):
            self.play(enc_box.animate.set_stroke(color=CORAL, width=5), run_time=0.25)
            self.play(enc_box.animate.set_stroke(color=ACCENT1, width=3), run_time=0.25)
        self.wait(0.4)

        out_tokens = VGroup(*[
            make_token_col(height=1.2, width=0.3, color=ACCENT1, n_cells=4)
            for _ in range(17)
        ]).arrange(RIGHT, buff=0.08)
        out_tokens.width = self.token_seq.width
        out_tokens.next_to(enc_box, DOWN, buff=0.8)

        flow_out = Arrow(enc_box.get_bottom(), out_tokens.get_top(), color=ACCENT1, buff=0.08, stroke_width=5)
        
        self.play(GrowArrow(flow_out),
                  LaggedStart(*[FadeIn(t, shift=DOWN*0.15) for t in out_tokens], lag_ratio=0.04),
                  run_time=1.0)
        self.wait(0.5)

        self.play(FadeOut(VGroup(
            lbl, enc_box, enc_lbl, pipeline, main_arrows, res1, res2, res_lbl, 
            arcs, att_lbl, flow_in, self.token_seq, flow_out
        )))

        # Keeping only output tokens.
        self.out_tokens = out_tokens

    # ══════════════════════════════════════════
    # 7. MLP HEAD + OUTPUT
    # ══════════════════════════════════════════
    def scene_mlp_output(self):
        lbl = Text("Step 5 – Classification Head", font_size=32, color=ACCENT2)
        lbl.to_edge(UP, buff=0.3)
        self.play(FadeIn(lbl))

        # We take just the CLS token from the output tokens, isolate it, and move it to top
        cls_token = self.out_tokens[0]
        self.play(FadeOut(self.out_tokens[1:]))

        cls_box = RoundedRectangle(corner_radius=0.12, width=1.4, height=1.8,
                                   fill_color=ACCENT2, fill_opacity=0.85,
                                   stroke_color=WHITE_, stroke_width=2)
        cls_text = Text("[CLS]\nToken", font_size=20, color=WHITE_).move_to(cls_box)
        cls_grp = VGroup(cls_box, cls_text)
        
        self.play(Transform(cls_token, cls_grp))
        self.play(cls_token.animate.move_to(UP*3.5))

        mlp_box = RoundedRectangle(corner_radius=0.25, width=3.0, height=2.0,
                                   fill_color="#3D0050", fill_opacity=1,
                                   stroke_color=ACCENT2, stroke_width=3)
        mlp_box.next_to(cls_token, DOWN, buff=1.5)
        mlp_lbl_txt = Text("MLP\nHead", font_size=32, color=ACCENT2, weight=BOLD).move_to(mlp_box)
        
        arr1 = Arrow(cls_token.get_bottom(), mlp_box.get_top(), buff=0.1, color=ACCENT2, stroke_width=4)

        self.play(GrowArrow(arr1), GrowFromCenter(VGroup(mlp_box, mlp_lbl_txt)))

        categories = ["Cat", "Dog", "Bird", "Car", "Other"]
        probs      = [0.87, 0.06, 0.04, 0.02, 0.01]
        bar_colors = [TEAL, AMBER, CORAL, ACCENT1, DIM]

        bars_grp = VGroup()
        max_w    = 3.5
        for i, (cat, prob, col) in enumerate(zip(categories, probs, bar_colors)):
            bar = Rectangle(width=max_w*prob + 0.1, height=0.45,
                            fill_color=col, fill_opacity=0.9, stroke_width=0)
            
            name = Text(cat, font_size=20, color=WHITE_)
            name.next_to(bar, LEFT, buff=0.2)
            pct  = Text(f"{int(prob*100)}%", font_size=20, color=col)
            pct.next_to(bar, RIGHT, buff=0.2)
            
            row = VGroup(name, bar, pct)
            bars_grp.add(row)

        bars_grp.arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        bars_grp.next_to(mlp_box, DOWN, buff=1.5)
        # Shift slightly right to center the bars roughly
        bars_grp.shift(RIGHT*0.5)

        arr2 = Arrow(mlp_box.get_bottom(), bars_grp.get_top(), buff=0.1, color=ACCENT2, stroke_width=4)

        self.play(GrowArrow(arr2))
        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT*0.2) for b in bars_grp], lag_ratio=0.15), run_time=1.5)

        winner_box = SurroundingRectangle(bars_grp[0], color=TEAL, corner_radius=0.1, buff=0.15, stroke_width=3)
        winner_lbl = Text("🐱 Cat Selected!", font_size=36, color=TEAL, weight=BOLD)
        winner_lbl.next_to(bars_grp[0], UP, buff=0.5).shift(RIGHT*1.0)

        self.play(Create(winner_box), FadeIn(winner_lbl, shift=DOWN*0.2))
        self.wait(1.5)

        self.play(FadeOut(VGroup(lbl, cls_token, mlp_box, mlp_lbl_txt,
                                 arr1, arr2, bars_grp, winner_box, winner_lbl)))

    # ══════════════════════════════════════════
    # 8. END CARD
    # ══════════════════════════════════════════
    def scene_end(self):
        steps = [
            ("Image",       make_input_image(scale=0.35), TEAL),
            ("Patches",     VGroup(*[
                Square(side_length=0.25, fill_color=interpolate_color(TEAL, ACCENT1, i/8), fill_opacity=0.9, stroke_width=0)
                for i in range(8)
            ]).arrange_in_grid(2, 4, buff=0.06), TEAL),
            ("Embed +\nPos", make_token_col(height=1.2, width=0.35, color=AMBER, n_cells=4), AMBER),
            ("Encoder",      RoundedRectangle(corner_radius=0.15, width=1.4, height=1.4, fill_color=ACCENT1, fill_opacity=0.85, stroke_color=WHITE_, stroke_width=2), ACCENT1),
            ("MLP Head",     RoundedRectangle(corner_radius=0.15, width=1.4, height=1.4, fill_color=ACCENT2, fill_opacity=0.85, stroke_color=WHITE_, stroke_width=2), ACCENT2),
            ("Output",       Text("87% 🐱", font_size=36, color=TEAL, weight=BOLD), TEAL),
        ]

        nodes, arrows = Group(), VGroup()
        prev = None
        for i, (name, icon, col) in enumerate(steps):
            lbl = Text(name, font_size=20, color=col)
            grp = Group(icon, lbl).arrange(DOWN, buff=0.15)
            nodes.add(grp)

        nodes.arrange(DOWN, buff=0.6)
        nodes.move_to(ORIGIN)

        for i in range(len(nodes)-1):
            arr = Arrow(nodes[i].get_bottom(), nodes[i+1].get_top(), buff=0.1, color=DIM, stroke_width=3)
            arrows.add(arr)

        title = Text("Vision Transformer Pipeline", font_size=36, gradient=(ACCENT1, TEAL), weight=BOLD)
        title.to_edge(UP, buff=0.5)

        self.play(FadeIn(title))
        self.play(
            LaggedStart(*[FadeIn(n, shift=UP*0.3) for n in nodes], lag_ratio=0.15),
            run_time=1.6
        )
        self.play(
            LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.12),
            run_time=0.9
        )
        self.wait(0.8)

        glow = SurroundingRectangle(nodes[-1], color=TEAL, corner_radius=0.15, buff=0.2, stroke_width=4)
        self.play(Create(glow))
        self.play(glow.animate.set_stroke(color=AMBER, width=5), run_time=0.4)
        self.play(glow.animate.set_stroke(color=TEAL, width=4), run_time=0.4)

        outro = Text("Like & Follow for more! 🚀", font_size=32, color=WHITE_)
        outro.to_edge(DOWN, buff=0.6)
        self.play(FadeIn(outro, shift=UP*0.2))
        self.wait(2.0)
        self.play(FadeOut(Group(title, nodes, arrows, glow, outro)), run_time=1.0)



# manim -pqh vit.py VisionTransformerShort