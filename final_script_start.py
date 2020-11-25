import arcpy
import os, sys
import re

debug_print_enabled = bool(sys.argv[1]) if len(sys.argv) > 1 else False

def debug_print(string):
    if(debug_print_enabled):
        print("[DEBUG]: {}".format(string))

def info_print(string):
    print("[INFO]: {}".format(string))

def error_print(string):
    print("[ERROR]: {}".format(string))

folder_location = raw_input("Please input where the files are located (root folder of project): ")

while(not os.path.exists(folder_location)):
    debug_print(folder_location)
    folder_location =  raw_input("Bruh give me an actual path: ")

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

debug_print("Setting workspace to C:/data...")
arcpy.env.workspace = "C:\\data"

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
    # disable cause there's an issue
    # for field in field_list:
    #     if(not re.match("(.*)shape(.*)", field.name, flags=re.IGNORECASE)):
    #         if(field.name not in ["FID", "OID", "AREA"]):
    #             to_delete.append(field.name)
    debug_print("Currently deleting attributes on file: " + polygon)
    arcpy.AddGeometryAttributes_management(polygon, "AREA")
    arcpy.DeleteField_management(polygon, "ADDRESS")

try:
    info_print("Now attempting to merge all polygons together, wish me luck!")
    arcpy.Merge_management(polygon_files, "merged.shp")
except Exception as e:
    error_print("Hit error while merging, error produced is: " + str(e))

info_print("Now attempting to buffer points")
output_locations = ["c:\\data\\merged.shp"]
for points in point_files:
    debug_print("Buffering point file: " + points)
    split_name = points.split('.')
    out_name = split_name[0] + '_buffered.' + split_name[1]
    output_locations.append("c:\\data\\" + out_name)
    try:
        # 338.084881 is from arcmap I'm not doing the statistics thing on this thanks
        arcpy.Buffer_analysis(file_path + '/ParkingLot_Data/' + shp, out_name, 338.084881)
    except Exception as e:
        error_print("Hit error while trying to buffer point {}, produced error".format(points) + str(e))

try:
    info_print("Now attempting to merge all shapes together, wish me luck!")
    arcpy.Merge_management(output_locations, "final_merged.shp")
except Exception as e:
    error_print("Hit error while merging all shapes together, error produced is: " + str(e))
