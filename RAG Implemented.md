Listed directory ingestion
Listed directory sources
Listed directory playbooks
Listed directory repositories
Listed directory backend
Listed directory db
Listed directory models
Viewed knowledge_chunk.py:1-78
Viewed knowledge_document.py:1-75
Viewed candidate_memory.py:1-61
Viewed knowledge_tag.py:1-55
Viewed integration.py:1-800
Viewed retrieval_pipeline.py:1-412
Viewed memory_pipeline.py:1-124
Viewed memory_decay.py:1-84
Viewed retrieval_ranker.py:1-107

Here's a precise breakdown of all the RAG techniques implemented, across **two distinct retrieval subsystems**:

---

## RAG Techniques Implemented

There are **two RAG pipelines** — one for **Knowledge Base** retrieval and one for **Long-Term Candidate Memory** retrieval.

---

### 📚 Pipeline 1: Knowledge Base RAG ([retrieval_pipeline.py](file:///Users/mithun/Downloads/braintrain/apps/api/app/ai/intelligence/retrieval/retrieval_pipeline.py))

Used to ground interview questions with domain knowledge.

#### 1. Naive / Dense RAG (Base class: `RetrievalPipeline`)
- Embeds the query → cosine distance search against `pgvector`
- **Index**: IVFFlat with 100 lists, `vector_cosine_ops`
- **Embedding dimension**: 1536 (OpenAI-compatible / bge-large / nomic)
- `similarity_threshold` gates out low-confidence results (default: 0.7)

#### 2. Metadata-Filtered RAG
- Pre-filters chunks by `domain`, `topic`, `difficulty` at the SQL level before vector scoring
- Tags taxonomy: `domain`, `difficulty`, `company`, `interview_type`, `topic` (stored in `KnowledgeTag` — many-to-many)
- Filters are composed with `AND` clauses, combined with vector ordering

#### 3. Hybrid RAG (`HybridRetrievalPipeline`)
- Runs **semantic search** + **keyword search** in parallel, then merges
- Keyword search uses PostgreSQL `ILIKE` on chunk text (top 5 tokens)
- Merge strategy: semantic results get priority; keyword-only matches get a +0.05 score boost; deduplication by `chunk_id`

#### 4. Reranking
After retrieval, a second-pass rerank:
- +0.10 boost for exact domain match
- +0.10 boost for exact topic match
- +0.05 boost for authoritative source flag in metadata
- **Diversity filter**: max 3 chunks per source document (prevents one document dominating context)

#### 5. Token-Budgeted Context Building
- Context assembled in character-budget mode: `max_tokens * 4 chars`
- Chunks inserted in ranked order, truncated when budget is exhausted
- Each chunk tagged with source title, domain, topic for grounding

---

### 🧠 Pipeline 2: Long-Term Candidate Memory RAG ([memory_pipeline.py](file:///Users/mithun/Downloads/braintrain/apps/api/app/ai/voice/memory/memory_pipeline.py))

Used to recall past behavioral patterns, hesitations, strengths across sessions.

#### 6. Memory-Augmented RAG
- Candidate memories stored with 1536-dim embeddings in `candidate_memories` table
- At turn time, past memories are retrieved and injected as a `Candidate Historical Behavior Context` block

#### 7. Time-Decayed RAG
[`memory_decay.py`](file:///Users/mithun/Downloads/braintrain/apps/api/app/ai/voice/memory/memory_decay.py) applies **exponential decay** to memory relevance:
```
R(t) = base_relevance × e^(−decay_rate × days_since_created)
```
Decay is mitigated by:
- Higher `importance_score`
- Higher `access_count` (reinforcement on retrieval)
- Memory type: `SEMANTIC` decays slowest (0.3×), `BEHAVIORAL` medium (0.5×), `EPISODIC` fastest

#### 8. Multi-Signal Composite Reranking
[`retrieval_ranker.py`](file:///Users/mithun/Downloads/braintrain/apps/api/app/ai/voice/memory/retrieval_ranker.py) uses a **weighted composite score**:

| Signal | Weight |
|---|---|
| Semantic similarity | 0.45 |
| Importance score | 0.20 |
| Time decay penalty | −0.15 |
| Recency | 0.15 |
| Access frequency | 0.05 |
| Context-phase boost | dynamic |

#### 9. Context-Phase-Aware Retrieval (`RetrievalPolicies`)
- Memories are boosted based on the active interview phase:
  - `SYSTEM_DESIGN` phase → boosts architecture/system memory tags
  - `BEHAVIORAL` phase → boosts communication/leadership tags
  - `PRESSURE_ROUND` → boosts hesitation/stress/confidence memory tags
- This is a form of **conditional/adaptive RAG**

#### 10. Memory Extraction via LLM (Write path)
At session end, `SessionSummarizer` uses an LLM to extract structured memory objects from the full conversation transcript — these are then embedded and persisted for future sessions.

#### 11. Memory Compaction
`MemoryCompactor` deduplicates and merges semantically similar memories across sessions, preventing redundant context injection.

---

### Summary Table

| Technique | Where |
|---|---|
| Dense Vector RAG | `RetrievalPipeline` (pgvector cosine) |
| Metadata-Filtered RAG | SQL filters + vector sort |
| Hybrid RAG (semantic + keyword) | `HybridRetrievalPipeline` |
| Score-based Reranking + Diversity | `_rerank()` |
| Token-Budgeted Context Assembly | `build_context()` |
| Memory-Augmented RAG | `MemoryPipeline` |
| Time-Decayed RAG | `MemoryDecay` (exponential decay) |
| Multi-Signal Composite Reranking | `RetrievalRanker` (5-signal formula) |
| Context-Phase-Aware Retrieval | `RetrievalPolicies` + context boost |
| LLM-based Memory Extraction | `SessionSummarizer` |
| Memory Compaction | `MemoryCompactor` |