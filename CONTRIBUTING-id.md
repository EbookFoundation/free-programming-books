*Read this in other languages: [中文](CONTRIBUTING-zh.md).*
*Baca dengan bahasa lain: [English](CONTRIBUTING.md), [中文](CONTRIBUTING-zh.md).*

## Persetujuan Lisensi Kontributor
Dengan berkontribusi anda menyetujui kepada [LICENSE](https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE) dari repository ini.

## Kode Etik Kontributor
Dengan berkontribusi anda menyetujui untuk mengakui Code of Conduct](https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT.md) dari repository ini

## Pendeknya
1. "Link ke buku yang mudah di unduh" bukan selalu link ke buku yang *gratis*. Mohon untuk hanya berkontribusi dengan konten gratis. Pastikan konten itu gratis. Kami tidak menerima link ke halaman yang *memerlukan* email aktif untuk mendapatkan buku, tetapi kami menerima halaman yang menanyakan nya.
2. Anda tidak perlu mengetauhi Git: jika anda menemukan sesuatu yang menarik dan yang *belum ada di repo ini*, mohon membuka sebuah [Issue](https://github.com/EbookFoundation/free-programming-books/issues) dengan tautan proposisi anda.
    - Jika anda tahu Git, mohon Fork repo ini dan mengirim pull request.
3. Kami mempunyai 5 jenis daftar. Pilih satu yang benar:

    - *Buku* : PDF, HTML, ePub, halaman berbasis gitbook.io, Git repo, etc.
    - *Kursus* : Kursus adalah sebuah materi belajar yang bukanlah sebuah buku. [Ini adalah kursus](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Tutorial Interaktif* : Website Interaktif yang memungkinkan pengguna untuk mengetik kode atau perintah dan mengevaluasi hasil (dengan *evaluasi* kami tidak bermaksud "nilai"). e.g.: [Try Haskell](http://tryhaskell.org), [Try Github](http://try.github.io).
    - *Podcast dan screencast* : Podcast dan screencast.
    - *Set Masalah & Programming Kompetitif* : Website atau software yang memungkinkan anda untuk menilai skill programming anda dengan menyelesaikan masalah simpel sampai kompleks, dengan atau tidak dengan Ulasan nilai, dengan atau tidak dengan perbandingan hasil dengan pengguna lain.
    
4. Pastikan untuk mengikuti [pedoman dibawah](#pedoman) dan mengikuti [pemformatan markdown](#formatting) dari files.

5. Travis CI akan menjalankan uji untuk memastikan daftar anda sudah terabjadkan dan sudah mengikuti aturan formatting. Pastikan untuk memeriksa apakah perubahan anda lolos uji.

### Pedoman
- pastikan buku itu gratis. Periksa ulang jika diperlukan. Ini membantu admin jika anda memberi komen di PR atas mengapa anda berpikir buku itu gratis.
- kami tidak menerima file yang di host di google drive, dropbox, mega, scribd, issuu dan platform upload file yang mirip lainya
- masukan link anda dalam urutan alfabetikal. Jika anda melihat link yang salah tempat, mohon mengurutkan ulang dan kirimkan sebuah PR
- gunakan link dengan sumber autoritatif paling besar (berarti website autor lebih baik daripada website editor dan website pihak ketiga)
    + tidak ada service file hosting (ini termasuk (tetapi tidak terbatas kepada) link Dropbox dan Google Drive)
- selalu pilih link `https` daripada `http` -- selama mereka dalam satu domain dan memiliki konten yang sama
- dalam domain root, hilangkan garis miring tertinggal: `http://contoh.com` daripada `http://contoh.com/`
- selalu pilih link yang lebih pendek: `http://contoh.com/dir/` lebih baik daripada `http://contoh.com/dir/index.html`
    + tidak ada link pemendek URL
- biasakan memilih link yang "current" atau "sekarang" daripada yang ber "versi": `http://contoh.com/dir/buku/current` lebih baik daripada `http://contoh.com/dir/buku/v1.0.0/index.html`
- jika link memiliki sertifikat/sertifikat sendiri/SSL kadaluarsa atau jenis lain:
  1. *ganti link* dengan versi `http` nya jika memungkinkan (karena menerima pengecualian bisa kompleks di gawai mobile)
  2. *tinggalkan link* jika tidak ada versi `http` tetapi link masih bisa di akses via `https` dengan menambahkan pengecualian ke browser atau mengabaikan peringatanya
  3. jika tidak, *hapus link*
- jika link hadir dalam berbagai format, tambahkan link yang terpisah dengan catatan tentang setiap format
- jika materi hadir di tempat berbeda di internet
    + gunakan link dengan autoritatif terbesar (berarti website autor lebih baik daripada website editor dan lebih baik daripada website pihak ketiga)
    + jika mereka melink ke edisi berbeda dan anda melihat edisi ini cukup berbeda dan berhak disimpan, tambahkan link terpisah dengan catatan tentang setiap edisi (lihat [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) untuk berkontribusi dalam diskusi formatting.)
- pilih commit atomic (satu commit dengan penambahan/pengurangan/modifikasi) daripada commit yang lebih besar. Tidak perlu menjepit commit anda sebelum mengirimkan PR. (kami tidak akan melaksanakan aturan ini karena ini hanyalah masalah kenyamanan untuk penjaga)
- jika buku sudah tua, masukan tanggal publikasi di judul.
- masukan nama autor dimana yang sesuai. Anda bisa memendekan daftar nama autor dengan "et al."
- jika buku belum selesai, dan sedang dalam pengerjaan, tambahkan notasi "dalam pengerjaan", seperti yang dikatakan di [bawah](#dalampengerjaan)
- jika alamat email atau pendaftaran akun diminta sebelum mengunduh diaktifkan, tambahkan catatan sesuai di tanda kurung, e.g : `alamat email *diminta*, tidak diwajibkan`

### Formatting
- Semua daftar adalah file `.md`. Coba untuk belajar syntax [[Markdown](https://guides.github.com/features/mastering-markdown/). itu simpel!
- Semua daftar dimulai dengan Index. Idenya adalah untuk mendaftar dan menyambunkan section dan subsection disana. Jagalah dalam bentuk alfabetikal
- Section menggunakan judul tingkat ke-3 (`###`), dan subsection adalah judul tingkat ke-4 (`####`).

Idenya adalah untuk memiliki
- `2` baris kosong diantara link terakhir dan section baru
- `1` baris kosong diantara judul dan link pertama dari section tersebut
- `0` baris kosong diantara dua link
- `1` baris kosong di akhir dari setiap file `.md`

Contoh:

    [...]
    * [Buku Keren](http://contoh.com/contoh.html)
                                    (blank line)
                                    (blank line)
    ### Example
                                    (blank line)
    * [Buku Keren Lagi](http://contoh.com/book.html)
    * [Buku lain](http://contoh.com/other.html)

- Jangan letakan spasi diantara `]` dan `(`:

```
BURUK : * [Buku Keren Lagi] (http://contoh.com/book.html)
BAIK  : * [Buku Keren Lagi](http://contoh.com/book.html)
```

- Jika anda memasukan nama autor, gunakan ` - ` (strip di kelilingi satu spasi)

```
BURUK : * [Buku Keren Lagi](http://contoh.com/book.html)- John Doe
BAIK  : * [Buku Keren Lagi](http://contoh.com/book.html) - John Doe
```

- Masukan spasi diantara link dan formatnya:

```
BURUK : * [Buku Keren](https://contoh.org/book.pdf)(PDF)
BAIK  : * [Buku Keren](https://contoh.org/book.pdf) (PDF)
```

- Autor diletakan sebelum format:

```
BURUK : * [Buku Keren](https://contoh.org/book.pdf)- (PDF) Jane Roe
BAIK  : * [Buku Keren](https://contoh.org/book.pdf) - Jane Roe (PDF)
```

- Bermacam-macam format:

```
BURUK : * [Buku Keren](http://contoh.com/)- John Doe (HTML)
BURUK : * [Buku Keren Lagi](https://downloads.contoh.org/book.html)- John Doe (download site)
BAIK  : * [Buku Keren Lagi](http://contoh.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.contoh.org/book.html)
```

- Masukan tahun publikasi di judul untuk buku yang lebih tua:

```
Buruk : * [Buku Keren](https://contoh.org/book.html) - Jane Roe - 1970
BAIK  : * [Buku Keren (1970)](https://contoh.org/book.html) - Jane Roe
```

<a name="dalam_pengerjaan"></a>
- buku dalam-pengerjaan:

```
BAIK  : * [Akan menjadi Buku Keren](http://contoh.com/book2.html) - John Doe (HTML) (:construction: *dalam pengerjaan*)
```

### Automation
- Pelaksanaan aturan formatting di automasi via [Travis CI](https://travis-ci.com) menggunakan [fpb-lint](https://github.com/vhf/free-programming-books-lint) (lihat [.travis.yml](.travis.yml))
-Validasi URL menggunakan [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- Untuk memulai Validasi URL, push sebuah commit yang berisi pesan commit `check_urls=file_yang_diperiksa`

```
check_urls=free-programming-books.md free-programming-books-id.md
```

- Anda boleh menyatakan lebih dari satu file untuk di periksa, gunakan spasi tunggal untuk memisah setiap masukan
- Jika anda menyatakan lebih dari satu file, hasil dari build berbasis dari hasil dari file yang diperiksa terakhir. Anda harus tahu bahwa anda mungkin mendapatkan build lolos hijau karena ini, jadi anda harus yakin untuk memeriksa log build di akhir pull request dengan mengclick di "Show all checks" - > "Details".

