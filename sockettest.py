"""
sockettest.py - Test socket I/O redirection for Mystic BBS
Run this as a door first to verify the approach works
before wiring it into the full game.

Mystic door command (DD):
  c:\\games\\demoscene\\sockettest.bat %N %H

Where %H is the socket handle Mystic passes to external programs.
"""

import sys
import os
import socket
import msvcrt

def get_socket_from_handle(handle_int):
    """
    Convert a Windows socket handle (passed by Mystic as %H)
    into a Python socket object.
    """
    try:
        sock = socket.fromfd(handle_int, socket.AF_INET, socket.SOCK_STREAM)
        return sock
    except Exception as e:
        return None


def redirect_io_to_socket(sock):
    """
    Redirect stdin/stdout to the socket so all game I/O
    goes to the connected telnet user.
    """
    # Duplicate the socket for reading and writing
    sock_fd = sock.fileno()

    # Reopen stdout to write to the socket
    sys.stdout = os.fdopen(os.dup(sock_fd), 'wb', buffering=0)
    sys.stdin  = os.fdopen(os.dup(sock_fd), 'rb', buffering=0)


class SocketIO:
    """
    A cleaner approach — wrap the socket directly for I/O
    without replacing sys.stdout/stdin.
    """
    def __init__(self, sock):
        self.sock = sock
        self.buf  = b""

    def write(self, data):
        if isinstance(data, str):
            data = data.encode("cp437", errors="replace")
        try:
            self.sock.sendall(data)
        except Exception:
            pass

    def read(self, n=1):
        while len(self.buf) < n:
            try:
                chunk = self.sock.recv(1024)
                if not chunk:
                    return b""
                self.buf += chunk
            except Exception:
                return b""
        result = self.buf[:n]
        self.buf = self.buf[n:]
        return result

    def getkey(self):
        """Read a single keypress, return as uppercase string."""
        ch = self.read(1)
        if not ch:
            return "Q"
        # Handle telnet IAC sequences
        if ch == b"\xff":
            self.read(2)  # skip IAC + command
            return self.getkey()
        return ch.decode("cp437", errors="replace").upper()

    def flush(self):
        pass


def run_test(io):
    """Simple test — draw a screen and wait for a keypress."""
    ESC = b"\x1b"

    def out(text, colour=b""):
        if isinstance(text, str):
            text = text.encode("cp437", errors="replace")
        io.write(colour + text + ESC + b"[0m")

    def outln(text="", colour=b""):
        out(text, colour)
        io.write(b"\r\n")

    CYAN  = ESC + b"[36m"
    WHITE = ESC + b"[97m"
    GRAY  = ESC + b"[90m"
    YELLOW= ESC + b"[33m"

    # Clear screen
    io.write(ESC + b"[2J" + ESC + b"[H")

    outln()
    outln("  ============================================", CYAN)
    outln("  DEMOSCENE: THE EXPLORATION OF ART", WHITE)
    outln("  Socket I/O Test", GRAY)
    outln("  ============================================", CYAN)
    outln()
    outln("  If you can read this in SyncTerm then", WHITE)
    outln("  the socket approach is working!", YELLOW)
    outln()
    outln("  Press any key to continue...", GRAY)
    outln()

    key = io.getkey()

    io.write(ESC + b"[2J" + ESC + b"[H")
    outln()
    outln(f"  You pressed: {key}", YELLOW)
    outln()
    outln("  Socket I/O is confirmed working!", WHITE)
    outln("  Returning to BBS...", GRAY)
    outln()

    import time
    time.sleep(2)


def main():
    # Write startup info to a log so we can debug
    log_path = os.path.join(os.environ.get("TEMP", "C:\\mystic\\temp1"), "sockettest.log")

    with open(log_path, "w") as log:
        log.write(f"Args: {sys.argv}\n")
        log.write(f"Env SOCKET_HANDLE: {os.environ.get('SOCKET_HANDLE','not set')}\n")

    # Mystic passes socket handle as command line argument
    # Door command should be: sockettest.bat %N %H
    # %H = socket handle integer

    sock_handle = None

    # Try to get socket handle from argv
    # Mystic typically passes: script.bat NODE_NUM SOCKET_HANDLE
    for arg in sys.argv[1:]:
        try:
            val = int(arg)
            if val > 3:  # skip node numbers (usually 1-9)
                sock_handle = val
                break
        except ValueError:
            pass

    # Also check environment variable
    if sock_handle is None:
        env_handle = os.environ.get("SOCKET_HANDLE")
        if env_handle:
            try:
                sock_handle = int(env_handle)
            except ValueError:
                pass

    with open(log_path, "a") as log:
        log.write(f"Socket handle found: {sock_handle}\n")

    if sock_handle is None:
        # No socket handle — probably running locally
        print("No socket handle found. Running local test.")
        print(f"Args were: {sys.argv}")
        print("Check sockettest.log for details.")
        input("Press Enter to exit.")
        return

    # Try to connect via socket handle
    try:
        sock = socket.fromfd(sock_handle, socket.AF_INET, socket.SOCK_STREAM)
        io   = SocketIO(sock)

        with open(log_path, "a") as log:
            log.write("Socket connected successfully.\n")

        run_test(io)
        sock.close()

    except Exception as e:
        with open(log_path, "a") as log:
            log.write(f"Socket error: {e}\n")

        # Fallback — try writing directly to stdout
        print(f"Socket error: {e}")
        print("See sockettest.log for details.")
        input("Press Enter.")


if __name__ == "__main__":
    main()