from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

DEFAULT_BASE_URL = "http://124.225.183.175:8361"
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
GENERATE_REPORT_TEXTS = ("Generate Report", "Buat Laporan", "Hasilkan Laporan", "生成报告", "生成报告单")
AI_REPORT_TEXTS = ("AI Report", "Laporan AI", "AI报告")
IMAGE_REPORT_TEXTS = ("Image Report", "Laporan Gambar", "Laporan Citra", "影像报告", "图像报告")
DOWNLOAD_REPORT_TEXTS = ("Download Report", "Unduh Laporan", "下载报告")

PDF_HOOK_SCRIPT = r"""
(() => {
  const originalCreateObjectURL = URL.createObjectURL.bind(URL);
  window.__pacsCapturedPdf = null;
  window.__pacsCapturedPdfCount = 0;
  URL.createObjectURL = function(blob) {
    if (blob instanceof Blob && blob.type === 'application/pdf') {
      window.__pacsCapturedPdf = blob;
      window.__pacsCapturedPdfCount += 1;
    }
    return originalCreateObjectURL(blob);
  };
})();
"""


def find_system_chromium() -> str | None:
    override = os.environ.get("PACS_CHROMIUM_EXECUTABLE", "").strip()
    if override and Path(override).is_file():
        return override

    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "msedge", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            return found

    # Search user's Playwright cache directory
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


@dataclass(frozen=True, order=True)
class Study:
    sid: int
    ai_calc_id: int
    patient_id: str = field(default="", compare=False)
    patient_name: str = field(default="", compare=False)


def load_credentials(path: str | Path) -> tuple[str, str]:
    values: dict[str, str] = {}
    credential_path = Path(path)
    if not credential_path.is_file() and credential_path.name == "credential.txt":
        dotenv_path = credential_path.with_name(".env")
        if dotenv_path.is_file():
            credential_path = dotenv_path

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


def build_viewer_url(base_url: str, study: Study) -> str:
    query = urlencode(
        {
            "action": "viewer",
            "type": "CR",
            "sid": study.sid,
            "pacs": "fei",
            "aiCalcId": study.ai_calc_id,
        }
    )
    return urljoin(base_url.rstrip("/") + "/", "view/dr/index.html/viewer") + "?" + query


