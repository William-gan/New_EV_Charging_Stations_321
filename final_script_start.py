import arcpy
import os
import re

folder_location = raw_input("Please input where the files are located (root folder of project): ")

while(not os.path.exists(folder_location)):
    print(folder_location)
    print(os.path.exists(folder_location))
    folder_location =  raw_input("Bruh give me an actual path: ")

directories = os.listdir(folder_location)
if("ParkingLot_Data" not in directories):
    print("Bro you need to give me ParkingLot_Data as a directory kinda cringe")
    exit(1)

parking_lot_source = []

for f in os.listdir(folder_location + '/' + 'ParkingLot_Data/'):
    if f.endswith('.shp'):
        print("Using: {}\n".format(f))
        parking_lot_source.append(f)
    else:
        print("Ignoring file: {}\n".format(f))

if len(parking_lot_source) == 0:
    print("No files found exiting...")
    exit(1)

print("Setting workspace to C:/data...\n")
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
        polygon_files.append(shp)
    else:
        print("Unaccounted for file type: {} in file {}".format(file_type, shp))

for points in point_files:
    split_name = points.split('.')
    out_name = split_name[0] + '_buffered' + split_name[1]
    arcpy.Buffer_analysis(file_path + '/ParkingLot_Data/' + shp, out_name, 10)