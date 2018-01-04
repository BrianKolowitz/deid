#!/usr/bin/env python3
import os
import pydicom
from deid.config import load_deid
from deid.dicom import DicomCleaner
from deid.utils import get_installdir

# This is a complete example of using the cleaning client to inspect
# and clean pixels 
# based on a deid.dicom specification
# https://pydicom.github.io/deid

#########################################
# 1. Get List of Files
#########################################

# This will get a set of example cookie dicoms
from deid.dicom import get_files 
from deid.data import get_dataset

deid_path = os.path.abspath("%s\\..\\my_examples\\deid" %get_installdir())
input_path = os.path.abspath('f:\\data\\phi')
output_path = os.path.abspath('f:\\data\\filtered')

deid = load_deid(deid_path)
dicom_files = get_files(input_path)

#########################################
# 2. Create Client
#########################################

# You can set the output folder if you want, otherwis tmpdir is used
client = DicomCleaner(output_folder=output_path,
                      deid=deid)

#########################################
# 3. Detect 
#########################################

# Detect means using the deid recipe to parse headers
filters = [ #add in order of precidence
    {
        'group': 'blacklist', # matches names in deid.dicom e.g. %filter whitelist
        'path': os.path.join(output_path, 'blacklist')
    },
    {
        'group': 'graylist', # matches names in deid.dicom e.g. %filter whitelist
        'path': os.path.join(output_path, 'graylist')
    },
    {
        'group': 'whitelist',
        'path': os.path.join(output_path, 'whitelist')
    }
]

for filter in filters:
    if not os.path.exists(filter['path']):
        os.makedirs(filter['path'])

missed_path = os.path.join(output_path, 'missed')
if not os.path.exists(missed_path):
    os.makedirs(missed_path)

for dicom_file in dicom_files:
    df = pydicom.read_file(dicom_file)
    detect_result = client.detect(dicom_file)
    
    dst_path = None
    if detect_result['flagged']:
        for filter in filters:
            dst_path = next((filter['path'] for d in detect_result['results'] if d['group'] == filter['group']), None)
            if dst_path is not None:
                break

    if dst_path is None:
        dst_path = missed_path
    
    src = dicom_file
    dst = os.path.join(dst_path, os.path.basename(src))
    os.rename(src, dst)

    # {'flagged': True,
    # 'results': [{'coordinates': [],
    #   'group': 'blacklist',
    #   'reason': ' ImageType missing  or ImageType empty '}]}


#########################################
# 4. Clean and save 
#########################################

# client.clean()

# If there are coordinates, they are blanked. Otherwise, no change.
# Blanking 0 coordinate results

# Default output folder is temporary, unless specified at client onset
# or directly to saving functions
# client.save_png()
# client.save_dicom()

