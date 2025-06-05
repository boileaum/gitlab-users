import subprocess
import sys
from unittest.mock import MagicMock, patch

from gitlab_users.cli import main
from gitlab_users.models import Group, User


def test_cli_help():
    """Test that the CLI help command runs and displays usage information."""
    result = subprocess.run(
        [sys.executable, "-m", "gitlab_users.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()


def test_list_users_command(capsys):
    """Test the list-users command."""
    mock_service = MagicMock()
    mock_users = [
        User(id=1, username="bob", email="bob@example.com", name="Bob", state="active"),
        User(
            id=2,
            username="alice",
            email="alice@example.com",
            name="Alice",
            state="active",
        ),
    ]
    mock_service.list_users.return_value = mock_users

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("sys.argv", ["gitlab-users", "list-users"]):
            main()

    captured = capsys.readouterr()
    assert "1: bob (bob@example.com) [active]" in captured.out
    assert "2: alice (alice@example.com) [active]" in captured.out


def test_list_groups_command(capsys):
    """Test the list-groups command."""
    mock_service = MagicMock()
    mock_groups = [
        Group(id=1, name="developers", path="devs"),
        Group(id=2, name="administrators", path="admins"),
    ]
    mock_service.list_groups.return_value = mock_groups

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("sys.argv", ["gitlab-users", "list-groups"]):
            main()

    captured = capsys.readouterr()
    assert "1: developers (devs)" in captured.out
    assert "2: administrators (admins)" in captured.out


def test_export_users_command(capsys, tmp_path):
    """Test the export-users command."""
    output_file = tmp_path / "users.csv"
    mock_service = MagicMock()
    mock_users = [
        User(id=1, username="bob", email="bob@example.com", name="Bob", state="active"),
    ]
    mock_service.list_users.return_value = mock_users

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("gitlab_users.cli.utils.export_users_to_csv") as mock_export:
            with patch("sys.argv", ["gitlab-users", "export-users", str(output_file)]):
                main()

    captured = capsys.readouterr()
    assert "Exported 1 users" in captured.out
    mock_export.assert_called_once()


def test_create_from_csv_command(capsys, tmp_path):
    """Test the create-from-csv command."""
    csv_file = tmp_path / "test_users.csv"
    csv_file.write_text("bob,Bob,bob@example.com,Acme Corp,New York,devs,developer\n")

    mock_service = MagicMock()
    mock_user = User(
        id=1, username="bob", email="bob@example.com", name="Bob", state="active"
    )
    mock_service.create_user.return_value = mock_user

    mock_group = MagicMock()
    mock_service.gl.groups.get.return_value = mock_group

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("gitlab_users.cli.utils.get_users_from_csv") as mock_get_users:
            mock_get_users.return_value = [
                {
                    "username": "bob",
                    "name": "Bob",
                    "email": "bob@example.com",
                    "organization": "Acme Corp",
                    "location": "New York",
                    "group": "devs",
                    "access_level": "developer",
                }
            ]
            with patch("gitlab_users.cli.AccessLevel") as mock_access_level:
                mock_access_level.DEVELOPER = 30
                with patch(
                    "sys.argv", ["gitlab-users", "create-from-csv", str(csv_file)]
                ):
                    main()

    captured = capsys.readouterr()
    assert "Created user: bob" in captured.out
    assert "Added to group devs as developer" in captured.out


def test_create_from_csv_dry_run(capsys, tmp_path):
    """Test the create-from-csv command in dry run mode."""
    csv_file = tmp_path / "test_users.csv"
    csv_file.write_text("bob,Bob,bob@example.com\n")

    mock_service = MagicMock()

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("gitlab_users.cli.utils.get_users_from_csv") as mock_get_users:
            mock_get_users.return_value = [
                {"username": "bob", "name": "Bob", "email": "bob@example.com"}
            ]
            with patch(
                "sys.argv",
                ["gitlab-users", "create-from-csv", str(csv_file), "--dry-run"],
            ):
                main()

    captured = capsys.readouterr()
    assert "[DRY RUN] Would create user: bob" in captured.out
    mock_service.create_user.assert_not_called()


def test_delete_from_csv_dry_run(capsys, tmp_path):
    """Test the delete-from-csv command in dry run mode."""
    csv_file = tmp_path / "test_users.csv"
    csv_file.write_text("bob\nalice\n")

    mock_service = MagicMock()
    mock_user = User(
        id=1, username="bob", email="bob@example.com", name="Bob", state="active"
    )
    mock_service.get_user_by_username.return_value = mock_user

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch(
            "sys.argv", ["gitlab-users", "delete-from-csv", str(csv_file), "--dry-run"]
        ):
            main()

    captured = capsys.readouterr()
    assert "[DRY RUN] Would delete user: bob" in captured.out
    mock_service.delete_user.assert_not_called()


def test_delete_from_csv_user_not_found(capsys, tmp_path):
    """Test the delete-from-csv command when user is not found."""
    csv_file = tmp_path / "test_users.csv"
    csv_file.write_text("nonexistent\n")

    mock_service = MagicMock()
    mock_service.get_user_by_username.side_effect = ValueError("User not found")

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("sys.argv", ["gitlab-users", "delete-from-csv", str(csv_file)]):
            main()

    captured = capsys.readouterr()
    assert "User nonexistent not found" in captured.out


def test_delete_from_csv_with_confirmation(capsys, tmp_path):
    """Test the delete-from-csv command with user confirmation."""
    csv_file = tmp_path / "test_users.csv"
    csv_file.write_text("bob\n")

    mock_service = MagicMock()
    mock_user = User(
        id=1, username="bob", email="bob@example.com", name="Bob", state="active"
    )
    mock_service.get_user_by_username.return_value = mock_user

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("builtins.input", return_value="y"):
            with patch("sys.argv", ["gitlab-users", "delete-from-csv", str(csv_file)]):
                main()

    captured = capsys.readouterr()
    assert "Deleted user: bob" in captured.out
    mock_service.delete_user.assert_called_once_with(1)


def test_delete_from_csv_cancelled_by_user(capsys, tmp_path):
    """Test the delete-from-csv command when user cancels deletion."""
    csv_file = tmp_path / "test_users.csv"
    csv_file.write_text("bob\n")

    mock_service = MagicMock()
    mock_user = User(
        id=1, username="bob", email="bob@example.com", name="Bob", state="active"
    )
    mock_service.get_user_by_username.return_value = mock_user

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("builtins.input", return_value="n"):
            with patch("sys.argv", ["gitlab-users", "delete-from-csv", str(csv_file)]):
                main()

    captured = capsys.readouterr()
    assert "Skipped user: bob" in captured.out
    mock_service.delete_user.assert_not_called()


def test_delete_user_command(capsys):
    """Test the delete-user command."""
    mock_service = MagicMock()
    mock_user = User(
        id=1, username="bob", email="bob@example.com", name="Bob", state="active"
    )
    mock_service.get_user_by_username.return_value = mock_user

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("sys.argv", ["gitlab-users", "delete-user", "bob"]):
            main()

    captured = capsys.readouterr()
    assert "Deleted user: bob" in captured.out
    mock_service.delete_user.assert_called_once_with(1)


def test_delete_user_not_found(capsys):
    """Test the delete-user command when user is not found."""
    mock_service = MagicMock()
    mock_service.get_user_by_username.side_effect = ValueError("User not found")

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("sys.argv", ["gitlab-users", "delete-user", "nonexistent"]):
            main()

    captured = capsys.readouterr()
    assert "User nonexistent not found" in captured.out


def test_delete_user_dry_run(capsys):
    """Test the delete-user command in dry run mode."""
    mock_service = MagicMock()
    mock_user = User(
        id=1, username="bob", email="bob@example.com", name="Bob", state="active"
    )
    mock_service.get_user_by_username.return_value = mock_user

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("sys.argv", ["gitlab-users", "delete-user", "bob", "--dry-run"]):
            main()

    captured = capsys.readouterr()
    assert "[DRY RUN] Would delete user: bob" in captured.out
    mock_service.delete_user.assert_not_called()


def test_export_ssh_keys_command(capsys):
    """Test the export-ssh-keys command."""
    mock_service = MagicMock()
    mock_user = User(
        id=1, username="bob", email="bob@example.com", name="Bob", state="active"
    )
    mock_service.get_user_by_username.return_value = mock_user
    mock_service.export_ssh_keys.return_value = [
        "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7...",
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHYr...",
    ]

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("sys.argv", ["gitlab-users", "export-ssh-keys", "bob"]):
            main()

    captured = capsys.readouterr()
    assert "SSH keys for user bob:" in captured.out
    assert "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7..." in captured.out


def test_export_ssh_keys_user_not_found(capsys):
    """Test the export-ssh-keys command when user is not found."""
    mock_service = MagicMock()
    mock_service.get_user_by_username.side_effect = ValueError("User not found")

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("sys.argv", ["gitlab-users", "export-ssh-keys", "nonexistent"]):
            main()

    captured = capsys.readouterr()
    assert "User nonexistent not found" in captured.out


def test_create_from_csv_unknown_access_level(capsys, tmp_path):
    """Test the create-from-csv command with unknown access level."""
    csv_file = tmp_path / "test_users.csv"
    csv_content = "bob,Bob,bob@example.com,Acme Corp,New York,devs,unknown_level\n"
    csv_file.write_text(csv_content)

    mock_service = MagicMock()
    mock_user = User(
        id=1, username="bob", email="bob@example.com", name="Bob", state="active"
    )
    mock_service.create_user.return_value = mock_user

    mock_group = MagicMock()
    mock_service.gl.groups.get.return_value = mock_group

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("gitlab_users.cli.utils.get_users_from_csv") as mock_get_users:
            mock_get_users.return_value = [
                {
                    "username": "bob",
                    "name": "Bob",
                    "email": "bob@example.com",
                    "organization": "Acme Corp",
                    "location": "New York",
                    "group": "devs",
                    "access_level": "unknown_level",
                }
            ]
            with patch("gitlab_users.cli.AccessLevel") as mock_access_level:
                mock_access_level.UNKNOWN_LEVEL = None  # Unknown access level
                with patch(
                    "sys.argv", ["gitlab-users", "create-from-csv", str(csv_file)]
                ):
                    main()

    captured = capsys.readouterr()
    assert "Created user: bob" in captured.out
    assert "[WARN] Unknown access level: unknown_level" in captured.out


def test_create_from_csv_group_assignment_error(capsys, tmp_path):
    """Test the create-from-csv command when group assignment fails."""
    csv_file = tmp_path / "test_users.csv"
    csv_content = "bob,Bob,bob@example.com,Acme Corp,New York,devs,developer\n"
    csv_file.write_text(csv_content)

    mock_service = MagicMock()
    mock_user = User(
        id=1, username="bob", email="bob@example.com", name="Bob", state="active"
    )
    mock_service.create_user.return_value = mock_user

    mock_group = MagicMock()
    mock_group.members.create.side_effect = Exception("Group assignment failed")
    mock_service.gl.groups.get.return_value = mock_group

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("gitlab_users.cli.utils.get_users_from_csv") as mock_get_users:
            mock_get_users.return_value = [
                {
                    "username": "bob",
                    "name": "Bob",
                    "email": "bob@example.com",
                    "organization": "Acme Corp",
                    "location": "New York",
                    "group": "devs",
                    "access_level": "developer",
                }
            ]
            with patch("gitlab_users.cli.AccessLevel") as mock_access_level:
                mock_access_level.DEVELOPER = 30
                with patch(
                    "sys.argv", ["gitlab-users", "create-from-csv", str(csv_file)]
                ):
                    main()

    captured = capsys.readouterr()
    assert "Created user: bob" in captured.out
    assert "[WARN] Could not add to group devs:" in captured.out


def test_unknown_command(capsys):
    """Test handling of unknown commands."""
    mock_service = MagicMock()

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("sys.argv", ["gitlab-users", "unknown-command"]):
            try:
                main()
            except SystemExit:
                pass  # Expected behavior for unknown command

    # The function should exit without reaching normal execution


def test_no_command_prints_help(capsys):
    """Test that no command prints help."""
    mock_service = MagicMock()

    with patch("gitlab_users.cli.GitLabService", return_value=mock_service):
        with patch("sys.argv", ["gitlab-users"]):
            main()

    captured = capsys.readouterr()
    # When no command is provided, the else clause should trigger parser.print_help()
    assert captured.out != ""  # Some help text should be printed