def _intish(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str):
        text = value.strip()
        if not text.isdigit():
            return None
        number = int(text)
        return number if number > 0 else None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _first_text(obj: dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = obj.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def extract_studies_from_json(payload: Any) -> list[Study]:
    found: dict[tuple[int, int], Study] = {}

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            ai = None
            for key in ("aiCalcId", "ai_calc_id", "aicalcid", "aiCalculationId"):
                if key in node:
                    ai = _intish(node.get(key))
                    if ai is not None:
                        break
            if ai is not None:
                sid = None
                for key in ("sid", "studyId", "study_id", "id"):
                    if key in node:
                        sid = _intish(node.get(key))
                        if sid is not None:
                            break
                if sid is not None:
                    found.setdefault(
                        (sid, ai),
                        Study(
                            sid=sid,
                            ai_calc_id=ai,
                            patient_id=_first_text(
                                node,
                                ("patientId", "patientID", "patient_id", "patientNo", "patient_no"),
                            ),
                            patient_name=_first_text(
                                node,
                                ("patientName", "patient_name", "name", "patient"),
                            ),
                        ),
                    )
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return sorted(found.values(), key=lambda study: (study.sid, study.ai_calc_id))


def extract_studies_from_hrefs(hrefs: Iterable[str], base_url: str) -> list[Study]:
    found: dict[tuple[int, int], Study] = {}
    for href in hrefs:
        if not href:
            continue
        absolute = urljoin(base_url.rstrip("/") + "/", href)
        parsed = urlparse(absolute)
        if "/view/dr/index.html/viewer" not in parsed.path:
            continue
        query = parse_qs(parsed.query)
        sid = _intish(query.get("sid", [None])[0])
        ai = _intish(query.get("aiCalcId", [None])[0])
        if sid is None or ai is None:
            continue
        found.setdefault((sid, ai), Study(sid=sid, ai_calc_id=ai))
    return sorted(found.values(), key=lambda study: (study.sid, study.ai_calc_id))


class StudyCollector:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self._studies: dict[tuple[int, int], Study] = {}

    def _add(self, study: Study) -> None:
        key = (study.sid, study.ai_calc_id)
        current = self._studies.get(key)
        if current is None:
            self._studies[key] = study
            return
        self._studies[key] = Study(
            sid=study.sid,
            ai_calc_id=study.ai_calc_id,
            patient_id=study.patient_id or current.patient_id,
            patient_name=study.patient_name or current.patient_name,
        )

    def add_json(self, payload: Any) -> None:
        for study in extract_studies_from_json(payload):
            self._add(study)

    def add_hrefs(self, hrefs: Iterable[str]) -> None:
        for study in extract_studies_from_hrefs(hrefs, self.base_url):
            self._add(study)

    def studies(self) -> list[Study]:
        return sorted(self._studies.values(), key=lambda study: (study.sid, study.ai_calc_id))


def validate_pdf_bytes(data: bytes) -> None:
    if not data.startswith(b"%PDF-"):
        raise ValueError("Missing PDF header")
    if len(data) < 1024:
        raise ValueError(f"PDF is too small ({len(data)} bytes)")
    if b"%%EOF" not in data[-4096:]:
        raise ValueError("Missing PDF EOF marker")


def safe_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value)
    cleaned = cleaned.strip(". ")
    return cleaned


def extract_patient_info_from_page(page) -> tuple[str | None, str | None]:
    try:
        text = page.evaluate("document.body.innerText")
        name = None
        patient_id = None

        match_name = re.search(r"Name[：:\s]+([^\n\r]+)", text)
        if match_name:
            cand = match_name.group(1).strip()
            if cand and cand != "-":
                name = cand

        match_id = re.search(r"Patient ID[：:\s]+([^\n\r]+)", text)
        if match_id:
            cand = match_id.group(1).strip()
            if cand and cand != "-":
                patient_id = cand

        if not name:
            match_header = re.search(r"Chest DR Intelligent Analysis\s*\n\s*([^\n\r]+)", text)
            if match_header:
                cand = match_header.group(1).strip()
                if cand and cand != "-":
                    name = cand

        return name, patient_id
    except Exception:
        return None, None


def study_stem(study: Study) -> str:
    if study.patient_name:
        cleaned = safe_filename(study.patient_name)
        if cleaned:
            return f"{cleaned}__sid-{study.sid}__ai-{study.ai_calc_id}"
    return f"CR-{study.sid}-AI-{study.ai_calc_id}"


def report_filename(study: Study) -> str:
    return f"{study_stem(study)}.pdf"


def screenshot_filename(study: Study) -> str:
    return f"{study_stem(study)}.png"


def atomic_save_pdf(path: str | Path, data: bytes) -> None:
    validate_pdf_bytes(data)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".part")
    temporary.write_bytes(data)
    temporary.replace(target)


def parse_explicit_studies(values: list[str]) -> list[Study]:
    result: list[Study] = []
    seen: set[tuple[int, int]] = set()
    for value in values:
        try:
            parts = value.split(":", 2)
            if len(parts) == 3:
                sid_text, ai_text, patient_name = parts
            else:
                sid_text, ai_text = value.split(":", 1)
                patient_name = ""
            sid = int(sid_text)
            ai = int(ai_text)
            if sid <= 0 or ai <= 0:
                raise ValueError
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"Invalid --study {value!r}; expected SID:AICALCID or SID:AICALCID:NAME, e.g. 58:50"
            ) from exc
        key = (sid, ai)
        if key not in seen:
            result.append(Study(sid=sid, ai_calc_id=ai, patient_name=patient_name))
            seen.add(key)
    return result


