import asyncio
import json
import os
from math import sin, cos, sqrt, atan2, radians
from decimal import Decimal
from map import structures_searchbysity
from map import get_city_districts
from map import convert_decimal_to_float
from map import RegionInfo

region_structures = { "school", "kindergarten", "language_school", "music_school", "college", "university", "driving_school", "training", "driving_school", "dancing_school" }
city_structures = { "theme_park", "zoo", "national_park", "park", "water_park", "trampoline_park", "fountain", "place_of_worship", "playground" }
positive_structures = { "civic", "stadium", "riding_hall", "sports_hall", "cycleway", "ice_rink", "footway", "pitch", "track", "marketplace", "greengrocer", "farm", "playground" }
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
                            dist_dict = { "Тип": dest_type, "МейнНазвание": structure["Название"], "Название": dest_structure["Название"], "Дистанция": round(dist, 2) }
                            if not dist_dict in distances:
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
        
def calculate_factor(value):
    if value <= 0.1:
        return 0
    elif value >= 0.2:
        return 1
    else:
        return (value - 0.1) / (0.2 - 0.1)

async def parse_city(city):
    live_prompt = []
    live_quality = 0
    average_negative_distance = 0
    negative_distances_count = 0
    data = structures_searchbysity(city)
    
    if not os.path.exists(f"app_cache\\results\\{city}"):
        os.makedirs(f"app_cache\\results\\{city}")
    
    for main_structure in city_structures:
        negative_dists = get_distances_of_type(data, main_structure, negative_structures, 0.4)
        for dist in negative_dists:
            average_negative_distance += dist["Дистанция"]
        negative_distances_count += len(negative_dists)
        #print_distances(main_structure, negative_dists)
    if negative_distances_count != 0:
        average_negative_distance = average_negative_distance / negative_distances_count
    else:
        average_negative_distance = None
        
    if average_negative_distance != None:
        print(f"Средняя дистанция негативных объектов до парков поблизости: {round(average_negative_distance, 2)} км")
        factor = calculate_factor(average_negative_distance)
        live_quality = live_quality + (30 * factor)
        if factor < 0.2:
            live_prompt.append(f"Необходимо ограничить парки от табачной и алкогольной продукции. Средняя дистанция до парков: {average_negative_distance}")    
        
    rayons = get_city_districts(city)
    
    positive_rayons = 0
    negative_rayons = 0
    
    tasks = []
    for rayon_name in rayons:
        tasks.append(parse_region(city, rayon_name, live_prompt))
    results = await asyncio.gather(*tasks)
    
    rayons_info = []
    for rayon_data in results:
        rayons_info.append({
            "Название": rayon_data.reg_name,
            "Баллы": rayon_data.live_quality
        })
        if rayon_data.positive_structures_count > 1.5 * rayon_data.negative_structures_count:
            positive_rayons += 1
        else:
            negative_rayons += 1
            live_prompt.append(f"В {rayon_data.reg_name} положительные структуры не преобладают на 50% над негативными структурами: {rayon_data.positive_structures_count} vs {1.5 * rayon_data.negative_structures_count}")

    with open(f"app_cache\\results\\{city}\\rayons.json", "w", encoding="utf-8") as json_file:
        json.dump(rayons_info, json_file, ensure_ascii=False, indent=4, default=convert_decimal_to_float)

    live_quality = live_quality + (70 * (positive_rayons / len(rayons)))
        
    print(f"Хороших районов {positive_rayons} из {len(rayons)}")
    print(f"Качество жизни города {city}: {live_quality}")

    with open(f"app_cache\\results\\{city}\\prompt.json", "w", encoding="utf-8") as json_file:
        json.dump(live_prompt, json_file, ensure_ascii=False, indent=4, default=convert_decimal_to_float)
        
    with open(f"app_cache\\results\\{city}\\info.json", "w", encoding="utf-8") as json_file:
        linfo = {
            "LifeQuality": live_quality,
            "Name": city,
            "PositiveRayons": positive_rayons,
            "AllRayons": len(rayons)
        }
        json.dump(linfo, json_file, ensure_ascii=False, indent=4, default=convert_decimal_to_float)
        
    print("prompt:")
    for prompt in live_prompt:
        print(prompt)
        
def parse_saved_data(city):
    linfo = []
    prompt = []
    rayons = []
    
    if os.path.exists(f"app_cache\\results\\{city}\\rayons.json"):
        with open(f"app_cache\\results\\{city}\\rayons.json", 'r', encoding='utf-8') as f:
            rayons = json.load(f)
            
    for rayon in rayons:
        print(f"Качество жизни района {rayon["Название"]}: {rayon["Баллы"]}")        
    
    if os.path.exists(f"app_cache\\results\\{city}\\info.json"):
        with open(f"app_cache\\results\\{city}\\info.json", 'r', encoding='utf-8') as f:
            linfo = json.load(f)
            
    if os.path.exists(f"app_cache\\results\\{city}\\prompt.json"):
        with open(f"app_cache\\results\\{city}\\prompt.json", 'r', encoding='utf-8') as f:
            live_prompt = json.load(f)
            
    print(f"Хороших районов {linfo["PositiveRayons"]} из {linfo["AllRayons"]}")
    print(f"Качество жизни города {city}: {linfo["LifeQuality"]}")
    print("prompt:")
    for prompt in live_prompt:
        print(prompt)
    
        
async def parse_region(city_name, rayon, live_prompt):
    reg_quality_struct_count = []
    live_quality = 0
    data = structures_searchbysity(rayon, city_name)
    
    positive_count = get_structures_count(data, positive_structures)
    negative_count = get_structures_count(data, negative_structures)
    for main_structure in region_structures:
        negative_dists = get_distances_of_type(data, main_structure, negative_structures, 0.1)
        if len(negative_dists) != 0:
            for neg_dist in negative_dists:
                live_prompt.append(f"Возле {neg_dist["МейнНазвание"]} ({main_structure}) в радиусе 100м находится {neg_dist["Название"]} ({neg_dist["Тип"]})")
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
    print(f"Качество жизни района {rayon}: {live_quality}")
    
    return RegionInfo(rayon, positive_structs_count, reg_quality_struct_count, live_quality, positive_count, negative_count)
    
#print(len(tobacco_searchbysity("Сочи")))
#asyncio.run(parse_city("Ростов-на-Дону"))
parse_saved_data("Ростов-на-Дону")
#print(get_city_districts("Советский район"))