# PureClip Technical Architecture Specification

**Document Version:** 1.0.0  
**Author:** PureClip Core Engineering  
**Target Platform:** Windows 10 / Windows 11 (x64)  
**Target RAM Footprint:** $\le$ 30 MB  

---

## 1. System Overview & Constraints

PureClip is a high-performance, local-first background utility that enhances the Windows clipboard experience. It solves multi-slot copying friction without requiring the user to learn complex secondary copy shortcuts or suffer the cognitive friction of bulky clipboard history managers (`Win + V`).

### Non-Functional Requirements (NFRs)
1. **Memory Budget:** $\le$ 30 MB working set in RAM. Strict prohibition of heavyweight Electron runtimes.
2. **Latency Budget:** Hotkey interception to UI presentation in $\le$ 15ms. Key selection to OS paste injection in $\le$ 10ms.
3. **Data Integrity & Privacy:** 100% offline-first. No outbound network requests. Sensitive text (passwords/API keys) can be automatically purged or kept purely in volatile RAM.
4. **Resilience:** Unbreakable Win32 clipboard locking handling (graceful backoff when target apps hold the clipboard lock).

---

## 2. Component Architecture

```
                          ┌───────────────────────────┐
                          │   Windows OS Subsystem    │
                          │   (Win32, DWM, User32)    │
                          └─────────────┬─────────────┘
                                        │
           Low-Level Keyboard Hook      │   Native Clipboard Read/Write
           (WH_KEYBOARD_LL)             │   (CF_UNICODETEXT)
                                        ▼
                          ┌───────────────────────────┐
                          │     PureClip Daemon       │
                          └─────────────┬─────────────┘
                                        │
                ┌───────────────────────┼───────────────────────┐
                ▼                       ▼                       ▼
    ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐
    │     Hotkey Engine     │ │  Pipeline Engine  │ │     Slot Manager      │
    │  - Ctrl+C Sequence    │ │  - URL Cleaner    │ │  - RAM Ring Buffer    │
    │  - Alt+V / Double-Tap │ │  - PDF Unwrapper  │ │  - Form Multi-Item    │
    │  - Numeric Keys [1-9] │ │  - Whitespace     │ │  - Transient State    │
    └───────────┬───────────┘ └─────────┬─────────┘ └───────────┬───────────┘
                │                       │                       │
                └───────────────────────┼───────────────────────┘
                                        ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │                        Presentation Layer                             │
    │   - Acrylic / Mica Translucent Palette (DWM Backdrop)                 │
    │   - Spring Physics Transitions (cubic-bezier(0.16, 1, 0.3, 1))        │
    │   - Tactile Keycap Badges ([1], [2], [Tab])                           │
    │   - System Tray Icon & Status                                         │
    └───────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
    ┌───────────────────────────────────────────────────────────────────────┐
    │                  Persistence & Metrics (Local SQLite)                 │
    │   - pureclip.db: Daily stats, time-saved counters, switch savings     │
    └───────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow & State Machine

The daemon transitions through discrete states:

```
[ IDLE ]
   │
   │ User hits Ctrl+C
   ▼
[ COLLECTING ] ──> Intercept clip -> Run Pipeline -> Push to Ring Buffer -> Flash Mini Pill
   │
   │ User hits Dispatch Trigger (Alt+V or Double-Tap Ctrl+V)
   ▼
[ PALETTE_ACTIVE ] ──> Query cursor position -> Render Acrylic Glass Palette -> Grab Focus
   │
   ├─► User hits [1..9]  ──> Inject item into OS Clipboard -> Simulate Ctrl+V -> [ IDLE ]
   ├─► User hits [Tab]   ──> Cascade-paste (Item1 -> Tab -> Item2 -> Tab)    -> [ IDLE ]
   └─► User hits [Esc]   ──> Dismiss Palette                                -> [ IDLE ]
```

---

## 4. Subsystems Specification

### 4.1. Low-Level Input Interception (`HotkeyEngine`)
* Uses Win32 `SetWindowsHookEx(WH_KEYBOARD_LL, ...)` or raw input / global hotkey APIs (`RegisterHotKey`) to ensure near-zero CPU consumption when idle.
* Distinguishes between:
  * **Standard Copy Event:** Detects `Ctrl + C` without blocking the OS default behavior, then queries the clipboard for updates.
  * **Dispatch Trigger:** Intercepts `Alt + V` (or configurable alternate key) and consumes the event to display the Palette.
  * **Modal Selection:** When Palette is visible, intercepts direct keystrokes `1` through `9`, `Tab`, and `Esc`.

### 4.2. Pipeline Engine (Sanitization & Intelligence)
Raw clipboard strings pass through a modular transformation pipeline:
1. **URL Tracking Stripper:** Strips query parameters matching regex `(utm_[^&]+|fbclid|gclid|ref_[^&]+|source=[^&]+)`.
2. **PDF Wrap Normalizer:** Detects single line-breaks surrounded by non-terminal punctuation (e.g., lowercase letters, commas) and joins them with spaces while preserving genuine paragraph breaks (`\n\n`).
3. **Whitespace & Non-Breaking Space Cleaner:** Replaces `\u00A0` (`&nbsp;`), zero-width spaces (`\u200B`), and trailing line clutter.
4. **Metadata Classifier:** Tags items as `URL`, `Email`, `Code`, `Multiline`, or `Text` for contextual badge rendering in the UI.

### 4.3. Presentation Layer ("Apple Liquid UI" on Windows)
* **Frameless Glass Window:** Uses `DwmSetWindowAttribute` with `DWMWA_SYSTEMBACKDROP_TYPE = 2 (Acrylic)` or `3 (Mica)` on Windows 11/10 to achieve native hardware-accelerated translucent glass without CPU rendering penalties.
* **Transient Positioning:** Automatically positions the popup slightly offset from the current caret or mouse coordinates (`GetCaretPos` / `GetCursorPos`), ensuring zero eye-travel distance.
* **Micro-Animations:** Fluid easing curve for pop-in and dismissal.

### 4.4. Analytics & Productivity Insights ("Wispr Flow" Engine)
Every interaction updates a local SQLite database (`pureclip.db`) with zero privacy leakage:
* `clips_collected`: Total items gathered.
* `dispatches_executed`: Total pastes made via single-key selection.
* `context_switches_saved`: Calculated as $(\text{items in buffer} - 1)$ per batch session.
* `seconds_saved`: Metric formula:
  $$\text{Seconds Saved} = \sum (\text{switches avoided} \times 4.5\,\text{s}) + (\text{form auto-fills} \times 8.0\,\text{s})$$

---

## 5. Security & Privacy Model
1. **Zero Outbound Telemetry:** No tracking, no external API calls, 100% functional air-gapped.
2. **Password & Sensitive Data Handling:** Optional toggle to automatically detect password managers (e.g., Bitwarden, 1Password) or clipboard flags (`Clipboard Viewer Ignore`) and bypass persistence.
3. **Local Encryption (Optional):** Historical clips can be encrypted with Windows DPAPI (Data Protection API) tied to the user's Windows login.
