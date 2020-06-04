def readmov(connection, context):
    cursor = connection.cursor()
    # Validate User Input
    if context['choice'] == 'سریال ها🎬':
        sql = "SELECT id, description, name, genre, year, director, pg, season, episode, star, serial FROM movies WHERE tags LIKE '%" + context[
            context['choice']].lower() + "%' AND serial = True ORDER BY id"
    elif context['choice'] == 'فیلم ها🎞':
        sql = "SELECT id, description, name, genre, year, director, pg, season, episode, star, serial FROM movies WHERE tags LIKE '%" + context[
            context['choice']].lower() + "%' AND serial = False ORDER BY id"
    elif context['choice'] == 'فیلم های اخیر📅':
        sql = "SELECT id, description, name, genre, year, director, pg, season, episode, star, serial FROM movies ORDER BY id DESC LIMIT 20"
    elif context['choice'] == 'بر اساس ژانر🔫🕵':
        sql = "SELECT id, description, name, genre, year, director, pg, season, episode, star, serial FROM movies WHERE genre LIKE '%" + context[
            context['choice']] + "%'ORDER BY id DESC LIMIT 20"
    else:
        sql = "SELECT id, description, name, genre, year, director, pg, season, episode, star, serial FROM movies ORDER BY id DESC LIMIT 20"
    cursor.execute(sql)

    return cursor.fetchall()


def getmovie(connection, ID):
    cursor = connection.cursor()
    # Validate User Input
    sql = "SELECT name, genre , year , star  FROM movies WHERE id = " + ID + " ORDER BY id"
    cursor.execute(sql)

    return cursor.fetchall()
