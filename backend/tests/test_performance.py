"""
Performance tests for Biped Platform
Tests caching, rate limiting, response times, and system performance under load.
"""

import unittest
import time
import threading
import sys
import os
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.performance import (
    PerformanceCache, PerformanceMonitor, cache_result,
    monitor_performance, performance_cache, performance_monitor,
    paginate_query, AssetOptimizer, PerformanceProfiler
)

class TestPerformanceCache(unittest.TestCase):
    """Test performance cache functionality"""
    
    def setUp(self):
        self.cache = PerformanceCache(default_ttl=60)
    
    def test_basic_cache_operations(self):
        """Test basic cache set/get operations"""
        # Set and get value
        self.cache.set('test_key', 'test_value')
        self.assertEqual(self.cache.get('test_key'), 'test_value')
        
        # Test non-existent key
        self.assertIsNone(self.cache.get('non_existent'))
    
    def test_cache_ttl(self):
        """Test cache TTL (Time To Live)"""
        # Set value with short TTL
        self.cache.set('ttl_key', 'ttl_value', ttl=1)
        self.assertEqual(self.cache.get('ttl_key'), 'ttl_value')
        
        # Wait for expiration
        time.sleep(1.1)
        self.assertIsNone(self.cache.get('ttl_key'))
    
    def test_cache_size_limit(self):
        """Test cache size limit enforcement"""
        # Set max size to small value for testing
        self.cache.max_size = 3
        
        # Add items beyond limit
        for i in range(5):
            self.cache.set(f'key_{i}', f'value_{i}')
        
        # Should only have 3 items (most recent)
        self.assertEqual(len(self.cache.cache), 3)
        
        # Oldest items should be evicted
        self.assertIsNone(self.cache.get('key_0'))
        self.assertIsNone(self.cache.get('key_1'))
        
        # Recent items should still exist
        self.assertEqual(self.cache.get('key_4'), 'value_4')
    
    def test_cache_lru_behavior(self):
        """Test Least Recently Used (LRU) behavior"""
        self.cache.max_size = 3
        
        # Add 3 items
        self.cache.set('a', 'value_a')
        self.cache.set('b', 'value_b')
        self.cache.set('c', 'value_c')
        
        # Access 'a' to make it recently used
        self.cache.get('a')
        
        # Add new item (should evict 'b' as it's least recently used)
        self.cache.set('d', 'value_d')
        
        # 'b' should be evicted, others should remain
        self.assertIsNone(self.cache.get('b'))
        self.assertEqual(self.cache.get('a'), 'value_a')
        self.assertEqual(self.cache.get('c'), 'value_c')
        self.assertEqual(self.cache.get('d'), 'value_d')
    
    def test_cache_thread_safety(self):
        """Test cache thread safety"""
        results = []
        
        def cache_worker(worker_id):
            for i in range(100):
                key = f'worker_{worker_id}_key_{i}'
                value = f'worker_{worker_id}_value_{i}'
                self.cache.set(key, value)
                retrieved = self.cache.get(key)
                results.append(retrieved == value)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All operations should have succeeded
        self.assertTrue(all(results))

