import io

class ExportService:
    """Manages writing compiled binary payloads to files or memory streams."""

    @staticmethod
    def export_to_stream(ppt_bytes: bytes) -> io.BytesIO:
        """Wraps presentation raw bytes into an in-memory BytesIO stream."""
        return io.BytesIO(ppt_bytes)

    @staticmethod
    def export_to_file(ppt_bytes: bytes, destination_path: str):
        """Writes presentation binary payload directly to a local file path."""
        with open(destination_path, "wb") as f:
            f.write(ppt_bytes)
