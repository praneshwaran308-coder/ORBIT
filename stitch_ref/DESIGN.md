---
name: Terminal Control
colors:
  surface: '#0b141c'
  surface-dim: '#0b141c'
  surface-bright: '#313a43'
  surface-container-lowest: '#060f16'
  surface-container-low: '#141c24'
  surface-container: '#182028'
  surface-container-high: '#222b33'
  surface-container-highest: '#2d363e'
  on-surface: '#dae3ee'
  on-surface-variant: '#c1c6d6'
  inverse-surface: '#dae3ee'
  inverse-on-surface: '#29313a'
  outline: '#8b909f'
  outline-variant: '#414754'
  surface-tint: '#acc7ff'
  primary: '#acc7ff'
  on-primary: '#002f68'
  primary-container: '#498fff'
  on-primary-container: '#00285b'
  inverse-primary: '#005bbf'
  secondary: '#7bdb80'
  on-secondary: '#00390e'
  secondary-container: '#007124'
  on-secondary-container: '#91f294'
  tertiary: '#fabc45'
  on-tertiary: '#422c00'
  tertiary-container: '#bd8708'
  on-tertiary-container: '#392600'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d7e2ff'
  primary-fixed-dim: '#acc7ff'
  on-primary-fixed: '#001a40'
  on-primary-fixed-variant: '#004492'
  secondary-fixed: '#97f999'
  secondary-fixed-dim: '#7bdb80'
  on-secondary-fixed: '#002106'
  on-secondary-fixed-variant: '#005319'
  tertiary-fixed: '#ffdeaa'
  tertiary-fixed-dim: '#fabc45'
  on-tertiary-fixed: '#271900'
  on-tertiary-fixed-variant: '#5f4100'
  background: '#0b141c'
  on-background: '#dae3ee'
  surface-variant: '#2d363e'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  code-lg:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 12px
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 0.75rem
  gutter-desktop: 1rem
  margin: 1rem
  margin-desktop: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system is tailored for mission-critical developer platforms, infrastructure observability, and autonomous agent orchestration. The visual language centers on high-density utility, low latency perception, and structural precision. Drawing direct cues from high-performance developer workflows (Linear, GitHub, Datadog), it avoids extraneous ornamentation, decorative glows, and atmospheric fuzziness in favor of mathematical rigor, hairline partitions, and clear typographic hierarchy.

The aesthetic philosophy is **Engineered Minimalism**:
- **Information Density:** High spatial efficiency that maximizes usable monitoring and execution surface.
- **Utilitarian Discipline:** Every color shift, border token, and status glyph conveys actionable telemetry.
- **Cognitive Calm:** Deep slate-black canvas values reduce eye strain during continuous on-call monitoring, with accent hues reserved strictly for execution states, focused interaction points, and anomalous signals.

## Colors

The palette operates under a strictly functional hierarchy where luminance and saturation map directly to system states:

- **Canvas & Structural Surfaces:**
  - Base Canvas (`#0d1117`): Deep obsidian base layer for terminal panels, graphs, and the primary application viewport.
  - Surface Tier 1 (`#161b22`): Elevated cards, toolbars, sidebar navigations, and structural shells.
  - Surface Tier 2 (`#21262d`): Hover states, interactive table rows, dropdown menus, and popovers.
  - Borders & Hairlines (`#30363d`): 1px structural boundaries defining grid modules, split panes, and cell divisions.
  - Subtle Dividers (`#21262d`): Internal non-interactive hairline boundaries.

- **Content & Typography:**
  - Text Primary (`#f0f6fc`): High-contrast crisp white for active states, key values, titles, and terminal outputs.
  - Text Secondary (`#8b949e`): Balanced gray for labels, structural metadata, timestamps, and column headers.
  - Text Muted (`#6e7681`): Low-emphasis gray for disabled states, subtle breadcrumbs, and non-actionable hex tags.

