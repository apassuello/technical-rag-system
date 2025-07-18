#!/usr/bin/env python3
"""
Academic Paper Collector for RISC-V Documentation

Searches and collects relevant RISC-V academic papers from arXiv and other sources
to build a comprehensive research corpus for Epic 2 demo.

Usage:
    python tools/search_academic_papers.py --search
    python tools/search_academic_papers.py --download --max-papers 25
    python tools/search_academic_papers.py --curated  # Download curated list
"""

import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    import arxiv
except ImportError:
    print("⚠️  arxiv package not found. Install with: pip install arxiv")
    sys.exit(1)


class AcademicPaperCollector:
    """Collect RISC-V academic papers from various sources."""

    def __init__(self, output_dir: str = "data/riscv_comprehensive_corpus"):
        """Initialize paper collector."""
        self.output_dir = Path(output_dir)
        self.research_dir = self.output_dir / "research"
        self.metadata_dir = self.output_dir / "metadata"

        # Create directories
        for category in [
            "performance-analysis",
            "security-studies",
            "architecture-studies",
            "benchmarking",
        ]:
            (self.research_dir / "papers" / category).mkdir(parents=True, exist_ok=True)

        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        # Collection statistics
        self.stats = {"searched": 0, "downloaded": 0, "skipped": 0, "failed": 0}

        # Load existing paper metadata
        self.paper_metadata = self.load_paper_metadata()

    def load_paper_metadata(self) -> List[Dict]:
        """Load existing paper metadata to avoid duplicates."""
        metadata_file = self.metadata_dir / "academic-papers.json"
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                return json.load(f)
        return []

    def save_paper_metadata(self):
        """Save paper metadata."""
        metadata_file = self.metadata_dir / "academic-papers.json"
        with open(metadata_file, "w") as f:
            json.dump(self.paper_metadata, f, indent=2)
        print(f"💾 Saved metadata for {len(self.paper_metadata)} papers")

    def search_arxiv(self, query: str = "RISC-V", max_results: int = 100) -> List[Dict]:
        """Search arXiv for RISC-V papers."""
        print(f"🔍 Searching arXiv for: {query}")

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )

        papers = []
        for result in search.results():
            # Check if paper is RISC-V related
            text_content = f"{result.title} {result.summary}".lower()
            if any(keyword in text_content for keyword in ["risc", "riscv", "risc-v"]):
                paper_info = {
                    "source": "arxiv",
                    "id": result.entry_id.split("/")[-1],
                    "title": result.title,
                    "authors": [author.name for author in result.authors],
                    "summary": result.summary,
                    "pdf_url": result.pdf_url,
                    "published": result.published.isoformat(),
                    "categories": [cat for cat in result.categories],
                    "relevance_score": self.calculate_relevance_score(result),
                    "category": self.categorize_paper(result),
                }
                papers.append(paper_info)
                self.stats["searched"] += 1

        print(f"📊 Found {len(papers)} relevant papers on arXiv")
        return papers

    def calculate_relevance_score(self, paper) -> float:
        """Calculate relevance score for paper filtering."""
        # Keywords for different categories (higher score = more relevant)
        keywords = {
            "high_relevance": [
                "processor",
                "implementation",
                "architecture",
                "performance",
                "benchmark",
            ],
            "medium_relevance": [
                "instruction",
                "compiler",
                "optimization",
                "security",
                "design",
            ],
            "risc_specific": ["risc-v", "riscv", "risc v", "rocket", "boom"],
            "technical": [
                "pipeline",
                "cache",
                "memory",
                "branch",
                "superscalar",
                "out-of-order",
            ],
        }

        text = f"{paper.title} {paper.summary}".lower()
        score = 0.0

        # Base score for RISC-V mention
        risc_mentions = sum(
            text.count(keyword) for keyword in keywords["risc_specific"]
        )
        score += risc_mentions * 2.0

        # High relevance keywords
        score += (
            sum(text.count(keyword) for keyword in keywords["high_relevance"]) * 1.5
        )

        # Medium relevance keywords
        score += (
            sum(text.count(keyword) for keyword in keywords["medium_relevance"]) * 1.0
        )

        # Technical depth keywords
        score += sum(text.count(keyword) for keyword in keywords["technical"]) * 0.5

        # Penalty for very short abstracts (likely not substantial papers)
        if len(paper.summary) < 500:
            score *= 0.8

        return round(score, 2)

    def categorize_paper(self, paper) -> str:
        """Categorize paper based on content."""
        text = f"{paper.title} {paper.summary}".lower()

        # Category keywords
        categories = {
            "performance-analysis": [
                "performance",
                "benchmark",
                "evaluation",
                "comparison",
                "speed",
            ],
            "security-studies": [
                "security",
                "attack",
                "vulnerability",
                "defense",
                "crypto",
            ],
            "architecture-studies": [
                "architecture",
                "design",
                "microarchitecture",
                "implementation",
            ],
            "benchmarking": [
                "benchmark",
                "evaluation",
                "measurement",
                "analysis",
                "testing",
            ],
        }

        # Score each category
        category_scores = {}
        for category, keywords in categories.items():
            score = sum(text.count(keyword) for keyword in keywords)
            category_scores[category] = score

        # Return category with highest score, default to architecture-studies
        if any(score > 0 for score in category_scores.values()):
            return max(category_scores, key=lambda x: category_scores[x])
        else:
            return "architecture-studies"

    def download_paper(self, paper: Dict, force: bool = False) -> bool:
        """Download individual paper PDF."""
        # Check if already downloaded
        paper_id = paper["id"]
        if not force:
            for existing in self.paper_metadata:
                if existing.get("id") == paper_id and "local_path" in existing:
                    local_path = Path(existing["local_path"])
                    if local_path.exists():
                        print(f"⏭️  Skipped (exists): {paper['title'][:60]}...")
                        self.stats["skipped"] += 1
                        return True

        try:
            # Determine output path
            category = paper["category"]
            filename = f"{paper_id}_{paper['title'][:50]}.pdf"
            # Clean filename
            filename = "".join(
                c for c in filename if c.isalnum() or c in "._- "
            ).strip()
            filename = filename.replace(" ", "_")

            local_path = self.research_dir / "papers" / category / filename

            print(f"⬇️  Downloading: {paper['title'][:60]}...")

            # Download PDF
            response = requests.get(paper["pdf_url"], stream=True, timeout=30)
            response.raise_for_status()

            # Write file
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Update paper metadata
            paper["local_path"] = str(local_path)
            paper["download_date"] = datetime.now().isoformat()
            paper["file_size_mb"] = round(local_path.stat().st_size / (1024 * 1024), 2)

            self.paper_metadata.append(paper)
            self.stats["downloaded"] += 1

            print(
                f"✅ Downloaded: {paper['title'][:60]}... ({paper['file_size_mb']}MB)"
            )

            # Be respectful to servers
            time.sleep(2)
            return True

        except Exception as e:
            print(f"❌ Failed to download {paper['title'][:60]}...: {str(e)}")
            self.stats["failed"] += 1
            return False

    def download_relevant_papers(
        self, papers: List[Dict], max_papers: int = 25, min_relevance: float = 2.0
    ):
        """Download most relevant papers."""
        # Filter and sort by relevance
        relevant_papers = [p for p in papers if p["relevance_score"] >= min_relevance]
        relevant_papers.sort(key=lambda x: x["relevance_score"], reverse=True)

        print(
            f"\n📋 Found {len(relevant_papers)} papers above relevance threshold ({min_relevance})"
        )
        print(f"🎯 Will download top {min(max_papers, len(relevant_papers))} papers")

        # Download top papers
        downloaded = 0
        for paper in relevant_papers[:max_papers]:
            if self.download_paper(paper):
                downloaded += 1

            # Stop if we hit too many failures
            if self.stats["failed"] > 5:
                print("⚠️  Too many download failures, stopping...")
                break

        return downloaded

    def get_curated_papers(self) -> List[Dict]:
        """Get curated list of important RISC-V papers with known URLs."""
        curated_papers = [
            {
                "source": "curated",
                "id": "riscv-isa-manual",
                "title": "The RISC-V Instruction Set Manual: Historical Overview and Current Status",
                "authors": ["David Patterson", "Andrew Waterman"],
                "summary": "Comprehensive overview of RISC-V ISA development and current status",
                "pdf_url": "https://people.eecs.berkeley.edu/~krste/papers/RISC-V-overview.pdf",
                "category": "architecture-studies",
                "relevance_score": 10.0,
            },
            {
                "source": "curated",
                "id": "boom-processor",
                "title": "BOOM: Berkeley Out-of-Order RISC-V Processor",
                "authors": [
                    "Christopher Celio",
                    "Palmer Dabbelt",
                    "David Chiou",
                    "Krste Asanović",
                ],
                "summary": "Description of BOOM out-of-order RISC-V processor implementation",
                "pdf_url": "https://www2.eecs.berkeley.edu/Pubs/TechRpts/2015/EECS-2015-167.pdf",
                "category": "architecture-studies",
                "relevance_score": 9.5,
            },
            {
                "source": "curated",
                "id": "rocket-chip",
                "title": "Rocket Chip Generator: A RISC-V SoC Generator",
                "authors": ["Krste Asanović", "Rimas Avižienis", "Jonathan Bachrach"],
                "summary": "Description of the Rocket Chip generator for RISC-V SoCs",
                "pdf_url": "https://people.eecs.berkeley.edu/~krste/papers/rocket-chip-generator.pdf",
                "category": "architecture-studies",
                "relevance_score": 9.0,
            },
            # Add more curated papers as discovered
        ]

        return curated_papers

    def download_curated_papers(self):
        """Download curated high-value papers."""
        print("\n📚 Downloading Curated RISC-V Papers")
        print("=" * 50)

        curated = self.get_curated_papers()
        downloaded = 0

        for paper in curated:
            if self.download_paper(paper):
                downloaded += 1

        print(
            f"\n📊 Curated collection complete: {downloaded}/{len(curated)} papers downloaded"
        )
        return downloaded

    def print_statistics(self):
        """Print collection statistics."""
        print("\n" + "=" * 50)
        print("📊 ACADEMIC PAPER COLLECTION STATISTICS")
        print("=" * 50)
        print(f"🔍 Papers searched: {self.stats['searched']}")
        print(f"✅ Papers downloaded: {self.stats['downloaded']}")
        print(f"⏭️  Papers skipped: {self.stats['skipped']}")
        print(f"❌ Download failures: {self.stats['failed']}")

        # Category breakdown
        if self.paper_metadata:
            categories = {}
            for paper in self.paper_metadata:
                cat = paper.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1

            print(f"\n📁 Papers by category:")
            for category, count in sorted(categories.items()):
                print(f"   {category}: {count} papers")

        print(f"\n📁 Papers location: {self.research_dir / 'papers'}")

    def run_search_and_download(self, max_papers: int = 25, min_relevance: float = 2.0):
        """Run complete search and download process."""
        print("🚀 STARTING ACADEMIC PAPER COLLECTION")
        print("=" * 50)

        # Search arXiv
        papers = self.search_arxiv(max_results=200)

        # Download relevant papers
        downloaded = self.download_relevant_papers(papers, max_papers, min_relevance)

        # Save metadata
        self.save_paper_metadata()

        # Print statistics
        self.print_statistics()

        return downloaded


