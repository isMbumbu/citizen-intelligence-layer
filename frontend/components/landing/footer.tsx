export default function Footer() {
  return (
    <footer className="border-t border-black/10 dark:border-white/10">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-6 py-12 text-sm sm:flex-row sm:items-center sm:justify-between">
        <p className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="h-2 w-2 rounded-full bg-sky-500" />
          Citizen Intelligence Layer
        </p>
        <p className="opacity-60">
          Citizen-first intelligence for public spending, projects, evidence,
          and civic action.
        </p>
      </div>
    </footer>
  );
}