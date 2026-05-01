import { PositionRow } from "./PositionRow.jsx";

export function PositionList({ positions }) {
  if (!positions || positions.length === 0) {
    return (
      <div className="pd-empty">
        No open positions in this portfolio yet. Place a bet from a market page to get started.
      </div>
    );
  }
  return (
    <div className="pd-pos-list">
      {positions.map((p) => (
        <PositionRow key={p.id} position={p} />
      ))}
    </div>
  );
}
