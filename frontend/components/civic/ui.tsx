"use client";

import Link from "next/link";
import { type ReactNode } from "react";
import { ApiError } from "@/lib/api";

export function Brand({ inverse = false }: { inverse?: boolean }) {
  return (
    <Link href="/" className={`brand ${inverse ? "brand--inverse" : ""}`} aria-label="CIVICACT home">
      <span className="brand-mark" aria-hidden="true"><i /><b /><em /></span>
      <span className="brand-copy"><strong>CIVIC</strong><strong className="brand-act">ACT</strong><small>Public information citizens can understand, verify and act on.</small></span>
    </Link>
  );
}

export function Icon({ name, size = 18 }: { name: "search" | "filter" | "pin" | "folder" | "home" | "projects" | "report" | "comment" | "evidence" | "moderation" | "arrow" | "menu" | "close" | "check" | "upload" | "download" | "shield" | "clock" | "megaphone"; size?: number }) {
  const common = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.9, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true };
  const paths: Record<string, ReactNode> = {
    search: <><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4 4"/></>,
    filter: <><path d="M4 5h16M7 12h10m-7 7h4"/></>,
    pin: <><path d="M20 10c0 5-8 10-8 10S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.2"/></>,
    folder: <><path d="M3 6.5h7l2 2h9v10.8H3z"/><path d="M3 6.5V5h7l2 2"/></>,
    home: <><path d="m3 10 9-7 9 7v10H3z"/><path d="M9 20v-6h6v6"/></>,
    projects: <><rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/></>,
    report: <><path d="M7 3h10l4 18H3z"/><path d="M12 8v5m0 3h.01"/></>,
    comment: <><path d="M20 11.5a7.5 7.5 0 0 1-8 7.5 8.5 8.5 0 0 1-3.6-.8L4 20l1.4-4.2A7.4 7.4 0 0 1 4 11.5 7.5 7.5 0 0 1 12 4a7.5 7.5 0 0 1 8 7.5Z"/><path d="M8 12h.01M12 12h.01M16 12h.01"/></>,
    evidence: <><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v5h5M10 13h5m-5 3h5"/></>,
    moderation: <><path d="M12 3 4 7v5c0 5.1 3.4 8 8 9 4.6-1 8-3.9 8-9V7z"/><path d="m9 12 2 2 4-4"/></>,
    arrow: <path d="M5 12h14m-5-5 5 5-5 5"/>,
    menu: <><path d="M4 7h16M4 12h16M4 17h16"/></>,
    close: <><path d="m6 6 12 12M18 6 6 18"/></>,
    check: <path d="m5 12 4.2 4L19 6.5"/>,
    upload: <><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M5 20h14"/></>,
    download: <><path d="M12 4v12m0 0 4.5-4.5M12 16l-4.5-4.5M5 20h14"/></>,
    shield: <><path d="M12 3 5 6v5c0 4.7 3.1 7.6 7 9 3.9-1.4 7-4.3 7-9V6z"/><path d="m9 11 2 2 4-4"/></>,
    clock: <><circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3.5 2"/></>,
    megaphone: <><path d="m4 13 11-5v8L4 11zM15 10h3.5a2 2 0 0 1 0 4H15M6.5 14l1.3 5H11l-1.2-5"/></>,
  };
  return <svg {...common}>{paths[name]}</svg>;
}

export function LoadingSkeleton({ lines = 3, label = "Loading public information" }: { lines?: number; label?: string }) {
  return <div className="loading-skeleton" role="status" aria-label={label}>{Array.from({ length: lines }, (_, index) => <span key={index} />)}</div>;
}

export function EmptyState({ title = "Nothing to show yet", body, action }: { title?: string; body: string; action?: ReactNode }) {
  return <div className="empty-state"><Icon name="folder" size={22}/><div><strong>{title}</strong><p>{body}</p>{action}</div></div>;
}

export function humanError(error: unknown): string {
  if (!(error instanceof ApiError)) return "We could not load this public information. Please try again.";
  if (error.status === 0) return "The public service is unavailable right now. Please try again shortly.";
  if (error.status === 401 || error.status === 403) return "This item is restricted by the current backend permission boundary. There is no public sign-in flow available.";
  if (error.status === 404) return "This public record could not be found.";
  if (error.status === 409) return "That action conflicts with the record’s current state. Refresh and try again.";
  if (error.status === 422) return "Please check the information entered and try again.";
  if (error.status === 429) return `This action is temporarily rate-limited${error.retryAfter ? `. Try again in ${error.retryAfter} seconds` : ""}.`;
  if (error.status === 503) return "The public service is temporarily unavailable. Please try again later.";
  return "We could not complete that request. Please try again.";
}

export function ErrorState({ error, retry }: { error: unknown; retry?: () => void }) {
  return <div className="error-state" role="alert"><Icon name="report" size={21}/><div><strong>Something needs attention</strong><p>{humanError(error)}</p>{retry && <button className="text-button" onClick={retry}>Try again <Icon name="arrow" size={14}/></button>}</div></div>;
}

export function StatusBadge({ value, kind = "project" }: { value: string; kind?: "project" | "report" | "verification" | "review" }) {
  const label = value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());
  const semantic = value.toLowerCase().replaceAll("_", "-");
  return <span className={`status-badge status-badge--${kind} status-badge--${semantic}`}>{kind === "review" ? "Review signal: " : ""}{label}</span>;
}

export function VerificationBadge({ value }: { value: string | null | undefined }) {
  return <StatusBadge value={value ?? "UNVERIFIED"} kind="verification" />;
}

export function ProgressBar({ value }: { value: string | number | null | undefined }) {
  const progress = typeof value === "number" ? value : Number.parseFloat(value ?? "0");
  const safeProgress = Number.isFinite(progress) ? Math.max(0, Math.min(100, progress)) : 0;
  return <div className="progress-wrap"><div className="progress-bar" aria-label={`${safeProgress}% reported progress`}><span style={{ width: `${safeProgress}%` }} /></div><strong>{safeProgress}%</strong></div>;
}

export function formatDate(value: string | null | undefined) {
  if (!value) return "Not available";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : new Intl.DateTimeFormat("en-KE", { day: "numeric", month: "short", year: "numeric" }).format(date);
}

export function formatMoney(amount: string | number | null | undefined, currency = "KES") {
  if (amount === null || amount === undefined) return "Not available";
  const number = Number(amount);
  if (!Number.isFinite(number)) return "Not available";
  return new Intl.NumberFormat("en-KE", { style: "currency", currency, maximumFractionDigits: 0 }).format(number);
}
