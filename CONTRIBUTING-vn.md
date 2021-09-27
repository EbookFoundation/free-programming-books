*Đọc bằng ngôn ngữ khác: [English](CONTRIBUTING.md), [Français](CONTRIBUTING-fr.md), [Español](CONTRIBUTING-es.md), [体中文](CONTRIBUTING-zh.md), [繁體中文](CONTRIBUTING-zh-TW.md), [فارسی](CONTRIBUTING-fa_IR.md).*

Bản dịch Tiếng Việt:

* Bản dịch này mục đích để khuyến khích các bạn đóng góp vào dự án sách, khóa học miễn phí này mà chưa thể đọc tốt được Tiếng Anh. Mình cũng mong Việt Nam có thể có nhiều hơn những khóa học, những cuốn sách miễn phí về lập trình để giúp các bạn trẻ hiện nay có thể sớm tiếp cận với công nghệ, phát triển sớm được niềm đam mê của bản thân.

* Mình đã cố gắng dịch cho chính xác, nhưng cũng khó có thể tránh khỏi sai sót, có một số  mong các bạn lượng thứ.

* Mọi ý kiến, đóng góp về bản dịch, vui lòng [tạo một issue mới](/issues/new) hoặc bạn có thể chỉnh sửa và tạo Pull Request.

---

## Giấy Phép Thỏa Thuận Cộng Tác Viên
Bằng cách đóng góp, bạn đồng ý với [LICENSE](https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE) của repo này.

## Quy Tắc Ứng Xử của Cộng Tác Viên
Bằng cách đóng góp, bạn đồng ý tôn trọng [Quy Tắc Ứng Xử](https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT.md) của repo này.

