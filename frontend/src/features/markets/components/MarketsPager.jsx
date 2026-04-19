export function MarketsPager({ total, pageInfo, page, totalPages, pageSize, onPrev, onNext }) {
  return (
    <footer className="mkt-pager">
      <span className="mkt-pager-info">
        {total ? (
          <>
            {pageInfo.from}–{pageInfo.to} of {total}
          </>
        ) : (
          "0 markets"
        )}
      </span>
      <div className="mkt-pager-btns">
        <button type="button" className="mkt-navbtn" disabled={page <= 0} onClick={onPrev}>
          Previous
        </button>
        <span className="mkt-pager-page">
          Page {page + 1} / {totalPages}
        </span>
        <button type="button" className="mkt-navbtn" disabled={(page + 1) * pageSize >= total} onClick={onNext}>
          Next
        </button>
      </div>
    </footer>
  );
}
