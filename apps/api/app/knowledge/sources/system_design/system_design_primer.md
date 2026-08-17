# System Design Primer Questions

This document is compiled from the System Design Primer (donnemartin/system-design-primer) and standard system design questions from roadmap.sh. These questions are used by top companies to evaluate architectural thinking, scalability, database choices, load balancing, caching, and fault tolerance.

## Question 1: Design a Distributed Metrics Logging and Aggregation System
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, Facebook, Amazon, eBay, Datadog, Atlassian
- **Key Concepts**: Time-series databases, agent-collector architecture, pull vs. push metrics collection, buffer queues (Kafka), stream processing, retention policies.

## Question 2: Design a Distributed Stream Processing System like Kafka
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Amazon, Microsoft, Wise, Confluent
- **Key Concepts**: Append-only log file, message partitioning, consumer group offset tracking, replication & high-availability, zero-copy reads, ZooKeeper/KRaft consensus.

## Question 3: Design a Key-Value Store
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Apple, Google, Canva, Avalara, Rubrik, OpenDoor
- **Key Concepts**: Consistent hashing, replication, vector clocks (versioning), gossip protocol for membership, LSM-trees or B-Trees storage, SSTables, Bloom filters.

## Question 4: Identify the K Most Shared Articles in Various Time Windows (24 hours, 1 hour, 5 minutes)
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: LinkedIn, Facebook, Twitter
- **Key Concepts**: Sliding window count, count-min sketch, top-K heap structures, map-reduce stream processing, real-time analytics pipelines.

## Question 5: Design an API Rate Limiter
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Amazon, Atlassian, Uber, Patreon, Microsoft, Stripe, Headway, Reputation dot com, Pinterest
- **Key Concepts**: Token bucket, leaky bucket, sliding window logs, sliding window counter algorithms, Redis integration, race condition handling using Lua scripts.

## Question 6: System to Collect Performance Metrics from Thousands of Servers
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, Datadog, Amazon, eBay, LinkedIn
- **Key Concepts**: Time-series ingestion pipelines, agent daemon, push vs. pull architecture (Prometheus style vs. Telegraf style), data rollups & downsampling, alerting thresholds.

## Question 7: Design Google Calendar
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, LinkedIn
- **Key Concepts**: DB schema for recurring events, search query indexing (Elasticsearch), calendar sharing permissions, notification queue, synchronization protocols (CalDAV).

## Question 8: Design a Distributed Queue like RabbitMQ
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Amazon, Apple, Instacart
- **Key Concepts**: AMQP protocol, exchanges (Direct, Fanout, Topic, Headers), message acknowledgment, dead-letter queues, cluster federation, persistent storage backends.

## Question 9: Design Google Analytics - User Analytics Dashboard and Pipeline
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Microsoft, Facebook, Qualtrics, Google
- **Key Concepts**: High-throughput ingestion (tracking pixel), stream processing pipelines (Flink/Spark), pre-aggregations, columnar storage (BigQuery/ClickHouse), low-latency dashboard query serving.

## Question 10: Design a System for Sorting Large Data Sets
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, Microsoft
- **Key Concepts**: External merge sort, MapReduce architecture, chunking, distributed storage systems (GFS/HDFS), worker node communication & fault tolerance.

## Question 11: Top K Elements: App Store Rankings, Amazon Bestsellers, etc.
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Amazon, Bloomberg, Facebook, Pinterest
- **Key Concepts**: Min-heap, MapReduce top-K calculation, stream-processing window aggregations, partition-wise top-K computation, caching strategies for read access.

## Question 12: Design Dropbox or Google Drive
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Dropbox, Facebook, Google, Amazon, Microsoft, OCI
- **Key Concepts**: Block-level sync, deduplication, metadata database sharding, notification service (long polling/WebSockets), offline editing handling, Amazon S3 storage integration.

## Question 13: Design a Job Scheduler
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, Amazon, Microsoft, Doordash, Netflix, Atlassian
- **Key Concepts**: Priority queues, distributed lock managers (ZooKeeper/Redis), cron parser, worker status monitoring, execution logs, retry & backoff policies.

