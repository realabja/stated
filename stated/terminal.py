from stated.main import Agent


def entrypoint():
    from logging import basicConfig
    from logging import getLogger

    from rich.logging import RichHandler

    FORMAT = "%(message)s"
    basicConfig(level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])
    logger = getLogger(__name__)
    from time import sleep

    sleep(10)

    print("...")


if __name__ == "__main__":
    entrypoint()
