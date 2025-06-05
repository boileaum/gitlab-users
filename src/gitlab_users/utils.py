"""
Utility functions for CSV import/export and user data processing.

Includes helpers for reading and writing user data in CSV format.
"""

import csv
from pathlib import Path

from .models import User


def get_user_data(user: dict, dataname: str) -> str:
    """
    Retrieve specific user data from a user dictionary.

    Args:
        user: User data dictionary.
        dataname: Key to retrieve from the user dictionary.
    Returns:
        The value associated with the dataname key.
    Raises:
        ValueError: If the dataname key is not found in the user dictionary.
    """
    try:
        return user[dataname]
    except KeyError:
        raise ValueError(f"User data '{dataname}' not found in user: {user}")


def export_users_to_csv(users: list[User], filepath: Path):
    """
    Export a list of users to a CSV file.

    Args:
        users: list of User objects to export.
        filepath: Path to the output CSV file.

    A typical output CSV file will have the following columns:

    .. code-block:: text

        id,username,name,email,state
        1,alice,Alice,alice@example.com,active
        2,bob,Bob,bob@example.com,blocked

    """
    with open(filepath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["id", "username", "name", "email", "state"])
        for user in users:
            writer.writerow([user.id, user.username, user.name, user.email, user.state])


def get_users_from_csv(filepath: Path) -> list[dict[str, str]]:
    """
    Read users from a CSV file (with or without header).

    Args:
        filepath: Path to the CSV file.

    Returns:
        list of user dictionaries with keys: username, name, email, organization,
        location, group, access_level.

    A typical input CSV file will have the following columns:

    .. include:: ../../example.csv
        :literal:
        :code: csv

    """
    from itertools import zip_longest

    fieldnames = (
        "username",
        "name",
        "email",
        "organization",
        "location",
        "group",
        "access_level",
    )
    with open(filepath, "r") as csvfile:
        csvreader = csv.reader(row for row in csvfile if not row.startswith("#"))
        stripped_reader = [[x.strip() for x in row] for row in csvreader]
        newusers = [dict(zip_longest(fieldnames, row)) for row in stripped_reader]
        return newusers


def get_usernames_from_csv(filepath: Path) -> list[str]:
    """
    Return a list of usernames from a CSV or text file (first column).

    Args:
        filepath: Path to the CSV or text file.

    Returns:
        list of usernames.
    """
    with open(filepath, "r") as csvfile:
        csvreader = csv.reader(row for row in csvfile if not row.startswith("#"))
        return [row[0] for row in csvreader if row]
