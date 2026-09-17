import Link from "next/link";

const navLinks = [
  { href: "#mission", label: "Mission" },
  { href: "#approach", label: "Approach" },
  { href: "#domains", label: "Domains" },
  { href: "#principles", label: "Principles" },
];

export default function Header() {
  return (
    <header className="sticky top-0 z-10 border-b border-black/10 bg-background/80 backdrop-blur dark:border-white/10">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm font-semibold tracking-tight"
        >
          <span className="h-2 w-2 rounded-full bg-sky-500" />
          Citizen Intelligence Layer
        </Link>
        <nav className="hidden items-center gap-8 text-sm sm:flex">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="opacity-70 transition-opacity hover:opacity-100"
            >
              {link.label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}