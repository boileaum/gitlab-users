#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Use GitLab API to:
    1) list gitlab users info
    2) automate user account creation/deletion
"""

from __future__ import print_function
from builtins import super, str, input
try:
    from itertools import zip_longest  # python3
except ImportError:
    from itertools import izip_longest as zip_longest  # python2

import argparse
import csv
from datetime import datetime, timedelta
import gitlab
import os
import sys


ACCESS_LEVEL = {'guest': gitlab.GUEST_ACCESS,
                'reporter': gitlab.REPORTER_ACCESS,
                'developer': gitlab.DEVELOPER_ACCESS,
                'master': gitlab.MASTER_ACCESS,
                'maintainer': gitlab.MASTER_ACCESS,
                'owner': gitlab.OWNER_ACCESS}


def query_yes_no(question, default="no"):
    """
    (From https://gist.github.com/hrouault/1358474)
    Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
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
        if default and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def connect_to_gitlab(gitlab_id=None):
    """Return a connection to GitLab API"""
    try:
        gl = gitlab.Gitlab.from_config(gitlab_id)
    except (gitlab.config.GitlabIDError, gitlab.config.GitlabDataError,
            gitlab.config.GitlabConfigMissingError) as e:
        print("Exception in python-gitlab: {}.\n".format(e),
              "Check python-gitlab configuration on",
              "http://python-gitlab.readthedocs.io/en/stable/cli.html",
              file=sys.stderr)
        sys.exit(1)

    return gl


class GLUsers(object):
    """A mother class to handle gitlab users"""

    def __init__(self, gitlab_id=None, email_only=False, export_keys=False,
                 username=False, activity=None, sign_in_date=False,
                 name_only=False, gl=None):

        self.gitlab_id = gitlab_id
        self.email_only = email_only
        self.name_only = name_only
        self.export_keys = export_keys
        self.username = username
        self.activity = activity
        self.sign_in_date = sign_in_date

        self.gl = connect_to_gitlab(self.gitlab_id) if gl is None else gl
        self.url = self.gl.api_url
        self.all_gl_users = self.gl.users.list(all=True)
        self.alluser_ids = [gl_user.id for gl_user in self.all_gl_users]

        # Create a {id: user} dictionary from user_ids list
        self.userdict = {key: value for (key, value)
                         in zip(self.alluser_ids, self.all_gl_users)}

    @staticmethod
    def _format_date(gl_user,field):
        """Format date field"""
        if getattr(gl_user, field):
            return getattr (gl_user,field).split('T')[0]
        else:
            return None

    @staticmethod
    def _sign_in_date(gl_user):
        """Return user sign-in date"""
        return __class__._format_date(gl_user,"current_sign_in_at")

    def _sign_in_date_and_time(self, gl_user):
        """Return user sign-in date and time"""
        return datetime.strptime(self._sign_in_date(gl_user), "%Y-%m-%d")

    def user_info(self, gl_user):
        """Return info for given user"""
        if self.email_only:
            info = gl_user.email
        elif self.name_only:
            info = gl_user.name
        else:
            info = u"{} <{}>".format(str(gl_user.name), gl_user.email)
            # Complete with additional info
            if self.username:
                info = "@{} ".format(gl_user.username) + info
            if self.sign_in_date:
                info = info + " ({})".format(self._sign_in_date(gl_user))
        return info

    def list_usernames(self):
        usernames = [gl_user.username for gl_user in self.all_gl_users]
        msg = "Existing usernames ({}):".format(len(usernames))
        for username in sorted(usernames):
            msg = msg + "\n - {}".format(username)
        return msg

    def print_users(self, user_ids):
        """Print info for a list of users and collect ssh_keys"""

        nokey_gl_users = []

        for user_id in user_ids:
            gl_user = self.userdict[user_id]
            if self.export_keys:
                key_dir = 'ssh_keys'
                if not os.path.exists(key_dir):
                    os.mkdir(key_dir)
                keys = gl_user.keys.list()
                if keys:  # User has a ssh-key
                    print(self.user_info(gl_user))
                    key = keys[0].key
                    key_filename = "{}/{}.pub".format(key_dir,
                                                      gl_user.username)
                    with open(key_filename, 'w') as f:
                        f.write(key)

                else:
                    nokey_gl_users.append(gl_user)

            else:
                print(self.user_info(gl_user))

        if self.export_keys:
            print("--")
            nuser = len(user_ids)
            nuser_key = len(user_ids) - len(nokey_gl_users)
            print("{}/{} users has an ssh key.".format(nuser_key, nuser))
            if nokey_gl_users:
                print("--")
                print("The following users has no ssh key:\n")
                for gl_user in nokey_gl_users:
                    print(self.user_info(gl_user))
                print("--")

    def _getactivity(self):

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
                if gl_user.state == 'active':
                    already_sign_in.append(gl_user)
                    if current_sign_in < datetime.now() - \
                       timedelta(days=365):
                        old_sign_in.append(gl_user)
                    else:
                        active.append(gl_user)
            elif gl_user.state == 'active':
                never_sign_in.append(gl_user)

        return (old_sign_in,never_sign_in,already_sign_in,active)

    def output(self):
        """Output users information"""
        if self.activity:
            (old_sign_in, never_sign_in, already_sign_in,active) = self._getactivity()

            if 'unused' in self.activity:
                print("  Users whose last connexion is older than 1 year:")
                for gl_user in old_sign_in:
                    print(self.user_info(gl_user))
                print("  Users who never signed in:")
                for gl_user in never_sign_in:
                    print(self.user_info(gl_user))

            elif 'sign_in' in self.activity:
                print("  Users who have already signed in:")
                for gl_user in already_sign_in:
                    print(self.user_info(gl_user))
            
            elif 'active' in self.activity:
                print(f"""\
  Active users (last connection < 1 year) [{len(active)}]:""")
                for gl_user in active:
                    print(self.user_info(gl_user))               
        else:
            self.print_users(self.alluser_ids)

    @staticmethod
    def _getuids(gl_users):
        return [gu.id for gu in gl_users]

    def user_info_csv(self, gl_user):
        """Return info for given user in csv"""
        ## Username, E-mail, Name, State, isAdmin, isExternal, LastSignInAt, CreatedAt
        info = u"{},{},\"{}\",{},{},{},{},{}".format(gl_user.username, gl_user.email, str(gl_user.name), gl_user.state, gl_user.is_admin, gl_user.external, self._format_date(gl_user,"last_sign_in_at"), self._format_date(gl_user,"created_at"))
        # Complete with additional info
        return info

    def print_users_csv(self, user_ids):
        """Print csv listing of users"""

        for user_id in user_ids:
            gl_user = self.userdict[user_id]
            print(self.user_info_csv(gl_user))

    def out_csv(self):
        """Output csv of all users"""
        print("Username,E-mail,\"Name\",State,isAdmin,isExternal,LastSignInAt,CreatedAt")
        if self.activity:
            (old_sign_in, never_sign_in, already_sign_in,active) = self._getactivity()
            if 'unused' in self.activity:
                #print("  Users whose last connexion is older than 1 year:")
                #print("  Users who never signed in:")
                self.print_users_csv(self._getuids(old_sign_in + never_sign_in))

            elif 'sign_in' in self.activity:
                #print("  Users who have already signed in:")
                self.print_users_csv(self._getuids(already_sign_in))
            elif 'active' in self.activity:
                #print(f"""Active users (last connection < 1 year) [{len(active)}]:""")
                self.print_users_csv(self._getuids(active))
        else:
            self.print_users_csv(self.alluser_ids)


class GLGroups(GLUsers):
    """A class to handle a group of gitlab users"""

    def __init__(self, groups, *args, **kwargs):

        self.groups = groups
        super().__init__(*args, **kwargs)
        self.all_gl_groups = self.gl.groups.list(all=True)

    def list_all_groups(self):
        groupnames = [gl_group.name for gl_group in self.all_gl_groups]
        msg = "Existing groups ({}):".format(len(groupnames))
        for groupname in sorted(groupnames):
            msg = msg + "\n - {}".format(groupname)
        return msg

    def output(self):
        """Output users information"""

        if self.groups == 'list':
            print(self.list_all_groups())
            sys.exit(0)
        else:
            gl_groups = self.gl.groups.list(search=self.groups)

            if not gl_groups:
                print("No group matching {} found on {}.".format(self.groups,
                                                                 self.url))
                print(self.list_all_groups())
                sys.exit(1)
            for gl_group in gl_groups:
                user_ids = [gl_user.id for gl_user
                            in gl_group.members.list(all=True)]
                print("  Group {} ({} members):".format(gl_group.name,
                                                        len(user_ids)))
                self.print_users(user_ids)


class GLSingleUser(GLUsers):
    """A class to handle a single gitlab user"""

    def __init__(self, user, *args, **kwargs):

        self.user = user
        super().__init__(*args, **kwargs)

        if self.user != 'list':
            gl_userlist = self.gl.users.list(username=self.user)
            try:
                self.gl_user = gl_userlist[0]
            except IndexError:
                print("username {} not found in GitLab.".format(user))
                print(self.list_usernames())
                sys.exit(1)

    def get_ssh_key(self):
        """Return user most recent ssh key as a string"""
        keys = self.gl_user.keys.list()
        if keys:  # User has a ssh-key
            return keys[0].key
        else:
            print("No ssh key found for {}".format(self.gl_user.username))

    def output(self):
        """Output users information"""

        if self.user == 'list':
            print(self.list_usernames())
        else:
            # Filter by username
            self.print_users([self.gl_user.id])


class NewUser():
    """A class to create a user"""

    def __init__(self, userdict, dry_run=False):
        self.gl = connect_to_gitlab()
        self.url = self.gl.api_url
        self.all_gl_users = self.gl.users.list(all=True)
        self.userdict = userdict
        self.dry_run = dry_run
        if self.userdict['group']:
            # save group info and delete from userdict
            if self.userdict['access_level'] not in ACCESS_LEVEL.keys():
                sys.exit("Wrong access level: {} for group {}".format(
                    self.userdict['access_level'], self.userdict['group']))
            else:
                self.group = {'name': self.userdict['group'],
                              'access_level': self.userdict['access_level']}
                del self.userdict['group']
                del self.userdict['access_level']
        else:
            self.group = None
        # Trigger a password reset token and email notification
        self.userdict['reset_password'] = True

    def _check(self):
        print("Checking...")
        print(self)

        gl = {'usernames': [gl_user.username for gl_user in self.all_gl_users],
              'emails': [gl_user.email for gl_user in self.all_gl_users],
              'names': [gl_user.name for gl_user in self.all_gl_users],
              'groupnames': [gl_group.name for gl_group in
                             self.gl.groups.list(all=True)]
              }

        checkok = True
        for entry in 'username', 'email', 'name':
            if self.userdict[entry] in gl[entry + 's']:
                print("{} {} already used".format(
                    entry.title(),
                    self.userdict[entry]))
                checkok = False

        if self.group:
            try:
                self.gl.groups.get(self.group['name'])
            except gitlab.GitlabGetError as e:
                if e.response_body == 'Group Not Found':
                    print('Group "{}" does not exist.'.format(
                        self.group['name']))
                    newgroup_url = self.url + "/admin/groups/new"
                    print("Create it using GitLab using this link: {}"
                          .format(newgroup_url))
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
        self.gluser.organization = self.userdict['organization']
        self.gluser.location = self.userdict['location']
        self.gluser.save()
        print("    User {} created".format(self.userdict['username']))

    def _add_to_group(self):

        print("Adding to group...")
        if self.group:
            try:
                group = self.gl.groups.get(self.group['name'])
            except gitlab.GitlabGetError as e:
                if e.response_body == 'Group Not Found':
                    sys.exit("Group {} not found".format(self.group['name']))
                else:
                    raise
            access_level = ACCESS_LEVEL[self.group['access_level']]
            group.members.create({'user_id': self.gluser.id,
                                  'access_level': access_level})
            print("    User {} added to group {}".format(
                self.userdict['username'], self.group['name']))
        else:
            sys.exit("No group for this new user")

    def save(self):
        if self._check() and not self.dry_run:
            self._create()
            if self.group:
                self._add_to_group()

        else:
            warn = "Dry run mode" if self.dry_run else "WARNING"
            print("\n{}: user {} will not be created\n".format(warn,
                  self.userdict['username']))

    def __repr__(self):
        """Return a pretty output of user info"""
        output = self.userdict['name']
        for entry in 'username', 'email', 'organization', 'location':
            output = output + """
    {:12} : {}""".format(entry, self.userdict[entry])

        if self.group:
            output = output + """
    group        : {} (as {})""".format(self.group['name'],
                                        self.group['access_level'])
        return output


class OldUser():
    """Handle old users to delete"""

    def __init__(self, username, dry_run=False):
        self.username = username
        self.dry_run = dry_run
        self.gl = connect_to_gitlab()
        self.url = self.gl.api_url
        gl_user_list = self.gl.users.list(username=self.username)
        if gl_user_list:
            self.gl_user = gl_user_list[0]
            self.skip_user = False
        else:
            print("WARNING: user {} does not exist".format(self.username))
            self.skip_user = True

    def delete(self):
        if self.skip_user:
            print("WARNING: user {} will not be deleted".format(
                  self.username))
        else:
            print("User {}:".format(self.gl_user.username))
            print("    Name: {}".format(self.gl_user.name))
            print("    Email: {}".format(self.gl_user.email))

            if not self.dry_run and query_yes_no("Delete?", default="no"):
                self.gl_user.delete()
                print("    User {} deleted".format(self.username))
            else:
                message = "dry run mode" if self.dry_run \
                          else "deletion aborted"
                print("    User {} not deleted ({})".format(self.username,
                                                            message))


def get_usernames_from_csv(filename):
    """Return a list of usernames"""
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(row for row in csvfile
                               if not row.startswith('#'))
        return [row[0] for row in csvreader]


def get_users_from_csv(filename):
    """Return a dict containing users information"""
    with open(filename, 'r') as csvfile:
        fieldnames = 'username', 'name', 'email', 'organization', 'location', \
                     'group', 'access_level'
        # Filter csv file header
        csvreader = csv.reader(row for row in csvfile
                               if not row.startswith('#'))
        stripped_reader = [[x.strip() for x in row] for row in csvreader]
        newusers = [dict(zip_longest(fieldnames, row))
                    for row in stripped_reader]

        return newusers


def main():
    """Get user input from command line and launch gitlab API"""

    description = ("List GitLab users information and "
                   "automate user accounts creation")

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('--gitlab', required=False,
                        help=("Which configuration section should be used in "
                              "~/.python-gitlab.cfg file. If not defined, the "
                              "default selection will be used."))

    arg_filter = parser.add_mutually_exclusive_group()
    arg_filter.add_argument('-g', nargs='?', const='list', required=False,
                            metavar="group",
                            help="List all groups [restrict to a GitLab \
                                  group]")

    arg_filter.add_argument('-u', nargs='?', const='list', required=False,
                            metavar="user",
                            help="List all users [restrict to a username]")

    parser.add_argument('--email-only', dest='email_only',
                        action='store_true',
                        default=False,
                        help="Display only e-mail address")

    parser.add_argument('--name-only', dest='name_only',
                        action='store_true',
                        default=False,
                        help="Display only name")

    arg_show = parser.add_argument_group('Additional info')

    arg_show.add_argument('--sign-in-date', dest='sign_in_date',
                          action='store_true', default=False,
                          help="Display last sign-in date")
    arg_show.add_argument('--username', dest='username', action='store_true',
                          default=False,
                          help="Display username as @username")

    parser.add_argument('--export-keys', dest='export_keys',
                        action='store_true', default=False,
                        help="Export ssh keys (first in user's ssh-key list)")

    arg_activity = parser.add_mutually_exclusive_group()
    arg_activity.add_argument('--unused', dest='unused',
                              action='store_true', default=False,
                              help="List unused accounts")
    arg_activity.add_argument('--sign-in', dest='sign_in',
                              action='store_true', default=False,
                              help="Display only users that have already \
                              signed in")
    arg_activity.add_argument('--active', dest='active',
                              action='store_true', default=False,
                              help="Display only active users")

    arg_group = parser.add_mutually_exclusive_group()
    arg_group.add_argument('--create-from', nargs=1, required=False,
                           dest='create', metavar="csv_file",
                           help="Create users from .csv file with format: "
                           "username,name,email,[organization],[location], "
                           "[group],[access_level]")
    arg_group.add_argument('--delete-from', nargs=1, required=False,
                           dest='delete_from', metavar="text_file",
                           help="Delete users using text (or csv) file")
    arg_group.add_argument('--delete', nargs=1, required=False,
                           dest='delete', metavar="username",
                           help="Delete user")

    arg_group.add_argument('--csv', action='store_true', required=False,
                           dest='csv_out', default=False,
                           help="CSV output with detailed information")

    parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true',
                        help=("Do not commit any change"))
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

        activityd = {'unused': args.unused,
                     'sign_in': args.sign_in,
                     'active': args.active}
        activity = [key for key in activityd.keys() if activityd[key]]

        if args.g:
            glu = GLGroups(args.g, args.gitlab, args.email_only,
                           args.export_keys, args.username, activity,
                           args.sign_in_date, args.name_only)
        elif args.u:
            glu = GLSingleUser(args.u, args.gitlab, args.email_only,
                               args.export_keys, args.username, activity,
                               args.sign_in_date, args.name_only)
        else:
            glu = GLUsers(args.gitlab, args.email_only,
                          args.export_keys, args.username, activity,
                          args.sign_in_date, args.name_only)
        if args.csv_out:
            glu.out_csv()
        else:
            glu.output()


if __name__ == "__main__":
    main()
