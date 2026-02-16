#!/usr/bin/env python3
"""
Demo script for the Technical Documentation RAG System.

Three tiered demonstrations, each runnable independently:
  Tier 1 - Full pipeline walk-through (process PDFs, embed, query)
  Tier 2 - Config comparison (same query across different retrieval configs)
  Tier 3 - Agent tool showcase (calculator, code analyzer, registry stats)

Usage:
    python demo.py                # all three tiers
    python demo.py --tier 1       # pipeline only
    python demo.py --tier 2       # config comparison only
    python demo.py --tier 3       # agent tools only
    python demo.py --no-cache     # force PDF reprocessing
    python demo.py --verbose       # show component-level logging

Architecture:
    DemoRunner (logic layer) returns structured dicts. The CLI layer at the
    bottom formats and prints them. A future web UI can import DemoRunner
    and render the same data differently.
"""

import argparse
import hashlib
import logging
import os
import pickle
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Ensure src/ is importable
# ---------------------------------------------------------------------------
_project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_project_root / "src"))

from core.platform_orchestrator import PlatformOrchestrator
from core.interfaces import Answer, Document

logger = logging.getLogger("demo")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CORPUS_DIR = _project_root / "data" / "riscv_corpus"
CACHE_DIR = _project_root / "data" / ".demo_cache"
CACHE_FILE = CACHE_DIR / "documents.pkl"

DEMO_QUERIES = [
    "What is the RISC-V vector extension and what operations does it support?",
    "How does RISC-V handle privilege levels and memory protection?",
    "What are the security challenges in RISC-V implementations?",
]

CONFIG_COMPARISON = [
    {
        "name": "basic.yaml",
        "path": "config/basic.yaml",
        "fusion": "RRF",
        "reranker": "identity",
    },
    {
        "name": "epic2_graph_enhanced_mock.yaml",
        "path": "config/epic2_graph_enhanced_mock.yaml",
        "fusion": "graph-enhanced RRF",
        "reranker": "neural",
    },
    {
        "name": "epic2_score_aware_mock.yaml",
        "path": "config/epic2_score_aware_mock.yaml",
        "fusion": "score-aware",
        "reranker": "neural",
    },
]


# ===========================================================================
# Logic layer — importable by other UIs
# ===========================================================================

def _corpus_hash(corpus_dir: Path) -> str:
    """Hash of sorted PDF paths for cache invalidation."""
    paths = sorted(str(p) for p in corpus_dir.rglob("*.pdf"))
    return hashlib.sha256("\n".join(paths).encode()).hexdigest()[:16]


def _patch_mps_to_cpu(config_path: str) -> str:
    """Return a temp config file with device: 'mps' replaced by device: 'cpu'."""
    original = Path(config_path)
    text = original.read_text()
    if 'device: "mps"' not in text and "device: 'mps'" not in text:
        return config_path
    patched = text.replace('device: "mps"', 'device: "cpu"')
    patched = patched.replace("device: 'mps'", 'device: "cpu"')
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", prefix="demo_", delete=False
    )
    tmp.write(patched)
    tmp.close()
    return tmp.name


def _collect_pdfs(corpus_dir: Path) -> List[Path]:
    """Collect all PDFs from the corpus directory, sorted for determinism."""
    return sorted(corpus_dir.rglob("*.pdf"))


