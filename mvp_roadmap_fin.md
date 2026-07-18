create call control app
with webhook url

get all events from webhook url

calls.dial with connection_id
in loop until 
answering_machine = human

if not human => dial next number

if = human => calls.tranfer(to my number)

when event = call.hang_up => start loop again