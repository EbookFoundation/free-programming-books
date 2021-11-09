*Leggilo in altre lingue: [Deutsch](CONTRIBUTING-de.md), [English](CONTRIBUTING.md), [Español](CONTRIBUTING-es.md), [Français](CONTRIBUTING-fr.md), **Italiano**, [简体中文](CONTRIBUTING-zh.md), [繁體中文](CONTRIBUTING-zh_TW.md), [فارسی](CONTRIBUTING-fa_IR.md), [Tiếng Việt](CONTRIBUTING-vn.md), [Русский](CONTRIBUTING-ru.md), [Português Brasileiro](CONTRIBUTING-pt_BR.md), [한국어](CONTRIBUTING-ko.md).*

## Accordo di Licenza
Contribuendo tu accetti alla [LICENZA](https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE) di questa repository.

## Codice di Comportamento del Collaboratore
I collaboratori accettano di rispettare il [Codice di Comportamento](https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT-it.md) di questa repository.

## In breve
1. "Un link per scaricare facilmente un libro" non è sempre un link per scaricare un libro *gratuito*. Per favore contribuisci solo con contenuti gratuiti. Assicurati che sia gratuito. Non accettiamo link a pagine che *richiedono* email funzionanti per ottenere il libro, ma diamo il benvenuto agli annunci che li richiedono.
2. Non devi conoscere Git: se trovi qualcosa di interessante che che non è *ancora in questa repo*, apri un [Issue](https://github.com/EbookFoundation/free-programming-books/issues) con il link della risorsa.
    - Se conosci Git, forka questa repository e crea una Pull Request.
3. Abbiamo 5 tipi di liste. Scegli quella giusta:

    - *Libri* : PDF, HTML, ePub, gitbook.io, una Git repo, etc.
    - *Corsi* : Un corso è del materiale gratuito che non è un libro. [Questo è un corso](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Tutorial Interattivi* : Un sito interattivo permette all'utente di scrivere codice o comandi e analizzarne il risultato. esempi: [Try Haskell](http://tryhaskell.org), [Try Github](http://try.github.io).
    - *Podcasts e Screencasts* : Podcasts and screencasts.
    - *Set di problemi & Programmazione competitiva* : Un sito o software che ti permette di valutare le tue skills da programmatore risolvendo problemi semplici o complessi, con o senza la revisione del codice, con o senza la comparazione del risultato con gli altri utenti.

4. Assicurati di seguire le [linee guida qui sotto](#guidelines) e rispettare la [formattazione Markdown](#formatting) dei file.

5. GitHub Actions avvierà dei test per assicurarsi che le tue liste siano ordinate alfabeticamente e formattate correttamente. Assicurati che i tuoi cambiamenti passino il test.

<a name="guidelines"></a>
### Linee guida
- assicurati che il libro sia gratuito. Controlla più volte se necessario. Commentare nella PR il perché pensi che il libro sia gratuito aiuta gli admin.
- non accettiamo file hostati su Google Drive, Dropbox, Mega, Scribd, Issuu e altre piattaforme simili per l'upload dei file
- inserisci i link ordinandoli alfabeticamente. Se sbagli la posizione di un link, riordinalo e invia la PR
- usa il link più "autorevole" per segnalare la risorsa (significa che il sito web dell'autore è migliore del sito web dell'editore, che è migliore di un sito web di terze parti)
    + nessun servizio di file hosting (questo include (ma non è limitato a) link di Dropbox e Google Drive)
- preferisci sempre un link `https` rispetto ad un `http` -- purché si trovino sullo stesso dominio e contengano lo stesso contenuto
- sul dominio di root, elimina il trailing slash (lo slash finale): `http://example.com` invece di `http://example.com/`
- preferisci sempre link più corti: `http://example.com/dir/` è migliore di `http://example.com/dir/index.html`
    + niente link accorciati
- generalmente preferisci il link "current" rispetto al link "version": `http://example.com/dir/book/current/` è migliore di `http://example.com/dir/book/v1.0.0/index.html`
- se un link ha un certificato scaduto/certificato auto-firmato/problemi di SSL o di qualsiasi altro tipo:
  1. *sostituiscilo* con la controparte in `http` se possibile (perché accettare eccezione può essere complicato sui dispositivi mobile).
  2. *lascialo* se non è disponibile alcuna versione in `http` ma la versione `https` è ancora accessibile aggiungendo l'eccezione al browser o ignorando l'avviso.
  3. *rimuovilo* altrimenti.
- se un link esiste in più formati, aggiungi un link separato con una nota riguardante il formato
- se una risorsa è presente in posti differenti su internet
    + usa il link più "autorevole" per segnalare la risorsa (significa che il sito web dell'autore è migliore del sito web dell'editore, che è migliore di un sito web di terze parti)
    + se reindirizzano a edizioni differenti e tu credi che queste edizioni siano abbastanza diverse tra loro da valere la pena di essere tenute, aggiungi un link separato con una nota riguardante ogni edizione (guarda [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) per contribuire alla discussione sulla formattazione.)
- preferisci gli atomic commits (un commit per aggiunta/modifica/eliminazione) rispetto ai grandi commit. Non c'è bisogno di raggruppare i commit per inviarli in una sola PR. (Non applichiamo mai questa regola, è solo per comodità dei moderatori)
- se il libro è più vecchio, includi la data di pubblicazione assieme al titolo.
- includi il nome o i nomi degli autori se è il caso. Puoi accorciare il nome degli autori con "et al."
- se il libro non è ancora finito, e ci stanno ancora lavorando su, aggiungi "in process", come descritto [qui sotto](#in_process). Seleziona sempre l'ultima versione disponibile in questi siti.
- se una risorsa è archiviata usando la Wayback Machine di Internet Archive (o simili), aggiungi la notazione "archived", come descritto [qui sotto](#archived). La versione migliore da utilizzare è quella più recente/completa.
- se è richiesto un indirizzo email o un account per poter scaricare il libro, aggiungilo tra parentesi, esempio: `(email address *requested*, not required)`

<a name="formatting"></a>
### Formattazione
- Tutte le liste sono file `.md`. Prova ad imparare la sintassi [Markdown](https://guides.github.com/features/mastering-markdown/). È semplice!
- Tutte le liste iniziano con un Index. L'idea è di elencare e collegare tutte le sezioni e sottosezioni lì. Mantienila in ordine alfabetico.
- Le sezioni utilizzano il livello 3 di heading (`###`), e le sottosezioni utilizzano il livello 4 di heading (`####`).

L'idea è di avere:
- `2` linee vuote tra l'ultimo link e la nuova sezione.
- `1` linea vuota tra il titolo e il primo link della sezione.
- `0` linee vuote tra due link.
- `1` linea vuota alla fine di ogni file `.md`.

Esempi:

    [...]
    * [An Awesome Book](http://example.com/example.html)
                                    (linea vuota)
                                    (linea vuota)
    ### Esempio
                                    (linea vuota)
    * [Another Awesome Book](http://example.com/book.html)
    * [Some Other Book](http://example.com/other.html)

- Non mettere uno spazio tra `]` e `(`:

```
SCORRETTO : * [Another Awesome Book] (http://example.com/book.html)
CORRETTO: * [Another Awesome Book](http://example.com/book.html)
```

- Se includi gli autori, usa ` - ` (un trattino circondato da spazi singoli):

```
SCORRETTO : * [Another Awesome Book](http://example.com/book.html)- John Doe
CORRETTO: * [Another Awesome Book](http://example.com/book.html) - John Doe
```

- Metti uno spazio tra il link e il formato:

```
SCORRETTO : * [A Very Awesome Book](https://example.org/book.pdf)(PDF)
CORRETTO: * [A Very Awesome Book](https://example.org/book.pdf) (PDF)
```

- Gli autori vanno prima del formato:

```
SCORRETTO : * [A Very Awesome Book](https://example.org/book.pdf)- (PDF) Jane Roe
CORRETTO: * [A Very Awesome Book](https://example.org/book.pdf) - Jane Roe (PDF)
```

- Formati multipli:

```
SCORRETTO : * [Another Awesome Book](http://example.com/)- John Doe (HTML)
SCORRETTO : * [Another Awesome Book](https://downloads.example.org/book.html)- John Doe (download site)
CORRETTO: * [Another Awesome Book](http://example.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
```

- Includi l'anno di pubblicazione nel titolo per i libri più vecchi:

```
SCORRETTO : * [A Very Awesome Book](https://example.org/book.html) - Jane Roe - 1970
CORRETTO: * [A Very Awesome Book (1970)](https://example.org/book.html) - Jane Roe
```

<a name="in_process"></a>
- Libri in sviluppo:

```
CORRETTO: * [Will Be An Awesome Book Soon](http://example.com/book2.html) - John Doe (HTML) (:construction: *in process*)
```

<a name="archived"></a>
- Link archiviato:

```
CORRETTO: * [A Way-backed Interesting Book](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) *(:card_file_box: archived)*
```

### Note

Mentre le basi sono relativamente semplici, c'è una notevole differenza tra le risorse che inseriamo nelle liste. Qui ci sono alcuni appunti su come affrontiamo queste diversità.

#### Metadata

I nostri elenchi forniscono un set minimo di metadati: titoli, URLs, autori, piattaforme e note di accesso.

##### Titoli

- Non inventiamo i titoli. Cerchiamo di prendere i titoli dalla risorsa originale; i contributori sono invitati a non inventare titoli o usarli editorialmente se questo può essere evitato. Un'eccezione è per i libri più vecchi; se sono principalmente di interesse storico, l'anno tra parentesi inserito nel titolo aiuta gli utenti a capire se sono interessati a quella risorsa.
- Niente titoli completamente in MAIUSCOLO. Di solito il title case è appropriato, ma in caso di dubbio usa le maiuscole utilizzate nella fonte.

##### URLs

- Non per mettiamo di rimpicciolire il link con gli appositi strumenti.
- Il codice di tracciamento deve essere rimosso dall'URL.
- Gli URL internazionali devono essere evitati. Le barre del browser in genere li rendono in Unicode, ma usa copia e incolla, per favore.
- I link sicuri (https) sono preferibili al posto dei link non sicuri (http), dove l'https è stato implementato.
- Non ci piacciono gli URL che reindirizzano in una pagina che non hosta la risorsa, ma invece reindirizza altrove.

##### Autori

- Vogliamo dare i crediti agli autori ove appropriato, anche ai traduttori!
- Per i lavori tradotti, l'autore originale dovrebbe essere incluso.
- Non permettiamo collegamenti per gli autori.
- Per le compilation o remix, il "creatore" potrebbe aver bisogno di una descrizione. Ad esempio, i libri "GoalKicker" o "RIP Tutorial" sono accreditati come "Compiled from StackOverflow documentation"

##### Piattaforme e note di accesso

- Corsi. Specialmente per la nostra liste dei corsi, la piattaforma è una parte importante della descrizione. Questo perché le varie piattaforme di corsi hanno diverse affordance e metodi di accesso. Mentre solitamente i libri non hanno bisogno di un account per essere letti, molte piattaforme di corsi ne hanno bisogno. Esempi di piattaforme di corsi sono Coursera, EdX, Udacity e Udemy. Quando un corso dipende dalla piattaforma, il suo nome dovrebbe essere incluso tra parentesi.
- YouTube. Abbiamo molti corsi che consistono in playlist di YouTube. Non consideriamo YouTube come piattaforma, cerchiamo di inserire il creatore del corso, che è spesso una sotto-piattaforma.
- Video YouTube. Solitamente non accettiamo singoli video YouTube, a meno che non siano più lunghi di un'ora e che siano strutturati come un corso o un tutorial.
- Leanpub. Leanpub ospita libri con varie modalità di accesso. Alcune volte i libri possono essere letti senza l'obbligo di registrazione; alcune volte è necessario creare un account gratuito su Leanpub. Data la qualità dei libri e la commistione e fluidità dei modelli di accesso Leanpub, consentiamo di elencare questi ultimi con la nota di accesso *(Leanpub account or valid email requested)*

#### Generi

La prima regola è decidere a quale lista appartiene di più una risorsa. Se si definisce un libro, allora forse è un libro.

##### Generi che non accettiamo

Essendo che internet è vasto, noi non accettiamo:

- blog
- blog posts
- articoli
- siti web (ad eccezione di quelli che ospitano MOLTI articoli che elenchiamo.)
- video che non sono corsi o screencasts.
- capitoli dei libri
- teaser dei libri
- IRC o canali Telegram
- Slacks o newsletter

I nostri elenchi di programmi competitivi non sono così severi riguardo a queste esclusioni. L'ambito del repo è determinato dalla comunità; se desideri suggerire una modifica o un'aggiunta all'ambito, utilizza un problema per suggerire.


##### Libri vs. Altro

Non siamo così esigenti riguardo al libro. Ecco alcuni attributi che indicano che una risorsa è un libro:

- ha un ISBN (International Standard Book Number)
- ha una tabella dei contenuti
- è offerta una versione scaricabile, specialmente ePub
- ha un'editizone
- non dipende da contenuti interattivi o video
- cerca di coprire in modo completo l'argomento
- è autonomo

Ci sono molti libri che abbiamo aggiunto che però non hanno questi attributi; dipende dal contesto.


##### Libri vs. Corsi

A volte questi possono essere difficili da distinguere!

I corsi hanno spesso libri di testo associati, che elencheremo nei nostri elenchi di libri. I corsi prevedono lezioni, esercitazioni, test, appunti o altri supporti didattici. Una singola lezione o video di per sé non è un corso. Un powerpoint non è un corso.


##### Tutorial interattivi vs. Altro

Se riesci a stamparlo e conservarne l'essenza, non è un tutorial interattivo.


### Automazione

- L'applicazione delle regole di formattazione è automatizzata tramite [GitHub Actions](https://github.com/features/actions) usando [fpb-lint](https://github.com/vhf/free-programming-books-lint) (guarda [.github/workflows/fpb-lint.yml](.github/workflows/fpb-lint.yml))
- La validazione dell'URL usa [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- Per attivare la convalida dell'URL, invia un commit che includa un messaggio di commit contenente `check_urls=file_to_check`:

```
check_urls=free-programming-books.md free-programming-books-en.md
```

- È possibile specificare più di un file da controllare, utilizzando un singolo spazio per separare ogni voce.
- Se specifichi più di un file, i risultati della build si basano sul risultato dell'ultimo file controllato. Dovresti essere consapevole che potresti ottenere il passaggio di build verdi a causa di ciò, quindi assicurati di ispezionare il registro di build alla fine della richiesta pull facendo clic su "Show all checks" -> "Details".
