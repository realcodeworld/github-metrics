import os
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich import box
from .metrics import GitHubMetrics

app = typer.Typer(help="GitHub Contribution Metrics - Analyze PR contributions in organizations")
console = Console()

"""
GitHub Contribution Metrics

Usage:
    # Compare specific users
    python -m src.cli analyze -u dev1 -u dev2 -o organization [-d days] [-t token]

    # List org members
    python -m src.cli members -o organization [-t token]

    # Analyze all members
    python -m src.cli analyze-all -o organization [-d days] [--min-prs count] [-t token]

Options:
    -u, --username    GitHub username (can be multiple)
    -o, --org        GitHub organization name
    -d, --days       Number of days to analyze [default: 7]
    -t, --token      GitHub API token (or set GITHUB_TOKEN env var)
    --min-prs        Minimum number of PRs to include user [default: 1]
"""

@app.command()
def analyze(
    usernames: List[str] = typer.Option(..., "--username", "-u", help="GitHub usernames (can be multiple)"),
    org: str = typer.Option(..., "--org", "-o", help="GitHub organization name"),
    days: int = typer.Option(7, "--days", "-d", help="Number of days to analyze"),
    token: Optional[str] = typer.Option(None, "--token", "-t", help="GitHub API token", envvar="GITHUB_TOKEN"),
):
    """Analyze contributions for multiple users in an organization"""
    try:
        metrics = GitHubMetrics(token)
        all_results = metrics.get_users_org_contributions(usernames, org, days)
        
        if not all_results:
            console.print(f"[bold red]No data found for any users in {org}[/]")
            raise typer.Exit(1)
        
        # Create table
        table = Table(
            title=f"Contribution Metrics in {org} (Last {days} days)",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
            show_lines=True
        )
        
        # Add columns
        table.add_column("Username", style="bold")
        table.add_column("Total PRs", justify="right")
        table.add_column("Median Changes", justify="right")
        table.add_column("Additions", justify="right", style="green")
        table.add_column("Deletions", justify="right", style="red")
        table.add_column("Reviews Given", justify="right", style="blue")
        table.add_column("Total Changes", justify="right", style="bold")
        table.add_column("Impact Score", justify="right", style="yellow")
        
        # Sort users by total changes
        sorted_users = sorted(
            all_results.items(),
            key=lambda x: x[1].total_additions + x[1].total_deletions,
            reverse=True
        )
        
        # Add rows for each user
        for username, metrics in sorted_users:
            table.add_row(
                username,
                str(metrics.total_prs),
                f"{metrics.median_changes:,.0f}",
                f"{metrics.total_additions:,}",
                f"{metrics.total_deletions:,}",
                str(metrics.reviews_given),
                f"{metrics.total_additions + metrics.total_deletions:,}",
                f"{metrics.multiplied_changes:,.0f}"
            )
        
        # Print the table
        console.print()
        console.print(table)
        console.print()
        
    except Exception as e:
        console.print("[bold red]Error:[/] " + str(e), style="red")
        raise typer.Exit(1)

def main():
    app()

if __name__ == "__main__":
    app()  