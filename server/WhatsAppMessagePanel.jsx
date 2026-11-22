import { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle, CheckCheck, ChevronDown, Loader2, MessageCircle, Send } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function formatDisplayDate(isoDate) {
  if (!isoDate) return '';
  const [year, month, day] = isoDate.split('-');
  const monthIndex = Number(month) - 1;
  if (!year || !day || !MONTHS[monthIndex]) return isoDate;
  return `${day}-${MONTHS[monthIndex]}-${year}`;
}

/**
 * Map template fields from API response into a lookup by field name.
 * Each template from backend has fields like:
 *   { name: "vehicle_number", label: "Vehicle Number", field_type: "text"|"date", ... }
 */
function buildFieldConfig(templateFields) {
  return templateFields.map((f) => ({
    key: f.name,
    label: f.label,
    placeholder: f.placeholder || f.example || '',
    type: f.field_type === 'date' ? 'date' : 'text',
    required: f.required,
  }));
}

/**
 * WhatsApp Admin Notification Panel
 *
 * Fetches templates dynamically from the FastAPI backend, renders form fields
 * based on template metadata, previews via API, and sends via Meta Cloud API
 * (or dry-run simulator).
 *
 * Props:
 * - apiBase: string — backend base URL (default: 'http://localhost:8000')
 * - initialValues: { phone, ...fieldValues } — optional pre-filled form values
 * - countryCode: string — default '91'
 * - onSend({ response }): called after a successful send with the API response
 * - className: extra classes for the outer card
 */
