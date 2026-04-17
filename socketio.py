"""
socketio.py - Socket I/O layer for Mystic BBS door integration
Demoscene: The Exploration of Art
A Cellfish Production
"""

import sys
import os
import socket as _socket
from socket import timeout as _socket_timeout

_io = None

def get_io():
    return _io

def set_io(io_instance):
    global _io
    _io = io_instance

class SocketIO:
    def __init__(self, sock):
        self.sock = sock
        self._buf = b""
        self.is_socket = True

    def write(self, data):
        if isinstance(data, str):
            data = data.encode("cp437", errors="replace")
        try:
            self.sock.sendall(data)
        except Exception:
            pass

    def flush(self):
        pass

    def read_byte(self):
        while True:
            while len(self._buf) < 1:
                try:
                    self.sock.settimeout(120)
                    chunk = self.sock.recv(256)
                    if not chunk:
                        return b""
                    self._buf += chunk
                except _socket_timeout:
                    try:
                        self.sock.sendall(b"\xff\xf1")
                    except Exception:
                        return b""
                    continue
                except Exception:
                    return b""

            byte = self._buf[:1]
            self._buf = self._buf[1:]

            if byte == b"\xff":
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
                continue

            return byte

    def getkey(self, valid_keys=None):
        while True:
            byte = self.read_byte()
            if not byte: return "Q"
            try:
                ch = byte.decode("cp437", errors="replace")
                key = ch.upper()
                if valid_keys is None or key in [k.upper() for k in valid_keys]:
                    return key
            except Exception:
                continue

    def getline(self, max_len=30):
        result = []
        while True:
            byte = self.read_byte()
            if not byte: break
            ch = byte.decode("cp437", errors="replace")
            if ch in ("\r", "\n"):
                self.write(b"\r\n")
                break
            elif ch in ("\x08", "\x7f"):
                if result:
                    result.pop()
                    self.write(b"\x08 \x08")
            elif len(result) < max_len and ch.isprintable():
                result.append(ch)
                self.write(byte)
        return "".join(result).strip()

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass

class DebugIO:
    def __init__(self):
        self.is_socket = False
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
            sys.stdout.buffer.write(data.encode("cp437", errors="replace"))
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
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    ch = sys.stdin.read(1)
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

    def close(self):
        pass

def init(socket_handle=None):
    if socket_handle is not None:
        try:
            sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM, 0, socket_handle)
            # Adopt handle directly — fromfd() dups it, leaving the original open at exit
            io = SocketIO(sock)
            set_io(io)
            return io
        except Exception:
            pass
    io = DebugIO()
    set_io(io)
    return io

def parse_socket_handle(argv=None):
    if argv is None: argv = sys.argv[1:]
    node, handle = None, None
    for arg in argv:
        try:
            val = int(arg)
            if node is None: node = val
            else: handle = val; break
        except ValueError: pass
    return handle