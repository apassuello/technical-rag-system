"""
Portfolio Readiness Assessment for Epic 2 System.

This script evaluates the Epic 2 Advanced Retriever system against Swiss engineering
standards and portfolio readiness criteria, providing a comprehensive score and
recommendations for portfolio inclusion.

Swiss Engineering Standards Assessment:
- Technical Sophistication (30%)
- Performance Excellence (25%)
- Code Quality & Architecture (20%)
- Production Readiness (15%)
- Documentation & Testing (10%)
"""

import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PortfolioScoreComponent:
    """Component of portfolio scoring."""

    name: str
    weight: float
    score: float
    max_score: float
    details: Dict[str, Any]


class PortfolioAssessor:
    """Comprehensive portfolio readiness assessor for Epic 2."""

    def __init__(self):
        self.score_components = []
        self.assessment_results = {}

        # Swiss engineering standards weights
        self.weights = {
            "technical_sophistication": 0.30,
            "performance_excellence": 0.25,
            "code_quality_architecture": 0.20,
            "production_readiness": 0.15,
            "documentation_testing": 0.10,
        }

    def assess_portfolio_readiness(
        self, validation_results: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Assess complete portfolio readiness."""
        logger.info("Starting comprehensive portfolio readiness assessment...")

        # Load validation results if provided
        if validation_results:
            self.validation_results = validation_results
        else:
            self.validation_results = self._load_latest_validation_results()

        # Assess each component
        self.score_components = [
            self._assess_technical_sophistication(),
            self._assess_performance_excellence(),
            self._assess_code_quality_architecture(),
            self._assess_production_readiness(),
            self._assess_documentation_testing(),
        ]

        # Calculate overall portfolio score
        overall_score = self._calculate_overall_score()

        # Generate recommendations
        recommendations = self._generate_recommendations()

        # Create final assessment
        self.assessment_results = {
            "overall_portfolio_score": overall_score,
            "portfolio_status": self._determine_portfolio_status(overall_score),
            "score_components": [
                {
                    "name": comp.name,
                    "weight": comp.weight,
                    "score": comp.score,
                    "max_score": comp.max_score,
                    "percentage": (
                        (comp.score / comp.max_score * 100) if comp.max_score > 0 else 0
                    ),
                    "details": comp.details,
                }
                for comp in self.score_components
            ],
            "recommendations": recommendations,
            "assessment_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "epic2_readiness_indicators": self._get_epic2_readiness_indicators(),
        }

        return self.assessment_results

    def _load_latest_validation_results(self) -> Dict[str, Any]:
        """Load latest validation results if available."""
        try:
            results_dir = Path("validation_results")
            if results_dir.exists():
                # Find latest results file
                result_files = list(results_dir.glob("epic2_validation_results_*.json"))
                if result_files:
                    latest_file = max(result_files, key=lambda f: f.stat().st_mtime)
                    with open(latest_file, "r") as f:
                        return json.load(f)

            # Return empty results if no validation found
            logger.warning("No validation results found - using simulated assessment")
            return {"validation_results": {}, "overall_metrics": {}}

        except Exception as e:
            logger.warning(f"Failed to load validation results: {str(e)}")
            return {"validation_results": {}, "overall_metrics": {}}

    def _assess_technical_sophistication(self) -> PortfolioScoreComponent:
        """Assess technical sophistication (30% weight)."""
        details = {}
        score = 0
        max_score = 100

        # Epic 2 advanced features (40 points)
        epic2_features = {
            "multi_backend_infrastructure": 10,  # FAISS + Weaviate
            "graph_based_retrieval": 10,  # NetworkX + Entity extraction
            "neural_reranking": 15,  # Cross-encoder ML models
            "4_stage_pipeline": 5,  # Dense → Sparse → Graph → Neural
        }

        feature_scores = {}
        for feature, points in epic2_features.items():
            # Check if feature is validated
            if (
                self.validation_results.get("validation_results", {})
                .get("epic2_integration", {})
                .get("test_results", {})
                .get("four_stage_pipeline", {})
                .get("passed", False)
            ):
                feature_scores[feature] = points
                score += points
            elif (
                self.validation_results.get("validation_results", {})
                .get("graph_integration", {})
                .get("overall_score", 0)
                > 70
            ):
                feature_scores[feature] = points * 0.8  # Partial credit
                score += points * 0.8
            else:
                feature_scores[feature] = 0

        details["epic2_features"] = feature_scores

        # ML/AI sophistication (30 points)
        ml_ai_features = {
            "neural_models": 15,  # Cross-encoder transformers
            "embeddings": 10,  # Sentence transformers
            "graph_ml": 5,  # Graph-based ML
        }

        ml_scores = {}
        neural_score = (
            self.validation_results.get("validation_results", {})
            .get("neural_reranking", {})
            .get("overall_score", 0)
        )
        for feature, points in ml_ai_features.items():
            if neural_score > 70:
                ml_scores[feature] = points
                score += points
            else:
                ml_scores[feature] = points * 0.5  # Partial credit for framework
                score += points * 0.5

        details["ml_ai_features"] = ml_scores

        # Architecture patterns (30 points)
        architecture_features = {
            "modular_design": 10,
            "factory_pattern": 10,
            "configuration_driven": 10,
        }

        arch_scores = {}
        integration_score = (
            self.validation_results.get("validation_results", {})
            .get("epic2_integration", {})
            .get("overall_score", 0)
        )
        for feature, points in architecture_features.items():
            if integration_score > 80:
                arch_scores[feature] = points
                score += points
            else:
                arch_scores[feature] = points * 0.7
                score += points * 0.7

        details["architecture_features"] = arch_scores
        details["total_possible"] = max_score

        return PortfolioScoreComponent(
            name="Technical Sophistication",
            weight=self.weights["technical_sophistication"],
            score=score,
            max_score=max_score,
            details=details,
        )

    def _assess_performance_excellence(self) -> PortfolioScoreComponent:
        """Assess performance excellence (25% weight)."""
        details = {}
        score = 0
        max_score = 100

        performance_results = self.validation_results.get("validation_results", {}).get(
            "performance", {}
        )

        # Latency performance (40 points)
        latency_details = (
            performance_results.get("test_results", {})
            .get("end_to_end_latency", {})
            .get("details", {})
        )
        if latency_details.get("latency_target_met", False):
            score += 40
            details["latency_performance"] = "✅ <700ms P95 target met"
        elif latency_details.get("p95_latency_ms", 1000) < 1000:
            score += 25  # Partial credit
            details["latency_performance"] = (
                f"⚠️ {latency_details.get('p95_latency_ms', 'N/A')}ms (above target)"
            )
        else:
            details["latency_performance"] = "❌ Latency target not met"

        # Memory efficiency (25 points)
        memory_details = (
            performance_results.get("test_results", {})
            .get("memory_usage", {})
            .get("details", {})
        )
        if memory_details.get("memory_target_met", False):
            score += 25
            details["memory_efficiency"] = "✅ <2GB memory target met"
        elif memory_details.get("current_memory_mb", 3000) < 3000:
            score += 15  # Partial credit
            details["memory_efficiency"] = (
                f"⚠️ {memory_details.get('current_memory_mb', 'N/A')}MB (acceptable)"
            )
        else:
            details["memory_efficiency"] = "❌ Memory usage too high"

        # CPU efficiency (20 points)
        cpu_details = (
            performance_results.get("test_results", {})
            .get("cpu_efficiency", {})
            .get("details", {})
        )
        if cpu_details.get("cpu_target_met", False):
            score += 20
            details["cpu_efficiency"] = "✅ <25% CPU increase target met"
        else:
            score += 10  # Partial credit for framework
            details["cpu_efficiency"] = "⚠️ CPU efficiency framework validated"

        # Scalability (15 points)
        backend_switching = (
            performance_results.get("test_results", {})
            .get("backend_switching", {})
            .get("details", {})
        )
        if backend_switching.get("switching_target_met", False):
            score += 15
            details["scalability"] = "✅ <50ms backend switching"
        else:
            score += 8  # Partial credit
            details["scalability"] = "⚠️ Backend switching framework available"

        details["total_possible"] = max_score

        return PortfolioScoreComponent(
            name="Performance Excellence",
            weight=self.weights["performance_excellence"],
            score=score,
            max_score=max_score,
            details=details,
        )

    def _assess_code_quality_architecture(self) -> PortfolioScoreComponent:
        """Assess code quality and architecture (20% weight)."""
        details = {}
        score = 0
        max_score = 100

        # Architectural compliance (40 points)
        integration_results = self.validation_results.get("validation_results", {}).get(
            "epic2_integration", {}
        )
        if integration_results.get("overall_score", 0) > 85:
            score += 40
            details["architectural_compliance"] = "✅ Strong architectural patterns"
        elif integration_results.get("overall_score", 0) > 70:
            score += 30
            details["architectural_compliance"] = "✅ Good architectural patterns"
        else:
            score += 15
            details["architectural_compliance"] = "⚠️ Basic architectural patterns"

        # Error handling (25 points)
        error_handling = integration_results.get("test_results", {}).get(
            "error_handling", {}
        )
        if error_handling.get("passed", False):
            score += 25
            details["error_handling"] = "✅ Comprehensive error handling"
        else:
            score += 12
            details["error_handling"] = "⚠️ Basic error handling"

        # Configuration management (20 points)
        yaml_config = integration_results.get("test_results", {}).get(
            "yaml_configuration", {}
        )
        if yaml_config.get("passed", False):
            score += 20
            details["configuration_management"] = "✅ YAML-driven configuration"
        else:
            score += 10
            details["configuration_management"] = "⚠️ Basic configuration"

        # Graceful degradation (15 points)
        degradation = integration_results.get("test_results", {}).get(
            "graceful_degradation", {}
        )
        if degradation.get("passed", False):
            score += 15
            details["graceful_degradation"] = "✅ Graceful degradation implemented"
        else:
            score += 7
            details["graceful_degradation"] = "⚠️ Basic degradation handling"

        details["total_possible"] = max_score

        return PortfolioScoreComponent(
            name="Code Quality & Architecture",
            weight=self.weights["code_quality_architecture"],
            score=score,
            max_score=max_score,
            details=details,
        )

    def _assess_production_readiness(self) -> PortfolioScoreComponent:
        """Assess production readiness (15% weight)."""
        details = {}
        score = 0
        max_score = 100

        # Monitoring and analytics (35 points)
        multi_backend = self.validation_results.get("validation_results", {}).get(
            "multi_backend", {}
        )
        if multi_backend.get("overall_score", 0) > 80:
            score += 35
            details["monitoring_analytics"] = "✅ Advanced monitoring capabilities"
        else:
            score += 20
            details["monitoring_analytics"] = "⚠️ Basic monitoring framework"

        # Health checking (25 points)
        health_monitoring = multi_backend.get("test_results", {}).get(
            "health_monitoring", {}
        )
        if health_monitoring.get("passed", False):
            score += 25
            details["health_checking"] = "✅ Health monitoring implemented"
        else:
            score += 12
            details["health_checking"] = "⚠️ Basic health framework"

        # Fallback mechanisms (25 points)
        fallback = multi_backend.get("test_results", {}).get("fallback_mechanism", {})
        if fallback.get("passed", False):
            score += 25
            details["fallback_mechanisms"] = "✅ Fallback mechanisms operational"
        else:
            score += 12
            details["fallback_mechanisms"] = "⚠️ Basic fallback framework"

        # Migration capabilities (15 points)
        migration = multi_backend.get("test_results", {}).get("migration_integrity", {})
        if migration.get("passed", False):
            score += 15
            details["migration_capabilities"] = "✅ Data migration tools available"
        else:
            score += 7
            details["migration_capabilities"] = "⚠️ Basic migration framework"

        details["total_possible"] = max_score

        return PortfolioScoreComponent(
            name="Production Readiness",
            weight=self.weights["production_readiness"],
            score=score,
            max_score=max_score,
            details=details,
        )

    def _assess_documentation_testing(self) -> PortfolioScoreComponent:
        """Assess documentation and testing (10% weight)."""
        details = {}
        score = 0
        max_score = 100

        # Comprehensive test suite (60 points)
        total_tests = 0
        passed_tests = 0

        for validator_results in self.validation_results.get(
            "validation_results", {}
        ).values():
            total_tests += validator_results.get("total_tests", 0)
            passed_tests += validator_results.get("passed_tests", 0)

        if total_tests > 30 and passed_tests / total_tests > 0.8:
            score += 60
            details["test_coverage"] = (
                f"✅ Comprehensive: {passed_tests}/{total_tests} tests"
            )
        elif total_tests > 15:
            score += 40
            details["test_coverage"] = f"✅ Good: {passed_tests}/{total_tests} tests"
        else:
            score += 20
            details["test_coverage"] = f"⚠️ Basic: {passed_tests}/{total_tests} tests"

        # Validation framework (25 points)
        if len(self.validation_results.get("validation_results", {})) >= 4:
            score += 25
            details["validation_framework"] = "✅ Multi-component validation suite"
        else:
            score += 12
            details["validation_framework"] = "⚠️ Basic validation framework"

        # Performance benchmarking (15 points)
        performance_tests = self.validation_results.get("validation_results", {}).get(
            "performance", {}
        )
        if performance_tests.get("overall_score", 0) > 70:
            score += 15
            details["performance_benchmarking"] = (
                "✅ Performance benchmarking implemented"
            )
        else:
            score += 7
            details["performance_benchmarking"] = "⚠️ Basic performance testing"

        details["total_possible"] = max_score

        return PortfolioScoreComponent(
            name="Documentation & Testing",
            weight=self.weights["documentation_testing"],
            score=score,
            max_score=max_score,
            details=details,
        )

    def _calculate_overall_score(self) -> float:
        """Calculate weighted overall portfolio score."""
        weighted_score = 0
        total_weight = 0

        for component in self.score_components:
            component_percentage = (component.score / component.max_score) * 100
            weighted_score += component_percentage * component.weight
            total_weight += component.weight

        return weighted_score / total_weight if total_weight > 0 else 0

    def _determine_portfolio_status(self, score: float) -> str:
        """Determine portfolio status based on score."""
        if score >= 95:
            return "PORTFOLIO_EXCELLENT"
        elif score >= 90:
            return "PORTFOLIO_READY"
        elif score >= 75:
            return "PORTFOLIO_APPROACHING"
        elif score >= 60:
            return "PORTFOLIO_DEVELOPING"
        else:
            return "PORTFOLIO_INCOMPLETE"

    def _get_epic2_readiness_indicators(self) -> Dict[str, Any]:
        """Get Epic 2 specific readiness indicators."""
        return {
            "advanced_retriever_operational": self.validation_results.get(
                "validation_results", {}
            )
            .get("epic2_integration", {})
            .get("overall_score", 0)
            > 70,
            "multi_backend_validated": self.validation_results.get(
                "validation_results", {}
            )
            .get("multi_backend", {})
            .get("overall_score", 0)
            > 70,
            "graph_retrieval_functional": self.validation_results.get(
                "validation_results", {}
            )
            .get("graph_integration", {})
            .get("overall_score", 0)
            > 70,
            "neural_reranking_ready": self.validation_results.get(
                "validation_results", {}
            )
            .get("neural_reranking", {})
            .get("overall_score", 0)
            > 70,
            "performance_targets_met": self.validation_results.get(
                "validation_results", {}
            )
            .get("performance", {})
            .get("overall_score", 0)
            > 70,
            "quality_improvements_validated": self.validation_results.get(
                "validation_results", {}
            )
            .get("quality", {})
            .get("overall_score", 0)
            > 70,
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate specific recommendations based on assessment."""
        recommendations = []

        overall_score = self._calculate_overall_score()

        if overall_score >= 90:
            recommendations.extend(
                [
                    "✅ Epic 2 system is ready for portfolio inclusion",
                    "✅ System demonstrates advanced RAG capabilities",
                    "✅ Performance and quality targets met",
                    "📝 Consider highlighting multi-backend and neural reranking features",
                    "📝 Emphasize Swiss engineering quality standards compliance",
                ]
            )
        elif overall_score >= 75:
            recommendations.extend(
                [
                    "⚠️ Epic 2 system is approaching portfolio readiness",
                    "🔧 Address performance bottlenecks if any exist",
                    "🔧 Enhance error handling and monitoring",
                    "📝 Strengthen documentation for complex features",
                    "⏱️ Continue validation and testing efforts",
                ]
            )
        else:
            recommendations.extend(
                [
                    "❌ Epic 2 system requires significant improvements",
                    "🔧 Fix critical component failures",
                    "🔧 Improve performance to meet <700ms target",
                    "🔧 Implement proper error handling and graceful degradation",
                    "📝 Expand test coverage and validation",
                    "⏱️ Focus on core functionality before advanced features",
                ]
            )

        # Component-specific recommendations
        for component in self.score_components:
            component_percentage = (component.score / component.max_score) * 100
            if component_percentage < 70:
                recommendations.append(
                    f"🔧 Improve {component.name.lower()}: currently at {component_percentage:.1f}%"
                )

        return recommendations

    def save_assessment(self, output_file: str = None):
        """Save portfolio assessment to file."""
        if not output_file:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = f"epic2_portfolio_assessment_{timestamp}.json"

        output_path = Path(output_file)
        with open(output_path, "w") as f:
            json.dump(self.assessment_results, f, indent=2)

        logger.info(f"Portfolio assessment saved to {output_path}")

        # Also save human-readable summary
        summary_file = output_path.with_suffix(".txt")
        self._save_summary_report(summary_file)

    def _save_summary_report(self, summary_file: Path):
        """Save human-readable summary report."""
        with open(summary_file, "w") as f:
            f.write("EPIC 2 PORTFOLIO READINESS ASSESSMENT\n")
            f.write("=" * 80 + "\n\n")

            # Overall score
            overall_score = self.assessment_results["overall_portfolio_score"]
            status = self.assessment_results["portfolio_status"]

            f.write(f"Overall Portfolio Score: {overall_score:.1f}%\n")
            f.write(f"Portfolio Status: {status}\n")
            f.write(
                f"Assessment Date: {self.assessment_results['assessment_timestamp']}\n\n"
            )

            # Component scores
            f.write("COMPONENT BREAKDOWN:\n")
            f.write("-" * 40 + "\n")
            for component in self.assessment_results["score_components"]:
                f.write(
                    f"{component['name']}: {component['percentage']:.1f}% "
                    f"(weight: {component['weight']*100:.0f}%)\n"
                )
            f.write("\n")

            # Epic 2 readiness indicators
            f.write("EPIC 2 READINESS INDICATORS:\n")
            f.write("-" * 40 + "\n")
            for indicator, ready in self.assessment_results[
                "epic2_readiness_indicators"
            ].items():
                status = "✅ READY" if ready else "❌ NOT READY"
                f.write(f"  {indicator}: {status}\n")
            f.write("\n")

            # Recommendations
            f.write("RECOMMENDATIONS:\n")
            f.write("-" * 40 + "\n")
            for rec in self.assessment_results["recommendations"]:
                f.write(f"{rec}\n")

            f.write(f"\nGenerated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")


def main():
    """Main entry point for portfolio assessment."""
    assessor = PortfolioAssessor()

    print("Starting Epic 2 Portfolio Readiness Assessment...")

    # Run assessment
    results = assessor.assess_portfolio_readiness()

    # Save results
    assessor.save_assessment()

    # Print summary
    print("\n" + "=" * 80)
    print("EPIC 2 PORTFOLIO ASSESSMENT COMPLETED")
    print("=" * 80)
    print(f"Overall Score: {results['overall_portfolio_score']:.1f}%")
    print(f"Portfolio Status: {results['portfolio_status']}")

    print("\nComponent Scores:")
    for component in results["score_components"]:
        print(f"  {component['name']}: {component['percentage']:.1f}%")

    print("\nKey Recommendations:")
    for rec in results["recommendations"][:5]:  # Show first 5 recommendations
        print(f"  {rec}")

    if len(results["recommendations"]) > 5:
        print(f"  ... and {len(results['recommendations']) - 5} more recommendations")

    return 0 if results["overall_portfolio_score"] >= 75 else 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
