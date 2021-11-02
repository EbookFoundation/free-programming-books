*이 문서를 다른 언어로 보시려면: [Deutsch](CONTRIBUTING-de.md), [Français](CONTRIBUTING-fr.md), [Español](CONTRIBUTING-es.md), [Indonesia](CONTRIBUTING-id.md),[简体中文](CONTRIBUTING-zh.md), [English](CONTRIBUTING.md), [فارسی](CONTRIBUTING-fa_IR.md), [Tiếng Việt](CONTRIBUTING-vn.md), [Русский](CONTRIBUTING-ru.md).*

## 기여자 라이선스 동의서
이 프로젝트의 기여자들은 리포지토리의 [약관](https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE) 에 동의하는 것으로 간주됩니다.

## 기여자 행도 강령
이 리포지토리 기여함으로서, 모든 기여자는 이 [행동강령](https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT-ko.md) 에 동의한 것으로 간주됩니다.

## 요약
1. "책을 쉽게 내려받을 수 있는 바로가기"는 해당 책이 무료임을 보장하지 않습니다. 이 프로젝트에 기여하기 전에 해당 바로가기가 무료임을 확인해 주십시오. 저희는 또한 작동하는 이메일을 요구하는 바로가기는 허용하지 않습니다만, 이메일을 요청하는 것들은 허용됩니다.
2. 깃에 대해 알고 있을 필요는 없습니다: 만약 당신이 조건에 부합하면서 이미 등재되지 않은 바로가기를 발견한다면, 새로운 바로가기와 함께 새로운 [이슈](https://github.com/EbookFoundation/free-programming-books/issues)를 열 수 있습니다.
    - 만약 깃 사용법을 알고 있다면, 해당 리포지토리를 Fork 하며 Pull request를 보내주세요.
3. 저희는 다섯 가지의 리스트를 제공하고 있습니다. 올바른 것을 선택해 주세요:
    - *책* : PDF, HTML, ePub, gitbook.io 기반 웹사이트, 깃 리포지토리, 등.
    - *강좌* : 여기서 강좌는 책이 아닌 교육 도구를 칭합니다. [강좌 예시](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *상호작용을 할 수 있는 강좌* : 사용자가 코드를 입력하거나 명령어를 입력하여 평가을 받을 수 있는 웹사이트를 칭합니다(평가는 채점이 아닙니다). 예시: [Try Haskell](http://tryhaskell.org), [Try Github](http://try.github.io).
    - *팟캐스트와 화면 녹화*
    - *문제집 & 경쟁 하며 배우는 프로그래밍* : 문제를 풂으로서 프로그래밍 실력을 향상시키는데 도움을 주는 소프트웨어 또는 웹사이트를 칭합니다. 해당 소프트웨어 또는 웹사이트는 동료가 주체가 되는 코드 검토를 포함 할 수 있습니다.

4. 아래의 [가이드라인](#가이드라인) 을 참조하고 [마크다운 규격](#규격) 을 준수하여 주십시오.

5. 깃허브 액션이 각각의 리스트가 오름차순인지, 또하 규격이 준수되었는지 검수 할 것입니다. 각 제출이 검수를 통과하는지 확인해주십시오.

### 가이드라인
- 책이 무료인지 반드시 확인 해 주십시오. 해당 책이 무료라고 생각하는 이유를 PR의 comment에 포함하는 것은 관리자들에게 큰 도움이 됩니다.
- 저희는 Google Drive, Dropbox, Mega, Scribd, Issuu 또는 유사한 파일 공유 시스템에 업로드된 파일들을 수락하지 않습니다.
- 바로가기를 오름차순으로 정렬해 주십시오. 만약 당신이 오름차순이 아닌 파일을 발견한다면, 수정후 PR을 보내주세요.
- 가능한 가장 원작자에 가까운 바로가기를 사용해주세요(작가의 웹사이트가 편집자의 웹사이트보다 낫고, 제 3자의 웹사이트보다는 편집자의 것이 낫습니다).
- 동일한 내용으 포함한다는 전 하에 `https` 주소를 `http`주소보다 우선시 해주십시오
- 루트 도메인을 사용할때는, 마지막에 붙는 /를 배제하여주십시오. (`http://example.com` 가 `http://example.com/` 보다 낫습니다)
- 모든 경우에 더 짧은 링크를 선호합니다: `http://example.com/dir/` 가 `http://example.com/dir/index.html`보다 낫지만, URL 단추 서비스를 사용하지 마십시오.
- 대부분의 경우에 버전이 명시된 웹사이트보다는 현행 버젼 웹사이트를 선호합니다 (`http://example.com/dir/book/current/`가 `http://example.com/dir/book/v1.0.0/index.html`보다 낫습니다)
- 만약 해당 바로가기의 인증서가 만료되었다면:
    1. `http` 형식으로 *대치 하십시오*
    2. `http` 버젼이 존재하지 않는다면, 기존의 링크를 사용하십시오. `https`형식또한 예외를 추가한다면 사용할 수 있습니다.
    3. 이외의 경우에 *제외하십시오*
- 만약 바로가기가 여러 형식으로 존재한다면, 각각을 쪽지와 함께 모두 첨부해주세요.
- 만약 자료가 여러 사이트에 분산되어 있다면, 가장 믿을 수 있는 바로가기를 첨부해주세요. 만약 각각의 바로가기가 다른 버젼으로 향한다면, 쪽지와 함께 모두 포함하십시오. (참고: [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) 해당문서는 규격에 대해 설명합니다.)
- 대량의 자료를 포함한 하나의 커밋보다는 작은 변화를 포함하는 여러개의 커밋이 선호됩니다.
- 만약 오래된 책이라면, 출판일을 제목과 함께 포함하세요.
- 작가(들)의 이름을 명시하십시오. "et al."을 사용하여 단축 할 수 있습니다.
- 만약 책이 아직 완결되지 않았다면, [아래](#in_process)에 명시되어 있다시피, "in progress" 표시를 추가하십시오.
- 만약 이메일 주소 또는 계정 생성이 다운로드 이전에 요청된다면, 별도의 노트를 첨부하세요.

### 규격
- 모든 목록은 `.md`파일 형식 이어야 합니다. 해당 형식의 문법은 간단하며, [Markdown](https://guides.github.com/features/mastering-markdown/) 에서 찾아 볼 수 있습니다.
- 모든 목록은 목차와 함께 시작해야 합니다. 각 항목을 목차에 연결하는 것이 목표입니다. 오름차순으로 정렬되어 있어야 합니다.
- 각 섹션은 3단계 헤딩을 사용합니다 (`###`). 하위 섹션은 4단계 헤딩을 사용합니다 (`####`).

반드시 포함하여야 하는 항목들:
- 마지막 바로가기와 새로운 섹션 사이의 줄바꿈 `2`회
- 머리말과 섹션의 첫 바로가기 사이의 줄바꿈 `1`회
- 두 바로가기 사이의 줄바꿈 `0`회
- `.md` 파일의 마지막에 `1`회의 줄바꿈

예시:

    [...]
    * [An Awesome Book](http://example.com/example.html)
                                    (blank line)
                                    (blank line)
    ### Example
                                    (blank line)
    * [Another Awesome Book](http://example.com/book.html)
    * [Some Other Book](http://example.com/other.html)

- `]` 와 `(` 사이에 공백을 넣지 마십시오:

```
BAD : * [Another Awesome Book] (http://example.com/book.html)
GOOD: * [Another Awesome Book](http://example.com/book.html)
```

- 저자를 표시할 경우, ` - `를 사용하십시오 (띄어쓰기 - 띄어쓰기):

```
BAD : * [Another Awesome Book](http://example.com/book.html)- John Doe
GOOD: * [Another Awesome Book](http://example.com/book.html) - John Doe
```

- 바로가기와 형식 사이에는 공백을 삽입 하십시오:

```
BAD : * [A Very Awesome Book](https://example.org/book.pdf)(PDF)
GOOD: * [A Very Awesome Book](https://example.org/book.pdf) (PDF)
```

- 저자는 형식 전에 옵니다:

```
BAD : * [A Very Awesome Book](https://example.org/book.pdf)- (PDF) Jane Roe
GOOD: * [A Very Awesome Book](https://example.org/book.pdf) - Jane Roe (PDF)
```

- 여러가지의 파일 형식이 존재할떄:

```
BAD : * [Another Awesome Book](http://example.com/)- John Doe (HTML)
BAD : * [Another Awesome Book](https://downloads.example.org/book.html)- John Doe (download site)
GOOD: * [Another Awesome Book](http://example.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
```

- 오래된 책들은 출판 년도를 포함하세요:

```
BAD : * [A Very Awesome Book](https://example.org/book.html) - Jane Roe - 1970
GOOD: * [A Very Awesome Book (1970)](https://example.org/book.html) - Jane Roe
```

<a name="in_process"></a>
- 작성중인 책:

```
GOOD: * [Will Be An Awesome Book Soon](http://example.com/book2.html) - John Doe (HTML) (:construction: *in process*)
```

### 노트(쪽지)

각 파일의 형식은 간단하지만, 목록에는 다양한 형태와 종류의 자료들이 존재할 수 있습니다. 아래에 나열될 항목들은 저희가 그런 다양성을 어떻게 다르는지에 대한 설명 입니다.

#### 메타데이터

각 목록은 최소한의 메타데이터만을 제공합니다: 제목, 바로가기 주소, 제작자, 플랫폼, 그리고 접속 노트

##### 제목

- 원제를 사용하세요. 저희는 원작(원본)의 제목을 사용하기를 원합니다. 기여자들은 가능한 원제에 가깝거나 동일한 제목을 제공하여야 합니다. 예외는 오래된 책들입니다. 독자들의 더 쉬운 이해와 검색을 위해 현대의 언어로 제목을 새로 짓는것은 허가됩니다.
- 대문자로만 이루어진 제목은 금지됩니다. 대부분 경우에 title case가 허가되지만, 확실하지 않다면 자료에 명시된 방식으로 기술 하세요.

##### 바로가기 주소

- 주소 길이를 줄이는 행위는 허가되지 않습니다.
- 추적을 위한 코드는 주소에서 제거되어야 합니다.
- 주소에 영어가 아닌 언어가 포함 된 주소는 허가되지 않습니다. 대부분의 브라우져에서 정상적인 동작을 하지만, 주소창을 그대로 복사해주세요. 부탁드립니다.
- 보안 주소(https)가 존재하는 경우, 보안 주소가 일반 주소(http)보다 선호됩니다.
- 설명과 다른 웹페이지로 향하는 바로가기 주소는 선호되지 않습니다.

##### 제작자

- 저희는 무료로 자료들을 배포하는 제작자들(번역가들 포함)에게 감사함을 표합니다!
- 번역된 자료들의 경우, 원작자들이 우선적으로 명시되어야 합니다.
- 제작자들의 정보로 향하는 바로가기 주소는 허가되지 않습니다.
- 여러 작업물이 조합된 자료의 경우, "제작자"는 설명이 필요할 수 있습니다. 예를 들어, "GoalKicker" 책들의 제작자들은 "Compiled from StackOverflow documentation"로 명시되어야 합니다.

##### 플랫폼과 접속 노트

- 강좌, 특히 걍좌 목록의 경우, 플랫폼을 명시하는것이 필수적입니다. 각각의 강좌들의 플랫폼을 추가하여야 무료로 접속할 수 있음을 이용자들이 인지 할 수 있습니다. 일반적으로 로그인이 필요한 책은 목록에 포함하지 않지만, 강좌는 대부분 계정을 생성하지 않으면 접근 할 수 없기 때문에 예외로 합니다. 예시로는 Coursera, EdX, Udacity, 그리고 Udemy가 있습니다. 해당 강좌들이 플랫폼 의존적이라면, 플랫폼의 이름은 반드시 포함되어야 합니다.
- 만약 강좌가 유튜브에 존재하는 경우, 유튜브는 플랫폼으로 간주하지 않고, 크리에이터를 명시합니다.
- 유튜브 영상들은 각각의 영상이 한시간이 넘지 않는 경우에는 바로가기 주소를 포함하지 않습니다.
- Leanpub는 많은 책들과 강좌에 접근을 제공합니다. 경우에 따라 회원가입 없이 접근 할 수 있는 책들 또한 존재합니다. 경우에 따라 *(Leanpub account or valid email requested)* 노트를 포함하여 목록을 작성해야 합니다.

#### 장르

자료가 어떤 장르에 속하는지 결정하는 첫번째 방법은 해당 자료의 분류에 따르는 것입니다.

##### 기술하지않는 장르

인터넷에는 너무 다양하고 정확하지않은 자료들이 있기에, 저희는 다음 장르를 포함하지 않습니다:

- 블로그
- 블로그 게시글
- 기사
- (목록에 포함된 장르를 대량 포함하지 않는 경우) 웹사이트
- 강좌가 아닌 영상
- 책의 목차
- 채팅 채널
- 책의 미리보기
- 슬랙, 전자메일

상기된 목록은 최종적이지 않으며, 이슈를 생성하여 기여자들이 제안을 할 수 있습니다.


##### 책 vs. 다른 자료

저희는 자료가 얼마나 책에 가까운지는 중요하지 않습니다. 다음의 항목을을 포함한다면, 책으로 간주됩니다:

- ISBN의 존재 여부 (International Standard Book Number)
- 목차가 존재하는가
- 다운로드를 받을 수 있는가 (특히 ePub 형식)
- 개정판이 있는가
- 상호작용을 하지않는가
- 분명한 하나의 주제가 있는가
- 스스로 내용을 포함하고 있는가

저희가 인정하는 책들은 위 항목을 모두 포함하지 않을 수 있으며, 최종적으로는 내용에 의해 결정됩니다.


##### 책 vs. 강좌

때에 따라 이 둘은 구분하기 어려울 수 있습니다.

강좌는 종종 책을 보조교재로 사용하는데, 이것은 상기한 책의 특성에 의해 목록에 추가 될 수 있습니다. 이 보조교재에는 종종 강의 노트, 연습 문제, 시험, 등등이 포함됩니다. 영상/강의 하나는 강좌로 간주되지 않습니다. 또한, 파워포인트는 강좌가 아닙니다.

##### 상호작용 강의 vs. 다른 자료

만약 강의가 인쇄되어서도 사용 될 수 있다면, 상호작용 강의에 포함되지 않습니다.


### 자동화

- 규격 규칙은 [GitHub Actions](https://github.com/features/actions)에 의해 [fpb-lint](https://github.com/vhf/free-programming-books-lint)를 사용하여 강제됩니다 (see [.github/workflows/fpb-lint.yml](.github/workflows/fpb-lint.yml))
- 바로가기 주소 검증은 [awesome_bot](https://github.com/dkhamsing/awesome_bot)를 이용합니다
- 바로가기 주소 검증을 위해 커밋 메시지에 `check_urls=file_to_check`을 포함해 주세요:

```
check_urls=free-programming-books.md free-programming-books-en.md
```

- 각 입력을 공백으로 구문하여 하나 이상의 파일을 검사 할 수 있습니다.
- 만약 하나 이상의 파일을 검사한다면, 검사 결과는 마지막 파일의 검사 결과가 표시됩니다. 이 특성으로 인하여 통과를 받았더라도 관리자에 의하여 최종 승인이 보류 될 수 있습니다. 정확한 결과를 확인 하려면, "Show all checks" -> "Details"로 가세요.
