/**
 * Reports submitted from this browser, so citizens can reopen them without
 * keeping the reference themselves. Stored only in localStorage; nothing about
 * the citizen is sent to the backend.
 */

import type { ReportCategory } from "./api";

export interface MyReport {
  id: string;
  project_id: string;
  project_name: string;
  category: ReportCategory;
  submitted_at: string;
}

const storageKey = "civicact-my-reports";
const maxReports = 50;

export function getMyReports(): MyReport[] {
  try {
    const parsed: unknown = JSON.parse(window.localStorage.getItem(storageKey) ?? "[]");
    return Array.isArray(parsed) ? (parsed as MyReport[]) : [];
  } catch {
    return [];
  }
}

export function rememberReport(report: MyReport): void {
  try {
    const others = getMyReports().filter((item) => item.id !== report.id);
    window.localStorage.setItem(storageKey, JSON.stringify([report, ...others].slice(0, maxReports)));
  } catch {
    // Storage unavailable: the confirmation still shows the reference to copy.
  }
}

export function forgetReport(reportId: string): void {
  try {
    window.localStorage.setItem(storageKey, JSON.stringify(getMyReports().filter((item) => item.id !== reportId)));
  } catch {
    // Nothing to forget when storage is unavailable.
  }
}
