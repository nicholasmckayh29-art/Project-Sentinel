# Mr. Robot Design System

Shared tokens live in [`packages/theme/tokens.ts`](../packages/theme/tokens.ts).

## Visual language

- **Background**: near-black `#0D0D0D`
- **Accent**: terminal green `#00FF41`
- **Alerts**: green ▼ drops, red ▲ increases
- **Typography**: JetBrains Mono for data/headers, system sans for body
- **Effects**: scanline overlay, typewriter boot, `[ CLASSIFIED ]` badges

## Web implementation

- Tailwind CSS v4 custom properties in [`web/app/globals.css`](../web/app/globals.css)
- Components: `Scanlines`, `TerminalBoot`, `AlertCard`, `card-terminal`

## Copy tone

Intel briefing, not SaaS marketing. Examples:

- "INTEL STREAM" not "Dashboard"
- "REQUEST ACCESS" not "Sign up"
- "CLEARANCE LEVEL 2 — PREMIUM" not "Pro plan"

Reference alert formatting in [`backend/alerts/slack_formatter.py`](../backend/alerts/slack_formatter.py).
