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

    def check_staleness(self, run: MatchRun) -> tuple[bool, str | None]:
        """
        Evaluate if a MatchRun is stale and determine the precise cause:
          1. "JD edited": JD content/skills modified since the run.
          2. "candidate removed": A candidate evaluated in the run was deleted.
          3. "candidates added": New candidate resumes exist in DB after run creation.
        """
        if run.jd is None:
            return True, "JD edited"

        # Check 1: JD modified
        curr_hash = compute_jd_hash(run.jd.parsed_json)
        if curr_hash != run.jd_snapshot_hash:
            return True, "JD edited"

        # Check 2: Evaluated candidate was removed (orphan check)
        active_results_count = (
            self.db.query(MatchResultDB)
            .filter(MatchResultDB.run_id == run.id)
            .count()
        )
        if active_results_count < run.candidate_count:
            return True, "candidate removed"

        # Check 3: New candidates added to pool AFTER this run
        if run.created_at:
            new_cands_count = (
                self.db.query(Candidate)
                .filter(Candidate.created_at > run.created_at)
                .count()
            )
            if new_cands_count > 0:
                return True, "candidates added"

        return False, None

    def get_run(self, run_id: int) -> tuple[MatchRun | None, bool, str | None]:
        """
        Retrieve a MatchRun by ID and assess whether it is stale.

        Returns:
            (run, is_stale, stale_reason)
        """
        run = (
            self.db.query(MatchRun)
            .options(joinedload(MatchRun.jd))
            .filter(MatchRun.id == run_id)
            .first()
        )
        if run is None:
            return None, False, None

        is_stale, stale_reason = self.check_staleness(run)
        return run, is_stale, stale_reason

    def get_latest_run(
        self, jd_id: int | None = None
    ) -> tuple[MatchRun | None, bool, str | None]:
        """Retrieve the newest match run, optionally filtered by Job Description."""
        query = (
            self.db.query(MatchRun)
            .options(joinedload(MatchRun.jd))
            .order_by(desc(MatchRun.created_at))
        )
        if jd_id is not None:
            query = query.filter(MatchRun.jd_id == jd_id)

        run = query.first()
        if not run:
            return None, False, None

        is_stale, stale_reason = self.check_staleness(run)
        return run, is_stale, stale_reason

    def list_runs(
        self, jd_id: int | None = None, limit: int = 50
    ) -> list[tuple[MatchRun, bool, str | None]]:
        """
        List recent match runs, optionally filtered by Job Description.
        Returns list of (MatchRun, is_stale, stale_reason) tuples.
        """
        query = (
            self.db.query(MatchRun)
            .options(joinedload(MatchRun.jd))
            .order_by(desc(MatchRun.created_at))
        )
        if jd_id is not None:
            query = query.filter(MatchRun.jd_id == jd_id)

        runs = query.limit(limit).all()
        results: list[tuple[MatchRun, bool, str | None]] = []
        for run in runs:
            stale, reason = self.check_staleness(run)
            results.append((run, stale, reason))
        return results

    def get_run_results_advanced(
        self,
        run_id: int,
        sort_by: str = "rank",
        order: str = "asc",
        min_score: float | None = None,
        max_score: float | None = None,
        band: str | None = None,
        min_experience: float | None = None,
        skill: str | None = None,
        search: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[MatchResultDB], int, int, dict[str, int]]:
        """
        Fetch filtered and sorted candidate results for a given run.
        Computes overall band counts and preserves original ranks.

        Returns:
            (paged_items, filtered_count, total_count, band_counts)
        """
        # Load all results with candidate models for the run
        all_results = (
            self.db.query(MatchResultDB)
            .options(joinedload(MatchResultDB.candidate))
            .filter(MatchResultDB.run_id == run_id)
            .order_by(asc(MatchResultDB.rank))
            .all()
        )

        total_count = len(all_results)
        band_counts = {
            "Strong match": 0,
            "Good match": 0,
            "Partial match": 0,
            "Weak match": 0,
            "strong": 0,
            "good": 0,
            "partial": 0,
            "weak": 0,
        }

        # Calculate run-wide band counts
        for r in all_results:
            b_norm = "weak"
            b_raw = "Weak match"
            for k in ("strong", "good", "partial", "weak"):
                if k in (r.band or "").lower():
                    b_norm = k
                    b_raw = f"{k.capitalize()} match"
                    break
            band_counts[b_raw] = band_counts.get(b_raw, 0) + 1
            band_counts[b_norm] = band_counts.get(b_norm, 0) + 1

        # Apply in-memory filtering (to support complex JSON skills and search criteria)
        filtered = []
        skill_query = skill.strip().lower() if skill else None
        search_query = search.strip().lower() if search else None

        for r in all_results:
            # 1. Band filter
            if band and band.strip().lower() not in r.band.lower():
                continue

            # 2. Min / Max Score
            if min_score is not None and r.final_score < min_score:
                continue
            if max_score is not None and r.final_score > max_score:
                continue

            # Candidate info & JSON breakdown
            c = r.candidate
            name = (c.name if c and c.name else r.result_json.get("name", "")).strip()
            email = (c.email if c and c.email else "").strip()
            total_exp = c.total_experience_years if c else r.result_json.get("experience", {}).get("total_years", 0.0)

            # 3. Min Experience filter
            if min_experience is not None and total_exp < min_experience:
                continue

            # 4. Search filter (name or email)
            if search_query:
                if (search_query not in name.lower()) and (search_query not in email.lower()):
                    continue

            # 5. Skill filter (candidate matched this skill)
            if skill_query:
                r_json = r.result_json or {}
                skills_data = r_json.get("skills", {})
                matched_items = skills_data.get("matched", []) + skills_data.get("partially_matched", [])
                matched_names = {
                    (m.get("candidate_skill") or m.get("jd_skill") or "").lower()
                    for m in matched_items
                }
                if not any(skill_query in s_name for s_name in matched_names):
                    continue

            filtered.append(r)

        filtered_count = len(filtered)

        # Sorting
        reverse = order.lower() == "desc"
        if sort_by in ("score", "final_score"):
            filtered.sort(key=lambda x: x.final_score, reverse=reverse)
        elif sort_by == "experience":
            filtered.sort(
                key=lambda x: x.candidate.total_experience_years if x.candidate else 0.0,
                reverse=reverse,
            )
        elif sort_by == "name":
            filtered.sort(
                key=lambda x: (x.candidate.name or "").lower() if x.candidate else "",
                reverse=reverse,
            )
        else:  # default "rank"
            filtered.sort(key=lambda x: x.rank, reverse=reverse)

        # Pagination slice
        paged_items = filtered[offset : offset + limit]
        return paged_items, filtered_count, total_count, band_counts

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

    def get_candidate_detail_context(
        self, run_id: int, candidate_id: int
    ) -> dict[str, Any] | None:
        """
        Fetch a candidate's complete match result with ranking navigation context
        (previous/next candidate IDs by rank) and JD requirements.
        """
        # Fetch all results ordered by rank to determine prev/next
        results = (
            self.db.query(MatchResultDB)
            .options(joinedload(MatchResultDB.candidate), joinedload(MatchResultDB.run).joinedload(MatchRun.jd))
            .filter(MatchResultDB.run_id == run_id)
            .order_by(asc(MatchResultDB.rank))
            .all()
        )
        if not results:
            return None

        target_idx = None
        for idx, r in enumerate(results):
            if r.candidate_id == candidate_id:
                target_idx = idx
                break

        if target_idx is None:
            return None

        target_res = results[target_idx]
        prev_cand_id = results[target_idx - 1].candidate_id if target_idx > 0 else None
        next_cand_id = (
            results[target_idx + 1].candidate_id
            if target_idx < len(results) - 1
            else None
        )

        return {
            "result": target_res,
            "rank": target_res.rank,
            "total_candidates": len(results),
            "prev_candidate_id": prev_cand_id,
            "next_candidate_id": next_cand_id,
            "jd": target_res.run.jd if target_res.run else None,
        }

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
