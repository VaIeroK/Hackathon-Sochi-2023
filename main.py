import overpy
import json
import asyncio
from math import sin, cos, sqrt, atan2, radians
from decimal import Decimal
from map import structures_searchbysity
from map import get_city_districts
from map import RegionInfo

region_structures = { "school", "kindergarten", "language_school", "music_school", "college", "university", "driving_school", "training" }
city_structures = { "theme_park", "zoo", "national_park", "park", "water_park", "trampoline_park", "fountain", "place_of_worship" }
positive_structures = { "civic", "stadium", "riding_hall", "sports_hall", "cycleway", "ice_rink", "footway", "pitch", "track", "marketplace", "greengrocer", "farm" }
negative_structures = { "tobacco", "kiosk", "alcohol", "pub", "fast_food", "food_court", "bar", "biergarten", "beverages", "wine" }

def distance(lat1, lon1, lat2, lon2):
    R = 6371.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance
        
def get_distances_of_type(data, src_type, dest_type_list, max_radius = -1):
    distances = []
    for structure in data:
        if structure["Тип"] == src_type:
            for dest_structure in data:
                for dest_type in dest_type_list:
                    if dest_structure["Тип"] == dest_type:
                        dist = distance(structure["Широта"], structure["Долгота"], dest_structure["Широта"], dest_structure["Долгота"])
                        if dist < max_radius or max_radius == -1:
                            dist_dict = { "Тип": dest_type, "Дистанция": round(dist, 2) }
                            distances.append(dist_dict)
    return distances

def get_structures_count(data, type_list):
    count = 0
    for structure in data:
        for type in type_list:
            if structure["Тип"] == type:
                count += 1
    return count

def print_distances(main_structure, distances):
    for dist in distances:
        print(f"Дистанция {dist["Тип"]} до {main_structure}: {dist["Дистанция"]} км")

async def parse_city(city):
    live_quality = 0
    average_negative_distance = 0
    negative_distances_count = 0
    data = structures_searchbysity(city)
    
    for main_structure in city_structures:
        negative_dists = get_distances_of_type(data, main_structure, negative_structures, 0.3)
        for dist in negative_dists:
            average_negative_distance += dist["Дистанция"]
        negative_distances_count += len(negative_dists)
        #print_distances(main_structure, negative_dists)
    average_negative_distance = average_negative_distance / negative_distances_count
        
    print(f"Средняя дистанция негативных объектов до парков поблизости: {round(average_negative_distance, 2)} км")
    if average_negative_distance > 0.2:
        live_quality = live_quality + 30
        
    rayons = get_city_districts(city)
    positive_rayons = 0
    negative_rayons = 0
    
    
    tasks = []
    for rayon_name in rayons:
        tasks.append(parse_region(rayon_name))
    results = await asyncio.gather(*tasks)
    
    for rayon_data in results:
        if rayon_data.positive_structures_count > 1.5 * rayon_data.negative_structures_count:
            positive_rayons += 1
        else:
            negative_rayons += 1

    diff = positive_rayons - negative_rayons
    if diff >= 1:
        live_quality = live_quality + 70
        
    print(f"Хороших районов {diff} из {len(rayons)}")
    print(f"Качество жизни города {city}: {live_quality}")
        
async def parse_region(city):
    reg_quality_struct_count = []
    live_quality = 0
    data = structures_searchbysity(city)
    
    positive_count = get_structures_count(data, positive_structures)
    negative_count = get_structures_count(data, negative_structures)
    for main_structure in region_structures:
        negative_dists = get_distances_of_type(data, main_structure, negative_structures, 0.1)
        reg_quality_struct_count.append({
            "ТочкаИнтереса": main_structure,
            "Благополучность": (len(negative_dists) == 0)
        })
        
    positive_structs_count = 0
    for struct in reg_quality_struct_count:
        if struct["Благополучность"] == True:
            positive_structs_count = positive_structs_count + 1
            
    live_quality = live_quality + (40 * (positive_structs_count / len(reg_quality_struct_count)))
        
    if positive_count > 1.5 * negative_count:
        live_quality += 60
        #print(f"Добро и позитив! {positive_count} vs {negative_count}")
    #else:
        #print(f"Зло и негатив! {positive_count} vs {negative_count}")
    print(f"Качество жизни района {city}: {live_quality}")
    return RegionInfo(positive_structs_count, reg_quality_struct_count, live_quality, positive_count, negative_count)
    
#print(len(tobacco_searchbysity("Сочи")))
asyncio.run(parse_city("Ростов-на-Дону"))
#print(get_city_districts("Советский район"))
    

    