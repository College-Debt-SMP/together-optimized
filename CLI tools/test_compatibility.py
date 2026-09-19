#!/usr/bin/env python3
"""Unit tests for mod compatibility checking and version constraints."""

import unittest
import sys
from pathlib import Path

# Add CLI tools to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import importlib
update_fork_mods = importlib.import_module("update-fork-mods")

parse_version = update_fork_mods.parse_version
compare_versions = update_fork_mods.compare_versions
check_constraint = update_fork_mods.check_constraint
check_mod_compatibility = update_fork_mods.check_mod_compatibility


class TestVersionParsingAndComparison(unittest.TestCase):
    def test_parse_version(self):
        self.assertEqual(parse_version("0.9.2+mc26.2"), ([0, 9, 2], None))
        self.assertEqual(parse_version("0.9.2-beta.1+mc26.1.2"), ([0, 9, 2], "beta.1"))
        self.assertEqual(parse_version("1.14.1+kotlin.2.4.20"), ([1, 14, 1], None))
        self.assertEqual(parse_version("26.2.155"), ([26, 2, 155], None))

    def test_compare_versions(self):
        self.assertEqual(compare_versions("0.9.1", "0.9.2"), -1)
        self.assertEqual(compare_versions("0.9.2", "0.9.1"), 1)
        self.assertEqual(compare_versions("0.9.2", "0.9.2"), 0)
        self.assertEqual(compare_versions("0.9.2+mc26.2", "0.9.2"), 0)
        # Prerelease is lower than release
        self.assertEqual(compare_versions("0.9.2-beta.1", "0.9.2"), -1)
        self.assertEqual(compare_versions("0.9.2", "0.9.2-beta.1"), 1)

    def test_check_constraint_exact(self):
        self.assertTrue(check_constraint("0.9.1", "0.9.1"))
        self.assertTrue(check_constraint("0.9.1+build.1", "=0.9.1"))
        self.assertFalse(check_constraint("0.9.2", "0.9.1"))

    def test_check_constraint_operators(self):
        self.assertTrue(check_constraint("0.9.2", ">=0.9.1"))
        self.assertTrue(check_constraint("0.9.2", ">0.9.1"))
        self.assertFalse(check_constraint("0.9.2", "<=0.9.1"))
        self.assertFalse(check_constraint("0.9.2", "<0.9.2"))
        self.assertTrue(check_constraint("0.9.2", "<=0.9.2"))
        self.assertTrue(check_constraint("0.9.2", "*"))

    def test_check_constraint_tilde(self):
        self.assertTrue(check_constraint("0.9.1", "~0.9.1"))
        self.assertTrue(check_constraint("0.9.9", "~0.9.1"))
        self.assertFalse(check_constraint("0.10.0", "~0.9.1"))

    def test_check_constraint_disjunction(self):
        spec = ["=0.9.1", ">=0.9.2- <=0.9.2"]
        self.assertTrue(check_constraint("0.9.1", spec))
        self.assertTrue(check_constraint("0.9.2", spec))
        self.assertTrue(check_constraint("0.9.2+mc26.2", spec))
        self.assertFalse(check_constraint("0.9.3", spec))
        self.assertFalse(check_constraint("0.9.0", spec))

    def test_check_constraint_nvidium_sodium_conflict(self):
        nvidium_spec = ["0.9.1"]
        self.assertTrue(check_constraint("0.9.1", nvidium_spec))
        self.assertFalse(check_constraint("0.9.2", nvidium_spec))
        self.assertFalse(check_constraint("0.9.2+mc26.2", nvidium_spec))


class TestCompatibilityChecker(unittest.TestCase):
    def setUp(self):
        self.installed = {
            "AANobbMI": {
                "name": "Sodium",
                "stem": "sodium",
                "version_id": "xJZxADzI",
                "filename": "sodium-fabric-0.9.2+mc26.2.jar",
                "url": None,
            },
            "P7dR8mSH": {
                "name": "Fabric API",
                "stem": "fabric-api",
                "version_id": "fabric_api_ver_1",
                "filename": "fabric-api-0.160.0+26.2.jar",
                "url": None,
            },
        }

    def test_incompatible_dependency_type(self):
        candidate = {
            "dependencies": [
                {
                    "project_id": "AANobbMI",
                    "version_id": None,
                    "dependency_type": "incompatible",
                }
            ],
            "files": [],
        }
        conflicts = check_mod_compatibility(candidate, self.installed)
        self.assertEqual(len(conflicts), 1)
        self.assertIn("incompatible with installed mod 'Sodium'", conflicts[0])

    def test_compatible_unpinned_required_dependency(self):
        candidate = {
            "dependencies": [
                {
                    "project_id": "P7dR8mSH",
                    "version_id": None,
                    "dependency_type": "required",
                }
            ],
            "files": [],
        }
        conflicts = check_mod_compatibility(candidate, self.installed)
        self.assertEqual(conflicts, [])

    def test_matching_pinned_required_dependency(self):
        candidate = {
            "dependencies": [
                {
                    "project_id": "AANobbMI",
                    "version_id": "xJZxADzI",
                    "dependency_type": "required",
                }
            ],
            "files": [],
        }
        conflicts = check_mod_compatibility(candidate, self.installed)
        self.assertEqual(conflicts, [])

    def test_mismatched_pinned_required_dependency_without_jar(self):
        candidate = {
            "dependencies": [
                {
                    "project_id": "AANobbMI",
                    "version_id": "2Yom1N68",
                    "dependency_type": "required",
                }
            ],
            "files": [],
        }
        conflicts = check_mod_compatibility(candidate, self.installed)
        self.assertEqual(len(conflicts), 1)
        self.assertIn("requires Sodium version 2Yom1N68, but installed is xJZxADzI", conflicts[0])


if __name__ == "__main__":
    unittest.main()