def main():
    """Main entry point for academic paper collection."""
    parser = argparse.ArgumentParser(description="Collect RISC-V academic papers")
    parser.add_argument(
        "--search",
        action="store_true",
        help="Search and display papers without downloading",
    )
    parser.add_argument(
        "--download", action="store_true", help="Search and download relevant papers"
    )
    parser.add_argument(
        "--curated", action="store_true", help="Download curated high-value papers"
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=25,
        help="Maximum number of papers to download",
    )
    parser.add_argument(
        "--min-relevance",
        type=float,
        default=2.0,
        help="Minimum relevance score for download",
    )
    parser.add_argument(
        "--output-dir",
        default="data/riscv_comprehensive_corpus",
        help="Output directory for papers",
    )

    args = parser.parse_args()

    # Initialize collector
    collector = AcademicPaperCollector(args.output_dir)

    try:
        if args.curated:
            downloaded = collector.download_curated_papers()
            collector.save_paper_metadata()
            collector.print_statistics()
            print(f"\n🎯 Curated papers downloaded: {downloaded}")

        elif args.download:
            downloaded = collector.run_search_and_download(
                args.max_papers, args.min_relevance
            )
            print(f"\n🎯 Academic papers downloaded: {downloaded}")

        elif args.search:
            papers = collector.search_arxiv(max_results=100)
            relevant = [p for p in papers if p["relevance_score"] >= args.min_relevance]

            print(f"\n📋 Top {min(10, len(relevant))} most relevant papers:")
            for i, paper in enumerate(
                sorted(relevant, key=lambda x: x["relevance_score"], reverse=True)[:10],
                1,
            ):
                print(
                    f"{i:2d}. [{paper['relevance_score']:4.1f}] {paper['title'][:70]}..."
                )
                print(f"     {paper['category']} | {paper['published'][:10]}")

            print(
                f"\n💡 Run with --download to download the top {args.max_papers} papers"
            )

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
        collector.save_paper_metadata()
        collector.print_statistics()
    except Exception as e:
        print(f"\n❌ Collection failed: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
