*Instruksi ini dalam bahasa lain: [Deutsch](CONTRIBUTING-de.md), [English](CONTRIBUTING.md),[Español](CONTRIBUTING-es.md), [Français](CONTRIBUTING-fr.md), [简体中文](CONTRIBUTING-zh.md), [繁體中文](CONTRIBUTING-zh_TW.md), [فارسی](CONTRIBUTING-fa_IR.md), [Tiếng Việt](CONTRIBUTING-vn.md), [Русский](CONTRIBUTING-ru.md), [Português Brasileiro](CONTRIBUTING-pt_BR.md), [한국어](CONTRIBUTING-ko.md).*

## Perjanjian lisensi kontributor
Dengan kerja sama Anda, Anda menerima [lisensi](https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE) dari repositori ini.

## Kode Etik untuk Kontributor
Dengan partisipasi Anda, Anda berjanji untuk mengikuti [Kode Etik](https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT.md) dari repositori ini.

## Versi pendek
1. "Tautan untuk mengunduh buku dengan mudah" tidak selalu merupakan tautan ke buku *gratis*. Harap hanya menambahkan konten gratis. Pastikan mereka gratis. Kami tidak menerima tautan ke situs yang * mengharuskan * Anda mendaftar dengan alamat email yang berfungsi untuk mengunduh buku, tetapi kami menyambut situs yang meminta alamat email.
2. Anda tidak harus terbiasa dengan Git: Jika Anda telah menemukan sesuatu yang menarik *yang belum ada di salah satu daftar*, silakan buka [Masalah](https://github.com/EbookFoundation/free-programming-books/issues) dengan tautan yang Anda sarankan.
    - Jika Anda sudah familiar dengan Git, fork repositori dan kirim pull request.
3. Kami menyimpan 5 jenis daftar. Pastikan untuk memilih yang tepat:

    - *Buku*: PDF, HTML, ePub, halaman berdasarkan gitbook.io, repo Git, dll.
    - *Kursus*: Kursus menggambarkan materi pembelajaran yang tidak ada dalam bentuk buku. [Ini adalah kursus](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Tutorial interaktif*: Situs web interaktif yang memungkinkan pengguna memasukkan kode sumber atau perintah dan mengevaluasi hasilnya (dengan "mengevaluasi" kami tidak bermaksud "mengevaluasi"). misalnya: [Coba Haskell](http://tryhaskell.org), [Coba Github](http://try.github.io).
    - *Podcast dan Screencasts*: Podcast dan Screencasts.
    - *Kumpulan Masalah & Pemrograman Kompetitif*: Situs web atau perangkat lunak yang memberi Anda kesempatan untuk menguji keterampilan pemrograman Anda dengan memecahkan masalah sederhana atau kompleks, dengan atau tanpa tinjauan kode dan dengan atau tanpa membandingkan kinerja dengan orang lain Pengunjung situs .

4. Pastikan Anda mengikuti [Guidelines](#guidelines) dan [Markdown Formatting](#formatting) dari file.

5. GitHub Actions akan menjalankan tes untuk memastikan bahwa daftar diurutkan berdasarkan abjad dengan benar dan bahwa aturan pemformatan telah diikuti. Pastikan perubahan Anda lulus tes ini.

### Pedoman
- Pastikan sebuah buku benar-benar gratis. Periksa kembali jika perlu. Ini membantu administrator jika Anda menjelaskan dalam PR Anda mengapa menurut Anda buku tersebut gratis.
- Kami tidak merekam file yang ada di Google Drive, Dropbox, Mega, Scribd, Issuu atau platform unggahan yang sebanding.
- Masukkan tautan dalam urutan abjad. Jika Anda menemukan tautan yang salah dimasukkan, harap perbaiki pesanan dan buka PR.
- Selalu pilih tautan dari sumber otoritatif (yaitu, situs web penulis lebih baik daripada situs web editor, yang pada gilirannya akan lebih baik daripada situs web pihak ketiga)
    + tidak ada platform hosting file (termasuk tautan ke Dropbox, Google Drive, dll.)
- Tautan `https` harus selalu lebih disukai daripada tautan `http` - selama tautan tersebut mengarah ke domain dan konten yang sama.
- Garis miring harus dihapus pada domain root: `http://example.com` alih-alih `http://example.com/ `
- Selalu pilih tautan terpendek: `http://example.com/dir/` lebih baik daripada `http://example.com/dir/index.html`
    + jangan gunakan penyingkat url
- Pilih tautan ke versi terbaru alih-alih menautkan ke versi tertentu: `http://example.com/dir/book/current/` lebih baik daripada `http://example.com/dir/book/v1.0.0/index.html`
- Jika tautan menggunakan sertifikat yang kedaluwarsa atau ditandatangani sendiri atau memiliki masalah SSL lain:
  1. *ganti* dengan mitra `http` jika memungkinkan (karena mungkin sulit untuk mengizinkan pengecualian pada perangkat seluler).
  2. *biarkan apa adanya* jika versi `http` tidak tersedia, tetapi tautan dapat diakses melalui` https` dengan mengabaikan peringatan di browser atau menambahkan pengecualian.
  3. *hapus* jika tidak.
- jika ada tautan dalam format yang berbeda, tambahkan tautan terpisah dengan referensi ke setiap format
- jika sepotong konten tersedia di beberapa tempat di Internet
    + pilih tautan otoritatif
