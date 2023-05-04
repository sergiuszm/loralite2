from typing import Any
from re import split
from random import getrandbits
# import fasteners
# from loralite.simulator import _DATA
# from oslo_concurrency import lockutils
# # from oslo_config import cfg

# _prefix = 'energy'
# synchronized = lockutils.synchronized_with_prefix(_prefix)
# lock = lockutils.lock_with_prefix(_prefix)
# lock_cleanup = lockutils.remove_external_lock_file_with_prefix(_prefix)
# lockutils.set_defaults(f'{_DATA}')

# print(lockutils.get_lock_path(lockutils.CONF))

# default = cfg.CONF.import_group('oslo_concurrency', 'oslo_concurrency')

# lock = fasteners.InterProcessLock(f'{_DATA}/lock.file')

ROUND_N = 4


class bcolors:
    HEADER = "\033[95m"
    HEADER2 = "\033[96m"
    HEADER3 = "\033[32m"
    OKBLUE = "\033[94m"
    BBLUE = "\033[44m"
    BCYAN = "\033[46m"
    OKGREEN = "\033[92m"
    BGREEN = "\033[42m"
    MAGNETA = "\033[35m"
    BMAGNETA = "\033[45m"
    WHITE = "\033[37m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    BRED = "\033[41m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BYELLOW = '\033[43m'
    BRED = '\033[41m'
    BWHITEDARK = '\033[7m'
    BBLINKING = '\033[5m'
    LIGHT_GRAY = '\033[2m'
    YELLOW_MAGNETA = '\033[93m\033[45m'


def atof(text: Any) -> float:
    try:
        retval = float(text)
    except ValueError:
        retval = text
    return retval


def natural_keys(text: Any) -> list[Any]:
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    float regex comes from https://stackoverflow.com/a/12643073/190597
    """
    return [atof(c) for c in split(r"[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)", text)]


def format_ms(time_ms: int, second_in_unit: int) -> str:
    return f"{int((time_ms - time_ms % second_in_unit) / second_in_unit):,}.{time_ms % second_in_unit:03d}s"

def get_random_true_false() -> bool:
    return bool(getrandbits(1))

def round1(f_to_round: float) -> float:
    return int(f_to_round*(10**1)+0.5)/(10**1)

def round2(f_to_round: float) -> float:
    return int(f_to_round*(10**2)+0.5)/(10**2)

def round3(f_to_round: float) -> float:
    return int(f_to_round*(10**3)+0.5)/(10**3)

def round4(f_to_round: float) -> float:
    return int(f_to_round*(10**4)+0.5)/(10**4)

def bytes_from_bits_little_endian(s: str) -> bytes:
    return ''.join(chr(int(s[i:i+8][::-1], 2)) for i in range(0, len(s), 8)).encode('iso-8859-1')

def bits_little_endian_from_bytes(b: bytes) -> str:
    s = b.decode('iso-8859-1')
    return ''.join(bin(ord(x))[2:].rjust(8,'0')[::-1] for x in s)