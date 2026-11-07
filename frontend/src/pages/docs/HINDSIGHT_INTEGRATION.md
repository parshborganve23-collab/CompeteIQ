# Hindsight Memory Integration — CompeteIQ

## 1. Overview

Hindsight provides long-term memory capabilities for CompeteIQ. It helps the application retain historical intelligence and use relevant past information during future analysis.

## 2. Main Memory Operations

### Retain
Stores competitor intelligence and historical information in memory.

### Recall
Retrieves relevant information from previously stored memories.

### Reflect
Uses stored information to generate insights and support strategic reasoning.

## 3. Memory Workflow

1. Competitor information is submitted.
2. Relevant information is retained in Hindsight.
3. A future analysis request triggers memory recall.
4. Relevant historical information is retrieved.
5. Reflection helps generate insights using the stored information.
6. The application can use those insights in its recommendations.

## 4. Configuration

Configure the following environment settings locally:

- `HINDSIGHT_API_KEY`
- `HINDSIGHT_TIMEOUT_SECONDS`

The integration also uses the configured Hindsight service endpoint.

Keep credentials in your local `.env` file. Never commit secrets to GitHub.

## 5. Verification

Test the three operations:

- Retain a competitor event.
- Recall the stored event.
- Reflect on the retrieved information.

Capture genuine screenshots of successful operations.

## 6. Why Hindsight Matters

Without memory, an AI agent may analyze each request independently.

With long-term memory, CompeteIQ can use previous competitor events and historical context to improve future analysis.

**Note:** Successful live memory operations must be verified with a configured Hindsight service and valid credentials.