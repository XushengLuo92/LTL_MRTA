# Project website

Live site: https://xushengluo92.github.io/LTL_MRTA/

GitHub Pages serves the repository root from `codex/demo-visual-refresh`. `.nojekyll` keeps it a plain static site. Push changes to that branch to publish.

- `index.html`: layout, introduction, and first-demo fallback.
- `site/demos.js`: selectable demo descriptions and media paths.
- `site/app.js`: accessible demo selection and query-string links (`?demo=2`).
- `site/style.css`: responsive layout.
- `demo/generated/`: existing video and replay assets, shared with the README.

Preview from the repository root with `python3 -m http.server 8000`, then open `http://localhost:8000`. No Node, build step, or external CDN is required. When replacing a video, refresh its poster as well.

Regenerate the two workspace maps with `python scripts/export_workspace_maps.py` in the `ltl_mrta` environment. The exporter verifies that Cases 1–8 and Cases 9–10 respectively share a layout and uses the demo renderer to draw regions and obstacles.
