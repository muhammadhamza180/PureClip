# PureClip Engineering Roadmap (GSD Sprints)

This roadmap outlines the lean execution plan to build, test, polish, and package PureClip into a commercial-grade product.

---

## 🏁 Phase 1: Core Engine & Multi-Slot Buffer (Hours 1–6)
* [ ] Initialize project environment & dependencies.
* [ ] Implement Win32 global hotkey listener (`Ctrl+C` monitor, `Alt+V` trigger).
* [ ] Implement in-memory FIFO / Multi-Slot Ring Buffer.
* [ ] Build Sanitization Pipeline:
  * URL tracking stripper (`utm_*`, `ref`, `fbclid`).
  * PDF single-line break normalizer.
  * Unicode & trailing whitespace cleaner.
* [ ] Implement keyboard injection for target application pasting.

## 🎨 Phase 2: Apple Liquid UI & Dispatch Palette (Hours 7–14)
* [ ] Frameless translucent palette window with Windows Acrylic/Mica blur.
* [ ] Sleek Apple-inspired dark aesthetic (`#121216` at 80% opacity, 1px border glow).
* [ ] Tactile keycap badges (`[ 1 ]`, `[ 2 ]`, `[ 3 ]`).
* [ ] Instant 1-key press dispatch:
  * Tap `1` $\rightarrow$ paste item 1 and dismiss.
  * Tap `2` $\rightarrow$ paste item 2 and dismiss.
  * Tap `Tab` $\rightarrow$ cascade-paste all items across form fields.
* [ ] Cursor-following positioning logic (`GetCursorPos`).

## 📊 Phase 3: Wispr Flow Analytics Engine (Hours 15–18)
* [ ] Embedded SQLite database (`pureclip.db`) for offline metrics.
* [ ] Calculate daily & weekly productivity ROI:
  * Number of app switches avoided.
  * Estimated minutes saved.
  * Tracking links sanitized.
* [ ] Minimalist "Insights" tab/modal.

## 🚀 Phase 4: Packaging & Release (Hours 19–24)
* [ ] System tray icon with quick settings toggles (`pystray` / native tray).
* [ ] Standalone Windows executable build (`.exe` under 25MB).
* [ ] Performance & memory audit: verify RAM footprint $< 30$ MB.
* [ ] Launch kit: Product Hunt assets, demo screen recording, Gumroad / Lemon Squeezy product setup.
