from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import openpyxl

DEFAULT_BASE_URL = "http://124.225.183.175:8361"
DEFAULT_DOCTOR_HASH = "#/doctor"
DEFAULT_LIST_HASH = "#/userTable/%E8%83%B8%E9%83%A8DR"

USERNAME_SELECTORS = (
    'input[name="username"]',
    'input[name*="user" i]',
    'input[placeholder*="username" i]',
    'input[placeholder*="user name" i]',
    'input[placeholder*="Nama Pengguna" i]',
    'input[placeholder*="用户名"]',
    'input[placeholder*="账号"]',
    'input[placeholder*="帐号"]',
    'input[type="text"]',
)
PASSWORD_SELECTORS = (
    'input[type="password"]',
    'input[name="password"]',
    'input[name*="pass" i]',
    'input[placeholder*="Kata Sandi" i]',
)
LOGIN_BUTTON_TEXTS = ("Login", "Sign in", "Log in", "Masuk", "登录", "登入")

TECHNICAL_TERMS = {
    "AI", "PACS", "DICOM", "DR", "CR", "CT", "MRI", "JPEG", "PNG", "PDF",
    "ID", "Madeena", "UMI", "HTML", "URL", "JSON", "HTTP", "HTTPS", "GB", "MB", "KB",
    "B-MODE", "2D", "3D", "4D",
    # Product names — must not be translated
    "Insight", "Insight ChestDR", "Insight QCDR",
}

KNOWN_TRANSLATIONS = {
    "用户名": "Nama Pengguna",
    "密码": "Kata Sandi",
    "登录": "Masuk",
    "登入": "Masuk",
    "胸部DR": "DR Dada",
    "医生": "Dokter",
    "Login": "Masuk",
    "Log in": "Masuk",
    "Sign in": "Masuk",
    "Username": "Nama Pengguna",
    "Password": "Kata Sandi",
    "Doctor": "Dokter",
    "Patient": "Pasien",
    "Status": "Status",
    "Search": "Cari",
    "Reset": "Atur Ulang",
    "Export": "Ekspor",
    "Action": "Tindakan",
    "Detail": "Rincian",
    "Operation": "Operasi",
    "Language": "Bahasa",
    "Download Report": "Unduh Laporan",
    "Generate Report": "Buat Laporan",
    "AI Report": "Laporan AI",
    "Image Report": "Laporan Gambar",
    "Unduh Report": "Unduh Laporan",
    "Sex": "Jenis Kelamin",
    "Age": "Usia",
    "Name": "Nama",
    "Date": "Tanggal",
    "Department": "Departemen",
}


@dataclass
class Finding:
    finding_id: str
    route: str
    module_name: str
    element_selector: str
    text_observed: str
    classification: str
    expected_indonesian: str
    quality_note: str
    screenshot_path: str


def find_system_chromium() -> str | None:
    override = os.environ.get("PACS_CHROMIUM_EXECUTABLE", "").strip()
    if override and Path(override).is_file():
        return override

    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "msedge", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            return found

    pw_cache = Path.home() / ".cache" / "ms-playwright"
    if pw_cache.is_dir():
        for candidate in sorted(pw_cache.glob("chromium-*/chrome-linux64/chrome"), reverse=True):
            if candidate.is_file():
                return str(candidate)
        for candidate in sorted(pw_cache.glob("chromium-*/chrome-linux/chrome"), reverse=True):
            if candidate.is_file():
                return str(candidate)

    if os.name == "nt":
        roots = [
            os.environ.get("PROGRAMFILES"),
            os.environ.get("PROGRAMFILES(X86)"),
            os.environ.get("LOCALAPPDATA"),
        ]
        relatives = (
            Path("Google/Chrome/Application/chrome.exe"),
            Path("Microsoft/Edge/Application/msedge.exe"),
        )
        for root in roots:
            if not root:
                continue
            for relative in relatives:
                candidate = Path(root) / relative
                if candidate.is_file():
                    return str(candidate)
    return None


