#
# Copyright (C) 2020 IBM. All Rights Reserved.
#
# See LICENSE.txt file in the root directory
# of this source tree for licensing information.
#

# pylint: disable=no-name-in-module,import-error
import getpass
import json
import os
import sys
import io
from distutils.dir_util import remove_tree

from clai.datasource.config_storage import ConfigStorage
from clai.datasource.stats_tracker import StatsTracker
from clai.server.agent_datasource import AgentDatasource
from clai.tools.anonymizer import Anonymizer
from clai.tools.console_helper import print_complete, print_error
from clai.tools.file_util import get_rc_file, get_setup_file, get_rc_files


def remove(path):
    print("cleaning %s" % path)
    try:
        remove_tree(path)
    except OSError:
        print('folder not found')


def remove_system_folder():
    default_system_destdir = os.path.join(
        os.path.expanduser('/opt/local/share'),
        'clai',
    )
    remove(default_system_destdir)


def clai_installed(rc_file_path):
    path = os.path.expanduser(rc_file_path)
    if os.path.isfile(path):
        line_to_search = "export CLAI_PATH="
        print("searching %s" % line_to_search)
        lines = io.open(path, 'r',
                        encoding='utf-8',
                        errors='ignore').readlines()
        lines_found = list(filter(lambda line: line_to_search in line, lines))

        if lines_found:
            my_path = lines_found[0].replace(line_to_search, '').replace('\n', '').strip()
            return my_path

    return None


def is_root_user():
    return os.geteuid() == 0


# pylint: disable=bare-except
def read_users(bin_path):
    try:
        with open(bin_path + '/usersInstalled.json') as file:
            users = json.load(file)
            return users
    except:
        return []


def unregister_the_user(bin_path):
    users = read_users(bin_path)
    user_path = os.path.expanduser(get_rc_file())
    if user_path in users:
        users.remove(user_path)

    with open(bin_path + '/usersInstalled.json', 'w') as json_file:
        json.dump(users, json_file)

    return users


def stat_uninstall(bin_path):
    agent_datasource = AgentDatasource(config_storage=ConfigStorage(alternate_path=f'{bin_path}/configPlugins.json'))
    report_enable = agent_datasource.get_report_enable()
    stats_tracker = StatsTracker(sync=True, anonymizer=Anonymizer(alternate_path=f'{bin_path}/anonymize.json'))
    stats_tracker.report_enable = report_enable
    login = getpass.getuser()
    stats_tracker.log_uninstall(login)
    print("record uninstall")


def remove_setup_file(rc_file_path):
    path = os.path.expanduser(rc_file_path)
    os.remove(path)



def remove_between(rc_file_path, start, end):
    path = os.path.expanduser(rc_file_path)
    if os.path.isfile(path):
        lines = io.open(path, 'r',
                        encoding='utf-8',
                        errors='ignore').readlines()

        remove_line = False
        lines_after_remove = []
        for line in lines:
            if line.strip() == start.strip():
                remove_line = True
            if not remove_line:
                lines_after_remove.append(line)

            if line.strip() == end.strip():
                remove_line = False

        io.open(path, 'w').writelines(lines_after_remove)


def remove_lines_setup(rc_file_path):
    remove_between(rc_file_path, "# CLAI setup\n", "# End CLAI setup\n")


def remove_setup_register():
    rc_files = get_rc_files()

    for file in rc_files:
        remove_lines_setup(file)


def execute():
    path = clai_installed(get_setup_file())
    if not path:
        print_error('CLAI is not installed.')
        sys.exit(1)

    stat_uninstall(path)
    users = unregister_the_user(path)
    if not users:
        remove_system_folder()

    remove_setup_file(get_setup_file())
    remove_setup_register()

    print_complete("CLAI has been uninstalled correctly, you need restart your shell.")

    sys.exit(0)


if __name__ == '__main__':
    sys.exit(execute())
