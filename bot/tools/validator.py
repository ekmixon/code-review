# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import collections
import json
import logging
import os.path
import sys

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

Field = collections.namedtuple("Field", "name, validators, required")


def validate_path(value):
    assert isinstance(value, str), "Path should be a string"
    assert len(value) > 0, "Path should not be empty"
    assert not os.path.isabs(value), "Path should not be absolute"
    logger.debug(f"Path {value} is valid")


def validate_all_types(iterable, t):
    return all(map(lambda k: isinstance(k, t), iterable))


def validate_positive_int(value):
    if isinstance(value, int):
        assert value >= 0, "must be a positive integer (>= 0)"
    elif value is None:
        logger.debug("Found null value instead of positive integer")
    else:
        raise Exception("must be either a positive integer or null")


def validate_string(value):
    assert isinstance(value, str), "must be a string"
    assert len(value) > 0, "must be a non-empty string"


def validate_levels(value, levels=("warning", "error")):
    assert value in levels, f'must be in {", ".join(levels)}'


FIELDS = (
    # Required fields
    Field("path", [validate_path], True),
    Field("line", [validate_positive_int], True),
    Field("column", [validate_positive_int], True),
    Field("level", [validate_string, validate_levels], True),
    Field("message", [validate_string], True),
    # Optional fields
    Field("nb_lines", [validate_positive_int], False),
    Field("analyzer", [validate_string], False),
    Field("check", [validate_string], False),
)


def validate_issue(payload):
    """Validate an issue payload"""
    assert isinstance(payload, dict), "Issue must be a dict"

    # Check all required keys are here
    keys = set(payload.keys())
    required = {field.name for field in FIELDS if field.required is True}
    if diff := required.difference(keys):
        raise Exception(f'Missing required keys {", ".join(sorted(diff))}')

    if diff := keys.difference(field.name for field in FIELDS):
        logger.warning(f'Extra fields will not be used: {", ".join(sorted(diff))}')

    # Validate all fields one by one
    for field in FIELDS:
        if field.name in payload:
            logger.debug(f"Validating field {field.name}")
            for validator in field.validators:
                try:
                    validator(payload[field.name])
                except Exception as e:
                    raise Exception(f"{field.name} {e}")
        elif field.required is True:
            raise Exception(f"Missing required field {field.name}")
        else:
            logger.debug(f"Missing optional field {field.name}")

    return True


def validate(payload):
    """Validate an issues file payload"""

    # Top level must be a dict
    assert isinstance(payload, dict), "Top structure is not a dict"

    # All keys must be str
    assert validate_all_types(payload.keys(), str), "All top keys must be strings"

    # All values must be lists
    assert validate_all_types(payload.values(), list), "All top values must be lists"

    for path, issues in payload.items():
        logger.debug(f"Validating section {path}")
        validate_path(path)

        # All issues must be dicts
        assert validate_all_types(
            issues, dict
        ), f"All issues for {path} must be dicts"


        # Validate all issues
        for i, issue in enumerate(issues):
            logger.debug(f"Validating issue n°{i + 1} for {path}")
            try:
                validate_issue(issue)

                # Check the top path is the same in the issue
                assert (
                    path == issue["path"]
                ), f'Top path and issue path must be identical ({path} != {issue["path"]})'

            except Exception as e:
                raise Exception(f"Invalid issue n°{i + 1} for {path} : {e}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "issues_file",
        help="Local path to a JSON payload containing issues detected",
        type=open,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Display detailed log lines",
    )
    args = parser.parse_args()

    if args.verbose is True:
        logger.setLevel(logging.DEBUG)
        logger.debug("Enabled debug output")

    try:
        payload = json.load(args.issues_file)
        validate(payload)
    except json.decoder.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Invalid issues format: {e}")
        sys.exit(1)

    logger.info("Your file is valid !")
