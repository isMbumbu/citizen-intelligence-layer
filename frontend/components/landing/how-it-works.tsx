const steps = [
  {
    step: "01",
    title: "Collect and structure",
    body: "Source documents are retrieved, hashed, and parsed into extracted records and claims — preserving original values and their versions.",
  },
  {
    step: "02",
    title: "Verify and connect",
    body: "Verification works independently of AI. Records move through explicit states — from UNVERIFIED to VERIFIED, or STALE and DISPUTED — and link to projects, places, and contracts.",
  },
  {
    step: "03",
    title: "Understand and act",
    body: "Intelligence answers are grounded in sourced records. Citizens can follow what happens and file reports with institutions.",
  },
];

export default function HowItWorks() {
  return (
    <section id="approach" className="border-b border-black/10 dark:border-white/10">
      <div className="mx-auto w-full max-w-6xl px-6 py-20">
        <p className="text-sm font-medium uppercase tracking-widest text-sky-600 dark:text-sky-400">
          The approach
        </p>
        <h2 className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight">
          From scattered records to usable knowledge.
        </h2>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {steps.map((item) => (
            <div key={item.step} className="flex flex-col gap-3">
              <p className="text-sm font-medium text-sky-600 dark:text-sky-400">
                {item.step}
              </p>
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