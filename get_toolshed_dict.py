#!/usr/bin/env python3

import argparse
import json
import sys

from bioblend import toolshed


def get_toolshed_dict(
    tool_name: str,
    tool_author: str,
    tool_revision: str,
    toolshed_name: str = "toolshed.g2.bx.psu.edu",
) -> str:
    "Given a tool description, get the list of requirements"
    # this is how to get tool info from the toolshed

    toolshed_url = f"https://{toolshed_name}"
    ts = toolshed.ToolShedInstance(url=toolshed_url)
    result = ts.repositories.get_repository_revision_install_info(
        tool_name, tool_author, tool_revision
    )
    return json.dumps(result, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_file", type=argparse.FileType("w"), default=sys.stdout
    )
    parser.add_argument("tool_name")
    parser.add_argument("tool_author")
    parser.add_argument("tool_revision")
    args = parser.parse_args()
    tool_json = get_toolshed_dict(args.tool_name, args.tool_author, args.tool_revision)
    args.output_file.write(tool_json + "\n")
