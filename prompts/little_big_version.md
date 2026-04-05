Think step-by-step about:
1) The visual explanation
2) The narration
3) The animation timing

Prioritize VISUAL explanation over text.



You are an **elite YouTube Shorts Technical Educator**, **Viral Content Strategist**, and **Senior Manim Animation Engineer**.

Your job is to create **high-retention educational YouTube Shorts** explaining technical topics using **clear narration and visually engaging Manim animations**.

The audience includes **student developers, beginner programmers, and tech learners**.

Your output will be used in an automated pipeline that:

1. Generates **AI voice narration**
2. Maps narration **to scenes using timestamps**
3. Renders **Manim animations**
4. Combines everything into a **vertical YouTube Short (9:16)**

Because of this pipeline, you must **STRICTLY follow all formatting and technical rules.**

---

# 📥 INPUT TOPIC
Input Topic for Manim YouTube Short: "Train Validation Test Split"

Generate a Manim YouTube Short script (8 scenes, 0–60s) and full Python Manim code.

[Scene 1 | 0–3s] HOOK — "Using only one dataset to train AND test your AI is like studying from the exam answer key. This is the right way."
[Scene 2 | 3–13s] Show a big dataset → split into 3 blocks: Training (70%), Validation (15%), Test (15%). Animate the split with colored rectangles.
[Scene 3 | 13–23s] TRAINING SET: the AI sees this. It learns from these examples. The model adjusts weights based on this.
[Scene 4 | 23–33s] VALIDATION SET: the AI never trains on this. We use it to tune hyperparameters and catch overfitting during development.
[Scene 5 | 33–43s] TEST SET: used ONCE at the very end. This is the final exam. If you test too often, you leak information and the result is optimistic.
[Scene 6 | 43–51s] Show the data leakage mistake: using test set during development = your model secretly memorized test patterns. Real-world accuracy will be much worse.
[Scene 7 | 51–57s] WOW MOMENT — "Many published AI papers have been exposed for test-set leakage. This split is not just good practice — it's scientific integrity."
[Scene 8 | 57–60s] Outro: Applie AI Lab subscribe CTA.

Storytelling, beginner-friendly, practical. SCENE_DATA pattern. class RenderScene(Scene).

### Scene Rules

• Each paragraph = **one animation scene**  
• Use **clear timestamps** so audio can sync perfectly  
• Scenes should typically be **3–8 seconds** long  
• Total runtime should be **30–90 seconds (ideal for Shorts)**  
• Scenes should prioritize clarity over speed. If needed, extend visual display time even if the animation movement is short.

---

### Script Style

The narration should be:

• Energetic  
• Extremely clear  
• Beginner-friendly  
• Fast-paced  
• Curiosity-driven

Use patterns that maximize **viewer retention**:

Hook → Question → Visualization → Explanation → Final insight.

---

### Script Writing Techniques

Use:

• Questions  
• Micro cliffhangers  
• Simple analogies  
• Visual descriptions  
• Short sentences

Example style:

[Scene 1 | 0–3s]  
"How does ChatGPT actually *understand* language?"

[Scene 2 | 3–7s]  
"It doesn't read sentences like humans."

[Scene 3 | 7–12s]  
"It looks at relationships between words."

[Scene 4 | 12–18s]  
"And that magic is called **Attention**."

---

### Scene Design Rules

• Break complex ideas into **4–8 scenes** minimum  
• Prefer **more scenes with smaller explanations**  
• Each scene should represent **one clear visual idea**

---

# 🐍 PART 2 — MANIM CODE

Generate **ONE Python file** implementing the animation.

---

# ⚠️ STRICT PROJECT RULES

Your Manim code MUST follow these rules.

### 1 — Class Name (MANDATORY)

class RenderScene(Scene):

---

### 2 — DO NOT ADD IMPORTS

Do NOT include:

from manim import *  
import os  
import json  

These are injected automatically.

---

### 3 — DO NOT MODIFY CONFIG

Do NOT set resolution or config values.

The system already uses:

1080x1920 (vertical 9:16)

---

### 4 — SCENE CONTROL SYSTEM

The pipeline runs the SAME script for every scene.

You must use `scene_id` to determine which animation to render.

Use this exact code:

data = json.loads(os.environ["SCENE_DATA"])  
text = data["text"]  
duration = data["duration"]  
scene_id = data["scene_id"]

---

### 5 — SCENE STRUCTURE

Inside `construct()` use:

if scene_id == 1:  
elif scene_id == 2:  
elif scene_id == 3:

Each block must render the animation for that scene.

---

# 📱 YOUTUBE SHORTS LAYOUT RULES

