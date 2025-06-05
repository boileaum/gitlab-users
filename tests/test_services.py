from unittest.mock import MagicMock, patch

import pytest

from gitlab_users.models import Group, User
from gitlab_users.services import GitLabService


def test_list_users_returns_user_objects():
    mock_gl = MagicMock()
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "bob"
    mock_user.email = "bob@example.com"
    mock_user.name = "Bob"
    mock_user.state = "active"
    mock_gl.users.list.return_value = [mock_user]
    with patch("gitlab_users.services.gitlab.Gitlab", return_value=mock_gl):
        service = GitLabService(gitlab_id=None)
        service.gl = mock_gl
        users = service.list_users()
        assert isinstance(users[0], User)
        assert users[0].username == "bob"


def test_list_groups_returns_group_objects():
    mock_gl = MagicMock()
    mock_group = MagicMock()
    mock_group.id = 42
    mock_group.name = "devs"
    mock_group.path = "devs-path"
    mock_gl.groups.list.return_value = [mock_group]
    with patch("gitlab_users.services.gitlab.Gitlab", return_value=mock_gl):
        service = GitLabService(gitlab_id=None)
        service.gl = mock_gl
        groups = service.list_groups()
        assert isinstance(groups[0], Group)
        assert groups[0].name == "devs"


def test_gitlab_service_with_gitlab_id():
    """Test GitLabService initialization with specific gitlab_id."""
    with patch("gitlab_users.services.gitlab.Gitlab.from_config") as mock_from_config:
        GitLabService(gitlab_id="test_id")
        mock_from_config.assert_called_once_with("test_id")


def test_gitlab_service_without_gitlab_id():
    """Test GitLabService initialization without gitlab_id."""
    with patch("gitlab_users.services.gitlab.Gitlab.from_config") as mock_from_config:
        GitLabService(gitlab_id=None)
        mock_from_config.assert_called_once_with()


def test_create_user():
    """Test user creation."""
    mock_gl = MagicMock()
    mock_created_user = MagicMock()
    mock_created_user.id = 123
    mock_created_user.username = "newuser"
    mock_created_user.email = "newuser@example.com"
    mock_created_user.name = "New User"
    mock_created_user.state = "active"
    mock_gl.users.create.return_value = mock_created_user

    with patch("gitlab_users.services.gitlab.Gitlab", return_value=mock_gl):
        service = GitLabService(gitlab_id=None)
        service.gl = mock_gl
        user = service.create_user("newuser", "newuser@example.com", "New User")

        assert isinstance(user, User)
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        mock_gl.users.create.assert_called_once()


def test_create_user_with_kwargs():
    """Test user creation with additional kwargs."""
    mock_gl = MagicMock()
    mock_created_user = MagicMock()
    mock_created_user.id = 123
    mock_created_user.username = "newuser"
    mock_created_user.email = "newuser@example.com"
    mock_created_user.name = "New User"
    mock_created_user.state = "active"
    mock_gl.users.create.return_value = mock_created_user

    with patch("gitlab_users.services.gitlab.Gitlab", return_value=mock_gl):
        service = GitLabService(gitlab_id=None)
        service.gl = mock_gl
        user = service.create_user(
            "newuser", "newuser@example.com", "New User", organization="Acme Corp"
        )

        assert isinstance(user, User)
        expected_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "name": "New User",
            "reset_password": True,
            "organization": "Acme Corp",
        }
        mock_gl.users.create.assert_called_once_with(expected_data)


def test_delete_user():
    """Test user deletion."""
    mock_gl = MagicMock()

    with patch("gitlab_users.services.gitlab.Gitlab", return_value=mock_gl):
        service = GitLabService(gitlab_id=None)
        service.gl = mock_gl
        service.delete_user(123)

        mock_gl.users.delete.assert_called_once_with(123, hard_delete=False)


def test_delete_user_hard_delete():
    """Test user deletion with hard delete."""
    mock_gl = MagicMock()

    with patch("gitlab_users.services.gitlab.Gitlab", return_value=mock_gl):
        service = GitLabService(gitlab_id=None)
        service.gl = mock_gl
        service.delete_user(123, hard_delete=True)

        mock_gl.users.delete.assert_called_once_with(123, hard_delete=True)


