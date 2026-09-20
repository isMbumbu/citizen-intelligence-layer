"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { type ProjectDetail, type ProjectFilters, type ProjectListItem, type ProjectStatus, type TaxonomyCategory, fetchCategories, fetchProjects } from "@/lib/api";
import { useApiQuery, useDebouncedValue } from "@/lib/use-api-query";
import { EmptyState, ErrorState, Icon, LoadingSkeleton, ProgressBar, StatusBadge, formatMoney } from "./ui";

type FilterState = Omit<ProjectFilters, "page" | "page_size">;
const blankFilters: FilterState = { search: "", county: "", ward: "", project_type: "", category_id: "", subtype_id: "", status: undefined };
const statuses: ProjectStatus[] = ["PLANNED", "IN_PROGRESS", "COMPLETED", "ON_HOLD"];

function filtersFromParams(params: URLSearchParams): FilterState {
  const status = params.get("status");
  return {
    search: params.get("search") ?? "",
    county: params.get("county") ?? "",
    ward: params.get("ward") ?? "",
    project_type: params.get("project_type") ?? "",
    category_id: params.get("category_id") ?? "",
    subtype_id: params.get("subtype_id") ?? "",
    status: statuses.includes(status as ProjectStatus) ? status as ProjectStatus : undefined,
  };
}

function projectVisual(project: ProjectListItem) {
  const source = `${project.category.code} ${project.project_type ?? ""}`.toLowerCase();
  if (source.includes("water")) return "project-visual--water";
  if (source.includes("health")) return "project-visual--health";
  if (source.includes("road") || source.includes("transport")) return "project-visual--road";
  return "project-visual--school";
}

export function ProjectCard({ project, detail }: { project: ProjectListItem; detail?: ProjectDetail }) {
  const finance = detail?.financial_summary.allocated ?? detail?.financial_summary.contracted ?? detail?.financial_summary.spent;
  return <article className="project-card">
    <div className={`project-visual ${projectVisual(project)}`} role="img" aria-label="Illustrative project placeholder; no project image is available from the API"><StatusBadge value={project.status}/><span className="project-visual__label">Project image unavailable</span></div>
    <div className="project-card__body"><h3><Link href={`/projects/${project.id}`}>{project.name}</Link></h3><p className="project-description">{project.description}</p>
      <p className="project-place"><Icon name="pin" size={13}/>{project.location.county} <span>·</span> {project.location.ward}</p>
      <div className="project-tags"><span>{project.category.name}</span>{project.project_type && <span>{project.project_type}</span>}</div><p className="project-card__provenance"><Icon name="evidence" size={11}/> Public project record</p>
      <div className="project-money"><div><small>{finance?.kind ? finance.kind.toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase()) : "Financial data"}</small><strong>{finance ? formatMoney(finance.amount, finance.currency) : "Not available"}</strong></div>{detail?.progress && <ProgressBar value={detail.progress.percentage}/>}</div>
      <Link className="card-link" href={`/projects/${project.id}`}>View details <Icon name="arrow" size={14}/></Link>
    </div>
  </article>;
}

function SelectField({ id, label, value, onChange, children, disabled }: { id: string; label: string; value: string; onChange: (value: string) => void; children: React.ReactNode; disabled?: boolean }) {
  return <label className="filter-field" htmlFor={id}><span>{label}</span><select id={id} value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)}>{children}</select></label>;
}

