/**
 * Telnyx Call Control – Beispiel: Outbound Call mit AMD,
 * automatisches Bridging zur eigenen Nummer bei "Mensch"-Erkennung.
 *
 * Voraussetzungen:
 *   npm install express telnyx body-parser
 *
 * .env / Umgebungsvariablen:
 *   TELNYX_API_KEY        -> API Key aus dem Mission Control Portal
 *   TELNYX_CONNECTION_ID  -> Call Control Connection ID (nicht die Telefonnummer!)
 *   FROM_NUMBER           -> deine eigene, bei Telnyx zugeteilte Absendernummer, z.B. "+4930xxxxxxx"
 *   AGENT_NUMBER          -> die Nummer, zu der bei einem Human-Treffer gebridged wird
 *   PUBLIC_WEBHOOK_URL    -> öffentlich erreichbare URL dieses Servers (für Telnyx-Webhooks)
 *   PORT                  -> lokaler Port, z.B. 3000
 *
 * Wichtig: Der Connection muss im Mission Control Portal als
 * "Call Control Application" angelegt sein, und die Webhook-URL
 * muss dort auf PUBLIC_WEBHOOK_URL + /webhooks gesetzt werden.
 */

const express = require('express');
const bodyParser = require('body-parser');
const telnyx = require('telnyx')(process.env.TELNYX_API_KEY);

const app = express();
app.use(bodyParser.json());

const {
  TELNYX_CONNECTION_ID,
  FROM_NUMBER,
  AGENT_NUMBER,
  PORT = 3000,
} = process.env;

// Merkt sich zu jedem Kunden-Call, ob/mit welchem Agenten-Leg er verbunden werden soll
const pendingCalls = new Map();

/**
 * Startet einen ausgehenden Anruf mit Answering Machine Detection.
 * POST /dial  { "to": "+49301234567" }
 */
app.post('/dial', async (req, res) => {
  const { to } = req.body;
  if (!to) return res.status(400).json({ error: 'Feld "to" fehlt' });

  try {
    const call = await telnyx.calls.create({
      connection_id: TELNYX_CONNECTION_ID,
      to,
      from: FROM_NUMBER,
      answering_machine_detection: 'premium', // genauer, aber etwas langsamer als "detect"
      answering_machine_detection_config: {
        total_analysis_time_millis: 5000,
        after_greeting_silence_millis: 800,
      },
    });

    pendingCalls.set(call.data.call_control_id, { to, status: 'dialing' });
    res.json({ call_control_id: call.data.call_control_id });
  } catch (err) {
    console.error('Fehler beim Dial:', err.message);
    res.status(500).json({ error: err.message });
  }
});

/**
 * Zentraler Webhook-Endpunkt für alle Call-Control-Events.
 */
app.post('/webhooks', async (req, res) => {
  const event = req.body.data;
  const eventType = event.event_type;
  const callControlId = event.payload.call_control_id;

  console.log(`[Webhook] ${eventType} für ${callControlId}`);

  try {
    switch (eventType) {
      // AMD-Ergebnis liegt vor (bei answering_machine_detection: "premium")
      case 'call.machine.premium.detection.ended': {
        const result = event.payload.result; // "human", "machine", "not_sure", "fax" ...

        if (result === 'human') {
          await bridgeToAgent(callControlId);
        } else if (result === 'machine') {
          // Nicht sofort auflegen: wir warten auf das Ende der Ansage
          // und hinterlassen danach eine Nachricht (siehe Case unten).
          console.log(`Mailbox erkannt, warte auf Ende der Ansage: ${callControlId}`);
        } else {
          // "fax" oder "not_sure" -> hier bleibt es beim direkten Auflegen
          console.log(`Kein verwertbares Ergebnis (${result}) -> auflegen: ${callControlId}`);
          await telnyx.calls.hangup(callControlId);
          pendingCalls.delete(callControlId);
        }
        break;
      }

      // Die Begrüßungsansage der Mailbox ist zu Ende -> jetzt Nachricht abspielen
      case 'call.machine.premium.greeting.ended': {
        await telnyx.calls.speak(callControlId, {
          payload: 'Hallo, dies ist eine automatische Nachricht. Bitte rufen Sie uns zurück.',
          voice: 'female',
          language: 'de-DE',
        });
        break;
      }

      // Nachricht wurde vollständig abgespielt -> jetzt sauber auflegen
      case 'call.speak.ended': {
        await telnyx.calls.hangup(callControlId);
        pendingCalls.delete(callControlId);
        break;
      }

      // Falls du statt "premium" den einfacheren Modus "detect" nutzt:
      case 'call.machine.detection.ended': {
        const result = event.payload.result;
        if (result === 'human') {
          await bridgeToAgent(callControlId);
        } else {
          await telnyx.calls.hangup(callControlId);
          pendingCalls.delete(callControlId);
        }
        break;
      }

      case 'call.bridged':
        console.log(`Bridge erfolgreich für ${callControlId}`);
        break;

      case 'call.hangup':
        pendingCalls.delete(callControlId);
        break;

      default:
        // andere Events (call.initiated, call.answered, ...) ignorieren wir hier
        break;
    }
  } catch (err) {
    console.error('Fehler bei Webhook-Verarbeitung:', err.message);
  }

  res.sendStatus(200);
});

/**
 * Ruft die eigene Agenten-Nummer an und bridged sie automatisch,
 * sobald abgehoben wird, mit dem übergebenen Kunden-Call-Leg.
 */
async function bridgeToAgent(customerCallControlId) {
  console.log(`Mensch erkannt -> rufe Agent an und bridge mit ${customerCallControlId}`);

  await telnyx.calls.create({
    connection_id: TELNYX_CONNECTION_ID,
    to: AGENT_NUMBER,
    from: FROM_NUMBER,
    bridge_on_answer: true,
    link_to: customerCallControlId,
  });

  pendingCalls.set(customerCallControlId, { status: 'bridging' });
}

app.listen(PORT, () => {
  console.log(`Server läuft auf Port ${PORT}`);
  console.log('Webhook-Endpunkt: /webhooks | Dial-Endpunkt: /dial');
});