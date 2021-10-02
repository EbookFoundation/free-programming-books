*Baca dalam bahasa lain: [Français](CONTRIBUTING-fr.md), [Español](CONTRIBUTING-es.md), [简体中文](CONTRIBUTING-zh.md), [繁體中文](CONTRIBUTING-zh_TW.md), [فارسی](CONTRIBUTING-fa_IR.md), [Tiếng Việt](CONTRIBUTING-vn.md), [Русский](CONTRIBUTING-ru.md), [Indonesia](CONTRIBUTING-id.md).*

## Perjanjian Lisensi Kontributor
Dengan berkontribusi, Anda setuju dengan [LISENSI](https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE) dari repository ini.

## Kode Etik Kontributor
Dengan berkontribusi, Anda setuju untuk menghormati [Kode Etik](https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT.md) dari repository ini.

## Secara Singkat
1. "Tautan untuk mengunduh buku dengan mudah" tidak selalu merupakan tautan ke buku *gratis*. Harap hanya berkontribusi konten gratis. Pastikan gratis. Kami tidak menerima tautan ke halaman yang *memerlukan* alamat email yang berfungsi untuk mendapatkan buku, tetapi kami menerima daftar yang memintanya.
2. Anda tidak perlu tahu Git: jika Anda menemukan sesuatu yang menarik yang *belum ada di repo ini*, silakan buka [Issue](https://github.com/EbookFoundation/free-programming-books/issues) dengan proposisi tautan Anda.
    - Jika Anda tahu Git, silakan Fork repo dan kirim permintaan *pull request*.
3. Kami memiliki 5 jenis daftar. Pilih yang tepat:

    - *Buku* : PDF, HTML, ePub, situs berbasis gitbook.io, repo Git, dll.
    - *Kursus* : Kursus adalah bahan ajar yang bukan buku. [Ini adalah kursus](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Tutorial Interaktif* : Situs web interaktif yang memungkinkan pengguna mengetik kode atau perintah dan mengevaluasi hasilnya (dengan "mengevaluasi" kami tidak bermaksud "menilai"). misalnya.: [Try Haskell](http://tryhaskell.org), [Try Github](http://try.github.io).
    - *Podcast dan Screencasts* : Podcast dan screencast.
    - *Rangkaian Masalah & Pemrograman Kompetitif* : Situs web atau perangkat lunak yang memungkinkan Anda menilai keterampilan pemrograman Anda dengan memecahkan masalah sederhana atau kompleks, dengan atau tanpa tinjauan kode, dengan atau tanpa membandingkan hasilnya dengan pengguna lain.

4. Pastikan untuk mengikuti [panduan di bawah](#guidelines) dan hormati [Pemformatan file Markdown](#formatting).

5. GitHub Actions akan menjalankan tes untuk memastikan daftar Anda diurutkan menurut abjad dan aturan pemformatan diikuti. Pastikan untuk memeriksa bahwa perubahan Anda lulus tes.

### Pedoman
- pastikan buku gratis. Periksa kembali jika diperlukan. Ini membantu admin jika Anda berkomentar di PR mengapa menurut Anda buku itu gratis.
- kami tidak menerima file yang dihosting di google drive, dropbox, mega, scribd, issuu, dan platform unggah file serupa lainnya
- masukkan tautan Anda dalam urutan abjad. Jika Anda melihat tautan yang salah tempat, harap ulangi dan kirimkan PR
- gunakan tautan dengan sumber paling otoritatif (artinya situs web penulis lebih baik daripada situs web editor, yang lebih baik daripada situs web pihak ketiga)
    + tidak ada layanan hosting file (ini termasuk (tetapi tidak terbatas pada) tautan Dropbox dan Google Drive)
- selalu lebih suka tautan `https` daripada tautan `http` -- selama mereka berada di domain yang sama dan menyajikan konten yang sama
- pada domain root, hapus garis miring: `http://example.com` alih-alih `http://example.com/`
- selalu lebih suka tautan terpendek: `http://example.com/dir/` lebih baik daripada `http://example.com/dir/index.html`
     + tidak ada tautan penyingkat URL
- biasanya lebih suka tautan "saat ini" daripada tautan "versi": `http://example.com/dir/book/current/` ini lebih baik dari `http://example.com/dir/book/v1.0.0/index.html`
- jika tautan memiliki sertifikat kedaluwarsa/sertifikat yang ditandatangani sendiri/masalah SSL dalam bentuk apa pun:
  1. *ganti* dengan mitra `http` jika memungkinkan (karena menerima pengecualian dapat menjadi rumit pada perangkat seluler).
   2. *biarkan* jika tidak ada versi `http` yang tersedia tetapi tautan masih dapat diakses melalui `https` dengan menambahkan pengecualian ke browser atau mengabaikan peringatan.
   3. *hapus* jika tidak.
- jika ada tautan dalam berbagai format, tambahkan tautan terpisah dengan catatan tentang setiap format
- jika sumber daya ada di tempat yang berbeda di Internet
     + gunakan tautan dengan sumber paling otoritatif (artinya situs web penulis lebih baik daripada situs web editor lebih baik daripada situs web pihak ketiga)
     + jika mereka menautkan ke edisi yang berbeda dan Anda menilai edisi ini cukup berbeda sehingga layak untuk disimpan, tambahkan tautan terpisah dengan catatan tentang setiap edisi (lihat [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) untuk berkontribusi pada diskusi tentang pemformatan.)
- lebih suka komit atom (satu komit dengan penambahan/penghapusan/modifikasi) daripada komit yang lebih besar. Tidak perlu menekan komitmen Anda sebelum mengirimkan PR. (Kami tidak akan pernah menegakkan aturan ini karena ini hanya masalah kenyamanan bagi pengelola)
- jika buku lebih tua, sertakan tanggal penerbitan dengan judul.
- sertakan nama penulis atau nama yang sesuai. Anda dapat mempersingkat daftar penulis dengan "et al."
- jika buku belum selesai, dan masih dalam pengerjaan, tambahkan notasi "dalam proses", seperti yang dijelaskan [di bawah ini.](#in_process)
- jika alamat email atau pengaturan akun diminta sebelum pengunduhan diaktifkan, tambahkan catatan bahasa yang sesuai dalam tanda kurung, misalnya: `(alamat email *diminta*, tidak wajib)`

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

    [...]
    * [Contoh Buku](http://example.com/example.html)
                                    (baris kosong)
                                    (baris kosong)
    ### Contoh
                                    (baris kosong)
    * [Contoh Buku Lainnya](http://example.com/book.html)
    * [Beberapa Buku Lain](http://example.com/other.html)

- Jangan gunakan spasi diantara `]` dan `(`:

```
BURUK : * [Contoh Buku Lainnya] (http://example.com/book.html)
BAIK  : * [Contoh Buku Lainnya](http://example.com/book.html)
```

- Jika Anda menyertakan penulis, gunakan ` - ` (tanda hubung yang dikelilingi oleh satu spasi):

```
BURUK : * [Contoh Buku Lainnya](http://example.com/book.html)- John Doe
BAIK  : * [Contoh Buku Lainnya](http://example.com/book.html) - John Doe
```

- Letakkan satu spasi di antara tautan dan formatnya:

```
BURUK : * [Buku yang Sangat Bagus](https://example.org/book.pdf)(PDF)
BAIK  : * [Buku yang Sangat Bagus](https://example.org/book.pdf) (PDF)
```

- Penulis diletakan sebelum format file:

```
BURUK : * [Buku yang Sangat Bagus](https://example.org/book.pdf)- (PDF) Jane Roe
BAIK  : * [Buku yang Sangat Bagus](https://example.org/book.pdf) - Jane Roe (PDF)
```

- Format lebih dari satu:

```
BURUK : * [Contoh Buku Lainnya](http://example.com/)- John Doe (HTML)
BURUK : * [Contoh Buku Lainnya](https://downloads.example.org/book.html)- John Doe (situs download)
BAIK  : * [Contoh Buku Lainnya](http://example.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
```

- Cantumkan tahun penerbitan dalam judul buku lama:

```
BURUK : * [Buku yang Sangat Bagus](https://example.org/book.html) - Jane Roe - 1970
BAIK  : * [Buku yang Sangat Bagus (1970)](https://example.org/book.html) - Jane Roe
```

<a name="in_process"></a>
- Buku dalam proses:

```
BAIK  : * [Akan Segera Menjadi Buku yang Luar Biasa](http://example.com/book2.html) - John Doe (HTML) (:construction: *in process*)
```

### Catatan

Meskipun dasar-dasarnya relatif sederhana, ada keragaman besar dalam sumber daya yang kami daftarkan. Berikut adalah beberapa catatan tentang bagaimana kita menghadapi keragaman ini.

#### Metadata

Daftar kami menyediakan kumpulan metadata minimal: judul, URL, pembuat, platform, dan catatan akses.

##### Judul

- Tidak ada judul yang diciptakan. Kami mencoba mengambil judul dari sumber itu sendiri; kontributor diperingatkan untuk tidak membuat judul atau menggunakannya secara editorial jika hal ini dapat dihindari. Pengecualian adalah untuk karya yang lebih tua; jika mereka terutama memiliki minat historis, satu tahun dalam tanda kurung yang ditambahkan ke judul membantu pengguna mengetahui apakah mereka menarik.
- Tidak ada judul SEMUANYA KAPITAL. Biasanya judul kasus sesuai, tetapi jika ragu gunakan kapitalisasi dari sumbernya

##### URL

- Kami tidak mengizinkan URL yang dipersingkat.
- Kode pelacakan harus dihapus dari URL.
- URL internasional harus diloloskan. Bilah peramban biasanya merender ini ke Unicode, tetapi gunakan salin dan tempel.
- URL aman (https) selalu lebih disukai daripada url tidak aman (http) di mana https telah diterapkan.
- Kami tidak menyukai URL yang mengarah ke halaman web yang tidak menghosting sumber daya yang terdaftar, melainkan menunjuk ke tempat lain.

##### Pencipta

- Kami ingin menghargai pencipta sumber daya gratis jika perlu, termasuk penerjemah!
- Untuk karya terjemahan penulis asli harus dikreditkan.
- Kami tidak mengizinkan tautan untuk Kreator.
- Untuk karya kompilasi atau remix, "pencipta" mungkin memerlukan deskripsi. Misalnya, buku "GoalKicker" dikreditkan sebagai "Dikompilasi dari dokumentasi StackOverflow"

##### Platform dan Catatan Akses

- Kursus. Khusus untuk daftar kursus kami, platform merupakan bagian penting dari deskripsi sumber daya. Ini karena platform kursus memiliki keterjangkauan dan model akses yang berbeda. Meskipun kami biasanya tidak akan mencantumkan buku yang memerlukan pendaftaran, banyak platform kursus memiliki keterjangkauan yang tidak berfungsi tanpa semacam akun. Contoh platform kursus termasuk Coursera, EdX, Udacity , dan Udemy. Jika kursus bergantung pada platform, nama platform harus dicantumkan dalam tanda kurung.
- Youtube. Kami memiliki banyak kursus yang terdiri dari daftar putar YouTube. Kami tidak mencantumkan Youtube sebagai platform, kami mencoba mencantumkan pembuat Youtube, yang seringkali merupakan sub-platform.
- Video Youtube. Kami biasanya tidak menautkan ke video YouTube individu kecuali jika durasinya lebih dari satu jam dan terstruktur seperti kursus atau tutorial.
- Leanpub. Leanpub menyelenggarakan buku dengan berbagai model akses. Terkadang sebuah buku dapat dibaca tanpa registrasi; terkadang sebuah buku memerlukan akun Leanpub untuk akses gratis. Mengingat kualitas buku dan campuran dan fluiditas model akses Leanpub, kami mengizinkan daftar yang terakhir dengan catatan akses *(Akun Leanpub atau email yang valid diminta)*

#### Genre

Aturan pertama dalam memutuskan daftar mana yang termasuk dalam sumber daya adalah melihat bagaimana sumber daya itu menggambarkan dirinya sendiri. Jika itu menyebut dirinya sebuah buku, maka mungkin itu adalah sebuah buku.

##### Genre yang tidak kami cantumkan

Karena Internet sangat luas, kami tidak memasukkan dalam daftar kami:

- blog
- postingan blog
- artikel
- situs web (kecuali yang menghosting BANYAK item yang kami daftarkan.)
- video yang bukan kursus atau screencasts.
- bab buku
- sampel penggoda dari buku
- Saluran IRC atau Telegram
- Celana panjang atau milis

Daftar pemrograman kompetitif kami tidak seketat pengecualian ini. Lingkup repo ditentukan oleh komunitas; jika Anda ingin menyarankan perubahan atau penambahan ruang lingkup, silakan gunakan masalah untuk membuat saran.


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

##### Buku vs. Kursus

Terkadang ini sulit untuk dibedakan!

Kursus sering kali memiliki buku teks terkait, yang akan kami daftarkan dalam daftar buku kami. Kursus memiliki kuliah, latihan, tes, catatan atau alat bantu didaktik lainnya. Sebuah kuliah atau video dengan sendirinya bukanlah sebuah kursus. Sebuah powerpoint bukanlah kursus.

##### Tutorial Interaktif vs. Hal-hal lain

Jika Anda dapat mencetaknya dan mempertahankan esensinya, itu bukan Tutorial Interaktif.


### Otomatisasi

- Pemformatan penegakan aturan otomatis melalui [GitHub Actions](https://github.com/features/actions) gunakan [fpb-lint](https://github.com/vhf/free-programming-books-lint) (lihat [.github/workflows/fpb-lint.yml](.github/workflows/fpb-lint.yml))
- Validasi URL menggunakan [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- Untuk memicu validasi URL, *push commit* yang menyertakan pesan komit yang berisi `check_urls=file_to_check`:

```
check_urls=free-programming-books.md free-programming-books-en.md
```

- Anda dapat menentukan lebih dari satu file untuk diperiksa, menggunakan satu spasi untuk memisahkan setiap entri.
- Jika Anda menentukan lebih dari satu file, hasil build didasarkan pada hasil file terakhir yang diperiksa. Anda harus menyadari bahwa Anda dapat melewati build hijau karena hal ini, jadi pastikan untuk memeriksa log build di akhir pull request dengan mengklik "Show all checks" -> "Details".
