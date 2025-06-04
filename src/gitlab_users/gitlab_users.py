"""
Use GitLab API to:

1. List GitLab users info
2. Automate user account creation/deletion
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timedelta
from itertools import zip_longest
from typing import Any, Dict, List, Optional, Sequence, Tuple

import gitlab
from gitlab.const import AccessLevel

ACCESS_LEVEL = {
    "guest": AccessLevel.GUEST,
    "reporter": AccessLevel.REPORTER,
    "developer": AccessLevel.DEVELOPER,
    "master": AccessLevel.MAINTAINER,
    "maintainer": AccessLevel.MAINTAINER,
    "owner": AccessLevel.OWNER,
}


def query_yes_no(question: str, default: Optional[str] = "no") -> bool:
    """
        Ask a yes/no question via input() and return the answer as a boolean.

    - ``query_yes_no`` : Demande de    Args:
            question: The question to present to the user.
            default: The presumed answer if the user just hits <Enter>.

        Returns:
            True if the answer is yes, False if the answer is no.
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        print(question + prompt)
        choice = input().lower()
        if default and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def connect_to_gitlab(gitlab_id: Optional[str] = None) -> gitlab.Gitlab:
    """
    Connect to the GitLab API using the configuration.

    Args:
        gitlab_id: Optional configuration section name.

    Returns:
        An authenticated gitlab.Gitlab instance.
    """
    try:
        gl = gitlab.Gitlab.from_config(gitlab_id)
    except (
        gitlab.config.GitlabIDError,
        gitlab.config.GitlabDataError,
        gitlab.config.GitlabConfigMissingError,
    ) as e:
        print(
            f"Exception in python-gitlab: {e}.\n",
            "Check python-gitlab configuration on",
            "http://python-gitlab.readthedocs.io/en/stable/cli.html",
            file=sys.stderr,
        )
        sys.exit(1)

    return gl


