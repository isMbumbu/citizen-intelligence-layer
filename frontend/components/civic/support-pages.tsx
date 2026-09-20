"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { type TaxonomyCategory, fetchCategories } from "@/lib/api";
import { ProjectExplorer } from "./discovery";
import { EmptyState, ErrorState, Icon, LoadingSkeleton } from "./ui";
import { PageIntro } from "./site-shell";

export function CivicActionPage() {
  return <><PageIntro eyebrow="CIVIC ACTION" title="Report an issue" body="Choose a public project, describe what you have observed, and submit a citizen report. Reports are not treated as verification."/><div className="content-wrap page-space"><details className="report-tracker"><summary><span><Icon name="clock"/>Already submitted a report?</span><small>Track it with your report reference</small></summary><div className="report-tracker__body"><p>Use the report reference shown after submission. This is optional and is only needed when you want to check a previous report.</p><ReportLookup/></div></details></div><ProjectExplorer title="Choose a project" intro="Search public projects, then open the one you want to report on."/></>;
}

function ReportLookup() { const [id, setId] = useState(""); const router = useRouter(); return <form className="inline-lookup" onSubmit={(event) => { event.preventDefault(); const reference = id.trim(); if (reference) router.push(`/reports/${encodeURIComponent(reference)}`); }}><label htmlFor="report-reference">Your report reference<span>Paste the reference from your submission confirmation.</span></label><input id="report-reference" value={id} onChange={(event) => setId(event.target.value)} placeholder="Paste report reference" autoComplete="off" required/><button className="button button--outline">Check report status</button></form>; }

export function TaxonomyPage() {
  const [items, setItems] = useState<TaxonomyCategory[]>(); const [error, setError] = useState<unknown>();
  const load = useCallback(async () => { setError(undefined); try { setItems(await fetchCategories()); } catch (caught) { setError(caught); } }, []);
  useEffect(() => { void load(); }, [load]);
  return <><PageIntro eyebrow="PROJECT TAXONOMY" title="Browse project categories" body="Categories and subtypes come directly from the public API, so this list stays aligned with the backend reference data."/><div className="content-wrap page-space">{error ? <ErrorState error={error} retry={() => void load()}/> : !items ? <LoadingSkeleton lines={8}/> : items.length ? <div className="taxonomy-grid">{items.map((category) => <article key={category.id}><Icon name="folder"/><h2>{category.name}</h2><p>{category.description}</p>{category.subtypes.length ? <ul>{category.subtypes.map((subtype) => <li key={subtype.id}><strong>{subtype.name}</strong><span>{subtype.description}</span></li>)}</ul> : <p className="form-hint">No active subtypes published.</p>}</article>)}</div> : <EmptyState title="No taxonomy published" body="The API did not return active project categories."/>}</div></>;
}

export function CommentsPage() { return <><PageIntro eyebrow="PUBLIC DISCUSSION" title="Project conversations" body="Comments are available within each public project. They are labelled citizen-submitted information and are not verification."/><ProjectExplorer title="Choose a project discussion" intro="Open a project to read or add public comments."/></>; }

export function EvidenceLookupPage() { const [id, setId] = useState(""); const router = useRouter(); const submit = (event: FormEvent) => { event.preventDefault(); router.push(`/evidence/${id}`); }; return <><PageIntro eyebrow="EVIDENCE" title="Evidence records" body="View public evidence metadata, processing state, and files where the backend makes them publicly available."/><div className="content-wrap page-space"><section className="lookup-card"><Icon name="evidence" size={28}/><h2>Open evidence metadata</h2><p>The current API does not expose a global evidence browse list. Enter a public evidence ID from an evidence submission or project link.</p><form onSubmit={submit}><label>Evidence ID<input value={id} onChange={(event) => setId(event.target.value)} placeholder="UUID" required/></label><button className="button button--dark">Open evidence</button></form></section></div></>; }
