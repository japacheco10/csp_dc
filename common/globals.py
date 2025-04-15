class Globals:
    class Config():
        CONFIG_FOLDER = "_config"
        CONFIG_FILE_NAME = "config.cfg"

        class Sections():
            FILES = "files"

            class Files():
                HOLIDAYS = "holidays"
                PROJECTS = "projects"
                RESOURCES = "resources"