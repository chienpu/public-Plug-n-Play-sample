"""
load_domain_packs.py
====================
Loads Domain Pack definitions from JSON files into Neo4j KG.
Extended from STRIDE base (github.com/chienpu/public-STRIDE-sample).

Corresponds to the Ontology Agent role in the ISARC 2026 paper:
  "The Ontology Agent applies ontologies and mappings from Domain
   Packs to establish a unified semantic layer."
"""

import json
import time
from pathlib import Path
from neo4j import GraphDatabase

NEO4J_URI      = "bolt://localhost:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "your_password_here"   # ← update this

PACK_FILES = [
    "../domain-packs/pdm_pack_v1.json",
    "../domain-packs/procurement_pack_v1.json"
]

LOAD_PACK_QUERY = """
MERGE (dp:DomainPack {id: $pack_id})
SET dp.name      = $name,
    dp.domain    = $domain,
    dp.version   = $version,
    dp.ontology  = $ontology,
    dp.loaded_at = $loaded_at
WITH dp
UNWIND $rules AS rule
MERGE (r:ReasoningRule {rule_id: rule.rule_id})
SET r.name         = rule.name,
    r.condition    = rule.condition,
    r.trigger_type = rule.tiaa.trigger.type,
    r.issue_type   = rule.tiaa.issue.type,
    r.action_type  = rule.tiaa.action.type,
    r.actor_role   = rule.tiaa.actor.type
MERGE (dp)-[:CONTAINS_RULE]->(r)
RETURN dp.id AS pack_loaded, count(r) AS rules_loaded
"""


def load_pack(driver, pack_path):
    with open(pack_path) as f:
        pack = json.load(f)

    dp   = pack["domain_pack"]
    sea  = pack["semantic_alignment_assets"]
    esa  = pack["executable_semantic_assets"]

    t0 = time.perf_counter()
    with driver.session() as session:
        result = session.run(
            LOAD_PACK_QUERY,
            pack_id    = dp["id"],
            name       = dp["name"],
            domain     = dp["domain"],
            version    = dp["version"],
            ontology   = sea["ontology"],
            rules      = esa["reasoning_rules"],
            loaded_at  = time.strftime("%Y-%m-%dT%H:%M:%S")
        )
        data = result.data()
    elapsed = (time.perf_counter() - t0) * 1000

    print(f"  ✓ Loaded: {dp['id']}  ({elapsed:.2f} ms)  "
          f"→ {data[0]['rules_loaded']} rules")
    return elapsed


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    base   = Path(__file__).parent

    print("Loading Domain Packs into Neo4j...\n")
    for pack_file in PACK_FILES:
        path = (base / pack_file).resolve()
        if not path.exists():
            print(f"  ✗ File not found: {path}")
            continue
        load_pack(driver, path)

    print("\nAll packs loaded. Verifying...\n")
    with driver.session() as session:
        result = session.run(
            "MATCH (dp:DomainPack) "
            "RETURN dp.id AS id, dp.domain AS domain, dp.version AS version "
            "ORDER BY dp.domain"
        )
        for row in result:
            print(f"  {row['domain']:30s} | {row['id']:30s} | v{row['version']}")

    driver.close()


if __name__ == "__main__":
    main()
