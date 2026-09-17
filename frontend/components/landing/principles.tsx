const principles = [
  {
    title: "Every claim has a source",
    body: "Material claims trace back to source records, documents, and versions. Official records, derived data, human verification, citizen submissions, and AI explanations are kept strictly distinct.",
  },
  {
    title: "Honest about uncertainty",
    body: "Raw values, normalization decisions, and validation outcomes are preserved. Gaps, conflicts, and uncertainty are surfaced rather than turned into false certainty.",
  },
  {
    title: "AI explains, never asserts",
    body: "AI compares, explains, and flags discrepancies only when grounded in sourced records. AI output is explanatory — never authoritative evidence or verification.",
  },
];

export default function Principles() {
  return (
    <section id="principles" className="border-b border-black/10 dark:border-white/10">
      <div className="mx-auto w-full max-w-6xl px-6 py-20">
        <p className="text-sm font-medium uppercase tracking-widest text-sky-600 dark:text-sky-400">
          Principles
        </p>
        <h2 className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight">
          Designed so information can be trusted.
        </h2>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {principles.map((item) => (
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