class DemoRunner:
    """Orchestrates demo logic. Returns structured data, never prints."""

    def __init__(
        self,
        corpus_dir: Path = CORPUS_DIR,
        config_name: str = "basic.yaml",
        use_cache: bool = True,
    ):
        self.corpus_dir = corpus_dir
        self.config_name = config_name
        self.config_path = str(_project_root / "config" / config_name)
        self.use_cache = use_cache
        self._orch: Optional[PlatformOrchestrator] = None
        self._documents: List[Document] = []
        self._temp_files: List[str] = []

    def cleanup(self):
        """Remove any temp config files created during the run."""
        for f in self._temp_files:
            try:
                os.unlink(f)
            except OSError:
                pass
        self._temp_files.clear()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def documents(self) -> List[Document]:
        """Cached Document objects for reuse across tiers."""
        return self._documents

    # ------------------------------------------------------------------
    # Tier 1: Full pipeline
    # ------------------------------------------------------------------

    def init_system(self) -> Dict[str, Any]:
        """Initialize PlatformOrchestrator and return health/architecture info."""
        t0 = time.time()
        self._orch = PlatformOrchestrator(self.config_path)
        elapsed = time.time() - t0

        health = self._orch.get_system_health()
        components = {}
        for name, info in health.get("components", {}).items():
            components[name] = info.get("type", "unknown")

        return {
            "config": self.config_name,
            "architecture": health.get("architecture", "unknown"),
            "components": components,
            "health_status": health.get("status", "unknown"),
            "init_time": elapsed,
        }

    def process_corpus(self) -> Dict[str, Any]:
        """Process all PDFs. Uses cache if available and valid."""
        assert self._orch is not None, "Call init_system() first"

        pdfs = _collect_pdfs(self.corpus_dir)
        if not pdfs:
            return {"total_docs": 0, "total_chunks": 0, "per_file": [], "elapsed": 0}

        current_hash = _corpus_hash(self.corpus_dir)

        # Try loading from cache
        if self.use_cache and CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "rb") as f:
                    cached = pickle.load(f)
                if cached.get("hash") == current_hash and cached.get("documents"):
                    self._documents = cached["documents"]
                    # Index cached documents into current orchestrator
                    self._orch.index_documents(self._documents)
                    return {
                        "total_docs": cached.get("total_files", len(pdfs)),
                        "total_chunks": len(self._documents),
                        "per_file": cached.get("per_file", []),
                        "elapsed": 0,
                        "from_cache": True,
                    }
            except Exception as e:
                logger.warning("Cache load failed, reprocessing: %s", e)

        # Process from scratch
        t0 = time.time()
        per_file = []
        total_chunks = 0
        failed = 0

        for i, pdf in enumerate(pdfs, 1):
            try:
                chunks = self._orch.process_document(pdf)
                total_chunks += chunks
                per_file.append({
                    "file": pdf.name,
                    "chunks": chunks,
                    "cumulative_chunks": total_chunks,
                })
            except Exception as e:
                failed += 1
                per_file.append({
                    "file": pdf.name,
                    "chunks": 0,
                    "error": str(e),
                })
                logger.warning("Skipping %s: %s", pdf.name, e)

        elapsed = time.time() - t0

        # Collect processed documents from retriever for caching
        retriever = self._orch._components.get("retriever")
        if hasattr(retriever, "_documents"):
            self._documents = list(retriever._documents)
        elif hasattr(retriever, "documents"):
            self._documents = list(retriever.documents)

        # Save cache
        if self.use_cache and self._documents:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "wb") as f:
                pickle.dump({
                    "hash": current_hash,
                    "documents": self._documents,
                    "per_file": per_file,
                    "total_files": len(pdfs),
                }, f)

        return {
            "total_docs": len(pdfs),
            "total_chunks": total_chunks,
            "per_file": per_file,
            "elapsed": elapsed,
            "failed": failed,
            "from_cache": False,
        }

    def query(self, q: str, k: int = 5) -> Dict[str, Any]:
        """Run a single query and return structured results."""
        assert self._orch is not None, "Call init_system() first"

        t0 = time.time()
        answer: Answer = self._orch.process_query(q, k=k)
        elapsed = time.time() - t0

        sources = []
        for doc in answer.sources:
            source_file = doc.metadata.get("source", doc.metadata.get("file", "unknown"))
            # Show relative path if within project
            source_str = str(source_file)
            try:
                source_str = str(Path(source_str).relative_to(_project_root))
            except ValueError:
                pass
            sources.append({
                "file": source_str,
                "snippet": doc.content[:200],
            })

        scores = answer.metadata.get("retrieval_scores", [])

        return {
            "query": q,
            "answer": answer.text,
            "confidence": answer.confidence,
            "sources": sources,
            "scores": scores,
            "timing": elapsed,
        }

    # ------------------------------------------------------------------
    # Tier 2: Config comparison
    # ------------------------------------------------------------------

    def compare_configs(self, q: str) -> List[Dict[str, Any]]:
        """Run the same query through multiple configs and compare."""
        results = []
        for cfg in CONFIG_COMPARISON:
            config_path = str(_project_root / cfg["path"])

            # Patch MPS -> CPU if needed
            effective_path = _patch_mps_to_cpu(config_path)
            if effective_path != config_path:
                self._temp_files.append(effective_path)

            try:
                t0 = time.time()
                orch = PlatformOrchestrator(effective_path)

                # Reuse cached documents if available
                if self._documents:
                    orch.index_documents(self._documents)

                answer = orch.process_query(q, k=5)
                elapsed = time.time() - t0

                scores = answer.metadata.get("retrieval_scores", [])
                top_score = max(scores) if scores else 0.0

                results.append({
                    "config": cfg["name"],
                    "fusion": cfg["fusion"],
                    "reranker": cfg["reranker"],
                    "confidence": answer.confidence,
                    "top_score": top_score,
                    "timing": elapsed,
                    "answer_preview": answer.text[:120],
                })
            except Exception as e:
                results.append({
                    "config": cfg["name"],
                    "fusion": cfg["fusion"],
                    "reranker": cfg["reranker"],
                    "error": str(e),
                })

        return results

    # ------------------------------------------------------------------
    # Tier 3: Agent tools
    # ------------------------------------------------------------------

    def demo_tools(self) -> Dict[str, Any]:
        """Demonstrate Epic 5 agent tools."""
        from components.query_processors.tools.tool_registry import ToolRegistry
        from components.query_processors.tools.implementations import (
            CalculatorTool,
            CodeAnalyzerTool,
        )

        registry = ToolRegistry()
        calculator = CalculatorTool()
        analyzer = CodeAnalyzerTool()
        registry.register(calculator)
        registry.register(analyzer)

        # Calculator demos
        expressions = [
            "2 ** 10",
            "sqrt(144) + log(e)",
            "sin(pi / 4) * cos(pi / 4)",
            "1 / 0",  # error case
        ]
        calc_results = []
        for expr in expressions:
            result = registry.execute_tool("calculator", expression=expr)
            calc_results.append({
                "expression": expr,
                "result": result.content if result.success else None,
                "error": result.error if not result.success else None,
                "success": result.success,
                "time": result.execution_time,
            })

        # Code analyzer demo
        sample_code = '''
def decode_instruction(raw: int) -> dict:
    """Decode a 32-bit RISC-V instruction into its fields."""
    opcode = raw & 0x7F
    rd = (raw >> 7) & 0x1F
    funct3 = (raw >> 12) & 0x07
    rs1 = (raw >> 15) & 0x1F
    rs2 = (raw >> 20) & 0x1F
    funct7 = (raw >> 25) & 0x7F

    return {
        "opcode": opcode,
        "rd": rd,
        "funct3": funct3,
        "rs1": rs1,
        "rs2": rs2,
        "funct7": funct7,
        "format": _classify_format(opcode),
    }

def _classify_format(opcode: int) -> str:
    """Map opcode to RISC-V instruction format (R, I, S, B, U, J)."""
    r_type = {0x33}
    i_type = {0x13, 0x03, 0x67}
    s_type = {0x23}
    b_type = {0x63}
    u_type = {0x37, 0x17}
    j_type = {0x6F}

    if opcode in r_type:
        return "R"
    elif opcode in i_type:
        return "I"
    elif opcode in s_type:
        return "S"
    elif opcode in b_type:
        return "B"
    elif opcode in u_type:
        return "U"
    elif opcode in j_type:
        return "J"
    return "UNKNOWN"
'''
        analyzer_result = registry.execute_tool("analyze_code", code=sample_code)
        analyzer_data = {
            "success": analyzer_result.success,
            "analysis": analyzer_result.content if analyzer_result.success else None,
            "error": analyzer_result.error if not analyzer_result.success else None,
        }

        # Registry stats
        stats = registry.get_registry_stats()

        return {
            "calculator_results": calc_results,
            "analyzer_results": analyzer_data,
            "stats": stats,
        }


