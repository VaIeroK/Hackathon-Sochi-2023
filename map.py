import overpy
import json
import os
from decimal import Decimal

ignore_structures = { "restaurant", "parking", "cafe", "fuel" } #Игнор популярных структур для оптимизации

class RegionInfo:
    def __init__(self, positive_main_structs_size, main_structs_quality_array, live_quality, positive_structures_count, negative_structures_count):
        self.positive_main_structs_size = positive_main_structs_size
        self.main_structs_quality_array = main_structs_quality_array
        self.live_quality = live_quality
        self.positive_structures_count = positive_structures_count
        self.negative_structures_count = negative_structures_count

def convert_decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def load_cache(Name):
    if not os.path.exists("app_cache"):
        os.makedirs("app_cache")
    if os.path.exists(f"app_cache\\{Name}.json"):
        with open(f"app_cache\\{Name}.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    else:
        return None

def parks_searchbysity(Name):
    api = overpy.Overpass()
    data = load_cache(Name)
    
    if data == None: 
        data = []
        osm_query = f"""
        [out:json][timeout:250];
        area["name"="{Name}"]->.searchArea;
        way(area.searchArea)["leisure"];
        out center;
        """

        result = api.query(osm_query)

        for way in result.ways:
            struct_type = way.tags.get("leisure", "Не указано")
            if struct_type in ignore_structures:
                continue
            data.append({
                "Тип": struct_type,
                "Широта": way.center_lat,
                "Долгота": way.center_lon
            })
        with open(f"app_cache\\{Name}.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4, default=convert_decimal_to_float)
    return data

def tobacco_searchbysity(Name):
    api = overpy.Overpass()
    data = load_cache(Name)
    
    if data == None: 
        data = []
        osm_query = f"""
        [out:json][timeout:250];
        area["name"="{Name}"]->.searchArea;
        (
        nwr["shop"="tobacco"](area.searchArea);
        nwr["shop"="kiosk"](area.searchArea);
        );
        out center;
        """

        result = api.query(osm_query)

        for way in result.ways:
            data.append({
                "Тип": "tobacco",
                "Название": way.tags.get("name", "Без названия"),
                "Широта": way.center_lat,
                "Долгота": way.center_lon
            })
        with open(f"app_cache\\{Name}.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4, default=convert_decimal_to_float)

    return data

def structures_searchbysity(Name):
    api = overpy.Overpass()
    data = load_cache(Name)
    
    if data == None: 
        data = []
        osm_query = f"""
        [out:json][timeout:250];
        area["name"="{Name}"]->.searchArea;
        way(area.searchArea)["amenity"];
        out center;
        """

        result = api.query(osm_query)

        for way in result.ways:
            struct_type = way.tags.get("amenity", "Не указано")
            if struct_type in ignore_structures:
                continue
            data.append({
                "Тип": struct_type,
                "Название": way.tags.get("name", "Без названия"),
                "Широта": way.center_lat,
                "Долгота": way.center_lon
            })
        with open(f"app_cache\\{Name}.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4, default=convert_decimal_to_float)
    data.extend(tobacco_searchbysity(Name))
    data.extend(parks_searchbysity(Name))
    return data

def get_city_districts(city_name, admlevel=8):
    api = overpy.Overpass()
    district_names = load_cache(f"{city_name}_districts")
    
    if district_names == None: 
        district_names = []
        districts_query = f"""
            [out:json];
            area["name"="{city_name}"];
            rel(area)["admin_level"="{admlevel}"];
            out center;
        """

        districts_result = api.query(districts_query)

        for rel in districts_result.relations:
            district_names.append(rel.tags.get("name", "Не указано"))

        if admlevel == 8:
            district_names = district_names + get_city_districts(city_name, admlevel=9)
            
        with open(f"app_cache\\{city_name}_districts.json", "w", encoding="utf-8") as json_file:
            json.dump(district_names, json_file, ensure_ascii=False, indent=4, default=convert_decimal_to_float)

    return district_names