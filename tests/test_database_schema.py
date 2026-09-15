import os
import re
import unittest
from pathlib import Path


class TestDatabaseSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_path = Path(__file__).resolve().parent.parent / "database" / "schema.sql"
        with open(cls.schema_path, "r", encoding="utf-8") as f:
            cls.schema_sql = f.read()

    def test_schema_file_exists(self):
        """Verify database/schema.sql exists and is non-empty."""
        self.assertTrue(self.schema_path.exists(), "database/schema.sql must exist")
        self.assertGreater(len(self.schema_sql), 100, "schema.sql must not be empty")

    def test_all_twelve_tables_present(self):
        """Confirm all 12 required application tables are created."""
        expected_tables = [
            "users",
            "user_profiles",
            "states",
            "districts",
            "scheme_categories",
            "schemes",
            "scheme_eligibility",
            "scheme_documents",
            "scheme_sources",
            "saved_schemes",
            "notifications",
            "chat_history",
        ]
        for table in expected_tables:
            pattern = rf"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?{table}\b"
            match = re.search(pattern, self.schema_sql, re.IGNORECASE)
            self.assertIsNotNone(match, f"Table '{table}' definition was not found in schema.sql")

    def test_rls_enabled_on_all_twelve_tables(self):
        """Confirm ROW LEVEL SECURITY is enabled on all 12 application tables."""
        expected_tables = [
            "users",
            "user_profiles",
            "states",
            "districts",
            "scheme_categories",
            "schemes",
            "scheme_eligibility",
            "scheme_documents",
            "scheme_sources",
            "saved_schemes",
            "notifications",
            "chat_history",
        ]
        for table in expected_tables:
            pattern = rf"ALTER\s+TABLE\s+(?:public\.)?{table}\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY"
            match = re.search(pattern, self.schema_sql, re.IGNORECASE)
            self.assertIsNotNone(match, f"RLS must be enabled on table '{table}'")

    def test_rls_private_tables_security(self):
        """Confirm private tables enforce auth.uid() and never use insecure USING (true)."""
        private_tables = [
            "users",
            "user_profiles",
            "saved_schemes",
            "notifications",
            "chat_history",
        ]
        for table in private_tables:
            # Find all policy definitions for this table
            policy_pattern = rf"CREATE\s+POLICY\s+\"[^\"]+\"\s+ON\s+(?:public\.)?{table}[\s\S]*?;"
            policies = re.findall(policy_pattern, self.schema_sql, re.IGNORECASE)
            self.assertGreater(len(policies), 0, f"Table '{table}' must have RLS policies defined")

            for policy in policies:
                # Private tables must never contain USING (true)
                self.assertNotIn(
                    "USING (true)",
                    re.sub(r"\s+", " ", policy.strip()),
                    f"Private table '{table}' has insecure 'USING (true)' in policy: {policy}",
                )
                # Policies on private tables must reference auth.uid()
                self.assertIn(
                    "auth.uid()",
                    policy,
                    f"Policy on private table '{table}' must reference auth.uid(): {policy}",
                )

    def test_rls_public_tables_readable(self):
        """Confirm public reference and scheme tables permit public SELECT access."""
        public_tables = [
            "states",
            "districts",
            "scheme_categories",
            "schemes",
            "scheme_eligibility",
            "scheme_documents",
            "scheme_sources",
        ]
        for table in public_tables:
            pattern = rf"CREATE\s+POLICY\s+\"[^\"]+\"\s+ON\s+(?:public\.)?{table}\s+FOR\s+SELECT\s+USING\s*\(\s*true\s*\)"
            match = re.search(pattern, self.schema_sql, re.IGNORECASE)
            self.assertIsNotNone(match, f"Table '{table}' must have public SELECT policy with USING (true)")

    def test_required_indexes(self):
        """Confirm all 17 required indexes are explicitly defined in schema.sql."""
        required_indexes = [
            "idx_user_profiles_user_id",
            "idx_user_profiles_state_id",
            "idx_user_profiles_district_id",
            "idx_districts_state_id",
            "idx_schemes_state_id",
            "idx_schemes_government_level",
            "idx_schemes_category_id",
            "idx_schemes_status",
            "idx_schemes_last_date",
            "idx_scheme_eligibility_scheme_id",
            "idx_scheme_documents_scheme_id",
            "idx_scheme_sources_scheme_id",
            "idx_saved_schemes_user_id",
            "idx_saved_schemes_scheme_id",
            "idx_notifications_user_id",
            "idx_notifications_scheme_id",
            "idx_chat_history_user_id",
        ]
        for idx in required_indexes:
            self.assertIn(idx, self.schema_sql, f"Required index '{idx}' not found in schema.sql")

    def test_central_vs_state_scheme_constraint(self):
        """Verify constraint enforcing CENTRAL schemes (state_id nullable) and STATE schemes (state_id NOT NULL)."""
        self.assertIn("chk_central_or_state_validity", self.schema_sql)
        self.assertIn("CENTRAL", self.schema_sql)
        self.assertIn("STATE", self.schema_sql)

    def test_user_profiles_one_to_one_constraint(self):
        """Verify user_profiles has unique foreign key to users ensuring 1:1 relationship."""
        profile_block = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?user_profiles\s*\(([\s\S]*?)\);", self.schema_sql, re.IGNORECASE)
        self.assertIsNotNone(profile_block, "user_profiles table block not found")
        content = profile_block.group(1)
        self.assertTrue(
            re.search(r"user_id\s+UUID\s+NOT\s+NULL\s+UNIQUE\s+REFERENCES", content, re.IGNORECASE) is not None,
            "user_id in user_profiles must be NOT NULL UNIQUE REFERENCES public.users(id)",
        )

    def test_saved_schemes_unique_constraint(self):
        """Verify saved_schemes prevents saving the same scheme twice per user."""
        self.assertIn("uq_user_saved_scheme", self.schema_sql)

    def test_indian_states_and_uts_seeded(self):
        """Verify all 28 states and 8 UTs (36 total) are seeded in states table."""
        expected_state_codes = [
            "AP", "AR", "AS", "BR", "CG", "GA", "GJ", "HR", "HP", "JH",
            "KA", "KL", "MP", "MH", "MN", "ML", "MZ", "NL", "OD", "PB",
            "RJ", "SK", "TN", "TS", "TR", "UP", "UK", "WB", "AN", "CH",
            "DN", "DL", "JK", "LA", "LD", "PY",
        ]
        self.assertEqual(len(expected_state_codes), 36)
        for code in expected_state_codes:
            pattern = rf"'\b{code}\b'"
            self.assertIsNotNone(
                re.search(pattern, self.schema_sql),
                f"State / UT code '{code}' was not found in states seed data",
            )

    def test_scheme_categories_seeded(self):
        """Verify official scheme categories are seeded."""
        categories = [
            "Agriculture, Rural & Environment",
            "Education & Learning",
            "Health & Wellness",
            "Skills & Employment",
            "Women and Child Development",
        ]
        for cat in categories:
            self.assertIn(cat, self.schema_sql, f"Category '{cat}' missing from schema seed")


if __name__ == "__main__":
    unittest.main()
