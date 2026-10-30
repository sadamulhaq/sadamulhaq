# Animated GitHub profile workflow banner — installation

This version uses the full 1200 × 430 canvas for technical workflow animations. It contains no personal identity sidebar. The scene cards include concise technical annotations, and luminous packets travel along the exact straight and orthogonal connector paths between workflow nodes.

## Animation coverage

The 16 scenes cover automation control, visual workflow orchestration, VPS/system administration, backup and disaster recovery, development/Git, CI/CD, REST APIs/webhooks, queues and reliable execution, AI agents, RAG/document intelligence, databases/data engineering, observability/incident response, security/governance, email/business automation, AI chatbot/human handoff, and CRM/M&A intelligence.

## Upload to `sadamulhaq/sadamulhaq`

Copy `README.md` to the root of your GitHub profile repository and upload the GIF into `assets`: 

```text
sadamulhaq/
├── README.md
└── assets/
    └── sadam-workflow.gif
```

The README references `./assets/sadam-workflow.gif`. Keep the filename and casing exact. The old `sadam-dashboard.svg` is not used by this README.

## Playback and validation

- Canvas: **1200 × 430 px**
- Frames: **864**
- Frame cadence: **approximately 12 fps**
- Loop duration: **71.71 seconds**
- File size: see the included GIF (approximately 2.3 MiB)
- GIF loop metadata: **infinite** (`loop=0`)
- Seam check: first and last frames are pixel-identical

GitHub normally plays animated GIFs automatically in README pages without a click. A viewer's browser, operating-system, or reduced-motion preferences may suppress animation; autoplay cannot be forced for every visitor.

## Regenerate or customize

`generate_sadam_workflow.py` is the editable Python source. Install Pillow and FFmpeg, then run:

```bash
python -m pip install Pillow
python generate_sadam_workflow.py
```

The generator rebuilds the GIF, a static scene preview, and the 16-scene contact sheet. Activity, metrics, and server states are illustrative simulations, not live connections to production systems.
