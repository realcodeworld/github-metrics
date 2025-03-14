import os
import logging
from typing import List, Optional, Dict
import requests
from datetime import datetime, timedelta
from .models import PullRequest
import typer
from functools import lru_cache, wraps
import time
import random

def timer(func):
    """Decorator to time API calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        # Get the instance (self) from args
        instance = args[0]
        instance.logger.info(f"{func.__name__} took {duration:.2f} seconds")
        return result
    return wrapper

def retry_with_backoff(retries=3, backoff_in_seconds=1):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            x = 0
            while True:
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise
                    wait = (backoff_in_seconds * (2 ** x) + 
                           random.uniform(0, 1))  # Add jitter
                    self.logger.warning(
                        f"Attempt {x + 1} failed: {str(e)}. "
                        f"Retrying in {wait:.2f} seconds..."
                    )
                    time.sleep(wait)
                    x += 1
        return wrapper
    return decorator

class GitHubClient:
    def __init__(self, token: str = None):
        """Initialize GitHub API client."""
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable or pass token to constructor.")
        
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.graphql_headers = {
            'Authorization': f'bearer {self.token}',
            'Content-Type': 'application/json',
        }
        self.base_url = 'https://api.github.com'
        self.logger = logging.getLogger(__name__)

    @timer
    @lru_cache(maxsize=32)
    def get_users_contributed_repos_and_prs(self, usernames: tuple, org: str, since_days: int = 7) -> Dict[str, List[PullRequest]]:
        """Get all PRs by multiple users in an organization using GraphQL."""
        since_date = (datetime.now() - timedelta(days=since_days)).strftime('%Y-%m-%d')
        results = {}
        
        # Process users in batches of 25 to avoid query complexity limits
        BATCH_SIZE = 25
        for i in range(0, len(usernames), BATCH_SIZE):
            batch = usernames[i:i + BATCH_SIZE]
            self.logger.info(f"Processing batch of {len(batch)} users ({i+1}-{i+len(batch)} of {len(usernames)})")
            
            batch_results = self._process_user_batch(batch, org, since_date)
            results.update(batch_results)
            
            # Small delay between batches to avoid rate limiting
            time.sleep(1)
        
        return results

    @retry_with_backoff(retries=3, backoff_in_seconds=1)
    def _process_user_batch(self, batch: List[str], org: str, since_date: str) -> Dict[str, List[PullRequest]]:
        """Process a batch of users with retry logic."""
        user_queries = " ".join([
            f"""
            user_{j}: search(
                query: "org:{org} author:{username} created:>={since_date} type:pr",
                type: ISSUE,
                first: 100
            ) {{
                nodes {{
                    ... on PullRequest {{
                        number
                        additions
                        deletions
                        createdAt
                        mergedAt
                        state
                    }}
                }}
            }}
            reviews_{j}: search(
                query: "org:{org} reviewed-by:{username} updated:>={since_date} type:pr",
                type: ISSUE,
                first: 100
            ) {{
                nodes {{
                    ... on PullRequest {{
                        number
                        author {{
                            login
                        }}
                    }}
                }}
            }}
            """ for j, username in enumerate(batch)
        ])
        
        query = f"""
        query {{
            {user_queries}
        }}
        """
        
        response = self._post_graphql(query, {})
        
        if not response or 'data' not in response:
            self.logger.error(f"Invalid response from GitHub API: {response}")
            raise ValueError("Invalid response from GitHub API")

        results = {username: [] for username in batch}
        
        for j, username in enumerate(batch):
            user_data = response['data'].get(f'user_{j}')
            reviews_data = response['data'].get(f'reviews_{j}')
            
            if not user_data or 'nodes' not in user_data:
                continue

            # Count reviews given
            reviews_given = 0
            if reviews_data and 'nodes' in reviews_data:
                reviews_given = len([
                    node for node in reviews_data['nodes']
                    if node and node.get('author')
                ])

            prs = []
            for node in user_data.get('nodes', []):
                if not node:
                    continue

                try:
                    prs.append(PullRequest(
                        number=node.get('number'),
                        additions=node.get('additions', 0),
                        deletions=node.get('deletions', 0),
                        created_at=node.get('createdAt'),
                        merged_at=node.get('mergedAt'),
                        state=node.get('state', 'unknown'),
                        reviews_given=reviews_given  # Add this to PR object
                    ))
                except Exception as e:
                    self.logger.warning(f"Error processing PR for {username}: {str(e)}")
                    continue

            results[username] = prs
            
        return results

    @timer
    @lru_cache(maxsize=32)
    def get_org_members(self, org: str) -> List[Dict]:
        """Get all members of an organization using GraphQL."""
        query = """
        query($org: String!, $cursor: String) {
          organization(login: $org) {
            membersWithRole(first: 100, after: $cursor) {
              nodes {
                login
                url
                type: __typename
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """
        
        members = []
        cursor = None
        
        while True:
            variables = {
                'org': org,
                'cursor': cursor
            }
            
            response = self._post_graphql(query, variables)
            
            if not response.get('data'):
                self.logger.error(f"Organization not found or no access: {org}")
                raise typer.Exit(1)
            
            org_data = response['data']['organization']
            members_data = org_data['membersWithRole']
            
            members.extend([{
                'login': member['login'],
                'url': member['url'],
                'type': member['type']
            } for member in members_data['nodes']])
            
            if not members_data['pageInfo']['hasNextPage']:
                break
                
            cursor = members_data['pageInfo']['endCursor']
        
        return members

    @retry_with_backoff(retries=3, backoff_in_seconds=1)
    def _post_graphql(self, query: str, variables: Dict) -> Dict:
        """Make a POST request to the GitHub GraphQL API with retries."""
        url = 'https://api.github.com/graphql'
        response = requests.post(
            url,
            headers=self.graphql_headers,
            json={'query': query, 'variables': variables}
        )
        response.raise_for_status()
        return response.json()

    def clear_cache(self):
        """Clear the cached results."""
        self.get_org_members.cache_clear()
        self.get_users_contributed_repos_and_prs.cache_clear()

    def get_user_contributed_repos(self, username: str, org: str, since_days: int = 7) -> List[str]:
        """Get repositories where the user has created PRs within the specified time period."""
        repos = set()
        page = 1
        since_date = (datetime.now() - timedelta(days=since_days)).strftime('%Y-%m-%d')
        
        while True:
            query = f'org:{org} author:{username} created:>={since_date}'
            response = self._get('/search/issues', params={
                'q': query,
                'type': 'pr',
                'page': page,
                'per_page': 100,
                'sort': 'created',
                'order': 'desc'
            })
            
            items = response.get('items', [])
            if not items:
                break
                
            for item in items:
                repo = '/'.join(item['repository_url'].split('/')[-2:])
                repos.add(repo)
            
            if len(items) < 100 or self._is_rate_limited(response):
                break
                
            page += 1
        
        return list(repos)

    def get_pull_requests(self, username: str, repo: str, since_days: int = 7) -> List[PullRequest]:
        """Get all PRs by a user in a repository within the specified time period."""
        prs = []
        page = 1
        since_date = (datetime.now() - timedelta(days=since_days)).strftime('%Y-%m-%d')
        cutoff_date = datetime.now() - timedelta(days=since_days)
        
        while True:
            try:
                response = self._get(f'/repos/{repo}/pulls', params={
                    'state': 'all',
                    'creator': username,
                    'page': page,
                    'per_page': 100,
                    'since': since_date
                })
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    self.logger.warning(f"Repository not found or no access: {repo}")
                    return []
                raise
                
            if not response:
                break
                
            recent_prs = [
                pr for pr in response 
                if datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ') > cutoff_date
            ]
            
            if not recent_prs:
                break
                
            for pr in recent_prs:
                pr_details = self._get(f'/repos/{repo}/pulls/{pr["number"]}')
                if pr_details:
                    prs.append(PullRequest(
                        number=pr_details['number'],
                        additions=pr_details['additions'],
                        deletions=pr_details['deletions'],
                        created_at=pr_details['created_at']
                    ))
            
            if len(recent_prs) < 100:
                break
                
            page += 1
        
        return prs

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a GET request to the GitHub API."""
        url = f'{self.base_url}{endpoint}'
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def _is_rate_limited(self, response: requests.Response) -> bool:
        """Check if we're approaching the rate limit."""
        if 'X-RateLimit-Remaining' in response.headers:
            remaining = int(response.headers['X-RateLimit-Remaining'])
            if remaining < 10:
                self.logger.warning("Approaching GitHub API rate limit")
                return True
        return False 