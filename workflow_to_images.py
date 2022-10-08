#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ephemeris.generate_tool_list_from_ga_workflow_files import  translate_workflow_dictionary_to_tool_list

from write_spec_string import get_image_name, get_tool_requirements

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true', default=False)
    parser.add_argument('-C', '--continue_after_failure', action='store_true', default=False)
    parser.add_argument('workflow_file', type=argparse.FileType())
    parser.add_argument('image_dir')
    args = parser.parse_args()

    image_store_path = Path(args.image_dir)
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
                # the images are sometimes stored as 'image_name:0' so use a glob to see if we already have this image
                # glob returns a generator - turn it into a list and then it is false is empty, true if not empty
                if args.force or not list(image_store_path.glob(f'{image_name}*')):
                    print(tool_name, tool_owner, revision, spec_string, image_name, file=sys.stderr)
                    build_cmd = ['mulled-build', 'build-and-test', '--test', 'echo', '--singularity', '--singularity-image-dir', str(image_store_path), spec_string]
                    try:
                        subprocess.run(build_cmd, check=True)
                    except subprocess.CalledProcessError:
                        if args.continue_after_failure:
                            print('BUILD FAILED, skipping', file=sys.stderr)
                        else:
                            sys.exit(1)

            