- **State & Action Tokens:**
  - Accent Primary (`#2f81f7`): Calm operational blue dedicated to focus outlines, selected tree nodes, active tab rules, and primary triggers.
  - Operational Success (`#238636` background tint, `#3fb950` text/indicator): Signifies clean agent runs, healthy nodes, and successful deploys.
  - Operational Warning (`#d29922`): Latency spikes, retry thresholds, resource constraints, and rate limits.
  - Operational Danger (`#f85149`): Failed task executions, trace exceptions, container terminations, and destructive actions.

## Typography

The typographic system utilizes a dual-font structure: **Inter** handles narrative UI, navigation, and structural labels; **JetBrains Mono** powers telemetry data, execution logs, run IDs, memory metrics, latency counters, and syntax blocks.

- **Tabular Alignment:** Enable `font-feature-settings: "tnum" 1` globally across both font families to ensure tabular figures in live metric counters and tabular lists do not jitter during real-time streaming updates.
- **Hierarchy Rules:** Large display sizes are avoided; developer platforms need compact visual footprints. The largest desktop headline is capped at 24px.
- **Uppercase Labels:** Apply `label-sm` with uppercase styling exclusively to small technical meta-keys (e.g., `STATUS`, `LATENCY`, `P99`, `CPU`), paired with subtle letter spacing for legibility.

## Layout & Spacing

The layout is built upon an engineered 4px baseline grid operating inside a fluid pane-based layout model:

- **Structural Layout:** Split-pane architectures (multi-panel collapsible panels, dockable terminal consoles, and fluid data grids) rather than traditional marketing multi-column grids. Content stretches to fit available workspace canvas (`width: 100%`).
- **Density Profile:** Spacing is restrained to preserve contextual visibility:
  - Table rows maintain a default height of 32px (compact) to 40px (standard).
  - Component gaps favor `space-sm` (8px) and `space-md` (12px) to prevent sprawling empty canvas space.
- **Breakpoints & Reflow:**
  - **Desktop (≥ 1280px):** Multi-pane workflow active. Persistent navigation sidebar (collapsed to 56px or expanded to 240px), primary telemetry canvas, and right-hand inspector pane (360px fixed width).
  - **Tablet (768px - 1279px):** Right-hand inspector transitions to an overlay drawer. Multi-column logs collapse to single-stream data feeds.
  - **Mobile (< 768px):** Navigation moves to a bottom bar or top dropdown drawer. Metrics tables horizontally scroll with sticky primary identifier columns.

## Elevation & Depth

This system intentionally rejects atmospheric drop shadows, neon blurs, and skeuomorphic gradients. Visual depth is established purely through **tonal layering** and **hairline boundaries**:

- **Canvas Base (`#0d1117`):** The foundational plane. Houses background canvas areas, grid backdrops, and unselected log gutters.
- **Layer 1 (`#161b22`):** Primary interactive surface. Data tables, card wrappers, navigation bars, and code panels sit here, outlined with a 1px border of `#30363d`.
- **Layer 2 (`#21262d`):** Elevated overlays. Context menus, command palettes, filter flyouts, and modal dialogs. These components use a solid `#21262d` surface, a 1px `#30363d` hairline border, and a functional shadow of `0 8px 24px rgba(1, 4, 9, 0.65)` strictly to differentiate floating overlays from the underlying grid.
- **Focus & Selection:** Active elements avoid outer glow rings. Focus states use a clean, sharp 1px solid ring of `#2f81f7` with an offset of 1px against the dark canvas (`box-shadow: 0 0 0 1px #0d1117, 0 0 0 2px #2f81f7`).

## Shapes

The interface uses a calibrated, compact corner radius to project precision and stability:

