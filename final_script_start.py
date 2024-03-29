import arcpy
import os
import sys
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


# Global Variables to hold file paths for sanity reasons they're here for now
airports_FP = ""
existing_charging_FP = ""
cinemas_FP = ""
facilities_FP = ""
gas_FP = ""
malls_FP = ""
picnic_FP = ""
province_FP = ""


# First thing grab the info from the users
folder_location = arcpy.GetParameterAsText(0)
final_results = arcpy.GetParameterAsText(1)
output_folder = arcpy.GetParameterAsText(2)

# =====================================HELPERS=================================#


def do_feature_to_point(features_lst, output_name, point_loc="CENTROID"):
    # https://pro.arcgis.com/en/pro-app/tool-reference/data-management/feature-to-point.htm

    if len(features_lst) < 1 :
        info_print("Did not provide enough features for feature to point")

    try:
        arcpy.FeatureToPoint_management(features_lst, output_name, point_loc)
        return output_name
    except Exception as e:
        error_print("FTP failed on outputting for " + output_name + " with error " + str(e))
    return None


def do_erase_points(points_file, boundaries):
    # https://desktop.arcgis.com/en/arcmap/10.3/tools/editing-toolbox/erase-point.htm

    try:
        arcpy.ErasePoint_edit(points_file, boundaries, "INSIDE")
    except Exception as e:
        error_print("Hit error while trying to Erase points produced error: " + str(e))


def do_intersect(features_lst, output_name, join="ALL"):
    # https://pro.arcgiscmd.com/en/pro-app/tool-reference/analysis/intersect.htm

    info_print("Doing Intersect for " + output_name)
    if len(features_lst) < 1:
        info_print("Did not provide enough features for intersect")

    for i in features_lst:
        debug_print("item " + i)

    try:
        arcpy.Intersect_analysis(features_lst, output_name, join)
    except Exception as e:
        error_print("Hit error while trying to intersect files, produced error" + str(e))


def do_buffer(points_file, dist_to_buf):
    debug_print("do_buffer is Buffering point file " + points_file)
    new_split_name = points_file.split('.')
    new_out_name = new_split_name[0] + '_buffered.' + new_split_name[1]

    try:
        arcpy.Buffer_analysis(points_file, new_out_name, dist_to_buf)
        return new_out_name
    except Exception as e:
        error_print("Hit error while trying to buffer point {}, produced error".format(points_file) + str(e))


def check_exists(dict_name):

    info_print("Checking inside of " + dict_name + " for a shape file")
    folder_name = str(dict_name)
    if folder_name not in directories:
        info_print(folder_name + " not present in root dir")
        exit(1)

    check_src = []

    for items in os.listdir(folder_location + '/' + folder_name + '/'):
        if items.endswith('.shp'):
            info_print("Using: {}".format(items))
            check_src.append(items)
        else:
            debug_print("Ignoring file: {}".format(items))

    if not len(check_src):
        error_print("No files found inside of" + folder_name)
        exit(1)

    return check_src


def get_FP(dirs_in_folder, folder_name):
    info_print("Looking for file path to " + folder_name)
    for item in dirs_in_folder:
        temp_path = folder_location + '/' + folder_name + '/' + item
        temp_type = arcpy.Describe(temp_path).shapeType
        if(temp_type == "Point") or (temp_type == "Polygon"):
            return temp_path
        else:
            debug_print("Unaccounted for file type: {} in file {}".format(temp_type, item))
        return None


def create_folder():
    try:
        os.mkdir(folder_location + '/' + output_folder)
    except Exception as e:
        error_print("Hit error while trying to create a new folder produced error: " + str(e))


# =====================================END OF HELPERS==========================#

# ================== env setup ================================================#
create_folder()
directories = os.listdir(folder_location)

debug_print("Setting workspace...")
arcpy.env.workspace = folder_location

# ====================================Parking Lots ============================#

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

polygon_files = []
point_files = []

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
    points = str(points)
    debug_print("Buffering point file: " + points)
    split_name = points.split('.')
    out_name = split_name[0] + str('_buffered.') + split_name[1]
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
        #debug_print("Point {} has fields {}".format(points, field.name))
        if(not re.match("(.*)shape(.*)", field.name, flags=re.IGNORECASE)):
            if(field.name.upper() not in ["FID", "OID", "AREA", "POLY_AREA", "AREA_GEO", "BUFF_DIST", "Shape"]):
                debug_print("Deleteing attribute {} on point {}".format(field.name, out_name))
                to_delete.append(field.name)
    for delete in to_delete:
       # debug_print("Currently deleting attributes on file: " + out_name)
        arcpy.DeleteField_management(out_name, delete)