## Question 14: Design a Notification Service at Scale
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, Pinterest, OCI, Stubhub, Amazon, Airbnb, Instacart
- **Key Concepts**: Multi-channel sending (SMS, Email, Push notifications), rate limiting/throttling per channel, prioritization (transactional vs. marketing), template rendering engine, provider fallback.

## Question 15: Surge Pricing System: Uber - Stream Processing, etc.
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Uber, Lyft
- **Key Concepts**: Geospatial indexing (H3, S2 geometry libraries), stream aggregation of ride requests and driver locations, dynamic pricing algorithm execution, low-latency key-value serving.

## Question 16: Netflix: Limit the Number of Screens Each User Can Watch
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Some FAANG
- **Key Concepts**: Heartbeat service, session state management (Redis), distributed locks, race conditions during concurrent logins, token verification.

## Question 17: Design an ETA Service and Location Sharing Between Driver and Rider
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Uber, Some FAANG
- **Key Concepts**: Location updates (WebSocket connections), geospatial database indexes, route estimation algorithms (Dijkstra, A* search, OSRM), pub-sub message routing.

## Question 18: Design a Hotel Booking System: Room Availability, Reservation, Booking
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Amazon, Square, Booking dot com
- **Key Concepts**: Handling double-booking, distributed transactions (Saga pattern or 2PC), inventory caching, database locking strategies (optimistic vs. pessimistic lock), payment processing integration.

## Question 19: Design an A/B Testing System (like Optimizely)
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Affirm, Some FAANG
- **Key Concepts**: Hashing function for deterministic user grouping, configuration rollout systems, real-time logs processing, statistical significance calculator, cache-friendly variation assignment.

## Question 20: Design a Price Alert System for Amazon (or for Stock prices)
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Facebook, Bloomberg, Coinbase, Swyftx, Trade Republic
- **Key Concepts**: Pub-sub event brokers, dynamic price feed ingestion, cron trigger vs. event-based evaluations, worker pool execution, scalable notification push.

## Question 21: Design an IoC/Dependency Injection Framework
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: ADP, Some FAANG
- **Key Concepts**: Reflection & annotation parsing, dependency graph creation, cycle detection (directed acyclic graphs), singleton vs. prototype lifecycle management.

## Question 22: Design a Credit Card Processing System
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Stripe, Paytm, Paypal, Databricks, Capital One
- **Key Concepts**: PCI-DSS compliance, tokenization, idempotency keys, dual-entry ledger design, integration with card networks (Visa/Mastercard), payment retry queues.

## Question 23: Count Facebook Likes, Especially for High-Profile Users
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Facebook, Amazon, Twitter
- **Key Concepts**: Write-back caching, counter sharding (avoiding database locks), message queues for async counting, MapReduce aggregates, read replication.

## Question 24: Design a Control Plane for a Distributed Database
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Netflix
- **Key Concepts**: Leader election, dynamic topology discovery, cluster health checking, remote configuration deployment, backup and restore coordination.

## Question 25: Design a User Login and Authentication System for a Website
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, Visa, Gusto
- **Key Concepts**: Password hashing (bcrypt, Argon2), JWT vs. session tokens, OAuth2 flows, multi-factor authentication (MFA), rate limiting on login attempts, session revocation mechanisms.

## Question 26: Develop a Weather Application
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Amazon, Chime, Facebook, Hubspot, Uber, Klaviyo
- **Key Concepts**: Weather data provider API aggregation, aggressive caching at edge (CDN), geographical lookup mapping, push notification alerts for severe weather.

## Question 27: Create a Document Management System like Wikipedia, Notion or Google Docs
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, Flipkart, Notion, Amazon
- **Key Concepts**: Operational Transformation (OT) or Conflict-Free Replicated Data Types (CRDT), search indexing (reverse index), revision history and diff engines, collaborative locking.

## Question 28: Build a Marketplace Feature for Facebook
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Facebook, Roblox
- **Key Concepts**: Elastic search indexing for location-based query filtering, media storage (CDN upload & resizing), messaging integration, fraud detection feeds.

## Question 29: Design a System to Monitor the Health of a Cluster
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Uber, Lacework, Amazon, Google
- **Key Concepts**: Heartbeat protocol, failure detection algorithms (Phi Accrual Failure Detector), gossip protocol for state propagation, monitoring dashboards.

