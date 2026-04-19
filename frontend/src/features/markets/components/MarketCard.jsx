import polymarketMark from "../../../../assets/polymarket.jpg";
import { readVolumeNum } from "../domain/volumeNum.js";
import { outcomeCount } from "../domain/outcomes.js";
import { field } from "../domain/rowField.js";
import { formatDate, formatUsdCompact } from "../format/format.js";

export function MarketCard({ market }) {
  const id = field(market, "id");
  const question = field(market, "question") || id || "";
  const slug = field(market, "slug");
  const img = field(market, "image") || field(market, "icon");
  const start =
    field(market, "startDateIso") || field(market, "startDate") || field(market, "createdAt");
  const end = field(market, "endDateIso") || field(market, "endDate");
  const startStr = formatDate(start);
  const endStr = formatDate(end);
  const volLabel = formatUsdCompact(readVolumeNum(market));
  const active = Number(field(market, "active")) === 1;
  const closed = Number(field(market, "closed")) === 1;
  const live = active && !closed;
  const nOut = outcomeCount(market);

  return (
    <article className="mkt-card">
      <div className="mkt-card-top">
        <div className="mkt-thumb-wrap">
          <img
            className="mkt-thumb"
            src={img || polymarketMark}
            alt=""
            onError={(ev) => {
              ev.currentTarget.onerror = null;
              ev.currentTarget.src = polymarketMark;
            }}
          />
        </div>
        <div className="mkt-card-main">
          <div className="mkt-card-title-row">
            <span className="mkt-title">{question}</span>
            {live ? <span className="mkt-pill mkt-live">Live</span> : null}
          </div>
          {slug ? <div className="mkt-slug">{slug}</div> : null}
          {startStr || endStr ? (
            <div className="mkt-dates">
              {startStr ? <span>{startStr}</span> : null}
              {startStr && endStr ? <span className="mkt-dates-sep">→</span> : null}
              {endStr ? <span>{endStr}</span> : null}
            </div>
          ) : null}
        </div>
        <div className="mkt-card-side">
          {volLabel ? <div className="mkt-vol">Vol {volLabel}</div> : null}
          {nOut > 0 ? <div className="mkt-ocount">{nOut} outcomes</div> : null}
        </div>
      </div>
    </article>
  );
}
