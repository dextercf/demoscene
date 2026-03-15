"""
socketio.py - Socket I/O layer for Mystic BBS door integration
Demoscene: The Exploration of Art
A Cellfish Production

When the game runs as a BBS door, all output goes through a TCP socket
connected to the player's terminal. This module wraps that socket and
provides read/write methods used by ansi.py.

In debug mode (no socket handle) it falls back to plain stdout/stdin.
"""

import sys
import os
import socket as _socket
from socket import timeout as _socket_timeout

# ---------------------------------------------------------------------------
# Global I/O instance — set once at startup by game.py
# ---------------------------------------------------------------------------
_io = None

def get_io():
    return _io


def set_io(io_instance):
    global _io
    _io = io_instance


# ---------------------------------------------------------------------------
# Socket I/O class — used when running as a BBS door
# ---------------------------------------------------------------------------

class SocketIO:
    """Wraps a TCP socket for BBS door I/O."""

    def __init__(self, sock):
        self.sock    = sock
        self._buf    = b""
        self.is_socket = True

    def write(self, data):
        if isinstance(data, str):
            data = data.encode("cp437", errors="replace")
        try:
            self.sock.sendall(data)
        except Exception:
            pass

    def flush(self):
        pass  # socket sends immediately

    def read_byte(self):
        """Read exactly one byte, handling telnet IAC sequences."""
        while True:
            # If buffer has data use it first
            while len(self._buf) < 1:
                try:
                    self.sock.settimeout(120)  # 2 minute timeout
                    chunk = self.sock.recv(256)
                    if not chunk:
                        # Connection closed by remote end
                        return b""
                    self._buf += chunk
                except _socket_timeout:
                    # Send a telnet NOP to keep connection alive
                    try:
                        self.sock.sendall(b"\xff\xf1")  # IAC NOP
                    except Exception:
                        return b""
                    continue
                except Exception:
                    return b""

            byte = self._buf[:1]
            self._buf = self._buf[1:]

            # Handle telnet IAC (0xFF) sequences — skip them
            if byte == b"\xff":
                # Read 2 more bytes (command + option) and discard
                for _ in range(2):
                    while len(self._buf) < 1:
                        try:
                            chunk = self.sock.recv(256)
                            if chunk:
                                self._buf += chunk
                        except Exception:
                            break
                    if self._buf:
                        self._buf = self._buf[1:]
                continue  # skip and read next real byte

            return byte

    def getkey(self, valid_keys=None):
        """
        Read a single keypress from the player.
        Returns uppercase character string.
        valid_keys — if set, only return keys in this list.
        """
        while True:
            byte = self.read_byte()
            if not byte:
                return "Q"  # disconnect safety
            try:
                ch  = byte.decode("cp437", errors="replace")
                key = ch.upper()
                if valid_keys is None or key in [k.upper() for k in valid_keys]:
                    return key
            except Exception:
                continue

    def getline(self, max_len=30):
        """
        Read a line of text input, echoing characters back.
        Returns stripped string.
        """
        result = []
        while True:
            byte = self.read_byte()
            if not byte:
                break
            ch = byte.decode("cp437", errors="replace")
            if ch in ("\r", "\n"):
                self.write(b"\r\n")
                break
            elif ch in ("\x08", "\x7f"):  # backspace
                if result:
                    result.pop()
                    self.write(b"\x08 \x08")
            elif len(result) < max_len and ch.isprintable():
                result.append(ch)
                self.write(byte)  # echo
        return "".join(result).strip()

    def close(self):
        """
        Detach the socket file descriptor so Python doesn't close
        the underlying OS socket when we exit. Mystic keeps the
        socket alive and redraws its menu after our process ends.
        """
        try:
            self.sock.detach()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Debug I/O class — used when running locally without a BBS
# ---------------------------------------------------------------------------

class DebugIO:
    """Falls back to stdout/stdin for local testing."""

    def __init__(self):
        self.is_socket = False
        # Enable ANSI on Windows terminal
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.kernel32.SetConsoleMode(
                    ctypes.windll.kernel32.GetStdHandle(-11), 7
                )
            except Exception:
                pass

    def write(self, data):
        if isinstance(data, bytes):
            sys.stdout.buffer.write(data)
        else:
            sys.stdout.buffer.write(
                data.encode("cp437", errors="replace")
            )
        sys.stdout.buffer.flush()

    def flush(self):
        sys.stdout.buffer.flush()

    def getkey(self, valid_keys=None):
        try:
            import msvcrt
            while True:
                ch = msvcrt.getwch()
                if ch in ("\x00", "\xe0"):
                    msvcrt.getwch()
                    continue
                key = ch.upper()
                if valid_keys is None or key in [k.upper() for k in valid_keys]:
                    return key
        except ImportError:
            import tty, termios
            fd  = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    ch  = sys.stdin.read(1)
                    key = ch.upper()
                    if valid_keys is None or key in [k.upper() for k in valid_keys]:
                        return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def getline(self, max_len=30):
        try:
            result = input()
            return result.strip()[:max_len]
        except (EOFError, KeyboardInterrupt):
            return ""

    def clear_screen(self):
        if sys.platform == "win32":
            os.system("cls")

    def close(self):
        pass


# ---------------------------------------------------------------------------
# Factory — called once at startup
# ---------------------------------------------------------------------------

def init(socket_handle=None):
    """
    Initialise the I/O layer.
    socket_handle — integer socket handle from Mystic %H, or None for debug.
    Returns the I/O instance and sets the global.
    """
    if socket_handle is not None:
        try:
            sock = _socket.fromfd(
                socket_handle,
                _socket.AF_INET,
                _socket.SOCK_STREAM
            )
            io = SocketIO(sock)
            set_io(io)
            return io
        except Exception as e:
            # Fall through to debug mode
            pass

    io = DebugIO()
    set_io(io)
    return io


# ---------------------------------------------------------------------------
# Helper — parse socket handle from Mystic command line args
# Mystic passes: script.py NODE_NUM SOCKET_HANDLE
# ---------------------------------------------------------------------------

def parse_socket_handle(argv=None):
    """
    Extract the socket handle from command line arguments.
    Returns integer handle or None.
    """
    if argv is None:
        argv = sys.argv[1:]

    node   = None
    handle = None

    for arg in argv:
        try:
            val = int(arg)
            if node is None:
                node = val      # first int = node number
            else:
                handle = val    # second int = socket handle
                break
        except ValueError:
            pass

    return handle