from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator, ValidationError
from typing import List
from pathlib import Path

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
            user_input = prompt(">>> ", validator)
            if user_input in validator.keywords:  # Handle keywords
                match user_input:
                    case "done":
                        if not input_dirs:
                            print("At least one input directory must be given")
                        else:
                            return input_dirs
                    case "list":
                        msg = ["Added directories: "]
                        for i, dir in enumerate(input_dirs):
                            msg.append(f"\t{i}) {dir}")
                        print("\n".join(msg))
            else:  # Handle paths
                input_dirs.append(user_input)
        except ValidationError as e:
            print(f"\nError: {e}")


def display_files(msg, file_list: List[File]):
    msg = [msg]
    for i, file in enumerate(file_list, 1):
        msg.append(f"{i}) {str(file)}")
    print("\n".join(msg))


def run_prompt():
    # Prompt user for input dirs
    # Add files to dir_index
    # Find matches
    return True
