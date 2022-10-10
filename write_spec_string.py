#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from typing import Union

from bioblend import toolshed
from galaxy.tool_util.deps.mulled.util import (
    v1_image_name,
    v2_image_name,
    build_target,
    Target,
)


def find_conda_package(target: Target) -> Target:
    # add build details from conda for package
    search_string = targets_to_spec_string([target])
    assert "," not in search_string
    conda_cmd = ["conda", "search", "--json", search_string]
    conda_proc = subprocess.run(conda_cmd, check=True, capture_output=True)
    conda_packages = json.loads(conda_proc.stdout)
    most_recent_package = sorted(
        conda_packages[target.package_name], key=lambda d: d["timestamp"], reverse=True
    )[0]
    conda_target = Target(
        target.package_name.lower(),
        target.version,
        most_recent_package["build"],
        target.package_name,
    )
    return conda_target


def get_tool_targets(
    tool_name: str,
    tool_author: str,
    tool_revision: str,
    tool_id: str,
    toolshed_name: str = "toolshed.g2.bx.psu.edu",
) -> Union[list[Target], None]:
    "Given a tool description, get the list of requirements"
    # this is how to get tool info from the toolshed
    toolshed_url = f"https://{toolshed_name}"
    ts = toolshed.ToolShedInstance(url=toolshed_url)
    result = ts.repositories.get_repository_revision_install_info(
        tool_name, tool_author, tool_revision
    )

    revisions_seen = set()
    for dictionary in result:
        if "downloadable" not in dictionary or not dictionary["downloadable"]:
            continue
        revision = dictionary["changeset_revision"]
        if "valid_tools" in dictionary:
            if revision in revisions_seen:
                continue
            tool_targets = []
            valid_tools_seen = 0
            # this dict contains a list of installable tools
            for tool in dictionary["valid_tools"]:
                if tool["id"] != tool_id:
                    continue
                valid_tools_seen += 1
                for requirement in tool["requirements"]:
                    if "version" in requirement:
                        tool_target = build_target(
                            requirement["name"], requirement["version"]
                        )
                    else:
                        tool_target = build_target(requirement["name"])
                    tool_targets.append(tool_target)
            if valid_tools_seen != 1:
                print(
                    "Warning: more than one matching tool for",
                    tool_name,
                    tool_id,
                    tool_author,
                    tool_revision,
                    file=sys.stderr,
                )
            if len(tool_targets) == 1:
                # single package target, we need to find the conda build details
                tool_targets = [find_conda_package(tool_targets[0])]
            return tool_targets


def get_image_name(
    tool_name: str,
    tool_author: str,
    tool_revision: str,
    tool_id: str,
    tool_shed: str,
    mulled_version: str = "v2",
) -> Union[str, None]:
    targets = get_tool_targets(
        tool_name, tool_author, tool_revision, tool_id, tool_shed
    )
    if targets is not None:
        if mulled_version == "v2":
            image_name = v2_image_name
        else:
            image_name = v1_image_name
        return image_name(targets)
    else:
        return None


def targets_to_spec_string(targets: list[Target]) -> str:
    spec_string = ",".join(f"{t.package_name}={t.version}" for t in targets)
    return spec_string


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mulled_version", default="v2")
    parser.add_argument("tool_name")
    parser.add_argument("tool_author")
    parser.add_argument("tool_revision")
    args = parser.parse_args()

    targets = get_tool_targets(args.tool_name, args.tool_author, args.tool_revision)
    spec_str = targets_to_spec_string(targets)
    print(
        spec_str,
        get_image_name(
            args.tool_name, args.tool_author, args.tool_revision, args.mulled_version
        ),
    )
