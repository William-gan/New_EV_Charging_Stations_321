import arcpy
import os, sys
import re

debug_print_enabled = bool(sys.argv[1]) if len(sys.argv) > 1 else False

arcpy.env.overwriteOutput = True

def debug_print(string):
    if(debug_print_enabled):
        print("[DEBUG]: {}".format(string))

def info_print(string):
    print("[INFO]: {}".format(string))

def error_print(string):
    print("[ERROR]: {}".format(string))


#Global Variables to hold file paths for sanity reasons they're here for now
airports_FP = ""
existing_charging_FP = ""
cinemas_FP = ""
facilities_FP = ""
gas_FP = ""
malls_FP = ""
picnic_FP = ""
province_FP = "'"

#======================================HELPERS=============================================# 
def do_intersect(features_lst, output_name):
    #https://pro.arcgis.com/en/pro-app/tool-reference/analysis/intersect.htm
    return None 

def create_folder(name):
    try:
        new_dir = folder_location + '/' + name
        # 0 clue if this works be CAREFUL
        # if (os.path.exists(new_dir)):
        #    arcpy.Delete_management(new_dir)
        # else:
        os.mkdir(new_dir)
        return new_dir
    except Exception as e:
        error_print("Hit error while creating new output dir for " + name + " use")

def do_buffer(points_file, dist_to_buf):
    debug_print("Buffering point file" + points_file)
    split_name = points_file.split('.')
    out_name = split_name[0] + '_buffered.' + split_name[1]
    # output_file = str(create_folder(out_name)) + out_name

    try:
        arcpy.Buffer_analysis(points_file, out_name, dist_to_buf)
        return out_name
    except Exception as e:
        error_print("Hit error while trying to buffer point {}, produced error".format(points) + str(e))

def check_exists (dict_name):
    folder_name = str(dict_name)
    if(folder_name not in directories):
        info_print(folder_name + " not present in root dir")
        exit(1)
    
    check_src = []

    for items in os.listdir(folder_location + '/' + folder_name + '/'):
        if items.endswith('.shp'):
            info_print("Using: {}".format(items))
            check_src.append(items)
        else:
            debug_print("Ignoring file: {}".format(items))
    
    if (not len(check_src)):
        error_print("No files found inside of" + folder_name)
        exit(1)
    
    return check_src


def get_FP (dirs_in_folder, folder_name):
    for item in dirs_in_folder:
        temp_path = folder_location + '/' + folder_name + '/' + item
        temp_type = arcpy.Describe(temp_path).shapeType
        if(file_type == "Point") or (file_type == "Polygon"):
            return temp_path
        else:
            debug_print("Unaccounted for file type: {} in file {}".format(temp_type, item))
        return None

def get_roads(road_shapefile):
    pass

#======================================END OF HELPERS=============================================# 


#Global Function variable here used by everyone

folder_location = raw_input("Please input where the files are located (root folder of project): ")
while(not os.path.exists(folder_location)):
    debug_print(folder_location)
    folder_location =  raw_input("Bruh give me an actual path: ")

# =====================================Parking Lots ===============================#
# ==========Special Case since theres a lot of data at once ================# 
#https://www150.statcan.gc.ca/n1/pub/92-500-g/92-500-g2020001-eng.htm --> recommend Rank  or class type to get major/highway# 
directories = os.listdir(folder_location)
if("ParkingLot_Data" not in directories):
    info_print("Bro you need to give me ParkingLot_Data as a directory kinda cringe")
    exit(1)

parking_lot_source = []

for f in os.listdir(folder_location + '/' + 'ParkingLot_Data/'):
    if f.endswith('.shp') and f != 'Ontario_boundary_pr.shp':
        info_print("Using: {}".format(f))
        parking_lot_source.append(f)
    else:
        debug_print("Ignoring file: {}".format(f))

if len(parking_lot_source) == 0:
    error_print("No files found exiting...")
    exit(1)

debug_print("Setting workspace...")
arcpy.env.workspace = folder_location

polygon_files = []
point_files = []

first_polygon = ""

for shp in parking_lot_source:
    file_path = folder_location + '/ParkingLot_Data/' + shp
    file_type = arcpy.Describe(file_path).shapeType
    if(file_type == "Point"):
        point_files.append(shp)
    elif(file_type == "Polygon"):
        polygon_files.append(file_path)
    else:
        debug_print("Unaccounted for file type: {} in file {}".format(file_type, shp))

for polygon in polygon_files:
    debug_print("Working on file: " + polygon)
    field_list = arcpy.ListFields(polygon)
    to_delete = []
    arcpy.AddGeometryAttributes_management(polygon, "AREA")
    # disable cause there's an issue
    for field in field_list:
        if(not re.match("(.*)shape(.*)", field.name, flags=re.IGNORECASE)):
            if(field.name.upper() not in ["FID", "OID", "AREA", "POLY_AREA"]):
                debug_print("Deleteing attribute {} on polygon {}".format(field.name, polygon))
                to_delete.append(field.name)
    for delete in to_delete:
        debug_print("Currently deleting attributes on file: " + polygon)
        arcpy.DeleteField_management(polygon, delete)
