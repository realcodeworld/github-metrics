# GitHub Contribution Metrics 📊

Track and analyze GitHub pull request contributions across your organization. Simple, fast, and insightful metrics for your team.

![Analysis](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDd6Y2JxNXh4MWF1NWF2OWs4NmN0NXJ3Z2t1aHd0ZHBxbXJ0Y3NvdyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/13HgwGsXF0aiGY/giphy.gif)

## Features
- 📈 Compare PR metrics between team members
- 📊 View essential contribution metrics:
  - Total PRs created
  - Median changes per PR
  - Lines added and deleted
  - Reviews given to other PRs
  - Impact score (PRs × Median Changes)
- 🚀 Fast GraphQL queries with smart batching
- 🎨 Beautiful terminal output

## Installation

![Setup](https://media.giphy.com/media/Y4ak9Ki2GZCbJxAnJD/giphy.gif)

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/github-metrics.git
   cd github-metrics
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up GitHub token:
   - Go to GitHub Settings > Developer Settings > Personal Access Tokens
   - Create token with `read:org` and `repo` scopes
   - Set as environment variable:
     ```
     export GITHUB_TOKEN=your_token_here
     ```

## Usage

### List Organization Members

View all members in an organization:
```
python -m src.cli list-users -o organization
```

Example output:
```
                    Organization Members in organization                    
╭──────────┬────────────────────────────────┬──────────────╮
│ Username │ Profile URL                    │ Type         │
├──────────┼────────────────────────────────┼──────────────┤
│ dev1     │ https://github.com/dev1        │ User         │
│ dev2     │ https://github.com/dev2        │ User         │
│ bot-user │ https://github.com/bot-user    │ Bot          │
╰──────────┴────────────────────────────────┴──────────────╯

Total members: 3
```

### Compare Developers

Compare specific developers:
```
python -m src.cli analyze -u dev1 -u dev2 -o organization
```

Analyze last 14 days:
```
python -m src.cli analyze -u dev1 -u dev2 -o organization -d 14
```

Example output:
```
                    Contribution Metrics in organization (Last 7 days)                    
╭──────────┬───────────┬────────────────┬───────────┬───────────┬───────────────┬───────────────┬──────────────╮
│ Username │ Total PRs │ Median Changes │ Additions │ Deletions │ Reviews Given │ Total Changes │ Impact Score │
├──────────┼───────────┼────────────────┼───────────┼───────────┼───────────────┼───────────────┼──────────────┤
│ dev1     │        12 │            156 │     2,345 │     1,234 │            25 │        3,579  │       1,872  │
│ dev2     │         8 │            234 │     1,876 │       987 │            18 │        2,863  │       1,872  │
╰──────────┴───────────┴────────────────┴───────────┴───────────┴───────────────┴───────────────┴──────────────╯
```

![Metrics](https://media.giphy.com/media/3oKIPEqDGUULpEU0aQ/giphy.gif)

## Understanding the Metrics

- **Total PRs**: Number of pull requests created by the developer
- **Median Changes**: Typical size of changes per PR (additions + deletions)
- **Additions**: Lines of code added (shown in green)
- **Deletions**: Lines of code removed (shown in red)
- **Reviews Given**: Number of PRs reviewed for other team members
- **Total Changes**: Sum of all lines modified (additions + deletions)
- **Impact Score**: Contribution impact measurement (PRs × Median Changes)

## Command Options

```
Options:
  -u, --username    GitHub username (can specify multiple)
  -o, --org        GitHub organization name
  -d, --days       Number of days to analyze [default: 7]
  -t, --token      GitHub API token (or set GITHUB_TOKEN env var)
  --help           Show this message and exit
```

## Troubleshooting

![Debug](https://media.giphy.com/media/USV0ym3bVWQJJmNu3N/giphy.gif)

Common issues and solutions:

1. Authentication Errors
   - Ensure GITHUB_TOKEN is set
   - Verify token has `read:org` and `repo` scopes
   - Check token hasn't expired

2. Rate Limiting
   - Tool automatically handles rate limits
   - Uses batching for efficient queries
   - Adds delays between requests

3. Organization Access
   - Verify membership in organization
   - Check organization name spelling
   - Ensure token has organization access

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a Pull Request

## License

MIT License - See LICENSE file for details

---
Made with 💻 by developers who love metrics

![Code](https://media.giphy.com/media/ZVik7pBtu9dNS/giphy.gif)

# A Note on Developer Productivity 📈

While this tool provides metrics about PR activity, it's important to understand that **developer productivity cannot and should not be measured purely by quantitative metrics** like number of PRs or lines of code. Here's why:

## Why Pure Metrics Can Be Misleading 🚫

1. **Quality Over Quantity** 🎯
   - A single well-designed PR might provide more value than dozens of small fixes
   - Clean, maintainable code often means writing less, not more
   - Bug prevention is as valuable as bug fixing

2. **Different Types of Contributions** 💡
   - Code review and mentoring
   - Architecture and design work
   - Documentation and knowledge sharing
   - Team collaboration and communication
   - Technical debt reduction

3. **Context Matters** 🔍
   - Project complexity varies
   - Learning new technologies takes time
   - Different phases require different approaches
   - Some tasks require more research than coding

## Better Ways to Evaluate Impact 🌟

1. **Code Quality Indicators**
   - Code maintainability
   - Test coverage
   - Documentation quality
   - Architecture improvements

2. **Team Collaboration**
   - Code review quality
   - Knowledge sharing
   - Mentoring others
   - Team communication

3. **Business Impact**
   - Feature completion
   - Customer satisfaction
   - System reliability
   - Problem-solving effectiveness

## How to Use This Tool Responsibly ⚖️

- Use metrics as **conversation starters**, not performance evaluators
- Look for patterns and trends, not absolute numbers
- Consider metrics alongside qualitative feedback
- Focus on team improvement, not individual comparison
- Use data to identify systemic issues or bottlenecks

Remember: The best developers often make their entire team more productive, and that's something no metric can fully capture. 🌱

---

*"Not everything that can be counted counts, and not everything that counts can be counted." - Albert Einstein*