class GLUsers:
    """
    Main class to handle GitLab users and their information.
    Provides methods for listing, exporting, and analyzing users.

    Args:
        gitlab_id: Optional GitLab config section.
        email_only: If True, only show emails.
        export_keys: If True, export SSH keys.
        username: If True, show usernames.
        activity: List of activity filters ("unused", "sign_in", "active").
        sign_in_date: If True, show last sign-in date.
        name_only: If True, only show names.
        gl: Optionally provide an existing gitlab.Gitlab instance.

    """

    def __init__(
        self,
        gitlab_id: Optional[str] = None,
        email_only: bool = False,
        export_keys: bool = False,
        username: bool = False,
        activity: Optional[Sequence[str]] = None,
        sign_in_date: bool = False,
        name_only: bool = False,
        gl: Optional[gitlab.Gitlab] = None,
    ):
        self.gitlab_id = gitlab_id
        self.email_only = email_only
        self.name_only = name_only
        self.export_keys = export_keys
        self.username = username
        self.activity = activity
        self.sign_in_date = sign_in_date

        self.gl: gitlab.Gitlab = connect_to_gitlab(self.gitlab_id) if gl is None else gl
        self.url = self.gl.api_url
        self.all_gl_users: list[gitlab.v4.objects.UserManager] = self.gl.users.list(
            all=True
        )
        self.alluser_ids = [gl_user.id for gl_user in self.all_gl_users]

        # Create a {id: user} dictionary from user_ids list
        self.userdict: dict[int, gitlab.v4.objects.UserManager] = {
            key: value for (key, value) in zip(self.alluser_ids, self.all_gl_users)
        }

    @staticmethod
    def _sign_in_date(gl_user: gitlab.v4.objects.UserManager) -> Optional[str]:
        """
        Get the sign-in date (YYYY-MM-DD) for a user.

        Args:
            gl_user: The GitLab user object.

        Returns:
            The date string or None if not available.
        """
        if gl_user.current_sign_in_at:
            return gl_user.current_sign_in_at.split("T")[0]
        else:
            return None

    @staticmethod
    def _sign_in_date(gl_user: gitlab.v4.objects.UserManager) -> Optional[str]:
        """Return user sign-in date"""
        return __class__._format_date(gl_user, "current_sign_in_at")

    def _sign_in_date_and_time(
        self, gl_user: gitlab.v4.objects.UserManager
    ) -> datetime:
        """
        Get the sign-in date as a datetime object.

        Args:
            gl_user: The GitLab user object.

        Returns:
            The sign-in date as a datetime object.
        """
        return datetime.strptime(self._sign_in_date(gl_user), "%Y-%m-%d")

    def user_info(self, gl_user: gitlab.v4.objects.UserManager) -> str:
        """
        Get a formatted string with user information.

        Args:
            gl_user: The GitLab user object.

        Returns:
            A string with user info (name, email, etc.).
        """
        if self.email_only:
            info = gl_user.email
        elif self.name_only:
            info = gl_user.name
        else:
            info = f"{str(gl_user.name)} <{gl_user.email}>"
            # Complete with additional info
            if self.username:
                info = f"@{gl_user.username} " + info
            if self.sign_in_date:
                info += f" ({self._sign_in_date(gl_user)})"
        return info

    def list_usernames(self) -> str:
        """
        List all usernames in the GitLab instance.

        Returns:
            A string listing all usernames.
        """
        usernames = [gl_user.username for gl_user in self.all_gl_users]
        msg = f"Existing usernames ({len(usernames)}):"
        for username in sorted(usernames):
            msg += f"\n - {username}"
        return msg

    def print_users(self, user_ids: Sequence[int]):
        """
        Print information for a list of users and optionally export SSH keys.

        Args:
            user_ids: List of user IDs to print.
        """

        nokey_gl_users = []

        for user_id in user_ids:
            gl_user = self.userdict[user_id]
            if self.export_keys:
                key_dir = "ssh_keys"
                if not os.path.exists(key_dir):
                    os.mkdir(key_dir)
                keys = gl_user.keys.list()
                if keys:  # User has a ssh-key
                    print(self.user_info(gl_user))
                    key = keys[0].key
                    key_filename = f"{key_dir}/{gl_user.username}.pub"
                    with open(key_filename, "w") as f:
                        f.write(key)

                else:
                    nokey_gl_users.append(gl_user)

            else:
                print(self.user_info(gl_user))

        if self.export_keys:
            print("--")
            nuser = len(user_ids)
            nuser_key = len(user_ids) - len(nokey_gl_users)
            print(f"{nuser_key}/{nuser} users has an ssh key.")
            if nokey_gl_users:
                print("--")
                print("The following users has no ssh key:\n")
                for gl_user in nokey_gl_users:
                    print(self.user_info(gl_user))
                print("--")

    def _getactivity(
        self,
    ) -> Tuple[
        List[gitlab.v4.objects.UserManager],
        List[gitlab.v4.objects.UserManager],
        List[gitlab.v4.objects.UserManager],
        List[gitlab.v4.objects.UserManager],
    ]:
        """
        Categorize users by activity (old sign-in, never, already, active).

        Returns:
            Tuple of lists: (old_sign_in, never_sign_in, already_sign_in, active)
        """
        old_sign_in = []
        never_sign_in = []
        already_sign_in = []
        active = []
        for gl_user in self.all_gl_users:
            # Find the last connexion date
            # Split using the T between date and hours
            # Do not care about minutes...
            if gl_user.current_sign_in_at:
                current_sign_in = self._sign_in_date_and_time(gl_user)
                if gl_user.state == "active":
                    already_sign_in.append(gl_user)
                    if current_sign_in < datetime.now() - timedelta(days=365):
                        old_sign_in.append(gl_user)
                    else:
                        active.append(gl_user)
            elif gl_user.state == "active":
                never_sign_in.append(gl_user)

        return (old_sign_in, never_sign_in, already_sign_in, active)

    def output(self):
        """
        Print user information to standard output, filtered by activity if set.
        """
        if self.activity:
            (old_sign_in, never_sign_in, already_sign_in, active) = self._getactivity()

            if "unused" in self.activity:
                print("  Users whose last connexion is older than 1 year:")
                for gl_user in old_sign_in:
                    print(self.user_info(gl_user))
                print("  Users who never signed in:")
                for gl_user in never_sign_in:
                    print(self.user_info(gl_user))

            elif "sign_in" in self.activity:
                print("  Users who have already signed in:")
                for gl_user in already_sign_in:
                    print(self.user_info(gl_user))

            elif "active" in self.activity:
                print(
                    f"""\
  Active users (last connection < 1 year) [{len(active)}]:"""
                )
                for gl_user in active:
                    print(self.user_info(gl_user))
        else:
            self.print_users(self.alluser_ids)

    @staticmethod
    def _getuids(gl_users: Sequence[gitlab.v4.objects.UserManager]) -> List[int]:
        """
        Extract user IDs from a list of user objects.

        Args:
            gl_users: List of GitLab user objects.

        Returns:
            List of user IDs.
        """
        return [gu.id for gu in gl_users]

    def csv_user_line(self, gl_user: gitlab.v4.objects.UserManager) -> str:
        """
        Return user information as a CSV-formatted string.

        Args:
            gl_user: The GitLab user object.

        Returns:
            CSV line containing user details.
        """
        info = ",".join(
            [
                gl_user.username,
                gl_user.email,
                f'"{str(gl_user.name)}"',
                gl_user.state,
                str(gl_user.is_admin),
                str(gl_user.external),
                self._format_date(gl_user, "last_sign_in_at"),
                self._format_date(gl_user, "created_at"),
            ]
        )
        return info

    def print_users_csv(self, user_ids: Sequence[int]):
        """
        Print a CSV listing of users.

        Args:
            user_ids: List of user IDs to print.
        """

        for user_id in user_ids:
            gl_user = self.userdict[user_id]
            print(self.csv_user_line(gl_user))

    def out_csv(self):
        """
        Output a CSV of all users, filtered by activity if set.
        """
        print('Username,E-mail,"Name",State,isAdmin,isExternal,LastSignInAt,CreatedAt')
        if self.activity:
            (old_sign_in, never_sign_in, already_sign_in, active) = self._getactivity()
            if "unused" in self.activity:
                # print("  Users whose last connexion is older than 1 year:")
                # print("  Users who never signed in:")
                self.print_users_csv(self._getuids(old_sign_in + never_sign_in))

            elif "sign_in" in self.activity:
                # print("  Users who have already signed in:")
                self.print_users_csv(self._getuids(already_sign_in))
            elif "active" in self.activity:
                # print(f"""Active users (last connection < 1 year) [{len(active)}]:""")
                self.print_users_csv(self._getuids(active))
        else:
            self.print_users_csv(self.alluser_ids)


