const AUTHOR_NAME = "Nicholas Mckay";
const LINKEDIN_URL =
  process.env.NEXT_PUBLIC_AUTHOR_LINKEDIN ?? "https://www.linkedin.com/in/nicholasmckay29/";

export function SiteCredits() {
  return (
    <footer className="fixed bottom-3 right-4 z-50 pointer-events-none">
      <p className="font-mono text-[10px] text-muted/80 tracking-wide pointer-events-auto">
        built by {AUTHOR_NAME}
        <span className="text-border mx-1.5">·</span>
        <a
          href={LINKEDIN_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="text-muted hover:text-accent transition-colors"
        >
          LinkedIn
        </a>
      </p>
    </footer>
  );
}
