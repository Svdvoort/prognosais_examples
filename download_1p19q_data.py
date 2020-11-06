import os
import shutil
import urllib.request
import zipfile

import numpy as np
import pandas as pd
import requests


GENETIC_DATA_URL = "https://wiki.cancerimagingarchive.net/download/attachments/25789042/TCIA_LGG_cases_159.xlsx?version=1&modificationDate=1509045953290&api=v2"
SCAN_DATA_URL = "https://app.box.com/shared/static/d0ew9t885nktg163ia4r8qntav9boevj"


def download_url(url, save_path, chunk_size=2056):
    # Function to download the zip file in chuncks
    r = requests.get(url, stream=True)
    with open(save_path, "wb") as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)


local_directory = input("In which local directory should the data be saved? (If left blank, will be saved in current folder)")
local_directory = os.path.normpath(local_directory)

if local_directory == ".":
    local_directory = os.getcwd()
    local_directory = os.path.normpath(local_directory)

if not os.path.exists(local_directory):
    create_local_dir = "unselected"
    while create_local_dir.lower() not in ["yes", "no"]:
        create_local_dir = input(
            "Going to save data to {local_dir}, however, this directory does not exist, should it be created? (yes/no) ".format(local_dir=local_directory)
        )

    if create_local_dir == "yes":
        os.makedirs(local_directory)
    else:
        print(
            "Not creating local directory. Please create directory, or specificy a different directory."
        )

zipfile_location = os.path.join(local_directory, "data.zip")

print("Downloading scan data, please wait....")
download_url(SCAN_DATA_URL, zipfile_location)

print("Download completed, extracting data.....")
with zipfile.ZipFile(zipfile_location, "r") as zip_ref:
    zip_ref.extractall(local_directory)

print("Data extracted, organizing data....")
os.remove(zipfile_location)

# This is the default name of the zip
full_patient_data_path = os.path.join(local_directory, "NiFTiSegmentationsEdited")
scan_data_dir = os.path.join(local_directory, "scan_data")
shutil.move(full_patient_data_path, scan_data_dir)

for root, dir, files in os.walk(scan_data_dir):
    # Here we fix to make sure that the naming of fies is consistent for all patients
    for i_file in files:
        if "T1" in i_file:
            shutil.move(os.path.join(root, i_file), os.path.join(root, "T1.nii.gz"))
        elif "T2" in i_file and "LGG-223" not in root:
            shutil.move(os.path.join(root, i_file), os.path.join(root, "T2.nii.gz"))
        elif "T2" in i_file and "LGG-223" in root:
            # There is an error for patient LGG-223, the scan indicated as T2 is actually the mask
            shutil.move(os.path.join(root, i_file), os.path.join(root, "MASK.nii.gz"))
        elif "LGG-223" not in root:
            shutil.move(os.path.join(root, i_file), os.path.join(root, "MASK.nii.gz"))
        else:
            shutil.move(os.path.join(root, i_file), os.path.join(root, "T2.nii.gz"))

print("Scan data organized, downloading genetic data....")
urllib.request.urlretrieve(
    GENETIC_DATA_URL, os.path.join(local_directory, "genetics.xlsx")
)
print("Genetic data downloaded, transforming into label file....")
out_label_file = os.path.join(local_directory, "patient_labels.tsv")

# Now we need to transform this file into one with labels we can work with
df = pd.read_excel(os.path.join(local_directory, "genetics.xlsx"))
patient_IDs = df["Filename"].to_numpy()
genetic_status = df["1p/19q"].to_numpy()

for i_i_genetic_status, i_genetic_status in enumerate(genetic_status):
    if i_genetic_status == "d/d":
        genetic_status[i_i_genetic_status] = 1
    elif i_genetic_status == "n/n":
        genetic_status[i_i_genetic_status] = 0

with open(out_label_file, "w") as the_file:
    the_file.write("Image\t1p19q\n")
    for i_patient_id, i_genetic_status in zip(patient_IDs, genetic_status):
        the_file.write(i_patient_id + "\t" + str(i_genetic_status) + "\n")

print("Data downloading and preparation done!")
print("Use the following as your input_folder: {input_folder}".format(input_folder=scan_data_dir))
print("Use the following as the label file: {label_file}".format(label_file=out_label_file))

