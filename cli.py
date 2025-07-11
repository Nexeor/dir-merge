import shutil
import subprocess
from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator, ValidationError
from typing import List
from pathlib import Path
from enum import Enum

import utils
from comparison_index import ComparisonIndex
from comparison_manager import ComparisonManager
from comparison import Comparison, CompType
from file import File


# Validate when user has single choice from many options
class SingleChoiceValidator(Validator):
    def __init__(self, num_options: int):
        self.num_options = num_options

    def validate(self, document):
        # Check that input is an int
        user_input = document.text
        if not user_input.isdigit():
            raise ValidationError(
                message="Please enter a number", cursor_position=len(document.text)
            )
        # Check that input is valid range
        user_input = int(user_input)
        if not (0 < user_input < self.num_options + 1):
            raise ValidationError(
                message=f"Value {user_input} is out of range. Must be between 1 and {self.num_options}",
                cursor_position=len(document.text),
            )


# Validate when user has multiple choices from many options
class MultiChoiceValidator(Validator):
    def __init__(self, num_options: int):
        self.num_options = num_options
        self.previous_inputs = set()

    def validate(self, document):
        # Check that input is an int
        user_input = document.text
        if not user_input.isdigit():
            raise ValidationError(
                message="Please enter a number", cursor_position=len(document.text)
            )
        # Check that input is valid range
        user_input = int(user_input)
        if not (0 < user_input < self.num_options + 1):
            raise ValidationError(
                message=f"Value {user_input} is out of range. Must be between 1 and {self.num_options}",
                cursor_position=len(document.text),
            )
        # Check that input has not been selected already
        if user_input in self.previous_inputs:
            raise ValidationError(
                message=f"Value {user_input} has been selected already"
            )
        else:
            self.previous_inputs.add(user_input)


# Validate that the input is a valid path that exists in the file system
class InputDirValidator(Validator):
    def __init__(self):
        self.keywords = ["done", "list"]

    def validate(self, document):
        user_input = document.text
        # Return early if keyword
        if user_input in self.keywords:
            return
        # Check if path leads to valid dir
        path = Path(user_input)
        if not path.exists():
            raise ValidationError(
                message="Path does not exist. Please provide a valid path",
                cursor_position=len(document.text),
            )
        elif not path.is_dir():
            raise ValidationError(
                message="Path is not a directory. Please provide a path to a directory",
                cursor_position=len(document.text),
            )


# Prompt the user to make a single chouce from a list of options
def prompt_single_choice(msg: str, options: List[str]) -> str:
    while True:  # Loop until valid input or exit
        try:
            # Print the message then the options
            print(f"{msg}")
            for i, option in enumerate(options):
                print(f"\t{i + 1}) {option}")

            # Gather user input and validate
            user_input = int(
                prompt(
                    ">>> ", validator=SingleChoiceValidator(num_options=len(options))
                )
            )
            # Return the selected option
            return options[user_input - 1]
        except ValidationError as e:
            print(f"\nError: {e}")


# Prompt the user to make multiple choices from a list of options
def prompt_multi_choice(msg: str, options: List[object], num_choices: int) -> List[str]:
    selected = []
    local_validator = MultiChoiceValidator(num_options=len(options))
    print(f"{msg}")
    while len(selected) < num_choices:
        print(f"Choice {len(selected) + 1}")
        try:
            for i, option in enumerate(options):
                print(f"\t{i + 1}) {option}")

            user_input = int(prompt(">>> ", validator=local_validator))
            selected.append(options[user_input - 1])
        except ValidationError as e:
            print(f"\nError: {e}")

    return selected


def prompt_keep_options(file_list: List[File], link_paths=False):
    msg = "Choose how to resolve:"
    options = ["Keep one", "Keep all (system will auto-rename)", "Delete all"]
    user_choice = prompt_single_choice(msg, options)
    match user_choice:
        case 1:
            msg = "Choose which file to keep"
            choices = [
                (utils.make_link(file.abs_path) if link_paths else file.abs_path)
                for file in file_list
            ]
            user_choice = prompt_single_choice(msg, choices)
            return file_list[user_choice - 1]
        case 2:
            for i, file in enumerate(file_list):
                file.name = f"{file.name}_v{i}"
            return file_list
        case 3:
            return []


