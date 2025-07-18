#!/usr/bin/env python3
"""
RISC-V Documentation Collector

Automated tool to collect comprehensive RISC-V technical documentation
for Epic 2 demo corpus. Systematically downloads and organizes documents
from official sources, academic repositories, and implementation guides.

Usage:
    python tools/collect_riscv_docs.py --phase 1  # Core specifications
    python tools/collect_riscv_docs.py --phase 2  # Implementation guides
    python tools/collect_riscv_docs.py --phase 3  # Academic papers
    python tools/collect_riscv_docs.py --all      # Complete collection
"""

import os
import sys
import requests
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import urllib.parse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    import arxiv

    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False


class RISCVDocCollector:
    """Automated RISC-V documentation collector for Epic 2 demo corpus."""

    def __init__(self, base_dir: str = "data/riscv_comprehensive_corpus"):
        """Initialize collector with organized directory structure."""
        self.base_dir = Path(base_dir)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

        # Collection statistics
        self.stats = {"downloaded": 0, "skipped": 0, "failed": 0, "total_size_mb": 0.0}

        # Downloaded file tracking
        self.download_log = []

        self.create_directory_structure()
        self.load_existing_log()

    def create_directory_structure(self):
        """Create organized directory structure for corpus."""
        dirs = [
            "core-specs/official",
            "core-specs/extensions",
            "core-specs/standards",
            "implementation/processors",
            "implementation/toolchain",
            "implementation/os-ports",
            "implementation/hardware",
            "research/papers/performance-analysis",
            "research/papers/security-studies",
            "research/papers/architecture-studies",
            "research/papers/benchmarking",
            "research/workshops",
            "research/theses",
            "reference/quick-refs",
            "reference/tutorials",
            "reference/examples",
            "metadata",
        ]

        for dir_path in dirs:
            (self.base_dir / dir_path).mkdir(parents=True, exist_ok=True)

        print(f"📁 Directory structure created in: {self.base_dir}")

    def load_existing_log(self):
        """Load existing download log to avoid duplicates."""
        log_file = self.base_dir / "metadata" / "download-log.json"
        if log_file.exists():
            with open(log_file, "r") as f:
                log_data = json.load(f)
                # Recursively find the downloads list in any nested structure
                downloads = self._extract_downloads_list(log_data)
                self.download_log = downloads if downloads else []
            print(f"📋 Loaded existing log with {len(self.download_log)} entries")

    def _extract_downloads_list(self, data):
        """Recursively extract downloads list from nested structure."""
        if isinstance(data, list):
            # Check if this looks like a downloads list (contains dicts with url keys)
            if data and isinstance(data[0], dict) and "url" in data[0]:
                return data
        elif isinstance(data, dict):
            # Look for downloads key
            if "downloads" in data:
                result = self._extract_downloads_list(data["downloads"])
                if result:
                    return result
            # If no downloads key, search all values
            for value in data.values():
                result = self._extract_downloads_list(value)
                if result:
                    return result
        return None

    def save_download_log(self):
        """Save download log with metadata."""
        log_file = self.base_dir / "metadata" / "download-log.json"
        log_data = {
            "collection_date": datetime.now().isoformat(),
            "statistics": self.stats,
            "downloads": self.download_log,
        }

        with open(log_file, "w") as f:
            json.dump(log_data, f, indent=2)

        print(f"💾 Download log saved: {len(self.download_log)} entries")

    def download_pdf(
        self, url: str, local_path: str, title: str = "", force: bool = False
    ):
        """Download PDF with comprehensive error handling and deduplication."""
        full_path = self.base_dir / local_path

        # Check if already downloaded
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if not force:
            for entry in self.download_log:
                if (
                    entry.get("url_hash") == url_hash
                    and Path(entry.get("local_path", "")).exists()
                ):
                    print(f"⏭️  Skipped (exists): {title or local_path}")
                    self.stats["skipped"] += 1
                    return True

        try:
            print(f"⬇️  Downloading: {title or local_path}")

            # Create directory if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Download with streaming
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("content-type", "").lower()
            if (
                "pdf" not in content_type
                and "application/octet-stream" not in content_type
            ):
                print(f"⚠️  Warning: Unexpected content type: {content_type}")

            # Write file
            total_size = 0
            with open(full_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)

            size_mb = total_size / (1024 * 1024)

            # Log successful download
            download_entry = {
                "url": url,
                "url_hash": url_hash,
                "local_path": str(full_path),
                "title": title,
                "size_mb": round(size_mb, 2),
                "download_date": datetime.now().isoformat(),
                "status": "success",
            }

            self.download_log.append(download_entry)
            self.stats["downloaded"] += 1
            self.stats["total_size_mb"] += size_mb

            print(f"✅ Downloaded: {title or local_path} ({size_mb:.1f}MB)")

            # Be respectful to servers
            time.sleep(1)
            return True

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to download {url}: {str(e)}"
            print(f"❌ {error_msg}")

            # Log failed download
            self.download_log.append(
                {
                    "url": url,
                    "url_hash": url_hash,
                    "local_path": str(full_path),
                    "title": title,
                    "error": error_msg,
                    "download_date": datetime.now().isoformat(),
                    "status": "failed",
                }
            )

            self.stats["failed"] += 1
            return False

        except Exception as e:
            error_msg = f"Unexpected error downloading {url}: {str(e)}"
            print(f"❌ {error_msg}")
            self.stats["failed"] += 1
            return False

    def collect_official_specs(self):
        """Collect official RISC-V Foundation specifications."""
        print("\n📚 Phase 1: Collecting Official RISC-V Specifications")
        print("=" * 60)

        # Official RISC-V Foundation documents (Updated URLs for 2025)
        official_docs = {
            # Core specifications - Current versions from official RISC-V wiki
            "riscv-spec-unprivileged-v20250508": {
                "url": "https://drive.google.com/uc?export=download&id=1uviu1nH-tScFfgrovvFCrj7Omv8tFtkp",
                "path": "core-specs/official/riscv-spec-unprivileged-v20250508.pdf",
                "title": "RISC-V Instruction Set Manual Volume I: Unprivileged ISA (May 2025)",
            },
            "riscv-spec-privileged-v20250508": {
                "url": "https://drive.google.com/uc?export=download&id=17GeetSnT5wW3xNuAHI95-SI1gPGd5sJ_",
                "path": "core-specs/official/riscv-spec-privileged-v20250508.pdf",
                "title": "RISC-V Instruction Set Manual Volume II: Privileged Architecture (May 2025)",
            },
            # Non-ISA specifications from current RISC-V wiki
            "riscv-abis-specification": {
                "url": "https://drive.google.com/uc?export=download&id=1Ja_Tpp_5Me583CGVD-BIZMlgGBnlKU4R",
                "path": "core-specs/standards/riscv-abis-specification.pdf",
                "title": "RISC-V ABIs Specification",
            },
            "riscv-debug-specification": {
                "url": "https://drive.google.com/uc?export=download&id=1h_f9NgB_8m2fS6uCnKP1Oho-3x1MpBEl",
                "path": "core-specs/standards/riscv-debug-specification.pdf",
                "title": "RISC-V Debug Specification",
            },
            "riscv-sbi-specification": {
                "url": "https://drive.google.com/uc?export=download&id=1U2kwjqxXgDONXk_-ZDTYzvsV-F_8ylEH",
                "path": "core-specs/standards/riscv-sbi-specification.pdf",
                "title": "RISC-V Supervisor Binary Interface Specification",
            },
            "rva23-profile": {
                "url": "https://drive.google.com/uc?export=download&id=12QKRm92cLcEk8-5J9NI91m0fAQOxqNAq",
                "path": "core-specs/profiles/rva23-profile.pdf",
                "title": "RVA23 Profile Specification",
            },
            "rvb23-profile": {
                "url": "https://drive.google.com/uc?export=download&id=1pBQAeTasG6smBxZc_zLkQU1GPA4Zngo7",
                "path": "core-specs/profiles/rvb23-profile.pdf",
                "title": "RVB23 Profile Specification",
            },
            # Recent ratified extensions
            "vector-intrinsic-specification": {
                "url": "https://drive.google.com/uc?export=download&id=1RTZi2iOLKzqaX95JCCnzwOm7iCIN3JEq",
                "path": "core-specs/extensions/vector-intrinsic-specification.pdf",
                "title": "RISC-V Vector C Intrinsic Specification",
            },
        }

        success_count = 0
        for doc_id, doc_info in official_docs.items():
            if self.download_pdf(doc_info["url"], doc_info["path"], doc_info["title"]):
                success_count += 1

        print(
            f"\n📊 Official specs collection complete: {success_count}/{len(official_docs)} successful"
        )
        return success_count

    def collect_implementation_guides(self):
        """Collect processor implementation and toolchain documentation."""
        print("\n🔧 Phase 2: Collecting Implementation Guides")
        print("=" * 60)

        # Current working implementation guides (Updated URLs for 2025)
        implementation_docs = {
            # Trace and Debug specifications
            "efficient-trace-riscv": {
                "url": "https://drive.google.com/uc?export=download&id=1iijHsZB7YXW0A2HuuzHo5QTZSKrO_KbW",
                "path": "implementation/debug/efficient-trace-riscv.pdf",
                "title": "Efficient Trace for RISC-V Specification",
            },
            "advanced-interrupt-architecture": {
                "url": "https://drive.google.com/uc?export=download&id=16life2Y5u7Plebbl4v1fFM1-NK-KHw0Y",
                "path": "implementation/system/advanced-interrupt-architecture.pdf",
                "title": "RISC-V Advanced Interrupt Architecture",
            },
            "platform-interrupt-controller": {
                "url": "https://drive.google.com/uc?export=download&id=1at94PNJl4v2eAsKIwKOsZWBxsVcY2U2F",
                "path": "implementation/system/platform-interrupt-controller.pdf",
                "title": "RISC-V Platform-Level Interrupt Controller Specification",
            },
            "iommu-architecture": {
                "url": "https://drive.google.com/uc?export=download&id=1kVapIJPXUUNFQv_yauCDgtWzMvpgh6C2",
                "path": "implementation/system/iommu-architecture.pdf",
                "title": "RISC-V IOMMU Architecture Specification",
            },
            "server-soc-specification": {
                "url": "https://drive.google.com/uc?export=download&id=1KjewRE0NltEmbKOz7YlgOsTF51lZ6aPL",
                "path": "implementation/soc/server-soc-specification.pdf",
                "title": "RISC-V Server SOC Specification",
            },
            "semihosting-specification": {
                "url": "https://drive.google.com/uc?export=download&id=1qu74D4_EmjGmc03qzfQ7Pf4g6m0fOtcD",
                "path": "implementation/system/semihosting-specification.pdf",
                "title": "RISC-V Semihosting Specification",
            },
            "uefi-protocol-specification": {
                "url": "https://drive.google.com/uc?export=download&id=1rbQDRkoeJyqTKTI6tTCKw8zmh7T9dLUZ",
                "path": "implementation/firmware/uefi-protocol-specification.pdf",
                "title": "RISC-V UEFI Protocol Specification",
            },
            # Trace specifications
            "n-trace-nexus": {
                "url": "https://drive.google.com/uc?export=download&id=1UXFptcTjd5akPhKRtn0onBC6t53O61qU",
                "path": "implementation/debug/n-trace-nexus.pdf",
                "title": "RISC-V N-Trace (Nexus-based Trace) Specification",
            },
            "trace-control-interface": {
                "url": "https://drive.google.com/uc?export=download&id=1ZQvU1WNamY5EHGum4yP1z-WmPrcxH2b8",
                "path": "implementation/debug/trace-control-interface.pdf",
                "title": "RISC-V Trace Control Interface Specification",
            },
            "trace-connectors": {
                "url": "https://drive.google.com/uc?export=download&id=1SMypv0CUL338L-sURMyJuO60WZ7oDi9V",
                "path": "implementation/debug/trace-connectors.pdf",
                "title": "RISC-V Trace Connectors Specification",
            },
        }

        success_count = 0
        for doc_id, doc_info in implementation_docs.items():
            if self.download_pdf(doc_info["url"], doc_info["path"], doc_info["title"]):
                success_count += 1

        print(
            f"\n📊 Implementation guides collection: {success_count}/{len(implementation_docs)} successful"
        )
        print(
            "💡 Note: Additional processor-specific docs available from vendor websites"
        )
        print("   Examples: SiFive documentation, Andes cores, Microchip PIC64GX, etc.")

        return success_count

    def collect_academic_papers(self):
        """Collect relevant academic papers and research."""
        print("\n🎓 Phase 3: Collecting Academic Papers")
        print("=" * 60)

        # Quality RISC-V system specifications and implementation guides
        system_docs = {
            # QoS and reliability specifications
            "qos-register-interface": {
                "url": "https://drive.google.com/uc?export=download&id=1XSKqg6MXEmRdpdUYLj-Q03kZD6TDQhtu",
                "path": "research/system/qos-register-interface.pdf",
                "title": "RISC-V Capacity and Bandwidth QoS Register Interface",
            },
            "reri-architecture": {
                "url": "https://drive.google.com/uc?export=download&id=19gMRFbWDrfDZKyqoO3iFkySPvKpxm26a",
                "path": "research/system/reri-architecture.pdf",
                "title": "RISC-V RERI Architecture Specification",
            },
            "functional-fixed-hardware": {
                "url": "https://drive.google.com/uc?export=download&id=1XzlA0LE4N5_47wJXsU3aqyD69pHGvdcL",
                "path": "research/system/functional-fixed-hardware.pdf",
                "title": "RISC-V Functional Fixed Hardware Specification",
            },
            "io-mapping-table": {
                "url": "https://drive.google.com/uc?export=download&id=1sxQ3iQ1l5Jgq9tukvGMnucRUvY16s8zN",
                "path": "research/system/io-mapping-table.pdf",
                "title": "RISC-V IO Mapping Table Specification",
            },
            # Trace and diagnostic specifications
            "trace-encapsulation": {
                "url": "https://drive.google.com/uc?export=download&id=1R-_koXIpdb9_qW6jpz74TSnNXOfJGhfn",
                "path": "research/debug/trace-encapsulation.pdf",
                "title": "Unformatted Trace & Diagnostic Data Packet Encapsulation for RISC-V",
            },
        }

        success_count = 0
        for doc_id, doc_info in system_docs.items():
            if self.download_pdf(doc_info["url"], doc_info["path"], doc_info["title"]):
                success_count += 1

        print(
            f"\n📊 Research documents collection: {success_count}/{len(system_docs)} successful"
        )
        print(
            "💡 Note: Academic papers from arXiv are automatically collected separately"
        )
        print("   This phase focuses on official research and system specifications")

        # Also collect arXiv papers if available
        arxiv_count = 0
        if ARXIV_AVAILABLE:
            print("\n🔍 Searching arXiv for RISC-V academic papers...")
            arxiv_count = self.collect_arxiv_papers()
        else:
            print("\n⚠️  arXiv library not available. Install with: pip install arxiv")
            print("   Skipping academic paper collection from arXiv")

        total_count = success_count + arxiv_count
        print(
            f"\n📊 Total academic papers collected: {total_count} ({success_count} official + {arxiv_count} arXiv)"
        )
        return total_count

    def collect_arxiv_papers(
        self, max_papers: int = 50, min_relevance: float = 2.0
    ) -> int:
        """Collect relevant RISC-V papers from arXiv."""
        if not ARXIV_AVAILABLE:
            return 0

        # RISC-V search queries
        search_queries = [
            "RISC-V processor architecture",
            "RISC-V instruction set",
            "RISC-V performance optimization",
            "RISC-V security analysis",
            "RISC-V compiler optimization",
        ]

        collected_papers = []
        all_papers = []

        # Search arXiv for each query
        for query in search_queries:
            try:
                print(f"🔍 Searching: {query}")
                search = arxiv.Search(
                    query=query, max_results=20, sort_by=arxiv.SortCriterion.Relevance
                )

                for paper in search.results():
                    # Calculate relevance score
                    relevance = self.calculate_relevance_score(paper)
                    if relevance >= min_relevance:
                        paper_info = {
                            "id": paper.entry_id.split("/")[-1],
                            "title": paper.title,
                            "authors": [str(author) for author in paper.authors],
                            "abstract": paper.summary,
                            "url": paper.pdf_url,
                            "relevance": relevance,
                            "category": self.categorize_paper(paper),
                        }
                        all_papers.append(paper_info)

                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"⚠️  Error searching '{query}': {e}")
                continue

        # Remove duplicates and sort by relevance
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            if paper["id"] not in seen_ids:
                unique_papers.append(paper)
                seen_ids.add(paper["id"])

        # Sort by relevance and take top papers
        unique_papers.sort(key=lambda x: x["relevance"], reverse=True)
        selected_papers = unique_papers[:max_papers]

        print(
            f"📊 Found {len(unique_papers)} unique relevant papers, downloading top {len(selected_papers)}"
        )

        # Download selected papers
        success_count = 0
        for paper in selected_papers:
            category_path = f"research/papers/{paper['category']}"
            filename = f"{paper['id'].replace('/', '_')}.pdf"
            file_path = f"{category_path}/{filename}"

            if self.download_pdf(paper["url"], file_path, paper["title"]):
                success_count += 1

        return success_count

    def calculate_relevance_score(self, paper) -> float:
        """Calculate relevance score for a paper based on title and abstract."""
        text = (paper.title + " " + paper.summary).lower()

        # High value keywords
        high_value = [
            "risc-v",
            "riscv",
            "instruction set",
            "processor architecture",
            "isa design",
            "risc five",
            "open source processor",
        ]
        medium_value = [
            "risc",
            "processor",
            "cpu",
            "microprocessor",
            "instruction",
            "architecture",
            "performance",
            "optimization",
            "compiler",
        ]
        low_value = ["embedded", "system", "hardware", "software", "implementation"]

        score = 0.0

        # Count keyword occurrences
        for keyword in high_value:
            score += text.count(keyword) * 3.0
        for keyword in medium_value:
            score += text.count(keyword) * 1.0
        for keyword in low_value:
            score += text.count(keyword) * 0.5

        # Boost for recent papers (last 5 years)
        try:
            year = paper.published.year
            if year >= 2020:
                score += 1.0
            elif year >= 2018:
                score += 0.5
        except:
            pass

        return score

    def categorize_paper(self, paper) -> str:
        """Categorize paper based on content."""
        text = (paper.title + " " + paper.summary).lower()

        if any(
            keyword in text
            for keyword in [
                "performance",
                "benchmark",
                "speed",
                "optimization",
                "efficiency",
            ]
        ):
            return "performance-analysis"
        elif any(
            keyword in text
            for keyword in [
                "security",
                "attack",
                "vulnerability",
                "encryption",
                "protection",
            ]
        ):
            return "security-studies"
        elif any(
            keyword in text
            for keyword in [
                "architecture",
                "design",
                "microarchitecture",
                "pipeline",
                "core",
            ]
        ):
            return "architecture-studies"
        else:
            return "benchmarking"

    def collect_reference_materials(self):
        """Collect quick reference materials and tutorials."""
        print("\n📖 Phase 4: Collecting Reference Materials")
        print("=" * 60)

        # NOTE: This is a stub - reference materials are mostly HTML-based
        # Key resources include:
        # - RISC-V Optimization Guide: https://riscv-optimization-guide-riseproject-c94355ae3e6872252baa952524.gitlab.io/
        # - RISC-V Assembler Cheat Sheet: https://projectf.io/posts/riscv-cheat-sheet/
        # - RISC-V Green Cards and quick references (various formats)

        reference_docs = {
            # Placeholder for any PDF-based reference materials
            # Most modern RISC-V references are web-based for better accessibility
        }

        success_count = 0
        # Note: No downloads in current implementation as modern refs are web-based

        print(f"\n📊 Reference materials phase complete")
        print("💡 Key reference resources (web-based):")
        print("   • RISC-V Optimization Guide: Comprehensive performance tuning")
        print("   • Project F Cheat Sheet: Complete instruction reference")
        print("   • Official RISC-V Specifications: Latest technical docs")
        print("   • Academic papers: Research corpus via arXiv collection")

        return success_count

    def print_statistics(self):
        """Print collection statistics."""
        print("\n" + "=" * 60)
        print("📊 COLLECTION STATISTICS")
        print("=" * 60)
        print(f"✅ Downloaded: {self.stats['downloaded']} documents")
        print(f"⏭️  Skipped: {self.stats['skipped']} documents")
        print(f"❌ Failed: {self.stats['failed']} documents")
        print(f"💾 Total Size: {self.stats['total_size_mb']:.1f} MB")
        print(f"📁 Corpus Location: {self.base_dir}")

        if self.stats["downloaded"] > 0:
            print(f"\n🎉 Collection successful! Ready for Epic 2 demo processing.")
        else:
            print(
                f"\n⚠️  No new documents collected. Check URLs or network connectivity."
            )

    def run_phase(self, phase: int):
        """Run specific collection phase."""
        if phase == 1:
            return self.collect_official_specs()
        elif phase == 2:
            return self.collect_implementation_guides()
        elif phase == 3:
            return self.collect_academic_papers()
        elif phase == 4:
            return self.collect_reference_materials()
        else:
            print(f"❌ Invalid phase: {phase}")
            return 0

    def run_all_phases(self):
        """Run complete collection process."""
        print("🚀 STARTING COMPREHENSIVE RISC-V DOCUMENTATION COLLECTION")
        print("=" * 70)

        total_collected = 0
        for phase in range(1, 5):
            collected = self.run_phase(phase)
            total_collected += collected
            time.sleep(2)  # Brief pause between phases

        self.save_download_log()
        self.print_statistics()

        return total_collected


def main():
    """Main entry point for document collection."""
    parser = argparse.ArgumentParser(
        description="Collect RISC-V documentation for Epic 2 demo"
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3, 4],
        help="Collection phase: 1=specs, 2=implementation, 3=academic, 4=reference",
    )
    parser.add_argument("--all", action="store_true", help="Run all collection phases")
    parser.add_argument(
        "--output-dir",
        default="data/riscv_comprehensive_corpus",
        help="Output directory for collected documents",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force re-download of existing documents"
    )

    args = parser.parse_args()

    # Initialize collector
    collector = RISCVDocCollector(args.output_dir)

    try:
        if args.all:
            total = collector.run_all_phases()
            print(f"\n🎯 Total documents collected across all phases: {total}")
        elif args.phase:
            collected = collector.run_phase(args.phase)
            collector.save_download_log()
            collector.print_statistics()
            print(f"\n🎯 Phase {args.phase} collected: {collected} documents")
        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
        collector.save_download_log()
        collector.print_statistics()
    except Exception as e:
        print(f"\n❌ Collection failed: {str(e)}")
        collector.save_download_log()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
