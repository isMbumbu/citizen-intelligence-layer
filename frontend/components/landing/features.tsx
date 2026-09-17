const domains = [
  {
    title: "Finance",
    body: "Budgets, allocations, commitments, contracts, and expenditure treated as distinct concepts — every value tied to its currency, period, meaning, and source.",
  },
  {
    title: "Projects",
    body: "Every project connects location, budgets, expenditure, contracts, contractors, funding sources, timelines, progress, and source documents.",
  },
  {
    title: "Geography",
    body: "Navigate public works from Country to County to Ward to Project, with spatial boundaries where coordinates are known.",
  },
  {
    title: "Sources and evidence",
    body: "A traceable chain from source document to extracted record to claim to displayed fact — with retrieval time and document hashes preserved.",
  },
  {
    title: "Verification",
    body: "Verification independent of AI, using explicit states: UNVERIFIED, PARTIALLY_VERIFIED, VERIFIED, STALE, and DISPUTED.",
  },
  {
    title: "Civic action",
    body: "Citizen reports retain issue, project, location, evidence, submission time, institution, status, and response.",
  },
];

export default function Features() {
  return (
    <section id="domains" className="border-b border-black/10 dark:border-white/10">
      <div className="mx-auto w-full max-w-6xl px-6 py-20">
        <p className="text-sm font-medium uppercase tracking-widest text-sky-600 dark:text-sky-400">
          What it covers
        </p>
        <h2 className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight">
          Six domains, one evidence trail.
        </h2>
        <p className="mt-4 max-w-2xl text-lg leading-8 opacity-70">
          Each domain keeps provenance attached to the facts it surfaces, so a
          displayed figure can always be traced to what was published.
        </p>
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {domains.map((item) => (
            <div
              key={item.title}
              className="flex flex-col gap-3 rounded-lg border border-black/10 p-6 dark:border-white/15"
            >
              <h3 className="text-lg font-semibold tracking-tight">
                {item.title}
              </h3>
              <p className="text-sm leading-7 opacity-70">{item.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}