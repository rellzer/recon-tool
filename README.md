# AI Recon Tool

A Gradio-based web interface for running passive and light-active reconnaissance against
authorized lab targets. Built with assistance from a local LLM (Qwen Coder via coyotegpt).

## Lab Targets Only
Use this tool only against systems you own or have explicit written authorization to test.
The default target is `scanme.nmap.org`, which Nmap publishes for educational scanning.

## Features
- DNS lookup (A, MX, NS, TXT)
- WHOIS lookup
- HTTP header inspection
- robots.txt / sitemap.xml / security.txt fetcher
- Ping sweep
- Light Nmap scan (top 100 ports + service detection)
- One-click "full recon" that runs all of the above

## Install
```bash
# In Kali (or any Linux with Python 3.10+)
sudo apt update
sudo apt install -y nmap whois dnsutils
pip install -r requirements.txt
```

## Run
```bash
python app.py
```
Then open the local URL Gradio prints (or use the public `.gradio.live` link
because the app launches with `share=True`).

## Notes
- Gradio's `share=True` makes the tool reachable by a temporary public URL —
  share it only with people you trust.
- Some functions need root for full output (e.g., Nmap SYN scans). The default
  here uses `-sV --top-ports 100`, which works without root.
