"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";
import { type PublicEvidenceItem, fetchCategories, fetchEvidenceFeed, fetchProjects } from "@/lib/api";
import { attachedToLabel, evidenceKindLabel, processingLabel } from "@/lib/labels";
import { useApiQuery } from "@/lib/use-api-query";
import { EmptyState, ErrorState, Icon, LoadingSkeleton, formatDate } from "./ui";
import { PageIntro } from "./site-shell";
import { EvidenceImage } from "./evidence-gallery";

const pageSize = 24;

async function loadFilterOptions() {
  const [categories, projects] = await Promise.all([fetchCategories(), fetchProjects({ page_size: 100 })]);
  const counties = Array.from(new Set(projects.items.map((project) => project.location.county))).sort();
  return { categories, counties, projects: projects.items };
}

function EvidenceCard({ item }: { item: PublicEvidenceItem }) {
  return <article className="evidence-card">
    <Link href={`/evidence/${item.id}`} className="evidence-card__media" aria-label={`Open ${evidenceKindLabel(item.mime_type).toLowerCase()} for ${item.project_name}`}>
      {item.kind === "image"
        ? <EvidenceImage id={item.id} alt={`${evidenceKindLabel(item.mime_type)} for ${item.project_name}`}/>
        : <span className="evidence-tile__doc"><Icon name="evidence" size={30}/><span>{item.mime_type === "application/pdf" ? "PDF document" : "Document"}</span></span>}
    </Link>
    <div className="evidence-card__body">
      <span className="trust-chip trust-chip--citizen">Citizen-submitted</span>
      {item.review_status === "UNDER_REVIEW" && <span className="trust-chip trust-chip--review">Under review</span>}
      <h3><Link href={`/evidence/${item.id}`}>{evidenceKindLabel(item.mime_type)}</Link></h3>
      <p className="evidence-card__project"><Link href={`/projects/${item.project_id}`}>{item.project_name}</Link></p>
      <small>{item.county} · {item.category}</small>
      <small>{attachedToLabel(item.attached_to)} · {formatDate(item.uploaded_at)}</small>
      <small>{item.review_status === "UNDER_REVIEW" ? "Being reviewed" : "Not yet reviewed"} · {processingLabel(item.processing_state)}</small>
    </div>
  </article>;
}

function ReferenceLookup() {
  const [reference, setReference] = useState("");
  const router = useRouter();
  return <details className="report-tracker">
    <summary><span><Icon name="evidence"/>Open with a reference</span><small>For when someone has shared an evidence reference with you</small></summary>
    <div className="report-tracker__body"><form className="inline-lookup" onSubmit={(event) => { event.preventDefault(); const value = reference.trim(); if (value) router.push(`/evidence/${encodeURIComponent(value)}`); }}><label htmlFor="evidence-reference">Evidence reference<span>Paste the reference exactly as shared.</span></label><input id="evidence-reference" value={reference} onChange={(event) => setReference(event.target.value)} placeholder="Paste evidence reference" autoComplete="off" required/><button className="button button--outline">Open</button></form></div>
  </details>;
}

