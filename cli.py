import shutil
import subprocess
from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator, ValidationError
from typing import List, Optional
from pathlib import Path
from enum import Enum

import utils
from comparison_index import ComparisonIndex
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

    # Call this method to record the input so it can be checked against future inputs
    def record_input(self, input):
        self.previous_inputs.add(input)


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


class UserPrompt:
    def __init__(
        self,
        msg: str,
        options: List[str],
        option_msgs: List[str],
        num_choices: int,
        min_choices: Optional[int] = None,
    ):
        self.msg = msg  # Send this message when displaying the prompt
        self.options = options  # Enum containing options and corresponding messages
        self.option_msgs = option_msgs  # Messages to display for each option
        self.num_choices = num_choices  # Number of total choices the user can make
        self.min_choices = (
            num_choices if not min_choices else min_choices
        )  # Number of choices the user must make

    @classmethod
    def from_enum(
        cls,
        msg: str,
        options: Enum,
        num_choices: int,
        min_choices: Optional[int] = None,
    ):
        option_msgs = [option.name for option in options]
        options = [option.value for option in options]
        return cls(msg, options, option_msgs, num_choices, min_choices)

    @classmethod
    def from_list(
        cls,
        msg: str,
        options: List[str],
        option_msgs: List[str],
        num_choices: int,
        min_choices: Optional[int] = None,
    ):
        return cls(msg, options, option_msgs, num_choices, min_choices)

    def send_prompt(self):
        # Print message and options
        print(self.msg)
        for i, option in enumerate(self.options):
            print(f"\t{i + 1}) {option}")

        # Prompt user for input based on number of choices
        if self.num_choices == 1:
            return self.prompt_single_choice()
        else:
            return self.prompt_multi_choice()

    def prompt_single_choice(self) -> object:
        """
        Prompt the user to make a single choice from a list of options.
        Returns the selected option.
        """
        while True:  # Loop until valid input or exit
            try:
                # Calidate user input and return the selected option
                user_input = int(
                    prompt(
                        ">>> ",
                        validator=SingleChoiceValidator(num_options=len(self.options)),
                    )
                )
                print(list(self.options)[user_input - 1])
                return list(self.options)[user_input - 1]
            except ValidationError as e:
                print(f"\nError: {e}")

    # Prompt the user to make multiple choices from a list of options
    def prompt_multi_choice(self) -> List[object]:
        if (
            self.num_choices <= len(self.options)
            and self.min_choices == self.num_choices
        ):
            print("Only one choice can be made, using single choice prompt")
            return self.options

        selected = []
        local_validator = MultiChoiceValidator(num_options=len(self.options))
        while len(selected) < self.num_choices and len(selected) < self.min_choices:
            print(f"Choice {len(selected) + 1}")
            try:
                for i, option in enumerate(self.options):
                    if option not in selected:
                        print(f"\t{i + 1}) {option}")
                    else:
                        print(f"\t{i + 1}) (selected) {option} ")
                # If the user has selected enough options, give them "done" option
                if len(selected) > self.min_choices:
                    # TODO: Done option non-functional
                    print(f"\t{i + 1}) Done")
                # Otherwise, prompt them to select more options
                else:
                    print(
                        f"Choose at least {self.min_choices - len(selected)} more options"
                    )
                user_input = int(prompt(">>> ", validator=local_validator))
                selected.append(self.options[user_input - 1])
                local_validator.record_input(user_input)
            except ValidationError as e:
                print(f"\nError: {e}")

        return selected


# Prompt the user to input directories for directory indexing
def prompt_input_dirs() -> List[Path]:
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


class KeepOptions(Enum):
    KEEP_ONE = "Keep one"
    KEEP_SOME = "Choose files to keep"
    KEEP_ALL = "Keep all (system will auto-rename)"
    DELETE_ALL = "Delete all"


# Prompt the user to choose which files to keep from a list of files
def prompt_keep_options(file_list: List[File]):
    view_prompt = UserPrompt(
        msg="Choose which file(s) to keep",
        options=KeepOptions,
        num_choices=1,
    )
    user_choice = view_prompt.send_prompt()
    match user_choice:
        case KeepOptions.KEEP_ONE:
            keep_prompt = UserPrompt(
                msg="Choose which file to keep",
                option_msg=[utils.make_link(file.abs_path) for file in file_list],
                options=file_list,
                num_choices=1,
            )
            return keep_prompt.send_prompt()
        case KeepOptions.KEEP_SOME:
            keep_prompt = UserPrompt(
                msg="Choose which files to keep",
                option_msg=[utils.make_link(file.abs_path) for file in file_list],
                options=file_list,
                num_choices=len(file_list),
                min_choices=1,  # User may choose one or more files
            )
            return keep_prompt.send_prompt()
        case KeepOptions.KEEP_ALL:
            # Automatically rename files to avoid duplicates
            for i, file in enumerate(file_list):
                file.name = f"{file.name}_v{i}"
            return file_list
        case KeepOptions.DELETE_ALL:
            return []


def display_files(msg, file_list: List[File]):
    msg = [msg]
    for i, file in enumerate(file_list, 1):
        msg.append(f"{i}) {str(file)}")
    print("\n".join(msg))


class DiffViewOptions(Enum):
    DIFF_EDITOR = "Open in diff editor"
    DIFF_UNIFIED = "View unified diff"
    DIFF_SIDE_BY_SIDE = "View side-by-side diff"
    CONTINUE = "Skip viewing and continue"


# Prompt the user to view different diff options for the selected files
def prompt_build_diff(file_list: List[File]):
    view_prompt = UserPrompt.from_enum(
        msg="Choose how to view the files",
        options=DiffViewOptions,
        num_choices=1,
    )
    comparing = True
    while comparing:
        user_input = view_prompt.send_prompt()
        print(f"You chose: {user_input}")

        if user_input is not DiffViewOptions.CONTINUE:
            compare_prompt = UserPrompt.from_list(
                msg="Choose files to compare",
                option_msgs=[str(file) for file in file_list],
                options=file_list,
                num_choices=2,
            )
            to_compare: List[File] = compare_prompt.send_prompt()

        match user_input:
            # TODO: Add alternative options for non-VSCode users
            case DiffViewOptions.DIFF_EDITOR:
                if shutil.which("code") is None:
                    print("Need VSCode cmd-line 'code' to open diff editor")
                else:
                    print("Opening diff editor...")
                    subprocess.run(
                        [
                            "code",
                            "--new-window",
                            "-diff",
                            to_compare[0].abs_path,
                            to_compare[1].abs_path,
                        ]
                    )
            case DiffViewOptions.DIFF_UNIFIED:
                diff_log = utils.make_unified_diff(
                    to_compare[0].abs_path, to_compare[1].abs_path
                )
                for line in diff_log:
                    print(line)
            case DiffViewOptions.DIFF_SIDE_BY_SIDE:
                if shutil.which("code") is None:
                    print("Need VSCode cmd-line 'code' to view unified diff")
                else:
                    subprocess.run(
                        [
                            "diff",
                            "--new-window",
                            "--side-by-side",
                            to_compare[0].abs_path,
                            to_compare[1].abs_path,
                        ]
                    )
            case DiffViewOptions.CONTINUE:
                comparing = False
