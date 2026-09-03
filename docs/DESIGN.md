# AI Retail Shelf Intelligence · Design System

## Status

**Day 1 foundation · design direction selected**

## Product Personality

AI-powered retail intelligence should feel precise, visual, operational, and trustworthy. The interface should communicate computer-vision results quickly without becoming a generic enterprise dashboard.

## Primary Visual Direction

**Futuristic / Sci-Fi UI**

## Supporting Direction

**Dashboard / Data-Heavy UI**

This deliberately differs from JobTrack's Brutalist/Neo-Brutalist identity.

## Why This Fits

Shelf intelligence is fundamentally a visual-analysis workflow. A futuristic visual language supports the idea of machine vision, detection overlays, processing states, spatial analysis, and live intelligence. The data-heavy layer keeps the experience practical for retail users who need counts, confidence, shelf status, and historical observations.

## Design Principles

1. **Vision first** · uploaded shelf imagery and detection results are the visual center of the product.
2. **Evidence over decoration** · overlays and annotations should explain detected objects and shelf regions.
3. **Fast scanning** · counts, confidence, status, and alerts should be readable at a glance.
4. **Technical but approachable** · futuristic elements should support comprehension rather than imitate a movie HUD.
5. **Responsive by design** · analysis results must remain usable on desktop and mobile widths.
6. **Clear system states** · upload, processing, success, partial detection, empty result, and failure states must be explicit.

## Typography Direction

- Strong geometric/display face for major product headings.
- Highly readable sans-serif for interface content.
- Monospace treatment for technical metadata such as detection confidence, processing states, timestamps, and model information.

Final font choices will be made from available/open-source options during implementation.

## Color Direction

Use a dark technical base with controlled luminous accents for detection states and data visualization. The final palette must maintain accessible text contrast and should not rely on color alone to communicate status.

Suggested semantic roles:

- Base: deep technical surface
- Primary text: high-contrast light
- Detection: luminous accent
- Success/available: distinct positive accent
- Warning/low-stock: high-visibility warning accent
- Error: explicit error accent
- Neutral analytics: restrained supporting tones

Exact colors will be finalized in the frontend implementation.

## Layout

Use a modular analysis workspace:

```text
┌──────────────────────────────────────────────────────────┐
│ Navigation / System Status                               │
├───────────────────────────────┬──────────────────────────┤
│ Shelf Image / Detection View  │ Analysis Summary         │
│                               │ Counts / Confidence      │
│                               │ Shelf Status             │
├───────────────────────────────┴──────────────────────────┤
│ History / Analytics / Shelf Observations                 │
└──────────────────────────────────────────────────────────┘
```

On smaller screens, convert the workspace into a logical vertical flow rather than shrinking the desktop canvas.

## Component Language

- Precision cards with subtle depth
- Technical labels
- Detection bounding boxes
- Image overlays
- Status indicators
- Metric tiles
- Timeline/history rows
- Filter controls
- Processing indicators
- Empty and error states

Avoid copying JobTrack's thick black borders, offset shadows, neon brutalist cards, or editorial composition as the dominant language.

## Motion

Use restrained motion for:

- Upload progress
- Image processing state
- Detection reveal
- Filter transitions
- Dashboard metric updates

Motion must never block core interaction or make the product feel like a game.

## Accessibility

- Keyboard-accessible controls
- Visible focus states
- Sufficient contrast
- Semantic headings and landmarks
- Text alternatives for meaningful images
- Status communicated with text/icons in addition to color
- Reduced-motion support where practical

## Decoration Rules

Decorative grids, scanning lines, data markers, and technical motifs may reinforce the computer-vision theme, but must remain behind or outside critical content. No decorative layer should interfere with touch targets, text, or image annotations.
