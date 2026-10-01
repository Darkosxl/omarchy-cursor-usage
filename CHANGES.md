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

Runtime records and account credentials are outside the repository. Live screenshots are not committed because they may contain personal desktop content.

## Validation

Automated collector and updater checks and the Omarchy manifest validator pass. Live installation and removal verification is recorded here before release.