## Question 30: Find a Rider for Uber or Uber Eats
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Facebook, Uber, Google, Microsoft
- **Key Concepts**: Location matching algorithms, spatial databases (PostGIS, Redis GEO), pub-sub channels for rider requests, matching dispatch optimization.

## Question 31: Design a Distributed Tracing System
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Uber, Amazon
- **Key Concepts**: Trace ID and Span ID propagation, context injection/extraction headers, asynchronous telemetry collectors (Jaeger/Zipkin style), sampling strategies (adaptive sampling).

## Question 32: Design Backend for an App to Distribute 6 Million Free Burgers in One Hour
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, Deliveroo
- **Key Concepts**: Managing massive traffic spikes (flash sale), queue-based throttling (virtual waiting rooms), database locks reduction, static asset CDNs.

## Question 33: Design a File Downloader Library
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Facebook
- **Key Concepts**: Multi-threaded block download, pause/resume file transfers using HTTP Range headers, local storage file locking, connection pool configuration.

## Question 34: Design a System to View Latest Stock Prices Worldwide
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, Bloomberg, Amazon
- **Key Concepts**: Low-latency multicast feeds, WebSocket push networks, in-memory databases (Redis/Memcached), message payload compression, read-heavy API scaling.

## Question 35: Develop a Photo Sharing Platform like Flickr or Google Photos
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, Doordash, Amazon, Uber, Facebook
- **Key Concepts**: Image uploading & scaling workers, CDN caching, metadata database sharding, asynchronous photo analyzer pipelines, storage cost tiers.

## Question 36: Design an On-Call Escalation System
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Uber
- **Key Concepts**: Escalation rules engine, scheduler rotations, notification providers integration (PagerDuty/Twilio), feedback acknowledgment state machine.

## Question 37: Design and Implement a Wire Transfer API
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, Capital One, Revolut
- **Key Concepts**: Transaction isolation levels (Serializable), lock handling, idempotency enforcement, dual-entry accounting ledger system, audit trails.

## Question 38: Design a Live Comments Feature for Facebook
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Facebook
- **Key Concepts**: Pub-sub push architecture (WebSockets/Server-Sent Events), hot-post scaling strategy (fanout handling), edge caching, message pagination.

## Question 39: Design a Feature to Show the Number of Users Viewing a Page
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Booking dot com
- **Key Concepts**: Approximate counting algorithms (HyperLogLog), active connection heartbeats, Redis sliding window counters, stream event aggregation.

## Question 40: Design Facebook Likes Feature with Live Updates
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Facebook, Coinbase
- **Key Concepts**: Real-time counter increments, message broker fan-out, event-driven updates, cache writeback routines, localized replication feeds.

## Question 41: Create a System to Migrate Large Data to Google Cloud
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, OCI
- **Key Concepts**: Offline data transfer (Transfer Appliance), network compression, data integrity checksum verification (MD5), parallel streaming transfers, cloud storage ingestion pipelines.

## Question 42: Design a Distributed Botnet
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Facebook, Lyft
- **Key Concepts**: Command and Control (C&C) patterns, DNS fluxing, fallback coordination systems, decentralized peer-to-peer (P2P) network nodes.

## Question 43: Create a Distributed File Transfer System like Bittorrent
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Google, Atlassian, Twitch
- **Key Concepts**: BitTorrent protocol, torrent file parsing, DHT (Distributed Hash Table) lookup, peer discovery trackers, block verification, tit-for-tat scheduling algorithms.

## Question 44: Design a Parts Compatibility Feature for an eCommerce Site
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Some FAANG
- **Key Concepts**: Graph database structures (nodes representing parts/vehicles), relation parsing algorithms, scale-out read queries, matrix lookup caching.

## Question 45: Develop an Ads Management and Display System for a Social Feed
- **Source Reference**: donnemartin/system-design-primer & roadmap.sh
- **Asked By Companies**: Facebook, Google, Amazon, Pinterest
- **Key Concepts**: Ad indexing & retrieval matching engine, pacing algorithms, bidding auctions (Vickrey-Clarke-Groves), impression event tracker, click fraud detection stream processing.
