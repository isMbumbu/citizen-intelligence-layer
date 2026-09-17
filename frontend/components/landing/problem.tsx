const problems = [
  {
    title: "Fragmented",
    body: "Budgets, tenders, contracts, and expenditure live in different systems and formats — PDFs, portals, and spreadsheets that rarely connect.",
  },
  {
    title: "Opaque",
    body: "Figures appear without context. A monetary value means little when its currency, period, meaning, and source are missing.",
  },
  {
    title: "Hard to verify",
    body: "Claims circulate without links to the underlying record, so people cannot tell what is official, derived, or simply reported.",
  },
];

export default function Problem() {
  return (
    <section className="border-b border-black/10 dark:border-white/10">
      <div className="mx-auto w-full max-w-6xl px-6 py-20">
        <p className="text-sm font-medium uppercase tracking-widest text-sky-600 dark:text-sky-400">
          The problem
        </p>
        <h2 className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight">
          Public information is scattered and hard to trust.
        </h2>
        <p className="mt-4 max-w-2xl text-lg leading-8 opacity-70">
          Decisions that shape communities are made from records people rarely
          see, in formats people decode with difficulty.
        </p>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {problems.map((item) => (
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