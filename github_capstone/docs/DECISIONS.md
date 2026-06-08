# Design Decisions
## GitHub Events Data Pipeline — Databricks Free Edition

This document explains the key technical decisions made during the design and
implementation of the pipeline, including the reasoning behind each choice and
the trade-offs considered.

---

## 1. Lakeflow SDP (Delta Live Tables) over Plain Structured Streaming

**Decision:** Use Lakeflow SDP declarative pipeline framework instead of manually
written Structured Streaming jobs.

**Reasoning:**
- SDP handles pipeline orchestration, dependency resolution, and execution order
  automatically. The Bronze → Silver → Gold dependency chain is inferred from
  `dlt.read()` and `dlt.read_stream()` calls — no manual wiring required.
- Built-in data quality enforcement via `@dlt.expect_or_fail` and
  `@dlt.expect_or_drop` decorators. Writing equivalent logic manually in
  Structured Streaming would require significantly more boilerplate code.
- Automatic lineage tracking and a visual pipeline graph in the UI — valuable for
  debugging, monitoring, and demonstrating the pipeline to stakeholders.
- Expectation metrics (pass/fail counts) are logged automatically and visible in
  the pipeline UI without any additional instrumentation.
- SDP is the current Databricks-recommended approach for Medallion Architecture
  pipelines and is fully supported in Free Edition.

**Trade-off:** SDP adds a layer of abstraction that can make debugging harder when
errors occur inside the framework. Plain Structured Streaming gives more direct
control but requires significantly more code.

---

## 2. Batch Read in Silver (`dlt.read`) Instead of Streaming (`dlt.read_stream`)

**Decision:** Silver reads Bronze data using `dlt.read()` (batch) rather than
`dlt.read_stream()` (streaming).

**Reasoning:**
- The original TDD specified `dlt.read_stream()` for Silver with a
  `ROW_NUMBER()` window function for deduplication. During implementation this
  caused a runtime error:
  `[NON_TIME_WINDOW_NOT_SUPPORTED_IN_STREAMING]`.
- Spark Structured Streaming does not support non-time-based window functions
  like `ROW_NUMBER()` on streaming DataFrames.
- Switching to `dlt.read()` allows the full deduplication window function to work
  correctly because Silver can see all Bronze records at once.
- This also provides stronger deduplication guarantees — duplicates are detected
  across all historical data, not just within a single batch.
- Given the ingestion frequency (once daily, 100 events per run), the dataset
  remains small enough that full recomputation is acceptable.

**Trade-off:** Silver recomputes fully on each run rather than processing only
new records incrementally. This is acceptable at current scale but would require
revisiting for higher-volume ingestion.

---

## 3. Volume-Based Storage over DBFS

**Decision:** All raw storage uses Unity Catalog Volumes instead of DBFS.

**Reasoning:**
- DBFS root and DBFS mounts are unavailable in Databricks Free Edition.
- Unity Catalog Volumes are the modern Databricks-recommended storage abstraction.
- Volumes integrate with governance, lineage, and access control capabilities.
- Volumes fully support Auto Loader incremental ingestion patterns.

**Trade-off:** None in this environment. Volumes are strictly superior within
Databricks Free Edition.

---

## 4. Unique File Naming Strategy (Timestamp + UUID)

**Decision:** Each ingestion run produces uniquely named JSON files using a
timestamp and UUID suffix.

**Reasoning:**
- Auto Loader tracks processed files via checkpoint metadata.
- Overwriting an existing file would prevent Auto Loader from reprocessing it.
- Unique filenames guarantee every ingestion run is detectable.
- Timestamp improves readability and chronological sorting.
- UUID suffix prevents collisions between rapid executions.

**Trade-off:** Raw storage accumulates append-only historical snapshots indefinitely.
Production environments would require lifecycle management or cleanup policies.

---

## 5. Decoupled Ingestion and Processing

**Decision:** Ingestion and SDP processing are fully decoupled through raw landing
Volumes.

**Reasoning:**
- API outages or rate limits do not block SDP processing of previously ingested
  data.
- SDP failures do not prevent ingestion from continuing to land raw snapshots.
- Components can be debugged, rerun, and evolved independently.
- The raw Volume acts as a durable ingestion buffer.

**Trade-off:** Adds one extra storage layer between ingestion and transformation.

---

## 6. Rate Limit Handling with Graceful Exit

**Decision:** GitHub API rate limits trigger controlled notebook exits using
`dbutils.notebook.exit("RATE_LIMITED")`.

**Reasoning:**
- Rate limiting is a temporary operational condition, not a code failure.
- Controlled exits distinguish operational throttling from true ingestion errors.
- Downstream tasks are prevented from running against incomplete enrichment data.
- Preserves workflow integrity without corrupting downstream layers.

