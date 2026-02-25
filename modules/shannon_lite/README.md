```markdown
# Shannon Lite Module

Shannon Lite is an autonomous AI‑powered code analyzer. It detects deep vulnerabilities in source code with 96.15% accuracy.

## Usage

### Analyze a local file

```bash
python analyzer.py path/to/file.py
```

Scan a GitHub repository

```bash
python analyzer.py https://github.com/user/repo
```

Run as a service (with Docker)

```bash
docker build -t shannon-lite .
docker run -p 8080:8080 shannon-lite
```

Then POST code to http://localhost:8080/analyze.

Requirements

See requirements.txt for Python dependencies.

License

Proprietary – All rights reserved.

```