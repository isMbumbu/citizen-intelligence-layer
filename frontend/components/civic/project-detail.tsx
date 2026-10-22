"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { FormEvent, createContext, useCallback, useContext, useEffect, useState } from "react";
import {
  type CitizenComment,
  type ClaimEvidence,
  type Evidence,
  type ProjectAnomaly,
  type ProjectDetail,
  type ProjectVerification,
  ApiError,
  createComment,
  createReport,
  fetchAnomalies,
  fetchReports,
  fetchComments,
  fetchProject,
  fetchProjectSources,
  fetchPublicEvidence,
  fetchVerification,
  reportComment,
} from "@/lib/api";
import { getContributorId } from "@/lib/contributor";
import { rememberReport } from "@/lib/my-reports";
import { useApiQuery } from "@/lib/use-api-query";
import {
  EmptyState,
  ErrorState,
  Icon,
  LoadingSkeleton,
  ProgressBar,
  StatusBadge,
  VerificationBadge,
  formatDate,
  formatMoney,
  humanError,
} from "./ui";
import { ReportRow } from "./reports";
import { EvidenceFileInput, EvidenceUploadForm, evidenceFileProblem, uploadEvidenceFile } from "./evidence-upload";
import { EvidenceGallery } from "./evidence-gallery";

// Public evidence for the open project, shared by the gallery, comment cards, and upload forms.
const EvidenceContext = createContext<{ items: Evidence[]; refresh: () => Promise<void> }>({ items: [], refresh: async () => {} });

type DetailData = {
  project: ProjectDetail;
  sources: ClaimEvidence[];
  verification: ProjectVerification | null;
  anomalies: ProjectAnomaly[];
  comments: CitizenComment[];
};