**Trade-off:** Databricks Free Edition cannot currently treat RATE_LIMITED as a
successful workflow status, so these runs appear as failed in workflow history.

---

## 7. Partitioning Strategy

**Decision:** Silver events table is partitioned by `created_at_date`.

**Reasoning:**
- Most analytical queries filter by date ranges.
- Date partitioning enables partition pruning and reduces scan cost.
- Event timestamps naturally align with analytical usage patterns.

**Known Limitation:** Late-arriving events may land in historical partitions.
Future refactoring may switch to ingestion-date partitioning.

---

## 8. Single SDP Pipeline for All Layers

**Decision:** Bronze, Silver, and Gold layers run inside a single SDP pipeline.

**Reasoning:**
- Databricks Free Edition allows only one active SDP pipeline.
- A single pipeline provides unified lineage visualization.
- Dependency resolution is automatic across all notebooks.
- Operational complexity is reduced compared to coordinating multiple pipelines.

**Trade-off:** Failures in one layer stop the entire pipeline.

---

## 9. Gold Layer as Materialized Views

**Decision:** Gold datasets are implemented as Materialized Views using
`@dlt.materialized_view`.

**Reasoning:**
- Gold datasets are aggregation-oriented and recompute-friendly.
- Materialized Views refresh automatically whenever upstream data changes.
- Declarative Gold views align naturally with SDP semantics.
- Simplifies orchestration and removes manual refresh logic.

**Trade-off:** Materialized Views do not support OPTIMIZE or ZORDER operations.

---

## 10. Maximum Concurrent Runs Set to 1

**Decision:** Workflow concurrency is restricted to a single active run.

**Reasoning:**
- Prevents simultaneous writes into Silver and Gold layers.
- Eliminates checkpoint contention risks in Auto Loader.
- Guarantees deterministic sequential processing.
- Protects against accidental overlapping executions.

**Trade-off:** None for this workload profile.

---

## 11. Repository & User Enrichment as Separate Pipelines

**Decision:** Repository enrichment and user enrichment are implemented as
independent ingestion workflows.

**Reasoning:**
- Repository metadata and contributor metadata evolve independently.
- Failures in one enrichment domain do not block the other.
- Independent workflows improve debugging and operational isolation.
- Distinct Bronze/Silver enrichment layers preserve Medallion consistency.

**Trade-off:** Additional orchestration complexity and more pipeline objects.

---

## 12. Append-Only Enrichment Snapshots

**Decision:** Repository and user enrichment payloads are stored as immutable
append-only JSON snapshots.

**Reasoning:**
- Preserves historical metadata states for reproducibility.
- Enables replayability and auditing of enrichment runs.
- Maintains architectural consistency with raw event ingestion.
- Aligns with lakehouse append-only ingestion patterns.

**Trade-off:** Raw enrichment storage grows continuously over time.

---

## 13. Cross-Domain Semantic Gold Layer

**Decision:** Repository enrichment, contributor enrichment, and event activity
are unified in semantic Gold materialized views.

**Reasoning:**
- Enables cross-domain analytics spanning:
  - repository popularity
  - contributor influence
  - organizational participation
  - language ecosystems
  - temporal activity trends
- Centralizes business-facing analytics into reusable semantic datasets.
- Avoids repetitive joins in downstream analytical queries.

**Trade-off:** Gold views become more computationally expensive due to multi-table
joins.

---

## 14. Deterministic Silver-Layer Deduplication

**Decision:** Silver layers enforce deterministic deduplication using business keys
and `ROW_NUMBER()` window functions.

**Reasoning:**
- `event_id` uniquely identifies GitHub events.
- `repo_name` uniquely identifies repositories.
- `actor_login` uniquely identifies contributors.
- Window-based deduplication guarantees stable semantic joins.
- Provides logical idempotency across repeated workflow executions.

**Trade-off:** Full-table recomputation is required due to batch deduplication.

---

## 15. API Retry Strategy with Session Reuse

**Decision:** GitHub enrichment ingestion uses reusable HTTP sessions with retry
logic for transient failures.

**Reasoning:**
- Session reuse improves connection efficiency.
- Retry handling reduces sensitivity to transient 5xx API failures.
- Controlled retry behavior increases ingestion resilience.
- Granular exception handling improves operational observability.

**Trade-off:** Retry delays slightly increase total ingestion runtime.

---

## 16. Lightweight API Throttling

**Decision:** Enrichment ingestion applies lightweight throttling between API
requests.

**Reasoning:**
- Reduces burst pressure against GitHub API rate limits.
- Prevents accidental aggressive request spikes.
- Improves operational stability during enrichment runs.
- Aligns with GitHub API best practices.

**Trade-off:** Slightly slower ingestion throughput.

---

## 17. Semantic Validation Suite

