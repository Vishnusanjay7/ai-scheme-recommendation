import sqlite3
import unittest


class TestRelationalLogicAndConstraints(unittest.TestCase):
    """
    Validates relational schema behavior, integrity constraints, and cascade logic.
    Simulates the exact relational constraints defined in database/schema.sql.
    """

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.conn.cursor()

        # Build schema tables matching database/schema.sql
        self.cursor.executescript("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE districts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_id INTEGER NOT NULL REFERENCES states(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (state_id, name)
        );

        CREATE TABLE user_profiles (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            age INTEGER CHECK (age >= 0 AND age <= 150),
            gender TEXT CHECK (gender IN ('MALE', 'FEMALE', 'TRANSGENDER', 'OTHER')),
            state_id INTEGER REFERENCES states(id) ON DELETE SET NULL,
            district_id INTEGER REFERENCES districts(id) ON DELETE SET NULL,
            annual_income NUMERIC(12, 2) CHECK (annual_income >= 0),
            occupation TEXT,
            education TEXT,
            category TEXT,
            disability_status BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE scheme_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE schemes (
            id TEXT PRIMARY KEY,
            scheme_name TEXT NOT NULL,
            description TEXT,
            government_level TEXT NOT NULL CHECK (government_level IN ('CENTRAL', 'STATE')),
            state_id INTEGER REFERENCES states(id) ON DELETE SET NULL,
            category_id INTEGER REFERENCES scheme_categories(id) ON DELETE SET NULL,
            benefits TEXT,
            application_process TEXT,
            start_date DATE,
            last_date DATE,
            status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'EXPIRED')),
            official_url TEXT,
            source_url TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT chk_central_or_state CHECK (
                (government_level = 'CENTRAL') OR
                (government_level = 'STATE' AND state_id IS NOT NULL)
            )
        );

        CREATE TABLE scheme_eligibility (
            id TEXT PRIMARY KEY,
            scheme_id TEXT NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
            min_age INTEGER CHECK (min_age >= 0),
            max_age INTEGER CHECK (max_age IS NULL OR min_age IS NULL OR max_age >= min_age),
            max_income NUMERIC(12, 2) CHECK (max_income >= 0),
            gender TEXT CHECK (gender IN ('ALL', 'MALE', 'FEMALE', 'TRANSGENDER', 'OTHER') OR gender IS NULL),
            occupation TEXT,
            education TEXT,
            category TEXT,
            disability_required BOOLEAN NOT NULL DEFAULT 0,
            state_restriction INTEGER REFERENCES states(id) ON DELETE SET NULL,
            district_restriction INTEGER REFERENCES districts(id) ON DELETE SET NULL,
            other_conditions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE scheme_documents (
            id TEXT PRIMARY KEY,
            scheme_id TEXT NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
            document_name TEXT NOT NULL,
            mandatory BOOLEAN NOT NULL DEFAULT 1,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE scheme_sources (
            id TEXT PRIMARY KEY,
            scheme_id TEXT NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
            source_url TEXT NOT NULL,
            source_type TEXT,
            last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE saved_schemes (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            scheme_id TEXT NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, scheme_id)
        );

        CREATE TABLE notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            scheme_id TEXT REFERENCES schemes(id) ON DELETE SET NULL,
            message TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            scheduled_at TIMESTAMP,
            sent_at TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'SENT', 'FAILED', 'CANCELLED')),
            is_read BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE chat_history (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'en',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

    def tearDown(self):
        self.conn.close()

    def test_state_district_relationship(self):
        """Test states 1:N districts and cascade deletion."""
        self.cursor.execute("INSERT INTO states (id, name, code) VALUES (1, 'Tamil Nadu', 'TN');")
        self.cursor.execute("INSERT INTO districts (state_id, name, code) VALUES (1, 'Chennai', 'CHN');")
        self.cursor.execute("INSERT INTO districts (state_id, name, code) VALUES (1, 'Coimbatore', 'CBE');")

        # Verify duplicate district name in same state fails
        with self.assertRaises(sqlite3.IntegrityError):
            self.cursor.execute("INSERT INTO districts (state_id, name, code) VALUES (1, 'Chennai', 'CHN2');")

        # Verify cascade delete
        self.cursor.execute("DELETE FROM states WHERE id = 1;")
        self.cursor.execute("SELECT count(*) FROM districts WHERE state_id = 1;")
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 0)

    def test_user_profile_one_to_one(self):
        """Test users 1:1 user_profiles relationship and unique constraint."""
        self.cursor.execute("INSERT INTO users (id, email, full_name) VALUES ('u1', 'citizen@example.com', 'A Citizen');")
        self.cursor.execute("INSERT INTO user_profiles (id, user_id, age, gender, annual_income) VALUES ('p1', 'u1', 30, 'MALE', 250000);")

        # Attempting second profile for same user must fail
        with self.assertRaises(sqlite3.IntegrityError):
            self.cursor.execute("INSERT INTO user_profiles (id, user_id, age, gender) VALUES ('p2', 'u1', 25, 'FEMALE');")

    def test_central_vs_state_scheme_constraints(self):
        """Test central schemes allow state_id NULL, while state schemes require state_id NOT NULL."""
        self.cursor.execute("INSERT INTO states (id, name, code) VALUES (1, 'Tamil Nadu', 'TN');")

        # Central scheme with NULL state_id is allowed
        self.cursor.execute("""
            INSERT INTO schemes (id, scheme_name, government_level, state_id)
            VALUES ('s-central', 'PM-Kisan', 'CENTRAL', NULL);
        """)

        # State scheme with valid state_id is allowed
        self.cursor.execute("""
            INSERT INTO schemes (id, scheme_name, government_level, state_id)
            VALUES ('s-state', 'Kalaignar Magalir Urimai', 'STATE', 1);
        """)

        # State scheme with NULL state_id must fail constraint check
        with self.assertRaises(sqlite3.IntegrityError):
            self.cursor.execute("""
                INSERT INTO schemes (id, scheme_name, government_level, state_id)
                VALUES ('s-invalid', 'Invalid State Scheme', 'STATE', NULL);
            """)

    def test_saved_schemes_uniqueness(self):
        """Test user cannot save the same scheme twice."""
        self.cursor.execute("INSERT INTO users (id, email) VALUES ('u1', 'c1@test.com');")
        self.cursor.execute("INSERT INTO schemes (id, scheme_name, government_level) VALUES ('s1', 'Test Scheme', 'CENTRAL');")

        self.cursor.execute("INSERT INTO saved_schemes (id, user_id, scheme_id) VALUES ('ss1', 'u1', 's1');")

        with self.assertRaises(sqlite3.IntegrityError):
            self.cursor.execute("INSERT INTO saved_schemes (id, user_id, scheme_id) VALUES ('ss2', 'u1', 's1');")

    def test_scheme_cascading_deletions(self):
        """Test scheme deletion cascades to eligibility, documents, sources, and saved_schemes."""
        self.cursor.execute("INSERT INTO users (id, email) VALUES ('u1', 'c1@test.com');")
        self.cursor.execute("INSERT INTO schemes (id, scheme_name, government_level) VALUES ('s1', 'Test Scheme', 'CENTRAL');")
        self.cursor.execute("INSERT INTO scheme_eligibility (id, scheme_id, min_age, max_age) VALUES ('e1', 's1', 18, 60);")
        self.cursor.execute("INSERT INTO scheme_documents (id, scheme_id, document_name) VALUES ('d1', 's1', 'Aadhaar');")
        self.cursor.execute("INSERT INTO scheme_sources (id, scheme_id, source_url) VALUES ('src1', 's1', 'https://example.gov.in');")
        self.cursor.execute("INSERT INTO saved_schemes (id, user_id, scheme_id) VALUES ('ss1', 'u1', 's1');")
        self.cursor.execute("INSERT INTO notifications (id, user_id, scheme_id, message, notification_type) VALUES ('n1', 'u1', 's1', 'Alert', 'DEADLINE');")

        # Delete scheme
        self.cursor.execute("DELETE FROM schemes WHERE id = 's1';")

        self.cursor.execute("SELECT count(*) FROM scheme_eligibility WHERE scheme_id = 's1';")
        self.assertEqual(self.cursor.fetchone()[0], 0)

        self.cursor.execute("SELECT count(*) FROM scheme_documents WHERE scheme_id = 's1';")
        self.assertEqual(self.cursor.fetchone()[0], 0)

        self.cursor.execute("SELECT count(*) FROM scheme_sources WHERE scheme_id = 's1';")
        self.assertEqual(self.cursor.fetchone()[0], 0)

        self.cursor.execute("SELECT count(*) FROM saved_schemes WHERE scheme_id = 's1';")
        self.assertEqual(self.cursor.fetchone()[0], 0)

        # Notification scheme_id is SET NULL on scheme delete
        self.cursor.execute("SELECT scheme_id FROM notifications WHERE id = 'n1';")
        self.assertIsNone(self.cursor.fetchone()[0])


if __name__ == "__main__":
    unittest.main()
