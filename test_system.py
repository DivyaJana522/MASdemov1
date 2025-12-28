"""
Comprehensive Test Suite for Multi-Agent Stock Analysis Platform

This test suite validates all major components and functionality.
Run this to ensure the system is working correctly.

Usage:
    python test_system.py
"""
from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class SystemTester:
    """Comprehensive system testing suite."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results: List[Tuple[str, bool, str]] = []
    
    def print_header(self, text: str):
        """Print section header."""
        print(f"\n{BLUE}{'='*60}")
        print(f"{text}")
        print(f"{'='*60}{RESET}\n")
    
    def test(self, name: str, func, *args, **kwargs) -> bool:
        """Run a single test."""
        try:
            print(f"  Testing: {name}...", end=" ")
            result = func(*args, **kwargs)
            if result:
                print(f"{GREEN}✓ PASS{RESET}")
                self.passed += 1
                self.results.append((name, True, ""))
                return True
            else:
                print(f"{RED}✗ FAIL{RESET}")
                self.failed += 1
                self.results.append((name, False, "Test returned False"))
                return False
        except Exception as e:
            print(f"{RED}✗ FAIL: {str(e)}{RESET}")
            self.failed += 1
            self.results.append((name, False, str(e)))
            return False
    
    def warn(self, message: str):
        """Print warning message."""
        print(f"{YELLOW}  ⚠ Warning: {message}{RESET}")
        self.warnings += 1
    
    # ========== DEPENDENCY TESTS ==========
    
    def test_dependencies(self) -> bool:
        """Test all required dependencies are installed."""
        required = [
            'pandas', 'numpy', 'yfinance', 'ta', 'scipy',
            'vaderSentiment', 'streamlit', 'certifi', 'curl_cffi'
        ]
        missing = []
        for module in required:
            try:
                __import__(module)
            except ImportError:
                missing.append(module)
        
        if missing:
            print(f"    Missing: {', '.join(missing)}")
            return False
        return True
    
    # ========== IMPORT TESTS ==========
    
    def test_import_agents(self) -> bool:
        """Test agent imports."""
        from agents.technical_agent import TechnicalAgent
        from agents.fundamental_agent import FundamentalAgent
        from agents.sentiment_agent import SentimentAgent
        from agents.base_agent import BaseAgent
        
        # Verify they are classes
        assert TechnicalAgent is not None
        assert FundamentalAgent is not None
        assert SentimentAgent is not None
        assert BaseAgent is not None
        return True
    
    def test_import_coordination(self) -> bool:
        """Test coordination imports."""
        from coordination.master_agent import MasterAgent
        from coordination.market_regime import MarketRegimeDetector
        
        assert MasterAgent is not None
        assert MarketRegimeDetector is not None
        return True
    
    def test_import_data(self) -> bool:
        """Test data module imports."""
        from data.data_fetcher import DataFetcher
        from data.cache_manager import CacheManager
        
        assert DataFetcher is not None
        assert CacheManager is not None
        return True
    
    def test_import_utils(self) -> bool:
        """Test utilities imports."""
        from utils.logging_utils import get_logger
        from utils.normalization import clip_signal
        from utils.result_storage import ResultStorage
        
        assert get_logger is not None
        assert clip_signal is not None
        assert ResultStorage is not None
        return True
    
    # ========== FUNCTIONALITY TESTS ==========
    
    def test_data_fetcher(self) -> bool:
        """Test DataFetcher initialization."""
        from data.data_fetcher import DataFetcher
        
        fetcher = DataFetcher()
        assert fetcher is not None
        assert fetcher.cache is not None
        return True
    
    def test_cache_manager(self) -> bool:
        """Test CacheManager functionality."""
        from data.cache_manager import CacheManager
        import tempfile
        import time
        
        # Create temp cache with unique name
        temp_dir = tempfile.gettempdir()
        cache_file = os.path.join(temp_dir, f"test_cache_{os.getpid()}.db")
        
        try:
            cache = CacheManager(cache_file, default_ttl=1)
            
            # Test set/get
            cache.set("test_key", {"data": "test_value"})
            result = cache.get("test_key")
            
            assert result is not None
            assert result["data"] == "test_value"
            
            # Test expiry
            time.sleep(2)
            expired = cache.get("test_key")
            assert expired is None
            
            # Test stale cache
            cache.set("test_key2", {"data": "stale"}, ttl=1)
            time.sleep(2)
            stale = cache.get("test_key2", allow_stale=True)
            assert stale is not None
            
            # Close and cleanup
            cache.close()
            time.sleep(0.5)  # Give Windows time to release the file
            
            # Try to remove file, ignore errors
            try:
                os.unlink(cache_file)
                # Also clean up WAL files
                for ext in ['-wal', '-shm']:
                    try:
                        os.unlink(cache_file + ext)
                    except:
                        pass
            except:
                pass  # File might still be locked on Windows, that's OK
            
        except Exception as e:
            # Cleanup on error
            try:
                os.unlink(cache_file)
            except:
                pass
            raise e
        
        return True
    
    def test_agents_initialization(self) -> bool:
        """Test agent initialization."""
        from agents.technical_agent import TechnicalAgent
        from agents.fundamental_agent import FundamentalAgent
        from agents.sentiment_agent import SentimentAgent
        
        tech = TechnicalAgent()
        fund = FundamentalAgent()
        sent = SentimentAgent()
        
        assert tech is not None
        assert fund is not None
        assert sent is not None
        return True
    
    def test_master_agent(self) -> bool:
        """Test MasterAgent initialization."""
        from coordination.master_agent import MasterAgent
        from agents.technical_agent import TechnicalAgent
        from agents.fundamental_agent import FundamentalAgent
        from agents.sentiment_agent import SentimentAgent
        
        agents = [TechnicalAgent(), FundamentalAgent(), SentimentAgent()]
        master = MasterAgent(agents)
        
        assert master is not None
        assert len(master.agents) == 3
        return True
    
    def test_result_storage(self) -> bool:
        """Test ResultStorage functionality."""
        from utils.result_storage import ResultStorage
        import tempfile
        import shutil
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        try:
            storage = ResultStorage(results_dir=temp_dir)
            
            # Test save
            test_result = {
                "decision": "BUY",
                "final_score": 0.75,
                "overall_confidence": 0.85
            }
            
            path = storage.save_result("TEST.NS", test_result)
            assert os.path.exists(path)
            
            # Test retrieve
            latest = storage.get_latest_result("TEST.NS")
            assert latest is not None
            assert latest["result"]["decision"] == "BUY"
            
            # Test list
            results = storage.list_results()
            assert len(results) > 0
            
        finally:
            shutil.rmtree(temp_dir)
        
        return True
    
    def test_normalization(self) -> bool:
        """Test signal normalization."""
        from utils.normalization import clip_signal
        
        assert clip_signal(1.5) == 1.0
        assert clip_signal(-1.5) == -1.0
        assert clip_signal(0.5) == 0.5
        return True
    
    def test_market_regime_detector(self) -> bool:
        """Test MarketRegimeDetector."""
        from coordination.market_regime import MarketRegimeDetector
        
        detector = MarketRegimeDetector()
        assert detector is not None
        assert detector.vol_threshold == 0.25
        return True
    
    # ========== INTEGRATION TESTS ==========
    
    def test_end_to_end_analysis(self) -> bool:
        """Test complete analysis workflow with cached data."""
        from data.data_fetcher import DataFetcher
        from agents.technical_agent import TechnicalAgent
        from agents.fundamental_agent import FundamentalAgent
        from agents.sentiment_agent import SentimentAgent
        from coordination.market_regime import MarketRegimeDetector
        from coordination.master_agent import MasterAgent
        
        # Fetch data (should use cache)
        fetcher = DataFetcher()
        snapshot = fetcher.build_snapshot("RELIANCE.NS")
        
        # Verify snapshot structure
        assert "price_data" in snapshot
        assert "fundamentals" in snapshot
        assert "news" in snapshot
        assert "macro" in snapshot
        
        # Run agents
        agents = [TechnicalAgent(), FundamentalAgent(), SentimentAgent()]
        regime = MarketRegimeDetector().detect(snapshot)
        master = MasterAgent(agents)
        decision = master.decide(snapshot, regime)
        
        # Verify decision structure
        assert "decision" in decision
        assert decision["decision"] in ["BUY", "SELL", "HOLD"]
        assert "final_score" in decision
        assert "overall_confidence" in decision
        assert "weights" in decision
        assert "agents" in decision
        assert "explanation" in decision
        
        return True
    
    # ========== FILE STRUCTURE TESTS ==========
    
    def test_folder_structure(self) -> bool:
        """Test project folder structure."""
        base_dir = Path(__file__).parent
        
        required_dirs = [
            "agents",
            "coordination",
            "data",
            "ui",
            "utils",
            "results",
        ]
        
        missing = []
        for dir_name in required_dirs:
            if not (base_dir / dir_name).exists():
                missing.append(dir_name)
        
        if missing:
            print(f"    Missing directories: {', '.join(missing)}")
            return False
        return True
    
    def test_required_files(self) -> bool:
        """Test required files exist."""
        base_dir = Path(__file__).parent
        
        required_files = [
            "__init__.py",
            "main.py",
            "requirements.txt",
            "README.md",
            ".gitignore",
            "agents/__init__.py",
            "agents/base_agent.py",
            "agents/technical_agent.py",
            "agents/fundamental_agent.py",
            "agents/sentiment_agent.py",
            "coordination/__init__.py",
            "coordination/master_agent.py",
            "coordination/market_regime.py",
            "data/__init__.py",
            "data/data_fetcher.py",
            "data/cache_manager.py",
            "utils/__init__.py",
            "utils/logging_utils.py",
            "utils/result_storage.py",
            "ui/__init__.py",
            "ui/app.py",
        ]
        
        missing = []
        for file_path in required_files:
            if not (base_dir / file_path).exists():
                missing.append(file_path)
        
        if missing:
            print(f"    Missing files: {', '.join(missing)}")
            return False
        return True
    
    def test_cache_exists(self) -> bool:
        """Test cache file exists."""
        base_dir = Path(__file__).parent
        cache_file = base_dir / "data" / "cache.sqlite3"
        
        if not cache_file.exists():
            self.warn("Cache file doesn't exist. Run create_sample_cache.py to create it.")
            return True  # This is a warning, not a failure
        return True
    
    def test_results_directory(self) -> bool:
        """Test results directory is writable."""
        base_dir = Path(__file__).parent
        results_dir = base_dir / "results"
        
        assert results_dir.exists()
        assert results_dir.is_dir()
        
        # Test write permission
        test_file = results_dir / "test_write.tmp"
        try:
            test_file.write_text("test")
            test_file.unlink()
            return True
        except Exception as e:
            print(f"    Cannot write to results directory: {e}")
            return False
    
    # ========== DOCUMENTATION TESTS ==========
    
    def test_documentation_exists(self) -> bool:
        """Test documentation files exist."""
        base_dir = Path(__file__).parent
        
        docs = [
            "README.md",
            "DEVELOPER_GUIDE.md",
        ]
        
        missing = []
        for doc in docs:
            if not (base_dir / doc).exists():
                missing.append(doc)
        
        if missing:
            print(f"    Missing documentation: {', '.join(missing)}")
            return False
        return True
    
    # ========== RUN ALL TESTS ==========
    
    def run_all_tests(self):
        """Run all test suites."""
        print(f"\n{BLUE}{'='*60}")
        print("Multi-Agent Stock Analysis Platform - System Test")
        print(f"{'='*60}{RESET}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Dependency Tests
        self.print_header("1. DEPENDENCY TESTS")
        self.test("Required packages installed", self.test_dependencies)
        
        # Import Tests
        self.print_header("2. IMPORT TESTS")
        self.test("Agent imports", self.test_import_agents)
        self.test("Coordination imports", self.test_import_coordination)
        self.test("Data module imports", self.test_import_data)
        self.test("Utility imports", self.test_import_utils)
        
        # Functionality Tests
        self.print_header("3. FUNCTIONALITY TESTS")
        self.test("DataFetcher initialization", self.test_data_fetcher)
        self.test("CacheManager operations", self.test_cache_manager)
        self.test("Agent initialization", self.test_agents_initialization)
        self.test("MasterAgent initialization", self.test_master_agent)
        self.test("ResultStorage operations", self.test_result_storage)
        self.test("Signal normalization", self.test_normalization)
        self.test("MarketRegimeDetector initialization", self.test_market_regime_detector)
        
        # Integration Tests
        self.print_header("4. INTEGRATION TESTS")
        self.test("End-to-end analysis workflow", self.test_end_to_end_analysis)
        
        # File Structure Tests
        self.print_header("5. FILE STRUCTURE TESTS")
        self.test("Required directories exist", self.test_folder_structure)
        self.test("Required files exist", self.test_required_files)
        self.test("Cache file status", self.test_cache_exists)
        self.test("Results directory writable", self.test_results_directory)
        
        # Documentation Tests
        self.print_header("6. DOCUMENTATION TESTS")
        self.test("Documentation files exist", self.test_documentation_exists)
        
        # Print Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n{BLUE}{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}{RESET}\n")
        
        print(f"  Total Tests: {total}")
        print(f"  {GREEN}Passed: {self.passed}{RESET}")
        print(f"  {RED}Failed: {self.failed}{RESET}")
        print(f"  {YELLOW}Warnings: {self.warnings}{RESET}")
        print(f"  Pass Rate: {pass_rate:.1f}%\n")
        
        if self.failed > 0:
            print(f"{RED}{'='*60}")
            print("FAILED TESTS")
            print(f"{'='*60}{RESET}\n")
            for name, passed, error in self.results:
                if not passed:
                    print(f"  {RED}✗{RESET} {name}")
                    if error:
                        print(f"    Error: {error}\n")
        
        print(f"{BLUE}{'='*60}{RESET}")
        
        if self.failed == 0:
            print(f"{GREEN}✓ ALL TESTS PASSED - SYSTEM IS PRODUCTION READY!{RESET}")
        else:
            print(f"{RED}✗ SOME TESTS FAILED - REVIEW ERRORS ABOVE{RESET}")
        
        print(f"{BLUE}{'='*60}{RESET}\n")
        
        return self.failed == 0


def main():
    """Main entry point."""
    tester = SystemTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
