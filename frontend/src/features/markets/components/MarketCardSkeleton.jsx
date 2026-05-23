export function MarketCardSkeleton() {
  return (
    <article className="mkt-card mkt-card-skeleton" aria-hidden="true">
      <div className="mkt-card-head">
        <div className="sk sk-avatar" />
        <div className="mkt-card-head-text">
          <div className="sk sk-line sk-line-title" />
          <div className="sk sk-line sk-line-title sk-line-short" />
        </div>
      </div>
      <div className="sk-meta-row">
        <div className="sk sk-pill" />
        <div className="sk sk-pill" />
        <div className="sk sk-pill sk-pill-wide" />
      </div>
      <div className="sk-outcomes">
        <div className="sk sk-outcome" />
        <div className="sk sk-outcome" />
        <div className="sk sk-outcome" />
        <div className="sk sk-outcome" />
      </div>
    </article>
  );
}

export function MarketsSkeletonList({ count = 9 }) {
  return (
    <div className="mkt-list" aria-busy="true" aria-live="polite">
      {Array.from({ length: count }).map((_, i) => (
        <MarketCardSkeleton key={i} />
      ))}
    </div>
  );
}