class GLGroups(GLUsers):
    """
    Handle groups of gitlab users

    Args:
        groups: The name of the group to filter by, or "list" to list all groups.
        *args: Additional positional arguments passed to GLUsers.
        **kwargs: Additional keyword arguments passed to GLUsers.

    """

    def __init__(self, groups: str, *args: Any, **kwargs: Any):
        self.groups = groups
        super().__init__(*args, **kwargs)
        self.all_gl_groups = self.gl.groups.list(all=True)

    def list_all_groups(self) -> str:
        """
        List all groups in the GitLab instance.

        Returns:
            A string listing all group names.
        """
        groupnames = [gl_group.name for gl_group in self.all_gl_groups]
        msg = f"Existing groups ({len(groupnames)}):"
        for groupname in sorted(groupnames):
            msg += f"\n - {groupname}"
        return msg

    def output(self):
        """Output users information"""

        if self.groups == "list":
            print(self.list_all_groups())
            sys.exit(0)
        else:
            gl_groups = self.gl.groups.list(search=self.groups)

            if not gl_groups:
                print(f"No group matching {self.groups} found on {self.url}.")
                print(self.list_all_groups())
                sys.exit(1)
            for gl_group in gl_groups:
                user_ids = [gl_user.id for gl_user in gl_group.members.list(all=True)]
                print(f"  Group {gl_group.name} ({len(user_ids)} members):")
                self.print_users(user_ids)


class GLSingleUser(GLUsers):
    """Handle a single gitlab user"""

    def __init__(self, user: str, *args: Any, **kwargs: Any):
        self.user = user
        super().__init__(*args, **kwargs)

        if self.user != "list":
            gl_userlist = self.gl.users.list(username=self.user)
            try:
                self.gl_user = gl_userlist[0]
            except IndexError:
                print(f"username {user} not found in GitLab.")
                print(self.list_usernames())
                sys.exit(1)

    def get_ssh_key(self) -> Optional[str]:
        """Return user most recent ssh key as a string"""
        keys = self.gl_user.keys.list()
        if keys:  # User has a ssh-key
            return keys[0].key
        else:
            print(f"No ssh key found for {self.gl_user.username}")

    def output(self):
        """Output users information"""

        if self.user == "list":
            print(self.list_usernames())
        else:
            # Filter by username
            self.print_users([self.gl_user.id])


