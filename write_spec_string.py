#!/usr/bin/env python3

import argparse
import sys
from typing import Union

from bioblend import toolshed
from galaxy.tool_util.deps.mulled.mulled_build import target_str_to_targets
from galaxy.tool_util.deps.mulled.util import v1_image_name, v2_image_name


def get_tool_requirements(tool_name: str, tool_author: str, tool_revision: str,
                         toolshed_name: str = 'toolshed.g2.bx.psu.edu') -> Union[str, None]:
    "Given a tool description, get the list of requirements"
    # this is how to get tool info from the toolshed
    toolshed_url = f'https://{toolshed_name}'
    ts = toolshed.ToolShedInstance(url=toolshed_url)
    result = ts.repositories.get_repository_revision_install_info(
        tool_name, tool_author, tool_revision)

    for dictionary in result:
        if 'valid_tools' in dictionary:
            spec_strs = []
            # this dict contains a list of installable tools
            for tool in dictionary['valid_tools']:
                for requirement in tool['requirements']:
                    if 'version' in requirement:
                        spec_str = f'{requirement["name"]}=={requirement["version"]}'
                        spec_strs.append(spec_str)
                    else:
                        print(f'unversioned {requirement["name"]}', file=sys.stderr)
            return ','.join(spec_strs)


def get_image_name(tool_name: str, tool_author: str, tool_revision: str, mulled_version='v2') -> Union[str, None]:
    targets = target_str_to_targets(get_tool_requirements(tool_name, tool_author, tool_revision))
    if targets is not None:
        if mulled_version == 'v2':
            image_name = v2_image_name
        else:
            image_name = v1_image_name
        return image_name(targets)
    else:
        return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mulled_version', default='v2')
    parser.add_argument('tool_name')
    parser.add_argument('tool_author')
    parser.add_argument('tool_revision')
    args = parser.parse_args()

    print(get_image_name(args.tool_name, args.tool_author, args.tool_revision, args.mulled_version))
