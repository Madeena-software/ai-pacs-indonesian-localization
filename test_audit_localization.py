from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import openpyxl

from audit_localization import (
    Finding,
    classify_string,
    export_to_excel,
    generate_finding_id,
    load_credentials,
)


class TestAuditLocalizationOffline(unittest.TestCase):
    def test_load_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            env_file = dir_path / ".env"
            env_file.write_text("AI_PACS_USERNAME=user_env\nAI_PACS_PASSWORD=pass_env\n", encoding="utf-8")

            # Fallback to .env when credential.txt does not exist
            missing_cred = dir_path / "credential.txt"
            u, p = load_credentials(missing_cred)
            self.assertEqual(u, "user_env")
            self.assertEqual(p, "pass_env")

            # Direct load of .env file
            u2, p2 = load_credentials(env_file)
            self.assertEqual(u2, "user_env")
            self.assertEqual(p2, "pass_env")

            # Missing key error
            bad_env = dir_path / "bad.env"
            bad_env.write_text("AI_PACS_USERNAME=user_only\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_credentials(bad_env)

    def test_generate_finding_id(self) -> None:
        fid1 = generate_finding_id("login", "input#username", "Login")
        fid2 = generate_finding_id("login", "input#username", "Login")
        fid3 = generate_finding_id("doctor", "input#username", "Login")

        self.assertEqual(len(fid1), 16)
        self.assertEqual(fid1, fid2)
        self.assertNotEqual(fid1, fid3)

    def test_classify_string(self) -> None:
        # Technical terms & exclusions
        cls, exp, note = classify_string("AI")
        self.assertEqual(cls, "technical-term")

        cls, exp, note = classify_string("PACS")
        self.assertEqual(cls, "technical-term")

        cls, exp, note = classify_string("Window Leveling")
        self.assertEqual(cls, "technical-term")

        cls, exp, note = classify_string("123.45")
        self.assertEqual(cls, "technical-term")

        cls, exp, note = classify_string("2026-08-11")
        self.assertEqual(cls, "technical-term")

        # Not Indonesian (Chinese)
        cls, exp, note = classify_string("用户名")
        self.assertEqual(cls, "not-indonesian")
        self.assertEqual(exp, "Nama Pengguna")

        cls, exp, note = classify_string("登录")
        self.assertEqual(cls, "not-indonesian")
        self.assertEqual(exp, "Masuk")

        # Not Indonesian (English)
        cls, exp, note = classify_string("Login")
        self.assertEqual(cls, "not-indonesian")
        self.assertEqual(exp, "Masuk")

        cls, exp, note = classify_string("Download Report")
        self.assertEqual(cls, "not-indonesian")
        self.assertEqual(exp, "Unduh Laporan")

        cls, exp, note = classify_string("Doctor")
        self.assertEqual(cls, "not-indonesian")
        self.assertEqual(exp, "Dokter")

        cls, exp, note = classify_string("Sex")
        self.assertEqual(cls, "not-indonesian")
        self.assertEqual(exp, "Jenis Kelamin")

        # Mixed
        cls, exp, note = classify_string("Unduh Report")
        self.assertEqual(cls, "mixed")
        self.assertEqual(exp, "Unduh Laporan")

        # Quality issue
        cls, exp, note = classify_string("Masukan kata sandi")
        self.assertEqual(cls, "quality-issue")
        self.assertEqual(exp, "Masukkan kata sandi")
        self.assertTrue(len(note) > 0)

        # Valid Indonesian (excluded from findings)
        cls, exp, note = classify_string("Nama Pengguna")
        self.assertEqual(cls, "technical-term")

        cls, exp, note = classify_string("Masuk")
        self.assertEqual(cls, "technical-term")

        cls, exp, note = classify_string("Waktu penerimaan")
        self.assertEqual(cls, "technical-term")

        cls, exp, note = classify_string("Tidak ada kasus ditemukan")
        self.assertEqual(cls, "technical-term")

    # --- Remediation AC-13 test cases ---

    def test_classify_string_remediation(self) -> None:
        """AC-13: Verify R-D3, R-D4 classification fixes."""

        # R-D4: Insight must be a technical-term (product name)
        cls, exp, note = classify_string("Insight")
        self.assertEqual(cls, "technical-term", "'Insight' is a product name and must not be a finding")

        # R-D3: Language must return expected_indonesian = "Bahasa"
        cls, exp, note = classify_string("Language")
        self.assertEqual(cls, "not-indonesian")
        self.assertEqual(exp, "Bahasa")
        self.assertTrue(len(note) > 0, "quality_note must be populated")

    def test_deduplication_keys(self) -> None:
        seen = set()
        key1 = ("login", "input#username", "Login")
        key2 = ("login", "input#username", "Login")
        key3 = ("doctor", "button#submit", "Login")

        seen.add(key1)
        self.assertIn(key2, seen)

        seen.add(key3)
        self.assertEqual(len(seen), 2)

    def test_export_to_excel_schema(self) -> None:
        findings = [
            Finding(
                finding_id="1a2b3c4d5e6f7g8h",
                route="login",
                module_name="Authentication",
                page_url="http://124.225.183.175:8361/#/login",
                page_title="AI-PACS Login",
                element_selector="button.login-btn",
                text_observed="Login",
                classification="not-indonesian",
                expected_indonesian="Masuk",
                quality_note="",
                screenshot_path="screenshots/login_001_1a2b3c4d.png",
                fullpage_screenshot_path="screenshots/fullpage_login.png",
            )
        ]
        summary = {
            "run_timestamp": "2026-08-11T00:00:00Z",
            "base_url": "http://124.225.183.175:8361",
            "routes_visited": 1,
            "strings_inspected": 10,
            "findings_total": 1,
            "findings_not_indonesian": 1,
            "findings_mixed": 0,
            "findings_quality_issue": 0,
            "findings_uncertain": 0,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "test_report.xlsx"
            export_to_excel(findings, summary, out_file)

            self.assertTrue(out_file.is_file())
            wb = openpyxl.load_workbook(out_file)

            self.assertEqual(set(wb.sheetnames), {"Findings", "Summary"})

            # Verify Findings Sheet
            ws_f = wb["Findings"]
            headers_f = [cell.value for cell in ws_f[1]]
            expected_f_headers = [
                "finding_id",
                "route",
                "module_name",
                "page_url",
                "page_title",
                "element_selector",
                "text_observed",
                "classification",
                "expected_indonesian",
                "quality_note",
                "screenshot_image",
                "fullpage_screenshot_image",
            ]
            self.assertEqual(headers_f, expected_f_headers)

            row2_f = [cell.value for cell in ws_f[2]]
            self.assertEqual(row2_f[0], "1a2b3c4d5e6f7g8h")
            self.assertEqual(row2_f[1], "login")
            self.assertEqual(row2_f[2], "Authentication")
            self.assertEqual(row2_f[3], "http://124.225.183.175:8361/#/login")
            self.assertEqual(row2_f[4], "AI-PACS Login")
            self.assertEqual(row2_f[6], "Login")
            self.assertEqual(row2_f[7], "not-indonesian")
            self.assertEqual(row2_f[8], "Masuk")

            # Verify Summary Sheet
            ws_s = wb["Summary"]
            headers_s = [cell.value for cell in ws_s[1]]
            expected_s_headers = [
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
            self.assertEqual(headers_s, expected_s_headers)

            row2_s = [cell.value for cell in ws_s[2]]
            self.assertEqual(row2_s[2], 1)
            self.assertEqual(row2_s[3], 10)
            self.assertEqual(row2_s[4], 1)


if __name__ == "__main__":
    unittest.main()
