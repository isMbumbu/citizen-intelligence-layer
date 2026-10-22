"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { type ProjectDetail, type ProjectFilters, type ProjectListItem, type ProjectStatus, type TaxonomyCategory, fetchCategories, fetchProjects } from "@/lib/api";
import { useApiQuery, useDebouncedValue } from "@/lib/use-api-query";
import { EmptyState, ErrorState, Icon, LoadingSkeleton, ProgressBar, StatusBadge, formatMoney } from "./ui";
import { HeroCarousel } from "./hero-carousel";

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

function projectImage(project: ProjectListItem) {
  const source = `${project.category.code} ${project.project_type ?? ""}`.toLowerCase();
  if (source.includes("water")) return "/water-project-illustration.jpg";
  if (source.includes("health") || source.includes("clinic")) return "/health-project-illustration.jpg";
  if (source.includes("road") || source.includes("transport")) return "/road-project-illustration.jpg";
  return null;
}

export function ProjectCard({ project, detail }: { project: ProjectListItem; detail?: ProjectDetail }) {
  const finance = detail?.financial_summary.allocated ?? detail?.financial_summary.contracted ?? detail?.financial_summary.spent;
  const image = projectImage(project);
  return <article className="project-card">
    <Link href={`/projects/${project.id}`} className="project-card__media-wrap" aria-label={`View ${project.name}`}>
      {image ? <Image src={image} alt={`Illustration of a ${project.category.name.toLowerCase()} project; this image is not a project record`} className="project-card__image" fill sizes="(max-width: 760px) 100vw, (max-width: 1050px) 50vw, 25vw"/> : <div className="project-card__image-placeholder"><Icon name="folder" size={30}/><span>Illustrative image unavailable</span></div>}
      <span className="illustration-label">Illustration</span>
      <span className="project-card__badge-overlay"><StatusBadge value={project.status}/></span>
    </Link>
    <div className="project-card__body">
      <div className="project-card__meta"><span>{project.location.county}</span><span aria-hidden="true">·</span><span>{project.location.ward}</span><span aria-hidden="true">·</span><span className="project-card__cat-label">{project.category.name}</span></div>
      <h3 className="project-card__title"><Link href={`/projects/${project.id}`}>{project.name}</Link></h3>
      <p className="project-card__description">{project.description}</p>
      <div className="project-card__metrics">
        <div className="project-card__finance"><span className="project-card__finance-label">{finance?.kind ? finance.kind.toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase()) : "Financial data"}</span><strong>{finance ? formatMoney(finance.amount, finance.currency) : "Not available"}</strong></div>
        {detail?.progress && <div className="project-card__progress"><span className="project-card__finance-label">Reported progress</span><ProgressBar value={detail.progress.percentage}/></div>}
      </div>
      <div className="project-card__footer"><span className="project-card__audit-mark"><Icon name="evidence" size={13}/> Public record</span><Link className="project-card__cta" href={`/projects/${project.id}`}>Inspect record <Icon name="arrow" size={13}/></Link></div>
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
  return <div className="active-filters-bar" aria-label="Active project filters"><span className="active-filters-bar__label">Showing results for</span><div className="active-filters-bar__tags">{entries.map((item) => <span className="active-filter-tag" key={item}>{item}</span>)}</div><button className="active-filters-bar__reset" type="button" onClick={onReset}>Reset all filters</button></div>;
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
  return <section className="explorer-container">
    {!featured && <header className="explorer-header"><div><p className="eyebrow">PUBLIC PROJECT EXPLORER</p><h1>{title}</h1>{intro && <p className="explorer-header__intro">{intro}</p>}</div></header>}
    <div className="search-strip"><form className="search-box" onSubmit={(event) => { event.preventDefault(); updateUrl({ ...filters, search: searchInput.trim() }, 1); }}><Icon name="search" size={18} className="search-box__icon"/><input value={searchInput} maxLength={120} onChange={(event) => setSearchInput(event.target.value)} placeholder="Search projects, counties, wards, or keywords..." aria-label="Search public projects"/>{searchInput && <button className="search-box__clear" type="button" aria-label="Clear search" onClick={() => { setSearchInput(""); updateUrl({ ...filters, search: "" }, 1); }}><Icon name="close" size={16}/></button>}<button className="button button--red" type="submit">Search</button></form><button className="mobile-filters-trigger" type="button" onClick={() => setShowFilters(!showFilters)} aria-expanded={showFilters}><Icon name="filter" size={16}/> Filters</button></div>
    <ActiveFilters filters={filters} categories={categories} onReset={clear}/>
    {showFilters && <div className="mobile-filter-panel"><FilterControls mobile filters={filters} setFilters={setFilters} categories={categories} publicProjects={allProjects}/><button className="text-button text-button--danger" onClick={clear}>Clear filters</button></div>}
    <div className="explorer-layout"><aside className="explorer-sidebar"><div className="sidebar-box"><div className="sidebar-box__title"><Icon name="filter" size={16}/><h2>Filter projects</h2></div><FilterControls filters={filters} setFilters={setFilters} categories={categories} publicProjects={allProjects}/><button className="text-button text-button--danger" onClick={clear}>Reset filters</button></div><div className="sidebar-box sidebar-box--quiet"><h3 className="sidebar-box__heading">Quick links</h3><ul className="sidebar-links"><li><Link href="/civic-action"><Icon name="report" size={16}/><span><strong>Report an issue</strong><small>Help review a project</small></span></Link></li><li><Link href="/projects"><Icon name="projects" size={16}/><span><strong>View all projects</strong><small>Browse public records</small></span></Link></li><li><Link href="/taxonomy"><Icon name="folder" size={16}/><span><strong>Browse taxonomy</strong><small>Categories and subtypes</small></span></Link></li></ul></div></aside>
      <div className="explorer-results"><div className="results-header"><h2>{featured ? "Featured Projects" : "Public Project Catalog"}</h2>{featured ? <Link href="/projects">View all projects <Icon name="arrow" size={14}/></Link> : data && <span className="results-count">{data.total} public project{data.total === 1 ? "" : "s"}</span>}</div>
        {loading ? <div className="project-grid project-grid--loading"><LoadingSkeleton lines={7}/><LoadingSkeleton lines={7}/><LoadingSkeleton lines={7}/></div> : error ? <ErrorState error={error} retry={() => void refresh()}/> : data && data.items.length > 0 ? <><div className="project-grid">{data.items.map((project) => <ProjectCard key={project.id} project={project}/>)}</div>{!featured && <div className="pagination-bar"><span className="pagination-bar__info" aria-live="polite">Page {page} of {totalPages}</span><div><button disabled={page <= 1} onClick={() => updateUrl(filters, page - 1)}>Previous</button><button disabled={page >= totalPages} onClick={() => updateUrl(filters, page + 1)}>Next</button></div></div>}</> : <EmptyState title="No public projects match these filters" body="Try clearing a filter or broadening your search." action={<button className="text-button" onClick={clear}>Clear filters <Icon name="arrow" size={14}/></button>}/>}</div>
    </div>
  </section>;
}

