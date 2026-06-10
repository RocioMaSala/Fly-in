class UsageError(Exception):
    """
    Exception raised when the program is executed with invalid arguments.
    """

    def __init__(self, message: str = "Usage Error: python3 a_maze_ing.py "
                 "config.txt") -> None:
        """
        Initialize the exception with a custom error message.

        Args:
            message (str): Error message to display.

        Returns:
            None
        """
        super().__init__(message)


class ConfigSyntaxError(Exception):
    """
    Exception raised when the configuration file syntax is invalid.
    """

    def __init__(self, message: str = "Invalid config file syntax.") -> None:
        """
        Initialize the exception with a custom error message.

        Args:
            message (str): Error message to display.

        Returns:
            None
        """
        super().__init__(message)


class MissingConfigKeyError(Exception):
    """
    Exception raised when a required key
    is missing from the configuration file.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ConfigValueError(Exception):
    """
    Exception raised when a configuration key has an invalid value type.
    """

    def __init__(self, message: str) -> None:
        """Initialize the exception with a custom error message.

        Args:
            message (str): Error message to display.
        """
        super().__init__(message)


class MazeError(Exception):
    """
    Custom exception for invalid maze configurations.
    """

    def __init__(self, message: str = "Invalid maze configuration") -> None:
        """
        Initialize the exception with a custom error message.

        Args:
            message (str): Explanation of the error.
                Defaults to "Invalid maze configuration".

        Returns:
            None
        """
        super().__init__(message)


def parse_config_line(line: str) -> tuple[str, str]:
    """
    Parse a configuration line into a key-value pair.

    The expected format is:

        KEY=VALUE

    Args:
        line (str): Configuration line to parse.

    Returns:
        tuple[str, str]: Parsed key and value.

    Raises:
        ConfigSyntaxError: If the line format is invalid.
    """
    parts = line.split("=", 1)
    if len(parts) != 2:
        raise ConfigSyntaxError(f"Invalid config format: '{line.strip()}'. "
                                "Expected 'KEY=VALUE'")
    key, value = parts
    if not key.strip():
        raise ConfigSyntaxError(
            f"Missing key in config line: '{line.strip()}'")
    return key.strip(), value.strip()

    if int(config["WIDTH"]) <= 7 or int(config["HEIGHT"]) <= 5:
        print("To show the 42, the maze mmust be larger than 7x5")
    try:
        maze_gen = MazeGenerator(config)
    except Exception:
        raise MazeError
    

def main() -> None:
    try:
        if len(sys.argv) != 2:
            raise UsageError
        if sys.argv[1] != "config.txt":
            raise UsageError
        with open(sys.argv[1]) as file:
            config = {key.strip(): value.strip() for key, value in
                      (parse_config_line(line) for line in file if
                       line.strip() and not line.strip().startswith("#"))}
        REQUIRED_KEYS = {
            "WIDTH",
            "HEIGHT",
            "ENTRY",
            "EXIT",
            "OUTPUT_FILE",
            "PERFECT"
        }
        missing_keys = [
            req_key for req_key in REQUIRED_KEYS if req_key not in config
        ]
        if missing_keys:
            keys_str = ', '.join(missing_keys)
            msg = f"Config Error: Missing required keys:{keys_str}"
            raise MissingConfigKeyError(msg)

        if config["PERFECT"] not in ("True", "False"):
            raise ConfigValueError(
                f"Config Error: Invalid value for 'PERFECT'. "
                f"Expected 'True' or 'False', got '{config['PERFECT']}'."
            )
        generate = random_generator(config)
        menu(generate, config)
    except UsageError as e:
        print(e)
    except FileNotFoundError:
        print("config.txt file not present")
    except MissingConfigKeyError as e:
        print(e)
    except ConfigValueError as e:
        print(e)
    except ConfigSyntaxError as e:
        print(e)
    except ValueError:
        print(
            "ValueError: Entry and exit coordinates must only contain numbers"
        )
    except MazeError:
        return