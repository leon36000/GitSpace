from __future__ import annotations

import unittest

from sonar_evidence_gate import EvidenceError, classify_sonar_evidence


class SonarEvidenceGateTests(unittest.TestCase):
    def test_successful_quality_gate_is_pass(self) -> None:
        state = classify_sonar_evidence(
            check={
                "status": "completed",
                "conclusion": "success",
                "annotations_count": 0,
            },
            quality={"http_status": 200, "status": "OK"},
            issues={"http_status": 200, "total": 0},
        )
        self.assertEqual(state, "PASS")

    def test_missing_external_analysis_is_not_computed_not_pass(self) -> None:
        for issues in (
            {"http_status": 404, "total": None},
            {"http_status": 200, "total": 0},
        ):
            with self.subTest(issues=issues):
                state = classify_sonar_evidence(
                    check={
                        "status": "completed",
                        "conclusion": "cancelled",
                        "annotations_count": 0,
                    },
                    quality={"http_status": 404, "status": None},
                    issues=issues,
                )
                self.assertEqual(state, "NOT_COMPUTED_EXTERNAL")

    def test_annotations_are_a_material_finding(self) -> None:
        with self.assertRaises(EvidenceError):
            classify_sonar_evidence(
                check={
                    "status": "completed",
                    "conclusion": "cancelled",
                    "annotations_count": 1,
                },
                quality={"http_status": 404, "status": None},
                issues={"http_status": 404, "total": None},
            )

    def test_open_issues_are_a_material_finding(self) -> None:
        with self.assertRaises(EvidenceError):
            classify_sonar_evidence(
                check={
                    "status": "completed",
                    "conclusion": "success",
                    "annotations_count": 0,
                },
                quality={"http_status": 200, "status": "OK"},
                issues={"http_status": 200, "total": 1},
            )

    def test_failed_or_error_quality_gate_fails_closed(self) -> None:
        for quality in (
            {"http_status": 200, "status": "ERROR"},
            {"http_status": 500, "status": None},
        ):
            with self.subTest(quality=quality):
                with self.assertRaises(EvidenceError):
                    classify_sonar_evidence(
                        check={
                            "status": "completed",
                            "conclusion": "failure",
                            "annotations_count": 0,
                        },
                        quality=quality,
                        issues={"http_status": 200, "total": 0},
                    )

    def test_cancelled_check_with_computed_gate_is_not_accepted(self) -> None:
        with self.assertRaises(EvidenceError):
            classify_sonar_evidence(
                check={
                    "status": "completed",
                    "conclusion": "cancelled",
                    "annotations_count": 0,
                },
                quality={"http_status": 200, "status": "OK"},
                issues={"http_status": 200, "total": 0},
            )

    def test_incomplete_check_fails_closed(self) -> None:
        with self.assertRaises(EvidenceError):
            classify_sonar_evidence(
                check={
                    "status": "in_progress",
                    "conclusion": None,
                    "annotations_count": 0,
                },
                quality={"http_status": 404, "status": None},
                issues={"http_status": 404, "total": None},
            )


if __name__ == "__main__":
    unittest.main()
