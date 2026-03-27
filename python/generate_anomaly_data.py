"""
generate_anomaly_data.py
========================
Generates synthetic sensor anomaly data for the campus PdM scenario.
Adapted from STRIDE sample (github.com/chienpu/public-STRIDE-sample).

Generates CSV datasets compatible with the STRIDE ontology schema,
used as input to the Domain Pack TIAA simulation.
"""

import csv
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from neo4j import GraphDatabase

NEO4J_URI      = "bolt://localhost:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "your_password_here"   # ← update this

OUTPUT_DIR     = Path(__file__).parent.parent / "sample-data"
N_RECORDS      = 300
ANOMALY_THRESHOLD = 33.0   # degrees C — same as STRIDE baseline

SENSORS = [
    {"SensorId": "SEN-001", "GlobalId": "IFC-100001", "SensorType": "TemperatureSensor", "Unit": "C"},
    {"SensorId": "SEN-002", "GlobalId": "IFC-100002", "SensorType": "TemperatureSensor", "Unit": "C"},
    {"SensorId": "SEN-003", "GlobalId": "IFC-100003", "SensorType": "TemperatureSensor", "Unit": "C"},
]


def generate_records(n=N_RECORDS):
    records = []
    base_time = datetime(2025, 2, 1, 8, 0, 0)

    for i in range(n):
        sensor    = random.choice(SENSORS)
        timestamp = base_time + timedelta(hours=i * 0.5)
        # ~20% anomaly rate to match STRIDE baseline
        if random.random() < 0.20:
            value = round(random.uniform(33.5, 38.0), 2)
        else:
            value = round(random.uniform(24.0, 32.5), 2)

        records.append({
            "SensorId":   sensor["SensorId"],
            "GlobalId":   sensor["GlobalId"],
            "MetricName": "Temperature",
            "Value":      value,
            "Timestamp":  timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Anomaly":    "Yes" if value > ANOMALY_THRESHOLD else "No",
            "DomainPack": "pdm-pack-v1.0"
        })
    return records


def write_csv(records, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"  ✓ Written: {path}  ({len(records)} records)")
    return path


def load_to_neo4j(driver, records):
    """Load performance data into Neo4j — mirrors STRIDE ingest."""
    query = """
    UNWIND $records AS row
    MERGE (s:Sensor {SensorId: row.SensorId})
    SET s.GlobalId = row.GlobalId, s.SensorType = 'TemperatureSensor'
    MERGE (c:BuildingComponent {GlobalId: row.GlobalId})
    MERGE (pd:PerformanceData {
        EventId:    row.SensorId + '-' + row.Timestamp,
        SensorId:   row.SensorId,
        MetricName: row.MetricName,
        Value:      toFloat(row.Value),
        Timestamp:  row.Timestamp,
        Anomaly:    row.Anomaly,
        DomainPack: row.DomainPack
    })
    MERGE (s)-[:GENERATES]->(pd)
    MERGE (s)-[:ASSOCIATES_WITH]->(c)
    """
    t0 = time.perf_counter()
    with driver.session() as session:
        session.run(query, records=records)
    elapsed = (time.perf_counter() - t0) * 1000
    anomalies = sum(1 for r in records if r["Anomaly"] == "Yes")
    print(f"  ✓ Loaded {len(records)} records to Neo4j  ({elapsed:.2f} ms)")
    print(f"    Anomalies: {anomalies} / {len(records)} "
          f"({anomalies/len(records)*100:.1f}%)")


def main():
    print("Generating campus sensor anomaly data...\n")
    records = generate_records()
    write_csv(records, "Sensor_Data_300.csv")

    anomaly_records = [r for r in records if r["Anomaly"] == "Yes"]
    write_csv(anomaly_records, "Anomaly_Data_300.csv")

    print("\nLoading into Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    load_to_neo4j(driver, records)
    driver.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
