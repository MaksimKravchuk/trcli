import enum
import trcli


class ProjectErrors(enum.IntEnum):
    multiple_project_same_name = -1
    not_existing_project = -2
    other_error = -3


FAULT_MAPPING = dict(
    missing_file="Please provide a valid path to your results file with the -f argument.",
    missing_host="Please provide a TestRail server address with the -h argument.",
    missing_project="Please specify the project name using the --project argument.",
    missing_title="Please give your Test Run a title using the --title argument.",
    missing_username="Please provide a valid TestRail username using the -u argument.",
    missing_password_and_key="Please provide either a password using the -p "
    "argument or an API key using the -k argument.",
    no_response_from_host="Your upload to TestRail did not receive a successful response from your TestRail Instance. "
    "Please check your settings and try again.",
    connection_error="Upload to TestRail failed due to a network error. Please make sure you have a "
    "valid network connection then try again.",
    host_issues="Please provide a valid TestRail server address.",
    yaml_file_parse_issue="Error occurred while parsing yaml file ({file_path}).\nMake sure that structure of a file is correct.",
    file_open_issue="Error occurred while opening the file ({file_path}).\nMake sure that the file exists or the path is correct.",
)

TOOL_VERSION_AND_USAGE = f"""TestRail Connect v{trcli.__version__}
Copyright 2021 Gurock Software GmbH - www.gurock.com
Supported and loaded modules:
    - junit: JUnit XML Files (& Similar)"""

MISSING_COMMAND_SLOGAN = """Usage: trcli [OPTIONS] COMMAND [ARGS]...\nTry 'trcli --help' for help.
\nError: Missing command."""
