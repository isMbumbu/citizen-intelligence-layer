"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { type TaxonomyCategory, fetchCategories, fetchProjects } from "@/lib/api";
import { useApiQuery } from "@/lib/use-api-query";
import { EmptyState, ErrorState, Icon, LoadingSkeleton } from "./ui";
import { PageIntro } from "./site-shell";

type CategoryWithCount = TaxonomyCategory & { projectCount: number };

async function loadCategories(): Promise<CategoryWithCount[]> {
  const categories = await fetchCategories();
  const counts = await Promise.all(categories.map((category) => fetchProjects({ category_id: category.id, page_size: 1 }).then((page) => page.total)));
  return categories.map((category, index) => ({ ...category, projectCount: counts[index] }));
}

function matches(category: TaxonomyCategory, term: string) {
  const text = [category.name, category.description, ...category.subtypes.flatMap((subtype) => [subtype.name, subtype.description])].join(" ").toLowerCase();
  return text.includes(term);
}

export function CategoriesPage() {
  const { data, error, loading, refresh } = useApiQuery(loadCategories);
  const [search, setSearch] = useState("");
  const term = search.trim().toLowerCase();
  const visible = useMemo(() => (data ?? []).filter((category) => !term || matches(category, term)), [data, term]);
  return <>
    <PageIntro eyebrow="PROJECT CATEGORIES" title="Explore by category" body="Find public projects by what they deliver, from roads and water to health and schools. Pick a category or a specific type to see matching projects."/>
    <div className="content-wrap page-space">
      <div className="search-box categories-search"><Icon name="search" size={18} className="search-box__icon"/><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search categories, e.g. water, clinic, road" aria-label="Search project categories"/>{search && <button className="search-box__clear" type="button" aria-label="Clear search" onClick={() => setSearch("")}><Icon name="close" size={16}/></button>}</div>
      {loading ? <LoadingSkeleton lines={8}/> : error ? <ErrorState error={error} retry={() => void refresh()}/> : !data?.length ? <EmptyState title="No categories published yet" body="Project categories will appear here once they are published."/> : !visible.length ? <EmptyState title={`No categories match "${search.trim()}"`} body="Try a broader word, or browse all projects." action={<button className="text-button" onClick={() => setSearch("")}>Show all categories <Icon name="arrow" size={14}/></button>}/> : <div className="category-grid">{visible.map((category) => <article className="category-card" key={category.id}>
        <div className="category-card__head"><span className="category-card__icon"><Icon name="folder" size={20}/></span><div><h2>{category.name}</h2><span className="category-card__count">{category.projectCount === 0 ? "No projects yet" : `${category.projectCount} project${category.projectCount === 1 ? "" : "s"}`}</span></div></div>
        <p>{category.description}</p>
        {category.subtypes.length > 0 && <div className="category-card__types"><span>Types</span><ul>{category.subtypes.map((subtype) => <li key={subtype.id}><Link href={`/projects?category_id=${category.id}&subtype_id=${subtype.id}`} title={subtype.description}>{subtype.name}</Link></li>)}</ul></div>}
        <Link className="category-card__cta" href={`/projects?category_id=${category.id}`}>{category.projectCount === 0 ? "Open category" : "Browse projects"} <Icon name="arrow" size={14}/></Link>
      </article>)}</div>}
    </div>
  </>;
}
