import json
import os
from pathlib import Path
from typing import Any

from supabase import Client, create_client


def load_env_file(env_path: Path | None = None) -> None:
    env_path = env_path or Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_supabase_client() -> Client:
    load_env_file()

    url = os.getenv("SUPABASE_URL") or "https://ujakxcwyahuwcglfbqcp.supabase.co"
    key = (
        os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVqYWt4Y3d5YWh1d2NnbGZicWNwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUzMjg0OTMsImV4cCI6MjEwMDkwNDQ5M30.hTOmv_xwWWm1lmnwWgi1gtpfX9yqVUi0dnf7K1KjTHI"
    )

    if not url or not key:
        raise RuntimeError(
            "Missing Supabase configuration. Set SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY / SUPABASE_ANON_KEY) in your environment or in a .env file."
        )

    normalized_url = url.rstrip("/")
    if normalized_url.endswith("/rest/v1"):
        normalized_url = normalized_url[: -len("/rest/v1")]

    return create_client(normalized_url, key)


def fetch_all_rows(table_name: str = "College_Course_Teaching_Details") -> list[dict[str, Any]]:
    client = get_supabase_client()
    response = client.table(table_name).select("*").execute()

    data = response.data or []
    print(f"Fetched {len(data)} row(s) from {table_name}.")
    print(json.dumps(data, indent=2, default=str))
    return data


if __name__ == "__main__":
    fetch_all_rows()
