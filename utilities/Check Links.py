from re import findall
from requests import get

def get_book_urls(file_name) -> dict:
    """Creates a dictionary with book name-url key-value pairs.
  
    :param file_name: Name of file with extension.
    :return: Dictionary containing book name-url key-value pairs.
    """
    book_urls = dict()

    with open(file_name, "r") as file:
        file_content = file.readlines()

        for content in file_content:
            result = findall(r"\[.+?\]\(h.+?\)", content)   # result has format ["[Book Name](URL)"]

            # Try block is used to bypass all other entries
            # which are not books, courses, etc; like a section.
            try:
                result = result[0].split("](")  # result is ["[Book Name", "URL)"]
                name = result[0][1:] 
                url = result[1][:len(result[1]) - 1]

                book_urls[name] = url
            except IndexError:
                pass

    return book_urls

def check_urls(book_urls: dict) -> list:
    """Checks URLs to see if they return a 404 status code.
  
    :param book_urls: Dictionary containing book name-url key-value pairs.
    :return: List containing book, status code in string format.
    """
    broken_urls = list()
    for book in book_urls:
        try:
            status_code = get(book_urls[book]).status_code
        except:
            status_code = "Unknown Error"

        if status_code == 404:
            broken_urls.append(str(book + " - " + status_code + "\n"))

def write_data(content: list):
    """Write data regarding broken urls to file.
    
    :param content: List containing book, status code in string format.
    """
    with open("Need Link Review.txt", "w") as file:
        file.writelines(content)

if __name__ == "__main__":
    book_urls = get_book_urls("free-programming-books-subjects.md")
    broken_urls = check_urls(book_urls)
    write_data(broken_urls)

