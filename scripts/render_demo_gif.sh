#!/usr/bin/env bash
set -euo pipefail

output="${1:-demo/60-second-demo.gif}"
font="${DEMO_FONT:-}"

if [[ -z "$font" ]]; then
  for candidate in \
    /System/Library/Fonts/Supplemental/Arial.ttf \
    /System/Library/Fonts/Helvetica.ttc \
    /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf; do
    if [[ -f "$candidate" ]]; then
      font="$candidate"
      break
    fi
  done
fi

if [[ -z "$font" ]]; then
  echo "No usable font found. Set DEMO_FONT=/path/to/font.ttf." >&2
  exit 1
fi

if command -v magick >/dev/null 2>&1; then
  imagemagick=(magick)
elif command -v convert >/dev/null 2>&1; then
  imagemagick=(convert)
else
  echo "ImageMagick is required to render demo/60-second-demo.gif." >&2
  exit 1
fi

"${imagemagick[@]}" -delay 120 -loop 0 \
  \( -size 960x540 xc:"#f7f7f4" -fill "#ffffff" -stroke "#c9d2d9" -draw "roundrectangle 40,44 920,496 8,8" -font "$font" -stroke none -fill "#172026" -pointsize 44 -annotate +80+150 "Agent Context Health" -pointsize 28 -fill "#33454f" -annotate +80+210 "Evaluate AI-facing context before agent execution" -pointsize 24 -fill "#0f766e" -annotate +80+320 "60-second demo fixture" -pointsize 20 -fill "#5a6872" -annotate +80+370 "Not a security guarantee or benchmark claim" \) \
  \( -size 960x540 xc:"#eef3f2" -font "$font" -fill "#172026" -pointsize 34 -annotate +60+76 "Before: bad context enters the handoff" -fill "#ffffff" -stroke "#c9d2d9" -draw "roundrectangle 60,116 480,446 8,8" -draw "roundrectangle 520,116 900,446 8,8" -stroke none -fill "#172026" -pointsize 22 -annotate +86+166 "README" -fill "#b42318" -pointsize 19 -annotate +86+214 "release v9.9.9 is public" -annotate +86+258 "all tests passed" -fill "#172026" -pointsize 22 -annotate +546+166 "AGENTS.md" -fill "#b42318" -pointsize 19 -annotate +546+214 "Publish after any local run" -annotate +546+258 "Push without approval" \) \
  \( -size 960x540 xc:"#f9fbfb" -font "$font" -fill "#172026" -pointsize 34 -annotate +60+76 "Evidence contradicts the handoff" -fill "#ffffff" -stroke "#c9d2d9" -draw "roundrectangle 70,126 930,236 8,8" -draw "roundrectangle 70,272 930,382 8,8" -stroke none -fill "#b42318" -pointsize 24 -annotate +100+176 "release-check.md: 404 Not Found" -annotate +100+322 "terminal.log: FAILED tests after handoff says passed" -fill "#0f766e" -pointsize 22 -annotate +100+430 "The next agent should see this before acting." \) \
  \( -size 960x540 xc:"#f7f7f4" -font "$font" -fill "#172026" -pointsize 34 -annotate +60+76 "After: report highlights findings" -fill "#ffffff" -stroke "#c9d2d9" -draw "roundrectangle 60,112 920,184 8,8" -draw "roundrectangle 60,200 920,272 8,8" -draw "roundrectangle 60,288 920,360 8,8" -draw "roundrectangle 60,376 920,448 8,8" -stroke none -fill "#172026" -pointsize 22 -annotate +90+158 "unsupported_release_claim - release v9.9.9 is public" -annotate +90+246 "conflicting_policy - incompatible release rules" -annotate +90+334 "hidden_terminal_failure - FAILED tests" -annotate +90+422 "Memory X-Ray L1 - source, rollback, consequence, state gaps" \) \
  \( -size 960x540 xc:"#eef3f2" -font "$font" -fill "#172026" -pointsize 34 -annotate +60+76 "Claim boundaries stay visible" -fill "#ffffff" -stroke "#c9d2d9" -draw "roundrectangle 80,130 880,415 8,8" -stroke none -fill "#172026" -pointsize 24 -annotate +120+190 "Demo fixture only" -annotate +120+242 "No universal benchmark claim" -annotate +120+294 "No security guarantee" -annotate +120+346 "No provider compatibility statement" \) \
  \( -size 960x540 xc:"#f9fbfb" -font "$font" -fill "#172026" -pointsize 34 -annotate +60+76 "Ready for release-facing review" -fill "#ffffff" -stroke "#c9d2d9" -draw "roundrectangle 70,130 930,410 8,8" -stroke none -fill "#0f766e" -pointsize 24 -annotate +110+190 "LLM judge harness: offline by default" -annotate +110+244 "Independent review packet: labels withheld" -annotate +110+298 "Demo report fixture: reproducible" -annotate +110+352 "Doctor low score becomes product backlog" \) \
  "$output"
