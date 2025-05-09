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
        if not (0 < user_input < len(self.num_options) + 1):
            raise ValidationError(
                f"Value {user_input} is out of range. Must be between 1 and {len(self.num_options)}"
            )

class DirValidator(Validator):
    def validate(self, document):
        path = Path(document.text)
        if not path.exists():
            raise ValidationError(
                message="Path does not exist. Please provide a valid path",  cursor_position=len(document.text)
            )
        elif not path.is_dir():
            raise ValidationError(
                message="Path is not a directory. Please provide a path to a directory",  cursor_position=len(document.text)
            )


def prompt_user_options(msg: str, options: List[str]) -> int:
    while True:  # Loop until valid input or exit
        try:
            # Print the message then the options
            print(f"{msg}")
            for i, option in enumerate(options):
                print(f"\t{i + 1}) {option}")

            # Gather user input and validate
            user_input = int(prompt(">>> ", validator=UserOptionValidator(num_options=len(options))))

            return user_input - 1  # Adjust to 0-based indexing
        except (ValueError, ValidationError) as e:
            print(f"\nError: {e}")
        except EOFError:
            print("\nEOF recieved. Exiting")
            exit(0)

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
