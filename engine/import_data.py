import psycopg2


def execute_sql(s):
    con = psycopg2.connect('dbname=django_pugliaeventi user=postgres password=Frapama29')
    with con:
        cur = con.cursor()
        cur.execute(s)


def single_quote(s):
    if len(s) == 0:
        return 'None'
    if s.find('\'') != -1:
        return s.replace("\'", "\'\'")
    else:
        return s


def import_places():
    with open('data/items.csv') as f:
        for row in f.readlines():
            columns = row.split(',')
            place_id = columns[0]
            place_name = columns[1]
            place_location = columns[2]
            free_entry = columns[3]
            bere = columns[4]
            mangiare = columns[5]
            benessere = columns[6]
            dormire = columns[7]
            goloso = columns[8]
            libri = columns[9]
            romantico = columns[10]
            museo = columns[11]
            spiaggia = columns[12]
            teatro = columns[13]

            try:
                sql = (
                    '''INSERT INTO recommender_place VALUES ({},\'{}\',\'{}\',{},{},{},{},{},{},{},{},{},{},{})'''.format(
                        place_id,
                        single_quote(place_name),
                        single_quote(place_location),
                        bool(int(free_entry)), bool(int(bere)), bool(int(mangiare)), bool(int(benessere)),
                        bool(int(dormire)), bool(int(goloso)), bool(int(libri)), bool(int(romantico)),
                        bool(int(museo)), bool(int(spiaggia)), bool(int(teatro))
                    ))
                execute_sql(sql)
                print("Insert place: " + place_id)
            except Exception as e:
                print('Place Insert Failure: ' + place_id, e)
                continue


if __name__ == "__main__":
    import_places()
