from __future__ import annotations

import json
import logging
import os
import tempfile
import uuid
import hashlib
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from recon_engine.reconcile import run_reconciliation_from_file_groups
from recon_engine.outputs import format_date_for_output
from recon_engine import __version__ as engine_version

app = FastAPI(title="ClearTrail Service", version="0.3.0")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("cleartrail.api")

TEMP_TTL_HOURS = 2


@dataclass
class RunInfo:
    run_id: str
    temp_dir: str
    created_at: datetime
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]


RUNS: Dict[str, RunInfo] = {}


def _cleanup_expired_runs() -> None:
    cutoff = datetime.utcnow() - timedelta(hours=TEMP_TTL_HOURS)
    expired = [run_id for run_id, info in RUNS.items() if info.created_at < cutoff]
    for run_id in expired:
        info = RUNS.pop(run_id, None)
        if info and os.path.isdir(info.temp_dir):
            try:
                logger.info("Cleaning up expired run: %s", run_id)
                for root, _, files in os.walk(info.temp_dir):
                    for name in files:
                        os.remove(os.path.join(root, name))
                os.rmdir(info.temp_dir)
            except Exception:
                logger.exception("Failed to clean temp dir for run: %s", run_id)


def _save_upload(upload: UploadFile, base_dir: str) -> str:
    filename = os.path.basename(upload.filename or "upload")
    file_path = os.path.join(base_dir, filename)
    with open(file_path, "wb") as handle:
        handle.write(upload.file.read())
    return file_path


def _materialize_uploads(files: List[UploadFile], base_dir: str) -> List[Dict[str, Any]]:
    """
    Save uploads to disk and normalize xlsx inputs to csv for the engine.
    Assumption: CSV and XLSX are the only supported formats.
    """
    materialized: List[Dict[str, Any]] = []
    for upload in files:
        saved_path = _save_upload(upload, base_dir)
        ext = os.path.splitext(saved_path)[1].lower()
        engine_path = saved_path

        if ext in [".xlsx", ".xls"]:
            logger.info("Converting spreadsheet to CSV: %s", saved_path)
            df = pd.read_excel(saved_path)
            csv_path = os.path.splitext(saved_path)[0] + ".csv"
            df.to_csv(csv_path, index=False)
            engine_path = csv_path

        materialized.append({
            "original_name": upload.filename,
            "saved_path": saved_path,
            "engine_path": engine_path,
        })
    return materialized


def _materialize_upload_group(
    files: Optional[List[UploadFile]],
    base_dir: str,
    system_label: str
) -> List[Dict[str, Any]]:
    if not files:
        return []
    group = _materialize_uploads(files, base_dir)
    for item in group:
        item["system"] = system_label
    return group


def _sha256_file(path: str) -> str:
    hash_obj = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def _serialize_remittance_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for row in rows:
        row_copy = dict(row)
        if "txn_date_a" in row_copy:
            row_copy["txn_date_a"] = format_date_for_output(row_copy.get("txn_date_a"))
        if "txn_date_b" in row_copy:
            row_copy["txn_date_b"] = format_date_for_output(row_copy.get("txn_date_b"))
        serialized.append(row_copy)
    return serialized


