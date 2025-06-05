"""
Data models for GitLab users and groups.

Defines dataclasses for User and Group entities.
"""

from dataclasses import dataclass


@dataclass
class User:
    """
    Data class representing a GitLab user.
    """

    id: int  #: User ID
    username: str  #: GitLab username
    email: str  #: User email address
    name: str  #: Full name of the user
    state: str  #: User state (e.g., 'active')


@dataclass
class Group:
    """
    Data class representing a GitLab group.
    """

    id: int  #: Group ID
    name: str  #: Group name
    path: str  #: Group path (URL path)