class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring functionality"""
    
    def setUp(self):
        self.monitor = PerformanceMonitor()
    
    def test_request_time_recording(self):
        """Test request time recording"""
        endpoint = 'test_endpoint'
        duration = 0.5
        
        self.monitor.record_request_time(endpoint, duration)
        
        stats = self.monitor.get_stats(hours=1)
        self.assertIn(f'avg_response_time_{endpoint}', stats)
        self.assertEqual(stats[f'avg_response_time_{endpoint}'], duration)
        self.assertEqual(stats[f'request_count_{endpoint}'], 1)
    
    def test_cache_hit_miss_recording(self):
        """Test cache hit/miss recording"""
        cache_type = 'test_cache'
        
        # Record hits and misses
        for _ in range(3):
            self.monitor.record_cache_hit(cache_type)
        for _ in range(2):
            self.monitor.record_cache_miss(cache_type)
        
        stats = self.monitor.get_stats(hours=1)
        self.assertEqual(stats[f'cache_hit_{cache_type}'], 3)
        self.assertEqual(stats[f'cache_miss_{cache_type}'], 2)
    
    def test_stats_time_filtering(self):
        """Test statistics time filtering"""
        endpoint = 'time_test_endpoint'
        
        # Record some data
        self.monitor.record_request_time(endpoint, 0.1)
        
        # Get stats for very short period (should be empty)
        stats = self.monitor.get_stats(hours=0.001)  # ~3.6 seconds
        self.assertEqual(stats.get(f'request_count_{endpoint}', 0), 0)
        
        # Get stats for longer period (should include data)
        stats = self.monitor.get_stats(hours=1)
        self.assertEqual(stats[f'request_count_{endpoint}'], 1)

class TestCacheDecorator(unittest.TestCase):
    """Test cache decorator functionality"""
    
    def setUp(self):
        # Clear cache before each test
        performance_cache.clear()
    
    def test_cache_decorator_basic(self):
        """Test basic cache decorator functionality"""
        call_count = 0
        
        @cache_result(ttl=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call should execute function
        result1 = expensive_function(1, 2)
        self.assertEqual(result1, 3)
        self.assertEqual(call_count, 1)
        
        # Second call with same args should use cache
        result2 = expensive_function(1, 2)
        self.assertEqual(result2, 3)
        self.assertEqual(call_count, 1)  # Should not increment
        
        # Call with different args should execute function
        result3 = expensive_function(2, 3)
        self.assertEqual(result3, 5)
        self.assertEqual(call_count, 2)
    
    def test_cache_decorator_with_kwargs(self):
        """Test cache decorator with keyword arguments"""
        call_count = 0
        
        @cache_result(ttl=60)
        def function_with_kwargs(a, b=10, c=20):
            nonlocal call_count
            call_count += 1
            return a + b + c
        
        # Test with different combinations
        result1 = function_with_kwargs(1, b=5, c=10)
        result2 = function_with_kwargs(1, b=5, c=10)  # Should use cache
        result3 = function_with_kwargs(1, c=10, b=5)  # Different order, should use cache
        
        self.assertEqual(result1, 16)
        self.assertEqual(result2, 16)
        self.assertEqual(result3, 16)
        self.assertEqual(call_count, 1)  # Should only call once

class TestMonitorPerformanceDecorator(unittest.TestCase):
    """Test performance monitoring decorator"""
    
    def setUp(self):
        self.monitor = PerformanceMonitor()
    
    @patch('utils.performance.performance_monitor')
    def test_monitor_decorator(self, mock_monitor):
        """Test performance monitoring decorator"""
        @monitor_performance
        def test_function():
            time.sleep(0.1)  # Simulate work
            return 'result'
        
        result = test_function()
        
        self.assertEqual(result, 'result')
        # Verify that record_request_time was called
        mock_monitor.record_request_time.assert_called_once()
        
        # Check that duration is reasonable
        call_args = mock_monitor.record_request_time.call_args
        endpoint, duration = call_args[0]
        self.assertEqual(endpoint, 'test_function')
        self.assertGreaterEqual(duration, 0.1)
        self.assertLess(duration, 0.2)  # Should be close to 0.1

class TestPaginationUtility(unittest.TestCase):
    """Test pagination utility"""
    
    def test_basic_pagination(self):
        """Test basic pagination functionality"""
        # Mock query object
        class MockQuery:
            def __init__(self, items):
                self.items = items
            
            def count(self):
                return len(self.items)
            
            def offset(self, offset):
                self.items = self.items[offset:]
                return self
            
            def limit(self, limit):
                self.items = self.items[:limit]
                return self
            
            def all(self):
                return self.items
        
        # Create test data
        test_items = list(range(1, 101))  # 100 items
        query = MockQuery(test_items)
        
        # Test first page
        result = paginate_query(query, page=1, per_page=10)
        
        self.assertEqual(len(result['items']), 10)
        self.assertEqual(result['items'][0], 1)
        self.assertEqual(result['total'], 100)
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['per_page'], 10)
        self.assertEqual(result['total_pages'], 10)
        self.assertFalse(result['has_prev'])
        self.assertTrue(result['has_next'])
    
    def test_pagination_edge_cases(self):
        """Test pagination edge cases"""
        class MockQuery:
            def __init__(self, items):
                self.items = items
            
            def count(self):
                return len(self.items)
            
            def offset(self, offset):
                return self
            
            def limit(self, limit):
                return self
            
            def all(self):
                return []
        
        # Test empty result set
        empty_query = MockQuery([])
        result = paginate_query(empty_query, page=1, per_page=10)
        
        self.assertEqual(len(result['items']), 0)
        self.assertEqual(result['total'], 0)
        self.assertEqual(result['total_pages'], 0)
        self.assertFalse(result['has_prev'])
        self.assertFalse(result['has_next'])

class TestAssetOptimizer(unittest.TestCase):
    """Test asset optimization functionality"""
    
    def setUp(self):
        self.optimizer = AssetOptimizer()
    
    def test_css_minification(self):
        """Test CSS minification"""
        css_input = """
        /* This is a comment */
        .class1 {
            color: red;
            margin: 10px;
        }
        
        .class2 {
            background: blue;
        }
        """
        
        minified = self.optimizer.minify_css(css_input)
        
        # Should remove comments
        self.assertNotIn('/* This is a comment */', minified)
        
        # Should reduce whitespace
        self.assertLess(len(minified), len(css_input))
        
        # Should still contain the actual CSS
        self.assertIn('color:red', minified.replace(' ', ''))
        self.assertIn('background:blue', minified.replace(' ', ''))
    
    def test_js_minification(self):
        """Test JavaScript minification"""
        js_input = """
        // This is a comment
        function testFunction() {
            /* Multi-line
               comment */
            var x = 10;
            return x + 5;
        }
        """
        
        minified = self.optimizer.minify_js(js_input)
        
        # Should remove comments
        self.assertNotIn('// This is a comment', minified)
        self.assertNotIn('/* Multi-line', minified)
        
        # Should reduce whitespace
        self.assertLess(len(minified), len(js_input))
        
        # Should still contain the actual JavaScript
        self.assertIn('function testFunction()', minified)
        self.assertIn('var x = 10', minified)
    
    def test_asset_hash_generation(self):
        """Test asset hash generation for versioning"""
        content1 = "body { color: red; }"
        content2 = "body { color: blue; }"
        
        hash1 = self.optimizer.generate_asset_hash(content1)
        hash2 = self.optimizer.generate_asset_hash(content2)
        
        # Hashes should be different for different content
        self.assertNotEqual(hash1, hash2)
        
        # Hash should be consistent for same content
        hash1_again = self.optimizer.generate_asset_hash(content1)
        self.assertEqual(hash1, hash1_again)
        
        # Hash should be 8 characters long
        self.assertEqual(len(hash1), 8)

class TestPerformanceProfiler(unittest.TestCase):
    """Test performance profiler"""
    
    def setUp(self):
        self.profiler = PerformanceProfiler()
    
    def test_profiling_basic(self):
        """Test basic profiling functionality"""
        profile_name = 'test_profile'
        
        self.profiler.start_profile(profile_name)
        time.sleep(0.1)  # Simulate work
        result = self.profiler.end_profile(profile_name)
        
        self.assertIsNotNone(result)
        self.assertIn('duration', result)
        self.assertIn('memory_used', result)
        self.assertIn('memory_peak', result)
        
        # Duration should be approximately 0.1 seconds
        self.assertGreaterEqual(result['duration'], 0.1)
        self.assertLess(result['duration'], 0.2)
    
    def test_profiling_nonexistent(self):
        """Test profiling non-existent profile"""
        result = self.profiler.end_profile('nonexistent')
        self.assertIsNone(result)

class TestLoadTesting(unittest.TestCase):
    """Test system performance under load"""
    
    def test_cache_performance_under_load(self):
        """Test cache performance with concurrent access"""
        cache = PerformanceCache()
        results = []
        
        def cache_load_test(thread_id):
            start_time = time.time()
            
            # Perform many cache operations
            for i in range(1000):
                key = f'load_test_{thread_id}_{i}'
                value = f'value_{thread_id}_{i}'
                
                cache.set(key, value)
                retrieved = cache.get(key)
                
                if retrieved != value:
                    results.append(False)
                    return
            
            duration = time.time() - start_time
            results.append(duration)
        
        # Run load test with multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=cache_load_test, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All operations should complete successfully
        self.assertEqual(len(results), 10)
        self.assertTrue(all(isinstance(r, float) for r in results))
        
        # Average time per thread should be reasonable
        avg_time = sum(results) / len(results)
        self.assertLess(avg_time, 5.0)  # Should complete within 5 seconds

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestPerformanceCache))
    test_suite.addTest(unittest.makeSuite(TestPerformanceMonitor))
    test_suite.addTest(unittest.makeSuite(TestCacheDecorator))
    test_suite.addTest(unittest.makeSuite(TestMonitorPerformanceDecorator))
    test_suite.addTest(unittest.makeSuite(TestPaginationUtility))
    test_suite.addTest(unittest.makeSuite(TestAssetOptimizer))
    test_suite.addTest(unittest.makeSuite(TestPerformanceProfiler))
    test_suite.addTest(unittest.makeSuite(TestLoadTesting))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nPerformance Tests Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)

