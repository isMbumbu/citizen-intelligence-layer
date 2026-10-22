"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { type Institution, type InstitutionResponse, type ReportComparison, type ReportDetail, type ReportingChannel, fetchInstitutions, fetchReport, fetchReportChannels, fetchPublicEvidence, fetchReportComparison, fetchReportResponses } from "@/lib/api";
import { useApiQuery } from "@/lib/use-api-query";
import { EmptyState, ErrorState, Icon, LoadingSkeleton, StatusBadge, formatDate } from "./ui";
import { EvidenceUploadForm } from "./evidence-upload";
import { EvidenceGallery } from "./evidence-gallery";

type ReportData = { report: ReportDetail; channels: ReportingChannel[]; institutions: Institution[]; responses: InstitutionResponse[]; comparison: ReportComparison };

export function ReportDetailPage({ id }: { id: string }) {
  const [data, setData] = useState<ReportData>(); const [error, setError] = useState<unknown>(); const [loading, setLoading] = useState(true);
  const load = useCallback(async () => { setLoading(true); setError(undefined); try { const [report, channels, institutions, responses, comparison] = await Promise.all([fetchReport(id), fetchReportChannels(id), fetchInstitutions(id), fetchReportResponses(id), fetchReportComparison(id)]); setData({ report, channels, institutions, responses, comparison }); } catch (caught) { setError(caught); } finally { setLoading(false); } }, [id]);
  useEffect(() => { void load(); }, [load]);
  const evidenceQuery = useCallback(() => fetchPublicEvidence("reports", id), [id]);
  const { data: evidence, refresh: refreshEvidence } = useApiQuery(evidenceQuery);
  if (loading) return <div className="content-wrap detail-loading"><LoadingSkeleton lines={10}/></div>;
  if (error) return <div className="content-wrap page-space"><ErrorState error={error} retry={() => void load()}/></div>;
  if (!data) return null;
  const { report } = data;
  return <div className="report-detail"><section className="detail-hero"><div className="content-wrap"><Link className="back-link" href="/civic-action">← Civic Action / Reports</Link><div className="detail-hero__top"><div><p className="eyebrow">CITIZEN REPORT</p><h1>Report status</h1><p>This page shows the public report status. Status updates are not available here.</p></div><StatusBadge value={report.status} kind="report"/></div><div className="detail-meta"><span><Icon name="report"/> {report.category}</span><span><Icon name="clock"/> Submitted {formatDate(report.submitted_at)}</span><Link href={`/projects/${report.project_id}`}><Icon name="projects"/> View project</Link></div></div></section>
    <div className="content-wrap report-grid"><div><section className="detail-section"><div className="section-heading"><h2>Status history</h2><span>Updates supplied by the service</span></div>{report.status_history.length ? <ol className="timeline report-timeline">{report.status_history.map((entry, index) => <li key={`${entry.to_status}-${index}`}><i/><div><StatusBadge value={entry.to_status} kind="report"/><p>{entry.from_status ? `${entry.from_status.replaceAll("_", " ")} → ${entry.to_status.replaceAll("_", " ")}` : `Status set to ${entry.to_status.replaceAll("_", " ")}`}</p><small>{formatDate(entry.created_at)}</small></div></li>)}</ol> : <EmptyState title="No status history yet" body="The report is currently recorded without public status transitions."/>}</section><Comparison comparison={data.comparison} responses={data.responses}/><section className="detail-section"><div className="section-heading"><h2>Photos and documents</h2><span>Shared by citizens, not verified</span></div>{evidence?.length ? <EvidenceGallery items={evidence}/> : <EmptyState title="No evidence on this report yet" body="Photos or documents added to this report will appear here."/>}</section></div>
      <aside><section className="aside-card evidence-upload"><div className="aside-card__icon"><Icon name="upload"/></div><h2>Add evidence to this report</h2><p>Share a photo or document that supports this report. Evidence is shared by citizens and is not verification.</p><EvidenceUploadForm path={`/reports/${report.id}/evidence`} submitLabel="Add evidence" onUploaded={() => void refreshEvidence()}/></section><Channels channels={data.channels}/><Institutions institutions={data.institutions}/></aside></div>
  </div>;
}

function Channels({ channels }: { channels: ReportingChannel[] }) { return <section className="aside-card"><h2>Reporting channels</h2>{channels.length ? <ul className="simple-list">{channels.map((channel) => <li key={channel.id}><strong>{channel.display_label ?? channel.office_name}</strong><span>{channel.channel_type} · {channel.destination}</span></li>)}</ul> : <EmptyState title="No channels linked" body="No reporting channel is currently published for this report."/>}</section>; }
function Institutions({ institutions }: { institutions: Institution[] }) { return <section className="aside-card"><h2>Institutions</h2>{institutions.length ? <ul className="simple-list">{institutions.map((item) => <li key={item.institution_id}><strong>{item.institution_name}</strong><span>{item.institution_role.replaceAll("_", " ")} · {item.relationship_type}</span></li>)}</ul> : <EmptyState title="No institutions linked" body="No institution relationship is currently published for this report."/>}</section>; }
function Comparison({ comparison, responses }: { comparison: ReportComparison; responses: InstitutionResponse[] }) { return <section className="detail-section"><div className="section-heading"><h2>Issue & institutional response</h2><span>Public report view</span></div><div className="comparison-grid"><article><p className="eyebrow">ORIGINAL ISSUE</p><strong>{comparison.issue.category}</strong><p>{comparison.issue.description}</p><small>Submitted {formatDate(comparison.issue.submitted_at)}</small></article><div>{responses.length ? responses.map((response) => <article className="institution-response" key={response.response_id}><p className="eyebrow">INSTITUTION RESPONSE</p><strong>{response.institution_name}</strong><p>{response.content}</p><small>{formatDate(response.created_at)}</small></article>) : <EmptyState title="No response yet" body="No institutional response has been provided through the public API."/>}</div></div></section>; }
