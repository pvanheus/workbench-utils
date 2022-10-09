#!/usr/bin/env python3

import argparse
import json

from bioblend.galaxy import GalaxyInstance
from ephemeris.generate_tool_list_from_ga_workflow_files import (
    translate_workflow_dictionary_to_tool_list,
)
from ephemeris.shed_tools import InstallRepositoryManager
from ephemeris.ephemeris_log import (
    setup_global_logger,
    disable_external_library_logging,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel_label", default="Workbench Tools")
    parser.add_argument("--log_file")
    parser.add_argument("workflow_file", type=argparse.FileType())
    parser.add_argument("galaxy_url")
    parser.add_argument("api_key")
    args = parser.parse_args()

    disable_external_library_logging()
    logger = setup_global_logger(args.log_file)
    gi = GalaxyInstance(args.galaxy_url, args.api_key)
    install_manager = InstallRepositoryManager(gi)
    workflow_dict = json.load(args.workflow_file)
    tool_list = translate_workflow_dictionary_to_tool_list(
        workflow_dict, args.panel_label
    )
    install_manager.install_repositories(
        tool_list,
        log=logger,
        default_install_resolver_dependencies=False,
        default_install_repository_dependencies=False,
    )
