"""
CLI for managing GitLab users and groups.

Provides commands to list, export, create, and delete users and groups,
as well as export SSH keys, using the python-gitlab API.
"""

import argparse
from pathlib import Path

from . import utils
from .services import GitLabService


# Access level constants
class AccessLevel:
    """GitLab access levels."""

    MINIMAL_ACCESS = 5
    GUEST = 10
    REPORTER = 20
    DEVELOPER = 30
    MAINTAINER = 40
    OWNER = 50


def main():
    """
    Main entry point for the GitLab Users CLI.
    """
    parser = argparse.ArgumentParser(description="GitLab Users CLI")
    parser.add_argument(
        "--gitlab-id",
        dest="gitlab_id",
        default=None,
        help=(
            "Section de configuration à utiliser pour la connexion GitLab "
            "(python-gitlab.cfg)"
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    # List users
    subparsers.add_parser("list-users", help="List all users in the GitLab instance.")

    # List groups
    subparsers.add_parser("list-groups", help="List all groups in the GitLab instance.")

    # Export users
    parser_export = subparsers.add_parser(
        "export-users", help="Export all users to a CSV file."
    )
    parser_export.add_argument("filepath", type=Path, help="Output CSV file path.")

    # Create users from CSV
    parser_create = subparsers.add_parser(
        "create-from-csv",
        help=(
            "Create multiple users from a CSV file. The CSV should contain columns: "
            "username, name, email, [organization], [location], [group], "
            "[access_level]."
        ),
    )
    parser_create.add_argument("csvfile", type=Path, help="CSV file with user data.")
    parser_create.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not actually create users, just show what would be done.",
    )

    # Delete users from CSV
    parser_delete_csv = subparsers.add_parser(
        "delete-from-csv",
        help=(
            "Delete users from a CSV or text file (usernames in first column). "
            "Confirmation is required for each user."
        ),
    )
    parser_delete_csv.add_argument(
        "csvfile",
        type=Path,
        help="CSV or text file with usernames in the first column.",
    )
    parser_delete_csv.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not actually delete users, just show what would be done.",
    )

    # Delete a single user
    parser_delete = subparsers.add_parser(
        "delete-user",
        help="Delete a single user by username. Confirmation is required.",
    )
    parser_delete.add_argument("username", help="Username to delete.")
    parser_delete.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not actually delete the user, just show what would be done.",
    )

    # Export SSH keys
    parser_ssh = subparsers.add_parser(
        "export-ssh-keys", help="Export the SSH keys of a given user"
    )
    parser_ssh.add_argument("username", help="Username to export SSH keys for.")

    args = parser.parse_args()
    service = GitLabService(gitlab_id=args.gitlab_id)

    if args.command == "list-users":
        for user in service.list_users():
            print(f"{user.id}: {user.username} ({user.email}) [{user.state}]")
    elif args.command == "list-groups":
        for group in service.list_groups():
            print(f"{group.id}: {group.name} ({group.path})")
    elif args.command == "export-users":
        users = service.list_users()
        utils.export_users_to_csv(users, args.filepath)
        print(f"Exported {len(users)} users to {args.filepath}")
    elif args.command == "create-from-csv":
        users = utils.get_users_from_csv(args.csvfile)
        for user in users:
            username = utils.get_user_data(user, "username")
            email = utils.get_user_data(user, "email")
            name = utils.get_user_data(user, "name")
            organization = user.get("organization")
            location = user.get("location")
            group = user.get("group")
            access_level = user.get("access_level")
            extra = {}
            if organization:
                extra["organization"] = organization
            if location:
                extra["location"] = location
            if args.dry_run:
                print(f"[DRY RUN] Would create user: {username} <{email}>")
                continue
            u = service.create_user(username, email, name, **extra)
            print(f"Created user: {u.username} <{u.email}>")
            if group and access_level:
                try:
                    g = service.gl.groups.get(group)

                    level = getattr(AccessLevel, access_level.upper(), None)
                    if not level:
                        print(f"[WARN] Unknown access level: {access_level}")
                        continue
                    g.members.create({"user_id": u.id, "access_level": level})
                    print(f"  Added to group {group} as {access_level}")
                except Exception as e:
                    print(f"[WARN] Could not add to group {group}: {e}")
    elif args.command == "delete-from-csv":
        usernames = utils.get_usernames_from_csv(args.csvfile)
        for username in usernames:
            try:
                user = service.get_user_by_username(username)
            except ValueError:
                print(f"User {username} not found")
                continue
            if args.dry_run:
                print(f"[DRY RUN] Would delete user: {username}")
            else:
                confirm = input(f"Delete user {username}? [y/N]: ").strip().lower()
                if confirm in ("y", "yes"):
                    service.delete_user(user.id)
                    print(f"Deleted user: {username}")
                else:
                    print(f"Skipped user: {username}")
    elif args.command == "delete-user":
        try:
            user = service.get_user_by_username(args.username)
        except ValueError:
            print(f"User {args.username} not found")
            return
        if args.dry_run:
            print(f"[DRY RUN] Would delete user: {args.username}")
        else:
            service.delete_user(user.id)
            print(f"Deleted user: {args.username}")
    elif args.command == "export-ssh-keys":
        try:
            user = service.get_user_by_username(args.username)
            keys = service.export_ssh_keys(user)
            print(f"SSH keys for user {args.username}:")
            for i, key in enumerate(keys, 1):
                print(f"  {i}: {key}")
        except ValueError:
            print(f"User {args.username} not found")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
