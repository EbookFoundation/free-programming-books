from re import findall

def parse_content(file_name: str) -> list:
    with open(file_name, "r") as file:
        file_content = file.readlines()
        file_content = [content.removeprefix("* ").removesuffix("\n") for content in file_content]

    return file_content

def get_formatted_content(file_content: list) -> list:
    temp = list()
    for content in file_content:
        match = findall(r"\[.+?\]\(h.+?\) - .+? \(.+?\)", content)
        temp.append(match)

    formatted_content = list()    
    for i in range(len(temp)):
        try:
            formatted_content.append(temp[i][0])
        except IndexError:
            pass

    return formatted_content

def get_unformatted_content(file_content: list) -> list:
    formatted_content = get_formatted_content(file_content)
    unformatted_content = list()
    for content in file_content:
        if content not in formatted_content:
            unformatted_content.append(content + "\n")

    return unformatted_content


def write_data(content: list):
    with open("Need Style Review.txt", "w") as file:
        file.writelines(content)

    print("Done!")


if __name__ == "__main__":
    parsed_content = parse_content("free-programming-books-subjects.md")
    unformatted_content = get_unformatted_content(parsed_content)

    write_data(unformatted_content)

