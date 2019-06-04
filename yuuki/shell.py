#!/usr/bin/env python

import requests
import sys
import json
import yaml
import readline
import re

HEADERS = {"Content-Type": "application/json"}

ACTUATOR = r"\A(\S+)\s+(\S+)\s+(\{.*\})\s+(\S+)\s+(\{.*\})(\s+.*)?\Z"
NO_ACTUATOR = r"\A(\S+)\s+(\S+)\s+(\{.*\})(\s+.*)?\Z"
TARGET_ONLY = r"\A(\S+)\s+(\S+)\Z"


def main():
    """
    OpenC2 debug shell
    """
    endpoint = None
    if len(sys.argv) == 2:
        endpoint = sys.argv[1]
        if str.find(endpoint, "://") == -1:
            print("Warning: URI scheme not specified")

    print("OpenC2 debug shell (endpoint={})".format(endpoint))

    while True:
        try:
            cmd = parse(input("openc2> "))
            print(json.dumps(cmd, indent=4))
            
            if endpoint is not None:
                print("-->")
                print("<--")
                r = requests.post(endpoint, json=cmd, headers=HEADERS)
                print(json.dumps(r.json(), indent=4))

        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print("^C")
        except Exception as e:
            print("{}: {}".format(e.__class__.__name__, str(e)))

    return 0


def parse(cmd):
    """
    Debug OpenC2 CLI parser
    """
    actuator_match = re.match(ACTUATOR, cmd)
    non_actuator_match = re.match(NO_ACTUATOR, cmd)
    target_only_match = re.match(TARGET_ONLY, cmd)

    action = None
    target_type = None
    target = {}
    actuator_type = None
    actuator = {}
    modifier = {}

    if actuator_match:
        groups = actuator_match.groups("")

        action = str.lower(groups[0])
        target_type = groups[1]
        target = yaml.load(groups[2], Loader=yaml.FullLoader)

        actuator_type = groups[3]
        actuator = yaml.load(groups[4], Loader=yaml.FullLoader)
        
        modifier = yaml.load("{{{}}}".format(groups[5]), Loader=yaml.FullLoader)
    elif non_actuator_match:
        groups = non_actuator_match.groups("")

        action = str.lower(groups[0])
        target_type = groups[1]
        target = yaml.load(groups[2], Loader=yaml.FullLoader)

        modifier = yaml.load("{{{}}}".format(groups[3]), Loader=yaml.FullLoader)
    elif target_only_match:
        groups = target_only_match.groups("")

        action = str.lower(groups[0])
        target_type = groups[1]
    else:
        raise SyntaxError("Invalid OpenC2 command")


    target['type'] = target_type

    if actuator_match:
        actuator['type'] = actuator_type

    return {'action': action, 'target': target, 'actuator': actuator,
            'modifier': modifier}


if __name__ == "__main__":
    sys.exit(main())

