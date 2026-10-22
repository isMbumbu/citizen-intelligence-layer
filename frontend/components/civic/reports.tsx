"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { type PublicReportItem, type ReportCategory, type ReportStatus, fetchReports } from "@/lib/api";
import { type MyReport, forgetReport, getMyReports } from "@/lib/my-reports";
import { useApiQuery } from "@/lib/use-api-query";
import { EmptyState, ErrorState, Icon, LoadingSkeleton, StatusBadge, formatDate } from "./ui";
import { PageIntro } from "./site-shell";

const statuses: ReportStatus[] = ["SUBMITTED", "UNDER_REVIEW", "REFERRED", "RESPONDED", "RESOLVED", "CLOSED"];
const categories: ReportCategory[] = ["QUALITY", "DELAY", "ACCESS", "SAFETY", "OTHER"];
const pageSize = 15;

export function humanLabel(value: string) {
  return value.replaceAll("_", " ").toLowerCase().replace(/^\w/, (letter) => letter.toUpperCase());
}

export function ReportRow({ report, showProject = true }: { report: PublicReportItem | MyReport; showProject?: boolean }) {
  return <li className="report-row">
    <Link href={`/reports/${report.id}`}>
      <span className="report-row__main">
        {showProject && <strong>{report.project_name}</strong>}
        <small>{humanLabel(report.category)} · submitted {formatDate(report.submitted_at)}</small>
      </span>
      {"status" in report && <StatusBadge value={report.status} kind="report"/>}
      <Icon name="arrow" size={14}/>
    </Link>
  </li>;
}

function MyReports() {
  const [reports, setReports] = useState<MyReport[]>();
  useEffect(() => { setReports(getMyReports()); }, []);
  if (reports === undefined) return null;
  return <section className="detail-section">
    <div className="section-heading"><h2>My reports</h2><span>Saved in this browser only</span></div>
    {reports.length ? <ul className="report-list">{reports.map((report) => <li className="report-row report-row--mine" key={report.id}>
      <Link href={`/reports/${report.id}`}><span className="report-row__main"><strong>{report.project_name}</strong><small>{humanLabel(report.category)} · submitted {formatDate(report.submitted_at)}</small></span><span className="report-row__cta">Check status</span><Icon name="arrow" size={14}/></Link>
      <button type="button" className="report-row__forget" aria-label={`Remove report on ${report.project_name} from this browser`} onClick={() => { forgetReport(report.id); setReports(getMyReports()); }}><Icon name="close" size={14}/></button>
    </li>)}</ul> : <EmptyState title="No reports from this browser yet" body="Reports you submit here are saved on this device so you can check them later without the reference." action={<Link className="text-button" href="/civic-action">Report an issue <Icon name="arrow" size={14}/></Link>}/>}
  </section>;
}

function ReportLookup() {
  const [id, setId] = useState("");
  const router = useRouter();
  return <details className="report-tracker">
    <summary><span><Icon name="clock"/>Have a report reference?</span><small>Useful for reports made on another device</small></summary>
    <div className="report-tracker__body"><form className="inline-lookup" onSubmit={(event) => { event.preventDefault(); const reference = id.trim(); if (reference) router.push(`/reports/${encodeURIComponent(reference)}`); }}><label htmlFor="report-reference">Report reference<span>Paste the reference from your confirmation.</span></label><input id="report-reference" value={id} onChange={(event) => setId(event.target.value)} placeholder="Paste report reference" autoComplete="off" required/><button className="button button--outline">Check status</button></form></div>
  </details>;
}

function AllReports() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const status = statuses.find((value) => value === searchParams.get("status"));
  const category = categories.find((value) => value === searchParams.get("category"));
  const projectId = searchParams.get("project_id") ?? undefined;
  const page = Number.parseInt(searchParams.get("page") ?? "1", 10) || 1;
  const update = useCallback((next: Record<string, string | undefined>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(next).forEach(([key, value]) => { if (value) params.set(key, value); else params.delete(key); });
    if (!("page" in next)) params.delete("page");
    router.replace(`${pathname}${params.size ? `?${params.toString()}` : ""}`, { scroll: false });
  }, [pathname, router, searchParams]);
  const query = useCallback(() => fetchReports({ status, category, project_id: projectId, page, page_size: pageSize }), [status, category, projectId, page]);
  const { data, error, loading, refresh } = useApiQuery(query);
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const projectName = useMemo(() => projectId && data?.items[0]?.project_name, [projectId, data]);
  return <section className="detail-section">
    <div className="section-heading"><h2>All citizen reports</h2><span>Citizen submissions, not verified findings</span></div>
    <div className="report-filters">
      <label className="filter-field" htmlFor="report-status"><span>Status</span><select id="report-status" value={status ?? ""} onChange={(event) => update({ status: event.target.value || undefined })}><option value="">All statuses</option>{statuses.map((value) => <option key={value} value={value}>{humanLabel(value)}</option>)}</select></label>
      <label className="filter-field" htmlFor="report-category"><span>Issue type</span><select id="report-category" value={category ?? ""} onChange={(event) => update({ category: event.target.value || undefined })}><option value="">All issue types</option>{categories.map((value) => <option key={value} value={value}>{humanLabel(value)}</option>)}</select></label>
      {projectId && <button type="button" className="active-filter-tag report-filters__project" onClick={() => update({ project_id: undefined })}>Project: {projectName || "selected project"} <Icon name="close" size={12}/></button>}
    </div>
    {loading ? <LoadingSkeleton lines={6}/> : error ? <ErrorState error={error} retry={() => void refresh()}/> : data && data.items.length ? <>
      <p className="results-count" aria-live="polite">{data.total} report{data.total === 1 ? "" : "s"}</p>
      <ul className="report-list">{data.items.map((report) => <ReportRow key={report.id} report={report}/>)}</ul>
      {totalPages > 1 && <div className="pagination-bar"><span className="pagination-bar__info">Page {page} of {totalPages}</span><div><button disabled={page <= 1} onClick={() => update({ page: String(page - 1) })}>Previous</button><button disabled={page >= totalPages} onClick={() => update({ page: String(page + 1) })}>Next</button></div></div>}
    </> : <EmptyState title="No reports match" body={status || category || projectId ? "Try clearing a filter." : "No citizen reports have been submitted yet."}/>}
  </section>;
}

export function ReportsPage() {
  return <>
    <PageIntro eyebrow="CITIZEN REPORTS" title="Reports" body="See what citizens have reported and how each report is progressing. Report descriptions stay on each report's own page; contact details are never shown.">
      <Link href="/civic-action" className="button button--red page-intro__cta"><Icon name="report" size={16}/> Report an issue</Link>
    </PageIntro>
    <div className="content-wrap page-space reports-layout">
      <MyReports/>
      <ReportLookup/>
      <AllReports/>
    </div>
  </>;
}
