import Logo from "@/components/Logo";

const CONTACT_EMAIL = "hello@assambl.com";
const CALENDAR_URL =
  "https://calendar.google.com/calendar/appointments/schedules/AcZssZ3zYBWkMNwe1_YYQV_wDJkXSyhege37wd821enNfmD2E9_rQF4hTp8NhG1SHVnV4K9jztY4OGYs?gv=true";

export default function Home() {
  return (
    <main className="flex min-h-dvh flex-col px-6 py-6 sm:px-10 sm:py-8">
      <header className="font-mono text-xs uppercase tracking-[0.18em] text-rebar">
        assambl
      </header>

      <section className="flex flex-1 flex-col items-center justify-center gap-6 sm:gap-8">
        <Logo />
        <p className="font-mono text-sm text-rebar sm:text-base">
          Vos diseñás. Assambl resuelve.
        </p>
      </section>

      <footer className="flex flex-col gap-3 font-mono text-xs text-rebar sm:flex-row sm:items-center sm:justify-between sm:text-sm">
        <span>
          <span className="text-signal">{"//"}</span> llega en 2027
        </span>
        <div className="flex flex-col text-fg">
          <span className="text-signal">try:</span>
          <a
            href={`mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent("assambl(lista de espera)")}`}
            className="pl-[4ch] underline decoration-rebar/40 underline-offset-4 hover:decoration-fg"
          >
            {CONTACT_EMAIL}
          </a>
          <span className="text-signal">else:</span>
          <a
            href={CALENDAR_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="pl-[4ch] underline decoration-rebar/40 underline-offset-4 hover:decoration-fg"
          >
            reunión 15 min
          </a>
        </div>
      </footer>
    </main>
  );
}