## Tóm Tắt
1. "Một liên kết để tải một cuốn sách" không có nghĩa nó là một cuốn sách *miễn phí*. Vui lòng chỉ đóng góp nội dung miễn phí. Đảm bảo rằng nó là miễn phí. Chúng tôi không chấp nhận các liên kết đến các trang có *yêu cầu bắt buộc* nhập địa chỉ email để nhận sách.
2. Bạn không cần phải biết về Git: nếu bạn tìm được thứ gì đó thú vị *và chưa có trong kho lưu trữ này*, vui lòng mở một [Issue](https://github.com/EbookFoundation/free-programming-books/issues) với các đề xuất mà bạn muốn đóng góp.
    - Nếu bạn biết Git, vui lòng Fork repo này và gửi pull requests.
3. Chúng tôi có 5 loại tài liệu, bạn có thể chọn một trong những cái dưới đây:

    - *Sách* : PDF, HTML, ePub, một trang web dựa trên gitbook.io, a Git repo, vv.
    - *Khóa Học* : Một khóa học là một tài liệu học tập, không phải là sách. [Đây là một khóa học](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Hướng Dẫn Tương Tác* : Một trang web cho phép người dùng gõ Code và chạy chương trình dựa trên kết quả và đánh giá. Ví dụ: [Try Haskell](http://tryhaskell.org), [Try Github](http://try.github.io).
    - *Podcasts and Screencasts* : Podcasts và screencasts.
    - *Đặt Vấn Đề & Cuộc Thi Lập Trình* : Trang web hoặc phần mềm cho phép bạn đánh giá kỹ năng lập trình của mình bằng cách giải quyết các vấn đề đơn giản hoặc phức tạp, có hoặc không có đánh giá Code, có hoặc không so sánh kết quả với những người khác.

4. Đảm bảo tuân thủ theo [những nguyên tắc bên dưới](#Những Nguyên Tắc) và đảm bảo sử dụng đúng những [định dạng Markdown](#Định Dạng).

5. Travis CI sẽ chạy các test để đảm bảo danh sách của bạn được sắp xếp theo thứ tự bảng chữ cái và các quy tắc định dạng được tuân thủ. Đảm bảo kiểm tra xem các thay đổi của bạn có vượt qua các bài test hay không.

### Những Nguyên Tắc
- đảm bảo rằng một cuốn sách là miễn phí. Kiểm tra kỹ nếu cần. Nó sẽ giúp ích cho các quản trị viên nếu bạn nhận xét trong phần PR về lý do tại sao bạn cho rằng cuốn sách là miễn phí.
- chúng tôi không chấp nhận các tệp được lưu trữ trên google drive, dropbox, mega, scribd, issu và các nền tảng tải lên tệp tương tự khác.
- chèn các liên kết của bạn theo thứ tự bảng chữ cái. Nếu bạn thấy một liên kết bị đặt sai vị trí, vui lòng sắp xếp lại nó và gửi một PR.
- sử dụng liên kết với nguồn có thẩm quyền nhất (có nghĩa là trang web của tác giả tốt hơn trang web của người biên tập tốt hơn trang web của bên thứ ba)
    + không có dịch vụ lưu trữ tệp (điều này bao gồm (nhưng không giới hạn) liên kết Dropbox và Google Drive)
- một liên kết `https` tốt hơn liên kết có giao thức `http` - miễn là chúng ở trên cùng một domain và phân phát cùng một nội dung.
- trên các miền gốc, bỏ dấu gạch chéo sau: `http://example.com` thay vì `http://example.com/`
- luôn luôn ưu tiên đường dẫn ngắn: `http://example.com/dir/` tốt hơn là `http://example.com/dir/index.html`
    + không sử dụng rút gọn link
- thường ưu tiên những liên kết "mới nhất" hơn những liên kết có "phiên bản (version)": `http://example.com/dir/book/current/` tốt hơn `http://example.com/dir/book/v1.0.0/index.html`
- nếu một liên kết có chứng chỉ hết hạn như chứng chỉ tự ký / chứng chỉ SSL hoặc các vấn đề tương tự:
  1. *thay thế nó* bằng giao thức `http` nếu có thể (bởi vì việc chấp nhận các lỗi ngoại lệ có thể phức tạp trên thiết bị di động)
  2. *để nguyên* nếu không thể sử dụng `http` nhưng liên kết có thể truy cập được thông qua `https` bằng cách thêm một ngoại lệ vào trình duyệt hoặc có thể bỏ qua cảnh báo
  3. *xóa nó đi* nếu không thể làm gì khác
- nếu một liên kết tồn tại ở nhiều định dạng, hãy thêm một liên kết riêng với ghi chú về từng định dạng
- nếu một tài liệu tồn tại ở những nơi khác nhau trên Internet
    + sử dụng liên kết với nguồn có thẩm quyền nhất (có nghĩa là trang web của tác giả tốt hơn trang web của người biên tập và tốt hơn trang web của bên thứ ba)
    + nếu chúng liên kết đến các ấn bản khác nhau và bạn đánh giá các ấn bản này đủ khác nhau để có giá trị giữ chúng, hãy thêm một liên kết riêng với ghi chú về từng ấn bản (xem [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) để đóng góp vào cuộc thảo luận về định dạng.)
- ưu tiên các commit nhỏ (atomic commits - một commit chỉ có thêm, xóa hoặc sửa) hơn các commit lớn. Không cần phải giấu giếm các commits của bạn trước khi gửi PR. (Chúng tôi sẽ không bao giờ thực thi những thứ này vì nó thuận tiện sau này cho người bảo trì)
- nếu sách cũ hơn, hãy bao gồm ngày xuất bản cùng với tên sách.
- bao gồm tên tác giả hoặc tên nếu thích hợp. Bạn có thể rút ngắn danh sách tác giả với "et al."
- nếu cuốn sách chưa hoàn thành và vẫn đang được hoàn thiện, hãy thêm ký hiệu "đang xử lý", như được mô tả [dưới đây.](#in_process)
- nếu địa chỉ email hoặc thiết lập tài khoản được yêu cầu trước khi kích hoạt tải xuống, hãy thêm ghi chú phù hợp với ngôn ngữ trong ngoặc đơn, ví dụ: `(địa chỉ email *được yêu cầu*, không bắt buộc)`

### Định Dạng
- Tất cả danh sách đều là tệp `.md`. Cố gắng học các cú pháp [Markdown](https://guides.github.com/features/mastering-markdown/). Nó rất đơn giản!
- Tất cả các danh sách bắt đầu bằng một Chỉ mục. Ý tưởng là liệt kê và liên kết tất cả các phần và tiểu mục ở đó. Giữ nó theo thứ tự bảng chữ cái.
- Các phần đang sử dụng tiêu đề cấp 3 (`###`) và các tiểu mục là tiêu đề cấp 4 (`####`).

Ý tưởng là phải có
- `2` dòng trống giữa liên kết cuối cùng và phần mới
- `1` dòng trống giữa tiêu đề và liên kết đầu tiên của phần của nó
- `0` dòng trống giữa hai liên kết
- `1` dòng trống ở cuối mỗi tệp` .md`

Ví dụ:

    [...]
    * [Một cuốn sách tuyệt vời](http://example.com/example.html)
                                    (dòng trống)
                                    (dòng trống)
    ### Ví dụ
                                    (dòng trống)
    * [Một cuốn sách tuyệt vời khác](http://example.com/book.html)
    * [Một số sách khác](http://example.com/other.html)

- Không đặt dấu cách giữa `]` và `(`:

```
Tệ : * [Một cuốn sách tuyệt vời khác] (http://example.com/book.html)
Tốt: * [Một cuốn sách tuyệt vời khác](http://example.com/book.html)
```

- Nếu bao gồm tác giả, hãy sử dụng ` - ` (dấu gạch ngang được bao quanh bởi các khoảng trắng):

```
Tệ : * [Một cuốn sách tuyệt vời khác](http://example.com/book.html)- John Doe
Tốt: * [Một cuốn sách tuyệt vời khác](http://example.com/book.html) - John Doe
```

- Đặt một khoảng trắng giữa liên kết và định dạng của nó:

```
Tệ : * [Một cuốn sách rất tuyệt vời](https://example.org/book.pdf)(PDF)
Tốt: * [Một cuốn sách rất tuyệt vời](https://example.org/book.pdf) (PDF)
```

- Tác giả đặt trước định dạng:

```
Tệ : * [Một cuốn sách rất tuyệt vời](https://example.org/book.pdf)- (PDF) Jane Roe
Tốt: * [Một cuốn sách rất tuyệt vời](https://example.org/book.pdf) - Jane Roe (PDF)
```

- Nhiều định dạng:

```
Tệ : * [Một cuốn sách tuyệt vời khác](http://example.com/)- John Doe (HTML)
Tệ : * [Một cuốn sách tuyệt vời khác](https://downloads.example.org/book.html)- John Doe (download site)
Tốt: * [Một cuốn sách tuyệt vời khác](http://example.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
```

- Bao gồm năm xuất bản trong tiêu đề cho các sách cũ hơn:

```
Tệ : * [Một cuốn sách rất tuyệt vời](https://example.org/book.html) - Jane Roe - 1970
Tốt: * [Một cuốn sách rất tuyệt vời (1970)](https://example.org/book.html) - Jane Roe
```

<a name="in_process"></a>
- Sách đang trong quá trình viết:

```
Tốt: * [Sách sẽ sớm trở nên tuyệt vời](http://example.com/book2.html) - John Doe (HTML) (:construction: *in process*)
```

### Ghi Chú

Mặc dù những điều cơ bản tương đối đơn giản, nhưng có sự đa dạng lớn trong các nguồn mà chúng tôi liệt kê. Dưới đây là một số lưu ý về cách chúng ta phân loại những sự đa dạng này.

#### Metadata

Danh sách của chúng tôi cung cấp một metadata: tiêu đề, URL, người tạo, nền tảng và ghi chú truy cập.

##### Tiêu Đề

- Không được chế ra tiêu đề. Chúng tôi cố gắng lấy các tiêu đề từ chính các nguồn tài liệu đó; những người đóng góp được khuyến cáo không chế ra tiêu đề hoặc chỉnh sửa chúng nếu điều này có thể tránh được. Một ngoại lệ là đối với các tác phẩm cũ hơn; nếu họ chủ yếu quan tâm đến lịch sử, thêm số năm vào trong dấu ngoặc đơn nằm trong tiêu đề sẽ giúp người dùng biết liệu họ có quan tâm hay không.
- Không sử dụng tiêu đề ALLCAPS (tiêu đề sử dụng toàn bộ bằng chữ In Hoa). Thông thường, viết hoa tiêu đề là phù hợp, nhưng khi không chắc chắn, hãy sử dụng chữ viết hoa từ nguồn.

##### URLs

- Chúng tôi không cho phép các URL rút gọn.
- Mã theo dõi phải được xóa khỏi URL.
- URL quốc tế phải được thoát. Các thanh trình duyệt thường hiển thị chúng thành Unicode, nhưng vui lòng sử dụng sao chép và dán.
- Các URL an toàn (https) luôn được ưu tiên hơn các url không an toàn (http) nơi https đã được triển khai.
- Chúng tôi không thích các URL trỏ đến các trang web không lưu trữ tài liệu được liệt kê, mà thay vào đó trỏ đến nơi khác.

##### Người Sáng Tạo

- Chúng tôi muốn ghi công những người tạo ra các tài liệu miễn phí nếu thích hợp, bao gồm cả những người dịch!
- Đối với các tác phẩm đã dịch, tác giả gốc nên được ghi công.
- Chúng tôi không cho phép liên kết bởi Người sáng tạo.
- Đối với các tác phẩm tổng hợp hoặc phối lại, "người sáng tạo" có thể cần mô tả. Ví dụ: sách "GoalKicker" được ghi là "Được tổng hợp từ tài liệu StackOverflow"

##### Nền Tảng và Ghi Chú Truy Cập

- Các khóa học. Đặc biệt đối với danh sách khóa học của chúng tôi, nền tảng là một phần quan trọng của mô tả tài liệu. Điều này là do các nền tảng khóa học có khả năng chi trả và mô hình truy cập khác nhau. Mặc dù chúng tôi thường không liệt kê một cuốn sách yêu cầu đăng ký, nhưng nhiều nền tảng khóa học có khả năng chi trả không hoạt động nếu không có một số loại tài khoản. Các nền tảng khóa học ví dụ bao gồm Coursera, EdX, Udacity và Udemy. Khi một khóa học phụ thuộc vào một nền tảng, tên nền tảng phải được liệt kê trong ngoặc đơn.
- YouTube. Chúng tôi có nhiều khóa học bao gồm các danh sách phát trên YouTube. Chúng tôi không cho rằng Youtube như một nền tảng, chúng tôi cố gắng liệt kê người sáng tạo nội dung trên Youtube, thường là một nền tảng phụ.
- Video trên YouTube. Chúng tôi thường không có các liên kết đến các video YouTube riêng lẻ trừ khi chúng dài hơn một giờ và có cấu trúc giống như một khóa học hoặc một hướng dẫn.
- Leanpub. Leanpub lưu trữ sách với nhiều mô hình truy cập. Đôi khi một cuốn sách có thể được đọc mà không cần đăng ký; đôi khi một cuốn sách yêu cầu tài khoản Leanpub để được truy cập miễn phí. Do chất lượng của sách và sự hỗn hợp và tính linh hoạt của các mô hình truy cập Leanpub, chúng tôi cho phép liệt kê mô hình sau cùng với ghi chú truy cập *(yêu cầu tài khoản Leanpub hoặc email hợp lệ)*

#### Thể Loại

Quy tắc đầu tiên để quyết định tài liệu thuộc danh sách nào là xem tài liệu đó mô tả thế nào. Nếu nó tự gọi nó là một cuốn sách, thì có lẽ nó là một cuốn sách.

##### Các Thể Loại chúng tôi không liệt kê

Vì Internet rất rộng lớn, chúng tôi không đưa chúng vào danh sách của mình:

- blogs
- bài đăng trên blog
- bài viết
- các trang web (ngoại trừ những nơi lưu trữ RẤT NHIỀU tài liệu mà chúng tôi liệt kê.) 
- video không phải là khóa học hoặc video truyền hình.
- các chương của cuốn sách
- các ví dụ khó từ sách
- IRC hoặc Telegram
- Slacks hoặc danh sách mail

Danh sách của chúng tôi không nghiêm ngặt về những loại trừ này. Phạm vi của repo được xác định bởi cộng đồng; nếu bạn muốn đề xuất thay đổi hoặc bổ sung, vui lòng tạo một Issue để đưa ra đề xuất.


##### Sách so với Nội dung khác

Chúng tôi không quá cầu kỳ về sách. Dưới đây là một số thuộc tính biểu thị rằng nguồn tài liệu là sách:

- nó có một ISBN
- nó có một Mục lục
- một phiên bản đã tải xuống, đặc biệt là ePub
- nó có các tái bản
- nó không phụ thuộc vào nội dung hoặc video tương tác
- nó cố gắng bao quát toàn diện một chủ đề
- nó khép kín

Có rất nhiều sách mà chúng tôi liệt kê không có các thuộc tính này; nó có thể phụ thuộc vào ngữ cảnh.


##### Sách so với các khóa học

Đôi khi chúng có thể khó phân biệt!

Các khóa học thường có sách giáo khoa liên quan, mà chúng tôi sẽ liệt kê trong danh sách sách của chúng tôi. Các khóa học có các bài giảng, bài tập, bài kiểm tra, ghi chú hoặc các hỗ trợ giáo khoa khác. Bản thân một bài giảng hoặc video không phải là một khóa học. Powerpoint không phải là một khóa học.


##### Hướng dẫn tương tác so với những thứ khác

Nếu bạn có thể in nó ra và giữ lại bản chất của nó, thì đó không phải là Hướng dẫn tương tác.


### Tự động hóa

- Việc thực thi quy tắc định dạng được tự động hóa qua [Travis CI](https://travis-ci.com) sử dụng [fpb-lint](https://github.com/vhf/free-programming-books-lint) (xem file [.travis.yml](.travis.yml))
- Sử dụng xác thực URL [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- Để kích hoạt xác thực URL, hãy push một commit bao gồm một commit message chứa `check_urls=file_to_check`:

```
check_urls=free-programming-books.md free-programming-books-en.md
```

- Bạn có thể chỉ định nhiều tệp để kiểm tra, sử dụng một khoảng trắng duy nhất để tách từng mục nhập.
- Nếu bạn chỉ định nhiều hơn một tệp, kết quả của việc build sẽ dựa trên kết quả của tệp cuối cùng được kiểm tra. Bạn nên biết rằng bạn có thể nhận được bản build thành công, vì vậy hãy đảm bảo kiểm tra build log ở cuối pull request bằng cách nhấp vào "Show all checks" -> "Details".
