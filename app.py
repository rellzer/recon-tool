"""
AI-Assisted Reconnaissance Web Interface
Lab targets only. Do not use against systems you do not own or have explicit
written authorization to test.
"""

import socket
import subprocess
import shutil
import gradio as gr
import requests
from urllib.parse import urlparse


# -------- Helpers --------

def _run(cmd, timeout=30):
    """Run a shell command safely and return its combined output."""
    try:
        result = subprocess.run(
            cmd,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (result.stdout or "") + (result.stderr or "")
    except subprocess.TimeoutExpired:
        return f"[!] Command timed out after {timeout}s"
    except FileNotFoundError:
        return f"[!] Tool not installed: {cmd[0]}"
    except Exception as e:
        return f"[!] Error: {e}"


def _normalize_target(target):
    """Strip scheme and path so we get a bare host."""
    target = target.strip()
    if "://" in target:
        target = urlparse(target).netloc or urlparse(target).path
    return target.split("/")[0]


# -------- Recon Functions --------

def whois_lookup(target):
    target = _normalize_target(target)
    if not target:
        return "[!] No target provided"
    if not shutil.which("whois"):
        return "[!] whois not installed (sudo apt install whois)"
    return _run(["whois", target], timeout=20)


def dns_lookup(target):
    target = _normalize_target(target)
    if not target:
        return "[!] No target provided"
    out = []
    try:
        out.append(f"A record:    {socket.gethostbyname(target)}")
    except Exception as e:
        out.append(f"A record:    error - {e}")

    if shutil.which("dig"):
        out.append("\n--- dig ANY ---")
        out.append(_run(["dig", "+noall", "+answer", "ANY", target]))
        out.append("\n--- dig MX ---")
        out.append(_run(["dig", "+short", "MX", target]))
        out.append("\n--- dig NS ---")
        out.append(_run(["dig", "+short", "NS", target]))
        out.append("\n--- dig TXT ---")
        out.append(_run(["dig", "+short", "TXT", target]))
    else:
        out.append("[!] dig not installed (sudo apt install dnsutils)")
    return "\n".join(out)


def http_headers(target):
    target = target.strip()
    if not target:
        return "[!] No target provided"
    if not target.startswith(("http://", "https://")):
        target = "http://" + target
    try:
        r = requests.get(target, timeout=10, allow_redirects=True)
        lines = [f"Status: {r.status_code}", f"Final URL: {r.url}", ""]
        for k, v in r.headers.items():
            lines.append(f"{k}: {v}")
        return "\n".join(lines)
    except Exception as e:
        return f"[!] Error: {e}"


def ping_sweep(target):
    target = _normalize_target(target)
    if not target:
        return "[!] No target provided"
    return _run(["ping", "-c", "4", target], timeout=15)


def nmap_quick(target):
    target = _normalize_target(target)
    if not target:
        return "[!] No target provided"
    if not shutil.which("nmap"):
        return "[!] nmap not installed (sudo apt install nmap)"
    # Light scan - top 100 ports, service detection
    return _run(["nmap", "-sV", "--top-ports", "100", target], timeout=120)


def robots_check(target):
    target = target.strip()
    if not target:
        return "[!] No target provided"
    if not target.startswith(("http://", "https://")):
        target = "http://" + target
    if not target.endswith("/"):
        target += "/"
    out = []
    for path in ["robots.txt", "sitemap.xml", ".well-known/security.txt"]:
        try:
            r = requests.get(target + path, timeout=8)
            out.append(f"=== /{path} ({r.status_code}) ===")
            out.append(r.text[:2000] if r.status_code == 200 else "(not found)")
            out.append("")
        except Exception as e:
            out.append(f"=== /{path} ===\n[!] {e}\n")
    return "\n".join(out)


def full_recon(target):
    """Run everything in sequence."""
    sections = [
        ("DNS", dns_lookup(target)),
        ("HTTP HEADERS", http_headers(target)),
        ("ROBOTS / SITEMAP", robots_check(target)),
        ("NMAP (top 100)", nmap_quick(target)),
    ]
    return "\n\n".join(f"========== {name} ==========\n{content}" for name, content in sections)


# -------- Gradio UI --------

with gr.Blocks(title="AI Recon Tool", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # AI-Assisted Reconnaissance Tool
        Authorized lab targets only. Use only on systems you own or have written
        permission to test. Default lab target prefilled below.
        """
    )

    with gr.Row():
        target_input = gr.Textbox(
            label="Target (host, IP, or URL)",
            value="scanme.nmap.org",
            scale=3,
        )

    with gr.Tab("Quick Recon (run all)"):
        btn_full = gr.Button("Run Full Recon", variant="primary")
        out_full = gr.Textbox(label="Output", lines=25)
        btn_full.click(full_recon, inputs=target_input, outputs=out_full)

    with gr.Tab("DNS"):
        btn_dns = gr.Button("DNS Lookup")
        out_dns = gr.Textbox(label="Output", lines=15)
        btn_dns.click(dns_lookup, inputs=target_input, outputs=out_dns)

    with gr.Tab("WHOIS"):
        btn_whois = gr.Button("WHOIS Lookup")
        out_whois = gr.Textbox(label="Output", lines=20)
        btn_whois.click(whois_lookup, inputs=target_input, outputs=out_whois)

    with gr.Tab("HTTP Headers"):
        btn_http = gr.Button("Fetch HTTP Headers")
        out_http = gr.Textbox(label="Output", lines=15)
        btn_http.click(http_headers, inputs=target_input, outputs=out_http)

    with gr.Tab("Robots / Sitemap"):
        btn_robots = gr.Button("Check robots.txt and sitemap.xml")
        out_robots = gr.Textbox(label="Output", lines=15)
        btn_robots.click(robots_check, inputs=target_input, outputs=out_robots)

    with gr.Tab("Ping"):
        btn_ping = gr.Button("Ping (4 packets)")
        out_ping = gr.Textbox(label="Output", lines=10)
        btn_ping.click(ping_sweep, inputs=target_input, outputs=out_ping)

    with gr.Tab("Nmap (light)"):
        btn_nmap = gr.Button("Nmap top 100 ports + service detection")
        out_nmap = gr.Textbox(label="Output", lines=20)
        btn_nmap.click(nmap_quick, inputs=target_input, outputs=out_nmap)

    gr.Markdown(
        """
        ---
        **Built with local AI assistance (Qwen Coder via coyotegpt).**
        Authorized testing only.
        """
    )


if __name__ == "__main__":
    demo.launch(share=True)
