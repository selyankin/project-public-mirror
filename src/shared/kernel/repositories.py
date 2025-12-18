"""In-memory singletons для временных хранилищ."""

from checks.infrastructure.check_results_repo_inmemory import (
    InMemoryCheckResultsRepo,
)
from reports.infrastructure.reports_repo_inmemory import InMemoryReportsRepo

check_results_repo = InMemoryCheckResultsRepo()
reports_repo = InMemoryReportsRepo()
