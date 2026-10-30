# Animated profile dashboard — installation

This profile banner is an animated GIF with 14 looping scenes: automation control plane; VPS/system administration; backup and disaster recovery; development and Git; CI/CD; REST APIs and webhooks; reliable queues and retries; AI agents; RAG/document intelligence; databases and data engineering; observability; security/governance; email automation; and CRM/M&A intelligence.

## Upload to `sadamulhaq/sadamulhaq`

Copy the updated `README.md` to the root of your GitHub profile repository and upload the GIF into the `assets` folder, creating that folder if needed:

```text
sadamulhaq/
├── README.md
└── assets/
    └── sadam-workflow.gif
```

The README already references it using this relative path:

```html
<img src="./assets/sadam-workflow.gif" alt="Animated systems dashboard: workflow automation, system administration, AI agents, databases, REST APIs, email automation, orchestration, observability, coding and deployment, and chatbot handoff" width="100%" />
```

## Animation details

- Dimensions: 1200 × 430 px
- Loop: about 42.1 seconds
- Format: animated GIF, suitable for a GitHub README
- Content: 14 differentiated technical workspaces with eased transitions, moving workflow signals, branching paths, host telemetry, backup verification, Git review, CI/CD release gates, REST request/response, queue retries and dead-letter recovery, AI tool routing, RAG retrieval, database ingestion, observability and incident response, security policy checks, email sequences, and CRM/M&A scoring

## Regenerate or customize

`generate_sadam_workflow.py` is the editable Python source. Install Pillow with `python -m pip install Pillow`, then run. FFmpeg is optional but recommended for compact GIF encoding; when available, the script uses it to keep the full-resolution animation small:

```bash
python generate_sadam_workflow.py
```

It regenerates `assets/sadam-workflow.gif`, a preview image, and an animation contact sheet. All activity shown is a visual simulation; it is not connected to live infrastructure or services. The GIF is 1200 × 430 pixels, loops continuously, and is optimized to approximately 1.6 MiB for practical README loading.
