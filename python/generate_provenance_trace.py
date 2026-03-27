"""
generate_provenance_trace.py
============================
Generates PROV-O compatible provenance traces for all TIAA execution steps.
New script — not in STRIDE base.

Corresponds to the Provenance Agent role in the ISARC 2026 paper:
  "The Provenance Agent records event lineage and execution outcomes
   to ensure traceable and auditable automation across domains."

Output:
  - ProvActivity nodes in Neo4j (PROV-O style)
  - provenance_trace.json for inspection
"""

import json
import time
from datetime import datetime
from pathlib import Path
from neo4j import GraphDatabase

NEO4J_URI      = "bolt://localhost:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "your_password_here"   # ← update this

OUTPUT_DIR = Path(__file__).parent.parent / "results"

# Build provenance trace from TIAA events
BUILD_PROV_QUERY = """
MATCH (e:TIAAEvent)
OPTIONAL MATCH (e)-[prop:PROPAGATES_TO]->(next:TIAAEvent)
RETURN
    e.id                AS activity_id,
    e.stage             AS tiaa_stage,
    e.domain            AS domain,
    e.pack_id           AS domain_pack,
    e.description       AS description,
    e.propagated_from   AS propagated_from,
    next.id             AS propagates_to,
    prop.cross_domain   AS is_cross_domain
ORDER BY e.domain, e.stage
"""

# Store provenance back into Neo4j as ProvActivity nodes
STORE_PROV_QUERY = """
UNWIND $activities AS act
MERGE (p:ProvActivity {id: 'PROV-' + act.activity_id})
SET p.tiaa_event        = act.activity_id,
    p.tiaa_stage        = act.tiaa_stage,
    p.domain            = act.domain,
    p.domain_pack       = act.domain_pack,
    p.description       = act.description,
    p.propagated_from   = act.propagated_from,
    p.propagates_to     = act.propagates_to,
    p.is_cross_domain   = act.is_cross_domain,
    p.recorded_at       = $recorded_at,
    p.prov_type         = 'prov:Activity'
RETURN count(p) AS prov_nodes_created
"""


def build_prov_o_document(activities, recorded_at):
    """Format as PROV-O compatible JSON-LD document."""
    return {
        "@context": {
            "prov":  "http://www.w3.org/ns/prov#",
            "tiaa":  "http://stride.ntu.edu.tw/tiaa#",
            "xsd":   "http://www.w3.org/2001/XMLSchema#"
        },
        "@type": "prov:Bundle",
        "prov:generatedAtTime": recorded_at,
        "domain_packs_involved": list({a["domain_pack"] for a in activities if a["domain_pack"]}),
        "prov:Activity": [
            {
                "@id":                    f"tiaa:{a['activity_id']}",
                "prov:type":              "prov:Activity",
                "tiaa:stage":             a["tiaa_stage"],
                "tiaa:domain":            a["domain"],
                "tiaa:domainPack":        a["domain_pack"],
                "tiaa:description":       a["description"],
                "tiaa:propagatedFrom":    a["propagated_from"],
                "tiaa:propagatesTo":      a["propagates_to"],
                "tiaa:isCrossDomain":     a["is_cross_domain"],
                "prov:generatedAtTime":   {"@value": recorded_at, "@type": "xsd:dateTime"}
            }
            for a in activities
        ]
    }


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    recorded_at = datetime.now().isoformat()

    print("Generating PROV-O provenance traces...\n")

    # Fetch TIAA events
    t0 = time.perf_counter()
    with driver.session() as session:
        result = session.run(BUILD_PROV_QUERY)
        activities = [dict(r) for r in result]
    fetch_time = (time.perf_counter() - t0) * 1000

    print(f"  ✓ TIAA activities fetched: {len(activities)}  ({fetch_time:.2f} ms)")

    cross_domain = [a for a in activities if a.get("is_cross_domain")]
    print(f"    Cross-domain propagations: {len(cross_domain)}")

    # Store ProvActivity nodes
    t0 = time.perf_counter()
    with driver.session() as session:
        result = session.run(
            STORE_PROV_QUERY,
            activities  = activities,
            recorded_at = recorded_at
        )
        data = result.data()
    store_time = (time.perf_counter() - t0) * 1000
    print(f"  ✓ ProvActivity nodes stored: {data[0]['prov_nodes_created']}  ({store_time:.2f} ms)")

    # Export PROV-O JSON-LD
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prov_doc  = build_prov_o_document(activities, recorded_at)
    out_path  = OUTPUT_DIR / "provenance_trace.json"
    with open(out_path, "w") as f:
        json.dump(prov_doc, f, indent=2, default=str)
    print(f"  ✓ PROV-O document saved: {out_path}")

    # Summary
    print(f"""
  Provenance Summary:
    Total activities:        {len(activities)}
    Cross-domain links:      {len(cross_domain)}
    Domain packs recorded:   {len(prov_doc['domain_packs_involved'])}
    PROV-O document size:    {out_path.stat().st_size} bytes
    """)

    driver.close()
    print("Done.")


if __name__ == "__main__":
    main()
