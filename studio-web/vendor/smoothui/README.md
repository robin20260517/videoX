# SmoothUI provenance

Official registry sources retrieved on 2026-09-10 from:
- https://smoothui.dev/r/smooth-button.json
- https://smoothui.dev/r/animated-input.json
- https://smoothui.dev/r/animated-file-upload.json
- https://smoothui.dev/r/animated-tabs.json

Author: Eduardo Calvo. License: MIT, preserved in LICENSE (retrieved from https://raw.githubusercontent.com/educlopez/smoothui/main/LICENSE).

The adjacent JSON files preserve the unmodified registry payloads. Their actual source files are installed under src/components/smoothui/. Business adaptations: Chinese upload labels, password input support, studio theme overrides. Buttons, tabs, inputs and drag upload interactions all use these components. The registry's shared tokens were inspected; studio CSS overrides their neutral/brand colors with the user's mandated grey palette. No gradient variants are used. No simulated progress bar is used because the API has no numeric generation progress.