def test_get_user_by_username():
    """Test getting user by username."""
    mock_gl = MagicMock()
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "bob"
    mock_user.email = "bob@example.com"
    mock_user.name = "Bob"
    mock_user.state = "active"
    mock_gl.users.list.return_value = [mock_user]

    with patch("gitlab_users.services.gitlab.Gitlab", return_value=mock_gl):
        service = GitLabService(gitlab_id=None)
        service.gl = mock_gl
        user = service.get_user_by_username("bob")

        assert isinstance(user, User)
        assert user.username == "bob"
        mock_gl.users.list.assert_called_once_with(username="bob")


def test_get_user_by_username_not_found():
    """Test getting user by username when user doesn't exist."""
    mock_gl = MagicMock()
    mock_gl.users.list.return_value = []

    with patch("gitlab_users.services.gitlab.Gitlab", return_value=mock_gl):
        service = GitLabService(gitlab_id=None)
        service.gl = mock_gl

        with pytest.raises(
            ValueError, match="User with username 'nonexistent' not found"
        ):
            service.get_user_by_username("nonexistent")


def test_get_user_by_username_no_email():
    """Test getting user by username when user has no email attribute."""
    mock_gl = MagicMock()
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "bob"
    mock_user.name = "Bob"
    mock_user.state = "active"
    # Simulate user without email attribute
    del mock_user.email
    mock_gl.users.list.return_value = [mock_user]

    with patch("gitlab_users.services.gitlab.Gitlab", return_value=mock_gl):
        service = GitLabService(gitlab_id=None)
        service.gl = mock_gl
        user = service.get_user_by_username("bob")

        assert user.email == ""  # Should default to empty string


def test_get_group_by_id():
    """Test getting group by ID."""
    mock_gl = MagicMock()
    mock_group = MagicMock()
    mock_group.id = 42
    mock_group.name = "developers"
    mock_group.path = "devs"
    mock_gl.groups.get.return_value = mock_group

    with patch("gitlab_users.services.gitlab.Gitlab", return_value=mock_gl):
        service = GitLabService(gitlab_id=None)
        service.gl = mock_gl
        group = service.get_group_by_id(42)

        assert isinstance(group, Group)
        assert group.id == 42
        assert group.name == "developers"
        assert group.path == "devs"
        mock_gl.groups.get.assert_called_once_with(42)


def test_delete_user_from_group():
    """Test removing user from group."""
    mock_gl = MagicMock()
    mock_group_obj = MagicMock()
    mock_gl.groups.get.return_value = mock_group_obj

    group = Group(id=42, name="developers", path="devs")
    user = User(
        id=1, username="bob", email="bob@example.com", name="Bob", state="active"
    )

    with patch("gitlab_users.services.gitlab.Gitlab", return_value=mock_gl):
        service = GitLabService(gitlab_id=None)
        service.gl = mock_gl
        service.delete_user_from_group(group, user)

        mock_gl.groups.get.assert_called_once_with(42)
        mock_group_obj.members.delete.assert_called_once_with(1, permanently=False)


def test_delete_user_from_group_hard_delete():
    """Test removing user from group with hard delete."""
    mock_gl = MagicMock()
    mock_group_obj = MagicMock()
    mock_gl.groups.get.return_value = mock_group_obj

    group = Group(id=42, name="developers", path="devs")
    user = User(
        id=1, username="bob", email="bob@example.com", name="Bob", state="active"
    )

    with patch("gitlab_users.services.gitlab.Gitlab", return_value=mock_gl):
        service = GitLabService(gitlab_id=None)
        service.gl = mock_gl
        service.delete_user_from_group(group, user, hard_delete=True)

        mock_gl.groups.get.assert_called_once_with(42)
        mock_group_obj.members.delete.assert_called_once_with(1, permanently=True)


def test_export_user_ssh_keys():
    """Test exporting SSH keys for a user."""
    mock_gl = MagicMock()
    mock_user_obj = MagicMock()
    mock_key1 = MagicMock()
    mock_key1.key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7..."
    mock_key2 = MagicMock()
    mock_key2.key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHYr..."
    mock_user_obj.keys.list.return_value = [mock_key1, mock_key2]
    mock_gl.users.get.return_value = mock_user_obj

    user = User(
        id=1, username="bob", email="bob@example.com", name="Bob", state="active"
    )

    with patch("gitlab_users.services.gitlab.Gitlab", return_value=mock_gl):
        service = GitLabService(gitlab_id=None)
        service.gl = mock_gl
        keys = service.export_ssh_keys(user)

        assert len(keys) == 2
        assert keys[0] == "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7..."
        assert keys[1] == "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHYr..."
        mock_gl.users.get.assert_called_once_with(1)
        mock_user_obj.keys.list.assert_called_once()
