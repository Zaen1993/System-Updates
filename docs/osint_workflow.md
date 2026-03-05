# OSINT Workflow

## Passive Reconnaissance
- Search engines (Google, Bing)
- Social media (LinkedIn, Facebook, Twitter)
- Public code repositories (GitHub, GitLab)
- Pastebin and similar services
- WHOIS and DNS records

## Active Reconnaissance
- Port scanning (nmap, masscan)
- Service enumeration
- Directory brute-forcing
- Subdomain discovery
- Technology fingerprinting

## Tools Integration
- `ai_hunter.py`: Automated target profiling
- `haystack_osint`: Leaked credential lookup
- `intelliradar`: Threat intelligence feeds

## Data Processing
- Normalize and deduplicate findings
- Correlate with existing intelligence
- Store in `target_intelligence` table

## Reporting
- Generate target summaries
- Highlight critical vulnerabilities
- Recommend exploitation paths