# Implementation record

## 0.1.0

- Imported the native agents widget and its SVG assets from Omarchy 4.0.4 with the upstream MIT license.
- Added a Python standard-library Cursor collector. It reads desktop authentication without modifying it, fetches actual plan percentages and paginated token events, and emits the existing agent record format.
- Added an updater that calls Omarchy's installed collector runner and the Cursor collector using the same refresh flags and provider selection rules.
- Connected the existing QML refresh command to the bundled updater. The timer, panel-open behavior, manual refresh, rendering, keyboard interactions and stock collectors are unchanged.
- Declared a root plugin manifest with ID `darkosxl.agents-cursor` and `clonedFrom: omarchy.agents`, preserving native enable/disable restoration behavior.
- Added executable checks and installation, update, privacy and removal documentation.
- Corrected the headline allowance to use included spend / plan limit, matching Cursor's overall usage display; model-pool percentages remain separately labeled. Small nonzero Cursor percentages no longer round to zero.
- Cursor refreshes both limits and token history every time the existing panel-open refresh runs; other providers retain their stock limits-only behavior.

Runtime records and account credentials are outside the repository. `preview.png` is a reviewed capture of the agents panel only.

## Validation

Checked on 2026-10-01 with Omarchy 4.0.4-1.

- `python3 tests/check.py`, `omarchy plugin validate .`, and `bash -n bin/omarchy-agent-usage-update` pass. The checks cover percentage conversion, token totals, pagination, cache and failure handling, and refresh flag routing.
- After `omarchy-shell omarchy.agents refresh` and opening the panel, Cursor showed Included plan 99%, Auto pool 4%, and API pool 4%. The usage record behind that view was about 0.994, 0.0405, and 0.0369. No meter displayed 0%. Every live value was at least 1%, so the panel used ordinary rounding. Nonzero Cursor values below 1% still format as one decimal, or `<0.1%` when they are below a tenth of a percent, in `Panel.qml`.
- Opening the panel runs the bundled updater with `--limits-only`. Cursor still fetches limits and token history on that path; the other providers keep their stock limits-only behavior. A manual refresh (`omarchy-shell omarchy.agents refresh`) collects both as well.
- Removing the plugin restores the stock Omarchy agents widget. Installing again with `omarchy plugin add https://github.com/Darkosxl/omarchy-cursor-usage --enable` put the Cursor tab back in the same bar position. That copy's origin is the public repository, `omarchy plugin update darkosxl.agents-cursor` reported it up to date, and the panel showed Included plan 100%, Auto pool 5%, and API pool 4%, matching the fresh record (1.0, about 0.0537, and about 0.0369).
