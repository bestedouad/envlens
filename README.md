# envlens

> A CLI tool that audits and diffs `.env` files across environments to catch missing or mismatched variables.

---

## Installation

```bash
pip install envlens
```

Or install from source:

```bash
git clone https://github.com/yourusername/envlens.git
cd envlens && pip install -e .
```

---

## Usage

### Audit a single `.env` file against a template

```bash
envlens audit --template .env.example --target .env
```

### Diff two environment files

```bash
envlens diff .env.staging .env.production
```

### Example output

```
[MISSING]   DATABASE_URL   found in .env.staging but not in .env.production
[MISMATCH]  LOG_LEVEL      staging=debug | production=debug ✓
[EXTRA]     DEBUG_MODE     found in .env.production but not in .env.staging
```

### Options

| Flag | Description |
|------|-------------|
| `--strict` | Exit with non-zero code if any issues are found |
| `--ignore KEY` | Skip a specific key during comparison |
| `--format json` | Output results as JSON |

---

## Why envlens?

Shipping broken configs to production is painful. `envlens` makes it easy to spot gaps between your `.env` files before they become incidents — great for CI pipelines and local development alike.

---

## License

This project is licensed under the [MIT License](LICENSE).