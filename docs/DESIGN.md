# AI Retail Shelf Intelligence · Design System

## Status

**Day 1 foundation · implementation established**

## Product Personality

Precise, visual, operational and trustworthy. The interface should communicate computer-vision evidence quickly without becoming a generic enterprise dashboard or a movie-style HUD.

## Primary Visual Direction

**Futuristic / Sci-Fi UI**

## Supporting Direction

**Dashboard / Data-Heavy UI**

This deliberately differs from JobTrack's Brutalist/Neo-Brutalist identity.

## Why This Fits

Shelf intelligence is a visual-analysis workflow. A controlled futuristic language supports image overlays, processing states, spatial detection and model telemetry. The dashboard layer keeps the product useful for retail users who need counts, confidence and shelf status at a glance.

## Typography

- **Space Grotesk** · product headings and high-level metrics.
- **DM Sans** · readable interface content and explanatory copy.
- **Space Mono** · technical labels, statuses, timestamps and model metadata.

The implementation loads these open-source font families through CSS. A production deployment can self-host them later if external font loading is undesirable.

## Color System

Semantic tokens used by the Day 1 shell:

| Token | Value | Role |
|---|---|---|
| Technical base | `#080B10` | Application background |
| Surface | `#10151D` | Primary panels |
| Secondary surface | `#151C26` | Elevated panels |
| Line | `#2B3543` | Borders/dividers |
| Primary text | `#EDF3F7` | Main readable content |
| Muted text | `#8F9BAA` | Supporting content |
| Detection cyan | `#45E6FF` | Active vision/analysis signal |
| Available lime | `#B8FF4A` | Positive/system state |
| Warning orange | `#FFB454` | Future low-stock warning role |
| Error pink | `#FF6B8B` | Error role |
| Violet | `#9D7CFF` | Secondary analytics accent |

Color is never intended to be the sole carrier of status. Labels and text accompany semantic states.

## Layout

The primary workspace is modular:

```text
┌──────────────────────────────────────────────────────────────┐
│ Brand · Navigation · System status                          │
├──────────────────────────────────┬───────────────────────────┤
│ Shelf image / analysis workspace │ Metrics / pipeline state  │
├──────────────────────────────────┴───────────────────────────┤
│ History / analytics / observations                          │
└──────────────────────────────────────────────────────────────┘
```

On smaller screens, the workspace becomes a vertical flow. It is not a shrunken desktop canvas.

## Component Language

- Precision cards with restrained depth
- Technical labels and metadata
- Detection bounding-box language for future inference results
- Image-analysis surfaces
- Status indicators
- Metric tiles
- Pipeline steps
- Timeline/history rows
- Clear empty/error states

Avoid thick black borders, offset shadows, neon brutalist cards and editorial compositions from JobTrack.

## Motion

Use restrained motion for upload progress, processing, detection reveal and data updates. Respect `prefers-reduced-motion` and never make animation necessary for understanding or interaction.

## Accessibility

- Semantic headings and landmarks
- Keyboard-accessible navigation and controls
- Visible focus states
- High-contrast text
- Text/icon labels in addition to color
- Meaningful alternative text for images
- Reduced-motion support

## Decoration Rules

Grid textures, scan lines and technical markers can reinforce the vision theme, but remain behind or outside critical content. Decorative layers must never interfere with text, image evidence or touch targets.
