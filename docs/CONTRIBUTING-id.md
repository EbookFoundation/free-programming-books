*[Baca instruksi ini dalam bahasa lain](README.md#translations)*


<!----><a id="contributor-license-agreement"></a>
## Perjanjian Lisensi Kontributor

Dengan berkontribusi, Anda setuju dengan [lisensi](../LICENSE) dari repositori ini.


<!----><a id="contributor-code-of-conduct"></a>
## Kode Etik untuk Kontributor

Dengan berkontribusi, Anda setuju untuk menghormati [Kode Etik](CODE_OF_CONDUCT-id.md) dari repositori ini. ([translations](README.md#translations))


<!----><a id="in-a-nutshell"></a>
## Versi pendek

1. "Tautan untuk mengunduh buku" tidak selalu merujuk pada buku yang benar-benar *gratis*. Mohon untuk hanya mendaftarkan tautan ke buku/konten yang benar-benar gratis. Kami tidak menerima tautan ke situs web yang *membutuhkan* alamat email dari pengguna sebelum mengunduh atau mengakses kontennya. Kami hanya dapat menerima tautan yang membutuhkan alamat email pengguna (atau yang serupa) jika bagian keterangan sesuai dengan panduan yang kami berikan.

2. Anda tidak harus terbiasa dengan Git: jika Anda menemukan sesuatu yang menarik *dan belum ada di repositori ini*, silakan buka [Isu](https://github.com/EbookFoundation/free-programming-books/issues) dengan proposal tautan Anda.
    - Jika Anda sudah familiar dengan Git, fork repositori dan kirimkan Pull Request (PR) Anda.

3. Kami memiliki 6 kategori tautan. Pastikan untuk memilih kategori yang tepat sebelum mendaftarkan tautan yang anda usulkan:

    - *Buku*: PDF, HTML, ePub, halaman gitbook.io berbasis web, repositori Git, dll.
    - *Kursus*: Kursus menggambarkan materi pembelajaran yang bukan berupa buku. [Ini adalah contoh kursus](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Tutorial interaktif*: Situs web interaktif yang memungkinkan pengguna memasukkan kode sumber (source code) atau perintah dan hasilnya bisa dievaluasi ("evaluasi" yang dimaksud bukan evaluasi dengan tujuan memberikan "nilai" yang berupa angka). misalnya: [Coba Haskell](http://tryhaskell.org), [Coba Git](https://learngitbranching.js.org).
    - *Playgrounds*: Situs web interaktif, permainan (game), atau aplikasi desktop untuk belajar pemrograman. Anda dapat menulis, mengkompilasi (atau menjalankan), dan membagikan source code yang ditulis. Playgrounds seringkali memperbolehkan Anda untuk membuat salinan (fork) dan membebaskan Anda untuk bermain dengan kodenya.
    - *Podcast dan Screencasts*: Podcast dan Screencasts.
    - *Kumpulan Masalah & Pemrograman Kompetitif*: Situs web atau perangkat lunak yang memungkinkan Anda untuk mengukur kemampuan pemrograman Anda dengan menyelesaikan masalah-masalah sederhana atau kompleks, dengan atau tanpa proses tinjauan kode, dengan atau tanpa membandingkan hasilnya dengan pengguna lain.

4. Pastikan Anda mengikuti [Pedoman](#guidelines) di bawah ini dan mengikuti [Panduan Penulisan Markdown](#formatting).

5. GitHub Actions akan melakukan pengujian untuk **memastikan bahwa daftar yang Anda buat diurutkan secara alfabetis** dan **mengikuti aturan format**. **Pastikan** untuk memeriksa bahwa perubahan yang Anda buat lulus pengujian tersebut.


<!----><a id="guidelines"></a>
### Pedoman

- Pastikan bahwa buku yang Anda tambahkan benar-benar gratis. Periksa dua kali jika perlu. Para Admin akan sangat terbantu jika Anda menambahkan catatan pada Pull Request (PR) tentang alasan Anda menganggap buku/konten yang diusulkan gratis.
- Kami tidak menerima file yang bersumber dari Google Drive, Dropbox, Mega, Scribd, Issuu, dan platform unggah file serupa lainnya.
- Masukkan tautan Anda dalam urutan alfabetis, seperti yang dijelaskan [di bawah](#alphabetical-order).
- Gunakan tautan dengan sumber yang paling otoritatif (artinya situs web penulis lebih baik daripada situs web penyunting, yang lebih baik daripada situs web pihak ketiga).
    - Jangan gunakan layanan hosting file (termasuk namun tidak terbatas pada tautan Dropbox dan Google Drive).
- Selalu gunakan protokol tautan `https` daripada tautan `http` -- selama keduanya berada di domain yang sama dan menyajikan konten yang sama.
- Pada domain utama, hapus garis miring di akhir: `http://example.com` alih-alih `http://example.com/`
- Selalu pilih tautan terpendek: `http://example.com/dir/` lebih baik daripada `http://example.com/dir/index.html`.
    - Jangan gunakan tautan penyingkat (shortener) URL.
- Gunakan tautan ke "versi terbaru" daripada menautkan ke "versi tertentu": `http://example.com/dir/book/current/` lebih baik daripada `http://example.com/dir/book/v1.0.0/index.html`.
- Jika sebuah tautan memiliki sertifikat SSL yang sudah kedaluwarsa, sertifikat SSL buatan sendiri, atau masalah SSL lainnya:
    1. *Gantilah* dengan versi `http` jika memungkinkan (karena proses bypass sertifikat SSL pada perangkat genggam terbilang sulit).
    2. *Biarkan apa adanya* jika versi `http` tidak tersedia, tetapi tautan dapat diakses melalui `https` dengan mengabaikan peringatan di browser atau menambahkan pengecualian.
    3. *Hapus* jika tidak ada pilihan lain.
- Jika sebuah tautan/konten mempunyai beberapa format, tambahkan tautan terpisah dengan catatan tentang setiap format.
- Jika sebuah tautan/konten ada di berbagai tempat di Internet:
    - Gunakan tautan dengan sumber yang paling otoritatif (artinya situs web penulis lebih baik daripada situs web penyunting, yang lebih baik daripada situs web pihak ketiga).
    - Jika tautan/konten-nya merujuk ke edisi yang berbeda, dan Anda merasa edisi tersebut cukup berbeda sehingga layak untuk tetap didaftarkan, tambahkan tautan terpisah dengan menambahkan keterangan untuk masing-masing edisi (lihat [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) untuk berpartisipasi dalam diskusi tentang pemformatan).
- Utamakan komit atomik (satu komit per-penambahan/penghapusan/modifikasi) daripada komit yang lebih besar. Tidak perlu menggabungkan komit-komit Anda sebelum mengirimkan PR. (Kami tidak memaksakan aturan ini untuk diikuti, karena ini hanya masalah kenyamanan bagi para pengelola).
- Jika buku/konten yang ingin didaftarkan atau terbitan lama, sertakan tanggal publikasi setelah judul dari konten/buku yang diusulkan.
- Sertakan nama atau nama-nama penulis (jika penulis lebih dari satu). Anda dapat menyingkat daftar penulis dengan "`et al.`".
- Jika buku belum selesai, dan masih dalam tahap pengerjaan, tambahkan keterangan "`dalam proses`" seperti yang dijelaskan [di bawah ini](#in_process).
- Jika suatu sumber merupakan sumber yang dipulihkan menggunakan [*Internet Archive's Wayback Machine*](https://web.archive.org) (atau serupa), mohon tambahkan keterangan "`terarsip`" seperti yang dijelaskan [di bawah](#archived). Akan tetapi mohon gunakan versi terbaru dan lengkap.
- Jika suatu sumber membutuhkan alamat email pengunduh/pengunjung atau membutuhkan proses pembuatan akun maka tambahkan catatan sesuai dengan bahasa yang tepat dalam tanda kurung, misalnya: `(alamat email *wajib*, tidak wajib)`.


<!----><a id="formatting"></a>
### Pemformatan

- Semua daftar tautan ditulis pada berkas `.md`. Coba pelajari sintaks [Markdown](https://guides.github.com/features/mastering-markdown/). Itu mudah!
- Semua daftar tautan dimulai dengan Indeks. Idenya adalah untuk membuat daftar dan menautkan semua bagian dan subbagian di sana. Simpan dalam urutan alfabetis.
- Bagian daftar tautan menggunakan heading level 3 (`###`), dan subbagiannya menggunakan heading level 4 (`####`).

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

- Konten dengan lebih dari satu format (Kami lebih mengutamakan satu tautan untuk semua sumber. Ketika tidak ada tautan tunggal yang bisa digunakan, maka boleh menggunakan satu tautan untuk masing-masing format. Namun, setiap tautan yang ditambahkan akan menambah beban pemeliharaan sehingga kami mencoba menghindarinya.)
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

- <a id="in_process"></a>Buku dalam proses penulisan:

    ```text
    BAIK  : * [Akan Segera Menjadi Buku yang Luar Biasa](http://example.com/book2.html) - John Doe (HTML) *( :construction: in process)*
    ```

- <a id="archived"></a>Tautan yang diarsipkan:

    ```text
    BAIK  : * [A Way-backed Interesting Book](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) *( :card_file_box: archived)*
    ```

<!----><a id="alphabetical-order"></a>
### Urutan Alfabetis

- Jika terdapat beberapa judul konten yang diawali dengan huruf yang sama, maka urutkan berdasarkan huruf kedua dari judul konten tersebut, dan seterusnya. Sebagai contoh: `aa` terlebih dahulu sebelum `ab`.
- `one two` terlebih dahulu sebelum `onetwo`

Jika Anda melihat tautan dengant urutan yang salah, mohon periksa pesan kesalahan yang diberikan oleh linter untuk mengetahui baris mana yang harus ditukar/diubah.


<!----><a id="notes"></a>
### Catatan

Meskipun dasar-dasarnya relatif sederhana, terdapat keragaman yang besar pada konten-konten yang kami daftarkan. Berikut beberapa catatan tentang bagaimana kami menangani keragaman ini.


#### Metadata

Daftar kami menyediakan kumpulan metadata minimal: judul, URL, pembuat, platform, dan catatan akses.


<!----><a id="titles"></a>
##### Judul

- Tidak menggunakan judul yang diciptakan. Kami mencoba menggunakan judul dari konten-konten yang terdaftar sebagaimana adanya; Sebisa mungkin bagi kontributor untuk tidak membuat, mengubah, mensunting, atau menulis ulang judul dari konten-konten yang didaftarkan. Kecuali jika konten-konten yang didaftarkan merupakan karya-karya lama; Jika konten-konten yang didaftarkan bertujuan untuk kepentingan sejarah (historis), menambahkan tahun perilisan atau terbit konten akan membantu pengguna untuk mengetahui apakah konten tersebut sesuai dengan yang dibutuhkan.
- Judul konten tidak boleh ditulis dengan menggunakan HURUF KAPITAL semua. Biasanya, penggunaan huruf kapital pada judul konten hanya untuk awalan kata saja, tetapi jika ragu, gunakan kapitalisasi yang sesuai dari sumbernya.
- Tidak menggunakan emoji.


##### URLs

- Kami tidak mengizinkan menggunakan tautan (URL) yang disingkat.
- Kode pelacakan harus dihapus dari URL.
- URL internasional harus diubah menjadi format yang benar (escaped). Biasanya, bilah peramban akan menampilkan ini dalam bentuk Unicode, namun, untuk menghindari kesalahan, harap menggunakan salin dan tempel (copy and paste).
- URL yang aman (`https`) selalu diutamakan daripada URL yang tidak aman (`http`) di tempat-tempat di mana HTTPS telah diimplementasikan.
- Kami tidak menyukai URL yang mengarah ke halaman web yang tidak menghosting sumber daya yang terdaftar, melainkan menunjuk ke tempat lain.


<!----><a id="creators"></a>
##### Pencipta

- Kami ingin menghargai pencipta sumber daya gratis jika perlu, termasuk penerjemah!
- Untuk karya terjemahan, penulis asli harus disebutkan. Kami rekomendasikan menggunakan [kode relator MARC](https://loc.gov/marc/relators/relaterm.html) untuk mengkredit pencipta selain penulis, seperti dalam contoh ini:

    ```markdown
    * [A Translated Book](http://example.com/book-id.html) - John Doe, `trl.:` Mike The Translator
    ```

    di sini, anotasi `trl.:` memakai kode relator MARC untuk "penerjemah".
- Gunakan koma `,` untuk memisahkan setiap nama dalam daftar penulis.
- Anda dapat mempersingkat daftar penulis dengan "`et al.`".
- Kami tidak mengizinkan tautan untuk Kreator.
- Untuk karya kompilasi atau campuran, "pencipta" mungkin memerlukan deskripsi. Misalnya, buku "GoalKicker" atau "RIP Tutorial" dikreditkan sebagai "`Dikompilasi dari dokumentasi StackOverflow`" (dalam Bahasa Inggris: `Compiled from StackOverflow documentation`).


<!----><a id="time-limited-courses-and-trials"></a>
##### Kursus dan Uji Coba dengan Batas Waktu

- Kami tidak mencantumkan konten-konten yang perlu kami hapus dalam enam bulan kedepan.
- Jika sebuah kursus mempunyai periode pendaftaran atau durasinya terbatas, kami tidak akan mencantumkannya.
- Kami tidak dapat mencantumkan konten gratis hanya untuk jangka waktu tertentu.


<!----><a id="platforms-and-access-notes"></a>
##### Platform dan Catatan Akses

- Kursus. Khususnya untuk konten kursus yang didaftarkan, platform tempat kursus tersebut berada harus ditambahkan pada keterangan konten. Hal ini karena platform kursus memiliki keterjangkauan dan model akses yang berbeda. Meskipun kami biasanya tidak akan mencantumkan konten yang memerlukan proses pendaftaran, banyak platform kursus yang tidak bisa diakses tanpa proses pembuatan/pendaftaran akun terlebih dahulu. Seperti Coursera, EdX, Udacity, dan Udemy. Ketika sebuah kursus bergantung pada suatu platform, nama platform tersebut harus dicantumkan pada keterangan konten dalam tanda kurung.
- YouTube. Kami memiliki banyak kursus yang terdiri dari daftar putar YouTube. Kami tidak mencantumkan YouTube sebagai sebuah platform, kami mencoba mencantumkan kreator YouTube, yang seringkali merupakan sub-platform.
- Video YouTube. Kami biasanya tidak mengaitkan tautan ke video YouTube individu kecuali jika video tersebut berdurasi lebih dari satu jam dan disusun seperti kursus atau tutorial. Jika ini adalah kasusnya, pastikan untuk mencatatnya dalam deskripsi PR.
- Leanpub. Leanpub menyediakan buku dengan berbagai model akses. Terkadang sebuah buku bisa dibaca tanpa registrasi; terkadang sebuah buku memerlukan akun Leanpub untuk bisa mengaksesnya secara gratis. Mengingat kualitas buku dan campuran serta kelenturan model akses Leanpub, kami mengizinkan penulisan yang terakhir dengan catatan akses `*(Akun Leanpub atau alamat email valid diminta)*`


<!----><a id="genres"></a>
#### Genre

Aturan pertama dalam menentukan genre mana sebuah konten adalah dengan melihat bagaimana isi dari konten tersebut. Jika konten tersebut mengatakan dirinya sebagai buku, bisa jadi konten tersebut adalah buku.


<!----><a id="genres-we-dont-list"></a>
##### Genre yang tidak kami cantumkan

Karena Internet sangat luas, kami tidak mendaftarkan konten dengan genre:

- blog
- postingan blog
- artikel
- situs web (kecuali yang meng-host BANYAK item yang kami daftarkan).
- video yang bukan kursus atau screencasts.
- bab buku
- sampel dari buku
- saluran IRC atau Telegram
- Slacks atau berlangganan email (Slacks or mailing lists)

Panduan untuk daftar konten-konten pemrograman kompetitif kami tidak seketat ini. Ruang lingkup repositori ini ditentukan oleh komunitas; jika Anda ingin menyarankan perubahan atau penambahan pada ruang lingkup yang sekarang, harap gunakan isu (issue) untuk memberikan saran.


<!----><a id="books-vs-other-stuff"></a>
##### Buku vs. Barang Lainnya

Kami tidak rewel tentang kebukuan. Berikut adalah beberapa atribut yang menandakan bahwa konten yang didaftarkan adalah sebuah buku:

- memiliki ISBN (Nomor Buku Standar Internasional)
- memiliki Daftar Isi
- ada versi yang dapat diunduh, terutama ePub
- memiliki edisi
- tidak tergantung pada video atau konten interaktif
- mencoba untuk mencakup topik secara komprehensif
- bersifat mandiri

Terdapat banyak buku yang kami daftarkan tidak memiliki atribut-atribut ini; Hal ini kembali ke konteks dari konten yang didaftarkan.


<!----><a id="books-vs-courses"></a>
##### Buku vs. Kursus

Terkadang ini sulit untuk dibedakan!

Kursus sering kali memiliki buku teks terkait, yang akan kami daftarkan dalam daftar buku kami. Kursus memiliki materi pembelajaran, latihan, tes, catatan atau alat bantu pembelajaran lainnya. Materi pembelajaran tunggal atau video tunggal bukan sebuah kursus. Slide persentasi (biasanya berupa PowerPoint) bukan sebuah kursus.


<!----><a id="interactive-tutorials-vs-other-stuff"></a>
##### Tutorial Interaktif vs. Hal-hal lain

Jika Anda dapat mencetaknya dan isi tidak berubah, maka itu bukan Tutorial Interaktif.


<!----><a id="automation"></a>
### Otomatisasi

- Proses validasi aturan-aturan tulisan/pemformatan dilakukan secara otomatis oleh [GitHub Actions](https://github.com/features/actions) dengan menggunakan [fpb-lint](https://github.com/vhf/free-programming-books-lint) (lihat [`.github/workflows/fpb-lint.yml`](../.github/workflows/fpb-lint.yml)).
- Proses validasi URL menggunakan [awesome_bot](https://github.com/dkhamsing/awesome_bot).
- Untuk menjalankan proses validasi URL, *lakukan commit* yang mencatumkan pesan `check_urls=berkas_yang_akan_dicek`:

    ```properties
    check_urls=free-programming-books.md free-programming-books-id.md
    ```

- Anda dapat memvalidasi URL banyak berkas dengan menggunakan spasi sebagai pemisah masing-masing berkas.
- Jika Anda memvalidasi URL untuk banyak berkas, hasil validasi yang ditampilkan merupakan hasil validasi dari berkas terakhir. Sehingga, jika proses validasi berhasil, mohon untuk memeriksa log dari proses validasi pada Pull Request  Anda dengan mengklik "Show all checks" -> "Details".
