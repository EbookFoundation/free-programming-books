*[このドキュメントを別の言語で表示するには]（README.md＃translations）*


## 貢献者ライセンス同意書

このプロジェクトの貢献者は、リポジトリの[利用規約]（../LICENSE）に同意するものと見なされます。


## 貢献者行道規範

このリポジトリの貢献として、すべての貢献者はこの[行動規範]（CODE_OF_CONDUCT-ja.md）に同意したものと見なされます。 ([translations](README.md#translations))


## まとめ

1. 「本を簡単にダウンロードできるショートカット」は、その本が無料であることを保証しません。このプロジェクトに貢献する前に、ショートカットが無料であることを確認してください。私達はまた働く電子メールを要求するショートカットを許可しませんが、電子メールを要求するものは許可されます。

2. Git を知る必要はありません: 条件に合致しながら*すでに登録されていない* ショートカットを発見した場合、新しいショートカットとともに新しい [問題] (https://github.com/EbookFoundation/free- programming-books/issues) を開くことができます。
    - もし羽の使い方を知っているなら、該当のリポジトリをForkしてPull Request（PR）を送ってください。

3. 私達は6種類のリストを提供しています。正しいものを選択してください：

    - *本*：PDF、HTML、ePub、gitbook.ioベースのウェブサイト、フェザーリポジトリなど。
    - *講座* : ここで講座は本ではなく教育ツールを指します。 [コース例]（http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/）。
    - *相互作用ができる講座*：ユーザーがコードを入力したり、命令を入力して評価を受けることができるウェブサイトを指します（評価は採点ではありません）。例：[Try Haskell]（http://tryhaskell.org）、[Try GitHub]（http://try.github.io）。
    - *Playgrounds* : are online and interactive websites, games or desktop software for learning programming. Write, compile (or run), and share code snippets. Playgrounds often allow you to fork and get your hands dirty by playing with code.
    - *ポッドキャストと画面録画*
    - *問題集 & 競争して学ぶプログラミング* : 問題を解消してプログラミングのスキルを向上させるのに役立つソフトウェアまたはウェブサイトを指します。そのソフトウェアまたはウェブサイトには、同僚が主体となるコードレビューを含めることができます。

4. 下の[ガイドライン](#ガイドライン)を参照し、[マークダウン規格](#規格)を遵守してください。

5. GitHub Actionsは各**リストが昇順か**、また**マークダウン規格が遵守されたか**検収します。各提出が検収を通過することを確認してください**。


###ガイドライン

- 本が無料であることを必ず確認してください。その本が無料だと思う理由をPRのコメントに含めることは、管理者にとって大きな助けになります。
- 私たちは、Googleドライブ、Dropbox、Mega、Scribd、Issuuなどのファイル共有システムにアップロードされたファイルを受け入れません。
- ショートカットを昇順に並べ替えてください、as described [below](#alphabetical-order).
- 可能な限り原作者に近いショートカットを使用してください（作家のウェブサイトが編集者のウェブサイトより優れており、第三者のウェブサイトよりも編集者の方が良いです）。
- 同じ内容を含むという前提の下で、httpsアドレスをhttpアドレスよりも優先してください
- ルートドメインを使用する場合は、最後につく/を除外してください。 （ `http://example.com`は `http://example.com/`よりも優れています）
- すべてのケースでより短いリンクを好む： `http://example.com/dir/`は `http://example.com/dir/index.html`よりも優れていますが、URLボタンサービスを使用しないでください。
- ほとんどの場合、バージョンが指定されているウェブサイトではなく、現在のバージョンのウェブサイトを好む（「http://example.com/dir/book/current/」 .0.0/index.html`よりも優れています）
- 該当するショートカットの証明書が期限切れになった場合:
    1. `http` 形式で *置換しなさい*
    2. `http`バージョンが存在しない場合は、既存のリンクを使用してください。 `https`型も例外を追加した場合に使用できます。
    3. 以外の場合に*除外して下さい*
- もしショートカットが複数の形式で存在する場合、それぞれをメモと一緒にすべて添付してください。
- 資料が複数のサイトに分散している場合は、最も信頼できるショートカットを添付してください。各ショートカットが別のバージョンに向かっている場合は、メモと一緒にすべてを含めてください。 （注：[Issue＃2353]（https://github.com/EbookFoundation/free-programming-books/issues/2353）この文書は仕様を説明しています）。
- 大量のデータを含む1つのコミットよりも小さな変更を含む複数のコミットが好ましい。
- 古い本の場合は、出版日をタイトルと一緒に含めてください。
- 作家の名前を明記してください。 「et al.」を使って短縮できます。
- 書籍がまだ完成していない場合は、[下]（#in_process）に記載されているように、「`in process`」マークを追加してください。
- if a resource is restored using the [*Internet Archive's Wayback Machine*](https://web.archive.org) (or similar), add the "`archived`" notation, as described [below](#archived) 。 The best versions to use are recent and complete.
- 電子メールアドレスまたはアカウントの作成がダウンロード前に要求された場合は、別のノートを添付してください。例： `(Eメールアドレス*要求された*、不要)`。


### 仕様

- すべてのリストは `.md`ファイル形式でなければなりません。この形式の文法は簡単で、[Markdown](https://guides.github.com/features/mastering-markdown/) で参照できます。
- すべてのリストは目次で始める必要があります。各項目を目次にリンクすることが目標です。昇順でソートする必要があります。
- 各セクションは3段階の見出しを使用します（ `###`）。サブセクションは4段階の見出しを使用します（ `####`）。

必ず含めるべき項目：

- 最後のショートカットと新しいセクションの間の改行「2」回
- ヘッダーとセクションの最初のショートカットの間の改行「1」回
- 2つのショートカット間の改行「0」回
- `.md`ファイルの終わりに `1`会議の改行

例：

``text
[...]
* [An Awesome Book](http://example.com/example.html)
                                (ブランクライン)
                                (ブランクライン)
### Example
                                (ブランクライン)
* [Another Awesome Book](http://example.com/book.html)
* [Some Other Book](http://example.com/other.html)
「」

- `]`と`（`の間にスペースを入れないでください：

    ``text
    BAD: * [Another Awesome Book] (http://example.com/book.html)
    GOOD：* [Another Awesome Book]（http://example.com/book.html）
    「」

- 作者を表示する場合は、 ` - `を使用してください。

    ``text
    BAD：* [Another Awesome Book]（http://example.com/book.html） - John Doe
    GOOD: * [Another Awesome Book](http://example.com/book.html) - John Doe
    「」

- ショートカットとフォーマットの間にスペースを挿入します。

    ``text
    BAD：* [A Very Awesome Book](https://example.org/book.pdf)(PDF)
    GOOD: * [A Very Awesome Book](https://example.org/book.pdf) (PDF)
    「」

- 著者はフォーマットの前に書かれています：

    ``text
    BAD: * [A Very Awesome Book](https://example.org/book.pdf)-(PDF) Jane Roe
    GOOD: * [A Very Awesome Book](https://example.org/book.pdf) - Jane Roe (PDF)
    「」

- さまざまなファイル形式が存在する場合：

    ``text
    BAD: * [Another Awesome Book](http://example.com/)- John Doe (HTML)
    BAD: * [Another Awesome

    本](https://downloads.example.org/book.html) - John Doe (ダウンロードサイト)
    GOOD: * [Another Awesome Book](http://example.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
    ```

- 오래된 책들은 출판 연도를 포함하세요:

    ```テキスト
    BAD : * [A Very Awesome Book](https://example.org/book.html) - Jane Roe - 1970
    良い: * [A Very Awesome Book (1970)](https://example.org/book.html) - Jane Roe
    ```

- <a id="in_process"></a>注意事項:

    ```テキスト
    良い: * [すぐにすばらしい本になる](http://example.com/book2.html) - John Doe (HTML) (:construction: *in process*)
    ```

- <a id="archived"></a>アーカイブされたリンク:

    ```テキスト
    GOOD: * [A Way-backed Interesting Book](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) *(:card_file_box: archived)*
    ```

＃＃＃ アルファベット順

- 同じ文字で始まるタイトルが複数ある場合は、秒単位などで並べ替えます。例: `aa` は `ab` の前に来ます。
- 「one two」が「onetwo」の前に来る

リンクの場所が間違っている場合は、リンターのエラー メッセージを確認して、どの行を交換する必要があるかを確認してください。


### 노트(쪽지)

각 파일의 형식은 간단하지만, 목록에는 다양한 형태와 종류의 자료들이 존재할 있습니다. 아래에 나열될 항목들은 저희가 그런 다양성을 어떻게 다루는지에 대한 설명입니다.


#### 메타데이터

각 목록은 최소한의 메타데이터만을 제공합니다: 제목, 바로가기 주소, 제작자, 플랫폼, 그리고 접솸


##### 제목

- 원제를 사용하세요. 저희는 원작(원본)의 제목을 사용하기를 원합니다. 기여자들은 가능한 원제에 가깝거나 동일한 제목을 제공하여야 합니다. 예외는 오래된 책들입니다. 독자들의 더 쉬운 이해와 검색을 위해 현대의 언어로 제목을 새로 짓는 것은 허가됩니다.
- 대문자로만 이루어진 제목은 금지됩니다. 대부분 경우에 タイトル ケースを取得しました。
- 絵文字はありません。


##### 바로가기 주소

- 주소 길이를 줄이는 행위는 허가되지 않습니다.
- 추적을 위한 코드는 주소에서 제거되어야 합니다.
- 주소에 영어가 아닌 언어가 포함된 주소는 허가되지 않습니다. 대부분의 브라우져에서 정상적인 동작을 하지만, 주소창을 그대로 복사해주세요. 부탁드립니다。
- 보안 주소(`https`)가 존재하는 경우, 보안 주소가 일반 주소(`http`)보다 선호됩니다.
- 설명과 다른 웹페이지로 향하는 바로가기 주소는 선호되지 않습니다.


##### 제작자

- 저희는 무료로 자료들을 배포하는 제작자들(번역가들 포함)에게 감사함을 표합니다!
- 번역된 자료들의 경우, 원작자들이 우선적으로 명시되어야 합니다.次の例のように、[MARC relators](https://loc.gov/marc/relators/relaterm.html) を使用して、著者以外の作成者をクレジットすることをお勧めします。

    マークダウン
    * [翻訳された本](http://example.com/book-ko.html) - John Doe, `trl.:` Mike The Translator
    ```

    ここで、注釈 `trl.:` は、「翻訳者」に MARC リレーター コードを使用します。
- 著者リスト内の各項目を区切るには、カンマ `,` を使用します。
- 「`et al.`」で著者リストを短縮できます。
- 제작자들의 정보로 향하는 바로가기 주소는 허가되지 않습니다.
- 여러 작업물이 조합된 자료의 경우, "제작자"는 설명이 필요할 있습니다. 「GoalKicker」または「RIP チュートリアル」を参照してください。「`StackOverflow のドキュメントからコンパイルされています`」


##### 플랫폼과 접속 노트

- 강좌, 특히 강좌 목록의 경우, 플랫폼을 명시하는 것이 필수적입니다. 각각의 강좌들의 플랫폼을 추가하여야 무료로 접속할 수 있음을 이용자들이 인지할 수 있습니다. 일반적으로로그인이필요이한책은에포함않지만、강좌강좌대부분계정계정생성생성하지접근할これは、Coursera、EdX、Udacity、および Udemy から入手できます。 해당 강좌들이 플랫폼 의존적이라면, 플랫폼의 이름은 포함되어야 합니다.
- 유튜브。 YouTube 재생 목록으로 구성된 많은 과정이 있습니다. YouTube를 플랫폼으로 나열하지 않고 종종 하위 플랫폼인 YouTube 제작자를 나열하려고 합니다.
- 유튜브 동영상.続きを読む もっと少なく読む
- Leanpub는 많은 책들과 강좌에 접근을 제공합니다. 경우에 따라 회원가입 없이 접근할 수 있는 책들 또한 존재합니다. 경우에 따라 `*(Leanpub アカウントまたは有効な電子メールが要求されました)*` 노트를 포함하여 목록을 작성해야 합니다.


#### 장르

자료가 어떤 장르에 속하는지 결정하는 첫 번째 방법은 해당 자료의 분류에 따르는 것입니다.


##### 기술하지 않는 장르

次へ: 次へ: 次へ:

- 블로그
- 블로그 게시글
- 사사
- (목록에 포함된 장르를 대량​​ 포함하지 않는 경우) 웹사이트
- 강좌가 아닌 영상
- 책의 목차
- 채팅 채널
- 책의 미리보기
- 슬랙、전자메일

상기된 목록은 최종적이지 않으며, 이슈를 생성하여 기여자들이 제안을 할 있습니다.


##### 책 vs. 다른 자료

저희는 자료가 얼마나 책에 가까운지는 중요하지 않습니다.次へ 次へ 次へ:

- ISBN의 존재 여부 (国際標準図書番号)
- 목차가 존재하는가
- 다운로드를 받을 수 있는가 (특히 ePub 형식)
- 개정판이 있는가
- 상호작용을 하지 않는가
- 분명한 하나의 주제가 있는가
- 스스로 내용을 포함하고 있는가

저희가 인정하는 책들은 위 항목을 모두 포함하지 않을 수 있으며, 최종적으로는 내용에 의해 결겕


##### 책 vs. 강좌

때에 따라 이 둘은 구분하기 어려울 수 있습니다.

강좌는 종종 책을 보조교재로 사용하는데, 이것은 상기한 책의 특성에 의해 목록에 추가 될 있슈다. 이 보조교재에는 종종 강의 노트, 연습 문제, 시험, 등등이 포함됩니다. 영상/강의 하나는 강좌로 간주하지 않습니다. 또한, 파워포인트는 강좌가 아닙니다.


##### 상호작용 강의 vs. 다른 자료

만약 강의가 인쇄되어서도 사용될 수 있다면, 상호작용 강의에 포함되지 않습니다.


### 자동화

- [GitHub Actions](https://github.com/features/actions)から[fpb-lint](https://github.com/vhf/free-programming-books-lint)に移行([`.github/workflows/fpb-lint.yml`](../.github/workflows/fpb-lint.yml) を参照)
- 바로가기 주소 검증은 [awesome_bot](https://github.com/dkhamsing/awesome_bot)를 이용합니다
- より多くのことを確認してください:

    プロパティ
    check_urls=free-programming-books.md free-programming-books-ko.md
    ```

- 각 입력을 공백으로 구분하여 하나 이상의 파일을 검사 할 있습니다.
- 만약 하나 이상의 파일을 검사한다면, 검사 결과는 마지막 파일의 검사 결과가 표시됩니다. 이 특성으로 인하여 통과를 받았더라도 관리자에 의하여 최종 승인이 보류될 수 있습니다. 「すべてのチェックを表示」 -> 「詳細」を選択してください。
