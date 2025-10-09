"""HTML5 entities map: { name -> characters }."""
import html.entities

entities = {name.rstrip(";"): chars for name, chars in html.entities.html5.items()}
