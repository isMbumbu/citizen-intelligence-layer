"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { type Institution, type InstitutionResponse, type ReportComparison, type ReportDetail, type ReportingChannel, fetchInstitutions, fetchReport, fetchReportChannels, fetchReportComparison, fetchReportResponses } from "@/lib/api";
import { EmptyState, ErrorState, Icon, LoadingSkeleton, StatusBadge, formatDate } from "./ui";

type ReportData = { report: ReportDetail; channels: ReportingChannel[]; institutions: Institution[]; responses: InstitutionResponse[]; comparison: ReportComparison };

export function ReportDetailPage({ id }: { id: string }) {
  const [data, setData] = useState<ReportData>(); const [error, setError] = useState<unknown>(); const [loading, setLoading] = useState(true);
  const load = useCallback(async () => { setLoading(true); setError(undefined); try { const [report, channels, institutions, responses, comparison] = await Promise.all([fetchReport(id), fetchReportChannels(id), fetchInstitutions(id), fetchReportResponses(id), fetchReportComparison(id)]); setData({ report, channels, institutions, responses, comparison }); } catch (caught) { setError(caught); } finally { setLoading(false); } }, [id]);
  useEffect(() => { void load(); }, [load]);
  if (loading) return <div className="content-wrap detail-loading"><LoadingSkeleton lines={10}/></div>;
  if (error) return <div className="content-wrap page-space"><ErrorState error={error} retry={() => void load()}/></div>;
  if (!data) return null;
  const { report } = data;
  return <div className="report-detail"><section className="detail-hero"><div className="content-wrap"><Link className="back-link" href="/civic-action">← Civic Action / Reports</Link><div className="detail-hero__top"><div><p className="eyebrow">CITIZEN REPORT</p><h1>Report status</h1><p>This is a read-only public status view. The current API does not offer public status changes.</p></div><StatusBadge value={report.status} kind="report"/></div><div className="detail-meta"><span><Icon name="report"/> {report.category}</span><span><Icon name="clock"/> Submitted {formatDate(report.submitted_at)}</span><Link href={`/projects/${report.project_id}`}><Icon name="projects"/> View project</Link></div></div></section>
    <div className="content-wrap report-grid"><div><section className="detail-section"><div className="section-heading"><h2>Status history</h2><span>Backend-reported only</span></div>{report.status_history.length ? <ol className="timeline report-timeline">{report.status_history.map((entry, index) => <li key={`${entry.to_status}-${index}`}><i/><div><StatusBadge value={entry.to_status} kind="report"/><p>{entry.from_status ? `${entry.from_status.replaceAll("_", " ")} → ${entry.to_status.replaceAll("_", " ")}` : `Status set to ${entry.to_status.replaceAll("_", " ")}`}</p><small>{formatDate(entry.created_at)}</small></div></li>)}</ol> : <EmptyState title="No status history yet" body="The report is currently recorded without public status transitions."/>}</section><Comparison comparison={data.comparison} responses={data.responses}/></div>
      <aside><Channels channels={data.channels}/><Institutions institutions={data.institutions}/></aside></div>
  </div>;
}

function Channels({ channels }: { channels: ReportingChannel[] }) { return <section className="aside-card"><h2>Reporting channels</h2>{channels.length ? <ul className="simple-list">{channels.map((channel) => <li key={channel.id}><strong>{channel.display_label ?? channel.office_name}</strong><span>{channel.channel_type} · {channel.destination}</span></li>)}</ul> : <EmptyState title="No channels linked" body="No reporting channel is currently published for this report."/>}</section>; }
function Institutions({ institutions }: { institutions: Institution[] }) { return <section className="aside-card"><h2>Institutions</h2>{institutions.length ? <ul className="simple-list">{institutions.map((item) => <li key={item.institution_id}><strong>{item.institution_name}</strong><span>{item.institution_role.replaceAll("_", " ")} · {item.relationship_type}</span></li>)}</ul> : <EmptyState title="No institutions linked" body="No institution relationship is currently published for this report."/>}</section>; }
function Comparison({ comparison, responses }: { comparison: ReportComparison; responses: InstitutionResponse[] }) { return <section className="detail-section"><div className="section-heading"><h2>Issue & institutional response</h2><span>Read-only public view</span></div><div className="comparison-grid"><article><p className="eyebrow">ORIGINAL ISSUE</p><strong>{comparison.issue.category}</strong><p>{comparison.issue.description}</p><small>Submitted {formatDate(comparison.issue.submitted_at)}</small></article><div>{responses.length ? responses.map((response) => <article className="institution-response" key={response.response_id}><p className="eyebrow">INSTITUTION RESPONSE</p><strong>{response.institution_name}</strong><p>{response.content}</p><small>{formatDate(response.created_at)}</small></article>) : <EmptyState title="No response yet" body="No institutional response has been provided through the public API."/>}</div></div></section>; }