class NewUser:
    """Create a user"""

    def __init__(self, userdict: Dict[str, Any], dry_run: bool = False):
        self.gl = connect_to_gitlab()
        self.url = self.gl.api_url
        self.all_gl_users = self.gl.users.list(all=True)
        self.userdict = userdict
        self.dry_run = dry_run
        if self.userdict["group"]:
            # save group info and delete from userdict
            if self.userdict["access_level"] not in ACCESS_LEVEL.keys():
                sys.exit(
                    f"Wrong access level: {self.userdict['access_level']}"
                    f" for group {self.userdict['group']}"
                )
            else:
                self.group = {
                    "name": self.userdict["group"],
                    "access_level": self.userdict["access_level"],
                }
                del self.userdict["group"]
                del self.userdict["access_level"]
        else:
            self.group = None
        # Trigger a password reset token and email notification
        self.userdict["reset_password"] = True

    def _check(self) -> bool:
        print("Checking...")
        print(self)

        gld = {
            "usernames": [gl_user.username for gl_user in self.all_gl_users],
            "emails": [gl_user.email for gl_user in self.all_gl_users],
            "names": [gl_user.name for gl_user in self.all_gl_users],
            "groupnames": [gl_group.name for gl_group in self.gl.groups.list(all=True)],
        }

        checkok = True
        for entry in "username", "email", "name":
            if self.userdict[entry] in gld[entry + "s"]:
                print(f"{entry.title()} {self.userdict[entry]} already used")
                checkok = False

        if self.group:
            try:
                self.gl.groups.get(self.group["name"])
            except gitlab.GitlabGetError as e:
                if e.response_body == "Group Not Found":
                    print(f'Group "{self.group["name"]}" does not exist.')
                    newgroup_url = self.url + "/admin/groups/new"
                    print(f"Create it using GitLab using this link: {newgroup_url}")
                    checkok = False
                else:
                    raise

        if checkok:
            print("... OK")

        return checkok

    def _create(self):
        print("Creating...")
        self.gluser = self.gl.users.create(self.userdict)
        # 'organization' and 'location' field are not created by current
        # version of python-gitlab (0.20) so add them using .save() method
        self.gluser.organization = self.userdict["organization"]
        self.gluser.location = self.userdict["location"]
        self.gluser.save()
        print(f"    User {self.userdict['username']} created")

    def _add_to_group(self):
        print("Adding to group...")
        if self.group:
            try:
                group = self.gl.groups.get(self.group["name"])
            except gitlab.GitlabGetError as e:
                if e.response_body == "Group Not Found":
                    sys.exit(f"Group {self.group['name']} not found")
                else:
                    raise
            access_level = ACCESS_LEVEL[self.group["access_level"]]
            group.members.create(
                {"user_id": self.gluser.id, "access_level": access_level}
            )
            print(
                f"    User {self.userdict['username']} added to group "
                f"{self.group['name']}"
            )
        else:
            sys.exit("No group for this new user")

    def save(self):
        """Check user info and create user if everything is ok"""

        if self._check() and not self.dry_run:
            self._create()
            if self.group:
                self._add_to_group()
        else:
            warn = "Dry run mode" if self.dry_run else "WARNING"
            print(f"\n{warn}: user {self.userdict['username']} will not be created\n")

    def __repr__(self) -> str:
        """Return a pretty output of user info"""
        output = self.userdict["name"]
        for entry in "username", "email", "organization", "location":
            output += f"    {entry:12} : {self.userdict[entry]}\n"

        if self.group:
            output += f"""\
    group        : {self.group["name"]} (as {self.group["access_level"]})"""

        return output


class OldUser:
    """Handle old users to delete"""

    def __init__(self, username: str, dry_run: bool = False):
        self.username = username
        self.dry_run = dry_run
        self.gl = connect_to_gitlab()
        self.url = self.gl.api_url
        gl_user_list = self.gl.users.list(username=self.username)
        if gl_user_list:
            self.gl_user = gl_user_list[0]
            self.skip_user = False
        else:
            print(f"WARNING: user {self.username} does not exist")
            self.skip_user = True

    def delete(self):
        if self.skip_user:
            print(f"WARNING: user {self.username} will not be deleted")
        else:
            print(
                f"""\
User {self.gl_user.username}:
    Name: {self.gl_user.name}
    Email: {self.gl_user.email}
"""
            )

            if not self.dry_run and query_yes_no("Delete?", default="no"):
                self.gl_user.delete()
                print(f"    User {self.username} deleted")
            else:
                message = "dry run mode" if self.dry_run else "deletion aborted"
                print(f"    User {self.username} not deleted ({message})")


def get_usernames_from_csv(filename: str) -> List[str]:
    """Return a list of usernames"""
    with open(filename, "r") as csvfile:
        csvreader = csv.reader(row for row in csvfile if not row.startswith("#"))
        return [row[0] for row in csvreader]


def get_users_from_csv(filename: str) -> List[Dict[str, Any]]:
    """Return a dict containing users information"""
    with open(filename, "r") as csvfile:
        fieldnames = (
            "username",
            "name",
            "email",
            "organization",
            "location",
            "group",
            "access_level",
        )
        # Filter csv file header
        csvreader = csv.reader(row for row in csvfile if not row.startswith("#"))
        stripped_reader = [[x.strip() for x in row] for row in csvreader]
        newusers = [dict(zip_longest(fieldnames, row)) for row in stripped_reader]

        return newusers


