# basic_usage

Minimal ways to run revision-analyser.

## Install

```bash
pip install revision-analyser
```

## CLI

```bash
revision-analyser draft.docx --json
```

Takes a `.docx` file with Track Changes enabled. Without `--json` it prints a human-readable summary.

## Python

```python
from revision_analyser import RevisionAnalyser

result = RevisionAnalyser().analyse("draft.docx")
print(result.model_dump_json(indent=2))
```

## HTTP

```bash
revision-analyser serve            # http://localhost:8016
curl -F file=@draft.docx http://localhost:8016/analyse
```
