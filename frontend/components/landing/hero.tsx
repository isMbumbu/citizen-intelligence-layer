export default function Hero({ apiStatus }: { apiStatus: string }) {
  return (
    <section id="mission" className="border-b border-black/10 dark:border-white/10">
      <div className="mx-auto flex w-full max-w-6xl flex-col items-start gap-8 px-6 py-24 md:py-32">
        <p className="text-sm font-medium uppercase tracking-widest text-sky-600 dark:text-sky-400">
          Citizen-first intelligence
        </p>
        <h1 className="max-w-3xl text-4xl font-semibold leading-tight tracking-tight md:text-6xl">
          Public money and projects, made intelligible, verifiable, and
          actionable.
        </h1>
        <p className="max-w-2xl text-lg leading-8 opacity-70">
          The Citizen Intelligence Layer turns fragmented public budgets,
          projects, contracts, expenditure, timelines, and government records
          into information that people can understand, verify, and act on.
        </p>
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <a
            href="#domains"
            className="rounded-full bg-foreground px-5 py-2.5 text-background transition-opacity hover:opacity-90"
          >
            Explore the platform
          </a>
          <span className="flex items-center gap-2 opacity-60">
            <span
              className={`h-2 w-2 rounded-full ${
                apiStatus === "ok" ? "bg-green-500" : "bg-red-500"
              }`}
            />
            API {apiStatus}
          </span>
        </div>
      </div>
    </section>
  );
}