export default function WhatsAppMessagePanel({
  apiBase = API_BASE,
  initialValues = {},
  countryCode = '91',
  onSend,
  className = '',
} = {}) {
  // ─── Template loading from API ────────────────────────────────────
  const [templates, setTemplates] = useState([]);
  const [templatesLoading, setTemplatesLoading] = useState(true);
  const [templatesError, setTemplatesError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchTemplates() {
      setTemplatesLoading(true);
      setTemplatesError(null);
      try {
        const res = await fetch(`${apiBase}/api/templates`);
        if (!res.ok) throw new Error(`Failed to load templates (${res.status})`);
        const data = await res.json();
        if (!cancelled) setTemplates(data);
      } catch (err) {
        if (!cancelled) setTemplatesError(err.message);
      } finally {
        if (!cancelled) setTemplatesLoading(false);
      }
    }
    fetchTemplates();
    return () => { cancelled = true; };
  }, [apiBase]);

  // ─── Form state ───────────────────────────────────────────────────
  const [selectedTemplateName, setSelectedTemplateName] = useState('');
  const [phone, setPhone] = useState(initialValues.phone ?? '');
  const [fieldValues, setFieldValues] = useState({});
  const [showPreview, setShowPreview] = useState(false);

  // ─── API action state ─────────────────────────────────────────────
  const [previewText, setPreviewText] = useState('');
  const [previewLoading, setPreviewLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState(null); // { success, message_id, dry_run }
  const [apiError, setApiError] = useState(null);

  // Select first template once loaded
  useEffect(() => {
    if (templates.length > 0 && !selectedTemplateName) {
      setSelectedTemplateName(templates[0].name);
    }
  }, [templates, selectedTemplateName]);

  const selectedTemplate = templates.find((t) => t.name === selectedTemplateName);
  const fieldConfig = useMemo(
    () => (selectedTemplate ? buildFieldConfig(selectedTemplate.fields) : []),
    [selectedTemplate]
  );

  // Reset field values when template changes
  useEffect(() => {
    if (selectedTemplate) {
      const defaults = {};
      for (const f of selectedTemplate.fields) {
        defaults[f.name] = initialValues[f.name] ?? '';
      }
      setFieldValues(defaults);
      setShowPreview(false);
      setPreviewText('');
      setSendResult(null);
      setApiError(null);
    }
  }, [selectedTemplateName]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleFieldChange(fieldName, value) {
    setFieldValues((prev) => ({ ...prev, [fieldName]: value }));
    setSendResult(null);
    setApiError(null);
  }

  // ─── Validation ───────────────────────────────────────────────────
  const isValid = useMemo(() => {
    if (phone.replace(/\D/g, '').length < 10) return false;
    for (const fc of fieldConfig) {
      if (fc.required && !String(fieldValues[fc.key] ?? '').trim()) return false;
    }
    return true;
  }, [phone, fieldValues, fieldConfig]);

  // Build parameters object for API: format dates to display format
  const buildParams = useCallback(() => {
    const params = {};
    for (const fc of fieldConfig) {
      let val = String(fieldValues[fc.key] ?? '').trim();
      if (fc.type === 'date' && val) {
        val = formatDisplayDate(val);
      }
      params[fc.key] = val;
    }
    return params;
  }, [fieldValues, fieldConfig]);

  // ─── Preview via API ──────────────────────────────────────────────
  async function handlePreview() {
    if (!selectedTemplate) return;
    setPreviewLoading(true);
    setApiError(null);
    setSendResult(null);

    try {
      const res = await fetch(`${apiBase}/api/messages/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_name: selectedTemplate.name,
          parameters: buildParams(),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Preview failed (${res.status})`);
      }

      const data = await res.json();
      setPreviewText(data.rendered_text);
      setShowPreview(true);
    } catch (err) {
      setApiError(err.message);
      setShowPreview(false);
    } finally {
      setPreviewLoading(false);
    }
  }

  // ─── Send via API ─────────────────────────────────────────────────
  async function handleSend() {
    if (!isValid || !selectedTemplate || sending) return;
    setSending(true);
    setApiError(null);
    setSendResult(null);

    try {
      const res = await fetch(`${apiBase}/api/messages/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: phone.trim(),
          template_name: selectedTemplate.name,
          parameters: buildParams(),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Send failed (${res.status})`);
      }

      const data = await res.json();
      setSendResult(data);
      onSend?.({ response: data });
    } catch (err) {
      setApiError(err.message);
    } finally {
      setSending(false);
    }
  }

  // ─── Loading / Error states for template fetch ────────────────────
  if (templatesLoading) {
    return (
      <div className={`w-full max-w-md mx-auto rounded-3xl border border-stone-200 bg-white p-6 sm:p-7 ${className}`}>
        <div className="flex items-center justify-center gap-2 py-12 text-stone-400">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm">Loading templates…</span>
        </div>
      </div>
    );
  }

  if (templatesError) {
    return (
      <div className={`w-full max-w-md mx-auto rounded-3xl border border-red-200 bg-white p-6 sm:p-7 ${className}`}>
        <div className="flex flex-col items-center gap-3 py-8">
          <AlertCircle className="h-8 w-8 text-red-400" />
          <p className="text-sm text-red-600 text-center">{templatesError}</p>
          <p className="text-xs text-stone-400">
            Is the backend running at <code className="rounded bg-stone-100 px-1.5 py-0.5">{apiBase}</code>?
          </p>
        </div>
      </div>
    );
  }

  if (!selectedTemplate) return null;

  // ─── Customer name field (for avatar/preview header) ──────────────
  const personNameField = fieldConfig.find(
    (f) => f.key === 'person_name' || f.key === 'customer_name'
  );
  const personNameValue = personNameField ? String(fieldValues[personNameField.key] ?? '').trim() : '';

  return (
    <div className={`w-full max-w-md mx-auto rounded-3xl border border-stone-200 bg-white p-6 sm:p-7 ${className}`}>
      {/* Header */}
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600">
          <MessageCircle className="h-5 w-5" strokeWidth={2} />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-stone-900">Send reminder</h2>
          <p className="text-sm text-stone-500">{selectedTemplate.description}</p>
        </div>
      </div>

      {/* Template selector */}
      <div className="mb-4">
        <label htmlFor="wa-template" className="mb-1.5 block text-sm font-medium text-stone-700">
          Template
        </label>
        <div className="relative">
          <select
            id="wa-template"
            value={selectedTemplateName}
            onChange={(e) => setSelectedTemplateName(e.target.value)}
            className="w-full appearance-none rounded-xl border border-stone-200 bg-white px-3.5 py-2.5 pr-9 text-sm text-stone-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          >
            {templates.map((t) => (
              <option key={t.name} value={t.name}>
                {t.title}
              </option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
        </div>
      </div>

      {/* Phone number */}
      <div className="mb-4">
        <label htmlFor="wa-phone" className="mb-1.5 block text-sm font-medium text-stone-700">
          Phone number
        </label>
        <div className="flex items-stretch overflow-hidden rounded-xl border border-stone-200 focus-within:border-emerald-500 focus-within:ring-2 focus-within:ring-emerald-100">
          <span className="flex items-center border-r border-stone-200 bg-stone-50 px-3 text-sm font-medium text-stone-500">
            +{countryCode}
          </span>
          <input
            id="wa-phone"
            type="tel"
            inputMode="numeric"
            value={phone}
            onChange={(e) => { setPhone(e.target.value); setSendResult(null); setApiError(null); }}
            placeholder="98XXXXXXXX"
            className="w-full bg-white px-3 py-2.5 text-sm text-stone-900 outline-none"
          />
        </div>
      </div>

      {/* Dynamic template fields from API */}
      {fieldConfig.map((fc) => (
        <div className="mb-4" key={fc.key}>
          <label htmlFor={`wa-${fc.key}`} className="mb-1.5 block text-sm font-medium text-stone-700">
            {fc.label}
          </label>
          <input
            id={`wa-${fc.key}`}
            type={fc.type}
            value={fieldValues[fc.key] ?? ''}
            onChange={(e) =>
              handleFieldChange(
                fc.key,
                fc.type === 'text' && fc.key.includes('vehicle')
                  ? e.target.value.toUpperCase()
                  : e.target.value
              )
            }
            placeholder={fc.placeholder}
            className={`w-full rounded-xl border border-stone-200 bg-white px-3.5 py-2.5 text-sm text-stone-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 ${
              fc.key.includes('vehicle') ? 'font-mono tracking-wider' : ''
            }`}
          />
        </div>
      ))}

      {/* API Preview (from server) */}
      {showPreview && previewText && (
        <div className="mb-6 rounded-2xl border border-stone-200 bg-stone-50 p-4">
          <div className="mb-2 flex items-center gap-2 text-xs font-medium text-stone-500">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-xs font-semibold text-emerald-700">
              {(personNameValue || '?').charAt(0).toUpperCase()}
            </span>
            <span>{personNameValue || 'Customer'}</span>
          </div>
          <div className="max-w-xs rounded-2xl rounded-tl-sm bg-emerald-50 px-3.5 py-2.5 text-sm leading-relaxed text-stone-800 whitespace-pre-line">
            {previewText}
            <div className="mt-1.5 flex items-center justify-end gap-1 text-xs text-stone-400">
              <span>now</span>
              <CheckCheck className="h-3 w-3" />
            </div>
          </div>
        </div>
      )}

      {/* Success result */}
      {sendResult && (
        <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
          <div className="flex items-center gap-2">
            <CheckCheck className="h-4 w-4 text-emerald-600" />
            <span className="text-sm font-medium text-emerald-800">
              {sendResult.dry_run ? 'Simulated send (dry-run)' : 'Message sent successfully!'}
            </span>
          </div>
          <p className="mt-1 text-xs text-emerald-600 font-mono break-all">
            ID: {sendResult.message_id}
          </p>
          {sendResult.dry_run && (
            <p className="mt-1 text-xs text-amber-600">
              ⚠ DRY_RUN is enabled on the server. No real message was sent to WhatsApp.
            </p>
          )}
        </div>
      )}

      {/* Error display */}
      {apiError && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
            <p className="text-sm text-red-700">{apiError}</p>
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <button
          type="button"
          onClick={handlePreview}
          disabled={!isValid || previewLoading}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-medium text-stone-700 transition hover:bg-stone-50 focus:outline-none focus:ring-2 focus:ring-stone-200 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {previewLoading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
          {showPreview ? 'Refresh preview' : 'Preview message'}
        </button>
        <button
          type="button"
          onClick={handleSend}
          disabled={!isValid || sending}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-200 disabled:cursor-not-allowed disabled:bg-stone-200 disabled:text-stone-400"
        >
          {sending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          {sending ? 'Sending…' : 'Send via WhatsApp'}
        </button>
      </div>
      {!isValid && (
        <p className="mt-2.5 text-center text-xs text-stone-400">Fill in all fields to send</p>
      )}
    </div>
  );
}
