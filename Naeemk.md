BUG BOUNTY TIPS & References
============================

#TOOLS 
./././.
Corsy - CORS Misconfiguration Scanner  >>  https://github.com/s0md3v/Corsy/
Auto tool use to find CORS bug .

#Prerequisites
=============
BURP HEADER> Origin: https://evil.com <br>
VICTIM HEADER> Access-Control-Allow-Credential: true<br>
VICTIM HEADER> Access-Control-Allow-Origin: https://evil.com OR Access-Control-Allow-Origin: null

#Exploitation
-------------
<b>
Usually you want to target an API endpoint. Use the following payload to exploit a CORS misconfiguration on target https://victim.example.com/endpoint.
<b>
<br>

Vulnerable Example: Origin Reflection
--------------------------------------
<link>https://victim.example.com/endpoint</link>

#Bug Bounty reports
====================
https://hackerone.com/reports/168574<br>
https://hackerone.com/reports/426147<br>
https://hackerone.com/reports/235200<br>
https://hackerone.com/reports/430249<br>
https://hackerone.com/reports/470298<br>





