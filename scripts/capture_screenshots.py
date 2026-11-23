"""
scripts/capture_screenshots.py — Start backend (port 8080) + frontend and capture Phase 6A screenshots.
"""

import os
import sys
import time
import subprocess
import requests

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(ROOT_DIR, "docs", "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

print(f"Using browser binary: {CHROME_PATH}", flush=True)


def wait_for_url(url, timeout=45):
    start = time.time()
    while time.time() - start < timeout:
        try:
            res = requests.get(url, timeout=2)
            if res.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def capture(url, out_name, width=1280, height=900):
    out_path = os.path.join(SCREENSHOTS_DIR, out_name)
    if os.path.exists(out_path):
        os.remove(out_path)

    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--screenshot={out_path}",
        f"--window-size={width},{height}",
        "--hide-scrollbars",
        "--virtual-time-budget=6000",
        "--disable-gpu",
        "--no-sandbox",
        url,
    ]
    print(f"Capturing {out_name} ({width}x{height}) from {url}...", flush=True)
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    if os.path.exists(out_path):
        size_kb = os.path.getsize(out_path) / 1024
        print(f"  ✓ Saved {out_name} ({size_kb:.1f} KB)", flush=True)
    else:
        print(f"  ✗ Failed to save {out_name}", flush=True)


def main():
    py_exec = os.path.join(ROOT_DIR, "backend", "venv", "Scripts", "python.exe")
    backend_proc = None
    frontend_proc = None

    try:
        # 1. Start backend on port 8080 (port 8000 is WinNAT-reserved on this host)
        print("Starting backend uvicorn server on 127.0.0.1:8080...", flush=True)
        backend_cmd = [
            py_exec,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8080",
        ]
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=os.path.join(ROOT_DIR, "backend"),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        print("Waiting for backend warmup (SentenceTransformer + DB)...", flush=True)
        if not wait_for_url("http://127.0.0.1:8080/health", timeout=45):
            print("ERROR: Backend failed to respond on http://127.0.0.1:8080/health", flush=True)
            if backend_proc.poll() is not None:
                out, _ = backend_proc.communicate()
                print("Backend output:\n", out, flush=True)
            sys.exit(1)
        print("  ✓ Backend is online on port 8080 & warmed up!", flush=True)

        # 2. Seed demo dataset (AI/ML JD with 12 resumes)
        print("Seeding AI/ML demo dataset...", flush=True)
        seed_resp = requests.post(
            "http://127.0.0.1:8080/api/demo/seed?jd_key=aiml&reset=true",
            timeout=30,
        )
        if seed_resp.status_code == 200:
            demo_data = seed_resp.json()
            run_id = demo_data.get("run_id", 1)
            print(f"  ✓ Seeded demo run #{run_id}", flush=True)
        else:
            run_id = 1
            print(f"  Warning: demo seed returned {seed_resp.status_code}", flush=True)

        # 3. Start frontend preview on 127.0.0.1:5173
        print("Starting frontend preview server on 127.0.0.1:5173...", flush=True)
        vite_bin = os.path.join(ROOT_DIR, "frontend", "node_modules", "vite", "bin", "vite.js")
        frontend_cmd = [
            "node",
            vite_bin,
            "preview",
            "--host",
            "127.0.0.1",
            "--port",
            "5173",
        ]
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=os.path.join(ROOT_DIR, "frontend"),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        if not wait_for_url("http://127.0.0.1:5173", timeout=20):
            print("ERROR: Frontend preview failed to start on port 5173", flush=True)
            if frontend_proc.poll() is not None:
                out, _ = frontend_proc.communicate()
                print("Frontend output:\n", out, flush=True)
            sys.exit(1)
        print("  ✓ Frontend is online on 127.0.0.1:5173!", flush=True)

        # Find first candidate ID from results
        res = requests.get(f"http://127.0.0.1:8080/api/match/runs/{run_id}/results?limit=1")
        first_candidate_id = 1
        if res.status_code == 200:
            items = res.json().get("items", [])
            if items:
                first_candidate_id = items[0]["candidate_id"]

        time.sleep(2)

        # 4. Capture screenshots
        # A. Home desktop (1280px)
        capture("http://127.0.0.1:5173/", "home_desktop.png", 1280, 950)

        # B. Dashboard desktop (1280px)
        capture(f"http://127.0.0.1:5173/dashboard?run={run_id}", "dashboard_desktop.png", 1280, 950)

        # C. Dashboard mobile (375px)
        capture(f"http://127.0.0.1:5173/dashboard?run={run_id}", "dashboard_mobile_375px.png", 375, 812)

        # D. Candidate detail desktop (1280px)
        capture(
            f"http://127.0.0.1:5173/candidate/{first_candidate_id}?run={run_id}",
            "candidate_detail_desktop.png",
            1280,
            1050,
        )

        print("\nAll Phase 6A screenshots captured successfully!", flush=True)

    finally:
        if frontend_proc:
            print("Shutting down frontend server...", flush=True)
            frontend_proc.terminate()
        if backend_proc:
            print("Shutting down backend server...", flush=True)
            backend_proc.terminate()


if __name__ == "__main__":
    main()
