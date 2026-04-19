import polymarketMark from "../../../../assets/polymarket.jpg";

export function MarketsHero() {
  return (
    <header className="mkt-hero">
      <div className="mkt-hero-brand">
        <img className="mkt-hero-logo" src={polymarketMark} alt="" width={40} height={40} />
        <div>
          <h1 className="mkt-hero-title">Trade Polymarkets</h1>
          <p className="mkt-hero-sub">
            Browse markets from your catalog with stored pricing. Practice trades use your paper balance on the
            API.
          </p>
        </div>
      </div>
    </header>
  );
}
