#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
import requests
from pathlib import Path

from ephemeris.generate_tool_list_from_ga_workflow_files import (
    translate_workflow_dictionary_to_tool_list,
)

from write_spec_string import get_image_name, get_tool_targets, targets_to_spec_string


def download(image_def, force=False) -> tuple[bool, int]:
    url = f"https://depot.galaxyproject.org/singularity/{image_def}"
    image_path = image_store_path / f"{image_def}"
    if not force and image_path.exists():
        # image already exists
        return (True, 200)

    response = requests.get(url)
    if response.status_code == 200:
        open(image_path, "wb").write(response.content)
        return (True, response.status_code)
    else:
        return (False, response.status_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-build-images", action="store_true", default=False)
    parser.add_argument("--list_only", action="store_true", default=False)
    parser.add_argument("--force", action="store_true", default=False)
    parser.add_argument(
        "-C", "--continue_after_failure", action="store_true", default=False
    )
    parser.add_argument("workflow_file", type=argparse.FileType())
    parser.add_argument("image_dir")
    args = parser.parse_args()

    image_store_path = Path(args.image_dir)
    if not image_store_path.exists():
        image_store_path.mkdir(mode=0o0755)

    workflow_dict = json.load(args.workflow_file)
    tool_list = translate_workflow_dictionary_to_tool_list(workflow_dict, "label")
    for tool in tool_list:
        for revision in tool["revisions"]:
            tool_name = tool["name"]
            tool_owner = tool["owner"]
            image_name = get_image_name(tool_name, tool_owner, revision)
            targets = get_tool_targets(tool_name, tool_owner, revision)
            if targets is not None:
                spec_string = targets_to_spec_string(targets)
                if args.list_only:
                    print(tool_name, revision, spec_string, image_name)
                else:
                    # assume build_number is 3, 2, 1 or 0 - don't know how to calculate
                    # this for now
                    downloaded = False
                    if len(targets) == 1:
                        (downloaded, status_code) = download(image_name)
                        if downloaded:
                            print(
                                tool_name,
                                tool_owner,
                                revision,
                                "downloaded",
                                image_name,
                                file=sys.stderr,
                            )
                    else:
                        for image_build in (3, 2, 1, 0):
                            image_def = f"{image_name}-{image_build}"
                            (downloaded, status_code) = download(image_def)
                            if downloaded:
                                print(
                                    tool_name,
                                    tool_owner,
                                    revision,
                                    "downloaded",
                                    f"{image_name}-{image_build}",
                                    file=sys.stderr,
                                )
                                break
                            elif status_code == 404:
                                # try again with a different URL
                                continue
                    if not downloaded:
                        print(
                            "Download failed for",
                            tool_name,
                            tool_owner,
                            revision,
                            targets,
                        )
                    if not downloaded and not args.no_build_images:
                        image_path = image_store_path / f"{image_name}-{image_build}"
                        if args.force or not image_path.exists():
                            print(
                                tool_name,
                                tool_owner,
                                revision,
                                spec_string,
                                image_name,
                                file=sys.stderr,
                            )
                            build_cmd = [
                                "mulled-build",
                                "build-and-test",
                                "--test",
                                "echo",
                                "--singularity",
                                "--singularity-image-dir",
                                str(image_store_path),
                                spec_string,
                            ]
                            try:
                                subprocess.run(build_cmd, check=True)
                            except subprocess.CalledProcessError:
                                if args.continue_after_failure:
                                    print("BUILD FAILED, skipping", file=sys.stderr)
                                else:
                                    sys.exit(1)