function FilterControls({ filters, setFilters, categories, publicProjects, mobile = false }: { filters: FilterState; setFilters: (next: FilterState) => void; categories: TaxonomyCategory[]; publicProjects: ProjectListItem[]; mobile?: boolean }) {
  const counties = useMemo(() => Array.from(new Set(publicProjects.map((project) => project.location.county))).sort(), [publicProjects]);
  const wards = useMemo(() => Array.from(new Set(publicProjects.filter((project) => !filters.county || project.location.county === filters.county).map((project) => project.location.ward))).sort(), [publicProjects, filters.county]);
  const types = useMemo(() => Array.from(new Set(publicProjects.map((project) => project.project_type).filter((value): value is string => Boolean(value)))).sort(), [publicProjects]);
  const selectedCategory = categories.find((category) => category.id === filters.category_id);
  const update = (key: keyof FilterState, value: string) => setFilters({ ...filters, [key]: value || undefined, ...(key === "category_id" ? { subtype_id: undefined } : {}) });
  return <div className={`filter-controls ${mobile ? "filter-controls--mobile" : ""}`}>
    <SelectField id={`${mobile ? "mobile-" : ""}county`} label="County" value={filters.county ?? ""} onChange={(value) => update("county", value)}><option value="">All Counties</option>{counties.map((value) => <option value={value} key={value}>{value}</option>)}</SelectField>
    <SelectField id={`${mobile ? "mobile-" : ""}ward`} label="Ward" value={filters.ward ?? ""} onChange={(value) => update("ward", value)}><option value="">All Wards</option>{wards.map((value) => <option value={value} key={value}>{value}</option>)}</SelectField>
    <SelectField id={`${mobile ? "mobile-" : ""}type`} label="Project Type" value={filters.project_type ?? ""} onChange={(value) => update("project_type", value)}><option value="">All Types</option>{types.map((value) => <option value={value} key={value}>{value}</option>)}</SelectField>
    <SelectField id={`${mobile ? "mobile-" : ""}category`} label="Category" value={filters.category_id ?? ""} onChange={(value) => update("category_id", value)}><option value="">All Categories</option>{categories.map((value) => <option value={value.id} key={value.id}>{value.name}</option>)}</SelectField>
    <SelectField id={`${mobile ? "mobile-" : ""}subtype`} label="Subtype" value={filters.subtype_id ?? ""} disabled={!selectedCategory} onChange={(value) => update("subtype_id", value)}><option value="">{selectedCategory ? "All Subtypes" : "Choose a category first"}</option>{selectedCategory?.subtypes.map((value) => <option value={value.id} key={value.id}>{value.name}</option>)}</SelectField>
    <SelectField id={`${mobile ? "mobile-" : ""}status`} label="Status" value={filters.status ?? ""} onChange={(value) => update("status", value)}><option value="">All Statuses</option>{statuses.map((value) => <option value={value} key={value}>{value.replaceAll("_", " ")}</option>)}</SelectField>
  </div>;
}

function ActiveFilters({ filters, categories, onReset }: { filters: FilterState; categories: TaxonomyCategory[]; onReset: () => void }) {
  const category = categories.find((item) => item.id === filters.category_id);
  const entries = [
    filters.search && `Search: ${filters.search}`,
    filters.county && `County: ${filters.county}`,
    filters.ward && `Ward: ${filters.ward}`,
    filters.project_type && `Type: ${filters.project_type}`,
    category && `Category: ${category.name}`,
    filters.status && `Status: ${filters.status.replaceAll("_", " ")}`,
  ].filter((item): item is string => Boolean(item));
  if (!entries.length) return null;
  return <div className="active-filters" aria-label="Active project filters"><span>Showing results for</span>{entries.map((item) => <em key={item}>{item}</em>)}<button type="button" onClick={onReset}>Reset all filters</button></div>;
}

