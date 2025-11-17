#!/usr/bin/env python3
"""
Agent 6: Data Pipeline & Index Quality Verification
Comprehensive empirical verification of claimed index status.
"""

import os
import json
from pathlib import Path
from datetime import datetime

def verify_index_quality():
    """Verify all claims about the data pipeline and indices."""

    results = {
        "timestamp": datetime.now().isoformat(),
        "agent": "Agent 6: Data Pipeline & Index Quality",
        "status": "FAIL",
        "score": 0,
        "checks": {}
    }

    project_root = Path("/home/user/rag-portfolio/project-1-technical-rag")

    # Check 1: Index directory exists
    indices_dir = project_root / "data" / "indices"
    check1 = {
        "name": "Index directory exists",
        "claimed": "data/indices/ with 3 files (FAISS, documents, metadata)",
        "actual": f"Directory exists: {indices_dir.exists()}",
        "status": "PASS" if indices_dir.exists() else "FAIL"
    }
    results["checks"]["index_directory"] = check1

    # Check 2: FAISS index file
    faiss_file = indices_dir / "faiss_index.bin"
    if faiss_file.exists():
        size_mb = faiss_file.stat().st_size / 1024 / 1024
        check2 = {
            "name": "FAISS index file",
            "claimed": "3.72 MB faiss_index.bin with 2,538 vectors",
            "actual": f"{size_mb:.2f} MB file exists",
            "status": "PASS" if abs(size_mb - 3.72) < 0.5 else "WARN"
        }
    else:
        check2 = {
            "name": "FAISS index file",
            "claimed": "3.72 MB faiss_index.bin with 2,538 vectors",
            "actual": "File does NOT exist",
            "status": "FAIL"
        }
    results["checks"]["faiss_index"] = check2

    # Check 3: Documents file
    docs_file = indices_dir / "documents.pkl"
    if docs_file.exists():
        size_mb = docs_file.stat().st_size / 1024 / 1024
        check3 = {
            "name": "Documents file",
            "claimed": "12.69 MB documents.pkl with 2,538 chunks",
            "actual": f"{size_mb:.2f} MB file exists",
            "status": "PASS" if abs(size_mb - 12.69) < 1.0 else "WARN"
        }
    else:
        check3 = {
            "name": "Documents file",
            "claimed": "12.69 MB documents.pkl with 2,538 chunks",
            "actual": "File does NOT exist",
            "status": "FAIL"
        }
    results["checks"]["documents_file"] = check3

    # Check 4: Metadata file
    meta_file = indices_dir / "index_metadata.json"
    if meta_file.exists():
        with open(meta_file, 'r') as f:
            metadata = json.load(f)
        check4 = {
            "name": "Index metadata",
            "claimed": "2,538 vectors, 384 dimensions",
            "actual": f"{metadata.get('num_vectors', 'N/A')} vectors, {metadata.get('dimension', 'N/A')} dims",
            "status": "PASS" if metadata.get('num_vectors') == 2538 else "WARN"
        }
    else:
        check4 = {
            "name": "Index metadata",
            "claimed": "2,538 vectors, 384 dimensions",
            "actual": "File does NOT exist",
            "status": "FAIL"
        }
    results["checks"]["metadata_file"] = check4

    # Check 5: Source PDF count
    pdf_dir = project_root / "data" / "test"
    pdf_files = list(pdf_dir.glob("*.pdf"))
    check5 = {
        "name": "Source PDF files",
        "claimed": "34 technical PDFs processed",
        "actual": f"{len(pdf_files)} PDF files found in data/test/",
        "status": "PASS" if len(pdf_files) == 34 else "WARN"
    }
    results["checks"]["source_pdfs"] = check5

    # Check 6: Any index files anywhere
    all_pkl = list(project_root.glob("data/**/*.pkl"))
    all_faiss = list(project_root.glob("data/**/*.faiss")) + list(project_root.glob("data/**/*.bin"))
    check6 = {
        "name": "Index files search (recursive)",
        "claimed": "Index files should exist in data/indices/",
        "actual": f"Found {len(all_pkl)} .pkl files, {len(all_faiss)} FAISS/bin files in data/",
        "status": "PASS" if (len(all_pkl) > 0 or len(all_faiss) > 0) else "FAIL"
    }
    results["checks"]["recursive_search"] = check6

    # Calculate overall status
    failures = sum(1 for c in results["checks"].values() if c["status"] == "FAIL")
    warnings = sum(1 for c in results["checks"].values() if c["status"] == "WARN")
    passes = sum(1 for c in results["checks"].values() if c["status"] == "PASS")

    total_checks = failures + warnings + passes
    if failures == 0 and warnings == 0:
        results["status"] = "PASS"
        results["score"] = 100
    elif failures == 0:
        results["status"] = "WARN"
        results["score"] = 70
    else:
        results["status"] = "FAIL"
        results["score"] = max(0, int((passes / total_checks) * 100) - (failures * 20))

    # Critical findings
    results["critical_findings"] = []

    if not indices_dir.exists():
        results["critical_findings"].append(
            "CRITICAL: data/indices/ directory does not exist - pipeline was never executed"
        )

    if not faiss_file.exists():
        results["critical_findings"].append(
            "CRITICAL: FAISS index file missing - no vector search capability"
        )

    if not docs_file.exists():
        results["critical_findings"].append(
            "CRITICAL: Documents file missing - no document retrieval capability"
        )

    if len(pdf_files) != 34:
        results["critical_findings"].append(
            f"WARNING: PDF count mismatch - claimed 34, found {len(pdf_files)}"
        )

    if len(all_pkl) == 0 and len(all_faiss) == 0:
        results["critical_findings"].append(
            "CRITICAL: No index files found anywhere in data/ directory"
        )

    return results

if __name__ == "__main__":
    results = verify_index_quality()

    # Print formatted report
    print("=" * 80)
    print(f"STATUS: {'✅' if results['status'] == 'PASS' else '⚠️' if results['status'] == 'WARN' else '❌'} {results['status']}")
    print(f"SCORE: {results['score']}/100")
    print("=" * 80)
    print()

    print("KEY FINDINGS:")
    for check_name, check in results["checks"].items():
        status_icon = "✅" if check["status"] == "PASS" else "⚠️" if check["status"] == "WARN" else "❌"
        print(f"{status_icon} {check['name']}:")
        print(f"   Claimed: {check['claimed']}")
        print(f"   Actual:  {check['actual']}")
        print()

    print("=" * 80)
    print("CRITICAL ISSUES:")
    if results["critical_findings"]:
        for i, finding in enumerate(results["critical_findings"], 1):
            print(f"{i}. {finding}")
    else:
        print("None found")
    print("=" * 80)

    # Save results
    output_file = Path("/home/user/rag-portfolio/project-1-technical-rag/agent6_verification_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")
