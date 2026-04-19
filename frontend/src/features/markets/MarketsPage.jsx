import "./markets.css";
import { MarketCard } from "./components/MarketCard.jsx";
import { MarketsHero } from "./components/MarketsHero.jsx";
import { MarketsPager } from "./components/MarketsPager.jsx";
import { MarketsToolbar } from "./components/MarketsToolbar.jsx";
import { field } from "./domain/rowField.js";
import { useMarketsCatalog } from "./hooks/useMarketsCatalog.js";

export function MarketsPage() {
  const {
    filter,
    setFilter,
    sort,
    setSort,
    qInput,
    setQInput,
    pageSize,
    setPageSize,
    page,
    setPage,
    loading,
    err,
    items,
    total,
    totalPages,
    pageInfo,
  } = useMarketsCatalog();

  return (
    <div className="mkt-app">
      <MarketsHero />
      <MarketsToolbar
        qInput={qInput}
        onQInput={setQInput}
        filter={filter}
        onFilter={setFilter}
        sort={sort}
        onSort={setSort}
        pageSize={pageSize}
        onPageSize={setPageSize}
      />
      <main className="mkt-main">
        {loading ? <div className="mkt-state">Loading markets…</div> : null}
        {err ? <div className="mkt-state mkt-err">{err}</div> : null}
        {!loading && !err && items.length === 0 ? <div className="mkt-state">No markets match.</div> : null}
        <div className="mkt-list">
          {items.map((m) => (
            <MarketCard key={field(m, "id") || field(m, "slug")} market={m} />
          ))}
        </div>
      </main>
      <MarketsPager
        total={total}
        pageInfo={pageInfo}
        page={page}
        totalPages={totalPages}
        pageSize={pageSize}
        onPrev={() => setPage((p) => p - 1)}
        onNext={() => setPage((p) => p + 1)}
      />
    </div>
  );
}
