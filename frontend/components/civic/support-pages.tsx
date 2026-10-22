"use client";

import Link from "next/link";
import { ProjectExplorer } from "./discovery";
import { Icon } from "./ui";
import { PageIntro } from "./site-shell";

export function CivicActionPage() {
  return <><PageIntro eyebrow="CIVIC ACTION" title="Report an issue" body="Choose a public project, describe what you have observed, and submit a citizen report. Reports are not treated as verification."/><div className="content-wrap page-space"><Link className="report-tracker report-tracker--link" href="/reports"><span><Icon name="clock"/>Already reported something?</span><small>See your reports and their status <Icon name="arrow" size={13}/></small></Link></div><ProjectExplorer title="Choose a project" intro="Search public projects, then open the one you want to report on."/></>;
}

export function CommentsPage() { return <><PageIntro eyebrow="PUBLIC DISCUSSION" title="Project conversations" body="Comments are available within each public project. They are labelled as information shared by citizens, not as verification."/><ProjectExplorer title="Choose a project discussion" intro="Open a project to read or add public comments."/></>; }
