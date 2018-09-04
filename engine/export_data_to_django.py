import csv

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


if __name__ == "__main__":
    import_places()
    import_sample_ratings()
    import_comuni()
    import_distanze()
