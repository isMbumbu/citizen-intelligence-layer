"use client";

import Link from "next/link";
import { type FormEvent, useId, useState } from "react";
import { type Evidence, ApiError, uploadEvidence } from "@/lib/api";
import { getContributorId } from "@/lib/contributor";
import { Icon, humanError } from "./ui";

// Mirrors the backend defaults (evidence_allowed_mime_types / evidence_max_size_bytes)
// so citizens hear about a bad file before it is uploaded.
export const evidenceAccept = ".pdf,image/jpeg,image/png,image/webp,image/gif";
const allowedTypes = ["application/pdf", "image/jpeg", "image/png", "image/webp", "image/gif"];
const maxBytes = 10 * 1024 * 1024;

export function evidenceFileProblem(file: File): string | undefined {
  if (!allowedTypes.includes(file.type)) return "This file type isn't accepted. Use a PDF, JPG, PNG, WebP, or GIF.";
  if (file.size > maxBytes) return "This file is larger than 10 MB. Choose a smaller file.";
  return undefined;
}

export function uploadEvidenceFile(path: string, file: File): Promise<Evidence> {
  const form = new FormData();
  form.append("uploader_id", getContributorId());
  form.append("file", file);
  return uploadEvidence(path, form);
}

export function EvidenceFileInput({ file, onChange }: { file: File | undefined; onChange: (file: File | undefined) => void }) {
  return <label className="file-input">
    <Icon name="upload" /> <span>{file?.name ?? "Choose a photo or document"}</span>
    <input type="file" accept={evidenceAccept} onChange={(event) => onChange(event.target.files?.[0])} />
  </label>;
}

/**
 * Upload one evidence file to any of the citizen evidence endpoints. The
 * uploader is the browser's anonymous contributor reference.
 */
export function EvidenceUploadForm({ path, submitLabel = "Upload evidence", className = "", onUploaded }: { path: string; submitLabel?: string; className?: string; onUploaded?: (evidence: Evidence) => void }) {
  const [file, setFile] = useState<File>();
  const [result, setResult] = useState<Evidence>();
  const [error, setError] = useState<unknown>();
  const [pending, setPending] = useState(false);
  const hintId = useId();

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(undefined);
    setResult(undefined);
    if (!file) {
      setError(new ApiError("Choose a file to upload.", 422));
      return;
    }
    const problem = evidenceFileProblem(file);
    if (problem) {
      setError(new ApiError(problem, 422));
      return;
    }
    setPending(true);
    try {
      const uploaded = await uploadEvidenceFile(path, file);
      setResult(uploaded);
      setFile(undefined);
      onUploaded?.(uploaded);
    } catch (caught) {
      setError(caught);
    } finally {
      setPending(false);
    }
  };

  return <form className={`evidence-form ${className}`} onSubmit={submit} aria-describedby={hintId}>
    <EvidenceFileInput file={file} onChange={(next) => { setFile(next); setError(undefined); }} />
    <small id={hintId} className="form-hint">PDF, JPG, PNG, WebP, or GIF up to 10 MB. Sent with an anonymous reference saved in this browser.</small>
    {Boolean(error) && <p className="form-error" role="alert">{humanError(error)}</p>}
    {result && <p className="form-success" role="status">Evidence received. <Link href={`/evidence/${result.id}`}>View its record and processing status</Link></p>}
    <button className="button button--outline button--full" disabled={pending}>{pending ? "Uploading…" : submitLabel}</button>
  </form>;
}
