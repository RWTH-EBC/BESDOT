import os
from datetime import datetime
from warnings import warn
import pandas as pd

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
profile_dir = os.path.join(base_path, "data", "standardlastprofil")


def change_bld_typ(tek_bld_type):
    """Due to the different name for building type in TEK method and
    'Standardlastprofil', a name matching should be done before generate the
    electricity profile.
    tek_building_typ_list = ["Verwaltungsgebäude",
                             "Büro und Dienstleistungsgebäude",
                             "Hochschule und Forschung",
                             "Gesundheitswesen",
                             "Bildungseinrichtungen",
                             "Kultureinrichtungen",
                             "Sporteinrichtungen",
                             "Beherbergen und Verpflegen",
                             "Gewerbliche und industrielle",
                             "Verkaufsstätten",
                             "Technikgebäude"]
    slp_building_typ_list = {"H0": "Haushlt",
                             "L1": "Landwirtschaftsbetriebe mit "
                                   "Milchewirtschaft/Nebenerwerbs-Tierzucht",
                             "L2": "Übrige Landwirtschaftsbetribe",
                             "L0": "Landwirtschaftsbetriebe",
                             "G1": "Gewerbe werktags 8-18",
                             "G2": "gewerbe mit starkem bis überwiegendem "
                                   "Verbrauch in den Abendstunden",
                             "G3": "Gewerbe durchlaufend",
                             "G4": "Laden/Friseur",
                             "G5": "Bäckerei mit Backstube",
                             "G6": "Wochenendbetribe",
                             "G0": "Gewerbe allgemein"}
    """
    if tek_bld_type in ["Verwaltungsgebäude",
                        "Büro und Dienstleistungsgebäude",
                        "Hochschule und Forschung",
                        "Bildungseinrichtungen",
                        "Gesundheitswesen",
                        "Gewerbliche und industrielle",
                        "Technikgebäude"]:
        slp_bld_type = "G1"
    elif tek_bld_type in ["Kultureinrichtungen",
                          "Sporteinrichtungen"]:
        slp_bld_type = "G2"
    elif tek_bld_type in ["Beherbergen und Verpflegen"]:
        slp_bld_type = "G6"
    elif tek_bld_type in ["Verkaufsstätten"]:
        slp_bld_type = "G0"
    else:
        # warn('The tek building is not allowed, slp building type is set to '
        #      'residential building')
        slp_bld_type = "H0"

    return slp_bld_type


def gen_elec_profile(annual_value, building_type, year):
    """The 'Standardlastprofil' method use the summarized profile as standard
    profile for the building. In order to using this method, should attention
    the building_type is pre-defined within the 'Standardlastprofil'."""

    slp_bld_typ = change_bld_typ(building_type)
    profile = pd.read_excel(os.path.join(profile_dir,
                                         "Lastprofil_" + slp_bld_typ + ".xls"),
                            skiprows=10,
                            header=None)
    profile.columns = ["summer", "summer_weekday", "summer_time_from",
                       "summer_time_to", "summer_value", "",
                       "trans", "trans_weekday", "trans_time_from",
                       "trans_time_to", "trans_value", "",
                       "winter", "winter_weekday", "winter_time_from",
                       "winter_time_to", "winter_value"]

    # get the weekday of first day of given year. return 0 to 6, 0 means Monday
    first_day = datetime(year=year, month=1, day=1).weekday()
    # get the list of weekday for whole year
    weekday_list = []
    for day in range(365):
        weekday_list.append((first_day + day) % 7)

    if year % 4 == 0 and year % 100 != 0:
        weekday_list.append((weekday_list[-1] + 1) % 7)

    # get the list of season for each day, according to standard last profile
    # Winter:      01.11. to 20.03.
    # Summer:      15.05. to 14.09.
    # Transition:  21.03. to 14.05. and 15.09. to 31.10.
    season_list = []
    season_list = ['winter'] * ((datetime(year=year, month=3, day=20) -
                                 datetime(year=year, month=1, day=1)).days
                                + 1)
    season_list += ['transition'] * ((datetime(year=year, month=5, day=14) -
                                      datetime(year=year, month=3, day=21)).days
                                     + 1)
    season_list += ['summer'] * ((datetime(year=year, month=9, day=14) -
                                  datetime(year=year, month=5, day=15)).days
                                 + 1)
    season_list += ['transition'] * ((datetime(year=year, month=10, day=31) -
                                      datetime(year=year, month=9, day=15)).days
                                     + 1)
    season_list += ['winter'] * ((datetime(year=year, month=12, day=31) -
                                  datetime(year=year, month=11,
                                           day=1)).days
                                 + 1)

    # Generate the profile
    weight_profile = []
    for day_nr in range(len(weekday_list)):
        if weekday_list[day_nr] < 5 and season_list[day_nr] == 'summer':
            # print(type(profile[profile["summer_weekday"]=="Montag - Freitag"][
            #           "summer_value"].to_list()))
            weight_profile += profile[profile["summer_weekday"] == "Montag - " \
                                                                   "Freitag"][
                "summer_value"].to_list()
        elif weekday_list[day_nr] < 5 and season_list[day_nr] == 'transition':
            weight_profile += profile[profile["trans_weekday"] == "Montag - " \
                                                                  "Freitag"][
                "trans_value"].to_list()
        elif weekday_list[day_nr] < 5 and season_list[day_nr] == 'winter':
            weight_profile += profile[profile["winter_weekday"] == "Montag - " \
                                                                   "Freitag"][
                "winter_value"].to_list()
        elif weekday_list[day_nr] == 5 and season_list[day_nr] == 'summer':
            weight_profile += profile[profile["summer_weekday"] == "Samstag"][
                "summer_value"].to_list()
        elif weekday_list[day_nr] == 5 and season_list[day_nr] == 'transition':
            weight_profile += profile[profile["trans_weekday"] == "Samstag"][
                "trans_value"].to_list()
        elif weekday_list[day_nr] == 5 and season_list[day_nr] == 'winter':
            weight_profile += profile[profile["winter_weekday"] == "Samstag"][
                "winter_value"].to_list()
        elif weekday_list[day_nr] == 6 and season_list[day_nr] == 'summer':
            weight_profile += profile[profile["summer_weekday"] == "Sonntag"][
                "summer_value"].to_list()
        elif weekday_list[day_nr] == 6 and season_list[day_nr] == 'transition':
            weight_profile += profile[profile["trans_weekday"] == "Sonntag"][
                "trans_value"].to_list()
        elif weekday_list[day_nr] == 6 and season_list[day_nr] == 'winter':
            weight_profile += profile[profile["winter_weekday"] == "Sonntag"][
                "winter_value"].to_list()

    weight_profile_1h = []
    for weight_nr in range(int(len(weight_profile) / 4)):
        weight_profile_1h.append(weight_profile[4 * weight_nr] +
                                 weight_profile[4 * weight_nr + 1] +
                                 weight_profile[4 * weight_nr + 2] +
                                 weight_profile[4 * weight_nr + 3])

    # generate the last profile according to the annual consumption and
    # weight profile.
    profile_1h = [i * annual_value / sum(weight_profile_1h) for i in
                  weight_profile_1h]

    return profile_1h


if __name__ == "__main__":
    pass
