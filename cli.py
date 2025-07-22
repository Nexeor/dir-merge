import shutil
import subprocess
from typing import List
from enum import Enum

import utils
from file import File
from prompts import SelectSinglePrompt, SelectMultiPrompt


def make_file_options(file_list: List[File]) -> dict[str:File]:
    return {
        f"File {i + 1}: {file.rel_path} \n            {file.get_link()}": file
        for i, file in enumerate(file_list)
    }


def display_files(msg, file_list: List[File]):
    msg = [msg]
    for i, file in enumerate(file_list, 1):
        msg.append(f"{i}) {str(file)}")
    print("\n".join(msg))


# Prompt the user to choose which files to keep from a list of files
def prompt_keep_options(file_list: List[File]):
    view_prompt = SelectMultiPrompt(
        msg="Choose one or more files to keep",
        options=make_file_options(file_list),
        min_choices=0,
        max_choices=len(file_list),
    )
    return view_prompt.send_prompt()


class DiffViewOptions(Enum):
    DIFF_EDITOR = "Open in diff editor"
    DIFF_UNIFIED = "View unified diff"
    DIFF_SIDE_BY_SIDE = "View side-by-side diff"
    CONTINUE = "Skip viewing and continue"


def prompt_build_diff(file_list: List[File]):
    view_prompt = SelectSinglePrompt(
        msg="Choose how to view the files",
        options=DiffViewOptions,
    )
    while True:
        user_selection = view_prompt.send_prompt()

        if user_selection is DiffViewOptions.CONTINUE:
            break

        compare_prompt = SelectMultiPrompt(
            msg="Choose files to compare",
            options=make_file_options(file_list),
            min_choices=2,
            max_choices=2,
        )
        to_compare = compare_prompt.send_prompt()

        match user_selection:
            # TODO: Add alternative options for non-VSCode users
            case DiffViewOptions.DIFF_EDITOR:
                print("Opening diff editor...")
                if shutil.which("code") is None:
                    print("Need VSCode cmd-line 'code' to open diff editor")
                else:
                    subprocess.run(
                        'code --new-window --diff "{}" "{}"'.format(
                            to_compare[0].abs_path.resolve(),
                            to_compare[1].abs_path.resolve(),
                        ),
                        shell=True,
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
                        'diff --side-by-side "{}" "{}"'.format(
                            to_compare[0].abs_path.resolve(),
                            to_compare[1].abs_path.resolve(),
                        ),
                        shell=True,
                    )
                    print("\n")
