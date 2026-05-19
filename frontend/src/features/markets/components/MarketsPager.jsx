import { useEffect, useMemo, useState } from "react";
import { buildPagerItems } from "../domain/buildPagerItems.js";

function clampPage(page, totalPages) {
  if (totalPages <= 0) return 0;
  return Math.max(0, Math.min(totalPages - 1, page));
}

export function MarketsPager({ total, pageInfo, page, totalPages, onPageChange }) {
  const items = useMemo(() => buildPagerItems(page, totalPages, 2), [page, totalPages]);
  const [jumpEditing, setJumpEditing] = useState(false);
  const [jumpDraft, setJumpDraft] = useState("");

  const go = (next) => onPageChange(clampPage(next, totalPages));

  useEffect(() => {
    if (!jumpEditing) setJumpDraft(String(page + 1));
  }, [page, jumpEditing]);

  const commitJump = () => {
    setJumpEditing(false);
    const n = Number.parseInt(jumpDraft.trim(), 10);
    if (Number.isFinite(n) && n >= 1 && n <= totalPages) go(n - 1);
    else setJumpDraft(String(page + 1));
  };

  const atStart = page <= 0;
  const atEnd = page + 1 >= totalPages || total === 0;
  const showNav = totalPages > 1;

  return (
    <footer className="mkt-pager">
      <div className="mkt-pager-top">
        <p className="mkt-pager-meta">
          {total ? (
            <>
              Showing <span className="mkt-pager-meta-strong">{pageInfo.from}–{pageInfo.to}</span> of{" "}
              <span className="mkt-pager-meta-strong">{total.toLocaleString()}</span>
            </>
          ) : (
            "No markets"
          )}
        </p>
        {showNav ? (
          <form
            className="mkt-pager-goto"
            onSubmit={(e) => {
              e.preventDefault();
              commitJump();
            }}
          >
            <span className="mkt-pager-goto-label">Page</span>
            <input
              className="mkt-pager-goto-input"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              aria-label={`Page number, 1 to ${totalPages}`}
              value={jumpEditing ? jumpDraft : String(page + 1)}
              onFocus={() => {
                setJumpEditing(true);
                setJumpDraft(String(page + 1));
              }}
              onChange={(e) => setJumpDraft(e.target.value.replace(/\D/g, ""))}
              onBlur={commitJump}
            />
            <span className="mkt-pager-goto-of">
              of <span className="mkt-pager-goto-total">{totalPages.toLocaleString()}</span>
            </span>
          </form>
        ) : null}
      </div>
      {showNav ? (
        <nav className="mkt-pager-nav" aria-label="Pagination">
          <div className="mkt-pager-track">
            <button
              type="button"
              className="mkt-pager-cell mkt-pager-cell--edge"
              disabled={atStart}
              aria-label="First page"
              onClick={() => go(0)}
            >
              «
            </button>
            <button
              type="button"
              className="mkt-pager-cell mkt-pager-cell--edge"
              disabled={atStart}
              aria-label="Previous page"
              onClick={() => go(page - 1)}
            >
              ‹
            </button>
            <div className="mkt-pager-nums">
              {items.map((item, i) =>
                item === "ellipsis" ? (
                  <span key={`e-${i}`} className="mkt-pager-cell mkt-pager-cell--gap" aria-hidden>
                    …
                  </span>
                ) : (
                  <button
                    key={item}
                    type="button"
                    className={`mkt-pager-cell mkt-pager-cell--num${item === page ? " mkt-pager-cell--on" : ""}`}
                    aria-current={item === page ? "page" : undefined}
                    aria-label={`Page ${item + 1}`}
                    onClick={() => go(item)}
                  >
                    {item + 1}
                  </button>
                ),
              )}
            </div>
            <button
              type="button"
              className="mkt-pager-cell mkt-pager-cell--edge"
              disabled={atEnd}
              aria-label="Next page"
              onClick={() => go(page + 1)}
            >
              ›
            </button>
            <button
              type="button"
              className="mkt-pager-cell mkt-pager-cell--edge"
              disabled={atEnd}
              aria-label="Last page"
              onClick={() => go(totalPages - 1)}
            >
              »
            </button>
          </div>
        </nav>
      ) : null}
    </footer>
  );
}
