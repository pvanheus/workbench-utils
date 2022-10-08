#!/usr/bin/env python3

import argparse
import json
import subprocess
from pathlib import Path

from ephemeris.generate_tool_list_from_ga_workflow_files import  translate_workflow_dictionary_to_tool_list

from write_spec_string import get_image_name, get_tool_requirements

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true', default=False)
    parser.add_argument('workflow_file', type=argparse.FileType())
    parser.add_argument('image_dir')
    args = parser.parse_args()

    image_store_path = Path(args.image_name)
    if not image_store_path.exists():
        image_store_path.mkdir(mode=0o0755)
    
    workflow_dict = json.load(args.workflow_file)
    tool_list = translate_workflow_dictionary_to_tool_list(workflow_dict, 'label')
    for tool in tool_list:
        for revision in tool['revisions']:
            tool_name = tool['name']
            tool_owner = tool['owner']
            image_name = get_image_name(tool_name, tool_owner, revision)
            spec_string = get_tool_requirements(tool_name, tool_owner, revision)
            if spec_string is not None:
                image_path = image_store_path / image_name
                if args.force or not image_name.exists():
                    build_cmd = ['mulled-build', 'build-and-test', '--test', 'echo', '--singularity', '--singularity-image-dir', str(image_path)] + spec_string
                    subprocess.run(build_cmd, check=True)

            
