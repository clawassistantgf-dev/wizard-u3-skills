# SVG Banner Template for HermesDeck Lead Emails

Use this when FAL_KEY is not set and you need a lead image for prospecting emails.

## Key Visual Elements

- Background: dark (#0d1117) with subtle circuit-line decoration
- Accent colors: Bitcoin orange (#f7931a), tech blue (#58a6ff), green (#3fb950)
- Logo: Hermes caduceus staff (winged rod with two snakes)
- Fonts: Georgia for brand name, Segoe UI for tagline
- Badges: pill-shaped rects with icon dots + text

## SVG Structure

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 250">
  <defs>
    <!-- Gradients: bg (dark), accent (orange gradient), glow overlay -->
    <!-- Filter: shadow drop, neon glow -->
  </defs>
  <rect width="600" height="250" fill="url(#bg)" rx="12"/>
  <!-- Circuit lines: Q-curves with low opacity -->
  <!-- Decorative nodes: small circles -->
  <!-- Logo: staff rect + wing paths + snake paths + orb circle -->
  <!-- Brand text: Hermes + Deck (orange) -->
  <!-- Tagline -->
  <!-- Feature badges: 3x pill-shaped with icon dots -->
</svg>
```

## Attachment Code

```python
from email.mime.image import MIMEImage
with open("banner.svg", "rb") as f:
    svg_part = MIMEImage(f.read(), _subtype="svg+xml", name="banner.svg")
svg_part.add_header("Content-Disposition", "attachment; filename=banner.svg")
svg_part.add_header("Content-ID", "<hermesdeck-banner>")
msg.attach(svg_part)
```

Reference in HTML body as `<img src="cid:hermesdeck-banner" alt="HermesDeck">`.