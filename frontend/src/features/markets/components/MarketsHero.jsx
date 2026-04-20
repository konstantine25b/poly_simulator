import polymarketMark from "../../../../assets/polymarket.jpg";

export function MarketsHero() {
  return (
    <header className="mkt-hero">
      <div className="mkt-hero-card">
        <div className="mkt-hero-brand">
          <img className="mkt-hero-logo" src={polymarketMark} alt="" width={44} height={44} />
          <div className="mkt-hero-copy">
            <h1 className="mkt-hero-title">Trade Polymarkets</h1>
            <p className="mkt-hero-sub">
              Browse markets from catalog with stored pricing. Practice trades using your paper balance through the API.
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
