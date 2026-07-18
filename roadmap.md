
server - creating telnyx server


telnyx-server:
- ruft dich an bei start
- dann ist nutzer eingewählt
- bridge wird hergestellt und erste kontakt wird angerufen
- arbeitet json ab, ruft im loop immer den nächsten an, wenn aufgelegt
- braucht webhook, URL - kann erstellt werden, via 

hubspot search:
- liefert kontakte, die noch nie kontaktiert wurden "setup_telnyx_server" / Call Conrol App
https://developers.telnyx.com/api-reference/call-commands/bridge-calls#bridge-calls




GOALS:
(x) Hubspot connection
() telnyx verbindung herstellen

(x) Hubspot, nicht kontaktierte via search API-Endpoint finden

() HS Kontakte speichern


hs_srch:
- can receive all contadts which were never contacted




(x) hubspot search api call
() Hubspot serach api call call many

call via telnyx

call next from the json file and sort it into other file "called.json"