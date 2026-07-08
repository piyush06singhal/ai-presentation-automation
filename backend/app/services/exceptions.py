class DeckMateException(Exception):
    """Base exception class for all errors in the DeckMate system."""
    pass

class GroqAPIException(DeckMateException):
    """Exception raised when calls to the Groq API fail, timeout, or hit rate limits."""
    pass

class JSONParsingException(DeckMateException):
    """Exception raised when the LLM response cannot be parsed as valid JSON or violates schema schemas."""
    pass

class ValidationException(DeckMateException):
    """Exception raised when an LLM presentation plan fails the structural or logic audits."""
    pass
