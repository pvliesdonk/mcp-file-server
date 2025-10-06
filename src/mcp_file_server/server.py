import json
import pathlib
from typing import Annotated, Any, Optional

import click
from click_params import IP_ADDRESS
from fastmcp import Context, FastMCP
from fastmcp.utilities.logging import configure_logging, get_logger
from pydantic import Field

# configure logging
logger = get_logger(__name__)

BASE_PATH: pathlib.Path = pathlib.Path("/data")


def get_full_path(relative_path: pathlib.Path) -> pathlib.Path:
    """Get the full path for a given relative path."""
    if relative_path.is_absolute(): 	   
        return BASE_PATH.joinpath(relative_path.relative_to("/"))
    else:
        return BASE_PATH.joinpath(relative_path)


def get_relative_path(full_path: pathlib.Path) -> pathlib.Path:
    """Get the relative path from the base path."""
    return pathlib.Path("/").joinpath(full_path.relative_to(BASE_PATH))


mcp = FastMCP("mcp-file-server")


@mcp.tool
async def list_files(
    path: Annotated[pathlib.Path, Field(description="The directory path to list files from.")],
) -> dict | list[dict]:
    """List all files in the specified directory"""

    full_path = get_full_path(path)

    if not full_path.exists() or not full_path.is_dir():
        return {"error": f"Directory {path} does not exist or is not a directory."}

    file_info = []
    for f in full_path.iterdir():
        file_info.append(
            {
                "name": f.name,
                "full path": get_relative_path(f).as_posix(),
                "type": "Directory" if f.is_dir() else "File",
                "size": f.stat().st_size if f.is_file() else "-",
            }
        )

    if len(file_info) == 0:
        return {"message": f"No files found in directory {path}."}

    return file_info


@mcp.tool
async def read_file(file_path: Annotated[pathlib.Path, Field(description="The file path to read from.")]) -> dict | str:
    """Read the contents of a specified file"""
    full_path = get_full_path(file_path)

    if not full_path.exists() or not full_path.is_file():
        return {"error": f"File {file_path} does not exist or is not a file."}

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
            logger.debug(f"Read content from {full_path}: {content[:100]}...")  # Log first 100 chars
            return content
    except Exception as e:
        logger.error(f"Error reading file {full_path}: {e}")
        return {"error": f"Error reading file {file_path}: {e}"}


@mcp.tool
async def create_file(
    file_path: Annotated[pathlib.Path, Field(description="The file path to create.")], content: str
) -> dict:
    """Create a new file with the specified content"""
    full_path = get_full_path(file_path)

    if full_path.exists():
        if full_path.is_dir():
            return {"error": f"File {file_path} is an existing directory."}
        return {"error": f"File {file_path} already exists."}

    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
            logger.info(f"Successfully created file {full_path}")
            return {"message": f"File {file_path} created successfully."}
    except Exception as e:
        logger.error(f"Error creating file {full_path}: {e}")
        return {"error": f"Error creating file {file_path}: {e}"}


@mcp.tool
async def delete_file(file_path: Annotated[pathlib.Path, Field(description="The file path to delete.")]) -> dict:
    """Delete a specified file"""
    full_path = get_full_path(file_path)

    if not full_path.exists() or not full_path.is_file():
        return {"error": f"File {file_path} does not exist or is not a file."}

    try:
        full_path.unlink()
        logger.info(f"Successfully deleted file {full_path}")
        return {"message": f"File {file_path} deleted successfully."}
    except Exception as e:
        logger.error(f"Error deleting file {full_path}: {e}")
        return {"error": f"Error deleting file {file_path}: {e}"}


@mcp.tool
async def create_directory(
    dir_path: Annotated[pathlib.Path, Field(description="The directory path to create.")],
) -> dict:
    """Create a new directory"""
    full_path = get_full_path(dir_path)

    if full_path.exists():
        if full_path.is_file():
            return {"error": f"File {dir_path} is an existing file."}
        return {"error": f"Directory {dir_path} already exists."}

    try:
        full_path.mkdir(parents=True, exist_ok=False)
        logger.info(f"Successfully created directory {full_path}")
        return {"message": f"Directory {dir_path} created successfully."}
    except Exception as e:
        logger.error(f"Error creating directory {full_path}: {e}")
        return {"error": f"Error creating directory {dir_path}: {e}"}


@mcp.tool
async def delete_directory(
    dir_path: Annotated[pathlib.Path, Field(description="The directory path to delete.")],
) -> dict:
    """Delete a specified directory"""
    full_path = get_full_path(dir_path)

    if not full_path.exists() or not full_path.is_dir():
        return {"error": f"Directory {dir_path} does not exist or is not a directory."}

    try:
        full_path.rmdir()
        logger.info(f"Successfully deleted directory {full_path}")
        return {"message": f"Directory {dir_path} deleted successfully."}
    except Exception as e:
        logger.error(f"Error deleting directory {full_path}: {e}")
        return {"error": f"Error deleting directory {dir_path}: {e}"}


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["streamable-http", "stdio"]),
    default="streamable-http",
    envvar=["TRANSPORT"],
    help="Transport protocol to use",
)
@click.option("--port", type=click.INT, default=3000, envvar=["PORT"], help="Port to listen on for HTTP")
@click.option("--host", type=IP_ADDRESS, default="127.0.0.1", envvar=["HOST"], help="Host to listen on for HTTP")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    envvar="LOG_LEVEL",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default="/data",
    help="Base path for the file server",
)
def main(transport: str, port: int, host: str, log_level: str, path: pathlib.Path) -> None:
    # Configure logging
    configure_logging(log_level)  # type: ignore

    global BASE_PATH
    BASE_PATH = pathlib.Path(path).resolve()
    if not BASE_PATH.exists():
        logger.error(f"Base path {BASE_PATH} does not exist.")
        return

    logger.info(f"Using base path: {BASE_PATH}")

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host=str(host), port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
