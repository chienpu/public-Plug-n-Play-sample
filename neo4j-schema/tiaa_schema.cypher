// ============================================================
// TIAA Schema — Neo4j Cypher
// ============================================================
// Extends the STRIDE base schema with Domain Pack and TIAA
// node/relationship types for cross-domain semantic execution.
//
// Run this AFTER loading the base STRIDE schema.
// Related paper: Huang & Hsieh, ISARC 2026
// ============================================================

// ── Constraints ──────────────────────────────────────────────

CREATE CONSTRAINT domainpack_id IF NOT EXISTS
FOR (dp:DomainPack) REQUIRE dp.id IS UNIQUE;

CREATE CONSTRAINT tiaa_event_id IF NOT EXISTS
FOR (e:TIAAEvent) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT reasoning_rule_id IF NOT EXISTS
FOR (r:ReasoningRule) REQUIRE r.rule_id IS UNIQUE;

CREATE CONSTRAINT provenance_activity_id IF NOT EXISTS
FOR (p:ProvActivity) REQUIRE p.id IS UNIQUE;

// ── Domain Pack Nodes ─────────────────────────────────────────

// PdM Domain Pack
MERGE (dp1:DomainPack {id: 'pdm-pack-v1.0'})
SET dp1.name     = 'Predictive Maintenance Domain Pack',
    dp1.domain   = 'PredictiveMaintenance',
    dp1.version  = '1.0',
    dp1.ontology = 'STRIDE-HVAC-Ontology-v1.0';

// Procurement Domain Pack
MERGE (dp2:DomainPack {id: 'procurement-pack-v1.0'})
SET dp2.name     = 'Procurement Domain Pack',
    dp2.domain   = 'Procurement',
    dp2.version  = '1.0',
    dp2.ontology = 'Campus-Procurement-Ontology-v1.0';

// ── Reasoning Rule Nodes ──────────────────────────────────────

// PdM rules
MERGE (r1:ReasoningRule {rule_id: 'R-PdM-001'})
SET r1.name          = 'Temperature Anomaly Detection',
    r1.condition     = 'sensor.value > 33 AND sensor.type = Temperature',
    r1.trigger_type  = 'SensorAnomaly',
    r1.issue_type    = 'AssetRisk',
    r1.action_type   = 'MaintenanceRequired',
    r1.actor_role    = 'FacilityTechnician';

MERGE (r2:ReasoningRule {rule_id: 'R-PdM-002'})
SET r2.name          = 'Repeated Anomaly Detection',
    r2.condition     = 'anomalyCount > 3 WITHIN 7 DAYS',
    r2.trigger_type  = 'RepeatedAnomaly',
    r2.issue_type    = 'ComponentDegradation',
    r2.action_type   = 'ReplacementRequired',
    r2.actor_role    = 'MaintenanceManager';

MERGE (r3:ReasoningRule {rule_id: 'R-PdM-003'})
SET r3.name              = 'Cross-Domain Propagation Trigger',
    r3.condition         = 'action.type = ReplacementRequired',
    r3.trigger_type      = 'ProcurementSignal',
    r3.propagates_to     = 'procurement-pack-v1.0',
    r3.propagation_type  = 'cross_domain';

// Procurement rules
MERGE (r4:ReasoningRule {rule_id: 'R-PRO-001'})
SET r4.name          = 'Procurement Feasibility Check',
    r4.condition     = 'incoming.trigger = ProcurementSignal',
    r4.trigger_type  = 'ProcurementNeeded',
    r4.issue_type    = 'ProcurementFeasibility',
    r4.action_type   = 'PurchaseOrderCreation',
    r4.actor_role    = 'ProcurementOfficer';

MERGE (r5:ReasoningRule {rule_id: 'R-PRO-002'})
SET r5.name          = 'Budget Constraint Escalation',
    r5.condition     = 'budget.remaining < order.estimated_cost',
    r5.trigger_type  = 'BudgetConstraint',
    r5.issue_type    = 'BudgetApprovalRequired',
    r5.action_type   = 'ManagerApproval',
    r5.actor_role    = 'DepartmentManager';

// ── Link Rules to Packs ───────────────────────────────────────

MATCH (dp1:DomainPack {id: 'pdm-pack-v1.0'})
MATCH (r1:ReasoningRule {rule_id: 'R-PdM-001'})
MATCH (r2:ReasoningRule {rule_id: 'R-PdM-002'})
MATCH (r3:ReasoningRule {rule_id: 'R-PdM-003'})
MERGE (dp1)-[:CONTAINS_RULE]->(r1)
MERGE (dp1)-[:CONTAINS_RULE]->(r2)
MERGE (dp1)-[:CONTAINS_RULE]->(r3);

MATCH (dp2:DomainPack {id: 'procurement-pack-v1.0'})
MATCH (r4:ReasoningRule {rule_id: 'R-PRO-001'})
MATCH (r5:ReasoningRule {rule_id: 'R-PRO-002'})
MERGE (dp2)-[:CONTAINS_RULE]->(r4)
MERGE (dp2)-[:CONTAINS_RULE]->(r5);

// ── TIAA Event Nodes ──────────────────────────────────────────

// PdM TIAA chain
MERGE (t1:TIAAEvent {id: 'TIAA-PdM-T001'})
SET t1.stage       = 'Trigger',
    t1.domain      = 'PredictiveMaintenance',
    t1.pack_id     = 'pdm-pack-v1.0',
    t1.description = 'Sensor anomaly: Temperature > 33C';