debug_print(output_locations)
parking_lot_buffered = "parking_lot_buffered_merged.shp"
try:
    info_print("Now attempting to merge all shapes together, wish me luck!")
    arcpy.Merge_management(output_locations, parking_lot_buffered)
except Exception as e:
    error_print("Hit error while merging all shapes together, error produced is: " + str(e))


# Get roads file and pull major roads and highways from it
# ===================================Buffered Roads============================#
info_print("Pulling all major roads from roads shp file")
roads = folder_location + '/ParkingLot_Data/Ontario_Roads.shp'

try:
    arcpy.MakeFeatureLayer_management(roads, 'major_roads')
    arcpy.SelectLayerByAttribute_management('major_roads', 'NEW_SELECTION', 'RANK < \'4\'')
    # Write the selected features to a new feature class
    arcpy.CopyFeatures_management('major_roads', 'major_roads.shp')
except Exception as e:
    error_print("Hit error when extracting roads from Ontario_Roads, error is:" + str(e))

info_print("Buffering Roads")
buffered_roads = folder_location + '/major_roads_buffered.shp'
arcpy.Buffer_analysis(folder_location + "/major_roads.shp", buffered_roads, '500 Meters', "", "ROUND", "ALL", "")


# ======================================Airports===============================#
airport_lst_src = check_exists("airports")
airports_FP = get_FP(airport_lst_src, "airports")
if (airports_FP is None):
    info_print("airports_FP did not find a shape file for usage")


# =====================================Current Charging Stations ==============#
charging_lst_src = check_exists("charging_stations")
existing_charging_FP = get_FP(charging_lst_src, "charging_stations")
if (existing_charging_FP is None):
    info_print("existing_charging_FP did not find a shape file for usage")


charging_station_buffer = do_buffer(existing_charging_FP, '500 Meters')

# =====================================Cinemas=================================#
cinemas_lst_src = check_exists("cinemas")
cinemas_FP = get_FP(cinemas_lst_src, "cinemas")
if (cinemas_FP is None):
    info_print("cinemas_FP did not find a shape file for usage")

cinemas_buffer = do_buffer(cinemas_FP, '150 Meters')

# =====================================Specific Local Parks====================#
facilities_lst_src = check_exists("facilities")
facilities_FP = get_FP(facilities_lst_src, "facilities")
if (facilities_FP is None):
    info_print("facilities_FP did not find a shape file for usage")

facilities_buffer = do_buffer(facilities_FP, '150 Meters')


# =====================================Gas Stations============================#
gas_station_lst_src = check_exists("Gas_Stations_Points_Ontario")
gas_FP = get_FP(gas_station_lst_src, "Gas_Stations_Points_Ontario")
if (gas_FP is None):
    info_print("gas_FP did not find a shape file for usage")

gas_buffer = do_buffer(gas_FP, '50 Meters')


# =====================================Malls===================================#
mall_lst_src = check_exists("Malls_Shopping_Hubs")
malls_FP = get_FP(mall_lst_src, "Malls_Shopping_Hubs")
if (malls_FP is None):
    info_print("malls_FP did not find a shape file for usage")

malls_buffer = do_buffer(malls_FP, '150 Meters')

# =====================================Picnic Parks============================#
picnic_lst_src = check_exists("picnic_parks_projections")
picnic_FP = get_FP(picnic_lst_src, "picnic_parks_projections")
if (picnic_FP is None):
    info_print("picnic_FP did not find a shape file for usage")

picnic_buffer = do_buffer(picnic_FP, '150 Meters')


# =====================================Provincal Parks=========================#
province_lst_src = check_exists("provincial_parks_projected")
province_FP = get_FP(province_lst_src, "provincial_parks_projected")
if (province_FP is None):
    info_print("province_FP did not find a shape file for usage")


# ======================================== Do intersection and pray ===========#
lst_intersect = [
                cinemas_buffer, picnic_buffer, gas_buffer, facilities_buffer,
                malls_buffer, province_FP, airports_FP, parking_lot_buffered
                ]

lst_for_merging = []
for i in range(len(lst_intersect)):
    split = lst_intersect[i].split('.')
    new_name = split[0] + '_inter.shp'
    do_intersect([lst_intersect[i], buffered_roads], new_name)
    new_aggregate = split[0] + '_agg.shp'
    arcpy.AggregatePolygons_cartography(new_name, new_aggregate, '30 Meters', "", "" , False , "", "")
    lst_for_merging.append(split[0] + '_FTP.shp')
    do_feature_to_point(new_aggregate, lst_for_merging[i], "INSIDE")

try:
    info_print("Trying to Merge final EV locations")
    arcpy.Merge_management(lst_for_merging, final_results)
except Exception as e:
    debug_print("Failed on final EV_location merging")
# ====== Subtract from existing charging here ======#
do_erase_points(final_results, charging_station_buffer)

