export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { phone, templateName, customerName, customerId } = req.body || {};
  if (!phone || !templateName || !customerName || !customerId) {
    return res.status(400).json({ error: 'Phone, template name, customer name, and customer ID are required' });
  }

  const formattedPhone = String(phone).replace(/\D/g, '');
  const internationalPhone = formattedPhone.length === 10 ? `91${formattedPhone}` : formattedPhone;

  if (!process.env.PHONE_NUMBER_ID || !process.env.WHATSAPP_TOKEN) {
    return res.status(500).json({ error: 'WhatsApp environment variables are not configured' });
  }

  const payload = {
    messaging_product: 'whatsapp',
    to: internationalPhone,
    type: 'template',
    template: {
      name: templateName.trim(),
      language: { code: 'en' },
      components: [{
        type: 'body',
        parameters: [
          { type: 'text', text: String(customerName).trim() },
          { type: 'text', text: String(customerId).trim() }
        ]
      }]
    }
  };

  try {
    const response = await fetch(
      `https://graph.facebook.com/v22.0/${process.env.PHONE_NUMBER_ID}/messages`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${process.env.WHATSAPP_TOKEN}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      }
    );

    const data = await response.json();
    if (!response.ok) {
      return res.status(response.status).json({ error: data.error?.message || 'Failed to send template' });
    }

    return res.status(200).json({ success: true, messageId: data.messages?.[0]?.id });
  } catch (error) {
    return res.status(500).json({ error: error.message || 'Unable to reach WhatsApp' });
  }
}