MERGE (i1:TIAAEvent {id: 'TIAA-PdM-I001'})
SET i1.stage       = 'Issue',
    i1.domain      = 'PredictiveMaintenance',
    i1.pack_id     = 'pdm-pack-v1.0',
    i1.description = 'Asset risk: HVAC component degradation';

MERGE (a1:TIAAEvent {id: 'TIAA-PdM-A001'})
SET a1.stage       = 'Action',
    a1.domain      = 'PredictiveMaintenance',
    a1.pack_id     = 'pdm-pack-v1.0',
    a1.description = 'Component replacement required';

MERGE (ac1:TIAAEvent {id: 'TIAA-PdM-AC001'})
SET ac1.stage       = 'Actor',
    ac1.domain      = 'PredictiveMaintenance',
    ac1.pack_id     = 'pdm-pack-v1.0',
    ac1.description = 'Assigned: Facility Technician';

// Procurement TIAA chain (cross-domain)
MERGE (t2:TIAAEvent {id: 'TIAA-PRO-T001'})
SET t2.stage            = 'Trigger',
    t2.domain           = 'Procurement',
    t2.pack_id          = 'procurement-pack-v1.0',
    t2.description      = 'Procurement needed: replacement part required',
    t2.propagated_from  = 'TIAA-PdM-A001';

MERGE (i2:TIAAEvent {id: 'TIAA-PRO-I001'})
SET i2.stage       = 'Issue',
    i2.domain      = 'Procurement',
    i2.pack_id     = 'procurement-pack-v1.0',
    i2.description = 'Procurement feasibility assessed';

MERGE (a2:TIAAEvent {id: 'TIAA-PRO-A001'})
SET a2.stage       = 'Action',
    a2.domain      = 'Procurement',
    a2.pack_id     = 'procurement-pack-v1.0',
    a2.description = 'Purchase order creation initiated';

MERGE (ac2:TIAAEvent {id: 'TIAA-PRO-AC001'})
SET ac2.stage       = 'Actor',
    ac2.domain      = 'Procurement',
    ac2.pack_id     = 'procurement-pack-v1.0',
    ac2.description = 'Assigned: Procurement Officer';

// ── TIAA Relationships ────────────────────────────────────────

// PdM chain
MATCH (t1:TIAAEvent {id: 'TIAA-PdM-T001'})
MATCH (i1:TIAAEvent {id: 'TIAA-PdM-I001'})
MATCH (a1:TIAAEvent {id: 'TIAA-PdM-A001'})
MATCH (ac1:TIAAEvent {id: 'TIAA-PdM-AC001'})
MERGE (t1)-[:RESOLVES_TO]->(i1)
MERGE (i1)-[:TRIGGERS_ACTION]->(a1)
MERGE (a1)-[:ASSIGNED_TO]->(ac1);

// Cross-domain propagation: PdM Action → Procurement Trigger
MATCH (a1:TIAAEvent  {id: 'TIAA-PdM-A001'})
MATCH (t2:TIAAEvent  {id: 'TIAA-PRO-T001'})
MERGE (a1)-[:PROPAGATES_TO {cross_domain: true, from_pack: 'pdm-pack-v1.0', to_pack: 'procurement-pack-v1.0'}]->(t2);

// Procurement chain
MATCH (t2:TIAAEvent  {id: 'TIAA-PRO-T001'})
MATCH (i2:TIAAEvent  {id: 'TIAA-PRO-I001'})
MATCH (a2:TIAAEvent  {id: 'TIAA-PRO-A001'})
MATCH (ac2:TIAAEvent {id: 'TIAA-PRO-AC001'})
MERGE (t2)-[:RESOLVES_TO]->(i2)
MERGE (i2)-[:TRIGGERS_ACTION]->(a2)
MERGE (a2)-[:ASSIGNED_TO]->(ac2);

// ── Provenance Activity Nodes (PROV-O style) ──────────────────

MERGE (p1:ProvActivity {id: 'PROV-001'})
SET p1.tiaa_event  = 'TIAA-PdM-T001',
    p1.pack_id     = 'pdm-pack-v1.0',
    p1.type        = 'prov:Activity',
    p1.label       = 'SensorAnomalyDetection';

MERGE (p2:ProvActivity {id: 'PROV-002'})
SET p2.tiaa_event  = 'TIAA-PdM-A001',
    p2.pack_id     = 'pdm-pack-v1.0',
    p2.type        = 'prov:Activity',
    p2.label       = 'MaintenanceActionGeneration';

MERGE (p3:ProvActivity {id: 'PROV-003'})
SET p3.tiaa_event  = 'TIAA-PRO-T001',
    p3.pack_id     = 'procurement-pack-v1.0',
    p3.type        = 'prov:Activity',
    p3.label       = 'CrossDomainPropagation';

MERGE (p4:ProvActivity {id: 'PROV-004'})
SET p4.tiaa_event  = 'TIAA-PRO-A001',
    p4.pack_id     = 'procurement-pack-v1.0',
    p4.type        = 'prov:Activity',
    p4.label       = 'PurchaseOrderGeneration';

MATCH (p1:ProvActivity {id: 'PROV-001'})
MATCH (p2:ProvActivity {id: 'PROV-002'})
MATCH (p3:ProvActivity {id: 'PROV-003'})
MATCH (p4:ProvActivity {id: 'PROV-004'})
MERGE (p1)-[:PROV_GENERATED]->(p2)
MERGE (p2)-[:PROV_GENERATED {cross_domain: true}]->(p3)
MERGE (p3)-[:PROV_GENERATED]->(p4);

// ── Verify Schema ─────────────────────────────────────────────

MATCH (dp:DomainPack)
RETURN dp.id AS pack, dp.domain AS domain, dp.version AS version
ORDER BY dp.domain;