def _write_outputs(
    temp_dir: str,
    remittance_rows: List[Dict[str, Any]],
    run_id: str,
    input_files: List[Dict[str, Any]],
    params: Dict[str, Any]
) -> List[Dict[str, Any]]:
    remittance_df = pd.DataFrame(remittance_rows)
    matched_df = remittance_df[remittance_df["exception_code"] == "matched"].copy()
    probable_df = remittance_df[remittance_df["exception_code"] == "probable_match"].copy()
    exceptions_df = remittance_df[remittance_df["exception_code"] != "matched"].copy()

    outputs_dir = os.path.join(temp_dir, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    remittance_path = os.path.join(outputs_dir, "remittance.csv")
    matched_path = os.path.join(outputs_dir, "matched.csv")
    probable_path = os.path.join(outputs_dir, "probable.csv")
    exceptions_path = os.path.join(outputs_dir, "exceptions.csv")
    summary_path = os.path.join(outputs_dir, "exception_summary.json")
    metadata_path = os.path.join(outputs_dir, "run_metadata.json")
    manifest_path = os.path.join(outputs_dir, "evidence_manifest.json")
    bundle_path = os.path.join(outputs_dir, "evidence_bundle.zip")

    remittance_df.to_csv(remittance_path, index=False)
    matched_df.to_csv(matched_path, index=False)
    probable_df.to_csv(probable_path, index=False)
    exceptions_df.to_csv(exceptions_path, index=False)

    exception_summary: Dict[str, int] = {}
    for row in remittance_rows:
        exception_code = row.get("exception_code") or "unresolved"
        exception_summary[exception_code] = exception_summary.get(exception_code, 0) + 1
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(exception_summary, handle, indent=2)

    run_metadata = {
        "run_id": run_id,
        "run_timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "engine_version": engine_version,
        "inputs": [
            {
                "filename": item.get("original_name"),
                "sha256": _sha256_file(item.get("engine_path"))
            }
            for item in input_files
        ],
        "parameters": params
    }
    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(run_metadata, handle, indent=2)

    output_files = [
        remittance_path,
        matched_path,
        probable_path,
        exceptions_path,
        summary_path,
        metadata_path
    ]
    manifest = {
        "artifacts": [
            {"filename": os.path.basename(path), "sha256": _sha256_file(path)}
            for path in output_files
        ]
    }
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    output_files.append(manifest_path)

    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for path in output_files:
            zipf.write(path, arcname=os.path.basename(path))

    return [
        {"name": "remittance.csv", "path": remittance_path},
        {"name": "matched.csv", "path": matched_path},
        {"name": "probable.csv", "path": probable_path},
        {"name": "exceptions.csv", "path": exceptions_path},
        {"name": "exception_summary.json", "path": summary_path},
        {"name": "run_metadata.json", "path": metadata_path},
        {"name": "evidence_manifest.json", "path": manifest_path},
        {"name": "evidence_bundle.zip", "path": bundle_path},
    ]


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    # Assumption: minimal UI is acceptable and uses client-side fetch to call /reconcile.
    return """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>ClearTrail Reconciliation</title>
    <style>
      :root {
        --bg: #f5f7fa;
        --card: #ffffff;
        --text: #1f2933;
        --muted: #6b7280;
        --border: #e5e7eb;
        --shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
        --primary: #1d4ed8;
        --primary-dark: #1e40af;
        --success: #166534;
        --success-bg: #dcfce7;
        --error: #991b1b;
        --error-bg: #fee2e2;
        --warning: #92400e;
        --warning-bg: #fef3c7;
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        font-family: "Inter", "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
        background: var(--bg);
        color: var(--text);
      }

      .container {
        max-width: 1100px;
        margin: 32px auto 64px;
        padding: 0 20px;
      }

      h1 { margin: 0 0 8px; font-size: 28px; }
      h2 { margin: 0 0 12px; font-size: 18px; color: var(--text); }
      h3 { margin: 0 0 8px; font-size: 16px; color: var(--text); }
      p { margin: 0; color: var(--muted); }

      .card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        box-shadow: var(--shadow);
        margin-bottom: 16px;
      }

      .section-title {
        margin-bottom: 12px;
      }

      .row {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }

      .btn {
        border: 1px solid var(--border);
        background: #fff;
        color: var(--text);
        padding: 10px 14px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
      }

      .btn.primary {
        background: var(--primary);
        color: #fff;
        border-color: var(--primary);
      }

      .btn.primary:hover { background: var(--primary-dark); }

      .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .upload-zone {
        border: 2px dashed var(--border);
        border-radius: 12px;
        padding: 16px;
        background: #f9fafb;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .upload-zone p {
        font-size: 13px;
      }

      .file-list {
        list-style: none;
        padding: 0;
        margin: 12px 0 0;
      }

      .file-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 10px;
        border: 1px solid var(--border);
        border-radius: 8px;
        margin-bottom: 8px;
        background: #f9fafb;
      }

      .file-name {
        font-size: 14px;
        color: var(--text);
      }

      .remove-btn {
        border: none;
        background: transparent;
        cursor: pointer;
        font-size: 16px;
        color: var(--muted);
      }

      .stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
      }

      .stat-card {
        background: #fff;
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 14px;
      }

      .stat-label {
        font-size: 12px;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }

      .stat-value {
        font-size: 22px;
        font-weight: 700;
        margin-top: 6px;
      }

      .table-wrap {
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: auto;
        max-height: 360px;
      }

      table {
        width: 100%;
        border-collapse: collapse;
        min-width: 720px;
      }

      thead th {
        position: sticky;
        top: 0;
        background: #f3f4f6;
        border-bottom: 1px solid var(--border);
        padding: 10px;
        text-align: left;
        font-size: 13px;
      }

      tbody td {
        border-bottom: 1px solid var(--border);
        padding: 10px;
        font-size: 13px;
      }

      tbody tr:nth-child(even) {
        background: #f9fafb;
      }

      .downloads {
        list-style: none;
        padding: 0;
        margin: 0;
      }

      .downloads li {
        margin-bottom: 6px;
      }

      .downloads a {
        color: var(--primary);
        text-decoration: none;
        font-weight: 600;
      }

      .muted { color: var(--muted); }

      .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
      }

      .status-idle {
        background: #e5e7eb;
        color: #374151;
      }

      .status-running {
        background: var(--warning-bg);
        color: var(--warning);
      }

      .status-success {
        background: var(--success-bg);
        color: var(--success);
      }

      .status-error {
        background: var(--error-bg);
        color: var(--error);
      }

      .exports-panel {
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 14px;
        background: #f9fafb;
      }

      .badge {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }

      .sev-high {
        background: #fee2e2;
        color: #991b1b;
      }

      .sev-medium {
        background: #fef3c7;
        color: #92400e;
      }

      .sev-low {
        background: #dcfce7;
        color: #166534;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="card">
        <div class="section-title">
          <h1>ClearTrail</h1>
          <p class="muted">Internal reconciliation console</p>
        </div>
        <div class="row" style="justify-content: space-between; align-items: center;">
          <span class="status-pill status-idle" id="status-pill">Idle</span>
        </div>
      </div>

      <div class="card">
        <h2 class="section-title">Input files</h2>
        <form id="recon-form" class="upload-zone">
          <div class="row" style="justify-content: space-between;">
            <div>
              <h3>System A</h3>
              <input type="file" id="files-a" name="system_a" multiple />
              <button type="button" class="btn" id="add-files-a">Add files</button>
              <ul class="file-list" id="file-list-a"></ul>
            </div>
            <div>
              <h3>System B</h3>
              <input type="file" id="files-b" name="system_b" multiple />
              <button type="button" class="btn" id="add-files-b">Add files</button>
              <ul class="file-list" id="file-list-b"></ul>
            </div>
            <div>
              <h3>System C (optional)</h3>
              <input type="file" id="files-c" name="system_c" multiple />
              <button type="button" class="btn" id="add-files-c">Add files</button>
              <ul class="file-list" id="file-list-c"></ul>
            </div>
          </div>
          <div class="row">
            <button type="submit" class="btn primary" id="run-btn" disabled>Run analysis</button>
            <button type="button" class="btn" id="clear-files">Clear all</button>
          </div>
          <p class="muted">Add 1+ files for System A and System B. System C is optional.</p>
        </form>
      </div>

      <div class="card" id="error-card" style="display:none;">
        <h2 class="section-title">Error</h2>
        <div id="error-box" style="background:#fee2e2;border:1px solid #fca5a5;color:#991b1b;padding:12px;border-radius:8px;"></div>
      </div>

      <div class="card" id="summary-card">
        <h2 class="section-title">Reconciliation summary</h2>
        <div class="stats" id="summary-cards">
          <div class="stat-card">
            <div class="stat-label">Matched</div>
            <div class="stat-value" id="matched-count">0</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Unmatched</div>
            <div class="stat-value" id="unmatched-count">0</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Exceptions</div>
            <div class="stat-value" id="exception-count">0</div>
          </div>
        </div>
        <div class="exports-panel" style="margin-top:12px;">
          <div class="stat-label">Exception types</div>
          <ul class="downloads" id="exception-summary"></ul>
        </div>
      </div>

      <div class="card" id="preview-card">
        <h2 class="section-title">Exception preview</h2>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>txn_date</th>
                <th>amount_a</th>
                <th>amount_b</th>
                <th>amount_c</th>
                <th>exception_label</th>
                <th>exception_code</th>
                <th>confidence</th>
                <th>severity</th>
                <th>date_delta_days</th>
                <th>present_in_c</th>
              </tr>
            </thead>
            <tbody id="preview-body"></tbody>
          </table>
        </div>
      </div>

      <div class="card" id="outputs-card">
        <h2 class="section-title">Exports</h2>
        <div class="exports-panel">
          <ul class="downloads" id="downloads"></ul>
        </div>
      </div>
    </div>
    <script>
      const form = document.getElementById("recon-form");
      const statusPill = document.getElementById("status-pill");
      const matchedCount = document.getElementById("matched-count");
      const unmatchedCount = document.getElementById("unmatched-count");
      const exceptionCount = document.getElementById("exception-count");
      const exceptionSummaryList = document.getElementById("exception-summary");
      const previewBody = document.getElementById("preview-body");
      const downloads = document.getElementById("downloads");
      const errorCard = document.getElementById("error-card");
      const errorBox = document.getElementById("error-box");
      const summaryCard = document.getElementById("summary-card");
      const previewCard = document.getElementById("preview-card");
      const outputsCard = document.getElementById("outputs-card");
      const fileInputA = document.getElementById("files-a");
      const fileInputB = document.getElementById("files-b");
      const fileInputC = document.getElementById("files-c");
      const fileListA = document.getElementById("file-list-a");
      const fileListB = document.getElementById("file-list-b");
      const fileListC = document.getElementById("file-list-c");
      const addFilesButtonA = document.getElementById("add-files-a");
      const addFilesButtonB = document.getElementById("add-files-b");
      const addFilesButtonC = document.getElementById("add-files-c");
      const clearFilesButton = document.getElementById("clear-files");
      const runButton = document.getElementById("run-btn");
      const selectedFilesA = [];
      const selectedFilesB = [];
      const selectedFilesC = [];

      function renderFileList(listEl, files, onRemove) {
        listEl.innerHTML = "";
        files.forEach((file, index) => {
          const li = document.createElement("li");
          li.className = "file-item";
          const name = document.createElement("span");
          name.className = "file-name";
          name.textContent = file.name;
          const removeBtn = document.createElement("button");
          removeBtn.className = "remove-btn";
          removeBtn.type = "button";
          removeBtn.textContent = "✕";
          removeBtn.addEventListener("click", () => {
            onRemove(index);
          });
          li.appendChild(name);
          li.appendChild(removeBtn);
          listEl.appendChild(li);
        });
        runButton.disabled = selectedFilesA.length < 1 || selectedFilesB.length < 1;
      }

      function renderAll() {
        renderFileList(fileListA, selectedFilesA, (idx) => {
          selectedFilesA.splice(idx, 1);
          renderAll();
        });
        renderFileList(fileListB, selectedFilesB, (idx) => {
          selectedFilesB.splice(idx, 1);
          renderAll();
        });
        renderFileList(fileListC, selectedFilesC, (idx) => {
          selectedFilesC.splice(idx, 1);
          renderAll();
        });
      }

      function clearError() {
        errorCard.style.display = "none";
        errorBox.textContent = "";
        summaryCard.style.display = "block";
        previewCard.style.display = "block";
        outputsCard.style.display = "block";
      }

      function showError(message) {
        errorCard.style.display = "block";
        errorBox.textContent = message;
        summaryCard.style.display = "none";
        previewCard.style.display = "none";
        outputsCard.style.display = "none";
      }

      addFilesButtonA.addEventListener("click", () => {
        fileInputA.click();
      });
      addFilesButtonB.addEventListener("click", () => {
        fileInputB.click();
      });
      addFilesButtonC.addEventListener("click", () => {
        fileInputC.click();
      });

      fileInputA.addEventListener("change", () => {
        for (const file of fileInputA.files) {
          selectedFilesA.push(file);
        }
        fileInputA.value = "";
        renderAll();
      });

      fileInputB.addEventListener("change", () => {
        for (const file of fileInputB.files) {
          selectedFilesB.push(file);
        }
        fileInputB.value = "";
        renderAll();
      });

      fileInputC.addEventListener("change", () => {
        for (const file of fileInputC.files) {
          selectedFilesC.push(file);
        }
        fileInputC.value = "";
        renderAll();
      });

      clearFilesButton.addEventListener("click", () => {
        selectedFilesA.length = 0;
        selectedFilesB.length = 0;
        selectedFilesC.length = 0;
        renderAll();
      });

      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        statusPill.textContent = "Running";
        statusPill.className = "status-pill status-running";
        matchedCount.textContent = "0";
        unmatchedCount.textContent = "0";
        exceptionCount.textContent = "0";
        previewBody.innerHTML = "";
        downloads.innerHTML = "";
        exceptionSummaryList.innerHTML = "";
        clearError();

        const formData = new FormData();
        for (const file of selectedFilesA) {
          formData.append("system_a", file);
        }
        for (const file of selectedFilesB) {
          formData.append("system_b", file);
        }
        for (const file of selectedFilesC) {
          formData.append("system_c", file);
        }

        if (selectedFilesA.length < 1 || selectedFilesB.length < 1) {
          statusPill.textContent = "Needs files";
          statusPill.className = "status-pill status-error";
          showError("Provide at least one file for System A and System B.");
          return;
        }

        const response = await fetch("/reconcile", {
          method: "POST",
          body: formData
        });

        if (!response.ok) {
          let message = "Reconciliation failed.";
          try {
            const errorPayload = await response.json();
            message = errorPayload?.error || message;
          } catch (err) {
            // ignore parse errors
          }
          statusPill.textContent = "Error";
          statusPill.className = "status-pill status-error";
          showError(message);
          return;
        }

        const data = await response.json();
        statusPill.textContent = "Complete";
        statusPill.className = "status-pill status-success";

        const matched = data?.stats?.matched ?? 0;
        const unmatched = data?.stats?.unmatched ?? 0;
        const exceptions = data?.stats?.exceptions ?? {};
        matchedCount.textContent = matched;
        unmatchedCount.textContent = unmatched;
        exceptionCount.textContent = Object.values(exceptions).reduce((a, b) => a + b, 0);
        exceptionSummaryList.innerHTML = "";
        Object.keys(exceptions).sort().forEach((key) => {
          const li = document.createElement("li");
          li.textContent = `${key}: ${exceptions[key]}`;
          exceptionSummaryList.appendChild(li);
        });

        const preview = data?.preview ?? [];
        for (const row of preview) {
          const tr = document.createElement("tr");
          const confidence = typeof row.confidence_score === "number"
            ? row.confidence_score.toFixed(2)
            : (row.confidence_score ?? "");
          tr.innerHTML = `
            <td>${row.txn_date ?? ""}</td>
            <td>${row.amount_a ?? ""}</td>
            <td>${row.amount_b ?? ""}</td>
            <td>${row.amount_c ?? ""}</td>
            <td>${row.exception_label ?? ""}</td>
            <td>${row.exception_code ?? ""}</td>
            <td>${confidence}</td>
            <td><span class="badge ${row.severity ? `sev-${row.severity}` : ""}">${row.severity ?? ""}</span></td>
            <td>${row.date_delta_days ?? ""}</td>
            <td>${row.present_in_c ?? ""}</td>
          `;
          previewBody.appendChild(tr);
        }

        const outputLinks = data?.outputs ?? [];
        const bundle = outputLinks.find(o => o.name === "evidence_bundle.zip");
        if (bundle) {
          const li = document.createElement("li");
          const link = document.createElement("a");
          link.href = bundle.url;
          link.textContent = "Download evidence bundle";
          li.appendChild(link);
          downloads.appendChild(li);
        }
      });
    </script>
  </body>
</html>
    """.strip()


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/download/{run_id}/{filename}")
async def download(run_id: str, filename: str):
    run_info = RUNS.get(run_id)
    if not run_info:
        raise HTTPException(status_code=404, detail="Unknown run_id.")
    for output in run_info.outputs:
        if output["name"] == filename:
            return FileResponse(output["path"], filename=filename)
    raise HTTPException(status_code=404, detail="File not found.")


@app.post("/reconcile")
async def reconcile(
    system_a: List[UploadFile] = File(...),
    system_b: List[UploadFile] = File(...),
    system_c: Optional[List[UploadFile]] = File(None)
) -> Dict[str, Any]:
    logger.info("Reconcile request received A=%d B=%d C=%d", len(system_a), len(system_b), len(system_c or []))
    if len(system_a) < 1 or len(system_b) < 1:
        raise HTTPException(status_code=400, detail="System A and System B files are required.")

    _cleanup_expired_runs()

    run_id = uuid.uuid4().hex
    temp_dir = tempfile.mkdtemp(prefix=f"cleartrail_{run_id}_")
    logger.info("Run %s temp dir: %s", run_id, temp_dir)

    a_materialized = _materialize_upload_group(system_a, temp_dir, "A")
    b_materialized = _materialize_upload_group(system_b, temp_dir, "B")
    c_materialized = _materialize_upload_group(system_c, temp_dir, "C")

    system_a_paths = [item["engine_path"] for item in a_materialized]
    system_b_paths = [item["engine_path"] for item in b_materialized]
    system_c_paths = [item["engine_path"] for item in c_materialized]

    logger.info("Run %s executing reconciliation pipeline", run_id)
    try:
        result = run_reconciliation_from_file_groups(system_a_paths, system_b_paths, system_c_paths)
        if not result.get("ok"):
            message = result.get("error") or "Reconciliation failed."
            return JSONResponse(status_code=400, content={"error": message})
        remittance_df = result["remittance_df"]
        remittance_rows = _serialize_remittance_rows(remittance_df.to_dict(orient="records"))

        matched = sum(1 for row in remittance_rows if row.get("exception_code") == "matched")
        unmatched = len(remittance_rows) - matched

        exception_summary: Dict[str, int] = {}
        for row in remittance_rows:
            exception_code = row.get("exception_code") or "unresolved"
            if exception_code == "matched":
                continue
            exception_summary[exception_code] = exception_summary.get(exception_code, 0) + 1

        logger.info("Run %s writing outputs", run_id)
        outputs = _write_outputs(
            temp_dir,
            remittance_rows,
            run_id,
            a_materialized + b_materialized + c_materialized,
            {"date_window_days": 3, "amount_tolerance": 0.01}
        )
        outputs_payload = [
            {"name": output["name"], "url": f"/download/{run_id}/{output['name']}"}
            for output in outputs
        ]
        remittance_rows = [r for r in remittance_rows if r.get("exception_code") != "matched"]
        remittance_rows.sort(key=lambda r: r.get("priority_rank", 0), reverse=True)
        preview = []
        for row in remittance_rows[:10]:
            preview.append({
                "txn_date": row.get("txn_date_a") or row.get("txn_date_b"),
                "amount_a": row.get("amount_a") or row.get("txn_amount_a"),
                "amount_b": row.get("amount_b") or row.get("txn_amount_b"),
                "amount_c": row.get("amount_c"),
                "exception_label": row.get("exception_label"),
                "exception_code": row.get("exception_code"),
                "confidence_score": row.get("confidence_score"),
                "severity": row.get("severity"),
                "date_delta_days": row.get("date_delta_days"),
                "present_in_c": row.get("present_in_c"),
                "priority_rank": row.get("priority_rank"),
            })

        RUNS[run_id] = RunInfo(
            run_id=run_id,
            temp_dir=temp_dir,
            created_at=datetime.utcnow(),
            inputs=a_materialized + b_materialized + c_materialized,
            outputs=outputs,
        )

        logger.info("Run %s completed", run_id)
        return {
            "run_id": run_id,
            "inputs": [{"name": item["original_name"], "system": item.get("system")} for item in a_materialized + b_materialized + c_materialized],
            "stats": {
                "matched": matched,
                "unmatched": unmatched,
                "exceptions": exception_summary,
            },
            "outputs": outputs_payload,
            "preview": preview,
        }
    except Exception as exc:
        logger.exception("Run %s failed", run_id)
        message = str(exc) if str(exc) else "Reconciliation failed."
        return JSONResponse(status_code=400, content={"error": message})