def load_credentials(path: str | Path) -> tuple[str, str]:
    values: dict[str, str] = {}
    credential_path = Path(path)
    if not credential_path.is_file() and credential_path.name == "credential.txt":
        dotenv_path = credential_path.with_name(".env")
        if dotenv_path.is_file():
            credential_path = dotenv_path

    if not credential_path.is_file():
        raise ValueError(f"Credential file not found: {path}")

    for raw_line in credential_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    missing = [
        key
        for key in ("AI_PACS_USERNAME", "AI_PACS_PASSWORD")
        if not values.get(key)
    ]
    if missing:
        raise ValueError(f"Missing credential key(s): {', '.join(missing)}")
    return values["AI_PACS_USERNAME"], values["AI_PACS_PASSWORD"]


def probe_http_origin(base_url: str, timeout: float = 5.0) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/"
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "AI-PACS-Localization-Probe/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"ok": True, "url": url, "status": getattr(response, "status", None), "error": None}
    except urllib.error.HTTPError as exc:
        return {"ok": True, "url": url, "status": exc.code, "error": None}
    except Exception as exc:
        return {"ok": False, "url": url, "status": None, "error": str(exc)}


def generate_finding_id(route: str, element_selector: str, text_observed: str) -> str:
    key = f"{route}\x00{element_selector}\x00{text_observed}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


INDONESIAN_KEYWORDS = {
    "produk", "ini", "hanya", "untuk", "keperluan", "penelitian", "bukan", "aplikasi", "klinis",
    "impor", "analisis", "dan", "penilaian", "citra", "dada", "multi-penyakit", "manajemen",
    "antrian", "pengarsipan", "komputasi", "pasien", "nama", "stasiun", "pengguna", "kata",
    "sandi", "masuk", "keluar", "batal", "simpan", "cari", "atur", "ulang", "tindakan",
    "rincian", "laporan", "gambar", "hasil", "diagnosis", "pengaturan", "sistem", "dokter",
    "jenis", "kelamin", "usia", "tanggal", "departemen", "tabel", "daftar", "id", "pemeriksaan"
}


def classify_string(text: str) -> tuple[str, str, str]:
    text_clean = text.strip()
    if not text_clean or len(text_clean) < 2:
        return "technical-term", "", ""

    # Pure numeric or punctuation
    if re.match(r"^[\d\.\,\:\-\/\s\%\#\$\(\)\+\=\>\<]+$", text_clean):
        return "technical-term", "", ""

    # Icon names or tech identifiers
    if text_clean in {"eye-invisible", "eye", "lock", "user", "search", "loading", "anticon"}:
        return "technical-term", "", ""

    # Date string
    if re.match(r"^\d{4}[-/]\d{2}[-/]\d{2}", text_clean) or re.match(r"^\d{2}[-/]\d{2}[-/]\d{4}", text_clean):
        return "technical-term", "", ""

    # Technical terms or upper-case codes
    if text_clean in TECHNICAL_TERMS or re.match(r"^[A-Z0-9_\-]+$", text_clean):
        return "technical-term", "", ""

    # Check for quality issue typos
    if text_clean == "Masukan kata sandi":
        return "quality-issue", "Masukkan kata sandi", "Kata kerja imperatif membutuhkan 'Masukkan' bukan 'Masukan'"

    # Check for Chinese characters
    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", text_clean))
    if has_chinese:
        expected = KNOWN_TRANSLATIONS.get(text_clean, "")
        return "not-indonesian", expected, ""

    # Check for mixed
    if "Unduh Report" in text_clean or "Laporan AI (AI Report)" in text_clean:
        expected = KNOWN_TRANSLATIONS.get(text_clean, "Unduh Laporan" if "Unduh Report" in text_clean else "Laporan AI")
        return "mixed", expected, ""

    # Check for English UI words when ID locale is active
    english_words = {
        "Login", "Sign in", "Log in", "Username", "Password", "Download Report",
        "Generate Report", "AI Report", "Image Report", "Doctor", "Patient",
        "Search", "Reset", "Export", "Operation", "Action", "Detail", "Sex", "Age",
        "Date", "Department", "Language", "Insight", "User", "System"
    }
    if text_clean in english_words or any(w in text_clean for w in ("Download Report", "Generate Report", "Image Report")):
        expected = KNOWN_TRANSLATIONS.get(text_clean, "")
        return "not-indonesian", expected, ""

    # Check if text is valid Indonesian (words contained in INDONESIAN_KEYWORDS)
    words = [w.lower().strip(".,()!*") for w in text_clean.split()]
    if words:
        indonesian_word_count = sum(1 for w in words if w in INDONESIAN_KEYWORDS)
        if (indonesian_word_count / len(words)) >= 0.4:
            return "technical-term", "", ""

    return "uncertain", "", ""


