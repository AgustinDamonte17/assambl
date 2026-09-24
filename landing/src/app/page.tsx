import Logo from "@/components/Logo";

const CONTACT_EMAIL = "agusda95@gmail.com";

export default function Home() {
  return (
    <main className="flex min-h-dvh flex-col px-6 py-6 sm:px-10 sm:py-8">
      <header className="font-mono text-xs uppercase tracking-[0.18em] text-rebar">
        assambl
      </header>

      <section className="flex flex-1 flex-col items-center justify-center gap-6 sm:gap-8">
        <Logo />
        <p className="font-mono text-sm text-rebar sm:text-base">
          You design. Assambl solves.
        </p>
      </section>

      <footer className="flex flex-col gap-3 font-mono text-xs text-rebar sm:flex-row sm:items-center sm:justify-between sm:text-sm">
        <span>
          <span className="text-signal">{"//"}</span> coming 2027
        </span>
        <a
          href={`mailto:${CONTACT_EMAIL}?subject=assambl(waitlist)`}
          className="group inline-flex items-center gap-2 transition-colors hover:text-fg"
        >
          <span className="text-signal">$</span>
          <span>notify me</span>
          <span className="text-rebar transition-colors group-hover:text-fg">
            →
          </span>
          <span className="underline decoration-rebar/40 underline-offset-4 group-hover:decoration-fg">
            {CONTACT_EMAIL}
          </span>
        </a>
      </footer>
    </main>
  );
}
