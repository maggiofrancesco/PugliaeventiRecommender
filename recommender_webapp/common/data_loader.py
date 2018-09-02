from pugliaeventi import constant
from recommender_webapp.models import Place


class DataLoader:
    data_in_memory = {'places_dict': {}, 'places_list': [], 'place_feature': {}}

    def __init__(self):
        self.__load_data_from_db()

    def __load_data_from_db(self):
        for place in Place.objects.all():
            self.data_in_memory['places_dict'][place.placeId] = place
            self.data_in_memory['places_list'].append(place)

            if place.freeEntry:
                self.data_in_memory['place_feature'][constant.FREE_ENTRY] = place
            if place.teatro:
                self.data_in_memory['place_feature'][constant.TEATRO] = place
            if place.spiaggia:
                self.data_in_memory['place_feature'][constant.SPIAGGIA] = place
            if place.museo:
                self.data_in_memory['place_feature'][constant.MUSEO] = place
            if place.romantico:
                self.data_in_memory['place_feature'][constant.ROMANTICO] = place
            if place.benessere:
                self.data_in_memory['place_feature'][constant.BENESSERE] = place
            if place.mangiare:
                self.data_in_memory['place_feature'][constant.MANGIARE] = place
            if place.bere:
                self.data_in_memory['place_feature'][constant.BERE] = place
            if place.dormire:
                self.data_in_memory['place_feature'][constant.DORMIRE] = place
            if place.goloso:
                self.data_in_memory['place_feature'][constant.GOLOSO] = place
            if place.libri:
                self.data_in_memory['place_feature'][constant.LIBRI] = place