function PlatformStats({ projectCount }: { projectCount: number | undefined }) {
  const stats = [
    { label: "Public projects", value: projectCount === undefined ? "Loading" : projectCount.toLocaleString("en-KE"), note: "Records available now" },
    { label: "Financial records", value: "By project", note: "Open a record for details" },
    { label: "Citizen reports", value: "Track by code", note: "Use your report reference" },
    { label: "Evidence", value: "Project linked", note: "Sources shown with records" },
  ];
  return <aside className="hero-metric-card" aria-label="Public information available">
    <div className="hero-metric-card__header"><h2>Public information</h2><span className="font-mono text-xs">API v1</span></div>
    <div className="hero-metrics-grid">{stats.map((item) => <div className="hero-metric" key={item.label}><span className="hero-metric__label">{item.label}</span><strong>{item.value}</strong><small>{item.note}</small></div>)}</div>
    <Link href="/projects" className="button button--outline button--full hero-metric-card__cta"><Icon name="projects" size={15}/><span>Browse project records</span></Link>
  </aside>;
}

export function CivicHome() {
  const query = useCallback(() => fetchProjects({ page_size: 4 }), []);
  const { data, error, loading, refresh } = useApiQuery(query);
  const featured = data?.items ?? [];
  const router = useRouter();
  const [search, setSearch] = useState("");
  const submitSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const value = search.trim();
    router.push(value ? `/projects?search=${encodeURIComponent(value)}` : "/projects");
  };

  return <div className="home-page">
    <section className="hero-section">
      <HeroCarousel />
      <div className="content-wrap hero-section__content">
        <div className="hero-section__text">
          <div className="hero-kicker"><span>REPUBLIC OF KENYA</span><span className="hero-kicker__flag" aria-hidden="true"><i className="flag-green"/><i className="flag-red"/><i className="flag-white"/></span><span>CITIZEN INTELLIGENCE LAYER</span></div>
          <h1 className="hero-heading">Better public projects.<br/><strong>Accountable</strong> communities.</h1>
          <p className="hero-lead">Explore public project records, follow budgets and sources, and report what you see in your community.</p>
          <form className="hero-search-bar" onSubmit={submitSearch}>
            <Icon name="search" size={20} className="hero-search-bar__icon"/>
            <input value={search} onChange={(event) => setSearch(event.target.value)} maxLength={120} placeholder="Search by project name, county, ward, or contractor..." aria-label="Search public projects"/>
            <button type="submit" className="button button--red">Explore Projects</button>
          </form>
          <div className="hero-quick-tags"><span className="hero-quick-tags__label">Browse:</span><Link href="/projects" className="hero-tag">Public projects</Link><Link href="/evidence" className="hero-tag">Evidence &amp; sources</Link><Link href="/civic-action" className="hero-tag">Civic reports</Link></div>
        </div>
        <PlatformStats projectCount={data?.total}/>
      </div>
    </section>

    <section className="home-featured-section content-wrap">
      <div className="section-head"><div><p className="eyebrow">PUBLIC PROJECT RECORDS</p><h2>Projects to explore</h2></div><Link href="/projects" className="section-head__link"><span>Browse all projects</span><Icon name="arrow" size={14}/></Link></div>
      {loading ? <div className="project-grid project-grid--four"><LoadingSkeleton lines={7}/><LoadingSkeleton lines={7}/><LoadingSkeleton lines={7}/><LoadingSkeleton lines={7}/></div> : error ? <ErrorState error={error} retry={() => void refresh()}/> : featured.length ? <div className="project-grid project-grid--four">{featured.map((project) => <ProjectCard project={project} key={project.id}/>)}</div> : <EmptyState title="No public projects available yet" body="The project service has not returned any public records."/>}
    </section>

    <section className="home-triad content-wrap" aria-label="How the platform supports civic oversight">
      <article className="triad-card"><div className="triad-card__icon triad-card__icon--green"><Icon name="shield" size={24}/></div><h3>Follow the source</h3><p>Open project records to review the source information and evidence available for each claim.</p><Link href="/evidence" className="triad-card__link">Explore evidence <span aria-hidden="true">→</span></Link></article>
      <article className="triad-card"><div className="triad-card__icon triad-card__icon--red"><Icon name="alert-triangle" size={24}/></div><h3>Understand the signals</h3><p>Review prompts highlight information that may need attention. They are not findings or accusations.</p><Link href="/projects" className="triad-card__link">Browse projects <span aria-hidden="true">→</span></Link></article>
      <article className="triad-card"><div className="triad-card__icon triad-card__icon--blue"><Icon name="megaphone" size={24}/></div><h3>Share what you see</h3><p>Submit a citizen report about a project and keep its reference to check the status later.</p><Link href="/civic-action" className="triad-card__link">Report an issue <span aria-hidden="true">→</span></Link></article>
    </section>
  </div>;
}
