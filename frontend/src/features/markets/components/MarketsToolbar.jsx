import { usePhoneLayout } from "../../../hooks/usePhoneLayout.js";

const SORT_OPTIONS = [
  ["created_desc", "Newest (created)"],
  ["created_asc", "Oldest (created)"],
  ["volume_desc", "Volume (high → low)"],
  ["volume_asc", "Volume (low → high)"],
  ["end_desc", "End date (latest first)"],
  ["end_asc", "End date (earliest first)"],
  ["start_desc", "Start date (newest first)"],
  ["start_asc", "Start date (oldest first)"],
];

export function MarketsToolbar({
  qInput,
  onQInput,
  gammaInput,
  onGammaInput,
  filter,
  onFilter,
  sort,
  onSort,
  acceptingOrdersOnly,
  onAcceptingOrdersOnly,
  minVolumeInput,
  onMinVolumeInput,
  startDateFrom,
  onStartDateFrom,
  startDateTo,
  onStartDateTo,
  endDateFrom,
  onEndDateFrom,
  endDateTo,
  onEndDateTo,
  pageSize,
  onPageSize,
}) {
  const isPhone = usePhoneLayout();
  return (
    <div className="mkt-toolbar">
      <div className="mkt-toolbar-section">
        <div className="mkt-toolbar-section-head">
          <span className="mkt-toolbar-section-title">Catalog</span>
          <span className="mkt-toolbar-section-hint">Search your synced database</span>
        </div>
        <label className="mkt-field-label" htmlFor="mkt-catalog-q">
          Question or slug
        </label>
        <input
          id="mkt-catalog-q"
          className="mkt-input mkt-input-search"
          type="search"
          placeholder="Type to filter by question or slug…"
          value={qInput}
          onChange={(ev) => onQInput(ev.target.value)}
          autoComplete="off"
        />
      </div>

      <div className="mkt-toolbar-section">
        <div className="mkt-toolbar-section-head">
          <span className="mkt-toolbar-section-title">Polymarket lookup</span>
          <span className="mkt-toolbar-section-hint">Live Gamma API by id or slug</span>
        </div>
        <label className="mkt-field-label" htmlFor="mkt-gamma-q">
          Market id or slug
        </label>
        <input
          id="mkt-gamma-q"
          className="mkt-input mkt-input-search"
          type="search"
          placeholder="Digits or slug…"
          value={gammaInput}
          onChange={(ev) => onGammaInput(ev.target.value)}
          autoComplete="off"
        />
      </div>

      <div className="mkt-toolbar-row mkt-toolbar-controls">
        <label className="mkt-sort">
          <span className="mkt-sort-lbl">Sort</span>
          <select className="mkt-sort-select" value={sort} onChange={(ev) => onSort(ev.target.value)}>
            {SORT_OPTIONS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        {isPhone ? null : (
          <label className="mkt-pagesize">
            <span className="mkt-pagesize-lbl">Per page</span>
            <select value={pageSize} onChange={(ev) => onPageSize(Number(ev.target.value))}>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>
        )}
      </div>

      <div className="mkt-filter-panel" role="region" aria-label="Catalog filters">
        <div className="mkt-filter-panel-head">
          <span className="mkt-filter-panel-title">Filters</span>
          <span className="mkt-filter-panel-sub">Status, volume, and dates</span>
        </div>

        <div className="mkt-filter-panel-body">
          <div className="mkt-filter-row mkt-filter-row-status">
            <span className="mkt-filter-inline-lbl">Status</span>
            <div className="mkt-filters" role="tablist" aria-label="Market status">
              {[
                ["all", "All"],
                ["active", "Active"],
                ["closed", "Closed"],
              ].map(([id, label]) => (
                <button
                  key={id}
                  type="button"
                  role="tab"
                  aria-selected={filter === id}
                  className={`mkt-filter ${filter === id ? "on" : ""}`}
                  onClick={() => onFilter(id)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="mkt-filter-row mkt-filter-row-extras">
            <label className="mkt-filter-check">
              <input
                type="checkbox"
                checked={acceptingOrdersOnly}
                onChange={(ev) => onAcceptingOrdersOnly(ev.target.checked)}
              />
              <span>Accepting orders</span>
            </label>
            <label className="mkt-filter-minvol">
              <span className="mkt-filter-minvol-lbl">Min volume (USD)</span>
              <input
                className="mkt-input mkt-input-num"
                type="number"
                min="0"
                step="any"
                inputMode="decimal"
                placeholder="Any"
                value={minVolumeInput}
                onChange={(ev) => onMinVolumeInput(ev.target.value)}
                autoComplete="off"
              />
            </label>
          </div>

          <div className="mkt-date-ranges">
            <fieldset className="mkt-date-range">
              <legend className="mkt-date-range-legend">Start date</legend>
              <div className="mkt-date-pair">
                <label className="mkt-date-field">
                  <span className="mkt-date-lbl">From</span>
                  <input
                    className="mkt-input mkt-input-date"
                    type="date"
                    value={startDateFrom}
                    onChange={(ev) => onStartDateFrom(ev.target.value)}
                  />
                </label>
                <label className="mkt-date-field">
                  <span className="mkt-date-lbl">To</span>
                  <input
                    className="mkt-input mkt-input-date"
                    type="date"
                    value={startDateTo}
                    onChange={(ev) => onStartDateTo(ev.target.value)}
                  />
                </label>
              </div>
            </fieldset>
            <fieldset className="mkt-date-range">
              <legend className="mkt-date-range-legend">End date</legend>
              <div className="mkt-date-pair">
                <label className="mkt-date-field">
                  <span className="mkt-date-lbl">From</span>
                  <input
                    className="mkt-input mkt-input-date"
                    type="date"
                    value={endDateFrom}
                    onChange={(ev) => onEndDateFrom(ev.target.value)}
                  />
                </label>
                <label className="mkt-date-field">
                  <span className="mkt-date-lbl">To</span>
                  <input
                    className="mkt-input mkt-input-date"
                    type="date"
                    value={endDateTo}
                    onChange={(ev) => onEndDateTo(ev.target.value)}
                  />
                </label>
              </div>
            </fieldset>
          </div>
        </div>
      </div>
    </div>
  );
}
