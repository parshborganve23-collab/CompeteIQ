\# Hindsight Memory Integration — CompeteIQ



\## 1. Overview



Hindsight provides long-term memory capabilities for CompeteIQ.



It helps the application retain historical competitor intelligence and use relevant past information during future analysis.



\## 2. Main Memory Operations



\### Retain

Stores competitor intelligence and historical information in memory.



\### Recall

Retrieves relevant information from previously stored memories.



\### Reflect

Uses stored information to generate insights and support strategic reasoning.



\## 3. Memory Workflow



1\. Competitor information is submitted.

2\. Relevant information is retained.

3\. A future analysis request triggers memory recall.

4\. Relevant historical information is retrieved.

5\. Reflection generates insights.

6\. The application can use those insights in recommendations.



\## 4. Configuration



Configure the following settings locally:



\- HINDSIGHT\_API\_KEY

\- HINDSIGHT\_TIMEOUT\_SECONDS



The integration also uses a configured Hindsight service endpoint.



Keep credentials inside your local .env file. Never publish API keys.



\## 5. Verification



Test these three operations:



\- Retain a competitor event.

\- Recall the stored event.

\- Reflect on retrieved information.



Capture genuine screenshots of successful operations.



\## 6. Why Hindsight Matters



Without memory, an AI system may analyze each request independently.



With long-term memory, CompeteIQ can use previous competitor events and historical context to support future analysis.



Note: Successful live memory operations require valid configuration and credentials.

