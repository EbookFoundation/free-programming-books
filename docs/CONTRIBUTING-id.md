*[Instruksi ini dalam bahasa lain](README.md#translations)*


<!----><a id="contributor-license-agreement"></a>
## Perjanjian lisensi kontributor

Dengan kerja sama Anda, Anda menerima [lisensi](../LICENSE) dari repositori ini.


<!----><a id="contributor-code-of-conduct"></a>
## Kode Etik untuk Kontributor

Dengan partisipasi Anda, Anda berjanji untuk mengikuti [Kode Etik](CODE_OF_CONDUCT-id.md) dari repositori ini. ([translations](README.md#translations))


<!----><a id="in-a-nutshell"></a>
## Versi pendek

1. "Tautan untuk mengunduh buku dengan mudah" tidak selalu merupakan tautan ke buku *gratis*. Harap hanya menambahkan konten gratis. Pastikan mereka gratis. Kami tidak menerima tautan ke situs yang *mengharuskan* Anda mendaftar dengan alamat email yang berfungsi untuk mengunduh buku, tetapi kami menyambut situs yang meminta alamat email.

2. Anda tidak harus terbiasa dengan Git: Jika Anda telah menemukan sesuatu yang menarik *yang belum ada di salah satu daftar*, silakan buka [Masalah](https://github.com/EbookFoundation/free-programming-books/issues) dengan tautan yang Anda sarankan.
    - Jika Anda sudah familiar dengan Git, fork repositori dan kirim Pull Request (PR).

3. Kami menyimpan 6 jenis daftar. Pastikan untuk memilih yang tepat:

    - *Buku*: PDF, HTML, ePub, halaman berdasarkan gitbook.io, repo Git, dll.
    - *Kursus*: Kursus menggambarkan materi pembelajaran yang tidak ada dalam bentuk buku. [Ini adalah kursus](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Tutorial interaktif*: Situs web interaktif yang memungkinkan pengguna memasukkan kode sumber perintah dan mengevaluasi hasilnya (dengan "mengevaluasi" kami tidak bermaksud "menilai"). misalnya: [Coba Haskell](http://tryhaskell.org), [Coba GitHub](http://try.github.io).
    - *Playgrounds* : are online and interactive websites, games or desktop software for learning programming. Write, compile (or run), and share code snippets. Playgrounds often allow you to fork and get your hands dirty by playing with code.
    - *Podcast dan Screencasts*: Podcast dan Screencasts.
    - *Kumpulan Masalah & Pemrograman Kompetitif*: Situs web atau perangkat lunak yang memberi Anda kesempatan untuk menguji keterampilan pemrograman Anda dengan memecahkan masalah sederhana atau kompleks, dengan atau tanpa tinjauan kode dan dengan atau tanpa membandingkan kinerja dengan orang lain Pengunjung situs.

4. Pastikan Anda mengikuti [Guidelines](#guidelines) dan hormati [Markdown Formatting](#formatting) dari file.

5. GitHub Actions akan menjalankan tes untuk memastikan bahwa **daftar diurutkan berdasarkan abjad dengan benar** dan bahwa **aturan pemformatan telah diikuti**. **Pastikan** perubahan Anda lulus tes ini.


<!----><a id="guidelines"></a>
### Pedoman

- Pastikan sebuah buku benar-benar gratis. Periksa kembali jika perlu. Ini membantu administrator jika Anda menjelaskan dalam PR Anda mengapa menurut Anda buku tersebut gratis.
- Kami tidak merekam file yang ada di Google Drive, Dropbox, Mega, Scribd, Issuu atau platform unggah file lainnya sebanding.
- Masukkan tautan dalam urutan abjad, as described [below](#alphabetical-order).
- Selalu pilih tautan dari sumber otoritatif (yaitu, situs web penulis lebih baik daripada situs web editor, yang pada gilirannya akan lebih baik daripada situs web pihak ketiga)
    - tidak ada platform hosting file (termasuk tautan ke Dropbox, Google Drive, dll.).
- Tautan `https` harus selalu lebih disukai daripada tautan `http` - selama tautan tersebut mengarah ke domain dan konten yang sama.
- Garis miring harus dihapus pada domain root: `http://example.com` alih-alih `http://example.com/`
- Selalu pilih tautan terpendek: `http://example.com/dir/` lebih baik daripada `http://example.com/dir/index.html`.
    - jangan gunakan penyingkat URL.
- Pilih tautan ke "versi terbaru" alih-alih menautkan ke "versi tertentu": `http://example.com/dir/book/current/` lebih baik daripada `http://example.com/dir/book/v1.0.0/index.html`.
- Jika tautan menggunakan sertifikat yang kedaluwarsa atau ditandatangani sendiri atau memiliki masalah SSL lain:
    1. *ganti* dengan mitra `http` jika memungkinkan (karena menerima pengecualian dapat menjadi rumit pada perangkat seluler).
    2. *biarkan apa adanya* jika versi `http` tidak tersedia, tetapi tautan dapat diakses melalui `https` dengan mengabaikan peringatan di browser atau menambahkan pengecualian.
    3. *hapus* jika tidak.
- jika ada tautan dalam format yang berbeda, tambahkan tautan terpisah dengan catatan tentang setiap format.
- jika sepotong konten tersedia di beberapa tempat di Internet.
    - pilih tautan otoritatif.
    - gunakan tautan dengan sumber paling otoritatif (artinya situs web penulis lebih baik daripada situs web editor lebih baik daripada situs web pihak ketiga).
    - jika mereka menautkan ke edisi yang berbeda dan Anda menilai edisi ini cukup berbeda sehingga layak untuk disimpan, tambahkan tautan terpisah dengan catatan tentang setiap edisi (lihat [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) untuk berkontribusi pada diskusi tentang pemformatan).
- lebih suka komit atom (satu komit dengan penambahan/penghapusan/modifikasi) daripada komit yang lebih besar. Tidak perlu menekan komitmen Anda sebelum mengirimkan PR. (Kami tidak akan pernah menegakkan aturan ini karena ini hanya masalah kenyamanan bagi pengelola).
- jika buku lebih tua, sertakan tanggal penerbitan dengan judul.
- sertakan nama penulis atau nama yang sesuai. Anda dapat mempersingkat daftar penulis dengan "`et al.`".
- jika buku belum selesai, dan masih dalam pengerjaan, tambahkan notasi "`dalam proses`", seperti yang dijelaskan [di bawah ini](#in_process).
- if a resource is restored using the [*Internet Archive's Wayback Machine*](https://web.archive.org) (or similar), add the "`archived`" notation, as described [below](#archived). The best versions to use are recent and complete.
- jika alamat email atau pengaturan akun diminta sebelum pengunduhan diaktifkan, tambahkan catatan bahasa yang sesuai dalam tanda kurung, misalnya: `(alamat email *diminta*, tidak wajib)`.


<!----><a id="formatting"></a>
### Pemformatan

- Semua daftar adalah file `.md`. Coba pelajari sintaks [Markdown](https://guides.github.com/features/mastering-markdown/). Itu mudah!
- Semua daftar dimulai dengan Indeks. Idenya adalah untuk membuat daftar dan menautkan semua bagian dan subbagian di sana. Simpan dalam urutan abjad.
- Bagian menggunakan heading level 3 (`###`), dan subbagian menggunakan heading level 4 (`####`).

Idenya adalah untuk memiliki:

- `2` baris kosong antara tautan terakhir dan bagian baru.
- `1` baris kosong antara heading & tautan pertama dari bagiannya.
- `0` baris kosong di antara dua tautan.
- `1` baris kosong di akhir setiap file `.md`.

Contoh:

```text
[...]
* [Contoh Buku](http://example.com/example.html)
                            (baris kosong)
                            (baris kosong)
### Contoh
                            (baris kosong)
* [Contoh Buku Lainnya](http://example.com/book.html)
* [Beberapa Buku Lain](http://example.com/other.html)
```

- Jangan gunakan spasi diantara `]` dan `(`:

    ```text
    BURUK : * [Contoh Buku Lainnya] (http://example.com/book.html)
    BAIK  : * [Contoh Buku Lainnya](http://example.com/book.html)
    ```

- Jika Anda menyertakan penulis, gunakan ` - ` (tanda hubung yang dikelilingi oleh satu spasi):

    ```text
    BURUK : * [Contoh Buku Lainnya](http://example.com/book.html)- John Doe
    BAIK  : * [Contoh Buku Lainnya](http://example.com/book.html) - John Doe
    ```

- Letakkan satu spasi di antara tautan dan formatnya:

    ```text
    BURUK : * [Buku yang Sangat Bagus](https://example.org/book.pdf)(PDF)
    BAIK  : * [Buku yang Sangat Bagus](https://example.org/book.pdf) (PDF)
    ```

- Penulis diletakan sebelum format file:

    ```text
    BURUK : * [Buku yang Sangat Bagus](https://example.org/book.pdf)- (PDF) Jane Roe
    BAIK  : * [Buku yang Sangat Bagus](https://example.org/book.pdf) - Jane Roe (PDF)
    ```

- Format lebih dari satu:

    ```text
    BURUK : * [Contoh Buku Lainnya](http://example.com/)- John Doe (HTML)
    BURUK : * [Contoh Buku Lainnya](https://downloads.example.org/book.html)- John Doe (situs download)
    BAIK  : * [Contoh Buku Lainnya](http://example.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
    ```

- Cantumkan tahun penerbitan dalam judul buku lama:

    ```text
    BURUK : * [Buku yang Sangat Bagus](https://example.org/book.html) - Jane Roe - 1970
    BAIK  : * [Buku yang Sangat Bagus (1970)](https://example.org/book.html) - Jane Roe
    ```

- <a id="in_process"></a>Buku dalam proses:

    ```text
    BAIK  : * [Akan Segera Menjadi Buku yang Luar Biasa](http://example.com/book2.html) - John Doe (HTML) (:construction: *in process*)
    ```

- <a id="archived"></a>Archived link:

    ```text
    BAIK  : * [A Way-backed Interesting Book](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) *(:card_file_box: archived)*
    ```

### Alphabetical order

- When there are multiple titles beginning with the same letter order them by the second, and so on. For example: `aa` comes before `ab`.
- `one two` comes before `onetwo`

If you see a misplaced link, check the linter error message to know which lines should be swapped.


<!----><a id="notes"></a>
### Catatan

Meskipun dasar-dasarnya relatif sederhana, ada keragaman besar dalam sumber daya yang kami daftarkan. Berikut adalah beberapa catatan tentang bagaimana kita menghadapi keragaman ini.


#### Metadata

Daftar kami menyediakan kumpulan metadata minimal: judul, URL, pembuat, platform, dan catatan akses.


<!----><a id="titles"></a>
##### Judul

- Tidak ada judul yang diciptakan. Kami mencoba mengambil judul dari sumber itu sendiri; kontributor diperingatkan untuk tidak membuat judul atau menggunakannya secara editorial jika hal ini dapat dihindari. Pengecualian adalah untuk karya yang lebih tua; jika mereka terutama memiliki minat historis, satu tahun dalam tanda kurung yang ditambahkan ke judul membantu pengguna mengetahui apakah mereka menarik.
- Tidak ada judul SEMUANYA KAPITAL. Biasanya judul kasus sesuai, tetapi jika ragu gunakan kapitalisasi dari sumbernya.
- No emojis.


##### URLs

- Kami tidak mengizinkan URL yang dipersingkat.
- Kode pelacakan harus dihapus dari URL.
- URL internasional harus diloloskan. Bilah peramban biasanya merender ini ke Unicode, tetapi gunakan salin dan tempel.
- URL aman (`https`) selalu lebih disukai daripada url tidak aman (`http`) di mana HTTPS telah diterapkan.
- Kami tidak menyukai URL yang mengarah ke halaman web yang tidak menghosting sumber daya yang terdaftar, melainkan menunjuk ke tempat lain.


<!----><a id="creators"></a>
##### Pencipta

- Kami ingin menghargai pencipta sumber daya gratis jika perlu, termasuk penerjemah!
- Untuk karya terjemahan penulis asli harus dikreditkan. We recommend using [MARC relators](https://loc.gov/marc/relators/relaterm.html) to credit creators other than authors, as in this example:

    ```markdown
    * [A Translated Book](http://example.com/book-id.html) - John Doe, `trl.:` Mike The Translator
    ```

    here, the annotation `trl.:` uses the MARC relator code for "translator".
- Use a comma `,` to delimit each item in the author list.
- You can shorten author lists with "`et al.`".
- Kami tidak mengizinkan tautan untuk Kreator.
- Untuk karya kompilasi atau remix, "pencipta" mungkin memerlukan deskripsi. Misalnya, buku "GoalKicker" atau "RIP Tutorial" dikreditkan sebagai "`Dikompilasi dari dokumentasi StackOverflow`" (dalam Bahasa Inggris: `Compiled from StackOverflow documentation`).


<!----><a id="platforms-and-access-notes"></a>
##### Platform dan Catatan Akses

- Kursus. Khusus untuk daftar kursus kami, platform merupakan bagian penting dari deskripsi sumber daya. Ini karena platform kursus memiliki keterjangkauan dan model akses yang berbeda. Meskipun kami biasanya tidak akan mencantumkan buku yang memerlukan pendaftaran, banyak platform kursus memiliki keterjangkauan yang tidak berfungsi tanpa semacam akun. Contoh platform kursus termasuk Coursera, EdX, Udacity , dan Udemy. Jika kursus bergantung pada platform, nama platform harus dicantumkan dalam tanda kurung.
- YouTube. Kami memiliki banyak kursus yang terdiri dari daftar putar YouTube. Kami tidak mencantumkan YouTube sebagai platform, kami mencoba mencantumkan pembuat YouTube, yang seringkali merupakan sub-platform.
- Video YouTube. Kami biasanya tidak menautkan ke video YouTube individu kecuali jika durasinya lebih dari satu jam dan terstruktur seperti kursus atau tutorial.
- Leanpub. Leanpub menyelenggarakan buku dengan berbagai model akses. Terkadang sebuah buku dapat dibaca tanpa registrasi; terkadang sebuah buku memerlukan akun Leanpub untuk akses gratis. Mengingat kualitas buku dan campuran dan fluiditas model akses Leanpub, kami mengizinkan daftar yang terakhir dengan catatan akses `*(Akun Leanpub atau email yang valid diminta)*`.


<!----><a id="genres"></a>
#### Genre

Aturan pertama dalam memutuskan daftar mana yang termasuk dalam sumber daya adalah melihat bagaimana sumber daya itu menggambarkan dirinya sendiri. Jika itu menyebut dirinya sebuah buku, maka mungkin itu adalah sebuah buku.


<!----><a id="genres-we-dont-list"></a>
##### Genre yang tidak kami cantumkan

Karena Internet sangat luas, kami tidak memasukkan dalam daftar kami:

- blog
- postingan blog
- artikel
- situs web (kecuali yang menghosting BANYAK item yang kami daftarkan).
- video yang bukan kursus atau screencasts.
- bab buku
- sampel penggoda dari buku
- Saluran IRC atau Telegram
- Celana panjang atau milis

Daftar pemrograman kompetitif kami tidak seketat pengecualian ini. Lingkup repo ditentukan oleh komunitas; jika Anda ingin menyarankan perubahan atau penambahan ruang lingkup, silakan gunakan masalah untuk membuat saran.


<!----><a id="books-vs-other-stuff"></a>
##### Buku vs. Barang Lainnya

Kami tidak rewel tentang kebukuan. Berikut adalah beberapa atribut yang menandakan bahwa sumber daya adalah sebuah buku:

- memiliki ISBN (Nomor Buku Standar Internasional)
- memiliki Daftar Isi
- versi yang diunduh, terutama ePub, ditawarkan
- memiliki edisi
- itu tidak tergantung pada konten atau video interaktif
- mencoba untuk mencakup topik secara komprehensif
- itu mandiri

Ada banyak buku yang kami daftarkan yang tidak memiliki atribut ini; itu bisa tergantung pada konteksnya.


<!----><a id="books-vs-courses"></a>
##### Buku vs. Kursus

Terkadang ini sulit untuk dibedakan!

Kursus sering kali memiliki buku teks terkait, yang akan kami daftarkan dalam daftar buku kami. Kursus memiliki kuliah, latihan, tes, catatan atau alat bantu didaktik lainnya. Sebuah kuliah atau video dengan sendirinya bukanlah sebuah kursus. Sebuah powerpoint bukanlah kursus.


<!----><a id="interactive-tutorials-vs-other-stuff"></a>
##### Tutorial Interaktif vs. Hal-hal lain

Jika Anda dapat mencetaknya dan mempertahankan esensinya, itu bukan Tutorial Interaktif.


<!----><a id="automation"></a>
### Otomatisasi

- Pemformatan penegakan aturan otomatis melalui [GitHub Actions](https://github.com/features/actions) gunakan [fpb-lint](https://github.com/vhf/free-programming-books-lint) (lihat [`.github/workflows/fpb-lint.yml`](../.github/workflows/fpb-lint.yml)).
- Validasi URL menggunakan [awesome_bot](https://github.com/dkhamsing/awesome_bot).
- Untuk memicu validasi URL, *push commit* yang menyertakan pesan komit yang berisi `check_urls=file_to_check`:

    ```properties
    check_urls=free-programming-books.md free-programming-books-id.md
    ```

- Anda dapat menentukan lebih dari satu file untuk diperiksa, menggunakan satu spasi untuk memisahkan setiap entri.
- Jika Anda menentukan lebih dari satu file, hasil build didasarkan pada hasil file terakhir yang diperiksa. Anda harus menyadari bahwa Anda dapat melewati build hijau karena hal ini, jadi pastikan untuk memeriksa log build di akhir Pull Request dengan mengklik "Show all checks" -> "Details".
