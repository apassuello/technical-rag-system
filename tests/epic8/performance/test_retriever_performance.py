"""
Performance Tests for Epic 8 Retriever Service.

Tests performance characteristics, scalability, and resource usage of the Retriever Service
under various load conditions. Based on CT-8.3 performance specifications.

Testing Philosophy:
- Hard Fails: >60s operations, >8GB memory, service crashes, 0% success rate
- Quality Flags: P95 latency >2s, throughput <10 ops/sec, >70% resource usage
"""

import pytest
import asyncio
import time
import psutil
import os
import tempfile
import statistics
from typing import Dict, Any, List
from pathlib import Path
import sys
import concurrent.futures

# Add services to path
services_path = Path(__file__).parent.parent.parent.parent / "services" / "retriever"
project_path = Path(__file__).parent.parent.parent.parent
if services_path.exists():
    sys.path.insert(0, str(services_path))
if project_path.exists():
    sys.path.insert(0, str(project_path))

try:
    sys.path.insert(0, str(project_path / "services" / "retriever"))
    from retriever_app.core.retriever import RetrieverService
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class TestRetrieverServiceBasicPerformance:
    """Test basic performance characteristics of retrieval operations."""

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_single_query_latency(self):
        """Test latency of single query operations (CT-8.3.1)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                config = {
                    'retriever_config': {
                        'vector_index': {'type': 'faiss', 'path': temp_dir},
                        'sparse': {'type': 'bm25'},
                        'fusion': {'type': 'rrf'},
                        'reranker': {'type': 'identity'}
                    },
                    'embedder_config': {
                        'type': 'sentence_transformer',
                        'config': {'model_name': 'all-MiniLM-L6-v2', 'device': 'cpu'}
                    }
                }
                
                service = RetrieverService(config=config)
                
                # Index test documents
                test_documents = [
                    {
                        "content": f"Performance test document {i} containing various keywords for latency testing. This document has enough content to be meaningful for retrieval performance analysis.",
                        "metadata": {"title": f"Perf Doc {i}", "category": "performance"},
                        "doc_id": f"perf_{i:03d}",
                        "source": f"perf_test_{i}.pdf"
                    }
                    for i in range(50)  # 50 documents for meaningful performance test
                ]
                
                await service.index_documents(test_documents)
                
                # Test queries
                test_queries = [
                    "performance test document",
                    "keywords for latency testing",
                    "meaningful for retrieval performance",
                    "analysis document containing",
                    "various keywords performance"
                ]
                
                latencies = []
                
                for query in test_queries:
                    # Warm-up query (not measured)
                    await service.retrieve_documents(query, k=5)
                    
                    # Measured queries
                    for _ in range(5):  # 5 measurements per query
                        start_time = time.time()
                        results = await service.retrieve_documents(query, k=10)
                        latency = time.time() - start_time
                        latencies.append(latency)
                        
                        # Hard fail: Individual query >60s is broken
                        assert latency < 60.0, f"Query latency {latency:.2f}s exceeds 60s limit"
                        
                        # Verify we got results
                        assert len(results) > 0, "Should return results for performance test"
                
                # Calculate performance metrics
                avg_latency = statistics.mean(latencies)
                p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
                p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
                min_latency = min(latencies)
                max_latency = max(latencies)
                
                # Quality thresholds based on Epic 8 specifications
                # Quality flag: P95 latency >2s indicates performance issues
                if p95_latency > 2.0:
                    pytest.warns(UserWarning, f"P95 latency {p95_latency:.3f}s exceeds 2s target")
                
                # Quality flag: Average latency >1s is slow
                if avg_latency > 1.0:
                    pytest.warns(UserWarning, f"Average latency {avg_latency:.3f}s exceeds 1s target")
                
                print(f"Single query latency performance:")
                print(f"  Average: {avg_latency:.3f}s")
                print(f"  P95: {p95_latency:.3f}s")
                print(f"  P99: {p99_latency:.3f}s")
                print(f"  Range: {min_latency:.3f}s - {max_latency:.3f}s")
                
            except Exception as e:
                pytest.fail(f"Single query latency test failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_indexing_throughput(self):
        """Test document indexing throughput performance (CT-8.3.3)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                config = {
                    'retriever_config': {
                        'vector_index': {'type': 'faiss', 'path': temp_dir},
                        'sparse': {'type': 'bm25'},
                        'fusion': {'type': 'rrf'},
                        'reranker': {'type': 'identity'}
                    },
                    'embedder_config': {
                        'type': 'sentence_transformer',
                        'config': {'model_name': 'all-MiniLM-L6-v2', 'device': 'cpu'}
                    }
                }
                
                service = RetrieverService(config=config)
                
                # Test different batch sizes
                batch_sizes = [1, 5, 10, 25, 50]
                throughput_results = {}
                
                for batch_size in batch_sizes:
                    # Generate test documents
                    test_documents = [
                        {
                            "content": f"Throughput test document {i} with substantial content for realistic indexing performance measurement. This document contains enough text to represent typical document sizes in real-world scenarios.",
                            "metadata": {"title": f"Throughput Doc {i}", "batch": batch_size},
                            "doc_id": f"throughput_{batch_size}_{i:03d}",
                            "source": f"throughput_batch_{batch_size}_{i}.pdf"
                        }
                        for i in range(batch_size)
                    ]
                    
                    # Measure indexing time
                    start_time = time.time()
                    result = await service.index_documents(test_documents)
                    indexing_time = time.time() - start_time
                    
                    # Hard fail: Indexing >60s per document is broken
                    time_per_doc = indexing_time / batch_size
                    assert time_per_doc < 60.0, f"Indexing {time_per_doc:.2f}s per document exceeds 60s limit"
                    
                    # Calculate throughput
                    throughput = batch_size / indexing_time  # docs/second
                    throughput_results[batch_size] = {
                        'throughput': throughput,
                        'time_per_doc': time_per_doc,
                        'total_time': indexing_time,
                        'success': result.get('success', False)
                    }
                    
                    # Verify indexing succeeded
                    assert result.get('success', False), f"Indexing batch {batch_size} failed"
                    
                    print(f"Batch size {batch_size:2d}: {throughput:.2f} docs/sec ({time_per_doc:.3f}s per doc)")
                
                # Quality assessments
                best_throughput = max(throughput_results.values(), key=lambda x: x['throughput'])['throughput']
                
                # Quality flag: Throughput <1 doc/sec is very slow
                if best_throughput < 1.0:
                    pytest.warns(UserWarning, f"Best throughput {best_throughput:.2f} docs/sec below 1 doc/sec")
                
                # Quality flag: Should see some improvement with larger batches
                small_batch_throughput = throughput_results[1]['throughput']
                large_batch_throughput = throughput_results[max(batch_sizes)]['throughput']
                
                if large_batch_throughput < small_batch_throughput * 1.5:
                    pytest.warns(UserWarning, f"Batching not improving throughput significantly")
                
                print(f"\nIndexing throughput summary:")
                print(f"  Best throughput: {best_throughput:.2f} docs/sec")
                print(f"  Batch efficiency: {large_batch_throughput/small_batch_throughput:.2f}x improvement")
                
            except Exception as e:
                pytest.fail(f"Indexing throughput test failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_concurrent_query_performance(self):
        """Test performance under concurrent query load (CT-8.3.2)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                config = {
                    'retriever_config': {
                        'vector_index': {'type': 'faiss', 'path': temp_dir},
                        'sparse': {'type': 'bm25'},
                        'fusion': {'type': 'rrf'},
                        'reranker': {'type': 'identity'}
                    },
                    'embedder_config': {
                        'type': 'sentence_transformer',
                        'config': {'model_name': 'all-MiniLM-L6-v2', 'device': 'cpu'}
                    }
                }
                
                service = RetrieverService(config=config)
                
                # Index documents for concurrent testing
                documents = [
                    {
                        "content": f"Concurrent performance test document {i} designed for multi-user load testing scenarios with realistic content distribution.",
                        "metadata": {"title": f"Concurrent Doc {i}", "thread_test": True},
                        "doc_id": f"concurrent_{i:03d}",
                        "source": f"concurrent_{i}.pdf"
                    }
                    for i in range(100)  # More documents for concurrent testing
                ]
                
                await service.index_documents(documents)
                
                # Test different concurrency levels
                concurrency_levels = [1, 5, 10, 20]
                concurrent_results = {}
                
                for concurrency in concurrency_levels:
                    # Generate queries
                    queries = [
                        f"concurrent performance test document {i % 10}"
                        for i in range(concurrency * 3)  # 3 queries per concurrent worker
                    ]
                    
                    # Measure concurrent performance
                    start_time = time.time()
                    
                    # Create batches of concurrent queries
                    query_batches = [queries[i:i+concurrency] for i in range(0, len(queries), concurrency)]
                    
                    all_results = []
                    for batch in query_batches:
                        # Execute batch concurrently
                        tasks = [service.retrieve_documents(query, k=5) for query in batch]
                        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                        all_results.extend(batch_results)
                    
                    total_time = time.time() - start_time
                    
                    # Analyze results
                    successful_results = [r for r in all_results if not isinstance(r, Exception)]
                    success_rate = len(successful_results) / len(all_results)
                    
                    # Hard fail: Success rate <50% indicates serious concurrency issues
                    assert success_rate >= 0.5, f"Concurrent success rate {success_rate:.2%} too low at concurrency {concurrency}"
                    
                    # Calculate throughput
                    throughput = len(queries) / total_time
                    avg_latency = total_time / len(queries)
                    
                    concurrent_results[concurrency] = {
                        'success_rate': success_rate,
                        'throughput': throughput,
                        'avg_latency': avg_latency,
                        'total_time': total_time
                    }
                    
                    print(f"Concurrency {concurrency:2d}: {success_rate:.1%} success, {throughput:.1f} q/s, {avg_latency:.3f}s avg")
                
                # Quality assessments
                peak_throughput = max(concurrent_results.values(), key=lambda x: x['throughput'])['throughput']
                
                # Quality flag: Peak throughput <10 queries/sec is low
                if peak_throughput < 10.0:
                    pytest.warns(UserWarning, f"Peak concurrent throughput {peak_throughput:.1f} q/s below 10 q/s target")
                
                # Quality flag: Success rate should remain high under load
                high_concurrency_success = concurrent_results[max(concurrency_levels)]['success_rate']
                if high_concurrency_success < 0.9:
                    pytest.warns(UserWarning, f"High concurrency success rate {high_concurrency_success:.1%} below 90%")
                
                print(f"\nConcurrent performance summary:")
                print(f"  Peak throughput: {peak_throughput:.1f} queries/sec")
                print(f"  High concurrency success: {high_concurrency_success:.1%}")
                
            except Exception as e:
                pytest.fail(f"Concurrent query performance test failed: {e}")


class TestRetrieverServiceScalabilityPerformance:
    """Test scalability characteristics with increasing data sizes."""

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_dataset_size_scaling(self):
        """Test how performance scales with dataset size."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                config = {
                    'retriever_config': {
                        'vector_index': {'type': 'faiss', 'path': temp_dir},
                        'sparse': {'type': 'bm25'},
                        'fusion': {'type': 'rrf'},
                        'reranker': {'type': 'identity'}
                    },
                    'embedder_config': {
                        'type': 'sentence_transformer',
                        'config': {'model_name': 'all-MiniLM-L6-v2', 'device': 'cpu'}
                    }
                }
                
                service = RetrieverService(config=config)
                
                # Test different dataset sizes
                dataset_sizes = [10, 50, 100, 200]  # Start small for CI environments
                scaling_results = {}
                
                for size in dataset_sizes:
                    # Generate documents
                    documents = [
                        {
                            "content": f"Scaling test document {i} for dataset size {size}. This document contains topic-specific content about scaling, performance, and retrieval systems to ensure meaningful search results.",
                            "metadata": {"title": f"Scale Doc {i}", "size": size, "topic": f"topic_{i%5}"},
                            "doc_id": f"scale_{size}_{i:04d}",
                            "source": f"scaling_{size}_{i}.pdf"
                        }
                        for i in range(size)
                    ]
                    
                    # Measure indexing time
                    start_time = time.time()
                    index_result = await service.index_documents(documents)
                    indexing_time = time.time() - start_time
                    
                    # Hard fail: Indexing time grows too dramatically
                    indexing_rate = size / indexing_time
                    assert indexing_time < size * 5.0, f"Indexing {size} docs took {indexing_time:.1f}s - too slow"
                    
                    # Test retrieval performance at this scale
                    test_queries = [
                        "scaling test document",
                        "performance and retrieval systems", 
                        "topic-specific content about scaling",
                        f"dataset size {size}",
                        "meaningful search results"
                    ]
                    
                    retrieval_times = []
                    for query in test_queries:
                        start_time = time.time()
                        results = await service.retrieve_documents(query, k=10)
                        retrieval_time = time.time() - start_time
                        retrieval_times.append(retrieval_time)
                        
                        # Verify results quality
                        assert len(results) > 0, f"Should return results at scale {size}"
                    
                    avg_retrieval_time = statistics.mean(retrieval_times)
                    
                    scaling_results[size] = {
                        'indexing_time': indexing_time,
                        'indexing_rate': indexing_rate,
                        'avg_retrieval_time': avg_retrieval_time,
                        'retrieval_times': retrieval_times,
                        'document_count': service.retriever.get_document_count() if service.retriever else 0
                    }
                    
                    print(f"Dataset size {size:3d}: Index {indexing_rate:.1f} docs/s, Retrieve {avg_retrieval_time:.3f}s avg")
                
                # Analyze scaling characteristics
                small_scale = scaling_results[min(dataset_sizes)]
                large_scale = scaling_results[max(dataset_sizes)]
                
                # Quality assessment: Retrieval time shouldn't grow dramatically
                retrieval_scaling_factor = large_scale['avg_retrieval_time'] / small_scale['avg_retrieval_time']
                dataset_scaling_factor = max(dataset_sizes) / min(dataset_sizes)
                
                # Quality flag: Retrieval time growth should be sub-linear
                if retrieval_scaling_factor > dataset_scaling_factor * 0.5:
                    pytest.warns(UserWarning, f"Retrieval time scaling factor {retrieval_scaling_factor:.1f}x concerning")
                
                # Quality flag: Indexing rate shouldn't degrade too much
                indexing_scaling_factor = small_scale['indexing_rate'] / large_scale['indexing_rate']
                if indexing_scaling_factor > 3.0:
                    pytest.warns(UserWarning, f"Indexing rate degraded {indexing_scaling_factor:.1f}x at larger scales")
                
                print(f"\nScaling analysis:")
                print(f"  Dataset size: {min(dataset_sizes)} -> {max(dataset_sizes)} ({dataset_scaling_factor:.1f}x)")
                print(f"  Retrieval time: {small_scale['avg_retrieval_time']:.3f}s -> {large_scale['avg_retrieval_time']:.3f}s ({retrieval_scaling_factor:.1f}x)")
                print(f"  Indexing rate: {small_scale['indexing_rate']:.1f} -> {large_scale['indexing_rate']:.1f} docs/s")
                
            except Exception as e:
                pytest.fail(f"Dataset size scaling test failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_query_complexity_scaling(self):
        """Test performance with different query complexities and k values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                config = {
                    'retriever_config': {
                        'vector_index': {'type': 'faiss', 'path': temp_dir},
                        'sparse': {'type': 'bm25'},
                        'fusion': {'type': 'rrf'},
                        'reranker': {'type': 'identity'}
                    },
                    'embedder_config': {
                        'type': 'sentence_transformer',
                        'config': {'model_name': 'all-MiniLM-L6-v2', 'device': 'cpu'}
                    }
                }
                
                service = RetrieverService(config=config)
                
                # Index documents
                documents = [
                    {
                        "content": f"Query complexity test document {i} containing various topics including machine learning, artificial intelligence, natural language processing, computer vision, robotics, and data science for comprehensive retrieval testing.",
                        "metadata": {"title": f"Complex Doc {i}", "topics": ["ml", "ai", "nlp", "cv", "robotics", "data_science"]},
                        "doc_id": f"complex_{i:03d}",
                        "source": f"complex_{i}.pdf"
                    }
                    for i in range(75)  # Moderate size for complexity testing
                ]
                
                await service.index_documents(documents)
                
                # Test different query complexities
                query_complexities = {
                    'simple': [
                        "machine learning",
                        "artificial intelligence",
                        "data science"
                    ],
                    'medium': [
                        "machine learning and artificial intelligence applications",
                        "natural language processing techniques for text analysis",
                        "computer vision algorithms for image recognition"
                    ],
                    'complex': [
                        "machine learning algorithms for natural language processing and computer vision applications in robotics",
                        "artificial intelligence systems combining deep learning with traditional data science methods",
                        "comprehensive analysis of machine learning, AI, NLP, computer vision, and robotics integration"
                    ]
                }
                
                # Test different k values
                k_values = [5, 10, 20, 50]
                
                complexity_results = {}
                
                for complexity, queries in query_complexities.items():
                    complexity_results[complexity] = {}
                    
                    for k in k_values:
                        times = []
                        
                        for query in queries:
                            start_time = time.time()
                            results = await service.retrieve_documents(query, k=k)
                            query_time = time.time() - start_time
                            times.append(query_time)
                            
                            # Hard fail: Individual query >60s
                            assert query_time < 60.0, f"Query time {query_time:.2f}s exceeds 60s limit"
                            
                            # Verify results
                            assert len(results) > 0, f"Should return results for {complexity} query with k={k}"
                            assert len(results) <= k, f"Should not return more than k={k} results"
                        
                        avg_time = statistics.mean(times)
                        complexity_results[complexity][k] = {
                            'avg_time': avg_time,
                            'times': times,
                            'queries_count': len(queries)
                        }
                        
                        print(f"{complexity:7s} k={k:2d}: {avg_time:.3f}s avg")
                
                # Quality assessments
                # Check that performance doesn't degrade too much with complexity
                simple_avg = complexity_results['simple'][10]['avg_time']  # k=10 as baseline
                complex_avg = complexity_results['complex'][10]['avg_time']
                
                complexity_overhead = (complex_avg - simple_avg) / simple_avg * 100
                
                # Quality flag: >200% overhead for complex queries is concerning
                if complexity_overhead > 200:
                    pytest.warns(UserWarning, f"Complex query overhead {complexity_overhead:.1f}% is high")
                
                # Check that performance doesn't degrade too much with k
                k_small = complexity_results['medium'][5]['avg_time']
                k_large = complexity_results['medium'][50]['avg_time']
                
                k_overhead = (k_large - k_small) / k_small * 100
                
                # Quality flag: >300% overhead for larger k is concerning  
                if k_overhead > 300:
                    pytest.warns(UserWarning, f"Large k overhead {k_overhead:.1f}% is high")
                
                print(f"\nQuery complexity scaling:")
                print(f"  Simple -> Complex: {simple_avg:.3f}s -> {complex_avg:.3f}s ({complexity_overhead:.1f}% overhead)")
                print(f"  k=5 -> k=50: {k_small:.3f}s -> {k_large:.3f}s ({k_overhead:.1f}% overhead)")
                
            except Exception as e:
                pytest.fail(f"Query complexity scaling test failed: {e}")


class TestRetrieverServiceResourceUsage:
    """Test resource usage characteristics and limits."""

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_memory_usage_profiling(self):
        """Test memory usage patterns during operations."""
        try:
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            with tempfile.TemporaryDirectory() as temp_dir:
                config = {
                    'retriever_config': {
                        'vector_index': {'type': 'faiss', 'path': temp_dir},
                        'sparse': {'type': 'bm25'},
                        'fusion': {'type': 'rrf'},
                        'reranker': {'type': 'identity'}
                    },
                    'embedder_config': {
                        'type': 'sentence_transformer',
                        'config': {'model_name': 'all-MiniLM-L6-v2', 'device': 'cpu'}
                    }
                }
                
                service = RetrieverService(config=config)
                
                # Measure memory during initialization
                await service._initialize_components()
                after_init_memory = process.memory_info().rss / 1024 / 1024
                
                # Measure memory during indexing
                documents = [
                    {
                        "content": f"Memory usage test document {i} with substantial content to measure realistic memory consumption patterns during indexing operations. This document is designed to be representative of typical document sizes.",
                        "metadata": {"title": f"Memory Doc {i}", "size": "large"},
                        "doc_id": f"memory_{i:03d}",
                        "source": f"memory_{i}.pdf"
                    }
                    for i in range(100)  # 100 docs for memory testing
                ]
                
                await service.index_documents(documents)
                after_indexing_memory = process.memory_info().rss / 1024 / 1024
                
                # Measure memory during heavy retrieval
                queries = [f"memory usage test document {i}" for i in range(50)]
                
                for query in queries:
                    await service.retrieve_documents(query, k=10)
                
                after_retrieval_memory = process.memory_info().rss / 1024 / 1024
                
                # Calculate memory increases
                init_increase = after_init_memory - initial_memory
                indexing_increase = after_indexing_memory - after_init_memory
                retrieval_increase = after_retrieval_memory - after_indexing_memory
                total_memory = after_retrieval_memory
                
                # Hard fail: >8GB total memory usage
                assert total_memory < 8000, f"Total memory usage {total_memory:.1f}MB exceeds 8GB limit"
                
                # Quality flags for memory usage
                if total_memory > 2000:  # 2GB
                    pytest.warns(UserWarning, f"High total memory usage: {total_memory:.1f}MB")
                
                if indexing_increase > 1000:  # 1GB increase during indexing
                    pytest.warns(UserWarning, f"High indexing memory increase: {indexing_increase:.1f}MB")
                
                if retrieval_increase > 500:  # 500MB increase during retrieval
                    pytest.warns(UserWarning, f"High retrieval memory increase: {retrieval_increase:.1f}MB")
                
                # Test for memory leaks (simplified)
                memory_before_gc = process.memory_info().rss / 1024 / 1024
                
                # Force cleanup
                await service.shutdown()
                service = None
                
                # Give some time for cleanup
                await asyncio.sleep(1)
                
                memory_after_gc = process.memory_info().rss / 1024 / 1024
                memory_freed = memory_before_gc - memory_after_gc
                
                print(f"Memory usage profiling:")
                print(f"  Initial: {initial_memory:.1f}MB")
                print(f"  After init: {after_init_memory:.1f}MB (+{init_increase:.1f}MB)")
                print(f"  After indexing: {after_indexing_memory:.1f}MB (+{indexing_increase:.1f}MB)")
                print(f"  After retrieval: {after_retrieval_memory:.1f}MB (+{retrieval_increase:.1f}MB)")
                print(f"  After cleanup: {memory_after_gc:.1f}MB (freed {memory_freed:.1f}MB)")
                
        except Exception as e:
            pytest.fail(f"Memory usage profiling test failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_cpu_usage_patterns(self):
        """Test CPU usage during different operations."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                config = {
                    'retriever_config': {
                        'vector_index': {'type': 'faiss', 'path': temp_dir},
                        'sparse': {'type': 'bm25'},
                        'fusion': {'type': 'rrf'},
                        'reranker': {'type': 'identity'}
                    },
                    'embedder_config': {
                        'type': 'sentence_transformer',
                        'config': {'model_name': 'all-MiniLM-L6-v2', 'device': 'cpu'}
                    }
                }
                
                service = RetrieverService(config=config)
                
                # Monitor CPU during initialization
                start_cpu_times = psutil.Process().cpu_times()
                await service._initialize_components()
                init_cpu_times = psutil.Process().cpu_times()
                
                # Monitor CPU during indexing
                documents = [
                    {
                        "content": f"CPU usage test document {i} containing computational content for measuring CPU utilization patterns during various retrieval operations and indexing processes.",
                        "metadata": {"title": f"CPU Doc {i}"},
                        "doc_id": f"cpu_{i:03d}",
                        "source": f"cpu_{i}.pdf"
                    }
                    for i in range(50)
                ]
                
                start_time = time.time()
                await service.index_documents(documents)
                indexing_duration = time.time() - start_time
                indexing_cpu_times = psutil.Process().cpu_times()
                
                # Monitor CPU during retrieval
                queries = ["CPU usage test document computational"] * 20
                
                start_time = time.time()
                for query in queries:
                    await service.retrieve_documents(query, k=10)
                retrieval_duration = time.time() - start_time
                retrieval_cpu_times = psutil.Process().cpu_times()
                
                # Calculate CPU usage
                init_cpu_usage = (init_cpu_times.user - start_cpu_times.user) / 1.0  # Rough estimate
                indexing_cpu_usage = (indexing_cpu_times.user - init_cpu_times.user) / indexing_duration
                retrieval_cpu_usage = (retrieval_cpu_times.user - indexing_cpu_times.user) / retrieval_duration
                
                # Quality assessments (very rough, as CPU measurement is tricky)
                print(f"CPU usage patterns:")
                print(f"  Initialization: ~{init_cpu_usage:.2f}s CPU time")
                print(f"  Indexing: ~{indexing_cpu_usage:.2f} CPU ratio during {indexing_duration:.1f}s")
                print(f"  Retrieval: ~{retrieval_cpu_usage:.2f} CPU ratio during {retrieval_duration:.1f}s")
                
        except Exception as e:
            # CPU monitoring can be flaky, so warn but don't fail
            pytest.warns(UserWarning, f"CPU usage monitoring failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_disk_usage_patterns(self):
        """Test disk usage for index storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                config = {
                    'retriever_config': {
                        'vector_index': {'type': 'faiss', 'path': temp_dir},
                        'sparse': {'type': 'bm25'},
                        'fusion': {'type': 'rrf'},
                        'reranker': {'type': 'identity'}
                    },
                    'embedder_config': {
                        'type': 'sentence_transformer',
                        'config': {'model_name': 'all-MiniLM-L6-v2', 'device': 'cpu'}
                    }
                }
                
                service = RetrieverService(config=config)
                
                # Measure initial disk usage
                initial_size = sum(f.stat().st_size for f in Path(temp_dir).rglob('*') if f.is_file()) / 1024 / 1024  # MB
                
                # Index documents and measure disk growth
                document_sizes = [10, 25, 50, 100]
                disk_usage_results = {}
                
                for size in document_sizes:
                    documents = [
                        {
                            "content": f"Disk usage test document {i} with content designed to measure index storage requirements. This document has substantial text to represent realistic disk usage patterns for vector and sparse indices in retrieval systems.",
                            "metadata": {"title": f"Disk Doc {i}", "set": size},
                            "doc_id": f"disk_{size}_{i:04d}",
                            "source": f"disk_{size}_{i}.pdf"
                        }
                        for i in range(size)
                    ]
                    
                    await service.index_documents(documents)
                    
                    # Measure disk usage
                    current_size = sum(f.stat().st_size for f in Path(temp_dir).rglob('*') if f.is_file()) / 1024 / 1024
                    size_increase = current_size - initial_size
                    
                    disk_usage_results[size] = {
                        'total_size_mb': current_size,
                        'size_increase_mb': size_increase,
                        'mb_per_document': size_increase / size if size > 0 else 0
                    }
                    
                    print(f"Documents: {size:3d}, Disk: {current_size:.1f}MB (+{size_increase:.1f}MB, {disk_usage_results[size]['mb_per_document']:.3f}MB/doc)")
                
                # Quality assessments
                largest_set = max(document_sizes)
                mb_per_doc = disk_usage_results[largest_set]['mb_per_document']
                
                # Quality flag: >10MB per document seems excessive for index storage
                if mb_per_doc > 10.0:
                    pytest.warns(UserWarning, f"High disk usage: {mb_per_doc:.3f}MB per document")
                
                # Check disk usage scaling
                small_usage = disk_usage_results[min(document_sizes)]['mb_per_document']
                large_usage = disk_usage_results[max(document_sizes)]['mb_per_document']
                
                # Should be relatively linear (efficient index growth)
                scaling_ratio = large_usage / small_usage if small_usage > 0 else 1
                if scaling_ratio > 2.0:
                    pytest.warns(UserWarning, f"Non-linear disk usage scaling: {scaling_ratio:.1f}x")
                
                print(f"\nDisk usage analysis:")
                print(f"  Final size: {disk_usage_results[largest_set]['total_size_mb']:.1f}MB")
                print(f"  Usage per doc: {mb_per_doc:.3f}MB")
                print(f"  Scaling ratio: {scaling_ratio:.1f}x")
                
            except Exception as e:
                pytest.fail(f"Disk usage patterns test failed: {e}")


class TestRetrieverServiceStressTest:
    """Stress testing and edge case performance."""

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_sustained_load_performance(self):
        """Test performance under sustained load over time."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                config = {
                    'retriever_config': {
                        'vector_index': {'type': 'faiss', 'path': temp_dir},
                        'sparse': {'type': 'bm25'},
                        'fusion': {'type': 'rrf'},
                        'reranker': {'type': 'identity'}
                    },
                    'embedder_config': {
                        'type': 'sentence_transformer',
                        'config': {'model_name': 'all-MiniLM-L6-v2', 'device': 'cpu'}
                    }
                }
                
                service = RetrieverService(config=config)
                
                # Index moderate dataset
                documents = [
                    {
                        "content": f"Sustained load test document {i} designed for long-running performance evaluation. This content includes various keywords and topics to ensure diverse query responses during extended testing periods.",
                        "metadata": {"title": f"Load Doc {i}", "batch": i//10},
                        "doc_id": f"load_{i:04d}",
                        "source": f"load_{i}.pdf"
                    }
                    for i in range(150)  # Moderate size for sustained testing
                ]
                
                await service.index_documents(documents)
                
                # Run sustained load test
                queries = [
                    "sustained load test document",
                    "performance evaluation keywords",
                    "diverse query responses",
                    "extended testing periods",
                    "long-running performance"
                ]
                
                # Test for several minutes with continuous load
                test_duration = 60  # 60 seconds of sustained load
                query_count = 0
                successful_queries = 0
                response_times = []
                
                start_test_time = time.time()
                
                while time.time() - start_test_time < test_duration:
                    query = queries[query_count % len(queries)]
                    
                    start_query_time = time.time()
                    try:
                        results = await service.retrieve_documents(query, k=5)
                        query_time = time.time() - start_query_time
                        
                        # Hard fail: Individual query >60s even under load
                        assert query_time < 60.0, f"Query under load took {query_time:.2f}s"
                        
                        if len(results) > 0:
                            successful_queries += 1
                            response_times.append(query_time)
                        
                    except Exception as e:
                        pytest.warns(UserWarning, f"Query failed under sustained load: {e}")
                    
                    query_count += 1
                    
                    # Small delay to prevent overwhelming
                    await asyncio.sleep(0.1)
                
                total_test_time = time.time() - start_test_time
                success_rate = successful_queries / query_count
                avg_response_time = statistics.mean(response_times) if response_times else 0
                throughput = query_count / total_test_time
                
                # Hard fail: <50% success rate under load indicates serious issues
                assert success_rate >= 0.5, f"Sustained load success rate {success_rate:.2%} too low"
                
                # Quality flags
                if success_rate < 0.9:
                    pytest.warns(UserWarning, f"Sustained load success rate {success_rate:.2%} below 90%")
                
                if avg_response_time > 2.0:
                    pytest.warns(UserWarning, f"High response time under load: {avg_response_time:.3f}s")
                
                if throughput < 5.0:
                    pytest.warns(UserWarning, f"Low throughput under sustained load: {throughput:.1f} q/s")
                
                print(f"Sustained load test results:")
                print(f"  Duration: {total_test_time:.1f}s")
                print(f"  Queries: {query_count} total, {successful_queries} successful")
                print(f"  Success rate: {success_rate:.1%}")
                print(f"  Avg response time: {avg_response_time:.3f}s")
                print(f"  Throughput: {throughput:.1f} queries/sec")
                
            except Exception as e:
                pytest.fail(f"Sustained load performance test failed: {e}")

    # Service availability handled by fixtures
    @pytest.mark.asyncio
    async def test_edge_case_performance(self):
        """Test performance with edge cases like very long queries, large k values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                config = {
                    'retriever_config': {
                        'vector_index': {'type': 'faiss', 'path': temp_dir},
                        'sparse': {'type': 'bm25'},
                        'fusion': {'type': 'rrf'},
                        'reranker': {'type': 'identity'}
                    },
                    'embedder_config': {
                        'type': 'sentence_transformer',
                        'config': {'model_name': 'all-MiniLM-L6-v2', 'device': 'cpu'}
                    }
                }
                
                service = RetrieverService(config=config)
                
                # Index documents
                documents = [
                    {
                        "content": f"Edge case performance test document {i} with comprehensive content covering multiple topics including machine learning, artificial intelligence, data science, natural language processing, and computer vision for testing retrieval performance with various query patterns.",
                        "metadata": {"title": f"Edge Doc {i}"},
                        "doc_id": f"edge_{i:03d}",
                        "source": f"edge_{i}.pdf"
                    }
                    for i in range(100)
                ]
                
                await service.index_documents(documents)
                
                # Test edge cases
                edge_cases = [
                    {
                        "name": "Very long query",
                        "query": "edge case performance test document with comprehensive content covering multiple topics including machine learning artificial intelligence data science natural language processing computer vision testing retrieval performance various query patterns " * 10,
                        "k": 10
                    },
                    {
                        "name": "Very short query",
                        "query": "AI",
                        "k": 10
                    },
                    {
                        "name": "Large k value",
                        "query": "performance test document",
                        "k": 95  # Nearly all documents
                    },
                    {
                        "name": "Repetitive query",
                        "query": "test test test test test document document document",
                        "k": 10
                    },
                    {
                        "name": "Special characters",
                        "query": "test-document with_special & symbols (performance) [testing]",
                        "k": 10
                    }
                ]
                
                edge_case_results = {}
                
                for case in edge_cases:
                    try:
                        start_time = time.time()
                        results = await service.retrieve_documents(case["query"], k=case["k"])
                        response_time = time.time() - start_time
                        
                        # Hard fail: Even edge cases shouldn't take >60s
                        assert response_time < 60.0, f"{case['name']} took {response_time:.2f}s"
                        
                        edge_case_results[case["name"]] = {
                            'response_time': response_time,
                            'result_count': len(results),
                            'successful': True
                        }
                        
                        # Quality flag: Edge cases taking >10s might indicate issues
                        if response_time > 10.0:
                            pytest.warns(UserWarning, f"{case['name']} slow: {response_time:.2f}s")
                        
                        print(f"{case['name']:20s}: {response_time:.3f}s, {len(results)} results")
                        
                    except Exception as e:
                        edge_case_results[case["name"]] = {
                            'response_time': None,
                            'result_count': 0,
                            'successful': False,
                            'error': str(e)
                        }
                        
                        # Edge case failures might be acceptable, but log them
                        pytest.warns(UserWarning, f"{case['name']} failed: {e}")
                
                # Quality assessment
                successful_cases = sum(1 for result in edge_case_results.values() if result['successful'])
                success_rate = successful_cases / len(edge_cases)
                
                # Quality flag: <80% success rate on edge cases indicates robustness issues
                if success_rate < 0.8:
                    pytest.warns(UserWarning, f"Edge case success rate {success_rate:.1%} below 80%")
                
                print(f"\nEdge case performance summary:")
                print(f"  Success rate: {success_rate:.1%} ({successful_cases}/{len(edge_cases)})")
                
            except Exception as e:
                pytest.fail(f"Edge case performance test failed: {e}")


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([__file__ + "::TestRetrieverServiceBasicPerformance::test_single_query_latency", "-v"])