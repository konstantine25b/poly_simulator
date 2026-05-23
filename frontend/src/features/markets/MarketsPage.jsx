import "./markets.css";
import { MarketCard } from "./components/MarketCard.jsx";
import { MarketsSkeletonList } from "./components/MarketCardSkeleton.jsx";
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
    acceptingOrdersOnly,
    setAcceptingOrdersOnly,
    minVolumeInput,
    setMinVolumeInput,
    startDateFrom,
    setStartDateFrom,
    startDateTo,
    setStartDateTo,
    endDateFrom,
    setEndDateFrom,
    endDateTo,
    setEndDateTo,
    qInput,
    setQInput,
    gammaInput,
    setGammaInput,
    gammaMarket,
    gammaLoading,
    gammaErr,
    pageSize,
    setPageSize,
    page,
    setPage,
    loading,
    showSkeletons,
    err,
    items,
    total,
    totalPages,
    pageInfo,
  } = useMarketsCatalog();

  const skeletonCount = Math.min(Math.max(pageSize, 3), 12);

  return (
    <div className="mkt-app">
      <MarketsHero />
      <MarketsToolbar
        qInput={qInput}
        onQInput={setQInput}
        gammaInput={gammaInput}
        onGammaInput={setGammaInput}
        filter={filter}
        onFilter={setFilter}
        sort={sort}
        onSort={setSort}
        acceptingOrdersOnly={acceptingOrdersOnly}
        onAcceptingOrdersOnly={setAcceptingOrdersOnly}
        minVolumeInput={minVolumeInput}
        onMinVolumeInput={setMinVolumeInput}
        startDateFrom={startDateFrom}
        onStartDateFrom={setStartDateFrom}
        startDateTo={startDateTo}
        onStartDateTo={setStartDateTo}
        endDateFrom={endDateFrom}
        onEndDateFrom={setEndDateFrom}
        endDateTo={endDateTo}
        onEndDateTo={setEndDateTo}
        pageSize={pageSize}
        onPageSize={setPageSize}
      />
      <main className="mkt-main">
        {gammaInput.trim() ? (
          <section className="mkt-gamma-panel" aria-label="Polymarket lookup">
            <div className="mkt-gamma-head">Gamma lookup</div>
            {gammaLoading ? <div className="mkt-state">Loading from Polymarket…</div> : null}
            {gammaErr ? <div className="mkt-state mkt-err">{gammaErr}</div> : null}
            {!gammaLoading && !gammaErr && gammaMarket ? (
              <div className="mkt-list mkt-list-gamma">
                <MarketCard market={gammaMarket} />
              </div>
            ) : null}
          </section>
        ) : null}
        {err ? <div className="mkt-state mkt-err">{err}</div> : null}
        {showSkeletons ? (
          <MarketsSkeletonList count={skeletonCount} />
        ) : (
          <>
            {!loading && !err && items.length === 0 ? (
              <div className="mkt-state">No markets match.</div>
            ) : null}
            <div className={`mkt-list${loading ? " mkt-list-refreshing" : ""}`}>
              {items.map((m) => (
                <MarketCard key={field(m, "id") || field(m, "slug")} market={m} />
              ))}
            </div>
          </>
        )}
      </main>
      <MarketsPager
        total={total}
        pageInfo={pageInfo}
        page={page}
        totalPages={totalPages}
        onPageChange={setPage}
      />
    </div>
  );
}
