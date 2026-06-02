import asyncio
import logging
from sqlalchemy import select, delete
from app.db.session import SessionLocal
from app.db.models.knowledge_document import KnowledgeDocument
from app.db.models.knowledge_chunk import KnowledgeChunk
from app.modules.knowledge.service import KnowledgeDocumentService
from app.modules.knowledge.schemas import KnowledgeDocumentCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag_ingest")

CURATED_DOCUMENTS = [
    # ── BACKEND ENGINEERING ──
    {
        "title": "Backend Interview Guide: Caching Strategies and Redis",
        "source": "curated/backend/caching.md",
        "source_type": "markdown",
        "domain": "backend",
        "topic": "caching",
        "difficulty": "MEDIUM",
        "content": """
# Caching Strategies & Redis Tradeoffs

## Cache-Aside (Lazy Loading)
- **Concept**: Application query cache first. If a miss occurs, query DB, update cache, and return.
- **Tradeoffs**:
  - Pros: Only cache what is requested. DB/cache failures are isolated.
  - Cons: Three-turn round trips for misses. Cache thrashing or stale data if updates skip cache.
  - Mitigations: Always set appropriate TTL. Write to cache on database updates.

## Write-Through Cache
- **Concept**: Application updates the cache first, and the cache immediately writes through to the database synchronously.
- **Tradeoffs**:
  - Pros: Data is never stale. Reads are always fast.
  - Cons: Write latency is higher (sync DB write). Redundant cache writes for rarely read data.

## Write-Behind (Write-Back) Cache
- **Concept**: Application updates cache. Cache queues DB write asynchronously.
- **Tradeoffs**:
  - Pros: Extremely high write performance and throughput.
  - Cons: Risk of data loss if cache fails before flushing to DB. Eventual consistency window.

## Redis Eviction Policies
- **volatile-lru**: Remove least recently used keys with expire set.
- **allkeys-lru**: Remove least recently used keys across all keys.
- **volatile-ttl**: Remove keys with shortest time-to-live remaining.
- **noeviction**: Return error on write when memory is full (safe for DB-backed caches).
"""
    },
    {
        "title": "Backend Interview Guide: Database Concurrency and Deadlocks",
        "source": "curated/backend/database_concurrency.md",
        "source_type": "markdown",
        "domain": "backend",
        "topic": "database",
        "difficulty": "HARD",
        "content": """
# Database Concurrency, Isolation Levels, and Deadlocks

## Transaction Isolation Levels (ANSI SQL-92)
1. **Read Uncommitted**: Allows Dirty Reads. One transaction reads uncommitted changes of another.
2. **Read Committed**: Prevents Dirty Reads. Allows Non-repeatable Reads (data changes between reads).
3. **Repeatable Read**: Prevents Dirty/Non-repeatable reads. Allows Phantom Reads (new rows added).
4. **Serializable**: Prevents all anomalies. Complete serialization of concurrent transactions.

## Deadlock Prevention and Resolution
- **Definition**: Mutual blockage where Transaction A locks Row 1 and waits for Row 2, while Transaction B locks Row 2 and waits for Row 1.
- **Detection**: DB engine builds dependency graphs and kills the transaction with the least cost/work done.
- **Prevention Tactics**:
  - Always acquire locks in the same deterministic order.
  - Keep transactions short and limit user interaction inside locks.
  - Use appropriate lower isolation levels if application logic allows.
  - Implement optimistic concurrency control (OCC) using version columns.
"""
    },
    # ── FRONTEND ENGINEERING ──
    {
        "title": "Frontend Interview Guide: React Performance and Fiber",
        "source": "curated/frontend/react_performance.md",
        "source_type": "markdown",
        "domain": "frontend",
        "topic": "react",
        "difficulty": "HARD",
        "content": """
# React Performance, Fiber Architecture, and Optimization

## Fiber Engine Architecture
- **Fiber**: A unit of work that can be paused, aborted, or reused. It replaces the synchronous stack-based reconciler.
- **Phases**:
  - **Render Phase**: Asynchronous, interruptible. Builds the work-in-progress fiber tree. Compares virtual DOM nodes.
  - **Commit Phase**: Synchronous, uninterruptible. Applies changes to the actual DOM.

## Common Performance Bottlenecks and Hooks
- **Unnecessary Re-renders**: Triggered by parent updates or changing object references.
- **useMemo**: Memoizes computationally expensive return values. Only use when recalculation is heavy.
- **useCallback**: Memoizes function reference. Critical when passing callback functions to memoized child components (`React.memo`) to maintain referential equality.
- **Virtualization**: Rendering only visible items in a massive list (e.g., react-window, react-virtualized) to minimize DOM nodes and memory footprints.
"""
    },
    {
        "title": "Frontend Interview Guide: Core Web Vitals and Performance",
        "source": "curated/frontend/web_performance.md",
        "source_type": "markdown",
        "domain": "frontend",
        "topic": "web_performance",
        "difficulty": "MEDIUM",
        "content": """
# Optimizing Core Web Vitals (LCP, INP, CLS)

## Largest Contentful Paint (LCP)
- **Definition**: Measures perceived loading speed. Marks the point in page load when main content is likely loaded.
- **Target**: Under 2.5 seconds.
- **Optimizations**:
  - Eliminate render-blocking JS and CSS.
  - Optimize images: Next-gen formats (WebP/AVIF), responsive sizes, prioritize hero image loading using `fetchpriority="high"`.
  - Server-side rendering (SSR) or Static Site Generation (SSG).

## Interaction to Next Paint (INP)
- **Definition**: Replaces FID. Measures user interface responsiveness. Evaluates the latency of all interactions (clicks, taps, keyboard inputs) throughout the session.
- **Target**: Under 200 milliseconds.
- **Optimizations**:
  - Yield main thread using `setTimeout` or `requestIdleCallback` for non-critical work.
  - Split long-running JS tasks into smaller chunks.
  - Minimize layout thrashing by avoiding inline style lookups after modifications.
"""
    },
    # ── SYSTEM DESIGN ──
    {
        "title": "System Design Guide: Distributed Rate Limiters",
        "source": "curated/system_design/rate_limiter.md",
        "source_type": "markdown",
        "domain": "system_design",
        "topic": "distributed_systems",
        "difficulty": "HARD",
        "content": """
# Designing a Distributed Rate Limiter

## Token Bucket Algorithm
- **Concept**: A bucket holds tokens, refilled at a constant rate. Each request consumes one token. If empty, request is dropped.
- **Tradeoffs**: Allows sudden bursts of traffic, but memory efficient.

## Leaky Bucket Algorithm
- **Concept**: Requests enter a queue and leak out at a constant rate. If queue is full, request is dropped.
- **Tradeoffs**: Smooths out traffic spikes, but can delay requests.

## Sliding Window Counter (Redis Sorted Sets)
- **Concept**: Track timestamps of requests in a sliding window using Redis Sorted Sets (`ZADD`, `ZREMRANGEBYSCORE`).
- **Tradeoffs**: Extremely accurate, prevents boundary double-limits, but has higher memory footprint than token bucket.

## Distributed Consistency Challenges
- **Race Conditions**: Multi-server setups concurrency can lead to double-spends of tokens. Resolve using Redis Lua scripts (runs atomically) or lock-free cell algorithms.
- **Multi-region Synchronization**: Sync bucket counts across regions asynchronously to prevent write latency, or direct user to localized regional rate limiters.
"""
    },
    # ── AI ENGINEERING ──
    {
        "title": "AI Engineering Guide: RAG Optimization and Vector Search",
        "source": "curated/ai_engineering/rag_optimization.md",
        "source_type": "markdown",
        "domain": "ai_engineering",
        "topic": "rag",
        "difficulty": "HARD",
        "content": """
# Advanced RAG Optimization and Vector Search

## Document Chunking Strategies
- **Fixed-size Chunking**: Simple split by word/token count with overlap.
- **Semantic/Recursive Chunking**: Split based on document structure (headers, paragraphs, sentences) to preserve context boundaries.
- **Metadata Enhancement**: Ingesting titles, summaries, and parent headers alongside the chunk text to maintain context during dense search.

## Vector Search Indexing in Postgres (pgvector)
- **Cosine Distance vs L2 Distance**: Use cosine distance for directional similarity ignoring text length; L2 for absolute coordinate offsets.
- **IVFFlat Index**: Speeds up search by partitioning vectors into lists. Requires rebuilding index periodically as data grows.
- **HNSW (Hierarchical Navigable Small World)**: Graph-based index. Offers better recall/speed tradeoff than IVFFlat but requires higher memory.
- **Hybrid Retrieval**: Combine dense vector search with BM25 / lexical full-text keyword search (`to_tsquery` or `ILIKE`) using Reciprocal Rank Fusion (RRF) to get the best of both semantics and keyword exactness.
"""
    }
]

