"""
Unified service for all GitLab users and groups operations.
This module provides a service class for managing GitLab users and groups,
including listing, creating, deleting users, and managing groups.
"""

from typing import Optional

import gitlab

from .models import Group, User


class GitLabService:
    """Service for interacting with GitLab users, groups, and related operations."""

    def __init__(self, gitlab_id: Optional[str] = None):
        """
        Initialize the GitLab connection.

        Args:
            gitlab_id: Section name in python-gitlab.cfg.If None, use default.
        """
        if gitlab_id is not None:
            self.gl = gitlab.Gitlab.from_config(gitlab_id)
        else:
            self.gl = gitlab.Gitlab.from_config()

    def list_users(self) -> list[User]:
        """
        List all users on the GitLab instance.

        Returns:
            A list of User objects representing all users.
        """
        return [
            User(
                id=u.id,
                username=u.username,
                email=getattr(u, "email", ""),
                name=u.name,
                state=u.state,
            )
            for u in self.gl.users.list(all=True)
        ]

    def create_user(
        self,
        username: str,
        email: str,
        name: str,
        **kwargs,
    ) -> User:
        """
        Create a new user.

        Args:
            username: Username.
            email: Email address.
            name: Full name.
            **kwargs: Other GitLab user fields.

        Returns:
            The created user.
        """
        data = dict(
            username=username, email=email, name=name, reset_password=True, **kwargs
        )

        user = self.gl.users.create(data)
        return User(
            id=user.id,
            username=user.username,
            email=user.email,
            name=user.name,
            state=user.state,
        )

    def delete_user(self, user_id: int, hard_delete: bool = False) -> None:
        """
        Delete a user by ID.

        Args:
            user_id: User ID.
            hard_delete: If True, hard delete the user.
        """
        self.gl.users.delete(user_id, hard_delete=hard_delete)

    def get_user_by_username(self, username: str) -> User:
        """
        Get a user by their username.

        Args:
            username: The username of the user to retrieve.

        Returns:
            The user object with ID, username, email, name, and state.

        Raises:
            ValueError: If the user with the given username does not exist.
        """
        users = self.gl.users.list(username=username)
        if not users:
            raise ValueError(f"User with username '{username}' not found.")
        u = list(users)[0]
        return User(
            id=u.id,
            username=u.username,
            email=getattr(u, "email", ""),
            name=u.name,
            state=u.state,
        )

    def list_groups(self) -> list[Group]:
        """
        List all groups on the GitLab instance.

        Returns:
            A list of Group objects.
        """
        return [
            Group(
                id=g.id,
                name=g.name,
                path=g.path,
            )
            for g in self.gl.groups.list(all=True)
        ]

    def get_group_by_id(self, group_id: int) -> Group:
        """
        Get a group by its ID.

        Returns:
            The group object with ID, name, and path.
        """
        g = self.gl.groups.get(group_id)
        return Group(id=g.id, name=g.name, path=g.path)

    def delete_user_from_group(
        self, group: Group, user: User, hard_delete: bool = False
    ):
        """
        Remove a user from a group.

        Args:
            group: The group from which to remove the user.
            user: The user to remove.
            hard_delete: If True, permanently delete the user from the group.
        """
        g = self.gl.groups.get(group.id)
        g.members.delete(user.id, permanently=hard_delete)

    def export_ssh_keys(self, user: User) -> list[str]:
        """
        Export SSH keys of a user.

        Args:
            user: The user whose SSH keys to export.

        Returns:
            A list of SSH keys for the user.
        """
        user_obj = self.gl.users.get(user.id)
        keys = user_obj.keys.list()
        return [k.key for k in keys]