export function ProjectExplorer({ title = "All Projects", intro, featured = false }: { title?: string; intro?: string; featured?: boolean }) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const filters = useMemo(() => filtersFromParams(searchParams), [searchParams]);
  const [searchInput, setSearchInput] = useState(filters.search ?? "");
  const [showFilters, setShowFilters] = useState(false);
  const page = Number.parseInt(searchParams.get("page") ?? "1", 10) || 1;
  const debouncedSearch = useDebouncedValue(searchInput.trim(), 350);
  const updateUrl = useCallback((next: FilterState, nextPage = 1) => {
    const params = new URLSearchParams();
    Object.entries(next).forEach(([key, value]) => { if (value) params.set(key, String(value)); });
    if (nextPage > 1) params.set("page", String(nextPage));
    router.replace(`${pathname}${params.size ? `?${params.toString()}` : ""}`, { scroll: false });
  }, [pathname, router]);
  useEffect(() => { setSearchInput(filters.search ?? ""); }, [filters.search]);
  useEffect(() => {
    if (debouncedSearch !== (filters.search ?? "")) updateUrl({ ...filters, search: debouncedSearch }, 1);
  }, [debouncedSearch, filters, updateUrl]);
  const query = useCallback(() => fetchProjects({ ...filters, page, page_size: featured ? 4 : 12 }), [featured, filters, page]);
  const optionsQuery = useCallback(async () => Promise.all([fetchCategories(), fetchProjects({ page_size: 100 })]), []);
  const { data, error, loading, refresh } = useApiQuery(query);
  const { data: options } = useApiQuery(optionsQuery);
  const categories = options?.[0] ?? [];
  const allProjects = options?.[1].items ?? [];
  const setFilters = (next: FilterState) => updateUrl(next, 1);
  const clear = () => { setSearchInput(""); updateUrl(blankFilters, 1); };
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  return <section className={`project-explorer ${featured ? "project-explorer--featured" : ""}`}>
    {!featured && <div className="projects-toolbar"><div><p className="eyebrow">PUBLIC PROJECT EXPLORER</p><h1>{title}</h1>{intro && <p>{intro}</p>}</div></div>}
    <div className="project-search-row"><form onSubmit={(event) => { event.preventDefault(); updateUrl({ ...filters, search: searchInput.trim() }, 1); }}><Icon name="search" size={20}/><input value={searchInput} maxLength={120} onChange={(event) => setSearchInput(event.target.value)} placeholder="Search projects, counties, wards, or keywords..." aria-label="Search public projects"/><button className="button button--red" type="submit">Search</button></form><button className="filters-toggle" onClick={() => setShowFilters(!showFilters)} aria-expanded={showFilters}><Icon name="filter" size={16}/> Filters</button></div>
    <ActiveFilters filters={filters} categories={categories} onReset={clear}/>
    {showFilters && <div className="mobile-filter-panel"><FilterControls mobile filters={filters} setFilters={setFilters} categories={categories} publicProjects={allProjects}/><button className="text-button" onClick={clear}>Clear filters</button></div>}
    <div className="explorer-layout"><aside className="filter-sidebar"><div className="filter-sidebar__title"><Icon name="filter" size={16}/><h2>Filter Projects</h2></div><FilterControls filters={filters} setFilters={setFilters} categories={categories} publicProjects={allProjects}/><button className="text-button" onClick={clear}>Clear filters</button><div className="quick-links"><h3>Quick Links</h3><Link href="/civic-action"><Icon name="report"/>Report an Issue<small>Help us verify a project</small></Link><Link href="/projects"><Icon name="projects"/>View All Projects<small>Browse the full list</small></Link><Link href="/taxonomy"><Icon name="folder"/>Browse Taxonomy<small>Categories and subtypes</small></Link></div><p className="sidebar-trust"><span>🇰🇪</span> Kenya <i/> Transparency <i/> Accountability</p></aside>
      <div className="project-results"><div className="section-heading"><h2>{featured ? "Featured Projects" : "Projects"}</h2>{featured ? <Link href="/projects">View all projects <Icon name="arrow" size={14}/></Link> : data && <span>{data.total} public project{data.total === 1 ? "" : "s"}</span>}</div>
        {loading ? <div className="project-grid project-grid--loading"><LoadingSkeleton lines={7}/><LoadingSkeleton lines={7}/><LoadingSkeleton lines={7}/></div> : error ? <ErrorState error={error} retry={() => void refresh()}/> : data && data.items.length > 0 ? <><div className="project-grid">{data.items.map((project) => <ProjectCard key={project.id} project={project}/>)}</div>{!featured && <div className="pagination"><button disabled={page <= 1} onClick={() => updateUrl(filters, page - 1)}>Previous</button><span aria-live="polite">Page {page} of {totalPages}</span><button disabled={page >= totalPages} onClick={() => updateUrl(filters, page + 1)}>Next</button></div>}</> : <EmptyState title="No public projects match these filters" body="Try clearing a filter or broadening your search." action={<button className="text-button" onClick={clear}>Clear filters <Icon name="arrow" size={14}/></button>}/>}</div>
    </div>
  </section>;
}

function PlatformStats({ projectCount }: { projectCount: number | undefined }) {
  const stats = [
    { icon: "projects" as const, label: "Public Projects", value: projectCount === undefined ? "…" : String(projectCount), tone: "green", href: "/projects" },
    { icon: "report" as const, label: "Citizen Reports", value: "—", tone: "red", href: "/civic-action" },
    { icon: "comment" as const, label: "Comments", value: "—", tone: "blue", href: "/comments" },
    { icon: "evidence" as const, label: "Evidence Files", value: "—", tone: "purple", href: "/evidence" },
  ];
  return <aside className="platform-stats"><h2>Platform at a glance</h2><div>{stats.map((item) => <Link key={item.label} href={item.href} className="stat-card"><span className={`stat-icon stat-icon--${item.tone}`}><Icon name={item.icon} size={18}/></span><strong>{item.value}</strong><small>{item.label}</small><em>{item.value === "—" ? "Not exposed by API" : <>View all <Icon name="arrow" size={12}/></>}</em></Link>)}</div></aside>;
}

