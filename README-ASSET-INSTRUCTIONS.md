# GitHub profile animation cache refresh

This package uses a versioned asset filename to prevent GitHub's image/CDN cache from continuing to display an older GIF at the previous path.

## Upload these files

- Replace the profile repository's `README.md` with this package's `README.md`.
- Upload `assets/sadam-workflow-v2.gif` into the `assets/` directory.

The README references `./assets/sadam-workflow-v2.gif` (not the old `sadam-workflow.gif`). This new path forces GitHub to request a new image rather than reusing a cached response for the previous filename.

## Recommended cleanup

After confirming the profile displays the new full-width animation, delete the old `assets/sadam-workflow.gif` from the repository to avoid confusion. Keep the new v2 file.

## Expected structure

```text
sad amulhaq/
├── README.md
└── assets/
    └── sadam-workflow-v2.gif
```

The animation is an illustrative simulation, not a live connection to production services. GIF autoplay and looping work automatically in normal GitHub README rendering, subject to viewer accessibility/reduced-motion preferences.