async def run_ingestion():
    db_session = SessionLocal()
    async with db_session as db:
        logger.info("Starting ingestion of curated mock interview Q&A documents...")
        
        for doc_data in CURATED_DOCUMENTS:
            # Check if document already exists by title
            stmt = select(KnowledgeDocument).where(KnowledgeDocument.title == doc_data["title"])
            res = await db.execute(stmt)
            existing_doc = res.scalar_one_or_none()
            
            if existing_doc:
                logger.info(f"Document '{doc_data['title']}' already exists. Recreating...")
                await db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == existing_doc.id))
                await db.delete(existing_doc)
                await db.commit()
            
            # Create the document using the service (handles chunking, token estimation, and embedding generation)
            schema = KnowledgeDocumentCreate(
                title=doc_data["title"],
                source=doc_data["source"],
                source_type=doc_data["source_type"],
                domain=doc_data["domain"],
                topic=doc_data["topic"],
                difficulty=doc_data["difficulty"],
                content=doc_data["content"],
                meta_data={"authoritative": True}
            )
            
            try:
                doc = await KnowledgeDocumentService.create_document(db, schema)
                logger.info(f"Successfully ingested '{doc.title}' into {doc.chunk_count} chunks.")
            except Exception as e:
                logger.error(f"Failed to ingest document '{doc_data['title']}': {e}", exc_info=True)
                
        logger.info("Ingestion completed successfully.")

if __name__ == "__main__":
    asyncio.run(run_ingestion())
