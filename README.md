# Domain Pack + TIAA Cross-Domain Simulation
## Artifact Repository for ISARC 2026

This repository contains selected implementation artifacts supporting the paper:

> Huang, C.-P., & Hsieh, S.-H. (2026). **A Plug-and-Play Semantic Execution Framework for Reusable Cross-Domain Automation in Digital Twins**. *Proceedings of ISARC 2026*.

> 🔒 This is a **public sample**. Proprietary and full-scale datasets are omitted for privacy and intellectual property considerations.

---

## Background

This work extends the STRIDE semantic reasoning framework ([Huang & Hsieh, 2026, AEI](https://doi.org/10.1016/j.aei.2025.104240)) with:

- **Domain Packs** — modular semantic execution units encapsulating ontologies, reasoning rules, workflow templates, and provenance policies
- **TIAA model** — Trigger–Issue–Action–Actor cross-domain execution abstraction
- **Domain-agnostic multi-agent runtime** — agents interpret Pack-defined logic without code modification

---

## Repository Structure

```
public-DomainPack-TIAA-sample/
├── README.md
├── domain-packs/
│   ├── pdm_pack_v1.json              # PdM Domain Pack definition
│   └── procurement_pack_v1.json      # Procurement Domain Pack definition
├── neo4j-schema/
│   └── tiaa_schema.cypher            # TIAA node/relationship schema
├── python/
│   ├── Domain_Pack_TIAA_Simulation.py   # Main simulation + measurement script
│   ├── load_domain_packs.py             # Domain Pack loader (extended from STRIDE)
│   ├── generate_anomaly_data.py         # Sensor anomaly generator (from STRIDE)
│   ├── generate_maintenance_task.py     # Maintenance task generator (from STRIDE)
│   ├── generate_triggers.py             # Semantic TRIGGERS edges (from STRIDE)
│   └── generate_provenance_trace.py     # PROV-O provenance recorder
├── sample-data/
│   ├── Sensor_Data_300.csv              # Campus scenario synthetic data (from STRIDE)
│   ├── Anomaly_Data_300.csv
│   ├── BuildingComponent_Dataset.csv
│   └── campus_procurement_synthetic.csv # Procurement domain synthetic data (new)
└── results/
    └── tiaa_simulation_results.json     # Output from simulation run
```

---

## Prerequisites

- Neo4j (v5.x), running locally at `bolt://localhost:7687`
- Python 3.9+
- `pip install neo4j pandas`
- Existing STRIDE schema loaded (run STRIDE scripts first, or use the loaders here)

---

## Quick Start

### Step 1 — Load Domain Packs into Neo4j

```bash
python python/load_domain_packs.py
```

### Step 2 — Generate synthetic campus scenario data

```bash
python python/generate_anomaly_data.py
python python/generate_maintenance_task.py
python python/generate_triggers.py
```

### Step 3 — Run cross-domain TIAA simulation and measurement

```bash
python python/Domain_Pack_TIAA_Simulation.py
```

Results are printed to console and saved to `results/tiaa_simulation_results.json`.

---

## What Is Measured

| Metric | Purpose |
|--------|---------|
| Domain Pack loading time | Validates runtime Pack composition feasibility |
| Cross-domain TIAA query time | Measures propagation across PdM → Procurement |
| TIAA propagation steps | Confirms cross-domain chain completeness |
| Provenance trace nodes | Validates auditability via PROV-O |
| Agent code modifications | Confirms domain-agnostic reusability (expected: 0) |

---

## Relationship to STRIDE

Scripts in `python/` marked *(from STRIDE)* are adapted from the STRIDE sample repository:
[https://github.com/chienpu/public-STRIDE-sample](https://github.com/chienpu/public-STRIDE-sample)

The STRIDE base achieves 82.5% task automation rate and 0.74s query response time at 30,082 nodes [Huang & Hsieh, 2026, AEI]. This repository extends that validated runtime with Domain Pack composition and cross-domain TIAA propagation.

---

## Related Publication

Huang, C.-P., & Hsieh, S.-H. (2026). Semantic reasoning and integration for automating predictive maintenance in smart facility management. *Advanced Engineering Informatics*, 71, 104240. https://doi.org/10.1016/j.aei.2025.104240

---

## Contact

Maintained by [chienpu](https://github.com/chienpu).
For academic use or collaboration: chienpu@gmail.com

## License

MIT License — for academic and non-commercial use.
