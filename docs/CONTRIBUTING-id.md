*[Baca instruksi ini dalam bahasa lain](README.md#translations)*


<!----><a id="contributor-license-agreement"></a>
## Perjanjian Lisensi Kontributor

Dengan berkontribusi, Anda setuju dengan [lisensi](../LICENSE) dari repositori ini.


<!----><a id="contributor-code-of-conduct"></a>
## Kode Etik untuk Kontributor

Dengan berkontribusi, Anda setuju untuk menghormati [Kode Etik](CODE_OF_CONDUCT-id.md) dari repositori ini. ([translations](README.md#translations))


<!----><a id="in-a-nutshell"></a>
## Versi pendek

1. "Tautan untuk mengunduh buku dengan mudah" tidak selalu merujuk pada buku yang *gratis*. Harap hanya memberikan konten yang gratis. Pastikan itu benar-benar gratis. Kami tidak menerima tautan ke halaman yang *meminta* alamat email yang valid untuk mengunduh buku, tetapi kami menyambut daftar situs yang meminta alamat email.

2. Anda tidak harus terbiasa dengan Git: jika Anda menemukan sesuatu yang menarik *dan belum ada di repositori ini*, silakan buka [Isu](https://github.com/EbookFoundation/free-programming-books/issues) dengan proposal tautan Anda.
    - Jika Anda sudah familiar dengan Git, fork repositori dan kirimkan Pull Request (PR) Anda.

3. Kami memiliki 6 jenis daftar. Pastikan untuk memilih yang tepat:

    - *Buku*: PDF, HTML, ePub, halaman berdasarkan gitbook.io, repositori Git, dll.
    - *Kursus*: Kursus menggambarkan materi pembelajaran yang bukan berupa buku. [Ini adalah contoh kursus](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Tutorial interaktif*: Situs web interaktif yang memungkinkan pengguna memasukkan kode sumber perintah dan mengevaluasi hasilnya (dengan "mengevaluasi" kami tidak bermaksud "menilai"). misalnya: [Coba Haskell](http://tryhaskell.org), [Coba Git](https://learngitbranching.js.org).
    - *Playgrounds*: Situs web interaktif, permainan, atau perangkat lunak desktop untuk belajar pemrograman. Anda dapat menulis, mengkompilasi (atau menjalankan), dan membagikan potongan kode. Playgrounds seringkali memperbolehkan Anda untuk membuat salinan (fork) dan membebaskan Anda untuk bermain dengan kodenya.
    - *Podcast dan Screencasts*: Podcast dan Screencasts.
    - *Kumpulan Masalah & Pemrograman Kompetitif*: Situs web atau perangkat lunak yang memungkinkan Anda mengukur kemampuan pemrograman Anda dengan menyelesaikan masalah-masalah sederhana atau kompleks, dengan atau tanpa tinjauan kode, dengan atau tanpa membandingkan hasilnya dengan pengguna lain.

4. Pastikan Anda mengikuti [Guidelines di bawah](#guidelines) dan menghormati [Formatting Markdown](#formatting) dari setiap file.

5. GitHub Actions akan menjalankan pengujian untuk **memastikan bahwa daftar yang Anda buat diurutkan secara alfabetis** dan **mengikuti aturan format**. **Pastikan** untuk memeriksa bahwa perubahan yang Anda buat lulus uji coba tersebut.


<!----><a id="guidelines"></a>
### Pedoman

- Pastikan bahwa buku yang Anda tambahkan benar-benar gratis. Periksa dua kali jika perlu. Ini akan membantu para admin jika Anda memberikan komentar di PR mengenai alasan Anda menganggap buku tersebut gratis.
- Kami tidak menerima file yang bersumber dari Google Drive, Dropbox, Mega, Scribd, Issuu, dan platform unggah file serupa lainnya.
- Masukkan tautan Anda dalam urutan alfabetis, seperti yang dijelaskan [di bawah](#alphabetical-order).
- Gunakan tautan dengan sumber yang paling otoritatif (artinya situs web penulis lebih baik daripada situs web penyunting, yang lebih baik daripada situs web pihak ketiga).
    - Jangan gunakan layanan hosting file (termasuk namun tidak terbatas pada tautan Dropbox dan Google Drive).
- Selalu gunakan protokol tautan `https` daripada tautan `http` -- selama keduanya berada di domain yang sama dan menyajikan konten yang sama.
- Pada domain root, hapus garis miring di akhir: `http://example.com` alih-alih `http://example.com/`
- Selalu pilih tautan terpendek: `http://example.com/dir/` lebih baik daripada `http://example.com/dir/index.html`.
    - Jangan gunakan tautan penyusut (shortener) URL.
- Pilih tautan ke "versi terbaru" alih-alih menautkan ke "versi tertentu": `http://example.com/dir/book/current/` lebih baik daripada `http://example.com/dir/book/v1.0.0/index.html`.
- Jika sebuah tautan memiliki sertifikat yang sudah kedaluwarsa/sertifikat buatan sendiri/masalah SSL lainnya:
    1. *Gantilah* dengan versi `http` jika memungkinkan (karena prosesi pengecualian / bypass bisa jadi rumit di perangkat seluler).
    2. *Biarkan apa adanya* jika versi `http` tidak tersedia, tetapi tautan dapat diakses melalui `https` dengan mengabaikan peringatan di browser atau menambahkan pengecualian.
    3. *Hapus* jika tidak ada pilihan lain.
- Jika sebuah tautan ada dalam beberapa format, tambahkan tautan terpisah dengan catatan tentang setiap format.
- Jika sebuah sumber ada di berbagai tempat di Internet:
    - Gunakan tautan dengan sumber yang paling otoritatif (artinya situs web penulis lebih baik daripada situs web penyunting, yang lebih baik daripada situs web pihak ketiga).
    - Jika mereka merujuk ke edisi yang berbeda, dan Anda menganggap edisi tersebut cukup berbeda sehingga layak untuk tetap mempertahankannya, tambahkan tautan terpisah dengan catatan tentang setiap edisi (lihat [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) untuk berpartisipasi dalam diskusi tentang pemformatan).
- Utamakan komit atomik (satu komit per-penambahan/penghapusan/modifikasi) daripada komit yang lebih besar. Tidak perlu menggabungkan komit-komit Anda sebelum mengirimkan PR. (Kami tidak akan pernah menegakkan aturan ini karena ini hanya masalah kenyamanan bagi para pengelola).
- Jika buku sudah lama diterbitkan, sertakan tanggal publikasinya bersama dengan judulnya.
- Sertakan nama atau nama-nama penulis yang sesuai. Anda dapat memendekkan daftar penulis dengan "`et al.`".
- Jika buku belum selesai, dan masih dalam tahap pengerjaan, tambahkan keterangan "`dalam proses`" seperti yang dijelaskan [di bawah ini](#in_process).
- Jika suatu sumber dipulihkan menggunakan [*Internet Archive's Wayback Machine*](https://web.archive.org) (atau serupa), tambahkan keterangan "`terarsip`" seperti yang dijelaskan [di bawah](#archived). Versi terbaik untuk digunakan adalah versi terbaru dan lengkap.
- Jika alamat email atau pengaturan akun diperlukan sebelum pengunduhan, tambahkan catatan sesuai dengan bahasa yang tepat dalam tanda kurung, misalnya: `(alamat email *diminta*, tidak wajib)`.


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

- Format lebih dari satu (Kami lebih suka satu tautan untuk setiap sumber. Ketika tidak ada tautan tunggal yang dapat  diakses lebih mudah ke format yang berbeda, beberapa tautan lebih diutamakan. Namun, setiap tautan yang kami tambahkan akan menambah beban pemeliharaan sehingga kami mencoba menghindarinya.)
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

- Ketika terdapat beberapa judul yang dimulai dengan huruf yang sama, urutkan berdasarkan yang kedua, dan seterusnya. Sebagai contoh: `aa` muncul sebelum `ab`.
- `one two` muncul sebelum `onetwo`

Jika Anda melihat tautan yang salah tempat, periksa pesan kesalahan linter untuk mengetahui baris mana yang harus ditukar.


<!----><a id="notes"></a>
### Catatan

Meskipun dasar-dasarnya relatif sederhana, ada keragaman besar dalam sumber daya yang kami daftarkan. Berikut adalah beberapa catatan tentang bagaimana kita menghadapi keragaman ini.


#### Metadata

Daftar kami menyediakan kumpulan metadata minimal: judul, URL, pembuat, platform, dan catatan akses.


<!----><a id="titles"></a>
##### Judul

- Tidak menggunakan judul yang diciptakan. Kami mencoba menggunakan judul dari sumber daya itu sendiri; kontributor diharapkan untuk tidak membuat judul atau menggunakan judul secara editorial jika hal ini dapat dihindari. Sebuah pengecualian adalah untuk karya-karya lama; jika mereka utamanya dari minat sejarah, tahun dalam tanda kurung yang ditambahkan ke judul membantu pengguna mengetahui jika mereka menarik minat.
- Tidak menggunakan judul dengan HURUF KAPITAL. Biasanya, judul yang ditulis dengan huruf kapital awal adalah yang sesuai, tetapi jika ragu, gunakan kapitalisasi yang sesuai dari sumbernya.
- Tidak menggunakan emoji.


##### URLs

- Kami tidak mengizinkan penggunaan URL yang disingkat.
- Kode pelacakan harus dihapus dari URL.
- URL internasional harus diubah menjadi format yang benar (escaped). Biasanya, bilah peramban akan menampilkan ini dalam bentuk Unicode, namun, untuk menghindari kesalahan, harap menggunakan salin dan tempel (copy and paste).
- URL yang aman (`https`) selalu diutamakan daripada URL yang tidak aman (`http`) di tempat-tempat di mana HTTPS telah diimplementasikan.
- Kami tidak menyukai URL yang mengarah ke halaman web yang tidak menghosting sumber daya yang terdaftar, melainkan menunjuk ke tempat lain.


<!----><a id="creators"></a>
##### Pencipta

- Kami ingin menghargai pencipta sumber daya gratis jika perlu, termasuk penerjemah!
- Untuk karya terjemahan, penulis asli harus dikreditkan. Kami rekomendasikan menggunakan [kode relator MARC](https://loc.gov/marc/relators/relaterm.html) untuk mengkredit pencipta selain penulis, seperti dalam contoh ini:

    ```markdown
    * [A Translated Book](http://example.com/book-id.html) - John Doe, `trl.:` Mike The Translator
    ```

    di sini, anotasi `trl.:` memakai kode relator MARC untuk "penerjemah".
- Gunakan koma `,` untuk memisahkan setiap item dalam daftar penulis.
- Anda dapat mempersingkat daftar penulis dengan "`et al.`".
- Kami tidak mengizinkan tautan untuk Kreator.
- Untuk karya kompilasi atau campuran, "pencipta" mungkin memerlukan deskripsi. Misalnya, buku "GoalKicker" atau "RIP Tutorial" dikreditkan sebagai "`Dikompilasi dari dokumentasi StackOverflow`" (dalam Bahasa Inggris: `Compiled from StackOverflow documentation`).


<!----><a id="time-limited-courses-and-trials"></a>
##### Kursus dan Uji Coba dengan Batas Waktu

- Kami tidak mencantumkan hal-hal yang perlu kami hapus dalam enam bulan.
- Jika sebuah kursus memiliki periode pendaftaran atau durasi terbatas, kami tidak akan mencantumkannya.
- Kami tidak dapat mencantumkan sumber daya yang gratis hanya untuk jangka waktu tertentu.


<!----><a id="platforms-and-access-notes"></a>
##### Platform dan Catatan Akses

- Kursus. Khususnya untuk daftar kursus kami, platform merupakan bagian penting dari deskripsi sumber daya. Hal ini karena platform kursus memiliki keterjangkauan dan model akses yang berbeda. Meskipun kami biasanya tidak akan mencantumkan buku yang memerlukan pendaftaran, banyak platform kursus memiliki keterjangkauan yang tidak berfungsi tanpa akun tertentu. Contoh platform kursus termasuk Coursera, EdX, Udacity, dan Udemy. Ketika sebuah kursus bergantung pada suatu platform, nama platform tersebut harus dicantumkan dalam tanda kurung.
- YouTube. Kami memiliki banyak kursus yang terdiri dari daftar putar YouTube. Kami tidak mencantumkan YouTube sebagai sebuah platform, kami mencoba mencantumkan kreator YouTube, yang seringkali merupakan sub-platform.
- Video YouTube. Kami biasanya tidak mengaitkan tautan ke video YouTube individu kecuali jika video tersebut berdurasi lebih dari satu jam dan disusun seperti kursus atau tutorial. Jika ini adalah kasusnya, pastikan untuk mencatatnya dalam deskripsi PR.
- Leanpub. Leanpub menyediakan buku dengan berbagai model akses. Terkadang sebuah buku bisa dibaca tanpa registrasi; terkadang sebuah buku memerlukan akun Leanpub untuk akses gratis. Mengingat kualitas buku dan campuran serta kelenturan model akses Leanpub, kami mengizinkan penulisan yang terakhir dengan catatan akses `*(Akun Leanpub atau alamat email valid diminta)*`


<!----><a id="genres"></a>
#### Genre

Aturan pertama dalam menentukan daftar mana sebuah sumber daya masuk adalah melihat bagaimana sumber daya itu menggambarkan dirinya sendiri. Jika sumber daya tersebut menyebut dirinya sebagai buku, bisa jadi sumber daya tersebut adalah buku.


<!----><a id="genres-we-dont-list"></a>
##### Genre yang tidak kami cantumkan

Karena Internet sangat luas, kami tidak memasukkan dalam daftar kami:

- blog
- postingan blog
- artikel
- situs web (kecuali yang meng-host BANYAK item yang kami daftarkan).
- video yang bukan kursus atau screencasts.
- bab buku
- sampel teaser dari buku
- saluran IRC atau Telegram
- Slacks atau daftar email (Slacks or mailing lists)

Daftar pemrograman kompetitif kami tidak seketat pengecualian ini. Lingkup repositori ini ditentukan oleh komunitas; jika Anda ingin menyarankan perubahan atau penambahan pada lingkup, harap gunakan isu (issue) untuk memberikan saran.


<!----><a id="books-vs-other-stuff"></a>
##### Buku vs. Barang Lainnya

Kami tidak rewel tentang kebukuan. Berikut adalah beberapa atribut yang menandakan bahwa sumber daya adalah sebuah buku:

- memiliki ISBN (Nomor Buku Standar Internasional)
- memiliki Daftar Isi
- ada versi yang dapat diunduh, terutama ePub
- memiliki edisi
- tidak tergantung pada video atau konten interaktif
- mencoba untuk mencakup topik secara komprehensif
- bersifat mandiri

Ada banyak buku yang kami cantumkan yang tidak memiliki atribut-atribut ini; itu bisa tergantung pada konteks.


<!----><a id="books-vs-courses"></a>
##### Buku vs. Kursus

Terkadang ini sulit untuk dibedakan!

Kursus sering kali memiliki buku teks terkait, yang akan kami daftarkan dalam daftar buku kami. Kursus memiliki kuliah, latihan, tes, catatan atau alat bantu didaktik lainnya. Sebuah kuliah atau video dengan sendirinya bukanlah sebuah kursus. Sebuah powerpoint bukanlah kursus.


<!----><a id="interactive-tutorials-vs-other-stuff"></a>
##### Tutorial Interaktif vs. Hal-hal lain

Jika Anda dapat mencetaknya dan mempertahankan esensinya, itu bukan Tutorial Interaktif.


<!----><a id="automation"></a>
### Otomatisasi

- Penegakan aturan format dilakukan secara otomatis melalui [GitHub Actions](https://github.com/features/actions) menggunakan [fpb-lint](https://github.com/vhf/free-programming-books-lint) (lihat [`.github/workflows/fpb-lint.yml`](../.github/workflows/fpb-lint.yml)).
- Validasi URL menggunakan [awesome_bot](https://github.com/dkhamsing/awesome_bot).
- Untuk memicu validasi URL, *lakukan commit* yang mencakup pesan commit yang berisi `check_urls=berkas_yang_akan_dicek`:

    ```properties
    check_urls=free-programming-books.md free-programming-books-id.md
    ```

- Anda dapat menentukan lebih dari satu berkas untuk diperiksa, dengan menggunakan spasi tunggal untuk memisahkan setiap entri.
- Jika Anda menentukan lebih dari satu berkas, hasil build didasarkan pada hasil berkas terakhir yang diperiksa. Anda harus memperhatikan bahwa Anda mungkin mendapatkan hasil build yang berhasil, jadi pastikan Anda memeriksa log pembangunan pada akhir Pull Request dengan mengklik "Show all checks" -> "Details".
