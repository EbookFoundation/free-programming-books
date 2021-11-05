*Basahin ito sa ibang mga wika: [Deutsch](CONTRIBUTING-de.md), [Français](CONTRIBUTING-fr.md), **Filipino**, [Español](CONTRIBUTING-es.md), [English](CONTRIBUTING.md), [Indonesia](CONTRIBUTING-id.md),[简体中文](CONTRIBUTING-zh.md), [繁體中文](CONTRIBUTING-zh_TW.md), [Português (BR)](CONTRIBUTING-pt_BR.md), [فارسی](CONTRIBUTING-fa_IR.md), [Tiếng Việt](CONTRIBUTING-vn.md), [Русский](CONTRIBUTING-ru.md), [한국어](CONTRIBUTING-ko.md).*

## Kasunduan sa Lisensya ng Contributor
Sa pamamagitan ng pag-aambag sumasang-ayon ka sa [LICENSE](https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE) ng repositoryong ito.

## Kodigo ng Pag-uugali ng Contributor
Sa pamamagitan ng pag-aambag sumasang-ayon kang igalang ang [Code of Conduct](https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT-fil.md) ng repositoryong ito.

## Sa maikling sabi
1. "Ang isang link para madaling mag-download ng libro" ay hindi palaging isang link sa isang *libre* na libro. Mangyaring mag-ambag lamang ng libreng nilalaman. Tiyaking libre ito. Hindi kami tumatanggap ng mga link sa mga pahina na *nangangailangan* ng gumaganang mga email address upang makakuha ng mga aklat, ngunit malugod naming tinatanggap ang mga listahan na humihiling sa kanila.
2. Hindi mo kailangang malaman ang Git: kung nakakita ka ng isang bagay na interesado na *wala pa sa repo na ito*, mangyaring magbukas ng [Issue](https://github.com/EbookFoundation/free-programming-books/issues) kasama ang iyong mga proposisyon ng link.
    - Kung alam mo ang Git, mangyaring Fork ang repo at magpadala ng mga Pull Request (PR).
3. Mayroon kaming 5 uri ng mga listahan. Piliin ang tama:

    - *Mga libro* : PDF, HTML, ePub, isang site na nakabatay sa gitbook.io, a Git repo, etc.
    - *Kurso* : Ang kurso ay isang materyal sa pag-aaral na hindi isang libro. [This is a course](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Mga Interactive na Tutorial* : Isang interactive na website na nagbibigay-daan sa user na mag-type ng code o command at suriin ang resulta (sa pamamagitan ng "suriin" hindi namin ibig sabihin ay "grado"). e.g.: [Try Haskell](http://tryhaskell.org), [Try Github](http://try.github.io).
    - *Mga Podcast at Screencast* : Mga podcast at screencast.
    - *Mga Set ng Problema at Kompetisyon sa Programming* : Isang website o software na nagbibigay-daan sa iyong tasahin ang iyong mga kasanayan sa programming sa pamamagitan ng paglutas ng mga simple o kumplikadong problema, mayroon man o walang code review, mayroon man o walang paghahambing ng mga resulta sa ibang mga user.

4. Siguraduhing sundin ang [guidelines below](#guidelines) at igalang ang [Markdown formatting](#formatting) ng mga file.

5. Ang GitHub Actions ay magpapatakbo ng mga pagsubok upang matiyak na ang iyong mga listahan ay naka-alpabeto at sinusunod ang mga panuntunan sa pag-format. Siguraduhing suriin na ang iyong mga pagbabago ay pumasa sa mga pagsubok.

<a name="guidelines"></a>
### Mga Alituntunin
- siguraduhin na ang isang libro ay libre. I-double check kung kinakailangan. Nakakatulong ito sa mga admin kung magkomento ka sa PR kung bakit sa tingin mo ay libre ang libro.
- hindi kami tumatanggap ng mga file na naka-host sa Google Drive, Dropbox, Mega, Scribd, Issuu at iba pang katulad na mga platform sa pag-upload ng file
- ipasok ang iyong mga link sa alphabetical order. Kung makakita ka ng maling lugar na link, mangyaring muling ayusin ito at magsumite ng PR
- gamitin ang link na may pinakamakapangyarihang pinagmulan (ibig sabihin ang website ng may-akda ay mas mahusay kaysa sa website ng editor, na mas mahusay kaysa sa isang third party na website)
    + walang mga serbisyo sa pagho-host ng file (kabilang dito ang (ngunit hindi limitado sa) mga link ng Dropbox at Google Drive)
- palaging mas gusto ang isang link na `https` kaysa sa isang link na `http` -- hangga't sila ay nasa parehong domain at naghahatid ng parehong nilalaman
- sa mga root domain, tanggalin ang trailing slash: `http://example.com` sa halip na `http://example.com/`
- palaging mas gusto ang pinakamaikling link: `http://example.com/dir/` ay mas mabuti kaysa sa `http://example.com/dir/index.html`
    + walang URL shortener link
- kadalasang mas gusto ang "kasalukuyang" link kaysa sa "bersyon": `http://example.com/dir/book/current/` ay mas mabuti kaysa sa `http://example.com/dir/book/v1.0.0/index.html`
- kung ang isang link ay nag-expire na certificate/self-signed certificate/SSL isyu ng anumang iba pang uri:
  1. *palitan ito* ng katapat nitong `http` kung maaari (dahil ang pagtanggap ng mga pagbubukod ay maaaring kumplikado sa mga mobile device).
  2. *iwanan ito* kung walang available na bersyon ng `http` ngunit maa-access pa rin ang link sa pamamagitan ng `https` sa pamamagitan ng pagdaragdag ng exception sa browser o hindi papansinin ang babala.
  3. *tanggalin mo* kung hindi.
- kung mayroong isang link sa maraming format, magdagdag ng isang hiwalay na link na may tala tungkol sa bawat format
- kung mayroong isang mapagkukunan sa iba't ibang lugar sa Internet
    + gamitin ang link na may pinaka-makapangyarihang pinagmulan (ibig sabihin ang website ng may-akda ay mas mahusay kaysa sa website ng editor ay mas mahusay kaysa sa third party na website)
    + kung nagli-link ang mga ito sa iba't ibang mga edisyon, at hinuhusgahan mo na ang mga edisyong ito ay sapat na naiiba upang maging sulit na panatilihin ang mga ito, magdagdag ng hiwalay na link na may tala tungkol sa bawat edisyon (see [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) upang mag-ambag sa talakayan sa pag-format.)
- mas gusto ang atomic commit (one commit by addition/deletion/modification) higit sa mas malalaking commit. Hindi na kailangang i-squash ang iyong mga commit bago magsumite ng PR. (Hindi namin kailanman ipapatupad ang panuntunang ito dahil ito ay isang bagay lamang ng kaginhawahan para sa mga nagpapanatili)
- kung mas luma ang aklat, isama ang petsa ng publikasyon na may pamagat.
- isama ang pangalan ng may-akda o mga pangalan kung saan naaangkop. Maaari mong paikliin ang mga listahan ng may-akda gamit ang "`et al.`"
- kung ang aklat ay hindi pa tapos, at ginagawa pa rin, idagdag ang "in process" notation, gaya ng inilarawan [below.](#in_process)
- kung ang isang mapagkukunan ay naibalik gamit ang Wayback Machine ng Internet Archive (o katulad), idagdag ang "naka-archive" na notation, tulad ng inilarawan [below](#archived). Ang pinakamahusay na mga bersyon na gagamitin ay bago at kumpleto.
- kung humiling ng email address o pag-setup ng account bago i-enable ang pag-download, magdagdag ng mga tala na naaangkop sa wika sa mga panaklong, hal.: `(email address *requested*, not required)`

<a name="formatting"></a>
### Pag-format
- Ang lahat ng mga listahan ay `.md` files. Subukang matuto [Markdown](https://guides.github.com/features/mastering-markdown/) syntax. Simple lang!
- Ang lahat ng mga listahan ay nagsisimula sa isang Index. Ang ideya ay ilista at i-link ang lahat ng seksyon at subsection doon. Panatilihin ito sa alpabetikong pagkakasunud-sunod.
- Gumagamit ang mga seksyon ng antas 3 na mga heading (`###`), at ang mga subsection ay level 4 na mga heading (`####`).

The idea is to have:
- `2` walang laman na linya sa pagitan ng huling link at bagong seksyon.
- `1` walang laman na linya sa pagitan ng heading.
- `0` walang laman na linya sa pagitan ng dalawang link.
- `1` walang laman na linya sa dulo ng bawat isa `.md` file.

Halimbawa:

    [...]
    * [An Awesome Book](http://example.com/example.html)
                                    (blank line)
                                    (blank line)
    ### Example
                                    (blank line)
    * [Another Awesome Book](http://example.com/book.html)
    * [Some Other Book](http://example.com/other.html)

- Huwag maglagay ng mga puwang sa pagitan `]` at `(`:

```
BAD : * [Another Awesome Book] (http://example.com/book.html)
GOOD: * [Another Awesome Book](http://example.com/book.html)
```

- Kung isasama mo ang may-akda, gamitin ` - ` (isang gitling na napapalibutan ng mga solong espasyo):

```
BAD : * [Another Awesome Book](http://example.com/book.html)- John Doe
GOOD: * [Another Awesome Book](http://example.com/book.html) - John Doe
```

- Maglagay ng isang puwang sa pagitan ng link at ang format nito:

```
BAD : * [A Very Awesome Book](https://example.org/book.pdf)(PDF)
GOOD: * [A Very Awesome Book](https://example.org/book.pdf) (PDF)
```

- Nauna ang may-akda sa format:

```
BAD : * [A Very Awesome Book](https://example.org/book.pdf)- (PDF) Jane Roe
GOOD: * [A Very Awesome Book](https://example.org/book.pdf) - Jane Roe (PDF)
```

- Maramihang format:

```
BAD : * [Another Awesome Book](http://example.com/)- John Doe (HTML)
BAD : * [Another Awesome Book](https://downloads.example.org/book.html)- John Doe (download site)
GOOD: * [Another Awesome Book](http://example.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
```

- Isama ang taon ng publikasyon sa pamagat para sa mga mas lumang aklat:

```
BAD : * [A Very Awesome Book](https://example.org/book.html) - Jane Roe - 1970
GOOD: * [A Very Awesome Book (1970)](https://example.org/book.html) - Jane Roe
```

<a name="in_process"></a>
- In-process books:

```
GOOD: * [Will Be An Awesome Book Soon](http://example.com/book2.html) - John Doe (HTML) (:construction: *in process*)
```

<a name="archived"></a>
- Archived link:

```
GOOD: * [A Way-backed Interesting Book](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) *(:card_file_box: archived)*
```

### Mga Tala

Bagama't medyo simple ang mga pangunahing kaalaman, mayroong malaking pagkakaiba-iba sa mga mapagkukunang inilista namin. Narito ang ilang tala sa kung paano natin haharapin ang pagkakaiba-iba na ito.

#### Metadata

Nagbibigay ang aming mga listahan ng kaunting hanay ng metadata: mga pamagat, URL, tagalikha, platform, at tala sa pag-access.

##### Mga pamagat

- Walang naimbentong pamagat. Sinusubukan naming kumuha ng mga pamagat mula sa mga mapagkukunan mismo; ang mga nag-aambag ay pinapayuhan na huwag mag-imbento ng mga pamagat o gamitin ang mga ito sa editoryal kung ito ay maiiwasan. Ang isang pagbubukod ay para sa mas lumang mga gawa; kung pangunahin ang mga ito sa makasaysayang interes, ang isang taon sa panaklong na nakadugtong sa pamagat ay tumutulong sa mga user na malaman kung sila ay interesado.
- Walang pamagat ng ALLCAPS. Kadalasan ay angkop ang title case, ngunit kapag may pagdududa, gamitin ang capitalization mula sa source

##### URLs

- Hindi namin pinahihintulutan ang mga pinaikling URL.
- Dapat alisin ang mga tracking code sa URL.
- Dapat na i-escape ang mga internasyonal na URL. Karaniwang nire-render ito ng mga browser bar sa Unicode, ngunit gumamit ng kopya at i-paste.
- Ang mga Secure (https) na URL ay palaging mas gusto kaysa sa mga hindi secure na (http) na mga url kung saan ipinatupad ang https.
- Hindi namin gusto ang mga URL na tumuturo sa mga webpage na hindi nagho-host ng nakalistang mapagkukunan, ngunit sa halip ay tumuturo sa ibang lugar.

##### Mga tagalikha

- Gusto naming pasalamatan ang mga lumikha ng mga libreng mapagkukunan kung saan naaangkop, kabilang ang mga tagasalin!
- Para sa mga isinaling gawa ang orihinal na may-akda ay dapat na kredito.
- Hindi namin pinahihintulutan ang mga link para sa Mga Tagalikha.
- Para sa compilation o remixed na mga gawa, maaaring kailanganin ng "creator" ang isang paglalarawan. Halimbawa, ang mga aklat na "GoalKicker" o "RIP Tutorial" ay kinikilala bilang "`Compiled from StackOverflow Documentation`"

##### Mga Platform at Mga Tala sa Pag-access

- Kurso. Lalo na para sa aming mga listahan ng kurso, ang platform ay isang mahalagang bahagi ng paglalarawan ng mapagkukunan. Ito ay dahil ang mga platform ng kurso ay may iba't ibang mga affordance at mga modelo ng pag-access. Bagama't karaniwang hindi namin ilista ang isang aklat na nangangailangan ng pagpaparehistro, maraming mga platform ng kurso ang may mga affordance na hindi gumagana nang walang isang uri ng account. Kasama sa mga halimbawang platform ng kurso ang Coursera, EdX, Udacity, at Udemy. Kapag ang isang kurso ay nakasalalay sa isang platform, ang pangalan ng platform ay dapat na nakalista sa mga panaklong.
- YouTube. Marami kaming mga kurso na binubuo ng mga playlist sa YouTube. Hindi namin inilista ang Youtube bilang isang platform, sinusubukan naming ilista ang tagalikha ng Youtube, na kadalasan ay isang sub-platform.
- Mga video ng YouTube. Karaniwang hindi kami nagli-link sa mga indibidwal na video sa YouTube maliban kung ang mga ito ay higit sa isang oras ang haba at nakabalangkas tulad ng isang kurso o isang tutorial.
- Leanpub. Nagho-host ang Leanpub ng mga aklat na may iba't ibang modelo ng access. Minsan ang isang libro ay maaaring basahin nang walang pagpaparehistro; minsan ang isang libro ay nangangailangan ng isang Leanpub account para sa libreng pag-access. Dahil sa kalidad ng mga aklat at ang pinaghalong mga modelo ng pag-access sa Leanpub, pinahihintulutan namin ang paglilista ng huli kasama ang tala sa pag-access `*(Leanpub account o valid na email ang hinihiling)*`

#### Mga genre

Ang unang tuntunin sa pagpapasya kung saang listahan kabilang ang isang mapagkukunan ay upang makita kung paano inilalarawan ng mapagkukunan ang sarili nito. Kung ito ay tinatawag na isang libro, marahil ito ay isang libro.

##### Mga genre na hindi namin inililista

Dahil malawak ang Internet, hindi namin isinasama sa aming mga listahan:

- blogs
- blog posts
- articles
- websites (except for those that host LOTS of items that we list.)
- videos that aren't courses or screencasts.
- book chapters
- teaser samples from books
- IRC or Telegram channels
- Slacks or mailing lists

Ang aming mga listahan ng mapagkumpitensyang programming ay hindi kasing higpit tungkol sa mga pagbubukod na ito. Ang saklaw ng repo ay tinutukoy ng komunidad; kung gusto mong magmungkahi ng pagbabago o pagdaragdag sa saklaw, mangyaring gumamit ng isyu para gawin ang mungkahi.


##### Mga Aklat kumpara sa Iba Pang Bagay

Hindi kami masyadong maselan sa mga libro. Narito ang ilang mga katangian na nagpapahiwatig na ang isang mapagkukunan ay isang libro:

- mayroon itong ISBN (International Standard Book Number)
- mayroon itong Talaan ng mga Nilalaman
- inaalok ang isang nada-download na bersyon, lalo na ang mga ePub file.
- ito ay may mga edisyon
- hindi ito nakadepende sa interactive na content o mga video
- sinusubukan nitong kumprehensibong saklawin ang isang paksa
- ito ay may sarili

Maraming mga aklat na inilista namin na walang mga katangiang ito; ito ay maaaring depende sa konteksto.


##### Mga Aklat kumpara sa Mga Kurso

Minsan ang mga ito ay maaaring mahirap makilala!

Ang mga kurso ay kadalasang may kaugnay na mga aklat-aralin, na aming ililista sa aming mga listahan ng mga aklat. Ang mga kurso ay may mga lektura, pagsasanay, pagsusulit, tala o iba pang mga tulong sa didactic. Ang isang lektura o video mismo ay hindi isang kurso. Ang powerpoint ay hindi kurso.


##### Mga Interactive na Tutorial kumpara sa Iba pang bagay

Kung maaari mong i-print ito at panatilihin ang kakanyahan nito, hindi ito isang Interactive na Tutorial.


### Automation

- Ang pagpapatupad ng mga panuntunan sa pag-format ay awtomatiko sa pamamagitan ng [GitHub Actions](https://github.com/features/actions) gamit [fpb-lint](https://github.com/vhf/free-programming-books-lint) (see [.github/workflows/fpb-lint.yml](.github/workflows/fpb-lint.yml))
- Gumagamit ng pagpapatunay ng URL [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- Upang ma-trigger ang pagpapatunay ng URL, mag-push ng commit na may kasamang commit na mensahe na naglalaman `check_urls=file_to_check`:

```
check_urls=free-programming-books.md free-programming-books-en.md
```

- Maaari kang tumukoy ng higit sa isang file na susuriin, gamit ang isang puwang upang paghiwalayin ang bawat entry.
- Kung tumukoy ka ng higit sa isang file, ang mga resulta ng build ay batay sa resulta ng huling file na nasuri. Dapat mong malaman na maaari kang makapasa sa mga berdeng build dahil dito kaya siguraduhing suriin ang build log sa dulo ng pull request sa pamamagitan ng pag-click sa "Show all checks" -> "Details".
