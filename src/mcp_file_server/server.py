import logging
from typing import Any, Optional

import click
from click_params import IP_ADDRESS
from fastmcp import Context, FastMCP

# configure logging
logger = logging.getLogger(__name__)


mcp = FastMCP("mcp-file-server")


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
def main(transport: str, port: int, host: str, log_level: str) -> None:
    # Configure logging
    logging.basicConfig(level=getattr(logging, log_level.upper()))

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host=str(host), port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
