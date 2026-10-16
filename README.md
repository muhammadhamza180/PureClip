# PureClip ✦

> **The Apple-grade, lightweight smart clipboard buffer for Windows.**  
> Effortlessly collect multiple items with `Ctrl + C`, dispatch with a fluid glass palette, and track your productivity ROI.

---

## 🌟 The Vision

Traditional clipboards suffer from a fundamental friction: **single-slot amnesia**. Copying three things across documents requires six window switches (`Alt + Tab`). Built-in OS history managers (`Win + V`) break your flow with slow, clunky modals.

**PureClip eliminates this friction completely:**
1. **Natural Collection:** Keep copying as many items as you want with standard `Ctrl + C`. No new shortcuts to learn.
2. **Liquid Dispatch:** Tap a single trigger (`Alt + V` or double-tap `Ctrl + V`) to summon a frosted-glass palette right at your cursor.
3. **Instant 1-Key Paste:** Press `1`, `2`, `3` or `Space` to paste the target snippet.
4. **Smart Form-Fill (`Tab`):** Automatically cascade-paste copied fields (`Item 1` $\rightarrow$ `Tab` $\rightarrow$ `Item 2` $\rightarrow$ `Tab` $\rightarrow$ `Item 3`) directly into web forms or spreadsheets.
5. **Wispr Flow Insights:** Quantify your productivity with automated metrics: app switches avoided, seconds saved, and tracking parameters stripped.

---

## ⚡ Performance & Resource Budget

PureClip is engineered for minimal footprint:
* **Target Memory (RAM):** `< 30 MB` idle and active.
* **CPU Usage:** `0.0%` idle, `< 1%` during paste operations.
* **Latency:** Sub-10ms response time from keypress to paste.
* **Privacy & Security:** 100% offline and local-first. Zero network telemetry.

---

## 🛠️ Architecture Overview

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for full engineering specifications.

```
[OS Win32 Keyboard Hook] ──> [Hotkey Engine] ──> [Clip Buffer & Pipeline]
                                                       │
                                 ┌─────────────────────┴─────────────────────┐
                                 ▼                                           ▼
                       [Liquid UI Palette]                         [SQLite Local Metrics]
                       (Acrylic/Mica Glass)                        (Wispr Flow Analytics)
```

---

## 🗺️ Roadmap & Milestones

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for sprint breakdown.
