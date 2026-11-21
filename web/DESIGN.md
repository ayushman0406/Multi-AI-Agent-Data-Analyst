# DESIGN.md — Analyst web

Direction chosen without the UXKIN library (it was unavailable), so it is not based on
side-by-side comparison of real sites. It draws on the conventions of printed lab notebooks,
audit ledgers and newspaper data desks: ruled paper, marginal annotations, a single ink colour
for "checked". Tokens live in `src/styles/tokens.css`; components use names, never raw values.

## Idea

**A ledger you can audit.** Every number the product shows either carries a green
underline (it traces to a tool result) or an amber highlight (it does not). The interface is
mostly ink on paper, so the one colour that appears means something. Structure is shown with
hairline rules and numbered margins, not boxes and shadows.

## Colour

| Token | Value | Role |
|---|---|---|
| `--paper` | `#FBFAF7` | page background |
| `--surface` | `#FFFFFF` | panels, chart surface, composer |
| `--paper-2` | `#F3F1EB` | inset wells (code, JSON, chips at rest) |
| `--ink` | `#141412` | headings, body, values |
| `--ink-2` | `#4A4944` | secondary text (9.0:1 on paper) |
| `--ink-3` | `#6F6D66` | captions, axis labels (5.0:1 on paper) |
| `--rule` | `#E5E2DA` | hairlines, gridlines |
| `--rule-2` | `#CFCBC0` | input borders, axis baseline |
| `--accent` | `#0A7D55` | **the one accent**: primary buttons, links, focus ring, grounded underline, chart slot 1 (4.9:1 on paper) |
| `--accent-ink` | `#075E41` | accent text on tinted backgrounds, hover |
| `--accent-wash` | `#E6F2EC` | selected/active backgrounds |
| `--warn` / `--warn-wash` | `#9A4A06` / `#FCEFD9` | status only: ungrounded numbers, offline banner. Always with an icon or label |
| `--error` / `--error-wash` | `#B42318` / `#FDECEA` | status only: failed step, failed request |

No dark mode: the owner asked for a light product. No gradients anywhere.

**Chart palette** (validated with the dataviz validator on `#FFFFFF`, adjacent pairs, light):
`#0A7D55 #2A78D6 #EB6834 #6250D6 #EDA100 #E87BA4` — CVD worst adjacent ΔE 16.3, normal-vision 19.6.
Single-series charts use slot 1 only. Scatter colour is capped at three series (green, blue, orange;
CVD 6.5 all-pairs, so a legend is always shown). Slots 5–6 are below 3:1 contrast, so charts with
more than four series always offer the table view. Heatmaps: sequential green ramp; correlation
(−1…1): diverging blue ↔ orange with grey midpoint `#EFEDE7`.

## Typography

| Family | Use |
|---|---|
| **Newsreader** (serif, optical sizes, italic) | display headings, dataset titles, the question at the top of each turn |
| **Geist** (grotesk) | UI, body copy, answers, key-number values |
| **Geist Mono** | tool names, args, JSON, column names, axis ticks, timings |

Scale (rem, line-height): `--t-xs .75/1.4` · `--t-sm .875/1.5` · `--t-base 1/1.6` · `--t-md 1.125/1.5` ·
`--t-lg 1.375/1.3` · `--t-xl 2/1.15` · `--t-2xl 3/1.05` · `--t-3xl clamp(3rem, 7vw, 5.75rem)/0.98`.
Weights: 400, 500, 600. Body 16px, measure 64ch for answers. Tables and axis ticks use
`tabular-nums`; standalone key numbers use proportional figures.

## Spacing, width, shape

4px base: `--s-1 4` `--s-2 8` `--s-3 12` `--s-4 16` `--s-5 24` `--s-6 32` `--s-7 48` `--s-8 64` `--s-9 96` `--s-10 144`.
Page width 1240px, reading column 720px, rail 340px. Sections on the landing page: `--s-10` apart.
Radius: `--r-1 4px` (inputs, chips, bars' data end) · `--r-2 8px` (panels) · `--r-pill 999px` (badges). One shadow,
`--shadow-pop`, only for things that float (tooltips, drawer, menus).

## Components

- **Button.** Primary: accent fill, white text. Secondary: surface, `--rule-2` border, ink text. Quiet: text only,
  underline on hover. All: 40px min height (44 on touch), 2px accent focus ring offset 2px, disabled = 45% opacity + `not-allowed`.
- **Chip** (suggested questions, follow-ups): paper-2 fill, ink text, mono arrow; hover = accent-wash + accent-ink.
- **Step row.** Margin number in mono, tool name in mono, status glyph (circle outline → spinning arc → check / cross),
  timing right-aligned. Expanded: `why` in serif italic, args as a definition list, chart, raw JSON in a well.
- **Grounding badge.** Pill: check icon + "6 of 6 numbers trace to a computed result" in accent; with any
  ungrounded: alert icon + warn colours + "5 of 6 …". Never colour alone.
- **Number marks in answers.** Grounded: 1.5px accent underline offset 3px. Ungrounded: warn-wash background, warn underline,
  `title` + screen-reader text "not found in any tool result".
- **Step reference** `[1]`: small mono superscript button; click scrolls to and flashes that step.
- **Inputs.** Surface fill, `--rule-2` border, 4px radius, focus = accent border + ring.
- **Nav.** Wordmark (serif "Analyst" + mono "/ledger"-free plain text), two links, one button. Hairline bottom rule.

## Imagery and icons

No stock photography and no illustration: the product's own output (traces, charts, tables) is the imagery.
Icons: `lucide-react` at 16/18px, 1.5 stroke, always paired with text or an aria-label. No emoji.

## Motion

Landing only: GSAP + ScrollTrigger with Lenis as the single smooth-scroll engine. The hero trace types itself once;
one pinned section scrubs through the five stages; others reveal on enter. Workspace motion is functional only
(status spinners, a 600ms flash on a referenced step). `prefers-reduced-motion: reduce` → no Lenis, no pin,
final states rendered immediately.
