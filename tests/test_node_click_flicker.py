"""
Test: clicking a node must not cause opacity flicker.

Records the computed opacity of an unrelated node on every animation frame
for 1 second after a click. If opacity goes 1 → <1 → 1 → <1 (non-monotonic
decrease), that's a flicker.
"""
import time
import json
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType


BASE_URL = "http://localhost:80"


@pytest.fixture(scope="module")
def driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1400,900")
    # Use Yandex Browser (Chromium-based, version 144)
    opts.binary_location = "/Applications/Yandex.app/Contents/MacOS/Yandex"

    svc = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM, driver_version="144.0.7559.2182").install())
    d = webdriver.Chrome(service=svc, options=opts)
    d.get(BASE_URL)
    # Wait for graph to render (nodes appear in DOM)
    WebDriverWait(d, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "g.node circle"))
    )
    # Let simulation settle
    time.sleep(2)
    yield d
    d.quit()


def test_first_click_no_flicker(driver):
    """
    Click a node when nothing is selected.
    Record EVERYTHING per frame: opacity, fill color, panel state, node positions.
    Detect any visual bounce/flicker.
    """
    driver.execute_script("""
        window.__log = [];
        window.__recording = true;

        const circles = document.querySelectorAll('g.node circle');
        window.__targetCircle = circles[circles.length - 1];
        window.__clickedCircle = circles[0];
        window.__panel = document.getElementById('proof-panel');

        function record() {
            if (!window.__recording) return;
            const tgt = window.__targetCircle;
            const clicked = window.__clickedCircle;
            const panelRight = getComputedStyle(window.__panel).right;
            window.__log.push({
                time: performance.now(),
                targetOpacity: parseFloat(getComputedStyle(tgt).opacity),
                targetFill: tgt.getAttribute('fill'),
                clickedOpacity: parseFloat(getComputedStyle(clicked).opacity),
                clickedFill: clicked.getAttribute('fill'),
                panelRight: panelRight,
                panelOpen: window.__panel.classList.contains('open'),
            });
            requestAnimationFrame(record);
        }
        requestAnimationFrame(record);
    """)

    time.sleep(0.3)

    # Real click via Selenium (goes through D3 drag handlers too)
    from selenium.webdriver.common.action_chains import ActionChains
    circle_el = driver.find_elements(By.CSS_SELECTOR, "g.node circle")[0]
    ActionChains(driver).click(circle_el).perform()

    time.sleep(2.0)

    log = driver.execute_script("""
        window.__recording = false;
        return window.__log;
    """)

    assert len(log) > 10, f"Too few frames: {len(log)}"

    # Print full trace for debugging
    print(f"\n{'frame':>5} {'tgtOp':>6} {'tgtFill':>10} {'clkOp':>6} {'clkFill':>10} {'panelOpen':>10} {'panelRight':>12}")
    for i, f in enumerate(log):
        print(f"{i:5d} {f['targetOpacity']:6.3f} {f['targetFill']:>10} {f['clickedOpacity']:6.3f} {f['clickedFill']:>10} {str(f['panelOpen']):>10} {f['panelRight']:>12}")

    # Detect flicker: any property that changes, reverts, then changes again
    opacities = [e['targetOpacity'] for e in log]
    fills = [e['clickedFill'] for e in log]

    # Check opacity flicker
    transition_start = next((i for i, op in enumerate(opacities) if op < 0.99), None)
    if transition_start is None:
        pytest.fail(f"Target node never dimmed. Opacities: {opacities[:20]}")

    post = opacities[transition_start:]
    min_seen = post[0]
    flicker_frames = []
    for i, op in enumerate(post[1:], 1):
        if op > min_seen + 0.05:
            flicker_frames.append({'frame': transition_start + i, 'op': op, 'min': min_seen})
        min_seen = min(min_seen, op)

    # Check fill flicker on clicked node — should go to #e05555 and stay
    fill_changes = []
    for i in range(1, len(fills)):
        if fills[i] != fills[i-1]:
            fill_changes.append({'frame': i, 'from': fills[i-1], 'to': fills[i]})

    print(f"\nFill changes on clicked node: {json.dumps(fill_changes, indent=2)}")
    print(f"Opacity flicker frames: {json.dumps(flicker_frames, indent=2)}")

    # Fill should change at most once (initial → active color)
    assert len(fill_changes) <= 1, (
        f"FILL FLICKER: clicked node fill changed {len(fill_changes)} times: {fill_changes}"
    )

    assert not flicker_frames, (
        f"OPACITY FLICKER: {json.dumps(flicker_frames, indent=2)}"
    )

    assert opacities[-1] < 0.2, f"Final opacity {opacities[-1]} not dimmed"


def test_switch_node_no_flicker(driver):
    """
    With a node already selected, click a different node.
    Should not flicker — opacity of unrelated nodes stays low.
    """
    # First make sure a node is already selected from previous test
    # Click a different node and monitor
    driver.execute_script("""
        window.__opacityLog = [];
        window.__recording = true;

        const circles = document.querySelectorAll('g.node circle');
        // Click the 5th node (different from first)
        window.__clickCircle2 = circles[4];
        // Monitor a node that's NOT the 5th
        window.__targetCircle2 = circles[circles.length - 1];

        function record2() {
            if (!window.__recording) return;
            const op = parseFloat(getComputedStyle(window.__targetCircle2).opacity);
            window.__opacityLog.push({ time: performance.now(), opacity: op });
            requestAnimationFrame(record2);
        }
        requestAnimationFrame(record2);
    """)

    time.sleep(0.2)

    driver.execute_script("window.__clickCircle2.parentElement.dispatchEvent(new MouseEvent('click', {bubbles: true}))")

    time.sleep(1.5)

    log = driver.execute_script("""
        window.__recording = false;
        return window.__opacityLog;
    """)

    opacities = [e['opacity'] for e in log]

    # Check for bounces > 5%
    min_seen = opacities[0]
    flicker_frames = []
    for i, op in enumerate(opacities[1:], 1):
        if op > min_seen + 0.05:
            flicker_frames.append({'frame': i, 'opacity': op, 'prev_min': min_seen})
        min_seen = min(min_seen, op)

    assert not flicker_frames, (
        f"FLICKER on node switch!\n"
        f"Flicker frames: {json.dumps(flicker_frames, indent=2)}\n"
        f"Opacity sequence: {opacities[:20]}"
    )

    print(f"\nPASSED: node switch, {len(log)} frames, no flicker")
