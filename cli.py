from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator, ValidationError
from typing import List

from file import File


class NumberValidator(Validator):
    def validate(self, document):
        if not document.text.isdigit():
            raise ValidationError(
                message="Please enter a number", cursor_position=len(document.text)
            )


def prompt_user_options(msg: str, options: List[str]) -> int:
    while True:  # Loop until valid input or exit
        try:
            print(f"{msg}")
            for i, option in enumerate(options):
                print(f"\t{i + 1}) {option}")

            user_input = int(prompt(">>> ", validator=NumberValidator()))
            if not (0 < user_input < len(options) + 1):
                raise ValueError(
                    f"Value {user_input} is out of range. Must be between 1 and {len(options)}"
                )
            return user_input
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
