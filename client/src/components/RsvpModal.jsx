import React, { useEffect, useRef, useState } from "react";
import ReactDOM from "react-dom";
import "./RsvpModal.css";

// Simple, accessible modal for selecting RSVP status (Going / Interested)
export default function RsvpModal({
  isOpen,
  onClose,
  initialStatus = null,
  onConfirm,
  loading = false,
  error = null,
}) {
  const [status, setStatus] = useState(initialStatus);
  const dialogRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setStatus(initialStatus);
      // trap focus to dialog
      const prevActive = document.activeElement;
      const dialog = dialogRef.current;
      if (dialog) dialog.focus();
      const onKey = (e) => {
        if (e.key === "Escape") onClose();
      };
      document.addEventListener("keydown", onKey);
      return () => {
        document.removeEventListener("keydown", onKey);
        if (prevActive && prevActive.focus) prevActive.focus();
      };
    }
  }, [isOpen, initialStatus, onClose]);

  if (!isOpen) return null;

  return ReactDOM.createPortal(
    <div className="rsvp-modal-backdrop" onMouseDown={onClose}>
      <div
        className="rsvp-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="rsvp-title"
        onMouseDown={(e) => e.stopPropagation()}
        tabIndex={-1}
        ref={dialogRef}
      >
        <h2 id="rsvp-title">RSVP to this event</h2>

        <div className="rsvp-options">
          <label>
            <input
              type="radio"
              name="rsvp"
              value="Going"
              checked={status === "Going"}
              onChange={() => setStatus("Going")}
            />
            <span className="rsvp-label-text">Going</span>
          </label>
          <label>
            <input
              type="radio"
              name="rsvp"
              value="Interested"
              checked={status === "Interested"}
              onChange={() => setStatus("Interested")}
            />
            <span className="rsvp-label-text">Interested</span>
          </label>
        </div>

        {error && (
          <div className="rsvp-error" role="alert">
            {error}
          </div>
        )}

        <div className="rsvp-actions">
          <button className="rsvp-cancel" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button
            className="rsvp-confirm"
            onClick={() => onConfirm(status)}
            disabled={loading || !status}
          >
            {loading ? "Saving…" : "Confirm"}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
