import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class BufferManager:
    def __init__(self, size=500):
        self.size = size
        self.buffer = b""  # Use bytes
        self.snapshot = b""  # Use bytes
        self.line_count = 0

    def add_line(self, line):
        logging.debug(f"Adding line: {line}")
        if isinstance(line, str):
            line = line.encode('utf-8')  # Convert str to bytes

        lines = line.split(b'\n')
        need_flush = False
        for l in lines:
            self.buffer += l + b"\n"
            self.line_count += 1
            if self.line_count >= self.size:
                need_flush = True

        if need_flush:
            self.flush()
            return False

        return True

    def flush(self):
        logging.debug(f"Flushing buffer: {self.buffer}")    
        if self.buffer != b"":
            self.snapshot = self.buffer
            self.buffer = b""  # Reset buffer to bytes
            self.line_count = 0
            return True
        return False

    def get_snapshot(self):
        logging.debug(f"Getting snapshot: {self.snapshot}")
        if self.snapshot == b"":
            return None
        return self.snapshot.decode('utf-8')  # Convert bytes to str for output
