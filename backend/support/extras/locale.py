def get_correct_case_for_number(number, words: list) -> str:
    '''
    :param number: number
    :param words: list of words [nominative, genitive, genitive_plural] cases
    :return: string
    '''
    if number % 100 // 10 == 1 or number == 11:
        return words[2]
    elif number % 10 == 1:
        return words[0]
    elif 2 <= number % 10 <= 4:
        return words[1]
    else:
        return words[2]
