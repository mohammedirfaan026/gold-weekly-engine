"""
Model Versioning and Git Reproducibility Auditor for Gold AI Engine.
Tracks Git commit hashes, dirty working trees, configuration hashes,
and schema versions to ensure complete auditability of all decision briefs.
"""

from __future__ import annotations
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

MODEL_VERSION = "v1.2.0-decision-support"
SPECIFICATION_VERSION = "v1.2.0-corridor-hedged"
FEATURE_SCHEMA_VERSION = "v2.0-pit"
DATA_VERSION = "2026-09-18-master"


def get_git_commit_hash(repo_dir: Optional[Path | str] = None) -> str:
    """Retrieves full 40-character Git commit hash of current HEAD."""
    try:
        cmd = ["git", "rev-parse", "HEAD"]
        cwd = str(repo_dir) if repo_dir else None
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def is_working_tree_dirty(repo_dir: Optional[Path | str] = None) -> bool:
    """Checks if there are uncommitted changes in the Git working tree."""
    try:
        cmd = ["git", "status", "--porcelain"]
        cwd = str(repo_dir) if repo_dir else None
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        return len(res.stdout.strip()) > 0
    except Exception:
        return True  # Conservatively assume dirty if git command fails


def compute_config_hash(config_dict: Dict[str, Any]) -> str:
    """Computes deterministic SHA256 hash of configuration parameters."""
    try:
        serialized = json.dumps(config_dict, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
    except Exception:
        return "UNKNOWN_HASH"


def get_system_version_info(
    config: Optional[Dict[str, Any]] = None, repo_dir: Optional[Path | str] = None
) -> Dict[str, Any]:
    """
    Compiles complete versioning and provenance metadata.
    Emits explicit warnings if working tree is uncommitted.
    """
    commit_full = get_git_commit_hash(repo_dir)
    commit_short = commit_full[:8] if len(commit_full) >= 8 else commit_full
    dirty = is_working_tree_dirty(repo_dir)

    cfg = config or {
        "threshold": 0.05,
        "sizing": "fixed",
        "corridor_stops": True,
        "stop_pct": 0.025,
        "target_pct": 0.020,
        "ambiguity": "conservative",
        "cost_bps": 10.0,
        "slippage": 0.0005,
    }

    dirty_warning = (
        "UNCOMMITTED CHANGES -- OUTPUT IS NOT REPRODUCIBLE FROM COMMITTED SOURCE"
        if dirty
        else "CLEAN -- FULLY REPRODUCIBLE"
    )

    return {
        "model_version": MODEL_VERSION,
        "specification_version": SPECIFICATION_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "data_version": DATA_VERSION,
        "git_commit": commit_short,
        "git_commit_full": commit_full,
        "is_dirty": dirty,
        "reproducibility_status": dirty_warning,
        "config_hash": compute_config_hash(cfg),
        "generation_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
