from re import findall

def parse_content(file_name: str) -> list:
    """Parse the raw content read from file.
    
    :param file_name: Name of file to parse content.
    :return: List containing each line of the file parsed in a certain manner.
    """
    with open(file_name, "r") as file:
        file_content = file.readlines()
        file_content = [content.removeprefix("* ").removesuffix("\n") for content in file_content]

    return file_content

def get_formatted_content(file_content: list) -> list:
    """Search parsed file content to match certain listing patterns.
    Currently only one pattern is supported:
        [Book Name](URL) - Author Name (File Type).
    
    :param file_content: Parsed file content.
    :return: List containing all matched listings.
    """
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
    """Search parsed file content to find unformatted listings.
    Unformatted listings are those that do not follow the format
    of listing an item.
    Currently only one pattern is supported:
        [Book Name](URL) - Author Name (File Type).
    This function is not perfect and returns various other listings,
    like section names.
    
    :param file_content: Parsed file content.
    :return: List containing all unmatched listings.
    """
    formatted_content = get_formatted_content(file_content)
    unformatted_content = list()
    for content in file_content:
        if content not in formatted_content:
            unformatted_content.append(content + "\n")

    return unformatted_content


def write_data(content: list):
    """Write data regarding unmatched listings to file.
    
    :param content: List containg all unmatched listings in string format.
    """
    print(content)
    with open("Need Style Review.txt", "w") as file:
        file.writelines(content)

    print("Done!")


if __name__ == "__main__":
    parsed_content = parse_content("free-programming-books-subjects.md")
    unformatted_content = get_unformatted_content(parsed_content)

    write_data(unformatted_content)

