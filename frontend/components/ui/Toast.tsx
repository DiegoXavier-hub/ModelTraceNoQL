"use client";

import { Activity, AlertTriangle, CheckCircle2 } from "lucide-react";

export type ToastTone = "success" | "error" | "info";

interface ToastProps {
  tone: ToastTone;
  message: string;
  inline?: boolean;
  onClose: () => void;
}

export function Toast({ tone, message, inline = false, onClose }: ToastProps) {
  const Icon = tone === "success" ? CheckCircle2 : tone === "error" ? AlertTriangle : Activity;
  return (
    <div className={`toast ${tone} ${inline ? "inline" : ""}`} role="status" aria-live="polite">
      <Icon size={18} />
      <span>{message}</span>
      <button type="button" className="toast-close" aria-label="Fechar notificação" onClick={onClose}>
        ✕
      </button>
    </div>
  );
}