def export_to_excel(findings: list[Finding], summary: dict[str, Any], output_path: str | Path) -> None:
    wb = openpyxl.Workbook()
    
    # Sheet 1: Findings
    ws_findings = wb.active
    ws_findings.title = "Findings"
    
    findings_headers = [
        "finding_id",
        "route",
        "module_name",
        "element_selector",
        "text_observed",
        "classification",
        "expected_indonesian",
        "quality_note",
        "screenshot_path",
    ]
    ws_findings.append(findings_headers)
    
    for f in findings:
        ws_findings.append([
            f.finding_id,
            f.route,
            f.module_name,
            f.element_selector,
            f.text_observed,
            f.classification,
            f.expected_indonesian,
            f.quality_note,
            f.screenshot_path,
        ])

    # Sheet 2: Summary
    ws_summary = wb.create_sheet(title="Summary")
    summary_headers = [
        "run_timestamp",
        "base_url",
        "routes_visited",
        "strings_inspected",
        "findings_total",
        "findings_not_indonesian",
        "findings_mixed",
        "findings_quality_issue",
        "findings_uncertain",
        "viewer_modal_visited",
    ]
    ws_summary.append(summary_headers)
    ws_summary.append([
        summary.get("run_timestamp", ""),
        summary.get("base_url", ""),
        summary.get("routes_visited", 0),
        summary.get("strings_inspected", 0),
        summary.get("findings_total", 0),
        summary.get("findings_not_indonesian", 0),
        summary.get("findings_mixed", 0),
        summary.get("findings_quality_issue", 0),
        summary.get("findings_uncertain", 0),
        summary.get("viewer_modal_visited", False),
    ])

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)