**Decision:** Validation queries are implemented as a dedicated analytical
validation layer.

**Reasoning:**
- Verifies:
  - table materialization
  - semantic join completeness
  - deduplication correctness
  - enrichment coverage
  - idempotent behavior
- Provides operational confidence after workflow execution.
- Creates reusable acceptance testing artifacts.

**Trade-off:** Additional SQL maintenance overhead.

---

## 18. Idempotent Silver / Non-Idempotent Raw Design

**Decision:** Raw layers are append-only while Silver layers enforce logical
idempotency.

**Reasoning:**
- Raw historical snapshots should never be mutated or deleted.
- Silver layers provide stable business-facing entity representations.
- This aligns with standard Medallion Architecture principles:
  - Bronze preserves history
  - Silver normalizes and cleans
  - Gold aggregates and enriches

**Trade-off:** Raw storage grows indefinitely while Silver remains stable.

---

## 19. Workflow-Oriented Sequential Orchestration

**Decision:** Workflow dependencies enforce a strict sequential ingestion order.

**Reasoning:**
- Events must ingest before enrichment extraction.
- Repository enrichment must complete before user enrichment.
- SDP processing must only execute after all enrichment snapshots land.
- Sequential orchestration guarantees deterministic semantic joins.

**Trade-off:** Longer total workflow runtime compared to parallel execution.

---

## 20. Platform Scope Optimized for Databricks Free Edition

**Decision:** Architecture choices intentionally prioritize compatibility with
Databricks Free Edition constraints.

**Reasoning:**
- Free Edition lacks:
  - DBFS mounts
  - custom clusters
  - advanced orchestration options
  - multiple active pipelines
- Design decisions intentionally maximize platform capability within those limits.
- The project demonstrates production architectural concepts despite environment
  constraints.

**Trade-off:** Some production-scale optimizations are intentionally deferred.# workflow dispatch enabled

## Decision: Deployment Strategy for Databricks Free Edition

### Status

Accepted

### Context

As part of the project, a Continuous Deployment workflow was implemented using GitHub Actions. The goal was to automate Databricks Asset Bundle deployment using:

```bash
databricks bundle deploy --target dev
```

and optionally execute the deployed job using:

```bash
databricks bundle run gh_pipeline_job --target dev
```

The workflow was successfully created, configured, and executed within GitHub Actions.

### Investigation

Deployment failed during execution despite successful authentication and bundle validation.

Initial errors suggested insufficient token permissions. After updating token scopes and reconfiguring GitHub Secrets, the error changed and was isolated to a user identity lookup performed during deployment.

The failing endpoint was:

```text
/api/2.0/preview/scim/v2/Me
```

To determine whether the problem originated from GitHub Actions, Databricks Asset Bundles, or authentication, several tests were performed.

#### Test 1 - Bundle Validation

```bash
databricks bundle validate
```

Result:

Success.

Conclusion:

Bundle configuration was valid.

#### Test 2 - Local Deployment Using OAuth Authentication

```bash
databricks auth login
databricks bundle deploy --target dev
```

Result:

Success.

Conclusion:

Deployment logic and workspace configuration were valid.

#### Test 3 - PAT Authentication

Environment variables were configured using the same PAT stored in GitHub Secrets.

```bash
export DATABRICKS_HOST=<workspace>
export DATABRICKS_TOKEN=<PAT>
```

User lookup was tested using:

```bash
databricks current-user me
```

Result:

Authentication failed with:

```text
Credential was not sent or was of an unsupported type for this API
```

The same error appeared in GitHub Actions.

Conclusion:

The issue was reproduced outside GitHub Actions and therefore was not caused by workflow configuration.

### Findings

The investigation demonstrated the following:

| Authentication Method | Bundle Validate | Bundle Deploy |
| --------------------- | --------------- | ------------- |
| OAuth Login           | Success         | Success       |
| PAT Authentication    | Success         | Failure       |

The failure occurs during account-level identity resolution required by Databricks Asset Bundle deployment.

Databricks Free Edition does not support the account-level functionality required for Service Principals, SCIM identity APIs, or OIDC-based automation.

### Decision

The GitHub Actions deployment workflow was removed from the project.

Continuous Integration remains fully implemented through:

* Databricks Bundle Validation
* Automated pytest execution
* GitHub Actions workflow automation

Deployment will be performed manually from the local development environment using OAuth authentication.

### Consequences

Benefits:

* Reliable deployment process
* Full compatibility with Databricks Free Edition
* Stable CI pipeline

Trade-offs:

* Deployment is not fully automated
* Deployment requires a locally authenticated user session

### Future Considerations

If the project is migrated to a Standard, Premium, or Enterprise Databricks environment, deployment automation should be revisited using Service Principals and OIDC authentication.
