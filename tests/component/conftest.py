"""
Pytest configuration for component tests.
"""

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def project_root():
    """Provide project root path for all tests."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def component_test_data():
    """Provide common test data for component tests."""
    return {
        'sample_text': 'This is sample text for component testing.',
        'sample_embeddings': [0.1, 0.2, 0.3, 0.4, 0.5],
        'sample_documents': [
            {'content': 'Component test document', 'metadata': {'source': 'comp_test.txt'}},
        ],
        'test_configurations': {
            'embedder': {
                'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
                'device': 'cpu'
            },
            'retriever': {
                'similarity_top_k': 5,
                'fusion_method': 'rrf'
            },
            'generator': {
                'model': 'llama3.2:3b',
                'temperature': 0.1
            }
        }
    }
