*[Read this in other languages](README.md#translations)*
*[Citiți aceasta în alte limbi](README.md#translations)*


## Acordul de licență pentru contribuitori

Prin contribuție, sunteți de acord cu [LICENSE](../LICENSE) al acestui depozit.


## Codul de conduită pentru contribuitori

Prin contribuție, sunteți de acord să respectați [Codul de conduită](CODE_OF_CONDUCT.md) al acestui depozit. ([traduceri](README.md#translations))


## Pe scurt

1. „Un link pentru a descărca ușor o carte" nu înseamnă întotdeauna o carte *gratuită*. Vă rugăm să contribuiți doar conținut gratuit. Asigurați-vă că este gratuit. Nu acceptăm linkuri către pagini care *cer* adrese de email funcționale pentru a obține cărți, dar acceptăm listări care le solicită.

2. Nu trebuie să știți Git: dacă ați găsit ceva interesant care *nu este deja în acest repo*, deschideți un [Issue](https://github.com/EbookFoundation/free-programming-books/issues) cu propunerile dvs. de linkuri.
    - Dacă știți Git, vă rugăm să faceți Fork repo-ului și să trimiteți Pull Requests (PR).

3. Avem 6 tipuri de liste. Alegeți-o pe cea potrivită:

    - *Books* : PDF, HTML, ePub, un site bazat pe gitbook.io, un repo Git etc.
    - *Courses* : Un curs este material didactic care nu este o carte. [Acesta este un curs](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Interactive Tutorials* : Un site interactiv care permite utilizatorului să tasteze cod sau comenzi și evaluează rezultatul (prin „evaluează” nu înțelegem „notează”). De ex.: [Try Haskell](http://tryhaskell.org), [Try Git](https://learngitbranching.js.org).
    - *Playgrounds* : site-uri interactive online, jocuri sau aplicații desktop pentru învățarea programării. Scrieți, compilați (sau rulați) și partajați fragmente de cod. Playgrounds permit deseori să forkați și să experimentați cu codul.
    - *Podcasts and Screencasts* : Podcasturi și screencast-uri.
    - *Problem Sets & Competitive Programming* : Un site sau software care vă permite să vă evaluați abilitățile de programare rezolvând probleme simple sau complexe, cu sau fără review de cod, cu sau fără compararea rezultatelor cu alți utilizatori.

4. Asigurați-vă că urmați [liniile directoare de mai jos](#guidelines) și respectați [formatul Markdown](#formatting) al fișierelor.

5. GitHub Actions va rula teste pentru a **se asigura că listele dvs. sunt ordonate alfabetic** și **că regulile de formatare sunt respectate**. **Verificați** că modificările dvs. trec testele.


### Linii directoare

- asigurați-vă că o carte este gratuită. Verificați de două ori dacă este nevoie. Ajută administratorii dacă comentați în PR de ce credeți că cartea este gratuită.
- nu acceptăm fișiere găzduite pe Google Drive, Dropbox, Mega, Scribd, Issuu și alte platforme similare de încărcare a fișierelor
- introduceți linkurile în ordine alfabetică, conform descrierii de mai jos ([alphabetical order](#alphabetical-order)).
- folosiți linkul cu cea mai autoritară sursă (adică site-ul autorului este mai bun decât site-ul editorului, iar acesta este mai bun decât un site terț)
    - fără servicii de găzduire de fișiere (inclusiv, dar fără a se limita la, linkuri Dropbox și Google Drive)
- preferați întotdeauna un link `https` în loc de `http` -- atât timp cât sunt pe același domeniu și servesc același conținut
- pe domeniile rădăcină, eliminați slash-ul terminal: `http://example.com` în loc de `http://example.com/`
- preferați întotdeauna linkul cel mai scurt: `http://example.com/dir/` este mai bun decât `http://example.com/dir/index.html`
    - fără linkuri scurtate (URL shortener)
- de regulă preferați linkul „curent” în locul celui „versiune”: `http://example.com/dir/book/current/` este mai bun decât `http://example.com/dir/book/v1.0.0/index.html`
- dacă un link are un certificat expirat/certificat self-signed/altă problemă SSL:
    1. *înlocuiți-l* cu echivalentul său `http` dacă este posibil (deoarece acceptarea excepțiilor poate fi complicată pe dispozitive mobile).
    2. *lăsați-l* dacă nu există o versiune `http`, dar linkul este accesibil prin `https` adăugând o excepție în browser sau ignorând avertismentul.
    3. *îndepărtați-l* în caz contrar.
- dacă un link există în multiple formate, adăugați un link separat cu o notă despre fiecare format
- dacă un resursă există în locuri diferite pe Internet
    - folosiți linkul cu cea mai autoritară sursă (site-ul autorului > site-ul editorului > site terț)
    - dacă ele duc la ediții diferite, iar dumneavoastră apreciați că edițiile sunt suficient de diferite pentru a merita păstrate, adăugați un link separat cu o notă despre fiecare ediție (vezi [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) pentru discuții despre formatare).
- preferați commit-uri atomice (un commit pentru adăugare/ștergere/modificare) în loc de commit-uri mari. Nu este necesar să faceți squash înainte de PR. (Nu vom impune această regulă; este doar pentru comoditatea întreținătorilor)
- dacă cartea este mai veche, includeți anul publicării în titlu.
- includeți numele autorului sau autorilor acolo unde este cazul. Puteți scurta lista autorilor cu "`et al.`".
- dacă cartea nu este finalizată și încă se lucrează la ea, adăugați nota "`in process`", așa cum este descris [mai jos](#in_process).
- dacă o resursă a fost restaurată folosind [*Internet Archive's Wayback Machine*](https://web.archive.org) (sau similar), adăugați nota "`archived`", așa cum este descris [mai jos](#archived). Cele mai bune versiuni de folosit sunt cele recente și complete.
- dacă se solicită o adresă de email sau configurarea unui cont înainte de a permite descărcarea, adăugați note potrivite limbii între paranteze, ex.: `(email address *requested*, not required)`.


### Formatare

- Toate listele sunt fișiere `.md`. Încercați să învățați [Markdown](https://guides.github.com/features/mastering-markdown/). Este simplu!
- Toate listele încep cu un Index. Ideea este să listați și să legați toate secțiunile și subsecțiunile acolo. Păstrați ordinea alfabetică.
- Secțiunile folosesc titluri de nivel 3 (`###`), iar subsecțiunile nivel 4 (`####`).

Ideea este să avem:

- `2` linii goale între ultimul link și o secțiune nouă.
- `1` linie goală între titlu și primul link din secțiune.
- `0` linii goale între două linkuri.
- `1` linie goală la sfârșitul fiecărui fișier `.md`.

Exemplu:

```text
 [...]
* [An Awesome Book](http://example.com/example.html)
                                (linie goală)
                                (linie goală)
### Example
                                (linie goală)
* [Another Awesome Book](http://example.com/book.html)
* [Some Other Book](http://example.com/other.html)
```

- Nu puneți spații între `]` și `(`:

    ```text
    BAD : * [Another Awesome Book] (http://example.com/book.html)
    GOOD: * [Another Awesome Book](http://example.com/book.html)
    ```

- Dacă includeți autorul, folosiți ` - ` (o cratimă înconjurată de un singur spațiu):

    ```text
    BAD : * [Another Awesome Book](http://example.com/book.html)- John Doe
    GOOD: * [Another Awesome Book](http://example.com/book.html) - John Doe
    ```

- Lăsați un singur spațiu între link și formatul său:

    ```text
    BAD : * [A Very Awesome Book](https://example.org/book.pdf)(PDF)
    GOOD: * [A Very Awesome Book](https://example.org/book.pdf) (PDF)
    ```

- Autorul vine înaintea formatului:

    ```text
    BAD : * [A Very Awesome Book](https://example.org/book.pdf)- (PDF) Jane Roe
    GOOD: * [A Very Awesome Book](https://example.org/book.pdf) - Jane Roe (PDF)
    ```

- Formate multiple (Preferăm un singur link pentru fiecare resursă. Când nu există un singur link cu acces facil la formatele diferite, linkurile multiple pot avea sens. Dar fiecare link adăugat crește povara de întreținere, așa că încercăm să evităm acest lucru.):

    ```text
    BAD : * [Another Awesome Book](http://example.com/)- John Doe (HTML)
    BAD : * [Another Awesome Book](https://downloads.example.org/book.html)- John Doe (download site)
    GOOD: * [Another Awesome Book](http://example.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
    ```

- Includeți anul publicării în titlu pentru cărțile vechi:

    ```text
    BAD : * [A Very Awesome Book](https://example.org/book.html) - Jane Roe - 1970
    GOOD: * [A Very Awesome Book (1970)](https://example.org/book.html) - Jane Roe
    ```

- <a id="in_process"></a>Cărți în curs de lucru:

    ```text
    GOOD: * [Will Be An Awesome Book Soon](http://example.com/book2.html) - John Doe (HTML) *( :construction: in process)*
    ```

- <a id="archived"></a>Link arhivat:

    ```text
    GOOD: * [A Way-backed Interesting Book](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) *( :card_file_box: archived)*
    ```
    
- <a id="license"></a>Licențe gratuite (În timp ce includem resurse care sunt "All Rights Reserved" dar gratuite pentru citit, încurajăm utilizarea licențelor libere, cum ar fi Creative Commons):

    ```text
    GOOD: * [A Very Awesome Book](https://example.org/book.pdf) - Jane Roe (PDF) (CC BY-SA)
    ```

    Licențe acceptate (fără versiune):

    - `CC BY` 'Creative Commons attribution'
    - `CC BY-NC` 'Creative Commons non-commercial'
    - `CC BY-SA` 'Creative Commons share-alike'
    - `CC BY-NC-SA` 'Creative Commons non-commercial, share-alike'
    - `CC BY-ND` 'Creative Commons no-derivatives'
    - `CC BY-NC-ND` 'Creative Commons non-commercial, no-derivatives'
    - `GFDL` 'Gnu Free Documentation License'

#### Adăugarea unei note despre licență (pas cu pas)

Atunci când o resursă este distribuită sub o licență liberă/deschisă, adăugați o scurtă notă despre licență între paranteze după nota de format. Urmați acești pași:

1. Confirmați licența pe pagina resursei.
   - Căutați în footer-ul site-ului, pe pagina „About” sau în secțiunea LICENSE/Legal.
   - Adăugați note despre licență doar pentru licențe libere/deschise (vedeți lista acceptată mai sus). Nu adăugați note precum „All Rights Reserved”.
2. Normalizați șirul licenței la unul dintre codurile scurte acceptate fără număr de versiune.
   - Exemple: „Creative Commons Attribution 4.0” → `CC BY`; „CC BY-SA 3.0” → `CC BY-SA`; „GNU Free Documentation License” → `GFDL`.
3. Plasați licența după format(e) și înaintea oricăror alte note.
   - Format unic:
     ```markdown
     * [A Very Awesome Book](https://example.org/book.pdf) - Jane Roe (PDF) (CC BY-SA)
     ```
   - Formate multiple:
     ```markdown
     * [Awesome Guide](https://example.org/) - Jane Roe (HTML, PDF) (CC BY)
     ```
   - Cu o notă adițională (de ex., archived sau in process):
     ```markdown
     * [Old but Gold](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) (CC BY) *( :card_file_box: archived)*
     ```
4. Dacă ediții/formate diferite au licențe diferite, listați-le ca elemente separate și notați licența corectă pentru fiecare intrare.
5. Dacă nu sunteți sigur, adăugați un comentariu în PR explicând de ce credeți că resursa este sub o licență liberă și unde ați găsit informația.


### Ordine alfabetică

- Când există titluri multiple care încep cu aceeași literă, ordonați-le după a doua literă și așa mai departe. De exemplu: `aa` vine înainte de `ab`.
- `one two` vine înainte de `onetwo`

Dacă vedeți un link plasat greșit, verificați mesajul de eroare al linter-ului pentru a ști care linii trebuie interschimbate.


### Note

Deși elementele de bază sunt relativ simple, există o mare diversitate în resursele pe care le listăm. Iată câteva note despre cum gestionăm această diversitate.


#### Metadate

Listele noastre oferă un set minim de metadate: titluri, URL-uri, creatori, platforme și note de acces.


##### Titluri

- Fără titluri inventate. Încercăm să preluăm titlurile de la resursele în sine; contribuabilii sunt avertizați să nu inventeze titluri sau să le editeze dacă se poate evita. O excepție este pentru lucrările vechi; dacă sunt de interes istoric, un an între paranteze adăugat la titlu îi ajută pe utilizatori să decidă dacă le interesează.
- Fără titluri TOT CU MAJUSCULE. De obicei, capitalizarea titlurilor este potrivită, dar dacă există îndoieli folosiți capitalizarea de pe sursă.
- Fără emoji-uri.


##### URL-uri

- Nu permitem URL-uri scurtate.
- Codurile de urmărire (tracking) trebuie eliminate din URL.
- URL-urile internaționale trebuie escape-uite. Bara browser-ului le afișează de obicei în Unicode, dar folosiți copy-paste.
- URL-urile securizate (`https`) sunt întotdeauna preferate față de cele nesecurizate (`http`) acolo unde HTTPS este disponibil.
- Nu ne plac URL-urile care duc la pagini care nu găzduiesc resursa listată, ci redirecționează în altă parte.


##### Creatori

- Dorim să credităm creatorii resurselor gratuite acolo unde este cazul, inclusiv traducătorii!
- Pentru lucrările traduse, autorul original trebuie creditat. Recomandăm folosirea [MARC relators](https://loc.gov/marc/relators/relaterm.html) pentru a credita creatori care nu sunt autori, ca în acest exemplu:

    ```markdown
    * [A Translated Book](http://example.com/book.html) - John Doe, `trl.:` Mike The Translator
    ```

    aici, notația `trl.:` folosește codul MARC pentru "translator".
- Folosiți virgula `,` pentru a delimita fiecare element din lista de autori.
- Puteți scurta listele de autori cu "`et al.`".
- Nu permitem linkuri pentru Creatori.
- Pentru lucrări compilate sau remixate, "creatorul" poate necesita o descriere. De exemplu, cărțile „GoalKicker” sau „RIP Tutorial” sunt creditate ca "`Compiled from StackOverflow documentation`".
- Nu includem titluri onorifice precum "Prof." sau "Dr." în numele creatorilor.


##### Cursuri cu durată limitată și trial-uri

- Nu listăm lucruri pe care va trebui să le eliminăm în șase luni.
- Dacă un curs are o perioadă de înscriere limitată sau o durată limitată, nu îl vom lista.
- Nu putem lista resurse care sunt gratuite doar pentru o perioadă limitată.


##### Platforme și note de acces

- Cursuri. Mai ales pentru listele noastre de cursuri, platforma este o parte importantă a descrierii resursei. Acest lucru deoarece platformele de cursuri au facilități și modele de acces diferite. Deși, de obicei, nu vom lista o carte care necesită înregistrare, multe platforme de cursuri au facilități care nu funcționează fără un cont. Exemple de platforme: Coursera, EdX, Udacity și Udemy. Când un curs depinde de o platformă, numele platformei trebuie listat între paranteze.
- YouTube. Avem multe cursuri care constau din playlist-uri YouTube. Nu listăm YouTube ca platformă; încercăm să listăm creatorul YouTube, care este adesea o sub-platformă.
- Videoclipuri YouTube. De obicei nu legăm la videoclipuri YouTube individuale decât dacă au mai mult de o oră și sunt structurate ca un curs sau tutorial. Dacă este cazul, menționați acest lucru în descrierea PR-ului.
- Fără linkuri scurtate (ex. youtu.be/xxxx)!
- Leanpub. Leanpub găzduiește cărți cu modele de acces variate. Uneori o carte poate fi citită fără înregistrare; alteori este necesar un cont Leanpub pentru acces gratuit. Având în vedere calitatea și fluiditatea modelelor Leanpub, permitem listarea acestora cu nota de acces `*(Leanpub account or valid email requested)*`.


#### Genuri

Prima regulă în a decide în ce listă intră o resursă este să vedeți cum se descrie resursa. Dacă se numește carte, atunci probabil este o carte.


##### Genuri pe care nu le listăm

Din cauza vastității Internetului, nu includem în listele noastre:

- bloguri
- postări de blog
- articole
- site-uri web (cu excepția celor care găzduiesc MULTE elemente pe care le listăm).
- videoclipuri care nu sunt cursuri sau screencast-uri.
- capitole de carte
- mostre teaser din cărți
- canale IRC sau Telegram
- Slack-uri sau liste de discuții

Listele noastre pentru programare competitivă nu sunt la fel de stricte în privința acestor excluderi. Domeniul repo-ului este determinat de comunitate; dacă doriți să propuneți o schimbare sau o adăugare la domeniu, folosiți un issue.


##### Cărți vs. Alte materiale

Nu suntem foarte pretențioși cu privire la ce înseamnă o carte. Iată câteva atribute care pot semnala că o resursă este o carte:

- are un ISBN (International Standard Book Number)
- are un Cuprins (Table of Contents)
- oferă o versiune descărcabilă, în special fișiere ePub.
- are ediții
- nu depinde de conținut interactiv sau videoclipuri
- încearcă să acopere un subiect în mod cuprinzător
- este autoconținută

Există multe cărți pe care le listăm care nu au aceste atribute; depinde de context.


##### Cărți vs. Cursuri

Uneori acestea pot fi greu de distins!

Cursurile au adesea manuale asociate, pe care le-am lista în listele de cărți. Cursurile au prelegeri, exerciții, teste, note sau alte materiale didactice. O singură prelegere sau un singur videoclip nu este un curs. Un PowerPoint nu este un curs.


##### Tutoriale interactive vs. Alte materiale

Dacă poți printa conținutul și acesta își păstrează esența, nu este un Tutorial Interactiv.


### Automatizare

- Aplicarea regulilor de formatare este automatizată prin [GitHub Actions](https://github.com/features/actions) folosind [fpb-lint](https://github.com/vhf/free-programming-books-lint) (vezi [`.github/workflows/fpb-lint.yml`](../.github/workflows/fpb-lint.yml))
- Validarea URL-urilor folosește [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- Pentru a declanșa validarea URL-urilor, împingeți un commit care conține în mesajul commit-ului `check_urls=file_to_check`:

    ```properties
    check_urls=free-programming-books.md free-programming-books-en.md
    ```

- Puteți specifica mai mult de un fișier pentru verificare, separate printr-un spațiu.
- Dacă specificați mai multe fișiere, rezultatul build-ului se bazează pe rezultatul ultimului fișier verificat. Trebuie să fiți conștienți că puteți obține build-uri verzi din această cauză, deci inspectați jurnalul de build la sfârșitul Pull Request-ului făcând click pe "Show all checks" -> "Details".


### Corectarea erorilor de linter RTL/LTR

Dacă rulați RTL/LTR Markdown Linter (pe fișiere `*-ar.md`, `*-he.md`, `*-fa.md`, `*-ur.md`) și vedeți erori sau avertismente:

- **Cuvinte LTR** (ex. “HTML”, “JavaScript”) în text RTL: adăugați `&rlm;` imediat după fiecare segment LTR;
- **Simboluri LTR** (ex. “C#”, “C++”): adăugați `&lrm;` imediat după fiecare simbol LTR;

#### Exemple

**RĂU**
```html
<div dir="rtl" markdown="1">
* [كتاب الأمثلة في R](URL) - John Doe (PDF)
</div>
```
**BINE**
```html
<div dir="rtl" markdown="1">
* [كتاب الأمثلة في R&rlm;](URL) - John Doe&rlm; (PDF)
</div>
```
---
**RĂU**
```html
<div dir="rtl" markdown="1">
* [Tech Podcast - بودكاست المثال](URL) – Ahmad Hasan, محمد علي
</div>
```
**BINE**
```html
<div dir="rtl" markdown="1">
* [Tech Podcast - بودكاست المثال](URL) – Ahmad Hasan,&rlm; محمد علي
</div>
```
---
**RĂU**
```html
<div dir="rtl" markdown="1">
* [أساسيات C#](URL)
</div>
```
**BINE**
```html
<div dir="rtl" markdown="1">
* [أساسيات C#&lrm;](URL)
</div>
```
