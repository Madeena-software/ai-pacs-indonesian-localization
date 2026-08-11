from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pacs_batch import (
    Study,
    StudyCollector,
    atomic_save_pdf,
    build_manifest_record,
    build_viewer_url,
    extract_studies_from_hrefs,
    extract_studies_from_json,
    load_credentials,
    parse_explicit_studies,
    report_filename,
    safe_filename,
    screenshot_filename,
    study_stem,
    validate_pdf_bytes,
)


class TestPacsBatchOffline(unittest.TestCase):
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
    def test_study_dataclass(self) -> None:
        s1 = Study(sid=33, ai_calc_id=48, patient_id="P1", patient_name="Name1")
        s2 = Study(sid=33, ai_calc_id=48, patient_id="P2", patient_name="Name2")
        self.assertEqual(s1, s2)
        s3 = Study(sid=34, ai_calc_id=10)
        self.assertLess(s1, s3)

    def test_safe_filename(self) -> None:
        self.assertEqual(safe_filename("02-WCI-02B_Thorax_PA"), "02-WCI-02B_Thorax_PA")
        self.assertEqual(safe_filename("John/Doe:Test?*"), "John_Doe_Test__")
        self.assertEqual(safe_filename("  trailing.  "), "trailing")

    def test_study_stem(self) -> None:
        # Patient name present
        study1 = Study(sid=33, ai_calc_id=48, patient_name="02-WCI-02B_Thorax_PA")
        self.assertEqual(study_stem(study1), "02-WCI-02B_Thorax_PA__sid-33__ai-48")
        self.assertEqual(report_filename(study1), "02-WCI-02B_Thorax_PA__sid-33__ai-48.pdf")
        self.assertEqual(screenshot_filename(study1), "02-WCI-02B_Thorax_PA__sid-33__ai-48.png")

        # Patient name with invalid filesystem characters
        study2 = Study(sid=33, ai_calc_id=48, patient_name="John/Doe:123")
        self.assertEqual(study_stem(study2), "John_Doe_123__sid-33__ai-48")

        # Empty / missing patient name fallback
        study3 = Study(sid=58, ai_calc_id=50, patient_name="")
        self.assertEqual(study_stem(study3), "CR-58-AI-50")
        self.assertEqual(report_filename(study3), "CR-58-AI-50.pdf")
        self.assertEqual(screenshot_filename(study3), "CR-58-AI-50.png")

        # Whitespace patient name fallback
        study4 = Study(sid=12, ai_calc_id=34, patient_name="   ")
        self.assertEqual(study_stem(study4), "CR-12-AI-34")

        # Duplicate patient names across different studies produce distinct stems
        study5a = Study(sid=10, ai_calc_id=1, patient_name="Same Patient")
        study5b = Study(sid=11, ai_calc_id=2, patient_name="Same Patient")
        self.assertNotEqual(study_stem(study5a), study_stem(study5b))

    def test_extract_studies_from_json(self) -> None:
        payload = {
            "code": 200,
            "data": {
                "records": [
                    {
                        "sid": "58",
                        "aiCalcId": 50,
                        "patientId": "PID123",
                        "patientName": "Test Patient",
                    },
                    {
                        "studyId": 99,
                        "aicalcid": 100,
                        "patient_id": "PID456",
                        "patient_name": "Another Patient",
                    },
                ]
            },
        }
        extracted = extract_studies_from_json(payload)
        self.assertEqual(len(extracted), 2)
        self.assertEqual(extracted[0], Study(sid=58, ai_calc_id=50, patient_id="PID123", patient_name="Test Patient"))
        self.assertEqual(extracted[1], Study(sid=99, ai_calc_id=100, patient_id="PID456", patient_name="Another Patient"))

    def test_extract_studies_from_hrefs(self) -> None:
        hrefs = [
            "/view/dr/index.html/viewer?action=viewer&type=CR&sid=58&pacs=fei&aiCalcId=50",
            "/view/dr/index.html/viewer?action=viewer&type=CR&sid=99&pacs=fei&aiCalcId=100",
            "http://example.com/other",
        ]
        extracted = extract_studies_from_hrefs(hrefs, "http://124.225.183.175:8361")
        self.assertEqual(len(extracted), 2)
        self.assertEqual(extracted[0].sid, 58)
        self.assertEqual(extracted[0].ai_calc_id, 50)

    def test_study_collector(self) -> None:
        collector = StudyCollector("http://124.225.183.175:8361")
        collector.add_hrefs(["/view/dr/index.html/viewer?action=viewer&type=CR&sid=58&pacs=fei&aiCalcId=50"])
        collector.add_json({"sid": 58, "aiCalcId": 50, "patientId": "P58", "patientName": "Patient 58"})
        studies = collector.studies()
        self.assertEqual(len(studies), 1)
        self.assertEqual(studies[0].patient_name, "Patient 58")

    def test_build_viewer_url(self) -> None:
        url = build_viewer_url("http://124.225.183.175:8361", Study(sid=58, ai_calc_id=50))
        self.assertIn("sid=58", url)
        self.assertIn("aiCalcId=50", url)
        self.assertIn("view/dr/index.html/viewer", url)

    def test_validate_pdf_bytes(self) -> None:
        valid_pdf = b"%PDF-1.4\n" + b"x" * 1020 + b"\n%%EOF\n"
        validate_pdf_bytes(valid_pdf)

        with self.assertRaises(ValueError):
            validate_pdf_bytes(b"NOT A PDF")

        with self.assertRaises(ValueError):
            validate_pdf_bytes(b"%PDF-1.4 short")

        with self.assertRaises(ValueError):
            validate_pdf_bytes(b"%PDF-1.4\n" + b"x" * 1020 + b"\nNO EOF\n")

    def test_atomic_save_pdf(self) -> None:
        valid_pdf = b"%PDF-1.4\n" + b"x" * 1020 + b"\n%%EOF\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.pdf"
            atomic_save_pdf(path, valid_pdf)
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_bytes(), valid_pdf)

    def test_build_manifest_record(self) -> None:
        study = Study(sid=33, ai_calc_id=48, patient_id="P33", patient_name="Name33")
        record = build_manifest_record(
            study,
            status="succeeded",
            output="Name33__sid-33__ai-48.pdf",
            screenshot="Name33__sid-33__ai-48.png",
            size=2048,
            attempts=1,
            error=None,
        )
        self.assertEqual(record["sid"], 33)
        self.assertEqual(record["aiCalcId"], 48)
        self.assertEqual(record["patientName"], "Name33")
        self.assertEqual(record["status"], "succeeded")
        self.assertEqual(record["output"], "Name33__sid-33__ai-48.pdf")
        self.assertEqual(record["screenshot"], "Name33__sid-33__ai-48.png")

    def test_parse_explicit_studies(self) -> None:
        parsed = parse_explicit_studies(["58:50", "33:48:Patient Name"])
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0], Study(sid=58, ai_calc_id=50, patient_name=""))
        self.assertEqual(parsed[1], Study(sid=33, ai_calc_id=48, patient_name="Patient Name"))


if __name__ == "__main__":
    unittest.main()
