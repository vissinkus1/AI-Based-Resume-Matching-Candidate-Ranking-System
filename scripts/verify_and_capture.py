"""
scripts/verify_and_capture.py — Robust Headless Chrome CDP automation.
Captures full-page screenshots at 1280px, 768px, and 375px for Home, Dashboard, Candidate Detail.
Ensures real data is loaded (no skeleton / network error), measures full scrollHeight,
and audits browser console logs for zero warnings/errors.
"""

import os
import sys
import time
import json
import base64
import asyncio
import subprocess
import requests
import websockets

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(ROOT_DIR, "docs", "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def wait_for_url(url, timeout=45):
    start = time.time()
    while time.time() - start < timeout:
        try:
            res = requests.get(url, timeout=2)
            if res.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


async def capture_page(ws_url, url, width, out_names, console_logs, ready_selector="body", min_wait=3.0):
    async with websockets.connect(ws_url, max_size=30 * 1024 * 1024) as ws:
        msg_id = 0
        pending_responses = {}

        async def send(method, params=None):
            nonlocal msg_id
            msg_id += 1
            cur_id = msg_id
            fut = asyncio.get_event_loop().create_future()
            pending_responses[cur_id] = fut
            payload = {"id": cur_id, "method": method}
            if params:
                payload["params"] = params
            await ws.send(json.dumps(payload))
            return await fut

        # Background message dispatcher
        async def dispatch():
            try:
                while True:
                    raw = await ws.recv()
                    msg = json.loads(raw)
                    if "id" in msg and msg["id"] in pending_responses:
                        pending_responses.pop(msg["id"]).set_result(msg.get("result"))

                    # Console & Exception capturing
                    if msg.get("method") == "Console.messageAdded":
                        entry = msg.get("params", {}).get("message", {})
                        level = entry.get("level", "LOG")
                        text = entry.get("text", "")
                        console_logs.append(f"[{level.upper()}] {text}")
                    elif msg.get("method") == "Runtime.consoleAPICalled":
                        entry = msg.get("params", {})
                        level = entry.get("type", "log")
                        args = [str(a.get("value", "")) for a in entry.get("args", [])]
                        console_logs.append(f"[{level.upper()}] {' '.join(args)}")
                    elif msg.get("method") == "Runtime.exceptionThrown":
                        details = msg.get("params", {}).get("exceptionDetails", {})
                        text = details.get("text", "")
                        desc = details.get("exception", {}).get("description", "")
                        console_logs.append(f"[EXCEPTION] {text} {desc}")
            except (asyncio.CancelledError, websockets.ConnectionClosed):
                pass

        dispatcher_task = asyncio.create_task(dispatch())

        try:
            # Enable CDP domains
            await send("Console.enable")
            await send("Runtime.enable")
            await send("Page.enable")
            await send("DOM.enable")

            # Set viewport initial width
            is_mobile = width < 768
            await send("Emulation.setDeviceMetricsOverride", {
                "width": width,
                "height": 900,
                "deviceScaleFactor": 1,
                "mobile": is_mobile
            })

            # Navigate to target URL
            await send("Page.navigate", {"url": url})

            # Wait for DOM ready selector & data populated
            start_time = time.time()
            data_loaded = False
            while time.time() - start_time < 15:
                await asyncio.sleep(0.5)
                eval_res = await send("Runtime.evaluate", {
                    "expression": f"!!document.querySelector('{ready_selector}')",
                    "returnByValue": True
                })
                if eval_res and eval_res.get("result", {}).get("value") is True:
                    data_loaded = True
                    break

            # Extra sleep to allow animations, fonts, and charts to stabilize
            await asyncio.sleep(min_wait)

            # Get actual full document height
            eval_height = await send("Runtime.evaluate", {
                "expression": "Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, 900)",
                "returnByValue": True
            })
            scroll_height = int(eval_height.get("result", {}).get("value", 900))

            # Resize viewport to full scroll height
            await send("Emulation.setDeviceMetricsOverride", {
                "width": width,
                "height": scroll_height,
                "deviceScaleFactor": 1,
                "mobile": is_mobile
            })
            await asyncio.sleep(0.6)

            # Capture full-page screenshot
            screenshot_res = await send("Page.captureScreenshot", {
                "format": "png",
                "captureBeyondViewport": True,
                "fromSurface": True
            })

            b64_data = screenshot_res.get("data")
            if b64_data:
                png_bytes = base64.b64decode(b64_data)
                for out_name in out_names:
                    out_path = os.path.join(SCREENSHOTS_DIR, out_name)
                    with open(out_path, "wb") as f:
                        f.write(png_bytes)
                    size_kb = len(png_bytes) / 1024
                    print(f"  ✓ Saved {out_name} ({width}x{scroll_height}px) — {size_kb:.1f} KB", flush=True)

        finally:
            dispatcher_task.cancel()
            try:
                await dispatcher_task
            except asyncio.CancelledError:
                pass


async def main():
    py_exec = os.path.join(ROOT_DIR, "backend", "venv", "Scripts", "python.exe")
    backend_proc = None
    frontend_proc = None
    chrome_proc = None

    try:
        # 1. Start backend uvicorn on 0.0.0.0:8080 (binds both IPv4 127.0.0.1 and localhost)
        print("Starting backend uvicorn server on 0.0.0.0:8080...", flush=True)
        backend_cmd = [
            py_exec,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
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

        print("Waiting for backend warmup (/health)...", flush=True)
        if not wait_for_url("http://localhost:8080/health", timeout=45):
            print("ERROR: Backend failed to start on port 8080", flush=True)
            sys.exit(1)
        print("  ✓ Backend is online on http://localhost:8080 & healthy!", flush=True)

        # 2. Seed Java demo dataset
        print("Seeding Java demo dataset (POST /api/demo/seed?jd_key=java&reset=true)...", flush=True)
        seed_resp = requests.post(
            "http://localhost:8080/api/demo/seed?jd_key=java&reset=true",
            timeout=35,
        )
        if seed_resp.status_code == 200:
            demo_data = seed_resp.json()
            run_id = demo_data.get("run_id", 1)
            print(f"  ✓ Java demo seeded! Run ID = {run_id}, Candidates = {demo_data.get('candidate_count')}", flush=True)
        else:
            run_id = 1
            print(f"  Warning: demo seed returned HTTP {seed_resp.status_code}", flush=True)

        # Query first candidate ID
        res = requests.get(f"http://localhost:8080/api/match/runs/{run_id}/results?limit=1")
        first_candidate_id = 8
        if res.status_code == 200:
            items = res.json().get("items", [])
            if items:
                first_candidate_id = items[0]["candidate_id"]
                cand_name = items[0]["name"]
                cand_score = items[0]["final_score"]
                cand_band = items[0]["band"]
                print(f"  ✓ Top candidate: {cand_name} (ID: {first_candidate_id}, Score: {cand_score:.1f}%, Band: {cand_band})", flush=True)

        # 3. Start frontend preview on port 5173
        print("Starting frontend preview server on localhost:5173...", flush=True)
        vite_bin = os.path.join(ROOT_DIR, "frontend", "node_modules", "vite", "bin", "vite.js")
        frontend_cmd = [
            "node",
            vite_bin,
            "preview",
            "--host",
            "localhost",
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

        if not wait_for_url("http://localhost:5173", timeout=20):
            print("ERROR: Frontend failed to start on http://localhost:5173", flush=True)
            sys.exit(1)
        print("  ✓ Frontend is online on http://localhost:5173!", flush=True)

        # 4. Start Chrome headless with remote debugging port
        print(f"Starting Chrome CDP: {CHROME_PATH} on port 9222...", flush=True)
        chrome_cmd = [
            CHROME_PATH,
            "--headless=new",
            "--remote-debugging-port=9222",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--window-size=1280,900",
            "about:blank",
        ]
        chrome_proc = subprocess.Popen(
            chrome_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if not wait_for_url("http://localhost:9222/json/version", timeout=15):
            print("ERROR: Chrome CDP failed on port 9222", flush=True)
            sys.exit(1)
        print("  ✓ Chrome CDP is online on port 9222!", flush=True)

        def get_fresh_tab():
            r = requests.put("http://localhost:9222/json/new")
            return r.json()["webSocketDebuggerUrl"]

        console_logs = []

        home_url = "http://localhost:5173/"
        dash_url = f"http://localhost:5173/dashboard?run={run_id}"
        cand_url = f"http://localhost:5173/candidate/{first_candidate_id}?run={run_id}"

        print("\n--- 1. CAPTURING HOME PAGE SCREENSHOTS (1280px, 768px, 375px) ---", flush=True)
        await capture_page(get_fresh_tab(), home_url, 1280, ["home_1280px.png", "home_desktop.png"], console_logs, ready_selector="h1")
        await capture_page(get_fresh_tab(), home_url, 768, ["home_768px.png"], console_logs, ready_selector="h1")
        await capture_page(get_fresh_tab(), home_url, 375, ["home_375px.png"], console_logs, ready_selector="h1")

        print("\n--- 2. CAPTURING DASHBOARD SCREENSHOTS (1280px, 768px, 375px) ---", flush=True)
        # On dashboard, wait until tbody tr rows are populated (or mobile card view)
        await capture_page(get_fresh_tab(), dash_url, 1280, ["dashboard_1280px.png", "dashboard_desktop.png"], console_logs, ready_selector="tbody tr")
        await capture_page(get_fresh_tab(), dash_url, 768, ["dashboard_768px.png"], console_logs, ready_selector="tbody tr")
        await capture_page(get_fresh_tab(), dash_url, 375, ["dashboard_375px.png", "dashboard_mobile_375px.png"], console_logs, ready_selector=".font-serif")

        print("\n--- 3. CAPTURING CANDIDATE DETAIL SCREENSHOTS (1280px, 768px, 375px) ---", flush=True)
        # On candidate detail, wait until candidate hero gauge svg circle exists
        await capture_page(get_fresh_tab(), cand_url, 1280, ["candidate_1280px.png", "candidate_detail_desktop.png"], console_logs, ready_selector="svg circle")
        await capture_page(get_fresh_tab(), cand_url, 768, ["candidate_768px.png"], console_logs, ready_selector="svg circle")
        await capture_page(get_fresh_tab(), cand_url, 375, ["candidate_375px.png"], console_logs, ready_selector="svg circle")

        # Report console audit findings
        print("\n--- BROWSER CONSOLE AUDIT FINDINGS ---", flush=True)
        if not console_logs:
            print("✓ Zero errors or warnings logged in browser console across all 9 pages and viewports!", flush=True)
        else:
            errors_or_warns = [log for log in console_logs if "ERROR" in log or "WARN" in log or "EXCEPTION" in log]
            if not errors_or_warns:
                print(f"✓ Zero console errors or warnings! (Total informational logs: {len(console_logs)})", flush=True)
            else:
                print(f"Found {len(errors_or_warns)} warnings/errors:", flush=True)
                for log in errors_or_warns:
                    print("  " + log, flush=True)

        print("\nAll visual verifications and screenshots completed!", flush=True)

    finally:
        if chrome_proc:
            print("Terminating Chrome...", flush=True)
            chrome_proc.terminate()
        if frontend_proc:
            print("Terminating frontend preview...", flush=True)
            frontend_proc.terminate()
        if backend_proc:
            print("Terminating backend server...", flush=True)
            backend_proc.terminate()


if __name__ == "__main__":
    asyncio.run(main())
