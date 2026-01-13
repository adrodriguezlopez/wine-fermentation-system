"""
Cancellation Token for ETL Import Operations.

Provides thread-safe mechanism to cancel long-running imports gracefully.
Used in conjunction with progress callbacks (ADR-030 Phase 3).
"""
import asyncio
from typing import Optional


class CancellationToken:
    """
    Thread-safe token for cancelling async operations.
    
    Example:
        token = CancellationToken()
        
        # In another thread/task:
        token.cancel()
        
        # In import loop:
        if token.is_cancelled:
            raise ImportCancelledException(...)
    """
    
    def __init__(self):
        """Initialize cancellation token in non-cancelled state."""
        self._cancelled = False
        self._lock = asyncio.Lock()
    
    async def cancel(self) -> None:
        """
        Request cancellation of the operation.
        
        Thread-safe: can be called from any thread/task.
        """
        async with self._lock:
            self._cancelled = True
    
    @property
    def is_cancelled(self) -> bool:
        """
        Check if cancellation has been requested.
        
        Returns:
            True if cancel() has been called, False otherwise.
        """
        return self._cancelled
    
    def reset(self) -> None:
        """
        Reset token to non-cancelled state.
        
        Useful for reusing token across multiple operations.
        Note: Not async since it's typically called between operations.
        """
        self._cancelled = False


class ImportCancelledException(Exception):
    """
    Raised when import is cancelled by user via CancellationToken.
    
    Contains information about partial progress before cancellation.
    """
    
    def __init__(self, imported: int, total: int, message: Optional[str] = None):
        """
        Initialize exception with partial progress info.
        
        Args:
            imported: Number of fermentations successfully imported before cancellation
            total: Total number of fermentations to import
            message: Optional custom message
        """
        self.imported = imported
        self.total = total
        
        if message:
            self.message = message
        else:
            self.message = f"Import cancelled after {imported}/{total} fermentations"
        
        super().__init__(self.message)
