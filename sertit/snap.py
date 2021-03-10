import logging
import os
import psutil
from sertit import strings, misc
from sertit.logs import SU_NAME

MAX_CORES = os.cpu_count() - 2
MAX_MEM = int(os.environ.get('JAVA_OPTS_XMX', 0.95 * psutil.virtual_memory().total))
TILE_SIZE = 2048
LOGGER = logging.getLogger(SU_NAME)

def bytes2snap(nof_bytes: int) -> str:
    """
    Convert nof bytes into snap-compatible Java options

    Args:
        nof_bytes (int): Byte nb

    Returns:
        str: Human-readable in bits

    """
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for idx, sym in enumerate(symbols):
        prefix[sym] = 1 << (idx + 1) * 10
    for sym in reversed(symbols):
        if nof_bytes >= prefix[sym]:
            value = int(float(nof_bytes) / prefix[sym])
            return '%s%s' % (value, sym)
    return "%sB" % nof_bytes


def get_gpt_cli(graph_path: str, other_args: list, display_snap_opt: bool = False) -> list:
    """
    Get GPT command line with system OK optimizations.
    To see options, type this command line with --diag (but it won't run the graph)

    Args:
        graph_path (str): Graph path
        other_args (list): Other args as a list such as `['-Pfile="in_file.zip", '-Pout="out_file.dim"']`
        display_snap_opt (bool): Display SNAP options via --diag

    Returns:
        list: GPT command line as a list
    """
    gpt_cli = ['gpt',
               strings.to_cmd_string(graph_path),
               '-q', MAX_CORES,  # Maximum parallelism
               f'-J-Xms2G -J-Xmx{bytes2snap(MAX_MEM)}',  # Initially/max allocated memory
               '-J-Dsnap.log.level=WARNING',
               f'-J-Dsnap.jai.defaultTileSize={TILE_SIZE}',
               f'-J-Dsnap.dataio.reader.tileWidth={TILE_SIZE}',
               f'-J-Dsnap.dataio.reader.tileHeigh={TILE_SIZE}',
               '-J-Dsnap.jai.prefetchTiles=true',
               f'-c {bytes2snap(int(0.5 * MAX_MEM))}',  # Tile cache set to 50% of max memory (up to 75%)
               # '-x',
               *other_args]  # Clears the internal tile cache after writing a complete row to the target file

    # LOGs
    LOGGER.debug(gpt_cli)
    if display_snap_opt:
        misc.run_cli(gpt_cli + ["--diag"])

    return gpt_cli
