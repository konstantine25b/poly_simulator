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

export function MarketsToolbar({ qInput, onQInput, filter, onFilter, sort, onSort, pageSize, onPageSize }) {
  return (
    <div className="mkt-toolbar">
      <input
        className="mkt-search"
        type="search"
        placeholder="Search markets…"
        value={qInput}
        onChange={(ev) => onQInput(ev.target.value)}
        autoComplete="off"
      />
      <div className="mkt-toolbar-row mkt-toolbar-sort">
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
      </div>
      <div className="mkt-toolbar-row">
        <div className="mkt-filters" role="tablist">
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
        <label className="mkt-pagesize">
          <span className="mkt-pagesize-lbl">Per page</span>
          <select value={pageSize} onChange={(ev) => onPageSize(Number(ev.target.value))}>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </label>
      </div>
    </div>
  );
}
