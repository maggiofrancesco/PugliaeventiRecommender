import csv
from datetime import datetime, date

import psycopg2


def execute_sql(s):
    con = psycopg2.connect('dbname=django_pugliaeventi user=postgres password=password')
    with con:
        cur = con.cursor()
        cur.execute(s)
    return cur


def single_quote(s):
    if len(s) == 0:
        return 'None'
    if s.find('\'') != -1:
        return s.replace("\'", "\'\'")
    else:
        return s


def import_places():
    with open('data/items.csv', encoding="utf8") as f:
        file_reader = csv.reader(f, delimiter=',')
        for row in file_reader:
            place_id = row[0]
            if place_id == '5112':
                print("qui")
            place_name = row[1]
            place_location = row[2]
            free_entry = row[3]
            bere = row[4]
            mangiare = row[5]
            benessere = row[6]
            dormire = row[7]
            goloso = row[8]
            libri = row[9]
            romantico = row[10]
            museo = row[11]
            spiaggia = row[12]
            teatro = row[13]

            try:
                sql = (
                    '''INSERT INTO recommender_webapp_place VALUES ({},\'{}\',\'{}\',{},{},{},{},{},{},{},{},{},{},{})'''.format(
                        place_id,
                        single_quote(place_name),
                        single_quote(place_location),
                        bool(int(free_entry)), bool(int(bere)), bool(int(mangiare)), bool(int(benessere)),
                        bool(int(dormire)), bool(int(goloso)), bool(int(libri)), bool(int(romantico)),
                        bool(int(museo)), bool(int(spiaggia)), bool(int(teatro))
                    ))
                execute_sql(sql)
                print("Inserted place: " + place_id)
            except Exception as e:
                print('Place Insert Failure: ' + place_id, e)
                continue


def import_sample_ratings():
    """
    Questo metodo effettua l'importazione nel db Django dei rating creati in maniera casuale preesistenti nel dataset
    ratings_train.csv. Tuttavia, tali ratings non sono direttamente utilizzati in Django, per cui tale funzione al
    momento risulta essere inutile.
    """

    with open('data/ratings_train.csv') as f:
        i = 1
        for row in f.readlines():
            columns = row.split(',')
            user_id = columns[0]
            place_id = columns[1]
            rating = columns[2]

            try:
                sql = (
                    '''INSERT INTO recommender_webapp_samplerating VALUES ({},{},{},{})'''.format(
                        i,
                        user_id,
                        rating,
                        place_id
                    ))
                execute_sql(sql)
                i += 1
                print("Inserted sample rating by user: " + user_id + " and place: " + place_id)
            except Exception as e:
                print('Rating Insert Failure: ' + place_id, e)
                continue


def import_comuni():
    with open('data/comuni.csv') as f:
        for row in f.readlines():
            columns = row.split(',')
            istat = columns[0]
            nome = columns[1]
            provincia = columns[2]
            regione = columns[3]
            prefisso = columns[4]
            cap = columns[5]
            cod_fis = columns[6]
            abitanti = columns[7]

            try:
                sql = (
                    '''INSERT INTO recommender_webapp_comune VALUES (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',{})'''.format(
                        istat,
                        single_quote(nome),
                        provincia,
                        regione,
                        prefisso,
                        cap,
                        cod_fis,
                        abitanti
                    ))
                execute_sql(sql)
                print("Inserted city: " + nome)
            except Exception as e:
                print('City Insert Failure: ' + nome, e)
                continue


def import_distanze():
    with open('data/distanze.csv') as csvfile:
        file_reader = csv.reader(csvfile, delimiter=',')
        i = 1
        for row in file_reader:
            citta_a = row[0]
            citta_b = row[1]
            distanza = row[2]

            try:
                sql = (
                    '''INSERT INTO recommender_webapp_distanza VALUES ({},\'{}\',\'{}\',{})'''.format(
                        i,
                        single_quote(citta_a),
                        single_quote(citta_b),
                        distanza
                    ))
                execute_sql(sql)
                i += 1
                print("Inserted distance between " + citta_a + " and " + citta_b)
            except Exception as e:
                print('Distance Insert Failure: ' + citta_a + " and " + citta_b, e)
                continue


def import_eventi():
    with open('data/eventi.csv', encoding="utf8") as csvfile:
        file_reader = csv.reader(csvfile, delimiter=',')
        for row in file_reader:
            event_id = int(row[0])
            title = row[2]
            place_name = row[4]
            date_from = row[5]
            date_to = row[6]
            location = row[7]
            description = row[23]
            popularity = row[24]

            date_converted = datetime.strptime(date_from.split(" ")[0], '%Y-%m-%d').date()
            date_from_events_query = date(2018, 8, 1)

            if place_name != '' and date_converted > date_from_events_query:
                try:
                    query_django_places = (
                        '''SELECT "placeId" FROM recommender_webapp_place p WHERE p.name LIKE '{}' AND p.location LIKE '{}' '''.format(
                            single_quote(place_name),
                            single_quote(location)
                        ))
                    cur = execute_sql(query_django_places)
                    result = cur.fetchone()
                    if result:
                        place_id = result[0]

                        sql = (
                            '''INSERT INTO recommender_webapp_event VALUES ({},\'{}\',\'{}\',\'{}\',\'{}\',{},\'{}\',{})'''.format(
                                event_id,
                                single_quote(title),
                                single_quote(location),
                                single_quote(date_from),
                                single_quote(date_to),
                                popularity,
                                single_quote(description),
                                place_id
                            ))
                        execute_sql(sql)
                        print("Inserted event " + title + " for location:  " + location)
                except Exception as e:
                    print("Error Insert event " + title + " for location:  " + location)
                    continue


if __name__ == "__main__":
    # import_places()
    # import_sample_ratings() INUTILE
    # import_comuni()
    # import_distanze()
    import_eventi()
