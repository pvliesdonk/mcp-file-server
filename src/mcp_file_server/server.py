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

mcp = FastMCP("mcp-file-server")


@mcp.tool
async def list_files(
    path: Annotated[pathlib.Path, Field(description="The directory path to list files from.")],
) -> dict | str:
    """List all files in the specified directory"""

    global BASE_PATH

    logger.info(f"Received request to list files in directory: {path}")
    full_path = BASE_PATH.joinpath(path)
    logger.info(f"Adding this to {BASE_PATH} results in {full_path}")
    logger.info(f"Listing files in directory: {full_path}")

    if not full_path.exists() or not full_path.is_dir():
        return f"Directory {path} does not exist or is not a directory."

    file_info = []
    for f in full_path.iterdir():
        file_info.append({"name": f.name, "type": "Directory", "size": f.stat().st_size if f.is_dir() else "-"})

    out = json.dumps(file_info, indent=2)
    logger.debug(f"File listing output: {out}")
    return out


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