def prompt_input_dirs() -> List[Path]:
    """Prompt the user for any number of input dirs to add to the index"""
    input_dirs = []
    validator = InputDirValidator()

    # Loop until user enters 'done'
    while True:
        print(
            "Enter the path to the input directory (e.g., /home/user/documents/project):\n",
            "Type 'done' when finished or 'list' to view all added directories\n",
        )
        try:
            user_input = prompt(">>> ", validator=validator)
            if user_input in validator.keywords:  # Handle keywords
                match user_input:
                    case "done":
                        if not input_dirs:
                            print("At least one input directory must be given")
                        else:
                            return input_dirs
                    case "list":
                        msg = ["Added directories: "]
                        for i, dir in enumerate(input_dirs, 1):
                            msg.append(f"\t{i}) {dir}")
                        print("\n".join(msg))
            else:  # Handle paths
                input_dirs.append(Path(user_input))
        except ValidationError as e:
            print(f"\nError: {e}")


def display_files(msg, file_list: List[File]):
    msg = [msg]
    for i, file in enumerate(file_list, 1):
        msg.append(f"{i}) {str(file)}")
    print("\n".join(msg))


def prompt_path_name_dup(manager: ComparisonManager):
    path_name_index: ComparisonIndex = manager.comparisons[CompType.PATH_NAME_DUP]
    for key, dup_list in path_name_index.index.items():
        display_files(
            "PATH-NAME DUP: Files have the same name and path but have different content",
            dup_list,
        )

        prompt_build_diff(dup_list)
        prompt_keep_options(dup_list, link_paths=True)


class DiffViewOptions(Enum):
    DIFF_EDITOR = "Open in diff editor"
    DIFF_UNIFIED = "View unified diff"
    DIFF_SIDE_BY_SIDE = "View side-by-side diff"
    CONTINUE = "Skip viewing and continue"


def prompt_build_diff(file_list: List[File]):
    if shutil.which("code") is None:
        print("Need VSCode command-line tool 'code' to view ")
    comparing = True
    while comparing:
        user_choice = prompt_single_choice(
            msg="Would you like to view the files?",
            options=[option.value for option in DiffViewOptions],
        )
        match user_choice:
            case DiffViewOptions.DIFF_EDITOR:
                diff_files = prompt_pick_files(
                    msg="Choose files to open in diff editor",
                    file_list=file_list,
                    num_files=2,
                )
                if shutil.which("code") is None:
                    print("Need VSCode cmd-line 'code' to open diff editor")
                else:
                    subprocess.run(
                        [
                            "code",
                            "--new-window",
                            "-diff",
                            diff_files[0].abs_path,
                            diff_files[1].abs_path,
                        ]
                    )
            case DiffViewOptions.DIFF_UNIFIED:
                diff_files = prompt_pick_files(
                    msg="Choose files to open in diff editor",
                    file_list=file_list,
                    num_files=2,
                )
                # TODO: Generate unified diff and print it here

            case DiffViewOptions.DIFF_SIDE_BY_SIDE:
                diff_files = prompt_pick_files(
                    msg="Choose files to open in diff editor",
                    file_list=file_list,
                    num_files=2,
                )
                # TODO: Generate side by side diff and print it here

            case DiffViewOptions.CONTINUE:
                comparing = False


# Given a list of files, prompt the user to pick a certain number
def prompt_pick_files(msg: str, file_list: List[File], num_files: int):
    to_compare: List[File] = file_list

    if len(file_list) == num_files:
        return file_list

    selected_files = prompt_multi_choice(
        msg=msg, options=file_list, num_choices=num_files
    )

    return selected_files
