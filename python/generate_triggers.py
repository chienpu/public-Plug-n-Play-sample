"""
generate_triggers.py
====================
Establishes semantic TRIGGERS edges and cross-domain PROPAGATES_TO links.
Adapted from STRIDE sample (github.com/chienpu/public-STRIDE-sample).

New in this version: cross-domain propagation from PdM → Procurement
pack, implementing the TIAA execution contract described in ISARC 2026.
"""

import time
from neo4j import GraphDatabase

NEO4J_URI      = "bolt://localhost:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "your_password_here"   # ← update this

# Standard TRIGGERS: Anomaly → MaintenanceTask (from STRIDE)
TRIGGERS_QUERY = """
MATCH (pd:PerformanceData)-[:TRIGGERS]->(task:MaintenanceTask)
WHERE NOT EXISTS {
    MATCH (pd)-[:TIAA_TRIGGERS]->(task)
}
MERGE (pd)-[:TIAA_TRIGGERS {
    stage:      'Action',
    pack_id:    'pdm-pack-v1.0',
    rule_id:    'R-PdM-001',
    created_at: datetime()
}]->(task)
RETURN count(*) AS tiaa_triggers_created
"""

# Cross-domain PROPAGATES_TO: PdM Action → Procurement Trigger
CROSS_DOMAIN_QUERY = """
MATCH (task:MaintenanceTask)
WHERE task.TIAAAction = 'ReplacementRequired'
  AND NOT EXISTS {
    MATCH (task)-[:PROPAGATES_TO]->(:TIAAEvent {stage: 'Trigger', domain: 'Procurement'})
  }
MATCH (pro_trigger:TIAAEvent {id: 'TIAA-PRO-T001'})
MERGE (task)-[:PROPAGATES_TO {
    cross_domain:   true,
    from_pack:      'pdm-pack-v1.0',
    to_pack:        'procurement-pack-v1.0',
    from_domain:    'PredictiveMaintenance',
    to_domain:      'Procurement',
    propagated_at:  datetime()
}]->(pro_trigger)
RETURN count(*) AS cross_domain_links_created
"""

# Verify the complete chain
VERIFY_QUERY = """
MATCH path = (pd:PerformanceData)-[:TRIGGERS|PROPAGATES_TO*1..5]->(end)
WHERE end:TIAAEvent AND end.domain = 'Procurement'
RETURN
    count(path)       AS total_cross_domain_paths,
    length(path)      AS path_length
LIMIT 1
"""


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    print("Establishing TIAA semantic edges...\n")

    # TIAA TRIGGERS edges
    t0 = time.perf_counter()
    with driver.session() as session:
        result = session.run(TRIGGERS_QUERY)
        data = result.data()
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"  ✓ TIAA_TRIGGERS edges: {data[0]['tiaa_triggers_created']}  ({elapsed:.2f} ms)")

    # Cross-domain PROPAGATES_TO edges
    t0 = time.perf_counter()
    with driver.session() as session:
        result = session.run(CROSS_DOMAIN_QUERY)
        data = result.data()
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"  ✓ Cross-domain PROPAGATES_TO links: {data[0]['cross_domain_links_created']}  ({elapsed:.2f} ms)")
    print(f"    → PdM Domain Pack  →  Procurement Domain Pack")

    # Verify complete chain
    with driver.session() as session:
        result = session.run(VERIFY_QUERY)
        data = result.data()
    if data:
        print(f"\n  ✓ Cross-domain paths verified: {data[0]['total_cross_domain_paths']}")
        print(f"    Path length: {data[0]['path_length']} hops")

    driver.close()
    print("\nDone. Run Domain_Pack_TIAA_Simulation.py to measure performance.")


if __name__ == "__main__":
    main()
