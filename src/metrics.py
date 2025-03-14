import logging
from statistics import median
from typing import List, Dict
from .client import GitHubClient
from .models import ContributionMetrics, PullRequest
from datetime import datetime

class GitHubMetrics:
    def __init__(self, token: str = None):
        """Initialize metrics calculator."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        self.client = GitHubClient(token)

    def get_users_org_contributions(self, usernames: List[str], org: str, days: int = 7) -> Dict[str, ContributionMetrics]:
        """Get contribution metrics for multiple users in an organization."""
        self.logger.info(f"Fetching contributions for {len(usernames)} users in {org}")
        
        # Convert usernames list to tuple for caching
        usernames_tuple = tuple(usernames)
        
        # Get all PRs for all users in one request
        all_prs = self.client.get_users_contributed_repos_and_prs(usernames_tuple, org, days)
        
        # Calculate metrics for each user
        results = {}
        for username, prs in all_prs.items():
            self.logger.info(f"Processing metrics for {username} ({len(prs)} PRs)")
            results[username] = self._calculate_metrics(prs)
        
        return results

    def _calculate_metrics(self, prs: List[PullRequest]) -> ContributionMetrics:
        """Calculate metrics from a list of pull requests."""
        if not prs:
            return ContributionMetrics.empty()

        changes_per_pr = [pr.additions + pr.deletions for pr in prs]
        total_additions = sum(pr.additions for pr in prs)
        total_deletions = sum(pr.deletions for pr in prs)
        
        # Get reviews given (will be same for all PRs since it's per user)
        reviews_given = prs[0].reviews_given if prs else 0

        return ContributionMetrics(
            total_prs=len(prs),
            median_changes=median(changes_per_pr),
            total_additions=total_additions,
            total_deletions=total_deletions,
            reviews_given=reviews_given
        ) 