# ===========================================================================
# Presentation layer — formatting helpers
# ===========================================================================

def _supports_color() -> bool:
    """Check if terminal supports ANSI colors."""
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_USE_COLOR = _supports_color()


def _bold(text: str) -> str:
    if _USE_COLOR:
        return f"\033[1m{text}\033[0m"
    return text


def _dim(text: str) -> str:
    if _USE_COLOR:
        return f"\033[2m{text}\033[0m"
    return text


def _section(title: str) -> str:
    line = "=" * 70
    return f"\n{line}\n  {title}\n{line}"


def _subsection(title: str) -> str:
    return f"\n--- {title} ---"


def format_init(data: Dict[str, Any]) -> str:
    """Format system initialization results."""
    lines = [_section("System Initialization")]
    lines.append(f"  Config:        {data['config']}")
    lines.append(f"  Architecture:  {data['architecture']}")
    lines.append(f"  Status:        {data['health_status']}")
    lines.append(f"  Init time:     {data['init_time']:.2f}s")
    lines.append("")
    lines.append("  Components:")
    for name, ctype in data["components"].items():
        lines.append(f"    {name:25s} {ctype}")
    return "\n".join(lines)


def format_corpus(data: Dict[str, Any]) -> str:
    """Format corpus processing results."""
    lines = [_subsection("Corpus Processing")]

    if data.get("from_cache"):
        lines.append(f"  Loaded from cache: {data['total_chunks']} chunks "
                      f"from {data['total_docs']} files")
        return "\n".join(lines)

    lines.append(f"  Files:      {data['total_docs']}")
    lines.append(f"  Chunks:     {data['total_chunks']}")
    lines.append(f"  Elapsed:    {data['elapsed']:.1f}s")
    if data.get("failed"):
        lines.append(f"  Failed:     {data['failed']}")

    lines.append("")
    lines.append(f"  {'File':50s} {'Chunks':>8s}  {'Cumulative':>10s}")
    lines.append(f"  {'-'*50} {'-'*8}  {'-'*10}")
    for entry in data["per_file"]:
        if entry.get("error"):
            lines.append(f"  {entry['file']:50s} {'ERROR':>8s}  {_dim(entry['error'][:30])}")
        else:
            lines.append(
                f"  {entry['file']:50s} {entry['chunks']:8d}"
                f"  {entry.get('cumulative_chunks', ''):>10}"
            )
    return "\n".join(lines)