def probe_http_origin(base_url: str, timeout: float = 5.0) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/"
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "AI-PACS-Batch-Probe/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"ok": True, "url": url, "status": getattr(response, "status", None), "error": None}
    except urllib.error.HTTPError as exc:
        # An HTTP response proves the server is reachable even if authentication is required.
        return {"ok": True, "url": url, "status": exc.code, "error": None}
    except Exception as exc:
        return {"ok": False, "url": url, "status": None, "error": str(exc)}


def build_manifest_record(
    study: Study,
    *,
    status: str,
    output: str | None,
    screenshot: str | None = None,
    size: int | None,
    attempts: int,
    error: str | None,
) -> dict[str, Any]:
    return {
        "sid": study.sid,
        "aiCalcId": study.ai_calc_id,
        "patientId": study.patient_id,
        "patientName": study.patient_name,
        "status": status,
        "output": output,
        "screenshot": screenshot,
        "size": size,
        "attempts": attempts,
        "error": error,
    }


def append_manifest(path: str | Path, record: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


class PacsBrowser:
    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        password: str,
        storage_state: str | Path,
        diagnostics_dir: str | Path,
        headed: bool = False,
        timeout_ms: int = 30000,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.storage_state = Path(storage_state)
        self.diagnostics_dir = Path(diagnostics_dir)
        self.headed = headed
        self.timeout_ms = timeout_ms
        self.collector = StudyCollector(self.base_url)
        self._playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._timeout_error = Exception

    @property
    def list_url(self) -> str:
        return f"{self.base_url}/{DEFAULT_LIST_HASH}"

    def __enter__(self) -> "PacsBrowser":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def start(self) -> None:
        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Run: python -m pip install playwright"
            ) from exc

        self._timeout_error = PlaywrightTimeoutError
        self._playwright = sync_playwright().start()
        managed_executable = Path(self._playwright.chromium.executable_path)
        launch_kwargs: dict[str, Any] = {"headless": not self.headed}
        if not managed_executable.is_file():
            system_chromium = find_system_chromium()
            if system_chromium:
                launch_kwargs["executable_path"] = system_chromium
        try:
            self.browser = self._playwright.chromium.launch(**launch_kwargs)
        except PlaywrightError as exc:
            self._playwright.stop()
            self._playwright = None
            message = str(exc)
            if "Executable doesn't exist" in message or "playwright install" in message.lower():
                raise RuntimeError(
                    "No usable Chromium browser was found. Run: python -m playwright install chromium "
                    "or set PACS_CHROMIUM_EXECUTABLE to an installed Chrome/Edge/Chromium executable."
                ) from exc
            raise

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
        self.context.add_init_script(PDF_HOOK_SCRIPT)
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout_ms)
        self.page.set_default_navigation_timeout(self.timeout_ms)

        def on_response(response) -> None:
            try:
                if response.request.resource_type not in ("xhr", "fetch"):
                    return
                content_type = response.headers.get("content-type", "").lower()
                if "json" not in content_type and not response.url.lower().endswith(".json"):
                    return
                self.collector.add_json(response.json())
            except Exception:
                return

        self.page.on("response", on_response)

    def close(self) -> None:
        if self.context is not None:
            try:
                self.context.close()
            except Exception:
                pass
            self.context = None
        if self.browser is not None:
            try:
                self.browser.close()
            except Exception:
                pass
            self.browser = None
        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    def _require_page(self):
        if self.page is None:
            raise RuntimeError("Browser has not been started")
        return self.page

    def _first_visible_css(self, selectors: Iterable[str]):
        page = self._require_page()
        for selector in selectors:
            locator = page.locator(selector)
            try:
                count = min(locator.count(), 10)
            except Exception:
                continue
            for index in range(count):
                candidate = locator.nth(index)
                try:
                    if candidate.is_visible():
                        return candidate
                except Exception:
                    continue
        return None

    def _first_visible_text(self, texts: Iterable[str]):
        page = self._require_page()
        for text in texts:
            for exact in (True, False):
                locator = page.get_by_text(text, exact=exact)
                try:
                    count = min(locator.count(), 10)
                except Exception:
                    continue
                for index in range(count):
                    candidate = locator.nth(index)
                    try:
                        if candidate.is_visible():
                            return candidate
                    except Exception:
                        continue
        return None

    def _login_button(self):
        page = self._require_page()
        for text in LOGIN_BUTTON_TEXTS:
            locator = page.get_by_role("button", name=text, exact=False)
            try:
                count = min(locator.count(), 5)
            except Exception:
                count = 0
            for index in range(count):
                candidate = locator.nth(index)
                try:
                    if candidate.is_visible():
                        return candidate
                except Exception:
                    continue
        return self._first_visible_css(("button[type=submit]", ".ant-btn-primary", "button"))

    def _password_visible(self) -> bool:
        return self._first_visible_css(PASSWORD_SELECTORS) is not None

    def _select_indonesian_language(self) -> None:
        page = self._require_page()
        try:
            page.evaluate("() => localStorage.setItem('i18nextLng', 'id')")
        except Exception:
            pass

        try:
            triggers = (
                ".ant-dropdown-trigger",
                ".header-lang",
                ".lang-select",
                "button[class*='lang' i]",
                "div[class*='lang' i]",
                "span[class*='lang' i]",
            )
            trigger = None
            for sel in triggers:
                loc = page.locator(sel)
                try:
                    for i in range(min(loc.count(), 5)):
                        item = loc.nth(i)
                        if item.is_visible():
                            trigger = item
                            break
                except Exception:
                    continue
                if trigger is not None:
                    break

            if trigger is None:
                for text in ("Indonesian", "Bahasa Indonesia", "English", "Language"):
                    loc = page.get_by_text(text, exact=False)
                    try:
                        for i in range(min(loc.count(), 5)):
                            item = loc.nth(i)
                            if item.is_visible():
                                trigger = item
                                break
                    except Exception:
                        continue
                    if trigger is not None:
                        break

            if trigger is not None:
                text = trigger.inner_text().strip()
                if "Indonesian" in text or "Bahasa" in text:
                    page.evaluate("() => localStorage.setItem('i18nextLng', 'id')")
                    return
                trigger.click()
                page.wait_for_timeout(300)

                for opt_text in ("Indonesian", "Bahasa Indonesia", "Indonesia"):
                    opt = page.get_by_text(opt_text, exact=True)
                    try:
                        if opt.is_visible():
                            opt.click()
                            page.wait_for_timeout(500)
                            page.evaluate("() => localStorage.setItem('i18nextLng', 'id')")
                            return
                    except Exception:
                        continue
        except Exception:
            pass

    def login(self) -> None:
        page = self._require_page()
        page.goto(self.base_url + "/", wait_until="domcontentloaded")
        page.wait_for_timeout(800)

        self._select_indonesian_language()

        password_field = self._first_visible_css(PASSWORD_SELECTORS)
        if password_field is not None:
            username_field = self._first_visible_css(USERNAME_SELECTORS)
            if username_field is None:
                raise RuntimeError("Login page detected but no visible username field was found")
            button = self._login_button()
            if button is None:
                raise RuntimeError("Login page detected but no visible login button was found")

            username_field.fill(self.username)
            password_field.fill(self.password)
            button.click()
            page.wait_for_timeout(1200)

        page.goto(self.list_url, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)
        if self._password_visible():
            password_field = self._first_visible_css(PASSWORD_SELECTORS)
            username_field = self._first_visible_css(USERNAME_SELECTORS)
            button = self._login_button()
            if username_field and password_field and button:
                username_field.fill(self.username)
                password_field.fill(self.password)
                button.click()
                page.wait_for_timeout(1200)
                page.goto(self.list_url, wait_until="domcontentloaded")
                page.wait_for_timeout(1000)

        if self._password_visible():
            raise RuntimeError("Authentication failed: the login form is still visible after submission")

        # A table is language-independent enough to prove the authenticated list shell loaded.
        try:
            page.locator("table").first.wait_for(state="visible", timeout=min(self.timeout_ms, 15000))
        except Exception:
            # Some Ant Design tables are div-based; accept a user-table route if login is absent.
            if "userTable" not in page.url:
                raise RuntimeError(
                    f"Authentication could not be verified. Current URL: {page.url}"
                )

        self.storage_state.parent.mkdir(parents=True, exist_ok=True)
        self.context.storage_state(path=str(self.storage_state))
        try:
            os.chmod(self.storage_state, 0o600)
        except OSError:
            pass

    def _collect_dom_hrefs(self, collector: StudyCollector) -> None:
        page = self._require_page()
        try:
            hrefs = page.locator("a[href]").evaluate_all(
                "els => els.map(el => el.href || el.getAttribute('href') || '')"
            )
            collector.add_hrefs(hrefs)
        except Exception:
            pass

    def _visible_next_button(self):
        page = self._require_page()
        selectors = (
            "li.ant-pagination-next:not(.ant-pagination-disabled) button",
            "li.ant-pagination-next:not(.ant-pagination-disabled)",
            ".ant-pagination-next:not(.ant-pagination-disabled) button",
            'button[aria-label="right"]:not([disabled])',
            'button[aria-label="Next Page"]:not([disabled])',
        )
        return self._first_visible_css(selectors)

    def discover_studies(self) -> list[Study]:
        page = self._require_page()
        page.goto(self.list_url, wait_until="domcontentloaded")
        page.wait_for_timeout(1200)
        self._collect_dom_hrefs(self.collector)

        if not self.collector.studies():
            try:
                page.reload(wait_until="domcontentloaded")
                page.wait_for_timeout(1500)
                self._collect_dom_hrefs(self.collector)
            except Exception:
                pass

        visited_pages = 0
        while visited_pages < 100:
            next_button = self._visible_next_button()
            if next_button is None:
                break
            before = page.locator("tbody").first.inner_text() if page.locator("tbody").count() else ""
            next_button.click()
            page.wait_for_timeout(1000)
            self._collect_dom_hrefs(self.collector)
            visited_pages += 1
            if before and page.locator("tbody").count():
                after = page.locator("tbody").first.inner_text()
                if after == before:
                    break

        return self.collector.studies()

    def _click_first_text(self, texts: Iterable[str], label: str) -> None:
        locator = self._first_visible_text(texts)
        if locator is None:
            raise RuntimeError(f"Could not find visible {label}")
        locator.click()

    def _ensure_image_report(self) -> None:
        page = self._require_page()
        modal = page.locator(".ant-modal-content").first
        combo = modal.locator(".ant-select-selector, .ant-select").first

        try:
            combo.click(timeout=5000)
            page.wait_for_timeout(500)
            dropdown = page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)")
            pattern = re.compile(r"Image Report|影像报告|Laporan Gambar|Laporan Citra", re.I)
            option = dropdown.locator(".ant-select-item-option, .ant-select-item-option-content, .ant-select-item").filter(has_text=pattern).first
            option.click(timeout=5000)
            # Wait for modal canvas to be populated with real content
            # (canvas.width > 100 means it's initialised; we then wait
            #  an extra 8s so the DICOM X-Ray fully renders inside it)
            try:
                page.wait_for_function(
                    """() => {
                        const c = document.querySelector('.ant-modal-content canvas');
                        return c && c.width > 100 && c.height > 100;
                    }""",
                    timeout=15000,
                )
            except Exception:
                pass
            page.wait_for_timeout(8000)
        except Exception:
            pass

    def read_captured_pdf(self) -> bytes:
        page = self._require_page()
        encoded = page.evaluate(
            """
            async () => {
              const blob = window.__pacsCapturedPdf;
              if (!(blob instanceof Blob) || blob.type !== 'application/pdf') {
                throw new Error('No captured application/pdf Blob');
              }
              return await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onerror = () => reject(reader.error || new Error('FileReader failed'));
                reader.onload = () => resolve(String(reader.result).split(',', 2)[1]);
                reader.readAsDataURL(blob);
              });
            }
            """
        )
        if not isinstance(encoded, str) or not encoded:
            raise RuntimeError("Captured PDF Blob could not be encoded")
        data = base64.b64decode(encoded, validate=True)
        validate_pdf_bytes(data)
        return data

    def download_report(
        self, study: Study, screenshot_path: str | Path | None = None
    ) -> bytes:
        page = self._require_page()
        # Set Indonesian locale BEFORE navigation so i18next reads it at startup
        try:
            page.context.add_init_script(
                "window.localStorage && localStorage.setItem('i18nextLng', 'id');"
            )
        except Exception:
            pass
        page.goto(build_viewer_url(self.base_url, study), wait_until="load")
        # Belt-and-suspenders: also set after load in case init script missed
        try:
            page.evaluate("localStorage.setItem('i18nextLng', 'id')")
        except Exception:
            pass
        page.wait_for_timeout(2000)

        ext_name, ext_id = extract_patient_info_from_page(page)
        if ext_name and not study.patient_name:
            object.__setattr__(study, "patient_name", ext_name)
        if ext_id and not study.patient_id:
            object.__setattr__(study, "patient_id", ext_id)

        generate = self._first_visible_text(GENERATE_REPORT_TEXTS)
        if generate is None:
            try:
                page.get_by_role("button", name="Generate Report", exact=False).wait_for(
                    state="visible", timeout=self.timeout_ms
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Generate Report button was not found for sid={study.sid}, aiCalcId={study.ai_calc_id}"
                ) from exc
            generate = page.get_by_role("button", name="Generate Report", exact=False).first

        if screenshot_path is not None:
            try:
                page.wait_for_selector("canvas", state="visible", timeout=10000)
            except Exception:
                pass
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(3000)
            target = Path(screenshot_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            temp_path = target.with_name(target.stem + ".tmp.png")
            page.screenshot(path=str(temp_path), full_page=False, type="png")
            temp_path.replace(target)

        generate.click()

        # Wait for report rendering controls to appear.
        deadline_button = None
        for _ in range(max(1, self.timeout_ms // 250)):
            deadline_button = self._first_visible_text(DOWNLOAD_REPORT_TEXTS)
            if deadline_button is not None:
                break
            page.wait_for_timeout(250)
        if deadline_button is None:
            raise RuntimeError("Report dialog opened but Download Report did not become visible")

        modal = page.locator(".ant-modal-content").first
        try:
            modal_text = modal.inner_text()
            m_name = re.search(r"Name[：:\s]+([^\n\r]+)", modal_text)
            if m_name:
                cand = m_name.group(1).strip()
                if cand and cand != "-":
                    object.__setattr__(study, "patient_name", cand)
            m_id = re.search(r"Patient ID[：:\s]+([^\n\r]+)", modal_text)
            if m_id:
                cand = m_id.group(1).strip()
                if cand and cand != "-":
                    object.__setattr__(study, "patient_id", cand)
        except Exception:
            pass
        ai_tab = None
        for text in AI_REPORT_TEXTS:
            loc = modal.get_by_text(text, exact=False)
            try:
                if loc.count() and loc.first.is_visible():
                    ai_tab = loc.first
                    break
            except Exception:
                continue

        if ai_tab is not None:
            try:
                ai_tab.click(timeout=2000)
                page.wait_for_timeout(400)
            except Exception:
                pass

        self._ensure_image_report()

        page.evaluate(
            "window.__pacsCapturedPdf = null; window.__pacsCapturedPdfCount = 0;"
        )
        download = self._first_visible_text(DOWNLOAD_REPORT_TEXTS)
        if download is None:
            raise RuntimeError("Download Report button disappeared before download")
        download.click()

        page.wait_for_function(
            """
            () => window.__pacsCapturedPdf instanceof Blob &&
                  window.__pacsCapturedPdf.type === 'application/pdf' &&
                  window.__pacsCapturedPdf.size > 50000
            """,
            timeout=self.timeout_ms,
        )
        data = self.read_captured_pdf()
        if len(data) < 50000:
            raise RuntimeError(f"Downloaded PDF is too small ({len(data)} bytes); expected Image Report PDF with embedded X-Ray image (>50KB).")
        return data

    def capture_diagnostic(self, study: Study, attempt: int, error: Exception) -> None:
        page = self._require_page()
        self.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        stem = safe_filename(f"sid-{study.sid}-ai-{study.ai_calc_id}-attempt-{attempt}")
        screenshot = self.diagnostics_dir / f"{stem}.png"
        metadata = self.diagnostics_dir / f"{stem}.json"
        try:
            page.screenshot(path=str(screenshot), full_page=True)
        except Exception:
            pass
        payload = {
            "sid": study.sid,
            "aiCalcId": study.ai_calc_id,
            "attempt": attempt,
            "url": getattr(page, "url", ""),
            "errorType": type(error).__name__,
            "error": str(error),
        }
        metadata.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def download_with_retries(
    browser: PacsBrowser,
    study: Study,
    *,
    output_dir: str | Path,
    retries: int,
    overwrite: bool,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    pdf_dir = output_dir / "pdf"
    ss_dir = output_dir / "ss"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    ss_dir.mkdir(parents=True, exist_ok=True)

    pdf_target = pdf_dir / report_filename(study)
    screenshot_target = ss_dir / screenshot_filename(study)
    pdf_rel = f"pdf/{pdf_target.name}"
    ss_rel = f"ss/{screenshot_target.name}"

    if (
        pdf_target.exists()
        and screenshot_target.exists()
        and screenshot_target.stat().st_size > 0
        and not overwrite
    ):
        try:
            data = pdf_target.read_bytes()
            validate_pdf_bytes(data)
            return build_manifest_record(
                study,
                status="skipped",
                output=pdf_rel,
                screenshot=ss_rel,
                size=len(data),
                attempts=0,
                error=None,
            )
        except Exception:
            pass

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            current_ss_target = ss_dir / screenshot_filename(study)
            data = browser.download_report(study, screenshot_path=current_ss_target)

            pdf_target = pdf_dir / report_filename(study)
            final_ss_target = ss_dir / screenshot_filename(study)
            pdf_rel = f"pdf/{pdf_target.name}"
            ss_rel = f"ss/{final_ss_target.name}"

            if current_ss_target != final_ss_target and current_ss_target.exists():
                current_ss_target.replace(final_ss_target)

            atomic_save_pdf(pdf_target, data)
            return build_manifest_record(
                study,
                status="succeeded",
                output=pdf_rel,
                screenshot=ss_rel,
                size=len(data),
                attempts=attempt,
                error=None,
            )
        except Exception as exc:
            last_error = exc
            browser.capture_diagnostic(study, attempt, exc)

    return build_manifest_record(
        study,
        status="failed",
        output=None,
        screenshot=ss_rel if screenshot_target.exists() and screenshot_target.stat().st_size > 0 else None,
        size=None,
        attempts=retries,
        error=str(last_error) if last_error else "Unknown execution failure",
    )


def _merge_studies(*groups: Iterable[Study]) -> list[Study]:
    collector = StudyCollector(DEFAULT_BASE_URL)
    for group in groups:
        for study in group:
            collector._add(study)
    return collector.studies()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch-download Chest DR AI Image Reports from YiZhun AI-PACS."
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument(
        "--credentials",
        default="credential.txt",
        help="Path to env-style credential.txt (default: credential.txt)",
    )
    parser.add_argument("--output", default="reports")
    parser.add_argument(
        "--study",
        action="append",
        default=[],
        metavar="SID:AICALCID",
        help="Download an explicit study; repeat for more than one.",
    )
    parser.add_argument("--all", action="store_true", help="Discover and download all Chest DR studies.")
    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Discover Chest DR study mappings and print them without downloading.",
    )
    parser.add_argument("--headed", action="store_true", help="Show the Chromium browser window.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument("--storage-state", default="auth-state.json")
    parser.add_argument("--diagnostics", default="diagnostics")
    parser.add_argument("--probe-only", action="store_true", help="Only test HTTP reachability.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.retries < 1:
        parser.error("--retries must be at least 1")
    if args.timeout_ms < 1000:
        parser.error("--timeout-ms must be at least 1000")
    if not args.probe_only and not args.all and not args.study and not args.discover_only:
        parser.error("choose --all, --discover-only, or at least one --study SID:AICALCID")

    explicit = parse_explicit_studies(args.study) if args.study else []
    probe = probe_http_origin(args.base_url)
    print("PACS probe:", json.dumps(probe, ensure_ascii=False))
    if args.probe_only:
        return 0 if probe["ok"] else 2
    if not probe["ok"]:
        print(
            "PACS is not reachable from this machine. Run the script from the network/VPN/whitelisted "
            "machine that can open the PACS site.",
            file=sys.stderr,
        )
        return 2

    try:
        username, password = load_credentials(args.credentials)
    except Exception as exc:
        print(f"Credential error: {exc}", file=sys.stderr)
        return 2

    output_dir = Path(args.output)
    manifest_path = output_dir / "manifest.jsonl"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with PacsBrowser(
            base_url=args.base_url,
            username=username,
            password=password,
            storage_state=args.storage_state,
            diagnostics_dir=args.diagnostics,
            headed=args.headed,
            timeout_ms=args.timeout_ms,
        ) as pacs:
            pacs.login()
            discovered: list[Study] = []
            if args.all or args.discover_only:
                discovered = pacs.discover_studies()
                if not discovered:
                    raise RuntimeError(
                        "No trustworthy sid + aiCalcId pairs were discovered from the Chest DR list. "
                        "Run with --headed and inspect diagnostics/network behavior."
                    )
                print(f"Discovered {len(discovered)} study mapping(s).")

            if args.discover_only:
                print(
                    json.dumps(
                        [
                            {
                                "sid": study.sid,
                                "aiCalcId": study.ai_calc_id,
                                "patientId": study.patient_id,
                                "patientName": study.patient_name,
                            }
                            for study in discovered
                        ],
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0

            studies = _merge_studies(explicit, discovered if args.all else [])
            if not studies:
                raise RuntimeError("No studies selected")

            failed = 0
            for index, study in enumerate(studies, start=1):
                print(
                    f"[{index}/{len(studies)}] sid={study.sid} aiCalcId={study.ai_calc_id} ... ",
                    end="",
                    flush=True,
                )
                record = download_with_retries(
                    pacs,
                    study,
                    output_dir=output_dir,
                    retries=args.retries,
                    overwrite=args.overwrite,
                )
                append_manifest(manifest_path, record)
                print(f"{record['status']}" + (f" ({record['size']} bytes)" if record["size"] else ""))
                if record["status"] == "failed":
                    failed += 1

            print(f"Completed: {len(studies) - failed}/{len(studies)} without failure.")
            print(f"Manifest: {manifest_path}")
            return 1 if failed else 0
    except Exception as exc:
        print(f"Fatal: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