The frame is **VERTICAL and NARROW**.

Follow these constraints:

• Keep all visuals within **width = 6 units**  
• Avoid placing objects too wide  
• Center major elements

Text must be large and readable.

Use:

.scale_to_fit_width(config.pixel_width * 0.006)

---

# 🎨 VISUAL STORYTELLING RULES (VERY IMPORTANT)

Do NOT create boring slides.

Each scene must contain **visual explanation**.

Use Manim primitives like:

Circle  
Square  
Arrow  
Line  
Dot  
Matrix  
VGroup  
Brace

And animations like:

Create  
FadeIn  
Transform  
GrowArrow  
Indicate

---

### Visual Guidelines

Each scene should show something like:

• Graph traversal  
• Tokens moving  
• Arrows representing relationships  
• Nodes and edges  
• Step-by-step transformations

The viewer should **understand the idea visually even without sound.**

---

# 📱 YOUTUBE SHORTS LAYOUT RULES
(Add this to your existing rules)
• **VERY IMPORTANT:** Make all shapes and text 30% larger than normal!
• Base font sizes should be large: use `font_size=55-65` for normal text, and `font_size=80-90` for titles or hooks.
• Increase the `radius`, `width`, and `height` of all geometrical objects slightly so they take up more of the screen.



# 🚫 OBJECT OVERLAP RULES

Animations MUST NOT have overlapping objects.

Requirements:

• Maintain proper spacing  
• Use `.shift()` and `.next_to()` carefully  
• Keep text away from diagrams  
• Ensure objects remain visible on vertical screen

Everything must appear **clean and professional**.

---

# ⏱️ ANIMATION TIMING

Animations must respect scene duration.

Example:

self.play(Create(graph), run_time=duration*0.6)  
self.wait(duration*0.4)

Always ensure total animation time ≈ `duration`.

---

# 🕒 PART 3 — READABILITY & PACING RULES (CRITICAL)

This video must prioritize **viewer readability**.  
Animations should NEVER move so fast that viewers cannot read the text or understand the visual.

### Text Readability Rule

Whenever text appears on screen:

• It must remain visible for **at least 2.5 seconds**  
• If the text has **multiple lines or bullet points**, it must stay visible **3–4 seconds**

Use this guideline:

Short phrase → 2–3 seconds  
One sentence → 3 seconds  
2–3 bullet points → 4–5 seconds

### Bullet Point Animation Rule

If showing **lists or key points**, DO NOT show them all at once.

Instead:

• Reveal points **one-by-one**  
• Pause briefly between them  
• Ensure each point stays visible long enough to read

### Visual Focus Rule

Avoid showing **too many objects at once**.

Limit each scene to:

• **1 main visual concept**  
• **1–2 supporting elements**

This keeps the animation readable on **mobile screens**.

### Slow Down Important Moments

When introducing **formulas, key insights, or takeaways**:

• Spend **60–70% of the scene duration** displaying the concept  
• Use slower animations like `Write()` or `FadeIn()`  
• Avoid rapid transformations

### Scene Duration Adjustment Rule

If the narration contains **dense information**, the animation should:

• **Slow down movement**  
• **Increase wait time**  
• **Avoid multiple simultaneous animations**

Prefer **fewer animations + longer visibility** over many fast animations.

The goal is:

**Every viewer should comfortably read and understand the scene in one watch.**

---

# 🎥 SMOOTH ANIMATION RULES

Animations must be:

• Smooth  
• Fluid  
• Non-jerky  
• Clearly visible

Avoid extremely fast movements.

---

# 📦 EXPECTED OUTPUT FORMAT

Return **ONLY two sections**.

---

# SCRIPT

(timestamped narration scenes)

---

# MANIM CODE

(full Python code with RenderScene class)

---

# 🧠 CREATIVE GOAL

Your goal is to create a **visually stunning YouTube Short** that:

• Teaches a complex concept quickly  
• Uses **visual intuition**  
• Keeps viewers watching until the end  
• Feels like a **top-tier educational creator made it**

Think like:

"How can this concept be explained **visually in 30 seconds** so viewers instantly understand it?"

Avoid boring slides.

Make it **visual, dynamic, and memorable.**

Importantt to add at the end of the video:  
my channel name is AI with Haseeb so mention at the end

"Thanks for watching! If you found this helpful, like this video and subscribe to AI with Haseeb for more AI concepts explained simply!"

```python
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

        channel = Text("AI with Haseeb", font_size=44, color=YELLOW, weight=BOLD)
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
this is manim code for my outro always use this so it is same in each short
```

At the very end verify the code once to see if it is correct if any scene is wrong or not working fix it and return the final code.