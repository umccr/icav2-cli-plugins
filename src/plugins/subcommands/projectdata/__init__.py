#!/usr/bin/env python3

"""
Project data
"""

from subcommands import SuperCommand
import sys


class ProjectData(SuperCommand):
    """
Usage:
  icav2 projectdata <command> <args...>

CLI Commands:
  archive              archive data
  create               Create data id for a project
  delete               delete data
  download             Download a file/folder
  downloadurl          get download url
  folderuploadsession  Get details of a folder upload
  get                  Get details of a data
  link                 Link data to a project
  list                 List data
  mount                Mount project data
  temporarycredentials fetch temporal credentials for data
  unarchive            unarchive data
  unlink               Unlink data to a project
  unmount              Unmount project data
  update               Updates the details of a data
  upload               Upload a file/folder

Plugin Commands:
  ls                       List data with standard posix ls options
  view                     View a file and parse into stdout
  s3-sync-upload           Upload a directory to a project folder, calling aws s3 sync underneath
  s3-sync-download         Download a directory to a project folder, calling aws s3 sync underneath
  create-download-script   Create a shell script that downloads a project folder via presigned urls

Flags:
  -h, --help   help for projectanalyses

Global Flags:
  -t, --access-token string    JWT used to call rest service
  -o, --output-format string   output format (default "table")
  -s, --server-url string      server url to direct commands
  -k, --x-api-key string       api key used to call rest service

Use "icav2 projectdata [command] --help" for more information about a command.
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)

    def get_subcommand_obj(self, cmd, command_argv):

        if cmd == "ls":
            from subcommands.projectdata.ls import ProjectDataLs as subcommand
        elif cmd == "view":
            from subcommands.projectdata.view import ProjectDataView as subcommand
        elif cmd == "s3-sync-download":
            from subcommands.projectdata.s3_sync_download import S3SyncDownload as subcommand
        elif cmd == "s3-sync-upload":
            from subcommands.projectdata.s3_sync_upload import S3SyncUpload as subcommand
        elif cmd == "create-download-script":
            from subcommands.projectdata.create_download_script import CreateDownloadScript as subcommand
        else:
            print(self.__doc__)
            print(f"Could not find cmd \"{cmd}\". Please refer to usage above")
            sys.exit(1)

        # Initialise and return
        return subcommand(command_argv)







