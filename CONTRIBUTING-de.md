*Diese Anleitung in anderen Sprachen: [Français](CONTRIBUTING-fr.md), [Español](CONTRIBUTING-es.md), [简体中文](CONTRIBUTING-zh.md), [繁體中文](CONTRIBUTING-zh_TW.md), [فارسی](CONTRIBUTING-fa_IR.md), [Tiếng Việt](CONTRIBUTING-vn.md), [Русский](CONTRIBUTING-ru.md), [Português Brasileiro](CONTRIBUTING-pt_BR.md), [한국어](CONTRIBUTING-ko.md).*

## Lizenzvereinbarung für Mitwirkende
Durch Deine Mitwirkung akzeptierst Du die [Lizenz](https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE) dieses Repositorys.

## Verhaltenskodex für Mitwirkende
Durch Deine Mitwirkung verpflichtest Du Dich, dem [Verhaltenskodex](https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT.md) dieses Repositorys zu folgen.

## Kurzfassung
1. „Ein Link, um ein Buch auf einfache Weise herunterzuladen“ ist nicht immer ein Link zu einem *kostenlosen* Buch. Bitte füge nur kostenlose Inhalte hinzu. Vergewissere Dich, dass sie kostenlos sind. Wir akzeptieren keine Links zu Seiten, die *voraussetzen*, dass man sich mit einer funktionierenden E-Mail-Adresse registriert, um ein Buch herunterzuladen, aber wir heißen Seiten willkommen, die um (optionale) Eingaben von E-Mail-Adressen bitten.
2. Du musst Dich nicht mit Git auskennen: Wenn Du etwas Interessantes gefunden hast, *das noch nicht in einer der Listen enthalten ist*, öffne bitte ein [Issue](https://github.com/EbookFoundation/free-programming-books/issues) mit Deinen Linkvorschlägen.
    - Wenn Du Dich mit Git auskennst, erstelle einen Fork des Repositorys und sende einen Pull Request.
3. Wir führen 5 Arten von Listen. Achte darauf, die richtige zu wählen:

    - *Bücher*: PDF, HTML, ePub, eine auf gitbook.io basierende Seite, ein Git Repo etc.
    - *Kurse*: Ein Kurs beschreibt Lernmaterialien, die nicht in Buchform existieren. [Dies ist ein Kurs](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Interaktive Tutorials*: Eine interaktive Webseite, die den Benutzer Sourcecode oder Kommandos eingeben lässt und das Resultat auswertet (mit "auswerten" meinen wir nicht "bewerten"). z.&nbsp;B.: [Try Haskell](http://tryhaskell.org), [Try Github](http://try.github.io).
    - *Podcasts und Screencasts*: Podcasts und Screencasts.
    - *Problem Sets & Competitive Programming*: Eine Webseite oder Software, die Dir die Möglichkeit gibt, Deine Programmierfähigkeiten durch die Lösung einfacher oder komplexer Problemstellungen auf die Probe zu stellen, mit oder ohne Code Review und mit oder ohne den Vergleich der Leistungen mit anderen Besuchern der Seite.

4. Stell sicher, dass Du den [Richtlinien](#richtlinien) folgst und die [Markdown Formatierung](#formatierung) der Dateien beachtest.

5. GitHub Actions werden Tests ausführen, um sicherzustellen, dass die Listen korrekt alphabetisiert sind und den Formatierungsregeln Folge geleistet wurde. Stell sicher, dass Deine Änderungen diese Tests bestehen.

### Richtlinien
- Stell sicher, dass ein Buch wirklich kostenlos ist. Vergewissere Dich noch einmal, falls nötig. Es hilft den Administratoren, wenn Du in Deinem PR beschreibst, warum Du der Ansicht bist, dass das jeweilige Buch kostenlos ist.
- Wir nehmen keine Dateien auf, die auf Google Drive, Dropbox, Mega, Scribd, Issuu oder einer vergleichbaren Upload-Plattform liegen.
- Füge die Links in alphabetischer Reihenfolge ein. Wenn Du einen fehlerhaft eingefügten Link findest, korrigiere bitte die Reihenfolge und öffne eine PR.
- Wähle immer den Link der maßgeblichen Quelle aus (das heißt, dass die Website des Autors besser ist als die eines Redakteurs, welche wiederum besser wäre als die einer Drittanbieterseite)
    + Keine File Hosting Plattformen (inklusive Links zu Dropbox, Google Drive u.ä.)
- Ein `https` Link sollte einem `http` Link immer vorgezogen werden -- solange sie auf dieselbe Domain und denselben Inhalt verweisen. 
- Auf Root Domains sollte der abschließende Schrägstrich entfernt werden: `http://example.com` anstelle von `http://example.com/`
- Wähle immer den kürzesten Link: `http://example.com/dir/` ist besser als `http://example.com/dir/index.html`
    + Benutze keine URL-Verkürzer
- Wähle bevorzugt den Link zur aktuellsten Version anstatt eine konkrete Version zu verlinken: `http://example.com/dir/book/current/` ist besser als `http://example.com/dir/book/v1.0.0/index.html`
- Wenn ein Link ein abgelaufenes oder selbst-signiertes Zertifikat nutzt oder ein anderes SSL Problem aufweist:
  1. *ersetze ihn* mit seinem `http` Gegenstück, wenn möglich (weil es auf Mobilgeräten kompliziert sein kann, Ausnahmen zuzulassen).
  2. *lass ihn wie er ist*, falls keine `http` Version verfügbar ist, auf den Link aber über `https` zugegriffen werden kann, indem man im Browser die Warnung ignoriert oder eine Ausnahme hinzufügt.
  3. *entferne ihn* anderenfalls.
- Wenn ein Link in verschiedenen Formaten existiert, füge einen separaten Link hinzu mit einem Hinweis zu jedem Format
- Wenn ein Inhalt an mehreren Stellen im Internet verfügbar ist
    + wähle den Link der maßgeblichen Quelle aus (das heißt, dass die Website des Autors besser ist als die eines Redakteurs, welche wiederum besser wäre als die einer Drittanbieterseite)
    + wenn sie verschiedene Ausgaben verlinken und Du der Meinung bist, dass sich diese Ausgaben in einem Maße unterscheiden, dass man alle aufheben sollte, füge einen separaten Link hinzu mit einem Hinweis zu jeder Ausgabe (siehe [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353), um Dich an der Diskussion zur Formatierung zu beteiligen.)
- Bevorzuge atomare Commits (ein Commit pro Änderung), anstatt größere Commits zu machen. Es besteht keine Notwendigkeit, die Commits vor dem Abschicken des PR zu squashen. (Wir werden die Befolgung dieser Regel niemals erzwingen, da es sich hier nur um die Vermeidung von Unannehmlichkeiten für die Maintainer handelt)
- Vermerke das Datum der Veröffentlichung im Titel, wenn es sich um ein älteres Buch handelt.
- Erfasse gegebenenfalls den Namen des oder der Autoren. Eine längere Liste von Autoren kann mit dem Zusatz "et al." gekürzt werden.
- Wenn das Buch noch nicht fertiggestellt ist und sich noch in Bearbeitung befindet, füge wie [unten](#in_process) beschrieben einen "in Bearbeitung" Hinweis hinzu.
- Wenn eine funktionierende E-Mail Adresse oder das Einrichten eines Benutzerkontos vor Aktivierung des Downloads erbeten wird, sollten angemessene Hinweise in Klammern angegeben werden, z.&nbsp;B.: `(E-Mail Adresse *erbeten*, nicht erforderlich)`

### Formatierung
- Bei allen Listen handelt es sich um `.md` Dateien. Versuche bitte, Dir die [Markdown](https://guides.github.com/features/mastering-markdown/) Syntax anzueignen. Sie ist ganz einfach!
- Alle Listen beginnen mit einem Inhaltsverzeichnis, in dem alle Abschnitte und Unterabschnitte verlinkt werden sollten. Bitte halte eine alphabetische Reihenfolge ein.
- Abschnitte nutzen Überschriften der Ebene 3 (`###`), während Unterabschnitte die 4. Ebene (`####`) nutzen.

Folgende Formatierungsregeln sollten eingehalten werden:
- `2` Leerzeilen zwischen dem letzten Link und einem neuen Abschnitt.
- `1` Leerzeile zwischen der Überschrift und dem ersten Link eines Abschnitts.
- `0` Leerzeilen zwischen zwei Links.
- `1` Leerzeile am Ende jeder `.md` Datei.

Beispiel:

    [...]
    * [Ein tolles Buch](http://example.com/example.html)
                                    (Leerzeile)
                                    (Leerzeile)
    ### Beispiel
                                    (Leerzeile)
    * [Noch ein tolles Buch](http://example.com/book.html)
    * [Ein anderes Buch](http://example.com/other.html)

- Keine Leerzeichen zwischen `]` und `(` einfügen:

```
FALSCH : * [Noch ein tolles Buch] (http://example.com/book.html)
RICHTIG: * [Noch ein tolles Buch](http://example.com/book.html)
```

- Wenn Du den Autor nennst, nutze ` - ` (einen mit Leerzeichen eingefassten Gedankenstrich):

```
FALSCH : * [Noch ein tolles Buch](http://example.com/book.html)- John Doe
RICHTIG: * [Noch ein tolles Buch](http://example.com/book.html) - John Doe
```

- Füge ein einzelnes Leerzeichen zwischen dem Link und seinem Dateiformat ein:

```
FALSCH : * [Ein sehr tolles Buch](https://example.org/book.pdf)(PDF)
RICHTIG: * [Ein sehr tolles Buch](https://example.org/book.pdf) (PDF)
```

- Der Autor wird vor dem Format genannt:

```
FALSCH : * [Ein sehr tolles Buch](https://example.org/book.pdf)- (PDF) Jane Roe
RICHTIG: * [Ein sehr tolles Buch](https://example.org/book.pdf) - Jane Roe (PDF)
```

- Verschiedene Formate:

```
FALSCH : * [Noch ein tolles Buch](http://example.com/)- John Doe (HTML)
FALSCH : * [Noch ein tolles Buch](https://downloads.example.org/book.html)- John Doe (download site)
RICHTIG: * [Noch ein tolles Buch](http://example.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
```

- Nenne das Jahr der Veröffentlichung im Titel bei älteren Publikationen:

```
FALSCH : * [Ein sehr tolles Buch](https://example.org/book.html) - Jane Roe - 1970
RICHTIG: * [Ein sehr tolles Buch (1970)](https://example.org/book.html) - Jane Roe
```

<a name="in_process"></a>
- Bücher in Bearbeitung:

```
RICHTIG: * [Wird bald ein tolles Buch sein](http://example.com/book2.html) - John Doe (HTML) (:construction: *in Bearbeitung*)
```

### Hinweise

Während die Grundlagen relativ einfach sind, existiert eine große Vielfalt von Ressourcen in unseren Listen. Es folgen einige Hinweise, wie wir mit dieser Vielfalt umgehen.

#### Metadaten

Unsere Listen enthalten einen minimalen Satz an Metadaten: Titel, URLs, Autoren, Plattformen und Zugriffshinweise.

##### Titel

- Keine erfundenen Titel. Wir versuchen, die Titel den Inhalten selbst zu entnehmen; Mitwirkende werden dazu ermahnt, sich keine Titel auszudenken oder redaktionell zu nutzen, falls dies vermieden werden kann. Eine Ausnahme bilden ältere Werke; wenn sie vor allem von historischem Interesse sind, kann das Hinzufügen einer Jahreszahl in Klammern den Nutzern helfen zu bestimmen, ob die Inhalte für sie nützlich sind.   
- Keine Titel, die NUR GROßBUCHSTABEN ENTHALTEN. Titelkapitalisierung ist normalerweise angemessen, aber im Zweifel nutze einfach die Formatierung der Originalquelle.

##### URLs

- Wir erlauben keine gekürzten URLs.
- Sämtliche Tracking-Codes sind aus der URL zu entfernen.
- Internationale URLs sollten entsprechend maskiert/escaped werden. Auch wenn Adressleisten in Browsern diese üblicherweise in Unicode darstellen, nutze bitte kopieren & einfügen.
- Sichere (https) URLs werden immer nicht-sicheren (http) URLs vorgezogen, wenn von der Quelle https implementiert wurde.
- Wir mögen keine URLs, die auf Webseiten zeigen, die den angegebenen Inhalt nicht bereitstellen, sondern stattdessen an andere Stelle umleiten.

##### Urheber

- Wir wollen alle Urheber kostenloser Inhalte angemessen nennen, inklusive eventueller Übersetzer!
- For übersetzte Werke sollte der Autor des ursprünglichen Werks genannt werden.
- Wir erlauben keine Links für Urheber.
- Für Sammlungen oder neu zusammengestellte Werke, benötigt der "Urheber" eventuell eine Beschreibung. Bücher von "GoalKicker" werden z.&nbsp;B. als "Zusammengestellt aus StackOverflow Dokumentationen" gekennzeichnet.

##### Plattformen und Zugriffshinweise

- Kurse. Insbesondere bei unseren Kurslisten spielt die Plattform eine wichtige Rolle in der Beschreibung des Inhalts. Der Grund dafür ist, dass Kurs-Plattformen unterschiedliche Zugangsmodelle und Angebotscharakter haben. Obwohl wir keine Bücher aufnehmen, die eine Registrierung erfordern, können viele Kurs-Plattformen ohne irgendeine Art der Registrierung nicht funktionieren. Beispiele für Kurs-Plattformen sind Coursera, EdX, Udacity und Udemy. Wenn ein Kurs von einer bestimmten Plattform abhängt, sollte der Name der Plattform in Klammern angehängt werden. 
- YouTube. Wir haben viele Kurse in Form von YouTube Wiedergabelisten. Wir führen Youtube nicht als Plattform auf, sondern versuchen den Urheber des Kurses zu nennen, der oftmals eine Unter-Plattform darstellt.
- YouTube Videos. Wir verlinken normalerweise keine einzelnen YouTube Videos. Ausnahmen bilden Videos von mehr als einer Stunde Länge, die wie ein Kurs oder Tutorial strukturiert sind. 
- Leanpub. Leanpub beherbergt Bücher mit einer Vielzahl von Zugangsmodellen. Manchmal kann ein Buch ohne Registrierung gelesen werden; in anderen Fällen wird ein Leanpub Konto für einen kostenfreien Zugang benötigt. Aufgrund der Qualität der Bücher und der unterschiedlichen und fließenden Zugangsmodelle erlauben wir die Aufnahme letzterer, wenn sie mit dem Zugriffshinweis *(Leanpub Konto oder gültige E-Mail angefordert)* versehen sind.

#### Genre

Die wichtigste Regel zur korrekten Zuordnung von Inhalten in Listen ist zu schauen, wie die Ressource sich selbst beschreibt. Wenn sie sich als Buch bezeichnet, dann ist sie vielleicht ein Buch.   

##### Genres, die wir nicht aufnehmen

Da das Internet unermesslich ist, nehmen wir folgende Inhalte nicht in unsere Listen auf:

- Blogs
- Blogeinträge
- Artikel
- Webseiten (außer jene, die SEHR viele Inhalte bereitstellen, die wir in unseren Listen führen.)
- Videos, die keine Kurse oder Screencasts sind.
- einzelne Buchkapitel
- Teaser oder Muster aus Büchern
- IRC oder Telegram Kanäle
- Slack Workspaces oder Mailinglisten

Unsere Listen zu Programmierwettbewerben setzen diese Verbote nicht so strikt um. Art und Umfang des Repositorys wird von der Community bestimmt; wenn Du eine Änderung oder Ausweitung der Ausrichtung vorschlagen möchtest, eröffne bitte ein Issue, um den Vorschlag zu unterbreiten. 

##### Buch vs. anderes Zeug

Wir sind nicht kleinlich, was die Definition, was ein Buch ist und was nicht. Hier sind einige Eigenschaften, die darauf hinweisen, dass es sich bei einer bestimmten Ressource um ein Buch handelt: 

- es hat eine ISBN (International Standard Book Number)
- es hat ein Inhaltsverzeichnis
- eine herunterladbare Version, besonders ePub, wird angeboten
- es hat verschiedene Auflagen
- es ist unabhängig von interaktiven Inhalten oder Videos
- es versucht, ein Thema umfassend zu behandeln
- es ist ein eigenständiges Werk

Vielen Büchern in unseren Listen fehlen diese Eigenschaften; es kann vom Kontext abhängen.  

##### Buch vs. Kurs

Das ist manchmal gar nicht so leicht zu unterscheiden!

Kurse kommen oftmals mit begleitenden Lehrbüchern, die wir in unseren Bücherlisten führen würden. Kurse bieten Vorträge, Übungen, Tests, Anmerkungen oder andere Lernhilfen. Ein einzelner Vortrag oder Video allein ist kein Kurs. Eine Powerpoint-Präsentation ist kein Kurs.  

##### Interaktive Tutorials vs. anderes Zeug

Wenn etwas ausgedruckt werden kann, ohne dass es seinen Nutzen verliert, ist es kein interaktives Tutorial.  

### Automatisierung

- Die Durchsetzung der Formatierungsregeln wird über [GitHub Actions](https://github.com/features/actions) mittels [fpb-lint](https://github.com/vhf/free-programming-books-lint) sichergestellt (siehe [.github/workflows/fpb-lint.yml](.github/workflows/fpb-lint.yml))
- Die URLs werden über [awesome_bot](https://github.com/dkhamsing/awesome_bot) validiert.
- Um die URL-Validierung auszulösen, kann ein Commit abgeschickt werden, der `check_urls=file_to_check` enthält:

```
check_urls=free-programming-books.md free-programming-books-en.md
```

- Man kann mehr als eine zu überprüfende Datei angeben, wobei die Einträge mit einem einzelnen Leerzeichen getrennt werden.
- Bei Angabe von mehr als einer Datei basiert das Ergebnis des Builds auf dem Ergebnis der letzten geprüften Datei. Du solltest Dir darüber im Klaren sein, dass dies zu gültigen Builds führen kann und daher das Build Protokoll am Ende des Pull Request durch Klick auf "Show all checks" -> "Details" genau geprüft werden sollte.   