class LocalizationAuditor:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        storage_state: str | Path,
        screenshots_dir: str | Path,
        headed: bool = False,
        timeout_ms: int = 30000,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.storage_state = Path(storage_state)
        self.screenshots_dir = Path(screenshots_dir)
        self.headed = headed
        self.timeout_ms = timeout_ms

        self.findings: list[Finding] = []
        self.seen_keys: set[tuple[str, str, str]] = set()
        self.strings_inspected = 0
        self.routes_visited: set[str] = set()

        self._playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Run: python -m pip install playwright"
            ) from exc

        self._playwright = sync_playwright().start()
        managed_executable = Path(self._playwright.chromium.executable_path)
        launch_kwargs: dict[str, Any] = {"headless": not self.headed}
        if not managed_executable.is_file():
            system_chromium = find_system_chromium()
            if system_chromium:
                launch_kwargs["executable_path"] = system_chromium

        self.browser = self._playwright.chromium.launch(**launch_kwargs)

        context_kwargs: dict[str, Any] = {
            "accept_downloads": True,
            "locale": "id-ID",
            "extra_http_headers": {"Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"},
        }
        if self.storage_state.is_file():
            try:
                json.loads(self.storage_state.read_text(encoding="utf-8"))
                context_kwargs["storage_state"] = str(self.storage_state)
            except (OSError, json.JSONDecodeError):
                pass

        self.context = self.browser.new_context(**context_kwargs)
        self.context.add_init_script(
            "try { "
            "localStorage.setItem('umi_locale', 'id-ID'); "
            "localStorage.setItem('i18nextLng', 'id'); "
            "localStorage.setItem('locale', 'id-ID'); "
            "localStorage.setItem('lang', 'id'); "
            "} catch(e) {}"
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout_ms)
        self.page.set_default_navigation_timeout(self.timeout_ms)

    def close(self) -> None:
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
            self.context = None
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
            self.browser = None
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    def _first_visible_css(self, selectors: Iterable[str]):
        for selector in selectors:
            locator = self.page.locator(selector)
            try:
                count = min(locator.count(), 10)
            except Exception:
                continue
            for i in range(count):
                item = locator.nth(i)
                try:
                    if item.is_visible():
                        return item
                except Exception:
                    continue
        return None

    def login_if_needed(self) -> None:
        self.page.goto(self.base_url + "/", wait_until="domcontentloaded")
        self.page.wait_for_timeout(800)

        password_field = self._first_visible_css(PASSWORD_SELECTORS)
        if password_field is not None:
            username_field = self._first_visible_css(USERNAME_SELECTORS)
            if username_field and password_field:
                login_btn = None
                for text in LOGIN_BUTTON_TEXTS:
                    loc = self.page.get_by_role("button", name=text, exact=False)
                    try:
                        for i in range(min(loc.count(), 5)):
                            cand = loc.nth(i)
                            if cand.is_visible():
                                login_btn = cand
                                break
                    except Exception:
                        continue
                    if login_btn:
                        break
                if not login_btn:
                    login_btn = self._first_visible_css(("button[type=submit]", ".ant-btn-primary", "button"))

                if username_field and login_btn:
                    username_field.fill(self.username)
                    password_field.fill(self.password)
                    login_btn.click()
                    self.page.wait_for_timeout(1200)

        self.storage_state.parent.mkdir(parents=True, exist_ok=True)
        self.context.storage_state(path=str(self.storage_state))

    def derive_module_name(self, route_id: str) -> str:
        if route_id == "login":
            return "Authentication"
        elif route_id == "doctor":
            return "Doctor Portal"
        elif route_id in ("study-list", "userTable"):
            return "Study List"
        elif route_id == "viewer-modal":
            return "Viewer Window"
        elif "userTable" in route_id:
            clean = route_id.replace("userTable/", "").replace("%E8%83%B8%E9%83%A8DR", "Chest DR")
            return f"Study List ({clean})"
        return route_id.replace("_", " ").replace("-", " ").title()

    def extract_and_classify_route(self, route_id: str, module_name: str | None = None) -> None:
        self.routes_visited.add(route_id)
        if not module_name:
            module_name = self.derive_module_name(route_id)

        self.page.wait_for_timeout(1000)

        elements_data = self.page.evaluate(
            """() => {
                const items = [];
                const isVisible = (el) => {
                    if (!el) return false;
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                };
                
                const processElement = (el) => {
                    if (!isVisible(el)) return;
                    
                    // Check if inside patient table data cell
                    const isTd = Boolean(el.closest('td') && !el.closest('th'));
                    
                    let text = '';
                    let sel = el.tagName.toLowerCase();
                    if (el.id) {
                        sel += '#' + el.id;
                    } else if (el.className && typeof el.className === 'string') {
                        const cls = el.className.split(/\\s+/).filter(c => c && !c.includes('active')).slice(0, 2);
                        if (cls.length > 0) sel += '.' + cls.join('.');
                    }

                    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                        const ph = el.getAttribute('placeholder');
                        if (ph) {
                            text = ph.trim();
                            sel += '[placeholder]';
                        }
                    } else if (el.tagName === 'IMG') {
                        const alt = el.getAttribute('alt') || el.getAttribute('title');
                        if (alt) text = alt.trim();
                    } else {
                        // Check direct child text nodes
                        for (let c of el.childNodes) {
                            if (c.nodeType === Node.TEXT_NODE) {
                                const t = c.textContent.trim();
                                if (t.length >= 2) {
                                    text = t;
                                    break;
                                }
                            }
                        }
                        if (!text) {
                            const aria = el.getAttribute('aria-label') || el.getAttribute('title');
                            if (aria) text = aria.trim();
                        }
                    }

                    if (text && text.length >= 2) {
                        items.push({
                            selector: sel,
                            text: text,
                            isTd: isTd
                        });
                    }
                };

                const all = document.querySelectorAll('span, div, button, a, input, th, td, label, p, h1, h2, h3, h4, h5, h6, li, option');
                for (let el of all) {
                    processElement(el);
                }
                return items;
            }"""
        )

        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        for item in elements_data:
            text = item.get("text", "").strip()
            selector = item.get("selector", "")
            is_td = item.get("isTd", False)

            self.strings_inspected += 1

            # Exclude patient data inside td
            if is_td and "study-list" in route_id:
                continue

            classification, expected, quality_note = classify_string(text)
            if classification == "technical-term":
                continue

            key = (route_id, selector, text)
            if key in self.seen_keys:
                continue

            self.seen_keys.add(key)
            finding_id = generate_finding_id(route_id, selector, text)

            # Capture element screenshot
            screenshot_rel_path = ""
            screenshot_filename = f"{route_id}_{len(self.findings)+1:03d}_{finding_id[:8]}.png"
            screenshot_full_path = self.screenshots_dir / screenshot_filename

            try:
                # Find matching Playwright locator
                loc = self.page.get_by_text(text, exact=True).first
                if loc and loc.is_visible():
                    loc.screenshot(path=str(screenshot_full_path))
                    screenshot_rel_path = f"{self.screenshots_dir.name}/{screenshot_filename}"
            except Exception:
                screenshot_rel_path = ""

            self.findings.append(Finding(
                finding_id=finding_id,
                route=route_id,
                module_name=module_name,
                element_selector=selector,
                text_observed=text,
                classification=classification,
                expected_indonesian=expected,
                quality_note=quality_note,
                screenshot_path=screenshot_rel_path,
            ))

    def discover_and_audit_navigation(self) -> None:
        """Safely discovers and audits all accessible navigation links and sub-tabs."""
        # Detect menu links and sub-tabs
        nav_elements = self.page.evaluate(
            """() => {
                const links = [];
                const selectors = ['.ant-menu-item', '.ant-menu-submenu-title', 'a[href*="#/"]', '.ant-tabs-tab'];
                const unsafeKeywords = ['delete', 'hapus', 'remove', 'submit', 'kirim', 'save', 'simpan', 'edit', 'ubah', 'download', 'unduh', 'export', 'ekspor', 'logout', 'exit', 'out'];
                
                for (const sel of selectors) {
                    for (const el of document.querySelectorAll(sel)) {
                        const txt = (el.textContent || '').trim().toLowerCase();
                        const href = el.getAttribute('href') || '';
                        
                        // Safety check: skip mutating/destructive links
                        if (unsafeKeywords.some(k => txt.includes(k) || href.toLowerCase().includes(k))) {
                            continue;
                        }
                        
                        links.push({
                            text: el.textContent.trim(),
                            href: href,
                            isTab: el.classList.contains('ant-tabs-tab'),
                        });
                    }
                }
                return links;
            }"""
        )

        for item in nav_elements:
            text = item.get("text", "").strip()
            href = item.get("href", "").strip()
            is_tab = item.get("isTab", False)

            if not text or len(text) < 2:
                continue

            route_name = text.lower().replace(" ", "-")
            if is_tab:
                # Safely click tab if visible
                try:
                    tab_loc = self.page.get_by_role("tab", name=text, exact=False).first
                    if tab_loc and tab_loc.is_visible():
                        tab_loc.click(timeout=3000)
                        self.page.wait_for_timeout(800)
                        self.extract_and_classify_route(f"tab-{route_name}", module_name=f"Tab: {text}")
                except Exception:
                    pass
            elif href and "#/" in href:
                # Navigate to hash route
                hash_part = href[href.index("#/"):].strip()
                if hash_part and hash_part not in ("/login", "#/login"):
                    try:
                        self.page.goto(f"{self.base_url}/{hash_part}", wait_until="domcontentloaded")
                        self.page.wait_for_timeout(800)
                        self.extract_and_classify_route(f"nav-{route_name}", module_name=f"Navigation: {text}")
                    except Exception:
                        pass

    def run_audit(self) -> None:
        self.viewer_modal_visited = False
        self.login_if_needed()

        # 1. Login route
        self.page.goto(f"{self.base_url}/#/login", wait_until="domcontentloaded")
        self.extract_and_classify_route("login", module_name="Authentication")

        # 2. Doctor landing route
        self.page.goto(f"{self.base_url}/{DEFAULT_DOCTOR_HASH}", wait_until="domcontentloaded")
        self.extract_and_classify_route("doctor", module_name="Doctor Portal")
        self.discover_and_audit_navigation()

        # 3. Study list route
        self.page.goto(f"{self.base_url}/{DEFAULT_LIST_HASH}", wait_until="domcontentloaded")
        self.extract_and_classify_route("study-list", module_name="Study List (Chest DR)")
        self.discover_and_audit_navigation()

        # 4. Viewer modal route (click first visible study row)
        try:
            self.page.wait_for_timeout(1000)
            rows = self.page.locator("tbody tr")
            row_count = 0
            try:
                row_count = rows.count()
            except Exception:
                pass

            visible_row = None
            for i in range(min(row_count, 5)):
                try:
                    candidate = rows.nth(i)
                    if candidate.is_visible():
                        visible_row = candidate
                        break
                except Exception:
                    continue

            if visible_row is None:
                print(
                    "[viewer-modal] No visible study row found in study list "
                    "— skipping viewer modal route."
                )
            else:
                try:
                    visible_row.click(timeout=10000)
                    self.page.wait_for_timeout(1500)
                    self.extract_and_classify_route("viewer-modal", module_name="Viewer Window")
                    self.viewer_modal_visited = True
                except Exception as exc:
                    print(
                        f"[viewer-modal] Failed to open viewer modal: "
                        f"{type(exc).__name__}: {exc}"
                    )
        except Exception as outer_exc:
            print(f"[viewer-modal] Unexpected error during row detection: {outer_exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="AI-PACS Indonesian Localization Audit Tool")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL of AI-PACS")
    parser.add_argument("--credentials", default="credential.txt", help="Credentials file path")
    parser.add_argument("--storage-state", default="auth-state.json", help="Playwright storage state file")
    parser.add_argument("--output", default="localization_report.xlsx", help="Output Excel report path")
    parser.add_argument("--screenshots-dir", default="screenshots", help="Directory for evidence screenshots")
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode")
    parser.add_argument("--timeout-ms", type=int, default=30000, help="Default Playwright timeout in ms")
    parser.add_argument("--probe-only", action="store_true", help="Probe PACS reachability only and exit")

    args = parser.parse_args()

    if args.probe_only:
        probe = probe_http_origin(args.base_url)
        if probe["ok"]:
            print(f"PACS probe success: {probe['url']} (status {probe['status']})")
            return 0
        else:
            print(f"PACS probe failed: {probe['error']}", file=sys.stderr)
            return 2

    try:
        username, password = load_credentials(args.credentials)
    except Exception as exc:
        print(f"Credential load error: {exc}", file=sys.stderr)
        return 2

    auditor = LocalizationAuditor(
        base_url=args.base_url,
        username=username,
        password=password,
        storage_state=args.storage_state,
        screenshots_dir=args.screenshots_dir,
        headed=args.headed,
        timeout_ms=args.timeout_ms,
    )

    try:
        auditor.start()
        auditor.run_audit()
    except Exception as exc:
        print(f"Audit run error: {exc}", file=sys.stderr)
        auditor.close()
        return 2
    finally:
        auditor.close()

    # Counts
    counts = {
        "not-indonesian": 0,
        "mixed": 0,
        "quality-issue": 0,
        "uncertain": 0,
    }
    for f in auditor.findings:
        if f.classification in counts:
            counts[f.classification] += 1

    summary = {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "routes_visited": len(auditor.routes_visited),
        "strings_inspected": auditor.strings_inspected,
        "findings_total": len(auditor.findings),
        "findings_not_indonesian": counts["not-indonesian"],
        "findings_mixed": counts["mixed"],
        "findings_quality_issue": counts["quality-issue"],
        "findings_uncertain": counts["uncertain"],
        "viewer_modal_visited": getattr(auditor, "viewer_modal_visited", False),
    }

    try:
        export_to_excel(auditor.findings, summary, args.output)
    except Exception as exc:
        print(f"Failed to export report: {exc}", file=sys.stderr)
        return 2

    print("--- Localization Audit Summary ---")
    print(f"Routes Visited    : {summary['routes_visited']}")
    print(f"Strings Inspected : {summary['strings_inspected']}")
    print(f"Findings Total    : {summary['findings_total']}")
    print(f"  - Not Indonesian: {counts['not-indonesian']}")
    print(f"  - Mixed         : {counts['mixed']}")
    print(f"  - Quality Issue : {counts['quality-issue']}")
    print(f"  - Uncertain     : {counts['uncertain']}")
    print(f"Report exported to: {args.output}")

    return 1 if len(auditor.findings) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