export function CivicHome() {
  const query = useCallback(() => fetchProjects({ page_size: 4 }), []);
  const { data, error, loading, refresh } = useApiQuery(query);
  const featured = data?.items ?? [];
  return <>
    <section className="hero"><div className="hero__image"/><div className="hero__shade"/><div className="hero__content content-wrap"><div className="hero-copy"><p className="hero-country">KENYA <span/><i/><b/></p><h1>Better projects.<br/><strong>Stronger</strong> communities.</h1><p>Explore public projects, track spending, report issues,<br className="desktop-only"/> and help build a more transparent Kenya.</p></div><PlatformStats projectCount={data?.total}/></div><div className="hero-search content-wrap"><Link className="screen-reader-link" href="/projects">Browse public projects</Link><HeroSearch/></div></section>
    <section className="home-content content-wrap"><div className="home-main"><aside className="filter-sidebar home-filter-sidebar"><div className="filter-sidebar__title"><Icon name="filter" size={16}/><h2>Filter Projects</h2></div><p className="compact-copy">Use the live explorer to filter by county, ward, type, category, or status.</p><Link className="button button--outline button--full" href="/projects">Open project filters <Icon name="arrow" size={15}/></Link><div className="quick-links"><h3>Quick Links</h3><Link href="/civic-action"><Icon name="report"/>Report an Issue<small>Help us verify a project</small></Link><Link href="/projects"><Icon name="projects"/>View All Projects<small>Browse the full list</small></Link><Link href="/taxonomy"><Icon name="folder"/>Browse Taxonomy<small>Categories and subtypes</small></Link></div><p className="sidebar-trust"><span>🇰🇪</span> Kenya <i/> Transparency <i/> Accountability</p></aside>
      <section className="featured-results"><div className="section-heading"><h2>Featured Projects</h2><Link href="/projects">View all projects <Icon name="arrow" size={14}/></Link></div>{loading ? <div className="project-grid"><LoadingSkeleton lines={7}/><LoadingSkeleton lines={7}/><LoadingSkeleton lines={7}/></div> : error ? <ErrorState error={error} retry={() => void refresh()}/> : featured.length ? <div className="project-grid project-grid--four">{featured.map((project) => <ProjectCard project={project} key={project.id}/>)}</div> : <EmptyState title="No public projects published yet" body="The projects API has not returned any public project records."/>}</section></div>
      <div className="home-bottom"><section className="recent-reports"><div className="section-heading"><h2>Recent Civic Reports</h2><Link href="/civic-action">View all reports <Icon name="arrow" size={14}/></Link></div><EmptyState title="A public reports feed is not available" body="The current API supports submitting and tracking an individual report, but does not publish a list of recent reports." action={<Link className="text-button" href="/civic-action">Report an issue <Icon name="arrow" size={14}/></Link>}/></section><CivicActionCTA/><section className="recent-activity"><div className="section-heading"><h2>Recent Activity</h2><span>View all <Icon name="arrow" size={14}/></span></div><EmptyState title="No public activity feed" body="The current API does not expose a timeline of project or community updates."/></section></div>
    </section>
  </>;
}

function HeroSearch() {
  const [value, setValue] = useState("");
  return <form className="hero-search__form" action="/projects"><Icon name="search" size={20}/><input name="search" value={value} onChange={(event) => setValue(event.target.value)} maxLength={120} placeholder="Search projects, counties, wards, or keywords..." aria-label="Search public projects"/><button className="button button--red" type="submit">Search</button><div className="hero-filter-labels"><span>County</span><span>Ward</span><span>Project Type</span><span>Category</span><span>Status</span><Link href="/projects">Clear filters</Link></div></form>;
}

function CivicActionCTA() {
  return <section className="civic-cta"><Icon name="megaphone" size={28}/><h2>Be the change</h2><p>Report an issue, share evidence,<br/>or join the conversation.</p><Link href="/civic-action" className="button button--red">Report an Issue <Icon name="arrow" size={15}/></Link><Link className="cta-link" href="/help">Learn how it works</Link><div className="cta-landscape" aria-hidden="true"><i/><b/><em/></div></section>;
}
