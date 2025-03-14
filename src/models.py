from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

@dataclass
class PullRequest:
    number: int
    additions: int
    deletions: int
    created_at: str
    merged_at: str = None
    state: str = "open"
    reviews_given: int = 0

@dataclass
class ContributionMetrics:
    total_prs: int
    median_changes: float
    total_additions: int
    total_deletions: int
    reviews_given: int = 0

    @property
    def multiplied_changes(self) -> float:
        """Calculate impact score (PRs × Median Changes)."""
        return self.median_changes * self.total_prs

    @classmethod
    def empty(cls) -> 'ContributionMetrics':
        return cls(
            total_prs=0,
            median_changes=0,
            total_additions=0,
            total_deletions=0,
            reviews_given=0
        )

@dataclass(frozen=True)  # Make it immutable and hashable
class ComponentMetrics:
    name: str
    file_count: int
    unique_files: int
    pr_count: int

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, ComponentMetrics):
            return NotImplemented
        return self.name == other.name

    def __lt__(self, other):
        if not isinstance(other, ComponentMetrics):
            return NotImplemented
        return self.name < other.name

@dataclass
class ReviewMetrics:
    reviewer: str
    total_reviews: int
    avg_response_time: float
    total_comments: int
    repositories: List[str] 