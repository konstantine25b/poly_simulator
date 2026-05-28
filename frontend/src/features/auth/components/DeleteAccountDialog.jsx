import { useEffect, useState } from "react";

export function DeleteAccountDialog({ open, email, onConfirm, onClose }) {
  const [password, setPassword] = useState("");
  const [confirmText, setConfirmText] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (open) {
      setPassword("");
      setConfirmText("");
      setBusy(false);
      setErr(null);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape" && !busy) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, busy, onClose]);

  if (!open) return null;

  const canSubmit =
    !busy && password.length > 0 && confirmText.trim().toUpperCase() === "DELETE";

  const handleConfirm = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    setBusy(true);
    setErr(null);
    try {
      await onConfirm(password);
    } catch (ex) {
      setErr(ex.message || String(ex));
      setBusy(false);
    }
  };

  return (
    <div className="prof-modal-backdrop" onClick={busy ? undefined : onClose}>
      <div
        className="prof-modal"
        role="alertdialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="prof-modal-title">Delete your account?</h2>
        <p className="prof-modal-sub">
          Your account <strong>{email || ""}</strong> will be deactivated. You will be
          signed out immediately and unable to log in. An administrator can restore your
          account later.
        </p>

        <form className="set-form" onSubmit={handleConfirm}>
          <div className="auth-field">
            <label className="auth-label" htmlFor="del-pw">
              Confirm with your password
            </label>
            <input
              id="del-pw"
              className="auth-input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoFocus
            />
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="del-confirm">
              Type DELETE to confirm
            </label>
            <input
              id="del-confirm"
              className="auth-input"
              type="text"
              spellCheck={false}
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
            />
          </div>

          {err ? <p className="auth-error">{err}</p> : null}

          <div className="prof-modal-actions">
            <button
              type="button"
              className="auth-btn auth-btn-ghost"
              onClick={onClose}
              disabled={busy}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="auth-btn auth-btn-danger"
              disabled={!canSubmit}
            >
              {busy ? "Deleting…" : "Delete account"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
