#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Use GitLab API to:
    1) list gitlab users info
    2) automate user account creation/deletion
"""

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
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def connect_to_gitlab(gitlab_id=None):
    """Return a connection to GitLab API"""
    try:
        gl = gitlab.Gitlab.from_config(gitlab_id)
        url = gl._url.split('/api/v')[0]
    except (gitlab.config.GitlabIDError, gitlab.config.GitlabDataError) as e:
        print("Exception in python-gitlab: {}.\n".format(e),
              "Check python-gitlab configuration on",
              "http://python-gitlab.readthedocs.io/en/stable/cli.html",
              file=sys.stderr)
        sys.exit(1)

    return gl, url


class GLUsers():
    """A mother class to handle gitlab users"""

    def __init__(self, gitlab_id=None, email_only=False, export_keys=False,
                 username=False, activity=[], sign_in_date=False):

        self.gitlab_id = gitlab_id
        self.email_only = email_only
        self.export_keys = export_keys
        self.username = username
        self.activity = activity
        self.sign_in_date = sign_in_date

        self.gl, self.url = connect_to_gitlab(self.gitlab_id)
        self.all_gl_users = self.gl.users.list(all=True)
        self.alluser_ids = [gl_user.id for gl_user in self.all_gl_users]

        # Create a {id: user} dictionary from user_ids list
        self.userdict = {key: value for (key, value)
                         in zip(self.alluser_ids, self.all_gl_users)}

    def _sign_in_date(self, gl_user):
        """Return user sign-in date"""
        if gl_user.current_sign_in_at:
            return gl_user.current_sign_in_at.split('T')[0]
        else:
            return None

    def _sign_in_date_and_time(self, gl_user):
        """Return user sign-in date and time"""
        return datetime.strptime(self._sign_in_date(gl_user), "%Y-%m-%d")

    def user_info(self, gl_user):
        """Return info for given user"""
        if self.email_only:
            info = gl_user.email
        else:
            info = "{} <{}>".format(gl_user.name, gl_user.email)
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

    def print_users(self, user_ids, groupname=None):
        """Print info for a list of users"""

        nokey_gl_users = []

        for user_id in user_ids:
            gl_user = self.userdict[user_id]
            if self.export_keys:
                key_dir = 'ssh_keys'
                if not os.path.exists(key_dir):
                    os.mkdir(key_dir)
                keys = gl_user.keys.list()
                if keys:  # User has a ssh-key
                    sys.stdout.buffer.write(self.user_info(gl_user))
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

    def output(self):
        """Output users information"""

        if self.activity:

            old_sign_in = []
            never_sign_in = []
            already_sign_in = []
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
                elif gl_user.state == 'active':
                    never_sign_in.append(gl_user)

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
        else:
            self.print_users(self.alluser_ids)


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
            gl_groups = self.gl.groups.search(self.groups)

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
                self.print_users(user_ids, groupname=gl_group.name)


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

    def __init__(self, userdict):
        self.gl, self.url = connect_to_gitlab()
        self.all_gl_users = self.gl.users.list(all=True)
        self.userdict = userdict
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

        gl = {}
        gl['usernames'] = [gl_user.username for gl_user in self.all_gl_users]
        gl['emails'] = [gl_user.email for gl_user in self.all_gl_users]
        gl['names'] = [gl_user.name for gl_user in self.all_gl_users]
        gl['groupnames'] = [gl_group.name for gl_group in
                            self.gl.groups.list(all=True)]
        checkok = True
        for entry in 'username', 'email', 'name':
            if self.userdict[entry] in gl[entry + 's']:
                print("{} {} already used".format(
                       entry.title(),
                       self.userdict[entry]))
                checkok = False

        if self.group:
            if self.group['name'] not in gl['groupnames']:
                print('Group "{}" does not exist.'.format(self.group['name']))
                newgroup_url = self.url + "/admin/groups/new"
                print("Create it using GitLab using this link: {}"
                      .format(newgroup_url))
                checkok = False

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
            groups = self.gl.groups.search(self.group['name'])
            if len(groups) == 1 and self.group['name'] == groups[0].name:
                access_level = ACCESS_LEVEL[self.group['access_level']]
                group_id = groups[0].id
                self.gl.group_members.create({'user_id': self.gluser.id,
                                              'access_level': access_level},
                                             group_id=group_id)
                print("    User {} added to group {}".format(
                        self.userdict['username'], self.group['name']))
            else:
                sys.exit("Group {} not found".format(self.group['name']))
        else:
            sys.exit("No group for this new user")

    def save(self):
        if self._check():
            self._create()
            if self.group:
                self._add_to_group()

        else:
            print("\nWARNING: user {} will not be created\n".format(
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

    def __init__(self, username):
        self.username = username
        self.gl, self.url = connect_to_gitlab()
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

            if query_yes_no("Delete?", default="no"):
                self.gl_user.delete()
                print("    User {} deleted".format(self.username))
            else:
                print("    User {} not deleted".format(self.username))


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
        newusers = [dict(zip(fieldnames, row)) for row in csvreader]

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

    args = parser.parse_args()

    if args.create:
        create_file = args.create[0]
        newuserdicts = get_users_from_csv(create_file)
        for userdict in newuserdicts:
            newuser = NewUser(userdict)
            newuser.save()

    elif args.delete_from:
        oldusernames = get_usernames_from_csv(args.delete_from[0])

        for username in oldusernames:
            olduser = OldUser(username)
            olduser.delete()

    elif args.delete:
        username = args.delete[0]
        olduser = OldUser(username)
        olduser.delete()

    else:
        # Print info to standard output

        activityd = {'unused': args.unused,
                     'sign_in': args.sign_in}
        activity = [key for key in activityd.keys() if activityd[key]]

        if args.g:
            glu = GLGroups(args.gitlab, args.g, args.email_only,
                           args.export_keys, args.username, activity,
                           args.sign_in_date)
        elif args.u:
            glu = GLSingleUser(args.gitlab, args.u, args.email_only,
                               args.export_keys, args.username, activity,
                               args.sign_in_date)
        else:
            glu = GLUsers(args.gitlab, args.email_only, args.export_keys,
                          args.username, activity, args.sign_in_date)

        glu.output()

if __name__ == "__main__":
    main()
