import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, LogOut, RefreshCw } from "lucide-react";

import { Brand, ForbiddenPage, SignInPage, UnreachablePage } from "./components/Gate";
import { request, useSession } from "./http";
import { messageOf } from "./lib";

type Settings = { refresh_seconds: number };

type Stack = {
  key: string;
  name: string;
  description: string;
  url: string;
  host: string;
  state: "running" | "degraded" | "offline";
  status: string;
  can_open: boolean;
  also: { name: string; url: string; host: string } | null;
};

function Card({ stack }: { stack: Stack }) {
  const body = (
    <>
      <div className="lu-top">
        <img className="lu-icon" src={`/apps/${stack.key}.png`} alt="" />
        <div className="lu-heading">
          <span className="lu-name">{stack.name}</span>
          <span className="lu-status">{stack.status}</span>
        </div>
      </div>
      <p className="lu-desc">{stack.description}</p>
      <div className="lu-link">
        <span>{stack.host}</span>
        {stack.can_open && <ArrowUpRight size={16} />}
      </div>
    </>
  );
  const classes = `lu-card lu-${stack.state}`;
  if (!stack.can_open) {
    return (
      <div className={classes} aria-disabled="true">
        {body}
      </div>
    );
  }
  const card = (
    <a className={classes} href={stack.url} target="_blank" rel="noopener" aria-label={`Open ${stack.name}`}>
      {body}
    </a>
  );
  if (!stack.also) return card;
  // A link inside a link is not valid, so the second one sits beside the card, over its foot.
  return (
    <div className="lu-card-pair">
      {card}
      <a className="lu-also" href={stack.also.url} target="_blank" rel="noopener" aria-label={`Open ${stack.also.name}`}>
        <span>
          {stack.also.name} · {stack.also.host}
        </span>
        <ArrowUpRight size={16} />
      </a>
    </div>
  );
}

function Workspace({ logoutUrl, settings }: { logoutUrl: string; settings: Settings }) {
  const stacks = useQuery({
    queryKey: ["stacks"],
    queryFn: () => request<{ apps: Stack[] }>("/app/status"),
    refetchInterval: settings.refresh_seconds * 1000,
    staleTime: 0,
  });
  const apps = stacks.data?.apps;
  const running = apps?.filter((stack) => stack.can_open).length ?? 0;

  return (
    <main className="lv-page">
      <div className="lv-header-row">
        <Brand />
        <div className="lv-header-actions">
          <button
            className="lv-button lv-button-primary lv-header-main"
            type="button"
            disabled={stacks.isFetching}
            onClick={() => stacks.refetch()}
          >
            <RefreshCw size={17} />
            Check again
          </button>
          <a className="lv-button lv-sign-out" href={logoutUrl}>
            <LogOut size={16} />
            Sign out
          </a>
        </div>
      </div>

      {stacks.error && <p className="lv-alert lv-alert-error">{messageOf(stacks.error, "The stacks could not be checked.")}</p>}
      {apps && (
        <>
          <div className="lu-summary">
            <span>
              <strong>
                {running} of {apps.length}
              </strong>{" "}
              Luna stacks running
            </span>
            <span>Checked again every {settings.refresh_seconds} seconds · open an app to go to it</span>
          </div>
          <div className="lu-grid">
            {apps.map((stack) => (
              <Card stack={stack} key={stack.key} />
            ))}
          </div>
        </>
      )}
    </main>
  );
}

export function App() {
  const { data: session, error, refetch } = useSession<Settings>();

  if (error) return <UnreachablePage onRetry={() => refetch()} />;
  if (!session) return null;
  if (session.status === "signed_out") return <SignInPage url={session.login_url} />;
  if (session.status === "forbidden") return <ForbiddenPage email={session.email} logoutUrl={session.logout_url} />;
  return <Workspace logoutUrl={session.logout_url} settings={session.settings} />;
}
