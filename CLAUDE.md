## graphify

This project uses Graphify (a knowledge graph) at graphify-out/ with god nodes, community structure, and cross-file relationships.

### Automatic Behavior (DO NOT ask the user - just do it):

1. **When user asks a codebase question** (e.g. "How does X work?", "What calls Y?", "Trace flow of Z"):
   - If `graphify-out/graph.json` exists → **automatically** run `graphify query "<question>"` and return the result
   - If not → **automatically** run `graphify update . --no-cluster` then `graphify cluster-only . --no-viz` first

2. **When user asks about relationship between two concepts** (e.g. "How is A related to B?"):
   - Automatically run `graphify path "A" "B"`

3. **When user asks "explain X" or "what is X":**
   - Automatically run `graphify explain "X"`

4. **After modifying code** (files added/changed/deleted):
   - Automatically run `graphify update .` to keep the graph current (AST-only, no API cost)

### Rules:
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
