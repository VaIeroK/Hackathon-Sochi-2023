import overpy
import json
import os
import httpx
import asyncio
from decimal import Decimal

region_structures = { "school", "kindergarten", "language_school", "music_school", "college", "university", "driving_school", "training", "driving_school", "dancing_school" }
city_structures = { "theme_park", "zoo", "national_park", "park", "water_park", "trampoline_park", "fountain", "place_of_worship", "playground" }
positive_structures = { "civic", "stadium", "riding_hall", "sports_hall", "cycleway", "ice_rink", "footway", "pitch", "track", "marketplace", "greengrocer", "farm", "playground" }
negative_structures = { "tobacco", "kiosk", "alcohol", "pub", "fast_food", "food_court", "bar", "biergarten", "beverages", "wine" }

class RegionInfo:
    def __init__(self, reg_name, positive_main_structs_size, main_structs_quality_array, live_quality, positive_structures_count, negative_structures_count, sementeries_count):
        self.reg_name = reg_name
        self.positive_main_structs_size = positive_main_structs_size
        self.main_structs_quality_array = main_structs_quality_array
        self.live_quality = live_quality
        self.positive_structures_count = positive_structures_count
        self.negative_structures_count = negative_structures_count
        self.sementeries_count = sementeries_count

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
    
def playgrounds_searchbysity(Name):
    api = overpy.Overpass()

    data = []
    osm_query = f"""
    [out:json][timeout:250];
    area["name"="{Name}"]->.searchArea;
    nwr["leisure"="playground"](area.searchArea);
    out center;
    """

    result = api.query(osm_query)

    for way in result.ways:
        struct_type = way.tags.get("leisure", "Не указано")
        if not struct_type in region_structures and not struct_type in city_structures:
            continue
        struct_name = way.tags.get("name", "null")
        if struct_name == "null":
            continue
        data.append({
            "Тип": struct_type,
            "Название": struct_name,
            "Широта": way.center_lat,
            "Долгота": way.center_lon
        })
    return data

def parks_searchbysity(Name):
    api = overpy.Overpass()
    
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
        if not struct_type in region_structures and not struct_type in city_structures:
            continue
        struct_name = way.tags.get("name", "null")
        if struct_name == "null":
            continue
        data.append({
            "Тип": struct_type,
            "Название": struct_name,
            "Широта": way.center_lat,
            "Долгота": way.center_lon
        })
    return data

def highway_searchbysity(Name):
    api = overpy.Overpass()
    data = []
    osm_query = f"""
    [out:json][timeout:250];
    area["name"="{Name}"]->.searchArea;
    way(area.searchArea)["highway"];
    out center;
    """

    result = api.query(osm_query)

    for way in result.ways:
        struct_type = way.tags.get("highway", "Не указано")
        if not struct_type in region_structures and not struct_type in city_structures and not struct_type in positive_structures and not struct_type in negative_structures:
            continue
        struct_name = way.tags.get("name", "null")
        if struct_name == "null":
            continue
        data.append({
            "Тип": struct_type,
            "Название": struct_name,
            "Широта": way.center_lat,
            "Долгота": way.center_lon
        })
    return data

def fetch_tobacco_shops(city, skip, results_per_page, page, results):
    api_key = "4deae437-2d92-4cb6-a8aa-79e3754c8f35"
    base_url = "https://search-maps.yandex.ru/v1/"

    search_params = {
        "text": f"{city}, табака",
        "type": "biz",
        "lang": "ru_RU",
        "results": results_per_page,
        "apikey": api_key,
        "skip": skip
    }

    with httpx.Client() as client:
        response = client.get(base_url, params=search_params)
        data = response.json()

    if "features" in data:
        for feature in data["features"]:
            name = feature["properties"]["CompanyMetaData"]["name"]
            coordinates = feature["geometry"]["coordinates"]

            result = {
                "Тип": "tobacco",
                "Название": "Помогите(((((( (табачка какая то лол)",
                "Широта": coordinates[1],  
                "Долгота": coordinates[0],
            }

            results.append(result)

def tobacco_searchbysity(Name, data):
    api = overpy.Overpass()
    
    osm_query = f"""
    [out:json][timeout:250];
    area["name"="{Name}"]->.searchArea;
    (
    nwr["shop"="tobacco"](area.searchArea);
    );
    out center;
    """

    result = api.query(osm_query)

    for way in result.ways:
        struct_name = way.tags.get("name", "null")
        if struct_name == "null":
            continue
        data.append({
            "Тип": "tobacco",
            "Название": struct_name,
            "Широта": way.center_lat,
            "Долгота": way.center_lon
        })
            
    num_pages = 10
    results_per_page = 50
    
    for page in range(1, num_pages + 1):
        skip = (page - 1) * results_per_page
        fetch_tobacco_shops(Name, skip, results_per_page, page, data)

def structures_searchbysity(Name, city_name = None):
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
            if not struct_type in region_structures and not struct_type in city_structures and not struct_type in positive_structures and not struct_type in negative_structures:
                continue
            struct_name = way.tags.get("name", "null")
            if struct_name == "null":
                continue
            data.append({
                "Тип": struct_type,
                "Название": struct_name,
                "Широта": way.center_lat,
                "Долгота": way.center_lon
            })
        tobacco_searchbysity(Name, data)
        data.extend(parks_searchbysity(Name))
        data.extend(highway_searchbysity(Name))
        data.extend(playgrounds_searchbysity(Name))
        with open(f"app_cache\\{f"{city_name}_" if city_name != None else ""}{Name}.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4, default=convert_decimal_to_float)
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

def search_cemeteries_in_city(city):
    api = overpy.Overpass()

    osm_query = f"""
    [out:json][timeout:25];
    area["name"="{city}"]->.searchArea;
    (
     way["landuse"="cemetery"](area.searchArea);
    );
    out center;
    """

    result = api.query(osm_query)

    cemeteries = []

    for way in result.ways:
        lat = way.center_lat
        lon = way.center_lon
        name = way.name
        cemeteries.append({
            "Тип": "cemetery",
            "Долгота": lat,
            "Ширина": lon,
            "Название": name
        })

    with open(f"{city}_cemeteries.json", "w", encoding="utf-8") as json_file:
        json.dump(cemeteries, json_file, ensure_ascii=False, indent=4, default=convert_decimal_to_float)