import os
import tempfile
from pathlib import Path

import pytest

from gitlab_users import utils
from gitlab_users.models import User


def test_import_users_csv():
    example_csv_file_path = Path(__file__).parent / "example.csv"
    imported = utils.get_users_from_csv(example_csv_file_path)
    ww, wayne = imported
    assert ww["username"] == "ww"
    assert ww["email"] == "wonder.woman@themyscira.org"
    assert ww["name"] == "Diana Prince"
    assert ww["location"] == "Themyscira"

    assert wayne["username"] == "wayne"
    assert wayne["email"] == "bruce.wayne@wayne-enterprises.com"
    assert wayne["name"] == "Bruce Wayne"
    assert wayne["location"] == "Gotham City"
    assert wayne["organization"] == "Wayne Enterprises"
    assert wayne["group"] == "board"
    assert wayne["access_level"] == "owner"


def test_get_usernames_from_csv():
    csv_content = "bob,Bob,bob@example.com\nalice,Alice,alice@example.com\n"
    with tempfile.NamedTemporaryFile(delete=False, mode="w+") as tmp:
        tmp.write(csv_content)
        tmp.flush()
        usernames = utils.get_usernames_from_csv(tmp.name)
        assert usernames == ["bob", "alice"]
    os.remove(tmp.name)


def test_get_user_data_success():
    """Test successful retrieval of user data."""
    user = {"username": "bob", "email": "bob@example.com", "name": "Bob"}
    assert utils.get_user_data(user, "username") == "bob"
    assert utils.get_user_data(user, "email") == "bob@example.com"
    assert utils.get_user_data(user, "name") == "Bob"


def test_get_user_data_key_error():
    """Test get_user_data raises ValueError when key is missing."""
    user = {"username": "bob", "email": "bob@example.com"}
    with pytest.raises(ValueError, match="User data 'missing_key' not found in user"):
        utils.get_user_data(user, "missing_key")


def test_export_users_to_csv(tmp_path):
    """Test exporting users to CSV file."""
    users = [
        User(
            id=1,
            username="alice",
            email="alice@example.com",
            name="Alice",
            state="blocked",
        ),
        User(id=2, username="bob", email="bob@example.com", name="Bob", state="active"),
    ]

    csv_file = tmp_path / "exported_users.csv"
    utils.export_users_to_csv(users, csv_file)

    # Verify the file was created and contains expected content
    assert csv_file.exists()
    content = csv_file.read_text()
    lines = content.strip().split("\n")

    # Check header
    assert lines[0] == "id,username,name,email,state"

    # Check data
    assert "1,alice,Alice,alice@example.com,blocked" in lines
    assert "2,bob,Bob,bob@example.com,active" in lines


def test_get_users_from_csv_with_comments(tmp_path):
    """Test reading CSV file with comments (lines starting with #)."""
    csv_content = """# This is a comment
bob,Bob,bob@example.com,Acme Corp,New York
# Another comment
alice,Alice,alice@example.com,,,devs,maintainer"""

    csv_file = tmp_path / "users_with_comments.csv"
    csv_file.write_text(csv_content)

    users = utils.get_users_from_csv(csv_file)
    assert len(users) == 2
    assert users[0]["username"] == "bob"
    assert users[1]["username"] == "alice"


def test_get_users_from_csv_empty_fields(tmp_path):
    """Test reading CSV file with empty fields."""
    csv_content = "bob,Bob Smith,,,,devs,\nalice,Alice Johnson,alice@example.com,,,,"

    csv_file = tmp_path / "users_empty_fields.csv"
    csv_file.write_text(csv_content)

    users = utils.get_users_from_csv(csv_file)
    assert len(users) == 2

    # Check bob's data
    bob = users[0]
    assert bob["username"] == "bob"
    assert bob["name"] == "Bob Smith"
    assert bob["email"] == ""
    assert bob["organization"] == ""
    assert bob["location"] == ""
    assert bob["group"] == "devs"
    assert bob["access_level"] == ""

    # Check alice's data
    alice = users[1]
    assert alice["username"] == "alice"
    assert alice["name"] == "Alice Johnson"
    assert alice["email"] == "alice@example.com"
    assert alice["organization"] == ""
    assert alice["location"] == ""
    assert alice["group"] == ""
    assert alice["access_level"] == ""


def test_get_usernames_from_csv_with_comments(tmp_path):
    """Test getting usernames from CSV file with comments."""
    csv_content = """# Comment line
bob,Bob,bob@example.com
# Another comment
alice,Alice,alice@example.com
charlie,Charlie,charlie@example.com"""

    csv_file = tmp_path / "usernames_with_comments.csv"
    csv_file.write_text(csv_content)

    usernames = utils.get_usernames_from_csv(csv_file)
    assert usernames == ["bob", "alice", "charlie"]


def test_get_usernames_from_csv_empty_rows(tmp_path):
    """Test getting usernames from CSV file with empty rows."""
    csv_content = "bob,Bob,bob@example.com\n\n\nalice,Alice,alice@example.com\n"

    csv_file = tmp_path / "usernames_empty_rows.csv"
    csv_file.write_text(csv_content)

    usernames = utils.get_usernames_from_csv(csv_file)
    assert usernames == ["bob", "alice"]  # Empty rows should be filtered out