try:
    info_print("Now attempting to merge all polygons together, wish me luck!")
    arcpy.Merge_management(polygon_files, "merged_polygons.shp")
except Exception as e:
    error_print("Hit error while merging, error produced is: " + str(e))

info_print("Now attempting to buffer points")
output_locations = [folder_location + "\\merged_polygons.shp"]

for points in point_files:
    debug_print("Buffering point file: " + points)
    split_name = points.split('.')
    out_name = split_name[0] + '_buffered.' + split_name[1]
    output_locations.append(folder_location + '\\' + out_name)
    try:
        # 338.084881 is from arcmap I'm not doing the statistics thing on this thanks
        arcpy.Buffer_analysis(file_path + '/ParkingLot_Data/' + points, out_name, "50 Feet")
    except Exception as e:
        error_print("Hit error while trying to buffer point {}, produced error".format(points) + str(e))

    arcpy.AddGeometryAttributes_management(out_name, "AREA_GEODESIC")
    field_list = arcpy.ListFields(out_name)
    to_delete = []
    for field in field_list:
        debug_print("Point {} has fields {}".format(points, field.name))
        if(not re.match("(.*)shape(.*)", field.name, flags=re.IGNORECASE)):
            if(field.name.upper() not in ["FID", "OID", "AREA", "POLY_AREA", "AREA_GEO", "BUFF_DIST", "Shape"]):
                debug_print("Deleteing attribute {} on point {}".format(field.name, out_name))
                to_delete.append(field.name)
    for delete in to_delete:
        debug_print("Currently deleting attributes on file: " + out_name)
        arcpy.DeleteField_management(out_name, delete)


debug_print(output_locations)

try:
    info_print("Now attempting to merge all shapes together, wish me luck!")
    arcpy.Merge_management(output_locations, "final_merged.shp")
except Exception as e:
    error_print("Hit error while merging all shapes together, error produced is: " + str(e))
    

# Get roads file and pull major roads and highways from it
info_print("Pulling all major roads from roads shp file")
roads = folder_location + '/ParkingLot_Data/Ontario_Roads.shp'

try:
    arcpy.MakeFeatureLayer_management(roads,'major_roads')
    arcpy.SelectLayerByAttribute_management('major_roads', 'NEW_SELECTION', 'RANK < \'4\'')
    # Write the selected features to a new featureclass
    arcpy.CopyFeatures_management('major_roads', 'major_roads.shp')
except Exception as e:
    error_print("Hit error when extracting roads from Ontario_Roads, error is:" + str(e))

info_print("buffered_roads")
buffered_roads = do_buffer(folder_location +"/major_roads.shp",'500 Meters')


#Unsure how we want to handle the folder names since its kind of specific naming we used so unless user provides? 
#maybe then we can sub out the hardcoded strings 
#======================================Airports=============================================# 
airport_lst_src = check_exists("airports")
airports_FP = get_FP(airport_lst_src, "airports")
if (airports_FP is None):
    info_print("airports_FP did not find a shape file for usage")


#======================================Current Charging Stations ===========================#
charging_lst_src = check_exists("charging_station")
existing_charging_FP = get_FP(charging_lst_src, "charging_station")
if (existing_charging_FP is None):
    info_print("existing_charging_FP did not find a shape file for usage")

#======================================Cinemas==============================================#
cinemas_lst_src = check_exists("cinemas")
cinemas_FP = get_FP(cinemas_lst_src, "cinemas")
if (cinemas_FP is None):
    info_print("cinemas_FP did not find a shape file for usage")

#======================================Specific Local Parks=================================#
facilities_lst_src = check_exists("facilities")
facilities_FP = get_FP(facilities_lst_src, "facilities")
if (facilities_FP is None):
    info_print("facilities_FP did not find a shape file for usage")

#======================================Gas Stations=========================================#
gas_station_lst_src = check_exists("Gas_Stations_Points_Ontario")
gas_FP = get_FP(gas_station_lst_src, "Gas_Stations_Points_Ontario")
if (gas_FP is None):
    info_print("gas_FP did not find a shape file for usage")

#======================================Malls================================================#
mall_lst_src = check_exists("Malls_Shopping_Hubs")
malls_FP = get_FP(mall_lst_src, "Malls_shopping_Hubs")
if (malls_FP is None):
    info_print("malls_FP did not find a shape file for usage")

#======================================Picnic Parks=========================================#
picnic_lst_src = check_exists("picnic_parks_projections")
picnic_FP = get_FP(picnic_lst_src, "picnic_parks_projections")
if (picnic_FP is None):
    info_print("picnic_FP did not find a shape file for usage")

#======================================Provincal Parks======================================#
province_lst_src = check_exists("provincial_parks_projected")
province_FP = get_FP(province_lst_src, "provincial_parks_projected")
if (province_FP is None):
    info_print("province_FP did not find a shape file for usage")

