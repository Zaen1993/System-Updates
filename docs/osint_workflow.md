# OSINT Workflow Guide

## Overview
This document outlines the OSINT (Open Source Intelligence) workflow used in the project. It integrates multiple tools and techniques for gathering information about targets.

## Tools Integrated
- **Holehe**: Email OSINT
- **PhoneInfoga**: Phone number OSINT
- **Sherlock**: Username search across platforms
- **FinalRecon**: Domain and network reconnaissance
- **IntelliRadar**: Continuous threat intelligence

## Workflow Steps

### 1. Target Definition
- Define target type (email, phone, username, domain)
- Collect initial data points

### 2. Automated Scanning
- Run `osint_email` for email addresses
- Run `osint_phone` for phone numbers
- Run `osint_username` for usernames
- Run `osint_domain` for domains

### 3. Data Correlation
- Use `Haystack` to search through leaked databases
- Correlate results across different sources
- Build relationship graphs

### 4. Deep Analysis
- Analyze social media profiles
- Extract metadata from documents
- Identify associated accounts

### 5. Reporting
- Generate structured JSON output
- Encrypt sensitive findings
- Store in database for later use

## Command Reference
| Command | Description |
|---------|-------------|
| `/osint_email <email>` | Search email across 120+ sites |
| `/osint_phone <number>` | Get carrier, location, reputation |
| `/osint_username <name>` | Find profiles on 250+ platforms |
| `/osint_domain <domain>` | DNS, WHOIS, subdomains |
| `/osint_haystack <query>` | Search leaked databases |

## Example Workflow
1. Start with email: `/osint_email target@example.com`
2. Discover associated username: `johndoe`
3. Run `/osint_username johndoe`
4. Find linked phone: `+1234567890`
5. Run `/osint_phone +1234567890`
6. Correlate all data with `/osint_haystack johndoe`

## Output Format
Results are returned as JSON and stored in the database. Sensitive data is encrypted.

## Best Practices
- Always use VPN/Tor for anonymity
- Rotate user agents and IPs
- Respect rate limits to avoid blocking
- Verify findings from multiple sources

## Troubleshooting
- No results: Check target format, try variations
- Partial results: Run again with different parameters
- API errors: Verify API keys in environment