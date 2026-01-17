#!/usr/bin/env python3
"""
Quick test of GenomeFunctionAgent.

Usage:
    python scripts/test_genome_agent.py
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from microgrowagents.agents.genome_function_agent import GenomeFunctionAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_find_enzymes():
    """Test find_enzymes method."""
    logger.info("=" * 80)
    logger.info("TEST: find_enzymes()")
    logger.info("=" * 80)

    agent = GenomeFunctionAgent(db_path=Path("data/processed/microgrow.duckdb"))

    # Test 1: Find enzymes by EC wildcard
    logger.info("\n1. Find oxidoreductases (EC 1.*.*.*) in E. coli")
    result = agent.find_enzymes(
        query="find oxidoreductases",
        organism="Escherichia",
        ec_number="1.*"
    )

    logger.info(f"Success: {result['success']}")
    if result["success"]:
        logger.info(f"Found {result['data']['count']} enzymes")
        if result['data']['enzymes']:
            logger.info(f"Example: {result['data']['enzymes'][0]}")
    else:
        logger.error(f"Error: {result.get('error')}")

    # Test 2: Find specific enzyme
    logger.info("\n2. Find glucose-6-phosphate dehydrogenase")
    result2 = agent.find_enzymes(
        query="find glucose-6-phosphate dehydrogenase",
        product="glucose-6-phosphate dehydrogenase"
    )

    logger.info(f"Success: {result2['success']}")
    if result2["success"]:
        logger.info(f"Found {result2['data']['count']} enzymes")
    else:
        logger.error(f"Error: {result2.get('error')}")

    logger.info("\n" + "=" * 80)


def test_detect_auxotrophies():
    """Test detect_auxotrophies method."""
    logger.info("=" * 80)
    logger.info("TEST: detect_auxotrophies()")
    logger.info("=" * 80)

    agent = GenomeFunctionAgent(db_path=Path("data/processed/microgrow.duckdb"))

    logger.info("\n1. Detect auxotrophies for first genome")
    result = agent.detect_auxotrophies(
        query="detect auxotrophies",
        organism="SAMN00114986"
    )

    logger.info(f"Success: {result['success']}")
    if result["success"]:
        summary = result['data']['summary']
        logger.info(f"Pathways checked: {summary['total_pathways_checked']}")
        logger.info(f"Auxotrophies detected: {summary['auxotrophies_detected']}")
        logger.info(f"Prototrophic: {summary['prototrophic']}")

        if result['data']['auxotrophies']:
            logger.info(f"\nFirst auxotrophy: {result['data']['auxotrophies'][0]}")
    else:
        logger.error(f"Error: {result.get('error')}")

    logger.info("\n" + "=" * 80)


def test_find_transporters():
    """Test find_transporters method."""
    logger.info("=" * 80)
    logger.info("TEST: find_transporters()")
    logger.info("=" * 80)

    agent = GenomeFunctionAgent(db_path=Path("data/processed/microgrow.duckdb"))

    logger.info("\n1. Find glucose transporters")
    result = agent.find_transporters(
        query="find glucose transporters",
        organism="SAMN00114986",
        substrate="glucose"
    )

    logger.info(f"Success: {result['success']}")
    if result["success"]:
        logger.info(f"Found {len(result['data']['transporters'])} transporters")
        if result['data']['transporters']:
            logger.info(f"Example: {result['data']['transporters'][0]}")
    else:
        logger.error(f"Error: {result.get('error')}")

    logger.info("\n" + "=" * 80)


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("=" * 80)
    logger.info("GENOME FUNCTION AGENT TESTS")
    logger.info("=" * 80)
    logger.info("\n")

    try:
        test_find_enzymes()
        test_detect_auxotrophies()
        test_find_transporters()

        logger.info("\n")
        logger.info("=" * 80)
        logger.info("ALL TESTS COMPLETE")
        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
