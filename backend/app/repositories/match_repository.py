"""
repositories/match_repository.py — Data access layer for Match Runs and Results.
"""

import hashlib
import json
from typing import Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, func

from app.models.match import MatchRun, MatchResultDB
from app.models.jd import JobDescription
from app.models.candidate import Candidate


def compute_jd_hash(parsed_json: dict | None) -> str:
    """
    Generate a deterministic SHA-256 hash of a Job Description's parsed JSON.
    Used for stale-run detection if the recruiter modifies the JD later.
    """
    if not parsed_json:
        return hashlib.sha256(b"{}").hexdigest()
    # Normalize by sorting keys and serializing deterministically
    serialized = json.dumps(parsed_json, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class MatchRepository:
    """Repository for MatchRun and MatchResultDB CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_run(
        self,
        jd_id: int,
        jd_snapshot_hash: str,
        candidate_count: int,
        duration_ms: float,
        config_snapshot: dict[str, Any] | None,
        results_data: list[dict[str, Any]],
    ) -> MatchRun:
        """
        Persist a new MatchRun along with its individual MatchResultDB rows.

        Args:
            jd_id: ID of the Job Description.
            jd_snapshot_hash: SHA-256 hash of JD parsed data at execution time.
            candidate_count: Number of candidates ranked.
            duration_ms: Execution duration in milliseconds.
            config_snapshot: Scoring weights / thresholds snapshot.
            results_data: List of dicts containing:
                candidate_id, rank, final_score, band, is_knockout, result_json.

        Returns:
            The newly created MatchRun with results populated.
        """
        run = MatchRun(
            jd_id=jd_id,
            jd_snapshot_hash=jd_snapshot_hash,
            candidate_count=candidate_count,
            duration_ms=round(duration_ms, 2),
            config_snapshot=config_snapshot,
        )
        self.db.add(run)
        self.db.flush()  # Populates run.id

        result_objs = []
        for item in results_data:
            res_obj = MatchResultDB(
                run_id=run.id,
                candidate_id=item["candidate_id"],
                rank=item["rank"],
                final_score=round(float(item["final_score"]), 2),
                band=item["band"],
                is_knockout=bool(item.get("is_knockout", False)),
                result_json=item["result_json"],
            )
            result_objs.append(res_obj)

        self.db.bulk_save_objects(result_objs)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_run(self, run_id: int) -> tuple[MatchRun | None, bool]:
        """
        Retrieve a MatchRun by ID and assess whether it is stale.

        Returns:
            (run, is_stale)
            is_stale is True if:
              - The associated Job Description was deleted or modified since the run.
        """
        run = (
            self.db.query(MatchRun)
            .options(joinedload(MatchRun.jd))
            .filter(MatchRun.id == run_id)
            .first()
        )
        if run is None:
            return None, False

        # Check JD staleness
        is_stale = False
        if run.jd is None:
            is_stale = True
        else:
            current_hash = compute_jd_hash(run.jd.parsed_json)
            if current_hash != run.jd_snapshot_hash:
                is_stale = True

        return run, is_stale

    def list_runs(
        self, jd_id: int | None = None, limit: int = 50
    ) -> list[tuple[MatchRun, bool]]:
        """
        List recent match runs, optionally filtered by Job Description.
        Returns list of (MatchRun, is_stale) tuples.
        """
        query = (
            self.db.query(MatchRun)
            .options(joinedload(MatchRun.jd))
            .order_by(desc(MatchRun.created_at))
        )
        if jd_id is not None:
            query = query.filter(MatchRun.jd_id == jd_id)

        runs = query.limit(limit).all()
        results: list[tuple[MatchRun, bool]] = []
        for run in runs:
            stale = False
            if run.jd is None:
                stale = True
            else:
                curr_hash = compute_jd_hash(run.jd.parsed_json)
                if curr_hash != run.jd_snapshot_hash:
                    stale = True
            results.append((run, stale))
        return results

    def get_run_results(
        self,
        run_id: int,
        sort_by: str = "rank",
        order: str = "asc",
        band: str | None = None,
        min_score: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MatchResultDB], int]:
        """
        Retrieve paginated candidate results for a given run with optional
        sorting and band/score filtering.

        Returns:
            (results_page, total_count)
        """
        query = (
            self.db.query(MatchResultDB)
            .options(joinedload(MatchResultDB.candidate))
            .filter(MatchResultDB.run_id == run_id)
        )

        # Filters
        if band:
            # Case-insensitive substring/equality
            query = query.filter(func.lower(MatchResultDB.band) == band.lower())

        if min_score is not None:
            query = query.filter(MatchResultDB.final_score >= min_score)

        total_count = query.count()

        # Sorting
        sort_column = MatchResultDB.rank
        if sort_by == "final_score":
            sort_column = MatchResultDB.final_score
        elif sort_by == "rank":
            sort_column = MatchResultDB.rank
        elif sort_by == "created_at":
            sort_column = MatchResultDB.created_at

        if order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        items = query.offset(offset).limit(limit).all()
        return items, total_count

    def get_candidate_result(
        self, run_id: int, candidate_id: int
    ) -> MatchResultDB | None:
        """Find a single candidate's result within a specific match run."""
        return (
            self.db.query(MatchResultDB)
            .options(joinedload(MatchResultDB.candidate), joinedload(MatchResultDB.run))
            .filter(
                MatchResultDB.run_id == run_id,
                MatchResultDB.candidate_id == candidate_id,
            )
            .first()
        )

    def delete_run(self, run_id: int) -> bool:
        """Delete a run and all associated results."""
        run = self.db.query(MatchRun).filter(MatchRun.id == run_id).first()
        if not run:
            return False
        # Explicitly delete child results to ensure complete clean up across all DB dialects
        self.db.query(MatchResultDB).filter(MatchResultDB.run_id == run_id).delete()
        self.db.delete(run)
        self.db.commit()
        return True
