# Animated GitHub profile dashboard — installation

This profile banner is a continuously looping animated GIF with **16 technical scenes** and a total loop duration of **89.6 seconds**. It covers automation control, branched visual workflows, VPS/system administration, backup and recovery, Git, CI/CD, REST APIs, reliable queues, AI agents, RAG, databases, observability, security, email automation, AI chatbot/human handoff, and CRM/M&A intelligence.

## Upload to `sadamulhaq/sadamulhaq`

Copy the updated `README.md` to the root of your GitHub profile repository and upload the GIF into the `assets` folder, creating that folder if needed:

```text
sadamulhaq/
├── README.md
└── assets/
    └── sadam-workflow.gif
```

The README references the local GIF with `./assets/sadam-workflow.gif`. Keep the file name and casing exact.

## Playback behavior

The GIF has **896 frames**, is **1200 × 430 px**, and stores an infinite loop (`loop=0`). GitHub normally plays animated GIFs automatically in README pages, without requiring the visitor to click. However, GitHub respects the viewer's reduced-motion preference and accessibility setting for animated images, so autoplay cannot be forced for every visitor.

## Regenerate or customize

`generate_sadam_workflow.py` is the editable Python source. Install Pillow (`python -m pip install Pillow`) and FFmpeg, then run:

```bash
python generate_sadam_workflow.py
```

The generator rebuilds the GIF, a static first-scene preview, and a 16-scene contact sheet. Scenes use eased progression, continuous telemetry movement, accent-colored transitions, and a seamless loop. All metrics and system activity shown are illustrative; the animation is not connected to live services or real server telemetry.