export function EvidenceSourcesPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const projectId = searchParams.get("project_id") ?? undefined;
  const categoryId = searchParams.get("category_id") ?? undefined;
  const county = searchParams.get("county") ?? undefined;
  const kindParam = searchParams.get("kind");
  const kind = kindParam === "image" || kindParam === "document" ? kindParam : undefined;
  const page = Number.parseInt(searchParams.get("page") ?? "1", 10) || 1;
  const update = useCallback((next: Record<string, string | undefined>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(next).forEach(([key, value]) => { if (value) params.set(key, value); else params.delete(key); });
    if (!("page" in next)) params.delete("page");
    router.replace(`${pathname}${params.size ? `?${params.toString()}` : ""}`, { scroll: false });
  }, [pathname, router, searchParams]);
  const feedQuery = useCallback(() => fetchEvidenceFeed({ project_id: projectId, category_id: categoryId, county, kind, page, page_size: pageSize }), [projectId, categoryId, county, kind, page]);
  const { data, error, loading, refresh } = useApiQuery(feedQuery);
  const { data: options } = useApiQuery(loadFilterOptions);
  const projectName = useMemo(() => options?.projects.find((project) => project.id === projectId)?.name, [options, projectId]);
  const filtered = Boolean(projectId || categoryId || county || kind);
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return <>
    <PageIntro eyebrow="EVIDENCE & SOURCES" title="Evidence & Sources" body="See the photos and documents citizens have shared about public projects. Official sources are listed on each project record, kept separate from citizen evidence."/>
    <div className="content-wrap page-space evidence-browse">
      <section className="evidence-kinds" aria-label="Kinds of evidence">
        <article><span className="trust-chip trust-chip--official">Official source</span><p>Published documents and records behind each project fact. Find them under <strong>Evidence &amp; sources</strong> on any project page.</p><Link href="/projects">Browse projects <Icon name="arrow" size={13}/></Link></article>
        <article><span className="trust-chip trust-chip--citizen">Citizen-submitted</span><p>Photos and documents shared by citizens. Useful context, but not verified. Location and camera details are removed from photos before publishing.</p><Link href="/community-safety">How evidence is reviewed <Icon name="arrow" size={13}/></Link></article>
      </section>

      <div className="report-filters" role="group" aria-label="Filter evidence">
        <label className="filter-field" htmlFor="evidence-county"><span>County</span><select id="evidence-county" value={county ?? ""} onChange={(event) => update({ county: event.target.value || undefined })}><option value="">All counties</option>{options?.counties.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
        <label className="filter-field" htmlFor="evidence-category"><span>Category</span><select id="evidence-category" value={categoryId ?? ""} onChange={(event) => update({ category_id: event.target.value || undefined })}><option value="">All categories</option>{options?.categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
        <label className="filter-field" htmlFor="evidence-kind"><span>Type</span><select id="evidence-kind" value={kind ?? ""} onChange={(event) => update({ kind: event.target.value || undefined })}><option value="">Photos and documents</option><option value="image">Photos</option><option value="document">Documents</option></select></label>
        <label className="filter-field" htmlFor="evidence-project"><span>Project</span><select id="evidence-project" value={projectId ?? ""} onChange={(event) => update({ project_id: event.target.value || undefined })}><option value="">All projects</option>{options?.projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}{projectId && !projectName && <option value={projectId}>Selected project</option>}</select></label>
        {filtered && <button type="button" className="text-button" onClick={() => update({ project_id: undefined, category_id: undefined, county: undefined, kind: undefined })}>Reset all</button>}
      </div>

      {loading ? <LoadingSkeleton lines={6}/> : error ? <ErrorState error={error} retry={() => void refresh()}/> : data && data.items.length ? <>
        <p className="results-count" aria-live="polite">{data.total} item{data.total === 1 ? "" : "s"} of citizen evidence</p>
        <div className="evidence-card-grid">{data.items.map((item) => <EvidenceCard key={item.id} item={item}/>)}</div>
        {totalPages > 1 && <div className="pagination-bar"><span className="pagination-bar__info">Page {page} of {totalPages}</span><div><button disabled={page <= 1} onClick={() => update({ page: String(page - 1) })}>Previous</button><button disabled={page >= totalPages} onClick={() => update({ page: String(page + 1) })}>Next</button></div></div>}
      </> : <EmptyState title={filtered ? "No evidence matches these filters" : "No citizen evidence yet"} body={filtered ? "Try a different county, category, or type." : "Photos and documents citizens share on project pages will appear here."} action={<Link className="text-button" href="/projects">Find a project to add evidence <Icon name="arrow" size={14}/></Link>}/>}
      <ReferenceLookup/>
    </div>
  </>;
}
