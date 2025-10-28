*[Llegiu això en altres idiomes][translations-list-link]*


<!----><a id="contributor-license-agreement"></a>
## Acord de llicència

En contribuir, accepteu la [LLICÈNCIA][license] d'aquest repositori.


<!----><a id="contributor-code-of-conduct"></a>
## Codi de Conducta com a Col·laborador

En contribuir, accepta respectar el [Codi de Conducta][coc] ([traduccions / altres idiomes][translations-list-link]) present al repositori.


<!----><a id="in-a-nutshell"></a>
## Breu resum

1. "Un enllaç per descarregar fàcilment un llibre" no sempre és un enllaç a un llibre gratuït. Si us plau, contribuïu només amb contingut gratuït. Assegureu-vos que s'ofereixi gratuït. No s'accepten enllaços a pàgines que requereixin adreces de correu electrònic per a l'obtenció de llibres, però sí que donem la benvinguda a aquells llistats que així se sol·licitin.

2. No cal conèixer Git: si vau trobar una mica d'interès que *no estigui ja en aquest repositori*, tingueu el gust d'obrir una [Issue][issues] amb la vostra proposta d'enllaços.
    - Si ja maneja Git, feu un Fork del repositori i envieu la vostra contribució mitjançant Pull Request (PR).

3. Disposa de 6 categories. Seleccioneu aquell llistat que cregueu convenient segons:

    - *Llibres* : PDF, HTML, ePub, un recurs allotjat a gitbook.io, un repositori Git, etc.
    - *Cursos* : Un curs és aquell material d'aprenentatge que no és un llibre. [Això és un curs](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Tutorials interactius* : Un lloc web es considera interactiu si permet a l'usuari escriure codi o ordres i avaluar-ne el resultat ("avaluar" no significa "obtenir" una qualificació"). Per exemple: [Proveu Haskell](http://tryhaskell.org), [Proveu GitHub](http://try.github.io).
    - *Playgrounds* : es tracten de llocs en línia interactius, jocs o programari d'escriptori que té com a finalitat aprendre programació. Permeten escriure, compiar (o executar), i compartir parts de codi font. Sovint ofereixen la possibilitat de fer bifurcacions i embrutar-se les mans jugant amb el codi generat fins dit instant.
    - *Podcasts i Screencasts* : Són aquelles retransmissions gravades ja sigui en àudio i/o en vídeo, respectivament.
    - *Conjunts de problemes & Programació competitiva* : Es tracta d'un lloc web o programari que permeti avaluar les seves habilitats de programació resolent problemes simples o complexos, amb revisió de codi o sense, amb o sense comparar els resultats amb altres usuaris.

4. Assegureu-vos de seguir la [guia de pautes que mostrem a continuació][guidelines] així com de respectar el [format Markdown][formatting] dels fitxers.

5. GitHub Actions executarà proves per assegurar-se que **les llistes estiguin ordenades alfabèticament** i que **se segueixi aquesta normalització de format**. **Assegureu-vos** de verificar que els canvis passin totes aquestes comprovacions de qualitat.


<!----><a id="guidelines"></a>
### Pautes
- Reviseu si el llibre és gratuït. Feu-ho les vegades que considereu necessàries. Ajudeu els administradors comentant a les PR per què creu que el llibre s'ofereix gratis o és valuós.
- No s'accepten fitxers allotjats a Google Drive, Dropbox, Mega, Scribd, Issuu o altres plataformes d'emmagatzematge i/o descàrrega similars.
- Inseriu els enllaços ordenats alfabèticament, tal com es descriu [més avall](#alphabetical-order).
- Utilitzeu l'enllaç que apunti a la font més fidedigna. Això és, el lloc web de l'autor és millor que el de l'editor i aquest millor que un de tercers.
    - No utilitzeu serveis d'emmagatzematge al núvol. Això inclou, encara que sense limitar, enllaços a Dropbox i Google Drive.
- És sempre preferible l'ús d'enllaços amb protocol https en comptes d'http si tots dos fan referència al mateix domini i serveixen el mateix contingut.
- Als dominis arrel, elimineu la barra inclinada del final: `http://example.com` en lloc de `http://example.com/`.
- Utilitzeu preferentment la forma curta dels hipervincles: `http://example.com/dir/` és millor que `http://example.com/dir/index.html`.
    - No s'admeten escurçadors d'enllaços URL.
- En general, es prefereix l'enllaç "actual" sobre el de "versió": `http://example.com/dir/book/current/` és més assequible que `http://example.com/dir/book/v1.0.0/index.html`.
- Si en un enllaç es troba amb algun problema de certificats, ja sigui caducat, autosignat o de qualsevol altre tipus:
    1. **Reemplaceu-lo** amb el vostre anàleg `http` si fos possible (perquè acceptar excepcions pot ser complicat en dispositius mòbils).
    2. `Mantingueu-lo` si no hi ha versió `http` però l'enllaç encara és accessible a través de `https` afegint una excepció al navegador o ignorant l'advertència.
    3. Elimineu -lo en qualsevol altre cas.
- Si hi ha un mateix enllaç amb diversos formats, annexeu enllaços a part amb una nota sobre cada format.
- Si un recurs existeix a diferents llocs d'Internet:
    - Utilitzeu aquella font més fidedigna (el que significa que el lloc web del mateix autor és més assequible que el lloc web de l'editor i alhora aquest és millor que una font de tercers).
    - Si apunten a diferents edicions i considera que aquestes edicions són prou dispars perquè valgui la pena conservar-les, afegiu per separat un nou enllaç fent al·lusió a cada edició. Adreceu-vos a l'[Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) si voleu contribuir a la discussió sobre el formateig que han de seguir aquests registres.

- És preferible realitzar commits atòmics (un commit per cada addició/eliminació/modificació) davant d'uns amb més calat. No cal fer un esquaix de tots abans d'enviar una PR. (No aplicarem mai aquesta regla, ja que només és una qüestió de conveniència per a qui manté el projecte).
- Si es tracta d'un llibre més antic, incloeu la data de publicació dins del títol.
- Incloeu el nom o noms d'autor/s quan correspongui. Pot valdre's de "`et al.`" per escurçar aquesta enumeració d'autors.
- Si el llibre no està acabat i encara s'hi està treballant, afegiu l'anotació de "`in process`", tal com es descriu [a continuació][in_process].
- En el cas que decidiu recuperar un recurs usant serveis com [*Internet Archive's Wayback Machine*](https://web.archive.org), anexeu l'anotació "`archived`" (en consonància amb l'idioma) tal com es descriu [a continuació][archived]. Utilitzeu com a millor versió aquella que sigui la més recent i completa.
- Si se sol·licita una adreça de correu electrònic o configuració de compte abans d'habilitar la descàrrega, afegiu entre parèntesis aquestes notes i en consonància amb el idioma. Per exemple: (*es sol·licita* email, no requerit...).


<!----><a id="formatting"></a>
### Format estandarditzat

- Com podreu observar, els llistats tenen `.md` com a extensió de fitxer. Intenteu aprendre la sintaxi [Markdown][markdown_guide]. És força senzill d'aprendre!
- Aquests llistats comencen amb una Taula de Continguts (TOC). Aquest índex permet enumerar i vincular totes les seccions i subseccions en què es classifica cada recurs. Mantingueu-ho també en ordre alfabètic.
- Les seccions utilitzen capçaleres de nivell 3 (`###`) i les subseccions de nivell 4 (`####`).

La idea és tenir:

- `2` línies buides entre el darrer enllaç d'una secció i el títol de la secció següent.
- `1` línia buida entre la capçalera i el primer enllaç duna determinada secció.
- `0` línies en blanc entre els diferents enllaços.
- `1` línia en blanc al final de cada fitxer .md.

Exemple:

```text
* [Un llibre increïble](http://example.com/example.html)
                                (línia en blanc)
                                (línia en blanc)
### Secció d'exemple
                                (línia en blanc)
* [Un altre llibre fascinant](http://example.com/book.html)
* [Un altre llibre més](http://example.com/other.html)
```

- Ometeu els espais entre `]` i `(`:

    ```text
    INCORRECTE: * [Un altre llibre fascinant] (http://example.com/book.html)
    CORRECTE  : * [Un altre llibre fascinant](http://example.com/book.html)
    ```

- Si al registre decideix incloure l'autor, empreu - (un guió envoltat d'espais simples) com a separador:

    ```text
    INCORRECTE: * [Un llibre senzillament fabulós](http://example.com/book.html)- John Doe
    CORRECTE  : * [Un llibre senzillament fabulós](http://example.com/book.html) - John Doe
    ```

- Poseu un sol espai entre l'enllaç al contingut i el format:

    ```text
    INCORRECTE: * [Un llibre molt interessant](https://example.org/book.pdf)(PDF)
    CORRECTE  : * [Un llibre molt interessant](https://example.org/book.pdf) (PDF)
    ```

- L'autor s'anteposa al format:
    ```text
    INCORRECTE: * [Un llibre molt interessant](https://example.org/book.pdf)- (PDF) Jane Roe
    CORRECTE  : * [Un llibre molt interessant](https://example.org/book.pdf) - Jane Roe (PDF)
    ```

- Múltiples formats:

    ```text
    INCORRECTE: * [Un altre llibre interessant](http://example.com/) - John Doe (HTML)
    INCORRECTE: * [Un altre llibre interessant](https://downloads.example.org/book.html) - John Doe (lloc de descàrrega)
    CORRECTE  : * [Altre llibre interessant](http://example.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.example.org/book.
    ```

- Incloeu l'any de publicació com a part del títol dels llibres més antics:

    ```text
    INCORRECTE: * [Un llibre força especial](https://example.org/book.html) - Jane Roe - 1970
    CORRECTE  : * [Un llibre força especial (1970)](https://example.org/book.html) - Jane Roe
    ```

- <a id="in_process"></a>Llibres en procés / encara no acabats:

    ```text
    CORRECTE : * [A punt de ser un llibre fascinant](http://example.com/book2.html) - John Doe (HTML) ( :construction: *en procés
    ```

- <a id="archived"></a>Enllaços arxivats:

    ```text
    CORRECTE : * [Un recurs recuperat a partir de la seva línia de temps](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) *( :card_file_box: arxivat)*
    ```

<!----><a id="alphabetical-order"></a>
### Ordenació alfabètica

- Quan hi ha diversos títols començant per la mateixa lletra, ordeneu per la segona, ... i així consecutivament. Per exemple:
    - `aa` va abans de `ab`.
    - `one two` va abans que `onetwo`.

En qualsevol cas o si per casualitat trobés un enllaç fora de lloc, comproveu el missatge d'error que facilita el nostre linter. Us permetrà saber les línies de codi que heu de intercanviar.


<!----><a id="notes"></a>
### Anotacions

Si bé els conceptes bàsics són relativament simples, hi ha una gran diversitat entre els recursos que enumerem. Aquí hi ha algunes notes sobre com ens ocupem d'aquesta diversitat.


<!----><a id="metadata"></a>
#### Metadades

Les nostres llistes proporcionen un conjunt mínim de metadades: títols, URL, autors, format, plataformes i notes d'accés.


<!----><a id="titles"></a>
#### Títols

- Sense títols inventats: Intentem prendre el text dels propis recursos; s'adverteix als col·laboradors que, si es pot evitar, no inventin títols ni els utilitzin editorialment. Una excepció és per a obres més antigues: si són principalment d'interès històric, un any entre parèntesi adjunt al títol ajuda els usuaris a saber si aquests són interessants.
- Sense títols TOT EN MAJÚSCULES: En general, és apropiat tenir cada primera lletra de paraula en majúscules, però en cas de dubte, useu sempre l'estil tal com ve a la font original.
- Eviteu utilitzar emoticones.


<!----><a id="urls"></a>
##### Adreces URL

- No es permeten escurçadors d'URL per als enllaços.
- Els paràmetres de consulta o codis referents al seguiment o campanyes de màrqueting s'han d'eliminar de la URL.
- Les URL internacionals s'han d'escapar. Les barres del navegador solen representar els caràcters a Unicode, però utilitzeu copiar i enganxar, si us plau; és la forma més ràpida de construir un hiperenllaç vàlid.
- Les URL segures (https) sempre són millor opció davant de les no segures (http).
- No ens agraden les URL que apunten a pàgines web que no allotgin el recurs esmentat, enllaçant al contrari a una altra part.


<!----><a id="creators"></a>
##### Atribucions

- Volem donar crèdit als creadors de recursos gratuïts quan sigui apropiat, fins i tot traductors!

- En el cas d'obres traduïdes, cal acreditar-ho també a l'autor original. Recomanem fer servir [MARC relators](https://loc.gov/marc/relators/relaterm.html) per donar presència a la resta de creadors diferents de l'autor original, tal com es mostra en aquest exemple:

    ```markdown
    * [Un llibre traduït](http://example.com/book-ca.html) - John Doe, `trl.:` Mike Traduce
    ```

    on, l'anotació trl.: inclou el codi MARC relator per a "traductor".
- Utilitzeu comes `,` per separar cada element de la llista d'autors.
- Quan siguin moltes, es pot emprar "`i altres.`" per escurçar aquesta llista.
- No permetem enllaços directes al creador.
- En el cas de recopilacions o obres remesclades, el “creador” pot necessitar una descripció. Per exemple, els llibres de "GoalKicker" o "RIP Tutorial" s'acrediten com "`Creat a partir de la documentació de StackOverflow`" (en anglès: "`Compiled from StackOverflow documentation`").


<!----><a id="platforms-and-access-notes"></a>
##### Plataformes i notes d'accés

- Cursos. Especialment per a les nostres llistes de cursos, la plataforma és una part important de la descripció del recurs. Això és perquè les plataformes de cursos tenen diferents prestacions i models daccés. Si bé generalment no incloem un llibre que requereix de registre previ, moltes plataformes de cursos tenen la casualitat de no funcionar sense cap tipus de compte. Un exemple de plataformes de cursos podrien ser: Coursera, EdX, Udacity i Udemy. Quan un curs depèn d'una plataforma, el nom de la plataforma ha d'aparèixer entre parèntesis.
- YouTube. Tenim molts cursos que consisteixen en llistes de reproducció de YouTube. No incloem YouTube com a plataforma, sinó que intentem incloure el creador de YouTube, el quin és sovint una sub-plataforma en si.
- Vídeos de YouTube. En general, no vinculem vídeos individuals de YouTube a no ser que tinguin més d'una hora de durada i estiguin estructurats com un curs
o un tutorial.
- Leanpub. Leanpub allotja llibres amb una àmplia varietat de models daccés. De vegades, un llibre es pot llegir sense enregistrar-se; en altres, un llibre requereix un compte Leanpub per tenir accés gratuït. Atesa la qualitat dels llibres i la barreja i fluïdesa dels models d'accés Leanpub, donem validesa a aquests darrers annexant la nota d'accés: `*(compte Leanpub o email vàlid requerit)*`.


<!----><a id="genres"></a>
#### Gèneres

La primera regla per decidir a quin llistat encaixa un determinat recurs és veure com es descriu a si mateix. Si per exemple es retrata a si mateix com un llibre, llavors potser és que ho sigui.


<!----><a id="genres-we-dont-list"></a>
##### Gèneres no acceptats

Ja que a Internet podem trobar una varietat infinita de recursos, no incloem al nostre registre:

- Blogs
- Publicacions de blogs
- Articles
- Llocs web (excepte aquells que allotgin MOLTS elements que puguem incloure als llistats).
- Vídeos que en sean cursos o screencasts (retrasmisiones)
- Capítols solts a llibres
- Mostres o introduccions de llibres
- Canals/grups d'IRC, Telegram...
- Canals/Sales Slack... o llistes de correu

El [llistat on incloem llocs o programari de programació competitiva][programming_playgrounds_list] no és tan restrictiu. L'abast d'aquest repositori el determina la comunitat; si voleu suggerir un canvi o estendre l'abast, utilitzeu els [issues][issues] per registrar aquest suggeriment.


<!----><a id="books-vs-other-stuff"></a>
##### Llibres vs. Un altre Material

No som tan exquisits amb el que considerem com a llibre. A continuació, es mostren algunes propietats que un recurs pugui encaixar com a llibre:

- Té un ISBN (número de llibre estàndard internacional)
- Té una Taula de Continguts (TOC)
- S'ofereix una versió per a baixar electrònica, especialment ePub.
- té diverses edicions
- no depèn d'un contingut interactiu extra o vídeos
- tracta d'abordar un tema de manera integral
- és autosuficient

Hi ha molts llibres que enumerem els quins no tenen aquests atributs; això pot dependre del context.


<!----><a id="books-vs-courses"></a>
##### Llibres vs. Cursos

De vegades distingir pot ser dificultós!

Els cursos solen tenir llibres de text associats, que inclouríem a les nostres llistes de llibres. A més, els cursos tenen conferències, exercicis, proves, apunts o altres ajuts didàctiques. Una sola conferència o vídeo per si sol no és un curs. Una presentació de PowerPoint tampoc pot ser catalogat com a curs.


<!----><a id="interactive-tutorials-vs-other-stuff"></a>
##### Tutorials interactius vs. Un altre Material

Si és possible imprimir-lo i conservar-ne l'essència, no és un Tutorial Interactiu.


<!----><a id="automation"></a>
### Automatització

- El compliment de les regles de formatat s'automatitza via [GitHub Actions](https://docs.github.com/en/actions) usant [fpb-lint](https://github.com/vhf/free-programming-books-lint) (ver [`.github/workflows/fpb-lint.yml`](../.github/workflows/fpb-lint.yml))
- La validació d'URLs es fa mitjançant [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- Per activar aquesta validació d'URL, envieu un commit que inclogui com a missatge de confirmació `check_urls=fitxer_a_comprovar`:

    ```properties
    check_urls=free-programming-books.md free-programming-books-es_CAT.md
    ```

- Podeu especificar més d'un fitxer a comprovar. Simplement utilitzeu un espai per separar cada entrada.
- Si especifiqueu més d'un fitxer, els resultats obtinguts es basen en l'estat del darrer fitxer verificat. Ha de tenir-ho en compte ja que, per això, pot obtenir falsos positius en finalitzar el procés. Així que després de l'enviament de la Pull Request assegureu-vos d'inspeccionar el registre de compilació fent clic a "Show all checks" -> "Detalls".


[license]: ../LICENSE
[coc]: CODE_OF_CONDUCT-es.md
[translations-list-link]: README.md#translations
[issues]: https://github.com/EbookFoundation/free-programming-books/issues
[formatting]: #formato-normalizado
[guidelines]: #pautas
[in_process]: #in_process
[archived]: #archived
[markdown_guide]: https://guides.github.com/features/mastering-markdown/
[programming_playgrounds_list]: https://github.com/EbookFoundation/free-programming-books/blob/main/more/free-programming-playgrounds.md
