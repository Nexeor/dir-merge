from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator, ValidationError
from typing import List
from pathlib import Path

import utils
from comparison_index import ComparisonIndex
from comparison_manager import ComparisonManager
from comparison import Comparison, CompType
from file import File


class UserOptionValidator(Validator):
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


def prompt_user_options(msg: str, options: List[str]) -> int:
    while True:  # Loop until valid input or exit
        try:
            # Print the message then the options
            print(f"{msg}")
            for i, option in enumerate(options):
                print(f"\t{i + 1}) {option}")

            # Gather user input and validate
            user_input = int(
                prompt(">>> ", validator=UserOptionValidator(num_options=len(options)))
            )
            return user_input
        except ValidationError as e:
            print(f"\nError: {e}")


def prompt_keep_options(file_list: List[File], link_paths=False):
    msg = "Choose how to resolve:"
    options = ["Keep one", "Keep all (system will auto-rename)", "Delete all"]
    user_choice = prompt_user_options(msg, options)
    match user_choice:
        case 1:
            msg = "Choose which file to keep"
            choices = [
                (utils.make_link(file.abs_path) if link_paths else file.abs_path)
                for file in file_list
            ]
            user_choice = prompt_user_options(msg, choices)
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


def prompt_build_diff(file_list: List[File]):
    comparing = True
    while comparing:
        user_choice = prompt_user_options(
            msg="Would you like to view a line-by-line comparison?",
            options=["Yes", "No"],
        )
        match user_choice:
            # Generate a line-by-line
            case 1:
                diff_log = _build_diff_helper(file_list)
                for line in diff_log:
                    print(line)
                if len(file_list) == 2:
                    comparing = False
            # Continue
            case 2:
                comparing = False


# Given a list of files, prompt the user to pick two to generate a diff from
def _build_diff_helper(file_list: List[File]):
    to_compare: List[File] = file_list

    # If file_list has 2 or more items, prompt user for which to choose
    if len(file_list) > 2:
        for i in range(2):
            diff_files = [
                diff_file
                for diff_file in file_list
                if diff_file.abs_path not in to_compare
            ]

            user_choice = prompt_user_options(
                msg=f"Choose {'first' if i == 0 else 'second'} file to compare",
                options=[diff_file.abs_path for diff_file in diff_files],
            )
            to_compare.append(diff_files[user_choice])
    return utils.make_file_diff(to_compare[0].abs_path, to_compare[1].abs_path)
