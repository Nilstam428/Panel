import { useEffect, useMemo, useState } from "react";
import { AlertCircle, ArrowUpRight, Check, CheckCheck, LoaderCircle, MessageCircle, Send, ShieldCheck, Sparkles } from "lucide-react";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

async function apiRequest(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail;
    throw new Error(typeof detail === "string" ? detail : `Request failed (${response.status})`);
  }
  return data;
}

function fieldType(field) {
  return field.field_type === "date" ? "date" : "text";
}

function formatDate(value) {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  const [year, month, day] = value.split("-");
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${day}-${months[Number(month) - 1]}-${year}`;
}

export default function App() {
  const [templates, setTemplates] = useState([]);
  const [templateName, setTemplateName] = useState("");
  const [phone, setPhone] = useState("");
  const [values, setValues] = useState({});
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [busy, setBusy] = useState("");

  useEffect(() => {
    apiRequest("/api/templates")
      .then((items) => {
        setTemplates(items);
        if (items.length) setTemplateName(items[0].name);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoadingTemplates(false));
  }, []);

  const selected = templates.find((item) => item.name === templateName);
  const fields = useMemo(() => selected?.fields || [], [selected]);
  const valid = phone.replace(/\D/g, "").length >= 10 && fields.every((field) => !field.required || String(values[field.name] || "").trim());

  useEffect(() => {
    if (!selected) return;
    const next = {};
    selected.fields.forEach((field) => { next[field.name] = ""; });
    setValues(next);
    setPreview("");
    setResult(null);
    setError("");
  }, [templateName]);

  function buildParameters() {
    return Object.fromEntries(fields.map((field) => {
      const value = String(values[field.name] || "").trim();
      return [field.name, fieldType(field) === "date" ? formatDate(value) : value];
    }));
  }

  async function handlePreview() {
    setBusy("preview"); setError(""); setResult(null);
    try {
      const data = await apiRequest("/api/messages/preview", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ template_name: templateName, parameters: buildParameters() }),
      });
      setPreview(data.rendered_text);
    } catch (err) { setError(err.message); }
    finally { setBusy(""); }
  }

  async function handleSend(event) {
    event.preventDefault();
    if (!valid || busy) return;
    setBusy("send"); setError(""); setResult(null);
    try {
      const data = await apiRequest("/api/messages/send", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: phone.trim(), template_name: templateName, parameters: buildParameters() }),
      });
      setResult(data);
    } catch (err) { setError(err.message); }
    finally { setBusy(""); }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#home" aria-label="Message Center home">
          <span className="brand-mark"><MessageCircle size={20} strokeWidth={2.2} /></span>
          <span>message<span className="brand-light">center</span></span>
        </a>
        <div className="topbar-status"><span className="status-dot" /> Notification workspace</div>
      </header>

      <section className="hero" id="home">
        <div className="hero-copy">
          <div className="eyebrow"><Sparkles size={14} /> CUSTOMER COMMUNICATIONS</div>
          <h1>Make every reminder <span>feel personal.</span></h1>
          <p>Send timely vehicle compliance updates to your customers, right where they are.</p>
          <div className="trust-note"><ShieldCheck size={16} /> Preview every message before it goes out</div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="art-orbit orbit-one" /><div className="art-orbit orbit-two" />
          <div className="art-bubble"><MessageCircle size={34} /></div>
          <span className="art-spark spark-one">✦</span><span className="art-spark spark-two">✧</span>
        </div>
      </section>

      <section className="workspace">
        <div className="section-heading">
          <div><p className="section-kicker">NEW MESSAGE</p><h2>Compose a reminder</h2></div>
          <span className="secure-label"><ShieldCheck size={15} /> Secure send</span>
        </div>

        {loadingTemplates ? (
          <div className="loading-state"><LoaderCircle className="spin" size={22} /> Loading your message templates…</div>
        ) : templates.length === 0 ? (
          <div className="notice notice-error"><AlertCircle size={18} /><span>{error || "No templates are available. Check that the API is running."}</span></div>
        ) : (
          <form onSubmit={handleSend}>
            <div className="form-grid">
              <div className="field field-wide">
                <label htmlFor="template">Message template <span className="required">*</span></label>
                <select id="template" value={templateName} onChange={(event) => setTemplateName(event.target.value)}>
                  {templates.map((item) => <option value={item.name} key={item.name}>{item.title}</option>)}
                </select>
                {selected?.description && <p className="field-hint">{selected.description}</p>}
              </div>
              <div className="field field-wide">
                <label htmlFor="phone">Customer phone number <span className="required">*</span></label>
                <div className="phone-input"><span className="country-code">+91</span><input id="phone" type="tel" inputMode="tel" autoComplete="tel-national" value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="98765 43210" /></div>
                <p className="field-hint">Include the country code if the number is outside India.</p>
              </div>
              {fields.map((field) => (
                <div className="field" key={field.name}>
                  <label htmlFor={`field-${field.name}`}>{field.label}{field.required && <span className="required"> *</span>}</label>
                  <input id={`field-${field.name}`} type={fieldType(field)} required={field.required} placeholder={field.placeholder || field.example || `Enter ${field.label.toLowerCase()}`} value={values[field.name] || ""} onChange={(event) => setValues((current) => ({ ...current, [field.name]: field.name.includes("vehicle") ? event.target.value.toUpperCase() : event.target.value }))} />
                </div>
              ))}
            </div>

            {preview && <div className="preview-card"><div className="preview-heading"><span className="preview-avatar">{(values.person_name || values.customer_name || "C").charAt(0).toUpperCase()}</span><div><strong>{values.person_name || values.customer_name || "Customer"}</strong><small>WhatsApp preview</small></div><CheckCheck className="preview-check" size={17} /></div><div className="chat-bubble">{preview}</div></div>}
            {result && <div className="notice notice-success"><Check size={18} /><div><strong>{result.dry_run ? "Test message simulated" : "Message sent successfully"}</strong><span>{result.dry_run ? "Dry-run mode is on; no real WhatsApp message was sent." : `Message ID: ${result.message_id}`}</span></div></div>}
            {error && templates.length > 0 && <div className="notice notice-error"><AlertCircle size={18} /><span>{error}</span></div>}

            <div className="form-footer">
              <p><span className="required">*</span> Required fields</p>
              <div className="actions">
                <button className="button button-secondary" type="button" onClick={handlePreview} disabled={!valid || Boolean(busy)}>{busy === "preview" ? <LoaderCircle className="spin" size={16} /> : <MessageCircle size={16} />} Preview message</button>
                <button className="button button-primary" type="submit" disabled={!valid || Boolean(busy)}>{busy === "send" ? <LoaderCircle className="spin" size={16} /> : <Send size={16} />} Send reminder <ArrowUpRight size={15} /></button>
              </div>
            </div>
          </form>
        )}
      </section>
      <footer className="page-footer">Thoughtful reminders. Safer roads. <span>·</span> Powered by WhatsApp Cloud API</footer>
    </main>
  );
}