def format_answer(data: Dict[str, Any]) -> str:
    """Format a single query/answer result."""
    lines = [_subsection(f"Query")]
    lines.append(f"  Q: {data['query']}")
    lines.append("")
    lines.append(f"  Answer (confidence: {data['confidence']:.2f}, {data['timing']:.2f}s):")
    # Wrap answer text
    answer_text = data["answer"]
    for line in answer_text.split("\n"):
        lines.append(f"    {line}")

    if data["sources"]:
        lines.append("")
        lines.append("  Sources:")
        for i, src in enumerate(data["sources"][:5], 1):
            score = data["scores"][i - 1] if i <= len(data["scores"]) else 0
            lines.append(f"    [{i}] {src['file']}")
            lines.append(f"        score={score:.4f}")
            snippet = src["snippet"].replace("\n", " ")[:120]
            lines.append(f"        {_dim(snippet)}")
    return "\n".join(lines)


def format_comparison(results: List[Dict[str, Any]], query: str) -> str:
    """Format config comparison table."""
    lines = [_section("Config Comparison")]
    lines.append(f"  Query: {query}")
    lines.append("")

    # Header
    lines.append(
        f"  {'Config':40s} {'Fusion':20s} {'Reranker':10s} "
        f"{'Conf':>6s} {'Top Score':>10s} {'Time':>7s}"
    )
    lines.append(f"  {'-'*40} {'-'*20} {'-'*10} {'-'*6} {'-'*10} {'-'*7}")

    for r in results:
        if r.get("error"):
            lines.append(f"  {r['config']:40s} {r['fusion']:20s} {r['reranker']:10s} {'ERROR':>6s}")
            lines.append(f"    {_dim(r['error'][:80])}")
        else:
            lines.append(
                f"  {r['config']:40s} {r['fusion']:20s} {r['reranker']:10s} "
                f"{r['confidence']:6.2f} {r['top_score']:10.4f} {r['timing']:6.1f}s"
            )
    return "\n".join(lines)


