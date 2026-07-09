"use client";

import {
  Activity,
  AlertTriangle,
  Boxes,
  CheckCircle2,
  Database,
  Eye,
  EyeOff,
  Fingerprint,
  KeyRound,
  Lock,
  LogIn,
  MailCheck,
  ShieldCheck,
  UserPlus
} from "lucide-react";
import { useState, type FormEvent } from "react";
import type { Locale } from "@/lib/i18n";
import { LanguageToggle } from "../shell/LanguageToggle";

export interface PasswordCheck {
  id: string;
  label: string;
  passed: boolean;
}

export interface Notice {
  id: number;
  tone: "success" | "error" | "info";
  message: string;
}

type AuthMode = "signin" | "signup";

interface PasswordInputProps {
  value: string;
  onChange: (value: string) => void;
  autoComplete: "current-password" | "new-password";
  visible: boolean;
  onToggleVisible: () => void;
}

function PasswordInput({ value, onChange, autoComplete, visible, onToggleVisible }: PasswordInputProps) {
  return (
    <div style={{ position: "relative", display: "flex", alignItems: "stretch" }}>
      <input
        autoComplete={autoComplete}
        type={visible ? "text" : "password"}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required
        style={{ flex: 1, paddingRight: 40 }}
      />
      <button
        type="button"
        className="ghost icon-only"
        onClick={onToggleVisible}
        aria-label={visible ? "Ocultar senha" : "Mostrar senha"}
        title={visible ? "Ocultar senha" : "Mostrar senha"}
        aria-pressed={visible}
        style={{
          position: "absolute",
          right: 4,
          top: "50%",
          transform: "translateY(-50%)",
          width: 32,
          height: 32,
          minHeight: 32,
          border: "none",
          background: "transparent"
        }}
      >
        {visible ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </div>
  );
}

interface AuthScreenProps {
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;

  email: string;
  password: string;
  name: string;
  organizationName: string;
  jobTitle: string;
  department: string;
  company: string;
  phone: string;
  timezone: string;
  bio: string;

  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onNameChange: (value: string) => void;
  onOrganizationChange: (value: string) => void;
  onJobTitleChange: (value: string) => void;
  onDepartmentChange: (value: string) => void;
  onCompanyChange: (value: string) => void;
  onPhoneChange: (value: string) => void;
  onTimezoneChange: (value: string) => void;
  onBioChange: (value: string) => void;

  passwordChecks: ReadonlyArray<PasswordCheck>;
  passwordReadyForRegister: boolean;

  resetOpen: boolean;
  onToggleReset: () => void;
  resetEmail: string;
  resetToken: string;
  resetPassword: string;
  onResetEmailChange: (value: string) => void;
  onResetTokenChange: (value: string) => void;
  onResetPasswordChange: (value: string) => void;
  resetPasswordChecks: ReadonlyArray<PasswordCheck>;
  resetPasswordReady: boolean;

  status: string;
  notice: Notice | null;
  onCloseNotice: () => void;

  onLogin: () => void;
  onRegister: () => void;
  onRequestPasswordReset: () => void;
  onConfirmPasswordReset: () => void;
}

export function AuthScreen(props: AuthScreenProps) {
  const {
    locale,
    onLocaleChange,
    email,
    password,
    name,
    organizationName,
    jobTitle,
    department,
    company,
    phone,
    timezone,
    bio,
    onEmailChange,
    onPasswordChange,
    onNameChange,
    onOrganizationChange,
    onJobTitleChange,
    onDepartmentChange,
    onCompanyChange,
    onPhoneChange,
    onTimezoneChange,
    onBioChange,
    passwordChecks,
    passwordReadyForRegister,
    resetOpen,
    onToggleReset,
    resetEmail,
    resetToken,
    resetPassword,
    onResetEmailChange,
    onResetTokenChange,
    onResetPasswordChange,
    resetPasswordChecks,
    resetPasswordReady,
    notice,
    onCloseNotice,
    onLogin,
    onRegister,
    onRequestPasswordReset,
    onConfirmPasswordReset
  } = props;

  const [mode, setMode] = useState<AuthMode>("signin");
  const [showSigninPassword, setShowSigninPassword] = useState(false);
  const [showSignupPassword, setShowSignupPassword] = useState(false);
  const [showResetPassword, setShowResetPassword] = useState(false);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (mode === "signin") {
      onLogin();
    } else {
      onRegister();
    }
  };

  const cardSubtitle = mode === "signin" ? "Entrar no ModelTrace" : "Criar conta no ModelTrace";

  return (
    <main className="auth-shell">
      <section className="auth-product">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
          <div className="brand-mark">
            <span
              aria-hidden="true"
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                width: 32,
                height: 32,
                borderRadius: "var(--radius-sm)",
                background: "linear-gradient(135deg, var(--accent), var(--info))",
                color: "#fff",
                boxShadow: "0 6px 18px var(--accent-glow)"
              }}
            >
              <Database size={18} />
            </span>
            ModelTrace
          </div>
          <span className="badge accent" aria-label="Versão 2.0">
            <Fingerprint size={12} />
            v2.0 · Decision Ops
          </span>
        </div>

        <div style={{ display: "grid", gap: 14 }}>
          <span className="eyebrow">Decision Operations Platform</span>
          <h1>Operação e governança para modelos em produção.</h1>
          <p>
            Auditoria append-only, drift, what-if e replay em um workspace único.
            Modelagem documental NoSQL flexível por modelo, criptografia de PII e
            exportações prontas para auditoria regulatória.
          </p>
        </div>

        <div className="auth-proof-grid">
          <div>
            <span
              aria-hidden="true"
              style={{
                width: 30,
                height: 30,
                display: "inline-grid",
                placeItems: "center",
                borderRadius: "var(--radius-sm)",
                background: "var(--accent-soft)",
                color: "var(--accent-strong)",
                marginBottom: 4
              }}
            >
              <ShieldCheck size={15} />
            </span>
            <strong>Append-only</strong>
            <span>Histórico imutável de cada decisão tomada por modelo.</span>
          </div>
          <div>
            <span
              aria-hidden="true"
              style={{
                width: 30,
                height: 30,
                display: "inline-grid",
                placeItems: "center",
                borderRadius: "var(--radius-sm)",
                background: "var(--success-soft)",
                color: "var(--success-strong)",
                marginBottom: 4
              }}
            >
              <Activity size={15} />
            </span>
            <strong>Observabilidade</strong>
            <span>Drift, calibração, equidade e replay em tempo de operação.</span>
          </div>
          <div>
            <span
              aria-hidden="true"
              style={{
                width: 30,
                height: 30,
                display: "inline-grid",
                placeItems: "center",
                borderRadius: "var(--radius-sm)",
                background: "var(--info-soft)",
                color: "var(--info-strong)",
                marginBottom: 4
              }}
            >
              <Boxes size={15} />
            </span>
            <strong>Schema flexível</strong>
            <span>Documentos NoSQL adaptados por modelo, versão e contrato.</span>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: 12,
            paddingTop: 8,
            borderTop: "1px solid var(--border)"
          }}
        >
          <div>
            <strong className="num" style={{ fontSize: "var(--fs-xl)" }}>
              102k+
            </strong>
            <small className="stat-label" style={{ display: "block", marginTop: 2 }}>
              Predições reais
            </small>
          </div>
          <div>
            <strong className="num" style={{ fontSize: "var(--fs-xl)" }}>
              30+
            </strong>
            <small className="stat-label" style={{ display: "block", marginTop: 2 }}>
              Coleções NoSQL
            </small>
          </div>
          <div>
            <strong className="num" style={{ fontSize: "var(--fs-xl)" }}>
              5
            </strong>
            <small className="stat-label" style={{ display: "block", marginTop: 2 }}>
              Domínios ativos
            </small>
          </div>
        </div>
      </section>

      <section className="auth-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
          <div>
            <span className="eyebrow">Acesso ao workspace</span>
            <h2 style={{ marginTop: 4, fontSize: "var(--fs-xl)" }}>{cardSubtitle}</h2>
          </div>
          <LanguageToggle locale={locale} onChange={onLocaleChange} />
        </div>

        <div
          role="tablist"
          aria-label="Modo de acesso"
          className="auth-tablist"
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 4,
            padding: 4,
            borderRadius: "var(--radius-md)",
            background: "var(--surface-2)",
            border: "1px solid var(--border)"
          }}
        >
          <button
            type="button"
            role="tab"
            aria-selected={mode === "signin"}
            className={mode === "signin" ? "" : "ghost"}
            onClick={() => setMode("signin")}
            style={{
              justifyContent: "center",
              borderRadius: "var(--radius-sm)",
              padding: "8px 10px",
              minHeight: 34
            }}
          >
            <LogIn size={14} />
            Entrar
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "signup"}
            className={mode === "signup" ? "" : "ghost"}
            onClick={() => setMode("signup")}
            style={{
              justifyContent: "center",
              borderRadius: "var(--radius-sm)",
              padding: "8px 10px",
              minHeight: 34
            }}
          >
            <UserPlus size={14} />
            Criar conta
          </button>
        </div>

        {mode === "signin" ? (
          <form className="form" onSubmit={handleSubmit} aria-label="Formulário de login">
            <label>
              Email
              <input
                autoComplete="email"
                type="email"
                value={email}
                onChange={(event) => onEmailChange(event.target.value)}
                required
              />
            </label>
            <label>
              Senha
              <PasswordInput
                value={password}
                onChange={onPasswordChange}
                autoComplete="current-password"
                visible={showSigninPassword}
                onToggleVisible={() => setShowSigninPassword((value) => !value)}
              />
            </label>

            <div className="auth-actions">
              <button type="submit">
                <Lock size={16} />
                Entrar
              </button>
              <button type="button" className="ghost" onClick={onToggleReset}>
                <KeyRound size={16} />
                Esqueci minha senha
              </button>
            </div>
          </form>
        ) : (
          <form className="form" onSubmit={handleSubmit} aria-label="Formulário de cadastro">
            <label>
              Nome
              <input
                autoComplete="name"
                value={name}
                onChange={(event) => onNameChange(event.target.value)}
                required
              />
            </label>
            <label>
              Organização
              <input
                value={organizationName}
                onChange={(event) => onOrganizationChange(event.target.value)}
                required
              />
            </label>
            <label>
              Email
              <input
                autoComplete="email"
                type="email"
                value={email}
                onChange={(event) => onEmailChange(event.target.value)}
                required
              />
            </label>
            <label>
              Senha
              <PasswordInput
                value={password}
                onChange={onPasswordChange}
                autoComplete="new-password"
                visible={showSignupPassword}
                onToggleVisible={() => setShowSignupPassword((value) => !value)}
              />
            </label>

            <details className="auth-register-details">
              <summary>Dados profissionais (opcional)</summary>
              <div className="auth-extra-grid">
                <label>
                  Cargo
                  <input value={jobTitle} onChange={(event) => onJobTitleChange(event.target.value)} />
                </label>
                <label>
                  Área
                  <input value={department} onChange={(event) => onDepartmentChange(event.target.value)} />
                </label>
                <label>
                  Empresa
                  <input value={company} onChange={(event) => onCompanyChange(event.target.value)} />
                </label>
                <label>
                  Telefone
                  <input
                    autoComplete="tel"
                    value={phone}
                    onChange={(event) => onPhoneChange(event.target.value)}
                  />
                </label>
                <label>
                  Fuso horário
                  <input value={timezone} onChange={(event) => onTimezoneChange(event.target.value)} />
                </label>
                <label className="span-2">
                  Bio profissional
                  <textarea rows={3} value={bio} onChange={(event) => onBioChange(event.target.value)} />
                </label>
              </div>
            </details>

            <div className="password-policy" aria-live="polite">
              <span>
                {passwordReadyForRegister
                  ? "Senha pronta para cadastro."
                  : "Para novas contas, use uma senha forte:"}
              </span>
              <div>
                {passwordChecks.map((item) => (
                  <small key={item.id} className={item.passed ? "passed" : ""}>
                    {item.passed ? "✓" : "•"} {item.label}
                  </small>
                ))}
              </div>
            </div>

            <div className="auth-actions">
              <button type="submit" disabled={!passwordReadyForRegister}>
                <UserPlus size={16} />
                Criar conta
              </button>
              <button type="button" className="ghost" onClick={() => setMode("signin")}>
                <LogIn size={16} />
                Já tenho conta
              </button>
            </div>
          </form>
        )}

        {resetOpen ? (
          <section className="reset-panel">
            <div className="section-title-row">
              <KeyRound size={16} />
              <h2>Redefinir senha</h2>
            </div>
            <p>
              Solicite o email de redefinição e informe o token recebido para criar uma nova senha.
            </p>
            <div className="auth-extra-grid">
              <label>
                Email da conta
                <input
                  value={resetEmail}
                  onChange={(event) => onResetEmailChange(event.target.value)}
                />
              </label>
              <label>
                Token
                <input
                  value={resetToken}
                  onChange={(event) => onResetTokenChange(event.target.value)}
                />
              </label>
              <label className="span-2">
                Nova senha
                <PasswordInput
                  value={resetPassword}
                  onChange={onResetPasswordChange}
                  autoComplete="new-password"
                  visible={showResetPassword}
                  onToggleVisible={() => setShowResetPassword((value) => !value)}
                />
              </label>
            </div>
            <div className="password-policy compact" aria-live="polite">
              <span>{resetPasswordReady ? "Nova senha pronta." : "Requisitos da nova senha:"}</span>
              <div>
                {resetPasswordChecks.map((item) => (
                  <small key={item.id} className={item.passed ? "passed" : ""}>
                    {item.passed ? "✓" : "•"} {item.label}
                  </small>
                ))}
              </div>
            </div>
            <div className="auth-actions">
              <button type="button" className="secondary" onClick={onRequestPasswordReset}>
                <MailCheck size={16} />
                Enviar email
              </button>
              <button type="button" onClick={onConfirmPasswordReset} disabled={!resetPasswordReady}>
                <Lock size={16} />
                Salvar nova senha
              </button>
            </div>
          </section>
        ) : null}

        {notice ? (
          <div className={`toast inline ${notice.tone}`} role="status" aria-live="polite">
            {notice.tone === "success" ? (
              <CheckCircle2 size={18} />
            ) : notice.tone === "error" ? (
              <AlertTriangle size={18} />
            ) : (
              <Activity size={18} />
            )}
            <span>{notice.message}</span>
            <button
              type="button"
              className="toast-close"
              aria-label="Fechar notificação"
              onClick={onCloseNotice}
            >
              ✕
            </button>
          </div>
        ) : null}
      </section>
    </main>
  );
}
