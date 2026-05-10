Edge fixture 02: WAL slice whose total byte size exceeds the max_input_tokens * 3 byte
heuristic (50,000 tokens * 3 bytes/token = ~150KB).

Bucket: edge. Labeler: deployer (KeenySpace v1 eval baseline).

Scenario: The wal.md contains 50 WAL entries of ~4KB each, totalling ~200KB. In v1,
the coordinator does NOT implement the input-token splitter (deferred to v1.1 per AI-SPEC
§4 Context Window Strategy). This test is xfail until the splitter ships. It documents
the expected behavior: the coordinator should either truncate the slice at a safe entry
boundary and set required_notes_substring to wal_slice_truncated, or abort with abort_budget.
