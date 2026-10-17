
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "trust_juggler.db"


def get_connection():
    """Create a connection to the existing SQLite database."""
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10,
    )
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create required tables if they do not already exist."""

    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS riders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rider_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                face_enrolled INTEGER DEFAULT 0,
                fingerprint_enrolled INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS verification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rider_id TEXT NOT NULL,
                method TEXT NOT NULL,
                result TEXT NOT NULL,
                risk_score INTEGER DEFAULT 0,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS security_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rider_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                description TEXT NOT NULL,
                risk_score INTEGER DEFAULT 0,
                resolved INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def add_rider(rider_id, full_name, email):
    """Register a rider; reject duplicate IDs and emails."""

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO riders (rider_id, full_name, email)
            VALUES (?, ?, ?)
            """,
            (rider_id, full_name, email),
        )


def get_riders():
    """Return registered riders, newest first."""

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM riders
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()


def add_verification_log(
    rider_id,
    method,
    result,
    risk_score=0,
    details="",
):
    """Save a verification attempt and its risk assessment."""

    risk_score = max(0, min(100, int(risk_score)))

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO verification_logs
                (rider_id, method, result, risk_score, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (rider_id, method, result, risk_score, details),
        )


def get_verification_logs(limit=100):
    """Return recent verification attempts."""

    limit = max(1, min(1000, int(limit)))

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM verification_logs
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def add_security_alert(
    rider_id,
    alert_type,
    description,
    risk_score=0,
):
    """Create a security alert for administrator review."""

    risk_score = max(0, min(100, int(risk_score)))

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO security_alerts
                (rider_id, alert_type, description, risk_score)
            VALUES (?, ?, ?, ?)
            """,
            (rider_id, alert_type, description, risk_score),
        )


def get_security_alerts():
    """Return all security alerts, newest first."""

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM security_alerts
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()


def get_unresolved_security_alerts():
    """Return alerts that still need administrator review."""

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM security_alerts
            WHERE resolved = 0
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()


def resolve_security_alert(alert_id):
    """Mark an alert as resolved without deleting its history."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE security_alerts
            SET resolved = 1
            WHERE id = ? AND resolved = 0
            """,
            (int(alert_id),),
        )

        return cursor.rowcount > 0


def get_database_summary():
    """Return record counts without exposing personal details."""

    with get_connection() as connection:
        riders = connection.execute(
            "SELECT COUNT(*) FROM riders"
        ).fetchone()[0]

        logs = connection.execute(
            "SELECT COUNT(*) FROM verification_logs"
        ).fetchone()[0]

        alerts = connection.execute(
            "SELECT COUNT(*) FROM security_alerts"
        ).fetchone()[0]

        unresolved = connection.execute(
            """
            SELECT COUNT(*)
            FROM security_alerts
            WHERE resolved = 0
            """
        ).fetchone()[0]

    return {
        "riders": riders,
        "verification_logs": logs,
        "security_alerts": alerts,
        "unresolved_alerts": unresolved,
    }


if __name__ == "__main__":
    initialize_database()

    print("Trust Juggler database check")
    print("-" * 32)
    print(f"Database file: {DATABASE_PATH}")
    print("Database initialized successfully.")

    summary = get_database_summary()

    print(f"Registered riders: {summary['riders']}")
    print(f"Verification logs: {summary['verification_logs']}")
    print(f"Security alerts: {summary['security_alerts']}")
    print(f"Unresolved alerts: {summary['unresolved_alerts']}")
