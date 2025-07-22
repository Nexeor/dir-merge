import questionary
from enum import EnumMeta


# Prompt to display to the user when they must make one choice from a list of options
class SelectSinglePrompt:
    def __init__(self, msg: str, options: EnumMeta | dict):
        if isinstance(options, EnumMeta):
            options = [questionary.Choice(title=opt.name, value=opt) for opt in options]
        else:
            options = [
                questionary.Choice(title=key, value=value)
                for key, value in options.items()
            ]
        self.question = questionary.select(message=msg, choices=options)

    def send_prompt(self):
        user_selection = self.question.ask()
        return user_selection


# Prompt to display to user when they must make one or more choices from a list of options
class SelectMultiPrompt:
    def __init__(
        self,
        msg: str,
        options: EnumMeta | dict,
        min_choices: int,
        max_choices: int,
    ):
        self.min_choices = min_choices
        self.max_choices = max_choices
        if isinstance(options, EnumMeta):
            options = [questionary.Choice(title=opt.name, value=opt) for opt in options]
        else:
            options = [
                questionary.Choice(title=key, value=value)
                for key, value in options.items()
            ]
        self.question = questionary.checkbox(message=msg, choices=options)

    def send_prompt(self):
        # Ask prompt until valid number of selections are chosen
        while True:
            user_selection = self.question.ask()

            if (
                self.min_choices == self.max_choices
                and len(user_selection) != self.min_choices
            ):
                print(f"Please select {self.min_choices} options")
                continue
            if len(user_selection) < self.min_choices:
                print(f"Please select at least {self.min_choices} option(s)")
                continue
            if len(user_selection) > self.max_choices:
                print(f"Please select at most {self.max_choices} option(s)")
                continue
            return user_selection
