# benchmarks/golden-qa/

Hand-curated question-and-answer pairs grounded in the committed synthetic corpus (`../corpus/metadata.jsonl`).

* **v1.jsonl** — 30 items. Split:
  * 22 direct (single-document) questions
  * 4 multi-hop questions requiring synthesis across two or three documents
  * 4 unanswerable questions whose reference answer is exactly `"I don't know based on the provided context."`

The unanswerable items are deliberately included so faithfulness can be measured (a good RAG system should refuse to invent answers).

## Schema

```json
{
  "id": "q01",
  "question": "...",
  "answer": "...",
  "source_ids": ["synth-001"],
  "tags": ["direct", "moe"]
}
```

`source_ids` is empty for unanswerable items. `tags` are free-form but conventional ones include `direct`, `multi-hop`, `unanswerable`, and a topic tag (`rag`, `moe`, `multilingual`, …).