export function ProjectDetailPage({ id }: { id: string }) {
  const load = useCallback(async (): Promise<DetailData> => {
    const [project, sources, verification, anomalies, comments] = await Promise.all([
      fetchProject(id),
      fetchProjectSources(id),
      fetchVerification(id),
      fetchAnomalies(id),
      fetchComments(id),
    ]);
    return { project, sources, verification, anomalies, comments };
  }, [id]);
  const { data, error, loading, refresh } = useApiQuery(load);
  const evidenceQuery = useCallback(() => fetchPublicEvidence("projects", id), [id]);
  const { data: evidenceItems, refresh: refreshEvidence } = useApiQuery(evidenceQuery);
  if (loading) return <div className="content-wrap detail-loading"><LoadingSkeleton lines={11}/></div>;
  if (error) return <div className="content-wrap page-space"><ErrorState error={error} retry={() => void refresh()}/></div>;
  if (!data) return null;
  const { project } = data;
  return (
    <EvidenceContext.Provider value={{ items: evidenceItems ?? [], refresh: refreshEvidence }}>
    <div className="project-detail">
      <section className="detail-hero">
        <div className="detail-hero__decor" />
        <div className="content-wrap">
          <Link className="back-link" href="/projects">
            <Icon name="arrow" size={14} /> Back to projects
          </Link>
          <div className="detail-hero__top">
            <div>
              <p className="eyebrow">PUBLIC PROJECT</p>
              <h1>{project.name}</h1>
              <p>{project.description}</p>
            </div>
            <StatusBadge value={project.status} />
          </div>
          <div className="detail-meta">
            <span><Icon name="pin" /> {project.location.county}, {project.location.ward}</span>
            <span><Icon name="folder" /> {project.category.name}{project.subtype ? ` · ${project.subtype.name}` : ""}</span>
            {project.project_type && <span><Icon name="projects" /> {project.project_type}</span>}
          </div>
        </div>
      </section>

      <div className="content-wrap detail-grid">
        <div className="detail-main">
          <TrustSummary project={project} sources={data.sources} verification={data.verification} anomalies={data.anomalies} />
          <section className="detail-section" id="overview">
            <div className="section-heading">
              <h2>Project overview</h2>
              <VerificationBadge value={data.verification?.status} />
            </div>
            <div className="overview-grid">
              <Info label="County" value={project.location.county} />
              <Info label="Sub-county" value={project.location.sub_county} />
              <Info label="Ward" value={project.location.ward} />
              <Info label="Last verified" value={formatDate(project.last_verified_at)} />
            </div>
            {project.progress ? (
              <div className="progress-card">
                <div>
                  <small>Reported project progress</small>
                  <p>Reported on {formatDate(project.progress.reported_at)}. This is project metadata, not an independent verification finding.</p>
                </div>
                <ProgressBar value={project.progress.percentage} />
              </div>
            ) : (
              <EmptyState title="No reported progress" body="The project record does not currently include a progress update." />
            )}
          </section>

          <FinancialSummary project={project} />
          <Timeline project={project} />
          <VerificationPanel verification={data.verification} />
          <ReviewSignals anomalies={data.anomalies} />
          <Sources sources={data.sources} />
          <ProjectEvidence claims={project.evidence} />
          <CitizenEvidence />
          <ProjectReports projectId={id} />
          <Comments projectId={id} initialComments={data.comments} onChange={refresh} />
        </div>

        <aside className="detail-aside">
          <ReportForm projectId={id} projectName={project.name} />
          <EvidenceUpload projectId={id} />
          {project.contractor ? (
            <section className="aside-card">
              <div className="aside-card__icon"><Icon name="projects" /></div>
              <h2>Contractor</h2>
              <strong>{project.contractor.legal_name}</strong>
              <p>{project.contractor.award_reference}</p>
              <span className="metadata-tag">{project.contractor.contract_status}</span>
              {project.contractor.contract_end_date && <p>Contract end: {formatDate(project.contractor.contract_end_date)}</p>}
            </section>
          ) : (
            <section className="aside-card">
              <div className="aside-card__icon"><Icon name="folder" /></div>
              <h2>Contractor</h2>
              <p>No contractor record is available for this project.</p>
            </section>
          )}
        </aside>
      </div>
    </div>
    </EvidenceContext.Provider>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return <div className="info-cell"><small>{label}</small><strong>{value}</strong></div>;
}

function TrustSummary({ project, sources, verification, anomalies }: { project: ProjectDetail; sources: ClaimEvidence[]; verification: ProjectVerification | null; anomalies: ProjectAnomaly[] }) {
  const sourceCount = new Set(sources.flatMap((claim) => claim.sources.map((source) => source.source_id))).size;
  return (
    <section className="trust-summary" aria-label="Record trust summary">
      <a className="trust-summary__item" href="#overview">
        <span className="trust-summary__label">Record type</span>
        <strong>Public project record</strong>
        <small>Published project information</small>
      </a>
      <a className="trust-summary__item" href="#verification">
        <span className="trust-summary__label">Verification</span>
        <VerificationBadge value={verification?.status} />
        <small>{verification?.verification_date ? `Recorded ${formatDate(verification.verification_date)}` : "No verification date recorded"}</small>
      </a>
      <a className="trust-summary__item" href="#overview">
        <span className="trust-summary__label">Latest reported progress</span>
        <strong>{project.progress ? `${Number(project.progress.percentage)}%` : "Not reported"}</strong>
        <small>{project.progress ? `Reported ${formatDate(project.progress.reported_at)}; not a verification finding` : "No progress update in this record"}</small>
      </a>
      <a className="trust-summary__item" href="#sources">
        <span className="trust-summary__label">Sources available</span>
        <strong>{sourceCount ? `${sourceCount} source${sourceCount === 1 ? "" : "s"}` : "None published"}</strong>
        <small>{sources.length ? `Supporting ${sources.length} claim${sources.length === 1 ? "" : "s"}` : "No source-linked claims yet"}</small>
      </a>
      <a className="trust-summary__item" href="#review-signals">
        <span className="trust-summary__label">Review signals</span>
        <strong>{anomalies.length ? `${anomalies.length} to review` : "None"}</strong>
        <small>Prompts for review, not findings or accusations</small>
      </a>
    </section>
  );
}

function FinancialSummary({ project }: { project: ProjectDetail }) {
  const entries = Object.entries(project.financial_summary).filter(([, value]) => value);
  return (
    <section className="detail-section">
      <div className="section-heading">
        <h2>Financial information</h2>
        <span>Amounts reflect the published project record</span>
      </div>
      {entries.length ? (
        <div className="financial-grid">
          {entries.map(([key, fact]) => fact && (
            <div className="finance-card" key={key}>
              <small>{key.replace(/\b\w/g, (letter) => letter.toUpperCase())}</small>
              <strong>{formatMoney(fact.amount, fact.currency)}</strong>
              <p>{fact.financial_period}</p>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No financial facts published" body="This project does not currently have public financial summary data." />
      )}
    </section>
  );
}

function Timeline({ project }: { project: ProjectDetail }) {
  const timeline = project.timeline;
  return (
    <section className="detail-section">
      <div className="section-heading">
        <h2>Timeline</h2>
        <Icon name="clock" size={16} />
      </div>
      {timeline ? (
        <ol className="timeline">
          <li><i /><div><small>Planned start</small><strong>{formatDate(timeline.planned_start_date)}</strong></div></li>
          <li><i /><div><small>Actual start</small><strong>{formatDate(timeline.actual_start_date)}</strong></div></li>
          <li><i /><div><small>Expected completion</small><strong>{formatDate(timeline.expected_completion_date ?? timeline.planned_completion_date)}</strong></div></li>
        </ol>
      ) : (
        <EmptyState title="No timeline available" body="The project record does not currently include planned or actual dates." />
      )}
    </section>
  );
}

function VerificationPanel({ verification }: { verification: ProjectVerification | null }) {
  return (
    <section className="detail-section verification-panel" id="verification">
      <div className="section-heading">
        <h2>Verification</h2>
        <VerificationBadge value={verification?.status} />
      </div>
      {verification ? (
        <>
          <p>{verification.notes}</p>
          <div className="overview-grid">
            <Info label="Verification date" value={formatDate(verification.verification_date)} />
            <Info label="Recorded" value={formatDate(verification.recorded_at)} />
          </div>
          {verification.source && (
            <p className="source-note">Source: <a href={verification.source.url} target="_blank" rel="noreferrer">{verification.source.title}</a></p>
          )}
        </>
      ) : (
        <p>This project has no active verification record and should be understood as <strong>Unverified</strong>. Citizen submissions and review signals below do not change that status.</p>
      )}
    </section>
  );
}

function ReviewSignals({ anomalies }: { anomalies: ProjectAnomaly[] }) {
  return (
    <section className="detail-section review-signals" id="review-signals">
      <div className="section-heading">
        <h2>Review signals</h2>
        <span>Not findings or accusations</span>
      </div>
      {anomalies.length ? (
        <div className="signal-list">
          {anomalies.map((signal, index) => (
            <details className="signal-card" key={`${signal.type}-${index}`}>
              <summary>
                <span><StatusBadge kind="review" value={signal.status} /><strong>{signal.type.replaceAll("_", " ")}</strong></span>
                <Icon name="arrow" size={16} />
              </summary>
              <p>{signal.message}</p>
              <p className="signal-copy">Requires verification: {signal.requires_verification ? "Yes" : "No"}. This deterministic review signal indicates a data gap or timeline review, not misconduct.</p>
              {signal.supporting_claims.length > 0 && (
                <ul>
                  {signal.supporting_claims.map((claim) => <li key={claim.claim_id}>Supporting claim: {claim.claim_id}</li>)}
                </ul>
              )}
            </details>
          ))}
        </div>
      ) : (
        <EmptyState title="No review signals" body="The API has not returned deterministic review signals for this project." />
      )}
    </section>
  );
}

function Sources({ sources }: { sources: ClaimEvidence[] }) {
  return (
    <section className="detail-section" id="sources">
      <div className="section-heading">
        <h2>Sources &amp; provenance</h2>
        <Icon name="download" size={16} />
      </div>
      {sources.length ? (
        <div className="source-list">
          {sources.map((claim) => (
            <details key={claim.id} className="source-card">
              <summary>
                <span><strong>{claim.field_name}</strong><small>{claim.claim_kind.replaceAll("_", " ")}</small></span>
                <Icon name="arrow" size={16} />
              </summary>
              <p>{claim.value_text}</p>
              {claim.numeric_value !== null && (
                <p><strong>{formatMoney(claim.numeric_value, claim.currency ?? "KES")}</strong>{claim.financial_period ? ` · ${claim.financial_period}` : ""}</p>
              )}
              <ul>
                {claim.sources.map((source) => (
                  <li key={source.source_id}>
                    <a href={source.url} target="_blank" rel="noreferrer">{source.title}</a>
                    <span>{source.publisher} · retrieved {formatDate(source.retrieved_at)}</span>
                  </li>
                ))}
              </ul>
            </details>
          ))}
        </div>
      ) : (
        <EmptyState title="No sources published" body="No link between a claim and its source is currently available for this project." />
      )}
    </section>
  );
}

function CitizenEvidence() {
  const { items } = useContext(EvidenceContext);
  return (
    <section className="detail-section" id="citizen-evidence">
      <div className="section-heading">
        <h2>Photos and documents from citizens</h2>
        <span>Shared by citizens, not verified</span>
      </div>
      {items.length ? <EvidenceGallery items={items} showSource /> : <EmptyState title="No citizen evidence yet" body="Photos and documents shared on this project, its reports, or its comments will appear here." />}
    </section>
  );
}

function ProjectEvidence({ claims }: { claims: ClaimEvidence[] }) {
  return (
    <section className="detail-section">
      <div className="section-heading">
        <h2>Evidence references</h2>
        <span>Supporting claims, not uploaded files</span>
      </div>
      {claims.length ? (
        <div className="evidence-claims">
          {claims.map((claim) => (
            <article key={claim.id}>
              <Icon name="evidence" />
              <div>
                <strong>{claim.field_name}</strong>
                <p>{claim.value_text}</p>
                <small>{claim.sources.length} linked source{claim.sources.length === 1 ? "" : "s"}</small>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState title="No evidence references" body="The project detail does not contain linked evidence claims." />
      )}
    </section>
  );
}

function ProjectReports({ projectId }: { projectId: string }) {
  const query = useCallback(() => fetchReports({ project_id: projectId, page_size: 5 }), [projectId]);
  const { data, error, loading, refresh } = useApiQuery(query);
  return (
    <section className="detail-section" id="reports">
      <div className="section-heading">
        <h2>Citizen reports</h2>
        {data && data.total > 0 ? <Link href={`/reports?project_id=${projectId}`}>See all {data.total}</Link> : <span>Citizen submissions, not verified findings</span>}
      </div>
      {loading ? <LoadingSkeleton lines={3} /> : error ? <ErrorState error={error} retry={() => void refresh()} /> : data && data.items.length ? (
        <ul className="report-list">{data.items.map((report) => <ReportRow key={report.id} report={report} showProject={false} />)}</ul>
      ) : (
        <EmptyState title="No reports yet" body="No citizen has reported an issue on this project. Use the form to report one." />
      )}
    </section>
  );
}

function ReportForm({ projectId, projectName }: { projectId: string; projectName: string }) {
  const { refresh: refreshEvidence } = useContext(EvidenceContext);
  const [category, setCategory] = useState("QUALITY");
  const [description, setDescription] = useState("");
  const [contact, setContact] = useState("");
  const [attachment, setAttachment] = useState<File>();
  const [attachmentError, setAttachmentError] = useState<unknown>();
  const [attached, setAttached] = useState<Evidence>();
  const [pending, setPending] = useState(false);
  const [submitted, setSubmitted] = useState<string>();
  const [error, setError] = useState<unknown>();
  const [descriptionError, setDescriptionError] = useState("");
  const descriptionLength = description.trim().length;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(undefined);
    setSubmitted(undefined);
    setAttachmentError(undefined);
    setAttached(undefined);
    const attachmentProblem = attachment && evidenceFileProblem(attachment);
    if (attachmentProblem) {
      setAttachmentError(new ApiError(attachmentProblem, 422));
      return;
    }
    if (descriptionLength < 10) {
      setDescriptionError(`The description needs at least 10 characters. Add ${10 - descriptionLength} more.`);
      return;
    }
    setDescriptionError("");
    setPending(true);
    try {
      const report = await createReport(projectId, {
        category,
        description: description.trim(),
        contact_information: contact.trim() || undefined,
      });
      rememberReport({ id: report.id, project_id: projectId, project_name: projectName, category: report.category, submitted_at: report.submitted_at });
      setSubmitted(report.id);
      setDescription("");
      setContact("");
      if (attachment) {
        // The report is already saved; a failed upload is reported separately.
        try {
          setAttached(await uploadEvidenceFile(`/projects/${projectId}/reports/${report.id}/evidence`, attachment));
          void refreshEvidence();
          setAttachment(undefined);
        } catch (caught) {
          setAttachmentError(caught);
        }
      }
    } catch (caught) {
      setError(caught);
    } finally {
      setPending(false);
    }
  };

  return (
    <section className="action-card">
      <div className="action-card__icon"><Icon name="report" /></div>
      <h2>Report an Issue</h2>
      <p>Submit citizen information about this project. It is not verification.</p>
      <form onSubmit={submit} className="action-card__form">
        <label>
          Issue category
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="QUALITY">Quality</option>
            <option value="DELAY">Delay</option>
            <option value="ACCESS">Access</option>
            <option value="SAFETY">Safety</option>
            <option value="OTHER">Other</option>
          </select>
        </label>
        <label>
          Description
          <textarea value={description} maxLength={4000} onChange={(event) => { setDescription(event.target.value); if (descriptionError && event.target.value.trim().length >= 10) setDescriptionError(""); }} aria-invalid={Boolean(descriptionError)} aria-describedby="report-description-help" placeholder="Describe the issue with at least 10 characters." required />
          <small id="report-description-help" className={descriptionError ? "field-error" : undefined}>{descriptionError || (descriptionLength < 10 ? `${descriptionLength}/10 characters minimum` : `${description.length}/4000`)}</small>
        </label>
        <label>
          <span>Phone or email <span className="field-optional">(optional)</span></span>
          <input value={contact} maxLength={255} placeholder="Leave blank to report anonymously" onChange={(event) => setContact(event.target.value)} />
          <small>Stored with your report only. It is never shown publicly.</small>
        </label>
        <div className="report-attachment">
          <span>Photo or document <span className="field-optional">(optional)</span></span>
          <EvidenceFileInput file={attachment} onChange={(file) => { setAttachment(file); setAttachmentError(undefined); }} />
          <small>PDF, JPG, PNG, WebP, or GIF up to 10 MB. Attached to your report as citizen evidence.</small>
        </div>
        {Boolean(error) && <p className="form-error" role="alert">{humanError(error)}</p>}
        {Boolean(attachmentError) && <p className="form-error" role="alert">{submitted ? "Your report was saved, but the attachment could not be uploaded: " : ""}{humanError(attachmentError)}{submitted ? " You can add it from the report's status page." : ""}</p>}
        {submitted && (
          <div className="form-success" role="status">
            <p>Report submitted. It is saved under <Link href="/reports">My reports</Link> in this browser. Your reference:</p>
            <code className="report-reference">{submitted}</code>
            {attached && <p>Attachment received. <Link href={`/evidence/${attached.id}`}>View its record</Link></p>}
            <Link href={`/reports/${submitted}`}>Track this report <Icon name="arrow" size={13} /></Link>
          </div>
        )}
        <button className="button button--red button--full" disabled={pending}>
          {pending ? "Submitting…" : "Report an Issue"} <Icon name="arrow" size={15} />
        </button>
      </form>
    </section>
  );
}

function EvidenceUpload({ projectId }: { projectId: string }) {
  const { refresh } = useContext(EvidenceContext);
  return (
    <section className="aside-card evidence-upload">
      <div className="aside-card__icon"><Icon name="upload" /></div>
      <h2>Share evidence</h2>
      <p>Photos or documents about this project. Evidence is shared by citizens and processed by the service; it is not verification.</p>
      <EvidenceUploadForm path={`/projects/${projectId}/evidence`} onUploaded={() => void refresh()} />
    </section>
  );
}

function Comments({ projectId, initialComments, onChange }: { projectId: string; initialComments: CitizenComment[]; onChange: () => Promise<void> }) {
  const [comments, setComments] = useState(initialComments);
  const [content, setContent] = useState("");
  const [error, setError] = useState<unknown>();
  const [pending, setPending] = useState(false);
  const [replyTo, setReplyTo] = useState<string>();

  useEffect(() => setComments(initialComments), [initialComments]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(undefined);
    if (content.trim().length < 10) {
      setError(new ApiError("Comments need at least 10 characters", 422));
      return;
    }
    setPending(true);
    try {
      const newComment = await createComment(projectId, {
        author_id: getContributorId(),
        content: content.trim(),
        parent_comment_id: replyTo,
      });
      setComments((current) => [...current, newComment]);
      setContent("");
      setReplyTo(undefined);
    } catch (caught) {
      setError(caught);
    } finally {
      setPending(false);
    }
  };

  return (
    <section className="detail-section comments-section">
      <div className="section-heading">
        <h2>Community discussion</h2>
        <span>Information shared by citizens</span>
      </div>
      <p className="trust-copy">Comments are public civic discussion, not verified project facts.</p>
      <form className="comment-form" onSubmit={submit}>
        <label>
          Your comment{replyTo && <small> Replying to a comment</small>}
          <textarea value={content} maxLength={4000} onChange={(event) => setContent(event.target.value)} placeholder="Share relevant, respectful information (at least 10 characters)." required />
          <small>{content.length}/4000 · Posted publicly as &ldquo;Citizen contributor&rdquo;, without your name</small>
        </label>
        {Boolean(error) && <p className="form-error">{humanError(error)}</p>}
        <div>
          <button className="button button--dark" disabled={pending}>
            {pending ? "Posting…" : "Post comment"}
          </button>
          {replyTo && <button className="text-button" type="button" onClick={() => setReplyTo(undefined)}>Cancel reply</button>}
        </div>
      </form>
      {comments.length ? (
        <div className="comment-list">
          {comments.map((comment) => (
            <CommentCard key={comment.id} comment={comment} onReply={() => setReplyTo(comment.id)} onReport={onChange} />
          ))}
        </div>
      ) : (
        <EmptyState title="No public comments yet" body="Be the first to add relevant, respectful civic information." />
      )}
    </section>
  );
}

function CommentCard({ comment, onReply, onReport }: { comment: CitizenComment; onReply: () => void; onReport: () => void }) {
  const [open, setOpen] = useState(false);
  const [attaching, setAttaching] = useState(false);
  const { items: projectEvidence, refresh: refreshEvidence } = useContext(EvidenceContext);
  const commentEvidence = projectEvidence.filter((item) => item.comment_id === comment.id);
  const [reason, setReason] = useState("SPAM");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<unknown>();

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(undefined);
    try {
      await reportComment(comment.id, { reporter_id: getContributorId(), reason });
      setMessage("Comment report submitted for review.");
      onReport();
    } catch (caught) {
      setError(caught);
    }
  };

  return (
    <article className={`comment-card ${comment.parent_comment_id ? "comment-card--reply" : ""}`}>
      <div className="comment-card__head">
        <span className="comment-avatar">C</span>
        <div>
          <strong>Citizen contributor</strong>
          <small>{formatDate(comment.created_at)} · {comment.trust_label.replaceAll("_", " ")}</small>
        </div>
        <span className="metadata-tag">{comment.moderation_state}</span>
      </div>
      <p>{comment.content}</p>
      <div className="comment-actions">
        <button className="text-button" onClick={onReply}>Reply</button>
        <button className="text-button" onClick={() => setAttaching(!attaching)} aria-expanded={attaching}>Attach evidence</button>
        <button className="text-button" onClick={() => setOpen(!open)}>Report comment</button>
      </div>
      {commentEvidence.length > 0 && <EvidenceGallery items={commentEvidence} compact />}
      {attaching && <EvidenceUploadForm path={`/comments/${comment.id}/evidence`} submitLabel="Attach to this comment" className="comment-evidence-form" onUploaded={() => void refreshEvidence()} />}
      {open && (
        <form className="comment-report-form" onSubmit={submit}>
          <select value={reason} aria-label="Reason for reporting this comment" onChange={(event) => setReason(event.target.value)}>
            <option value="SPAM">Spam</option>
            <option value="HARASSMENT">Harassment</option>
            <option value="PERSONAL_INFORMATION">Personal information</option>
            <option value="INAPPROPRIATE">Inappropriate</option>
            <option value="OTHER">Other</option>
          </select>
          <button className="button button--outline">Submit report</button>
          {Boolean(error) && <p className="form-error">{humanError(error)}</p>}
          {message && <p className="form-success">{message}</p>}
        </form>
      )}
    </article>
  );
}