- **Default Form Factor (`4px` / `0.25rem`):** Applied uniformly to buttons, text inputs, status badges, code tokens, table selection checkboxes, and card panels.
- **Enclosures & Dialogs (`6px` / `0.375rem`):** Applied to modal shells, command palettes (Cmd+K), and dropdown containers.
- **Status Indicator Dots (`9999px`):** Strict full circles reserved strictly for real-time status pings (e.g., green pulsating heartbeat dot for active agent listeners).
- **Prohibition:** Fully pill-shaped action buttons or large rounded corners (> 8px) are prohibited, as they erode structural density and misalign with terminal-grade tools.

## Components

### Buttons
- **Primary:** Background `#238636`, border 1px solid `rgba(240, 246, 252, 0.1)`, text `#ffffff`, weight 500, height 28px (compact) or 32px (standard), padding 0 12px. Hover: `#2ea043`. Active: `#238636`.
- **Secondary (Default):** Background `#21262d`, border 1px solid `#30363d`, text `#f0f6fc`. Hover: `#30363d` background, border `#8b949e`.
- **Ghost / Utility:** Background transparent, text `#8b949e`, hover text `#f0f6fc`, hover background `#161b22`.
- **Danger:** Background `#21262d`, border 1px solid `#30363d`, text `#f85149`. Hover: Background `#b62324`, text `#ffffff`, border `transparent`.

### Chips & Status Badges
- **Dimensions:** 20px fixed height, font family JetBrains Mono, size 11px, weight 500, border radius 4px, padding 0 6px.
- **Success (Running / Healthy):** Background `rgba(46, 160, 67, 0.15)`, text `#3fb950`, border 1px solid `rgba(63, 185, 80, 0.3)`.
- **Warning (Throttled / Degraded):** Background `rgba(187, 128, 9, 0.15)`, text `#d29922`, border 1px solid `rgba(210, 153, 34, 0.3)`.
- **Error (Failed / Killed):** Background `rgba(248, 81, 73, 0.15)`, text `#f85149`, border 1px solid `rgba(248, 81, 73, 0.3)`.
- **Neutral / Version Tag:** Background `#21262d`, text `#8b949e`, border 1px solid `#30363d`.

### Form Inputs
- **Base Input:** Height 32px, background `#0d1117`, border 1px solid `#30363d`, border-radius 4px, color `#f0f6fc`, font-size 13px, padding 0 8px. Placeholder color: `#6e7681`.
- **Focus State:** Border `#2f81f7`, box-shadow `0 0 0 1px #2f81f7`.
- **Checkboxes & Radios:** 14px x 14px box, border 1px solid `#30363d`, background `#0d1117`. Selected state: Background `#2f81f7`, border `#2f81f7`, white checkmark or center pip.

### Lists, Tables & Traces
- **Table Container:** Hairline outer boundary (`1px solid #30363d`), background `#161b22`, row height 32px.
- **Header Cells:** Background `#161b22`, border-bottom 1px solid `#30363d`, text `#8b949e`, font 12px Inter, weight 500.
- **Row Hover:** Background `#21262d`. Selected row: Background `rgba(47, 129, 247, 0.12)`, border-left 2px solid `#2f81f7`.
- **Log Stream Rows:** JetBrains Mono 12px, zero vertical gap, hover background `#161b22`. Timestamp column in `#6e7681`, message in `#f0f6fc`.

### Cards & Group Panels
- **Structure:** Surface background `#161b22`, border 1px solid `#30363d`, border-radius 4px, padding 12px.
- **Header:** Embedded sub-bar with bottom border 1px solid `#30363d`, 0 horizontal margin offset, padding-bottom 8px, containing title (Inter 13px bold) and right-aligned metric tags.

### Telemetry Streamers & Agent Graph Nodes
- **Agent Node Component:** 1px border `#30363d`, background `#161b22`, minimum width 180px. Top section displays agent runtime status indicator (green/amber/red dot) + name in Inter 12px bold. Bottom metrics ribbon in JetBrains Mono 11px showing latency (`ms`) and tokens used.
- **Terminal Console Panel:** Background `#0d1117`, border 1px solid `#30363d`, monospace syntax styling with primary green `#3fb950` prompt signifier (`$`).