def format_tools(data: Dict[str, Any]) -> str:
    """Format agent tools demo results."""
    lines = [_section("Epic 5 Agent Tools")]

    # Calculator
    lines.append(_subsection("Calculator Tool"))
    lines.append(f"  {'Expression':35s} {'Result':>20s}")
    lines.append(f"  {'-'*35} {'-'*20}")
    for r in data["calculator_results"]:
        if r["success"]:
            lines.append(f"  {r['expression']:35s} {str(r['result']):>20s}")
        else:
            lines.append(f"  {r['expression']:35s} {'ERROR: ' + (r['error'] or '')[:13]:>20s}")

    # Code analyzer
    lines.append(_subsection("Code Analyzer Tool"))
    ar = data["analyzer_results"]
    if ar["success"]:
        lines.append("  Analysis of RISC-V instruction decoder:")
        for line in str(ar["analysis"]).split("\n"):
            lines.append(f"    {line}")
    else:
        lines.append(f"  ERROR: {ar['error']}")

    # Registry stats
    lines.append(_subsection("Registry Stats"))
    stats = data["stats"]
    lines.append(f"  Registered tools:    {stats['total_tools']}")
    lines.append(f"  Total executions:    {stats['total_executions']}")
    lines.append(f"  Total errors:        {stats['total_errors']}")
    lines.append(f"  Success rate:        {stats['overall_success_rate']:.1%}")

    return "\n".join(lines)


# ===========================================================================
# CLI
# ===========================================================================

def run_tier1(runner: DemoRunner) -> bool:
    """Tier 1: full pipeline walk-through."""
    print(_section("Tier 1: Full Pipeline Walk-Through"))

    # Init
    init_data = runner.init_system()
    print(format_init(init_data))

    # Mock LLM notice
    print(_subsection("Note"))
    print("  Retrieval uses real embeddings (sentence-transformers) and real")
    print("  PDF processing. Answer generation uses a mock LLM adapter --")
    print("  text is templated, not from a language model. Swap the llm_client")
    print("  config key to 'ollama' or 'openai' for real generation.")

    # Process corpus
    corpus_data = runner.process_corpus()
    print(format_corpus(corpus_data))

    # Queries
    for q in DEMO_QUERIES:
        answer_data = runner.query(q)
        print(format_answer(answer_data))

    return True


def run_tier2(runner: DemoRunner) -> bool:
    """Tier 2: config comparison."""
    q = DEMO_QUERIES[0]
    results = runner.compare_configs(q)
    print(format_comparison(results, q))
    return True


def run_tier3(runner: DemoRunner) -> bool:
    """Tier 3: agent tools showcase."""
    tools_data = runner.demo_tools()
    print(format_tools(tools_data))
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Technical Documentation RAG System -- Demo",
    )
    parser.add_argument(
        "--tier",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="Run a specific tier (default: all)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Force PDF reprocessing (ignore cache)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show component-level logging",
    )
    args = parser.parse_args()

    # Logging: quiet by default, --verbose to see component internals
    level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Even in verbose mode, suppress library chatter
    for noisy in ("sentence_transformers", "transformers", "torch", "urllib3",
                  "filelock", "huggingface_hub"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    runner = DemoRunner(use_cache=not args.no_cache)

    tiers = {1: run_tier1, 2: run_tier2, 3: run_tier3}
    run_tiers = [args.tier] if args.tier else [1, 2, 3]

    # If running tier 2 or 3 alone, still need system init + corpus
    if args.tier in (2, 3):
        print(_dim("  Initializing system for standalone tier..."))
        runner.init_system()
        if args.tier == 2:
            # Need documents for comparison
            runner.process_corpus()

    results = {}
    for t in run_tiers:
        try:
            results[t] = tiers[t](runner)
        except Exception as e:
            print(f"\n  Tier {t} failed: {e}")
            logger.exception("Tier %d failed", t)
            results[t] = False

    runner.cleanup()

    # Summary
    print(_section("Summary"))
    for t in run_tiers:
        status = "OK" if results.get(t) else "FAILED"
        print(f"  Tier {t}: {status}")
    print()

    return 0 if all(results.get(t) for t in run_tiers) else 1


if __name__ == "__main__":
    sys.exit(main())
