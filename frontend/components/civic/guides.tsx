import Link from "next/link";
import { PageIntro } from "./site-shell";
import { Icon } from "./ui";

export function HowItWorksPage() {
  const steps = [
    { icon: "projects" as const, title: "Find a project", body: "Search or browse public projects by county, category, or status.", href: "/projects", link: "Browse projects" },
    { icon: "evidence" as const, title: "Check the record", body: "Each project shows its budget, progress, official sources, and whether it has been verified.", href: "/categories", link: "Explore by category" },
    { icon: "report" as const, title: "Report what you see", body: "Submit a report on a project, optionally with a photo. Find it again any time under My reports.", href: "/reports", link: "See reports" },
    { icon: "upload" as const, title: "Share evidence", body: "Add photos or documents from a project page so others can see the conditions on the ground.", href: "/evidence", link: "Evidence & Sources" },
  ];
  return <>
    <PageIntro eyebrow="HOW IT WORKS" title="How CivicAct works" body="CivicAct brings public project records together with what citizens observe, and keeps the two clearly apart so you can judge the evidence yourself."/>
    <div className="content-wrap page-space guide-page">
      <ol className="guide-steps">{steps.map((step, index) => <li key={step.title}><span className="guide-steps__icon"><Icon name={step.icon} size={20}/></span><div><small>Step {index + 1}</small><h2>{step.title}</h2><p>{step.body}</p><Link href={step.href}>{step.link} <Icon name="arrow" size={13}/></Link></div></li>)}</ol>
      <section className="guide-section">
        <h2>What the labels mean</h2>
        <dl className="guide-terms">
          <div><dt><span className="trust-chip trust-chip--official">Official source</span></dt><dd>A published document or record that a project fact is based on.</dd></div>
          <div><dt><span className="trust-chip trust-chip--verified">Verified</span></dt><dd>A project record that has been checked and recorded as verified. Only the verification panel on a project can say this.</dd></div>
          <div><dt><span className="trust-chip trust-chip--citizen">Citizen-submitted</span></dt><dd>Reports, comments, photos, and documents shared by members of the public. Useful context, not verification.</dd></div>
          <div><dt><span className="trust-chip trust-chip--review">Review signal</span></dt><dd>An automatic prompt that something may need a closer look. It is never a finding or an accusation.</dd></div>
        </dl>
      </section>
      <section className="guide-section guide-section--link">
        <Icon name="shield" size={22}/>
        <div><h2>Keeping the platform safe</h2><p>How content is reviewed, what may be limited or removed, and how to report something harmful.</p><Link href="/community-safety">Read Community safety <Icon name="arrow" size={13}/></Link></div>
      </section>
    </div>
  </>;
}

export function CommunitySafetyPage() {
  const states = [
    { label: "Visible", tone: "neutral", body: "Shown to everyone. Most content stays visible and has not needed review." },
    { label: "Not yet reviewed", tone: "neutral", body: "Evidence that is public but has not been looked at by a reviewer yet." },
    { label: "Under review", tone: "review", body: "Someone has raised a concern and a reviewer is looking at it. It stays visible meanwhile." },
    { label: "Limited while reviewed", tone: "limited", body: "Temporarily hidden from public view while a reviewer decides." },
    { label: "Removed for safety or privacy", tone: "removed", body: "Taken down because it was unsafe, unlawful, or exposed someone's personal information." },
    { label: "Unavailable", tone: "removed", body: "The item no longer exists or cannot be shown." },
  ];
  return <>
    <PageIntro eyebrow="COMMUNITY SAFETY" title="Community safety" body="CivicAct is for public information about public projects. Review protects people and privacy; it is not a judgement on whether a citizen's account is true."/>
    <div className="content-wrap page-space guide-page">
      <section className="guide-section">
        <h2>Before you share</h2>
        <ul className="guide-list">
          <li>Keep it about the project: what was built, delayed, or missing.</li>
          <li>Don&rsquo;t include faces, phone numbers, ID numbers, or home addresses of private individuals.</li>
          <li>Location and camera details are removed from photos automatically, but check the picture itself.</li>
          <li>No harassment, threats, hate, or spam.</li>
          <li>Contact details on a report are optional and never shown publicly.</li>
        </ul>
      </section>
      <section className="guide-section">
        <h2>How to report something harmful</h2>
        <p>Use <strong>Report comment</strong> under any comment and choose a reason. You&rsquo;ll see a confirmation once it has been sent. Reviewers check reports and may limit or remove the content.</p>
        <p className="form-hint">Reporting a specific photo or document is not available yet. If evidence shows personal information, report a related comment on the same project and describe the problem.</p>
      </section>
      <section className="guide-section" id="content-states">
        <h2>What content labels mean</h2>
        <p>We use neutral labels. Reviewer notes and the reasons behind individual decisions are not published.</p>
        <dl className="guide-terms">{states.map((state) => <div key={state.label}><dt><span className={`state-chip state-chip--${state.tone}`}>{state.label}</span></dt><dd>{state.body}</dd></div>)}</dl>
      </section>
      <section className="guide-section">
        <h2>Who reviews content</h2>
        <p>Moderation is carried out by authorised staff through a separate, permission-protected tool. There is no public sign-in, and moderation actions are recorded so they can be audited.</p>
      </section>
    </div>
  </>;
}
