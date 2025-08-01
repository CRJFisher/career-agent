# Career Application Agent - Project Guidelines

## Edit Notation Guide

When providing feedback or edits, use these tags:

| Tag | Purpose | Example |
|-----|---------|---------|
| `[CHUCK]` or `[CF]` | Your general comments/thoughts | `[CHUCK]: This positioning might be too modest` |
| `[Q]` | Questions to consider | `[Q]: Should I mention specific team sizes?` |
| `[TODO]` | Action items to complete | `[TODO]: Add metrics about user adoption` |
| `[ADD]` | Content to add at this point | `[ADD: "including 10k daily active users"]` |
| `[EDIT]` | Suggested replacement text | `[EDIT: "architected" instead of "built"]` |
| `[!]` | Important/critical points | `[!]: Must emphasize MCP experience` |
| `[?]` | Uncertain areas needing review | `[?]: Is this too technical?` |
| `[NOTE]` | Additional context or reminders | `[NOTE: Relates to discussion about scale]` |
| `[CUT]` | Suggest removing this content | `[CUT]: Too much detail for cover letter` |

## Project-Specific Guidelines

### PocketFlow Implementation

This project implements nodes and flows following The-Pocket/PocketFlow framework patterns:

1. **Node Structure**: Each node should implement the 3-step pattern:
   - `prep(shared)`: Read and preprocess data from shared store
   - `exec(prep_res)`: Execute compute logic (mainly LLM calls)
   - `post(shared, prep_res, exec_res)`: Write results back to shared store and return action

2. **Flow Structure**: Flows connect nodes through action-based transitions:
   - Use `node_a >> node_b` for default transitions
   - Use `node_a - "action_name" >> node_b` for named actions
   - Flows should be created with `Flow(start=node)`

3. **Shared Store**: Central data structure for node communication:
   - Career database information
   - Job requirements
   - Analysis results
   - Generated documents

### Project File Structure

```text
career-agent/
├── main.py              # Entry point and orchestrator
├── nodes.py             # Node implementations
├── flow.py              # Flow definitions
├── utils/               # Utility functions
│   ├── llm_wrapper.py   # LLM integration
│   ├── database_parser.py # Career DB parsing
│   └── ...
├── docs/
│   ├── design.md        # High-level design document
│   └── ...
└── tests/               # Test files
```

### Key Implementation Notes

1. **LLM Integration**: Use the wrapper in `utils/llm_wrapper.py` for all LLM calls
2. **Error Handling**: Let nodes handle retries through PocketFlow's built-in mechanism
3. **Data Validation**: Validate structured outputs (YAML) in nodes
4. **Logging**: Use Python logging throughout for debugging

### Testing Requirements

All new features must include:

- Unit tests for individual nodes
- Integration tests for complete flows
- Test data for career database and job descriptions
- Mock LLM responses for consistent testing

### Documentation Requirements

- Update `docs/design.md` when adding new nodes or flows
- Document node inputs/outputs in docstrings
- Keep schema documentation up to date

## Development Workflow

1. Design at high level before implementation
2. Start with simple solutions and iterate
3. Test individual nodes before integrating into flows
4. Validate outputs match expected schemas
5. Run integration tests before marking tasks complete