def main():
    """Get user input from command line and launch gitlab API"""

    description = "List GitLab users information and automate user accounts creation"

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--gitlab",
        required=False,
        help=(
            "Which configuration section should be used in "
            "~/.python-gitlab.cfg file. If not defined, the "
            "default selection will be used."
        ),
    )

    arg_filter = parser.add_mutually_exclusive_group()
    arg_filter.add_argument(
        "-g",
        nargs="?",
        const="list",
        required=False,
        metavar="group",
        help="List all groups [restrict to a GitLab \
                                  group]",
    )

    arg_filter.add_argument(
        "-u",
        nargs="?",
        const="list",
        required=False,
        metavar="user",
        help="List all users [restrict to a username]",
    )

    parser.add_argument(
        "--email-only",
        dest="email_only",
        action="store_true",
        default=False,
        help="Display only e-mail address",
    )

    parser.add_argument(
        "--name-only",
        dest="name_only",
        action="store_true",
        default=False,
        help="Display only name",
    )

    arg_show = parser.add_argument_group("Additional info")

    arg_show.add_argument(
        "--sign-in-date",
        dest="sign_in_date",
        action="store_true",
        default=False,
        help="Display last sign-in date",
    )
    arg_show.add_argument(
        "--username",
        dest="username",
        action="store_true",
        default=False,
        help="Display username as @username",
    )

    parser.add_argument(
        "--export-keys",
        dest="export_keys",
        action="store_true",
        default=False,
        help="Export ssh keys (first in user's ssh-key list)",
    )

    arg_activity = parser.add_mutually_exclusive_group()
    arg_activity.add_argument(
        "--unused",
        dest="unused",
        action="store_true",
        default=False,
        help="List unused accounts",
    )
    arg_activity.add_argument(
        "--sign-in",
        dest="sign_in",
        action="store_true",
        default=False,
        help="Display only users that have already \
                              signed in",
    )
    arg_activity.add_argument(
        "--active",
        dest="active",
        action="store_true",
        default=False,
        help="Display only active users",
    )

    arg_group = parser.add_mutually_exclusive_group()
    arg_group.add_argument(
        "--create-from",
        nargs=1,
        required=False,
        dest="create",
        metavar="csv_file",
        help="Create users from .csv file with format: "
        "username,name,email,[organization],[location], "
        "[group],[access_level]",
    )
    arg_group.add_argument(
        "--delete-from",
        nargs=1,
        required=False,
        dest="delete_from",
        metavar="text_file",
        help="Delete users using text (or csv) file",
    )
    arg_group.add_argument(
        "--delete",
        nargs=1,
        required=False,
        dest="delete",
        metavar="username",
        help="Delete user",
    )

    arg_group.add_argument(
        "--csv",
        action="store_true",
        required=False,
        dest="csv_out",
        default=False,
        help="CSV output with detailed information",
    )

    parser.add_argument(
        "-n",
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help=("Do not commit any change"),
    )
    args = parser.parse_args()

    if args.create:
        create_file = args.create[0]
        newuserdicts = get_users_from_csv(create_file)
        for userdict in newuserdicts:
            newuser = NewUser(userdict, dry_run=args.dry_run)
            newuser.save()

    elif args.delete_from:
        oldusernames = get_usernames_from_csv(args.delete_from[0])

        for username in oldusernames:
            olduser = OldUser(username, dry_run=args.dry_run)
            olduser.delete()

    elif args.delete:
        username = args.delete[0]
        olduser = OldUser(username, dry_run=args.dry_run)
        olduser.delete()

    else:
        # Print info to standard output

        activityd = {
            "unused": args.unused,
            "sign_in": args.sign_in,
            "active": args.active,
        }
        activity = [key for key in activityd.keys() if activityd[key]]

        if args.g:
            glu = GLGroups(
                args.g,
                args.gitlab,
                args.email_only,
                args.export_keys,
                args.username,
                activity,
                args.sign_in_date,
                args.name_only,
            )
        elif args.u:
            glu = GLSingleUser(
                args.u,
                args.gitlab,
                args.email_only,
                args.export_keys,
                args.username,
                activity,
                args.sign_in_date,
                args.name_only,
            )
        else:
            glu = GLUsers(
                args.gitlab,
                args.email_only,
                args.export_keys,
                args.username,
                activity,
                args.sign_in_date,
                args.name_only,
            )
        if args.csv_out:
            glu.out_csv()
        else:
            glu.output()


if __name__ == "__main__":
    main()
