"use client";
/* eslint-disable react-hooks/set-state-in-effect, @next/next/no-img-element */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { type Evidence, type EvidenceProcessing, downloadEvidenceFile, evidenceFileUrl, fetchEvidence, fetchEvidenceProcessing } from "@/lib/api";
import { evidenceKindLabel, evidenceReviewLabel, processingLabel } from "@/lib/labels";
import { EmptyState, ErrorState, Icon, LoadingSkeleton, formatDate, humanError } from "./ui";

function fileSize(bytes: number) {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function sharedOn(evidence: Evidence) {
  if (evidence.report_id) return { label: "A citizen report", href: `/reports/${evidence.report_id}` };
  if (evidence.comment_id && evidence.project_id) return { label: "A comment on the project", href: `/projects/${evidence.project_id}#citizen-evidence` };
  return evidence.project_id ? { label: "The project page", href: `/projects/${evidence.project_id}` } : undefined;
}

const eventLabels: Record<string, string> = { VALIDATION: "File checks", EXTRACTION: "Content processed" };

export function EvidenceDetailPage({ id }: { id: string }) {
  const [evidence, setEvidence] = useState<Evidence>(); const [processing, setProcessing] = useState<EvidenceProcessing>(); const [error, setError] = useState<unknown>(); const [loading, setLoading] = useState(true); const [downloadError, setDownloadError] = useState<unknown>();
  const load = useCallback(async () => { setLoading(true); setError(undefined); try { const [record, process] = await Promise.all([fetchEvidence(id), fetchEvidenceProcessing(id)]); setEvidence(record); setProcessing(process); } catch (caught) { setError(caught); } finally { setLoading(false); } }, [id]);
  useEffect(() => { void load(); }, [load]);
  const download = async () => {
    if (!evidence) return;
    if (!window.confirm("This file was shared by a citizen and has not been verified. Only open files you trust. Download it?")) return;
    setDownloadError(undefined);
    try { const blob = await downloadEvidenceFile(evidence.id); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = `civicact-evidence.${evidence.mime_type.split("/")[1] ?? "file"}`; link.click(); URL.revokeObjectURL(url); } catch (caught) { setDownloadError(caught); }
  };
  if (loading) return <div className="content-wrap detail-loading"><LoadingSkeleton lines={9}/></div>;
  if (error) return <div className="content-wrap page-space"><ErrorState error={error} retry={() => void load()}/><p className="form-hint">Evidence that is limited while reviewed, or removed for safety or privacy, is not shown. <Link href="/community-safety#content-states">Why content may be unavailable</Link></p></div>;
  if (!evidence) return null;
  const isImage = evidence.mime_type.startsWith("image/");
  const review = evidenceReviewLabel(evidence.moderation_state);
  const origin = sharedOn(evidence);
  return <div className="evidence-page">
    <section className="page-intro"><div className="content-wrap"><p className="eyebrow">EVIDENCE &amp; SOURCES</p><h1>{evidenceKindLabel(evidence.mime_type)}</h1><div className="trust-chips"><span className="trust-chip trust-chip--citizen">Citizen-submitted</span><span className={`state-chip state-chip--${review.tone}`}>{review.label}</span></div><p>Citizen evidence is useful context, not an official source or a verification result.</p></div></section>
    <div className="content-wrap evidence-grid">
      {isImage && <figure className="evidence-preview"><img src={evidenceFileUrl(evidence.id)} alt={evidenceKindLabel(evidence.mime_type)}/><figcaption>Location and camera details are removed from photos before publishing.</figcaption></figure>}
      <section className="detail-section">
        <div className="section-heading"><h2>About this evidence</h2></div>
        <dl className="metadata-grid">
          <div><dt>Shared on</dt><dd>{origin ? <Link href={origin.href}>{origin.label}</Link> : "Not linked"}</dd></div>
          <div><dt>Shared</dt><dd>{formatDate(evidence.uploaded_at)}</dd></div>
          <div><dt>Type</dt><dd>{isImage ? "Photo" : evidence.mime_type === "application/pdf" ? "PDF document" : "Document"} · {fileSize(evidence.file_size_bytes)}</dd></div>
          <div><dt>Review</dt><dd>{review.label}</dd></div>
          <div><dt>File checks</dt><dd>{processingLabel(evidence.processing_state)}</dd></div>
          <div><dt>Trust</dt><dd>Citizen-submitted, not verified</dd></div>
        </dl>
        {evidence.project_id && <Link className="button button--outline" href={`/projects/${evidence.project_id}`}><Icon name="projects" size={16}/> View the project</Link>}
        <button type="button" className="text-button evidence-download" onClick={() => void download()}><Icon name="download" size={14}/> Download file</button>
        {Boolean(downloadError) && <p className="form-error">{humanError(downloadError)}</p>}
      </section>
      <Processing processing={processing}/>
    </div>
  </div>;
}

function Processing({ processing }: { processing: EvidenceProcessing | undefined }) {
  return <section className="detail-section"><div className="section-heading"><h2>What has happened to this file</h2></div>
    {processing ? <>{processing.events.length ? <ol className="timeline">{processing.events.map((event) => <li key={event.id}><i/><div><strong>{eventLabels[event.event_type] ?? "Update"}</strong><p>{processingLabel(event.to_state)}</p><small>{formatDate(event.created_at)}</small></div></li>)}</ol> : <EmptyState title="Received" body="The file has been received. Automatic checks will appear here when they run."/>}
      {processing.derived_artifacts.length > 0 && <details className="technical-details"><summary>Technical details</summary><ul className="simple-list">{processing.derived_artifacts.map((artifact) => <li key={artifact.id}><strong>Derived record</strong><span>{artifact.trust_classification.replaceAll("_", " ").toLowerCase()} · {formatDate(artifact.created_at)}</span></li>)}</ul></details>}</>
      : <EmptyState title="Processing details unavailable" body="The service did not return processing information for this file."/>}
  </section>;
}
