"""
Result Storage Module

This module handles saving analysis results to disk for audit trail and analysis.
Each result is stored as a JSON file with timestamp and symbol information.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .logging_utils import get_logger

logger = get_logger(__name__)


class ResultStorage:
    """
    Manages storage of stock analysis results to the file system.
    
    Each analysis result is saved as a JSON file with the following naming convention:
    {symbol}_{timestamp}.json
    
    Example: RELIANCE.NS_20251224_143052.json
    """
    
    def __init__(self, results_dir: Optional[str] = None):
        """
        Initialize result storage manager.
        
        Args:
            results_dir: Directory to store results. Defaults to 'results' in project root.
        """
        if results_dir is None:
            # Default to results directory in project root
            base_dir = Path(__file__).parent.parent
            results_dir = base_dir / "results"
        
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ResultStorage initialized. Saving to: {self.results_dir}")
    
    def save_result(
        self, 
        symbol: str, 
        result: Dict[str, Any], 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save an analysis result to disk.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            result: The complete analysis result dictionary
            metadata: Optional metadata to include (user info, settings, etc.)
        
        Returns:
            Path to the saved file
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Sanitize symbol for filename (replace dots with underscores)
            safe_symbol = symbol.replace(".", "_")
            filename = f"{safe_symbol}_{timestamp}.json"
            filepath = self.results_dir / filename
            
            # Prepare complete output with metadata
            output = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "result": result,
            }
            
            if metadata:
                output["metadata"] = metadata
            
            # Write to file with pretty formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Result saved successfully: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save result for {symbol}: {e}")
            raise IOError(f"Could not save result: {e}")
    
    def get_latest_result(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the most recent analysis result for a symbol.
        
        Args:
            symbol: Stock symbol to search for
            
        Returns:
            The latest result dictionary, or None if not found
        """
        try:
            safe_symbol = symbol.replace(".", "_")
            pattern = f"{safe_symbol}_*.json"
            
            # Find all matching files
            matching_files = sorted(
                self.results_dir.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            if not matching_files:
                logger.debug(f"No saved results found for {symbol}")
                return None
            
            # Read the most recent file
            latest_file = matching_files[0]
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Retrieved latest result for {symbol} from {latest_file.name}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to retrieve latest result for {symbol}: {e}")
            return None
    
    def list_results(self, symbol: Optional[str] = None, limit: int = 10) -> list:
        """
        List recent analysis results.
        
        Args:
            symbol: Optional symbol to filter by. If None, returns all results.
            limit: Maximum number of results to return
            
        Returns:
            List of result file information dictionaries
        """
        try:
            if symbol:
                safe_symbol = symbol.replace(".", "_")
                pattern = f"{safe_symbol}_*.json"
            else:
                pattern = "*.json"
            
            # Find and sort files by modification time
            files = sorted(
                self.results_dir.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:limit]
            
            results = []
            for filepath in files:
                stat = filepath.stat()
                results.append({
                    "filename": filepath.name,
                    "path": str(filepath),
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            
            logger.debug(f"Listed {len(results)} results (symbol={symbol}, limit={limit})")
            return results
            
        except Exception as e:
            logger.error(f"Failed to list results: {e}")
            return []
    
    def cleanup_old_results(self, days: int = 30) -> int:
        """
        Delete result files older than specified days.
        
        Args:
            days: Delete files older than this many days
            
        Returns:
            Number of files deleted
        """
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_timestamp = cutoff_time.timestamp()
            
            deleted_count = 0
            for filepath in self.results_dir.glob("*.json"):
                if filepath.stat().st_mtime < cutoff_timestamp:
                    filepath.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old result: {filepath.name}")
            
            logger.info(f"Cleanup completed: {deleted_count} files deleted (older than {days} days)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0
