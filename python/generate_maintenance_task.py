"""
generate_maintenance_task.py
============================
Generates MaintenanceTask nodes in Neo4j from detected anomalies.
Adapted from STRIDE sample (github.com/chienpu/public-STRIDE-sample).

In the TIAA model, this corresponds to the Action stage of the
PdM Domain Pack's reasoning rules (R-PdM-001, R-PdM-002).
"""

import time
import uuid
from neo4j import GraphDatabase

NEO4J_URI      = "bolt://localhost:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "your_password_here"   # ← update this

# Detect anomalies and create MaintenanceTask nodes
DETECT_AND_CREATE_QUERY = """
MATCH (s:Sensor)-[:GENERATES]->(pd:PerformanceData)
WHERE pd.Anomaly = 'Yes'
  AND NOT EXISTS {
    MATCH (pd)-[:TRIGGERS]->(t:MaintenanceTask)
  }
WITH s, pd
MERGE (task:MaintenanceTask {
    TaskId:        'TASK-' + pd.EventId,
    SensorId:      pd.SensorId,
    GlobalId:      s.GlobalId,
    MetricName:    pd.MetricName,
    AnomalyValue:  pd.Value,
    AssignedTime:  pd.Timestamp,
    UrgencyLevel:  CASE WHEN toFloat(pd.Value) > 36 THEN 'P1' ELSE 'P2' END,
    Status:        'Open',
    DomainPack:    'pdm-pack-v1.0',
    TIAAStage:     'Action',
    TIAAAction:    'MaintenanceRequired'
})
MERGE (pd)-[:TRIGGERS]->(task)
RETURN count(task) AS tasks_created
"""

# Identify components with repeated anomalies (R-PdM-002)
REPEATED_ANOMALY_QUERY = """
MATCH (s:Sensor)-[:GENERATES]->(pd:PerformanceData)
WHERE pd.Anomaly = 'Yes'
WITH s.GlobalId AS component, count(pd) AS anomaly_count
WHERE anomaly_count > 3
MERGE (task:MaintenanceTask {
    TaskId:       'TASK-REPLACE-' + component,
    GlobalId:     component,
    UrgencyLevel: 'P1',
    Status:       'ReplacementRequired',
    DomainPack:   'pdm-pack-v1.0',
    TIAAStage:    'Action',
    TIAAAction:   'ReplacementRequired',
    NoteForProcurement: 'Trigger procurement pack'
})
RETURN count(task) AS replacement_tasks_created
"""


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    print("Generating maintenance tasks from anomalies...\n")

    # Standard maintenance tasks
    t0 = time.perf_counter()
    with driver.session() as session:
        result = session.run(DETECT_AND_CREATE_QUERY)
        data = result.data()
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"  ✓ Standard tasks created: {data[0]['tasks_created']}  ({elapsed:.2f} ms)")

    # Replacement tasks (triggers cross-domain to Procurement)
    t0 = time.perf_counter()
    with driver.session() as session:
        result = session.run(REPEATED_ANOMALY_QUERY)
        data = result.data()
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"  ✓ Replacement tasks created: {data[0]['replacement_tasks_created']}  ({elapsed:.2f} ms)")
    print(f"    → These will propagate to Procurement Domain Pack via TIAA")

    # Summary
    with driver.session() as session:
        result = session.run(
            "MATCH (t:MaintenanceTask) "
            "RETURN t.UrgencyLevel AS level, t.Status AS status, count(*) AS n "
            "ORDER BY level"
        )
        print("\n  Task summary:")
        for row in result:
            print(f"    {row['level']:4s} | {row['status']:25s} | {row['n']} tasks")

    driver.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
