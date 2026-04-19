import { Link } from "react-router-dom";
import polymarketMark from "../../../../assets/polymarket.jpg";
import { outcomePairs } from "../domain/outcomes.js";
import { shouldShowLiveBadge } from "../domain/liveBadge.js";
import { field } from "../domain/rowField.js";
import { readVolumeNum } from "../domain/volumeNum.js";
import { formatDate, formatOutcomeOdds, formatUsdCompact } from "../format/format.js";

const OUTCOME_CAP = 6;

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
  const live = shouldShowLiveBadge(market);
  const pairs = outcomePairs(market);
  const shown = pairs.slice(0, OUTCOME_CAP);
  const rest = pairs.length - shown.length;
  const refRaw = slug || id || "";
  const detailEnc = refRaw ? encodeURIComponent(refRaw) : "";

  const inner = (
    <article className="mkt-card">
      <div className="mkt-card-head">
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
        <div className="mkt-card-head-text">
          <div className="mkt-card-title-row">
            <span className="mkt-title" title={question}>
              {question}
            </span>
            {live ? <span className="mkt-pill mkt-live">Live</span> : null}
          </div>
          {slug ? (
            <div className="mkt-slug" title={slug}>
              {slug}
            </div>
          ) : null}
        </div>
      </div>
      {startStr || endStr ? (
        <div className="mkt-dates">
          {startStr ? <span>{startStr}</span> : null}
          {startStr && endStr ? <span className="mkt-dates-sep">→</span> : null}
          {endStr ? <span>{endStr}</span> : null}
        </div>
      ) : null}
      {volLabel ? <div className="mkt-vol">Vol {volLabel}</div> : null}
      {shown.length ? (
        <ul className="mkt-odds">
          {shown.map((o, i) => {
            const odds = formatOutcomeOdds(o.price);
            return (
              <li key={`${id || slug}-${i}`} className="mkt-odds-row">
                <span className="mkt-odds-lbl">{o.label}</span>
                {odds ? <span className="mkt-odds-val">{odds}</span> : null}
              </li>
            );
          })}
        </ul>
      ) : null}
      {rest > 0 ? <div className="mkt-odds-more">+{rest} more</div> : null}
    </article>
  );

  return detailEnc ? (
    <Link className="mkt-card-link" to={`/m/${detailEnc}`}>
      {inner}
    </Link>
  ) : (
    inner
  );
}
