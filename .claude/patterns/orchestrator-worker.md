# PAT-001 — Orchestrator/Worker

The Publisher-in-Chief owns sequencing and dependencies. Worker agents receive a bounded task, explicit input artifact hashes, output path, schema, budget, and stop condition. Workers return results; they do not advance project state. Puzzle-generation workers and puzzle-verification workers are always separate — a generator never self-certifies. The orchestrator validates and registers outputs before selecting the next action.
