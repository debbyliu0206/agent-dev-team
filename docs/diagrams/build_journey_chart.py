"""Render the Convergence Journey figure for the writeup/README.

Two small multiples (different test-suite sizes -> % passing on one shared
y-axis, never a dual axis). Every point is a measured checkpoint:
- Study Tracker: journey percentages documented in the repo guide/README.
- Job Radar: session-state evidence (docs/demo/pipeline-run-evidence.json)
  plus local pytest measurements. The final Job Radar segment was completed
  by a human (disclosed) -> drawn dashed, not solid.

Usage: uv run python docs/diagrams/build_journey_chart.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE = "#2a78d6"      # series hue (palette slot 1)
INK = "#0b0b0b"       # text-primary
INK2 = "#52514e"      # text-secondary
GRID = "#e4e3df"
SURFACE = "#fcfcfb"

fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2), dpi=200, sharey=True)
fig.patch.set_facecolor(SURFACE)

# ---------------------------------------------------------------- Study Tracker
st_x = [0, 1, 2, 3, 4]
st_y = [13, 76, 47, 76, 100]
st_labels = ["no\narchitect", "contract-\nfirst", "regeneration\noscillation", "", "canonical layout\n+ KeepBest"]

ax = axes[0]
ax.plot(st_x, st_y, color=BLUE, linewidth=2, marker="o", markersize=6, zorder=3)
ax.set_title("Study Tracker — fully autonomous", fontsize=12, color=INK, loc="left", pad=12)
ax.annotate("59/59 green", (4, 100), textcoords="offset points", xytext=(-4, -16),
            ha="right", fontsize=10, color=INK, fontweight="bold")
ax.annotate("13%", (0, 13), textcoords="offset points", xytext=(8, -2), fontsize=9, color=INK2)
ax.annotate("oscillation 47–76%", (2.5, 60), ha="center", fontsize=9, color=INK2, style="italic")
ax.set_xticks(st_x)
ax.set_xticklabels(st_labels, fontsize=8.5, color=INK2)

# ------------------------------------------------------------------- Job Radar
jr_x = [0, 1, 2, 3, 4, 5, 6]
jr_pass = [0, 30, 31, 21, 10, 19, 40]
jr_y = [p / 40 * 100 for p in jr_pass]
jr_labels = ["start", "build\nloop", "autonomous\npeak", "dependency\ndrift", "harness\nbug", "TestFixer\nrecovery", "human\nhandoff"]

ax = axes[1]
# Autonomous part: solid. Human-completed last segment: dashed (disclosed).
ax.plot(jr_x[:6], jr_y[:6], color=BLUE, linewidth=2, marker="o", markersize=6, zorder=3)
ax.plot(jr_x[5:], jr_y[5:], color=BLUE, linewidth=2, linestyle=(0, (5, 4)),
        marker="o", markersize=6, zorder=3)
ax.set_title("Job Radar — autonomous peak, then disclosed human handoff", fontsize=12, color=INK, loc="left", pad=12)
ax.annotate("31/40 autonomous peak", (2, 77.5), textcoords="offset points", xytext=(0, 10),
            ha="center", fontsize=10, color=INK, fontweight="bold")
ax.annotate("40/40", (6, 100), textcoords="offset points", xytext=(-2, -16),
            ha="right", fontsize=10, color=INK, fontweight="bold")
ax.annotate("credits exhausted →\nhuman completes vs.\nfrozen agent tests", (5.45, 62),
            ha="center", fontsize=9, color=INK2, style="italic")
ax.set_xticks(jr_x)
ax.set_xticklabels(jr_labels, fontsize=8.5, color=INK2)

# ------------------------------------------------------------------ shared look
for ax in axes:
    ax.set_facecolor(SURFACE)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2, length=0)

axes[0].set_ylabel("tests passing (% of suite)", fontsize=10, color=INK2)

fig.suptitle("The Convergence Journey — two apps, every point a measured checkpoint",
             fontsize=14, color=INK, x=0.045, ha="left", fontweight="bold")
fig.text(0.045, 0.925, "Study Tracker: 59-test suite. Job Radar: 40-test suite; evidence in docs/demo/pipeline-run-evidence.json. Dashed = human-completed (disclosed).",
         fontsize=9, color=INK2)
fig.tight_layout(rect=(0, 0, 1, 0.90))
out = "docs/diagrams/convergence-journey.png"
fig.savefig(out, facecolor=SURFACE, bbox_inches="tight")
print("saved", out)
