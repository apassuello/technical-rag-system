#!/usr/bin/env python3
"""
Document Collection Manager

Interactive tool for managing and scaling the RAG system's knowledge base
with multiple document collections for different domains/topics.
"""

import sys
from pathlib import Path
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from src.batch_document_processor import BatchDocumentProcessor, process_documents_from_directory
from src.rag_with_generation import RAGWithGeneration


class DocumentCollectionManager:
    """
    Manages multiple document collections for scaled knowledge base.
    
    Supports different document categories (technical specs, guidelines, etc.)
    with efficient processing and organization.
    """
    
    def __init__(self):
        self.rag_system = RAGWithGeneration()
        self.collections: Dict[str, Dict[str, Any]] = {}
        self.collection_metadata_file = "document_collections.json"
        
        # Load existing collections if available
        self._load_collection_metadata()
    
    def _load_collection_metadata(self):
        """Load existing collection metadata."""
        metadata_path = Path(self.collection_metadata_file)
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    self.collections = json.load(f)
                print(f"📁 Loaded {len(self.collections)} existing collections")
            except Exception as e:
                print(f"⚠️ Failed to load collection metadata: {e}")
    
    def _save_collection_metadata(self):
        """Save collection metadata to file."""
        try:
            with open(self.collection_metadata_file, 'w') as f:
                json.dump(self.collections, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Failed to save collection metadata: {e}")
    
    def add_document_collection(
        self,
        collection_name: str,
        directory_path: str,
        description: str = "",
        file_patterns: List[str] = ["*.pdf"],
        max_workers: int = 4
    ) -> bool:
        """
        Add a new document collection to the knowledge base.
        
        Args:
            collection_name: Unique name for the collection
            directory_path: Path to directory containing documents
            description: Human-readable description
            file_patterns: File patterns to match
            max_workers: Parallel processing workers
            
        Returns:
            True if successful, False otherwise
        """
        if collection_name in self.collections:
            print(f"❌ Collection '{collection_name}' already exists")
            return False
        
        directory = Path(directory_path)
        if not directory.exists():
            print(f"❌ Directory not found: {directory_path}")
            return False
        
        print(f"\n🔄 Processing collection: {collection_name}")
        print(f"   📁 Directory: {directory_path}")
        print(f"   📝 Description: {description}")
        
        try:
            # Find documents
            document_paths = []
            for pattern in file_patterns:
                document_paths.extend(directory.glob(pattern))
            
            if not document_paths:
                print(f"❌ No documents found matching {file_patterns}")
                return False
            
            print(f"   📄 Found {len(document_paths)} documents")
            
            # Process documents
            processor = BatchDocumentProcessor(
                rag_system=self.rag_system,
                max_workers=max_workers
            )
            
            def progress_callback(completed, total):
                print(f"   Progress: {completed}/{total} documents ({completed/total*100:.1f}%)")
            
            start_time = time.time()
            stats = processor.process_document_collection(
                document_paths,
                parallel=True,
                progress_callback=progress_callback
            )
            
            # Record collection metadata
            self.collections[collection_name] = {
                "description": description,
                "directory_path": str(directory),
                "file_patterns": file_patterns,
                "documents_processed": stats.successful_documents,
                "documents_failed": stats.failed_documents,
                "total_chunks": stats.total_chunks,
                "processing_time": stats.total_processing_time,
                "added_at": datetime.now().isoformat(),
                "document_list": [p.name for p in document_paths],
                "successful_documents": [r.filename for r in processor.processing_results if r.success],
                "failed_documents": [
                    {"filename": r.filename, "error": r.error_message}
                    for r in processor.processing_results if not r.success
                ]
            }
            
            self._save_collection_metadata()
            
            print(f"✅ Collection '{collection_name}' added successfully!")
            print(f"   📊 Documents: {stats.successful_documents}/{stats.total_documents}")
            print(f"   📚 Chunks: {stats.total_chunks}")
            print(f"   ⏱️ Time: {stats.total_processing_time:.1f}s")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to process collection '{collection_name}': {e}")
            return False
    
    def list_collections(self):
        """Display all document collections."""
        if not self.collections:
            print("📂 No document collections found")
            return
        
        print(f"\n📚 Document Collections ({len(self.collections)} total)")
        print("=" * 60)
        
        total_documents = 0
        total_chunks = 0
        
        for name, metadata in self.collections.items():
            print(f"\n📁 {name}")
            print(f"   📝 {metadata.get('description', 'No description')}")
            print(f"   📄 Documents: {metadata['documents_processed']} successful, {metadata['documents_failed']} failed")
            print(f"   📚 Chunks: {metadata['total_chunks']}")
            print(f"   ⏱️ Processing time: {metadata['processing_time']:.1f}s")
            print(f"   📅 Added: {metadata['added_at'][:10]}")
            
            if metadata['failed_documents']:
                print(f"   ❌ Failed: {[d['filename'] for d in metadata['failed_documents']]}")
            
            total_documents += metadata['documents_processed']
            total_chunks += metadata['total_chunks']
        
        print(f"\n📊 Total across all collections:")
        print(f"   📄 Documents: {total_documents}")
        print(f"   📚 Chunks: {total_chunks}")
        print(f"   🧠 Current system chunks: {len(self.rag_system.chunks)}")
    
    def get_collection_details(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific collection."""
        if collection_name not in self.collections:
            print(f"❌ Collection '{collection_name}' not found")
            return None
        
        return self.collections[collection_name]
    
    def test_knowledge_coverage(self, test_queries: List[str]) -> Dict[str, Any]:
        """
        Test the expanded knowledge base with various queries.
        
        Args:
            test_queries: List of test questions
            
        Returns:
            Dictionary with test results
        """
        print(f"\n🧪 Testing knowledge coverage with {len(test_queries)} queries")
        print("=" * 60)
        
        results = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: {query}")
            
            try:
                start_time = time.time()
                result = self.rag_system.query_with_answer(
                    question=query,
                    top_k=5,
                    use_hybrid=True,
                    return_context=True
                )
                query_time = time.time() - start_time
                
                # Get unique sources
                sources = set(c['source'] for c in result['citations'])
                
                print(f"   ✅ Confidence: {result['confidence']:.1%}")
                print(f"   📚 Citations: {len(result['citations'])}")
                print(f"   📄 Sources: {len(sources)} - {list(sources)[:3]}{'...' if len(sources) > 3 else ''}")
                print(f"   ⏱️ Time: {query_time:.2f}s")
                
                results.append({
                    "query": query,
                    "confidence": result['confidence'],
                    "citations_count": len(result['citations']),
                    "unique_sources": len(sources),
                    "sources": list(sources),
                    "query_time": query_time,
                    "answer_preview": result['answer'][:100] + "..." if len(result['answer']) > 100 else result['answer']
                })
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({
                    "query": query,
                    "error": str(e)
                })
        
        # Calculate summary statistics
        successful_queries = [r for r in results if 'error' not in r]
        
        summary = {
            "total_queries": len(test_queries),
            "successful_queries": len(successful_queries),
            "avg_confidence": sum(r['confidence'] for r in successful_queries) / len(successful_queries) if successful_queries else 0,
            "avg_citations": sum(r['citations_count'] for r in successful_queries) / len(successful_queries) if successful_queries else 0,
            "avg_query_time": sum(r['query_time'] for r in successful_queries) / len(successful_queries) if successful_queries else 0,
            "unique_sources_used": len(set(source for r in successful_queries for source in r.get('sources', []))),
            "high_confidence_queries": len([r for r in successful_queries if r['confidence'] >= 0.7]),
            "results": results
        }
        
        print(f"\n📊 Knowledge Coverage Test Results:")
        print(f"   ✅ Successful queries: {summary['successful_queries']}/{summary['total_queries']}")
        print(f"   🎯 Average confidence: {summary['avg_confidence']:.1%}")
        print(f"   📚 Average citations: {summary['avg_citations']:.1f}")
        print(f"   📄 Unique sources used: {summary['unique_sources_used']}")
        print(f"   🔥 High confidence (≥70%): {summary['high_confidence_queries']}")
        print(f"   ⏱️ Average query time: {summary['avg_query_time']:.2f}s")
        
        return summary
    
    def export_collection_report(self, output_file: str = "collection_report.json"):
        """Export comprehensive report of all collections."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_collections": len(self.collections),
            "collections": self.collections,
            "system_stats": {
                "total_chunks": len(self.rag_system.chunks),
                "memory_estimate_mb": len(self.rag_system.chunks) * 2  # Rough estimate
            },
            "summary": {
                "total_documents": sum(c['documents_processed'] for c in self.collections.values()),
                "total_chunks": sum(c['total_chunks'] for c in self.collections.values()),
                "total_processing_time": sum(c['processing_time'] for c in self.collections.values())
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📋 Collection report exported to: {output_file}")


def main():
    """Interactive document collection management."""
    manager = DocumentCollectionManager()
    
    print("🚀 Document Collection Manager")
    print("=" * 50)
    
    # Pre-defined test collections (modify as needed)
    test_collections = [
        {
            "name": "technical_specs",
            "directory": "data/test",
            "description": "Technical specifications and standards",
            "patterns": ["*.pdf"]
        }
    ]
    
    # Add test collection
    for collection in test_collections:
        if Path(collection["directory"]).exists():
            print(f"\n📁 Adding collection: {collection['name']}")
            manager.add_document_collection(
                collection_name=collection["name"],
                directory_path=collection["directory"],
                description=collection["description"],
                file_patterns=collection["patterns"],
                max_workers=2  # Conservative for testing
            )
    
    # List collections
    manager.list_collections()
    
    # Test knowledge coverage
    test_queries = [
        "What is RISC-V and what are its main principles?",
        "How does RISC-V determine instruction length?",
        "What are the requirements for software validation?",
        "What are the main principles of medical device software development?",
        "How should AI/ML systems be validated in medical devices?"
    ]
    
    coverage_results = manager.test_knowledge_coverage(test_queries)
    
    # Export report
    manager.export_collection_report("document_collection_report.json")
    
    print(f"\n✅ Document collection management completed!")
    print(f"   📚 Total knowledge base: {len(manager.rag_system.chunks)} chunks")
    print(f"   📊 Collections: {len(manager.collections)}")
    print(f"   🎯 Test coverage: {coverage_results['avg_confidence']:.1%} avg confidence")


if __name__ == "__main__":
    main()